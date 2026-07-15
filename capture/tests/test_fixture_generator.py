"""Adversarial checks for the reviewed synthetic fixture source boundary."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "artifact_pair"
GENERATOR = Path(__file__).parents[1] / "scripts" / "generate_artifact_pair_fixtures.py"
SOURCE_ONLY_CANARY = "CANARY_UNAPPROVED_SOURCE_ONLY_PERSONAL_DATA"


def _generator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("fixture_generator_under_test", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unapproved_source_cannot_forge_origin_or_copy_source_only_fields(tmp_path: Path) -> None:
    source: Any = json.loads((FIXTURES / "valid_success" / "manifest.json").read_bytes())
    source["metadata"]["dbt_version"] = "9.9.9"
    source["metadata"]["adapter_type"] = "snowflake"
    model = source["nodes"]["model.dbtobsb_capture_fixture.observed_model"]
    model["description"] = SOURCE_ONLY_CANARY
    model["meta"] = {"private": SOURCE_ONLY_CANARY}
    source_path = tmp_path / "unapproved-manifest.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    output_root = tmp_path / "output"

    module = _generator_module()
    with pytest.raises(ValueError, match="reviewed synthetic parse"):
        module.generate(source_manifest_path=source_path, output_root=output_root)

    assert not output_root.exists()
