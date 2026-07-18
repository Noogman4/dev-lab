# Repository Guard V1

## Ziel

`Repository Guard` soll in NetMon einen ersten, lokalen Sicherheitscheck fuer
Paketquellen und Update-Herkunft vorbereiten. V1 ist als schlanke, gut
nachvollziehbare Ausbaustufe gedacht: lesen, strukturieren, bewerten,
anzeigen.

Nicht Ziel von V1:

- keine Paketinstallation
- keine Aenderung an Repositories
- keine Auto-Reparatur
- keine Hintergrundueberwachung
- keine Chad-Anfrage als Pflichtbestandteil

## V1 Umfang

V1 soll nur lokale, nicht-destruktive Pruefungen enthalten.

Geplante Datenquellen:

- APT Hauptdatei: `/etc/apt/sources.list`
- APT Verzeichnisse: `/etc/apt/sources.list.d/*.list`
- Deb822-Quellen: `/etc/apt/sources.list.d/*.sources`
- APT Keyring-Hinweise aus Quellenangaben, zum Beispiel `signed-by=...`
- Flatpak Remotes ueber lokale Abfrage, falls `flatpak` vorhanden ist

Bewusst nicht in V1:

- DNS-Lookups externer Repository-Domains
- Download oder Online-Verifikation von GPG-Schluesseln
- tiefe Paket-Metadatenanalyse
- Live-Monitoring mit Dateiwatchern
- automatische Trust- oder Whitelist-Pflege

## Funktionsidee fuer V1

Der Guard soll einen Snapshot der aktuell konfigurierten Paketquellen sammeln
und in drei Schritten auswerten:

1. Quellen lesen und normalisieren
2. Sicherheitsrelevante Signale ableiten
3. Ergebnis als strukturierte Findings an die GUI liefern

Optional fuer eine spaetere V1.x:

- Baseline-Datei speichern
- aktuelle Konfiguration gegen letzte bekannte Konfiguration vergleichen

## Zu erfassende Repository-Typen

### APT Legacy `.list`

Pro Eintrag sollen mindestens diese Felder extrahiert werden:

- `kind`: `apt`
- `format`: `list`
- `file_path`
- `enabled`
- `raw_line`
- `repo_type` wie `deb` oder `deb-src`
- `uri`
- `suite`
- `components`
- `options`
- `signed_by`

### APT Deb822 `.sources`

Pro Block sollen mindestens diese Felder extrahiert werden:

- `kind`: `apt`
- `format`: `deb822`
- `file_path`
- `enabled`
- `types`
- `uris`
- `suites`
- `components`
- `signed_by`
- `raw_block`

### Flatpak

Falls verfuegbar, pro Remote mindestens:

- `kind`: `flatpak`
- `name`
- `url`
- `scope` wie `system` oder `user`
- `enabled`

Falls `flatpak` nicht installiert ist, soll das kein Fehler sein, sondern ein
neutraler Hinweis.

## Geplante Findings in V1

V1 soll noch keine "harte Sicherheit" behaupten, sondern nachvollziehbare
Signale liefern.

### Finding-Typen

- `info`
- `notice`
- `warning`
- `critical`
- `error`

### Finding-Codes

V1 sollte mit festen Codes arbeiten, damit GUI und spaetere Exporte stabil
bleiben.

Empfohlene erste Codes:

- `repo_file_missing`
- `repo_file_unreadable`
- `repo_parse_error`
- `repo_disabled_entry`
- `repo_http_used`
- `repo_no_signed_by`
- `repo_duplicate_source`
- `repo_unknown_origin`
- `repo_empty_components`
- `repo_deb_src_enabled`
- `repo_flatpak_remote_present`
- `repo_flatpak_remote_untrusted_candidate`
- `repo_status_unchecked`

### Erste Bewertungslogik fuer V1

- `critical`
  - Repository-Datei kann nicht gelesen oder sinnvoll geparst werden
  - unsignierte oder offensichtlich ungueltige Struktur
- `warning`
  - `http://` statt `https://`
  - kein `signed-by` bei Drittquellen
  - unbekannte oder ungewoehnliche Drittquelle
  - doppelte oder widerspruechliche Quellen
- `notice`
  - deaktivierte Eintraege
  - `deb-src` aktiv
  - Flatpak-Remote vorhanden, aber noch nicht weiter bewertet
- `info`
  - normale Standardquelle
  - Flatpak auf System nicht vorhanden
- `error`
  - Laufzeit- oder Erfassungsfehler waehrend des Scans

Wichtig:
V1 soll keine pauschale Vertrauensbewertung aller Fremdquellen treffen.
Unbekannt bedeutet zunaechst nur "nicht im kleinen bekannten Satz enthalten".

## Bekannte Basisquellen fuer V1

V1 darf mit einer kleinen, lokalen Known-List arbeiten, nur fuer eine
vorsichtige Erstklassifikation.

Beispiel fuer bekannte, erwartbare Muster:

- `deb.debian.org`
- `security.debian.org`
- `archive.ubuntu.com`
- `security.ubuntu.com`
- `ppa.launchpadcontent.net`
- `dl.flathub.org`

Diese Liste ist nicht als Vertrauensgarantie zu verstehen, sondern nur als
Orientierung fuer `known` gegen `unknown`.

## Ergebnisstruktur fuer die GUI

Der Guard sollte spaeter ein Dictionary zurueckgeben, das stabil genug fuer
Tabellen, Statusfelder und Detailansichten ist.

Beispielstruktur:

```python
{
    "status": "warning",
    "checked_at": "2026-05-31T10:15:00Z",
    "summary": {
        "repositories_total": 8,
        "findings_total": 3,
        "critical": 0,
        "warning": 2,
        "notice": 1,
        "info": 5,
        "errors": 0,
    },
    "sources": [
        {
            "id": "apt:/etc/apt/sources.list:12",
            "kind": "apt",
            "format": "list",
            "file_path": "/etc/apt/sources.list",
            "enabled": True,
            "uri": "https://deb.debian.org/debian",
            "suite": "bookworm",
            "components": ["main"],
            "signed_by": "",
            "origin_class": "known",
        }
    ],
    "findings": [
        {
            "id": "finding-1",
            "severity": "warning",
            "code": "repo_no_signed_by",
            "title": "Quelle ohne signed-by-Hinweis",
            "summary": "Drittquelle nutzt keinen expliziten Keyring-Hinweis.",
            "source_id": "apt:/etc/apt/sources.list.d/example.list:3",
            "details": {
                "uri": "https://example.invalid/repo",
                "file_path": "/etc/apt/sources.list.d/example.list",
            },
        }
    ],
    "errors": [],
}
```

## Statusmodell fuer den Tab

Empfohlene Statuswerte:

- `unchecked`
- `ok`
- `notice`
- `warning`
- `critical`
- `error`

Interpretation:

- `unchecked`: noch kein Scan gelaufen
- `ok`: keine relevanten Findings
- `notice`: nur informative oder leichte Hinweise
- `warning`: sichtbare Risiken oder Auffaelligkeiten
- `critical`: schwere Struktur- oder Signaturprobleme
- `error`: Scan technisch fehlgeschlagen

## Empfohlene Modulstruktur

Wenn wir V1 implementieren, sollte sie sich an den vorhandenen Guard-Bausteinen
orientieren.

Vorschlag:

- `netmon/services/repository_guard_service.py`
- `netmon/features/repository_guard_controller.py`

Service-Aufgaben:

- lokale Quellen lesen
- Daten normalisieren
- Findings erzeugen
- Ergebnisobjekt zurueckgeben

Controller-Aufgaben:

- Button-Aktion ausloesen
- GUI-Status setzen
- Tabellen und Detailansicht fuellen
- Fehler sauber ins Log schreiben

## GUI-Ziel fuer V1

Der bereits vorbereitete Tab soll in V1 folgende echten Inhalte bekommen:

- Statuszeile mit `Nicht geprueft`, `OK`, `Warnungen`, `Fehler`
- Tabelle oder Liste der gefundenen Quellen
- Tabelle oder Liste der Findings
- Detailbereich fuer den markierten Eintrag
- Button `Repository Scan`

Noch nicht fuer V1 noetig:

- Editieren von Quellen
- Trust-Management
- Auto-Fix
- Live-Refresh

## Testfaelle fuer die spaetere Implementierung

Mindestens diese Faelle sollten wir spaeter mit `pytest` abdecken:

- leere oder fehlende `sources.list`
- gueltige `deb`-Zeile
- auskommentierte Zeile
- Zeile mit `http://`
- Zeile mit `signed-by=...`
- doppelte Quelle in zwei Dateien
- Deb822-Quelle mit mehreren `URIs`
- Flatpak nicht installiert
- Flatpak mit einem Standard-Remote
- Parserfehler in defekter Quelldatei

## Empfehlung fuer den naechsten Implementierungsschritt

Nach dieser V1-Spezifikation ist der beste naechste Schritt:

1. `repository_guard_service.py` als reine Leselogik anlegen
2. Parser zuerst nur fuer APT `.list` bauen
3. Rueckgabeformat auf das obige Ergebnisobjekt festlegen
4. danach Deb822 und Flatpak ergaenzen
5. erst zum Schluss die GUI mit echten Daten verbinden
