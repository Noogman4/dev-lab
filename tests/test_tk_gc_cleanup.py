"""Destroyed Tk cycles must be collected by the test protocol's main thread."""

import gc
import threading
import tkinter as tk
import weakref
from types import SimpleNamespace

import pytest

import conftest


@pytest.mark.parametrize("failure", [False, True])
def test_protocol_releases_destroyed_tk_cycle_on_main_thread(failure):
    finalized = []

    class Root(tk.Tk):
        def __del__(self):
            finalized.append(threading.get_ident())

    enabled = gc.isenabled()
    gc.disable()  # Only this test: prevent incidental collection before the hook.
    original_init = tk.Tk.__init__
    boundary = conftest.pytest_runtest_protocol(None, None)
    next(boundary)
    try:
        root = Root()
        root.withdraw()
        root.test_cycle = root
        reference = weakref.ref(root)
        root.destroy()
        del root
        assert reference() is not None
        error = RuntimeError("synthetic test protocol failure")
        if failure:
            with pytest.raises(RuntimeError) as caught:
                boundary.throw(error)
            assert caught.value is error
        else:
            with pytest.raises(StopIteration):
                boundary.send(True)
        assert reference() is None
        assert tk.Tk.__init__ is original_init
        assert finalized == [threading.main_thread().ident]
        assert not gc.isenabled()  # The hook must not change the caller's state.
        worker = threading.Thread(target=gc.collect)
        worker.start()
        worker.join(2)
        assert not worker.is_alive()
    finally:
        boundary.close()
        gc.collect()
        if enabled:
            gc.enable()


def test_protocol_without_tk_construction_skips_full_collection(monkeypatch):
    calls = []
    original_init = tk.Tk.__init__
    monkeypatch.setattr(
        conftest, "gc", SimpleNamespace(collect=lambda: calls.append(True))
    )
    boundary = conftest.pytest_runtest_protocol(None, None)
    next(boundary)
    with pytest.raises(StopIteration):
        boundary.send(True)
    assert not calls and tk.Tk.__init__ is original_init
