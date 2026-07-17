"""Bounded reconstruction of one dbt evidence archive from a Unity Catalog Volume."""

from __future__ import annotations

import gzip
import io
import re
import tarfile
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound, ResourceDoesNotExist
from dbtobsb_capture.archive import MAX_ARCHIVE_BYTES
from dbtobsb_capture.inspector import MAX_PRIMARY_ARTIFACT_BYTES
from dbtobsb_contracts import load_support_manifest

from dbtobsb_collector.contracts import ArtifactReference, ArtifactSource, VolumeArtifactReference
from dbtobsb_collector.download import ArtifactDownloadError, HttpsArchiveDownloader

_ATTEMPT_KEY = r"w[1-9][0-9]*-j[1-9][0-9]*-r[1-9][0-9]*-t[1-9][0-9]*-p[0-9]+-e[1-9][0-9]*"
_SOURCE_ROOT = re.compile(
    r"^/Volumes/[A-Za-z_][A-Za-z0-9_]{0,127}/"
    r"[A-Za-z_][A-Za-z0-9_]{0,127}/dbtobsb_stage/incoming/"
    rf"(?P<attempt>{_ATTEMPT_KEY})$"
)
_ARCHIVE_ROOT = re.compile(rf"^target/dbtobsb/attempts/(?P<attempt>{_ATTEMPT_KEY})$")


def _read_volume_file(files: Any, path: str, *, limit: int, required: bool) -> bytes | None:
    try:
        metadata = files.get_metadata(path)
        size = getattr(metadata, "content_length", None)
        if not isinstance(size, int) or size < 0:
            raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_METADATA_INVALID")
        if size > limit:
            raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_SIZE_LIMIT_EXCEEDED")
        response = files.download(path)
        with response.contents as stream:
            value = stream.read(limit + 1)
    except (NotFound, ResourceDoesNotExist):
        if required:
            raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_UNAVAILABLE") from None
        return None
    except ArtifactDownloadError:
        raise
    except Exception:
        raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_READ_FAILED") from None
    if len(value) != size or len(value) > limit:
        raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_SIZE_LIMIT_EXCEEDED")
    return value


def _add_member(archive: tarfile.TarFile, *, name: str, value: bytes) -> None:
    member = tarfile.TarInfo(name=name)
    member.size = len(value)
    member.mode = 0o600
    member.mtime = 0
    member.uid = 0
    member.gid = 0
    member.uname = ""
    member.gname = ""
    archive.addfile(member, io.BytesIO(value))


class VolumeArchiveDownloader:
    """Read only the fixed artifact pair and bounded structured logs for one attempt."""

    def __init__(self, client: WorkspaceClient | None = None) -> None:
        self._files = (client or WorkspaceClient()).files

    def download(self, reference: VolumeArtifactReference) -> bytes:
        if not isinstance(reference, VolumeArtifactReference):
            raise TypeError("reference must be VolumeArtifactReference")
        source_match = _SOURCE_ROOT.fullmatch(reference.source_root)
        archive_match = _ARCHIVE_ROOT.fullmatch(reference.archive_root)
        if (
            source_match is None
            or archive_match is None
            or source_match.group("attempt") != archive_match.group("attempt")
            or not isinstance(reference.include_deps, bool)
        ):
            raise ArtifactDownloadError("DBT_VOLUME_ARTIFACT_REFERENCE_INVALID")

        source = reference.source_root
        build = f"{source}/001-build"
        manifest = _read_volume_file(
            self._files,
            f"{build}/artifacts/manifest.json",
            limit=MAX_PRIMARY_ARTIFACT_BYTES,
            required=True,
        )
        run_results = _read_volume_file(
            self._files,
            f"{build}/artifacts/run_results.json",
            limit=MAX_PRIMARY_ARTIFACT_BYTES,
            required=True,
        )
        assert manifest is not None and run_results is not None

        governed = load_support_manifest().governed_output
        max_log_bytes = int(governed["file_log_max_bytes"])
        max_log_files = int(governed["file_log_max_files"])
        members: list[tuple[str, bytes]] = [
            (f"{reference.archive_root}/001-build/artifacts/manifest.json", manifest),
            (f"{reference.archive_root}/001-build/artifacts/run_results.json", run_results),
        ]
        ordinals = ["000-deps"] if reference.include_deps else []
        ordinals.append("001-build")
        for ordinal in ordinals:
            base = f"{source}/{ordinal}/logs/dbt.log"
            for rotation in range(max_log_files):
                path = base if rotation == 0 else f"{base}.{rotation}"
                value = _read_volume_file(
                    self._files,
                    path,
                    limit=max_log_bytes,
                    required=False,
                )
                if value is None:
                    continue
                suffix = "" if rotation == 0 else f".{rotation}"
                members.append((f"{reference.archive_root}/{ordinal}/logs/dbt.log{suffix}", value))

        destination = io.BytesIO()
        with (
            gzip.GzipFile(fileobj=destination, mode="wb", filename="", mtime=0) as compressed,
            tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive,
        ):
            for name, value in members:
                _add_member(archive, name=name, value=value)
        value = destination.getvalue()
        if len(value) > MAX_ARCHIVE_BYTES:
            raise ArtifactDownloadError("DBT_ARCHIVE_SIZE_LIMIT_EXCEEDED")
        return value


class DatabricksArtifactDownloader:
    """Dispatch between the customer-local Volume and optional native signed archive."""

    def __init__(self) -> None:
        self._volume = VolumeArchiveDownloader()
        self._https = HttpsArchiveDownloader()

    def download(self, reference: ArtifactSource) -> bytes:
        if isinstance(reference, VolumeArtifactReference):
            return self._volume.download(reference)
        if isinstance(reference, ArtifactReference):
            return self._https.download(reference)
        raise TypeError("reference must be an approved artifact source")
