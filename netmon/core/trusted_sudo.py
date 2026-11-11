"""Trusted sudo boundary for the supported Debian installation layout."""

import os
import stat

SUDO_PATH = "/usr/bin/sudo"


def trusted_sudo_path() -> str:
    """Reject links, writable ancestors and non-root-owned executables."""
    for path in ("/", "/usr", "/usr/bin", SUDO_PATH):
        info = os.lstat(path)
        expected_type = stat.S_ISREG if path == SUDO_PATH else stat.S_ISDIR
        if (
            info.st_uid != 0
            or info.st_mode & 0o022
            or not expected_type(info.st_mode)
            or (path == SUDO_PATH and not info.st_mode & 0o111)
        ):
            raise PermissionError("Unsafe system sudo path")
    return SUDO_PATH


def sudo_environment() -> dict[str, str]:
    """Do not pass user-controlled loader, plugin or search-path settings."""
    return {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"}


def trusted_command_args(args):
    tokens = list(args)
    if tokens and os.path.basename(os.fsdecode(tokens[0])) == "sudo":
        tokens[0] = trusted_sudo_path()
    return tokens
