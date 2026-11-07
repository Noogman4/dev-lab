"""Profile paths and explicit legacy selection, using only temporary folders."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.core import state
from netmon.features import vpn_controller as vpn


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    return tmp_path


def configure(home, text):
    directory = home / ".config"
    directory.mkdir(exist_ok=True)
    (directory / "user-dirs.dirs").write_text(text, encoding="utf-8")


@pytest.mark.parametrize("variable", ["$HOME", "${HOME}"])
def test_system_documents_setting_wins_for_profiles_without_moving_settings(
    home, variable
):
    (home / "Documents" / "NetMon" / "Config").mkdir(parents=True)
    settings = home / "Documents" / "NetMon" / "Config" / "settings.json"
    settings.write_text('{"existing":true}')
    configure(home, f'XDG_DOCUMENTS_DIR="{variable}/Dokumente"\n')

    expected = home / "Dokumente" / "NetMon" / "WireGuard"
    assert state.get_netmon_wireguard_dir() == str(expected)
    assert vpn.netmon_wireguard_profiles_dir() == str(expected)
    assert expected.is_dir()
    assert state.get_netmon_documents_dir() == str(home / "Documents" / "NetMon")
    assert settings.read_text() == '{"existing":true}'
    assert not (home / "Dokumente" / "NetMon" / "Config").exists()


def test_environment_override_wins_over_user_dirs_file(home, monkeypatch):
    configure(home, 'XDG_DOCUMENTS_DIR="$HOME/Dokumente"\n')
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(home / "Override"))
    assert state.get_netmon_wireguard_dir() == str(
        home / "Override" / "NetMon" / "WireGuard"
    )


def test_absolute_system_documents_path_with_spaces(home):
    configure(home, f'XDG_DOCUMENTS_DIR="{home}/My Documents" # comment\n')
    assert state.get_netmon_wireguard_dir() == str(
        home / "My Documents" / "NetMon" / "WireGuard"
    )


@pytest.mark.parametrize(
    "value",
    [
        '"relative/path"',
        '"$OTHER/Documents"',
        '"$(touch /tmp/NETMON_MUST_NOT_EXECUTE)"',
        '"`touch /tmp/NETMON_MUST_NOT_EXECUTE`"',
        '"/unterminated',
        '"/one" "/two"',
    ],
)
def test_invalid_config_is_data_and_falls_back(home, value, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Document resolution must never execute a shell or command")

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(state.os, "system", forbidden)
    configure(home, f"XDG_DOCUMENTS_DIR={value}\n")
    assert state.get_netmon_wireguard_dir() == str(
        home / "Documents" / "NetMon" / "WireGuard"
    )


def test_no_config_keeps_existing_dokumente_fallback(home):
    (home / "Dokumente").mkdir()
    assert state.get_netmon_wireguard_dir() == str(
        home / "Dokumente" / "NetMon" / "WireGuard"
    )


@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.parametrize("old_name", ["Documents", ".local/share/netmon/wireguard"])
@pytest.mark.parametrize("system_name", ["Documents", "Dokumente"])
def test_legacy_selection_requires_consent_and_never_copies(
    home, monkeypatch, accept, old_name, system_name
):
    configure(home, f'XDG_DOCUMENTS_DIR="$HOME/{system_name}"\n')
    if old_name == "Documents" and system_name == "Documents":
        old_name = "Dokumente"
    old = home / old_name
    if old_name in {"Documents", "Dokumente"}:
        old = old / "NetMon" / "WireGuard"
    old.mkdir(parents=True)
    source = old / "work.conf"
    source.write_text("synthetic profile, never imported in this test")
    source.chmod(0o600)
    standard = Path(state.get_netmon_wireguard_dir())
    dialogs = []
    monkeypatch.setattr(
        vpn.messagebox,
        "askyesno",
        lambda title, text, **kwargs: dialogs.append(text) or accept,
    )
    app = SimpleNamespace(get_wg_import_dir=lambda: str(standard))
    before = source.read_bytes(), source.stat().st_mode

    assert vpn._wireguard_import_initialdir(app) == str(old if accept else standard)
    assert len(dialogs) == 1 and str(old) in dialogs[0]
    assert list(standard.iterdir()) == []
    assert (source.read_bytes(), source.stat().st_mode) == before


def test_deliberately_selected_import_directory_is_preserved(home, monkeypatch):
    chosen = home / "Downloaded profiles"
    chosen.mkdir()
    app = SimpleNamespace(get_wg_import_dir=lambda: str(chosen))
    monkeypatch.setattr(
        vpn.messagebox, "askyesno", lambda *a, **k: pytest.fail("Unnecessary prompt")
    )
    assert vpn._wireguard_import_initialdir(app) == str(chosen)


def test_both_profile_import_dialogs_use_same_resolver(home, monkeypatch):
    chosen = home / "Chosen"
    chosen.mkdir()
    calls = []
    monkeypatch.setattr(vpn, "_wireguard_import_initialdir", lambda app: str(chosen))
    monkeypatch.setattr(vpn, "has_cmd", lambda name: True)
    monkeypatch.setattr(
        vpn.filedialog,
        "askopenfilenames",
        lambda **kwargs: calls.append(kwargs["initialdir"]) or (),
    )
    app = SimpleNamespace(tr=lambda key, fallback: fallback, log=lambda text: None)
    vpn.import_wg_profiles_from_folder(app)
    vpn.import_wg_profiles_to_networkmanager(app)
    assert calls == [str(chosen), str(chosen)]
