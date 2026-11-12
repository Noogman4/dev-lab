"""Open Tk's X display without an external XIM server.

Every Tk widget gets an X input context. With ``XMODIFIERS=@im=ibus`` each one
is a synchronous round trip to ``ibus-x11``; once that server has accumulated
contexts it answers slowly and NetMon's window took up to two minutes to map
(2026-11-12: 140 s with ibus, 8 s with ``@im=none``). ``@im=none`` keeps Xlib's
local input method, so dead keys and Compose still work.

Xlib reads ``XMODIFIERS`` only while Tk opens the display, so the variable is
set just for that moment and restored afterwards; child processes keep the
user's input method. ``NETMON_KEEP_XIM=1`` restores the old behaviour.
"""

from contextlib import contextmanager
import os

_UNSET = object()


@contextmanager
def x_input_method_bypass():
    if os.environ.get("NETMON_KEEP_XIM") == "1":
        yield
        return
    previous = os.environ.get("XMODIFIERS", _UNSET)
    os.environ["XMODIFIERS"] = "@im=none"
    try:
        yield
    finally:
        if previous is _UNSET:
            os.environ.pop("XMODIFIERS", None)
        else:
            os.environ["XMODIFIERS"] = previous
