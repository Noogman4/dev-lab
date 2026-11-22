---
id: "test"
name: "test"
command: "test"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["test", "grundlagen & hilfe"]
status: "Bedingungssyntax geprüft; kein sicherheitsrelevanter Pfadzugriff durchgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 368
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# test – Bedingungen prüfen, ohne sie als Zugriffsfreigabe zu missverstehen

## 1. Kurzbeschreibung

`test` bewertet eine Bedingung und liefert ihren Wahrheitswert als Rückgabestatus. Es kann Zeichenketten, Ganzzahlen oder Dateieigenschaften betrachten. **Root-Rechte sind für die gewöhnliche Nutzung nicht nötig.**

## 2. Was macht der Befehl?

Die lokale Hilfe `help test` beschreibt die Bash-Variante. Status `0` steht für wahr; eine falsche Bedingung liefert einen negativen Ausgang. Fehlerhafte Argumente sind davon als Diagnosefall zu unterscheiden.

Eine Dateiabfrage ist eine Momentaufnahme. Zwischen Test und späterem Öffnen kann sich ein Pfad verändern. Deshalb ist `test` allein keine Sicherheitsgrenze für sensible Schreiboperationen.

## 3. Syntax

```bash
test -n "$text"
test "$zahl" -eq 3
[ -n "$text" ]
```

Bei der eckigen Form müssen `[` und `]` eigene Argumente bleiben. Leerzeichen sind dafür relevant. Zahlen vor einer arithmetischen Prüfung auf geeignetes Format begrenzen.

## 4. Wichtige Optionen

| Ausdruck | Frage | Grenze |
| --- | --- | --- |
| `-n TEXT` | Nicht leer? | Text quotieren. |
| `-z TEXT` | Leer? | Nicht gleich „Variable ungesetzt“. |
| `A = B` | Gleiche Zeichenketten? | Kein allgemeiner Zahlenvergleich. |
| `A -eq B` | Gleiche Ganzzahlen? | Eingabeformat beachten. |
| `-f PFAD` | Reguläre Datei? | Folgt gewöhnlich einem Symlink zum Ziel. |
| `-d PFAD` | Verzeichnis? | Kein Beweis privater Eigentümerschaft. |
| `-L PFAD` | Symbolischer Link? | Prüft eine andere Eigenschaft. |
| `-r PFAD` | Als lesbar bewertet? | Kein Ersatz für den tatsächlichen Öffnungsversuch. |

Für mehrere Bedingungen getrennte Tests mit klarer Shellverknüpfung bevorzugen, statt mehrdeutige lange `-a`/`-o`-Ausdrücke aufzubauen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  netmon_text='Eigener Wert'
  if test -n "$netmon_text"; then
    printf '%s\n' 'Text ist vorhanden'
  fi
)
```

Der eigene feste Text ist nicht leer. Deshalb wäre der positive Zweig zu erwarten. Es gibt keine Dateiabfrage und keine Veränderung persönlicher Daten. Ein gesonderter Beispieltest wird nicht behauptet.

Die Bedingung prüft nur die Länge des Textes. Sie bestätigt weder Format noch Vertrauenswürdigkeit seines Inhalts.

## 6. Typische Anwendungsfälle

- Leere optionale Eingaben behandeln.
- Bekannte Ganzzahlwerte vergleichen.
- Eine normale Bedienmeldung anhand eines Dateizustands wählen.
- Kontrollfluss in einem eigenen Skript erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

`test -f` bestätigt keine sichere Quelle und verhindert kein späteres Austauschen des Pfads. Für empfindliche Dateien müssen Öffnung und Validierung passend verbunden sein.

Unquotierte Variablen können die Argumentzahl und Bedeutung verändern. Eine leere Eingabe ist deshalb kein Grund, Anführungszeichen wegzulassen.

## 8. Häufige Fehler

- **Fehlende Leerzeichen bei `[`/`]`:** Falsche Argumentstruktur.
- **Textvergleich statt Zahlenvergleich:** Passenden Operator wählen.
- **Symlinkziel übersehen:** `-f` und `-L` fragen Verschiedenes.
- **Wahrheitswert als Inhaltsprüfung:** Die Aussage ist enger.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einzelnen, quotierten Bedingungen beginnen. Für Bash-spezifische Ausdrücke kann `[[ ... ]]` andere Regeln und Möglichkeiten bieten; nicht beide Sprachen gedankenlos mischen.

Ein fehlgeschlagener späterer Dateizugriff muss trotz vorherigem Test behandelt werden. Der frühere Test garantiert den Zugriff nicht.

## 10. Verwandte Befehle

- `true`, `false`: Feste Statuswerte.
- `expr`: Ausdrucksausgabe mit anderer Statusbedeutung.
- `stat`: Dateimetadaten lesen.
- `help test`: Lokale Bedingungen nachschlagen.

**Prüfstand:** Lokale Hilfe gelesen. Keine sensible Datei aufgrund einer bloßen Vorprüfung geöffnet oder verändert.

Ausgangsdatensatz 368 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
