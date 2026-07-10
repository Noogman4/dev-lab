# NetMon HTTPS Deployment

## Domain-Entscheidung

- Hauptdomain: `netmonroots.com`
- Redirect: `netmon-roots.com`
- Redirect: `netmon-roots.app`

## Zielumgebung

- cPanel-Hosting fuer `netmonroots.com`
- HTTPS ueber Hosting-SSL, `AutoSSL` oder das SSL-Tool des Hosters
- Redirects und Canonical Host ueber `.htaccess`

## Erwartete Verzeichnisstruktur auf dem Server

Die Website soll in den cPanel-Webroot, typischerweise:

```text
public_html/
```

Kopiert werden. Dort sollten mindestens diese Dateien liegen:

- `index.html`
- `downloads.html`
- `tour.html`
- `legal.html`
- `impressum.html`
- `security-audit.html`
- `docs.html`
- `download.php`
- `download-stats.php`
- `robots.txt`
- `sitemap.xml`
- `styles.css`
- `app.js`
- `.htaccess`
- `en/...`
- `screenshots/...`
- `netmon_security_audit_2026.pdf`
- `LICENSE.txt`
- `THIRD_PARTY_NOTICES.md`
- `dist/...`
- `dist/SHA256SUMS`
- `tools/netmon.png`
- `tools/netmon-radio.png`
- `docs/CHANGELOG.md`
- `verify/verify_netmon_download.sh`
- `data/download-stats.json`
- optional `dist/SHA256SUMS.minisig`
- optional `verify/netmonroots.minisign.pub`
- optional `verify/verify_netmon_signature.sh`

Die HTML-Dateien verwenden jetzt Root-Pfade wie `/dist/...` und `/tools/...`. Das passt fuer cPanel gut, solange `dist/`, `tools/` und optional `docs/` direkt unter `public_html/` liegen.

## Empfohlene Auslieferung

Beispiel:

```text
public_html/index.html
public_html/downloads.html
public_html/tour.html
public_html/legal.html
public_html/impressum.html
public_html/security-audit.html
public_html/docs.html
public_html/download.php
public_html/download-stats.php
public_html/robots.txt
public_html/sitemap.xml
public_html/styles.css
public_html/app.js
public_html/.htaccess
public_html/en/index.html
public_html/en/downloads.html
public_html/en/docs.html
public_html/en/tour.html
public_html/en/legal.html
public_html/en/impressum.html
public_html/en/security-audit.html
public_html/screenshots/netmon-status-header-tour.png
public_html/netmon_security_audit_2026.pdf
public_html/LICENSE.txt
public_html/THIRD_PARTY_NOTICES.md
public_html/dist/netmon_1.1.17_all.deb
public_html/dist/SHA256SUMS
public_html/tools/netmon.png
public_html/docs/CHANGELOG.md
public_html/verify/verify_netmon_download.sh
public_html/data/download-stats.json
public_html/dist/SHA256SUMS.minisig
public_html/verify/netmonroots.minisign.pub
public_html/verify/verify_netmon_signature.sh
```

## .htaccess

Die fertige Apache-/cPanel-Konfiguration liegt in:

- `site/.htaccess`

Fuer den Downloadzaehler wichtig:

- `public_html/download.php` zaehlt und leitet danach auf die echte Datei weiter.
- `public_html/download-stats.php` zeigt die Statistikseite.
- `public_html/data/download-stats.json` muss fuer PHP schreibbar sein.
- Bevorzugt den Token serverseitig als Umgebungsvariable `NETMON_STATS_TOKEN` setzen.
- Beispiel per `.htaccess` auf dem Server: `SetEnv NETMON_STATS_TOKEN dein_langer_token`
- Keine echten Tokens in `download-config.php`, Repo-`.htaccess`, Commits oder Upload-Zips speichern.
- Aufruf danach: `https://netmonroots.com/download-stats.php?token=DEIN_TOKEN`

Sie macht:

- `301`-Redirect auf `https://netmonroots.com`
- Redirect von `www.netmonroots.com`
- Redirect von `netmon-roots.com`
- Redirect von `netmon-roots.app`
- grundlegende Security-Header

## DNS

Vor produktivem Start:

1. `A`- oder `AAAA`-Records fuer alle drei Domains auf den Zielserver setzen.
2. Warten, bis die Domains aufloesen.
3. Im Hostingpanel pruefen, dass SSL fuer `netmonroots.com` aktiv ist.
4. Erst danach HTTPS-Redirect erzwingen.

## Server-Schritte

Beispielhaft:

```bash
make site-build
```

Danach kannst du entweder:

- `dist/site-build/public_html/` direkt hochladen
- oder `dist/site-build/netmonroots_public_html.zip` in cPanel entpacken

Fuer signierte Releases:

- `NETMON_MINISIGN_SECRET_KEY=/pfad/zum/seckey.txt make site-build`
- optional zusaetzlich `NETMON_MINISIGN_PUBKEY=/pfad/zum/pubkey.txt`
- kompletter Ablauf in `docs/MINISIGN_RELEASES.md`

## Wichtiger Hinweis zu Zertifikaten

Bei deinem cPanel-Hosting ist es meist besser, das Zertifikat direkt im Hostingpanel zu verwalten.

Manuelle Zertifikate lohnen sich eher nur dann, wenn:

- der Hoster kein `AutoSSL` anbietet
- du ein vorhandenes eigenes Zertifikat ueber das SSL-Tool importieren willst
- oder dir vom Hoster genau dieses Verfahren vorgegeben wird

## Reihenfolge fuer den Go-Live

1. Domain zeigt auf `169.60.39.100`.
2. SSL fuer `netmonroots.com` ist im Hosting aktiv.
3. Dateien liegen in `public_html/`.
4. `.htaccess` ist aktiv.
5. `https://netmonroots.com` testen.
6. `http://netmonroots.com`, `https://netmon-roots.com` und `https://netmon-roots.app` auf Redirect pruefen.

## Lokal pruefen

Website lokal weiter per:

```bash
make site-serve
```

Lokal per `http.server` laufen die Root-Pfade nur dann sauber, wenn du den Repo-Wurzelordner servierst. Das ist bei `make site-serve` bereits der Fall.
