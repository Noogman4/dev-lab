---
id: "exec"
name: "exec"
command: "exec"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "exec"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 542
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# exec – Die aktuelle Shell durch einen Befehl ersetzen

## 1. Kurzbeschreibung

exec ersetzt mit einem Programmargument die aktuelle Shell; ohne Programm verändert es deren Umleitungen.

## 2. Was macht der Befehl?

Bei erfolgreichem Prozessersatz kehrt die Ausführung nicht zu den nachfolgenden Shellzeilen zurück. Der bestehende Prozess führt das neue Programm aus. Ein bloßes exec > DATEI hält dagegen die Shell am Leben und ändert ihre Ausgabeziele. Beide Varianten sind von einem normalen Kindprozessstart zu unterscheiden. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help exec`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
exec [OPTIONEN] [BEFEHL [ARGUMENTE]] [UMLEITUNGEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c | Leere Umgebung für das neue Programm. |
| -a NAME | argv[0] für das Zielprogramm setzen. |
| ohne BEFEHL | Nur Umleitungen im aktuellen Shellprozess anwenden. |
| mit BEFEHL | Shell durch das Programm ersetzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
exec /usr/bin/printf 'Eigene Kind-Shell ersetzt\n'
printf 'Diese Zeile darf nicht erscheinen\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die neu gestartete Übungsshell wird durch printf ersetzt. Die zweite Ausgabe erscheint nicht; die Arbeitsshell des Benutzers wird nicht ersetzt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Wrapper verstehen; bewusstes Weiterreichen von Prozessidentität und Signalen vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht probeweise in einer wichtigen interaktiven Sitzung verwenden. Dauerhafte Umleitungen können spätere Ausgaben unbemerkt in Dateien schreiben. Nur die isolierte neue Shell ist betroffen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nachfolgende Zeilen fehlen | Bei erfolgreichem exec beabsichtigt. |
| Shell endet bei fehlendem Programm | Nichtinteraktives Fehlerverhalten und execfail beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| bash | Neue Shell für Übungen. |
| env | Kindumgebung setzen. |
| trap | Shellereignisse behandeln. |

Ausgangsdatensatz 542 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
