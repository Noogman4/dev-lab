---
id: "semanage"
name: "semanage"
command: "semanage"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["semanage", "firewall & sicherheit"]
status: "Upstream-Handbücher geprüft; keine Policy- oder Labeländerung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 323
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# semanage – lokale SELinux-Policyanpassungen verwalten

## 1. Kurzbeschreibung

`semanage` verwaltet bestimmte SELinux-Anpassungen, beispielsweise Porttypen, Benutzerzuordnungen oder Vorgaben für Dateikontexte. Es ist kein allgemeiner Ersatz für jede Policyentwicklung.

**Für produktive Änderungen an der Policy sind administrative Rechte erforderlich.** Die Hilfe kann ohne Root-Rechte gelesen werden. Lesende Verwaltungsabfragen können je nach Policyablage ebenfalls besondere Zugriffsrechte benötigen.

## 2. Was macht der Befehl?

Der Unterbefehl wählt den Verwaltungsbereich. `fcontext` betrifft Sollzuordnungen von Pfaden zu Dateikontexten, `port` betrifft Porttypen und `login` die Zuordnung von Linux-Anmeldungen zu SELinux-Identitäten.

Das [semanage-Upstream-Handbuch](https://man7.org/linux/man-pages/man8/semanage.8.html) erläutert die Bereiche. Für das konkrete Beispiel wurde außerdem [semanage-fcontext](https://man7.org/linux/man-pages/man8/semanage-fcontext.8.html) gelesen.

Eine gespeicherte Sollzuordnung und das tatsächlich an einer Datei vorhandene Label sind verschieden. Das Hinzufügen einer Pfadregel bedeutet nicht, dass jeder vorhandene Dateieintrag sofort umgelabelt wurde. Umgekehrt ist eine einmalige Labeländerung nicht automatisch eine dauerhaft passende Sollregel.

## 3. Syntax

```text
semanage --help
semanage BEREICH --help
semanage fcontext --list
semanage fcontext --list --locallist
```

Diese Formen zeigen Hilfe beziehungsweise Zuordnungen. Sie wurden hier nicht ausgeführt, weil `semanage` nicht installiert ist. Die verfügbare Verwaltungsablage wurde ebenfalls nicht untersucht.

## 4. Wichtige Optionen

Die Bedeutung gilt im jeweiligen Unterbefehl; nicht jeder Bereich unterstützt automatisch jede Form.

| Form bei `fcontext` | Wirkung | Abgrenzung |
| --- | --- | --- |
| `--help` | Bereichshilfe zeigen. | Vor Änderungen lesen. |
| `--list` | Zuordnungen auflisten. | Keine direkte Liste sämtlicher aktueller Dateilabels. |
| `--locallist` | Lokale Anpassungen auswählen. | Zusammen mit passender Listenaktion. |
| `--add` | Zuordnung hinzufügen. | Persistente Policyanpassung. |
| `--modify` | Bestehende Zuordnung ändern. | Vorhandenen Eintrag eindeutig bestimmen. |
| `--delete` | Zuordnung entfernen. | Kann gewollte lokale Vorgabe entfernen. |
| `--deleteall` | Lokale Anpassungen entfernen. | Kein sicherer allgemeiner Reparaturschritt. |
| `--type TYP` | SELinux-Typ bestimmen. | Muss zur Aufgabe und Policy passen. |
| `--noreload` | Neuladen nach Commit vermeiden. | Verhindert nicht die Speicherung selbst. |

Pfadmuster bei `fcontext` sind reguläre Ausdrücke. Shell-Platzhalter und reguläre Ausdrücke sind unterschiedliche Sprachen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur lokale Sollanpassungen betrachten

```text
semanage fcontext --list --locallist
```

Dieser geplante Aufruf würde gespeicherte lokale Dateikontextanpassungen anzeigen. Er wurde nicht ausgeführt. Es wird keine tatsächliche lokale Pfadregel behauptet.

### Schritt 2: Eine fiktive Pfadregel einordnen

Angenommen, eine Anwendung nutzt einen bewusst gewählten Datenpfad außerhalb ihres üblichen Ortes. Eine vorhandene Sollregel könnte dafür einen passenden Typ festlegen. Zunächst muss geklärt werden, welche Rechte der Dienst tatsächlich benötigt.

Die Frage lautet nicht: „Welcher besonders großzügige Typ beseitigt die Fehlermeldung?“, sondern: „Welche minimale und vorgesehene Zuordnung passt zum Dienst?“ Eine zu weite Zuordnung kann Schutzgrenzen verschieben.

### Schritt 3: Soll und Ist getrennt vergleichen

Eine spätere Untersuchung würde Sollzuordnung und aktuelle Labels des konkreten Pfades betrachten. Erst danach wäre eine begründete Korrektur zu planen. Das übliche Anwenden von Sollkontexten mit `restorecon` verändert Dateimetadaten und wird hier nicht ausgeführt.

### Schritt 4: Musterreichweite beachten

Eine unpräzise reguläre Pfadregel kann andere Dateien mit erfassen. Lokale fcontext-Regeln haben außerdem besondere Prioritätsregeln. Nicht einfach davon ausgehen, dass der optisch längste Ausdruck immer gewinnt.

## 6. Typische Anwendungsfälle

- Vorhandene lokale SELinux-Anpassungen dokumentieren.
- Eine Dienstverlagerung in einen anderen Datenpfad fachlich vorbereiten.
- Porttypzuordnungen bei einem bewusst geänderten Dienstport betrachten.
- Sollzuordnungen und tatsächliche Dateikontexte auseinanderhalten.

Eine fehlgeschlagene Verbindung beweist nicht, dass eine Porttypzuordnung die Ursache ist. Dienstbindung, Firewall und passende Verweigerungsmeldungen sind andere mögliche Prüfpunkte.

## 7. Risiken, Nebenwirkungen und Vorsicht

Policyanpassungen können Zugriffe erweitern oder legitime Abläufe unterbrechen. Breite Pfadmuster und pauschales Entfernen lokaler Anpassungen haben einen größeren Wirkungsbereich als ein einzelner sichtbarer Fehler.

`semanage import` kann umfangreiche Anpassungen übernehmen. Eine fremde Exportdatei deshalb nicht als unverbindlichen Bericht behandeln. Auch ein Modus ohne Reload ist kein vollständiger Dry-run.

## 8. Häufige Fehler

- **Sollregel hinzugefügt, Istlabel unverändert:** Speicherung und Anwendung sind getrennt.
- **Falsche Syntaxebene:** Bereichshilfe statt universeller Optionsannahmen verwenden.
- **Shellwildcard als Pfadregex:** Muster genau begrenzen und richtig quotieren.
- **Falscher Typ beseitigt Warnung:** Funktionieren beweist keine passende Schutzgrenze.
- **Alles löschen als Rückweg:** Entfernt möglicherweise fremde gewollte Anpassungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst vorhandene Anpassungen lesen und eine konkrete Fragestellung festlegen. Die dienstspezifische SELinux-Dokumentation hinzunehmen, bevor neue Typzuordnungen geplant werden.

Änderungen einzeln mit Ausgangswert und gewünschter Wirkung dokumentieren. Falls die passende Zuordnung unbekannt bleibt, dies als Prüfpunkt festhalten und keine großzügige Freigabe erfinden.

## 10. Verwandte Befehle

- `sestatus`: Allgemeinen SELinux-Zustand lesen.
- `restorecon`: Sollkontexte auf Dateien anwenden; verändernd.
- `matchpathcon`: Erwartete Dateikontexte betrachten.
- `ls -Z`: Vorhandene Kontextanzeige, soweit unterstützt.
- `setsebool`: SELinux-Booleans ändern; anderer Verwaltungsbereich.

**Prüfstand:** Handbücher gelesen. Keine reale Policyablage ausgelesen, keine Zuordnung hinzugefügt und kein Dateikontext verändert.

Ausgangsdatensatz 323 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
