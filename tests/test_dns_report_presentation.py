"""DNS reports describe one routing snapshot; no host configuration is touched."""

import copy
import json
from pathlib import Path

import pytest

from netmon import app as app_module
from netmon.services.dns_control_service import DNSControlService

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = """Global
    Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
    Current DNS Server: 1.1.1.1
    DNS Servers: 1.1.1.1 9.9.9.9
    Fallback DNS Servers: 8.8.8.8
Link 2 (enp4s0)
    Current Scopes: none
    Protocols: -DefaultRoute -DNSOverTLS DNSSEC=no/unsupported
Link 3 (enp42s0)
    Current Scopes: none
    Protocols: -DefaultRoute -DNSOverTLS DNSSEC=no/unsupported
Link 4 (Irland)
    Current Scopes: DNS
    Protocols: +DefaultRoute -DNSOverTLS DNSSEC=no/unsupported
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1
    DNS Domain: ~.
"""


@pytest.fixture
def service(tmp_path):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Presentation attempted a system command")

    result = DNSControlService(
        forbidden,
        lambda _name: False,
        dot_dropin_path=str(tmp_path / "missing.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    result.get_wireguard_interfaces = lambda: {"Irland"}
    return result


@pytest.fixture(params=["de", "en"])
def tr(request):
    translations = json.loads((ROOT / f"netmon/lang/{request.param}.json").read_text())
    return lambda key, fallback: translations.get(key, fallback)


def reports(service, text, tr, *, selected=None):
    return [
        service.build_dns_status_report(
            text, resolved_active=True, selected_dns=selected, tr=tr
        ),
        service.build_dns_health_report(text, tr=tr),
        service.build_dns_leak_check_result(
            resolvectl_output=text,
            dns_servers=["203.0.113.53"],
            public_ip="198.51.100.42",
            tr=tr,
        ),
    ]


def test_actual_report_case_separates_vpn_dns_and_shadowed_global_servers(service, tr):
    before = service.parse_dns_snapshot(OBSERVED)
    original = copy.deepcopy(before)
    view = service.dns_report_view(snapshot=before)
    assert before == original
    assert view["preferred_dns"] == ["10.2.0.1"]
    assert view["other_dns"] == ["1.1.1.1", "9.9.9.9"]
    assert view["effective_dns"] == ["10.2.0.1"]
    for report in reports(service, OBSERVED, tr, selected=["1.1.1.1", "9.9.9.9"]):
        assert tr("dns_report_vpn_dns", "").format(dns="10.2.0.1") in report
        assert (
            tr("dns_report_other_configured", "").format(dns="1.1.1.1, 9.9.9.9")
            in report
        )
        assert (
            "203.0.113.53" not in report
        )  # separately supplied stale flat list is ignored
        assert "8.8.8.8" not in report  # system fallback is not an active resolver
        assert tr("dns_status_system_limited", "") not in report
        assert "exklusiv" not in report and "exclusively" not in report
    leak_report = reports(service, OBSERVED, tr)[2]
    assert tr("dns_report_check_scope", "") in leak_report
    assert (
        tr("dns_leak_detected", "").format(value=tr("dns_leak_no", "")) in leak_report
    )
    assert tr("dns_leak_action_none_needed", "") in leak_report


@pytest.mark.parametrize("change", ["missing_root", "competing_root"])
def test_real_competing_routes_still_warn_in_every_report(service, tr, change):
    text = (
        OBSERVED.replace("DNS Domain: ~.", "DNS Domain:")
        if change == "missing_root"
        else OBSERVED.replace("Global\n", "Global\n    DNS Domain: ~.\n")
    )
    assert service.evaluate_dns_policy(resolvectl_output=text)["conflict"]
    for report in reports(service, text, tr):
        assert (
            tr("dns_report_competing_dns", "").format(dns="1.1.1.1, 9.9.9.9") in report
        )
        assert tr("dns_report_vpn_preferred", "") not in report
    leak_report = reports(service, text, tr)[2]
    assert (
        tr("dns_leak_detected", "").format(value=tr("dns_leak_yes", "")) in leak_report
    )
    assert (
        tr("dns_leak_risk_line", "").format(risk=tr("dns_leak_risk_high", ""))
        in leak_report
    )


def test_intentional_split_dns_is_named_instead_of_claiming_exclusivity(service, tr):
    text = (
        OBSERVED
        + """Link 8 (lan0)
    Current Scopes: DNS
    Protocols: -DefaultRoute -DNSOverTLS DNSSEC=no/unsupported
    DNS Servers: 192.168.1.1
    DNS Domain: ~lan.example
"""
    )
    for report in reports(service, text, tr):
        assert tr("dns_report_split_hint", "") in report
        assert "192.168.1.1" in report
        assert "exklusiv" not in report and "exclusively" not in report
    assert not service.evaluate_dns_policy(resolvectl_output=text)["conflict"]


@pytest.mark.parametrize(
    "bad", ["", "status query failed", OBSERVED.replace("10.2.0.1", "invalid")]
)
def test_unknown_or_invalid_input_never_claims_safe_vpn_dns(service, tr, bad):
    for report in reports(service, bad, tr):
        assert tr("dns_report_vpn_preferred", "") not in report
        assert tr("dns_leak_status_vpn_only", "") not in report
    leak_report = reports(service, bad, tr)[2]
    assert (
        tr("dns_leak_detected", "").format(value=tr("dns_leak_unknown", ""))
        in leak_report
    )


def test_global_security_flags_do_not_claim_protection_for_plain_vpn(service, tr):
    text = OBSERVED.replace(
        "-DNSOverTLS DNSSEC=no/unsupported", "+DNSOverTLS DNSSEC=yes/supported", 1
    )
    for report in reports(service, text, tr)[:2]:
        assert tr("dns_status_dot_inactive", "") in report
        assert tr("dns_status_dnssec_disabled", "") in report
        assert tr("dns_status_dot_active", "") not in report
        assert tr("dns_status_dnssec_strict", "") not in report
        assert tr("dns_report_vpn_preferred", "") in report


def test_offline_plain_dns_profile_is_neutral_without_dot_or_dnssec(service, tr):
    service.get_wireguard_interfaces = lambda: set()
    text = "Global\n    Protocols: -DNSOverTLS DNSSEC=no/unsupported\n    DNS Servers: 9.9.9.9\n"
    for report in reports(service, text, tr, selected=["9.9.9.9"])[:2]:
        assert tr("dns_status_plain_configured", "") in report
        assert tr("dns_status_system_limited", "") not in report
        assert tr("dns_status_dnssec_disabled", "") in report


def test_guard_popup_uses_one_fresh_snapshot_and_the_same_report(
    service, tr, monkeypatch
):
    app = app_module.App.__new__(app_module.App)
    app.tr = tr
    app._dns_control_service = lambda: service
    app.get_selected_user_dns = lambda: ["9.9.9.9"]
    app.dns_guard_allowed_dns = [
        "203.0.113.53"
    ]  # stale cache must not leak into details
    reads, shown = [], []
    snapshot = service.parse_dns_snapshot(OBSERVED)
    service.read_dns_snapshot = lambda: reads.append(True) or snapshot
    monkeypatch.setattr(
        app_module.messagebox, "showinfo", lambda *args, **_kw: shown.append(args)
    )
    app.show_dns_guard_details()
    assert reads == [True]
    assert len(shown) == 1
    title, text = shown[0]
    assert title == tr("dns_guard_details_title", "")
    assert tr("dns_report_vpn_preferred", "") in text
    assert tr("dns_report_other_configured", "").format(dns="1.1.1.1, 9.9.9.9") in text
    assert tr("dns_report_allowed", "") + "\n10.2.0.1" in text
    assert "203.0.113.53" not in text
    assert app.dns_guard_allowed_dns == ["10.2.0.1"]


def test_dot_dropin_conflict_is_not_reported_as_safe_vpn_dns(service, tr):
    service.detect_netmon_dot_dropin_conflict = lambda: (
        True,
        "[Resolve]\nDNS=1.1.1.1\nDomains=~.\n",
    )
    for report in reports(service, OBSERVED, tr):
        assert tr("dns_report_vpn_preferred", "") not in report
        assert tr("dns_leak_status_vpn_only", "") not in report
    report = reports(service, OBSERVED, tr)[2]
    assert tr("dns_leak_detected", "").format(value=tr("dns_leak_yes", "")) in report
