import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "netmon_uninstall_menu.sh"


def _run_uninstaller_function(function_body, *, home_dir, documents_dir):
    command = f"""
source "$1"
TEST_HOME="$2"
TEST_DOCUMENTS="$3"
target_home() {{ printf '%s\\n' "$TEST_HOME"; }}
collect_document_root_dirs() {{ printf '%s\\n' "$TEST_DOCUMENTS"; }}
{function_body}
"""
    return subprocess.run(
        [
            "bash",
            "-c",
            command,
            "netmon-uninstall-test",
            str(SCRIPT),
            str(home_dir),
            str(documents_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_remove_user_data_preserves_secure_browser_directory(tmp_path):
    home_dir = tmp_path / "home"
    documents_dir = home_dir / "Dokumente"
    secure_dir = documents_dir / "NetMon" / "Secure Browser"
    config_dir = documents_dir / "NetMon" / "Config"
    secure_dir.mkdir(parents=True)
    config_dir.mkdir()
    (secure_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (config_dir / "remove.txt").write_text("remove", encoding="utf-8")

    result = _run_uninstaller_function(
        "remove_user_data ja",
        home_dir=home_dir,
        documents_dir=documents_dir,
    )

    assert result.returncode == 0, result.stderr
    assert (secure_dir / "keep.txt").is_file()
    assert not config_dir.exists()


def test_remove_secure_browsers_removes_document_storage_and_menu_entry(tmp_path):
    home_dir = tmp_path / "home"
    documents_dir = home_dir / "Dokumente"
    secure_dir = documents_dir / "NetMon" / "Secure Browser"
    secure_dir.mkdir(parents=True)
    unrelated = home_dir / "Programme" / "firefox-personal"
    unrelated.mkdir(parents=True)
    app_dir = home_dir / ".local" / "share" / "applications"
    app_dir.mkdir(parents=True)
    menu_entry = app_dir / "netmon-secure-browser-test.desktop"
    menu_entry.write_text(
        "[Desktop Entry]\nName=Test\nComment=NetMon Secure Browser fuer Test\n",
        encoding="utf-8",
    )

    result = _run_uninstaller_function(
        "remove_secure_browsers",
        home_dir=home_dir,
        documents_dir=documents_dir,
    )

    assert result.returncode == 0, result.stderr
    assert not secure_dir.exists()
    assert unrelated.is_dir()
    assert not menu_entry.exists()
