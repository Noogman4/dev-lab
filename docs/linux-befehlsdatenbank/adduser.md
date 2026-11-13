---
id: "adduser"
name: "adduser"
command: "adduser"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer & rechte", "adduser"]
status: "Lokale Hilfe, Version und Handbücher geprüft; Kontoänderungen praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 99
reviewed_at: "2026-11-13"
locally_checked_version: "adduser 3.137ubuntu1; nur Hilfe und Version ausgeführt"
---

# adduser – Lokale Benutzerkonten und Gruppenzuordnung geplant verwalten

## 1. Kurzbeschreibung

`adduser` ist unter Debian und Ubuntu ein Verwaltungswerkzeug zum Anlegen lokaler Benutzerkonten. Es kann außerdem bestimmte Gruppen- und Mitgliedschaftsaufgaben übernehmen. **Tatsächliche Konto- oder Mitgliedschaftsänderungen erfordern administrative Rechte.** Hilfe und Version benötigen keine Neuanlage.

Die Bedeutung ist distributionsabhängig. Andere Implementierungen oder direkte `useradd`-Aufrufe besitzen nicht zwangsläufig dieselben Vorgaben und Optionen.

## 2. Was macht der Befehl?

Bei einer normalen Kontoanlage werden unter anderem Benutzerkennung, primäre Gruppe, Login-Shell und Home-Verzeichnis festgelegt. Je nach Modus und Konfiguration können weitere Dateien, Vorlagen, Passwortabfragen oder lokale Abschlussaktionen beteiligt sein. Es wird also mehr verändert als nur eine sichtbare Namenszeile.

Zwei nichtoptionale Namen bedeuten in dieser Werkzeugfamilie dagegen: bestehenden Benutzer zu bestehender Gruppe hinzufügen. `--system` wählt die Regeln für ein Systemkonto, etwa für einen Dienst. Der Modus ist kein allgemeiner sicherer Ausführungskäfig für diesen Dienst.

Primärquellen sind die lokale Manpage und Hilfe zu 3.137ubuntu1 sowie die [Debian-adduser-Referenz](https://manpages.debian.org/trixie/adduser/adduser.8.en.html). Lokale Konfigurationswerte wurden für diese Dokumentation nicht ausgewertet; konkrete UID-Bereiche und Standardpfade deshalb nicht als universelle Vorgabe behaupten.

## 3. Syntax

```text
adduser [OPTIONEN] BENUTZER
adduser --system [OPTIONEN] BENUTZER
adduser BENUTZER GRUPPE
```

Das sind Aktionsmuster und werden hier nicht ausgeführt. Ein einzelner Name und zwei Namen sind unterschiedliche Betriebsarten. Bestehendes persönliches Konto nicht als Übungsziel einsetzen. Zentrale Verzeichnisdienste haben eigene Verwaltungswege; eine lokale Neuanlage ist keine automatische Änderung einer solchen Identität.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `--system` | Systemkonto nach entsprechenden Regeln anlegen. | Vorgaben und vorhandene Paketkonten prüfen. |
| `--uid ID` | Numerische UID festlegen. | Konflikte und bereits zugeordnete Dateien berücksichtigen. |
| `--ingroup GRUPPE` | Bestehende primäre Gruppe nach Namen wählen. | Nicht automatisch eine zusätzliche Gruppe. |
| `--gid ID` | Primäre Gruppe über numerische Kennung wählen. | GID und UID sind verschiedene Identitäten. |
| `--home PFAD` | Home-Pfad festlegen. | Ist ein reales Schreib- und Rechteziel. |
| `--no-create-home` | Automatische Home-Anlage unterdrücken. | Das Konto kann trotzdem entstehen. |
| `--shell PFAD` | Login-Shell wählen. | Verfügbarkeit und beabsichtigte Anmelderegeln prüfen. |
| `--disabled-password` | Passwortsetzung über passwd auslassen. | Andere Authentisierungswege können weiterhin möglich sein. |
| `--disabled-login` | Zusätzlich eine nologin-Shell setzen. | Kein universeller Ersatz für eine umfassende Kontosperrplanung. |
| `--comment TEXT` | Kommentarfeld vorgeben. | Ältere Anleitungen nennen dafür den veralteten Namen --gecos. |
| `--add-extra-groups` | Konfigurierte Zusatzgruppen anwenden. | Kann zusätzliche Rechte verleihen. |

Nicht jede Option gilt in jedem Modus. Insbesondere Systemkontoanlage, normale Anlage und Mitgliedschaftsänderung getrennt betrachten. Eine fehlende Passwortsetzung ist nicht gleichbedeutend mit einem geprüften sicheren Authentisierungskonzept.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Aufrufhilfe und Version lesen

```bash
adduser --help
adduser --version
```

Erwartet werden die unterstützten Betriebsarten und die Versionsinformation. Lokal wurde `adduser version 3.137ubuntu1` gemeldet. Es wird dabei kein Testbenutzer angelegt.

### Schritt 2: Einen fiktiven Kontoplan erstellen

Angenommen, ein isoliertes Labor benötigte später einen eigenen Dienstaccount. Notiere Zweck, verantwortliche Anwendung, benötigte Datenpfade und erlaubte Anmeldeart. Danach klären, ob das zuständige Paket bereits ein passendes Konto verwaltet. Ein zweites gleichartiges Konto kann Berechtigungen unnötig komplizieren.

### Schritt 3: Konto, Dateien und Zugriff getrennt planen

UID und primäre Gruppe bestimmen Identität. Home-Verzeichnis, Dateirechte, zusätzliche Gruppen und Dienstkonfiguration bestimmen weitere Zugriffe. Für einen Dienst sind interaktive Shell und persönliche Benutzerverzeichnisse nicht automatisch erforderlich. Ein Systemkonto besitzt trotzdem die Rechte seiner Dateien und Prozesse.

### Schritt 4: Spätere Prüfung festlegen

Nach einer gesondert freigegebenen Laboranlage wären Kontoattribute, Gruppen, Ablagebesitz und tatsächlich erlaubte Anmeldungen zu prüfen. Dabei keinen bestehenden Benutzer verändern. Der Plan ist kein ausgeführter Nachweis, dass ein Dienst sicher oder funktionsfähig eingerichtet wurde.

## 6. Typische Anwendungsfälle

### Eigenständiges lokales Benutzerkonto

Ein klar getrennter Benutzer benötigt eigene Daten und bewusst gewählte Anmeldung. Die Verwaltungsentscheidung sollte auch Wiederherstellung, Wartung und spätere Entfernung berücksichtigen.

### Dienstkonto

Eine Anwendung erhält eine eigene lokale Identität. Das hilft bei Rechtezuordnung, ersetzt aber keine Begrenzung von Dateizugriff, Netzwerk oder Ausführungsumgebung.

### Mitgliedschaft ergänzen

Ein bestehender Benutzer soll zu einer bestehenden Gruppe gehören. Die Rechte dieser Gruppe vorher verstehen und berücksichtigen, dass laufende Prozesse neue Gruppen nicht automatisch nachträglich übernehmen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Neue Konten und Gruppen beeinflussen Zugriffsentscheidungen. Eine wiederverwendete UID kann alte Dateien wieder einem aktiven Konto zuordnen. Home-Pfade und Shelloptionen können zusätzliche lokale Wirkungen haben. Namensvalidierung nicht umgehen, um einen unklaren Fehler wegzudrücken.

`--disabled-password` verhindert nicht allgemein SSH-Schlüssel, andere PAM-Verfahren oder andere vorgesehene Zugänge. Auch eine nologin-Shell ist keine vollständige Betrachtung aller Dienste und bereits laufenden Prozesse. Kontoanlage nicht durch anschließende Löschung als vermeintlich spurlosen Dokumentationstest behandeln; es können weitere Daten und Zustände entstehen.

## 8. Häufige Fehler

- **Zwei Namen als normale Neuanlage verstanden:** Die Mitgliedschaftsform wurde gewählt.
- **Gleichen Namen mit gleicher Identität gleichgesetzt:** UID/GID und Verzeichnisdienstbezug mitbetrachten.
- **Kein Home trotz Konto:** --no-create-home oder Systemmodus kann das beabsichtigen.
- **Passwort deaktiviert, trotzdem anderer Zugang möglich:** Authentisierungswege getrennt prüfen.
- **Neue Gruppe noch nicht im Prozess:** Bereits laufende Sitzungen behalten ihren früheren Kontext.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe und einem schriftlichen Kontoplan beginnen. Die tatsächliche Anlage nur als bewusst freigegebene Systemänderung ausführen. Für reine Dokumentation weder ein produktives Konto ändern noch zusätzliche privilegierte Gruppen zum Ausprobieren vergeben.

**Prüfstand:** Version 3.137ubuntu1 und lokale Hilfe ausgeführt, lokale und verlinkte Manpages gelesen. Kein Konto oder Home angelegt, kein Passwort gesetzt, keine Shell, UID oder Mitgliedschaft verändert. Praktische Anlage, Anmeldung, Paketintegration und Entfernung bleiben offen.

## 10. Verwandte Befehle

- `useradd`: niedrigeres Werkzeug mit eigener Schnittstelle.
- `addgroup`: lokale Gruppenanlage.
- `id`, `getent passwd`: Identitätsinformationen lesen, gegebenenfalls über Verzeichnisdienste.
- `passwd`: Passwort- und bestimmte Sperrfunktionen, eigener Verwaltungsauftrag.
- `chage`: Passwortalter und Kontoablauf verwalten.

Ausgangseintrag: Datensatz 99 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
