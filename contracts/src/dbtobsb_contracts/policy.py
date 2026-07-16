"""Canonical installed dbt policy shared by onboarding and every runtime reader."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, NoReturn, cast

from dbtobsb_contracts.commands import InstalledDbtPolicy, generate_dbt_commands
from dbtobsb_contracts.support import load_support_manifest

_POLICY_DOMAIN = "dbtobsb.dbt-runtime-policy.v1"
_SOURCE_CONTRACT_DOMAIN = "dbtobsb.dbt-source-contract.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_AZURE_HOST = re.compile(r"^adb-[0-9]{1,20}\.[0-9]{1,20}\.azuredatabricks\.net$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_WAREHOUSE_HTTP_PATH = re.compile(r"^/sql/1\.0/warehouses/(?P<warehouse>[0-9a-f]{16})$")
_REGULAR_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_PROJECT_DIRECTORY = re.compile(
    r"^\./dbtobsb_onboarding/(?P<source_contract>[0-9a-f]{64})/project$"
)
_REQUIRED_SOURCE_FILES = frozenset({"dbt_project.yml", "profiles.yml", "selectors.yml"})
_POLICY_KEYS = frozenset(
    {
        "commands",
        "dependency_definition_files",
        "dependency_lock_sha256",
        "domain",
        "environment_key",
        "expected_runtime_policy_sha256",
        "include_deps",
        "policy_contract_version",
        "profile_name",
        "profiles_directory",
        "project_directory",
        "selector",
        "source",
        "source_contract_sha256",
        "source_sha256",
        "support_contract_sha256",
        "target",
        "task_key",
    }
)
_TARGET_KEYS = frozenset({"catalog", "host", "http_path", "name", "schema", "warehouse_id"})


class DbtRuntimePolicyError(ValueError):
    """Sanitized fail-closed policy error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise DbtRuntimePolicyError(code)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("DBTOBSB_DBT_POLICY_DUPLICATE_KEY")
        result[key] = value
    return result


def _load(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_strict_object)
    except DbtRuntimePolicyError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("DBTOBSB_DBT_POLICY_JSON_INVALID")
    if not isinstance(value, dict) or set(value) != _POLICY_KEYS:
        _fail("DBTOBSB_DBT_POLICY_SHAPE_INVALID")
    if raw != _canonical_json(value) + b"\n":
        _fail("DBTOBSB_DBT_POLICY_NOT_CANONICAL")
    return value


def _string(value: object, *, code: str) -> str:
    if not isinstance(value, str):
        _fail(code)
    return value


def _digest(value: object, *, code: str) -> str:
    result = _string(value, code=code)
    if _SHA256.fullmatch(result) is None:
        _fail(code)
    return result


def _source_path(value: object) -> str:
    result = _string(value, code="DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
    path = PurePosixPath(result)
    if (
        not result
        or result.startswith("/")
        or "\\" in result
        or path.as_posix() != result
        or any(part in {"", ".", ".."} or part.startswith(".") for part in path.parts)
        or path.parts[0] in {"logs", "target", "dbtobsb_onboarding"}
    ):
        _fail("DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
    return result


@dataclass(frozen=True, slots=True, repr=False)
class DbtRuntimeTarget:
    """Nonsecret custom-profile target frozen into an installed policy."""

    host: str
    warehouse_id: str
    http_path: str
    catalog: str
    schema: str

    def __post_init__(self) -> None:
        match = _WAREHOUSE_HTTP_PATH.fullmatch(self.http_path)
        if (
            _AZURE_HOST.fullmatch(self.host) is None
            or _WAREHOUSE_ID.fullmatch(self.warehouse_id) is None
            or match is None
            or match.group("warehouse") != self.warehouse_id
            or _REGULAR_IDENTIFIER.fullmatch(self.catalog) is None
            or _REGULAR_IDENTIFIER.fullmatch(self.schema) is None
        ):
            _fail("DBTOBSB_DBT_POLICY_TARGET_INVALID")

    def __repr__(self) -> str:
        return "DbtRuntimeTarget(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class DbtRuntimePolicyInputs:
    """Complete typed input used to render one immutable runtime policy."""

    source_sha256: Mapping[str, str]
    source_contract_sha256: str
    project_directory: str
    profile_name: str
    selector: str
    include_deps: bool
    dependency_definition_files: tuple[str, ...]
    dependency_lock_sha256: str | None
    target: DbtRuntimeTarget

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_sha256", MappingProxyType(dict(self.source_sha256)))
        object.__setattr__(
            self,
            "dependency_definition_files",
            tuple(self.dependency_definition_files),
        )

    def __repr__(self) -> str:
        return "DbtRuntimePolicyInputs(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class DbtRuntimePolicySnapshot:
    """Strictly parsed installed policy and its canonical bytes."""

    installed_policy: InstalledDbtPolicy
    commands: tuple[str, ...]
    dependency_definition_files: tuple[str, ...]
    dependency_lock_sha256: str | None
    environment_key: str
    expected_runtime_policy_sha256: str
    policy_contract_version: str
    profile_name: str
    profiles_directory: str
    project_directory: str
    source: str
    source_contract_sha256: str
    source_sha256: Mapping[str, str] = field(repr=False)
    target: DbtRuntimeTarget = field(repr=False)
    task_key: str
    canonical_bytes: bytes = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "commands", tuple(self.commands))
        object.__setattr__(
            self,
            "dependency_definition_files",
            tuple(self.dependency_definition_files),
        )
        object.__setattr__(self, "source_sha256", MappingProxyType(dict(self.source_sha256)))

    def __repr__(self) -> str:
        return (
            "DbtRuntimePolicySnapshot("
            f"policy_contract_version={self.policy_contract_version!r}, "
            f"expected_runtime_policy_sha256={self.expected_runtime_policy_sha256!r})"
        )


def _validate_source_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        _fail("DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
    result: dict[str, str] = {}
    for raw_path, raw_digest in value.items():
        path = _source_path(raw_path)
        if path in result:
            _fail("DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
        result[path] = _digest(raw_digest, code="DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
    if not _REQUIRED_SOURCE_FILES.issubset(result):
        _fail("DBTOBSB_DBT_POLICY_SOURCE_MAP_INVALID")
    return dict(sorted(result.items()))


def _validate_dependencies(
    *,
    include_deps: object,
    definition_files: object,
    lock_sha256: object,
    source_sha256: Mapping[str, str],
) -> tuple[bool, tuple[str, ...], str | None]:
    if not isinstance(include_deps, bool):
        _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
    if not isinstance(definition_files, list) or any(
        not isinstance(item, str) for item in definition_files
    ):
        _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
    definitions = tuple(cast(str, item) for item in definition_files)
    if include_deps:
        if definitions not in {("dependencies.yml",), ("packages.yml",)}:
            _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
        lock = _digest(lock_sha256, code="DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
        if definitions[0] not in source_sha256 or source_sha256.get("package-lock.yml") != lock:
            _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
        return True, definitions, lock
    if definitions or lock_sha256 is not None:
        _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
    if {"dependencies.yml", "packages.yml", "package-lock.yml"}.intersection(source_sha256):
        _fail("DBTOBSB_DBT_POLICY_DEPENDENCIES_INVALID")
    return False, (), None


def _validate_target(value: object) -> DbtRuntimeTarget:
    if not isinstance(value, dict) or set(value) != _TARGET_KEYS or value.get("name") != "dbtobsb":
        _fail("DBTOBSB_DBT_POLICY_TARGET_INVALID")
    target = cast(dict[str, object], value)
    try:
        return DbtRuntimeTarget(
            host=_string(target["host"], code="DBTOBSB_DBT_POLICY_TARGET_INVALID"),
            warehouse_id=_string(target["warehouse_id"], code="DBTOBSB_DBT_POLICY_TARGET_INVALID"),
            http_path=_string(target["http_path"], code="DBTOBSB_DBT_POLICY_TARGET_INVALID"),
            catalog=_string(target["catalog"], code="DBTOBSB_DBT_POLICY_TARGET_INVALID"),
            schema=_string(target["schema"], code="DBTOBSB_DBT_POLICY_TARGET_INVALID"),
        )
    except (DbtRuntimePolicyError, TypeError):
        _fail("DBTOBSB_DBT_POLICY_TARGET_INVALID")


def parse_dbt_runtime_policy(raw: bytes) -> DbtRuntimePolicySnapshot:
    """Parse canonical policy bytes and rederive every sealed command and digest."""

    document = _load(raw)
    manifest = load_support_manifest()
    if document["domain"] != _POLICY_DOMAIN:
        _fail("DBTOBSB_DBT_POLICY_DOMAIN_INVALID")
    if document["policy_contract_version"] != manifest.onboarding["policy_contract_version"]:
        _fail("DBTOBSB_DBT_POLICY_VERSION_INVALID")
    if document["support_contract_sha256"] != manifest.canonical_sha256:
        _fail("DBTOBSB_DBT_POLICY_SUPPORT_CONTRACT_INVALID")
    if (
        document["source"] != manifest.onboarding["source_type"]
        or document["task_key"] != manifest.onboarding["task_key"]
        or document["environment_key"] != manifest.onboarding["environment_key"]
    ):
        _fail("DBTOBSB_DBT_POLICY_JOB_CONTRACT_INVALID")

    source_sha256 = _validate_source_map(document["source_sha256"])
    source_contract_sha256 = _digest(
        document["source_contract_sha256"], code="DBTOBSB_DBT_POLICY_SOURCE_CONTRACT_INVALID"
    )
    computed_source_contract = _sha256(
        _canonical_json({"domain": _SOURCE_CONTRACT_DOMAIN, "source_sha256": source_sha256})
    )
    if computed_source_contract != source_contract_sha256:
        _fail("DBTOBSB_DBT_POLICY_SOURCE_CONTRACT_INVALID")

    project_directory = _string(
        document["project_directory"], code="DBTOBSB_DBT_POLICY_PROJECT_DIRECTORY_INVALID"
    )
    project_match = _PROJECT_DIRECTORY.fullmatch(project_directory)
    if (
        project_match is None
        or project_match.group("source_contract") != source_contract_sha256
        or document["profiles_directory"] != project_directory
    ):
        _fail("DBTOBSB_DBT_POLICY_PROJECT_DIRECTORY_INVALID")

    profile_name = _string(document["profile_name"], code="DBTOBSB_DBT_POLICY_PROFILE_INVALID")
    profile_target = cast(Mapping[str, object], manifest.onboarding["profile_target"])
    profile_pattern = str(profile_target["profile_name_pattern"])
    if re.fullmatch(profile_pattern, profile_name) is None:
        _fail("DBTOBSB_DBT_POLICY_PROFILE_INVALID")

    selector = _string(document["selector"], code="DBTOBSB_DBT_POLICY_SELECTOR_INVALID")
    include_deps, definitions, lock_sha256 = _validate_dependencies(
        include_deps=document["include_deps"],
        definition_files=document["dependency_definition_files"],
        lock_sha256=document["dependency_lock_sha256"],
        source_sha256=source_sha256,
    )
    try:
        installed = InstalledDbtPolicy(
            support_contract_sha256=manifest.canonical_sha256,
            approved_selector=selector,
            include_deps=include_deps,
        )
    except (TypeError, ValueError):
        _fail("DBTOBSB_DBT_POLICY_SELECTOR_INVALID")
    commands = tuple(command.shell_command for command in generate_dbt_commands(policy=installed))
    if document["commands"] != list(commands):
        _fail("DBTOBSB_DBT_POLICY_COMMANDS_INVALID")
    target = _validate_target(document["target"])

    expected_digest = _digest(
        document["expected_runtime_policy_sha256"],
        code="DBTOBSB_DBT_POLICY_DIGEST_INVALID",
    )
    digest_input = dict(document)
    del digest_input["expected_runtime_policy_sha256"]
    if _sha256(_canonical_json(digest_input)) != expected_digest:
        _fail("DBTOBSB_DBT_POLICY_DIGEST_INVALID")

    return DbtRuntimePolicySnapshot(
        installed_policy=installed,
        commands=commands,
        dependency_definition_files=definitions,
        dependency_lock_sha256=lock_sha256,
        environment_key=str(manifest.onboarding["environment_key"]),
        expected_runtime_policy_sha256=expected_digest,
        policy_contract_version=str(manifest.onboarding["policy_contract_version"]),
        profile_name=profile_name,
        profiles_directory=project_directory,
        project_directory=project_directory,
        source=str(manifest.onboarding["source_type"]),
        source_contract_sha256=source_contract_sha256,
        source_sha256=source_sha256,
        target=target,
        task_key=str(manifest.onboarding["task_key"]),
        canonical_bytes=raw,
    )


def render_dbt_runtime_policy(inputs: DbtRuntimePolicyInputs) -> DbtRuntimePolicySnapshot:
    """Render and immediately parse one canonical installed policy."""

    if not isinstance(inputs, DbtRuntimePolicyInputs) or not isinstance(
        inputs.target, DbtRuntimeTarget
    ):
        _fail("DBTOBSB_DBT_POLICY_INPUTS_INVALID")
    manifest = load_support_manifest()
    installed = InstalledDbtPolicy(
        support_contract_sha256=manifest.canonical_sha256,
        approved_selector=inputs.selector,
        include_deps=inputs.include_deps,
    )
    document: dict[str, object] = {
        "commands": [command.shell_command for command in generate_dbt_commands(policy=installed)],
        "dependency_definition_files": list(inputs.dependency_definition_files),
        "dependency_lock_sha256": inputs.dependency_lock_sha256,
        "domain": _POLICY_DOMAIN,
        "environment_key": manifest.onboarding["environment_key"],
        "include_deps": inputs.include_deps,
        "policy_contract_version": manifest.onboarding["policy_contract_version"],
        "profile_name": inputs.profile_name,
        "profiles_directory": inputs.project_directory,
        "project_directory": inputs.project_directory,
        "selector": inputs.selector,
        "source": manifest.onboarding["source_type"],
        "source_contract_sha256": inputs.source_contract_sha256,
        "source_sha256": dict(inputs.source_sha256),
        "support_contract_sha256": manifest.canonical_sha256,
        "target": {
            "catalog": inputs.target.catalog,
            "host": inputs.target.host,
            "http_path": inputs.target.http_path,
            "name": "dbtobsb",
            "schema": inputs.target.schema,
            "warehouse_id": inputs.target.warehouse_id,
        },
        "task_key": manifest.onboarding["task_key"],
    }
    digest = _sha256(_canonical_json(document))
    raw = _canonical_json({**document, "expected_runtime_policy_sha256": digest}) + b"\n"
    return parse_dbt_runtime_policy(raw)
