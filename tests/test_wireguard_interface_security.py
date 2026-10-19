"""Interface-name confusion: protected synthetic profiles and fake kernel/tools."""

import io
import json
from types import SimpleNamespace

import pytest
from test_netmon_nm_ownership import store as store  # noqa: PLC0414

from netmon.core import nm_ownership as own
from netmon.core import wireguard_import
from netmon.features import firewall_controller as firewall
from netmon.features import vpn_controller as vpn

PRIVATE = "A" * 43 + "="
PUBLIC = "B" * 43 + "="
OTHER = "C" * 43 + "="
CONTENT = f"[Interface]\nPrivateKey = {PRIVATE}\n[Peer]\nPublicKey = {OTHER}\n[Peer]\nPublicKey = {OTHER}\n"


@pytest.fixture
def kernel(tmp_path, monkeypatch, store):
    directory = tmp_path / "wireguard"
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(own, "PROFILE_DIRECTORY", str(directory))
    path = directory / "work.conf"
    path.write_text(CONTENT)
    path.chmod(0o600)
    state = SimpleNamespace(
        index=7,
        kind="wireguard",
        public=PUBLIC,
        calls=[],
        path=path,
        store=store,
        interfaces=[],
    )
    monkeypatch.setattr(own.socket, "if_nameindex", lambda: state.interfaces)

    def command(argv, *, input_text=None):
        state.calls.append((argv, input_text))
        if argv[:2] == ["/usr/sbin/ip", "-j"]:
            return json.dumps(
                [
                    {
                        "ifname": argv[-1],
                        "ifindex": state.index,
                        "flags": ["UP"],
                        "linkinfo": {"info_kind": state.kind},
                    }
                ]
            )
        if argv == ["/usr/bin/wg", "pubkey"]:
            assert input_text == PRIVATE + "\n"
            return PUBLIC
        if argv == ["/usr/bin/wg", "show", "work", "public-key"]:
            return state.public
        pytest.fail("unexpected tool operation")

    monkeypatch.setattr(own, "_interface_command", command)
    return state


def test_live_interface_is_bound_to_protected_profile(kernel):
    proof = kernel.store.verify_interface("work")
    assert proof == {
        "name": "work",
        "kind": "wireguard",
        "ifindex": 7,
        "public_key": PUBLIC,
        "profile_sha256": kernel.store.snapshot_profile("work")["sha256"],
    }
    assert PRIVATE not in json.dumps(proof)
    assert len(kernel.calls) == 4


@pytest.mark.parametrize("kind", ["ether", "veth", "bridge", "tun", None])
def test_non_wireguard_link_cannot_reach_key_lookup(kernel, kind):
    kernel.kind = kind
    with pytest.raises(own.OwnershipError):
        kernel.store.verify_interface("work")
    assert len(kernel.calls) == 1


@pytest.mark.parametrize("public", [OTHER, "", "(none)", PUBLIC + "\nextra"])
def test_wrong_or_missing_live_key_rejected(kernel, public):
    kernel.public = public
    with pytest.raises(own.OwnershipError):
        kernel.store.verify_interface("work")


@pytest.mark.parametrize("change", ["index", "kind", "profile", "symlink", "mode"])
def test_identity_switch_during_verification_rejected(kernel, monkeypatch, change):
    original = own._interface_command

    def command(argv, **kwargs):
        result = original(argv, **kwargs)
        if argv[-1] == "public-key":
            if change == "index":
                kernel.index = 8
            elif change == "kind":
                kernel.kind = "ether"
            elif change == "profile":
                kernel.path.write_text(CONTENT + "# changed\n")
            elif change == "mode":
                kernel.path.chmod(0o666)
            else:
                target = kernel.path.with_name("other.conf")
                kernel.path.rename(target)
                kernel.path.symlink_to(target)
        return result

    monkeypatch.setattr(own, "_interface_command", command)
    with pytest.raises((own.OwnershipError, OSError)):
        kernel.store.verify_interface("work")


@pytest.mark.parametrize(
    "content",
    [
        "",
        "[Peer]\nPrivateKey=" + PRIVATE,
        "[Interface]\nPrivateKey=no",
        CONTENT + "[Interface]\nPrivateKey=" + PRIVATE,
        CONTENT.replace("[Peer]", "PrivateKey=" + PRIVATE, 1),
    ],
)
def test_ambiguous_or_invalid_private_key_rejected(kernel, content):
    kernel.path.write_text(content)
    with pytest.raises(own.OwnershipError):
        kernel.store.verify_interface("work")
    assert not kernel.calls


@pytest.mark.parametrize(
    "name", ["../work", ".", "..", "-bad/name", "x" * 16, "eth0\n", None]
)
def test_invalid_interface_names_fail_closed(kernel, name):
    with pytest.raises(own.OwnershipError):
        kernel.store.verify_interface(name)
    assert own.verified_interface(name) is None
    assert not kernel.calls


@pytest.mark.parametrize("name", ["eth0", "enp4s0", "wlan0", "work"])
def test_privileged_import_rejects_live_name_collision(kernel, name):
    kernel.interfaces = [(2, name)]
    payload = wireguard_import.ProfileSnapshot.from_bytes(
        "synthetic", name, CONTENT.encode()
    ).payload()
    with pytest.raises(own.OwnershipError):
        kernel.store.install_profile(payload)
    assert kernel.path.read_text() == CONTENT


def test_late_import_collision_rejected(kernel, monkeypatch):
    calls = []

    def interfaces():
        calls.append(True)
        return [] if len(calls) == 1 else [(2, "work")]

    monkeypatch.setattr(own.socket, "if_nameindex", interfaces)
    payload = wireguard_import.ProfileSnapshot.from_bytes(
        "synthetic", "work", (CONTENT + "# new").encode()
    ).payload()
    with pytest.raises(own.OwnershipError):
        kernel.store.install_profile(payload)
    assert kernel.path.read_text() == CONTENT


@pytest.mark.parametrize("name", ["eth0", "enp4s0", "wlan0", "work"])
@pytest.mark.parametrize("verified", [False, True])
def test_collector_and_ufw_sink_require_identity(monkeypatch, name, verified):
    queries = []

    def proof(iface):
        queries.append(iface)
        return {"name": iface} if verified else None

    monkeypatch.setattr(own, "verified_interface", proof)
    app = SimpleNamespace(
        _base_wg_profile_name=lambda p: p,
        resolve_profile_family_runtime=lambda *a, **kw: {
            "effective_ipv4_interface": name
        },
        log_debug=lambda *a: None,
    )
    assert vpn.collect_interface_rules_for_profiles(app, [name]) == (
        {name} if verified else set()
    )
    calls = []
    service = SimpleNamespace(
        ufw_allow_on_iface=lambda *args, **kw: (calls.append(args) or (0, ""))
    )
    for direction in ("in", "out"):
        ok, added, _, _ = firewall.ensure_ufw_rule_exists(
            {"type": "interface", "iface": name, "direction": direction},
            network_service=service,
        )
        assert ok == verified and added == verified
    assert len(calls) == (2 if verified else 0)
    assert queries == [name] * 3


def test_sink_rechecks_after_collection_and_before_existing_rule(monkeypatch):
    monkeypatch.setattr(own, "verified_interface", lambda name: None)
    ok, added, _, _keys = firewall.ensure_ufw_rule_exists(
        {"type": "interface", "iface": "eth0", "direction": "in"},
        known_keys={("iface", "in", "eth0")},
    )
    assert not ok and not added


def test_missing_helper_fails_closed(monkeypatch):
    monkeypatch.setattr(own, "trusted_helper_available", lambda: False)
    assert own.verified_interface("work") is None


def test_tool_environment_is_fixed_and_private_key_only_on_stdin(monkeypatch):
    calls = []
    monkeypatch.setenv("PATH", "/untrusted")
    monkeypatch.setenv("PYTHONPATH", "/untrusted")

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=PUBLIC)

    monkeypatch.setattr(own.subprocess, "run", run)
    assert (
        own._interface_command(["/usr/bin/wg", "pubkey"], input_text=PRIVATE + "\n")
        == PUBLIC
    )
    argv, kwargs = calls[0]
    assert PRIVATE not in " ".join(argv)
    assert kwargs["env"] == {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
    assert kwargs["input"] == PRIVATE + "\n"


@pytest.mark.parametrize("name", ["eth0", "enp4s0", "wlan0"])
def test_killswitch_does_not_trust_active_interface_names(monkeypatch, name):
    from test_killswitch_failure_recovery import Ufw

    ufw = Ufw()
    ufw.app.get_wg_interfaces = lambda: [name]
    monkeypatch.setattr(own, "verified_interface", lambda iface: None)
    firewall.killswitch_on_sync(ufw.app, refresh_ui=False)
    assert not any(cmd[:1] == ["allow"] and cmd[-1] == name for cmd in ufw.calls)
    ufw.assert_closed()


@pytest.mark.parametrize("direction", ["out", "in"])
def test_killswitch_rechecks_each_rule_and_recovers_on_identity_loss(
    monkeypatch, direction
):
    from test_killswitch_failure_recovery import Ufw

    ufw = Ufw()
    queries = []

    def verify(name):
        queries.append(name)
        # First collection succeeds; fail before selected rule is executed.
        return (
            {"name": name} if len(queries) < (2 if direction == "out" else 3) else None
        )

    monkeypatch.setattr(own, "verified_interface", verify)
    assert not firewall.killswitch_on_sync(ufw.app, refresh_ui=False)
    assert ["allow", direction, "on", "wg0"] not in ufw.calls
    ufw.assert_closed()


def test_down_link_is_rejected(kernel, monkeypatch):
    original = own._interface_command

    def command(argv, **kwargs):
        result = original(argv, **kwargs)
        if argv[0] == "/usr/sbin/ip":
            rows = json.loads(result)
            rows[0]["flags"] = []
            return json.dumps(rows)
        return result

    monkeypatch.setattr(own, "_interface_command", command)
    with pytest.raises(own.OwnershipError):
        kernel.store.verify_interface("work")


def test_protected_cli_returns_only_public_identity(kernel, monkeypatch, capsys):
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(own, "OwnershipStore", lambda: kernel.store)
    monkeypatch.setattr(
        own.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b'{"name":"work"}'))
    )
    assert own.main(["verify-interface"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["public_key"] == PUBLIC
    assert PRIVATE not in output.out + output.err


@pytest.mark.parametrize(
    "payload", [{"name": "work", "content": "x"}, [], {"name": "../work"}]
)
def test_protected_cli_rejects_invalid_requests(kernel, monkeypatch, capsys, payload):
    monkeypatch.setattr(own.os, "geteuid", lambda: 0)
    monkeypatch.setattr(own, "__file__", own.HELPER)
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(own, "OwnershipStore", lambda: kernel.store)
    monkeypatch.setattr(
        own.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(json.dumps(payload).encode())),
    )
    assert own.main(["verify-interface"]) == 1
    assert PRIVATE not in str(capsys.readouterr())
    assert not kernel.calls


@pytest.mark.parametrize(
    "reply,rc",
    [
        ("not-json", 0),
        ("{}", 0),
        ("[]", 0),
        ('{"name":"work","kind":"ether","ifindex":7}', 0),
        ('{"name":"other","kind":"wireguard","ifindex":7}', 0),
        ('{"name":"work","kind":"wireguard","ifindex":true}', 0),
        ('{"name":"work","kind":"wireguard","ifindex":7}', 1),
    ],
)
def test_helper_rpc_fails_closed_on_error_or_malformed_proof(monkeypatch, reply, rc):
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(
        own.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=rc, stdout=reply),
    )
    assert own.verified_interface("work") is None


def test_helper_rpc_uses_fixed_isolated_installed_helper(monkeypatch):
    monkeypatch.setattr(own, "trusted_helper_available", lambda: True)

    def run(argv, **kwargs):
        assert argv == [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            own.HELPER,
            "verify-interface",
        ]
        assert kwargs["input"] == '{"name": "work"}'
        assert kwargs["env"] == {
            "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
        }
        return SimpleNamespace(
            returncode=0, stdout='{"name":"work","kind":"wireguard","ifindex":7}'
        )

    monkeypatch.setattr(own.subprocess, "run", run)
    assert own.verified_interface("work")["ifindex"] == 7


@pytest.mark.parametrize(
    "name,kind",
    [("eth0", "ether"), ("enp4s0", "ether"), ("wlan0", "ether"), ("work", "wireguard")],
)
def test_original_attack_through_real_runtime_collector_verifier_and_sink(
    kernel, monkeypatch, name, kind
):
    kernel.kind = kind
    if name != "work":
        kernel.path.rename(kernel.path.with_name(name + ".conf"))

    def verify(iface):
        try:
            return kernel.store.verify_interface(iface)
        except own.OwnershipError:
            return None

    monkeypatch.setattr(own, "verified_interface", verify)
    app = SimpleNamespace(
        _base_wg_profile_name=lambda p: p,
        ipv6_is_disabled=lambda: False,
        _internal_ipv4_profile_name=lambda p: p + "_ipv4",
        profile_supports_ipv6=lambda p: False,
        _wg_profile_exists=lambda p: p == name,
        log_debug=lambda *a: None,
    )
    app.resolve_profile_family_runtime = (
        lambda p, **kw: vpn.resolve_profile_family_runtime(app, p, **kw)
    )
    interfaces = vpn.collect_interface_rules_for_profiles(
        app, [wireguard_import.profile_name(name + ".conf")]
    )
    assert interfaces == ({"work"} if kind == "wireguard" else set())
    calls = []
    service = SimpleNamespace(
        ufw_allow_on_iface=lambda *args, **kw: (calls.append(args) or (0, ""))
    )
    for iface in interfaces:
        for direction in ("in", "out"):
            assert firewall.ensure_ufw_rule_exists(
                {"type": "interface", "iface": iface, "direction": direction},
                network_service=service,
            )[0]
    assert calls == ([("in", "work"), ("out", "work")] if kind == "wireguard" else [])
