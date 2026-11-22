"""Exercise the shared entry with fake maintenance runners, never real actions."""

import configparser
from pathlib import Path
import shlex
from unittest.mock import Mock

import pytest

from netmon import manage_assistant as manager
from netmon.core import lifecycle


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setattr(
        manager, "netmon_documents_path", lambda: str(tmp_path / "NetMon")
    )
    calls = []
    app = manager.ManagementWindow(lang="de", version="1.0", runner=calls.append)
    app.update()
    yield app, calls
    app.destroy()


def test_single_visible_management_entry_and_hidden_legacy_install_entry():
    entries = []
    for name in ("netmon-install.desktop", "netmon-uninstall.desktop"):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / "packaging" / name)
        entry = config["Desktop Entry"]
        assert entry["Exec"] == "/usr/bin/netmon-manage"
        assert entry["Terminal"] == "false"
        entries.append(entry)
    assert (
        sum(not entry.getboolean("NoDisplay", fallback=False) for entry in entries) == 1
    )
    assert entries[1]["Name"] == "NetMon verwalten"


def test_opening_window_is_passive_and_both_removal_buttons_forward_the_mode(window):
    app, calls = window
    assert calls == []
    assert list(app.buttons) == ["install", "backup", "keep", "delete"]

    def labels(widget):
        for child in widget.winfo_children():
            if child.winfo_class() == "Label":
                yield child.cget("text")
            yield from labels(child)

    assert sum(app.copy["duration"] in text for text in labels(app)) == 2
    for action in ("keep", "delete"):
        app.buttons[action].invoke()
        assert calls[-1] == ["/usr/bin/netmon-uninstall", "--mode", action]
    assert len(calls) == 2
    assert app.status.get() == app.copy["launched"]


@pytest.mark.parametrize("package", ["", "/tmp/NetMon ' neu; $(touch marker).deb"])
def test_package_selection_and_cancellation(window, monkeypatch, package):
    app, calls = window
    monkeypatch.setattr(manager.filedialog, "askopenfilename", lambda **kwargs: package)
    app.buttons["install"].invoke()
    assert calls == ([["/usr/bin/netmon-install", package]] if package else [])


def test_missing_terminal_reports_an_error_without_success_status(window, monkeypatch):
    app, calls = window
    errors = []

    def missing(_argv):
        raise FileNotFoundError("fixture")

    app.runner = missing
    monkeypatch.setattr(
        manager.messagebox, "showerror", lambda *args, **kw: errors.append(args)
    )
    app.buttons["keep"].invoke()
    assert errors == [(app.copy["error"], app.copy["terminal"])]
    assert app.status.get() == ""
    assert calls == []


@pytest.mark.parametrize("lang", ["de", "en"])
@pytest.mark.parametrize("size", ["700x520", "1060x880"])
def test_window_keeps_close_button_visible_and_all_actions_reachable(
    tmp_path, monkeypatch, lang, size
):
    monkeypatch.setattr(
        manager, "netmon_documents_path", lambda: str(tmp_path / "NetMon")
    )
    app = manager.ManagementWindow(lang=lang, version="1.0", runner=lambda _: None)
    try:
        app.geometry(size)
        app.update()
        assert app.title() == manager.COPY[lang]["title"]
        assert (
            app.footer_text.winfo_y() + app.footer_text.winfo_height()
            <= app.footer_text.master.winfo_height()
        )
        for action in ("install", "backup", "keep", "delete"):
            button = app.buttons[action]
            reachable = False
            for step in range(21):
                app.canvas.yview_moveto(step / 20)
                app.update()
                y = button.winfo_rooty() - app.canvas.winfo_rooty()
                if 0 <= y and y + button.winfo_height() <= app.canvas.winfo_height():
                    reachable = True
                    break
            assert reachable, action
    finally:
        app.destroy()


def test_terminal_launch_quotes_package_and_uses_clean_environment(monkeypatch):
    package = "/tmp/NetMon ' neu; $(touch marker).deb"
    commands = []
    launches = []
    monkeypatch.setattr(
        manager,
        "maintenance_terminal_command",
        lambda script: commands.append(script) or ["fixture-terminal"],
    )
    monkeypatch.setattr(manager, "terminal_environment", lambda: {"LANG": "C.UTF-8"})
    monkeypatch.setattr(
        manager.subprocess, "Popen", lambda argv, **kw: launches.append((argv, kw))
    )
    monkeypatch.setattr(manager.Path, "is_file", lambda _: True)
    manager.launch_terminal(manager.action_command("install", package))
    assert shlex.split(commands[0].splitlines()[0]) == [
        "/usr/bin/netmon-install",
        package,
    ]
    assert launches == [
        (["fixture-terminal"], {"env": {"LANG": "C.UTF-8"}, "start_new_session": True})
    ]


@pytest.mark.parametrize(
    "action,package", [("unknown", None), ("install", None), ("backup", None)]
)
def test_incomplete_or_unknown_action_cannot_launch(action, package):
    with pytest.raises(ValueError):
        manager.action_command(action, package)


@pytest.mark.parametrize("folder", ["", "/tmp/Sicherung ' neu; $(touch marker)"])
def test_backup_folder_selection_and_cancellation(window, monkeypatch, folder):
    app, calls = window
    options = []

    def choose(**kwargs):
        options.append(kwargs)
        return folder

    monkeypatch.setattr(manager.filedialog, "askdirectory", choose)
    app.buttons["backup"].invoke()
    assert options[0]["mustexist"] is True
    assert options[0]["initialdir"].endswith("/NetMon-Sicherungen")
    assert calls == (
        [["/usr/bin/netmon-manage", "--backup", "--parent", folder, "--lang", "de"]]
        if folder
        else []
    )


def test_backup_terminal_preserves_quoted_folder_as_one_argument(monkeypatch):
    folder = "/tmp/Sicherung ' neu; $(touch marker)"
    scripts = []
    monkeypatch.setattr(
        manager,
        "maintenance_terminal_command",
        lambda script: scripts.append(script) or ["fixture-terminal"],
    )
    monkeypatch.setattr(manager, "terminal_environment", lambda: {})
    monkeypatch.setattr(manager.subprocess, "Popen", lambda *args, **kwargs: None)
    command = manager.action_command("backup", backup_parent=folder, lang="en")
    monkeypatch.setattr(manager.Path, "is_file", lambda _: True)
    manager.launch_terminal(command)
    assert shlex.split(scripts[0].splitlines()[0]) == [
        "/usr/bin/netmon-manage",
        "--backup",
        "--parent",
        folder,
        "--lang",
        "en",
    ]


def test_backup_cli_does_not_open_a_window(monkeypatch):
    backup = Mock(return_value=0)
    monkeypatch.setattr(manager, "run_backup", backup)
    monkeypatch.setattr(
        manager, "ManagementWindow", Mock(side_effect=AssertionError("No GUI expected"))
    )
    assert manager.main(["--backup", "--parent", "/tmp/backups", "--lang", "en"]) == 0
    backup.assert_called_once_with("/tmp/backups", lang="en")


@pytest.mark.parametrize(
    "args", [["--backup"], ["--parent", "/tmp/backups"], ["--lang", "en"]]
)
def test_incomplete_backup_cli_cannot_start_work(monkeypatch, args):
    backup = Mock()
    monkeypatch.setattr(manager, "run_backup", backup)
    with pytest.raises(SystemExit) as error:
        manager.main(args)
    assert error.value.code == 2
    backup.assert_not_called()


def test_backup_refuses_root_before_any_work(monkeypatch, capsys):
    monkeypatch.setattr(manager.os, "geteuid", lambda: 0)
    backup = Mock()
    closed = Mock()
    monkeypatch.setattr(manager, "backup_for_update", backup)
    monkeypatch.setattr(manager, "ensure_closed", closed)
    assert manager.run_backup("/tmp/backups") == 1
    backup.assert_not_called()
    closed.assert_not_called()
    assert "ohne sudo" in capsys.readouterr().err


def test_running_netmon_stops_backup_before_export(monkeypatch, capsys):
    monkeypatch.setattr(
        manager, "ensure_closed", Mock(side_effect=ValueError("Close NetMon first"))
    )
    backup = Mock()
    monkeypatch.setattr(manager, "backup_for_update", backup)
    assert manager.run_backup("/tmp/backups", lang="en") == 1
    backup.assert_not_called()
    output = capsys.readouterr()
    assert "Close NetMon first" in output.err
    assert manager.COPY["en"]["backup_done"] not in output.out


@pytest.mark.parametrize("lang", ["de", "en"])
def test_backup_exports_and_verifies_without_installing_or_changing_source(
    tmp_path, monkeypatch, capsys, lang
):
    documents = tmp_path / "documents"
    source = documents / "NetMon"
    (source / "Config").mkdir(parents=True)
    original = b'{"theme": "dark"}\n'
    (source / "Config/config.json").write_bytes(original)
    parent = tmp_path / "backups"
    parent.mkdir()
    monkeypatch.setattr(lifecycle, "document_root", lambda: documents)
    monkeypatch.setattr(manager, "ensure_closed", lambda: None)
    commands = Mock(side_effect=AssertionError("Backup must not run system commands"))
    monkeypatch.setattr(manager.subprocess, "run", commands)
    assert manager.run_backup(str(parent), lang=lang) == 0
    commands.assert_not_called()
    backups = list(parent.glob("netmon_documents_backup_*"))
    assert len(backups) == 1
    assert (backups[0] / "NetMon/Config/config.json").read_bytes() == original
    assert (source / "Config/config.json").read_bytes() == original
    assert (backups[0] / "netmon_documents_backup_manifest.json").is_file()
    output = capsys.readouterr()
    assert manager.COPY[lang]["backup_done"] in output.out
    assert manager.COPY[lang]["duration"] in output.out
    assert str(backups[0]) in output.out
    assert manager.COPY[lang]["backup_files"].format(count=1) in output.out
    assert manager.COPY[lang]["backup_verify"] in output.err


def test_changed_browser_data_cannot_be_reported_as_verified(monkeypatch, capsys):
    monkeypatch.setattr(manager, "ensure_closed", lambda: None)
    monkeypatch.setattr(
        manager,
        "backup_for_update",
        Mock(
            side_effect=ValueError(
                "Quelle wurde verändert: Secure Browser/Proton/profile/cache.json"
            )
        ),
    )
    assert manager.run_backup("/tmp/backups") == 1
    output = capsys.readouterr()
    assert "Quelle wurde verändert" in output.err
    assert manager.COPY["de"]["backup_done"] not in output.out


def test_management_removal_is_explicit_and_never_attached_to_keep(window):
    app, calls = window
    assert not app.remove_manager.get()
    app.remove_manager.set(True)
    app.buttons["keep"].invoke()
    assert calls[-1] == ["/usr/bin/netmon-uninstall", "--mode", "keep"]
    app.buttons["delete"].invoke()
    assert calls[-1] == [
        "/usr/bin/netmon-uninstall",
        "--mode",
        "delete",
        "--remove-manager",
    ]
    app.manager_button.invoke()
    assert calls[-1] == ["/usr/bin/netmon-uninstall", "--mode", "manager"]
    with pytest.raises(ValueError):
        manager.action_command("keep", remove_manager=True)


def test_version_refresh_after_external_uninstall(window, monkeypatch):
    app, _ = window
    app._version_override = None
    monkeypatch.setattr(manager, "installed_version", lambda: "")
    app._refresh_version()
    assert app.version_text.get() == app.copy["missing"]
    monkeypatch.setattr(manager, "installed_version", lambda: "1.1.22~beta3")
    app._refresh_version()
    assert app.version_text.get().endswith("1.1.22~beta3")
