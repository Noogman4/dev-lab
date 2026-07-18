#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.16 Runde 5."""

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
        title="NetMon Security Audit 2026 — v1.1.16 Runde 5",
        author="Claude Sonnet 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.16 (Runde 5)",
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

    C_GREEN    = colors.HexColor("#15803d")
    C_AMBER    = colors.HexColor("#b45309")
    C_MUTED    = colors.HexColor("#9db5cc")
    C_LINE     = colors.HexColor("#d9e1e7")
    C_BG_HEAD  = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#f0fdf4")
    C_BG_AMBER = colors.HexColor("#fffbeb")

    story = []

    # ── Titelseite ──────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 5", s(
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
        ["Datum", "05. Juli 2026"],
        ["Analysierte Version", "v1.1.16 — Runde 5"],
        ["Geaenderte/neue Dateien", "~13"],
        ["Sicherheitsfokus-Module", "12"],
        ["Offene Findings", "0"],
        ["Bewertete Kandidaten", "3 (alle behoben)"],
        ["Konfidenz-Schwelle", ">= 7 / 10"],
        ["Methode", "Sub-Agent-Review + Fix-Verifikation per Exploit-Repro"],
        ["Analysewerkzeug", "Claude Sonnet 5 (Anthropic)"],
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
        [[Paragraph("3 FINDINGS GEFUNDEN UND NOCH IN DIESER RUNDE BEHOBEN — 0 OFFEN", s(
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

    # ── Zusammenfassung ─────────────────────────────────────────────────────
    story += [
        Paragraph("1. Zusammenfassung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die fuenfte Sicherheitsanalyse konzentrierte sich ausschliesslich auf das "
            "neue Secure-Browser-Manager-Feature (Commit 9baa6284 + aktueller "
            "Arbeitsstand) sowie kleinere Diffs seit Runde 4. Ein dedizierter "
            "Sub-Agent identifizierte 3 bestaetigte Schwachstellen (kein False "
            "Positive) im brandneuen Feature, alle mit Konfidenz 7-8/10.",
            BODY),
        Paragraph(
            "K1 (Medium, behoben): Fehlende Zeichensatzvalidierung fuer Container-Namen "
            "erlaubte Pfad-Escapes aus dem Container-Basisverzeichnis heraus, u.a. in "
            "~/.config/autostart (Persistenz-Risiko).",
            BODY),
        Paragraph(
            "K2 (Medium, behoben): homepage_url/new_tab_url wurden unescaped in "
            "Firefox user.js eingesetzt -> Preference-Injection, die die eigenen "
            "Isolations-Haertungen des Containers untergraben konnte.",
            BODY),
        Paragraph(
            "K3 (Low, behoben): Fehlende Newline-Bereinigung in .desktop-Feldern "
            "(Name=/Comment=) konnte zusaetzliche Desktop-Entry-Schluessel einschleusen.",
            BODY),
        Paragraph(
            "Alle drei Fixes wurden per Reproduktionsskript verifiziert (Exploit vor "
            "Fix erfolgreich, nach Fix abgewiesen/entschaerft) und gegen die "
            "bestehenden 121 automatisierten Tests regressionsgetestet - alle "
            "bestanden.",
            BODY),
    ]

    # ── Methodik ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Reconnaissance", H3),
        Paragraph(
            "Vollstaendiges Lesen von netmon/modules/secure_browser/*.py "
            "(manager/service/ui/models), secure_browser_tab.py und "
            "browser_container_builder.py; Abgleich gegen die im README "
            "dokumentierten Sicherheitsgarantien.",
            BODY),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Dedizierter Sub-Agent verfolgte Datenflussketten von Nutzereingaben "
            "(Containername, Homepage-URL, containers.json) bis zu "
            "Dateisystem-Operationen. 4 Kandidaten mit Konfidenz 7-8/10 "
            "identifiziert, 2 mit identischer Ursache zusammengefasst zu K1.",
            BODY),
        Paragraph("Phase 3 - Fix & Exploit-Verifikation", H3),
        Paragraph(
            "Alle 3 Kandidaten direkt am Quelltext bestaetigt. Patches implementiert: "
            "CONTAINER_NAME_PATTERN-Validierung, json.dumps()-Escaping in "
            "build_user_js_content(), _desktop_field()-Sanitizer. Mit Python-Repro-"
            "Skript verifiziert.",
            BODY),
        Paragraph("Phase 4 - Regressionscheck", H3),
        Paragraph(
            "tests/test_browser_container_builder.py (54 Tests) und "
            "tests/test_secure_browser_module.py (67 Tests) erneut ausgefuehrt - "
            "alle 121 weiterhin gruen nach den Fixes.",
            BODY),
    ]

    # ── Findings ────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bestaetigte Findings (alle in dieser Runde behoben)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    findings = [
        (
            "K1 — Fehlende Namensvalidierung: Pfad-Escape beim Anlegen von "
            "Browser-Containern  [Medium]",
            "tools/secure_browser_manager/browser_container_builder.py — "
            "validate_config_payload(); betrifft transitiv netmon/modules/"
            "secure_browser/manager.py.",
            "Das Feld 'name' wurde nur auf 'nicht leer' geprueft. Zielverzeichnis "
            "(base_dir / name) und .desktop-Dateiname wurden direkt daraus "
            "abgeleitet, ohne Zeichensatz- oder Confinement-Pruefung. Ein Name wie "
            "'../../../../.config/autostart/update-check' verschiebt den erzeugten "
            ".desktop-Eintrag in den Autostart-Ordner (Persistenz beim naechsten "
            "Login).",
            "CONTAINER_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$') in "
            "validate_config_payload() ergaenzt. Da CLI-Tool und NetMon-UI ueber "
            "denselben load_config()-Pfad laufen, schliesst ein Fixpunkt beide "
            "Einstiegspfade. Verifiziert: Escape-Name abgelehnt, regulaerer Name "
            "funktioniert weiter, 54 Tests gruen.",
        ),
        (
            "K2 — Firefox user.js-Praeferenz-Injection via Homepage-/Neue-Tab-URL  "
            "[Medium]",
            "tools/secure_browser_manager/browser_container_builder.py — "
            "build_user_js_content().",
            "homepage_url/new_tab_url wurden per f-string in "
            "user_pref(\"...\", \"{value}\"); eingesetzt, ohne Anfuehrungszeichen zu "
            "escapen. Ein Wert mit eingebettetem \" beendet den String vorzeitig und "
            "haengt beliebige weitere user_pref(...)-Aufrufe an — potenziell die "
            "eigene Isolations-Haertung des Containers aushebelnd (z. B. "
            "https_only_mode, cookieBehavior).",
            "Beide Werte werden jetzt mit json.dumps() kodiert. Verifiziert: "
            "derselbe Angriffswert erzeugt jetzt eine einzelne, harmlose "
            "user_pref-Zeile ohne injizierte Folgeanweisung.",
        ),
        (
            "K3 — Fehlende Zeilenumbruch-Bereinigung in .desktop-Launcher-Feldern  "
            "[Low]",
            "tools/secure_browser_manager/browser_container_builder.py — "
            "build_launcher_content(), build_existing_launcher_content(), "
            "build_menu_launcher_content().",
            "Name=/Comment=-Zeilen wurden direkt aus spec.name/menu_name gebildet, "
            "ohne eingebettete Zeilenumbrueche zu entfernen — potenziell zusaetzliche "
            "Desktop-Entry-Schluessel injizierbar (parserabhaengig auch ein "
            "zweiter Exec=-Eintrag).",
            "Neue Hilfsfunktion _desktop_field() entfernt \\r/\\n aus "
            "name/menu_name vor Einsatz in Name=/Comment= — an allen drei "
            "Launcher-Erzeugungsstellen angewendet.",
        ),
    ]

    for title, loc, detail, fix in findings:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [Paragraph("<b>Fix:</b> " + fix, s(
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

    # ── Verbesserungen seit Runde 4 ──────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Sicherheitsverbesserungen seit Runde 4", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("Agent-Runner-Allowlist verkleinert — agent/runner.py",
         "'python' und 'cat' aus ALLOWED_BASE_COMMANDS entfernt. Neu: "
         "ALLOWED_GIT_SUBCOMMANDS = {status, diff, log, show} begrenzt git auf "
         "Lesebefehle; _validate_repo_confined_arguments() erzwingt fuer "
         "black/ruff/pytest/ls, dass Pfadargumente innerhalb von REPO_ROOT liegen."),
        ("Repo-Confinement fuer Datei-Tools — agent/tools.py",
         "Neue Hilfsfunktion _ensure_repo_path() prueft in list_files() und "
         "read_file(), dass der aufgeloeste Pfad via relative_to(REPO_ROOT) "
         "innerhalb des Repositories bleibt."),
        ("sys.path-Bereinigung — tools/netmon.py",
         "Alle Eintraege, die auf NETMON_REPO_ROOT aufloesen, werden vor dem "
         "Neueinfuegen an Position 0 entfernt. Verhindert, dass ein veralteter "
         "Eintrag Vorrang vor dem echten Repository-Root bekommt."),
        ("Transparenz: eigene Listener in der Firewall-Ansicht erkennbar",
         "app.py + network_helpers.py: ss -lntupeH (cgroup-Ausgabe) ergaenzt; "
         "_is_netmon_listener()/_is_netmon_app_scope() erkennen NetMon-eigene "
         "Ports anhand Prozessname/PID/systemd-Scope."),
        ("Versions-Bump auf v1.1.16",
         "netmon/config/constants.py: NETMON_APP_VERSION von 1.1.15 auf 1.1.16 "
         "angehoben, passend zum in dieser Runde veroeffentlichten Codestand."),
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

    # ── Offene Empfehlung fuer Runde 6 ───────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("5. Offene Hardening-Empfehlung (Runde 6)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]
    open_rec_rows = [
        [Paragraph(
            "Client-seitige Namensvalidierung im Secure-Browser-Dialog",
            s("OT", fontName="Helvetica-Bold", fontSize=10, leading=14,
              textColor=C_AMBER)), Paragraph("")],
        [Paragraph(
            "Die Durchsetzung von K1 sitzt aktuell ausschliesslich in "
            "browser_container_builder.py (Subprocess-Ebene) — funktional "
            "korrekt und ausreichend (fail-closed), aber ein ungueltiger Name "
            "fuehrt im NetMon-UI-Dialog erst nach dem Subprocess-Aufruf zu einer "
            "Fehlermeldung statt zu sofortigem Inline-Feedback. Empfehlung: "
            "dieselbe CONTAINER_NAME_PATTERN-Pruefung zusaetzlich in "
            "manager.py::_resolve_create_inputs() spiegeln — reine "
            "UX-Verbesserung, keine sicherheitskritische Luecke.",
            BODY), Paragraph("")],
    ]
    open_rec_t = Table(open_rec_rows, colWidths=["80%", "20%"])
    open_rec_t.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("SPAN", (0, 1), (1, 1)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f2c185")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
        ("BACKGROUND", (0, 0), (-1, 0), C_BG_AMBER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [open_rec_t, Spacer(1, 3 * mm)]

    # ── Analysierte Kategorien ───────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("6. Gepruefte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def ok(text: str = "Kein Finding"):
        return Paragraph(text, s("OK", fontName="Helvetica-Bold", fontSize=10,
                                  textColor=C_GREEN))

    def warn(text: str):
        return Paragraph(text, s("WN", fontName="Helvetica-Bold", fontSize=10,
                                  textColor=C_AMBER))

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY), ok()],
        [Paragraph("Path Traversal (Dateioperationen mit Nutzereingabe)", BODY),
         warn("K1 -> behoben (Secure Browser Manager)")],
        [Paragraph("Privilege Escalation (sudo mit unkontrollierten Argumenten)", BODY), ok()],
        [Paragraph("Argument Injection (list-form subprocess mit externen Daten)", BODY), ok()],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval)", BODY), ok()],
        [Paragraph("Firefox user.js/Preference-Injection", BODY),
         warn("K2 -> behoben (Secure Browser Manager)")],
        [Paragraph("Desktop-Entry-Injection (.desktop Name=/Comment=)", BODY),
         Paragraph("K3 -> behoben (Secure Browser Manager)", s(
             "LOW", fontName="Helvetica-Bold", fontSize=10, textColor=C_AMBER))],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY), ok()],
        [Paragraph("Sensitive Data Exposure (PII in Logs)", BODY), ok()],
        [Paragraph("SSRF via urllib.request / externe URL-Weitergabe", BODY), ok()],
        [Paragraph("Kryptographische Schwachstellen", BODY), ok()],
        [Paragraph("Symlink-Angriffe auf privilegierte Dateioperationen", BODY), ok()],
        [Paragraph("Agent-Runner Command-/Pfad-Allowlist", BODY),
         ok("Gehaertet (agent/runner.py, agent/tools.py)")],
        [Paragraph("WireGuard-Hook-Ausfuehrung via Import (R4-K1)", BODY),
         Paragraph("Geschlossen (R4, FP)", MUTED)],
        [Paragraph("PATH-Hijacking via shutil.which (R3-K1)", BODY),
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
        Paragraph("7. Analysierte Module (Runde 5 — Sicherheitsfokus)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def okrow(text: str = "Kein Finding"):
        return Paragraph(text, s("OK2", fontName="Helvetica", fontSize=9,
                                  textColor=C_GREEN))

    module_rows = [
        [Paragraph("Datei / Modul", MUTED),
         Paragraph("Fokus", MUTED),
         Paragraph("Ergebnis", MUTED)],
        [Paragraph("netmon/modules/secure_browser/manager.py", MONO),
         Paragraph("Containername-/Pfad-Ableitung, Apply-Freigabe mit Bestaetigungscode", BODY),
         Paragraph("K1 -> behoben", MUTED)],
        [Paragraph("netmon/modules/secure_browser/service.py", MONO),
         Paragraph("Subprocess-Delegation (List-Form, shell=False), Backup-Rendering", BODY),
         okrow()],
        [Paragraph("netmon/modules/secure_browser/ui.py + secure_browser_tab.py", MONO),
         Paragraph("Tkinter-Formulare, Eingabe-Weiterleitung an manager.py", BODY),
         okrow()],
        [Paragraph("tools/secure_browser_manager/browser_container_builder.py", MONO),
         Paragraph("Namensvalidierung, Zielpfad-Aufbau, user.js/.desktop-Erzeugung", BODY),
         Paragraph("K1+K2+K3 -> behoben", MUTED)],
        [Paragraph("tools/secure_browser_manager/containers.example.json", MONO),
         Paragraph("Konfig-Schema", BODY),
         okrow()],
        [Paragraph("agent/runner.py", MONO),
         Paragraph("Allowlist verkleinert, git-Subcommand-Allowlist, Repo-Confinement", BODY),
         okrow("Kein Finding (Haertung)")],
        [Paragraph("agent/tools.py", MONO),
         Paragraph("_ensure_repo_path()-Guard fuer list_files/read_file", BODY),
         okrow("Kein Finding (Haertung)")],
        [Paragraph("netmon/features/vpn_controller.py", MONO),
         Paragraph("Preshared-Key-Feld, Validierung via validate_wireguard_key_value()", BODY),
         okrow()],
        [Paragraph("netmon/app.py + network_helpers.py", MONO),
         Paragraph("cgroup-basierte Selbst-Erkennung eigener Firewall-Listener", BODY),
         okrow()],
        [Paragraph("netmon/ui/tabs/log_tab.py", MONO),
         Paragraph("Auto-Clear-Log-Checkbox, nutzt bestehende Einstellung", BODY),
         okrow()],
        [Paragraph("tools/netmon.py", MONO),
         Paragraph("sys.path-Bereinigung vor Neueintrag", BODY),
         okrow("Kein Finding (Haertung)")],
        [Paragraph("netmon/app.py (Commit 9d660ae3)", MONO),
         Paragraph("Runtime-Log-Persistenz, Pfade rein intern (netmon_state_dir)", BODY),
         okrow()],
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
        Paragraph("Impressum und Haftungsausschluss", s(
            "H2", fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=colors.HexColor("#16263a"), spaceBefore=14, spaceAfter=6)),
        Paragraph("<b>Auditor:</b> Claude Sonnet 5 (Anthropic) — dedizierter Sub-Agent-Review + manuelle Fix-Verifikation per Exploit-Reproduktionsskript", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 05. Juli 2026", BODY),
        Paragraph("<b>Codestand:</b> 920cfc9b + Arbeitsstand (Secure Browser Manager, modified/untracked), ~13 Dateien — Runde 5", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation + Regressionstests (121/121 bestanden) — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r5.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
