from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from dbtobsb_installer.auth import InstallerConnectionInputs, validate_connection
from dbtobsb_installer.onboarding import (
    DbtOnboardingError,
    DbtTargetBinding,
    OnboardingInputs,
    build_onboarding_plan,
    target_from_preflight,
)

_HOST = "https://adb-1234567890123456.10.azuredatabricks.net"
_WAREHOUSE = "0123456789abcdef"
_LOCK_HASH = "226ae69cdfbc9367e2aa2c472b01f99dbce11de0"
_SECRET_CANARY = "source-profile-secret-canary"


def _write(path: Path, raw: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw.encode() if isinstance(raw, str) else raw)


def _project(root: Path, *, source_profile: bool = False) -> Path:
    project = root / "customer_weather"
    _write(
        project / "dbt_project.yml",
        """name: customer_weather
version: '1.0'
config-version: 2
profile: customer_weather
model-paths: [models]
""",
    )
    _write(
        project / "selectors.yml",
        """selectors:
  - name: weather_release
    definition:
      method: path
      value: models
""",
    )
    _write(project / "models" / "weather_daily.sql", "select 1 as observation_count\n")
    if source_profile:
        _write(
            project / "profiles.yml",
            f"customer_weather:\n  outputs:\n    secret: {_SECRET_CANARY}\n",
        )
    _write(project / "logs" / "dbt.log", "ignored log\n")
    _write(project / "target" / "manifest.json", "ignored target\n")
    return project


def _target() -> DbtTargetBinding:
    connection = validate_connection(
        InstallerConnectionInputs(
            profile="paid-azure-test",
            canonical_host=_HOST,
            installer_warehouse_id="fedcba9876543210",
        )
    )
    return target_from_preflight(
        connection=connection,
        dbt_warehouse_id=_WAREHOUSE,
        dbt_warehouse_http_path=f"/sql/1.0/warehouses/{_WAREHOUSE}",
        catalog="analytics",
        schema="weather_prod",
    )


def _build(project: Path, bundle: Path):
    bundle.mkdir(parents=True, exist_ok=True)
    return build_onboarding_plan(
        OnboardingInputs(source_project=project, bundle_root=bundle, target=_target())
    )


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes())


def test_non_demo_project_generates_exact_custom_profile_policy_and_job_patch(
    tmp_path: Path,
) -> None:
    source = _project(tmp_path / "source", source_profile=True)
    source_before = _tree(source)
    bundle = tmp_path / "bundle"

    plan = _build(source, bundle)

    assert _tree(source) == source_before
    assert plan.file_count == 4
    assert plan.include_deps is False
    assert plan.project_relative_path.startswith("dbtobsb_onboarding/")
    root = bundle / Path(plan.project_relative_path).parent
    project = bundle / plan.project_relative_path
    profile = yaml.safe_load((project / "profiles.yml").read_bytes())
    output = profile["customer_weather"]["outputs"]["dbtobsb"]
    assert profile["customer_weather"]["target"] == "dbtobsb"
    assert list(output) == [
        "type",
        "method",
        "host",
        "http_path",
        "token",
        "catalog",
        "schema",
        "threads",
    ]
    assert output == {
        "type": "databricks",
        "method": "http",
        "host": "adb-1234567890123456.10.azuredatabricks.net",
        "http_path": f"/sql/1.0/warehouses/{_WAREHOUSE}",
        "token": "{{ env_var('DBT_ACCESS_TOKEN') }}",
        "catalog": "analytics",
        "schema": "weather_prod",
        "threads": 1,
    }
    assert _SECRET_CANARY.encode() not in b"".join(_tree(root).values())
    assert not (project / "logs").exists()
    assert not (project / "target").exists()

    policy = _load_json(bundle / plan.policy_relative_path)
    assert policy["profile_name"] == "customer_weather"
    assert policy["selector"] == "weather_release"
    assert policy["include_deps"] is False
    assert policy["dependency_definition_files"] == []
    assert policy["dependency_lock_sha256"] is None
    assert policy["project_directory"] == f"./{plan.project_relative_path}"
    assert policy["profiles_directory"] == policy["project_directory"]
    assert policy["source_contract_sha256"] == plan.source_contract_sha256
    assert policy["expected_runtime_policy_sha256"] == plan.expected_runtime_policy_sha256
    assert len(policy["commands"]) == 1
    assert policy["commands"][0].startswith("dbt build ")
    assert "--selector weather_release" in policy["commands"][0]

    patch = yaml.safe_load((bundle / plan.job_patch_relative_path).read_bytes())
    job = patch["resources"]["jobs"]["dbtobsb_observed"]
    dbt_task = job["tasks"][0]["dbt_task"]
    assert dbt_task == {
        "source": "WORKSPACE",
        "project_directory": policy["project_directory"],
        "profiles_directory": policy["project_directory"],
        "commands": policy["commands"],
    }
    assert {"warehouse_id", "catalog", "schema"}.isdisjoint(dbt_task)
    assert job["tasks"][1]["run_if"] == "ALL_DONE"
    assert job["tasks"][1]["run_job_task"]["job_id"] == ("${resources.jobs.dbtobsb_collector.id}")


def test_identical_sources_with_different_paths_and_mtimes_are_byte_stable(
    tmp_path: Path,
) -> None:
    first_source = _project(tmp_path / "first-source")
    second_source = _project(tmp_path / "second-source")
    for path in second_source.rglob("*"):
        if path.is_file():
            os.utime(path, (1_700_000_000, 1_700_000_000))

    first = _build(first_source, tmp_path / "first-bundle")
    second = _build(second_source, tmp_path / "second-bundle")

    assert first == second
    first_root = tmp_path / "first-bundle" / Path(first.project_relative_path).parent
    second_root = tmp_path / "second-bundle" / Path(second.project_relative_path).parent
    assert _tree(first_root) == _tree(second_root)


def test_dependency_project_derives_deps_command_from_matching_dbt_lock(tmp_path: Path) -> None:
    source = _project(tmp_path / "source")
    _write(
        source / "packages.yml",
        """packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
""",
    )
    _write(
        source / "package-lock.yml",
        f"""packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
    name: dbt_utils
sha1_hash: {_LOCK_HASH}
""",
    )

    plan = _build(source, tmp_path / "bundle")
    policy = _load_json(tmp_path / "bundle" / plan.policy_relative_path)

    assert plan.include_deps is True
    assert policy["dependency_definition_files"] == ["packages.yml"]
    assert isinstance(policy["dependency_lock_sha256"], str)
    assert [command.split(" ", maxsplit=2)[:2] for command in policy["commands"]] == [
        ["dbt", "deps"],
        ["dbt", "build"],
    ]


def test_dependency_lock_package_graph_cannot_be_substituted(tmp_path: Path) -> None:
    source = _project(tmp_path / "source")
    _write(
        source / "packages.yml",
        "packages:\n  - package: dbt-labs/dbt_utils\n    version: 1.3.0\n",
    )
    _write(
        source / "package-lock.yml",
        f"""packages:
  - package: dbt-labs/codegen
    version: 0.13.1
    name: codegen
sha1_hash: {_LOCK_HASH}
""",
    )

    with pytest.raises(
        DbtOnboardingError,
        match="DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_MISMATCH",
    ):
        _build(source, tmp_path / "bundle")

    assert not (tmp_path / "bundle" / "dbtobsb_onboarding").exists()


def test_pinned_dbt_core_parses_the_final_non_demo_snapshot(tmp_path: Path) -> None:
    source = _project(tmp_path / "source")
    bundle = tmp_path / "bundle"
    plan = _build(source, bundle)
    project = bundle / plan.project_relative_path

    environment = os.environ.copy()
    environment["DBT_ACCESS_TOKEN"] = "local-parse-test-value"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(Path(__file__).parents[2] / "qualification" / "dbt-runtime"),
            "--locked",
            "dbt",
            "parse",
            "--project-dir",
            str(project),
            "--profiles-dir",
            str(project),
            "--target",
            "dbtobsb",
            "--target-path",
            str(tmp_path / "parse-target"),
            "--log-path",
            str(tmp_path / "parse-logs"),
            "--no-send-anonymous-usage-stats",
            "--no-upload-to-artifacts-ingest-api",
            "--quiet",
            "--no-use-colors",
            "--no-use-colors-file",
        ],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "parse-target" / "manifest.json").is_file()


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda project: _write(
                project / "dbt_project.yml",
                "name: x\nprofile: first\nprofile: second\n",
            ),
            "DBTOBSB_ONBOARDING_YAML_DUPLICATE_KEY",
        ),
        (
            lambda project: _write(project / "dbt_project.yml", "name: x\nprofile: invalid.name\n"),
            "DBTOBSB_ONBOARDING_PROFILE_NAME_INVALID",
        ),
        (
            lambda project: _write(
                project / "selectors.yml",
                "selectors:\n  - name: first\n  - name: second\n",
            ),
            "DBTOBSB_ONBOARDING_SELECTOR_COUNT_INVALID",
        ),
        (
            lambda project: _write(
                project / "dbt_project.yml",
                "name: x\nprofile: valid\nflags:\n  fail_fast: true\n",
            ),
            "DBTOBSB_ONBOARDING_DBT_PROJECT_FLAGS_UNSUPPORTED",
        ),
        (
            lambda project: _write(
                project / "packages.yml",
                "packages:\n  - package: dbt-labs/dbt_utils\n    version: 1.3.0\n",
            ),
            "DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_REQUIRED",
        ),
        (
            lambda project: (
                _write(
                    project / "packages.yml",
                    "packages:\n  - package: dbt-labs/dbt_utils\n    version: 1.3.0\n",
                ),
                _write(
                    project / "package-lock.yml",
                    "packages:\n  - package: dbt-labs/dbt_utils\n    version: 1.3.0\n"
                    f"sha1_hash: '{'0' * 40}'\n",
                ),
            ),
            "DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_MISMATCH",
        ),
        (
            lambda project: (
                _write(project / "packages.yml", "packages: []\n"),
                _write(project / "dependencies.yml", "packages: []\n"),
                _write(project / "package-lock.yml", "packages: []\nsha1_hash: " + "0" * 40),
            ),
            "DBTOBSB_ONBOARDING_DEPENDENCY_DEFINITION_AMBIGUOUS",
        ),
        (
            lambda project: _write(project / ".env", "DBT_ACCESS_TOKEN=secret\n"),
            "DBTOBSB_ONBOARDING_SOURCE_FILE_UNSUPPORTED",
        ),
    ],
)
def test_unsupported_source_fails_before_output(
    tmp_path: Path,
    mutation: Any,
    code: str,
) -> None:
    source = _project(tmp_path / "source")
    mutation(source)
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    with pytest.raises(DbtOnboardingError, match=code):
        _build(source, bundle)

    assert not (bundle / "dbtobsb_onboarding").exists()


def test_source_symlink_and_output_conflict_fail_closed(tmp_path: Path) -> None:
    source = _project(tmp_path / "source")
    (source / "models" / "linked.sql").symlink_to(source / "models" / "weather_daily.sql")
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    with pytest.raises(
        DbtOnboardingError,
        match="DBTOBSB_ONBOARDING_SOURCE_SYMLINK_UNSUPPORTED",
    ):
        _build(source, bundle)

    (source / "models" / "linked.sql").unlink()
    plan = _build(source, bundle)
    (bundle / plan.policy_relative_path).write_text("tampered", encoding="utf-8")
    with pytest.raises(DbtOnboardingError, match="DBTOBSB_ONBOARDING_OUTPUT_CONFLICT"):
        _build(source, bundle)


def test_target_binding_requires_matching_verified_azure_values() -> None:
    with pytest.raises(
        DbtOnboardingError,
        match="DBTOBSB_ONBOARDING_TARGET_CONSTRUCTION_DENIED",
    ):
        DbtTargetBinding(
            canonical_workspace_hostname="adb-1234567890123456.10.azuredatabricks.net",
            warehouse_id=_WAREHOUSE,
            warehouse_http_path=f"/sql/1.0/warehouses/{_WAREHOUSE}",
            catalog="analytics",
            schema="weather_prod",
            _construction_token=object(),
        )

    connection = validate_connection(
        InstallerConnectionInputs(
            profile="paid-azure-test",
            canonical_host=_HOST,
            installer_warehouse_id="fedcba9876543210",
        )
    )
    with pytest.raises(DbtOnboardingError, match="DBTOBSB_ONBOARDING_TARGET_INVALID"):
        target_from_preflight(
            connection=connection,
            dbt_warehouse_id=_WAREHOUSE,
            dbt_warehouse_http_path="/sql/1.0/warehouses/fedcba9876543210",
            catalog="analytics",
            schema="weather_prod",
        )
