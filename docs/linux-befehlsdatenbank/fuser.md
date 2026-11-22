---
id: "fuser"
name: "fuser"
command: "fuser"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "fuser"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 484
reviewed_at: "2026-11-13"
locally_checked_version: "fuser / PSmisc 23.7"
---

# fuser – Zugriff auf eine eigene geöffnete Datei anzeigen

## 1. Kurzbeschreibung

fuser ordnet Dateien oder ausgewählten Socketnamensräumen zugreifende Prozesse zu. Ohne -k wird angezeigt; -k sendet standardmäßig SIGKILL. Die Operationsoption ist deshalb entscheidend.

## 2. Was macht der Befehl?

Eine Dateireferenz kann offener Deskriptor, Arbeitsverzeichnis, ausgeführte Datei oder Mapping sein. Rechte und Namensräume begrenzen die Sicht. PIDs gehen nach stdout, zusätzliche Informationen nach stderr. Die eigene Übung hält nur eine frisch erzeugte Datei über Deskriptor 9 offen.

Quelle, am 2026-11-13 gelesen: [psmisc: fuser-Handbuch](https://man7.org/linux/man-pages/man1/fuser.1.html)

## 3. Syntax

```text
fuser [ANZEIGEOPTIONEN] DATEI...
fuser -n {tcp|udp} PORT
fuser -k [SIGNALOPTION] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-v` | Ausführliche Zugriffsarten. |
| `-s` | Stille Abfrage über Status. |
| `-n tcp`, `-n udp` | Socketnamensraum statt Datei. |
| `-m` | Gesamtes Dateisystem auswählen; sehr großer Wirkbereich. |
| `-M` | Bei Mountmodus echten Mountpoint verlangen; keine allgemeine Isolation. |
| `-k` | Signale senden, standardmäßig SIGKILL. |
| `-i` | Nur mit -k eine Rückfrage, kein eigener Schutzmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-fuser-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'eigene Datei\n' > testdatei
exec 9< testdatei
fuser "$uebung/testdatei" > pids.txt
cat pids.txt
tr ' ' '\n' < pids.txt | rg -x "$$"
exec 9<&-
```

### Schritt 3: Ergebnis einordnen

Die eigene Shell-PID muss in der Ausgabe vorkommen. Danach wird nur der eigene Deskriptor geschlossen. Weitere geerbte Deskriptoren können zusätzliche eigene Prozess-PIDs erklären. Es wird kein Signal gesendet. Die Sandbox meldete bereits beim Versionsaufruf eine nicht verfügbare Netzsocketfunktion; das ist vom Dateibeispiel getrennt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Dateizugriffe verstehen:** Einen eigenen offenen Deskriptor zuordnen. **Diagnose planen:** Fehlenden Treffer nicht als universelle Freigabe für Löschen oder Unmount deuten.

## 7. Risiken, Nebenwirkungen und Vorsicht

-km auf einem breiten Pfad kann viele Prozesse abrupt beenden. Nie pauschal zum Freimachen eines Dateisystems verwenden. Keine fremden Dateien, Mounts oder Sockets geprüft und kein Prozess beendet. Rechte nicht für vollständigere Anzeige erweitern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Treffer | Rechte, Namensraum und Zeitpunkt prüfen. |
| Status ungleich 0 | Kein Zugriff oder Fehler; stderr mitlesen. |
| Unerwartet viele Treffer mit -m | Dateisystemweite Auswahl statt einzelner Datei. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** fuser / PSmisc 23.7. Praktisch geprüft: Eigene geöffnete Datei abgefragt und Shell-PID geprüft; keine Signale. Sandbox-Netzsocketwarnung beobachtet. Fremdprozesssicht, Socket-/Mountmodus und Signalfunktionen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lsof` | Andere Sicht auf offene Dateien. |
| `ss` | Socketbezogene Anzeige. |
| `kill` | Explizites Signal statt automatischer Dateiauswahl. |

Ausgangsdatensatz 484 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
