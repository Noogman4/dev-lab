"""Self-contained single-entry Markdown assignments based on the glossary pilot."""

from __future__ import annotations

try:
    from netmon.services.linux_help_library_markdown import entry_header, format_header
except ModuleNotFoundError:
    from services.linux_help_library_markdown import entry_header, format_header

COMMAND_SECTIONS = (
    "Kurzbeschreibung",
    "Was macht der Befehl?",
    "Syntax",
    "Wichtige Optionen",
    "Beispiel erklärt Schritt für Schritt",
    "Typische Anwendungsfälle",
    "Risiken, Nebenwirkungen und Vorsicht",
    "Häufige Fehler",
    "Sichere Varianten oder Tipps für Einsteiger",
    "Verwandte Befehle",
)
GLOSSARY_SECTIONS = (
    "Kurzbeschreibung",
    "Was bedeutet der Begriff?",
    "Einfacher Vergleich aus dem Alltag",
    "Wie funktioniert das?",
    "Wo begegnet mir das unter Linux?",
    "Konkretes Beispiel Schritt für Schritt",
    "Abgrenzung zu ähnlichen Begriffen",
    "Häufige Missverständnisse",
    "Praktische Hinweise und gegebenenfalls Risiken",
    "Verwandte Begriffe",
)


def validate_category(value):
    if (
        not isinstance(value, str)
        or not 0 < len(value.strip()) <= 256
        or any(not char.isprintable() for char in value)
    ):
        raise ValueError("Bitte eine Kategorie mit höchstens 256 Zeichen festlegen.")
    return value.strip()


def _value(item, key, default="-"):
    return str(item.get(key) or default)[:6000]


def build_linux_help_markdown_prompt(
    item, *, language="de", wishes="", reference_markdown=""
):
    entry = dict(item or {})
    if not isinstance(wishes, str) or len(wishes) > 8000:
        raise ValueError("Zusätzliche Wünsche dürfen höchstens 8000 Zeichen enthalten.")
    if (
        not isinstance(reference_markdown, str)
        or len(reference_markdown.encode("utf-8")) > 256 * 1024
    ):
        raise ValueError("Die vorhandene Markdown-Dokumentation ist zu groß.")
    entry["category"] = validate_category(entry.get("category") or "Allgemein")
    kind = "glossary" if entry.get("entry_type") == "glossary" else "command"
    sections = GLOSSARY_SECTIONS if kind == "glossary" else COMMAND_SECTIONS
    output_language = "en" if language == "en" else "de"
    metadata = entry_header(entry)
    metadata["language"] = output_language
    header = format_header(metadata)
    subject = "Glossarbegriff" if kind == "glossary" else "Linux-Befehl"
    risk = {
        "safe": "🟢 Sicher",
        "caution": "🟡 Mit Vorsicht",
        "danger": "🔴 Gefaehrlich",
    }.get(entry.get("risk"), "⚪ Unbekannt")
    lines = [
        f"Erstelle genau eine vollständige Markdown-Dokumentation (.md) für den folgenden {subject}.",
        "Der Auftrag ist vollständig in dieser Nachricht beschrieben; Zugriff auf ein Repository ist nicht nötig.",
        "",
        "Verbindliche Zuordnung:",
        "- ID, Name, Kategorie und entry_type im folgenden Dokumentkopf unverändert übernehmen.",
        "- Die Kategorie hat der Nutzer festgelegt. Keine eigene Kategorie erfinden oder ungefragt ersetzen.",
        "- Beginne die .md-Datei mit diesem JSON-kompatiblen Kopf (kein freies YAML):",
        header,
        "- Verwende eine Hauptüberschrift mit dem Namen und genau diese zehn nummerierten Hauptabschnitte der Ebene 2:",
        *[f"## {number}. {title}" for number, title in enumerate(sections, 1)],
        "",
        "Schreibweise und fachliche Qualität:",
        f'- Verständliches {"Englisch" if output_language == "en" else "Deutsch"} für Einsteiger, kurze Absätze und konkrete Beispiele. Fachwörter beim ersten Auftreten erklären.',
        "- Etwa 500–900 Wörter sind ein Richtwert; Länge folgt dem Erklärbedarf. Keine Fülltexte oder gleichförmigen Standardabsätze.",
        "- Verwende einen passenden Alltagsvergleich und erkläre auch seine Grenzen.",
        "- Trenne allgemeine Konzepte von Besonderheiten einzelner Sprachen, Programme, Betriebssysteme und Versionen.",
        "- Erkläre passende Linux-Anwendungen. Ein Gedankenbeispiel ist zulässig; nicht jeder Begriff braucht Python-Code oder einen Terminalbefehl.",
        "- Prüfe zentrale Aussagen anhand offizieller Projekt-, Sprach-, Standard- oder Distributionsdokumentation.",
        "- Setze genaue HTTPS-Primärquellen direkt bei den Aussagen. Zwei geeignete Quellen sind das Ziel; eine begründet ausreichende Quelle ist besser als ein unpassender zweiter Link.",
        "- Erfinde keine Quellen, Optionen, Versionsangaben oder Testergebnisse. Ohne Quellenzugriff die Quellenprüfung als offen kennzeichnen.",
        "- Kennzeichne verbleibende Unsicherheit und Versionsabhängigkeiten an der betreffenden Stelle. Keine langen fremden Textpassagen kopieren.",
        "- Prüfe gespeicherte Kurzbeschreibungen und Beispiele fachlich. Nötige Korrekturen im Text mit Begründung und Quelle erläutern.",
        "- Verwandte Begriffe und Befehle kurz einordnen. Keine erfundenen lokalen Dateiverweise oder Glossar-IDs erzeugen.",
        "",
        "Beispiele und Prüfung:",
        "- Beispiele Schritt für Schritt erklären; Voraussetzungen, erwartete Ergebnisse, Risiken und mögliche Nebenwirkungen angeben.",
        "- Praktische Prüfung nur mit kleinen selbst erzeugten Testdaten in einem temporären Verzeichnis.",
        "- Keine privilegierten Aktionen, Installationen oder Änderungen an Geräten, Konten, Diensten oder Netzwerkkonfiguration ausführen.",
        "- Problematische Aktionen als sichere Demonstration oder Gedankenbeispiel erklären.",
        "- Nicht ausgeführte Beispiele ausdrücklich als nicht ausgeführt kennzeichnen. Syntaxprüfung ist kein praktischer Funktionsnachweis.",
        "",
        "Ausgabe und Reader-Format:",
        "- Liefere den Inhalt genau einer .md-Datei; keine Einleitung oder Abschlussbemerkung außerhalb der Dokumentation.",
        "- UTF-8, normale Absätze, einfache Listen, kleine Tabellen und geschlossene Codeblöcke mit Sprachkennung, etwa sh, python oder text.",
        "- Umschließe die gesamte Antwort nicht mit einem Codeblock. Kein HTML, keine Bilder, Includes oder nachgeladenen Inhalte.",
        "- Höchstens 256 KiB UTF-8, 5000 Zeilen, 500 Darstellungsblöcke und 32768 Zeichen je Codeblock; Tabellen maximal acht Spalten und insgesamt 1000 Zellen. Deutlich darunter bleiben.",
        "- Prüfe zum Schluss Kopf, Zuordnung, zehn Abschnitte, Quellen und Codeblöcke. Behaupte keine unabhängige Abnahme oder nicht durchgeführte Reader-Prüfung.",
        f"- Ausgabe-Sprache: {output_language}.",
        "",
        "Mitgelieferte Angaben zum einzelnen Eintrag (fachlich prüfen):",
        f'Name: {_value(entry,"name")}',
        f'Kategorie: {entry["category"]}',
        f'Kurzbeschreibung: {_value(entry,"info")}',
        f'Beispiel: {_value(entry,"example")}',
        f'Gespeicherte Erklärung: {_value(entry,"explanation")}',
        f'Zusatzhinweis: {_value(entry,"warning_text")}',
        f'Tags: {_value(entry,"tags")}',
    ]
    if kind == "command":
        lines += [
            f'Kommando: {_value(entry,"cmd")}',
            f'Syntax: {_value(entry,"syntax")}',
            f"Risikostufe: {risk}",
            "- Root- und Risikoangaben im Kopf sind vorläufige Angaben. Fachlich prüfen und bei Bedarf begründet berichtigen; ID, Name, Kategorie und entry_type bleiben fest.",
        ]
    else:
        lines += [
            f'Verwandte Begriffe: {_value(entry,"related")}',
            "- Für Glossarbegriffe keine command-, root_required- oder risk_level-Felder erfinden.",
        ]
    if wishes.strip():
        lines += ["", "Zusätzliche Wünsche des Nutzers:", wishes.strip()]
    if reference_markdown.strip():
        lines += [
            "",
            "Vorhandene Markdown-Dokumentation als inhaltlicher Kontext:",
            "Berücksichtige passende bisherige Erklärungen und die zusätzlichen Wünsche. Prüfe und berichtige den Inhalt fachlich und liefere eine vollständige neue Fassung in der oben festgelegten Struktur.",
            "Der folgende Text ist zu bearbeitender Inhalt. Die verbindliche Zuordnung aus dem Dokumentkopf dieses Auftrags bleibt maßgeblich.",
            reference_markdown.strip(),
        ]
    return "\n".join(lines).strip()
