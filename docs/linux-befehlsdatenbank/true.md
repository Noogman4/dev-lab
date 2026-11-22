---
id: "true"
name: "true"
command: "true"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["true", "grundlagen & hilfe"]
status: "Statussemantik dokumentiert; kein Systemtest daraus abgeleitet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 369
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# true – einen absichtlich erfolgreichen Status liefern

## 1. Kurzbeschreibung

`true` liefert einen erfolgreichen Rückgabestatus. **Root-Rechte sind nicht nötig.** Die gewöhnliche Aktion erzeugt keinen sichtbaren Text und untersucht keine Umgebung.

## 2. Was macht der Befehl?

Nach der lokalen Bash-Hilfe ist der positive Status die beabsichtigte Funktion. Eine Shell kann ihn für Bedingungen oder Kontrollfluss verwenden.

Der Name bedeutet nicht, dass irgendeine äußere Behauptung wahr ist. Insbesondere werden weder Netzwerkzugang noch Dateien, Prüfungen oder Sicherheitszustände bestätigt.

## 3. Syntax

```bash
if true; then
  printf '%s\n' 'Dieser Zweig wird gewählt'
fi
```

In Bash existiert ein Builtin; eine externe Variante kann zusätzlich installiert sein. Hilfeformen daher nicht ohne Prüfung gleichsetzen.

## 4. Wichtige Optionen

Für den normalen Zweck sind keine Optionen nötig.

| Form | Aussage | Grenze |
| --- | --- | --- |
| `true` | Erfolgreicher Status. | Keine äußere Prüfung. |
| `! true` | Shell verneint den Status. | Negativer Bedingungsausgang. |
| `false` | Absichtlich erfolgloser Status. | Gegenteilige feste Funktion. |

`help true` beschreibt das Bash-Builtin, ohne einen tatsächlichen Funktionstest des Systems vorzunehmen.

## 5. Beispiel erklärt Schritt für Schritt

Im gezeigten `if` liefert `true` Status `0`. Die Shell wählt deshalb den positiven Zweig und würde die eigene Meldung ausgeben.

Das Beispiel beschreibt nur den selbst festgelegten Ablauf. Es wurde nicht als unabhängiger Test durchgeführt und bestätigt keine Funktion von NetMon oder des Betriebssystems.

Ein nachfolgender Befehl ersetzt den vorherigen Wert von `$?`. Wenn ein Status für spätere Logik benötigt wird, muss der tatsächlich gemeinte Aufruf unmittelbar ausgewertet werden.

## 6. Typische Anwendungsfälle

- Einen bewusst positiven Kontrollfluss erklären.
- Eine leere zulässige Aktion in einem eigenen Ablauf ausdrücken.
- Einen absichtlich behandelten Status als solchen kennzeichnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die eigentliche Aktion ist klein. Gefährlich kann ihre Verwendung zum Verbergen von Fehlern sein: `OPERATION || true` lässt den Gesamtausdruck erfolgreich erscheinen, obwohl die Operation gescheitert sein kann.

Bei Validierung, Paketbau oder Sicherheitsprüfungen darf eine solche Konstruktion nicht unbegründet den erforderlichen Erfolg ersetzen. Die erwartete Fehlersituation muss ausdrücklich behandelt werden.

## 8. Häufige Fehler

- **Keine Ausgabe gleich keine Wirkung:** Der Status ist relevant.
- **Erfolg gleich geprüfte Funktion:** Hier wurde nichts untersucht.
- **Fehler pauschal mit `|| true` verdecken:** Beweiskraft geht verloren.
- **Status zu spät lesen:** Ein anderer Befehl hat ihn ersetzt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für Lernbeispiele einen klaren `if`-Block verwenden. Fehler realer Aufgaben getrennt berichten, statt sie nur durch einen erfolgreichen Status verschwinden zu lassen.

Für eine tatsächliche Bedingung `test` beziehungsweise die passende Fachprüfung einsetzen. Ein fester Wahrheitswert ist dafür kein Ersatz.

## 10. Verwandte Befehle

- `false`: Fester negativer Status.
- `test`: Reale Bedingung auswerten.
- `:`: Shell-No-op mit eigener Syntax und möglichen Argumentexpansionen.
- `return`: Funktionsstatus festlegen.

**Prüfstand:** Lokale Hilfe gelesen. Keine reale Prüfung unterdrückt und kein Erfolg einer äußeren Operation behauptet.

Ausgangsdatensatz 369 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
