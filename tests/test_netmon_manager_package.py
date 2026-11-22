"""Independent management package tests; APT/system actions are synthetic."""

import importlib.util
import os
import re
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/netmon_uninstall_menu.sh"


def shell(body, inputs=""):
    return subprocess.run(
        ["/bin/bash", "-p", "-c", 'source "$1"\n' + body, "fixture", str(SCRIPT)],
        input=inputs,
        text=True,
        capture_output=True,
        timeout=15,
    )


@pytest.mark.parametrize(
    "approval,removed", [("n\n", False), ("", False), ("y\n", True)]
)
def test_manager_only_does_not_touch_app_data_or_firewall(approval, removed):
    result = shell(
        """
ensure_root() { :; }
target_home() { printf '/synthetic\\n'; }
detect_netmon_language() { NETMON_LANG_CODE=en; }
check_firewall_transaction() { printf 'FORBIDDEN'; return 90; }
run_checked_cleanup() { printf 'FORBIDDEN'; return 90; }
apt-get() { [[ "$*" == 'remove -y netmon-manager' ]] || return 91; printf 'MANAGER-REMOVED\\n'; }
main --mode manager
""",
        inputs=approval,
    )
    assert result.returncode == 0, result.stderr
    assert "FORBIDDEN" not in result.stdout
    assert ("MANAGER-REMOVED" in result.stdout) == removed


@pytest.mark.parametrize(
    "args",
    [
        "--mode keep --remove-manager",
        "--mode manager --remove-manager",
        "--mode delete --other",
    ],
)
def test_bad_removal_plan_never_requests_root(args):
    result = shell("ensure_root() { printf FORBIDDEN; }\nmain " + args)
    assert result.returncode != 0
    assert "FORBIDDEN" not in result.stdout


@pytest.mark.parametrize(
    "remove_app,remove_manager,expected",
    [
        ("ja", "nein", "remove -y netmon"),
        ("ja", "ja", "remove -y netmon netmon-manager"),
        ("nein", "nein", ""),
    ],
)
def test_fixed_package_targets(remove_app, remove_manager, expected):
    result = shell(
        "apt-get() { printf '%s' \"$*\"; }\n"
        f"remove_selected_packages {remove_app} {remove_manager}"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.fixture(scope="module")
def manager_package(tmp_path_factory):
    folder = tmp_path_factory.mktemp("independent-manager")
    archive = folder / "manager.deb"
    subprocess.run(
        [
            "/usr/bin/python3",
            "-B",
            str(ROOT / "scripts/build_netmon_manager_deb.py"),
            "--output",
            str(archive),
        ],
        check=True,
        capture_output=True,
    )
    tree = folder / "extracted"
    subprocess.run(["dpkg-deb", "-R", str(archive), str(tree)], check=True)
    return archive, tree


def test_package_has_no_app_dependency_or_shared_ownership(manager_package):
    archive, tree = manager_package
    depends = subprocess.check_output(
        ["dpkg-deb", "-f", str(archive), "Depends"], text=True
    )
    assert "netmon" not in depends
    assert "netmon (<< 1.1.22~beta3)" in (tree / "DEBIAN/control").read_text()
    assert not (tree / "usr/lib/netmon").exists()
    assert (tree / "usr/share/pixmaps/netmon-manager.png").is_file()
    for name in ("netmon-install", "netmon-manage", "netmon-uninstall"):
        path = tree / "usr/bin" / name
        assert path.stat().st_mode & 0o777 == 0o755
        assert "/usr/lib/netmon-manager" in path.read_text()
    subprocess.run(
        ["md5sum", "-c", "DEBIAN/md5sums"], cwd=tree, check=True, capture_output=True
    )


def test_private_backup_and_protected_checks_work_without_app(
    manager_package, tmp_path
):
    _, tree = manager_package
    private = tree / "usr/lib/netmon-manager"
    home = tmp_path / "home"
    (home / ".config").mkdir(parents=True)
    (home / ".config/user-dirs.dirs").write_text(
        'XDG_DOCUMENTS_DIR="$HOME/Documents"\n'
    )
    data = home / "Documents/NetMon/Config"
    data.mkdir(parents=True)
    (data / "config.json").write_text('{"fixture": true}')
    code = """
import json,sys,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from netmon import manage_assistant, install_assistant
from netmon.core import lifecycle
assert manage_assistant.__file__.startswith(sys.argv[1])
receipt=lifecycle.backup_for_update(Path.home()/'backups')
assert receipt['files_verified'] == 1
assert (Path.home()/'Documents/NetMon/Config/config.json').is_file()
# Do not execute privileged main. Gate reads private fixtures only.
from netmon.core import ufw_snapshot
store=ufw_snapshot.SnapshotStore(ufw_snapshot.NativeUfw(), root=Path(sys.argv[2]), owner=os.getuid())
assert store.removal() == {'removable': True}
print(json.dumps(receipt))
"""
    # Determine constructor parameter from actual helper; no privileged operation.
    spec = importlib.util.spec_from_file_location(
        "fixture_helper", private / "netmon/core/ufw_snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import inspect

    assert "root" in inspect.signature(module.SnapshotStore).parameters
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"))
    result = subprocess.run(
        [
            "/usr/bin/python3",
            "-I",
            "-c",
            code,
            str(private),
            str(tmp_path / "absent-state"),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for name in ("ufw_snapshot.py", "nm_ownership.py"):
        original = (ROOT / "netmon/core" / name).read_text()
        assert (private / "netmon/core" / name).read_text() == original.replace(
            "/usr/lib/netmon", "/usr/lib/netmon-manager"
        )


@pytest.mark.parametrize("execute", [False, True])
def test_combined_removal_still_requires_final_confirmation(execute):
    result = shell(
        """
ensure_root() { :; }
target_home() { printf '/synthetic\\n'; }
target_user() { printf 'synthetic\\n'; }
detect_netmon_language() { NETMON_LANG_CODE=en; }
check_firewall_transaction() { :; }
ensure_netmon_not_running() { :; }
pause_before_exit() { :; }
run_checked_cleanup() { printf 'PLANNED-ACTION %s\\n' "$*"; }
main --mode delete --remove-manager
""",
        inputs="y\nn\nn\nn\nn\nn\nn\nn\n" + ("y\n" if execute else "n\n"),
    )
    assert result.returncode == 0, result.stderr
    assert "Start execution now?" in result.stdout
    # The confirmation prompt has no trailing newline in captured terminal output.
    actions = re.findall(r"PLANNED-ACTION [^\n]+", result.stdout)
    assert actions == (
        [
            "PLANNED-ACTION remove_user_data ja",
            "PLANNED-ACTION remove_selected_packages ja ja",
        ]
        if execute
        else []
    )
