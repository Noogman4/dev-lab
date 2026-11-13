---
id: "mvn"
name: "mvn"
command: "mvn"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "mvn"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 287
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# mvn – Maven-Phasen und Plugingoals gezielt wählen

## 1. Kurzbeschreibung

mvn startet Apache Maven. Es liest das Projektmodell pom.xml und führt Phasen oder Plugingoals aus. validate ist eine Phase und keine garantierte reine XML-Syntaxprüfung eines beliebigen Projekts.

## 2. Was macht der Befehl?

Die default-Lebenszyklusphasen bauen aufeinander auf: package umfasst vorherige Phasen wie compile und test; verify schließt weitere Prüfungen ein. clean ist ein eigener Lebenszyklus. install legt Artefakte im lokalen Maven-Repository ab und bedeutet keine Betriebssysteminstallation. deploy veröffentlicht sie in einem entfernten Repository. Welche Goals tatsächlich laufen, bestimmen Packaging, POM, Plugins und Profile.

Quelle, am 2026-11-13 gelesen: [Maven-Lebenszyklus](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html) und [Maven-3.9-CLI](https://maven.apache.org/ref/3.9.11/maven-embedder/cli.html)

## 3. Syntax

```text
mvn [OPTIONEN] [PHASE-ODER-PLUGIN:GOAL...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-f POM` | Projektdatei ausdrücklich wählen. |
| `-o` | Offline arbeiten; fehlende Plugins/Abhängigkeiten bleiben Fehler. |
| `-B` | Nicht interaktiv laufen, keine automatische Sicherheitsprüfung. |
| `-DNAME=WERT` | Maven-Property setzen. |
| `-Dmaven.repo.local=PFAD` | Lokales Artefaktrepository gezielt ablegen. |
| `-P PROFILE` | Profile aktivieren; verändert wirksamen Build. |
| `-pl`, `-am` | Reaktorteilprojekte und nötige Abhängigkeiten wählen. |
| `-v` / `-V` | Version und Ende beziehungsweise Version mit anschließendem Build unterscheiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-287-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cat > pom.xml <<'POM'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>lernen</artifactId>
  <version>1.0</version>
  <packaging>pom</packaging>
</project>
POM
mvn -B -o -Dmaven.repo.local="$uebung/artefakte" -f pom.xml validate

```

### Schritt 3: Ergebnis auswerten

Bei passender installierter Maven-/Java-Umgebung wäre ein erfolgreicher validate-Durchlauf dieses minimalen eigenen POM-Projekts zu erwarten. Es enthält keine Abhängigkeiten, Profile oder eigenen Plugins. mvn fehlt lokal; BUILD SUCCESS wird deshalb nicht als beobachtetes Ergebnis ausgegeben. Fremde Projekte können zusätzliche Aktionen bereits an validate binden. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Buildabläufe verstehen: Phase und Goal unterscheiden. Artefakte planen: package, lokale Ablage und entfernte Veröffentlichung gezielt trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Plugins und Erweiterungen führen Code aus; Profile und Benutzereinstellungen beeinflussen den Build. Downloads, Tests und deploy haben reale Nebenwirkungen. Offline schränkt Mavens Artefaktbezug ein, ist aber keine allgemeine Netzwerksandbox für Plugins. Keine Installations-, Veröffentlichungs- oder clean-Aufrufe sind Teil des Beispiels. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No goals specified | Gewünschte Phase ausdrücklich wählen. |
| Plugin offline nicht vorhanden | Prüfung offen lassen; kein unbemerkter Netzwechsel. |
| Unexpected lifecycle action | Wirksame POM-/Profilbindungen prüfen. |
| Test übersprungen | Überspringoptionen und Pluginregeln prüfen; kein bestandener Test. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gradle` | Alternatives Buildsystem. |
| `javac` | Compiler, den Mavenplugins ansteuern können. |
| `jar` | Archivwerkzeug statt Lebenszyklusverwaltung. |

Ausgangsdatensatz 287 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
