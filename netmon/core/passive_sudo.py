"""Bounded sudo retries for explicitly marked display reads only.

Never wrap mutations or their verification in an observation. Explicit reads
outside an observation remain live, regardless of the display's auth pause.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import re
import threading
import time

BACKOFF_SECONDS = 30.0
UNAVAILABLE = (1, "")
_PASSWORD_REQUIRED = re.compile(
    r"^sudo: .*(password|passwort)", re.IGNORECASE | re.MULTILINE
)
_observer = ContextVar("netmon_passive_sudo_observer", default=None)


@contextmanager
def observation(app):
    token = _observer.set(app)
    try:
        yield
    finally:
        _observer.reset(token)


def current_app():
    return _observer.get()


def paused(app):
    return time.monotonic() < float(app.__dict__.get("_ufw_sudo_backoff_until", 0))


def note_result(app, rc, output):
    if rc == 0:
        app.__dict__.pop("_ufw_sudo_backoff_until", None)
    elif _PASSWORD_REQUIRED.search(str(output or "")):
        app.__dict__["_ufw_sudo_backoff_until"] = time.monotonic() + BACKOFF_SECONDS
        app.__dict__.pop("_passive_sudo_samples", None)


def reset(app):
    """Resume observation immediately after conscious sudo authentication."""
    app.__dict__.pop("_ufw_sudo_backoff_until", None)
    app.__dict__.pop("_passive_sudo_samples", None)
    app.__dict__.pop("_profile_ipv6_display_sample", None)


def read(app, key, callback, *, ttl=0):
    """Read a (rc, output) pair, sharing only explicitly passive observations.

    A busy background read never makes Tk wait for its sudo process. No command
    output containing profile keys is cached: callers must leave ttl at zero.
    """
    lock = app.__dict__.setdefault("_passive_sudo_lock", threading.RLock())
    if not lock.acquire(blocking=False):
        return UNAVAILABLE
    try:
        if paused(app):
            return UNAVAILABLE
        samples = app.__dict__.setdefault("_passive_sudo_samples", {})
        sample = samples.get(key)
        if ttl and sample and time.monotonic() - sample[0] < ttl:
            return sample[1]
        rc, output = callback()
        note_result(app, rc, output)
        if ttl and rc == 0:
            samples[key] = (time.monotonic(), (rc, output))
        return rc, output
    finally:
        lock.release()
