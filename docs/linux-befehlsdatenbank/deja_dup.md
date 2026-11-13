---
id: "deja_dup"
name: "deja-dup"
command: "deja-dup"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "deja_dup"]
status: "Quellen und lokale Hilfe geprüft; GUI-Sicherung und Rücksicherung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 64
reviewed_at: "2026-11-13"
locally_checked_version: "Paket 45.2-1build2; lokale Aufrufhilfe geprüft"
---

# Déjà Dup – Persönliche Dateien mit einer grafischen Sicherungsanwendung schützen

## 1. Kurzbeschreibung

Déjà Dup ist eine grafische Anwendung für persönliche Dateisicherungen. Sie bündelt Dateiauswahl, Sicherungsziel, Zeitplanung und Wiederherstellung in einer Oberfläche. **Für die Sicherung eigener zugänglicher Dateien sind keine Root-Rechte nötig.** Ein gestartetes Programm bedeutet noch nicht, dass eine verwertbare Sicherung vorhanden ist.

Der Terminalname lautet `deja-dup`. Ein Desktop kann die Anwendung übersetzt als „Datensicherungen“ anzeigen. Der Eintrag beschreibt keine vollständige Systemabbild-Sicherung und keine garantierte Wiederherstellung eines startfähigen Rechners.

## 2. Was macht der Befehl?

Die Anwendung verwaltet ausgewählte Ordner und übergibt Sicherungsvorgänge an ein Backend. **Die Version ist dabei entscheidend:** Die lokal vorhandene 45.2-Linie wird in der passenden [Debian-Manpage](https://manpages.debian.org/trixie/deja-dup/deja-dup.1.en.html) mit duplicity beschrieben. Die aktuelle [GNOME-Projektseite](https://apps.gnome.org/DejaDup/) nennt für neuere Ausgaben Restic. Deshalb nicht behaupten, jede Version verwende dasselbe Repositoryformat oder dieselben Wiederherstellungswerkzeuge.

Ausgewählte Daten werden am eingestellten Ziel abgelegt. Ausschlüsse, verfügbare Rechte und fehlgeschlagene Einzeldateien beeinflussen den Umfang. Zeitplanung hilft nur, wenn Anwendung und Ziel zum vorgesehenen Zeitpunkt tatsächlich verfügbar sind. Ein abgezogenes Sicherungsmedium kann nicht beschrieben werden.

## 3. Syntax

```text
deja-dup [OPTIONEN]
deja-dup --backup
deja-dup --restore DATEI ...
```

Ohne Aktionsoption öffnet sich üblicherweise die grafische Oberfläche. `--backup` startet dagegen unmittelbar eine Sicherungsaktion anhand bestehender Einstellungen; es ist kein Vorschauaufruf. `--restore` verwendet Dateiangaben für die Wiederherstellung. Einzelheiten anhand der tatsächlich installierten Aufrufhilfe prüfen.

## 4. Wichtige Optionen

| Option | Bedeutung | Wirkung |
| --- | --- | --- |
| `--help` | Kurze Aufrufhilfe anzeigen. | Geeigneter erster Terminalaufruf. |
| `--help-all` | Zusätzliche Framework-Hilfe anzeigen. | Nicht jede Option beschreibt eine Sicherungsfunktion. |
| `--version` | Programmversion anzeigen. | Mit der verwendeten Dokumentation vergleichen. |
| `--backup` | Sicherung unmittelbar beginnen. | Kann Dateien lesen und ein lokales oder entferntes Ziel beschreiben. |
| `--restore` | Wiederherstellung der angegebenen Dateien anstoßen. | Ziel und möglichen Ersatz bestehender Daten prüfen. |

Einige ältere Handbücher nennen GTK-spezifische Hilfeoptionen. Die lokale 45.2-Hilfe zeigt andere Framework-Optionen. Nicht dokumentierte Schalter nicht aus einer anderen Version übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Hilfe statt Sicherungsaktion starten

```bash
deja-dup --help
```

Die lokale Hilfe nennt unter anderem `--backup` und `--restore`. Dadurch lässt sich der Aufruf prüfen, ohne einen Sicherungsauftrag zu starten. Eine Versionsangabe und lesbare Hilfe sagen noch nichts über vorhandene Benutzereinstellungen aus.

### Schritt 2: Einen Testfall planen

Für einen späteren ausdrücklich geplanten GUI-Test einen neuen Übungsordner mit einer unkritischen Testdatei und ein getrenntes leeres Sicherungsziel vorsehen. Nicht als ersten Versuch das ganze Home-Verzeichnis auswählen. Bereits gespeicherte Einstellungen dürfen nicht stillschweigend als passende Testkonfiguration vorausgesetzt werden.

### Schritt 3: Auswahl und Ziel prüfen

Vor dem eigentlichen Start müsste die Oberfläche zeigen, welcher Ordner eingeschlossen, was ausgeschlossen und wohin gesichert wird. Bei einem Netzwerk- oder Cloudziel zusätzlich Konto, Zugriffsrechte und mögliche Übertragungskosten prüfen. Für einen ersten Dateitest reicht ein lokales neues Ziel; dies ersetzt kein dauerhaft getrenntes Backupmedium.

### Schritt 4: Rückgabe prüfen

Nach einer später erfolgreich abgeschlossenen Testsicherung die einzelne Testdatei in einen neuen, getrennten Ordner zurückholen. Anschließend Inhalt vergleichen. Rücksicherung in den ursprünglichen Ordner würde den Vergleich erschweren und könnte vorhandene Dateien ersetzen.

Dieser Ablauf ist ein Testplan. Hier wurde nur die lokale Hilfe aufgerufen; keine Oberfläche bedient, Auswahl geändert oder Sicherung ausgeführt.

## 6. Typische Anwendungsfälle

### Versehentlich überschriebene Dokumente

Aus einem älteren Sicherungsstand eine passende Dateiversion zurückholen. Dazu müssen dieser Stand und die benötigten Zugangsdaten noch vorhanden sein.

### Regelmäßige persönliche Sicherung

Dokumente und andere bewusst ausgewählte Ordner auf ein getrenntes Ziel sichern. Vor dem ersten echten Lauf Ausschlüsse prüfen: Ein optisch großer Sicherungsumfang ist kein Beweis, dass alle wichtigen Dateien enthalten sind.

### Rechnerwechsel

Eine getestete Rücksicherung kann persönliche Dateien übertragen. Anwendungsdaten, Dateirechte und Backend-Kompatibilität müssen dazu gesondert passen; eine Neuinstallation des Betriebssystems wird dadurch nicht automatisch ersetzt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Backups enthalten oft vertrauliche Daten. Verschlüsselung und Aufbewahrung des Passworts bewusst prüfen, nicht nur aus dem Produktnamen ableiten. Ein verlorenes Passwort kann die Wiederherstellung verhindern.

Cloudziele können Daten übertragen und dauerhafte Anmeldung verwenden. Lokale Ziele auf demselben defekten Laufwerk bieten keine unabhängige Ausfallreserve. Alte Stände können durch Aufbewahrungsregeln verschwinden. Wiederherstellung kann bestehende Dateien ersetzen; deshalb eine neue Rückgabeablage bevorzugen.

## 8. Häufige Fehler

- **Falsches Handbuch:** Backend und Oberfläche unterscheiden sich zwischen Programmversionen.
- **Sicherung wird nicht aktuell:** Ziel fehlt, Zeitplanung greift nicht oder Auftrag meldet Fehler.
- **Datei fehlt:** Ausschlüsse, Rechte und gewählten Zeitpunkt prüfen.
- **Vorhandenes Repository wird nicht erkannt:** Andere Version oder anderes Backendformat möglich; nichts neu initialisieren, bevor die Herkunft klar ist.
- **`--backup` als reine Prüfung benutzt:** Der Aufruf ist eine echte Aktion.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit `--help` beginnen. Einen vollständigen kleinen Sicherungs- und Rücksicherungstest planen, bevor echte wichtige Daten davon abhängig gemacht werden. Versionsangaben und Passwortvorsorge zum Backup notieren.

**Prüfstand:** Installiertes Paket 45.2-1build2 festgestellt, lokale Hilfe gelesen und mit Distributions-Manpage sowie aktueller GNOME-Projektbeschreibung verglichen. Keine GUI gestartet, keine Einstellungen gelesen oder verändert, keine Daten gesichert oder wiederhergestellt. Backendwechsel und Formatmigration wurden nicht praktisch geprüft.

## 10. Verwandte Befehle

- `duplicity`: Backend älterer Déjà-Dup-Versionen mit eigener Kommandozeile.
- `restic`: Backend neuerer Ausgaben; nicht automatisch mit älteren Sicherungen kompatibel.
- `borg`: eigenständiges versioniertes Sicherungssystem.
- `timeshift`: Systemwiederherstellung mit anderem Schwerpunkt.
- `cmp`: zwei zurückgeholte eigene Testdateien inhaltlich vergleichen.

Ausgangseintrag: Datensatz 64 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
