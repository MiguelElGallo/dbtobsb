"""Copy-ready Python API first-success example used by the documentation gate."""

from __future__ import annotations

import json
from pathlib import Path

from dbtobsb_capture import inspect_artifact_pair

fixture = Path(__file__).parents[1] / "tests" / "fixtures" / "artifact_pair" / "valid_success"
report = inspect_artifact_pair(
    manifest=(fixture / "manifest.json").read_bytes(),
    run_results=(fixture / "run_results.json").read_bytes(),
)
print(report.state.value)
print(json.dumps(report.to_dict(), ensure_ascii=True, separators=(",", ":"), sort_keys=True))
