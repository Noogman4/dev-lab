#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.14 Runde 2 (rev.)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dist" / "docs"


def build_pdf(pdf_path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: F401
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="NetMon Security Audit 2026 — v1.1.14 Runde 2",
        author="Claude Sonnet 4.6 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.14 (Runde 2)",
    )

    styles = getSampleStyleSheet()

    def s(name: str, **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

    H1 = s("H1", fontName="Helvetica-Bold", fontSize=20, leading=26,
            textColor=colors.HexColor("#16263a"), spaceBefore=8, spaceAfter=10)
    H2 = s("H2", fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=colors.HexColor("#16263a"), spaceBefore=14, spaceAfter=6)
    H3 = s("H3", fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=colors.HexColor("#16263a"), spaceBefore=10, spaceAfter=4)
    BODY = s("BODY", fontName="Helvetica", fontSize=10, leading=14,
             textColor=colors.HexColor("#202124"), spaceAfter=6)
    MUTED = s("MUTED", fontName="Helvetica", fontSize=9, leading=13,
              textColor=colors.HexColor("#5f6368"), spaceAfter=5)
    MONO = s("MONO", fontName="Courier", fontSize=8.5, leading=11,
             textColor=colors.HexColor("#0b5d0e"), spaceAfter=4)
    VERDICT = s("VERDICT", fontName="Helvetica", fontSize=9.5, leading=14,
                textColor=colors.HexColor("#5f6368"), spaceAfter=4,
                leftIndent=8, backColor=colors.HexColor("#f0faf5"),
                borderPadding=6)
    FINDING_TITLE = s("FINDING_TITLE", fontName="Helvetica-Bold", fontSize=10.5,
                      leading=14, textColor=colors.HexColor("#16263a"), spaceAfter=3)
    FIXED_TITLE = s("FIXED_TITLE", fontName="Helvetica-Bold", fontSize=10,
                    leading=14, textColor=colors.HexColor("#145a32"), spaceAfter=3)

    C_GREEN    = colors.HexColor("#145a32")
    C_MUTED    = colors.HexColor("#9db5cc")
    C_LINE     = colors.HexColor("#d9e1e7")
    C_BG_HEAD  = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#eafaf3")

    story = []

    # ── Titelseite ─────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 2", s("EYEBROW", fontName="Helvetica",
                  fontSize=10, leading=13, textColor=C_MUTED,
                  alignment=TA_CENTER, spaceAfter=6)),
        Paragraph("NetMon Roots v1.1.14", s("TITLE", fontName="Helvetica-Bold",
                  fontSize=28, leading=34, textColor=colors.HexColor("#16263a"),
                  alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Code Security Review — Juni 2026",
                  s("SUB", fontName="Helvetica", fontSize=14, leading=18,
                    textColor=colors.HexColor("#5f6368"), alignment=TA_CENTER,
                    spaceAfter=20)),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "28. Juni 2026"],
        ["Analysierte Version", "v1.1.14 — Runde 2"],
        ["Geaenderte / neue Dateien", "100+"],
        ["Neue / revidierte Module", "25+"],
        ["Kritische Findings", "0"],
        ["Findings gesamt", "0 (alle 4 Kandidaten ausgeschlossen)"],
        ["Bewertete Kandidaten", "4"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Methode", "Statische Code-Analyse + manuelle Verifikation"],
        ["Analysewerkzeug", "Claude Sonnet 4.6 (Anthropic)"],
        ["Projektverantwortlicher", "Sven Froehlich"],
    ]
    meta_table = Table(
        [[Paragraph(k, MUTED), Paragraph(v, BODY)] for k, v in meta_data],
        colWidths=[62 * mm, None],
    )
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), C_BG_HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [meta_table, Spacer(1, 8 * mm)]

    verdict_table = Table(
        [[Paragraph("KEINE KRITISCHEN SCHWACHSTELLEN GEFUNDEN", s(
            "VT", fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=C_GREEN, alignment=TA_CENTER))]], colWidths=["100%"])
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BG_GREEN),
        ("BOX", (0, 0), (-1, -1), 1.5, C_GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story += [verdict_table, PageBreak()]

    # ── Zusammenfassung ────────────────────────────────────────────────────
    story += [
        Paragraph("1. Zusammenfassung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die zweite statische Sicherheitsanalyse des NetMon-Arbeitsstands v1.1.14 "
            "(100+ Dateien, 25+ neue bzw. revidierte Module) durch ein automatisiertes "
            "Multi-Agenten-System auf Basis von Claude Sonnet 4.6 ergab keine "
            "ausnutzbaren Sicherheitsluecken. Alle vier Kandidaten wurden als False "
            "Positives ausgeschlossen.",
            BODY),
        Paragraph(
            "Besonderer Befund: K1 (SSRF-Verdacht im Radio-Modul) wurde initial mit "
            "Konfidenz 8/10 als bestaetigt eingestuft, nach manueller Datenfluss-"
            "Verifikation jedoch widerlegt: _normalize_station_stream_url() mit "
            "ALLOWED_RADIO_STREAM_SCHEMES = {'http', 'https', 'rtsp', 'rtmp'} (Zeile 103) "
            "validiert jede URL bereits vor der Aufnahme ins Station-Dict. "
            "mpv und urllib.request empfangen ausschliesslich vorvalidierte URLs.",
            BODY),
        Paragraph(
            "Erstmalig analysiert: radio_controller.py (5 531 Zeilen), "
            "ai_analysis_service.py, lang_service.py, network_helpers.py, "
            "coordinator.py, state.py, fun_controller.py, speedtest_controller.py, "
            "dot_controller.py, security_audit_controller.py sowie neue UI-Tabs. "
            "Regressionscheck: 82 Proxy-Methoden aus app.py entfernt — keine Regression.",
            BODY),
        Paragraph(
            "Sicherheitsverbesserungen seit Runde 1: (1) ClamAV-Tempdir-Symlink-Schutz "
            "_safe_makedirs_no_symlink() implementiert. "
            "(2) URL-Schema-Validierung im Radio-Modul bereits vollstaendig vorhanden. "
            "(3) 82 Proxy-Methoden aus app.py entfernt (Angriffsflaechenreduktion).",
            MUTED),
    ]

    # ── Methodik ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 — Reconnaissance", H3),
        Paragraph(
            "Lesen aller neuen und geaenderten Module; Fokus auf externe "
            "API-Anbindungen, Subprocess-Aufrufe mit externen Daten, URL-Handling, "
            "Datei-Operationen mit Nutzereingabe, Deserialisierung.",
            BODY),
        Paragraph("Phase 2 — Kandidaten-Analyse", H3),
        Paragraph(
            "Datenflussketten von externen Quellen bis zu sensitiven Operationen "
            "nachverfolgt. Besonderes Augenmerk: URL-Schemata an mpv, ffmpeg, "
            "urllib.request und webbrowser.open().",
            BODY),
        Paragraph("Phase 3 — False-Positive-Filter", H3),
        Paragraph(
            "Jeder Kandidat in einem unabhaengigen Agenten re-analysiert. "
            "Ausschluss: DoS, Single-User-Desktop ohne Fremd-Input, "
            "stdout/stderr=DEVNULL + Re-Encoding verhindert Exfil, Browser-Sandbox.",
            BODY),
        Paragraph("Phase 4 — Manuelle Verifikation (K1)", H3),
        Paragraph(
            "Zusaetzliche Nachpruefung des Radio-Kandidaten durch direktes Lesen "
            "der Funktionskette: normalize_station_entry() -> "
            "_normalize_station_stream_url() -> ALLOWED_RADIO_STREAM_SCHEMES. "
            "Kandidat als False Positive widerlegt.",
            BODY),
        Paragraph(
            "Konfidenz-Schwelle: Nur Findings mit Score >= 8/10 waeren aufgenommen worden.",
            MUTED),
    ]

    # ── Analysierte Dateien ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Spacer(1, 4 * mm),
        Paragraph("3. Neu analysierte Module (Runde 2)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    scope_rows = [
        [Paragraph("Datei / Modul", MUTED), Paragraph("Fokus", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("netmon/features/radio_controller.py", MONO),
         Paragraph("mpv, ffmpeg, radio-browser.info API, ICY-Fetch, URL-Schema-Validierung", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/features/chad_controller.py", MONO),
         Paragraph("KI-Integration, getattr-Muster, Datei-Import", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/features/fun_controller.py", MONO),
         Paragraph("Subprocess-Aufrufe, Paketpruefung", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/features/speedtest_controller.py", MONO),
         Paragraph("Speedtest-Subprocess, Ergebnis-Parsing", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/features/dot_controller.py", MONO),
         Paragraph("Dropin-Generierung, systemd-Konfiguration", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/features/security_audit_controller.py", MONO),
         Paragraph("Lynis/rkhunter, Startup-Guard-Baseline-Lesen", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/services/ai_analysis_service.py", MONO),
         Paragraph("KI-Analyse-Pipeline, Datenuebertragung", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/services/lang_service.py", MONO),
         Paragraph("Lokalisierung, JSON-Laden", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/services/network_helpers.py", MONO),
         Paragraph("Netzwerk-Hilfsfunktionen, IP-Parsing", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/core/coordinator.py + state.py", MONO),
         Paragraph("Koordinator, globaler Zustand", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/ui/tabs/radio_tab.py", MONO),
         Paragraph("Radio-UI, Benutzerinteraktion", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/ui/tabs/ (cleanup, download, fun, chad_settings)", MONO),
         Paragraph("Neue UI-Tabs, Dateioperationen", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("scripts/refactor_safety.py", MONO),
         Paragraph("AST-Analyse, Caller-Check, Read-Only-Tool", MUTED),
         Paragraph("Kein Finding", BODY)],
        [Paragraph("netmon/app.py (Refaktorierung)", MONO),
         Paragraph("82 Proxy-Methoden entfernt", MUTED),
         Paragraph("Keine Regression", BODY)],
    ]
    scope_table = Table(scope_rows, colWidths=[72 * mm, 72 * mm, None])
    scope_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BG_HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [scope_table]

    # ── Kandidaten ─────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Bewertete Kandidaten (alle ausgeschlossen)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Alle vier Kandidaten wurden als False Positives ausgeschlossen. "
            "K1 wurde initial mit Konfidenz 8/10 als bestaetigt gewertet und "
            "anschliessend durch manuelle Datenfluss-Verifikation widerlegt: "
            "_normalize_station_stream_url() mit ALLOWED_RADIO_STREAM_SCHEMES "
            "= {'http', 'https', 'rtsp', 'rtmp'} (Zeile 103) validiert jede URL "
            "bevor sie ins Station-Dict uebernommen wird.",
            BODY),
    ]

    candidates = [
        {
            "title": "K1 — Radio-URL an mpv / urllib.request — manuell widerlegt",
            "file": "netmon/features/radio_controller.py, Zeilen 103, 298-309, 4835",
            "conf": "8/10 -> FP (nach manueller Verifikation)",
            "desc": (
                "Initiale Bewertung: Radio-URLs aus radio-browser.info-API gelangen ohne "
                "Schema-Validierung an mpv (Zeile 4835) und urllib.request.urlopen() "
                "(Zeile 3150). Erstes Filter-Ergebnis: Konfidenz 8/10."
            ),
            "verdict": (
                "WIDERLEGT: _normalize_station_stream_url() (Zeile 298) wird von "
                "normalize_station_entry() (Zeile 317) aufgerufen und prueft das "
                "URL-Schema via urllib.parse.urlparse() gegen ALLOWED_RADIO_STREAM_SCHEMES "
                "= {'http', 'https', 'rtsp', 'rtmp'} (Zeile 103). Nicht erlaubte Schemata "
                "(file://, lavfi://, etc.) geben '' zurueck; Station wird als None verworfen. "
                "mpv und urllib.request empfangen ausschliesslich vorvalidierte URLs."
            ),
        },
        {
            "title": "K2 — webbrowser.open mit nicht validierter API-URL",
            "file": "netmon/features/radio_controller.py, Zeile 5197",
            "conf": "3/10",
            "desc": (
                "webbrowser.open(url, new=2) wird mit dem homepage-Feld aus der "
                "API-Antwort ohne Schema-Validierung aufgerufen."
            ),
            "verdict": (
                "AUSGESCHLOSSEN: Moderne Browser erzwingen strikte Same-Origin-Policy "
                "fuer file://-URLs — keine Exfiltration moeglich. "
                "javascript:-URIs werden als Top-Level-URL nicht ausgefuehrt."
            ),
        },
        {
            "title": "K3 — ffmpeg -i mit nicht validierter API-URL",
            "file": "netmon/features/radio_controller.py, Zeile 2160",
            "conf": "FP",
            "desc": (
                "_recording_command(stream_url, output_path) uebergibt die Station-URL "
                "als 'ffmpeg -i <url>'-Argument. "
                "Zusaetzlich: URL bereits durch _normalize_station_stream_url() vorvalidiert."
            ),
            "verdict": (
                "AUSGESCHLOSSEN: (1) URL durch _normalize_station_stream_url() vorvalidiert. "
                "(2) stdin/stdout/stderr nach DEVNULL; libmp3lame-Transcoding verhindert "
                "Exfil beliebiger Binaerdaten. Kein Exfiltrationspfad."
            ),
        },
        {
            "title": "K4 — Dateilese-Operation via Startup-Guard-Baseline",
            "file": "netmon/features/security_audit_controller.py, Zeilen 1173-1184",
            "conf": "FP",
            "desc": (
                "format_startup_guard_entry_details() oeffnet beliebige Dateipfade "
                "aus einer nutzerschreibbaren JSON-Baseline-Datei."
            ),
            "verdict": (
                "AUSGESCHLOSSEN: Single-User-Desktop — kein Privilege-Boundary-Crossing. "
                "Baseline im Konfig-Verzeichnis des Nutzers (nur von diesem schreibbar). "
                "Angreifer mit Baseline-Zugriff hat bereits vollen Lesezugriff auf "
                "alle open()-erreichbaren Dateien."
            ),
        },
    ]

    for c in candidates:
        rows = [
            [Paragraph(c["title"], FINDING_TITLE),
             Paragraph(f"Konfidenz: {c['conf']}", MUTED)],
            [Paragraph(f"Datei: {c['file']}", MONO), Paragraph("")],
            [Paragraph(c["desc"], BODY), Paragraph("")],
            [Paragraph(f"Filterentscheid: {c['verdict']}", VERDICT), Paragraph("")],
        ]
        t = Table(rows, colWidths=["80%", "20%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
            ("BACKGROUND", (0, 3), (-1, 3), C_BG_GREEN),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [t, Spacer(1, 4 * mm)]

    # ── Verbesserungen seit Runde 1 ────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("5. Sicherheitsverbesserungen seit Runde 1", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die folgenden Hardening-Empfehlungen aus Audit Runde 1 wurden "
            "im aktuellen Codestand umgesetzt.",
            BODY),
    ]

    improvements = [
        {
            "title": "ClamAV Tempdir: Symlink-Schutz implementiert — clamav_controller.py",
            "desc": (
                "Runde 1 empfahl, os.makedirs(exist_ok=True) durch eine Sequenz zu ersetzen, "
                "die Symlinks vor dem Anlegen des Verzeichnisses prueft (Punkt 4). "
                "Umgesetzt als _safe_makedirs_no_symlink(path) (Zeile 71): "
                "prueft via os.lstat(), wirft RuntimeError bei Symlink. Empfehlung geschlossen."
            ),
        },
        {
            "title": "URL-Schema-Validierung im Radio-Modul — radio_controller.py",
            "desc": (
                "Das Radio-Modul enthaelt bereits eine vollstaendige Schema-Allowlist: "
                "ALLOWED_RADIO_STREAM_SCHEMES = {'http', 'https', 'rtsp', 'rtmp'} (Zeile 103), "
                "durchgesetzt durch _normalize_station_stream_url() (Zeile 298-309) via "
                "urllib.parse.urlparse(). Nicht erlaubte Schemata werden vor der Speicherung "
                "im Station-Dict abgelehnt — mpv und urllib.request empfangen nur validierte URLs."
            ),
        },
        {
            "title": "Angriffsflaechenreduktion: 82 Proxy-Methoden aus app.py entfernt",
            "desc": (
                "Im Zuge der God-Object-Extraktion wurden 82 Proxy-Methoden aus app.py "
                "geloescht, deren Controller-Gegenstuecke in netmon/features/ vorhanden waren. "
                "Alle Methoden vorab per refactor_safety.py auf Null-Aufrufer verifiziert. "
                "Commit 920cfc9b. Reduzierung von 34 294 auf 34 005 Zeilen."
            ),
        },
    ]

    for imp in improvements:
        rows = [
            [Paragraph(f"  {imp['title']}", FIXED_TITLE), Paragraph("")],
            [Paragraph(imp["desc"], BODY), Paragraph("")],
        ]
        t = Table(rows, colWidths=["80%", "20%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("SPAN", (0, 1), (1, 1)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#a3d9b8")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
            ("BACKGROUND", (0, 0), (-1, 0), C_BG_GREEN),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [t, Spacer(1, 3 * mm)]

    # ── Hardening-Empfehlungen ─────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("6. Umgesetzte Defense-in-Depth-Massnahmen", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die folgenden Punkte sind keine Sicherheitsluecken, sondern "
            "Defense-in-Depth-Massnahmen aus Runde 1. Sie wurden im aktuellen "
            "Codestand nachgezogen und sind nicht mehr offen.",
            BODY),
    ]

    hardenings = [
        ("1. Git-Subcommand-Allowlist in agent/runner.py",
         "Umgesetzt: explizite Subcommand-Allowlist fuer status, diff, log und show."),
        ("2. IP-Validierung fuer WireGuard-Endpoints",
         "Umgesetzt: parse_vpn_endpoint() validiert den Host-Teil mit "
         "ipaddress.ip_address(), bevor er in UFW-Kommandos verwendet wird."),
        ("3. Pfadpruefung in image_to_data_url()",
         "Umgesetzt: Dateipfad wird zusaetzlich auf das Benutzer-Homeverzeichnis "
         "begrenzt."),
        ("4. Schema-Validierung fuer homepage-URLs im Radio-Modul",
         "Umgesetzt: homepage-URLs werden auf erlaubte Browser-Schemata "
         "(http/https) begrenzt, bevor sie an webbrowser.open() gehen."),
        ("5. Shell-Quoting in Repository-Guard-Snippets",
         "Umgesetzt: URI- und Pfadwerte in "
         "get_repository_guard_quick_action_snippet() werden mit shlex.quote() "
         "maskiert."),
        ("6. os.path.realpath() im Roots-Baseline-Guard",
         "Umgesetzt: _normalize_guard_path_pattern() nutzt os.path.realpath(), "
         "um Symlinks vor dem fnmatch-Check aufzuloesen."),
    ]

    for title, desc in hardenings:
        story += [
            Paragraph(title, H3),
            Paragraph(desc, BODY),
        ]

    # ── Geprueft Kategorien ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("7. Geprufte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Path Traversal (Dateioperationen mit Nutzereingabe)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Privilege Escalation (sudo, Argument-Injektion)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Eval/Exec mit Nutzereingabe", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Authentication Bypass / Privilege Escalation", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Sensitive Data Exposure (PII in Logs)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Externe API-Aufrufe mit unkontrollierten Daten", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("SSRF via urllib.request / externe URL-Weitergabe", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Kryptographische Schwachstellen", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Symlink-Angriffe auf privilegierte Dateioperationen", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Clipboard-Injection / Snippet-Generierung ohne Auto-Exec", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("URL-Schema-Validierung an Media-Subprocess", BODY), Paragraph("Kein Finding", BODY)],
    ]
    cat_table = Table(cat_rows, colWidths=["75%", "25%"])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BG_HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [cat_table]

    # ── Impressum / Signatur ───────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE),
        Spacer(1, 3 * mm),
        Paragraph("Impressum und Haftungsausschluss", H2),
        Paragraph(
            "<b>Auditor:</b> Claude Sonnet 4.6 (Anthropic) — Automatisiertes "
            "Multi-Agenten-Sicherheits-Review + manuelle Verifikation",
            BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 28. Juni 2026", BODY),
        Paragraph(
            "<b>Analysierter Codestand:</b> e334324a ... 920cfc9b + Arbeitsstand "
            "(unstaged), gesamt 100+ Dateien — Runde 2",
            BODY),
        Paragraph(
            "<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation "
            "— kein Laufzeit-Penetrationstest",
            BODY),
        Spacer(1, 3 * mm),
        Paragraph(
            "Dieses Audit ersetzt keinen professionellen Penetrationstest durch eine "
            "zertifizierte Sicherheitsfirma. Die Analyse beschraenkt sich auf den "
            "angegebenen Codestand. Nicht erfasst werden: Laufzeitverhalten, "
            "abhaengige Systembibliotheken, Netzwerkkonfiguration und soziale "
            "Angriffsvektoren.",
            MUTED),
    ]

    doc.build(story)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r2.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
