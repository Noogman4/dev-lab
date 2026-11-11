"""Fullscreen scaling runs off the Tk main thread; the main thread only pastes."""

import os
import threading
import time
import tkinter as tk
from types import SimpleNamespace

import pytest
from PIL import Image

from netmon.core import projectm_pixels as pixels
from netmon.ui import projectm_pixel_window as ui


def wait(predicate, root, timeout=3):
    end = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < end
        root.update()
        time.sleep(0.002)


@pytest.fixture
def window():
    root = tk.Tk()
    root.withdraw()
    request = SimpleNamespace(
        frames=pixels.FrameMailbox(),
        cancelled=threading.Event(),
        done=threading.Event(),
    )
    request.stop = request.cancelled.set
    root.radio_projectm_proc = request
    view = ui.ensure(root, request)
    root.update()
    yield root, view, request
    view.close()
    root.destroy()


def test_frames_are_resized_in_worker_and_pasted_in_main_thread(window, monkeypatch):
    root, view, request = window
    resized, original = [], Image.Image.resize

    def recording(self, *args, **kwargs):
        resized.append(threading.get_ident())
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Image.Image, "resize", recording)
    view.window.geometry("1000x600")
    root.update()
    for shown in range(3):
        request.frames.put(os.urandom(pixels.FRAME_BYTES))
        wait(lambda: view.displayed > shown, root)
    assert len(resized) == 3 and set(resized) == {view.scaler.thread.ident}
    assert (view.photo.width(), view.photo.height()) == (800, 600)
    first = view.photo
    request.frames.put(os.urandom(pixels.FRAME_BYTES))
    shown = view.displayed
    wait(lambda: view.displayed > shown, root)
    assert view.photo is first  # reused, not recreated per frame


def test_native_size_frames_skip_resize(window, monkeypatch):
    root, view, request = window
    monkeypatch.setattr(
        Image.Image, "resize", lambda *_, **__: pytest.fail("resize at native size")
    )
    request.frames.put(b"\x10\x20\x30\xff" * (pixels.WIDTH * pixels.HEIGHT))
    wait(lambda: view.displayed == 1, root)
    assert (view.photo.width(), view.photo.height()) == (640, 480)
    assert view.photo.tk.call(str(view.photo), "get", 0, 0) == (16, 32, 48)


def test_stale_scaled_result_for_old_size_is_discarded(window):
    root, view, request = window
    view.window.geometry("1000x600")
    root.update()
    request.frames.put(os.urandom(pixels.FRAME_BYTES))
    wait(lambda: view.displayed == 1, root)
    assert view.photo.width() == 800
    # Shrink while a job for the old size is still in flight.
    request.frames.put(os.urandom(pixels.FRAME_BYTES))
    view.window.geometry("640x480")
    root.update()
    assert (view.photo.width(), view.photo.height()) == (640, 480)
    end = time.monotonic() + 0.5
    while time.monotonic() < end:
        root.update()
        assert (view.photo.width(), view.photo.height()) == (640, 480)
        time.sleep(0.01)


def test_close_is_fast_and_ends_worker_even_while_busy(window):
    root, view, request = window
    view.window.geometry("1000x600")
    root.update()
    # Fill the worker with work; stop must not wait for it.
    for _ in range(5):
        view.scaler.submit(Image.new("RGB", (pixels.WIDTH, pixels.HEIGHT)), (1280, 960))
    start = time.monotonic()
    view.close()
    assert time.monotonic() - start < 0.1 and request.cancelled.is_set()
    view.scaler.thread.join(2)
    assert not view.scaler.thread.is_alive()


def test_worker_failure_closes_window_and_stops_request(window, monkeypatch):
    root, view, request = window
    view.window.geometry("1000x600")
    root.update()
    monkeypatch.setattr(
        Image.Image, "resize", lambda *_, **__: (_ for _ in ()).throw(MemoryError())
    )
    request.frames.put(os.urandom(pixels.FRAME_BYTES))
    wait(lambda: view.closed, root)
    assert request.cancelled.is_set() and "MemoryError" in view.scaler.error
