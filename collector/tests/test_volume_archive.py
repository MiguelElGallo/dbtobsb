"""Unity Catalog Volume artifact acquisition tests."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from databricks.sdk import WorkspaceClient

import dbtobsb_collector.volume_archive as volume_module
from dbtobsb_collector import VolumeArtifactReference
from dbtobsb_collector.download import ArtifactDownloadError
from dbtobsb_collector.volume_archive import VolumeArchiveDownloader

_ATTEMPT = "w101-j201-r301-t401-p0-e1"
_SOURCE = f"/Volumes/observability/dbtobsb/dbtobsb_stage/incoming/{_ATTEMPT}"
_ARCHIVE = f"target/dbtobsb/attempts/{_ATTEMPT}"
_FIXTURES = (
    Path(__file__).parents[2] / "capture" / "tests" / "fixtures" / "artifact_pair" / "valid_success"
)
_CLIENT = cast(WorkspaceClient, SimpleNamespace(files=object()))


def _reference(**overrides: object) -> VolumeArtifactReference:
    values: dict[str, object] = {
        "source_root": _SOURCE,
        "archive_root": _ARCHIVE,
        "include_deps": False,
    }
    values.update(overrides)
    return VolumeArtifactReference(**values)  # type: ignore[arg-type]


def test_volume_archive_is_deterministic_and_contains_only_allowlisted_members(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = (_FIXTURES / "manifest.json").read_bytes()
    run_results = (_FIXTURES / "run_results.json").read_bytes()

    def read(files: object, path: str, *, limit: int, required: bool) -> bytes | None:
        del files, limit, required
        if path.endswith("/manifest.json"):
            return manifest
        if path.endswith("/run_results.json"):
            return run_results
        if path.endswith("/dbt.log"):
            return b'{"info":{"name":"MainReportVersion","msg":"v1"}}\n'
        return None

    monkeypatch.setattr(volume_module, "_read_volume_file", read)
    first = VolumeArchiveDownloader(client=_CLIENT).download(_reference())
    second = VolumeArchiveDownloader(client=_CLIENT).download(_reference())

    assert first == second
    with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as archive:
        assert archive.getnames() == [
            f"{_ARCHIVE}/001-build/artifacts/manifest.json",
            f"{_ARCHIVE}/001-build/artifacts/run_results.json",
            f"{_ARCHIVE}/001-build/logs/dbt.log",
        ]


@pytest.mark.parametrize(
    "reference",
    [
        _reference(source_root="/tmp/customer-controlled"),
        _reference(archive_root="../../outside"),
        _reference(archive_root="target/dbtobsb/attempts/w101-j201-r301-t999-p0-e1"),
    ],
)
def test_volume_archive_rejects_unsealed_or_mismatched_roots(
    reference: VolumeArtifactReference,
) -> None:
    with pytest.raises(ArtifactDownloadError, match="DBT_VOLUME_ARTIFACT_REFERENCE_INVALID"):
        VolumeArchiveDownloader(client=_CLIENT).download(reference)


def test_volume_reader_rejects_invalid_metadata() -> None:
    files = SimpleNamespace(
        get_metadata=lambda path: SimpleNamespace(content_length="unknown"),
    )

    with pytest.raises(ArtifactDownloadError, match="DBT_VOLUME_ARTIFACT_METADATA_INVALID"):
        volume_module._read_volume_file(files, "/Volumes/c/s/v/file", limit=10, required=True)
