"""Assistant tests use synthetic DEBs/profiles; sudo and APT are always fakes."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
import stat
import tarfile
from types import SimpleNamespace

import pytest

from netmon import install_assistant as assistant
from netmon.core import lifecycle

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def deb(tmp_path):
    tree = tmp_path / "payload"
    control = tree / "DEBIAN"
    control.mkdir(parents=True)
    control.chmod(0o755)
    (control / "control").write_text(
        "Package: netmon\nVersion: 99.0\nArchitecture: all\nMaintainer: Fixture <test@example.invalid>\nDescription: synthetic\n"
    )
    for name in assistant.MODULES:
        target = tree / "usr/lib/netmon" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    archive = tmp_path / "fixture.deb"
    subprocess.run(
        ["/usr/bin/dpkg-deb", "--build", str(tree), str(archive)],
        check=True,
        capture_output=True,
    )
    return archive


@pytest.fixture
def account(tmp_path, monkeypatch):
    home = tmp_path / "account with spaces"
    (home / ".config").mkdir(parents=True)
    documents = home / "Meine Unterlagen"
    documents.mkdir()
    (home / ".config/user-dirs.dirs").write_text(
        'XDG_DOCUMENTS_DIR="$HOME/Meine Unterlagen"\n'
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        assistant.pwd,
        "getpwuid",
        lambda _: SimpleNamespace(pw_dir=str(home), pw_name="synthetic"),
    )
    return home, documents


@pytest.mark.parametrize(
    "current,has_data", [("", False), ("1.0", False), ("1.0", True), ("", True)]
)
def test_new_install_update_and_reinstall_with_real_incoming_backup_tools(
    deb, account, monkeypatch, current, has_data, capsys
):
    _, documents = account
    source = documents / "NetMon"
    if has_data:
        (source / "Config").mkdir(parents=True)
        (source / "Config/config.json").write_text('{"fixture":"unchanged"}')
    monkeypatch.setattr(assistant, "installed_version", lambda: current)
    monkeypatch.setattr(assistant, "ensure_closed", lambda: None)

    def approve(_message):
        assert "mehrere Minuten" in capsys.readouterr().out
        return True

    monkeypatch.setattr(assistant, "confirm", approve)
    real_run = subprocess.run
    installs = []

    def fake_sudo(args, **kwargs):
        if args[0] != "/usr/bin/sudo":
            return real_run(args, **kwargs)
        installs.append(args)
        assert args[:5] == ["/usr/bin/sudo", "--", "/usr/bin/python3", "-I", "-c"]
        assert args[5] == assistant.ROOT_INSTALL
        assert args[-1] == current
        assert hashlib.sha256(Path(args[-3]).read_bytes()).hexdigest() == args[-2]
        manifests = list(
            (documents / "NetMon-Sicherungen").glob(
                "*/netmon_documents_backup_manifest.json"
            )
        )
        assert bool(manifests) == has_data
        if has_data:
            assert json.loads(manifests[0].read_text())["kind"] == "full"
            assert (
                source / "Config/config.json"
            ).read_text() == '{"fixture":"unchanged"}'
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(assistant.subprocess, "run", fake_sudo)
    assert assistant.run_assistant(deb) == 0
    assert len(installs) == 1
    assert source.exists() == has_data


@pytest.mark.parametrize("failure", ["cancel", "backup", "legacy", "running"])
def test_abort_conditions_never_request_sudo_or_apt(deb, account, monkeypatch, failure):
    home, documents = account
    if failure == "legacy":
        (home / ".config/netmon").mkdir()
        (home / ".config/netmon/config.json").write_text("{}")
    else:
        (documents / "NetMon/Config").mkdir(parents=True)
        (documents / "NetMon/Config/config.json").write_text("{}")
    monkeypatch.setattr(assistant, "installed_version", lambda: "1.0")

    def close_check():
        if failure == "running":
            raise ValueError("running")

    monkeypatch.setattr(assistant, "ensure_closed", close_check)
    monkeypatch.setattr(assistant, "confirm", lambda _: failure != "cancel")
    real_tool = assistant.run_backup_tool

    def tool(tools, operation, *args):
        if operation == "backup" and failure == "backup":
            raise subprocess.CalledProcessError(1, ["synthetic failed backup"])
        return real_tool(tools, operation, *args)

    monkeypatch.setattr(assistant, "run_backup_tool", tool)
    real_run = subprocess.run

    def no_sudo(args, **kwargs):
        assert args[0] not in {"/usr/bin/sudo", "/usr/bin/apt-get"}
        return real_run(args, **kwargs)

    monkeypatch.setattr(assistant.subprocess, "run", no_sudo)
    if failure == "cancel":
        assert assistant.run_assistant(deb) == 0
    else:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            assistant.run_assistant(deb)
    assert not (documents / "NetMon-Sicherungen").exists()


@pytest.mark.parametrize(
    "state,expected",
    [
        ("install ok installed\n1.2", "1.2"),
        ("deinstall ok config-files\n1.2", ""),
        ("unknown ok not-installed\n", ""),
    ],
)
def test_both_status_readers_agree(state, expected, monkeypatch):
    namespace = {"__name__": "root_fixture"}
    exec(assistant.ROOT_INSTALL, namespace)
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=state)
    )
    assert assistant.installed_version() == expected
    assert namespace["installed_version"]() == expected


def test_damaged_package_state_blocks_installer(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(
            returncode=0, stdout="install reinstreq half-installed\n1.2"
        ),
    )
    with pytest.raises(ValueError, match="Paketstatus"):
        assistant.installed_version()


def test_packet_copy_rejects_symlink_and_detects_identity(deb, tmp_path):
    output = tmp_path / "copy.deb"
    assert (
        assistant.copy_package(deb, output)
        == hashlib.sha256(deb.read_bytes()).hexdigest()
    )
    link = tmp_path / "link.deb"
    link.symlink_to(deb)
    with pytest.raises(OSError):
        assistant.copy_package(link, tmp_path / "rejected.deb")
    assert assistant.package_identity(output, "1.0")["Package"] == "netmon"
    with pytest.raises(subprocess.CalledProcessError):
        assistant.package_identity(output, "99.0")


def test_package_tools_ignore_inherited_database_and_temporary_overrides(
    deb, monkeypatch
):
    before = assistant.installed_version()
    monkeypatch.setenv("DPKG_ADMINDIR", "/nonexistent-database")
    monkeypatch.setenv("DPKG_ROOT", "/nonexistent-root")
    monkeypatch.setenv("TMPDIR", "/nonexistent-temp")
    monkeypatch.setenv("APT_CONFIG", "/nonexistent-apt-config")
    assert assistant.installed_version() == before
    assert assistant.package_identity(deb, "1.0")["Version"] == "99.0"
    namespace = {"__name__": "root_fixture"}
    exec(assistant.ROOT_INSTALL, namespace)
    assert namespace["installed_version"]() == before
    assert not set(namespace["SYSTEM_ENV"]) & {
        "DPKG_ADMINDIR",
        "DPKG_ROOT",
        "APT_CONFIG",
    }


@pytest.mark.parametrize("damage", ["traversal", "link", "duplicate", "missing"])
def test_archive_safety_without_extracting_links_or_traversal(
    tmp_path, monkeypatch, damage
):
    payload = io.BytesIO()
    name = "usr/lib/netmon/netmon/__init__.py"
    with tarfile.open(fileobj=payload, mode="w") as archive:
        names = (
            ["../../escape"]
            if damage == "traversal"
            else [name, name] if damage == "duplicate" else [name]
        )
        for item in names:
            info = tarfile.TarInfo(item)
            if damage == "link":
                info.type = tarfile.SYMTYPE
                info.linkname = "/outside"
                archive.addfile(info)
            else:
                info.size = 1
                archive.addfile(info, io.BytesIO(b"#"))
    payload.seek(0)

    class FakePipe:
        stdout = payload

        def wait(self, **kwargs):
            return 0

        def poll(self):
            return 0

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: FakePipe())
    with pytest.raises(ValueError):
        assistant.extract_backup_tools(tmp_path / "fixture.deb", tmp_path / "tools")
    assert not (tmp_path / "escape").exists()
    assert not (tmp_path / "tools/netmon/__init__.py").is_symlink()


@pytest.mark.parametrize(
    "problem",
    [
        "none",
        "hash",
        "changed-version",
        "changed-version-after-copy",
        "firewall",
        "running",
        "apt-failed",
        "wrong-package",
    ],
)
def test_fixed_root_program_rechecks_bytes_and_state_before_fake_apt(
    tmp_path, monkeypatch, problem
):
    namespace = {"__name__": "root_fixture"}
    exec(assistant.ROOT_INSTALL, namespace)
    source = tmp_path / "source.deb"
    source.write_bytes(b"synthetic local package")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(assistant.os, "geteuid", lambda: 0)
    versions = iter(["1.0", "2.0"])
    namespace["installed_version"] = lambda: (
        next(versions)
        if problem == "changed-version-after-copy"
        else "2.0" if problem == "changed-version" else "1.0"
    )

    def guard(kind):
        if kind == problem:
            raise ValueError(kind)

    namespace["check_firewall"] = lambda: guard("firewall")
    namespace["check_closed"] = lambda: guard("running")
    temporary = assistant.tempfile.TemporaryDirectory
    monkeypatch.setattr(
        assistant.tempfile,
        "TemporaryDirectory",
        lambda **kw: temporary(prefix="root-fixture-", dir=tmp_path),
    )
    calls = []

    def fields(args, **kwargs):
        if args[-1] == "--print-architecture":
            return "amd64"
        return {
            "Package": "foreign" if problem == "wrong-package" else "netmon",
            "Version": "99.0",
            "Architecture": "all",
        }[args[-1]]

    monkeypatch.setattr(subprocess, "check_output", fields)
    real_run = subprocess.run

    def fake_apt(args, **kwargs):
        if args[0] == "/usr/bin/dpkg":
            return real_run(args, **kwargs)
        assert args[:4] == [
            "/usr/bin/apt-get",
            "--no-remove",
            "install",
            "--no-install-recommends",
        ]
        assert Path(args[-1]).read_bytes() == source.read_bytes()
        calls.append(args)
        return SimpleNamespace(returncode=42 if problem == "apt-failed" else 0)

    monkeypatch.setattr(subprocess, "run", fake_apt)
    if problem in {"none", "apt-failed"}:
        assert namespace["install"](str(source), digest, "1.0") == (
            42 if problem == "apt-failed" else 0
        )
        assert len(calls) == 1
    else:
        with pytest.raises(ValueError):
            namespace["install"](
                str(source), "0" * 64 if problem == "hash" else digest, "1.0"
            )
        assert not calls
    assert not list(tmp_path.glob("root-fixture-*"))


def test_root_invocation_rejected_before_any_work(monkeypatch):
    monkeypatch.setattr(assistant.os, "geteuid", lambda: 0)
    with pytest.raises(ValueError, match="ohne sudo"):
        assistant.run_assistant(Path("/not-used.deb"))


def test_saved_profile_inspection_never_creates_canonical_data(account):
    _, documents = account
    status = lifecycle.inspect_user_data()
    assert not status["canonical_data_present"]
    assert not status["legacy_data_present"]
    assert not (documents / "NetMon").exists()


@pytest.mark.parametrize(
    "command,blocked",
    [
        ([b"/usr/bin/python3", b"-m", b"netmon"], True),
        ([b"python3", b"-u", b"-m", b"netmon.main"], True),
        ([b"python3", b"/workspace/netmon/app.py"], True),
        ([b"/usr/bin/netmon"], True),
        ([b"grep", b"netmon"], False),
        ([b"python3", b"-c", b"print('netmon')"], False),
    ],
)
def test_user_and_root_process_checks_agree(monkeypatch, command, blocked):
    class Process:
        name = "900001"

        def __truediv__(self, name):
            return SimpleNamespace(read_bytes=lambda: bytes([0]).join(command))

    original = Path.iterdir
    monkeypatch.setattr(
        Path,
        "iterdir",
        lambda self: iter([Process()]) if str(self) == "/proc" else original(self),
    )
    namespace = {"__name__": "root_fixture"}
    exec(assistant.ROOT_INSTALL, namespace)
    for check in [assistant.ensure_closed, namespace["check_closed"]]:
        if blocked:
            with pytest.raises(ValueError):
                check()
        else:
            check()


@pytest.mark.parametrize(
    "damage", [None, "owner", "parent", "symlink", "hardlink", "missing"]
)
def test_root_firewall_helper_must_be_protected(monkeypatch, damage):
    namespace = {"__name__": "root_fixture"}
    exec(assistant.ROOT_INSTALL, namespace)
    helper = "/usr/lib/netmon-manager/netmon/core/ufw_snapshot.py"
    real_lstat = Path.lstat

    def lstat(path):
        name = str(path)
        if not (name == helper or path in Path(helper).parents):
            return real_lstat(path)
        is_file = name == helper
        if damage == "missing" and is_file:
            raise FileNotFoundError()
        mode = (stat.S_IFREG | 0o644) if is_file else (stat.S_IFDIR | 0o755)
        if damage == "symlink" and is_file:
            mode = stat.S_IFLNK | 0o777
        if damage == "parent" and name == "/usr/lib/netmon-manager":
            mode |= 0o020
        return SimpleNamespace(
            st_uid=1000 if damage == "owner" and is_file else 0,
            st_mode=mode,
            st_nlink=2 if damage == "hardlink" and is_file else 1,
        )

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(assistant.os.path, "lexists", lambda _: True)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: calls.append((args, kw)))
    if damage:
        with pytest.raises((OSError, ValueError)):
            namespace["check_firewall"]()
        assert not calls
    else:
        namespace["check_firewall"]()
        assert calls[0][0] == ["/usr/bin/python3", "-I", helper, "removal"]
        assert calls[0][1]["input"] == "{}"
