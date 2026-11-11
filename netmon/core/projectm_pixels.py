"""Continuous fixed raw-pixel boundary. No image/X11 decoding in the UI.

The reader capsule sees only private X and its cookie. Tk gets one latest
profile-sized RGBA frame, never paths, dimensions, X11 requests or image containers.
"""

from functools import lru_cache
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import threading
import time

from netmon.core import projectm_profile as profiles

from netmon.core import radio_sandbox as sandbox

WIDTH, HEIGHT = 640, 480
FRAME_BYTES = WIDTH * HEIGHT * 4
CHUNK = 65536
FRAME_TIMEOUT = 5
WORKER = Path(__file__).with_name("projectm_pixel_worker.py")


class FrameMailbox:
    def __init__(self, resolution=profiles.DEFAULT):
        self.profile = profiles.resolve(resolution)
        self._lock = threading.Lock()
        self._frame = None
        self.received = self.dropped = 0

    def put(self, frame):
        if type(frame) is not bytes or len(frame) != self.profile.frame_bytes:
            raise ValueError("Invalid fixed raw frame")
        with self._lock:
            self.dropped += self._frame is not None
            self._frame = frame
            self.received += 1

    def take(self):
        with self._lock:
            result, self._frame = self._frame, None
            return result


class RawFrames:
    def __init__(self, resolution=profiles.DEFAULT):
        self.frame_bytes = profiles.resolve(resolution).frame_bytes
        self.buffer = bytearray()
        self.peak = 0

    def feed(self, data):
        if type(data) is not bytes or len(data) > CHUNK:
            raise ValueError("Invalid bounded raw chunk")
        self.buffer.extend(data)
        self.peak = max(self.peak, len(self.buffer))
        if len(self.buffer) < self.frame_bytes:
            return None
        frame = bytes(self.buffer[: self.frame_bytes])
        del self.buffer[: self.frame_bytes]
        return frame


@lru_cache(maxsize=1)
def _runtime():
    stdlib, python = sandbox._pcm_runtime()
    return stdlib, tuple(
        sorted(set(python) | set(sandbox._runtime_files(sandbox.FFMPEG)))
    )


def _command(directory, plan, display_fd, auth_fd, resolution=profiles.DEFAULT):
    profile = profiles.resolve(resolution)
    stdlib, files = plan
    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/pixel-worker.py",
            "--resolution",
            profile.key,
        ],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(WORKER),
        "/run/pixel-worker.py",
        "--ro-bind",
        str(Path(profiles.__file__)),
        "/run/projectm-profile.py",
        "--ro-bind-fd",
        str(display_fd),
        "/tmp/.X11-unix/X1",
        "--ro-bind-data",
        str(auth_fd),
        "/run/client.auth",
        "--setenv",
        "DISPLAY",
        ":1",
        "--setenv",
        "XAUTHORITY",
        "/run/client.auth",
    ]
    command[command.index("--") : command.index("--")] = extra
    return command


class PixelStream:
    def __init__(
        self,
        process,
        temporary,
        resolution=profiles.DEFAULT,
        *,
        owns_process=True,
        marker=None,
    ):
        self.profile = profiles.resolve(resolution)
        self.process, self.temporary = process, temporary
        self.owns_process = owns_process
        self.reader = (
            process.stdout
            if owns_process
            else os.fdopen(os.dup(process.stdout.fileno()), "rb", buffering=0)
        )
        self.marker = marker
        self.frames = FrameMailbox(self.profile.key)
        self.ready = threading.Event()
        self._ended = threading.Event()
        self._lock = threading.RLock()
        self.error = ""
        self.received_bytes = 0
        self.thread = threading.Thread(
            target=self._read, name="projectm-pixels", daemon=True
        )
        try:
            self.thread.start()
        except Exception:
            self.stop()
            raise

    def _read(self):
        parser = RawFrames(self.profile.key)
        last_frame = budget_time = time.monotonic()
        capacity = self.profile.frame_bytes * self.profile.burst_frames
        credit = capacity
        marker = self.marker
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.reader, selectors.EVENT_READ)
                while not self._ended.is_set():
                    now = time.monotonic()
                    if now - last_frame > FRAME_TIMEOUT:
                        raise TimeoutError(
                            f"Private pixel stream stalled ({self.received_bytes} bytes)"
                        )
                    if not selector.select(0.05):
                        continue
                    data = os.read(self.reader.fileno(), CHUNK)
                    if not data:
                        raise ValueError("Private pixel stream ended")
                    if marker:
                        size = min(len(marker), len(data))
                        if data[:size] != marker[:size]:
                            raise ValueError("Invalid GPU pixel stream marker")
                        marker, data = marker[size:], data[size:]
                    self.received_bytes += len(data)
                    credit = min(
                        capacity,
                        credit
                        + (now - budget_time)
                        * self.profile.frame_bytes
                        * self.profile.max_fps,
                    )
                    credit -= len(data)
                    budget_time = now
                    if credit < 0:
                        raise ValueError("Private pixel stream rate exceeded")
                    frame = parser.feed(data)
                    if frame is not None:
                        self.frames.put(frame)
                        last_frame = time.monotonic()
                        self.ready.set()
        except Exception as exc:
            if not self._ended.is_set():
                self.error = f"{type(exc).__name__}: {exc}"[:256]
        finally:
            self.ready.set()

    def poll(self):
        return 2 if self.error else self.process.poll()

    def stop(self):
        with self._lock:
            self._ended.set()
            if self.owns_process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            elif self.owns_process:
                self.process.wait(timeout=2)
            if (
                self.thread.ident is not None
                and self.thread is not threading.current_thread()
            ):
                self.thread.join(timeout=1)
            self.reader.close()
            self.frames.take()
            self.temporary.cleanup()


def start(
    display, *, work_root=None, cancelled=lambda: False, resolution=profiles.DEFAULT
):
    profile = profiles.resolve(resolution)
    plan = _runtime()
    temporary = tempfile.TemporaryDirectory(prefix="projectm-pixels-", dir=work_root)
    stream = process = None
    try:
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        if cancelled():
            raise sandbox.RadioSandboxError("Pixelstart wurde entwertet.")
        with display.display_binding() as (display_fd, auth_fd):
            process = subprocess.Popen(
                sandbox._limited(
                    _command(directory, plan, display_fd, auth_fd, profile.key),
                    "pm-pixels",
                ),
                env=sandbox._quota_env(),
                cwd="/",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                pass_fds=(display_fd, auth_fd),
                close_fds=True,
            )
        stream = PixelStream(process, temporary, profile.key)
        deadline = time.monotonic() + 8
        while not stream.ready.wait(0.05):
            if cancelled() or time.monotonic() >= deadline:
                raise sandbox.RadioSandboxError("Privater Pixelstart abgebrochen.")
        if cancelled() or stream.poll() is not None or stream.frames.received == 0:
            raise sandbox.RadioSandboxError(
                "Privater Pixelstrom nicht bereit: "
                + (stream.error or "Helfer beendet.")
            )
        return stream
    except Exception:
        if stream is not None:
            stream.stop()
        else:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=2)
                process.stdout.close()
            temporary.cleanup()
        raise
