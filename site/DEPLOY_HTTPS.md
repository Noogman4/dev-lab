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
- `dist/SHA256SUMS.minisig`
- `verify/netmonroots.minisign.pub`
- `verify/verify_netmon_signature.sh`

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
public_html/dist/netmon_1.1.21_all.deb
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
- `public_html/data/` muss dem PHP-Benutzer gehoeren und fuer ihn schreibbar sein
  (empfohlen 0700, keine Gruppen-/Weltschreibrechte). Die atomare Speicherung
  benoetigt Schreibrechte im Verzeichnis, nicht nur auf der JSON-Datei.
- JSON-Datei und stabile `download-stats.json.lock` erhalten hoechstens 0600.
  Symlinks in Speicherpfaden sowie Hardlinks auf JSON-/Lock-Dateien werden abgelehnt.
- Beim Update vorhandene `data/download-stats.json` und ihre Lock-Datei erhalten;
  die produktiven Zaehler nicht durch die leere Datei aus einem Website-Bundle ersetzen.
- `download.php`, `download-lib.php` und `download-stats.php` zusammen ausrollen.
  Alte laufende PHP-Requests vorher auslaufen lassen, da sie noch auf der JSON-Datei
  statt auf der neuen separaten Lock-Datei sperren. Die Lock-Datei waehrend des
  Betriebs niemals loeschen oder austauschen.
- Pflicht: `NETMON_STATS_TOKEN` ueber die vom Hoster vorgesehene Secret-Konfiguration
  an die tatsaechlich verwendete PHP-SAPI uebergeben; leere/ungueltige Konfiguration
  sperrt die Seite mit HTTP 503. Eine Shell-Variable allein ist kein Nachweis.
- Keine echten Tokens in `download-config.php`, Repo-`.htaccess`, Commits oder Upload-Zips speichern.
- Zugriff nur per `Authorization: Bearer` ueber HTTPS direkt auf den kanonischen
  Host; URL-Tokens werden abgelehnt. Die CGI-/FPM-Headerweitergabe und die
  Erreichbarkeit des Secrets fuer PHP muessen separat geprueft werden.
- Lokale Pruefung: `python3 scripts/check_download_stats_readiness.py --php /pfad/zu/php`.
  Sie arbeitet mit temporaeren Kopien, synthetischen Daten und einem fluechtigen
  Testtoken. Ihr Erfolg bestaetigt **keine** produktive cPanel-/Apache-/FPM-Konfiguration.
- Authentifizierungsvertrag, sichere Administration und Hosting-Checkliste:
  [docs/security/L-02.md](../docs/security/L-02.md).

Die Statistik serialisiert vor jeder Ersetzung den vollstaendigen JSON-Zustand,
schreibt ihn in eine private temporaere Datei im selben Verzeichnis und verwendet
anschliessend ein atomares Rename. Eingabe-, Serialisierungs- und I/O-Fehler
erhalten den bisherigen Zustand; der Download-Redirect bleibt verfuegbar.
Ein bereits beschaedigter oder leerer vorhandener Speicher wird nicht automatisch
ueberschrieben und muss aus einer geprueften Sicherung wiederhergestellt werden.

Sie macht:

- `301`-Redirect auf `https://netmonroots.com`
- Redirect von `www.netmonroots.com`
- Redirect von `netmon-roots.com`
- Redirect von `netmon-roots.app`
- grundlegende Security-Header

## Statisches Caddy-Beispiel

Die dokumentierte Produktionsumgebung bleibt Apache/cPanel mit PHP. Es erfolgt
keine automatische Migration. `site/Caddyfile` ist nur fuer statische Auslieferung
vorgesehen: kein PHP-FastCGI, kein Downloadzaehler, keine Statistikseite.
Caddy wertet die Apache-`.htaccess`-Dateien nicht aus. Ein Repository-Checkout
oder das PHP-`public_html` darf deshalb nicht als Caddy-Webroot dienen.

Aus einem bereits signierten und separat geprueften vollstaendigen Website-Bundle
laesst sich ohne Paketbau ein neuer statischer Dateibaum erzeugen:

```bash
python3 scripts/export_netmon_caddy_site.py \
  /pfad/zum/geprueften/public_html /tmp/netmonroots-public-neu
```

Die Quelle bleibt unveraendert. Sie muss waehrend des Exports unveraenderlich
sein; ein unvollstaendiges Release-Update-Bundle allein reicht nicht aus.
Das Ziel muss neu sein. Der Export ueberschreibt keine vorhandene Ausgabe.
Bei Fehlern kann eine unvollstaendige, ausschliesslich statische Ausgabe
zurueckbleiben; sie ist kein erfolgreicher Export und darf nicht deployt werden.

Der Export kopiert nur freigegebene Seiten, Styles, Skripte, Bilder, Dokumente,
Release-Pakete, Pruefsummen, Signaturen und Verifikationsdateien. Er folgt keinen
Symlinks in den durchlaufenen Bundle-Verzeichnissen und fuehrt PHP nicht aus.
PHP-Quellen, `.htaccess`, Konfiguration und der gesamte `data/`-Baum bleiben
ausserhalb der Ausgabe, auch wenn dort spaeter neue Dateien hinzukommen.
Die literalen Download-ID-/Zielpaare aus `download-config.php` dienen allein
zum Ersetzen der HTML-Zaehlerlinks durch dieselben oeffentlichen Ziele mit
`?dl=1`. Unbekannte IDs, nichtoeffentliche Ziele oder fehlende Artefakte brechen
ab. PHP-Ausdruecke statt der bisherigen literalen Konfiguration werden nicht
interpretiert. Weder Konfiguration noch Tokens werden in die Ausgabe kopiert.

Die statische Ausgabe hat beispielsweise diese Struktur:

```text
/srv/netmonroots/public/index.html
/srv/netmonroots/public/en/index.html
/srv/netmonroots/public/styles.css
/srv/netmonroots/public/screenshots/...
/srv/netmonroots/public/dist/netmon_<version>_all.deb
/srv/netmonroots/public/dist/SHA256SUMS
/srv/netmonroots/public/dist/SHA256SUMS.minisig
/srv/netmonroots/public/dist/docs/...
/srv/netmonroots/public/verify/...
```

Nur die erfolgreich exportierte Ausgabe manuell als `/srv/netmonroots/public`
bereitstellen, mit fuer Caddy lesbaren Rechten. Der Caddy-Benutzer braucht weder
Schreibrechte im Webroot noch Leserechte auf PHP-/Statistikdateien. Keine Links
zu privaten Dateien im Webroot anlegen; Caddys Dateiserver ist keine Sandbox.
Konfiguration und Statistik bleiben im getrennten Apache-/PHP-Betrieb bzw.
ausserhalb dieses Dateibaums. Ein blindes `cp -r public_html` ist kein Export.

Das Caddyfile erlaubt zusaetzlich nur explizite oeffentliche Pfade und GET/HEAD.
PHP-/Datenpfade erhalten 404, auch unter `/site/`; weitere Methoden werden nicht
an den Dateiserver weitergereicht. Es gibt keine Verzeichnislisten und keinen
allgemeinen `try_files`-Fallback, der verweigerte Pfade auf die Startseite umbiegt.
Startseite, `/en/` und die bisherigen `/site/...`-Aliase funktionieren.
Domain-Redirects und HTTPS-Sicherheitsheader bleiben erhalten.

Die exportierten Downloadbuttons funktionieren ohne PHP ueber die vorhandenen
`/dist/...`-, Audit- und `/verify/...`-URLs. Direkte alte Aufrufe von
`download.php` und `download-stats.php` funktionieren im statischen Modus
absichtlich nicht; sie sind keine gezaehlten Downloads oder Statistik-API.
Auf Apache bleiben Originalseiten, PHP-Code, Daten und Zaehler unveraendert.
Wer unter Caddy PHP benoetigt, braucht eine separat gepruefte FastCGI-Konfiguration;
ein pauschales Freigeben von PHP-Dateien ist kein Ersatz.

Vor einer Verwendung mit vorhandenem Caddy separat pruefen:

```bash
caddy adapt --config site/Caddyfile --adapter caddyfile --validate
python3 -m pytest -q tests/test_caddy_static_security.py
```

Die Tests kennzeichnen fehlendes Caddy/PHP als fehlende Laufzeitabnahme.
Die statische Exportpruefung ersetzt weder Caddy-Konfigurationsvalidierung noch
einen HTTPS-/Hostingtest. Es werden keine Serverdienste automatisch umgestellt.

## DNS

Vor produktivem Start:

1. `A`- oder `AAAA`-Records fuer alle drei Domains auf den Zielserver setzen.
2. Warten, bis die Domains aufloesen.
3. Im Hostingpanel pruefen, dass SSL fuer `netmonroots.com` aktiv ist.
4. Erst danach HTTPS-Redirect erzwingen.

## Server-Schritte

Beispielhaft:

```bash
NETMON_MINISIGN_SECRET_KEY=/pfad/zum/bestehenden/release.key make site-build
```

Danach kannst du entweder:

- `dist/site-build/public_html/` direkt hochladen
- oder `dist/site-build/netmonroots_public_html.zip` in cPanel entpacken

Fuer alle Produktions-Releases:

- `NETMON_MINISIGN_SECRET_KEY=/pfad/zum/seckey.txt make site-build`
- der Build verwendet den in `docs/security/netmonroots.minisign.pub` gepinnten Public Key
- ein optional gesetzter `NETMON_MINISIGN_PUBKEY` muss exakt mit dem Repository-Pin uebereinstimmen
- ohne Secret Key oder ohne `minisign` bricht der Release-Build ab
- `NETMON_ALLOW_UNSIGNED_BUILD` kann keine Signierung oder Verifikation umgehen
- `verify/RELEASE-SHA256SUMS` und `.minisig` authentifizieren alle Bundle-Dateien;
  alte Bundles ohne Vollmanifest neu bauen. Bei einem Ordner-Upload die ZIP-Pruefung
  zusaetzlich mit `--upload-directory <public_html-Ordner>` ausfuehren.
- unsignierte Testpakete ausschliesslich ueber `make unsigned-test-bundle`; sie
  liegen unter `unsigned-test-builds/`, haben keine Uploadstruktur und duerfen
  niemals veroeffentlicht werden
- vor jedem manuellen Upload die exakte ZIP mit
  `python3 scripts/verify_netmon_release_bundle.py <ZIP> --kind site` beziehungsweise
  `--kind update` pruefen; bei Fehlern abbrechen
- es gibt keinen automatisierten Publikationsjob im Repository; die lokale
  Freigabepruefung ersetzt keine serverseitige CI-Schranke
- alte Ausgaben unter `dist/.release-history/` sind kein neuer Build-Erfolg
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
