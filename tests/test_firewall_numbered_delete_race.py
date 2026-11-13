"""UFW rule numbers must not be reused across a released lock.

A concurrent writer (another NetMon worker or e.g. fail2ban's ``ufw insert 1``)
can renumber the list as soon as ``app.ufw_lock`` is released. The fakes below
run such a writer deterministically right after the first lock release.
"""

import threading
from types import SimpleNamespace

import pytest

from netmon.features import firewall_controller as firewall


class Immediate:
    def __init__(self, target, **_kwargs):
        self.target = target

    def start(self):
        self.target()


class ReleaseHookLock:
    """Lock that lets a queued writer run right after the first release."""

    def __init__(self, on_first_release):
        self._lock = threading.Lock()
        self._hook = on_first_release

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, *_exc):
        self._lock.release()
        hook, self._hook = self._hook, None
        if hook is not None:
            with self._lock:
                hook()
        return False


class FakeUfw:
    def __init__(self, rules):
        self.rules = list(rules)
        self.deleted = []

    def status(self):
        rows = [f"[{index:2d}] {rule}" for index, rule in enumerate(self.rules, 1)]
        return "Status: active\n\n     To  Action  From\n" + "\n".join(rows)

    def run(self, args, **_kwargs):
        if args[3:5] == ["status", "numbered"]:
            return 0, self.status()
        if args[3:5] == ["--force", "delete"]:
            self.deleted.append(self.rules.pop(int(args[5]) - 1))
            return 0, "Rule deleted"
        raise AssertionError(f"unexpected command {args}")


def _patch_common(monkeypatch, ufw):
    monkeypatch.setattr(firewall.threading, "Thread", Immediate)
    monkeypatch.setattr(firewall, "run_cmd", ufw.run)
    monkeypatch.setattr(firewall, "unrelated_ufw_writes_blocked", lambda _app: False)
    monkeypatch.setattr(firewall, "call_in_ui_thread", lambda _app, _fn: None)


def _ssh_app(lock):
    return SimpleNamespace(
        ufw_lock=lock,
        ensure_sudo_session=lambda *_a: True,
        after=lambda *_a: None,
        log=lambda *_a: None,
        tr=lambda _key, fallback: fallback,
    )


def test_selected_rule_delete_survives_concurrent_insert_at_top(monkeypatch):
    ufw = FakeUfw(
        [
            "80/tcp ALLOW IN Anywhere",
            "443/tcp ALLOW IN Anywhere",
            "8080/tcp ALLOW IN Anywhere",
        ]
    )
    _patch_common(monkeypatch, ufw)
    monkeypatch.setattr(firewall.messagebox, "askyesno", lambda *_a, **_k: True)
    selected = firewall.parse_ufw_numbered_rule("[ 2] 443/tcp ALLOW IN Anywhere")
    app = SimpleNamespace(
        ufw_lock=ReleaseHookLock(
            lambda: ufw.rules.insert(0, "25/tcp DENY IN 203.0.113.9")
        ),
        firewall_rules_table=SimpleNamespace(selection=lambda: ("row",)),
        firewall_rule_row_meta={"row": selected},
        ensure_sudo_session=lambda *_a: True,
        after=lambda *_a: None,
        log=lambda *_a: None,
        tr=lambda _key, fallback: fallback,
    )

    assert firewall.remove_selected_firewall_rule(app) is True

    assert ufw.deleted == ["443/tcp ALLOW IN Anywhere"]
    assert "80/tcp ALLOW IN Anywhere" in ufw.rules


def test_ssh_cleanup_re_resolves_numbers_after_concurrent_append(monkeypatch):
    ufw = FakeUfw(
        [
            "22/tcp ALLOW IN Anywhere",
            "80/tcp ALLOW IN Anywhere",
            "22/tcp (v6) ALLOW IN Anywhere (v6)",
            "80/tcp (v6) ALLOW IN Anywhere (v6)",
        ]
    )
    _patch_common(monkeypatch, ufw)
    # ufw places a new IPv4 rule in front of all IPv6 rows.
    app = _ssh_app(
        ReleaseHookLock(lambda: ufw.rules.insert(2, "443/tcp ALLOW IN Anywhere"))
    )

    firewall.remove_ssh_rule_async(app, auto=True)

    assert sorted(ufw.deleted) == [
        "22/tcp (v6) ALLOW IN Anywhere (v6)",
        "22/tcp ALLOW IN Anywhere",
    ]
    assert ufw.rules == [
        "80/tcp ALLOW IN Anywhere",
        "443/tcp ALLOW IN Anywhere",
        "80/tcp (v6) ALLOW IN Anywhere (v6)",
    ]


def test_ssh_cleanup_keeps_port_22_rule_added_after_confirmation(monkeypatch):
    ufw = FakeUfw(
        [
            "22/tcp ALLOW IN Anywhere",
            "80/tcp ALLOW IN Anywhere",
            "22/tcp (v6) ALLOW IN Anywhere (v6)",
        ]
    )
    _patch_common(monkeypatch, ufw)
    app = _ssh_app(
        ReleaseHookLock(lambda: ufw.rules.insert(0, "22/tcp ALLOW IN 192.0.2.7"))
    )

    firewall.remove_ssh_rule_async(app, auto=True)

    assert sorted(ufw.deleted) == [
        "22/tcp (v6) ALLOW IN Anywhere (v6)",
        "22/tcp ALLOW IN Anywhere",
    ]
    assert ufw.rules == ["22/tcp ALLOW IN 192.0.2.7", "80/tcp ALLOW IN Anywhere"]


@pytest.mark.parametrize(
    "rule",
    [
        "443/tcp ALLOW IN 192.0.2.22",
        "Anywhere ALLOW IN 10.0.0.22",
        "443 ALLOW IN 2001:db8::22",
        "80/tcp ALLOW IN Anywhere # room 22",
        "Anywhere on wg22 ALLOW IN Anywhere",
        "Anywhere DENY OUT 192.0.2.1 22/tcp",
        "8022/tcp ALLOW IN Anywhere",
        "2222/tcp ALLOW IN Anywhere",
        "22/udp ALLOW IN Anywhere",
        "22/tcp DENY IN Anywhere",
        "22/tcp REJECT IN Anywhere",
        "22/tcp ALLOW OUT Anywhere",
        "22/tcp ALLOW FWD Anywhere",
        "OpenSSH DENY IN Anywhere",
    ],
)
def test_ssh_classifier_ignores_rules_that_only_mention_22(rule):
    assert firewall._numbered_ssh_rules(f"[ 7] {rule}") == ([], [])


@pytest.mark.parametrize(
    "rule",
    [
        "22/tcp ALLOW IN Anywhere",
        "22 ALLOW IN Anywhere",
        "22/tcp LIMIT IN Anywhere",
        "22/tcp (v6) ALLOW IN Anywhere (v6)",
        "22/tcp ALLOW IN 192.168.1.0/24",
        "192.168.1.5 22/tcp ALLOW IN Anywhere",
        "22/tcp on eth0 ALLOW IN Anywhere",
        "22/tcp ALLOW IN Anywhere # ssh",
        "OpenSSH ALLOW IN Anywhere",
        "OpenSSH (v6) LIMIT IN Anywhere (v6)",
        "192.168.1.5 OpenSSH ALLOW IN Anywhere",
    ],
)
def test_ssh_classifier_selects_exact_inbound_ssh_rules(rule):
    assert firewall._numbered_ssh_rules(f"[ 7] {rule}") == ([(7, rule)], [])


@pytest.mark.parametrize(
    "rule",
    ["21,22,80/tcp ALLOW IN Anywhere", "20:30/tcp ALLOW IN Anywhere"],
)
def test_ssh_classifier_reports_multiport_rules_for_manual_review(rule):
    assert firewall._numbered_ssh_rules(f"[ 7] {rule}") == ([], [(7, rule)])


def test_ssh_cleanup_deletes_only_ssh_rules_from_mixed_table(monkeypatch):
    ufw = FakeUfw(
        [
            "443/tcp ALLOW IN 192.0.2.22",
            "22/tcp ALLOW IN Anywhere",
            "Anywhere on wg22 ALLOW IN Anywhere",
            "21,22,80/tcp ALLOW IN Anywhere",
            "OpenSSH ALLOW IN Anywhere",
            "22/tcp DENY IN 203.0.113.0/24",
        ]
    )
    _patch_common(monkeypatch, ufw)
    logs = []
    app = _ssh_app(threading.Lock())
    app.after = lambda _delay, callback: callback()
    app.log = logs.append

    firewall.remove_ssh_rule_async(app, auto=True)

    assert sorted(ufw.deleted) == [
        "22/tcp ALLOW IN Anywhere",
        "OpenSSH ALLOW IN Anywhere",
    ]
    assert ufw.rules == [
        "443/tcp ALLOW IN 192.0.2.22",
        "Anywhere on wg22 ALLOW IN Anywhere",
        "21,22,80/tcp ALLOW IN Anywhere",
        "22/tcp DENY IN 203.0.113.0/24",
    ]
    assert any("21,22,80/tcp" in line and "manuell" in line for line in logs)


def test_ssh_confirmation_lists_exact_rules_and_deletes_only_those(monkeypatch):
    ufw = FakeUfw(
        [
            "22/tcp ALLOW IN Anywhere",
            "80/tcp ALLOW IN 192.0.2.22",
            "20:30/tcp ALLOW IN Anywhere",
        ]
    )
    _patch_common(monkeypatch, ufw)
    monkeypatch.setattr(firewall, "call_in_ui_thread", lambda _app, fn: fn())
    prompts = []

    def askyesno(_title, body, **_kwargs):
        prompts.append(body)
        # A port-22 rule appearing after the dialog was shown is not confirmed.
        ufw.rules.insert(0, "22 ALLOW IN 198.51.100.4")
        return True

    monkeypatch.setattr(firewall.messagebox, "askyesno", askyesno)

    firewall.remove_ssh_rule_async(_ssh_app(threading.Lock()))

    assert len(prompts) == 1
    assert "• 22/tcp ALLOW IN Anywhere" in prompts[0]
    assert "• 20:30/tcp ALLOW IN Anywhere" in prompts[0]
    assert "192.0.2.22" not in prompts[0]
    assert ufw.deleted == ["22/tcp ALLOW IN Anywhere"]
    assert ufw.rules == [
        "22 ALLOW IN 198.51.100.4",
        "80/tcp ALLOW IN 192.0.2.22",
        "20:30/tcp ALLOW IN Anywhere",
    ]


def test_ssh_confirmation_cancel_deletes_nothing(monkeypatch):
    ufw = FakeUfw(["22/tcp ALLOW IN Anywhere"])
    _patch_common(monkeypatch, ufw)
    monkeypatch.setattr(firewall, "call_in_ui_thread", lambda _app, fn: fn())
    monkeypatch.setattr(firewall.messagebox, "askyesno", lambda *_a, **_k: False)

    firewall.remove_ssh_rule_async(_ssh_app(threading.Lock()))

    assert ufw.deleted == []


def test_ssh_cleanup_stops_after_failed_delete(monkeypatch):
    ufw = FakeUfw(
        [
            "22/tcp ALLOW IN Anywhere",
            "22/tcp (v6) ALLOW IN Anywhere (v6)",
        ]
    )
    _patch_common(monkeypatch, ufw)
    calls = []

    def run(args, **kwargs):
        calls.append(args[3])
        if args[3] == "--force":
            return 1, "ERROR: Could not delete rule"
        return ufw.run(args, **kwargs)

    monkeypatch.setattr(firewall, "run_cmd", run)

    firewall.remove_ssh_rule_async(_ssh_app(threading.Lock()), auto=True)

    assert calls == ["status", "--force"]
    assert ufw.deleted == []
