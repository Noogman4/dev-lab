"""Real protected receipt IO and synthetic links; never operate on host tunnels."""

import json
import os
from types import SimpleNamespace

import pytest

from netmon.core import nm_ownership as own
from netmon.features import vpn_controller as vpn


class FakeWG:
    def __init__(self):
        self.links = {}
        self.calls = []
        self.fail_down = False
        self.leave_link = False

    def identity(self, name):
        return self.links.get(name)

    def up(self, source):
        name = source.stem
        assert name not in self.links
        assert source.stat().st_mode & 0o777 == 0o600
        self.calls.append(("up", name, source.read_bytes()))
        self.links[name] = {
            "ifindex": 42,
            "public_key": "synthetic",
            "boot_id": "boot1",
            "netns": 1,
        }

    def down(self, source):
        name = source.stem
        self.calls.append(("down", name, source.read_bytes()))
        if self.fail_down:
            raise own.OwnershipError("Synthetic teardown failure")
        if not self.leave_link:
            del self.links[name]


@pytest.fixture
def store(tmp_path, monkeypatch):
    # Guard subprocesses even if a future refactor accidentally bypasses FakeWG.
    monkeypatch.setattr(
        own.subprocess, "run", lambda *a, **kw: pytest.fail("host command")
    )
    profiles = tmp_path / "profiles"
    profiles.mkdir(mode=0o700)
    monkeypatch.setattr(own, "PROFILE_DIRECTORY", str(profiles))
    for name in ("work", "next", "work__ipv4"):
        path = profiles / (name + ".conf")
        path.write_text("[Interface]\nPrivateKey = synthetic\n")
        path.chmod(0o600)
    return own.WireGuardStore(
        tmp_path / "receipts", owner=os.getuid(), anchor=tmp_path, wg=FakeWG()
    )


def test_cleanup_retains_external_and_uses_original_teardown_snapshot(store):
    store.wg.links["corporate"] = {"ifindex": 7}
    identity = store.up("work")
    assert identity["ifindex"] == 42
    profile = store.anchor / "profiles/work.conf"
    profile.write_text("[Interface]\nPostDown = UNREVIEWED\n")
    # A fresh store models application restart; user-side memory is unnecessary.
    fresh = own.WireGuardStore(
        store.registry, owner=store.owner, anchor=store.anchor, wg=store.wg
    )
    fresh.cleanup()
    assert store.wg.links == {"corporate": {"ifindex": 7}}
    assert [(action, name) for action, name, _ in store.wg.calls] == [
        ("up", "work"),
        ("down", "work"),
    ]
    assert store.wg.calls[0][2] == store.wg.calls[1][2]
    assert sorted(p.name for p in store.registry.iterdir()) == [".lock"]


@pytest.mark.parametrize(
    "field,value",
    [("ifindex", 43), ("public_key", "other"), ("boot_id", "boot2"), ("netns", 2)],
)
def test_replaced_link_never_reaches_down(store, field, value):
    store.up("work")
    store.wg.links["work"] = dict(store.wg.links["work"], **{field: value})
    with pytest.raises(own.OwnershipError):
        store.cleanup()
    assert len(store.wg.calls) == 1
    assert "work" in store.wg.links


def test_same_name_foreign_link_never_adopted(store):
    store.wg.links["work"] = {"ifindex": 8}
    with pytest.raises(own.OwnershipError):
        store.up("work")
    assert store.wg.calls == []
    assert not (store.registry / "work.json").exists()


def test_missing_link_expires_receipt_without_teardown(store):
    store.up("work")
    del store.wg.links["work"]
    store.cleanup()
    assert len(store.wg.calls) == 1
    assert not (store.registry / "work.json").exists()


@pytest.mark.parametrize("failure", ["command", "lingering"])
def test_failed_down_retains_evidence_and_never_forces_delete(store, failure):
    store.up("work")
    store.wg.fail_down = failure == "command"
    store.wg.leave_link = failure == "lingering"
    with pytest.raises(own.OwnershipError):
        store.cleanup()
    assert "work" in store.wg.links
    assert (store.registry / "work.json").exists()
    store.wg.fail_down = store.wg.leave_link = False
    store.cleanup()
    assert "work" not in store.wg.links


@pytest.mark.parametrize(
    "damage", ["missing", "modified", "symlink", "writable", "receipt"]
)
def test_untrusted_receipts_and_configs_fail_closed(store, damage):
    store.up("work")
    path = store.registry / "work.conf"
    if damage == "missing":
        path.unlink()
    elif damage == "modified":
        path.write_text("changed")
    elif damage == "symlink":
        path.unlink()
        path.symlink_to(store.anchor / "profiles/work.conf")
    elif damage == "writable":
        path.chmod(0o666)
    else:
        (store.registry / "work.json").write_text("{}")
    with pytest.raises((OSError, own.OwnershipError)):
        store.cleanup()
    assert len(store.wg.calls) == 1


def test_cleanup_without_registry_is_noop_and_cannot_claim_saved_profiles(store):
    store.wg.links["work"] = {"ifindex": 8}
    store.cleanup()
    assert store.wg.calls == []


@pytest.mark.parametrize("name", ["../work", "-x/..", "a" * 16, ".", "..", "work\n"])
def test_invalid_name_never_reaches_privileged_commands(store, name):
    with pytest.raises(own.OwnershipError):
        store.up(name)
    assert store.wg.calls == []


def test_controller_cleanup_uses_only_protected_helper(monkeypatch):
    calls = []
    app = SimpleNamespace(log_safe=lambda text: None, _wg_activation_links={"work": 42})
    monkeypatch.setattr(
        vpn, "_owned_nm_command", lambda operation: calls.append(operation)
    )
    assert vpn.cleanup_wireguard_interfaces(app)
    assert calls == ["wg-cleanup"]
    assert "_wg_activation_links" not in app.__dict__


def test_controller_failure_preserves_session_evidence(monkeypatch):
    app = SimpleNamespace(log_safe=lambda text: None, _wg_activation_links={"work": 42})

    def fail(operation):
        raise own.OwnershipError("unavailable")

    monkeypatch.setattr(vpn, "_owned_nm_command", fail)
    assert not vpn.cleanup_wireguard_interfaces(app)
    assert app._wg_activation_links == {"work": 42}


def test_wireguard_identity_rejects_non_wg_and_malformed_inventory(monkeypatch):
    wg = own.WireGuard()
    for rows in (
        {},
        [{"ifname": "work", "ifindex": True}],
        [{"ifname": "work", "ifindex": 7, "linkinfo": {"info_kind": "ether"}}],
    ):
        monkeypatch.setattr(wg, "command", lambda args, rows=rows: json.dumps(rows))
        with pytest.raises(own.OwnershipError):
            wg.identity("work")


@pytest.mark.parametrize("force", [False, True])
def test_real_switch_and_off_preserve_external_tunnel(store, monkeypatch, force):
    store.up("work")
    store.wg.links["corporate"] = {"ifindex": 7}
    external = dict(store.wg.links["corporate"])
    operations = []

    def helper(operation, *, identity=None):
        operations.append(operation)
        if operation == "wg-up":
            return store.up(identity[0])
        assert operation == "wg-cleanup"
        store.cleanup()

    monkeypatch.setattr(vpn, "_owned_nm_command", helper)
    monkeypatch.setattr(
        vpn,
        "_network_links",
        lambda: {
            name: (link["ifindex"], "wireguard")
            for name, link in store.wg.links.items()
        },
    )
    monkeypatch.setattr(
        vpn, "run_cmd", lambda *a, **kw: pytest.fail("unprotected controller command")
    )
    app = SimpleNamespace(
        _wg_activation_links={"work": 42},
        _try_begin_network_operation=lambda label: True,
        _end_network_operation=lambda: None,
        resolve_profile_family_runtime=lambda name, **kw: {"runtime_profile": name},
        get_wg_interfaces=lambda: list(store.wg.links),
        _network_service=lambda: SimpleNamespace(file_exists=lambda path: (0, "")),
        _wg_profile_path=lambda name: str(store.anchor / "profiles" / (name + ".conf")),
        killswitch_is_on=lambda: False,
        tr=lambda key, fallback: fallback,
    )
    for name in (
        "log_safe",
        "log_debug",
        "log_debug_safe",
        "log_network_debug",
        "_check_wireguard_profile_for_multiple_endpoints",
        "prepare_dns_for_vpn_profile_switch",
        "refresh_wg_profiles",
        "update_primary_vpn_form_controls",
        "sync_primary_vpn_form_selection",
        "update_ipv6_controls_state_safe",
        "refresh_safe",
        "_schedule_dns_finalize_after_vpn_profile_switch",
        "run_async",
        "reconcile_vpn_slot_firewall_state",
    ):
        setattr(app, name, lambda *a, **kw: None)
    assert vpn.vpn_switch(app, "next", ensure_sudo=False, force_reconnect=force)
    assert set(store.wg.links) == {"next", "corporate"}
    assert store.wg.links["corporate"] == external
    assert vpn.vpn_off(app, ensure_sudo=False)
    assert store.wg.links == {"corporate": external}
    assert operations == ["wg-cleanup", "wg-up", "wg-cleanup"]
    assert [(action, name) for action, name, _ in store.wg.calls] == [
        ("up", "work"),
        ("down", "work"),
        ("up", "next"),
        ("down", "next"),
    ]


def test_link_replaced_immediately_before_down_is_retained(store, monkeypatch):
    store.up("work")
    original = store.wg.links["work"]
    observations = iter([original, dict(original, ifindex=99)])
    monkeypatch.setattr(store.wg, "identity", lambda name: next(observations))
    with pytest.raises(own.OwnershipError):
        store.cleanup()
    assert len(store.wg.calls) == 1
