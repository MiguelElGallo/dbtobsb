"""HTTP, setup-state, sanitization, and self-contained UI tests."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from io import StringIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dbtobsb_app.main import SERVICE_VERSION, create_app, logger
from dbtobsb_app.models import (
    CollectionHealth,
    NodeHealth,
    RunHealth,
    StructuredLogState,
)
from dbtobsb_app.repository import AppDataAccessError


def _environment() -> dict[str, str]:
    return {
        "DBTOBSB_WAREHOUSE_ID": "0123456789abcdef",
        "DBTOBSB_RUN_HEALTH_VIEW": "catalog.obs.dbt_run_health",
        "DBTOBSB_NODE_HEALTH_VIEW": "catalog.obs.dbt_node_health",
        "DBTOBSB_COLLECTION_HEALTH_VIEW": "catalog.obs.dbt_collection_health",
    }


def _run(
    *,
    structured_log_state: StructuredLogState = "VALID",
    logs_truncated: bool | None = False,
    include_deps: bool = False,
    deps_structured_log_state: StructuredLogState | None = None,
) -> RunHealth:
    now = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    return RunHealth(
        workspace_id=1,
        dbt_task_run_id=2,
        observed_job_id=3,
        observed_job_run_id=4,
        observed_task_key="dbt_build",
        repair_count=0,
        execution_count=1,
        attempt_number=1,
        task_start_time=now,
        task_end_time=now,
        lakeflow_result_state="SUCCESS",
        retrieval_state="RETRIEVED",
        capture_state="COMPLETE",
        pair_state="PAIR_VALID",
        dbt_include_deps=include_deps,
        issue_code=None,
        logs_truncated=logs_truncated,
        structured_log_state=structured_log_state,
        deps_structured_log_state=deps_structured_log_state,
        structured_log_expected_dbt_common_version="1.37.5",
        invocation_id="invocation-id",
        expected_node_count=1,
        collected_at=now,
        published_at=now,
        generated_at=now,
        elapsed_time=1.25,
        dbt_version="1.11.12",
        adapter_type="databricks",
        result_count=1,
    )


def _node(unique_id: str = "model.weather.daily") -> NodeHealth:
    return NodeHealth(
        workspace_id=1,
        dbt_task_run_id=2,
        observed_job_id=3,
        observed_job_run_id=4,
        observed_task_key="dbt_build",
        capture_state="COMPLETE",
        lakeflow_result_state="SUCCESS",
        invocation_id="invocation-id",
        unique_id=unique_id,
        resource_type="model",
        status="success",
        execution_time=0.2,
        failures=None,
    )


def _collection() -> CollectionHealth:
    now = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    return CollectionHealth(
        workspace_id=1,
        dbt_task_run_id=2,
        observed_job_id=3,
        observed_job_run_id=4,
        observed_task_key="dbt_build",
        repair_count=0,
        execution_count=1,
        attempt_number=1,
        task_start_time=now,
        task_end_time=now,
        lakeflow_result_state="SUCCESS",
        collector_state="PUBLISHED",
        collection_issue_code=None,
        first_discovered_at=now,
        last_attempted_at=now,
        collection_attempt_count=1,
        published_at=now,
        last_reconciliation_run_id=5,
    )


class FakeRepository:
    def __init__(self, *, fail: Exception | None = None) -> None:
        self.fail = fail
        self.run_limits: list[int] = []
        self.node_limits: list[int] = []
        self.collection_limits: list[int] = []

    def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
        self.run_limits.append(limit)
        if self.fail is not None:
            raise self.fail
        return (_run(),)

    def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]:
        self.node_limits.append(limit)
        if self.fail is not None:
            raise self.fail
        return (_node(),)

    def recent_collection(self, limit: int) -> tuple[CollectionHealth, ...]:
        self.collection_limits.append(limit)
        if self.fail is not None:
            raise self.fail
        return (_collection(),)


def test_health_is_stable_and_does_not_create_repository() -> None:
    factory_calls = 0

    def factory(_bindings):
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("health must not access data")

    client = TestClient(create_app(environment={}, repository_factory=factory))

    assert client.get("/api/health").json() == {
        "status": "alive",
        "check": "process_liveness",
        "service": "dbtobsb",
        "version": SERVICE_VERSION,
    }
    assert factory_calls == 0


def test_packaged_logo_is_served_without_querying_customer_data() -> None:
    def factory(_bindings):
        raise AssertionError("logo must not access data")

    response = TestClient(create_app(environment={}, repository_factory=factory)).get(
        "/assets/logo.png"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(
    ("path", "heading"),
    [
        ("/operators/how-to/reconcile-collection/", "Reconcile missing dbt evidence"),
        ("/operators/how-to/reconcile-installation/", "Reconcile a dbtobsb installation"),
    ],
)
def test_operator_runbooks_are_local_non_querying_pages(path: str, heading: str) -> None:
    factory_calls = 0

    def factory(_bindings):
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("operator runbooks must not access data")

    response = TestClient(create_app(environment={}, repository_factory=factory)).get(path)

    assert response.status_code == 200
    assert f"<h1>{heading}</h1>" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "DBTOBSB_WAREHOUSE_ID" not in response.text
    assert factory_calls == 0


def test_health_logger_emits_static_info_to_stdout() -> None:
    stdout_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout
    ]
    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert len(stdout_handlers) == 1


def test_setup_only_state_is_useful_and_never_queries() -> None:
    def factory(_bindings):
        raise AssertionError("setup-only App must not access data")

    client = TestClient(create_app(environment={}, repository_factory=factory))

    readiness = client.get("/api/readiness")
    assert readiness.status_code == 503
    assert readiness.json()["status"] == "setup_required"
    assert readiness.json()["required_bindings"] == [
        "DBTOBSB_WAREHOUSE_ID",
        "DBTOBSB_RUN_HEALTH_VIEW",
        "DBTOBSB_NODE_HEALTH_VIEW",
        "DBTOBSB_COLLECTION_HEALTH_VIEW",
    ]
    runs = client.get("/api/v1/runs")
    assert runs.status_code == 200
    assert runs.headers["x-dbtobsb-cost-notice"] == ("query-may-auto-start-bound-sql-warehouse")
    assert runs.json()["state"] == "setup_required"
    assert runs.json()["items"] == []
    assert client.get("/api/v1/nodes").json()["state"] == "setup_required"
    assert client.get("/api/v1/collection").json()["state"] == "setup_required"
    page = client.get("/")
    assert page.status_code == 200
    assert "Finish App setup" in page.text
    assert "CAN USE" in page.text
    assert "SELECT" in page.text


def test_ready_json_apis_return_only_public_models_and_forward_limit() -> None:
    repository = FakeRepository()
    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: repository)
    )

    assert client.get("/api/readiness").json()["status"] == "ready"
    runs = client.get("/api/v1/runs?limit=7")
    nodes = client.get("/api/v1/nodes?limit=8")
    collection = client.get("/api/v1/collection?limit=9")

    assert runs.status_code == 200
    assert runs.json()["state"] == "ready"
    assert runs.json()["items"][0]["observed_job_run_id"] == 4
    assert nodes.json()["items"][0]["unique_id"] == "model.weather.daily"
    assert collection.json()["items"][0]["collector_state"] == "PUBLISHED"
    assert repository.run_limits == [7]
    assert repository.node_limits == [8]
    assert repository.collection_limits == [9]
    serialized = runs.text + nodes.text
    for forbidden in (
        "raw_archive_locator",
        "archive_sha256",
        "manifest_sha256",
        "run_results_sha256",
        "compiled_code",
        "raw_sql",
        "log_message",
        "runtime_trust",
    ):
        assert forbidden not in serialized


def test_nullable_jobs_log_truncation_and_deps_state_remain_queryable() -> None:
    class NullableRepository(FakeRepository):
        def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
            return (
                _run(
                    logs_truncated=None,
                    include_deps=True,
                    deps_structured_log_state="MALFORMED",
                ),
            )

    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: NullableRepository())
    )

    response = client.get("/api/v1/runs")
    page = client.get("/observability")

    assert response.status_code == 200
    assert response.json()["items"][0]["logs_truncated"] is None
    assert response.json()["items"][0]["deps_structured_log_state"] == "MALFORMED"
    assert page.status_code == 200
    assert "Build logs" in page.text
    assert "Deps logs" in page.text
    assert "MALFORMED" in page.text


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pair_state", "VALID"),
        ("dbt_version", "9.9.9"),
        ("structured_log_expected_dbt_common_version", "9.9.9"),
        ("capture_state", "PARTIAL"),
        ("result_count", 2),
        ("deps_structured_log_state", "VALID"),
        ("issue_code", "DBT_ARCHIVE_INVALID"),
        ("observed_task_key", "caller_controlled"),
        ("execution_count", 0),
        ("repair_count", -1),
    ],
)
def test_run_model_rejects_impossible_or_unqualified_evidence(field: str, value: object) -> None:
    candidate = _run().model_dump()
    candidate[field] = value

    with pytest.raises(ValidationError):
        RunHealth.model_validate(candidate)


def test_node_model_keeps_native_status_resource_aware() -> None:
    candidate = _node().model_dump()
    candidate["status"] = "pass"

    with pytest.raises(ValidationError):
        NodeHealth.model_validate(candidate)


def test_run_model_rejects_invalid_pair_outside_invalid_capture() -> None:
    candidate = _run().model_dump()
    candidate.update(
        {
            "capture_state": "PARTIAL",
            "pair_state": "PAIR_INVALID",
            "issue_code": "DBT_RUN_RESULTS_NOT_PRODUCED",
            "invocation_id": None,
            "generated_at": None,
            "elapsed_time": None,
            "dbt_version": None,
            "adapter_type": None,
            "result_count": None,
            "expected_node_count": 0,
        }
    )

    with pytest.raises(ValidationError):
        RunHealth.model_validate(candidate)


def test_run_model_requires_issue_code_for_noncomplete_capture() -> None:
    candidate = _run().model_dump()
    candidate.update(
        {
            "capture_state": "PARTIAL",
            "pair_state": None,
            "issue_code": None,
            "invocation_id": None,
            "generated_at": None,
            "elapsed_time": None,
            "dbt_version": None,
            "adapter_type": None,
            "result_count": None,
            "expected_node_count": 0,
        }
    )

    with pytest.raises(ValidationError):
        RunHealth.model_validate(candidate)


def test_node_model_rejects_negative_failure_count() -> None:
    candidate = _node().model_dump()
    candidate["failures"] = -1

    with pytest.raises(ValidationError):
        NodeHealth.model_validate(candidate)


@pytest.mark.parametrize(
    "result_state",
    [
        "CANCELED",
        "DISABLED",
        "EXCLUDED",
        "FAILED",
        "MAXIMUM_CONCURRENT_RUNS_REACHED",
        "SUCCESS",
        "SUCCESS_WITH_FAILURES",
        "TIMEDOUT",
        "UPSTREAM_CANCELED",
        "UPSTREAM_FAILED",
    ],
)
def test_pinned_legacy_lakeflow_result_states_remain_observable(result_state: str) -> None:
    candidate = _run().model_dump()
    candidate["lakeflow_result_state"] = result_state

    assert RunHealth.model_validate(candidate).lakeflow_result_state == result_state


def test_ready_landing_explains_cost_and_never_queries() -> None:
    factory_calls = 0

    def factory(_bindings):
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("landing must not access data")

    client = TestClient(create_app(environment=_environment(), repository_factory=factory))

    response = client.get("/")

    assert response.status_code == 200
    assert factory_calls == 0
    assert "The Databricks App is already running" in response.text
    assert "App compute" in response.text
    assert "SQL warehouse" in response.text
    assert "auto-start" in response.text
    assert "separate SQL-warehouse cost" in response.text
    assert "neither changes nor currently knows" in response.text
    assert "auto-stop" in response.text
    assert "cost-center/tag settings" in response.text
    assert "verify those settings" in response.text
    assert 'rel="icon"' in response.text
    assert 'href="/assets/logo.png"' in response.text
    assert 'type="image/png"' in response.text
    assert 'class="brand-logo"' in response.text
    assert 'src="/assets/logo.png"' in response.text
    assert 'alt="dbtobsb logo"' in response.text
    assert 'href="/observability"' in response.text
    assert "/api/v1/runs" in response.text
    assert "/api/v1/nodes" in response.text


def test_ready_health_and_readiness_never_query() -> None:
    factory_calls = 0

    def factory(_bindings):
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("operational checks must not access data")

    client = TestClient(create_app(environment=_environment(), repository_factory=factory))

    assert client.get("/api/health").status_code == 200
    readiness = client.get("/api/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "ready"
    assert factory_calls == 0


def test_limits_are_bounded_before_repository_access() -> None:
    repository = FakeRepository()
    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: repository)
    )

    assert client.get("/api/v1/runs?limit=0").status_code == 422
    assert client.get("/api/v1/nodes?limit=101").status_code == 422
    assert client.get("/api/v1/collection?limit=0").status_code == 422
    assert client.get("/observability?limit=1000").status_code == 422
    assert repository.run_limits == []
    assert repository.node_limits == []
    assert repository.collection_limits == []


def test_connector_details_never_escape_categorized_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canary = "jdbc-canary token=secret path=/Volumes/private"
    repository = FakeRepository(fail=RuntimeError(canary))
    monkeypatch.setattr("dbtobsb_app.main.uuid.uuid4", lambda: SimpleNamespace(hex="a" * 32))
    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: repository)
    )

    for path in ("/api/v1/runs", "/api/v1/nodes", "/api/v1/collection"):
        response = client.get(path)
        assert response.status_code == 503
        detail = response.json()["error"]
        assert detail["code"] == "DBTOBSB_APP_QUERY_FAILED"
        assert detail["correlation_id"] == "a" * 16
        assert detail["responsible_actor"] == "data operator"
        assert detail["action"] == (
            "Open /operators/how-to/reconcile-collection/ and follow this code."
        )
        assert response.headers["x-dbtobsb-cost-notice"] == (
            "query-may-auto-start-bound-sql-warehouse"
        )
        assert canary not in response.text
    page = client.get("/observability")
    assert page.status_code == 503
    assert "Recent runs unavailable" in page.text
    assert "Recent nodes unavailable" in page.text
    assert "Collection health unavailable" in page.text
    assert 'href="/operators/how-to/reconcile-collection/"' in page.text
    assert "DBTOBSB_APP_QUERY_FAILED" in page.text
    assert "aaaaaaaaaaaaaaaa" in page.text
    assert canary not in page.text


def test_error_log_matches_safe_operator_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    monkeypatch.setattr("dbtobsb_app.main.uuid.uuid4", lambda: SimpleNamespace(hex="b" * 32))
    client = TestClient(
        create_app(
            environment=_environment(),
            repository_factory=lambda _: FakeRepository(
                fail=AppDataAccessError("DBTOBSB_APP_AUTH_INVALID")
            ),
        )
    )

    try:
        assert client.get("/api/v1/runs").status_code == 503
    finally:
        logger.removeHandler(handler)

    event = json.loads(stream.getvalue())
    assert event == {
        "event": "app_data_read_denied",
        "surface": "runs",
        "code": "DBTOBSB_APP_AUTH_INVALID",
        "correlation_id": "b" * 16,
        "responsible_actor": "deployment/seal verifier",
        "action": "Open /operators/how-to/reconcile-installation/ and follow this code.",
    }


def test_dashboard_preserves_healthy_panel_when_other_panel_fails() -> None:
    class DegradedRepository(FakeRepository):
        def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
            raise AppDataAccessError("DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH")

    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: DegradedRepository())
    )

    page = client.get("/observability")

    assert page.status_code == 200
    assert "Recent runs unavailable" in page.text
    assert "DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH" in page.text
    assert 'aria-labelledby="recent-runs-failed-heading"' in page.text
    assert 'id="recent-runs-failed-heading"' in page.text
    assert 'aria-labelledby="Recent runs-failed-heading"' not in page.text
    assert 'id="recent-nodes-heading"' in page.text
    assert "model.weather.daily" in page.text


@pytest.mark.parametrize(
    ("code", "action"),
    [
        (
            "DBTOBSB_APP_AUTH_INVALID",
            "Open /operators/how-to/reconcile-installation/ and follow this code.",
        ),
        (
            "DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH",
            "Open /operators/how-to/reconcile-installation/ and follow this code.",
        ),
        (
            "DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH",
            "Open /operators/how-to/reconcile-installation/ and follow this code.",
        ),
        (
            "DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH",
            "Open /operators/how-to/reconcile-installation/ and follow this code.",
        ),
    ],
)
def test_safe_error_categories_have_one_deterministic_recovery(code: str, action: str) -> None:
    client = TestClient(
        create_app(
            environment=_environment(),
            repository_factory=lambda _: FakeRepository(fail=AppDataAccessError(code)),
        )
    )

    detail = client.get("/api/v1/runs").json()["error"]

    assert detail["code"] == code
    assert detail["action"] == action
    assert " or " not in detail["action"]


def test_invalid_binding_values_are_not_reflected() -> None:
    canary = "catalog.schema.dbt_run_health` UNION SELECT secret"
    environment = _environment() | {"DBTOBSB_RUN_HEALTH_VIEW": canary}
    client = TestClient(create_app(environment=environment))

    readiness = client.get("/api/readiness")
    assert readiness.status_code == 503
    assert readiness.json()["status"] == "configuration_invalid"
    response = client.get("/api/v1/runs")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DBTOBSB_CONFIGURATION_INVALID"
    assert canary not in response.text
    assert canary not in client.get("/").text


def test_dashboard_is_self_contained_escaped_and_hardened() -> None:
    class MarkupRepository(FakeRepository):
        def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
            return (_run(structured_log_state="MALFORMED"),)

        def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]:
            return (_node("model.<img src=x onerror=alert(1)>"),)

    repository = MarkupRepository()
    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: repository)
    )

    response = client.get("/observability")

    assert response.status_code == 200
    assert "Recent runs" in response.text
    assert "Recent nodes" in response.text
    assert "Collection health" in response.text
    assert "Build logs" in response.text
    assert "Retrieval" in response.text
    assert "Issue" in response.text
    assert "Jobs logs truncated" in response.text
    assert "Expected dbt-common" in response.text
    assert "1 / 1 expected" in response.text
    assert ">None</td>" in response.text
    assert ">No</td>" in response.text
    assert ">Unknown</td>" in response.text
    assert response.text.count('role="region"') == 3
    assert response.text.count('tabindex="0"') == 3
    assert response.text.count("<caption") == 3
    assert '<th scope="row">4</th>' in response.text
    assert '<time datetime="2026-07-16T10:00:00+00:00">' in response.text
    assert "How to read this evidence" in response.text
    assert "Closing this page does not stop App compute" in response.text
    assert ">1.37.5</td>" in response.text
    assert ">COMPLETE</td>" in response.text
    assert ">MALFORMED</td>" in response.text
    assert "The Databricks App is already running" in response.text
    assert "SQL warehouse" in response.text
    assert "auto-start" in response.text
    assert "auto-stop" in response.text
    assert "&lt;img src=x onerror=alert(1)&gt;" in response.text
    assert "<script>" not in response.text
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")


def test_empty_dashboard_has_concrete_next_steps() -> None:
    class EmptyRepository(FakeRepository):
        def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
            return ()

        def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]:
            return ()

        def recent_collection(self, limit: int) -> tuple[CollectionHealth, ...]:
            return ()

    client = TestClient(
        create_app(environment=_environment(), repository_factory=lambda _: EmptyRepository())
    )

    page = client.get("/observability")

    assert page.status_code == 200
    assert "Run an onboarded dbt Job" in page.text
    assert "verify its collector child succeeded" in page.text
    assert "Review the run capture state and issue code above" in page.text
    assert "No collection records yet" in page.text


def test_openapi_has_json_surfaces_and_no_external_interactive_docs() -> None:
    client = TestClient(create_app(environment={}))

    document = client.get("/api/openapi.json").json()
    assert document["info"]["version"] == SERVICE_VERSION
    assert "/api/health" in document["paths"]
    assert "/api/readiness" in document["paths"]
    assert "/api/v1/runs" in document["paths"]
    assert "/api/v1/nodes" in document["paths"]
    assert "/api/v1/collection" in document["paths"]
    assert "/" not in document["paths"]
    assert "/observability" not in document["paths"]
    assert "auto-start" in document["paths"]["/api/v1/runs"]["get"]["description"]
    assert "auto-start" in document["paths"]["/api/v1/nodes"]["get"]["description"]
    assert "auto-start" in document["paths"]["/api/v1/collection"]["get"]["description"]
    cost_header = document["paths"]["/api/v1/runs"]["get"]["responses"]["200"]["headers"]
    assert "X-DBTOBSB-Cost-Notice" in cost_header
    assert "auto-start" in cost_header["X-DBTOBSB-Cost-Notice"]["description"]
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
