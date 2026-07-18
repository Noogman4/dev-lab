"""Prompt builders for Linux help command documentation."""

from __future__ import annotations


def _value(item: dict, key: str, default: str = "") -> str:
    return str((item or {}).get(key) or default).strip()


def _risk_text(risk_key: str) -> str:
    mapping = {
        "safe": "🟢 Sicher",
        "caution": "🟡 Mit Vorsicht",
        "danger": "🔴 Gefaehrlich",
    }
    return mapping.get(str(risk_key or "").strip().lower(), "⚪ Unbekannt")


def build_linux_help_pdf_prompt(item: dict, *, language: str = "de") -> str:
    """Build a detailed documentation prompt for one Linux command."""
    entry = dict(item or {})
    name = _value(entry, "name", "Unbekannter Befehl")
    command = _value(entry, "cmd", name)
    category = _value(entry, "category", "Allgemein")
    info = _value(entry, "info", "-")
    syntax = _value(entry, "syntax", command or "-")
    example = _value(entry, "example", command or "-")
    explanation = _value(entry, "explanation", "-")
    warning_text = _value(entry, "warning_text", "-")
    tags = _value(entry, "tags", "-")
    root_required = "Ja" if bool(entry.get("root_required")) else "Nein"
    risk = _risk_text(_value(entry, "risk"))

    if str(language or "de").strip().lower() != "de":
        language = "en"
    else:
        language = "de"

    lines = [
        "Erstelle eine vollstaendige, gut lesbare Linux-Befehlsdokumentation.",
        "",
        "Ziel:",
        "- Der Text soll fuer Einsteiger verstaendlich sein.",
        "- Gleichzeitig sollen fortgeschrittene Nutzer genug technische Details bekommen.",
        "- Die Ausgabe soll direkt fuer eine spaetere PDF-Dokumentation geeignet sein.",
        "",
        "Wichtige Regeln fuer deine Antwort:",
        "- Schreibe klar, sachlich und ohne Marketing-Sprache.",
        "- Erklaere Optionen und Risiken konkret.",
        "- Wenn Root-Rechte nicht noetig sind, sage das explizit.",
        "- Wenn Risiken bestehen, erklaere sie konkret und praxisnah.",
        "- Nutze kurze Abschnitte mit klaren Ueberschriften.",
        "- Erfinde keine Optionen, die der Befehl nicht hat.",
        "- Falls Informationen unsicher sind, markiere sie als Pruefpunkt.",
        "",
        "Gewuenschte Struktur der Antwort:",
        "1. Kurzbeschreibung",
        "2. Was macht der Befehl?",
        "3. Syntax",
        "4. Wichtige Optionen",
        "5. Beispiel erklaert Schritt fuer Schritt",
        "6. Typische Anwendungsfaelle",
        "7. Risiken, Nebenwirkungen und Vorsicht",
        "8. Haeufige Fehler",
        "9. Sichere Varianten oder Tipps fuer Einsteiger",
        "10. Verwandte Befehle",
        "",
        "Ausgabe-Sprache:",
        f"- {language}",
        "",
        "NetMon-Daten zum Befehl:",
        f"- Name: {name}",
        f"- Kommando: {command}",
        f"- Kategorie: {category}",
        f"- Kurzbeschreibung: {info}",
        f"- Syntax: {syntax}",
        f"- Beispiel: {example}",
        f"- Datenbank-Erklaerung: {explanation}",
        f"- Zusatzhinweis: {warning_text}",
        f"- Root noetig: {root_required}",
        f"- Risikostufe: {risk}",
        f"- Tags: {tags}",
    ]
    return "\n".join(lines).strip()
