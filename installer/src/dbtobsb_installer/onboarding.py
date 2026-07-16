"""Deterministic, non-mutating dbt Core project onboarding artifacts.

The generated snapshot and Job fragment are review inputs.  This module never calls Databricks,
applies a Bundle, edits an existing Job, or accepts caller-supplied dbt commands and paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn, cast
from urllib.parse import urlsplit

import yaml
from dbt.config.project import (
    Project,
    package_and_project_data_from_root,
    package_config_from_data,
)
from dbt.config.renderer import DbtProjectYamlRenderer, PackageRenderer
from dbt.deps.base import downloads_directory
from dbt.deps.resolver import resolve_packages
from dbt.flags import set_from_args
from dbt.task.deps import _create_sha1_hash
from dbt_common.context import set_invocation_context
from dbtobsb_contracts import (
    DbtRuntimePolicyError,
    DbtRuntimePolicyInputs,
    DbtRuntimePolicySnapshot,
    DbtRuntimeTarget,
    load_support_manifest,
    render_dbt_runtime_policy,
)
from yaml.resolver import BaseResolver

from dbtobsb_installer.auth import ValidatedInstallerConnection

_PROFILE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")
_SELECTOR_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_WAREHOUSE_HTTP_PATH = re.compile(r"^/sql/1\.0/warehouses/(?P<warehouse>[0-9a-f]{16})$")
_REGULAR_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OUTPUT_ROOT = "dbtobsb_onboarding"
_GENERATED_PROFILE = "profiles.yml"
_POLICY_FILE = "dbt-policy-v1.json"
_PATCH_FILE = "dbt-observed-job.generated.yml"
_ACTIVE_PATCH_FILE = ".dbtobsb-observed.generated.yml"
_RECEIPT_FILE = "onboarding-receipt.json"
_SOURCE_CONTRACT_DOMAIN = "dbtobsb.dbt-source-contract.v1"
_MAX_SOURCE_FILE_BYTES = 128 * 1024 * 1024
_MAX_SOURCE_TOTAL_BYTES = 512 * 1024 * 1024
_IGNORED_TOP_LEVEL = frozenset(
    {
        "logs",
        "target",
        _OUTPUT_ROOT,
    }
)
_FORBIDDEN_SOURCE_NAMES = frozenset({".env", ".user.yml"})
_TARGET_TOKEN = object()


class DbtOnboardingError(RuntimeError):
    """Sanitized onboarding failure containing no project content or connection values."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: _StrictLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_YAML_DUPLICATE_KEY")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


class _DeterministicDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        del data
        return True


@dataclass(frozen=True, slots=True, repr=False)
class DbtTargetBinding:
    """Preflight-validated nonsecret dbt target values rendered into the snapshot."""

    canonical_workspace_hostname: str
    warehouse_id: str
    warehouse_http_path: str
    catalog: str
    schema: str
    artifact_catalog: str
    artifact_schema: str

    def __init__(
        self,
        *,
        canonical_workspace_hostname: str,
        warehouse_id: str,
        warehouse_http_path: str,
        catalog: str,
        schema: str,
        artifact_catalog: str,
        artifact_schema: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _TARGET_TOKEN:
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_TARGET_CONSTRUCTION_DENIED")
        match = _WAREHOUSE_HTTP_PATH.fullmatch(warehouse_http_path)
        if (
            re.fullmatch(
                r"adb-[0-9]{1,20}\.[0-9]{1,20}\.azuredatabricks\.net", canonical_workspace_hostname
            )
            is None
            or _WAREHOUSE_ID.fullmatch(warehouse_id) is None
            or match is None
            or match.group("warehouse") != warehouse_id
            or _REGULAR_IDENTIFIER.fullmatch(catalog) is None
            or _REGULAR_IDENTIFIER.fullmatch(schema) is None
            or _REGULAR_IDENTIFIER.fullmatch(artifact_catalog) is None
            or _REGULAR_IDENTIFIER.fullmatch(artifact_schema) is None
        ):
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_TARGET_INVALID")
        object.__setattr__(self, "canonical_workspace_hostname", canonical_workspace_hostname)
        object.__setattr__(self, "warehouse_id", warehouse_id)
        object.__setattr__(self, "warehouse_http_path", warehouse_http_path)
        object.__setattr__(self, "catalog", catalog)
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "artifact_catalog", artifact_catalog)
        object.__setattr__(self, "artifact_schema", artifact_schema)

    def __repr__(self) -> str:
        return "DbtTargetBinding(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class OnboardingInputs:
    """Local project and preflight target; commands, selector, and output paths are derived."""

    source_project: Path
    bundle_root: Path
    target: DbtTargetBinding

    def __repr__(self) -> str:
        return "OnboardingInputs(<redacted>)"


@dataclass(frozen=True, slots=True)
class DbtOnboardingPlan:
    """Sanitized immutable receipt for one generated review directory."""

    policy_contract_version: str
    support_contract_sha256: str
    source_contract_sha256: str
    expected_runtime_policy_sha256: str
    project_relative_path: str
    profiles_relative_path: str
    policy_relative_path: str
    job_patch_relative_path: str
    receipt_relative_path: str
    policy_sha256: str
    job_patch_sha256: str
    file_count: int
    include_deps: bool


def target_from_preflight(
    *,
    connection: ValidatedInstallerConnection,
    dbt_warehouse_id: str,
    dbt_warehouse_http_path: str,
    catalog: str,
    schema: str,
    artifact_catalog: str,
    artifact_schema: str,
) -> DbtTargetBinding:
    """Construct a target only from a previously validated named-profile connection."""

    if not isinstance(connection, ValidatedInstallerConnection):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_CONNECTION_INVALID")
    parsed = urlsplit(connection.canonical_host)
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
    ):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_CONNECTION_INVALID")
    return DbtTargetBinding(
        canonical_workspace_hostname=hostname,
        warehouse_id=dbt_warehouse_id,
        warehouse_http_path=dbt_warehouse_http_path,
        catalog=catalog,
        schema=schema,
        artifact_catalog=artifact_catalog,
        artifact_schema=artifact_schema,
        _construction_token=_TARGET_TOKEN,
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_yaml(raw: bytes, *, code: str) -> Any:
    try:
        text = raw.decode("utf-8")
        if "\x00" in text:
            raise ValueError
        return yaml.load(text, Loader=_StrictLoader)
    except DbtOnboardingError:
        raise
    except (UnicodeError, ValueError, yaml.YAMLError):
        raise DbtOnboardingError(code) from None


def _real_directory(path: Path, *, code: str) -> Path:
    try:
        if path.is_symlink() or not path.is_dir():
            raise OSError
        resolved = path.resolve(strict=True)
        if resolved.is_symlink() or not resolved.is_dir():
            raise OSError
        return resolved
    except OSError:
        raise DbtOnboardingError(code) from None


def _read_source_files(source: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total = 0
    try:
        for candidate in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
            relative = candidate.relative_to(source)
            parts = relative.parts
            if not parts or parts[0] in _IGNORED_TOP_LEVEL:
                continue
            if candidate.is_symlink():
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_SYMLINK_UNSUPPORTED")
            if candidate.is_dir():
                continue
            if not candidate.is_file() or any(part in {"", ".", ".."} for part in parts):
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_ENTRY_INVALID")
            posix = PurePosixPath(*parts).as_posix()
            if posix == _GENERATED_PROFILE:
                continue
            if (
                any(part.startswith(".") for part in parts)
                or candidate.name in _FORBIDDEN_SOURCE_NAMES
            ):
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_FILE_UNSUPPORTED")
            raw = candidate.read_bytes()
            if len(raw) > _MAX_SOURCE_FILE_BYTES:
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_FILE_TOO_LARGE")
            total += len(raw)
            if total > _MAX_SOURCE_TOTAL_BYTES:
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_TOO_LARGE")
            if posix in files:
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_ENTRY_INVALID")
            files[posix] = raw
    except DbtOnboardingError:
        raise
    except OSError:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SOURCE_READ_FAILED") from None
    return files


def _project_profile(source_files: Mapping[str, bytes]) -> str:
    raw = source_files.get("dbt_project.yml")
    if raw is None:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DBT_PROJECT_REQUIRED")
    document = _strict_yaml(raw, code="DBTOBSB_ONBOARDING_DBT_PROJECT_INVALID")
    if not isinstance(document, dict):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DBT_PROJECT_INVALID")
    if {"flags", "log-path", "packages-install-path", "target-path"}.intersection(document):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DBT_PROJECT_FLAGS_UNSUPPORTED")
    profile = document.get("profile")
    if not isinstance(profile, str) or _PROFILE_NAME.fullmatch(profile) is None:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_PROFILE_NAME_INVALID")
    return profile


def _selector(source_files: Mapping[str, bytes]) -> str:
    raw = source_files.get("selectors.yml")
    if raw is None:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SELECTORS_REQUIRED")
    if b"{{" in raw or b"{%" in raw:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SELECTORS_INVALID")
    document = _strict_yaml(raw, code="DBTOBSB_ONBOARDING_SELECTORS_INVALID")
    if not isinstance(document, dict) or set(document) != {"selectors"}:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SELECTORS_INVALID")
    selectors = document["selectors"]
    if not isinstance(selectors, list) or len(selectors) != 1 or not isinstance(selectors[0], dict):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SELECTOR_COUNT_INVALID")
    name = selectors[0].get("name")
    if not isinstance(name, str) or _SELECTOR_NAME.fullmatch(name) is None:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_SELECTOR_INVALID")
    return name


def _dependency_policy(
    source: Path, source_files: Mapping[str, bytes]
) -> tuple[bool, tuple[str, ...], str | None]:
    definition_names = tuple(
        name for name in ("dependencies.yml", "packages.yml") if name in source_files
    )
    lock = source_files.get("package-lock.yml")
    if not definition_names:
        if lock is not None:
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_UNEXPECTED")
        return False, (), None
    if len(definition_names) != 1:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_DEFINITION_AMBIGUOUS")
    if lock is None:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_REQUIRED")
    for name in (*definition_names, "package-lock.yml"):
        if b"{{" in source_files[name] or b"{%" in source_files[name]:
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_TEMPLATE_UNSUPPORTED")
    lock_document = _strict_yaml(lock, code="DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_INVALID")
    if not isinstance(lock_document, dict) or set(lock_document) != {"packages", "sha1_hash"}:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_INVALID")
    previous_hash = lock_document["sha1_hash"]
    packages = lock_document["packages"]
    if (
        not isinstance(previous_hash, str)
        or _SHA1.fullmatch(previous_hash) is None
        or not isinstance(packages, list)
        or not packages
    ):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_INVALID")
    try:
        packages_data, _ = package_and_project_data_from_root(str(source))
        rendered = PackageRenderer({}).render_data(packages_data)
        configuration = package_config_from_data(rendered, packages_data)
        current_hash = _create_sha1_hash(configuration.packages)
        set_invocation_context({})
        set_from_args(
            argparse.Namespace(PROJECT_DIR=str(source), PROFILES_DIR=None),
            {},
        )
        project = Project.from_project_root(
            str(source),
            DbtProjectYamlRenderer(cli_vars={}, require_vars=False),
            verify_version=True,
            validate=True,
        )
        with downloads_directory():
            resolved = resolve_packages(configuration.packages, project, {})
        renderer = PackageRenderer({})
        expected_packages: list[dict[str, object]] = []
        for package in resolved:
            entry = cast(dict[str, object], package.to_dict())
            entry["name"] = package.get_project_name(project, renderer)
            expected_packages.append(entry)
    except Exception:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_DEFINITION_INVALID") from None
    if current_hash != previous_hash or lock_document != {
        "packages": expected_packages,
        "sha1_hash": current_hash,
    }:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_DEPENDENCY_LOCK_MISMATCH")
    return True, definition_names, _sha256(lock)


def _profile_bytes(profile_name: str, target: DbtTargetBinding) -> bytes:
    manifest = load_support_manifest()
    profile_contract = cast(Mapping[str, Any], manifest.onboarding["profile_target"])
    output = {
        "type": profile_contract["type"],
        "method": profile_contract["method"],
        "host": target.canonical_workspace_hostname,
        "http_path": target.warehouse_http_path,
        "token": profile_contract["token"],
        "catalog": target.catalog,
        "schema": target.schema,
        "threads": profile_contract["threads"],
    }
    if list(output) != list(profile_contract["output_keys"]):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_PROFILE_CONTRACT_INVALID")
    document = {profile_name: {"target": "dbtobsb", "outputs": {"dbtobsb": output}}}
    return yaml.dump(
        document,
        Dumper=_DeterministicDumper,
        allow_unicode=False,
        default_flow_style=False,
        sort_keys=False,
    ).encode("ascii")


def _source_contract(source_files: Mapping[str, bytes]) -> tuple[dict[str, str], str]:
    digests = {name: _sha256(raw) for name, raw in sorted(source_files.items())}
    digest = _sha256(_canonical_json({"domain": _SOURCE_CONTRACT_DOMAIN, "source_sha256": digests}))
    return digests, digest


def _runtime_policy(
    *,
    source_sha256: Mapping[str, str],
    source_contract_sha256: str,
    project_directory: str,
    profile_name: str,
    selector: str,
    include_deps: bool,
    dependency_definition_files: tuple[str, ...],
    dependency_lock_sha256: str | None,
    target: DbtTargetBinding,
) -> DbtRuntimePolicySnapshot:
    try:
        return render_dbt_runtime_policy(
            DbtRuntimePolicyInputs(
                source_sha256=source_sha256,
                source_contract_sha256=source_contract_sha256,
                project_directory=project_directory,
                profile_name=profile_name,
                selector=selector,
                include_deps=include_deps,
                dependency_definition_files=dependency_definition_files,
                dependency_lock_sha256=dependency_lock_sha256,
                target=DbtRuntimeTarget(
                    host=target.canonical_workspace_hostname,
                    warehouse_id=target.warehouse_id,
                    http_path=target.warehouse_http_path,
                    catalog=target.catalog,
                    schema=target.schema,
                    artifact_catalog=target.artifact_catalog,
                    artifact_schema=target.artifact_schema,
                ),
            )
        )
    except DbtRuntimePolicyError:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_POLICY_INVALID") from None


def _job_patch(policy: DbtRuntimePolicySnapshot) -> bytes:
    manifest = load_support_manifest()
    project_directory = policy.project_directory
    installed_project_directory = "${workspace.file_path}/" + project_directory.removeprefix("./")
    installed_policy_path = (
        installed_project_directory.rsplit("/project", maxsplit=1)[0] + "/dbt-policy-v1.json"
    )
    packages = cast(Mapping[str, str], manifest.dbt["packages"])
    document = {
        "resources": {
            "jobs": {
                "dbtobsb_observed": {
                    "name": "dbtobsb-observed",
                    "description": (
                        "Approved customer dbt Core project with deterministic dbtobsb "
                        "evidence collection."
                    ),
                    "max_concurrent_runs": 1,
                    "timeout_seconds": 1200,
                    "performance_target": "STANDARD",
                    "run_as": {"service_principal_name": "${var.observed_service_principal_name}"},
                    "permissions": [
                        {
                            "level": "CAN_VIEW",
                            "service_principal_name": "${var.collector_service_principal_name}",
                        },
                        {"level": "CAN_MANAGE", "group_name": "${var.job_manager_group_name}"},
                    ],
                    "tasks": [
                        {
                            "task_key": "dbt_build",
                            "timeout_seconds": 900,
                            "max_retries": 0,
                            "retry_on_timeout": False,
                            "environment_key": "dbt",
                            "python_wheel_task": {
                                "package_name": "dbtobsb-collector",
                                "entry_point": "run-dbt",
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
                                    installed_project_directory,
                                    "--policy_path",
                                    installed_policy_path,
                                ],
                            },
                        },
                        {
                            "task_key": "collect_dbt_evidence",
                            "depends_on": [{"task_key": "dbt_build"}],
                            "run_if": "ALL_DONE",
                            "timeout_seconds": 900,
                            "max_retries": 0,
                            "retry_on_timeout": False,
                            "run_job_task": {
                                "job_id": "${resources.jobs.dbtobsb_collector.id}",
                                "job_parameters": {
                                    "workspace_id": "{{workspace.id}}",
                                    "observed_job_id": "{{job.id}}",
                                    "observed_job_run_id": "{{job.run_id}}",
                                    "dbt_task_run_id": "{{tasks.dbt_build.run_id}}",
                                    "observed_task_key": "dbt_build",
                                    "repair_count": "{{job.repair_count}}",
                                    "execution_count": "{{tasks.dbt_build.execution_count}}",
                                },
                            },
                        },
                    ],
                    "environments": [
                        {
                            "environment_key": "dbt",
                            "spec": {
                                "client": str(manifest.platform["serverless_environment_client"]),
                                "dependencies": [
                                    "./contracts/dist/${var.contracts_wheel_filename}",
                                    "./capture/dist/${var.capture_wheel_filename}",
                                    "./collector/dist/${var.collector_wheel_filename}",
                                    *[
                                        f"{name}=={version}"
                                        for name, version in sorted(packages.items())
                                    ],
                                ],
                            },
                        }
                    ],
                }
            }
        }
    }
    return yaml.dump(
        document,
        Dumper=_DeterministicDumper,
        allow_unicode=False,
        default_flow_style=False,
        sort_keys=False,
        width=4096,
    ).encode("ascii")


def _write_tree(root: Path, files: Mapping[str, bytes]) -> None:
    for relative, raw in sorted(files.items()):
        target = root.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        target.write_bytes(raw)
        os.chmod(target, 0o644)


def _write_active_patch(bundle: Path, raw: bytes) -> None:
    target = bundle / _ACTIVE_PATCH_FILE
    temporary: Path | None = None
    try:
        if bundle.is_symlink() or not bundle.is_dir() or target.is_symlink():
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_ACTIVE_PATCH_INVALID")
        descriptor, temporary_name = tempfile.mkstemp(prefix=".observed-job.", dir=bundle)
        temporary = Path(temporary_name)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        if target.is_symlink() or target.read_bytes() != raw:
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_ACTIVE_PATCH_READBACK_FAILED")
    except DbtOnboardingError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_ACTIVE_PATCH_WRITE_FAILED") from None


def _tree_bytes(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise DbtOnboardingError("DBTOBSB_ONBOARDING_OUTPUT_INVALID")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def build_onboarding_plan(inputs: OnboardingInputs) -> DbtOnboardingPlan:
    """Create or exactly verify one byte-stable source-controlled onboarding directory."""

    if not isinstance(inputs, OnboardingInputs) or not isinstance(inputs.target, DbtTargetBinding):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_INPUTS_INVALID")
    source = _real_directory(inputs.source_project, code="DBTOBSB_ONBOARDING_SOURCE_INVALID")
    bundle = _real_directory(inputs.bundle_root, code="DBTOBSB_ONBOARDING_BUNDLE_ROOT_INVALID")
    source_files = _read_source_files(source)
    profile_name = _project_profile(source_files)
    selector = _selector(source_files)
    include_deps, dependency_files, lock_sha256 = _dependency_policy(source, source_files)
    source_files[_GENERATED_PROFILE] = _profile_bytes(profile_name, inputs.target)
    source_sha256, source_contract_sha256 = _source_contract(source_files)
    project_directory = f"./{_OUTPUT_ROOT}/{source_contract_sha256}/project"
    policy = _runtime_policy(
        source_sha256=source_sha256,
        source_contract_sha256=source_contract_sha256,
        project_directory=project_directory,
        profile_name=profile_name,
        selector=selector,
        include_deps=include_deps,
        dependency_definition_files=dependency_files,
        dependency_lock_sha256=lock_sha256,
        target=inputs.target,
    )
    policy_raw = policy.canonical_bytes
    policy_digest = policy.expected_runtime_policy_sha256
    patch_raw = _job_patch(policy)
    relative_root = PurePosixPath(_OUTPUT_ROOT, source_contract_sha256)
    receipt = DbtOnboardingPlan(
        policy_contract_version=str(load_support_manifest().onboarding["policy_contract_version"]),
        support_contract_sha256=load_support_manifest().canonical_sha256,
        source_contract_sha256=source_contract_sha256,
        expected_runtime_policy_sha256=policy_digest,
        project_relative_path=f"{relative_root.as_posix()}/project",
        profiles_relative_path=f"{relative_root.as_posix()}/project/profiles.yml",
        policy_relative_path=f"{relative_root.as_posix()}/{_POLICY_FILE}",
        job_patch_relative_path=f"{relative_root.as_posix()}/{_PATCH_FILE}",
        receipt_relative_path=f"{relative_root.as_posix()}/{_RECEIPT_FILE}",
        policy_sha256=_sha256(policy_raw),
        job_patch_sha256=_sha256(patch_raw),
        file_count=len(source_files),
        include_deps=include_deps,
    )
    receipt_raw = (
        _canonical_json({name: getattr(receipt, name) for name in receipt.__dataclass_fields__})
        + b"\n"
    )
    expected: dict[str, bytes] = {
        **{f"project/{name}": raw for name, raw in source_files.items()},
        _POLICY_FILE: policy_raw,
        _PATCH_FILE: patch_raw,
        _RECEIPT_FILE: receipt_raw,
    }
    destination = bundle.joinpath(*relative_root.parts)
    try:
        if destination.exists():
            if destination.is_symlink() or _tree_bytes(destination) != expected:
                raise DbtOnboardingError("DBTOBSB_ONBOARDING_OUTPUT_CONFLICT")
        else:
            parent = destination.parent
            parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            staged = Path(tempfile.mkdtemp(prefix=f".{source_contract_sha256}.", dir=parent))
            try:
                _write_tree(staged, expected)
                if _tree_bytes(staged) != expected:
                    raise DbtOnboardingError("DBTOBSB_ONBOARDING_OUTPUT_READBACK_FAILED")
                os.replace(staged, destination)
            finally:
                shutil.rmtree(staged, ignore_errors=True)
    except DbtOnboardingError:
        raise
    except OSError:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_OUTPUT_WRITE_FAILED") from None
    if _tree_bytes(destination) != expected:
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_OUTPUT_READBACK_FAILED")
    _write_active_patch(bundle, patch_raw)
    return receipt


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_ARGUMENTS_INVALID")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description="Generate a deterministic dbtobsb onboarding review directory.")
    parser.add_argument("--source-project", required=True, type=Path)
    parser.add_argument("--bundle-root", required=True, type=Path)
    return parser


def _read_target(stream: Any) -> DbtTargetBinding:
    try:
        raw = stream.buffer.read(4097)
        if len(raw) > 4096:
            raise ValueError
        document = json.loads(raw)
    except (AttributeError, OSError, UnicodeError, ValueError, json.JSONDecodeError):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_TARGET_INPUT_INVALID") from None
    keys = {
        "artifact_catalog",
        "artifact_schema",
        "canonical_workspace_hostname",
        "warehouse_id",
        "warehouse_http_path",
        "catalog",
        "schema",
    }
    if (
        not isinstance(document, dict)
        or set(document) != keys
        or any(not isinstance(document[key], str) for key in keys)
    ):
        raise DbtOnboardingError("DBTOBSB_ONBOARDING_TARGET_INPUT_INVALID")
    return DbtTargetBinding(
        **document,
        _construction_token=_TARGET_TOKEN,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Generate local review files; the target arrives on stdin and is never echoed."""

    try:
        arguments = _parser().parse_args(argv)
        result = build_onboarding_plan(
            OnboardingInputs(
                source_project=arguments.source_project,
                bundle_root=arguments.bundle_root,
                target=_read_target(sys.stdin),
            )
        )
    except DbtOnboardingError as error:
        print(error.code, file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "expected_runtime_policy_sha256": result.expected_runtime_policy_sha256,
                "job_patch_relative_path": result.job_patch_relative_path,
                "outcome": "DBT_ONBOARDING_REVIEW_READY",
                "policy_relative_path": result.policy_relative_path,
                "source_contract_sha256": result.source_contract_sha256,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
