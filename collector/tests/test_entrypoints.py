"""Operator-safe collector entrypoint diagnostics."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from typing import NoReturn

import pytest

from dbtobsb_collector import entrypoints
from dbtobsb_collector.jobs import JobsEvidenceError


def _bootstrap_argv(*, catalog: str, schema: str) -> list[str]:
    return [
        "dbtobsb-bootstrap",
        "--workspace_id",
        "1",
        "--catalog",
        catalog,
        "--schema",
        schema,
        "--warehouse_id",
        "0123456789abcdef",
        "--observed_job_id",
        "2",
        "--collector_job_id",
        "3",
        "--reconciler_job_id",
        "4",
        "--observed_service_principal_name",
        "observed-sp",
        "--collector_service_principal_name",
        "collector-sp",
        "--job_manager_group_name",
        "job-managers",
        "--collector_environment_sha256",
        "b" * 64,
    ]


def _collect_argv(*, observed_task_key: str = "dbt_build", catalog: str = "c") -> list[str]:
    return [
        "dbtobsb-collect",
        "--workspace_id",
        "1",
        "--observed_job_id",
        "2",
        "--observed_job_run_id",
        "3",
        "--dbt_task_run_id",
        "4",
        "--observed_task_key",
        observed_task_key,
        "--repair_count",
        "0",
        "--execution_count",
        "1",
    ]


def _reconcile_argv() -> list[str]:
    return [
        "dbtobsb-reconcile",
        "--workspace_id",
        "1",
        "--reconciler_job_id",
        "2",
        "--reconciliation_run_id",
        "3",
    ]


def _delete_argv(*, catalog: str = "c", schema: str = "s") -> list[str]:
    return ["dbtobsb-uninstall-delete", "--catalog", catalog, "--schema", schema]


def test_collect_prints_safe_machine_readable_runtime_denial(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canary = "SENSITIVE_PLATFORM_VALUE_CANARY"

    def deny(**_: str) -> NoReturn:
        raise JobsEvidenceError("DBT_JOBS_DBT_TARGET_BINDING_INVALID")

    monkeypatch.setattr(entrypoints, "_run_collect", deny)
    monkeypatch.setattr(
        sys,
        "argv",
        _collect_argv(observed_task_key=canary, catalog=canary),
    )

    with pytest.raises(SystemExit) as exc_info:
        entrypoints.collect()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "DBT_JOBS_DBT_TARGET_BINDING_INVALID"
    assert payload["component"] == "dbt target binding"
    assert payload["responsible_actor"] == "deployment/seal verifier"
    assert payload["action"] == (
        "Open /operators/how-to/reconcile-installation/ and follow the matching code."
    )
    assert canary not in json.dumps(payload, sort_keys=True)


def test_run_now_override_is_rejected_before_spark_or_unity_catalog_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Reader:
        @staticmethod
        def preflight(context: object) -> NoReturn:
            del context
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")

    monkeypatch.setattr(
        entrypoints,
        "load_deployed_runtime_contract",
        lambda: SimpleNamespace(
            seal=SimpleNamespace(),
            policy=SimpleNamespace(installed_policy=SimpleNamespace()),
        ),
    )
    monkeypatch.setattr(
        entrypoints.DatabricksJobsEvidenceReader,
        "for_installed_policy",
        lambda **_: _Reader(),
    )

    def forbidden_spark() -> NoReturn:
        raise AssertionError("Spark and Unity Catalog must remain untouched")

    monkeypatch.setattr(entrypoints, "_active_spark", forbidden_spark)

    with pytest.raises(
        JobsEvidenceError,
        match="DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH",
    ):
        entrypoints._run_collect(
            workspace_id="1",
            observed_job_id="2",
            observed_job_run_id="3",
            dbt_task_run_id="4",
            observed_task_key="dbt_build",
            repair_count="0",
            execution_count="1",
        )


@pytest.mark.parametrize(
    "code",
    [
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE",
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID",
    ],
)
@pytest.mark.parametrize("runner", ["_run_bootstrap", "_run_collect", "_run_reconcile"])
def test_deployed_contract_failure_precedes_spark_for_every_runtime_entrypoint(
    monkeypatch: pytest.MonkeyPatch,
    runner: str,
    code: str,
) -> None:
    def deny_contract() -> NoReturn:
        raise RuntimeError(code)

    def forbidden_spark() -> NoReturn:
        raise AssertionError("Spark and Unity Catalog must remain untouched")

    monkeypatch.setattr(entrypoints, "load_deployed_runtime_contract", deny_contract)
    monkeypatch.setattr(entrypoints, "_active_spark", forbidden_spark)
    arguments = {
        "_run_bootstrap": {
            "workspace_id": "1",
            "catalog": "c",
            "schema": "s",
            "warehouse_id": "0123456789abcdef",
            "observed_job_id": "2",
            "collector_job_id": "3",
            "reconciler_job_id": "4",
            "observed_service_principal_name": "observed-sp",
            "collector_service_principal_name": "collector-sp",
            "job_manager_group_name": "job-managers",
            "collector_environment_sha256": "b" * 64,
        },
        "_run_collect": {
            "workspace_id": "1",
            "observed_job_id": "2",
            "observed_job_run_id": "3",
            "dbt_task_run_id": "4",
            "observed_task_key": "dbt_build",
            "repair_count": "0",
            "execution_count": "1",
        },
        "_run_reconcile": {
            "workspace_id": "1",
            "reconciler_job_id": "2",
            "reconciliation_run_id": "3",
        },
    }[runner]

    with pytest.raises(RuntimeError, match=code):
        getattr(entrypoints, runner)(**arguments)


@pytest.mark.parametrize(
    ("code", "component", "responsible_actor"),
    [
        (
            "DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH",
            "installed deployment seal",
            "deployment/seal verifier",
        ),
        ("DBT_RAW_ARCHIVE_READBACK_MISMATCH", "raw archive custody", "UC volume operator"),
        ("DBTOBSB_CHILD_READBACK_MISMATCH", "evidence publication", "data operator"),
        (
            "DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED",
            "installed deployment binding",
            "deployment/seal verifier",
        ),
        (
            "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE",
            "installed deployment binding",
            "deployment/seal verifier",
        ),
        (
            "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID",
            "installed deployment binding",
            "deployment/seal verifier",
        ),
        (
            "DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH",
            "installed attempt binding",
            "deployment/seal verifier",
        ),
    ],
)
def test_collect_maps_known_runtime_failures_to_one_safe_recovery(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    code: str,
    component: str,
    responsible_actor: str,
) -> None:
    def deny(**_: str) -> NoReturn:
        raise RuntimeError(code)

    monkeypatch.setattr(entrypoints, "_run_collect", deny)
    monkeypatch.setattr(sys, "argv", _collect_argv())

    with pytest.raises(SystemExit):
        entrypoints.collect()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == code
    assert payload["component"] == component
    assert payload["responsible_actor"] == responsible_actor
    assert payload["action"].startswith(("Run the documented ", "Open /operators/"))


def test_collect_unknown_runtime_exception_text_is_not_disclosed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canary = "signed URL token SQL and Personal Data canary"

    def deny(**_: str) -> NoReturn:
        raise RuntimeError(canary)

    monkeypatch.setattr(entrypoints, "_run_collect", deny)
    monkeypatch.setattr(sys, "argv", _collect_argv())

    with pytest.raises(SystemExit):
        entrypoints.collect()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "DBTOBSB_COLLECTOR_FAILED"
    assert canary not in json.dumps(payload, sort_keys=True)


@pytest.mark.parametrize("entrypoint", ["collect", "bootstrap", "reconcile", "uninstall_delete"])
def test_unknown_cli_argument_is_sanitized_without_argv_echo(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: str,
) -> None:
    canary = "SENSITIVE_PARSE_CANARY"
    arguments = {
        "collect": _collect_argv(),
        "bootstrap": _bootstrap_argv(catalog="c", schema="s"),
        "reconcile": _reconcile_argv(),
        "uninstall_delete": _delete_argv(),
    }[entrypoint]
    arguments.extend(["--unknown-secret", canary])
    monkeypatch.setattr(sys, "argv", arguments)

    with pytest.raises(SystemExit) as exc_info:
        getattr(entrypoints, entrypoint)()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert canary not in captured.out
    assert canary not in captured.err
    assert json.loads(captured.out)["outcome"] == "denied"


def test_delete_uninstall_uses_deployed_binding_and_reports_exact_count(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spark = object()
    monkeypatch.setattr(
        entrypoints,
        "load_deployed_runtime_contract",
        lambda: SimpleNamespace(seal=SimpleNamespace(evidence_catalog="c", evidence_schema="s")),
    )
    monkeypatch.setattr(entrypoints, "_active_spark", lambda: spark)
    monkeypatch.setattr(
        entrypoints,
        "delete_installation_objects",
        lambda actual, *, catalog, schema: (
            SimpleNamespace(deleted_object_count=9)
            if (actual, catalog, schema) == (spark, "c", "s")
            else pytest.fail("Delete arguments did not match the deployed binding")
        ),
    )
    monkeypatch.setattr(sys, "argv", _delete_argv())

    entrypoints.uninstall_delete()

    assert json.loads(capsys.readouterr().out) == {
        "deleted_object_count": 9,
        "event": "dbtobsb_delete_uninstall_verified",
        "schema_preserved": True,
    }


def test_delete_uninstall_binding_mismatch_precedes_spark_and_hides_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    canary = "SENSITIVE_DELETE_TARGET_CANARY"
    monkeypatch.setattr(
        entrypoints,
        "load_deployed_runtime_contract",
        lambda: SimpleNamespace(seal=SimpleNamespace(evidence_catalog="c", evidence_schema="s")),
    )

    def forbidden_spark() -> NoReturn:
        raise AssertionError("Spark must not start for a mismatched delete binding")

    monkeypatch.setattr(entrypoints, "_active_spark", forbidden_spark)
    monkeypatch.setattr(sys, "argv", _delete_argv(catalog=canary, schema=canary))

    with pytest.raises(SystemExit) as exc_info:
        entrypoints.uninstall_delete()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "DBTOBSB_DEPLOYMENT_BINDING_INVALID"
    assert canary not in json.dumps(payload, sort_keys=True)


@pytest.mark.parametrize(
    ("code", "component", "action"),
    [
        (
            "DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH",
            "schema ownership",
            "Run the documented schema-ownership reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL",
            "partial fresh installation",
            "Run the documented partial-install cleanup workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT",
            "evidence-object grants",
            "Run the documented evidence-object grant reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE",
            "Databricks metadata compatibility",
            "Run the documented bootstrap compatibility reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_SPARK_SESSION_UNAVAILABLE",
            "serverless Spark session",
            "Run the documented bootstrap compatibility reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_SCHEMA_METADATA_READ_FAILED",
            "serverless bootstrap metadata",
            "Run the documented bootstrap compatibility reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED",
            "fresh-install object creation",
            "Run the documented evidence-object reconciliation workflow.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED",
            "table creation authorization",
            "Open /operators/how-to/reconcile-installation/ and follow the matching code.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE",
            "managed storage connectivity",
            "Open /operators/how-to/reconcile-installation/ and follow the matching code.",
        ),
        (
            "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE",
            "Databricks DDL compatibility",
            "Open /operators/how-to/reconcile-installation/ and follow the matching code.",
        ),
    ],
)
def test_bootstrap_prints_one_safe_recovery_workflow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    code: str,
    component: str,
    action: str,
) -> None:
    canary = "SENSITIVE_CATALOG_SCHEMA_CANARY"

    def deny(**_: str) -> NoReturn:
        raise RuntimeError(code)

    monkeypatch.setattr(entrypoints, "_run_bootstrap", deny)
    monkeypatch.setattr(
        sys,
        "argv",
        _bootstrap_argv(catalog=canary, schema=canary),
    )

    with pytest.raises(SystemExit) as exc_info:
        entrypoints.bootstrap()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == code
    assert payload["component"] == component
    assert payload["responsible_actor"] == "UC operator"
    assert payload["action"] == action
    assert " or " not in action
    assert canary not in json.dumps(payload, sort_keys=True)


def test_unknown_bootstrap_exception_text_is_not_disclosed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canary = "connector response secret canary"

    def deny(**_: str) -> NoReturn:
        raise RuntimeError(canary)

    monkeypatch.setattr(entrypoints, "_run_bootstrap", deny)
    monkeypatch.setattr(
        sys,
        "argv",
        _bootstrap_argv(catalog="c", schema="s"),
    )

    with pytest.raises(SystemExit):
        entrypoints.bootstrap()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "DBTOBSB_BOOTSTRAP_FAILED"
    assert canary not in json.dumps(payload, sort_keys=True)


def test_bootstrap_spark_start_failure_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    canary = "SENSITIVE_SPARK_START_FAILURE"

    def fail() -> NoReturn:
        raise RuntimeError(canary)

    monkeypatch.setattr(entrypoints, "_active_spark", fail)

    with pytest.raises(RuntimeError) as exc_info:
        entrypoints._active_bootstrap_spark()

    assert str(exc_info.value) == "DBTOBSB_BOOTSTRAP_SPARK_SESSION_UNAVAILABLE"
    assert canary not in str(exc_info.value)


@pytest.mark.parametrize(
    "code",
    [
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE",
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID",
        "DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED",
    ],
)
def test_bootstrap_routes_deployed_contract_failures_to_the_seal_verifier(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    code: str,
) -> None:
    def deny(**_: str) -> NoReturn:
        raise RuntimeError(code)

    monkeypatch.setattr(entrypoints, "_run_bootstrap", deny)
    monkeypatch.setattr(sys, "argv", _bootstrap_argv(catalog="c", schema="s"))

    with pytest.raises(SystemExit):
        entrypoints.bootstrap()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == code
    assert payload["component"] == "installed deployment binding"
    assert payload["responsible_actor"] == "deployment/seal verifier"


@pytest.mark.parametrize(
    ("raised", "expected_code", "expected_actor"),
    [
        (
            entrypoints.ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED"),
            "DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED",
            "data operator",
        ),
        (
            entrypoints.ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH"),
            "DBTOBSB_RECONCILIATION_BINDING_MISMATCH",
            "deployment/seal verifier",
        ),
        (
            entrypoints.ReconciliationError("DBTOBSB_RECONCILIATION_native response canary"),
            "DBTOBSB_RECONCILIATION_FAILED",
            "data operator",
        ),
        (
            RuntimeError("DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED"),
            "DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED",
            "deployment/seal verifier",
        ),
        (
            RuntimeError("DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE"),
            "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE",
            "deployment/seal verifier",
        ),
        (
            RuntimeError("DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID"),
            "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID",
            "deployment/seal verifier",
        ),
    ],
)
def test_reconciliation_diagnostic_accepts_only_closed_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    raised: Exception,
    expected_code: str,
    expected_actor: str,
) -> None:
    def deny(**_: str) -> NoReturn:
        raise raised

    monkeypatch.setattr(entrypoints, "_run_reconcile", deny)
    monkeypatch.setattr(sys, "argv", _reconcile_argv())

    with pytest.raises(SystemExit):
        entrypoints.reconcile()

    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == expected_code
    assert payload["responsible_actor"] == expected_actor
    assert "runtime trust" not in payload["action"].lower()
    assert "canary" not in json.dumps(payload, sort_keys=True)
