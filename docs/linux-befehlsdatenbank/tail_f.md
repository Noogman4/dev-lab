---
id: "tail_f"
name: "tail -f"
command: "tail -f"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["aufgabenorientierte hilfe", "tail_f"]
status: "Quellen geprüft; Ende und Anhängen an eigener Testdatei praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 60
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# tail -f – Neue Zeilen einer Datei verfolgen

## 1. Kurzbeschreibung

`tail` zeigt das Ende einer Datei. Mit `-f` bleibt es aktiv und gibt anschließend angehängte Daten aus. Das eignet sich beispielsweise, um während eines eigenen Programmtests neue Logmeldungen zu beobachten. **Root ist bei lesbaren eigenen Dateien nicht nötig.** Lesen kann trotzdem vertrauliche Informationen auf dem Bildschirm sichtbar machen.

## 2. Was macht der Befehl?

Ohne weitere Angaben erscheinen zunächst die letzten zehn Zeilen. Danach wartet `-f` auf Wachstum. Es gibt keine automatische Bewertung von Fehlern: Eine ausgegebene Zeile ist zunächst nur Text des schreibenden Programms. `tail` beendet oder repariert diesen Prozess nicht.

GNU `tail -f` folgt standardmäßig dem geöffneten Dateideskriptor. Wenn ein Log rotiert und durch eine neue Datei gleichen Namens ersetzt wird, kann es deshalb bei der alten Datei bleiben. `-F` folgt dagegen dem Namen und versucht nach vorübergehend fehlender Datei erneut zu öffnen. Das ist eine bewusste Wahl zwischen zwei Beobachtungsweisen, keine Garantie lückenloser Protokollierung. Grundlage sind die [Debian-Manpage](https://manpages.debian.org/trixie/coreutils/tail.1.en.html) und die lokal gelesene Hilfe von coreutils 9.4.

## 3. Syntax

```text
tail [OPTIONEN] [DATEI ...]
tail -f -- DATEI
tail -F -- DATEI
```

Eckige Klammern kennzeichnen optionale Teile der Syntax; sie werden nicht eingegeben. `--` beendet die Optionsverarbeitung und schützt Dateinamen, die mit einem Minus beginnen. Ohne Dateiangabe liest `tail` die Standardeingabe. Das Verfolgen einer Pipe ist nicht dasselbe wie das Wiederöffnen einer benannten Logdatei.

## 4. Wichtige Optionen

| Option | Bedeutung | Konsequenz |
| --- | --- | --- |
| `-n 20` | Zunächst letzte 20 Zeilen ausgeben. | Begrenzt den Anfang, nicht spätere neue Zeilen. |
| `-n 0` | Vorhandenen Inhalt zunächst überspringen. | Für neue Meldungen ab Beobachtungsbeginn. |
| `-n +5` | Ab der fünften Zeile ausgeben. | Das Plus verändert die Bedeutung. |
| `-f` | Weiter angehängte Daten verfolgen. | Standardmäßig am geöffneten Deskriptor. |
| `-F` | Namen verfolgen und Öffnen wiederholen. | Für ersetzte oder zeitweise fehlende Logs. |
| `-c 100` | Letzte 100 Bytes ausgeben. | Kann mitten in einem UTF-8-Zeichen beginnen. |
| `--pid=PID` | Mit Follow nach Ende dieses Prozesses beenden. | Richtige Prozessnummer und GNU-Version beachten. |
| `-s 0.5` | Prüfintervall beeinflussen. | Ereignisbenachrichtigungen können anders arbeiten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Testdatei vorbereiten

In einem Bash-Terminal einen isolierten Übungsordner anlegen. Bei Fehlern nicht fortfahren; die geklammerte Sitzung endet dann, ohne dein Terminal zu schließen.

```bash
(
  uebung="$(mktemp -d -t netmon-tail-XXXXXX)" || exit 1
  printf 'Start\nBereit\n' > "$uebung/test.log" || exit 1
  printf 'Testdatei: %s\n' "$uebung/test.log"
  tail -n 1 -- "$uebung/test.log"
)
```

Die letzte Ausgabe muss `Bereit` lauten. Merke dir den zuvor angezeigten vollständigen Dateipfad; die Shellvariable selbst gilt nur innerhalb der Klammern.

### Schritt 2: Beobachtung starten

Im ersten Terminal den angezeigten Pfad einsetzen:

```text
tail -n 0 -f -- /PFAD/ZUM/EIGENEN-UEBUNGSORDNER/test.log
```

Dies ist ein Pfadmuster. Keine fremde oder echte Systemlogdatei einsetzen. Zunächst erscheint nichts, weil `-n 0` den bisherigen Inhalt überspringt.

### Schritt 3: Eine neue Meldung anhängen

In einem zweiten Terminal denselben eigenen Pfad verwenden:

```text
printf 'Neue Meldung\n' >> /PFAD/ZUM/EIGENEN-UEBUNGSORDNER/test.log
```

Im ersten Terminal erscheint `Neue Meldung`. `>>` hängt an; `>` würde den bisherigen Dateiinhalt abschneiden. Die Beobachtung im ersten Terminal mit `Strg+C` beenden. Das beendet den Vordergrundprozess `tail`, nicht den anderen Schreiber und nicht das Terminal.

## 6. Typische Anwendungsfälle

### Eigene Anwendung beobachten

Ein Programm schreibt in eine bekannte Testlogdatei. Du verfolgst ausschließlich die neuen Zeilen und vergleichst ihre Zeitpunkte mit deinen Bedienhandlungen. Eine fehlende Meldung kann auch bedeuten, dass das Programm gepuffert schreibt.

### Bestehende Fehler einordnen

Mit `tail -n 100 -- DATEI` zunächst einen begrenzten Ausschnitt lesen. Erst danach Follow aktivieren; sonst fehlt möglicherweise der Zusammenhang des ersten Fehlers.

### Rotierende Dateien

Für einen wiederkehrenden Dateinamen `-F` erwägen. Bei vom Journal verwalteten Diensten ist häufig `journalctl -f` passender, weil dort nicht einfach eine Textdatei beobachtet wird.

## 7. Risiken, Nebenwirkungen und Vorsicht

`tail` schreibt nicht in die beobachtete Datei, kann aber viele Daten ans Terminal liefern und unbemerkt weiterlaufen. Protokolle können Passwörter, Tokens, personenbezogene Daten oder Terminal-Steuerfolgen enthalten. Vor Weitergabe Ausgabe prüfen und private Informationen entfernen.

Es ist kein zuverlässiger Exportmechanismus: Rotation, sehr schnelles Kürzen/Neuschreiben, Pufferung und Ausfälle können Beobachtungslücken verursachen. Ein lesbarer Dateiname beweist zudem nicht, dass der Inhalt vertrauenswürdig ist. `sudo` vergrößert den lesbaren Bereich und ist kein pauschaler Lösungsweg.

## 8. Häufige Fehler

- **Nach Rotation keine neuen Zeilen:** Deskriptor statt Namen verfolgt; `-F` bewusst wählen.
- **Keine Ausgabe:** `-n 0`, falscher Pfad oder der Schreiber hat noch nicht geschrieben.
- **Veraltete Meldungen erscheinen zuerst:** Anfangsausschnitt wurde nicht begrenzt beziehungsweise nicht übersprungen.
- **Zweiter Test zerstört alte Zeilen:** Beim Anhängen versehentlich `>` statt `>>` benutzt.
- **Beobachtung endet nicht:** Follow ist dauerhaft vorgesehen; im Vordergrund `Strg+C` verwenden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst ohne `-f` lesen, dann mit eigenen Daten das Anhängen üben. Für Live-Logs ein eigenes Terminal verwenden und die Beobachtung danach gezielt beenden. Pipes in Suchwerkzeuge können zusätzlich puffern; eine verzögerte Anzeige beweist keinen Programmstillstand.

**Prüfstand:** GNU coreutils 9.4 lokal festgestellt. Letzte Zeile und nachträglich angehängte Zeile einer eigenen temporären Testdatei geprüft; Testprozess anschließend beendet. Keine Benutzerlogs gelesen. Logrotation, Prozessüberwachung mit `--pid` und Fehler unter Last wurden nicht praktisch geprüft.

## 10. Verwandte Befehle

- `head`: Anfang einer Datei anzeigen.
- `less +F`: interaktiv neue Daten verfolgen und wieder zurückblättern.
- `journalctl -f`: neue Einträge des Systemjournals beobachten, abhängig von Leserechten.
- `grep`: Textmuster filtern; Pufferung bei Live-Pipelines beachten.
- `sed -n`: gezielte Zeilenbereiche ausgeben.

Ausgangseintrag: Datensatz 60 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
