"""Generate the semantic runtime-trust v1 golden contract from one typed chain."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from unittest.mock import patch

from dbtobsb_installer import runtime_trust

HERE = Path(__file__).resolve().parent
VECTOR_PATH = HERE / "vectors-v1.json"
TEST_MODULE_PATH = HERE.parent / "test_runtime_trust.py"


class RuntimeTrustVectorError(ValueError):
    """A sanitized mismatch between checked-in vectors and typed product behavior."""


def _load_test_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_dbtobsb_runtime_trust_semantic_source",
        TEST_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_SOURCE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _captured_domain_records(
    module: ModuleType,
) -> tuple[dict[runtime_trust._Domain, dict[str, Any]], tuple[Any, Any, Any]]:
    records: dict[runtime_trust._Domain, dict[str, Any]] = {}
    original_digest = runtime_trust._digest

    def capture(domain: runtime_trust._Domain, data: Mapping[str, Any]) -> str:
        records[domain] = copy.deepcopy(dict(data))
        return original_digest(domain, data)

    with patch.object(runtime_trust, "_digest", capture):
        registration, candidate, acceptance = cast(Any, module)._chain()
        candidate_at = cast(Any, module).datetime(
            2026,
            7,
            16,
            10,
            0,
            0,
            123456,
            tzinfo=cast(Any, module).UTC,
        )
        accepted_at = cast(Any, module).datetime(
            2026,
            7,
            16,
            10,
            5,
            0,
            654321,
            tzinfo=cast(Any, module).UTC,
        )
        runtime_trust.derive_event_record(
            acceptance,
            statement_evaluated_at=accepted_at,
            candidate_statement_evaluated_at=candidate_at,
            roster_statement_evaluated_at=candidate_at,
        )
    if set(records) != set(runtime_trust._Domain):
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_DOMAIN_COVERAGE_INVALID")
    return records, (registration, candidate, acceptance)


def _semantic_invalid(
    records: dict[runtime_trust._Domain, dict[str, Any]],
) -> list[dict[str, Any]]:
    missing = copy.deepcopy(records[runtime_trust._Domain.DEPLOYMENT_SET])
    del missing["app_digest"]
    extra = copy.deepcopy(records[runtime_trust._Domain.EVENT_ID])
    extra["unbound_field"] = "must-reject"
    wrong_nested = copy.deepcopy(records[runtime_trust._Domain.ROSTER_OBSERVATION])
    observed = cast(list[dict[str, Any]], wrong_nested["observed_components"])[0]
    observed["observation"] = observed.pop("observation_digest")
    wrong_enum = copy.deepcopy(records[runtime_trust._Domain.MACHINE_OBSERVATION])
    wrong_enum["phase"] = "BETWEEN_STARTS"

    component_order = copy.deepcopy(records[runtime_trust._Domain.ROSTER_OBSERVATION])
    expected_base = cast(list[dict[str, Any]], component_order["expected_components"])[0]
    observed_base = cast(list[dict[str, Any]], component_order["observed_components"])[0]
    expected_system = {
        "component_key": "SYSTEM_ENRICHMENT",
        "contract_digest": "2" * 64,
    }
    observed_system = {
        **expected_system,
        "observation_digest": "3" * 64,
    }
    component_order["expected_component_count"] = "2"
    component_order["expected_components"] = [expected_system, expected_base]
    component_order["observed_components"] = [observed_system, observed_base]

    duplicate_component = copy.deepcopy(records[runtime_trust._Domain.ROSTER_OBSERVATION])
    duplicate_component["expected_component_count"] = "2"
    duplicate_component["expected_components"] = [
        copy.deepcopy(expected_base),
        copy.deepcopy(expected_base),
    ]
    duplicate_component["observed_components"] = [
        copy.deepcopy(observed_base),
        copy.deepcopy(observed_base),
    ]

    deployment_order = copy.deepcopy(records[runtime_trust._Domain.DEPLOYMENT_SET])
    selected = cast(list[dict[str, Any]], deployment_order["deployments"])[0]
    lower_id = copy.deepcopy(selected)
    lower_id["deployment_id"] = "0" * 32
    deployment_order["deployments"] = [selected, lower_id]

    duplicate_deployment = copy.deepcopy(records[runtime_trust._Domain.DEPLOYMENT_SET])
    duplicate_deployment["deployments"] = [
        copy.deepcopy(selected),
        copy.deepcopy(selected),
    ]
    return [
        {
            "name": "missing-top-level-field",
            "category": "missing_field",
            "domain": runtime_trust._Domain.DEPLOYMENT_SET.value,
            "data": missing,
        },
        {
            "name": "extra-top-level-field",
            "category": "extra_field",
            "domain": runtime_trust._Domain.EVENT_ID.value,
            "data": extra,
        },
        {
            "name": "wrong-nested-field",
            "category": "wrong_nested_field",
            "domain": runtime_trust._Domain.ROSTER_OBSERVATION.value,
            "data": wrong_nested,
        },
        {
            "name": "wrong-enum",
            "category": "wrong_enum",
            "domain": runtime_trust._Domain.MACHINE_OBSERVATION.value,
            "data": wrong_enum,
        },
        {
            "name": "component-array-order",
            "category": "array_order",
            "domain": runtime_trust._Domain.ROSTER_OBSERVATION.value,
            "data": component_order,
        },
        {
            "name": "duplicate-component-key",
            "category": "duplicate",
            "domain": runtime_trust._Domain.ROSTER_OBSERVATION.value,
            "data": duplicate_component,
        },
        {
            "name": "deployment-array-order",
            "category": "array_order",
            "domain": runtime_trust._Domain.DEPLOYMENT_SET.value,
            "data": deployment_order,
        },
        {
            "name": "duplicate-deployment-id",
            "category": "duplicate",
            "domain": runtime_trust._Domain.DEPLOYMENT_SET.value,
            "data": duplicate_deployment,
        },
    ]


def _event_conflicts(
    module: ModuleType,
    registration: runtime_trust.ManifestRegistered,
) -> list[dict[str, Any]]:
    changed = replace(
        registration,
        expected_components=(
            runtime_trust.ExpectedComponent(
                runtime_trust.ComponentKey.BASE_OBSERVABILITY,
                "2" * 64,
            ),
        ),
    )
    at = cast(Any, module).datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=cast(Any, module).UTC)

    def variant(event: runtime_trust.ManifestRegistered) -> dict[str, Any]:
        payload_data: dict[str, Any] | None = None
        original_digest = runtime_trust._digest

        def capture(domain: runtime_trust._Domain, data: Mapping[str, Any]) -> str:
            nonlocal payload_data
            if domain is runtime_trust._Domain.PAYLOAD:
                payload_data = copy.deepcopy(dict(data))
            return original_digest(domain, data)

        with patch.object(runtime_trust, "_digest", capture):
            record = runtime_trust.derive_event_record(event, statement_evaluated_at=at)
        if payload_data is None:
            raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_PAYLOAD_MISSING")
        return {
            "event_id": record.event_id,
            "data": payload_data,
            "canonical": runtime_trust._canonical_object(
                runtime_trust._Domain.PAYLOAD,
                payload_data,
            ).decode("ascii"),
            "sha256": record.payload_digest,
        }

    original = variant(registration)
    different = variant(changed)
    if original["event_id"] != different["event_id"] or original["sha256"] == different["sha256"]:
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_EVENT_CONFLICT_INVALID")
    return [
        {
            "name": "same-event-different-payload",
            "domain": runtime_trust._Domain.PAYLOAD.value,
            "original": original,
            "changed": different,
        }
    ]


def _version_separation(
    records: dict[runtime_trust._Domain, dict[str, Any]],
) -> list[dict[str, Any]]:
    domain = runtime_trust._Domain.EVENT_ID
    v1_data = copy.deepcopy(records[domain])
    v2_data = {**v1_data, "contract_version": "dbtobsb.runtime-trust.v2"}

    def version(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "data": data,
            "canonical": runtime_trust._canonical_object(domain, data).decode("ascii"),
            "sha256": runtime_trust._digest(domain, data),
        }

    return [
        {
            "name": "event-contract-version-separation",
            "domain": domain.value,
            "v1": version(v1_data),
            "v2": version(v2_data),
        }
    ]


def build_contract() -> dict[str, Any]:
    """Build all domain and SQL goldens from one registration-to-acceptance chain."""
    module = _load_test_module()
    records, (registration, candidate, acceptance) = _captured_domain_records(module)
    invalidation = cast(Any, module)._invalidation()
    original_digest = runtime_trust._digest
    domains: list[dict[str, Any]] = []
    for domain in runtime_trust._Domain:
        data = records[domain]
        domains.append(
            {
                "name": domain.name.lower().replace("_", "-"),
                "domain": domain.value,
                "data": data,
                "canonical": runtime_trust._canonical_object(domain, data).decode("ascii"),
                "sha256": original_digest(domain, data),
            }
        )

    names = runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb")
    events = {
        "registration": registration,
        "candidate": candidate,
        "acceptance": acceptance,
        "invalidation": invalidation,
    }
    sql: list[dict[str, Any]] = []

    def add_sql(name: str, statement: runtime_trust.RuntimeTrustStatement) -> None:
        text = statement._transport_text()
        sql.append(
            {
                "name": name,
                "kind": statement.kind.value,
                "semantic_sha256": statement.semantic_sha256,
                "utf8_size": len(text.encode("utf-8")),
            }
        )

    add_sql("create-ledger", runtime_trust.render_create_ledger_statement(names))
    add_sql("create-status-view", runtime_trust.render_create_status_view_statement(names))
    for name, event in events.items():
        add_sql(
            f"append-{name}",
            runtime_trust.render_append_event_statement(names, event),
        )
        add_sql(
            f"readback-{name}",
            runtime_trust.render_event_readback_statement(names, event),
        )
    return {
        "contract_version": "dbtobsb.runtime-trust.semantic-golden-v1",
        "domain_count": len(runtime_trust._Domain),
        "domains": domains,
        "decimal_valid": [
            "0",
            "1",
            "2147483647",
            "9007199254740991",
            "9007199254740992",
            "9007199254740993",
            "9223372036854775807",
        ],
        "decimal_invalid": [
            {"name": "negative", "value": "-1"},
            {"name": "leading-zero", "value": "01"},
            {"name": "plus-sign", "value": "+1"},
            {"name": "fractional", "value": "1.0"},
            {"name": "exponent", "value": "1e0"},
            {"name": "empty", "value": ""},
            {"name": "leading-whitespace", "value": " 1"},
            {"name": "trailing-whitespace", "value": "1 "},
            {"name": "unicode-digit", "value": "١"},  # noqa: RUF001
            {"name": "json-number", "value": 1},
            {"name": "null-required", "value": None},
            {"name": "overflow", "value": "9223372036854775808"},
        ],
        "canonical_invalid": [
            {"name": "json-number", "value": {"n": 1}},
            {"name": "json-boolean", "value": {"n": True}},
            {"name": "unicode-string", "value": {"n": "å"}},
        ],
        "timestamp_valid": [
            "2026-07-16T10:05:00.654321Z",
            "2000-02-29T23:59:59.000000Z",
        ],
        "timestamp_invalid": [
            {"name": "missing-microseconds", "value": "2026-07-16T10:05:00Z"},
            {
                "name": "offset-not-z",
                "value": "2026-07-16T10:05:00.654321+00:00",
            },
            {"name": "invalid-calendar-day", "value": "2026-02-30T10:05:00.654321Z"},
        ],
        "semantic_invalid": _semantic_invalid(records),
        "event_conflicts": _event_conflicts(module, registration),
        "version_separation": _version_separation(records),
        "sql": sql,
    }


def render_contract() -> str:
    return json.dumps(build_contract(), ensure_ascii=False, indent=2) + "\n"


def validate_contract_document(document: dict[str, Any]) -> None:
    """Reject any checked-in field, shape, enum, digest, or SQL golden drift."""
    if document != build_contract():
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_SEMANTIC_MISMATCH")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rendered = render_contract()
    if args.write:
        VECTOR_PATH.write_text(rendered, encoding="utf-8")
        return 0
    try:
        observed = VECTOR_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_READ_FAILED") from error
    if observed != rendered:
        raise RuntimeTrustVectorError("DBTOBSB_RUNTIME_TRUST_VECTOR_SEMANTIC_MISMATCH")
    print(
        "runtime-trust Python semantic contract verified: 12 domains, 10 SQL, "
        "7 decimal accepts, 12 decimal rejects, 3 canonical rejects, "
        "2 timestamp accepts, 3 timestamp rejects, 8 semantic rejects, "
        "1 event conflict, 1 version separation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
