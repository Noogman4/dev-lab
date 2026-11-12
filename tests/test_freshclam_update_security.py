"""Exercise update fallback boundaries without executing FreshClam or sudo."""

from contextlib import contextmanager
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from netmon.features import clamav_controller as controller


@pytest.fixture
def update(monkeypatch, tmp_path):
    logs, panels, calls = [], [], []
    app = SimpleNamespace(
        security_clamav_update_running=False,
        clamav_database_dir="old-selection",
        log=logs.append,
        log_safe=logs.append,
        log_debug_safe=logs.append,
    )

    class InlineThread:
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", InlineThread)
    monkeypatch.setattr(controller.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(controller, "has_cmd", lambda _name: True)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / 'user data with "quotes"'))
    monkeypatch.setattr(
        controller, "update_clamav_panel", lambda _app, **kw: panels.append(kw)
    )
    monkeypatch.setattr(
        controller, "update_clamav_panel_safe", lambda _app, **kw: panels.append(kw)
    )
    original_temp = controller.tempfile.NamedTemporaryFile
    temp_dir = tmp_path / "configs"
    temp_dir.mkdir()
    monkeypatch.setattr(
        controller.tempfile,
        "NamedTemporaryFile",
        lambda *a, **kw: original_temp(*a, dir=temp_dir, **kw),
    )

    def fail_command(cmd, **_kwargs):
        calls.append(cmd)
        return 1, "synthetic update failure"

    monkeypatch.setattr(controller, "run_cmd", fail_command)
    return SimpleNamespace(
        app=app, logs=logs, panels=panels, calls=calls, temp_dir=temp_dir
    )


@pytest.mark.parametrize("control", ["\n", "\r", "\0", "\t", "\x1b", "\x7f"])
@pytest.mark.parametrize("position", ["before", "inside", "after"])
def test_invalid_xdg_path_aborts_before_files_or_commands(
    update, monkeypatch, control, position
):
    path = {
        "before": control + "/tmp/user-data",
        "inside": "/tmp/user" + control + "DatabaseOwner root",
        "after": "/tmp/user-data" + control,
    }[position]
    # os.environ itself rejects NUL; a dictionary also exercises that case.
    monkeypatch.setattr(controller.os, "environ", {"XDG_DATA_HOME": path})

    def forbidden_mkdir(_path):
        pytest.fail("invalid environment reached mkdir")

    monkeypatch.setattr(controller, "_safe_makedirs_no_symlink", forbidden_mkdir)
    with pytest.raises(ValueError, match="Steuerzeichen"):
        controller.clamav_user_database_dir()
    controller.security_clamav_update_async(update.app)
    assert not update.calls
    assert not list(update.temp_dir.iterdir())
    assert update.panels[-1]["status"] == "Fehler"
    assert update.app.security_clamav_update_running is False


def test_invalid_expanded_home_is_rejected(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(
        controller.os.path, "expanduser", lambda _path: "/home/user\nHook cmd"
    )
    with pytest.raises(ValueError, match="Steuerzeichen"):
        controller.clamav_user_database_dir()


def test_user_success_keeps_private_database_and_needs_no_sudo(update, monkeypatch):
    def run(cmd, **kwargs):
        update.calls.append(cmd)
        assert kwargs["timeout"] == 900
        assert cmd[0] == "freshclam"
        config = Path(cmd[cmd.index("--config-file") + 1])
        assert stat.S_IMODE(config.stat().st_mode) == 0o600
        content = config.read_text()
        assert (
            content
            == "DatabaseMirror database.clamav.net\nForeground true\nCompressLocalDatabase no\n"
        )
        database = Path(cmd[cmd.index("--datadir") + 1])
        assert str(database) not in content
        assert 'user data with "quotes"' in str(database)
        (database / "daily.cvd").write_bytes(b"synthetic signature")
        return 0, "synthetic success"

    monkeypatch.setattr(controller, "run_cmd", run)
    controller.security_clamav_update_async(update.app)
    assert len(update.calls) == 1
    assert update.app.clamav_database_dir == controller.clamav_user_database_dir()
    assert update.panels[-1]["signatures"] == "aktuell"
    assert update.app.security_clamav_update_running is False
    assert not list(update.temp_dir.iterdir())


@pytest.mark.parametrize("system_user_success", [False, True])
def test_mutated_user_config_never_reaches_system_fallback(
    update, monkeypatch, tmp_path, system_user_success
):
    checked = []
    monkeypatch.setattr(
        controller, "_clamav_check_system_update_paths", lambda: checked.append(True)
    )
    hostile = tmp_path / "hostile.conf"
    hostile.write_text("DatabaseOwner root\nOnUpdateExecute synthetic-hook\n")
    user_config = []

    def run(cmd, **_kwargs):
        update.calls.append(cmd)
        config = Path(cmd[cmd.index("--config-file") + 1])
        if len(update.calls) == 1:
            user_config.append(config)
            config.unlink()
            config.symlink_to(hostile)
            return 1, "synthetic user failure"
        assert str(config) == "/etc/clamav/freshclam.conf"
        assert str(user_config[0]) not in cmd
        assert "--datadir" not in cmd
        if cmd[0] == "sudo":
            assert checked == [True]
            assert cmd[:4] == ["sudo", "-n", "--", "/usr/bin/freshclam"]
            return 0, "synthetic system success"
        assert cmd[0] == "/usr/bin/freshclam"
        return (0 if system_user_success else 1), "synthetic system attempt"

    monkeypatch.setattr(controller, "run_cmd", run)
    controller.security_clamav_update_async(update.app)
    assert len(update.calls) == (2 if system_user_success else 3)
    assert checked == ([] if system_user_success else [True])
    assert update.app.clamav_database_dir == ""
    assert not user_config[0].is_symlink()
    assert "OnUpdateExecute" in hostile.read_text()
    assert update.app.security_clamav_update_running is False


def test_unsafe_system_layout_blocks_sudo_after_user_failures(update, monkeypatch):
    def reject():
        raise PermissionError("synthetic untrusted system config")

    monkeypatch.setattr(controller, "_clamav_check_system_update_paths", reject)
    controller.security_clamav_update_async(update.app)
    assert len(update.calls) == 2
    assert all(cmd[0] != "sudo" for cmd in update.calls)
    assert update.panels[-1]["status"] == "Fehler"
    assert any("Systemupdate blockiert" in line for line in update.logs)
    assert update.app.security_clamav_update_running is False
    assert not list(update.temp_dir.iterdir())


def test_partial_config_is_cleaned_and_not_used(update, monkeypatch):
    original_temp = controller.tempfile.NamedTemporaryFile

    @contextmanager
    def broken_config(*args, **kwargs):
        with original_temp(*args, **kwargs) as handle:

            def fail_write(_content):
                raise OSError("synthetic disk full")

            yield SimpleNamespace(name=handle.name, write=fail_write)

    monkeypatch.setattr(controller.tempfile, "NamedTemporaryFile", broken_config)
    monkeypatch.setattr(controller, "has_cmd", lambda name: name == "freshclam")
    controller.security_clamav_update_async(update.app)
    assert len(update.calls) == 1
    assert update.calls[0][-1] == "/etc/clamav/freshclam.conf"
    assert not list(update.temp_dir.iterdir())
    assert update.app.security_clamav_update_running is False


def test_root_gui_cannot_feed_user_config_to_privileged_parser(update, monkeypatch):
    monkeypatch.setattr(controller.os, "geteuid", lambda: 0)
    controller.security_clamav_update_async(update.app)
    assert not update.calls
    assert not list(update.temp_dir.iterdir())
    assert update.panels[-1]["signatures"] == "Update blockiert"


@pytest.fixture
def safe_system_layout(monkeypatch):
    def info(path):
        is_file = path in {"/usr/bin/freshclam", "/etc/clamav/freshclam.conf"}
        return SimpleNamespace(
            st_uid=0, st_mode=(stat.S_IFREG if is_file else stat.S_IFDIR) | 0o755
        )

    monkeypatch.setattr(controller.os, "lstat", info)
    return info


def test_protected_system_layout_is_accepted(safe_system_layout):
    controller._clamav_check_system_update_paths()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/usr",
        "/usr/bin",
        "/usr/bin/freshclam",
        "/etc",
        "/etc/clamav",
        "/etc/clamav/freshclam.conf",
    ],
)
@pytest.mark.parametrize(
    "defect",
    ["owner", "group_write", "world_write", "symlink", "wrong_type", "missing"],
)
def test_privileged_fallback_rejects_unsafe_paths(
    monkeypatch, safe_system_layout, path, defect
):
    def info(candidate):
        entry = safe_system_layout(candidate)
        if candidate == path:
            if defect == "owner":
                entry.st_uid = 1000
            elif defect == "group_write":
                entry.st_mode |= 0o020
            elif defect == "world_write":
                entry.st_mode |= 0o002
            elif defect == "symlink":
                entry.st_mode = stat.S_IFLNK | 0o777
            elif defect == "wrong_type":
                entry.st_mode = stat.S_IFIFO | 0o600
            else:
                raise FileNotFoundError(candidate)
        return entry

    monkeypatch.setattr(controller.os, "lstat", info)
    with pytest.raises(OSError):
        controller._clamav_check_system_update_paths()


def test_privileged_fallback_rejects_nonexecutable_binary(
    monkeypatch, safe_system_layout
):
    def info(path):
        entry = safe_system_layout(path)
        if path == "/usr/bin/freshclam":
            entry.st_mode = stat.S_IFREG | 0o644
        return entry

    monkeypatch.setattr(controller.os, "lstat", info)
    with pytest.raises(PermissionError):
        controller._clamav_check_system_update_paths()
