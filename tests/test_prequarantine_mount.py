import os

import pytest

import netmon.app as app_module
from netmon.app import App
from netmon.core import prequarantine_mount as pm


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


TMPFS_OPTS = "rw,nosuid,nodev,noexec,relatime"
TMPFS_SUPER = "rw,size=262144k,mode=700,uid={uid},gid={gid}"


def _mount_line(point, fs_type="tmpfs", source="tmpfs", opts=TMPFS_OPTS, sup=None):
    sup = sup or TMPFS_SUPER.format(uid=os.getuid(), gid=os.getgid())
    escaped = point.replace(" ", "\\040")
    return f"36 35 0:50 / {escaped} {opts} shared:1 - {fs_type} {source} {sup}\n"


@pytest.fixture
def fixed(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir(mode=0o755)
    run.chmod(0o755)
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(_mount_line("/"))
    monkeypatch.setattr(pm, "RUN_DIR", str(run))
    monkeypatch.setattr(pm, "PREQUARANTINE_ROOT", str(run / "netmon-prequarantine"))
    monkeypatch.setattr(pm, "_MOUNTINFO", str(mountinfo))
    # Test files belong to the test user; it plays root for owner checks.
    monkeypatch.setattr(pm, "_ROOT_UID", os.getuid())
    return {
        "run": run,
        "root": run / "netmon-prequarantine",
        "leaf": run / "netmon-prequarantine" / str(os.getuid()),
        "mountinfo": mountinfo,
    }


def _create_fixed(fixed):
    for path in (fixed["root"], fixed["leaf"]):
        path.mkdir(mode=0o755, exist_ok=True)
        path.chmod(0o755)


def _simulate_mount(fixed, **line):
    fixed["leaf"].chmod(0o700)
    with open(fixed["mountinfo"], "a", encoding="utf-8") as handle:
        handle.write(_mount_line(str(fixed["leaf"]), **line))


class FakeSystem:
    """Records privileged argv and simulates install/mount/umount effects."""

    def __init__(self, fixed, *, mount_line=None, mount_rc=0):
        self.fixed = fixed
        self.calls = []
        self.mount_line = mount_line or {}
        self.mount_rc = mount_rc

    def run_cmd(self, args, timeout=15, **_kwargs):
        args = list(args)
        self.calls.append(args)
        assert args[:2] == ["sudo", "-n"]
        if args[2] == "install":
            _create_fixed(self.fixed)
            return 0, ""
        if args[2] == "mount":
            if self.mount_rc:
                return self.mount_rc, "mount failed"
            _simulate_mount(self.fixed, **self.mount_line)
            return 0, ""
        if args[2] == "umount":
            lines = self.fixed["mountinfo"].read_text().splitlines(keepends=True)
            kept = [line for line in lines if f" {self.fixed['leaf']} " not in line]
            self.fixed["mountinfo"].write_text("".join(kept))
            self.fixed["leaf"].chmod(0o755)
            return 0, ""
        raise AssertionError(f"unexpected privileged command: {args}")


def _app(monkeypatch, system, configured=""):
    app = App.__new__(App)
    app.settings = {"download_scan_temp_dir": configured}
    app.download_scan_temp_dir_var = DummyVar(configured)
    app.logs = []
    app.saved = 0
    app.tr = lambda _key, default: default
    app.log_safe = app.logs.append
    app.log_debug_safe = app.logs.append
    app._refresh_download_scan_temp_security_status = lambda: None
    app._download_scan_secure_mount_ready = lambda _path: False
    app.ensure_sudo_session = lambda _reason: True

    def save_settings(log_success=True):
        app.saved += 1

    app.save_settings = save_settings
    monkeypatch.setattr(app_module, "run_cmd", system.run_cmd)
    monkeypatch.setattr(app_module, "has_cmd", lambda _name: True)
    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)
    return app


# --- module -------------------------------------------------------------


def test_mount_point_and_commands_are_fixed_per_uid(fixed):
    leaf = str(fixed["leaf"])
    assert pm.prequarantine_mount_point() == leaf
    assert pm.prepare_command() == [
        "sudo",
        "-n",
        "install",
        "-d",
        "-o",
        "root",
        "-g",
        "root",
        "-m",
        "0755",
        str(fixed["root"]),
        leaf,
    ]
    command = pm.mount_command()
    assert command[:6] == ["sudo", "-n", "mount", "-t", "tmpfs", "-o"]
    assert command[-2:] == ["tmpfs", leaf]
    assert {"noexec", "nosuid", "nodev", "mode=700"} <= set(command[6].split(","))
    assert pm.unmount_command() == ["sudo", "-n", "umount", leaf]
    with pytest.raises(ValueError):
        pm.prequarantine_mount_point(-1)


def test_exact_mount_entry_matches_only_the_exact_point_and_topmost(fixed, tmp_path):
    spaced = str(tmp_path / "with space")
    fixed["mountinfo"].write_text(
        _mount_line("/run")
        + _mount_line(spaced, fs_type="ext4", source="/dev/sda1")
        + _mount_line(spaced)
    )
    assert pm.exact_mount_entry(spaced)["fs_type"] == "tmpfs"
    assert pm.exact_mount_entry(spaced + "/sub") is None
    assert pm.exact_mount_entry("/run/x") is None
    assert "noexec" in pm.exact_mount_entry("/run")["mount_options"]


def test_unmounted_point_accepts_root_created_directories(fixed):
    _create_fixed(fixed)
    assert pm.unsafe_unmounted_point_reason() == ""


@pytest.mark.parametrize("victim", ["leaf", "root"])
def test_unmounted_point_rejects_symlinks(fixed, tmp_path, victim):
    target = tmp_path / "etc"
    target.mkdir(mode=0o755)
    target.chmod(0o755)
    if victim == "root":
        fixed["root"].symlink_to(target)
        (target / str(os.getuid())).mkdir(mode=0o755)
    else:
        fixed["root"].mkdir(mode=0o755)
        fixed["root"].chmod(0o755)
        fixed["leaf"].symlink_to(target)
    assert "kein echtes Verzeichnis" in pm.unsafe_unmounted_point_reason()


def test_unmounted_point_rejects_foreign_owner_and_writable_parents(fixed, monkeypatch):
    _create_fixed(fixed)
    fixed["root"].chmod(0o777)
    assert "beschreibbar" in pm.unsafe_unmounted_point_reason()
    fixed["root"].chmod(0o755)
    monkeypatch.setattr(pm, "_ROOT_UID", os.getuid() + 1)
    assert "gehört nicht root" in pm.unsafe_unmounted_point_reason()


def test_unmounted_point_rejects_existing_mount(fixed):
    _create_fixed(fixed)
    _simulate_mount(fixed, fs_type="ext4", source="/dev/sda2")
    assert "bereits ein Mountpunkt" in pm.unsafe_unmounted_point_reason()


def test_active_mount_requires_exact_verified_tmpfs(fixed):
    _create_fixed(fixed)
    assert "nicht eingehängt" in pm.unsafe_active_mount_reason()
    _simulate_mount(fixed)
    assert pm.active_mount_ready()
    fixed["leaf"].chmod(0o755)
    assert "Rechte" in pm.unsafe_active_mount_reason()


@pytest.mark.parametrize(
    "line, expected",
    [
        ({"opts": "rw,nosuid,nodev"}, "noexec"),
        ({"fs_type": "ext4", "source": "/dev/sda1"}, "kein NetMon-tmpfs"),
        ({"source": "/dev/shm"}, "kein NetMon-tmpfs"),
    ],
)
def test_active_mount_rejects_wrong_mount(fixed, line, expected):
    _create_fixed(fixed)
    _simulate_mount(fixed, **line)
    assert expected in pm.unsafe_active_mount_reason()


# --- App flow -----------------------------------------------------------


def test_configured_symlink_target_is_never_mounted(fixed, tmp_path, monkeypatch):
    protected = tmp_path / "etc"
    protected.mkdir()
    planted = tmp_path / "shared" / "download_scan"
    planted.parent.mkdir()
    planted.symlink_to(protected)
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system, configured=str(planted))

    assert app._ensure_download_scan_secure_mount(interactive=True) is True

    leaf = str(fixed["leaf"])
    assert [call[2] for call in system.calls] == ["install", "mount"]
    assert system.calls[1][-1] == leaf
    for call in system.calls:
        assert not any(str(planted) in arg or str(protected) in arg for arg in call)
        paths = [arg for arg in call if arg.startswith("/")]
        assert set(paths) <= {str(fixed["root"]), leaf}
    assert app.settings["download_scan_temp_dir"] == leaf
    assert app.download_scan_temp_dir_var.get() == leaf
    assert app.saved == 1
    assert not any(protected.iterdir())


def test_already_verified_mount_needs_no_privileged_command(fixed, monkeypatch):
    _create_fixed(fixed)
    _simulate_mount(fixed)
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system, configured=str(fixed["leaf"]))

    assert app._ensure_download_scan_secure_mount(interactive=False) is True
    assert system.calls == []
    assert app.saved == 0


def test_symlinked_fixed_point_fails_closed_before_mount(fixed, tmp_path, monkeypatch):
    target = tmp_path / "etc"
    target.mkdir()
    fixed["root"].mkdir(mode=0o755)
    fixed["root"].chmod(0o755)
    fixed["leaf"].symlink_to(target)

    class NoCreate(FakeSystem):
        def run_cmd(self, args, timeout=15, **kwargs):
            if args[2] == "install":
                self.calls.append(list(args))
                return 0, ""
            return super().run_cmd(args, timeout, **kwargs)

    system = NoCreate(fixed)
    app = _app(monkeypatch, system)

    assert app._ensure_download_scan_secure_mount(interactive=True) is False
    assert [call[2] for call in system.calls] == ["install"]
    assert "kein echtes Verzeichnis" in app._download_scan_temp_last_error
    assert app.saved == 0


def test_foreign_mount_at_fixed_point_is_neither_prepared_nor_overmounted(
    fixed, monkeypatch
):
    _create_fixed(fixed)
    _simulate_mount(fixed, fs_type="ext4", source="/dev/sda2")
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system)

    assert app._ensure_download_scan_secure_mount(interactive=True) is False
    assert system.calls == []
    assert "bereits ein Mountpunkt" in app._download_scan_temp_last_error


def test_unverified_result_after_mount_is_not_used(fixed, monkeypatch):
    system = FakeSystem(fixed, mount_line={"opts": "rw,nosuid,nodev"})
    app = _app(monkeypatch, system, configured="/home/user/scan")

    assert app._ensure_download_scan_secure_mount(interactive=True) is False
    assert app.settings["download_scan_temp_dir"] == "/home/user/scan"
    assert "noexec" in app._download_scan_temp_last_error


def test_failed_mount_or_cancelled_sudo_stops(fixed, monkeypatch):
    system = FakeSystem(fixed, mount_rc=32)
    app = _app(monkeypatch, system)
    assert app._ensure_download_scan_secure_mount(interactive=True) is False
    assert [call[2] for call in system.calls] == ["install", "mount"]

    system = FakeSystem(fixed)
    app = _app(monkeypatch, system)
    app.ensure_sudo_session = lambda _reason: False
    assert app._ensure_download_scan_secure_mount(interactive=True) is False
    assert system.calls == []


def test_disable_unmounts_only_the_fixed_netmon_tmpfs(fixed, monkeypatch):
    _create_fixed(fixed)
    _simulate_mount(fixed)
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system, configured=str(fixed["leaf"]))
    app._default_download_scan_temp_dir = lambda: "/home/user/.cache/scan"

    assert app._disable_download_scan_secure_mount(interactive=True) is True
    assert system.calls == [["sudo", "-n", "umount", str(fixed["leaf"])]]
    assert app.settings["download_scan_temp_dir"] == "/home/user/.cache/scan"
    assert app.download_scan_temp_dir_var.get() == "/home/user/.cache/scan"


def test_disable_never_unmounts_a_configured_system_mount(fixed, monkeypatch):
    # A configured path inside a noexec system tmpfs (e.g. /run/lock) used to
    # be passed to "sudo umount".
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system, configured="/run/lock")
    app._download_scan_secure_mount_ready = lambda _path: True

    assert app._disable_download_scan_secure_mount(interactive=True) is True
    assert system.calls == []
    assert app.settings["download_scan_temp_dir"] == "/run/lock"


def test_disable_refuses_foreign_mount_at_fixed_point(fixed, monkeypatch):
    _create_fixed(fixed)
    _simulate_mount(fixed, fs_type="ext4", source="/dev/sda2")
    system = FakeSystem(fixed)
    app = _app(monkeypatch, system)

    assert app._disable_download_scan_secure_mount(interactive=True) is False
    assert system.calls == []


def test_unmounted_fixed_point_falls_back_to_unprivileged_default(fixed, monkeypatch):
    _create_fixed(fixed)
    app = _app(monkeypatch, FakeSystem(fixed), configured=str(fixed["leaf"]))
    app._default_download_scan_temp_dir = lambda: "/home/user/.cache/scan"
    assert app._normalized_download_scan_temp_dir() == "/home/user/.cache/scan"

    _simulate_mount(fixed)
    assert app._normalized_download_scan_temp_dir() == str(fixed["leaf"])


def test_default_prefers_verified_fixed_mount(fixed, monkeypatch):
    _create_fixed(fixed)
    _simulate_mount(fixed)
    app = _app(monkeypatch, FakeSystem(fixed))
    assert app._default_download_scan_temp_dir() == str(fixed["leaf"])
