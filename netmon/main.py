"""NetMon startup entrypoint."""

from __future__ import annotations

import argparse
import os
import sys
import traceback

try:
    from netmon.core.crash import (
        CRASH_LOG_PATH,
        _append_crash_dump,
        _install_global_crash_hooks,
    )
    from netmon.core.lock import (
        acquire_netmon_instance_lock,
        release_netmon_instance_lock,
    )
except ModuleNotFoundError:
    from core.crash import (
        CRASH_LOG_PATH,
        _append_crash_dump,
        _install_global_crash_hooks,
    )
    from core.lock import (
        acquire_netmon_instance_lock,
        release_netmon_instance_lock,
    )


def get_startup_error_log_path():
    base = os.environ.get("XDG_STATE_HOME", "").strip()
    if not base:
        base = os.path.expanduser("~/.local/state")

    state_dir = os.path.join(base, "netmon")
    os.makedirs(state_dir, exist_ok=True)

    return os.path.join(state_dir, "startup_error.log")


def _write_startup_error_log(
    title: str, detail: str = "", exc: BaseException | None = None
):
    log_path = get_startup_error_log_path()
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 80 + "\n")
            fh.write(f"{title}\n\n")
            fh.write(f"argv={sys.argv!r}\n")
            fh.write(f"cwd={os.getcwd()}\n")
            fh.write(f"DISPLAY={os.environ.get('DISPLAY', '')!r}\n\n")
            if detail:
                fh.write(detail.rstrip() + "\n\n")
            if exc is not None:
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=fh)
            fh.write("=" * 80 + "\n")
    except Exception:
        pass
    return log_path


def main(argv=None):
    try:
        from netmon.app import App, TK_IMPORT_ERROR, TkError, run_headless_snapshot, tk
    except ModuleNotFoundError:
        from app import App, TK_IMPORT_ERROR, TkError, run_headless_snapshot, tk

    parser = argparse.ArgumentParser(description="NetMon GUI / headless launcher")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI and print a compact status snapshot.",
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default=None,
        help="Start theme for the integrated NetMon UI.",
    )
    args, unknown_args = parser.parse_known_args(argv)

    print(f"[NetMon] startup_error.log: {get_startup_error_log_path()}")
    if unknown_args:
        print(
            f"[NetMon] Ignoring extra startup args: {unknown_args!r}",
            file=sys.stderr,
        )

    if args.headless:
        run_headless_snapshot()
        return 0

    if tk is None:
        log_path = _write_startup_error_log(
            "NetMon startup failure: tkinter missing",
            detail=f"TK_IMPORT_ERROR={TK_IMPORT_ERROR}",
        )
        print(
            "Fehler: tkinter ist nicht installiert. GUI kann nicht gestartet werden.\n"
            "Lösung (Debian/Ubuntu): sudo apt install -y python3-tk\n"
            "Alternativ: mit --headless starten.\n"
            f"Details: {TK_IMPORT_ERROR}\n"
            f"Start-Log: {log_path}",
            file=sys.stderr,
        )
        return 2

    display = os.environ.get("DISPLAY", "").strip()
    if not display:
        log_path = _write_startup_error_log(
            "NetMon startup failure: no DISPLAY",
            detail="Kein DISPLAY gesetzt.",
        )
        print(
            "Fehler: Kein DISPLAY gesetzt. GUI kann nicht gestartet werden.\n"
            "Tipp: Mit --headless starten oder X11/Wayland-Forwarding aktivieren.\n"
            f"Start-Log: {log_path}",
            file=sys.stderr,
        )
        return 2

    _install_global_crash_hooks()

    lock_ok, lock_path = acquire_netmon_instance_lock()
    if not lock_ok:
        startup_log = _write_startup_error_log(
            "NetMon startup failure: instance lock",
            detail=f"Lock-Datei: {lock_path}",
        )
        print(
            "Fehler: NetMon läuft bereits. Es wird nur eine Instanz gleichzeitig erlaubt.\n"
            f"Lock-Datei: {lock_path}\n"
            f"Start-Log: {startup_log}",
            file=sys.stderr,
        )
        return 1

    try:
        app = App(start_theme=args.theme)
        app.mainloop()
        return 0
    except TkError as e:
        _append_crash_dump("main.tk", type(e), e, e.__traceback__)
        log_path = _write_startup_error_log(
            "NetMon startup failure: TkError",
            detail=f"Crash-Dump: {CRASH_LOG_PATH}",
            exc=e,
        )
        print(
            "Fehler: Tkinter konnte keine GUI-Verbindung aufbauen "
            f"(DISPLAY={display!r}).\n"
            "Hinweis: In VS Code Remote/Container fehlt oft X11-Auth.\n"
            "Optionen: 1) --headless nutzen 2) xvfb-run verwenden 3) X11-Forwarding korrekt einrichten.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}\n"
            f"Start-Log: {log_path}",
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        _append_crash_dump("main.exception", type(e), e, e.__traceback__)
        log_path = _write_startup_error_log(
            "NetMon startup failure: exception",
            detail=f"Crash-Dump: {CRASH_LOG_PATH}",
            exc=e,
        )
        print(
            "Fehler: NetMon ist beim Start abgestürzt.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}\n"
            f"Start-Log: {log_path}",
            file=sys.stderr,
        )
        return 1
    finally:
        release_netmon_instance_lock()


def _report_bootstrap_failure(exc: BaseException):
    log_path = _write_startup_error_log(
        "NetMon startup bootstrap failure",
        exc=exc,
    )

    try:
        import tkinter as _tk
        from tkinter import messagebox as _messagebox

        root = _tk.Tk()
        root.withdraw()
        _messagebox.showerror(
            "NetMon Startfehler",
            "NetMon konnte nicht gestartet werden.\n\n"
            f"Fehler: {exc}\n\n"
            f"Details: {log_path}",
            parent=root,
        )
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        _report_bootstrap_failure(exc)
        raise
