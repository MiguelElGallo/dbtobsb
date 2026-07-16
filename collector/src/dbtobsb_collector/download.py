"""Bounded consumption of a short-lived Databricks artifact link."""

from __future__ import annotations

import urllib.error
import urllib.request
from http.client import HTTPMessage
from typing import IO
from urllib.parse import urlparse

from dbtobsb_capture.archive import MAX_ARCHIVE_BYTES

from dbtobsb_collector.contracts import ArtifactReference


class ArtifactDownloadError(RuntimeError):
    """Static download error that never contains a signed URL or response body."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _trusted_internal_http(url: str) -> bool:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme.lower() == "http"
        and (host.endswith(".azuredatabricks.net") or host.endswith(".databricks.com"))
        and parsed.username is None
        and parsed.password is None
        and port is None
    )


class _SameOriginRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirect hops that could disclose the signed query or required headers."""

    def __init__(self, *, origin_url: str, allow_internal_http: bool) -> None:
        self._origin = urlparse(origin_url)
        self._allow_internal_http = allow_internal_http

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        target = urlparse(newurl)
        try:
            target_port = target.port
        except ValueError:
            raise ArtifactDownloadError("DBT_ARCHIVE_REDIRECT_ORIGIN_CHANGED") from None
        same_origin = (
            (target.hostname or "").lower() == (self._origin.hostname or "").lower()
            and target_port is None
            and target.username is None
            and target.password is None
        )
        allowed_scheme = target.scheme.lower() == "https" or (
            self._allow_internal_http and _trusted_internal_http(newurl)
        )
        if not same_origin or not allowed_scheme:
            raise ArtifactDownloadError("DBT_ARCHIVE_REDIRECT_ORIGIN_CHANGED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HttpsArchiveDownloader:
    """Download one artifact over HTTPS or a capability-gated Databricks-internal URL."""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 120:
            raise ValueError("timeout_seconds must be in (0, 120]")
        self._timeout_seconds = timeout_seconds

    def download(self, reference: ArtifactReference) -> bytes:
        parsed = urlparse(reference.url)
        allow_internal_http = reference.allow_internal_databricks_http and _trusted_internal_http(
            reference.url
        )
        if parsed.scheme.lower() != "https" and not allow_internal_http:
            raise ArtifactDownloadError("DBT_ARCHIVE_LINK_NOT_HTTPS")
        request = urllib.request.Request(
            reference.url,
            headers=reference.headers,
            method="GET",
        )
        try:
            opener = urllib.request.build_opener(
                _SameOriginRedirectHandler(
                    origin_url=reference.url,
                    allow_internal_http=allow_internal_http,
                )
            )
            with opener.open(request, timeout=self._timeout_seconds) as response:
                final_url = response.geturl()
                final = urlparse(final_url)
                same_origin = (final.hostname or "").lower() == (parsed.hostname or "").lower()
                final_transport_allowed = final.scheme.lower() == "https" or (
                    allow_internal_http and _trusted_internal_http(final_url)
                )
                if not same_origin or not final_transport_allowed:
                    raise ArtifactDownloadError("DBT_ARCHIVE_REDIRECT_ORIGIN_CHANGED")
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        if int(content_length) > MAX_ARCHIVE_BYTES:
                            raise ArtifactDownloadError("DBT_ARCHIVE_SIZE_LIMIT_EXCEEDED")
                    except ValueError as exc:
                        raise ArtifactDownloadError("DBT_ARCHIVE_CONTENT_LENGTH_INVALID") from exc
                archive = response.read(MAX_ARCHIVE_BYTES + 1)
        except ArtifactDownloadError:
            raise
        except urllib.error.HTTPError as exc:
            code = (
                "DBT_ARCHIVE_LINK_EXPIRED_OR_DENIED"
                if exc.code in {401, 403}
                else "DBT_ARCHIVE_HTTP_ERROR"
            )
            raise ArtifactDownloadError(code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ArtifactDownloadError("DBT_ARCHIVE_TRANSPORT_UNAVAILABLE") from None
        if len(archive) > MAX_ARCHIVE_BYTES:
            raise ArtifactDownloadError("DBT_ARCHIVE_SIZE_LIMIT_EXCEEDED")
        return archive
