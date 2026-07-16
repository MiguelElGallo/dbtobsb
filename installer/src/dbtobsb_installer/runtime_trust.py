"""Closed v1 runtime-trust ledger, digest, event, and status-view contract.

This module deliberately has no generic SQL entry point.  Callers provide validated, typed
runtime observations and receive opaque statements rendered from versioned product code.  The
statements are intended to be bound to the installer's signed preparation marker before one
Statement Execution request is submitted.

Only ``BASE_OBSERVABILITY`` is installable in this release.  The two future component names are
reserved so an unknown value can never be silently accepted as a product capability.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Never, cast

_MAX_BIGINT = 9_223_372_036_854_775_807
_MAX_INT = 2_147_483_647
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_DEPLOYMENT_ID = re.compile(r"^[0-9a-f]{32}$")
RUNTIME_TRUST_V1_IDENTIFIER_POLICY = "ASCII_REGULAR_IDENTIFIER_1_TO_128_V1"
RUNTIME_TRUST_V1_REGULAR_IDENTIFIER_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,127}$"
_IDENTIFIER = re.compile(RUNTIME_TRUST_V1_REGULAR_IDENTIFIER_PATTERN, flags=re.ASCII)
_CONTRACT_VERSION = "dbtobsb.runtime-trust.v1"
_QUALIFIER = "ADMIN_ATTESTED_POINT_IN_TIME"
_STATEMENT_TOKEN = object()
_ACCEPTANCE_PROOF_TOKEN = object()


class RuntimeTrustContractError(ValueError):
    """Stable fail-closed error without customer values or rendered SQL."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _RedactedRepresentation:
    """Stable representation for values that contain customer or trust evidence."""

    __slots__ = ()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(<redacted>)"


class ComponentKey(Enum):
    BASE_OBSERVABILITY = "BASE_OBSERVABILITY"
    SYSTEM_ENRICHMENT = "SYSTEM_ENRICHMENT"
    CONTROLLED_ACTIONS = "CONTROLLED_ACTIONS"


class RegistrationReason(Enum):
    INSTALL = "INSTALL"
    UPGRADE = "UPGRADE"
    ROLLBACK = "ROLLBACK"
    CHANGED_REFRESH = "CHANGED_REFRESH"
    UNCHANGED_REFRESH = "UNCHANGED_REFRESH"


class InvalidationReason(Enum):
    DEPLOYMENT_RECONCILIATION_FAILED = "DEPLOYMENT_RECONCILIATION_FAILED"
    FINAL_PLAN_DRIFT = "FINAL_PLAN_DRIFT"
    PRE_START_MISMATCH = "PRE_START_MISMATCH"
    ROSTER_REVIEW_FAILED = "ROSTER_REVIEW_FAILED"
    START_MISMATCH = "START_MISMATCH"
    POST_START_MISMATCH = "POST_START_MISMATCH"
    TRUST_WRITE_INDETERMINATE = "TRUST_WRITE_INDETERMINATE"
    OPERATOR_ABORTED = "OPERATOR_ABORTED"


class DeploymentStatus(Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    IN_PROGRESS = "IN_PROGRESS"


class DeploymentMode(Enum):
    SNAPSHOT = "SNAPSHOT"
    AUTO_SYNC = "AUTO_SYNC"


class LifecycleState(Enum):
    STOPPED = "STOPPED"
    ACTIVE = "ACTIVE"


class ObservationPhase(Enum):
    PRE_START = "PRE_START"
    POST_START = "POST_START"


class RuntimeTrustOperation(Enum):
    MANIFEST_REGISTERED = "MANIFEST_REGISTERED"
    TRUST_CANDIDATE = "TRUST_CANDIDATE"
    SNAPSHOT_ACCEPTED = "SNAPSHOT_ACCEPTED"
    SNAPSHOT_INVALIDATED = "SNAPSHOT_INVALIDATED"


class RuntimeTrustStatementKind(Enum):
    CREATE_LEDGER = "CREATE_LEDGER"
    CREATE_STATUS_VIEW = "CREATE_STATUS_VIEW"
    APPEND_EVENT = "APPEND_EVENT"
    READBACK_EVENT = "READBACK_EVENT"


class _Domain(Enum):
    DEPLOYMENT_SET = "dbtobsb.runtime-trust.deployment-set.v1"
    COMPONENT_OBSERVATION = "dbtobsb.runtime-trust.component-observation.v1"
    ROSTER_OBSERVATION = "dbtobsb.runtime-trust.roster-observation.v1"
    STABLE_GRAPH = "dbtobsb.runtime-trust.stable-graph.v1"
    MACHINE_OBSERVATION = "dbtobsb.runtime-trust.machine-observation.v1"
    EVENT_ID = "dbtobsb.runtime-trust.event-id.v1"
    CANDIDATE = "dbtobsb.runtime-trust.candidate-digest.v1"
    ACCEPTANCE = "dbtobsb.runtime-trust.acceptance-digest.v1"
    PAYLOAD = "dbtobsb.runtime-trust.payload-digest.v1"
    SNAPSHOT_ID = "dbtobsb.runtime-trust.snapshot-id.v1"
    SERVER_RECORD = "dbtobsb.runtime-trust.server-record.v1"
    LEDGER_ROW_ID = "dbtobsb.runtime-trust.ledger-row-id.v1"


def _fail(code: str) -> Never:
    raise RuntimeTrustContractError(code)


def _require_digest(value: object, code: str = "DBTOBSB_RUNTIME_TRUST_DIGEST_INVALID") -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        _fail(code)
    return value


def _require_deployment_id(value: object) -> str:
    if not isinstance(value, str) or _DEPLOYMENT_ID.fullmatch(value) is None:
        _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_ID_INVALID")
    return value


def _require_int(value: object, minimum: int, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        _fail(code)
    return value


def _decimal(value: int, minimum: int = 0, maximum: int = _MAX_BIGINT) -> str:
    """Map a validated SQL integer to the frozen canonical JSON decimal string."""
    return str(_require_int(value, minimum, maximum, "DBTOBSB_RUNTIME_TRUST_INTEGER_INVALID"))


def parse_canonical_decimal(
    value: object,
    *,
    minimum: int = 0,
    maximum: int = _MAX_BIGINT,
) -> int:
    """Parse the v1 JSON integer representation without coercion or binary64 loss."""
    if (
        not isinstance(value, str)
        or re.fullmatch(r"0|[1-9][0-9]*", value, flags=re.ASCII) is None
        or len(value) > 19
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_DECIMAL_INVALID")
    parsed = int(value)
    if not minimum <= parsed <= maximum:
        _fail("DBTOBSB_RUNTIME_TRUST_DECIMAL_INVALID")
    return parsed


def _validate_canonical_value(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            _fail("DBTOBSB_RUNTIME_TRUST_CANONICAL_ASCII_REQUIRED")
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_canonical_value(item)
        return
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            _fail("DBTOBSB_RUNTIME_TRUST_CANONICAL_OBJECT_INVALID")
        for key, item in value.items():
            _validate_canonical_value(key)
            _validate_canonical_value(item)
        return
    _fail("DBTOBSB_RUNTIME_TRUST_CANONICAL_TYPE_INVALID")


def _canonical_object(domain: _Domain, data: Mapping[str, Any]) -> bytes:
    """RFC 8785 bytes for the deliberately restricted v1 value universe.

    v1 permits only ASCII strings, null, arrays, and objects.  Numbers and booleans are rejected;
    SQL integers must first use the explicit unsigned decimal-string mapping.  For this restricted
    universe, sorted compact JSON is byte-for-byte the JSON Canonicalization Scheme result.
    """
    if not isinstance(domain, _Domain) or not isinstance(data, dict):
        _fail("DBTOBSB_RUNTIME_TRUST_CANONICAL_OBJECT_INVALID")
    document = {"domain": domain.value, "data": data}
    _validate_canonical_value(document)
    return json.dumps(
        document,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _digest(domain: _Domain, data: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_object(domain, data)).hexdigest()


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _fail("DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID")
    utc = value.astimezone(UTC)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_canonical_timestamp(value: object) -> datetime:
    """Parse the exact six-microsecond-digit UTC timestamp used by v1 digests."""
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z",
            value,
            flags=re.ASCII,
        )
        is None
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        _fail("DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID")
    if _timestamp(parsed) != value:
        _fail("DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID")
    return parsed


def _utc_datetime(value: object) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _fail("DBTOBSB_RUNTIME_TRUST_TIMESTAMP_INVALID")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True, repr=False)
class RuntimeTrustObjectNames(_RedactedRepresentation):
    """Customer-selected object parents under the explicit v1 identifier policy.

    v1 supports only unquoted-style ASCII regular identifiers of 1--128 characters matching
    ``RUNTIME_TRUST_V1_REGULAR_IDENTIFIER_PATTERN``. Unicode, spaces, punctuation, already quoted
    names, and otherwise valid Unity Catalog names outside that deliberately narrow support
    contract fail before SQL rendering.
    """

    catalog: str
    schema: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.catalog, str)
            or _IDENTIFIER.fullmatch(self.catalog) is None
            or not isinstance(self.schema, str)
            or _IDENTIFIER.fullmatch(self.schema) is None
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_IDENTIFIER_INVALID")

    @property
    def ledger(self) -> str:
        return f"`{self.catalog}`.`{self.schema}`.`runtime_trust_ledger`"

    @property
    def status_view(self) -> str:
        return f"`{self.catalog}`.`{self.schema}`.`runtime_trust_status_v`"


@dataclass(frozen=True, slots=True, repr=False)
class ExpectedComponent(_RedactedRepresentation):
    component_key: ComponentKey
    contract_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.component_key, ComponentKey):
            _fail("DBTOBSB_RUNTIME_TRUST_COMPONENT_UNKNOWN")
        _require_digest(self.contract_digest)

    def canonical(self) -> dict[str, str]:
        return {
            "component_key": self.component_key.value,
            "contract_digest": self.contract_digest,
        }


@dataclass(frozen=True, slots=True, repr=False)
class ObservedComponent(ExpectedComponent):
    observation_digest: str

    def __post_init__(self) -> None:
        ExpectedComponent.__post_init__(self)
        _require_digest(self.observation_digest)

    def canonical(self) -> dict[str, str]:
        return {
            "component_key": self.component_key.value,
            "contract_digest": self.contract_digest,
            "observation_digest": self.observation_digest,
        }


def _expected_components(values: Sequence[ExpectedComponent]) -> tuple[ExpectedComponent, ...]:
    if not isinstance(values, (tuple, list)):
        _fail("DBTOBSB_RUNTIME_TRUST_COMPONENTS_INVALID")
    result = tuple(values)
    if (
        not result
        or len(result) > 3
        or any(not isinstance(item, ExpectedComponent) for item in result)
        or tuple(item.component_key.value for item in result)
        != tuple(sorted({item.component_key.value for item in result}))
        or result[0].component_key is not ComponentKey.BASE_OBSERVABILITY
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_COMPONENTS_INVALID")
    return result


def _base_components(values: Sequence[ExpectedComponent]) -> tuple[ExpectedComponent, ...]:
    result = _expected_components(values)
    if len(result) != 1 or result[0].component_key is not ComponentKey.BASE_OBSERVABILITY:
        _fail("DBTOBSB_RUNTIME_TRUST_BASE_COMPONENT_REQUIRED")
    return result


def _observed_components(
    values: Sequence[ObservedComponent],
    expected: Sequence[ExpectedComponent],
) -> tuple[ObservedComponent, ...]:
    if not isinstance(values, (tuple, list)):
        _fail("DBTOBSB_RUNTIME_TRUST_OBSERVED_COMPONENTS_INVALID")
    result = tuple(values)
    if (
        len(result) != len(expected)
        or any(not isinstance(item, ObservedComponent) for item in result)
        or tuple(item.component_key.value for item in result)
        != tuple(sorted({item.component_key.value for item in result}))
        or any(
            observed.component_key is not required.component_key
            or observed.contract_digest != required.contract_digest
            for observed, required in zip(result, expected, strict=True)
        )
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_OBSERVED_COMPONENTS_INVALID")
    return result


@dataclass(frozen=True, slots=True, repr=False)
class ComponentObservation(_RedactedRepresentation):
    component_key: ComponentKey
    contract_digest: str
    runtime_resource_digest: str
    runtime_principal_digest: str
    binding_digest: str
    dml_allowlist_digest: str
    authority_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.component_key, ComponentKey):
            _fail("DBTOBSB_RUNTIME_TRUST_COMPONENT_UNKNOWN")
        for value in (
            self.contract_digest,
            self.runtime_resource_digest,
            self.runtime_principal_digest,
            self.binding_digest,
            self.dml_allowlist_digest,
            self.authority_digest,
        ):
            _require_digest(value)

    @property
    def observation_digest(self) -> str:
        return _digest(
            _Domain.COMPONENT_OBSERVATION,
            {
                "component_key": self.component_key.value,
                "contract_digest": self.contract_digest,
                "runtime_resource_digest": self.runtime_resource_digest,
                "runtime_principal_digest": self.runtime_principal_digest,
                "binding_digest": self.binding_digest,
                "dml_allowlist_digest": self.dml_allowlist_digest,
                "authority_digest": self.authority_digest,
            },
        )

    def observed_component(self) -> ObservedComponent:
        return ObservedComponent(
            component_key=self.component_key,
            contract_digest=self.contract_digest,
            observation_digest=self.observation_digest,
        )


@dataclass(frozen=True, slots=True, repr=False)
class DeploymentRecord(_RedactedRepresentation):
    deployment_id: str
    status: DeploymentStatus
    mode: DeploymentMode
    source_digest: str | None
    artifact_digest: str | None
    configuration_digest: str | None

    def __post_init__(self) -> None:
        _require_deployment_id(self.deployment_id)
        if not isinstance(self.status, DeploymentStatus) or not isinstance(
            self.mode, DeploymentMode
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_ENUM_INVALID")
        for value in (self.source_digest, self.artifact_digest, self.configuration_digest):
            if value is not None:
                _require_digest(value)

    def canonical(self) -> dict[str, str | None]:
        return {
            "deployment_id": self.deployment_id,
            "status": self.status.value,
            "mode": self.mode.value,
            "source_digest": self.source_digest,
            "artifact_digest": self.artifact_digest,
            "configuration_digest": self.configuration_digest,
        }


@dataclass(frozen=True, slots=True, repr=False)
class DeploymentSet(_RedactedRepresentation):
    account_digest: str
    workspace_digest: str
    app_digest: str
    deployments: tuple[DeploymentRecord, ...]

    def __post_init__(self) -> None:
        for value in (self.account_digest, self.workspace_digest, self.app_digest):
            _require_digest(value)
        if not isinstance(self.deployments, tuple) or any(
            not isinstance(item, DeploymentRecord) for item in self.deployments
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_SET_INVALID")
        ids = tuple(item.deployment_id for item in self.deployments)
        if ids != tuple(sorted(set(ids))):
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_SET_INVALID")

    @property
    def digest(self) -> str:
        return _digest(
            _Domain.DEPLOYMENT_SET,
            {
                "account_digest": self.account_digest,
                "workspace_digest": self.workspace_digest,
                "app_digest": self.app_digest,
                "deployments": [item.canonical() for item in self.deployments],
            },
        )


@dataclass(frozen=True, slots=True, repr=False)
class CommonIdentity(_RedactedRepresentation):
    installation_digest: str
    workspace_digest: str
    account_digest: str
    manifest_digest: str
    generation: int

    def __post_init__(self) -> None:
        for value in (
            self.installation_digest,
            self.workspace_digest,
            self.account_digest,
            self.manifest_digest,
        ):
            _require_digest(value)
        _require_int(
            self.generation,
            1,
            _MAX_BIGINT,
            "DBTOBSB_RUNTIME_TRUST_GENERATION_INVALID",
        )


@dataclass(frozen=True, slots=True, repr=False)
class RuntimeGraph(_RedactedRepresentation):
    identity: CommonIdentity
    app_digest: str
    deployment_id: str
    deployment_mode: DeploymentMode
    deployment_set_after_digest: str
    direct_plan_digest: str
    direct_lineage_digest: str
    direct_state_serial: int
    resource_selection_digest: str
    source_digest: str
    build_digest: str
    artifact_digest: str
    configuration_digest: str
    app_resource_digest: str
    acl_digest: str
    job_run_as_digest: str
    uc_grant_digest: str
    group_root_digest: str
    service_principal_set_digest: str
    expected_roster_digest: str
    observed_roster_digest: str
    expected_components: tuple[ExpectedComponent, ...]
    observed_components: tuple[ObservedComponent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CommonIdentity):
            _fail("DBTOBSB_RUNTIME_TRUST_IDENTITY_INVALID")
        _require_deployment_id(self.deployment_id)
        if self.deployment_mode is not DeploymentMode.SNAPSHOT:
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_MODE_INVALID")
        for value in (
            self.app_digest,
            self.deployment_set_after_digest,
            self.direct_plan_digest,
            self.direct_lineage_digest,
            self.resource_selection_digest,
            self.source_digest,
            self.build_digest,
            self.artifact_digest,
            self.configuration_digest,
            self.app_resource_digest,
            self.acl_digest,
            self.job_run_as_digest,
            self.uc_grant_digest,
            self.group_root_digest,
            self.service_principal_set_digest,
            self.expected_roster_digest,
            self.observed_roster_digest,
        ):
            _require_digest(value)
        _require_int(
            self.direct_state_serial,
            0,
            _MAX_BIGINT,
            "DBTOBSB_RUNTIME_TRUST_DIRECT_SERIAL_INVALID",
        )
        expected = _base_components(self.expected_components)
        observed = _observed_components(self.observed_components, expected)
        object.__setattr__(self, "expected_components", expected)
        object.__setattr__(self, "observed_components", observed)
        if self.expected_roster_digest != self.observed_roster_digest:
            _fail("DBTOBSB_RUNTIME_TRUST_ROSTER_MISMATCH")

    @property
    def stable_graph_digest(self) -> str:
        identity = self.identity
        return _digest(
            _Domain.STABLE_GRAPH,
            {
                "installation_digest": identity.installation_digest,
                "workspace_digest": identity.workspace_digest,
                "account_digest": identity.account_digest,
                "manifest_digest": identity.manifest_digest,
                "app_digest": self.app_digest,
                "deployment_id": self.deployment_id,
                "deployment_mode": self.deployment_mode.value,
                "deployment_set_after_digest": self.deployment_set_after_digest,
                "direct_plan_digest": self.direct_plan_digest,
                "direct_lineage_digest": self.direct_lineage_digest,
                "direct_state_serial": _decimal(self.direct_state_serial),
                "resource_selection_digest": self.resource_selection_digest,
                "source_digest": self.source_digest,
                "build_digest": self.build_digest,
                "artifact_digest": self.artifact_digest,
                "configuration_digest": self.configuration_digest,
                "app_resource_digest": self.app_resource_digest,
                "acl_digest": self.acl_digest,
                "job_run_as_digest": self.job_run_as_digest,
                "uc_grant_digest": self.uc_grant_digest,
                "group_root_digest": self.group_root_digest,
                "service_principal_set_digest": self.service_principal_set_digest,
                "expected_roster_digest": self.expected_roster_digest,
                "observed_roster_digest": self.observed_roster_digest,
                "expected_component_count": _decimal(len(self.expected_components), 1, 3),
                "expected_components": [item.canonical() for item in self.expected_components],
                "observed_components": [item.canonical() for item in self.observed_components],
            },
        )


@dataclass(frozen=True, slots=True, repr=False)
class MachineObservation(_RedactedRepresentation):
    phase: ObservationPhase
    identity: CommonIdentity
    deployment_id: str
    deployment_mode: DeploymentMode
    deployment_set_after_digest: str
    stable_graph_digest: str
    lifecycle_state: LifecycleState
    active_deployment_id: str
    pending_deployment_count: int
    machine_observer_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.phase, ObservationPhase) or not isinstance(
            self.identity, CommonIdentity
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_MACHINE_OBSERVATION_INVALID")
        _require_deployment_id(self.deployment_id)
        _require_deployment_id(self.active_deployment_id)
        if (
            self.deployment_mode is not DeploymentMode.SNAPSHOT
            or self.active_deployment_id != self.deployment_id
            or self.pending_deployment_count != 0
            or (
                self.phase is ObservationPhase.PRE_START
                and self.lifecycle_state is not LifecycleState.STOPPED
            )
            or (
                self.phase is ObservationPhase.POST_START
                and self.lifecycle_state is not LifecycleState.ACTIVE
            )
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_MACHINE_OBSERVATION_INVALID")
        for value in (
            self.deployment_set_after_digest,
            self.stable_graph_digest,
            self.machine_observer_fingerprint,
        ):
            _require_digest(value)
        _require_int(
            self.pending_deployment_count,
            0,
            0,
            "DBTOBSB_RUNTIME_TRUST_PENDING_DEPLOYMENT_INVALID",
        )

    @property
    def digest(self) -> str:
        identity = self.identity
        return _digest(
            _Domain.MACHINE_OBSERVATION,
            {
                "phase": self.phase.value,
                "installation_digest": identity.installation_digest,
                "workspace_digest": identity.workspace_digest,
                "account_digest": identity.account_digest,
                "manifest_digest": identity.manifest_digest,
                "deployment_id": self.deployment_id,
                "deployment_mode": self.deployment_mode.value,
                "deployment_set_after_digest": self.deployment_set_after_digest,
                "stable_graph_digest": self.stable_graph_digest,
                "lifecycle_state": self.lifecycle_state.value,
                "active_deployment_id": self.active_deployment_id,
                "pending_deployment_count": _decimal(self.pending_deployment_count, 0, 0),
                "machine_observer_fingerprint": self.machine_observer_fingerprint,
            },
        )


@dataclass(frozen=True, slots=True, repr=False)
class RosterObservation(_RedactedRepresentation):
    identity: CommonIdentity
    service_principal_set_digest: str
    expected_roster_digest: str
    observed_roster_digest: str
    roster_reviewer_fingerprint: str
    expected_components: tuple[ExpectedComponent, ...]
    observed_components: tuple[ObservedComponent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CommonIdentity):
            _fail("DBTOBSB_RUNTIME_TRUST_IDENTITY_INVALID")
        for value in (
            self.service_principal_set_digest,
            self.expected_roster_digest,
            self.observed_roster_digest,
            self.roster_reviewer_fingerprint,
        ):
            _require_digest(value)
        expected = _base_components(self.expected_components)
        observed = _observed_components(self.observed_components, expected)
        object.__setattr__(self, "expected_components", expected)
        object.__setattr__(self, "observed_components", observed)
        if self.expected_roster_digest != self.observed_roster_digest:
            _fail("DBTOBSB_RUNTIME_TRUST_ROSTER_MISMATCH")

    @property
    def digest(self) -> str:
        identity = self.identity
        return _digest(
            _Domain.ROSTER_OBSERVATION,
            {
                "account_digest": identity.account_digest,
                "workspace_digest": identity.workspace_digest,
                "service_principal_set_digest": self.service_principal_set_digest,
                "expected_roster_digest": self.expected_roster_digest,
                "observed_roster_digest": self.observed_roster_digest,
                "roster_reviewer_fingerprint": self.roster_reviewer_fingerprint,
                "expected_component_count": _decimal(len(self.expected_components), 1, 3),
                "expected_components": [item.canonical() for item in self.expected_components],
                "observed_components": [item.canonical() for item in self.observed_components],
            },
        )


def _event_id(
    identity: CommonIdentity,
    operation: RuntimeTrustOperation,
    predecessor_event_id: str | None,
) -> str:
    if predecessor_event_id is not None:
        _require_digest(predecessor_event_id)
    return _digest(
        _Domain.EVENT_ID,
        {
            "contract_version": _CONTRACT_VERSION,
            "installation_digest": identity.installation_digest,
            "generation": _decimal(identity.generation, 1),
            "operation": operation.value,
            "predecessor_event_id": predecessor_event_id,
        },
    )


@dataclass(frozen=True, slots=True, repr=False)
class ManifestRegistered(_RedactedRepresentation):
    identity: CommonIdentity
    reason: RegistrationReason
    expected_components: tuple[ExpectedComponent, ...]
    predecessor_event_id: str | None = None
    prior_generation: int | None = None
    prior_snapshot_id: str | None = None
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CommonIdentity) or not isinstance(
            self.reason, RegistrationReason
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_REGISTRATION_INVALID")
        expected = _base_components(self.expected_components)
        object.__setattr__(self, "expected_components", expected)
        if self.identity.generation == 1:
            if self.reason is not RegistrationReason.INSTALL:
                _fail("DBTOBSB_RUNTIME_TRUST_REGISTRATION_REASON_INVALID")
            if any(
                value is not None
                for value in (
                    self.predecessor_event_id,
                    self.prior_generation,
                    self.prior_snapshot_id,
                )
            ):
                _fail("DBTOBSB_RUNTIME_TRUST_REGISTRATION_PREDECESSOR_INVALID")
        else:
            if self.reason is RegistrationReason.INSTALL:
                _fail("DBTOBSB_RUNTIME_TRUST_REGISTRATION_REASON_INVALID")
            _require_digest(self.predecessor_event_id)
            if self.prior_generation != self.identity.generation - 1:
                _fail("DBTOBSB_RUNTIME_TRUST_REGISTRATION_PREDECESSOR_INVALID")
            if self.prior_snapshot_id is not None:
                _require_digest(self.prior_snapshot_id)
        object.__setattr__(
            self,
            "event_id",
            _event_id(
                self.identity,
                RuntimeTrustOperation.MANIFEST_REGISTERED,
                self.predecessor_event_id,
            ),
        )


@dataclass(frozen=True, slots=True, repr=False)
class CandidateEvidence(_RedactedRepresentation):
    deployment_set_before: DeploymentSet
    deployment_set_after: DeploymentSet
    graph: RuntimeGraph
    pre_start: MachineObservation
    roster: RosterObservation

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, expected)
            for value, expected in (
                (self.deployment_set_before, DeploymentSet),
                (self.deployment_set_after, DeploymentSet),
                (self.graph, RuntimeGraph),
                (self.pre_start, MachineObservation),
                (self.roster, RosterObservation),
            )
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_CANDIDATE_EVIDENCE_INVALID")
        identity = self.graph.identity
        for deployment_set in (self.deployment_set_before, self.deployment_set_after):
            if (
                deployment_set.account_digest != identity.account_digest
                or deployment_set.workspace_digest != identity.workspace_digest
                or deployment_set.app_digest != self.graph.app_digest
            ):
                _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_SET_MISMATCH")
        if (
            self.graph.deployment_set_after_digest != self.deployment_set_after.digest
            or self.pre_start.identity != identity
            or self.roster.identity != identity
            or self.pre_start.deployment_id != self.graph.deployment_id
            or self.pre_start.deployment_set_after_digest != self.deployment_set_after.digest
            or self.pre_start.stable_graph_digest != self.graph.stable_graph_digest
            or self.roster.service_principal_set_digest != self.graph.service_principal_set_digest
            or self.roster.expected_roster_digest != self.graph.expected_roster_digest
            or self.roster.observed_roster_digest != self.graph.observed_roster_digest
            or self.roster.expected_components != self.graph.expected_components
            or self.roster.observed_components != self.graph.observed_components
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_CANDIDATE_EVIDENCE_MISMATCH")
        if any(
            item.status is DeploymentStatus.IN_PROGRESS
            for deployment_set in (
                self.deployment_set_before,
                self.deployment_set_after,
            )
            for item in deployment_set.deployments
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_PENDING")
        selected = next(
            (
                item
                for item in self.deployment_set_after.deployments
                if item.deployment_id == self.graph.deployment_id
            ),
            None,
        )
        if (
            selected is None
            or selected.source_digest != self.graph.source_digest
            or selected.artifact_digest != self.graph.artifact_digest
            or selected.configuration_digest != self.graph.configuration_digest
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_SELECTED_DEPLOYMENT_MISMATCH")

    @property
    def new_deployment_count(self) -> int:
        before = {item.deployment_id for item in self.deployment_set_before.deployments}
        after = {item.deployment_id for item in self.deployment_set_after.deployments}
        return len(after - before)


@dataclass(frozen=True, slots=True, repr=False)
class TrustCandidate(_RedactedRepresentation):
    registration: ManifestRegistered
    evidence: CandidateEvidence
    roster_anchor_event_id: str | None = None
    roster_anchor_digest: str | None = None
    event_id: str = field(init=False)
    candidate_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.registration, ManifestRegistered) or not isinstance(
            self.evidence, CandidateEvidence
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_CANDIDATE_INVALID")
        identity = self.registration.identity
        graph = self.evidence.graph
        if (
            graph.identity != identity
            or graph.expected_components != self.registration.expected_components
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_CANDIDATE_IDENTITY_MISMATCH")
        event_id = _event_id(
            identity,
            RuntimeTrustOperation.TRUST_CANDIDATE,
            self.registration.event_id,
        )
        anchor_event = self.roster_anchor_event_id
        anchor_digest = self.roster_anchor_digest
        if anchor_event is None and anchor_digest is None:
            anchor_event = event_id
            anchor_digest = self.evidence.roster.digest
        elif anchor_event is None or anchor_digest is None:
            _fail("DBTOBSB_RUNTIME_TRUST_ROSTER_ANCHOR_INVALID")
        _require_digest(anchor_event)
        _require_digest(anchor_digest)
        object.__setattr__(self, "roster_anchor_event_id", anchor_event)
        object.__setattr__(self, "roster_anchor_digest", anchor_digest)
        object.__setattr__(self, "event_id", event_id)
        if (
            anchor_event != event_id
            and self.registration.reason is not RegistrationReason.UNCHANGED_REFRESH
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_ROSTER_REUSE_INVALID")
        graph = self.evidence.graph
        object.__setattr__(
            self,
            "candidate_digest",
            _digest(
                _Domain.CANDIDATE,
                {
                    "event_id": event_id,
                    "predecessor_event_id": self.registration.event_id,
                    "installation_digest": identity.installation_digest,
                    "workspace_digest": identity.workspace_digest,
                    "account_digest": identity.account_digest,
                    "manifest_digest": identity.manifest_digest,
                    "deployment_id": graph.deployment_id,
                    "deployment_mode": graph.deployment_mode.value,
                    "deployment_set_before_digest": self.evidence.deployment_set_before.digest,
                    "deployment_set_after_digest": self.evidence.deployment_set_after.digest,
                    "new_deployment_count": _decimal(self.evidence.new_deployment_count, 0, 1),
                    "stable_graph_digest": graph.stable_graph_digest,
                    "pre_start_machine_observation_digest": self.evidence.pre_start.digest,
                    "roster_observation_digest": self.evidence.roster.digest,
                    "roster_anchor_event_id": anchor_event,
                    "roster_anchor_digest": anchor_digest,
                    "machine_observer_fingerprint": (
                        self.evidence.pre_start.machine_observer_fingerprint
                    ),
                    "roster_reviewer_fingerprint": self.evidence.roster.roster_reviewer_fingerprint,
                    "expected_component_count": _decimal(len(graph.expected_components), 1, 3),
                    "expected_components": [item.canonical() for item in graph.expected_components],
                    "observed_components": [item.canonical() for item in graph.observed_components],
                },
            ),
        )
        before_ids = {
            item.deployment_id for item in self.evidence.deployment_set_before.deployments
        }
        after = {
            item.deployment_id: item for item in self.evidence.deployment_set_after.deployments
        }
        selected = after.get(graph.deployment_id)
        if (
            selected is None
            or selected.status is not DeploymentStatus.SUCCEEDED
            or selected.mode is not DeploymentMode.SNAPSHOT
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_SELECTED_DEPLOYMENT_INVALID")
        if self.registration.reason is RegistrationReason.UNCHANGED_REFRESH:
            if (
                self.evidence.new_deployment_count != 0
                or self.evidence.deployment_set_before != self.evidence.deployment_set_after
                or graph.deployment_id not in before_ids
            ):
                _fail("DBTOBSB_RUNTIME_TRUST_UNCHANGED_REFRESH_INVALID")
        elif self.evidence.new_deployment_count != 1 or {
            item.deployment_id for item in self.evidence.deployment_set_after.deployments
        } - before_ids != {graph.deployment_id}:
            _fail("DBTOBSB_RUNTIME_TRUST_DEPLOYMENT_DELTA_INVALID")


@dataclass(frozen=True, slots=True, repr=False)
class SnapshotAccepted(_RedactedRepresentation):
    candidate: TrustCandidate
    post_start: MachineObservation
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, TrustCandidate) or not isinstance(
            self.post_start, MachineObservation
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_INVALID")
        graph = self.candidate.evidence.graph
        pre = self.candidate.evidence.pre_start
        if (
            self.post_start.phase is not ObservationPhase.POST_START
            or self.post_start.identity != graph.identity
            or self.post_start.deployment_id != graph.deployment_id
            or self.post_start.deployment_mode is not graph.deployment_mode
            or self.post_start.deployment_set_after_digest != graph.deployment_set_after_digest
            or self.post_start.stable_graph_digest != graph.stable_graph_digest
            or self.post_start.machine_observer_fingerprint != pre.machine_observer_fingerprint
            or self.post_start.digest == pre.digest
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_MISMATCH")
        object.__setattr__(
            self,
            "event_id",
            _event_id(
                graph.identity,
                RuntimeTrustOperation.SNAPSHOT_ACCEPTED,
                self.candidate.event_id,
            ),
        )


@dataclass(frozen=True, slots=True, repr=False)
class SnapshotInvalidated(_RedactedRepresentation):
    identity: CommonIdentity
    reason: InvalidationReason
    expected_components: tuple[ExpectedComponent, ...]
    predecessor_event_id: str
    target_event_id: str
    target_snapshot_id: str | None = None
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CommonIdentity) or not isinstance(
            self.reason, InvalidationReason
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_INVALIDATION_INVALID")
        expected = _base_components(self.expected_components)
        object.__setattr__(self, "expected_components", expected)
        _require_digest(self.predecessor_event_id)
        _require_digest(self.target_event_id)
        if self.target_event_id != self.predecessor_event_id:
            _fail("DBTOBSB_RUNTIME_TRUST_INVALIDATION_TARGET_INVALID")
        if self.target_snapshot_id is not None:
            _require_digest(self.target_snapshot_id)
        object.__setattr__(
            self,
            "event_id",
            _event_id(
                self.identity,
                RuntimeTrustOperation.SNAPSHOT_INVALIDATED,
                self.predecessor_event_id,
            ),
        )


RuntimeTrustEvent = ManifestRegistered | TrustCandidate | SnapshotAccepted | SnapshotInvalidated


@dataclass(frozen=True, slots=True, repr=False)
class DerivedEventRecord(_RedactedRepresentation):
    """Reference result used to verify one persisted server-derived event row."""

    event_id: str
    payload_digest: str
    snapshot_id: str | None
    server_record_digest: str
    ledger_row_id: str
    statement_evaluated_at: datetime
    valid_until: datetime | None
    acceptance_digest: str | None


RUNTIME_TRUST_READBACK_COLUMNS: tuple[str, ...] = (
    "physical_row_count",
    "event_id",
    "payload_digest",
    "server_record_digest",
    "ledger_row_id",
    "snapshot_id",
    "statement_evaluated_at",
    "valid_until",
    "distinct_payload_count",
    "distinct_server_record_count",
    "distinct_ledger_row_count",
)


@dataclass(frozen=True, slots=True, repr=False)
class RuntimeTrustReadback:
    """Typed sanitized result of the fixed event-readback statement."""

    physical_row_count: int
    event_id: str | None
    payload_digest: str | None
    server_record_digest: str | None
    ledger_row_id: str | None
    snapshot_id: str | None
    statement_evaluated_at: datetime | None
    valid_until: datetime | None
    distinct_payload_count: int
    distinct_server_record_count: int
    distinct_ledger_row_count: int

    def __post_init__(self) -> None:
        for value in (
            self.physical_row_count,
            self.distinct_payload_count,
            self.distinct_server_record_count,
            self.distinct_ledger_row_count,
        ):
            _require_int(
                value,
                0,
                _MAX_BIGINT,
                "DBTOBSB_RUNTIME_TRUST_READBACK_INVALID",
            )
        for value in (
            self.event_id,
            self.payload_digest,
            self.server_record_digest,
            self.ledger_row_id,
            self.snapshot_id,
        ):
            if value is not None:
                _require_digest(value, "DBTOBSB_RUNTIME_TRUST_READBACK_INVALID")
        for value in (self.statement_evaluated_at, self.valid_until):
            if value is not None:
                _utc_datetime(value)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> RuntimeTrustReadback:
        """Normalize one exact connector row without accepting additional metadata."""
        if not isinstance(value, Mapping) or set(value) != set(RUNTIME_TRUST_READBACK_COLUMNS):
            _fail("DBTOBSB_RUNTIME_TRUST_READBACK_INVALID")
        try:
            return cls(
                physical_row_count=cast(int, value["physical_row_count"]),
                event_id=cast(str | None, value["event_id"]),
                payload_digest=cast(str | None, value["payload_digest"]),
                server_record_digest=cast(str | None, value["server_record_digest"]),
                ledger_row_id=cast(str | None, value["ledger_row_id"]),
                snapshot_id=cast(str | None, value["snapshot_id"]),
                statement_evaluated_at=cast(datetime | None, value["statement_evaluated_at"]),
                valid_until=cast(datetime | None, value["valid_until"]),
                distinct_payload_count=cast(int, value["distinct_payload_count"]),
                distinct_server_record_count=cast(int, value["distinct_server_record_count"]),
                distinct_ledger_row_count=cast(int, value["distinct_ledger_row_count"]),
            )
        except (KeyError, TypeError):
            _fail("DBTOBSB_RUNTIME_TRUST_READBACK_INVALID")

    def __repr__(self) -> str:
        return "RuntimeTrustReadback(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class AcceptedRuntimeTrustEvent:
    """Opaque proof that one fixed event's persisted row passed exact readback validation."""

    operation: RuntimeTrustOperation
    event_id: str
    payload_digest: str
    server_record_digest: str
    ledger_row_id: str
    snapshot_id: str | None
    statement_evaluated_at: datetime
    valid_until: datetime | None

    def __init__(
        self,
        *,
        operation: RuntimeTrustOperation,
        event_id: str,
        payload_digest: str,
        server_record_digest: str,
        ledger_row_id: str,
        snapshot_id: str | None,
        statement_evaluated_at: datetime,
        valid_until: datetime | None,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _ACCEPTANCE_PROOF_TOKEN:
            _fail("DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_PROOF_CONSTRUCTION_DENIED")
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "payload_digest", payload_digest)
        object.__setattr__(self, "server_record_digest", server_record_digest)
        object.__setattr__(self, "ledger_row_id", ledger_row_id)
        object.__setattr__(self, "snapshot_id", snapshot_id)
        object.__setattr__(self, "statement_evaluated_at", statement_evaluated_at)
        object.__setattr__(self, "valid_until", valid_until)

    def __repr__(self) -> str:
        return f"AcceptedRuntimeTrustEvent(operation={self.operation.value}, <redacted>)"


def _canonical_payload_data(row: Mapping[str, object]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, _ in _LEDGER_COLUMNS:
        if name in _PAYLOAD_EXCLUSIONS:
            continue
        value = row[name]
        if name in _INTEGER_COLUMNS:
            result[name] = None if value is None else _decimal(cast(int, value))
        elif name == "expected_components":
            result[name] = [item.canonical() for item in cast(tuple[ExpectedComponent, ...], value)]
        elif name == "observed_components":
            result[name] = (
                None
                if value is None
                else [item.canonical() for item in cast(tuple[ObservedComponent, ...], value)]
            )
        else:
            result[name] = value
    return result


def derive_event_record(
    event: RuntimeTrustEvent,
    *,
    statement_evaluated_at: datetime,
    candidate_statement_evaluated_at: datetime | None = None,
    roster_statement_evaluated_at: datetime | None = None,
) -> DerivedEventRecord:
    """Recompute the exact stored digests for readback and cross-language vectors."""
    statement_time = _utc_datetime(statement_evaluated_at)
    row = _event_row(event)
    acceptance_digest: str | None = None
    valid_until: datetime | None = None
    snapshot_id: str | None = None
    if isinstance(event, SnapshotAccepted):
        if candidate_statement_evaluated_at is None or roster_statement_evaluated_at is None:
            _fail("DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_TIME_REQUIRED")
        candidate_time = _utc_datetime(candidate_statement_evaluated_at)
        roster_time = _utc_datetime(roster_statement_evaluated_at)
        candidate = event.candidate
        evidence = candidate.evidence
        graph = evidence.graph
        acceptance_digest = _digest(
            _Domain.ACCEPTANCE,
            {
                "event_id": event.event_id,
                "candidate_event_id": candidate.event_id,
                "candidate_digest": candidate.candidate_digest,
                "installation_digest": graph.identity.installation_digest,
                "workspace_digest": graph.identity.workspace_digest,
                "account_digest": graph.identity.account_digest,
                "manifest_digest": graph.identity.manifest_digest,
                "deployment_id": graph.deployment_id,
                "deployment_mode": graph.deployment_mode.value,
                "deployment_set_before_digest": evidence.deployment_set_before.digest,
                "deployment_set_after_digest": evidence.deployment_set_after.digest,
                "new_deployment_count": _decimal(evidence.new_deployment_count, 0, 1),
                "stable_graph_digest": graph.stable_graph_digest,
                "pre_start_machine_observation_digest": evidence.pre_start.digest,
                "post_start_machine_observation_digest": event.post_start.digest,
                "candidate_statement_evaluated_at": _timestamp(candidate_time),
                "roster_statement_evaluated_at": _timestamp(roster_time),
                "roster_anchor_event_id": candidate.roster_anchor_event_id,
                "roster_anchor_digest": candidate.roster_anchor_digest,
                "machine_observer_fingerprint": (evidence.pre_start.machine_observer_fingerprint),
                "roster_reviewer_fingerprint": (evidence.roster.roster_reviewer_fingerprint),
                "expected_component_count": _decimal(len(graph.expected_components), 1, 3),
                "expected_components": [item.canonical() for item in graph.expected_components],
                "observed_components": [item.canonical() for item in graph.observed_components],
            },
        )
        row["acceptance_digest"] = acceptance_digest
        valid_until = min(
            statement_time + timedelta(hours=24),
            roster_time + timedelta(hours=24),
        )
        if not roster_time <= candidate_time <= statement_time:
            _fail("DBTOBSB_RUNTIME_TRUST_ACCEPTANCE_TIME_INVALID")
    elif candidate_statement_evaluated_at is not None or roster_statement_evaluated_at is not None:
        _fail("DBTOBSB_RUNTIME_TRUST_UNEXPECTED_SERVER_TIME")
    payload_digest = _digest(_Domain.PAYLOAD, _canonical_payload_data(row))
    if isinstance(event, SnapshotAccepted):
        candidate = event.candidate
        graph = candidate.evidence.graph
        snapshot_id = _digest(
            _Domain.SNAPSHOT_ID,
            {
                "event_id": event.event_id,
                "candidate_event_id": candidate.event_id,
                "candidate_digest": candidate.candidate_digest,
                "acceptance_digest": acceptance_digest,
                "payload_digest": payload_digest,
                "installation_digest": graph.identity.installation_digest,
                "generation": _decimal(graph.identity.generation, 1),
                "deployment_id": graph.deployment_id,
                "deployment_mode": graph.deployment_mode.value,
                "deployment_set_before_digest": candidate.evidence.deployment_set_before.digest,
                "deployment_set_after_digest": candidate.evidence.deployment_set_after.digest,
                "new_deployment_count": _decimal(candidate.evidence.new_deployment_count, 0, 1),
                "stable_graph_digest": graph.stable_graph_digest,
                "pre_start_machine_observation_digest": candidate.evidence.pre_start.digest,
                "post_start_machine_observation_digest": event.post_start.digest,
                "candidate_statement_evaluated_at": _timestamp(
                    cast(datetime, candidate_statement_evaluated_at)
                ),
                "roster_statement_evaluated_at": _timestamp(
                    cast(datetime, roster_statement_evaluated_at)
                ),
                "acceptance_statement_evaluated_at": _timestamp(statement_time),
                "roster_anchor_event_id": candidate.roster_anchor_event_id,
                "roster_anchor_digest": candidate.roster_anchor_digest,
                "valid_until": _timestamp(cast(datetime, valid_until)),
                "expected_component_count": _decimal(len(graph.expected_components), 1, 3),
                "expected_components": [item.canonical() for item in graph.expected_components],
                "observed_components": [item.canonical() for item in graph.observed_components],
            },
        )
    server_record_digest = _digest(
        _Domain.SERVER_RECORD,
        {
            "event_id": event.event_id,
            "payload_digest": payload_digest,
            "snapshot_id": snapshot_id,
            "statement_evaluated_at": _timestamp(statement_time),
            "valid_until": None if valid_until is None else _timestamp(valid_until),
        },
    )
    ledger_row_id = _digest(
        _Domain.LEDGER_ROW_ID,
        {"event_id": event.event_id, "server_record_digest": server_record_digest},
    )
    return DerivedEventRecord(
        event_id=event.event_id,
        payload_digest=payload_digest,
        snapshot_id=snapshot_id,
        server_record_digest=server_record_digest,
        ledger_row_id=ledger_row_id,
        statement_evaluated_at=statement_time,
        valid_until=valid_until,
        acceptance_digest=acceptance_digest,
    )


def _operation_for_event(event: RuntimeTrustEvent) -> RuntimeTrustOperation:
    if isinstance(event, ManifestRegistered):
        return RuntimeTrustOperation.MANIFEST_REGISTERED
    if isinstance(event, TrustCandidate):
        return RuntimeTrustOperation.TRUST_CANDIDATE
    if isinstance(event, SnapshotAccepted):
        return RuntimeTrustOperation.SNAPSHOT_ACCEPTED
    if isinstance(event, SnapshotInvalidated):
        return RuntimeTrustOperation.SNAPSHOT_INVALIDATED
    _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")


def validate_event_readback(
    event: RuntimeTrustEvent,
    readback: RuntimeTrustReadback,
    *,
    candidate_statement_evaluated_at: datetime | None = None,
    roster_statement_evaluated_at: datetime | None = None,
) -> AcceptedRuntimeTrustEvent:
    """Validate one terminal readback and issue an opaque, non-forgeable acceptance proof.

    The validator never treats a successful Statement Execution response as proof. It requires
    one physical row, one value for every non-null digest axis, exact recomputation from the
    server-returned query-evaluation time, and operation-specific snapshot/validity nullability.
    A matching deterministic event ID with different payload evidence is reported as a conflict,
    never as a retry success.
    """
    if not isinstance(
        event, (ManifestRegistered, TrustCandidate, SnapshotAccepted, SnapshotInvalidated)
    ) or not isinstance(readback, RuntimeTrustReadback):
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_INVALID")
    if (
        readback.event_id == event.event_id
        and readback.distinct_payload_count != 1
        and readback.physical_row_count > 0
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_EVENT_CONFLICT")
    if (
        readback.physical_row_count != 1
        or readback.distinct_payload_count != 1
        or readback.distinct_server_record_count != 1
        or readback.distinct_ledger_row_count != 1
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_CARDINALITY_INVALID")
    if (
        readback.event_id is None
        or readback.payload_digest is None
        or readback.server_record_digest is None
        or readback.ledger_row_id is None
        or readback.statement_evaluated_at is None
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_INTEGRITY_INVALID")
    is_acceptance = isinstance(event, SnapshotAccepted)
    if (is_acceptance and (readback.snapshot_id is None or readback.valid_until is None)) or (
        not is_acceptance and (readback.snapshot_id is not None or readback.valid_until is not None)
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID")
    statement_time = _utc_datetime(readback.statement_evaluated_at)
    if is_acceptance:
        if candidate_statement_evaluated_at is None or roster_statement_evaluated_at is None:
            _fail("DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID")
        candidate_time = _utc_datetime(candidate_statement_evaluated_at)
        roster_time = _utc_datetime(roster_statement_evaluated_at)
        valid_until = _utc_datetime(readback.valid_until)
        if (
            not roster_time <= candidate_time <= statement_time
            or valid_until
            != min(statement_time + timedelta(hours=24), roster_time + timedelta(hours=24))
            or valid_until <= candidate_time
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID")
    elif candidate_statement_evaluated_at is not None or roster_statement_evaluated_at is not None:
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_CHRONOLOGY_INVALID")
    expected = derive_event_record(
        event,
        statement_evaluated_at=readback.statement_evaluated_at,
        candidate_statement_evaluated_at=candidate_statement_evaluated_at,
        roster_statement_evaluated_at=roster_statement_evaluated_at,
    )
    if (
        readback.event_id == expected.event_id
        and readback.payload_digest != expected.payload_digest
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_EVENT_CONFLICT")
    if (
        readback.event_id != expected.event_id
        or readback.payload_digest != expected.payload_digest
        or readback.server_record_digest != expected.server_record_digest
        or readback.ledger_row_id != expected.ledger_row_id
        or readback.snapshot_id != expected.snapshot_id
        or readback.valid_until != expected.valid_until
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_READBACK_INTEGRITY_INVALID")
    return AcceptedRuntimeTrustEvent(
        operation=_operation_for_event(event),
        event_id=expected.event_id,
        payload_digest=expected.payload_digest,
        server_record_digest=expected.server_record_digest,
        ledger_row_id=expected.ledger_row_id,
        snapshot_id=expected.snapshot_id,
        statement_evaluated_at=statement_time,
        valid_until=expected.valid_until,
        _construction_token=_ACCEPTANCE_PROOF_TOKEN,
    )


@dataclass(frozen=True, slots=True, repr=False)
class RuntimeTrustStatement:
    """Opaque statement created only by this module's closed renderers."""

    kind: RuntimeTrustStatementKind
    semantic_sha256: str
    _text: str = field(repr=False)

    def __init__(
        self,
        *,
        kind: RuntimeTrustStatementKind,
        text: str,
        _construction_token: object,
    ) -> None:
        if (
            _construction_token is not _STATEMENT_TOKEN
            or not isinstance(kind, RuntimeTrustStatementKind)
            or not isinstance(text, str)
            or not text
            or ";" in text
        ):
            _fail("DBTOBSB_RUNTIME_TRUST_STATEMENT_CONSTRUCTION_DENIED")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "semantic_sha256", hashlib.sha256(text.encode()).hexdigest())
        object.__setattr__(self, "_text", text)

    def _transport_text(self) -> str:
        """Package-private bridge for the signed one-operation transport."""
        return self._text

    def __repr__(self) -> str:
        return f"RuntimeTrustStatement(kind={self.kind.value}, <redacted>)"


def _statement(kind: RuntimeTrustStatementKind, text: str) -> RuntimeTrustStatement:
    return RuntimeTrustStatement(kind=kind, text=text, _construction_token=_STATEMENT_TOKEN)


_LEDGER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("ledger_row_id", "STRING NOT NULL"),
    ("event_id", "STRING NOT NULL"),
    ("installation_digest", "STRING NOT NULL"),
    ("workspace_digest", "STRING NOT NULL"),
    ("account_digest", "STRING NOT NULL"),
    ("generation", "BIGINT NOT NULL"),
    ("operation", "STRING NOT NULL"),
    ("state", "STRING NOT NULL"),
    ("reason", "STRING NOT NULL"),
    ("contract_version", "STRING NOT NULL"),
    ("manifest_digest", "STRING NOT NULL"),
    ("predecessor_event_id", "STRING"),
    ("prior_generation", "BIGINT"),
    ("prior_snapshot_id", "STRING"),
    ("candidate_event_id", "STRING"),
    ("snapshot_id", "STRING"),
    ("target_event_id", "STRING"),
    ("target_snapshot_id", "STRING"),
    ("expected_component_count", "INT NOT NULL"),
    (
        "expected_components",
        "ARRAY<STRUCT<component_key:STRING,contract_digest:STRING>> NOT NULL",
    ),
    (
        "observed_components",
        "ARRAY<STRUCT<component_key:STRING,contract_digest:STRING,observation_digest:STRING>>",
    ),
    ("app_digest", "STRING"),
    ("deployment_id", "STRING"),
    ("deployment_mode", "STRING"),
    ("deployment_set_before_digest", "STRING"),
    ("deployment_set_after_digest", "STRING"),
    ("new_deployment_count", "INT"),
    ("direct_plan_digest", "STRING"),
    ("direct_lineage_digest", "STRING"),
    ("direct_state_serial", "BIGINT"),
    ("resource_selection_digest", "STRING"),
    ("source_digest", "STRING"),
    ("build_digest", "STRING"),
    ("artifact_digest", "STRING"),
    ("configuration_digest", "STRING"),
    ("app_resource_digest", "STRING"),
    ("acl_digest", "STRING"),
    ("job_run_as_digest", "STRING"),
    ("uc_grant_digest", "STRING"),
    ("group_root_digest", "STRING"),
    ("service_principal_set_digest", "STRING"),
    ("expected_roster_digest", "STRING"),
    ("observed_roster_digest", "STRING"),
    ("stable_graph_digest", "STRING"),
    ("pre_start_machine_observation_digest", "STRING"),
    ("pre_start_lifecycle_state", "STRING"),
    ("pre_start_active_deployment_id", "STRING"),
    ("pre_start_pending_deployment_count", "INT"),
    ("post_start_machine_observation_digest", "STRING"),
    ("post_start_lifecycle_state", "STRING"),
    ("post_start_active_deployment_id", "STRING"),
    ("post_start_pending_deployment_count", "INT"),
    ("machine_observer_fingerprint", "STRING"),
    ("roster_observation_digest", "STRING"),
    ("roster_reviewer_fingerprint", "STRING"),
    ("roster_anchor_event_id", "STRING"),
    ("roster_anchor_digest", "STRING"),
    ("candidate_digest", "STRING"),
    ("acceptance_digest", "STRING"),
    ("payload_digest", "STRING NOT NULL"),
    ("server_record_digest", "STRING NOT NULL"),
    ("statement_evaluated_at", "TIMESTAMP NOT NULL"),
    ("valid_until", "TIMESTAMP"),
    ("client_signer_fingerprint", "STRING"),
    ("client_signature_algorithm", "STRING"),
    ("client_signature", "STRING"),
)

_INTEGER_COLUMNS = frozenset(
    {
        "generation",
        "prior_generation",
        "expected_component_count",
        "new_deployment_count",
        "direct_state_serial",
        "pre_start_pending_deployment_count",
        "post_start_pending_deployment_count",
    }
)
_ARRAY_COLUMNS = frozenset({"expected_components", "observed_components"})
_PAYLOAD_EXCLUSIONS = frozenset(
    {
        "ledger_row_id",
        "snapshot_id",
        "payload_digest",
        "server_record_digest",
        "statement_evaluated_at",
        "valid_until",
        "client_signer_fingerprint",
        "client_signature_algorithm",
        "client_signature",
    }
)
_CLIENT_COLUMNS = tuple(
    name
    for name, _ in _LEDGER_COLUMNS
    if name
    not in {
        "ledger_row_id",
        "snapshot_id",
        "payload_digest",
        "server_record_digest",
        "statement_evaluated_at",
        "valid_until",
    }
)


def render_create_ledger_statement(names: RuntimeTrustObjectNames) -> RuntimeTrustStatement:
    """Render the exact managed Delta ledger DDL; no table property is inferred."""
    if not isinstance(names, RuntimeTrustObjectNames):
        _fail("DBTOBSB_RUNTIME_TRUST_IDENTIFIER_INVALID")
    columns = ",\n  ".join(f"{name} {data_type}" for name, data_type in _LEDGER_COLUMNS)
    return _statement(
        RuntimeTrustStatementKind.CREATE_LEDGER,
        f"/* DBTOBSB_RUNTIME_TRUST_LEDGER_DDL_V1 */\n"
        f"CREATE TABLE {names.ledger} (\n  {columns}\n) USING DELTA",
    )


def _sql_literal(value: str) -> str:
    # All dynamic values reaching this function have already passed a closed ASCII regex/enum.
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        _fail("DBTOBSB_RUNTIME_TRUST_SQL_LITERAL_INVALID")
    if "'" in value or "\\" in value or any(ord(character) < 32 for character in value):
        _fail("DBTOBSB_RUNTIME_TRUST_SQL_LITERAL_INVALID")
    return f"'{value}'"


def _sql_optional_string(value: str | None, data_type: str = "STRING") -> str:
    return f"CAST(NULL AS {data_type})" if value is None else _sql_literal(value)


def _sql_optional_int(value: int | None, data_type: str) -> str:
    return f"CAST(NULL AS {data_type})" if value is None else f"CAST({value} AS {data_type})"


def _sql_expected_components(values: Sequence[ExpectedComponent]) -> str:
    expected = _base_components(values)
    items = ", ".join(
        "named_struct('component_key', "
        f"{_sql_literal(item.component_key.value)}, 'contract_digest', "
        f"{_sql_literal(item.contract_digest)})"
        for item in expected
    )
    return f"array({items})"


def _sql_observed_components(values: Sequence[ObservedComponent] | None) -> str:
    if values is None:
        return (
            "CAST(NULL AS ARRAY<STRUCT<component_key:STRING,contract_digest:STRING,"
            "observation_digest:STRING>>)"
        )
    expected = tuple(ExpectedComponent(item.component_key, item.contract_digest) for item in values)
    observed = _observed_components(values, expected)
    items = ", ".join(
        "named_struct('component_key', "
        f"{_sql_literal(item.component_key.value)}, 'contract_digest', "
        f"{_sql_literal(item.contract_digest)}, 'observation_digest', "
        f"{_sql_literal(item.observation_digest)})"
        for item in observed
    )
    return f"array({items})"


def _json_string_sql(expression: str) -> str:
    return (
        f"CASE WHEN {expression} IS NULL THEN 'null' "
        f"ELSE concat(chr(34), {expression}, chr(34)) END"
    )


def _json_integer_sql(expression: str) -> str:
    return (
        f"CASE WHEN {expression} IS NULL THEN 'null' "
        f"ELSE concat(chr(34), CAST({expression} AS STRING), chr(34)) END"
    )


def _json_expected_components_sql(expression: str) -> str:
    return (
        "concat('[', array_join(transform("
        f'{expression}, c -> concat(\'{{"component_key":"\', c.component_key, '
        "'\",\"contract_digest\":\"', c.contract_digest, '\"}')), ','), ']')"
    )


def _json_observed_components_sql(expression: str) -> str:
    return (
        f"CASE WHEN {expression} IS NULL THEN 'null' ELSE concat('[', "
        f'array_join(transform({expression}, c -> concat(\'{{"component_key":"\', '
        'c.component_key, \'","contract_digest":"\', c.contract_digest, '
        "'\",\"observation_digest\":\"', c.observation_digest, '\"}')), ','), ']') END"
    )


def _json_timestamp_sql(expression: str) -> str:
    utc = f"convert_timezone('UTC', {expression})"
    formatted = (
        f"concat(date_format({utc}, 'yyyy-MM-dd'), 'T', date_format({utc}, 'HH:mm:ss.SSSSSS'), 'Z')"
    )
    return (
        f"CASE WHEN {expression} IS NULL THEN 'null' ELSE concat(chr(34), {formatted}, chr(34)) END"
    )


def _canonical_sql(domain: _Domain, fields: Mapping[str, str]) -> str:
    """Build JCS bytes from already JSON-encoded value expressions in sorted key order."""
    if not isinstance(domain, _Domain) or not isinstance(fields, dict):
        _fail("DBTOBSB_RUNTIME_TRUST_CANONICAL_SQL_INVALID")
    parts: list[str] = ["'{\"data\":{'"]
    for index, key in enumerate(sorted(fields)):
        if index:
            parts.append("','")
        parts.append(_sql_literal(f'"{key}":'))
        parts.append(fields[key])
    parts.extend(
        (
            _sql_literal('},"domain":"'),
            _sql_literal(domain.value),
            _sql_literal('"}'),
        )
    )
    return f"concat({', '.join(parts)})"


def _payload_digest_sql(alias: str) -> str:
    fields: dict[str, str] = {}
    for name, _ in _LEDGER_COLUMNS:
        if name in _PAYLOAD_EXCLUSIONS:
            continue
        expression = f"{alias}.{name}"
        if name in _INTEGER_COLUMNS:
            fields[name] = _json_integer_sql(expression)
        elif name == "expected_components":
            fields[name] = _json_expected_components_sql(expression)
        elif name == "observed_components":
            fields[name] = _json_observed_components_sql(expression)
        else:
            fields[name] = _json_string_sql(expression)
    return f"sha2({_canonical_sql(_Domain.PAYLOAD, fields)}, 256)"


def _event_id_sql(alias: str) -> str:
    return (
        "sha2("
        + _canonical_sql(
            _Domain.EVENT_ID,
            {
                "contract_version": _json_string_sql(f"{alias}.contract_version"),
                "installation_digest": _json_string_sql(f"{alias}.installation_digest"),
                "generation": _json_integer_sql(f"{alias}.generation"),
                "operation": _json_string_sql(f"{alias}.operation"),
                "predecessor_event_id": _json_string_sql(f"{alias}.predecessor_event_id"),
            },
        )
        + ", 256)"
    )


def _candidate_digest_sql(alias: str) -> str:
    strings = (
        "event_id",
        "predecessor_event_id",
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "manifest_digest",
        "deployment_id",
        "deployment_mode",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "stable_graph_digest",
        "pre_start_machine_observation_digest",
        "roster_observation_digest",
        "roster_anchor_event_id",
        "roster_anchor_digest",
        "machine_observer_fingerprint",
        "roster_reviewer_fingerprint",
    )
    fields = {name: _json_string_sql(f"{alias}.{name}") for name in strings}
    fields["new_deployment_count"] = _json_integer_sql(f"{alias}.new_deployment_count")
    fields["expected_component_count"] = _json_integer_sql(f"{alias}.expected_component_count")
    fields["expected_components"] = _json_expected_components_sql(f"{alias}.expected_components")
    fields["observed_components"] = _json_observed_components_sql(f"{alias}.observed_components")
    return f"sha2({_canonical_sql(_Domain.CANDIDATE, fields)}, 256)"


def _acceptance_digest_sql(alias: str) -> str:
    strings = (
        "event_id",
        "candidate_event_id",
        "candidate_digest",
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "manifest_digest",
        "deployment_id",
        "deployment_mode",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "stable_graph_digest",
        "pre_start_machine_observation_digest",
        "post_start_machine_observation_digest",
        "roster_anchor_event_id",
        "roster_anchor_digest",
        "machine_observer_fingerprint",
        "roster_reviewer_fingerprint",
    )
    fields = {name: _json_string_sql(f"{alias}.{name}") for name in strings}
    fields["new_deployment_count"] = _json_integer_sql(f"{alias}.new_deployment_count")
    fields["expected_component_count"] = _json_integer_sql(f"{alias}.expected_component_count")
    fields["expected_components"] = _json_expected_components_sql(f"{alias}.expected_components")
    fields["observed_components"] = _json_observed_components_sql(f"{alias}.observed_components")
    fields["candidate_statement_evaluated_at"] = _json_timestamp_sql(
        f"{alias}.candidate_statement_evaluated_at"
    )
    fields["roster_statement_evaluated_at"] = _json_timestamp_sql(
        f"{alias}.roster_statement_evaluated_at"
    )
    return f"sha2({_canonical_sql(_Domain.ACCEPTANCE, fields)}, 256)"


def _snapshot_id_sql(alias: str) -> str:
    strings = (
        "event_id",
        "candidate_event_id",
        "candidate_digest",
        "acceptance_digest",
        "payload_digest",
        "installation_digest",
        "deployment_id",
        "deployment_mode",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "stable_graph_digest",
        "pre_start_machine_observation_digest",
        "post_start_machine_observation_digest",
        "roster_anchor_event_id",
        "roster_anchor_digest",
    )
    fields = {name: _json_string_sql(f"{alias}.{name}") for name in strings}
    fields["generation"] = _json_integer_sql(f"{alias}.generation")
    fields["new_deployment_count"] = _json_integer_sql(f"{alias}.new_deployment_count")
    fields["expected_component_count"] = _json_integer_sql(f"{alias}.expected_component_count")
    fields["expected_components"] = _json_expected_components_sql(f"{alias}.expected_components")
    fields["observed_components"] = _json_observed_components_sql(f"{alias}.observed_components")
    for name in (
        "candidate_statement_evaluated_at",
        "roster_statement_evaluated_at",
        "acceptance_statement_evaluated_at",
        "valid_until",
    ):
        fields[name] = _json_timestamp_sql(f"{alias}.{name}")
    return f"sha2({_canonical_sql(_Domain.SNAPSHOT_ID, fields)}, 256)"


def _server_record_digest_sql(alias: str) -> str:
    return (
        "sha2("
        + _canonical_sql(
            _Domain.SERVER_RECORD,
            {
                "event_id": _json_string_sql(f"{alias}.event_id"),
                "payload_digest": _json_string_sql(f"{alias}.payload_digest"),
                "snapshot_id": _json_string_sql(f"{alias}.snapshot_id"),
                "statement_evaluated_at": _json_timestamp_sql(f"{alias}.statement_evaluated_at"),
                "valid_until": _json_timestamp_sql(f"{alias}.valid_until"),
            },
        )
        + ", 256)"
    )


def _ledger_row_id_sql(alias: str) -> str:
    return (
        "sha2("
        + _canonical_sql(
            _Domain.LEDGER_ROW_ID,
            {
                "event_id": _json_string_sql(f"{alias}.event_id"),
                "server_record_digest": _json_string_sql(f"{alias}.server_record_digest"),
            },
        )
        + ", 256)"
    )


def _stable_graph_digest_sql(alias: str) -> str:
    string_names = (
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "manifest_digest",
        "app_digest",
        "deployment_id",
        "deployment_mode",
        "deployment_set_after_digest",
        "direct_plan_digest",
        "direct_lineage_digest",
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
    )
    fields = {name: _json_string_sql(f"{alias}.{name}") for name in string_names}
    fields["direct_state_serial"] = _json_integer_sql(f"{alias}.direct_state_serial")
    fields["expected_component_count"] = _json_integer_sql(f"{alias}.expected_component_count")
    fields["expected_components"] = _json_expected_components_sql(f"{alias}.expected_components")
    fields["observed_components"] = _json_observed_components_sql(f"{alias}.observed_components")
    return f"sha2({_canonical_sql(_Domain.STABLE_GRAPH, fields)}, 256)"


def _machine_observation_digest_sql(alias: str, *, post_start: bool) -> str:
    prefix = "post_start" if post_start else "pre_start"
    phase = ObservationPhase.POST_START.value if post_start else ObservationPhase.PRE_START.value
    fields = {
        "phase": _json_string_sql(f"'{phase}'"),
        "installation_digest": _json_string_sql(f"{alias}.installation_digest"),
        "workspace_digest": _json_string_sql(f"{alias}.workspace_digest"),
        "account_digest": _json_string_sql(f"{alias}.account_digest"),
        "manifest_digest": _json_string_sql(f"{alias}.manifest_digest"),
        "deployment_id": _json_string_sql(f"{alias}.deployment_id"),
        "deployment_mode": _json_string_sql(f"{alias}.deployment_mode"),
        "deployment_set_after_digest": _json_string_sql(f"{alias}.deployment_set_after_digest"),
        "stable_graph_digest": _json_string_sql(f"{alias}.stable_graph_digest"),
        "lifecycle_state": _json_string_sql(f"{alias}.{prefix}_lifecycle_state"),
        "active_deployment_id": _json_string_sql(f"{alias}.{prefix}_active_deployment_id"),
        "pending_deployment_count": _json_integer_sql(f"{alias}.{prefix}_pending_deployment_count"),
        "machine_observer_fingerprint": _json_string_sql(f"{alias}.machine_observer_fingerprint"),
    }
    return f"sha2({_canonical_sql(_Domain.MACHINE_OBSERVATION, fields)}, 256)"


def _roster_observation_digest_sql(alias: str) -> str:
    fields = {
        "account_digest": _json_string_sql(f"{alias}.account_digest"),
        "workspace_digest": _json_string_sql(f"{alias}.workspace_digest"),
        "service_principal_set_digest": _json_string_sql(f"{alias}.service_principal_set_digest"),
        "expected_roster_digest": _json_string_sql(f"{alias}.expected_roster_digest"),
        "observed_roster_digest": _json_string_sql(f"{alias}.observed_roster_digest"),
        "roster_reviewer_fingerprint": _json_string_sql(f"{alias}.roster_reviewer_fingerprint"),
        "expected_component_count": _json_integer_sql(f"{alias}.expected_component_count"),
        "expected_components": _json_expected_components_sql(f"{alias}.expected_components"),
        "observed_components": _json_observed_components_sql(f"{alias}.observed_components"),
    }
    return f"sha2({_canonical_sql(_Domain.ROSTER_OBSERVATION, fields)}, 256)"


def _blank_event_row() -> dict[str, object]:
    return {name: None for name in _CLIENT_COLUMNS}


def _common_event_row(
    event: RuntimeTrustEvent,
    *,
    operation: RuntimeTrustOperation,
    reason: str,
    predecessor_event_id: str | None,
    expected_components: Sequence[ExpectedComponent],
) -> dict[str, object]:
    if isinstance(event, (ManifestRegistered, SnapshotInvalidated)):
        identity = event.identity
    elif isinstance(event, TrustCandidate):
        identity = event.registration.identity
    else:
        identity = event.candidate.registration.identity
    row = _blank_event_row()
    row.update(
        {
            "event_id": event.event_id,
            "installation_digest": identity.installation_digest,
            "workspace_digest": identity.workspace_digest,
            "account_digest": identity.account_digest,
            "generation": identity.generation,
            "operation": operation.value,
            "state": operation.value,
            "reason": reason,
            "contract_version": _CONTRACT_VERSION,
            "manifest_digest": identity.manifest_digest,
            "predecessor_event_id": predecessor_event_id,
            "expected_component_count": len(expected_components),
            "expected_components": tuple(expected_components),
        }
    )
    return row


def _candidate_row(candidate: TrustCandidate) -> dict[str, object]:
    graph = candidate.evidence.graph
    pre = candidate.evidence.pre_start
    roster = candidate.evidence.roster
    row = _common_event_row(
        candidate,
        operation=RuntimeTrustOperation.TRUST_CANDIDATE,
        reason="PRE_START_OBSERVED",
        predecessor_event_id=candidate.registration.event_id,
        expected_components=graph.expected_components,
    )
    row.update(
        {
            "observed_components": graph.observed_components,
            "app_digest": graph.app_digest,
            "deployment_id": graph.deployment_id,
            "deployment_mode": graph.deployment_mode.value,
            "deployment_set_before_digest": candidate.evidence.deployment_set_before.digest,
            "deployment_set_after_digest": candidate.evidence.deployment_set_after.digest,
            "new_deployment_count": candidate.evidence.new_deployment_count,
            "direct_plan_digest": graph.direct_plan_digest,
            "direct_lineage_digest": graph.direct_lineage_digest,
            "direct_state_serial": graph.direct_state_serial,
            "resource_selection_digest": graph.resource_selection_digest,
            "source_digest": graph.source_digest,
            "build_digest": graph.build_digest,
            "artifact_digest": graph.artifact_digest,
            "configuration_digest": graph.configuration_digest,
            "app_resource_digest": graph.app_resource_digest,
            "acl_digest": graph.acl_digest,
            "job_run_as_digest": graph.job_run_as_digest,
            "uc_grant_digest": graph.uc_grant_digest,
            "group_root_digest": graph.group_root_digest,
            "service_principal_set_digest": graph.service_principal_set_digest,
            "expected_roster_digest": graph.expected_roster_digest,
            "observed_roster_digest": graph.observed_roster_digest,
            "stable_graph_digest": graph.stable_graph_digest,
            "pre_start_machine_observation_digest": pre.digest,
            "pre_start_lifecycle_state": pre.lifecycle_state.value,
            "pre_start_active_deployment_id": pre.active_deployment_id,
            "pre_start_pending_deployment_count": pre.pending_deployment_count,
            "machine_observer_fingerprint": pre.machine_observer_fingerprint,
            "roster_observation_digest": roster.digest,
            "roster_reviewer_fingerprint": roster.roster_reviewer_fingerprint,
            "roster_anchor_event_id": candidate.roster_anchor_event_id,
            "roster_anchor_digest": candidate.roster_anchor_digest,
            "candidate_digest": candidate.candidate_digest,
        }
    )
    return row


def _event_row(event: RuntimeTrustEvent) -> dict[str, object]:
    if isinstance(event, ManifestRegistered):
        row = _common_event_row(
            event,
            operation=RuntimeTrustOperation.MANIFEST_REGISTERED,
            reason=event.reason.value,
            predecessor_event_id=event.predecessor_event_id,
            expected_components=event.expected_components,
        )
        row["prior_generation"] = event.prior_generation
        row["prior_snapshot_id"] = event.prior_snapshot_id
        return row
    if isinstance(event, TrustCandidate):
        return _candidate_row(event)
    if isinstance(event, SnapshotAccepted):
        candidate = event.candidate
        row = _candidate_row(candidate)
        row.update(
            {
                "event_id": event.event_id,
                "operation": RuntimeTrustOperation.SNAPSHOT_ACCEPTED.value,
                "state": RuntimeTrustOperation.SNAPSHOT_ACCEPTED.value,
                "reason": "POST_START_MATCHED",
                "predecessor_event_id": candidate.event_id,
                "candidate_event_id": candidate.event_id,
                "post_start_machine_observation_digest": event.post_start.digest,
                "post_start_lifecycle_state": event.post_start.lifecycle_state.value,
                "post_start_active_deployment_id": event.post_start.active_deployment_id,
                "post_start_pending_deployment_count": event.post_start.pending_deployment_count,
                "acceptance_digest": None,
            }
        )
        return row
    if isinstance(event, SnapshotInvalidated):
        row = _common_event_row(
            event,
            operation=RuntimeTrustOperation.SNAPSHOT_INVALIDATED,
            reason=event.reason.value,
            predecessor_event_id=event.predecessor_event_id,
            expected_components=event.expected_components,
        )
        row["target_event_id"] = event.target_event_id
        row["target_snapshot_id"] = event.target_snapshot_id
        return row
    _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")


def _sql_value(name: str, value: object) -> str:
    data_type = dict(_LEDGER_COLUMNS)[name].replace(" NOT NULL", "")
    if name == "expected_components":
        if not isinstance(value, tuple):
            _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
        return _sql_expected_components(cast(tuple[ExpectedComponent, ...], value))
    if name == "observed_components":
        if value is not None and not isinstance(value, tuple):
            _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
        return _sql_observed_components(cast(tuple[ObservedComponent, ...] | None, value))
    if name in _INTEGER_COLUMNS:
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
        return _sql_optional_int(cast(int | None, value), data_type)
    if value is not None and not isinstance(value, str):
        _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
    return _sql_optional_string(value, data_type)


def _select_columns(alias: str, replacements: Mapping[str, str] | None = None) -> str:
    replacements = replacements or {}
    return ",\n    ".join(
        f"{replacements[name]} AS {name}" if name in replacements else f"{alias}.{name}"
        for name in _CLIENT_COLUMNS
    )


def _same_component_sql(left: str, right: str) -> str:
    return (
        f"{left}.expected_component_count = {right}.expected_component_count "
        f"AND {left}.expected_components = {right}.expected_components"
    )


def _candidate_preconditions_sql(names: RuntimeTrustObjectNames, alias: str) -> str:
    ledger = names.ledger
    pre_start_digest = _machine_observation_digest_sql(alias, post_start=False)
    registration_valid = _registration_row_valid_sql("registration", names)
    return f"""(
      SELECT count(*)
      FROM {ledger} generation_row
      WHERE generation_row.installation_digest = {alias}.installation_digest
        AND generation_row.generation = {alias}.generation
    ) = 1
    AND EXISTS (
      SELECT 1
      FROM {ledger} registration
      WHERE registration.event_id = {alias}.predecessor_event_id
        AND registration.installation_digest = {alias}.installation_digest
        AND registration.workspace_digest = {alias}.workspace_digest
        AND registration.account_digest = {alias}.account_digest
        AND registration.generation = {alias}.generation
        AND registration.operation = 'MANIFEST_REGISTERED'
        AND registration.state = 'MANIFEST_REGISTERED'
        AND registration.manifest_digest = {alias}.manifest_digest
        AND {_same_component_sql("registration", alias)}
        AND {registration_valid}
        AND (
          (registration.reason = 'UNCHANGED_REFRESH'
            AND {alias}.new_deployment_count = 0
            AND {alias}.deployment_set_before_digest = {alias}.deployment_set_after_digest)
          OR
          (registration.reason IN ('INSTALL', 'UPGRADE', 'ROLLBACK', 'CHANGED_REFRESH')
            AND {alias}.new_deployment_count = 1
            AND {alias}.deployment_set_before_digest <> {alias}.deployment_set_after_digest)
        )
    )
    AND (
      {alias}.new_deployment_count = 1
      OR EXISTS (
        SELECT 1 FROM {ledger} prior_accepted_graph
        WHERE prior_accepted_graph.installation_digest = {alias}.installation_digest
          AND prior_accepted_graph.generation = {alias}.generation - 1
          AND prior_accepted_graph.operation = 'SNAPSHOT_ACCEPTED'
          AND prior_accepted_graph.deployment_id = {alias}.deployment_id
          AND prior_accepted_graph.deployment_mode = {alias}.deployment_mode
          AND prior_accepted_graph.deployment_set_after_digest =
              {alias}.deployment_set_after_digest
          AND prior_accepted_graph.stable_graph_digest = {alias}.stable_graph_digest
      )
    )
    AND {alias}.event_id = {_event_id_sql(alias)}
    AND {alias}.stable_graph_digest = {_stable_graph_digest_sql(alias)}
    AND {alias}.pre_start_machine_observation_digest = {pre_start_digest}
    AND {alias}.roster_observation_digest = {_roster_observation_digest_sql(alias)}
    AND {alias}.expected_roster_digest = {alias}.observed_roster_digest
    AND {alias}.candidate_digest = {_candidate_digest_sql(alias)}
    AND (
      ({alias}.roster_anchor_event_id = {alias}.event_id
        AND {alias}.roster_anchor_digest = {alias}.roster_observation_digest)
      OR EXISTS (
        SELECT 1
        FROM {ledger} anchor
        JOIN {ledger} source_registration
          ON source_registration.installation_digest = anchor.installation_digest
         AND source_registration.generation = anchor.generation
         AND source_registration.operation = 'MANIFEST_REGISTERED'
        JOIN {ledger} source_acceptance
          ON source_acceptance.installation_digest = anchor.installation_digest
         AND source_acceptance.generation = anchor.generation
         AND source_acceptance.operation = 'SNAPSHOT_ACCEPTED'
         AND source_acceptance.candidate_event_id = anchor.event_id
         AND source_acceptance.predecessor_event_id = anchor.event_id
        JOIN {ledger} prior_acceptance
          ON prior_acceptance.installation_digest = {alias}.installation_digest
         AND prior_acceptance.generation = {alias}.generation - 1
         AND prior_acceptance.operation = 'SNAPSHOT_ACCEPTED'
        WHERE anchor.event_id = {alias}.roster_anchor_event_id
          AND anchor.operation = 'TRUST_CANDIDATE'
          AND anchor.installation_digest = {alias}.installation_digest
          AND anchor.roster_anchor_event_id = anchor.event_id
          AND anchor.roster_anchor_digest = anchor.roster_observation_digest
          AND anchor.roster_anchor_digest = {alias}.roster_anchor_digest
          AND anchor.account_digest = {alias}.account_digest
          AND anchor.workspace_digest = {alias}.workspace_digest
          AND anchor.service_principal_set_digest = {alias}.service_principal_set_digest
          AND anchor.expected_roster_digest = {alias}.expected_roster_digest
          AND anchor.observed_roster_digest = {alias}.observed_roster_digest
          AND anchor.roster_reviewer_fingerprint = {alias}.roster_reviewer_fingerprint
          AND anchor.expected_components = {alias}.expected_components
          AND anchor.observed_components = {alias}.observed_components
          AND prior_acceptance.roster_anchor_event_id = anchor.event_id
          AND prior_acceptance.roster_anchor_digest = anchor.roster_anchor_digest
          AND prior_acceptance.deployment_id = {alias}.deployment_id
          AND prior_acceptance.deployment_mode = {alias}.deployment_mode
          AND prior_acceptance.deployment_set_after_digest =
              {alias}.deployment_set_after_digest
          AND prior_acceptance.stable_graph_digest = {alias}.stable_graph_digest
          AND anchor.statement_evaluated_at <= {alias}.statement_evaluated_at
          AND {alias}.statement_evaluated_at < anchor.statement_evaluated_at + INTERVAL 24 HOURS
          AND EXISTS (
            SELECT 1 FROM {ledger} refresh_registration
            WHERE refresh_registration.event_id = {alias}.predecessor_event_id
              AND refresh_registration.operation = 'MANIFEST_REGISTERED'
              AND refresh_registration.reason = 'UNCHANGED_REFRESH'
          )
          AND (
            SELECT count(*) FROM {ledger} source_row
            WHERE source_row.installation_digest = anchor.installation_digest
              AND source_row.generation = anchor.generation
          ) = 3
      )
    )"""


def _registration_preconditions_sql(names: RuntimeTrustObjectNames, alias: str) -> str:
    ledger = names.ledger
    return f"""{alias}.event_id = {_event_id_sql(alias)}
    AND NOT EXISTS (
      SELECT 1 FROM {ledger} current_generation
      WHERE current_generation.installation_digest = {alias}.installation_digest
        AND current_generation.generation >= {alias}.generation
    )
    AND (
      ({alias}.generation = 1
        AND {alias}.predecessor_event_id IS NULL
        AND {alias}.prior_generation IS NULL
        AND {alias}.prior_snapshot_id IS NULL
        AND NOT EXISTS (
          SELECT 1 FROM {ledger} any_prior
          WHERE any_prior.installation_digest = {alias}.installation_digest
        ))
      OR
      ({alias}.generation > 1
        AND {alias}.prior_generation = {alias}.generation - 1
        AND EXISTS (
          SELECT 1 FROM {ledger} prior_terminal
          WHERE prior_terminal.event_id = {alias}.predecessor_event_id
            AND prior_terminal.installation_digest = {alias}.installation_digest
            AND prior_terminal.generation = {alias}.generation - 1
            AND prior_terminal.operation IN ('SNAPSHOT_ACCEPTED', 'SNAPSHOT_INVALIDATED')
            AND (
              (prior_terminal.operation = 'SNAPSHOT_ACCEPTED'
                AND {alias}.prior_snapshot_id = prior_terminal.snapshot_id)
              OR
              (prior_terminal.operation = 'SNAPSHOT_INVALIDATED'
                AND {alias}.prior_snapshot_id <=> prior_terminal.target_snapshot_id)
            )
            AND NOT EXISTS (
              SELECT 1 FROM {ledger} later_prior
              WHERE later_prior.installation_digest = prior_terminal.installation_digest
                AND later_prior.generation = prior_terminal.generation
                AND later_prior.predecessor_event_id = prior_terminal.event_id
            )
        ))
    )"""


def _acceptance_preconditions_sql(names: RuntimeTrustObjectNames, alias: str) -> str:
    ledger = names.ledger
    post_start_digest = _machine_observation_digest_sql(alias, post_start=True)
    candidate_valid = _candidate_row_valid_sql("candidate")
    anchor_valid = _candidate_row_valid_sql("anchor")
    repeated = (
        "workspace_digest",
        "account_digest",
        "manifest_digest",
        "expected_component_count",
        "expected_components",
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
    )
    equality = "\n          AND ".join(f"candidate.{name} <=> {alias}.{name}" for name in repeated)
    return f"""{alias}.event_id = {_event_id_sql(alias)}
    AND {alias}.acceptance_digest = {_acceptance_digest_sql(alias)}
    AND {alias}.post_start_machine_observation_digest = {post_start_digest}
    AND {alias}.post_start_machine_observation_digest <>
        {alias}.pre_start_machine_observation_digest
    AND (
      SELECT count(*) FROM {ledger} generation_row
      WHERE generation_row.installation_digest = {alias}.installation_digest
        AND generation_row.generation = {alias}.generation
    ) = 2
    AND EXISTS (
      SELECT 1 FROM {ledger} candidate
      WHERE candidate.event_id = {alias}.candidate_event_id
        AND candidate.event_id = {alias}.predecessor_event_id
        AND candidate.installation_digest = {alias}.installation_digest
        AND candidate.generation = {alias}.generation
        AND candidate.operation = 'TRUST_CANDIDATE'
        AND candidate.state = 'TRUST_CANDIDATE'
        AND {candidate_valid}
        AND {equality}
        AND candidate.statement_evaluated_at = {alias}.candidate_statement_evaluated_at
    )
    AND (
      SELECT count(*) FROM {ledger} exact_candidate
      WHERE exact_candidate.event_id = {alias}.candidate_event_id
        AND exact_candidate.operation = 'TRUST_CANDIDATE'
    ) = 1
    AND EXISTS (
      SELECT 1 FROM {ledger} anchor
      WHERE anchor.event_id = {alias}.roster_anchor_event_id
        AND anchor.operation = 'TRUST_CANDIDATE'
        AND anchor.roster_anchor_event_id = anchor.event_id
        AND anchor.roster_anchor_digest = {alias}.roster_anchor_digest
        AND anchor.statement_evaluated_at = {alias}.roster_statement_evaluated_at
        AND {anchor_valid}
    )
    AND (
      SELECT count(*) FROM {ledger} exact_anchor
      WHERE exact_anchor.event_id = {alias}.roster_anchor_event_id
        AND exact_anchor.operation = 'TRUST_CANDIDATE'
    ) = 1"""


def _invalidation_preconditions_sql(names: RuntimeTrustObjectNames, alias: str) -> str:
    ledger = names.ledger
    return f"""{alias}.event_id = {_event_id_sql(alias)}
    AND EXISTS (
      SELECT 1 FROM {ledger} predecessor
      WHERE predecessor.event_id = {alias}.predecessor_event_id
        AND predecessor.installation_digest = {alias}.installation_digest
        AND predecessor.generation = {alias}.generation
        AND predecessor.event_id = {alias}.target_event_id
        AND predecessor.snapshot_id <=> {alias}.target_snapshot_id
    )
    AND NOT EXISTS (
      SELECT 1 FROM {ledger} successor
      WHERE successor.installation_digest = {alias}.installation_digest
        AND successor.generation = {alias}.generation
        AND successor.predecessor_event_id = {alias}.predecessor_event_id
    )"""


def _append_sql(names: RuntimeTrustObjectNames, event: RuntimeTrustEvent) -> str:
    row = _event_row(event)
    input_projection = ",\n    ".join(
        f"{_sql_value(name, row[name])} AS {name}" for name in _CLIENT_COLUMNS
    )
    acceptance = isinstance(event, SnapshotAccepted)
    if acceptance:
        linked_predicate = f"""FROM input_value i
  JOIN {names.ledger} candidate
    ON candidate.event_id = i.candidate_event_id
   AND candidate.operation = 'TRUST_CANDIDATE'
  JOIN {names.ledger} anchor
    ON anchor.event_id = i.roster_anchor_event_id
   AND anchor.operation = 'TRUST_CANDIDATE'"""
        linked_times = (
            "candidate.statement_evaluated_at AS candidate_statement_evaluated_at,\n"
            "    anchor.statement_evaluated_at AS roster_statement_evaluated_at"
        )
    else:
        linked_predicate = "FROM input_value i"
        linked_times = (
            "CAST(NULL AS TIMESTAMP) AS candidate_statement_evaluated_at,\n"
            "    CAST(NULL AS TIMESTAMP) AS roster_statement_evaluated_at"
        )
    accepted_projection = _select_columns(
        "l",
        {
            "acceptance_digest": (
                _acceptance_digest_sql("l") if acceptance else "l.acceptance_digest"
            )
        },
    )
    valid_until = (
        "least(c.statement_evaluated_at + INTERVAL 24 HOURS, "
        "p.roster_statement_evaluated_at + INTERVAL 24 HOURS)"
        if acceptance
        else "CAST(NULL AS TIMESTAMP)"
    )
    snapshot_id = _snapshot_id_sql("v") if acceptance else "CAST(NULL AS STRING)"
    if isinstance(event, ManifestRegistered):
        preconditions = _registration_preconditions_sql(names, "f")
    elif isinstance(event, TrustCandidate):
        preconditions = _candidate_preconditions_sql(names, "f")
    elif isinstance(event, SnapshotAccepted):
        preconditions = _acceptance_preconditions_sql(names, "f")
    else:
        preconditions = _invalidation_preconditions_sql(names, "f")
    final_columns = ", ".join(name for name, _ in _LEDGER_COLUMNS)
    insert_values = ", ".join(f"source.{name}" for name, _ in _LEDGER_COLUMNS)
    return f"""/* DBTOBSB_RUNTIME_TRUST_EVENT_V1 */
WITH input_value AS (
  SELECT
    {input_projection}
),
linked AS (
  SELECT
    {_select_columns("i")},
    {linked_times}
  {linked_predicate}
),
accepted AS (
  SELECT
    {accepted_projection},
    l.candidate_statement_evaluated_at,
    l.roster_statement_evaluated_at
  FROM linked l
),
payloaded AS (
  SELECT
    a.*,
    {_payload_digest_sql("a")} AS payload_digest
  FROM accepted a
),
query_clock AS (
  SELECT current_timestamp() AS statement_evaluated_at
),
validated_time AS (
  SELECT
    p.*,
    c.statement_evaluated_at,
    {valid_until} AS valid_until,
    c.statement_evaluated_at AS acceptance_statement_evaluated_at
  FROM payloaded p
  CROSS JOIN query_clock c
),
snapshotted AS (
  SELECT
    v.*,
    {snapshot_id} AS snapshot_id
  FROM validated_time v
),
recorded AS (
  SELECT
    s.*,
    {_server_record_digest_sql("s")} AS server_record_digest
  FROM snapshotted s
),
finalized AS (
  SELECT
    r.*,
    {_ledger_row_id_sql("r")} AS ledger_row_id
  FROM recorded r
),
eligible AS (
  SELECT f.*
  FROM finalized f
  WHERE {preconditions}
)
MERGE INTO {names.ledger} AS target
USING eligible AS source
ON target.event_id = source.event_id
WHEN NOT MATCHED THEN INSERT ({final_columns})
VALUES ({insert_values})"""


def render_append_event_statement(
    names: RuntimeTrustObjectNames,
    event: RuntimeTrustEvent,
) -> RuntimeTrustStatement:
    """Render one fixed idempotent event append; arbitrary SQL/events are impossible."""
    if not isinstance(names, RuntimeTrustObjectNames) or not isinstance(
        event, (ManifestRegistered, TrustCandidate, SnapshotAccepted, SnapshotInvalidated)
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
    return _statement(RuntimeTrustStatementKind.APPEND_EVENT, _append_sql(names, event))


def render_event_readback_statement(
    names: RuntimeTrustObjectNames,
    event: RuntimeTrustEvent,
) -> RuntimeTrustStatement:
    """Return fixed post-write evidence; callers must require physical_row_count exactly one."""
    if not isinstance(names, RuntimeTrustObjectNames) or not isinstance(
        event, (ManifestRegistered, TrustCandidate, SnapshotAccepted, SnapshotInvalidated)
    ):
        _fail("DBTOBSB_RUNTIME_TRUST_EVENT_INVALID")
    event_id = _sql_literal(event.event_id)
    text = f"""/* DBTOBSB_RUNTIME_TRUST_EVENT_READBACK_V1 */
SELECT
  count(*) AS physical_row_count,
  min(event_id) AS event_id,
  min(payload_digest) AS payload_digest,
  min(server_record_digest) AS server_record_digest,
  min(ledger_row_id) AS ledger_row_id,
  min(snapshot_id) AS snapshot_id,
  min(statement_evaluated_at) AS statement_evaluated_at,
  min(valid_until) AS valid_until,
  count(DISTINCT payload_digest) AS distinct_payload_count,
  count(DISTINCT server_record_digest) AS distinct_server_record_count,
  count(DISTINCT ledger_row_id) AS distinct_ledger_row_count
FROM {names.ledger}
WHERE event_id = {event_id}"""
    return _statement(RuntimeTrustStatementKind.READBACK_EVENT, text)


_COMMON_REQUIRED = frozenset(
    {
        "ledger_row_id",
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
        "payload_digest",
        "server_record_digest",
        "statement_evaluated_at",
    }
)
_SIGNATURE_COLUMNS = frozenset(
    {"client_signer_fingerprint", "client_signature_algorithm", "client_signature"}
)
_CANDIDATE_REQUIRED = frozenset(
    {
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
)
_ACCEPTANCE_EXTRA_REQUIRED = frozenset(
    {
        "candidate_event_id",
        "snapshot_id",
        "post_start_machine_observation_digest",
        "post_start_lifecycle_state",
        "post_start_active_deployment_id",
        "post_start_pending_deployment_count",
        "acceptance_digest",
        "valid_until",
    }
)
_HEX_COLUMNS = frozenset(
    {
        "ledger_row_id",
        "event_id",
        "installation_digest",
        "workspace_digest",
        "account_digest",
        "manifest_digest",
        "predecessor_event_id",
        "prior_snapshot_id",
        "candidate_event_id",
        "snapshot_id",
        "target_event_id",
        "target_snapshot_id",
        "app_digest",
        "deployment_set_before_digest",
        "deployment_set_after_digest",
        "direct_plan_digest",
        "direct_lineage_digest",
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
        "post_start_machine_observation_digest",
        "machine_observer_fingerprint",
        "roster_observation_digest",
        "roster_reviewer_fingerprint",
        "roster_anchor_event_id",
        "roster_anchor_digest",
        "candidate_digest",
        "acceptance_digest",
        "payload_digest",
        "server_record_digest",
        "client_signer_fingerprint",
    }
)


def _matrix_sql(
    alias: str,
    *,
    operation: RuntimeTrustOperation,
    required: frozenset[str],
    conditional: frozenset[str] = frozenset(),
) -> str:
    checks: list[str] = []
    for name, _ in _LEDGER_COLUMNS:
        if name in required:
            checks.append(f"{alias}.{name} IS NOT NULL")
        elif name not in conditional and name not in _SIGNATURE_COLUMNS:
            checks.append(f"{alias}.{name} IS NULL")
    checks.extend(
        (
            f"{alias}.operation = '{operation.value}'",
            f"{alias}.state = '{operation.value}'",
            f"{alias}.contract_version = '{_CONTRACT_VERSION}'",
            f"{alias}.generation BETWEEN 1 AND {_MAX_BIGINT}",
            f"{alias}.expected_component_count = 1",
            f"size({alias}.expected_components) = 1",
            f"{alias}.expected_components[0].component_key = 'BASE_OBSERVABILITY'",
            f"{alias}.expected_components[0].contract_digest RLIKE '^[0-9a-f]{{64}}$'",
            "(("
            f"{alias}.client_signer_fingerprint IS NULL AND "
            f"{alias}.client_signature_algorithm IS NULL AND {alias}.client_signature IS NULL"
            ") OR ("
            f"{alias}.client_signer_fingerprint RLIKE '^[0-9a-f]{{64}}$' AND "
            f"{alias}.client_signature_algorithm = 'ED25519' AND "
            f"{alias}.client_signature RLIKE '^[0-9a-f]{{128}}$'))",
        )
    )
    for name in sorted(_HEX_COLUMNS):
        checks.append(f"({alias}.{name} IS NULL OR {alias}.{name} RLIKE '^[0-9a-f]{{64}}$')")
    checks.append(
        f"({alias}.deployment_id IS NULL OR {alias}.deployment_id RLIKE '^[0-9a-f]{{32}}$')"
    )
    checks.append(
        f"({alias}.pre_start_active_deployment_id IS NULL OR "
        f"{alias}.pre_start_active_deployment_id RLIKE '^[0-9a-f]{{32}}$')"
    )
    checks.append(
        f"({alias}.post_start_active_deployment_id IS NULL OR "
        f"{alias}.post_start_active_deployment_id RLIKE '^[0-9a-f]{{32}}$')"
    )
    return "\n      AND ".join(checks)


def _stored_record_integrity_sql(alias: str, *, include_payload: bool = True) -> str:
    checks = [
        f"{alias}.event_id = {_event_id_sql(alias)}",
        f"{alias}.server_record_digest = {_server_record_digest_sql(alias)}",
        f"{alias}.ledger_row_id = {_ledger_row_id_sql(alias)}",
    ]
    if include_payload:
        checks.insert(1, f"{alias}.payload_digest = {_payload_digest_sql(alias)}")
    return "\n      AND ".join(checks)


def _registration_row_valid_sql(alias: str, names: RuntimeTrustObjectNames) -> str:
    required = _COMMON_REQUIRED
    conditional = frozenset({"predecessor_event_id", "prior_generation", "prior_snapshot_id"})
    matrix = _matrix_sql(
        alias,
        operation=RuntimeTrustOperation.MANIFEST_REGISTERED,
        required=required,
        conditional=conditional,
    )
    reasons = ", ".join(f"'{item.value}'" for item in RegistrationReason)
    return f"""{matrix}
      AND {alias}.reason IN ({reasons})
      AND (({alias}.generation = 1 AND {alias}.reason = 'INSTALL')
        OR ({alias}.generation > 1 AND {alias}.reason <> 'INSTALL'))
      AND {_stored_record_integrity_sql(alias)}
      AND (
        ({alias}.generation = 1
          AND {alias}.predecessor_event_id IS NULL
          AND {alias}.prior_generation IS NULL
          AND {alias}.prior_snapshot_id IS NULL)
        OR
        ({alias}.generation > 1
          AND {alias}.predecessor_event_id IS NOT NULL
          AND {alias}.prior_generation = {alias}.generation - 1
          AND EXISTS (
            SELECT 1 FROM {names.ledger} prior_terminal
            WHERE prior_terminal.event_id = {alias}.predecessor_event_id
              AND prior_terminal.installation_digest = {alias}.installation_digest
              AND prior_terminal.generation = {alias}.generation - 1
              AND prior_terminal.operation IN ('SNAPSHOT_ACCEPTED', 'SNAPSHOT_INVALIDATED')
              AND (
                (prior_terminal.operation = 'SNAPSHOT_ACCEPTED'
                  AND {alias}.prior_snapshot_id = prior_terminal.snapshot_id)
                OR
                (prior_terminal.operation = 'SNAPSHOT_INVALIDATED'
                  AND {alias}.prior_snapshot_id <=> prior_terminal.target_snapshot_id)
              )
              AND (
                SELECT count(*) FROM {names.ledger} same_terminal
                WHERE same_terminal.event_id = prior_terminal.event_id
              ) = 1
          ))
      )"""


def _candidate_row_valid_sql(alias: str) -> str:
    required = _COMMON_REQUIRED | _CANDIDATE_REQUIRED
    matrix = _matrix_sql(
        alias,
        operation=RuntimeTrustOperation.TRUST_CANDIDATE,
        required=required,
    )
    return f"""{matrix}
      AND {alias}.reason = 'PRE_START_OBSERVED'
      AND {alias}.deployment_mode = 'SNAPSHOT'
      AND {alias}.new_deployment_count BETWEEN 0 AND 1
      AND {alias}.direct_state_serial BETWEEN 0 AND {_MAX_BIGINT}
      AND {alias}.pre_start_lifecycle_state = 'STOPPED'
      AND {alias}.pre_start_active_deployment_id = {alias}.deployment_id
      AND {alias}.pre_start_pending_deployment_count = 0
      AND size({alias}.observed_components) = 1
      AND {alias}.observed_components[0].component_key = 'BASE_OBSERVABILITY'
      AND {alias}.observed_components[0].contract_digest =
          {alias}.expected_components[0].contract_digest
      AND {alias}.observed_components[0].observation_digest RLIKE '^[0-9a-f]{{64}}$'
      AND {alias}.stable_graph_digest = {_stable_graph_digest_sql(alias)}
      AND {alias}.pre_start_machine_observation_digest =
          {_machine_observation_digest_sql(alias, post_start=False)}
      AND {alias}.roster_observation_digest = {_roster_observation_digest_sql(alias)}
      AND {alias}.expected_roster_digest = {alias}.observed_roster_digest
      AND {alias}.candidate_digest = {_candidate_digest_sql(alias)}
      AND {_stored_record_integrity_sql(alias)}"""


def _acceptance_row_matrix_sql(alias: str) -> str:
    required = _COMMON_REQUIRED | _CANDIDATE_REQUIRED | _ACCEPTANCE_EXTRA_REQUIRED
    matrix = _matrix_sql(
        alias,
        operation=RuntimeTrustOperation.SNAPSHOT_ACCEPTED,
        required=required,
    )
    return f"""{matrix}
      AND {alias}.reason = 'POST_START_MATCHED'
      AND {alias}.deployment_mode = 'SNAPSHOT'
      AND {alias}.new_deployment_count BETWEEN 0 AND 1
      AND {alias}.direct_state_serial BETWEEN 0 AND {_MAX_BIGINT}
      AND {alias}.pre_start_lifecycle_state = 'STOPPED'
      AND {alias}.pre_start_active_deployment_id = {alias}.deployment_id
      AND {alias}.pre_start_pending_deployment_count = 0
      AND {alias}.post_start_lifecycle_state = 'ACTIVE'
      AND {alias}.post_start_active_deployment_id = {alias}.deployment_id
      AND {alias}.post_start_pending_deployment_count = 0
      AND {alias}.post_start_machine_observation_digest <>
          {alias}.pre_start_machine_observation_digest
      AND size({alias}.observed_components) = 1
      AND {alias}.observed_components[0].component_key = 'BASE_OBSERVABILITY'
      AND {alias}.observed_components[0].contract_digest =
          {alias}.expected_components[0].contract_digest
      AND {alias}.observed_components[0].observation_digest RLIKE '^[0-9a-f]{{64}}$'
      AND {alias}.stable_graph_digest = {_stable_graph_digest_sql(alias)}
      AND {alias}.pre_start_machine_observation_digest =
          {_machine_observation_digest_sql(alias, post_start=False)}
      AND {alias}.post_start_machine_observation_digest =
          {_machine_observation_digest_sql(alias, post_start=True)}
      AND {alias}.roster_observation_digest = {_roster_observation_digest_sql(alias)}
      AND {alias}.expected_roster_digest = {alias}.observed_roster_digest"""


def _acceptance_derived_valid_sql(alias: str) -> str:
    return f"""{alias}.acceptance_digest = {_acceptance_digest_sql(alias)}
      AND {alias}.payload_digest = {_payload_digest_sql(alias)}
      AND {alias}.snapshot_id = {_snapshot_id_sql(alias)}
      AND {alias}.server_record_digest = {_server_record_digest_sql(alias)}
      AND {alias}.ledger_row_id = {_ledger_row_id_sql(alias)}
      AND {alias}.valid_until = least(
        {alias}.statement_evaluated_at + INTERVAL 24 HOURS,
        {alias}.roster_statement_evaluated_at + INTERVAL 24 HOURS
      )"""


def _invalidation_row_valid_sql(alias: str) -> str:
    required = _COMMON_REQUIRED | frozenset({"predecessor_event_id", "target_event_id"})
    matrix = _matrix_sql(
        alias,
        operation=RuntimeTrustOperation.SNAPSHOT_INVALIDATED,
        required=required,
        conditional=frozenset({"target_snapshot_id"}),
    )
    reasons = ", ".join(f"'{item.value}'" for item in InvalidationReason)
    return f"""{matrix}
      AND {alias}.reason IN ({reasons})
      AND {alias}.target_event_id = {alias}.predecessor_event_id
      AND {_stored_record_integrity_sql(alias)}"""


_CANDIDATE_REPEAT_COLUMNS = (
    "workspace_digest",
    "account_digest",
    "manifest_digest",
    "expected_component_count",
    "expected_components",
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
)


def render_create_status_view_statement(names: RuntimeTrustObjectNames) -> RuntimeTrustStatement:
    """Render the fail-closed, one-row-per-installation latest-generation status view."""
    if not isinstance(names, RuntimeTrustObjectNames):
        _fail("DBTOBSB_RUNTIME_TRUST_IDENTIFIER_INVALID")
    repeated = "\n      AND ".join(
        f"acceptance.{name} <=> candidate.{name}" for name in _CANDIDATE_REPEAT_COLUMNS
    )
    registration_valid = _registration_row_valid_sql("registration", names)
    candidate_valid = _candidate_row_valid_sql("candidate")
    acceptance_matrix = _acceptance_row_matrix_sql("acceptance")
    invalidation_valid = _invalidation_row_valid_sql("invalidation")
    original_derived = _acceptance_derived_valid_sql("original_ready")
    reused_derived = _acceptance_derived_valid_sql("reused_ready")
    current_derived = _acceptance_derived_valid_sql("anchored")
    ledger = names.ledger
    text = f"""/* DBTOBSB_RUNTIME_TRUST_STATUS_VIEW_V1 */
CREATE OR REPLACE VIEW {names.status_view} AS
WITH query_clock AS (
  SELECT current_timestamp() AS evaluated_at
),
latest_generation AS (
  SELECT installation_digest, max(generation) AS generation
  FROM {ledger}
  GROUP BY installation_digest
),
generation_counts AS (
  SELECT
    ledger_row.installation_digest,
    ledger_row.generation,
    count(*) AS physical_row_count,
    count_if(ledger_row.operation = 'MANIFEST_REGISTERED') AS registration_count,
    count_if(ledger_row.operation = 'TRUST_CANDIDATE') AS candidate_count,
    count_if(ledger_row.operation = 'SNAPSHOT_ACCEPTED') AS acceptance_count,
    count_if(ledger_row.operation = 'SNAPSHOT_INVALIDATED') AS invalidation_count,
    count(DISTINCT ledger_row.event_id) AS distinct_event_count,
    count(DISTINCT ledger_row.ledger_row_id) AS distinct_ledger_row_count,
    count(DISTINCT ledger_row.snapshot_id) AS distinct_snapshot_count
  FROM {ledger} ledger_row
  GROUP BY ledger_row.installation_digest, ledger_row.generation
),
raw_chains AS (
  SELECT
    acceptance.*,
    registration.reason AS registration_reason,
    registration.event_id AS registration_event_id,
    candidate.statement_evaluated_at AS candidate_statement_evaluated_at,
    acceptance.statement_evaluated_at AS acceptance_statement_evaluated_at
    ,registration.predecessor_event_id AS registration_predecessor_event_id
    ,registration.prior_snapshot_id AS registration_prior_snapshot_id
  FROM {ledger} registration
  JOIN {ledger} candidate
    ON candidate.installation_digest = registration.installation_digest
   AND candidate.generation = registration.generation
   AND candidate.operation = 'TRUST_CANDIDATE'
  JOIN {ledger} acceptance
    ON acceptance.installation_digest = registration.installation_digest
   AND acceptance.generation = registration.generation
   AND acceptance.operation = 'SNAPSHOT_ACCEPTED'
  JOIN generation_counts counts
    ON counts.installation_digest = registration.installation_digest
   AND counts.generation = registration.generation
  WHERE registration.operation = 'MANIFEST_REGISTERED'
    AND counts.physical_row_count = 3
    AND counts.registration_count = 1
    AND counts.candidate_count = 1
    AND counts.acceptance_count = 1
    AND counts.invalidation_count = 0
    AND counts.distinct_event_count = 3
    AND counts.distinct_ledger_row_count = 3
    AND counts.distinct_snapshot_count = 1
    AND candidate.predecessor_event_id = registration.event_id
    AND candidate.workspace_digest = registration.workspace_digest
    AND candidate.account_digest = registration.account_digest
    AND candidate.manifest_digest = registration.manifest_digest
    AND acceptance.predecessor_event_id = candidate.event_id
    AND acceptance.candidate_event_id = candidate.event_id
    AND acceptance.installation_digest = candidate.installation_digest
    AND acceptance.generation = candidate.generation
    AND acceptance.statement_evaluated_at >= candidate.statement_evaluated_at
    AND candidate.statement_evaluated_at >= registration.statement_evaluated_at
    AND registration.expected_components = candidate.expected_components
    AND {repeated}
    AND (
      (registration.reason = 'UNCHANGED_REFRESH'
        AND candidate.new_deployment_count = 0
        AND candidate.deployment_set_before_digest = candidate.deployment_set_after_digest)
      OR
      (registration.reason IN ('INSTALL', 'UPGRADE', 'ROLLBACK', 'CHANGED_REFRESH')
        AND candidate.new_deployment_count = 1
        AND candidate.deployment_set_before_digest <> candidate.deployment_set_after_digest)
    )
    AND {registration_valid}
    AND {candidate_valid}
    AND {acceptance_matrix}
),
original_ready AS (
  SELECT
    raw.*,
    raw.candidate_statement_evaluated_at AS roster_statement_evaluated_at
  FROM raw_chains raw
  WHERE raw.roster_anchor_event_id = raw.candidate_event_id
    AND raw.roster_anchor_digest = raw.roster_observation_digest
),
original_chains AS (
  SELECT original_ready.*
  FROM original_ready
  WHERE {original_derived}
),
reused_ready AS (
  SELECT
    raw.*,
    original.candidate_statement_evaluated_at AS roster_statement_evaluated_at
  FROM raw_chains raw
  JOIN original_chains original
    ON original.candidate_event_id = raw.roster_anchor_event_id
   AND original.installation_digest = raw.installation_digest
   AND original.roster_anchor_event_id = original.candidate_event_id
   AND original.roster_anchor_digest = raw.roster_anchor_digest
   AND original.account_digest = raw.account_digest
   AND original.workspace_digest = raw.workspace_digest
   AND original.service_principal_set_digest = raw.service_principal_set_digest
   AND original.expected_roster_digest = raw.expected_roster_digest
   AND original.observed_roster_digest = raw.observed_roster_digest
   AND original.roster_reviewer_fingerprint = raw.roster_reviewer_fingerprint
   AND original.expected_components = raw.expected_components
   AND original.observed_components = raw.observed_components
  WHERE raw.registration_reason = 'UNCHANGED_REFRESH'
    AND raw.roster_anchor_event_id <> raw.candidate_event_id
    AND original.candidate_statement_evaluated_at <=
        raw.candidate_statement_evaluated_at
    AND raw.candidate_statement_evaluated_at <
        original.candidate_statement_evaluated_at + INTERVAL 24 HOURS
),
reused_chains AS (
  SELECT reused_ready.*
  FROM reused_ready
  WHERE {reused_derived}
),
eligible_prior_chains AS (
  SELECT * FROM original_chains
  UNION ALL
  SELECT * FROM reused_chains
),
valid_invalidations AS (
  SELECT invalidation.*
  FROM {ledger} invalidation
  JOIN {ledger} target
    ON target.event_id = invalidation.target_event_id
   AND target.installation_digest = invalidation.installation_digest
   AND target.generation = invalidation.generation
   AND target.snapshot_id <=> invalidation.target_snapshot_id
  WHERE {invalidation_valid}
    AND invalidation.statement_evaluated_at >= target.statement_evaluated_at
    AND invalidation.expected_components = target.expected_components
    AND (
      SELECT count(*) FROM {ledger} exact_target
      WHERE exact_target.event_id = invalidation.target_event_id
    ) = 1
    AND (
      SELECT count(*) FROM {ledger} generation_row
      WHERE generation_row.installation_digest = invalidation.installation_digest
        AND generation_row.generation = invalidation.generation
    ) = CASE target.operation
          WHEN 'MANIFEST_REGISTERED' THEN 2
          WHEN 'TRUST_CANDIDATE' THEN 3
          WHEN 'SNAPSHOT_ACCEPTED' THEN 4
          ELSE -1
        END
    AND (
      (target.operation = 'MANIFEST_REGISTERED'
        AND {_registration_row_valid_sql("target", names)})
      OR
      (target.operation = 'TRUST_CANDIDATE'
        AND {_candidate_row_valid_sql("target")}
        AND EXISTS (
          SELECT 1 FROM {ledger} target_registration
          WHERE target_registration.event_id = target.predecessor_event_id
            AND target_registration.installation_digest = target.installation_digest
            AND target_registration.generation = target.generation
            AND target_registration.expected_components = target.expected_components
            AND {_registration_row_valid_sql("target_registration", names)}
        ))
      OR
      (target.operation = 'SNAPSHOT_ACCEPTED'
        AND EXISTS (
          SELECT 1 FROM eligible_prior_chains accepted_target
          WHERE accepted_target.event_id = target.event_id
            AND accepted_target.snapshot_id = target.snapshot_id
        ))
    )
),
anchored AS (
  SELECT
    raw.*,
    CASE
      WHEN raw.roster_anchor_event_id = raw.candidate_event_id
        THEN raw.candidate_statement_evaluated_at
      ELSE original.candidate_statement_evaluated_at
    END AS roster_statement_evaluated_at
  FROM raw_chains raw
  LEFT JOIN original_chains original
    ON original.candidate_event_id = raw.roster_anchor_event_id
   AND original.installation_digest = raw.installation_digest
   AND original.roster_anchor_event_id = original.candidate_event_id
   AND original.roster_anchor_digest = raw.roster_anchor_digest
   AND original.account_digest = raw.account_digest
   AND original.workspace_digest = raw.workspace_digest
   AND original.service_principal_set_digest = raw.service_principal_set_digest
   AND original.expected_roster_digest = raw.expected_roster_digest
   AND original.observed_roster_digest = raw.observed_roster_digest
   AND original.roster_reviewer_fingerprint = raw.roster_reviewer_fingerprint
   AND original.expected_components = raw.expected_components
   AND original.observed_components = raw.observed_components
  WHERE
    (raw.roster_anchor_event_id = raw.candidate_event_id
      AND raw.roster_anchor_digest = raw.roster_observation_digest)
    OR
    (raw.registration_reason = 'UNCHANGED_REFRESH'
      AND raw.roster_anchor_event_id <> raw.candidate_event_id
      AND original.candidate_event_id IS NOT NULL
      AND original.candidate_statement_evaluated_at <=
          raw.candidate_statement_evaluated_at
      AND raw.candidate_statement_evaluated_at <
          original.candidate_statement_evaluated_at + INTERVAL 24 HOURS
      AND EXISTS (
        SELECT 1 FROM eligible_prior_chains prior
        WHERE prior.installation_digest = raw.installation_digest
          AND prior.generation = raw.generation - 1
          AND prior.roster_anchor_event_id = original.candidate_event_id
          AND prior.roster_anchor_digest = original.roster_anchor_digest
      ))
),
verified AS (
  SELECT anchored.*
  FROM anchored
  WHERE {current_derived}
),
lineage_verified AS (
  SELECT verified.*
  FROM verified
  WHERE (verified.generation = 1 AND verified.registration_reason = 'INSTALL')
    OR (verified.registration_reason = 'UNCHANGED_REFRESH' AND EXISTS (
      SELECT 1 FROM eligible_prior_chains prior_acceptance
      WHERE prior_acceptance.event_id = verified.registration_predecessor_event_id
        AND prior_acceptance.installation_digest = verified.installation_digest
        AND prior_acceptance.generation = verified.generation - 1
        AND prior_acceptance.snapshot_id = verified.registration_prior_snapshot_id
        AND prior_acceptance.deployment_id = verified.deployment_id
        AND prior_acceptance.deployment_mode = verified.deployment_mode
        AND prior_acceptance.deployment_set_after_digest =
            verified.deployment_set_after_digest
        AND prior_acceptance.stable_graph_digest = verified.stable_graph_digest
    ))
    OR (verified.registration_reason IN ('UPGRADE', 'ROLLBACK', 'CHANGED_REFRESH')
      AND (EXISTS (
        SELECT 1 FROM eligible_prior_chains prior_acceptance
        WHERE prior_acceptance.event_id = verified.registration_predecessor_event_id
          AND prior_acceptance.installation_digest = verified.installation_digest
          AND prior_acceptance.generation = verified.generation - 1
          AND prior_acceptance.snapshot_id = verified.registration_prior_snapshot_id
      ) OR EXISTS (
      SELECT 1 FROM valid_invalidations prior_invalidation
      WHERE prior_invalidation.event_id = verified.registration_predecessor_event_id
        AND prior_invalidation.installation_digest = verified.installation_digest
        AND prior_invalidation.generation = verified.generation - 1
        AND prior_invalidation.target_snapshot_id <=>
            verified.registration_prior_snapshot_id
    )))
),
latest_verified AS (
  SELECT verified.*
  FROM lineage_verified verified
  JOIN latest_generation latest
    ON latest.installation_digest = verified.installation_digest
   AND latest.generation = verified.generation
)
SELECT
  verified.installation_digest,
  verified.workspace_digest,
  verified.account_digest,
  verified.generation,
  verified.snapshot_id,
  verified.deployment_id,
  verified.deployment_mode,
  verified.deployment_set_before_digest,
  verified.deployment_set_after_digest,
  verified.stable_graph_digest,
  verified.pre_start_machine_observation_digest,
  verified.post_start_machine_observation_digest,
  verified.roster_anchor_event_id,
  verified.roster_anchor_digest,
  verified.expected_components,
  verified.observed_components,
  verified.candidate_statement_evaluated_at AS pre_start_statement_evaluated_at,
  verified.statement_evaluated_at AS post_start_statement_evaluated_at,
  verified.roster_statement_evaluated_at,
  verified.statement_evaluated_at AS machine_evidence_at,
  verified.roster_statement_evaluated_at AS roster_evidence_at,
  least(
    verified.statement_evaluated_at,
    verified.roster_statement_evaluated_at
  ) AS oldest_evidence_at,
  verified.valid_until,
  clock.evaluated_at,
  '{_QUALIFIER}' AS qualifier,
  CASE
    WHEN clock.evaluated_at >= verified.valid_until THEN 'RUNTIME_TRUST_STALE'
    ELSE 'RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED'
  END AS state
FROM latest_verified verified
CROSS JOIN query_clock clock"""
    return _statement(RuntimeTrustStatementKind.CREATE_STATUS_VIEW, text)


def runtime_trust_provider_contract_sha256() -> str:
    """Digest the closed provider DDL/reducer contract using fixed placeholder names."""
    names = RuntimeTrustObjectNames("dbtobsb_contract", "base_observability")
    contract = {
        "contract_version": _CONTRACT_VERSION,
        "domains": [domain.value for domain in _Domain],
        "identifier_policy": RUNTIME_TRUST_V1_IDENTIFIER_POLICY,
        "operations": [operation.value for operation in RuntimeTrustOperation],
        "qualifier": _QUALIFIER,
        "ledger_ddl": render_create_ledger_statement(names)._transport_text(),
        "status_view_sql": render_create_status_view_statement(names)._transport_text(),
    }
    rendered = json.dumps(
        contract,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(rendered).hexdigest()
