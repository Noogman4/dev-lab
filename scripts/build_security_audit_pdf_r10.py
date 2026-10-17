#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.20 Runde 10."""

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
        title="NetMon Security Audit 2026 — v1.1.20 Runde 10",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.20 (Runde 10)",
    )

    styles = getSampleStyleSheet()

    def s(name: str, **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

    H1 = s(
        "H1",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        textColor=colors.HexColor("#16263a"),
        spaceBefore=8,
        spaceAfter=10,
    )
    H3 = s(
        "H3",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#16263a"),
        spaceBefore=10,
        spaceAfter=4,
    )
    BODY = s(
        "BODY",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#202124"),
        spaceAfter=6,
    )
    MUTED = s(
        "MUTED",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#5f6368"),
        spaceAfter=5,
    )
    MONO = s(
        "MONO",
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0b5d0e"),
        spaceAfter=4,
    )
    FINDING_TITLE = s(
        "FINDING_TITLE",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#16263a"),
        spaceAfter=3,
    )
    FIXED_TITLE = s(
        "FIXED_TITLE",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#145a32"),
        spaceAfter=3,
    )

    C_GREEN = colors.HexColor("#15803d")
    C_AMBER = colors.HexColor("#b45309")
    C_BLUE = colors.HexColor("#2563eb")
    C_MUTED = colors.HexColor("#9db5cc")
    C_LINE = colors.HexColor("#d9e1e7")
    C_BG_HEAD = colors.HexColor("#eef3f7")
    C_BG_GREEN = colors.HexColor("#f0fdf4")
    C_BG_AMBER = colors.HexColor("#fffbeb")
    C_BG_RED = colors.HexColor("#fef2f2")

    story = []

    # ── Titelseite ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph(
            "SICHERHEITS-AUDIT — RUNDE 10",
            s(
                "EYEBROW",
                fontName="Helvetica",
                fontSize=10,
                leading=13,
                textColor=C_MUTED,
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
        ),
        Paragraph(
            "NetMon Roots v1.1.20",
            s(
                "TITLE",
                fontName="Helvetica-Bold",
                fontSize=28,
                leading=34,
                textColor=colors.HexColor("#16263a"),
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
        ),
        Paragraph(
            "Code Security Review — Juli 2026",
            s(
                "SUB",
                fontName="Helvetica",
                fontSize=13,
                leading=18,
                textColor=colors.HexColor("#5f6368"),
                alignment=TA_CENTER,
                spaceAfter=20,
            ),
        ),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "19. Juli 2026"],
        ["Analysierte Version", "v1.1.20"],
        [
            "Schwerpunkt",
            "Security-Baseline-/Sysctl-Apply-Stufe, Baseline-Transferpaket, UFW-Locale, Test-Infrastruktur",
        ],
        ["Kritische Findings", "0"],
        ["Hohe Findings", "2 (beide behoben & verifiziert)"],
        ["Mittlere Findings", "0"],
        ["Haertungen umgesetzt", "2 + 15 neue Regressionstests"],
        ["Gesamt-Testsuite", "2133 bestanden (3 bekannte Umgebungsfehler)"],
        ["Analysewerkzeug", "Claude Fable 5 (Anthropic)"],
        ["Projektverantwortlicher", "Sven Froehlich"],
    ]
    meta_table = Table(
        [[Paragraph(k, MUTED), Paragraph(v, BODY)] for k, v in meta_data],
        colWidths=[60 * mm, None],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), C_BG_HEAD),
                ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story += [meta_table, Spacer(1, 8 * mm)]

    verdict_table = Table(
        [
            [
                Paragraph(
                    "0 KRITISCHE — 2 HOHE — 0 MITTLERE FINDINGS (BEIDE UMGESETZT & VERIFIZIERT)",
                    s(
                        "VT",
                        fontName="Helvetica-Bold",
                        fontSize=11.5,
                        leading=16,
                        textColor=C_AMBER,
                        alignment=TA_CENTER,
                    ),
                )
            ]
        ],
        colWidths=["100%"],
    )
    verdict_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_BG_AMBER),
                ("BOX", (0, 0), (-1, -1), 1.5, C_AMBER),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story += [verdict_table, PageBreak()]

    # ── Zusammenfassung ───────────────────────────────────────────────────────
    story += [
        Paragraph("1. Zusammenfassung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die zehnte Sicherheitsanalyse pruefte den kompletten Code-Diff seit "
            "dem Runde-9-Stand — rund 15.300 neue Zeilen, ueberwiegend die neue "
            "Security-Baseline-/Lynis-Funktionalitaet, die neue Sysctl-Apply-Stufe "
            "samt Baseline-Transferpaket (Export/Import zwischen Rechnern), die "
            "locale-unabhaengige UFW-Auswertung, das neue Daten-Backup und die "
            "neuen, rein lesenden System-Checks (Home-/Dateirechte, Secure Boot, "
            "APT-Sicherheitsupdates). Ergaenzend im Fokus: die privilegierten "
            "Senken (sudo -n, pkexec, root-netmon_network_service) und die "
            "Test-/Entwicklungsinfrastruktur.",
            BODY,
        ),
        Paragraph(
            "Diese Runde brachte zwei belastbare Schwachstellen hohen "
            "Schweregrads. Beide wurden direkt umgesetzt, mit Regressionstests "
            "abgesichert und verifiziert. Keine kritischen, keine "
            "remote-ausloesbaren Befunde.",
            BODY,
        ),
        Paragraph(
            "F1 (HIGH, Konfidenz 9/10, behoben): Das neue Baseline-Transferpaket — "
            "eine per Dateidialog importierte JSON-Datei, gedacht zum Teilen "
            "gehaerteter Profile zwischen Rechnern — reichte die Felder "
            "id/key/expected ohne Zeichen- oder Whitelist-Pruefung bis in eine "
            "Datei unter /etc/sysctl.d/ durch, die als root per "
            "'sudo -n sysctl --system' geladen wird. Eine praeparierte Datei mit "
            "id=sysctl.kernel.core_pattern und expected=|/tmp/evil.sh erzeugte die "
            "Zeile 'kernel.core_pattern = |/tmp/evil.sh' — der Kernel fuehrt danach "
            "bei jedem Prozess-Crash das Programm als root aus (klassische "
            "Rechteausweitung). Eingebettete Zeilenumbrueche ueberlebten das "
            ".strip() und erlaubten das stille Herabsetzen der Kernel-Haertung. Ein "
            "dedizierter Validierungs-Sub-Agent bestaetigte das mit Konfidenz 9/10 "
            "und lauffaehigem Repro. Gehaertet: importierte Sysctl-Eintraege "
            "werden jetzt gegen eine Allowlist der zehn dokumentierten "
            "Baseline-Schluessel plus ein strenges Schluessel-/Wertformat geprueft "
            "(keine Zeilenumbrueche, Pipes, Shell-Metazeichen); die Drop-in-id wird "
            "nur aus dem validierten Schluessel abgeleitet; eine zweite "
            "Verteidigungslinie filtert direkt an der Schreibsenke.",
            BODY,
        ),
        Paragraph(
            "F2 (HIGH, empirisch entdeckt, behoben): Zwei Tests fuer die neuen "
            "Systemaktionen (Reboot/Shutdown/Logout) liessen einen "
            "Kommando-Generator das echte ['systemctl','reboot'] zurueckgeben, ohne "
            "run_cmd bzw. den ausfuehrenden Job-Thread zu mocken. Da ein aktiver "
            "Desktop-Nutzer ueber polkit ohne Passwort neu starten darf, fuehrte "
            "jeder Lauf der Testsuite auf einem Desktop-System zu einem "
            "tatsaechlichen Neustart des Rechners. Dieses Finding wurde nicht "
            "statisch, sondern empirisch entdeckt: Der Audit-Host startete beim "
            "Testlauf reproduzierbar neu; die Boot-Zeitstempel deckten sich exakt "
            "mit den Testlaeufen. Betroffen ist die Test-/Entwicklungs- und "
            "CI-Infrastruktur, nicht der ausgelieferte Anwendungscode (dessen "
            "Release-Pfad durch Bestaetigungsdialog, Sicherungsphrase und "
            "Strict-Protection abgesichert ist). Gehaertet: beide Tests brechen vor "
            "dem Job-Thread ab und nutzen inerte Stubs; zusaetzlich blockiert ein "
            "suiteweiter Guard (tests/conftest.py) destruktive Kommandos hart auf "
            "subprocess-Ebene — auch hinter sudo/pkexec-Wrappern.",
            BODY,
        ),
        Paragraph(
            "Ergaenzend: Eine latente Shell-Injektion ueber das aus dem "
            "importierten Schluessel gebildete 'sysctl -n {key}'-Kommando-Template "
            "(aktuell nicht erreichbar) wird durch die strenge Schluessel-Pruefung "
            "aus F1 automatisch mitentschaerft. Die Game-Mode-UFW-Ausnahmen sind "
            "kein ausnutzbarer Befund (argv-Token, ufw lehnt Ungueltiges ab). Die "
            "Kindersicherung bleibt als bewusste Design-Entscheidung dokumentiert; "
            "die postinst-DNS-Policy (8.8.8.8) und die Nur-Hash-Schnellpruefung auf "
            "der Downloadseite bleiben als Runde-9-Hinweise offen. Alle "
            "Runde-7/8/9-Haertungen sind intakt; Versionskonsistenz (App, deb, "
            "Changelog) ist durchgaengig 1.1.20.",
            BODY,
        ),
    ]

    # ── Methodik ──────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Diff-Recon", H3),
        Paragraph(
            "Vollstaendige, datei-weise Sichtung des Branch-Diffs seit dem "
            "Runde-9-Stand (Commit ac412cbc). Versionskonsistenz-Abgleich (App = "
            "deb = Changelog = 1.1.20). Suche nach neuen Datenfluessen von "
            "Fremdeingaben (importierte Dateien, geparster Kommando-Output) zu "
            "privilegierten Senken.",
            BODY,
        ),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Ein Analyse-Sub-Agent verfolgte importierte und geparste Daten bis zu "
            "sudo/pkexec-Aufrufen und Datei-Schreibpfaden. Drei Kandidaten "
            "identifiziert — einer belastbar (Sysctl-Injektion), zwei als "
            "Defense-in-Depth (latente command-Injektion, Game-Mode-Port).",
            BODY,
        ),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Der belastbare Kandidat wurde von einem eigenen Validierungs-Sub-"
            "Agenten mit lauffaehigem Repro gegengeprueft: Konfidenz 9/10, HIGH. "
            "Ein Detail-Ueberclaim (angeblich angreiferkontrollierter Schreibpfad) "
            "wurde dabei widerlegt — der Zielpfad ist fix; fuer die Ausnutzbarkeit "
            "irrelevant, da der feste Pfad ohnehin als root geladen wird.",
            BODY,
        ),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "Beide HIGH-Findings wurden umgesetzt und mit 15 neuen "
            "Regressionstests abgesichert (8 fuer die Sysctl-Allowlist, 7 fuer den "
            "Kommando-Guard). Gesamtsuite erneut ausgefuehrt: 2133 bestanden. Die "
            "drei verbleibenden Fehler sind bekannte, umgebungsbedingte Faelle ohne "
            "Sicherheitsbezug (installiertes Radio-Desktop-File gewinnt gegen den "
            "Laufzeitpfad; echtes proton-de-VPN-Profil des Hosts).",
            BODY,
        ),
    ]

    # ── Findings ──────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bestaetigte Findings", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    findings = [
        (
            "F1 — Sysctl-Direktiven-Injektion ueber importiertes Baseline-Transferpaket  "
            "[HIGH, Konfidenz 9/10, behoben]",
            "netmon/features/security_audit_controller.py — "
            "_sanitize_transfer_sysctl_entries() / _build_sysctl_dropin_content() / "
            "apply_security_baseline_sysctl() / import_security_baseline_transfer().",
            "Das neue Baseline-Transferpaket (per Dateidialog importierte JSON, "
            "gedacht zum Teilen gehaerteter Profile zwischen Rechnern) durchlief "
            "eine Sanitisierung, die nur auf nicht-leer prueft — ohne Zeichen- oder "
            "Whitelist-Validierung von id/key/expected. Die Werte wurden als "
            "'key = value' in eine Datei unter /etc/sysctl.d/ geschrieben und per "
            "'sudo -n sysctl --system' als root geladen. Eine praeparierte Datei "
            "mit id=sysctl.kernel.core_pattern und expected=|/tmp/evil.sh erzeugte "
            "'kernel.core_pattern = |/tmp/evil.sh' — der Kernel fuehrt danach bei "
            "jedem Prozess-Crash das Programm als root aus (Rechteausweitung). "
            "Eingebettete Zeilenumbrueche ueberlebten das .strip() und erlaubten "
            "mehrere eingeschleuste Direktiven bzw. das stille Herabsetzen der "
            "Kernel-Haertung, waehrend die UI 'Haertung angewendet' meldete. Kein "
            "Zero-Click (Import + Bestaetigung + sudo-Session noetig), aber ein "
            "realistischer Social-Engineering-Pfad, da Transferpakete explizit zum "
            "Teilen gedacht sind. Anders als die parallele UFW-Validierung "
            "(ValueError bei ungueltigen Regeln) filterte der Sysctl-Pfad nichts.",
            "Gehaertet & verifiziert: Neue Allowlist "
            "SECURITY_BASELINE_ALLOWED_SYSCTL_KEYS (zehn dokumentierte Schluessel, "
            "siehe docs/security/KERNEL_SYSCTL.md) plus Format-Regex fuer Schluessel "
            "und Werte. _sanitize_transfer_sysctl_entries() lehnt unerlaubte "
            "Schluessel und ungueltige Werte (Zeilenumbrueche, Pipes, "
            "Shell-Metazeichen) per ValueError ab und leitet die Drop-in-id nur aus "
            "dem validierten Schluessel ab, nie aus dem freien id-Feld. Zweite "
            "Verteidigungslinie in _build_sysctl_dropin_content() filtert direkt an "
            "der Schreibsenke. Mit acht neuen Regressionstests abgesichert.",
        ),
        (
            "F2 — Testsuite fuehrte echtes 'systemctl reboot' aus (Host-Neustart)  "
            "[HIGH, empirisch entdeckt, behoben]",
            "tests/test_netmon_diagnostics.py (run_system_action_async-Tests); "
            "netmon/app.py (_system_action_commands / Job-Thread).",
            "Zwei Tests fuer die neuen Systemaktionen (Reboot/Shutdown/Logout) "
            "prueften die Bestaetigungsphrase, stubbten aber den Kommando-Generator "
            "so, dass er das echte ['systemctl','reboot'] zurueckgab — ohne run_cmd "
            "bzw. den ausfuehrenden Job-Thread zu mocken. Da ein aktiver "
            "Desktop-Nutzer ueber polkit ohne Passwort neu starten darf, fuehrte "
            "jeder Lauf der Testsuite auf einem Desktop-System zu einem "
            "tatsaechlichen Neustart des Rechners. Empirisch entdeckt: Der "
            "Audit-Host startete beim Testlauf reproduzierbar neu; die "
            "Boot-Zeitstempel deckten sich exakt mit den Testlaeufen. Einordnung: "
            "betrifft die Test-/Entwicklungs- und CI-Infrastruktur, nicht den "
            "ausgelieferten Anwendungscode (dessen Release-Pfad durch "
            "Bestaetigungsdialog, Sicherungsphrase AUSFUEHREN und Strict-Protection "
            "abgesichert ist). Wirkung dennoch hoch: unerwarteter Neustart mit "
            "Risiko fuer ungespeicherte Arbeit auf jeder Maschine, die die Suite "
            "ausfuehrt.",
            "Gehaertet & verifiziert: Beide Tests brechen jetzt vor dem Job-Thread "
            "ab und verwenden nur inerte Stub-Kommandos. Zusaetzlich blockiert ein "
            "suiteweiter Guard (tests/conftest.py) destruktive Kommandos "
            "(systemctl reboot/poweroff/halt, shutdown, reboot, "
            "loginctl terminate-*) hart auf subprocess-Ebene — auch hinter "
            "sudo/pkexec/env-Wrappern und in Shell-String-Form. Mit sieben neuen "
            "Regressionstests (test_destructive_command_guard.py) abgesichert.",
        ),
    ]

    for title, loc, detail, fix in findings:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [
                Paragraph(
                    "<b>Behebung:</b> " + fix,
                    s(
                        "VD",
                        fontName="Helvetica",
                        fontSize=9,
                        leading=13,
                        textColor=colors.HexColor("#145a32"),
                        backColor=C_BG_GREEN,
                        leftIndent=4,
                    ),
                ),
                Paragraph(""),
            ],
        ]
        t = Table(rows, colWidths=["82%", "18%"])
        t.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("SPAN", (0, 1), (1, 1)),
                    ("SPAN", (0, 2), (1, 2)),
                    ("SPAN", (0, 3), (1, 3)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f0a0a0")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), C_BG_RED),
                    ("BACKGROUND", (0, 3), (-1, 3), C_BG_GREEN),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story += [t, Spacer(1, 5 * mm)]

    # ── Weitere Beobachtungen ─────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Weitere Beobachtungen & Design-Entscheidungen", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    observations = [
        (
            "Latente Shell-Injektion ueber das command-Feld — mitbehoben",
            "Der importierte Sysctl-Schluessel floss auch in ein "
            "'sysctl -n {key}'-Kommando-Template. Aktuell nicht erreichbar (die "
            "Auswertung nutzt die statische Baseline-Liste), aber ein spaeteres "
            "Refactoring haette daraus eine Kommando-Injektion machen koennen. Durch "
            "die neue strenge Schluessel-Validierung aus F1 automatisch "
            "mitentschaerft.",
        ),
        (
            "Game-Mode-UFW-Ausnahmen — kein ausnutzbarer Befund",
            "Der Port des Spielmodus wird nicht per Regex vorgeprueft, geht aber als "
            "einzelnes argv-Token an 'sudo -n ufw allow ...' (kein Shell-Parsing; ufw "
            "lehnt Ungueltiges ab); der benutzerdefinierte Pfad validiert bereits "
            "streng (isdigit, 1-65535, Protokoll-Whitelist). Nur zur Vollstaendigkeit "
            "notiert.",
        ),
        (
            "Kindersicherung — weiterhin bewusste Design-Entscheidung",
            "Die PBKDF2-gestuetzte Kindersicherung im Secure-Browser bleibt wie in "
            "Runde 8 dokumentiert: Alltagshuerde gegen Gelegenheitszugriff im selben "
            "Konto, keine harte Grenze gegen technisch versierte Nutzer mit "
            "Kontozugriff. Keine Codeaenderung, unveraendert gueltig.",
        ),
        (
            "postinst-DNS & Nur-Hash-Schnellpruefung — Policy-Hinweise offen",
            "Die beiden Policy-Hinweise aus Runde 9 bleiben bestehen: Das "
            "root-postinst biegt aktive NM-DNS bei der Installation auf 8.8.8.8 "
            "(Opt-in empfohlen), und die Schnellpruefung auf der Downloadseite "
            "empfiehlt nur sha256sum -c statt der minisign-Vollpruefung. Kein "
            "ausnutzbarer Befund — als Design-Entscheidungen des "
            "Projektverantwortlichen offen.",
        ),
    ]

    for title, desc in observations:
        rows = [
            [Paragraph(title, FIXED_TITLE), Paragraph("")],
            [Paragraph(desc, BODY), Paragraph("")],
        ]
        t = Table(rows, colWidths=["82%", "18%"])
        t.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("SPAN", (0, 1), (1, 1)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#a3d9b8")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), C_BG_GREEN),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story += [t, Spacer(1, 3 * mm)]

    # ── Umgesetzte Haertungen ─────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("5. Umgesetzte Haertungen (Runde 10)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        (
            "Sysctl-Allowlist + Wert-Validierung fuer importierte Transferpakete — security_audit_controller.py",
            "Neue Konstante SECURITY_BASELINE_ALLOWED_SYSCTL_KEYS (zehn dokumentierte "
            "Schluessel) plus Format-Regex fuer Schluessel und Werte. "
            "_sanitize_transfer_sysctl_entries() lehnt unerlaubte Schluessel und "
            "ungueltige Werte per ValueError ab und leitet die id nur aus dem "
            "validierten Schluessel ab; _build_sysctl_dropin_content() filtert als "
            "zweite Verteidigungslinie an der Schreibsenke.",
        ),
        (
            "Suiteweiter Guard gegen destruktive Systemkommandos — tests/conftest.py",
            "Ein subprocess.Popen-Wrapper blockiert systemctl reboot/poweroff/halt, "
            "shutdown, reboot, poweroff, halt, telinit und loginctl terminate-* — auch "
            "hinter sudo/pkexec/env-Wrappern und in Shell-String-Form. Kein Test kann "
            "je wieder ein echtes destruktives Kommando bis zum System durchreichen.",
        ),
        (
            "15 neue Regressionstests",
            "Acht Tests in test_netmon_lynis_output.py fuer die Sysctl-Allowlist "
            "(Ablehnung von core_pattern, Pipe-/Newline-Werten, id-Ableitung, "
            "End-to-End-Import-Refusal) und sieben in "
            "test_destructive_command_guard.py fuer den Kommando-Guard. Gesamtsuite: "
            "2133 bestanden.",
        ),
    ]

    for title, desc in improvements:
        rows = [
            [Paragraph(title, FIXED_TITLE), Paragraph("")],
            [Paragraph(desc, BODY), Paragraph("")],
        ]
        t = Table(rows, colWidths=["82%", "18%"])
        t.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("SPAN", (0, 1), (1, 1)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#a3d9b8")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), C_BG_GREEN),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story += [t, Spacer(1, 3 * mm)]

    # ── Analysierte Kategorien ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("6. Geprüfte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def ok(text: str = "Kein Finding"):
        return Paragraph(
            text, s("OK", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN)
        )

    def fixed(text: str):
        return Paragraph(
            text, s("FX", fontName="Helvetica-Bold", fontSize=10, textColor=C_AMBER)
        )

    def info(text: str):
        return Paragraph(
            text, s("IN", fontName="Helvetica-Bold", fontSize=10, textColor=C_BLUE)
        )

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [
            Paragraph(
                "Direktiven-Injektion in privilegierte Konfig (/etc/sysctl.d/)", BODY
            ),
            fixed("F1 -> behoben (Allowlist+Wert-Check)"),
        ],
        [
            Paragraph("Destruktive Kommandos in Test-/CI-Infrastruktur", BODY),
            fixed("F2 -> behoben (Guard+Tests)"),
        ],
        [
            Paragraph(
                "Command-/Argument-Injection (ufw/nmcli/wg-quick, subprocess)", BODY
            ),
            ok("list-form; command-Feld mitbehoben"),
        ],
        [
            Paragraph(
                "Locale-unabhaengige UFW-/Lynis-Auswertung (Output-Parsing)", BODY
            ),
            ok("Kein Finding (Anzeige-Logik)"),
        ],
        [
            Paragraph(
                "Native Rechte-Checks (Home/kritische Dateien, Symlink/TOCTOU)", BODY
            ),
            ok("Kein Finding (lstat, kein Follow)"),
        ],
        [
            Paragraph("Root-Service (netmon_network_service, pkexec)", BODY),
            ok("Kein neuer Endpunkt, argv-validiert"),
        ],
        [
            Paragraph("Daten-Backup (Symlink-Escape, Rekursion, Pfadgrenzen)", BODY),
            ok("Kein Finding (kein Follow, $HOME)"),
        ],
        [
            Paragraph("Repository-Guard (Keyring-/URI-Parsing, Quick-Actions)", BODY),
            ok("Kein Finding (shlex.quote)"),
        ],
        [
            Paragraph(
                "Unsichere Deserialisierung (pickle, yaml.load, eval, shell=True)", BODY
            ),
            ok(),
        ],
        [
            Paragraph("Autorisierung / Kindersicherung", BODY),
            info("Bewusste Design-Entscheidung"),
        ],
        [Paragraph("Regression der Runde-7/8/9-Haertungen", BODY), ok("Alle intakt")],
        [
            Paragraph("Versionskonsistenz (App / deb / Changelog)", BODY),
            ok("Durchgaengig 1.1.20"),
        ],
    ]
    cat_table = Table(cat_rows, colWidths=["62%", "38%"])
    cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_BG_HEAD),
                ("BOX", (0, 0), (-1, -1), 0.5, C_LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story += [cat_table]

    # ── Impressum ─────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE),
        Spacer(1, 3 * mm),
        Paragraph(
            "Impressum und Haftungsausschluss",
            s(
                "H2",
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=20,
                textColor=colors.HexColor("#16263a"),
                spaceBefore=14,
                spaceAfter=6,
            ),
        ),
        Paragraph(
            "<b>Auditor:</b> Claude Fable 5 (Anthropic) — Analyse-Sub-Agent + dedizierter False-Positive-Validierungs-Sub-Agent (mit Repro)",
            BODY,
        ),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 19. Juli 2026", BODY),
        Paragraph(
            "<b>Codestand:</b> Arbeitsstand v1.1.20 (Diff seit dem Runde-9-Stand ac412cbc), einschliesslich der neuen Security-Baseline-/Sysctl-Apply-Stufe und des Baseline-Transferpakets — Runde 10",
            BODY,
        ),
        Paragraph(
            "<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation des kompletten Branch-Diffs + Konfidenz-gescorte FP-Validierung mit lauffaehigem Repro + Umsetzung von zwei Haertungen mit 15 Regressionstests + Regressions-Gegenpruefung der Vorrunden-Haertungen (Gesamtsuite 2133 bestanden, drei bekannte umgebungsbedingte Fehler ohne Sicherheitsbezug) — kein Laufzeit-Penetrationstest",
            BODY,
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "Dieses Audit ersetzt keinen professionellen Penetrationstest durch eine zertifizierte "
            "Sicherheitsfirma. Die Analyse beschraenkt sich auf den angegebenen Codestand. "
            "Nicht erfasst: Laufzeitverhalten, Systembibliotheken, Netzwerkkonfiguration.",
            MUTED,
        ),
    ]

    doc.build(story)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r10.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
