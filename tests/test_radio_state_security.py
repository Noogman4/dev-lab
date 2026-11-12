"""Radio state and handover regression tests; no playback or network access."""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from netmon.core import state
from netmon.core import private_state
from netmon.core import private_logs
from netmon import netmon_radio_core as radio


STATE_NAMES = (
    "radio_host_state.json",
    "radio_attach_request.json",
    "radio_standalone_attach_request.json",
    "radio_standalone_show_request.json",
    "radio_detached_state.json",
    "radio_handover_request.json",
    "radio_handover_ack.json",
    "netmon_host_state.json",
)


@pytest.fixture
def paths(monkeypatch, tmp_path):
    for name in ("config", "state", "documents"):
        (tmp_path / name).mkdir(mode=0o700)
    monkeypatch.setattr(
        radio, "get_netmon_config_dir", lambda: str(tmp_path / "config")
    )
    monkeypatch.setattr(radio, "get_netmon_state_dir", lambda: str(tmp_path / "state"))
    monkeypatch.setattr(
        radio, "get_netmon_documents_dir", lambda: str(tmp_path / "documents")
    )
    return radio.build_radio_paths()


@pytest.mark.parametrize("mode", [0o775, 0o777])
def test_unsafe_xdg_ancestor_is_not_returned(monkeypatch, tmp_path, mode):
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o777)
    shared.chmod(mode)
    monkeypatch.setenv("XDG_STATE_HOME", str(shared))
    with pytest.raises(PermissionError):
        state.get_netmon_state_dir()
    assert shared.stat().st_mode & 0o777 == mode


def test_foreign_owned_xdg_ancestor_is_rejected(monkeypatch, tmp_path):
    base = tmp_path / "foreign"
    base.mkdir(mode=0o700)
    identity = base.stat()
    real_fstat = os.fstat

    def foreign_owner(fd):
        info = real_fstat(fd)
        if (info.st_dev, info.st_ino) == (identity.st_dev, identity.st_ino):
            fields = list(info)
            fields[4] = os.geteuid() + 10000
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(private_logs.os, "fstat", foreign_owner)
    monkeypatch.setenv("XDG_STATE_HOME", str(base))
    with pytest.raises(PermissionError):
        state.get_netmon_state_dir()
    assert not (base / "netmon").exists()


def test_foreign_owned_state_file_is_rejected(monkeypatch, tmp_path):
    path = tmp_path / "radio_host_state.json"
    assert radio._safe_write_json(str(path), {"pid": 123})
    before = path.read_bytes()
    real_stat = os.stat

    def foreign_owner(name, *args, **kwargs):
        info = real_stat(name, *args, **kwargs)
        if name == path.name:
            fields = list(info)
            fields[4] = os.geteuid() + 10000
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(private_state.os, "stat", foreign_owner)
    assert radio._safe_read_json(str(path)) == {}
    assert not radio._safe_write_json(str(path), {"pid": 456})
    assert not radio._safe_remove_state(str(path))
    assert path.read_bytes() == before


@pytest.mark.parametrize("name", STATE_NAMES)
def test_radio_access_does_not_follow_or_remove_symlinks(tmp_path, name):
    directory = tmp_path / "private-state"
    directory.mkdir(mode=0o700)
    victim = tmp_path / "victim"
    victim.write_bytes(b"must remain unchanged")
    path = directory / name
    path.symlink_to(victim)
    assert radio._safe_write_json(str(path), {"pid": 123}) is False
    assert radio._safe_read_json(str(path)) == {}
    assert radio._safe_remove_state(str(path)) is False
    assert victim.read_bytes() == b"must remain unchanged"
    assert path.is_symlink()


@pytest.mark.parametrize("kind", ["hardlink", "fifo", "directory", "writable"])
def test_unsafe_state_entries_are_rejected(tmp_path, kind):
    path = tmp_path / "radio_host_state.json"
    victim = tmp_path / "victim"
    victim.write_bytes(b'{"pid": 123}')
    if kind == "hardlink":
        os.link(victim, path)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.write_text('{"pid": 123}')
        path.chmod(0o666)
    assert not radio._safe_write_json(str(path), {"pid": 456})
    assert radio._safe_read_json(str(path)) == {}
    assert not radio._safe_remove_state(str(path))
    assert victim.read_bytes() == b'{"pid": 123}'


def test_state_directory_symlink_is_rejected(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.setenv("XDG_STATE_HOME", str(link))
    with pytest.raises(OSError):
        state.get_netmon_state_dir()
    assert not radio._safe_write_json(str(link / "radio_host_state.json"), {"pid": 1})
    assert list(target.iterdir()) == []


def test_oversized_state_is_rejected_before_json_parsing(tmp_path, monkeypatch):
    path = tmp_path / "radio_handover_request.json"
    path.write_bytes(b" " * (private_state.MAX_STATE_BYTES + 1))
    path.chmod(0o600)

    def unexpected_parse(_content):
        pytest.fail("Oversized state reached the JSON parser")

    monkeypatch.setattr(private_state.json, "loads", unexpected_parse)
    assert radio._safe_read_json(str(path)) == {}
    assert radio._consume_radio_payload(str(path), target_mode="standalone") is None


def test_oversized_write_preserves_existing_state(tmp_path):
    path = tmp_path / "radio_host_state.json"
    assert radio._safe_write_json(str(path), {"pid": 123})
    before = path.read_bytes()
    assert not radio._safe_write_json(
        str(path), {"oversized": "x" * private_state.MAX_STATE_BYTES}
    )
    assert path.read_bytes() == before


def test_failed_atomic_publication_preserves_old_state(tmp_path, monkeypatch):
    path = tmp_path / "radio_host_state.json"
    assert radio._safe_write_json(str(path), {"pid": 123})

    def fail_replace(*_args, **_kwargs):
        raise OSError("simulated publication failure")

    monkeypatch.setattr(private_state.os, "replace", fail_replace)
    assert not radio._safe_write_json(str(path), {"pid": 456})
    assert radio._safe_read_json(str(path)) == {"pid": 123}
    assert not list(tmp_path.glob(".netmon-state-*.tmp"))


def test_valid_handover_is_private_and_consumed_once(paths):
    assert radio.request_radio_handover(
        target_mode="standalone", payload={"was_playing": True}, transition_id="current"
    )
    key = Path(paths.state_dir) / "radio_ipc.key"
    assert key.stat().st_mode & 0o777 == 0o600
    assert len(key.read_bytes()) == 32
    request = Path(paths.radio_handover_request_path)
    assert request.stat().st_mode & 0o777 == 0o600
    assert radio.consume_radio_handover("embedded", transition_id="current") is None
    assert radio.consume_radio_handover("standalone", transition_id="old") is None
    assert radio.consume_radio_handover("standalone", transition_id="current") == {
        "was_playing": True
    }
    assert radio.consume_radio_handover("standalone") is None


@pytest.mark.parametrize("elapsed", [121, -6])
def test_signed_stale_or_future_handover_is_rejected(paths, monkeypatch, elapsed):
    monkeypatch.setattr(radio.time, "time", lambda: 1000)
    assert radio.request_radio_handover(
        target_mode="standalone", payload={"was_playing": True}
    )
    monkeypatch.setattr(radio.time, "time", lambda: 1000 + elapsed)
    assert radio.consume_radio_handover("standalone") is None
    assert Path(paths.radio_handover_request_path).exists()


@pytest.mark.parametrize(
    "change",
    [
        {"payload": {"was_playing": True, "current_station_id": "forged"}},
        {"target_mode": "embedded"},
        {"transition_id": "forged"},
        {"requested_at": True},
        {"ipc_version": True},
        {"nonce": "f" * 32},
        {"auth": "0" * 64},
        {"auth": "non-ascii-ä"},
    ],
)
def test_modified_handover_is_not_consumed(paths, change):
    assert radio.request_radio_handover(
        target_mode="standalone", payload={"was_playing": False}
    )
    path = paths.radio_handover_request_path
    message = radio._safe_read_json(path)
    message.update(change)
    assert radio._safe_write_json(path, message)
    assert radio.consume_radio_handover(message["target_mode"]) is None
    assert Path(path).exists()


def test_unsigned_handover_is_not_consumed(paths):
    assert radio._safe_write_json(
        paths.radio_handover_request_path,
        {"target_mode": "standalone", "payload": {"was_playing": True}},
    )
    assert radio.consume_radio_handover("standalone") is None


def test_request_cannot_be_substituted_as_acknowledgement(paths):
    assert radio.request_radio_handover(
        target_mode="standalone", payload={"was_playing": True}
    )
    assert radio._safe_write_json(
        paths.radio_handover_ack_path,
        radio._safe_read_json(paths.radio_handover_request_path),
    )
    assert radio.consume_radio_handover_ack("standalone") is None
    assert radio.consume_radio_handover("standalone") == {"was_playing": True}


@pytest.mark.parametrize("entry", ["radio_ipc.key", ".radio_ipc.key.lock"])
def test_symlinked_authentication_key_or_lock_is_rejected(paths, tmp_path, entry):
    victim = tmp_path / "victim"
    victim.write_bytes(b"original")
    path = Path(paths.state_dir) / entry
    path.symlink_to(victim)
    assert not radio.request_standalone_radio_show()
    assert victim.read_bytes() == b"original"
    assert path.is_symlink()


def test_host_registration_refuses_symlinked_lock(paths, tmp_path, monkeypatch):
    victim = tmp_path / "victim"
    victim.write_bytes(b"original")
    lock = Path(paths.netmon_host_state_path + ".lock")
    lock.symlink_to(victim)
    monkeypatch.setattr(radio, "_process_identity", lambda _pid: ("boot", 1))
    assert not radio.write_netmon_host_state(123)
    assert not radio.clear_netmon_host_state()
    assert victim.read_bytes() == b"original"
    assert lock.is_symlink()


def test_concurrent_consumers_cannot_accept_same_handover_twice(paths):
    assert radio.request_radio_handover(
        target_mode="standalone", payload={"was_playing": True}
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _: radio.consume_radio_handover("standalone"), range(2))
        )
    assert results.count({"was_playing": True}) == 1
    assert results.count(None) == 1
