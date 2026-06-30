# NetMon Website

## Lokal testen

Im Repo-Wurzelverzeichnis:

```bash
make site-open
```

Dadurch wird der lokale Server bei Bedarf gestartet und die Startseite geoeffnet.

Manuell im Browser:

- `http://127.0.0.1:8765/site/index.html`
- `http://127.0.0.1:8765/site/docs.html`

Hinweis:

- Die Download-Statistik (`download.php`, `download-stats.php`) benoetigt PHP.
- Beim lokalen simplen HTTP-Test laufen die PHP-Seiten nicht automatisch mit.
- Die Statistikseite ist per Token geschuetzt. Bevorzugt den Token serverseitig als Umgebungsvariable `NETMON_STATS_TOKEN` setzen.
- Nur wenn das nicht moeglich ist, den Platzhalter in `site/download-config.php` ersetzen.

Server stoppen:

```bash
make site-stop
```

## HTTPS vorbereiten

Fuer produktive HTTPS-Auslieferung mit `netmonroots.com` auf cPanel liegen bereit:

- `site/.htaccess`
- `site/DEPLOY_HTTPS.md`

Anzeigen per:

```bash
make site-print-htaccess
```

## Upload-Paket bauen

Fuer eine `public_html`-fertige Struktur:

```bash
make site-build
```

Danach liegen bereit:

- `dist/site-build/public_html/`
- `dist/site-build/netmonroots_public_html.zip`

Zusaetzlich enthalten:

- `dist/site-build/public_html/latest-version.json`
- `dist/site-build/public_html/aktuelles.html`
- `dist/site-build/public_html/downloads.html`
- `dist/site-build/public_html/tour.html`
- `dist/site-build/public_html/legal.html`
- `dist/site-build/public_html/impressum.html`
- `dist/site-build/public_html/security-audit.html`
- `dist/site-build/public_html/security-audit-r4.html`
- `dist/site-build/public_html/favicon.png`
- `dist/site-build/public_html/download.php`
- `dist/site-build/public_html/download-stats.php`
- `dist/site-build/public_html/data/download-stats.json`
- `dist/site-build/public_html/robots.txt`
- `dist/site-build/public_html/sitemap.xml`
- `dist/site-build/public_html/en/`
- `dist/site-build/public_html/screenshots/`
- `dist/site-build/public_html/netmon_security_audit_2026.pdf`
- `dist/site-build/public_html/netmon_security_audit_2026_r4.pdf`
- `dist/site-build/public_html/LICENSE.txt`
- `dist/site-build/public_html/THIRD_PARTY_NOTICES.md`
- `dist/site-build/public_html/dist/SHA256SUMS`
- `dist/site-build/public_html/verify/verify_netmon_download.sh`

Optional bei signierten Releases:

- `dist/site-build/public_html/dist/SHA256SUMS.minisig`
- `dist/site-build/public_html/verify/netmonroots.minisign.pub`
- `dist/site-build/public_html/verify/verify_netmon_signature.sh`
- Maintainer-Doku: `docs/MINISIGN_RELEASES.md`

## Download verifizieren

Hash:

```bash
cd /tmp/netmon-download
sha256sum -c SHA256SUMS
```

Signatur, falls vorhanden:

```bash
bash verify_netmon_signature.sh \
  netmonroots.minisign.pub \
  SHA256SUMS.minisig \
  SHA256SUMS
```

Maintainer-Ablauf fuer signierte Releases:

```bash
make site-print-minisign
```

## Kurzcheck

- Startseite laedt ohne fehlende Styles oder Bilder.
- Sprachumschalter `DE / EN` funktioniert auf Start-, Download-, Doku-, Rundgang-, Legal-, Impressum- und Audit-Seite.
- Navigation und Sprachumschalter funktionieren auch auf `Aktuelles` bzw. `Updates`.
- Download-Link zeigt auf `dist/netmon_1.1.15_all.deb`.
- `latest-version.json` liegt im Build und passt zum aktuellen Website-/Paketstand.
- Doku-Links fuer PDF und HTML funktionieren.
- Rundgang-Bilder oeffnen per Klick in der Lightbox.
- Security-Audit ist als HTML und PDF erreichbar; der aktuelle Release-Stand zeigt auf Runde 4 fuer `1.1.15`.
- `robots.txt` und `sitemap.xml` liegen im Build unter `public_html/`.
- `download.php` und `download-stats.php` liegen im Build unter `public_html/`.
- Seite bleibt auch bei schmalem Browserfenster lesbar.
- Statistikaufruf nach Deploy: `https://netmonroots.com/download-stats.php?token=DEIN_TOKEN`

## Struktur

- `site/index.html`: Landingpage
- `site/latest-version.json`: Website-Version fuer den About-Dialog der App
- `site/downloads.html`: Download, Verifikation, Lizenz- und Audit-Einstieg
- `site/aktuelles.html`: zentrale Status- und Hinweis-Seite fuer bekannte Probleme
- `site/docs.html`: Doku, FAQ, AI- und Betriebsinfos
- `site/tour.html`: Rundgang mit Screenshots und Lightbox
- `site/security-audit.html`: historische Webfassung eines frueheren Audits
- `site/security-audit-r4.html`: aktuelle Webfassung des Audits fuer `1.1.15`
- `site/legal.html`: Drittlizenzen und Lizenzhinweise
- `site/impressum.html`: Anbieterangaben
- `site/en/`: englische Spiegel-Seiten inklusive `updates.html`
- `site/styles.css`: Layout und visuelle Gestaltung
- `site/app.js`: kleine lokale Laufzeitlogik
- `site/download.php`: serverseitiger Download-Zaehler mit Redirect
- `site/download-stats.php`: einfache Statistikseite
- `site/data/download-stats.json`: JSON-Speicher fuer Downloadzahlen
