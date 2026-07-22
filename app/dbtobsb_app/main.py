"""Read-only FastAPI surface for customer-local dbt Core observability."""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Query, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from dbtobsb_app.configuration import BindingState, ResourceBindings, resolve_bindings
from dbtobsb_app.models import (
    CollectionList,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    NodeList,
    ReadinessResponse,
    ResponsibleActor,
    RunList,
    TrendList,
)
from dbtobsb_app.repository import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    AppDataAccessError,
    ObservabilityRepository,
    databricks_repository,
)
from dbtobsb_app.ui import (
    collection_runbook_page,
    dashboard_page,
    installation_runbook_page,
    landing_page,
    setup_page,
)

SERVICE_NAME = "dbtobsb"
SERVICE_VERSION = "0.4.0"
LOGO_PATH = Path(__file__).parent / "static" / "logo.png"

RepositoryFactory = Callable[[ResourceBindings], ObservabilityRepository]

logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stdout_handler)


_COST_HEADER_VALUE = "query-may-auto-start-bound-sql-warehouse"
_COST_RESPONSE_HEADER = {
    "description": (
        "This data read may auto-start the installer-bound SQL warehouse and accrue cost."
    ),
    "schema": {"type": "string", "enum": [_COST_HEADER_VALUE]},
}
_ERRORS: dict[str, tuple[str, ResponsibleActor, str]] = {
    "DBTOBSB_CONFIGURATION_INVALID": (
        "The installer-owned App resource configuration is invalid.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
    "DBTOBSB_APP_AUTH_INVALID": (
        "The App service identity could not authenticate for the data read.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
    "DBTOBSB_APP_QUERY_FAILED": (
        "The bound observability data source could not complete the read.",
        "data operator",
        "Open /operators/how-to/reconcile-collection/ and follow this code.",
    ),
    "DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH": (
        "The run-health view does not match this dbtobsb release.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
    "DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH": (
        "The node-health view does not match this dbtobsb release.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
    "DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH": (
        "The collection-health view does not match this dbtobsb release.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
    "DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH": (
        "The dashboard trend query does not match this dbtobsb release.",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and follow this code.",
    ),
}


def _error_detail(code: str, *, surface: str) -> ErrorDetail:
    safe_code = cast(ErrorCode, code if code in _ERRORS else "DBTOBSB_APP_QUERY_FAILED")
    message, responsible_actor, action = _ERRORS[safe_code]
    detail = ErrorDetail(
        code=safe_code,
        message=message,
        responsible_actor=responsible_actor,
        action=action,
        correlation_id=uuid.uuid4().hex[:16],
    )
    logger.error(
        json.dumps(
            {
                "event": "app_data_read_denied",
                "surface": surface,
                "code": detail.code,
                "correlation_id": detail.correlation_id,
                "responsible_actor": detail.responsible_actor,
                "action": detail.action,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return detail


def _exception_detail(error: Exception, *, surface: str) -> ErrorDetail:
    code = error.code if isinstance(error, AppDataAccessError) else "DBTOBSB_APP_QUERY_FAILED"
    return _error_detail(code, surface=surface)


def _safe_error(detail: ErrorDetail) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(error=detail).model_dump(mode="json"),
        headers={"X-DBTOBSB-Cost-Notice": _COST_HEADER_VALUE},
    )


def create_app(
    *,
    environment: Mapping[str, str] | None = None,
    repository_factory: RepositoryFactory = databricks_repository,
) -> FastAPI:
    """Create an App with injected configuration and data access dependencies."""
    bindings = resolve_bindings(os.environ if environment is None else environment)
    app = FastAPI(
        title="dbtobsb",
        summary="Read-only dbt Core observability in the customer Databricks workspace",
        description=(
            "Queries only the installer-bound sanitized run, node, and collection health views. "
            "It exposes no raw artifacts, SQL, log messages, paths, or credentials."
        ),
        version=SERVICE_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.bindings = bindings
    app.state.repository_factory = repository_factory

    def repository() -> ObservabilityRepository:
        return repository_factory(bindings)

    safe_html_headers = {
        "Cache-Control": "no-store",
        "Content-Security-Policy": (
            "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; "
            "form-action 'none'; frame-ancestors 'self'"
        ),
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    }

    @app.get("/api/health", response_model=HealthResponse, tags=["Operations"])
    def health() -> HealthResponse:
        """Confirm process liveness without contacting a SQL warehouse."""
        logger.info('{"event":"health_check","status":"alive"}')
        return HealthResponse(
            status="alive",
            check="process_liveness",
            service="dbtobsb",
            version=SERVICE_VERSION,
        )

    @app.get(
        "/api/readiness",
        response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse}},
        tags=["Operations"],
    )
    def readiness() -> ReadinessResponse | JSONResponse:
        """Report configuration readiness without starting billable SQL compute."""
        response = ReadinessResponse(
            status=bindings.state.value,
            check="resource_binding_configuration",
            service="dbtobsb",
            version=SERVICE_VERSION,
            required_bindings=bindings.missing,
        )
        if bindings.ready:
            return response
        return JSONResponse(status_code=503, content=response.model_dump(mode="json"))

    @app.get(
        "/api/v1/runs",
        response_model=RunList,
        responses={
            200: {"headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER}},
            503: {
                "model": ErrorResponse,
                "headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER},
            },
        },
        tags=["Observability"],
    )
    def recent_runs(
        response: Response,
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    ) -> RunList | JSONResponse:
        """Return recent runs; this query can auto-start the bound SQL warehouse and cost."""
        response.headers["X-DBTOBSB-Cost-Notice"] = _COST_HEADER_VALUE
        if bindings.state is BindingState.SETUP_REQUIRED:
            return RunList(
                state="setup_required",
                limit=limit,
                items=(),
                required_bindings=bindings.missing,
            )
        if bindings.state is BindingState.INVALID:
            return _safe_error(_error_detail("DBTOBSB_CONFIGURATION_INVALID", surface="runs"))
        try:
            source = repository()
            items = source.recent_runs(limit)
        except Exception as error:
            return _safe_error(_exception_detail(error, surface="runs"))
        return RunList(state="ready", limit=limit, items=items)

    @app.get(
        "/api/v1/nodes",
        response_model=NodeList,
        responses={
            200: {"headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER}},
            503: {
                "model": ErrorResponse,
                "headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER},
            },
        },
        tags=["Observability"],
    )
    def recent_nodes(
        response: Response,
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    ) -> NodeList | JSONResponse:
        """Return recent nodes; this query can auto-start the bound SQL warehouse and cost."""
        response.headers["X-DBTOBSB-Cost-Notice"] = _COST_HEADER_VALUE
        if bindings.state is BindingState.SETUP_REQUIRED:
            return NodeList(
                state="setup_required",
                limit=limit,
                items=(),
                required_bindings=bindings.missing,
            )
        if bindings.state is BindingState.INVALID:
            return _safe_error(_error_detail("DBTOBSB_CONFIGURATION_INVALID", surface="nodes"))
        try:
            source = repository()
            items = source.recent_nodes(limit)
        except Exception as error:
            return _safe_error(_exception_detail(error, surface="nodes"))
        return NodeList(state="ready", limit=limit, items=items)

    @app.get(
        "/api/v1/collection",
        response_model=CollectionList,
        responses={
            200: {"headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER}},
            503: {
                "model": ErrorResponse,
                "headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER},
            },
        },
        tags=["Observability"],
    )
    def recent_collection(
        response: Response,
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    ) -> CollectionList | JSONResponse:
        """Return collection lifecycle; this query can auto-start the SQL warehouse."""
        response.headers["X-DBTOBSB-Cost-Notice"] = _COST_HEADER_VALUE
        if bindings.state is BindingState.SETUP_REQUIRED:
            return CollectionList(
                state="setup_required",
                limit=limit,
                items=(),
                required_bindings=bindings.missing,
            )
        if bindings.state is BindingState.INVALID:
            return _safe_error(_error_detail("DBTOBSB_CONFIGURATION_INVALID", surface="collection"))
        try:
            source = repository()
            items = source.recent_collection(limit)
        except Exception as error:
            return _safe_error(_exception_detail(error, surface="collection"))
        return CollectionList(state="ready", limit=limit, items=items)

    @app.get(
        "/api/v1/trends",
        response_model=TrendList,
        responses={
            200: {"headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER}},
            503: {
                "model": ErrorResponse,
                "headers": {"X-DBTOBSB-Cost-Notice": _COST_RESPONSE_HEADER},
            },
        },
        tags=["Observability"],
    )
    def recent_trends(
        response: Response,
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    ) -> TrendList | JSONResponse:
        """Return chart aggregates; this query can auto-start the SQL warehouse and cost."""
        response.headers["X-DBTOBSB-Cost-Notice"] = _COST_HEADER_VALUE
        if bindings.state is BindingState.SETUP_REQUIRED:
            return TrendList(
                state="setup_required",
                limit=limit,
                items=(),
                required_bindings=bindings.missing,
            )
        if bindings.state is BindingState.INVALID:
            return _safe_error(_error_detail("DBTOBSB_CONFIGURATION_INVALID", surface="trends"))
        try:
            source = repository()
            items = source.recent_trends(limit)
        except Exception as error:
            return _safe_error(_exception_detail(error, surface="trends"))
        return TrendList(state="ready", limit=limit, items=items)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def landing() -> HTMLResponse:
        """Render a non-querying setup or cost-awareness landing page."""
        if bindings.state is BindingState.SETUP_REQUIRED:
            return HTMLResponse(setup_page(bindings.missing), headers=safe_html_headers)
        if bindings.state is BindingState.INVALID:
            return HTMLResponse(
                setup_page((), invalid=True), status_code=503, headers=safe_html_headers
            )
        return HTMLResponse(landing_page(), headers=safe_html_headers)

    @app.get("/assets/logo.png", response_class=FileResponse, include_in_schema=False)
    def logo() -> FileResponse:
        """Serve the packaged dbtobsb logo without contacting customer data."""
        return FileResponse(
            LOGO_PATH,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get(
        "/operators/how-to/reconcile-collection/",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def collection_runbook() -> HTMLResponse:
        """Explain fixed collection recovery without contacting a SQL warehouse."""
        return HTMLResponse(collection_runbook_page(), headers=safe_html_headers)

    @app.get(
        "/operators/how-to/reconcile-installation/",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def installation_runbook() -> HTMLResponse:
        """Explain fail-closed installer recovery without contacting a SQL warehouse."""
        return HTMLResponse(installation_runbook_page(), headers=safe_html_headers)

    @app.get("/observability", response_class=HTMLResponse, include_in_schema=False)
    def dashboard(limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)) -> HTMLResponse:
        """Explicitly load observability data, which can auto-start the SQL warehouse."""
        if bindings.state is BindingState.SETUP_REQUIRED:
            return HTMLResponse(setup_page(bindings.missing), headers=safe_html_headers)
        if bindings.state is BindingState.INVALID:
            return HTMLResponse(
                setup_page((), invalid=True), status_code=503, headers=safe_html_headers
            )
        try:
            source = repository()
        except Exception as error:
            failure = _exception_detail(error, surface="dashboard")
            return HTMLResponse(
                dashboard_page(
                    (),
                    (),
                    (),
                    (),
                    run_failure=failure,
                    node_failure=failure,
                    collection_failure=failure,
                    trend_failure=failure,
                ),
                status_code=503,
                headers=safe_html_headers,
            )
        run_failure: ErrorDetail | None = None
        node_failure: ErrorDetail | None = None
        collection_failure: ErrorDetail | None = None
        trend_failure: ErrorDetail | None = None
        try:
            runs = source.recent_runs(limit)
        except Exception as error:
            runs = ()
            run_failure = _exception_detail(error, surface="dashboard-runs")
        try:
            nodes = source.recent_nodes(limit)
        except Exception as error:
            nodes = ()
            node_failure = _exception_detail(error, surface="dashboard-nodes")
        try:
            collection = source.recent_collection(limit)
        except Exception as error:
            collection = ()
            collection_failure = _exception_detail(error, surface="dashboard-collection")
        try:
            trends = source.recent_trends(limit)
        except Exception as error:
            trends = ()
            trend_failure = _exception_detail(error, surface="dashboard-trends")
        status_code = (
            503
            if run_failure is not None
            and node_failure is not None
            and collection_failure is not None
            and trend_failure is not None
            else 200
        )
        return HTMLResponse(
            dashboard_page(
                runs,
                nodes,
                collection,
                trends,
                run_failure=run_failure,
                node_failure=node_failure,
                collection_failure=collection_failure,
                trend_failure=trend_failure,
            ),
            status_code=status_code,
            headers=safe_html_headers,
        )

    return app


app = create_app()
