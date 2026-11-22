---
id: "tail"
name: "tail"
command: "tail"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "tail"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 638
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# tail – Dateiende begrenzen und Follow-Modi unterscheiden

## 1. Kurzbeschreibung

tail zeigt standardmäßig die letzten zehn Zeilen einer Eingabe.

## 2. Was macht der Befehl?

-n +ZAHL beginnt ab einer Zeilennummer. -f folgt standardmäßig einem offenen Deskriptor; --follow=name beziehungsweise -F reagiert anders auf Dateiaustausch und Rotation. -n begrenzt beim Follow nicht die Zahl künftiger Meldungen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tail.1.html)

## 3. Syntax

```text
tail [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n ZAHL | Letzte Zeilen |
| -c ZAHL | Letzte Bytes |
| -f | Fortlaufend folgen |
| -F | Dateiname mit Wiederholungsversuchen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\nzwei\ndrei\n' > own.txt
tail -n 2 own.txt > result.txt
printf 'zwei\ndrei\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Geprüft ist nur ein endlicher Auszug der eigenen Datei. Follow, Rotation und dauerhafte Beobachtung bleiben ungeprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Ein begrenztes Dateiende lesen oder einen bewusst gewählten Followmodus verstehen; hier nur endliche Dateiausgabe geprüft.

## 7. Risiken, Nebenwirkungen und Vorsicht

Protokolle können Geheimnisse enthalten. Kein echter Logpfad und kein unbefristeter Beobachter gestartet. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nach zehn Zeilen läuft es weiter | -n begrenzt nur die anfängliche Auswahl, -f folgt danach weiter |
| Neue Logdatei bleibt unsichtbar | Deskriptorfolge und namensbasiertes -F unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| head | Dateianfang |
| sed | Feste Zeilenauswahl |
| tailf | Historischer verworfener Alternativname |

Ausgangsdatensatz 638 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
