#!/usr/bin/env python3
"""Build and verify the sealed darwin-arm64 dbtobsb installer wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import urllib.parse
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_ROOT = REPO_ROOT / "installer"
NATIVE_ROOT = REPO_ROOT / "native"
PACKAGE_NAME = "dbtobsb_installer"
HELPER_NAME = "dbtobsb-native-bridge"
LAYOUT = Path("_native") / "darwin-arm64"
MANIFEST_SCHEMA = "dbtobsb.native-helper-release.v1"
PROTOCOL = "dbtobsb.native-bridge.v1"
WHEEL_TAG = "py3-none-macosx_11_0_arm64"
SOURCE_DATE_EPOCH = "315532800"
EXPECTED_CLI = {
    "commit": "2f68ee4951ef96fa9d99e40c8ebadccf08412d58",
    "module": "github.com/databricks/cli",
    "module_sum": "h1:rXIWpyz11eng0BJ3b83MHkmvxqHhbID1xa9nHRu9lHA=",
    "version": "v1.7.0",
}
EXPECTED_SDK = {
    "module": "github.com/databricks/databricks-sdk-go",
    "module_sum": "h1:Vmif0i0rbu7kgphoEBPRroZNd5uLBOITvjU4dr2lwXY=",
    "version": "v0.154.0",
}


class ReleaseBuildError(RuntimeError):
    """Stable build failure without subprocess or environment details."""


def _run(command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
    try:
        subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_BUILD_FAILED") from None


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _canonical_json(document: dict[str, object]) -> bytes:
    return (
        json.dumps(
            document, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("ascii")
        + b"\n"
    )


def _copy_installer_source(destination: Path) -> Path:
    project = destination / "installer"
    project.mkdir(parents=True, mode=0o755)
    pyproject = project / "pyproject.toml"
    shutil.copy2(INSTALLER_ROOT / "pyproject.toml", pyproject)
    configuration = pyproject.read_text(encoding="utf-8")
    wheel_table = "[tool.hatch.build.targets.wheel]"
    if configuration.count(wheel_table) != 1:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_CONFIGURATION_INVALID")
    pyproject.write_text(
        configuration.replace(
            wheel_table,
            wheel_table + '\nsbom-files = ["sbom.spdx.json"]',
        )
        + "\n[tool.hatch.build.targets.wheel.hooks.custom]\n"
        + 'path = "hatch_build.py"\n',
        encoding="utf-8",
    )
    (project / "hatch_build.py").write_text(
        "from hatchling.builders.hooks.plugin.interface import BuildHookInterface\n\n\n"
        "class CustomBuildHook(BuildHookInterface):\n"
        "    def initialize(self, version, build_data):\n"
        f'        build_data["tag"] = "{WHEEL_TAG}"\n'
        '        build_data["pure_python"] = False\n',
        encoding="ascii",
    )
    source = INSTALLER_ROOT / "src" / PACKAGE_NAME
    package = project / "src" / PACKAGE_NAME
    shutil.copytree(
        source,
        package,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "_native",
            "_generated_native_release_seal.py",
        ),
    )
    return project


def _build_helper(destination: Path, environment: dict[str, str]) -> Path:
    first = destination / f"{HELPER_NAME}.first"
    second = destination / f"{HELPER_NAME}.second"
    build = (
        "go",
        "build",
        "-trimpath",
        "-buildvcs=false",
        "-ldflags=-buildid=",
    )
    _run(
        (*build, "-o", str(first), "./cmd/dbtobsb-native-bridge"),
        cwd=NATIVE_ROOT,
        environment=environment,
    )
    _run(
        (*build, "-o", str(second), "./cmd/dbtobsb-native-bridge"),
        cwd=NATIVE_ROOT,
        environment=environment,
    )
    if first.read_bytes() != second.read_bytes():
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_NOT_REPRODUCIBLE")
    second.unlink()
    first.chmod(0o755)
    return first


def _verify_cli_origin(environment: dict[str, str]) -> None:
    try:
        result = subprocess.run(
            (
                "go",
                "mod",
                "download",
                "-json",
                f"{EXPECTED_CLI['module']}@{EXPECTED_CLI['version']}",
            ),
            cwd=NATIVE_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_ORIGIN_INVALID") from None
    if not result.stdout or len(result.stdout) > 64 * 1024:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_ORIGIN_INVALID")

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        document: dict[str, object] = {}
        for key, value in pairs:
            if key in document:
                raise ValueError
            document[key] = value
        return document

    try:
        document = json.loads(result.stdout, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_ORIGIN_INVALID") from None
    if not isinstance(document, dict):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_ORIGIN_INVALID")
    origin = document.get("Origin")
    if (
        document.get("Path") != EXPECTED_CLI["module"]
        or document.get("Version") != EXPECTED_CLI["version"]
        or document.get("Sum") != EXPECTED_CLI["module_sum"]
        or not isinstance(origin, dict)
        or origin
        != {
            "Hash": EXPECTED_CLI["commit"],
            "Ref": f"refs/tags/{EXPECTED_CLI['version']}",
            "URL": "https://github.com/databricks/cli",
            "VCS": "git",
        }
        or "Replace" in document
        or "Error" in document
    ):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_ORIGIN_INVALID")


def _go_components(
    helper: Path, environment: dict[str, str]
) -> tuple[dict[str, str], ...]:
    try:
        result = subprocess.run(
            ("go", "version", "-m", str(helper)),
            cwd=NATIVE_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID") from None
    if not result.stdout or len(result.stdout) > 256 * 1024:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID")
    try:
        build_information = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID") from None
    components: list[dict[str, str]] = []
    for line in build_information.splitlines():
        fields = line.strip().split("\t")
        if fields and fields[0] == "=>":
            raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID")
        if len(fields) == 4 and fields[0] == "dep":
            _, module, version, module_sum = fields
            if (
                not module
                or not version
                or not module_sum.startswith("h1:")
                or any(
                    character.isspace() for character in module + version + module_sum
                )
            ):
                raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID")
            components.append(
                {"module": module, "module_sum": module_sum, "version": version}
            )
    ordered = tuple(sorted(components, key=lambda item: item["module"].encode("ascii")))
    if not ordered or len({item["module"] for item in ordered}) != len(ordered):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID")
    by_module = {item["module"]: item for item in ordered}
    if by_module.get(EXPECTED_CLI["module"]) != {
        "module": EXPECTED_CLI["module"],
        "module_sum": EXPECTED_CLI["module_sum"],
        "version": EXPECTED_CLI["version"],
    } or by_module.get(EXPECTED_SDK["module"]) != {
        "module": EXPECTED_SDK["module"],
        "module_sum": EXPECTED_SDK["module_sum"],
        "version": EXPECTED_SDK["version"],
    }:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_NATIVE_BUILD_INFO_INVALID")
    return ordered


def _spdx_sbom(
    *,
    helper_sha256: str,
    helper_size: int,
    components: tuple[dict[str, str], ...],
    release_version: str,
) -> bytes:
    helper_id = "SPDXRef-Package-dbtobsb-native-bridge"
    packages: list[dict[str, object]] = [
        {
            "SPDXID": helper_id,
            "checksums": [{"algorithm": "SHA256", "checksumValue": helper_sha256}],
            "copyrightText": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "name": HELPER_NAME,
            "primaryPackagePurpose": "APPLICATION",
            "versionInfo": release_version,
        }
    ]
    relationships: list[dict[str, str]] = [
        {
            "relatedSpdxElement": helper_id,
            "relationshipType": "DESCRIBES",
            "spdxElementId": "SPDXRef-DOCUMENT",
        }
    ]
    for index, component in enumerate(components, start=1):
        component_id = f"SPDXRef-GoModule-{index:03d}"
        locator = (
            "pkg:golang/"
            + urllib.parse.quote(component["module"], safe="/")
            + "@"
            + urllib.parse.quote(component["version"], safe="")
        )
        packages.append(
            {
                "SPDXID": component_id,
                "comment": f"Go module sum: {component['module_sum']}",
                "copyrightText": "NOASSERTION",
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceLocator": locator,
                        "referenceType": "purl",
                    }
                ],
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "name": component["module"],
                "primaryPackagePurpose": "LIBRARY",
                "versionInfo": component["version"],
            }
        )
        relationships.append(
            {
                "relatedSpdxElement": component_id,
                "relationshipType": "DEPENDS_ON",
                "spdxElementId": helper_id,
            }
        )
    document: dict[str, object] = {
        "SPDXID": "SPDXRef-DOCUMENT",
        "creationInfo": {
            "created": "1980-01-01T00:00:00Z",
            "creators": ["Tool: dbtobsb-release-builder-v1"],
        },
        "dataLicense": "CC0-1.0",
        "documentNamespace": (
            "https://github.com/miguelperedo/dbtobsb/sbom/" + helper_sha256
        ),
        "name": f"dbtobsb-native-bridge-{helper_sha256[:12]}",
        "packages": packages,
        "relationships": relationships,
        "spdxVersion": "SPDX-2.3",
    }
    rendered = _canonical_json(document)
    if len(rendered) > 1024 * 1024 or helper_size < 1:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_SBOM_INVALID")
    return rendered


def _stage_release(
    project: Path,
    helper: Path,
    components: tuple[dict[str, str], ...],
) -> tuple[str, int, str]:
    try:
        release_version = tomllib.loads(
            (project / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"]
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, KeyError, TypeError):
        raise ReleaseBuildError(
            "DBTOBSB_INSTALLER_RELEASE_CONFIGURATION_INVALID"
        ) from None
    if (
        not isinstance(release_version, str)
        or not release_version.isascii()
        or not release_version
        or len(release_version) > 64
        or any(character.isspace() for character in release_version)
    ):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_CONFIGURATION_INVALID")
    package = project / "src" / PACKAGE_NAME
    layout = package / LAYOUT
    layout.mkdir(parents=True, mode=0o755)
    packaged_helper = layout / HELPER_NAME
    shutil.copyfile(helper, packaged_helper)
    packaged_helper.chmod(0o755)
    helper_sha256 = _sha256(packaged_helper)
    helper_size = packaged_helper.stat().st_size
    manifest: dict[str, object] = {
        "arch": "arm64",
        "databricks_cli": EXPECTED_CLI,
        "helper": {
            "filename": HELPER_NAME,
            "sha256": helper_sha256,
            "size": helper_size,
        },
        "os": "darwin",
        "protocol": PROTOCOL,
        "schema": MANIFEST_SCHEMA,
        "sdk": EXPECTED_SDK,
    }
    manifest_raw = _canonical_json(manifest)
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
    (layout / "manifest.json").write_bytes(manifest_raw)
    seal = package / "_generated_native_release_seal.py"
    seal.write_text(
        '"""Generated native release seal; do not edit."""\n\n'
        f'MANIFEST_SHA256 = "{manifest_sha256}"\n',
        encoding="ascii",
    )
    for path in (layout / "manifest.json", seal):
        path.chmod(0o644)
    sbom_raw = _spdx_sbom(
        helper_sha256=helper_sha256,
        helper_size=helper_size,
        components=components,
        release_version=release_version,
    )
    (project / "sbom.spdx.json").write_bytes(sbom_raw)
    return manifest_sha256, helper_size, hashlib.sha256(sbom_raw).hexdigest()


def _wheel_member(names: tuple[str, ...], suffix: str) -> str:
    matches = tuple(name for name in names if name.endswith(suffix))
    if len(matches) != 1:
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID")
    return matches[0]


def _verify_wheel(
    wheel: Path,
    manifest_sha256: str,
    helper_size: int,
    sbom_sha256: str,
) -> None:
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = tuple(archive.namelist())
            helper_name = _wheel_member(names, f"/{LAYOUT.as_posix()}/{HELPER_NAME}")
            manifest_name = _wheel_member(names, f"/{LAYOUT.as_posix()}/manifest.json")
            seal_name = _wheel_member(names, "/_generated_native_release_seal.py")
            wheel_metadata_name = _wheel_member(names, ".dist-info/WHEEL")
            sbom_name = _wheel_member(names, ".dist-info/sboms/sbom.spdx.json")
            helper = archive.read(helper_name)
            manifest_raw = archive.read(manifest_name)
            seal_raw = archive.read(seal_name)
            wheel_metadata = archive.read(wheel_metadata_name)
            sbom_raw = archive.read(sbom_name)
            mode = archive.getinfo(helper_name).external_attr >> 16
    except (OSError, KeyError, zipfile.BadZipFile):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID") from None
    try:
        manifest = json.loads(manifest_raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID") from None
    if (
        not isinstance(manifest, dict)
        or manifest_raw != _canonical_json(manifest)
        or hashlib.sha256(manifest_raw).hexdigest() != manifest_sha256
        or len(helper) != helper_size
        or hashlib.sha256(helper).hexdigest()
        != manifest.get("helper", {}).get("sha256")
        or not stat.S_ISREG(mode)
        or stat.S_IMODE(mode) != 0o755
        or f"Tag: {WHEEL_TAG}\n".encode("ascii") not in wheel_metadata
        or b"Root-Is-Purelib: false\n" not in wheel_metadata
        or hashlib.sha256(sbom_raw).hexdigest() != sbom_sha256
        or seal_raw
        != (
            '"""Generated native release seal; do not edit."""\n\n'
            f'MANIFEST_SHA256 = "{manifest_sha256}"\n'
        ).encode("ascii")
    ):
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID")


def build_release(output_directory: Path) -> Path:
    """Build twice, prove byte reproducibility, and publish one verified wheel."""
    if not output_directory.is_absolute():
        raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_OUTPUT_INVALID")
    output_directory.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(
        {
            "CGO_ENABLED": "0",
            "GOARCH": "arm64",
            "GOOS": "darwin",
            "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
            "TZ": "UTC",
        }
    )
    with tempfile.TemporaryDirectory(prefix="dbtobsb-installer-release-") as temporary:
        root = Path(temporary)
        helper = _build_helper(root, environment)
        _verify_cli_origin(environment)
        components = _go_components(helper, environment)
        wheels: list[Path] = []
        manifest_sha256 = ""
        helper_size = 0
        sbom_sha256 = ""
        for ordinal in (1, 2):
            project = _copy_installer_source(root / f"stage-{ordinal}")
            manifest_sha256, helper_size, sbom_sha256 = _stage_release(
                project,
                helper,
                components,
            )
            wheel_output = root / f"wheel-{ordinal}"
            wheel_output.mkdir()
            _run(
                (
                    "uv",
                    "build",
                    "--wheel",
                    "--no-sources",
                    "--offline",
                    "--no-progress",
                    "--out-dir",
                    str(wheel_output),
                    str(project),
                ),
                cwd=REPO_ROOT,
                environment=environment,
            )
            candidates = tuple(wheel_output.glob("*.whl"))
            if len(candidates) != 1:
                raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID")
            if not candidates[0].name.endswith(f"-{WHEEL_TAG}.whl"):
                raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_INVALID")
            _verify_wheel(candidates[0], manifest_sha256, helper_size, sbom_sha256)
            wheels.append(candidates[0])
        if wheels[0].read_bytes() != wheels[1].read_bytes():
            raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_WHEEL_NOT_REPRODUCIBLE")
        destination = output_directory / wheels[0].name
        if destination.exists() and destination.read_bytes() != wheels[0].read_bytes():
            raise ReleaseBuildError("DBTOBSB_INSTALLER_RELEASE_OUTPUT_CONFLICT")
        shutil.copyfile(wheels[0], destination)
        destination.chmod(0o644)
        _verify_wheel(destination, manifest_sha256, helper_size, sbom_sha256)
        return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        wheel = build_release(arguments.out_dir.resolve())
    except ReleaseBuildError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
