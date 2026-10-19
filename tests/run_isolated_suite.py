"""Run pytest without host services, external networking or writable host state.

Requires existing bubblewrap and Xvfb; never installs tools or invokes sudo.
All persistent output goes into one newly created directory under /tmp.
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--php", type=Path)
    options, pytest_args = parser.parse_known_args()
    root = Path(__file__).resolve().parents[1]
    for program in ("bwrap", "xvfb-run"):
        if shutil.which(program) is None:
            parser.error(f"Required existing tool missing: {program}")
    output = Path(tempfile.mkdtemp(prefix="netmon-isolation-"))
    for name in ("home", "tmp", "runtime", "config", "cache", "data"):
        (output / name).mkdir(mode=0o700)
    # Certificate fixtures need req settings, not the host's OpenSSL config.
    openssl_config = output / "config" / "openssl.cnf"
    openssl_config.write_text(
        "[req]\n"
        "prompt = no\n"
        "distinguished_name = test_dn\n"
        "[test_dn]\n"
        "CN = isolated-test.invalid\n"
    )
    openssl_config.chmod(0o600)
    (output / "hosts").write_text("127.0.0.1 localhost\n::1 localhost\n")
    (output / "passwd").write_text(
        f"root:x:0:0:root:/root:/bin/false\n"
        f"happy:x:{os.getuid()}:{os.getgid()}:Test:/work/home:/bin/sh\n"
    )
    (output / "group").write_text(f"happy:x:{os.getgid()}:\n")
    command = [
        "bwrap",
        "--unshare-user",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--clearenv",
    ]
    for source in ("/usr", "/lib", "/lib64"):
        if Path(source).exists():
            command += ["--ro-bind", source, source]
    command += [
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
        "/home",
        "--dir",
        "/root",
        "--dir",
        "/etc",
        "--bind",
        str(output),
        "/work",
        "--ro-bind",
        str(root),
        str(root),
        "--chdir",
        str(root),
    ]
    for name in ("ld.so.cache", "alternatives", "fonts"):
        source = Path("/etc") / name
        if source.exists():
            command += ["--ro-bind", str(source), str(source)]
    for name in ("hosts", "passwd", "group"):
        command += ["--ro-bind", str(output / name), f"/etc/{name}"]
    for name in ("secure-browser", ".aws", ".codex", ".agents"):
        path = root / name
        if path.is_dir():
            command += ["--tmpfs", str(path)]
    environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": "/work/home",
        "USER": "happy",
        "TMPDIR": "/work/tmp",
        "XDG_RUNTIME_DIR": "/work/runtime",
        "XDG_CONFIG_HOME": "/work/config",
        "XDG_CACHE_HOME": "/work/cache",
        "XDG_DATA_HOME": "/work/data",
        "OPENSSL_CONF": "/work/config/openssl.cnf",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
        "LC_ALL": "C.UTF-8",
        "TZ": "Europe/Berlin",
        "NETMON_TEST_ISOLATED": "1",
        "NETMON_PARENT_NET_NS": os.readlink("/proc/self/ns/net"),
    }
    if options.php:
        php = options.php.resolve(strict=True)
        command += ["--ro-bind", str(php), "/opt/test-php"]
        environment["NETMON_TEST_PHP"] = "/opt/test-php"
    for key, value in environment.items():
        command += ["--setenv", key, value]
    python = str(root / ".venv/bin/python")
    if options.probe:
        command += [python, "-B", "-c", PROBE]
    else:
        command += [
            "xvfb-run",
            "-a",
            "-e",
            "/work/xvfb.log",
            "-s",
            "-screen 0 1280x1024x24 -nolisten tcp -extension GLX",
            python,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--basetemp=/work/tmp/pytest",
            "--junitxml=/work/junit.xml",
            *([] if "--netmon-audit-continue" in pytest_args else ["--maxfail=1"]),
            *(
                pytest_args
                or [
                    "-q",
                    "-rs",
                    "--tb=short",
                    "tests",
                    "tools/secure_browser_manager/tests/test_browser_container_builder.py",
                ]
            ),
        ]
    print(f"Isolated output: {output}", flush=True)
    result = subprocess.run(command, check=False)
    return result.returncode


PROBE = """
import os, pathlib
assert os.geteuid() != 0
assert os.readlink('/proc/self/ns/net') != os.environ['NETMON_PARENT_NET_NS']
assert 'NoNewPrivs:\\t1' in pathlib.Path('/proc/self/status').read_text()
assert os.statvfs(os.getcwd()).f_flag & os.ST_RDONLY
assert os.environ['OPENSSL_CONF'] == '/work/config/openssl.cnf'
assert pathlib.Path(os.environ['OPENSSL_CONF']).is_file()
assert not pathlib.Path('/run/dbus/system_bus_socket').exists()
assert not pathlib.Path('/run/systemd/private').exists()
assert not pathlib.Path('/etc/wireguard').exists()
assert not pathlib.Path('/etc/NetworkManager').exists()
assert not pathlib.Path('/home/happy').exists()
assert len(pathlib.Path('/proc/net/route').read_text().splitlines()) == 1
print('Isolation verified: non-root, no-new-privileges, read-only project, '
      'private network without routes, no host home/keys/service sockets')
"""


if __name__ == "__main__":
    sys.exit(main())
