"""Closed generated-onboarding Bundle and source-attestation tests."""

from __future__ import annotations

import json
import runpy
import shutil
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

ROOT = Path(__file__).parents[2]
BUNDLE = ROOT / "databricks.yml"
CHECKER = runpy.run_path(str(ROOT / "contracts" / "scripts" / "check_bundle_commands.py"))
validate_bundle = cast(Callable[[Path], None], CHECKER["validate_bundle"])
bundle_failure_diagnostic = CHECKER["bundle_failure_diagnostic"]
bundle_success_diagnostic = CHECKER["bundle_success_diagnostic"]
print_diagnostic = CHECKER["_print_diagnostic"]
BundleContractError = CHECKER["BundleContractError"]


def _document() -> dict[str, Any]:
    value = yaml.safe_load(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    overlay = yaml.safe_load((ROOT / ".dbtobsb-observed.generated.yml").read_text())
    value["resources"]["jobs"]["dbtobsb_observed"] = deepcopy(
        overlay["resources"]["jobs"]["dbtobsb_observed"]
    )
    return value


def _write_bundle(tmp_path: Path, document: dict[str, Any]) -> Path:
    document = deepcopy(document)
    observed = document["resources"]["jobs"].pop("dbtobsb_observed")
    shutil.copytree(ROOT / "dbtobsb_onboarding", tmp_path / "dbtobsb_onboarding")
    (tmp_path / ".dbtobsb-observed.generated.yml").write_text(
        yaml.safe_dump(
            {"resources": {"jobs": {"dbtobsb_observed": observed}}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    path = tmp_path / "databricks.yml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _observed_job(document: dict[str, Any]) -> dict[str, Any]:
    return document["resources"]["jobs"]["dbtobsb_observed"]


def _generated_project(bundle_path: Path, document: dict[str, Any]) -> Path:
    parameters = _dbt_task(document)["parameters"]
    relative = parameters[parameters.index("--project_directory") + 1].removeprefix(
        "${workspace.file_path}/"
    )
    return bundle_path / relative


def _checked_in_source_relatives() -> tuple[str, ...]:
    project = _generated_project(ROOT, _document())
    return tuple(
        path.relative_to(project).as_posix()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    )


def _dbt_wrapper(document: dict[str, Any]) -> dict[str, Any]:
    return _observed_job(document)["tasks"][0]


def _dbt_task(document: dict[str, Any]) -> dict[str, Any]:
    return _dbt_wrapper(document)["python_wheel_task"]


def _collector_wrapper(document: dict[str, Any]) -> dict[str, Any]:
    return _observed_job(document)["tasks"][1]


def _collector_job(document: dict[str, Any]) -> dict[str, Any]:
    return document["resources"]["jobs"]["dbtobsb_collector"]


def _dbt_environment(document: dict[str, Any]) -> dict[str, Any]:
    return _observed_job(document)["environments"][0]["spec"]


def test_checked_in_bundle_matches_the_generated_onboarding_contract() -> None:
    validate_bundle(BUNDLE)


def test_success_diagnostic_limits_acceptance_to_local_unsealed_preview(
    capsys: pytest.CaptureFixture[str],
) -> None:
    diagnostic = bundle_success_diagnostic()

    print_diagnostic(diagnostic, output_format="human")
    human = capsys.readouterr().out
    assert "Accepted for the supported private release" in human
    assert "Installed deployment integrity is not sealed" in human
    assert human.count("Next action:") == 1

    print_diagnostic(diagnostic, output_format="json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "accepted"
    assert payload["code"] == "DBTOBSB_BUNDLE_DBT_CONTRACT_OK"
    assert payload["responsible_actor"] == "deployment/seal verifier"
    assert payload["action"] == ("Continue with the documented deployment-and-seal workflow.")


@pytest.mark.parametrize(
    ("code", "component"),
    [
        ("DBTOBSB_BUNDLE_TARGET_INVALID", "deployment target binding"),
        ("DBTOBSB_BUNDLE_DBT_COMMAND_DRIFT", "dbt runtime contract"),
        ("DBTOBSB_BUNDLE_COLLECT_TASK_INVALID", "collector handoff"),
        ("DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT", "onboarded dbt source"),
    ],
)
def test_failure_diagnostic_is_actionable_and_contains_no_observed_values(
    code: str, component: str
) -> None:
    canaries = (
        "SENSITIVE_ID_123",
        "/Workspace/Users/person",
        "dbt build --selector secret",
        "warehouse_id: secret",
        "SELECT * FROM secret",
    )
    diagnostic = bundle_failure_diagnostic(BundleContractError(code))
    rendered = json.dumps(diagnostic.as_dict(), sort_keys=True)

    assert diagnostic.outcome == "denied"
    assert diagnostic.component == component
    assert diagnostic.consequence == "No Databricks Job was run by this local check."
    assert diagnostic.responsible_actor == "deployment/seal verifier"
    assert diagnostic.human().count("Next action:") == 1
    assert not any(canary in rendered for canary in canaries)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("databricks_cli_version", ">= 1.8.0", "CLI_VERSION_DRIFT"),
        ("engine", "terraform", "ENGINE_DRIFT"),
        ("name", "caller-controlled", "METADATA_INVALID"),
    ],
)
def test_bundle_metadata_drift_is_rejected(
    tmp_path: Path, field: str, value: str, code: str
) -> None:
    document = _document()
    document["bundle"][field] = value

    with pytest.raises(ValueError, match=f"DBTOBSB_BUNDLE_{code}"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_include_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["include"] = ["caller-controlled.yml"]

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_INCLUDE_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_generated_onboarding_sync_include_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["sync"]["include"] = ["caller-controlled/**"]

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_SYNC_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_unknown_root_extension_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["unknown_future_root"] = ["caller-controlled"]

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_ROOT_EXTENSION_UNSUPPORTED"):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize("overlay", ["variables", "resources", "git_source", "mode"])
def test_target_overlays_and_extensions_are_rejected(tmp_path: Path, overlay: str) -> None:
    document = _document()
    document["targets"]["smoke"][overlay] = {"caller": "controlled"}

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_TARGET_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_additional_target_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["targets"]["production"] = document["targets"]["smoke"]

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_TARGET_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_fixed_evidence_variable_default_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["variables"]["evidence_schema"]["default"] = "caller_controlled"

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_VARIABLES_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_runtime_wheel_filename_default_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["variables"]["collector_wheel_filename"]["default"] = "caller.whl"

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_VARIABLES_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_runtime_artifact_source_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    document["artifacts"]["collector_wheel"]["files"][0]["source"] = "./caller.whl"

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_ARTIFACTS_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("package_name", "caller", "DBT_TASK_CONFIGURATION_UNSUPPORTED"),
        ("entry_point", "collect", "DBT_TASK_CONFIGURATION_UNSUPPORTED"),
        (
            "parameters",
            ["--project_directory", "./another_project"],
            "DBT_TASK_CONFIGURATION_UNSUPPORTED",
        ),
    ],
)
def test_exact_dbt_task_source_and_target_drift_is_rejected(
    tmp_path: Path, field: str, value: object, code: str
) -> None:
    document = _document()
    _dbt_task(document)[field] = value

    with pytest.raises(ValueError, match=f"DBTOBSB_BUNDLE_{code}"):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize(
    ("location", "field"),
    [
        ("job", "git_source"),
        ("job", "parameters"),
        ("task", "git_source"),
        ("task", "parameters"),
        ("task", "libraries"),
        ("dbt_task", "warehouse_id"),
        ("dbt_task", "unknown_future_field"),
    ],
)
def test_observed_job_and_task_extensions_are_rejected(
    tmp_path: Path, location: str, field: str
) -> None:
    document = _document()
    target = {
        "job": _observed_job(document),
        "task": _dbt_wrapper(document),
        "dbt_task": _dbt_task(document),
    }[location]
    target[field] = {"caller": "controlled"}

    code = (
        "DBTOBSB_BUNDLE_DBT_JOB_INVALID"
        if location == "job"
        else "DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED"
    )
    with pytest.raises(ValueError, match=code):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("environment_key", "caller"),
        ("timeout_seconds", 0),
        ("max_retries", 1),
        ("retry_on_timeout", True),
    ],
)
def test_dbt_task_wrapper_drift_is_rejected(tmp_path: Path, field: str, value: object) -> None:
    document = _document()
    _dbt_wrapper(document)[field] = value

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_collector_wrapper_extension_is_rejected(tmp_path: Path) -> None:
    document = _document()
    _collector_wrapper(document)["git_source"] = {"git_url": "https://invalid"}

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_COLLECT_TASK_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_runtime_bundle_contains_no_privileged_bootstrap_job(tmp_path: Path) -> None:
    document = _document()
    document["resources"]["jobs"]["dbtobsb_bootstrap"] = {"name": "caller"}

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_JOBS_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_collector_wheel_arguments_are_exact_and_positional(tmp_path: Path) -> None:
    document = _document()
    wheel = _collector_job(document)["tasks"][0]["python_wheel_task"]
    wheel["named_parameters"] = {"catalog": "caller-controlled"}

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize("name", ["catalog", "schema", "observed_job_id"])
def test_collector_job_has_no_overridable_installation_binding(tmp_path: Path, name: str) -> None:
    document = _document()
    _collector_job(document)["parameters"].append({"name": name, "default": "caller"})

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_observed_task_order_and_membership_are_exact(tmp_path: Path) -> None:
    document = _document()
    _observed_job(document)["tasks"].reverse()

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_DBT_TASK_INVALID"):
        validate_bundle(_write_bundle(tmp_path, document))


@pytest.mark.parametrize("field", ["environment_variables", "spark_conf", "unknown_future"])
def test_any_dbt_environment_extension_is_rejected(tmp_path: Path, field: str) -> None:
    document = _document()
    _dbt_environment(document)[field] = {"DBT_ENGINE_FULL_REFRESH": "true"}

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_DBT_ENVIRONMENT_OVERRIDE_UNSUPPORTED"):
        validate_bundle(_write_bundle(tmp_path, document))


def test_dependency_or_serverless_client_drift_is_rejected(tmp_path: Path) -> None:
    document = _document()
    _dbt_environment(document)["dependencies"].reverse()

    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_DBT_DEPENDENCY_DRIFT"):
        validate_bundle(_write_bundle(tmp_path, document))

    document = _document()
    _dbt_environment(document)["client"] = "4"
    with pytest.raises(ValueError, match="DBTOBSB_BUNDLE_SERVERLESS_CLIENT_DRIFT"):
        validate_bundle(_write_bundle(tmp_path / "client", document))


@pytest.mark.parametrize(
    ("field", "value"),
    [("profile", "other"), ("require-dbt-version", ">=1.0")],
)
def test_exact_project_profile_and_required_version_are_attested(
    tmp_path: Path, field: str, value: object
) -> None:
    bundle_path = _write_bundle(tmp_path, _document())
    project_path = _generated_project(tmp_path, _document()) / "dbt_project.yml"
    project = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project[field] = value
    project_path.write_text(yaml.safe_dump(project, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT"):
        validate_bundle(bundle_path)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("target",), "other"),
        (("outputs", "dbtobsb", "type"), "spark"),
        (("outputs", "dbtobsb", "catalog"), "{{ env_var('CALLER') }}"),
        (("outputs", "dbtobsb", "http_path"), "caller"),
    ],
)
def test_exact_profile_target_adapter_and_env_shape_are_attested(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    bundle_path = _write_bundle(tmp_path, _document())
    profile_path = _generated_project(tmp_path, _document()) / "profiles.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile_name = next(iter(profile))
    current = profile[profile_name]
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT"):
        validate_bundle(bundle_path)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("name",), "caller"),
        (("definition", "method"), "tag"),
        (("definition", "value"), "caller"),
    ],
)
def test_exact_selector_definition_is_attested(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    bundle_path = _write_bundle(tmp_path, _document())
    selector_path = _generated_project(tmp_path, _document()) / "selectors.yml"
    selectors = yaml.safe_load(selector_path.read_text(encoding="utf-8"))
    current = selectors["selectors"][0]
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value
    selector_path.write_text(yaml.safe_dump(selectors, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT"):
        validate_bundle(bundle_path)


@pytest.mark.parametrize("relative", _checked_in_source_relatives())
def test_onboarded_source_byte_mutation_is_rejected(tmp_path: Path, relative: str) -> None:
    document = _document()
    bundle_path = _write_bundle(tmp_path, document)
    source = _generated_project(tmp_path, document) / relative
    source.write_bytes(source.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT"):
        validate_bundle(bundle_path)


def test_extra_or_missing_onboarded_source_file_is_rejected(tmp_path: Path) -> None:
    document = _document()
    bundle_path = _write_bundle(tmp_path, document)
    project = _generated_project(tmp_path, document)
    macro = project / "macros" / "caller.sql"
    macro.parent.mkdir()
    macro.write_text("{% macro caller() %}{% endmacro %}", encoding="utf-8")

    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_FILE_SET_DRIFT"):
        validate_bundle(bundle_path)

    macro.unlink()
    macro.parent.rmdir()
    model = next(
        relative
        for relative in _checked_in_source_relatives()
        if relative.startswith("models/") and relative.endswith(".sql")
    )
    (project / model).unlink()
    with pytest.raises(ValueError, match="DBTOBSB_ONBOARDED_SOURCE_FILE_SET_DRIFT"):
        validate_bundle(bundle_path)
