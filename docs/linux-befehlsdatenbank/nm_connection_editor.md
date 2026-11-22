---
id: "nm_connection_editor"
name: "nm-connection-editor"
command: "nm-connection-editor"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "nm-connection-editor"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 411
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# nm-connection-editor – NetworkManager-Profile grafisch bearbeiten

## 1. Kurzbeschreibung

nm-connection-editor ist ein GTK-Editor für gespeicherte NetworkManager-Verbindungsprofile. Er kann hinzufügen, ändern und löschen. Die Oberfläche ist deshalb kein ausschließlich lesendes Diagnosewerkzeug.

## 2. Was macht der Befehl?

Ein Profil beschreibt gewünschte Einstellungen, eine aktive Verbindung deren aktuelle Nutzung. Die Profil-UUID bezeichnet ein Profil zuverlässiger als ein mehrfach vergebbarer Anzeigename. NetworkManager muss für Profiländerungen laufen. Schreibberechtigungen hängen von Benutzer, Profil und Polkit ab; die gesamte Anwendung mit sudo zu starten ist kein sinnvoller Standard. Speichern kann nachfolgende Aktivierungen verändern, auch wenn die aktuelle Verbindung zunächst weiterläuft.

Quelle, am 2026-11-13 gelesen: [NetworkManager-Applet-Handbuch](https://manpages.debian.org/bookworm/network-manager-gnome/nm-connection-editor.1.en.html) und lokale Manpage; neuere Webpfade waren nicht erreichbar. Handbuchstand ist keine ausgeführte Programmversion

## 3. Syntax

```text
nm-connection-editor [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--edit=UUID` | Bestimmtes vorhandenes Profil im Editor öffnen. |
| `--create` | Neues Profil zur Bearbeitung anlegen; Speichern ist eine echte Änderung. |
| `--type=TYP` | Typ für --create oder --show; allein laut Manpage wirkungslos. |
| `--show` | Typgruppe der Profilliste hervorheben/aufklappen. |
| `--type=802-3-ethernet` | Beispiel für einen NetworkManager-Einstellungstyp, kein Interfacename. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nm-connection-editor --edit=PROFIL-UUID
```

Das Muster setzt eine vorher eindeutig bestimmte Profil-UUID voraus und würde ein Fenster öffnen. Für diese Aufgabe wurde kein Fenster gestartet. Vor echtem Speichern wären insbesondere Adressvergabe, DNS, Routen, Autoconnect und Zugangsdaten zu prüfen; eine Profiländerung ist nicht gleichbedeutend mit einer bereits getesteten aktiven Verbindung.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Profilstruktur erklären: Gespeicherte Parameter und aktuelle Netzlage auseinanderhalten. Änderungen vorbereiten: Ein konkretes Profil identifizieren, statt ähnliche Namen zu verwechseln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Löschen oder Ändern eines Profils kann später Netz-/VPN-Zugriff verhindern. Zugangsdaten und Zertifikatspfade sind vertraulich. Keine echten Profile öffnen, speichern, aktivieren oder entfernen; keine Polkit-, DNS- oder Dienständerungen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Profil nicht gefunden | UUID und Sichtbarkeit im passenden Benutzerkontext prüfen. |
| Speichern gesperrt | Profilrechte/Polkit klären, Schutz nicht umgehen. |
| Option type ohne Wirkung | --create oder --show ist zusätzlich erforderlich. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nmcli` | NetworkManager-Kommandooberfläche. |
| `nmtui` | Textoberfläche mit echten Änderungen. |
| `nm-online` | Wartet auf NetworkManager-Zustände. |

Ausgangsdatensatz 411 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
