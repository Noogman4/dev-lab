"""Backup controls, explicit preview consent, worker errors and private Xvfb UI."""

from types import SimpleNamespace
import json
import tkinter as tk

from PIL import ImageGrab
import pytest

from netmon.core import user_backup
from netmon.core import utils
from netmon.features import user_backup_controller as ui
from netmon.ui.tabs import settings_tab
from test_user_backup import data as data, exported as exported


@pytest.fixture(autouse=True)
def clear_write_protection(monkeypatch):
    monkeypatch.setattr(utils, "_RESTORE_WRITE_PROTECTION", frozenset())


@pytest.fixture
def fake_app(monkeypatch):
    calls, logs, statuses, button_states = [], [], [], []
    app = SimpleNamespace(
        tr=lambda key, fallback: fallback,
        backup_status_var=SimpleNamespace(set=statuses.append),
        _append_backup_log=logs.append,
        refresh_netmon_backup_folder_options=lambda: calls.append("refresh"),
        btn_backup_netmon_export=SimpleNamespace(
            configure=lambda **kw: button_states.append(kw["state"])
        ),
        btn_backup_netmon_restore=SimpleNamespace(
            configure=lambda **kw: button_states.append(kw["state"])
        ),
        _netmon_backup_selected_entries=lambda: [{"key": "__all__"}],
        calls=calls,
        logs=logs,
        statuses=statuses,
        button_states=button_states,
    )

    class ImmediateThread:
        def __init__(self, *, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(ui.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(ui, "call_in_ui_thread", lambda app, fn: fn())
    monkeypatch.setattr(
        ui.messagebox,
        "showinfo",
        lambda title, text, **kw: calls.append(("info", text)),
    )
    monkeypatch.setattr(
        ui.messagebox,
        "showerror",
        lambda title, text, **kw: calls.append(("error", text)),
    )
    return app


@pytest.mark.parametrize(
    ("failure", "notification"),
    [
        (None, None),
        (FileNotFoundError("/usr/bin/netmon-manage"), "info"),
        (PermissionError("permission denied"), "error"),
    ],
)
def test_manager_button_only_launches_the_installed_window(
    fake_app, monkeypatch, failure, notification
):
    calls = []

    def launch(args, **options):
        calls.append(args)
        assert options["start_new_session"] is True
        if failure is not None:
            raise failure

    monkeypatch.setattr(settings_tab.subprocess, "Popen", launch)
    assert settings_tab.open_manager(fake_app) is (failure is None)
    assert calls == [["/usr/bin/netmon-manage"]]
    if notification is None:
        assert fake_app.calls == []
    else:
        [(kind, message)] = fake_app.calls
        assert kind == notification
        assert ("netmon-manager" if kind == "info" else str(failure)) in message


def test_export_controls_use_versioned_engine(fake_app, data, monkeypatch):
    monkeypatch.setattr(ui.filedialog, "askdirectory", lambda **kw: str(data.parent))
    assert ui.export_documents(fake_app)
    (folder,) = data.parent.iterdir()
    assert (folder / user_backup.MANIFEST).is_file()
    assert fake_app.button_states == ["disabled", "disabled", "normal", "normal"]
    assert not fake_app._netmon_backup_busy
    assert any(item[0] == "info" for item in fake_app.calls)
    assert len(fake_app.statuses) >= 2
    assert all("mehrere Minuten" in text for text in fake_app.statuses[:-1])


def test_cancel_export_has_no_filesystem_effect(fake_app, data, monkeypatch):
    monkeypatch.setattr(ui.filedialog, "askdirectory", lambda **kw: "")
    assert not ui.export_documents(fake_app)
    assert list(data.parent.iterdir()) == []


def test_partial_export_only_contains_selected_folder(fake_app, data, monkeypatch):
    fake_app._netmon_backup_selected_entries = lambda: [{"key": "Config"}]
    monkeypatch.setattr(ui.filedialog, "askdirectory", lambda **kw: str(data.parent))
    assert ui.export_documents(fake_app)
    (folder,) = data.parent.iterdir()
    assert (folder / "NetMon/Config/config.json").exists()
    assert not (folder / "NetMon/Radio").exists()


def test_restore_previews_without_applying(fake_app, data, exported, monkeypatch):
    monkeypatch.setattr(ui.filedialog, "askdirectory", lambda **kw: str(exported))
    monkeypatch.setattr(ui, "netmon_documents_path", lambda: str(data.target))
    previews = []
    monkeypatch.setattr(ui, "show_preview", lambda app, plan: previews.append(plan))
    monkeypatch.setattr(
        user_backup,
        "restore_backup",
        lambda *a, **kw: pytest.fail("No restore before consent"),
    )
    assert ui.restore_documents(fake_app)
    assert len(previews) == 1 and not data.target.exists()
    assert all("mehrere Minuten" in text for text in fake_app.statuses)


def test_corrupt_backup_shows_error_without_restore(
    fake_app, data, exported, monkeypatch
):
    (exported / "NetMon/Log-Pics/test.png").write_text("corrupt")
    monkeypatch.setattr(ui.filedialog, "askdirectory", lambda **kw: str(exported))
    monkeypatch.setattr(ui, "netmon_documents_path", lambda: str(data.target))
    assert ui.restore_documents(fake_app)
    assert any(item[0] == "error" for item in fake_app.calls)
    assert not data.target.exists() and not fake_app._netmon_backup_busy


def test_busy_action_does_not_start_another_operation(fake_app, monkeypatch):
    fake_app._netmon_backup_busy = True
    monkeypatch.setattr(
        ui.filedialog, "askdirectory", lambda **kw: pytest.fail("Already busy")
    )
    assert not ui.export_documents(fake_app)
    assert not ui.restore_documents(fake_app)


def test_restore_freeze_blocks_stale_settings_and_reading_updates(data, exported):
    from netmon import app as app_module
    from netmon.services.linux_help_reading_service import ReadingState

    user_backup.restore_backup(user_backup.preview_restore(exported, data.target))
    app = app_module.App.__new__(app_module.App)
    app.netmon_config_dir = str(data.target / "Config")
    app.netmon_config_path = str(data.target / "Config/config.json")
    app.settings = {"theme": "old-session"}
    app.log = lambda text: None
    utils.protect_user_json_writes(data.target)
    before = (data.target / "Config/config.json").read_bytes()
    app.save_settings(log_success=False)
    assert (data.target / "Config/config.json").read_bytes() == before
    with pytest.raises(PermissionError, match="Neustart"):
        ReadingState(data.target / "LinuxHelp/reading.json").change(
            {"id": "ls", "cmd": "ls"}, read=True
        )
    outside = data.parent / "unrelated.json"
    assert utils.safe_write_json(outside, {"unrelated": True})[0]
    utils.protect_user_json_writes(data.target, enabled=False)
    app.save_settings(log_success=False)
    assert (
        json.loads((data.target / "Config/config.json").read_text())["theme"]
        == "old-session"
    )


def test_worker_failure_runs_cleanup_and_reenables_controls(fake_app):
    failures = []

    def fail():
        raise ValueError("synthetic operation failure")

    assert ui._run(
        fake_app, fail, lambda value: pytest.fail("No success"), failed=failures.append
    )
    assert len(failures) == 1 and not fake_app._netmon_backup_busy


def test_restart_notice_only_exits_after_explicit_button():
    app = tk.Tk()
    app.update_idletasks()
    app.tr = lambda key, fallback: fallback
    closed = []
    app.on_close = lambda: closed.append(True)
    try:
        notice = ui.show_restart_notice(app, "Synthetic restore completed")
        notice.update_idletasks()
        assert closed == []
        button = next(
            w
            for w in notice.winfo_children()[0].winfo_children()
            if w.winfo_class() == "TButton"
        )
        button.invoke()
        assert closed == [True]
    finally:
        app.destroy()


def test_preview_explains_conflicts_and_inactive_system_references(
    fake_app, data, exported
):
    plan = user_backup.preview_restore(exported, data.target)
    text = ui.preview_text(fake_app, plan)
    assert "keine digitale Herkunftssignatur" in text
    assert "nicht als aktuelle Systemreferenz" in text
    assert "WireGuard" in text and "manuellen Neustart" in text
    assert "Config/config.json" in text
    assert str(data.root) in text and str(data.target) in text


@pytest.mark.parametrize("width", [760, 1050])
def test_real_preview_has_visible_actions_and_cancel_is_read_only(
    data, exported, width
):
    app = tk.Tk()
    app.geometry("300x100+0+0")
    app.update_idletasks()
    app.tr = lambda key, fallback: fallback
    plan = user_backup.preview_restore(exported, data.target)
    window = None
    try:
        window = ui.show_preview(app, plan)
        window.geometry(f"{width}x640+10+10")
        window.update_idletasks()
        window.update()
        buttons = []

        def walk(widget):
            if widget.winfo_class() == "TButton":
                buttons.append(widget)
            for child in widget.winfo_children():
                walk(child)

        walk(window)
        assert len(buttons) == 2
        for button in buttons:
            assert button.winfo_rootx() >= window.winfo_rootx()
            assert (
                button.winfo_rootx() + button.winfo_width()
                <= window.winfo_rootx() + window.winfo_width()
            )
            assert (
                button.winfo_rooty() + button.winfo_height()
                <= window.winfo_rooty() + window.winfo_height()
            )
        x, y = window.winfo_rootx(), window.winfo_rooty()
        ImageGrab.grab(
            (x, y, x + window.winfo_width(), y + window.winfo_height())
        ).save(f"/work/netmon-restore-preview-{width}.png")
        buttons[0].invoke()
        assert not data.target.exists()
        window = None
    finally:
        if window is not None:
            window.destroy()
        app.destroy()


@pytest.mark.parametrize("replace", [False, True])
def test_apply_requires_button_and_replacement_is_explicit(
    data, exported, monkeypatch, replace
):
    from test_user_backup import json_file

    destination = json_file(data.target / "Config/config.json", {"theme": "light"})
    data.target.chmod(0o700)
    app = tk.Tk()
    app.update_idletasks()
    app.tr = lambda key, fallback: fallback
    app.backup_status_var = tk.StringVar(app)
    app._append_backup_log = lambda text: None
    app.refresh_netmon_backup_folder_options = lambda: None
    monkeypatch.setattr(ui.messagebox, "showinfo", lambda *a, **kw: None)
    monkeypatch.setattr(
        ui, "_run", lambda app, operation, finished, **kwargs: finished(operation())
    )
    notices = []
    monkeypatch.setattr(
        ui, "show_restart_notice", lambda app, text: notices.append(text)
    )
    try:
        window = ui.show_preview(
            app, user_backup.preview_restore(exported, data.target)
        )
        window.update_idletasks()
        widgets = []

        def walk(widget):
            widgets.append(widget)
            for child in widget.winfo_children():
                walk(child)

        walk(window)
        assert json.loads(destination.read_text())["theme"] == "light"
        checkbox = next(w for w in widgets if w.winfo_class() == "TCheckbutton")
        assert not bool(app.tk.getvar(checkbox.cget("variable")))
        if replace:
            checkbox.invoke()
        buttons = [w for w in widgets if w.winfo_class() == "TButton"]
        buttons[1].invoke()
        assert json.loads(destination.read_text())["theme"] == (
            "dark" if replace else "light"
        )
        assert "Neustart" in app.backup_status_var.get()
        assert notices
    finally:
        app.destroy()
