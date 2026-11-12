"""Untrusted checksum names cannot open anything outside explicit selections."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_netmon_download.sh"


@pytest.fixture
def helper():
    source = SCRIPT.read_text().split("<<'PYTHON'\n", 1)[1].rsplit("\nPYTHON", 1)[0]
    module = types.ModuleType("netmon_hash_helper_test")
    exec(compile(source, str(SCRIPT), "exec"), module.__dict__)
    return module


@pytest.fixture
def payload(tmp_path):
    file = tmp_path / "netmon_1.1.21_all.deb"
    file.write_bytes(b"synthetic package, never installed")
    return file


def entry(path, name=None, *, marker=" "):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest()
        + " "
        + marker
        + (name or path.name)
        + "\n"
    )


def manifest(tmp_path, content):
    target = tmp_path / "SHA256SUMS"
    target.write_bytes(content.encode() if isinstance(content, str) else content)
    return target


def cli(sums, *paths, env=None):
    return subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), str(sums), *map(str, paths)],
        capture_output=True,
        text=True,
        timeout=4,
        env=env,
    )


@pytest.mark.parametrize("marker", [" ", "*"])
@pytest.mark.parametrize("final_newline", [False, True])
def test_regular_file_and_document_members_work_in_standalone_script(
    tmp_path, payload, marker, final_newline
):
    docs = tmp_path / "dist" / "docs"
    docs.mkdir(parents=True)
    document = docs / "netmon_dokumentation_1.1.21.pdf"
    document.write_bytes(b"synthetic document")
    html = docs / "netmon_dokumentation_1.1.21.html"
    html.write_bytes(b"synthetic html")
    content = (
        entry(payload, marker=marker)
        + entry(document, "docs/" + document.name, marker=marker)
        + entry(html, "docs/" + html.name, marker=marker)
    )
    sums = manifest(tmp_path, content if final_newline else content.rstrip("\n"))
    result = cli(sums, payload, document, html)
    assert result.returncode == 0, result.stderr
    assert result.stdout.count(": OK") == 3
    assert "Herkunft erfordert" in result.stdout
    assert not list(tmp_path.glob(".netmon*"))


@pytest.mark.parametrize(
    "name",
    [
        "/outside",
        "../outside",
        "docs/../../outside",
        "./safe",
        "docs/../safe",
        "a/b",
        "docs/a/b",
        "docs//safe",
        "docs/./safe",
        "docs/",
        ".",
        "..",
        "-",
        "--help",
        "\\outside",
        "a\\b",
        "\\x2foutside",
        "name\tfile",
        "name\rfile",
        "name\x00file",
        "name\x1bfile",
        "name\x7ffile",
        "é.deb",
        "docs/--option",
        "/dev/zero",
        "docs",
        "SHA256SUMS",
    ],
)
def test_malicious_member_names_never_open_any_payload(
    helper, tmp_path, payload, monkeypatch, name
):
    sums = manifest(tmp_path, entry(payload, name))
    opened = []
    original = helper.regular_file

    @contextmanager
    def observe(path):
        opened.append(str(path))
        with original(path) as value:
            yield value

    monkeypatch.setattr(helper, "regular_file", observe)
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), str(payload)])
    assert opened == [str(sums)]


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"\n",
        b"invalid\n",
        b"0" * 63 + b"  safe\n",
        b"g" * 64 + b"  safe\n",
        b"0" * 64 + b" safe\n",
        b"0" * 64 + b"  safe\n\n",
        b"\\" + b"0" * 64 + b"  safe\n",
        b"0" * 64 + b"  safe\r\n",
        b"0" * 64 + b"  \xff\n",
    ],
)
def test_malformed_manifest_rejected_before_payload_open(
    helper, tmp_path, payload, monkeypatch, content
):
    sums = manifest(tmp_path, content)
    original = helper.regular_file

    @contextmanager
    def observe(path):
        assert path == str(sums)
        with original(path) as value:
            yield value

    monkeypatch.setattr(helper, "regular_file", observe)
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), str(payload)])


@pytest.mark.parametrize(
    "change", ["duplicate", "missing", "extra", "duplicate-selection"]
)
def test_manifest_membership_must_match_exactly(
    helper, tmp_path, payload, monkeypatch, change
):
    content = entry(payload)
    arguments = [str(payload)]
    if change == "duplicate":
        content += entry(payload)
    elif change == "extra":
        content += entry(payload, "other.deb")
    elif change == "missing":
        arguments.append(str(tmp_path / "not-selected-in-manifest"))
    else:
        arguments.append(str(tmp_path / "other-folder" / payload.name))
    sums = manifest(tmp_path, content)
    original = helper.regular_file

    @contextmanager
    def observe(path):
        assert path == str(sums)
        with original(path) as value:
            yield value

    monkeypatch.setattr(helper, "regular_file", observe)
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), *arguments])


@pytest.mark.parametrize("target", ["manifest", "payload"])
@pytest.mark.parametrize(
    "attack", ["symlink", "parent-symlink", "fifo", "directory", "hardlink"]
)
def test_unsafe_file_types_fail_without_hanging(tmp_path, payload, target, attack):
    sums = manifest(tmp_path, entry(payload))
    original = sums if target == "manifest" else payload
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(original.read_bytes())
    if attack == "parent-symlink":
        folder = tmp_path / "linked"
        folder.symlink_to(tmp_path, target_is_directory=True)
        selected = folder / original.name
    else:
        original.unlink()
        selected = original
        if attack == "symlink":
            selected.symlink_to(sentinel)
        elif attack == "fifo":
            os.mkfifo(selected)
        elif attack == "directory":
            selected.mkdir()
        else:
            os.link(sentinel, selected)
    result = cli(
        selected if target == "manifest" else sums,
        selected if target == "payload" else payload,
    )
    assert result.returncode != 0 and ": OK" not in result.stdout
    assert sentinel.read_bytes()


@pytest.mark.parametrize("kind", ["manifest", "file", "total", "count"])
def test_read_budgets_reject_before_large_work(
    helper, tmp_path, payload, monkeypatch, kind
):
    sums = manifest(tmp_path, entry(payload))
    monkeypatch.setattr(
        helper,
        {
            "manifest": "MAX_MANIFEST_BYTES",
            "file": "MAX_FILE_BYTES",
            "total": "MAX_TOTAL_BYTES",
            "count": "MAX_FILES",
        }[kind],
        1 if kind != "count" else 0,
    )
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), str(payload)])


@pytest.mark.parametrize("mutation", ["replace", "grow", "shrink"])
@pytest.mark.parametrize("target", ["manifest", "payload"])
def test_changed_files_cannot_report_success(
    helper, tmp_path, payload, monkeypatch, capsys, mutation, target
):
    sums = manifest(tmp_path, entry(payload))
    selected = sums if target == "manifest" else payload
    inode = selected.stat().st_ino
    original = helper.os.read
    mutated = False

    def read(fd, size):
        nonlocal mutated
        content = original(fd, size)
        if not mutated and os.fstat(fd).st_ino == inode:
            mutated = True
            if mutation == "replace":
                replacement = tmp_path / "replacement"
                replacement.write_bytes(selected.read_bytes())
                os.replace(replacement, selected)
            elif mutation == "grow":
                with selected.open("ab") as output:
                    output.write(b"extra")
            else:
                selected.write_bytes(b"")
        return content

    monkeypatch.setattr(helper.os, "read", read)
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), str(payload)])
    assert ": OK" not in capsys.readouterr().out


def test_full_manifest_is_checked_before_payload_open_even_if_first_entry_valid(
    helper, tmp_path, payload, monkeypatch
):
    sums = manifest(tmp_path, entry(payload) + entry(payload, "../outside"))
    original = helper.regular_file

    @contextmanager
    def observe(path):
        assert str(path) == str(sums)
        with original(path) as value:
            yield value

    monkeypatch.setattr(helper, "regular_file", observe)
    with pytest.raises(helper.VerificationError):
        helper.verify([str(sums), str(payload)])


def test_mismatch_does_not_print_partial_success(tmp_path, payload):
    second = tmp_path / "second.deb"
    second.write_bytes(b"different")
    sums = manifest(tmp_path, entry(payload) + "0" * 64 + "  second.deb\n")
    result = cli(sums, payload, second)
    assert result.returncode == 1 and ": OK" not in result.stdout


def test_helper_is_self_contained_and_never_calls_external_checker(tmp_path, payload):
    copy = tmp_path / "published-verifier.sh"
    shutil.copyfile(SCRIPT, copy)
    marker = tmp_path / "checker-was-called"
    fake = tmp_path / "sha256sum"
    fake.write_text('#!/bin/sh\necho called > "' + str(marker) + '"\n')
    fake.chmod(0o755)
    sums = manifest(tmp_path, entry(payload))
    result = subprocess.run(
        ["/usr/bin/bash", str(copy), str(sums), str(payload)],
        env={"PATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=4,
    )
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_empty_payload_and_uppercase_hash_are_valid(tmp_path):
    payload = tmp_path / "empty.deb"
    payload.write_bytes(b"")
    sums = manifest(tmp_path, entry(payload).upper().replace("EMPTY.DEB", "empty.deb"))
    assert cli(sums, payload).returncode == 0


def test_duplicate_basename_in_different_directories_is_rejected(tmp_path, payload):
    other = tmp_path / "other" / payload.name
    other.parent.mkdir()
    other.write_bytes(payload.read_bytes())
    sums = manifest(tmp_path, entry(payload))
    assert cli(sums, payload, other).returncode != 0


def test_explicit_payload_parent_exchange_cannot_redirect_descriptor(
    helper, tmp_path, monkeypatch
):
    folder = tmp_path / "files"
    folder.mkdir()
    payload = folder / "package.deb"
    payload.write_bytes(b"checked original")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / payload.name).write_bytes(b"must not be read")
    sums = manifest(tmp_path, entry(payload))
    original = helper.os.read
    inode = payload.stat().st_ino
    replaced = False

    def read(fd, size):
        nonlocal replaced
        if os.fstat(fd).st_ino == inode and not replaced:
            replaced = True
            folder.rename(tmp_path / "held-folder")
            folder.symlink_to(outside, target_is_directory=True)
        return original(fd, size)

    monkeypatch.setattr(helper.os, "read", read)
    helper.verify([str(sums), str(payload)])
    assert (outside / payload.name).read_bytes() == b"must not be read"
