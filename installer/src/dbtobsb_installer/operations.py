"""Closed, signed operation descriptors for the attended installer foundation.

The public surface accepts typed locator fields, never SQL.  Executable mutation renderers are
intentionally absent from this release slice; the private foundation sentinel exists only so the
transport and recovery boundary can be tested without DDL or DML.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_GROUP_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_. -]{0,126}[A-Za-z0-9_.-]$|^[A-Za-z]$")
_SECURABLE_NAME = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]{0,127}(?:\.[A-Za-z_][A-Za-z0-9_]{0,127}){0,2}$"
)
_PREPARATION_PREFIX = "DBTOBSB_PREPARATION_MARKER_V1"
_MUTATION_PREFIX = "DBTOBSB_MUTATION_MARKER_V1"
_MARKER_VERSION = "dbtobsb.preparation-marker.v1"
_NATIVE_REGISTRY_VERSION = "dbtobsb.native-operation-registry.v1"
_NATIVE_PREPARATION_MARKER_V1 = "preparation_marker_v1"
_NATIVE_FOUNDATION_SENTINEL_V1 = "foundation_sentinel_v1"
_CLOSED_STATEMENT_TOKEN = object()
_SIGNED_MARKER_TOKEN = object()


class InstallerOperationError(RuntimeError):
    """Stable fail-closed error that never includes SQL, IDs, or customer values."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class SecurableType(Enum):
    CATALOG = "CATALOG"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    VIEW = "VIEW"


class CleanupPrivilege(Enum):
    MODIFY = "MODIFY"
    SELECT = "SELECT"
    USE_CATALOG = "USE_CATALOG"
    USE_SCHEMA = "USE_SCHEMA"


class CleanupAction(Enum):
    REMOVE_EXACT_PRODUCT_GRANT = "REMOVE_EXACT_PRODUCT_GRANT"
    RECONSTRUCT_FIXED_DATA_CHANGE = "RECONSTRUCT_FIXED_DATA_CHANGE"
    VERIFY_FIXED_POST_STATE = "VERIFY_FIXED_POST_STATE"


class StatementKind(Enum):
    PREPARATION_MARKER = "PREPARATION_MARKER"
    MUTATION = "MUTATION"


class MarkerTextKind(Enum):
    PREPARATION = "PREPARATION"
    MUTATION = "MUTATION"


@dataclass(frozen=True, slots=True, repr=False)
class PreparationLocator:
    """Exact signed cleanup locator made visible on the dedicated warehouse."""

    installation_id: str
    generation: int
    sequence: int
    operation_uuid: uuid.UUID
    envelope_sha256: str
    statement_sha256: str
    operator_group: str
    warehouse_id: str
    securable_type: SecurableType
    securable_name: str
    privilege: CleanupPrivilege
    action: CleanupAction

    def __post_init__(self) -> None:
        if (
            _HEX_SHA256.fullmatch(self.installation_id) is None
            or _HEX_SHA256.fullmatch(self.envelope_sha256) is None
            or _HEX_SHA256.fullmatch(self.statement_sha256) is None
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_LOCATOR_DIGEST_INVALID")
        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
            or not 1 <= self.generation <= 9_223_372_036_854_775_807
            or isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or not 1 <= self.sequence <= 9_223_372_036_854_775_807
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_LOCATOR_SEQUENCE_INVALID")
        if not isinstance(self.operation_uuid, uuid.UUID) or self.operation_uuid.version != 4:
            raise InstallerOperationError("DBTOBSB_INSTALLER_OPERATION_UUID_INVALID")
        if (
            not isinstance(self.operator_group, str)
            or _GROUP_NAME.fullmatch(self.operator_group) is None
            or "@" in self.operator_group
            or any(token in self.operator_group for token in ("--", "/*", "*/", "'", '"', ";"))
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_OPERATOR_GROUP_INVALID")
        if _WAREHOUSE_ID.fullmatch(self.warehouse_id) is None:
            raise InstallerOperationError("DBTOBSB_INSTALLER_LOCATOR_WAREHOUSE_INVALID")
        if _SECURABLE_NAME.fullmatch(self.securable_name) is None:
            raise InstallerOperationError("DBTOBSB_INSTALLER_SECURABLE_INVALID")
        if not isinstance(self.securable_type, SecurableType):
            raise InstallerOperationError("DBTOBSB_INSTALLER_SECURABLE_TYPE_INVALID")
        if not isinstance(self.privilege, CleanupPrivilege):
            raise InstallerOperationError("DBTOBSB_INSTALLER_PRIVILEGE_INVALID")
        if not isinstance(self.action, CleanupAction):
            raise InstallerOperationError("DBTOBSB_INSTALLER_ACTION_INVALID")

    def __repr__(self) -> str:
        return "PreparationLocator(<redacted>)"


class MarkerSigner(Protocol):
    @property
    def key_id(self) -> str: ...

    def sign(self, payload: bytes) -> bytes: ...


class MarkerVerifier(Protocol):
    @property
    def key_id(self) -> str: ...

    def verify(self, payload: bytes, signature: bytes) -> bool: ...


@dataclass(frozen=True, slots=True, repr=False)
class Ed25519MarkerSigner:
    """Asymmetric marker signer; only the public verifier crosses actor boundaries."""

    private_key: Ed25519PrivateKey = field(repr=False)

    @property
    def key_id(self) -> str:
        return _public_key_id(self.private_key.public_key())

    def sign(self, payload: bytes) -> bytes:
        return self.private_key.sign(payload)

    def verifier(self) -> Ed25519MarkerVerifier:
        return Ed25519MarkerVerifier(self.private_key.public_key())

    def __repr__(self) -> str:
        return "Ed25519MarkerSigner(<redacted>)"


@dataclass(frozen=True, slots=True)
class Ed25519MarkerVerifier:
    """Public-only verifier used by Query History recovery."""

    public_key: Ed25519PublicKey

    @property
    def key_id(self) -> str:
        return _public_key_id(self.public_key)

    def verify(self, payload: bytes, signature: bytes) -> bool:
        try:
            self.public_key.verify(signature, payload)
        except (InvalidSignature, ValueError):
            return False
        return True


def _public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True, repr=False)
class ClosedStatement:
    """Statement bytes constructed only by a versioned in-package renderer."""

    kind: StatementKind
    _text: str = field(repr=False)
    semantic_sha256: str
    _native_operation: str = field(repr=False)
    _native_parameters: tuple[tuple[str, str], ...] = field(repr=False)

    def __init__(
        self,
        *,
        kind: StatementKind,
        text: str,
        semantic_sha256: str,
        native_operation: str = "",
        native_parameters: tuple[tuple[str, str], ...] = (),
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CLOSED_STATEMENT_TOKEN:
            raise InstallerOperationError("DBTOBSB_INSTALLER_STATEMENT_CONSTRUCTION_DENIED")
        if not isinstance(kind, StatementKind) or not isinstance(text, str):
            raise InstallerOperationError("DBTOBSB_INSTALLER_STATEMENT_INVALID")
        if not text or ";" in text or len(text.encode("utf-8")) > 32_768:
            raise InstallerOperationError("DBTOBSB_INSTALLER_STATEMENT_INVALID")
        if _HEX_SHA256.fullmatch(semantic_sha256) is None:
            raise InstallerOperationError("DBTOBSB_INSTALLER_STATEMENT_DIGEST_INVALID")
        if (
            not isinstance(native_operation, str)
            or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", native_operation) is None
            or not isinstance(native_parameters, tuple)
            or not native_parameters
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_NATIVE_OPERATION_INVALID")
        previous = ""
        for parameter in native_parameters:
            if (
                not isinstance(parameter, tuple)
                or len(parameter) != 2
                or not isinstance(parameter[0], str)
                or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", parameter[0]) is None
                or parameter[0] <= previous
                or not isinstance(parameter[1], str)
                or not parameter[1]
                or len(parameter[1].encode("ascii", errors="ignore"))
                != len(parameter[1].encode("utf-8"))
                or len(parameter[1]) > 16_384
                or any(ord(character) < 32 or ord(character) == 127 for character in parameter[1])
            ):
                raise InstallerOperationError("DBTOBSB_INSTALLER_NATIVE_PARAMETERS_INVALID")
            previous = parameter[0]
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "_text", text)
        object.__setattr__(self, "semantic_sha256", semantic_sha256)
        object.__setattr__(self, "_native_operation", native_operation)
        object.__setattr__(self, "_native_parameters", native_parameters)

    def _transport_text(self) -> str:
        return self._text

    def _native_transport(self) -> dict[str, object]:
        """Return the fixed registry descriptor; executable SQL never crosses this boundary."""

        return {
            "parameters": dict(self._native_parameters),
            "registry_operation": self._native_operation,
            "registry_version": _NATIVE_REGISTRY_VERSION,
            "semantic_sha256": self.semantic_sha256,
        }

    def __repr__(self) -> str:
        return f"ClosedStatement(kind={self.kind.value}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class SignedPreparationMarker:
    """Signed locator and its compact Query History token."""

    locator: PreparationLocator = field(repr=False)
    compact_token: str = field(repr=False)
    payload_sha256: str

    def __init__(
        self,
        *,
        locator: PreparationLocator,
        compact_token: str,
        payload_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _SIGNED_MARKER_TOKEN:
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_CONSTRUCTION_DENIED")
        if (
            not isinstance(locator, PreparationLocator)
            or not isinstance(compact_token, str)
            or _HEX_SHA256.fullmatch(payload_sha256) is None
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_INVALID")
        object.__setattr__(self, "locator", locator)
        object.__setattr__(self, "compact_token", compact_token)
        object.__setattr__(self, "payload_sha256", payload_sha256)

    def __repr__(self) -> str:
        return "SignedPreparationMarker(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ClosedMutationOperation:
    """Opaque fixed operation rendered by signed code, never by CLI/YAML/plan input."""

    _base_statement: ClosedStatement = field(repr=False)

    @property
    def statement_sha256(self) -> str:
        return self._base_statement.semantic_sha256

    def __repr__(self) -> str:
        return "ClosedMutationOperation(<redacted>)"


def _canonical_payload(locator: PreparationLocator, key_id: str) -> bytes:
    if _HEX_SHA256.fullmatch(key_id) is None:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_KEY_INVALID")
    document = {
        "action": locator.action.value,
        "envelope_sha256": locator.envelope_sha256,
        "generation": str(locator.generation),
        "installation_id": locator.installation_id,
        "marker_version": _MARKER_VERSION,
        "operation_uuid": str(locator.operation_uuid),
        "operator_group": locator.operator_group,
        "privilege": locator.privilege.value,
        "securable_name": locator.securable_name,
        "securable_type": locator.securable_type.value,
        "sequence": str(locator.sequence),
        "signer_key_id": key_id,
        "statement_sha256": locator.statement_sha256,
        "warehouse_id": locator.warehouse_id,
    }
    return json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _base32(raw: bytes) -> str:
    """Encode marker bytes with an SQL-delimiter-free alphabet."""
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _decode_base32(value: str) -> bytes:
    if not value or re.fullmatch(r"[A-Z2-7]+", value) is None:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_ENCODING_INVALID")
    try:
        decoded = base64.b32decode(value + "=" * (-len(value) % 8), casefold=False)
    except (binascii.Error, ValueError, TypeError):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_ENCODING_INVALID") from None
    if _base32(decoded) != value:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_ENCODING_INVALID")
    return decoded


def sign_preparation_marker(
    locator: PreparationLocator,
    signer: MarkerSigner,
) -> SignedPreparationMarker:
    """Sign one closed locator without rendering or accepting SQL."""
    payload = _canonical_payload(locator, signer.key_id)
    try:
        signature = signer.sign(payload)
    except InstallerOperationError:
        raise
    except Exception:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_SIGNING_FAILED") from None
    if not isinstance(signature, bytes) or not 32 <= len(signature) <= 512:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_SIGNATURE_INVALID")
    token = f"{signer.key_id}.{_base32(payload)}.{_base32(signature)}"
    return SignedPreparationMarker(
        locator=locator,
        compact_token=token,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        _construction_token=_SIGNED_MARKER_TOKEN,
    )


def _validate_signed_marker(
    marker: SignedPreparationMarker,
    verifier: MarkerVerifier,
) -> None:
    if not isinstance(marker, SignedPreparationMarker):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_INVALID")
    observed = parse_marker_token(marker.compact_token, verifier)
    if (
        observed.locator != marker.locator
        or observed.payload_sha256 != marker.payload_sha256
        or observed.compact_token != marker.compact_token
    ):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_INVALID")


def render_preparation_statement(
    marker: SignedPreparationMarker,
    verifier: MarkerVerifier,
) -> ClosedStatement:
    """Render the one fixed read-only marker operation."""
    _validate_signed_marker(marker, verifier)
    text = f"SELECT '{_PREPARATION_PREFIX}.{marker.compact_token}' AS dbtobsb_preparation_marker"
    return ClosedStatement(
        kind=StatementKind.PREPARATION_MARKER,
        text=text,
        semantic_sha256=hashlib.sha256(text.encode()).hexdigest(),
        native_operation=_NATIVE_PREPARATION_MARKER_V1,
        native_parameters=(("marker_token", marker.compact_token),),
        _construction_token=_CLOSED_STATEMENT_TOKEN,
    )


def bind_mutation_marker(
    operation: ClosedMutationOperation,
    marker: SignedPreparationMarker,
    verifier: MarkerVerifier,
) -> ClosedStatement:
    """Bind a signed marker to an already rendered closed operation."""
    _validate_signed_marker(marker, verifier)
    if marker.locator.statement_sha256 != operation.statement_sha256:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_STATEMENT_MISMATCH")
    base = operation._base_statement._transport_text()
    text = f"/* {_MUTATION_PREFIX}.{marker.compact_token} */\n{base}"
    return ClosedStatement(
        kind=StatementKind.MUTATION,
        text=text,
        semantic_sha256=operation.statement_sha256,
        native_operation=operation._base_statement._native_operation,
        native_parameters=tuple(
            sorted(
                (
                    *operation._base_statement._native_parameters,
                    ("marker_token", marker.compact_token),
                )
            )
        ),
        _construction_token=_CLOSED_STATEMENT_TOKEN,
    )


def _foundation_test_mutation(operation_uuid: uuid.UUID) -> ClosedMutationOperation:
    """Return a harmless fixed sentinel used only by foundation tests.

    This is intentionally private and read-only.  Production mutation operation renderers do not
    exist in this slice.
    """
    if not isinstance(operation_uuid, uuid.UUID) or operation_uuid.version != 4:
        raise InstallerOperationError("DBTOBSB_INSTALLER_OPERATION_UUID_INVALID")
    text = (
        "SELECT CAST(1 AS INT) AS dbtobsb_foundation_sentinel "
        f"/* fixed-operation:{operation_uuid} */"
    )
    digest = hashlib.sha256(text.encode()).hexdigest()
    statement = ClosedStatement(
        kind=StatementKind.MUTATION,
        text=text,
        semantic_sha256=digest,
        native_operation=_NATIVE_FOUNDATION_SENTINEL_V1,
        native_parameters=(("operation_uuid", str(operation_uuid)),),
        _construction_token=_CLOSED_STATEMENT_TOKEN,
    )
    return ClosedMutationOperation(statement)


def _registered_mutation(
    *,
    native_operation: str,
    native_parameters: tuple[tuple[str, str], ...],
    text: str,
) -> ClosedMutationOperation:
    """Construct one package-owned production registry operation from fixed renderer output."""

    digest = hashlib.sha256(text.encode()).hexdigest()
    return ClosedMutationOperation(
        ClosedStatement(
            kind=StatementKind.MUTATION,
            text=text,
            semantic_sha256=digest,
            native_operation=native_operation,
            native_parameters=tuple(sorted(native_parameters)),
            _construction_token=_CLOSED_STATEMENT_TOKEN,
        )
    )


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_PAYLOAD_INVALID")
        result[key] = value
    return result


def _locator_from_payload(payload: bytes, verifier: MarkerVerifier) -> PreparationLocator:
    try:
        document = json.loads(payload, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, InstallerOperationError):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_PAYLOAD_INVALID") from None
    expected_keys = {
        "action",
        "envelope_sha256",
        "generation",
        "installation_id",
        "marker_version",
        "operation_uuid",
        "operator_group",
        "privilege",
        "securable_name",
        "securable_type",
        "sequence",
        "signer_key_id",
        "statement_sha256",
        "warehouse_id",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_PAYLOAD_INVALID")
    if (
        document["marker_version"] != _MARKER_VERSION
        or document["signer_key_id"] != verifier.key_id
    ):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_VERSION_INVALID")
    if not all(isinstance(value, str) for value in document.values()):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_PAYLOAD_INVALID")
    generation = document["generation"]
    sequence = document["sequence"]
    if (
        re.fullmatch(r"[1-9][0-9]{0,18}", generation) is None
        or re.fullmatch(r"[1-9][0-9]{0,18}", sequence) is None
    ):
        raise InstallerOperationError("DBTOBSB_INSTALLER_LOCATOR_SEQUENCE_INVALID")
    try:
        operation_uuid = uuid.UUID(document["operation_uuid"])
        if str(operation_uuid) != document["operation_uuid"]:
            raise ValueError
        return PreparationLocator(
            installation_id=document["installation_id"],
            generation=int(generation),
            sequence=int(sequence),
            operation_uuid=operation_uuid,
            envelope_sha256=document["envelope_sha256"],
            statement_sha256=document["statement_sha256"],
            operator_group=document["operator_group"],
            warehouse_id=document["warehouse_id"],
            securable_type=SecurableType(document["securable_type"]),
            securable_name=document["securable_name"],
            privilege=CleanupPrivilege(document["privilege"]),
            action=CleanupAction(document["action"]),
        )
    except (ValueError, TypeError):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_PAYLOAD_INVALID") from None


def parse_marker_token(token: str, verifier: MarkerVerifier) -> SignedPreparationMarker:
    """Verify and parse one compact token using only the expected public key."""
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != verifier.key_id:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_KEY_INVALID")
    payload = _decode_base32(parts[1])
    signature = _decode_base32(parts[2])
    try:
        verified = verifier.verify(payload, signature)
    except Exception:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_SIGNATURE_INVALID") from None
    if not verified:
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_SIGNATURE_INVALID")
    locator = _locator_from_payload(payload, verifier)
    if payload != _canonical_payload(locator, verifier.key_id):
        raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_CANONICALIZATION_INVALID")
    return SignedPreparationMarker(
        locator=locator,
        compact_token=token,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        _construction_token=_SIGNED_MARKER_TOKEN,
    )


def parse_query_marker(
    query_text: str,
    kind: MarkerTextKind,
    verifier: MarkerVerifier,
) -> SignedPreparationMarker:
    """Recover one signed marker from an exact versioned Query History query text."""
    if not isinstance(query_text, str) or len(query_text.encode("utf-8")) > 32_768:
        raise InstallerOperationError("DBTOBSB_INSTALLER_QUERY_MARKER_INVALID")
    if kind is MarkerTextKind.PREPARATION:
        prefix = f"SELECT '{_PREPARATION_PREFIX}."
        suffix = "' AS dbtobsb_preparation_marker"
        if not query_text.startswith(prefix) or not query_text.endswith(suffix):
            raise InstallerOperationError("DBTOBSB_INSTALLER_QUERY_MARKER_INVALID")
        token = query_text[len(prefix) : -len(suffix)]
        return parse_marker_token(token, verifier)
    if kind is MarkerTextKind.MUTATION:
        prefix = f"/* {_MUTATION_PREFIX}."
        separator = " */\n"
        if not query_text.startswith(prefix) or separator not in query_text:
            raise InstallerOperationError("DBTOBSB_INSTALLER_QUERY_MARKER_INVALID")
        token, base_statement = query_text[len(prefix) :].split(separator, 1)
        marker = parse_marker_token(token, verifier)
        if hashlib.sha256(base_statement.encode()).hexdigest() != marker.locator.statement_sha256:
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_STATEMENT_MISMATCH")
        return marker
    raise InstallerOperationError("DBTOBSB_INSTALLER_QUERY_MARKER_KIND_INVALID")
