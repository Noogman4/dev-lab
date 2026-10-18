"""L-01: synthetic NetworkManager only; no root commands or system profiles."""

from io import StringIO
import json
import os
from types import SimpleNamespace
import uuid

import pytest

from netmon.core import nm_ownership as own
from netmon.features import vpn_controller as vpn


class FakeNM:
    def __init__(self, directory):
        self.directory = directory
        self.rows = {}
        self.deleted = []
        self.create_uuid = None
        self.fail = None

    def uuids(self):
        return set(self.rows)

    def filename(self, identity):
        return (
            str(self.directory / (identity + ".nmconnection"))
            if identity in self.rows
            else None
        )

    def show(self, identity):
        if self.fail == "show":
            raise own.OwnershipError("NM unavailable")
        if identity not in self.rows:
            raise own.OwnershipError("UUID missing")
        return {"uuid": identity, "name": self.rows[identity]}

    def keyfile(self, identity, name):
        path = self.directory / (identity + ".nmconnection")
        path.write_text(
            f"[connection]\nid={name}\nuuid={identity}\ntype=wireguard\n[wireguard]\n"
        )
        path.chmod(0o600)
        return path

    def create(self, source):
        assert source.read_text().startswith("[Interface]")
        assert source.stat().st_mode & 0o777 == 0o600
        if self.fail == "create":
            raise own.OwnershipError("Import failed")
        identity = self.create_uuid or str(uuid.uuid4())
        self.rows[identity] = source.stem
        self.keyfile(identity, source.stem)
        return identity

    def delete(self, identity):
        if self.fail == "delete":
            raise own.OwnershipError("Delete failed")
        self.deleted.append(identity)
        del self.rows[identity]
        (self.directory / (identity + ".nmconnection")).unlink()


@pytest.fixture
def store(tmp_path, monkeypatch):
    # No production subprocess can accidentally be invoked by these tests.
    monkeypatch.setattr(
        own.NetworkManager, "command", lambda *a: pytest.fail("real NM call")
    )
    directory = tmp_path / "connections"
    directory.mkdir(mode=0o700)
    nm = FakeNM(directory)
    return own.OwnershipStore(
        tmp_path / "registry", directory, owner=os.getuid(), anchor=tmp_path, nm=nm
    )


def create(store, name="vpn"):
    return store.create(name, "[Interface]\nAddress=10.0.0.1/32\n")


def receipt_path(store, candidate):
    return store.registry / (candidate["uuid"] + ".json")


def rewrite_receipt(store, candidate, change):
    path = receipt_path(store, candidate)
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def test_owned_creation_receipt_and_exact_uuid_deletion(store):
    candidate = create(store)
    record = json.loads(receipt_path(store, candidate).read_text())
    assert record["owner"] == own.OWNER
    assert record["uuid"] == candidate["uuid"]
    assert len(record["source_sha256"]) == 64
    assert record["created_ns"] > 0
    assert store.registry.stat().st_mode & 0o777 == 0o700
    assert receipt_path(store, candidate).stat().st_mode & 0o777 == 0o600
    assert store.candidates() == [candidate]
    store.delete(candidate)
    assert store.nm.deleted == [candidate["uuid"]]
    assert not receipt_path(store, candidate).exists()


def test_duplicate_display_names_leave_foreign_uuid(store):
    foreign = str(uuid.uuid4())
    store.nm.rows[foreign] = "vpn"
    store.nm.keyfile(foreign, "vpn")
    candidate = create(store)
    store.delete(candidate)
    assert store.nm.rows == {foreign: "vpn"}


def test_existing_uuid_never_registered(store):
    identity = str(uuid.uuid4())
    store.nm.rows[identity] = "foreign"
    store.nm.keyfile(identity, "foreign")
    store.nm.create_uuid = identity
    with pytest.raises(own.OwnershipError, match="Existing UUID"):
        create(store)
    assert store.candidates() == []
    assert store.nm.deleted == []


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "json",
        "marker",
        "uuid",
        "nonce",
        "source",
        "future",
        "schema",
        "keyfile",
    ],
)
def test_missing_corrupt_and_conflicting_receipts_retained(store, mode):
    candidate = create(store)
    path = receipt_path(store, candidate)
    if mode == "missing":
        path.unlink()
    elif mode == "json":
        path.write_text("{bad")
    else:
        key, value = {
            "marker": ("owner", "attacker"),
            "uuid": ("uuid", str(uuid.uuid4())),
            "nonce": ("receipt_id", "forged"),
            "source": ("source_sha256", "bad"),
            "future": ("created_ns", 10**30),
            "schema": ("schema", 2),
            "keyfile": ("keyfile", {"filename": "../foreign"}),
        }[mode]
        rewrite_receipt(store, candidate, lambda data: data.update({key: value}))
    assert store.candidates() == []
    with pytest.raises(Exception):
        store.delete(candidate)
    assert store.nm.deleted == []


@pytest.mark.parametrize("target", ["receipt", "lock", "registry", "keyfile", "parent"])
@pytest.mark.parametrize("attack", ["permissions", "symlink"])
def test_symlinks_and_untrusted_permissions_fail_closed(
    store, tmp_path, target, attack
):
    candidate = create(store)
    path = {
        "receipt": receipt_path(store, candidate),
        "lock": store.registry / ".lock",
        "registry": store.registry,
        "keyfile": store.nm_directory / (candidate["uuid"] + ".nmconnection"),
        "parent": tmp_path,
    }[target]
    if attack == "permissions":
        path.chmod(0o777)
    else:
        if target == "parent":
            # Injectable anchor must itself be a real, protected directory.
            alias = tmp_path.parent / (tmp_path.name + "-alias")
            alias.symlink_to(tmp_path, target_is_directory=True)
            store.anchor = alias
            store.registry = alias / "registry"
            store.nm_directory = alias / "connections"
        else:
            original = path.with_name(path.name + "-original")
            path.rename(original)
            path.symlink_to(original, target_is_directory=original.is_dir())
    with pytest.raises(Exception):
        store.delete(candidate)
    assert store.nm.deleted == []


def test_receipt_hardlink_and_wrong_owner_rejected(store):
    candidate = create(store)
    path = receipt_path(store, candidate)
    os.link(path, path.with_suffix(".alias"))
    assert store.candidates() == []
    with pytest.raises(own.OwnershipError):
        store.delete(candidate)
    path.with_suffix(".alias").unlink()
    store.owner = os.getuid() + 1
    with pytest.raises(own.OwnershipError):
        store.delete(candidate)


@pytest.mark.parametrize("change", ["same_uuid", "new_uuid", "rewrite", "rename_file"])
def test_deleted_recreated_or_rewritten_connections_retained(store, change):
    candidate = create(store)
    path = store.nm_directory / (candidate["uuid"] + ".nmconnection")
    if change == "same_uuid":
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data)
        path.chmod(0o600)
    elif change == "new_uuid":
        del store.nm.rows[candidate["uuid"]]
        replacement = str(uuid.uuid4())
        store.nm.rows[replacement] = candidate["name"]
        store.nm.keyfile(replacement, candidate["name"])
    elif change == "rewrite":
        path.write_text(path.read_text() + "# changed\n")
    else:
        path.rename(path.with_name("renamed.nmconnection"))
    assert store.candidates() == []
    with pytest.raises(Exception):
        store.delete(candidate)
    assert store.nm.deleted == []


def test_rename_uses_current_name_and_uuid_not_old_name(store):
    candidate = create(store)
    store.nm.rows[candidate["uuid"]] = "renamed"
    renamed = store.candidates()[0]
    assert renamed["name"] == "renamed"
    with pytest.raises(own.OwnershipError):
        store.delete(candidate)  # old confirmation invalidated
    store.delete(renamed)
    assert store.nm.deleted == [candidate["uuid"]]


def test_realistic_keyfile_rename_is_conservatively_retained(store):
    candidate = create(store)
    store.nm.rows[candidate["uuid"]] = "renamed"
    store.nm.keyfile(candidate["uuid"], "renamed")
    assert store.candidates() == []
    assert not store.nm.deleted


@pytest.mark.parametrize("failure", ["show", "delete"])
def test_nm_failure_preserves_receipt_and_connection(store, failure):
    candidate = create(store)
    store.nm.fail = failure
    with pytest.raises(own.OwnershipError):
        store.delete(candidate)
    assert receipt_path(store, candidate).exists()
    assert not store.nm.deleted


def test_receipt_changed_after_preview_not_deleted(store):
    candidate = create(store)
    rewrite_receipt(
        store,
        candidate,
        lambda data: data.update({"created_ns": data["created_ns"] - 1}),
    )
    with pytest.raises(own.OwnershipError, match="confirmation expired"):
        store.delete(candidate)
    assert not store.nm.deleted


def test_change_during_final_verification_not_deleted(store, monkeypatch):
    candidate = create(store)
    original = store.nm.show

    def race(identity):
        result = original(identity)
        store.nm.keyfile(identity, "foreign-replacement")
        return result

    monkeypatch.setattr(store.nm, "show", race)
    with pytest.raises(own.OwnershipError):
        store.delete(candidate)
    assert not store.nm.deleted


def test_old_installation_and_foreign_keyfile_never_claimed(store):
    identity = str(uuid.uuid4())
    store.nm.rows[identity] = "vpn"
    store.nm.keyfile(identity, "vpn")
    assert store.candidates() == []
    assert not store.registry.exists()
    with pytest.raises(FileNotFoundError):
        store.inspect(identity, "0" * 32)


@pytest.mark.parametrize("malformation", ["huge", "fifo", "ambiguous"])
def test_keyfile_validation_failure_leaves_new_connection_unmanaged(
    store, malformation, monkeypatch
):
    original = store.nm.create

    def altered(source):
        identity = original(source)
        path = store.nm_directory / (identity + ".nmconnection")
        if malformation == "huge":
            path.write_bytes(b"x" * (own.MAX_CONFIG + 1))
        elif malformation == "fifo":
            path.unlink()
            os.mkfifo(path, 0o600)
        else:
            duplicate = path.with_name("duplicate.nmconnection")
            duplicate.write_bytes(path.read_bytes())
            duplicate.chmod(0o600)
        return identity

    monkeypatch.setattr(store.nm, "create", altered)
    with pytest.raises(own.OwnershipError):
        create(store)
    assert store.candidates() == []
    assert not store.nm.deleted
    assert not list(store.registry.glob(".import-*"))


def test_failed_import_no_receipt_or_staging_left(store):
    store.nm.fail = "create"
    with pytest.raises(own.OwnershipError):
        create(store)
    assert not list(store.registry.glob("*.json"))
    assert not list(store.registry.glob(".import-*"))


def test_receipt_publish_failure_no_claim_or_destructive_rollback(store, monkeypatch):
    monkeypatch.setattr(
        own.os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("full"))
    )
    with pytest.raises(OSError):
        create(store)
    assert not list(store.registry.glob(".receipt-*"))
    assert not list(store.registry.glob("*.json"))
    assert not store.nm.deleted


def test_oversized_registry_and_source_budgets(store, monkeypatch):
    monkeypatch.setattr(own, "MAX_ENTRIES", 2)
    create(store)
    with pytest.raises(own.OwnershipError, match="registry full"):
        create(store, "vpn2")
    with pytest.raises(own.OwnershipError, match="size"):
        store.create("vpn", "x" * (own.MAX_CONFIG + 1))


def test_registry_lock_serializes_deletion(store, monkeypatch):
    candidate = create(store)
    with store.locked():
        monkeypatch.setattr(own.time, "monotonic", iter([0, 3]).__next__)
        with pytest.raises(own.OwnershipError, match="busy"):
            store.delete(candidate)
    assert not store.nm.deleted


def allow_fake_cli(monkeypatch, store, stdin):
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(own, "OwnershipStore", lambda: store)
    monkeypatch.setattr(own.sys, "stdin", StringIO(stdin))


@pytest.mark.parametrize("answer", ["", "n\n", "yes\n"])
def test_cli_preview_confirmation_and_cancel(store, monkeypatch, capsys, answer):
    candidate = create(store)
    allow_fake_cli(monkeypatch, store, answer)
    assert own.main(["cleanup"]) == 0
    output = capsys.readouterr().out
    assert output.index(candidate["uuid"]) < output.index("[y/N]")
    assert candidate["name"] in output
    assert store.nm.deleted == ([candidate["uuid"]] if answer == "yes\n" else [])


def test_cli_refuses_checkout_and_register_existing(monkeypatch, capsys):
    monkeypatch.setattr(own, "trusted_helper_available", lambda: False)
    assert own.main(["cleanup"]) == 1
    assert "Protected installed root helper" in capsys.readouterr().err


def fake_app(monkeypatch, state=None):
    logs = []
    app = SimpleNamespace(
        privacy_config={"nm_last_import": state or {}},
        log=logs.append,
        after=lambda delay, fn: fn(),
        ensure_sudo_session=lambda text: True,
    )
    monkeypatch.setattr(vpn, "call_in_ui_thread", lambda app, fn: fn())
    monkeypatch.setattr(vpn, "_save_privacy_config_safe", lambda *a: True)
    monkeypatch.setattr(vpn, "get_nm_wireguard_profiles", lambda app: [])
    monkeypatch.setattr(
        vpn, "run_cmd", lambda *a, **k: pytest.fail("unexpected real command")
    )
    return app, logs


def test_gui_owned_import_passes_bytes_not_user_path(store, tmp_path, monkeypatch):
    app, _logs = fake_app(monkeypatch)
    source = tmp_path / "gui.conf"
    source.write_text("[Interface]\nAddress=10.1.0.1/32\n")
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    calls = []

    def command(operation, *, payload):
        calls.append((operation, payload))
        return store.create(payload["name"], payload["content"])

    monkeypatch.setattr(vpn, "_owned_nm_command", command)
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert calls == [("import", {"name": "gui", "content": source.read_text()})]
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 1


def test_gui_missing_helper_import_remains_unowned(monkeypatch, tmp_path):
    app, logs = fake_app(monkeypatch)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: False)
    calls = []
    monkeypatch.setattr(
        vpn, "run_cmd", lambda args, **kw: (calls.append(args) or (0, "ok"))
    )
    source = tmp_path / "legacy.conf"
    source.write_text("[Interface]\n")
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == []
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(calls) == 1 and "import" in calls[0]
    assert any("manuell" in entry for entry in logs)


@pytest.mark.parametrize(
    "forgery",
    [
        {"connections": ["foreign"]},
        {
            "connections": ["foreign"],
            "owned_connections": [{"uuid": "forged", "receipt_id": own.OWNER}],
        },
    ],
)
def test_gui_user_json_never_authorizes_deletion(monkeypatch, forgery):
    app, _logs = fake_app(monkeypatch, forgery)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)

    def reject(*a, **kw):
        raise own.OwnershipError("not registered")

    monkeypatch.setattr(vpn, "_owned_nm_command", reject)
    monkeypatch.setattr(
        vpn.messagebox, "askyesno", lambda *a: pytest.fail("no valid plan")
    )
    vpn.rollback_last_nm_wireguard_import(app)


@pytest.mark.parametrize("confirm", [False, True])
def test_gui_rollback_previews_uuid_and_revalidates(store, monkeypatch, confirm):
    candidate = create(store)
    app, _logs = fake_app(
        monkeypatch, {"connections": ["vpn"], "owned_connections": [candidate]}
    )
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)

    def command(operation, *, identity=None, payload=None):
        return (
            store.inspect(*identity)
            if operation == "inspect"
            else store.delete(payload)
        )

    monkeypatch.setattr(vpn, "_owned_nm_command", command)

    def ask(title, text):
        assert candidate["uuid"] in text and candidate["name"] in text
        return confirm

    monkeypatch.setattr(vpn.messagebox, "askyesno", ask)

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(vpn.threading, "Thread", Immediate)
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == ([candidate["uuid"]] if confirm else [])


@pytest.mark.parametrize("kind", ["symlink", "fifo", "size"])
def test_gui_source_snapshot_rejects_unsafe_files(tmp_path, kind):
    source = tmp_path / "bad.conf"
    if kind == "symlink":
        target = tmp_path / "target"
        target.write_text("[Interface]\n")
        source.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(source)
    else:
        source.write_bytes(b"x" * (own.MAX_CONFIG + 1))
    with pytest.raises((OSError, ValueError)):
        vpn._nm_import_source(source)


def test_nm_adapter_absolute_command_and_uuid_selector(monkeypatch):
    calls = []

    def command(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=b"ok")

    monkeypatch.setattr(own.subprocess, "run", command)
    identity = str(uuid.uuid4())
    own.NetworkManager().delete(identity)
    args, kwargs = calls[0]
    assert args[0] == "/usr/bin/nmcli"
    assert args[-4:] == ["connection", "delete", "uuid", identity]
    assert kwargs["env"]["LC_ALL"] == "C"
    assert "PYTHONPATH" not in kwargs["env"]


def test_non_wireguard_keyfiles_do_not_break_managed_import(store):
    ethernet = store.nm_directory / "ethernet.nmconnection"
    ethernet.write_text(
        "[connection]\nid=LAN\ntype=802-3-ethernet\nuuid=" + str(uuid.uuid4())
    )
    ethernet.chmod(0o600)
    candidate = create(store)
    assert store.candidates() == [candidate]


def test_unloaded_existing_keyfile_never_claimed(store):
    identity = str(uuid.uuid4())
    store.nm.keyfile(identity, "foreign-unloaded")
    store.nm.create_uuid = identity
    with pytest.raises(own.OwnershipError, match="Existing UUID"):
        create(store)
    assert not store.nm.deleted
    assert store.candidates() == []


def test_wrong_type_or_uuid_live_query_rejected(monkeypatch):
    identity = str(uuid.uuid4())
    adapter = own.NetworkManager()
    for answer in [
        f"{identity}\nvpn\nethernet",
        f"{uuid.uuid4()}\nvpn\nwireguard",
        f"{identity}\nbad\nname\nwireguard",
    ]:
        monkeypatch.setattr(adapter, "command", lambda *a, text=answer: text)
        with pytest.raises(own.OwnershipError):
            adapter.show(identity)


def test_import_identity_must_come_from_successful_command(monkeypatch, tmp_path):
    adapter = own.NetworkManager()
    identity = str(uuid.uuid4())
    monkeypatch.setattr(
        adapter,
        "command",
        lambda *a: f"Connection 'vpn' ({identity}) successfully added.",
    )
    assert adapter.create(tmp_path / "vpn.conf") == identity
    monkeypatch.setattr(adapter, "command", lambda *a: "vpn successfully added")
    with pytest.raises(own.OwnershipError):
        adapter.create(tmp_path / "vpn.conf")


def test_ui_cannot_override_fixed_privileged_paths(monkeypatch):
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setenv("NETMON_NM_OWNERSHIP_HELPER", "/tmp/attacker.py")
    calls = []
    monkeypatch.setattr(
        vpn,
        "run_cmd_with_input",
        lambda args, **kwargs: (calls.append((args, kwargs)) or (0, "{}")),
    )
    vpn._owned_nm_command("import", payload={"name": "vpn", "content": "SECRET"})
    args, kwargs = calls[0]
    assert args == ["sudo", "-n", "/usr/bin/python3", "-I", own.HELPER, "import"]
    assert "SECRET" not in " ".join(args)
    assert json.loads(kwargs["input_text"])["content"] == "SECRET"


def test_final_race_after_confirmation_is_retained_in_cli(store, monkeypatch, capsys):
    candidate = create(store)
    allow_fake_cli(monkeypatch, store, "yes\n")
    original = store.candidates

    def stale_plan():
        result = original()
        store.nm.keyfile(candidate["uuid"], "replacement")
        return result

    monkeypatch.setattr(store, "candidates", stale_plan)
    assert own.main(["cleanup"]) == 0
    assert not store.nm.deleted
    assert "Retained" in capsys.readouterr().out


def test_partial_batch_keeps_created_profiles_for_separate_confirmation(
    store, tmp_path, monkeypatch
):
    app, logs = fake_app(monkeypatch)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)

    def command(operation, *, payload):
        if payload["name"] == "broken":
            raise own.OwnershipError("error")
        return store.create(payload["name"], payload["content"])

    monkeypatch.setattr(vpn, "_owned_nm_command", command)
    paths = []
    for name in ["good", "broken"]:
        path = tmp_path / (name + ".conf")
        path.write_text("[Interface]\n")
        paths.append(str(path))
    vpn.import_wireguard_paths_to_networkmanager(app, paths)
    assert len(store.candidates()) == 1
    assert not store.nm.deleted
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 1
    assert any("separat" in entry for entry in logs)


def test_cli_has_no_retroactive_register_or_force_operation(store, monkeypatch, capsys):
    allow_fake_cli(monkeypatch, store, "")
    assert own.main(["register-existing", str(uuid.uuid4())]) == 1
    assert own.main(["cleanup", "--force"]) == 1
    assert not store.registry.exists()
    assert not store.nm.deleted
    assert "Ownership verification failed" in capsys.readouterr().err


def test_unloaded_foreign_other_type_uuid_never_claimed(store):
    identity = str(uuid.uuid4())
    path = store.nm.keyfile(identity, "foreign")
    path.write_text(path.read_text().replace("type=wireguard", "type=802-3-ethernet"))
    store.nm.create_uuid = identity
    with pytest.raises(own.OwnershipError, match="Existing UUID"):
        create(store)
    assert store.candidates() == []
    assert not store.nm.deleted


def test_live_nm_backend_must_match_receipt(store, monkeypatch):
    candidate = create(store)
    monkeypatch.setattr(
        store.nm,
        "filename",
        lambda identity: "/run/NetworkManager/system-connections/foreign.nmconnection",
    )
    assert store.candidates() == []
    with pytest.raises(own.OwnershipError, match="storage backend"):
        store.delete(candidate)
    assert not store.nm.deleted


@pytest.mark.parametrize(
    "suffix",
    [
        ":/etc/NetworkManager/system-connections/vpn.nmconnection",
        ":",
        ":/path:with:colons",
    ],
)
def test_nm_adapter_parses_storage_table(monkeypatch, suffix):
    identity = str(uuid.uuid4())
    adapter = own.NetworkManager()
    monkeypatch.setattr(adapter, "command", lambda *args: identity + suffix)
    assert adapter.uuids() == {identity}
    assert adapter.filename(identity) == suffix[1:]


@pytest.mark.parametrize(
    "kind", ["duplicate", "missing_separator", "control", "oversized"]
)
def test_nm_adapter_rejects_ambiguous_storage_table(monkeypatch, kind):
    identity = str(uuid.uuid4())
    text = {
        "duplicate": f"{identity}:/path\n{identity}:/other",
        "missing_separator": identity,
        "control": f"{identity}:/path\tbad",
        "oversized": identity + ":" + "x" * 4097,
    }[kind]
    adapter = own.NetworkManager()
    monkeypatch.setattr(adapter, "command", lambda *args: text)
    with pytest.raises(own.OwnershipError):
        adapter.profiles()
