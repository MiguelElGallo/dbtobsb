"""Executable support-manifest contract tests."""

from __future__ import annotations

import json
from importlib.resources import files

import pytest

from dbtobsb_contracts import load_support_manifest, parse_support_manifest


def test_packaged_support_manifest_is_exact_and_final() -> None:
    manifest = load_support_manifest()

    assert manifest.contract_version == "dbtobsb.support.v1"
    assert manifest.release_state == "FINAL"
    assert manifest.platform["cloud"] == "AZURE_DATABRICKS"
    assert manifest.installation["launcher"] == "dbtobsb bootstrap"
    assert manifest.installation["runtime_trust_ledger"] == "NOT_IN_V0_4_SUPPORTED_PATH"
    assert len(manifest.customer_state["objects"]) == 9
    assert len(manifest.customer_state["direct_grants"]) == 18
    assert manifest.dbt["packages"]["dbt-core"] == "1.11.12"
    assert manifest.dbt["packages"]["dbt-databricks"] == "1.12.2"
    assert manifest.onboarding["policy_contract_version"] == "dbtobsb.dbt-policy.v1"
    assert manifest.onboarding["profiles_directory"] == "MATCH_PROJECT_DIRECTORY"
    assert manifest.onboarding["profile_target"] == {
        "profile_name_source": "DBT_PROJECT_YML_PROFILE_SCALAR",
        "profile_name_pattern": "^[A-Za-z][A-Za-z0-9_-]{0,127}$",
        "target_name": "dbtobsb",
        "connection_source": "PRODUCT_GENERATED_PROJECT_ROOT_PROFILE",
        "dbt_task_warehouse_id": "ABSENT_CUSTOM_PROFILE",
        "dbt_task_catalog": "ABSENT_CUSTOM_PROFILE",
        "dbt_task_schema": "ABSENT_CUSTOM_PROFILE",
        "dbt_task_profiles_directory": "MATCH_PROJECT_DIRECTORY",
        "output_keys": (
            "type",
            "method",
            "host",
            "http_path",
            "token",
            "catalog",
            "schema",
            "threads",
        ),
        "type": "databricks",
        "method": "http",
        "host": "INSTALLER_RENDERED_CANONICAL_WORKSPACE_SERVER_HOSTNAME",
        "host_source": "AUTHENTICATED_NAMED_DATABRICKS_CLI_PROFILE",
        "host_canonicalization": "HTTPS_AZURE_WORKSPACE_URL_TO_LOWERCASE_DNS_NAME",
        "http_path": "INSTALLER_RESOLVED_EXISTING_SQL_WAREHOUSE_HTTP_PATH",
        "token": "{{ env_var('DBT_ACCESS_TOKEN') }}",
        "catalog": "INSTALLER_RENDERED_LITERAL_CATALOG",
        "schema": "INSTALLER_RENDERED_LITERAL_SCHEMA",
        "threads": 1,
        "secret_values_in_snapshot": False,
        "run_as_authentication": "DATABRICKS_INJECTED_DBT_ACCESS_TOKEN",
        "operator_supplied_connection_fields": (),
    }
    assert manifest.app["landing_queries"] is False
    assert manifest.app["dashboard_rendering"] == (
        "NATIVE_SERVER_RENDERED_APP_NO_EXTERNAL_DASHBOARD_RESOURCE"
    )
    assert manifest.app["dashboard_metrics"] == (
        "FAILED_NODE_RESULTS_PER_RUN",
        "MODEL_RESULTS_PER_RUN",
    )
    assert manifest.lifecycle["default_action"] == "STOP"
    assert "ZERO_PRODUCT_STARTED_COMPUTE" in manifest.qualification["live_cases"]
    assert manifest.distribution["marketplace"] is False
    assert manifest.distribution["required_external_telemetry"] is False
    assert len(manifest.canonical_sha256) == 64


@pytest.mark.parametrize(
    ("path", "value", "code"),
    [
        (("release_state",), "SUPPORTED", "BASELINE"),
        (("distribution", "marketplace"), True, "DISTRIBUTION"),
        (("governed_output", "anonymous_usage"), True, "OUTPUT_POLICY"),
        (("governed_output", "raw_archive_custody"), "OPTIONAL", "OUTPUT_POLICY"),
        (("dbt", "packages", "dbt-core"), "1.12.0", "PACKAGE_VERSION"),
        (("dbt", "manifest_schema_exceptions"), [], "SCHEMA_EXCEPTION"),
        (("installation", "mode"), "SEPARATED_DUTIES", "INSTALLATION"),
        (("onboarding", "source_type"), "GIT", "ONBOARDING"),
        (("onboarding", "profile_target", "target_name"), "dev", "ONBOARDING"),
        (
            ("onboarding", "profile_target", "token"),
            "{{ env_var('DATABRICKS_TOKEN') }}",
            "ONBOARDING",
        ),
        (
            ("onboarding", "profile_target", "host_source"),
            "OPERATOR_INPUT",
            "ONBOARDING",
        ),
        (
            ("onboarding", "profile_target", "operator_supplied_connection_fields"),
            ["host"],
            "ONBOARDING",
        ),
        (
            ("onboarding", "profile_target", "dbt_task_warehouse_id"),
            "PLATFORM_GENERATED_PROFILE",
            "ONBOARDING",
        ),
        (("app", "landing_queries"), True, "APP"),
        (("lifecycle", "default_action"), "DELETE_UNINSTALL", "LIFECYCLE"),
        (("qualification", "live_cases"), [], "QUALIFICATION"),
    ],
)
def test_manifest_rejects_weakened_or_unreviewed_values(
    path: tuple[str, ...], value: object, code: str
) -> None:
    packaged = load_support_manifest()
    raw = json.loads(files("dbtobsb_contracts").joinpath("support-manifest-v1.json").read_text())
    current = raw
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value

    with pytest.raises(ValueError, match=f"DBTOBSB_SUPPORT_MANIFEST_{code}"):
        parse_support_manifest(json.dumps(raw).encode())

    assert packaged.release_state == "FINAL"


def test_manifest_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="DUPLICATE_KEY"):
        parse_support_manifest(b'{"contract_version":"a","contract_version":"b"}')


def test_loaded_manifest_cannot_diverge_from_its_digest_by_nested_mutation() -> None:
    manifest = load_support_manifest()
    original_digest = manifest.canonical_sha256

    assert manifest.dbt["command_sequence"] == ("OPTIONAL_DEPS", "REQUIRED_BUILD")
    with pytest.raises(TypeError):
        manifest.dbt["command_sequence"][0] = "ARBITRARY"  # type: ignore[index]
    with pytest.raises(TypeError):
        manifest.dbt["packages"]["dbt-core"] = "1.12.0"  # type: ignore[index]
    with pytest.raises(TypeError):
        manifest.customer_state["objects"][0]["name"] = "foreign"  # type: ignore[index]
    with pytest.raises(TypeError):
        manifest.lifecycle["operations"][0]["action"] = "ARBITRARY"  # type: ignore[index]
    assert manifest.canonical_sha256 == original_digest
