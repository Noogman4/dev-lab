#!/usr/bin/env python3
"""Standalone local DEB assistant; all personal-data work runs without root."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import pwd
import stat
import subprocess
import sys
import tarfile
import tempfile

MAX_PACKAGE = 4 * 1024**3
TOOL_ENV = {
    "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TMPDIR": "/tmp",
}
MODULES = {
    "netmon/__init__.py",
    "netmon/config/__init__.py",
    "netmon/config/constants.py",
    "netmon/core/__init__.py",
    "netmon/core/import_limits.py",
    "netmon/core/private_logs.py",
    "netmon/core/private_state.py",
    "netmon/core/log_redaction.py",
    "netmon/core/state.py",
    "netmon/core/utils.py",
    "netmon/core/user_files.py",
    "netmon/core/user_backup.py",
    "netmon/core/lifecycle.py",
}

# Only this fixed, standard-library program runs under sudo. It never imports
# Python from the selected package. APT alone runs package maintainer scripts.
ROOT_INSTALL = r"""
import hashlib, os, stat, subprocess, sys, tempfile
from pathlib import Path
SYSTEM_ENV = {"PATH":"/usr/sbin:/usr/bin:/sbin:/bin", "LANG":"C.UTF-8", "LC_ALL":"C.UTF-8", "HOME":"/root", "TMPDIR":"/var/tmp"}

def installed_version():
    result = subprocess.run(['/usr/bin/dpkg-query', '-W', '-f=${Status}\n${Version}', 'netmon'], capture_output=True, text=True, env=SYSTEM_ENV)
    if result.returncode:
        return ''
    state, _, version = result.stdout.partition(chr(10))
    if state == 'install ok installed':
        return version
    if state in {'deinstall ok config-files', 'unknown ok not-installed'}:
        return ''
    raise ValueError('NetMon package state needs administrator review: ' + state)

def check_firewall():
    if not os.path.lexists('/var/lib/netmon/ufw-snapshot'):
        return
    helper = Path('/usr/lib/netmon-manager/netmon/core/ufw_snapshot.py')
    for path in [helper, *helper.parents]:
        info = path.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Unprotected firewall helper')
        if path == helper:
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError('Unsafe firewall helper')
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError('Unsafe firewall helper parent')
    subprocess.run(['/usr/bin/python3', '-I', str(helper), 'removal'], input='{}', text=True, check=True, env=SYSTEM_ENV)

def check_closed():
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            args = (process / 'cmdline').read_bytes().split(bytes([0]))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        name = Path(os.fsdecode(args[0])).name
        modules = {b'netmon', b'netmon.main', b'netmon.netmon_radio_app'}
        scripts = (b'/netmon/app.py', b'/netmon/main.py', b'/netmon_radio_app.py')
        python_app = name.startswith('python') and (
            any(a.endswith(scripts) for a in args[1:]) or
            any(a == b'-m' and i + 1 < len(args) and args[i + 1] in modules for i, a in enumerate(args)))
        if name in {'netmon', 'netmon-radio'} or python_app:
            raise ValueError('Close NetMon and Radio first (PID ' + process.name + ')')

def install(source, expected_hash, expected_version):
    if os.geteuid() != 0:
        raise ValueError('Root rights required only for package installation')
    if installed_version() != expected_version:
        raise ValueError('Installed version changed; start the assistant again')
    check_closed()
    check_firewall()
    with tempfile.TemporaryDirectory(prefix='netmon-install-', dir='/var/tmp') as folder:
        package = str(Path(folder) / 'netmon.deb')
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(source, flags), 'rb') as incoming, open(package, 'xb') as outgoing:
            before = os.fstat(incoming.fileno())
            if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 4 * 1024**3:
                raise ValueError('Invalid package file')
            digest = hashlib.sha256()
            remaining = before.st_size
            while remaining:
                block = incoming.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError('Package became shorter')
                outgoing.write(block); digest.update(block); remaining -= len(block)
            if incoming.read(1) or digest.hexdigest() != expected_hash:
                raise ValueError('Package changed after review')
            after = os.fstat(incoming.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError('Package changed while copying')
            outgoing.flush(); os.fsync(outgoing.fileno())
        name = subprocess.check_output(['/usr/bin/dpkg-deb', '-f', package, 'Package'], text=True, env=SYSTEM_ENV).strip()
        version = subprocess.check_output(['/usr/bin/dpkg-deb', '-f', package, 'Version'], text=True, env=SYSTEM_ENV).strip()
        architecture = subprocess.check_output(['/usr/bin/dpkg-deb', '-f', package, 'Architecture'], text=True, env=SYSTEM_ENV).strip()
        native = subprocess.check_output(['/usr/bin/dpkg', '--print-architecture'], text=True, env=SYSTEM_ENV).strip()
        if name != 'netmon' or architecture not in {'all', native}:
            raise ValueError('Wrong package identity or architecture')
        if expected_version:
            subprocess.run(['/usr/bin/dpkg', '--compare-versions', version, 'gt', expected_version], check=True, env=SYSTEM_ENV)
        if installed_version() != expected_version:
            raise ValueError('Installed version changed while preparing the package')
        return subprocess.run(['/usr/bin/apt-get', '--no-remove', 'install', '--no-install-recommends', package], env=SYSTEM_ENV).returncode

if __name__ == '__main__':
    try:
        sys.exit(install(*sys.argv[1:]))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print('Installation stopped: ' + str(exc), file=sys.stderr)
        sys.exit(1)
"""


def installed_version():
    """Read package status without executing NetMon code."""
    result = subprocess.run(
        ["/usr/bin/dpkg-query", "-W", "-f=${Status}\n${Version}", "netmon"],
        capture_output=True,
        text=True,
        check=False,
        env=TOOL_ENV,
    )
    if result.returncode:
        return ""
    state, _, version = result.stdout.partition(chr(10))
    if state == "install ok installed":
        return version
    if state in {"deinstall ok config-files", "unknown ok not-installed"}:
        return ""
    raise ValueError("NetMon-Paketstatus muss zuerst mit APT geklaert werden: " + state)


def ensure_closed():
    """Recognize exact application arguments, never command text embedded in -c."""
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            args = (process / "cmdline").read_bytes().split(b"\0")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        name = Path(os.fsdecode(args[0])).name
        modules = {b"netmon", b"netmon.main", b"netmon.netmon_radio_app"}
        scripts = (b"/netmon/app.py", b"/netmon/main.py", b"/netmon_radio_app.py")
        python_app = name.startswith("python") and (
            any(a.endswith(scripts) for a in args[1:])
            or any(
                a == b"-m" and i + 1 < len(args) and args[i + 1] in modules
                for i, a in enumerate(args)
            )
        )
        if name in {"netmon", "netmon-radio"} or python_app:
            raise ValueError(
                "NetMon und Radio zuerst schliessen (PID " + process.name + ")."
            )


def copy_package(source, destination):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with (
        os.fdopen(os.open(source, flags), "rb") as incoming,
        destination.open("xb") as outgoing,
    ):
        before = os.fstat(incoming.fileno())
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_PACKAGE:
            raise ValueError("Keine regulaere Paketdatei innerhalb des Groessenlimits.")
        remaining = before.st_size
        digest = hashlib.sha256()
        while remaining:
            chunk = incoming.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("Paket wurde waehrend des Lesens verkuerzt.")
            outgoing.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
        if incoming.read(1):
            raise ValueError("Paket wurde waehrend des Lesens vergroessert.")
        after = os.fstat(incoming.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("Paket wurde waehrend des Lesens veraendert.")
    return digest.hexdigest()


def package_identity(package, current):
    fields = {
        name: subprocess.check_output(
            ["/usr/bin/dpkg-deb", "-f", str(package), name], text=True, env=TOOL_ENV
        ).strip()
        for name in ["Package", "Version", "Architecture"]
    }
    native = subprocess.check_output(
        ["/usr/bin/dpkg", "--print-architecture"], text=True, env=TOOL_ENV
    ).strip()
    if fields["Package"] != "netmon" or fields["Architecture"] not in {"all", native}:
        raise ValueError("Kein passendes netmon-Paket fuer dieses System.")
    if subprocess.run(
        [
            "/usr/bin/dpkg",
            "--compare-versions",
            fields["Version"],
            "ge",
            "1.1.22~beta3",
        ],
        env=TOOL_ENV,
        check=False,
    ).returncode:
        raise ValueError(
            "Die eigenstaendige Verwaltung benoetigt NetMon ab 1.1.22~beta3. "
            "Aeltere Pakete enthalten noch die gemeinsame Verwaltung."
        )
    if current:
        subprocess.run(
            ["/usr/bin/dpkg", "--compare-versions", fields["Version"], "gt", current],
            check=True,
            env=TOOL_ENV,
        )
    return fields


def extract_backup_tools(package, target):
    """Extract only bounded regular backup modules; never unpack archive links."""
    seen = set()
    with tempfile.TemporaryFile() as errors:
        pipe = subprocess.Popen(
            ["/usr/bin/dpkg-deb", "--fsys-tarfile", str(package)],
            stdout=subprocess.PIPE,
            stderr=errors,
            env=TOOL_ENV,
        )
        try:
            total = count = 0
            with tarfile.open(fileobj=pipe.stdout, mode="r|") as archive:
                for member in archive:
                    count += 1
                    total += member.size
                    path = PurePosixPath(member.name)
                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or member.size < 0
                        or count > 100_000
                        or total > 2 * 1024**3
                    ):
                        raise ValueError("Unsicheres oder zu grosses Paketarchiv.")
                    name = str(path)
                    if not name.startswith("usr/lib/netmon/"):
                        continue
                    relative = name.removeprefix("usr/lib/netmon/")
                    if relative not in MODULES:
                        continue
                    if (
                        relative in seen
                        or not member.isfile()
                        or member.size > 2 * 1024**2
                    ):
                        raise ValueError("Ungueltiges Backup-Modul im Paket.")
                    seen.add(relative)
                    output = target / relative
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with output.open("xb") as stream:
                        stream.write(archive.extractfile(member).read())
            if pipe.wait(timeout=30):
                raise ValueError("Paketarchiv konnte nicht gelesen werden.")
        finally:
            pipe.stdout.close()
            if pipe.poll() is None:
                pipe.kill()
                pipe.wait()
    if seen != MODULES:
        raise ValueError(
            "Das neue Paket enthaelt nicht die benoetigte versionierte Backup-Funktion."
        )


def run_backup_tool(tools, operation, *args):
    account = pwd.getpwuid(os.getuid())
    home = Path(account.pw_dir)
    if not home.is_absolute() or home == Path("/") or home.resolve() != home:
        raise ValueError("Benutzer-Home konnte nicht sicher bestimmt werden.")
    env = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": str(home),
        "USER": account.pw_name,
        "LOGNAME": account.pw_name,
        "LANG": "C.UTF-8",
        "TMPDIR": "/tmp",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    code = "import sys; sys.path.insert(0, sys.argv.pop(1)); from netmon.core.lifecycle import main; sys.exit(main())"
    result = subprocess.run(
        ["/usr/bin/python3", "-I", "-c", code, str(tools), operation, *args],
        env=env,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def confirm(message):
    try:
        return input(message + " [y/N] ").strip().lower() in {"y", "yes", "j", "ja"}
    except EOFError:
        return False


def run_assistant(package, backup_parent=None):
    if os.geteuid() == 0:
        raise ValueError(
            "Diesen Assistenten ohne sudo starten. Root wird erst fuer APT angefordert."
        )
    ensure_closed()
    current = installed_version()
    print(
        "Vorbereitung, Sicherung und Installation koennen je nach Datenmenge und Datentraeger mehrere Minuten dauern. "
        "Bitte das Terminal bis zum Abschluss geoeffnet lassen. Einzelne Arbeitsschritte koennen laenger ohne neue Fortschrittsmeldung dauern.",
        flush=True,
    )
    with tempfile.TemporaryDirectory(
        prefix="netmon-install-review-", dir="/tmp"
    ) as folder:
        private = Path(folder)
        snapshot = private / "netmon.deb"
        digest = copy_package(package, snapshot)
        fields = package_identity(snapshot, current)
        print(
            "NetMon: " + (current or "nicht installiert") + " -> " + fields["Version"],
            flush=True,
        )
        print("Paket-SHA256: " + digest, flush=True)
        print(
            "Nur Pakete aus vertrauenswuerdiger Quelle verwenden. Keine Herausgebersignaturpruefung.",
            flush=True,
        )
        print(
            "Backup-Werkzeuge werden aus diesem Paket mit Benutzerrechten geladen.",
            flush=True,
        )
        if not confirm(
            "Benutzerdaten pruefen, falls vorhanden sichern und danach Installation vorbereiten?"
        ):
            print("Abgebrochen.")
            return 0
        tools = private / "tools"
        extract_backup_tools(snapshot, tools)
        status = run_backup_tool(tools, "inspect")
        if status["canonical_data_present"]:
            parent = (
                Path(backup_parent)
                if backup_parent
                else Path(status["documents"]) / "NetMon-Sicherungen"
            )
            receipt = run_backup_tool(tools, "backup", "--parent", str(parent))
            print(
                "Vollbackup erfolgreich geprueft: "
                + json.dumps(receipt, ensure_ascii=False),
                flush=True,
            )
        elif status["legacy_data_present"]:
            raise ValueError(
                "Nur alte/verteilte Benutzerablagen gefunden. Datenuebernahme zuerst klaeren; keine Installation gestartet."
            )
        else:
            print(
                "Keine bekannten NetMon-Benutzerdaten vorhanden; kein Backup erforderlich.",
                flush=True,
            )
        ensure_closed()
        # The elevated fixed program rechecks version, identity and the exact
        # reviewed bytes before asking APT to install its root-owned snapshot.
        return subprocess.run(
            [
                "/usr/bin/sudo",
                "--",
                "/usr/bin/python3",
                "-I",
                "-c",
                ROOT_INSTALL,
                str(snapshot),
                digest,
                current,
            ]
        ).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package", nargs="?", help="Pfad zur neuen vertrauenswuerdigen NetMon-.deb"
    )
    parser.add_argument(
        "--backup-parent", help="Absoluter Sicherungsordner, ausserhalb von NetMon"
    )
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 oder neuer wird benoetigt.")
    try:
        package = args.package or input("Pfad zur NetMon-.deb: ").strip()
        if not package or any(ord(c) < 32 for c in package):
            raise ValueError("Ungueltiger Paketpfad.")
        return run_assistant(
            Path(os.path.abspath(os.path.expanduser(package))), args.backup_parent
        )
    except EOFError:
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print("Vorgang abgebrochen: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
