"""Golden tests for the canonical installed dbt runtime policy."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import PurePosixPath

import pytest

from dbtobsb_contracts import (
    DbtRuntimePolicyError,
    DbtRuntimePolicyInputs,
    DbtRuntimeTarget,
    parse_dbt_runtime_policy,
    render_dbt_runtime_policy,
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "ascii"
    )


def _inputs(*, include_deps: bool = False) -> DbtRuntimePolicyInputs:
    source = {
        "dbt_project.yml": "1" * 64,
        "models/weather.sql": "2" * 64,
        "profiles.yml": "3" * 64,
        "selectors.yml": "4" * 64,
    }
    definitions: tuple[str, ...] = ()
    lock: str | None = None
    if include_deps:
        source["packages.yml"] = "5" * 64
        source["package-lock.yml"] = "6" * 64
        definitions = ("packages.yml",)
        lock = "6" * 64
    source_contract = hashlib.sha256(
        _canonical(
            {
                "domain": "dbtobsb.dbt-source-contract.v1",
                "source_sha256": dict(sorted(source.items())),
            }
        )
    ).hexdigest()
    return DbtRuntimePolicyInputs(
        source_sha256=source,
        source_contract_sha256=source_contract,
        project_directory=f"./dbtobsb_onboarding/{source_contract}/project",
        profile_name="customer_weather",
        selector="weather_release",
        include_deps=include_deps,
        dependency_definition_files=definitions,
        dependency_lock_sha256=lock,
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


def _document(raw: bytes) -> dict[str, object]:
    value = json.loads(raw)
    assert isinstance(value, dict)
    return value


def _render_document(value: dict[str, object]) -> bytes:
    return _canonical(value) + b"\n"


def test_non_demo_policy_round_trips_and_derives_commands_from_one_sealed_choice() -> None:
    rendered = render_dbt_runtime_policy(_inputs())
    parsed = parse_dbt_runtime_policy(rendered.canonical_bytes)

    assert parsed == rendered
    assert parsed.installed_policy.approved_selector == "weather_release"
    assert parsed.installed_policy.include_deps is False
    commands = _document(parsed.canonical_bytes)["commands"]
    assert isinstance(commands, list)
    assert all(isinstance(command, str) for command in commands)
    assert parsed.commands == tuple(commands)
    assert len(parsed.commands) == 1
    assert parsed.commands[0].startswith("dbt build ")
    assert parsed.commands[0].endswith("--selector weather_release")
    assert parsed.profiles_directory == parsed.project_directory
    assert PurePosixPath(parsed.project_directory.removeprefix("./")).parts[0] == (
        "dbtobsb_onboarding"
    )


def test_dependency_policy_seals_deps_command_definition_and_lock() -> None:
    parsed = render_dbt_runtime_policy(_inputs(include_deps=True))

    assert parsed.installed_policy.include_deps is True
    assert parsed.dependency_definition_files == ("packages.yml",)
    assert parsed.dependency_lock_sha256 == "6" * 64
    assert [command.split(" ", 2)[:2] for command in parsed.commands] == [
        ["dbt", "deps"],
        ["dbt", "build"],
    ]


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda document: document.__setitem__("unexpected", True),
            "DBTOBSB_DBT_POLICY_SHAPE_INVALID",
        ),
        (
            lambda document: document["commands"].append("dbt run"),  # type: ignore[union-attr]
            "DBTOBSB_DBT_POLICY_COMMANDS_INVALID",
        ),
        (
            lambda document: document.__setitem__("include_deps", True),
            "DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID",
        ),
        (
            lambda document: document["source_sha256"].__setitem__(  # type: ignore[union-attr]
                "models/weather.sql", "9" * 64
            ),
            "DBTOBSB_DBT_POLICY_SOURCE_CONTRACT_INVALID",
        ),
        (
            lambda document: document.__setitem__("project_directory", "./customer"),
            "DBTOBSB_DBT_POLICY_PROJECT_DIRECTORY_INVALID",
        ),
        (
            lambda document: document["target"].__setitem__(  # type: ignore[union-attr]
                "http_path", "/sql/1.0/warehouses/fedcba9876543210"
            ),
            "DBTOBSB_DBT_POLICY_TARGET_INVALID",
        ),
        (
            lambda document: document.__setitem__("expected_runtime_policy_sha256", "0" * 64),
            "DBTOBSB_DBT_POLICY_DIGEST_INVALID",
        ),
    ],
)
def test_every_policy_drift_is_rejected(
    mutation: Callable[[dict[str, object]], None],
    code: str,
) -> None:
    document = _document(render_dbt_runtime_policy(_inputs()).canonical_bytes)
    mutation(document)

    with pytest.raises(DbtRuntimePolicyError, match=code):
        parse_dbt_runtime_policy(_render_document(document))


def test_duplicate_keys_and_noncanonical_bytes_are_rejected() -> None:
    raw = render_dbt_runtime_policy(_inputs()).canonical_bytes
    duplicate = raw.replace(
        b'{"commands":',
        b'{"commands":[],"commands":',
        1,
    )
    with pytest.raises(DbtRuntimePolicyError, match="DBTOBSB_DBT_POLICY_DUPLICATE_KEY"):
        parse_dbt_runtime_policy(duplicate)

    pretty = json.dumps(_document(raw), indent=2, sort_keys=True).encode("ascii") + b"\n"
    with pytest.raises(DbtRuntimePolicyError, match="DBTOBSB_DBT_POLICY_NOT_CANONICAL"):
        parse_dbt_runtime_policy(pretty)


def test_renderer_defensively_freezes_caller_owned_source_map() -> None:
    inputs = _inputs()
    caller_owned = dict(inputs.source_sha256)
    copied = DbtRuntimePolicyInputs(
        source_sha256=caller_owned,
        source_contract_sha256=inputs.source_contract_sha256,
        project_directory=inputs.project_directory,
        profile_name=inputs.profile_name,
        selector=inputs.selector,
        include_deps=inputs.include_deps,
        dependency_definition_files=inputs.dependency_definition_files,
        dependency_lock_sha256=inputs.dependency_lock_sha256,
        target=inputs.target,
    )
    caller_owned["models/foreign.sql"] = "f" * 64

    assert "models/foreign.sql" not in copied.source_sha256
    render_dbt_runtime_policy(copied)
