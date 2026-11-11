"""System-Logs sub-tab: fixed sources, bounded reads, anonymisation, Chad hand-over."""

import os
import threading
import time
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.core import system_logs as logs
from netmon.ui.tabs import system_logs_view as view_module

# ── Sources and argv ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("source", [s for s in logs.SOURCES if s.journal])
@pytest.mark.parametrize("range_key", list(logs.RANGES))
def test_journal_argv_is_fixed_and_bounded(source, range_key):
    argv = logs.journal_argv(source, range_key, 200)
    assert argv[:5] == ["journalctl", "--no-pager", "-q", "-o", "short-iso"]
    assert argv[-2:] == ["-n", "200"]
    assert all(isinstance(part, str) for part in argv)
    assert "sudo" not in argv and "--vacuum-time" not in " ".join(argv)


@pytest.mark.parametrize(
    "args",
    [
        ("evil", "boot", 200),
        ("system", "since-forever", 200),
        ("system", "boot", 199),
        ("system", "boot", True),
        ("system", "boot", "200"),
    ],
)
def test_unknown_source_range_or_size_is_rejected(args):
    with pytest.raises(ValueError):
        logs.read_source(*args, run=lambda *a, **k: pytest.fail("ran"))


def test_journal_read_uses_runner_and_handles_empty_and_errors():
    calls = []

    def run(argv, timeout):
        calls.append((argv, timeout))
        return 0, "line a\nline b\n"

    assert logs.read_source("system", "hour", 500, run=run) == (
        True,
        "line a\nline b\n",
    )
    assert calls[0][1] == logs.JOURNAL_TIMEOUT
    assert logs.read_source("firewall", run=lambda *a, **k: (1, "")) == (
        True,
        "Keine Einträge im gewählten Zeitraum.",
    )
    ok, text = logs.read_source("kernel", run=lambda *a, **k: (1, "Permission denied"))
    assert not ok and "Permission denied" in text

    def boom(*_a, **_k):
        raise TimeoutError

    ok, text = logs.read_source("network", run=boom)
    assert not ok and "TimeoutError" in text


def test_output_is_capped(monkeypatch):
    monkeypatch.setattr(logs, "MAX_OUTPUT_BYTES", 50)
    ok, text = logs.read_source(
        "system", run=lambda *a, **k: (0, "\n".join(f"row {i}" for i in range(100)))
    )
    assert ok and len(text) <= 50 and text.endswith("row 99")


# ── File tails ───────────────────────────────────────────────────────────────


def test_file_tail_reads_only_the_end(tmp_path):
    path = tmp_path / "auth.log"
    path.write_text("".join(f"line {i}\n" for i in range(5000)))
    tail = logs.read_file_tail(path, lines=200, max_bytes=4096)
    rows = tail.splitlines()
    assert rows[-1] == "line 4999" and len(rows) <= 200
    assert all(row.startswith("line ") for row in rows)  # cut first row dropped


def test_file_tail_refuses_links_and_special_files(tmp_path):
    target = tmp_path / "real.log"
    target.write_text("secret\n")
    link = tmp_path / "link.log"
    link.symlink_to(target)
    with pytest.raises(OSError):
        logs.read_file_tail(link)
    fifo = tmp_path / "fifo.log"
    os.mkfifo(fifo)
    with pytest.raises(PermissionError):
        logs.read_file_tail(fifo)


def test_file_sources_report_missing_and_unreadable(tmp_path, monkeypatch):
    present = tmp_path / "history.log"
    present.write_text("Start-Date: x\n")
    missing = tmp_path / "missing.log"
    monkeypatch.setattr(
        logs,
        "_BY_KEY",
        {
            **logs._BY_KEY,
            "packages": logs.Source(
                "packages", "P", files=(str(present), str(missing))
            ),
        },
    )
    ok, text = logs.read_source("packages")
    assert ok and "Start-Date: x" in text and "(Datei nicht vorhanden)" in text


# ── Anonymisation ────────────────────────────────────────────────────────────

SAMPLE = (
    "2026-11-11T10:00:01 proglab kernel: [UFW BLOCK] IN=wlp3s0 MAC=aa:bb:cc:dd:ee:ff:"
    "11:22:33:44:55:66:08:00 SRC=192.168.1.20 DST=8.8.8.8 PROTO=UDP\n"
    "2026-11-11T10:00:02 proglab NetworkManager: connection 'Heim' "
    "(3f1c2b7a-1111-2222-3333-444455556666) SSID 'MeinWLAN' dev aa:bb:cc:00:11:22\n"
    "2026-11-11T10:00:03 proglab sudo: happy : TTY=pts/0 ; USER=root ; "
    "COMMAND=/usr/bin/wg show token=abc123\n"
    "peer AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdefg= 2a02:810d::7 8.8.8.8 "
    "fe80::1 time 12:34:56 local 127.0.0.1 user@example.org"
)


def test_anonymisation_replaces_identifying_data_consistently():
    text, counts = logs.anonymize_for_ai(SAMPLE, hostname="proglab", username="happy")
    for secret in (
        "proglab",
        "happy",
        "192.168.1.20",
        "8.8.8.8",
        "aa:bb:cc",
        "3f1c2b7a",
        "MeinWLAN",
        "Heim",
        "AbCdEfGh",
        "2a02:810d",
        "fe80::1",
        "abc123",
        "user@example.org",
    ):
        assert secret not in text, secret
    assert text.count("IP-1") >= 2  # 8.8.8.8 twice -> same placeholder
    assert "127.0.0.1" in text and "12:34:56" in text  # not identifying
    assert counts["HOST"] == 3 and counts["IP"] == 2 and counts["MAC"] == 3


def test_truncation_keeps_the_newest_lines():
    text = "\n".join(f"r{i}" for i in range(1000))
    short, truncated = logs.truncate_for_ai(text, max_lines=10)
    assert truncated and short.splitlines() == [f"r{i}" for i in range(990, 1000)]
    same, truncated = logs.truncate_for_ai("a\nb")
    assert same == "a\nb" and not truncated


# ── View ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def view(monkeypatch):
    root = tk.Tk()
    root.withdraw()
    handed = []
    root.prepare_chad_analysis = lambda title, text: handed.append((title, text))
    reads = []

    def read_source(key, range_key, lines):
        reads.append((key, range_key, lines, threading.get_ident()))
        return True, (
            "ok line\nsomething failed hard\nwarning: slow\n"
            "proglab sshd: from 192.168.1.20 user happy"
        )

    monkeypatch.setattr(view_module.system_logs, "read_source", read_source)
    monkeypatch.setattr(logs.socket, "gethostname", lambda: "proglab")
    monkeypatch.setattr(logs.getpass, "getuser", lambda: "happy")
    notebook = ttk.Notebook(root)
    notebook.pack()
    built = view_module.build_system_logs_view(root, notebook)
    notebook.add(built.frame, text="System-Logs")
    root.update()
    yield root, built, reads, handed
    root.destroy()


def _wait(predicate, root, timeout=3):
    end = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < end
        root.update()
        time.sleep(0.005)


def test_nothing_is_read_until_shown_and_reading_is_off_the_tk_thread(view):
    root, built, reads, _handed = view
    assert reads == [] and not built.loaded_once
    built.on_shown()
    _wait(lambda: "something failed" in built.text.get("1.0", "end"), root)
    assert reads[0][:3] == ("system", "boot", 500)
    assert reads[0][3] != threading.main_thread().ident
    built.on_shown()  # second show does not reload
    root.update()
    assert len(reads) == 1
    error_lines = built.text.tag_ranges("error")
    assert error_lines and "failed" in built.text.get(*error_lines[:2])


def test_stale_result_is_dropped(view):
    root, built, _reads, _handed = view
    first = built.refresh()
    built.refresh()
    assert not built._deliver(first, "system", True, "OLD")
    assert "OLD" not in built.text.get("1.0", "end")


def test_filter_and_source_selection(view):
    root, built, reads, _handed = view
    built.on_shown()
    _wait(lambda: built.raw_text, root)
    built.filter_var.set("warning")
    root.update()
    assert built.text.get("1.0", "end").strip() == "warning: slow"
    built.sources.selection_clear(0, "end")
    built.sources.selection_set(4)
    built._source_selected()
    _wait(lambda: len(reads) == 2, root)
    assert reads[-1][0] == "auth"


def test_chad_preview_shows_only_anonymised_text_and_hands_over_once(view):
    root, built, _reads, handed = view
    built.on_shown()
    _wait(lambda: built.raw_text, root)
    window = built.open_chad_preview()
    root.update()
    shown = window.preview_text
    assert "proglab" not in shown and "192.168.1.20" not in shown
    assert "happy" not in shown and "[HOST]" in shown
    assert handed == []  # nothing sent before the explicit click
    window.hand_over()
    assert len(handed) == 1 and handed[0][0].startswith("System-Log: ")
    assert handed[0][1] == shown


def test_log_tab_has_two_subtabs_and_loads_lazily(monkeypatch):
    from netmon.ui.tabs import log_tab

    root = tk.Tk()
    root.withdraw()
    try:
        reads = []
        monkeypatch.setattr(
            view_module.system_logs,
            "read_source",
            lambda *a: reads.append(a) or (True, "x"),
        )
        app = root
        app.nb = ttk.Notebook(root)
        app.nb.pack()
        app.tr = lambda _key, default=None: default
        app.add_tooltip = lambda *a, **k: None
        app.attach_chad_context_menu = lambda *a, **k: None
        for name in (
            "clear_log",
            "prepare_log_selection_chad_analysis",
            "choose_log_overlay_image",
            "toggle_log_overlay",
            "preflight_recheck",
            "open_dependency_installer",
            "_on_log_overlay_picker_select",
            "_choose_log_overlay_folder",
            "_step_log_overlay_selection",
            "close_log_overlay_picker",
            "_on_log_overlay_resize",
            "_restore_log_overlay_from_config",
        ):
            setattr(app, name, lambda *a, **k: None)
        app.dep_installer_button_var = tk.StringVar(root, "x")
        app.var_auto_log_clear = tk.BooleanVar(root, False)
        log_tab.build_log_tab(app)
        root.update()
        tabs = [app.log_subtabs.tab(t, "text") for t in app.log_subtabs.tabs()]
        assert tabs == ["NetMon", "System-Logs"]
        assert app.text.winfo_toplevel() is root and reads == []
        app.log_subtabs.select(app.tab_log_system)
        root.update()
        _wait(lambda: reads, root)
    finally:
        root.destroy()


# ── Review fixes (Codex SL-1 … SL-6, H-1) ───────────────────────────────────


@pytest.mark.parametrize(
    "line,secret",
    [
        ("NetworkManager: Config: added 'ssid' value 'HomeNet'", "HomeNet"),
        ("wpa_supplicant: ssid=HomeNet freq=2412", "HomeNet"),
        ('ssid: "Home Net 5G"', "Home Net 5G"),
        ("Activation: starting connection 'Office VPN'", "Office VPN"),
        ("added 'connection.id' value 'Office VPN'", "Office VPN"),
    ],
)
def test_ssid_and_connection_values_are_replaced_not_the_field_names(line, secret):
    text, counts = logs.anonymize_for_ai(line, hostname="hostfx", username="userfx")
    assert secret not in text and ("SSID-1" in text or "CONN-1" in text), text
    assert sum(counts.values()) == 1


def test_counts_only_real_replacements():
    text, counts = logs.anonymize_for_ai(
        "nothing private here 12:34:56", hostname="hostfx", username="userfx"
    )
    assert counts == {} and text == "nothing private here 12:34:56"


def test_ipv6_with_two_digit_groups_is_not_a_mac():
    text, counts = logs.anonymize_for_ai(
        "SRC=2a02:810d:ab:cd:ef:12:34:56 dev aa:bb:cc:dd:ee:ff",
        hostname="hostfx",
        username="userfx",
    )
    assert text == "SRC=IP6-1 dev MAC-1" and counts == {"IP6": 1, "MAC": 1}


@pytest.mark.parametrize(
    "address,label",
    [
        ("::ffff:198.51.100.7", "LAN-IP6-1"),  # documentation range = private
        ("::ffff:8.8.4.4", "IP6-1"),
        ("2001:db8::192.0.2.42", "LAN-IP6-1"),
        ("64:ff9b::8.8.8.8", "IP6-1"),
    ],
)
def test_ipv6_with_embedded_ipv4_is_one_token(address, label):
    text, counts = logs.anonymize_for_ai(
        f"SRC={address} x", hostname="hostfx", username="userfx"
    )
    assert text == f"SRC={label} x" and sum(counts.values()) == 1


def test_mapped_loopback_stays_like_real_loopback():
    text, counts = logs.anonymize_for_ai(
        "SRC=::ffff:127.0.0.1 DST=127.0.0.1 via ::1",
        hostname="hostfx",
        username="userfx",
    )
    assert text == "SRC=::ffff:127.0.0.1 DST=127.0.0.1 via ::1" and counts == {}


def test_placeholder_index_is_never_read_as_an_address():
    # SL-4-R: placeholder IP6-127 + IPv4 tail used to look like 127.0.113.42.
    earlier = "\n".join(f"DST=2606:4700::{n:x}" for n in range(1, 127))
    text, counts = logs.anonymize_for_ai(
        earlier + "\nSRC=::ffff:203.0.113.42",
        hostname="hostfx",
        username="userfx",
    )
    rows = text.splitlines()
    assert rows[125] == "DST=IP6-126"
    assert rows[126] == "SRC=LAN-IP6-1"
    assert ".0.113.42" not in text and "203" not in text
    assert counts == {"IP6": 126, "LAN-IP6": 1}


def test_input_cannot_forge_placeholder_tokens():
    forged = "\ue000\ue010\ue001 SRC=8.8.8.8"
    text, _ = logs.anonymize_for_ai(forged, hostname="hostfx", username="userfx")
    assert text == "\ufffd\ufffd\ufffd SRC=IP-1"


def test_user_name_does_not_rewrite_host_placeholder():
    text, counts = logs.anonymize_for_ai(
        "on mybox as HOST", hostname="mybox", username="HOST"
    )
    assert text == "on [HOST] as [USER]" and counts == {"HOST": 1, "USER": 1}


def test_same_mac_gets_same_label_everywhere():
    text, _ = logs.anonymize_for_ai(
        "MAC=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:08:00 later AA-BB-CC-DD-EE-FF "
        "and 11:22:33:44:55:66",
        hostname="hostfx",
        username="userfx",
    )
    assert text == "MAC=MAC-1:MAC-2:08:00 later MAC-1 and MAC-2"


def test_limits_are_utf8_bytes():
    ok, text = logs.read_source("system", run=lambda *a, **k: (0, "😀" * (1 << 20)))
    assert ok and len(text.encode("utf-8")) <= logs.MAX_OUTPUT_BYTES
    short, truncated = logs.truncate_for_ai("😀" * 100_000)
    assert truncated and len(short.encode("utf-8")) <= logs.CHAD_MAX_BYTES


def test_bounded_runner_keeps_only_the_newest_bytes_while_reading(monkeypatch):
    import sys

    monkeypatch.setattr(logs, "MAX_OUTPUT_BYTES", 1 << 16)
    program = (
        "import sys\n" "for i in range(200000): sys.stdout.write(f'row {i:06d}\\n')\n"
    )
    rc, text = logs._run_bounded(
        [sys.executable, "-I", "-S", "-c", program], timeout=20
    )
    assert rc == 0 and len(text.encode()) <= 1 << 16
    assert text.splitlines()[-1] == "row 199999" and text.startswith("row ")


def test_bounded_runner_times_out_and_reaps(monkeypatch):
    import sys

    with pytest.raises(TimeoutError):
        logs._run_bounded(
            [sys.executable, "-I", "-S", "-c", "import time; time.sleep(30)"],
            timeout=0.5,
        )


def test_only_one_reader_runs_and_the_newest_request_wins(view, monkeypatch):
    root, built, _reads, _handed = view
    release = threading.Event()
    started = []

    def blocked(key, range_key, lines):
        started.append(key)
        assert release.wait(5)
        return True, f"text for {key}"

    monkeypatch.setattr(view_module.system_logs, "read_source", blocked)
    for _ in range(10):
        built.refresh()
    built.source_key = "kernel"
    built.refresh()
    root.update()
    assert started == ["system"]  # one reader, the rest coalesced
    release.set()
    _wait(lambda: built.loaded_key == "kernel", root)
    assert started == ["system", "kernel"]
    assert "text for kernel" in built.text.get("1.0", "end")


def test_file_sources_disable_the_time_range(view):
    root, built, _reads, _handed = view
    index = next(i for i, s in enumerate(logs.SOURCES) if s.key == "auth")
    built.sources.selection_clear(0, "end")
    built.sources.selection_set(index)
    built._source_selected()
    assert str(built.range_box.cget("state")) == "disabled"
    _wait(lambda: built.loaded_key == "auth", root)
    assert "Zeitraum" in built.status_var.get()
    built.sources.selection_clear(0, "end")
    built.sources.selection_set(0)
    built._source_selected()
    assert str(built.range_box.cget("state")) == "readonly"


def test_preview_label_comes_from_the_shown_snapshot(view, monkeypatch):
    root, built, _reads, handed = view
    assert built._deliver(built.generation, "system", True, "OLD SYSTEM TEXT")
    release = threading.Event()
    monkeypatch.setattr(
        view_module.system_logs,
        "read_source",
        lambda *a: (release.wait(5), (True, "NEW AUTH TEXT"))[1],
    )
    built.sources.selection_clear(0, "end")
    built.sources.selection_set(4)
    built._source_selected()
    window = built.open_chad_preview()
    window.hand_over()
    title, text = handed[-1]
    assert "OLD SYSTEM TEXT" in text and "Systemfehler" in title
    release.set()
    _wait(lambda: built.loaded_key == "auth", root)
