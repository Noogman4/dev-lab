"""Suite-weiter Schutz: blockiert destruktive Systemkommandos in Tests.

Hintergrund (Audit Runde 10): Zwei Tests ließen einen gestubbten
Kommando-Generator das echte ["systemctl", "reboot"] zurückgeben, ohne
run_cmd/subprocess zu mocken — auf einem Desktop-Host darf ein aktiver
Nutzer über polkit ohne Passwort rebooten, der Testlauf hat den Rechner
also tatsächlich neu gestartet. Dieser Guard fängt solche Fälle auf
subprocess-Ebene ab, bevor sie das System erreichen: subprocess.run/
call/check_output laufen alle über Popen.
"""

import ipaddress
import os
from pathlib import Path
import shlex
import socket
import subprocess
import traceback

import pytest

_HOST_COMMANDS = {
    "sudo",
    "pkexec",
    "doas",
    "nmcli",
    "wg",
    "wg-quick",
    "ufw",
    "resolvectl",
    "systemctl",
    "service",
    "loginctl",
    "sysctl",
    "ip",
    "ifconfig",
    "iptables",
    "ip6tables",
    "nft",
    "reboot",
    "poweroff",
    "shutdown",
    "halt",
    "telinit",
}
_host_attempts = []
_continue_audit = False


def _record_host_attempt(kind, target):
    # Do not record command arguments, stdin, environment or configuration data.
    frames = traceback.extract_stack(limit=8)[:-1]
    _host_attempts.append(
        (kind, target, [(f.filename, f.lineno, f.name) for f in frames])
    )
    message = f"Hostzugriffs-Guard: {kind} {target}; Test-Fake erforderlich"
    if _continue_audit:
        raise AssertionError(message)
    pytest.exit(message, returncode=1)


def _reject_host_command(args, *, executable=None, shell=False):
    argv = shlex.split(args) if isinstance(args, str) else list(args)
    if not argv:
        return
    candidates = [os.fsdecode(executable or argv[0])]
    for candidate in candidates:
        path = Path(candidate)
        # Executable synthetic test fixtures are allowed; installed tools are not.
        installed = not path.is_absolute() or str(path).startswith(
            ("/usr/", "/bin/", "/sbin/")
        )
        if installed and path.name in _HOST_COMMANDS:
            if path.name == "systemctl" and argv[1:] == ["--version"]:
                return
            _record_host_attempt("command", path.name)
    if shell:
        _record_host_attempt("shell", "unparsed shell command")


def _reject_network(address, family):
    if family not in (socket.AF_INET, socket.AF_INET6):
        return
    host = address[0]
    if isinstance(host, bytes):
        host = host.decode("ascii")
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = False
    if not local or os.environ.get("NETMON_TEST_ISOLATED") != "1":
        _record_host_attempt("network", "non-isolated or non-loopback address")


class _GuardedSocket(socket.socket):
    def connect(self, address):
        _reject_network(address, self.family)
        return super().connect(address)

    def connect_ex(self, address):
        _reject_network(address, self.family)
        return super().connect_ex(address)

    def sendto(self, data, *args):
        _reject_network(args[-1], self.family)
        return super().sendto(data, *args)


socket.socket = _GuardedSocket


def pytest_addoption(parser):
    parser.addoption(
        "--netmon-audit-continue",
        action="store_true",
        help="Reproduce known blocked accesses; never permits the actual access",
    )


def pytest_configure(config):
    global _continue_audit
    _continue_audit = config.getoption("--netmon-audit-continue")


@pytest.fixture(autouse=True)
def verify_no_unexpected_host_access():
    start = len(_host_attempts)
    yield
    assert not _host_attempts[
        start:
    ], f"Blocked host accesses: {_host_attempts[start:]}"


def pytest_sessionfinish(session, exitstatus):
    if _host_attempts:
        session.exitstatus = 1


_PRIVILEGE_WRAPPERS = {"sudo", "pkexec", "doas", "env", "nice", "ionice"}

# Kommando -> verbotene Unterkommandos (None = jeder Aufruf ist verboten)
_DESTRUCTIVE_COMMANDS = {
    "systemctl": {
        "reboot",
        "poweroff",
        "halt",
        "suspend",
        "hibernate",
        "hybrid-sleep",
        "kexec",
        "isolate",
    },
    "loginctl": {
        "terminate-user",
        "terminate-session",
        "kill-user",
        "kill-session",
        "reboot",
        "poweroff",
    },
    "shutdown": None,
    "reboot": None,
    "poweroff": None,
    "halt": None,
    "telinit": None,
}


def _normalized_argv(args):
    if isinstance(args, (str, bytes)):
        text = args.decode(errors="replace") if isinstance(args, bytes) else args
        argv = text.split()
    else:
        try:
            argv = [str(part) for part in args]
        except TypeError:
            return []
    while argv:
        head = argv[0].rsplit("/", 1)[-1]
        if head in _PRIVILEGE_WRAPPERS or head.startswith("-") or "=" in head:
            argv = argv[1:]
            continue
        break
    return argv


def _reject_destructive(args):
    argv = _normalized_argv(args)
    if not argv:
        return
    command = argv[0].rsplit("/", 1)[-1]
    if command not in _DESTRUCTIVE_COMMANDS:
        return
    forbidden_subcommands = _DESTRUCTIVE_COMMANDS[command]
    if forbidden_subcommands is None or any(
        part in forbidden_subcommands for part in argv[1:]
    ):
        raise RuntimeError(
            "Testsuite-Guard: destruktives Systemkommando blockiert: "
            f"{argv!r}. Echte Reboot-/Shutdown-/Logout-Kommandos duerfen in "
            "Tests nie ausgefuehrt werden — subprocess/run_cmd mocken."
        )


class _GuardedPopen(subprocess.Popen):
    def __init__(self, args, *popen_args, **popen_kwargs):
        _reject_destructive(args)
        _reject_host_command(
            args,
            executable=popen_kwargs.get("executable"),
            shell=popen_kwargs.get("shell", False),
        )
        super().__init__(args, *popen_args, **popen_kwargs)


subprocess.Popen = _GuardedPopen
