"""Integration boundary: the V4 DNS repair must honor incident recovery gates."""

from types import SimpleNamespace

import pytest

from netmon.core.killswitch_journal import KillswitchJournal
from test_dns_guard_feedback import dirty_profile, make_app, status
from test_dns_guard_feedback import network as network


@pytest.mark.parametrize(
    "pending",
    [
        "memory",
        "applying",
        "restoring",
        "recovery_required",
        "unreadable",
        "root-recovery",
        "root-unknown",
    ],
)
@pytest.mark.parametrize("vpn_active", [True, False])
def test_dns_repair_pauses_on_persisted_or_live_firewall_recovery(
    network, tmp_path, pending, vpn_active
):
    fake, service = network
    dirty_profile(fake)
    if not vpn_active:
        fake.text = status(ethernet="192.0.2.53", vpn=False)
    app = make_app(service)
    if pending == "memory":
        app.killswitch_recovery_required = True
    elif pending.startswith("root-"):
        app.firewall_snapshots = SimpleNamespace(state=lambda: pending[5:])
    else:
        directory = tmp_path / "restart-state"
        journal = KillswitchJournal(directory)
        journal.mark("applying" if pending == "unreadable" else pending)
        if pending == "unreadable":
            (directory / "killswitch-state.json").write_text("invalid")
        app.killswitch_journal = KillswitchJournal(directory)
    before = {name: dict(profile["props"]) for name, profile in fake.profiles.items()}

    app.run_dns_guard_check_once(auto_repair=True)

    assert fake.writes == []
    assert {name: profile["props"] for name, profile in fake.profiles.items()} == before
    assert app.dns_guard_state == "unknown"
    assert "Firewall" in app.dns_guard_status_var.get()
    assert app.dns_guard_check_running is False
    assert not app.errors
    assert app.enforce_dns_clean()[0] is False


def test_dns_repair_remains_available_without_firewall_recovery(network):
    fake, service = network
    dirty_profile(fake)
    app = make_app(service)

    app.run_dns_guard_check_once(auto_repair=True)

    assert fake.writes
    assert app.dns_guard_state == "ok"
    assert not app.errors
