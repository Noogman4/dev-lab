from pathlib import Path

import pytest

from netmon.core import tooling


def write_speedtest_module(path: Path, body: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        body
        or (
            "def run_speedtest():\n    return None\n"
            "def format_speedtest_summary():\n    return ''\n"
            "def format_speedtest_table():\n    return ''\n"
        ),
        encoding="utf-8",
    )


def test_get_user_pictures_dir_uses_valid_xdg_result(monkeypatch, tmp_path):
    pictures = tmp_path / "xdg-pictures"
    pictures.mkdir()
    monkeypatch.setattr(tooling, "has_cmd", lambda name: name == "xdg-user-dir")

    class Proc:
        returncode = 0
        stdout = str(pictures)

    monkeypatch.setattr(tooling.subprocess, "run", lambda *_args, **_kwargs: Proc())

    assert tooling.get_user_pictures_dir() == str(pictures)


def test_get_user_pictures_dir_falls_back_to_bilder(monkeypatch, tmp_path):
    home = tmp_path / "home"
    bilder = home / "Bilder"
    bilder.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(tooling, "has_cmd", lambda _name: False)

    assert tooling.get_user_pictures_dir() == str(bilder)


def test_get_user_pictures_dir_falls_back_to_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(tooling, "has_cmd", lambda _name: False)

    assert tooling.get_user_pictures_dir() == str(home)


def test_load_speedtest_module_uses_first_existing_candidate(tmp_path):
    repo_root = tmp_path / "repo"
    app_file = repo_root / "netmon" / "app.py"
    module_file = repo_root / "netmon" / "modules" / "speedtest.py"
    app_file.parent.mkdir(parents=True)
    app_file.write_text("", encoding="utf-8")
    write_speedtest_module(module_file)

    mod, loaded_path = tooling.load_speedtest_module_from_file(
        app_file=str(app_file),
        repo_root=str(repo_root),
        search_paths=[],
    )

    assert loaded_path == str(module_file)
    assert callable(mod.run_speedtest)


def test_load_speedtest_module_deduplicates_checked_paths(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    app_file = repo_root / "netmon" / "app.py"
    app_file.parent.mkdir(parents=True)
    app_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(tooling.os.path, "isfile", lambda _path: False)

    with pytest.raises(ModuleNotFoundError) as exc_info:
        tooling.load_speedtest_module_from_file(
            app_file=str(app_file),
            repo_root=str(repo_root),
            search_paths=[str(repo_root)],
        )

    detail = str(exc_info.value)
    checked = detail.rsplit(": ", 1)[1].split(", ")
    assert len(checked) == len(set(checked))


def test_check_speedtest_module_available_reports_missing_functions(tmp_path):
    repo_root = tmp_path / "repo"
    app_file = repo_root / "netmon" / "app.py"
    module_file = repo_root / "netmon" / "modules" / "speedtest.py"
    app_file.parent.mkdir(parents=True)
    app_file.write_text("", encoding="utf-8")
    write_speedtest_module(module_file, "def run_speedtest():\n    return None\n")

    ok, detail = tooling.check_speedtest_module_available(
        app_file=str(app_file),
        repo_root=str(repo_root),
        search_paths=[],
    )

    assert ok is False
    assert "format_speedtest_summary" in detail
    assert "format_speedtest_table" in detail
