"""Nonsecret connection validation for the attended native installer."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

_PROFILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_AZURE_WORKSPACE_HOST = re.compile(r"^https://adb-[0-9]{1,20}\.[0-9]{1,20}\.azuredatabricks\.net$")
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_CREDENTIAL_ENVIRONMENT_PREFIXES = ("DATABRICKS_", "ARM_")
_CREDENTIAL_ENVIRONMENT_NAMES = frozenset(
    {
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_FEDERATED_TOKEN_FILE",
        "AZURE_PASSWORD",
        "AZURE_TENANT_ID",
        "AZURE_USERNAME",
    }
)
_VALIDATED_CONNECTION_TOKEN = object()


class InstallerAuthError(RuntimeError):
    """Fail-closed connection-policy error containing only a stable code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class InstallerConnectionInputs:
    """Explicit nonsecret connection inputs; there is no default-profile fallback."""

    profile: str
    canonical_host: str
    installer_warehouse_id: str

    def __repr__(self) -> str:
        return "InstallerConnectionInputs(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ValidatedInstallerConnection:
    """Validated nonsecret binding consumed by sealed native adapters."""

    profile: str
    canonical_host: str
    installer_warehouse_id: str

    def __init__(
        self,
        *,
        profile: str,
        canonical_host: str,
        installer_warehouse_id: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _VALIDATED_CONNECTION_TOKEN:
            raise InstallerAuthError("DBTOBSB_INSTALLER_CONNECTION_CONSTRUCTION_DENIED")
        if _PROFILE.fullmatch(profile) is None:
            raise InstallerAuthError("DBTOBSB_INSTALLER_PROFILE_INVALID")
        if _AZURE_WORKSPACE_HOST.fullmatch(canonical_host) is None:
            raise InstallerAuthError("DBTOBSB_INSTALLER_HOST_INVALID")
        if _WAREHOUSE_ID.fullmatch(installer_warehouse_id) is None:
            raise InstallerAuthError("DBTOBSB_INSTALLER_WAREHOUSE_INVALID")
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "canonical_host", canonical_host)
        object.__setattr__(self, "installer_warehouse_id", installer_warehouse_id)

    def __repr__(self) -> str:
        return "ValidatedInstallerConnection(<redacted>)"


def validate_connection(inputs: InstallerConnectionInputs) -> ValidatedInstallerConnection:
    """Validate one explicit Azure workspace/profile/dedicated-warehouse binding."""
    if not all(
        isinstance(value, str)
        for value in (inputs.profile, inputs.canonical_host, inputs.installer_warehouse_id)
    ):
        raise InstallerAuthError("DBTOBSB_INSTALLER_CONNECTION_INVALID")
    if _PROFILE.fullmatch(inputs.profile) is None:
        raise InstallerAuthError("DBTOBSB_INSTALLER_PROFILE_INVALID")
    if _AZURE_WORKSPACE_HOST.fullmatch(inputs.canonical_host) is None:
        raise InstallerAuthError("DBTOBSB_INSTALLER_HOST_INVALID")
    if _WAREHOUSE_ID.fullmatch(inputs.installer_warehouse_id) is None:
        raise InstallerAuthError("DBTOBSB_INSTALLER_WAREHOUSE_INVALID")
    return ValidatedInstallerConnection(
        profile=inputs.profile,
        canonical_host=inputs.canonical_host,
        installer_warehouse_id=inputs.installer_warehouse_id,
        _construction_token=_VALIDATED_CONNECTION_TOKEN,
    )


def reject_inherited_credential_environment(environment: Mapping[str, str]) -> None:
    """Reject inherited credential, profile, and host overrides before native execution."""
    for name, value in environment.items():
        if not value:
            continue
        if name in _CREDENTIAL_ENVIRONMENT_NAMES or name.startswith(
            _CREDENTIAL_ENVIRONMENT_PREFIXES
        ):
            raise InstallerAuthError("DBTOBSB_INSTALLER_INHERITED_CREDENTIAL_REJECTED")
