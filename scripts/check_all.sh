#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

scripts/check_installer.sh
scripts/check_native.sh
scripts/check_installer_release.sh
scripts/check_contracts.sh
scripts/check_capture.sh
scripts/check_collector.sh
scripts/check_app.sh

printf '%s\n' "DBTOBSB_ALL_CHECKS_PASSED"
