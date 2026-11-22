"""Question provenance, durable answers and restore to another private home."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import random

import pytest

from netmon.core import user_backup as backup
from netmon.core.private_state import MAX_STATE_BYTES
from netmon.core.utils import protect_user_json_writes
from netmon.features.linux_help_controller import load_entry_document
from netmon.services import linux_help_quiz_service as quiz
from netmon.services.linux_help_reading_service import ReadingState
from tests.test_user_backup import data as data


def entry(q):
    return {
        "id": q.entry_id,
        "entry_type": q.kind,
        "name": q.name,
        "cmd": q.command,
        "category": q.category,
    }


@pytest.fixture
def bank():
    return quiz.load_questions()


@pytest.fixture
def state(tmp_path):
    return quiz.QuizState(
        tmp_path / "NetMon/LinuxHelp/quiz.json",
        now=lambda: datetime(2026, 11, 15, 12, tzinfo=timezone.utc),
    )


def answer(state, q, choice):
    identifier = state.start_round(1)
    return state.record_answer(identifier, 0, q, choice)


def test_all_active_questions_match_reader_documents_and_evidence(bank):
    assert len(bank) == 225
    assert len({(q.kind, q.entry_id) for q in bank}) == 225
    assert sum(q.kind == "command" for q in bank) == 115
    assert sum(q.kind == "glossary" for q in bank) == 110
    active, suspended = quiz.available_questions(
        bank, map(entry, bank), load_entry_document
    )
    assert len(active) == len(bank) and suspended == []
    assert {q.answer for q in bank} == {0, 1, 2, 3}


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "../../outside"),
        ("id", []),
        ("entry_id", "a" * 49),
        ("revision", True),
        ("revision", 0),
        ("kind", []),
        ("kind", "shell"),
        ("name", ""),
        ("command", {}),
        ("category", "c" * 65),
        ("category", "ä" * 33),
        ("source_sha256", "bad"),
        ("source_sha256", []),
        ("prompt", "\x00"),
        ("options", ["a"] * 4),
        ("options", ["a", "b", "c", []]),
        ("options", ["a", "b", "c"]),
        ("answer", True),
        ("answer", 4),
        ("answer", -1),
        ("explanation", ""),
        ("evidence", ""),
        ("status", []),
        ("status", "approved_by_network"),
    ],
)
def test_invalid_question_bank_rejected(bank, tmp_path, field, value):
    payload = json.loads(quiz.BANK_PATH.read_text())
    payload["questions"][0][field] = value
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        quiz.load_questions(path)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(schema_version=True),
        lambda p: p.update(questions=[]),
        lambda p: p["questions"].append(p["questions"][0]),
        lambda p: p["questions"][0].update(document="../../etc/passwd"),
        lambda p: p.update(questions=p["questions"] * 20),
    ],
)
def test_invalid_catalog_shape_rejected(tmp_path, mutate):
    payload = json.loads(quiz.BANK_PATH.read_text())
    mutate(payload)
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        quiz.load_questions(path)


@pytest.mark.parametrize(
    "change",
    ["text", "pending", "identity", "missing", "error", "evidence", "disabled"],
)
def test_changed_or_unreviewed_document_is_suspended(bank, change):
    q = bank[0]
    item = entry(q)
    document = load_entry_document(item)
    if change == "text":
        document = replace(document, source=document.source + "\nNeue Fassung")
    elif change == "pending":
        q = replace(q, status="review_pending")
    elif change == "identity":
        item["name"] += " geändert"
    elif change == "missing":
        document = None
    elif change == "evidence":
        q = replace(q, evidence="Dieser Satz steht nicht im Dokument.")
    elif change == "disabled":
        item["enabled"] = False

    def load(_item):
        if change == "error":
            raise ValueError("hash mismatch")
        return document

    active, suspended = quiz.available_questions([q], [item], load)
    assert active == [] and suspended[0][0] == q


def test_filters_do_not_fall_back_to_unfiltered_questions(bank):
    pool = [(q, entry(q)) for q in bank]
    read_ids = {bank[0].entry_id}
    selected = quiz.choose_questions(
        pool, {}, 30, read=lambda item: item["id"] in read_ids
    )
    assert [q.id for q, _item in selected] == [bank[0].id]
    selected = quiz.choose_questions(pool, {}, 30, kind="glossary", category="Linux")
    assert len(selected) == 7 and all(
        q.kind == "glossary" and q.category == "Linux" for q, _item in selected
    )
    assert quiz.choose_questions(pool, {}, 5, category="missing") == []
    assert quiz.choose_questions(pool, {}, 5, errors_only=True) == []
    selected = quiz.choose_questions(pool, {}, 30)
    assert len(selected) == len({q.id for q, _item in selected}) == 30


def test_wrong_questions_are_weighted_without_duplicates_and_revision_clears_error(
    bank, state
):
    q = bank[0]
    answer(state, q, None)
    pool = [(item, entry(item)) for item in bank]
    errors = quiz.choose_questions(pool, state.data["progress"], 30, errors_only=True)
    assert [q.id for q, _item in errors] == [q.id]
    rng = random.Random(14)
    hits = sum(
        quiz.choose_questions(pool[:2], state.data["progress"], 1, rng=rng)[0][0] == q
        for _ in range(500)
    )
    assert hits > 330
    revised = replace(q, revision=q.revision + 1)
    assert (
        quiz.choose_questions(
            [(revised, entry(revised))], state.data["progress"], 5, errors_only=True
        )
        == []
    )
    answer(state, q, q.answer)
    assert (
        quiz.choose_questions(pool, state.data["progress"], 30, errors_only=True) == []
    )


def test_exactly_once_answers_unknown_and_partial_round_survive_restart(bank, state):
    q = bank[0]
    identifier = state.start_round(3)
    assert state.record_answer(identifier, 0, q, q.answer)
    before = state.path.read_bytes()
    with pytest.raises(ValueError):
        state.record_answer(identifier, 0, q, q.answer)
    assert state.path.read_bytes() == before
    assert not state.record_answer(identifier, 1, bank[1], None)
    state.end_round(identifier)
    with pytest.raises(ValueError):
        state.record_answer(identifier, 2, bank[2], bank[2].answer)
    restored = quiz.QuizState(state.path)
    assert not restored.error and restored.statistics()["total"] == [2, 1]
    assert restored.data["rounds"][-1]["answered"] == 2
    assert not restored.data["rounds"][-1]["complete"]
    assert state.path.stat().st_mode & 0o777 == 0o600


def test_answers_do_not_change_reading_status(bank, state):
    reading = ReadingState(state.path.with_name("reading.json"))
    q = bank[0]
    reading.change(entry(q), read=False)
    before = reading.path.read_bytes()
    answer(state, q, q.answer)
    assert reading.path.read_bytes() == before
    reading.change(entry(q), read=True)
    assert state.statistics()["total"] == [1, 1]


def test_statistics_have_lifetime_calendar_week_kinds_categories_and_distinct(
    bank, state
):
    clock = [datetime(2026, 11, 8, 12, tzinfo=timezone.utc)]
    state.now = lambda: clock[0]
    glossary_question = next(q for q in bank if q.kind == "glossary")
    answer(state, bank[0], bank[0].answer)
    clock[0] += timedelta(days=1)  # 9 November is the first included day on the 15th.
    answer(state, glossary_question, None)
    clock[0] += timedelta(days=6)
    answer(state, bank[0], None)
    total, week = state.statistics(), state.statistics(week=True)
    assert total["total"] == [3, 1] and week["total"] == [2, 0]
    assert total["command"] == [2, 1] and total["glossary"] == [1, 0]
    assert total["distinct"] == 2
    assert total["categories"][bank[0].category] == [2, 1]
    assert total["categories"][glossary_question.category] == [1, 0]
    clock[0] += timedelta(days=7)
    assert state.statistics(week=True)["total"] == [0, 0]
    assert state.statistics()["total"] == [3, 1]


def test_settings_and_concurrent_instances_preserve_answers(bank, state):
    other = quiz.QuizState(state.path)
    answer(state, bank[0], bank[0].answer)
    other.save_settings({"enabled": True, "minutes": 7, "count": 3, "kind": "glossary"})
    answer(state, bank[1], None)
    assert state.data["settings"] == other.data["settings"]
    assert state.statistics()["total"] == [2, 1]
    assert quiz.QuizState(state.path).data == state.data


@pytest.mark.parametrize(
    "key,value",
    [
        ("enabled", 1),
        ("minutes", 0),
        ("minutes", 1441),
        ("minutes", True),
        ("count", 31),
        ("count", "5"),
        ("kind", []),
        ("kind", "external"),
    ],
)
def test_invalid_settings_not_written(state, key, value):
    settings = {**quiz.DEFAULT_SETTINGS, key: value}
    with pytest.raises(ValueError):
        state.save_settings(settings)
    assert not state.path.exists()


def test_failed_write_does_not_count_answer_and_retry_counts_once(
    state, bank, monkeypatch
):
    identifier = state.start_round(1)
    previous = deepcopy(state.data)
    actual = quiz.write_private_json
    monkeypatch.setattr(
        quiz,
        "write_private_json",
        lambda *_a: (_ for _ in ()).throw(OSError("disk full")),
    )
    with pytest.raises(OSError):
        state.record_answer(identifier, 0, bank[0], bank[0].answer)
    assert state.data == previous
    monkeypatch.setattr(quiz, "write_private_json", actual)
    assert state.record_answer(identifier, 0, bank[0], bank[0].answer)
    assert state.statistics()["total"] == [1, 1]


@pytest.mark.parametrize(
    "payload",
    [
        b"broken",
        b'{"version": 2}',
        b"[]",
        json.dumps({**quiz._empty_state(), "settings": {"kind": []}}).encode(),
    ],
)
def test_corrupt_state_is_visible_and_never_overwritten(state, payload):
    state.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    state.path.write_bytes(payload)
    state.path.chmod(0o600)
    loaded = quiz.QuizState(state.path)
    assert loaded.error
    with pytest.raises((ValueError, OSError)):
        loaded.save_settings(quiz.DEFAULT_SETTINGS)
    assert state.path.read_bytes() == payload


def test_symlink_state_is_rejected_without_touching_target(state, tmp_path):
    target = tmp_path / "original.json"
    target.write_text("private original")
    state.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    state.path.symlink_to(target)
    loaded = quiz.QuizState(state.path)
    assert loaded.error
    with pytest.raises((ValueError, OSError)):
        loaded.start_round(1)
    assert target.read_text() == "private original" and state.path.is_symlink()


def test_restore_freeze_protects_quiz_writes(state):
    root = state.path.parents[1]
    protect_user_json_writes(root)
    try:
        with pytest.raises(PermissionError, match="Wiederherstellung"):
            state.save_settings(quiz.DEFAULT_SETTINGS)
    finally:
        protect_user_json_writes(root, enabled=False)


def test_bounded_history_keeps_lifetime_totals(state, bank):
    for _ in range(35):
        answer(state, bank[0], bank[0].answer)
    assert len(state.data["rounds"]) == 30
    assert state.statistics()["total"] == [35, 35]


@pytest.mark.parametrize("prefix", ["", "ä" * 30, "😀" * 15])
def test_maximum_supported_state_fits_private_file_bound(prefix):
    data = quiz._empty_state()

    def category(index):
        return prefix + str(index % 64).zfill(64 - len(prefix.encode("utf-8")))

    for index in range(256):
        data["progress"][str(index).zfill(48)] = [
            1000000,
            "glossary",
            str(index).zfill(48),
            category(index),
            10**12,
            10**12,
            False,
        ]
    for index in range(7):
        date = f"2026-11-{index+1:02}"
        data["days"][date] = {
            "total": [10**12, 10**12],
            "command": [10**12, 10**12],
            "glossary": [10**12, 10**12],
            "categories": {category(i): [10**12, 10**12] for i in range(64)},
        }
    for index in range(30):
        data["rounds"].append(
            {
                "id": str(index).zfill(48),
                "started": "x" * 40,
                "ended": "x" * 40,
                "planned": 30,
                "answered": 30,
                "correct": 30,
                "complete": True,
            }
        )
    quiz.validate_state(data)
    assert len(json.dumps(data, ensure_ascii=False).encode()) <= MAX_STATE_BYTES


def test_quiz_backup_restore_under_another_username_and_documents_path(data, bank):
    state = quiz.QuizState(data.root / "LinuxHelp/quiz.json")
    state.save_settings({"enabled": True, "minutes": 23, "count": 7, "kind": "both"})
    pilot_command = next(q for q in bank if q.id == "command.pwd.basic")
    pilot_glossary = next(q for q in bank if q.kind == "glossary")
    answer(state, pilot_command, None)
    answer(state, pilot_glossary, pilot_glossary.answer)
    original = state.path.read_bytes()
    exported = backup.export_backup(data.root, data.parent, selected=["LinuxHelp"])
    plan = backup.preview_restore(exported, data.target)
    assert any(row.path == "LinuxHelp/quiz.json" for row in plan.entries)
    _, report = backup.restore_backup(plan)
    assert report["complete"]
    path = data.target / "LinuxHelp/quiz.json"
    assert path.read_bytes() == original
    restored = quiz.QuizState(path)
    assert not restored.error and restored.data == state.data
    assert restored.statistics()["total"] == [2, 1]
    assert restored.data["settings"]["enabled"] is True
    assert restored.path.stat().st_mode & 0o777 == 0o600
    new_question = next(q for q in bank if q.id == "command.7z.basic")
    assert answer(restored, new_question, new_question.answer)
    new_glossary = next(q for q in bank if q.id == "glossary.it_0011.basic")
    assert answer(restored, new_glossary, new_glossary.answer)
    reloaded = quiz.QuizState(path)
    assert reloaded.statistics()["total"] == [4, 3]
    for question in (pilot_command, pilot_glossary):
        assert (
            reloaded.data["progress"][question.id]
            == state.data["progress"][question.id]
        )
