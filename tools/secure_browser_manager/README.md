# Firefox Browser Container Builder

Dieses Repo enthaelt ein vorsichtiges Python-Werkzeug, das bestehende
Firefox-Standalone-Installationen unter `/home/happy/Programme` erkennt,
dokumentiert und neue getrennte Container vorbereitet.

## Sicherheitsregeln

- Standardmodus ist immer Dry-Run.
- Echte Aenderungen passieren nur mit `--apply`.
- Vor `--apply` wird zuerst der komplette Plan angezeigt.
- Vor echten Aenderungen wird ein Backup unter
  `/home/happy/Programme/browser-container-builder-backups/<timestamp>/` angelegt.
- Bestehende Zielordner fuehren zum Abbruch.
- Es werden keine bestehenden Ordner geloescht oder ueberschrieben.
- Es werden keine Schreibzugriffe nach `~/.mozilla/firefox` oder
  `~/.config/mozilla/firefox` ausgefuehrt.
- Es werden keine `sudo`-Befehle verwendet.

## Dateien

- `browser_container_builder.py`
- `containers.json`
- `container_inventory.md` wird beim Lauf erzeugt

## Erkennung vorhandener Container

Gesucht werden unterhalb des Basisverzeichnisses:

- `firefox/firefox` Binaries
- `start.sh`
- Profilordner
- `.desktop` Dateien
- `user.js`
- `policies.json`

Die Inventardatei `container_inventory.md` enthaelt:

- Containername
- Pfad zur Binary
- Firefox-Version
- Profilpfad
- Startbefehl
- erkannte Domains oder Zweck
- Risiko-Hinweise

## Neue Container

Die Beispielkonfiguration legt diese Container an:

- `firefox-GitHub`
- `firefox-OpenAI`
- `firefox-NameCom`
- `firefox-cPanel`

Jeder neue Container enthaelt:

- `firefox/`
- `profile/`
- `start.sh`
- `backup.sh`
- `README.md`
- `user.js`
- `policies.json`
- `launcher.desktop`

Zusaetzlich wird beim Erstellen mit `--apply` ein Startmenue-Eintrag unter
`~/.local/share/applications/` angelegt. Der Dateiname folgt dem Schema
`netmon-secure-browser-<containername-klein>.desktop`. Bestehende
Menueeintraege werden vor dem Ueberschreiben erst unter
`~/.local/share/applications/browser-container-builder-backups/` gesichert.

Standardstart:

```bash
./firefox/firefox --no-remote --profile ./profile
```

Startseiten fuer neue Container werden ueber die Konfiguration gesetzt.
Beispiel: `firefox-GitHub` startet mit `https://github.com`, neue Tabs mit
`about:blank`.

## Hardening

Das generierte `user.js` und `policies.json` setzen unter anderem:

- Telemetrie aus
- Pocket aus
- Firefox Studies aus
- Formularvorschlaege aus
- Drittanbieter-Cookies blockieren
- Cookies beim Beenden loeschen
- WebRTC deaktiviert
- DNS over HTTPS deaktiviert
- Firefox Sync deaktiviert
- Profilimport deaktiviert

Zusaetzlich nutzt `policies.json` den Firefox-Enterprise-Mechanismus
`WebsiteFilter`, um standardmaessig alle Seiten zu blockieren und nur die
konfigurierten Ausnahmen zu erlauben. Port-genaue Freigaben wie
`netmonroots.com:2083` lassen sich damit nicht exakt nach Port modellieren; der
Builder dokumentiert dieses Risiko in den generierten Container-README-Dateien.

## Nutzung

Dry-Run:

```bash
python3 browser_container_builder.py
```

Mit eigener Konfiguration:

```bash
python3 browser_container_builder.py --config containers.json
```

Echte Erstellung:

```bash
python3 browser_container_builder.py --apply
```

## Voraussetzungen

- Python 3.11+
- vorhandenes Firefox-Quellverzeichnis fuer neue Container, z. B.
  `/home/happy/Programme/firefox-base/firefox`

Wenn `default_source_firefox_dir` nicht gesetzt ist, versucht der Builder genau
eine vorhandene standalone Firefox-Quelle aus dem Scan zu uebernehmen. Bei
mehrdeutigen Funden bricht `--apply` ab.
