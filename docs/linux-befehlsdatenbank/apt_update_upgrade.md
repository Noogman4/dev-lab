---
id: "apt_update_upgrade"
name: "apt update upgrade"
command: "apt update && apt upgrade"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: true
risk_level: "caution"
tags: ["aufgabenorientierte hilfe", "apt_update_upgrade"]
status: "Ausgearbeitet; Quellen geprüft; Aktualisierung nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 48
reviewed_at: "2026-11-13"
locally_checked_version: "APT 2.8.4; Hilfe und Version geprüft"
---

# apt update / apt upgrade – Paketwissen und installierte Software getrennt aktualisieren

## 1. Kurzbeschreibung

Der Datenbankeintrag `apt update upgrade` bezeichnet eine Aufgabe mit **zwei getrennten APT-Unterbefehlen**. `update` aktualisiert die lokalen Paketlisten. `upgrade` installiert verfügbare Aktualisierungen anhand dieses Wissens.

**Beide normalen systemweiten Aktualisierungsschritte benötigen Root-Rechte.** Lesende Übersichten und geeignete Simulationen brauchen sie gewöhnlich nicht. Die Aufgabe ist weder nur lesend noch durch einen einzelnen Aufruf `apt update upgrade` korrekt beschrieben.

## 2. Was macht der Befehl?

`apt update` lädt Informationen aus konfigurierten Paketquellen und verändert den lokalen Index. Dadurch werden noch keine neuen Programmversionen installiert. `apt upgrade` berechnet anschließend einen Aktualisierungsplan für installierte Pakete und führt ihn nach Bestätigung aus.

Bei `apt upgrade` können erforderliche neue Abhängigkeiten installiert werden; vorhandene Pakete werden dabei nicht einfach für die Auflösung entfernt. `apt full-upgrade` kann dagegen Entfernungen einplanen. Diese Unterscheidung ist nicht mit jedem Detail von `apt-get upgrade` gleichzusetzen.

Grundlagen: [APT-Handbuch](https://manpages.debian.org/trixie/apt/apt.8.en.html), [APT-Get-Referenz](https://manpages.debian.org/trixie/apt/apt-get.8.en.html) und [Authentifizierung der Paketquellen](https://manpages.debian.org/trixie/apt/apt-secure.8.en.html). Lokal wurden nur Hilfe und Version von APT 2.8.4 geprüft.

## 3. Syntax

```text
sudo apt update
sudo apt upgrade
```

Die Schritte zunächst getrennt betrachten und ihre Meldungen jeweils lesen. Die bekannte Shell-Verknüpfung lautet:

```bash
sudo apt update && sudo apt upgrade
```

`&&` startet den zweiten Aufruf nur bei erfolgreichem Abschlussstatus des ersten. Es garantiert nicht, dass jede Paketquelle frisch und ohne Warnung aktualisiert wurde. Ein Update mit Teilproblemen kann ältere Indexstände weiterverwenden; Meldungen deshalb zusätzlich beurteilen.

## 4. Wichtige Optionen

| Aufruf oder Option | Aufgabe | Konkreter Hinweis |
| --- | --- | --- |
| `apt update` | Paketindex aktualisieren. | Netzwerk- und Systemschreiboperation. |
| `apt list --upgradable` | Bekannte Aktualisierungen auflisten. | Beruht auf lokalem Index, nicht auf einem unabhängigen Echtzeitcheck. |
| `apt -s upgrade` | Plan simulieren. | Keine echte Paketskript- und Dienstprüfung. |
| `apt upgrade` | Aktualisierungen durchführen. | Kann Dienste und laufende Programme betreffen. |
| `apt full-upgrade` | Auch mit möglichen Entfernungen auflösen. | Eigene weitergehende Entscheidung, nicht gleichwertiger Ersatz. |
| `--download-only` | Benötigte Pakete nur laden. | Schreibt Cache und nutzt Netzwerk; installiert nicht vollständig. |
| `-y`, `--assume-yes` | Rückfragen weitgehend automatisch bestätigen. | Für erste manuelle Aktualisierung vermeiden. |
| `--no-remove` | Bei geplanten Entfernungen abbrechen. | Zusätzliche Grenze, kein vollständiger Systemschutz. |
| `apt --version` | APT-Version lesen. | Nicht der Aktualisierungsstand aller Pakete. |

Keine Signatur-, Zertifikats- oder Vertrauensprüfungen deaktivieren, nur damit ein fehlerhafter Quellenabruf fortgesetzt wird. Die richtige Ursache muss getrennt geklärt werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Arbeitsfenster und Rückweg planen

Vor einem echten Upgrade wichtige Arbeit speichern, Platzbedarf und geeignete Sicherung prüfen. Nicht parallel mehrere Paketmanager laufen lassen. Die Anleitung führt hier keine Aktualisierung aus.

### Schritt 2: Paketlisten bewusst aktualisieren

```bash
sudo apt update
```

Dieser Schritt würde Netzwerkverbindungen und lokale Indexschreibzugriffe auslösen. Meldungen zu allen benötigten Quellen lesen. Ein bloßes „fertig“ neben einzelnen Warnungen ist kein Nachweis, dass alles frisch eingelesen wurde.

### Schritt 3: Übersicht lesen

```bash
apt list --upgradable
```

Die Liste zeigt bekannte Kandidaten. Zur Herkunft und Version einzelner Pakete gegebenenfalls `apt-cache policy PAKET` lesen. Nicht pauschal jede Fremdquelle als zur Distribution passend voraussetzen.

### Schritt 4: Plan simulieren

```bash
apt -s upgrade
```

Der Plan zeigt mögliche Paketänderungen ohne deren echte Installation. Er ersetzt weder die spätere erneute Zusammenfassung noch einen Test der Paketskripte. Der reale Paketstand kann sich zwischen Planung und Ausführung ändern.

### Schritt 5: Upgrade als eigenen Systemauftrag ausführen

```bash
sudo apt upgrade
```

Nur nach bewusster Entscheidung durchführen. Die aktuelle Zusammenfassung, zusätzliche Pakete und Konfigurationsfragen prüfen. Kein automatisches `-y` als Standard ergänzen.

### Schritt 6: Abschluss und Betrieb prüfen

Fehlermeldungen und Paketkonfiguration beachten. Laufende Anwendungen können alte Bibliotheken nutzen; Dienste oder ein neuer Kernel können einen bewusst geplanten Neustart erfordern. Diesen nicht automatisch aus der Dokumentation heraus ausführen.

## 6. Typische Anwendungsfälle

**Regelmäßige Wartung:** Listenstand und installierte Software in einem geplanten Zeitfenster aktualisieren.

**Gezielte Sicherheitsaktualisierung:** Relevante Distributionshinweise und Paketkandidaten prüfen. Ein erfolgreicher APT-Lauf beweist keine vollständige Sicherheitsbewertung des ganzen Systems.

**Veralteten Paketindex erkennen:** Fehlende neue Kandidaten können mit alten beziehungsweise fehlerhaft aktualisierten Listen zusammenhängen. Update und Upgrade bleiben getrennte Aufgaben.

**Änderungsumfang vorbereiten:** Mit Übersicht und Simulation planen, bevor Systemrechte und echte Paketinstallation eingesetzt werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Netzwerk und Quellenvertrauen

`update` lädt Indexinformationen von konfigurierten Quellen. Unterschiedliche Releases oder fehlerhafte Fremdarchive können ungeeignete Kandidaten liefern. APT-Authentifizierung schützt den vorgesehenen Archivweg, nicht die allgemeine Harmlosigkeit jeder Software.

### Laufender Betrieb

`upgrade` kann Bibliotheken, Programme und Dienste verändern. Konfigurationsfragen betreffen vorhandene lokale Anpassungen. Eine unbedachte Standardantwort kann wichtige Einstellungen verdrängen; den konkreten Unterschied prüfen.

### Unterbrechung und Speicherplatz

Ein voller Datenträger, Stromverlust oder Abbruch kann einen unvollständigen Konfigurationsstand hinterlassen. Sperrdateien nicht blind löschen. Erst tatsächlichen Paketprozess und genaue Meldung beurteilen.

### Zurückgehaltene Pakete

Ein nicht aktualisiertes Paket muss nicht durch ein blindes `full-upgrade` erzwungen werden. Abhängigkeiten, Holds, gestaffelte Veröffentlichung oder Quellenlage können eine Rolle spielen. Weitergehende Schritte separat bewerten.

### Bedingte Verkettung ist keine Vollständigkeitsprüfung

`&&` wertet einen Prozessstatus aus. Es prüft weder alle Warntexte noch die fachliche Eignung des anschließenden Plans. Für einen ersten manuellen Ablauf die beiden Schritte getrennt lesen und entscheiden.

**Root-Rechte sind für echte systemweite Aktualisierungen nötig.** Lesen und Simulieren ist keine Freigabe für Paketänderung oder Neustart.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Quellen nicht erreichbar | Netzwerk-, Server- oder Konfigurationsproblem. | Betroffene Quelle und Meldung prüfen. |
| Signaturfehler | Schlüssel, Releaseinformation oder Quelle passt nicht. | Ursache klären statt Schutz abschalten. |
| Pakete zurückgehalten | Abhängigkeiten oder Verwaltungsentscheidung. | Kandidaten und Plan gezielt prüfen. |
| Sperre belegt | Anderer legitimer Paketprozess. | Dessen Abschluss beziehungsweise Zustand prüfen. |
| Konfiguration unterbrochen | Voriger Lauf nicht fertig. | Paketstatus und konkrete Fehler lesen. |
| Neue Version installiert, altes Verhalten | Laufender Prozess verwendet alten Code. | Geeigneten Neustart separat planen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Update und Upgrade begrifflich und praktisch trennen.
2. Wichtige Arbeit und geeigneten Rückweg vorbereiten.
3. Warnungen zu Paketquellen wirklich lesen.
4. Übersicht und Simulation vor echtem Upgrade nutzen.
5. Kein pauschales Erzwingen, Auto-Yes oder Prüfungs-Bypass.
6. Ergebnis und betroffene Anwendungen nachher gezielt prüfen.

**Prüfstand:** APT-Version 2.8.4 und lokale Hilfe wurden gelesen; offizielle Referenzen wurden geprüft. Keine Paketlisten, Upgrades, Simulationen, Downloads oder Neustarts wurden ausgeführt. Konkrete Kandidaten, Platzbedarf, Paketskripte und Systemverträglichkeit bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt install` | Einzelnen Paketauftrag durchführen. |
| `apt-cache policy` | Versions- und Herkunftsauswahl lesen. |
| `apt-mark showhold` | Explizit gehaltene Pakete ansehen. |
| `dpkg-query` | Installierten Paketstand lesen. |
| `apt-get` | Spezialisierte APT-Oberfläche mit teilweise anderen Upgrade-Regeln. |

Ausgangseintrag: Datensatz 48 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
