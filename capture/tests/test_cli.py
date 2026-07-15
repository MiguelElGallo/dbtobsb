"""Usability and safety tests for the packaged P1.1 CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from dbtobsb_capture.cli import (
    EXIT_INPUT_READ,
    EXIT_INTERNAL,
    EXIT_INVALID,
    EXIT_USAGE,
    EXIT_VALID,
    INPUT_READ_ERROR,
    main,
)
from dbtobsb_capture.inspector import MAX_PRIMARY_ARTIFACT_BYTES

FIXTURES = Path(__file__).parent / "fixtures" / "artifact_pair"
CANARY = "CANARY_DO_NOT_ECHO_PATH_OR_ARGUMENT"


def _arguments(fixture: str, *extra: str) -> list[str]:
    root = FIXTURES / fixture
    return [
        "inspect-artifact-pair",
        "--manifest",
        str(root / "manifest.json"),
        "--run-results",
        str(root / "run_results.json"),
        *extra,
    ]


def test_cli_json_valid_is_noninteractive_deterministic_and_canary_free(capsys: Any) -> None:
    arguments = _arguments("valid_success", "--json", "--no-color")

    first_exit = main(arguments)
    first = capsys.readouterr()
    second_exit = main(arguments)
    second = capsys.readouterr()

    assert first_exit == second_exit == EXIT_VALID
    assert first.out == second.out
    assert first.err == second.err == ""
    assert json.loads(first.out)["pair_state"] == "PAIR_VALID"
    assert "CANARY_" not in first.out
    assert "\x1b[" not in first.out


def test_cli_valid_failure_keeps_pair_and_native_outcome_distinct(capsys: Any) -> None:
    exit_code = main(_arguments("valid_dbt_failure"))
    captured = capsys.readouterr()

    assert exit_code == EXIT_VALID
    assert captured.err == ""
    assert captured.out.startswith("PAIR_VALID\n")
    assert "status_counts: error=1" in captured.out
    assert "before claiming capture state" in captured.out


def test_cli_invalid_returns_stable_exit_and_one_next_action(capsys: Any) -> None:
    exit_code = main(_arguments("invalid_invocation_mismatch", "--json", "--no-color"))
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == EXIT_INVALID
    assert captured.err == ""
    assert report["pair_state"] == "PAIR_INVALID"
    assert report["issues"][0]["code"] == "DBT_INVOCATION_ID_MISMATCH"
    assert report["issues"][0]["next_action"]
    assert "CANARY_" not in captured.out


def test_cli_read_failure_never_echoes_path_or_exception(capsys: Any, tmp_path: Path) -> None:
    missing = tmp_path / CANARY
    exit_code = main(
        [
            "inspect-artifact-pair",
            "--manifest",
            str(missing),
            "--run-results",
            str(missing),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == EXIT_INPUT_READ
    assert captured.out == ""
    assert captured.err == f"{INPUT_READ_ERROR}\n"
    assert CANARY not in captured.err


def test_cli_internal_failure_never_echoes_exception_or_evidence(
    capsys: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_safely(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise RuntimeError(CANARY)

    monkeypatch.setattr("dbtobsb_capture.cli.inspect_artifact_pair", fail_safely)

    exit_code = main(_arguments("valid_success"))
    captured = capsys.readouterr()

    assert exit_code == EXIT_INTERNAL
    assert captured.out == ""
    assert captured.err == "DBTOBSB_INTERNAL_ERROR\n"
    assert CANARY not in captured.err


def test_cli_rejects_symlink_input(capsys: Any, tmp_path: Path) -> None:
    target = FIXTURES / "valid_success" / "manifest.json"
    symlink = tmp_path / "manifest.json"
    symlink.symlink_to(target)

    exit_code = main(
        [
            "inspect-artifact-pair",
            "--manifest",
            str(symlink),
            "--run-results",
            str(FIXTURES / "valid_success" / "run_results.json"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == EXIT_INPUT_READ
    assert captured.err == f"{INPUT_READ_ERROR}\n"


def test_cli_deep_nesting_is_inspected_invalid_not_internal(capsys: Any, tmp_path: Path) -> None:
    nested = (b"[" * 300) + b"0" + (b"]" * 300)
    manifest = tmp_path / "manifest.json"
    run_results = tmp_path / "run_results.json"
    manifest.write_bytes(nested)
    run_results.write_bytes(nested)

    exit_code = main(
        [
            "inspect-artifact-pair",
            "--manifest",
            str(manifest),
            "--run-results",
            str(run_results),
            "--json",
            "--no-color",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == EXIT_INVALID
    assert json.loads(captured.out)["issues"][0]["code"].endswith("JSON_NESTING_LIMIT_EXCEEDED")
    assert captured.err == ""


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO contract is POSIX-only")
def test_installed_cli_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    executable = shutil.which("dbtobsb-capture")
    assert executable is not None
    fifo = tmp_path / "manifest.json"
    os.mkfifo(fifo)

    completed = subprocess.run(
        [
            executable,
            "inspect-artifact-pair",
            "--manifest",
            str(fifo),
            "--run-results",
            str(FIXTURES / "valid_success" / "run_results.json"),
            "--no-color",
        ],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )

    assert completed.returncode == EXIT_INPUT_READ
    assert completed.stdout == ""
    assert completed.stderr == f"{INPUT_READ_ERROR}\n"


def test_installed_cli_rejects_oversized_sparse_regular_file(tmp_path: Path) -> None:
    executable = shutil.which("dbtobsb-capture")
    assert executable is not None
    oversized = tmp_path / "manifest.json"
    oversized.touch()
    with oversized.open("r+b") as handle:
        handle.truncate(MAX_PRIMARY_ARTIFACT_BYTES + 1)

    completed = subprocess.run(
        [
            executable,
            "inspect-artifact-pair",
            "--manifest",
            str(oversized),
            "--run-results",
            str(FIXTURES / "valid_success" / "run_results.json"),
        ],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )

    assert completed.returncode == EXIT_INPUT_READ
    assert completed.stderr == f"{INPUT_READ_ERROR}\n"


@pytest.mark.skipif(not Path("/dev/null").exists(), reason="device contract is POSIX-only")
def test_installed_cli_rejects_device_without_blocking() -> None:
    executable = shutil.which("dbtobsb-capture")
    assert executable is not None

    completed = subprocess.run(
        [
            executable,
            "inspect-artifact-pair",
            "--manifest",
            "/dev/null",
            "--run-results",
            str(FIXTURES / "valid_success" / "run_results.json"),
        ],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )

    assert completed.returncode == EXIT_INPUT_READ
    assert completed.stderr == f"{INPUT_READ_ERROR}\n"


def test_cli_disables_abbreviated_flags_and_sanitizes_usage_error(capsys: Any) -> None:
    with pytest.raises(SystemExit) as error:
        main(["inspect-artifact-pair", "--man", CANARY])
    captured = capsys.readouterr()

    assert error.value.code == EXIT_USAGE
    assert captured.out == ""
    assert "DBTOBSB_CLI_USAGE_ERROR" in captured.err
    assert CANARY not in captured.err


def test_cli_honors_no_color_environment_without_changing_meaning(
    capsys: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")

    exit_code = main(_arguments("valid_success"))
    captured = capsys.readouterr()

    assert exit_code == EXIT_VALID
    assert "\x1b[" not in captured.out
