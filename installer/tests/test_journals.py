"""Adversarial durable Statement-dispatch journal tests."""

from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any, cast

import pytest

from dbtobsb_installer import journals
from dbtobsb_installer.journals import DurableDispatchJournal
from dbtobsb_installer.workflow import DispatchClaimOutcome

_OPERATION = uuid.UUID("12345678-1234-4234-8234-123456789abc")
_DIGEST = "a" * 64


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "private"
    root.mkdir(mode=0o700, parents=True)
    return root


def test_marker_and_mutation_claims_are_durable_idempotent_and_separate(tmp_path: Path) -> None:
    root = _root(tmp_path)
    journal = DurableDispatchJournal._for_test(root)

    assert journal.claim_marker_once(_OPERATION, _DIGEST) is DispatchClaimOutcome.CLAIMED
    assert journal.claim_marker_once(_OPERATION, _DIGEST) is DispatchClaimOutcome.ALREADY_CLAIMED
    assert journal.claim_once(_OPERATION, _DIGEST) is DispatchClaimOutcome.CLAIMED

    restarted = DurableDispatchJournal._for_test(root)
    assert restarted.claim_once(_OPERATION, _DIGEST) is DispatchClaimOutcome.ALREADY_CLAIMED
    assert restarted.claim_once(_OPERATION, "b" * 64) is DispatchClaimOutcome.INDETERMINATE

    state_path = root / "statement-dispatch-claims-v1.json"
    state = json.loads(state_path.read_bytes())
    assert state == {
        "markers": {str(_OPERATION): _DIGEST},
        "mutations": {str(_OPERATION): _DIGEST},
        "protocol": "dbtobsb.dispatch-journal.v1",
    }
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE((root / "statement-dispatch-claims-v1.lock").stat().st_mode) == 0o600
    assert str(root) not in repr(journal)
    assert str(_OPERATION) not in repr(journal)


@pytest.mark.parametrize(
    ("operation_id", "digest"),
    [
        ("not-a-uuid", _DIGEST),
        (uuid.UUID("12345678-1234-1234-8234-123456789abc"), _DIGEST),
        (_OPERATION, "A" * 64),
        (_OPERATION, "short"),
        (_OPERATION, None),
    ],
)
def test_malformed_claims_never_touch_state(
    tmp_path: Path,
    operation_id: object,
    digest: object,
) -> None:
    root = _root(tmp_path)
    journal = DurableDispatchJournal._for_test(root)

    assert (
        journal.claim_once(cast(Any, operation_id), cast(Any, digest))
        is DispatchClaimOutcome.INDETERMINATE
    )
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("bad_state", [b"{}", b'{"protocol":"x"}', b'{"protocol":1}'])
def test_malformed_existing_state_is_never_replaced(tmp_path: Path, bad_state: bytes) -> None:
    root = _root(tmp_path)
    state_path = root / "statement-dispatch-claims-v1.json"
    state_path.write_bytes(bad_state)
    state_path.chmod(0o600)
    journal = DurableDispatchJournal._for_test(root)

    assert journal.claim_once(_OPERATION, _DIGEST) is DispatchClaimOutcome.INDETERMINATE
    assert state_path.read_bytes() == bad_state


def test_duplicate_json_keys_are_indeterminate_and_preserved(tmp_path: Path) -> None:
    root = _root(tmp_path)
    state_path = root / "statement-dispatch-claims-v1.json"
    raw = b'{"markers":{},"markers":{},"mutations":{},"protocol":"dbtobsb.dispatch-journal.v1"}'
    state_path.write_bytes(raw)
    state_path.chmod(0o600)

    result = DurableDispatchJournal._for_test(root).claim_once(_OPERATION, _DIGEST)

    assert result is DispatchClaimOutcome.INDETERMINATE
    assert state_path.read_bytes() == raw


def test_symlinked_or_overpermissive_state_fails_without_touching_target(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("customer")
    state_path = root / "statement-dispatch-claims-v1.json"
    state_path.symlink_to(outside)

    result = DurableDispatchJournal._for_test(root).claim_once(_OPERATION, _DIGEST)

    assert result is DispatchClaimOutcome.INDETERMINATE
    assert outside.read_text() == "customer"

    state_path.unlink()
    state_path.write_text("{}")
    state_path.chmod(0o644)
    assert (
        DurableDispatchJournal._for_test(root).claim_once(_OPERATION, _DIGEST)
        is DispatchClaimOutcome.INDETERMINATE
    )
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o644


def test_atomic_write_failure_does_not_return_claimed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)

    def fail(_path: Path, _value: dict[str, object]) -> None:
        raise OSError

    monkeypatch.setattr(journals, "_atomic_write", fail)

    result = DurableDispatchJournal._for_test(root).claim_once(_OPERATION, _DIGEST)

    assert result is DispatchClaimOutcome.INDETERMINATE
    assert not (root / "statement-dispatch-claims-v1.json").exists()


def test_insecure_root_and_symlinked_root_are_rejected(tmp_path: Path) -> None:
    insecure = tmp_path / "insecure"
    insecure.mkdir(mode=0o755)
    assert (
        DurableDispatchJournal._for_test(insecure).claim_once(_OPERATION, _DIGEST)
        is DispatchClaimOutcome.INDETERMINATE
    )

    real = _root(tmp_path / "real-parent")
    link = tmp_path / "linked"
    link.symlink_to(real, target_is_directory=True)
    assert (
        DurableDispatchJournal._for_test(link).claim_once(_OPERATION, _DIGEST)
        is DispatchClaimOutcome.INDETERMINATE
    )

    product_parent = tmp_path / "product-parent"
    product_parent.mkdir(mode=0o700)
    product_private = product_parent / "private"
    product_private.mkdir(mode=0o700)
    linked_product_parent = tmp_path / "dbtobsb"
    linked_product_parent.symlink_to(product_parent, target_is_directory=True)
    assert (
        DurableDispatchJournal._for_test(linked_product_parent / "private").claim_once(
            _OPERATION, _DIGEST
        )
        is DispatchClaimOutcome.INDETERMINATE
    )


def test_state_is_canonical_and_fsynced_before_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _root(tmp_path)
    fsync_calls: list[int] = []
    real_fsync = os.fsync

    def record(descriptor: int) -> None:
        fsync_calls.append(descriptor)
        real_fsync(descriptor)

    monkeypatch.setattr(journals.os, "fsync", record)

    result = DurableDispatchJournal._for_test(root).claim_once(_OPERATION, _DIGEST)
    raw = (root / "statement-dispatch-claims-v1.json").read_bytes()

    assert result is DispatchClaimOutcome.CLAIMED
    assert raw.endswith(b"\n")
    assert (
        raw == json.dumps(json.loads(raw), separators=(",", ":"), sort_keys=True).encode() + b"\n"
    )
    assert len(fsync_calls) == 2
