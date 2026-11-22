---
id: "qemu_img"
name: "qemu-img"
command: "qemu-img"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "qemu-img"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 697
reviewed_at: "2026-11-13"
locally_checked_version: "QEMU 8.2.2"
---

# qemu-img – Ein eigenes leeres Diskabbild offline prüfen

## 1. Kurzbeschreibung

qemu-img bearbeitet Diskabbilddateien offline und startet selbst keine virtuelle Maschine.

## 2. Was macht der Befehl?

Virtuelle Größe ist nicht die tatsächlich belegte Dateigröße. -f wählt das Eingabeformat, -O ein Ausgabeformat bei convert. Fremde Images können Backing-Dateien oder externe Ressourcen referenzieren; die Übung erzeugt deshalb eine neue Datei ohne Backing-Kette.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.qemu.org/docs/master/tools/qemu-img.html)

## 3. Syntax

```text
qemu-img UNTERBEFEHL [OPTIONEN] DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| create -f FORMAT | Abbild erzeugen |
| info --output=json | Metadaten |
| convert -f IN -O OUT | Konvertieren |
| compare | Gastseitigen Inhalt vergleichen |
| check | Formatkonsistenz, keine Dateisystemprüfung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
qemu-img create -f qcow2 own.qcow2 1M
qemu-img info -f qcow2 --output=json own.qcow2 > info.json
python3 -c 'import json; d=json.load(open("info.json")); assert d["format"] == "qcow2"; assert d["virtual-size"] == 1048576'
qemu-img convert -f qcow2 -O raw own.qcow2 own.raw
qemu-img compare -f qcow2 -F raw own.qcow2 own.raw
printf 'Eigenes 1-MiB-Abbild offline verglichen\n'
```

### Schritt 3: Ergebnis einordnen

Die selbst erzeugte leere Datei hat 1 MiB virtuelle Größe. Der Vergleich bestätigt gleiche gastseitige Nullinhalte nach Raw-Konvertierung, kein bootfähiges System und keine Dateisystemintegrität. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Abbildformat und Inhaltsvergleich verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Niemals ein aktiv genutztes Abbild verändern. Keine realen Datenträger, Gastimages oder laufenden VMs beteiligt. Für eigene Dateien keine Root-Rechte nötig.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Formatfehler | Explizites Format und Herkunft prüfen |
| Virtuelle Größe größer als Datei | Sparse-/Metadatenformat unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** QEMU 8.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| qemu-system-x86_64 | VM-Ausführung |
| cmp | Dateibytes statt Gastsektoren |
| stat | Dateibelegung |

Ausgangsdatensatz 697 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
