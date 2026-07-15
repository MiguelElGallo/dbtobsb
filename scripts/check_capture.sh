#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

capture_python="${CAPTURE_PYTHON_VERSION:-3.12}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-capture-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

uv sync --project capture --locked --python "$capture_python"
uv run --project capture python capture/scripts/generate_report_schema.py --check
uv run --project capture pytest capture/tests
uv run --project capture python scripts/check_markdown_links.py --revision HEAD
uv run --project capture ruff check capture scripts/check_markdown_links.py
uv run --project capture ruff format --check capture scripts/check_markdown_links.py
uv run --project capture ty check capture scripts/check_markdown_links.py

uv run --project capture python capture/scripts/generate_artifact_pair_fixtures.py \
  --source-manifest capture/tests/fixture_source/approved-manifest.json \
  --output-root "$temporary_root/generated-fixtures"
diff -qr capture/tests/fixtures/artifact_pair "$temporary_root/generated-fixtures"

UV_PROJECT_ENVIRONMENT="$temporary_root/runtime" \
  uv sync --project capture --locked --no-dev --python "$capture_python"
runtime_output="$(
  UV_PROJECT_ENVIRONMENT="$temporary_root/runtime" \
    uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
      --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
      --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
      --no-color
)"
if [[ "$runtime_output" != PAIR_VALID$'\n'* ]]; then
  printf '%s\n' "DBTOBSB_CAPTURE_RUNTIME_ONLY_QUICKSTART_ERROR" >&2
  exit 1
fi
api_example_output="$(
  UV_PROJECT_ENVIRONMENT="$temporary_root/runtime" \
    uv run --project capture --no-sync python capture/examples/inspect_valid_fixture.py
)"
api_example_state="${api_example_output%%$'\n'*}"
api_example_json="${api_example_output#*$'\n'}"
if [[ "$api_example_state" != "PAIR_VALID" ]]; then
  printf '%s\n' "DBTOBSB_CAPTURE_API_EXAMPLE_ERROR" >&2
  exit 1
fi
printf '%s' "$api_example_json" \
  | "$temporary_root/runtime/bin/python" -c \
    'import json, sys; report = json.load(sys.stdin); assert report["pair_state"] == "PAIR_VALID"'

uv build --project capture --wheel --out-dir "$temporary_root/dist"
shopt -s nullglob
wheels=("$temporary_root"/dist/*.whl)
if [[ "${#wheels[@]}" -ne 1 ]]; then
  printf '%s\n' "DBTOBSB_CAPTURE_WHEEL_COUNT_ERROR" >&2
  exit 1
fi

uv venv --python "$capture_python" "$temporary_root/venv"
UV_LINK_MODE=copy uv pip install --python "$temporary_root/venv/bin/python" "${wheels[0]}"

"$temporary_root/venv/bin/dbtobsb-capture" inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --json \
  --no-color \
  | "$temporary_root/venv/bin/python" -c \
    'import json, sys; report = json.load(sys.stdin); assert report["pair_state"] == "PAIR_VALID"'

printf '%s\n' "DBTOBSB_CAPTURE_CHECK_PASSED"
