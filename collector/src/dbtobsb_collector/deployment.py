"""Install-specific, wheel-packaged runtime binding with no caller-selected target."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from typing import Any

from dbtobsb_contracts import DbtRuntimePolicySnapshot, parse_dbt_runtime_policy

from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationBinding,
    InstallationSeal,
    _installation_id,
    _validate_installation_binding,
)
from dbtobsb_collector.naming import quote_identifier

_BINDING_RESOURCE = "_generated/deployment-binding-v1.json"
_POLICY_RESOURCE = "_generated/dbt-policy-v1.json"
_BINDING_KEYS = {
    "manifest_version",
    "object_contract_sha256",
    "source_contract_sha256",
    "expected_runtime_policy_sha256",
    "base_observability_contract_sha256",
    "installation_id",
    "workspace_id",
    "evidence_catalog",
    "evidence_schema",
    "warehouse_id",
    "observed_job_id",
    "collector_job_id",
    "reconciler_job_id",
    "observed_service_principal_name",
    "collector_service_principal_name",
    "job_manager_group_name",
    "collector_environment_sha256",
    "artifact_state",
    "finalization_required",
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class DeployedRuntimeContract:
    """Install-specific policy and binding loaded from the same collector artifact."""

    seal: InstallationSeal
    policy: DbtRuntimePolicySnapshot


def parse_deployed_installation_seal(
    raw: bytes,
    *,
    policy: DbtRuntimePolicySnapshot,
) -> InstallationSeal:
    """Parse the closed install-specific binding packaged with the collector wheel."""
    try:
        document = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID") from None
    if not isinstance(document, dict) or set(document) != _BINDING_KEYS:
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    string_fields = _BINDING_KEYS - {
        "workspace_id",
        "observed_job_id",
        "collector_job_id",
        "reconciler_job_id",
        "finalization_required",
    }
    if (
        any(not isinstance(document[field], str) for field in string_fields)
        or any(
            type(document[field]) is not int
            for field in (
                "workspace_id",
                "observed_job_id",
                "collector_job_id",
                "reconciler_job_id",
            )
        )
        or type(document["finalization_required"]) is not bool
    ):
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    binding = InstallationBinding(
        workspace_id=document["workspace_id"],
        warehouse_id=document["warehouse_id"],
        source_contract_sha256=document["source_contract_sha256"],
        expected_runtime_policy_sha256=document["expected_runtime_policy_sha256"],
        observed_job_id=document["observed_job_id"],
        collector_job_id=document["collector_job_id"],
        reconciler_job_id=document["reconciler_job_id"],
        observed_service_principal_name=document["observed_service_principal_name"],
        collector_service_principal_name=document["collector_service_principal_name"],
        job_manager_group_name=document["job_manager_group_name"],
        collector_environment_sha256=document["collector_environment_sha256"],
    )
    try:
        _validate_installation_binding(binding)
    except ValueError:
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID") from None
    if not isinstance(policy, DbtRuntimePolicySnapshot):
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    catalog = document["evidence_catalog"]
    schema = document["evidence_schema"]
    if (
        not catalog
        or catalog != catalog.strip()
        or not schema
        or schema != schema.strip()
        or document["manifest_version"] != OBJECT_MANIFEST_VERSION
        or document["object_contract_sha256"] != OBJECT_CONTRACT_SHA256
        or document["source_contract_sha256"] != policy.source_contract_sha256
        or document["expected_runtime_policy_sha256"] != policy.expected_runtime_policy_sha256
        or document["base_observability_contract_sha256"] != BASE_OBSERVABILITY_CONTRACT_SHA256
        or document["installation_id"] != _installation_id(binding, catalog=catalog, schema=schema)
        or (
            document["artifact_state"],
            document["finalization_required"],
        )
        not in {
            ("PRE_DEPLOY_ARTIFACT_CANDIDATE", True),
            ("FINALIZED_RUNTIME", False),
        }
    ):
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    return InstallationSeal(
        manifest_version=OBJECT_MANIFEST_VERSION,
        object_contract_sha256=OBJECT_CONTRACT_SHA256,
        source_contract_sha256=policy.source_contract_sha256,
        expected_runtime_policy_sha256=policy.expected_runtime_policy_sha256,
        base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
        installation_id=document["installation_id"],
        workspace_id=binding.workspace_id,
        evidence_catalog=catalog,
        evidence_schema=schema,
        warehouse_id=binding.warehouse_id,
        observed_job_id=binding.observed_job_id,
        collector_job_id=binding.collector_job_id,
        reconciler_job_id=binding.reconciler_job_id,
        observed_service_principal_name=binding.observed_service_principal_name,
        collector_service_principal_name=binding.collector_service_principal_name,
        job_manager_group_name=binding.job_manager_group_name,
        collector_environment_sha256=binding.collector_environment_sha256,
        artifact_state=document["artifact_state"],
        finalization_required=document["finalization_required"],
    )


def render_deployed_installation_seal(
    seal: InstallationSeal,
    *,
    policy: DbtRuntimePolicySnapshot,
) -> bytes:
    """Render one canonical binding and prove the runtime parser accepts it exactly."""
    document = asdict(seal)
    raw = json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
    try:
        parsed = parse_deployed_installation_seal(raw, policy=policy)
    except ValueError:
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID") from None
    if parsed != seal:
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    return raw + b"\n"


def construct_deployed_installation_seal(
    *,
    binding: InstallationBinding,
    evidence_catalog: str,
    evidence_schema: str,
    artifact_state: str = "FINALIZED_RUNTIME",
    finalization_required: bool = False,
    policy: DbtRuntimePolicySnapshot,
) -> InstallationSeal:
    """Construct the exact install-specific seal from typed, already-attested values."""
    try:
        _validate_installation_binding(binding)
        if (
            evidence_catalog != evidence_catalog.strip()
            or evidence_schema != evidence_schema.strip()
        ):
            raise ValueError
        quote_identifier(evidence_catalog)
        quote_identifier(evidence_schema)
        if not isinstance(policy, DbtRuntimePolicySnapshot):
            raise ValueError
        seal = InstallationSeal(
            manifest_version=OBJECT_MANIFEST_VERSION,
            object_contract_sha256=OBJECT_CONTRACT_SHA256,
            source_contract_sha256=policy.source_contract_sha256,
            expected_runtime_policy_sha256=policy.expected_runtime_policy_sha256,
            base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
            installation_id=_installation_id(
                binding,
                catalog=evidence_catalog,
                schema=evidence_schema,
            ),
            workspace_id=binding.workspace_id,
            evidence_catalog=evidence_catalog,
            evidence_schema=evidence_schema,
            warehouse_id=binding.warehouse_id,
            observed_job_id=binding.observed_job_id,
            collector_job_id=binding.collector_job_id,
            reconciler_job_id=binding.reconciler_job_id,
            observed_service_principal_name=binding.observed_service_principal_name,
            collector_service_principal_name=binding.collector_service_principal_name,
            job_manager_group_name=binding.job_manager_group_name,
            collector_environment_sha256=binding.collector_environment_sha256,
            artifact_state=artifact_state,
            finalization_required=finalization_required,
        )
        render_deployed_installation_seal(seal, policy=policy)
    except (TypeError, ValueError):
        raise ValueError("DBTOBSB_DEPLOYMENT_BINDING_INVALID") from None
    return seal


def load_deployed_runtime_contract() -> DeployedRuntimeContract:
    """Load the sealed policy and binding from this wheel, never argv or environment."""
    try:
        package = files("dbtobsb_collector")
        policy_raw = package.joinpath(_POLICY_RESOURCE).read_bytes()
        binding_raw = package.joinpath(_BINDING_RESOURCE).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        raise RuntimeError("DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE") from None
    try:
        policy = parse_dbt_runtime_policy(policy_raw)
        seal = parse_deployed_installation_seal(binding_raw, policy=policy)
        if seal.finalization_required or seal.artifact_state != "FINALIZED_RUNTIME":
            raise RuntimeError("DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED")
        return DeployedRuntimeContract(seal=seal, policy=policy)
    except ValueError:
        raise RuntimeError("DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID") from None


def load_deployed_installation_seal() -> InstallationSeal:
    """Load only the install-specific binding for compatibility with bootstrap callers."""

    return load_deployed_runtime_contract().seal


def load_deployed_runtime_policy() -> DbtRuntimePolicySnapshot:
    """Load only the immutable installed dbt policy from the collector artifact."""

    return load_deployed_runtime_contract().policy
