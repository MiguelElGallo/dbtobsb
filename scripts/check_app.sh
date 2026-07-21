#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

app_python="${APP_PYTHON_VERSION:-3.11}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-app-check.XXXXXX")"
created_observed_patch=false
created_app_patch=false
created_onboarding_directory=false
cleanup() {
  rm -rf "$temporary_root"
  if [[ "$created_observed_patch" == true ]]; then
    rm -f .dbtobsb-observed.generated.yml
  fi
  if [[ "$created_app_patch" == true ]]; then
    rm -f .dbtobsb-app-bindings.generated.yml
  fi
  if [[ "$created_onboarding_directory" == true ]]; then
    rm -rf dbtobsb_onboarding
  fi
}
trap cleanup EXIT

if [[ ! -f .dbtobsb-observed.generated.yml ]]; then
  if [[ ! -e dbtobsb_onboarding ]]; then
    created_onboarding_directory=true
  fi
  printf '%s' '{"canonical_workspace_hostname":"adb-1234567890123456.10.azuredatabricks.net","warehouse_id":"0123456789abcdef","warehouse_http_path":"/sql/1.0/warehouses/0123456789abcdef","catalog":"analytics","schema":"weather_prod","artifact_catalog":"observability","artifact_schema":"dbtobsb"}' \
    | uv run --project installer dbtobsb-onboard-dbt-project \
        --source-project demo_dbt \
        --bundle-root . >/dev/null
  created_observed_patch=true
fi
if [[ ! -f .dbtobsb-app-bindings.generated.yml ]]; then
  uv run --project installer dbtobsb-render-app-stage >/dev/null
  created_app_patch=true
fi
uv sync --project app --extra dev --locked --python "$app_python"
uv run --project app --extra dev pytest app/tests
uv run --project app --extra dev ruff check app
uv run --project app --extra dev ruff format --check app
uv run --project app --extra dev ty check app
uv build --project app --wheel --out-dir "$temporary_root/dist"

printf '%s\n' "DBTOBSB_APP_CHECK_PASSED"
