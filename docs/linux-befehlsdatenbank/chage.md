---
id: "chage"
name: "chage"
command: "chage"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer & rechte", "chage"]
status: "Lokale und offizielle Handbücher geprüft; Hilfeaufruf in Sandbox gescheitert; Kontoaktionen offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 100
reviewed_at: "2026-11-13"
locally_checked_version: "Paket passwd 1:4.13+dfsg1-4ubuntu3.2; kein erfolgreicher Programmlauf"
---

# chage – Passwortalter und Kontoablauf getrennt verstehen

## 1. Kurzbeschreibung

`chage` verwaltet Informationen über das Alter eines Passworts und bestimmte Ablaufgrenzen eines lokalen Benutzerkontos. **Für Änderungen sind administrative Rechte nötig.** Die Anzeige der eigenen Ablaufdaten ist grundsätzlich ein anderer, unter geeigneten Bedingungen unprivilegierter Anwendungsfall.

Der Befehl setzt kein neues Passwort. Er verändert Regeln und Zeitpunkte, anhand derer Anmeldemechanismen einen Wechsel verlangen oder Zugang beschränken können. Passwortablauf und Kontoablauf sind unterschiedliche Einstellungen.

## 2. Was macht der Befehl?

Zu den verwalteten Feldern gehören letzter Passwortwechsel, minimale und maximale Gültigkeitsdauer, Warnfrist, Inaktivität nach Passwortablauf und ein separates Kontoablaufdatum. Die Werte stammen aus der lokalen Kontoverwaltung; sie beschreiben nicht automatisch alle zentralen Verzeichnisdienste oder Authentisierungswege.

Primärquellen sind die lokal gelesene chage-Manpage und die [Distributionsreferenz](https://manpages.debian.org/trixie/passwd/chage.1.en.html). Die installierte Paketdatenbank meldet `passwd` in Version `1:4.13+dfsg1-4ubuntu3.2`. Das ist kein durch einen Versionsaufruf bestätigter vollständiger Funktionsnachweis des Programms.

**Wichtig:** Ein Aufruf nur mit Benutzernamen ist keine reine Liste. Ohne passende Optionen kann ein interaktiver Änderungsdialog beginnen. Für die Anzeige ist die ausdrückliche Listenoption vorgesehen.

## 3. Syntax

```text
chage -l LOGIN
chage [AENDERUNGSOPTIONEN] LOGIN
```

Dies sind Syntaxmuster und keine hier ausgeführten Kontenabfragen. `LOGIN` bezeichnet den bewusst gewählten lokalen Kontonamen. Ein leerer oder erratener Name ist keine verlässliche Auswahl. Administrative Änderungen nur mit konkretem Ziel, gewünschter Regel und Wiederanlaufplan durchführen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `-l`, `--list` | Ablaufdaten anzeigen. | Keine automatische Bewertung sämtlicher Anmeldewege. |
| `-d`, `--lastday` | Zeitpunkt des letzten Passwortwechsels setzen. | 0 verlangt einen Wechsel beim nächsten passenden Anmelden; setzt kein neues Passwort. |
| `-m`, `--mindays` | Mindesttage zwischen Passwortwechseln. | Kann einen erneuten Wechsel begrenzen. |
| `-M`, `--maxdays` | Maximale Passwortgültigkeit in Tagen. | -1 hebt diese Gültigkeitsprüfung auf. |
| `-W`, `--warndays` | Warnfrist vor Passwortablauf. | Die tatsächliche Anzeige hängt vom Anmeldeweg ab. |
| `-I`, `--inactive` | Tage nach Passwortablauf bis zur entsprechenden Sperre. | Nicht einfach Tage seit letzter Anmeldung; -1 entfernt diese Grenze. |
| `-E`, `--expiredate` | Eigenständiges Kontoablaufdatum setzen. | -1 entfernt Kontoablauf, nicht alle anderen Regeln. |
| `-h`, `--help` | Hilfe anfordern. | In dieser Sandbox scheiterte bereits die Audit-Schnittstelle vor der Ausgabe. |

Datumswerte gemäß installierter Manpage mit eindeutigem Format wie `YYYY-MM-DD` planen. Numerische Tageswerte und Sonderwerte nicht mit Unixsekunden oder einer beliebigen Frist ab heute verwechseln.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Handbuch statt Konto ändern

```bash
man 1 chage
```

Die Dokumentation erklärt die Optionen, ohne einen Passwortzeitpunkt zu setzen. Fehlt eine lokale Manpage, kann die oben verlinkte Distributionsseite gelesen werden. Für diese Übung ist keine Rechteerhöhung nötig.

### Schritt 2: Ein ausdrücklich fiktives Modell betrachten

Das folgende Muster ist **keine Ausgabe einer echten Kontoabfrage**:

```text
Letzter Passwortwechsel: 2026-10-01
Minimale Gültigkeit: 0 Tage
Maximale Gültigkeit: 90 Tage
Warnfrist: 7 Tage
Inaktivität nach Passwortablauf: 14 Tage
Eigenständiger Kontoablauf: nicht gesetzt
```

Das Modell trennt sechs Felder. Eine Mindestdauer 0 bedeutet, dass dieses Feld keinen zusätzlichen Tagesabstand vor einem erneuten Wechsel verlangt. Eine maximale Dauer von 90 Tagen betrifft dagegen die Passwortgültigkeit.

### Schritt 3: Zeitbezug richtig einordnen

Der rein rechnerische Abstand von 90 Tagen ab 2026-10-01 endet am 2026-12-30. Das wurde separat als Datumsarithmetik geprüft. Es ist keine gemessene Aussage über eine reale Anmeldung oder den genauen Zeitpunkt einer Zugriffssperre.

Die Inaktivitätsfrist beginnt bezogen auf Passwortablauf, nicht auf den letzten interaktiven Login. Ein nicht gesetztes Kontoablaufdatum hebt die Passwortregeln nicht automatisch auf. Für einen echten Kontenplan wären diese Felder und der verwendete Anmeldemechanismus gemeinsam zu bewerten.

### Schritt 4: Den Prüfstand ehrlich festhalten

Es wurde kein realer Benutzer mit `chage -l` abgefragt. Der versuchte reine Hilfeaufruf endete in der Sandbox mit `Cannot open audit interface - aborting.` und Status 1. Dafür wurden weder Privilegien erhöht noch Systemregeln geändert. Die Dokumentation stützt sich auf Handbücher und gekennzeichnete Modelle, nicht auf einen erfolgreichen Kontentest.

## 6. Typische Anwendungsfälle

### Passwortregeln nachvollziehen

Ein zuständiger Administrator oder der berechtigte Benutzer kann Ablaufdaten in ihrem jeweiligen Kontext prüfen. Dabei die lokale Kontoverwaltung von externen Identitätsdiensten unterscheiden.

### Geplanten Passwortwechsel verlangen

Ein später freigegebener Verwaltungsablauf kann einen Wechsel bei der nächsten passenden Anmeldung verlangen. Zugang ohne interaktive Passwortänderungsmöglichkeit muss vorher bedacht werden.

### Befristetes Konto verwalten

Ein eigener Kontoablauf kann zu einem zeitlich begrenzten Zugriff gehören. Laufende Prozesse, alternative Zugänge und die gesamte Rechteentziehung sind trotzdem ein gesondertes Thema.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Zeitpunkte können Benutzer oder Dienste vom Zugang ausschließen. Ein erzwungener Passwortwechsel kann automatisierte Abläufe unterbrechen. Umgekehrt kann das Entfernen einer Ablaufgrenze beabsichtigte Regeln schwächen.

Der Befehl ist keine universelle Kontosperre und beendet nicht automatisch sämtliche bereits laufenden Prozesse. Eine nachgelagerte PAM-, SSH- oder Verzeichnisdienstentscheidung kann zusätzliche Regeln anwenden. Keine echten Konten zum Dokumentationsnachweis verändern. Ein misslungener Hilfsaufruf in einer eingeschränkten Sandbox begründet keine Änderung an Audit- oder Systemberechtigungen.

## 8. Häufige Fehler

- **Passwort- und Kontoablauf gleichgesetzt:** Es sind verschiedene Felder.
- **Inaktivität seit letzter Anmeldung erwartet:** Das beschriebene Feld bezieht sich auf Passwortablauf.
- **`-d 0` als Passwortsetzen verstanden:** Es markiert einen Wechselbedarf.
- **Nur Benutzername zur Anzeige benutzt:** Ein interaktiver Änderungsmodus kann folgen.
- **-1 als vollständige Entsperrung verstanden:** Es betrifft jeweils nur das gewählte Feld.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Handbuch und konkrete Zielregel verstehen. Eine Anzeige von echten Ablaufdaten und jede Änderung als getrennte Schritte behandeln. Vor einer Änderung einen erreichbaren administrativen Wiederanlaufweg und betroffene Dienste berücksichtigen.

**Prüfstand:** Lokale und verlinkte Manpage gelesen, Paketversion festgestellt, fiktiven 90-Tage-Abstand nachgerechnet. Der Hilfeaufruf scheiterte an der Sandbox-Audit-Schnittstelle. Keine Kontodaten angezeigt, kein Passwortalter, Ablaufdatum oder Sperrstatus verändert. Erfolgreicher Programmlauf, Anzeige und Änderungen praktisch offen.

## 10. Verwandte Befehle

- `passwd`: Passwort und bestimmte Passwort-Sperrzustände verwalten.
- `adduser`, `useradd`: Konten anlegen, andere Aufgabe.
- `usermod`: weitere Attribute eines Kontos ändern.
- `id`: Identitäts- und Gruppenzuordnung betrachten, keine Passwortalteranzeige.

Ausgangseintrag: Datensatz 100 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
