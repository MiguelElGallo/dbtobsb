"""Databricks Jobs artifact-link transport classification tests."""

from types import SimpleNamespace
from typing import cast

import pytest
from databricks.sdk import WorkspaceClient

from dbtobsb_collector import AttemptContext
from dbtobsb_collector.jobs import (
    DatabricksJobsEvidenceReader,
    JobsEvidenceError,
    _allow_internal_artifact_http,
)


def _enum(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _context() -> AttemptContext:
    return AttemptContext(101, 201, 301, 401, "dbt_build", 0, 1)


class _Jobs:
    def __init__(self, pages: list[SimpleNamespace], task: SimpleNamespace) -> None:
        self._pages = pages
        self._task = task
        self.output_calls = 0

    def get_run(self, run_id: int, *, page_token: str | None = None) -> SimpleNamespace:
        assert run_id == 301
        index = 0 if page_token is None else int(page_token)
        return self._pages[index]

    def get_run_output(self, run_id: int) -> SimpleNamespace:
        assert run_id == 401
        self.output_calls += 1
        return SimpleNamespace(
            metadata=SimpleNamespace(run_id=401, job_id=201, job_run_id=301),
            dbt_output=SimpleNamespace(
                artifacts_link="https://signed.invalid/archive",
                artifacts_headers={"x-required": "value"},
            ),
            logs_truncated=False,
        )


def _client(task: SimpleNamespace, *, paginated: bool = False) -> SimpleNamespace:
    if paginated:
        pages = [
            SimpleNamespace(run_id=301, job_id=201, tasks=[], next_page_token="1"),
            SimpleNamespace(run_id=301, job_id=201, tasks=[task], next_page_token=None),
        ]
    else:
        pages = [SimpleNamespace(run_id=301, job_id=201, tasks=[task], next_page_token=None)]
    return SimpleNamespace(
        jobs=_Jobs(pages, task),
        config=SimpleNamespace(host="https://adb-999.8.azuredatabricks.net"),
    )


def _task(*, current_state: str = "TERMINATED", result: str = "SUCCESS") -> SimpleNamespace:
    return SimpleNamespace(
        task_key="dbt_build",
        run_id=401,
        dbt_task=object(),
        status=SimpleNamespace(
            state=_enum(current_state),
            termination_details=SimpleNamespace(code=_enum(result)),
        ),
        state=SimpleNamespace(life_cycle_state=_enum("TERMINATED"), result_state=_enum("FAILED")),
        start_time=1_000,
        end_time=2_000,
        attempt_number=0,
    )


def test_azure_databricks_internal_http_link_is_recognized() -> None:
    original = "http://adb-123.4.azuredatabricks.net/path/archive?opaque=secret"

    assert _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_databricks_com_internal_http_link_is_recognized() -> None:
    original = "http://artifacts.cloud.databricks.com/path/archive?opaque=secret"

    assert _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_https_link_does_not_request_internal_http_capability() -> None:
    original = "https://signed.blob.core.windows.net/path/archive?opaque=secret"

    assert not _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_untrusted_cleartext_links_are_not_recognized() -> None:
    candidates = (
        "http://signed.blob.core.windows.net/path/archive",
        "http://azuredatabricks.net.attacker.invalid/path/archive",
        "http://databricks.com.attacker.invalid/path/archive",
        "http://user@adb-123.4.azuredatabricks.net/path/archive",
        "http://adb-123.4.azuredatabricks.net:80/path/archive",
    )

    assert not any(
        _allow_internal_artifact_http(value, workspace_host="https://adb-999.8.azuredatabricks.net")
        for value in candidates
    )


def test_untrusted_workspace_host_does_not_grant_capability() -> None:
    original = "http://artifacts.cloud.databricks.com/path/archive?opaque=secret"

    assert not _allow_internal_artifact_http(original, workspace_host="https://attacker.invalid")


def test_reader_paginates_and_prefers_current_terminal_status() -> None:
    client = _client(_task(), paginated=True)

    evidence = DatabricksJobsEvidenceReader(cast(WorkspaceClient, client)).read(_context())

    assert evidence.lakeflow_result_state == "SUCCESS"
    assert client.jobs.output_calls == 1


def test_reader_rejects_nonterminal_task_before_requesting_output() -> None:
    client = _client(_task(current_state="RUNNING"))

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_TASK_NOT_TERMINAL"):
        DatabricksJobsEvidenceReader(cast(WorkspaceClient, client)).read(_context())

    assert client.jobs.output_calls == 0
