---
id: "source"
name: "source"
command: "source"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "source"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 558
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# source – Geprüften Shellcode im gleichen Prozess laden

## 1. Kurzbeschreibung

source ist in Bash ein Synonym für das Punkt-Builtin .

## 2. Was macht der Befehl?

Die eingelesene Datei läuft im aktuellen Kontext; Zuweisungen und Funktionen bleiben dort erhalten. source ist keine universelle POSIX-Schreibweise. Mit einem expliziten ./-Pfad wird die Auswahl gegenüber einer Namenssuche eindeutiger. Ein Dateiname mit .env ist dadurch noch kein passives Datenformat. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help source`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
source DATEI [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| DATEI | Vollständig ausgeführter Shelltext. |
| ARGUMENTE | Positionsparameter während des Einlesens. |
| Rückgabestatus | Status des zuletzt ausgeführten Dateibefehls. |
| ./DATEI | Explizit ausgewählte Datei. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
printf 'lesson_source=geladen
' > own-source.sh
source ./own-source.sh
test "$lesson_source" = geladen
printf 'Eigene Quelldatei geladen\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Eine bekannte selbst erstellte Zuweisung wird eingelesen. Die sichtbare Variable belegt den gemeinsamen Kontext und keinen Kindprozessimport. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene geprüfte Funktionen einbinden; Aktivierungsskripte verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Konfiguration nicht mit source parsen. Der Dateitext kann Befehle, Umleitungen und Zustandsänderungen enthalten. Nur eigene Datei und neue Shell verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unter sh unbekannt | Dort bei passender Sprache . verwenden. |
| Variablen ändern sich unerwartet | Datei wird ausgeführt und besitzt Shellrechte. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| . | Bash-Synonym, portablere Schreibweise. |
| bash | Neuer Prozess als anderer Ausführungsmodus. |
| export | Umgebungsvererbung. |

Ausgangsdatensatz 558 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
