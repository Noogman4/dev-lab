---
id: "unalias"
name: "unalias"
command: "unalias"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["unalias", "grundlagen & hilfe"]
status: "Keine persönlichen Aliasdefinitionen verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 371
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# unalias – eine Bash-Abkürzung gezielt entfernen

## 1. Kurzbeschreibung

`unalias` entfernt Aliasdefinitionen aus der aktuellen Shell. **Root-Rechte sind nicht nötig.** Es deinstalliert kein Programm und löscht keine gleichnamige ausführbare Datei.

## 2. Was macht der Befehl?

Die lokale Hilfe `help unalias` beschreibt den gezielten Namen und die Gesamtentfernung. Nach der Entfernung wird ein Name nach den übrigen Shellregeln aufgelöst.

Die Definition in einer Startdatei wird dadurch nicht automatisch entfernt. Eine neu gestartete Shell kann sie deshalb erneut laden. Auch andere bereits laufende Terminals behalten ihren eigenen Zustand.

## 3. Syntax

```bash
unalias NAME
```

`NAME` bezeichnet einen vorhandenen Alias. Vor der Änderung mit `alias NAME` dessen Inhalt ansehen. Bei unbekanntem Namen liefert die Bash-Form einen Fehlerstatus.

## 4. Wichtige Optionen

| Form | Wirkung | Reichweite |
| --- | --- | --- |
| `unalias NAME` | Einzelne Definition entfernen. | Aktuelle Shell. |
| `unalias NAME1 NAME2` | Mehrere Namen entfernen. | Jeder Name einzeln relevant. |
| `unalias -a` | Alle Aliasdefinitionen entfernen. | Breite Sitzungsänderung. |

Eine gezielte Änderung ist übersichtlicher als `-a`, wenn nur ein Name stört. Für Hilfe `help unalias` lesen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  alias netmon_liste='ls -l'
  alias netmon_liste
  unalias netmon_liste
)
```

Die Definition wird ausschließlich in einer Subshell angelegt, angezeigt und entfernt. Dadurch bleibt die persönliche aufrufende Sitzung unverändert. Der Aliasinhalt wird nicht als Verzeichnisauflistung ausgeführt.

Das Beispiel beruht auf der lokalen Hilfe; ein gesonderter Lauf mit persönlichen Aliasen fand nicht statt. Es wird weder eine Startdatei geöffnet noch die dauerhafte Konfiguration verändert.

## 6. Typische Anwendungsfälle

- Eine selbst angelegte temporäre Abkürzung aufheben.
- Überraschende Zusatzoptionen eines Namens diagnostisch abgrenzen.
- Sitzung und dauerhafte Shellkonfiguration unterscheiden.
- Eine eigene Übungsdefinition wieder entfernen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nach Entfernung kann derselbe kurze Name etwas anderes aufrufen. Das kann gewünschte Zusatzoptionen oder Bedienhilfen entfallen lassen. Vor einem folgenden Arbeitsaufruf deshalb die neue Auflösung mit `type` betrachten.

`-a` betrifft auch andere persönliche Aliase dieser Sitzung. Nicht pauschal verwenden, nur weil eine einzelne Abkürzung unklar ist.

## 8. Häufige Fehler

- **Datei entfernt erwartet:** Nur Aliasliste geändert.
- **Neue Shell wieder gleich:** Startkonfiguration lädt erneut.
- **Andere Sitzung beeinflusst erwartet:** Shellzustände sind getrennt.
- **Name hat danach gleiche Wirkung:** Funktion oder externe Datei kann weiterhin existieren.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Definition anzeigen, dann nur den betroffenen Namen entfernen. Für eine einmalige gewünschte andere Ausführung kann ein bewusster Aufrufweg geeigneter sein als das Umbauen der Sitzung.

Dauerhafte Änderungen in Startdateien separat planen. Keine ganze Konfigurationsdatei löschen, um einen einzelnen Alias loszuwerden.

## 10. Verwandte Befehle

- `alias`: Definition anzeigen oder setzen.
- `type`: Tatsächliche Namensauflösung betrachten.
- `command`: Bestimmte Aufrufregeln verwenden.
- `help`: Builtin-Dokumentation.

**Prüfstand:** Lokale Hilfe gelesen. Kein persönlicher Alias und keine Startdatei geändert.

Ausgangsdatensatz 371 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
