from pathlib import Path

from netmon.core import state


def test_config_and_state_dirs_use_xdg_home(monkeypatch, tmp_path):
    config_home = tmp_path / "config-home"
    state_home = tmp_path / "state-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))

    assert state.get_netmon_config_dir() == str(config_home / "netmon")
    assert state.get_netmon_state_dir() == str(state_home / "netmon")
    assert (config_home / "netmon").is_dir()
    assert (state_home / "netmon").is_dir()


def test_xdg_documents_dir_wins_over_home_candidates(monkeypatch, tmp_path):
    docs_home = tmp_path / "xdg-docs"
    home = tmp_path / "home"
    (home / "Documents").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(docs_home))

    assert state.get_netmon_documents_dir() == str(docs_home / "NetMon")
    assert (docs_home / "NetMon").is_dir()


def test_documents_dir_prefers_documents_over_dokumente(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / "Documents").mkdir(parents=True)
    (home / "Dokumente").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)

    assert state.get_netmon_documents_dir() == str(home / "Documents" / "NetMon")


def test_documents_dir_uses_dokumente_when_documents_missing(monkeypatch, tmp_path):
    home = tmp_path / "home"
    (home / "Dokumente").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)

    assert state.get_netmon_documents_dir() == str(home / "Dokumente" / "NetMon")


def test_documents_dir_falls_back_to_documents(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)

    assert state.get_netmon_documents_dir() == str(home / "Documents" / "NetMon")
    assert (home / "Documents" / "NetMon").is_dir()


def test_documents_subdir_ignores_blank_parts(monkeypatch, tmp_path):
    docs_home = tmp_path / "docs"
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(docs_home))

    result = state.get_netmon_documents_subdir("Logs", "", "  ", Path("Daily"))

    assert result == str(docs_home / "NetMon" / "Logs" / "Daily")
    assert (docs_home / "NetMon" / "Logs" / "Daily").is_dir()
