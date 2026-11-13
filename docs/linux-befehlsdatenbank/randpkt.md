---
id: "randpkt"
name: "randpkt"
command: "randpkt"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Wireshark & Analyse", "randpkt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 708
reviewed_at: "2026-11-13"
locally_checked_version: "Wireshark-Werkzeugfamilie 4.2.2"
---

# randpkt – Zufallspakete nur als Testdatei erzeugen

## 1. Kurzbeschreibung

randpkt erzeugt eine Capturedatei mit zufälligen Testpaketen.

## 2. Was macht der Befehl?

Es sendet diese nicht selbst auf ein Interface. Die Daten können absichtlich unvollständig oder protokollwidrig sein. -t wählt ein Grundmuster, -b die maximale Größe und -c die Zahl. Das Ergebnis ist kein Mitschnitt eines tatsächlich geführten Dialogs. Die Testdaten sind vollständig synthetisch; kein Paket wurde aufgezeichnet, empfangen oder gesendet.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/randpkt.html)

## 3. Syntax

```text
randpkt [OPTIONEN] AUSGABEDATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c ANZAHL | Kleine feste Paketzahl |
| -b BYTES | Maximale Paketgröße |
| -t TYP | Musterart |
| -F FORMAT | Dateiformat |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
export WIRESHARK_CONFIG_DIR="$probe_dir/config"
export XDG_CONFIG_HOME="$probe_dir/xdg"
mkdir "$WIRESHARK_CONFIG_DIR" "$XDG_CONFIG_HOME"
randpkt -c 3 -b 96 -t eth own-random.pcapng
LC_ALL=C capinfos -c own-random.pcapng > info.txt
grep -Eq 'Number of packets: *3$' info.txt
cat info.txt
```

### Schritt 3: Ergebnis einordnen

Eine eigene Datei mit drei synthetischen Paketen wird erzeugt und gezählt. Inhalte sind zufällig und werden nicht als gültiges Ethernetgespräch behauptet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Werkzeugwirkung an kleinen selbst erzeugten Analyse-Dateien nachvollziehen. Für eigene Dateiarbeit sind keine Root-Rechte erforderlich.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große Fuzzingmengen können Ressourcen verbrauchen. Hier nur drei kleine Dateieinträge; keine Einspeisung und kein Netzverkehr. Reale Mitschnitte können Geheimnisse und personenbezogene Daten enthalten. Neue eigene Ziele verwenden und Quell-/Zielpfade trennen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Formatfehler | Dateiformat und Erzeugung prüfen |
| Unerwartete Zahl | Auswahl, Zeitstempel und Dateiformat getrennt betrachten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| capinfos | Dateimetadaten |
| editcap | Dateibearbeitung |
| tshark | Offline-Feldauswertung |

Ausgangsdatensatz 708 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
