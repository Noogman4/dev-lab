---
id: "curl"
name: "curl"
command: "curl"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "http", "download", "api"]
status: "Ausgearbeitet; Quellen geprüft; nur lokale file://-Abrufe praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 152
reviewed_at: "2026-11-13"
locally_checked_version: "curl 8.5.0 (Ubuntu-Paket 8.5.0-2ubuntu10.16)"
---

# curl – Daten über URLs abrufen und senden

## 1. Kurzbeschreibung

`curl` überträgt Daten von oder zu einem Server, angegeben als **URL**. Es unterstützt viele Protokolle, vor allem HTTP und HTTPS, aber auch FTP, SFTP, SCP und lokale Dateien (`file://`). Typische Aufgaben: eine Webseite oder Datei abrufen, HTTP-Header prüfen, eine Web-API aufrufen, Daten an einen Server senden.

**Root-Rechte sind nicht nötig.** Du brauchst Netzwerkzugang und – beim Speichern – Schreibrechte im Zielordner.

Grundlage ist die [Debian-Manpage zu curl](https://manpages.debian.org/trixie/curl/curl.1.en.html) (curl 8.14.1). Lokal installiert ist curl 8.5.0; Unterschiede sind unten vermerkt.

## 2. Was macht der Befehl?

Ohne weitere Optionen gibt `curl URL` den Inhalt der Antwort auf der **Standardausgabe** aus – im Terminal also direkt sichtbar. Gespeichert wird nur mit `-o` oder `-O`.

Wichtige Grundregeln laut Manpage:

- **Weiterleitungen** (HTTP 3xx) folgt `curl` nur mit `-L`.
- **HTTP-Fehler** (ab 400) sind ohne `-f` kein Fehler: `curl` gibt die Fehlerseite aus und endet mit `0`. Mit `-f` endet es mit Rückgabewert `22` ohne Ausgabe.
- **Zertifikate** werden bei HTTPS immer geprüft, außer mit `-k`.
- **Daten senden:** `-d` sendet einen POST mit Formularkodierung; `-X` ändert die HTTP-Methode ohne Prüfung.

Laut Manpage hängt `curl` dabei nichts selbst an die übergebene Methode oder Daten an; was du angibst, wird gesendet.

## 3. Syntax

```text
curl [OPTIONEN] URL ...
```

```bash
curl https://example.org/
curl -fsSL -o datei.tar.gz https://example.org/datei.tar.gz
curl -I https://example.org/
curl -fsS -H 'Accept: application/json' https://api.example.org/status
```

Das bisherige NetMon-Beispiel `curl --help` zeigt nur eine kurze Auswahl. Die vollständige Liste liefert `curl --help all`. Der Platzhalter `curl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-o DATEI`, `--output` | In Datei schreiben. | Überschreibt vorhandene Dateien ohne Rückfrage. |
| `-O`, `--remote-name` | Unter dem Namen aus der URL speichern. | Im aktuellen Ordner oder mit `--output-dir`. |
| `-L`, `--location` | Weiterleitungen folgen. | – |
| `-f`, `--fail` | Bei HTTP-Fehlern ab 400 mit Code 22 abbrechen. | Für Skripte wichtig. |
| `--fail-with-body` | Wie `-f`, aber Fehlerseite ausgeben. | – |
| `-s`, `-S` | Fortschritt ausblenden bzw. Fehler trotzdem zeigen. | Üblich: `-sS`. |
| `-I`, `--head` | Nur Header abrufen. | – |
| `-i`, `--include` | Header mit ausgeben. | Neuere Versionen nennen die Option `--show-headers`. |
| `-H 'Name: Wert'` | Eigenen Header senden. | – |
| `-d DATEN`, `--data` | POST mit Formularkodierung. | – |
| `-X METHODE` | HTTP-Methode setzen. | Wird ungeprüft übernommen. |
| `-u BENUTZER[:PASSWORT]` | Anmeldung. | Ohne Passwort fragt `curl` danach. |
| `-C OFFSET`, `-C -` | Übertragung fortsetzen. | Mit `-C -` ermittelt `curl` laut Manpage selbst, wo fortgesetzt wird. |
| `-m SEKUNDEN`, `--max-time` | Zeitlimit für die Übertragung. | Verhindert hängende Skripte. |
| `--retry N` | Bei vorübergehenden Fehlern wiederholen. | Vorgabe 0. |
| `-x PROXY` | Proxy verwenden. | Auch SOCKS. |
| `-k`, `--insecure` | Zertifikatsprüfung abschalten. | Nur in Ausnahmefällen. |
| `-w FORMAT` | Werte nach der Übertragung ausgeben. | Etwa `%{http_code}`. |
| `--proto =https` | Nur bestimmte Protokolle zulassen. | Schutz bei Weiterleitungen. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Umgang mit Ausgabe, Speichern und Fehlern an einer eigenen lokalen Datei üben – ganz ohne Netzwerk. `curl` kann dafür `file://`-URLs lesen.

### Schritt 1: Übungsdatei

```bash
uebung="$(mktemp -d -t netmon-curl-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'Hallo curl\n' > quelle.txt
```

### Schritt 2: Ausgabe ins Terminal

```bash
curl -sS "file://$PWD/quelle.txt"
```

Ausgabe: `Hallo curl`. Nichts wird gespeichert.

### Schritt 3: In Datei speichern und vergleichen

```bash
curl -sS -o kopie.txt "file://$PWD/quelle.txt"
cmp quelle.txt kopie.txt && echo gleich
```

### Schritt 4: Metadaten und Messwerte

```bash
curl -sS -I "file://$PWD/quelle.txt"
curl -sS -w '%{size_download}\n' -o /dev/null "file://$PWD/quelle.txt"
```

Bei `file://` zeigt `-I` unter anderem `Content-Length: 11`; `-w` gibt die übertragene Größe `11` aus.

### Schritt 5: Fehlerfall

```bash
curl -sS "file://$PWD/fehlt.txt"
echo $?
```

`curl` meldet `curl: (37) Couldn't open file ...` und endet mit `37`.

### Übertragung auf HTTP (nicht ausgeführt)

Für Webadressen gilt dasselbe Muster, ergänzt um `-f` und `-L`: `curl -fsSL -o datei https://example.org/datei`.

## 6. Typische Anwendungsfälle

- **Dateien laden:** `curl -fsSLO URL`.
- **Erreichbarkeit und Header prüfen:** `curl -sSI URL`.
- **APIs aufrufen:** `curl -fsS -H 'Authorization: ...' URL`.
- **Statuscode in Skripten:** `curl -s -o /dev/null -w '%{http_code}' URL`.
- **Fehlersuche mit TLS:** `curl -v URL` zeigt den Verbindungsaufbau.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft auf einfache Abrufe zu, nicht auf alle Funktionen. Der Kopf verwendet `caution`:

- **`curl ... | sh` oder `| sudo bash`** führt ungeprüften Code aus dem Netz aus. Skripte erst speichern und lesen.
- **Überschreiben:** `-o` und `-O` ersetzen vorhandene Dateien ohne Rückfrage.
- **Daten senden:** `-d`, `-F`, `-T` und `-X` verändern Daten auf Servern (POST, PUT, DELETE).
- **Zugangsdaten:** `-u name:passwort` oder Tokens in `-H` stehen in Shell-Verlauf und Prozessliste. Besser eine Konfigurationsdatei (`-K`) oder `--netrc-file` mit passenden Dateirechten.
- **`-k`, `--insecure`** überspringt bei HTTPS die Prüfung des Serverzertifikats und Hostnamens. TLS verschlüsselt weiterhin, bestätigt aber nicht mehr zuverlässig die Identität der Gegenstelle; ein Angreifer dazwischen kann dadurch Daten mitlesen oder verändern. Siehe die [curl-Dokumentation zur Zertifikatsprüfung](https://curl.se/docs/sslcerts.html).
- **Weiterleitungen mit `-L`** können auf andere Protokolle oder Hosts führen; `--proto` und `--proto-redir` begrenzen das.
- **Datenmengen:** Ohne `--max-filesize` oder `-m` kann ein Download sehr groß werden. **Prüfpunkt:** `--max-filesize` nicht im Einzelnen gelesen.

## 8. Häufige Fehler

| Rückgabewert und Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `(1) Protocol ... not supported or disabled` | Protokoll nicht erlaubt, etwa durch `--proto`. | Protokoll oder Einschränkung prüfen. |
| `(3) URL rejected` | Fehlerhafte URL. | URL in Anführungszeichen setzen und prüfen. |
| `(6) Could not resolve host` | DNS-Auflösung fehlgeschlagen. | Namen und DNS prüfen. |
| `(7) Failed to connect` | Server nicht erreichbar oder Port geschlossen. | Erreichbarkeit prüfen. |
| `(22)` | HTTP-Fehler ab 400 mit `-f`. | `-v` oder `--fail-with-body` zur Diagnose. |
| `(28)` | Zeitüberschreitung. | `-m` erhöhen, Netz prüfen. |
| `(35)`, `(60)` | TLS- bzw. Zertifikatsproblem. | Systemzeit, Zertifizierungsstellen prüfen; nicht reflexartig `-k`. |
| `(37)` | Lokale Datei nicht lesbar. | Pfad prüfen. |

Die Bedeutungen stammen aus dem Abschnitt EXIT CODES der Manpage. Lokal ausgelöst wurden die Codes `1`, `3` und `37`; die Meldungstexte der übrigen sind sinngemäß.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für Downloads `-fsSL -o DATEI`** verwenden.
2. **URLs immer in Anführungszeichen,** weil `&` und `?` sonst von der Shell gedeutet werden.
3. **Skripte nicht direkt in eine Shell leiten.**
4. **Keine Passwörter in der Befehlszeile.**
5. **In Skripten `-m` und `--retry`** setzen.

### Prüfstand

- **Geprüfte Version:** curl 8.5.0 (Ubuntu 24.04-Basis); Manpage aus Debian trixie (8.14.1).
- **Tatsächlich ausgeführt** im Testordner, nur mit `file://`: Ausgabe, `-o` mit Bytevergleich, `-I`, `-w '%{size_download}'`, `-O` mit `--output-dir` und `--create-dirs`, fehlende Datei (Rückgabe 37), `--proto =https` gegen `file://` (Rückgabe 1), leere HTTP-URL (Rückgabe 3).
- **Nicht geprüft:** jede Netzwerkanfrage (HTTP, HTTPS, FTP), Weiterleitungen, Anmeldung, Fortsetzen, Proxys.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `wget` | Downloads und rekursives Spiegeln. |
| `http` (HTTPie) | Komfortabler HTTP-Client für APIs. |
| `aria2c` | Downloads über mehrere Verbindungen. |
| `openssl s_client` | TLS-Verbindungen im Detail prüfen. |
| `jq` | JSON-Antworten auswerten. |

Ausgangseintrag: Datensatz 152 in `index.json` (`curl`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Grundregeln (Ausgabe, Weiterleitungen, Fehlerbehandlung), Optionen, Sicherheitshinweise und einen lokal geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben, weil `curl` auch Daten senden, Dateien überschreiben und Code-Downloads ermöglichen kann.
