---
id: "sh"
name: "sh"
command: "sh"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "sh"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 556
reviewed_at: "2026-11-13"
locally_checked_version: "/bin/sh -> dash; Paket 0.5.12-6ubuntu5"
---

# sh – sh als Schnittstelle statt feste Implementierung verstehen

## 1. Kurzbeschreibung

sh ist der übliche Aufruf einer Shell mit POSIX-orientierter Schnittstelle; welche Implementierung dahinterliegt, hängt vom System ab.

## 2. Was macht der Befehl?

Auf dieser Umgebung zeigt /bin/sh auf Dash. Das rechtfertigt keine Annahme für andere Distributionen. Ein Skript mit Bash-Arrays oder [[ ... ]] wird durch den Aufruf sh nicht zu portablem Code. Expliziter Interpreter und Shebang sind getrennt zu beachten: sh DATEI verwendet sh auch bei abweichender Shebang.

Quelle, am 2026-11-13 gelesen: [Dash-Handbuch als lokale sh-Implementierung](https://manpages.debian.org/bookworm/dash/dash.1.en.html); `/bin/sh`-Verknüpfung lokal geprüft, POSIX-Onlinereferenz nicht abrufbar

## 3. Syntax

```text
sh [OPTIONEN] [SKRIPT [ARGUMENTE]]
sh -c CODE NAME [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c CODE | Zeichenfolge ausführen. |
| -n | Shellsyntax prüfen. |
| -s | Befehle aus Standardeingabe. |
| -x | Ablauf protokollieren; keine reine Prüfung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
cat > own.sh <<'SHCODE'
test "$1" = eigen || exit 1
printf 'Eigenes sh-Skript ausgefuehrt
'
SHCODE
sh -n own.sh
env -u ENV sh own.sh eigen
```

### Schritt 3: Ergebnis einordnen

Ein eigenes minimales Skript besteht Syntaxprüfung und Ausführung unter dem lokalen sh. Dies ist kein Test aller POSIX-Sprachregeln. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine portable Skripte prüfen; Interpreterabhängigkeiten erkennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein fremdes Skript wird durch sh nicht sicher. Die eigene Login-Shell und /bin/sh-Verknüpfung bleiben unverändert. Keine realen Startdateien gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bash-Erweiterung scheitert | Benötigten Interpreter korrekt benennen oder Skript portieren. |
| Version unbekannt | Programmpfad und Paketzuordnung prüfen, nicht allgemeines sh --version voraussetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** /bin/sh -> dash; Paket 0.5.12-6ubuntu5. Praktisch geprüft: Lokale sh-Implementierung und eigenes Skript geprüft; andere Systeme und vollständige POSIX-Konformität offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| dash | Lokale sh-Implementierung. |
| bash | Andere Shell. |
| . | Datei im gleichen Shellkontext. |

Ausgangsdatensatz 556 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
