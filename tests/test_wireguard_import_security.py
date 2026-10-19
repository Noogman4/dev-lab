"""L-04: synthetic profiles, fake privileged RPC/NM, no real hooks or sudo."""

import hashlib
import io
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from netmon.core import nm_ownership as own
from netmon.core import wireguard_import as wg
from netmon.features import vpn_controller as vpn
from test_netmon_nm_ownership import store as store

SAFE = b"[Interface]\nAddress=10.0.0.2/32\n"
HOOK = SAFE + b"PostUp = L04_SYNTHETIC_NEVER_EXECUTE\n"


def profile(tmp_path, name="work", data=SAFE):
    path = tmp_path / (name + ".conf")
    path.write_bytes(data)
    path.chmod(0o600)
    return path


@pytest.fixture
def app(tmp_path, monkeypatch, store):
    monkeypatch.setattr(own.socket, "if_nameindex", list)
    directory = tmp_path / "wireguard"
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(own, "PROFILE_DIRECTORY", str(directory))
    logs, dialogs, warnings, operations, imported = [], [], [], [], []
    result = SimpleNamespace(
        privacy_config={},
        tr=lambda key, fallback: fallback,
        log=logs.append,
        log_safe=logs.append,
        after=lambda delay, fn: fn(),
        ensure_sudo_session=lambda reason: True,
        get_wg_import_dir=lambda: str(tmp_path),
        set_wg_import_dir=lambda value: None,
        _wg_profile_path=lambda name: str(directory / (name + ".conf")),
        wg_profiles=[],
        logs=logs,
        dialogs=dialogs,
        warnings=warnings,
        operations=operations,
        imported=imported,
        directory=directory,
    )
    for method in (
        "reconcile_vpn_slot_firewall_state",
        "sync_internal_ipv4_profiles",
        "refresh_wg_profiles",
        "update_primary_vpn_form_controls",
        "sync_primary_vpn_form_selection",
        "sync_vpn_profile_form_selection",
        "update_vpn_slot_buttons",
        "refresh_vpn_slots_table",
    ):
        setattr(result, method, lambda *a, **k: None)
    original_create = store.nm.create

    def create(source):
        imported.append(
            (
                source.read_bytes(),
                source.stat().st_mode & 0o777,
                source.parent.stat().st_mode & 0o777,
            )
        )
        return original_create(source)

    monkeypatch.setattr(store.nm, "create", create)

    def helper(operation, *, payload=None, identity=None):
        operations.append(operation)
        if operation == "import":
            name, content = own.checked_import_payload(payload)
            return store.create(name, content)
        if operation == "install-profile":
            return store.install_profile(payload)
        if operation == "snapshot-profile":
            return store.snapshot_profile(payload["name"])
        if operation == "inspect":
            return store.inspect(*identity)
        if operation == "delete":
            return store.delete(payload)
        pytest.fail("Unexpected operation")

    monkeypatch.setattr(vpn, "_owned_nm_command", helper)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(vpn, "has_cmd", lambda name: True)
    monkeypatch.setattr(
        vpn, "get_nm_wireguard_profiles", lambda app: list(store.nm.rows.values())
    )
    monkeypatch.setattr(
        vpn, "run_cmd", lambda *a, **k: pytest.fail("Real sudo/nmcli forbidden")
    )
    monkeypatch.setattr(
        vpn,
        "run_cmd_with_input",
        lambda *a, **k: pytest.fail("Real privileged RPC forbidden"),
    )
    monkeypatch.setattr(vpn, "call_in_ui_thread", lambda app, fn: fn())
    monkeypatch.setattr(
        vpn.messagebox,
        "askyesno",
        lambda title, text, **kw: (dialogs.append(text) or True),
    )
    monkeypatch.setattr(
        vpn.messagebox, "showwarning", lambda title, text, **kw: warnings.append(text)
    )

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(vpn.threading, "Thread", Immediate)
    return result


def enter(app, source, route, monkeypatch):
    monkeypatch.setattr(vpn.filedialog, "askopenfilenames", lambda **kw: (str(source),))
    if route == "folder":
        vpn.import_wg_profiles_from_folder(app)
    elif route == "dialog":
        vpn.import_wg_profiles_to_networkmanager(app)
    elif route == "referenced":
        app.collect_referenced_wg_profile_import_paths = lambda: [("work", str(source))]
        vpn.import_referenced_wg_profiles_to_networkmanager(app)
    else:
        vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])


@pytest.mark.parametrize("route", ["folder", "dialog", "referenced", "direct"])
@pytest.mark.parametrize("attack", ["replace", "inplace", "symlink"])
def test_change_after_hook_inspection_never_imported(
    app, tmp_path, monkeypatch, route, attack
):
    source = profile(tmp_path)

    def approve(title, text, **kwargs):
        assert hashlib.sha256(SAFE).hexdigest() in text
        if attack == "inplace":
            source.write_bytes(HOOK)
        else:
            replacement = profile(tmp_path, "replacement", HOOK)
            if attack == "replace":
                os.replace(replacement, source)
            else:
                source.unlink()
                source.symlink_to(replacement)
        return True

    monkeypatch.setattr(vpn.messagebox, "askyesno", approve)
    enter(app, source, route, monkeypatch)
    assert not app.imported
    assert not list(app.directory.iterdir())
    assert "import" not in app.operations and "install-profile" not in app.operations


@pytest.mark.parametrize("route", ["folder", "dialog", "referenced", "direct"])
def test_warning_confirmation_and_import_refer_to_exact_same_bytes(
    app, tmp_path, monkeypatch, route
):
    source = profile(tmp_path, data=HOOK)
    enter(app, source, route, monkeypatch)
    assert len(app.dialogs) == 1 and "PostUp" in app.dialogs[0]
    assert hashlib.sha256(HOOK).hexdigest() in app.dialogs[0]
    assert len(app.warnings) == 1 and "PostUp" in app.warnings[0]
    assert "L04_SYNTHETIC_NEVER_EXECUTE" not in " ".join(
        app.logs + app.warnings + app.dialogs
    )
    if route == "folder":
        assert (app.directory / "work.conf").read_bytes() == HOOK
    else:
        assert app.imported == [(HOOK, 0o600, 0o700)]
    assert not list(app.directory.glob(".import-*"))


@pytest.mark.parametrize("route", ["folder", "direct"])
def test_late_same_uid_process_source_mutation_cannot_change_rpc_bytes(
    app, tmp_path, monkeypatch, route
):
    source = profile(tmp_path)
    original = vpn._owned_nm_command

    def mutate(operation, **kwargs):
        if operation in {"import", "install-profile"}:
            # A distinct process with the same desktop UID changes the old source
            # after client verification, immediately before the privileged RPC.
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(bytes.fromhex(sys.argv[2]))",
                    str(source),
                    HOOK.hex(),
                ],
                check=True,
            )
        return original(operation, **kwargs)

    monkeypatch.setattr(vpn, "_owned_nm_command", mutate)
    enter(app, source, route, monkeypatch)
    assert source.read_bytes() == HOOK
    if route == "folder":
        assert (app.directory / "work.conf").read_bytes() == SAFE
    else:
        assert app.imported[0][0] == SAFE


@pytest.mark.parametrize("route", ["folder", "direct"])
@pytest.mark.parametrize(
    "field,value",
    [("content", HOOK.decode()), ("sha256", "0" * 64), ("hooks", ["PostDown"])],
)
def test_modified_handoff_proof_is_rejected_by_privileged_receiver(
    app, tmp_path, monkeypatch, route, field, value
):
    source = profile(tmp_path)
    original = vpn._owned_nm_command

    def corrupt(operation, **kwargs):
        if operation in {"import", "install-profile"}:
            kwargs["payload"][field] = value
        return original(operation, **kwargs)

    monkeypatch.setattr(vpn, "_owned_nm_command", corrupt)
    enter(app, source, route, monkeypatch)
    assert not app.imported and not list(app.directory.iterdir())


@pytest.mark.parametrize(
    "kind",
    [
        "symlink",
        "parent-symlink",
        "fifo",
        "directory",
        "hardlink",
        "world-write",
        "group-write",
        "empty",
        "oversize",
        "nul",
        "utf8",
    ],
)
def test_unsafe_sources_rejected_without_blocking(tmp_path, kind):
    source = profile(tmp_path)
    if kind == "symlink":
        other = profile(tmp_path, "other")
        source.unlink()
        source.symlink_to(other)
    elif kind == "parent-symlink":
        other = tmp_path / "alias"
        other.symlink_to(tmp_path, target_is_directory=True)
        source = other / source.name
    elif kind == "fifo":
        source.unlink()
        os.mkfifo(source)
    elif kind == "directory":
        source.unlink()
        source.mkdir()
    elif kind == "hardlink":
        os.link(source, tmp_path / "duplicate")
    elif kind in {"world-write", "group-write"}:
        source.chmod(0o606 if kind == "world-write" else 0o660)
    else:
        source.write_bytes(
            {
                "empty": b"",
                "oversize": b"x" * (own.MAX_CONFIG + 1),
                "nul": SAFE + b"\0",
                "utf8": SAFE + b"\xff",
            }[kind]
        )
    with pytest.raises((OSError, ValueError)):
        wg.ProfileSnapshot.read(source)


@pytest.mark.parametrize("mutation", ["content", "replace", "unlink"])
def test_stability_checked_during_descriptor_read(tmp_path, monkeypatch, mutation):
    source = profile(tmp_path)
    original = wg.os.fstat
    calls = 0

    def changed(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            if mutation == "content":
                source.write_bytes(HOOK)
            elif mutation == "replace":
                os.replace(profile(tmp_path, "other", HOOK), source)
            else:
                source.unlink()
        return original(fd)

    monkeypatch.setattr(wg.os, "fstat", changed)
    with pytest.raises((OSError, ValueError)):
        wg.ProfileSnapshot.read(source)


def test_batch_independent_proofs_and_no_secret_persistence(app, store, tmp_path):
    sources = [profile(tmp_path, "one"), profile(tmp_path, "two", HOOK)]
    vpn.import_wireguard_paths_to_networkmanager(app, list(map(str, sources)))
    assert [item[0] for item in app.imported] == [SAFE, HOOK]
    assert len(app.dialogs) == 1
    assert all(
        hashlib.sha256(data).hexdigest() in app.dialogs[0] for data in (SAFE, HOOK)
    )
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 2
    assert "L04_SYNTHETIC_NEVER_EXECUTE" not in json.dumps(app.privacy_config)
    assert len(store.candidates()) == 2


@pytest.mark.parametrize("failure", ["cancel", "closed"])
def test_missing_confirmation_never_imports(app, tmp_path, monkeypatch, failure):
    def confirm(*args, **kwargs):
        if failure == "closed":
            raise RuntimeError("GUI closed")
        return False

    monkeypatch.setattr(vpn.messagebox, "askyesno", confirm)
    source = profile(tmp_path)
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert not app.imported and "import" not in app.operations


@pytest.mark.parametrize("limit", ["count", "total"])
def test_batch_limits_before_any_privileged_import(app, tmp_path, monkeypatch, limit):
    sources = [profile(tmp_path, "one"), profile(tmp_path, "two")]
    monkeypatch.setattr(
        wg, "MAX_PROFILES" if limit == "count" else "MAX_BATCH_BYTES", 1
    )
    vpn.import_wireguard_paths_to_networkmanager(app, list(map(str, sources)))
    assert not app.imported and not app.dialogs


def test_root_snapshot_for_unreadable_protected_profile(app, tmp_path, monkeypatch):
    source = app.directory / "work.conf"
    source.write_bytes(HOOK)
    source.chmod(0o600)

    def forbidden(*args):
        pytest.fail(
            "Protected profile must use bounded root snapshot, not local path reading"
        )

    monkeypatch.setattr(wg, "_read", forbidden)
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert app.operations == ["snapshot-profile", "snapshot-profile", "import"]
    assert app.imported[0][0] == HOOK


def test_protected_profile_changes_after_review_are_rejected(app, monkeypatch):
    source = app.directory / "work.conf"
    source.write_bytes(SAFE)
    source.chmod(0o600)

    def approve(*args, **kwargs):
        source.write_bytes(HOOK)
        return True

    monkeypatch.setattr(vpn.messagebox, "askyesno", approve)
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert not app.imported
    assert app.operations == ["snapshot-profile", "snapshot-profile"]


@pytest.mark.parametrize("route", ["folder", "direct"])
def test_missing_protected_helper_fails_closed(app, tmp_path, monkeypatch, route):
    # Restore the real adapter: its availability check must reject before sudo.
    monkeypatch.setattr(own, "trusted_helper_available", lambda: False)
    original = vpn._owned_nm_command

    def unavailable(operation, **kwargs):
        if operation in {"import", "install-profile"}:
            raise own.OwnershipError("Protected helper missing")
        return original(operation, **kwargs)

    monkeypatch.setattr(vpn, "_owned_nm_command", unavailable)
    enter(app, profile(tmp_path), route, monkeypatch)
    assert not app.imported and not list(app.directory.iterdir())


@pytest.mark.parametrize("kind", ["symlink", "fifo", "hardlink", "permissions"])
def test_privileged_destination_controls_preserved(app, tmp_path, kind):
    target = app.directory / "work.conf"
    keep = profile(tmp_path, "keep")
    if kind == "symlink":
        target.symlink_to(keep)
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "hardlink":
        os.link(keep, target)
    else:
        target.write_bytes(SAFE)
        target.chmod(0o666)
    with pytest.raises((OSError, own.OwnershipError)):
        from_payload = wg.ProfileSnapshot.from_bytes(
            "synthetic", "work", HOOK
        ).payload()
        # Actual root-side storage, with isolated owner/anchor supplied by fixture.
        # The production CLI never accepts these overrides.
        own.checked_import_payload(from_payload)
        # Use fixture-bound operation to exercise actual install_profile().
        vpn._owned_nm_command("install-profile", payload=from_payload)
    assert keep.read_bytes() == SAFE
    assert not list(app.directory.glob(".import-*"))


@pytest.mark.parametrize(
    "phase", ["stage-write", "stage-verify", "rename", "nm-create"]
)
def test_staging_and_import_failures_cleanup_and_keep_existing(
    app, store, tmp_path, monkeypatch, phase
):
    target = app.directory / "work.conf"
    target.write_bytes(SAFE)
    target.chmod(0o600)
    payload = wg.ProfileSnapshot.from_bytes("synthetic", "work", HOOK).payload()
    if phase == "stage-write":
        monkeypatch.setattr(
            own.os,
            "fsync",
            lambda fd: (_ for _ in ()).throw(OSError("write/flush failure")),
        )
    elif phase == "stage-verify":
        original_read = own._read

        def corrupt(directory, name, owner, limit):
            if name == "work.conf":
                data, info = original_read(directory, name, owner, limit)
                if data == HOOK:
                    return SAFE, info
                return data, info
            return original_read(directory, name, owner, limit)

        monkeypatch.setattr(own, "_read", corrupt)
    elif phase == "rename":
        monkeypatch.setattr(
            own.os,
            "replace",
            lambda *a, **k: (_ for _ in ()).throw(OSError("rename failure")),
        )
    else:
        store.nm.fail = "create"
    with pytest.raises((OSError, own.OwnershipError)):
        if phase == "nm-create":
            store.create("work", HOOK.decode())
        else:
            store.install_profile(payload)
    assert target.read_bytes() == SAFE
    assert not list(app.directory.glob(".import-*"))
    assert not list(store.registry.glob(".import-*"))
    assert not store.nm.deleted


def test_generated_profiles_also_use_privileged_byte_handoff(app):
    content = vpn.build_manual_wireguard_config_text(
        None,
        {
            "private_key": "A" * 43 + "=",
            "public_key": "A" * 43 + "=",
            "address": "10.0.0.2/32",
            "allowed_ips": "0.0.0.0/0",
            "endpoint": "198.51.100.1:51820",
        },
    )
    assert vpn.write_manual_wg_profile(app, "manual", content) == (True, "")
    assert (app.directory / "manual.conf").read_bytes() == content.encode()
    assert app.operations == ["install-profile"]


@pytest.mark.parametrize("operation", ["import", "install-profile"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "work", "content": SAFE.decode()},
        {"name": "../work", "content": SAFE.decode(), "sha256": "0" * 64, "hooks": []},
    ],
)
def test_cli_rejects_missing_or_invalid_proof_without_creating_state(
    store, monkeypatch, capsys, operation, payload
):
    # Fake privilege gate only: no root operations or real NM executable.
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(own, "OwnershipStore", lambda: store)
    monkeypatch.setattr(
        own.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode())),
    )
    assert own.main([operation]) == 1
    assert "L04_SYNTHETIC" not in capsys.readouterr().err
    assert not store.registry.exists() and not store.nm.rows


@pytest.mark.parametrize("operation", ["import", "import-checked", "install-profile"])
def test_authorized_helper_checks_bytes_but_cannot_attest_human_consent(
    app, store, monkeypatch, capsys, operation
):
    # Explicit remaining boundary: a caller already authorized to invoke sudo can
    # generate a self-consistent digest/hooks record without using NetMon's UI.
    # This is NOT a file-race bypass, and the test does not run real sudo/root.
    payload = wg.ProfileSnapshot.from_bytes(
        "synthetic-other-process", "unconfirmed", HOOK
    ).payload()
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "OwnershipStore", lambda: store)
    monkeypatch.setattr(
        own.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode())),
    )
    assert own.main([operation]) == 0
    capsys.readouterr()
    assert not app.dialogs
    if operation == "install-profile":
        assert (app.directory / "unconfirmed.conf").read_bytes() == HOOK
    else:
        assert app.imported[0][0] == HOOK
        assert len(store.candidates()) == 1


@pytest.mark.parametrize("attack", ["payload", "hooks"])
def test_snapshot_object_inconsistency_is_caught(tmp_path, attack):
    original = wg.ProfileSnapshot.read(profile(tmp_path))
    # Fault injection of an internal programming/memory inconsistency, NOT a
    # claim that this protects a process controlled by an arbitrary-code attacker.
    object.__setattr__(
        original,
        "data" if attack == "payload" else "hooks",
        HOOK if attack == "payload" else ("PostDown",),
    )
    with pytest.raises(ValueError):
        original.payload()


def test_root_snapshot_rpc_does_not_relay_arbitrary_paths(
    app, store, monkeypatch, capsys
):
    payload = {"name": "../unrelated"}
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "OwnershipStore", lambda: store)
    monkeypatch.setattr(
        own.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode())),
    )
    assert own.main(["snapshot-profile"]) == 1
    assert str(app.directory) not in capsys.readouterr().err
    assert not app.imported


@pytest.mark.parametrize("route", ["folder", "dialog"])
def test_queued_jobs_keep_separate_reviewed_snapshots(
    app, tmp_path, monkeypatch, route
):
    queued = []

    class Queued:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            queued.append(self.target)

    monkeypatch.setattr(vpn.threading, "Thread", Queued)
    first = profile(tmp_path, "first")
    second = profile(tmp_path, "second", HOOK)
    enter(app, first, route, monkeypatch)
    enter(app, second, route, monkeypatch)
    queued[1]()
    queued[0]()
    if route == "folder":
        assert (app.directory / "first.conf").read_bytes() == SAFE
        assert (app.directory / "second.conf").read_bytes() == HOOK
    else:
        assert [record[0] for record in app.imported] == [HOOK, SAFE]
        assert set(vpn.get_nm_last_import_state(app)["connections"]) == {
            "first",
            "second",
        }


def test_partial_root_stage_writes_are_completed(app, store, monkeypatch):
    original = own.Path.open

    class Output:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.handle.close()

        def fileno(self):
            return self.handle.fileno()

        def write(self, data):
            return self.handle.write(data[:1])

        def flush(self):
            self.handle.flush()

    def partial(path, *args, **kwargs):
        handle = original(path, *args, **kwargs)
        return Output(handle) if args and args[0] == "xb" else handle

    monkeypatch.setattr(own.Path, "open", partial)
    payload = wg.ProfileSnapshot.from_bytes("synthetic", "work", SAFE).payload()
    store.install_profile(payload)
    assert (app.directory / "work.conf").read_bytes() == SAFE


def test_snapshot_copies_mutable_input_bytes():
    data = bytearray(SAFE)
    snapshot = wg.ProfileSnapshot.from_bytes("synthetic", "work", data)
    data.extend(HOOK)
    assert snapshot.data == SAFE
    assert snapshot.payload()["sha256"] == hashlib.sha256(SAFE).hexdigest()


def test_root_owned_readable_parent_preserves_private_staging(app, store):
    # Parent need not be 0700: root ownership/no unprivileged write plus 0700
    # staging and 0600 profiles preserve the boundary on existing installations.
    app.directory.chmod(0o755)
    payload = wg.ProfileSnapshot.from_bytes("synthetic", "work", SAFE).payload()
    store.install_profile(payload)
    assert (app.directory / "work.conf").stat().st_mode & 0o777 == 0o600
    assert store.snapshot_profile("work") == payload
    assert app.directory.stat().st_mode & 0o777 == 0o755
