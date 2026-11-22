---
id: "getenforce"
name: "getenforce"
command: "getenforce"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "safe"
tags: ["getenforce", "firewall & sicherheit"]
status: "Upstream-Handbücher geprüft; kein realer Schutzstatus abgefragt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 315
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# getenforce – den aktuellen SELinux-Modus abfragen

## 1. Kurzbeschreibung

`getenforce` meldet den aktuellen globalen SELinux-Modus. Es liest den Zustand und verändert keine Richtlinie. **Root-Rechte sind für diese übliche Statusabfrage nicht nötig.**

Der Befehl beantwortet eine eng begrenzte Frage. Er überprüft nicht sämtliche Schutzregeln, nicht jede Anwendung und nicht den allgemeinen Sicherheitszustand eines Linux-Rechners.

## 2. Was macht der Befehl?

Nach der [Upstream-Manpage zu getenforce](https://man7.org/linux/man-pages/man8/getenforce.8.html) sind die drei Zustände `Enforcing`, `Permissive` und `Disabled` zu unterscheiden. Das [SELinux-Grundlagenhandbuch](https://man7.org/linux/man-pages/man8/selinux.8.html) erläutert die Richtlinienwirkung.

`Enforcing` bedeutet grundsätzlich durchsetzende SELinux-Policy. `Permissive` lässt ansonsten verweigerte Zugriffe zu und kann entsprechende Meldungen erzeugen. `Disabled` bezeichnet einen deaktivierten SELinux-Zustand. Aus keinem dieser Wörter allein ergibt sich, wie eine bestimmte Anwendung tatsächlich eingeschränkt wird.

Ein Rechner kann ein anderes Schutzsystem wie AppArmor verwenden. Ein fehlendes `getenforce` ist daher weder automatisch ein Sicherheitsfehler noch ein Auftrag, SELinux nachträglich einzurichten.

## 3. Syntax

```bash
getenforce
```

Die dokumentierte Kernsyntax benötigt keine Argumente. Der allgemeine Datenbankplatzhalter `getenforce [OPTIONEN] [ARGUMENTE]` wird dadurch präzisiert. Auch ein universelles `--help` wird hier nicht als vorausgesetzte Funktion erfunden.

## 4. Wichtige Optionen

Für den normalen Zweck gibt es keine notwendige Optionsliste. Entscheidend sind vielmehr die Ergebniswerte:

| Anzeige | Bedeutung | Aussagegrenze |
| --- | --- | --- |
| `Enforcing` | Globale Durchsetzung aktiv. | Kein Audit aller Einzelregeln. |
| `Permissive` | Globale Durchsetzung lässt entsprechende Zugriffe zu. | Kein bloßes anderes Anzeigeformat. |
| `Disabled` | SELinux deaktiviert. | Andere Schutzmechanismen separat betrachten. |

Der aktuelle Modus ist von der für einen kommenden Start vorgesehenen Konfiguration zu unterscheiden. Die kurze Ausgabe ersetzt keinen Vergleich beider Ebenen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Statusfrage stellen

Für die Frage nach dem aktuellen globalen SELinux-Modus genügt der oben gezeigte Aufruf. Er wurde hier nicht ausgeführt, weil das Werkzeug lokal nicht installiert ist.

### Schritt 2: Ein fiktives Ergebnis lesen

Angenommen, die Antwort wäre `Enforcing`. Dann wäre die korrekte Notiz: „Zum Abfragezeitpunkt wurde der globale SELinux-Modus Enforcing gemeldet.“ Die weitergehende Behauptung „jede Anwendung ist sicher isoliert“ folgt daraus nicht.

### Schritt 3: Bei fehlendem Werkzeug nicht eingreifen

Eine Meldung wie „Befehl nicht gefunden“ beschreibt zunächst die Verfügbarkeit des Aufrufs. Für eine Bestandsaufnahme erst Distribution und vorgesehenes Schutzkonzept klären. Nicht zur Herstellung einer erwarteten Ausgabe Richtlinien oder Startparameter verändern.

## 6. Typische Anwendungsfälle

- Bei einer autorisierten Diagnose den globalen SELinux-Modus festhalten.
- Eine Anwendungsmeldung im richtigen Schutzkontext einordnen.
- Aktuellen Modus und dokumentierten Sollzustand vergleichen.
- Eine spätere Verwaltungsentscheidung mit einer lesenden Beobachtung vorbereiten.

Dabei Zeitpunkt und Ausführungskontext notieren. Ein Bericht aus einer eingeschränkten Umgebung muss nicht sämtliche Details des Hostsystems zeigen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Abfrage verändert keine Einstellungen. Das praktische Risiko liegt vor allem in einer falschen Schlussfolgerung: Weder ein positives Statuswort noch ein fehlendes Werkzeug beweist für sich die Sicherheit oder Unsicherheit des gesamten Systems.

SELinux bei einer Zugriffsfehlermeldung pauschal abzuschalten kann Schutz entfernen, ohne die eigentliche Ursache zu klären. Eine Statusabfrage ist kein Anlass für eine solche Änderung.

## 8. Häufige Fehler

- **Globale Anzeige mit Einzelprofil verwechseln:** Für einen bestimmten Prozess fehlen weitere Angaben.
- **Startkonfiguration mit Laufzeit gleichsetzen:** Beides kann auseinanderliegen.
- **`Permissive` als vollständige Deaktivierung lesen:** Das sind verschiedene Zustände.
- **Fehlendes Programm als Infektionshinweis deuten:** Paket- und Distributionskontext fehlen.
- **Beliebige Optionen ergänzen:** Die Kernsyntax ist absichtlich einfach.

## 9. Sichere Varianten oder Tipps für Einsteiger

Den kurzen Befehl als reine Beobachtung verwenden. Bei Rückfragen die tatsächlich angezeigte Antwort zitieren und nicht bereits eine Diagnose daraus machen.

Für mehr Kontext ist `sestatus` vorgesehen. Für die Einordnung konkreter Verweigerungen braucht es passende Meldungen und Policykenntnis. Eine Änderung gehört in einen getrennten, begründeten Arbeitsschritt.

## 10. Verwandte Befehle

- `sestatus`: Ausführlichere SELinux-Statusinformationen.
- `setenforce`: Ändert den aktuellen Modus; andere Wirkung.
- `semanage`: Verwaltet bestimmte Policyanpassungen.
- `aa-status`: Status eines anderen Schutzsystems, AppArmor.

**Prüfstand:** Handbücher gelesen. Kein realer SELinux-Zustand abgefragt, kein Schutzsystem installiert und keine Sicherheitskonfiguration verändert.

Ausgangsdatensatz 315 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
