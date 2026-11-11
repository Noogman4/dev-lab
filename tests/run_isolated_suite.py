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

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--radio-sandbox-probe", action="store_true")
    parser.add_argument("--radio-output-gate-probe", action="store_true")
    parser.add_argument("--radio-output-link-probe", action="store_true")
    parser.add_argument("--radio-stream-probe", action="store_true")
    parser.add_argument("--radio-gui-probe", action="store_true")
    parser.add_argument("--radio-projectm-handover-probe", action="store_true")
    parser.add_argument("--radio-security-probe", action="store_true")
    parser.add_argument("--projectm-audio-probe", action="store_true")
    parser.add_argument("--projectm-display-probe", action="store_true")
    parser.add_argument("--projectm-frontend-probe", action="store_true")
    parser.add_argument("--projectm-ui-probe", action="store_true")
    parser.add_argument("--projectm-pixel-probe", action="store_true")
    parser.add_argument("--projectm-pixel-benchmark", action="store_true")
    parser.add_argument("--projectm-pixel-ui-probe", action="store_true")
    parser.add_argument("--php", type=Path)
    parser.add_argument("--output-dir", type=Path)
    options, pytest_args = parser.parse_known_args()
    root = Path(__file__).resolve().parents[1]
    for program in ("bwrap", "xvfb-run"):
        if shutil.which(program) is None:
            parser.error(f"Required existing tool missing: {program}")
    if options.output_dir:
        output = options.output_dir.resolve()
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
    else:
        output = Path(tempfile.mkdtemp(prefix="netmon-isolation-"))
    if options.radio_output_gate_probe or options.radio_output_link_probe:
        if (
            pytest_args
            or any(
                value
                for key, value in vars(options).items()
                if key
                not in {
                    "radio_output_gate_probe",
                    "radio_output_link_probe",
                    "output_dir",
                }
            )
            or (options.radio_output_gate_probe and options.radio_output_link_probe)
        ):
            parser.error("Radio output probes accept no other test options")
        if options.radio_output_gate_probe:
            from radio_output_gate_probe import run
        else:
            from radio_output_link_probe import run

        return run(root, output)
    if (
        options.projectm_pixel_probe
        or options.projectm_pixel_benchmark
        or options.projectm_pixel_ui_probe
    ):
        if any(
            (
                options.probe,
                options.radio_sandbox_probe,
                options.radio_stream_probe,
                options.radio_gui_probe,
                options.radio_projectm_handover_probe,
                options.radio_security_probe,
                options.projectm_audio_probe,
                options.projectm_display_probe,
                options.projectm_frontend_probe,
                options.projectm_ui_probe,
                options.php,
                pytest_args,
                sum(
                    (
                        options.projectm_pixel_probe,
                        options.projectm_pixel_benchmark,
                        options.projectm_pixel_ui_probe,
                    )
                )
                != 1,
            )
        ):
            parser.error("Pixel prototype does not accept other test options")
        if options.projectm_pixel_ui_probe:
            from projectm_pixel_ui_probe import run
        elif options.projectm_pixel_benchmark:
            from projectm_pixel_benchmark import run
        else:
            from projectm_pixel_probe import run

        return run(root, output)
    if options.projectm_ui_probe:
        if any(
            (
                options.probe,
                options.radio_sandbox_probe,
                options.radio_stream_probe,
                options.radio_gui_probe,
                options.radio_projectm_handover_probe,
                options.radio_security_probe,
                options.projectm_audio_probe,
                options.projectm_display_probe,
                options.projectm_frontend_probe,
                options.php,
                pytest_args,
            )
        ):
            parser.error("Private projectM UI probe does not accept other test options")
        from projectm_ui_probe import run

        return run(root, output)
    if options.projectm_display_probe or options.projectm_frontend_probe:
        if any(
            (
                options.probe,
                options.radio_sandbox_probe,
                options.radio_stream_probe,
                options.radio_gui_probe,
                options.radio_projectm_handover_probe,
                options.radio_security_probe,
                options.projectm_audio_probe,
                options.projectm_display_probe and options.projectm_frontend_probe,
                options.php,
                pytest_args,
            )
        ):
            parser.error("Private display probe does not accept other test options")
        from projectm_display_probe import run

        return run(root, output, frontend=options.projectm_frontend_probe)
    if options.projectm_audio_probe:
        if any(
            (
                options.probe,
                options.radio_sandbox_probe,
                options.radio_stream_probe,
                options.radio_gui_probe,
                options.radio_projectm_handover_probe,
                options.radio_security_probe,
                options.php,
                pytest_args,
            )
        ):
            parser.error("Private audio probe does not accept other test options")
        from projectm_audio_probe import run

        return run(root, output)
    if (
        options.radio_stream_probe
        or options.radio_gui_probe
        or options.radio_projectm_handover_probe
        or options.radio_security_probe
    ):
        if options.probe or options.radio_sandbox_probe or options.php or pytest_args:
            parser.error("Radio stream probe does not accept other test options")
        if (
            sum(
                (
                    options.radio_stream_probe,
                    options.radio_gui_probe,
                    options.radio_projectm_handover_probe,
                    options.radio_security_probe,
                )
            )
            != 1
        ):
            parser.error("Choose one radio integration probe")
        from radio_stream_probe import run

        return run(
            root,
            output,
            gui=options.radio_gui_probe or options.radio_projectm_handover_probe,
            projectm=options.radio_projectm_handover_probe,
            security=options.radio_security_probe,
        )
    if options.radio_sandbox_probe:
        if options.probe or options.php or pytest_args:
            parser.error(
                "Radio probe does not accept pytest, PHP or other probe options"
            )
        # Each subject runs in the playback policy itself, offline/null audio.
        # No unisolated pytest or nested user namespace is needed here.
        from radio_sandbox_probe import run

        return run(root, output)
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
        "PYTHONPYCACHEPREFIX": "/nonexistent",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
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
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    (output / "console.log").write_text(result.stdout)
    print(result.stdout, end="", flush=True)
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
