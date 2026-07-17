"""Closed dbt Core command and attempt-path contracts for Lakeflow dbt tasks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from dbtobsb_contracts.support import SupportManifest, load_support_manifest

_WARN_ERROR_OPTIONS = '{"error":["NoNodesForSelectionCriteria","NothingToDo"]}'
_LOCAL_ATTEMPT_ROOT = "$PWD/target/dbtobsb/attempts"
_VOLUME_ATTEMPT_ROOT = re.compile(
    r"^/Volumes/[A-Za-z_][A-Za-z0-9_]{0,127}/"
    r"[A-Za-z_][A-Za-z0-9_]{0,127}/dbtobsb_stage/incoming$"
)


@dataclass(frozen=True, slots=True)
class InstalledDbtPolicy:
    """Digest-bound installation policy; ordinary callers cannot extend it."""

    support_contract_sha256: str
    approved_selector: str
    include_deps: bool

    def __post_init__(self) -> None:
        manifest = load_support_manifest()
        if self.support_contract_sha256 != manifest.canonical_sha256:
            raise ValueError("DBTOBSB_SUPPORT_CONTRACT_DIGEST_MISMATCH")
        _selector_name(self.approved_selector, manifest=manifest)
        if not isinstance(self.include_deps, bool):
            raise TypeError("include_deps must be bool")


@dataclass(frozen=True, slots=True)
class AttemptIdentity:
    """Resolved Databricks-controlled identity for one dbt task attempt."""

    workspace_id: int
    job_id: int
    job_run_id: int
    task_run_id: int
    repair_count: int
    execution_count: int

    def __post_init__(self) -> None:
        positive = (
            self.workspace_id,
            self.job_id,
            self.job_run_id,
            self.task_run_id,
            self.execution_count,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in positive
        ):
            raise ValueError("DBTOBSB_ATTEMPT_IDENTITY_INVALID")
        if (
            not isinstance(self.repair_count, int)
            or isinstance(self.repair_count, bool)
            or self.repair_count < 0
        ):
            raise ValueError("DBTOBSB_ATTEMPT_IDENTITY_INVALID")

    @property
    def key(self) -> str:
        """Return the deterministic resolved key used in archived member paths."""
        return (
            f"w{self.workspace_id}-j{self.job_id}-r{self.job_run_id}-"
            f"t{self.task_run_id}-p{self.repair_count}-e{self.execution_count}"
        )


@dataclass(frozen=True, slots=True)
class DbtOutputExpectation:
    """Exact selector and archive members accepted for one resolved attempt."""

    attempt_key: str
    approved_selector: str
    include_deps: bool
    manifest_member: str
    run_results_member: str
    log_member: str
    deps_log_member: str | None

    @property
    def ordinal_log_members(self) -> tuple[tuple[str, str], ...]:
        """Return the closed command-ordinal log roots in execution order."""
        manifest = load_support_manifest()
        members: list[tuple[str, str]] = []
        if self.include_deps:
            if self.deps_log_member is None:
                raise RuntimeError("DBTOBSB_DEPS_LOG_EXPECTATION_MISSING")
            members.append((str(manifest.dbt["deps_ordinal"]), self.deps_log_member))
        elif self.deps_log_member is not None:
            raise RuntimeError("DBTOBSB_DEPS_LOG_EXPECTATION_UNEXPECTED")
        members.append((str(manifest.dbt["build_ordinal"]), self.log_member))
        return tuple(members)


@dataclass(frozen=True, slots=True)
class GeneratedDbtCommand:
    """One closed command ordinal and its product-owned output templates."""

    ordinal: str
    command: Literal["deps", "build"]
    shell_command: str
    log_path_template: str
    target_path_template: str | None
    expected_archive_member_templates: tuple[str, ...]


def _selector_name(value: str, *, manifest: SupportManifest) -> str:
    pattern = str(manifest.dbt["selector_pattern"])
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError("DBTOBSB_DBT_SELECTOR_INVALID")
    return value


def _attempt_key_template(manifest: SupportManifest) -> str:
    return str(manifest.dbt["attempt_key_template"])


def _shared_flags(*, log_path: str, manifest: SupportManifest) -> list[str]:
    max_bytes = manifest.governed_output["file_log_max_bytes"]
    return [
        "--no-send-anonymous-usage-stats",
        "--no-upload-to-artifacts-ingest-api",
        "--write-json",
        "--log-format-file json",
        "--log-level-file info",
        f"--log-file-max-bytes {max_bytes}",
        f'--log-path "{log_path}"',
        "--no-use-colors",
        "--no-use-colors-file",
        f"--warn-error-options '{_WARN_ERROR_OPTIONS}'",
    ]


def generate_dbt_commands(
    *,
    policy: InstalledDbtPolicy,
    attempt_root: str = _LOCAL_ATTEMPT_ROOT,
) -> tuple[GeneratedDbtCommand, ...]:
    """Generate supported commands without accepting flags, paths, or command fragments."""
    if not isinstance(policy, InstalledDbtPolicy):
        raise TypeError("policy must be InstalledDbtPolicy")
    if attempt_root != _LOCAL_ATTEMPT_ROOT and _VOLUME_ATTEMPT_ROOT.fullmatch(attempt_root) is None:
        raise ValueError("DBTOBSB_DBT_ATTEMPT_ROOT_INVALID")
    manifest = load_support_manifest()
    attempt_root = f"{attempt_root}/{_attempt_key_template(manifest)}"
    commands: list[GeneratedDbtCommand] = []
    if policy.include_deps:
        ordinal = str(manifest.dbt["deps_ordinal"])
        deps_logs = f"{attempt_root}/{ordinal}/logs"
        deps_tokens = ["dbt deps", *_shared_flags(log_path=deps_logs, manifest=manifest)]
        commands.append(
            GeneratedDbtCommand(
                ordinal=ordinal,
                command="deps",
                shell_command=" ".join(deps_tokens),
                log_path_template=deps_logs,
                target_path_template=None,
                expected_archive_member_templates=(
                    "target/dbtobsb/attempts/"
                    f"{_attempt_key_template(manifest)}/{ordinal}/logs/dbt.log",
                ),
            )
        )

    ordinal = str(manifest.dbt["build_ordinal"])
    build_logs = f"{attempt_root}/{ordinal}/logs"
    build_target = f"{attempt_root}/{ordinal}/artifacts"
    build_tokens = [
        "dbt build",
        *_shared_flags(log_path=build_logs, manifest=manifest),
        f'--target-path "{build_target}"',
        "--no-fail-fast",
        "--indirect-selection eager",
        f"--selector {policy.approved_selector}",
    ]
    attempt_key = _attempt_key_template(manifest)
    commands.append(
        GeneratedDbtCommand(
            ordinal=ordinal,
            command="build",
            shell_command=" ".join(build_tokens),
            log_path_template=build_logs,
            target_path_template=build_target,
            expected_archive_member_templates=(
                f"target/dbtobsb/attempts/{attempt_key}/{ordinal}/artifacts/manifest.json",
                f"target/dbtobsb/attempts/{attempt_key}/{ordinal}/artifacts/run_results.json",
                f"target/dbtobsb/attempts/{attempt_key}/{ordinal}/logs/dbt.log",
            ),
        )
    )
    return tuple(commands)


def expected_dbt_output(
    *,
    attempt: AttemptIdentity,
    policy: InstalledDbtPolicy,
) -> DbtOutputExpectation:
    """Resolve the exact nested members accepted for a Databricks task attempt."""
    if not isinstance(policy, InstalledDbtPolicy):
        raise TypeError("policy must be InstalledDbtPolicy")
    manifest = load_support_manifest()
    deps_ordinal = str(manifest.dbt["deps_ordinal"])
    build_ordinal = str(manifest.dbt["build_ordinal"])
    attempt_base = f"target/dbtobsb/attempts/{attempt.key}"
    build_base = f"{attempt_base}/{build_ordinal}"
    return DbtOutputExpectation(
        attempt_key=attempt.key,
        approved_selector=policy.approved_selector,
        include_deps=policy.include_deps,
        manifest_member=f"{build_base}/artifacts/manifest.json",
        run_results_member=f"{build_base}/artifacts/run_results.json",
        log_member=f"{build_base}/logs/dbt.log",
        deps_log_member=(
            f"{attempt_base}/{deps_ordinal}/logs/dbt.log" if policy.include_deps else None
        ),
    )


def demo_installed_policy() -> InstalledDbtPolicy:
    """Return the fixed engineering-preview policy; v1 installation replaces this."""
    manifest = load_support_manifest()
    return InstalledDbtPolicy(
        support_contract_sha256=manifest.canonical_sha256,
        approved_selector="observability_demo",
        include_deps=False,
    )
