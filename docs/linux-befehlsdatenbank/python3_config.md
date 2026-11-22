---
id: "python3_config"
name: "python3-config"
command: "python3-config"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Entwicklung", "python3-config"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 295
reviewed_at: "2026-11-13"
locally_checked_version: "python3-config mit CPython-3.12-Flags; kein eigener --version-Schalter"
---

# python3-config – C-Buildparameter einer Python-Installation lesen

## 1. Kurzbeschreibung

python3-config gibt Compiler-, Linker- und ABI-Informationen der zugehörigen Python-Installation aus. Es kompiliert kein Programm und installiert keine Pakete. Der Name garantiert nicht die Übereinstimmung mit jeder anderen Python-Installation im PATH.

## 2. Was macht der Befehl?

Erweiterungsmodule werden in einen vorhandenen Interpreter geladen; Einbettung bindet den Interpreter in ein eigenes Hauptprogramm ein. Diese Fälle benötigen unterschiedliche Linkparameter. Bei modernen CPython-Versionen ist für Einbettung --embed zusammen mit --ldflags wichtig, weil normale Erweiterungsflags die Pythonbibliothek nicht zwingend enthalten. Absolute Pfade oder versionsspezifische config-Namen helfen, mehrere Installationen auseinanderzuhalten.

Quelle, am 2026-11-13 gelesen: [CPython: Einbettung und Linkparameter](https://docs.python.org/3.12/extending/embedding.html#compiling-and-linking-under-unix-like-systems), [Debian-python3-config-Handbuch](https://manpages.debian.org/trixie/python3-dev/python3-config.1.en.html) und lokale Hilfe. Die alten pauschalen Buildbeispiele der Debian-Manpage werden nicht übernommen

## 3. Syntax

```text
python3-config --includes
python3-config --cflags
python3-config [--embed] --ldflags
python3-config --extension-suffix
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--includes` | Header-Suchoptionen wie -I ausgeben. |
| `--cflags` | Empfohlene C-Compilerflags, oft mit Optimierungs-/Diagnosevorgaben. |
| `--ldflags` | Linkparameter ausgeben; Bedeutung hängt vom Einbettungsmodus ab. |
| `--embed` | Parameter für Einbettung wählen; Unterstützung lokaler Version prüfen. |
| `--libs` | Bibliotheksoptionen statt kompletter Linkerflags. |
| `--extension-suffix` | Passenden Namenssuffix für Erweiterungsmodule ausgeben. |
| `--prefix`, `--exec-prefix` | Installationspräfixe lesen. |
| `--help` | Unterstützte Optionen lesen; --version ist nicht pauschal vorgesehen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-295-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
python3-config --help > hilfe.txt
python3-config --includes > includes.txt
python3-config --ldflags > erweiterung.txt
python3-config --embed --ldflags > einbettung.txt
python3-config --extension-suffix > suffix.txt
cat includes.txt erweiterung.txt einbettung.txt suffix.txt

```

### Schritt 3: Ergebnis auswerten

Die lokale Ausgabe nannte /usr/include/python3.12. Erst mit --embed erschien -lpython3.12; der Suffix lautete .cpython-312-x86_64-linux-gnu.so. Diese Werte sind installationsspezifisch. Es wurde nur die Flagausgabe in eigene Dateien geschrieben: kein C-Build, kein Laden einer Erweiterung und keine Interpretereinbettung wurden damit nachgewiesen. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Erweiterungen planen: ABI und Header der vorgesehenen Installation wählen. Einbettung vorbereiten: Zusätzliche Bibliotheksanforderungen ausdrücklich prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgaben sind Buildargumente, kein blind auszuführendes Shellskript. Nicht per eval ausführen. Enthaltene Flags können etwa NDEBUG oder Optimierungsoptionen setzen und damit Prüfungen des C-Programms beeinflussen. Ungeprüfte einfache Wortzerlegung scheitert bei ungewöhnlichen Pfaden; robuste Builds verwenden passende Buildsystem-/sysconfig-Schnittstellen. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Python.h fehlt | Header der tatsächlich gewählten Installation prüfen. |
| Undefined reference to Py_* | Einbettungsflags, Reihenfolge und passende Bibliothek prüfen. |
| Import schlägt trotz Build fehl | ABI, Suffix, Architektur und Interpreter vergleichen. |
| Flags unterscheiden sich von Tutorial | Nicht hardcodieren; lokale Installation ist maßgeblich. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** python3-config mit CPython-3.12-Flags; kein eigener --version-Schalter. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `python3` | Zugehöriger Interpreter muss gesondert bestimmt werden. |
| `python3 -m sysconfig` | Weitere Konfigurationsdaten lesen. |
| `gcc` | Verwendet die ermittelten Compiler-/Linkerflags. |

Ausgangsdatensatz 295 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
