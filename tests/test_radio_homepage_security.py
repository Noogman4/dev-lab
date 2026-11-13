"""Untrusted station homepages never become ambient browser requests."""

import json
import socket
import subprocess
from types import SimpleNamespace
import webbrowser

import pytest

from netmon.core.radio_homepage import normalize_homepage_url
from netmon.features import radio_controller as radio

UNSAFE = [
    "http://127.0.0.1/admin",
    "http://127.1/",
    "http://2130706433/",
    "http://0177.0.0.1/",
    "http://0x7f000001/",
    "http://0x7f.0.0.1/",
    "https://[::1]/",
    "http://[::ffff:127.0.0.1]/",
    "http://10.0.0.1/",
    "http://172.16.0.1/",
    "http://192.168.1.1/",
    "http://169.254.169.254/",
    "http://100.64.0.1/",
    "http://0.0.0.0/",
    "http://224.0.0.1/",
    "http://255.255.255.255/",
    "http://[::]/",
    "http://[fe80::1]/",
    "http://[fc00::1]/",
    "http://[ff02::1]/",
    "http://[fe80::1%25eth0]/",
    "http://printer/",
    "http://localhost/",
    "https://x.localhost/",
    "http://router.local/",
    "http://router.localdomain/",
    "http://router.lan/",
    "http://router.home/",
    "http://router.home.arpa/",
    "http://x.internal/",
    "http://x.intranet/",
    "http://x.corp/",
    "http://x.onion/",
    "http://x.i2p/",
    "http://x.test/",
    "http://x.invalid/",
    "http://x.example/",
    "http://user@example.com/",
    "http://user:pass@example.com/",
    "http://attacker.example\\@example.com/",
    "https://example.com:22/",
    "https://example.com:8443/",
    "http://example.com:443/",
    "https://example.com:80/",
    "https://example.com:/",
    "https://example.com:bad/",
    "https://example.com:65536/",
    "https://example.com:0443/",
    "https://[2606:4700:4700::1111]evil.com/",
    "https://[2606:4700:4700::1111].example.com/",
    "https://%31%32%37.0.0.1/",
    "https:///path",
    "https://",
    "https://[::1",
    "https://example..com/",
    "https://example.com../",
    "https://-bad.example/",
    "https://bad_.example/",
    "https://example.com\n/",
    " https://example.com\t",
    "https://example.com/a b",
    "https://example.com/%0d%0aHost:private",
    "https://example.com/%zz",
    "file:///etc/passwd",
    "javascript:alert(1)",
    "//example.com/",
    "",
    None,
    123,
]


@pytest.mark.parametrize("url", UNSAFE)
def test_rejects_unsafe_homepage_authorities_and_syntax(url):
    assert normalize_homepage_url(url) == ""


@pytest.mark.parametrize(
    "raw, expected",
    [
        (
            "https://Example.COM:443/path?q=ok#part",
            "https://example.com/path?q=ok#part",
        ),
        ("http://example.com:80/", "http://example.com/"),
        ("https://example.com./", "https://example.com/"),
        ("https://8.8.8.8/", "https://8.8.8.8/"),
        ("https://[2606:4700:4700::1111]/", "https://[2606:4700:4700::1111]/"),
        ("https://bücher.de/", "https://xn--bcher-kva.de/"),
    ],
)
def test_canonical_display_addresses(raw, expected):
    assert normalize_homepage_url(raw) == expected


@pytest.fixture
def homepage_action(monkeypatch):
    clipboard = ["previous clipboard"]
    reviews, statuses = [], []
    station = {
        "id": "station",
        "name": "Station",
        "url": "https://stream.example.com/live",
    }
    app = SimpleNamespace(
        clipboard_clear=clipboard.clear, clipboard_append=clipboard.append
    )
    monkeypatch.setattr(radio, "_resolve_target_station", lambda *_: station)
    monkeypatch.setattr(radio, "_selected_station_id", lambda _: "station")
    monkeypatch.setattr(
        radio, "set_radio_status", lambda _, text: statuses.append(text)
    )
    for target, name in [
        (webbrowser, "open"),
        (subprocess, "Popen"),
        (socket, "getaddrinfo"),
    ]:
        monkeypatch.setattr(
            target,
            name,
            lambda *a, **k: pytest.fail("homepage caused external activity"),
        )

    def review(title, text, **options):
        reviews.append((title, text, options))
        return app.approved

    monkeypatch.setattr(radio.messagebox, "askyesno", review)
    app.approved = True
    return app, station, clipboard, reviews, statuses


@pytest.mark.parametrize("url", [x for x in UNSAFE if isinstance(x, str)])
def test_legacy_stored_homepages_are_rechecked_without_stream_fallback(
    homepage_action, url
):
    app, station, clipboard, reviews, _ = homepage_action
    station["homepage"] = url
    assert radio.open_selected_station_homepage(app) is False
    assert clipboard == ["previous clipboard"]
    assert not reviews


@pytest.mark.parametrize("approved", [False, True])
def test_public_address_is_only_copied_after_explicit_review(homepage_action, approved):
    app, station, clipboard, reviews, _ = homepage_action
    app.approved = approved
    # DNS answers and redirects are deliberately not trusted or followed at all.
    station["homepage"] = (
        "https://EXAMPLE.com:443/redirect?target=http%3A%2F%2F127.0.0.1"
    )
    expected = "https://example.com/redirect?target=http%3A%2F%2F127.0.0.1"
    assert radio.open_selected_station_homepage(app) is approved
    assert clipboard == ([expected] if approved else ["previous clipboard"])
    assert "Ziel: example.com" in reviews[0][1]
    assert expected in reviews[0][1]
    assert reviews[0][2]["default"] == "no"


@pytest.mark.parametrize("failure", ["dialog", "clipboard"])
def test_failed_review_or_copy_never_uses_a_browser(
    homepage_action, monkeypatch, failure
):
    app, station, _, _, statuses = homepage_action
    station["homepage"] = "https://example.com"

    def fail(*a, **k):
        raise RuntimeError("unavailable")

    if failure == "dialog":
        monkeypatch.setattr(radio.messagebox, "askyesno", fail)
    else:
        app.clipboard_append = fail
    assert radio.open_selected_station_homepage(app) is False
    assert "nicht kopiert" in statuses[-1]


def test_catalog_persistence_strips_private_homepage_without_losing_station(tmp_path):
    rows = radio._filter_radio_db_rows(
        [
            {
                "name": "Untrusted",
                "url": "https://stream.example.com/live",
                "homepage": "http://127.0.0.1/admin",
            },
            {
                "name": "Public",
                "url": "https://stream.example.com/live2",
                "homepage": "https://EXAMPLE.com:443",
            },
        ]
    )
    assert len(rows) == 2
    assert rows[0]["homepage"] == ""
    assert rows[1]["homepage"] == "https://example.com"
    app = SimpleNamespace(radio_db_path=str(tmp_path / "radio_db.json"))
    assert radio.save_radio_db(app, stations=rows)
    saved = json.loads((tmp_path / "radio_db.json").read_text())
    assert saved[0]["homepage"] == ""
    assert saved[1]["homepage"] == "https://example.com"
