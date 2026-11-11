"""Manual profile exclusivity, without host DNS or service access."""

from types import SimpleNamespace

import pytest

from netmon.features import dns_controller
from netmon.services.dns_control_service import DNSControlService
from tests.test_netmon_dns_consistency import DummyVar, ImmediateThread
from tools import netmon

GOOGLE = ["8.8.8.8", "8.8.4.4"]


def resolver_status(servers, *, link=""):
    return (
        "Global\n    DNS Servers: "
        + " ".join(servers)
        + "\n    DNS Domain: ~.\n"
        + ("Link 2 (eth0)\n    DNS Servers: " + link + "\n" if link else "")
    )


@pytest.fixture
def service(tmp_path):
    def unexpected(*args, **kwargs):
        pytest.fail("External command requires an explicit test response")

    instance = DNSControlService(
        unexpected,
        lambda _: False,
        dot_dropin_path=str(tmp_path / "netmon-dot.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    instance.get_wireguard_interfaces = lambda: set()
    instance.read_resolvectl_status = lambda: (0, resolver_status(GOOGLE))
    return instance


def test_manual_dropin_resets_previous_global_dns_without_touching_other_files():
    app = netmon.App.__new__(netmon.App)
    app._dns_servers_for_choice = lambda _: GOOGLE
    app.get_preferred_dnssec_mode = lambda: "allow-downgrade"
    written = []
    app._write_dot_dropin_text = lambda text: (written.append(text) or True, "")

    assert app._write_manual_dns_dropin("Google (8.8.8.8)")[0]

    lines = written[0].splitlines()
    assert lines.index("DNS=") < lines.index("DNS=8.8.8.8 8.8.4.4")
    assert len(written) == 1


@pytest.mark.parametrize(
    "servers", [GOOGLE, ["2001:db8::53", "2001:db8::54"], ["8.8.8.8#dns.google"]]
)
def test_effective_profile_accepts_exact_normalized_dns(service, servers):
    service.read_resolvectl_status = lambda: (0, resolver_status(servers))
    assert service.verify_dns_profile(servers)[0]


def test_unused_fallback_is_not_mistaken_for_an_additional_active_server(service):
    service.read_resolvectl_status = lambda: (
        0,
        resolver_status(GOOGLE) + "Fallback DNS Servers: 1.1.1.1\n",
    )
    assert service.verify_dns_profile(GOOGLE)[0]


@pytest.mark.parametrize("servers", [[], ["invalid"], ["8.8.8.8", ""]])
def test_invalid_target_cannot_be_confirmed(service, servers):
    service.read_resolvectl_status = lambda: pytest.fail(
        "Invalid target must not be read"
    )
    assert not service.verify_dns_profile(servers)[0]


@pytest.mark.parametrize(
    "defect",
    [
        "mixed",
        "wrong",
        "missing",
        "link",
        "unreadable",
        "malformed",
        "empty",
        "exception",
    ],
)
def test_effective_profile_rejects_unconfirmed_or_extra_servers(service, defect):
    text = resolver_status(GOOGLE)
    rc = 0
    if defect == "mixed":
        text = resolver_status(["1.1.1.1", "9.9.9.9", *GOOGLE])
    elif defect == "wrong":
        text = resolver_status(["1.1.1.1"])
    elif defect == "missing":
        text = resolver_status(GOOGLE[:1])
    elif defect == "link":
        text = resolver_status(GOOGLE, link="192.0.2.53")
    elif defect == "unreadable":
        rc = 1
    elif defect == "malformed":
        text = resolver_status([*GOOGLE, "not-an-address"])
    elif defect == "empty":
        text = ""
    else:

        def fail_read():
            raise OSError("simulated unavailable resolver")

        service.read_resolvectl_status = fail_read
    if defect != "exception":
        service.read_resolvectl_status = lambda: (rc, text)

    ok, detail = service.verify_dns_profile(GOOGLE)

    assert not ok and detail


@pytest.mark.parametrize("mixed", [False, True])
def test_manual_apply_checks_effective_state_before_reporting_success(service, mixed):
    events = []
    service.read_resolvectl_status = lambda: (
        events.append("verify") or 0,
        resolver_status([*GOOGLE, "1.1.1.1"] if mixed else GOOGLE),
    )
    app = SimpleNamespace(
        _dns_control_service=lambda: service,
        is_vpn_active=lambda: False,
        _apply_nm_dns_policy_to_targets=lambda **_: (True, []),
        _read_dot_dropin=lambda: "previous configuration",
        _write_manual_dns_dropin=lambda _: (events.append("write") or True, ""),
        _restart_resolved_for_dns_policy=lambda: (events.append("restart") or True, ""),
        tr=lambda _key, fallback: fallback,
    )

    result = dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )

    assert events == ["write", "restart", "verify"]
    assert result["success"] is (not mixed)
    assert result["verification_ok"] is (not mixed)
    report = dns_controller.format_dns_profile_control_result(
        app, result, heading="DNS", action="apply"
    )
    assert result["verification_detail"] in report


@pytest.mark.parametrize("defect", ["write", "restart", "no_service"])
def test_apply_cannot_succeed_without_verified_resolver(service, defect):
    events = []
    service.read_resolvectl_status = lambda: pytest.fail(
        "No verification after failed mutation"
    )
    app = SimpleNamespace(
        _dns_control_service=lambda: None if defect == "no_service" else service,
        is_vpn_active=lambda: False,
        _apply_nm_dns_policy_to_targets=lambda **_: (True, []),
        _read_dot_dropin=lambda: "previous",
        _write_manual_dns_dropin=lambda _: (defect != "write", "write error"),
        _restart_resolved_for_dns_policy=lambda: (defect != "restart", "restart error"),
        _restore_dot_dropin_backup=lambda _: (events.append("restore") or True, ""),
    )
    result = dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)"
    )
    assert not result["success"]
    assert not result["verification_ok"]
    assert events == (["restore"] if defect == "restart" else [])


@pytest.mark.parametrize("mixed", [False, True])
def test_consistency_cannot_report_stable_for_additional_dns(
    monkeypatch, service, mixed
):
    service.read_resolvectl_status = lambda: (
        0,
        resolver_status([*GOOGLE, "1.1.1.1", "9.9.9.9"] if mixed else GOOGLE),
    )
    app = netmon.App.__new__(netmon.App)
    app.dns_consistency_enabled = True
    app.dns_consistency_running = False
    app.last_dns_consistency_ts = 0
    app.dns_choice = DummyVar("Google (8.8.8.8)")
    app.killswitch_is_on = lambda: False
    app.active_wg_profile = lambda: None
    app._dns_control_service = lambda: service
    app.after = lambda _delay, callback: callback()
    app.log = lambda _: None
    app._update_dns_consistency_light_safe = lambda: None
    logs = []
    app.update_dns_output = lambda text, **_: logs.append(text)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name in {"dig", "curl"})

    def query(args, **kwargs):
        if args[0] == "dig":
            return 0, "192.0.2.1"
        if args[0] == "curl":
            return 0, "ok"
        pytest.fail(f"Unexpected query: {args}")

    monkeypatch.setattr(netmon, "run_cmd", query)
    app.dns_consistency_check_async(force=True)

    assert app.last_dns_consistency_ok is (not mixed)
    assert ("STABIL" in "\n".join(logs)) is (not mixed)
    assert "Resolver" in "\n".join(logs)
