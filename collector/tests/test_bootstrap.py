"""Fixed bootstrap-mode contract tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from dbtobsb_collector.bootstrap import (
    INVOCATION_FIELDS,
    NODE_FIELDS,
    NODE_VIEW_FIELDS,
    OBJECT_MANIFEST_VERSION,
    REGISTRY_FIELDS,
    RUN_VIEW_FIELDS,
    bootstrap_objects,
)
from dbtobsb_collector.entrypoints import collect


@dataclass
class _DataType:
    value: str

    def simpleString(self) -> str:
        return self.value


@dataclass
class _Field:
    name: str
    dataType: _DataType


@dataclass
class _Schema:
    fields: list[_Field]


@dataclass
class _Table:
    schema: _Schema


class _Spark:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.statements: list[str] = []
        self._schemas = [
            REGISTRY_FIELDS,
            INVOCATION_FIELDS,
            NODE_FIELDS,
            RUN_VIEW_FIELDS,
            NODE_VIEW_FIELDS,
        ]
        self._mismatch = mismatch
        self._index = 0

    def sql(self, query: str) -> None:
        self.statements.append(query)

    def table(self, table_name: str) -> _Table:
        fields = self._schemas[self._index]
        self._index += 1
        if self._mismatch and self._index == 1:
            fields = fields[:-1]
        return _Table(_Schema([_Field(name, _DataType(kind)) for name, kind in fields]))


def test_bootstrap_creates_only_fixed_objects_and_verifies_them() -> None:
    spark = _Spark()
    result = bootstrap_objects(
        spark,
        catalog="catalog-with-hyphen",
        schema="observability",
        raw_volume_name="dbtobsb_raw",
    )

    assert result.manifest_version == OBJECT_MANIFEST_VERSION
    assert len(result.verified_objects) == 5
    assert result.raw_volume.endswith(".`dbtobsb_raw`")
    rendered = "\n".join(spark.statements).upper()
    assert "CREATE SCHEMA IF NOT EXISTS" in rendered
    assert rendered.count("CREATE TABLE IF NOT EXISTS") == 3
    assert rendered.count("CREATE VIEW IF NOT EXISTS") == 2
    assert "CREATE VOLUME IF NOT EXISTS" in rendered
    assert "CREATE OR REPLACE" not in rendered


def test_bootstrap_rejects_an_incompatible_existing_object() -> None:
    with pytest.raises(RuntimeError, match="DBTOBSB_BOOTSTRAP_OBJECT_SCHEMA_MISMATCH"):
        bootstrap_objects(_Spark(mismatch=True), catalog="c", schema="s")


def test_runtime_entrypoint_has_no_bootstrap_mode_parameter() -> None:
    code_names = set(collect.__code__.co_names)

    assert "mode" not in code_names
    assert "bootstrap_objects" not in code_names
