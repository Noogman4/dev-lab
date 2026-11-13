---
id: "tshark"
name: "tshark"
command: "tshark"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Wireshark & Analyse", "tshark"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 712
reviewed_at: "2026-11-13"
locally_checked_version: "Wireshark-Werkzeugfamilie 4.2.2"
---

# tshark – Paketfelder ausdrücklich offline auswerten

## 1. Kurzbeschreibung

tshark kann live aufzeichnen oder gespeicherte Capturedateien analysieren.

## 2. Was macht der Befehl?

Ohne -r kann das Programm eine Livequelle wählen; für die Dateianalyse ist -r daher entscheidend. -f bezeichnet einen Capturefilter, -Y einen Displayfilter. -n schaltet Namensauflösung ab. -T fields und -e wählen Felder statt einer Bildschirmzusammenfassung. Die Testdaten sind vollständig synthetisch; kein Paket wurde aufgezeichnet, empfangen oder gesendet.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/tshark.html)

## 3. Syntax

```text
tshark [OPTIONEN] -r DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r DATEI | Offlinequelle |
| -n | Keine Namensauflösung |
| -Y FILTER | Displayfilter |
| -T fields | Feldausgabe |
| -e FELD | Spalte auswählen |

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
python3 <<'PCAPDATA'
import struct
from pathlib import Path
# Selbst erfundener Ethernet/ARP-Rahmen; niemals an ein Interface senden.
frame = bytes.fromhex(
    'ffffffffffff0200000000010806'
    '0001080006040001'
    '020000000001c0000201'
    '000000000000c0000202'
)
def capture(filename, timestamps):
    header = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
    packets = b''.join(
        struct.pack('<IIII', timestamp, 0, len(frame), len(frame)) + frame
        for timestamp in timestamps
    )
    Path(filename).write_bytes(header + packets)
capture('own.pcap', [1700000000, 1700000001])
PCAPDATA
tshark -n -r own.pcap -Y arp -T fields -e frame.number -e arp.opcode > fields.txt
printf '1	1
2	1
' > expected.txt
cmp fields.txt expected.txt
cat fields.txt
```

### Schritt 3: Ergebnis einordnen

Zwei selbst erfundene ARP-Request-Rahmen werden als Nummern 1 und 2 mit Opcode 1 dekodiert. Das ist keine Aussage über reales Netzwerkverhalten. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Werkzeugwirkung an kleinen selbst erzeugten Analyse-Dateien nachvollziehen. Für eigene Dateiarbeit sind keine Root-Rechte erforderlich.

## 7. Risiken, Nebenwirkungen und Vorsicht

Dissektoren verarbeiten komplexe Eingaben. Nur bekannte kleine eigene Daten, ohne Livequelle, externen Captureprozess und DNS. Reale Mitschnitte können Geheimnisse und personenbezogene Daten enthalten. Neue eigene Ziele verwenden und Quell-/Zielpfade trennen.

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

Ausgangsdatensatz 712 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
