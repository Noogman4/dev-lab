"""Tab-specific scope and bounded local cross-tab preparation."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon.features import chad_controller, chad_system_context as context
from netmon.services.ai_analysis_service import AiAnalysisService
from netmon.services.chad_tab_profiles import PROFILES, profile_for_title
from tests import test_chad_output_layout_v29 as layout

chad_app = layout.chad_app


@pytest.mark.parametrize(
    "title,key",
    [
        ("Security system check overall analysis", "system"),
        ("NetMon Gesamtcheck", "system"),
        ("DNS Analyse", "dns"),
        ("WireGuard Analyse", "vpn"),
        ("Firewall Analyse", "firewall"),
        ("Verbindungen Analyse", "connections"),
        ("Process Guard Fund Analyse", "process"),
        ("Roots Baseline Guard Änderung erklären", "roots"),
        ("PATH Guard Analyse", "path"),
        ("Startup Guard Eintrag Analyse", "startup"),
        ("Repository Guard Analyse", "repository"),
        ("Packet Capture Analyse", "capture"),
        ("Nmap Analyse", "nmap"),
        ("MTR Analyse", "route"),
        ("iftop Analyse", "traffic"),
        ("htop Analyse", "process"),
        ("HDD Analyse", "storage"),
        ("ClamAV Analyse", "clamav"),
        ("Lynis Analyse", "lynis"),
        ("rkhunter Analyse", "rkhunter"),
        ("System-Log: Kernel", "logs"),
        ("Linux Hilfe Analyse", "linux"),
        ("Unbekannte Auswahl", "general"),
    ],
)
def test_known_sources_receive_specific_profile(title, key):
    assert profile_for_title(title).key == key


def test_all_profiles_have_distinct_tasks_and_response_structures():
    assert len({p.key for p in PROFILES}) == len(PROFILES)
    assert len({p.task for p in PROFILES}) == len(PROFILES)
    assert len({p.answer for p in PROFILES}) == len(PROFILES)


def test_dns_and_storage_prompts_do_not_mix_instructions():
    service = AiAnalysisService()
    dns = service.build_prompt("DNS Analyse", "Resolver: Testdaten")
    storage = service.build_prompt("HDD Analyse", "SMART: Testdaten")
    assert "Split-DNS" in dns and "SMART-Indikatoren" not in dns
    assert "SMART-Indikatoren" in storage and "Split-DNS" not in storage
    assert "Genau einen zusammengehörigen Terminalbefehl" in dns


def test_per_tab_overrides_cannot_reintroduce_unrelated_default_focuses():
    prompt = chad_controller.build_chad_analysis_prompt(
        SimpleNamespace(), "HDD Analyse", "eigene Daten"
    )
    assert "DNS Analyse: achte" not in prompt
    assert "Firewall Analyse: achte" not in prompt
    assert "SMART-Indikatoren" in prompt


def test_overall_prompt_keeps_context_instead_of_applying_relevance_filter(monkeypatch):
    monkeypatch.setattr(
        chad_controller, "filter_chad_analysis_input", lambda *args: "GEFILTERT"
    )
    prompt = chad_controller.build_chad_analysis_prompt(
        SimpleNamespace(), "NetMon Gesamtcheck", "EIGENE_VOLLSTAENDIGE_DATEN"
    )
    assert "EIGENE_VOLLSTAENDIGE_DATEN" in prompt and "GEFILTERT" not in prompt
    assert "Dedupliziere" in prompt and "fehlende Zeitbezüge" in prompt


def test_title_and_input_are_redacted_and_oversized_data_is_marked():
    prompt = AiAnalysisService().build_prompt(
        "DNS password=SYNTHETIC_SECRET", "token=SYNTHETIC_SECRET\n" + "x" * 40000
    )
    assert "SYNTHETIC_SECRET" not in prompt
    assert "Auszug gekürzt" in prompt


class Text:
    def __init__(self, text):
        self.text = text

    def get(self, start, end):
        assert start == "1.0"
        assert end == f"1.0+{context.MAX_SECTION_CHARS+1}c"
        return self.text[: context.MAX_SECTION_CHARS + 1]


class Table:
    def get_children(self, parent):
        return tuple(range(1000))

    def item(self, row, field):
        return f"row-{row}" if field == "text" else ("pid", row)


def test_snapshot_reads_only_explicit_existing_data_and_labels_missing_sections():
    app = SimpleNamespace(
        dns_text=Text("DNS token=SYNTHETIC_SECRET"),
        conn_table=Table(),
        chad_chat_input=Text("PRIVATE_CHAT"),
    )
    app.refresh_dns = Mock(side_effect=AssertionError("refresh not allowed"))
    text = context.collect_system_context(app)
    assert "SYNTHETIC_SECRET" not in text and "PRIVATE_CHAT" not in text
    assert "DNS" in text and "nicht geprüft" in text and "Tabelle gekürzt" in text
    assert "row-60" not in text
    assert len(text) <= context.MAX_CONTEXT_CHARS
    app.refresh_dns.assert_not_called()


def test_partial_private_key_and_long_sections_do_not_escape_redaction():
    data = "prefix\n-----BEGIN OPENSSH PRIVATE KEY-----\n" + "SYNTHETIC_SECRET" * 1000
    text = context.collect_system_context(SimpleNamespace(dns_text=Text(data)))
    assert "SYNTHETIC_SECRET" not in text and "PRIVATE_KEY_REDACTED" in text


def test_preparation_has_no_online_or_browser_side_effect(monkeypatch):
    app = SimpleNamespace(dns_text=Text("Resolver vorhanden"), ai_online_service=Mock())
    prepare = Mock()
    monkeypatch.setattr(chad_controller, "prepare_chad_analysis", prepare)
    context.prepare_system_prompt(app)
    assert prepare.call_args.args[1] == "NetMon Gesamtcheck"
    assert "Resolver vorhanden" in prepare.call_args.args[2]
    assert app.ai_online_service.mock_calls == []


@pytest.mark.parametrize("geometry", ["650x480", "1024x768"])
def test_real_system_prompt_button_is_visible_and_prepares_only(
    chad_app, monkeypatch, geometry
):
    root, app = chad_app
    root.geometry(geometry)
    prepare = Mock()
    monkeypatch.setattr(context, "prepare_system_prompt", prepare)
    root.update()
    app.btn_chad_system_prompt.invoke()
    root.update()
    prepare.assert_called_once_with(app)
    button = app.btn_chad_system_prompt
    assert button.winfo_ismapped()
    assert (
        button.winfo_rootx() + button.winfo_width()
        <= root.winfo_rootx() + root.winfo_width()
    )
