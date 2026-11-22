"""Offline questions, revision checks and private, independent learning progress."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import random
import re
import uuid

try:
    from netmon.core.private_state import (
        private_state_lock,
        read_private_json,
        write_private_json,
    )
    from netmon.core.state import get_netmon_documents_subdir
    from netmon.core.utils import user_json_write_scope
    from netmon.services.linux_help_markdown_service import _read_regular
except ModuleNotFoundError:
    from core.private_state import (
        private_state_lock,
        read_private_json,
        write_private_json,
    )
    from core.state import get_netmon_documents_subdir
    from core.utils import user_json_write_scope
    from services.linux_help_markdown_service import _read_regular

BANK_PATH = Path(__file__).resolve().parents[2] / "docs/linux-quiz/questions.json"
MAX_QUESTIONS = 256
MAX_ROUNDS = 30
MAX_CATEGORIES = 64
DEFAULT_SETTINGS = {"enabled": False, "minutes": 60, "count": 5, "kind": "both"}


def _text(value, limit):
    return (
        isinstance(value, str)
        and 0 < len(value) <= limit
        and all(c.isprintable() or c == "\n" for c in value)
    )


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,48}", value)


def _category(value):
    # Categories recur in seven daily buckets; bound encoded size as well.
    return _text(value, 64) and len(value.encode("utf-8")) <= 64


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


@dataclass(frozen=True)
class Question:
    id: str
    revision: int
    kind: str
    entry_id: str
    name: str
    command: str
    category: str
    source_sha256: str
    prompt: str
    options: tuple[str, ...]
    answer: int
    explanation: str
    evidence: str
    status: str


def load_questions(path=None):
    payload = json.loads(_read_regular(Path(path or BANK_PATH), 1024 * 1024))
    if (
        not isinstance(payload, dict)
        or type(payload.get("schema_version")) is not int
        or payload["schema_version"] != 1
        or not isinstance(payload.get("questions"), list)
        or not 1 <= len(payload["questions"]) <= MAX_QUESTIONS
    ):
        raise ValueError("Ungültiger Quiz-Fragenbestand.")
    questions = []
    identifiers = set()
    for row in payload["questions"]:
        if not isinstance(row, dict):
            raise ValueError("Ungültige Quizfrage.")
        try:
            q = Question(**row)
        except TypeError as error:
            raise ValueError("Unvollständige Quizfrage.") from error
        if (
            not _identifier(q.id)
            or q.id in identifiers
            or not _identifier(q.entry_id)
            or not _integer(q.revision, 1, 1000000)
            or q.kind not in ("command", "glossary")
            or not _text(q.name, 128)
            or not isinstance(q.command, str)
            or len(q.command) > 128
            or not _category(q.category)
            or not isinstance(q.source_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", q.source_sha256)
            or not _text(q.prompt, 600)
            or not isinstance(q.options, list)
            or len(q.options) != 4
            or any(not _text(option, 300) for option in q.options)
            or len(set(q.options)) != 4
            or not _integer(q.answer, 0, 3)
            or not _text(q.explanation, 1200)
            or not _text(q.evidence, 600)
            or q.status not in ("reviewed", "review_pending")
        ):
            raise ValueError("Ungültige Quizfrage: " + str(q.id))
        identifiers.add(q.id)
        questions.append(Question(**{**row, "options": tuple(q.options)}))
    return questions


def available_questions(questions, entries, load_document):
    """No paths from the question bank; resolve through the existing reader."""
    index = {(e.get("entry_type", "command"), e.get("id")): e for e in entries}
    active, suspended = [], []
    for q in questions:
        item = index.get((q.kind, q.entry_id))
        reason = "Eintrag fehlt oder wurde verändert"
        if (
            item is not None
            and item.get("enabled", True)
            and item.get("name") == q.name
            and item.get("cmd", "").strip() == q.command
        ):
            try:
                document = load_document(item)
                if (
                    q.status == "reviewed"
                    and document is not None
                    and hashlib.sha256(document.source.encode("utf-8")).hexdigest()
                    == q.source_sha256
                    and q.evidence in document.source
                ):
                    active.append((q, item))
                    continue
                reason = "Dokumentfassung oder Frage erneut prüfen"
            except (OSError, ValueError, UnicodeError, RecursionError):
                reason = "Dokument konnte nicht geprüft werden"
        suspended.append((q, reason))
    return active, suspended


def choose_questions(
    pool,
    progress,
    count,
    *,
    kind="both",
    category="",
    read=None,
    errors_only=False,
    rng=None,
):
    rng = rng or random.SystemRandom()
    candidates = []
    weights = []
    for q, item in pool:
        previous = progress.get(q.id)
        # A revised question may be trained again but is no longer a current error.
        wrong = bool(previous and previous[0] == q.revision and previous[6])
        if (
            (kind != "both" and q.kind != kind)
            or (category and item.get("category") != category)
            or (read is not None and not read(item))
            or (errors_only and not wrong)
        ):
            continue
        candidates.append((q, item))
        weights.append(4 if wrong else 1)
    selected = []
    for _ in range(min(count, len(candidates))):
        index = rng.choices(range(len(candidates)), weights=weights, k=1)[0]
        selected.append(candidates.pop(index))
        weights.pop(index)
    return selected


def _empty_state():
    return {
        "version": 1,
        "settings": dict(DEFAULT_SETTINGS),
        "progress": {},
        "days": {},
        "rounds": [],
    }


def _settings(value):
    if (
        not isinstance(value, dict)
        or set(value) != set(DEFAULT_SETTINGS)
        or type(value["enabled"]) is not bool
        or not _integer(value["minutes"], 1, 1440)
        or not _integer(value["count"], 1, 30)
        or value["kind"] not in ("both", "command", "glossary")
    ):
        raise ValueError("Lernrunden: 1–1440 Minuten und 1–30 Fragen einstellen.")
    return dict(value)


def _pair(value):
    return (
        isinstance(value, list)
        and len(value) == 2
        and _integer(value[0], 0, 10**12)
        and _integer(value[1], 0, value[0])
    )


def validate_state(value):
    """Validate restored or concurrently written state before every mutation."""
    if (
        not isinstance(value, dict)
        or type(value.get("version")) is not int
        or value["version"] != 1
        or set(value) != {"version", "settings", "progress", "days", "rounds"}
    ):
        raise ValueError("Unbekanntes Lernquiz-Speicherformat.")
    _settings(value["settings"])
    progress, days, rounds = (value[k] for k in ("progress", "days", "rounds"))
    if (
        not isinstance(progress, dict)
        or len(progress) > MAX_QUESTIONS
        or not isinstance(days, dict)
        or len(days) > 7
        or not isinstance(rounds, list)
        or len(rounds) > MAX_ROUNDS
    ):
        raise ValueError("Lernquiz-Verlauf überschreitet die Grenzen.")
    for key, row in progress.items():
        if (
            not _identifier(key)
            or not isinstance(row, list)
            or len(row) != 7
            or not _integer(row[0], 1, 1000000)
            or row[1] not in ("command", "glossary")
            or not _identifier(row[2])
            or not _category(row[3])
            or not _pair(row[4:6])
            or type(row[6]) is not bool
        ):
            raise ValueError("Ungültiger Lernfortschritt.")
    if len({r[3] for r in progress.values()}) > MAX_CATEGORIES:
        raise ValueError("Zu viele Quizkategorien.")
    for date, day in days.items():
        if (
            not isinstance(date, str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
            or not isinstance(day, dict)
            or set(day) != {"total", "command", "glossary", "categories"}
            or any(not _pair(day[k]) for k in ("total", "command", "glossary"))
            or not isinstance(day["categories"], dict)
            or len(day["categories"]) > MAX_CATEGORIES
            or any(
                not _category(k) or not _pair(v) for k, v in day["categories"].items()
            )
        ):
            raise ValueError("Ungültige Tagesstatistik.")
    seen = set()
    for row in rounds:
        if (
            not isinstance(row, dict)
            or set(row)
            != {"id", "started", "ended", "planned", "answered", "correct", "complete"}
            or not _identifier(row["id"])
            or row["id"] in seen
            or not _text(row["started"], 40)
            or (row["ended"] is not None and not _text(row["ended"], 40))
            or not _integer(row["planned"], 1, 30)
            or not _integer(row["answered"], 0, row["planned"])
            or not _integer(row["correct"], 0, row["answered"])
            or type(row["complete"]) is not bool
            or row["complete"] != (row["answered"] == row["planned"])
            or (row["complete"] and row["ended"] is None)
        ):
            raise ValueError("Ungültiger Rundenverlauf.")
        seen.add(row["id"])
    return value


class QuizState:
    def __init__(self, path=None, *, now=None):
        self.path = Path(path) if path is not None else None
        self.now = now or (lambda: datetime.now().astimezone())
        self.data = _empty_state()
        self.error = ""
        self.reload()

    def _path(self):
        if self.path is None:
            self.path = Path(get_netmon_documents_subdir("LinuxHelp")) / "quiz.json"
        return self.path

    def _load(self):
        try:
            return validate_state(read_private_json(self._path()))
        except FileNotFoundError:
            return _empty_state()

    def reload(self):
        try:
            self.data = self._load()
            self.error = ""
        except (OSError, ValueError, UnicodeError, RecursionError) as error:
            self.error = "Quizdaten konnten nicht gelesen werden: " + str(error)
        return not self.error

    def _change(self, update):
        path = self._path()
        with user_json_write_scope(path):
            with private_state_lock(path.with_name(".linux_help_quiz_update.lock")):
                data = self._load()
                result = update(data)
                validate_state(data)
                write_private_json(path, data)
                self.data, self.error = data, ""
                return result

    def save_settings(self, settings):
        settings = _settings(settings)
        self._change(lambda data: data.update(settings=settings))

    def start_round(self, count):
        if not _integer(count, 1, 30):
            raise ValueError("Ungültiger Fragenumfang.")
        identifier = uuid.uuid4().hex

        def update(data):
            data["rounds"].append(
                {
                    "id": identifier,
                    "started": self.now().isoformat(),
                    "ended": None,
                    "planned": count,
                    "answered": 0,
                    "correct": 0,
                    "complete": False,
                }
            )
            data["rounds"] = data["rounds"][-MAX_ROUNDS:]

        self._change(update)
        return identifier

    def record_answer(self, round_id, index, question, choice):
        if choice is not None and not _integer(choice, 0, 3):
            raise ValueError("Ungültige Antwort.")
        correct = choice == question.answer

        def update(data):
            session = next((r for r in data["rounds"] if r["id"] == round_id), None)
            if (
                session is None
                or session["ended"] is not None
                or type(index) is not int
                or session["answered"] != index
            ):
                raise ValueError(
                    "Diese Antwort wurde bereits gezählt oder die Runde beendet."
                )
            q = question
            previous = data["progress"].get(q.id)
            attempts, hits = previous[4:6] if previous else (0, 0)
            data["progress"][q.id] = [
                q.revision,
                q.kind,
                q.entry_id,
                q.category,
                attempts + 1,
                hits + int(correct),
                not correct,
            ]
            today = self.now().date()
            first = (today - timedelta(days=6)).isoformat()
            data["days"] = {
                k: v for k, v in data["days"].items() if first <= k <= today.isoformat()
            }
            day = data["days"].setdefault(
                today.isoformat(),
                {
                    "total": [0, 0],
                    "command": [0, 0],
                    "glossary": [0, 0],
                    "categories": {},
                },
            )
            category = day["categories"].setdefault(q.category, [0, 0])
            for pair in (day["total"], day[q.kind], category):
                pair[0] += 1
                pair[1] += int(correct)
            session["answered"] += 1
            session["correct"] += int(correct)
            if session["answered"] == session["planned"]:
                session.update(complete=True, ended=self.now().isoformat())
            return correct

        return self._change(update)

    def end_round(self, round_id):
        def update(data):
            for session in data["rounds"]:
                if session["id"] == round_id and session["ended"] is None:
                    session["ended"] = self.now().isoformat()

        self._change(update)

    def statistics(self, *, week=False):
        result = {
            "total": [0, 0],
            "command": [0, 0],
            "glossary": [0, 0],
            "categories": defaultdict(lambda: [0, 0]),
        }

        def add(target, pair):
            target[0] += pair[0]
            target[1] += pair[1]

        if week:
            today = self.now().date()
            first = (today - timedelta(days=6)).isoformat()
            for date, day in self.data["days"].items():
                if first <= date <= today.isoformat():
                    for key in ("total", "command", "glossary"):
                        add(result[key], day[key])
                    for category, pair in day["categories"].items():
                        add(result["categories"][category], pair)
        else:
            for row in self.data["progress"].values():
                add(result["total"], row[4:6])
                add(result[row[1]], row[4:6])
                add(result["categories"][row[3]], row[4:6])
        result["distinct"] = len({(r[1], r[2]) for r in self.data["progress"].values()})
        result["rounds"] = deepcopy(self.data["rounds"])
        return result
