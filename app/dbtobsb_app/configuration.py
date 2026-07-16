"""Fail-closed resolution of Databricks App resource bindings."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

WAREHOUSE_ID_ENV = "DBTOBSB_WAREHOUSE_ID"
RUN_HEALTH_VIEW_ENV = "DBTOBSB_RUN_HEALTH_VIEW"
NODE_HEALTH_VIEW_ENV = "DBTOBSB_NODE_HEALTH_VIEW"
COLLECTION_HEALTH_VIEW_ENV = "DBTOBSB_COLLECTION_HEALTH_VIEW"

REQUIRED_BINDINGS: tuple[str, ...] = (
    WAREHOUSE_ID_ENV,
    RUN_HEALTH_VIEW_ENV,
    NODE_HEALTH_VIEW_ENV,
    COLLECTION_HEALTH_VIEW_ENV,
)

RUN_HEALTH_VIEW = "dbt_run_health"
NODE_HEALTH_VIEW = "dbt_node_health"
COLLECTION_HEALTH_VIEW = "dbt_collection_health"

_WAREHOUSE_ID = re.compile(r"[0-9a-f]{16}\Z")
_IDENTIFIER_PART = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,254}\Z")


class BindingState(StrEnum):
    """Configuration-only readiness state."""

    READY = "ready"
    SETUP_REQUIRED = "setup_required"
    INVALID = "configuration_invalid"


@dataclass(frozen=True, slots=True)
class QualifiedView:
    """Validated literal three-part Unity Catalog name."""

    catalog: str
    schema: str
    view: str

    @property
    def quoted(self) -> str:
        """Return a SQL-safe quoted name without changing any identifier part."""
        return ".".join(f"`{part}`" for part in (self.catalog, self.schema, self.view))


@dataclass(frozen=True, slots=True)
class ResourceBindings:
    """Resolved App resources or a static setup-only state."""

    state: BindingState
    missing: tuple[str, ...]
    warehouse_id: str | None = None
    run_health_view: QualifiedView | None = None
    node_health_view: QualifiedView | None = None
    collection_health_view: QualifiedView | None = None

    @property
    def ready(self) -> bool:
        return self.state is BindingState.READY


def _view(value: str, *, expected_view: str) -> QualifiedView | None:
    parts = value.split(".")
    if len(parts) != 3 or any(_IDENTIFIER_PART.fullmatch(part) is None for part in parts):
        return None
    if parts[2] != expected_view:
        return None
    return QualifiedView(catalog=parts[0], schema=parts[1], view=parts[2])


def resolve_bindings(environment: Mapping[str, str]) -> ResourceBindings:
    """Resolve only the four installer-owned App resource values."""
    missing = tuple(name for name in REQUIRED_BINDINGS if not environment.get(name, "").strip())
    if missing:
        return ResourceBindings(state=BindingState.SETUP_REQUIRED, missing=missing)

    warehouse_id = environment[WAREHOUSE_ID_ENV].strip()
    run_view = _view(environment[RUN_HEALTH_VIEW_ENV].strip(), expected_view=RUN_HEALTH_VIEW)
    node_view = _view(environment[NODE_HEALTH_VIEW_ENV].strip(), expected_view=NODE_HEALTH_VIEW)
    collection_view = _view(
        environment[COLLECTION_HEALTH_VIEW_ENV].strip(),
        expected_view=COLLECTION_HEALTH_VIEW,
    )
    if (
        _WAREHOUSE_ID.fullmatch(warehouse_id) is None
        or run_view is None
        or node_view is None
        or collection_view is None
        or len(
            {
                (run_view.catalog, run_view.schema),
                (node_view.catalog, node_view.schema),
                (collection_view.catalog, collection_view.schema),
            }
        )
        != 1
    ):
        return ResourceBindings(state=BindingState.INVALID, missing=())

    return ResourceBindings(
        state=BindingState.READY,
        missing=(),
        warehouse_id=warehouse_id,
        run_health_view=run_view,
        node_health_view=node_view,
        collection_health_view=collection_view,
    )
