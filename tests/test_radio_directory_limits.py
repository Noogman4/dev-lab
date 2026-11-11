"""Pure directory-parser budgets; transport tests use the protected radio_fetch."""

import json

import pytest

from netmon.core import radio_directory as directory


def test_normal_json_fields_are_preserved():
    rows = [{"name": "Radio", "url": "https://example.com/live"}]
    assert directory.parse_directory_json(json.dumps(rows)) == rows


def test_normal_xml_fields_are_preserved():
    root = directory.parse_directory_xml(
        "<directory><entry><server_name>Radio</server_name>"
        "<listen_url>https://example.com/live</listen_url></entry></directory>"
    )
    assert root.findtext("entry/server_name") == "Radio"
    assert root.findtext("entry/listen_url") == "https://example.com/live"


def test_json_nesting_rejected_before_decoder(monkeypatch):
    text = "[" * (directory.MAX_DEPTH + 1) + "]" * (directory.MAX_DEPTH + 1)

    def forbidden(*args):
        pytest.fail("JSON decoder must not receive excessively nested input")

    monkeypatch.setattr(directory.json, "loads", forbidden)
    with pytest.raises(ValueError, match="verschachtelt"):
        directory.parse_directory_json(text)


def test_json_strings_do_not_count_as_structure():
    value = ["[{:," * 100, 'a"b\\c', {"nested": [1]}]
    assert directory.parse_directory_json(json.dumps(value)) == value


@pytest.mark.parametrize("kind", ["json", "xml"])
def test_parser_item_budget(kind, monkeypatch):
    monkeypatch.setattr(directory, "MAX_ITEMS", 3)
    parse, text = (
        (directory.parse_directory_json, "[1,2,3,4]")
        if kind == "json"
        else (directory.parse_directory_xml, "<d><e/><e/><e/></d>")
    )
    with pytest.raises(ValueError):
        parse(text)


def test_xml_nesting_rejected():
    text = "<d>" * (directory.MAX_DEPTH + 1) + "</d>" * (directory.MAX_DEPTH + 1)
    with pytest.raises(ValueError, match="Strukturlimit"):
        directory.parse_directory_xml(text)


def test_xml_entity_declarations_rejected():
    with pytest.raises(ValueError, match="DTD"):
        directory.parse_directory_xml('<!DOCTYPE d [<!ENTITY x "expanded">]><d>&x;</d>')


@pytest.mark.parametrize("kind", ["json", "xml"])
def test_parser_budget_counts_utf8_bytes(kind, monkeypatch):
    monkeypatch.setattr(directory, "MAX_RESPONSE_BYTES", 128)
    if kind == "json":
        parse = directory.parse_directory_json
        text = json.dumps("ÿ" * 63, ensure_ascii=False)
        overflow = json.dumps("ÿ" * 64, ensure_ascii=False)
    else:
        parse = directory.parse_directory_xml
        text = "<d>" + "ÿ" * 60 + "x</d>"
        overflow = "<d>" + "ÿ" * 61 + "</d>"
    assert len(text.encode("utf-8")) == 128
    parse(text)
    with pytest.raises(ValueError, match="Größenlimit"):
        parse(overflow)
