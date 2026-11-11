"""Opt-in stall diagnosis for the radio/visualizer window.

Enabled only with NETMON_RADIO_STALL_LOG=1. Appends short timestamped lines to
<state dir>/logs/radio_stall.log (owner-only file, bounded size). No command
output, no addresses, no titles: only event names and millisecond numbers.
"""

import collections
import gc
import os
import stat
import threading
import time

ENV = "NETMON_RADIO_STALL_LOG"
MAX_BYTES = 2_000_000
GC_REPORT_MS = 10.0
_lock = threading.Lock()
_disabled_after_error = False
_gc_started = {}
_gc_stats = {"count": 0, "max_ms": 0.0, "total_ms": 0.0}
# GC events are only queued here (deque.append needs no lock). They are written
# later by WindowMonitor.observe(): a collection can start while write() holds
# _lock, and writing from the callback would then deadlock that thread.
_gc_events = collections.deque(maxlen=64)


def _timestamp() -> str:
    now = time.time()
    return (
        f"{time.strftime('%H:%M:%S', time.localtime(now))}.{int(now * 1000) % 1000:03d}"
    )


def _gc_callback(phase, info):
    """Cheap, never raises, never writes or locks; any thread may run it."""
    try:
        generation = info.get("generation")
        if phase == "start":
            _gc_started[generation] = time.perf_counter()
            return
        started = _gc_started.pop(generation, None)
        if started is None:
            return
        ms = (time.perf_counter() - started) * 1000.0
        if generation == 2:
            _gc_stats["count"] += 1
            _gc_stats["total_ms"] += ms
            _gc_stats["max_ms"] = max(_gc_stats["max_ms"], ms)
        if ms >= GC_REPORT_MS or generation == 2:
            _gc_events.append(
                (_timestamp(), generation, ms, int(info.get("collected", 0)))
            )
    except Exception:
        pass


def flush_gc_events() -> None:
    """Write queued GC events with their original time; call outside GC callbacks.

    Bounded to the events present at entry: writing can itself trigger a
    collection, whose event is then written on the next call, not looped here.
    """
    for _ in range(len(_gc_events)):
        try:
            stamp, generation, ms, collected = _gc_events.popleft()
        except IndexError:
            return
        write("gc", _stamp=stamp, gen=generation, ms=ms, collected=collected)


AFTER_REPORT_MS = 50.0
_after_installed = False


def _callback_name(func) -> str:
    name = getattr(func, "__qualname__", None) or type(func).__name__
    owner = getattr(getattr(func, "__self__", None), "__class__", None)
    if owner is not None and "." not in str(name):
        name = f"{owner.__name__}.{name}"
    return str(name)[:80]


def _timed(func):
    if getattr(func, "_stall_log_timed", False):
        return func

    def run(*args, **kwargs):
        started = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - started) * 1000.0
            if ms >= AFTER_REPORT_MS:
                write("after-callback", ms=ms, name=_callback_name(func))

    run._stall_log_timed = True
    return run


def install_after_hook() -> bool:
    """Time every Tk `after`/`after_idle` callback in this process (opt-in only).

    tkinter's after_idle delegates to after, so one patch covers both.
    """
    global _after_installed
    if not enabled():
        return False
    if _after_installed:
        return True
    import tkinter

    original_after = tkinter.Misc.after

    def after(self, ms, func=None, *args):
        if func is None:
            return original_after(self, ms)
        return original_after(self, ms, _timed(func), *args)

    tkinter.Misc.after = after
    _after_installed = True
    return True


def install_gc_hook() -> bool:
    """Register the GC timing hook once per process; only when enabled."""
    if not enabled():
        return False
    if _gc_callback not in gc.callbacks:
        gc.callbacks.append(_gc_callback)
    return True


def enabled() -> bool:
    value = str(os.environ.get(ENV, "") or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def path() -> str:
    from netmon.core.state import get_netmon_state_dir

    return os.path.join(get_netmon_state_dir(), "logs", "radio_stall.log")


def _open_private_log(target: str) -> int:
    """Owner-only regular file; never follow a link, never reuse a foreign file.

    O_NONBLOCK: a FIFO (or other special file) at the path must not block the
    open before the fstat type check can refuse it; harmless for regular files.
    """
    fd = os.open(
        target,
        os.O_WRONLY
        | os.O_APPEND
        | os.O_CREAT
        | os.O_NOFOLLOW
        | os.O_CLOEXEC
        | os.O_NONBLOCK,
        0o600,
    )
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
        ):
            raise PermissionError("unsafe stall log target")
        if stat.S_IMODE(info.st_mode) != 0o600:
            os.fchmod(fd, 0o600)
        return fd
    except BaseException:
        os.close(fd)
        raise


def write(event: str, _stamp: str | None = None, **values) -> None:
    """Best effort; never raises into the caller. Unsafe targets disable it."""
    global _disabled_after_error
    if _disabled_after_error or not enabled():
        return
    fields = " ".join(
        f"{key}={value:.1f}" if isinstance(value, float) else f"{key}={value}"
        for key, value in values.items()
    )
    line = f"{_stamp or _timestamp()} {event} {fields}".rstrip()
    try:
        with _lock:
            target = path()
            os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
            fd = _open_private_log(target)
            try:
                if os.fstat(fd).st_size >= MAX_BYTES:
                    return
                os.write(fd, (line + "\n").encode("utf-8", "replace"))
            finally:
                os.close(fd)
    except Exception:
        _disabled_after_error = True


class WindowMonitor:
    """Tk-thread view of one window.

    - ui-stall: gap between two tick() calls (main-thread wake-up), > STALL_MS.
    - update-gap: gap between two tick() calls that saw the mailbox's received
      counter change. A ui-stall can cause one; it is not a renderer timestamp.
    - reader_fps: increase of the received counter (frames the pixel reader got).
    - shown_fps: frames actually pasted into the Tk image.
    """

    STALL_MS = 20.0
    GAP_MS = 60.0
    SUMMARY_S = 10.0
    MAX_LINES_PER_WINDOW = 20

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        now = clock()
        self._last_tick = now
        self._window_start = now
        self._received = None
        self._last_update = None
        self._reset()
        install_gc_hook()
        install_after_hook()
        write("monitor-start", gc_threshold=",".join(map(str, gc.get_threshold())))

    def _reset(self):
        self.ticks = self.stalls = self.updates = self.gaps = self.pastes = 0
        self.received_frames = 0
        self.max_stall = self.max_gap = self.max_paste = 0.0
        self.paste_total = 0.0
        self._lines = 0

    def _event(self, name, **values):
        if self._lines < self.MAX_LINES_PER_WINDOW:
            self._lines += 1
            write(name, **values)

    def observe(self, received, paste_ms=None):
        flush_gc_events()
        now = self._clock()
        gap = (now - self._last_tick) * 1000.0
        self._last_tick = now
        self.ticks += 1
        if gap > self.STALL_MS:
            self.stalls += 1
            self.max_stall = max(self.max_stall, gap)
            self._event("ui-stall", ms=gap)
        if received != self._received:
            if self._received is not None and self._last_update is not None:
                self.received_frames += max(0, received - self._received)
                update_gap = (now - self._last_update) * 1000.0
                self.updates += 1
                if update_gap > self.GAP_MS:
                    self.gaps += 1
                    self.max_gap = max(self.max_gap, update_gap)
                    self._event("update-gap", ms=update_gap)
            self._received = received
            self._last_update = now
        if paste_ms is not None:
            self.pastes += 1
            self.paste_total += paste_ms
            self.max_paste = max(self.max_paste, paste_ms)
            if paste_ms > self.STALL_MS:
                self._event("paste", ms=paste_ms)
        if now - self._window_start >= self.SUMMARY_S:
            seconds = now - self._window_start
            gc2 = dict(_gc_stats)
            _gc_stats.update(count=0, max_ms=0.0, total_ms=0.0)
            write(
                "summary",
                gc2=gc2["count"],
                gc2_max_ms=gc2["max_ms"],
                gc2_total_ms=gc2["total_ms"],
                s=seconds,
                ticks=self.ticks,
                stalls=self.stalls,
                max_stall_ms=self.max_stall,
                reader_fps=self.received_frames / seconds,
                shown_fps=self.pastes / seconds,
                updates=self.updates,
                gaps=self.gaps,
                max_gap_ms=self.max_gap,
                pastes=self.pastes,
                mean_paste_ms=(self.paste_total / self.pastes if self.pastes else 0.0),
                max_paste_ms=self.max_paste,
            )
            self._window_start = now
            self._reset()
