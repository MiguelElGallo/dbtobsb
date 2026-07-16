"""Public contracts used by installation, capture, collection, and the App."""

from dbtobsb_contracts.base_observability import RUNTIME_TRUST_PROVIDER_CONTRACT_SHA256
from dbtobsb_contracts.commands import (
    AttemptIdentity,
    DbtOutputExpectation,
    GeneratedDbtCommand,
    InstalledDbtPolicy,
    demo_installed_policy,
    expected_dbt_output,
    generate_dbt_commands,
)
from dbtobsb_contracts.configuration import (
    DbtConfigurationAssessment,
    DbtConfigurationFinding,
    DbtConfigurationState,
    assess_dbt_configuration,
    fixed_demo_configuration_snapshot,
)
from dbtobsb_contracts.diagnostics import OperatorDiagnostic
from dbtobsb_contracts.policy import (
    DbtRuntimePolicyError,
    DbtRuntimePolicyInputs,
    DbtRuntimePolicySnapshot,
    DbtRuntimeTarget,
    parse_dbt_runtime_policy,
    render_dbt_runtime_policy,
)
from dbtobsb_contracts.support import SupportManifest, load_support_manifest, parse_support_manifest

__all__ = [
    "RUNTIME_TRUST_PROVIDER_CONTRACT_SHA256",
    "AttemptIdentity",
    "DbtConfigurationAssessment",
    "DbtConfigurationFinding",
    "DbtConfigurationState",
    "DbtOutputExpectation",
    "DbtRuntimePolicyError",
    "DbtRuntimePolicyInputs",
    "DbtRuntimePolicySnapshot",
    "DbtRuntimeTarget",
    "GeneratedDbtCommand",
    "InstalledDbtPolicy",
    "OperatorDiagnostic",
    "SupportManifest",
    "assess_dbt_configuration",
    "demo_installed_policy",
    "expected_dbt_output",
    "fixed_demo_configuration_snapshot",
    "generate_dbt_commands",
    "load_support_manifest",
    "parse_dbt_runtime_policy",
    "parse_support_manifest",
    "render_dbt_runtime_policy",
]
