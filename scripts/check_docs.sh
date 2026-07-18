#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

uvx --from zensical==0.0.51 zensical build --clean --strict
python3 scripts/check_markdown_links.py

printf '%s\n' "DBTOBSB_DOCS_CHECKS_PASSED"
