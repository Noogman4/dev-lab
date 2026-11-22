---
id: "aa_status"
name: "aa-status"
command: "aa-status"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "safe"
tags: ["aa_status", "firewall & sicherheit"]
status: "Handbücher und lokale Hilfe geprüft; reale Policyabfrage nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 305
reviewed_at: "2026-11-13"
locally_checked_version: "Paket apparmor 4.0.1really4.0.1-0ubuntu0.24.04.9; nur Hilfe gelesen"
---

# aa-status – AppArmor-Status mit klaren Aussagegrenzen lesen

## 1. Kurzbeschreibung

`aa-status` berichtet über den geladenen AppArmor-Zustand und, soweit zugänglich, über zugeordnete Prozesse. Es ändert keine Profile. **Für eine vollständige Abfrage der geschützten Policyinformationen werden entsprechende administrative Rechte benötigt.** Die lokale Hilfe lässt sich ohne solchen Statuszugriff lesen.

Eine erfolgreich angezeigte Anzahl ist noch kein Sicherheitsnachweis für eine bestimmte Anwendung. Profildefinition und tatsächliche Prozessbindung sind getrennte Informationen.

## 2. Was macht der Befehl?

Das Werkzeug betrachtet AppArmor-Kontrollinformationen und für Prozesszuordnungen auch den Prozessbestand. Diese Ansicht kann sich während der Abfrage ändern. Eine Profildatei auf dem Datenträger und ein geladenes Profil sind außerdem nicht derselbe Zustand.

Gelesen wurden die [aa-status-Manpage bei Debian](https://manpages.debian.org/trixie/apparmor/aa-status.8.en.html), die lokale Manpage und die lokale Aufrufhilfe. Der lokale Hilfetext bietet neben der Gesamtansicht unter anderem Auswahl nach Profilen oder Prozessen, Filter und JSON-Ausgabe. Legacy- und neuere Optionen nicht ohne Versionsabgleich mischen.

## 3. Syntax

```text
aa-status [OPTION]
aa-status --help
aa-status --json
```

Die letzten Aufrufe sind unterschiedliche Aktionen: Hilfe erklärt das Werkzeug, JSON fragt Zustände ab. Ein Aufruf ohne Option fordert grundsätzlich eine ausführliche Statusansicht an. Er ist deshalb kein leerer Hilfsaufruf.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `--help` | Unterstützte Aufrufe erklären. | Kein vollständiger Schutzstatus. |
| `--enabled` | Aktivierungszustand über Status melden. | Fehlender Zugriff und deaktiviert sind zu unterscheiden. |
| `--verbose` | Mehrere Statusaspekte anzeigen. | Gesamtzahlen nicht mit Schutz einer konkreten Anwendung gleichsetzen. |
| `--json` | Status maschinenlesbar ausgeben. | Gültige Struktur und Status separat prüfen. |
| `--pretty-json` | JSON lesbarer formatieren. | Kein anderer Sicherheitsumfang. |
| `--show=profiles` | Auswahl auf Profilinformationen richten. | Neuere Hilfeoption; lokale Unterstützung prüfen. |
| `--show=processes` | Prozessinformationen wählen. | Sichtbarkeit und zeitliche Änderungen beachten. |
| `--filter.mode=FILTER` | Nach Modus filtern. | Ausgeblendete Einträge fehlen absichtlich. |

Historische Zähloptionen und moderne Filter sind nicht beliebig über alle Versionen identisch. Ein unbekannter Schalter rechtfertigt keine Änderung an AppArmor oder Kerneldateien.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur die lokale Hilfe lesen

```bash
aa-status --help
```

Das wurde lokal ausgeführt. Die Ausgabe erklärt die Optionen, ohne dass daraus bereits eine reale Profil- oder Prozessinventur folgt. Die Paketversion wurde getrennt aus Paketmetadaten ermittelt, nicht durch eine erfundene Versionsoption.

### Schritt 2: Einen fiktiven Status gedanklich einordnen

Angenommen, eine spätere autorisierte Ansicht würde zehn geladene Profile melden, davon acht im Enforce- und zwei im Complain-Modus. Diese Zahlen sind hier ausdrücklich nur ein Modell.

Die zehn Profile bedeuten nicht, dass zehn Programme gerade laufen. Acht Enforce-Profile bedeuten ebenfalls nicht, dass jeder laufende Prozess eingeschränkt ist. Für eine konkrete Anwendung müsste ihre eigene Profilzuordnung zu diesem Zeitpunkt betrachtet werden.

### Schritt 3: Rückgabestatus nicht vereinfachen

Die Handbücher unterscheiden unter anderem:

| Status | Bedeutung | Sinnvolle Einordnung |
| --- | --- | --- |
| `0` | AppArmor aktiv und Policy geladen. | Keine vollständige fachliche Abnahme aller Regeln. |
| `1` | Nicht aktiv beziehungsweise nicht geladen. | Kontext und konkrete Meldung prüfen. |
| `2` | Aktiv, aber keine Policy geladen. | Anderer Zustand als aktiver Profilschutz. |
| `3` | Kontrollinformationen unter securityfs fehlen. | Umgebung kann unvollständig oder eingeschränkt sein. |
| `4` | Rechte zum Lesen reichen nicht. | Kein Beweis, dass AppArmor deaktiviert wäre. |
| `42` | Interner Fehler. | Nicht als gewöhnlicher negativer Status verstecken. |

Diese Werte wurden nicht durch Statusabfragen provoziert. Für skriptgestützte Auswertung Status, Datenformat und Fehlermeldung gemeinsam behandeln.

## 6. Typische Anwendungsfälle

### Zustandsbericht eines bekannten Systems

Ein ausdrücklich autorisierter lesender Bericht dokumentiert geladenen Modus und Umfang. Zeitpunkt, Umgebung und Rechte gehören zum Bericht.

### Verwechslung von Datei und Laufzeit vermeiden

Ein vorhandenes Profil muss nicht geladen sein. Umgekehrt können geladene Regeln noch von einer früheren gespeicherten Fassung stammen. Keine Seite allein als vollständigen Nachweis benutzen.

### Maschinenlesbare Auswertung

JSON kann strukturierter als eine übersetzte Menschenleseliste sein. Trotzdem Fehlerzustände getrennt erkennen und das tatsächlich gelieferte Schema passend validieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Statusabfrage ist lesend, kann aber interne Programmnamen, Pfade oder Prozessinformationen offenlegen. Ausgaben vor Weitergabe prüfen. Eine Namespace- oder Containeransicht muss nicht mit der vollständigen Hostansicht übereinstimmen.

Profil- und Prozesszahlen verändern sich. Ein gefilterter Bericht kann relevante andere Einträge ausblenden. Weder ein Status 0 noch ein hoher Enforce-Zähler beweist, dass die gewünschte Policy eng genug ist oder alle wichtigen Programme erfasst. Fehlende Leserechte nicht durch ungeplante Sicherheits- oder Systemänderungen „reparieren“.

## 8. Häufige Fehler

- **Keine Rechte als deaktiviert interpretiert:** Status und Fehlerursache unterscheiden.
- **Profilzahl als Prozesszahl gelesen:** Verschiedene Kategorien.
- **Gespeicherte Datei für wirksame Regel gehalten:** Laufzeitzustand gesondert prüfen.
- **Gefilterte Ansicht als Gesamtheit verstanden:** Auswahl dokumentieren.
- **JSON leer oder ungültig ignoriert:** Ausgabe und Abschlussstatus zusammen prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe und eindeutig erklärten Musterzahlen beginnen. Eine reale Statusinventur als eigenen lesenden Auftrag durchführen und nur den benötigten Umfang weitergeben. Zur Statusfrage keine Modi umschalten.

**Prüfstand:** Lokale und verlinkte Manpages sowie lokale Hilfe gelesen. Paketmetadaten nennen AppArmor 4.0.1really4.0.1-0ubuntu0.24.04.9. Keine echte Policy- oder Prozessabfrage, keine Modusänderung, kein Reload. Alle Beispielzahlen sind fiktiv; reale Statuswerte und JSON-Daten praktisch offen.

## 10. Verwandte Befehle

- `apparmor_status`: lokal gleicher Programmeinstieg.
- `aa-complain`, `aa-enforce`: echte Modusänderungen, keine Statusanzeige.
- `apparmor_parser`: Profilverarbeitung und Laden mit eigenem Änderungsbedarf.
- `journalctl`: mögliche Ereignisquelle; Protokolllesen ist ein eigener Auftrag.

Ausgangsdatensatz 305 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
