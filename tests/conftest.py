"""Suite-weiter Schutz: blockiert destruktive Systemkommandos in Tests.

Hintergrund (Audit Runde 10): Zwei Tests ließen einen gestubbten
Kommando-Generator das echte ["systemctl", "reboot"] zurückgeben, ohne
run_cmd/subprocess zu mocken — auf einem Desktop-Host darf ein aktiver
Nutzer über polkit ohne Passwort rebooten, der Testlauf hat den Rechner
also tatsächlich neu gestartet. Dieser Guard fängt solche Fälle auf
subprocess-Ebene ab, bevor sie das System erreichen: subprocess.run/
call/check_output laufen alle über Popen.
"""

import subprocess

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
        super().__init__(args, *popen_args, **popen_kwargs)


subprocess.Popen = _GuardedPopen
