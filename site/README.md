# NetMon Website

## Lokal testen

Wichtig:

- Fuer Build, Website und lokale NetMon-Entwicklung ist kein Docker-Setup mehr vorgesehen.
- Die aktuelle Repo-Grundlinie setzt auf Host + `.venv` oder optional den gehaerteten
  Standard-Devcontainer ohne Docker-Socket-Mount.

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
- Die JSON-Persistenz benoetigt PHP ab 7.3; geprueft mit PHP CLI 8.3.6. Es sind
  keine weiteren PHP-Erweiterungen erforderlich. Ab PHP 8.1 wird zusaetzlich
  `fsync()` vor dem Rename geprueft, wenn verfuegbar.
- Beim lokalen simplen HTTP-Test laufen die PHP-Seiten nicht automatisch mit.
- Die Statistikseite benoetigt zwingend einen serverseitig fuer PHP verfuegbaren
  `NETMON_STATS_TOKEN`. Fehlende/ungueltige Konfiguration ergibt HTTP 503;
  Zugriff nur per `Authorization: Bearer`, fehlende/falsche Berechtigung HTTP 403.
  URL-Tokens werden nicht mehr akzeptiert. Hosting- und lokale Readiness-Pruefung:
  [L-02](../docs/security/L-02.md).
- Keine echten Tokens in `site/download-config.php`, `.htaccess`, Commits oder Upload-Zips ablegen. Das Repo und die Build-Artefakte muessen secret-frei bleiben.

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
NETMON_MINISIGN_SECRET_KEY=/pfad/zum/bestehenden/release.key make site-build
```

Danach liegen bereit:

- `dist/site-build/public_html/`
- `dist/site-build/netmonroots_public_html.zip`

Zusaetzlich enthalten:

- `dist/site-build/public_html/latest-version.json`
- `dist/site-build/public_html/aktuelles.html`
- `dist/site-build/public_html/changelog.html`
- `dist/site-build/public_html/downloads.html`
- `dist/site-build/public_html/tour.html`
- `dist/site-build/public_html/legal.html`
- `dist/site-build/public_html/impressum.html`
- `dist/site-build/public_html/security-audit.html`
- `dist/site-build/public_html/security-audit-r2.html` bis `security-audit-r7.html`
- `dist/site-build/public_html/favicon.png`
- `dist/site-build/public_html/download.php`
- `dist/site-build/public_html/download-stats.php`
- `dist/site-build/public_html/data/download-stats.json`
- `dist/site-build/public_html/robots.txt`
- `dist/site-build/public_html/sitemap.xml`
- `dist/site-build/public_html/en/`
- `dist/site-build/public_html/screenshots/`
- `dist/site-build/public_html/netmon_security_audit_2026.pdf`
- `dist/site-build/public_html/netmon_security_audit_2026_r2.pdf` bis `netmon_security_audit_2026_r7.pdf`
- `dist/site-build/public_html/LICENSE.txt`
- `dist/site-build/public_html/THIRD_PARTY_NOTICES.md`
- `dist/site-build/public_html/dist/SHA256SUMS`
- `dist/site-build/public_html/verify/verify_netmon_download.sh`

Verpflichtend bei jedem Produktions-Build:

- `dist/site-build/public_html/dist/SHA256SUMS.minisig`
- `dist/site-build/public_html/verify/netmonroots.minisign.pub`
- `dist/site-build/public_html/verify/verify_netmon_signature.sh`
- Maintainer-Doku: `docs/MINISIGN_RELEASES.md`

Vor dem manuellen Upload muss die fertige ZIP aus einem geprueften Checkout
mit `python3 scripts/verify_netmon_release_bundle.py <ZIP> --kind site`
beziehungsweise `--kind update` geprueft werden. Bei einem Build-/Prueffehler
nicht hochladen. Alte Ausgaben liegen nach einem neuen Versuch nur noch in
`dist/.release-history/` und sind kein neuer Build-Erfolg. Im Repository gibt es
keinen automatisierten Publikationsjob.

Unsignierte Tests ausschliesslich mit `make unsigned-test-bundle`: Ausgabe unter
`unsigned-test-builds/`, andere Dateinamen, dauerhafter `UNSIGNED-TEST-ONLY`-Marker,
keine `public_html`-Struktur. Nicht veroeffentlichen. Die alte Variable
`NETMON_ALLOW_UNSIGNED_BUILD` ist wirkungslos. Details: [Release-Ablauf](../docs/MINISIGN_RELEASES.md).

## Nur Release-Dateien aktualisieren

Wenn sich nur Paket, Doku, `SHA256SUMS`, `latest-version.json` oder die
Download-/Doku-Seiten geaendert haben, reicht ein kleines Release-Update-Bundle:

```bash
NETMON_MINISIGN_SECRET_KEY=/pfad/zum/bestehenden/release.key make site-release-update
```

Danach liegen bereit:

- `dist/site-release-update/public_html/`
- `dist/site-release-update/netmonroots_release_update.zip`

Dieses Bundle enthaelt nur:

- `public_html/latest-version.json`
- `public_html/download-config.php`
- `public_html/downloads.html`
- `public_html/docs.html`
- `public_html/en/downloads.html`
- `public_html/en/docs.html`
- `public_html/dist/netmon_<version>_all.deb`
- `public_html/dist/SHA256SUMS`
- `public_html/dist/docs/netmon_dokumentation_<version>.pdf`
- `public_html/dist/docs/netmon_dokumentation_<version>.html`
- `public_html/verify/verify_netmon_download.sh`
- `public_html/dist/SHA256SUMS.minisig`
- `public_html/verify/netmonroots.minisign.pub`
- `public_html/verify/verify_netmon_signature.sh`

Das ist fuer neue `.deb`-Builds und Signaturen deutlich leichter als ein kompletter
Website-Reupload.

Wichtig:

- Vor dem Upload pruefen, dass `public_html/download-config.php` keinen fest eingebauten Token enthaelt.
- Zugriffstoken nur serverseitig ueber die vom Hoster vorgesehene Secret-Konfiguration
  an die verwendete PHP-SAPI uebergeben. Eine Shell-/cPanel-Variable allein belegt
  nicht, dass PHP-FPM sie sieht; Authorization-Weitergabe separat pruefen.
- Die Build-Skripte brechen absichtlich ab, wenn in `site/download-config.php` noch ein harter `stats_token` gefunden wird.

## Download verifizieren

Den Verifier aus einem unabhaengig bezogenen, geprueften Repository-Checkout
mit H-01-Fix verwenden. Der Verifier erzwingt den eingebauten NetMon-Key ohne
Umgebungsvariable. Ein gemeinsam mit den Artefakten vom Downloadserver bezogenes
Skript ist kein unabhaengiger Vertrauensanker. Den absoluten Pfad anpassen:

```bash
cd /tmp/netmon-download
NETMON_REPO=/absoluter/pfad/zum/vertrauten/dev-lab
bash "$NETMON_REPO/scripts/verify_netmon_signature.sh" \
  netmonroots.minisign.pub \
  SHA256SUMS.minisig \
  SHA256SUMS &&
sha256sum -c SHA256SUMS
```

Nur nach erfolgreicher Signatur- und Hash-Pruefung installieren. Nach dem
Herunterladen der Dateien ist keine Netzwerkverbindung zur Pruefung erforderlich.

Maintainer-Ablauf fuer signierte Releases:

```bash
make site-print-minisign
```

## Kurzcheck

- Startseite laedt ohne fehlende Styles oder Bilder.
- Sprachumschalter `DE / EN` funktioniert auf Start-, Download-, Doku-, Rundgang-, Legal-, Impressum- und Audit-Seite.
- Navigation und Sprachumschalter funktionieren auch auf `Aktuelles` bzw. `Updates`.
- Der veroeffentlichte Download-Link zeigt auf `dist/netmon_1.1.21_all.deb`; Paket-, Repository- und Dokumentationsstand sind damit angeglichen.
- `latest-version.json` liegt im Build und passt zum aktuellen Website-/Paketstand.
- Doku-Links fuer PDF und HTML funktionieren.
- Rundgang-Bilder oeffnen per Klick in der Lightbox.
- Security-Audit Runde 12 ist als HTML und PDF erreichbar; Runde 11 bleibt als Archivfassung erhalten.
- `robots.txt` und `sitemap.xml` liegen im Build unter `public_html/`.
- `download.php` und `download-stats.php` liegen im Build unter `public_html/`.
- Seite bleibt auch bei schmalem Browserfenster lesbar.
- Statistikzugriff nach Deploy nur mit `Authorization: Bearer` ueber HTTPS direkt
  auf den kanonischen Host; keine Token-URL, kein Credential-Redirect. Siehe L-02.

Die Statistik wird unter einer stabilen separaten Lock-Datei aktualisiert.
Schreib- und Serialisierungsfehler erhalten die bisherige Datei; parallele PHP-
Prozesse lesen und schreiben unter demselben Lock. Das JSON-Schema, konfigurierte
Download-IDs und Redirects bleiben unveraendert. L-02 aendert ausschliesslich
den Zugriff auf die Statistik von URL-Token auf verpflichtenden Bearer-Header.

Telemetrie wird auf gueltiges UTF-8 normalisiert und nach Bytes begrenzt:
`src` 256, Referer 2048, Sprache 8, Accept-Language 256 und IP-Eingabe vor dem
Hashen 128. Die Download-ID ist auf 128 Bytes begrenzt; ueberlange oder als
Array uebergebene IDs erhalten weiterhin 404. Nichtskalare Telemetrie wird nicht
uebernommen. Defekte UTF-8-Sequenzen werden durch U+FFFD ersetzt; mehrbyteige
Zeichen werden an der Laengengrenze nicht halb gespeichert.

Zum Deploy siehe [Dateirechte und Rollout](DEPLOY_HTTPS.md#htaccess). Vorhandene
produktive JSON-/Lock-Dateien beibehalten und die drei PHP-Endpunkt-/Bibliotheks-
Dateien gemeinsam aktualisieren. Regressionstests verwenden nur temporaere
Dateien und lokale Testserver:

```bash
python3 -m pytest -q tests/test_download_statistics.py
```

Falls PHP CLI nicht im PATH liegt, kann der Testlauf explizit
`NETMON_TEST_PHP=/absoluter/pfad/zum/php` verwenden. Ohne PHP CLI werden diese
Tests kenntlich uebersprungen; fuer die vollstaendige Sicherheitspruefung muss
PHP vorhanden sein. HTTP-Integrationstests benoetigen lokale Sockets auf 127.0.0.1.

## Struktur

- `site/index.html`: Landingpage
- `site/latest-version.json`: Website-Version fuer den About-Dialog der App
- `site/downloads.html`: Download, Verifikation, Lizenz- und Audit-Einstieg
- `site/aktuelles.html`: zentrale Status- und Hinweis-Seite fuer bekannte Probleme
- `site/docs.html`: Doku, FAQ, AI- und Betriebsinfos
- `site/tour.html`: Rundgang mit Screenshots und Lightbox
- `site/security-audit.html`: aktuelle Audit-Webfassung Runde 12 fuer `1.1.21`
- `site/security-audit-r6.html`: historischer Build-Zielalias fuer `1.1.16`
- `site/netmon_security_audit_2026_r12.pdf`: aktuelle Audit-PDF-Fassung fuer `1.1.21`
- `site/netmon_security_audit_2026_r11.pdf`: archivierte Audit-PDF-Fassung der Vorrunde
- `site/legal.html`: Drittlizenzen und Lizenzhinweise
- `site/impressum.html`: Anbieterangaben
- `site/en/`: englische Spiegel-Seiten inklusive `updates.html`
- `site/styles.css`: Layout und visuelle Gestaltung
- `site/app.js`: kleine lokale Laufzeitlogik
- `site/download.php`: serverseitiger Download-Zaehler mit Redirect
- `site/download-stats.php`: einfache Statistikseite
- `site/data/download-stats.json`: JSON-Speicher fuer Downloadzahlen
