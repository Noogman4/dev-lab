---
id: "logname"
name: "logname"
command: "logname"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["logname", "grundlagen & hilfe"]
status: "Kein persönlicher Login-Name erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 361
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# logname – den Login-Namen vom aktuellen Ausführungskonto unterscheiden

## 1. Kurzbeschreibung

`logname` gibt den zur Anmeldung ermittelten Benutzernamen aus. Das ist eine andere Frage als die nach der effektiven Identität des aktuellen Prozesses. **Für die normale Anzeige sind keine Root-Rechte nötig.**

## 2. Was macht der Befehl?

Grundlage ist die lokale GNU-Manpage mit Verweis auf die Login-Abfrage. Ein per `sudo` oder auf anderem Weg gestarteter Prozess kann eine andere effektive Identität besitzen als die ursprüngliche Anmeldung.

In nicht interaktiven, isolierten oder unvollständig erfassten Sitzungen kann die Login-Zuordnung fehlen. Das ist kein Beweis für ein unbekanntes Konto oder eine kompromittierte Anmeldung.

## 3. Syntax

```bash
logname
logname --help
```

Ein gewöhnlicher Benutzername ist kein Zielargument zur Kontoverwaltung. Das Programm wechselt oder erstellt keine Identität.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| Ohne Option | Login-Namen abfragen. | Benötigt passende Sitzungsinformation. |
| `--help` | Bedienung anzeigen. | Keine Anmeldung auslösen. |
| `--version` | Programmversion ausgeben. | Kein Identitätsnachweis. |

Für die effektive Identität `whoami` beziehungsweise `id -un` betrachten. `$USER` ist dagegen eine Umgebungsvariable und kein verlässlicher Ersatz für beide Abfragen.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, eine Person meldet sich als `beispielkonto` an und startet später einen ausdrücklich autorisierten Prozess unter anderer Identität. `logname` und `whoami` können dann unterschiedliche Antworten liefern.

Diese Namen sind ein Modell. Für die Dokumentation wurden keine tatsächlichen Login- oder Kontonamen des Rechners erhoben.

Die richtige Schlussfolgerung wäre zunächst: Beide Werkzeuge beantworten unterschiedliche Identitätsfragen. Erst wenn die erwarteten Zusammenhänge bekannt sind, lässt sich eine Abweichung sinnvoll untersuchen.

## 6. Typische Anwendungsfälle

- Anmeldung und effektiven Prozesskontext auseinanderhalten.
- Eine bekannte Sitzung sachlich beschreiben.
- Unterschiede zwischen interaktiver Anmeldung und Hintergrundaufgabe erklären.
- Ein Skript von ungeeigneten Identitätsannahmen befreien.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf ist lesend, kann aber einen persönlichen Namen offenlegen. Für öffentliche Berichte gegebenenfalls eine neutrale Beschreibung verwenden.

Den Login-Namen nicht als alleinige Autorisierungsprüfung für eine sensible Aktion nutzen. Tatsächliche Prozessrechte und vertrauenswürdige Identitätsbindung sind gesondert zu klären.

## 8. Häufige Fehler

- **Gleiche Ausgabe wie `whoami` voraussetzen:** Unterschiedlicher Bezug.
- **Fehler gleich illegale Anmeldung:** Sitzungsdaten könnten fehlen.
- **Variable als Beweis verwenden:** Umweltwerte können verändert sein.
- **Benutzername zum Wechseln anhängen:** Dafür ist das Werkzeug nicht vorgesehen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die benötigte Aussage wählen: ursprüngliche Anmeldung oder aktuelle Ausführung? Für die zweite Frage `id` verwenden.

Eine nicht ermittelbare Anmeldung als solche dokumentieren. Keine künstlichen Sitzungsdaten oder Konten anlegen, nur um eine erwartete Ausgabe zu erhalten.

## 10. Verwandte Befehle

- `whoami`: Effektiven Benutzernamen lesen.
- `id`: Kennungen und Gruppen präzisieren.
- `who`: Erfasste Anmeldesitzungen betrachten.
- `users`: Namen aus erfassten Sitzungsdaten ausgeben.

**Prüfstand:** Lokale Manpage gelesen. Kein Konto abgefragt, geändert oder als tatsächliche Anmeldung behauptet.

Ausgangsdatensatz 361 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
