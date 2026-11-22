---
id: "id"
name: "id"
command: "id"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["id", "grundlagen & hilfe"]
status: "Identitätsabfragen beschrieben; keine Kontoverwaltung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 359
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# id – reale und effektive Benutzer- und Gruppenkennungen lesen

## 1. Kurzbeschreibung

`id` zeigt Benutzer- und Gruppeninformationen. Ohne Benutzerangabe bezieht es sich auf den aktuellen Prozess. **Root-Rechte sind für die üblichen lesenden Abfragen nicht nötig.**

## 2. Was macht der Befehl?

Die lokale GNU-Manpage unterscheidet reale und effektive Kennungen. Die effektive Identität ist für viele Zugriffsentscheidungen relevant; sie kann vom ursprünglichen Anmeldekontext abweichen.

Mit einem ausdrücklich angegebenen Benutzernamen wird dessen Zuordnung abgefragt. Diese Datenbankansicht ist nicht in jeder Hinsicht identisch mit dem bereits laufenden Prozesskontext einer alten Sitzung.

## 3. Syntax

```bash
id
id -u
id -un
id -G
```

Die Varianten reduzieren die Ausgabe auf bestimmte Angaben. Sie ändern weder Benutzer noch Gruppenzugehörigkeit.

## 4. Wichtige Optionen

| Option | Inhalt | Grenze |
| --- | --- | --- |
| `-u` | Effektive Benutzerkennung. | Numerische Kennung. |
| `-g` | Effektive Gruppenkennung. | Nicht sämtliche Zusatzgruppen. |
| `-G` | Gruppenkennungen. | Prozess- und Datenbankkontext beachten. |
| `-n` | Namen statt Zahlen bei passender Auswahl. | Namensauflösung kann fehlen. |
| `-r` | Reale statt effektiver Kennung bei passender Auswahl. | Bewusst andere Aussage. |
| `-Z` | Sicherheitskontext anzeigen. | Unterstützung der Umgebung erforderlich. |

Eine UID allein beschreibt nicht jede zusätzliche Capability, Sandboxgrenze oder Policyentscheidung.

## 5. Beispiel erklärt Schritt für Schritt

Für die Frage „Unter welcher effektiven numerischen Identität läuft dieser Prozess?“ wäre der passende Aufruf:

```bash
id -u
```

Er würde eine Zahl ausgeben. Für eine menschenlesbare Zuordnung wäre `id -un` die entsprechende Variante. Die konkreten persönlichen Werte des Rechners wurden hier nicht erhoben.

Ein Skript sollte zunächst festlegen, welche Identität tatsächlich relevant ist. Den Login-Namen, eine Umgebungsvariable und die effektive UID als austauschbar zu behandeln wäre falsch.

## 6. Typische Anwendungsfälle

- Den Ausführungskontext eines eigenen Prozesses verstehen.
- Rechteprobleme mit konkreter Kennung beschreiben.
- Namen und numerische Identität unterscheiden.
- Eine beabsichtigte Benutzerumschaltung lesend überprüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Ausgabe ist lesend, kann jedoch Kontonamen und interne Rollen offenlegen. Nur den benötigten Ausschnitt weitergeben.

Eine angezeigte UID `0` beweist in eingeschränkten Umgebungen nicht automatisch unbeschränkte Hostrechte. Namespace-, Capability- und andere Grenzen können weiter gelten. Umgekehrt braucht nicht jede sensible Operation UID `0`.

## 8. Häufige Fehler

- **`-g` mit allen Gruppen verwechseln:** Dafür ist `-G` vorgesehen.
- **Real und effektiv gleichsetzen:** Kontext bewusst wählen.
- **`$USER` als sicheren Ersatz nutzen:** Umgebungsvariable kann abweichen.
- **Identitätsanzeige als Rechteänderung:** Der Befehl ändert nichts.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die konkrete Frage formulieren: Name, numerische Kennung oder Gruppen? Dann die kleinste passende Ausgabe wählen.

Für eine einzelne fehlende Dateiberechtigung nicht sofort den gesamten Prozess privilegieren. Die Identitätsanzeige hilft beim Verständnis, ersetzt aber keine gezielte Ursachenanalyse.

## 10. Verwandte Befehle

- `whoami`: Effektiven Benutzernamen anzeigen.
- `groups`: Gruppenmitgliedschaften betrachten.
- `logname`: Login-Namen mit anderem Bezug lesen.
- `sudo`, `su`: Identitätsbezogene Ausführung verändern.

**Prüfstand:** Lokale Manpage gelesen. Keine Konten, Gruppen oder Prozessrechte verändert.

Ausgangsdatensatz 359 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
