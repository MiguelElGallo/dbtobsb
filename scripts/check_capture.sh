#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

capture_python="${CAPTURE_PYTHON_VERSION:-3.12}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-capture-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

uv sync --project capture --locked --python "$capture_python"
uv run --project capture pytest capture/tests
uv run --project capture ruff check capture
uv run --project capture ruff format --check capture
uv run --project capture ty check capture

uv build --project capture --wheel --out-dir "$temporary_root/dist"
shopt -s nullglob
wheels=("$temporary_root"/dist/*.whl)
if [[ "${#wheels[@]}" -ne 1 ]]; then
  printf '%s\n' "DBTOBSB_CAPTURE_WHEEL_COUNT_ERROR" >&2
  exit 1
fi

uv venv --python "$capture_python" "$temporary_root/venv"
uv pip install --python "$temporary_root/venv/bin/python" "${wheels[0]}"

"$temporary_root/venv/bin/dbtobsb-capture" inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --json \
  --no-color \
  | "$temporary_root/venv/bin/python" -c \
    'import json, sys; report = json.load(sys.stdin); assert report["pair_state"] == "PAIR_VALID"'

printf '%s\n' "DBTOBSB_CAPTURE_CHECK_PASSED"
