"""Exact-byte raw archive custody in a Unity Catalog Volume."""

from __future__ import annotations

import hashlib
import os
from contextlib import suppress
from pathlib import Path, PurePosixPath

from dbtobsb_collector.contracts import AttemptContext


class RawArchiveCustodyError(RuntimeError):
    """Static custody failure that excludes evidence bytes."""


class VolumeRawArchiveStore:
    """Atomically preserve closed bytes and verify hash/size readback."""

    def __init__(self, root: str, *, require_volume: bool = True) -> None:
        path = PurePosixPath(root)
        if require_volume and (
            not path.is_absolute()
            or len(path.parts) != 5
            or path.parts[1] != "Volumes"
            or any(part in {"", ".", ".."} for part in path.parts[2:])
        ):
            raise ValueError("raw root must be exactly /Volumes/<catalog>/<schema>/<volume>")
        self._root = Path(root)

    def preserve(self, *, context: AttemptContext, archive: bytes) -> str:
        digest = hashlib.sha256(archive).hexdigest()
        destination = (
            self._root
            / "raw"
            / str(context.workspace_id)
            / str(context.dbt_task_run_id)
            / f"{digest}.tar.gz"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".part")

        if destination.exists():
            self._verify(destination=destination, expected=archive, digest=digest)
            return str(destination)

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(temporary, flags, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(archive)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except FileExistsError:
            if not destination.exists():
                raise RawArchiveCustodyError("DBT_RAW_ARCHIVE_WRITE_CONFLICT") from None
        finally:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)

        self._verify(destination=destination, expected=archive, digest=digest)
        return str(destination)

    @staticmethod
    def _verify(*, destination: Path, expected: bytes, digest: str) -> None:
        try:
            value = destination.read_bytes()
        except OSError:
            raise RawArchiveCustodyError("DBT_RAW_ARCHIVE_READBACK_FAILED") from None
        if len(value) != len(expected) or hashlib.sha256(value).hexdigest() != digest:
            raise RawArchiveCustodyError("DBT_RAW_ARCHIVE_READBACK_MISMATCH")
