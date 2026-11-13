---
id: "systemd_cgls"
name: "systemd-cgls"
command: "systemd-cgls"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-cgls"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 570
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; reale Cgroups nicht abgefragt"
---

# systemd-cgls – Prozesse nach Cgroups ordnen

## 1. Kurzbeschreibung

systemd-cgls zeigt Inhalte einer Cgroup-Hierarchie als Baum.

## 2. Was macht der Befehl?

Cgroups fassen Prozesse nach Verwaltungs- und Ressourcenbeziehungen zusammen. Das ist ein anderer Baum als die Eltern-Kind-Abstammung von pstree. Eine Untergruppe kann weitere Gruppen enthalten. Sichtbarkeit hängt von Namespace, Cgroup-Mount und Rechten ab.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-cgls-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cgls.1.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-cgls [OPTIONEN] [CGROUP ...]
systemd-cgls --unit UNIT ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --unit | Unterbaum einer Systemunit wählen. |
| --user-unit | Unterbaum einer Benutzerunit wählen. |
| --all | Auch leere Gruppen anzeigen. |
| --full | Zeilen nicht abkürzen. |
| --no-pager | Pager vermeiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-cgls --no-pager --unit TEST.service
```

Das Muster würde die Cgroup einer bekannten Unit lesend betrachten. Es bleibt unausgeführt; die Existenz von TEST.service wird nicht vorausgesetzt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Dienstzugehörigkeit von Prozessen erklären; Cgroup-Baum und Prozessbaum vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Prozessargumente können vertraulich sein. Ein sichtbarer Cgroupname ist keine vollständige Sicherheits- oder Ressourcenfreigabe. Keine Gruppen angelegt, verschoben oder geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Gruppe leer oder fehlt | Unitzustand, Pfad und Namespace prüfen. |
| Baum anders als pstree | Cgroup-Mitgliedschaft und Abstammung unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; reale Cgroups nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pstree | Elternbeziehungen. |
| systemd-cgtop | Ressourcen je Cgroup. |
| systemctl | Unitinformationen. |

Ausgangsdatensatz 570 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
