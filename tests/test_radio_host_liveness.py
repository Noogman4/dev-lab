"""Independent host liveness must survive radio ownership and process reuse."""

import io
from pathlib import Path
import threading

import pytest

from netmon import netmon_radio_core as core


@pytest.fixture
def states(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "get_netmon_config_dir", lambda: str(tmp_path / "config"))
    monkeypatch.setattr(core, "get_netmon_state_dir", lambda: str(tmp_path / "state"))
    monkeypatch.setattr(
        core, "get_netmon_documents_dir", lambda: str(tmp_path / "documents")
    )
    identities = {101: ("boot-a", 1000), 202: ("boot-a", 2000)}
    monkeypatch.setattr(core, "_process_identity", identities.get)
    monkeypatch.setattr(core, "_process_exists", lambda pid: pid in identities)
    return core.build_radio_paths(), identities


def test_standalone_owner_and_legacy_radio_state_are_not_a_netmon_host(states):
    paths, _identities = states
    assert core.write_radio_host_state(mode="standalone", owner_pid=202)
    assert core.standalone_radio_is_running()
    assert not core.netmon_host_is_available()
    # No migration of ambiguous old owner records into host authority.
    assert not Path(paths.netmon_host_state_path).exists()


def test_register_and_unregister_host_preserve_running_standalone(states):
    paths, _identities = states
    assert core.write_radio_host_state(mode="standalone", owner_pid=202)
    before = Path(paths.radio_host_state_path).read_bytes()
    assert core.write_netmon_host_state(101)
    assert core.netmon_host_is_available()
    assert Path(paths.radio_host_state_path).read_bytes() == before
    assert not core.clear_netmon_host_state(202)
    assert core.clear_netmon_host_state(101)
    assert not core.netmon_host_is_available()
    assert core.standalone_radio_is_running()
    assert Path(paths.radio_host_state_path).read_bytes() == before


def test_radio_cleanup_does_not_unregister_live_netmon(states):
    paths, _identities = states
    assert core.write_netmon_host_state(101)
    before = Path(paths.netmon_host_state_path).read_bytes()
    assert core.write_radio_host_state(mode="standalone", owner_pid=202)
    assert not core.clear_radio_host_state(101)
    assert core.clear_radio_host_state(202)
    assert core.netmon_host_is_available()
    assert Path(paths.netmon_host_state_path).read_bytes() == before


@pytest.mark.parametrize(
    "current", [None, ("boot-a", 1001), ("boot-b", 1000), ("boot-a", 1000)]
)
def test_dead_reused_or_rebooted_process_does_not_revive_host(states, current):
    _paths, identities = states
    assert core.write_netmon_host_state(101)
    if current is None:
        del identities[101]
    else:
        identities[101] = current
    assert core.netmon_host_is_available() is (current == ("boot-a", 1000))


def test_late_old_cleanup_preserves_new_registration(states):
    _paths, _identities = states
    assert core.write_netmon_host_state(101)
    assert core.write_netmon_host_state(202)
    assert not core.clear_netmon_host_state(101)
    assert core.netmon_host_is_available()
    assert core.read_netmon_host_state()["pid"] == 202


def test_reused_pid_cannot_clear_older_generation(states):
    _paths, identities = states
    assert core.write_netmon_host_state(101)
    identities[101] = ("boot-a", 9999)
    assert not core.clear_netmon_host_state(101)
    assert not core.netmon_host_is_available()


def test_host_restart_cannot_be_erased_by_concurrent_old_cleanup(states, monkeypatch):
    paths, _identities = states
    assert core.write_netmon_host_state(101)
    read_started = threading.Event()
    allow_cleanup = threading.Event()
    writer_started = threading.Event()
    writer_finished = threading.Event()
    results = {}
    original_read = core._safe_read_json

    def pause_old_read(path):
        state = original_read(path)
        if (
            path == paths.netmon_host_state_path
            and threading.current_thread().name == "old-host"
        ):
            read_started.set()
            assert allow_cleanup.wait(timeout=3)
        return state

    def new_host():
        writer_started.set()
        results["write"] = core.write_netmon_host_state(202)
        writer_finished.set()

    monkeypatch.setattr(core, "_safe_read_json", pause_old_read)
    old = threading.Thread(
        target=lambda: results.update(clear=core.clear_netmon_host_state(101)),
        name="old-host",
        daemon=True,
    )
    new = threading.Thread(target=new_host, daemon=True)
    old.start()
    try:
        assert read_started.wait(timeout=2)
        new.start()
        assert writer_started.wait(timeout=2)
        assert not writer_finished.wait(timeout=0.1)
    finally:
        allow_cleanup.set()
        old.join(timeout=3)
        if new.ident is not None:
            new.join(timeout=3)
    assert results == {"clear": True, "write": True}
    assert core.netmon_host_is_available()
    assert core.read_netmon_host_state()["pid"] == 202


@pytest.mark.parametrize(
    "contents",
    ["{broken", '{"pid":101}', '{"role":"netmon","schema_version":true,"pid":101}'],
)
def test_incomplete_host_marker_is_not_available(states, contents):
    paths, _identities = states
    Path(paths.netmon_host_state_path).write_text(contents)
    assert not core.netmon_host_is_available()


@pytest.mark.parametrize("process_state", ["S", "Z", "X"])
def test_identity_parses_comm_parentheses_and_excludes_zombies(
    monkeypatch, process_state
):
    # 19 fields from field 3 (state) to the field before starttime (22).
    stat_text = (
        "101 (radio ) test name) "
        + process_state
        + " "
        + " ".join(["0"] * 18)
        + " 9876 0\n"
    )

    def read_proc(path, *_args, **_kwargs):
        if path == "/proc/101/stat":
            return io.StringIO(stat_text)
        if path == "/proc/sys/kernel/random/boot_id":
            return io.StringIO("boot-a\n")
        raise AssertionError(path)

    monkeypatch.setattr(core, "open", read_proc, raising=False)
    assert core._process_identity(101) == (
        ("boot-a", 9876) if process_state == "S" else None
    )


def _write_legacy_standalone_state(paths, pid):
    import json

    Path(paths.radio_host_state_path).parent.mkdir(parents=True, exist_ok=True)
    Path(paths.radio_host_state_path).write_text(
        json.dumps(
            {"pid": pid, "owner_pid": pid, "launcher_state": "standalone_active"}
        )
    )
    Path(paths.radio_host_state_path).chmod(0o600)


@pytest.mark.parametrize("is_netmon", [False, True])
def test_legacy_state_without_identity_needs_a_netmon_process(
    states, monkeypatch, is_netmon
):
    # A state from before the reboot: the PID now belongs to anything else.
    paths, _identities = states
    _write_legacy_standalone_state(paths, 202)
    monkeypatch.setattr(core, "_is_netmon_process_leader", lambda pid: is_netmon)
    assert core.standalone_radio_is_running() is is_netmon
    assert core.radio_host_is_running() is is_netmon


def test_reused_pid_with_other_identity_is_not_running(states):
    paths, identities = states
    assert core.write_radio_host_state(mode="standalone", owner_pid=202)
    assert core.standalone_radio_is_running()
    identities[202] = ("boot-b", 2000)  # same PID after a reboot
    assert not core.standalone_radio_is_running()
    identities[202] = ("boot-a", 2001)  # same boot, PID reused later
    assert not core.standalone_radio_is_running()


def test_identity_is_recomputed_and_not_taken_from_extras(states):
    import json

    paths, _identities = states
    assert core.write_radio_launcher_state(
        launcher_state="standalone_active",
        owner_pid=202,
        extras={"boot_id": "forged", "start_ticks": 1},
    )
    state = json.loads(Path(paths.radio_host_state_path).read_text())
    assert (state["boot_id"], state["start_ticks"]) == ("boot-a", 2000)
    assert core.standalone_radio_is_running()


def test_thread_id_is_not_a_process_leader():
    ready, release = threading.Event(), threading.Event()
    ids = []

    def worker():
        ids.append(threading.get_native_id())
        ready.set()
        release.wait(5)

    thread = threading.Thread(target=worker)
    thread.start()
    try:
        assert ready.wait(5)
        assert ids[0] != __import__("os").getpid()
        assert not core._is_netmon_process_leader(ids[0])
    finally:
        release.set()
        thread.join(5)


def test_detached_only_while_the_standalone_owner_lives(states):
    _paths, identities = states
    assert core.write_radio_host_state(mode="standalone", owner_pid=202)
    assert core.radio_is_detached()
    identities[202] = ("boot-b", 2000)  # owner gone, PID reused after reboot
    assert not core.radio_is_detached()
    del identities[202]  # owner gone entirely
    assert not core.radio_is_detached()


def test_attaching_needs_a_live_owner_and_embedded_is_never_detached(states):
    _paths, identities = states
    assert core.write_radio_launcher_state(launcher_state="attaching", owner_pid=202)
    assert core.radio_is_detached()
    del identities[202]
    assert not core.radio_is_detached()
    assert core.write_radio_host_state(mode="embedded", owner_pid=101)
    assert not core.radio_is_detached()


@pytest.mark.parametrize("is_netmon", [False, True])
def test_legacy_detached_state_needs_a_netmon_process(states, monkeypatch, is_netmon):
    paths, _identities = states
    _write_legacy_standalone_state(paths, 202)
    monkeypatch.setattr(core, "_is_netmon_process_leader", lambda pid: is_netmon)
    assert core.radio_is_detached() is is_netmon
