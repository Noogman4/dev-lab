---
id: "users"
name: "users"
command: "users"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["users", "grundlagen & hilfe"]
status: "Keine tatsächliche Sitzungsliste ausgelesen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 374
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# users – Namen aus erfassten Anmeldesitzungen anzeigen

## 1. Kurzbeschreibung

`users` gibt Namen aus erfassten Anmeldesitzungen aus. **Für die normale lesende Abfrage sind keine Root-Rechte nötig.** Das Werkzeug ist keine Liste aller auf dem Rechner vorhandenen Konten.

## 2. Was macht der Befehl?

Nach der lokalen GNU-Manpage wird standardmäßig eine Sitzungsdatenquelle wie `utmp` gelesen. Eine ausdrücklich angegebene Datei kann eine andere passende Datenquelle wählen.

Sitzungserfassung ist nicht in jeder Umgebung gleich vollständig. Eine grafische oder isolierte Sitzung kann anders erscheinen als ein klassischer Terminal-Login. Leere Ausgabe bedeutet daher nicht automatisch, dass niemand den Rechner benutzt.

## 3. Syntax

```bash
users
users --help
```

Allgemein ist außerdem eine geeignete Sitzungsdatei als Argument möglich. Eine gewöhnliche Textdatei mit Namen ist nicht dasselbe Format.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| Ohne Datei | Standard-Sitzungsquelle lesen. | Abdeckung der Quelle berücksichtigen. |
| Mit Datei | Andere passende Quelle lesen. | Inhalt und Zeitraum können abweichen. |
| `--help` | Bedienung anzeigen. | Keine Sitzung anlegen. |
| `--version` | Werkzeugversion zeigen. | Kein Nachweis der Datenvollständigkeit. |

Die Ausgabe enthält Namen, nicht automatisch alle Details zu Terminal, Herkunft und Zeitpunkt.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, eine fiktive Ausgabe enthält denselben Namen zweimal. Das kann zu mehreren erfassten Sitzungen gehören und beweist nicht zwei verschiedene Personen.

Die richtige Einordnung lautet zunächst: Die gewählte Datenquelle meldet entsprechende Einträge. Für eine genauere Sitzungsfrage wäre ein dafür geeignetes Werkzeug wie `who` zu betrachten.

Für diesen Text wurden keine persönlichen Anmeldedaten gelesen. Das Beispiel bleibt ein Modell und ist kein Bericht über den tatsächlichen Rechner.

## 6. Typische Anwendungsfälle

- Eine kurze Übersicht erfasster Namen erhalten.
- Sitzungen von vorhandenen Konten unterscheiden.
- Eine bewusst ausgewählte Sitzungsdatei interpretieren.
- Unterschiede zwischen Rechnerumgebungen erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Namen können personenbezogen sein. Die vollständige Liste nicht ungeprüft öffentlich weitergeben.

Eine leere oder doppelte Anzeige ist kein ausreichender Beweis für einen Angriff. Zunächst Quelle, Aktualität und Sitzungsmodell klären. Das Werkzeug führt keine Authentisierungsprüfung durch.

## 8. Häufige Fehler

- **Alle Konten erwartet:** Angezeigte Sitzungen sind etwas anderes.
- **Doppelter Name gleich Angreifer:** Mehrfachsitzungen möglich.
- **Leer gleich unbenutzt:** Erfassung kann fehlen.
- **Beliebige Datei angeben:** Erwartetes Format muss passen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur für eine konkrete Sitzungsfrage verwenden. Für die aktuelle Prozessidentität `id` oder `whoami` heranziehen.

Sitzungsdateien nicht verändern, um eine Anzeige passend zu machen. Eine unvollständige Datenquelle als Grenze dokumentieren.

## 10. Verwandte Befehle

- `who`: Sitzungen mit mehr Kontext anzeigen.
- `w`: Weitere Sitzungs- und Aktivitätsangaben.
- `logname`: Login-Name der eigenen Zuordnung.
- `id`: Aktuelle oder ausdrücklich gewählte Identität.

**Prüfstand:** Lokale Manpage gelesen. Keine Sitzungsliste veröffentlicht oder Anmeldedatei geändert.

Ausgangsdatensatz 374 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
