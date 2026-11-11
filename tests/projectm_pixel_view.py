"""Experimental trusted Tk raw-pixel sink. No production UI integration.

Only the worker owns its Popen and blocking I/O. Tk polls one bounded latest
frame slot; no worker calls Tk. A replacement waits for its predecessor in the
worker, never in a callback. Every launch uses a fixed private probe command.
"""

from dataclasses import dataclass, field
import os
import selectors
import subprocess
import threading
import time

from projectm_pixel_benchmark import TimedDecoder
from projectm_pixel_protocol import CHUNK, FRAME_BYTES, HEIGHT, WIDTH


class LatestFrame:
    def __init__(self):
        self.lock = threading.Lock()
        self.pending = None
        self.received = self.dropped = 0

    def put(self, data):
        if type(data) is not bytes or len(data) != FRAME_BYTES:
            raise ValueError("Expected fixed RGBA frame")
        with self.lock:
            self.dropped += self.pending is not None
            self.pending = data
            self.received += 1

    def take(self):
        with self.lock:
            frame, self.pending = self.pending, None
            return frame


@dataclass
class Request:
    generation: int
    previous: object = None
    cancel: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    frames: LatestFrame = field(default_factory=LatestFrame)
    state: str = "starting"
    error: str = ""
    forced_kill: bool = False
    process: object = None
    thread: object = None
    displayed: int = 0
    display_times: list = field(default_factory=list)
    peak_buffer: int = 0


def _request_cancel(process):
    if process.stdin is not None and not process.stdin.closed:
        try:
            process.stdin.write(b"c")
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        try:
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass


def own(request, command, env):
    """Worker-only process/stream ownership, including cancellation and reap."""
    process = None
    try:
        if request.previous is not None:
            # Do not skip a predecessor even when this intermediate start dies.
            request.previous.done.wait()
            request.previous = None
        if request.cancel.is_set():
            return
        process = request.process = subprocess.Popen(
            command,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            bufsize=0,
        )
        decoder = TimedDecoder(30)
        deadline = time.monotonic() + 65
        cancel_deadline = None
        with selectors.DefaultSelector() as selected:
            selected.register(process.stdout, selectors.EVENT_READ)
            while True:
                now = time.monotonic()
                if request.cancel.is_set() and cancel_deadline is None:
                    _request_cancel(process)
                    cancel_deadline = now + 15
                if now >= (cancel_deadline or deadline):
                    raise TimeoutError("Private pixel producer deadline")
                if not selected.select(0.05):
                    continue
                data = os.read(process.stdout.fileno(), CHUNK)
                if not data:
                    if not request.cancel.is_set():
                        decoder.finish()
                    break
                for _stamp, frame in decoder.feed(data):
                    if not request.cancel.is_set():
                        request.frames.put(frame)
                        request.state = "streaming"
                request.peak_buffer = decoder.peak
        if process.wait(timeout=4) != 0 and not request.cancel.is_set():
            raise RuntimeError("Private pixel producer failed")
        request.state = "ended"
    except Exception as exc:
        request.error = f"{type(exc).__name__}: {exc}"[:512]
        request.state = "error"
    finally:
        try:
            if process is not None:
                _request_cancel(process)
                if process.poll() is None:
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        request.forced_kill = True
                        process.kill()  # Only this Popen; never a PID/name search.
                        process.wait(timeout=3)
                process.stdout.close()
        except Exception as exc:
            request.error = f"Cleanup {type(exc).__name__}: {exc}"[:512]
            request.state = "error"
        finally:
            if request.cancel.is_set():
                request.frames.take()
                request.state = "cancelled"
            request.done.set()


class PixelView:
    def __init__(self, root, label, status, launch):
        self.root, self.label, self.status, self.launch = root, label, status, launch
        self.generation = 0
        self.request = None
        self.closed = False
        self.photo = None
        self.latest_rgb = None
        self.timer = root.after(16, self.tick)

    def start(self):
        if self.closed:
            return None
        previous = self.request
        self.stop()
        request = Request(self.generation, previous=previous)
        self.request = request
        try:
            command, env = self.launch(request.generation)
            request.thread = threading.Thread(
                target=own,
                args=(request, command, env),
                name="pixel-owner",
            )
            request.thread.start()
        except Exception:
            request.state = "error"
            request.done.set()
            # A failed launch never replaces the cleanup predecessor. Otherwise
            # a later start could skip an older owner through this done request.
            self.request = previous
            self.status.set("error")
            raise
        self.status.set("starting")
        return request

    def stop(self):
        self.generation += 1
        if self.request is not None:
            self.request.cancel.set()
            self.request.frames.take()
        if not self.closed:
            self.status.set(
                "stopped"
                if self.request is None or self.request.done.is_set()
                else "stopping"
            )

    def tick(self):
        self.timer = None
        if self.closed:
            return
        request = self.request
        if request is not None and request.generation == self.generation:
            frame = request.frames.take()
            if frame is not None:
                # Fixed raw bytes only: no image-file/container decoder.
                from PIL import Image, ImageTk

                image = Image.frombytes("RGBA", (WIDTH, HEIGHT), frame)
                self.photo = ImageTk.PhotoImage(image, master=self.root)
                self.label.configure(image=self.photo)
                self.latest_rgb = image.convert("RGB")
                request.displayed += 1
                request.display_times.append(time.monotonic())
            self.status.set(request.state)
        elif request is not None and request.cancel.is_set() and request.done.is_set():
            self.status.set("stopped")
        self.timer = self.root.after(16, self.tick)

    def close(self):
        if self.closed:
            return
        self.stop()
        self.closed = True
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.photo = self.latest_rgb = None
