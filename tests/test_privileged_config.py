"""Regression coverage for privileged-tempfile-reopen (CWE-367).

All writes use temporary fixtures; sudo and host configuration are never run.
"""

import hashlib
import io
import os
import stat
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.core import privileged_config as writer
from netmon.core import rkhunter_manager
from netmon.features import dot_controller
from netmon.features import security_audit_controller as audit
from netmon.services.dns_control_service import DNSControlService

DOT = "/etc/systemd/resolved.conf.d/netmon-dot.conf"
SYSCTL = "/etc/sysctl.d/99-zz-netmon-hardening.conf"
UFW = "/etc/ufw/sysctl.conf"


@pytest.fixture
def root_main(monkeypatch):
    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(writer.os, "geteuid", lambda: 0)
    writes = []
    monkeypatch.setattr(writer, "_atomic_write", lambda p, d: writes.append((p, d)))
    return writes


def receive(monkeypatch, args, data):
    monkeypatch.setattr(writer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data)))
    return writer.main(args)


@pytest.mark.parametrize("path", sorted(writer.DESTINATIONS))
def test_exact_content_via_stdin(monkeypatch, root_main, path):
    content = "# Geprüfter Inhalt\nkey = 1\n"

    def runner(args, *, input_text, timeout):
        assert args[:5] == ["sudo", "-n", "/usr/bin/python3", "-I", "-c"]
        assert args[5] == writer.BOOTSTRAP
        assert content not in " ".join(args)
        return receive(monkeypatch, args[6:], input_text.encode("utf-8")), ""

    assert writer.write_privileged_config(path, content, run_cmd_fn=runner)[0] == 0
    assert root_main == [(path, content.encode("utf-8"))]


@pytest.mark.parametrize(
    "payload", [b"substituted=1\n", b"\xff", b"\0", b"x" * (writer.MAX_CONTENT + 1)]
)
def test_substituted_or_malformed_payload_fails_before_write(
    monkeypatch, root_main, payload
):
    digest = hashlib.sha256(b"reviewed=1\n").hexdigest()
    assert receive(monkeypatch, [DOT, digest], payload) == 1
    assert root_main == []


@pytest.mark.parametrize(
    "path", ["/etc/shadow", "/tmp/test.conf", "/etc/ufw/../rkhunter.conf"]
)
def test_destination_allowlist_both_sides(monkeypatch, root_main, path):
    def forbidden(*args, **kwargs):
        pytest.fail("must reject before sudo")

    assert writer.write_privileged_config(path, "", run_cmd_fn=forbidden)[0] == 1
    assert receive(monkeypatch, [path, hashlib.sha256(b"").hexdigest()], b"") == 1
    assert root_main == []


def test_source_checkout_fails_closed(monkeypatch):
    monkeypatch.setattr(writer, "__file__", "/tmp/privileged_config.py")
    assert writer.main([DOT, ""]) == 1


def test_bootstrap_rejects_unprotected_code_before_exec(monkeypatch):
    executed = []
    monkeypatch.setattr(os, "execv", lambda *args: executed.append(args))
    monkeypatch.setattr(
        os,
        "lstat",
        lambda path: SimpleNamespace(st_uid=1000, st_mode=stat.S_IFREG | 0o644),
    )
    with pytest.raises(SystemExit):
        exec(writer.BOOTSTRAP, {})  # noqa: S102 - exercise the fixed bootstrap
    assert executed == []


@pytest.fixture
def fixture_destination(monkeypatch, tmp_path):
    # The atomic writer itself runs unchanged, on an anchored fixture directory.
    monkeypatch.setattr(
        writer,
        "_destination_directory",
        lambda p: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY),
    )
    monkeypatch.setattr(os, "fchown", lambda fd, uid, gid: None)
    return tmp_path / "target.conf"


def test_atomic_write_and_mode(fixture_destination):
    writer._atomic_write(str(fixture_destination), b"reviewed=1\n")
    assert fixture_destination.read_bytes() == b"reviewed=1\n"
    assert stat.S_IMODE(fixture_destination.stat().st_mode) == 0o644
    assert list(fixture_destination.parent.iterdir()) == [fixture_destination]


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "directory"])
def test_unsafe_target_cannot_redirect_write(fixture_destination, kind):
    outside = fixture_destination.parent / "outside"
    outside.write_bytes(b"sentinel")
    if kind == "symlink":
        fixture_destination.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, fixture_destination)
    elif kind == "fifo":
        os.mkfifo(fixture_destination)
    else:
        fixture_destination.mkdir()
    with pytest.raises(ValueError):
        writer._atomic_write(str(fixture_destination), b"reviewed=1\n")
    assert outside.read_bytes() == b"sentinel"
    assert not list(fixture_destination.parent.glob(".netmon-config-*"))


def test_failure_before_rename_keeps_previous_file(monkeypatch, fixture_destination):
    fixture_destination.write_bytes(b"previous")
    fixture_destination.chmod(0o600)
    original_stat = os.stat

    def root_owned_fixture(path, **kwargs):
        info = original_stat(path, **kwargs)
        if path == fixture_destination.name and kwargs.get("dir_fd") is not None:
            return SimpleNamespace(
                st_mode=info.st_mode, st_uid=0, st_nlink=info.st_nlink
            )
        return info

    monkeypatch.setattr(os, "stat", root_owned_fixture)

    def fail(*args, **kwargs):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        writer._atomic_write(str(fixture_destination), b"reviewed=1\n")
    assert fixture_destination.read_bytes() == b"previous"
    assert not list(fixture_destination.parent.glob(".netmon-config-*"))


def test_swapped_parent_stays_anchored(monkeypatch, fixture_destination):
    anchored = fixture_destination.parent
    moved = anchored.with_name(anchored.name + "-moved")
    outside = anchored.with_name(anchored.name + "-outside")
    outside.mkdir()
    (outside / fixture_destination.name).write_bytes(b"sentinel")
    original = os.replace

    def swap(src, dst, **kwargs):
        anchored.rename(moved)
        anchored.symlink_to(outside, target_is_directory=True)
        original(src, dst, **kwargs)

    monkeypatch.setattr(os, "replace", swap)
    writer._atomic_write(str(fixture_destination), b"reviewed=1\n")
    assert (outside / fixture_destination.name).read_bytes() == b"sentinel"
    assert (moved / fixture_destination.name).read_bytes() == b"reviewed=1\n"


def test_parent_links_rejected(monkeypatch, tmp_path):
    # /tmp is writable, so bypass only ownership checks to exercise no-follow.
    monkeypatch.setattr(writer, "_check_directory", lambda fd: None)
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(OSError):
        writer._destination_directory(str(link / "target.conf"))


def test_writable_parent_rejected(tmp_path):
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        tmp_path.chmod(0o777)
        with pytest.raises(ValueError):
            writer._check_directory(fd)
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    "workflow", ["dns", "dot", "rkhunter", "sysctl", "rollback", "ufw"]
)
@pytest.mark.parametrize("failure", [False, True])
def test_workflows_never_create_reopenable_source(monkeypatch, workflow, failure):
    def forbidden(*args, **kwargs):
        pytest.fail("user-owned source tempfile must not be created")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", forbidden)
    writes = []
    reloads = []

    def runner(args, timeout=0, input_text=None):
        if input_text is not None:
            assert args[:5] == ["sudo", "-n", "/usr/bin/python3", "-I", "-c"]
            assert args[6] in writer.DESTINATIONS
            assert args[7] == hashlib.sha256(input_text.encode("utf-8")).hexdigest()
            writes.append((args[6], input_text))
            return (1, "write failed") if failure else (0, "")
        assert args[2] not in {"install", "chmod", "mkdir"}
        if args[2] == "cp":
            assert args[3:5] == ["-a", UFW]  # protected backup only
        if args[2] == "cat":
            return 0, "net/ipv4/conf/all/log_martians=0\n"
        if args[2] in {"sysctl", "systemctl"}:
            reloads.append(args)
        return 0, ""

    if workflow == "dns":
        service = DNSControlService(
            runner,
            lambda _: True,
            dot_dropin_path=DOT,
            dot_dropin_dir=str(Path(DOT).parent),
        )
        ok, _ = service.write_dropin("[Resolve]\nDNS=1.1.1.1\n")
        assert ok is not failure
    elif workflow == "rkhunter":
        monkeypatch.setattr(rkhunter_manager, "_run_cmd", runner)
        assert (
            rkhunter_manager._write_config("MIRRORS_MODE=0\n", "/etc/rkhunter.conf")[0]
            == 0
        ) is not failure
    elif workflow == "sysctl":
        assert (
            audit._apply_sysctl_dropin(SYSCTL, "kernel.sysrq=0\n", run_cmd_fn=runner)[0]
            is not failure
        )
    elif workflow == "rollback":
        if failure:
            with pytest.raises(RuntimeError):
                audit._restore_sysctl_dropin(
                    SYSCTL, True, "kernel.sysrq=1\n", run_cmd_fn=runner
                )
        else:
            audit._restore_sysctl_dropin(
                SYSCTL, True, "kernel.sysrq=1\n", run_cmd_fn=runner
            )
    elif workflow == "ufw":
        assert (
            audit._apply_ufw_sysctl_overrides(
                UFW, {"net.ipv4.conf.all.log_martians": "1"}, run_cmd_fn=runner
            )[0]
            is not failure
        )
    else:
        statuses = []
        app = SimpleNamespace(
            dot_running=False,
            update_dns_controls_state_safe=lambda: None,
            ensure_sudo_session=lambda _: True,
            nb=SimpleNamespace(select=lambda _: None),
            tab_dns=None,
            update_dns_output=lambda *a, **k: None,
            log_safe=lambda _: None,
            after=lambda _, f: f(),
            dot_choice=SimpleNamespace(get=lambda: "test"),
            _start_dns_guard_transition=lambda: None,
        )
        monkeypatch.setattr(
            dot_controller, "_vpn_dns_active_state", lambda _: (False, "")
        )
        monkeypatch.setattr(dot_controller, "read_dot_dropin", lambda _, **kw: "")
        monkeypatch.setattr(
            dot_controller,
            "build_dot_dropin_content",
            lambda _: ("test", {}, "[Resolve]\nDNS=1.1.1.1\n"),
        )
        monkeypatch.setattr(dot_controller, "run_cmd", runner)
        monkeypatch.setattr(
            dot_controller, "collect_dot_status", lambda *a, **k: {"ok": True}
        )
        monkeypatch.setattr(
            dot_controller, "show_dot_status_result", lambda _, s: statuses.append(s)
        )
        monkeypatch.setattr(dot_controller, "call_in_ui_thread", lambda _, f: f())
        monkeypatch.setattr(
            dot_controller.threading,
            "Thread",
            lambda target, **k: SimpleNamespace(start=target),
        )
        dot_controller.enable_dot_async(app)
        assert statuses[-1]["ok"] is not failure
        assert not app.dot_running
    assert len(writes) == 1
    if failure:
        assert reloads == []


@pytest.fixture
def installed_destination(monkeypatch, tmp_path):
    """Run the writer on fixtures; root identity/ownership are simulated."""
    target = tmp_path / "netmon-dot.conf"
    target.write_text("previous=1\n")
    target.chmod(0o600)
    original_stat = os.stat

    def trusted_fixture(path, *args, **kwargs):
        info = original_stat(path, *args, **kwargs)
        if path == target.name and kwargs.get("dir_fd") is not None:
            return SimpleNamespace(
                st_mode=info.st_mode, st_uid=0, st_nlink=info.st_nlink
            )
        return info

    monkeypatch.setattr(writer, "__file__", writer.HELPER)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(os, "stat", trusted_fixture)
    monkeypatch.setattr(os, "fchown", lambda *args: None)
    monkeypatch.setattr(
        writer,
        "_destination_directory",
        lambda path: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY),
    )
    return target


@pytest.mark.parametrize(
    "stage, expected_rc, replaced",
    [
        ("success", 0, True),
        ("file-fsync", 1, False),
        ("replace", 1, False),
        ("directory-fsync", writer.WRITE_COMMITTED_ERROR, True),
        ("directory-close", writer.WRITE_COMMITTED_ERROR, True),
    ],
)
def test_helper_reports_whether_exchange_completed(
    monkeypatch, installed_destination, capsys, stage, expected_rc, replaced
):
    original_fsync = os.fsync
    original_close = os.close
    directory_fds = []
    original_directory = writer._destination_directory

    def directory(path):
        fd = original_directory(path)
        directory_fds.append(fd)
        return fd

    def fsync(fd):
        is_directory = fd in directory_fds
        if (stage == "file-fsync" and not is_directory) or (
            stage == "directory-fsync" and is_directory
        ):
            raise OSError("synthetic fsync failure")
        original_fsync(fd)

    def close(fd):
        original_close(fd)
        if stage == "directory-close" and fd in directory_fds:
            raise OSError("synthetic close failure after exchange")

    monkeypatch.setattr(writer, "_destination_directory", directory)
    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "close", close)
    if stage == "replace":

        def fail_replace(*args, **kwargs):
            raise OSError("synthetic replace failure")

        monkeypatch.setattr(os, "replace", fail_replace)
    payload = b"new=1\n"
    assert (
        receive(monkeypatch, [DOT, hashlib.sha256(payload).hexdigest()], payload)
        == expected_rc
    )
    assert installed_destination.read_bytes() == (
        payload if replaced else b"previous=1\n"
    )
    if expected_rc == writer.WRITE_COMMITTED_ERROR:
        assert "Destination replaced" in capsys.readouterr().err
    assert not list(installed_destination.parent.glob(".netmon-config-*"))


@pytest.mark.parametrize(
    "outcome",
    [
        "before-exchange",
        "after-exchange",
        "rollback-fsync-failed",
        "rollback-denied",
        "rollback-exception",
        "restart-failed",
        "lost-response",
        "runner-exception",
        "backup-unreadable",
    ],
)
def test_dot_handles_committed_errors_and_checks_rollback(
    monkeypatch, installed_destination, outcome
):
    previous = installed_destination.read_text()
    content = "[Resolve]\nDNS=1.1.1.1\n"
    statuses, logs, writes, restores, restarts = [], [], [], [], []
    original_fsync = os.fsync
    directory_syncs = 0

    def fsync(fd):
        nonlocal directory_syncs
        is_directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        if is_directory:
            directory_syncs += 1
        if outcome == "before-exchange" and not is_directory:
            raise OSError("synthetic pre-exchange failure")
        if (
            is_directory
            and (directory_syncs == 1 or outcome == "rollback-fsync-failed")
            and outcome not in {"lost-response", "runner-exception"}
        ):
            raise OSError("synthetic post-exchange directory fsync failure")
        original_fsync(fd)

    def runner(args, *, input_text, timeout):
        assert args[:6] == [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-c",
            writer.BOOTSTRAP,
        ]
        writes.append(input_text)
        rc = receive(monkeypatch, args[6:], input_text.encode("utf-8"))
        if len(writes) == 1 and outcome == "lost-response":
            assert rc == 0
            return 124, "synthetic timeout after completed write"
        if len(writes) == 1 and outcome == "runner-exception":
            assert rc == 0
            raise OSError("synthetic lost result after completed write")
        return rc, "synthetic write failure" if rc else ""

    def restore(backup):
        restores.append(backup)
        if outcome == "rollback-denied":
            return False, "synthetic rollback authorization failure"
        if outcome == "rollback-exception":
            raise OSError("synthetic rollback exception")
        rc, out = writer.write_privileged_config(DOT, backup, run_cmd_fn=runner)
        return rc == 0, out

    def restart():
        restarts.append(True)
        return outcome != "restart-failed", "synthetic resolver restart failure"

    def backup(app, *, strict=False):
        assert strict
        if outcome == "backup-unreadable":
            raise PermissionError("synthetic unreadable backup")
        return previous

    app = SimpleNamespace(
        dot_running=False,
        update_dns_controls_state_safe=lambda: None,
        ensure_sudo_session=lambda reason: True,
        nb=SimpleNamespace(select=lambda tab: None),
        tab_dns=None,
        update_dns_output=lambda *args, **kwargs: None,
        log_safe=logs.append,
        after=lambda delay, fn: fn(),
        dot_choice=SimpleNamespace(get=lambda: "fixture"),
        _restore_dot_dropin_backup=restore,
        _restart_resolved_for_dns_policy=restart,
    )
    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(dot_controller, "run_cmd", runner)
    monkeypatch.setattr(dot_controller, "read_dot_dropin", backup)
    monkeypatch.setattr(
        dot_controller, "_vpn_dns_active_state", lambda app: (False, "")
    )
    monkeypatch.setattr(
        dot_controller, "build_dot_dropin_content", lambda app: ("fixture", {}, content)
    )
    monkeypatch.setattr(dot_controller, "call_in_ui_thread", lambda app, fn: fn())
    monkeypatch.setattr(
        dot_controller,
        "show_dot_status_result",
        lambda app, result: statuses.append(result),
    )
    monkeypatch.setattr(
        dot_controller.threading,
        "Thread",
        lambda target, **kwargs: SimpleNamespace(start=target),
    )
    dot_controller.enable_dot_async(app)
    assert not app.dot_running
    assert statuses[-1]["ok"] is False
    text = statuses[-1]["text"]
    if outcome in {"before-exchange", "backup-unreadable"}:
        assert restores == restarts == []
        assert installed_destination.read_text() == previous
        assert "Rollback-Schritte erfolgreich" not in text
        if outcome == "backup-unreadable":
            assert writes == []
    else:
        assert restores == [previous]
        incomplete = outcome in {
            "rollback-fsync-failed",
            "rollback-denied",
            "rollback-exception",
            "restart-failed",
        }
        assert ("Rollback nicht vollstaendig bestaetigt" in text) is incomplete
        assert ("Rollback-Schritte erfolgreich" in text) is not incomplete
        assert any("Rollback" in line for line in logs)
        if outcome in {
            "rollback-fsync-failed",
            "rollback-denied",
            "rollback-exception",
        }:
            assert restarts == []
        else:
            assert restarts == [True]
        assert installed_destination.read_text() == (
            content
            if outcome in {"rollback-denied", "rollback-exception"}
            else previous
        )


def test_strict_dot_backup_does_not_turn_read_error_into_empty_content(monkeypatch):
    def unreadable(*args, **kwargs):
        raise PermissionError("synthetic backup read failure")

    monkeypatch.setattr("builtins.open", unreadable)
    with pytest.raises(PermissionError, match="backup read failure"):
        dot_controller.read_dot_dropin(SimpleNamespace(), strict=True)
