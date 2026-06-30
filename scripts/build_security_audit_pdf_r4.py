#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.15 Runde 4."""

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
        title="NetMon Security Audit 2026 — v1.1.15 Runde 4",
        author="Claude Sonnet 4.6 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.15 (Runde 4)",
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

    C_GREEN    = colors.HexColor("#15803d")
    C_MUTED    = colors.HexColor("#9db5cc")
    C_LINE     = colors.HexColor("#d9e1e7")
    C_BG_HEAD  = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#f0fdf4")
    C_BLUE     = colors.HexColor("#1d4ed8")
    C_BG_BLUE  = colors.HexColor("#eff6ff")

    story = []

    # ── Titelseite ──────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 4", s(
            "EYEBROW", fontName="Helvetica", fontSize=10, leading=13,
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=6)),
        Paragraph("NetMon Roots v1.1.15", s(
            "TITLE", fontName="Helvetica-Bold", fontSize=28, leading=34,
            textColor=colors.HexColor("#16263a"), alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Code Security Review — Juni 2026", s(
            "SUB", fontName="Helvetica", fontSize=14, leading=18,
            textColor=colors.HexColor("#5f6368"), alignment=TA_CENTER, spaceAfter=20)),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "29. Juni 2026"],
        ["Analysierte Version", "v1.1.15 — Runde 4"],
        ["Geaenderte Dateien (gesamt)", "40+"],
        ["Sicherheitsfokus-Module", "20"],
        ["Bestaetigte Findings", "0"],
        ["Bewertete Kandidaten", "1 (K1 — FP)"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Methode", "Statische Code-Analyse + False-Positive-Filterrunde"],
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

    # ── Zusammenfassung ─────────────────────────────────────────────────────
    story += [
        Paragraph("1. Zusammenfassung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die vierte statische Sicherheitsanalyse des NetMon-Arbeitsstands v1.1.15 "
            "durch ein Multi-Agenten-System (Claude Sonnet 4.6) bestaetigte kein einziges "
            "Finding. 1 Kandidat (K1) wurde identifiziert und in einer unabhaengigen "
            "Filterrunde nach vollstaendigem Lesen von vpn_controller.py mit Konfidenz 3/10 "
            "als False Positive ausgeschlossen.",
            BODY),
        Paragraph(
            "K1 (FP): WireGuard-Konfig-Import kopiert .conf-Dateien ohne Inhaltspruefung "
            "nach /etc/wireguard/. PostUp/PreDown-Hooks werden von wg-quick als Root "
            "ausgefuehrt. Ausschluss: kein Privilege-Boundary-Crossing (Single-User-Desktop, "
            "explizite Nutzerauswahl per Datei-Dialog, bestehende sudo-Rechte vorausgesetzt). "
            "Angriffspfad erfordert entweder bereits volle Kompromittierung oder Social "
            "Engineering.",
            BODY),
        Paragraph(
            "Alle 3 Findings aus Runde 3 (K1 PATH-Hijacking rkhunter, K2 fun_controller "
            "Pfad-Confinement, K3 agent/runner Pfad-Allowlist) im aktuellen Codestand als "
            "geschlossen verifiziert.",
            BODY),
    ]

    # ── Methodik ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 — Reconnaissance", H3),
        Paragraph(
            "Alle 40+ geaenderten Module gelesen; Fokus auf Subprocess-Aufrufe mit "
            "Nutzerdaten, sudo-Einbettung, URL-Handling, Dateioperationen mit "
            "unkontrollierten Pfaden, eval/exec und Privilegienuebergaenge. "
            "20 Module mit sicherheitsrelevantem Fokus tiefgehend analysiert.",
            BODY),
        Paragraph("Phase 2 — Kandidaten-Analyse", H3),
        Paragraph(
            "Datenflussketten von externen Quellen (WireGuard-Konfig-Dateien, "
            "API-Antworten, Nutzer-Dialoge, Dateisystem) bis zu sensitiven Operationen "
            "(sudo install, wg-quick up, subprocess.Popen) vollstaendig nachverfolgt. "
            "1 Kandidat identifiziert (Konfidenz 7/10): vpn_controller.py — "
            "WireGuard-Import ohne Inhaltspruefung.",
            BODY),
        Paragraph("Phase 3 — False-Positive-Filter", H3),
        Paragraph(
            "K1 in einem unabhaengigen Agenten re-analysiert: vollstaendiger Quelltext "
            "von vpn_controller.py gelesen, exakter Code der Import-Funktion "
            "(import_wg_profiles_from_folder, Zeilen 3154-3238) lokalisiert. "
            "Ausschluss: kein Privilege-Boundary-Crossing auf Single-User-Desktop, "
            "explizite Nutzerinteraktion via filedialog.askopenfilenames(), "
            "bestehende sudo-Rechte (ensure_sudo_session() gate). Konfidenz: 3/10 -> FP.",
            BODY),
        Paragraph("Phase 4 — R3-Nachverfolgung", H3),
        Paragraph(
            "Alle 3 Findings aus Runde 3 auf Umsetzungsstand geprueft: "
            "rkhunter_manager.py (TRUSTED_WEB_CMD_PREFIXES), "
            "fun_controller.py (realpath() + fun_games_dir-Check), "
            "agent/runner.py (REPO_ROOT-Confinement fuer Pfadargumente). "
            "Alle drei im aktuellen Codestand geschlossen bestaetigt.",
            BODY),
    ]

    # ── Kandidat K1 ─────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bewerteter Kandidat (ausgeschlossen)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    k1_rows = [
        [Paragraph(
            "K1 — WireGuard-Import: PostUp/PreDown-Hooks ohne Inhaltspruefung",
            FINDING_TITLE),
         Paragraph("Konfidenz 7/10 -> 3/10 -> FP", MUTED)],
        [Paragraph(
            "netmon/features/vpn_controller.py — import_wg_profiles_from_folder(), Zeilen 3154–3238",
            MONO), Paragraph("")],
        [Paragraph("Datenfluss:", s("DFL", fontName="Helvetica-Bold", fontSize=9,
                                    textColor=colors.HexColor("#16263a"))), Paragraph("")],
        [Paragraph(
            "Nutzer waehlt .conf-Datei via filedialog.askopenfilenames()\n"
            "  -> Dateiname via re.fullmatch(r'[A-Za-z0-9_.-]+', name) validiert\n"
            "  -> Zielpfad via wg_profile_path() + os.path.commonpath() begrenzt\n"
            "  -> sudo -n install -m 600 <src> /etc/wireguard/<name>.conf\n"
            "     (Dateiinhalt wird NICHT geprueft — PostUp/PreDown werden uebernommen)\n"
            "  -> wg-quick up <name> fuehrt PostUp-Hooks als Root aus",
            s("FLOW", fontName="Courier", fontSize=8, leading=11,
              textColor=colors.HexColor("#374151"))), Paragraph("")],
        [Paragraph(
            "Vorhandene Schutzmassnahmen: Filename-Regex, commonpath()-Confinement auf "
            "/etc/wireguard/, realpath()-Normalisierung. Fehlend: Inhaltspruefung "
            "auf Hook-Direktiven.",
            BODY), Paragraph("")],
        [Paragraph(
            "Filterentscheid: Kein Privilege-Boundary-Crossing auf einem Single-User-Desktop. "
            "Nutzer initiiert Import explizit ueber nativen Datei-Dialog (keine Automation). "
            "WireGuard-Hooks sind dokumentiertes Protokoll-Feature. Angreifer benoetigt "
            "entweder bereits Schreibzugriff auf das Dateisystem (volle Kompromittierung) "
            "oder Social Engineering (Supply-Chain-Problem, keine Code-Schwachstelle). "
            "Anwendung setzt sudo-Rechte bereits voraus. Konfidenz: 3/10 -> FALSE POSITIVE.",
            s("VD", fontName="Helvetica", fontSize=9, leading=13,
              textColor=colors.HexColor("#5f6368"),
              backColor=C_BG_GREEN, leftIndent=4)), Paragraph("")],
    ]
    k1_t = Table(k1_rows, colWidths=["80%", "20%"])
    k1_t.setStyle(TableStyle([
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 2), (1, 2)),
        ("SPAN", (0, 3), (1, 3)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (0, 5), (1, 5)),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
        ("BACKGROUND", (0, 5), (-1, 5), C_BG_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [k1_t, Spacer(1, 5 * mm)]

    # ── Verbesserungen seit Runde 3 ─────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Sicherheitsverbesserungen seit Runde 3", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("HDD Mountpoint-Validierung — hdd_controller.py — Security Fix [Commit 0431faf8]",
         "_slot_mountpoint() kanonikalisiert den Pfad via os.path.realpath() und prueft gegen "
         "_SAFE_MOUNT_BASES = ('/mnt/', '/media/', '/run/media/'). Ungueltige Mountpoints "
         "fallen auf sicheren Default /mnt/<device-basename> zurueck. Fix verhindert "
         "Privilege Escalation via praepariertes Filesystem auf beliebigem Mountpoint."),
        ("CWD-Entfernung aus CSV-Suchpfaden — linux_help_controller.py [Commit 363d64f5]",
         "os.getcwd()-Fallback aus den CSV-Suchpfaden entfernt. Verhindert Command-Injection "
         "via manipulierte linux-befehle.csv aus einem world-writable Arbeitsverzeichnis."),
        ("EPERM-Behandlung in lock.py korrigiert [Commit 363d64f5]",
         "os.kill(pid, 0) mit PermissionError (EPERM) wird jetzt korrekt als 'Prozess laeuft' "
         "gewertet. Bisher fuehrte EPERM faelschlich zum Start einer zweiten Instanz."),
        ("REPO_ROOT dynamisch aus __file__ — agent/runner.py [Commit 363d64f5]",
         "Hardcoded /workspaces/dev-lab durch Path(__file__).resolve().parent.parent ersetzt. "
         "Macht REPO_ROOT-Confinement in Nicht-Codespaces-Umgebungen wirksam."),
        ("DNS-Token-Validierung: Falsy-Zero-Fix — dns_control_service.py [Commit 363d64f5]",
         "token.count('.') zu token.count('.') > 0 geaendert. "
         "Verhindert dass IP-Tokens ohne Punkt als gueltig durchgelassen werden."),
        ("82 Proxy-Methoden entfernt — app.py [Commits a279e38c + 920cfc9b]",
         "Insgesamt 101 tote/Proxy-Methoden aus app.py geloescht. Alle via "
         "refactor_safety.py auf Null-Aufrufer verifiziert. Reduziert Angriffsflaeche."),
        ("R3-Findings geschlossen bestaetigt (K1 rkhunter, K2 fun, K3 agent/runner)",
         "TRUSTED_WEB_CMD_PREFIXES in rkhunter_manager.py, realpath()-Check in "
         "fun_controller.py, REPO_ROOT-Pfad-Confinement in agent/runner.py — "
         "alle drei im aktuellen Codestand verifiziert."),
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

    # ── Hardening — alle geschlossen ────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("5. Hardening-Empfehlungen — alle geschlossen", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Saemtliche seit Runde 1 offenen Defense-in-Depth-Empfehlungen wurden "
            "im aktuellen Codestand v1.1.15 vollstaendig umgesetzt und per "
            "direktem Quelltext-Check verifiziert:",
            BODY),
    ]

    hardening_closed = [
        ("1. IP-Validierung fuer WireGuard-Endpoints [GESCHLOSSEN]",
         "vpn_controller.py:2479 — parse_vpn_endpoint() verwendet ipaddress.ip_address(host). "
         "Nicht-IP-Hostnamen werden via _warn_non_ip_endpoint_once() protokolliert und "
         "uebersprungen. Nur validiertes endpoint_ip.compressed erreicht UFW-Kommandos."),
        ("2. Schema-Validierung homepage-URLs im Radio-Modul [GESCHLOSSEN]",
         "radio_controller.py:106 — ALLOWED_RADIO_HOMEPAGE_SCHEMES = {'http', 'https'}. "
         "_normalize_station_homepage_url() (Zeilen 315-326) validiert via urlparse() "
         "und wird in open_selected_station_homepage() vor webbrowser.open() aufgerufen."),
        ("3. Shell-Quoting in Repository-Guard-Snippets [GESCHLOSSEN]",
         "repository_guard_controller.py:799-802 — shlex.quote() fuer alle eingebetteten "
         "Werte: quoted_uri, quoted_path, quoted_host, quoted_keyring_path."),
        ("4. realpath() im Roots-Baseline-Guard [GESCHLOSSEN]",
         "roots_baseline_guard_controller.py:123 — _normalize_guard_path_pattern() "
         "verwendet os.path.realpath(os.path.expanduser(raw)). Symlinks werden vor "
         "fnmatch-Vergleichen und Allowlist-Pruefungen vollstaendig aufgeloest."),
        ("5. Pfadpruefung in image_to_data_url() [GESCHLOSSEN]",
         "ai_online_service.py:35-39 — resolved.relative_to(home_dir) erzwingt "
         "Home-Verzeichnis-Confinement. Zusaetzlich: resolve(strict=True) und "
         "Dateiendungs-Allowlist {png, jpg, jpeg, webp, gif, bmp}."),
        ("6. WireGuard-Import: Hook-Hinweis [GESCHLOSSEN]",
         "vpn_controller.py:141 — _warn_wireguard_import_hooks() scannt jede .conf-Datei "
         "vor dem Import auf PreUp/PostUp/PreDown/PostDown-Direktiven und zeigt einen "
         "expliziten Nutzerhinweis mit Abbruch-Option an (3 Import-Einstiegspunkte: "
         "Zeilen 3229, 3328, 3363)."),
    ]

    for title, desc in hardening_closed:
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

    # ── Analysierte Kategorien ───────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("6. Gepruefe Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Path Traversal (Dateioperationen mit Nutzereingabe)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Privilege Escalation (sudo mit unkontrollierten Argumenten)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Argument Injection (list-form subprocess mit externen Daten)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Sensitive Data Exposure (PII in Logs)", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("SSRF via urllib.request / externe URL-Weitergabe", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("URL-Schema-Validierung an Media-Subprocessen", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Symlink-Angriffe auf privilegierte Dateioperationen", BODY),
         Paragraph("Kein Finding", s("OK", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=C_GREEN))],
        [Paragraph("Mountpoint-Manipulation via Konfig-Datei", BODY),
         Paragraph("Kein Finding (Fix v1.1.15)", s("OK", fontName="Helvetica-Bold",
                                                    fontSize=10, textColor=C_GREEN))],
        [Paragraph("WireGuard-Hook-Ausfuehrung via Import", BODY),
         Paragraph("K1 -> FP (kein Boundary Crossing)", MUTED)],
        [Paragraph("PATH-Hijacking via shutil.which (R3-K1)", BODY),
         Paragraph("Geschlossen (R3)", MUTED)],
        [Paragraph("Agent-CLI Pfad-Confinement (R3-K3)", BODY),
         Paragraph("Geschlossen (R3)", MUTED)],
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

    # ── Analysierte Module ───────────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        Paragraph("7. Analysierte Module (Runde 4 — Sicherheitsfokus)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    module_rows = [
        [Paragraph("Datei / Modul", MUTED),
         Paragraph("Fokus", MUTED),
         Paragraph("Ergebnis", MUTED)],
        [Paragraph("netmon/features/vpn_controller.py", MONO),
         Paragraph("WireGuard-Import, wg-quick, Interface-Validation", BODY),
         Paragraph("K1 -> FP", MUTED)],
        [Paragraph("netmon/features/hdd_controller.py", MONO),
         Paragraph("Mountpoint-Validierung, LUKS, sudo mount", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/linux_help_controller.py", MONO),
         Paragraph("CSV-Suchpfade nach CWD-Entfernung", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/firewall_controller.py", MONO),
         Paragraph("UFW, Port-Regex, ipaddress-Validierung", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/clamav_controller.py", MONO),
         Paragraph("ClamAV, _safe_makedirs_no_symlink()", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/radio_controller.py", MONO),
         Paragraph("mpv/ffmpeg, ALLOWED_RADIO_STREAM_SCHEMES", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/packet_capture_controller.py", MONO),
         Paragraph("tshark, Interface-Name aus ip link", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/security_audit_controller.py", MONO),
         Paragraph("Lynis/rkhunter, Startup-Guard-Baseline", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/security_monitoring_controller/_core.py", MONO),
         Paragraph("Event-System, Baseline, Shared Helpers", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/security_monitoring_controller/_scanning.py", MONO),
         Paragraph("Geraete-/Integritaets-Scanning", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/dot_controller.py", MONO),
         Paragraph("DNS-Dropin via sudo install, Pfad hardcoded", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/features/chad_controller.py", MONO),
         Paragraph("KI-Integration, getattr-Fix, kein Subprocess", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/core/lock.py", MONO),
         Paragraph("EPERM-Behandlung, Instanz-Lock", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/core/command.py", MONO),
         Paragraph("run_cmd-Wrapper, sudo -S -v, shell=False", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/services/dns_control_service.py", MONO),
         Paragraph("nmcli con mod, DNS-Token-Validierung", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/services/startup_guard_service.py", MONO),
         Paragraph("SHA-256-Hashing, neue-Dateien-Reporting", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/services/path_guard_service.py", MONO),
         Paragraph("PATH-Analyse, read-only", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("agent/runner.py", MONO),
         Paragraph("REPO_ROOT-Fix, Subprocess-Allowlist, Pfad-Confinement", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("agent/tools.py", MONO),
         Paragraph("Dateilesen mit relative_to(REPO_ROOT)-Guard", BODY),
         Paragraph("Kein Finding", s("OK2", fontName="Helvetica", fontSize=9,
                                     textColor=C_GREEN))],
        [Paragraph("netmon/app.py (Refaktorierung)", MONO),
         Paragraph("82 Proxy-Methoden entfernt, keine Regression", BODY),
         Paragraph("Keine Regression", MUTED)],
    ]
    mod_table = Table(module_rows, colWidths=["42%", "40%", "18%"])
    mod_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BG_HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [mod_table]

    # ── Impressum ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE),
        Spacer(1, 3 * mm),
        Paragraph("Impressum und Haftungsausschluss", H2),
        Paragraph("<b>Auditor:</b> Claude Sonnet 4.6 (Anthropic) — Multi-Agenten-System + False-Positive-Filterrunde", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 29. Juni 2026", BODY),
        Paragraph("<b>Codestand:</b> e334324a … 920cfc9b + Arbeitsstand (modified/untracked), 40+ Dateien — Runde 4", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + unabhaengige False-Positive-Filterrunde — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r4.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
