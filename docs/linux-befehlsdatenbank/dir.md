---
id: "dir"
name: "dir"
command: "dir"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "dir"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 180
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# dir – Verzeichnisinhalt mit festen Anzeigeoptionen lesen

## 1. Kurzbeschreibung

GNU dir listet Verzeichniseinträge und Dateiinformationen. Seine Vorgabe entspricht ls -C -b: spaltenweise, mit Backslashdarstellung nichtgrafischer Zeichen.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Ohne Pfad wird das aktuelle Verzeichnis gelesen. Ein übergebenes Verzeichnis wird normalerweise geöffnet, eine Datei dagegen selbst beschrieben. -d zeigt den Verzeichniseintrag statt seines Inhalts. -a nimmt Punktnamen einschließlich . und .. auf, -A lässt genau diese zwei besonderen Einträge weg. Der Name dir bezeichnet hier das GNU-Werkzeug und nicht den gleichnamigen Windows-Shellbefehl. Optionen und Ausgabe sind deshalb nicht zwischen den Systemen austauschbar. Für eine kontrollierte Zeilenansicht wird -1 ausdrücklich gesetzt; Locale und Quotierungsoptionen bestimmen weiterhin die Darstellung.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt dir invocation](https://www.gnu.org/software/coreutils/manual/html_node/dir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
dir [OPTIONEN] [DATEI_ODER_ORDNER ...]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -1 | Ein Eintrag pro Ausgabezeile |
| -A | Punktnamen außer . und .. |
| -l | Lange Ansicht mit Metadaten |
| -d | Verzeichnis selbst statt Inhalt |
| -b | Nichtgrafische Zeichen als Escape darstellen |
| --color=never | Keine ANSI-Farbcodes |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Nur einfache selbst angelegte ASCII-Namen werden verglichen. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-dir-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
mkdir daten
printf 'eigener Inhalt\n' > daten/notiz.txt
printf 'eigene Vorgabe\n' > daten/.vorgabe
LC_ALL=C dir -1 -A --color=never -- daten > liste.txt
printf '.vorgabe\nnotiz.txt\n' > erwartet.txt
cmp liste.txt erwartet.txt
cat liste.txt
)
```

### Schritt 3: Ergebnis verstehen

mkdir und printf erzeugen nur eigene Testdaten. -A macht die versteckte .vorgabe sichtbar; -1 verhindert Mehrspaltenlayout. Der feste C-Vergleich liefert genau zwei Zeilen. Die Datei liste.txt liegt außerhalb des gelisteten Datenordners. Das ist eine Anzeigeprüfung, keine Prüfung beliebiger Dateinamen mit Zeilenumbrüchen.

## 6. Typische Anwendungsfälle

Eine einfache Ordnerübersicht lesen oder GNU-dir-Verhalten in vorhandenen Skripten verstehen. Für eine menschenlesbare Metadatenansicht -l wählen; für maschinelle Dateiauswahl andere Schnittstellen verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Einträge und Eigentümerangaben können vertraulich sein. Rekursion mit -R kann große oder nicht freigegebene Bäume erfassen. Dateinamen können Steuerzeichen enthalten; rohe Anzeige und ungeprüfte Weitergabe an eine Shell vermeiden. Eine Liste ist kein atomarer Schnappschuss eines parallel veränderten Ordners.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Punktdatei fehlt | Normalerweise werden Punktnamen ausgelassen, -A bewusst wählen |
| Spalten statt einer Liste | GNU dir verwendet standardmäßig Spalten, -1 ausdrücklich angeben |
| Skript zerlegt Namen falsch | Zeilenbasierte Anzeige nicht als universelles Dateinamenformat behandeln |

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur den eigenen Zielordner auswählen. Die Übung nutzt keine Rekursion und keine fremden Pfade. Für beliebige Dateinamen etwa find -print0 mit passendem Empfänger verwenden, nicht die dekorierte Anzeige auswerten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Andere Dateinamen, Terminalbreiten und Implementierungen bleiben offen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ls | Eng verwandte GNU-Anzeige mit anderer Vorgabe |
| vdir | Lange Ansicht als Vorgabe |
| find | Explizite Auswahl und NUL-Ausgabe |

Herkunft: Originaldatensatz 180 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
