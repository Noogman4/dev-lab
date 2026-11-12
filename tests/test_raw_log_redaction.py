"""Synthetic credentials only; no existing host logs or real GUI startups."""

import ast
import json
import os
from pathlib import Path
import stat
import sys
import traceback
from types import SimpleNamespace

import pytest

from netmon import app as app_module
from netmon import main
from netmon.core import crash, diagnostics, log_redaction as redact, private_logs

SECRET = "SYNTHETIC_VALUE_NEVER_PERSIST"
PEM = (
    "-----BEGIN OPENSSH PRIVATE KEY-----\n"
    + SECRET
    + "\n-----END OPENSSH PRIVATE KEY-----"
)


@pytest.mark.parametrize(
    "text",
    [
        f"password={SECRET}",
        f'password="{SECRET} two words"',
        f"PrivateKey = {SECRET}",
        f"PresharedKey={SECRET}",
        f"api-key: {SECRET}",
        f"client_secret='{SECRET}'",
        f"psk={SECRET}",
        f"Authorization: Bearer {SECRET}",
        f"Authorization: Basic {SECRET}",
        f"Cookie: session={SECRET}; cookie2=also-private",
        f"Set-Cookie: session={SECRET}; secure",
        f"curl --password {SECRET}",
        f"tool --api-key '{SECRET} two words'",
        repr(["tool", "--token", SECRET]),
        json.dumps(["--password", SECRET]),
        json.dumps({"password": SECRET}),
        repr({"private_key": SECRET}),
        PEM,
        "PrivateKey = " + PEM,
        f"https://user:{SECRET}@example.invalid/path",
        "sk-proj-" + SECRET,
    ],
)
def test_shared_filter_masks_known_raw_forms_and_is_idempotent(text):
    result = redact.redact_sensitive_text(text)
    assert SECRET not in result
    assert "REDACTED" in result
    assert redact.redact_sensitive_text(result) == result


def test_structured_redaction_handles_keys_and_argv_pairs():
    data = {
        "private_key": SECRET,
        "password": SECRET + " two words",
        "argv": [
            "tool",
            "--token",
            SECRET,
            "--password",
            SECRET + " two words",
            "--port",
            "443",
        ],
        "context": {"authorization": "Bearer " + SECRET, "other": "password=" + SECRET},
    }
    result = diagnostics.redact_diagnostic_value(data)
    assert SECRET not in json.dumps(result)
    assert result["argv"][-2:] == ["--port", "443"]
    assert result["private_key"] == "[REDACTED]"
    assert diagnostics.redact_sensitive_text is redact.redact_sensitive_text


def test_private_writer_covers_split_values_multiline_keys_and_flush(tmp_path):
    output = tmp_path / "logs" / "private.log"
    text = (
        "password="
        + SECRET
        + "\n"
        + PEM
        + "\n/home/synthetic-account/private\nuser@example.invalid\n"
    )
    with private_logs.open_private_log(output) as log:
        for char in text:
            assert log.write(char) == 1
            log.flush()
        assert output.read_bytes() == b""  # Incomplete records are not published.
    result = output.read_text()
    assert SECRET not in result and "synthetic-account" not in result
    assert "user@example.invalid" not in result
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700


def test_record_budget_cannot_split_a_private_key_into_public_text(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(private_logs, "MAX_LOG_RECORD_CHARS", 100)
    output = tmp_path / "log"
    with private_logs.open_private_log(output) as log:
        log.writelines(
            [
                "-----BEGIN PRIVATE KEY-----\n",
                SECRET * 20,
                "\n-----END PRIVATE KEY-----",
            ]
        )
    result = output.read_text()
    assert SECRET not in result and "PRIVATE KEY" not in result
    assert "truncated" in result


@pytest.mark.parametrize("prefix", ["password=", "curl --password "])
def test_unquoted_multiword_values_do_not_leave_fragments(prefix):
    result = redact.redact_sensitive_text(prefix + SECRET + " private second part")
    assert SECRET not in result and "private second part" not in result


def test_cut_json_record_is_omitted_instead_of_publishing_partial_secret(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(private_logs, "MAX_LOG_RECORD_CHARS", 60)
    output = tmp_path / "log"
    with private_logs.open_private_log(output) as log:
        log.write(
            json.dumps(
                {"command": 'curl --password "' + SECRET + ' private second part"'}
            )
        )
    assert output.read_text() == "[NetMon log record truncated]\n"


def test_filter_failure_does_not_fall_back_to_raw_output(tmp_path, monkeypatch):
    def fail(_value):
        raise RuntimeError("synthetic filter failure")

    monkeypatch.setattr(private_logs, "redact_sensitive_text", fail)
    output = tmp_path / "log"
    with pytest.raises(RuntimeError):
        with private_logs.open_private_log(output) as log:
            log.write("password=" + SECRET)
    assert output.read_bytes() == b""


def configure_logs(tmp_path, monkeypatch):
    reports = tmp_path / "diagnostics"
    monkeypatch.setattr(diagnostics, "get_netmon_documents_dir", lambda: str(tmp_path))
    monkeypatch.setattr(diagnostics, "diagnostic_system_info", lambda: {})
    monkeypatch.setattr(main, "get_netmon_documents_dir", lambda: str(tmp_path))
    monkeypatch.setattr(crash, "CRASH_LOG_PATH", str(reports / "crash.log"))
    monkeypatch.setattr(
        sys, "argv", ["netmon", "--token", SECRET, "--password", SECRET + " two words"]
    )
    monkeypatch.setattr(
        diagnostics.os, "getcwd", lambda: "/home/synthetic-account/private"
    )
    return reports


@pytest.mark.parametrize("kind", ["startup", "crash"])
def test_real_traceback_and_metadata_writers_redact_credentials(
    tmp_path, monkeypatch, kind
):
    reports = configure_logs(tmp_path, monkeypatch)
    try:
        raise RuntimeError("password=" + SECRET + "\n" + PEM)
    except RuntimeError as error:
        if kind == "startup":
            main._write_startup_error_log(
                "Startup error", detail="api_key=" + SECRET, exc=error
            )
        else:
            crash._append_crash_dump(
                "password=" + SECRET, type(error), error, error.__traceback__
            )
    files = list(reports.iterdir())
    assert files and any(path.suffix == ".log" for path in files)
    for path in files:
        result = path.read_text()
        assert SECRET not in result and "synthetic-account" not in result
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_runtime_gui_stdout_files_and_network_memory_are_redacted(tmp_path, capsys):
    app = SimpleNamespace(
        netmon_state_dir=str(tmp_path),
        debug_network_logging=True,
        _translate_runtime_log_message=lambda text: text,
        _runtime_log_paths=lambda: [str(tmp_path / "logs" / "runtime.log")],
        _network_debug_log_path=lambda: str(tmp_path / "logs" / "network_debug.log"),
    )
    app._append_runtime_log_line = lambda line: app_module.App._append_runtime_log_line(
        app, line
    )
    app_module.App.log(app, "password=" + SECRET)
    assert SECRET not in capsys.readouterr().out
    captured = []
    app.text = SimpleNamespace(
        insert=lambda *_args: captured.append(_args[-1]), see=lambda *_a: None
    )
    app_module.App.log(app, "api_key=" + SECRET)
    app_module.App.log_network_debug(app, repr(["curl", "--token", SECRET]))
    app_module.App._append_runtime_log_line(app, "passphrase=" + SECRET)
    assert SECRET not in "".join(captured + app._network_debug_entries)
    for path in (tmp_path / "logs").iterdir():
        assert SECRET not in path.read_text()


def test_port_debug_records_remain_valid_json_with_sensitive_fields_redacted(tmp_path):
    app = SimpleNamespace(
        netmon_state_dir=str(tmp_path), log_debug_safe=lambda _text: None
    )
    app_module.App._append_port_check_debug_log(
        app,
        {
            "token": SECRET,
            "context": {"password": SECRET},
            "host": "example.invalid",
            "command": 'curl --password "' + SECRET + ' two words" --head',
        },
    )
    result = json.loads((tmp_path / "logs" / "port_check_debug.log").read_text())
    assert SECRET not in json.dumps(result)
    assert result["host"] == "example.invalid" and result["token"] == "[REDACTED]"


def test_json_log_fragments_keep_valid_escaping_and_redaction(tmp_path):
    output = tmp_path / "json.log"
    content = json.dumps(
        {"command": 'curl --password "' + SECRET + ' two words"', "other": "plain"}
    )
    with private_logs.open_private_log(output) as log:
        for char in content:
            log.write(char)
    result = json.loads(output.read_text())
    assert SECRET not in result["command"] and result["other"] == "plain"


def test_loading_legacy_runtime_log_masks_display_without_rewriting(tmp_path):
    output = tmp_path / "legacy.log"
    original = "password=" + SECRET + "\n"
    output.write_text(original)
    displayed = []
    app = SimpleNamespace(
        _runtime_log_paths=lambda: [str(output)],
        text=SimpleNamespace(
            delete=lambda *_a: None,
            insert=lambda *_a: displayed.append(_a[-1]),
            see=lambda *_a: None,
        ),
    )
    assert app_module.App._load_runtime_log_into_widget(app)
    assert SECRET not in "".join(displayed)
    assert output.read_text() == original


def test_direct_private_json_writes_apply_same_policy(tmp_path):
    output = tmp_path / "report.json"
    private_logs.write_private_diagnostic_json(
        output, {"password": SECRET, "argv": ["--token", SECRET]}
    )
    assert SECRET not in output.read_text()
    assert json.loads(output.read_text())["password"] == "[REDACTED]"


def bootstrap_functions(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir(mode=0o700)
    tree = ast.parse(Path(app_module.__file__).read_text())
    block = next(
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and ast.unparse(node.test) == "__name__ == '__main__'"
    )
    functions = [node for node in block.body if isinstance(node, ast.FunctionDef)]
    namespace = {
        "os": os,
        "_bootstrap_traceback": traceback,
        "get_netmon_state_dir": lambda: str(tmp_path / "state" / "netmon"),
        "open_private_log": private_logs.open_private_log,
    }
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            str(app_module.__file__),
            "exec",
        ),
        namespace,
    )
    monkeypatch.setitem(
        sys.modules,
        "tkinter",
        SimpleNamespace(
            Tk=lambda: (_ for _ in ()).throw(RuntimeError("No GUI allowed"))
        ),
    )
    monkeypatch.setitem(sys.modules, "tkinter.messagebox", SimpleNamespace())
    return namespace


@pytest.mark.parametrize("existing", [False, True])
def test_direct_app_bootstrap_failure_is_private_and_redacted(
    tmp_path, monkeypatch, existing
):
    functions = bootstrap_functions(tmp_path, monkeypatch)
    output = Path(functions["get_startup_error_log_path"]())
    if existing:
        output.parent.mkdir(parents=True)
        output.parent.chmod(0o755)
        output.write_text("existing log\n")
        output.chmod(0o644)
    old = os.umask(0)
    try:
        try:
            raise RuntimeError("password=" + SECRET)
        except RuntimeError as error:
            functions["_report_bootstrap_failure"](error)
    finally:
        os.umask(old)
    assert SECRET not in output.read_text()
    assert "RuntimeError" in output.read_text()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700


@pytest.mark.parametrize("attack", ["symlink", "hardlink", "parent-symlink", "fifo"])
def test_direct_bootstrap_refuses_unsafe_logs(tmp_path, monkeypatch, attack):
    functions = bootstrap_functions(tmp_path, monkeypatch)
    output = Path(functions["get_startup_error_log_path"]())
    output.parent.mkdir(parents=True)
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("untouched")
    sentinel.chmod(0o644)
    if attack == "parent-symlink":
        output.parent.rmdir()
        output.parent.symlink_to(tmp_path, target_is_directory=True)
    elif attack == "symlink":
        output.symlink_to(sentinel)
    elif attack == "hardlink":
        os.link(sentinel, output)
    else:
        os.mkfifo(output)
    try:
        raise RuntimeError("password=" + SECRET)
    except RuntimeError as error:
        functions["_report_bootstrap_failure"](error)
    assert sentinel.read_text() == "untouched"
    assert stat.S_IMODE(sentinel.stat().st_mode) == 0o644
