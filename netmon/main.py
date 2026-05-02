"""NetMon startup entrypoint."""

from __future__ import annotations

import argparse
import os
import sys

from netmon.core.crash import (
    CRASH_LOG_PATH,
    _append_crash_dump,
    _install_global_crash_hooks,
)
from netmon.core.lock import (
    acquire_netmon_instance_lock,
    release_netmon_instance_lock,
)


def main(argv=None):
    from netmon.app import App, TK_IMPORT_ERROR, TkError, run_headless_snapshot, tk

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
    args = parser.parse_args(argv)

    if args.headless:
        run_headless_snapshot()
        return 0

    if tk is None:
        print(
            "Fehler: tkinter ist nicht installiert. GUI kann nicht gestartet werden.\n"
            "Lösung (Debian/Ubuntu): sudo apt install -y python3-tk\n"
            "Alternativ: mit --headless starten.\n"
            f"Details: {TK_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 2

    display = os.environ.get("DISPLAY", "").strip()
    if not display:
        print(
            "Fehler: Kein DISPLAY gesetzt. GUI kann nicht gestartet werden.\n"
            "Tipp: Mit --headless starten oder X11/Wayland-Forwarding aktivieren.",
            file=sys.stderr,
        )
        return 2

    _install_global_crash_hooks()

    lock_ok, lock_path = acquire_netmon_instance_lock()
    if not lock_ok:
        print(
            "Fehler: NetMon läuft bereits. Es wird nur eine Instanz gleichzeitig erlaubt.\n"
            f"Lock-Datei: {lock_path}",
            file=sys.stderr,
        )
        return 1

    try:
        app = App(start_theme=args.theme)
        app.mainloop()
        return 0
    except TkError as e:
        _append_crash_dump("main.tk", type(e), e, e.__traceback__)
        print(
            "Fehler: Tkinter konnte keine GUI-Verbindung aufbauen "
            f"(DISPLAY={display!r}).\n"
            "Hinweis: In VS Code Remote/Container fehlt oft X11-Auth.\n"
            "Optionen: 1) --headless nutzen 2) xvfb-run verwenden 3) X11-Forwarding korrekt einrichten.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}",
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        _append_crash_dump("main.exception", type(e), e, e.__traceback__)
        print(
            "Fehler: NetMon ist beim Start abgestürzt.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}",
            file=sys.stderr,
        )
        return 1
    finally:
        release_netmon_instance_lock()


if __name__ == "__main__":
    sys.exit(main())
