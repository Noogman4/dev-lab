from types import SimpleNamespace

from netmon.features import security_audit_controller as controller


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyButton:
    def __init__(self):
        self.state = None

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]


def _valid_result():
    return {
        "propupd_allowed": True,
        "risk": "low",
        "scan_completed": True,
        "dpkg_verified": True,
        "critical": [],
        "review": [],
        "critical_flags": {
            "rootkits": False,
            "backdoors": False,
            "suspicious_runtime": False,
            "system_programs": False,
            "critical_network": False,
        },
    }


def _app():
    output = []
    logs = []
    app = SimpleNamespace(
        rkhunter_running=False,
        rkhunter_updating=False,
        rkhunter_active_process=None,
        rkhunter_last_result={},
        rkhunter_last_scan_output="",
        rkhunter_propupd_available=False,
        rkhunter_summary_var=DummyVar(),
        rkhunter_status_var=DummyVar(),
        btn_rkhunter_update=DummyButton(),
        btn_rkhunter_scan=DummyButton(),
        btn_rkhunter_propupd=DummyButton(),
        btn_rkhunter_revoke_reference=DummyButton(),
        btn_rkhunter_show_scan=DummyButton(),
        btn_rkhunter_log=DummyButton(),
        dep_status={"rkhunter": True},
        tr=lambda _key, fallback: fallback,
        ensure_sudo_session=lambda _reason: True,
        update_rkhunter_output=lambda text, append=False: output.append((text, append)),
        log_safe=logs.append,
        open_rkhunter_tab=lambda: None,
    )
    app.output = output
    app.logs = logs
    app._rkhunter_propupd_worker = lambda: None
    app._finish_rkhunter_propupd = lambda rc, text: None
    app._rkhunter_revoke_reference_worker = lambda: None
    app._finish_rkhunter_revoke_reference = lambda rc, text: None
    return app


def test_scan_analysis_enables_propupd_without_starting_it(monkeypatch):
    app = _app()
    started_threads = []
    monkeypatch.setattr(
        controller.threading,
        "Thread",
        lambda *args, **kwargs: started_threads.append((args, kwargs)),
    )

    result = controller.update_rkhunter_summary_from_output(
        app,
        "System checks summary\nPossible rootkits: 0\nNo rootkits found",
        0,
        dpkg_output="",
        dpkg_rc=0,
    )

    assert result["propupd_allowed"] is True
    assert app.btn_rkhunter_propupd.state == "normal"
    assert started_threads == []
    assert "Risk: Low" in app.rkhunter_summary_var.get()


def test_format_rkhunter_analysis_explains_locked_propupd_button():
    app = _app()
    result = _valid_result()
    result.update(
        {
            "propupd_allowed": False,
            "risk": "medium",
            "review": [
                {
                    "line": "Warning: Hidden file found: /etc/.unknown",
                    "code": "hidden_system_file",
                }
            ],
        }
    )

    text = controller.format_rkhunter_analysis(app, result)

    assert "Reference acceptance locked" in text
    assert "overall risk is not low" in text
    assert "unexplained warnings require review" in text


def test_propupd_without_valid_gate_never_asks_or_starts(monkeypatch):
    app = _app()
    calls = []
    monkeypatch.setattr(
        controller.messagebox,
        "showwarning",
        lambda *args, **kwargs: calls.append("warning"),
    )
    monkeypatch.setattr(
        controller.messagebox,
        "askyesno",
        lambda *args, **kwargs: calls.append("ask") or True,
    )

    controller.rkhunter_propupd_async(
        app,
        is_rkhunter_installed_fn=lambda: True,
    )

    assert calls == ["warning"]
    assert app.rkhunter_updating is False


def test_propupd_rechecks_gate_after_confirmation(monkeypatch):
    app = _app()
    app.rkhunter_last_result = _valid_result()
    sudo_calls = []
    app.ensure_sudo_session = lambda reason: sudo_calls.append(reason) or True

    def invalidate_gate(*_args, **_kwargs):
        app.rkhunter_last_result["risk"] = "high"
        return True

    monkeypatch.setattr(controller.messagebox, "askyesno", invalidate_gate)

    controller.rkhunter_propupd_async(
        app,
        is_rkhunter_installed_fn=lambda: True,
    )

    assert sudo_calls == []
    assert app.rkhunter_updating is False


def test_confirmed_propupd_starts_exactly_one_worker(monkeypatch):
    app = _app()
    app.rkhunter_last_result = _valid_result()
    threads = []

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon
            self.started = False
            threads.append(self)

        def start(self):
            self.started = True

    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(controller.threading, "Thread", FakeThread)

    controller.rkhunter_propupd_async(
        app,
        is_rkhunter_installed_fn=lambda: True,
    )

    assert len(threads) == 1
    assert threads[0].target is app._rkhunter_propupd_worker
    assert threads[0].daemon is True
    assert threads[0].started is True
    assert app.rkhunter_updating is True
    assert app.btn_rkhunter_propupd.state == "disabled"


def test_scan_worker_collects_dpkg_verification(monkeypatch):
    app = _app()
    completed = []
    app._finish_rkhunter_scan = lambda *args: completed.append(args)
    commands = []

    def fake_run_cmd(args, timeout):
        commands.append((args, timeout))
        if args == ["sudo", "-n", "cat", "/var/log/rkhunter.log"]:
            return 0, "[12:00:00] Warning: Hidden file found: /etc/.java"
        if args == ["sudo", "-n", "dpkg", "-V"]:
            return 0, "??5?????? c /etc/fwupd.conf"
        if args == ["dpkg", "-S", "/usr/bin/lwp-request"]:
            return 0, "libwww-perl: /usr/bin/lwp-request"
        if args == ["file", "-b", "/usr/bin/lwp-request"]:
            return 0, "Perl script text executable"
        return (
            1,
            "Warning: The command '/usr/bin/lwp-request' has been replaced by a script\n"
            "System checks summary\nPossible rootkits: 0",
        )

    monkeypatch.setattr(controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(controller, "has_cmd", lambda name: name in {"dpkg", "file"})
    monkeypatch.setattr(controller, "call_in_ui_thread", lambda _app, fn: fn())

    controller.rkhunter_scan_worker(app)

    assert commands == [
        (
            ["sudo", "-n", "rkhunter", "--check", "--skip-keypress", "--nocolors"],
            1800,
        ),
        (["sudo", "-n", "cat", "/var/log/rkhunter.log"], 30),
        (["sudo", "-n", "dpkg", "-V"], 300),
        (["dpkg", "-S", "/usr/bin/lwp-request"], 30),
        (["file", "-b", "/usr/bin/lwp-request"], 30),
    ]
    assert completed == [
        (
            1,
            "Warning: The command '/usr/bin/lwp-request' has been replaced by a script\n"
            "System checks summary\nPossible rootkits: 0\n"
            "=== rkhunter log evidence ===\n"
            "[12:00:00] Warning: Hidden file found: /etc/.java",
            0,
            "??5?????? c /etc/fwupd.conf",
            "/usr/bin/lwp-request\t0\tlibwww-perl: /usr/bin/lwp-request",
            "/usr/bin/lwp-request\t0\tPerl script text executable",
        )
    ]


def test_successful_propupd_revokes_gate_and_displays_success(monkeypatch):
    app = _app()
    app.rkhunter_last_result = _valid_result()
    shown = []
    monkeypatch.setattr(
        controller.messagebox,
        "showinfo",
        lambda title, message, **kwargs: shown.append((title, message, kwargs)),
    )

    controller.finish_rkhunter_propupd(app, 0, "properties updated")

    assert app.rkhunter_last_result["propupd_allowed"] is False
    assert app.btn_rkhunter_propupd.state == "disabled"
    assert "reference database was updated successfully" in app.output[-1][0]
    assert len(shown) == 1


def test_confirmed_revoke_reference_starts_exactly_one_worker(monkeypatch):
    app = _app()
    threads = []

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon
            self.started = False
            threads.append(self)

        def start(self):
            self.started = True

    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(controller.threading, "Thread", FakeThread)

    controller.rkhunter_revoke_reference_async(
        app,
        is_rkhunter_installed_fn=lambda: True,
    )

    assert len(threads) == 1
    assert threads[0].target is app._rkhunter_revoke_reference_worker
    assert threads[0].daemon is True
    assert threads[0].started is True
    assert app.rkhunter_updating is True
    assert app.btn_rkhunter_propupd.state == "disabled"


def test_successful_revoke_reference_revokes_gate_and_displays_success(monkeypatch):
    app = _app()
    app.rkhunter_last_result = _valid_result()
    shown = []
    monkeypatch.setattr(
        controller.messagebox,
        "showinfo",
        lambda title, message, **kwargs: shown.append((title, message, kwargs)),
    )

    controller.finish_rkhunter_revoke_reference(app, 0, "restored")

    assert app.rkhunter_last_result["propupd_allowed"] is False
    assert app.btn_rkhunter_propupd.state == "disabled"
    assert "previous rkhunter reference database was restored" in app.output[-1][0]
    assert len(shown) == 1


def test_failed_revoke_reference_shows_missing_backup_detail(monkeypatch):
    app = _app()
    shown = []
    monkeypatch.setattr(
        controller.messagebox,
        "showerror",
        lambda title, message, **kwargs: shown.append((title, message, kwargs)),
    )

    controller.finish_rkhunter_revoke_reference(app, 2, "Kein NetMon-Backup vorhanden.")

    assert "could not be restored (rc=2)" in app.output[-1][0]
    assert "Kein NetMon-Backup vorhanden." in app.output[-1][0]
    assert len(shown) == 1
    assert "Kein NetMon-Backup vorhanden." in shown[0][1]


def test_web_cmd_blocked_scan_revokes_stale_propupd_gate():
    app = _app()
    app.rkhunter_last_result = _valid_result()
    app.rkhunter_propupd_available = True
    app._looks_like_rkhunter_web_cmd_issue = lambda _output: True
    app.show_rkhunter_web_cmd_hint = lambda: None

    controller.finish_rkhunter_scan(app, 1, "Invalid WEB_CMD configuration option")

    assert app.rkhunter_last_result == {}
    assert app.rkhunter_propupd_available is False
    assert app.btn_rkhunter_propupd.state == "disabled"


def test_rkhunter_scan_rc_one_is_reported_as_finished_with_warnings():
    app = _app()
    app._looks_like_rkhunter_web_cmd_issue = lambda _output: False
    app._update_rkhunter_summary_from_output = lambda *args, **kwargs: _valid_result()

    controller.finish_rkhunter_scan(
        app,
        1,
        "System checks summary\nPossible rootkits: 0",
        0,
        "",
    )

    assert app.rkhunter_status_var.get() == "finished with warnings"


def test_show_rkhunter_log_loads_log_into_output(monkeypatch):
    app = _app()

    monkeypatch.setattr(
        controller,
        "run_cmd",
        lambda args, timeout: (0, "[12:00:00] Warning: Hidden file found: /etc/.java"),
    )

    controller.show_rkhunter_log(app)

    assert app.output == [
        (
            "=== rkhunter log file ===\n\n"
            "[12:00:00] Warning: Hidden file found: /etc/.java",
            False,
        )
    ]
    assert app.rkhunter_summary_var.get() == "rkhunter log file loaded."


def test_show_rkhunter_scan_output_restores_last_scan_view():
    app = _app()
    app.rkhunter_last_scan_output = "last scan\n\nanalysis"

    controller.show_rkhunter_scan_output(app)

    assert app.output == [("last scan\n\nanalysis", False)]


def test_show_rkhunter_scan_output_handles_missing_scan_view():
    app = _app()

    controller.show_rkhunter_scan_output(app)

    assert app.output == [("No rkhunter scan output is available yet.", False)]


def test_show_rkhunter_log_does_not_read_while_scan_is_running(monkeypatch):
    app = _app()
    app.rkhunter_running = True
    calls = []
    monkeypatch.setattr(controller, "run_cmd", lambda *a, **k: calls.append(a))

    controller.show_rkhunter_log(app)

    assert calls == []
    assert app.logs == ["rkhunter is already running."]
