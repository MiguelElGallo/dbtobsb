"""Fail-closed tests for the product-owned dbt Core runner."""

from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from databricks.sdk import WorkspaceClient

import dbtobsb_collector.runner as runner_module
from dbtobsb_collector.runner import (
    DbtRunnerError,
    _access_token,
    _stage_attempt,
    _upload_verified,
    main,
)


class _Files:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.directories: list[str] = []

    def create_directory(self, path: str) -> None:
        self.directories.append(path)

    def upload(
        self,
        path: str,
        contents: io.BytesIO,
        *,
        overwrite: bool,
        use_parallel: bool,
    ) -> None:
        assert overwrite is False
        assert use_parallel is False
        assert path not in self.values
        self.values[path] = contents.read()

    def download(self, path: str) -> SimpleNamespace:
        return SimpleNamespace(contents=io.BytesIO(self.values[path]))


def test_stage_attempt_uploads_only_the_allowlisted_artifacts(tmp_path: Path) -> None:
    attempt = tmp_path / "attempt"
    artifacts = attempt / "001-build" / "artifacts"
    logs = attempt / "001-build" / "logs"
    artifacts.mkdir(parents=True)
    logs.mkdir(parents=True)
    (artifacts / "manifest.json").write_bytes(b'{"metadata":{}}')
    (artifacts / "run_results.json").write_bytes(b'{"results":[]}')
    (logs / "dbt.log").write_bytes(b'{"info":{"name":"MainReportVersion"}}\n')
    (artifacts / "catalog.json").write_bytes(b"must-not-upload")
    files = _Files()
    client = cast(WorkspaceClient, SimpleNamespace(files=files))

    count = _stage_attempt(
        client,
        local_root=attempt,
        remote_root="/Volumes/observability/dbtobsb/dbtobsb_stage/incoming/w1-j2-r3-t4-p0-e1",
        include_deps=False,
    )

    assert count == 3
    assert {path.rsplit("/", maxsplit=1)[-1] for path in files.values} == {
        "manifest.json",
        "run_results.json",
        "dbt.log",
    }


def test_upload_requires_byte_exact_readback() -> None:
    class _CorruptFiles(_Files):
        def download(self, path: str) -> SimpleNamespace:
            return SimpleNamespace(contents=io.BytesIO(self.values[path] + b"corrupt"))

    files = _CorruptFiles()
    client = cast(WorkspaceClient, SimpleNamespace(files=files))
    with pytest.raises(DbtRunnerError, match="ARTIFACT_READBACK_MISMATCH"):
        _upload_verified(client, path="/Volumes/c/s/v/attempt/file", value=b"exact")


def test_access_token_accepts_only_an_oauth_bearer_header() -> None:
    valid = cast(
        WorkspaceClient,
        SimpleNamespace(
            config=SimpleNamespace(authenticate=lambda: {"Authorization": "Bearer short-lived"})
        ),
    )
    invalid = cast(
        WorkspaceClient,
        SimpleNamespace(config=SimpleNamespace(authenticate=lambda: {"x-token": "secret"})),
    )

    assert _access_token(valid) == "short-lived"
    with pytest.raises(DbtRunnerError, match="AUTH_UNAVAILABLE"):
        _access_token(invalid)


def test_cli_rejects_incomplete_context_without_echoing_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    canary = "customer-secret"

    assert main(["--workspace_id", canary]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == "DBTOBSB_DBT_RUNNER_ARGUMENTS_INVALID"
    assert canary not in output.err


def test_databricks_entrypoint_raises_when_the_runner_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_module, "main", lambda: 2)

    with pytest.raises(RuntimeError, match="DBTOBSB_DBT_RUNNER_TASK_FAILED"):
        runner_module.entrypoint()
