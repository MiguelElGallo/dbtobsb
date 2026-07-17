"""Install-specific packaged binding contract tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest
from dbtobsb_contracts import (
    DbtRuntimePolicyInputs,
    DbtRuntimeTarget,
    render_dbt_runtime_policy,
)

from dbtobsb_collector import deployment
from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationBinding,
    _installation_id,
)
from dbtobsb_collector.deployment import (
    parse_deployed_installation_seal,
    render_deployed_installation_seal,
)


def _policy(*, selector: str = "weather_release"):
    source = {
        "dbt_project.yml": "1" * 64,
        "models/weather.sql": "2" * 64,
        "profiles.yml": "3" * 64,
        "selectors.yml": "4" * 64,
    }
    source_contract = hashlib.sha256(
        json.dumps(
            {
                "domain": "dbtobsb.dbt-source-contract.v1",
                "source_sha256": source,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    return render_dbt_runtime_policy(
        DbtRuntimePolicyInputs(
            source_sha256=source,
            source_contract_sha256=source_contract,
            project_directory=f"./dbtobsb_onboarding/{source_contract}/project",
            profile_name="customer_weather",
            selector=selector,
            include_deps=False,
            dependency_definition_files=(),
            dependency_lock_sha256=None,
            target=DbtRuntimeTarget(
                host="adb-1234567890123456.10.azuredatabricks.net",
                warehouse_id="0123456789abcdef",
                http_path="/sql/1.0/warehouses/0123456789abcdef",
                catalog="analytics",
                schema="weather_prod",
                artifact_catalog="observability",
                artifact_schema="dbtobsb",
            ),
        )
    )


def _binding_document() -> dict[str, str | int | bool]:
    policy = _policy()
    binding = InstallationBinding(
        workspace_id=101,
        warehouse_id="0123456789abcdef",
        source_contract_sha256=policy.source_contract_sha256,
        expected_runtime_policy_sha256=policy.expected_runtime_policy_sha256,
        observed_job_id=201,
        collector_job_id=202,
        reconciler_job_id=203,
        observed_service_principal_name="observed-sp",
        collector_service_principal_name="collector-sp",
        job_manager_group_name="job-managers",
        collector_environment_sha256="b" * 64,
    )
    return {
        "manifest_version": OBJECT_MANIFEST_VERSION,
        "object_contract_sha256": OBJECT_CONTRACT_SHA256,
        "source_contract_sha256": policy.source_contract_sha256,
        "expected_runtime_policy_sha256": policy.expected_runtime_policy_sha256,
        "base_observability_contract_sha256": BASE_OBSERVABILITY_CONTRACT_SHA256,
        "installation_id": _installation_id(binding, catalog="catalog", schema="evidence"),
        "workspace_id": 101,
        "evidence_catalog": "catalog",
        "evidence_schema": "evidence",
        "warehouse_id": "0123456789abcdef",
        "observed_job_id": 201,
        "collector_job_id": 202,
        "reconciler_job_id": 203,
        "observed_service_principal_name": "observed-sp",
        "collector_service_principal_name": "collector-sp",
        "job_manager_group_name": "job-managers",
        "collector_environment_sha256": "b" * 64,
        "artifact_state": "FINALIZED_RUNTIME",
        "finalization_required": False,
    }


def _raw(document: dict[str, str | int | bool]) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def test_binding_parses_only_the_exact_release_and_location() -> None:
    seal = parse_deployed_installation_seal(_raw(_binding_document()), policy=_policy())

    assert seal.workspace_id == 101
    assert seal.evidence_catalog == "catalog"
    assert seal.evidence_schema == "evidence"
    assert seal.collector_job_id == 202
    assert seal.base_observability_contract_sha256 == BASE_OBSERVABILITY_CONTRACT_SHA256


def test_binding_renderer_is_canonical_and_round_trips() -> None:
    seal = parse_deployed_installation_seal(_raw(_binding_document()), policy=_policy())

    rendered = render_deployed_installation_seal(seal, policy=_policy())

    assert rendered.endswith(b"\n")
    assert rendered.rstrip(b"\n") == _raw(_binding_document())
    assert parse_deployed_installation_seal(rendered, policy=_policy()) == seal


def test_binding_renderer_rejects_a_constructed_invalid_seal() -> None:
    seal = parse_deployed_installation_seal(_raw(_binding_document()), policy=_policy())
    invalid = replace(seal, warehouse_id="not-a-warehouse-id")

    with pytest.raises(ValueError, match="DBTOBSB_DEPLOYMENT_BINDING_INVALID"):
        render_deployed_installation_seal(invalid, policy=_policy())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workspace_id", 0),
        ("evidence_catalog", "copied"),
        ("evidence_schema", " copied"),
        ("collector_job_id", 0),
        ("expected_runtime_policy_sha256", "0" * 64),
        ("base_observability_contract_sha256", "0" * 64),
    ],
)
def test_binding_rejects_drift_or_relocation(field: str, value: str | int) -> None:
    document = _binding_document()
    document[field] = value

    with pytest.raises(ValueError, match="DBTOBSB_DEPLOYMENT_BINDING_INVALID"):
        parse_deployed_installation_seal(_raw(document), policy=_policy())


def test_binding_rejects_unknown_and_duplicate_fields() -> None:
    document = _binding_document()
    document["caller"] = "value"
    with pytest.raises(ValueError, match="DBTOBSB_DEPLOYMENT_BINDING_INVALID"):
        parse_deployed_installation_seal(_raw(document), policy=_policy())

    duplicate = _raw(_binding_document())[:-1] + b',"workspace_id":999}'
    with pytest.raises(ValueError, match="DBTOBSB_DEPLOYMENT_BINDING_INVALID"):
        parse_deployed_installation_seal(duplicate, policy=_policy())


def test_pre_deploy_candidate_is_parseable_but_not_a_final_runtime_binding() -> None:
    document = _binding_document()
    document["artifact_state"] = "PRE_DEPLOY_ARTIFACT_CANDIDATE"
    document["finalization_required"] = True

    seal = parse_deployed_installation_seal(_raw(document), policy=_policy())

    assert seal.finalization_required is True
    assert seal.artifact_state == "PRE_DEPLOY_ARTIFACT_CANDIDATE"


def test_runtime_loader_rejects_a_pre_deploy_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = _binding_document()
    document["artifact_state"] = "PRE_DEPLOY_ARTIFACT_CANDIDATE"
    document["finalization_required"] = True
    resources = {
        "_generated/dbt-policy-v1.json": _policy().canonical_bytes,
        "_generated/deployment-binding-v1.json": _raw(document),
    }

    class _Resource:
        def __init__(self, name: str | None = None) -> None:
            self.name = name

        def joinpath(self, name: str):
            return _Resource(name)

        def read_bytes(self) -> bytes:
            assert self.name is not None
            return resources[self.name]

    resource = _Resource()
    monkeypatch.setattr(deployment, "files", lambda package: resource)

    with pytest.raises(RuntimeError, match="DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED"):
        deployment.load_deployed_installation_seal()


def test_binding_rejects_a_policy_from_another_installed_project() -> None:
    with pytest.raises(ValueError, match="DBTOBSB_DEPLOYMENT_BINDING_INVALID"):
        parse_deployed_installation_seal(
            _raw(_binding_document()),
            policy=_policy(selector="other_release"),
        )
