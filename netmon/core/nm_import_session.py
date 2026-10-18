"""In-memory NM job journal. References are hints, never ownership authority."""

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
import threading
import time

MAX_REFERENCES = 512


@dataclass
class ImportEntry:
    token: int
    job_id: int
    source: str
    created_at: int
    result: dict | None = None
    unowned_name: str = ""
    phase: str = "pending"
    deleting_job: int | None = None
    deleted: bool = False


@dataclass
class ImportJob:
    token: int
    kind: str
    owner: object = field(repr=False)
    phase: str = "queued"
    revision: int = 0
    errors: list = field(default_factory=list)


class ImportSession:
    def __init__(self, state):
        self.lock = threading.RLock()
        self.revision = 0
        self.sequence = 0
        self.active = set()
        self.jobs = deque(maxlen=64)
        self.entries = {}
        self.replace_when_idle(state)

    def _token(self):
        self.sequence += 1
        return self.sequence

    def replace_when_idle(self, state):
        """Compatibility setter for explicit idle initialization, never a job commit."""
        with self.lock:
            if self.active:
                raise RuntimeError("NM jobs active; snapshot replacement forbidden")
            self.base = deepcopy(state)
            self.entries.clear()
            self.include_owned = "owned_connections" in state
            for candidate in state.get("owned_connections", []):
                token = self._token()
                self.entries[token] = ImportEntry(
                    token,
                    0,
                    "",
                    state["imported_at"],
                    deepcopy(candidate),
                    phase="created",
                )
            self.revision += 1

    def new_job(self, kind):
        with self.lock:
            job = ImportJob(self._token(), kind, self)
            self.jobs.append(job)
            self.active.add(job.token)
            self.revision += 1
            return job

    def start(self, job, kind):
        with self.lock:
            if (
                job.owner is not self
                or job.kind != kind
                or job.token not in self.active
                or job.phase != "queued"
            ):
                return False
            job.phase = "running"
            self.revision += 1
            return True

    def reserve(self, job, source):
        with self.lock:
            if (
                job.owner is not self
                or job.kind != "import"
                or job.phase != "running"
                or job.token not in self.active
            ):
                raise RuntimeError("Import job is not running")
            # A secondary delete transition may have failed after the actual
            # successful deletion. Its recorded result must not consume budget.
            for token in [key for key, value in self.entries.items() if value.deleted]:
                self.entries.pop(token)
            if len(self.entries) >= MAX_REFERENCES:
                raise RuntimeError("NM session reference limit reached before import")
            token = self._token()
            entry = ImportEntry(token, job.token, source, int(time.time()))
            self.entries[token] = entry
            self.revision += 1
            return entry

    def finish_import(self, entry):
        # The caller has already captured the RPC result in the reserved entry.
        with self.lock:
            entry.phase = "created" if entry.result is not None else "unowned"
            self.include_owned = True
            self.revision += 1

    def failed_import(self, entry):
        with self.lock:
            if entry.result is None and not entry.unowned_name:
                self.entries.pop(entry.token, None)
            else:
                entry.phase = "recovery"
            self.revision += 1

    def finish(self, job, phase):
        with self.lock:
            if job.owner is not self:
                raise RuntimeError("Foreign NM job")
            job.phase = phase
            for entry in self.entries.values():
                if entry.deleting_job == job.token and not entry.deleted:
                    entry.deleting_job = None
                    entry.phase = "recovery"
            self.active.discard(job.token)
            self.revision += 1
            job.revision = self.revision

    def error(self, job, message):
        with self.lock:
            # Diagnostics contain no configs, private keys or source contents.
            job.errors.append(message)
            job.errors[:] = job.errors[-16:]
            self.revision += 1
            if job.token not in self.active:
                job.revision = self.revision

    def snapshot(self):
        with self.lock:
            result = {
                key: deepcopy(self.base[key])
                for key in ("connections", "source_files", "imported_at")
            }
            owned = []
            for entry in self.entries.values():
                if entry.deleted or (entry.result is None and not entry.unowned_name):
                    continue
                if entry.result is not None:
                    owned.append(deepcopy(entry.result))
                    name = entry.result.get("name", "")
                else:
                    name = entry.unowned_name
                if name and name not in result["connections"]:
                    result["connections"].append(name)
                if entry.source and entry.source not in result["source_files"]:
                    result["source_files"].append(entry.source)
                result["imported_at"] = max(result["imported_at"], entry.created_at)
            if self.include_owned or owned:
                result["owned_connections"] = owned
            return result

    def references(self):
        with self.lock:
            return [
                (entry.token, deepcopy(entry.result))
                for entry in self.entries.values()
                if entry.result is not None
                and not entry.deleted
                and entry.deleting_job is None
            ]

    def claim_delete(self, token, candidate, job):
        with self.lock:
            if (
                job.owner is not self
                or job.kind != "rollback"
                or job.token not in self.active
                or job.phase != "running"
            ):
                return None
            entry = self.entries.get(token)
            if entry is None or entry.deleted or entry.deleting_job is not None:
                return None
            if (entry.result.get("uuid"), entry.result.get("receipt_id")) != (
                candidate["uuid"],
                candidate["receipt_id"],
            ):
                return None
            entry.deleting_job = job.token
            entry.phase = "deleting"
            self.revision += 1
            return entry

    def finish_delete(self, entry, job):
        with self.lock:
            if entry.deleting_job != job.token:
                return
            if entry.deleted:
                self.entries.pop(entry.token, None)
            else:
                entry.phase = "recovery"
                entry.deleting_job = None
            self.revision += 1

    def notification(self, job):
        with self.lock:
            return {"revision": job.revision, "consumed": False, "job": job}

    def consume_notification(self, event):
        with self.lock:
            if event["consumed"]:
                return False
            event["consumed"] = True
            return event["revision"] == self.revision == event["job"].revision
