"""Bundle and bounded live-smoke safeguards retained for the App."""

import os
import stat
import subprocess
from pathlib import Path

from yaml import safe_load


def test_bundle_keeps_smoke_app_stopped_and_unbound_by_default() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    bundle = safe_load((repository_root / "databricks.yml").read_text(encoding="utf-8"))
    assert bundle["include"] == [
        ".dbtobsb-observed.generated.yml",
        ".dbtobsb-app-bindings.generated.yml",
    ]
    overlay = safe_load(
        (repository_root / ".dbtobsb-app-bindings.generated.yml").read_text(encoding="utf-8")
    )
    app_resource = overlay["resources"]["apps"]["dbtobsb_smoke"]

    assert bundle["targets"]["smoke"]["default"] is True
    assert app_resource["lifecycle"]["started"] is False
    assert app_resource["resources"] == []
    assert app_resource["permissions"] == []
    assert app_resource["config"] == {"env": []}
    description = app_resource["description"]
    assert "stopped until attended installation completes" in description
    assert "compute can incur cost" in description


def test_demo_passes_only_correlated_attempt_parameters_to_triggered_collector() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    bundle = safe_load((repository_root / "databricks.yml").read_text(encoding="utf-8"))
    observed = safe_load(
        (repository_root / ".dbtobsb-observed.generated.yml").read_text(encoding="utf-8")
    )
    demo_tasks = observed["resources"]["jobs"]["dbtobsb_observed"]["tasks"]
    dbt_task = next(task for task in demo_tasks if task["task_key"] == "dbt_build")
    collector_edge = next(task for task in demo_tasks if task["task_key"] == "collect_dbt_evidence")
    parameters = collector_edge["run_job_task"]["job_parameters"]

    assert dbt_task["python_wheel_task"]["entry_point"] == "run-dbt"
    assert dbt_task["python_wheel_task"]["package_name"] == "dbtobsb-collector"
    assert set(parameters) == {
        "workspace_id",
        "observed_job_id",
        "observed_job_run_id",
        "dbt_task_run_id",
        "observed_task_key",
        "repair_count",
        "execution_count",
    }
    assert "catalog" not in parameters
    assert "schema" not in parameters
    assert "raw_volume_name" not in bundle["variables"]


def _write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _smoke_environment(
    tmp_path: Path,
    *,
    fail_health: bool = False,
    fail_cleanup_get_once: bool = False,
    resource_binding: bool = False,
    compute_size: str = "MEDIUM",
    unrelated_app: bool = False,
) -> dict[str, str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "calls.log"
    curl_args_log = tmp_path / "curl-args.log"
    get_count_file = tmp_path / "get-count"
    state_file = tmp_path / "state"
    _write_executable(
        fake_bin / "databricks",
        """#!/usr/bin/env bash
set -eu
if [ "${DATABRICKS_AUTH_STORAGE:-}" != secure ]; then
  printf '%s\\n' 'secure auth storage was not forced' >&2
  exit 18
fi
printf '%s\\n' "$*" >> "$FAKE_CALL_LOG"
case "$*" in
  "--version") printf '%s\\n' 'Databricks CLI v1.7.0' ;;
  "auth describe"*)
    printf '%s' '{"username":"smoke@example.com","details":{"auth_type":"databricks-cli",'
    printf '%s\\n' '"host":"https://example.azuredatabricks.net"}}'
    ;;
  "auth token"*) printf '%s\\n' '{"access_token":"test-only-token"}' ;;
  "apps list"*)
    if [ "${FAKE_UNRELATED_APP:-0}" = 1 ]; then
      printf '%s' '[{"name":"unrelated","compute_size":"MEDIUM",'
      printf '%s\\n' '"compute_status":{"state":"STOPPED"}}]'
    else
      printf '%s\\n' '[]'
    fi
    ;;
  "warehouses list"*|"clusters list"*) printf '%s\\n' '[]' ;;
  "bundle validate"*|"bundle deploy"*) printf '%s\\n' '{}' ;;
  "bundle run"*) printf '%s\\n' 'ACTIVE' > "$FAKE_STATE_FILE" ;;
  "apps get"*)
    count=0
    if [ -f "$FAKE_GET_COUNT_FILE" ]; then count=$(cat "$FAKE_GET_COUNT_FILE"); fi
    count=$((count + 1))
    printf '%s\\n' "$count" > "$FAKE_GET_COUNT_FILE"
    if [ "${FAKE_FAIL_CLEANUP_GET_ONCE:-0}" = 1 ] && [ "$count" -eq 3 ]; then exit 17; fi
    state=STOPPED
    if [ -f "$FAKE_STATE_FILE" ]; then state=$(cat "$FAKE_STATE_FILE"); fi
    resources='[]'
    if [ "${FAKE_RESOURCE_BINDING:-0}" = 1 ]; then resources='[{"name":"unexpected"}]'; fi
    printf '%s' '{"url":"https://app.example.databricksapps.com","compute_size":"'
    printf '%s' "$FAKE_COMPUTE_SIZE"
    printf '%s' '","compute_status":'
    printf '{"state":"%s"},"resources":%s}\\n' "$state" "$resources"
    ;;
  "apps logs"*) printf '%s\\n' '{"event":"health_check","status":"alive"}' ;;
  "apps stop"*) printf '%s\\n' 'STOPPED' > "$FAKE_STATE_FILE" ;;
  *) printf 'unexpected databricks invocation: %s\\n' "$*" >&2; exit 9 ;;
esac
""",
    )
    _write_executable(
        fake_bin / "curl",
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" > "$FAKE_CURL_ARGS_LOG"
cat >/dev/null
if [ "${FAKE_CURL_FAIL:-0}" = 1 ]; then exit 22; fi
printf '%s' '{"status":"alive","check":"process_liveness",'
printf '%s' '"readiness":"not_evaluated","phase":"p0_smoke",'
printf '%s\\n' '"service":"dbtobsb","version":"0.1.0"}'
""",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "DBTOBSB_DATABRICKS_PROFILE": "smoke-u2m",
            "DBTOBSB_EXPECTED_HOST": "https://example.azuredatabricks.net",
            "DBTOBSB_EXPECTED_USER": "smoke@example.com",
            "FAKE_CALL_LOG": str(call_log),
            "FAKE_CURL_ARGS_LOG": str(curl_args_log),
            "FAKE_GET_COUNT_FILE": str(get_count_file),
            "FAKE_STATE_FILE": str(state_file),
            "FAKE_CURL_FAIL": "1" if fail_health else "0",
            "FAKE_FAIL_CLEANUP_GET_ONCE": "1" if fail_cleanup_get_once else "0",
            "FAKE_RESOURCE_BINDING": "1" if resource_binding else "0",
            "FAKE_COMPUTE_SIZE": compute_size,
            "FAKE_UNRELATED_APP": "1" if unrelated_app else "0",
        }
    )
    return environment


def test_smoke_wrapper_stops_after_success(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "bundle deploy" in calls
    assert "--select apps.dbtobsb_smoke" in calls
    assert "bundle run dbtobsb_smoke" in calls
    assert "apps logs dbtobsb-smoke" in calls
    assert "apps stop dbtobsb-smoke" in calls
    assert calls.index("bundle run dbtobsb_smoke") < calls.index("apps stop dbtobsb-smoke")
    assert (tmp_path / "state").read_text(encoding="utf-8").strip() == "STOPPED"
    assert "STOP VERIFIED: App compute state is STOPPED." in result.stdout
    curl_args = (tmp_path / "curl-args.log").read_text(encoding="utf-8").strip()
    assert curl_args == "--disable --proto =https --tlsv1.2 --config -"
    assert "test-only-token" not in curl_args
    assert "test-only-token" not in result.stdout
    assert "test-only-token" not in result.stderr


def test_smoke_wrapper_stops_after_health_failure(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path, fail_health=True),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "bundle run dbtobsb_smoke" in calls
    assert "apps stop dbtobsb-smoke" in calls
    assert (tmp_path / "state").read_text(encoding="utf-8").strip() == "STOPPED"


def test_smoke_wrapper_stops_even_when_first_cleanup_read_fails(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path, fail_cleanup_get_once=True),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "apps stop dbtobsb-smoke" in calls
    assert (tmp_path / "state").read_text(encoding="utf-8").strip() == "STOPPED"
    assert "STOP VERIFIED: App compute state is STOPPED." in result.stdout


def test_smoke_wrapper_rejects_live_resource_binding_and_stops(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path, resource_binding=True),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "live resource bindings" in result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "bundle run dbtobsb_smoke" not in calls
    assert "apps stop dbtobsb-smoke" in calls
    assert (tmp_path / "state").read_text(encoding="utf-8").strip() == "STOPPED"


def test_smoke_wrapper_rejects_unapproved_compute_size_and_stops(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path, compute_size="LARGE"),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Expected stopped MEDIUM deployment" in result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "bundle run dbtobsb_smoke" not in calls
    assert "apps stop dbtobsb-smoke" in calls
    assert (tmp_path / "state").read_text(encoding="utf-8").strip() == "STOPPED"


def test_smoke_wrapper_rejects_unrelated_workspace_before_mutation(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [repository_root / "scripts" / "smoke_databricks_app.sh"],
        cwd=repository_root,
        env=_smoke_environment(tmp_path, unrelated_app=True),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "P0 requires no unrelated Apps" in result.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "bundle validate" not in calls
    assert "bundle deploy" not in calls
    assert "bundle run" not in calls
    assert "apps stop" not in calls
