"""Fail-closed fresh-install Databricks App deployment reconciliation.

This module owns no CLI command construction and accepts no deployment identifier from a user.
The production adapter supplies closed operations for the one pinned Bundle-runner invocation,
App stop, paginated deployment inventory, and App observation.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

_DEPLOYMENT_ID = re.compile(r"^[0-9a-f]{32}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_DEPLOYMENT_PAGES = 100
_STOP_TIMEOUT_SECONDS = 20 * 60
_POLL_INTERVAL_SECONDS = 2.0
_MAX_RECONCILIATION_PAGES = _MAX_DEPLOYMENT_PAGES * (
    2 + math.ceil(_STOP_TIMEOUT_SECONDS / _POLL_INTERVAL_SECONDS)
)
_monotonic = time.monotonic
_sleep = time.sleep
_RECONCILED_TOKEN = object()
_EXPECTED_COMMAND = ("uvicorn", "dbtobsb_app.main:app")
_EXPECTED_ENVIRONMENT = tuple(
    sorted(
        (
            ("DBTOBSB_WAREHOUSE_ID", "dbtobsb-app-warehouse"),
            ("DBTOBSB_RUNTIME_TRUST_STATUS_VIEW", "dbtobsb-runtime-trust-status"),
            ("DBTOBSB_RUN_HEALTH_VIEW", "dbtobsb-run-health"),
            ("DBTOBSB_NODE_HEALTH_VIEW", "dbtobsb-node-health"),
            ("DBTOBSB_COLLECTION_HEALTH_VIEW", "dbtobsb-collection-health"),
        )
    )
)


class AppLifecycleError(RuntimeError):
    """Sanitized lifecycle failure containing no App or deployment identifier."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class DeploymentMode(Enum):
    SNAPSHOT = "SNAPSHOT"
    AUTO_SYNC = "AUTO_SYNC"


class DeploymentStatus(Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELLED = "CANCELLED"


class AppComputeState(Enum):
    STOPPED = "STOPPED"
    ACTIVE = "ACTIVE"
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True, repr=False)
class StableDeploymentContract:
    """Canonical intended/observed App code, configuration, and resource material."""

    source_code_path: str = field(repr=False)
    source_tree_sha256: str
    resource_bindings_sha256: str
    command: tuple[str, ...] = field(repr=False)
    environment: tuple[tuple[str, str], ...] = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.source_code_path, str)
            or not self.source_code_path.startswith("/Workspace/")
            or len(self.source_code_path) > 4_096
            or any(ord(character) < 32 for character in self.source_code_path)
            or not isinstance(self.source_tree_sha256, str)
            or not isinstance(self.resource_bindings_sha256, str)
            or _SHA256.fullmatch(self.source_tree_sha256) is None
            or _SHA256.fullmatch(self.resource_bindings_sha256) is None
            or self.command != _EXPECTED_COMMAND
            or self.environment != _EXPECTED_ENVIRONMENT
        ):
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_CONTRACT_INVALID")

    @property
    def sha256(self) -> str:
        raw = json.dumps(
            {
                "command": list(self.command),
                "environment": [list(item) for item in self.environment],
                "resource_bindings_sha256": self.resource_bindings_sha256,
                "source_code_path": self.source_code_path,
                "source_tree_sha256": self.source_tree_sha256,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return hashlib.sha256(raw).hexdigest()

    def __repr__(self) -> str:
        return f"StableDeploymentContract(sha256={self.sha256!r}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class AppDeploymentRecord:
    """Minimum deployment projection; sensitive native values stay out of reprs."""

    deployment_id: str = field(repr=False)
    mode: str
    status: str
    deployment_artifact_source_code_path: str = field(repr=False)
    contract: StableDeploymentContract = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.deployment_id, str)
            or _DEPLOYMENT_ID.fullmatch(self.deployment_id) is None
            or not isinstance(self.mode, str)
            or self.mode not in {item.value for item in DeploymentMode}
            or not isinstance(self.status, str)
            or self.status not in {item.value for item in DeploymentStatus}
            or not isinstance(self.deployment_artifact_source_code_path, str)
            or len(self.deployment_artifact_source_code_path) > 4_096
            or any(ord(character) < 32 for character in self.deployment_artifact_source_code_path)
            or not self.deployment_artifact_source_code_path.startswith("/Workspace/")
            or not self.deployment_artifact_source_code_path.endswith(f"/src/{self.deployment_id}")
            or not isinstance(self.contract, StableDeploymentContract)
        ):
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_RECORD_INVALID")

    @property
    def stable_deployment_sha256(self) -> str:
        return self.contract.sha256

    def __repr__(self) -> str:
        return f"AppDeploymentRecord(mode={self.mode!r}, status={self.status!r}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class AppDeploymentPage:
    records: tuple[AppDeploymentRecord, ...] = field(repr=False)
    next_page_token: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"AppDeploymentPage(record_count={len(self.records)}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class AppObservation:
    """Lifecycle pointers observed independently of deployment-list pagination."""

    compute_state: str
    active_deployment_id: str | None = field(default=None, repr=False)
    pending_deployment_id: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.compute_state, str) or self.compute_state not in {
            item.value for item in AppComputeState
        }:
            raise AppLifecycleError("DBTOBSB_APP_OBSERVATION_INVALID")
        for value in (self.active_deployment_id, self.pending_deployment_id):
            if value is not None and (
                not isinstance(value, str) or _DEPLOYMENT_ID.fullmatch(value) is None
            ):
                raise AppLifecycleError("DBTOBSB_APP_OBSERVATION_INVALID")

    def __repr__(self) -> str:
        return f"AppObservation(compute_state={self.compute_state!r}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ReconciledDeployment:
    """Opaque proof returned only for one stopped, matching fresh deployment."""

    _deployment_id: str = field(repr=False)
    stable_deployment_sha256: str
    pages_read: int

    def __init__(
        self,
        *,
        deployment_id: str,
        stable_deployment_sha256: str,
        pages_read: int,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _RECONCILED_TOKEN:
            raise AppLifecycleError("DBTOBSB_APP_RECONCILIATION_PROOF_DENIED")
        if (
            _DEPLOYMENT_ID.fullmatch(deployment_id) is None
            or _SHA256.fullmatch(stable_deployment_sha256) is None
            or isinstance(pages_read, bool)
            or not isinstance(pages_read, int)
            or not 1 <= pages_read <= _MAX_RECONCILIATION_PAGES
        ):
            raise AppLifecycleError("DBTOBSB_APP_RECONCILIATION_PROOF_INVALID")
        object.__setattr__(self, "_deployment_id", deployment_id)
        object.__setattr__(self, "stable_deployment_sha256", stable_deployment_sha256)
        object.__setattr__(self, "pages_read", pages_read)

    def __repr__(self) -> str:
        return (
            "ReconciledDeployment("
            f"stable_deployment_sha256={self.stable_deployment_sha256!r}, "
            f"pages_read={self.pages_read}, <redacted>)"
        )


class FreshAppDeploymentClient(Protocol):
    """Closed adapter surface used by the fresh-install reconciler."""

    def list_deployments(self, page_token: str | None) -> AppDeploymentPage: ...

    def observe_app(self) -> AppObservation: ...

    def run_bound_bundle_once(self) -> None: ...

    def stop_app(self) -> None: ...


@dataclass(frozen=True, slots=True)
class _Inventory:
    records: tuple[AppDeploymentRecord, ...]
    pages_read: int


@dataclass(slots=True)
class _PageCounter:
    pages_read: int = 0

    def note_request(self) -> None:
        if self.pages_read >= _MAX_RECONCILIATION_PAGES:
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_PAGE_BUDGET_EXHAUSTED")
        self.pages_read += 1


def _read_complete_inventory(
    client: FreshAppDeploymentClient,
    *,
    page_counter: _PageCounter,
) -> _Inventory:
    page_token: str | None = None
    seen_tokens: set[str] = set()
    records: list[AppDeploymentRecord] = []
    pages_read = 0
    while True:
        if pages_read >= _MAX_DEPLOYMENT_PAGES:
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_PAGE_LIMIT")
        page_counter.note_request()
        try:
            page = client.list_deployments(page_token)
        except Exception:
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_INVENTORY_INDETERMINATE") from None
        if not isinstance(page, AppDeploymentPage) or not isinstance(page.records, tuple):
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_INVENTORY_INDETERMINATE")
        pages_read += 1
        for record in page.records:
            if not isinstance(record, AppDeploymentRecord):
                raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_INVENTORY_INDETERMINATE")
            records.append(record)
        next_token = page.next_page_token
        if next_token is None:
            break
        if (
            not isinstance(next_token, str)
            or not next_token
            or len(next_token) > 4_096
            or any(ord(character) < 33 for character in next_token)
            or next_token in seen_tokens
        ):
            raise AppLifecycleError("DBTOBSB_APP_DEPLOYMENT_PAGINATION_INVALID")
        seen_tokens.add(next_token)
        page_token = next_token
    ids = [record.deployment_id for record in records]
    if len(ids) != len(set(ids)):
        raise AppLifecycleError("APP_DEPLOYMENT_SET_AMBIGUOUS")
    return _Inventory(tuple(records), pages_read)


def _observe(client: FreshAppDeploymentClient) -> AppObservation:
    try:
        observation = client.observe_app()
    except Exception:
        raise AppLifecycleError("DBTOBSB_APP_LIFECYCLE_OBSERVATION_INDETERMINATE") from None
    if not isinstance(observation, AppObservation):
        raise AppLifecycleError("DBTOBSB_APP_LIFECYCLE_OBSERVATION_INDETERMINATE")
    return observation


def _wait_for_stopped_terminal(
    client: FreshAppDeploymentClient,
    *,
    page_counter: _PageCounter,
) -> tuple[_Inventory, AppObservation]:
    deadline = _monotonic() + _STOP_TIMEOUT_SECONDS
    while True:
        inventory: _Inventory | None = None
        observation: AppObservation | None = None
        inventory_error: AppLifecycleError | None = None
        observation_failed = False
        try:
            inventory = _read_complete_inventory(client, page_counter=page_counter)
        except AppLifecycleError as error:
            # An inventory defect must never mask active compute or a pending deployment.
            # Observe the App independently and preserve the exact inventory failure only
            # after the stopped/no-pending lifecycle state has been proved.
            inventory_error = error
        try:
            observation = _observe(client)
        except AppLifecycleError:
            observation_failed = True

        if inventory is not None and observation is not None:
            pending_record = any(
                record.status == DeploymentStatus.IN_PROGRESS.value for record in inventory.records
            )
            stopped_without_pending = (
                observation.compute_state == AppComputeState.STOPPED.value
                and observation.pending_deployment_id is None
            )
            if len(inventory.records) > 1 and stopped_without_pending:
                return inventory, observation
            if len(inventory.records) == 1 and not pending_record and stopped_without_pending:
                return inventory, observation

        if _monotonic() >= deadline:
            if (
                observation_failed
                or observation is None
                or observation.compute_state != AppComputeState.STOPPED.value
            ):
                raise AppLifecycleError("APP_STOP_FAILED_RUNNING_UNVERIFIED")
            if observation.pending_deployment_id is not None:
                raise AppLifecycleError("APP_DEPLOYMENT_PENDING_TIMEOUT")
            if inventory_error is not None:
                raise inventory_error
            if inventory is None or not inventory.records:
                raise AppLifecycleError("APP_STAGE_DEPLOY_INDETERMINATE")
            raise AppLifecycleError("APP_DEPLOYMENT_PENDING_TIMEOUT")
        _sleep(_POLL_INTERVAL_SECONDS)


def deploy_bound_app_once(
    client: FreshAppDeploymentClient,
    *,
    expected_contract: StableDeploymentContract,
) -> ReconciledDeployment:
    """Create and reconcile the sole fresh deployment, stopping on every invocation exit.

    An error from the pinned runner can represent response loss after a successful platform
    mutation. It is therefore never retried and does not decide the outcome; the fully paginated
    after-set and stopped App observation do.
    """
    if not isinstance(expected_contract, StableDeploymentContract):
        raise AppLifecycleError("DBTOBSB_APP_EXPECTED_DEPLOYMENT_CONTRACT_INVALID")

    page_counter = _PageCounter()
    before_observation = _observe(client)
    if (
        before_observation.compute_state != AppComputeState.STOPPED.value
        or before_observation.active_deployment_id is not None
        or before_observation.pending_deployment_id is not None
    ):
        raise AppLifecycleError("UNSUPPORTED_EXISTING_APP_DEPLOYMENT")
    before = _read_complete_inventory(client, page_counter=page_counter)
    if before.records:
        raise AppLifecycleError("UNSUPPORTED_EXISTING_APP_DEPLOYMENT")

    try:
        # A process-level interruption can arrive after the remote deployment committed.  Never
        # retry the invocation: the stopped after-set below is authoritative and may complete the
        # operation when it proves exactly one matching deployment.
        with contextlib.suppress(BaseException):
            client.run_bound_bundle_once()
    finally:
        # The read-back below is authoritative: a lost stop response is harmless only
        # when an independent observation proves that compute is stopped.
        with contextlib.suppress(BaseException):
            client.stop_app()

    after, after_observation = _wait_for_stopped_terminal(
        client,
        page_counter=page_counter,
    )
    if len(after.records) != 1:
        raise AppLifecycleError("APP_DEPLOYMENT_SET_AMBIGUOUS")

    selected = after.records[0]
    if (
        selected.mode != DeploymentMode.SNAPSHOT.value
        or selected.status != DeploymentStatus.SUCCEEDED.value
        or selected.contract != expected_contract
        or after_observation.active_deployment_id != selected.deployment_id
    ):
        raise AppLifecycleError("APP_DEPLOYMENT_ACTIVE_MISMATCH")

    return ReconciledDeployment(
        deployment_id=selected.deployment_id,
        stable_deployment_sha256=selected.stable_deployment_sha256,
        pages_read=page_counter.pages_read,
        _construction_token=_RECONCILED_TOKEN,
    )
