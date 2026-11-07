"""F4 diagnostic only: real UFW and App, isolated capability-free kernel stub."""

import json
from pathlib import Path

import pytest

from test_review_v5 import system as system, real_app
from test_review_v13 import scene
from support import ufw_cli, reboot
from netmon.features import firewall_controller as fc, vpn_controller as vc


@pytest.mark.parametrize("foreign_rule", ["none", "allow", "global_block"])
def test_competing_off_diagnostic_preserves_existing_review_gates(
    system, monkeypatch, foreign_rule
):
    app, env, logs, original = scene(system, monkeypatch)
    monkeypatch.setattr(
        vc, "cleanup_wireguard_interfaces", lambda _a: env.live.clear() or True
    )
    monkeypatch.setattr(
        vc, "_show_killswitch_active_after_vpn_off_notice", lambda _a: None
    )
    transport = app.firewall_snapshots.transport
    commands = 0
    external = {}
    logs.clear()

    def inject(action, payload):
        nonlocal commands
        if action == "command":
            commands += 1
            if commands == 2:
                assert system.restore()["state"] == "off"
                if foreign_rule != "none":
                    arguments = (
                        ["allow", "in", "8080/tcp"]
                        if foreign_rule == "allow"
                        else ["deny", "out", "from", "any", "to", "any"]
                    )
                    assert ufw_cli(arguments)[0] == 0
                external["capture"] = system.capture()
        return transport(action, payload)

    app.firewall_snapshots.transport = inject
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False), logs
    app.firewall_snapshots.transport = transport
    assert system.state() == {"state": "off", "retired": True}
    assert system.capture() == external["capture"]
    assert not any("Notfallsperre nicht verifiziert" in message for message in logs)
    new_messages = [
        message for message in logs if "zwischenzeitlich bestätigtes AUS" in message
    ]
    if foreign_rule == "none":
        assert not new_messages
        assert app.killswitch_journal.phase() == "off_verified"
        assert not fc.firewall_recovery_pending(app)
        assert system.capture() == original
    else:
        assert len(new_messages) == 1
        assert "Wiederherstellung manuell geprüft …" in new_messages[0]
        assert app.killswitch_journal.phase() == "applying"
        assert fc.firewall_recovery_pending(app)
        assert app.finalize_dns_after_vpn_profile_switch() is False
        assert not vc.vpn_switch(app, "wg0", ensure_sudo=False, refresh_ui=False)
        assert not fc.killswitch_off_sync(app, refresh_ui=False)
        assert system.capture() == external["capture"]

        assert reboot().returncode == 0  # Private UFW init, not a VM reboot.
        restarted, restarted_env, _new_logs = real_app(system, monkeypatch)
        restarted_env.live.clear()
        assert restarted.killswitch_journal.phase() == "applying"
        assert fc.firewall_recovery_pending(restarted)
        fc.acknowledge_manual_firewall_review(restarted)
        if foreign_rule == "allow":
            assert system.state() == {"state": "reviewed", "retired": True}
            assert restarted.killswitch_journal.phase() == "manual_reviewed"
            assert not fc.firewall_recovery_pending(restarted)
        else:
            assert system.state() == {"state": "off", "retired": True}
            assert restarted.killswitch_journal.phase() == "applying"
            assert fc.firewall_recovery_pending(restarted)
        assert system.capture() == external["capture"]
    Path(f"/work/F4-diagnostic-{foreign_rule}.json").write_text(
        json.dumps(
            {
                "new_diagnostic": new_messages,
                "Root_after_review": system.state(),
                "foreign_rules_preserved": True,
                "no_automatic_gate_release": True,
                "logs": logs,
            },
            indent=2,
        )
        + "\n"
    )
