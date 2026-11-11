"""Real installed UFW code; capability-free private filesystem and kernel stub.

No real netfilter, host configuration, service socket or network is accessible.
The kernel bookkeeper derives from the user's independent review harness.
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    os.umask(0o022)
    root = Path(__file__).resolve().parents[1]
    output = Path(tempfile.mkdtemp(prefix="netmon-native-ufw-"))
    for name in (
        "etc/ufw/applications.d",
        "etc/default",
        "var/lib",
        "kernel",
        "home",
        "tmp",
    ):
        (output / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    script = root / "tests/native_ufw/fake_iptables.py"
    args = [
        "bwrap",
        "--unshare-user",
        "--uid",
        "0",
        "--gid",
        "0",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--clearenv",
        "--ro-bind",
        "/usr",
        "/usr",
        "--tmpfs",
        "/usr/sbin",
    ]
    for tool in (
        "iptables",
        "ip6tables",
        "iptables-save",
        "ip6tables-save",
        "iptables-restore",
        "ip6tables-restore",
        "sysctl",
        "modprobe",
    ):
        args += ["--ro-bind", str(script), "/usr/sbin/" + tool]
    for path in ("/lib", "/lib64"):
        args += ["--ro-bind", path, path]
    args += [
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/sbin",
        "/sbin",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/run",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/etc",
    ]
    for name in ("ld.so.cache", "alternatives"):
        args += ["--ro-bind", "/etc/" + name, "/etc/" + name]
    for name in ("ufw", "default"):
        args += ["--bind", str(output / "etc" / name), "/etc/" + name]
    args += [
        "--bind",
        str(output / "var"),
        "/var",
        "--bind",
        str(output),
        "/work",
        "--ro-bind",
        str(root),
        str(root),
        "--ro-bind",
        str(root / "tests/native_ufw"),
        "/sim",
        "--chdir",
        str(root),
    ]
    env = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": "/work/home",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONPATH": str(root) + ":/usr/lib/python3/dist-packages:/sim",
        "TMPDIR": "/work/tmp",
        "NETMON_NATIVE_UFW_ISOLATED": "1",
        "NETMON_PARENT_NET_NS": os.readlink("/proc/self/ns/net"),
    }
    for key, value in env.items():
        args += ["--setenv", key, value]
    # The normal suite forbids even installed-path stub executables. This
    # separate harness instead proves private namespaces, zero capabilities and
    # all eight replaced executables before importing real UFW or running tests.
    args += [
        str(root / ".venv/bin/python"),
        "-B",
        "-m",
        "pytest",
        "--confcutdir=" + str(root / "tests/native_ufw"),
        "-p",
        "no:cacheprovider",
        "--basetemp=/work/tmp/pytest",
        "--junitxml=/work/junit.xml",
        *(sys.argv[1:] or ["-q", "--tb=short", "tests/native_ufw"]),
    ]
    print("Native UFW sandbox output:", output, flush=True)
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )
    (output / "console.log").write_text(result.stdout)
    print(result.stdout, end="", flush=True)
    return result.returncode


if __name__ == "__main__":
    if shutil.which("bwrap") is None:
        raise SystemExit("Existing bwrap required; no unisolated fallback")
    raise SystemExit(main())
