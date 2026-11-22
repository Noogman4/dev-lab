"""A private display's scaling must not leak from one test root to the next."""

import os
import tkinter as tk

import pytest


def test_tcl_only_interpreter_does_not_require_display_scaling():
    interpreter = tk.Tcl()
    assert interpreter.eval("expr {2 + 2}") == "4"


@pytest.mark.skipif(
    os.environ.get("NETMON_TEST_ISOLATED") != "1",
    reason="Requires private isolated display",
)
@pytest.mark.parametrize("reverse", [False, True])
def test_destroy_restores_scaling_even_with_multiple_roots(reverse):
    first = tk.Tk()
    first.withdraw()
    initial = float(first.tk.call("tk", "scaling"))
    first.tk.call("tk", "scaling", 0.90)
    second = tk.Tk()
    second.withdraw()
    roots = [first, second]
    try:
        for root in reversed(roots) if reverse else roots:
            root.destroy()
        probe = tk.Tk()
        probe.withdraw()
        try:
            assert float(probe.tk.call("tk", "scaling")) == pytest.approx(initial)
        finally:
            probe.destroy()
    finally:
        for root in roots:
            try:
                root.destroy()
            except tk.TclError:
                pass
