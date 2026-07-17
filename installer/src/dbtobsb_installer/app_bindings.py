"""Render the three sequential App authority overlays accepted by the attended installer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

_REPO_ROOT = Path.cwd().resolve()
_OVERLAY_PATH = _REPO_ROOT / ".dbtobsb-app-bindings.generated.yml"
_APP_KEY = "dbtobsb_smoke"
_SIMPLE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_RESOURCE_ENV = (
    ("DBTOBSB_WAREHOUSE_ID", "dbtobsb-app-warehouse"),
    ("DBTOBSB_RUN_HEALTH_VIEW", "dbtobsb-run-health"),
    ("DBTOBSB_NODE_HEALTH_VIEW", "dbtobsb-node-health"),
    ("DBTOBSB_COLLECTION_HEALTH_VIEW", "dbtobsb-collection-health"),
)
_VIEW_RESOURCES = (
    ("dbtobsb-run-health", "dbt_run_health"),
    ("dbtobsb-node-health", "dbt_node_health"),
    ("dbtobsb-collection-health", "dbt_collection_health"),
)


class AppBindingError(RuntimeError):
    """Static App-overlay failure with no customer value in its message."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class AppBindingInputs:
    """Closed binding inputs; resource keys and view names are not caller-selected."""

    evidence_catalog: str
    evidence_schema: str
    app_warehouse_id: str
    app_user_group_name: str


@dataclass(frozen=True, slots=True)
class RenderedAppOverlay:
    """Digest and mode of one atomically written, ignored Bundle overlay."""

    mode: Literal[
        "STAGE_NO_AUTHORITY",
        "BOUND_READ_ONLY_NO_USER",
        "FINAL_READ_ONLY_USER_ACCESS",
    ]
    sha256: str


def _app_document(
    *,
    env: list[dict[str, str]],
    resources: list[dict[str, Any]],
    permissions: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "resources": {
            "apps": {
                _APP_KEY: {
                    "config": {"env": env},
                    "description": (
                        "Read-only dbt Core observability; stopped until attended installation "
                        "completes. App and bound warehouse compute can incur cost when used."
                    ),
                    "lifecycle": {"started": False},
                    "name": "dbtobsb-smoke",
                    "permissions": permissions,
                    "resources": resources,
                    "source_code_path": "./app",
                }
            }
        }
    }


def _stage_document() -> dict[str, Any]:
    return _app_document(env=[], resources=[], permissions=[])


def _validate_final_inputs(inputs: AppBindingInputs) -> None:
    values = (
        inputs.evidence_catalog,
        inputs.evidence_schema,
        inputs.app_warehouse_id,
        inputs.app_user_group_name,
    )
    if any(not isinstance(value, str) for value in values):
        raise AppBindingError("DBTOBSB_APP_BINDING_INPUT_INVALID")
    if any(
        _SIMPLE_IDENTIFIER.fullmatch(value) is None
        for value in (inputs.evidence_catalog, inputs.evidence_schema)
    ):
        raise AppBindingError("DBTOBSB_APP_BINDING_IDENTIFIER_UNSUPPORTED")
    if _WAREHOUSE_ID.fullmatch(inputs.app_warehouse_id) is None:
        raise AppBindingError("DBTOBSB_APP_BINDING_WAREHOUSE_INVALID")
    group = inputs.app_user_group_name
    if (
        not group
        or group != group.strip()
        or group == "replace_me"
        or len(group) > 255
        or any(ord(character) < 32 for character in group)
    ):
        raise AppBindingError("DBTOBSB_APP_BINDING_GROUP_INVALID")


def _bound_document(inputs: AppBindingInputs, *, grant_user_access: bool) -> dict[str, Any]:
    _validate_final_inputs(inputs)
    prefix = f"{inputs.evidence_catalog}.{inputs.evidence_schema}"
    resources: list[dict[str, Any]] = [
        {
            "name": "dbtobsb-app-warehouse",
            "sql_warehouse": {"id": inputs.app_warehouse_id, "permission": "CAN_USE"},
        }
    ]
    resources.extend(
        {
            "name": resource_name,
            "uc_securable": {
                "permission": "SELECT",
                "securable_full_name": f"{prefix}.{view_name}",
                "securable_type": "TABLE",
            },
        }
        for resource_name, view_name in _VIEW_RESOURCES
    )
    return _app_document(
        env=[{"name": name, "value_from": resource} for name, resource in _RESOURCE_ENV],
        resources=resources,
        permissions=(
            [{"group_name": inputs.app_user_group_name, "level": "CAN_USE"}]
            if grant_user_access
            else []
        ),
    )


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _render(document: dict[str, Any]) -> bytes:
    raw = (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        + b"\n"
    )
    try:
        json_value = json.loads(raw, object_pairs_hook=_json_object)
        yaml_value = yaml.safe_load(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, yaml.YAMLError):
        raise AppBindingError("DBTOBSB_APP_BINDING_RENDER_INVALID") from None
    if json_value != document or yaml_value != document:
        raise AppBindingError("DBTOBSB_APP_BINDING_RENDER_INVALID")
    return raw


def render_stage_app_overlay() -> bytes:
    """Return the exact zero-resource, zero-user-access stage overlay."""
    return _render(_stage_document())


def render_bound_app_overlay(inputs: AppBindingInputs) -> bytes:
    """Return read-only resources and deploy-time config with no end-user access."""
    return _render(_bound_document(inputs, grant_user_access=False))


def render_final_app_overlay(inputs: AppBindingInputs) -> bytes:
    """Return the same read-only deployment config plus the approved user ACL."""
    return _render(_bound_document(inputs, grant_user_access=True))


def _write(raw: bytes) -> str:
    if _REPO_ROOT / ".dbtobsb-app-bindings.generated.yml" != _OVERLAY_PATH:
        raise AppBindingError("DBTOBSB_APP_BINDING_LOCAL_TARGET_INVALID")
    try:
        if _REPO_ROOT.is_symlink() or not _REPO_ROOT.is_dir() or _OVERLAY_PATH.is_symlink():
            raise AppBindingError("DBTOBSB_APP_BINDING_LOCAL_TARGET_INVALID")
        descriptor, temporary_name = tempfile.mkstemp(prefix=".app-bindings.", dir=_REPO_ROOT)
    except AppBindingError:
        raise
    except OSError:
        raise AppBindingError("DBTOBSB_APP_BINDING_LOCAL_WRITE_FAILED") from None
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, _OVERLAY_PATH)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise AppBindingError("DBTOBSB_APP_BINDING_LOCAL_WRITE_FAILED") from None
    return hashlib.sha256(raw).hexdigest()


def write_stage_app_overlay() -> RenderedAppOverlay:
    """Atomically place the stage overlay at the one Bundle include path."""
    raw = render_stage_app_overlay()
    return RenderedAppOverlay(mode="STAGE_NO_AUTHORITY", sha256=_write(raw))


def write_bound_app_overlay(inputs: AppBindingInputs) -> RenderedAppOverlay:
    """Place read-only deployment bindings without exposing the App to end users."""
    raw = render_bound_app_overlay(inputs)
    return RenderedAppOverlay(mode="BOUND_READ_ONLY_NO_USER", sha256=_write(raw))


def write_final_app_overlay(inputs: AppBindingInputs) -> RenderedAppOverlay:
    """Place the reviewed post-deployment user-access overlay."""
    raw = render_final_app_overlay(inputs)
    return RenderedAppOverlay(mode="FINAL_READ_ONLY_USER_ACCESS", sha256=_write(raw))


def main() -> int:
    """Create only the stopped zero-resource shell overlay for validation."""
    try:
        result = write_stage_app_overlay()
    except AppBindingError as error:
        print(error.code, file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"mode": result.mode, "outcome": "APP_OVERLAY_RENDERED", "sha256": result.sha256},
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
