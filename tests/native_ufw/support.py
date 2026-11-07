"""Shared setup: genuine ufw-managed state on a fake kernel."""

import copy
import gettext
import glob
import os
import shutil
import subprocess

gettext.install("ufw")
import ufw.common  # noqa: E402
import ufw.frontend  # noqa: E402

import ufw.util  # noqa: E402

from netmon.core import ufw_snapshot as us  # noqa: E402

DEFAULT = (
    'IPV6=yes\nDEFAULT_INPUT_POLICY="DROP"\nDEFAULT_OUTPUT_POLICY="ACCEPT"\n'
    'DEFAULT_FORWARD_POLICY="DROP"\nDEFAULT_APPLICATION_POLICY="SKIP"\n'
    "MANAGE_BUILTINS=no\nIPT_MODULES=\n"
)


class Native(us.NativeUfw):
    # Ownership proof needs real WireGuard links; identity is not under test here.
    def verify_interface(self, name):
        return None


def fresh_system(loglevel="low"):
    for f in glob.glob("/work/kernel/*"):
        os.remove(f)
    shutil.rmtree("/var/lib/netmon", ignore_errors=True)
    for name in (
        "user.rules",
        "user6.rules",
        "before.rules",
        "before6.rules",
        "after.rules",
        "after6.rules",
    ):
        shutil.copy(f"/usr/share/ufw/iptables/{name}", f"/etc/ufw/{name}")
        os.chmod(f"/etc/ufw/{name}", 0o640)
    with open("/etc/default/ufw", "w") as f:
        f.write(DEFAULT)
    os.chmod("/etc/default/ufw", 0o644)
    with open("/etc/ufw/ufw.conf", "w") as f:
        f.write(f"ENABLED=no\nLOGLEVEL={loglevel}\n")
    os.chmod("/etc/ufw/ufw.conf", 0o644)
    return ufw_cli(["--force", "enable"])


def ufw_cli(arguments):
    """Equivalent of an out-of-band `ufw ...` (uses the real ufw code paths)."""
    try:
        with us._ufw_output():
            ui = ufw.frontend.UFWFrontend(False)
            parsed = ufw.frontend.parse_command(["ufw", *arguments])
            result = ui.do_action(
                parsed.action,
                parsed.data.get("rule", ""),
                parsed.data.get("iptype", ""),
                parsed.force,
            )
        return 0, str(result or "")
    except (Exception, SystemExit):
        return 1, "Out-of-band UFW command failed"


def reboot():
    for f in glob.glob("/work/kernel/*.json"):
        os.remove(f)
    return subprocess.run(
        ["/lib/ufw/ufw-init", "start", "quiet"], capture_output=True, text=True
    )


def store():
    return us.SnapshotStore(Native())


ON = [
    ["default", "deny", "outgoing"],
    ["default", "deny", "incoming"],
    ["allow", "in", "on", "lo"],
    ["allow", "out", "on", "lo"],
    ["allow", "out", "on", "wg0"],
    ["allow", "in", "on", "wg0"],
    ["allow", "out", "to", "198.51.100.10", "port", "51820", "proto", "udp"],
]
PLAN = {"interfaces": ["wg0"], "endpoints": [["198.51.100.10", "51820"]]}


def activate(s, plan=PLAN, commands=ON):
    token = s.begin(copy.deepcopy(plan))["token"]
    results = []
    for command in commands:
        results.append((" ".join(command), s.command(token, command)["rc"]))
    return token, results


def diff_runtime(a, b):
    out = []
    for fam in ("4", "6"):
        left, right = set(a[fam]), set(b[fam])
        out += [f"v{fam} only-expected: {x}" for x in sorted(left - right)]
        out += [f"v{fam} only-actual:   {x}" for x in sorted(right - left)]
    return out


def attempt(label, fn):
    try:
        print(f"{label}: {fn()}")
    except BaseException as exc:  # noqa: BLE001
        code = getattr(exc, "code", "")
        print(f"{label}: RAISED {type(exc).__name__}({exc}) code={code}")
