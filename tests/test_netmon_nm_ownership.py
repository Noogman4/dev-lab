"""L-01/F-01: synthetic NM and real local persistence, no system profiles."""

from io import StringIO
import json
import os
from types import SimpleNamespace
import uuid

import pytest

from netmon.core import nm_ownership as own
from netmon.features import vpn_controller as vpn


@pytest.fixture(autouse=True)
def private_profile_creation():
    # Synthetic secret-bearing profiles should have deployment-safe permissions.
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


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
    monkeypatch.setattr(vpn, "_network_links", dict)
    logs = []
    app = SimpleNamespace(
        privacy_config={},
        log=logs.append,
        after=lambda delay, fn: fn(),
        ensure_sudo_session=lambda text: True,
    )
    monkeypatch.setattr(vpn, "call_in_ui_thread", lambda app, fn: fn())
    if state is not None:
        vpn.set_nm_last_import_state(app, state)
    monkeypatch.setattr(vpn, "get_nm_wireguard_profiles", lambda app: [])
    monkeypatch.setattr(
        vpn, "run_cmd", lambda *a, **k: pytest.fail("unexpected real command")
    )
    monkeypatch.setattr(vpn.messagebox, "askyesno", lambda *a, **k: True)
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
    assert calls == [
        ("import", vpn.wireguard_import.ProfileSnapshot.read(source).payload())
    ]
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 1


def test_gui_missing_helper_import_fails_closed(monkeypatch, tmp_path):
    app, logs = fake_app(monkeypatch)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: False)
    calls = []
    monkeypatch.setattr(
        vpn, "run_cmd", lambda args, **kw: (calls.append(args) or (0, "ok"))
    )
    source = tmp_path / "legacy.conf"
    source.write_text("[Interface]\n")
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])
    assert vpn.get_nm_last_import_state(app).get("owned_connections", []) == []
    vpn.rollback_last_nm_wireguard_import(app)
    assert calls == []
    assert any("fehlgeschlagen" in entry for entry in logs)


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
    app, _logs = fake_app(monkeypatch)
    app.privacy_config["nm_last_import"] = forgery
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
    assert args == [
        "sudo",
        "-n",
        "/usr/bin/python3",
        "-I",
        own.HELPER,
        "import-checked",
    ]
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


@pytest.fixture
def real_privacy_app(store, tmp_path, monkeypatch):
    """Real App persistence and real receipt validation, synthetic NM only."""
    monkeypatch.setattr(vpn, "_network_links", dict)
    from netmon.app import App

    app = App.__new__(App)
    logs, operations, previews = [], [], []
    app.privacy_config_path = str(tmp_path / "config" / "privacy.json")
    app.netmon_config_dir = str(tmp_path / "config")
    app.netmon_config_path = str(tmp_path / "config" / "settings.json")
    app.settings = {"language": "de", "unrelated_setting": "keep"}
    app.privacy_config = {
        "wg_import_dir": str(tmp_path),
        "unrelated_privacy": {"keep": [1, 2]},
    }
    app.log = logs.append
    app.log_debug_safe = logs.append
    app.after = lambda delay, fn: fn()
    app.ensure_sudo_session = lambda text: True
    app.test_logs = logs
    app.test_operations = operations
    app.test_previews = previews
    monkeypatch.setattr(vpn, "call_in_ui_thread", lambda app, fn: fn())
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(
        vpn, "get_nm_wireguard_profiles", lambda app: list(store.nm.rows.values())
    )
    monkeypatch.setattr(
        vpn, "run_cmd", lambda *a, **kw: pytest.fail("real command forbidden")
    )
    monkeypatch.setattr(
        vpn, "run_cmd_with_input", lambda *a, **kw: pytest.fail("real helper forbidden")
    )

    def helper(operation, *, payload=None, identity=None):
        operations.append(operation)
        if operation == "import":
            return store.create(payload["name"], payload["content"])
        if operation == "inspect":
            return store.inspect(*identity)
        assert operation == "delete"
        return store.delete(payload)

    monkeypatch.setattr(vpn, "_owned_nm_command", helper)
    monkeypatch.setattr(
        vpn.messagebox,
        "askyesno",
        lambda title, text, **kwargs: (
            True
            if title == "WireGuard-Import bestaetigen"
            else (previews.append(text) or True)
        ),
    )

    class ImmediateThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(vpn.threading, "Thread", ImmediateThread)
    return app


def import_for_session(app, tmp_path, name="session-vpn"):
    source = tmp_path / (name + ".conf")
    source.write_text("[Interface]\nAddress=10.2.0.1/32\n")
    vpn.import_wireguard_paths_to_networkmanager(app, [str(source)])


def test_session_import_survives_real_privacy_save(real_privacy_app, store, tmp_path):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    assert state.get("owned_connections", []) == [candidate]
    assert state["connections"] == [candidate["name"]]
    saved = json.loads((tmp_path / "config" / "privacy.json").read_text())
    assert "nm_last_import" not in saved
    assert saved["unrelated_privacy"] == {"keep": [1, 2]}
    settings = json.loads((tmp_path / "config" / "settings.json").read_text())
    assert settings["unrelated_setting"] == "keep"
    serialized = json.dumps([saved, settings])
    assert candidate["uuid"] not in serialized
    assert candidate["receipt_id"] not in serialized
    assert "owned_connections" not in serialized
    assert "_nm_last_import_state" not in serialized


def test_session_rollback_after_real_privacy_save(real_privacy_app, store, tmp_path):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]
    app.save_privacy_config()
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == [candidate["uuid"]]
    assert candidate["uuid"] in app.test_previews[0]


@pytest.mark.parametrize("previous_import", [False, True])
def test_session_failed_import_preserves_previous_state(
    real_privacy_app, store, tmp_path, previous_import
):
    app = real_privacy_app
    if previous_import:
        import_for_session(app, tmp_path, "first")
    before = vpn.get_nm_last_import_state(app)
    store.nm.fail = "create"
    import_for_session(app, tmp_path, "broken")
    app.save_privacy_config()
    assert vpn.get_nm_last_import_state(app) == before
    assert not store.nm.deleted
    assert any("fehlgeschlagen" in text for text in app.test_logs)


def test_session_second_import_preserves_both_verified_references(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    import_for_session(app, tmp_path, "first")
    app.save_privacy_config()
    first = vpn.get_nm_last_import_state(app)["owned_connections"][0]
    import_for_session(app, tmp_path, "second")
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    assert state["connections"] == ["first", "second"]
    assert len(state["owned_connections"]) == 2
    assert state["owned_connections"][0] == first
    vpn.rollback_last_nm_wireguard_import(app)
    assert set(store.nm.deleted) == {
        item["uuid"] for item in state["owned_connections"]
    }
    assert all(
        item["uuid"] in app.test_previews[0] for item in state["owned_connections"]
    )


def test_session_cancel_and_repeated_rollback(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    monkeypatch.setattr(vpn.messagebox, "askyesno", lambda *args: False)
    vpn.rollback_last_nm_wireguard_import(app)
    assert vpn.get_nm_last_import_state(app) == state
    assert not store.nm.deleted
    app.save_privacy_config()
    monkeypatch.setattr(vpn.messagebox, "askyesno", lambda *args: True)
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == []
    app.save_privacy_config()
    operations = list(app.test_operations)
    vpn.rollback_last_nm_wireguard_import(app)
    assert app.test_operations == operations
    assert len(store.nm.deleted) == 1


def test_session_rollback_preserves_foreign_duplicate_name(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]
    foreign = str(uuid.uuid4())
    store.nm.rows[foreign] = candidate["name"]
    store.nm.keyfile(foreign, candidate["name"])
    app.save_privacy_config()
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == [candidate["uuid"]]
    assert store.nm.rows == {foreign: candidate["name"]}


@pytest.mark.parametrize("damage", ["missing", "invalid", "permissions", "recreated"])
def test_session_reference_cannot_replace_valid_ownership_proof(
    real_privacy_app, store, tmp_path, damage
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    if damage == "missing":
        receipt_path(store, candidate).unlink()
    elif damage == "invalid":
        rewrite_receipt(
            store, candidate, lambda record: record.update({"owner": "forged"})
        )
    elif damage == "permissions":
        receipt_path(store, candidate).chmod(0o666)
    else:
        store.nm.keyfile(candidate["uuid"], "replacement")
    vpn.rollback_last_nm_wireguard_import(app)
    assert not store.nm.deleted
    assert not app.test_previews
    assert vpn.get_nm_last_import_state(app) == state


def test_session_restart_does_not_restore_even_valid_receipt_references(
    real_privacy_app, store, tmp_path
):
    from netmon.app import App

    app = real_privacy_app
    import_for_session(app, tmp_path)
    state = vpn.get_nm_last_import_state(app)
    app.save_privacy_config()
    path = tmp_path / "config" / "privacy.json"
    saved = json.loads(path.read_text())
    saved["nm_last_import"] = state  # Inject a real UUID/nonce, not merely a bad token.
    path.write_text(json.dumps(saved))
    restarted = App.__new__(App)
    restarted.settings = {}
    restarted.privacy_config_path = str(path)
    restarted.log = app.test_logs.append
    restarted.privacy_config = restarted.load_privacy_config()
    assert "nm_last_import" not in restarted.privacy_config
    assert restarted.privacy_config["unrelated_privacy"] == {"keep": [1, 2]}
    assert vpn.get_nm_last_import_state(restarted)["connections"] == []
    operations = list(app.test_operations)
    vpn.rollback_last_nm_wireguard_import(restarted)
    assert app.test_operations == operations
    assert not store.nm.deleted
    assert store.candidates() == state["owned_connections"]


def test_session_save_write_error_preserves_state_and_existing_config(
    real_privacy_app, store, tmp_path, monkeypatch
):
    from netmon.core import utils

    app = real_privacy_app
    app.save_privacy_config()
    path = tmp_path / "config" / "privacy.json"
    before = path.read_bytes()
    import_for_session(app, tmp_path)
    state = vpn.get_nm_last_import_state(app)
    replace = utils.os.replace

    def fail_privacy_write(source, target):
        if str(target) == str(path):
            raise OSError("synthetic privacy write error")
        return replace(source, target)

    monkeypatch.setattr(utils.os, "replace", fail_privacy_write)
    app.save_privacy_config()
    assert path.read_bytes() == before
    assert vpn.get_nm_last_import_state(app) == state
    assert app.privacy_config["unrelated_privacy"] == {"keep": [1, 2]}
    assert any("synthetic privacy write error" in text for text in app.test_logs)
    assert not list(path.parent.glob(".netmon-tmp-*"))
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1


def test_session_changed_after_confirmation_is_not_deleted(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]
    app.save_privacy_config()

    def confirm_and_change(title, text):
        assert candidate["uuid"] in text
        store.nm.keyfile(candidate["uuid"], "changed-after-preview")
        return True

    monkeypatch.setattr(vpn.messagebox, "askyesno", confirm_and_change)
    vpn.rollback_last_nm_wireguard_import(app)
    assert not store.nm.deleted
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == [candidate]


@pytest.mark.parametrize("failure_stage", ["before_creation", "after_creation"])
def test_session_partial_import_tracks_only_successful_receipts(
    real_privacy_app, store, tmp_path, monkeypatch, failure_stage
):
    app = real_privacy_app
    create_original, find_original = store.nm.create, store._find_created

    def create_with_error(source):
        if source.stem == "broken" and failure_stage == "before_creation":
            raise own.OwnershipError("synthetic import error")
        return create_original(source)

    def find_with_error(identity):
        if store.nm.rows[identity] == "broken" and failure_stage == "after_creation":
            raise own.OwnershipError("synthetic receipt error")
        return find_original(identity)

    monkeypatch.setattr(store.nm, "create", create_with_error)
    monkeypatch.setattr(store, "_find_created", find_with_error)
    sources = []
    for name in ["good", "broken"]:
        source = tmp_path / (name + ".conf")
        source.write_text("[Interface]\n")
        sources.append(str(source))
    vpn.import_wireguard_paths_to_networkmanager(app, sources)
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    assert state["connections"] == ["good"]
    assert len(state["owned_connections"]) == 1
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == [state["owned_connections"][0]["uuid"]]
    assert list(store.nm.rows.values()) == (
        ["broken"] if failure_stage == "after_creation" else []
    )


@pytest.mark.parametrize("entry", ["file_dialog", "referenced_profiles"])
def test_session_canceled_import_keeps_previous_references(
    real_privacy_app, store, tmp_path, monkeypatch, entry
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    app.save_privacy_config()
    state = vpn.get_nm_last_import_state(app)
    operations = list(app.test_operations)
    monkeypatch.setattr(vpn, "has_cmd", lambda name: True)
    app.tr = lambda key, fallback: fallback
    if entry == "file_dialog":
        monkeypatch.setattr(vpn.filedialog, "askopenfilenames", lambda **kwargs: ())
        vpn.import_wg_profiles_to_networkmanager(app)
    else:
        app.collect_referenced_wg_profile_import_paths = lambda: []
        vpn.import_referenced_wg_profiles_to_networkmanager(app)
    app.save_privacy_config()
    assert vpn.get_nm_last_import_state(app) == state
    assert app.test_operations == operations
    assert not store.nm.deleted


def test_session_stale_reference_does_not_authorize_reused_uuid(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    old = vpn.get_nm_last_import_state(app)
    identity = old["owned_connections"][0]["uuid"]
    app.save_privacy_config()
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == [identity]
    store.nm.create_uuid = identity
    import_for_session(app, tmp_path, "new-session")
    current = store.candidates()[0]
    assert current["receipt_id"] != old["owned_connections"][0]["receipt_id"]
    # Even restoring old in-memory data conveys no authorization over the
    # replacement. Only the independently checked fresh root receipt can do so.
    vpn.set_nm_last_import_state(app, old)
    app.save_privacy_config()
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == [identity]
    assert store.nm.rows == {identity: "new-session"}
    assert store.candidates() == [current]


def test_r1_overlapping_import_results_are_both_retained(
    real_privacy_app, tmp_path, monkeypatch
):
    app = real_privacy_app
    original = vpn._owned_nm_command
    nested = False

    def overlap(operation, **kwargs):
        nonlocal nested
        result = original(operation, **kwargs)
        if operation == "import" and not nested:
            nested = True
            import_for_session(app, tmp_path, "newer")
        return result

    monkeypatch.setattr(vpn, "_owned_nm_command", overlap)
    import_for_session(app, tmp_path, "older")
    app.save_privacy_config()
    assert set(vpn.get_nm_last_import_state(app)["connections"]) == {"older", "newer"}
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 2


def test_r1_delayed_rollback_keeps_newer_import_reference(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path, "older")
    old = store.candidates()[0]
    queued = []

    class QueuedThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            queued.append(self.target)

    monkeypatch.setattr(vpn.threading, "Thread", QueuedThread)
    vpn.rollback_last_nm_wireguard_import(app)
    import_for_session(app, tmp_path, "newer")
    newer = next(item for item in store.candidates() if item["uuid"] != old["uuid"])
    queued.pop()()
    app.save_privacy_config()
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == [newer]
    assert store.nm.deleted == [old["uuid"]]


def test_r2_after_failure_retains_successful_import_reference(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    app.after = lambda *args: (_ for _ in ()).throw(RuntimeError("GUI closed"))
    try:
        import_for_session(app, tmp_path)
    except RuntimeError:
        pass
    assert (
        vpn.get_nm_last_import_state(app).get("owned_connections", [])
        == store.candidates()
    )
    assert len(store.candidates()) == 1


def test_r1_repeated_rollback_worker_cannot_touch_newer_import(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path, "old")
    old = store.candidates()[0]
    queued = []

    class Queued:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            queued.append(self.target)

    monkeypatch.setattr(vpn.threading, "Thread", Queued)
    vpn.rollback_last_nm_wireguard_import(app)
    vpn.rollback_last_nm_wireguard_import(app)
    import_for_session(app, tmp_path, "new")
    new = next(item for item in store.candidates() if item["uuid"] != old["uuid"])
    queued[1]()
    queued[0]()
    queued[1]()
    assert store.nm.deleted == [old["uuid"]]
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == [new]
    assert app.test_operations.count("delete") == 1


def test_r1_import_during_delete_is_not_lost(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path, "old")
    original = vpn._owned_nm_command

    def overlap(operation, **kwargs):
        result = original(operation, **kwargs)
        if operation == "delete":
            import_for_session(app, tmp_path, "new-during-delete")
        return result

    monkeypatch.setattr(vpn, "_owned_nm_command", overlap)
    vpn.rollback_last_nm_wireguard_import(app)
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == store.candidates()
    assert vpn.get_nm_last_import_state(app)["connections"] == ["new-during-delete"]


def test_r1_running_job_rejects_bulk_snapshot_replacement(
    real_privacy_app, tmp_path, monkeypatch
):
    app = real_privacy_app
    original = vpn._owned_nm_command

    def inspect_update(operation, **kwargs):
        if operation == "import":
            with pytest.raises(RuntimeError, match="snapshot replacement forbidden"):
                vpn.set_nm_last_import_state(app, {"owned_connections": []})
        return original(operation, **kwargs)

    monkeypatch.setattr(vpn, "_owned_nm_command", inspect_update)
    import_for_session(app, tmp_path)
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 1


def test_r1_duplicate_import_worker_executes_once(
    real_privacy_app, tmp_path, monkeypatch
):
    app = real_privacy_app
    source = tmp_path / "once.conf"
    source.write_text("[Interface]\n")
    queued = []

    class Queued:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            queued.append(self.target)

    monkeypatch.setattr(vpn.threading, "Thread", Queued)
    vpn._start_nm_import_job(app, [str(source)], "once")
    queued[0]()
    operations = list(app.test_operations)
    queued[0]()
    assert app.test_operations == operations == ["import"]
    assert not vpn._nm_session(app).active


def test_r1_job_cannot_cross_application_sessions(real_privacy_app, tmp_path):
    from netmon.core.nm_import_session import ImportSession

    other = ImportSession({"connections": [], "source_files": [], "imported_at": 0})
    job = other.new_job("import")
    vpn.import_wireguard_paths_to_networkmanager(
        real_privacy_app, [str(tmp_path / "unused")], _job=job
    )
    assert real_privacy_app.test_operations == []
    assert job.phase == "queued"


def test_r1_snapshots_do_not_alias_owned_records(real_privacy_app, store, tmp_path):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    snapshot = vpn.get_nm_last_import_state(app)
    snapshot["owned_connections"][0]["uuid"] = str(uuid.uuid4())
    snapshot["connections"].clear()
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == store.candidates()
    assert vpn.get_nm_last_import_state(app)["connections"] == ["session-vpn"]


@pytest.mark.parametrize(
    "failure", ["entry_transition", "job_transition", "compatibility_setter"]
)
def test_r2_state_update_failure_keeps_raw_import_result(
    real_privacy_app, store, tmp_path, monkeypatch, caplog, failure
):
    app = real_privacy_app
    session = vpn._nm_session(app)

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic state update failure")

    target, method = {
        "entry_transition": (session, "finish_import"),
        "job_transition": (session, "finish"),
        "compatibility_setter": (vpn, "set_nm_last_import_state"),
    }[failure]
    monkeypatch.setattr(target, method, fail)
    import_for_session(app, tmp_path)
    app.save_privacy_config()
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == store.candidates()
    assert len(store.candidates()) == 1
    if failure != "compatibility_setter":
        assert "gesichert" in caplog.text
        assert not any("beendet:" in message for message in app.test_logs)
    assert not session.active
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1


@pytest.mark.parametrize(
    "failure",
    ["closed_before_delivery", "log_failure", "enqueue_then_raise", "event_failure"],
)
def test_r2_callback_errors_never_change_import_results(
    real_privacy_app, store, tmp_path, monkeypatch, caplog, failure
):
    app = real_privacy_app
    callbacks = []

    def schedule(delay, callback):
        callbacks.append(callback)
        if failure == "enqueue_then_raise":
            raise RuntimeError("after enqueued then failed")

    app.after = schedule
    session = vpn._nm_session(app)
    if failure == "event_failure":
        monkeypatch.setattr(
            session,
            "notification",
            lambda *args: (_ for _ in ()).throw(RuntimeError("event failed")),
        )
    import_for_session(app, tmp_path)
    before = vpn.get_nm_last_import_state(app)
    assert before["owned_connections"] == store.candidates()
    app.save_privacy_config()
    if failure == "closed_before_delivery":
        app.winfo_exists = lambda: False
    elif failure == "log_failure":
        app.log = lambda message: (_ for _ in ()).throw(RuntimeError("widget gone"))
    for callback in callbacks:
        callback()
        callback()
    assert vpn.get_nm_last_import_state(app) == before
    assert not store.nm.deleted
    assert not app.test_logs
    assert "gesichert" in caplog.text


def test_r2_delayed_and_duplicate_callbacks_are_read_only(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    callbacks = []
    app.after = lambda delay, callback: callbacks.append(callback)
    import_for_session(app, tmp_path, "first")
    first = vpn._nm_session(app).jobs[-1]
    import_for_session(app, tmp_path, "second")
    second = vpn._nm_session(app).jobs[-1]
    before = vpn.get_nm_last_import_state(app)
    operations = list(app.test_operations)
    callbacks[1]()
    callbacks[0]()
    callbacks[1]()
    assert len(app.test_logs) == 1
    assert f"Job {second.token}" in app.test_logs[0]
    assert f"Job {first.token}" not in app.test_logs[0]
    assert vpn.get_nm_last_import_state(app) == before
    assert app.test_operations == operations
    assert not store.nm.deleted


def test_r2_old_import_callback_after_rollback_cannot_report_success(
    real_privacy_app, store, tmp_path
):
    app = real_privacy_app
    callbacks = []
    app.after = lambda delay, callback: callbacks.append(callback)
    import_for_session(app, tmp_path)
    old = callbacks[0]
    vpn.rollback_last_nm_wireguard_import(app)
    old()
    callbacks[-1]()
    assert len(store.nm.deleted) == 1
    assert len(app.test_logs) == 1
    assert "entfernt" in app.test_logs[0]
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == []


@pytest.mark.parametrize("delete_failure", [False, True])
def test_r2_rollback_callback_failure_preserves_actual_result(
    real_privacy_app, store, tmp_path, caplog, delete_failure
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    original = store.candidates()[0]
    app.after = lambda *args: (_ for _ in ()).throw(RuntimeError("closed"))
    if delete_failure:
        store.nm.fail = "delete"
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == ([] if delete_failure else [original["uuid"]])
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == (
        [original] if delete_failure else []
    )
    assert "GUI-Callback" in caplog.text
    assert not vpn._nm_session(app).active


def test_r2_delete_transition_error_keeps_actual_deletion_recorded(
    real_privacy_app, store, tmp_path, monkeypatch, caplog
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    session = vpn._nm_session(app)
    monkeypatch.setattr(
        session,
        "finish_delete",
        lambda *args: (_ for _ in ()).throw(RuntimeError("state error")),
    )
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == []
    assert "tatsächliches Ergebnis" in caplog.text
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1


@pytest.mark.parametrize("started", [False, True])
def test_r2_worker_start_error_does_not_lose_completed_result(
    real_privacy_app, store, tmp_path, monkeypatch, started
):
    app = real_privacy_app

    class BadStart:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            if started:
                self.target()
            raise RuntimeError("start failed")

    monkeypatch.setattr(vpn.threading, "Thread", BadStart)
    source = tmp_path / "start.conf"
    source.write_text("[Interface]\n")
    vpn._start_nm_import_job(app, [str(source)], "start")
    assert (
        vpn.get_nm_last_import_state(app).get("owned_connections", [])
        == store.candidates()
    )
    assert len(store.candidates()) == int(started)
    assert not vpn._nm_session(app).active


def test_r2_reference_capacity_is_checked_before_creation(
    real_privacy_app, store, tmp_path, monkeypatch
):
    from netmon.core import nm_import_session

    app = real_privacy_app
    monkeypatch.setattr(nm_import_session, "MAX_REFERENCES", 1)
    import_for_session(app, tmp_path, "first")
    first = store.candidates()[0]
    import_for_session(app, tmp_path, "second")
    assert app.test_operations == ["import"]
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == [first]


def test_r1_real_threads_with_controlled_completion_order(
    real_privacy_app, store, tmp_path, monkeypatch
):
    import threading
    from _thread import start_new_thread

    # The fixture replaces Thread for deterministic UI workers. Use the low-
    # level thread API here to exercise the real session locks without Tk/NM.
    app = real_privacy_app
    waiting, release, finished = threading.Event(), threading.Event(), threading.Event()
    original = vpn._owned_nm_command
    errors = []

    def overlap(operation, **kwargs):
        result = original(operation, **kwargs)
        if operation == "import" and kwargs["payload"]["name"] == "older-thread":
            waiting.set()
            assert release.wait(5), "test release timeout"
        return result

    monkeypatch.setattr(vpn, "_owned_nm_command", overlap)

    def older():
        try:
            import_for_session(app, tmp_path, "older-thread")
        except BaseException as error:
            errors.append(error)
        finally:
            finished.set()

    start_new_thread(older, ())
    try:
        assert waiting.wait(5), "older import did not reach controlled wait"
        import_for_session(app, tmp_path, "newer-thread")
        app.save_privacy_config()
    finally:
        release.set()
        assert finished.wait(5), "older import did not finish"
    assert not errors
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 2
    assert set(vpn.get_nm_last_import_state(app)["connections"]) == {
        "older-thread",
        "newer-thread",
    }
    assert len(store.candidates()) == 2


def test_r1_wrong_job_kind_cannot_start_an_import(real_privacy_app, tmp_path):
    app = real_privacy_app
    session = vpn._nm_session(app)
    job = session.new_job("rollback")
    vpn.import_wireguard_paths_to_networkmanager(
        app, [str(tmp_path / "unused")], _job=job
    )
    assert app.test_operations == []
    assert job.phase == "queued"
    session.finish(job, "canceled")


@pytest.mark.parametrize("started", [False, True])
def test_r2_rollback_start_error_preserves_real_outcome(
    real_privacy_app, store, tmp_path, monkeypatch, started
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    candidate = store.candidates()[0]

    class BadStart:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            if started:
                self.target()
            raise RuntimeError("start outcome error")

    monkeypatch.setattr(vpn.threading, "Thread", BadStart)
    vpn.rollback_last_nm_wireguard_import(app)
    assert store.nm.deleted == ([candidate["uuid"]] if started else [])
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == (
        [] if started else [candidate]
    )
    assert not vpn._nm_session(app).active


def test_r2_notification_generation_belongs_to_completed_job(
    real_privacy_app, tmp_path, monkeypatch
):
    app = real_privacy_app
    callbacks = []
    app.after = lambda delay, callback: callbacks.append(callback)
    notify = vpn._nm_notify
    nested = False

    def delayed_notification(app, session, job, message):
        nonlocal nested
        if not nested:
            nested = True
            import_for_session(app, tmp_path, "newer-before-old-notification")
        notify(app, session, job, message)

    monkeypatch.setattr(vpn, "_nm_notify", delayed_notification)
    import_for_session(app, tmp_path, "old-notification")
    jobs = list(vpn._nm_session(app).jobs)
    assert len(jobs) == 2
    for callback in reversed(callbacks):
        callback()
        callback()
    assert len(app.test_logs) == 1
    assert f"Job {jobs[1].token}" in app.test_logs[0]
    assert len(vpn.get_nm_last_import_state(app)["owned_connections"]) == 2


def test_r2_failed_claim_releases_only_its_own_reservation(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    session = vpn._nm_session(app)
    claim = session.claim_delete

    def broken_claim(*args):
        assert claim(*args) is not None
        raise RuntimeError("after reservation")

    monkeypatch.setattr(session, "claim_delete", broken_claim)
    vpn.rollback_last_nm_wireguard_import(app)
    assert not store.nm.deleted
    assert len(session.references()) == 1
    assert not session.active
    monkeypatch.setattr(session, "claim_delete", claim)
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1


def test_r1_failed_transition_cannot_clear_another_jobs_reservation(
    real_privacy_app, store, tmp_path, monkeypatch
):
    app = real_privacy_app
    import_for_session(app, tmp_path)
    session = vpn._nm_session(app)
    finish_delete = session.finish_delete
    other = []

    def broken_transition(entry, job):
        finish_delete(entry, job)  # First job's failed delete releases its lease.
        second = session.new_job("rollback")
        assert session.start(second, "rollback")
        assert session.claim_delete(entry.token, entry.result, second) is entry
        other.append(second)
        raise RuntimeError("after another job acquired reservation")

    monkeypatch.setattr(session, "finish_delete", broken_transition)
    store.nm.fail = "delete"
    vpn.rollback_last_nm_wireguard_import(app)
    entry = next(iter(session.entries.values()))
    assert entry.deleting_job == other[0].token
    assert session.active == {other[0].token}
    assert not store.nm.deleted
    session.finish(other[0], "canceled")
    assert len(session.references()) == 1


def test_r2_recorded_deletion_releases_capacity_after_transition_error(
    real_privacy_app, store, tmp_path, monkeypatch
):
    from netmon.core import nm_import_session

    app = real_privacy_app
    monkeypatch.setattr(nm_import_session, "MAX_REFERENCES", 1)
    import_for_session(app, tmp_path, "old-capacity")
    session = vpn._nm_session(app)
    monkeypatch.setattr(
        session,
        "finish_delete",
        lambda *args: (_ for _ in ()).throw(RuntimeError("after actual delete")),
    )
    vpn.rollback_last_nm_wireguard_import(app)
    assert len(store.nm.deleted) == 1
    import_for_session(app, tmp_path, "new-capacity")
    assert vpn.get_nm_last_import_state(app)["owned_connections"] == store.candidates()
    assert vpn.get_nm_last_import_state(app)["connections"] == ["new-capacity"]
