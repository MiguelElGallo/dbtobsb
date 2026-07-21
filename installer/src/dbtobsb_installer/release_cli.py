"""Supported attended lifecycle launcher for the private v0.4 Databricks release."""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from datetime import timedelta
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn, Protocol, TextIO, cast

import yaml
from databricks.sdk import WorkspaceClient
from databricks.sdk.credentials_provider import CredentialsProvider, CredentialsStrategy
from databricks.sdk.errors import NotFound
from databricks.sdk.service.catalog import PermissionsChange, Privilege
from databricks.sdk.service.iam import AccessControlRequest, PermissionLevel
from databricks.sdk.service.jobs import CronSchedule, JobSettings, PauseStatus
from dbtobsb_collector.bootstrap import (
    COLLECTION_HEALTH_VIEW,
    INVOCATIONS_TABLE,
    MANIFEST_TABLE,
    NODE_HEALTH_VIEW,
    NODE_RESULTS_TABLE,
    RAW_VOLUME_NAME,
    REGISTRY_TABLE,
    RUN_HEALTH_VIEW,
    STAGE_VOLUME_NAME,
)
from dbtobsb_contracts import load_support_manifest, parse_dbt_runtime_policy

from dbtobsb_installer.app_bindings import (
    AppBindingInputs,
    write_bound_app_overlay,
    write_final_app_overlay,
    write_stage_app_overlay,
)
from dbtobsb_installer.auth import InstallerConnectionInputs, validate_connection
from dbtobsb_installer.onboarding import (
    OnboardingInputs,
    build_onboarding_plan,
    preview_onboarding_project,
    target_from_preflight,
)
from dbtobsb_installer.runtime_seal import (
    RuntimeArtifactCandidate,
    RuntimeSealInputs,
    build_runtime_artifact_candidate,
)

_RELEASE_VERSION = "0.4.0"
_STATE_SCHEMA = "dbtobsb.installer-state.v2"
_STATE_FILE = "release-installation-v2.json"
_LEGACY_STATE_FILE = "release-installation-v1.json"
_TARGET = "smoke"
_APP_KEY = "dbtobsb_smoke"
_APP_NAME = "dbtobsb-smoke"
_WORKSPACE_ROOT = "/Workspace/dbtobsb"
_APP_SOURCE_PATH = f"{_WORKSPACE_ROOT}/.bundle/dbtobsb/{_TARGET}/files/app"
_REMOTE_TERRAFORM_STATE_PATH = (
    f"{_WORKSPACE_ROOT}/.bundle/dbtobsb/{_TARGET}/state/terraform.tfstate"
)
_REMOTE_DIRECT_STATE_PATH = f"{_WORKSPACE_ROOT}/.bundle/dbtobsb/{_TARGET}/state/resources.json"
_LOCAL_DIRECT_STATE_PATH = Path(".databricks/bundle/smoke/resources.json")
_APP_ENVIRONMENT_NAMES = frozenset(
    {
        "DBTOBSB_WAREHOUSE_ID",
        "DBTOBSB_RUN_HEALTH_VIEW",
        "DBTOBSB_NODE_HEALTH_VIEW",
        "DBTOBSB_COLLECTION_HEALTH_VIEW",
    }
)
_BUNDLE_BASE_DIRECTORY = Path(".dbtobsb-bundle-base")
_BUNDLE_BASE_FRAGMENT = _BUNDLE_BASE_DIRECTORY / "00-base.yml"
_TEMPORARY_OVERLAY = Path(".dbtobsb-bundle-base/99-lifecycle.generated.yml")
_SIMPLE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_PROFILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_WAREHOUSE = re.compile(r"^[0-9a-f]{16}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIRECT_LINEAGE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SEALED_DATABRICKS_CLI_SHA256 = "e6107da75e9dfc16c462563e11958c65689ea47d04d54cb4b31d0eb961f40be7"
_MACHO_64_MAGIC = 0xFEEDFACF
_CPU_TYPE_ARM64 = 0x0100000C
_WAIT_TIMEOUT = timedelta(minutes=20)
_BASE_WHEELS = {
    "contracts": "dbtobsb_contracts-0.4.0-py3-none-any.whl",
    "capture": "dbtobsb_capture-0.4.0-py3-none-any.whl",
    "collector": "dbtobsb_collector-0.4.0-py3-none-any.whl",
}
_STAGES = (
    "CONFIGURED",
    "ONBOARDED",
    "BASE_DEPLOYED",
    "CANDIDATE_BUILT",
    "CANDIDATE_DEPLOYED",
    "FINAL_DEPLOYED",
    "OBJECTS_BOOTSTRAPPED",
    "GRANTS_APPLIED",
    "APP_DEPLOYED",
    "INSTALLED",
)
_UNINSTALL_STAGES = (
    "APPROVED",
    "STOPPED",
    "APP_DELETED",
    "GRANTS_REVOKED",
    "OBJECTS_HANDLED",
    "BUNDLE_DESTROYED",
)
_PRODUCT_TABLES = frozenset(
    {
        MANIFEST_TABLE,
        REGISTRY_TABLE,
        INVOCATIONS_TABLE,
        NODE_RESULTS_TABLE,
        RUN_HEALTH_VIEW,
        NODE_HEALTH_VIEW,
        COLLECTION_HEALTH_VIEW,
    }
)
_PRODUCT_VOLUMES = frozenset({RAW_VOLUME_NAME, STAGE_VOLUME_NAME})
_PRODUCT_JOB_NAMES = (
    "dbtobsb-observed",
    "dbtobsb-collector",
    "dbtobsb-reconciler",
    "dbtobsb-bootstrap",
    "dbtobsb-delete",
)
_CREDENTIAL_ENVIRONMENT_PREFIXES = ("DATABRICKS_", "ARM_")
_CREDENTIAL_ENVIRONMENT_NAMES = frozenset(
    {
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_FEDERATED_TOKEN_FILE",
        "AZURE_PASSWORD",
        "AZURE_TENANT_ID",
        "AZURE_USERNAME",
    }
)


class ReleaseCliError(RuntimeError):
    """Stable release error that does not disclose native output or customer values."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class InstallationState:
    """Private resumable state; it contains identifiers but never credentials or raw artifacts."""

    schema: str
    release_version: str
    support_contract_sha256: str
    release_source_commit: str
    databricks_cli_sha256: str
    stage: str
    profile: str
    host: str
    workspace_id: int
    actor: str
    evidence_catalog: str
    evidence_schema: str
    dbt_catalog: str
    dbt_schema: str
    warehouse_id: str
    warehouse_http_path: str
    observed_service_principal_name: str
    observed_service_principal_display: str
    collector_service_principal_name: str
    collector_service_principal_display: str
    job_manager_group_name: str
    app_user_group_name: str
    source_project_relative_path: str
    policy_relative_path: str | None = None
    source_contract_sha256: str | None = None
    expected_runtime_policy_sha256: str | None = None
    candidate_id: str | None = None
    candidate_wheels: Mapping[str, str] | None = None
    final_wheels: Mapping[str, str] | None = None
    final_environment_sha256: str | None = None
    installation_id: str | None = None
    observed_job_id: int | None = None
    collector_job_id: int | None = None
    reconciler_job_id: int | None = None
    direct_state_lineage: str | None = None
    direct_state_serial: int | None = None
    direct_state_sha256: str | None = None
    app_name: str = _APP_NAME
    uninstall_mode: str | None = None
    uninstall_stage: str | None = None

    def __post_init__(self) -> None:
        if (
            self.schema != _STATE_SCHEMA
            or self.release_version != _RELEASE_VERSION
            or self.support_contract_sha256 != load_support_manifest().canonical_sha256
            or _GIT_COMMIT.fullmatch(self.release_source_commit) is None
            or self.databricks_cli_sha256 != _SEALED_DATABRICKS_CLI_SHA256
            or self.stage not in _STAGES
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        strings = (
            self.profile,
            self.host,
            self.actor,
            self.evidence_catalog,
            self.evidence_schema,
            self.dbt_catalog,
            self.dbt_schema,
            self.warehouse_id,
            self.warehouse_http_path,
            self.observed_service_principal_name,
            self.observed_service_principal_display,
            self.collector_service_principal_name,
            self.collector_service_principal_display,
            self.job_manager_group_name,
            self.app_user_group_name,
            self.source_project_relative_path,
            self.app_name,
        )
        if any(not value or value != value.strip() for value in strings):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        if (
            _PROFILE.fullmatch(self.profile) is None
            or self.workspace_id <= 0
            or _WAREHOUSE.fullmatch(self.warehouse_id) is None
            or self.warehouse_http_path != f"/sql/1.0/warehouses/{self.warehouse_id}"
            or any(
                _SIMPLE_IDENTIFIER.fullmatch(value) is None
                for value in (
                    self.evidence_catalog,
                    self.evidence_schema,
                    self.dbt_catalog,
                    self.dbt_schema,
                )
            )
            or self.observed_service_principal_name == self.collector_service_principal_name
            or self.app_name != _APP_NAME
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        for digest in (
            self.source_contract_sha256,
            self.expected_runtime_policy_sha256,
            self.candidate_id,
            self.final_environment_sha256,
            self.installation_id,
        ):
            if digest is not None and _SHA256.fullmatch(digest) is None:
                raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        ids = (self.observed_job_id, self.collector_job_id, self.reconciler_job_id)
        if any(value is not None and value <= 0 for value in ids):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        direct_identity = (
            self.direct_state_lineage,
            self.direct_state_serial,
            self.direct_state_sha256,
        )
        requires_direct_state = _STAGES.index(self.stage) >= _STAGES.index("BASE_DEPLOYED")
        if requires_direct_state:
            if (
                self.direct_state_lineage is None
                or _DIRECT_LINEAGE.fullmatch(self.direct_state_lineage) is None
                or self.direct_state_serial is None
                or self.direct_state_serial < 1
                or self.direct_state_sha256 is None
                or _SHA256.fullmatch(self.direct_state_sha256) is None
            ):
                raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        elif any(value is not None for value in direct_identity):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        wheel_prefixes = {
            "contracts": "dbtobsb_contracts",
            "capture": "dbtobsb_capture",
            "collector": "dbtobsb_collector",
        }
        for wheels, phase in (
            (self.candidate_wheels, "candidate"),
            (self.final_wheels, "final"),
        ):
            if wheels is None:
                continue
            if set(wheels) != set(_BASE_WHEELS):
                raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
            for key, value in wheels.items():
                pattern = re.compile(
                    rf"^{wheel_prefixes[key]}-{re.escape(_RELEASE_VERSION)}"
                    rf"\+dbtobsb\.{phase}\.[0-9a-f]{{64}}-py3-none-any\.whl$"
                )
                if (
                    not isinstance(value, str)
                    or PurePosixPath(value).name != value
                    or pattern.fullmatch(value) is None
                ):
                    raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")
        if (self.uninstall_mode is None) != (self.uninstall_stage is None) or (
            self.uninstall_mode is not None
            and (
                self.stage != "INSTALLED"
                or self.uninstall_mode not in {"DELETE", "RETAIN"}
                or self.uninstall_stage not in _UNINSTALL_STAGES
            )
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID")

    @property
    def job_ids(self) -> tuple[int, int, int]:
        values = (self.observed_job_id, self.collector_job_id, self.reconciler_job_id)
        if any(value is None for value in values):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        return cast(tuple[int, int, int], values)


@dataclass(frozen=True, slots=True)
class BootstrapPreflight:
    """Canonical read-only snapshot that binds preview, approval, and mutation."""

    canonical_json: bytes
    sha256: str

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> BootstrapPreflight:
        try:
            raw = (
                json.dumps(
                    document, ensure_ascii=True, separators=(",", ":"), sort_keys=True
                ).encode("ascii")
                + b"\n"
            )
        except (TypeError, UnicodeError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_INVALID") from None
        return cls(canonical_json=raw, sha256=hashlib.sha256(raw).hexdigest())

    def document(self) -> Mapping[str, Any]:
        value = _parse_json(
            self.canonical_json,
            code="DBTOBSB_INSTALLER_PREFLIGHT_INVALID",
        )
        if not isinstance(value, dict):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_INVALID")
        return cast(Mapping[str, Any], value)


@dataclass(frozen=True, slots=True)
class DirectStateIdentity:
    """Exact CLI 1.8 Direct state bound to a resumable installer checkpoint."""

    lineage: str
    serial: int
    sha256: str


class FixedCommandRunner(Protocol):
    def run(
        self,
        command: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdin: bytes | None = None,
    ) -> bytes: ...


class _SealedCliCredentials(CredentialsStrategy):
    """Supply SDK headers only through the launcher's reverified secure-store CLI."""

    def __init__(self, runner: FixedCommandRunner, profile: str) -> None:
        self._runner = runner
        self._profile = profile

    def auth_type(self) -> str:
        return "dbtobsb-sealed-databricks-cli"

    def __call__(self, cfg: Any) -> CredentialsProvider:
        del cfg

        def headers() -> dict[str, str]:
            document = _parse_json(
                self._runner.run(
                    (
                        "databricks",
                        "auth",
                        "token",
                        "--profile",
                        self._profile,
                        "--output",
                        "json",
                    ),
                    timeout_seconds=60,
                ),
                code="DBTOBSB_INSTALLER_PROFILE_INVALID",
            )
            token = document.get("access_token") if isinstance(document, dict) else None
            if not isinstance(token, str) or not token or len(token) > 64 * 1024:
                raise ReleaseCliError("DBTOBSB_INSTALLER_PROFILE_INVALID")
            return {"Authorization": f"Bearer {token}"}

        return headers


def _file_sha256(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    except OSError:
        raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID") from None


def _verify_databricks_cli_executable(
    path: Path,
    *,
    expected_sha256: str = _SEALED_DATABRICKS_CLI_SHA256,
) -> None:
    try:
        metadata = path.lstat()
        with path.open("rb") as stream:
            header = stream.read(8)
    except OSError:
        raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID") from None
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or len(header) != 8
        or struct.unpack("<II", header) != (_MACHO_64_MAGIC, _CPU_TYPE_ARM64)
        or _SHA256.fullmatch(expected_sha256) is None
        or _file_sha256(path) != expected_sha256
    ):
        raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID")


def _packaged_databricks_cli() -> Path | None:
    path = Path(__file__).resolve().parent / "_native" / "darwin-arm64" / "databricks"
    return path if path.exists() else None


def _resolve_databricks_cli_source() -> Path:
    packaged = _packaged_databricks_cli()
    if packaged is not None:
        return packaged
    discovered = shutil.which("databricks")
    if discovered is None:
        raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID")
    try:
        return Path(discovered).resolve(strict=True)
    except OSError:
        raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID") from None


class SubprocessRunner:
    """Execute only launcher-owned argv and suppress untrusted native diagnostics."""

    def __init__(
        self,
        repository_root: Path,
        *,
        databricks_cli_source: Path | None = None,
        expected_databricks_cli_sha256: str = _SEALED_DATABRICKS_CLI_SHA256,
    ) -> None:
        self._root = repository_root
        source = databricks_cli_source or _resolve_databricks_cli_source()
        _verify_databricks_cli_executable(source, expected_sha256=expected_databricks_cli_sha256)
        try:
            directory = Path(tempfile.mkdtemp(prefix="dbtobsb-cli-"))
            os.chmod(directory, 0o700)
            sealed = directory / "databricks"
            shutil.copyfile(source, sealed)
            os.chmod(sealed, 0o500)
        except OSError:
            raise ReleaseCliError("DBTOBSB_INSTALLER_CLI_SEAL_INVALID") from None
        try:
            _verify_databricks_cli_executable(
                sealed,
                expected_sha256=expected_databricks_cli_sha256,
            )
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        self._databricks_cli = sealed
        self._databricks_cli_sha256 = expected_databricks_cli_sha256
        atexit.register(shutil.rmtree, directory, ignore_errors=True)

    def run(
        self,
        command: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdin: bytes | None = None,
    ) -> bytes:
        if not command or any(not isinstance(value, str) or not value for value in command):
            raise ReleaseCliError("DBTOBSB_INSTALLER_COMMAND_INVALID")
        if command[0] == "databricks":
            _verify_databricks_cli_executable(
                self._databricks_cli,
                expected_sha256=self._databricks_cli_sha256,
            )
            command = (str(self._databricks_cli), *command[1:])
        if any(
            value
            and (
                name in _CREDENTIAL_ENVIRONMENT_NAMES
                or name.startswith(_CREDENTIAL_ENVIRONMENT_PREFIXES)
            )
            for name, value in os.environ.items()
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_INHERITED_CREDENTIAL_REJECTED")
        environment = dict(os.environ)
        environment["DATABRICKS_AUTH_STORAGE"] = "secure"
        try:
            result = subprocess.run(
                command,
                cwd=self._root,
                env=environment,
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_COMMAND_FAILED") from None
        if result.returncode != 0 or len(result.stdout) > 16 * 1024 * 1024:
            raise ReleaseCliError("DBTOBSB_INSTALLER_COMMAND_FAILED")
        return result.stdout


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError
        document[key] = value
    return document


def _parse_json(raw: bytes, *, code: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ReleaseCliError(code) from None


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
        + b"\n"
    )


def _repository_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        configuration = candidate / "databricks.yml"
        if configuration.is_file() and (candidate / "installer" / "pyproject.toml").is_file():
            if candidate.is_symlink() or configuration.is_symlink():
                break
            return candidate
    raise ReleaseCliError("DBTOBSB_INSTALLER_RELEASE_CHECKOUT_REQUIRED")


def _state_path(root: Path) -> Path:
    return root / ".dbtobsb" / _STATE_FILE


def _write_private(path: Path, raw: bytes) -> None:
    parent = path.parent
    try:
        if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
            raise OSError
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(parent, 0o700)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        finally:
            temporary.unlink(missing_ok=True)
    except OSError:
        raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_WRITE_FAILED") from None


def _save_state(root: Path, state: InstallationState) -> None:
    _write_private(_state_path(root), _canonical_json(asdict(state)))


def _load_state(root: Path) -> InstallationState | None:
    path = _state_path(root)
    legacy = root / ".dbtobsb" / _LEGACY_STATE_FILE
    if legacy.exists():
        raise ReleaseCliError("DBTOBSB_INSTALLER_LEGACY_STATE_UNSUPPORTED")
    if not path.exists():
        return None
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise OSError
        document = _parse_json(path.read_bytes(), code="DBTOBSB_INSTALLER_STATE_INVALID")
        if not isinstance(document, dict):
            raise TypeError
        return InstallationState(**document)
    except ReleaseCliError:
        raise
    except (OSError, TypeError):
        raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INVALID") from None


def _stage_at_least(state: InstallationState, stage: str) -> bool:
    return _STAGES.index(state.stage) >= _STAGES.index(stage)


def _uninstall_stage_at_least(state: InstallationState, stage: str) -> bool:
    if state.uninstall_stage is None:
        return False
    return _UNINSTALL_STAGES.index(state.uninstall_stage) >= _UNINSTALL_STAGES.index(stage)


def _value(document: Mapping[str, Any], key: str, expected: type[Any]) -> Any:
    value = document.get(key)
    if not isinstance(value, expected):
        raise ReleaseCliError("DBTOBSB_INSTALLER_DISCOVERY_INVALID")
    return value


def _plain_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


def _select(
    title: str,
    choices: Sequence[Mapping[str, Any]],
    *,
    label_key: str,
    input_stream: TextIO,
    output_stream: TextIO,
) -> Mapping[str, Any]:
    if not choices:
        raise ReleaseCliError("DBTOBSB_INSTALLER_DISCOVERY_EMPTY")
    ordered = sorted(choices, key=lambda item: str(item.get(label_key, "")).casefold())
    if len(ordered) == 1:
        print(f"{title}: {ordered[0][label_key]}", file=output_stream)
        return ordered[0]
    print(title, file=output_stream)
    for index, choice in enumerate(ordered, start=1):
        print(f"  {index}. {choice[label_key]}", file=output_stream)
    print("Select number: ", end="", flush=True, file=output_stream)
    answer = input_stream.readline().strip()
    try:
        selected = int(answer)
    except ValueError:
        raise ReleaseCliError("DBTOBSB_INSTALLER_SELECTION_INVALID") from None
    if selected < 1 or selected > len(ordered) or str(selected) != answer:
        raise ReleaseCliError("DBTOBSB_INSTALLER_SELECTION_INVALID")
    return ordered[selected - 1]


def _project_choices(root: Path) -> list[dict[str, str]]:
    excluded = {".dbtobsb", "dbtobsb_onboarding", "target", "logs", ".venv", "tests"}
    choices: list[dict[str, str]] = []
    for project_file in sorted(root.rglob("dbt_project.yml")):
        relative = project_file.parent.relative_to(root)
        if any(part in excluded or part.startswith(".") for part in relative.parts):
            continue
        choices.append({"path": relative.as_posix(), "name": relative.as_posix()})
    return choices


class ReleaseManager:
    """Compose the already-tested onboarding, seal, Bundle, and lifecycle mechanisms."""

    def __init__(
        self,
        *,
        root: Path,
        runner: FixedCommandRunner,
        input_stream: TextIO,
        output_stream: TextIO,
    ) -> None:
        self.root = root
        self.runner = runner
        self.input = input_stream
        self.output = output_stream
        self._clients: dict[str, WorkspaceClient] = {}
        self._direct_state_overrides: dict[str, DirectStateIdentity] = {}

    def _client(self, profile: str) -> WorkspaceClient:
        client = self._clients.get(profile)
        if client is None:
            try:
                client = WorkspaceClient(
                    profile=profile,
                    credentials_strategy=_SealedCliCredentials(self.runner, profile),
                    product="dbtobsb-installer",
                    product_version="0.4.0",
                )
            except Exception:
                raise ReleaseCliError("DBTOBSB_INSTALLER_PROFILE_INVALID") from None
            self._clients[profile] = client
        return client

    def _run_json(self, command: tuple[str, ...], *, timeout_seconds: int = 60) -> Any:
        return _parse_json(
            self.runner.run(command, timeout_seconds=timeout_seconds),
            code="DBTOBSB_INSTALLER_REMOTE_RESPONSE_INVALID",
        )

    def _release_source_commit(self) -> str:
        try:
            dirty = self.runner.run(
                ("git", "status", "--porcelain", "--untracked-files=no"),
                timeout_seconds=30,
            )
            raw = self.runner.run(("git", "rev-parse", "HEAD"), timeout_seconds=30)
            commit = raw.decode("ascii").strip()
        except (ReleaseCliError, UnicodeDecodeError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_RELEASE_SOURCE_INVALID") from None
        if dirty or _GIT_COMMIT.fullmatch(commit) is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_RELEASE_SOURCE_INVALID")
        return commit

    def _verify_state_release(self, state: InstallationState) -> None:
        if state.release_source_commit != self._release_source_commit():
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_RELEASE_MISMATCH")

    def _discover(self) -> InstallationState:
        profile_root = self._run_json(("databricks", "auth", "profiles", "--output", "json"))
        if not isinstance(profile_root, dict) or not isinstance(profile_root.get("profiles"), list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PROFILE_DISCOVERY_INVALID")
        profiles = [
            item
            for item in profile_root["profiles"]
            if isinstance(item, dict)
            and item.get("valid") is True
            and item.get("cloud") == "azure"
            and item.get("auth_type") == "databricks-cli"
            and isinstance(item.get("name"), str)
            and _PROFILE.fullmatch(item["name"]) is not None
        ]
        profile = _select(
            "Azure Databricks profile",
            profiles,
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        profile_name = cast(str, profile["name"])
        host = _value(profile, "host", str).rstrip("/").lower()
        workspace_raw = _value(profile, "workspace_id", str)
        try:
            workspace_id = int(workspace_raw)
        except ValueError:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PROFILE_DISCOVERY_INVALID") from None
        if workspace_id <= 0 or str(workspace_id) != workspace_raw:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PROFILE_DISCOVERY_INVALID")

        current = self._run_json(
            ("databricks", "current-user", "me", "--profile", profile_name, "--output", "json")
        )
        if not isinstance(current, dict):
            raise ReleaseCliError("DBTOBSB_INSTALLER_CURRENT_ACTOR_INVALID")
        actor = _value(current, "userName", str)

        principal_rows = self._run_json(
            (
                "databricks",
                "service-principals",
                "list",
                "--profile",
                profile_name,
                "--output",
                "json",
            )
        )
        if not isinstance(principal_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PRINCIPAL_DISCOVERY_INVALID")
        principals = [
            item
            for item in principal_rows
            if isinstance(item, dict)
            and item.get("active") is True
            and isinstance(item.get("displayName"), str)
            and isinstance(item.get("applicationId"), str)
        ]
        observed_candidates = [
            item for item in principals if "observed" in item["displayName"].casefold()
        ]
        collector_candidates = [
            item for item in principals if "collector" in item["displayName"].casefold()
        ]
        observed = _select(
            "Observed dbt Job service principal",
            observed_candidates,
            label_key="displayName",
            input_stream=self.input,
            output_stream=self.output,
        )
        collector = _select(
            "Collector service principal",
            collector_candidates,
            label_key="displayName",
            input_stream=self.input,
            output_stream=self.output,
        )
        observed_name = _value(observed, "applicationId", str)
        collector_name = _value(collector, "applicationId", str)
        if observed_name == collector_name:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PRINCIPAL_DISCOVERY_INVALID")

        group_rows = self._run_json(
            ("databricks", "groups", "list", "--profile", profile_name, "--output", "json")
        )
        if not isinstance(group_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_GROUP_DISCOVERY_INVALID")
        groups = [
            item
            for item in group_rows
            if isinstance(item, dict)
            and isinstance(item.get("displayName"), str)
            and item["displayName"].casefold() not in {"admins", "users"}
        ]
        managers = _select(
            "Job manager and App viewer group",
            groups,
            label_key="displayName",
            input_stream=self.input,
            output_stream=self.output,
        )
        group_name = _value(managers, "displayName", str)

        warehouse_rows = self._run_json(
            ("databricks", "warehouses", "list", "--profile", profile_name, "--output", "json")
        )
        if not isinstance(warehouse_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_WAREHOUSE_DISCOVERY_INVALID")
        warehouses = [
            item
            for item in warehouse_rows
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and isinstance(item.get("id"), str)
            and _WAREHOUSE.fullmatch(item["id"]) is not None
        ]
        warehouse = _select(
            "Existing dbt and App SQL warehouse",
            warehouses,
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        warehouse_id = _value(warehouse, "id", str)

        permission = self._run_json(
            (
                "databricks",
                "permissions",
                "get",
                "sql/warehouses",
                warehouse_id,
                "--profile",
                profile_name,
                "--output",
                "json",
            )
        )
        entries = permission.get("access_control_list") if isinstance(permission, dict) else None
        observed_can_use = False
        if isinstance(entries, list):
            for entry in entries:
                if (
                    not isinstance(entry, dict)
                    or entry.get("service_principal_name") != observed_name
                ):
                    continue
                all_permissions = entry.get("all_permissions")
                if isinstance(all_permissions, list) and any(
                    isinstance(item, dict)
                    and item.get("permission_level") in {"CAN_USE", "CAN_MANAGE", "IS_OWNER"}
                    for item in all_permissions
                ):
                    observed_can_use = True
        if not observed_can_use:
            raise ReleaseCliError("DBTOBSB_INSTALLER_OBSERVED_WAREHOUSE_ACCESS_REQUIRED")

        catalog_rows = self._run_json(
            ("databricks", "catalogs", "list", "--profile", profile_name, "--output", "json")
        )
        if not isinstance(catalog_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_CATALOG_DISCOVERY_INVALID")
        catalogs = [
            item
            for item in catalog_rows
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and _SIMPLE_IDENTIFIER.fullmatch(item["name"]) is not None
            and item.get("catalog_type") != "SYSTEM_CATALOG"
        ]
        catalog = _select(
            "Catalog containing the evidence and dbt schemas",
            catalogs,
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        catalog_name = _value(catalog, "name", str)
        schema_rows = self._run_json(
            (
                "databricks",
                "schemas",
                "list",
                catalog_name,
                "--profile",
                profile_name,
                "--output",
                "json",
            )
        )
        if not isinstance(schema_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_SCHEMA_DISCOVERY_INVALID")
        schemas = [
            item
            for item in schema_rows
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and _SIMPLE_IDENTIFIER.fullmatch(item["name"]) is not None
            and item["name"] not in {"default", "information_schema"}
        ]
        evidence = _select(
            "Existing dedicated evidence schema owned by the current administrator",
            [item for item in schemas if item.get("owner") == actor],
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        dbt_schema = _select(
            "Existing dbt target schema owned by the observed service principal",
            [item for item in schemas if item.get("owner") == observed_name],
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        source = _select(
            "dbt Core project to snapshot",
            _project_choices(self.root),
            label_key="name",
            input_stream=self.input,
            output_stream=self.output,
        )
        return InstallationState(
            schema=_STATE_SCHEMA,
            release_version=_RELEASE_VERSION,
            support_contract_sha256=load_support_manifest().canonical_sha256,
            release_source_commit=self._release_source_commit(),
            databricks_cli_sha256=_SEALED_DATABRICKS_CLI_SHA256,
            stage="CONFIGURED",
            profile=profile_name,
            host=host,
            workspace_id=workspace_id,
            actor=actor,
            evidence_catalog=catalog_name,
            evidence_schema=_value(evidence, "name", str),
            dbt_catalog=catalog_name,
            dbt_schema=_value(dbt_schema, "name", str),
            warehouse_id=warehouse_id,
            warehouse_http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            observed_service_principal_name=observed_name,
            observed_service_principal_display=_value(observed, "displayName", str),
            collector_service_principal_name=collector_name,
            collector_service_principal_display=_value(collector, "displayName", str),
            job_manager_group_name=group_name,
            app_user_group_name=group_name,
            source_project_relative_path=_value(source, "path", str),
        )

    def _bootstrap_preflight(self, state: InstallationState) -> BootstrapPreflight:
        """Freeze the complete fresh-install readback before any local or cloud mutation."""
        self._reject_terraform_state(state)
        client = self._client(state.profile)
        try:
            current = self._run_json(
                (
                    "databricks",
                    "current-user",
                    "me",
                    "--profile",
                    state.profile,
                    "--output",
                    "json",
                )
            )
            principal_rows = self._run_json(
                (
                    "databricks",
                    "service-principals",
                    "list",
                    "--profile",
                    state.profile,
                    "--output",
                    "json",
                )
            )
            group_rows = self._run_json(
                (
                    "databricks",
                    "groups",
                    "list",
                    "--profile",
                    state.profile,
                    "--output",
                    "json",
                )
            )
            warehouse_permissions = self._run_json(
                (
                    "databricks",
                    "permissions",
                    "get",
                    "sql/warehouses",
                    state.warehouse_id,
                    "--profile",
                    state.profile,
                    "--output",
                    "json",
                )
            )
            warehouse = client.warehouses.get(state.warehouse_id).as_dict()
            evidence_schema = client.schemas.get(
                f"{state.evidence_catalog}.{state.evidence_schema}"
            ).as_dict()
            target_schema = client.schemas.get(f"{state.dbt_catalog}.{state.dbt_schema}").as_dict()
            schema_grants = client.grants.get(
                "schema", f"{state.evidence_catalog}.{state.evidence_schema}"
            ).as_dict()
            catalog_grants = client.grants.get("catalog", state.evidence_catalog).as_dict()
            app_inventory = tuple(client.apps.list())
            tables = tuple(
                client.tables.list(
                    state.evidence_catalog,
                    state.evidence_schema,
                    omit_columns=True,
                    omit_properties=True,
                )
            )
            volumes = tuple(client.volumes.list(state.evidence_catalog, state.evidence_schema))
            jobs = tuple(
                job
                for name in _PRODUCT_JOB_NAMES
                for job in client.jobs.list(name=name, expand_tasks=True)
            )
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_READBACK_FAILED") from None
        if not isinstance(current, dict) or current.get("userName") != state.actor:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_IDENTITY_CHANGED")
        groups = current.get("groups")
        admin_verified = isinstance(groups, list) and any(
            isinstance(item, dict)
            and (item.get("display") == "admins" or item.get("value") == "admins")
            for item in groups
        )
        if not admin_verified:
            raise ReleaseCliError("DBTOBSB_INSTALLER_WORKSPACE_ADMIN_REQUIRED")
        if not isinstance(principal_rows, list) or not isinstance(group_rows, list):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_READBACK_FAILED")
        active_principals = {
            item.get("applicationId")
            for item in principal_rows
            if isinstance(item, dict) and item.get("active") is True
        }
        available_groups = {
            item.get("displayName") for item in group_rows if isinstance(item, dict)
        }
        if (
            state.observed_service_principal_name not in active_principals
            or state.collector_service_principal_name not in active_principals
            or state.job_manager_group_name not in available_groups
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_PRINCIPAL_CHANGED")
        permission_entries = (
            warehouse_permissions.get("access_control_list")
            if isinstance(warehouse_permissions, dict)
            else None
        )
        observed_can_use = isinstance(permission_entries, list) and any(
            isinstance(entry, dict)
            and entry.get("service_principal_name") == state.observed_service_principal_name
            and isinstance(entry.get("all_permissions"), list)
            and any(
                isinstance(permission, dict)
                and permission.get("permission_level") in {"CAN_USE", "CAN_MANAGE", "IS_OWNER"}
                for permission in entry["all_permissions"]
            )
            for entry in permission_entries
        )
        if not observed_can_use:
            raise ReleaseCliError("DBTOBSB_INSTALLER_OBSERVED_WAREHOUSE_ACCESS_REQUIRED")
        existing_apps = [
            item.as_dict() for item in app_inventory if item.as_dict().get("name") == state.app_name
        ]
        if existing_apps or jobs or tables or volumes:
            raise ReleaseCliError("DBTOBSB_INSTALLER_FRESH_INSTALL_REQUIRED")
        if (
            evidence_schema.get("owner") != state.actor
            or target_schema.get("owner") != state.observed_service_principal_name
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_OWNERSHIP_CHANGED")
        selected_privilege_limits = (
            (
                catalog_grants,
                state.observed_service_principal_name,
                {Privilege.USE_CATALOG.value},
            ),
            (
                catalog_grants,
                state.collector_service_principal_name,
                {Privilege.USE_CATALOG.value},
            ),
            (
                schema_grants,
                state.observed_service_principal_name,
                {Privilege.USE_SCHEMA.value},
            ),
            (
                schema_grants,
                state.collector_service_principal_name,
                {Privilege.USE_SCHEMA.value},
            ),
        )
        if any(
            not self._principal_privileges(document, principal).issubset(allowed)
            for document, principal, allowed in selected_privilege_limits
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_UNEXPECTED_SELECTED_PRINCIPAL_AUTHORITY")
        project_root = self.root / state.source_project_relative_path
        project = project_root / "dbt_project.yml"
        if project.is_symlink() or not project.is_file():
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_PROJECT_INVALID")
        try:
            project_preview = preview_onboarding_project(project_root)
            connection = validate_connection(
                InstallerConnectionInputs(
                    profile=state.profile,
                    canonical_host=state.host,
                    installer_warehouse_id=state.warehouse_id,
                )
            )
            target = target_from_preflight(
                connection=connection,
                dbt_warehouse_id=state.warehouse_id,
                dbt_warehouse_http_path=state.warehouse_http_path,
                catalog=state.dbt_catalog,
                schema=state.dbt_schema,
                artifact_catalog=state.evidence_catalog,
                artifact_schema=state.evidence_schema,
            )
            with tempfile.TemporaryDirectory(prefix="dbtobsb-preflight-onboarding-") as raw:
                onboarding_plan = build_onboarding_plan(
                    OnboardingInputs(
                        source_project=project_root,
                        bundle_root=Path(raw),
                        target=target,
                    )
                )
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_PROJECT_INVALID") from None
        manifest = load_support_manifest()
        document = {
            "app": {
                "deployments": [],
                "end_user_acl": {"group": state.app_user_group_name, "level": "CAN_USE"},
                "environment": {
                    "DBTOBSB_COLLECTION_HEALTH_VIEW": "dbtobsb-collection-health",
                    "DBTOBSB_NODE_HEALTH_VIEW": "dbtobsb-node-health",
                    "DBTOBSB_RUN_HEALTH_VIEW": "dbtobsb-run-health",
                    "DBTOBSB_WAREHOUSE_ID": "dbtobsb-app-warehouse",
                },
                "existing": False,
                "finish_state": "STOPPED",
                "resources": [
                    "dbtobsb-app-warehouse",
                    "dbtobsb-run-health",
                    "dbtobsb-node-health",
                    "dbtobsb-collection-health",
                ],
                "resource_bindings": list(self._expected_app_resources(state).values()),
            },
            "authority": {
                "app_api_access": True,
                "current_actor_matches": True,
                "evidence_schema_owner_matches": True,
                "named_oauth_profile": state.profile,
                "observed_warehouse_access": True,
                "target_schema_owner_matches": True,
                "workspace_admin_group_verified": True,
            },
            "compute": {
                "approved_operations": [
                    "BOUNDED_SERVERLESS_BUNDLE_JOBS",
                    "TWO_BOUNDED_APP_DEPLOYMENT_CHECKS",
                ],
                "warehouse_auto_stop_mins": warehouse.get("auto_stop_mins"),
                "warehouse_cluster_size": warehouse.get("cluster_size"),
                "warehouse_may_auto_start_after_explicit_app_load": True,
                "warehouse_managed_by_product": False,
                "warehouse_state": warehouse.get("state"),
            },
            "customer_state": {
                "existing_evidence_objects": [],
                "existing_product_jobs": [],
                "catalog_direct_grants": _plain_json(catalog_grants),
                "schema_direct_grants": _plain_json(schema_grants),
                "terraform": "ABSENT_DIRECT_FRESH",
            },
            "finish": {
                "app": "STOPPED",
                "jobs": "TERMINAL",
                "reconciler": "PAUSED",
                "warehouse": "UNCHANGED_BY_PRODUCT_REPORT_OBSERVED_STATE",
            },
            "planned": {
                "app_query_count_on_landing": 0,
                "direct_grants": _plain_json(manifest.customer_state["direct_grants"]),
                "jobs": list(_PRODUCT_JOB_NAMES[:3]),
                "objects": _plain_json(manifest.customer_state["objects"]),
                "principal_bindings": {
                    "COLLECTOR_SERVICE_PRINCIPAL": state.collector_service_principal_display,
                    "OBSERVED_SERVICE_PRINCIPAL": state.observed_service_principal_display,
                },
                "temporary_jobs": list(_PRODUCT_JOB_NAMES[3:]),
                "workspace_acl": {
                    "collector": "CAN_READ",
                    "job_manager_group": "CAN_MANAGE",
                    "observed": "CAN_READ",
                },
            },
            "project": {
                "commands": list(project_preview.commands),
                "expected_runtime_policy_sha256": (onboarding_plan.expected_runtime_policy_sha256),
                "include_deps": project_preview.include_deps,
                "job_patch_sha256": onboarding_plan.job_patch_sha256,
                "relative_path": state.source_project_relative_path,
                "selector": project_preview.selector,
                "source_contract_sha256": onboarding_plan.source_contract_sha256,
            },
            "release": {
                "databricks_cli_sha256": state.databricks_cli_sha256,
                "release_source_commit": state.release_source_commit,
                "support_contract_sha256": state.support_contract_sha256,
                "version": state.release_version,
            },
            "workspace": {
                "canonical_host": state.host,
                "cloud": "azure",
                "free_edition": False,
            },
        }
        return BootstrapPreflight.from_document(document)

    def _approve_bootstrap(self, state: InstallationState, preflight: BootstrapPreflight) -> None:
        document = preflight.document()
        planned = cast(Mapping[str, Any], document["planned"])
        app = cast(Mapping[str, Any], document["app"])
        authority = cast(Mapping[str, Any], document["authority"])
        compute = cast(Mapping[str, Any], document["compute"])
        finish = cast(Mapping[str, Any], document["finish"])
        project = cast(Mapping[str, Any], document["project"])
        print("\nInstallation preview", file=self.output)
        print(f"  Preview SHA-256: {preflight.sha256}", file=self.output)
        print("  Release: dbtobsb v0.4.0 fresh installation only", file=self.output)
        print(f"  Named OAuth profile: {authority['named_oauth_profile']}", file=self.output)
        print(f"  Workspace: {state.host}", file=self.output)
        print(
            f"  Evidence schema: {state.evidence_catalog}.{state.evidence_schema}",
            file=self.output,
        )
        print(f"  dbt target: {state.dbt_catalog}.{state.dbt_schema}", file=self.output)
        print(f"  dbt project: {state.source_project_relative_path}", file=self.output)
        print(f"  Observed identity: {state.observed_service_principal_display}", file=self.output)
        print(
            f"  Collector identity: {state.collector_service_principal_display}", file=self.output
        )
        print(
            "  Grant role bindings: "
            f"{json.dumps(planned['principal_bindings'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            f"  Objects: {json.dumps(planned['objects'], separators=(',', ':'))}", file=self.output
        )
        print(
            f"  Direct grants: {json.dumps(planned['direct_grants'], separators=(',', ':'))}",
            file=self.output,
        )
        print(f"  Runtime Jobs: {', '.join(planned['jobs'])}", file=self.output)
        print(f"  Temporary Jobs: {', '.join(planned['temporary_jobs'])}", file=self.output)
        print(
            f"  Workspace ACL: {json.dumps(planned['workspace_acl'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            f"  App bindings: {json.dumps(app['resource_bindings'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            f"  App environment: {json.dumps(app['environment'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            f"  App end-user ACL: {json.dumps(app['end_user_acl'], separators=(',', ':'))}",
            file=self.output,
        )
        print(f"  dbt selector: {project['selector']}", file=self.output)
        print(
            f"  Fixed dbt commands: {json.dumps(project['commands'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            "  Serverless cost scope: "
            f"{json.dumps(compute['approved_operations'], separators=(',', ':'))}",
            file=self.output,
        )
        print(
            "  App deployment checks: two bounded checks; final App state STOPPED.",
            file=self.output,
        )
        print(
            "  Warehouse: dbtobsb does not manage or stop it; current state "
            f"{compute['warehouse_state']}, auto-stop "
            f"{compute['warehouse_auto_stop_mins']} minutes, size "
            f"{compute['warehouse_cluster_size']}.",
            file=self.output,
        )
        print(
            "  App Load observability may auto-start the bound warehouse and incur cost.",
            file=self.output,
        )
        print(f"  Finish state: {json.dumps(finish, separators=(',', ':'))}", file=self.output)
        print(
            "  Unsupported state: any prior App, product Job, object, or Terraform state.",
            file=self.output,
        )
        print("Type APPROVE to continue: ", end="", flush=True, file=self.output)
        if self.input.readline().strip() != "APPROVE":
            raise ReleaseCliError("DBTOBSB_INSTALLER_APPROVAL_REQUIRED")
        if self._bootstrap_preflight(state).sha256 != preflight.sha256:
            raise ReleaseCliError("DBTOBSB_INSTALLER_PREFLIGHT_CHANGED")

    def _onboard(self, state: InstallationState) -> InstallationState:
        try:
            connection = validate_connection(
                InstallerConnectionInputs(
                    profile=state.profile,
                    canonical_host=state.host,
                    installer_warehouse_id=state.warehouse_id,
                )
            )
            target = target_from_preflight(
                connection=connection,
                dbt_warehouse_id=state.warehouse_id,
                dbt_warehouse_http_path=state.warehouse_http_path,
                catalog=state.dbt_catalog,
                schema=state.dbt_schema,
                artifact_catalog=state.evidence_catalog,
                artifact_schema=state.evidence_schema,
            )
            plan = build_onboarding_plan(
                OnboardingInputs(
                    source_project=self.root / state.source_project_relative_path,
                    bundle_root=self.root,
                    target=target,
                )
            )
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_ONBOARDING_FAILED") from None
        return replace(
            state,
            stage="ONBOARDED",
            policy_relative_path=plan.policy_relative_path,
            source_contract_sha256=plan.source_contract_sha256,
            expected_runtime_policy_sha256=plan.expected_runtime_policy_sha256,
        )

    def _wheel_variables(self, state: InstallationState, wheels: Mapping[str, str]) -> list[str]:
        variables = {
            "warehouse_id": state.warehouse_id,
            "evidence_catalog": state.evidence_catalog,
            "evidence_schema": state.evidence_schema,
            "observed_service_principal_name": state.observed_service_principal_name,
            "collector_service_principal_name": state.collector_service_principal_name,
            "job_manager_group_name": state.job_manager_group_name,
            "contracts_wheel_filename": wheels["contracts"],
            "capture_wheel_filename": wheels["capture"],
            "collector_wheel_filename": wheels["collector"],
        }
        argv: list[str] = []
        for key, value in variables.items():
            argv.extend(("--var", f"{key}={value}"))
        return argv

    def _deploy(
        self,
        state: InstallationState,
        wheels: Mapping[str, str],
        *,
        select: str | None = None,
    ) -> None:
        self._reject_terraform_state(state)
        self._verify_bundle_fragments(
            allow_temporary=select
            in {
                "jobs.dbtobsb_bootstrap",
                "jobs.dbtobsb_delete",
            }
        )
        command = [
            "databricks",
            "bundle",
            "deploy",
            "--target",
            _TARGET,
            "--profile",
            state.profile,
            "--auto-approve",
            "--fail-on-active-runs",
            *self._wheel_variables(state, wheels),
        ]
        if select is not None:
            command.extend(("--select", select))
        self.runner.run(tuple(command), timeout_seconds=900)
        self._capture_direct_state(
            state,
            allow_temporary=select
            in {
                "jobs.dbtobsb_bootstrap",
                "jobs.dbtobsb_delete",
            },
        )

    def _reject_terraform_state(self, state: InstallationState) -> None:
        local_terraform = (
            self.root / ".databricks" / "bundle" / _TARGET / "terraform" / "terraform.tfstate"
        )
        if local_terraform.is_symlink() or local_terraform.exists():
            raise ReleaseCliError("DBTOBSB_INSTALLER_TERRAFORM_STATE_UNSUPPORTED")
        workspace = self._client(state.profile).workspace
        try:
            workspace.get_status(_REMOTE_TERRAFORM_STATE_PATH)
        except NotFound:
            pass
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_TERRAFORM_STATE_CHECK_FAILED") from None
        else:
            raise ReleaseCliError("DBTOBSB_INSTALLER_TERRAFORM_STATE_UNSUPPORTED")
        local_direct = self.root / _LOCAL_DIRECT_STATE_PATH
        if local_direct.is_symlink():
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        local_present = local_direct.is_file()
        try:
            workspace.get_status(_REMOTE_DIRECT_STATE_PATH)
        except NotFound:
            remote_present = False
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_CHECK_FAILED") from None
        else:
            remote_present = True
        expected = self._direct_state_overrides.get(state.profile)
        if expected is None and state.direct_state_lineage is not None:
            expected = DirectStateIdentity(
                lineage=state.direct_state_lineage,
                serial=cast(int, state.direct_state_serial),
                sha256=cast(str, state.direct_state_sha256),
            )
        if expected is None:
            if local_present or remote_present:
                raise ReleaseCliError("DBTOBSB_INSTALLER_FRESH_INSTALL_REQUIRED")
            return
        if not local_present or not remote_present:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        actual = self._read_direct_state(
            state, allow_temporary=state.profile in self._direct_state_overrides
        )
        if actual != expected:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_MISMATCH")

    def _read_direct_state(
        self, state: InstallationState, *, allow_temporary: bool
    ) -> DirectStateIdentity:
        local = self.root / _LOCAL_DIRECT_STATE_PATH
        try:
            local_raw = local.read_bytes()
            exported = self._client(state.profile).workspace.export(_REMOTE_DIRECT_STATE_PATH)
            if not isinstance(exported.content, str):
                raise ValueError
            remote_raw = base64.b64decode(exported.content, validate=True)
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID") from None
        if not local_raw or len(local_raw) > 16 * 1024 * 1024 or remote_raw != local_raw:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        try:
            document = json.loads(local_raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID") from None
        if not isinstance(document, dict) or set(document) not in (
            {"state_version", "cli_version", "lineage", "serial", "state"},
            {"state_version", "cli_version", "lineage", "serial", "state", "features"},
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        lineage = document.get("lineage")
        serial = document.get("serial")
        resources = document.get("state")
        expected_resources = {
            "resources.apps.dbtobsb_smoke",
            "resources.jobs.dbtobsb_collector",
            "resources.jobs.dbtobsb_observed",
            "resources.jobs.dbtobsb_reconciler",
        }
        if allow_temporary:
            expected_resources |= {
                "resources.jobs.dbtobsb_bootstrap",
                "resources.jobs.dbtobsb_delete",
            }
        if (
            document.get("state_version") != 2
            or document.get("cli_version") not in {"1.8.0", "v1.8.0"}
            or not isinstance(lineage, str)
            or _DIRECT_LINEAGE.fullmatch(lineage) is None
            or isinstance(serial, bool)
            or not isinstance(serial, int)
            or serial < 1
            or not isinstance(resources, dict)
            or not set(resources).issubset(expected_resources)
            or not {
                "resources.apps.dbtobsb_smoke",
                "resources.jobs.dbtobsb_collector",
                "resources.jobs.dbtobsb_observed",
                "resources.jobs.dbtobsb_reconciler",
            }.issubset(resources)
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        return DirectStateIdentity(
            lineage=lineage,
            serial=serial,
            sha256=hashlib.sha256(local_raw).hexdigest(),
        )

    def _capture_direct_state(
        self, state: InstallationState, *, allow_temporary: bool
    ) -> DirectStateIdentity:
        actual = self._read_direct_state(state, allow_temporary=allow_temporary)
        previous = self._direct_state_overrides.get(state.profile)
        if previous is None and state.direct_state_lineage is not None:
            previous = DirectStateIdentity(
                lineage=state.direct_state_lineage,
                serial=cast(int, state.direct_state_serial),
                sha256=cast(str, state.direct_state_sha256),
            )
        if previous is not None and (
            actual.lineage != previous.lineage or actual.serial < previous.serial
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_MISMATCH")
        self._direct_state_overrides[state.profile] = actual
        return actual

    def _with_direct_state(self, state: InstallationState, **changes: Any) -> InstallationState:
        identity = self._direct_state_overrides.get(state.profile)
        if identity is None and state.direct_state_lineage is not None:
            identity = DirectStateIdentity(
                lineage=state.direct_state_lineage,
                serial=cast(int, state.direct_state_serial),
                sha256=cast(str, state.direct_state_sha256),
            )
        if identity is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_DIRECT_STATE_INVALID")
        return replace(
            state,
            direct_state_lineage=identity.lineage,
            direct_state_serial=identity.serial,
            direct_state_sha256=identity.sha256,
            **changes,
        )

    def _verify_bundle_fragments(self, *, allow_temporary: bool) -> None:
        directory = self.root / _BUNDLE_BASE_DIRECTORY
        base = self.root / _BUNDLE_BASE_FRAGMENT
        allowed = {base.name}
        if allow_temporary:
            allowed.add(_TEMPORARY_OVERLAY.name)
        try:
            if directory.is_symlink() or not directory.is_dir() or base.is_symlink():
                raise OSError
            entries = {entry.name for entry in directory.iterdir()}
            if entries != allowed:
                raise OSError
            if yaml.safe_load(base.read_bytes()) != {"resources": {}}:
                raise OSError
            if allow_temporary:
                temporary = self.root / _TEMPORARY_OVERLAY
                if temporary.is_symlink() or not temporary.is_file():
                    raise OSError
        except (OSError, UnicodeError, yaml.YAMLError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_BUNDLE_FRAGMENT_INVALID") from None

    def _bundle_summary(self, state: InstallationState) -> Mapping[str, Any]:
        document = self._run_json(
            (
                "databricks",
                "bundle",
                "summary",
                "--target",
                _TARGET,
                "--profile",
                state.profile,
                "--output",
                "json",
            )
        )
        if not isinstance(document, dict):
            raise ReleaseCliError("DBTOBSB_INSTALLER_BUNDLE_STATE_INVALID")
        return document

    def _read_job_ids(self, state: InstallationState) -> tuple[int, int, int]:
        summary = self._bundle_summary(state)
        try:
            jobs = summary["resources"]["jobs"]
            values = tuple(
                int(jobs[key]["id"])
                for key in ("dbtobsb_observed", "dbtobsb_collector", "dbtobsb_reconciler")
            )
        except (KeyError, TypeError, ValueError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_BUNDLE_STATE_INVALID") from None
        if any(value <= 0 for value in values) or len(set(values)) != 3:
            raise ReleaseCliError("DBTOBSB_INSTALLER_BUNDLE_STATE_INVALID")
        return cast(tuple[int, int, int], values)

    def _apply_workspace_acl(self, state: InstallationState) -> None:
        status = self._run_json(
            (
                "databricks",
                "workspace",
                "get-status",
                _WORKSPACE_ROOT,
                "--profile",
                state.profile,
                "--output",
                "json",
            )
        )
        if not isinstance(status, dict) or not isinstance(status.get("object_id"), int):
            raise ReleaseCliError("DBTOBSB_INSTALLER_WORKSPACE_ROOT_INVALID")
        client = self._client(state.profile)
        expected = {
            ("group_name", state.job_manager_group_name, "CAN_MANAGE"),
            ("service_principal_name", state.observed_service_principal_name, "CAN_READ"),
            ("service_principal_name", state.collector_service_principal_name, "CAN_READ"),
        }

        def selected_acl() -> set[tuple[str, str, str]]:
            document = client.permissions.get("directories", str(status["object_id"])).as_dict()
            entries = document.get("access_control_list")
            if not isinstance(entries, list):
                raise ValueError
            selected: set[tuple[str, str, str]] = set()
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError
                for kind, principal in (
                    ("group_name", state.job_manager_group_name),
                    ("service_principal_name", state.observed_service_principal_name),
                    ("service_principal_name", state.collector_service_principal_name),
                ):
                    if entry.get(kind) != principal:
                        continue
                    permissions = entry.get("all_permissions")
                    if not isinstance(permissions, list):
                        raise ValueError
                    selected.update(
                        (kind, principal, permission["permission_level"])
                        for permission in permissions
                        if isinstance(permission, dict)
                        and permission.get("inherited") is False
                        and isinstance(permission.get("permission_level"), str)
                    )
            return selected

        try:
            before = selected_acl()
            if before - expected:
                raise ValueError
            if before != expected:
                with suppress(Exception):
                    client.permissions.update(
                        "directories",
                        str(status["object_id"]),
                        access_control_list=[
                            AccessControlRequest(
                                group_name=state.job_manager_group_name,
                                permission_level=PermissionLevel.CAN_MANAGE,
                            ),
                            AccessControlRequest(
                                service_principal_name=state.observed_service_principal_name,
                                permission_level=PermissionLevel.CAN_READ,
                            ),
                            AccessControlRequest(
                                service_principal_name=state.collector_service_principal_name,
                                permission_level=PermissionLevel.CAN_READ,
                            ),
                        ],
                    )
                if selected_acl() != expected:
                    raise ValueError
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_WORKSPACE_ACL_FAILED") from None

    def _build_candidate(self, state: InstallationState) -> RuntimeArtifactCandidate:
        if state.policy_relative_path is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        try:
            policy = parse_dbt_runtime_policy((self.root / state.policy_relative_path).read_bytes())
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_POLICY_INVALID") from None
        return build_runtime_artifact_candidate(
            RuntimeSealInputs(
                profile=state.profile,
                target=_TARGET,
                evidence_catalog=state.evidence_catalog,
                evidence_schema=state.evidence_schema,
                warehouse_id=state.warehouse_id,
                observed_service_principal_name=state.observed_service_principal_name,
                collector_service_principal_name=state.collector_service_principal_name,
                job_manager_group_name=state.job_manager_group_name,
                dbt_policy=policy,
            )
        )

    def _copy_candidate_wheels(
        self,
        candidate_id: str,
        wheels: Mapping[str, str],
        *,
        phase: str,
    ) -> None:
        source_root = self.root / ".dbtobsb" / "runtime-candidates" / candidate_id
        if phase not in {"candidate", "final"}:
            raise ReleaseCliError("DBTOBSB_INSTALLER_ARTIFACT_INVALID")
        for package, filename in wheels.items():
            source = source_root / f"{phase}-wheels" / filename
            destination = self.root / package / "dist" / filename
            try:
                if source.is_symlink() or not source.is_file():
                    raise OSError
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                if source.read_bytes() != destination.read_bytes():
                    raise OSError
            except OSError:
                raise ReleaseCliError("DBTOBSB_INSTALLER_ARTIFACT_INVALID") from None

    def _verify_job_wheels(self, state: InstallationState, wheels: Mapping[str, str]) -> None:
        client = self._client(state.profile)
        expected = set(wheels.values())
        for job_id in state.job_ids:
            try:
                job = client.jobs.get(job_id)
                settings = job.settings.as_dict() if job.settings is not None else {}
            except Exception:
                raise ReleaseCliError("DBTOBSB_INSTALLER_JOB_READBACK_FAILED") from None
            dependencies: set[str] = set()
            for environment in settings.get("environments", []):
                spec = environment.get("spec", {})
                for dependency in spec.get("dependencies", []):
                    if isinstance(dependency, str):
                        dependencies.add(PurePosixPath(dependency).name)
            if not expected.issubset(dependencies):
                raise ReleaseCliError("DBTOBSB_INSTALLER_JOB_READBACK_FAILED")

    def _temporary_job_document(
        self,
        state: InstallationState,
        *,
        key: str,
        entry_point: str,
        parameters: Sequence[str],
    ) -> dict[str, Any]:
        if state.final_wheels is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        return {
            "resources": {
                "jobs": {
                    key: {
                        "name": f"dbtobsb-{key.removeprefix('dbtobsb_')}-temporary",
                        "description": (
                            "Attended fixed lifecycle operation; removed after readback."
                        ),
                        "max_concurrent_runs": 1,
                        "timeout_seconds": 900,
                        "performance_target": "STANDARD",
                        "tasks": [
                            {
                                "task_key": "operation",
                                "timeout_seconds": 900,
                                "max_retries": 0,
                                "retry_on_timeout": False,
                                "environment_key": "operation",
                                "python_wheel_task": {
                                    "package_name": "dbtobsb-collector",
                                    "entry_point": entry_point,
                                    "parameters": list(parameters),
                                },
                            }
                        ],
                        "environments": [
                            {
                                "environment_key": "operation",
                                "spec": {
                                    "client": "5",
                                    "dependencies": [
                                        f"../contracts/dist/{state.final_wheels['contracts']}",
                                        f"../capture/dist/{state.final_wheels['capture']}",
                                        f"../collector/dist/{state.final_wheels['collector']}",
                                        "databricks-sdk==0.117.0",
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }

    def _write_temporary_overlay(self, document: Mapping[str, Any]) -> Path:
        path = self.root / _TEMPORARY_OVERLAY
        try:
            raw = yaml.safe_dump(dict(document), sort_keys=True).encode("utf-8")
        except (UnicodeError, yaml.YAMLError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_INVALID") from None
        _write_private(path, raw)
        return path

    def _temporary_job_id(self, state: InstallationState, key: str) -> int:
        try:
            value = self._bundle_summary(state)["resources"]["jobs"][key]["id"]
            parsed = int(value)
        except (KeyError, TypeError, ValueError):
            raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_INVALID") from None
        if parsed <= 0:
            raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_INVALID")
        return parsed

    def _run_temporary_job(
        self,
        state: InstallationState,
        *,
        key: str,
        entry_point: str,
        parameters: Sequence[str],
        expected_event: str,
        reconcile_bundle: bool = True,
    ) -> None:
        if state.final_wheels is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        overlay = self._write_temporary_overlay(
            self._temporary_job_document(
                state,
                key=key,
                entry_point=entry_point,
                parameters=parameters,
            )
        )
        client = self._client(state.profile)
        temporary_job_id: int | None = None
        operation_succeeded = False
        try:
            self._deploy(state, state.final_wheels, select=f"jobs.{key}")
            temporary_job_id = self._temporary_job_id(state, key)
            previous_run_ids = {
                run.run_id
                for run in client.jobs.list_runs(job_id=temporary_job_id, limit=25)
                if run.run_id is not None
            }
            output = b""
            # A lost local response is not proof that the remote operation failed.
            # The new-run and task-output checks below are the authority.
            with suppress(ReleaseCliError):
                output = self.runner.run(
                    (
                        "databricks",
                        "bundle",
                        "run",
                        key,
                        "--target",
                        _TARGET,
                        "--profile",
                        state.profile,
                        "--output",
                        "json",
                    ),
                    timeout_seconds=1200,
                )
            runs = [
                run
                for run in client.jobs.list_runs(
                    job_id=temporary_job_id, completed_only=True, limit=5
                )
                if run.run_id is not None and run.run_id not in previous_run_ids
            ]
            if not runs:
                raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_READBACK_FAILED")
            latest = max(runs, key=lambda item: item.start_time or 0)
            result_state = getattr(getattr(latest, "state", None), "result_state", None)
            if getattr(result_state, "value", result_state) != "SUCCESS":
                raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_FAILED")
            event_observed = expected_event.encode("ascii") in output
            for task in latest.tasks or []:
                if task.run_id is None:
                    continue
                try:
                    task_output = client.jobs.get_run_output(task.run_id).as_dict()
                    if expected_event in json.dumps(task_output, sort_keys=True):
                        event_observed = True
                except Exception:
                    continue
            if not event_observed:
                raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_READBACK_FAILED")
            operation_succeeded = True
        finally:
            overlay.unlink(missing_ok=True)
            if reconcile_bundle:
                try:
                    self._deploy(state, state.final_wheels)
                except ReleaseCliError:
                    operation_succeeded = False
        if not operation_succeeded:
            raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_CLEANUP_FAILED")

    @staticmethod
    def _permission_change(
        principal: str,
        privileges: Sequence[Privilege],
        *,
        add: bool,
    ) -> PermissionsChange:
        return PermissionsChange(
            principal=principal,
            add=list(privileges) if add else None,
            remove=None if add else list(privileges),
        )

    @staticmethod
    def _principal_privileges(document: object, principal: str) -> set[str]:
        if not isinstance(document, dict):
            raise ValueError
        assignments = document.get("privilege_assignments")
        if not isinstance(assignments, list):
            raise ValueError
        result: set[str] = set()
        for assignment in assignments:
            if not isinstance(assignment, dict) or assignment.get("principal") != principal:
                continue
            privileges = assignment.get("privileges")
            if not isinstance(privileges, list) or any(
                not isinstance(privilege, str) for privilege in privileges
            ):
                raise ValueError
            result.update(cast(list[str], privileges))
        return result

    def _update_product_grants(self, state: InstallationState, *, add: bool) -> None:
        client = self._client(state.profile)
        catalog_name = state.evidence_catalog
        schema_name = f"{state.evidence_catalog}.{state.evidence_schema}"
        collector = state.collector_service_principal_name
        observed = state.observed_service_principal_name
        table_privileges = [Privilege.SELECT, Privilege.MODIFY]
        updates = [
            ("catalog", catalog_name, collector, [Privilege.USE_CATALOG]),
            ("schema", schema_name, collector, [Privilege.USE_SCHEMA]),
            (
                "table",
                f"{schema_name}.dbtobsb_object_manifest",
                collector,
                [Privilege.SELECT],
            ),
            *[
                ("table", f"{schema_name}.{name}", collector, table_privileges)
                for name in ("dbt_artifact_registry", "dbt_invocations", "dbt_node_results")
            ],
            (
                "volume",
                f"{schema_name}.dbtobsb_raw",
                collector,
                [Privilege.READ_VOLUME, Privilege.WRITE_VOLUME],
            ),
            (
                "volume",
                f"{schema_name}.dbtobsb_stage",
                collector,
                [Privilege.READ_VOLUME],
            ),
            ("catalog", catalog_name, observed, [Privilege.USE_CATALOG]),
            ("schema", schema_name, observed, [Privilege.USE_SCHEMA]),
            (
                "volume",
                f"{schema_name}.dbtobsb_stage",
                observed,
                [Privilege.READ_VOLUME, Privilege.WRITE_VOLUME],
            ),
        ]
        try:
            for securable_type, full_name, principal, privileges in updates:
                expected = {privilege.value for privilege in privileges}
                before = self._principal_privileges(
                    client.grants.get(securable_type, full_name).as_dict(), principal
                )
                if before - expected:
                    raise ValueError
                desired = expected if add else set()
                if before != desired:
                    with suppress(Exception):
                        client.grants.update(
                            securable_type,
                            full_name,
                            changes=[self._permission_change(principal, privileges, add=add)],
                        )
                    after = self._principal_privileges(
                        client.grants.get(securable_type, full_name).as_dict(), principal
                    )
                    if after != desired:
                        raise ValueError
        except Exception:
            code = "DBTOBSB_INSTALLER_GRANT_FAILED" if add else "DBTOBSB_UNINSTALL_REVOKE_FAILED"
            raise ReleaseCliError(code) from None

    def _list_deployments(self, state: InstallationState) -> list[Mapping[str, Any]]:
        document = self._run_json(
            (
                "databricks",
                "apps",
                "list-deployments",
                state.app_name,
                "--profile",
                state.profile,
                "--output",
                "json",
            )
        )
        if not isinstance(document, list) or any(not isinstance(item, dict) for item in document):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        return cast(list[Mapping[str, Any]], document)

    @staticmethod
    def _expected_app_resources(state: InstallationState) -> dict[str, Mapping[str, Any]]:
        prefix = f"{state.evidence_catalog}.{state.evidence_schema}"
        return {
            "dbtobsb-app-warehouse": {
                "name": "dbtobsb-app-warehouse",
                "sql_warehouse": {"id": state.warehouse_id, "permission": "CAN_USE"},
            },
            "dbtobsb-run-health": {
                "name": "dbtobsb-run-health",
                "uc_securable": {
                    "permission": "SELECT",
                    "securable_full_name": f"{prefix}.dbt_run_health",
                    "securable_type": "TABLE",
                },
            },
            "dbtobsb-node-health": {
                "name": "dbtobsb-node-health",
                "uc_securable": {
                    "permission": "SELECT",
                    "securable_full_name": f"{prefix}.dbt_node_health",
                    "securable_type": "TABLE",
                },
            },
            "dbtobsb-collection-health": {
                "name": "dbtobsb-collection-health",
                "uc_securable": {
                    "permission": "SELECT",
                    "securable_full_name": f"{prefix}.dbt_collection_health",
                    "securable_type": "TABLE",
                },
            },
        }

    def _app_resources_match(self, state: InstallationState, resources: object) -> bool:
        if not isinstance(resources, list) or any(not isinstance(item, dict) for item in resources):
            return False
        items = cast(list[dict[str, Any]], resources)
        actual = {item.get("name"): item for item in items}
        return actual == self._expected_app_resources(state)

    @staticmethod
    def _app_deployment_matches(deployment: Mapping[str, Any]) -> bool:
        environment = deployment.get("env_vars")
        if not isinstance(environment, list):
            return False
        return (
            deployment.get("mode") == "SNAPSHOT"
            and deployment.get("source_code_path") == _APP_SOURCE_PATH
            and {item.get("name") for item in environment if isinstance(item, dict)}
            == _APP_ENVIRONMENT_NAMES
        )

    def _deploy_app(self, state: InstallationState) -> None:
        if state.final_wheels is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        write_bound_app_overlay(
            AppBindingInputs(
                evidence_catalog=state.evidence_catalog,
                evidence_schema=state.evidence_schema,
                app_warehouse_id=state.warehouse_id,
                app_user_group_name=state.app_user_group_name,
            )
        )
        self._deploy(state, state.final_wheels)
        before = self._list_deployments(state)

        def configured(deployment: Mapping[str, Any]) -> bool:
            return self._app_deployment_matches(deployment)

        accepted_before = [
            item
            for item in before
            if configured(item)
            and isinstance(item.get("status"), dict)
            and item["status"].get("state") == "SUCCEEDED"
        ]
        if before and (len(before) != 1 or len(accepted_before) != 1):
            raise ReleaseCliError("DBTOBSB_INSTALLER_FRESH_APP_REQUIRED")
        before_ids = {item.get("deployment_id") for item in before}
        if None in before_ids or len(before_ids) != len(before):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        run_error: ReleaseCliError | None = None
        deployment: Mapping[str, Any] | None = accepted_before[0] if accepted_before else None
        if deployment is None:
            try:
                self.runner.run(
                    (
                        "databricks",
                        "bundle",
                        "run",
                        _APP_KEY,
                        "--target",
                        _TARGET,
                        "--profile",
                        state.profile,
                    ),
                    timeout_seconds=1200,
                )
            except ReleaseCliError as error:
                run_error = error
            discovery_deadline = time.monotonic() + 120
            deployment_deadline: float | None = None
            while True:
                after = self._list_deployments(state)
                new = [item for item in after if item.get("deployment_id") not in before_ids]
                if len(new) > 1:
                    raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
                configured_new = [item for item in new if configured(item)]
                if new and len(configured_new) != 1:
                    raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
                if len(configured_new) == 1:
                    deployment = configured_new[0]
                    deployment_deadline = deployment_deadline or (time.monotonic() + 1200)
                    status = deployment.get("status")
                    deployment_state = status.get("state") if isinstance(status, dict) else None
                    if deployment_state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                        break
                deadline = deployment_deadline or discovery_deadline
                if time.monotonic() >= deadline:
                    raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
                time.sleep(2)
        try:
            client = self._client(state.profile)
            app = client.apps.get(state.app_name).as_dict()
            if app.get("compute_status", {}).get("state") != "STOPPED":
                client.apps.stop(state.app_name).result(timeout=_WAIT_TIMEOUT)
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_STOP_FAILED") from None
        if deployment is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        status = deployment.get("status")
        env_names = {
            item.get("name") for item in deployment.get("env_vars", []) if isinstance(item, dict)
        }
        if (
            not isinstance(status, dict)
            or status.get("state") != "SUCCEEDED"
            or env_names != _APP_ENVIRONMENT_NAMES
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        if run_error is not None:
            print(
                "The deployment response was lost; independent stopped deployment "
                "readback succeeded.",
                file=self.output,
            )
        write_final_app_overlay(
            AppBindingInputs(
                evidence_catalog=state.evidence_catalog,
                evidence_schema=state.evidence_schema,
                app_warehouse_id=state.warehouse_id,
                app_user_group_name=state.app_user_group_name,
            )
        )
        self._deploy(state, state.final_wheels, select=f"apps.{_APP_KEY}")
        final_before = self._list_deployments(state)
        final_before_ids = {item.get("deployment_id") for item in final_before}
        if None in final_before_ids or len(final_before_ids) != len(final_before):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        # A lost CLI response is resolved only by the independent deployment readback below.
        with suppress(ReleaseCliError):
            self.runner.run(
                (
                    "databricks",
                    "bundle",
                    "run",
                    _APP_KEY,
                    "--target",
                    _TARGET,
                    "--profile",
                    state.profile,
                ),
                timeout_seconds=1200,
            )
        final_deployment: Mapping[str, Any] | None = None
        final_deadline = time.monotonic() + 1200
        while time.monotonic() < final_deadline:
            final_after = self._list_deployments(state)
            final_new = [
                item for item in final_after if item.get("deployment_id") not in final_before_ids
            ]
            configured_final = [item for item in final_new if configured(item)]
            if len(final_new) > 1 or (final_new and len(configured_final) != 1):
                raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
            if len(configured_final) == 1:
                final_deployment = configured_final[0]
                final_status = final_deployment.get("status")
                final_state = final_status.get("state") if isinstance(final_status, dict) else None
                if final_state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                    break
            time.sleep(2)
        if final_deployment is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        final_status = final_deployment.get("status")
        final_env_names = {
            item.get("name")
            for item in final_deployment.get("env_vars", [])
            if isinstance(item, dict)
        }
        if (
            not isinstance(final_status, dict)
            or final_status.get("state") != "SUCCEEDED"
            or final_env_names != _APP_ENVIRONMENT_NAMES
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")
        try:
            final_app = self._client(state.profile).apps.get(state.app_name)
            if final_app.as_dict().get("compute_status", {}).get("state") != "STOPPED":
                self._client(state.profile).apps.stop(state.app_name).result(timeout=_WAIT_TIMEOUT)
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_STOP_FAILED") from None
        try:
            app = self._client(state.profile).apps.get(state.app_name)
            permissions = self._client(state.profile).apps.get_permissions(state.app_name)
            app_document = app.as_dict()
            permission_document = permissions.as_dict()
        except Exception:
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_READBACK_FAILED") from None
        permission_entries = permission_document.get("access_control_list")
        direct_acl: set[tuple[str, str, str]] = set()
        if isinstance(permission_entries, list):
            for item in permission_entries:
                if not isinstance(item, dict):
                    continue
                group = item.get("group_name")
                service_principal = item.get("service_principal_name")
                principal_kind = "group" if isinstance(group, str) else "service_principal"
                principal = group if isinstance(group, str) else service_principal
                if not isinstance(principal, str):
                    continue
                permissions = item.get("all_permissions")
                if not isinstance(permissions, list):
                    continue
                direct_acl.update(
                    (principal_kind, principal, permission["permission_level"])
                    for permission in permissions
                    if isinstance(permission, dict)
                    and permission.get("inherited") is False
                    and isinstance(permission.get("permission_level"), str)
                )
        if (
            app_document.get("compute_status", {}).get("state") != "STOPPED"
            or not self._app_resources_match(state, app_document.get("resources"))
            or direct_acl != {("group", state.app_user_group_name, "CAN_USE")}
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_READBACK_FAILED")

    def bootstrap(self) -> None:
        state = _load_state(self.root)
        if state is not None:
            self._verify_state_release(state)
        if state is not None and state.uninstall_stage is not None:
            raise ReleaseCliError("DBTOBSB_UNINSTALL_RESUME_REQUIRED")
        if state is None:
            state = self._discover()
            preflight = self._bootstrap_preflight(state)
            self._approve_bootstrap(state, preflight)
            _save_state(self.root, state)
        if not _stage_at_least(state, "ONBOARDED"):
            state = self._onboard(state)
            _save_state(self.root, state)
        if not _stage_at_least(state, "BASE_DEPLOYED"):
            write_stage_app_overlay()
            self._deploy(state, _BASE_WHEELS)
            observed, collector, reconciler = self._read_job_ids(state)
            state = self._with_direct_state(
                state,
                stage="BASE_DEPLOYED",
                observed_job_id=observed,
                collector_job_id=collector,
                reconciler_job_id=reconciler,
            )
            self._apply_workspace_acl(state)
            _save_state(self.root, state)
        if not _stage_at_least(state, "CANDIDATE_BUILT"):
            candidate = self._build_candidate(state)
            candidate_wheels = {
                item.project_name.removeprefix("dbtobsb-"): item.filename
                for item in candidate.artifacts
            }
            final_wheels = {
                item.project_name.removeprefix("dbtobsb-"): item.filename
                for item in candidate.final_artifacts
            }
            state = replace(
                state,
                stage="CANDIDATE_BUILT",
                candidate_id=candidate.candidate_id,
                candidate_wheels=candidate_wheels,
                final_wheels=final_wheels,
                final_environment_sha256=candidate.final_environment_sha256,
                installation_id=candidate.installation_id,
            )
            _save_state(self.root, state)
        if (
            state.candidate_id is None
            or state.candidate_wheels is None
            or state.final_wheels is None
        ):
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        candidate_id = state.candidate_id
        candidate_wheels = state.candidate_wheels
        final_wheels = state.final_wheels
        if not _stage_at_least(state, "CANDIDATE_DEPLOYED"):
            self._copy_candidate_wheels(
                candidate_id,
                candidate_wheels,
                phase="candidate",
            )
            self._deploy(state, candidate_wheels)
            self._verify_job_wheels(state, candidate_wheels)
            state = replace(state, stage="CANDIDATE_DEPLOYED")
            state = self._with_direct_state(state)
            _save_state(self.root, state)
        if not _stage_at_least(state, "FINAL_DEPLOYED"):
            self._copy_candidate_wheels(candidate_id, final_wheels, phase="final")
            self._deploy(state, final_wheels)
            self._verify_job_wheels(state, final_wheels)
            state = replace(state, stage="FINAL_DEPLOYED")
            state = self._with_direct_state(state)
            _save_state(self.root, state)
        if not _stage_at_least(state, "OBJECTS_BOOTSTRAPPED"):
            observed, collector, reconciler = state.job_ids
            if state.final_environment_sha256 is None:
                raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
            self._run_temporary_job(
                state,
                key="dbtobsb_bootstrap",
                entry_point="bootstrap",
                parameters=(
                    "--workspace_id",
                    str(state.workspace_id),
                    "--catalog",
                    state.evidence_catalog,
                    "--schema",
                    state.evidence_schema,
                    "--warehouse_id",
                    state.warehouse_id,
                    "--observed_job_id",
                    str(observed),
                    "--collector_job_id",
                    str(collector),
                    "--reconciler_job_id",
                    str(reconciler),
                    "--observed_service_principal_name",
                    state.observed_service_principal_name,
                    "--collector_service_principal_name",
                    state.collector_service_principal_name,
                    "--job_manager_group_name",
                    state.job_manager_group_name,
                    "--collector_environment_sha256",
                    state.final_environment_sha256,
                ),
                expected_event="dbtobsb_bootstrap_verified",
            )
            state = replace(state, stage="OBJECTS_BOOTSTRAPPED")
            state = self._with_direct_state(state)
            _save_state(self.root, state)
        if not _stage_at_least(state, "GRANTS_APPLIED"):
            self._update_product_grants(state, add=True)
            state = replace(state, stage="GRANTS_APPLIED")
            _save_state(self.root, state)
        if not _stage_at_least(state, "APP_DEPLOYED"):
            self._deploy_app(state)
            state = replace(state, stage="APP_DEPLOYED")
            state = self._with_direct_state(state)
            _save_state(self.root, state)
        state = replace(state, stage="INSTALLED")
        _save_state(self.root, state)
        print(
            json.dumps(
                {
                    "app_state": "STOPPED",
                    "event": "dbtobsb_installation_verified",
                    "reconciler_state": "PAUSED",
                    "stage": state.stage,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            file=self.output,
        )

    def _installed_state(self, *, allow_uninstall: bool = False) -> InstallationState:
        state = _load_state(self.root)
        if state is None or state.stage != "INSTALLED":
            raise ReleaseCliError("DBTOBSB_INSTALLER_INSTALLED_STATE_REQUIRED")
        self._verify_state_release(state)
        if state.uninstall_stage is not None and not allow_uninstall:
            raise ReleaseCliError("DBTOBSB_UNINSTALL_RESUME_REQUIRED")
        return state

    def start(self) -> None:
        state = self._installed_state()
        print(
            "Starting the App incurs App compute cost; the SQL warehouse remains unchanged.\n"
            "Type START to acknowledge: ",
            end="",
            flush=True,
            file=self.output,
        )
        if self.input.readline().strip() != "START":
            raise ReleaseCliError("DBTOBSB_START_COST_ACKNOWLEDGEMENT_REQUIRED")
        client = self._client(state.profile)
        before = self._list_deployments(state)
        before_ids = {item.get("deployment_id") for item in before}
        if None in before_ids or len(before_ids) != len(before):
            raise ReleaseCliError("DBTOBSB_START_READBACK_FAILED")
        try:
            with suppress(ReleaseCliError):
                self.runner.run(
                    (
                        "databricks",
                        "bundle",
                        "run",
                        _APP_KEY,
                        "--target",
                        _TARGET,
                        "--profile",
                        state.profile,
                    ),
                    timeout_seconds=1200,
                )
            deadline = time.monotonic() + 1200
            while True:
                after = self._list_deployments(state)
                configured = [
                    item
                    for item in after
                    if item.get("deployment_id") not in before_ids
                    and item.get("source_code_path") == _APP_SOURCE_PATH
                    and {
                        env.get("name") for env in item.get("env_vars", []) if isinstance(env, dict)
                    }
                    == _APP_ENVIRONMENT_NAMES
                ]
                if len(configured) > 1:
                    raise ReleaseCliError("DBTOBSB_START_READBACK_FAILED")
                document = client.apps.get(state.app_name).as_dict()
                if len(configured) == 1:
                    status = configured[0].get("status")
                    deployment_id = configured[0].get("deployment_id")
                    active = document.get("active_deployment") or {}
                    if (
                        isinstance(status, dict)
                        and status.get("state") == "SUCCEEDED"
                        and active.get("deployment_id") == deployment_id
                        and document.get("compute_status", {}).get("state") == "ACTIVE"
                        and document.get("app_status", {}).get("state") == "RUNNING"
                    ):
                        break
                if time.monotonic() >= deadline:
                    raise ReleaseCliError("DBTOBSB_START_READBACK_FAILED")
                time.sleep(2)
        except Exception as error:
            with suppress(Exception):
                client.apps.stop(state.app_name).result(timeout=_WAIT_TIMEOUT)
            if isinstance(error, ReleaseCliError):
                raise
            raise ReleaseCliError("DBTOBSB_START_FAILED") from None
        print('{"app_state":"ACTIVE","event":"dbtobsb_start_verified"}', file=self.output)

    def _pause_reconciler(self, state: InstallationState) -> None:
        client = self._client(state.profile)
        try:
            job = client.jobs.get(state.job_ids[2])
            schedule = job.settings.schedule if job.settings is not None else None
            if schedule is None:
                raise ValueError
            if schedule.pause_status != PauseStatus.PAUSED:
                client.jobs.update(
                    state.job_ids[2],
                    new_settings=JobSettings(
                        schedule=CronSchedule(
                            quartz_cron_expression=schedule.quartz_cron_expression,
                            timezone_id=schedule.timezone_id,
                            pause_status=PauseStatus.PAUSED,
                        )
                    ),
                )
        except Exception:
            raise ReleaseCliError("DBTOBSB_STOP_RECONCILER_PAUSE_FAILED") from None

    def _stop_state(self, state: InstallationState) -> None:
        client = self._client(state.profile)
        self._pause_reconciler(state)

        # Cancellation and App-stop waiters can report a race after the remote
        # resource has already reached its terminal state. Treat the final
        # readback as authoritative so an idempotent stop does not fail merely
        # because a waiter observed that race.
        try:
            for run in list(client.jobs.list_runs(active_only=True)):
                if run.job_id in set(state.job_ids) and run.run_id is not None:
                    with suppress(Exception):
                        client.jobs.cancel_run(run.run_id).result(timeout=_WAIT_TIMEOUT)
            app = client.apps.get(state.app_name).as_dict()
            if app.get("compute_status", {}).get("state") != "STOPPED":
                with suppress(Exception):
                    client.apps.stop(state.app_name).result(timeout=_WAIT_TIMEOUT)
            active = [
                run
                for run in client.jobs.list_runs(active_only=True)
                if run.job_id in set(state.job_ids)
            ]
            app = client.apps.get(state.app_name).as_dict()
        except Exception:
            raise ReleaseCliError("DBTOBSB_STOP_FAILED") from None
        if active or app.get("compute_status", {}).get("state") != "STOPPED":
            raise ReleaseCliError("DBTOBSB_STOP_READBACK_FAILED")

    def _warehouse_cost_receipt(self, state: InstallationState) -> dict[str, Any]:
        try:
            document = self._client(state.profile).warehouses.get(state.warehouse_id).as_dict()
            warehouse_state = document.get("state")
            auto_stop_mins = document.get("auto_stop_mins")
        except Exception:
            raise ReleaseCliError("DBTOBSB_WAREHOUSE_STATE_UNREADABLE") from None
        if not isinstance(warehouse_state, str) or not warehouse_state:
            raise ReleaseCliError("DBTOBSB_WAREHOUSE_STATE_UNREADABLE")
        cost_may_continue = warehouse_state != "STOPPED"
        return {
            "warehouse_auto_stop_mins": auto_stop_mins,
            "warehouse_cost_may_continue": cost_may_continue,
            "warehouse_managed_by_product": False,
            "warehouse_next_action": (
                "NONE"
                if not cost_may_continue
                else "WAIT_FOR_AUTO_STOP_OR_USE_SEPARATELY_AUTHORIZED_DIRECT_STOP"
            ),
            "warehouse_state": warehouse_state,
        }

    def stop(self) -> None:
        state = self._installed_state()
        self._stop_state(state)
        receipt = {
            "app_state": "STOPPED",
            "event": "dbtobsb_stop_verified",
            "reconciler_state": "PAUSED",
            **self._warehouse_cost_receipt(state),
        }
        print(
            json.dumps(receipt, separators=(",", ":"), sort_keys=True),
            file=self.output,
        )

    def _delete_app_if_present(self, state: InstallationState) -> None:
        client = self._client(state.profile)
        try:
            client.apps.delete(state.app_name)
        except Exception:
            try:
                client.apps.get(state.app_name)
            except Exception:
                return
            raise ReleaseCliError("DBTOBSB_UNINSTALL_APP_DELETE_FAILED") from None
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            try:
                client.apps.get(state.app_name)
            except Exception:
                return
            time.sleep(1)
        raise ReleaseCliError("DBTOBSB_UNINSTALL_APP_DELETE_FAILED")

    def _destroy_bundle(self, state: InstallationState) -> None:
        if state.final_wheels is None:
            raise ReleaseCliError("DBTOBSB_INSTALLER_STATE_INCOMPLETE")
        self._reject_terraform_state(state)
        self.runner.run(
            (
                "databricks",
                "bundle",
                "destroy",
                "--target",
                _TARGET,
                "--profile",
                state.profile,
                "--auto-approve",
                *self._wheel_variables(state, state.final_wheels),
            ),
            timeout_seconds=900,
        )

    def _verify_retained_objects(self, state: InstallationState) -> None:
        client = self._client(state.profile)
        prefix = f"{state.evidence_catalog}.{state.evidence_schema}"
        try:
            schema = client.schemas.get(prefix)
            owners = {
                client.tables.get(f"{prefix}.{name}").owner
                for name in (
                    "dbtobsb_object_manifest",
                    "dbt_artifact_registry",
                    "dbt_invocations",
                    "dbt_node_results",
                    "dbt_run_health",
                    "dbt_node_health",
                    "dbt_collection_health",
                )
            }
            owners.update(
                client.volumes.read(f"{prefix}.{name}").owner
                for name in ("dbtobsb_raw", "dbtobsb_stage")
            )
        except Exception:
            raise ReleaseCliError("DBTOBSB_RETAIN_UNINSTALL_READBACK_FAILED") from None
        if schema.owner != state.actor or owners != {state.actor}:
            raise ReleaseCliError("DBTOBSB_RETAIN_UNINSTALL_READBACK_FAILED")

    def _product_object_presence(self, state: InstallationState) -> frozenset[str]:
        client = self._client(state.profile)
        prefix = f"{state.evidence_catalog}.{state.evidence_schema}"
        try:
            schema = client.schemas.get(prefix)
            tables = {
                item.name
                for item in client.tables.list(
                    state.evidence_catalog,
                    state.evidence_schema,
                    omit_columns=True,
                    omit_properties=True,
                )
                if item.name in _PRODUCT_TABLES
            }
            volumes = {
                item.name
                for item in client.volumes.list(
                    state.evidence_catalog,
                    state.evidence_schema,
                )
                if item.name in _PRODUCT_VOLUMES
            }
        except Exception:
            raise ReleaseCliError("DBTOBSB_DELETE_UNINSTALL_READBACK_FAILED") from None
        if schema.owner != state.actor:
            raise ReleaseCliError("DBTOBSB_DELETE_UNINSTALL_READBACK_FAILED")
        return frozenset(
            {
                *(name for name in tables if name is not None),
                *(name for name in volumes if name is not None),
            }
        )

    def _delete_product_objects(self, state: InstallationState) -> None:
        expected = _PRODUCT_TABLES | _PRODUCT_VOLUMES
        before = self._product_object_presence(state)
        if before and before != expected:
            raise ReleaseCliError("DBTOBSB_DELETE_UNINSTALL_PARTIAL_STATE")
        if before == expected:
            self._run_temporary_job(
                state,
                key="dbtobsb_delete",
                entry_point="uninstall-delete",
                parameters=(
                    "--catalog",
                    state.evidence_catalog,
                    "--schema",
                    state.evidence_schema,
                ),
                expected_event="dbtobsb_delete_uninstall_verified",
                reconcile_bundle=False,
            )
        if self._product_object_presence(state):
            raise ReleaseCliError("DBTOBSB_DELETE_UNINSTALL_READBACK_FAILED")

    def _clear_local_state(self) -> None:
        targets = (
            self.root / ".dbtobsb",
            self.root / "dbtobsb_onboarding",
            self.root / ".dbtobsb-observed.generated.yml",
            self.root / ".dbtobsb-app-bindings.generated.yml",
            self.root / _TEMPORARY_OVERLAY,
        )
        for target in targets:
            try:
                if target.is_symlink():
                    raise OSError
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink(missing_ok=True)
            except OSError:
                raise ReleaseCliError("DBTOBSB_UNINSTALL_LOCAL_CLEANUP_FAILED") from None

    def uninstall(self, *, delete: bool) -> None:
        state = self._installed_state(allow_uninstall=True)
        expected = "DELETE" if delete else "RETAIN"
        if state.uninstall_mode is not None and state.uninstall_mode != expected:
            raise ReleaseCliError("DBTOBSB_UNINSTALL_MODE_MISMATCH")
        consequence = (
            "irreversibly delete the nine product objects and raw archives"
            if delete
            else "remove runtime resources and preserve all nine product objects"
        )
        print(
            f"This will {consequence}.\nType {expected} to continue: ",
            end="",
            flush=True,
            file=self.output,
        )
        if self.input.readline().strip() != expected:
            raise ReleaseCliError("DBTOBSB_UNINSTALL_APPROVAL_REQUIRED")
        if delete:
            print(
                "Confirm retention, legal hold, and required export are satisfied.\n"
                "Type DELETE PRODUCT DATA: ",
                end="",
                flush=True,
                file=self.output,
            )
            if self.input.readline().strip() != "DELETE PRODUCT DATA":
                raise ReleaseCliError("DBTOBSB_DELETE_UNINSTALL_APPROVAL_REQUIRED")
        if state.uninstall_stage is None:
            state = replace(
                state,
                uninstall_mode=expected,
                uninstall_stage="APPROVED",
            )
            _save_state(self.root, state)
        if not _uninstall_stage_at_least(state, "STOPPED"):
            self._stop_state(state)
            state = replace(state, uninstall_stage="STOPPED")
            _save_state(self.root, state)
        if not _uninstall_stage_at_least(state, "APP_DELETED"):
            self._delete_app_if_present(state)
            state = replace(state, uninstall_stage="APP_DELETED")
            _save_state(self.root, state)
        if not _uninstall_stage_at_least(state, "GRANTS_REVOKED"):
            self._update_product_grants(state, add=False)
            state = replace(state, uninstall_stage="GRANTS_REVOKED")
            _save_state(self.root, state)
        if not _uninstall_stage_at_least(state, "OBJECTS_HANDLED"):
            if delete:
                self._delete_product_objects(state)
            else:
                self._verify_retained_objects(state)
            state = replace(state, uninstall_stage="OBJECTS_HANDLED")
            _save_state(self.root, state)
        if not _uninstall_stage_at_least(state, "BUNDLE_DESTROYED"):
            self._destroy_bundle(state)
            state = replace(state, uninstall_stage="BUNDLE_DESTROYED")
            _save_state(self.root, state)
        mode = "DELETE" if delete else "RETAIN"
        warehouse_receipt = self._warehouse_cost_receipt(state)
        self._clear_local_state()
        print(
            json.dumps(
                {
                    "app_state": "REMOVED",
                    "event": "dbtobsb_uninstall_verified",
                    "mode": mode,
                    "product_objects": "REMOVED" if delete else "RETAINED",
                    "schema_preserved": True,
                    **warehouse_receipt,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            file=self.output,
        )


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ReleaseCliError("DBTOBSB_INSTALLER_ARGUMENTS_INVALID")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="dbtobsb", description=__doc__, allow_abbrev=False)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("bootstrap", help="Install or resume the attended private release")
    subcommands.add_parser("start", help="Acknowledge cost and start the read-only App")
    subcommands.add_parser("stop", help="Stop App compute and pause reconciliation")
    uninstall = subcommands.add_parser("uninstall", help="Remove the installed product")
    mode = uninstall.add_mutually_exclusive_group(required=True)
    mode.add_argument("--retain", action="store_true")
    mode.add_argument("--delete", action="store_true")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    manager: ReleaseManager | None = None,
) -> int:
    """Run one closed lifecycle command and emit only stable failure codes."""

    try:
        arguments = _parser().parse_args(argv)
        active = manager or ReleaseManager(
            root=_repository_root(),
            runner=SubprocessRunner(_repository_root()),
            input_stream=sys.stdin,
            output_stream=sys.stdout,
        )
        if arguments.command == "bootstrap":
            active.bootstrap()
        elif arguments.command == "start":
            active.start()
        elif arguments.command == "stop":
            active.stop()
        elif arguments.command == "uninstall":
            active.uninstall(delete=bool(arguments.delete))
        else:
            raise ReleaseCliError("DBTOBSB_INSTALLER_ARGUMENTS_INVALID")
    except ReleaseCliError as error:
        print(error.code, file=sys.stderr)
        return 2
    except Exception:
        print("DBTOBSB_INSTALLER_FAILED", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
