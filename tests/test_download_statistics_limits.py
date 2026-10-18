"""M-06: bounded sources and state, real PHP, owned fixtures, no public traffic."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import time

import pytest

from tests.test_download_statistics import (
    app as app,
    php as php,
    stats_token as stats_token,
    stats_authorization as stats_authorization,
    http_server as http_server,
    assert_no_temporary_files,
    b64,
    http_request,
)

ROOT = Path(__file__).resolve().parents[1]
GLOBAL = 128
PER_FILE = 64
OVERFLOW = "__other__"
MAX_BYTES = 4 * 1024 * 1024
MAX_TOKENS = 65536


@pytest.fixture
def limited_app(app):
    (app[0] / "download_limits_driver.php").write_bytes(
        (ROOT / "tests/php/download_limits_driver.php").read_bytes()
    )
    return app


def limits_call(php, app, **payload):
    result = subprocess.run(
        [
            php,
            "-n",
            "-d",
            "memory_limit=64M",
            str(app[0] / "download_limits_driver.php"),
        ],
        input=json.dumps({"path": str(app[1]), **payload}),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    return json.loads(result.stdout)


def write_state(app, state):
    app[1].write_text(json.dumps(state))


def assert_source_caps(stats):
    assert len(stats["sources"]) <= GLOBAL
    assert all(len(key.encode()) <= 256 for key in stats["sources"])
    for entry in stats["files"].values():
        assert len(entry["sources"]) <= PER_FILE
        assert all(len(key.encode()) <= 256 for key in entry["sources"])


def test_thousands_of_unique_sources_stop_growing_and_keep_all_counts(php, limited_app):
    result = limits_call(php, limited_app, iterations=3000, rotate_files=3)
    stats = result["stats"]
    assert (result["successes"], result["failures"]) == (3000, 0)
    assert stats["total_downloads"] == 3007
    assert_source_caps(stats)
    assert len(stats["sources"]) == GLOBAL
    assert sum(stats["sources"].values()) == 3007
    assert stats["sources"][OVERFLOW] == 3000 - (GLOBAL - 2)
    for index in range(3):
        entry = stats["files"][f"file-{index}"]
        assert len(entry["sources"]) == PER_FILE
        assert entry["count"] == sum(entry["sources"].values()) == 1000
        assert entry["sources"][OVERFLOW] == 1000 - (PER_FILE - 1)
    size = limited_app[1].stat().st_size
    again = limits_call(
        php, limited_app, iterations=1000, rotate_files=3, prefix="another-"
    )
    assert (again["successes"], again["failures"]) == (1000, 0)
    assert_source_caps(again["stats"])
    assert sum(again["stats"]["sources"].values()) == 4007
    assert limited_app[1].stat().st_size < size + 5000
    assert limited_app[1].stat().st_size < 300000
    assert_no_temporary_files(limited_app)


@pytest.mark.parametrize(
    "count", [0, PER_FILE - 2, PER_FILE - 1, GLOBAL - 2, GLOBAL - 1, GLOBAL, 1000]
)
def test_exact_source_boundaries_and_existing_labels(php, limited_app, count):
    state = limited_app[2]
    labels = {f"legacy-{i}": i + 1 for i in range(count)}
    state["sources"] = dict(labels)
    state["files"]["artifact"]["sources"] = dict(labels)
    write_state(limited_app, state)
    result = limits_call(php, limited_app, source=b64("new-label"))
    stats = result["stats"]
    assert result["successes"] == 1
    assert_source_caps(stats)
    expected = sum(labels.values()) + 1
    assert sum(stats["sources"].values()) == expected
    assert sum(stats["files"]["artifact"]["sources"].values()) == expected
    for name, limit in [("sources", GLOBAL)]:
        assert ("new-label" in stats[name]) == (count < limit - 1)
    assert ("new-label" in stats["files"]["artifact"]["sources"]) == (
        count < PER_FILE - 1
    )
    if count:
        assert (
            limits_call(php, limited_app, source=b64("legacy-0"))["stats"]["sources"][
                "legacy-0"
            ]
            == 2
        )


def test_reserved_overflow_bucket_is_not_a_separate_escape_hatch(php, limited_app):
    state = limited_app[2]
    state["sources"] = {OVERFLOW: 20, **{f"s{i}": 1 for i in range(200)}}
    state["files"]["artifact"]["sources"] = dict(state["sources"])
    write_state(limited_app, state)
    result = limits_call(php, limited_app, iterations=10, source=b64(OVERFLOW))
    assert_source_caps(result["stats"])
    assert sum(result["stats"]["sources"].values()) == 230
    assert result["stats"]["sources"][OVERFLOW] == 20 + (200 - 127) + 10


@pytest.mark.parametrize(
    "value",
    [
        b"x" * 2000000,
        b"\xff" * 1000000,
        ("😀" * 500000).encode(),
        b"a" * 255 + "€".encode(),
        b"a" * 254 + b"\xff",
    ],
    ids=[
        "large-ascii",
        "large-invalid",
        "large-unicode",
        "cut-unicode",
        "cut-substitution",
    ],
)
def test_large_unicode_and_invalid_utf8_sources_remain_bounded(php, limited_app, value):
    result = limits_call(php, limited_app, source=b64(value))
    assert result["successes"] == 1
    stats = result["stats"]
    assert_source_caps(stats)
    source = stats["recent_events"][0]["source"]
    assert len(source.encode()) <= 256 and source in stats["sources"]
    assert stats["sources"]["seed"] == 7
    assert_no_temporary_files(limited_app)


def test_normalized_legacy_labels_merge_without_losing_counts(php, limited_app):
    state = limited_app[2]
    common = "x" * 256
    state["sources"] = {common + "a": 10, common + "b": 20, " spaced ": 3, "spaced": 4}
    state["files"]["artifact"]["sources"] = dict(state["sources"])
    write_state(limited_app, state)
    original = limited_app[1].read_bytes()
    read = limits_call(php, limited_app, action="read")["stats"]
    assert read["sources"] == {common: 30, "spaced": 7}
    assert limited_app[1].read_bytes() == original
    saved = limits_call(php, limited_app, source=b64(common))["stats"]
    assert saved["sources"] == {common: 31, "spaced": 7}
    assert saved["files"]["artifact"]["sources"] == saved["sources"]


def test_concurrent_unique_sources_keep_all_successful_updates(php, limited_app):
    workers, iterations = 8, 60
    ready = limited_app[0].parent / "start-m06"

    def worker(index):
        return limits_call(
            php,
            limited_app,
            iterations=iterations,
            prefix=f"worker-{index}-",
            start=str(ready),
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, index) for index in range(workers)]
        ready.touch()
        results = [future.result() for future in futures]
    accepted = sum(result["successes"] for result in results)
    rejected = sum(result["failures"] for result in results)
    # Saturated workers may time out on the deliberately finite lock wait.
    # Every successful transaction must be counted exactly once, with no
    # half-updated global/per-file counters from rejected transactions.
    assert accepted > 0 and accepted + rejected == workers * iterations
    stats = json.loads(limited_app[1].read_bytes())
    assert (
        stats["total_downloads"] == stats["files"]["artifact"]["count"] == 7 + accepted
    )
    assert (
        sum(stats["sources"].values())
        == sum(stats["files"]["artifact"]["sources"].values())
        == 7 + accepted
    )
    assert_source_caps(stats)
    assert_no_temporary_files(limited_app)


@pytest.mark.parametrize("kind", ["oversized", "entries", "depth"])
def test_unsafe_existing_state_is_rejected_before_json_decode(php, limited_app, kind):
    if kind == "oversized":
        raw = b" " * (MAX_BYTES + 1)
    elif kind == "entries":
        raw = b"[" + b"0," * MAX_TOKENS + b"0]"
    else:
        raw = b"[" * 100 + b"0" + b"]" * 100
    limited_app[1].write_bytes(raw)
    inode = limited_app[1].stat().st_ino
    result = limits_call(php, limited_app, action="read", instrument=True)
    assert result["stats"]["total_downloads"] == 0
    assert result["final_decodes"] == 0
    assert result["peak_bytes"] < 32 * 1024 * 1024
    # The only read is final load. Probe again with a record and skip final load:
    result = limits_call(php, limited_app, instrument=True, skip_load=True)
    assert result["failures"] == 1
    assert result["decodes"] == 3  # source/label/target normalization only
    assert result["read_lengths"] == ([] if kind == "oversized" else [MAX_BYTES + 1])
    assert limited_app[1].read_bytes() == raw
    assert limited_app[1].stat().st_ino == inode
    assert_no_temporary_files(limited_app)


def test_file_growth_after_stat_is_still_a_bounded_read(php, limited_app):
    result = limits_call(php, limited_app, fault="grow-on-read", skip_load=True)
    assert result["failures"] == 1
    assert result["read_lengths"] == [MAX_BYTES + 1]
    assert limited_app[1].stat().st_size > MAX_BYTES
    assert json.loads(limited_app[1].read_text())["total_downloads"] == 7
    assert_no_temporary_files(limited_app)


@pytest.mark.parametrize(
    "kind",
    [
        "files",
        "days",
        "file-days",
        "sources-type",
        "file-sources-type",
        "file-entry",
        "event",
        "negative",
        "array-count",
        "float-count",
        "null-count",
        "null-file-sources",
    ],
)
def test_manipulated_collections_preserve_original_bytes(php, limited_app, kind):
    state = limited_app[2]
    if kind == "files":
        state["files"] = {f"f{i}": {} for i in range(65)}
    elif kind in {"days", "file-days"}:
        days = {
            (date(2000, 1, 1) + timedelta(days=i)).isoformat(): 1 for i in range(3661)
        }
        if kind == "days":
            state["days"] = days
        else:
            state["files"]["artifact"]["days"] = days
    elif kind == "sources-type":
        state["sources"] = "not an object"
    elif kind == "file-sources-type":
        state["files"]["artifact"]["sources"] = "bad"
    elif kind == "null-file-sources":
        state["files"]["artifact"]["sources"] = None
    elif kind == "file-entry":
        state["files"]["artifact"] = "bad"
    elif kind == "event":
        state["recent_events"] = ["bad"]
    else:
        state["sources"]["bad"] = {
            "negative": -1,
            "array-count": [],
            "float-count": 1.5,
            "null-count": None,
        }[kind]
    write_state(limited_app, state)
    original = limited_app[1].read_bytes()
    result = limits_call(php, limited_app)
    assert result["failures"] == 1 and result["stats"]["total_downloads"] == 0
    assert limited_app[1].read_bytes() == original
    assert_no_temporary_files(limited_app)


@pytest.mark.parametrize("kind", ["bytes", "structure", "serialize"])
def test_output_budget_or_serialization_failure_cannot_replace_state(
    php, limited_app, kind
):
    original, inode = limited_app[1].read_bytes(), limited_app[1].stat().st_ino
    result = limits_call(php, limited_app, action="output-budget", kind=kind)
    assert result["failures"] == 1
    assert (
        limited_app[1].read_bytes() == original
        and limited_app[1].stat().st_ino == inode
    )
    assert_no_temporary_files(limited_app)


@pytest.mark.parametrize(
    "fault", ["write-fail", "partial-fail", "zero-write", "flush-fail", "rename-fail"]
)
def test_atomic_io_guarantees_survive_source_compaction(php, limited_app, fault):
    state = limited_app[2]
    state["sources"] = {f"s{i}": 1 for i in range(500)}
    state["files"]["artifact"]["sources"] = dict(state["sources"])
    write_state(limited_app, state)
    original = limited_app[1].read_bytes()
    result = limits_call(php, limited_app, fault=fault)
    assert result["failures"] == 1
    assert limited_app[1].read_bytes() == original
    assert_no_temporary_files(limited_app)


def test_lock_contention_is_time_bounded_and_never_resets_data(php, limited_app):
    lock_path = Path(str(limited_app[1]) + ".lock")
    original = limited_app[1].read_bytes()
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        start = time.monotonic()
        result = limits_call(php, limited_app, skip_load=True)
        elapsed = time.monotonic() - start
        assert result["failures"] == 1 and 0.8 < elapsed < 3
        fcntl.flock(lock, fcntl.LOCK_UN)
    assert limited_app[1].read_bytes() == original
    assert limits_call(php, limited_app)["successes"] == 1


def test_config_cannot_raise_event_budget(php, limited_app):
    result = limits_call(php, limited_app, iterations=300, max_events=1000000)
    assert result["failures"] == 0
    assert len(result["stats"]["recent_events"]) == 200


def test_json_punctuation_inside_strings_is_not_an_entry_bomb(php, limited_app):
    state = limited_app[2]
    state["extension"] = '"\\{},:[]' * 20000
    write_state(limited_app, state)
    result = limits_call(php, limited_app)
    assert result["successes"] == 1
    assert result["stats"]["extension"] == state["extension"]


@pytest.mark.parametrize(
    "raw", [b'{"sources":', b'{"sources":{"\xff":1}}', b"", b"null"]
)
def test_invalid_json_and_utf8_stay_unchanged(php, limited_app, raw):
    limited_app[1].write_bytes(raw)
    assert limits_call(php, limited_app)["failures"] == 1
    assert limited_app[1].read_bytes() == raw


@pytest.mark.parametrize(
    "query",
    [
        "src[]=bad",
        "src[deep][0]=bad",
        "src=0",
        "src=__other__",
        "src=%FFx",
        "src=%E2%82%AC",
        "src=first&src=last",
        "source=ignored",
    ],
)
def test_unusual_http_sources_keep_download_and_stats_working(
    http_server, app, query, stats_authorization
):
    status, headers, _ = http_request(http_server, "/download.php?id=artifact&" + query)
    assert status == 302 and headers["Location"] == "/artifact.bin?dl=1"
    stats = json.loads(app[1].read_bytes())
    assert stats["total_downloads"] == 8
    assert_source_caps(stats)
    assert (
        http_request(http_server, "/download-stats.php", stats_authorization)[0] == 200
    )


@pytest.mark.parametrize("kind", ["large", "malformed", "structure"])
def test_bad_existing_storage_never_blocks_normal_http_download(
    http_server, app, kind, stats_authorization
):
    raw = {
        "large": b" " * (MAX_BYTES + 1),
        "malformed": b"{bad",
        "structure": b"[" + b"0," * MAX_TOKENS + b"0]",
    }[kind]
    app[1].write_bytes(raw)
    status, headers, _ = http_request(
        http_server, "/download.php?id=artifact&src=downloads-de"
    )
    assert status == 302
    assert (
        http_request(http_server, headers["Location"])[2] == b"valid download bytes\n"
    )
    assert app[1].read_bytes() == raw
    status, _, body = http_request(
        http_server, "/download-stats.php", stats_authorization
    )
    assert status == 200 and b"Nicht lesbar oder Statistiklimit" in body


def test_exact_byte_ceiling_allows_a_valid_existing_file(php, limited_app):
    raw = limited_app[1].read_bytes()
    limited_app[1].write_bytes(raw + b" " * (MAX_BYTES - len(raw)))
    result = limits_call(php, limited_app, instrument=True)
    assert result["successes"] == 1 and result["stats"]["total_downloads"] == 8
    assert result["read_lengths"] == [MAX_BYTES + 1]
    assert limited_app[1].stat().st_size < MAX_BYTES


def test_file_budget_keeps_existing_entries_and_refuses_an_extra_file(php, limited_app):
    state = limited_app[2]
    state["files"].update({f"old-{i}": {} for i in range(63)})
    write_state(limited_app, state)
    assert limits_call(php, limited_app)["successes"] == 1
    original = limited_app[1].read_bytes()
    result = limits_call(php, limited_app, id="new-file")
    assert result["failures"] == 1 and len(result["stats"]["files"]) == 64
    assert limited_app[1].read_bytes() == original


@pytest.mark.parametrize("include_today", [False, True])
def test_day_budget_preserves_history_and_existing_daily_updates(
    php, limited_app, include_today
):
    days = {(date(2000, 1, 1) + timedelta(days=i)).isoformat(): 1 for i in range(3660)}
    if include_today:
        days.pop(next(iter(days)))
        days[datetime.now(timezone.utc).date().isoformat()] = 1
    state = limited_app[2]
    state["days"] = dict(days)
    state["files"]["artifact"]["days"] = dict(days)
    write_state(limited_app, state)
    original = limited_app[1].read_bytes()
    result = limits_call(php, limited_app)
    assert result["successes"] == int(include_today)
    assert len(result["stats"]["days"]) == 3660
    if not include_today:
        assert limited_app[1].read_bytes() == original


def test_counter_saturation_never_becomes_a_float(php, limited_app):
    maximum = 2**63 - 1  # Supported deployment/test platform: 64-bit PHP.
    state = limited_app[2]
    state["total_downloads"] = state["files"]["artifact"]["count"] = maximum
    state["sources"] = {OVERFLOW: maximum, **{f"s{i}": maximum for i in range(200)}}
    state["files"]["artifact"]["sources"] = dict(state["sources"])
    write_state(limited_app, state)
    result = limits_call(php, limited_app, source=b64(OVERFLOW))
    assert result["successes"] == 1
    assert result["stats"]["sources"][OVERFLOW] == maximum
    assert result["stats"]["total_downloads"] == maximum
    assert_source_caps(result["stats"])


def test_bounded_legacy_migration_preserves_totals_days_and_event_order(
    php, limited_app
):
    state = limited_app[2]
    sources = {f"old-{i}": 1 for i in range(5000)}
    state["sources"] = sources
    state["files"]["artifact"]["sources"] = dict(sources)
    write_state(limited_app, state)
    previous_event = state["recent_events"][0]
    result = limits_call(php, limited_app)
    stats = result["stats"]
    assert result["successes"] == 1
    assert_source_caps(stats)
    assert (
        sum(stats["sources"].values())
        == sum(stats["files"]["artifact"]["sources"].values())
        == 5001
    )
    assert stats["total_downloads"] == stats["files"]["artifact"]["count"] == 8
    assert (
        stats["days"]["2026-10-01"]
        == stats["files"]["artifact"]["days"]["2026-10-01"]
        == 7
    )
    assert stats["recent_events"][1] == previous_event
    assert result["peak_bytes"] < 32 * 1024 * 1024


def test_repeated_source_keeps_its_original_label(php, limited_app):
    result = limits_call(php, limited_app, iterations=300, source=b64("downloads-de"))
    assert result["failures"] == 0
    assert result["stats"]["sources"] == {"seed": 7, "downloads-de": 300}
    assert result["stats"]["files"]["artifact"]["sources"] == result["stats"]["sources"]


def test_sources_remain_escaped_in_statistics_view(http_server, stats_authorization):
    assert (
        http_request(
            http_server, "/download.php?id=artifact&src=%3Cscript%3Ebad%3C%2Fscript%3E"
        )[0]
        == 302
    )
    status, _, body = http_request(
        http_server, "/download-stats.php", stats_authorization
    )
    assert status == 200
    assert (
        b"&lt;script&gt;bad&lt;/script&gt;" in body
        and b"<script>bad</script>" not in body
    )
