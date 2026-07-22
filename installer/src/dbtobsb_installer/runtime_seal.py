"""Build a private pre-deploy runtime artifact candidate without remote mutation."""

from __future__ import annotations

import argparse
import base64
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from email.parser import BytesParser
from enum import Enum
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any, NoReturn, Protocol, cast
from urllib.parse import urlsplit

from dbtobsb_collector.bootstrap import InstallationBinding, collector_environment_sha256
from dbtobsb_collector.deployment import (
    construct_deployed_installation_seal,
    render_deployed_installation_seal,
)
from dbtobsb_collector.naming import quote_identifier
from dbtobsb_contracts import DbtRuntimePolicySnapshot, parse_dbt_runtime_policy

_REPO_ROOT = Path.cwd().resolve()
_PRIVATE_ROOT = _REPO_ROOT / ".dbtobsb" / "runtime-candidates"
_LOCK_PATH = _REPO_ROOT / ".dbtobsb" / "runtime-candidate.lock"
_BINDING_WHEEL_MEMBER = "dbtobsb_collector/_generated/deployment-binding-v1.json"
_POLICY_WHEEL_MEMBER = "dbtobsb_collector/_generated/dbt-policy-v1.json"
_SUPPORTED_TARGET = "smoke"
_BASE_VERSION = "0.5.0"
_PROFILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_CONTENT_VERSION = re.compile(r"^0\.5\.0\+dbtobsb\.(?:candidate|final)\.[0-9a-f]{64}$")
_EXPECTED_JOB_NAMES = {
    "dbtobsb_collector": "dbtobsb-collector",
    "dbtobsb_reconciler": "dbtobsb-reconciler",
    "dbtobsb_observed": "dbtobsb-observed",
}
_EXPECTED_DECLARED_DEPENDENCIES = (
    "./contracts/dist/dbtobsb_contracts-0.5.0-py3-none-any.whl",
    "./capture/dist/dbtobsb_capture-0.5.0-py3-none-any.whl",
    "./collector/dist/dbtobsb_collector-0.5.0-py3-none-any.whl",
    "databricks-sdk==0.117.0",
)
_RESOLVED_WHEEL_PATTERNS = (
    re.compile(
        r"^dbtobsb_contracts-0\.5\.0(?:\+dbtobsb\.(?:candidate|final)\."
        r"[0-9a-f]{64})?-py3-none-any\.whl$"
    ),
    re.compile(
        r"^dbtobsb_capture-0\.5\.0(?:\+dbtobsb\.(?:candidate|final)\."
        r"[0-9a-f]{64})?-py3-none-any\.whl$"
    ),
    re.compile(
        r"^dbtobsb_collector-0\.5\.0(?:\+dbtobsb\.(?:candidate|final)\."
        r"[0-9a-f]{64})?-py3-none-any\.whl$"
    ),
)
_DBT_DEPENDENCIES = (
    "databricks-sdk==0.117.0",
    "databricks-sql-connector==4.3.0",
    "dbt-adapters==1.24.5",
    "dbt-common==1.37.5",
    "dbt-core==1.11.12",
    "dbt-databricks==1.12.2",
    "dbt-protos==1.0.541",
    "dbt-spark==1.10.3",
)
_CREDENTIAL_ENVIRONMENT_NAMES = {
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TENANT_ID",
    "GOOGLE_CREDENTIALS",
}
_CREDENTIAL_ENVIRONMENT_PREFIXES = ("DATABRICKS_", "ARM_")
_CHILD_ENVIRONMENT_ALLOWLIST = frozenset({"HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"})
_DETERMINISTIC_BUILD_EPOCH = "315532800"
_SOURCE_CONTRACT_COMMAND = (
    "uv",
    "run",
    "--project",
    "contracts",
    "python",
    "contracts/scripts/check_bundle_commands.py",
)
_BUNDLE_VALIDATE_COMMAND = (
    "databricks",
    "bundle",
    "validate",
    "--strict",
    "--output",
    "json",
    "--target",
)
_AUTH_DESCRIBE_COMMAND = ("databricks", "auth", "describe", "--profile")
_SUMMARY_COMMAND = (
    "databricks",
    "bundle",
    "summary",
    "--force-pull",
    "--output",
    "json",
    "--target",
)
_JOBS_GET_COMMAND = ("databricks", "jobs", "get")
_JOBS_PERMISSIONS_COMMAND = ("databricks", "jobs", "get-permissions")
_PACKAGE_SPECS = (
    ("contracts", "dbtobsb-contracts", "dbtobsb_contracts"),
    ("capture", "dbtobsb-capture", "dbtobsb_capture"),
    ("collector", "dbtobsb-collector", "dbtobsb_collector"),
)
_PACKAGE_SOURCE_ROOTS = tuple(_REPO_ROOT / name for name in ("contracts", "capture", "collector"))


class RuntimeSealError(RuntimeError):
    """Stable fail-closed error that never includes native or customer values."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RuntimeSealInputs:
    """Typed attended inputs; Job IDs, paths, and SQL are deliberately absent."""

    profile: str
    target: str
    evidence_catalog: str
    evidence_schema: str
    warehouse_id: str
    observed_service_principal_name: str
    collector_service_principal_name: str
    job_manager_group_name: str
    dbt_policy: DbtRuntimePolicySnapshot


@dataclass(frozen=True, slots=True)
class ArtifactDigest:
    """Full-byte digest for one inspected wheel."""

    project_name: str
    filename: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class RuntimeArtifactCandidate:
    """Sanitized two-phase receipt; remote promotion and readback are still required."""

    candidate_id: str
    candidate_relative_path: str
    artifact_set_sha256: str
    artifacts: tuple[ArtifactDigest, ...]
    final_artifacts: tuple[ArtifactDigest, ...]
    installation_id: str
    workspace_id: int
    observed_job_id: int
    collector_job_id: int
    reconciler_job_id: int
    current_remote_environment_sha256: str
    candidate_environment_sha256: str
    final_environment_sha256: str
    current_remote_job_graph_sha256: str
    authenticated_host_sha256: str
    binding_resource_sha256: str
    final_binding_resource_sha256: str
    finalization_required: bool = True
    remote_deployment_readback_attested: bool = False
    executed_job_source_attested: bool = False
    executed_job_environment_attested: bool = False


@dataclass(frozen=True, slots=True)
class _BundleState:
    observed_job_id: int
    collector_job_id: int
    reconciler_job_id: int
    workspace_root: str
    artifact_root: str
    host: str


@dataclass(frozen=True, slots=True)
class _ProfileAttestation:
    profile: str
    host: str
    workspace_id: int


@dataclass(frozen=True, slots=True)
class _RuntimeAttestation:
    binding: InstallationBinding
    profile: _ProfileAttestation
    job_graph_sha256: str
    state: _BundleState
    resolved_dependencies: tuple[str, ...]


class _CommandRunner(Protocol):
    def run(self, command: tuple[str, ...], *, timeout_seconds: int) -> bytes: ...


class _ArtifactBuilder(Protocol):
    def build(
        self,
        *,
        package_root: Path,
        output_directory: Path,
        child_environment: Mapping[str, str],
    ) -> None: ...


def _sanitized_child_environment(environment: Mapping[str, str]) -> dict[str, str]:
    child = {
        name: value
        for name, value in environment.items()
        if name in _CHILD_ENVIRONMENT_ALLOWLIST and value
    }
    child["DATABRICKS_AUTH_STORAGE"] = "secure"
    child["PYTHONHASHSEED"] = "0"
    child["SOURCE_DATE_EPOCH"] = _DETERMINISTIC_BUILD_EPOCH
    child["TZ"] = "UTC"
    child["UV_NO_PROGRESS"] = "1"
    return child


class _FixedCommandRunner:
    def __init__(self, child_environment: Mapping[str, str]) -> None:
        self._child_environment = dict(child_environment)

    def run(self, command: tuple[str, ...], *, timeout_seconds: int) -> bytes:
        try:
            completed = subprocess.run(
                command,
                cwd=_REPO_ROOT,
                env=self._child_environment,
                check=False,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError):
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_COMMAND_FAILED") from None
        if completed.returncode != 0 or len(completed.stdout) > 8 * 1024 * 1024:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_COMMAND_FAILED")
        return completed.stdout

    @property
    def child_environment(self) -> Mapping[str, str]:
        """Expose only the sanitized names for deterministic security regression tests."""
        return dict(self._child_environment)


class _RealArtifactBuilder:
    def build(
        self,
        *,
        package_root: Path,
        output_directory: Path,
        child_environment: Mapping[str, str],
    ) -> None:
        command = (
            "uv",
            "build",
            "--wheel",
            "--out-dir",
            str(output_directory),
            "--clear",
            "--no-create-gitignore",
            str(package_root),
        )
        environment = dict(child_environment)
        environment["SOURCE_DATE_EPOCH"] = _DETERMINISTIC_BUILD_EPOCH
        try:
            completed = subprocess.run(
                command,
                cwd=_REPO_ROOT,
                env=environment,
                check=False,
                capture_output=True,
                timeout=180,
            )
        except (OSError, subprocess.SubprocessError):
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED") from None
        if completed.returncode != 0:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _package_source_sha256(package_roots: Sequence[Path] | None = None) -> str:
    """Bind content versions to every local file that can affect the runtime wheels."""

    roots = tuple(package_roots) if package_roots is not None else _PACKAGE_SOURCE_ROOTS
    source: dict[str, str] = {}
    try:
        for root in roots:
            if root.is_symlink() or not root.is_dir():
                raise OSError
            candidates = [root / "pyproject.toml"]
            readme = root / "README.md"
            if readme.exists():
                candidates.append(readme)
            candidates.extend(sorted((root / "src").rglob("*")))
            for path in candidates:
                if path.is_dir():
                    continue
                if "__pycache__" in path.parts or path.suffix == ".pyc":
                    continue
                if path.is_symlink() or not path.is_file():
                    raise OSError
                relative = f"{root.name}/{path.relative_to(root).as_posix()}"
                if relative in source:
                    raise OSError
                source[relative] = _sha256(path.read_bytes())
    except (OSError, ValueError):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_SOURCE_INVALID") from None
    if not source:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_SOURCE_INVALID")
    return _sha256(
        _canonical_json(
            {
                "domain": "dbtobsb.runtime-package-source.v1",
                "source_sha256": source,
            }
        )
    )


def _parse_json(raw: bytes, *, code: str) -> dict[str, Any]:
    try:
        document = json.loads(raw, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise RuntimeSealError(code) from None
    if not isinstance(document, dict):
        raise RuntimeSealError(code)
    return document


def _mapping(value: Any, *, code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise RuntimeSealError(code)
    return value


def _positive_job_id(value: Any, *, code: str) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise RuntimeSealError(code)
    parsed = int(value)
    if parsed <= 0 or str(parsed) != value:
        raise RuntimeSealError(code)
    return parsed


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_plain(item) for item in value]
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        return _plain(as_dict())
    if isinstance(value, SimpleNamespace):
        return _plain(vars(value))
    return value


def _validated_environment(
    value: Any,
    *,
    code: str,
    require_resolved: bool,
    artifact_root: str | None = None,
) -> tuple[str, ...]:
    plain = _plain(value)
    environments = plain if isinstance(plain, list) else []
    if len(environments) != 1 or not isinstance(environments[0], dict):
        raise RuntimeSealError(code)
    environment = environments[0]
    spec = environment.get("spec")
    if (
        set(environment) != {"environment_key", "spec"}
        or environment.get("environment_key") != "collector"
        or not isinstance(spec, dict)
        or set(spec) != {"client", "dependencies"}
        or spec.get("client") != "5"
        or not isinstance(spec.get("dependencies"), list)
        or any(not isinstance(item, str) for item in spec["dependencies"])
    ):
        raise RuntimeSealError(code)
    exact = tuple(cast(list[str], spec["dependencies"]))
    try:
        collector_environment_sha256(exact)
    except (TypeError, ValueError):
        raise RuntimeSealError(code) from None
    if not require_resolved:
        if exact != _EXPECTED_DECLARED_DEPENDENCIES:
            raise RuntimeSealError(code)
        return exact
    if artifact_root is None or exact[-1] != "databricks-sdk==0.117.0":
        raise RuntimeSealError(code)
    expected_parent = PurePosixPath(artifact_root)
    for dependency, pattern in zip(exact[:-1], _RESOLVED_WHEEL_PATTERNS, strict=True):
        path = PurePosixPath(dependency)
        if (
            not dependency.startswith("/Workspace/")
            or "*" in dependency
            or ".." in path.parts
            or path.parent != expected_parent
            or pattern.fullmatch(path.name) is None
        ):
            raise RuntimeSealError(code)
    return exact


def _validate_inputs(inputs: RuntimeSealInputs) -> None:
    values = tuple(
        getattr(inputs, field) for field in inputs.__dataclass_fields__ if field != "dbt_policy"
    )
    if any(not isinstance(value, str) for value in values):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_ARGUMENTS_INVALID")
    if not isinstance(inputs.dbt_policy, DbtRuntimePolicySnapshot):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_DBT_POLICY_INVALID")
    if _PROFILE.fullmatch(inputs.profile) is None:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID")
    if inputs.target != _SUPPORTED_TARGET:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_TARGET_INVALID")
    identifiers = (inputs.evidence_catalog, inputs.evidence_schema)
    try:
        if any(value != value.strip() for value in identifiers):
            raise ValueError
        for value in identifiers:
            quote_identifier(value)
    except (TypeError, ValueError):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_IDENTIFIER_INVALID") from None
    if _WAREHOUSE_ID.fullmatch(inputs.warehouse_id) is None:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_WAREHOUSE_INVALID")
    if (
        inputs.dbt_policy.target.artifact_catalog != inputs.evidence_catalog
        or inputs.dbt_policy.target.artifact_schema != inputs.evidence_schema
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_DBT_POLICY_INVALID")
    principals = (
        inputs.observed_service_principal_name,
        inputs.collector_service_principal_name,
        inputs.job_manager_group_name,
    )
    if (
        any(
            not value
            or value != value.strip()
            or value == "replace_me"
            or len(value) > 255
            or any(ord(character) < 32 for character in value)
            for value in principals
        )
        or inputs.observed_service_principal_name == inputs.collector_service_principal_name
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PRINCIPAL_INVALID")


def _reject_inherited_credentials(environment: Mapping[str, str]) -> None:
    if any(
        value
        and (
            name in _CREDENTIAL_ENVIRONMENT_NAMES
            or name.startswith(_CREDENTIAL_ENVIRONMENT_PREFIXES)
        )
        for name, value in environment.items()
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_INHERITED_CREDENTIALS_DENIED")


def _validate_local_layout() -> None:
    required = (
        _REPO_ROOT / "databricks.yml",
        _REPO_ROOT / "contracts" / "scripts" / "check_bundle_commands.py",
        *(_REPO_ROOT / name / "pyproject.toml" for name, _, _ in _PACKAGE_SPECS),
    )
    generated = _REPO_ROOT / "collector" / "src" / "dbtobsb_collector" / "_generated"
    try:
        generated_entries = {path.name for path in generated.iterdir()}
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
    if (
        any(path.is_symlink() or not path.is_file() for path in required)
        or generated.is_symlink()
        or generated_entries != {"__init__.py"}
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")


def _canonical_azure_host(value: Any) -> str:
    if not isinstance(value, str):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID")
    parts = urlsplit(value)
    try:
        port = parts.port
    except ValueError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID") from None
    hostname = (parts.hostname or "").lower()
    canonical = f"https://{hostname}"
    if (
        parts.scheme.lower() != "https"
        or not hostname.endswith(".azuredatabricks.net")
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
        or value.rstrip("/").lower() != canonical
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID")
    return canonical


def _validate_auth_description(raw: bytes, *, profile: str) -> _ProfileAttestation:
    code = "DBTOBSB_RUNTIME_CANDIDATE_PROFILE_INVALID"
    root = _parse_json(raw, code=code)
    details = _mapping(root.get("details"), code=code)
    configuration = _mapping(details.get("configuration"), code=code)
    token_storage = _mapping(root.get("token_storage"), code=code)

    def configured(name: str) -> tuple[Any, Any]:
        entry = _mapping(configuration.get(name), code=code)
        source = _mapping(entry.get("source"), code=code)
        return entry.get("value"), source.get("type")

    host, host_source = configured("host")
    auth_type, auth_source = configured("auth_type")
    configured_profile, profile_source = configured("profile")
    workspace_id, workspace_source = configured("workspace_id")
    canonical_host = _canonical_azure_host(host)
    try:
        parsed_workspace_id = int(workspace_id)
    except (TypeError, ValueError):
        raise RuntimeSealError(code) from None
    forbidden_configuration = {
        "token",
        "password",
        "client_id",
        "client_secret",
        "azure_client_id",
        "azure_client_secret",
        "azure_tenant_id",
        "google_credentials",
        "google_service_account",
    }
    if (
        root.get("status") != "success"
        or details.get("auth_type") != "databricks-cli"
        or auth_type != "databricks-cli"
        or configured_profile != profile
        or parsed_workspace_id <= 0
        or str(parsed_workspace_id) != workspace_id
        or host_source != "config file"
        or auth_source != "config file"
        or profile_source != "flag"
        or workspace_source != "config file"
        or token_storage.get("mode") != "secure"
        or forbidden_configuration.intersection(configuration)
    ):
        raise RuntimeSealError(code)
    return _ProfileAttestation(
        profile=profile,
        host=canonical_host,
        workspace_id=parsed_workspace_id,
    )


def _parse_bundle_summary(
    raw: bytes,
    *,
    profile: str,
    target: str,
    authenticated_host: str,
) -> _BundleState:
    code = "DBTOBSB_RUNTIME_CANDIDATE_BUNDLE_STATE_INVALID"
    root = _parse_json(raw, code=code)
    bundle = _mapping(root.get("bundle"), code=code)
    workspace = _mapping(root.get("workspace"), code=code)
    resources = _mapping(root.get("resources"), code=code)
    jobs = _mapping(resources.get("jobs"), code=code)
    workspace_root = workspace.get("root_path")
    workspace_host_value = workspace.get("host")
    if workspace_host_value is None:
        workspace_host = authenticated_host
    else:
        try:
            workspace_host = _canonical_azure_host(workspace_host_value)
        except RuntimeSealError:
            raise RuntimeSealError(code) from None
    expected_suffix = f"/.bundle/dbtobsb/{target}"
    if (
        bundle.get("name") != "dbtobsb"
        or bundle.get("databricks_cli_version") != "1.9.0"
        or str(bundle.get("engine", "")).lower() != "direct"
        or bundle.get("target") != target
        or workspace.get("profile") != profile
        or workspace_host != authenticated_host
        or not isinstance(workspace_root, str)
        or not workspace_root.startswith("/Workspace/")
        or not workspace_root.endswith(expected_suffix)
        or ".." in PurePosixPath(workspace_root).parts
        or set(jobs) != set(_EXPECTED_JOB_NAMES)
    ):
        raise RuntimeSealError(code)
    job_ids: dict[str, int] = {}
    for key, expected_name in _EXPECTED_JOB_NAMES.items():
        job = _mapping(jobs.get(key), code=code)
        if job.get("name") != expected_name or job.get("modified_status") is not None:
            raise RuntimeSealError(code)
        job_ids[key] = _positive_job_id(job.get("id"), code=code)
    if len(set(job_ids.values())) != 3:
        raise RuntimeSealError(code)
    collector = _validated_environment(
        _mapping(jobs["dbtobsb_collector"], code=code).get("environments"),
        code=code,
        require_resolved=False,
    )
    reconciler = _validated_environment(
        _mapping(jobs["dbtobsb_reconciler"], code=code).get("environments"),
        code=code,
        require_resolved=False,
    )
    if collector != reconciler:
        raise RuntimeSealError(code)
    artifact_root = f"{workspace_root}/artifacts/.internal"
    return _BundleState(
        observed_job_id=job_ids["dbtobsb_observed"],
        collector_job_id=job_ids["dbtobsb_collector"],
        reconciler_job_id=job_ids["dbtobsb_reconciler"],
        workspace_root=workspace_root,
        artifact_root=artifact_root,
        host=workspace_host,
    )


def _environment_document(key: str, dependencies: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"environment_key": key, "spec": {"client": "5", "dependencies": list(dependencies)}}]


def _common_settings(
    *,
    name: str,
    description: str,
    timeout_seconds: int,
    run_as: str,
    workspace_root: str,
    environments: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "deployment": {
            "kind": "BUNDLE",
            "metadata_file_path": f"{workspace_root}/state/metadata.json",
        },
        "description": description,
        "edit_mode": "UI_LOCKED",
        "email_notifications": {},
        "environments": environments,
        "format": "MULTI_TASK",
        "max_concurrent_runs": 1,
        "name": name,
        "performance_target": "STANDARD",
        "queue": {"enabled": True},
        "run_as": {"service_principal_name": run_as},
        "timeout_seconds": timeout_seconds,
        "webhook_notifications": {},
    }


def _expected_job_settings(
    *,
    key: str,
    inputs: RuntimeSealInputs,
    state: _BundleState,
    resolved_dependencies: tuple[str, ...],
) -> dict[str, Any]:
    if key == "dbtobsb_collector":
        expected = _common_settings(
            name="dbtobsb-collector",
            description=(
                "Unscheduled RUNTIME_DML_ONLY collector for one installed dbt task attempt."
            ),
            timeout_seconds=900,
            run_as=inputs.collector_service_principal_name,
            workspace_root=state.workspace_root,
            environments=_environment_document("collector", resolved_dependencies),
        )
        expected["parameters"] = [
            {"name": "workspace_id", "default": "0"},
            {"name": "observed_job_id", "default": "0"},
            {"name": "observed_job_run_id", "default": "0"},
            {"name": "dbt_task_run_id", "default": "0"},
            {"name": "observed_task_key", "default": "unresolved"},
            {"name": "repair_count", "default": "0"},
            {"name": "execution_count", "default": "0"},
        ]
        expected["tasks"] = [
            {
                "disabled": False,
                "email_notifications": {},
                "environment_key": "collector",
                "python_wheel_task": {
                    "entry_point": "collect",
                    "package_name": "dbtobsb-collector",
                    "parameters": [
                        "--workspace_id",
                        "{{job.parameters.workspace_id}}",
                        "--observed_job_id",
                        "{{job.parameters.observed_job_id}}",
                        "--observed_job_run_id",
                        "{{job.parameters.observed_job_run_id}}",
                        "--dbt_task_run_id",
                        "{{job.parameters.dbt_task_run_id}}",
                        "--observed_task_key",
                        "{{job.parameters.observed_task_key}}",
                        "--repair_count",
                        "{{job.parameters.repair_count}}",
                        "--execution_count",
                        "{{job.parameters.execution_count}}",
                    ],
                },
                "run_if": "ALL_SUCCESS",
                "task_key": "collect",
                "timeout_seconds": 900,
            }
        ]
        return expected
    if key == "dbtobsb_reconciler":
        expected = _common_settings(
            name="dbtobsb-reconciler",
            description=(
                "Paused-by-default 15-minute bounded recovery scan for the fixed observed dbt Job."
            ),
            timeout_seconds=900,
            run_as=inputs.collector_service_principal_name,
            workspace_root=state.workspace_root,
            environments=_environment_document("collector", resolved_dependencies),
        )
        expected["schedule"] = {
            "pause_status": "PAUSED",
            "quartz_cron_expression": "0 0/15 * * * ?",
            "timezone_id": "UTC",
        }
        expected["tasks"] = [
            {
                "disabled": False,
                "email_notifications": {},
                "environment_key": "collector",
                "python_wheel_task": {
                    "entry_point": "reconcile",
                    "package_name": "dbtobsb-collector",
                    "parameters": [
                        "--workspace_id",
                        "{{workspace.id}}",
                        "--reconciler_job_id",
                        "{{job.id}}",
                        "--reconciliation_run_id",
                        "{{job.run_id}}",
                    ],
                },
                "run_if": "ALL_SUCCESS",
                "task_key": "reconcile",
                "timeout_seconds": 900,
            }
        ]
        return expected
    policy = inputs.dbt_policy
    project_directory = (
        f"{state.workspace_root}/files/{policy.project_directory.removeprefix('./')}"
    )
    policy_path = project_directory.rsplit("/project", maxsplit=1)[0] + "/dbt-policy-v1.json"
    product_wheels = tuple(
        dependency for dependency in resolved_dependencies if dependency.endswith(".whl")
    )
    expected = _common_settings(
        name="dbtobsb-observed",
        description=(
            "Approved customer dbt Core project with deterministic dbtobsb evidence collection."
        ),
        timeout_seconds=1200,
        run_as=inputs.observed_service_principal_name,
        workspace_root=state.workspace_root,
        environments=_environment_document("dbt", (*product_wheels, *_DBT_DEPENDENCIES)),
    )
    expected["tasks"] = [
        {
            "depends_on": [{"task_key": "dbt_build"}],
            "disabled": False,
            "email_notifications": {},
            "run_if": "ALL_DONE",
            "run_job_task": {
                "job_id": state.collector_job_id,
                "job_parameters": {
                    "dbt_task_run_id": "{{tasks.dbt_build.run_id}}",
                    "execution_count": "{{tasks.dbt_build.execution_count}}",
                    "observed_job_id": "{{job.id}}",
                    "observed_job_run_id": "{{job.run_id}}",
                    "observed_task_key": "dbt_build",
                    "repair_count": "{{job.repair_count}}",
                    "workspace_id": "{{workspace.id}}",
                },
            },
            "task_key": "collect_dbt_evidence",
            "timeout_seconds": 900,
        },
        {
            "python_wheel_task": {
                "entry_point": "run-dbt",
                "package_name": "dbtobsb-collector",
                "parameters": [
                    "--workspace_id",
                    "{{workspace.id}}",
                    "--observed_job_id",
                    "{{job.id}}",
                    "--observed_job_run_id",
                    "{{job.run_id}}",
                    "--dbt_task_run_id",
                    "{{task.run_id}}",
                    "--repair_count",
                    "{{job.repair_count}}",
                    "--execution_count",
                    "{{task.execution_count}}",
                    "--project_directory",
                    project_directory,
                    "--policy_path",
                    policy_path,
                ],
            },
            "disabled": False,
            "email_notifications": {},
            "environment_key": "dbt",
            "run_if": "ALL_SUCCESS",
            "task_key": policy.task_key,
            "timeout_seconds": 900,
        },
    ]
    return expected


def _sorted_tasks(settings: dict[str, Any]) -> dict[str, Any]:
    result = dict(settings)
    tasks = result.get("tasks")
    if isinstance(tasks, list) and all(isinstance(task, dict) for task in tasks):
        result["tasks"] = sorted(tasks, key=lambda task: str(task.get("task_key")))
    return result


def _validate_permissions(
    permissions: Any,
    *,
    job_id: int,
    creator: str,
    direct_expected: frozenset[tuple[str, str, str]],
) -> dict[str, Any]:
    code = "DBTOBSB_RUNTIME_CANDIDATE_JOB_ACL_ATTESTATION_FAILED"
    document = _plain(permissions)
    if (
        not isinstance(document, dict)
        or document.get("object_id") != f"/jobs/{job_id}"
        or document.get("object_type") != "job"
        or set(document) != {"access_control_list", "object_id", "object_type"}
        or not isinstance(document.get("access_control_list"), list)
    ):
        raise RuntimeSealError(code)
    observed_direct: set[tuple[str, str, str]] = set()
    owner_matches = 0
    for entry in document["access_control_list"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("all_permissions"), list):
            raise RuntimeSealError(code)
        identity_keys = [
            key
            for key in ("group_name", "service_principal_name", "user_name")
            if isinstance(entry.get(key), str) and entry[key]
        ]
        if len(identity_keys) != 1 or set(entry) - {
            "all_permissions",
            "display_name",
            *identity_keys,
        }:
            raise RuntimeSealError(code)
        identity_type = identity_keys[0]
        identity = cast(str, entry[identity_type])
        for permission in entry["all_permissions"]:
            if not isinstance(permission, dict):
                raise RuntimeSealError(code)
            inherited = permission.get("inherited")
            level = permission.get("permission_level")
            if inherited is False:
                if set(permission) != {"inherited", "permission_level"}:
                    raise RuntimeSealError(code)
                if level == "IS_OWNER" and identity == creator:
                    owner_matches += 1
                else:
                    observed_direct.add((identity_type, identity, str(level)))
            elif inherited is True:
                if (
                    identity_type != "group_name"
                    or level != "CAN_MANAGE"
                    or permission.get("inherited_from_object") != ["/jobs/"]
                    or set(permission) != {"inherited", "inherited_from_object", "permission_level"}
                ):
                    raise RuntimeSealError(code)
            else:
                raise RuntimeSealError(code)
    if owner_matches != 1 or frozenset(observed_direct) != direct_expected:
        raise RuntimeSealError(code)
    return cast(dict[str, Any], document)


def _attest_job_graph(
    runner: _CommandRunner,
    *,
    inputs: RuntimeSealInputs,
    state: _BundleState,
) -> tuple[tuple[str, ...], str]:
    code = "DBTOBSB_RUNTIME_CANDIDATE_JOB_ATTESTATION_FAILED"
    ids = {
        "dbtobsb_collector": state.collector_job_id,
        "dbtobsb_reconciler": state.reconciler_job_id,
        "dbtobsb_observed": state.observed_job_id,
    }
    jobs: dict[str, dict[str, Any]] = {}
    permissions: dict[str, dict[str, Any]] = {}
    resolved: tuple[str, ...] | None = None
    for key in ("dbtobsb_collector", "dbtobsb_reconciler", "dbtobsb_observed"):
        job_id = ids[key]
        try:
            document = _parse_json(
                runner.run(
                    (
                        *_JOBS_GET_COMMAND,
                        str(job_id),
                        "--profile",
                        inputs.profile,
                        "--output",
                        "json",
                    ),
                    timeout_seconds=30,
                ),
                code=code,
            )
        except RuntimeSealError:
            raise RuntimeSealError(code) from None
        if not isinstance(document, dict) or document.get("job_id") != job_id:
            raise RuntimeSealError(code)
        creator = document.get("creator_user_name")
        run_as = (
            inputs.observed_service_principal_name
            if key == "dbtobsb_observed"
            else inputs.collector_service_principal_name
        )
        if (
            not isinstance(creator, str)
            or not creator
            or document.get("run_as_user_name") != run_as
            or not isinstance(document.get("created_time"), int)
            or set(document)
            - {
                "created_time",
                "creator_user_name",
                "job_id",
                "run_as_user_name",
                "settings",
            }
        ):
            raise RuntimeSealError(code)
        settings = document.get("settings")
        if not isinstance(settings, dict):
            raise RuntimeSealError(code)
        if key != "dbtobsb_observed":
            current = _validated_environment(
                settings.get("environments"),
                code=code,
                require_resolved=True,
                artifact_root=state.artifact_root,
            )
            if resolved is None:
                resolved = current
            elif resolved != current:
                raise RuntimeSealError(code)
        expected = _expected_job_settings(
            key=key,
            inputs=inputs,
            state=state,
            resolved_dependencies=resolved or (),
        )
        if _sorted_tasks(settings) != _sorted_tasks(expected):
            raise RuntimeSealError(code)
        if key == "dbtobsb_collector":
            direct = frozenset(
                {
                    (
                        "service_principal_name",
                        inputs.collector_service_principal_name,
                        "CAN_VIEW",
                    ),
                    (
                        "service_principal_name",
                        inputs.observed_service_principal_name,
                        "CAN_MANAGE_RUN",
                    ),
                    ("group_name", inputs.job_manager_group_name, "CAN_MANAGE"),
                }
            )
        else:
            direct = frozenset(
                {
                    (
                        "service_principal_name",
                        inputs.collector_service_principal_name,
                        "CAN_VIEW",
                    ),
                    ("group_name", inputs.job_manager_group_name, "CAN_MANAGE"),
                }
            )
        try:
            permission_response = _parse_json(
                runner.run(
                    (
                        *_JOBS_PERMISSIONS_COMMAND,
                        str(job_id),
                        "--profile",
                        inputs.profile,
                        "--output",
                        "json",
                    ),
                    timeout_seconds=30,
                ),
                code="DBTOBSB_RUNTIME_CANDIDATE_JOB_ACL_ATTESTATION_FAILED",
            )
        except RuntimeSealError:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_JOB_ACL_ATTESTATION_FAILED") from None
        permissions[key] = _validate_permissions(
            permission_response,
            job_id=job_id,
            creator=creator,
            direct_expected=direct,
        )
        jobs[key] = document
    if resolved is None:
        raise RuntimeSealError(code)
    graph = {"jobs": jobs, "permissions": permissions}
    return resolved, _sha256(_canonical_json(graph))


def _attest_runtime(
    *,
    inputs: RuntimeSealInputs,
    runner: _CommandRunner,
) -> _RuntimeAttestation:
    auth_raw = runner.run(
        (*_AUTH_DESCRIBE_COMMAND, inputs.profile, "--output", "json"),
        timeout_seconds=30,
    )
    profile = _validate_auth_description(auth_raw, profile=inputs.profile)
    summary_raw = runner.run(
        (*_SUMMARY_COMMAND, inputs.target, "--profile", inputs.profile),
        timeout_seconds=60,
    )
    state = _parse_bundle_summary(
        summary_raw,
        profile=inputs.profile,
        target=inputs.target,
        authenticated_host=profile.host,
    )
    resolved, graph_sha256 = _attest_job_graph(runner, inputs=inputs, state=state)
    environment_sha256 = collector_environment_sha256(resolved)
    return _RuntimeAttestation(
        binding=InstallationBinding(
            workspace_id=profile.workspace_id,
            warehouse_id=inputs.warehouse_id,
            source_contract_sha256=inputs.dbt_policy.source_contract_sha256,
            expected_runtime_policy_sha256=(inputs.dbt_policy.expected_runtime_policy_sha256),
            observed_job_id=state.observed_job_id,
            collector_job_id=state.collector_job_id,
            reconciler_job_id=state.reconciler_job_id,
            observed_service_principal_name=inputs.observed_service_principal_name,
            collector_service_principal_name=inputs.collector_service_principal_name,
            job_manager_group_name=inputs.job_manager_group_name,
            collector_environment_sha256=environment_sha256,
        ),
        profile=profile,
        job_graph_sha256=graph_sha256,
        state=state,
        resolved_dependencies=resolved,
    )


def _safe_copy_tree(source: Path, destination: Path) -> None:
    try:
        destination.mkdir(parents=True, mode=0o700)
        for candidate in sorted(source.rglob("*")):
            if candidate.is_symlink():
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
            relative = candidate.relative_to(source)
            target = destination / relative
            if candidate.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif candidate.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(candidate, target)
            else:
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
    except RuntimeSealError:
        raise
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None


def _source_input_sha256(version_seed_raw: bytes) -> str:
    entries: list[dict[str, str]] = [
        {"path": "version-seed-v1.json", "sha256": _sha256(version_seed_raw)}
    ]
    for package, _, _ in _PACKAGE_SPECS:
        root = _REPO_ROOT / package
        selected = [root / "pyproject.toml", *(root / "src").rglob("*")]
        readme = root / "README.md"
        if readme.is_file():
            selected.append(readme)
        for path in sorted(selected):
            if path.is_symlink():
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.name != "deployment-binding-v1.json"
            ):
                try:
                    entries.append(
                        {
                            "path": path.relative_to(_REPO_ROOT).as_posix(),
                            "sha256": _sha256(path.read_bytes()),
                        }
                    )
                except OSError:
                    raise RuntimeSealError(
                        "DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID"
                    ) from None
    return _sha256(_canonical_json(entries))


def _prepare_package_copy(
    *,
    package: str,
    destination: Path,
    version: str,
    binding_raw: bytes,
    policy_raw: bytes,
) -> tuple[Path, tuple[str, ...], frozenset[str]]:
    source = _REPO_ROOT / package
    package_root = destination / package
    _safe_copy_tree(source / "src", package_root / "src")
    for filename in ("pyproject.toml", "README.md"):
        path = source / filename
        if path.is_file():
            try:
                shutil.copyfile(path, package_root / filename)
            except OSError:
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None
    pyproject = package_root / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
        marker = f'version = "{_BASE_VERSION}"'
        if text.count(marker) != 1:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
        text = text.replace(marker, f'version = "{version}"')
        internal_requirements = {
            "capture": ("dbtobsb-contracts",),
            "collector": ("dbtobsb-capture", "dbtobsb-contracts"),
        }.get(package, ())
        for project in internal_requirements:
            dependency = f'"{project}=={_BASE_VERSION}"'
            if text.count(dependency) != 1:
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
            text = text.replace(dependency, f'"{project}=={version}"')
        pyproject.write_text(text, encoding="utf-8")
        if package == "collector":
            binding = (
                package_root
                / "src"
                / "dbtobsb_collector"
                / "_generated"
                / "deployment-binding-v1.json"
            )
            binding.write_bytes(binding_raw)
            os.chmod(binding, 0o600)
            policy = binding.parent / "dbt-policy-v1.json"
            policy.write_bytes(policy_raw)
            os.chmod(policy, 0o600)
        document = tomllib.loads(text)
        project_document = document.get("project")
        if not isinstance(project_document, dict):
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
        dependencies = project_document.get("dependencies", [])
        scripts = project_document.get("scripts", {})
        if (
            project_document.get("version") != version
            or not isinstance(dependencies, list)
            or any(not isinstance(item, str) for item in dependencies)
            or not isinstance(scripts, dict)
        ):
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
    except RuntimeSealError:
        raise
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None
    dist_info_members = {"METADATA", "RECORD", "WHEEL"}
    if scripts:
        dist_info_members.add("entry_points.txt")
    return package_root, tuple(cast(list[str], dependencies)), frozenset(dist_info_members)


def _record_sha256(raw: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode()


def _inspect_wheel(
    wheel: Path,
    *,
    project_name: str,
    package_name: str,
    version: str,
    expected_binding: bytes | None,
    expected_policy: bytes | None,
    source_root: Path,
    expected_requires_dist: tuple[str, ...],
    expected_dist_info_members: frozenset[str],
) -> ArtifactDigest:
    code = "DBTOBSB_RUNTIME_CANDIDATE_WHEEL_INVALID"
    normalized_project = project_name.replace("-", "_")
    expected_name = f"{normalized_project}-{version}-py3-none-any.whl"
    if wheel.name != expected_name or wheel.is_symlink() or not wheel.is_file():
        raise RuntimeSealError(code)
    try:
        wheel_raw = wheel.read_bytes()
        with zipfile.ZipFile(io.BytesIO(wheel_raw)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if (
                archive.comment
                or len(names) != len(set(names))
                or any(
                    (info.external_attr >> 16) & 0o170000 == 0o120000
                    or info.date_time != (1980, 1, 1, 0, 0, 0)
                    or info.comment
                    or info.extra
                    for info in infos
                )
            ):
                raise RuntimeSealError(code)
            dist_info = f"{normalized_project}-{version}.dist-info"
            allowed_prefixes = (f"{package_name}/", f"{dist_info}/")
            if any(
                not name.startswith(allowed_prefixes)
                or name.startswith(f"{package_name}/tests/")
                or name.endswith((".pyc", ".pyo"))
                or "/__pycache__/" in name
                for name in names
            ):
                raise RuntimeSealError(code)
            metadata_name = f"{dist_info}/METADATA"
            record_name = f"{dist_info}/RECORD"
            if names.count(metadata_name) != 1 or names.count(record_name) != 1:
                raise RuntimeSealError(code)
            metadata = BytesParser().parsebytes(archive.read(metadata_name))
            requires_dist = tuple(metadata.get_all("Requires-Dist", []))
            if (
                metadata.get("Name") != project_name
                or metadata.get("Version") != version
                or len(requires_dist) != len(expected_requires_dist)
                or frozenset(requires_dist) != frozenset(expected_requires_dist)
                or any(
                    requirement
                    in {
                        f"dbtobsb-contracts=={_BASE_VERSION}",
                        f"dbtobsb-capture=={_BASE_VERSION}",
                    }
                    for requirement in requires_dist
                )
            ):
                raise RuntimeSealError(code)
            actual_dist_info_members = {
                PurePosixPath(name).name for name in names if name.startswith(f"{dist_info}/")
            }
            if actual_dist_info_members != expected_dist_info_members:
                raise RuntimeSealError(code)
            expected_sources: dict[str, bytes] = {}
            for path in sorted(source_root.rglob("*")):
                if path.is_symlink():
                    raise RuntimeSealError(code)
                if path.is_file() and "__pycache__" not in path.parts:
                    expected_sources[
                        f"{package_name}/{path.relative_to(source_root).as_posix()}"
                    ] = path.read_bytes()
            actual_source_names = {name for name in names if name.startswith(f"{package_name}/")}
            if actual_source_names != set(expected_sources) or any(
                archive.read(name) != raw for name, raw in expected_sources.items()
            ):
                raise RuntimeSealError(code)
            rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
            if len(rows) != len(names) or {row[0] for row in rows if len(row) == 3} != set(names):
                raise RuntimeSealError(code)
            for member, digest, size in rows:
                raw = archive.read(member)
                if member == record_name:
                    if digest or size:
                        raise RuntimeSealError(code)
                elif digest != f"sha256={_record_sha256(raw)}" or size != str(len(raw)):
                    raise RuntimeSealError(code)
            generated = {name for name in names if name.startswith(f"{package_name}/_generated/")}
            if package_name == "dbtobsb_collector":
                if (
                    generated
                    != {
                        "dbtobsb_collector/_generated/__init__.py",
                        _BINDING_WHEEL_MEMBER,
                        _POLICY_WHEEL_MEMBER,
                    }
                    or archive.read(_BINDING_WHEEL_MEMBER) != expected_binding
                    or archive.read(_POLICY_WHEEL_MEMBER) != expected_policy
                ):
                    raise RuntimeSealError(code)
            elif generated:
                raise RuntimeSealError(code)
    except RuntimeSealError:
        raise
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile, KeyError):
        raise RuntimeSealError(code) from None
    return ArtifactDigest(
        project_name=project_name,
        filename=wheel.name,
        sha256=_sha256(wheel_raw),
        size_bytes=len(wheel_raw),
    )


def _content_version(*, version_seed_raw: bytes, phase: str) -> str:
    if phase not in {"candidate", "final"}:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
    source_digest = _source_input_sha256(
        _canonical_json(
            {
                "phase": phase,
                "version_seed_sha256": _sha256(version_seed_raw),
            }
        )
    )
    version = f"{_BASE_VERSION}+dbtobsb.{phase}.{source_digest}"
    if _CONTENT_VERSION.fullmatch(version) is None:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
    return version


def _resolved_dependencies_for_version(*, artifact_root: str, version: str) -> tuple[str, ...]:
    if _CONTENT_VERSION.fullmatch(version) is None:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
    return (
        f"{artifact_root}/dbtobsb_contracts-{version}-py3-none-any.whl",
        f"{artifact_root}/dbtobsb_capture-{version}-py3-none-any.whl",
        f"{artifact_root}/dbtobsb_collector-{version}-py3-none-any.whl",
        "databricks-sdk==0.117.0",
    )


def _build_private_artifact_set(
    *,
    work: Path,
    binding_raw: bytes,
    policy_raw: bytes,
    version: str,
    phase: str,
    builder: _ArtifactBuilder,
    child_environment: Mapping[str, str],
) -> tuple[str, tuple[ArtifactDigest, ...], Path]:
    if _CONTENT_VERSION.fullmatch(version) is None or phase not in {"candidate", "final"}:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
    package_copies = work / f"{phase}-package-copies"
    combined = work / "candidate" / f"{phase}-wheels"
    combined.mkdir(parents=True, mode=0o700)
    artifacts: list[ArtifactDigest] = []
    for package, project_name, package_name in _PACKAGE_SPECS:
        package_root, expected_requires_dist, expected_dist_info_members = _prepare_package_copy(
            package=package,
            destination=package_copies,
            version=version,
            binding_raw=binding_raw,
            policy_raw=policy_raw,
        )
        output = work / f"{phase}-build-output" / package
        builder.build(
            package_root=package_root,
            output_directory=output,
            child_environment=child_environment,
        )
        wheels = tuple(sorted(output.glob("*.whl")))
        if len(wheels) != 1:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_WHEEL_INVALID")
        artifact = _inspect_wheel(
            wheels[0],
            project_name=project_name,
            package_name=package_name,
            version=version,
            expected_binding=binding_raw if package == "collector" else None,
            expected_policy=policy_raw if package == "collector" else None,
            source_root=package_root / "src" / package_name,
            expected_requires_dist=expected_requires_dist,
            expected_dist_info_members=expected_dist_info_members,
        )
        destination = combined / artifact.filename
        try:
            shutil.copyfile(wheels[0], destination)
            os.chmod(destination, 0o600)
        except OSError:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None
        copied = _inspect_wheel(
            destination,
            project_name=project_name,
            package_name=package_name,
            version=version,
            expected_binding=binding_raw if package == "collector" else None,
            expected_policy=policy_raw if package == "collector" else None,
            source_root=package_root / "src" / package_name,
            expected_requires_dist=expected_requires_dist,
            expected_dist_info_members=expected_dist_info_members,
        )
        if copied != artifact:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_WHEEL_INVALID")
        artifacts.append(artifact)
    exact = tuple(artifacts)
    artifact_set_sha256 = _sha256(_canonical_json([asdict(item) for item in exact]))
    return artifact_set_sha256, exact, combined.parent


def _atomic_private_write(path: Path, raw: bytes) -> None:
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(temporary_name)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None


def _path_exists_without_following(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
    return True


def _require_real_directory(path: Path, *, allow_missing: bool = False) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")


def _validate_private_path(candidate_id: str | None = None) -> None:
    if _LOCK_PATH.parent != _PRIVATE_ROOT.parent:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
    _require_real_directory(_PRIVATE_ROOT.parent.parent)
    _require_real_directory(_PRIVATE_ROOT.parent)
    _require_real_directory(_PRIVATE_ROOT)
    lock_metadata: os.stat_result | None = None
    try:
        lock_metadata = _LOCK_PATH.lstat()
    except FileNotFoundError:
        pass
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
    if lock_metadata is not None and (
        stat.S_ISLNK(lock_metadata.st_mode) or not stat.S_ISREG(lock_metadata.st_mode)
    ):
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
    if candidate_id is not None:
        if re.fullmatch(r"[0-9a-f]{64}", candidate_id) is None:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
        target = _PRIVATE_ROOT / candidate_id
        try:
            metadata = target.lstat()
        except FileNotFoundError:
            return
        except OSError:
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID") from None
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")


def _verify_published_candidate(
    path: Path,
    raw: bytes,
    artifacts: tuple[ArtifactDigest, ...],
    final_artifacts: tuple[ArtifactDigest, ...],
) -> None:
    code = "DBTOBSB_RUNTIME_CANDIDATE_PUBLISH_CONFLICT"
    try:
        if (
            path.is_symlink()
            or path.read_bytes() != raw
            or {item.name for item in path.parent.iterdir()}
            != {"candidate.json", "candidate-wheels", "final-wheels"}
        ):
            raise RuntimeSealError(code)
        for directory_name, expected in (
            ("candidate-wheels", artifacts),
            ("final-wheels", final_artifacts),
        ):
            wheels = path.parent / directory_name
            if wheels.is_symlink() or {item.name for item in wheels.iterdir()} != {
                artifact.filename for artifact in expected
            }:
                raise RuntimeSealError(code)
            for artifact in expected:
                wheel = wheels / artifact.filename
                if wheel.is_symlink() or _sha256(wheel.read_bytes()) != artifact.sha256:
                    raise RuntimeSealError(code)
    except RuntimeSealError:
        raise
    except OSError:
        raise RuntimeSealError(code) from None


def _reject_published_version_collision(
    *,
    candidate_id: str,
    artifacts: tuple[ArtifactDigest, ...],
    final_artifacts: tuple[ArtifactDigest, ...],
) -> None:
    expected_names = {artifact.filename for artifact in (*artifacts, *final_artifacts)}
    try:
        for published in _PRIVATE_ROOT.iterdir():
            if published.name.startswith(".candidate-work-") or published.name == candidate_id:
                continue
            if published.is_symlink() or not published.is_dir():
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
            observed_names: set[str] = set()
            for directory_name in ("candidate-wheels", "final-wheels"):
                directory = published / directory_name
                if directory.is_symlink() or not directory.is_dir():
                    raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PUBLISH_CONFLICT")
                observed_names.update(path.name for path in directory.iterdir())
            if expected_names.intersection(observed_names):
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PUBLISH_CONFLICT")
    except RuntimeSealError:
        raise
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PUBLISH_CONFLICT") from None


def _publish_new_candidate_tree(*, candidate_tree: Path, candidate_id: str) -> None:
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    private_descriptor: int | None = None
    target_descriptor: int | None = None
    created = False
    try:
        private_descriptor = os.open(_PRIVATE_ROOT, directory_flags)
        os.mkdir(candidate_id, mode=0o700, dir_fd=private_descriptor)
        created = True
        target_descriptor = os.open(candidate_id, directory_flags, dir_fd=private_descriptor)
        for name in ("candidate.json", "candidate-wheels", "final-wheels"):
            os.rename(candidate_tree / name, name, dst_dir_fd=target_descriptor)
        os.fsync(target_descriptor)
        candidate_tree.rmdir()
    except OSError:
        if created:
            shutil.rmtree(_PRIVATE_ROOT / candidate_id, ignore_errors=True)
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_PUBLISH_CONFLICT") from None
    finally:
        if target_descriptor is not None:
            os.close(target_descriptor)
        if private_descriptor is not None:
            os.close(private_descriptor)


def _cleanup_stale_workdirs() -> None:
    try:
        _validate_private_path()
        for path in _PRIVATE_ROOT.iterdir():
            if not path.name.startswith(".candidate-work-"):
                continue
            if path.is_symlink() or not path.is_dir():
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_TARGET_INVALID")
            shutil.rmtree(path)
    except RuntimeSealError:
        raise
    except OSError:
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCAL_WRITE_FAILED") from None


@contextmanager
def _candidate_lock() -> Iterator[None]:
    descriptor: int | None = None
    parent_descriptor: int | None = None
    private_descriptor: int | None = None
    try:
        _require_real_directory(_PRIVATE_ROOT.parent.parent)
        _PRIVATE_ROOT.parent.mkdir(mode=0o700, exist_ok=True)
        _require_real_directory(_PRIVATE_ROOT.parent)
        _PRIVATE_ROOT.mkdir(mode=0o700, exist_ok=True)
        _validate_private_path()
        os.chmod(_PRIVATE_ROOT.parent, 0o700)
        os.chmod(_PRIVATE_ROOT, 0o700)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            directory_flags |= os.O_NOFOLLOW
        parent_descriptor = os.open(_PRIVATE_ROOT.parent, directory_flags)
        private_descriptor = os.open(
            _PRIVATE_ROOT.name,
            directory_flags,
            dir_fd=parent_descriptor,
        )
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(
            _LOCK_PATH.name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except RuntimeSealError:
        if descriptor is not None:
            os.close(descriptor)
        if private_descriptor is not None:
            os.close(private_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        raise
    except (OSError, BlockingIOError):
        if descriptor is not None:
            os.close(descriptor)
        if private_descriptor is not None:
            os.close(private_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_LOCKED") from None
    try:
        yield
    finally:
        if descriptor is not None:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
        if private_descriptor is not None:
            os.close(private_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)


class _RuntimeCandidateBuilder:
    def __init__(
        self,
        *,
        runner: _CommandRunner,
        artifact_builder: _ArtifactBuilder,
        environment: Mapping[str, str],
    ) -> None:
        self._runner = runner
        self._artifact_builder = artifact_builder
        self._environment = environment
        self._child_environment = _sanitized_child_environment(environment)

    def build(self, inputs: RuntimeSealInputs) -> RuntimeArtifactCandidate:
        _validate_inputs(inputs)
        _reject_inherited_credentials(self._environment)
        self._runner.run(_SOURCE_CONTRACT_COMMAND, timeout_seconds=180)
        self._runner.run(
            (*_BUNDLE_VALIDATE_COMMAND, inputs.target, "--profile", inputs.profile),
            timeout_seconds=60,
        )
        before = _attest_runtime(
            inputs=inputs,
            runner=self._runner,
        )
        version_seed_raw = _canonical_json(
            {
                "artifact_root": before.state.artifact_root,
                "collector_job_id": before.binding.collector_job_id,
                "collector_service_principal_name": (
                    before.binding.collector_service_principal_name
                ),
                "evidence_catalog": inputs.evidence_catalog,
                "evidence_schema": inputs.evidence_schema,
                "job_manager_group_name": before.binding.job_manager_group_name,
                "package_source_sha256": _package_source_sha256(),
                "observed_job_id": before.binding.observed_job_id,
                "observed_service_principal_name": (before.binding.observed_service_principal_name),
                "dbt_runtime_policy_sha256": (inputs.dbt_policy.expected_runtime_policy_sha256),
                "reconciler_job_id": before.binding.reconciler_job_id,
                "warehouse_id": before.binding.warehouse_id,
                "workspace_id": before.binding.workspace_id,
            }
        )
        candidate_version = _content_version(
            version_seed_raw=version_seed_raw,
            phase="candidate",
        )
        final_version = _content_version(version_seed_raw=version_seed_raw, phase="final")
        candidate_dependencies = _resolved_dependencies_for_version(
            artifact_root=before.state.artifact_root,
            version=candidate_version,
        )
        final_dependencies = _resolved_dependencies_for_version(
            artifact_root=before.state.artifact_root,
            version=final_version,
        )
        candidate_binding = replace(
            before.binding,
            collector_environment_sha256=collector_environment_sha256(candidate_dependencies),
        )
        final_binding = replace(
            before.binding,
            collector_environment_sha256=collector_environment_sha256(final_dependencies),
        )
        candidate_seal = construct_deployed_installation_seal(
            binding=candidate_binding,
            evidence_catalog=inputs.evidence_catalog,
            evidence_schema=inputs.evidence_schema,
            artifact_state="PRE_DEPLOY_ARTIFACT_CANDIDATE",
            finalization_required=True,
            policy=inputs.dbt_policy,
        )
        final_seal = construct_deployed_installation_seal(
            binding=final_binding,
            evidence_catalog=inputs.evidence_catalog,
            evidence_schema=inputs.evidence_schema,
            artifact_state="FINALIZED_RUNTIME",
            finalization_required=False,
            policy=inputs.dbt_policy,
        )
        candidate_binding_raw = render_deployed_installation_seal(
            candidate_seal,
            policy=inputs.dbt_policy,
        )
        final_binding_raw = render_deployed_installation_seal(
            final_seal,
            policy=inputs.dbt_policy,
        )
        policy_raw = inputs.dbt_policy.canonical_bytes
        work = Path(tempfile.mkdtemp(prefix=".candidate-work-", dir=_PRIVATE_ROOT))
        os.chmod(work, 0o700)
        try:
            _, artifacts, candidate_tree = _build_private_artifact_set(
                work=work,
                binding_raw=candidate_binding_raw,
                policy_raw=policy_raw,
                version=candidate_version,
                phase="candidate",
                builder=self._artifact_builder,
                child_environment=self._child_environment,
            )
            _, final_artifacts, final_candidate_tree = _build_private_artifact_set(
                work=work,
                binding_raw=final_binding_raw,
                policy_raw=policy_raw,
                version=final_version,
                phase="final",
                builder=self._artifact_builder,
                child_environment=self._child_environment,
            )
            if final_candidate_tree != candidate_tree:
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_BUILD_FAILED")
            artifact_set_sha256 = _sha256(
                _canonical_json(
                    {
                        "candidate": [asdict(item) for item in artifacts],
                        "final": [asdict(item) for item in final_artifacts],
                    }
                )
            )
            after = _attest_runtime(
                inputs=inputs,
                runner=self._runner,
            )
            if after != before:
                raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_REMOTE_STATE_CHANGED")
            candidate_id = artifact_set_sha256
            relative_path = f".dbtobsb/runtime-candidates/{candidate_id}"
            candidate = RuntimeArtifactCandidate(
                candidate_id=candidate_id,
                candidate_relative_path=relative_path,
                artifact_set_sha256=artifact_set_sha256,
                artifacts=artifacts,
                final_artifacts=final_artifacts,
                installation_id=final_seal.installation_id,
                workspace_id=final_seal.workspace_id,
                observed_job_id=final_seal.observed_job_id,
                collector_job_id=final_seal.collector_job_id,
                reconciler_job_id=final_seal.reconciler_job_id,
                current_remote_environment_sha256=before.binding.collector_environment_sha256,
                candidate_environment_sha256=(candidate_seal.collector_environment_sha256),
                final_environment_sha256=final_seal.collector_environment_sha256,
                current_remote_job_graph_sha256=before.job_graph_sha256,
                authenticated_host_sha256=_sha256(before.profile.host.encode()),
                binding_resource_sha256=_sha256(candidate_binding_raw),
                final_binding_resource_sha256=_sha256(final_binding_raw),
            )
            receipt_raw = _canonical_json(asdict(candidate)) + b"\n"
            _atomic_private_write(candidate_tree / "candidate.json", receipt_raw)
            target = _PRIVATE_ROOT / candidate_id
            _validate_private_path(candidate_id)
            _reject_published_version_collision(
                candidate_id=candidate_id,
                artifacts=artifacts,
                final_artifacts=final_artifacts,
            )
            if _path_exists_without_following(target):
                _verify_published_candidate(
                    target / "candidate.json",
                    receipt_raw,
                    artifacts,
                    final_artifacts,
                )
            else:
                _publish_new_candidate_tree(
                    candidate_tree=candidate_tree,
                    candidate_id=candidate_id,
                )
                _validate_private_path(candidate_id)
                _verify_published_candidate(
                    target / "candidate.json",
                    receipt_raw,
                    artifacts,
                    final_artifacts,
                )
            return candidate
        finally:
            shutil.rmtree(work, ignore_errors=True)


def build_runtime_artifact_candidate(inputs: RuntimeSealInputs) -> RuntimeArtifactCandidate:
    """Build a read-only-remote, local private candidate that still requires finalization."""
    _validate_local_layout()
    _reject_inherited_credentials(os.environ)
    child_environment = _sanitized_child_environment(os.environ)
    with _candidate_lock():
        _cleanup_stale_workdirs()
        return _RuntimeCandidateBuilder(
            runner=_FixedCommandRunner(child_environment),
            artifact_builder=_RealArtifactBuilder(),
            environment=os.environ,
        ).build(inputs)


def _read_identity_stdin(
    stream: Any,
) -> tuple[str, str, str, DbtRuntimePolicySnapshot]:
    code = "DBTOBSB_RUNTIME_CANDIDATE_IDENTITY_INPUT_INVALID"
    try:
        raw = stream.buffer.read(8193)
    except (AttributeError, OSError):
        raise RuntimeSealError(code) from None
    if len(raw) > 8192:
        raise RuntimeSealError(code)
    document = _parse_json(raw, code=code)
    keys = {
        "observed_service_principal_name",
        "collector_service_principal_name",
        "job_manager_group_name",
        "dbt_policy_relative_path",
    }
    if set(document) != keys or any(not isinstance(document[key], str) for key in keys):
        raise RuntimeSealError(code)
    relative = document["dbt_policy_relative_path"]
    match = re.fullmatch(
        r"dbtobsb_onboarding/(?P<source>[0-9a-f]{64})/dbt-policy-v1\.json",
        relative,
    )
    if match is None:
        raise RuntimeSealError(code)
    path = _REPO_ROOT
    try:
        parts = PurePosixPath(relative).parts
        for index, part in enumerate(parts):
            path = path / part
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or (
                index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode)
            ):
                raise RuntimeSealError(code)
        if not stat.S_ISREG(path.lstat().st_mode):
            raise RuntimeSealError(code)
        policy = parse_dbt_runtime_policy(path.read_bytes())
    except RuntimeSealError:
        raise
    except (OSError, TypeError, ValueError):
        raise RuntimeSealError(code) from None
    if policy.source_contract_sha256 != match.group("source"):
        raise RuntimeSealError(code)
    return (
        document["observed_service_principal_name"],
        document["collector_service_principal_name"],
        document["job_manager_group_name"],
        policy,
    )


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise RuntimeSealError("DBTOBSB_RUNTIME_CANDIDATE_ARGUMENTS_INVALID")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description="Build a private dbtobsb pre-deploy artifact candidate.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--evidence-catalog", required=True)
    parser.add_argument("--evidence-schema", required=True)
    parser.add_argument("--warehouse-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Build the candidate without putting raw principal identifiers in argv or stdout."""
    try:
        arguments = _parser().parse_args(argv)
        observed, collector, managers, policy = _read_identity_stdin(sys.stdin)
        result = build_runtime_artifact_candidate(
            RuntimeSealInputs(
                profile=arguments.profile,
                target=arguments.target,
                evidence_catalog=arguments.evidence_catalog,
                evidence_schema=arguments.evidence_schema,
                warehouse_id=arguments.warehouse_id,
                observed_service_principal_name=observed,
                collector_service_principal_name=collector,
                job_manager_group_name=managers,
                dbt_policy=policy,
            )
        )
    except RuntimeSealError as error:
        print(error.code, file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "artifact_set_sha256": result.artifact_set_sha256,
                "candidate_id": result.candidate_id,
                "candidate_relative_path": result.candidate_relative_path,
                "finalization_required": True,
                "outcome": "PRE_DEPLOY_ARTIFACT_CANDIDATE_BUILT",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
