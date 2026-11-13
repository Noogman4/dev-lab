---
id: "notify_send"
name: "notify-send"
command: "notify-send"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "notify-send"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 263
reviewed_at: "2026-11-13"
locally_checked_version: "notify-send 0.8.3"
---

# notify-send – Passive Desktopbenachrichtigungen senden

## 1. Kurzbeschreibung

notify-send sendet eine Nachricht an den Benachrichtigungsdienst der Benutzersitzung. Es liest nicht bloß einen Status und zeigt keine verlässliche Bestätigungsfrage. Sichtbarkeit und Dauer entscheidet auch der Desktopdienst.

## 2. Was macht der Befehl?

Zusammenfassung und optionaler Nachrichtentext sind Positionsargumente. Der Dienst präsentiert die Nachricht asynchron und kann sie unterdrücken oder in einer Historie speichern. Ein erfolgreicher Sendeaufruf bestätigt nicht, dass ein Mensch die Nachricht gesehen oder verstanden hat. Dringlichkeit ist eine Darstellungsempfehlung, keine garantierte Priorität des Betriebssystems.

Quelle, am 2026-11-13 gelesen: [libnotify-Handbuch](https://manpages.debian.org/trixie/libnotify-bin/notify-send.1.en.html), [Freedesktop-Benachrichtigungsstandard](https://specifications.freedesktop.org/notification/latest/) und lokale Manpage

## 3. Syntax

```text
notify-send [OPTIONEN] ZUSAMMENFASSUNG [TEXT]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-u low/normal/critical` | Dringlichkeit anfordern; Dienst entscheidet Darstellung. |
| `-t MILLISEKUNDEN` | Ablaufzeit anfordern; manche Desktops ignorieren sie. |
| `-a NAME`, `-i ICON` | Anzeigename und Symbol wählen; kein Identitätsnachweis. |
| `-p`, `-r ID` | Dienstkennung ausgeben beziehungsweise vorhandene Meldung ersetzen. |
| `-w` | Auf Schließen warten; kein Lesebeweis. |
| `-A [NAME=]TEXT` | Aktion anbieten, impliziert Warten; Unterstützung und Version prüfen. |
| `--version` | Version ausgeben ohne Benachrichtigung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
notify-send -u low -t 3000 "Lernhinweis" "Ein eigener Test wäre jetzt fertig."
```

Hier wären Titel und Text an den Dienst zu übergeben; 3000 bezeichnet Millisekunden, nicht Sekunden. Es wird kein Popup ausgelöst. Die Meldung wäre lediglich Information und keine Aufforderung, einen Geräte- oder Systemeingriff zu bestätigen.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nachrichtentext kann auf dem Bildschirm, Sperrbildschirm oder in einer Historie sichtbar werden. Keine Passwörter oder vertraulichen Inhalte senden. Viele Nachrichten stören die reale Sitzung. Nicht unterstützte Aktionen oder Zeiten dürfen keine Sicherheitsentscheidung tragen. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Benachrichtigungsdienst | Sitzungsbus oder Dienst fehlt; Root behebt das nicht. |
| Zeit wird ignoriert | Der Server kann eine andere Anzeigedauer vorgeben. |
| Rückgabe erfolgreich, nichts sichtbar | Desktoppolitik, Ruhemodus oder asynchrones Verhalten; kein Beweis einer Anzeige. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** notify-send 0.8.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kdialog` | Interaktive Dialoge mit anderer Statussemantik. |
| `zenity` | GTK-Dialoge. |
| `dbus-send` | Allgemeine D-Bus-Nachrichten ohne komfortable Benachrichtigungsschnittstelle. |

Ausgangsdatensatz 263 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
