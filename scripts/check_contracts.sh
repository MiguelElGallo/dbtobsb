#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

contracts_python="${CONTRACTS_PYTHON_VERSION:-3.12}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-contracts-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

uv sync --project contracts --locked --python "$contracts_python"
uv run --project contracts pytest contracts/tests
uv run --project contracts python contracts/scripts/check_bundle_commands.py
uv run --project contracts ruff check contracts
uv run --project contracts ruff format --check contracts
uv run --project contracts ty check contracts

uv build --project contracts --wheel --out-dir "$temporary_root/dist"
shopt -s nullglob
wheels=("$temporary_root"/dist/*.whl)
if [[ "${#wheels[@]}" -ne 1 ]]; then
  printf '%s\n' "DBTOBSB_CONTRACTS_WHEEL_COUNT_ERROR" >&2
  exit 1
fi

uv venv --python "$contracts_python" "$temporary_root/venv"
UV_LINK_MODE=copy uv pip install --python "$temporary_root/venv/bin/python" "${wheels[0]}"
"$temporary_root/venv/bin/python" -c \
  'from dbtobsb_contracts import load_support_manifest; assert load_support_manifest().release_state == "CANDIDATE"'

printf '%s\n' "DBTOBSB_CONTRACTS_CHECK_PASSED"
