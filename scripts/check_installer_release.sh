#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/dbtobsb-installer-release-check.XXXXXX")"
trap 'rm -rf "$temporary_root"' EXIT

cd "$repo_root"

uv run --project installer ruff format --check scripts/build_installer_release.py
uv run --project installer ruff check scripts/build_installer_release.py
scripts/build_installer_release.py --out-dir "$temporary_root" >/dev/null

wheel_count="$(find "$temporary_root" -maxdepth 1 -type f -name '*.whl' | wc -l | tr -d ' ')"
if [[ "$wheel_count" != "1" ]]; then
  printf '%s\n' "DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID" >&2
  exit 1
fi

wheel_path="$(find "$temporary_root" -maxdepth 1 -type f -name '*.whl' -print)"
dependency_root="$temporary_root/dependencies"
mkdir -p "$dependency_root"
uv build --wheel --out-dir "$dependency_root" contracts >/dev/null
uv build --wheel --out-dir "$dependency_root" capture >/dev/null
uv build --wheel --out-dir "$dependency_root" collector >/dev/null
probe_root="$temporary_root/probe"
mkdir -p "$probe_root"
unzip -q "$wheel_path" -d "$probe_root"
uv run --project installer --isolated --no-project --find-links "$dependency_root" \
  --with "$wheel_path" \
  dbtobsb --help >/dev/null
helper_path="$probe_root/dbtobsb_installer/_native/darwin-arm64/dbtobsb-native-bridge"
DBTOBSB_PROBE_HELPER="$helper_path" uv run --project installer python - <<'PY'
import json
import os
from pathlib import Path

from dbtobsb_installer.native_bridge import SubprocessNativeRunner, _VerifiedNativeExecutable

executable = _VerifiedNativeExecutable._for_test(Path(os.environ["DBTOBSB_PROBE_HELPER"]))
try:
    result = SubprocessNativeRunner().run(
        executable,
        stdin=b"{}\n",
        environment={"HOME": "/", "PATH": "/usr/bin:/bin"},
        timeout_seconds=5.0,
        max_output_bytes=65_536,
    )
finally:
    executable.close()
payload = json.loads(result.stdout)
if (
    result.return_code != 1
    or result.output_was_truncated
    or payload
    != {
        "code": "DBTOBSB_NATIVE_ENVIRONMENT_INVALID",
        "ok": False,
        "protocol": "dbtobsb.native-bridge.v1",
    }
):
    raise SystemExit("DBTOBSB_INSTALLER_NATIVE_POSITIVE_LAUNCH_PROBE_FAILED")
PY

printf '%s\n' "DBTOBSB_INSTALLER_RELEASE_CHECK_PASSED"
