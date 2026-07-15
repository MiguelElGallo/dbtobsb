"""Checksum-pinned access to the vendored upstream JSON schemas."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator

MANIFEST_SCHEMA_NAME = "manifest-v12.json"
RUN_RESULTS_SCHEMA_NAME = "run-results-v6.json"

MANIFEST_SCHEMA_SHA256 = "b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3"
RUN_RESULTS_SCHEMA_SHA256 = "1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf"


@lru_cache(maxsize=2)
def validator_for(schema_name: str) -> Validator:
    """Load one allowlisted schema and fail safely if its bytes drift."""
    expected_hashes = {
        MANIFEST_SCHEMA_NAME: MANIFEST_SCHEMA_SHA256,
        RUN_RESULTS_SCHEMA_NAME: RUN_RESULTS_SCHEMA_SHA256,
    }
    expected_hash = expected_hashes.get(schema_name)
    if expected_hash is None:
        raise RuntimeError("unsupported internal schema name")

    schema_bytes = files("dbtobsb_capture").joinpath("schemas", schema_name).read_bytes()
    if hashlib.sha256(schema_bytes).hexdigest() != expected_hash:
        raise RuntimeError("vendored dbt schema checksum mismatch")

    loaded: Any = json.loads(schema_bytes)
    if not isinstance(loaded, dict):
        raise RuntimeError("vendored dbt schema has an invalid root")
    Draft202012Validator.check_schema(loaded)
    return Draft202012Validator(loaded)
