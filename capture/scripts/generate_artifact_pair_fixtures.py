"""Create deterministic, canary-bearing P1.1 fixtures from a pinned parsed manifest.

This script intentionally creates synthetic run results. The outputs exercise the
artifact-pair contract; they are not represented as live Databricks run evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from dbtobsb_capture.schemas import MANIFEST_SCHEMA_NAME, validator_for

FIXED_INVOCATION_ID = "11111111-1111-4111-8111-111111111111"
MISMATCHED_INVOCATION_ID = "22222222-2222-4222-8222-222222222222"
MODEL_ID = "model.dbtobsb_capture_fixture.observed_model"
SEED_ID = "seed.dbtobsb_capture_fixture.observed_seed"
SNAPSHOT_ID = "snapshot.dbtobsb_capture_fixture.observed_snapshot"
DATA_TEST_ID = "test.dbtobsb_capture_fixture.not_null_observed_model_fixture_id.397be03b66"
UNIT_TEST_ID = "unit_test.dbtobsb_capture_fixture.observed_model.observed_model_returns_one"
SAVED_QUERY_ID = "saved_query.dbtobsb_capture_fixture.fixture_saved_query"
EXPOSURE_ID = "exposure.dbtobsb_capture_fixture.fixture_dashboard"
FUNCTION_ID = "function.dbtobsb_capture_fixture.fixture_double"
SOURCE_ID = "source.dbtobsb_capture_fixture.fixture_source.fixture_table"
MACRO_ID = "macro.dbtobsb_capture_fixture.fixture_macro"
METRIC_ID = "metric.dbtobsb_capture_fixture.fixture_row_count"
SEMANTIC_MODEL_ID = "semantic_model.dbtobsb_capture_fixture.fixture_semantic"
APPROVED_SOURCE_MANIFEST_SHA256 = "14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c"

CANARIES = {
    "compiled_sql": "CANARY_COMPILED_SQL_SELECT_SECRET",
    "environment": "CANARY_ENVIRONMENT_PERSONAL_DATA",
    "message": "CANARY_RESULT_MESSAGE_DATABASE_ERROR",
    "relation": "CANARY_RELATION_CUSTOMER_SECRET",
    "path": "models/CANARY_PATH_INTERNAL/observed_model.sql",
    "email": "CANARY_EMAIL@example.invalid",
    "token": "CANARY_TOKEN_NOT_A_REAL_CREDENTIAL",
    "vars": "CANARY_VARS_PRIVATE_VALUE",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _filtered_mapping(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: copy.deepcopy(item) for key, item in value.items() if key in keys}


def _manifest(source: dict[str, Any]) -> dict[str, Any]:
    node_ids = {MODEL_ID, SEED_ID, SNAPSHOT_ID, DATA_TEST_ID}
    kept_ids = {
        *node_ids,
        UNIT_TEST_ID,
        SAVED_QUERY_ID,
        EXPOSURE_ID,
        FUNCTION_ID,
        SOURCE_ID,
        METRIC_ID,
        SEMANTIC_MODEL_ID,
    }
    manifest = {
        "metadata": {
            "dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v12.json",
            "dbt_version": "1.11.12",
            "generated_at": "2026-01-01T00:00:01Z",
            "invocation_id": FIXED_INVOCATION_ID,
            "invocation_started_at": "2026-01-01T00:00:00Z",
            "env": {"SENSITIVE": CANARIES["environment"]},
            "project_name": "CANARY_PROJECT_PRIVATE_NAME",
            "project_id": "00000000000000000000000000000000",
            "user_id": None,
            "send_anonymous_usage_stats": False,
            "adapter_type": "databricks",
            "quoting": {
                "database": True,
                "schema": True,
                "identifier": True,
                "column": None,
            },
            "run_started_at": "2026-01-01T00:00:00+00:00",
        },
        "nodes": _filtered_mapping(source.get("nodes"), node_ids),
        "sources": _filtered_mapping(source.get("sources"), {SOURCE_ID}),
        "macros": _filtered_mapping(source.get("macros"), {MACRO_ID}),
        "docs": {},
        "exposures": _filtered_mapping(source.get("exposures"), {EXPOSURE_ID}),
        "metrics": _filtered_mapping(source.get("metrics"), {METRIC_ID}),
        "groups": {},
        "selectors": copy.deepcopy(source.get("selectors", {})),
        "disabled": {},
        "parent_map": _filtered_mapping(source.get("parent_map"), kept_ids),
        "child_map": _filtered_mapping(source.get("child_map"), kept_ids),
        "group_map": {},
        "saved_queries": _filtered_mapping(source.get("saved_queries"), {SAVED_QUERY_ID}),
        "semantic_models": _filtered_mapping(source.get("semantic_models"), {SEMANTIC_MODEL_ID}),
        "unit_tests": _filtered_mapping(source.get("unit_tests"), {UNIT_TEST_ID}),
        "functions": _filtered_mapping(source.get("functions"), {FUNCTION_ID}),
    }

    node = manifest["nodes"][MODEL_ID]
    node["created_at"] = 1767225600.0
    node["original_file_path"] = CANARIES["path"]
    node["raw_code"] = CANARIES["compiled_sql"]

    source_resource = manifest["sources"][SOURCE_ID]
    source_resource["created_at"] = 1767225600.0
    source_resource["original_file_path"] = CANARIES["path"]

    unit_test = manifest["unit_tests"][UNIT_TEST_ID]
    unit_test["created_at"] = 1767225600.0
    unit_test["original_file_path"] = CANARIES["path"]

    exposure = manifest["exposures"][EXPOSURE_ID]
    exposure["created_at"] = 1767225600.0
    exposure["original_file_path"] = CANARIES["path"]
    exposure["owner"] = {"name": "CANARY_PERSON_NAME", "email": CANARIES["email"]}

    macro = manifest["macros"][MACRO_ID]
    macro["created_at"] = 1767225600.0
    macro["original_file_path"] = CANARIES["path"]
    macro["macro_sql"] = CANARIES["token"]
    return manifest


def _validate_approved_source(source_bytes: bytes, source: dict[str, Any]) -> str:
    """Authenticate the reviewed synthetic parse before copying any resource."""
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != APPROVED_SOURCE_MANIFEST_SHA256:
        raise ValueError("source manifest is not the reviewed synthetic parse")
    if next(iter(validator_for(MANIFEST_SCHEMA_NAME).iter_errors(source)), None) is not None:
        raise ValueError("source manifest does not satisfy the pinned schema")
    metadata = source.get("metadata")
    if not isinstance(metadata, dict) or (
        metadata.get("dbt_schema_version"),
        metadata.get("dbt_version"),
        metadata.get("adapter_type"),
    ) != (
        "https://schemas.getdbt.com/dbt/manifest/v12.json",
        "1.11.12",
        "databricks",
    ):
        raise ValueError("source manifest origin is not the reviewed candidate")
    macros = source.get("macros")
    if not isinstance(macros, dict) or len(macros) != 1:
        raise ValueError("source manifest macro inventory is not the reviewed candidate")
    required = {
        "nodes": {MODEL_ID, SEED_ID, SNAPSHOT_ID, DATA_TEST_ID},
        "unit_tests": {UNIT_TEST_ID},
        "saved_queries": {SAVED_QUERY_ID},
        "exposures": {EXPOSURE_ID},
        "functions": {FUNCTION_ID},
        "sources": {SOURCE_ID},
        "metrics": {METRIC_ID},
        "semantic_models": {SEMANTIC_MODEL_ID},
        "macros": {MACRO_ID},
    }
    for collection_name, identifiers in required.items():
        collection = _filtered_mapping(source.get(collection_name), identifiers)
        if set(collection) != identifiers:
            raise ValueError("source manifest inventory is not the reviewed candidate")
    return source_hash


def _run_results(*, status: str, invocation_id: str) -> dict[str, Any]:
    return {
        "metadata": {
            "dbt_schema_version": "https://schemas.getdbt.com/dbt/run-results/v6.json",
            "dbt_version": "1.11.12",
            "generated_at": "2026-01-01T00:00:02Z",
            "invocation_id": invocation_id,
            "invocation_started_at": "2026-01-01T00:00:00Z",
            "env": {"SENSITIVE": CANARIES["environment"]},
        },
        "results": [
            {
                "status": status,
                "timing": [
                    {
                        "name": "execute",
                        "started_at": "2026-01-01T00:00:01Z",
                        "completed_at": "2026-01-01T00:00:02Z",
                    }
                ],
                "thread_id": "Thread-1",
                "execution_time": 0.125,
                "adapter_response": {
                    "_message": CANARIES["message"],
                    "job_id": "101",
                    "job_run_id": "202",
                    "task_run_id": "303",
                    "token_like": CANARIES["token"],
                },
                "message": CANARIES["message"],
                "failures": None,
                "unique_id": MODEL_ID,
                "compiled": True,
                "compiled_code": CANARIES["compiled_sql"],
                "relation_name": CANARIES["relation"],
            }
        ],
        "elapsed_time": 0.25,
        "args": {
            "which": "build",
            "selector": "observability_demo",
            "select": [],
            "exclude": [],
            "indirect_selection": "eager",
            "full_refresh": None,
            "vars": {"private": CANARIES["vars"]},
        },
    }


def _valid_report(status: str) -> dict[str, Any]:
    return {
        "schema_version": "dbtobsb.artifact-pair-report.v1",
        "pair_state": "PAIR_VALID",
        "summary": {
            "manifest_schema": "https://schemas.getdbt.com/dbt/manifest/v12.json",
            "run_results_schema": "https://schemas.getdbt.com/dbt/run-results/v6.json",
            "dbt_version": "1.11.12",
            "adapter_type": "databricks",
            "command": "build",
            "status_counts": {status: 1},
        },
        "issues": [],
    }


def _mismatch_report() -> dict[str, Any]:
    issue = {
        "code": "DBT_INVOCATION_ID_MISMATCH",
        "component": "artifact_pair",
        "field": "metadata.invocation_id",
        "observed_category": "different_valid_values",
        "impact": "The files do not have the same dbt invocation identity.",
        "next_action": (
            "Collect both closed artifacts from one completed pinned dbt build invocation "
            "before another dbt command runs."
        ),
    }
    return {
        "schema_version": "dbtobsb.artifact-pair-report.v1",
        "pair_state": "PAIR_INVALID",
        "summary": None,
        "issues": [issue],
    }


def _provenance(
    *,
    fixture_kind: str,
    source_manifest_sha256: str,
    manifest_path: Path,
    run_results_path: Path,
) -> dict[str, Any]:
    return {
        "fixture_kind": fixture_kind,
        "runtime_evidence": False,
        "source_kind": "reviewed_synthetic_manifest_projection_plus_synthetic_run_results",
        "source_command": (
            "project fixture parsed with dbt; reviewed projection checked into fixture_source"
        ),
        "source_manifest_sha256": source_manifest_sha256,
        "sanitizer": "capture/scripts/generate_artifact_pair_fixtures.py",
        "schema_compatibility_note": (
            "The exact Core 1.11.12 tag schema is pinned because the generic published v12 "
            "endpoint was stale on 2026-07-15. The candidate locks dbt-adapters 1.23.0, whose "
            "raw parsed manifest validates without an overlay. This fixture is not runtime "
            "evidence."
        ),
        "candidate_context": {
            "runtime_attestation": False,
            "note": (
                "Reviewed compatibility context only; the source manifest does not attest "
                "these transitive package versions or wheel digests."
            ),
            "python": "3.12.3",
            "dbt_core": "1.11.12",
            "dbt_core_wheel_sha256": (
                "3b7760a3760a6db8a14a6ef38fb86532b2c2b150d49beaa1feb0f50170baa86e"
            ),
            "dbt_databricks": "1.12.2",
            "dbt_databricks_wheel_sha256": (
                "158d76c940f3f0b0a8229203d9efb0752c73b881ede21c8f0696cfe9484aec43"
            ),
            "dbt_common": "1.37.5",
            "dbt_common_wheel_sha256": (
                "432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077"
            ),
            "dbt_adapters": "1.23.0",
            "dbt_adapters_wheel_sha256": (
                "6c6c9cb6fca5d01324b5c39961c8b16b985b1ac7b701909f4416ce9dad66e288"
            ),
            "dbt_protos": "1.0.541",
            "dbt_protos_wheel_sha256": (
                "4e03f88e6b5c13a8cac68c6aa78267d8eb4396e6341a807112d619ab938318d5"
            ),
            "dbt_spark": "1.10.3",
            "dbt_spark_wheel_sha256": (
                "1906f4cb507c931c4988ea6074603769da7466788b53483546e3abf6eabbf04d"
            ),
        },
        "schema_sha256": {
            "manifest_v12_core_1_11_12": (
                "b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3"
            ),
            "run_results_v6": ("1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf"),
        },
        "artifact_sha256": {
            "manifest": _sha256(manifest_path),
            "run_results": _sha256(run_results_path),
        },
        "canary_categories": sorted(CANARIES),
    }


def generate(*, source_manifest_path: Path, output_root: Path) -> None:
    source_bytes = source_manifest_path.read_bytes()
    source: Any = json.loads(source_bytes)
    if not isinstance(source, dict):
        raise ValueError("source manifest root must be an object")
    source_hash = _validate_approved_source(source_bytes, source)
    manifest = _manifest(source)

    fixtures = (
        ("valid_success", "success", FIXED_INVOCATION_ID, _valid_report("success")),
        ("valid_dbt_failure", "error", FIXED_INVOCATION_ID, _valid_report("error")),
        (
            "invalid_invocation_mismatch",
            "success",
            MISMATCHED_INVOCATION_ID,
            _mismatch_report(),
        ),
    )
    for fixture_kind, status, invocation_id, expected_report in fixtures:
        fixture_root = output_root / fixture_kind
        manifest_path = fixture_root / "manifest.json"
        run_results_path = fixture_root / "run_results.json"
        _write_json(manifest_path, manifest)
        _write_json(run_results_path, _run_results(status=status, invocation_id=invocation_id))
        _write_json(fixture_root / "expected-report.json", expected_report)
        _write_json(
            fixture_root / "provenance.json",
            _provenance(
                fixture_kind=fixture_kind,
                source_manifest_sha256=source_hash,
                manifest_path=manifest_path,
                run_results_path=run_results_path,
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    arguments = parser.parse_args()
    generate(source_manifest_path=arguments.source_manifest, output_root=arguments.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
