"""Catalog limits, separate parser process and preservation of the old catalog."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.core import radio_catalog as catalog
from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio

ROW = {
    "name": "Test Radio",
    "url": "https://example.com/live",
    "tags": "Jazz, Live",
    "bitrate": "128",
}


def test_json_catalog_keeps_only_bounded_fields():
    raw = json.dumps([{**ROW, "unknown": {"ignored": True}, "lastcheckok": 1}]).encode()
    reply = json.loads(catalog.encode_catalog(raw, "json"))
    rows = catalog.validate_rows(reply["rows"])
    assert rows[0] == {
        "name": "Test Radio",
        "url": ROW["url"],
        "tags": ["Jazz", "Live"],
        "bitrate": 128,
        "lastcheckok": True,
    }


def test_xml_fields_match_legacy_mapping():
    raw = b"<directory><entry><server_name>Ice Radio</server_name><listen_url>https://example.com/live</listen_url><genre>Jazz, Live</genre><bitrate>128</bitrate></entry></directory>"
    rows = json.loads(catalog.encode_catalog(raw, "xml"))["rows"]
    assert rows[0]["name"] == "Ice Radio"
    assert rows[0]["tags"] == ["Jazz", "Live"]
    assert rows[0]["bitrate"] == 128


@pytest.mark.parametrize(
    "raw,kind",
    [
        (b'{"wrong":"shape"}', "json"),
        (b"[1]", "json"),
        (b"[{", "json"),
        (b'[{"votes":NaN}]', "json"),
        (b"<directory>", "xml"),
        (b"<wrong/>", "xml"),
        (b"<!DOCTYPE directory [<!ENTITY a 'expanded'>]><directory/>", "xml"),
        (b"\xff", "json"),
        (b"<directory>\0</directory>", "xml"),
    ],
)
def test_malformed_or_unsupported_catalogs_fail(raw, kind):
    with pytest.raises((ValueError, SyntaxError)):
        catalog.encode_catalog(raw, kind)


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "X" * 513),
        ("url", "X" * 8193),
        ("votes", -1),
        ("clickcount", 2**31),
        ("tags", ["x"] * 65),
        ("tags", {"bad": 1}),
        ("tags", ["x" * 129]),
        ("lastcheckok", "false"),
        ("name", {"nested": "bad"}),
    ],
)
def test_oversized_or_structurally_wrong_fields_fail(field, value):
    with pytest.raises((ValueError, OverflowError)):
        catalog.clean_row({**ROW, field: value})


@pytest.mark.parametrize(
    "rows",
    [
        {},
        [1],
        [{"execute": "bad"}],
        [{"votes": True}],
        [{"lastcheckok": 1}],
        [{"url": ["bad"]}],
        [{"tags": [True]}],
        [{"name": "line\nbreak"}],
    ],
)
def test_parent_schema_rejects_untrusted_helper_claims(rows):
    with pytest.raises(ValueError):
        catalog.validate_rows(rows)


def test_row_body_and_reply_limits_are_failures_not_silent_truncation(monkeypatch):
    monkeypatch.setattr(catalog, "MAX_ROWS", 1)
    with pytest.raises(ValueError):
        catalog.encode_catalog(json.dumps([ROW, ROW]).encode(), "json")
    monkeypatch.setattr(catalog, "MAX_BODY_BYTES", 8)
    with pytest.raises(ValueError):
        catalog.encode_catalog(b" " * 9, "json")
    monkeypatch.setattr(catalog, "MAX_BODY_BYTES", 1024)
    monkeypatch.setattr(catalog, "MAX_REPLY_BYTES", 20)
    with pytest.raises(ValueError):
        catalog.encode_catalog(json.dumps([ROW]).encode(), "json")


def test_xml_depth_and_node_limits(monkeypatch):
    raw = ("<directory>" + "<nested>" * 33 + "</nested>" * 33 + "</directory>").encode()
    with pytest.raises(ValueError):
        catalog.encode_catalog(raw, "xml")
    monkeypatch.setattr(catalog, "MAX_ROWS", 1)
    with pytest.raises(ValueError):
        catalog.encode_catalog(b"<directory><entry/><entry/></directory>", "xml")


def controlled_pipeline(monkeypatch, program):
    children = []
    real_popen = sandbox.subprocess.Popen
    monkeypatch.setattr(
        sandbox, "_fetch_runtime", lambda **_kwargs: (Path("/unused"), ())
    )

    def source(_directory, *_args):
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", program]

    def parser(_directory, _stdlib, _runtime, kind):
        return [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            str(sandbox.CATALOG),
            "--" + kind,
        ]

    def spawn(arguments, **kwargs):
        assert kwargs["close_fds"]
        assert "private-token" not in " ".join(arguments)
        child = real_popen(arguments, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_fetch_command", source)
    monkeypatch.setattr(sandbox, "_catalog_command", parser)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def test_two_process_pipeline_parses_and_cleans_up(monkeypatch, tmp_path):
    raw = json.dumps([ROW]).encode()
    children = controlled_pipeline(
        monkeypatch, f"import sys; sys.stdout.buffer.write({raw!r})"
    )
    rows = sandbox.fetch_catalog(
        "https://example.com/?private-token", work_root=tmp_path
    )
    assert rows[0]["name"] == "Test Radio"
    assert len(children) == 2 and all(child.poll() == 0 for child in children)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "program",
    [
        "import sys; sys.stdout.write('[{'); sys.exit(0)",
        "import sys; sys.stdout.write('[]'); sys.exit(2)",
        "import time; time.sleep(10)",
    ],
)
def test_source_failure_or_timeout_reaps_both_helpers(monkeypatch, tmp_path, program):
    children = controlled_pipeline(monkeypatch, program)
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.fetch_catalog("https://example.com/s", timeout=0.2, work_root=tmp_path)
    assert len(children) == 2 and all(child.poll() is not None for child in children)
    assert not list(tmp_path.iterdir())


def test_parser_limits_apply_only_to_the_child_process():
    import resource
    import subprocess

    before = resource.getrlimit(resource.RLIMIT_AS), resource.getrlimit(
        resource.RLIMIT_CPU
    )
    code = (
        "import runpy,resource,json; p=runpy.run_path("
        + repr(str(sandbox.CATALOG))
        + "); "
        "p['apply_process_limits'](); print(json.dumps([resource.getrlimit(resource.RLIMIT_AS),resource.getrlimit(resource.RLIMIT_CPU),resource.getrlimit(resource.RLIMIT_NPROC)]))"
    )
    child = subprocess.run(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            code,
        ],
        capture_output=True,
        text=True,
        timeout=3,
        check=True,
    )
    limits = json.loads(child.stdout)
    assert 0 < limits[0][1] <= 384 * 1024 * 1024
    assert 0 < limits[1][1] <= 8
    assert limits[2] == [0, 0]
    assert before == (
        resource.getrlimit(resource.RLIMIT_AS),
        resource.getrlimit(resource.RLIMIT_CPU),
    )


def test_parser_respects_already_lower_soft_limits(monkeypatch):
    import resource

    current = {
        resource.RLIMIT_AS: (16 * 1024 * 1024, 64 * 1024 * 1024),
        resource.RLIMIT_CPU: (2, 4),
        resource.RLIMIT_NPROC: (12, 30),
    }
    applied = {}
    monkeypatch.setattr(resource, "getrlimit", lambda name: current[name])
    monkeypatch.setattr(
        resource, "setrlimit", lambda name, limits: applied.update({name: limits})
    )
    catalog.apply_process_limits()
    assert applied == {
        resource.RLIMIT_AS: (16 * 1024 * 1024, 16 * 1024 * 1024),
        resource.RLIMIT_CPU: (2, 2),
        resource.RLIMIT_NPROC: (0, 0),
    }


@pytest.mark.parametrize("kind", ["json", "xml"])
def test_controller_never_uses_direct_urlopen_for_catalogs(monkeypatch, kind):
    monkeypatch.setattr(
        radio.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("direct catalog request"),
    )
    calls = []

    def fetch(url, **kwargs):
        calls.append(kwargs)
        return [{"name": "Safe Radio", "url": "https://example.com/live"}]

    monkeypatch.setattr(sandbox, "fetch_catalog", fetch)
    source_id = "icecast_json" if kind == "xml" else "radio_browser_api"
    assert radio._download_radio_source_payload(source_id)[0]["name"] == "Safe Radio"
    assert calls == ([{"kind": "xml"}] if kind == "xml" else [{"post": True}])


def test_failed_source_keeps_existing_catalog_and_metadata(monkeypatch, tmp_path):
    path = tmp_path / "radio_db.json"
    meta = tmp_path / "radio_db_meta.json"
    path.write_bytes(b"ORIGINAL CATALOG")
    meta.write_bytes(b"ORIGINAL METADATA")
    app = SimpleNamespace(
        radio_db_path=str(path), radio_db_meta_path=str(meta), log=lambda _message: None
    )
    monkeypatch.setattr(
        radio, "_radio_database_source_ids_for_download", lambda _app: ["good", "bad"]
    )

    def fetch(source_id):
        if source_id == "bad":
            raise sandbox.RadioSandboxError("synthetic source rejected")
        return [{"name": "New Radio", "url": "https://example.com/live"}]

    monkeypatch.setattr(radio, "_download_radio_source_payload", fetch)
    monkeypatch.setattr(radio, "_schedule_ui", lambda _app, callback: callback())
    monkeypatch.setattr(
        radio, "_set_radio_database_import_progress", lambda *_a, **_k: None
    )
    monkeypatch.setattr(
        radio, "save_radio_db", lambda *_a, **_k: pytest.fail("failed import persisted")
    )
    thread = radio.download_radio_db(app)
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert path.read_bytes() == b"ORIGINAL CATALOG"
    assert meta.read_bytes() == b"ORIGINAL METADATA"


@pytest.mark.parametrize("failure", [None, "rows", "bytes"])
def test_success_merges_once_and_aggregate_limit_failure_does_not_write(
    monkeypatch, tmp_path, failure
):
    path = tmp_path / "radio_db.json"
    meta = tmp_path / "radio_db_meta.json"
    path.write_text("[]")
    meta.write_text("{}")
    app = SimpleNamespace(
        radio_db_path=str(path), radio_db_meta_path=str(meta), log=lambda _message: None
    )
    monkeypatch.setattr(
        radio, "_radio_database_source_ids_for_download", lambda _app: ["one", "two"]
    )
    monkeypatch.setattr(
        radio,
        "_download_radio_source_payload",
        lambda source: [{"name": source, "url": f"https://example.com/{source}"}],
    )
    monkeypatch.setattr(radio, "_schedule_ui", lambda _app, callback: callback())
    monkeypatch.setattr(
        radio, "_set_radio_database_import_progress", lambda *_a, **_k: None
    )
    monkeypatch.setattr(radio, "refresh_radio_ui", lambda _app: None)
    monkeypatch.setattr(radio, "_show_radio_database_import_summary", lambda *_a: None)
    if failure == "rows":
        monkeypatch.setattr(catalog, "MAX_ROWS", 1)
    elif failure == "bytes":
        monkeypatch.setattr(catalog, "MAX_IMPORT_BYTES", 1)
    thread = radio.download_radio_db(app)
    thread.join(timeout=3)
    assert not thread.is_alive()
    if failure:
        assert path.read_text() == "[]" and meta.read_text() == "{}"
    else:
        assert [row["name"] for row in json.loads(path.read_text())] == ["one", "two"]
        assert json.loads(meta.read_text())["count"] == 2


# -- RC-01: single invalid upstream rows are skipped, bounded -----------------


def test_single_invalid_row_is_skipped_not_whole_catalog():
    # Real upstream case (2026-11-10): one station with 79 comma-separated tags.
    bad = {**ROW, "name": "Too many tags", "tags": ",".join(["t"] * 79)}
    raw = json.dumps([ROW, bad, {**ROW, "name": "Second"}]).encode()
    rows = catalog.validate_rows(
        json.loads(catalog.encode_catalog(raw, "json"))["rows"]
    )
    assert [r["name"] for r in rows] == ["Test Radio", "Second"]


def test_skipping_is_bounded_and_mostly_invalid_catalogs_fail(monkeypatch):
    monkeypatch.setattr(catalog, "MAX_SKIPPED_ROWS", 2)
    bad = {**ROW, "votes": -1}
    ok = json.dumps([ROW] * 5 + [bad] * 2).encode()
    assert len(json.loads(catalog.encode_catalog(ok, "json"))["rows"]) == 5
    too_many = json.dumps([ROW] * 5 + [bad] * 3).encode()
    with pytest.raises(ValueError, match="Too many"):
        catalog.encode_catalog(too_many, "json")
    monkeypatch.setattr(catalog, "MAX_SKIPPED_ROWS", 100)
    mostly_bad = json.dumps([ROW] + [bad] * 2).encode()
    with pytest.raises(ValueError, match="Mostly invalid"):
        catalog.encode_catalog(mostly_bad, "json")


def test_xml_rows_are_skipped_the_same_way():
    raw = (
        b"<directory>"
        b"<entry><server_name>Ok</server_name><listen_url>https://e.com/a</listen_url></entry>"
        b"<entry><server_name>Bad</server_name><bitrate>-5</bitrate></entry>"
        b"<entry><server_name>Ok2</server_name><listen_url>https://e.com/b</listen_url></entry>"
        b"</directory>"
    )
    rows = json.loads(catalog.encode_catalog(raw, "xml"))["rows"]
    assert [r["name"] for r in rows] == ["Ok", "Ok2"]


def test_skipped_rows_never_reach_the_parent_reply():
    bad = {**ROW, "name": "X" * 513}
    reply = catalog.encode_catalog(json.dumps([ROW, bad]).encode(), "json")
    assert b"XXXX" not in reply
    assert set(json.loads(reply)) == {"rows"}  # parent contract unchanged
