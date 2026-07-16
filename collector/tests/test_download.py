"""Bounded HTTPS downloader tests."""

from __future__ import annotations

import io
import urllib.error
from email.message import Message
from typing import Any

import pytest

from dbtobsb_collector import ArtifactReference
from dbtobsb_collector.download import ArtifactDownloadError, HttpsArchiveDownloader


class _Response:
    def __init__(self, value: bytes, *, final_url: str = "https://blob.invalid/archive") -> None:
        self._stream = io.BytesIO(value)
        self._final_url = final_url
        self.headers = Message()
        self.headers["Content-Length"] = str(len(value))

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def geturl(self) -> str:
        return self._final_url

    def read(self, size: int) -> bytes:
        return self._stream.read(size)


def test_downloader_passes_required_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, Any] = {}

    class _Opener:
        def open(self, request: Any, *, timeout: float) -> _Response:
            observed["header"] = request.get_header("X-required")
            observed["timeout"] = timeout
            return _Response(b"closed archive", final_url=request.full_url)

    monkeypatch.setattr("urllib.request.build_opener", lambda *_: _Opener())
    result = HttpsArchiveDownloader(timeout_seconds=12).download(
        ArtifactReference("https://signed.invalid/archive", {"x-required": "yes"})
    )

    assert result == b"closed archive"
    assert observed == {"header": "yes", "timeout": 12}


def test_non_https_link_is_rejected_without_url_in_error() -> None:
    with pytest.raises(ArtifactDownloadError) as captured:
        HttpsArchiveDownloader().download(
            ArtifactReference("http://signed.invalid/?secret=TOP_SECRET", {})
        )

    assert captured.value.code == "DBT_ARCHIVE_LINK_NOT_HTTPS"
    assert "TOP_SECRET" not in str(captured.value)


def test_http_denial_is_static(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Opener:
        def open(self, *_: object, **__: object) -> _Response:
            raise urllib.error.HTTPError(
                "https://signed.invalid/?secret=TOP_SECRET",
                403,
                "forbidden",
                Message(),
                None,
            )

    monkeypatch.setattr("urllib.request.build_opener", lambda *_: _Opener())
    with pytest.raises(ArtifactDownloadError) as captured:
        HttpsArchiveDownloader().download(
            ArtifactReference("https://signed.invalid/?secret=TOP_SECRET", {})
        )

    assert captured.value.code == "DBT_ARCHIVE_LINK_EXPIRED_OR_DENIED"
    assert "TOP_SECRET" not in str(captured.value)


def test_capability_gated_internal_databricks_http_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Opener:
        def open(self, request: Any, *, timeout: float) -> _Response:
            assert timeout == 60
            return _Response(b"closed archive", final_url=request.full_url)

    monkeypatch.setattr("urllib.request.build_opener", lambda *_: _Opener())
    result = HttpsArchiveDownloader().download(
        ArtifactReference(
            "http://artifacts.cloud.databricks.com/archive?opaque=secret",
            {},
            allow_internal_databricks_http=True,
        )
    )

    assert result == b"closed archive"


def test_internal_http_without_capability_is_rejected() -> None:
    with pytest.raises(ArtifactDownloadError) as captured:
        HttpsArchiveDownloader().download(
            ArtifactReference("http://artifacts.cloud.databricks.com/archive", {})
        )

    assert captured.value.code == "DBT_ARCHIVE_LINK_NOT_HTTPS"


def test_cross_origin_final_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Opener:
        def open(self, *_: object, **__: object) -> _Response:
            return _Response(b"closed archive", final_url="https://attacker.invalid/archive")

    monkeypatch.setattr("urllib.request.build_opener", lambda *_: _Opener())
    with pytest.raises(ArtifactDownloadError) as captured:
        HttpsArchiveDownloader().download(ArtifactReference("https://signed.invalid/archive", {}))

    assert captured.value.code == "DBT_ARCHIVE_REDIRECT_ORIGIN_CHANGED"
