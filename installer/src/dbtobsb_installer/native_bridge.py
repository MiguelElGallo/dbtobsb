"""Sealed, bounded process boundary for the dbtobsb native Databricks bridge.

The production constructor has no caller-selected path, digest, environment, or operation.  A
release build must generate the package-local seal module and install the helper in the fixed
layout before this boundary becomes available.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import signal
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol, cast

from dbtobsb_installer.auth import (
    InstallerAuthError,
    reject_inherited_credential_environment,
)

_PROTOCOL = "dbtobsb.native-bridge.v1"
_MANIFEST_SCHEMA = "dbtobsb.native-helper-release.v1"
_HELPER_FILENAME = "dbtobsb-native-bridge"
_LAYOUT_DIRECTORY = "darwin-arm64"
_MAX_INPUT_BYTES = 64 * 1024
_MAX_OUTPUT_BYTES = (4 * 1024 * 1024) + (16 * 1024)
_PROCESS_TIMEOUT_SECONDS = 110.0
_PROCESS_POLL_SECONDS = 0.05
_GROUP_TERM_GRACE_SECONDS = 0.25
_GROUP_KILL_GRACE_SECONDS = 0.75
_MAX_MANIFEST_BYTES = 4_096
_VERIFIED_EXECUTABLE_TOKEN = object()
_EXPECTED_CLI = {
    "commit": "3b9fe151888df8fe937090e5f2be0a5c6dc0ff18",
    "module": "github.com/databricks/cli",
    "module_sum": "h1:+1aoZobpIBqGPuS1gyveIFeOC1BVK2jn8G6qYaQ/GwM=",
    "version": "v1.8.0",
}
_EXPECTED_SDK = {
    "module": "github.com/databricks/databricks-sdk-go",
    "module_sum": "h1:Vmif0i0rbu7kgphoEBPRroZNd5uLBOITvjU4dr2lwXY=",
    "version": "v0.154.0",
}

try:
    _generated_seal = importlib.import_module("dbtobsb_installer._generated_native_release_seal")
    _GENERATED_MANIFEST_SHA256 = getattr(_generated_seal, "MANIFEST_SHA256", None)
except ModuleNotFoundError:  # The source tree intentionally has no unqualified release artifact.
    _GENERATED_MANIFEST_SHA256 = None


class FailureStage(Enum):
    RELEASE_SEAL = "RELEASE_SEAL"
    PROCESS = "PROCESS"
    AUTH_CONFIGURATION = "AUTH_CONFIGURATION"
    ACTOR_IDENTITY = "ACTOR_IDENTITY"
    STATEMENT_SUBMISSION = "STATEMENT_SUBMISSION"
    QUERY_HISTORY = "QUERY_HISTORY"
    CANCELLATION = "CANCELLATION"


class RetryClass(Enum):
    DO_NOT_RETRY = "DO_NOT_RETRY"
    RETRY_AFTER_CORRECTION = "RETRY_AFTER_CORRECTION"
    BOUNDED_READ_ONLY_RETRY = "BOUNDED_READ_ONLY_RETRY"
    RECONCILE_BEFORE_RETRY = "RECONCILE_BEFORE_RETRY"


@dataclass(frozen=True, slots=True, repr=False)
class AdapterFailure:
    """JSON-ready failure guidance containing no customer or credential values."""

    code: str
    stage: FailureStage
    possible_running_or_cost: bool
    responsible_actor: str
    retry_class: RetryClass
    safe_next_action: str

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "code": self.code,
            "stage": self.stage.value,
            "possible_running_or_cost": self.possible_running_or_cost,
            "responsible_actor": self.responsible_actor,
            "retry_class": self.retry_class.value,
            "safe_next_action": self.safe_next_action,
        }

    def __repr__(self) -> str:
        return (
            "AdapterFailure("
            f"code={self.code!r}, stage={self.stage.value!r}, "
            f"possible_running_or_cost={self.possible_running_or_cost!r}, "
            f"responsible_actor={self.responsible_actor!r}, "
            f"retry_class={self.retry_class.value!r}, <safe>)"
        )


class DatabricksPlatformAdapterError(RuntimeError):
    """Fail-closed error with stable, sanitized recovery guidance."""

    def __init__(self, failure: AdapterFailure) -> None:
        self.failure = failure
        self.code = failure.code
        super().__init__(failure.code)

    def __repr__(self) -> str:
        return f"DatabricksPlatformAdapterError({self.failure!r})"


@dataclass(frozen=True, slots=True, repr=False)
class NativeProcessResult:
    return_code: int
    stdout: bytes = field(repr=False)
    output_was_truncated: bool = False

    def __repr__(self) -> str:
        return f"NativeProcessResult(return_code={self.return_code}, <redacted>)"


@dataclass(slots=True, repr=False)
class _VerifiedNativeExecutable:
    installed_path: str
    fd: int = field(repr=False)
    device: int = field(repr=False)
    inode: int = field(repr=False)
    size: int
    sha256: str = field(repr=False)
    _closed: bool = field(default=False, repr=False)

    def __init__(
        self,
        *,
        installed_path: str,
        fd: int,
        device: int,
        inode: int,
        size: int,
        sha256: str,
        _construction_token: object,
    ) -> None:
        if (
            _construction_token is not _VERIFIED_EXECUTABLE_TOKEN
            or not isinstance(installed_path, str)
            or not Path(installed_path).is_absolute()
            or isinstance(fd, bool)
            or not isinstance(fd, int)
            or fd < 0
            or not _is_sha256(sha256)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in (device, inode, size)
            )
        ):
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_IDENTITY_INVALID")
        self.installed_path = installed_path
        self.fd = fd
        self.device = device
        self.inode = inode
        self.size = size
        self.sha256 = sha256
        self._closed = False

    @classmethod
    def _for_test(cls, path: Path) -> _VerifiedNativeExecutable:
        fd = _open_executable_no_follow(path)
        info = os.fstat(fd)
        with os.fdopen(os.dup(fd), "rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        return cls(
            installed_path=str(path),
            fd=fd,
            device=info.st_dev,
            inode=info.st_ino,
            size=info.st_size,
            sha256=digest,
            _construction_token=_VERIFIED_EXECUTABLE_TOKEN,
        )

    def close(self) -> None:
        if not self._closed:
            with suppress(OSError):
                os.close(self.fd)
            self._closed = True

    def __enter__(self) -> _VerifiedNativeExecutable:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return "_VerifiedNativeExecutable(<redacted>)"


class NativeProcessRunner(Protocol):
    def run(
        self,
        executable: _VerifiedNativeExecutable,
        *,
        stdin: bytes,
        environment: Mapping[str, str],
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> NativeProcessResult: ...


def _darwin_resource_limits() -> None:
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (75, 75))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _wait_bounded(process: subprocess.Popen[bytes], timeout_seconds: float) -> bool:
    try:
        process.wait(timeout=timeout_seconds)
    except (KeyboardInterrupt, OSError, subprocess.TimeoutExpired):
        return False
    return True


def _signal_process_group(process: subprocess.Popen[bytes], signal_number: int) -> bool:
    pid = getattr(process, "pid", None)
    if not isinstance(pid, int) or pid <= 1 or pid == os.getpgrp():
        return False
    try:
        os.killpg(pid, signal_number)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return True


def _terminate_and_reap_process_group(process: subprocess.Popen[bytes]) -> None:
    """Bounded TERM/KILL escalation for the helper's dedicated process session."""

    term_sent = _signal_process_group(process, signal.SIGTERM)
    _wait_bounded(process, _GROUP_TERM_GRACE_SECONDS)
    kill_sent = _signal_process_group(process, signal.SIGKILL)
    if not term_sent and not kill_sent:
        with suppress(OSError):
            process.kill()
    if not _wait_bounded(process, _GROUP_KILL_GRACE_SECONDS):
        with suppress(OSError):
            process.kill()
        _wait_bounded(process, _GROUP_KILL_GRACE_SECONDS)


@contextmanager
def _materialize_verified_native_executable(
    executable: _VerifiedNativeExecutable,
) -> Iterator[str]:
    """Copy verified bytes into a private fixed-root Darwin execution directory."""

    try:
        current = os.fstat(executable.fd)
    except OSError:
        raise _process_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_IDENTITY_LOST") from None
    if (
        executable._closed
        or not stat.S_ISREG(current.st_mode)
        or current.st_dev != executable.device
        or current.st_ino != executable.inode
        or current.st_size != executable.size
    ):
        raise _process_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_IDENTITY_LOST")
    try:
        with TemporaryDirectory(prefix="dbtobsb-native-", dir="/private/tmp") as directory:
            directory_path = Path(directory)
            directory_stat = directory_path.stat(follow_symlinks=False)
            if (
                not stat.S_ISDIR(directory_stat.st_mode)
                or directory_stat.st_uid != os.getuid()
                or stat.S_IMODE(directory_stat.st_mode) != 0o700
            ):
                raise OSError
            staged_path = directory_path / _HELPER_FILENAME
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            no_follow = getattr(os, "O_NOFOLLOW", None)
            if no_follow is None:
                raise OSError
            descriptor = os.open(staged_path, flags | no_follow, 0o700)
            digest = hashlib.sha256()
            copied = 0
            try:
                while copied < executable.size:
                    chunk = os.pread(
                        executable.fd, min(64 * 1024, executable.size - copied), copied
                    )
                    if not chunk:
                        raise OSError
                    digest.update(chunk)
                    view = memoryview(chunk)
                    while view:
                        written = os.write(descriptor, view)
                        if written <= 0:
                            raise OSError
                        view = view[written:]
                    copied += len(chunk)
                if os.pread(executable.fd, 1, copied):
                    raise OSError
                os.fchmod(descriptor, 0o500)
                os.fsync(descriptor)
                staged_stat = os.fstat(descriptor)
            finally:
                os.close(descriptor)
            source_after = os.fstat(executable.fd)
            if (
                source_after.st_dev != executable.device
                or source_after.st_ino != executable.inode
                or source_after.st_size != executable.size
                or copied != executable.size
                or digest.hexdigest() != executable.sha256
                or not stat.S_ISREG(staged_stat.st_mode)
                or staged_stat.st_uid != os.getuid()
                or stat.S_IMODE(staged_stat.st_mode) != 0o500
                or staged_stat.st_size != executable.size
            ):
                raise OSError
            yield str(staged_path)
    except DatabricksPlatformAdapterError:
        raise
    except OSError:
        raise _process_failure("DBTOBSB_INSTALLER_NATIVE_SECURE_EXECUTION_UNAVAILABLE") from None


class SubprocessNativeRunner:
    """Shell-free helper runner with streaming output and Darwin resource limits."""

    def run(
        self,
        executable: _VerifiedNativeExecutable,
        *,
        stdin: bytes,
        environment: Mapping[str, str],
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> NativeProcessResult:
        if sys.platform != "darwin" or not isinstance(executable, _VerifiedNativeExecutable):
            raise _process_failure("DBTOBSB_INSTALLER_NATIVE_PLATFORM_UNSUPPORTED")
        with _materialize_verified_native_executable(executable) as staged_path:
            return self._run_staged(
                executable=executable,
                staged_path=staged_path,
                stdin=stdin,
                environment=environment,
                timeout_seconds=timeout_seconds,
                max_output_bytes=max_output_bytes,
            )

    def _run_staged(
        self,
        *,
        executable: _VerifiedNativeExecutable,
        staged_path: str,
        stdin: bytes,
        environment: Mapping[str, str],
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> NativeProcessResult:
        try:
            process = subprocess.Popen(
                (_HELPER_FILENAME,),
                executable=staged_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=dict(environment),
                close_fds=True,
                cwd="/",
                start_new_session=True,
                preexec_fn=_darwin_resource_limits,
            )
        except OSError:
            raise _process_failure("DBTOBSB_INSTALLER_NATIVE_PROCESS_START_UNAVAILABLE") from None

        output = bytearray()
        oversized = threading.Event()
        read_failed = threading.Event()
        write_failed = threading.Event()

        def drain_stdout() -> None:
            try:
                if process.stdout is None:
                    read_failed.set()
                    return
                while chunk := process.stdout.read(4_096):
                    remaining = max_output_bytes + 1 - len(output)
                    if remaining > 0:
                        output.extend(chunk[:remaining])
                    if len(output) > max_output_bytes or len(chunk) > remaining:
                        oversized.set()
                        return
            except OSError:
                read_failed.set()

        def feed_stdin() -> None:
            try:
                if process.stdin is None:
                    write_failed.set()
                    return
                if process.stdin.write(stdin) != len(stdin):
                    write_failed.set()
                    with suppress(OSError):
                        process.stdin.close()
                    return
                process.stdin.close()
            except (BrokenPipeError, OSError):
                write_failed.set()

        reader = threading.Thread(
            target=drain_stdout,
            daemon=True,
            name="dbtobsb-native-bridge-output",
        )
        writer = threading.Thread(
            target=feed_stdin,
            daemon=True,
            name="dbtobsb-native-bridge-input",
        )
        reader.start()
        writer.start()
        return_code: int | None = None
        group_cleaned = False
        try:
            deadline = time.monotonic() + timeout_seconds
            while True:
                if oversized.is_set() or read_failed.is_set() or write_failed.is_set():
                    _terminate_and_reap_process_group(process)
                    group_cleaned = True
                    break
                remaining_seconds = deadline - time.monotonic()
                if remaining_seconds <= 0:
                    raise subprocess.TimeoutExpired(executable.installed_path, timeout_seconds)
                try:
                    return_code = process.wait(
                        timeout=min(_PROCESS_POLL_SECONDS, remaining_seconds)
                    )
                    break
                except subprocess.TimeoutExpired:
                    continue
        except subprocess.TimeoutExpired:
            _terminate_and_reap_process_group(process)
            reader.join(timeout=1.0)
            writer.join(timeout=1.0)
            raise _process_failure("DBTOBSB_INSTALLER_NATIVE_PROCESS_TIMEOUT") from None
        except KeyboardInterrupt:
            _terminate_and_reap_process_group(process)
            reader.join(timeout=1.0)
            writer.join(timeout=1.0)
            raise _process_failure("DBTOBSB_INSTALLER_NATIVE_PROCESS_INTERRUPTED") from None
        if return_code is not None and return_code != 0:
            _terminate_and_reap_process_group(process)
            group_cleaned = True
        reader.join(timeout=1.0)
        writer.join(timeout=1.0)
        if oversized.is_set():
            if not group_cleaned:
                _terminate_and_reap_process_group(process)
            return NativeProcessResult(
                return_code=(
                    process.returncode if getattr(process, "returncode", None) is not None else -1
                ),
                stdout=bytes(output),
                output_was_truncated=True,
            )
        if reader.is_alive() or writer.is_alive() or read_failed.is_set() or write_failed.is_set():
            if not group_cleaned:
                _terminate_and_reap_process_group(process)
            raise _process_failure("DBTOBSB_INSTALLER_NATIVE_PROCESS_UNAVAILABLE")
        return NativeProcessResult(
            return_code=return_code if return_code is not None else -1,
            stdout=bytes(output),
            output_was_truncated=oversized.is_set(),
        )


@dataclass(frozen=True, slots=True, repr=False)
class _ReleaseLayout:
    root_directory: Path
    directory: Path
    manifest_path: Path
    executable_path: Path
    expected_manifest_sha256: str | None = field(repr=False)

    @classmethod
    def production(cls) -> _ReleaseLayout:
        root_directory = Path(__file__).with_name("_native")
        directory = root_directory / _LAYOUT_DIRECTORY
        return cls(
            root_directory=root_directory,
            directory=directory,
            manifest_path=directory / "manifest.json",
            executable_path=directory / _HELPER_FILENAME,
            expected_manifest_sha256=_GENERATED_MANIFEST_SHA256,
        )

    def verify(self) -> _VerifiedNativeExecutable:
        if self.expected_manifest_sha256 is None:
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_NOT_PACKAGED")
        if not _is_sha256(self.expected_manifest_sha256):
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_SEAL_INVALID")
        if sys.platform != "darwin" or platform.machine().lower() != "arm64":
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_PLATFORM_UNSUPPORTED")
        if (
            not self.root_directory.is_absolute()
            or self.directory != self.root_directory / _LAYOUT_DIRECTORY
            or self.manifest_path != self.directory / "manifest.json"
            or self.executable_path != self.directory / _HELPER_FILENAME
        ):
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_PATH_INVALID")
        _verify_fixed_path(self.root_directory, expect_directory=True)
        _verify_fixed_path(self.directory, expect_directory=True)
        _verify_fixed_path(self.manifest_path, expect_directory=False)
        _verify_fixed_path(self.executable_path, expect_directory=False, executable=True)
        try:
            manifest_raw = self.manifest_path.read_bytes()
        except OSError:
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_UNAVAILABLE") from None
        if not manifest_raw or len(manifest_raw) > _MAX_MANIFEST_BYTES:
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
        manifest = _strict_json_object(manifest_raw, "DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
        canonical = (
            json.dumps(manifest, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
                "ascii"
            )
            + b"\n"
        )
        if (
            manifest_raw != canonical
            or hashlib.sha256(canonical).hexdigest() != self.expected_manifest_sha256
        ):
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_SEAL_MISMATCH")
        helper_sha256, helper_size = _validate_manifest(manifest)
        fd = -1
        try:
            fd = _open_executable_no_follow(self.executable_path)
            executable_stat = os.fstat(fd)
            with os.fdopen(os.dup(fd), "rb") as executable:
                digest = hashlib.file_digest(executable, "sha256").hexdigest()
            os.lseek(fd, 0, os.SEEK_SET)
        except OSError:
            if fd >= 0:
                with suppress(OSError):
                    os.close(fd)
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_UNAVAILABLE") from None
        if (
            not stat.S_ISREG(executable_stat.st_mode)
            or executable_stat.st_uid != os.getuid()
            or executable_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            or not executable_stat.st_mode & stat.S_IXUSR
            or executable_stat.st_size != helper_size
            or digest != helper_sha256
        ):
            with suppress(OSError):
                os.close(fd)
            raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_SEAL_MISMATCH")
        return _VerifiedNativeExecutable(
            installed_path=str(self.executable_path),
            fd=fd,
            device=executable_stat.st_dev,
            inode=executable_stat.st_ino,
            size=executable_stat.st_size,
            sha256=helper_sha256,
            _construction_token=_VERIFIED_EXECUTABLE_TOKEN,
        )


def _verify_fixed_path(path: Path, *, expect_directory: bool, executable: bool = False) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_NOT_PACKAGED") from None
    expected_type = stat.S_ISDIR(info.st_mode) if expect_directory else stat.S_ISREG(info.st_mode)
    if not expected_type or stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_PATH_INVALID")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_MODE_INVALID")
    if executable and not info.st_mode & stat.S_IXUSR:
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_RELEASE_MODE_INVALID")


def _open_executable_no_follow(path: Path) -> int:
    flags = os.O_RDONLY | os.O_CLOEXEC
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if not isinstance(no_follow, int):
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_FD_EXECUTION_UNAVAILABLE")
    try:
        return os.open(path, flags | no_follow)
    except OSError:
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_UNAVAILABLE") from None


def _validate_manifest(document: dict[str, Any]) -> tuple[str, int]:
    if set(document) != {
        "arch",
        "databricks_cli",
        "helper",
        "os",
        "protocol",
        "schema",
        "sdk",
    }:
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
    if (
        document["schema"] != _MANIFEST_SCHEMA
        or document["protocol"] != _PROTOCOL
        or document["os"] != "darwin"
        or document["arch"] != "arm64"
        or document["databricks_cli"] != _EXPECTED_CLI
        or document["sdk"] != _EXPECTED_SDK
    ):
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
    helper = document["helper"]
    if not isinstance(helper, dict) or set(helper) != {"filename", "sha256", "size"}:
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
    helper = cast(dict[str, object], helper)
    size = helper["size"]
    if (
        helper["filename"] != _HELPER_FILENAME
        or not _is_sha256(helper["sha256"])
        or isinstance(size, bool)
        or not isinstance(size, int)
        or not 1 <= size <= 128 * 1024 * 1024
    ):
        raise _seal_failure("DBTOBSB_INSTALLER_NATIVE_MANIFEST_INVALID")
    return cast(str, helper["sha256"]), size


def _positive_environment(environment: Mapping[str, str]) -> dict[str, str]:
    reject_inherited_credential_environment(environment)
    if any(name.startswith("AZURE_") and value for name, value in environment.items()):
        raise InstallerAuthError("DBTOBSB_INSTALLER_INHERITED_CREDENTIAL_REJECTED")
    allowed = {
        "APPDATA",
        "DBUS_SESSION_BUS_ADDRESS",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOCALAPPDATA",
        "LOGNAME",
        "SystemRoot",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
        "USER",
        "USERPROFILE",
        "WINDIR",
        "XDG_RUNTIME_DIR",
    }
    result = {name: value for name, value in environment.items() if name in allowed and value}
    result["DATABRICKS_AUTH_STORAGE"] = "secure"
    return result


@dataclass(frozen=True, slots=True, repr=False)
class NativeResponse:
    ok: bool
    code: str
    result: dict[str, Any] | None = field(repr=False)

    def __repr__(self) -> str:
        return f"NativeResponse(ok={self.ok!r}, code={self.code!r}, <redacted>)"


class _NativeBridgeLauncher:
    """Fixed production launcher; caller-controlled paths exist only in ``_for_test``."""

    def __init__(self) -> None:
        self._layout = _ReleaseLayout.production()
        self._runner: NativeProcessRunner = SubprocessNativeRunner()
        self._environment: Mapping[str, str] = os.environ

    @classmethod
    def _for_test(
        cls,
        *,
        layout_directory: Path,
        expected_manifest_sha256: str,
        runner: NativeProcessRunner,
        environment: Mapping[str, str],
    ) -> _NativeBridgeLauncher:
        launcher = cls.__new__(cls)
        launcher._layout = _ReleaseLayout(
            root_directory=layout_directory.parent,
            directory=layout_directory,
            manifest_path=layout_directory / "manifest.json",
            executable_path=layout_directory / _HELPER_FILENAME,
            expected_manifest_sha256=expected_manifest_sha256,
        )
        launcher._runner = runner
        launcher._environment = environment
        return launcher

    def __repr__(self) -> str:
        return "_NativeBridgeLauncher(<redacted>)"

    def _invoke(
        self,
        *,
        stage: FailureStage,
        operation: str,
        profile: str,
        canonical_host: str,
        payload: dict[str, object],
    ) -> NativeResponse:
        try:
            executable = self._layout.verify()
        except DatabricksPlatformAdapterError:
            raise
        try:
            return self._invoke_verified(
                executable=executable,
                stage=stage,
                operation=operation,
                profile=profile,
                canonical_host=canonical_host,
                payload=payload,
            )
        finally:
            executable.close()

    def _invoke_verified(
        self,
        *,
        executable: _VerifiedNativeExecutable,
        stage: FailureStage,
        operation: str,
        profile: str,
        canonical_host: str,
        payload: dict[str, object],
    ) -> NativeResponse:
        try:
            child_environment = _positive_environment(self._environment)
        except InstallerAuthError as error:
            raise _failure_for_code(error.code, FailureStage.AUTH_CONFIGURATION) from None
        stdin = (
            json.dumps(
                {
                    "canonical_host": canonical_host,
                    "operation": operation,
                    "payload": payload,
                    "profile": profile,
                    "protocol": _PROTOCOL,
                },
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            + b"\n"
        )
        if len(stdin) > _MAX_INPUT_BYTES:
            raise _failure_for_code("DBTOBSB_INSTALLER_NATIVE_REQUEST_TOO_LARGE", stage)
        try:
            process = self._runner.run(
                executable,
                stdin=stdin,
                environment=child_environment,
                timeout_seconds=_PROCESS_TIMEOUT_SECONDS,
                max_output_bytes=_MAX_OUTPUT_BYTES,
            )
        except DatabricksPlatformAdapterError as error:
            if error.failure.stage is FailureStage.PROCESS:
                raise
            raise
        except KeyboardInterrupt:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_NATIVE_PROCESS_INTERRUPTED",
                stage,
                possible_running_or_cost=True,
            ) from None
        except Exception:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_NATIVE_PROCESS_UNAVAILABLE",
                stage,
                possible_running_or_cost=True,
            ) from None
        if process.output_was_truncated:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_NATIVE_OUTPUT_TOO_LARGE",
                stage,
                possible_running_or_cost=True,
            )
        response = _parse_response(process.stdout, stage)
        if (response.ok and process.return_code != 0) or (
            not response.ok and process.return_code != 1
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_NATIVE_EXIT_RESPONSE_MISMATCH",
                stage,
                possible_running_or_cost=True,
            )
        if not response.ok:
            raise _failure_for_native_code(response.code, stage)
        return response


_NATIVE_FAILURE_CODES = frozenset(
    {
        "DBTOBSB_NATIVE_ACTOR_INDETERMINATE",
        "DBTOBSB_NATIVE_ACTOR_MISMATCH",
        "DBTOBSB_NATIVE_ACTOR_RESPONSE_INVALID",
        "DBTOBSB_NATIVE_AUTH_TYPE_INVALID",
        "DBTOBSB_NATIVE_AUTH_UNAVAILABLE",
        "DBTOBSB_NATIVE_CANCEL_INDETERMINATE",
        "DBTOBSB_NATIVE_CANCEL_RESPONSE_INVALID",
        "DBTOBSB_NATIVE_ENVIRONMENT_INVALID",
        "DBTOBSB_NATIVE_HISTORY_RESPONSE_INVALID",
        "DBTOBSB_NATIVE_HISTORY_UNAVAILABLE",
        "DBTOBSB_NATIVE_HOST_INVALID",
        "DBTOBSB_NATIVE_HOST_MISMATCH",
        "DBTOBSB_NATIVE_INPUT_TOO_LARGE",
        "DBTOBSB_NATIVE_INTERNAL_FAILURE",
        "DBTOBSB_NATIVE_OPERATION_DENIED",
        "DBTOBSB_NATIVE_PROFILE_INVALID",
        "DBTOBSB_NATIVE_PROFILE_UNAVAILABLE",
        "DBTOBSB_NATIVE_PROTOCOL_INVALID",
        "DBTOBSB_NATIVE_REDIRECT_REJECTED",
        "DBTOBSB_NATIVE_RELEASE_BUILD_INVALID",
        "DBTOBSB_NATIVE_REQUEST_INVALID",
        "DBTOBSB_NATIVE_RESPONSE_TOO_LARGE",
        "DBTOBSB_NATIVE_STATEMENT_INDETERMINATE",
        "DBTOBSB_NATIVE_STATEMENT_RESPONSE_INVALID",
        "DBTOBSB_NATIVE_REGISTRY_OPERATION_DENIED",
        "DBTOBSB_NATIVE_REGISTRY_PARAMETERS_INVALID",
        "DBTOBSB_NATIVE_REGISTRY_DIGEST_MISMATCH",
    }
)

_PRE_NETWORK_NATIVE_CODES = frozenset(
    {
        "DBTOBSB_NATIVE_AUTH_TYPE_INVALID",
        "DBTOBSB_NATIVE_AUTH_UNAVAILABLE",
        "DBTOBSB_NATIVE_ENVIRONMENT_INVALID",
        "DBTOBSB_NATIVE_HOST_INVALID",
        "DBTOBSB_NATIVE_HOST_MISMATCH",
        "DBTOBSB_NATIVE_INPUT_TOO_LARGE",
        "DBTOBSB_NATIVE_OPERATION_DENIED",
        "DBTOBSB_NATIVE_PROFILE_INVALID",
        "DBTOBSB_NATIVE_PROFILE_UNAVAILABLE",
        "DBTOBSB_NATIVE_PROTOCOL_INVALID",
        "DBTOBSB_NATIVE_RELEASE_BUILD_INVALID",
        "DBTOBSB_NATIVE_REQUEST_INVALID",
    }
)

_NATIVE_SUCCESS_CODES = frozenset(
    {
        "DBTOBSB_NATIVE_ACTOR_MATCHED",
        "DBTOBSB_NATIVE_ACTOR_FINGERPRINT_OBSERVED",
        "DBTOBSB_NATIVE_CANCEL_ACCEPTED",
        "DBTOBSB_NATIVE_CANCEL_REJECTED",
        "DBTOBSB_NATIVE_HISTORY_PAGE",
        "DBTOBSB_NATIVE_STATEMENT_RECEIPT",
    }
)


def _parse_response(raw: bytes, stage: FailureStage) -> NativeResponse:
    def remote_failure(code: str) -> DatabricksPlatformAdapterError:
        return _failure_for_code(code, stage, possible_running_or_cost=True)

    if not raw:
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_NO_OUTPUT")
    if len(raw) > _MAX_OUTPUT_BYTES or not raw.endswith(b"\n") or b"\n" in raw[:-1]:
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
    try:
        document = _strict_json_object(raw[:-1], "DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID", stage)
    except DatabricksPlatformAdapterError:
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID") from None
    if set(document) not in (
        {"code", "ok", "protocol"},
        {"code", "ok", "protocol", "result"},
    ):
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
    ok = document["ok"]
    code = document["code"]
    if (
        document["protocol"] != _PROTOCOL
        or not isinstance(ok, bool)
        or not isinstance(code, str)
        or code not in _NATIVE_FAILURE_CODES | _NATIVE_SUCCESS_CODES
    ):
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
    if ok:
        if code not in _NATIVE_SUCCESS_CODES or set(document) != {
            "code",
            "ok",
            "protocol",
            "result",
        }:
            raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
        result = document["result"]
        if not isinstance(result, dict):
            raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
        return NativeResponse(True, code, cast(dict[str, Any], result))
    if code not in _NATIVE_FAILURE_CODES or set(document) != {"code", "ok", "protocol"}:
        raise remote_failure("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID")
    return NativeResponse(False, code, None)


def _strict_json_object(
    raw: bytes,
    code: str,
    stage: FailureStage = FailureStage.RELEASE_SEAL,
) -> dict[str, Any]:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise _failure_for_code(code, stage) from None
    if not isinstance(value, dict):
        raise _failure_for_code(code, stage)
    return cast(dict[str, Any], value)


def _is_sha256(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _seal_failure(code: str) -> DatabricksPlatformAdapterError:
    return DatabricksPlatformAdapterError(
        AdapterFailure(
            code=code,
            stage=FailureStage.RELEASE_SEAL,
            possible_running_or_cost=False,
            responsible_actor="RELEASE_OPERATOR",
            retry_class=RetryClass.RETRY_AFTER_CORRECTION,
            safe_next_action="Install the signed release artifact, then verify its seal again.",
        )
    )


def _process_failure(code: str) -> DatabricksPlatformAdapterError:
    possible = code in {
        "DBTOBSB_INSTALLER_NATIVE_PROCESS_INTERRUPTED",
        "DBTOBSB_INSTALLER_NATIVE_PROCESS_TIMEOUT",
        "DBTOBSB_INSTALLER_NATIVE_PROCESS_UNAVAILABLE",
    }
    return DatabricksPlatformAdapterError(
        AdapterFailure(
            code=code,
            stage=FailureStage.PROCESS,
            possible_running_or_cost=possible,
            responsible_actor="INSTALLER_OPERATOR",
            retry_class=RetryClass.RETRY_AFTER_CORRECTION,
            safe_next_action="Correct the local process condition before another attempt.",
        )
    )


def _failure_for_native_code(code: str, stage: FailureStage) -> DatabricksPlatformAdapterError:
    if code not in _NATIVE_FAILURE_CODES:
        return _failure_for_code("DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID", stage)
    product_code = "DBTOBSB_INSTALLER_" + code.removeprefix("DBTOBSB_NATIVE_")
    if code in {
        "DBTOBSB_NATIVE_REGISTRY_OPERATION_DENIED",
        "DBTOBSB_NATIVE_REGISTRY_PARAMETERS_INVALID",
        "DBTOBSB_NATIVE_REGISTRY_DIGEST_MISMATCH",
    }:
        return _failure_for_code(product_code, stage)
    if code in _PRE_NETWORK_NATIVE_CODES:
        return _failure_for_code(
            product_code,
            FailureStage.AUTH_CONFIGURATION,
        )
    return _failure_for_code(
        product_code,
        stage,
        possible_running_or_cost=True,
    )


def _failure_for_code(
    code: str,
    stage: FailureStage,
    *,
    possible_running_or_cost: bool = False,
) -> DatabricksPlatformAdapterError:
    retry_class = RetryClass.DO_NOT_RETRY
    action = "Stop and inspect the sanitized installer recovery state."
    responsible = "INSTALLER_OPERATOR"
    if stage is FailureStage.AUTH_CONFIGURATION:
        retry_class = RetryClass.RETRY_AFTER_CORRECTION
        action = (
            "Stop. Return to the approved actor's managed OS account and resume with "
            "dbtobsb bootstrap."
        )
    elif stage is FailureStage.QUERY_HISTORY:
        retry_class = RetryClass.BOUNDED_READ_ONLY_RETRY
        action = "Open the installer-provided signed-operation Query History route."
    elif stage is FailureStage.CANCELLATION:
        retry_class = RetryClass.RECONCILE_BEFORE_RETRY
        action = "Reconcile Query History and live state before another cancellation request."
        responsible = "WAREHOUSE_MANAGER"
    elif stage is FailureStage.STATEMENT_SUBMISSION:
        retry_class = RetryClass.RECONCILE_BEFORE_RETRY
        action = "Reconcile the signed operation in Query History before any later action."
    elif code == "DBTOBSB_INSTALLER_ACTOR_MISMATCH":
        action = (
            "Stop. Return to the approved actor's managed OS account and resume with "
            "dbtobsb bootstrap."
        )
    return DatabricksPlatformAdapterError(
        AdapterFailure(
            code=code,
            stage=stage,
            possible_running_or_cost=possible_running_or_cost,
            responsible_actor=responsible,
            retry_class=retry_class,
            safe_next_action=action,
        )
    )


__all__ = [
    "AdapterFailure",
    "DatabricksPlatformAdapterError",
    "FailureStage",
    "NativeProcessResult",
    "RetryClass",
    "SubprocessNativeRunner",
]
