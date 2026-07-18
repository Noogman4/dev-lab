#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.18 Runde 7."""

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
        title="NetMon Security Audit 2026 — v1.1.18 Runde 7",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.18 (Runde 7)",
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
    C_BLUE = colors.HexColor("#2563eb")
    C_MUTED = colors.HexColor("#9db5cc")
    C_LINE = colors.HexColor("#d9e1e7")
    C_BG_HEAD = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#f0fdf4")

    story = []

    # ── Titelseite ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph("SICHERHEITS-AUDIT — RUNDE 7", s(
            "EYEBROW", fontName="Helvetica", fontSize=10, leading=13,
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=6)),
        Paragraph("NetMon Roots v1.1.18", s(
            "TITLE", fontName="Helvetica-Bold", fontSize=28, leading=34,
            textColor=colors.HexColor("#16263a"), alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Code Security Review — Juli 2026", s(
            "SUB", fontName="Helvetica", fontSize=14, leading=18,
            textColor=colors.HexColor("#5f6368"), alignment=TA_CENTER, spaceAfter=20)),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "17. Juli 2026"],
        ["Analysierte Version", "v1.1.18 — Runde 7"],
        ["Neue Angriffsflaeche", "RKHunter-Referenz & Analyse, ClamAV-DB"],
        ["Bewertete Kandidaten", "4 (2 kein Finding)"],
        ["Ausnutzbare Findings", "0"],
        ["Haertungen umgesetzt", "2 (Defense-in-Depth)"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Regressionstests", "59 / 59 gruen"],
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
            "0 AUSNUTZBARE FINDINGS — 2 DEFENSE-IN-DEPTH-HAERTUNGEN UMGESETZT & VERIFIZIERT", s(
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
            "Die siebte Sicherheitsanalyse konzentrierte sich auf die seit dem "
            "Runde-6-Snapshot neu hinzugekommene Angriffsflaeche im Arbeitsstand — "
            "vor allem die RKHunter-Referenzuebernahme (rkhunter --propupd ueber "
            "run_rkhunter_propupd() / restore_property_database()), den neuen "
            "deterministischen Analysedienst (rkhunter_analysis_service.py) mit "
            "seinem propupd-Sicherheits-Gate, die im Scan-Worker neu ausgefuehrten "
            "privilegierten Hilfskommandos (dpkg -V/-S, file -b, cat "
            "/var/log/rkhunter.log) sowie die neue ClamAV-Signaturdatenbank-Auswahl "
            "(clamav_database_args) und die konfigurierbaren Schnellscan-Pfade.",
            BODY),
        Paragraph(
            "Ein Analyse-Sub-Agent identifizierte vier Kandidaten. Jeder wurde "
            "gegengeprueft, ergaenzt um eine empirische Reproduktion des "
            "Klassifizierer-Verhaltens am realen Modul. Zwei Kandidaten wurden als "
            "'kein Finding' verworfen, zwei lagen unterhalb der Schwelle von 8/10, "
            "wurden aber dennoch als Defense-in-Depth direkt umgesetzt und "
            "empirisch verifiziert. Grund fuer die Einstufung unter der Schwelle: In "
            "einem Einzelnutzer-Desktop-Werkzeug stammt die vermeintliche "
            "'Angreifer'-Eingabe entweder vom selben lokalen Nutzer oder setzt "
            "bereits lokale Root-Rechte voraus — es wird keine echte "
            "Vertrauensgrenze ueberschritten.",
            BODY),
        Paragraph(
            "K1 (Konfidenz 3/10, gehaertet): Die FP-Klassifizierung des "
            "propupd-Gates war zu breit — _EXPECTED_CONFIG_RE matchte jede "
            "*.conf-Datei, _DEVELOPER_ENV_RE bloße Substrings wie 'docker'/'vscode', "
            "wodurch selbst eine nicht paketverwaltete /etc/cron.d/persist.conf als "
            "'expected' galt und das Gate oeffnete. Jetzt gehaertet: Whitelist statt "
            "Wildcard und Wortgrenzen fuer Entwicklungs-Pfade. Empirisch "
            "gegengeprueft — solche Aenderungen fallen nun nach 'review', das Gate "
            "bleibt geschlossen (propupd_allowed=False), legitime Faelle bleiben "
            "'expected'.",
            BODY),
        Paragraph(
            "K2 (Konfidenz 2/10, gehaertet): Die ClamAV-Signaturdatenbank liegt in "
            "einem vorhersagbaren /tmp-Pfad (netmon-clamav-db-<user>). Jetzt "
            "gehaertet: _clamav_database_dir_is_secure() laesst clamscan --database "
            "nur auf ein Verzeichnis zeigen, das dem aktuellen Nutzer gehoert, kein "
            "Symlink ist und keine Gruppen-/Welt-Rechte traegt (& 0o077 == 0). "
            "Empirisch gegengeprueft — fremd-owned, welt-/gruppen-zugaengliche und "
            "symlink-Verzeichnisse werden abgelehnt.",
            BODY),
        Paragraph(
            "K3 (kein Finding): Die neuen sudo-Hilfskommandos erhalten Pfade aus der "
            "rkhunter-Ausgabe, laufen aber alle ueber run_cmd() in Listenform ohne "
            "shell=True — keine Command- oder Argument-Injection.",
            BODY),
        Paragraph(
            "K4 (kein Finding): backup/restore_property_database() nutzen sudo cp -a, "
            "beschraenken die Pfade jedoch per _normalize_allowed_path(allow_prop_db=True) "
            "fail-closed auf zwei fest kodierte Realpaths; vor der Wiederherstellung "
            "wird die Existenz des NetMon-Backups verlangt. Keine Pfad-Traversal.",
            BODY),
        Paragraph(
            "Alle 59 relevanten automatisierten Tests bleiben nach den Haertungen "
            "gruen. Der Codestand v1.1.18 enthaelt keine offenen ausnutzbaren "
            "Sicherheitsluecken; die in Runde 6 gehaerteten Bereiche (Secure Browser "
            "Manager, Agent-Confinement) waren in diesem Arbeitsstand unveraendert.",
            BODY),
    ]

    # ── Methodik ──────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Diff- & Reconnaissance", H3),
        Paragraph(
            "Vollstaendiger git diff gegen den letzten Commit (c2087b63) plus "
            "Sichtung der neuen unversionierten Dateien (rkhunter_analysis_service.py "
            "und zugehoerige Tests); gezieltes Lesen der neuen RKHunter-Pfade und der "
            "ClamAV-Datenbankwahl.",
            BODY),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Ein dedizierter Analyse-Sub-Agent verfolgte Datenflussketten von "
            "rkhunter-/dpkg-Ausgaben und lokalen Eingaben bis zu sensiblen "
            "Operationen (sudo cp -a, subprocess.run, --propupd, clamscan --database). "
            "4 Kandidaten identifiziert.",
            BODY),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Fuer jeden Kandidaten lief eine eigene Validierung mit striktem "
            "FP-Filter-Regelwerk und Konfidenz-Scoring, ergaenzt um eine empirische "
            "Reproduktion des Klassifizierer-Verhaltens am realen Modul. Ergebnis: "
            "2 kein Finding, 2 unter der Schwelle (2-3/10).",
            BODY),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "Die beiden Kandidaten unter der Schwelle wurden als Defense-in-Depth "
            "umgesetzt, empirisch am realen Modul gegengeprueft und mit neuen "
            "Regressionstests abgesichert. Suiten erneut ausgefuehrt: "
            "test_rkhunter_analysis_service.py, test_rkhunter_security_flow.py, "
            "test_rkhunter_manager.py, test_clamav_controller.py — "
            "59 Tests, alle gruen.",
            BODY),
    ]

    # ── Kandidaten ────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bewertete Kandidaten", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    findings = [
        (
            "K1 — Zu permissive FP-Klassifizierung im propupd-Gate  [Konfidenz 3/10, gehaertet]",
            "netmon/services/rkhunter_analysis_service.py — _classify_rkhunter_line() / "
            "analyze_rkhunter_output(), ausgewertet in _rkhunter_propupd_gate_valid().",
            "Das Gate entscheidet, ob der aktuelle Dateizustand per rkhunter --propupd "
            "als neue vertrauenswuerdige Referenz uebernommen werden darf. "
            "_EXPECTED_CONFIG_RE matchte mit dem Teilmuster [^\\s:]+\\.conf jede Datei "
            "mit .conf-Endung (z. B. /etc/cron.d/persist.conf), und _DEVELOPER_ENV_RE "
            "matchte bloße Substrings wie 'docker'/'containerd'/'vscode' an beliebiger "
            "Stelle. Solche Zeilen wurden 'expected'; empirisch verifiziert fiel das "
            "Risiko dann auf 'low' und propupd_allowed wurde True — obwohl die Datei "
            "nicht paketverwaltet ist und daher von dpkg -V nicht erfasst wird. Unter "
            "der Schwelle, weil das Platzieren einer solchen Datei bereits Root "
            "voraussetzt und die Referenzuebernahme manuell, doppelt bestaetigt und "
            "sudo-geschuetzt ist — keine Privilegien-Eskalation.",
            "Gehaertet & verifiziert: _EXPECTED_CONFIG_RE wurde auf eine explizite "
            "Whitelist bekannter Konfigurationsdateien eingeschraenkt (rkhunter.conf, "
            "gdm3/custom.conf, fwupd.conf, systemd/resolved.conf, "
            "systemd/timesyncd.conf, mirrors.dat); _DEVELOPER_ENV_RE nutzt jetzt "
            "Wortgrenzen und Pfadsegment-Anker. Empirisch gegengeprueft: "
            "/etc/cron.d/persist.conf und .../dockerish-malware fallen nun nach "
            "'review', das Gate schliesst (risk=medium, propupd_allowed=False), "
            "waehrend /etc/rkhunter.conf, /usr/bin/docker und .vscode/ weiterhin "
            "korrekt 'expected' bleiben. Mit Regressionstests abgesichert.",
        ),
        (
            "K2 — ClamAV-Signaturdatenbank in vorhersagbarem /tmp-Pfad  [Konfidenz 2/10, gehaertet]",
            "netmon/features/clamav_controller.py — clamav_user_database_dir() / "
            "clamav_database_args() / _clamav_database_dir_is_secure().",
            "Nach einem nutzergetriebenen ClamAV-Update ohne sudo liegen die Signaturen "
            "in <tmp>/netmon-clamav-db-<user> und werden via clamscan --database "
            "genutzt. Der Pfad ist vorhersagbar; auf einem gemeinsam genutzten Host "
            "koennte ein Fremdnutzer das Verzeichnis theoretisch mit eigenen "
            ".cvd/.cld-Dateien vorbelegen und die Signaturbasis beeinflussen. Unter der "
            "Schwelle, weil das Zielprofil ein Einzelnutzer-Desktop ist und NetMon dem "
            "Verzeichnis erst nach erfolgreichem freshclam-Lauf vertraut.",
            "Gehaertet & verifiziert: Vor jeder Verwendung von clamscan --database "
            "prueft _clamav_database_dir_is_secure() das Verzeichnis — es muss dem "
            "aktuellen Nutzer gehoeren (st_uid == os.getuid()), darf kein Symlink sein "
            "und keine Gruppen-/Welt-Rechte tragen (st_mode & 0o077 == 0). Empirisch "
            "gegengeprueft: fremd-owned, gruppen-/welt-zugaengliche, symlink- und "
            "fehlende Verzeichnisse werden abgelehnt — nur ein eigenes 0700-Verzeichnis "
            "wird als Signaturquelle akzeptiert. Das /tmp-Vorbelegungs-Szenario ist "
            "geschlossen; mit Regressionstests abgesichert.",
        ),
        (
            "K3 — Neue privilegierte Hilfskommandos im Scan-Worker  [kein Finding]",
            "netmon/features/security_audit_controller.py — rkhunter_scan_worker().",
            "Der Scan-Worker fuehrt neu sudo -n dpkg -V, dpkg -S <pfad>, file -b <pfad> "
            "und sudo -n cat /var/log/rkhunter.log aus. Die Pfade stammen aus der "
            "rkhunter-Ausgabe (extract_replaced_script_paths / "
            "extract_warning_command_paths), also aus extern beeinflussbarem Text. "
            "Bewertung: Alle Aufrufe laufen ueber run_cmd(), das subprocess.run() in "
            "Listenform ohne shell=True nutzt. Pfade werden als einzelne argv-Elemente "
            "an dpkg -S / file -b uebergeben — keine Shell-Interpolation, keine "
            "Option-Injection. Kein Command- oder Argument-Injection-Pfad.",
            "Kein Finding. Die neuen Hilfskommandos sind gegen Shell- und "
            "Argument-Injection abgesichert.",
        ),
        (
            "K4 — cp -a auf die RKHunter-Referenzdatenbank  [kein Finding]",
            "netmon/core/rkhunter_manager.py — backup_property_database() / "
            "restore_property_database().",
            "Beide Funktionen kopieren die rkhunter-Referenz-DB per sudo -n cp -a. "
            "Beide Pfade laufen zuerst durch _normalize_allowed_path(allow_prop_db=True), "
            "das os.realpath() anwendet und ausschließlich die zwei fest kodierten "
            "Zielpfade (rkhunter.dat und ....netmon.bak) zulaesst; alles andere liefert "
            "einen leeren String und die Operation bricht mit 'Nicht erlaubter "
            "rkhunter-Datenbankpfad' ab. Vor der Wiederherstellung wird zudem die "
            "Existenz des NetMon-Backups (test -f) verlangt. Fail-closed, keine "
            "Pfad-Traversal.",
            "Kein Finding. Die Referenz-Sicherung ist fail-closed auf eine feste "
            "Pfad-Allowlist begrenzt.",
        ),
    ]

    for title, loc, detail, fix in findings:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [Paragraph("<b>Bewertung:</b> " + fix, s(
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
        Paragraph("4. Umgesetzte Defense-in-Depth-Haertungen (Runde 7)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("Konservativeres propupd-Gate — rkhunter_analysis_service.py",
         "_EXPECTED_CONFIG_RE nutzt statt der .conf-Wildcard eine explizite Whitelist "
         "bekannter Konfigurationsdateien; _DEVELOPER_ENV_RE ist mit Wortgrenzen und "
         "Pfadsegment-Ankern versehen. Eine nicht paketverwaltete /etc-Aenderung "
         "faellt jetzt nach 'review' — das Gate bleibt fail-closed "
         "(propupd_allowed=False). Empirisch gegengeprueft, legitime Faelle bleiben "
         "'expected'."),
        ("Owner-/Rechte-Pruefung der ClamAV-Signaturdatenbank — clamav_controller.py",
         "_clamav_database_dir_is_secure() laesst clamscan --database nur auf ein "
         "Verzeichnis zeigen, das dem aktuellen Nutzer gehoert, kein Symlink ist und "
         "keine Gruppen-/Welt-Rechte traegt (& 0o077 == 0). Das "
         "/tmp-Vorbelegungs-Szenario ist damit geschlossen."),
        ("Neue Regressionstests — 59 / 59 gruen",
         "test_rkhunter_analysis_service.py und test_clamav_controller.py wurden um "
         "Tests fuer die verschaerfte Klassifizierung bzw. die "
         "Verzeichnis-Sicherheitspruefung erweitert. Alle relevanten Suiten bestehen "
         "nach den Haertungen vollstaendig."),
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

    # ── Analysierte Kategorien ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("5. Geprüfte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def ok(text: str = "Kein Finding"):
        return Paragraph(text, s("OK", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_GREEN))

    def info(text: str):
        return Paragraph(text, s("IN", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_BLUE))

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("Command Injection (subprocess, shell=True)", BODY), ok()],
        [Paragraph("Argument Injection (Pfade aus rkhunter-Ausgabe an dpkg/file)", BODY),
         ok("Kein Finding (K3, list-form)")],
        [Paragraph("Path Traversal (cp -a der Referenz-DB)", BODY),
         ok("Kein Finding (K4, fail-closed)")],
        [Paragraph("Sicherheitskontroll-Umgehung (propupd-Gate zu permissiv)", BODY),
         ok("K1 -> gehaertet (Whitelist)")],
        [Paragraph("Signatur-/Datenbank-Vertrauen (ClamAV --database)", BODY),
         ok("K2 -> gehaertet (Owner/Rechte)")],
        [Paragraph("Privilegierte Kommandos (sudo -n Umfang & Argumente)", BODY), ok()],
        [Paragraph("TOCTOU / Symlink bei Verzeichniserstellung", BODY),
         ok("Kein Finding (_safe_makedirs_no_symlink)")],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval)", BODY), ok()],
        [Paragraph("Persistierte Konfiguration (Schnellscan-Pfade in Settings)", BODY),
         ok("Kein Finding (normalisiert/validiert)")],
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
        Paragraph("<b>Auditor:</b> Claude Fable 5 (Anthropic) — Analyse-Sub-Agent + False-Positive-Validierung mit empirischer Reproduktion am realen Modul", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 17. Juli 2026", BODY),
        Paragraph("<b>Codestand:</b> c2087b63 + Arbeitsstand (modified/untracked), Fokus RKHunter-Referenzuebernahme, deterministische Analyse & ClamAV-Datenbankwahl — Runde 7", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation + empirische Reproduktion des Klassifizierer-Verhaltens + Konfidenz-gescorte FP-Validierung + Umsetzung der beiden Haertungen mit empirischer Gegenpruefung + Regressionstests (59/59 relevante Tests bestanden) — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r7.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
