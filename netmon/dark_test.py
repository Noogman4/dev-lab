"""NetMon Darkmode Test Launcher (separate from stable main app)."""

from __future__ import annotations

import argparse
import os
import sys
import tkinter as tk

try:
    from netmon.app import (
        App,
        CRASH_LOG_PATH,
        TK_IMPORT_ERROR,
        TkError,
        _append_crash_dump,
        _install_global_crash_hooks,
        run_headless_snapshot,
    )
except ModuleNotFoundError:
    # Allow direct file start: python netmon/dark_test.py
    from app import (  # type: ignore
        App,
        CRASH_LOG_PATH,
        TK_IMPORT_ERROR,
        TkError,
        _append_crash_dump,
        _install_global_crash_hooks,
        run_headless_snapshot,
    )


class DarkTestApp(App):
    def __init__(self, start_theme: str = "dark"):
        super().__init__(start_theme=start_theme)

        try:
            self.title(self.title() + "  [Darkmode Test]")
        except Exception:
            pass

        self.after(
            80,
            lambda: self.log(
                "[TEST] Darkmode-Test-Version aktiv (integrierter Theme-Stack)."
            ),
        )


def main():
    parser = argparse.ArgumentParser(description="NetMon Darkmode Test Launcher")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI and print a compact status snapshot.",
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default="dark",
        help="Start theme for darkmode test app.",
    )
    args = parser.parse_args()

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

    try:
        app = DarkTestApp(start_theme=args.theme)
        app.mainloop()
        return 0
    except TkError as e:
        _append_crash_dump("dark_test.main.tk", type(e), e, e.__traceback__)
        print(
            "Fehler: Tkinter konnte keine GUI-Verbindung aufbauen.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}",
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        _append_crash_dump("dark_test.main.exception", type(e), e, e.__traceback__)
        print(
            "Fehler: NetMon Darkmode-Test ist beim Start abgestürzt.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
