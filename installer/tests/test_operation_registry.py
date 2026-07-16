"""Cross-language contract tests for the fixed production bootstrap registry."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace
from importlib.resources import files
from typing import Any, cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dbtobsb_collector import bootstrap as collector_bootstrap
from dbtobsb_collector.bootstrap import InstallationBinding

from dbtobsb_installer.bootstrap_operations import render_bootstrap_mutations
from dbtobsb_installer.operations import (
    CleanupAction,
    CleanupPrivilege,
    Ed25519MarkerSigner,
    PreparationLocator,
    SecurableType,
    bind_mutation_marker,
    sign_preparation_marker,
)


def _vectors() -> dict[str, Any]:
    raw = (
        files("dbtobsb_contracts")
        .joinpath("bootstrap-operation-registry-v1-vectors.json")
        .read_bytes()
    )
    return cast(dict[str, Any], json.loads(raw))


def _binding(document: dict[str, Any]) -> InstallationBinding:
    binding = cast(dict[str, Any], document["binding"])
    assert isinstance(binding, dict)
    return InstallationBinding(**binding)


def test_python_bootstrap_registry_matches_the_packaged_native_vectors() -> None:
    vectors = _vectors()
    catalog = vectors["catalog"]
    schema = vectors["schema"]
    marker_token = vectors["marker_token"]
    assert isinstance(catalog, str) and isinstance(schema, str) and isinstance(marker_token, str)
    operations = render_bootstrap_mutations(
        catalog=catalog,
        schema=schema,
        binding=_binding(vectors),
    )
    observed: list[dict[str, object]] = []
    for operation in operations:
        descriptor = operation._base_statement._native_transport()
        parameters = cast(dict[str, str], descriptor["parameters"])
        assert isinstance(parameters, dict)
        parameters["marker_token"] = marker_token
        observed.append(descriptor)

    assert len(operations) == 10
    assert observed == vectors["operations"]
    assert len({operation.statement_sha256 for operation in operations}) == 10
    assert all(
        "bootstrap_" in operation._base_statement._native_operation for operation in operations
    )
    assert "observed principal''s runtime" in operations[-1]._base_statement._transport_text()


def test_registry_covers_every_current_collector_bootstrap_mutation_in_order() -> None:
    class RecordingSpark:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def sql(self, query: str) -> None:
            self.statements.append(query)

        def table(self, table_name: str) -> None:
            raise AssertionError(f"unexpected table read: {table_name}")

    vectors = _vectors()
    binding = _binding(vectors)
    spark = RecordingSpark()
    collector_bootstrap._create_fresh_objects(
        spark,
        catalog=str(vectors["catalog"]),
        schema=str(vectors["schema"]),
        binding=binding,
    )
    registry = render_bootstrap_mutations(
        catalog=str(vectors["catalog"]),
        schema=str(vectors["schema"]),
        binding=binding,
    )

    assert spark.statements == [item._base_statement._transport_text() for item in registry]


def test_every_bootstrap_operation_binds_one_signed_recovery_marker() -> None:
    vectors = _vectors()
    operations = render_bootstrap_mutations(
        catalog=str(vectors["catalog"]),
        schema=str(vectors["schema"]),
        binding=_binding(vectors),
    )
    signer = Ed25519MarkerSigner(Ed25519PrivateKey.generate())
    for sequence, operation in enumerate(operations, start=1):
        locator = PreparationLocator(
            installation_id="a" * 64,
            generation=1,
            sequence=sequence,
            operation_uuid=uuid.uuid4(),
            envelope_sha256="b" * 64,
            statement_sha256=operation.statement_sha256,
            operator_group="dbtobsb migration operators",
            warehouse_id="0123456789abcdef",
            securable_type=SecurableType.SCHEMA,
            securable_name="observability.dbtobsb",
            privilege=CleanupPrivilege.MODIFY,
            action=CleanupAction.RECONSTRUCT_FIXED_DATA_CHANGE,
        )
        marker = sign_preparation_marker(locator, signer)
        statement = bind_mutation_marker(operation, marker, signer.verifier())
        descriptor = statement._native_transport()
        assert descriptor["semantic_sha256"] == operation.statement_sha256
        parameters = cast(dict[str, str], descriptor["parameters"])
        assert parameters["marker_token"] == marker.compact_token
        assert "DBTOBSB_MUTATION_MARKER_V1" in statement._transport_text()


@pytest.mark.parametrize(
    ("catalog", "schema"),
    (
        ("contains-hyphen", "dbtobsb"),
        ("observability", "contains space"),
        ("observability", "x' OR 1=1 --"),
        ("1invalid", "dbtobsb"),
    ),
)
def test_unsupported_or_hostile_identifiers_fail_before_render(
    catalog: str,
    schema: str,
) -> None:
    vectors = _vectors()
    with pytest.raises(ValueError, match="BOOTSTRAP_IDENTIFIER_UNSUPPORTED"):
        render_bootstrap_mutations(
            catalog=catalog,
            schema=schema,
            binding=_binding(vectors),
        )


def test_binding_drift_changes_the_manifest_operation_only() -> None:
    vectors = _vectors()
    binding = _binding(vectors)
    original = render_bootstrap_mutations(
        catalog=str(vectors["catalog"]),
        schema=str(vectors["schema"]),
        binding=binding,
    )
    changed = render_bootstrap_mutations(
        catalog=str(vectors["catalog"]),
        schema=str(vectors["schema"]),
        binding=replace(binding, observed_job_id=binding.observed_job_id + 1),
    )

    assert [item.statement_sha256 for item in original[:-1]] == [
        item.statement_sha256 for item in changed[:-1]
    ]
    assert original[-1].statement_sha256 != changed[-1].statement_sha256
