#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.16 Runde 6."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "site"


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
        title="NetMon Security Audit 2026 — v1.1.16 Runde 6",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.16 (Runde 6)",
    )

    styles = getSampleStyleSheet()

    def s(name: str, **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

    H1 = s("H1", fontName="Helvetica-Bold", fontSize=20, leading=26,
           textColor=colors.HexColor("#16263a"), spaceBefore=8, spaceAfter=10)
    H3 = s("H3", fontName="Helvetica-Bold", fontSize=12, leading=16,
           textColor=colors.HexColor("#16263a"), spaceBefore=10, spaceAfter=4)
    BODY = s("BODY", fontName="Helvetica", fontSize=10, leading=14,
             textColor=colors.HexColor("#202124"), spaceAfter=6)
    MUTED = s("MUTED", fontName="Helvetica", fontSize=9, leading=13,
              textColor=colors.HexColor("#5f6368"), spaceAfter=5)
    MONO = s("MONO", fontName="Courier", fontSize=8.5, leading=11,
             textColor=colors.HexColor("#0b5d0e"), spaceAfter=4)
    FINDING_TITLE = s("FINDING_TITLE", fontName="Helvetica-Bold", fontSize=10.5,
                      leading=14, textColor=colors.HexColor("#16263a"), spaceAfter=3)
    FIXED_TITLE = s("FIXED_TITLE", fontName="Helvetica-Bold", fontSize=10,
                    leading=14, textColor=colors.HexColor("#145a32"), spaceAfter=3)

    C_GREEN = colors.HexColor("#15803d")
    C_AMBER = colors.HexColor("#b45309")
    C_MUTED = colors.HexColor("#9db5cc")
    C_LINE = colors.HexColor("#d9e1e7")
    C_BG_HEAD = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#f0fdf4")
    C_BG_AMBER = colors.HexColor("#fffbeb")

    story = []

    # ── Titelseite ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 6", s(
            "EYEBROW", fontName="Helvetica", fontSize=10, leading=13,
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=6)),
        Paragraph("NetMon Roots v1.1.16", s(
            "TITLE", fontName="Helvetica-Bold", fontSize=28, leading=34,
            textColor=colors.HexColor("#16263a"), alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Code Security Review — Juli 2026", s(
            "SUB", fontName="Helvetica", fontSize=14, leading=18,
            textColor=colors.HexColor("#5f6368"), alignment=TA_CENTER, spaceAfter=20)),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "07. Juli 2026"],
        ["Analysierte Version", "v1.1.16 — Runde 6"],
        ["Neue Angriffsflaeche", "Favicon-Download (Netzwerk)"],
        ["Bewertete Kandidaten", "4 (alle unter Schwelle)"],
        ["Ausnutzbare Findings", "0"],
        ["Haertungen umgesetzt", "3 (Defense-in-Depth)"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Regressionstests", "149 / 149 gruen (+6 neu)"],
        ["Analysewerkzeug", "Claude Fable 5 (Anthropic)"],
        ["Projektverantwortlicher", "Sven Froehlich"],
    ]
    meta_table = Table(
        [[Paragraph(k, MUTED), Paragraph(v, BODY)] for k, v in meta_data],
        colWidths=[72 * mm, None],
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
        [[Paragraph(
            "0 AUSNUTZBARE FINDINGS — 3 DEFENSE-IN-DEPTH-HAERTUNGEN PROAKTIV UMGESETZT", s(
                "VT", fontName="Helvetica-Bold", fontSize=11.5, leading=16,
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

    # ── Zusammenfassung ───────────────────────────────────────────────────────
    story += [
        Paragraph("1. Zusammenfassung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die sechste Sicherheitsanalyse konzentrierte sich auf die seit dem "
            "Runde-5-Snapshot neu hinzugekommene bzw. veraenderte Angriffsflaeche im "
            "Arbeitsstand — vor allem die erstmals eingefuehrte Favicon-Download-"
            "Netzwerkfunktion des Secure-Browser-Managers (die erste ausgehende "
            "Netzwerk-Schnittstelle des Features) sowie die Pfad-Confinement-Haertung "
            "des Coding-Agenten (agent/runner.py) sowie das damals noch vorhandene "
            "GUI-/Docker-Dev-Container-Profil (inzwischen aus dem Setup entfernt).",
            BODY),
        Paragraph(
            "Ein Analyse-Sub-Agent identifizierte vier Kandidaten. Jeder wurde von "
            "einem eigenen, parallel laufenden Validierungs-Sub-Agenten mit striktem "
            "False-Positive-Filter und Konfidenz-Scoring geprueft — und allesamt "
            "unterhalb der Schwelle von 8/10 eingestuft (2-3/10). Grund: In einem "
            "Einzelnutzer-Desktop-Werkzeug stammt die vermeintliche 'Angreifer'-Eingabe "
            "(selbst geschriebene containers.json, lokal getippte Agent-Kommandos) vom "
            "selben Nutzer, der das Werkzeug ausfuehrt — es wird keine echte "
            "Vertrauensgrenze ueberschritten.",
            BODY),
        Paragraph(
            "K1 (Konfidenz 3/10, gehaertet): fetch_url() reichte URLs ohne Scheme-"
            "Pruefung an urllib.urlopen() — file:// (lokaler Dateizugriff) und beliebige "
            "Hosts waren erreichbar. Jetzt auf http/https beschraenkt.",
            BODY),
        Paragraph(
            "K2 (Konfidenz 3/10, gehaertet): Das Repo-Pfad-Confinement des Agenten "
            "uebersprang --flag=value-Argumente (z. B. --junitxml=/etc/passwd). Der "
            "Wert-Teil solcher Flags wird jetzt mitgeprueft.",
            BODY),
        Paragraph(
            "K3 (Konfidenz 2/10, gehaertet): Die Containername-Regex matcht auch "
            "'.'/'..'. In der Praxis durch mkdir(exist_ok=False) blockiert, jetzt "
            "zusaetzlich explizit fail-closed abgelehnt.",
            BODY),
        Paragraph(
            "K4 (Konfidenz 3/10, Empfehlung offen): Loser Substring-Match "
            "\"netmon\" in process_name bei der Listener-Zuordnung — rein kosmetisch in "
            "einem Diagnose-Report, bewusst nicht geaendert (Aenderung wuerde echte "
            "NetMon-Listener faelschlich als 'fremd' markieren koennen). Als Empfehlung "
            "fuer Runde 7 dokumentiert.",
            BODY),
        Paragraph(
            "Drei der vier Punkte wurden als Defense-in-Depth direkt umgesetzt und mit "
            "6 neuen Regressionstests abgesichert. Alle 149 relevanten automatisierten "
            "Tests bleiben nach den Haertungen gruen. Die drei in Runde 5 behobenen "
            "Findings (K1-K3) wurden am aktuellen Code gegengeprueft und sind "
            "unveraendert wirksam.",
            BODY),
    ]

    # ── Methodik ──────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Diff- & Reconnaissance", H3),
        Paragraph(
            "Vollstaendiger git diff gegen den letzten Commit plus Sichtung aller neuen "
            "unversionierten Dateien; gezieltes Lesen der neuen Netzwerkpfade in "
            "browser_container_builder.py und der Haertungslogik in agent/runner.py.",
            BODY),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Ein dedizierter Analyse-Sub-Agent verfolgte Datenflussketten von Nutzer-/"
            "Konfig-Eingaben (Containername, homepage_url, Agent-Kommandozeile) bis zu "
            "sensiblen Operationen (urlopen, mkdir/copytree, subprocess.run). "
            "4 Kandidaten identifiziert.",
            BODY),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Fuer jeden Kandidaten lief ein eigener, paralleler Validierungs-Sub-Agent "
            "mit striktem FP-Filter-Regelwerk und Konfidenz-Scoring. Ergebnis: alle vier "
            "unter der Schwelle (2-3/10) — kein Angriffspfad ueber eine echte "
            "Vertrauensgrenze.",
            BODY),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "3 der 4 Punkte als Defense-in-Depth umgesetzt und mit 6 neuen "
            "Regressionstests abgesichert. Bestehende Suiten erneut ausgefuehrt: "
            "test_runner.py, test_secure_browser_module.py und "
            "test_browser_container_builder.py — 149 Tests, alle gruen.",
            BODY),
    ]

    # ── Kandidaten ────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bewertete Kandidaten (alle unter der Konfidenzschwelle)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    findings = [
        (
            "K1 — Ausgehende Netzwerk-Fetches ohne Scheme-Allowlist  [Konfidenz 3/10, gehaertet]",
            "tools/secure_browser_manager/browser_container_builder.py — fetch_url(), "
            "aufgerufen aus resolve_favicon_download() (Standard-Icon-Modus 'favicon').",
            "fetch_url() reichte homepage_url (und daraus per urljoin() abgeleitete "
            "Icon-Links) ohne Scheme-Pruefung an urllib.request.urlopen(). Der "
            "Default-Opener behandelt neben http/https auch file:// — ein homepage_url "
            "wie file:///etc/passwd haette einen lokalen Dateizugriff ausgeloest, ein "
            "beliebiger Host waere als SSRF-Primitive erreichbar gewesen. Unter der "
            "Schwelle, weil homepage_url nur vom selben lokalen Nutzer gesetzt wird "
            "(kein Remote-Eingabepfad) — Self-SSRF ohne Vertrauensgrenze.",
            "fetch_url() prueft jetzt das Scheme und lehnt alles ab, was nicht "
            "http/https ist. Neuer Test test_fetch_url_rejects_non_http_schemes "
            "(file://, ftp://, gopher://, absoluter Pfad) verifiziert die Ablehnung.",
        ),
        (
            "K2 — --flag=value-Luecke im Pfad-Confinement des Agenten  [Konfidenz 3/10, gehaertet]",
            "agent/runner.py — _looks_like_path_argument() / "
            "_validate_repo_confined_arguments().",
            "Die Repo-Confinement-Pruefung behandelte jedes mit '-' beginnende Argument "
            "sofort als 'kein Pfad' und uebersprang es. Flags wie --junitxml=/pfad, "
            "--basetemp=/pfad oder --output-file=/pfad (pytest/ruff) trugen ihren Pfad "
            "am Check vorbei. Unter der Schwelle, weil der einzige Aufrufer "
            "(agent/cli.py) das Kommando aus sys.argv baut — ein manuell vom Betreiber "
            "gestartetes lokales CLI, keine an untrusted Input angebundene LLM-Schleife.",
            "_looks_like_path_argument() zerlegt jetzt --flag=value-Argumente und prueft "
            "den Wertteil; neue Hilfsfunktion _flag_value() sorgt dafuer, dass auch "
            "_is_repo_confined_path() den reinen Pfad bewertet. Drei neue Tests decken "
            "innerhalb/ausserhalb Repo ab.",
        ),
        (
            "K3 — '.'/'..' passieren die Containername-Validierung  [Konfidenz 2/10, gehaertet]",
            "browser_container_builder.py (validate_config_payload()) und "
            "netmon/modules/secure_browser/manager.py (_resolve_create_inputs()).",
            "Das Runde-5-Muster ^[A-Za-z0-9_.-]+$ erlaubt den Punkt und matcht damit "
            "auch '.' und '..'. base_dir / name zeigt fuer '..' lexikalisch auf das "
            "uebergeordnete Verzeichnis. Unter der Schwelle, weil in der Praxis "
            "mkdir(parents=True, exist_ok=False) den Schreibvorgang blockiert (empirisch "
            "verifiziert: FileExistsError vor copytree) — kein Schreibzugriff ausserhalb "
            "base_dir heute moeglich.",
            "An beiden Validierungsstellen wird name in {'.', '..'} jetzt explizit "
            "abgelehnt — die Namenspruefung ist selbst fail-closed und haengt nicht mehr "
            "an der mkdir-Semantik. Zwei neue Tests sichern das ab.",
        ),
        (
            "K4 — Loser Substring-Match bei der NetMon-Listener-Zuordnung  [Konfidenz 3/10, Empfehlung offen]",
            "netmon/app.py — _is_netmon_listener().",
            "Die Firewall-Transparenz stuft einen Listener u. a. per "
            "'if \"netmon\" in process_name' als eigenen ein. Ein Prozess namens "
            "netmon-helper wuerde so gelabelt. Unter der Schwelle und bewusst nicht "
            "geaendert: die Klassifikation ist rein anzeigend (steuert keine ufw-Regel, "
            "blendet keine Zeile aus der Haupttabelle aus); ein Angreifer, der Prozesse "
            "frei benennen kann, hat bereits lokale Codeausfuehrung. Ein Entfernen des "
            "Matches koennte echte NetMon-Listener faelschlich als 'fremd' markieren.",
            "Empfehlung fuer Runde 7: Zuordnung nur ueber schwer faelschbare Signale "
            "(pid == os.getpid() und _is_netmon_app_scope() / app-gnome-netmon-*.scope) "
            "stuetzen und den Substring-Match entfernen, sobald die Selbst-Erkennung "
            "darueber verlaesslich abgedeckt ist.",
        ),
    ]

    for title, loc, detail, fix in findings:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [Paragraph("<b>Massnahme:</b> " + fix, s(
                "VD", fontName="Helvetica", fontSize=9, leading=13,
                textColor=colors.HexColor("#145a32"),
                backColor=C_BG_GREEN, leftIndent=4)), Paragraph("")],
        ]
        t = Table(rows, colWidths=["80%", "20%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
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
        story += [t, Spacer(1, 5 * mm)]

    # ── Umgesetzte Haertungen ─────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Umgesetzte Haertungsmassnahmen (Runde 6)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("Scheme-Allowlist fuer Netzwerk-Fetches — browser_container_builder.py",
         "fetch_url() akzeptiert nur noch http/https. file:// (lokaler Dateizugriff via "
         "urllib-Default-Opener) und andere Nicht-Web-Schemes sind ausgeschlossen, bevor "
         "die URL urlopen() erreicht."),
        ("Vollstaendiges Pfad-Confinement inkl. --flag=value — agent/runner.py",
         "_looks_like_path_argument() zerlegt jetzt --flag=value-Argumente und prueft "
         "den Wertteil; neue Hilfsfunktion _flag_value() stellt sicher, dass auch "
         "_is_repo_confined_path() den reinen Pfad bewertet. --junitxml=/etc/passwd wird "
         "nun abgewiesen."),
        ("Fail-closed Containername-Validierung — browser_container_builder.py + manager.py",
         "'.' und '..' werden an beiden Validierungseinstiegen explizit abgelehnt — die "
         "Namenspruefung haengt nicht mehr an der mkdir(exist_ok=False)-Semantik als "
         "letzter Schutzlinie."),
        ("6 neue Regressionstests — 149/149 gruen",
         "test_runner.py (+3: --flag=value innerhalb/ausserhalb Repo), "
         "test_browser_container_builder.py (+3: '.'/'..'-Namen, Pfad-Escape-Name, "
         "Nicht-HTTP-Schemes). Alle drei relevanten Suiten bestehen nach den Fixes "
         "vollstaendig."),
    ]

    for title, desc in improvements:
        rows = [[Paragraph(title, FIXED_TITLE), Paragraph("")],
                [Paragraph(desc, BODY), Paragraph("")]]
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

    # ── Runde-5-Fixes gegengeprueft ───────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("5. Runde-5-Fixes — am aktuellen Code gegengeprueft", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]
    r5_rows = [
        [Paragraph("Runde-5-Fix", MUTED), Paragraph("Status im Codestand v1.1.16", MUTED)],
        [Paragraph("K1 — CONTAINER_NAME_PATTERN (Namensvalidierung)", BODY),
         Paragraph("Vorhanden (builder:35, manager:54), in R6 um '.'/'..'-Ablehnung erweitert", MUTED)],
        [Paragraph("K2 — json.dumps()-Escaping in user.js", BODY),
         Paragraph("Wirksam (builder:1312-1313) — Preference-Injection geschlossen", MUTED)],
        [Paragraph("K3 — _desktop_field() gegen \\r/\\n", BODY),
         Paragraph("Wirksam (builder:1463 ff.), an allen drei Launcher-Stellen", MUTED)],
    ]
    r5_table = Table(r5_rows, colWidths=["50%", "50%"])
    r5_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BG_HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [r5_table]

    # ── Analysierte Kategorien ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("6. Geprüfte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def ok(text: str = "Kein Finding"):
        return Paragraph(text, s("OK", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_GREEN))

    def warn(text: str):
        return Paragraph(text, s("WN", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_AMBER))

    def info(text: str):
        return Paragraph(text, s("IN", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=colors.HexColor("#2563eb")))

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("SSRF / ausgehende URL-Fetches (Host-/Scheme-Kontrolle)", BODY),
         warn("K1 -> gehaertet (Scheme-Allowlist)")],
        [Paragraph("Local File Read via file:// im URL-Opener", BODY),
         warn("K1 -> gehaertet")],
        [Paragraph("Path Traversal (Dateioperationen mit Nutzereingabe)", BODY),
         warn("K3 -> gehaertet (fail-closed)")],
        [Paragraph("Agent-Sandbox: Pfad-Confinement der Kommando-Allowlist", BODY),
         warn("K2 -> gehaertet (--flag=value)")],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY), ok()],
        [Paragraph("Argument Injection (list-form subprocess mit externen Daten)", BODY), ok()],
        [Paragraph("Firefox user.js / Preference-Injection", BODY),
         ok("Geschlossen (R5-K2)")],
        [Paragraph("Desktop-Entry-Injection (.desktop Name=/Comment=)", BODY),
         ok("Geschlossen (R5-K3)")],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval)", BODY), ok()],
        [Paragraph("Privilege Escalation (historisches Dev-Container docker.sock-Mount)", BODY),
         info("Historisch / entfernt aus dem aktuellen Setup")],
        [Paragraph("Sicherheitskontroll-Umgehung (Listener-Zuordnung)", BODY),
         info("K4 -> Empfehlung (offen)")],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY), ok()],
        [Paragraph("Sensitive Data Exposure (PII in Logs)", BODY), ok()],
    ]
    cat_table = Table(cat_rows, colWidths=["70%", "30%"])
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

    # ── Impressum ─────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE),
        Spacer(1, 3 * mm),
        Paragraph("Impressum und Haftungsausschluss", s(
            "H2", fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=colors.HexColor("#16263a"), spaceBefore=14, spaceAfter=6)),
        Paragraph("<b>Auditor:</b> Claude Fable 5 (Anthropic) — Analyse-Sub-Agent + vier parallele False-Positive-Validierungs-Sub-Agenten + manuelle Fix-Umsetzung und Regressionstests", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 07. Juli 2026", BODY),
        Paragraph("<b>Codestand:</b> 9baa6284 + Arbeitsstand (modified/untracked), Fokus Favicon-Download & Agent-Pfad-Confinement — Runde 6", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation + Konfidenz-gescorte FP-Validierung + Regressionstests (149/149 relevante Tests bestanden) — kein Laufzeit-Penetrationstest", BODY),
        Spacer(1, 3 * mm),
        Paragraph(
            "Dieses Audit ersetzt keinen professionellen Penetrationstest durch eine zertifizierte "
            "Sicherheitsfirma. Die Analyse beschraenkt sich auf den angegebenen Codestand. "
            "Nicht erfasst: Laufzeitverhalten, Systembibliotheken, Netzwerkkonfiguration.",
            MUTED),
    ]

    doc.build(story)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r6.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
