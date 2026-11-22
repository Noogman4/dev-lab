---
id: "gradle"
name: "gradle"
command: "gradle"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "gradle"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 278
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# gradle – Projektaufgaben mit Gradle ausführen

## 1. Kurzbeschreibung

Gradle wertet Buildlogik aus und führt daraus gebildete Tasks aus. Buildskripte sind ausführbarer Groovy- oder Kotlin-Code. Selbst eine Aufgabenliste ist deshalb keine garantiert passive Dateianalyse.

## 2. Was macht der Befehl?

settings.gradle beziehungsweise settings.gradle.kts beschreibt den Buildverbund; build.gradle beziehungsweise build.gradle.kts definiert Projektlogik und Tasks. Gewählte Tasks können weitere abhängige Tasks auslösen. Der Wrapper ./gradlew legt eine Projektversion fest, ist aber selbst Code und kann Gradle herunterladen. Eine lokal installierte gradle-Version und der Wrapper sind nicht automatisch identisch. Plugin- und Java-Kompatibilität müssen dazu passen.

Quelle, am 2026-11-13 gelesen: [Gradle-Aufrufhandbuch](https://docs.gradle.org/current/userguide/command_line_interface.html)

## 3. Syntax

```text
gradle [OPTIONEN] [TASK...]
./gradlew [OPTIONEN] [TASK...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `tasks`, `help --task NAME` | Aufgaben beziehungsweise konkrete Taskhilfe; Konfiguration kann ausgeführt werden. |
| `--dry-run` | Taskausführung auslassen; Konfiguration bleibt aktiv. |
| `--offline` | Abhängigkeiten aus Cache verwenden; fehlende Artefakte führen zum Fehler. |
| `--no-daemon` | Keinen wiederverwendbaren Dauerdaemon anfordern; ein kurzlebiger Prozess kann je nach JVM nötig sein. |
| `--gradle-user-home ORDNER` | Caches und benutzerbezogene Gradledaten gezielt ablegen. |
| `--max-workers=1` | Parallelität begrenzen. |
| `--console=plain` | Einfachere Terminalausgabe. |
| `--scan` | Kann Builddaten veröffentlichen; hier nicht verwenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-278-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf "rootProject.name = 'lernen'
" > settings.gradle
cat > build.gradle <<'GRADLE'
tasks.register('hallo') {
    doLast { println 'Hallo Gradle' }
}
GRADLE
gradle --gradle-user-home "$uebung/gradle-daten" --offline --no-daemon --console=plain --max-workers=1 hallo

```

### Schritt 3: Ergebnis auswerten

Eine passende installierte Gradle-/Java-Kombination würde den eigenen hallo-Task ausführen und Hallo Gradle ausgeben. Das Projekt verwendet keine Plugins oder externen Abhängigkeiten. Gradle fehlt hier; Muster und erwartete Ausgabe bleiben praktisch ungeprüft. Auch --offline schränkt selbst geschriebenen Buildcode nicht allgemein vom Netz ab. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Buildabläufe nachvollziehen: Konfigurationsphase, Taskgraph und Taskaktionen unterscheiden. Teamprojekte: Projektversion und Toolchain dokumentieren, bevor ein Build gestartet wird.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Buildskripte und Wrapper können beliebigen Code ausführen. Caches, JVM-Prozesse, Downloads und Veröffentlichungen sind mögliche Nebenwirkungen. --dry-run ist keine Sandbox und keine Garantie gegen Konfigurationsaktionen. Keine Installation und kein Wrapperdownload wurden ausgeführt. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Task nicht gefunden | Projekt und exakten Tasknamen prüfen. |
| Offline-Abhängigkeit fehlt | Keinen automatischen Netzwechsel vornehmen; benötigte Artefakte klären. |
| Java inkompatibel | Versionsanforderungen von Gradle und Toolchain vergleichen. |
| Unerwartete Aktionen bei tasks | Konfigurationscode wird bereits für die Aufgabenermittlung ausgewertet. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mvn` | Anderes JVM-Buildsystem mit Phasen und Plugins. |
| `java` | Laufzeit für Gradle. |
| `make` | Anderer Aufgaben-/Abhängigkeitsmechanismus. |

Ausgangsdatensatz 278 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
