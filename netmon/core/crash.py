"""Crash logging helpers for NetMon startup and runtime hooks."""

from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime

from netmon.config.constants import NETMON_APP_VERSION

CRASH_LOG_PATH = "/tmp/netmon_crash.log"


def _append_crash_dump(origin, exc_type, exc_value, exc_tb):
    try:
        with open(CRASH_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"{datetime.now().isoformat()} | origin={origin}\n")
            f.write(f"netmon_version={NETMON_APP_VERSION}\n")
            f.write(f"python={sys.version}\n")
            f.write(f"argv={sys.argv!r}\n")
            f.write(f"cwd={os.getcwd()}\n\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
            f.write("=" * 80 + "\n")
    except Exception:
        pass


def _install_global_crash_hooks():
    def _sys_hook(exc_type, exc_value, exc_tb):
        _append_crash_dump("sys.excepthook", exc_type, exc_value, exc_tb)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _sys_hook

    if hasattr(threading, "excepthook"):
        _threading_default = threading.excepthook

        def _thread_hook(args):
            _append_crash_dump(
                "threading.excepthook",
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
            )
            _threading_default(args)

        threading.excepthook = _thread_hook
