"""DoT configuration, verification and guard integration on synthetic state."""

from types import SimpleNamespace

import pytest

from netmon.features import dot_controller as dot
from netmon.services.dns_control_service import DNSControlService
from tests.test_netmon_dns_consistency import DummyVar, ImmediateThread
from tools import netmon


@pytest.fixture
def model(monkeypatch, tmp_path):
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Quad9")
    app.get_preferred_dnssec_mode = lambda: "allow-downgrade"
    state = SimpleNamespace(
        app=app,
        rc_dns=0,
        rc_status=0,
        query_rc=0,
        tls_ok=True,
        extra="",
        mode="yes",
        raw_dns=None,
    )
    state.content = dot.build_dot_dropin_content(app)[2]

    def status():
        return (
            "Global\n    Protocols: "
            + ("+DNSOverTLS" if state.mode == "yes" else "-DNSOverTLS")
            + " DNSSEC=allow-downgrade/supported\n    DNS Servers: 9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net "
            + state.extra
            + "\n    DNS Domain: ~.\n"
        )

    def run(args, **kwargs):
        if args == ["resolvectl", "status"]:
            return state.rc_status, status()
        if args == ["resolvectl", "dns"]:
            return state.rc_dns, (
                state.raw_dns
                if state.raw_dns is not None
                else "Global: 9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net "
                + state.extra
                + "\nLink 2 (eth0):\n"
            )
        if args == ["resolvectl", "query", "example.com"]:
            return state.query_rc, "192.0.2.1" if not state.query_rc else "query failed"
        if args == ["sudo", "-n", "systemctl", "restart", "systemd-resolved"]:
            return 0, ""
        pytest.fail(f"Unmodelled command: {args}")

    service = DNSControlService(
        run,
        lambda _: False,
        dot_dropin_path=str(tmp_path / "netmon.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    service.get_wireguard_interfaces = lambda: set()
    app._dns_control_service = lambda: service
    state.service = service
    state.status = status
    monkeypatch.setattr(dot, "run_cmd", run)
    monkeypatch.setattr(dot, "read_dot_dropin", lambda *args, **kwargs: state.content)
    monkeypatch.setattr(
        dot, "detect_netmon_dot_dropin_conflict", lambda _: (True, state.content)
    )
    monkeypatch.setattr(
        dot,
        "dot_preflight",
        lambda: {
            "checks": {"systemctl": True, "resolvectl": True},
            "resolved_active": True,
            "resolved_state": "active",
        },
    )
    monkeypatch.setattr(
        dot,
        "dot_tls_probe",
        lambda *args, **kwargs: (state.tls_ok, "synthetic TLS result"),
    )
    return state


@pytest.mark.parametrize("profile", ["Cloudflare", "Quad9", "Google"])
def test_dot_profiles_reset_previous_dns_and_keep_tls(model, profile):
    _, config, text = dot.build_dot_dropin_content(model.app, profile)
    assert text.splitlines().index("DNS=") < next(
        i
        for i, line in enumerate(text.splitlines())
        if line.startswith("DNS=") and line != "DNS="
    )
    assert "DNSOverTLS=yes" in text
    assert all(address + "#" + config["hostname"] in text for address in config["dns"])


@pytest.mark.parametrize("run_test", [False, True])
def test_clean_effective_profile_can_be_green(model, run_test):
    result = dot.collect_dot_status(model.app, run_test=run_test)
    assert result["ok"] is True
    assert "TLS-Modus bestätigt" in result["text"]


@pytest.mark.parametrize("run_test", [False, True])
@pytest.mark.parametrize(
    "case",
    [
        "old_servers",
        "bare_same_ip",
        "wrong_sni",
        "extra_link",
        "mode_off",
        "dns_read_error",
        "status_read_error",
        "missing_global",
    ],
)
def test_successful_tls_probe_cannot_hide_effective_mismatch(model, run_test, case):
    if case == "old_servers":
        model.extra = "1.1.1.1 9.9.9.9"
    elif case == "bare_same_ip":
        model.extra = "9.9.9.9"
    elif case == "wrong_sni":
        model.raw_dns = "Global: 9.9.9.9#wrong.example 149.112.112.112#dns.quad9.net"
    elif case == "extra_link":
        model.raw_dns = "Global: 9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net\nLink 2 (eth0): 1.1.1.1"
    elif case == "mode_off":
        model.mode = "no"
    elif case == "dns_read_error":
        model.rc_dns = 1
    elif case == "status_read_error":
        model.rc_status = 1
    else:
        model.raw_dns = (
            "Link 2 (eth0): 9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net"
        )
    assert dot.collect_dot_status(model.app, run_test=run_test)["ok"] is not True


@pytest.mark.parametrize("tls_ok", [False, None])
def test_real_test_cannot_pass_without_positive_tls_probe(model, tls_ok):
    model.tls_ok = tls_ok
    assert dot.collect_dot_status(model.app, run_test=True)["ok"] is not True


@pytest.mark.parametrize(
    "source",
    ["cached", "starting", "file", "runtime", "unreadable_file", "unreadable_runtime"],
)
def test_guard_never_replaces_tls_with_plain_dns(model, monkeypatch, source):
    app = model.app
    app._auto_dns_control_available = lambda: True
    app.is_vpn_active = lambda: False
    app.get_selected_user_dns = lambda: ["8.8.8.8", "8.8.4.4"]
    app.apply_dns = lambda **kwargs: pytest.fail("Must not write plain DNS over DoT")
    if source == "cached":
        app.dot_enabled = True
    elif source == "starting":
        app.dot_running = True
    elif source == "runtime":
        model.content = ""
    elif source == "unreadable_file":

        def unreadable(*args, **kwargs):
            raise PermissionError("synthetic unreadable configuration")

        monkeypatch.setattr(dot, "read_dot_dropin", unreadable)
    elif source == "unreadable_runtime":
        model.content = ""
        model.rc_status = 1
    before = model.content
    ok, detail = app.enforce_dns_clean()
    assert not ok and "DoT" in detail
    assert model.content == before


@pytest.mark.parametrize(
    "ok,expected", [(True, "green"), (False, "red"), (None, "yellow")]
)
def test_configured_flag_alone_cannot_force_green(model, ok, expected):
    colors = []
    app = model.app
    app.l_dot = object()
    app.dot_enabled = True
    app.dot_last_test_ok = ok
    app.set_light = lambda _, color: colors.append(color)
    dot.update_dot_light(app)
    assert colors == [expected]


def test_ipv6_sni_is_compared_canonically():
    config = "[Resolve]\nDNS=\nDNS=2001:db8::53#DNS.Example\nDNSOverTLS=yes\n"
    status = "Global\n    Protocols: +DNSOverTLS\n"
    assert (
        dot.verify_effective_dot_profile(
            config, status, "Global: 2001:0db8:0:0:0:0:0:53#dns.example"
        )[0]
        is True
    )
    assert (
        dot.verify_effective_dot_profile(config, status, "Global: 2001:db8::53")[0]
        is False
    )


def test_activation_and_guard_ticks_preserve_quad9_tls(model, monkeypatch):
    app = model.app
    app.dot_running = False
    app.dot_enabled = False
    app.dot_last_test_ok = False
    app.dot_last_test_var = DummyVar()
    app.dns_guard_enabled_var = DummyVar(True)
    app.ensure_sudo_session = lambda _: True
    app.confirm_dnssec_mode_activation = lambda _: True
    app.update_dns_controls_state_safe = lambda: None
    app.nb = SimpleNamespace(select=lambda _: None)
    app.tab_dns = None
    app.after = lambda *args: None
    app.update_dns_output = lambda *args, **kwargs: None
    app.log_safe = lambda _: None
    app.log_debug_safe = lambda text: pytest.fail(text)
    app.get_selected_user_dns = lambda: ["8.8.8.8", "8.8.4.4"]
    app.apply_dns = lambda **kwargs: pytest.fail("Guard must not downgrade DoT")
    app._auto_dns_control_available = lambda: True
    writes = []

    def write(path, content, **kwargs):
        assert path == dot.DOT_DROPIN_PATH and "DNSOverTLS=yes" in content
        writes.append(content)
        model.content = content
        return 0, ""

    monkeypatch.setattr(dot, "write_privileged_config", write)
    monkeypatch.setattr(dot.threading, "Thread", ImmediateThread)
    dot.enable_dot_async(app)
    assert app.dot_last_test_ok is True and app.dot_enabled
    # Represent expiry of the existing two-second guard transition.
    app.dns_guard_transition_until = 0
    for _ in range(3):
        app.run_dns_guard_check_once(auto_repair=True)
        assert app.dns_guard_state == "ok"
    assert len(writes) == 1 and "DNSOverTLS=yes" in model.content
