"""NetMon service helpers for operation coordination."""

from __future__ import annotations

import threading
from typing import Callable, Optional


class NetworkOperationCoordinator:
    """Coordinates mutually exclusive network operations with reentrant ownership."""

    def __init__(
        self,
        lock: Optional[threading.RLock] = None,
        log_busy_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.lock = lock or threading.RLock()
        self.log_busy_fn = log_busy_fn
        self.active_operation = ""
        self.owner_thread_id = None
        self.depth = 0

    def try_begin(self, operation: str, log_busy: bool = True) -> bool:
        current_tid = threading.get_ident()

        if self.owner_thread_id == current_tid:
            self.lock.acquire()
            self.depth += 1
            return True

        if not self.lock.acquire(blocking=False):
            if log_busy and callable(self.log_busy_fn):
                active = (self.active_operation or "andere Netzwerkaktion").strip()
                self.log_busy_fn(
                    f"Netzwerkaktion blockiert: {operation} wird nicht gestartet, da bereits '{active}' läuft."
                )
            return False

        self.owner_thread_id = current_tid
        self.depth = 1
        self.active_operation = operation
        return True

    def end(self) -> None:
        current_tid = threading.get_ident()
        if self.owner_thread_id != current_tid:
            return

        self.depth = max(0, int(self.depth) - 1)
        if self.depth == 0:
            self.owner_thread_id = None
            self.active_operation = ""
        self.lock.release()


class RollbackTransaction:
    """Simple rollback stack for multi-step operations.

    Register rollback callbacks after each successful mutating step. When
    rollback is triggered, callbacks execute in reverse order.
    """

    def __init__(
        self,
        name: str,
        *,
        log_fn: Optional[Callable[[str], None]] = None,
        log_debug_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.name = (name or "Transaktion").strip()
        self._log_fn = log_fn
        self._log_debug_fn = log_debug_fn
        self._callbacks = []
        self._committed = False

    def add_rollback(self, label: str, callback: Callable[[], None]) -> None:
        if not callable(callback):
            return
        self._callbacks.append(((label or "Rollback-Schritt").strip(), callback))

    def commit(self) -> None:
        self._committed = True
        self._callbacks.clear()

    def rollback(self) -> bool:
        if self._committed:
            return True

        ok = True
        callbacks = list(reversed(self._callbacks))
        self._callbacks.clear()
        for label, callback in callbacks:
            try:
                callback()
            except Exception as exc:  # pragma: no cover - defensive path
                ok = False
                if callable(self._log_fn):
                    self._log_fn(f"{self.name}: Rollback fehlgeschlagen ({label}).")
                if callable(self._log_debug_fn):
                    self._log_debug_fn(f"{self.name}: Rollback-Fehler ({label}): {exc}")
        if ok and callbacks and callable(self._log_debug_fn):
            self._log_debug_fn(
                f"{self.name}: Rollback mit {len(callbacks)} Schritt(en) ausgeführt."
            )
        return ok
