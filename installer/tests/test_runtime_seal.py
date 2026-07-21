"""Pre-deploy runtime artifact candidate tests."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import tomllib
import zipfile
from collections.abc import Mapping
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from dbtobsb_collector.bootstrap import InstallationBinding
from dbtobsb_collector.deployment import (
    construct_deployed_installation_seal,
    parse_deployed_installation_seal,
    render_deployed_installation_seal,
)
from dbtobsb_contracts import (
    DbtRuntimePolicyInputs,
    DbtRuntimeTarget,
    parse_dbt_runtime_policy,
    render_dbt_runtime_policy,
)

from dbtobsb_installer import runtime_seal
from dbtobsb_installer.runtime_seal import (
    RuntimeSealError,
    RuntimeSealInputs,
    _RuntimeCandidateBuilder,
)

PROFILE = "dbtobsb-smoke"
TARGET = "smoke"
HOST = "https://adb-1234567890123456.10.azuredatabricks.net"
WORKSPACE_ID = 1234567890123456
WORKSPACE_ROOT = "/Workspace/dbtobsb/.bundle/dbtobsb/smoke"
ARTIFACT_ROOT = f"{WORKSPACE_ROOT}/artifacts/.internal"
RESOLVED_DEPENDENCIES = (
    f"{ARTIFACT_ROOT}/dbtobsb_contracts-0.4.0-py3-none-any.whl",
    f"{ARTIFACT_ROOT}/dbtobsb_capture-0.4.0-py3-none-any.whl",
    f"{ARTIFACT_ROOT}/dbtobsb_collector-0.4.0-py3-none-any.whl",
    "databricks-sdk==0.117.0",
)


def _policy():
    source = {
        "dbt_project.yml": "1" * 64,
        "models/weather.sql": "2" * 64,
        "profiles.yml": "3" * 64,
        "selectors.yml": "4" * 64,
    }
    source_contract = hashlib.sha256(
        runtime_seal._canonical_json(
            {
                "domain": "dbtobsb.dbt-source-contract.v1",
                "source_sha256": source,
            }
        )
    ).hexdigest()
    return render_dbt_runtime_policy(
        DbtRuntimePolicyInputs(
            source_sha256=source,
            source_contract_sha256=source_contract,
            project_directory=f"./dbtobsb_onboarding/{source_contract}/project",
            profile_name="customer_weather",
            selector="weather_release",
            include_deps=False,
            dependency_definition_files=(),
            dependency_lock_sha256=None,
            target=DbtRuntimeTarget(
                host="adb-1234567890123456.10.azuredatabricks.net",
                warehouse_id="fedcba9876543210",
                http_path="/sql/1.0/warehouses/fedcba9876543210",
                catalog="analytics",
                schema="weather_prod",
                artifact_catalog="observability",
                artifact_schema="dbtobsb",
            ),
        )
    )


def _inputs() -> RuntimeSealInputs:
    return RuntimeSealInputs(
        profile=PROFILE,
        target=TARGET,
        evidence_catalog="observability",
        evidence_schema="dbtobsb",
        warehouse_id="0123456789abcdef",
        observed_service_principal_name="observed-sp",
        collector_service_principal_name="collector-sp",
        job_manager_group_name="job-managers",
        dbt_policy=_policy(),
    )


def _declared_environment() -> list[dict[str, Any]]:
    return [
        {
            "environment_key": "collector",
            "spec": {
                "client": "5",
                "dependencies": list(runtime_seal._EXPECTED_DECLARED_DEPENDENCIES),
            },
        }
    ]


def _summary(*, host: str | None = HOST) -> bytes:
    workspace = {"profile": PROFILE, "root_path": WORKSPACE_ROOT}
    if host is not None:
        workspace["host"] = host
    return json.dumps(
        {
            "bundle": {
                "databricks_cli_version": "1.8.0",
                "name": "dbtobsb",
                "engine": "direct",
                "target": TARGET,
            },
            "workspace": workspace,
            "resources": {
                "jobs": {
                    "dbtobsb_collector": {
                        "id": "202",
                        "name": "dbtobsb-collector",
                        "environments": _declared_environment(),
                    },
                    "dbtobsb_reconciler": {
                        "id": "203",
                        "name": "dbtobsb-reconciler",
                        "environments": _declared_environment(),
                    },
                    "dbtobsb_observed": {"id": "201", "name": "dbtobsb-observed"},
                }
            },
        },
        separators=(",", ":"),
    ).encode()


def _auth_description(*, secure: bool = True, forbidden: bool = False) -> bytes:
    def configured(value: str, *, source: str = "config file") -> dict[str, Any]:
        return {"value": value, "source": {"type": source}}

    configuration = {
        "host": configured(HOST),
        "auth_type": configured("databricks-cli"),
        "profile": configured(PROFILE, source="flag"),
        "workspace_id": configured(str(WORKSPACE_ID)),
    }
    if forbidden:
        configuration["token"] = configured("not-printed")
    return json.dumps(
        {
            "status": "success",
            "details": {
                "auth_type": "databricks-cli",
                "configuration": configuration,
            },
            "token_storage": {"mode": "secure" if secure else "file"},
        },
        separators=(",", ":"),
    ).encode()


def _state() -> runtime_seal._BundleState:
    return runtime_seal._BundleState(201, 202, 203, WORKSPACE_ROOT, ARTIFACT_ROOT, HOST)


def _permission_entry(identity_type: str, identity: str, level: str) -> dict[str, Any]:
    return {
        identity_type: identity,
        "all_permissions": [{"inherited": False, "permission_level": level}],
    }


def _permission_document(key: str, job_id: int) -> dict[str, Any]:
    inputs = _inputs()
    entries = [_permission_entry("user_name", "installer-owner", "IS_OWNER")]
    if key == "dbtobsb_collector":
        entries.extend(
            [
                _permission_entry(
                    "service_principal_name",
                    inputs.collector_service_principal_name,
                    "CAN_VIEW",
                ),
                _permission_entry(
                    "service_principal_name",
                    inputs.observed_service_principal_name,
                    "CAN_MANAGE_RUN",
                ),
                _permission_entry("group_name", inputs.job_manager_group_name, "CAN_MANAGE"),
            ]
        )
    else:
        entries.extend(
            [
                _permission_entry(
                    "service_principal_name",
                    inputs.collector_service_principal_name,
                    "CAN_VIEW",
                ),
                _permission_entry("group_name", inputs.job_manager_group_name, "CAN_MANAGE"),
            ]
        )
    entries.append(
        {
            "group_name": "admins",
            "all_permissions": [
                {
                    "inherited": True,
                    "inherited_from_object": ["/jobs/"],
                    "permission_level": "CAN_MANAGE",
                }
            ],
        }
    )
    return {
        "access_control_list": entries,
        "object_id": f"/jobs/{job_id}",
        "object_type": "job",
    }


class _Jobs:
    def __init__(self, *, drift: str | None = None):
        self.requested: list[int] = []
        self.permission_requests: list[str] = []
        self.drift = drift

    def get(self, job_id: int) -> Any:
        self.requested.append(job_id)
        key = {
            202: "dbtobsb_collector",
            203: "dbtobsb_reconciler",
            201: "dbtobsb_observed",
        }[job_id]
        settings = runtime_seal._expected_job_settings(
            key=key,
            inputs=_inputs(),
            state=_state(),
            resolved_dependencies=RESOLVED_DEPENDENCIES,
        )
        if self.drift == "task" and key == "dbtobsb_observed":
            settings["tasks"][0]["run_if"] = "ALL_SUCCESS"
        run_as = (
            _inputs().observed_service_principal_name
            if key == "dbtobsb_observed"
            else _inputs().collector_service_principal_name
        )
        if self.drift == "run_as" and key == "dbtobsb_collector":
            run_as = "another-principal"
        return {
            "created_time": 1,
            "creator_user_name": "installer-owner",
            "job_id": job_id,
            "run_as_user_name": run_as,
            "settings": settings,
        }

    def get_permissions(self, job_id: str) -> Any:
        self.permission_requests.append(job_id)
        numeric = int(job_id)
        key = {
            202: "dbtobsb_collector",
            203: "dbtobsb_reconciler",
            201: "dbtobsb_observed",
        }[numeric]
        document = _permission_document(key, numeric)
        if self.drift == "acl" and key == "dbtobsb_collector":
            document["access_control_list"].append(
                _permission_entry("group_name", "unexpected", "CAN_MANAGE")
            )
        return document


class _Runner:
    def __init__(
        self,
        *,
        insecure_auth: bool = False,
        drift: str | None = None,
        summary_host: str | None = HOST,
    ):
        self.commands: list[tuple[tuple[str, ...], int]] = []
        self.insecure_auth = insecure_auth
        self.jobs = _Jobs(drift=drift)
        self.summary_host = summary_host

    def run(self, command: tuple[str, ...], *, timeout_seconds: int) -> bytes:
        self.commands.append((command, timeout_seconds))
        if command == runtime_seal._SOURCE_CONTRACT_COMMAND:
            return b"DBTOBSB_BUNDLE_DBT_CONTRACT_OK"
        if command[:3] == ("databricks", "bundle", "validate"):
            return b"{}"
        if command[:3] == ("databricks", "bundle", "summary"):
            return _summary(host=self.summary_host)
        if command[:3] == ("databricks", "auth", "describe"):
            return _auth_description(secure=not self.insecure_auth)
        if command[:3] == runtime_seal._JOBS_GET_COMMAND:
            return json.dumps(self.jobs.get(int(command[3])), separators=(",", ":")).encode()
        if command[:3] == runtime_seal._JOBS_PERMISSIONS_COMMAND:
            return json.dumps(self.jobs.get_permissions(command[3]), separators=(",", ":")).encode()
        raise AssertionError("unexpected fixed command")


def _record_hash(raw: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode()


def _write_wheel(package_root: Path, output: Path, *, external_attr: int | None = None) -> None:
    project = tomllib.loads((package_root / "pyproject.toml").read_text())
    name = project["project"]["name"]
    version = project["project"]["version"]
    package_name = name.replace("-", "_")
    dist_info = f"{package_name}-{version}.dist-info"
    members: dict[str, bytes] = {}
    source = package_root / "src" / package_name
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            members[f"{package_name}/{path.relative_to(source).as_posix()}"] = path.read_bytes()
    dependencies = project["project"].get("dependencies", [])
    requires_dist = "".join(f"Requires-Dist: {item}\n" for item in dependencies)
    members[f"{dist_info}/METADATA"] = (
        f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n{requires_dist}\n"
    ).encode()
    members[f"{dist_info}/WHEEL"] = b"Wheel-Version: 1.0\nTag: py3-none-any\n\n"
    if project["project"].get("scripts"):
        members[f"{dist_info}/entry_points.txt"] = b"[console_scripts]\nplaceholder = x:y\n"
    record_name = f"{dist_info}/RECORD"
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for member, raw in members.items():
        writer.writerow((member, f"sha256={_record_hash(raw)}", str(len(raw))))
    writer.writerow((record_name, "", ""))
    members[record_name] = record.getvalue().encode()
    output.mkdir(parents=True)
    wheel = output / f"{package_name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for member, raw in members.items():
            info = zipfile.ZipInfo(member, (1980, 1, 1, 0, 0, 0))
            if external_attr is not None:
                info.external_attr = external_attr
            archive.writestr(info, raw)


class _FakeArtifactBuilder:
    def __init__(
        self,
        *,
        fail_package: str | None = None,
        external_attr: int | None = None,
    ):
        self.fail_package = fail_package
        self.external_attr = external_attr

    def build(
        self,
        *,
        package_root: Path,
        output_directory: Path,
        child_environment: Mapping[str, str],
    ) -> None:
        del child_environment
        if package_root.name == self.fail_package:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
        _write_wheel(package_root, output_directory, external_attr=self.external_attr)


class _InjectedSourceArtifactBuilder(_FakeArtifactBuilder):
    def build(
        self,
        *,
        package_root: Path,
        output_directory: Path,
        child_environment: Mapping[str, str],
    ) -> None:
        super().build(
            package_root=package_root,
            output_directory=output_directory,
            child_environment=child_environment,
        )
        wheel = next(output_directory.glob("*.whl"))
        package_name = package_root.name.replace("-", "_")
        with zipfile.ZipFile(wheel, "a") as archive:
            info = zipfile.ZipInfo(f"{package_name}/injected.py", (1980, 1, 1, 0, 0, 0))
            archive.writestr(info, b"INJECTED = True\n")


@pytest.fixture
def private_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / ".dbtobsb" / "runtime-candidates"
    root.mkdir(parents=True)
    monkeypatch.setattr(runtime_seal, "_PRIVATE_ROOT", root)
    monkeypatch.setattr(runtime_seal, "_LOCK_PATH", root.parent / "runtime-candidate.lock")
    return root


def _candidate_builder(
    *,
    runner: _Runner | None = None,
    artifacts: _FakeArtifactBuilder | None = None,
    environment: dict[str, str] | None = None,
) -> _RuntimeCandidateBuilder:
    return _RuntimeCandidateBuilder(
        runner=runner or _Runner(),
        artifact_builder=artifacts or _FakeArtifactBuilder(),
        environment=environment or {},
    )


def test_runtime_inputs_have_no_caller_supplied_job_id_or_path() -> None:
    input_names = {field.name for field in fields(RuntimeSealInputs)}

    assert not any(name.endswith("job_id") or name.endswith("path") for name in input_names)


def test_workspace_runner_uses_sealed_project_and_policy_paths() -> None:
    settings = runtime_seal._expected_job_settings(
        key="dbtobsb_observed",
        inputs=_inputs(),
        state=_state(),
        resolved_dependencies=RESOLVED_DEPENDENCIES,
    )
    runner = next(
        task["python_wheel_task"]
        for task in settings["tasks"]
        if task.get("python_wheel_task", {}).get("entry_point") == "run-dbt"
    )
    parameters = runner["parameters"]
    project = parameters[parameters.index("--project_directory") + 1]
    policy = parameters[parameters.index("--policy_path") + 1]

    assert project.startswith("/Workspace/")
    assert policy == project.rsplit("/project", maxsplit=1)[0] + "/dbt-policy-v1.json"


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"profile": "../profile"}, "DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID"),
        ({"target": "production"}, "DBTOBSB_RUNTIME_CANDIDATE_TARGET_INVALID"),
        ({"evidence_schema": " dbtobsb"}, "DBTOBSB_RUNTIME_CANDIDATE_IDENTIFIER_INVALID"),
        ({"warehouse_id": "invalid"}, "DBTOBSB_RUNTIME_CANDIDATE_WAREHOUSE_INVALID"),
        (
            {"collector_service_principal_name": "observed-sp"},
            "DBTOBSB_RUNTIME_CANDIDATE_PRINCIPAL_INVALID",
        ),
    ],
)
def test_typed_inputs_fail_closed(change: dict[str, str], code: str) -> None:
    with pytest.raises(RuntimeSealError, match=code):
        runtime_seal._validate_inputs(replace(_inputs(), **change))


def test_summary_is_force_pulled_and_derives_one_exact_artifact_root(private_root: Path) -> None:
    runner = _Runner()

    result = _candidate_builder(runner=runner).build(_inputs())

    assert result.finalization_required is True
    summary_commands = [
        command
        for command, _ in runner.commands
        if command[:3] == ("databricks", "bundle", "summary")
    ]
    assert len(summary_commands) == 2
    assert all("--force-pull" in command for command in summary_commands)


def test_summary_workspace_host_must_equal_the_forced_secure_profile_host(
    private_root: Path,
) -> None:
    with pytest.raises(RuntimeSealError, match="BUNDLE_STATE_INVALID"):
        _candidate_builder(
            runner=_Runner(summary_host="https://adb-9999999999999999.10.azuredatabricks.net")
        ).build(_inputs())

    assert tuple(private_root.iterdir()) == ()


def test_summary_without_host_uses_the_forced_secure_profile_host(private_root: Path) -> None:
    result = _candidate_builder(runner=_Runner(summary_host=None)).build(_inputs())

    assert result.workspace_id == WORKSPACE_ID


def test_all_remote_readbacks_use_one_explicit_profile_cli_context(private_root: Path) -> None:
    runner = _Runner()

    _candidate_builder(runner=runner).build(_inputs())

    remote_commands = [
        command
        for command, _ in runner.commands
        if command[0] == "databricks" and command[:3] not in (("databricks", "bundle", "validate"),)
    ]
    assert (
        len(
            [
                command
                for command in remote_commands
                if command[:3] == ("databricks", "auth", "describe")
            ]
        )
        == 2
    )
    assert all("--profile" in command and PROFILE in command for command in remote_commands)
    assert not any(command[0:2] == ("databricks", "api") for command in remote_commands)


def test_resolved_wheels_must_share_the_exact_bundle_internal_root() -> None:
    dependencies = list(RESOLVED_DEPENDENCIES)
    dependencies[1] = dependencies[1].replace(ARTIFACT_ROOT, "/Workspace/another/.internal")
    value = runtime_seal._environment_document("collector", tuple(dependencies))

    with pytest.raises(RuntimeSealError, match="JOB_ATTESTATION_FAILED"):
        runtime_seal._validated_environment(
            value,
            code="DBTOBSB_RUNTIME_CANDIDATE_JOB_ATTESTATION_FAILED",
            require_resolved=True,
            artifact_root=ARTIFACT_ROOT,
        )


def test_secure_profile_forbids_plain_storage_and_credential_fields() -> None:
    attestation = runtime_seal._validate_auth_description(_auth_description(), profile=PROFILE)

    assert attestation.host == HOST
    assert attestation.workspace_id == WORKSPACE_ID
    for raw in (_auth_description(secure=False), _auth_description(forbidden=True)):
        with pytest.raises(RuntimeSealError, match="PROFILE_INVALID"):
            runtime_seal._validate_auth_description(raw, profile=PROFILE)


def test_inherited_credentials_are_denied_then_child_storage_is_forced() -> None:
    with pytest.raises(RuntimeSealError, match="INHERITED_CREDENTIALS_DENIED"):
        runtime_seal._reject_inherited_credentials({"DATABRICKS_TOKEN": "not-logged"})

    child = runtime_seal._sanitized_child_environment(
        {
            "PATH": "/bin",
            "AWS_SECRET_ACCESS_KEY": "customer-secret",
            "DATABRICKS_CONFIG_PROFILE": "plaintext-profile",
            "DATABRICKS_HOST": "https://wrong.example",
            "DATABRICKS_TOKEN": "plaintext-token",
            "GITHUB_TOKEN": "customer-secret",
            "SOURCE_DATE_EPOCH": "946684800",
        }
    )

    assert child["DATABRICKS_AUTH_STORAGE"] == "secure"
    assert child["PATH"] == "/bin"
    assert child["SOURCE_DATE_EPOCH"] == runtime_seal._DETERMINISTIC_BUILD_EPOCH
    assert "AWS_SECRET_ACCESS_KEY" not in child
    assert "DATABRICKS_CONFIG_PROFILE" not in child
    assert "DATABRICKS_HOST" not in child
    assert "DATABRICKS_TOKEN" not in child
    assert "GITHUB_TOKEN" not in child


@pytest.mark.parametrize("drift", ["run_as", "task", "acl"])
def test_complete_job_graph_and_acl_drift_is_rejected(
    private_root: Path,
    drift: str,
) -> None:
    with pytest.raises(RuntimeSealError, match=r"JOB_.*ATTESTATION_FAILED"):
        _candidate_builder(runner=_Runner(drift=drift)).build(_inputs())

    assert tuple(private_root.glob("*")) == ()


def test_candidate_is_private_complete_and_explicitly_not_final(private_root: Path) -> None:
    runner = _Runner()
    result = _candidate_builder(runner=runner).build(_inputs())
    candidate = private_root / result.candidate_id

    assert result.remote_deployment_readback_attested is False
    assert result.executed_job_source_attested is False
    assert result.executed_job_environment_attested is False
    assert candidate.stat().st_mode & 0o777 == 0o700
    assert (candidate / "candidate.json").stat().st_mode & 0o777 == 0o600
    assert {path.name for path in (candidate / "candidate-wheels").iterdir()} == {
        artifact.filename for artifact in result.artifacts
    }
    assert {path.name for path in (candidate / "final-wheels").iterdir()} == {
        artifact.filename for artifact in result.final_artifacts
    }
    assert all(
        path.stat().st_mode & 0o777 == 0o600
        for directory in ("candidate-wheels", "final-wheels")
        for path in (candidate / directory).iterdir()
    )
    candidate_collector = next(
        artifact for artifact in result.artifacts if artifact.project_name == "dbtobsb-collector"
    )
    final_collector = next(
        artifact
        for artifact in result.final_artifacts
        if artifact.project_name == "dbtobsb-collector"
    )
    assert "+dbtobsb.candidate." in candidate_collector.filename
    assert "+dbtobsb.final." in final_collector.filename
    with zipfile.ZipFile(candidate / "candidate-wheels" / candidate_collector.filename) as archive:
        candidate_policy = parse_dbt_runtime_policy(archive.read(runtime_seal._POLICY_WHEEL_MEMBER))
        candidate_seal = parse_deployed_installation_seal(
            archive.read(runtime_seal._BINDING_WHEEL_MEMBER),
            policy=candidate_policy,
        )
    with zipfile.ZipFile(candidate / "final-wheels" / final_collector.filename) as archive:
        final_policy = parse_dbt_runtime_policy(archive.read(runtime_seal._POLICY_WHEEL_MEMBER))
        final_seal = parse_deployed_installation_seal(
            archive.read(runtime_seal._BINDING_WHEEL_MEMBER),
            policy=final_policy,
        )
    assert candidate_policy == final_policy == _policy()
    assert (candidate_seal.artifact_state, candidate_seal.finalization_required) == (
        "PRE_DEPLOY_ARTIFACT_CANDIDATE",
        True,
    )
    assert (final_seal.artifact_state, final_seal.finalization_required) == (
        "FINALIZED_RUNTIME",
        False,
    )
    assert candidate_seal.collector_environment_sha256 == result.candidate_environment_sha256
    assert final_seal.collector_environment_sha256 == result.final_environment_sha256
    assert final_seal.installation_id == result.installation_id
    assert result.current_remote_environment_sha256 not in {
        result.candidate_environment_sha256,
        result.final_environment_sha256,
    }
    assert runner.jobs.requested == [202, 203, 201, 202, 203, 201]
    assert runner.jobs.permission_requests == ["202", "203", "201", "202", "203", "201"]
    assert not tuple(private_root.glob(".candidate-work-*"))


def test_failed_build_deletes_all_partial_outputs(private_root: Path) -> None:
    builder = _candidate_builder(artifacts=_FakeArtifactBuilder(fail_package="capture"))

    with pytest.raises(RuntimeSealError, match="BUILD_FAILED"):
        builder.build(_inputs())

    assert tuple(private_root.iterdir()) == ()


def test_wheel_with_unstaged_python_source_member_is_rejected(private_root: Path) -> None:
    with pytest.raises(RuntimeSealError, match="WHEEL_INVALID"):
        _candidate_builder(artifacts=_InjectedSourceArtifactBuilder()).build(_inputs())

    assert tuple(private_root.iterdir()) == ()


def test_same_content_version_cannot_publish_different_wheel_bytes(
    private_root: Path,
) -> None:
    first = _candidate_builder(artifacts=_FakeArtifactBuilder(external_attr=0o100600 << 16)).build(
        _inputs()
    )

    with pytest.raises(RuntimeSealError, match="PUBLISH_CONFLICT"):
        _candidate_builder(artifacts=_FakeArtifactBuilder(external_attr=0o100644 << 16)).build(
            _inputs()
        )

    assert {path.name for path in private_root.iterdir()} == {first.candidate_id}


def test_runtime_package_source_digest_changes_with_console_or_source_code(
    tmp_path: Path,
) -> None:
    roots = tuple(tmp_path / name for name in ("contracts", "capture", "collector"))
    for root in roots:
        (root / "src" / root.name).mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{root.name}"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        (root / "src" / root.name / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

    first = runtime_seal._package_source_sha256(roots)
    assert runtime_seal._package_source_sha256(roots) == first

    (roots[2] / "pyproject.toml").write_text(
        '[project]\nname = "collector"\nversion = "1.0.0"\n'
        '[project.scripts]\nbootstrap = "collector:bootstrap"\n',
        encoding="utf-8",
    )
    assert runtime_seal._package_source_sha256(roots) != first


def test_candidate_lock_denies_concurrent_packaging(private_root: Path) -> None:
    del private_root
    with (
        runtime_seal._candidate_lock(),
        pytest.raises(RuntimeSealError, match="CANDIDATE_LOCKED"),
        runtime_seal._candidate_lock(),
    ):
        pass


def test_candidate_root_and_relevant_ancestor_symlinks_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    dbtobsb = tmp_path / "plain" / ".dbtobsb"
    dbtobsb.mkdir(parents=True)
    root_link = dbtobsb / "runtime-candidates"
    root_link.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(runtime_seal, "_PRIVATE_ROOT", root_link)
    monkeypatch.setattr(runtime_seal, "_LOCK_PATH", dbtobsb / "runtime-candidate.lock")

    with (
        pytest.raises(RuntimeSealError, match="LOCAL_TARGET_INVALID"),
        runtime_seal._candidate_lock(),
    ):
        pass

    ancestor_link = tmp_path / "linked-ancestor"
    ancestor_link.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(
        runtime_seal,
        "_PRIVATE_ROOT",
        ancestor_link / ".dbtobsb" / "runtime-candidates",
    )
    monkeypatch.setattr(
        runtime_seal,
        "_LOCK_PATH",
        ancestor_link / ".dbtobsb" / "runtime-candidate.lock",
    )
    with (
        pytest.raises(RuntimeSealError, match="LOCAL_TARGET_INVALID"),
        runtime_seal._candidate_lock(),
    ):
        pass


def test_lock_target_and_candidate_id_symlinks_are_rejected(
    private_root: Path,
) -> None:
    outside_file = private_root.parent / "outside-lock"
    outside_file.write_text("outside", encoding="utf-8")
    runtime_seal._LOCK_PATH.symlink_to(outside_file)
    with (
        pytest.raises(RuntimeSealError, match="LOCAL_TARGET_INVALID"),
        runtime_seal._candidate_lock(),
    ):
        pass
    runtime_seal._LOCK_PATH.unlink()

    result = _candidate_builder().build(_inputs())
    target = private_root / result.candidate_id
    shutil.rmtree(target)
    outside_directory = private_root.parent / "outside-candidate"
    outside_directory.mkdir()
    target.symlink_to(outside_directory, target_is_directory=True)

    with pytest.raises(RuntimeSealError, match="LOCAL_TARGET_INVALID"):
        _candidate_builder().build(_inputs())


def test_real_hatch_build_produces_three_fully_inspected_wheels(tmp_path: Path) -> None:
    binding = InstallationBinding(
        workspace_id=WORKSPACE_ID,
        warehouse_id=_inputs().warehouse_id,
        source_contract_sha256=_inputs().dbt_policy.source_contract_sha256,
        expected_runtime_policy_sha256=(_inputs().dbt_policy.expected_runtime_policy_sha256),
        observed_job_id=201,
        collector_job_id=202,
        reconciler_job_id=203,
        observed_service_principal_name=_inputs().observed_service_principal_name,
        collector_service_principal_name=_inputs().collector_service_principal_name,
        job_manager_group_name=_inputs().job_manager_group_name,
        collector_environment_sha256="a" * 64,
    )
    seal = construct_deployed_installation_seal(
        binding=binding,
        evidence_catalog=_inputs().evidence_catalog,
        evidence_schema=_inputs().evidence_schema,
        artifact_state="PRE_DEPLOY_ARTIFACT_CANDIDATE",
        finalization_required=True,
        policy=_inputs().dbt_policy,
    )

    binding_raw = render_deployed_installation_seal(seal, policy=_inputs().dbt_policy)
    version_seed = runtime_seal._canonical_json({"test_installation": WORKSPACE_ID})
    version = runtime_seal._content_version(
        version_seed_raw=version_seed,
        phase="candidate",
    )

    first = runtime_seal._build_private_artifact_set(
        work=tmp_path / "first",
        binding_raw=binding_raw,
        policy_raw=_inputs().dbt_policy.canonical_bytes,
        version=version,
        phase="candidate",
        builder=runtime_seal._RealArtifactBuilder(),
        child_environment=runtime_seal._sanitized_child_environment(
            {**os.environ, "SOURCE_DATE_EPOCH": "315532800"}
        ),
    )
    second = runtime_seal._build_private_artifact_set(
        work=tmp_path / "second",
        binding_raw=binding_raw,
        policy_raw=_inputs().dbt_policy.canonical_bytes,
        version=version,
        phase="candidate",
        builder=runtime_seal._RealArtifactBuilder(),
        child_environment=runtime_seal._sanitized_child_environment(
            {**os.environ, "SOURCE_DATE_EPOCH": "946684800"}
        ),
    )
    digest, artifacts, candidate = first

    assert (
        digest
        == hashlib.sha256(
            runtime_seal._canonical_json([runtime_seal.asdict(item) for item in artifacts])
        ).hexdigest()
    )
    assert len(artifacts) == 3
    assert all(len(item.sha256) == 64 and item.size_bytes > 0 for item in artifacts)
    assert len(tuple((candidate / "candidate-wheels").glob("*.whl"))) == 3
    assert first[:2] == second[:2]
    assert [
        path.read_bytes() for path in sorted((candidate / "candidate-wheels").glob("*.whl"))
    ] == [path.read_bytes() for path in sorted((second[2] / "candidate-wheels").glob("*.whl"))]

    by_project = {artifact.project_name: artifact for artifact in artifacts}
    capture_wheel = candidate / "candidate-wheels" / by_project["dbtobsb-capture"].filename
    collector_wheel = candidate / "candidate-wheels" / by_project["dbtobsb-collector"].filename
    with zipfile.ZipFile(capture_wheel) as archive:
        metadata = archive.read(
            next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        ).decode()
        assert f"Requires-Dist: dbtobsb-contracts=={version}" in metadata
        assert "Requires-Dist: dbtobsb-contracts==0.4.0\n" not in metadata
    with zipfile.ZipFile(collector_wheel) as archive:
        metadata = archive.read(
            next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        ).decode()
        assert f"Requires-Dist: dbtobsb-capture=={version}" in metadata
        assert f"Requires-Dist: dbtobsb-contracts=={version}" in metadata


def test_identity_input_uses_stdin_and_unknown_argv_is_sanitized(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = _policy()
    relative = Path(
        "dbtobsb_onboarding",
        policy.source_contract_sha256,
        "dbt-policy-v1.json",
    )
    policy_path = tmp_path / relative
    policy_path.parent.mkdir(parents=True)
    policy_path.write_bytes(policy.canonical_bytes)
    monkeypatch.setattr(runtime_seal, "_REPO_ROOT", tmp_path)
    stream = SimpleNamespace(
        buffer=io.BytesIO(
            json.dumps(
                {
                    "observed_service_principal_name": "observed-sp",
                    "collector_service_principal_name": "collector-sp",
                    "job_manager_group_name": "managers",
                    "dbt_policy_relative_path": relative.as_posix(),
                }
            ).encode()
        )
    )

    observed, collector, managers, parsed_policy = runtime_seal._read_identity_stdin(stream)
    assert (observed, collector, managers) == ("observed-sp", "collector-sp", "managers")
    assert parsed_policy == policy
    exit_code = runtime_seal.main(["--collector-job-id", "sensitive-caller-value"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == "DBTOBSB_RUNTIME_CANDIDATE_ARGUMENTS_INVALID\n"
    assert "sensitive-caller-value" not in captured.err
