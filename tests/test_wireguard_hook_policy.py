"""Reject command-bearing WireGuard profiles; fake NM/WG, no host VPN actions."""

import hashlib
import json

import pytest

from netmon.core import nm_ownership as own
from netmon.core import wireguard_import as wg
from netmon.features import vpn_controller as vpn
from tests.test_wireguard_import_security import (
    SAFE,
    app as app,
    store as store,
    profile,
    enter,
)
from tests import test_wg_quick_ownership

wg_store = pytest.fixture(test_wg_quick_ownership.store.__wrapped__)

HOOKS = ("PreUp", "PostUp", "PreDown", "PostDown")
COMMAND = "HOOK_POLICY_NEVER_EXECUTE secret=DO_NOT_DISPLAY"


def with_hook(directive, variant="plain"):
    line = f"{directive} = {COMMAND}"
    if variant == "indent":
        line = "\t  " + line + " # comment"
    elif variant == "mixed":
        line = "  " + directive.swapcase() + "=" + COMMAND
    elif variant == "empty":
        line = directive + " ="
    elif variant == "peer":
        line = "[Peer]\n" + line
    newline = "\r\n" if variant == "crlf" else "\n"
    return SAFE + (line + newline).encode()


@pytest.mark.parametrize("directive", HOOKS)
@pytest.mark.parametrize(
    "variant", ["plain", "indent", "mixed", "empty", "peer", "crlf"]
)
@pytest.mark.parametrize("route", ["folder", "dialog", "referenced", "direct"])
def test_every_import_route_rejects_hooks_without_copy_or_confirmation(
    app, tmp_path, monkeypatch, directive, variant, route
):
    source = profile(tmp_path, data=with_hook(directive, variant))
    original = source.read_bytes(), source.stat().st_mode
    enter(app, source, route, monkeypatch)
    assert not app.imported and not app.operations and not app.dialogs
    assert not app.managed_directory.exists()
    assert not list(app.directory.iterdir())
    assert (source.read_bytes(), source.stat().st_mode) == original
    assert COMMAND not in " ".join(app.logs + app.warnings)


@pytest.mark.parametrize("directive", HOOKS)
@pytest.mark.parametrize("boundary", ["payload", "create", "install", "snapshot"])
def test_privileged_boundaries_reject_self_consistent_hook_bytes(
    app, store, directive, boundary
):
    data = with_hook(directive)
    payload = wg.ProfileSnapshot.from_bytes("synthetic", "work", data).payload()
    assert payload["sha256"] == hashlib.sha256(data).hexdigest()
    if boundary == "snapshot":
        target = profile(app.directory, data=data)
    with pytest.raises(own.OwnershipError, match="Hooks abgelehnt") as error:
        if boundary == "payload":
            own.checked_import_payload(payload)
        elif boundary == "create":
            store.create("work", data.decode())
        elif boundary == "install":
            store.install_profile(payload)
        else:
            store.snapshot_profile("work")
    assert COMMAND not in str(error.value)
    assert not store.registry.exists() and not app.imported and not store.nm.rows
    if boundary == "snapshot":
        assert target.read_bytes() == data


@pytest.mark.parametrize("directive", HOOKS)
def test_saved_root_profile_cannot_activate_hooks(wg_store, directive):
    target = wg_store.anchor / "profiles" / "work.conf"
    data = with_hook(directive)
    target.write_bytes(data)
    with pytest.raises(own.OwnershipError, match="Hooks abgelehnt"):
        wg_store.up("work")
    assert not wg_store.wg.calls and not wg_store.wg.links
    assert target.read_bytes() == data
    assert not list(wg_store.registry.glob(".import-*"))
    assert not (wg_store.registry / "work.json").exists()


@pytest.mark.parametrize("directive", HOOKS)
def test_matching_legacy_receipt_cannot_execute_teardown_hooks(wg_store, directive):
    wg_store.up("work")
    data = with_hook(directive)
    (wg_store.registry / "work.conf").write_bytes(data)
    receipt_path = wg_store.registry / "work.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["sha256"] = hashlib.sha256(data).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(own.OwnershipError, match="Hooks abgelehnt"):
        wg_store.cleanup()
    assert len(wg_store.wg.calls) == 1  # Only the earlier hook-free activation.
    assert "work" in wg_store.wg.links and receipt_path.exists()
    assert (wg_store.registry / "work.conf").read_bytes() == data


def test_mixed_batch_rejected_before_any_copy_or_import(app, tmp_path):
    paths = [profile(tmp_path, "safe"), profile(tmp_path, "hook", with_hook("PostUp"))]
    vpn.import_wireguard_paths_to_networkmanager(app, list(map(str, paths)))
    assert not app.imported and not app.dialogs and not app.operations
    assert not app.managed_directory.exists()


@pytest.mark.parametrize(
    "comment", ["# PostUp = ignored", "  # PreDown=ignored", "# PostDown=ignored"]
)
def test_comment_only_hook_names_do_not_block_safe_profiles(comment):
    data = SAFE + (comment + "\n").encode()
    payload = wg.ProfileSnapshot.from_bytes("synthetic", "safe", data).payload()
    assert own.checked_import_payload(payload) == ("safe", data.decode())
