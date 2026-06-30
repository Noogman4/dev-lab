import netmon.core.rkhunter_manager as rkhunter_manager


def test_preferred_web_cmd_prefers_wget(monkeypatch):
    def fake_which(name):
        if name == "wget":
            return "/usr/bin/wget"
        if name == "curl":
            return "/usr/bin/curl"
        return None

    monkeypatch.setattr(rkhunter_manager.shutil, "which", fake_which)

    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/wget"


def test_preferred_web_cmd_falls_back_to_curl(monkeypatch):
    def fake_which(name):
        if name == "curl":
            return "/usr/bin/curl"
        return None

    monkeypatch.setattr(rkhunter_manager.shutil, "which", fake_which)

    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/curl"


def test_preferred_web_cmd_rejects_untrusted_path_and_falls_back(monkeypatch):
    def fake_which(name):
        if name == "wget":
            return "/home/demo/.local/bin/wget"
        if name == "curl":
            return "/usr/bin/curl"
        return None

    monkeypatch.setattr(rkhunter_manager.shutil, "which", fake_which)

    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/curl"


def test_preferred_web_cmd_returns_empty_when_only_untrusted_candidates_exist(monkeypatch):
    def fake_which(name):
        if name == "wget":
            return "/home/demo/.local/bin/wget"
        if name == "curl":
            return "/tmp/curl"
        return None

    monkeypatch.setattr(rkhunter_manager.shutil, "which", fake_which)

    assert rkhunter_manager._preferred_web_cmd() == ""


def test_detect_update_failure_matches_invalid_web_cmd_message():
    output = 'Invalid WEB_CMD configuration option: Relative pathname: "/usr/bin/wget"'

    assert rkhunter_manager.detect_update_failure(output) is True


def test_repair_config_replaces_invalid_web_cmd(monkeypatch):
    written = {}

    monkeypatch.setattr(
        rkhunter_manager,
        "_read_config",
        lambda path: (
            0,
            "UPDATE_MIRRORS=0\nMIRRORS_MODE=1\nWEB_CMD=/bin/false\nOTHER=keep\n",
        ),
    )
    monkeypatch.setattr(
        rkhunter_manager.shutil,
        "which",
        lambda name: "/usr/bin/wget" if name == "wget" else None,
    )

    def fake_write(config_text, config_path):
        written["text"] = config_text
        written["path"] = config_path
        return 0, ""

    monkeypatch.setattr(rkhunter_manager, "_write_config", fake_write)

    rc, out = rkhunter_manager.repair_config("/etc/rkhunter.conf")

    assert rc == 0
    assert out == ""
    assert written["path"] == "/etc/rkhunter.conf"
    assert 'UPDATE_MIRRORS=1\n' in written["text"]
    assert 'MIRRORS_MODE=0\n' in written["text"]
    assert "WEB_CMD=/usr/bin/wget\n" in written["text"]
    assert "OTHER=keep\n" in written["text"]
