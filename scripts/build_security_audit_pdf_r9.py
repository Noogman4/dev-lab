#!/usr/bin/env python3
"""Generate NetMon Security Audit Report as PDF — v1.1.19 Runde 9 (Release)."""

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
        title="NetMon Security Audit 2026 — v1.1.19 Runde 9",
        author="Claude Fable 5 / Sven Froehlich",
        subject="Statische Sicherheitsanalyse NetMon Roots v1.1.19 (Runde 9, Release)",
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
        Paragraph("SICHERHEITS-AUDIT — RUNDE 9 (RELEASE)", s(
            "EYEBROW", fontName="Helvetica", fontSize=10, leading=13,
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=6)),
        Paragraph("NetMon Roots v1.1.19", s(
            "TITLE", fontName="Helvetica-Bold", fontSize=28, leading=34,
            textColor=colors.HexColor("#16263a"), alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Code Security Review — finaler Release-Stand — Juli 2026", s(
            "SUB", fontName="Helvetica", fontSize=13, leading=18,
            textColor=colors.HexColor("#5f6368"), alignment=TA_CENTER, spaceAfter=20)),
        HRFlowable(width="100%", thickness=1, color=C_LINE),
        Spacer(1, 6 * mm),
    ]

    meta_data = [
        ["Datum", "18. Juli 2026"],
        ["Analysierte Version", "v1.1.19 — finaler Release-Stand"],
        ["Schwerpunkt", "Killswitch-Reconcile, DNS-Recovery, Update-Check, deb-Skripte, Release-Signatur"],
        ["Kritische Findings", "0"],
        ["Hohe Findings", "0"],
        ["Mittlere Findings", "2 (beide behoben & verifiziert)"],
        ["Haertungen umgesetzt", "2 + neue Regressionstests"],
        ["Release-Signatur (minisign)", "gueltig verifiziert"],
        ["Regressionstests", "253 + 80 Tests, sicherheitsrelevante alle gruen"],
        ["Analysewerkzeug", "Claude Fable 5 (Anthropic)"],
        ["Projektverantwortlicher", "Sven Froehlich"],
    ]
    meta_table = Table(
        [[Paragraph(k, MUTED), Paragraph(v, BODY)] for k, v in meta_data],
        colWidths=[60 * mm, None],
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
            "0 KRITISCHE — 0 HOHE — 2 MITTLERE FINDINGS (BEIDE UMGESETZT & VERIFIZIERT)", s(
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
            "Die neunte Sicherheitsanalyse pruefte erstmals den finalen "
            "Release-Stand v1.1.19 statt eines Zwischenstands. Schwerpunkte: der "
            "VPN/UFW-Killswitch-Reconcile, die DNS-Startup-Recovery, der "
            "In-App-Update-Check, die Debian-Maintainer-Skripte (Install/"
            "Deinstall als root) und der komplette Release-Verifikationspfad "
            "(SHA256SUMS + minisign). Die Release-Artefakte wurden empirisch "
            "verifiziert: sha256sum -c bestaetigt alle drei Dateien, und die "
            "minisign-Signatur der SHA256SUMS ist gegen den gepinnten Public Key "
            "gueltig.",
            BODY),
        Paragraph(
            "Anders als in den Vorrunden wurden zwei belastbare Schwachstellen "
            "mittleren Schweregrads bestaetigt (Validierung je Konfidenz 8/10). "
            "Beide wurden direkt umgesetzt, mit Regressionstests abgesichert und "
            "verifiziert. Keine kritischen oder hohen, keine klar "
            "remote-ausnutzbaren RCE-Befunde.",
            BODY),
        Paragraph(
            "F1 (MEDIUM, behoben): Der In-App-Update-Check uebernahm die "
            "download_url aus der per HTTPS geladenen latest-version.json "
            "ungeprueft und uebergab sie beim Oeffnen des Ueber-Dialogs ohne "
            "weiteren Klick an xdg-open — ohne die http/https-Allowlist, die an "
            "vergleichbaren Stellen (Secure-Browser-fetch_url, Radio-Logo) bereits "
            "existiert. Ein kompromittierter Server/CDN haette so eine file://- "
            "oder Custom-Scheme-URL oder eine Phishing-Seite an den registrierten "
            "Desktop-Handler weiterreichen koennen (kein RCE — Listenform-Popen). "
            "Gehaertet: _open_url_with_xdg_open() erzwingt jetzt http/https; "
            "_is_trusted_update_url() beschraenkt die automatisch geoeffnete URL "
            "zusaetzlich auf die netmonroots.com-Domain und faellt sonst auf die "
            "fest konfigurierte Download-Seite zurueck.",
            BODY),
        Paragraph(
            "F2 (MEDIUM, behoben): recover_firewall_after_killswitch_failure() "
            "setzte die Firewall bedingungslos auf 'ufw default allow outgoing' "
            "und wurde in drei fruehen Fehlerpfaden von vpn_switch() aufgerufen "
            "(leeres Ziel, nicht aufloesbares Runtime-Profil, WG-Cleanup-Fehler) "
            "— ohne zu pruefen, ob der Killswitch bewusst aktiv war. Ein "
            "fehlgeschlagener Slot-Wechsel bei aktivem Killswitch konnte so die "
            "deny-outgoing-Garantie still aufheben und Klartext-Traffic freigeben "
            "— ein Fail-Open in einer Kontrolle, deren Zweck Fail-Closed ist. "
            "Gehaertet: die drei Stellen nutzen jetzt "
            "_recover_firewall_preserving_killswitch(), das bei aktivem "
            "Killswitch die deny-outgoing-Policy per idempotentem "
            "_killswitch_on_sync() erhaelt und nur ohne aktiven Killswitch auf "
            "allow-outgoing zuruecksetzt.",
            BODY),
        Paragraph(
            "Ergaenzend: Die Release-Signaturkette ist technisch dicht, aber die "
            "minisign-Vollpruefung ist auf der Downloadseite nur als optionaler "
            "Zusatz dargestellt — Empfehlung, sie als Standardweg hervorzuheben "
            "(Doku/UX, keine Code-Luecke). Das postinst biegt aktive NM-DNS bei "
            "der Installation auf 8.8.8.8 um (Vorzustand gesichert, in prerm "
            "restauriert) — funktional sauber, aber fuer ein Privacy-Tool eine "
            "Policy-Frage (Opt-in empfohlen); kein ausnutzbarer Befund. Die "
            "Kindersicherung bleibt als bewusste Design-Entscheidung dokumentiert. "
            "Alle Runde-7/8-Haertungen sind intakt; Versionskonsistenz (App, deb, "
            "Site, latest-version.json) ist durchgaengig 1.1.19.",
            BODY),
    ]

    # ── Methodik ──────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("2. Methodik", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
        Paragraph("Phase 1 - Release-Recon & Signaturpruefung", H3),
        Paragraph(
            "Verifikation der Artefakte: sha256sum -c SHA256SUMS (alle drei OK), "
            "minisign -V gegen den gepinnten Public Key (Signatur gueltig). "
            "Extraktion und Review der .deb-Maintainer-Skripte (postinst/prerm). "
            "Versionskonsistenz-Abgleich ueber App, deb-control, latest-version.json "
            "und Download-Seiten.",
            BODY),
        Paragraph("Phase 2 - Kandidaten-Analyse", H3),
        Paragraph(
            "Ein Analyse-Sub-Agent verfolgte Datenfluesse von Fremdeingaben "
            "(Update-/API-Antworten, VPN-Profil-/Slot-Daten, Install-Zeit-Zustand) "
            "bis zu privilegierten Senken (ufw/nmcli/wg-quick, xdg-open, "
            "root-cp/chown). 5 Kandidaten identifiziert.",
            BODY),
        Paragraph("Phase 3 - False-Positive-Validierung", H3),
        Paragraph(
            "Die zwei belastbaren Kandidaten wurden von je einem eigenen "
            "Validierungs-Sub-Agenten gegengeprueft (beide Konfidenz 8/10, "
            "MEDIUM). Drei weitere Kandidaten (postinst-DNS-Policy, "
            "State-Datei-Parsing, root-Symlink-chown) lagen als Policy-/Grenzfall "
            "unter der Schwelle und sind nicht ausnutzbar im Threat Model.",
            BODY),
        Paragraph("Phase 4 - Haertung & Regressionscheck", H3),
        Paragraph(
            "Beide MEDIUM-Findings wurden umgesetzt, mit fuenf neuen "
            "Regressionstests abgesichert und verifiziert. Suiten erneut "
            "ausgefuehrt: Killswitch/VPN/DNS/Firewall (253) und "
            "Diagnostik/Update-Check (80) — alle sicherheitsrelevanten Tests gruen.",
            BODY),
    ]

    # ── Findings ──────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Bestaetigte Findings", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    findings = [
        (
            "F1 — Update-Check oeffnet server-gelieferte URL ohne Schema-Allowlist  "
            "[MEDIUM, Konfidenz 8/10, behoben]",
            "netmon/app.py — _fetch_latest_release_info() / "
            "check_about_latest_version() / _open_url_with_xdg_open().",
            "Der In-App-Update-Check laedt latest-version.json per HTTPS und "
            "uebernimmt die download_url daraus ungeprueft. Wird beim Oeffnen des "
            "Ueber-Dialogs eine neuere Version erkannt, wird diese URL ohne "
            "weiteren Klick an xdg-open uebergeben — ohne Schema-/Host-Pruefung, "
            "obwohl dieselbe http/https-Allowlist an vergleichbaren Stellen "
            "(fetch_url, _station_logo_url) bereits existiert. Ein kompromittierter "
            "Server/CDN (im Threat Model enthalten) kann eine download_url mit "
            "beliebigem Schema (file://, vnc://) oder eine Phishing-Seite liefern, "
            "die xdg-open an den registrierten Desktop-Handler weiterreicht. Kein "
            "direktes RCE (Listenform-Popen, keine Shell-Injection), aber "
            "zuverlaessig fuer Phishing und situativ zum Ansteuern eines "
            "Scheme-Handlers.",
            "Gehaertet & verifiziert: _open_url_with_xdg_open() begrenzt Ziel-URLs "
            "auf http/https (deckt alle Aufrufer ab); _is_trusted_update_url() "
            "laesst nur eine netmonroots.com-URL automatisch oeffnen und faellt "
            "sonst auf die fest konfigurierte Download-Seite zurueck. Mit "
            "Regressionstests abgesichert.",
        ),
        (
            "F2 — Killswitch-Fail-Open in fruehen VPN-Slot-Wechsel-Fehlerpfaden  "
            "[MEDIUM, Konfidenz 8/10, behoben]",
            "netmon/features/vpn_controller.py — vpn_switch(); "
            "netmon/features/firewall_controller.py — "
            "recover_firewall_after_killswitch_failure().",
            "recover_firewall_after_killswitch_failure() setzt die Firewall "
            "bedingungslos auf 'ufw default allow outgoing'. Sie wurde in drei "
            "fruehen Fehlerpfaden von vpn_switch() aufgerufen (leeres Ziel, nicht "
            "aufloesbares Runtime-Profil, WG-Cleanup-Fehler) — ohne zu pruefen, ob "
            "der Killswitch bewusst aktiv war. Hatte der Nutzer Killswitch AN + VPN "
            "aktiv und waehlte einen Slot, dessen Profil geloescht/umbenannt wurde "
            "oder dessen IPv4-Runtime-Kopie fehlt, brach vpn_switch() frueh ab und "
            "die deny-outgoing-Garantie wurde still auf allow zurueckgesetzt — "
            "Klartext-Traffic konnte das System verlassen, obwohl der Nutzer "
            "Killswitch-Schutz erwartete. Ein Fail-Open in einer Kontrolle, deren "
            "einziger Zweck Fail-Closed ist.",
            "Gehaertet & verifiziert: die drei Aufrufstellen nutzen jetzt "
            "_recover_firewall_preserving_killswitch(). War der Killswitch aktiv "
            "(killswitch_is_on(), ausgewertet vor jeder Zustandsaenderung), wird die "
            "deny-outgoing-Policy per idempotentem _killswitch_on_sync() erhalten "
            "statt geoeffnet; nur ohne aktiven Killswitch wird wie bisher auf "
            "allow-outgoing zurueckgesetzt, damit sich der Nutzer nicht aussperrt. "
            "Mit Regressionstests abgesichert.",
        ),
    ]

    for title, loc, detail, fix in findings:
        rows = [
            [Paragraph(title, FINDING_TITLE), Paragraph("")],
            [Paragraph(loc, MONO), Paragraph("")],
            [Paragraph(detail, BODY), Paragraph("")],
            [Paragraph("<b>Behebung:</b> " + fix, s(
                "VD", fontName="Helvetica", fontSize=9, leading=13,
                textColor=colors.HexColor("#145a32"),
                backColor=C_BG_GREEN, leftIndent=4)), Paragraph("")],
        ]
        t = Table(rows, colWidths=["82%", "18%"])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f0c98a")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.3, C_LINE),
            ("BACKGROUND", (0, 0), (-1, 0), C_BG_AMBER),
            ("BACKGROUND", (0, 3), (-1, 3), C_BG_GREEN),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [t, Spacer(1, 5 * mm)]

    # ── Release-Verifikation & Beobachtungen ──────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Release-Verifikation & weitere Beobachtungen", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    observations = [
        ("Release-Signaturkette technisch dicht — Empfehlung zur Sichtbarkeit",
         "SHA256SUMS deckt alle drei Artefakte korrekt ab (sha256sum -c OK) und ist "
         "per minisign signiert; die Signatur wurde gegen den gepinnten Public Key "
         "gueltig verifiziert. Das Verifier-Skript prueft jedoch nur die Hashes, und "
         "die prominente 'Schnellpruefung' auf der Downloadseite empfiehlt ebenfalls "
         "nur sha256sum -c — ein MitM, der .deb UND SHA256SUMS gemeinsam ersetzt, "
         "bestuende diesen Schnellcheck. Empfehlung (Doku/UX, keine Code-Luecke): die "
         "minisign-Vollpruefung als empfohlenen Standardweg hervorheben statt als "
         "optionalen 'falls signiert'-Zusatz."),
        ("Kindersicherung — weiterhin bewusste Design-Entscheidung",
         "Die PBKDF2-gestuetzte Kindersicherung im Secure-Browser bleibt wie in "
         "Runde 8 dokumentiert: Alltagshuerde gegen Gelegenheitszugriff im selben "
         "Konto, keine harte Grenze gegen technisch versierte Nutzer mit "
         "Kontozugriff. Keine Codeaenderung, unveraendert gueltig."),
        ("postinst setzt aktive NM-DNS auf 8.8.8.8 — Policy-Hinweis",
         "Das root-postinst biegt aktive NetworkManager-Verbindungen bei der "
         "Installation auf ipv4.dns 8.8.8.8 um (Vorzustand gesichert, in prerm "
         "restauriert). Funktional sauber und ohne ausnutzbaren Befund "
         "(State-Datei 0600 root, Argumentlisten-Aufrufe, keine Injection), aber "
         "fuer ein Privacy-Tool eine ueberraschende Richtung. Empfehlung: Opt-in "
         "statt hart verdrahtetem Public-Resolver. Als Design-Entscheidung des "
         "Projektverantwortlichen offen — keine Codeaenderung in dieser Runde."),
    ]

    for title, desc in observations:
        rows = [[Paragraph(title, FIXED_TITLE), Paragraph("")],
                [Paragraph(desc, BODY), Paragraph("")]]
        t = Table(rows, colWidths=["82%", "18%"])
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

    # ── Umgesetzte Haertungen ─────────────────────────────────────────────────
    story += [
        Spacer(1, 4 * mm),
        Paragraph("5. Umgesetzte Haertungen (Runde 9)", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    improvements = [
        ("Schema-Allowlist + Host-Pin fuer die Update-URL — app.py",
         "_open_url_with_xdg_open() laesst nur noch http/https zu; "
         "_is_trusted_update_url() beschraenkt die automatisch geoeffnete "
         "Update-URL zusaetzlich auf die netmonroots.com-Domain."),
        ("Killswitch-erhaltender Recover-Pfad — vpn_controller.py / firewall_controller.py",
         "_recover_firewall_preserving_killswitch() haelt die deny-outgoing-Policy "
         "bei aktivem Killswitch aufrecht (idempotenter Re-Sync), statt sie bei "
         "einem fehlgeschlagenen Slot-Wechsel still zu oeffnen."),
        ("Neue Regressionstests — 5 Tests",
         "test_netmon_diagnostics.py (Update-URL-Allowlist / Host-Pin) und "
         "test_netmon_killswitch.py (Killswitch-erhaltendes Recover-Verhalten). "
         "Sicherheitsrelevante Suiten (253 + 80 Tests) sind gruen."),
    ]

    for title, desc in improvements:
        rows = [[Paragraph(title, FIXED_TITLE), Paragraph("")],
                [Paragraph(desc, BODY), Paragraph("")]]
        t = Table(rows, colWidths=["82%", "18%"])
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
        Paragraph("6. Geprüfte Sicherheitskategorien", H1),
        HRFlowable(width="100%", thickness=0.5, color=C_LINE, spaceAfter=8),
    ]

    def ok(text: str = "Kein Finding"):
        return Paragraph(text, s("OK", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_GREEN))

    def fixed(text: str):
        return Paragraph(text, s("FX", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_AMBER))

    def info(text: str):
        return Paragraph(text, s("IN", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=C_BLUE))

    cat_rows = [
        [Paragraph("Kategorie", MUTED), Paragraph("Ergebnis", MUTED)],
        [Paragraph("Sicherheitskontroll-Umgehung (Killswitch Fail-Open)", BODY),
         fixed("F2 -> behoben (fail-closed)")],
        [Paragraph("Unvalidierte Fremd-URL an Desktop-Handler (xdg-open)", BODY),
         fixed("F1 -> behoben (Allowlist+Host-Pin)")],
        [Paragraph("Command-/Argument-Injection (ufw/nmcli/wg-quick, subprocess)", BODY),
         ok("Kein Finding (list-form)")],
        [Paragraph("DNS-Startup-Recovery (privilegierte nmcli/resolvectl)", BODY),
         ok("Kein Finding (validiert, fail-safe)")],
        [Paragraph("Debian-Maintainer-Skripte (root cp/chown, State-Parsing)", BODY),
         ok("Kein ausnutzbarer Befund")],
        [Paragraph("Release-Integritaet (SHA256SUMS + minisign)", BODY),
         ok("Signatur gueltig (UX-Empfehlung)")],
        [Paragraph("Path Traversal / TOCTOU / Symlink (privilegierte Dateiops)", BODY),
         ok("Kein Finding im Threat Model")],
        [Paragraph("Autorisierung / Kindersicherung", BODY),
         info("Bewusste Design-Entscheidung")],
        [Paragraph("Unsichere Deserialisierung (pickle, yaml.load, eval, shell=True)", BODY),
         ok()],
        [Paragraph("Regression der Runde-7/8-Haertungen", BODY),
         ok("Alle intakt")],
        [Paragraph("Versionskonsistenz (App / deb / Site / latest-version.json)", BODY),
         ok("Durchgaengig 1.1.19")],
    ]
    cat_table = Table(cat_rows, colWidths=["66%", "34%"])
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
        Paragraph("<b>Codestand:</b> finaler Release-Stand v1.1.19 (Arbeitsstand auf c2087b63), einschliesslich der gebauten netmon_1.1.19_all.deb und der signierten Release-Artefakte — Runde 9", BODY),
        Paragraph("<b>Methode:</b> Statische Code-Analyse + manuelle Datenfluss-Verifikation + empirische Verifikation der Release-Signatur (sha256sum -c + minisign -V) + Konfidenz-gescorte FP-Validierung pro Kandidat + Umsetzung von zwei Defense-in-Depth-Haertungen mit Regressionstests + Regressions-Gegenpruefung der Runde-7/8-Haertungen (Suiten: 253 + 80 Tests bestanden) — kein Laufzeit-Penetrationstest", BODY),
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
    pdf_path = OUT_DIR / "netmon_security_audit_2026_r9.pdf"
    build_pdf(pdf_path)
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
