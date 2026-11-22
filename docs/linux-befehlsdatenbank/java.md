---
id: "java"
name: "java"
command: "java"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "java"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 281
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# java – Java-Anwendungen in der JVM starten

## 1. Kurzbeschreibung

java startet eine Java Virtual Machine und führt Anwendungscode aus. Der Klassenstart, der JAR-Start und der Quelldateimodus sind unterschiedliche Aufrufformen. Eine JVM ist keine Sicherheitsisolation für unbekannte Programme.

## 2. Was macht der Befehl?

Beim klassischen Klassenstart wird der voll qualifizierte Klassenname ohne .class angegeben. Der Launcher sucht über Klassen- oder Modulpfad und ruft den passenden Einstieg auf. Im hier dokumentierten JDK-21-Modell ist dies public static void main(String[] args). Neuere JDKs können weitere Einstiegsformen unterstützen. Ab Java 11 kann der Quelldateimodus einfachen eigenen Quelltext direkt kompilieren und starten; das ist bereits Programmausführung.

Quelle, am 2026-11-13 gelesen: [JDK-21-Launcherhandbuch](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)

## 3. Syntax

```text
java [JVM-OPTIONEN] KLASSE [PROGRAMMARGUMENTE...]
java [JVM-OPTIONEN] -jar ARCHIV.jar [ARGUMENTE...]
java [OPTIONEN] QUELLE.java [ARGUMENTE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` / `-version` | Version lesen und beenden; Ausgabeziel kann sich unterscheiden. |
| `-cp PFAD` | Klassenpfad setzen; Linuxeinträge mit Doppelpunkt trennen. |
| `-jar ARCHIV` | Main-Class des Manifests verwenden; andere Klassenpfadeinstellungen werden dabei ignoriert. |
| `--module-path PFAD`, `-m MODUL` | Modulpfad und Einstiegsmodul wählen. |
| `-DNAME=WERT` | JVM-Systemeigenschaft setzen, keine Shellvariable. |
| `-XmxGROESSE` | Heap-Obergrenze setzen; begrenzt nicht den gesamten Prozessspeicher. |
| `--source VERSION` | Sprach-/API-Version des Quelldateimodus wählen; verfügbare Versionen prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-281-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cat > Hallo.java <<'JAVA'
class Hallo {
    public static void main(String[] args) {
        System.out.println("Hallo Java");
    }
}
JAVA
env -u JDK_JAVA_OPTIONS -u JAVA_TOOL_OPTIONS -u _JAVA_OPTIONS java --source 11 Hallo.java

```

### Schritt 3: Ergebnis auswerten

Mit einer geeigneten vollständigen Java-Installation würde Hallo Java ausgegeben. Der Quellmodus erzeugt hier keine gewöhnliche persistente Hallo.class im Arbeitsordner. Die genannten Optionsvariablen werden nur für den Prozess entfernt, damit keine zusätzlichen JVM-Optionen übernommen werden. Java fehlt lokal; Start und Ausgabe bleiben ungeprüft. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Eigene Anwendungen ausführen: Launcheroptionen vor dem Klassennamen von Programmargumenten dahinter unterscheiden. Laufzeitfehler eingrenzen: Java-Version und Klassenformat vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Java-Code kann Dateien verändern, Prozesse starten und das Netz nutzen. Agenten, Bibliothekspfade und fremde JARs sind zusätzliche Ausführungsquellen. Heapoptionen ersetzen keine Ressourcensandbox. Keine unbekannten Anwendungen zum Prüfen eines Versionsproblems starten. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ClassNotFoundException | Klassenname, Paket und -cp prüfen; nicht Hallo.class als Klassenname angeben. |
| UnsupportedClassVersionError | Bytecode wurde für eine neuere Laufzeit erzeugt. |
| Could not find main method | Einstieg passt nicht zur verwendeten Java-Version. |
| Unrecognized option | JVM-Variante und Version prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `javac` | Erzeugt separate Klassenartefakte. |
| `jar` | Packt Klassen und Ressourcen. |
| `javadoc` | Erstellt API-Dokumentation, kein Programmlauncher. |

Ausgangsdatensatz 281 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
