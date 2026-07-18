#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.18 Runde 8."""

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
        title="NetMon Security Audit 2026 — v1.1.18 Runde 8",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.18 (Runde 8)",
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
        Paragraph("SICHERHEITS-AUDIT — RUNDE 8", s(
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
        ["Datum", "18. Juli 2026"],
        ["Analysierte Version", "v1.1.18 — Runde 8"],
        ["Schwerpunkt", "Secure Browser inkl. Kindersicherung, Linux-Hilfe, Site-PHP"],
        ["Bewertete Kandidaten", "2 (beide Konfidenz 1/10)"],
        ["Ausnutzbare Findings", "0"],
        ["Haertungen umgesetzt", "1 (Defense-in-Depth)"],
        ["Dokumentierte Design-Entscheidungen", "1 (Kindersicherung)"],
        ["Konfidenz-Schwelle", ">= 8 / 10"],
        ["Regressionstests", "173 + 80 + 121 Tests, sicherheitsrelevante alle gruen"],
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
            "0 AUSNUTZBARE FINDINGS — 1 HAERTUNG UMGESETZT — KINDERSICHERUNG ALS "
            "BEWUSSTE DESIGN-ENTSCHEIDUNG DOKUMENTIERT", s(
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
            "Die achte Sicherheitsanalyse nahm die in Runde 7 nicht fokussierte "
            "bzw. neu hinzugekommene Angriffsflaeche vollstaendig in den Blick: "
            "das Secure-Browser-Subsystem (manager.py, service.py, ui.py, "
            "browser_container_builder.py) inklusive der neuen Kindersicherung, "
            "die fuenf neuen Linux-Hilfe-Services (linux_help_*_service.py), die "
            "Controller fuer Radio, Speedtest, VPN und Paketmitschnitt sowie die "
            "serverseitigen Website-Endpunkte (download.php, download-stats.php).",
            BODY),
        Paragraph(
            "Ein Analyse-Sub-Agent identifizierte zwei Kandidaten; beide wurden "
            "von eigenen Validierungs-Sub-Agenten geprueft und erhielten "
            "Konfidenz 1/10 — weit unterhalb der Melde-Schwelle von 8/10. Es "
            "wurden keine ausnutzbaren Schwachstellen bestaetigt.",
            BODY),
        Paragraph(
            "K1 (Kindersicherung, bewusste Design-Entscheidung): Das Passwort-Gate "
            "vor dem Browserstart ist kryptographisch sauber umgesetzt "
            "(PBKDF2-SHA256, 200.000 Iterationen, zufaelliges 16-Byte-Salt, "
            "konstantzeitiger Vergleich via hmac.compare_digest, maximal drei "
            "Versuche, fail-closed, Lock-Datei mit Rechten 0600). Dass ein "
            "technisch versierter Nutzer im selben Linux-Konto das Gate umgehen "
            "kann (Direktstart der Firefox-Binary, Loeschen der nutzereigenen "
            "child-lock.json), ist eine inhaerente Eigenschaft jeder "
            "Same-Account-Kindersicherung und kein Implementierungsfehler: Es "
            "existiert keine vom Betriebssystem durchsetzbare Vertrauensgrenze "
            "innerhalb derselben UID. Die Kindersicherung ist bewusst als "
            "Alltagshuerde gegen Gelegenheitszugriff konzipiert, nicht als harte "
            "Sicherheitsgrenze; fuer harte Durchsetzung sind getrennte "
            "Betriebssystem-Konten das empfohlene Setup. Diese Einordnung wird "
            "mit dieser Runde ausdruecklich als bewusste Design-Entscheidung "
            "dokumentiert — es erfolgt keine Codeaenderung.",
            BODY),
        Paragraph(
            "K2 (Favicon-/Logo-Download, False Positive + Konsistenz-Haertung): "
            "Der Favicon-Download des Container-Builders erzwingt vor jedem "
            "urlopen eine http/https-Allowlist und speichert die Bytes nur unter "
            "festem Namen mit Magic-Byte-Endungserkennung — der befuerchtete "
            "file://-Lesezugriff ueber boesartige Website-HTML ist nicht moeglich. "
            "Einziger Nebenbefund: Der Radio-Logo-Download "
            "(_download_station_logo) uebergab Favicon-URLs aus der "
            "radio-browser.info-API als einziger Fetcher ohne Schema-Pruefung an "
            "urlopen (nicht ausnutzbar: fester SHA-256-Zielpfad im eigenen Cache, "
            "PIL-Re-Encoding, kein Rueckkanal). Als Defense-in-Depth wurde "
            "dieselbe http/https-Allowlist in _station_logo_url() nachgezogen "
            "und mit einem Regressionstest abgesichert.",
            BODY),
        Paragraph(
            "Die Runde-7-Haertungen (konservatives propupd-Gate, "
            "ClamAV-Datenbankverzeichnis-Pruefung, rkhunter-Pfad-Allowlist, "
            "list-form Scan-Worker-Kommandos) wurden gegengeprueft und sind alle "
            "unveraendert intakt. Sicherheitsrelevante Testsuiten: "
            "Secure-Browser-Modul & Container-Builder (173 Tests), "
            "RKHunter/ClamAV/Linux-Hilfe (80 Tests), Radio-Modul (121 Tests) — "
            "alle sicherheitsrelevanten Tests gruen. (Zwei vorbestehende, "
            "umgebungsabhaengige Desktop-Launch-Tests der Radio-Suite schlagen "
            "auf dem Audit-Host unabhaengig vom Codestand fehl; kein "
            "Sicherheitsbezug.)",
            BODY),
    ]

    # ── Methodik ──────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Diff- & Reconnaissance", H3),
        Paragraph(
            "Vollstaendiger Branch-Diff (feature/secure-browser-manager, 3,7 MB, "
            "Codestand c2087b63 plus Arbeitsstand) plus Sichtung der neuen "
            "unversionierten Services. Abgleich mit den etablierten "
            "Sicherheitsmustern des Projekts (run_cmd in Listenform, "
            "_normalize_allowed_path, _safe_makedirs_no_symlink).",
            BODY),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Ein dedizierter Analyse-Sub-Agent verfolgte Datenflussketten von "
            "Fremdeingaben (besuchte Websites, API-Antworten von "
            "radio-browser.info, Datei- und Containernamen) bis zu sensiblen "
            "Operationen (subprocess, urlopen, Dateisystem-Schreibpfade, "
            ".desktop-Generierung). 2 Kandidaten identifiziert.",
            BODY),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Fuer jeden Kandidaten lief ein eigener Validierungs-Sub-Agent mit "
            "striktem FP-Filter-Regelwerk und Konfidenz-Scoring. Ergebnis: "
            "Kindersicherung = By-Design-Limitierung (1/10), Favicon-/Logo-Fetch "
            "= False Positive (1/10).",
            BODY),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "Die aus K2 abgeleitete Konsistenz-Haertung (http/https-Allowlist im "
            "Radio-Logo-Download) wurde umgesetzt und mit einem neuen "
            "Regressionstest abgesichert. Zusaetzlich Regressions-Gegenpruefung "
            "aller Runde-7-Haertungen am aktuellen Codestand.",
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
            "K1 — Kindersicherung: Same-User-Umgehbarkeit  "
            "[Konfidenz 1/10 — bewusste Design-Entscheidung]",
            "netmon/modules/secure_browser/manager.py — create_child_lock_payload(); "
            "tools/secure_browser_manager/browser_container_builder.py — "
            "start.sh-Gate + build_browser_lock_helper(); "
            "netmon/modules/secure_browser/ui.py — Tab-Integration.",
            "Die Kindersicherung im Secure-Browser-Tab schuetzt den Start eines "
            "Browser-Containers mit einem Passwort. Die Umsetzung ist "
            "kryptographisch korrekt: PBKDF2-SHA256 mit 200.000 Iterationen und "
            "zufaelligem 16-Byte-Salt, Ablage als Hash in child-lock.json (0600), "
            "Pruefung vor jedem Start ueber browser_lock.py mit konstantzeitigem "
            "Vergleich (hmac.compare_digest), maximal drei Versuchen und "
            "Fail-Closed-Verhalten (|| exit 1; fehlende/defekte Lock-Datei "
            "blockiert den Start). Geprueft wurde, ob die Umgehbarkeit im selben "
            "Linux-Konto (Direktstart ./firefox/firefox --no-remote --profile "
            "./profile, Loeschen der child-lock.json, Editieren von start.sh) "
            "eine Schwachstelle darstellt. Bewertung: Nein — Angreifer und Opfer "
            "teilen dieselbe UID, es existiert keine vom Betriebssystem "
            "durchsetzbare Vertrauensgrenze. Das ist eine inhaerente "
            "Kategorie-Eigenschaft jeder Same-Account-Kindersicherung, kein "
            "Implementierungsfehler; jede Haertung innerhalb desselben Kontos "
            "waere Sicherheitstheater, und Root-basierte Durchsetzung "
            "widerspraeche dem bewussten No-Root-Design des Moduls.",
            "BEWUSSTE DESIGN-ENTSCHEIDUNG (dokumentiert, keine Aenderung): Die "
            "Kindersicherung ist als Alltagshuerde gegen Gelegenheitszugriff im "
            "selben Konto konzipiert (z. B. Kinder am Familienrechner) und "
            "bewusst nicht als harte Sicherheitsgrenze gegen technisch versierte "
            "Nutzer mit Kontozugriff. Die UI macht keine weitergehenden "
            "Schutzversprechen. Fuer harte Durchsetzung sind getrennte "
            "Linux-Benutzerkonten das empfohlene Setup.",
        ),
        (
            "K2 — Favicon-/Logo-Download: file://-Lesezugriff & SSRF  "
            "[Konfidenz 1/10 — False Positive, Konsistenz gehaertet]",
            "tools/secure_browser_manager/browser_container_builder.py — "
            "fetch_url() / resolve_favicon_download(); "
            "netmon/netmon_radio_app.py — _download_station_logo() / "
            "_station_logo_url().",
            "Beim Anlegen eines Browser-Containers laedt NetMon das Favicon der "
            "eingetragenen Startseite; die Icon-URL stammt aus dem HTML der "
            "fremden Website (&lt;link rel=icon&gt;, via urljoin aufgeloest). Eine "
            "boesartige Website koennte href=file:///etc/passwd liefern. "
            "Bewertung: fetch_url() erzwingt vor jedem urlopen eine "
            "http/https-Allowlist (mit Kommentar, der genau dieses Szenario "
            "benennt) und deckt alle Aufrufer ab; die Bytes werden nur unter "
            "festem Namen (favicon.png/.ico/.svg, Endung per "
            "Magic-Byte-Erkennung) im Container-Verzeichnis gespeichert — kein "
            "Pfadeinfluss aus Fremddaten, http(s)->file-Redirects verhindert "
            "urllib selbst. Nebenbefund: Der Radio-Logo-Download uebergab "
            "Favicon-URLs aus der radio-browser.info-API als einziger Fetcher "
            "ohne Schema-Pruefung an urlopen — nicht ausnutzbar (fester "
            "SHA-256-Zielpfad im eigenen Cache, PIL-Re-Encoding nach PNG, kein "
            "Rueckkanal zum Angreifer), aber inkonsistent zum Builder-Standard.",
            "Gehaertet & verifiziert: _station_logo_url() begrenzt Logo-URLs "
            "jetzt wie fetch_url() auf http/https; file://, ftp://, data:, "
            "javascript: und schemalose URLs werden verworfen, bevor ein "
            "Download-Thread startet. Mit neuem Regressionstest "
            "(test_station_logo_url_allows_only_web_schemes) abgesichert.",
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

    # ── Kindersicherung als Design-Entscheidung ───────────────────────────────
    story += [
        Paragraph("4. Bewusste Design-Entscheidung: Kindersicherung", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph(
            "Die Kindersicherung im Secure-Browser-Tab wird mit dieser Runde "
            "formal als bewusste Design-Entscheidung festgehalten:",
            BODY),
        Paragraph(
            "Schutzziel: Alltagshuerde gegen Gelegenheitszugriff im selben "
            "Benutzerkonto (z. B. Kinder am Familienrechner). Das Passwort-Gate "
            "laeuft vor jedem Containerstart, ist fail-closed und "
            "kryptographisch sauber (PBKDF2-SHA256, 200.000 Iterationen, "
            "Zufalls-Salt, konstantzeitiger Vergleich).",
            BODY),
        Paragraph(
            "Nicht-Ziel: Schutz gegen technisch versierte Nutzer mit Zugriff auf "
            "dasselbe Linux-Konto. Innerhalb derselben UID existiert keine vom "
            "Betriebssystem durchsetzbare Vertrauensgrenze — wer das Konto "
            "bedienen darf, besitzt Firefox-Kopie, Profil und Lock-Datei und "
            "koennte auch jeden anderen Browser starten. Zusaetzliche "
            "Same-UID-Massnahmen waeren Sicherheitstheater; Root-basierte "
            "Durchsetzung widerspraeche dem No-Root-Design des Moduls.",
            BODY),
        Paragraph(
            "Empfehlung fuer harte Durchsetzung: getrennte "
            "Linux-Benutzerkonten fuer Kinder, ergaenzt um die Kindersicherung "
            "als zweite, komfortable Huerde innerhalb des Familienkontos.",
            BODY),
    ]

    # ── Umgesetzte Haertungen ─────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("5. Umgesetzte Defense-in-Depth-Haertung (Runde 8)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("http/https-Allowlist fuer Radio-Logo-Downloads — netmon_radio_app.py",
         "_station_logo_url() akzeptiert nur noch http-/https-URLs aus der "
         "radio-browser.info-API — dieselbe Regel, die fetch_url() im "
         "Container-Builder bereits erzwingt. Nicht-Web-Schemata (file://, "
         "ftp://, data:, javascript:, schemalose URLs) erreichen urlopen damit "
         "in keinem Codepfad des Projekts mehr; die Pruefung greift, bevor ein "
         "Download-Thread startet."),
        ("Neuer Regressionstest — Radio-Suite",
         "test_station_logo_url_allows_only_web_schemes stellt das "
         "Allowlist-Verhalten dauerhaft sicher. Sicherheitsrelevante Suiten "
         "nach der Haertung: Secure-Browser-Modul & Container-Builder (173), "
         "RKHunter/ClamAV/Linux-Hilfe (80), Radio-Modul (121) — alle "
         "sicherheitsrelevanten Tests gruen."),
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
        Spacer(1, 4 * mm),
        Paragraph("6. Geprüfte Sicherheitskategorien", H1),
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
        [Paragraph("Command Injection (subprocess, shell=True)", BODY),
         ok("Kein Finding (durchgaengig list-form)")],
        [Paragraph("Pfad-Traversal (Containernamen, Icon-/Logo-Pfade, "
                   "Hilfe-Dokumente)", BODY),
         ok("Kein Finding (Regex-Validierung)")],
        [Paragraph("Lokaler Dateizugriff / SSRF ueber Fremd-URLs (file://)", BODY),
         ok("K2 -> gehaertet (Allowlist)")],
        [Paragraph("Autorisierung / Zugriffskontrolle (Kindersicherung)", BODY),
         info("K1 -> bewusste Design-Entscheidung")],
        [Paragraph("Kryptographie (Passwort-Hashing der Kindersicherung)", BODY),
         ok("Kein Finding (PBKDF2, Salt, compare_digest)")],
        [Paragraph(".desktop-/Launcher-Injection (Exec-/Icon-Felder)", BODY),
         ok("Kein Finding (validierte Namen, CR/LF-Strip)")],
        [Paragraph("XSS / Pfad-Traversal in Website-PHP", BODY),
         ok("Kein Finding (Fix-Map, htmlspecialchars)")],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval, exec)", BODY),
         ok()],
        [Paragraph("PDF-Injection in der Linux-Hilfe (render_text_pdf)", BODY),
         ok("Kein Finding (Text-Escaping)")],
        [Paragraph("Hardcoded Credentials / API-Keys", BODY), ok()],
        [Paragraph("Regression der Runde-7-Haertungen", BODY),
         ok("Alle intakt")],
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
        Paragraph("<b>Auditor:</b> Claude Fable 5 (Anthropic) — Analyse-Sub-Agent + zwei dedizierte False-Positive-Validierungs-Sub-Agenten", BODY),
        Paragraph("<b>Projektverantwortlicher:</b> Sven Froehlich", BODY),
        Paragraph("<b>Datum:</b> 18. Juli 2026", BODY),
        Paragraph("<b>Codestand:</b> c2087b63 + Arbeitsstand (modified/untracked), Fokus Secure-Browser-Subsystem inkl. Kindersicherung, Linux-Hilfe-Services, Medien-Controller & Website-PHP — Runde 8", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation + Konfidenz-gescorte FP-Validierung pro Kandidat + Umsetzung einer Defense-in-Depth-Haertung mit Regressionstest + Regressions-Gegenpruefung der Runde-7-Haertungen (Testsuiten: 173 + 80 + 121 Tests, alle sicherheitsrelevanten Tests bestanden) — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r8.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
