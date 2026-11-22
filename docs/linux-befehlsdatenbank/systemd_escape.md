---
id: "systemd_escape"
name: "systemd-escape"
command: "systemd-escape"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-escape"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 573
reviewed_at: "2026-11-13"
locally_checked_version: "systemd 255.4-1ubuntu8.18"
---

# systemd-escape – Text in einen Systemd-Unitnamen umwandeln

## 1. Kurzbeschreibung

systemd-escape kodiert Zeichenfolgen für Unitnamen und kann diese Kodierung zurücknehmen.

## 2. Was macht der Befehl?

Pfadkodierung ist von Shellquoting und URL-Kodierung zu unterscheiden. --path normalisiert einen Pfad und ersetzt Trennzeichen nach Systemd-Regeln. Ein so erzeugter .mount-Name legt keine Unitdatei an und hängt kein Dateisystem ein. Der Pfad muss für die reine Textumwandlung nicht existieren.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-escape-Handbuch](https://man7.org/linux/man-pages/man1/systemd-escape.1.html)

## 3. Syntax

```text
systemd-escape [OPTIONEN] ZEICHENFOLGE ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --path | Pfadnormalisierung und -kodierung. |
| --suffix=TYP | Unittyp wie mount anhängen. |
| --unescape | Kodierung rückgängig machen; nicht mit --suffix kombinieren. |
| --template=VORLAGE | Instanz in eine passende Unitvorlage einsetzen. |
| --mangle | Bereits unitähnlichen Namen behandeln; anderer Modus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
lesson_path='/srv/lern ordner'
lesson_unit=$(systemd-escape --path --suffix=mount "$lesson_path")
printf '%s
' "$lesson_unit"
lesson_back=$(systemd-escape --unescape --path "${lesson_unit%.mount}")
test "$lesson_back" = "$lesson_path"
printf 'Text-Rueckumwandlung stimmt
'
```

### Schritt 3: Ergebnis einordnen

Nur eine erfundene Zeichenfolge wird umgewandelt und nach Entfernung des Suffixes zurückgewandelt. Die Gleichheit wird geprüft. /srv wird weder betreten noch angelegt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Unitnamen fachlich korrekt aus Pfaden ableiten; manuelles Ersetzen von Sonderzeichen vermeiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Ergebnis ist weiterhin Dateninhalt und darf nicht unzitiert als Shellcode verwendet werden. Pfadnormalisierung kann die ursprüngliche Schreibweise verändern; nicht jeder Modus ist bytegenau invertierbar.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Suffix stört Unescape | Unittypsuffix gezielt entfernen oder passenden Modus wählen. |
| Andere Schreibweise zurück | Normalisierung und unterschiedliche Escape-Modi beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** systemd 255.4-1ubuntu8.18. Praktisch geprüft: Ein eigener Pfadtext mit Leerzeichen hin und zurück geprüft; Vorlagen, problematische Pfade und Unitbetrieb offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl | Unitnamen verwenden. |
| systemd.unit | Namensregeln. |
| printf | Kodierten Text unverändert ausgeben. |

Ausgangsdatensatz 573 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
