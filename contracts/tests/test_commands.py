"""Golden tests for the only supported generated dbt command shapes."""

from __future__ import annotations

import shlex
from dataclasses import FrozenInstanceError, replace
from typing import Any, cast

import pytest
from click.testing import CliRunner
from dbt.cli.main import cli

from dbtobsb_contracts import (
    AttemptIdentity,
    InstalledDbtPolicy,
    demo_installed_policy,
    expected_dbt_output,
    generate_dbt_commands,
    load_support_manifest,
)


def test_build_only_command_owns_every_governed_flag_and_path() -> None:
    generated = generate_dbt_commands(policy=demo_installed_policy())

    assert len(generated) == 1
    command = generated[0]
    argv = shlex.split(command.shell_command)
    assert argv[:2] == ["dbt", "build"]
    assert argv[-2:] == ["--selector", "observability_demo"]
    assert "--no-send-anonymous-usage-stats" in argv
    assert "--no-upload-to-artifacts-ingest-api" in argv
    assert argv[argv.index("--log-file-max-bytes") + 1] == "20971520"
    assert argv[argv.index("--log-path") + 1] == command.log_path_template
    assert command.target_path_template is not None
    assert argv[argv.index("--target-path") + 1] == command.target_path_template
    assert "{{task.run_id}}" in command.log_path_template
    assert "{{job.run_id}}" in command.log_path_template
    assert "--vars" not in argv
    assert "--select" not in argv
    assert "--exclude" not in argv


def test_deps_has_ordinal_log_path_but_no_selector_or_target_path() -> None:
    generated = generate_dbt_commands(policy=replace(demo_installed_policy(), include_deps=True))

    assert len(generated) == 2
    deps = shlex.split(generated[0].shell_command)
    build = shlex.split(generated[1].shell_command)
    assert deps[:2] == ["dbt", "deps"]
    assert "--target-path" not in deps
    assert "--selector" not in deps
    assert deps[deps.index("--log-path") + 1].endswith("/000-deps/logs")
    assert build[build.index("--log-path") + 1].endswith("/001-build/logs")


@pytest.mark.parametrize(
    "selector",
    [
        "",
        "contains space",
        "../escape",
        "{{job.parameters.selector}}",
        "a" * 65,
    ],
)
def test_selector_is_a_bounded_installed_name_not_a_command_fragment(selector: str) -> None:
    with pytest.raises(ValueError, match="DBTOBSB_DBT_SELECTOR_INVALID"):
        InstalledDbtPolicy(
            support_contract_sha256=load_support_manifest().canonical_sha256,
            approved_selector=selector,
            include_deps=False,
        )


def test_command_generation_has_no_caller_selector_or_dependency_arguments() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        cast(Any, generate_dbt_commands)(
            policy=demo_installed_policy(),
            selector="other-selector",
            include_deps=True,
        )


def test_resolved_attempt_paths_change_with_native_attempt_identity() -> None:
    first = expected_dbt_output(
        attempt=AttemptIdentity(1, 2, 3, 4, 0, 1),
        policy=demo_installed_policy(),
    )
    repaired = expected_dbt_output(
        attempt=AttemptIdentity(1, 2, 3, 5, 1, 2),
        policy=demo_installed_policy(),
    )

    assert first.attempt_key == "w1-j2-r3-t4-p0-e1"
    assert first.manifest_member.endswith("/001-build/artifacts/manifest.json")
    assert first.manifest_member != repaired.manifest_member
    assert "{{" not in first.manifest_member


@pytest.mark.parametrize("include_deps", [False, True])
def test_output_expectation_carries_the_exact_installed_command_sequence(
    include_deps: bool,
) -> None:
    expectation = expected_dbt_output(
        attempt=AttemptIdentity(1, 2, 3, 4, 0, 1),
        policy=replace(demo_installed_policy(), include_deps=include_deps),
    )

    assert expectation.include_deps is include_deps
    assert [ordinal for ordinal, _ in expectation.ordinal_log_members] == (
        ["000-deps", "001-build"] if include_deps else ["001-build"]
    )
    assert expectation.ordinal_log_members[-1][1] == expectation.log_member
    assert (expectation.deps_log_member is not None) is include_deps


def test_policy_is_frozen_and_contains_exactly_one_selector_and_dependency_decision() -> None:
    policy = demo_installed_policy()

    assert policy.approved_selector == "observability_demo"
    assert policy.include_deps is False
    with pytest.raises(FrozenInstanceError):
        cast(Any, policy).approved_selector = "other-selector"


@pytest.mark.parametrize("include_deps", [False, True])
def test_pinned_dbt_core_cli_accepts_every_generated_command(include_deps: bool) -> None:
    generated = generate_dbt_commands(
        policy=replace(demo_installed_policy(), include_deps=include_deps)
    )

    for command in generated:
        result = CliRunner().invoke(cli, [*shlex.split(command.shell_command)[1:], "--help"])
        assert result.exit_code == 0, result.output
