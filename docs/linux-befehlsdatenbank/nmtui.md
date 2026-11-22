---
id: "nmtui"
name: "nmtui"
command: "nmtui"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "nmtui"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 438
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# nmtui – Textoberfläche mit echten Verwaltungsaktionen

## 1. Kurzbeschreibung

nmtui ist die Terminaloberfläche von NetworkManager. Menüpunkte können Profile speichern, Verbindungen schalten und den Systemhostname ändern. Eine Textoberfläche ist kein Simulationsmodus.

## 2. Was macht der Befehl?

edit bearbeitet Profile, connect aktiviert oder deaktiviert Verbindungen, hostname setzt den Systemnamen. Die dazugehörigen Aufrufnamen nmtui-edit, nmtui-connect und nmtui-hostname überspringen nur die Menüauswahl. Ein gespeichertes Profil muss nicht aktiv sein; eine aktive Verbindung muss nicht die beabsichtigte DNS-/Routingwirkung besitzen. Funktionen der aktuellen Onlinefassung können in älteren Paketen fehlen.

Quelle, am 2026-11-13 gelesen: [NetworkManager: nmtui-Handbuch](https://networkmanager.dev/docs/api/latest/nmtui.html)

## 3. Syntax

```text
nmtui
nmtui edit [NAME]
nmtui connect [NAME|UUID|GERAET|SSID]
nmtui hostname
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne Aktivität | Menü zur Auswahl öffnen. |
| `edit` | Profile ansehen, hinzufügen, ändern oder löschen. |
| `connect` | Verbindungen aktivieren oder deaktivieren. |
| `hostname` | Systemhostname setzen; echte Systemänderung. |
| `nmtui-edit`, `nmtui-connect` | Direkte Einstiege, keine getrennten Sicherheitsmodi. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nicht gestarteter Menüpfad: nmtui → Verbindung bearbeiten → Lernprofil
Kein Speichern, keine Aktivierung, kein Hostname-Dialog
```

Der Pfad erklärt nur, dass Profilbearbeitung und Verbindungsaktivierung verschiedene Aufgaben sind. Lernprofil ist ein erfundener Name. Die Oberfläche wurde nicht geöffnet; Tastaturverhalten und Bestätigungsdialoge sind daher praktisch offen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Bedienabläufe planen:** Anzeigen, Speichern und Aktivieren voneinander trennen. **Headless-Verwaltung verstehen:** Auch ohne grafischen Desktop bleibt ein Verwaltungsdienst beteiligt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Speichern und Aktivieren können sofort wirksam werden. Anzeigen oder Teilen von WLAN-Zugangsdaten beziehungsweise QR-Codes kann Geheimnisse offenlegen, sofern die Version diese Funktion bietet. Netzwerkrechte können über Polkit vermittelt werden; kein pauschaler sudo-Start nötig. Keine TUI gestartet und keine Sitzung geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| NetworkManager nicht verfügbar | Dienstabhängigkeit klären; hier nicht starten. |
| Profil gespeichert, aber nicht verbunden | Bearbeiten und Aktivieren sind unterschiedliche Schritte. |
| Anzeige unterscheidet sich | Installierte Version und Terminalgröße berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nmcli` | Skriptfähige Oberfläche desselben Dienstes. |
| `nm-connection-editor` | Grafische Profiloberfläche. |
| `nm-online` | Begrenzte Bereitschaftsprüfung. |

Ausgangsdatensatz 438 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
