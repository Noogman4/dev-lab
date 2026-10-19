"""Manual endpoint injection: synthetic configs and fake privileged boundaries."""

import ipaddress
from types import SimpleNamespace

import pytest

from netmon.core import manual_wireguard as manual
from netmon.core import nm_ownership
from netmon.features import vpn_controller as vpn


@pytest.fixture
def payload():
    return {
        "profile": "manual-test",
        "private_key": "A" * 43 + "=",
        "public_key": "A" * 43 + "=",
        "address": "10.0.0.2/32, 2001:db8::2/128",
        "allowed_ips": "0.0.0.0/0, ::/0",
        "endpoint": "vpn.example:51820",
        "dns": "10.0.0.1, 2001:db8::1",
        "preshared_key": "A" * 43 + "=",
        "keepalive": "25",
    }


@pytest.fixture
def form(payload):
    values = {
        "profile_name": "profile",
        "private_key": "private_key",
        "public_key": "public_key",
        "preshared_key": "preshared_key",
        "endpoint": "endpoint",
        "address": "address",
        "allowed_ips": "allowed_ips",
        "dns": "dns",
        "keepalive": "keepalive",
    }
    app = SimpleNamespace()
    for name, key in values.items():
        setattr(
            app,
            "manual_wg_" + name + "_var",
            SimpleNamespace(get=lambda k=key: payload[k]),
        )
    app._is_internal_ipv4_profile = lambda _: False
    app._validate_wireguard_key_value = lambda value, _: (value, "")
    app._parse_manual_wireguard_endpoint = (
        lambda value: vpn.parse_manual_wireguard_endpoint(app, value)
    )
    return app


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("vpn.example:51820", ("vpn.example", "51820")),
        ("VPN.Example.:00518", ("vpn.example.", "518")),
        ("xn--bcher-kva.example:443", ("xn--bcher-kva.example", "443")),
        ("198.51.100.2:1", ("198.51.100.2", "1")),
        ("[2001:0DB8::1]:65535", ("2001:db8::1", "65535")),
        (
            "[::ffff:192.0.2.1]:51820",
            (str(ipaddress.IPv6Address("::ffff:192.0.2.1")), "51820"),
        ),
    ],
)
def test_valid_endpoints(endpoint, expected):
    assert manual.parse_endpoint(endpoint) == expected


@pytest.mark.parametrize(
    "endpoint",
    [
        "vpn.example\n[Interface]\nPreUp = SYNTHETIC_NEVER_EXECUTE\n# :51820",
        "vpn.example\rPostUp=x:51820",
        "vpn.example\0:51820",
        " vpn.example:51820",
        "vpn.example:51820\n",
        "vpn.example :51820",
        "vpn.example:\t51820",
        "vpn.example\u2028:51820",
        "vpn.example\u0085:51820",
        "vpn.example\u200b:51820",
        "vpn.example#x:51820",
        "vpn.example;x:51820",
        "vpn.example=x:51820",
        "[vpn.example]:51820",
        "2001:db8::1:51820",
        "[2001:db8::1]extra:51820",
        "[fe80::1%eth0]:51820",
        "[::::]:51820",
        "vpn..example:51820",
        "-vpn.example:51820",
        "vpn-.example:51820",
        "vpn_example:51820",
        "256.1.1.1:51820",
        "127.1:51820",
        "vpn.example:0",
        "vpn.example:65536",
        "vpn.example:-1",
        "vpn.example:²",
        "vpn.example:５１８２０",
        "vpn.example:" + "9" * 10000,
        "a" * 64 + ".example:51820",
        ".example:51820",
        "",
        None,
        42,
    ],
)
def test_endpoint_rejected_without_exception(endpoint):
    host, port, error = vpn.parse_manual_wireguard_endpoint(None, endpoint)
    assert (host, port) == (None, None)
    assert error.startswith("Endpoint")


@pytest.mark.parametrize("codepoint", [*range(33), 127, *range(128, 160)])
def test_all_ascii_controls_and_c1_rejected(codepoint):
    with pytest.raises(ValueError):
        manual.parse_endpoint("vpn.example" + chr(codepoint) + ":51820")


def test_actual_form_rejects_injection_and_trailing_controls(form, payload):
    for endpoint in (
        "vpn.example\n[Interface]\nPreUp=x\n# :51820",
        "vpn.example:51820\n",
    ):
        payload["endpoint"] = endpoint
        result, error = vpn.validate_manual_wireguard_form(form)
        assert result is None
        assert error.startswith("Endpoint")


@pytest.mark.parametrize(
    "endpoint", ["vpn.example:51820", "198.51.100.1:1", "[2001:db8::1]:65535"]
)
def test_form_renderer_and_fake_install_roundtrip(form, payload, endpoint, monkeypatch):
    payload["endpoint"] = endpoint
    result, error = vpn.validate_manual_wireguard_form(form)
    assert not error
    text = vpn.build_manual_wireguard_config_text(form, result)
    assert text.count("[Interface]") == text.count("[Peer]") == 1
    assert not nm_ownership.wireguard_hooks(text.encode())
    installed = []
    monkeypatch.setattr(
        vpn,
        "_write_generated_wireguard_profile",
        lambda app, name, content: installed.append((name, content)),
    )
    assert vpn.write_manual_wg_profile(form, result["profile"], text) == (True, "")
    assert installed == [("manual-test", text)]


@pytest.mark.parametrize(
    "field",
    [
        "private_key",
        "public_key",
        "address",
        "allowed_ips",
        "endpoint",
        "dns",
        "preshared_key",
        "keepalive",
    ],
)
@pytest.mark.parametrize(
    "injected",
    [
        "\n[Interface]\nPreUp = SYNTHETIC_NEVER_EXECUTE",
        "\rPostDown=x",
        "\0",
        "\u2028PostUp=x",
    ],
)
def test_builder_rejects_injection_in_every_field(payload, field, injected):
    payload[field] += injected
    with pytest.raises(ValueError):
        vpn.build_manual_wireguard_config_text(None, payload)


@pytest.mark.parametrize(
    "suffix",
    [
        "\n[Interface]\n",
        "\n[Peer]\n",
        "\nPreUp = SYNTHETIC_NEVER_EXECUTE\n",
        "\npOsTdOwN = SYNTHETIC_NEVER_EXECUTE\n",
        "\nSaveConfig = true\n",
        "\nEndpoint = vpn.example:443\n",
        "\n[Other]\n",
        "\n# unexpected comment\n",
    ],
)
def test_write_boundary_blocks_bypass(payload, suffix, monkeypatch):
    text = vpn.build_manual_wireguard_config_text(None, payload) + suffix
    monkeypatch.setattr(
        vpn,
        "_write_generated_wireguard_profile",
        lambda *a: pytest.fail("Unsafe content reached privileged handoff"),
    )
    assert vpn.write_manual_wg_profile(None, "manual-test", text)[0] is False


def test_apply_invalid_render_never_requests_sudo_or_starts_worker(payload):
    payload["endpoint"] += "\n[Interface]\nPreUp=x\n# :51820"
    statuses, logs = [], []
    app = SimpleNamespace(
        _validate_manual_wireguard_form=lambda: (payload, ""),
        manual_wg_save_slot_var=SimpleNamespace(get=lambda: False),
        _build_manual_wireguard_config_text=lambda p: vpn.build_manual_wireguard_config_text(
            None, p
        ),
        _set_manual_wg_status=lambda text, **kw: statuses.append(kw["level"]),
        log=logs.append,
        ensure_sudo_session=lambda *a: pytest.fail("Sudo requested for invalid render"),
    )
    vpn.apply_manual_wireguard_profile(app)
    assert statuses == ["error"]
    assert logs


@pytest.mark.parametrize(
    "field,value",
    [
        ("endpoint", "bad..example:1"),
        ("address", "not-an-address"),
        ("allowed_ips", "0.0.0.0/0,#ignored"),
        ("dns", "example.com"),
        ("dns", "fe80::1%eth0"),
        ("keepalive", "65536"),
        ("private_key", "invalid"),
        ("public_key", "invalid"),
    ],
)
def test_final_config_values_are_parsed(payload, field, value):
    payload[field] = value
    with pytest.raises(ValueError):
        vpn.build_manual_wireguard_config_text(None, payload)
