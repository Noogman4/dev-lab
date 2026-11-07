"""F4 diagnostics never clear journal/gates or establish firewall authority."""

from types import SimpleNamespace

import pytest

from netmon.features import firewall_controller as fc
from netmon.core.ufw_snapshot import SnapshotError


@pytest.mark.parametrize(
    "response,recognized",
    [
        ({"state": "off", "retired": True}, True),
        ({"state": "off"}, False),
        ({"state": "off", "retired": False}, False),
        ({"state": "off", "retired": "true"}, False),
        ({"state": "reviewed", "retired": True}, False),
        ({"state": "on", "retired": True}, False),
        ({"state": "unknown", "retired": True}, False),
        ({"state": "recovery", "retired": True}, False),
        ({"state": "absent"}, False),
        (None, False),
        (["off"], False),
        (SnapshotError("helper unavailable"), False),
    ],
)
def test_only_retired_off_changes_recovery_message(monkeypatch, response, recognized):
    calls, logs = [], []

    def request(action, payload):
        calls.append((action, payload))
        if isinstance(response, Exception):
            raise response
        return response

    def recover():
        calls.append("stale recovery")
        raise SnapshotError("Unknown transaction")

    snapshots = SimpleNamespace(
        request=request, abort_unmodified=lambda: False, recovery=recover
    )
    journal = SimpleNamespace(mark=lambda *_a: pytest.fail("journal mutation"))
    app = SimpleNamespace(
        firewall_snapshots=snapshots,
        _active_firewall_snapshot=snapshots,
        killswitch_journal=journal,
        killswitch_recovery_required=True,
        _vpn_firewall_sync_pending=True,
        _vpn_dns_completion_deferred=True,
        log_safe=logs.append,
    )
    before = app.__dict__.copy()
    assert fc._recover_killswitch_failure_locked(app) is False
    assert calls == ["stale recovery", ("state", {})]
    assert app.__dict__ == before
    assert len(logs) == 1
    if recognized:
        assert "zwischenzeitlich bestätigtes AUS" in logs[0]
        assert "Wiederherstellung manuell geprüft …" in logs[0]
        assert "Notfallsperre nicht verifiziert" not in logs[0]
    else:
        assert logs == [
            "UFW-Notfallsperre nicht verifiziert: geschützter Snapshotpfad nicht verfügbar; manuelle Wiederherstellung erforderlich."
        ]


def test_failed_recovery_without_existing_transaction_keeps_generic_message():
    def begin():
        raise SnapshotError("No active authority")

    snapshots = SimpleNamespace(
        begin=begin, request=lambda *_a: pytest.fail("unrelated retired receipt")
    )
    logs = []
    app = SimpleNamespace(firewall_snapshots=snapshots, log_safe=logs.append)
    assert fc._recover_killswitch_failure_locked(app) is False
    assert "_active_firewall_snapshot" not in app.__dict__
    assert "Notfallsperre nicht verifiziert" in logs[0]
