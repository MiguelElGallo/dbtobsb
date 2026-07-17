from __future__ import annotations

import copy
import importlib.util
import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from dbtobsb_contracts import (
    RUNTIME_TRUST_PROVIDER_CONTRACT_SHA256,
)

from dbtobsb_installer import runtime_trust


def _h(character: str) -> str:
    return character * 64


def _load_semantic_vectors() -> dict[str, Any]:
    vector_path = Path(__file__).with_name("runtime_trust_vectors") / "vectors-v1.json"
    return cast(dict[str, Any], json.loads(vector_path.read_text(encoding="utf-8")))


def _load_vector_generator() -> Any:
    generator_path = Path(__file__).with_name("runtime_trust_vectors") / "generate.py"
    spec = importlib.util.spec_from_file_location("_runtime_trust_vector_generator", generator_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _chain() -> tuple[
    runtime_trust.ManifestRegistered,
    runtime_trust.TrustCandidate,
    runtime_trust.SnapshotAccepted,
]:
    expected = (
        runtime_trust.ExpectedComponent(
            runtime_trust.ComponentKey.BASE_OBSERVABILITY,
            _h("1"),
        ),
    )
    component = runtime_trust.ComponentObservation(
        component_key=runtime_trust.ComponentKey.BASE_OBSERVABILITY,
        contract_digest=_h("1"),
        runtime_resource_digest=_h("2"),
        runtime_principal_digest=_h("3"),
        binding_digest=_h("4"),
        dml_allowlist_digest=_h("5"),
        authority_digest=_h("6"),
    )
    observed = (component.observed_component(),)
    identity = runtime_trust.CommonIdentity(
        installation_digest=_h("a"),
        workspace_digest=_h("b"),
        account_digest=_h("c"),
        manifest_digest=_h("d"),
        generation=1,
    )
    registration = runtime_trust.ManifestRegistered(
        identity=identity,
        reason=runtime_trust.RegistrationReason.INSTALL,
        expected_components=expected,
    )
    before = runtime_trust.DeploymentSet(
        account_digest=identity.account_digest,
        workspace_digest=identity.workspace_digest,
        app_digest=_h("e"),
        deployments=(),
    )
    selected = runtime_trust.DeploymentRecord(
        deployment_id="0123456789abcdef0123456789abcdef",
        status=runtime_trust.DeploymentStatus.SUCCEEDED,
        mode=runtime_trust.DeploymentMode.SNAPSHOT,
        source_digest=_h("7"),
        artifact_digest=_h("8"),
        configuration_digest=_h("9"),
    )
    after = runtime_trust.DeploymentSet(
        account_digest=identity.account_digest,
        workspace_digest=identity.workspace_digest,
        app_digest=_h("e"),
        deployments=(selected,),
    )
    graph = runtime_trust.RuntimeGraph(
        identity=identity,
        app_digest=_h("e"),
        deployment_id=selected.deployment_id,
        deployment_mode=runtime_trust.DeploymentMode.SNAPSHOT,
        deployment_set_after_digest=after.digest,
        direct_plan_digest=_h("f"),
        direct_lineage_digest=_h("0"),
        direct_state_serial=9_223_372_036_854_775_807,
        resource_selection_digest=_h("1"),
        source_digest=selected.source_digest or "",
        build_digest=_h("2"),
        artifact_digest=selected.artifact_digest or "",
        configuration_digest=selected.configuration_digest or "",
        app_resource_digest=_h("3"),
        acl_digest=_h("4"),
        job_run_as_digest=_h("5"),
        uc_grant_digest=_h("6"),
        group_root_digest=_h("7"),
        service_principal_set_digest=_h("8"),
        expected_roster_digest=_h("9"),
        observed_roster_digest=_h("9"),
        expected_components=expected,
        observed_components=observed,
    )
    pre_start = runtime_trust.MachineObservation(
        phase=runtime_trust.ObservationPhase.PRE_START,
        identity=identity,
        deployment_id=selected.deployment_id,
        deployment_mode=runtime_trust.DeploymentMode.SNAPSHOT,
        deployment_set_after_digest=after.digest,
        stable_graph_digest=graph.stable_graph_digest,
        lifecycle_state=runtime_trust.LifecycleState.STOPPED,
        active_deployment_id=selected.deployment_id,
        pending_deployment_count=0,
        machine_observer_fingerprint=_h("b"),
    )
    roster = runtime_trust.RosterObservation(
        identity=identity,
        service_principal_set_digest=graph.service_principal_set_digest,
        expected_roster_digest=graph.expected_roster_digest,
        observed_roster_digest=graph.observed_roster_digest,
        roster_reviewer_fingerprint=_h("c"),
        expected_components=expected,
        observed_components=observed,
    )
    evidence = runtime_trust.CandidateEvidence(
        deployment_set_before=before,
        deployment_set_after=after,
        graph=graph,
        pre_start=pre_start,
        roster=roster,
    )
    candidate = runtime_trust.TrustCandidate(registration=registration, evidence=evidence)
    post_start = runtime_trust.MachineObservation(
        phase=runtime_trust.ObservationPhase.POST_START,
        identity=identity,
        deployment_id=selected.deployment_id,
        deployment_mode=runtime_trust.DeploymentMode.SNAPSHOT,
        deployment_set_after_digest=after.digest,
        stable_graph_digest=graph.stable_graph_digest,
        lifecycle_state=runtime_trust.LifecycleState.ACTIVE,
        active_deployment_id=selected.deployment_id,
        pending_deployment_count=0,
        machine_observer_fingerprint=pre_start.machine_observer_fingerprint,
    )
    acceptance = runtime_trust.SnapshotAccepted(
        candidate=candidate,
        post_start=post_start,
    )
    return registration, candidate, acceptance


def _readback(
    event: runtime_trust.RuntimeTrustEvent,
    *,
    statement_evaluated_at: datetime | None = None,
    candidate_statement_evaluated_at: datetime | None = None,
    roster_statement_evaluated_at: datetime | None = None,
) -> runtime_trust.RuntimeTrustReadback:
    at = statement_evaluated_at or datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=UTC)
    record = runtime_trust.derive_event_record(
        event,
        statement_evaluated_at=at,
        candidate_statement_evaluated_at=candidate_statement_evaluated_at,
        roster_statement_evaluated_at=roster_statement_evaluated_at,
    )
    return runtime_trust.RuntimeTrustReadback(
        physical_row_count=1,
        event_id=record.event_id,
        payload_digest=record.payload_digest,
        server_record_digest=record.server_record_digest,
        ledger_row_id=record.ledger_row_id,
        snapshot_id=record.snapshot_id,
        statement_evaluated_at=record.statement_evaluated_at,
        valid_until=record.valid_until,
        distinct_payload_count=1,
        distinct_server_record_count=1,
        distinct_ledger_row_count=1,
    )


def _invalidation() -> runtime_trust.SnapshotInvalidated:
    registration, candidate, _ = _chain()
    return runtime_trust.SnapshotInvalidated(
        identity=registration.identity,
        reason=runtime_trust.InvalidationReason.OPERATOR_ABORTED,
        expected_components=registration.expected_components,
        predecessor_event_id=candidate.event_id,
        target_event_id=candidate.event_id,
    )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "1",
        "2147483647",
        "9007199254740991",
        "9007199254740992",
        "9007199254740993",
        "9223372036854775807",
    ],
)
def test_decimal_codec_accepts_exact_quoted_boundaries(value: str) -> None:
    assert runtime_trust.parse_canonical_decimal(value) == int(value)


@pytest.mark.parametrize(
    "value",
    [
        -1,
        1,
        None,
        "-1",
        "+1",
        "01",
        "1.0",
        "1e0",
        "",
        " 1",
        "1 ",
        "١",  # noqa: RUF001 - intentional Unicode-digit rejection vector
        "9223372036854775808",
    ],
)
def test_decimal_codec_rejects_coercion_and_noncanonical_values(value: object) -> None:
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_DECIMAL_INVALID",
    ):
        runtime_trust.parse_canonical_decimal(value)


def test_rfc8785_restricted_vector_freezes_bytes_and_digest() -> None:
    data = {
        "nullable": None,
        "generation": "9007199254740993",
        "component": "BASE_OBSERVABILITY",
    }
    encoded = runtime_trust._canonical_object(runtime_trust._Domain.EVENT_ID, data)
    assert encoded == (
        b'{"data":{"component":"BASE_OBSERVABILITY","generation":"9007199254740993",'
        b'"nullable":null},"domain":"dbtobsb.runtime-trust.event-id.v1"}'
    )
    assert runtime_trust._digest(runtime_trust._Domain.EVENT_ID, data) == (
        "13d64c4b1f9a4460ef17aa2241d99c5754557139a268d2fc9fbc2a03e79ecf20"
    )


@pytest.mark.parametrize("value", [{"n": 1}, {"n": True}, {"n": "å"}])
def test_canonical_codec_rejects_numbers_booleans_and_unicode(value: dict[str, object]) -> None:
    with pytest.raises(runtime_trust.RuntimeTrustContractError):
        runtime_trust._canonical_object(runtime_trust._Domain.EVENT_ID, value)


def test_python_reference_verifies_full_typed_semantic_golden_contract() -> None:
    vectors = _load_semantic_vectors()
    generator = _load_vector_generator()
    generator.validate_contract_document(vectors)
    assert vectors["contract_version"] == "dbtobsb.runtime-trust.semantic-golden-v1"
    assert vectors["domain_count"] == len(runtime_trust._Domain) == 12
    assert [vector["domain"] for vector in vectors["domains"]] == [
        domain.value for domain in runtime_trust._Domain
    ]
    by_domain = {vector["domain"]: vector["data"] for vector in vectors["domains"]}
    assert (
        by_domain[runtime_trust._Domain.STABLE_GRAPH.value]["direct_state_serial"]
        == "9223372036854775807"
    )
    assert by_domain[runtime_trust._Domain.PAYLOAD.value]["prior_generation"] is None
    assert isinstance(
        by_domain[runtime_trust._Domain.ROSTER_OBSERVATION.value]["observed_components"],
        list,
    )
    assert (
        by_domain[runtime_trust._Domain.SERVER_RECORD.value]["statement_evaluated_at"]
        == "2026-07-16T10:05:00.654321Z"
    )
    assert len(vectors["sql"]) == 10


def test_python_reference_executes_the_shared_product_plan_matrix() -> None:
    vectors = _load_semantic_vectors()
    assert vectors["decimal_valid"] == [
        "0",
        "1",
        "2147483647",
        "9007199254740991",
        "9007199254740992",
        "9007199254740993",
        "9223372036854775807",
    ]
    for value in vectors["decimal_valid"]:
        runtime_trust.parse_canonical_decimal(value)
    assert [case["name"] for case in vectors["decimal_invalid"]] == [
        "negative",
        "leading-zero",
        "plus-sign",
        "fractional",
        "exponent",
        "empty",
        "leading-whitespace",
        "trailing-whitespace",
        "unicode-digit",
        "json-number",
        "null-required",
        "overflow",
    ]
    for case in vectors["decimal_invalid"]:
        with pytest.raises(runtime_trust.RuntimeTrustContractError):
            runtime_trust.parse_canonical_decimal(case["value"])
    for case in vectors["canonical_invalid"]:
        with pytest.raises(runtime_trust.RuntimeTrustContractError):
            runtime_trust._canonical_object(runtime_trust._Domain.EVENT_ID, case["value"])
    for value in vectors["timestamp_valid"]:
        runtime_trust.parse_canonical_timestamp(value)
    for case in vectors["timestamp_invalid"]:
        with pytest.raises(runtime_trust.RuntimeTrustContractError):
            runtime_trust.parse_canonical_timestamp(case["value"])

    assert Counter(case["category"] for case in vectors["semantic_invalid"]) == Counter(
        {
            "missing_field": 1,
            "extra_field": 1,
            "wrong_nested_field": 1,
            "wrong_enum": 1,
            "array_order": 2,
            "duplicate": 2,
        }
    )
    conflict = vectors["event_conflicts"][0]
    assert conflict["original"]["event_id"] == conflict["changed"]["event_id"]
    for variant in (conflict["original"], conflict["changed"]):
        data = variant["data"]
        assert runtime_trust._canonical_object(runtime_trust._Domain.PAYLOAD, data) == variant[
            "canonical"
        ].encode("ascii")
        assert runtime_trust._digest(runtime_trust._Domain.PAYLOAD, data) == variant["sha256"]
    assert conflict["original"]["sha256"] != conflict["changed"]["sha256"]

    separation = vectors["version_separation"][0]
    for version in (separation["v1"], separation["v2"]):
        data = version["data"]
        assert runtime_trust._canonical_object(runtime_trust._Domain.EVENT_ID, data) == version[
            "canonical"
        ].encode("ascii")
        assert runtime_trust._digest(runtime_trust._Domain.EVENT_ID, data) == version["sha256"]
    assert separation["v1"]["sha256"] != separation["v2"]["sha256"]


def test_python_semantic_reference_rejects_missing_extra_and_wrong_nested_fields() -> None:
    vectors = _load_semantic_vectors()
    generator = _load_vector_generator()
    malformed: list[dict[str, Any]] = []

    missing = copy.deepcopy(vectors)
    del missing["domains"][0]["data"]["app_digest"]
    malformed.append(missing)

    extra = copy.deepcopy(vectors)
    extra["domains"][5]["data"]["unbound_field"] = "must-reject"
    malformed.append(extra)

    wrong_nested = copy.deepcopy(vectors)
    observed = wrong_nested["domains"][2]["data"]["observed_components"][0]
    observed["observation"] = observed.pop("observation_digest")
    malformed.append(wrong_nested)

    wrong_enum = copy.deepcopy(vectors)
    wrong_enum["domains"][4]["data"]["phase"] = "BETWEEN_STARTS"
    malformed.append(wrong_enum)

    for document in malformed:
        with pytest.raises(
            generator.RuntimeTrustVectorError,
            match="DBTOBSB_RUNTIME_TRUST_VECTOR_SEMANTIC_MISMATCH",
        ):
            generator.validate_contract_document(document)


@pytest.mark.parametrize(
    ("catalog", "schema"),
    [
        ("catalog;DROP", "schema"),
        ("catalog", "schema.name"),
        ("catalog`", "schema"),
        ("catalog", "schema --"),
        ("catalog", "å"),
    ],
)
def test_object_names_reject_sql_and_identifier_injection(catalog: str, schema: str) -> None:
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_IDENTIFIER_INVALID",
    ):
        runtime_trust.RuntimeTrustObjectNames(catalog, schema)


def test_identifier_policy_is_exported_ascii_regular_identifier_v1() -> None:
    assert (
        runtime_trust.RUNTIME_TRUST_V1_IDENTIFIER_POLICY == "ASCII_REGULAR_IDENTIFIER_1_TO_128_V1"
    )
    assert (
        runtime_trust.RUNTIME_TRUST_V1_REGULAR_IDENTIFIER_PATTERN
        == r"^[A-Za-z_][A-Za-z0-9_]{0,127}$"
    )
    for value in ("a", "_", "A" + ("a" * 127)):
        names = runtime_trust.RuntimeTrustObjectNames(value, value)
        assert names.catalog == value
        assert names.schema == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1catalog",
        "a" * 129,
        "has-hyphen",
        "has space",
        'has"quote',
        "has`backtick",
        "å",
        "Ａ",  # noqa: RUF001 - intentional Unicode lookalike rejection vector
    ],
)
def test_identifier_policy_rejects_quoted_unicode_and_out_of_bounds(value: str) -> None:
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_IDENTIFIER_INVALID",
    ):
        runtime_trust.RuntimeTrustObjectNames(value, "schema")


def test_component_collection_is_sorted_unique_and_base_only() -> None:
    base = runtime_trust.ExpectedComponent(
        runtime_trust.ComponentKey.BASE_OBSERVABILITY,
        _h("1"),
    )
    optional = runtime_trust.ExpectedComponent(
        runtime_trust.ComponentKey.SYSTEM_ENRICHMENT,
        _h("2"),
    )
    with pytest.raises(runtime_trust.RuntimeTrustContractError):
        runtime_trust.ManifestRegistered(
            identity=_chain()[0].identity,
            reason=runtime_trust.RegistrationReason.INSTALL,
            expected_components=(base, optional),
        )
    with pytest.raises(runtime_trust.RuntimeTrustContractError):
        runtime_trust._expected_components((base, base))


def test_registration_reason_is_bound_to_first_or_later_generation() -> None:
    registration, _, _ = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_REGISTRATION_REASON_INVALID",
    ):
        replace(registration, reason=runtime_trust.RegistrationReason.UPGRADE)
    later_identity = replace(registration.identity, generation=2)
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_REGISTRATION_REASON_INVALID",
    ):
        runtime_trust.ManifestRegistered(
            identity=later_identity,
            reason=runtime_trust.RegistrationReason.INSTALL,
            expected_components=registration.expected_components,
            predecessor_event_id=_h("a"),
            prior_generation=1,
            prior_snapshot_id=_h("b"),
        )


def test_deployment_inventory_requires_ascii_order_and_unique_ids() -> None:
    _, candidate, _ = _chain()
    selected = candidate.evidence.deployment_set_after.deployments[0]
    duplicate = replace(selected)
    with pytest.raises(runtime_trust.RuntimeTrustContractError):
        runtime_trust.DeploymentSet(
            account_digest=candidate.registration.identity.account_digest,
            workspace_digest=candidate.registration.identity.workspace_digest,
            app_digest=candidate.evidence.graph.app_digest,
            deployments=(selected, duplicate),
        )


def test_candidate_rejects_pending_or_mismatched_selected_deployment() -> None:
    registration, candidate, _ = _chain()
    selected = candidate.evidence.deployment_set_after.deployments[0]
    pending = replace(selected, status=runtime_trust.DeploymentStatus.IN_PROGRESS)
    pending_after = replace(candidate.evidence.deployment_set_after, deployments=(pending,))
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_PENDING",
    ):
        pending_graph = replace(
            candidate.evidence.graph,
            deployment_set_after_digest=pending_after.digest,
        )
        runtime_trust.CandidateEvidence(
            deployment_set_before=candidate.evidence.deployment_set_before,
            deployment_set_after=pending_after,
            graph=pending_graph,
            pre_start=replace(
                candidate.evidence.pre_start,
                deployment_set_after_digest=pending_after.digest,
                stable_graph_digest=pending_graph.stable_graph_digest,
            ),
            roster=candidate.evidence.roster,
        )

    changed = replace(selected, source_digest=_h("f"))
    changed_after = replace(candidate.evidence.deployment_set_after, deployments=(changed,))
    changed_graph = replace(
        candidate.evidence.graph,
        deployment_set_after_digest=changed_after.digest,
    )
    changed_pre = replace(
        candidate.evidence.pre_start,
        deployment_set_after_digest=changed_after.digest,
        stable_graph_digest=changed_graph.stable_graph_digest,
    )
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_SELECTED_DEPLOYMENT_MISMATCH",
    ):
        runtime_trust.CandidateEvidence(
            deployment_set_before=candidate.evidence.deployment_set_before,
            deployment_set_after=changed_after,
            graph=changed_graph,
            pre_start=changed_pre,
            roster=candidate.evidence.roster,
        )

    assert registration.reason is runtime_trust.RegistrationReason.INSTALL


def test_roster_mismatch_and_nonrefresh_anchor_reuse_fail_closed() -> None:
    registration, candidate, _ = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_ROSTER_MISMATCH",
    ):
        replace(candidate.evidence.roster, observed_roster_digest=_h("a"))
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_ROSTER_REUSE_INVALID",
    ):
        runtime_trust.TrustCandidate(
            registration=registration,
            evidence=candidate.evidence,
            roster_anchor_event_id=_h("d"),
            roster_anchor_digest=candidate.evidence.roster.digest,
        )


def test_complete_chain_freezes_golden_ids_and_server_record() -> None:
    registration, candidate, acceptance = _chain()
    assert (
        registration.event_id == "47ac1e70b2f7dbd953514b349cdd3608f3358c9d47f57df76d3c15f3ea3970b9"
    )
    assert candidate.event_id == "200664aff064d47e96a52e4663533571fccbf93ce25312438909ffee7bfe36f0"
    assert candidate.candidate_digest == (
        "3fba0a1efea06b04e969a28c7c90135d422c820021c97c04b44656e2e3cc0116"
    )
    assert acceptance.event_id == "73825cb48859120dc8429a094e242d0c347e3f0aae0c1e7e4cd2239d5772564a"

    candidate_at = datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=UTC)
    roster_at = candidate_at
    accepted_at = datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=UTC)
    record = runtime_trust.derive_event_record(
        acceptance,
        statement_evaluated_at=accepted_at,
        candidate_statement_evaluated_at=candidate_at,
        roster_statement_evaluated_at=roster_at,
    )
    assert record.valid_until == roster_at + timedelta(hours=24)
    assert record.acceptance_digest == (
        "3279c0e6fd3b9914374f51eb9cee6c49aee117132db267220cfa89e93802696f"
    )
    assert record.payload_digest == (
        "a95cd64b7387192b3932a856fd9a80f13f6e72d4c54b248dc2ad909ac42759dc"
    )
    assert record.snapshot_id == (
        "17895d20d2c5175153a875fc410bb4e0c95a43532e18a0071164489bfd3acba0"
    )
    assert record.server_record_digest == (
        "47b0df9bd8451ccdd2bf230cce999267f321dbc6c08929cc194ef8ccffcc4e18"
    )
    assert record.ledger_row_id == (
        "e7f2dd18bf9e9ec1b9282290e00322994c921d970cb737e1a78e95679b96454c"
    )


def test_timestamp_rendering_is_timezone_independent() -> None:
    _, _, acceptance = _chain()
    east = timezone(timedelta(hours=3))
    accepted_at = datetime(2026, 7, 16, 13, 5, 0, 654321, tzinfo=east)
    candidate_at = datetime(2026, 7, 16, 13, 0, 0, 123456, tzinfo=east)
    local = runtime_trust.derive_event_record(
        acceptance,
        statement_evaluated_at=accepted_at,
        candidate_statement_evaluated_at=candidate_at,
        roster_statement_evaluated_at=candidate_at,
    )
    utc = runtime_trust.derive_event_record(
        acceptance,
        statement_evaluated_at=accepted_at.astimezone(UTC),
        candidate_statement_evaluated_at=candidate_at.astimezone(UTC),
        roster_statement_evaluated_at=candidate_at.astimezone(UTC),
    )
    assert local == utc


def test_acceptance_requires_both_server_predecessor_times() -> None:
    _, _, acceptance = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_TIME_REQUIRED",
    ):
        runtime_trust.derive_event_record(
            acceptance,
            statement_evaluated_at=datetime.now(UTC),
        )


def test_acceptance_rejects_reversed_server_chronology() -> None:
    _, _, acceptance = _chain()
    accepted_at = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_TIME_INVALID",
    ):
        runtime_trust.derive_event_record(
            acceptance,
            statement_evaluated_at=accepted_at,
            candidate_statement_evaluated_at=accepted_at + timedelta(seconds=1),
            roster_statement_evaluated_at=accepted_at,
        )


def test_server_times_reject_naive_client_datetime() -> None:
    registration, _, _ = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID",
    ):
        runtime_trust.derive_event_record(
            registration,
            statement_evaluated_at=datetime(2026, 7, 16, 10, 0),
        )


def test_exact_ledger_ddl_has_one_managed_delta_row_shape() -> None:
    statement = runtime_trust.render_create_ledger_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb")
    )
    sql = statement._transport_text()
    assert sql.startswith("/* DBTOBSB_RUNTIME_TRUST_LEDGER_DDL_V1 */\nCREATE TABLE")
    assert sql.endswith(") USING DELTA")
    assert "IF NOT EXISTS" not in sql
    assert "PARTITIONED BY" not in sql
    assert "PRIMARY KEY" not in sql
    assert "ledger_row_id STRING NOT NULL" in sql
    assert "expected_components ARRAY<STRUCT<component_key:STRING,contract_digest:STRING>>" in sql
    assert sql.count("current_timestamp") == 0
    assert ";" not in sql


@pytest.mark.parametrize("event_index", [0, 1, 2])
def test_fixed_event_sql_is_one_idempotent_marked_merge(event_index: int) -> None:
    events = _chain()
    statement = runtime_trust.render_append_event_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb"),
        events[event_index],
    )
    sql = statement._transport_text()
    assert sql.startswith("/* DBTOBSB_RUNTIME_TRUST_EVENT_V1 */")
    assert sql.count("current_timestamp()") == 1
    assert sql.count("MERGE INTO") == 1
    assert "WHEN NOT MATCHED THEN INSERT" in sql
    assert "WHEN MATCHED" not in sql
    assert "UPDATE" not in sql
    assert "DELETE" not in sql
    assert ";" not in sql
    assert "dbtobsb.runtime-trust.payload-digest.v1" in sql
    assert "CAST(9223372036854775807 AS BIGINT)" in sql if event_index else True


def test_generated_sql_hashes_and_sizes_match_the_shared_semantic_contract() -> None:
    names = runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb")
    registration, candidate, acceptance = _chain()
    events = {
        "registration": registration,
        "candidate": candidate,
        "acceptance": acceptance,
        "invalidation": _invalidation(),
    }
    statements = [
        ("create-ledger", runtime_trust.render_create_ledger_statement(names)),
        ("create-status-view", runtime_trust.render_create_status_view_statement(names)),
    ]
    for name, event in events.items():
        statements.extend(
            (
                (f"append-{name}", runtime_trust.render_append_event_statement(names, event)),
                (f"readback-{name}", runtime_trust.render_event_readback_statement(names, event)),
            )
        )
    observed = [
        {
            "name": name,
            "kind": statement.kind.value,
            "semantic_sha256": statement.semantic_sha256,
            "utf8_size": len(statement._transport_text().encode("utf-8")),
        }
        for name, statement in statements
    ]
    assert observed == _load_semantic_vectors()["sql"]


def test_acceptance_sql_resolves_server_times_and_exact_predecessors() -> None:
    _, candidate, acceptance = _chain()
    sql = runtime_trust.render_append_event_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb"), acceptance
    )._transport_text()
    assert "candidate.statement_evaluated_at AS candidate_statement_evaluated_at" in sql
    assert "anchor.statement_evaluated_at AS roster_statement_evaluated_at" in sql
    assert "least(c.statement_evaluated_at + INTERVAL 24 HOURS" in sql
    assert "candidate.event_id = f.candidate_event_id" in sql
    assert candidate.event_id in sql
    assert "f.post_start_lifecycle_state = 'ACTIVE'" not in sql  # typed literal, view validates


def test_reused_roster_anchor_rejects_backward_and_expired_candidate_clocks() -> None:
    _, candidate, _ = _chain()
    names = runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb")
    candidate_sql = runtime_trust.render_append_event_statement(names, candidate)._transport_text()
    assert "anchor.statement_evaluated_at <= f.statement_evaluated_at" in candidate_sql
    assert (
        "f.statement_evaluated_at < anchor.statement_evaluated_at + INTERVAL 24 HOURS"
        in candidate_sql
    )

    view_sql = runtime_trust.render_create_status_view_statement(names)._transport_text()
    assert view_sql.count("original.candidate_statement_evaluated_at <=") == 2
    assert view_sql.count("raw.candidate_statement_evaluated_at <") == 2
    assert view_sql.count("original.candidate_statement_evaluated_at + INTERVAL 24 HOURS") == 2


def test_readback_is_fixed_and_requires_cardinality_and_digest_agreement() -> None:
    registration, _, _ = _chain()
    sql = runtime_trust.render_event_readback_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb"), registration
    )._transport_text()
    assert "count(*) AS physical_row_count" in sql
    assert "count(DISTINCT payload_digest)" in sql
    assert registration.event_id in sql
    assert "SELECT *" not in sql
    assert ";" not in sql


def test_status_view_is_latest_generation_fail_closed_and_app_shaped() -> None:
    sql = runtime_trust.render_create_status_view_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb")
    )._transport_text()
    assert sql.count("current_timestamp()") == 1
    assert "max(generation) AS generation" in sql
    assert "counts.physical_row_count = 3" in sql
    assert "counts.invalidation_count = 0" in sql
    assert "counts.distinct_event_count = 3" in sql
    assert "original.roster_anchor_event_id = original.candidate_event_id" in sql
    assert "raw.generation - 1" in sql
    assert "clock.evaluated_at >= verified.valid_until" in sql
    assert "RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED" in sql
    assert "RUNTIME_TRUST_STALE" in sql
    assert "ADMIN_ATTESTED_POINT_IN_TIME" in sql
    for column in (
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "generation",
        "snapshot_id",
        "deployment_id",
        "deployment_mode",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "stable_graph_digest",
        "pre_start_machine_observation_digest",
        "post_start_machine_observation_digest",
        "roster_anchor_event_id",
        "roster_anchor_digest",
        "expected_components",
        "observed_components",
        "pre_start_statement_evaluated_at",
        "post_start_statement_evaluated_at",
        "roster_statement_evaluated_at",
        "machine_evidence_at",
        "roster_evidence_at",
        "oldest_evidence_at",
        "valid_until",
        "evaluated_at",
        "qualifier",
        "state",
    ):
        assert column in sql
    public_projection = sql.rsplit("\nSELECT\n", maxsplit=1)[-1].split(
        "FROM latest_verified", maxsplit=1
    )[0]
    assert "client_signature" not in public_projection


def test_statement_constructor_and_arbitrary_event_are_closed() -> None:
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_STATEMENT_CONSTRUCTION_DENIED",
    ):
        runtime_trust.RuntimeTrustStatement(
            kind=runtime_trust.RuntimeTrustStatementKind.APPEND_EVENT,
            text="DROP TABLE customer_data",
            _construction_token=object(),
        )
    with pytest.raises(runtime_trust.RuntimeTrustContractError):
        runtime_trust.render_append_event_statement(
            runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb"),
            cast(runtime_trust.RuntimeTrustEvent, object()),
        )


def test_invalidation_has_fixed_closed_reason_and_no_graph_values() -> None:
    registration, candidate, _ = _chain()
    invalidation = runtime_trust.SnapshotInvalidated(
        identity=registration.identity,
        reason=runtime_trust.InvalidationReason.OPERATOR_ABORTED,
        expected_components=registration.expected_components,
        predecessor_event_id=candidate.event_id,
        target_event_id=candidate.event_id,
    )
    sql = runtime_trust.render_append_event_statement(
        runtime_trust.RuntimeTrustObjectNames("observability", "dbtobsb"), invalidation
    )._transport_text()
    assert "'SNAPSHOT_INVALIDATED' AS operation" in sql
    assert "'OPERATOR_ABORTED' AS reason" in sql
    assert "CAST(NULL AS STRING) AS stable_graph_digest" in sql


def test_invalidation_must_target_the_current_predecessor() -> None:
    registration, candidate, _ = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_INVALIDATION_TARGET_INVALID",
    ):
        runtime_trust.SnapshotInvalidated(
            identity=registration.identity,
            reason=runtime_trust.InvalidationReason.OPERATOR_ABORTED,
            expected_components=registration.expected_components,
            predecessor_event_id=candidate.event_id,
            target_event_id=_h("f"),
        )


def test_four_event_client_nullability_matrix_is_exact() -> None:
    registration, candidate, acceptance = _chain()
    invalidation = runtime_trust.SnapshotInvalidated(
        identity=registration.identity,
        reason=runtime_trust.InvalidationReason.OPERATOR_ABORTED,
        expected_components=registration.expected_components,
        predecessor_event_id=candidate.event_id,
        target_event_id=candidate.event_id,
    )
    common = {
        "event_id",
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "generation",
        "operation",
        "state",
        "reason",
        "contract_version",
        "manifest_digest",
        "expected_component_count",
        "expected_components",
    }
    candidate_values = {
        "predecessor_event_id",
        "observed_components",
        "app_digest",
        "deployment_id",
        "deployment_mode",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "new_deployment_count",
        "direct_plan_digest",
        "direct_lineage_digest",
        "direct_state_serial",
        "resource_selection_digest",
        "source_digest",
        "build_digest",
        "artifact_digest",
        "configuration_digest",
        "app_resource_digest",
        "acl_digest",
        "job_run_as_digest",
        "uc_grant_digest",
        "group_root_digest",
        "service_principal_set_digest",
        "expected_roster_digest",
        "observed_roster_digest",
        "stable_graph_digest",
        "pre_start_machine_observation_digest",
        "pre_start_lifecycle_state",
        "pre_start_active_deployment_id",
        "pre_start_pending_deployment_count",
        "machine_observer_fingerprint",
        "roster_observation_digest",
        "roster_reviewer_fingerprint",
        "roster_anchor_event_id",
        "roster_anchor_digest",
        "candidate_digest",
    }
    acceptance_values = {
        "candidate_event_id",
        "post_start_machine_observation_digest",
        "post_start_lifecycle_state",
        "post_start_active_deployment_id",
        "post_start_pending_deployment_count",
    }
    expected_nonnull = (
        common,
        common | candidate_values,
        common | candidate_values | acceptance_values,
        common | {"predecessor_event_id", "target_event_id"},
    )
    for event, expected in zip(
        (registration, candidate, acceptance, invalidation),
        expected_nonnull,
        strict=True,
    ):
        row = runtime_trust._event_row(event)
        observed = {name for name, value in row.items() if value is not None}
        assert observed == expected


def test_changed_same_event_payload_and_contract_versions_change_digest() -> None:
    registration, _, _ = _chain()
    changed = replace(
        registration,
        expected_components=(
            runtime_trust.ExpectedComponent(
                runtime_trust.ComponentKey.BASE_OBSERVABILITY,
                _h("2"),
            ),
        ),
    )
    assert changed.event_id == registration.event_id
    at = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    original_record = runtime_trust.derive_event_record(registration, statement_evaluated_at=at)
    changed_record = runtime_trust.derive_event_record(changed, statement_evaluated_at=at)
    assert original_record.payload_digest != changed_record.payload_digest
    v1 = runtime_trust._digest(
        runtime_trust._Domain.EVENT_ID,
        {
            "contract_version": "dbtobsb.runtime-trust.v1",
            "installation_digest": registration.identity.installation_digest,
            "generation": "1",
            "operation": "MANIFEST_REGISTERED",
            "predecessor_event_id": None,
        },
    )
    v2 = runtime_trust._digest(
        runtime_trust._Domain.EVENT_ID,
        {
            "contract_version": "dbtobsb.runtime-trust.v2",
            "installation_digest": registration.identity.installation_digest,
            "generation": "1",
            "operation": "MANIFEST_REGISTERED",
            "predecessor_event_id": None,
        },
    )
    assert v1 != v2


def test_readback_validator_accepts_all_four_operations_and_redacts_proof() -> None:
    registration, candidate, acceptance = _chain()
    invalidation = _invalidation()
    candidate_at = datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=UTC)
    roster_at = candidate_at
    accepted_at = datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=UTC)
    cases = (
        (registration, {}, runtime_trust.RuntimeTrustOperation.MANIFEST_REGISTERED),
        (candidate, {}, runtime_trust.RuntimeTrustOperation.TRUST_CANDIDATE),
        (
            acceptance,
            {
                "candidate_statement_evaluated_at": candidate_at,
                "roster_statement_evaluated_at": roster_at,
            },
            runtime_trust.RuntimeTrustOperation.SNAPSHOT_ACCEPTED,
        ),
        (invalidation, {}, runtime_trust.RuntimeTrustOperation.SNAPSHOT_INVALIDATED),
    )
    for event, predecessor_times, operation in cases:
        readback = _readback(
            event,
            statement_evaluated_at=accepted_at,
            **predecessor_times,
        )
        proof = runtime_trust.validate_event_readback(
            event,
            readback,
            **predecessor_times,
        )
        assert proof.operation is operation
        assert proof.snapshot_id is not None if event is acceptance else proof.snapshot_id is None
        rendered = repr(proof)
        assert rendered == f"AcceptedRuntimeTrustEvent(operation={operation.value}, <redacted>)"
        for secret in (
            proof.event_id,
            proof.payload_digest,
            proof.server_record_digest,
            proof.ledger_row_id,
            proof.snapshot_id,
        ):
            if secret is not None:
                assert secret not in rendered


def test_acceptance_proof_cannot_be_constructed_by_caller() -> None:
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_PROOF_CONSTRUCTION_DENIED",
    ):
        runtime_trust.AcceptedRuntimeTrustEvent(
            operation=runtime_trust.RuntimeTrustOperation.MANIFEST_REGISTERED,
            event_id=_h("a"),
            payload_digest=_h("b"),
            server_record_digest=_h("c"),
            ledger_row_id=_h("d"),
            snapshot_id=None,
            statement_evaluated_at=datetime(2026, 7, 16, tzinfo=UTC),
            valid_until=None,
            _construction_token=object(),
        )


def test_readback_mapping_requires_exact_typed_sanitized_shape() -> None:
    registration, _, _ = _chain()
    readback = _readback(registration)
    mapping = {
        column: getattr(readback, column) for column in runtime_trust.RUNTIME_TRUST_READBACK_COLUMNS
    }
    assert runtime_trust.RuntimeTrustReadback.from_mapping(mapping) == readback
    assert repr(readback) == "RuntimeTrustReadback(<redacted>)"
    assert cast(str, readback.event_id) not in repr(readback)

    for malformed in (
        {key: value for key, value in mapping.items() if key != "event_id"},
        {**mapping, "connector_metadata": "must-not-be-accepted"},
        {**mapping, "physical_row_count": True},
        {**mapping, "event_id": "not-a-digest"},
        {
            **mapping,
            "statement_evaluated_at": datetime(2026, 7, 16, 10, 5),
        },
    ):
        with pytest.raises(
            runtime_trust.RuntimeTrustContractError,
            match=r"DBTOBSB_RUNTIME_TRUST_(READBACK|TIMESTAMP)_INVALID",
        ):
            runtime_trust.RuntimeTrustReadback.from_mapping(malformed)


@pytest.mark.parametrize(
    ("changes", "error_code"),
    [
        ({"physical_row_count": 0}, "READBACK_CARDINALITY_INVALID"),
        ({"physical_row_count": 2}, "READBACK_CARDINALITY_INVALID"),
        ({"distinct_payload_count": 0}, "EVENT_CONFLICT"),
        ({"distinct_payload_count": 2}, "EVENT_CONFLICT"),
        ({"distinct_server_record_count": 0}, "READBACK_CARDINALITY_INVALID"),
        ({"distinct_server_record_count": 2}, "READBACK_CARDINALITY_INVALID"),
        ({"distinct_ledger_row_count": 0}, "READBACK_CARDINALITY_INVALID"),
        ({"distinct_ledger_row_count": 2}, "READBACK_CARDINALITY_INVALID"),
    ],
)
def test_readback_validator_rejects_nonunique_physical_and_digest_axes(
    changes: dict[str, int], error_code: str
) -> None:
    registration, _, _ = _chain()
    readback = replace(_readback(registration), **changes)
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match=f"DBTOBSB_RUNTIME_TRUST_{error_code}",
    ):
        runtime_trust.validate_event_readback(registration, readback)


def test_readback_validator_distinguishes_event_conflict_from_integrity_failure() -> None:
    registration, _, _ = _chain()
    readback = _readback(registration)
    changed_payload = replace(
        registration,
        expected_components=(
            runtime_trust.ExpectedComponent(
                runtime_trust.ComponentKey.BASE_OBSERVABILITY,
                _h("2"),
            ),
        ),
    )
    assert changed_payload.event_id == registration.event_id
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_EVENT_CONFLICT",
    ):
        runtime_trust.validate_event_readback(changed_payload, readback)

    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_READBACK_INTEGRITY_INVALID",
    ):
        runtime_trust.validate_event_readback(
            registration,
            replace(readback, event_id=_h("f")),
        )


@pytest.mark.parametrize(
    "field",
    ["payload_digest", "server_record_digest", "ledger_row_id"],
)
def test_readback_validator_requires_exact_expected_digest(field: str) -> None:
    registration, _, _ = _chain()
    readback = replace(_readback(registration), **{field: _h("f")})
    expected_code = (
        "DBTOBSB_RUNTIME_TRUST_EVENT_CONFLICT"
        if field == "payload_digest"
        else "DBTOBSB_RUNTIME_TRUST_READBACK_INTEGRITY_INVALID"
    )
    with pytest.raises(runtime_trust.RuntimeTrustContractError, match=expected_code):
        runtime_trust.validate_event_readback(registration, readback)


def test_readback_validator_enforces_operation_nullability_and_acceptance_chronology() -> None:
    registration, _, acceptance = _chain()
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID",
    ):
        runtime_trust.validate_event_readback(
            registration,
            replace(_readback(registration), snapshot_id=_h("f")),
        )
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID",
    ):
        runtime_trust.validate_event_readback(
            registration,
            _readback(registration),
            candidate_statement_evaluated_at=datetime(2026, 7, 16, tzinfo=UTC),
        )

    candidate_at = datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=UTC)
    accepted_at = datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=UTC)
    readback = _readback(
        acceptance,
        statement_evaluated_at=accepted_at,
        candidate_statement_evaluated_at=candidate_at,
        roster_statement_evaluated_at=candidate_at,
    )
    for malformed in (
        replace(readback, snapshot_id=None),
        replace(readback, valid_until=None),
        replace(readback, valid_until=cast(datetime, readback.valid_until) + timedelta(seconds=1)),
    ):
        with pytest.raises(
            runtime_trust.RuntimeTrustContractError,
            match="DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID",
        ):
            runtime_trust.validate_event_readback(
                acceptance,
                malformed,
                candidate_statement_evaluated_at=candidate_at,
                roster_statement_evaluated_at=candidate_at,
            )
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_READBACK_INTEGRITY_INVALID",
    ):
        runtime_trust.validate_event_readback(
            acceptance,
            replace(readback, snapshot_id=_h("f")),
            candidate_statement_evaluated_at=candidate_at,
            roster_statement_evaluated_at=candidate_at,
        )
    with pytest.raises(
        runtime_trust.RuntimeTrustContractError,
        match="DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID",
    ):
        runtime_trust.validate_event_readback(
            acceptance,
            readback,
            candidate_statement_evaluated_at=accepted_at + timedelta(seconds=1),
            roster_statement_evaluated_at=candidate_at,
        )


def test_readback_errors_do_not_expose_customer_identifiers_or_digests() -> None:
    registration, _, _ = _chain()
    readback = replace(_readback(registration), payload_digest=_h("f"))
    with pytest.raises(runtime_trust.RuntimeTrustContractError) as raised:
        runtime_trust.validate_event_readback(registration, readback)
    rendered = str(raised.value)
    assert rendered == "DBTOBSB_RUNTIME_TRUST_EVENT_CONFLICT"
    assert registration.event_id not in rendered
    assert cast(str, readback.payload_digest) not in rendered


def test_all_typed_trust_evidence_has_stable_redacted_nested_representations() -> None:
    registration, candidate, acceptance = _chain()
    evidence = candidate.evidence
    graph = evidence.graph
    component = runtime_trust.ComponentObservation(
        component_key=runtime_trust.ComponentKey.BASE_OBSERVABILITY,
        contract_digest=graph.expected_components[0].contract_digest,
        runtime_resource_digest=_h("2"),
        runtime_principal_digest=_h("3"),
        binding_digest=_h("4"),
        dml_allowlist_digest=_h("5"),
        authority_digest=_h("6"),
    )
    derived = runtime_trust.derive_event_record(
        acceptance,
        statement_evaluated_at=datetime(2026, 7, 16, 10, 5, 0, 654321, tzinfo=UTC),
        candidate_statement_evaluated_at=datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=UTC),
        roster_statement_evaluated_at=datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=UTC),
    )
    names = runtime_trust.RuntimeTrustObjectNames("canary_catalog", "canary_schema")
    values = (
        names,
        graph.expected_components[0],
        graph.observed_components[0],
        component,
        evidence.deployment_set_before,
        evidence.deployment_set_after.deployments[0],
        evidence.deployment_set_after,
        graph.identity,
        graph,
        evidence.pre_start,
        evidence.roster,
        registration,
        evidence,
        candidate,
        acceptance.post_start,
        acceptance,
        _invalidation(),
        derived,
    )
    canaries = (
        "canary_catalog",
        "canary_schema",
        graph.identity.installation_digest,
        graph.deployment_id,
        graph.expected_components[0].contract_digest,
        candidate.event_id,
        acceptance.event_id,
        derived.snapshot_id,
    )
    for value in values:
        rendered = repr(value)
        assert rendered == f"{type(value).__name__}(<redacted>)"
        assert str(value) == rendered
        for canary in canaries:
            if canary is not None:
                assert canary not in rendered


def test_invalid_typed_evidence_exception_is_sanitized() -> None:
    canary = "customer-secret-must-not-be-logged"
    with pytest.raises(runtime_trust.RuntimeTrustContractError) as raised:
        runtime_trust.ExpectedComponent(
            runtime_trust.ComponentKey.BASE_OBSERVABILITY,
            canary,
        )
    assert str(raised.value) == "DBTOBSB_RUNTIME_TRUST_DIGEST_INVALID"
    assert canary not in str(raised.value)
    assert canary not in repr(raised.value)


def test_base_component_provider_digest_matches_the_runtime_trust_ddl_and_reducer() -> None:
    assert (
        runtime_trust.runtime_trust_provider_contract_sha256()
        == RUNTIME_TRUST_PROVIDER_CONTRACT_SHA256
    )
