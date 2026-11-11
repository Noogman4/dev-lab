"""DNS profile reads through the real command helper; subprocesses are fake."""

import subprocess
from types import SimpleNamespace

import pytest

from netmon.core import command
from netmon.features import dns_controller
from netmon.services.dns_control_service import DNSControlService

UUID = "12345678-1234-5678-9012-123456789abc"
TARGET = ("enp42s0", "Ethernet-Verbindung 1")
FIELDS = (
    "connection.uuid,connection.interface-name,connection.type,"
    "ipv4.ignore-auto-dns,ipv6.ignore-auto-dns,ipv4.dns,ipv6.dns"
)
PROPS = ("ipv4.ignore-auto-dns", "ipv6.ignore-auto-dns", "ipv4.dns", "ipv6.dns")


@pytest.fixture
def network(monkeypatch, tmp_path):
    state = SimpleNamespace(
        fields=[UUID, "", "802-3-ethernet", "no", "no", "", ""],
        active_uuid=UUID,
        read_rc=0,
        commands=[],
        fail_activation=False,
    )

    def run(args, **kwargs):
        args = list(args)
        state.commands.append(args)
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.STDOUT
        assert kwargs["text"] is True
        if args == ["resolvectl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, "Global\n    DNS Servers: 8.8.8.8 8.8.4.4\n"
            )
        if args == ["nmcli", "-g", FIELDS, "con", "show", "id", TARGET[1]]:
            return subprocess.CompletedProcess(
                args, state.read_rc, "\n".join(state.fields) + "\n"
            )
        if args == ["nmcli", "-g", "GENERAL.CON-UUID", "device", "show", TARGET[0]]:
            return subprocess.CompletedProcess(args, 0, state.active_uuid + "\n")
        if args[:7] == ["sudo", "-n", "nmcli", "con", "mod", "uuid", UUID]:
            props = dict(zip(PROPS, state.fields[3:]))
            props.update(zip(args[7::2], args[8::2]))
            state.fields[3:] = [props[key] for key in PROPS]
            return subprocess.CompletedProcess(args, 0, "")
        if args == ["sudo", "-n", "nmcli", "con", "up", "uuid", UUID]:
            return subprocess.CompletedProcess(
                args,
                int(state.fail_activation),
                "activation failed" if state.fail_activation else "",
            )
        pytest.fail(f"Unmodelled subprocess: {args}")

    monkeypatch.setattr(command.subprocess, "run", run)
    service = DNSControlService(
        command.run_cmd,
        lambda name: name == "nmcli",
        dot_dropin_path=str(tmp_path / "netmon-dot.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    return state, service


@pytest.mark.parametrize("bound_iface", ["", TARGET[0]])
@pytest.mark.parametrize(
    "dns4,dns6",
    [("", ""), ("8.8.8.8", ""), ("", "2001:db8::53"), ("8.8.8.8", "2001:db8::53")],
)
def test_profile_preserves_empty_fields_with_real_command_helper(
    network, bound_iface, dns4, dns6
):
    state, service = network
    state.fields[1] = bound_iface
    state.fields[5:] = [dns4, dns6]

    profiles = service.read_nm_dns_profiles([TARGET])

    assert profiles == [
        {
            "iface": TARGET[0],
            "name": TARGET[1],
            "uuid": UUID,
            "properties": dict(zip(PROPS, ("no", "no", dns4, dns6))),
        }
    ]
    assert not any(args[0] == "sudo" for args in state.commands)


@pytest.mark.parametrize("preserve_output", [False, True])
def test_command_output_preservation_is_opt_in(monkeypatch, preserve_output):
    output = "\nvalue\n\n\n"
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, output),
    )
    assert command.run_cmd(["synthetic"], preserve_output=preserve_output) == (
        0,
        output if preserve_output else "value",
    )
    assert command.run_cmd(["synthetic"]) == (0, "value")


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "extra",
        "read_error",
        "bad_uuid",
        "wrong_iface",
        "vpn_type",
        "unknown_auto",
        "inactive",
    ],
)
def test_invalid_profiles_still_abort_before_mutation(network, defect):
    state, service = network
    if defect == "missing":
        state.fields.pop()
    elif defect == "extra":
        state.fields.append("")
    elif defect == "read_error":
        state.read_rc = 1
    elif defect == "bad_uuid":
        state.fields[0] = "not-a-uuid"
    elif defect == "wrong_iface":
        state.fields[1] = "wg0"
    elif defect == "vpn_type":
        state.fields[2] = "wireguard"
    elif defect == "unknown_auto":
        state.fields[3] = "unknown"
    else:
        state.active_uuid = "87654321-4321-8765-2109-cba987654321"

    ok, details = service.apply_nm_dns_policy_to_targets(
        ignore_auto_dns=True, targets=[TARGET]
    )

    assert not ok and details
    assert not any(args[0] == "sudo" for args in state.commands)


@pytest.mark.parametrize("fail_activation", [False, True])
def test_manual_google_choice_with_empty_dns_fields(network, fail_activation):
    state, service = network
    state.fail_activation = fail_activation
    followup = []
    app = SimpleNamespace(
        _dns_control_service=lambda: service,
        is_vpn_active=lambda: False,
        _apply_nm_dns_policy_to_targets=lambda **kwargs: service.apply_nm_dns_policy_to_targets(
            targets=[TARGET], **kwargs
        ),
        _read_dot_dropin=lambda: followup.append("read"),
        _write_manual_dns_dropin=lambda choice: (followup.append(choice) or True, ""),
        _restart_resolved_for_dns_policy=lambda: (
            followup.append("restart") or True,
            "",
        ),
    )

    result = dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )

    assert result["success"] is (not fail_activation)
    assert result["servers"] == ["8.8.8.8", "8.8.4.4"]
    assert state.fields[3:] == ["yes", "yes", "", ""]
    assert followup == (
        [] if fail_activation else ["read", "Google (8.8.8.8)", "restart"]
    )
    assert (
        sum(
            args[:5] == ["sudo", "-n", "nmcli", "con", "mod"] for args in state.commands
        )
        == 1
    )
    assert (
        sum(args[:5] == ["sudo", "-n", "nmcli", "con", "up"] for args in state.commands)
        == 1
    )
