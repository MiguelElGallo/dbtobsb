#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

uv sync --project installer --locked \
  --reinstall-package dbtobsb-collector \
  --reinstall-package dbtobsb-contracts
uv run --project installer ruff format --check installer collector/src/dbtobsb_collector/deployment.py collector/src/dbtobsb_collector/_generated/__init__.py
uv run --project installer ruff check installer collector/src/dbtobsb_collector/deployment.py collector/src/dbtobsb_collector/_generated/__init__.py
uv run --project installer pytest -q installer/tests
node installer/tests/runtime_trust_vectors/verify.mjs
uv run --project installer ty check installer/src installer/tests collector/src/dbtobsb_collector/deployment.py
uv run --project installer dbtobsb-render-app-stage >/dev/null
uv run --project installer dbtobsb-build-runtime-candidate --help >/dev/null

if [[ -e collector/src/dbtobsb_collector/_generated/deployment-binding-v1.json ]]; then
  printf '%s\n' "DBTOBSB_RUNTIME_CANDIDATE_SOURCE_BINDING_FORBIDDEN" >&2
  exit 1
fi
