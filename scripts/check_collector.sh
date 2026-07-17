#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

collector_python="${COLLECTOR_PYTHON_VERSION:-3.12}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-collector-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

uv sync --project collector --locked --python "$collector_python" \
  --reinstall-package dbtobsb-contracts \
  --reinstall-package dbtobsb-capture \
  --reinstall-package dbtobsb-collector
uv run --project collector pytest collector/tests
uv run --project collector ruff check collector
uv run --project collector ruff format --check collector
uv run --project collector ty check collector
uv build --project contracts --wheel --out-dir "$temporary_root/dist"
uv build --project capture --wheel --out-dir "$temporary_root/dist"
uv build --project collector --wheel --out-dir "$temporary_root/dist"
shopt -s nullglob
contracts_wheels=("$temporary_root"/dist/dbtobsb_contracts-*.whl)
capture_wheels=("$temporary_root"/dist/dbtobsb_capture-*.whl)
collector_wheels=("$temporary_root"/dist/dbtobsb_collector-*.whl)
if [[ "${#contracts_wheels[@]}" -ne 1 \
  || "${#capture_wheels[@]}" -ne 1 \
  || "${#collector_wheels[@]}" -ne 1 ]]; then
  printf '%s\n' "DBTOBSB_COLLECTOR_WHEEL_COUNT_ERROR" >&2
  exit 1
fi
if unzip -Z1 "${collector_wheels[0]}" \
  | grep -Eq '^dbtobsb_collector/(trust|trust_contract)\.py$'; then
  printf '%s\n' "DBTOBSB_RUNTIME_TRUST_READER_PRESENT_IN_COLLECTOR_WHEEL" >&2
  exit 1
fi

uv venv --python "$collector_python" "$temporary_root/venv"
UV_LINK_MODE=copy uv pip install --python "$temporary_root/venv/bin/python" \
  "${contracts_wheels[0]}" "${capture_wheels[0]}" "${collector_wheels[0]}"
"$temporary_root/venv/bin/dbtobsb-collector" \
  | grep -F "fixed Databricks runtime wheel entrypoint"
if [[ ! -x "$temporary_root/venv/bin/bootstrap" \
  || ! -x "$temporary_root/venv/bin/uninstall-delete" ]]; then
  printf '%s\n' "DBTOBSB_LIFECYCLE_ENTRYPOINT_MISSING" >&2
  exit 1
fi

printf '%s\n' "DBTOBSB_COLLECTOR_CHECK_PASSED"
