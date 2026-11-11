"""Protected FIFO radio output (H1); no PipeWire, host config or network."""

import errno
import fcntl
import json
import os
from pathlib import Path
import stat

import pytest

from netmon.core import radio_fifo_output as out


@pytest.fixture
def p(tmp_path):
    return out.paths(home=tmp_path / "home", config_home=tmp_path / "config")


def prepared(p, *, mode=0o700, fifo=True):
    p.state_dir.mkdir(parents=True, mode=0o700)
    os.chmod(p.state_dir, mode)
    if fifo:
        os.mkfifo(p.fifo, 0o666)
    return p


def reader(p):
    return os.open(p.fifo, os.O_RDONLY | os.O_NONBLOCK)


# -- paths and drop-in -----------------------------------------------------


def test_paths_are_fixed_below_home_and_config(tmp_path, p):
    assert p.state_dir == tmp_path / "home/.local/state/netmon/radio-output"
    assert p.fifo.name == "radio.pcm"
    assert p.dropin == tmp_path / "config/pipewire/pipewire.conf.d" / out.DROPIN_NAME


def test_relative_xdg_config_home_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative")
    q = out.paths(home=tmp_path)
    assert q.config_dir == tmp_path / ".config/pipewire/pipewire.conf.d"


def test_dropin_is_the_tested_h1_form(p):
    text = out.dropin_text(p.fifo)
    assert text.startswith(out.DROPIN_MARKER)
    for line in (
        "tunnel.mode = playback",
        'remote.name = "internal"',
        f'pipe.filename = "{p.fifo}"',
        "audio.rate = 48000",
        "audio.channels = 2",
        f'node.name = "{out.TUNNEL_NODE}"',
        "stream.props = { node.autoconnect = false }",
        "flags = [ nofail ]",
    ):
        assert line in text
    assert "target.object" not in text


@pytest.mark.parametrize("bad", ["relative/radio.pcm", '/x/"a', "/x/a\nb", "/x/a\\b"])
def test_dropin_rejects_unsafe_paths(bad):
    with pytest.raises(out.RadioOutputError):
        out.dropin_text(Path(bad))


# -- install / uninstall ---------------------------------------------------


def test_install_requires_explicit_confirmation(p):
    with pytest.raises(out.RadioOutputError):
        out.install(p, confirmed=False)
    assert not p.dropin.exists() and not p.state_dir.exists()


def test_install_and_uninstall_own_files_only(p):
    out.install(p, confirmed=True)
    assert p.dropin.read_text() == out.dropin_text(p.fifo)
    assert oct(p.state_dir.stat().st_mode & 0o777) == "0o700"
    out.install(p, confirmed=True)  # idempotent
    os.mkfifo(p.fifo)
    out.uninstall(p)
    assert not p.dropin.exists() and not p.state_dir.exists()


def test_install_refuses_foreign_file_and_symlink(p, tmp_path):
    p.config_dir.mkdir(parents=True)
    p.dropin.write_text("context.modules = []\n")
    with pytest.raises(out.RadioOutputError):
        out.install(p, confirmed=True)
    with pytest.raises(out.RadioOutputError):
        out.uninstall(p)
    assert p.dropin.read_text() == "context.modules = []\n"
    p.dropin.unlink()
    p.dropin.symlink_to(tmp_path / "elsewhere.conf")
    with pytest.raises(out.RadioOutputError):
        out.install(p, confirmed=True)
    assert not (tmp_path / "elsewhere.conf").exists()


def test_install_refuses_symlinked_parent(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "home").mkdir()
    (tmp_path / "home/.local").symlink_to(real)
    q = out.paths(home=tmp_path / "home", config_home=tmp_path / "config")
    with pytest.raises(out.RadioOutputError):
        out.install(q, confirmed=True)
    assert not (real / "state").exists()


# -- setup status ----------------------------------------------------------


def version_run(version="1.0.5"):
    def run(argv, timeout):
        assert argv == [str(out.PIPEWIRE), "--version"]
        return (
            0,
            f"pipewire\nCompiled with libpipewire {version}\nLinked with libpipewire {version}\n",
        )

    return run


def test_status_lists_missing_setup(p, tmp_path):
    status = out.setup_status(p, version_run(), roots=())
    assert not status["ready"]
    assert any("nicht eingerichtet" in r for r in status["reasons"])


def test_status_requires_loaded_fifo_and_supported_version(p, monkeypatch):
    monkeypatch.setattr(out, "PW_DUMP", Path("/bin/true"))
    monkeypatch.setattr(out, "PW_LINK", Path("/bin/true"))
    monkeypatch.setattr(out, "PIPEWIRE", Path("/bin/true"))
    out.install(p, confirmed=True)
    status = out.setup_status(p, version_run(), roots=())
    assert status["reasons"] == [
        "PipeWire hat die Ausgabe noch nicht geladen (Audiodienste neu starten)."
    ]
    os.mkfifo(p.fifo)
    assert out.setup_status(p, version_run(), roots=())["ready"] is True
    bad = out.setup_status(p, version_run("1.2.0"), roots=())
    assert not bad["ready"] and "1.2.0" in bad["reasons"][0]


def test_status_detects_socket_access_but_ignores_comments(p, tmp_path, monkeypatch):
    monkeypatch.setattr(out, "PW_DUMP", Path("/bin/true"))
    monkeypatch.setattr(out, "PW_LINK", Path("/bin/true"))
    monkeypatch.setattr(out, "PIPEWIRE", Path("/bin/true"))
    out.install(p, confirmed=True)
    os.mkfifo(p.fifo)
    system = tmp_path / "system"
    system.mkdir()
    (system / "pipewire.conf").write_text(
        "#access.socket = { pipewire-0 = default }\n#access.legacy = true\n"
    )
    assert out.setup_status(p, version_run(), roots=(system,))["ready"]
    (system / "pipewire.conf.d").mkdir()
    (system / "pipewire.conf.d/10-x.conf").write_text(
        "args = { access.legacy = false }\n"
    )
    status = out.setup_status(p, version_run(), roots=(system,))
    assert not status["ready"] and "10-x.conf" in status["reasons"][0]


def test_status_rejects_open_state_directory(p):
    prepared(p, mode=0o755)
    status = out.setup_status(p, version_run(), roots=())
    assert "Privates Ausgabeverzeichnis fehlt oder ist unzulässig." in status["reasons"]


# -- FIFO writer -----------------------------------------------------------


def test_writer_without_reader_fails_closed(p):
    prepared(p)
    with pytest.raises(out.RadioOutputError, match="kein PipeWire-Tunnel"):
        out.FifoWriter(p).open()


def test_writer_missing_fifo_means_not_loaded(p):
    prepared(p, fifo=False)
    with pytest.raises(out.RadioOutputError, match="Audiodienste"):
        out.FifoWriter(p).open()


def test_writer_opens_blocking_private_fifo_and_writes(p):
    prepared(p)
    r = reader(p)
    try:
        with out.FifoWriter(p) as w:
            assert os.get_blocking(w.fd)
            assert oct(os.fstat(w.fd).st_mode & 0o777) == "0o600"
            os.write(w.fd, b"\x01\x00\x02\x00")
            assert os.read(r, 16) == b"\x01\x00\x02\x00"
            assert fcntl.fcntl(w.fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC
    finally:
        os.close(r)


def test_writer_is_exclusive_between_instances(p):
    prepared(p)
    r = reader(p)
    try:
        with out.FifoWriter(p):
            with pytest.raises(out.RadioOutputError, match="bereits"):
                out.FifoWriter(p).open()
        with out.FifoWriter(p):
            pass
    finally:
        os.close(r)


@pytest.mark.parametrize("failure", ["flock", "fstat", "fchmod", "set_blocking"])
def test_writer_open_failure_closes_descriptors_and_releases_lock(
    p, monkeypatch, failure
):
    prepared(p)
    r = reader(p)
    writer = out.FifoWriter(p)
    opened = []
    real_open, real_fstat = os.open, os.fstat
    error = OSError(errno.EIO, "injected writer setup failure")

    def track_open(*args, **kwargs):
        fd = real_open(*args, **kwargs)
        opened.append(fd)
        return fd

    def fail(*args, **kwargs):
        raise error

    def fail_fifo_stat(fd):
        info = real_fstat(fd)
        if stat.S_ISFIFO(info.st_mode):
            raise error
        return info

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", track_open)
            if failure == "flock":
                patch.setattr(fcntl, "flock", fail)
            elif failure == "fstat":
                patch.setattr(os, "fstat", fail_fifo_stat)
            else:
                patch.setattr(os, failure, fail)
            with pytest.raises(OSError) as caught:
                writer.open()
            assert caught.value is error

        assert len(opened) == (2 if failure == "flock" else 3)
        for fd in opened:
            with pytest.raises(OSError) as closed:
                real_fstat(fd)
            assert closed.value.errno == errno.EBADF
        assert writer.fd is None and writer._lock is None
        writer.close()

        # The same instance must be able to acquire the lock and write again.
        writer.open()
        os.write(writer.fd, b"\x01\x00\x02\x00")
        assert os.read(r, 16) == b"\x01\x00\x02\x00"
        writer.close()
    finally:
        writer.close()
        # Also clean up the old implementation's leaked descriptors in a red run.
        for fd in opened:
            try:
                os.close(fd)
            except OSError as exc:
                if exc.errno != errno.EBADF:
                    raise
        os.close(r)


def test_close_descriptor_keeps_lock(p):
    prepared(p)
    r = reader(p)
    try:
        w = out.FifoWriter(p)
        w.open()
        w.close_descriptor()
        assert w.fd is None
        with pytest.raises(out.RadioOutputError, match="bereits"):
            out.FifoWriter(p).open()
        w.close()
    finally:
        os.close(r)


@pytest.mark.parametrize("case", ["symlink", "regular", "hardlink", "open-dir"])
def test_writer_rejects_unsafe_targets(p, tmp_path, case):
    prepared(p, fifo=case not in ("symlink", "regular"))
    keep = None
    if case == "symlink":
        other = tmp_path / "other.fifo"
        os.mkfifo(other)
        keep = os.open(other, os.O_RDONLY | os.O_NONBLOCK)
        p.fifo.symlink_to(other)
    elif case == "regular":
        p.fifo.write_bytes(b"")
    elif case == "hardlink":
        os.link(p.fifo, p.state_dir / "second")
        keep = reader(p)
    else:
        os.chmod(p.state_dir, 0o755)
        keep = reader(p)
    try:
        with pytest.raises(out.RadioOutputError):
            out.FifoWriter(p).open()
    finally:
        if keep is not None:
            os.close(keep)


def test_writer_rejects_symlinked_state_directory(p, tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    os.mkfifo(real / out.FIFO_NAME)
    p.state_dir.parent.mkdir(parents=True)
    p.state_dir.symlink_to(real)
    keep = os.open(real / out.FIFO_NAME, os.O_RDONLY | os.O_NONBLOCK)
    try:
        with pytest.raises(out.RadioOutputError, match="Ausgabeverzeichnis"):
            out.FifoWriter(p).open()
    finally:
        os.close(keep)


# -- graph, links and watchdog ---------------------------------------------


def node(i, name, **props):
    return {
        "id": i,
        "type": "PipeWire:Interface:Node",
        "info": {"props": {"node.name": name, "object.serial": i + 100, **props}},
    }


def port(i, node_id, direction, channel, **props):
    return {
        "id": i,
        "type": "PipeWire:Interface:Port",
        "info": {
            "props": {
                "node.id": node_id,
                "port.direction": direction,
                "audio.channel": channel,
                **props,
            }
        },
    }


def fake_graph(fifo, *, client_remote="internal", extra=()):
    return [
        {
            "id": 21,
            "type": "PipeWire:Interface:Client",
            "info": {
                "props": {
                    "remote.name": client_remote,
                    "application.process.binary": "pipewire",
                }
            },
        },
        node(34, out.TUNNEL_NODE, **{"pipe.filename": str(fifo), "client.id": 21}),
        port(38, 34, "out", "FL"),
        port(39, 34, "out", "FR"),
        node(50, "alsa_output.speaker", **{"media.class": "Audio/Sink"}),
        port(51, 50, "in", "FL"),
        port(52, 50, "in", "FR"),
        port(53, 50, "out", "FL", **{"port.monitor": True}),
        node(60, "other", **{"media.class": "Audio/Sink"}),
        port(61, 60, "in", "FL"),
        port(62, 60, "in", "FR"),
        {
            "id": 70,
            "type": "PipeWire:Interface:Metadata",
            # Real pw-dump 1.0.5 form (top-level props), seen in private runs.
            "props": {"metadata.name": "default", "object.serial": 170},
            "metadata": [
                {
                    "subject": 0,
                    "key": "default.audio.sink",
                    "type": "Spa:String:JSON",
                    "value": {"name": "alsa_output.speaker"},
                }
            ],
        },
        *extra,
    ]


class Tools:
    def __init__(self, g, fail_link=None):
        self.g = g
        self.calls = []
        self.fail_link = fail_link

    def __call__(self, argv, timeout):
        self.calls.append(argv)
        if argv[0] == str(out.PW_DUMP):
            return 0, json.dumps(self.g)
        if argv[0] == str(out.PW_LINK):
            # Real pw-link refuses an already present pair with EEXIST.
            if len(argv) == 3 and argv[1] != "-d":
                pair = tuple(map(int, argv[1:]))
                if pair in {
                    (
                        o.get("info", {}).get("output-port-id"),
                        o.get("info", {}).get("input-port-id"),
                    )
                    for o in self.g
                    if o.get("type") == "PipeWire:Interface:Link"
                }:
                    return 1, "File exists"
            if self.fail_link and argv[1:] == self.fail_link:
                return 1, ""
            return 0, ""
        raise AssertionError(argv)


def test_link_connects_tunnel_to_default_sink_by_channel(p):
    tools = Tools(fake_graph(p.fifo))
    linked = out.link(p.fifo, tools)
    assert linked.pairs == ((38, 51), (39, 52))
    assert linked.tunnel_id == 34 and linked.sink_id == 50
    assert tools.calls[1:] == [
        [str(out.PW_LINK), "38", "51"],
        [str(out.PW_LINK), "39", "52"],
    ]


def test_partial_link_failure_is_rolled_back(p):
    tools = Tools(fake_graph(p.fifo), fail_link=["39", "52"])
    with pytest.raises(out.RadioOutputError):
        out.link(p.fifo, tools)
    assert tools.calls[-1] == [str(out.PW_LINK), "-d", "38", "51"]


@pytest.mark.parametrize(
    "graph_case",
    ["foreign-client", "other-fifo", "duplicate", "no-default", "mono-sink"],
)
def test_link_refuses_unclear_graph(p, graph_case):
    g = fake_graph(p.fifo)
    if graph_case == "foreign-client":
        g = fake_graph(p.fifo, client_remote="pipewire-0")
    elif graph_case == "other-fifo":
        g[1]["info"]["props"]["pipe.filename"] = "/tmp/other"
    elif graph_case == "duplicate":
        g.append(
            node(80, out.TUNNEL_NODE, **{"pipe.filename": str(p.fifo), "client.id": 21})
        )
    elif graph_case == "no-default":
        g = [o for o in g if o.get("type") != "PipeWire:Interface:Metadata"]
    else:
        g = [o for o in g if o.get("id") != 52]
    tools = Tools(g)
    with pytest.raises(out.RadioOutputError):
        out.link(p.fifo, tools)
    assert not any(c[0] == str(out.PW_LINK) for c in tools.calls)


def test_unlink_removes_exactly_the_own_pairs(p):
    linked = out.link(p.fifo, Tools(fake_graph(p.fifo)))
    tools = Tools([])
    assert out.unlink(linked, tools) is True
    assert tools.calls == [
        [str(out.PW_LINK), "-d", "38", "51"],
        [str(out.PW_LINK), "-d", "39", "52"],
    ]


def links_for(pairs):
    return [
        {
            "id": 90 + n,
            "type": "PipeWire:Interface:Link",
            "info": {"output-port-id": a, "input-port-id": b},
        }
        for n, (a, b) in enumerate(pairs)
    ]


@pytest.mark.parametrize("existing", [((38, 51), (39, 52)), ((38, 51),), ((39, 52),)])
def test_link_reuses_exact_existing_pairs_and_creates_only_missing(p, existing):
    tools = Tools(fake_graph(p.fifo, extra=links_for(existing)))
    linked = out.link(p.fifo, tools)
    assert linked.pairs == ((38, 51), (39, 52))
    assert [c for c in tools.calls if c[0] == str(out.PW_LINK)] == [
        [str(out.PW_LINK), str(a), str(b)]
        for a, b in linked.pairs
        if (a, b) not in existing
    ]


def test_link_does_not_adopt_pairs_to_a_different_sink(p):
    other_pairs = ((38, 61), (39, 62))
    tools = Tools(fake_graph(p.fifo, extra=links_for(other_pairs)))
    linked = out.link(p.fifo, tools)
    assert [c for c in tools.calls if c[0] == str(out.PW_LINK)] == [
        [str(out.PW_LINK), str(a), str(b)] for a, b in linked.pairs
    ]


def test_failed_completion_does_not_roll_back_adopted_link(p):
    tools = Tools(
        fake_graph(p.fifo, extra=links_for(((38, 51),))),
        fail_link=["39", "52"],
    )
    with pytest.raises(out.RadioOutputError):
        out.link(p.fifo, tools)
    assert not any(c[1:2] == ["-d"] for c in tools.calls)


def test_verify_requires_same_tunnel_generation_and_links(p):
    linked = out.link(p.fifo, Tools(fake_graph(p.fifo)))
    ok = fake_graph(p.fifo, extra=links_for(linked.pairs))
    assert out.verify(linked, Tools(ok)) is True
    missing = fake_graph(p.fifo, extra=links_for(linked.pairs[:1]))
    assert out.verify(linked, Tools(missing)) is False
    restarted = fake_graph(p.fifo, extra=links_for(linked.pairs))
    restarted[1]["info"]["props"]["object.serial"] = 999
    assert out.verify(linked, Tools(restarted)) is False


def test_verify_is_false_when_graph_unreadable(p):
    linked = out.Linked(34, "134", 50, ((38, 51), (39, 52)))
    assert out.verify(linked, lambda argv, timeout: (1, "")) is False


def test_run_tool_only_accepts_fixed_tools():
    with pytest.raises(out.RadioOutputError):
        out.run_tool(["/usr/bin/pactl", "info"], timeout=1)


@pytest.mark.parametrize(
    "inherited", ["/tmp/evil", f"/run/user/{os.getuid() + 1}", "/run/user/0"]
)
def test_tool_environment_is_minimal(monkeypatch, inherited):
    monkeypatch.setenv("PIPEWIRE_REMOTE", "evil")
    monkeypatch.setenv("XDG_RUNTIME_DIR", inherited)
    env = out._tool_env()
    assert "PIPEWIRE_REMOTE" not in env
    assert env["XDG_RUNTIME_DIR"] == f"/run/user/{os.getuid()}"
    assert out._systemctl_env()["DBUS_SESSION_BUS_ADDRESS"] == (
        f"unix:path=/run/user/{os.getuid()}/bus"
    )


def test_metadata_in_info_props_is_not_trusted_as_default(p):
    g = fake_graph(p.fifo)
    meta = [o for o in g if o.get("type") == "PipeWire:Interface:Metadata"][0]
    meta["info"] = {"props": meta.pop("props")}
    with pytest.raises(out.RadioOutputError):
        out.default_sink(g)


def test_restart_uses_only_the_fixed_user_units():
    calls = []
    out.restart_audio_services(lambda argv, timeout: calls.append(argv) or (0, ""))
    assert calls == [
        [
            str(out.SYSTEMCTL),
            "--user",
            "restart",
            "pipewire",
            "pipewire-pulse",
            "wireplumber",
        ]
    ]
    with pytest.raises(out.RadioOutputError):
        out.restart_audio_services(lambda argv, timeout: (1, "failed"))


def test_systemctl_runner_refuses_any_other_command():
    for argv in (
        [str(out.SYSTEMCTL), "restart", "pipewire"],
        [str(out.SYSTEMCTL), "--user", "stop", *out.AUDIO_UNITS],
        [str(out.SYSTEMCTL), "--user", "restart", "ssh"],
    ):
        with pytest.raises(out.RadioOutputError):
            out._run_systemctl(argv, timeout=1)


def test_systemctl_environment_is_derived_from_own_runtime(monkeypatch):
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/tmp/evil")
    env = out._systemctl_env()
    assert env["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path=/run/user/{os.getuid()}/bus"


def test_wait_for_fifo_is_bounded(p):
    prepared(p, fifo=False)
    now = [0.0]
    assert (
        out.wait_for_fifo(
            p,
            timeout=1,
            clock=lambda: now[0],
            sleep=lambda s: now.__setitem__(0, now[0] + s),
        )
        is False
    )
    os.mkfifo(p.fifo)
    assert out.wait_for_fifo(p, timeout=1) is True


@pytest.mark.parametrize("case", ["no-reader", "regular-file"])
def test_refused_open_releases_the_lock_for_a_later_start(p, case):
    prepared(p, fifo=case == "no-reader")
    if case == "regular-file":
        p.fifo.write_bytes(b"")
    writer = out.FifoWriter(p)
    with pytest.raises(out.RadioOutputError):
        writer.open()
    assert writer.fd is None and writer._lock is None
    if case == "regular-file":
        p.fifo.unlink()
        os.mkfifo(p.fifo)
    r = reader(p)
    try:
        writer.open()  # would fail with "bereits verwendet" if the lock leaked
        os.write(writer.fd, b"\x01\x00\x02\x00")
        assert os.read(r, 16) == b"\x01\x00\x02\x00"
    finally:
        writer.close()
        os.close(r)
