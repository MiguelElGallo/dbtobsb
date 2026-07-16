"""Product-owned dbt Core runner with customer-local artifact staging."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from databricks.sdk import WorkspaceClient
from dbtobsb_capture.inspector import MAX_PRIMARY_ARTIFACT_BYTES
from dbtobsb_contracts import load_support_manifest, parse_dbt_runtime_policy

from dbtobsb_collector.contracts import AttemptContext


class DbtRunnerError(RuntimeError):
    """Static runner failure that never contains credentials, paths, or dbt payloads."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARGUMENTS_INVALID")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description="Run one sealed dbt Core attempt and stage its evidence.")
    for name in (
        "workspace_id",
        "observed_job_id",
        "observed_job_run_id",
        "dbt_task_run_id",
        "repair_count",
        "execution_count",
    ):
        parser.add_argument(f"--{name}", required=True, type=int)
    parser.add_argument("--project_directory", required=True)
    parser.add_argument("--policy_path", required=True)
    return parser


def _access_token(client: WorkspaceClient) -> str:
    try:
        headers = client.config.authenticate()
    except Exception:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_AUTH_UNAVAILABLE") from None
    authorization = next(
        (value for name, value in headers.items() if name.casefold() == "authorization"),
        None,
    )
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_AUTH_UNAVAILABLE")
    token = authorization.removeprefix("Bearer ")
    if not token or any(character.isspace() for character in token):
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_AUTH_UNAVAILABLE")
    return token


def _bounded_file(path: Path, *, limit: int) -> bytes | None:
    try:
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_TYPE_UNSAFE")
        value = path.read_bytes()
    except DbtRunnerError:
        raise
    except OSError:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_READ_FAILED") from None
    if len(value) > limit:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_SIZE_LIMIT_EXCEEDED")
    return value


def _upload_verified(client: WorkspaceClient, *, path: str, value: bytes) -> None:
    try:
        parent = path.rsplit("/", maxsplit=1)[0]
        client.files.create_directory(parent)
        client.files.upload(path, io.BytesIO(value), overwrite=False, use_parallel=False)
        response = client.files.download(path)
        stream = response.contents
        if stream is None:
            raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_UPLOAD_FAILED")
        with stream:
            observed = stream.read(len(value) + 1)
    except DbtRunnerError:
        raise
    except Exception:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_UPLOAD_FAILED") from None
    if (
        len(observed) != len(value)
        or hashlib.sha256(observed).digest() != hashlib.sha256(value).digest()
    ):
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_ARTIFACT_READBACK_MISMATCH")


def _stage_attempt(
    client: WorkspaceClient,
    *,
    local_root: Path,
    remote_root: str,
    include_deps: bool,
) -> int:
    governed = load_support_manifest().governed_output
    log_limit = int(governed["file_log_max_bytes"])
    log_files = int(governed["file_log_max_files"])
    candidates: list[tuple[Path, str, int]] = [
        (
            local_root / "001-build" / "artifacts" / "manifest.json",
            "001-build/artifacts/manifest.json",
            MAX_PRIMARY_ARTIFACT_BYTES,
        ),
        (
            local_root / "001-build" / "artifacts" / "run_results.json",
            "001-build/artifacts/run_results.json",
            MAX_PRIMARY_ARTIFACT_BYTES,
        ),
    ]
    ordinals = ["000-deps"] if include_deps else []
    ordinals.append("001-build")
    for ordinal in ordinals:
        base = local_root / ordinal / "logs" / "dbt.log"
        for rotation in range(log_files):
            local = base if rotation == 0 else base.with_name(f"dbt.log.{rotation}")
            suffix = "" if rotation == 0 else f".{rotation}"
            candidates.append((local, f"{ordinal}/logs/dbt.log{suffix}", log_limit))

    uploaded = 0
    for local, relative, limit in candidates:
        value = _bounded_file(local, limit=limit)
        if value is None:
            continue
        _upload_verified(client, path=f"{remote_root}/{relative}", value=value)
        uploaded += 1
    return uploaded


def _run(arguments: argparse.Namespace, *, client: WorkspaceClient | None = None) -> int:
    context = AttemptContext(
        workspace_id=arguments.workspace_id,
        observed_job_id=arguments.observed_job_id,
        observed_job_run_id=arguments.observed_job_run_id,
        dbt_task_run_id=arguments.dbt_task_run_id,
        observed_task_key="dbt_build",
        repair_count=arguments.repair_count,
        execution_count=arguments.execution_count,
    )
    project = Path(arguments.project_directory)
    policy_path = Path(arguments.policy_path)
    if (
        not project.is_absolute()
        or not policy_path.is_absolute()
        or policy_path.name != "dbt-policy-v1.json"
        or policy_path.parent != project.parent
    ):
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_BINDING_INVALID")
    try:
        policy = parse_dbt_runtime_policy(policy_path.read_bytes())
    except Exception:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_POLICY_INVALID") from None
    suffix = f"/files/{policy.project_directory.removeprefix('./')}"
    if (
        not str(project).startswith("/Workspace/")
        or not str(project).endswith(suffix)
        or not project.is_dir()
    ):
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_BINDING_INVALID")

    workspace = client or WorkspaceClient()
    try:
        workspace_id = workspace.get_workspace_id()
    except Exception:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_WORKSPACE_INVALID") from None
    if workspace_id != context.workspace_id:
        raise DbtRunnerError("DBTOBSB_DBT_RUNNER_WORKSPACE_INVALID")

    attempt_key = context.as_dbt_attempt_identity().key
    unresolved_key = str(load_support_manifest().dbt["attempt_key_template"])
    remote_root = f"{policy.target.artifact_attempt_root}/{attempt_key}"
    dbt_exit_code = 0
    with tempfile.TemporaryDirectory(prefix=f"dbtobsb-{context.dbt_task_run_id}-") as temporary:
        local_root = Path(temporary) / "attempt"
        environment = dict(os.environ)
        environment["DBT_ACCESS_TOKEN"] = _access_token(workspace)
        environment["DBT_PROFILES_DIR"] = str(project)
        for command in policy.commands:
            resolved = command.replace(unresolved_key, attempt_key).replace(
                remote_root,
                str(local_root),
            )
            try:
                result = subprocess.run(
                    shlex.split(resolved),
                    cwd=project,
                    env=environment,
                    check=False,
                    timeout=840,
                )
            except (OSError, subprocess.TimeoutExpired):
                raise DbtRunnerError("DBTOBSB_DBT_RUNNER_EXECUTION_FAILED") from None
            dbt_exit_code = result.returncode
            if dbt_exit_code != 0:
                break
        uploaded = _stage_attempt(
            workspace,
            local_root=local_root,
            remote_root=remote_root,
            include_deps=policy.installed_policy.include_deps,
        )
    print(
        json.dumps(
            {
                "dbt_exit_code": dbt_exit_code,
                "event": "dbtobsb_dbt_artifacts_staged",
                "file_count": uploaded,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return dbt_exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the sealed observed-job runner."""
    try:
        return _run(_parser().parse_args(argv))
    except (DbtRunnerError, TypeError, ValueError) as error:
        code = error.code if isinstance(error, DbtRunnerError) else "DBTOBSB_DBT_RUNNER_INVALID"
        print(code, file=sys.stderr)
        return 2


def entrypoint() -> None:
    """Databricks wheel entry point that cannot have a return code ignored."""
    status = main()
    if status != 0:
        raise RuntimeError("DBTOBSB_DBT_RUNNER_TASK_FAILED")


if __name__ == "__main__":
    raise SystemExit(main())
