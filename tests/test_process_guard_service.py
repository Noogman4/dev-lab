from netmon.services.process_guard_service import ProcessGuardService


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


def test_evaluate_process_does_not_flag_temp_argument_as_temp_execution():
    service = ProcessGuardService()
    proc = {
        "pid": 8422,
        "ppid": 1337,
        "name": "crashhelper",
        "exe": "/home/happy/Dokumente/NetMon/Secure Browser/Chad/firefox/crashhelper",
        "cmdline": [
            "/home/happy/Dokumente/NetMon/Secure Browser/Chad/firefox/crashhelper",
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


def test_run_check_summarizes_findings_from_snapshot(monkeypatch):
    service = ProcessGuardService()
    monkeypatch.setattr(service, "is_available", lambda: True)
    monkeypatch.setattr(
        service,
        "snapshot_processes",
        lambda: [
            {
                "pid": 1,
                "ppid": 0,
                "name": "systemd",
                "exe": "/usr/lib/systemd/systemd",
                "cmdline": ["/usr/lib/systemd/systemd"],
                "cwd": "/",
                "username": "root",
                "create_time": 1.0,
                "status": "sleeping",
            },
            {
                "pid": 2,
                "ppid": 1,
                "name": "python3",
                "exe": "/usr/bin/python3",
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


def test_run_check_skips_trusted_findings(monkeypatch):
    service = ProcessGuardService()
    process = {
        "pid": 2,
        "ppid": 1,
        "name": "python3",
        "exe": "/usr/bin/python3",
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


def test_evaluate_process_does_not_flag_networkmanager_name_only():
    service = ProcessGuardService()
    proc = {
        "pid": 929,
        "ppid": 1,
        "name": "NetworkManager",
        "exe": "/usr/sbin/NetworkManager",
        "cmdline": ["/usr/sbin/NetworkManager", "--no-daemon"],
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
