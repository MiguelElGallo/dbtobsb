"""Minimal HTTP surface for the first Databricks App smoke test."""

import logging
import sys
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

SERVICE_NAME = "dbtobsb"
SERVICE_VERSION = "0.1.0"

logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stdout_handler)

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Service",
        "description": "Non-sensitive P0 service discovery. No product-readiness claim.",
    },
    {
        "name": "Operations",
        "description": "Process-liveness checks for deployment smoke testing.",
    },
]


class ServiceLinks(BaseModel):
    """Stable links exposed from the service index."""

    health: str = Field(description="Token-accessible process-liveness endpoint.")
    openapi: str = Field(description="Token-accessible OpenAPI document.")


class ServiceIndex(BaseModel):
    """Public service metadata."""

    service: str = Field(description="Stable service name.", examples=[SERVICE_NAME])
    version: str = Field(description="Application shell version.", examples=[SERVICE_VERSION])
    phase: Literal["p0_smoke"] = Field(
        description="Implementation phase; this shell is not the observability product."
    )
    links: ServiceLinks


class HealthResponse(BaseModel):
    """Machine-readable process-liveness response without a readiness claim."""

    status: Literal["alive"] = Field(
        description="The App process served this request.", examples=["alive"]
    )
    check: Literal["process_liveness"] = Field(
        description="The narrow scope of this check.", examples=["process_liveness"]
    )
    readiness: Literal["not_evaluated"] = Field(
        description="Product and dependency readiness are intentionally not checked.",
        examples=["not_evaluated"],
    )
    phase: Literal["p0_smoke"] = Field(
        description="This endpoint belongs to the bounded P0 smoke shell.",
        examples=["p0_smoke"],
    )
    service: str = Field(description="Stable service name.", examples=[SERVICE_NAME])
    version: str = Field(description="Application shell version.", examples=[SERVICE_VERSION])


app = FastAPI(
    title="dbtobsb",
    summary="P0 App process-liveness shell for future dbt Core observability",
    description=(
        "This bounded shell proves that a stopped-by-default Databricks App can serve "
        "FastAPI requests. It does not evaluate product readiness and has no data, job, "
        "secret, warehouse, or model-serving bindings. Interactive API documentation is "
        "disabled to avoid public runtime asset dependencies."
    ),
    version=SERVICE_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
    openapi_tags=OPENAPI_TAGS,
)


@app.get(
    "/",
    response_model=ServiceIndex,
    tags=["Service"],
    summary="Discover the P0 smoke API",
    description="Returns public shell metadata and token-accessible API links.",
    response_description="P0 smoke discovery metadata; not product readiness.",
    operation_id="getP0SmokeServiceIndex",
)
def service_index() -> ServiceIndex:
    """Return non-sensitive service metadata and discovery links."""
    return ServiceIndex(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        phase="p0_smoke",
        links=ServiceLinks(health="/api/health", openapi="/api/openapi.json"),
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Operations"],
    summary="Check App process liveness",
    description=(
        "Confirms only that the P0 App process can serve a request. It does not check "
        "dbt, Databricks resources, storage, capture, authorization, or product readiness."
    ),
    response_description="App process is alive; product readiness was not evaluated.",
    operation_id="getP0SmokeProcessLiveness",
)
def health() -> HealthResponse:
    """Confirm that the application process can serve requests."""
    logger.info(
        '{"event":"health_check","status":"alive","readiness":"not_evaluated","phase":"p0_smoke"}'
    )
    return HealthResponse(
        status="alive",
        check="process_liveness",
        readiness="not_evaluated",
        phase="p0_smoke",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )
