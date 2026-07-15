"""Non-interactive CLI for the local artifact-pair inspector."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import NoReturn

from dbtobsb_capture.contracts import ArtifactPairReport, PairState
from dbtobsb_capture.inspector import MAX_PRIMARY_ARTIFACT_BYTES, inspect_artifact_pair

EXIT_VALID = 0
EXIT_USAGE = 2
EXIT_INPUT_READ = 3
EXIT_INTERNAL = 4
EXIT_INVALID = 10
INPUT_READ_ERROR = "\n".join(
    (
        "DBTOBSB_INPUT_READ_ERROR",
        "impact: One or both inputs could not be read as closed regular files within 128 MiB.",
        (
            "next_action: Provide existing, closed, non-symlink regular files no larger "
            "than 128 MiB."
        ),
        (
            "help: docs/developers/how-to/diagnose-an-invalid-artifact-pair.md"
            "#recover-an-input-read-error"
        ),
    )
)


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, "DBTOBSB_CLI_USAGE_ERROR\n")


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        prog="dbtobsb-capture",
        description="Inspect one pinned dbt manifest/run-results pair offline.",
        allow_abbrev=False,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser(
        "inspect-artifact-pair",
        help="Validate one manifest.json and run_results.json pair.",
        allow_abbrev=False,
    )
    inspect_parser.add_argument("--manifest", required=True, type=Path)
    inspect_parser.add_argument("--run-results", required=True, type=Path)
    inspect_parser.add_argument("--json", action="store_true", dest="as_json")
    inspect_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Keep output text-only; accepted for automation consistency.",
    )
    return parser


def _read_regular_file(path: Path) -> bytes:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(path, flags)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size > MAX_PRIMARY_ARTIFACT_BYTES:
            raise OSError
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(MAX_PRIMARY_ARTIFACT_BYTES + 1)
        if len(data) > MAX_PRIMARY_ARTIFACT_BYTES:
            raise OSError
        return data
    finally:
        os.close(descriptor)


def _json_output(report: ArtifactPairReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _text_output(report: ArtifactPairReport) -> str:
    lines = [report.state.value]
    if report.state is PairState.VALID:
        summary = report.summary
        if summary is None:
            raise RuntimeError("valid report has no summary")
        counts = ",".join(f"{item.status}={item.count}" for item in summary.status_counts)
        lines.extend(
            [
                "The files satisfy the pinned artifact-pair contract.",
                f"dbt_version: {summary.dbt_version}",
                f"adapter_type: {summary.adapter_type}",
                f"command: {summary.command}",
                f"result_count: {summary.result_count}",
                f"status_counts: {counts}",
                (
                    "next_action: Evaluate outer run and archive evidence before claiming "
                    "capture state."
                ),
            ]
        )
    else:
        issue = report.primary_issue
        if issue is None:
            raise RuntimeError("invalid report has no primary issue")
        lines.extend(
            [
                f"code: {issue.code}",
                f"impact: {issue.impact}",
                f"next_action: {issue.next_action}",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the packaged CLI with stable exits and evidence-safe errors."""
    arguments = _parser().parse_args(argv)
    try:
        manifest = _read_regular_file(arguments.manifest)
        run_results = _read_regular_file(arguments.run_results)
    except (OSError, ValueError):
        print(INPUT_READ_ERROR, file=sys.stderr)
        return EXIT_INPUT_READ

    try:
        report = inspect_artifact_pair(manifest=manifest, run_results=run_results)
        rendered = _json_output(report) if arguments.as_json else _text_output(report)
    except Exception:  # The ordinary output must never expose exception or evidence text.
        print("DBTOBSB_INTERNAL_ERROR", file=sys.stderr)
        return EXIT_INTERNAL

    print(rendered)
    return EXIT_VALID if report.state is PairState.VALID else EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
