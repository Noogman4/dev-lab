---
id: "valgrind"
name: "valgrind"
command: "valgrind"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["valgrind", "entwicklung"]
status: "Quellen geprüft; eigener C-Test kompiliert und normal ausgeführt; Memcheck praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 302
reviewed_at: "2026-11-13"
locally_checked_version: "Valgrind nicht installiert; Testprogramm mit GCC 13.3.0 geprüft"
---

# valgrind – Eigene Programme auf beobachtete Speicherfehler untersuchen

## 1. Kurzbeschreibung

Valgrind ist eine Werkzeugsammlung zur Untersuchung laufender Programme. Das häufig verwendete Memcheck erkennt verschiedene Speicherzugriffs- und Speicherverwaltungsfehler, besonders bei C und C++. **Für ein eigenes normal ausführbares Testprogramm sind keine Root-Rechte nötig.**

Es liest ein Programm nicht nur passiv: Das Ziel wird tatsächlich ausgeführt, zusätzlich instrumentiert und meist deutlich langsamer. Alle normalen Wirkungen des Zielprogramms müssen deshalb berücksichtigt werden.

## 2. Was macht der Befehl?

Valgrind führt ausgewählten Maschinencode in einer instrumentierten Umgebung aus. Memcheck beobachtet dabei Speicherzugriffe und Zustände. Es kann beispielsweise ungültige Lese-/Schreibzugriffe, Nutzung uninitialisierter Werte oder fehlerhafte Speicherfreigaben melden.

Der [offizielle Schnellstart](https://valgrind.org/docs/manual/quick-start.html) beschreibt den Einstieg mit Debugsymbolen. Die [Memcheck-Referenz](https://valgrind.org/docs/manual/mc-manual.html) erklärt Fehlerklassen; das [Kernhandbuch](https://valgrind.org/docs/manual/manual-core.html) trennt allgemeine Optionen vom gewählten Werkzeug. Eine unauffällige Prüfung betrifft nur die tatsächlich ausgeführten Pfade und Eingaben, nicht alle denkbaren Programmzustände.

## 3. Syntax

```text
valgrind [VALGRIND_OPTIONEN] PROGRAMM [PROGRAMM_ARGUMENTE ...]
valgrind --tool=memcheck PROGRAMM
```

Valgrind-Optionen stehen vor dem Zielprogramm. Argumente danach gehören zum Ziel. Memcheck ist das übliche Standardwerkzeug; andere Werkzeuge wie Callgrind beantworten andere Fragen. Eine Profilingmessung ist keine gleichwertige Speicherfehlerprüfung.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `--tool=memcheck` | Speicherprüfung auswählen. | Nicht jedes Valgrind-Werkzeug meldet dieselben Fehler. |
| `--leak-check=full` | Ausführlichere Leckanalyse am Ende. | Kategorien wie erreichbar und verloren unterscheiden. |
| `--show-leak-kinds=all` | Weitere Leckkategorien anzeigen. | Mehr Ausgabe bedeutet nicht automatisch mehr echte Programmfehler. |
| `--track-origins=yes` | Ursprung undefinierter Werte genauer verfolgen. | Zusätzlicher Aufwand. |
| `--error-exitcode=99` | Bei entsprechend gewerteten Prüffehlern eigenen Status verwenden. | Programmstatus und Prüfkonfiguration gemeinsam betrachten. |
| `--log-file=DATEI` | Diagnose in eine Datei schreiben. | Reales Schreibziel, vorhandene Datei beachten. |
| `--trace-children=yes` | Geeignete Kindprogrammstarts mitverfolgen. | Vergrößert Untersuchungsumfang und Laufzeit. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Ein eigenes kleines Programm vorbereiten

In einer Bash einen neuen Übungsbereich verwenden. Der C-Code reserviert acht Bytes, benutzt einen gültigen Index und gibt den Speicher wieder frei.

```bash
(
  uebung="$(mktemp -d -t netmon-valgrind-XXXXXX)" || exit 1
  cat > "$uebung/probe.c" <<'C'
#include <stdlib.h>
#include <stdio.h>
int main(void) {
    unsigned char *p = malloc(8);
    if (p == NULL) return 1;
    p[0] = 42;
    printf("Wert: %u\n", (unsigned)p[0]);
    free(p);
    return 0;
}
C
  gcc -g -O0 -Wall -Wextra "$uebung/probe.c" -o "$uebung/probe" || exit 1
  "$uebung/probe" || exit 1
  printf 'Eigener Testordner: %s\n' "$uebung"
)
```

`-g` erzeugt Debuginformationen; `-O0` hält die Optimierung für diesen Lernfall gering. Der normale Programmlauf soll `Wert: 42` ausgeben. Das wurde lokal mit dem eigenen Quelltext geprüft. Es ist noch kein Memcheck-Lauf.

### Schritt 2: Späteren Memcheck-Aufruf verstehen

Nur bei installiertem Valgrind und mit dem zuvor angezeigten eigenen Pfad wäre folgender Musteraufruf möglich:

```text
valgrind --tool=memcheck --leak-check=full --error-exitcode=99 /PFAD/ZUM/EIGENEN-TESTORDNER/probe
```

Dieser Aufruf wurde hier nicht ausgeführt. Für den beabsichtigten fehlerfreien Test wäre ein unauffälliger Memcheck-Bericht zu erwarten; das ist keine gemessene Aussage über Bibliotheken oder andere Laufumgebungen.

### Schritt 3: Einen Bericht lesen

Programmausgabe und Valgrind-Diagnose unterscheiden. Bei einer Meldung zuerst Fehlerart, betroffene Stelle und Aufrufkette lesen. „Noch erreichbar“ bedeutet etwas anderes als „definitiv verloren“. Erst die erste ursächliche Meldung verstehen, bevor spätere Folgefehler behandelt werden.

## 6. Typische Anwendungsfälle

### Eigene Speicherverwaltung prüfen

Kleine Testfälle gezielt durchlaufen und gemeldete Zugriffe dem eigenen Code zuordnen. Fehlende Debugsymbole können die Zuordnung erschweren.

### Regressionen abfangen

Ein bekannter eigener Testfall kann unter Memcheck Teil einer Entwicklungskontrolle sein. Eingaben, Versionen und Fehlerstatuskonventionen müssen reproduzierbar festgehalten werden.

### Speicherverbrauch besser verstehen

Leckkategorien helfen, verlorene Reservierungen von absichtlich weiter erreichbaren Strukturen zu unterscheiden. Für umfassendes Profiling gibt es weitere Werkzeuge mit anderer Aussage.

## 7. Risiken, Nebenwirkungen und Vorsicht

Valgrind ist keine Sandbox. Ein untersuchtes Programm kann weiterhin Dateien verändern, Verbindungen öffnen oder Prozesse starten. Deshalb keine unbekannten fremden Programme nur wegen dieser Prüfung ausführen.

Laufzeit und Speicherbedarf steigen. Zeitabhängige Fehler können unter Instrumentierung anders auftreten. Unterdrückungsregeln können Meldungen ausblenden und benötigen eine konkrete Begründung. Ein sauberer Lauf ersetzt weder Sicherheitsreview noch Tests anderer Eingaben. Diagnoseprotokolle können interne Pfade und Daten enthalten.

## 8. Häufige Fehler

- **Keine Quellenzeilen:** Debugsymbole fehlen oder passen nicht zur Binärdatei.
- **Zielprogramm verändert Daten:** Instrumentierung verhindert dessen normale Aktionen nicht.
- **Status 0 als allgemeine Fehlerfreiheit verstanden:** Nur geprüfte Pfade und gewertete Fehlerklassen sind erfasst.
- **Große Verlangsamung:** Für instrumentierte Ausführung normal, Umfang begrenzen.
- **Alle Meldungen unterdrückt:** Ergebnis ist dadurch nicht automatisch fachlich geklärt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit eigenem minimalem Programm beginnen und normale Ausführung zuerst verstehen. Einen Fehler nach dem anderen anhand nachvollziehbarer Testdaten bearbeiten. Keine dauerhaften Dienste oder echten Benutzerdateien zum ersten Versuch verwenden.

**Prüfstand:** Offizielle Handbücher gelesen. GCC 13.3.0 kompilierte den eigenen C-Test; der normale Lauf ergab `Wert: 42`, Status 0. Valgrind ist nicht installiert. Kein Memcheck-, Profiling- oder Fehlerunterdrückungslauf; diese praktische Prüfung bleibt offen.

## 10. Verwandte Befehle

- `gdb`: interaktive Programmdiagnose mit eigenem Ausführungsmodell.
- `gcc`, `clang`: Compiler; Debuginformationen und passende Warnungen erzeugen.
- AddressSanitizer: andere, beim Übersetzen eingebundene Instrumentierung.
- `heaptrack`: anderes Speicherprofilingwerkzeug, nicht dieselbe Prüfung.

Ausgangsdatensatz 302 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
