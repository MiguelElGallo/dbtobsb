"""Durable per-actor dispatch claims for the attended Statement workflow.

The production constructor has no path argument.  Claims live only in the current OS account's
platform-standard private state directory and contain one operation UUID plus one signed-marker
payload digest.  They contain no credential, identity, SQL, host, warehouse, profile, or result.
"""

from __future__ import annotations

import fcntl
import json
import os
import pwd
import re
import stat
import sys
import tempfile
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dbtobsb_installer.workflow import DispatchClaimOutcome

_PROTOCOL = "dbtobsb.dispatch-journal.v1"
_STATE_NAME = "statement-dispatch-claims-v1.json"
_LOCK_NAME = "statement-dispatch-claims-v1.lock"
_MAX_STATE_BYTES = 1_048_576
_MAX_CLAIMS = 10_000
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROCESS_LOCK = threading.Lock()


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError
        value[key] = item
    return value


def _default_private_root() -> Path:
    if sys.platform != "darwin":
        raise OSError
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    if not home.is_absolute() or home.is_symlink() or not home.is_dir():
        raise OSError
    return home / "Library" / "Application Support" / "dbtobsb" / "private"


def _validate_secure_directory(path: Path) -> None:
    details = path.lstat()
    if (
        stat.S_ISLNK(details.st_mode)
        or not stat.S_ISDIR(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) != 0o700
    ):
        raise OSError


def _ensure_secure_directory(path: Path) -> None:
    parent = path.parent
    if parent.name == "dbtobsb" and (parent.exists() or parent.is_symlink()):
        _validate_secure_directory(parent)
    if path.exists() or path.is_symlink():
        _validate_secure_directory(path)
        return
    if parent.name == "dbtobsb" and not parent.exists():
        parent.mkdir(mode=0o700)
    if parent.name == "dbtobsb":
        _validate_secure_directory(parent)
    path.mkdir(mode=0o700)
    _validate_secure_directory(path)


def _open_secure_lock(path: Path) -> int:
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    details = os.fstat(descriptor)
    if (
        not stat.S_ISREG(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) != 0o600
    ):
        os.close(descriptor)
        raise OSError
    return descriptor


def _empty_state() -> dict[str, Any]:
    return {"markers": {}, "mutations": {}, "protocol": _PROTOCOL}


def _read_state(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return _empty_state()
    try:
        details = os.fstat(descriptor)
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_uid != os.getuid()
            or stat.S_IMODE(details.st_mode) != 0o600
            or details.st_size <= 0
            or details.st_size > _MAX_STATE_BYTES
        ):
            raise OSError
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(_MAX_STATE_BYTES + 1)
    finally:
        os.close(descriptor)
    if not raw or len(raw) > _MAX_STATE_BYTES:
        raise OSError
    try:
        value = json.loads(raw, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise OSError from None
    if not isinstance(value, dict) or set(value) != {"markers", "mutations", "protocol"}:
        raise OSError
    if value["protocol"] != _PROTOCOL:
        raise OSError
    for namespace in ("markers", "mutations"):
        claims = value[namespace]
        if not isinstance(claims, dict):
            raise OSError
        for operation_id, digest in claims.items():
            try:
                parsed = uuid.UUID(operation_id)
            except (ValueError, TypeError, AttributeError):
                raise OSError from None
            if (
                str(parsed) != operation_id
                or parsed.version != 4
                or not isinstance(digest, str)
                or _SHA256.fullmatch(digest) is None
            ):
                raise OSError
    if len(value["markers"]) + len(value["mutations"]) > _MAX_CLAIMS:
        raise OSError
    return value


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    raw = (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
        + b"\n"
    )
    if len(raw) > _MAX_STATE_BYTES:
        raise OSError
    descriptor, temporary_name = tempfile.mkstemp(prefix=".dispatch-claims.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            directory_flags |= os.O_DIRECTORY
        directory = os.open(path.parent, directory_flags)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class DurableDispatchJournal:
    """Atomic marker and mutation claims with no caller-selected production path."""

    def __init__(self) -> None:
        self._root_factory: Callable[[], Path] = _default_private_root

    @classmethod
    def _for_test(cls, root: Path) -> DurableDispatchJournal:
        journal = cls.__new__(cls)
        journal._root_factory = lambda: root
        return journal

    def __repr__(self) -> str:
        return "DurableDispatchJournal(<redacted>)"

    def claim_marker_once(
        self,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        return self._claim("markers", operation_uuid, marker_payload_sha256)

    def claim_once(
        self,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        return self._claim("mutations", operation_uuid, marker_payload_sha256)

    def _claim(
        self,
        namespace: str,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        if (
            namespace not in {"markers", "mutations"}
            or not isinstance(operation_uuid, uuid.UUID)
            or operation_uuid.version != 4
            or not isinstance(marker_payload_sha256, str)
            or _SHA256.fullmatch(marker_payload_sha256) is None
        ):
            return DispatchClaimOutcome.INDETERMINATE
        operation_id = str(operation_uuid)
        try:
            with _PROCESS_LOCK:
                root = self._root_factory()
                if not isinstance(root, Path) or not root.is_absolute():
                    raise OSError
                _ensure_secure_directory(root)
                lock_descriptor = _open_secure_lock(root / _LOCK_NAME)
                try:
                    fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
                    state = _read_state(root / _STATE_NAME)
                    claims = state[namespace]
                    existing = claims.get(operation_id)
                    if existing is not None:
                        if existing == marker_payload_sha256:
                            return DispatchClaimOutcome.ALREADY_CLAIMED
                        return DispatchClaimOutcome.INDETERMINATE
                    if len(state["markers"]) + len(state["mutations"]) >= _MAX_CLAIMS:
                        return DispatchClaimOutcome.INDETERMINATE
                    claims[operation_id] = marker_payload_sha256
                    _atomic_write(root / _STATE_NAME, state)
                    return DispatchClaimOutcome.CLAIMED
                finally:
                    fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
                    os.close(lock_descriptor)
        except BaseException:
            return DispatchClaimOutcome.INDETERMINATE
