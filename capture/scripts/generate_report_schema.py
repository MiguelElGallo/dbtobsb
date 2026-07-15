"""Generate or verify the closed artifact-pair report v1 JSON schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dbtobsb_capture.inspector import _ISSUES
from dbtobsb_capture.registry import ISSUE_PRECEDENCE, MAX_REPORT_ISSUES, NATIVE_STATUSES

OUTPUT = (
    Path(__file__).parents[1]
    / "src"
    / "dbtobsb_capture"
    / "schemas"
    / "artifact-pair-report-v1.json"
)


def _issue_variant(code: str) -> dict[str, Any]:
    template = _ISSUES[code]
    values = {
        "code": code,
        "component": template.component,
        "field": template.field,
        "observed_category": template.observed_category,
        "impact": template.impact,
        "next_action": template.next_action,
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(values),
        "properties": {name: {"const": value} for name, value in values.items()},
    }


def _issue_ref(code: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/issue_variants/{code}"}


def _primary_precedence_rule(code: str, earlier_codes: tuple[str, ...]) -> dict[str, Any]:
    """Require the first issue to be the earliest issue present in the v1 registry."""
    return {
        "if": {
            "properties": {
                "issues": {
                    "minItems": 1,
                    "prefixItems": [_issue_ref(code)],
                }
            }
        },
        "then": {
            "properties": {
                "issues": {
                    "allOf": [
                        {"not": {"contains": _issue_ref(earlier_code)}}
                        for earlier_code in earlier_codes
                    ]
                }
            }
        },
    }


def report_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:dbtobsb:artifact-pair-report:v1",
        "title": "dbtobsb artifact-pair inspection report v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "pair_state", "summary", "issues"],
        "properties": {
            "schema_version": {"const": "dbtobsb.artifact-pair-report.v1"},
            "pair_state": {"enum": ["PAIR_VALID", "PAIR_INVALID"]},
            "summary": {"anyOf": [{"$ref": "#/$defs/summary"}, {"type": "null"}]},
            "issues": {
                "type": "array",
                "maxItems": MAX_REPORT_ISSUES,
                "uniqueItems": True,
                "items": {"$ref": "#/$defs/issue"},
            },
        },
        "$defs": {
            "summary": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "manifest_schema",
                    "run_results_schema",
                    "dbt_version",
                    "adapter_type",
                    "command",
                    "status_counts",
                ],
                "properties": {
                    "manifest_schema": {
                        "const": "https://schemas.getdbt.com/dbt/manifest/v12.json"
                    },
                    "run_results_schema": {
                        "const": "https://schemas.getdbt.com/dbt/run-results/v6.json"
                    },
                    "dbt_version": {"const": "1.11.12"},
                    "adapter_type": {"const": "databricks"},
                    "command": {"const": "build"},
                    "status_counts": {
                        "type": "object",
                        "additionalProperties": False,
                        "minProperties": 1,
                        "maxProperties": len(NATIVE_STATUSES),
                        "properties": {
                            status: {"type": "integer", "minimum": 1} for status in NATIVE_STATUSES
                        },
                    },
                },
            },
            "issue": {"oneOf": [_issue_ref(code) for code in ISSUE_PRECEDENCE]},
            "issue_variants": {code: _issue_variant(code) for code in ISSUE_PRECEDENCE},
        },
        "oneOf": [
            {
                "properties": {
                    "pair_state": {"const": "PAIR_VALID"},
                    "summary": {"$ref": "#/$defs/summary"},
                    "issues": {"maxItems": 0},
                }
            },
            {
                "properties": {
                    "pair_state": {"const": "PAIR_INVALID"},
                    "summary": {"type": "null"},
                    "issues": {"minItems": 1},
                },
                "allOf": [
                    _primary_precedence_rule(code, ISSUE_PRECEDENCE[:rank])
                    for rank, code in enumerate(ISSUE_PRECEDENCE)
                ],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    rendered = json.dumps(report_schema(), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if arguments.check:
        return 0 if OUTPUT.read_text(encoding="utf-8") == rendered else 1
    OUTPUT.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
