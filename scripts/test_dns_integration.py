"""Repeatable DNS development test selections using the existing isolation runner."""

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PHASES = {
    "unit": [
        "tests/test_dns_integration_smoke.py::test_dns_imports_from_this_copy",
        "tests/test_core_utils.py",
        "tests/test_core_tooling.py",
        "tests/test_dot_controller.py",
        "tests/test_dns_privileged_config.py",
    ],
    "dns-unit": [
        "tests/test_dns_guard_feedback.py",
        "tests/test_dns_v2_regressions.py",
        "-k",
        "multiple_vpn_links or invalid_ip or contradictory_routes or specific_domain "
        "or global_search_domain or legitimate_split or split_default or missing_vpn_dns",
    ],
    "integration": [
        "tests/test_dns_guard_feedback.py",
        "tests/test_dns_v2_regressions.py",
        "tests/test_netmon_dns_consistency.py",
        "tests/test_dns_v3_known_issues.py",
    ],
    "48": ["tests/test_netmon_killswitch.py"],
    "regressions": [
        "tests/test_netmon_ipv6_ui.py",
        "tests/test_firewall_controller.py",
        "tests/test_wireguard_interface_security.py",
        "tests/test_manual_wireguard_security.py",
        "tests/test_killswitch_failure_recovery.py",
        "tests/test_settings_sync.py",
        "tests/test_netmon_lynis_output.py",
        "tests/test_ufw_locale.py",
        "tests/test_host_access_guard.py",
        "tests/test_destructive_command_guard.py",
    ],
    "gui": [
        "tests/test_dns_integration_smoke.py",
        "tests/test_netmon_startup_instance.py",
    ],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["all", *PHASES], nargs="?", default="all")
    args = parser.parse_args()
    for directory in (ROOT / "netmon", ROOT / "tests"):
        for path in directory.rglob("*.py"):
            compile(path.read_bytes(), str(path), "exec")
    print("Syntax check passed without imports or bytecode output", flush=True)
    output = Path(tempfile.mkdtemp(prefix="netmon-dns-development-"))
    selected = PHASES if args.phase == "all" else {args.phase: PHASES[args.phase]}
    for name, tests in selected.items():
        command = [
            sys.executable,
            "-B",
            str(ROOT / "tests/run_isolated_suite.py"),
            "--output-dir",
            str(output / name),
            "-q",
            "-rs",
            "--tb=short",
            *tests,
        ]
        print(f"DNS phase {name}; evidence: {output / name}", flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
