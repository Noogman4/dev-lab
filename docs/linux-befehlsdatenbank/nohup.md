---
id: "nohup"
name: "nohup"
command: "nohup"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "nohup"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 497
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# nohup – Ein eigenes kurzes Kommando mit expliziten Umleitungen

## 1. Kurzbeschreibung

GNU nohup startet ein Kommando mit ignoriertem SIGHUP. Es versetzt es nicht automatisch in den Hintergrund und ist kein Dienstmanager oder Wiederanlaufmechanismus.

## 2. Was macht der Befehl?

Automatische Umleitungen hängen davon ab, ob Ein-/Ausgabe an ein Terminal gebunden sind. Explizite Pfade verhindern, dass unerwartet nohup.out im Arbeits- oder Homeverzeichnis verwendet wird. Die Übung wartet auf ein sofort endendes printf; ein Überleben von Logout oder Sitzungsende wird nicht behauptet.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: GNU-coreutils-Manpage nohup; [Projektverweis nohup](https://www.gnu.org/software/coreutils/nohup) (Online-Vollabruf nicht verfügbar)

## 3. Syntax

```text
nohup BEFEHL [ARGUMENTE]
nohup --help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `BEFEHL ARGUMENTE` | Programm tatsächlich starten, kein Shellausdruck automatisch. |
| `< DATEI`, `> DATEI`, `2> DATEI` | Shellumleitungen vor dem Programmstart; Ausgabedateien können überschrieben werden. |
| `&` | Shell-Hintergrundstart, kein Bestandteil von nohup; hier nicht benutzt. |
| Automatische nohup.out | Nur unter passenden Terminalbedingungen; kein festes Ausgabeziel. |
| `--version` | Werkzeugstand ohne HUP-Funktionstest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-nohup-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
nohup --version
nohup /usr/bin/printf 'Lerntext\n' </dev/null > ausgabe.txt 2> fehler.txt
cat ausgabe.txt
test ! -e nohup.out
```

### Schritt 3: Ergebnis einordnen

ausgabe.txt muss Lerntext enthalten; im eigenen Ordner darf keine automatische nohup.out entstehen. Alle drei Standardkanäle sind explizit umgeleitet. Es wird kein SIGHUP gesendet und keine reale Sitzung geschlossen. Das belegt Programmstart und Ausgabeweg, nicht einen Logouttest. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Umleitungen lernen:** Ein-/Ausgabeziele ausdrücklich wählen. **Langläufer planen:** HUP-Behandlung, Hintergrundstart und Dienstüberwachung auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ignoriertes HUP schützt nicht vor KILL, Absturz, Ressourcenmangel oder sitzungsbezogener Prozessbeendigung. Gestarteter Code behält alle eigenen Wirkungen. Hier nur printf mit eigenen Dateien, kein dauerhafter Hintergrundprozess oder Konfigurationswechsel.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Shell bleibt belegt | nohup startet nicht automatisch im Hintergrund. |
| Trotzdem beendet | Andere Signale/Sitzungsregeln oder Programmfehler möglich. |
| Ausgabe unerwartet | Terminalabhängige Defaults durch ausdrückliche Umleitung ersetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Eigenes printf mit expliziten Kanälen ausgeführt; Ausgabetext und fehlende nohup.out geprüft. Kein HUP gesendet, keine Sitzung beendet. Logout-, Langzeit- und andere Implementierungsfälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `disown` | Bash-Jobtabelle/HUP-Weitergabe, anderer Zeitpunkt. |
| `jobs` | Eigene Shelljobs. |
| `systemd-run` | Dienst-/Scopeausführung mit eigenen Systemwirkungen. |

Ausgangsdatensatz 497 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
