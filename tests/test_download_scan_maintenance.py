"""Pre-quarantine maintenance never deletes or truncates outside its own folder.

Synthetic files in tmp_path only.
"""

import os
from types import SimpleNamespace

import pytest

from netmon import app as app_module
from netmon.core import download_scan_fs as dfs


def _private(path):
    path.mkdir(mode=0o700)
    return path


def _fill(directory):
    (directory / "download.bin").write_bytes(b"x")
    (directory / "unpacked").mkdir()
    (directory / "unpacked" / "inner.txt").write_text("inner")


@pytest.fixture
def victim(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "thesis.odt").write_text("precious")
    return victim


def test_clear_removes_entries_without_following_links(tmp_path, victim):
    temp = _private(tmp_path / "pre-quarantine")
    _fill(temp)
    (temp / "link-to-victim").symlink_to(victim)
    (temp / "unpacked" / "nested-link").symlink_to(victim)

    removed, errors = dfs.clear_directory(str(temp))

    assert (removed, errors) == (3, [])
    assert os.listdir(temp) == []
    assert (victim / "thesis.odt").read_text() == "precious"


@pytest.mark.parametrize("layout", ["not-private", "symlink", "symlinked-parent"])
def test_clear_refuses_foreign_or_redirected_folders(tmp_path, victim, layout):
    if layout == "not-private":
        target = victim
        victim.chmod(0o755)
    elif layout == "symlink":
        victim.chmod(0o700)
        target = tmp_path / "download_scan"
        target.symlink_to(victim)
    else:
        real_parent = tmp_path / "real"
        real_parent.mkdir(mode=0o700)
        victim.rename(real_parent / "download_scan")
        victim = real_parent / "download_scan"
        victim.chmod(0o700)
        (tmp_path / "linked").symlink_to(real_parent)
        target = tmp_path / "linked" / "download_scan"

    with pytest.raises((dfs.UnsafePath, OSError)):
        dfs.clear_directory(str(target))
    with pytest.raises((dfs.UnsafePath, OSError)):
        dfs.list_directory(str(target))
    assert (victim / "thesis.odt").read_text() == "precious"


def test_clear_only_removes_confirmed_names(tmp_path):
    temp = _private(tmp_path / "pre-quarantine")
    _fill(temp)
    confirmed = dfs.list_directory(str(temp))
    (temp / "arrived-later.bin").write_bytes(b"new")

    removed, _errors = dfs.clear_directory(str(temp), names=confirmed)

    assert removed == 2
    assert os.listdir(temp) == ["arrived-later.bin"]


def test_report_never_writes_through_planted_link(tmp_path, victim):
    reports = _private(tmp_path / "reports")
    (reports / "netmon_download_scan_file_1.txt").symlink_to(victim / "thesis.odt")

    path = dfs.write_report(str(reports), "netmon_download_scan_file_1.txt", "REPORT")

    assert (victim / "thesis.odt").read_text() == "precious"
    assert path == str(reports / "netmon_download_scan_file_1_1.txt")
    assert open(path).read() == "REPORT\n"
    assert os.stat(path).st_mode & 0o777 == 0o600


def test_report_folder_is_created_private_and_links_are_refused(tmp_path, victim):
    created = tmp_path / "Documents" / "NetMon" / "Download-Scan"
    dfs.write_report(str(created), "r.txt", "ok")
    assert created.stat().st_mode & 0o777 == 0o700

    linked = tmp_path / "linked-reports"
    victim.chmod(0o700)
    linked.symlink_to(victim)
    with pytest.raises(dfs.UnsafePath):
        dfs.write_report(str(linked), "r.txt", "x")
    shared = tmp_path / "shared-reports"
    shared.mkdir(mode=0o755)
    with pytest.raises(dfs.UnsafePath):
        dfs.write_report(str(shared), "r.txt", "x")
    assert sorted(os.listdir(victim)) == ["thesis.odt"]


@pytest.fixture
def app(monkeypatch):
    app = app_module.App.__new__(app_module.App)
    app.tr = lambda _key, fallback: fallback
    app.logs = []
    app.log_safe = app.logs.append
    app.log_debug_safe = app.logs.append
    app.dialogs = []
    app._refresh_download_scan_temp_security_status = lambda: None
    app._set_download_scan_status = lambda **_kwargs: None
    app._update_download_scan_result_text = lambda _text: None
    monkeypatch.setattr(
        app_module.messagebox,
        "showerror",
        lambda title, body, **_k: app.dialogs.append(("error", body)),
    )
    return app


def _use_temp(app, path):
    app._normalized_download_scan_temp_dir = lambda: str(path)


@pytest.mark.parametrize("answer", [True, False])
def test_clear_button_confirms_exact_folder_and_entries(
    app, tmp_path, monkeypatch, answer
):
    temp = _private(tmp_path / "pre-quarantine")
    _fill(temp)
    _use_temp(app, temp)

    def askyesno(_title, body, **_kwargs):
        app.dialogs.append(("confirm", body))
        (temp / "arrived-later.bin").write_bytes(b"new")
        return answer

    monkeypatch.setattr(app_module.messagebox, "askyesno", askyesno)

    assert app.clear_download_scan_temp_folder() is answer
    kind, body = app.dialogs[0]
    assert kind == "confirm"
    assert str(temp) in body and "2 Einträge" in body
    assert "- download.bin" in body and "- unpacked" in body
    expected = (
        ["arrived-later.bin"]
        if answer
        else sorted(["arrived-later.bin", "download.bin", "unpacked"])
    )
    assert sorted(os.listdir(temp)) == expected


def test_clear_button_refuses_non_private_folder_without_asking(
    app, victim, monkeypatch
):
    victim.chmod(0o755)
    _use_temp(app, victim)
    monkeypatch.setattr(
        app_module.messagebox,
        "askyesno",
        lambda *_a, **_k: pytest.fail("must not ask before validation"),
    )

    assert app.clear_download_scan_temp_folder() is False
    assert app.dialogs[0][0] == "error"
    assert (victim / "thesis.odt").read_text() == "precious"


@pytest.mark.parametrize("private", [False, True])
def test_temp_folder_choice_requires_a_private_folder(
    app, tmp_path, monkeypatch, private
):
    chosen = tmp_path / "chosen"
    chosen.mkdir(mode=0o700 if private else 0o755)
    chosen.chmod(0o700 if private else 0o755)
    previous = str(tmp_path / "previous")
    app.download_scan_temp_dir_var = SimpleNamespace(value=previous)
    app.download_scan_temp_dir_var.get = lambda: app.download_scan_temp_dir_var.value
    app.download_scan_temp_dir_var.set = lambda v: setattr(
        app.download_scan_temp_dir_var, "value", v
    )
    app.download_scan_temp_security_var = SimpleNamespace(get=lambda: "")
    app._normalized_download_scan_temp_dir = lambda: previous
    app.prepare_download_scan_workspace = lambda **_k: None
    monkeypatch.setattr(app_module.filedialog, "askdirectory", lambda **_k: str(chosen))

    app.choose_download_scan_temp_dir()

    if private:
        assert app.download_scan_temp_dir_var.value == str(chosen)
        assert app.dialogs == []
    else:
        assert app.download_scan_temp_dir_var.value == previous
        assert app.dialogs[0][0] == "error"


def test_reports_are_written_outside_the_pre_quarantine(app, tmp_path, monkeypatch):
    temp = _private(tmp_path / "pre-quarantine")
    _use_temp(app, temp)
    documents = tmp_path / "Documents" / "NetMon"
    monkeypatch.setattr(app_module, "get_netmon_documents_dir", lambda: str(documents))
    app.download_scan_save_report_var = SimpleNamespace(get=lambda: True)

    path = app._download_scan_write_report("file", "SCAN REPORT")

    assert path.startswith(str(documents / "Download-Scan") + os.sep)
    assert not path.startswith(str(temp))
    assert open(path).read() == "SCAN REPORT\n"
    assert os.listdir(temp) == []
