---
id: "text2pcap"
name: "text2pcap"
command: "text2pcap"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Wireshark & Analyse", "text2pcap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 711
reviewed_at: "2026-11-13"
locally_checked_version: "Wireshark-Werkzeugfamilie 4.2.2"
---

# text2pcap – Einen eigenen Hexdump in eine Capturedatei umwandeln

## 1. Kurzbeschreibung

text2pcap erzeugt Paketdateien aus passenden Hexdarstellungen.

## 2. Was macht der Befehl?

Offsetfelder und Bytewerte müssen zum Eingabeformat passen. -l beziehungsweise -E legen die Linkschicht fest. Optionen können künstliche Protokollheader ergänzen; solche Header sind keine gemessenen Netzwerkdaten. Der Test gibt einen selbst definierten vollständigen Rahmen vor. Die Testdaten sind vollständig synthetisch; kein Paket wurde aufgezeichnet, empfangen oder gesendet.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/text2pcap.html)

## 3. Syntax

```text
text2pcap [OPTIONEN] EINGABETEXT AUSGABECAPTURE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -l TYP | Numerische Linkschicht |
| -F FORMAT | Captureformat |
| -o BASIS | Offsetbasis |
| -t FORMAT | Zeitstempel parsen |
| -q | Weniger Diagnose |

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
python3 <<'HEXDATA'
from pathlib import Path
payload = Path('own.pcap').read_bytes()[40:82]
assert len(payload) == 42
lines = [f'{offset:06x}  ' + ' '.join(f'{value:02x}' for value in payload[offset:offset+16]) for offset in range(0, len(payload), 16)]
Path('own.hex').write_text('\n'.join(lines) + '\n')
HEXDATA
text2pcap -q -F pcap -l 1 own.hex generated.pcap
python3 <<'CHECKHEX'
from pathlib import Path
original = Path('own.pcap').read_bytes()[40:82]
converted = Path('generated.pcap').read_bytes()[40:]
assert converted == original
print('Eigene Rahmenbytes nach Heximport identisch')
CHECKHEX
```

### Schritt 3: Ergebnis einordnen

Die erzeugte Capturedatei enthält dieselben 42 selbst definierten Rahmenbytes. Zeitmetadaten werden nicht als gemessene Paketzeit behauptet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Werkzeugwirkung an kleinen selbst erzeugten Analyse-Dateien nachvollziehen. Für eigene Dateiarbeit sind keine Root-Rechte erforderlich.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein erzeugter Capture ist kein Echtheitsnachweis. Unklare Offsets und zusätzliche Header können Interpretation verändern. Reale Mitschnitte können Geheimnisse und personenbezogene Daten enthalten. Neue eigene Ziele verwenden und Quell-/Zielpfade trennen.

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

Ausgangsdatensatz 711 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
