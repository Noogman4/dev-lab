"""Imports and real Tk widget construction in the external private sandbox."""

import os
from pathlib import Path


def test_dns_imports_from_this_copy():
    from netmon import app
    from netmon.features import dns_controller, dot_controller
    from netmon.services import dns_control_service

    root = Path(__file__).resolve().parents[1]
    for module in (app, dns_controller, dot_controller, dns_control_service):
        assert Path(module.__file__).resolve().is_relative_to(root)
    assert callable(dns_control_service.DNSControlService.parse_dns_snapshot)


def test_cancel_child_widget_timer_before_destroy():
    import tkinter as tk

    from netmon.main import _cancel_pending_after_callbacks

    root = tk.Tk()
    root.withdraw()
    child = tk.Frame(root)
    callback = child.after(60_000, lambda: None)
    try:
        _cancel_pending_after_callbacks(root)
        assert callback not in root.tk.call("after", "info")
        child.destroy()
    finally:
        root.destroy()


def test_dns_gui_smoke(monkeypatch):
    import netmon.app as app_module
    from netmon.features import dns_controller, dot_controller
    from netmon.app import App
    from netmon.main import (
        _cancel_pending_after_callbacks,
        _temporary_app_smoke_patches,
    )

    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"
    unexpected = []

    def read_only_fixture(args, **kwargs):
        if args == ["resolvectl", "status"]:
            return 1, "synthetic unavailable resolver; status remains unknown"
        if args == ["systemctl", "is-active", "systemd-resolved"]:
            return 3, "inactive"
        if args in (
            ["wg", "show", "interfaces"],
            ["ip", "-o", "link", "show", "type", "wireguard"],
            ["ufw", "status", "verbose"],
            ["sudo", "-n", "ufw", "status", "verbose"],
        ):
            return 1, "synthetic unavailable status; no host command executed"
        unexpected.append(list(args))
        raise AssertionError(f"GUI construction requested unexpected command: {args}")

    monkeypatch.setattr(app_module, "run_cmd", read_only_fixture)
    monkeypatch.setattr(dns_controller, "run_cmd", read_only_fixture)
    monkeypatch.setattr(dot_controller, "run_cmd", read_only_fixture)
    monkeypatch.setattr(App, "get_default_iface", lambda self: "")
    monkeypatch.setattr(App, "_load_sysinfo_static", lambda self: None)

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, **options):
            self.target, self.args, self.kwargs = target, args, kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)
    # GUI construction only. Do not drain scheduled startup callbacks.
    with _temporary_app_smoke_patches(App):
        application = App(start_theme="dark")
        try:
            application.update_idletasks()
            assert application.tab_dns.winfo_exists()
            assert str(application.tab_dns) in application.nb.tabs()
            application.nb.select(application.tab_dns)
            assert application.nb.select() == str(application.tab_dns)
            assert callable(application.apply_dns)
            assert callable(application.run_dns_guard_check_once)
            assert callable(application.dns_repair_rollback_async)

            # Exercise the actual PATH button and private Xvfb clipboard. Copying
            # must neither trigger a new check nor navigate to the Chad tab.
            def unexpected_action(*args, **kwargs):
                raise AssertionError("Copy requested a check or Chad navigation")

            application.run_path_guard_check = unexpected_action
            application.prepare_chad_analysis = unexpected_action
            application.chad_filter_ignore_dev_environment_var.set(True)
            application.clipboard_clear()
            application.clipboard_append("existing clipboard")
            application.path_guard_last_result = None
            application.btn_path_guard_copy_prompt.invoke()
            assert application.clipboard_get() == "existing clipboard"
            application.path_guard_last_result = {
                "risk": "mittel",
                "counts": {"high": 0, "medium": 1},
                "path_entries": [
                    "/synthetic/project/bin",
                    "/synthetic/.vscode/extensions/bin",
                ],
                "review_items": [
                    {
                        "target": "/synthetic/project/bin",
                        "issue": "synthetic reviewed finding",
                        "state": "geprüft / Risiko akzeptiert",
                    }
                ],
            }
            application.btn_path_guard_copy_prompt.invoke()
            prompt = application.clipboard_get()
            assert "PATH Guard" in prompt
            assert "/synthetic/project/bin" in prompt
            assert "/synthetic/.vscode/extensions/bin" in prompt
            assert "synthetic reviewed finding" in prompt
            assert "geprüft / Risiko akzeptiert" in prompt
            assert application.nb.select() == str(application.tab_dns)
        finally:
            _cancel_pending_after_callbacks(application)
            application.destroy()
    assert unexpected == [], repr(unexpected)
