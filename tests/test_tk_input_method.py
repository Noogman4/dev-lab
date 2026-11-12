"""XIM bypass only while Tk opens the display; the user's setting survives."""

import os
import subprocess
import sys

from netmon.core.tk_input_method import x_input_method_bypass


def test_bypass_sets_local_im_and_restores_previous(monkeypatch):
    monkeypatch.setenv("XMODIFIERS", "@im=ibus")
    monkeypatch.delenv("NETMON_KEEP_XIM", raising=False)
    with x_input_method_bypass():
        assert os.environ["XMODIFIERS"] == "@im=none"
        # C-level getenv (as Xlib uses it) sees the bypass as well.
        child = subprocess.run(
            [sys.executable, "-I", "-c", "import os;print(os.environ['XMODIFIERS'])"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert child.stdout.strip() == "@im=none"
    assert os.environ["XMODIFIERS"] == "@im=ibus"


def test_bypass_removes_variable_that_was_unset(monkeypatch):
    monkeypatch.delenv("XMODIFIERS", raising=False)
    monkeypatch.delenv("NETMON_KEEP_XIM", raising=False)
    with x_input_method_bypass():
        assert os.environ["XMODIFIERS"] == "@im=none"
    assert "XMODIFIERS" not in os.environ


def test_bypass_restores_even_on_error(monkeypatch):
    monkeypatch.setenv("XMODIFIERS", "@im=fcitx")
    monkeypatch.delenv("NETMON_KEEP_XIM", raising=False)
    try:
        with x_input_method_bypass():
            raise RuntimeError("Tk failed")
    except RuntimeError:
        pass
    assert os.environ["XMODIFIERS"] == "@im=fcitx"


def test_opt_out_keeps_external_input_method(monkeypatch):
    monkeypatch.setenv("XMODIFIERS", "@im=ibus")
    monkeypatch.setenv("NETMON_KEEP_XIM", "1")
    with x_input_method_bypass():
        assert os.environ["XMODIFIERS"] == "@im=ibus"
