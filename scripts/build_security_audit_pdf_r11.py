#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.20 Runde 11."""

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
        title="NetMon Security Audit 2026 — v1.1.20 Runde 11",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.20 (Runde 11)",
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

    story = []

    # ── Titelseite ───────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20 * mm),
        Paragraph(
            "SICHERHEITS-AUDIT — RUNDE 11",
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
        ["Datum", "29. Juli 2026"],
        ["Analysierte Version", "v1.1.20"],
        [
            "Schwerpunkt",
            "UFW-sysctl-Override-Feature, neues Laufzeitmess-Modul, Radio-Refactoring, "
            "Ist-Stand-Pruefung der Radio-Senken",
        ],
        ["Kritische Findings", "0"],
        ["Hohe Findings", "0"],
        ["Mittlere Findings", "0"],
        ["Haertungen umgesetzt", "8 + 26 neue Regressionstests"],
        ["Gesamt-Testsuite", "2562 bestanden, 2 uebersprungen"],
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
                    "0 KRITISCHE — 0 HOHE — 0 MITTLERE FINDINGS "
                    "(8 HAERTUNGEN UMGESETZT)",
                    s(
                        "VT",
                        fontName="Helvetica-Bold",
                        fontSize=11.5,
                        leading=16,
                        textColor=C_GREEN,
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
                ("BACKGROUND", (0, 0), (-1, -1), C_BG_GREEN),
                ("BOX", (0, 0), (-1, -1), 1.5, C_GREEN),
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
            "Die elfte Sicherheitsanalyse pruefte den kompletten Diff seit dem "
            "Runde-10-Endstand (Commit 445279ac, 20. Juli 2026) bis zum aktuellen "
            "Arbeitsstand einschliesslich uncommitteter Aenderungen: 215 Commits "
            "und 468 Dateien, davon jedoch nur rund 3.750 Zeilen Produktivcode in "
            "22 Modulen — der Rest sind Tests und Refactoring-Dokumentation. "
            "Sicherheitsrelevant neu waren vor allem das noch unveroeffentlichte "
            "UFW-sysctl-Override-Feature, das /etc/ufw/sysctl.conf als root "
            "umschreibt, sowie ein neues Laufzeitmess-Modul und dessen Einbindung "
            "in den zentralen Kommandopfad.",
            BODY,
        ),
        Paragraph(
            "Diese Runde brachte kein Finding oberhalb der Melde-Schwelle von "
            "8/10. Drei Kandidaten wurden gemeldet, alle drei im neuen "
            "UFW-sysctl-Feature. Zwei davon gingen an unabhaengige "
            "Validierungs-Sub-Agenten mit dem ausdruecklichen Auftrag, sie zu "
            "widerlegen: einer wurde widerlegt (2/10), einer von MEDIUM auf LOW "
            "herabgestuft (6/10). Der dritte ist eine reine "
            "Defense-in-Depth-Inkonsistenz (3/10). Behoben wurden alle drei "
            "trotzdem.",
            BODY,
        ),
        Paragraph(
            "Bemerkenswert an dieser Runde ist eine strukturelle Erkenntnis: Der "
            "Radio-Diff-Agent stellte fest, dass die eigentlich scharfen "
            "Radio-Senken — mpv-/ffmpeg-Start, ICY-Metadaten, Aufnahme-Dateinamen, "
            "Playlist-Parsing — gar nicht in den geaenderten Dateien liegen, "
            "sondern in radio_controller.py und netmon_radio_core.py. Diese sind "
            "seit mehreren Runden unveraendert und fielen damit systematisch durch "
            "jeden diff-basierten Scope. Sie wurden in dieser Runde erstmals im "
            "Ist-Stand geprueft — mit vier weiteren Haertungen als Ergebnis. Fuer "
            "kommende Runden gilt daher: lange unveraenderte Senken periodisch im "
            "Ist-Stand pruefen, nicht nur den Diff.",
            BODY,
        ),
        Paragraph(
            "Insgesamt wurden acht Defense-in-Depth-Haertungen umgesetzt und mit "
            "26 neuen Regressionstests abgesichert. Die Gesamtsuite lief mit "
            "2562 bestandenen und 2 uebersprungenen Tests — keine Regression. "
            "Alle Haertungen der "
            "Runden 7 bis 10 wurden gegengeprueft und sind intakt. Die "
            "Kindersicherung bleibt als bewusste Design-Entscheidung dokumentiert; "
            "die postinst-DNS-Policy und die Nur-Hash-Schnellpruefung auf der "
            "Downloadseite bleiben als Runde-9-Hinweise offen.",
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
            "Bestimmung des Rundenscopes gegen den Runde-10-Endstand 445279ac, "
            "Trennung von Produktivcode, Tests und Dokumentation. "
            "Gegenpruefung der Vorrunden-Haertungen auf Regressionen: die "
            "xdg-open-Allowlist und der Update-URL-Host-Pin aus Runde 9, der "
            "killswitch-erhaltende Firewall-Recover aus Runde 9, die "
            "Sysctl-Allowlist und der suiteweite Reboot-Guard aus Runde 10 — alle "
            "intakt. Vor dem ersten Testlauf wurde bestaetigt, dass der "
            "Reboot-Guard aus Runde 10 aktiv ist (Betriebsregel seit dem "
            "Host-Neustart-Vorfall).",
            BODY,
        ),
        Paragraph("Phase 2 - Analyse-Sub-Agenten", H3),
        Paragraph(
            "Vier parallele Analyse-Sub-Agenten mit getrennten Scopes: (a) die "
            "sicherheitskritischen Feature-Controller inklusive des uncommitteten "
            "UFW-sysctl-Features, (b) Core-Module, Services und Skripte mit "
            "Schwerpunkt auf dem zentralen Kommandopfad, (c) der Radio-Diff und "
            "(d) — ausgeloest durch einen Abdeckungshinweis aus (c) — die "
            "Radio-Senken im Ist-Stand. Der Radio-Diff wurde nicht zeilenweise "
            "gesichtet, sondern ueber einen normalisierten Inhaltsdiff (beide "
            "Fassungen whitespace-normalisiert, sortiert, verglichen) als reines "
            "Refactoring belegt.",
            BODY,
        ),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Je ein unabhaengiger Validierungs-Sub-Agent pro belastbarem Kandidat, "
            "mit dem ausdruecklichen Auftrag, den Kandidaten zu widerlegen statt "
            "ihn zu bestaetigen. Beide arbeiteten empirisch: einer extrahierte das "
            "Original-Paket ufw_0.36.2-6_all.deb, um den behaupteten "
            "Auslieferungsinhalt zu pruefen, der andere testete das "
            "sysctl-Fehlerverhalten an temporaeren Kopien (procps-ng 4.0.4) und "
            "schrieb einen Proof-of-Concept. Ergebnis: 2/10 (widerlegt) und 6/10 "
            "(von MEDIUM auf LOW herabgestuft). In beiden Faellen erwiesen sich "
            "zentrale Teilbehauptungen der Melder als falsch — dokumentiert in "
            "Abschnitt 3.",
            BODY,
        ),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "Acht Defense-in-Depth-Haertungen umgesetzt und mit 26 neuen "
            "Regressionstests abgesichert. Jede Haertung wurde vor der Umsetzung am "
            "echten Code gegengeprueft, nicht auf Zuruf des meldenden Agenten "
            "uebernommen. Gesamtsuite danach: 2562 bestanden, 2 uebersprungen.",
            BODY,
        ),
    ]

    # ── Kandidaten ────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Kandidaten & Validierung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Kein Kandidat erreichte die Melde-Schwelle von 8/10; es gibt in dieser "
            "Runde also keine bestaetigten Findings. Der Vollstaendigkeit halber "
            "ist dokumentiert, was gemeldet, wie es gegengeprueft und wie es "
            "eingestuft wurde — einschliesslich der Teilbehauptungen, die sich als "
            "falsch erwiesen.",
            BODY,
        ),
    ]

    candidates = [
        (
            "K1 — stderr-Kontamination beim Read-Modify-Write von "
            "/etc/ufw/sysctl.conf  [LOW, Konfidenz 6/10, gehaertet]",
            "netmon/features/security_audit_controller.py — "
            "_apply_ufw_sysctl_overrides() / _read_existing_sysctl_dropin().",
            "Das neue Feature liest /etc/ufw/sysctl.conf per 'sudo -n cat' ueber "
            "run_cmd, veraendert den Inhalt und schreibt ihn als root zurueck. "
            "run_cmd fuehrt jedoch stderr mit stdout zusammen: eine sudo-Warnung "
            "wie 'unable to resolve host ...' erscheint mit Exit-Code 0 im "
            "vermeintlichen Dateiinhalt, passiert die Filter unveraendert und "
            "landet als Muellzeile in einer Root-Konfigdatei. WIDERLEGT wurde die "
            "behauptete Auswirkung: Der Melder gab an, die Haertungswerte koennten "
            "dadurch beim Boot ausfallen. Empirisch geprueft (procps-ng 4.0.4, "
            "temporaere Kopien) warnt sysctl bei einer Syntax-Muellzeile, "
            "verarbeitet die Folgezeilen aber weiter und liefert rc=0; ufw-init "
            "ignoriert Fehler ohnehin per '|| true'. Kein Haertungsverlust. "
            "Uebersehen hatte der Melder ausserdem, dass ein Zurueckschreiben nur "
            "bei tatsaechlicher Aenderung stattfindet, und dass dasselbe Muster "
            "bereits committed existiert — neu eingefuehrt wurde es also nicht. "
            "Der Inhalt der sudo-Warnungen ist zudem nicht angreiferkontrolliert "
            "(Hostname, PAM, Audit); es gibt keinen Injektionsvektor.",
            "Unterhalb der Melde-Schwelle, daher kein Finding. Trotzdem "
            "gehaertet: ein neues Plausibilitaetsgate "
            "(_implausible_sysctl_config_line) bricht den Lauf mit klarer Meldung "
            "ab, sobald der gelesene Inhalt eine Zeile enthaelt, die weder leer "
            "noch Kommentar noch 'key = value' ist — an beiden Lesestellen, also "
            "auch am bereits bestehenden Drop-in-Pfad. Bewusst Abbruch statt "
            "stillem Verwerfen: eine unerwartete Zeile in einer Root-Konfigdatei "
            "darf nicht kommentarlos geloescht werden.",
        ),
        (
            "K2 — Neue Schreibsenke ohne die Allowlist ihrer Schwester-Senke  "
            "[LOW, Konfidenz 3/10, gehaertet]",
            "netmon/features/security_audit_controller.py — "
            "_build_ufw_sysctl_override_content().",
            "Die in Runde 10 eingezogene Schluessel-Allowlist sitzt bewusst direkt "
            "an der Schreibsenke (_render_sysctl_dropin_content) — als zweite "
            "Verteidigungslinie fuer den Fall, dass ein Spec auf anderem Weg als "
            "ueber die Transfer-Import-Validierung hereinkommt. Die neue Senke "
            "schreibt nach /etc/ufw/sysctl.conf, eine Datei, die laut eigenem "
            "Header /etc/sysctl.conf und /etc/sysctl.d ueberschreibt — sie wirkt "
            "also eher staerker als die Drop-in-Datei, trug aber keine dieser "
            "Pruefungen. Heute nicht ausnutzbar: der einzige Aufrufer uebergibt "
            "eine Modulkonstante, und es existiert kein Datenfluss von "
            "Transferpaket, Remote-JSON oder Dateinamen zu dieser Senke; das wurde "
            "explizit nachverfolgt. Gemeldet als Defense-in-Depth-Regression gegen "
            "eine dokumentierte Schutzentscheidung, nicht als Exploit.",
            "Gehaertet: Die neue Senke prueft jetzt dieselbe "
            "SECURITY_BASELINE_ALLOWED_SYSCTL_KEYS-Allowlist und dieselbe "
            "Wert-Validierung wie ihre Schwester-Senke. Ein Eintrag wie "
            "'kernel.core_pattern = |/tmp/payload' oder ein Wert mit eingebettetem "
            "Zeilenumbruch wird verworfen, statt als root persistiert zu werden.",
        ),
        (
            "K3 — 'Sysctl-Re-Apply dreht Kernelhaertung still zurueck'  "
            "[WIDERLEGT, Konfidenz 2/10]",
            "netmon/features/security_audit_controller.py — "
            "_apply_ufw_sysctl_overrides() / apply_security_baseline_profile().",
            "Gemeldet wurde, das unbedingte Neuladen von /etc/ufw/sysctl.conf am "
            "Ende des UFW-Schritts koenne NetMons eigene Kernelhaertung "
            "ueberschreiben — konkret rp_filter. Widerlegt an drei Stellen. "
            "Erstens empirisch: der Validierer extrahierte das Original-Paket "
            "ufw_0.36.2-6_all.deb und wies nach, dass /etc/ufw/sysctl.conf "
            "ueberhaupt kein rp_filter enthaelt — weder gesetzt noch "
            "auskommentiert. Die tragende Praemisse war falsch. Zweitens: die "
            "einzige reale Ueberschneidung mit der NetMon-Baseline ist "
            "log_martians — und genau dafuer existiert der beanstandete Code. Die "
            "Paketdatei liefert log_martians=0 gegen NetMons Soll 1; das neue "
            "Override korrigiert das, bevor neu geladen wird. Der Melder hatte die "
            "Gegenmassnahme als Bug gemeldet. Drittens: eine nachgelagerte "
            "Wert-Verifikation existiert sehr wohl — nach allen Schritten laeuft "
            "ein erneuter Baseline-Check, der die Live-Kernelwerte liest. Eine "
            "stille Rueckdrehung ist strukturell ausgeschlossen. Hinzu kommt ein "
            "Denkfehler in der Richtung der Abweichung: rp_filter=1 (strict) ist "
            "strenger als NetMons bewusstes 2 (loose). Selbst im hypothetischen "
            "Fall wuerde die Sicherheit steigen und allein NetMons Funktionsabsicht "
            "(VPN, Multi-Interface) leiden — und das waere in der UI als 'Bewusste "
            "Abweichung' sichtbar, nicht still.",
            "Kein Sicherheits-Finding, keine Codeaenderung noetig. Das Entfernen "
            "der beanstandeten Zeile wuerde im Gegenteil die "
            "log_martians-Gegenmassnahme wirkungslos machen.",
        ),
    ]

    for title, loc, detail, fix in candidates:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [
                Paragraph(
                    "<b>Bewertung:</b> " + fix,
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
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9c48a")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
                    ("BACKGROUND", (0, 0), (-1, 0), C_BG_AMBER),
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
            "Scope-Luecke geschlossen — die Radio-Senken lagen nie in einem Diff",
            "Der Radio-Diff-Agent stellte fest, dass die sicherheitsrelevanten "
            "Radio-Pfade (mpv-/ffmpeg-Start, ICY-Metadaten, Aufnahme-Dateinamen, "
            "Playlist-Parsing) nicht in den geaenderten Dateien liegen, sondern in "
            "radio_controller.py und netmon_radio_core.py. Beide sind seit Runden "
            "unveraendert und fielen damit systematisch durch jeden diff-basierten "
            "Scope. Sie wurden in dieser Runde erstmals im Ist-Stand geprueft — mit "
            "vier Haertungen als Ergebnis. Konsequenz fuer kommende Runden: lange "
            "unveraenderte Senken periodisch im Ist-Stand pruefen.",
        ),
        (
            "Aufnahme-Dateinamen aus ICY-Metadaten — sauber",
            "Der naheliegendste Verdacht im Radio-Modul bestaetigte sich nicht: "
            "Stationsname und ICY-Titel laufen beide durch eine Slug-Funktion, die "
            "alles ausser Kleinbuchstaben und Ziffern ersetzt. Pfad-Traversal, "
            "Newlines, Null-Bytes, Shell-Metazeichen und fuehrende Bindestriche "
            "sind damit konstruktiv ausgeschlossen. Ebenso sauber: die "
            "Stream-URL-Schema-Allowlist wird auf allen Lade- und Speicherpfaden "
            "erzwungen, der EQ-Filter ist auf ganzzahlige Werte geklemmt, und der "
            "projectM-ZIP-Import ist gegen Zip-Slip abgesichert.",
        ),
        (
            "3.000 Zeilen Radio-Refactoring — ohne Verhaltensaenderung belegt",
            "Statt den grossen Refactoring-Diff zeilenweise zu sichten, wurde ein "
            "normalisierter Inhaltsdiff gefahren. Ergebnis: die entfernten Zeilen "
            "sind ausnahmslos State-Initialisierungen und Geometrie-Ausdruecke, die "
            "1:1 in neue Hilfsfunktionen gewandert sind. Die Whitelist beim Laden "
            "der Sprachdatei — ohne die ein Pfad-Traversal ueber die Konfigdatei "
            "moeglich waere — hat das Refactoring nachweislich ueberlebt.",
        ),
        (
            "Core und Services — keine Detektionsluecke durch die Refactorings",
            "Der zentrale Kommandopfad core/command.py hat als einzige Aenderung "
            "einen Mess-Wrapper erhalten; Argumentaufbau, Timeouts und "
            "Env-Handling sind byte-identisch, und der Reboot-Guard aus Runde 10 "
            "wird nicht umgangen. Im Repository-Guard wurden alle Detektionszweige "
            "gegen die Vorversion abgeglichen und sind vollstaendig erhalten — kein "
            "untrusted Repository und kein Schluessel kann durch den Refactor "
            "unbemerkt durchrutschen. Das Support-Bundle leakt keine Keys, "
            "VPN-Configs oder PSKs.",
        ),
        (
            "UFW-Konflikthinweis im rp_filter-Zweig — geprueft, vorhanden",
            "Bei der Widerlegung von K3 wurde zusaetzlich behauptet, den "
            "erklaerenden Hinweis '/etc/ufw/sysctl.conf setzt denselben Wert "
            "anders' erzeuge nur der sysctl-Zweig der Baseline-Auswertung, nicht "
            "der rp_filter-Zweig — eine Diagnose-Luecke also. Auch das hat der "
            "Nachtest widerlegt. Der rp_filter-Zweig ruft nicht den "
            "Low-Level-Helfer _sysctl_ufw_override_value() auf, nach dem gesucht "
            "wurde, sondern den Wrapper _sysctl_ufw_override_hint(), und haengt "
            "dessen Ergebnis an die Begruendung an; beide rp_filter-Specs tragen "
            "das dazu noetige config_source. End-to-End nachgestellt (Drop-in "
            "setzt 2, ufw-Datei setzt 1, Kernel meldet 1) liefert die Auswertung "
            "Status 'Bewusste Abweichung' samt ufw-Hinweis. Keine Luecke, kein "
            "Handlungsbedarf.",
        ),
        (
            "Kindersicherung — weiterhin bewusste Design-Entscheidung",
            "Die PBKDF2-gestuetzte Kindersicherung im Secure-Browser bleibt wie in "
            "Runde 8 dokumentiert: Alltagshuerde gegen Gelegenheitszugriff im "
            "selben Konto, keine harte Grenze gegen technisch versierte Nutzer mit "
            "Kontozugriff (No-Root-Design). Keine Codeaenderung, unveraendert "
            "gueltig.",
        ),
        (
            "postinst-DNS & Nur-Hash-Schnellpruefung — Policy-Hinweise weiter offen",
            "Die beiden Policy-Hinweise aus Runde 9 bleiben unveraendert bestehen: "
            "das root-postinst biegt aktive NM-DNS bei der Installation auf "
            "8.8.8.8 (Opt-in empfohlen), und die Schnellpruefung auf der "
            "Downloadseite empfiehlt nur sha256sum -c statt der "
            "minisign-Vollpruefung. Kein ausnutzbarer Befund — als "
            "Design-Entscheidungen des Projektverantwortlichen offen.",
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
        PageBreak(),
        Paragraph("5. Umgesetzte Haertungen (Runde 11)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Acht Haertungen, keine davon durch ein bestaetigtes Finding "
            "erzwungen — alle als Defense in Depth umgesetzt, jede mit "
            "Regressionstests abgesichert.",
            BODY,
        ),
    ]

    improvements = [
        (
            "Allowlist an der UFW-sysctl-Schreibsenke — security_audit_controller.py",
            "_build_ufw_sysctl_override_content() prueft Schluessel und Werte jetzt "
            "gegen dieselbe Allowlist und dieselben Format-Regeln wie die "
            "Drop-in-Senke. Unerlaubte Schluessel und Werte mit Zeilenumbruechen "
            "oder Shell-Metazeichen werden verworfen.",
        ),
        (
            "Plausibilitaetsgate gegen stderr-Kontamination — security_audit_controller.py",
            "_implausible_sysctl_config_line() bricht jeden Read-Modify-Write ab, "
            "dessen gelesener Inhalt eine Zeile enthaelt, die weder leer noch "
            "Kommentar noch 'key = value' ist — an beiden Lesestellen. Verhindert, "
            "dass eine sudo-Warnung mit Exit-Code 0 als root in eine "
            "Root-Konfigdatei zurueckgeschrieben wird.",
        ),
        (
            "'--'-Optionsterminator vor dem mpv-Medienargument — radio_controller.py",
            "mpv wertet Optionen an jeder Position aus. Ein Playlist-Eintrag namens "
            "'--script=payload.lua' waere als Option geladen worden statt als "
            "Dateiname. Das Medienargument steht jetzt hinter einem '--'; der "
            "EQ-Filter wird korrekt davor einsortiert.",
        ),
        (
            "Handover-Payload durchlaeuft die URL-Allowlist — radio_controller.py",
            "Die einzige Stelle im Modul, an der ein Stations-Datensatz ohne "
            "normalize_station_entry() in den App-Zustand gelangte — und damit die "
            "Stream-URL-Schema-Allowlist umging, die ueberall sonst erzwungen wird. "
            "Ein file://-Eintrag im Uebergabe-Payload wird jetzt verworfen.",
        ),
        (
            "mpv-IPC-Socket in ein privates Verzeichnis — radio_controller.py",
            "Wer auf diesen Socket schreiben darf, darf mpv steuern — und mpv kennt "
            "ein 'run'-Kommando. Der Socket lag bisher direkt im "
            "State-Verzeichnis (typisch 0755). Er liegt jetzt in XDG_RUNTIME_DIR, "
            "ersatzweise in einem eigens angelegten 0700-Unterverzeichnis.",
        ),
        (
            "ffmpeg-Protokoll-Allowlist ohne 'file' — radio_controller.py",
            "Die Aufnahme erhaelt jetzt ein explizites "
            "'-protocol_whitelist http,https,tcp,tls,crypto'. Ohne diese Grenze "
            "waehlt ffmpeg den Demuxer nach Inhalt — eine als Stream ausgelieferte "
            "HLS-/concat-Playlist konnte damit lokale Dateien in die Aufnahme "
            "ziehen.",
        ),
        (
            "Wert-seitige Redaction im Messlog — core/performance_monitor.py",
            "Die Redaction pruefte bisher nur den Metadaten-Schluessel; ein Secret "
            "unter einem harmlosen Schluessel waere im Klartext im Log gelandet. "
            "Werte laufen jetzt zusaetzlich durch dieselbe Redaction wie die "
            "Diagnosedaten — rekursiv auch in Listen und verschachtelten Dicts, "
            "ebenso der Fehlertext. Kein damaliger Aufrufer war betroffen; die "
            "Haertung schliesst die Falle fuer kuenftige.",
        ),
        (
            "Symlink-sicherer, nutzerprivater Messlog — core/performance_monitor.py",
            "Der Log wird jetzt mit O_NOFOLLOW | O_APPEND und Modus 0600 geoeffnet, "
            "die Rotation ruehrt symlink-verlinkte Pfade nicht an. Ein "
            "untergeschobener Symlink kann die Messwerte damit weder umlenken noch "
            "eine fremde Datei ueberschreiben.",
        ),
        (
            "26 neue Regressionstests",
            "Elf in test_netmon_lynis_output.py (Allowlist an der UFW-Senke, "
            "Erkennung von stderr-Zeilen, Abbruch statt Zurueckschreiben, "
            "ufw-Konflikthinweis im rp_filter-Zweig), neun in "
            "test_netmon_radio_module.py (Optionsterminator, EQ-Reihenfolge, "
            "Protokoll-Allowlist, Socket-Rechte inklusive Fehlerfallback, "
            "Handover-Normalisierung) und "
            "sechs in test_performance_monitor.py (Wert-Redaction verschachtelt, "
            "Symlink-Verweigerung, Dateirechte). Gesamtsuite danach: "
            "2562 bestanden, 2 uebersprungen.",
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
            Paragraph("Schreiben in root-eigene Konfig (/etc/ufw/sysctl.conf)", BODY),
            fixed("Allowlist + Plausibilitaetsgate ergaenzt"),
        ],
        [
            Paragraph(
                "Argument-/Options-Injektion in externe Player (mpv, ffmpeg)", BODY
            ),
            fixed("'--' + Protokoll-Allowlist ergaenzt"),
        ],
        [
            Paragraph("Fremddaten in Dateinamen (ICY-Metadaten, Stationsnamen)", BODY),
            ok("Kein Finding (Slug-Normalisierung)"),
        ],
        [
            Paragraph("URL-Schema-Allowlists (Streams, Logos, Homepages)", BODY),
            fixed("Handover-Luecke geschlossen"),
        ],
        [
            Paragraph("Zentraler Kommandopfad (core/command.py)", BODY),
            ok("Kein Finding (nur Mess-Wrapper)"),
        ],
        [
            Paragraph("Secret-Leaks in Logs, Support-Bundle und Diagnose", BODY),
            fixed("Wert-Redaction ergaenzt"),
        ],
        [
            Paragraph("Dateirechte, Symlink / TOCTOU an neuen Schreibpfaden", BODY),
            fixed("O_NOFOLLOW + 0600 + 0700-Socketdir"),
        ],
        [
            Paragraph("Repository-Guard, DNS-Service, Prozess-Guard", BODY),
            ok("Detektionszweige vollstaendig erhalten"),
        ],
        [
            Paragraph("Unsichere Deserialisierung (pickle, eval, shell=True)", BODY),
            ok(),
        ],
        [
            Paragraph("TLS-Verifikation und Redirect-Handling", BODY),
            ok("Keine Abschaltung, kein http->file"),
        ],
        [
            Paragraph("Autorisierung / Kindersicherung", BODY),
            info("Bewusste Design-Entscheidung"),
        ],
        [Paragraph("Regression der Runde-9/10-Haertungen", BODY), ok("Alle intakt")],
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
            "Auditor & Methode",
            s(
                "IMP",
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=20,
                textColor=colors.HexColor("#16263a"),
                spaceBefore=14,
                spaceAfter=6,
            ),
        ),
        Paragraph(
            "<b>Auditor:</b> Claude Fable 5 (Anthropic) — vier Analyse-Sub-Agenten "
            "+ zwei unabhaengige False-Positive-Validierungs-Sub-Agenten",
            BODY,
        ),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 29. Juli 2026", BODY),
        Paragraph(
            "<b>Codestand:</b> Arbeitsstand v1.1.20 (Diff seit dem "
            "Runde-10-Endstand 445279ac, einschliesslich uncommitteter "
            "Aenderungen), ergaenzt um eine Ist-Stand-Pruefung der Radio-Senken — "
            "Runde 11",
            BODY,
        ),
        Paragraph(
            "<b>Methode:</b> Statische Code-Analyse + manuelle "
            "Datenfluss-Verifikation + normalisierter Inhaltsdiff fuer die "
            "Refactoring-Masse + konfidenz-gescorte FP-Validierung mit empirischer "
            "Gegenpruefung (Paketextraktion, sysctl-Verhaltenstests) + Umsetzung "
            "von acht Haertungen mit 26 Regressionstests + "
            "Regressions-Gegenpruefung der Vorrunden-Haertungen (Gesamtsuite 2562 "
            "bestanden, 2 uebersprungen) — kein Laufzeit-Penetrationstest",
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r11.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
