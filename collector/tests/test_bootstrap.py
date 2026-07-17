"""Fresh-install-only bootstrap contract tests."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from typing import Any

import pytest

import dbtobsb_collector.bootstrap as bootstrap_module
from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    COLLECTION_HEALTH_FIELDS,
    COLLECTION_HEALTH_VIEW,
    INVOCATION_FIELDS,
    INVOCATIONS_TABLE,
    MANIFEST_FIELDS,
    MANIFEST_TABLE,
    NODE_FIELDS,
    NODE_HEALTH_VIEW,
    NODE_RESULTS_TABLE,
    NODE_VIEW_FIELDS,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    RAW_VOLUME_NAME,
    REGISTRY_FIELDS,
    REGISTRY_TABLE,
    RUN_HEALTH_VIEW,
    RUN_VIEW_FIELDS,
    STAGE_VOLUME_NAME,
    InstallationBinding,
    bootstrap_objects,
    delete_installation_objects,
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


@dataclass
class _Frame:
    rows: list[Any]

    def collect(self) -> list[Any]:
        return self.rows


@dataclass
class _Relation:
    fields: tuple[tuple[str, str], ...]
    object_type: str
    provider: str | None
    properties: dict[str, str]
    view_text: str | None = None
    owner: str = "installer-owner"


_FIELDS_BY_NAME = {
    MANIFEST_TABLE: MANIFEST_FIELDS,
    REGISTRY_TABLE: REGISTRY_FIELDS,
    INVOCATIONS_TABLE: INVOCATION_FIELDS,
    NODE_RESULTS_TABLE: NODE_FIELDS,
    RUN_HEALTH_VIEW: RUN_VIEW_FIELDS,
    NODE_HEALTH_VIEW: NODE_VIEW_FIELDS,
    COLLECTION_HEALTH_VIEW: COLLECTION_HEALTH_FIELDS,
}

_BINDING = InstallationBinding(
    workspace_id=101,
    warehouse_id="0123456789abcdef",
    source_contract_sha256="c" * 64,
    expected_runtime_policy_sha256="d" * 64,
    observed_job_id=201,
    collector_job_id=202,
    reconciler_job_id=203,
    observed_service_principal_name="observed-sp",
    collector_service_principal_name="collector-sp",
    job_manager_group_name="job-managers",
    collector_environment_sha256="b" * 64,
)


def _manifest_row(*, catalog: str = "c", schema: str = "s") -> dict[str, str | int]:
    return {
        "manifest_version": OBJECT_MANIFEST_VERSION,
        "object_contract_sha256": OBJECT_CONTRACT_SHA256,
        "source_contract_sha256": _BINDING.source_contract_sha256,
        "expected_runtime_policy_sha256": _BINDING.expected_runtime_policy_sha256,
        "base_observability_contract_sha256": BASE_OBSERVABILITY_CONTRACT_SHA256,
        "installation_id": bootstrap_module._installation_id(
            _BINDING, catalog=catalog, schema=schema
        ),
        "workspace_id": _BINDING.workspace_id,
        "evidence_catalog": catalog,
        "evidence_schema": schema,
        "warehouse_id": _BINDING.warehouse_id,
        "observed_job_id": _BINDING.observed_job_id,
        "collector_job_id": _BINDING.collector_job_id,
        "reconciler_job_id": _BINDING.reconciler_job_id,
        "observed_service_principal_name": _BINDING.observed_service_principal_name,
        "collector_service_principal_name": _BINDING.collector_service_principal_name,
        "job_manager_group_name": _BINDING.job_manager_group_name,
        "collector_environment_sha256": _BINDING.collector_environment_sha256,
    }


@dataclass
class _Spark:
    catalog: str = "c"
    schema_name: str = "s"
    schema_exists: bool = True
    owner: str = "installer-owner"
    schema_owner: str | None = None
    session_actor: str | None = None
    relations: dict[str, _Relation] = field(default_factory=dict)
    volume: dict[str, Any] | None = None
    stage_volume: dict[str, Any] | None = None
    grant_rows: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    manifest_rows: list[dict[str, str | int]] = field(default_factory=list)
    statements: list[str] = field(default_factory=list)

    @staticmethod
    def _identifiers(query: str) -> list[str]:
        return [value.replace("``", "`") for value in re.findall(r"`((?:``|[^`])*)`", query)]

    @staticmethod
    def _properties(query: str) -> dict[str, str]:
        return dict(re.findall(r"'([^']+)' = '([^']*)'", query))

    def _create_relation(self, query: str, *, object_type: str) -> None:
        identifiers = self._identifiers(query)
        catalog, schema, name = identifiers[:3]
        self.catalog = catalog
        self.schema_name = schema
        provider = "delta" if object_type == "MANAGED" else None
        view_text = query.split("\nAS\n", maxsplit=1)[1] if object_type == "VIEW" else None
        self.relations[name] = _Relation(
            fields=_FIELDS_BY_NAME[name],
            object_type=object_type,
            provider=provider,
            properties=self._properties(query),
            view_text=view_text,
            owner=self.owner,
        )

    def sql(self, query: str) -> _Frame:
        self.statements.append(query)
        upper = query.lstrip().upper()
        if upper.startswith("SELECT SESSION_USER() AS SESSION_USER"):
            return _Frame([{"session_user": self.session_actor or self.owner}])
        if upper.startswith("SELECT SCHEMA_NAME, SCHEMA_OWNER"):
            rows = (
                [
                    {
                        "schema_name": self.schema_name,
                        "schema_owner": self.schema_owner or self.owner,
                    }
                ]
                if self.schema_exists
                else []
            )
            return _Frame(rows)
        if upper.startswith("SELECT TABLE_NAME, TABLE_TYPE"):
            return _Frame(
                [
                    {
                        "table_name": name,
                        "table_type": "VIEW" if relation.object_type == "VIEW" else "BASE TABLE",
                    }
                    for name, relation in self.relations.items()
                ]
            )
        if upper.startswith("SELECT VOLUME_NAME, VOLUME_TYPE"):
            return _Frame(
                [volume for volume in (self.volume, self.stage_volume) if volume is not None]
            )
        if upper.startswith("SELECT\n  MANIFEST_VERSION,"):
            return _Frame(self.manifest_rows)
        if upper.startswith("SHOW GRANTS ON"):
            securable_type = upper.split()[3]
            object_name = self._identifiers(query)[2]
            return _Frame(self.grant_rows.get((securable_type, object_name), []))
        if upper.startswith("DESCRIBE TABLE EXTENDED"):
            catalog, schema, name = self._identifiers(query)[:3]
            relation = self.relations[name]
            payload = {
                "catalog_name": catalog,
                "schema_name": schema,
                "table_name": name,
                "type": relation.object_type,
                "provider": relation.provider,
                "table_properties": relation.properties,
                "view_text": relation.view_text,
                "owner": relation.owner,
            }
            return _Frame([{"json_string": json.dumps(payload)}])
        if upper.startswith("CREATE TABLE"):
            self._create_relation(query, object_type="MANAGED")
            return _Frame([])
        if upper.startswith("CREATE VIEW"):
            self._create_relation(query, object_type="VIEW")
            return _Frame([])
        if upper.startswith("CREATE VOLUME"):
            catalog, schema, name = self._identifiers(query)[:3]
            self.catalog = catalog
            self.schema_name = schema
            comment = re.search(r" COMMENT '([^']+)'$", query)
            assert comment is not None
            value = {
                "volume_name": name,
                "volume_type": "MANAGED",
                "volume_owner": self.owner,
                "comment": comment.group(1),
            }
            if name == STAGE_VOLUME_NAME:
                self.stage_volume = value
            else:
                self.volume = value
            return _Frame([])
        if upper.startswith("DROP VIEW") or upper.startswith("DROP TABLE"):
            name = self._identifiers(query)[2]
            self.relations.pop(name)
            if name == MANIFEST_TABLE:
                self.manifest_rows.clear()
            return _Frame([])
        if upper.startswith("DROP VOLUME"):
            name = self._identifiers(query)[2]
            if name == STAGE_VOLUME_NAME:
                self.stage_volume = None
            else:
                self.volume = None
            return _Frame([])
        if upper.startswith("INSERT INTO"):
            assert MANIFEST_TABLE in self._identifiers(query)
            assert OBJECT_MANIFEST_VERSION in query
            assert OBJECT_CONTRACT_SHA256 in query
            assert BASE_OBSERVABILITY_CONTRACT_SHA256 in query
            assert str(_BINDING.observed_job_id) in query
            assert str(_BINDING.collector_job_id) in query
            self.manifest_rows.append(_manifest_row(catalog=self.catalog, schema=self.schema_name))
            return _Frame([])
        raise AssertionError(f"unexpected SQL: {query}")

    def table(self, table_name: str) -> _Table:
        name = self._identifiers(table_name)[-1]
        fields = self.relations[name].fields
        return _Table(_Schema([_Field(column, _DataType(kind)) for column, kind in fields]))


def _install_exact(spark: _Spark | None = None) -> _Spark:
    installed = spark or _Spark()
    bootstrap_objects(
        installed,
        catalog=installed.catalog,
        schema=installed.schema_name,
        binding=_BINDING,
    )
    installed.statements.clear()
    return installed


def _assert_error(spark: _Spark, code: str) -> None:
    with pytest.raises(RuntimeError, match=code):
        bootstrap_objects(
            spark,
            catalog=spark.catalog,
            schema=spark.schema_name,
            binding=_BINDING,
        )


def _grant_row(
    *, principal: str, action_type: str, object_type: str, object_key: str
) -> dict[str, str]:
    return {
        "principal": principal,
        "actionType": action_type,
        "objectType": object_type,
        "objectKey": object_key,
    }


def test_fresh_bootstrap_creates_only_fixed_attested_objects() -> None:
    spark = _Spark(catalog="catalog-with-hyphen", schema_name="observability")
    result = bootstrap_objects(
        spark,
        catalog="catalog-with-hyphen",
        schema="observability",
        binding=_BINDING,
        raw_volume_name=RAW_VOLUME_NAME,
    )

    assert result.manifest_version == OBJECT_MANIFEST_VERSION
    assert result.object_owner == "installer-owner"
    assert len(result.verified_objects) == 7
    assert result.raw_volume.endswith(".`dbtobsb_raw`")
    assert result.stage_volume.endswith(".`dbtobsb_stage`")
    rendered = "\n".join(spark.statements).upper()
    assert "CREATE SCHEMA" not in rendered
    assert rendered.count("CREATE TABLE ") == 4
    assert rendered.count("CREATE VIEW ") == 3
    assert rendered.count("CREATE VOLUME ") == 2
    assert rendered.count("INSERT INTO ") == 1
    assert "IF NOT EXISTS" not in rendered
    assert "CREATE OR REPLACE" not in rendered
    assert rendered.count("USING (WORKSPACE_ID, DBT_TASK_RUN_ID, NORMALIZED_DIGEST)") == 1
    assert "ON R.WORKSPACE_ID = I.WORKSPACE_ID" in rendered
    assert "AND R.DBT_TASK_RUN_ID = I.DBT_TASK_RUN_ID" in rendered
    assert "AND R.NORMALIZED_DIGEST = I.NORMALIZED_DIGEST" in rendered
    create_statements = [
        statement for statement in spark.statements if statement.startswith("CREATE")
    ]
    assert f"`{MANIFEST_TABLE}`" in create_statements[-1]
    assert OBJECT_CONTRACT_SHA256 in rendered.lower()
    assert spark.manifest_rows == [
        _manifest_row(catalog="catalog-with-hyphen", schema="observability")
    ]


def test_exact_v1_rerun_is_idempotent_and_ddl_free() -> None:
    spark = _install_exact()

    result = bootstrap_objects(spark, catalog="c", schema="s", binding=_BINDING)

    assert result.object_owner == "installer-owner"
    assert not any(
        statement.lstrip().upper().startswith("CREATE") for statement in spark.statements
    )


def test_delete_uninstall_removes_exact_objects_and_preserves_schema() -> None:
    spark = _install_exact()

    result = delete_installation_objects(spark, catalog="c", schema="s")

    assert result.deleted_object_count == 9
    assert result.schema_owner == "installer-owner"
    assert spark.schema_exists
    assert spark.relations == {}
    assert spark.volume is None
    assert spark.stage_volume is None
    assert spark.manifest_rows == []
    mutations = [
        statement for statement in spark.statements if statement.lstrip().upper().startswith("DROP")
    ]
    assert len(mutations) == 9
    assert mutations[-1].endswith(".`dbtobsb_object_manifest`")


def test_exact_rerun_rejects_installation_binding_drift() -> None:
    spark = _install_exact()
    changed = InstallationBinding(
        workspace_id=_BINDING.workspace_id,
        warehouse_id=_BINDING.warehouse_id,
        source_contract_sha256=_BINDING.source_contract_sha256,
        expected_runtime_policy_sha256=_BINDING.expected_runtime_policy_sha256,
        observed_job_id=_BINDING.observed_job_id + 1,
        collector_job_id=_BINDING.collector_job_id,
        reconciler_job_id=_BINDING.reconciler_job_id,
        observed_service_principal_name=_BINDING.observed_service_principal_name,
        collector_service_principal_name=_BINDING.collector_service_principal_name,
        job_manager_group_name=_BINDING.job_manager_group_name,
        collector_environment_sha256=_BINDING.collector_environment_sha256,
    )

    with pytest.raises(RuntimeError, match="DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH"):
        bootstrap_objects(spark, catalog="c", schema="s", binding=changed)

    assert not any(
        statement.lstrip().upper().startswith(("CREATE", "INSERT", "UPDATE", "MERGE"))
        for statement in spark.statements
    )


@pytest.mark.parametrize(
    "binding",
    [
        replace(_BINDING, workspace_id=0),
        replace(_BINDING, warehouse_id="not-a-warehouse"),
        replace(_BINDING, source_contract_sha256="invalid"),
        replace(_BINDING, expected_runtime_policy_sha256="invalid"),
        replace(_BINDING, observed_job_id=0),
        replace(_BINDING, reconciler_job_id=0),
        replace(
            _BINDING,
            observed_service_principal_name="same",
            collector_service_principal_name="same",
        ),
        replace(_BINDING, collector_environment_sha256="invalid"),
    ],
)
def test_invalid_installation_binding_is_rejected_before_sql(
    binding: InstallationBinding,
) -> None:
    spark = _Spark()

    with pytest.raises(ValueError, match=r"DBTOBSB_BOOTSTRAP_.*_BINDING_INVALID"):
        bootstrap_objects(spark, catalog="c", schema="s", binding=binding)

    assert spark.statements == []


def test_partial_install_is_rejected_before_any_ddl() -> None:
    spark = _Spark()
    spark.relations[REGISTRY_TABLE] = _Relation(
        fields=REGISTRY_FIELDS,
        object_type="MANAGED",
        provider="delta",
        properties={},
    )

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL")

    assert not any(
        statement.lstrip().upper().startswith("CREATE") for statement in spark.statements
    )


@pytest.mark.parametrize("legacy_name", ["runtime_trust_ledger", "runtime_trust_status_v"])
def test_legacy_runtime_trust_object_is_rejected_before_any_ddl(legacy_name: str) -> None:
    spark = _Spark()
    spark.relations[legacy_name] = _Relation(
        fields=(("legacy", "string"),),
        object_type="VIEW" if legacy_name.endswith("_v") else "MANAGED",
        provider=None if legacy_name.endswith("_v") else "delta",
        properties={},
    )

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_UNSUPPORTED_SCHEMA_STATE")

    assert not any(
        statement.lstrip().upper().startswith(("CREATE", "INSERT", "UPDATE", "MERGE"))
        for statement in spark.statements
    )


def test_wrong_relation_type_is_rejected() -> None:
    spark = _install_exact()
    spark.relations[REGISTRY_TABLE].object_type = "VIEW"
    spark.relations[REGISTRY_TABLE].provider = None

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_KIND_MISMATCH")


def test_wrong_table_provider_is_rejected() -> None:
    spark = _install_exact()
    spark.relations[REGISTRY_TABLE].provider = "parquet"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_PROVIDER_MISMATCH")


def test_wrong_view_definition_is_rejected() -> None:
    spark = _install_exact()
    view = spark.relations[RUN_HEALTH_VIEW]
    assert view.view_text is not None
    view.view_text = view.view_text.replace("r.normalized_digest = i.normalized_digest", "TRUE")

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_VIEW_DEFINITION_MISMATCH")


def test_wrong_manifest_version_marker_is_rejected() -> None:
    spark = _install_exact()
    spark.relations[MANIFEST_TABLE].properties["dbtobsb.object_manifest_version"] = "foreign"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH")


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [
            {
                **_manifest_row(),
                "manifest_version": "foreign",
            }
        ],
        [
            {
                **_manifest_row(),
                "base_observability_contract_sha256": "0" * 64,
            }
        ],
        [
            {
                **_manifest_row(),
            },
            {
                **_manifest_row(),
            },
        ],
    ],
)
def test_manifest_table_requires_one_exact_row(rows: list[dict[str, str | int]]) -> None:
    spark = _install_exact()
    spark.manifest_rows = rows

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")


def test_copied_manifest_is_rejected_in_another_schema_before_any_dml() -> None:
    spark = _install_exact()
    spark.schema_name = "copied"
    statement_count = len(spark.statements)

    with pytest.raises(RuntimeError, match="DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH"):
        bootstrap_objects(spark, catalog="c", schema="copied", binding=_BINDING)

    later = spark.statements[statement_count:]
    assert not any(
        statement.lstrip().upper().startswith(("INSERT", "UPDATE", "MERGE", "DELETE"))
        for statement in later
    )


def test_contract_digest_commits_to_view_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    original = bootstrap_module._object_contract_sha256()
    original_run_view_query = bootstrap_module._run_view_query

    def changed_run_view_query(registry: str, invocations: str) -> str:
        return original_run_view_query(registry, invocations).replace("LEFT JOIN", "INNER JOIN")

    monkeypatch.setattr(bootstrap_module, "_run_view_query", changed_run_view_query)

    assert bootstrap_module._object_contract_sha256() != original


def test_base_observability_contract_is_distinct_and_domain_bound() -> None:
    contract = {
        "domain": "dbtobsb.base-observability-contract.v1",
        "component_key": "BASE_OBSERVABILITY",
        "object_contract_sha256": OBJECT_CONTRACT_SHA256,
    }
    rendered = json.dumps(contract, separators=(",", ":"), sort_keys=True).encode()

    assert hashlib.sha256(rendered).hexdigest() == BASE_OBSERVABILITY_CONTRACT_SHA256
    assert BASE_OBSERVABILITY_CONTRACT_SHA256 not in {
        OBJECT_CONTRACT_SHA256,
        _BINDING.source_contract_sha256,
        _BINDING.expected_runtime_policy_sha256,
    }


def test_base_observability_contract_commits_to_object_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = bootstrap_module._base_observability_contract_sha256()

    monkeypatch.setattr(bootstrap_module, "OBJECT_CONTRACT_SHA256", "0" * 64)

    assert bootstrap_module._base_observability_contract_sha256() != original


def test_sql_contract_and_attestation_preserve_quoted_literal_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_digest = bootstrap_module._object_contract_sha256()
    original_query = bootstrap_module._run_view_query("registry", "invocations")
    original_run_view_query = bootstrap_module._run_view_query

    def changed_run_view_query(registry: str, invocations: str) -> str:
        return original_run_view_query(registry, invocations).replace("'PUBLISHED'", "'published'")

    monkeypatch.setattr(bootstrap_module, "_run_view_query", changed_run_view_query)

    assert bootstrap_module._object_contract_sha256() != original_digest
    assert bootstrap_module._normalize_sql(original_query) != bootstrap_module._normalize_sql(
        changed_run_view_query("registry", "invocations")
    )


def test_same_shape_foreign_objects_are_not_adopted() -> None:
    spark = _install_exact()
    for relation in spark.relations.values():
        relation.properties.clear()
    assert spark.volume is not None
    spark.volume["comment"] = "foreign same-shape volume"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH")


def test_wrong_table_schema_is_rejected() -> None:
    spark = _install_exact()
    spark.relations[REGISTRY_TABLE].fields = REGISTRY_FIELDS[:-1]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_SCHEMA_MISMATCH")


def test_inconsistent_owner_is_rejected() -> None:
    spark = _install_exact()
    spark.relations[REGISTRY_TABLE].owner = "foreign-owner"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH")


def test_session_actor_must_exactly_match_schema_owner_before_any_ddl() -> None:
    spark = _Spark(schema_owner="customer-schema-owner")

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH")

    assert spark.statements[0] == "SELECT session_user() AS session_user"
    assert not any(
        statement.lstrip().upper().startswith("CREATE") for statement in spark.statements
    )


def test_session_actor_match_is_case_sensitive() -> None:
    spark = _Spark(owner="Installer-Owner", schema_owner="installer-owner")

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH")

    assert not any(
        statement.lstrip().upper().startswith("CREATE") for statement in spark.statements
    )


def test_object_owner_must_match_the_preflighted_schema_owner() -> None:
    spark = _install_exact()
    spark.relations[REGISTRY_TABLE].owner = "customer-schema-owner"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH")


def test_native_table_show_grants_direct_shape_is_rejected() -> None:
    spark = _install_exact()
    spark.grant_rows[("TABLE", REGISTRY_TABLE)] = [
        _grant_row(
            principal="foreign-principal",
            action_type="SELECT",
            object_type="TABLE",
            object_key=f"{spark.catalog}.{spark.schema_name}.{REGISTRY_TABLE}",
        )
    ]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT")


def test_native_view_show_grants_direct_shape_is_rejected() -> None:
    spark = _install_exact()
    spark.grant_rows[("VIEW", RUN_HEALTH_VIEW)] = [
        _grant_row(
            principal="foreign-principal",
            action_type="SELECT",
            object_type="VIEW",
            object_key=f"{spark.catalog}.{spark.schema_name}.{RUN_HEALTH_VIEW}",
        )
    ]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT")


def test_native_volume_show_grants_direct_shape_is_rejected() -> None:
    spark = _install_exact()
    spark.grant_rows[("VOLUME", RAW_VOLUME_NAME)] = [
        _grant_row(
            principal="foreign-principal",
            action_type="READ VOLUME",
            object_type="VOLUME",
            object_key=f"{spark.catalog}.{spark.schema_name}.{RAW_VOLUME_NAME}",
        )
    ]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT")


def test_native_show_grants_exact_schema_and_catalog_ancestors_are_allowed() -> None:
    spark = _install_exact()
    inherited = [
        _grant_row(
            principal="account users",
            action_type="USE CATALOG",
            object_type="CATALOG",
            object_key=spark.catalog,
        ),
        _grant_row(
            principal="data-engineers",
            action_type="SELECT",
            object_type="SCHEMA",
            object_key=f"{spark.catalog}.{spark.schema_name}",
        ),
    ]
    spark.grant_rows[("TABLE", REGISTRY_TABLE)] = inherited
    spark.grant_rows[("VIEW", RUN_HEALTH_VIEW)] = inherited
    spark.grant_rows[("VOLUME", RAW_VOLUME_NAME)] = inherited

    result = bootstrap_objects(
        spark, catalog=spark.catalog, schema=spark.schema_name, binding=_BINDING
    )

    assert result.object_owner == "installer-owner"


@pytest.mark.parametrize(
    "row",
    [
        {
            "principal": "foreign-principal",
            "actionType": "SELECT",
            "objectType": "TABLE",
        },
        _grant_row(
            principal="foreign-principal",
            action_type="SELECT",
            object_type="TABLE",
            object_key="c.s.unrelated_table",
        ),
        _grant_row(
            principal="foreign-principal",
            action_type="SELECT",
            object_type="SCHEMA",
            object_key="c.unrelated_schema",
        ),
    ],
)
def test_malformed_or_ambiguous_show_grants_rows_fail_closed(row: dict[str, str]) -> None:
    spark = _install_exact()
    spark.grant_rows[("TABLE", REGISTRY_TABLE)] = [row]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID")


def test_duplicate_show_grants_rows_fail_closed() -> None:
    spark = _install_exact()
    row = _grant_row(
        principal="data-engineers",
        action_type="SELECT",
        object_type="SCHEMA",
        object_key=f"{spark.catalog}.{spark.schema_name}",
    )
    spark.grant_rows[("TABLE", REGISTRY_TABLE)] = [row, row]

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID")


def test_every_reserved_object_uses_native_show_grants() -> None:
    spark = _install_exact()

    bootstrap_objects(spark, catalog=spark.catalog, schema=spark.schema_name, binding=_BINDING)

    show_grants = [statement for statement in spark.statements if statement.startswith("SHOW")]
    assert len(show_grants) == 9
    assert any(f"SHOW GRANTS ON TABLE `c`.`s`.`{REGISTRY_TABLE}`" == sql for sql in show_grants)
    assert any(f"SHOW GRANTS ON VIEW `c`.`s`.`{RUN_HEALTH_VIEW}`" == sql for sql in show_grants)
    assert any(f"SHOW GRANTS ON VOLUME `c`.`s`.`{RAW_VOLUME_NAME}`" == sql for sql in show_grants)
    assert "TABLE_PRIVILEGES" not in "\n".join(spark.statements).upper()


def test_later_object_owner_check_remains_exact() -> None:
    spark = _install_exact()
    spark.schema_owner = "customer-schema-owner"
    spark.session_actor = "customer-schema-owner"

    _assert_error(spark, "DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH")


def test_target_schema_must_already_exist() -> None:
    _assert_error(
        _Spark(schema_exists=False),
        "DBTOBSB_BOOTSTRAP_TARGET_SCHEMA_NOT_FOUND",
    )


def test_arbitrary_volume_name_is_rejected_before_sql() -> None:
    spark = _Spark()

    with pytest.raises(ValueError, match="DBTOBSB_BOOTSTRAP_FIXED_OBJECT_NAME_REQUIRED"):
        bootstrap_objects(
            spark,
            catalog="c",
            schema="s",
            binding=_BINDING,
            raw_volume_name="customer_chosen",
        )

    assert spark.statements == []


def test_runtime_entrypoint_has_no_bootstrap_mode_parameter() -> None:
    code_names = set(collect.__code__.co_names)

    assert "mode" not in code_names
    assert "bootstrap_objects" not in code_names
