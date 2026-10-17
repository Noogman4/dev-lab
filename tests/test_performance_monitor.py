import json
import os
import sys

import pytest

from netmon.core import command
from netmon.core import performance_monitor
from netmon.core import support_bundle


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_measure_disabled_does_not_write(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "off")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(area="test", operation="disabled"):
        pass

    assert not log_path.exists()


def test_measure_enabled_writes_jsonl_with_safe_metadata(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "detailed")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(
        area="dns",
        operation="health_check",
        command_name="dns_resolution_check",
        metadata={"count": 2, "api_key": "secret", "detail": "ok"},
        mode="detailed",
    ) as measurement:
        measurement.set_status(return_code=0)

    records = read_jsonl(log_path)
    assert len(records) == 1
    record = records[0]
    assert record["area"] == "dns"
    assert record["operation"] == "health_check"
    assert record["command_name"] == "dns_resolution_check"
    assert record["return_code"] == 0
    assert record["status"] == "success"
    assert record["metadata"]["api_key"] == "[REDACTED]"
    assert record["metadata"]["detail"] == "ok"
    assert record["duration_ms"] >= 0
    assert record["gui_thread"] is True


def test_measure_reraises_exceptions_and_logs_error(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with pytest.raises(RuntimeError):
        with performance_monitor.measure(area="test", operation="raises"):
            raise RuntimeError("boom")

    [record] = read_jsonl(log_path)
    assert record["status"] == "error"
    assert record["error"] == "RuntimeError"


def test_log_rotation(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    log_path.write_text("x" * 80, encoding="utf-8")
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))
    monkeypatch.setenv("NETMON_PERFORMANCE_MAX_BYTES", "10")
    monkeypatch.setenv("NETMON_PERFORMANCE_BACKUPS", "2")

    with performance_monitor.measure(area="test", operation="rotate"):
        pass

    assert log_path.exists()
    assert os.path.exists(f"{log_path}.1")
    assert read_jsonl(log_path)[0]["operation"] == "rotate"


def test_safe_command_name_omits_sudo_flags_and_arguments():
    assert (
        performance_monitor.safe_command_name(["sudo", "-n", "ufw", "status"]) == "ufw"
    )
    assert performance_monitor.safe_command_name(["/usr/bin/wg", "show"]) == "wg"
    assert performance_monitor.safe_command_name([]) == "unknown"


def test_measure_runtime_decorator(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    @performance_monitor.measure_runtime(area="decorator", operation="call")
    def add_one(value):
        return value + 1

    assert add_one(2) == 3
    [record] = read_jsonl(log_path)
    assert record["area"] == "decorator"
    assert record["operation"] == "call"


def test_run_cmd_logs_safe_command_name_when_enabled(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "detailed")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    rc, _out = command.run_cmd([sys.executable, "-c", "import sys; sys.exit(3)"])

    assert rc == 3
    [record] = read_jsonl(log_path)
    assert record["area"] == "system_command"
    assert record["operation"] == "run_cmd"
    assert record["command_name"] == os.path.basename(sys.executable)
    assert record["return_code"] == 3
    assert record["status"] == "error"
    assert "-c" not in json.dumps(record)


def test_create_support_package_logs_file_count_only(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    docs_dir = tmp_path / "docs"
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))
    monkeypatch.setattr(
        support_bundle, "get_netmon_documents_dir", lambda: str(docs_dir)
    )
    monkeypatch.setattr(
        support_bundle, "support_bundle_inputs", lambda: [str(report_path)]
    )

    package_path = support_bundle.create_support_package(metadata={"token": "secret"})

    assert package_path.endswith(".zip")
    [record] = read_jsonl(log_path)
    assert record["area"] == "diagnostics"
    assert record["operation"] == "create_support_package"
    assert record["metadata"] == {"file_count": 1}
    assert "secret" not in json.dumps(record)


# ── Runde-11-Haertungen ──────────────────────────────────────────────────────
# R11-H3: Wert-seitige Redaction. Bis Runde 11 pruefte _safe_metadata nur den
# Metadaten-SCHLUESSEL gegen _SENSITIVE_KEY_PARTS; ein Secret, das als WERT
# unter einem harmlosen Schluessel uebergeben wird, landete im Klartext im
# JSONL. Kein damaliger Aufrufer tat das - die Tests halten die Zusage fest,
# damit kuenftige Aufrufer nicht in die Falle laufen.


def test_metadata_values_are_redacted_not_only_keys(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "detailed")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(
        area="test",
        operation="value_redaction",
        metadata={"detail": "api_key=super-secret-value", "note": "harmlos"},
        mode="detailed",
    ):
        pass

    [record] = read_jsonl(log_path)
    assert "super-secret-value" not in json.dumps(record)
    assert record["metadata"]["detail"] == "api_key=[REDACTED]"
    assert record["metadata"]["note"] == "harmlos"


def test_nested_metadata_values_are_redacted(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "detailed")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(
        area="test",
        operation="nested_redaction",
        metadata={
            "items": ["passphrase=hunter2", "ok"],
            "inner": {"line": "token: abcdef123456"},
        },
        mode="detailed",
    ):
        pass

    [record] = read_jsonl(log_path)
    serialized = json.dumps(record)
    assert "hunter2" not in serialized
    assert "abcdef123456" not in serialized


def test_error_text_is_redacted(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(area="test", operation="err") as measurement:
        measurement.set_status("error", error="mount failed: passphrase=hunter2")

    [record] = read_jsonl(log_path)
    assert "hunter2" not in json.dumps(record)
    assert record["error"] == "mount failed: passphrase=[REDACTED]"


# R11-H4: Der Log-Pfad wird ohne Symlink-Verfolgung und nur fuer den eigenen
# Nutzer lesbar geoeffnet.


def test_write_measurement_refuses_to_follow_symlink(monkeypatch, tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("unberuehrt\n", encoding="utf-8")
    log_path = tmp_path / "performance.jsonl"
    os.symlink(victim, log_path)

    written = performance_monitor.write_measurement(
        {"area": "test"}, log_path=str(log_path)
    )

    assert written is False
    assert victim.read_text(encoding="utf-8") == "unberuehrt\n"


def test_rotation_does_not_act_on_symlinked_log(monkeypatch, tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("x" * 200, encoding="utf-8")
    log_path = tmp_path / "performance.jsonl"
    os.symlink(victim, log_path)
    monkeypatch.setenv("NETMON_PERFORMANCE_MAX_BYTES", "50")
    monkeypatch.setenv("NETMON_PERFORMANCE_BACKUPS", "2")

    performance_monitor._rotate_log(str(log_path))

    assert victim.exists()
    assert not os.path.exists(f"{log_path}.1")


def test_new_log_file_is_owner_only(monkeypatch, tmp_path):
    log_path = tmp_path / "performance.jsonl"
    monkeypatch.setenv("NETMON_PERFORMANCE_MONITORING", "basic")
    monkeypatch.setenv("NETMON_PERFORMANCE_LOG_PATH", str(log_path))

    with performance_monitor.measure(area="test", operation="perms"):
        pass

    assert log_path.exists()
    assert oct(log_path.stat().st_mode & 0o777) == "0o600"
