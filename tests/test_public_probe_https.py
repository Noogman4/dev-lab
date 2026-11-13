"""Public IP/country probes use authenticated transport and validated answers.

No real network access: run_cmd is faked, the curl check uses loopback only.
"""

import http.server
from pathlib import Path
import shutil
import socketserver
import threading

import pytest

from tools import netmon

APP_SOURCE = Path(netmon.__file__).read_text(encoding="utf-8")


def test_probe_arguments_force_https_and_cap_the_response():
    args = netmon.public_probe_curl_args(netmon.PUBLIC_IP_URL, 3)
    assert netmon.PUBLIC_IP_URL.startswith("https://")
    assert netmon.PUBLIC_COUNTRY_URL.startswith("https://")
    for flag, value in (
        ("--proto", "=https"),
        ("--proto-redir", "=https"),
        ("--max-filesize", str(netmon.PUBLIC_PROBE_MAX_BYTES)),
        ("--max-time", "3"),
    ):
        assert args[args.index(flag) + 1] == value


def test_no_scheme_less_probe_target_remains():
    for bare in ('"ifconfig.me"', '"ipinfo.io/country"', '"ifconfig.me"]'):
        assert bare not in APP_SOURCE


@pytest.mark.parametrize(
    "text, expected",
    [
        ("198.51.100.7\n", "198.51.100.7"),
        ("2001:DB8::1", "2001:db8::1"),
        ("<html>DE 1.2.3.4</html>", ""),
        ("1.2.3.4; rm -rf", ""),
        ("1" * 5000, ""),
        ("", ""),
    ],
)
def test_public_ip_answer_must_be_an_address(text, expected):
    assert netmon.canonical_public_ip(text) == expected


def _app(monkeypatch, ip_answer, country_answer):
    app = netmon.App.__new__(netmon.App)
    logs = []
    app.log_safe = logs.append
    app._base_wg_profile_name = lambda p: p
    app.public_ip = ""
    app.country = ""
    calls = []

    def fake_run_cmd(args, timeout=15, text=True):
        calls.append(args)
        target = " ".join(args)
        if "ipinfo.io" in target:
            return 0, country_answer + "\n200"
        if "ifconfig.me" in target:
            return 0, ip_answer
        return 1, ""

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    return app, logs, calls


def test_exit_country_check_uses_https_probes_only(monkeypatch):
    app, logs, calls = _app(monkeypatch, "203.0.113.9", "NL")
    assert app.verify_vpn_exit_country("NL") is True
    assert len(calls) == 2
    for args in calls:
        assert args[args.index("--proto") + 1] == "=https"
        assert args[-1].startswith("https://")
    assert any("public IP 203.0.113.9" in line for line in logs)


def test_forged_ip_text_is_never_logged_as_public_ip(monkeypatch):
    app, logs, _calls = _app(monkeypatch, "<b>Your IP: 10.0.0.1 (NL)</b>", "NL")
    app.verify_vpn_exit_country("NL")
    joined = "\n".join(logs)
    assert "<b>" not in joined and "Your IP" not in joined
    assert app.public_ip == ""


@pytest.mark.skipif(shutil.which("curl") is None, reason="curl missing")
def test_curl_refuses_plain_http_with_probe_arguments():
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"NL")

        def log_message(self, *_args):
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/country"
        rc, _out = netmon.run_cmd(
            [*netmon.public_probe_curl_args(url, 2), url], timeout=5
        )
    finally:
        server.shutdown()
        server.server_close()
    assert rc != 0
    assert requests == []
