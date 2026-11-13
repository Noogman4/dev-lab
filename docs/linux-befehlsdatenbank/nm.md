---
id: "nm"
name: "nm"
command: "nm"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Entwicklung", "nm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 289
reviewed_at: "2026-11-13"
locally_checked_version: "GNU nm / Binutils 2.42; gcc 13.3.0"
---

# nm – Symbole in Objektdateien und Bibliotheken lesen

## 1. Kurzbeschreibung

GNU nm listet Symbole aus Objektdateien, Archiven und geeigneten Programmen. Es zeigt unter anderem Definitionen und noch offene Bezüge. Die Datei wird dabei nicht als Programm gestartet.

## 2. Was macht der Befehl?

Die Standardsicht enthält Symbolwert, Typzeichen und Namen. Ein Wert in einem relocatierbaren Objekt ist nicht automatisch eine endgültige Laufzeitadresse. T steht typischerweise für Code, D für initialisierte Daten, B für BSS und U für einen undefinierten Bezug. Großbuchstaben bedeuten meist globale, Kleinbuchstaben meist lokale Symbole; besondere Typen wie schwache oder einzigartige globale Symbole haben Ausnahmen. Fehlende normale Symboltabellen schließen dynamische Symbole nicht aus.

Quelle, am 2026-11-13 gelesen: [GNU-Binutils: nm](https://sourceware.org/binutils/docs/binutils/nm.html)

## 3. Syntax

```text
nm [OPTIONEN] OBJEKT-ODER-ARCHIV...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-A` | Quelldatei beziehungsweise Archivmitglied je Symbol nennen. |
| `-g` | Nur externe Symbole anzeigen. |
| `-u` | Nur undefinierte Symbole. |
| `--defined-only` | Nur Definitionen. |
| `-D` | Dynamische statt normaler Symboltabelle wählen, falls vorhanden. |
| `-C` | C++-Namen lesbar demangeln. |
| `-n`, `-S`, `--size-sort` | Nach Wert sortieren, Größe zeigen beziehungsweise nach Größe sortieren. |
| `-s` | Bei Archiven auch Symbolindex anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-289-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
nm --version
cat > lernen.c <<'C'
extern int fehlt;
int lernwert = 42;
int hole(void) { return lernwert + fehlt; }
C
gcc -O0 -c lernen.c -o lernen.o
nm lernen.o
nm -u lernen.o

```

### Schritt 3: Ergebnis auswerten

Im Test erschienen D lernwert, T hole und U fehlt. Der zweite Aufruf beschränkte sich auf fehlt. Es wurde absichtlich nicht gelinkt: Der offene Bezug gehört zur Übung und ist auf Objektstufe kein fehlgeschlagener Programmlauf. Adresswerte und Reihenfolge sind nicht als plattformübergreifende Konstanten zu behandeln. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Linkfehler eingrenzen: Vorhandene Definitionen und erwartete externe Bezüge suchen. Bibliotheksoberfläche prüfen: Normale und dynamische Symbolsicht unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Analyseausgaben können interne Namen offenlegen. Große oder manipulierte Dateien können Parser beanspruchen; aktuelle Werkzeuge und vertrauenswürdige Daten verwenden. BFD-Plugins sind ausführbarer Code und keine bloßen Dateiformatbeschreibungen. Keine fremden Plugins laden und Demangler-Schutzlimits nicht grundlos abschalten. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No symbols | Datei gestrippt oder falsche Tabelle gewählt. |
| U-Symbol als defekt bewertet | Auf Objektstufe kann der spätere Linker den Bezug auflösen. |
| Unlesbare C++-Namen | -C verwenden; Compiler-Mangling beachten. |
| Dateiformat unbekannt | Target und passende Implementierung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU nm / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `readelf -s` | ELF-Symboltabellen mit weiteren Spalten. |
| `objdump -t` | Objektsymbolansicht. |
| `ranlib` | Erzeugt Archivsymbolindex. |
| `ld` | Löst Bezüge beim Linken auf. |

Ausgangsdatensatz 289 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
