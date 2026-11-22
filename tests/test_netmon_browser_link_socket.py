"""Test the browser handoff with real local sockets and a fake Firefox launch."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import select
import socket
from threading import Event

import pytest

from netmon.modules.secure_browser import link_socket, session


def test_forward_confirms_only_after_handoff(tmp_path):
    state = tmp_path / "browser"
    url = "https://example.org/ä?q=1&next=2"
    seen = []
    with session._lock_profile(state) as directory:
        with link_socket.listen(directory) as listener, ThreadPoolExecutor() as workers:
            future = workers.submit(link_socket.forward, directory, url, Event())
            assert select.select([listener], [], [], 2)[0]

            def handoff(link):
                assert not future.done()
                seen.append(link)

            link_socket.receive(listener, handoff)
            assert future.result(timeout=2) is True
        assert not (state / "links.sock").exists()
        assert link_socket.forward(directory, url, Event()) is False
    assert seen == [url]


@pytest.mark.parametrize(
    "packet",
    [b"file:///etc/passwd", b"https://example.org/\x00", b"x" * 32769, b"\xff"],
)
def test_invalid_packets_do_not_reach_firefox(tmp_path, packet):
    state = tmp_path / "browser"
    with (
        session._lock_profile(state) as directory,
        link_socket.listen(directory) as listener,
    ):
        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as client:
            client.settimeout(2)
            client.connect(f"/proc/self/fd/{directory}/links.sock")
            client.sendall(packet)
            link_socket.receive(listener, lambda _url: pytest.fail("Invalid handoff"))
            assert client.recv(8) == b"error"


def test_symlink_cannot_replace_reserved_socket(tmp_path):
    state = tmp_path / "browser"
    target = tmp_path / "untouched"
    target.write_text("kept", encoding="utf-8")
    with session._lock_profile(state) as directory:
        reserved = state / "links.sock"
        reserved.symlink_to(target)
        with pytest.raises(session.BrowserSandboxError, match="unzulässig"):
            with link_socket.listen(directory):
                pytest.fail("Replaced the symlink")
        with pytest.raises(session.BrowserSandboxError, match="unzulässig"):
            link_socket.forward(directory, "https://example.org/", Event())
        assert reserved.is_symlink() and target.read_text(encoding="utf-8") == "kept"


def test_new_owner_reclaims_socket_after_unclean_exit(tmp_path):
    state = tmp_path / "browser"
    endpoint = state / "links.sock"
    with session._lock_profile(state) as directory:
        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as stale:
            stale.bind(f"/proc/self/fd/{directory}/links.sock")
        assert endpoint.is_socket()
        assert link_socket.forward(directory, "https://example.org/", Event()) is False

    with session._lock_profile(state) as directory, link_socket.listen(directory):
        assert endpoint.is_socket()
    assert not endpoint.exists()


def test_peer_must_belong_to_the_same_linux_user():
    class OtherUser:
        def getsockopt(self, level, option, size):
            assert (level, option, size) == (
                socket.SOL_SOCKET,
                socket.SO_PEERCRED,
                link_socket._CREDENTIALS.size,
            )
            return link_socket._CREDENTIALS.pack(100, link_socket.os.getuid() + 1, 100)

    with pytest.raises(session.BrowserSandboxError, match="Gegenstelle"):
        link_socket._check_peer(OtherUser())


def test_failure_after_sending_is_reported_without_launching_a_second_instance(
    tmp_path,
):
    state = tmp_path / "browser"
    browser = session.BrowserSession(state)
    seen = []

    def handoff(url):
        seen.append(url)
        raise session.BrowserSandboxError("Failed in Firefox")

    with session._lock_profile(state) as directory:
        with link_socket.listen(directory) as listener, ThreadPoolExecutor() as workers:
            url = "https://example.org/"
            future = workers.submit(browser._serve, url)
            assert select.select([listener], [], [], 2)[0]
            link_socket.receive(listener, handoff)
            with pytest.raises(session.BrowserSandboxError, match="nicht bestätigt"):
                future.result(timeout=2)
    assert seen == [url]


def test_profile_can_be_taken_over_when_previous_owner_exits_before_send(
    tmp_path, monkeypatch
):
    state = tmp_path / "browser"
    browser = session.BrowserSession(state)
    locked = Event()
    tried = Event()
    owned = []
    underlying = session._lock_profile

    @contextmanager
    def signal_busy(path):
        try:
            with underlying(path) as directory:
                yield directory
        except session._ProfileBusy:
            locked.set()
            raise

    monkeypatch.setattr(session, "_lock_profile", signal_busy)
    monkeypatch.setattr(browser, "_serve_profile", lambda _fd, url: owned.append(url))
    original_forward = link_socket.forward

    def forward(directory, url, stop):
        assert original_forward(directory, url, stop) is False
        tried.set()
        return False

    monkeypatch.setattr(link_socket, "forward", forward)
    with ThreadPoolExecutor() as workers:
        with underlying(state):
            future = workers.submit(browser._serve, "https://example.org/")
            assert locked.wait(2) and tried.wait(2)
        assert future.result(timeout=2) is None
    assert owned == ["https://example.org/"]
