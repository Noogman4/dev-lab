import gc
import hashlib
import io
import os
from pathlib import Path
import stat
import subprocess
import threading
import tkinter as tk
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon.core import privileged_config as writer, system_files
from netmon.core import system_logs
from netmon.ui.tabs.system_files_view import SystemFilesView
from tests.test_system_logs import _wait


@pytest.fixture
def file_view(monkeypatch):
    root = tk.Tk()
    app = App.__new__(App)
    app.tk, app._w, app.children = root.tk, root._w, root.children
    app.tr = lambda _key, fallback: fallback
    handed, sounds = [], []
    app.prepare_chad_analysis = lambda title, text: handed.append((title, text))
    app._click_sound_command = root.register(lambda: sounds.append("click"))
    files = {
        "/etc/fstab": "# mount configuration\n",
        system_files.CRYPTTAB: "# mapping configuration\n",
        writer.HOSTS: "127.0.0.1 localhost\n",
        system_files.RESOLV_CONF: "nameserver 127.0.0.53\n",
        system_files.NSSWITCH: "# hosts: commented out\npasswd: files\nhosts: files dns\n",
        "/etc/ufw/user.rules": "# test rules\n",
        "/etc/apparmor.d/local/example": (
            "# Fixture content\nProfile Allow\nprofile deny\nPRIMARY data\n"
        ),
        "/etc/apparmor.d/example": "profile netmon-example { /tmp/example r, }\n",
        "/etc/apt/sources.list.d/example.sources": (
            "URIs: https://example.invalid/install\n"
            "password=fixture-only-private\nSuites: stable\n"
        ),
    }
    monkeypatch.setattr(
        system_files,
        "discover_files",
        lambda: {
            "mounts": ["/etc/fstab", system_files.CRYPTTAB],
            "apparmor": ["/etc/apparmor.d/local/example", "/etc/apparmor.d/example"],
            "network": [writer.HOSTS, system_files.RESOLV_CONF, system_files.NSSWITCH],
            "packages": ["/etc/apt/sources.list.d/example.sources"],
            "firewall": ["/etc/ufw/user.rules"],
        },
    )
    monkeypatch.setattr(
        system_files, "read_file", lambda path: system_files.FileSnapshot(files[path])
    )
    view = SystemFilesView(app, root)
    view.frame.pack(fill="both", expand=True)
    view.on_shown()
    try:
        _wait(lambda: view.snapshot is not None, root)
        yield root, view, files, handed, sounds
    finally:
        root.destroy()


def test_file_filter_and_content_navigation(file_view):
    root, view, files, _handed, _sounds = file_view
    apparmor = "/etc/apparmor.d/local/example"
    view.filter_var.set("LoCaL/")
    _wait(lambda: view.snapshot is not None, root)
    assert view.tree.get_children() == ("apparmor",)
    assert view.tree.get_children("apparmor") == (apparmor,)
    assert view.selected_path == apparmor

    view.text.focus_force()
    root.update()
    view.text.event_generate("<Control-f>")
    root.update()
    assert root.focus_get() is view.search_entry
    view.search_var.set("pRoFiLe")
    assert view.search_status.get() == "1 von 2"
    assert tuple(map(str, view.text.tag_ranges("search_current"))) == ("2.0", "2.7")
    assert view.text.tag_ranges("sel") == ()
    view.search_entry.event_generate("<Return>")
    assert view.search_status.get() == "2 von 2"
    assert tuple(map(str, view.text.tag_ranges("search_current"))) == ("3.0", "3.7")
    view.search_prev.invoke()
    assert view.search_status.get() == "1 von 2"
    assert view.text.get("1.0", "end-1c") == files[apparmor]

    view.filter_var.set(".sources")
    _wait(lambda: view.snapshot is not None, root)
    assert view.tree.get_children() == ("packages",)
    assert view.search_status.get() == "Keine Treffer."
    assert view.search_next.instate(["disabled"])
    view.filter_var.set("nicht-vorhanden")
    assert view.tree.get_children() == ()
    assert view.text.get("1.0", "end-1c") == ""
    assert view.status.get() == "Keine passenden Dateien."


def test_fstab_action_checks_the_snapshot_on_a_worker(file_view, monkeypatch):
    root, view, files, _handed, _sounds = file_view
    calls = []

    def verify(text):
        assert threading.current_thread() is not threading.main_thread()
        calls.append(text)
        return system_files.FstabCheck(
            "warnings",
            "[W] unreachable source",
            syntax_errors=0,
            optional_missing=("/mnt/backup",),
            type_unavailable=("/", "/boot/efi"),
            active_swaps=("/swapfile",),
            mounted_types=(("/mnt/disk", "ext4"),),
        )

    monkeypatch.setattr(system_files, "check_fstab", verify)
    assert view.file_action.cget("text") == "fstab prüfen"
    assert view.file_action.instate(["!disabled"])
    displayed = files[system_files.FSTAB]
    files[system_files.FSTAB] = "# Changed outside the viewer\n"
    view.file_action.invoke()
    report = view.check_reports[system_files.FSTAB]
    pane = report.winfo_children()[0]
    status, output_frame = pane.winfo_children()[1:3]
    _wait(lambda: status.cget("text") == "Prüfung meldet Warnungen.", root)
    output = output_frame.winfo_children()[0]
    assert output.get("1.0", "end-1c") == (
        "Syntax in Ordnung.\n"
        "Das optionale Laufwerk unter /mnt/backup ist derzeit nicht verfügbar (noauto,nofail).\n"
        "/mnt/disk ist laut Kernel als ext4 eingehängt. Die direkte Prüfung am Datenträger braucht Leserechte.\n"
        "Fehlende Leserechte verhindern die Prüfung des Dateisystemtyps für /, /boot/efi.\n"
        "Die Swapdatei /swapfile ist laut Kernel aktiv.\n\n"
        "Originalausgabe von findmnt\n"
        "[W] unreachable source"
    )
    assert output.cget("state") == "disabled"
    assert calls == [displayed]
    assert view.text.get("1.0", "end-1c") == displayed

    view.filter_var.set(".sources")
    _wait(lambda: view.snapshot is not None, root)
    assert view.file_action.cget("text") == "Paketquellen prüfen"
    assert view.file_action.instate(["!disabled"])


def test_fstab_report_context_menu_previews_and_copies_the_report(
    file_view, monkeypatch
):
    root, view, _files, handed, sounds = file_view
    report = "[W] simulated warning\npassword=fixture-only-private"
    monkeypatch.setattr(
        system_files,
        "check_fstab",
        lambda _: system_files.FstabCheck("warnings", report),
    )
    window = view.check_fstab()
    pane = window.winfo_children()[0]
    status, output_frame = pane.winfo_children()[1:3]
    _wait(lambda: status.cget("text") == "Prüfung meldet Warnungen.", root)
    output = output_frame.winfo_children()[0]
    menu = output.winfo_children()[0]

    def invoke_item(index):
        output.event_generate("<Button-3>", x=12, y=12)
        root.update()
        assert menu.winfo_ismapped()
        menu.invoke(index)
        menu.unpost()

    invoke_item(0)
    assert root.clipboard_get() == report
    assert output.get("sel.first", "sel.last") == report
    output.tag_remove("sel", "1.0", "end")
    output.tag_add("sel", "2.0", "2.end")
    invoke_item(1)
    assert root.clipboard_get() == "password=fixture-only-private"

    invoke_item(3)
    preview = output.winfo_children()[-1]
    assert preview.preview_text == "password=[REDACTED]"
    assert handed == []
    preview.hand_over()
    assert handed == [("Prüfbericht zu /etc/fstab", "password=[REDACTED]")]
    gc.collect()
    assert status.cget("text") == "Prüfung meldet Warnungen."

    output.tag_remove("sel", "1.0", "end")
    invoke_item(4)
    preview = output.winfo_children()[-1]
    assert "Prüfbericht zu /etc/fstab" in preview.preview_text
    assert "[W] simulated warning" in preview.preview_text
    assert "fixture-only-private" not in preview.preview_text
    assert root.clipboard_get() == "password=fixture-only-private"
    preview.hand_over()
    assert root.clipboard_get() == preview.preview_text
    assert len(handed) == 1
    assert sounds == ["click"] * 8


def test_apparmor_action_checks_the_selected_snapshot_and_skips_fragments(
    file_view, monkeypatch
):
    root, view, files, _, _ = file_view
    path = "/etc/apparmor.d/example"
    detail = "AppArmor parser error at line 1: syntax error"
    calls = []

    def check(text):
        assert threading.current_thread() is not threading.main_thread()
        calls.append(text)
        return system_files.FileCheck("errors", detail)

    monkeypatch.setattr(system_files, "check_apparmor_profile", check)
    view.tree.selection_set(path)
    _wait(lambda: view.selected_path == path and view.snapshot is not None, root)
    assert view.file_action.cget("text") == "Profil prüfen"
    assert view.file_action.instate(["!disabled"])
    displayed = files[path]
    files[path] = "# Changed outside the viewer\n"
    view.file_action.invoke()
    report = view.check_reports[path]
    assert view.check_apparmor() is report
    pane = report.winfo_children()[0]
    status, output_frame = pane.winfo_children()[1:3]
    _wait(lambda: status.cget("text") == "Prüfung meldet Fehler.", root)
    output = output_frame.winfo_children()[0]
    assert output.get("1.0", "end-1c") == detail
    assert output.bind("<Button-3>")
    assert calls == [displayed]
    report.destroy()
    assert path not in view.check_reports

    monkeypatch.setattr(
        system_files, "check_apparmor_profile", lambda _: system_files.FileCheck("ok")
    )
    report = view.check_apparmor()
    output = report.winfo_children()[0].winfo_children()[2].winfo_children()[0]
    clean = f"Der Parser meldet für {path} keine Fehler oder Warnungen."
    _wait(lambda: output.get("1.0", "end-1c") == clean, root)
    report.destroy()

    fragment = "/etc/apparmor.d/local/example"
    view.tree.selection_set(fragment)
    _wait(lambda: view.selected_path == fragment and view.snapshot is not None, root)
    assert view.file_action.instate(["disabled"])
    assert view.check_apparmor() is None


@pytest.mark.skipif(
    os.environ.get("NETMON_TEST_ISOLATED") != "1", reason="Private Xvfb"
)
@pytest.mark.parametrize(
    "close_mode,menu_open",
    [("button", False), ("button", True), ("window_manager", True), ("escape", False)],
)
def test_apparmor_report_closes_and_releases_its_menu(
    file_view, monkeypatch, close_mode, menu_open
):
    from tests.test_terminal_dock_v39 import PrivateKeys

    root, view, *_ = file_view
    monkeypatch.setattr(
        system_files, "check_apparmor_profile", lambda _: system_files.FileCheck("ok")
    )
    path = "/etc/apparmor.d/example"
    root.geometry("1000x700+40+40")
    view.frame.winfo_toplevel().bind(
        "<Button-1>", view.app._handle_app_click_for_context_menu, add="+"
    )
    view.tree.selection_set(path)
    _wait(lambda: view.selected_path == path and view.snapshot is not None, root)
    report = view.check_apparmor()
    report.geometry("+100+100")
    pane = report.winfo_children()[0]
    status, output_frame, close = pane.winfo_children()[1:]
    _wait(lambda: status.cget("text") == "Keine Fehler oder Warnungen gemeldet.", root)
    report.focus_force()
    root.update()
    if menu_open:
        output = output_frame.winfo_children()[0]
        output.event_generate("<Button-3>", x=12, y=12)
        _wait(output.winfo_children()[0].winfo_ismapped, root)

    mouse = PrivateKeys()
    try:
        if close_mode == "window_manager":
            root.tk.eval(report.protocol("WM_DELETE_WINDOW"))
        elif close_mode == "escape":
            output_frame.winfo_children()[0].focus_force()
            root.update()
            mouse.key("Escape")
            mouse.x.XFlush(mouse.display)
        else:
            mouse.click(close, x=close.winfo_width() // 2, y=close.winfo_height() // 2)
        _wait(lambda: not report.winfo_exists(), root)
        assert root.winfo_exists()
        assert path not in view.check_reports
        assert view.app.__dict__.get("_active_context_menu") is None
        assert view.app.__dict__.get("_active_context_menu_after_id") is None
        assert view.check_apparmor() is not report
    finally:
        mouse.close()


def test_apparmor_parser_checks_syntax_and_local_includes(tmp_path, monkeypatch):
    if not system_files.shutil.which(
        "apparmor_parser", path="/usr/sbin:/sbin:/usr/bin:/bin"
    ):
        pytest.skip("apparmor_parser is unavailable")
    monkeypatch.setattr(system_files, "APPARMOR_DIR", str(tmp_path))
    (tmp_path / "local").mkdir()
    fragment = tmp_path / "local/netmon-fixture"
    fragment.write_text("/tmp/netmon-fixture r,\n", encoding="utf-8")
    valid = "profile netmon-fixture {\n  #include <local/netmon-fixture>\n}\n"
    result = system_files.check_apparmor_profile(valid)
    if result.outcome == "warnings":
        assert result.detail.startswith(
            "Cache read/write disabled: interface file missing."
        ), result.detail
    else:
        assert result.outcome == "ok", result.detail
    result = system_files.check_apparmor_profile("profile netmon-fixture {\n")
    assert result.outcome == "errors" and "syntax error" in result.detail
    result = system_files.check_apparmor_profile(
        valid.replace("local/netmon-fixture", "local/netmon-missing")
    )
    assert result.outcome == "errors" and "local/netmon-missing" in result.detail


def test_apparmor_parser_uses_only_the_fixed_check_options(monkeypatch):
    sample = "# Fixture\n"

    def run(argv, **kwargs):
        assert argv == [
            "/usr/sbin/apparmor_parser",
            "--config-file=/dev/null",
            "--skip-kernel-load",
            "--skip-cache",
            "--jobs=0",
            "--base=/etc/apparmor.d",
            "--Include=/etc/apparmor.d",
        ]
        assert kwargs["input"] == sample
        assert kwargs["env"] == {"PATH": "/usr/sbin:/sbin:/usr/bin:/bin", "LC_ALL": "C"}
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(
        system_files.shutil, "which", lambda *a, **k: "/usr/sbin/apparmor_parser"
    )
    monkeypatch.setattr(system_files.subprocess, "run", run)
    assert system_files.check_apparmor_profile(sample).outcome == "timeout"
    monkeypatch.setattr(system_files.shutil, "which", lambda *a, **k: None)
    assert system_files.check_apparmor_profile(sample).outcome == "missing"


def test_apt_sources_action_checks_the_displayed_file_on_a_worker(
    file_view, monkeypatch
):
    root, view, files, _, _ = file_view
    path = "/etc/apt/sources.list.d/example.sources"
    calls = []

    def check(selected_path, text):
        assert threading.current_thread() is not threading.main_thread()
        calls.append((selected_path, text))
        return system_files.FileCheck("errors", "E: Malformed entry (Suite)")

    monkeypatch.setattr(system_files, "check_apt_sources", check)
    view.tree.selection_set(path)
    _wait(lambda: view.selected_path == path and view.snapshot is not None, root)
    assert view.file_action.cget("text") == "Paketquellen prüfen"
    displayed = files[path]
    files[path] = "# Changed outside the viewer\n"
    view.file_action.invoke()
    report = view.check_reports[path]
    pane = report.winfo_children()[0]
    status, output_frame = pane.winfo_children()[1:3]
    _wait(lambda: status.cget("text") == "Prüfung meldet Fehler.", root)
    output = output_frame.winfo_children()[0]
    assert output.get("1.0", "end-1c") == "E: Malformed entry (Suite)"
    assert output.bind("<Button-3>")
    assert calls == [(path, displayed)]


@pytest.mark.parametrize(
    "path,menu_label",
    [
        ("/etc/apparmor.d/example", "Profil prüfen"),
        ("/etc/apt/sources.list.d/example.sources", "Paketquellen prüfen"),
    ],
)
def test_system_file_tree_context_checks_the_right_clicked_file(
    file_view, monkeypatch, path, menu_label
):
    root, view, files, _handed, sounds = file_view
    calls = []

    def check(checked_path, text):
        calls.append((checked_path, text))
        return system_files.FileCheck("errors", "Fixture check result")

    monkeypatch.setattr(system_files, "check_apt_sources", check)
    monkeypatch.setattr(
        system_files,
        "check_apparmor_profile",
        lambda text: check("/etc/apparmor.d/example", text),
    )

    def right_click(row):
        view.tree.see(row)
        root.update()
        x, y, _, height = view.tree.bbox(row)
        view.tree.event_generate("<Button-3>", x=x + 30, y=y + height // 2)
        root.update()

    menu = view.tree_apt_menu if writer.is_deb822_source(path) else view.tree_edit_menu
    right_click("/etc/apparmor.d/local/example")
    assert not menu.winfo_ismapped()
    assert sounds == []
    right_click(path)
    assert menu.winfo_ismapped()
    assert menu.entrycget(0, "label") == menu_label
    assert view.selected_path == system_files.FSTAB
    assert calls == []
    menu.invoke(0)
    assert not menu.winfo_ismapped()
    assert view.app.__dict__.get("_active_context_menu") is None
    _wait(lambda: path in view.check_reports, root)
    pane = view.check_reports[path].winfo_children()[0]
    status = pane.winfo_children()[1]
    _wait(lambda: status.cget("text") == "Prüfung meldet Fehler.", root)
    assert view.selected_path == path
    assert view.tree.selection() == (path,)
    assert calls == [(path, files[path])]
    assert sounds == ["click", "click"]


_APT_LIST = "deb https://fixture.invalid/debian stable main\n"
_APT_SOURCES = "Types: deb\nURIs: https://fixture.invalid/debian\nSuites: stable\nComponents: main\n"


@pytest.mark.parametrize(
    "name,snapshot,outcome,message",
    [
        ("sources.list", _APT_LIST, "ok", ""),
        ("fixture.sources", _APT_SOURCES, "ok", ""),
        ("fixture.list", "deb https://fixture.invalid/debian\n", "errors", "(Suite)"),
        (
            "fixture.sources",
            _APT_SOURCES.replace("Suites: stable\n", ""),
            "errors",
            "(Suite)",
        ),
        ("fixture.sources", "Enabled: no\nTypes: deb\n", "ok", ""),
        ("fixture.list", _APT_LIST * 2, "warnings", "configured multiple times"),
        (
            "fixture.list",
            _APT_LIST.replace("deb ", "deb [signed-by=/etc/apt/keyrings/one.gpg] ")
            + _APT_LIST.replace("deb ", "deb [signed-by=/etc/apt/keyrings/two.gpg] "),
            "errors",
            "Conflicting values set for option Signed-By",
        ),
    ],
)
def test_apt_parser_checks_list_and_deb822_snapshots(name, snapshot, outcome, message):
    if not system_files.shutil.which("apt-get", path="/usr/bin:/bin"):
        pytest.skip("apt-get is unavailable")
    path = (
        f"/etc/apt/{name}"
        if name == "sources.list"
        else f"/etc/apt/sources.list.d/{name}"
    )
    result = system_files.check_apt_sources(path, snapshot)
    assert result.outcome == outcome, result.detail
    assert message in result.detail
    if message in ("(Suite)", "configured multiple times"):
        assert path in result.detail
    assert "netmon-apt-" not in result.detail


def test_apt_sources_check_does_not_inherit_config_and_handles_timeout(monkeypatch):
    path = "/etc/apt/sources.list.d/example.sources"
    tmp_dirs = []
    monkeypatch.setenv("APT_CONFIG", "/tmp/fixture-untrusted-config")

    def run(argv, **kwargs):
        config = Path(kwargs["env"]["APT_CONFIG"])
        directory = config.parent
        tmp_dirs.append(directory)
        parts = directory / "sources.list.d"
        snapshot = parts / "example.sources"
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert (
            config.read_text() == 'Dir::Etc::Parts "";\nDir::Etc::main "/dev/null";\n'
        )
        assert snapshot.read_text() == _APT_SOURCES
        assert not list((directory / "empty").iterdir())
        assert argv == [
            "/usr/bin/apt-get",
            "-o",
            f"Dir::Etc::sourcelist={directory / 'sources.list'}",
            "-o",
            f"Dir::Etc::sourceparts={parts}",
            "-o",
            f"Dir::State::lists={directory / 'empty'}",
            "-o",
            "Dir::Cache::pkgcache=",
            "-o",
            "Dir::Cache::srcpkgcache=",
            "indextargets",
        ]
        assert kwargs["stdout"] == subprocess.DEVNULL
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(
        system_files.shutil, "which", lambda *a, **k: "/usr/bin/apt-get"
    )
    monkeypatch.setattr(system_files.subprocess, "run", run)
    assert system_files.check_apt_sources(path, _APT_SOURCES).outcome == "timeout"
    assert len(tmp_dirs) == 1 and not tmp_dirs[0].exists()
    monkeypatch.setattr(system_files.shutil, "which", lambda *a, **k: None)
    assert system_files.check_apt_sources(path, _APT_SOURCES).outcome == "missing"


def test_apt_toggle_preserves_fields_and_changes_all_stanzas():
    first = "# Local comment\r\n" + _APT_SOURCES.replace("\n", "\r\n")
    second = _APT_SOURCES + "eNaBlEd: no\nSigned-By:\n  embedded key\n"
    original = first + "\r\n" + second
    disabled = writer.apt_enabled_draft(original, False)
    assert disabled == "Enabled: no\r\n" + original
    assert writer.apt_enabled_draft(disabled, False) == disabled
    assert writer.apt_enabled_draft(disabled, True) == (
        "Enabled: yes\r\n"
        + first
        + "\r\n"
        + second.replace("eNaBlEd: no", "eNaBlEd: yes")
    )
    with pytest.raises(ValueError):
        writer.apt_enabled_draft(first + "Enabled: yes\nEnabled: no\n", False)


def test_apt_review_checks_conflicts_with_other_files(monkeypatch):
    if not system_files.shutil.which("apt-get", path="/usr/bin:/bin"):
        pytest.skip("apt-get is unavailable")
    path = f"{writer.APT_SOURCE_PARTS}/example.sources"
    original = _APT_SOURCES + "Enabled: no\nSigned-By: /etc/apt/keyrings/one.gpg\n"
    sources = {
        path: original.encode(),
        writer.APT_SOURCE_LIST: _APT_LIST.replace(
            "deb ", "deb [signed-by=/etc/apt/keyrings/two.gpg] "
        ).encode(),
    }
    monkeypatch.setattr(writer, "require_local_apt_source", lambda _: None)
    monkeypatch.setattr(writer, "read_apt_source_set", lambda: sources.copy())
    result = system_files.review_apt_source_change(path, original, True)
    assert result.outcome == "errors"
    assert "Conflicting values set for option Signed-By" in result.detail
    assert result.digest == writer.apt_source_set_digest(sources)
    with pytest.raises(ValueError, match="inzwischen"):
        system_files.review_apt_source_change(path, original + "# stale\n", True)


def test_apt_helper_only_commits_a_reviewed_toggle(tmp_path, monkeypatch):
    path = f"{writer.APT_SOURCE_PARTS}/example.sources"
    original = _APT_SOURCES.encode()
    local_file = tmp_path / "example.sources"
    local_file.write_bytes(original)
    local_file.chmod(0o640)
    sources = {path: original, writer.APT_SOURCE_LIST: _APT_LIST.encode()}
    digest = writer.apt_source_set_digest(sources)
    monkeypatch.setattr(writer, "require_local_apt_source", lambda _: None)
    monkeypatch.setattr(writer, "read_apt_source_set", lambda: sources.copy())
    monkeypatch.setattr(
        writer,
        "_destination_directory",
        lambda _: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY),
    )
    monkeypatch.setattr(os, "fchown", lambda *args: None)
    real_fstat = os.fstat

    def root_owned(fd):
        info = real_fstat(fd)
        return SimpleNamespace(
            st_uid=0,
            **{
                field: getattr(info, field)
                for field in (
                    "st_mode",
                    "st_nlink",
                    "st_gid",
                    "st_ino",
                    "st_ctime_ns",
                )
            },
        )

    monkeypatch.setattr(os, "fstat", root_owned)
    draft = writer.apt_enabled_draft(_APT_SOURCES, False).encode()
    with pytest.raises(ValueError, match="Nur das Aktivieren"):
        writer._replace_apt_source(
            path, draft.replace(b"fixture.invalid", b"other.invalid"), digest
        )
    sources[writer.APT_SOURCE_LIST] += b"# Another editor updated this file\n"
    with pytest.raises(ValueError, match="inzwischen"):
        writer._replace_apt_source(path, draft, digest)
    assert list(tmp_path.iterdir()) == [local_file]
    reviewed_digest = writer.apt_source_set_digest(sources)
    backup = (
        tmp_path / Path(writer._replace_apt_source(path, draft, reviewed_digest)).name
    )
    assert local_file.read_bytes() == draft
    assert backup.read_bytes() == original
    assert stat.S_IMODE(local_file.stat().st_mode) == 0o640
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600


def test_apt_save_command_binds_the_source_set_and_draft(monkeypatch):
    path = f"{writer.APT_SOURCE_PARTS}/example.sources"
    digest = "a" * 64
    draft = "Enabled: no\n" + _APT_SOURCES
    calls = []
    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(writer, "_replace_apt_source", lambda *args: calls.append(args))

    def runner(argv, *, input_text, timeout):
        arguments = argv[6:]
        assert arguments[:2] == [path, digest]
        payload = input_text.encode()
        monkeypatch.setattr(
            writer.sys,
            "stdin",
            SimpleNamespace(buffer=io.BytesIO(payload + b"# edited")),
        )
        assert writer.main(arguments) == 1
        assert calls == []
        monkeypatch.setattr(
            writer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(payload))
        )
        return writer.main(arguments), ""

    assert writer.save_apt_source_config(path, draft, digest, run_cmd_fn=runner)[0] == 0
    assert calls == [(path, draft.encode(), digest)]


def test_apt_toggle_preview_requires_click_before_saving(file_view, monkeypatch):
    root, view, files, _, _ = file_view
    path = f"{writer.APT_SOURCE_PARTS}/example.sources"
    files[path] = _APT_SOURCES
    draft = "Enabled: no\n" + _APT_SOURCES
    calls = []
    monkeypatch.setattr(
        system_files,
        "review_apt_source_change",
        lambda *a: system_files.AptSourceReview("ok", draft=draft, digest="a" * 64),
    )
    monkeypatch.setattr(writer, "hosts_save_available", lambda: True)
    view.app.ensure_sudo_session = lambda path: calls.append(path) or True

    def save(path, draft, digest):
        calls.append((path, draft, digest))
        files[path] = draft
        return 0, "/fixture/backup.bak"

    monkeypatch.setattr(writer, "save_apt_source_config", save)
    view.tree.see(path)
    root.update()
    x, y, _, _ = view.tree.bbox(path)
    view.tree.event_generate("<Button-3>", x=x + 25, y=y + 5)
    root.update()
    menu = view.tree_apt_menu
    assert menu.entrycget(2, "label") == "Alle Quellen in der Datei deaktivieren"
    menu.invoke(2)
    key = (path, menu.entrycget(2, "label"))
    _wait(lambda: key in view.check_reports, root)
    pane = view.check_reports[key].winfo_children()[0]
    _, status, output_frame, _, save_button = pane.winfo_children()
    _wait(lambda: save_button.instate(["!disabled"]), root)
    assert "+Enabled: no" in output_frame.winfo_children()[0].get("1.0", "end-1c")
    assert calls == []
    save_button.invoke()
    _wait(lambda: "/fixture/backup.bak" in status.cget("text"), root)
    _wait(lambda: view.snapshot is not None and view.snapshot.text == draft, root)
    assert calls == [path, (path, draft, "a" * 64)]


def test_findmnt_classifies_warnings_and_parse_errors(tmp_path):
    if not system_files.shutil.which("findmnt", path="/usr/bin:/bin"):
        pytest.skip("findmnt is unavailable")
    clean = system_files.check_fstab("proc /proc proc defaults 0 0\n")
    assert clean.outcome == "ok"
    assert clean.syntax_errors == 0
    warning = system_files.check_fstab(
        f"proc {tmp_path / 'missing-target'} proc defaults,noauto 0 0\n"
    )
    assert warning.outcome == "warnings" and "[W]" in warning.detail
    error = system_files.check_fstab("bad-line\n")
    assert error.outcome == "errors"
    assert error.syntax_errors == 1
    assert "/etc/fstab: parse error at line 1" in error.detail


def test_fstab_report_explains_only_verified_findings(monkeypatch):
    monkeypatch.setattr(system_files, "_read_mountinfo", lambda: {})
    snapshot = (
        "/dev/example-root / ext4 defaults 0 1\n"
        "/dev/example-efi /boot/efi vfat defaults 0 2\n"
        "/swapfile none swap sw 0 0\n"
        "UUID=1111-2222 /mnt/backup auto noauto,nofail,x-gvfs-show 0 0\n"
    )
    report = (
        "/\n"
        "   [W] cannot detect on-disk filesystem type (Permission denied)\n"
        "/boot/efi\n"
        "   [W] cannot detect on-disk filesystem type (Permission denied)\n"
        "none\n"
        "   [W] non-bind mount source /swapfile is a directory or regular file\n"
        "   [W] cannot detect on-disk filesystem type (Permission denied)\n"
        "/mnt/backup\n"
        "   [W] unreachable source: /dev/disk/by-uuid/1111-2222: No such file or directory\n"
        "   [E] cannot detect on-disk filesystem type (No such file or directory)\n\n"
        "0 parse errors, 1 error, 5 warnings"
    )
    monkeypatch.setattr(
        system_files, "active_swap_files", lambda: {"/swapfile", "/other"}
    )
    result = system_files._describe_fstab_check(snapshot, "errors", report)
    assert result == system_files.FstabCheck(
        "warnings", report, 0, ("/mnt/backup",), ("/", "/boot/efi"), ("/swapfile",)
    )

    def unreadable_swap_table():
        raise PermissionError

    monkeypatch.setattr(system_files, "active_swap_files", unreadable_swap_table)
    result = system_files._describe_fstab_check(snapshot, "errors", report)
    assert result.outcome == "warnings"
    assert result.active_swaps == ()


@pytest.mark.parametrize(
    "mount_rows,device,fstab_type,extra_error,expected",
    [
        ([("8:1", "ext4")], "8:1", "auto", "", "warnings"),
        ([], "8:1", "auto", "", "errors"),
        ([("8:1", "ext4")], "8:2", "auto", "", "errors"),
        ([("8:1", "ext4"), ("8:2", "ext4")], "8:1", "auto", "", "errors"),
        ([("8:1", "ext4")], "8:1", "vfat", "", "errors"),
        ([("8:1", "ext4")], "8:1", "auto", "   [E] another error\n", "errors"),
    ],
)
def test_fstab_report_uses_only_the_exact_matching_live_mount(
    monkeypatch, mount_rows, device, fstab_type, extra_error, expected
):
    monkeypatch.setattr(
        system_files, "_read_mountinfo", lambda: {"/mnt/disk": mount_rows}
    )
    monkeypatch.setattr(system_files, "_block_device_number", lambda _: device)
    snapshot = f"/dev/disk/by-uuid/1111-2222 /mnt/disk {fstab_type} noauto,nofail 0 0\n"
    count = "2 errors" if extra_error else "1 error"
    detail = (
        "/mnt/disk\n"
        "   [E] cannot detect on-disk filesystem type (Permission denied)\n"
        f"{extra_error}\n0 parse errors, {count}, 0 warnings"
    )
    result = system_files._describe_fstab_check(snapshot, "errors", detail)
    assert result.outcome == expected
    assert result.detail == detail
    if expected == "warnings" or extra_error:
        assert result.mounted_types == (("/mnt/disk", "ext4"),)
        assert result.type_unavailable == ()
    else:
        assert result.mounted_types == ()
        assert result.type_unavailable == ("/mnt/disk",)


@pytest.mark.parametrize(
    "udev_uuid,expected", [("1111-2222", "warnings"), ("3333-4444", "errors")]
)
def test_fstab_report_can_match_the_mount_via_udev_without_device_access(
    monkeypatch, udev_uuid, expected
):
    def open_mountinfo(path, mode, **_):
        assert path == "/proc/self/mountinfo"
        assert mode == "r"
        return io.StringIO("36 35 252:0 / /mnt/disk rw shared:1 - ext4 /dev/dm-0 rw\n")

    def run(argv, **kwargs):
        assert argv == [
            "/usr/bin/udevadm",
            "info",
            "--query=property",
            "--path=/sys/dev/block/252:0",
        ]
        assert 0 < kwargs["timeout"] <= 2
        return subprocess.CompletedProcess(
            argv, 0, f"ID_FS_UUID={udev_uuid}\nID_FS_TYPE=ext4\n", ""
        )

    monkeypatch.setattr(system_files, "open", open_mountinfo, raising=False)
    monkeypatch.setattr(system_files, "_block_device_number", lambda _: None)
    monkeypatch.setattr(
        system_files.shutil, "which", lambda tool, **_: f"/usr/bin/{tool}"
    )
    monkeypatch.setattr(system_files.subprocess, "run", run)
    result = system_files._describe_fstab_check(
        'UUID="1111-2222" /mnt/disk auto noauto,nofail 0 0\n',
        "errors",
        "/mnt/disk\n"
        "   [E] cannot detect on-disk filesystem type (Permission denied)\n"
        "\n0 parse errors, 1 error, 0 warnings",
    )
    assert result.outcome == expected
    expected_mounts = (("/mnt/disk", "ext4"),) if expected == "warnings" else ()
    assert result.mounted_types == expected_mounts


@pytest.mark.parametrize(
    "target,source,options,duplicate,extra,footer",
    [
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "defaults",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "noauto",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "nofail",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "noauto,nofail,x-systemd.automount",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/boot",
            "UUID=1111-2222",
            "noauto,nofail",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=3333-4444",
            "noauto,nofail",
            False,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "noauto,nofail",
            True,
            "",
            "0 parse errors, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "noauto,nofail",
            False,
            "",
            "1 parse error, 1 error",
        ),
        (
            "/mnt/backup",
            "UUID=1111-2222",
            "noauto,nofail",
            False,
            "   [E] another error\n",
            "0 parse errors, 2 errors",
        ),
    ],
)
def test_fstab_report_keeps_errors_when_the_optional_case_is_not_the_only_error(
    target, source, options, duplicate, extra, footer
):
    entry = f"{source} {target} auto {options} 0 0\n"
    snapshot = entry * (2 if duplicate else 1)
    report = (
        f"{target}\n"
        "   [W] unreachable source: /dev/disk/by-uuid/1111-2222: No such file or directory\n"
        "   [E] cannot detect on-disk filesystem type (No such file or directory)\n"
        f"{extra}\n{footer}, 1 warning"
    )
    result = system_files._describe_fstab_check(snapshot, "errors", report)
    assert result.outcome == "errors"
    assert result.detail == report


def test_fstab_check_uses_private_exact_input_and_handles_timeout(monkeypatch):
    paths = []
    content = "# Prüffassung\nproc /proc proc defaults 0 0\n"

    def run(argv, **kwargs):
        assert argv[:3] == ["/usr/bin/findmnt", "--verify", "--tab-file"]
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
        snapshot = Path(argv[3])
        paths.append(snapshot)
        assert snapshot.read_bytes() == content.encode()
        assert stat.S_IMODE(snapshot.stat().st_mode) == 0o600
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(
        system_files.shutil, "which", lambda *a, **k: "/usr/bin/findmnt"
    )
    monkeypatch.setattr(system_files.subprocess, "run", run)
    assert system_files.check_fstab(content).outcome == "timeout"
    assert len(paths) == 1 and not paths[0].exists()
    monkeypatch.setattr(system_files.shutil, "which", lambda *a, **k: None)
    assert system_files.check_fstab(content).outcome == "missing"


def test_system_file_context_menu_reuses_reviewed_actions(file_view, monkeypatch):
    root, view, files, handed, sounds = file_view
    path = "/etc/apt/sources.list.d/example.sources"
    view.tree.selection_set(path)
    _wait(lambda: view.selected_path == path and view.snapshot is not None, root)
    view.search_var.set("Suites")
    menu = view.text_actions.menu

    def open_menu():
        view.text.event_generate("<Button-3>", x=12, y=12)
        root.update()
        assert menu.winfo_ismapped()

    open_menu()
    assert menu.entrycget(1, "state") == "disabled"
    menu.invoke(0)
    menu.unpost()
    assert root.clipboard_get() == files[path]
    assert view.text.get("sel.first", "sel.last") == files[path]
    assert sounds == ["click", "click"]

    view.text.tag_remove("sel", "1.0", "end")
    view.text.tag_add("sel", "2.0", "2.end")
    open_menu()
    menu.invoke(3)
    menu.unpost()
    preview = view.text_actions.preview
    assert handed == [] and root.clipboard_get() == files[path]
    assert preview.preview_text == "password=[REDACTED]"
    preview.hand_over()
    assert handed == [(f"Systemdatei: {path}", "password=[REDACTED]")]

    view.text.tag_remove("sel", "1.0", "end")
    open_menu()
    menu.invoke(4)
    menu.unpost()
    preview = view.text_actions.preview
    prompt = preview.preview_text
    assert (
        path in prompt
        and "password=[REDACTED]" in prompt
        and "Suites: stable" in prompt
    )
    assert "fixture-only-private" not in prompt
    assert root.clipboard_get() == files[path]
    preview.hand_over()
    assert root.clipboard_get() == prompt and len(handed) == 1

    monkeypatch.setattr(system_logs, "CHAD_MAX_LINES", 1)
    preview = view.text_actions.open_preview()
    assert preview.preview_text == files[path].splitlines(keepends=True)[0]


def test_discovers_distro_specific_apt_and_apparmor_files(tmp_path):
    paths = (
        "/etc/apt/sources.list.d/ubuntu.sources",
        "/etc/apt/sources.list.d/official-package-repositories.list",
        "/etc/apt/sources.list.d/example.list.disabled",
        "/etc/apparmor.d/usr.sbin.example",
        "/etc/apparmor.d/local/usr.sbin.example",
        "/etc/apparmor.d/abstractions/base",
    )
    for name in paths:
        file = tmp_path / name.lstrip("/")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("example\n")
    apt = tmp_path / "etc/apt/sources.list.d"
    (apt / "arbitrary.sources").symlink_to("/etc/shadow")
    catalog = system_files.discover_files(root=tmp_path)
    assert catalog["packages"] == ["/etc/apt/sources.list", paths[1], paths[0]]
    assert catalog["apparmor"] == list(paths[3:5])


def test_resolver_only_reads_a_recognised_text_target(tmp_path):
    etc = tmp_path / "etc"
    etc.mkdir()
    resolver = etc / "resolv.conf"
    target = tmp_path / "run/systemd/resolve/stub-resolv.conf"
    target.parent.mkdir(parents=True)
    target.write_text("nameserver 127.0.0.53\n")
    resolver.symlink_to("../run/systemd/resolve/stub-resolv.conf")
    snapshot = system_files.read_file("/etc/resolv.conf", root=tmp_path)
    assert snapshot.text == target.read_text()
    assert snapshot.link == "../run/systemd/resolve/stub-resolv.conf"
    resolver.unlink()
    resolver.symlink_to("/etc/shadow")
    assert system_files.read_file("/etc/resolv.conf", root=tmp_path) == (
        system_files.FileSnapshot(None, "/etc/shadow")
    )


def test_optional_system_files_only_include_known_paths(tmp_path):
    paths = (
        system_files.CRYPTTAB,
        "/etc/nftables.conf",
        "/etc/iptables/rules.v6",
        "/etc/ufw/before.rules",
        "/etc/ufw/other.rules",
    )
    for path in paths:
        file = tmp_path / path.lstrip("/")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    catalog = system_files.discover_files(root=tmp_path)
    assert catalog["mounts"] == [system_files.FSTAB, system_files.CRYPTTAB]
    assert system_files.NSSWITCH in catalog["network"]
    assert catalog["firewall"] == list(paths[1:4])


def test_privileged_system_file_reader_uses_only_known_regular_files(
    tmp_path, monkeypatch, capsys
):
    path = "/etc/ufw/user.rules"
    regular = tmp_path / Path(path).name
    content = "# Report\n\n  rule text\n"
    regular.write_text(content)
    regular.chmod(0o640)
    (tmp_path / "before.rules").symlink_to(regular)
    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    accessed = []

    def destination(requested):
        accessed.append(requested)
        return os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)

    def root_owned_file(fd):
        info = real_fstat(fd)
        return SimpleNamespace(st_uid=0, st_mode=info.st_mode, st_nlink=info.st_nlink)

    real_fstat = os.fstat
    monkeypatch.setattr(writer, "_destination_directory", destination)
    monkeypatch.setattr(os, "fstat", root_owned_file)
    assert writer.main(["--read", "/etc/shadow"]) == 1
    assert accessed == []
    assert writer.main(["--read", "/etc/ufw/before.rules"]) == 1
    capsys.readouterr()

    def runner(args, *, timeout, input_text):
        assert args[6:] == ["--read", path]
        assert timeout == 10 and input_text == ""
        rc = writer.main(args[6:])
        return rc, capsys.readouterr().out

    assert writer.read_system_config(path, run_cmd_fn=runner) == content
    assert regular.read_text() == content


def test_nsswitch_hosts_rule_is_highlighted_and_available_for_chad(file_view):
    root, view, files, handed, _sounds = file_view
    path = system_files.NSSWITCH
    view.tree.selection_set(path)
    _wait(lambda: view.snapshot is not None and view.selected_path == path, root)
    assert view.text.get("1.0", "end-1c") == files[path]
    start, end = view.text.tag_ranges("nsswitch_hosts")
    assert view.text.get(start, end) == "hosts: files dns"
    view.text.tag_add("sel", start, end)
    preview = view.text_actions.open_preview()
    assert preview.preview_text == "hosts: files dns"
    assert handed == []
    preview.hand_over()
    assert handed == [(f"Systemdatei: {path}", "hosts: files dns")]


def test_protected_firewall_file_is_read_only_after_explicit_action(
    file_view, monkeypatch
):
    root, view, files, _handed, _sounds = file_view
    path = "/etc/ufw/user.rules"
    calls = []

    def read(selected):
        if selected == path:
            raise PermissionError("fixture permission denied")
        return system_files.FileSnapshot(files[selected])

    def read_as_admin(selected):
        calls.append(("read", selected))
        return files[selected]

    monkeypatch.setattr(system_files, "read_file", read)
    monkeypatch.setattr(writer, "hosts_save_available", lambda: True)
    monkeypatch.setattr(writer, "read_system_config", read_as_admin)
    view.app.ensure_sudo_session = (
        lambda selected: calls.append(("auth", selected)) or True
    )

    view.tree.selection_set(path)
    _wait(lambda: view.file_action.cget("text") == "Mit Adminrechten lesen", root)
    assert calls == []
    view.file_action.invoke()
    _wait(lambda: view.snapshot is not None, root)
    assert calls == [("auth", path), ("read", path)]
    assert view.text.get("1.0", "end-1c") == files[path]
    assert view.text.cget("state") == "disabled"
    assert not view.file_edit_button.winfo_ismapped()


@pytest.mark.parametrize(
    ("content", "outcome", "detail"),
    [
        ("127.0.0.1 localhost\n::1 localhost\n", "ok", ""),
        ("# comment\ninvalid localhost\n", "errors", "Zeile 2:"),
    ],
)
def test_hosts_check_uses_the_editor_validation(content, outcome, detail):
    result = system_files.check_hosts(content)
    assert result.outcome == outcome
    assert result.detail.startswith(detail)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (
            "nameserver 127.0.0.53 # local stub\nnameserver fe80::1%eth0\n",
            system_files.FileCheck("ok"),
        ),
        (
            "# comment\nnameserver bad.example\n"
            "  nameserver 192.0.2.1\nnameserver\n",
            system_files.FileCheck("errors", "2, 3, 4"),
        ),
        (
            "; nameserver 127.0.0.53\nsearch example\n",
            system_files.FileCheck("warnings"),
        ),
    ],
)
def test_resolv_check_accepts_ip_literals_and_reports_bad_lines(content, expected):
    assert system_files.check_resolv_nameservers(content) == expected


@pytest.mark.parametrize("draft", ["not-an-ip localhost", "127.0.0.1", "::1 bad#\0"])
def test_invalid_hosts_entries_are_rejected(draft):
    with pytest.raises(ValueError):
        writer.validate_hosts(draft)


def test_hosts_helper_checks_both_the_original_and_reviewed_payload(monkeypatch):
    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    writes = []
    monkeypatch.setattr(writer, "_replace_hosts", lambda *args: writes.append(args))
    original_digest = hashlib.sha256(b"127.0.0.1 localhost\n").hexdigest()
    draft = "127.0.0.1 localhost\n::1 ip6-localhost\n"

    def runner(args, *, input_text, timeout):
        assert args[:6] == [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-c",
            writer.BOOTSTRAP,
        ]
        assert args[6:8] == [writer.HOSTS, original_digest]
        monkeypatch.setattr(
            writer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"tampered"))
        )
        assert writer.main(args[6:]) == 1
        assert writes == []
        monkeypatch.setattr(
            writer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(input_text.encode()))
        )
        assert writer.main([writer.HOSTS, args[-1]]) == 1
        return writer.main(args[6:]), ""

    assert writer.save_hosts_config(draft, original_digest, run_cmd_fn=runner)[0] == 0
    assert writes == [(draft.encode(), original_digest)]


@pytest.mark.parametrize("kind", ["hosts", "apparmor"])
def test_reviewed_write_preserves_mode_and_requires_unchanged_original(
    tmp_path, monkeypatch, kind
):
    original = b"127.0.0.1 localhost\n"
    draft = b"127.0.0.1 localhost\n::1 ip6-localhost\n"
    path = writer.HOSTS
    if kind == "apparmor":
        path = f"{writer.APPARMOR_DIR}/netmon-fixture"
        original = b"profile netmon-fixture {\n}\n"
        draft = b"profile netmon-fixture {\n  /tmp/netmon-fixture r,\n}\n"
    destination = tmp_path / Path(path).name
    destination.write_bytes(original)
    destination.chmod(0o640)
    monkeypatch.setattr(
        writer,
        "_destination_directory",
        lambda path: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY),
    )
    real_fstat = os.fstat
    inode = destination.stat().st_ino

    def root_owned_original(fd):
        info = real_fstat(fd)
        if info.st_ino != inode:
            return info
        return SimpleNamespace(
            st_uid=0,
            **{
                field: getattr(info, field)
                for field in (
                    "st_mode",
                    "st_nlink",
                    "st_gid",
                    "st_ino",
                    "st_ctime_ns",
                )
            },
        )

    monkeypatch.setattr(os, "fstat", root_owned_original)
    monkeypatch.setattr(os, "fchown", lambda *args: None)
    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(writer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(draft)))
    digest = hashlib.sha256(original).hexdigest()
    draft_digest = hashlib.sha256(draft).hexdigest()
    assert writer.main([path, digest, "0" * 64]) == 1
    writer.sys.stdin.buffer.seek(0)
    assert writer.main([path, "0" * 64, draft_digest]) == 1
    assert list(tmp_path.iterdir()) == [destination]

    writer.sys.stdin.buffer.seek(0)
    assert writer.main([path, digest, draft_digest]) == 0
    (backup,) = tmp_path.glob(f".netmon-{kind}-*.bak")
    assert destination.read_bytes() == draft
    assert backup.read_bytes() == original
    assert stat.S_IMODE(destination.stat().st_mode) == 0o640
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    "path",
    ["/etc/apparmor.d/local/example", "/etc/apparmor.d/../hosts", "/etc/hosts"],
)
def test_apparmor_save_rejects_paths_outside_top_level_profiles(path):
    with pytest.raises(ValueError, match="Profilpfad"):
        writer.save_apparmor_profile(path, "profile example {}\n", "0" * 64)


def test_apparmor_editor_checks_before_saving(file_view, monkeypatch):
    root, view, files, _handed, _sounds = file_view
    path = "/etc/apparmor.d/example"
    original = files[path]
    draft = original.replace("r,", "rw,")
    invalid = "profile example {\n"
    checked, saves = [], []

    def read(selected_path):
        return system_files.FileSnapshot(
            files[selected_path], apparmor_editable=selected_path == path
        )

    def check(content):
        checked.append(content)
        if content == invalid:
            return system_files.FileCheck("errors", "syntax error")
        return system_files.FileCheck("warnings", "fixture warning")

    def save(selected_path, content, digest):
        saves.append((selected_path, content, digest))
        return 0, "/etc/apparmor.d/.netmon-apparmor-fixture.bak"

    monkeypatch.setattr(system_files, "read_file", read)
    monkeypatch.setattr(system_files, "check_apparmor_profile", check)
    monkeypatch.setattr(writer, "save_apparmor_profile", save)
    monkeypatch.setattr(writer, "hosts_save_available", lambda: True)
    view.app.ensure_sudo_session = lambda selected_path: selected_path == path

    assert not view.file_edit_button.winfo_ismapped()
    view.tree.see(path)
    root.update()
    x, y, _, height = view.tree.bbox(path)
    view.tree.event_generate("<Button-3>", x=x + 30, y=y + height // 2)
    root.update()
    assert view.tree_edit_menu.entrycget(1, "label") == "Bearbeiten"
    view.tree_edit_menu.invoke(1)
    _wait(lambda: path in view.editors, root)
    window = view.editors[path]
    assert view.file_edit_button.winfo_ismapped()
    assert view.file_edit_button.instate(["!disabled"])
    assert view.file_edit_button.winfo_x() < view.file_action.winfo_x()
    assert view.file_edit_button.winfo_y() == view.file_action.winfo_y()
    view.file_edit_button.invoke()
    assert view.editors[path] is window
    pane = window.winfo_children()[0]
    text = pane.winfo_children()[1].winfo_children()[0]
    back, confirm = pane.winfo_children()[-1].winfo_children()
    assert text.get("1.0", "end-1c") == original

    text.replace("1.0", "end", invalid)
    confirm.invoke()
    _wait(lambda: confirm.cget("text") == "Speichern", root)
    assert confirm.instate(["disabled"])
    assert "syntax error" in text.get("1.0", "end-1c")
    assert saves == []

    back.invoke()
    text.replace("1.0", "end", draft)
    confirm.invoke()
    _wait(lambda: confirm.cget("text") == "Speichern", root)
    assert confirm.instate(["!disabled"])
    assert "fixture warning" in text.get("1.0", "end-1c")
    assert saves == []
    confirm.invoke()
    _wait(lambda: path not in view.editors, root)
    assert checked == [invalid, draft]
    assert saves == [(path, draft, hashlib.sha256(original.encode()).hexdigest())]
    assert view.text.get("1.0", "end-1c") == draft


def test_apparmor_draft_context_menu_pastes_and_previews_selected_text(
    file_view, monkeypatch
):
    root, view, files, handed, _sounds = file_view
    path = "/etc/apparmor.d/example"
    fragment = "/etc/apparmor.d/local/example"
    draft = "profile example { /tmp/fixture r, }\n# password=fixture-private\n"
    monkeypatch.setattr(
        system_files,
        "read_file",
        lambda selected_path: system_files.FileSnapshot(
            files[selected_path], apparmor_editable=selected_path == path
        ),
    )
    monkeypatch.setattr(
        system_files,
        "check_apparmor_profile",
        lambda _text: system_files.FileCheck("ok"),
    )

    view.tree.selection_set(path)
    _wait(lambda: view.file_edit_button.instate(["!disabled"]), root)
    view.file_edit_button.invoke()
    pane = view.editors[path].winfo_children()[0]
    text = pane.winfo_children()[1].winfo_children()[0]
    menu = text.winfo_children()[0]

    def invoke_item(item, *, state="normal"):
        text.event_generate("<Button-3>", x=12, y=12)
        root.update()
        assert menu.winfo_ismapped()
        assert menu.entrycget(item, "state") == state
        menu.invoke(item)
        menu.unpost()

    root.clipboard_clear()
    root.clipboard_append(draft)
    text.tag_add("sel", "1.0", "end-1c")
    invoke_item("Einfügen")
    assert text.get("1.0", "end-1c") == draft
    invoke_item("Alles kopieren")
    assert root.clipboard_get() == draft
    text.tag_remove("sel", "1.0", "end")
    text.tag_add("sel", "2.0", "2.end")
    invoke_item("Auswahl kopieren")
    assert root.clipboard_get() == "# password=fixture-private"

    invoke_item("Mit Chad analysieren…")
    preview = text.winfo_children()[-1]
    assert preview.preview_text == "# password=[REDACTED]"
    assert handed == []
    preview.hand_over()
    assert handed == [(f"Entwurf zu {path}", "# password=[REDACTED]")]

    invoke_item("Prompt für externen Chat…")
    preview = text.winfo_children()[-1]
    assert f"Entwurf zu {path}" in preview.preview_text
    assert "password=[REDACTED]" in preview.preview_text
    assert "fixture-private" not in preview.preview_text
    assert "profile example" not in preview.preview_text
    preview.hand_over()
    assert root.clipboard_get() == preview.preview_text

    confirm = pane.winfo_children()[-1].winfo_children()[-1]
    confirm.invoke()
    _wait(lambda: confirm.cget("text") == "Speichern", root)
    diff = text.get("1.0", "end-1c")
    invoke_item("Einfügen", state="disabled")
    assert text.get("1.0", "end-1c") == diff

    view.tree.selection_set(fragment)
    _wait(lambda: view.selected_path == fragment, root)
    assert not view.file_edit_button.winfo_ismapped()


@pytest.mark.parametrize(
    ("path", "check_label", "edit_label", "report"),
    [
        (
            writer.HOSTS,
            "hosts prüfen",
            "Bearbeiten",
            "Die Einträge entsprechen dem hosts-Dateiformat.",
        ),
        (
            system_files.RESOLV_CONF,
            "resolv.conf prüfen",
            "DNS bearbeiten",
            "Die Nameserver-Einträge enthalten gültige IP-Adressen.",
        ),
    ],
)
def test_network_files_have_check_and_edit_actions(
    file_view, monkeypatch, path, check_label, edit_label, report
):
    root, view, files, _handed, _sounds = file_view
    dns_opened = []
    view.app.open_dns_profile_manager = lambda: dns_opened.append(True)
    monkeypatch.setattr(
        system_files,
        "read_file",
        lambda selected_path: system_files.FileSnapshot(
            files[selected_path],
            link=(
                "../run/systemd/resolve/stub-resolv.conf"
                if selected_path == system_files.RESOLV_CONF
                else None
            ),
            hosts_editable=selected_path == writer.HOSTS,
        ),
    )

    def choose_menu_entry(index):
        view.tree.see(path)
        root.update()
        x, y, _, height = view.tree.bbox(path)
        view.tree.event_generate("<Button-3>", x=x + 30, y=y + height // 2)
        root.update()
        menu = view.tree_edit_menu
        assert menu.winfo_ismapped()
        assert menu.entrycget(0, "label") == check_label
        assert menu.entrycget(1, "label") == edit_label
        menu.invoke(index)

    assert view.selected_path == system_files.FSTAB
    choose_menu_entry(0)
    _wait(lambda: path in view.check_reports, root)
    window = view.check_reports[path]
    output = window.winfo_children()[0].winfo_children()[2].winfo_children()[0]
    _wait(lambda: output.get("1.0", "end-1c") == report, root)
    assert view.file_action.cget("text") == check_label
    assert view.file_edit_button.cget("text") == edit_label
    assert view.file_edit_button.winfo_x() < view.file_action.winfo_x()
    assert view.file_action.instate(["!disabled"])
    assert view.file_edit_button.instate(["!disabled"])
    assert view.file_action.invoke() == str(window)

    choose_menu_entry(1)
    if path == writer.HOSTS:
        assert path in view.editors
        assert not dns_opened
    else:
        view.file_edit_button.invoke()
        assert dns_opened == [True, True]
        assert path not in view.editors


def test_hosts_editor_reviews_then_submits_exact_draft(monkeypatch):
    root = tk.Tk()
    try:
        original = "127.0.0.1 localhost\n"
        draft = original + "::1 ip6-localhost\n"
        calls = []
        root.tr = lambda _key, fallback: fallback
        root.ensure_sudo_session = lambda path: calls.append(path) or True
        monkeypatch.setattr(
            system_files,
            "discover_files",
            lambda: system_files.FIXED_FILES,
        )
        monkeypatch.setattr(
            system_files,
            "read_file",
            lambda path: system_files.FileSnapshot(
                original,
                hosts_editable=(path == writer.HOSTS),
            ),
        )
        monkeypatch.setattr(writer, "hosts_save_available", lambda: True)

        def save(content, digest):
            calls.append((content, digest))
            return 0, "/etc/.netmon-hosts-fixture.bak"

        monkeypatch.setattr(writer, "save_hosts_config", save)
        view = SystemFilesView(root, root)
        view.frame.pack()
        view.on_shown()
        _wait(lambda: view.snapshot is not None, root)
        assert view.selected_path == "/etc/fstab"
        assert view.file_action.cget("text") == "fstab prüfen"
        view.tree.selection_set(writer.HOSTS)
        _wait(
            lambda: view.selected_path == writer.HOSTS
            and view.file_edit_button.instate(["!disabled"]),
            root,
        )
        assert view.file_edit_button.cget("text") == "Bearbeiten"
        view.file_edit_button.invoke()
        window = view.editors[writer.HOSTS]
        pane = window.winfo_children()[0]
        warning = pane.winfo_children()[0]
        assert "Nur für erfahrene Linux-Nutzer" in str(warning.cget("text"))
        text = pane.winfo_children()[1].winfo_children()[0]
        confirm = pane.winfo_children()[-1].winfo_children()[-1]
        text.insert("end-1c", "ungültig\n")
        confirm.invoke()
        assert confirm.cget("text") == "Änderungen prüfen" and calls == []
        text.delete("1.0", "end")
        text.insert("1.0", draft)
        confirm.invoke()
        assert text.cget("state") == "disabled"
        assert "+::1 ip6-localhost" in text.get("1.0", "end-1c")
        assert calls == []

        confirm.invoke()
        _wait(lambda: not window.winfo_exists(), root)
        assert calls == [
            writer.HOSTS,
            (draft, hashlib.sha256(original.encode()).hexdigest()),
        ]
        assert view.text.get("1.0", "end-1c") == draft
        assert "/etc/.netmon-hosts-fixture.bak" in view.status.get()
    finally:
        root.destroy()
