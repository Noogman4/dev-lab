---
id: "black"
name: "black"
command: "black"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "black"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 514
reviewed_at: "2026-11-13"
locally_checked_version: "Black 24.2.0 unter Python 3.12.3"
---

# black – Python-Dateien einheitlich formatieren

## 1. Kurzbeschreibung

Black formatiert Python-Quelltext; der Standardaufruf schreibt die betroffenen Dateien neu.

## 2. Was macht der Befehl?

Mit --check wird nur geprüft, mit --diff eine Änderung angezeigt. Beide Modi lassen den Quelltext unverändert. Ein Formatter beweist weder fachliche Korrektheit noch bestandene Tests. Zielversion und Konfiguration beeinflussen die Ausgabe; die Online-Dokumentation kann neuer als die installierte Version sein.

Quelle, am 2026-11-13 gelesen: [Black-Projektdokumentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)

## 3. Syntax

```text
python3 -m black [OPTIONEN] DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --check | Status 0 bei unverändertem Format, 1 bei Formatabweichung, 123 bei internem Fehler. |
| --diff | Unterschied anzeigen, nicht anwenden. |
| --line-length ZAHL | Bevorzugte Zeilenlänge; Standard 88. |
| --target-version VERSION | Unterstützte Python-Grammatik berücksichtigen. |
| --config DATEI | Ausgewählte Konfiguration lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'value = 1
' > sample.py
cp sample.py before.py
BLACK_CACHE_DIR="$probe_dir/cache" python3 -m black --check --diff sample.py
cmp sample.py before.py
printf 'Format passt; Quelldatei unveraendert
'
```

### Schritt 3: Ergebnis einordnen

Geprüft wurde genau eine bereits formatierte eigene Datei; cmp bestätigt unveränderte Bytes. In dieser Sandbox Black immer einzeln pro Datei aufrufen, um den dokumentierten Mehrdatei-Worker-Hänger zu vermeiden. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Formatabweichungen im Review zeigen; einheitlichen Stil in eigenen Python-Dateien prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ohne Prüfoptionen überschreibt Black Quelltext. Rekursive Verzeichnisauswahl kann mehr Dateien erfassen als beabsichtigt. Cache liegt im eigenen Temporärordner. Kein Projektcode formatiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 | Formatabweichung, nicht automatisch interner Fehler. |
| Syntax nicht unterstützt | Zielversion und installierte Black-Version prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Black 24.2.0 unter Python 3.12.3. Praktisch geprüft: Eine eigene Datei mit --check/--diff geprüft; Schreibmodus und weitere Grammatiken offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ruff | Lintregeln und alternativer Formatter. |
| pytest | Verhalten durch Tests prüfen. |
| mypy | Statische Typprüfung. |

Ausgangsdatensatz 514 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
