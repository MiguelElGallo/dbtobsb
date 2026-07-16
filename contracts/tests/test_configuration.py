"""Opaque, fail-closed fixed-demo configuration contract tests."""

from __future__ import annotations

from typing import Any, cast

import pytest

import dbtobsb_contracts
from dbtobsb_contracts import (
    DbtConfigurationState,
    assess_dbt_configuration,
    demo_installed_policy,
    fixed_demo_configuration_snapshot,
    generate_dbt_commands,
)


def _canonical_demo_commands() -> tuple[str, ...]:
    return tuple(
        command.shell_command for command in generate_dbt_commands(policy=demo_installed_policy())
    )


def test_fixed_demo_factory_returns_the_one_complete_ready_snapshot() -> None:
    first = fixed_demo_configuration_snapshot()
    second = fixed_demo_configuration_snapshot()

    assert first is second
    assert first.commands == _canonical_demo_commands()
    assert first.selector == "observability_demo"
    assert first.project_directory == "./demo_dbt"
    assert first.source == "WORKSPACE"
    assert first.environment_key == "dbt"
    assert assess_dbt_configuration(snapshot=first).state is DbtConfigurationState.READY


def test_caller_owned_mapping_can_never_be_assessed_as_ready() -> None:
    caller_owned = {
        "commands": _canonical_demo_commands(),
        "source": "WORKSPACE",
        "environment_overrides": {},
        "project_flags": {},
        "profile_config": {},
    }

    assessment = assess_dbt_configuration(snapshot=caller_owned)

    assert assessment.state is DbtConfigurationState.UNSUPPORTED
    assert tuple((item.code, item.component) for item in assessment.findings) == (
        ("DBT_CONFIGURATION_FIXED_DEMO_REQUIRED", "configuration_source"),
    )


def test_public_package_has_no_generic_installed_snapshot_surface() -> None:
    forbidden = (
        "DbtConfigurationOrigin",
        "DbtConfigurationSnapshot",
        "DbtConfigurationSource",
        "installed_configuration_snapshot",
    )

    assert all(not hasattr(dbtobsb_contracts, name) for name in forbidden)
    assert all(name not in dbtobsb_contracts.__all__ for name in forbidden)


def test_fixed_demo_source_attestation_is_complete_and_immutable() -> None:
    snapshot = fixed_demo_configuration_snapshot()

    assert frozenset(snapshot.source_sha256) == {
        "dbt_project.yml",
        "models/daily_weather_summary.sql",
        "models/schema.yml",
        "models/stg_weather.sql",
        "models/weather_alerts.sql",
        "profiles.yml",
        "seeds/weather_observations.csv",
        "selectors.yml",
    }
    assert snapshot.source_contract_sha256 == (
        "832cb9145fa60d05c702d99a244b2dcd83a26a3ac2e5b476ec2fcc45a90c8205"
    )
    with pytest.raises(TypeError):
        cast(Any, snapshot.source_sha256)["dbt_project.yml"] = "caller-controlled"


def test_fixed_demo_runtime_contract_digest_is_frozen() -> None:
    snapshot = fixed_demo_configuration_snapshot()

    assert snapshot.expected_runtime_policy_sha256 == (
        "9a03d3c7632cac7956f666677f30d51615238f9a5f2586d2b4f830039221779e"
    )
    assert len(snapshot.expected_runtime_policy_sha256) == 64


def test_fixed_snapshot_repr_excludes_source_hashes_and_commands() -> None:
    rendered = repr(fixed_demo_configuration_snapshot())

    assert "832cb914" not in rendered
    assert "57c38177" not in rendered
    assert "dbt build" not in rendered
