"""Trusted sudo and nmcli boundary for the supported Debian installation layout."""

import os
import stat

SUDO_PATH = "/usr/bin/sudo"
NMCLI_PATH = "/usr/bin/nmcli"


def _trusted_system_executable(executable: str) -> str:
    """Reject links, writable ancestors and non-root-owned executables."""
    for path in ("/", "/usr", "/usr/bin", executable):
        info = os.lstat(path)
        expected_type = stat.S_ISREG if path == executable else stat.S_ISDIR
        if (
            info.st_uid != 0
            or info.st_mode & 0o022
            or not expected_type(info.st_mode)
            or (path == executable and not info.st_mode & 0o111)
        ):
            raise PermissionError(f"Unsafe system {os.path.basename(executable)} path")
    return executable


def trusted_sudo_path() -> str:
    return _trusted_system_executable(SUDO_PATH)


def trusted_nmcli_path() -> str:
    return _trusted_system_executable(NMCLI_PATH)


def sudo_environment() -> dict[str, str]:
    """Do not pass user-controlled loader, plugin or search-path settings."""
    return {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"}


def trusted_command_args(args):
    tokens = list(args)
    command_index = 0
    if tokens and os.path.basename(os.fsdecode(tokens[0])) == "sudo":
        tokens[0] = trusted_sudo_path()
        command_index = 1
        # These supported sudo flags take no value. Do not interpret arguments
        # to other sudo options (e.g. a username) as an executable name.
        while command_index < len(tokens) and os.fsdecode(tokens[command_index]) in {
            "-n",
            "-S",
            "-H",
            "--non-interactive",
            "--stdin",
            "--set-home",
        }:
            command_index += 1
        if command_index < len(tokens) and tokens[command_index] == "--":
            command_index += 1
    if (
        command_index < len(tokens)
        and os.path.basename(os.fsdecode(tokens[command_index])) == "nmcli"
    ):
        tokens[command_index] = trusted_nmcli_path()
    return tokens
