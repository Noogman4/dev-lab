#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.14 Runde 3 (rev.)."""

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
        title="NetMon Security Audit 2026 — v1.1.14 Runde 3 (rev.)",
        author="Claude Sonnet 4.6 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.14 (Runde 3 rev.)",
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
    MONO_DARK = s("MONO_DARK", fontName="Courier", fontSize=8, leading=11,
                  textColor=colors.HexColor("#e2e8f0"),
                  backColor=colors.HexColor("#0f172a"), spaceAfter=4)
    FINDING_TITLE = s("FINDING_TITLE", fontName="Helvetica-Bold", fontSize=10.5,
                      leading=14, textColor=colors.HexColor("#16263a"), spaceAfter=3)
    FIXED_TITLE = s("FIXED_TITLE", fontName="Helvetica-Bold", fontSize=10,
                    leading=14, textColor=colors.HexColor("#145a32"), spaceAfter=3)

    C_RED      = colors.HexColor("#b91c1c")
    C_AMBER    = colors.HexColor("#b45309")
    C_GREEN    = colors.HexColor("#15803d")
    C_MUTED    = colors.HexColor("#9db5cc")
    C_LINE     = colors.HexColor("#d9e1e7")
    C_BG_HEAD  = colors.HexColor("#eef3f7")
    C_BG_RED   = colors.HexColor("#fef2f2")
    C_BG_AMBER = colors.HexColor("#fffbeb")
    C_BG_GREEN = colors.HexColor("#f0fdf4")

    story = []

    # ── Titelseite ─────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 3", s("EYEBROW", fontName="Helvetica",
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
        ["Analysierte Version", "v1.1.14 — Runde 3"],
        ["Analysierte Module (neu)", "17+"],
        ["Bestaetigte Findings", "1 (MEDIUM)"],
        ["Bewertete Kandidaten", "7"],
        ["Ausgeschlossene Kandidaten", "6 (K1+K2 manuell widerlegt, K4-K7 FP-Filter)"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Methode", "Statische Code-Analyse + manuelle Verifikation"],
        ["Analysewerkzeug", "Claude Sonnet 4.6 (Anthropic)"],
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
        [[Paragraph("1 FINDING BESTAETIGT (MEDIUM) · K1 + K2 MANUELL WIDERLEGT", s(
            "VT", fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=C_AMBER, alignment=TA_CENTER))]], colWidths=["100%"])
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BG_AMBER),
        ("BOX", (0, 0), (-1, -1), 1.5, C_AMBER),
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
            "Die dritte statische Sicherheitsanalyse des NetMon-Arbeitsstands v1.1.14 "
            "durch ein Multi-Agenten-System (Claude Sonnet 4.6) mit manueller Verifikation "
            "und Live-Tests bestaetigt 1 Finding (MEDIUM). 6 Kandidaten ausgeschlossen — "
            "K1 und K2 durch manuelle Code-Verifikation widerlegt. Kein Remote-Exploit.",
            BODY),
        Paragraph(
            "K1 (WIDERLEGT, 9/10 → FP): PATH-Hijacking via shutil.which(). "
            "Manuelle Verifikation: TRUSTED_WEB_CMD_PREFIXES bereits auf Zeile 16 implementiert.",
            BODY),
        Paragraph(
            "K2 (WIDERLEGT, 8/10 → FP): Beliebige Python-Ausfuehrung aus fun_games_dir. "
            "Manuelle Verifikation: fun_games_dir ist hardcoded (app.py Zeile 2581: "
            "~/.local/share/netmon/fun/code_the_classics), nie aus Settings geladen. "
            "Same-User-Desktop ohne Privilege Escalation — Ausschluss greift.",
            BODY),
        Paragraph(
            "K3 (MEDIUM, 9/10, bestaetigt): agent/runner.py prueft nur parts[0] in der Allowlist. "
            "Live-Test bewiesen: subprocess.run(['black', '/home/user/.bashrc']) schreibt die "
            "Datei tatsaechlich um. Tilde-Angriffe schlagen fehl (~/file nicht expandiert). "
            "Angriffsvektor: Prompt-Injection mit absoluten Pfaden.",
            BODY),
    ]

    # ── Methodik ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 — Reconnaissance", H3),
        Paragraph(
            "Alle 17+ neuen Module gelesen: rkhunter_manager.py, coordinator.py, state.py, "
            "support_bundle.py, diagnostics.py, links_controller.py, fun_controller.py, "
            "process_guard_controller.py, repository_guard_controller.py, "
            "roots_baseline_guard_controller.py, lang_service.py, network_helpers.py, "
            "process_guard_service.py, repository_guard_service.py, cleanup_assistant_tab.py, "
            "download_scan_tab.py, radio_tab.py. Fokus: subprocess-Calls, Dateioperationen, "
            "URL-Handling, Deserialisierung.",
            BODY),
        Paragraph("Phase 2 — Kandidaten-Analyse", H3),
        Paragraph(
            "Datenflussketten nachverfolgt: PATH-Umgebungsvariable → shutil.which → sudo install, "
            "os.walk(games_dir) → subprocess.Popen, Allowlist-Pruefung ohne Pfad-Confinement.",
            BODY),
        Paragraph("Phase 3 — False-Positive-Filter", H3),
        Paragraph(
            "Unabhaengige Re-Analyse jedes Kandidaten. Ausschluss: DoS, Single-User-Desktop "
            "ohne Privilege-Boundary-Crossing, Python-3.12+-Schutzmechanismen, "
            "Umgebungskontrolle als Pre-Condition.",
            BODY),
        Paragraph("Phase 4 — Manuelle Verifikation", H3),
        Paragraph(
            "Alle 3 High-Confidence-Findings durch direktes Lesen der Quelldateien verifiziert. "
            "Zeile fuer Zeile nachvollzogen: shutil.which-Rueckgabe, repair_targets-Schreibpfad, "
            "subprocess.Popen-Argumente, run_command-Allowlist-Logik.",
            BODY),
    ]

    # ── Bestätigte Findings ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bestaetrigte Findings (nach manueller Verifikation)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "K1 wurde initial mit Konfidenz 9/10 als HIGH eingestuft. Manuelle Verifikation "
            "zeigt: TRUSTED_WEB_CMD_PREFIXES ist bereits implementiert — K1 ist ein False Positive. "
            "Analoger Fehler wie Runde 2 K1 (Agent uebersah _normalize_station_stream_url()).",
            MUTED),
    ]

    # K1 als widerlegt anzeigen
    k1_rows = [
        [Paragraph("K1 — PATH-Hijacking rkhunter_manager — manuell widerlegt", FINDING_TITLE),
         Paragraph("Konfidenz: 9/10 → FP (nach manueller Verifikation)", MUTED)],
        [Paragraph("netmon/core/rkhunter_manager.py, Zeilen 16–26", MONO), Paragraph("")],
        [Paragraph(
            "WIDERLEGT: TRUSTED_WEB_CMD_PREFIXES = ('/usr/bin/', '/bin/', '/usr/local/bin/') "
            "bereits auf Zeile 16 definiert. _preferred_web_cmd() prueft jeden shutil.which()-"
            "Rueckgabewert dagegen — ~/.local/bin/wget wird abgelehnt. "
            "Automatischer Agent uebersah die Pruefroutine (analoger Fehler wie Runde 2 K1).",
            s("VD", fontName="Helvetica", fontSize=9, leading=13,
              textColor=colors.HexColor("#5f6368"),
              backColor=C_BG_GREEN, leftIndent=4)), Paragraph("")],
    ]
    k1_t = Table(k1_rows, colWidths=["80%", "20%"])
    k1_t.setStyle(TableStyle([
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 2), (1, 2)),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
        ("BACKGROUND", (0, 2), (-1, 2), C_BG_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [k1_t, Spacer(1, 5 * mm)]

    findings = [
        {
            "title": "K3 — Agent-CLI: black/ruff ohne Pfad-Confinement schreiben beliebige Dateien",
            "file": "agent/runner.py, Zeilen 7–13, 31–32",
            "severity": "MEDIUM",
            "conf": "9/10",
            "flow": (
                "LLM-Prompt-Injection mit absolutem Pfad\n"
                "  → run_command('black /home/user/.bashrc')\n"
                "  → parts[0] = 'black' → Allowlist-Check BESTANDEN  [Zeile 31]\n"
                "  → parts[1] = '/home/user/.bashrc' → KEIN Pfad-Check\n"
                "  → subprocess.run(['black', '/home/user/.bashrc'], cwd=REPO_ROOT)\n"
                "  → black schreibt .bashrc um  ← Live-Test bestaetigt"
            ),
            "desc": (
                "run_command() prueft nur parts[0] in ALLOWED_BASE_COMMANDS — keine "
                "Pfadrestriktion fuer black/ruff/ls. Live-Test bestaetigt: "
                "subprocess.run(['black', '/home/happy/.bashrc']) hat die Datei "
                "reformatiert/ueberschrieben. Tilde-Angriffe (black ~/.bashrc) "
                "scheitern: subprocess ohne shell=True expandiert ~ nicht; "
                "black selbst auch nicht ('Path does not exist'). "
                "Angriffsvektor: Prompt-Injection in LLM-Agent mit absolutem Pfad "
                "(z.B. nach Informationsgewinn via ls). AGENTS.md konzipiert diesen "
                "Agent fuer LLM-Eingaben — realistischer Angriffspfad."
            ),
            "fix": (
                "resolved = Path(arg).expanduser().resolve()\n"
                "if not resolved.is_relative_to(REPO_ROOT):\n"
                "    raise ValueError(f'Pfad ausserhalb REPO_ROOT: {arg}')\n"
                "# Gilt fuer ls, black, ruff, pytest (analog Git-Subcommand-Allowlist)"
            ),
            "bg_color": C_BG_AMBER,
            "border_color": C_AMBER,
        },
    ]

    for f in findings:
        rows = [
            [Paragraph(f["title"], FINDING_TITLE),
             Paragraph(f"Severity: {f['severity']} | Konfidenz: {f['conf']}", MUTED)],
            [Paragraph(f"Datei: {f['file']}", MONO), Paragraph("")],
            [Paragraph("Datenfluss:", s("DFL", fontName="Helvetica-Bold", fontSize=9,
                                         textColor=colors.HexColor("#16263a"))), Paragraph("")],
            [Paragraph(f["flow"], s("FLOW", fontName="Courier", fontSize=8,
                                    leading=11, textColor=colors.HexColor("#374151"))),
             Paragraph("")],
            [Paragraph(f["desc"], BODY), Paragraph("")],
            [Paragraph(f"Fix: {f['fix']}", s("FIX", fontName="Courier", fontSize=8,
                                              leading=11,
                                              textColor=colors.HexColor("#1d4ed8"),
                                              backColor=colors.HexColor("#eff6ff"))),
             Paragraph("")],
        ]
        t = Table(rows, colWidths=["80%", "20%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("SPAN", (0, 4), (1, 4)),
            ("SPAN", (0, 5), (1, 5)),
            ("BOX", (0, 0), (-1, -1), 0.5, f["border_color"]),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
            ("BACKGROUND", (0, 0), (-1, 0), f["bg_color"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [t, Spacer(1, 5 * mm)]

    # ── Ausgeschlossene Kandidaten ─────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Ausgeschlossene Kandidaten", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    excluded = [
        {
            "title": "K1 — PATH-Hijacking rkhunter_manager — manuell widerlegt",
            "file": "netmon/core/rkhunter_manager.py, Zeilen 16–26",
            "conf": "9/10 → FP",
            "verdict": (
                "WIDERLEGT — TRUSTED_WEB_CMD_PREFIXES = ('/usr/bin/', '/bin/', '/usr/local/bin/') "
                "bereits auf Zeile 16 definiert. _preferred_web_cmd() prueft jeden "
                "shutil.which()-Rueckgabewert — ~/.local/bin/wget wird abgelehnt. "
                "Automatischer Agent hat den Allowlist-Check uebersehen."
            ),
        },
        {
            "title": "K2 — Python-Ausfuehrung aus Spieleordner — manuell widerlegt",
            "file": "netmon/features/fun_controller.py · app.py Zeile 2581",
            "conf": "8/10 → FP",
            "verdict": (
                "WIDERLEGT — fun_games_dir ist hardcoded auf "
                "~/.local/share/netmon/fun/code_the_classics (app.py Zeile 2581, "
                "einzige Zuweisung, nie aus Settings geladen). Same-User-Desktop "
                "ohne Privilege Escalation. Ausschluss greift. Agent-Behauptung "
                "'konfigurierbar in Settings' war falsch."
            ),
        },
        {
            "title": "K4 — importlib-Modul-Loading aus sys.path (tooling.py)",
            "file": "netmon/core/tooling.py, Zeilen 47–81",
            "conf": "7/10",
            "verdict": (
                "AUSGESCHLOSSEN — Angriff erfordert Kontrolle ueber Umgebungsvariablen "
                "(PYTHONPATH) oder CWD vor Prozessstart. Pre-Condition = bereits volle "
                "Code-Ausfuehrung als gleicher Benutzer. Kein zusaetzlicher Angriffspfad."
            ),
        },
        {
            "title": "K5 — lang_code-Pfad-Traversal in LangService (lang_service.py)",
            "file": "netmon/services/lang_service.py, Zeile 12",
            "conf": "7/10",
            "verdict": (
                "AUSGESCHLOSSEN — Nur lesend (json.load), auf JSON-parsierbare Dateien "
                "beschraenkt. Erfordert Schreibzugriff auf Settings-Datei im "
                "Benutzerverzeichnis (gleiche Privilege-Ebene). Kein Privilege-Boundary-Crossing."
            ),
        },
        {
            "title": "K6 — TOCTOU-Race vor shutil.rmtree (cleanup_assistant_tab.py)",
            "file": "netmon/ui/tabs/cleanup_assistant_tab.py, Zeilen 2307–2464",
            "conf": "7/10",
            "verdict": (
                "AUSGESCHLOSSEN — Python 3.12+ shutil.rmtree schutzt gegen Symlinks via "
                "NotADirectoryError. Race-Window extrem eng; erfordert praezise Timing-Koordination "
                "durch denselben Benutzer. Als Hardening-Empfehlung notiert."
            ),
        },
        {
            "title": "K7 — .desktop-Exec-Parsing via links_controller.py",
            "file": "netmon/features/links_controller.py, Zeilen 804–813, 882–894",
            "conf": "7/10",
            "verdict": (
                "AUSGESCHLOSSEN — ~/.local/share/applications/ ist das Standard-XDG-Verzeichnis "
                "fuer benutzerinstallierte Anwendungen; Exec=-Zeilen auszufuehren ist "
                "spezifikationskonformes Verhalten. Kein Privilege-Boundary-Crossing."
            ),
        },
    ]

    for e in excluded:
        rows = [
            [Paragraph(e["title"], FINDING_TITLE),
             Paragraph(f"Konfidenz: {e['conf']} -> FP", MUTED)],
            [Paragraph(f"Datei: {e['file']}", MONO), Paragraph("")],
            [Paragraph(f"Filterentscheid: {e['verdict']}",
                       s("VD", fontName="Helvetica", fontSize=9, leading=13,
                         textColor=colors.HexColor("#5f6368"),
                         backColor=C_BG_GREEN, leftIndent=4)), Paragraph("")],
        ]
        t = Table(rows, colWidths=["80%", "20%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
            ("BACKGROUND", (0, 2), (-1, 2), C_BG_GREEN),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [t, Spacer(1, 4 * mm)]

    # ── Verbesserungen seit Runde 2 ────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("5. Sicherheitsverbesserungen seit Runde 2", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("URL-Schema-Validierung Radio-Modul (Runde 2, bestaetigt)",
         "ALLOWED_RADIO_STREAM_SCHEMES = {'http', 'https', 'rtsp', 'rtmp'} in "
         "_normalize_station_stream_url() — verhindert SSRF via mpv/urllib.request."),
        ("WireGuard Interface-Name-Validierung (neu, Runde 3)",
         "wg_profile_path() validiert Interface-Namen via re.fullmatch(r'[A-Za-z0-9_.-]+', ...) "
         "und os.path.commonpath()-Confinement auf /etc/wireguard."),
        ("roots_baseline_guard: sudo-Calls mit Pfad-Allowlist (neu, Runde 3)",
         "_is_allowed_guard_path(path) mit os.path.realpath()-Normalisierung gegen "
         "ROOTS_GUARD_DEFAULT_AREA_PATHS — verhindert sudo cat auf beliebige Pfade."),
        ("ClamAV Tempdir Symlink-Schutz (seit Runde 1)",
         "_safe_makedirs_no_symlink() prueft via os.lstat() — wirft RuntimeError bei Symlink."),
        ("82 Proxy-Methoden aus app.py entfernt (Runde 2)",
         "Angriffsflaechenreduktion; alle via refactor_safety.py auf Null-Aufrufer verifiziert."),
        ("HDD-Mountpoint-Validierung (Runde 2)",
         "_slot_mountpoint() mit os.path.realpath() + _SAFE_MOUNT_BASES-Allowlist."),
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

    # ── Hardening-Empfehlungen ─────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("6. Weitere Hardening-Empfehlungen", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Zusaetzlich zu den drei bestaetigten Findings — Defense-in-Depth-Massnahmen "
            "ohne unmittelbaren Exploitpfad:",
            BODY),
        Paragraph("1. cleanup_assistant_tab.py TOCTOU:",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("shutil.rmtree nach lstat()-Check via os.open(path, O_NOFOLLOW) atomar gestalten.", BODY),
        Paragraph("2. lang_service.py lang_code-Sanitierung:",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("Regex ^[a-z]{2}(_[A-Z]{2})?$ vor os.path.join() validieren.", BODY),
        Paragraph("3. state.py get_netmon_documents_subdir:",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("Jedes part-Argument via os.path.basename() normalisieren vor makedirs().", BODY),
        Paragraph("4. WireGuard wg-quick Interface-Name:",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("wg show interfaces-Output gegen re.fullmatch(r'[A-Za-z0-9_.-]{1,15}', ...) pruefen.", BODY),
        Paragraph("5. webbrowser.open Schema-Validierung (Radio):",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("station['homepage'] via urlparse().scheme gegen {'http','https'} pruefen.", BODY),
        Paragraph("6. os.path.realpath in Roots-Baseline-Guard:",
                  s("HB", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=2)),
        Paragraph("os.path.abspath durch os.path.realpath() fuer vollstaendige Symlink-Aufloesing ersetzen.", BODY),
    ]

    # ── Analysierte Kategorien ─────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("7. Gepruefe Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("PATH-Hijacking via shutil.which() ohne Prefix-Validierung", BODY), Paragraph("K1 BESTÄTIGT", s("HIT", fontName="Helvetica-Bold", fontSize=10, textColor=C_RED))],
        [Paragraph("Arbitrary Code Execution via unsignierten Spieleordner", BODY), Paragraph("K2 BESTÄTIGT", s("HIT", fontName="Helvetica-Bold", fontSize=10, textColor=C_AMBER))],
        [Paragraph("Dateikorruption via LLM-Prompt-Injection in Agent-CLI", BODY), Paragraph("K3 BESTÄTIGT", s("HIT", fontName="Helvetica-Bold", fontSize=10, textColor=C_AMBER))],
        [Paragraph("importlib-Module-Loading aus sys.path/PYTHONPATH", BODY), Paragraph("FP (K4)", MUTED)],
        [Paragraph("Path Traversal via lang_code in LangService", BODY), Paragraph("FP (K5)", MUTED)],
        [Paragraph("TOCTOU Race vor shutil.rmtree", BODY), Paragraph("FP (K6)", MUTED)],
        [Paragraph(".desktop-Exec-Parsing via links_controller", BODY), Paragraph("FP (K7)", MUTED)],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("SSRF via urllib.request / URL-Schema-Validierung", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Privilege Escalation (sudo mit Nutzereingabe)", BODY), Paragraph("Kein Finding (ausser K1)", BODY)],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval)", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("Symlink-Angriffe auf privilegierte Dateioperationen", BODY), Paragraph("Kein Finding", BODY)],
        [Paragraph("shell=True in subprocess-Calls", BODY), Paragraph("Kein Finding", BODY)],
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

    # ── Impressum ──────────────────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE),
        Spacer(1, 3 * mm),
        Paragraph("Impressum und Haftungsausschluss", H2),
        Paragraph("<b>Auditor:</b> Claude Sonnet 4.6 (Anthropic) — Multi-Agenten-System + manuelle Verifikation", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 28. Juni 2026", BODY),
        Paragraph("<b>Codestand:</b> Arbeitsstand v1.1.14 inkl. untracked/modified files — Runde 3", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r3.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
