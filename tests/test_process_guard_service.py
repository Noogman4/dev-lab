import os
from pathlib import Path

import pytest

from netmon.services.process_guard_service import ProcessGuardService


@pytest.fixture
def existing_executable(tmp_path):
    """Create inert files only in the isolated home, never in a host home."""
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"
    home = Path.home()
    assert home == Path("/work/home")
    runtime_dir = home / "process-guard-fixtures" / tmp_path.name
    runtime_dir.mkdir(mode=0o700, parents=True)

    def create(name):
        path = runtime_dir / name
        path.touch(mode=0o600, exist_ok=False)
        assert not path.stat().st_mode & 0o111
        return str(path)

    return create


def test_process_guard_service_is_available_with_ps_fallback(monkeypatch):
    monkeypatch.setattr(
        "netmon.services.process_guard_service.psutil",
        None,
    )
    monkeypatch.setattr(
        "netmon.services.process_guard_service.shutil.which",
        lambda name: "/usr/bin/ps" if name == "ps" else None,
    )

    service = ProcessGuardService()

    assert service.is_available() is True
    assert service.availability_reason() == ""


def test_process_guard_service_snapshot_processes_uses_ps_fallback(monkeypatch):
    monkeypatch.setattr(
        "netmon.services.process_guard_service.psutil",
        None,
    )
    monkeypatch.setattr(
        "netmon.services.process_guard_service.shutil.which",
        lambda name: "/usr/bin/ps" if name == "ps" else None,
    )

    class DummyCompleted:
        stdout = (
            "123 1 sven python3 15 S python3 /tmp/run.py\n"
            "456 123 root bash 2 R bash -c curl example.org\n"
        )

    monkeypatch.setattr(
        "netmon.services.process_guard_service.subprocess.run",
        lambda *args, **kwargs: DummyCompleted(),
    )
    monkeypatch.setattr(
        ProcessGuardService,
        "_read_proc_link",
        lambda self, pid, entry: {
            (123, "exe"): "/usr/bin/python3",
            (123, "cwd"): "/tmp",
            (456, "exe"): "/usr/bin/bash",
            (456, "cwd"): "/root",
        }.get((pid, entry), ""),
    )

    service = ProcessGuardService()
    processes = service.snapshot_processes()

    assert len(processes) == 2
    assert processes[0]["pid"] == 123
    assert processes[0]["exe"] == "/usr/bin/python3"
    assert processes[0]["cwd"] == "/tmp"
    assert processes[0]["cmdline"] == ["python3", "/tmp/run.py"]
    assert processes[1]["pid"] == 456
    assert processes[1]["status"] == "R"


def test_evaluate_process_flags_temp_shell_started_by_browser():
    service = ProcessGuardService()
    proc = {
        "pid": 8421,
        "ppid": 1337,
        "name": "bash",
        "exe": "/tmp/bash",
        "cmdline": ["bash", "/tmp/update.sh"],
        "cwd": "/tmp",
        "username": "sven",
        "create_time": 1.0,
        "status": "running",
    }
    parent = {"pid": 1337, "name": "firefox"}

    finding = service.evaluate_process(proc, parent=parent)

    assert finding is not None
    assert finding["risk_level"] == "high"
    assert finding["risk_score"] >= 6
    assert any("temporärem Pfad" in reason for reason in finding["reasons"])
    assert any("Parent-Prozess ist firefox" in reason for reason in finding["reasons"])


def test_evaluate_process_does_not_flag_temp_argument_as_temp_execution(
    existing_executable,
):
    service = ProcessGuardService()
    executable = existing_executable("crashhelper")
    proc = {
        "pid": 8422,
        "ppid": 1337,
        "name": "crashhelper",
        "exe": executable,
        "cmdline": [
            executable,
            "/tmp/firefox-crash",
        ],
        "cwd": "/tmp",
        "username": "happy",
        "create_time": 1.0,
        "status": "sleeping",
    }
    parent = {"pid": 1337, "name": "firefox"}

    finding = service.evaluate_process(proc, parent=parent)

    assert finding is None


def test_evaluate_process_reports_missing_executable_with_temp_argument(
    existing_executable,
):
    service = ProcessGuardService()
    present = Path(existing_executable("crashhelper"))
    missing = str(present.with_name("missing-crashhelper"))
    assert not Path(missing).exists()
    proc = {
        "pid": 8422,
        "ppid": 1337,
        "name": "crashhelper",
        "exe": missing,
        "cmdline": [missing, "/tmp/firefox-crash"],
        "cwd": "/tmp",
        "username": "happy",
        "create_time": 1.0,
        "status": "sleeping",
    }

    finding = service.evaluate_process(proc, parent={"pid": 1337, "name": "firefox"})

    assert finding is not None
    assert finding["risk_score"] == 2
    assert finding["risk_level"] == "low"
    assert finding["reasons"] == ["Executable-Pfad ist nicht mehr vorhanden."]


def test_evaluate_process_flags_run_user_executable_as_temp_execution():
    service = ProcessGuardService()
    proc = {
        "pid": 8423,
        "ppid": 1,
        "name": "helper",
        "exe": "/run/user/1000/helper",
        "cmdline": ["/run/user/1000/helper"],
        "cwd": "/home/happy",
        "username": "happy",
        "create_time": 1.0,
        "status": "running",
    }

    finding = service.evaluate_process(proc, parent={"pid": 1, "name": "systemd"})

    assert finding is not None
    assert finding["risk_level"] == "high"
    assert "Ausführung aus temporärem Pfad: /run/user/1000/helper" in finding["reasons"]


def test_evaluate_process_maps_downloads_only_to_medium_risk(existing_executable):
    service = ProcessGuardService()
    proc = {
        "pid": 8424,
        "ppid": 1,
        "name": "python3",
        "exe": existing_executable("python3"),
        "cmdline": ["python3"],
        "cwd": str(Path.home() / "Downloads"),
        "username": "happy",
        "create_time": 1.0,
        "status": "running",
    }

    finding = service.evaluate_process(proc, parent={"pid": 1, "name": "systemd"})

    assert finding is not None
    assert finding["risk_score"] == 3
    assert finding["risk_level"] == "medium"


def test_evaluate_process_uses_kernel_thread_display_for_empty_paths():
    service = ProcessGuardService()
    proc = {
        "pid": 8425,
        "ppid": 2,
        "name": "abcdefghijkl",
        "exe": "",
        "cmdline": [],
        "cwd": "",
        "username": "root",
        "create_time": 1.0,
        "status": "sleeping",
    }

    finding = service.evaluate_process(proc, parent={"pid": 2, "name": "kthreadd"})

    assert finding is not None
    assert finding["risk_level"] == "low"
    assert finding["exe"] == "Kernel-Thread"


def test_run_check_summarizes_findings_from_snapshot(monkeypatch, existing_executable):
    service = ProcessGuardService()
    systemd = existing_executable("systemd")
    python = existing_executable("python3")
    monkeypatch.setattr(service, "is_available", lambda: True)
    monkeypatch.setattr(
        service,
        "snapshot_processes",
        lambda: [
            {
                "pid": 1,
                "ppid": 0,
                "name": "systemd",
                "exe": systemd,
                "cmdline": [systemd],
                "cwd": "/",
                "username": "root",
                "create_time": 1.0,
                "status": "sleeping",
            },
            {
                "pid": 2,
                "ppid": 1,
                "name": "python3",
                "exe": python,
                "cmdline": ["python3", "-c", "print(1)"],
                "cwd": "/home/user/Downloads",
                "username": "user",
                "create_time": 2.0,
                "status": "running",
            },
        ],
    )

    result = service.run_check()

    assert result["available"] is True
    assert result["processes_count"] == 2
    assert len(result["findings"]) == 1
    assert result["risk"] in {"mittel", "hoch"}


def test_detect_new_findings_only_reports_unknown_signatures():
    service = ProcessGuardService()
    processes = [
        {
            "pid": 50,
            "ppid": 1,
            "name": "bash",
            "exe": "/tmp/bash",
            "cmdline": ["bash", "/tmp/run.sh"],
            "cwd": "/tmp",
            "username": "user",
            "create_time": 50.0,
            "status": "running",
        }
    ]

    findings, known = service.detect_new_findings(processes, known_processes=set())
    findings_again, known_again = service.detect_new_findings(
        processes, known_processes=known
    )

    assert len(findings) == 1
    assert findings_again == []
    assert known_again == known


def test_run_check_skips_trusted_findings(monkeypatch, existing_executable):
    service = ProcessGuardService()
    process = {
        "pid": 2,
        "ppid": 1,
        "name": "python3",
        "exe": existing_executable("python3"),
        "cmdline": ["python3", "-c", "print(1)"],
        "cwd": "/home/user/Downloads",
        "username": "user",
        "create_time": 2.0,
        "status": "running",
    }
    monkeypatch.setattr(service, "snapshot_processes", lambda: [process])
    monkeypatch.setattr(service, "is_available", lambda: True)

    finding = service.evaluate_process(process, parent={"pid": 1, "name": "systemd"})
    trustlist = {"trusted": {service.trust_signature(finding): {"name": "python3"}}}

    result = service.run_check(trustlist=trustlist)

    assert result["findings"] == []
    assert result["counts"] == {"high": 0, "medium": 0, "low": 0}


def test_reset_trustlist_clears_saved_entries(tmp_path):
    service = ProcessGuardService()
    trustlist_path = tmp_path / "process_guard_trustlist.json"

    ok, err = service.save_trustlist(
        str(trustlist_path),
        {"trusted": {"bash|/usr/bin/bash|sven": {"name": "bash"}}},
    )
    assert ok is True
    assert err == ""

    ok, err = service.reset_trustlist(str(trustlist_path))

    assert ok is True
    assert err == ""
    assert service.load_trustlist(str(trustlist_path)) == {"trusted": {}}


def test_match_suspicious_cmdline_avoids_context_false_positive():
    service = ProcessGuardService()

    text = (
        "--shared-files=v8_context_snapshot_data:100 "
        "--trace-process-track=uuid:3190708994745248135"
    )

    assert service._match_suspicious_cmdline(text) is False


def test_match_suspicious_cmdline_still_detects_real_nc_usage():
    service = ProcessGuardService()

    assert service._match_suspicious_cmdline("sh -c nc 1.2.3.4 4444") is True


def test_evaluate_process_does_not_flag_networkmanager_name_only(existing_executable):
    service = ProcessGuardService()
    executable = existing_executable("NetworkManager")
    proc = {
        "pid": 929,
        "ppid": 1,
        "name": "NetworkManager",
        "exe": executable,
        "cmdline": [executable, "--no-daemon"],
        "cwd": "",
        "username": "root",
        "create_time": 1.0,
        "status": "sleeping",
    }

    finding = service.evaluate_process(proc, parent={"pid": 1, "name": "systemd"})

    assert finding is None


def test_evaluate_process_does_not_flag_kworker_name_only():
    service = ProcessGuardService()
    proc = {
        "pid": 1152,
        "ppid": 2,
        "name": "kworker/R-comp_1.0.0",
        "exe": "",
        "cmdline": [],
        "cwd": "",
        "username": "root",
        "create_time": 1.0,
        "status": "sleeping",
    }

    finding = service.evaluate_process(proc, parent={"pid": 2, "name": "kthreadd"})

    assert finding is None
