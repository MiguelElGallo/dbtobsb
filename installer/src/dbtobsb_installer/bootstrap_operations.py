"""Production closed-operation registry entries for the v1 evidence bootstrap."""

from __future__ import annotations

import re

from dbtobsb_collector import bootstrap as contract
from dbtobsb_collector.bootstrap import InstallationBinding
from dbtobsb_collector.naming import qualify

from dbtobsb_installer.operations import ClosedMutationOperation, _registered_mutation

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")

_TABLE_OPERATIONS = {
    contract.REGISTRY_TABLE: "bootstrap_create_artifact_registry_table_v1",
    contract.INVOCATIONS_TABLE: "bootstrap_create_invocations_table_v1",
    contract.NODE_RESULTS_TABLE: "bootstrap_create_node_results_table_v1",
}
_VIEW_OPERATIONS = {
    contract.RUN_HEALTH_VIEW: "bootstrap_create_run_health_view_v1",
    contract.NODE_HEALTH_VIEW: "bootstrap_create_node_health_view_v1",
    contract.COLLECTION_HEALTH_VIEW: "bootstrap_create_collection_health_view_v1",
}


def _base_parameters(catalog: str, schema: str) -> tuple[tuple[str, str], ...]:
    if _IDENTIFIER.fullmatch(catalog) is None or _IDENTIFIER.fullmatch(schema) is None:
        raise ValueError("DBTOBSB_INSTALLER_BOOTSTRAP_IDENTIFIER_UNSUPPORTED")
    return (("catalog", catalog), ("schema", schema))


def render_bootstrap_mutations(
    *,
    catalog: str,
    schema: str,
    binding: InstallationBinding,
) -> tuple[ClosedMutationOperation, ...]:
    """Render the exact ten fresh-install operations accepted by the native registry."""

    base_parameters = _base_parameters(catalog, schema)
    contract._validate_installation_binding(binding)
    operations: list[ClosedMutationOperation] = []
    for spec in contract._TABLE_SPECS:
        text = f"""CREATE TABLE {qualify(catalog, schema, spec.name)} (
  {contract._column_sql(spec.fields)}
) USING DELTA
TBLPROPERTIES (
  {contract._properties_sql(spec.name)}
)"""
        operations.append(
            _registered_mutation(
                native_operation=_TABLE_OPERATIONS[spec.name],
                native_parameters=base_parameters,
                text=text,
            )
        )
    volume = qualify(catalog, schema, contract.RAW_VOLUME_NAME)
    operations.append(
        _registered_mutation(
            native_operation="bootstrap_create_raw_volume_v1",
            native_parameters=base_parameters,
            text=(
                f"CREATE VOLUME {volume} COMMENT "
                f"{contract._sql_literal(contract._volume_comment())}"
            ),
        )
    )
    stage_volume = qualify(catalog, schema, contract.STAGE_VOLUME_NAME)
    operations.append(
        _registered_mutation(
            native_operation="bootstrap_create_stage_volume_v1",
            native_parameters=base_parameters,
            text=(
                f"CREATE VOLUME {stage_volume} COMMENT "
                f"{contract._sql_literal(contract._volume_comment('artifact_stage'))}"
            ),
        )
    )
    registry = qualify(catalog, schema, contract.REGISTRY_TABLE)
    invocations = qualify(catalog, schema, contract.INVOCATIONS_TABLE)
    nodes = qualify(catalog, schema, contract.NODE_RESULTS_TABLE)
    view_queries = {
        contract.RUN_HEALTH_VIEW: contract._run_view_query(registry, invocations),
        contract.NODE_HEALTH_VIEW: contract._node_view_query(registry, nodes),
        contract.COLLECTION_HEALTH_VIEW: contract._collection_health_query(registry),
    }
    for spec in contract._VIEW_SPECS:
        text = f"""CREATE VIEW {qualify(catalog, schema, spec.name)}
TBLPROPERTIES (
  {contract._properties_sql(spec.name)}
)
AS
{view_queries[spec.name]}"""
        operations.append(
            _registered_mutation(
                native_operation=_VIEW_OPERATIONS[spec.name],
                native_parameters=base_parameters,
                text=text,
            )
        )
    manifest = qualify(catalog, schema, contract.MANIFEST_TABLE)
    operations.append(
        _registered_mutation(
            native_operation="bootstrap_create_object_manifest_table_v1",
            native_parameters=base_parameters,
            text=f"""CREATE TABLE {manifest} (
  {contract._column_sql(contract.MANIFEST_FIELDS)}
) USING DELTA
TBLPROPERTIES (
  {contract._properties_sql("object_manifest")}
)""",
        )
    )
    expected = contract._expected_manifest_row(binding, catalog=catalog, schema=schema)
    columns = ", ".join(expected)
    values = ", ".join(contract._manifest_value_sql(value) for value in expected.values())
    insert_parameters = (
        tuple((key, str(value)) for key, value in expected.items()) + base_parameters
    )
    operations.append(
        _registered_mutation(
            native_operation="bootstrap_insert_object_manifest_v1",
            native_parameters=insert_parameters,
            text=f"INSERT INTO {manifest} ({columns})\nVALUES ({values})",
        )
    )
    if len(operations) != 10:
        raise RuntimeError("DBTOBSB_INSTALLER_BOOTSTRAP_REGISTRY_INCOMPLETE")
    return tuple(operations)


__all__ = ["render_bootstrap_mutations"]
