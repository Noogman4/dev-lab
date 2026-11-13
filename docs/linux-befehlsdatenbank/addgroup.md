---
id: "addgroup"
name: "addgroup"
command: "addgroup"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer & rechte", "addgroup"]
status: "Lokale Hilfe, Version und Handbücher geprüft; Gruppenanlage praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 98
reviewed_at: "2026-11-13"
locally_checked_version: "adduser/addgroup 3.137ubuntu1; nur Hilfe und Version ausgeführt"
---

# addgroup – Eine lokale Gruppe mit Debian-Werkzeugen anlegen

## 1. Kurzbeschreibung

`addgroup` legt auf Debian- und Ubuntu-Systemen lokale Gruppen an. Es gehört dort zum Paket `adduser` und ergänzt die niedrigeren Verwaltungswerkzeuge um distributionsspezifische Regeln. **Für tatsächliche Änderungen an der lokalen Gruppendatenbank sind administrative Rechte nötig.** Hilfe und Version benötigen keine Gruppenanlage.

Andere Distributionen können unter demselben Namen eine andere Implementierung anbieten. Diese Anleitung beschreibt die lokal geprüfte Debian-/Ubuntu-Familie, nicht beliebige BusyBox- oder andere Varianten.

## 2. Was macht der Befehl?

Eine Gruppe erhält einen Namen und eine numerische GID. Die Auswahl der Kennung richtet sich normalerweise nach Konfiguration und verfügbaren Bereichen. Eine neue leere Gruppe verleiht nicht automatisch jedem Benutzer Zugriff auf Dateien oder Dienste.

Mitglieder, primäre Gruppenzuordnung, Dateigruppenrechte und laufende Prozesszugehörigkeiten sind getrennte Zustände. Ein Name allein ist kein Zugriffsrecht; das System bewertet an vielen Stellen die numerische Kennung und die konkrete Berechtigung.

Gelesene Quellen sind die lokale adduser/addgroup-Manpage und die [Debian-addgroup-Referenz](https://manpages.debian.org/trixie/adduser/addgroup.8.en.html). Lokal wurde Paketversion 3.137ubuntu1 festgestellt. Die aktuelle Webreferenz kann in Einzelheiten von dieser installierten Version abweichen.

## 3. Syntax

```text
addgroup [OPTIONEN] GRUPPE
addgroup --system [OPTIONEN] GRUPPE
```

Dies sind Aktionsmuster, keine hier auszuführenden Übungen. Die Verwendung mit zwei Namen, um einen bestehenden Benutzer zu einer bestehenden Gruppe hinzuzufügen, wird in dieser Werkzeugfamilie über `adduser BENUTZER GRUPPE` dokumentiert. Nicht wahllos Aufrufvarianten anderer Implementierungen übertragen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `--system` | Systemgruppe nach vorgesehenen Regeln anlegen. | Keine automatische Dienstkonfiguration oder besondere Vertrauenswürdigkeit. |
| `--gid ID` | Numerische Gruppenzuordnung ausdrücklich wählen. | Konflikte und bereits von Dateien verwendete IDs berücksichtigen. |
| `--firstgid ID` | Untere Grenze für passende Nichtsystemgruppen vorgeben. | Nicht mit der gewünschten exakten GID verwechseln. |
| `--lastgid ID` | Obere Grenze für passenden Bereich vorgeben. | Nur im unterstützten Modus verwenden. |
| `--conf DATEI` | Andere Konfiguration verwenden. | Kein allgemeiner Modus zur gefahrlosen Simulation. |
| `--quiet` | Meldungsumfang verringern. | Führt die Aktion trotzdem aus. |
| `--help` | Unterstützte Aufrufformen anzeigen. | Keine Gruppenanlage. |
| `--version` | Paket-/Programmversion anzeigen. | Kann den gemeinsamen Namen adduser melden. |

Namensvalidierung nicht durch Ausnahmeschalter umgehen, nur um einen unklaren Fehler zu unterdrücken. Die genauen zulässigen Bereiche und Namen sind Konfigurations- und Versionsfragen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur verfügbare Hilfe ansehen

```bash
addgroup --help
addgroup --version
```

Lokal zeigte die gemeinsame Hilfe unter anderem die Formen zum Anlegen normaler und systembezogener Gruppen. Der Versionsaufruf meldete `adduser version 3.137ubuntu1`. Das ist bei diesem gemeinsamen Programmpaket plausibel und kein Beweis für einen falsch gestarteten Gruppenänderungsauftrag.

### Schritt 2: Einen Plan ohne Datenbankänderung formulieren

Angenommen, ein Laborprojekt benötigt später eine neue lokale Gruppe. Zunächst gewünschten Namen, Zweck, zuständige Mitglieder und benötigte Dateirechte festlegen. Prüfen, ob bereits eine passende Gruppe oder eine zentral verwaltete Identität existiert. In dieser Dokumentationsprüfung wird kein realer Gruppenbestand abgefragt.

### Schritt 3: Gruppe und Mitgliedschaft auseinanderhalten

Die eigentliche Neuanlage wäre eine administrative Änderung. Eine später gewünschte Mitgliedschaft wäre ein zusätzlicher eigener Auftrag. Ein existierender Name beweist noch nicht, dass der betreffende Benutzer Mitglied ist oder dass ein laufender Prozess die neue Zuordnung bereits übernommen hat.

### Schritt 4: Erwartete Nachweise benennen

Ein später ausdrücklich freigegebener Laborversuch müsste die neue Gruppe, richtige GID, gewünschte Mitgliedschaften und tatsächlich benötigten Dateizugriffe prüfen. Eine reine Erfolgsmeldung ersetzt diese fachliche Prüfung nicht. Hier wurde nur die Hilfe-/Versionsphase durchgeführt.

## 6. Typische Anwendungsfälle

### Gemeinsame Projektablage

Eine geplante Gruppe kann für eine bewusst konfigurierte gemeinsame Ablage genutzt werden. Zusätzlich sind Eigentümer, Gruppenrechte, Vererbungsregeln und eventuell ACLs zu planen.

### Konto eines Dienstes vorbereiten

Pakete oder Administratoren können eigene Systemgruppen benötigen. Eine manuelle Gruppe sollte zu den vorhandenen Paket- und Dienstregeln passen; der Schalter `--system` übernimmt diese Abstimmung nicht automatisch.

### Kennungszuordnung dokumentieren

Bei Datenmigrationen können GIDs relevant sein. Nicht nur gleiche Namen vergleichen: Dateien können weiterhin auf eine numerische alte oder anders zugeordnete Kennung verweisen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Gruppen und Mitgliedschaften beeinflussen Zugriff. Manche Gruppen erlauben weitreichende Aktionen; Mitgliedschaften sind deshalb keine bloße Komforteinstellung. Eine spätere Wiederverwendung derselben GID kann vorhandenen Dateien eine unerwartete neue Bedeutung geben.

Änderungen können auch Schatten-Gruppendaten und weitere lokale Verwaltungszustände betreffen. `--conf` leitet nicht automatisch sämtliche systemweiten Schreibzugriffe in eine Übungsdatei um. Kein realer Gruppenversuch zum bloßen Nachweis eines Handbuchbeispiels. `sudo` nicht pauschal vor jede Hilfe oder Diagnose schreiben.

## 8. Häufige Fehler

- **Gruppe existiert bereits:** Zweck und vorhandene Identität prüfen statt Validierung umgehen.
- **GID ist belegt:** Exakte Kennung und Auswahlbereich unterscheiden.
- **Neue Gruppe, aber kein Zugriff:** Mitgliedschaft, Dateirechte und Prozesszustand fehlen möglicherweise.
- **Andere Optionen auf anderem System:** Implementierung und Version unterscheiden sich.
- **Ruhige Ausgabe als Trockenlauf verstanden:** `--quiet` verhindert keine Änderung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe und Dokumentationslesen beginnen. Vor einer tatsächlichen Änderung Zweck und benötigte Rechte konkret festlegen. Neue Gruppen nicht unüberlegt zu bereits privilegierten Mechanismen hinzufügen; die minimal nötige Mitgliedschaft und Ablagerechte planen.

**Prüfstand:** Lokale Hilfe und Version 3.137ubuntu1 ausgeführt, lokale und verlinkte Handbücher gelesen. Keine Gruppe erstellt, gelöscht oder verändert; keine GID vergeben und keine Mitgliedschaft bearbeitet. Praktische Anlage, Konfliktfälle und Zugriffsauswirkungen bleiben offen.

## 10. Verwandte Befehle

- `groupadd`: niedrigeres Gruppenverwaltungswerkzeug mit anderer Schnittstelle.
- `adduser`: auch für dokumentierte Mitgliedschaftsänderungen zuständig.
- `getent group`: Gruppenauflösung lesend betrachten, kann Verzeichnisdienste einbeziehen.
- `id`: Benutzer-/Prozesszuordnungen untersuchen.
- `chgrp`: Dateigruppenzuordnung ändern, eigener Schreibvorgang.

Ausgangseintrag: Datensatz 98 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
