"""Parity checks between the machine support manifest and its human release contract."""

from __future__ import annotations

from pathlib import Path

from dbtobsb_contracts import load_support_manifest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_RELEASE_CONTRACT = _REPOSITORY_ROOT / "docs" / "releases" / "v0.5.0-support-contract.md"


def _release_text() -> str:
    return _RELEASE_CONTRACT.read_text(encoding="utf-8")


def test_release_contract_names_normative_manifest_and_digest() -> None:
    manifest = load_support_manifest()
    text = _release_text()

    assert f"`{manifest.contract_version}`" in text
    assert f"`{manifest.canonical_sha256}`" in text
    assert "The packaged `dbtobsb.support.v1` manifest is normative" in text


def test_release_contract_projects_installation_objects_and_privileges() -> None:
    manifest = load_support_manifest()
    text = _release_text()

    assert f"`{manifest.installation['mode']}`" in text
    assert manifest.installation["launcher"] in text
    assert manifest.installation["schema_requirement"] == (
        "EXISTING_DEDICATED_SCHEMA_SESSION_USER_IS_OWNER"
    )
    for item in manifest.customer_state["objects"]:
        assert f"`{item['name']}`" in text
    for grant in manifest.customer_state["direct_grants"]:
        for privilege in grant["privileges"]:
            assert f"`{privilege}`" in text
    assert "No runtime-trust ledger" in text


def test_release_contract_projects_full_dbt_and_onboarding_boundary() -> None:
    manifest = load_support_manifest()
    text = _release_text()

    for package, version in manifest.dbt["packages"].items():
        assert f"`{package}`" in text
        assert f"`{version}`" in text
    exception = manifest.dbt["manifest_schema_exceptions"][0]
    assert f"`{exception['document_path']}`" in text
    assert str(manifest.dbt["structured_log_version"]) in text
    assert f"`{manifest.onboarding['policy_contract_version']}`" in text
    assert f"`{manifest.dbt['selector_pattern']}`" in text
    assert f"`{manifest.onboarding['dependency_lock_file']}`" in text
    profile_target = manifest.onboarding["profile_target"]
    assert f"`{profile_target['profile_name_source']}`" in text
    assert f"`{profile_target['profile_name_pattern']}`" in text
    assert f"`{profile_target['target_name']}`" in text
    assert f"`{profile_target['host']}`" in text
    assert f"`{profile_target['host_source']}`" in text
    assert f"`{profile_target['host_canonicalization']}`" in text
    assert f"`{profile_target['token']}`" in text
    assert f"`{profile_target['http_path']}`" in text
    assert profile_target["operator_supplied_connection_fields"] == ()
    assert "operator supplies none of the connection or generated-command fields" in text
    assert "The dbt task omits `warehouse_id`, `catalog`, and `schema`" in text
    assert "Raw custody is mandatory" in text


def test_release_contract_projects_app_lifecycle_and_release_gates() -> None:
    manifest = load_support_manifest()
    text = _release_text()

    assert manifest.app["initial_state"] == "STOPPED"
    for command in {operation["command"] for operation in manifest.lifecycle["operations"]}:
        assert f"`{command}`" in text
    for resource in manifest.app["resources"]:
        if resource != "APP_QUERY_WAREHOUSE":
            assert f"`{resource}`" in text
    assert "performs no evidence query" in text
    assert "auto-start the bound SQL warehouse" in text
    assert "zero product-started compute left running" in text
    assert "not certified or attested against a regulatory framework" in text
