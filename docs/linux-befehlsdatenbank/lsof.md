---
id: "lsof"
name: "lsof"
command: "lsof"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "lsof"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 493
reviewed_at: "2026-11-13"
locally_checked_version: "lsof 4.95.0"
---

# lsof – Eigene PID und eigenen Dateideskriptor gemeinsam auswählen

## 1. Kurzbeschreibung

lsof zeigt offene Dateireferenzen einschließlich Sockets, Verzeichnissen und Mappings. Mehrere Auswahlarten werden oft mit ODER verknüpft; -a fordert deren UND-Verknüpfung an.

## 2. Was macht der Befehl?

Eine Datei kann nach dem Löschen ihres Namens noch offen sein. Ein offener Deskriptor beweist umgekehrt keine aktuelle I/O-Aktivität oder Sperre. Rechte und Namensräume begrenzen die Sicht. Für Parser ist -F geeigneter als feste Spaltenpositionen; Feldkennungen sind Teil der Ausgabe.

Quelle, am 2026-11-13 gelesen: [lsof-Projekt: Manpage](https://man7.org/linux/man-pages/man8/lsof.8.html) und lokale Versionsausgabe

## 3. Syntax

```text
lsof [OPTIONEN] [PFAD...]
lsof -a -p PID -d DESKRIPTOR -F FELDER
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p PID` | PID-Auswahl. |
| `-d NUMMER` | Dateideskriptorauswahl. |
| `-a` | Verschiedene Auswahlmengen verunden. |
| `-F fn` | Deskriptornummer und Namen mit Feldkennungen ausgeben. |
| `-n`, `-P` | Host-/Portnamenauflösung vermeiden. |
| `+D VERZEICHNIS` | Rekursive Suche kann teuer sein und blockierende Dateisystemzugriffe auslösen. |
| `+L1` | Referenzen mit Linkanzahl unter eins auswählen; keine Löschaktion. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-lsof-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'eigene Datei\n' > testdatei
exec 9< testdatei
lsof -nP -a -p "$$" -d 9 -F fn > bericht.txt
cat bericht.txt
rg -F "n$uebung/testdatei" bericht.txt
exec 9<&-
```

### Schritt 3: Ergebnis einordnen

Nur die eigene Test-Shell und Deskriptor 9 werden gemeinsam ausgewählt. f9 kennzeichnet den Deskriptor; das n-Feld muss den eigenen absoluten Dateipfad enthalten. Danach wird nur dieser eigene Deskriptor geschlossen. Es wurden keine fremden offenen Dateien inventarisiert. lsof meldete jedoch fehlgeschlagene stat-Abfragen für /dev/hugepages und /dev/mqueue sowie eine mögliche unvollständige Sicht. Der eigene Deskriptor wurde trotzdem mit Status 0 gefunden; die Warnungen sind kein Nachweis uneingeschränkter Systemerfassung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Offene Dateien verstehen:** Prozess, Deskriptor und Pfad zuordnen. **Diagnose eingrenzen:** Auswahllogik vor breiten Abfragen prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte können vertrauliche Pfade, Adressen und Prozessdaten enthalten. Eine leere Liste ist bei eingeschränkter Sicht kein universeller Freigabenachweis. Keine rekursiven Fremdpfade, Signale oder Netzsockets als Prüfziel. Die von lsof selbst versuchten Dateisystem-Metadatenabfragen erzeugten die genannten Sandboxwarnungen; kein Gerät wurde geöffnet oder verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zu viele Treffer | Fehlendes -a kann ODER statt UND bedeuten. |
| Pfad mit deleted | Offene Referenz und vorhandener Name unterscheiden. |
| Kein Treffer | Prozessende, Rechte oder falscher Deskriptor möglich. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** lsof 4.95.0. Praktisch geprüft: Eigene Shell und eigener offener Deskriptor 9 mit UND-Auswahl geprüft. Keine fremden Dateien/Prozesse. Netzsockets, rekursive Pfade, gelöschte Dateien und Rechtefälle praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fuser` | Dateibezogene Prozesszuordnung. |
| `ss` | Socketansicht. |
| `stat` | Dateimetadaten ohne Prozessreferenzliste. |

Ausgangsdatensatz 493 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
