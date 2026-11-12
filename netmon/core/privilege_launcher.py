"""Protected system executables and clean shells for maintenance launchers."""

import os
import shlex
import stat

from .trusted_sudo import sudo_environment, trusted_sudo_path


def _protected_executable(path, depth=0):
    # Follow Debian's /bin and alternatives links, checking every link and
    # directory, including intermediate links rather than only realpath().
    if depth > 40 or not os.path.isabs(path):
        raise PermissionError("Unsafe system executable path")
    parts = os.path.normpath(path).split(os.sep)
    current = "/"
    for index, part in enumerate(parts):
        if part:
            current = os.path.join(current, part)
        info = os.lstat(current)
        if info.st_uid != 0 or (
            not stat.S_ISLNK(info.st_mode) and info.st_mode & 0o022
        ):
            raise PermissionError("Unsafe system executable ownership or permissions")
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(current)
            if not os.path.isabs(target):
                target = os.path.join(os.path.dirname(current), target)
            return _protected_executable(
                os.path.join(target, *parts[index + 1 :]), depth + 1
            )
        if index < len(parts) - 1:
            if not stat.S_ISDIR(info.st_mode):
                raise PermissionError("Unsafe system executable directory")
        elif not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o111:
            raise PermissionError("Unsafe system executable type or mode")
    return current


def trusted_system_executable(name):
    if not name or os.path.basename(name) != name:
        raise PermissionError("Expected a system executable name")
    return _protected_executable("/usr/bin/" + name)


def terminal_environment():
    env = sudo_environment()
    # Only session coordinates needed to open a graphical terminal. Loader,
    # shell startup and language/plugin search settings are never inherited.
    for key in (
        "HOME",
        "USER",
        "LOGNAME",
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XAUTHORITY",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "XDG_SESSION_TYPE",
        "TERM",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def packet_repair_command(script, *, polkit=False):
    shell = trusted_system_executable("bash")
    clean_shell = [
        trusted_system_executable("env"),
        "-i",
        *(f"{key}={value}" for key, value in sudo_environment().items()),
        shell,
        "--noprofile",
        "--norc",
        "-c",
        script,
    ]
    broker = trusted_system_executable("pkexec") if polkit else trusted_sudo_path()
    return [broker, *clean_shell]


def maintenance_terminal_command(script):
    shell = trusted_system_executable("bash")
    sudo = trusted_sudo_path()
    # Bind sudo even if a supported installation script later activates a venv.
    script = f'sudo() {{ {shlex.quote(sudo)} "$@"; }}; readonly -f sudo;\n{script}'
    command = [
        trusted_system_executable("env"),
        "-i",
        *(f"{key}={value}" for key, value in terminal_environment().items()),
        shell,
        "--noprofile",
        "--norc",
        "-c",
        script,
    ]
    candidates = (
        ("x-terminal-emulator", "-e", False),
        ("gnome-terminal", "--", False),
        ("konsole", "-e", False),
        ("xfce4-terminal", "--command", True),
        ("mate-terminal", "--", False),
        ("lxterminal", "-e", True),
        ("xterm", "-e", False),
    )
    for name, option, as_string in candidates:
        try:
            terminal = trusted_system_executable(name)
        except OSError:
            continue
        return (
            [terminal, option, shlex.join(command)]
            if as_string
            else [terminal, option, *command]
        )
    return None
