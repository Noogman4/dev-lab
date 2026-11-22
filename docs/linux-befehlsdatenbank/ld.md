---
id: "ld"
name: "ld"
command: "ld"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "ld"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 283
reviewed_at: "2026-11-13"
locally_checked_version: "GNU ld / Binutils 2.42; Hilfscompiler gcc 13.3.0"
---

# ld – Objektdateien mit dem GNU-Linker verbinden

## 1. Kurzbeschreibung

ld verbindet Objektdateien und Archive, ordnet Sektionen und löst Symbolbezüge auf. Es kann ausführbare Programme, gemeinsame Bibliotheken oder weitere verschiebbare Objekte erzeugen. Das Linkergebnis wird nicht automatisch gestartet.

## 2. Was macht der Befehl?

GNU ld arbeitet mit dem für sein Target passenden Format und Linkerskript. Reihenfolge kann bei Bibliotheken entscheidend sein: Ein statisches Archiv wird gewöhnlich an seiner Position für bereits offene Bezüge durchsucht. Für normale C-/C++-Programme ist der Compilertreiber meist geeigneter, weil er Laufzeitobjekte, Bibliotheken und Startkonventionen ergänzt. main allein ist kein vollständiger roher Betriebssystem-Einstieg.

Quelle, am 2026-11-13 gelesen: [GNU-ld-Aufruf](https://sourceware.org/binutils/docs/ld/Invocation.html) und [Optionen](https://sourceware.org/binutils/docs/ld/Options.html)

## 3. Syntax

```text
ld [OPTIONEN] OBJEKTE... [-lBIBLIOTHEK] -o AUSGABE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-o DATEI` | Ausgabedatei benennen. |
| `-r` | Relokatierbare Ausgabe statt fertig startbarem Programm erzeugen. |
| `-L ORDNER`, `-lNAME` | Bibliothekssuchpfad und Bibliotheksname. |
| `-T SKRIPT` | Linklayout über Skript bestimmen; kann weitere Dateien einbeziehen. |
| `-e SYMBOL` | Einstiegssymbol wählen; erzeugt keinen Laufzeitstartcode. |
| `-Map=DATEI` | Speicher-/Symbolzuordnung protokollieren. |
| `--shared` | Gemeinsames Objekt erzeugen; PIC und ABI gesondert planen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-283-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
ld --version
printf 'int lernwert = 42;
' > daten.c
printf 'extern int lernwert; int hole(void) { return lernwert; }
' > zugriff.c
gcc -c daten.c -o daten.o
gcc -c zugriff.c -o zugriff.o
ld -r -o gemeinsam.o daten.o zugriff.o
readelf -s gemeinsam.o

```

### Schritt 3: Ergebnis auswerten

Die kombinierte Symboltabelle enthält lernwert und hole als definierte Symbole. -r lässt weiterhin Relokationen für einen späteren endgültigen Link zu. gemeinsam.o ist kein ausführbares Lernprogramm und wurde nicht gestartet. Der Test belegt nur die Zusammenführung dieser eigenen Objekte mit der lokalen Toolchain. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Linkfehler verstehen: Definitionen, offene Bezüge und Bibliothekspositionen unterscheiden. Binäraufbau lernen: Mit kleinen eigenen Objekten Sektionen und Symbole vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Linkskripte und Plugins sind Vertrauensgrenzen; unbekannte Eingaben können weitere Dateien referenzieren. Ausgabeziele werden geschrieben. Ein erfolgreiches Linken garantiert keine richtige Speicherbehandlung oder ABI-Kompatibilität zur Laufzeit. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Undefined reference | Definition, Linkreihenfolge und passende Bibliothek prüfen. |
| Multiple definition | Symbol mehrfach definiert; keine Schutzoption blind abschalten. |
| File format not recognized | Architektur/Format prüfen; ld kann unbekannte Dateien als Skript behandeln. |
| Entry symbol fehlt | Normalen Compilertreiber beziehungsweise korrekten Startcode verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU ld / Binutils 2.42; Hilfscompiler gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gcc` | Geeigneter Treiber für normale C-Programmlinks. |
| `as` | Erzeugt Objektdateien. |
| `nm` | Zeigt Definitionen und offene Symbole. |
| `readelf` | Untersucht ELF-Ausgaben. |

Ausgangsdatensatz 283 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
