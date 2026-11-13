---
id: "jar"
name: "jar"
command: "jar"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "jar"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 280
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# jar – Java-Archive anlegen und ihren Inhalt lesen

## 1. Kurzbeschreibung

jar erstellt, listet, verändert und entpackt JAR-Archive. Ein JAR beruht auf ZIP und kann Klassen sowie Ressourcen enthalten. Eine Archivliste führt die enthaltenen Java-Klassen nicht aus.

## 2. Was macht der Befehl?

Ein gewöhnliches JAR ist nicht automatisch startbar. java -jar benötigt insbesondere einen passenden Main-Class-Eintrag und eine geeignete Einstiegsklasse. Modularchive enthalten einen Moduldeskriptor. Das Archivwerkzeug ersetzt nicht javac und prüft durch bloßes Packen keine Programmlogik. Die hier verwendeten langen Optionen beziehen sich auf moderne JDKs ab 9; ältere Versionen benötigen gegebenenfalls die klassische Kurzsyntax.

Quelle, am 2026-11-13 gelesen: [JDK-21-Werkzeughandbuch: jar](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jar.html)

## 3. Syntax

```text
jar --create --file ARCHIV DATEIEN...
jar --list --file ARCHIV
jar --extract --file ARCHIV [EINTRAEGE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--create` / `-c` | Neues Archiv erzeugen. |
| `--list` / `-t` | Inhaltsverzeichnis lesen. |
| `--extract` / `-x` | Dateien in das aktuelle Verzeichnis schreiben; eigenes Ziel wählen. |
| `--update` / `-u` | Vorhandenes Archiv verändern. |
| `--file` / `-f` | Archivdatei benennen. |
| `-C ORDNER DATEIEN` | Nachfolgende Eingaben relativ zum gewählten Ordner übernehmen. |
| `--main-class KLASSE` | Einstieg im Manifest vermerken; erzeugt die Klasse nicht. |
| `--no-compress` / `-0` | Unkomprimiert speichern; keine Verschlüsselung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-280-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir daten
printf 'Eigene Ressource
' > daten/notiz.txt
jar --create --file lernen.jar -C daten notiz.txt
jar --list --file lernen.jar
mkdir ausgabe
cd -- ausgabe || exit 1
jar --extract --file ../lernen.jar notiz.txt
cmp -- ../daten/notiz.txt notiz.txt

```

### Schritt 3: Ergebnis auswerten

Erwartet wäre notiz.txt in der Liste, zusätzlich normalerweise META-INF/MANIFEST.MF. cmp würde den extrahierten Inhalt mit der eigenen Quelle byteweise vergleichen. jar fehlt hier; weder Archiv noch Inhaltsvergleich wurden praktisch erzeugt. Der Textinhalt braucht keine Java-Klasse und wird nicht ausgeführt. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Ressourcen bündeln: Eigene Daten mit relativen Eintragsnamen packen. Auslieferung verstehen: Archivformat, Manifest und Laufzeit getrennt behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Entpacken kann vorhandene Dateien überschreiben und viel Speicher belegen. Unbekannte Archive zunächst nur listen und Pfade prüfen. Ein JAR ist keine vertrauenswürdige Anwendung allein wegen seines Formats; java -jar führt Code aus. Archivkompression schützt keine Geheimnisse. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No main manifest attribute | Packen ohne Main-Class ist zulässig, aber nicht mit java -jar startbar. |
| Klasse fehlt trotz Manifest | Klassenpfad, Eintragsnamen und Kompilierung prüfen. |
| Unbekannte lange Option | JDK-Version und klassische Syntax vergleichen. |
| Falsche Verzeichnisstruktur | Position von -C und die folgenden Eingaben prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `javac` | Erzeugt .class-Dateien. |
| `java` | Startet Klassen oder ausführbare JARs. |
| `unzip -l` | Weitere ZIP-Inhaltsansicht. |

Ausgangsdatensatz 280 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
