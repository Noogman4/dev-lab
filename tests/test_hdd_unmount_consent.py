"""Unmount consent tests use synthetic block identities and command fakes only."""

import json
from pathlib import Path
import queue
import threading
from types import SimpleNamespace

import pytest
from tkinter import TclError

from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service
from tests.test_hdd_mount_security import DEVICE, UUID
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app
from tests.test_hdd_mount_security import unmount_app as unmount_app

REAL_CONFIRM = controller._confirm_hdd_unmount
REAL_THREAD = threading.Thread


@pytest.mark.parametrize(
    "target",
    [
        "/",
        "/home",
        "/boot",
        "/boot/efi",
        "/usr",
        "/usr/local",
        "/var/lib/data",
        "/opt/application",
        "/srv",
        "/dev",
        "/proc",
        "/sys",
        "/etc",
        "/root",
        "/run/user/1000",
        "/run/media",
        "/mnt",
        "/media",
        "/tmp",
    ],
)
def test_matching_live_system_mount_never_reaches_consent_or_sudo(unmount_app, target):
    unmount_app.row["target"] = target
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.confirmations
    assert not unmount_app.auth
    assert not unmount_app.effects
    assert any("refused" in line for line in unmount_app.app.logs)


@pytest.mark.parametrize("ancestor", [False, True])
def test_active_account_home_is_protected_despite_forged_home_environment(
    unmount_app, monkeypatch, tmp_path, ancestor
):
    home = tmp_path / "accounts" / "active"
    monkeypatch.setattr(
        service.pwd, "getpwuid", lambda _uid: SimpleNamespace(pw_dir=str(home))
    )
    monkeypatch.setenv("HOME", "/attacker/decoy")
    unmount_app.row["target"] = str(home.parent if ancestor else home)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.confirmations
    assert not unmount_app.auth
    assert not unmount_app.effects


def test_unavailable_account_home_fails_closed(unmount_app, monkeypatch):
    def missing(_uid):
        raise KeyError("synthetic unavailable account")

    monkeypatch.setattr(service.pwd, "getpwuid", missing)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.confirmations
    assert not unmount_app.auth
    assert not unmount_app.effects


@pytest.mark.parametrize(
    "target", ["/mnt/data", "/media/user/disk", "/run/media/user/disk", "/variety"]
)
def test_data_mounts_remain_available_with_explicit_consent(unmount_app, target):
    unmount_app.row["target"] = target
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.confirmations[0][1] == target
    assert unmount_app.effects == [["sudo", "-n", "umount", target]]


@pytest.mark.parametrize("answer", [True, False, None])
def test_dialog_uses_live_identity_and_requires_explicit_yes(
    unmount_app, monkeypatch, answer
):
    monkeypatch.setattr(controller, "_confirm_hdd_unmount", REAL_CONFIRM)
    app = unmount_app.app
    app.hdd_slots[0]["custom_name"] = "Deceptive slot description"
    app.confirmations_enabled = False
    dialogs = []

    def ask(title, message, **kwargs):
        assert not unmount_app.auth and not unmount_app.effects
        dialogs.append((title, message, kwargs))
        return answer

    monkeypatch.setattr(controller.messagebox, "askyesno", ask)
    controller.hdd_unmount_async(app, 0)
    assert len(dialogs) == 1
    _title, message, options = dialogs[0]
    assert DEVICE in message and UUID in message and "8:17" in message
    assert unmount_app.target in message
    assert "ignored-config" not in message and "Deceptive" not in message
    assert options["default"] == controller.messagebox.NO
    assert options["icon"] == controller.messagebox.WARNING
    assert options["parent"] is app
    if answer is True:
        assert unmount_app.auth == ["HDD Unmount"]
        assert unmount_app.effects == [["sudo", "-n", "umount", unmount_app.target]]
    else:
        assert not unmount_app.auth and not unmount_app.effects
        assert any("cancelled" in line for line in app.logs)


@pytest.mark.parametrize("error", [TclError, RuntimeError])
def test_dialog_failure_never_acquires_privileges(unmount_app, monkeypatch, error):
    monkeypatch.setattr(controller, "_confirm_hdd_unmount", REAL_CONFIRM)

    def fail(*_args, **_kwargs):
        raise error("synthetic dialog failure")

    monkeypatch.setattr(controller.messagebox, "askyesno", fail)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.auth and not unmount_app.effects
    assert any("refused" in line for line in unmount_app.app.logs)


@pytest.mark.parametrize("change", ["source", "target", "uuid", "device"])
def test_change_during_confirmation_is_rejected_before_sudo(
    kernel, unmount_app, monkeypatch, change
):
    def confirm(*_args):
        if change == "device":
            kernel.node["uuid"] = "replacement"
        else:
            unmount_app.row[change] = {
                "source": "/dev/foreign",
                "target": "/mnt/changed",
                "uuid": "replacement",
            }[change]
        return True

    monkeypatch.setattr(controller, "_confirm_hdd_unmount", confirm)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.auth and not unmount_app.effects


def test_real_worker_waits_for_ui_consent(unmount_app, monkeypatch):
    monkeypatch.setattr(controller, "_confirm_hdd_unmount", REAL_CONFIRM)
    jobs = []
    callbacks = queue.Queue()
    app = unmount_app.app
    app.after = lambda _delay, fn: callbacks.put(fn)

    def launch(**kwargs):
        thread = REAL_THREAD(**kwargs)
        jobs.append(thread)
        return thread

    monkeypatch.setattr(
        controller, "threading", SimpleNamespace(Thread=launch, Event=threading.Event)
    )
    dialog_threads = []

    def cancel(*_args, **_kwargs):
        dialog_threads.append(threading.current_thread())
        assert not unmount_app.auth and not unmount_app.effects
        return False

    monkeypatch.setattr(controller.messagebox, "askyesno", cancel)
    controller.hdd_unmount_async(app, 0)
    try:
        while not dialog_threads:
            callbacks.get(timeout=3)()
        jobs[0].join(timeout=3)
        assert not jobs[0].is_alive()
        assert dialog_threads == [threading.main_thread()]
        assert not unmount_app.auth and not unmount_app.effects
    finally:
        # Drain UI feedback; no host commands can escape the fixture runner.
        while not callbacks.empty():
            callbacks.get_nowait()()


@pytest.mark.parametrize("language", ["de", "en"])
def test_consent_translations_have_all_identity_fields(language):
    translations = json.loads(
        (Path(__file__).parents[1] / "netmon" / "lang" / f"{language}.json").read_text()
    )

    message = translations["hdd_unmount_confirm_body"]
    assert message
    assert all(
        "{" + field + "}" in message
        for field in ("device", "source", "uuid", "number", "target")
    )
