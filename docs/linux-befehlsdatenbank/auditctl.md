---
id: "auditctl"
name: "auditctl"
command: "auditctl"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["auditctl", "firewall & sicherheit"]
status: "Upstream-Handbuch geprüft; keine Änderung am Audit-System"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 307
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# auditctl – Linux-Audit-Regeln und Kernelstatus verwalten

## 1. Kurzbeschreibung

`auditctl` steuert das Audit-System des Linux-Kernels. Es kann den aktuellen Zustand anzeigen, aber auch Ereignisregeln hinzufügen, entfernen oder das Verhalten bei Überlast verändern. Es ist daher ein Verwaltungswerkzeug mit weitreichenden Auswirkungen.

**Für die Kernelverwaltung sind administrative Rechte beziehungsweise die passenden Audit-Capabilities nötig.** Die reine Hilfe benötigt keine Root-Rechte. Eine Betriebssystemprüfung wird hier nicht als Anlass genutzt, Regeln zu ändern.

## 2. Was macht der Befehl?

Linux Audit kann bestimmte Systemereignisse protokollieren. `auditctl` bestimmt unter anderem, welche Ereignisse erfasst werden und wie die Kernelwarteschlange behandelt wird. Der Dienst `auditd` übernimmt eine andere Aufgabe: Er empfängt und speichert Ereignisse.

Das [Upstream-Handbuch auditctl](https://man7.org/linux/man-pages/man8/auditctl.8.html) beschreibt die Optionen. Die [Linux-Audit-Projektübersicht](https://github.com/linux-audit/audit-userspace) erklärt den Zusammenhang von Kernelereignissen und Userspace-Werkzeugen.

Eine sinnvolle Untersuchung unterscheidet Konfiguration, gespeicherte Ereignisse und daraus gezogene Schlüsse. Eine Regel beweist keine lückenlose Aufzeichnung; fehlende Ereignisse beweisen umgekehrt nicht, dass eine Handlung nie stattgefunden hat.

## 3. Syntax

```text
auditctl [OPTIONEN]
auditctl --help
auditctl -s
auditctl -l
```

Die letzten beiden Formen sind lesende Status- beziehungsweise Regelabfragen. Sie werden hier nur erläutert, nicht auf dem laufenden Rechner ausgeführt. Das Werkzeug ist lokal nicht installiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Einordnung |
| --- | --- | --- |
| `--help` | Bedienung zeigen. | Einstieg ohne Regeländerung. |
| `-v` | Programmversion ausgeben. | Nicht mit ausführlicher Ereignisanalyse verwechseln. |
| `-s` | Kernel-Auditstatus lesen. | Warteschlange und Verluste mitbetrachten. |
| `-l` | Aktive Regeln auflisten. | Keine Ereignisliste. |
| `-a` | Eine Ereignisregel ergänzen. | Ändert die Erfassung. |
| `-R DATEI` | Regeln aus Datei anwenden. | Kein bloßer Dateibetrachtungsmodus. |
| `-D` | Regeln und Watches entfernen. | Kann notwendige Überwachung beseitigen. |
| `-e 2` | Konfiguration bis zum Neustart sperren. | Nicht beiläufig ausprobieren. |

Insbesondere `-f 2` betrifft den Panic-Modus bei kritischen Auditfehlern. Solche Einstellungen sind keine gewöhnlichen Diagnoseoptionen. Sie benötigen einen geplanten betrieblichen Umgang mit Ausfällen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen lesenden Auftrag formulieren

Fragestellung: „Ist die erwartete Überwachung derzeit konfiguriert?“ Dafür wären Status und aktive Regeln relevant. Ein automatisches Nachladen einer fremden Regeldatei ist kein Teil dieser Frage.

### Schritt 2: Die geplanten Abfragen verstehen

```text
auditctl -s
auditctl -l
```

Ein später autorisierter Aufruf würde zuerst den Zustand und dann die Regeln liefern. In diesem Dokument wurden beide nicht ausgeführt. Es gibt deshalb keine behaupteten lokalen Regelzahlen oder Verlustzähler.

### Schritt 3: Einen fiktiven Bericht einordnen

Angenommen, ein Bericht enthielte einen erhöhten Verlustzähler. Dann könnte die Ereignismenge unvollständig sein. Es wäre falsch, aus einem leeren Suchergebnis anschließend eine vollständige Entlastung abzuleiten.

Angenommen, eine Regel fehlt. Dann zunächst Sollzustand, Dienstkonfiguration und Ladeweg klären. Ein pauschales Ersetzen sämtlicher Regeln könnte zugleich andere benötigte Prüfungen entfernen.

### Schritt 4: Dauerhaftigkeit getrennt behandeln

Zur Laufzeit gesetzte Regeln und die nach einem Neustart geladenen Dateien sind verschiedene Ebenen. Ein funktionierender Einzelaufruf ist noch keine dauerhafte Einrichtung. Vor Änderungen müssen beide Ebenen bekannt sein.

## 6. Typische Anwendungsfälle

- Erwartete Audit-Erfassung mit einem dokumentierten Sollzustand vergleichen.
- Warteschlangenprobleme vor der Interpretation von Loglücken berücksichtigen.
- Eine fachlich begründete neue Regel zunächst planen und auf einem geeigneten Testsystem bewerten.
- Nachvollziehen, ob ein Verwaltungswerkzeug aktive Regeln oder nur Konfigurationsdateien verändert hat.

Bei Änderungen gehören erwartete Ereignismenge, Datenschutz und Speicherbedarf in die Planung. Ein breit gefasster Filter kann sehr viele Einträge erzeugen und die eigentlich gesuchten Informationen verdecken.

## 7. Risiken, Nebenwirkungen und Vorsicht

Regeln beeinflussen Sichtbarkeit und Last. Unpassende Löschungen können Überwachungslücken schaffen; zu breite Regeln können Ressourcen beanspruchen. Ein Sperrmodus kann nachfolgende Korrekturen bis zum Neustart verhindern.

Auditdaten können Benutzerkennungen, Pfade und Handlungen enthalten. Auch lesende Berichte sind daher vor einer Weitergabe auf vertrauliche Inhalte zu prüfen. Protokollierung ist außerdem keine automatische Verhinderung der erfassten Aktion.

## 8. Häufige Fehler

- **Keine Berechtigung:** Capability- und Ausführungskontext prüfen, nicht Schutzmechanismen abschalten.
- **Regel unwirksam:** Architektur, Filter und Ladereihenfolge sind mögliche Prüfpunkte.
- **Nach Neustart verschwunden:** Laufzeitänderung wurde möglicherweise nicht dauerhaft eingerichtet.
- **Leere Ereignissuche:** Erfassungsumfang und Verluste fehlen als Kontext.
- **Datei nur ansehen wollen:** `-R` führt die enthaltenen Regeln aus.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Handbuch und lesender Bestandsaufnahme beginnen. Änderungen einzeln begründen, ihre erwartete Wirkung beschreiben und einen überprüfbaren Rückweg vorsehen. Keine kopierte Befehlsfolge mit pauschalem Löschen oder Sperren starten.

Für die Auswertung bereits vorliegender Protokolle sind `ausearch` und `aureport` geeigneter. Sie verlangen keine neue Audit-Regel, wenn die benötigten Ereignisse bereits erfasst wurden.

## 10. Verwandte Befehle

- `auditd`: Empfängt und speichert Auditereignisse.
- `augenrules`: Verarbeitet Regeldateien für den Ladeweg.
- `ausearch`: Sucht einzelne zusammengehörige Ereignisse.
- `aureport`: Verdichtet Auditdaten zu Berichten.
- `journalctl`: Liest Journalmeldungen; kein vollständiger Ersatz für Auditdaten.

**Prüfstand:** Quellen geprüft; Werkzeug nicht installiert. Keine Regeln, Dienste, Sicherheitsparameter oder Protokolle des laufenden Systems verändert.

Ausgangsdatensatz 307 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
