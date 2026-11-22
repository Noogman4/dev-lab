"""Preview or switch one closed Secure Browser to the Bubblewrap starter."""

import argparse
from configparser import ConfigParser, Error as ConfigError
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys

from tools.secure_browser_manager import browser_container_builder as builder

from . import container_launcher, sandbox, session
from .sandbox import BrowserSandboxError


@contextmanager
def _closed_profile(path):
    with builder.maintenance_directory(path) as directory:
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise BrowserSandboxError("Der Firefox-Profilordner ist nicht geschützt.")
        fd = os.open(
            ".parentlock", os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.getuid()
            ):
                raise BrowserSandboxError("Die Firefox-Profilsperre ist ungültig.")
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise BrowserSandboxError(
                    "Das Firefox-Profil ist noch geöffnet."
                ) from exc
            yield
        finally:
            os.close(fd)


def _check_version(profile, runtime):
    active = ConfigParser(interpolation=None)
    target = ConfigParser(interpolation=None)
    active.read_string(
        builder.maintenance_read(profile / "compatibility.ini", limit=8192).decode()
    )
    target.read(runtime / "application.ini", encoding="utf-8")
    last_version, _, last_build = active["Compatibility"]["LastVersion"].partition("_")
    app = target["App"]
    last_build = last_build.partition("/")[0]
    if not (last_build.isdecimal() and app["BuildID"].isdecimal()):
        raise BrowserSandboxError(
            "Die Firefox-Buildnummer konnte nicht geprüft werden."
        )
    current = (
        tuple(map(int, last_version.removesuffix("esr").split("."))),
        int(last_build),
    )
    candidate = (
        tuple(map(int, app["Version"].removesuffix("esr").split("."))),
        int(app["BuildID"]),
    )
    if candidate < current:
        raise BrowserSandboxError(
            "Die verwaltete Firefox-Basis ist älter als das Profil."
        )


def migrate_container(container, *, apply=False):
    if (
        os.getuid() == 0
        or not container.is_absolute()
        or not builder.CONTAINER_NAME_PATTERN.fullmatch(container.name)
    ):
        raise BrowserSandboxError(
            "Bitte einen absoluten Secure-Browser-Ordner als Benutzer angeben."
        )
    runtime = session._managed_runtime(session.FIREFOX_DIR)
    session._check_display_requirements()
    sandbox._require_network_tools()
    profile = container / "profile"
    with (
        builder.maintenance_directory(container) as directory,
        _closed_profile(profile),
    ):
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise BrowserSandboxError("Der Secure-Browser-Ordner ist nicht geschützt.")
        starter, before = builder._maintenance_read_at(
            directory, "start.sh", limit=builder.MAX_SCAN_FILE_SIZE
        )
        text = starter.decode()
        lines = [line.strip() for line in text.splitlines()]
        if builder.SANDBOX_START_COMMAND in lines:
            print(f"{container.name}: Der Sandbox-Starter ist bereits aktiv.")
            return
        local_profile = '--profile "$SCRIPT_DIR/profile"'
        if f"PROFILE_PATH={shlex.quote(os.fspath(profile))}" in lines:
            local_profile = '--profile "$PROFILE_PATH"'
        if not any(
            line.startswith('exec "$SCRIPT_DIR/firefox/firefox" ')
            and local_profile in line
            for line in lines
        ):
            raise BrowserSandboxError(
                "Erwartet wird ein NetMon-Starter mit internem Firefox-Profil."
            )
        _check_version(profile, runtime)
        policy = container / "policies.json"
        installed = container / "firefox/distribution/policies.json"
        if container_launcher._read_policies(
            policy
        ) != container_launcher._read_policies(installed):
            raise BrowserSandboxError(
                "Aktive Firefox-Richtlinien und Container-Richtlinien weichen ab."
            )
        print(
            f"{container.name}: Profil und Firefox-Basis geprüft. Ziel ist der Bubblewrap-Starter.",
            flush=True,
        )
        if not apply:
            return
        spec = builder.ContainerSpec(container.name, container, [], None)
        subprocess.run(
            ["/bin/bash"],
            input=builder.build_backup_script(spec, source_directory=container),
            text=True,
            env=sandbox._HOST_ENV,
            check=True,
        )
        after = builder._maintenance_stat(directory, "start.sh")
        if after is None or builder._maintenance_identity(
            after
        ) != builder._maintenance_identity(before):
            raise BrowserSandboxError(
                "Der Secure-Browser-Starter wurde während der Sicherung geändert."
            )
        builder._maintenance_write_at(
            directory,
            "start.sh",
            builder.build_sandbox_start_script().encode(),
            executable=True,
        )
        print(f"{container.name}: Bubblewrap-Starter aktiviert.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("container", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Back up the profile and replace the starter.",
    )
    args = parser.parse_args()
    try:
        migrate_container(args.container, apply=args.apply)
    except (
        BrowserSandboxError,
        ConfigError,
        KeyError,
        OSError,
        subprocess.CalledProcessError,
        ValueError,
    ) as exc:
        print(f"Secure Browser: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
