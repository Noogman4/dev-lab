"""Synthetic HDD requests and real Tk feedback; never operate a host drive."""

import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
from tkinter import ttk

import pytest
from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service
from netmon.ui.tabs.hdd_tab import build_hdd_tab
from tests.test_hdd_mount_security import DEVICE, privileged_calls
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app
from tests.test_hdd_mount_security import unmount_app as unmount_app

REAL_THREAD = threading.Thread


class Status:
    def __init__(self):
        self.values = []

    def set(self, value):
        assert threading.current_thread() is threading.main_thread()
        self.values.append(value)

    @property
    def text(self):
        return self.values[-1] if self.values else ""


def feedback(app):
    app.hdd_action_status_var = Status()
    app.tab_hdd = object()
    app._select_system_tab = Mock()
    app.page_canvas = SimpleNamespace(yview_moveto=Mock())
    return app.hdd_action_status_var


def test_mount_success_is_visible_and_keeps_safe_options(kernel, mount_app):
    status = feedback(mount_app)
    controller.hdd_mount_async(mount_app, 0)
    assert "requested" in status.values[0]
    assert "desktop-integriert" in status.text
    assert privileged_calls(kernel) == [
        [
            "udisksctl",
            "mount",
            "--block-device",
            DEVICE,
            "--options",
            "nodev,nosuid,noexec",
        ]
    ]
    mount_app._select_system_tab.assert_called_with(mount_app.tab_hdd)


def test_unmount_success_is_visible(unmount_app):
    status = feedback(unmount_app.app)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert "requested" in status.values[0]
    assert "unmount successful" in status.text
    assert unmount_app.effects == [["sudo", "-n", "umount", unmount_app.target]]


def test_mount_backend_denial_has_visible_reason_without_root_fallback(
    kernel, mount_app
):
    status = feedback(mount_app)
    kernel.mount_rc = 1
    controller.hdd_mount_async(mount_app, 0)
    assert "mount failed" in status.text and "synthetic mount result" in status.text
    assert len(privileged_calls(kernel)) == 1


def test_busy_unmount_has_visible_hint_and_is_never_forced(unmount_app):
    status = feedback(unmount_app.app)
    unmount_app.result = (1, "GDBus.Error.DeviceBusy: target is busy")
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert "busy" in status.text and "in use" in status.text
    assert "successful" not in status.text
    assert len(unmount_app.effects) == 4
    assert all(
        not any(x in {"-f", "-l", "--force", "--lazy"} for x in c)
        for c in unmount_app.effects
    )


def test_regular_fstab_source_stays_rejected_with_visible_reason(
    kernel, mount_app, tmp_path
):
    status = feedback(mount_app)
    swap = tmp_path / "swapfile"
    swap.write_bytes(b"synthetic file, never used as a device")
    kernel.table.write_text(f"{swap} none swap defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": str(swap), "fstype": "swap"}]}),
    )
    controller.hdd_mount_async(mount_app, 0)
    assert "fstab" in status.text and "swapfile" in status.text
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("tool", ["udisksctl", "lsblk", "findmnt"])
def test_missing_tool_is_visible_before_commands(kernel, mount_app, monkeypatch, tool):
    status = feedback(mount_app)
    monkeypatch.setattr(controller, "has_cmd", lambda name: name != tool)
    controller.hdd_mount_async(mount_app, 0)
    assert "required" in status.text and not kernel.calls


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_invalid_binding_is_visible_without_effects(kernel, unmount_app, action):
    status = feedback(unmount_app.app)
    unmount_app.app.hdd_slots[0]["device_uuid"] = "foreign-uuid"
    getattr(controller, f"hdd_{action}_async")(unmount_app.app, 0)
    assert "rejected" in status.text or "refused" in status.text
    assert not kernel.calls and not unmount_app.effects and not unmount_app.auth


def test_luks_cancel_is_visible_without_unlock(kernel, mount_app, monkeypatch):
    status = feedback(mount_app)
    kernel.node["fstype"] = "crypto_LUKS"
    monkeypatch.setattr(controller.simpledialog, "askstring", lambda *a, **kw: None)
    controller.hdd_mount_async(mount_app, 0)
    assert "cancelled" in status.text and not privileged_calls(kernel)


def test_unmount_authorization_cancel_is_visible(unmount_app):
    status = feedback(unmount_app.app)
    unmount_app.app.ensure_sudo_session = lambda label: False
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert "authorization" in status.text and not unmount_app.effects


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_worker_start_failure_is_visible_before_effects(
    kernel, unmount_app, monkeypatch, action
):
    status = feedback(unmount_app.app)

    class Unavailable:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise RuntimeError("synthetic worker limit")

    monkeypatch.setattr(controller.threading, "Thread", Unavailable)
    getattr(controller, f"hdd_{action}_async")(unmount_app.app, 0)
    assert "synthetic worker limit" in status.text
    assert not kernel.calls and not unmount_app.effects and not unmount_app.auth


@pytest.mark.parametrize("action", ["mount", "unmount"])
@pytest.mark.parametrize("index", [-1, 20, None, "1", True])
def test_invalid_slot_is_visible_and_never_queries_devices(
    kernel, unmount_app, action, index
):
    status = feedback(unmount_app.app)
    getattr(controller, f"hdd_{action}_async")(unmount_app.app, index)
    assert "slot" in status.text.lower()
    assert not kernel.calls and not unmount_app.effects


def test_background_feedback_does_not_steal_focus(kernel, mount_app):
    status = feedback(mount_app)
    controller.hdd_mount_async(mount_app, 0, select_tab=False)
    assert "desktop-integriert" in status.text
    mount_app._select_system_tab.assert_not_called()
    mount_app.page_canvas.yview_moveto.assert_not_called()


def test_worker_failure_feedback_runs_on_main_thread(kernel, mount_app):
    status = feedback(mount_app)
    callbacks = []
    mount_app.after = lambda delay, callback: callbacks.append(callback)
    kernel.node["uuid"] = "changed-before-live-inspection"
    worker = REAL_THREAD(target=lambda: controller.hdd_mount_async(mount_app, 0))
    worker.start()
    worker.join(5)
    assert not worker.is_alive() and not status.values
    while callbacks:
        callbacks.pop(0)()
    assert "rejected" in status.text and not privileged_calls(kernel)


def test_actual_hdd_tab_shows_rejected_button_request(monkeypatch):
    root = tk.Tk()
    root.geometry("900x650")
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)
    app = SimpleNamespace(system_nb=nb, tr=lambda key, fallback: fallback, logs=[])
    for name in [
        "scan_hdds_async",
        "add_tooltip",
        "on_hdd_name_focus_in",
        "on_hdd_name_focus_out",
        "on_hdd_name_changed",
        "assign_selected_disk_to_slot",
        "clear_slot_assignment",
        "on_hdd_table_select",
        "on_hdd_auto_mount_toggle",
    ]:
        setattr(app, name, Mock())
    app.log = app.logs.append
    app.after = root.after
    app._select_system_tab = lambda tab: nb.select(tab)
    app.hdd_slots = [{"device": "", "device_uuid": ""}]
    app.detected_disks = []
    app.detected_disks_by_device = {}
    monkeypatch.setattr(
        service,
        "run_hdd_command",
        Mock(side_effect=AssertionError("No host operation allowed")),
    )
    try:
        build_hdd_tab(app)
        button = ttk.Button(root, command=lambda: controller.hdd_mount_async(app, 0))
        button.pack()
        button.invoke()
        root.update()
        assert app.hdd_action_status_label.winfo_viewable()
        assert "rejected" in app.hdd_action_status_var.get()
        assert nb.select() == str(app.tab_hdd)
        service.run_hdd_command.assert_not_called()
    finally:
        root.destroy()


def test_luks_close_failure_stays_visible_after_successful_unmount(
    kernel, unmount_app, monkeypatch
):
    from tests.test_hdd_review_regressions import crypt_device

    crypt_device(kernel, unmount_app)
    status = feedback(unmount_app.app)
    monkeypatch.setattr(controller, "has_cmd", lambda name: name != "cryptsetup")
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert any("unmount successful" in text for text in status.values)
    assert "LUKS close failed" in status.text
    assert not any("cryptsetup" in args for args in unmount_app.effects)


@pytest.mark.parametrize(
    "language, expected",
    [("de", "Das Laufwerk ist belegt"), ("en", "The drive is in use")],
)
def test_busy_feedback_has_translated_explanation(unmount_app, language, expected):
    from pathlib import Path

    translations = json.loads(
        (
            Path(__file__).resolve().parents[1] / f"netmon/lang/{language}.json"
        ).read_text()
    )
    unmount_app.app.tr = lambda key, fallback: translations.get(key, fallback)
    status = feedback(unmount_app.app)
    unmount_app.result = (1, "target is busy")
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert expected in status.text
    assert "target is busy" in status.text


def test_udisks_permission_denial_is_explained_without_sudo(
    kernel, mount_app, monkeypatch
):
    status = feedback(mount_app)

    def denied(args, **kwargs):
        if args[:2] == ["udisksctl", "mount"]:
            kernel.calls.append(args)
            return 1, "org.freedesktop.UDisks2.Error.NotAuthorized: Not authorized"
        return kernel.runner(args, **kwargs)

    monkeypatch.setattr(service, "run_hdd_command", denied)
    controller.hdd_mount_async(mount_app, 0)
    assert "not authorized" in status.text
    assert "permissions" in status.text
    assert len(privileged_calls(kernel)) == 1
    assert not any(args[0] == "sudo" for args in kernel.calls)
