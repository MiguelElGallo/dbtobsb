"""Opaque, fail-closed configuration contract for the checked-in dbt demo."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from dbtobsb_contracts.commands import demo_installed_policy, generate_dbt_commands
from dbtobsb_contracts.support import load_support_manifest

_DEMO_SELECTOR: Final = "observability_demo"
_DEMO_PROJECT_DIRECTORY: Final = "./demo_dbt"
_DEMO_SOURCE: Final = "WORKSPACE"
_DEMO_ENVIRONMENT_KEY: Final = "dbt"
_DEMO_SOURCE_SHA256: Final = MappingProxyType(
    {
        "dbt_project.yml": "92f0f6e453f749903a673df785a013610d5a4d4674ed7e2e32e3b247664058ba",
        "models/daily_weather_summary.sql": (
            "8a3bb7b4e05349b5905d4335664a34c2cdbb95a7c78b49c63bb6b18b493e423c"
        ),
        "models/schema.yml": ("cdefb7c052f5b81d2981f7202e10c1c4ca5e4b41d79284bb126151f38a9890fc"),
        "models/stg_weather.sql": (
            "b437e4edb77e8a8b7ee081b8b580d479b7be6ab66e857dc953818a3889860db7"
        ),
        "models/weather_alerts.sql": (
            "903a008d3f4f275ce125be7fd0711d2df3b8b4748dc68debc67776da3972fd64"
        ),
        "profiles.yml": "d58b4bb2769913a7e3d5d8aaa2a42a698ac9c60da3638b00e39e46bcd8d23547",
        "seeds/weather_observations.csv": (
            "1852199e9e95087bbd07f89196b6892e8d5a65d76b20d27f06fcb8a7657acea4"
        ),
        "selectors.yml": "c8e8133e4349185e910fc266989a67fa1f5446f33d296808b862717b115ecf8c",
    }
)
_DEMO_SOURCE_CONTRACT_SHA256: Final = (
    "832cb9145fa60d05c702d99a244b2dcd83a26a3ac2e5b476ec2fcc45a90c8205"
)


class DbtConfigurationState(StrEnum):
    """Supported outcomes for the opaque fixed-demo configuration gate."""

    READY = "READY"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class DbtConfigurationFinding:
    """Static finding without raw commands, values, paths, or selector text."""

    code: str
    component: str


@dataclass(frozen=True, slots=True)
class DbtConfigurationAssessment:
    """Deterministic classification of the opaque fixed-demo contract."""

    state: DbtConfigurationState
    findings: tuple[DbtConfigurationFinding, ...]


@dataclass(frozen=True, slots=True)
class _FixedDemoConfigurationSnapshot:
    """Internal singleton; callers cannot supply configuration values to it."""

    commands: tuple[str, ...] = field(repr=False)
    selector: str
    project_directory: str
    source: str
    environment_key: str
    source_sha256: Mapping[str, str] = field(repr=False)
    source_contract_sha256: str = field(repr=False)
    expected_runtime_policy_sha256: str = field(repr=False)


def _expected_runtime_policy_sha256(commands: tuple[str, ...]) -> str:
    contract = {
        "commands": commands,
        "environment_key": _DEMO_ENVIRONMENT_KEY,
        "project_directory": _DEMO_PROJECT_DIRECTORY,
        "selector": _DEMO_SELECTOR,
        "source": _DEMO_SOURCE,
        "source_contract_sha256": _DEMO_SOURCE_CONTRACT_SHA256,
        "support_contract_sha256": load_support_manifest().canonical_sha256,
    }
    rendered = json.dumps(contract, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(rendered).hexdigest()


_DEMO_COMMANDS: Final = tuple(
    command.shell_command for command in generate_dbt_commands(policy=demo_installed_policy())
)

_FIXED_DEMO_SNAPSHOT: Final = _FixedDemoConfigurationSnapshot(
    commands=_DEMO_COMMANDS,
    selector=_DEMO_SELECTOR,
    project_directory=_DEMO_PROJECT_DIRECTORY,
    source=_DEMO_SOURCE,
    environment_key=_DEMO_ENVIRONMENT_KEY,
    source_sha256=_DEMO_SOURCE_SHA256,
    source_contract_sha256=_DEMO_SOURCE_CONTRACT_SHA256,
    expected_runtime_policy_sha256=_expected_runtime_policy_sha256(_DEMO_COMMANDS),
)


def fixed_demo_configuration_snapshot() -> _FixedDemoConfigurationSnapshot:
    """Return the one fixed snapshot proven by the Bundle/source checker."""
    return _FIXED_DEMO_SNAPSHOT


def assess_dbt_configuration(*, snapshot: object) -> DbtConfigurationAssessment:
    """Return READY only for the module-owned fixed-demo singleton."""
    if snapshot is not _FIXED_DEMO_SNAPSHOT:
        return DbtConfigurationAssessment(
            state=DbtConfigurationState.UNSUPPORTED,
            findings=(
                DbtConfigurationFinding(
                    code="DBT_CONFIGURATION_FIXED_DEMO_REQUIRED",
                    component="configuration_source",
                ),
            ),
        )
    return DbtConfigurationAssessment(state=DbtConfigurationState.READY, findings=())
