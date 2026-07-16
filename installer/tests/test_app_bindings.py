"""Closed shell, bound-deployment, and user-access App overlay tests."""

from __future__ import annotations

import json
import stat
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from dbtobsb_installer import app_bindings
from dbtobsb_installer.app_bindings import AppBindingError, AppBindingInputs


def _inputs() -> AppBindingInputs:
    return AppBindingInputs(
        evidence_catalog="observability",
        evidence_schema="dbtobsb",
        app_warehouse_id="0123456789abcdef",
        app_user_group_name="dbtobsb-users",
    )


def _app(raw: bytes) -> dict:
    document = yaml.safe_load(raw)
    return document["resources"]["apps"]["dbtobsb_smoke"]


def test_stage_overlay_has_no_authority_and_is_canonical() -> None:
    first = app_bindings.render_stage_app_overlay()
    second = app_bindings.render_stage_app_overlay()
    app = _app(first)

    assert first == second
    assert (
        first
        == json.dumps(
            yaml.safe_load(first), ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode()
        + b"\n"
    )
    assert app["config"] == {"env": []}
    assert app["lifecycle"] == {"started": False}
    assert app["name"] == "dbtobsb-smoke"
    assert app["source_code_path"] == "./app"
    assert app["permissions"] == []
    assert app["resources"] == []


def test_bound_overlay_is_one_exact_read_only_binding_set_without_users() -> None:
    app = _app(app_bindings.render_bound_app_overlay(_inputs()))

    assert app["lifecycle"] == {"started": False}
    assert app["permissions"] == []
    assert app["config"]["env"] == [
        {"name": "DBTOBSB_WAREHOUSE_ID", "value_from": "dbtobsb-app-warehouse"},
        {"name": "DBTOBSB_RUN_HEALTH_VIEW", "value_from": "dbtobsb-run-health"},
        {"name": "DBTOBSB_NODE_HEALTH_VIEW", "value_from": "dbtobsb-node-health"},
        {
            "name": "DBTOBSB_COLLECTION_HEALTH_VIEW",
            "value_from": "dbtobsb-collection-health",
        },
    ]
    assert app["resources"] == [
        {
            "name": "dbtobsb-app-warehouse",
            "sql_warehouse": {"id": "0123456789abcdef", "permission": "CAN_USE"},
        },
        {
            "name": "dbtobsb-run-health",
            "uc_securable": {
                "permission": "SELECT",
                "securable_full_name": "observability.dbtobsb.dbt_run_health",
                "securable_type": "TABLE",
            },
        },
        {
            "name": "dbtobsb-node-health",
            "uc_securable": {
                "permission": "SELECT",
                "securable_full_name": "observability.dbtobsb.dbt_node_health",
                "securable_type": "TABLE",
            },
        },
        {
            "name": "dbtobsb-collection-health",
            "uc_securable": {
                "permission": "SELECT",
                "securable_full_name": "observability.dbtobsb.dbt_collection_health",
                "securable_type": "TABLE",
            },
        },
    ]


def test_final_overlay_changes_only_end_user_access_after_deployment() -> None:
    bound = _app(app_bindings.render_bound_app_overlay(_inputs()))
    final = _app(app_bindings.render_final_app_overlay(_inputs()))

    assert final | {"permissions": []} == bound
    assert final["permissions"] == [{"group_name": "dbtobsb-users", "level": "CAN_USE"}]


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"evidence_catalog": "catalog-name"}, "DBTOBSB_APP_BINDING_IDENTIFIER_UNSUPPORTED"),
        ({"evidence_schema": " schema"}, "DBTOBSB_APP_BINDING_IDENTIFIER_UNSUPPORTED"),
        ({"app_warehouse_id": "not-an-id"}, "DBTOBSB_APP_BINDING_WAREHOUSE_INVALID"),
        ({"app_user_group_name": "replace_me"}, "DBTOBSB_APP_BINDING_GROUP_INVALID"),
    ],
)
def test_final_inputs_fail_closed(change: dict[str, str], code: str) -> None:
    with pytest.raises(AppBindingError, match=code):
        app_bindings.render_bound_app_overlay(replace(_inputs(), **change))


def test_atomic_writer_uses_only_ignored_generated_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    overlay = tmp_path / ".dbtobsb-app-bindings.generated.yml"
    monkeypatch.setattr(app_bindings, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(app_bindings, "_OVERLAY_PATH", overlay)

    result = app_bindings.write_bound_app_overlay(_inputs())

    assert result.mode == "BOUND_READ_ONLY_NO_USER"
    assert result.sha256 == app_bindings.hashlib.sha256(overlay.read_bytes()).hexdigest()
    assert stat.S_IMODE(overlay.stat().st_mode) == 0o600
    assert _app(overlay.read_bytes())["permissions"] == []


def test_writer_rejects_symlinked_generated_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.write_text("outside")
    overlay = tmp_path / ".dbtobsb-app-bindings.generated.yml"
    overlay.symlink_to(outside)
    monkeypatch.setattr(app_bindings, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(app_bindings, "_OVERLAY_PATH", overlay)

    with pytest.raises(AppBindingError, match="DBTOBSB_APP_BINDING_LOCAL_TARGET_INVALID"):
        app_bindings.write_stage_app_overlay()
