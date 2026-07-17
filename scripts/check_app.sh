#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

app_python="${APP_PYTHON_VERSION:-3.11}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-app-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

uv run --project installer dbtobsb-render-app-stage >/dev/null
uv sync --project app --extra dev --locked --python "$app_python"
uv run --project app --extra dev pytest app/tests
uv run --project app --extra dev ruff check app
uv run --project app --extra dev ruff format --check app
uv run --project app --extra dev ty check app
uv build --project app --wheel --out-dir "$temporary_root/dist"

printf '%s\n' "DBTOBSB_APP_CHECK_PASSED"
