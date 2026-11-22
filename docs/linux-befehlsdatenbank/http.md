---
id: "http"
name: "http"
command: "http"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "http", "api", "httpie"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 157
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert (Paket httpie fehlt); nicht praktisch geprüft"
---

# http – HTTP-Anfragen mit HTTPie lesbar senden

## 1. Kurzbeschreibung

`http` ist der Hauptbefehl von **HTTPie**, einem HTTP-Client für die Kommandozeile, der vor allem auf **Web-APIs** zugeschnitten ist. Er bietet eine kurze Schreibweise für Header, URL-Parameter und JSON-Daten und gibt Antworten farbig und formatiert aus. Zum Paket gehört auch `https`, das als Vorgabe `https://` verwendet.

**Root-Rechte sind nicht nötig.**

Grundlage ist die [Debian-Manpage zu http](https://manpages.debian.org/trixie/httpie/http.1.en.html) (HTTPie 3.2.4) und die [HTTPie-Dokumentation](https://httpie.io/docs/cli/main-features). Auf dem geprüften System ist HTTPie nicht installiert.

**Namensabgrenzung:** Der Datensatz `http` meint hier den Befehl aus HTTPie. Das Verwaltungsprogramm `httpie` aus demselben Paket ist ein eigener Eintrag (Datensatz 158).

## 2. Was macht der Befehl?

`http [METHODE] URL [ELEMENTE ...]` baut eine HTTP-Anfrage zusammen und sendet sie. Laut Manpage gilt:

- **Methode automatisch:** Ohne Daten `GET`, mit Datenfeldern `POST`.
- **Schema:** Ohne Angabe `http://`; `:3000` ist eine Kurzform für `http://localhost:3000`.
- **JSON als Vorgabe:** Datenfelder werden als JSON-Objekt gesendet; `Content-Type` und `Accept` stehen auf `application/json`.

Die Bedeutung eines Elements ergibt sich aus dem Trennzeichen:

| Trennzeichen | Bedeutung | Beispiel |
| --- | --- | --- |
| `:` | HTTP-Header | `User-Agent:test/1.0` |
| `==` | URL-Parameter | `suche==httpie` |
| `=` | Datenfeld (Text) | `name=Anna` |
| `:=` | Datenfeld als JSON-Wert | `anzahl:=42`, `aktiv:=true` |
| `@` | Datei als Formularfeld (mit `--form`) | `datei@bericht.pdf` |
| `=@` | Dateiinhalt als Textfeld | `text=@notiz.txt` |
| `:=@` | Dateiinhalt als JSON-Wert | `daten:=@werte.json` |

Laut Dokumentation endet `http` ohne weitere Optionen mit `0`, solange kein Netzwerk- oder anderer schwerer Fehler auftritt – auch bei HTTP-Fehlern wie 404.

## 3. Syntax

```text
http [OPTIONEN] [METHODE] URL [ELEMENT ...]
https [OPTIONEN] [METHODE] URL [ELEMENT ...]
```

```bash
http example.org
http --offline POST api.example.org/nutzer name=Anna alter:=30
https api.example.org/suche q==linux Authorization:'Bearer TOKEN'
http --download example.org/datei.zip
```

Das bisherige NetMon-Beispiel `http --help` ist gültig (`--help` laut Manpage). Der Platzhalter `http [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--offline` | Anfrage nur aufbauen und anzeigen, nicht senden. | Ideal zum Üben und Prüfen. |
| `-j`, `--json` | Daten als JSON (Vorgabe). | – |
| `-f`, `--form` | Daten als Formular. | Mit Dateien: multipart. |
| `-v`, `--verbose` | Anfrage und Antwort ausgeben. | – |
| `-h`, `--headers` / `-b`, `--body` | Nur Header bzw. nur Inhalt der Antwort. | Achtung: `-h` ist hier **nicht** die Hilfe. |
| `-p`, `--print=WAS` | Ausgabeteile wählen (`H`, `B`, `h`, `b`). | – |
| `-o`, `--output DATEI` | Ausgabe in Datei. | – |
| `-d`, `--download` | Inhalt wie `wget` in Datei speichern. | Schließt `--check-status` ein. |
| `-F`, `--follow` | Weiterleitungen folgen. | – |
| `-a`, `--auth BENUTZER[:PASSWORT]` | Anmeldung. | Ohne Passwort fragt HTTPie nach. |
| `--session NAME` | Header, Anmeldung und Cookies zwischen Aufrufen speichern. | Ablage unter `~/.config/httpie/sessions/`. |
| `--check-status` | Bei 3xx/4xx/5xx mit Fehler beenden. | Rückgabewerte 3, 4, 5. |
| `--timeout SEKUNDEN` | Wartezeit auf Antwort (Vorgabe: unbegrenzt). | – |
| `--verify no` | Zertifikatsprüfung abschalten. | Nur in Ausnahmefällen. |
| `-I`, `--ignore-stdin` | Standardeingabe nicht lesen. | Für Skripte empfohlen. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine JSON-Anfrage zusammenstellen und kontrollieren, ohne sie zu senden. Voraussetzung: HTTPie installiert. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Anfrage offline ansehen

```bash
http --offline POST api.example.org/nutzer name=Anna alter:=30 X-Test:1
```

Die Ausgabe zeigt die vollständige Anfrage: Methode, Pfad, Header (inklusive `Content-Type: application/json` und `X-Test: 1`) und den JSON-Körper `{"name": "Anna", "alter": 30}`.

### Schritt 2: Mit Statusprüfung senden

```bash
http --check-status --ignore-stdin --timeout=5 api.example.org/status
echo $?
```

Laut Dokumentation bedeutet `0` Erfolg, `2` Zeitüberschreitung, `3`/`4`/`5` eine Antwort mit 3xx/4xx/5xx.

## 6. Typische Anwendungsfälle

- **REST-APIs testen** mit lesbarer Ausgabe.
- **Anfragen dokumentieren:** `--offline` zeigt genau, was gesendet würde.
- **Anmeldung über Sitzungen** wiederverwenden.
- **Dateien laden** mit `--download`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ gilt nur für `GET`-Abrufe. Der Kopf verwendet `caution`:

- **Automatisch POST:** Sobald ein Datenfeld (`name=wert`) angegeben ist, sendet HTTPie `POST` – auch wenn man nur etwas abfragen wollte. Für URL-Parameter `==` verwenden.
- **Verändernde Methoden:** `PUT`, `PATCH`, `DELETE` verändern Daten auf dem Server.
- **Zugangsdaten:** Tokens in Headern oder `-a name:passwort` stehen im Shell-Verlauf. Sitzungsdateien speichern Anmeldedaten und Cookies im Klartext.
- **Standardeingabe:** In Skripten liest HTTPie ohne `--ignore-stdin` möglicherweise unerwartet Daten aus der Pipe als Anfragekörper.
- **`--verify no`** schaltet den Schutz von HTTPS ab.
- **Rückgabewert 0 bei HTTP-Fehlern** ohne `--check-status`.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `http: command not found` | HTTPie nicht installiert. | Paket `httpie`. |
| Unerwartet `POST` | Datenfeld mit `=` statt Parameter mit `==`. | Trennzeichen prüfen. |
| Zahl kommt als Text an | `=` statt `:=`. | `:=` für Zahlen, Wahrheitswerte, Listen. |
| `-h` zeigt keine Hilfe | `-h` bedeutet „nur Header“. | `--help` verwenden. |
| Skript hängt | Wartet auf Standardeingabe oder ohne Zeitlimit. | `--ignore-stdin`, `--timeout`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `--offline` üben.**
2. **`==` für Abfrageparameter,** damit kein unbeabsichtigtes `POST` entsteht.
3. **In Skripten `--check-status --ignore-stdin --timeout`.**
4. **Keine Tokens in die Befehlszeile;** Sitzungsdateien schützen.

### Prüfstand

- **Geprüfte Version:** keine; HTTPie ist nicht installiert. Die Debian-Manpage beschreibt 3.2.4.
- **Quellen gelesen** (Abruf 2026-11-13): Debian-Manpages `http(1)` und `httpie(1)`, HTTPie-Dokumentation (Rückgabewerte bei `--check-status`, Sitzungsablage).
- **Nicht geprüft:** alle Anfragen, Ausgabeformat, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `https` | Gleicher Befehl mit Vorgabe `https://`. |
| `httpie` | Verwaltung von Plugins und Sitzungen. |
| `curl` | Universeller Client mit mehr Protokollen. |
| `wget` | Downloads und Spiegeln. |
| `jq` | JSON weiterverarbeiten. |

Ausgangseintrag: Datensatz 157 in `index.json` (`http`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Element-Syntax, die automatische Methodenwahl, Optionen, Rückgabewerte und einen Offline-Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben, weil Datenfelder automatisch zu `POST`-Anfragen führen.
