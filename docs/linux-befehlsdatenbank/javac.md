---
id: "javac"
name: "javac"
command: "javac"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "javac"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 282
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# javac – Java-Quelltext in Klassen übersetzen

## 1. Kurzbeschreibung

javac kompiliert Java-Quellen in .class-Dateien für die JVM. Es startet das fertige Anwendungsprogramm nicht automatisch. Ein JDK mit Compiler und eine bloße Laufzeitinstallation sind zu unterscheiden.

## 2. Was macht der Befehl?

Die Ausgabe bildet Paketnamen als Verzeichnishierarchie ab. -d legt deren Wurzel fest; es ist nicht zugleich automatisch der Klassenpfad eines späteren Launchers. --release verbindet Sprachstand, Klassenformat und verfügbare Standard-API einer unterstützten Zielversion. Nur -source und -target allein verhindern nicht jede versehentliche Nutzung zu neuer APIs. Annotation Processing kann während der Kompilierung fremden Prozessorcode ausführen; Defaults ändern sich zwischen JDK-Versionen.

Quelle, am 2026-11-13 gelesen: [JDK-21-Compilerhandbuch](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html)

## 3. Syntax

```text
javac [OPTIONEN] QUELLE.java...
javac @ARGUMENTDATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-d ORDNER` | Klassen getrennt vom Quelltext ablegen. |
| `--release VERSION` | Unterstützte ältere Plattform gezielt wählen, ab JDK 9. |
| `-encoding UTF-8` | Quellzeichensatz ausdrücklich festlegen. |
| `-g` | Zusätzliche Debugdaten einschließlich lokaler Variablen erzeugen. |
| `-Xlint:all` | Viele zusätzliche Warnungen aktivieren. |
| `-Werror` | Warnungen als Fehler behandeln. |
| `-proc:none` | Annotation Processing deaktivieren. |
| `-cp PFAD` | Eigene Typen suchen; fremde Klassenpfade sind Vertrauensentscheidungen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-282-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cat > Hallo.java <<'JAVA'
public class Hallo {
    public static void main(String[] args) {
        System.out.println("Hallo javac");
    }
}
JAVA
mkdir klassen
env -u JDK_JAVAC_OPTIONS -u JAVA_TOOL_OPTIONS -u _JAVA_OPTIONS javac -proc:none --release 11 -encoding UTF-8 -Xlint:all -d klassen Hallo.java
test -f klassen/Hallo.class
env -u JDK_JAVA_OPTIONS -u JAVA_TOOL_OPTIONS -u _JAVA_OPTIONS java -cp klassen Hallo

```

### Schritt 3: Ergebnis auswerten

Eine passende JDK-/JVM-Kombination würde klassen/Hallo.class erzeugen und beim ausdrücklich getrennten Start Hallo javac ausgeben. Dateiname und öffentliche Klasse stimmen überein. javac und java fehlen hier, daher sind beide Funktionsschritte praktisch offen. Die kurzlebige env-Auswahl verändert keine realen Benutzereinstellungen. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Klassenartefakte bauen: Quellen und Ausgabe getrennt halten. Zielplattform planen: API-Verfügbarkeit mit --release prüfen, statt nur das Dateiformat zu ändern.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Prozessoren und Compilerplugins können schon beim Bauen Code ausführen. -proc:none schaltet Annotation Processing ab, isoliert aber nicht sämtliche Compilerkomponenten. Der gesonderte java-Aufruf führt Anwendungscode mit den Benutzerrechten aus. Keine zusätzlichen Bibliotheken werden heruntergeladen. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Public class muss in passende Datei | Groß-/Kleinschreibung und Klassenname beachten. |
| Release not supported | Liste unterstützter Zielversionen der konkreten javac-Version lesen. |
| Package does not exist | Klassen-/Modulpfad und Abhängigkeiten prüfen. |
| Klasse nach Build nicht gefunden | -d-Ausgabe bei java ausdrücklich als -cp angeben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `java` | Führt die erzeugten Klassen aus. |
| `jar` | Packt Klassen und Ressourcen. |
| `javap` | Liest Klassendateistrukturen. |

Ausgangsdatensatz 282 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
