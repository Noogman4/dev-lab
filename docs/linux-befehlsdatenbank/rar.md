---
id: "rar"
name: "rar"
command: "rar"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "rar"]
status: "Ausgearbeitet; Herstellerhandbuch geprüft, praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 13
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Text-Handbuch der Linux-Konsole RAR 7.23 gelesen"
---

# rar – RAR-Archive mit der Herstellerkonsole bearbeiten

## 1. Kurzbeschreibung

`rar` ist die RAR-Kommandozeilenanwendung des Herstellers. Sie kann RAR-Archive erstellen, untersuchen, testen und entpacken. Das ist von der grafischen Windows-Anwendung WinRAR und von anderen Programmen zum bloßen Entpacken zu unterscheiden.

**Für eigene Dateien sind keine Root-Rechte nötig.** Erstellen, Ergänzen, Verschieben und Entpacken haben unterschiedliche Schreibwirkungen. Der Befehl ist nicht grundsätzlich nur lesend.

## 2. Was macht der Befehl?

Ein Unterkommando wählt die Aktion. Bei einem neuen Archiv werden Dateien und gegebenenfalls ihre Pfade im RAR-Format gespeichert. Mit passenden Schaltern kann zusätzlich verschlüsselt werden.

**Wichtiger Unterschied zu WinRAR:** Das gelesene Handbuch der RAR-Linux-Konsole beschreibt RAR-Archive, nicht eine allgemeine ZIP-Erstellungsfunktion. Eine bloße Endung `.zip` macht eine mit dieser Konsole erstellte Datei nicht zum ZIP-Format.

Die Grundlage dieser Dokumentation ist `rar/rar.txt` aus dem [offiziellen RAR-Linux-Paket 7.23](https://www.rarlab.com/rar/rarlinux-x64-723.tar.gz), verlinkt über die [Hersteller-Downloadseite](https://www.rarlab.com/download.htm). Es wurde ausschließlich Text gelesen; das enthaltene Programm wurde nicht installiert oder ausgeführt.

## 3. Syntax

```text
rar BEFEHL [SCHALTER] ARCHIV [DATEIEN ...] [ZIELORDNER/]
```

| Befehl | Aufgabe |
| --- | --- |
| `a` | Dateien zum Archiv hinzufügen; bei Bedarf neu anlegen. |
| `l` | Inhalt auflisten. |
| `t` | Archivdateien testen. |
| `x` | Mit gespeicherten Pfaden entpacken. |
| `e` | Ohne gespeicherte Pfade entpacken. |
| `d` | Inhalte aus dem Archiv löschen. |
| `m` | Dateien ins Archiv verschieben und nach Erfolg von der Quelle entfernen. |

Für die Hilfe der Herstellerkonsole:

```bash
rar '-?'
```

Die Anführungszeichen halten das Fragezeichen von der Dateinamenexpansion der Shell fern. Der bisherige allgemeine `--help`-Platzhalter wird hier durch den im Herstellerhandbuch dokumentierten Hilfeschalter ersetzt.

## 4. Wichtige Optionen

| Schalter | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-cfg-` | Konfigurationsdateien und `RARINISWITCHES` ignorieren. | Für nachvollziehbare Beispiele ohne übernommene Voreinstellungen. |
| `-r` | Unterordner rekursiv berücksichtigen. | Erweitert die Dateiauswahl; im kleinen Einzeldatei-Beispiel nicht nötig. |
| `-m0` bis `-m5` | Kompressionsmethode beziehungsweise Stufe wählen. | `-m0` speichert ohne Kompression; Bedarf und Ergebnis abwägen. |
| `-o-` | Bereits vorhandene Ziele überspringen. | Schützt vor dieser Ersetzung, erzeugt aber keinen garantiert vollständig neuen Zielbestand. |
| `-o+` | Vorhandene Ziele ersetzen. | Nicht unbedacht mit unbekannten Eingaben verwenden. |
| `-p` | Passwort für Dateidaten interaktiv anfordern. | Dateinamen bleiben dabei grundsätzlich von einer gesonderten Kopfverschlüsselung zu unterscheiden. |
| `-hp` | Dateidaten und Archivkopf verschlüsseln. | Schützt auch die Liste sensibler Namen; Passwortverfügbarkeit ist für Wiederherstellung entscheidend. |
| `-df` | Dateien nach erfolgreicher Archivierung entfernen. | Zusätzliche Löschwirkung; nicht Teil der vorsichtigen Beispiele. |
| `-y` | Rückfragen mit Ja beantworten. | Kann notwendige Entscheidungen übergehen. |

Der konkrete Umfang ist versionsabhängig. Die aufgeführten Schalter wurden im Text-Handbuch der Herstellerkonsole 7.23 geprüft. Eine WinRAR-Anleitung oder die Hilfe eines freien UnRAR-Werkzeugs ist dafür kein gleichwertiger Ersatz.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug und Hilfe am Zielsystem prüfen

```bash
command -v rar
rar '-?'
```

Das Beispiel setzt die passende Herstellerkonsole voraus. Paketverfügbarkeit und Nutzungsbedingungen sind über die vorgesehene Bereitstellung zu prüfen. Eine Installation ist nicht Bestandteil des folgenden Arbeitsablaufs.

### Schritt 2: Neue kleine Eingabe vorbereiten

```bash
uebung="$(mktemp -d -t netmon-rar-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eigene RAR-Testnotiz.' > "notiz.txt"
```

Vor dem Fortsetzen den erfolgreichen Verzeichniswechsel prüfen. Die Datei wird neu angelegt und ist kein vorhandenes privates Original.

### Schritt 3: Ein neues Archiv anlegen

```bash
rar a -cfg- "sammlung.rar" "notiz.txt"
```

`a` nimmt die genannte Eingabe auf. `-cfg-` verhindert, dass eigene Konfigurationsvorgaben eine zusätzliche Wirkung in das Beispiel hineintragen. `sammlung.rar` ist der neue Archivname. Eine bestehende Datei gleichen Namens könnte dagegen verändert werden; deshalb einen noch nicht belegten Namen verwenden.

### Schritt 4: Auflisten und testen

```bash
rar l -cfg- "sammlung.rar"
rar t -cfg- "sammlung.rar"
```

Die erste Aktion sollte die Testnotiz auflisten. Der zweite Aufruf fordert den Test der Archivdaten an. Ein bestandener Test ist weder ein Virenscan noch ein Nachweis einer vertrauenswürdigen Herkunft.

### Schritt 5: In einen neuen Ordner entpacken

```bash
mkdir "Ausgabe"
rar x -cfg- -o- "sammlung.rar" "Ausgabe/"
```

`x` erhält gespeicherte Pfade. Der abschließende Schrägstrich macht die Rolle des Zielordners deutlich. `-o-` überspringt bereits vorhandene Ziele. Nachher den Inhalt der ausgegebenen `notiz.txt` mit dem Original vergleichen.

**Prüfpunkt:** Diese Schritte wurden hier nicht praktisch ausgeführt. Sie sind anhand des Herstellerhandbuchs aufgeschrieben und am tatsächlichen Zielsystem mit eigenen Testdaten zu prüfen.

## 6. Typische Anwendungsfälle

**RAR-Dateien für einen vorgegebenen Austauschweg erstellen:** Die empfangende Seite muss Formatversion und verwendete Funktionen unterstützen. Ein Dateiname allein beweist keine Kompatibilität.

**Ein bestehendes Archiv untersuchen:** `l` liefert eine Liste, `lt` technische Details. Das Lesen einer Liste führt nicht automatisch zur Ausführung enthaltener Programme.

**Ein neues Archiv mit geschütztem Kopf erstellen:** Für einen ausdrücklich benötigten Verschlüsselungsablauf kann beispielsweise `rar a -cfg- -hp privat.rar notiz.txt` verwendet werden. Ein echtes Passwort nicht direkt im Kommando speichern. Die ursprüngliche Textdatei bleibt dennoch unverschlüsselt vorhanden.

**Mehrteilige Archive bearbeiten:** Alle erforderlichen Teile müssen vollständig und passend benannt verfügbar sein. Für konkrete Volumen-, Reparatur- und Wiederherstellungsfunktionen ist die installierte Version gesondert zu prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Archiv verändern statt neu erzeugen

`a` kann ein vorhandenes Archiv ändern. Das ist kein „nur erstellen, falls noch nicht vorhanden“-Schalter. Für eine unabhängige neue Kopie einen neuen Namen wählen und Originale behalten.

### Verschieben und Löschen

`m` entfernt nach erfolgreicher Aufnahme die Quellen; `-df` fordert eine zusätzliche Löschwirkung beim Archivieren an. `d` löscht Inhalte innerhalb des Archivs. Diese drei Fälle nicht mit einem rein lesenden Test verwechseln.

### Überschreiben und Voreinstellungen

`-o+` kann vorhandene Ausgaben ersetzen. Konfigurationsdateien und `RARINISWITCHES` können normale Aufrufe zusätzlich beeinflussen. `-cfg-` wird in der Übung bewusst eingesetzt, um diese versteckten Vorgaben auszuschließen.

### Verschlüsselung und Dateikopien

Ein vergessener Schlüssel kann den Zugriff auf verschlüsselte Daten dauerhaft verhindern. `-p` und `-hp` schützen nicht automatisch unverschlüsselte Quellen oder temporäre Kopien außerhalb des Archivs. Passwörter in Argumenten können in Verlauf und Prozessinformationen sichtbar werden.

### Fremde Archive und große Ausgaben

Dateipfade, Verknüpfungen, große Dekompressionsmengen und besondere Dateitypen sind bei fremden Archiven gesondert zu beurteilen. Ein eigener Zielordner ist keine Sandbox. Ausgepackte Programme nicht ungeprüft starten.

**Root ist für keine der gezeigten eigenen Dateien nötig.** Ein allgemeines Systembackup mit vollständigen Linux-Metadaten braucht einen gesondert geplanten und getesteten Rückspielweg.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `rar` fehlt | Passendes Werkzeug ist nicht bereitgestellt. | Vorgesehenes Paket und Herstellerkonsole prüfen; UnRAR nicht mit RAR gleichsetzen. |
| Angebliches ZIP ist kein ZIP | Die Konsole hat RAR-Daten unter einer irreführenden Endung erzeugt. | Format statt Endung prüfen; passende ZIP-Werkzeuge verwenden. |
| Vorhandene Ausgabedatei bleibt unverändert | `-o-` überspringt sie absichtlich. | Für eine vollständige getrennte Ausgabe einen neuen Ordner wählen. |
| Passwort oder Test schlägt fehl | Falsches Passwort, fehlende Teile oder Datenfehler möglich. | Originalarchiv erhalten und Ursache prüfen. |
| Liste kann nicht angezeigt werden | Archivkopf ist möglicherweise verschlüsselt. | Berechtigtes Passwort benötigen; nicht vorschnell Dateikorruption annehmen. |
| Verhalten unterscheidet sich vom Beispiel | Andere Version oder übernommene Voreinstellungen. | Passendes Handbuch sowie Konfiguration prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erst mit einer neu angelegten Textdatei arbeiten.
2. Das passende Konsolenhandbuch lesen, nicht unbesehen WinRAR-Schalter übernehmen.
3. Im Beispiel Voreinstellungen mit `-cfg-` ausschließen.
4. Für eine neue Kopie neue Archiv- und Zielnamen wählen.
5. Auflisten, Testen und kontrolliertes Zurückspielen getrennt durchführen.
6. Lösch-, Verschiebe- und automatische Ja-Funktionen nicht in Standardbeispiele übernehmen.
7. Bei Verschlüsselung auch unverschlüsselte Quellen und Passwortaufbewahrung berücksichtigen.

**Prüfstand:** Das Handbuch `rar.txt` aus dem offiziellen Linux-Paket 7.23 wurde als Text gelesen und die beschriebenen Schalter darin abgeglichen. In dieser Umgebung ist `rar` nicht installiert. Es gab weder eine Programmausführung aus dem heruntergeladenen Paket noch eine praktische Prüfung von Archivierung, Verschlüsselung oder Extraktion. Diese Punkte bleiben ausdrücklich offen.

## 10. Verwandte Befehle

| Befehl oder Werkzeug | Zusammenhang |
| --- | --- |
| `unrar` | Herstellerwerkzeug zum Lesen, Testen und Entpacken; keine RAR-Erstellung. |
| `unrar-free`, `unar` | Andere Implementierungen mit eigenem Funktionsumfang und eigener Syntax. |
| `7z` | Kann je nach Variante RAR-Dateien lesen, erstellt damit aber nicht automatisch RAR-Archive. |
| `zip`, `unzip` | Für das eigenständige ZIP-Format. |
| `tar` | Andere Archivierungsschnittstelle, häufig für Linux-Verzeichnisbäume. |

Der unveränderte Ausgangseintrag steht unter Datensatz 13 in `index.json`. Neu präzisiert sind Herstellerkonsole, tatsächliches Archivformat, Hilfeschalter sowie Lösch- und Verschiebewirkungen.
