---
id: "nvme"
name: "nvme"
command: "nvme"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "nvme"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 236
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; nvme fehlt"
---

# nvme – NVMe-Unterbefehle und Zielbereiche unterscheiden

## 1. Kurzbeschreibung

`nvme` aus nvme-cli ist eine Sammlung für NVMe-Controller und Namespaces. Sie umfasst lesende Berichte ebenso wie Formatierung, Firmware- und Namespaceänderungen. Hilfe benötigt kein Root; echte Gerätebefehle haben unterbefehlsspezifische Rechteanforderungen.

## 2. Was macht der Befehl?

Ein Controller und ein Namespace sind unterschiedliche Zielobjekte. NVMe-over-Fabrics kann zudem Netzverbindungen betreffen. Die Hauptseite führt Unterbefehle auf; deren einzelne Handbücher definieren Parameter und Ausgabe. Ein Erfolg eines Leseberichts ist kein Ersatz für Selbsttest, Integritätsprüfung oder unabhängige Datensicherung.

Quelle, am 2026-11-13 gelesen: [nvme-cli-Hauptseite](https://manpages.debian.org/trixie/nvme-cli/nvme.1.en.html), [smart-log](https://manpages.debian.org/trixie/nvme-cli/nvme-smart-log.1.en.html)

## 3. Syntax

```text
nvme UNTERBEFEHL [ZIEL] [OPTIONEN]
nvme PLUGIN UNTERBEFEHL [ZIEL] [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `help` | Verfügbare Befehle beschreiben; keine Geräteinventur nötig. |
| `list` | Geräteübersicht; echter Systemzustand, hier nicht ausgeführt. |
| `id-ctrl`, `id-ns` | Controller- beziehungsweise Namespaceidentifikation anfordern. |
| `smart-log` | Gesundheits-/SMART-Log lesen; Umfang hängt vom Ziel und unterstützten Namespacebezug ab. |
| `format`, `delete-ns` | Destruktive Verwaltungsoperationen, kein Diagnosezusatz. |
| `fw-download`, `fw-commit` | Firmware übertragen beziehungsweise übernehmen; gesondertes Hochrisikoverfahren. |
| `connect`, `disconnect` | Fabrics-Verbindungen verändern; keine Offline-Dokumentationsprobe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Nur Syntaxmuster: nvme smart-log ZIEL
Frage: Welche gespeicherten Gesundheitsinformationen liefert dieses Ziel?
```

Ein Bericht müsste mit Zielidentität, Zeitpunkt und Werkzeugversion dokumentiert werden. Logfelder dürfen nicht pauschal zu einer garantierten Restlebensdauer umgerechnet werden. Das Lesen eines Logs startet nicht denselben Ablauf wie device-self-test. Keine hier dargestellte Information wurde an einem realen Controller ermittelt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Supportbericht vorbereiten:** Identifikation, Log und verwendetes Protokoll trennen. **Speicheraufbau erklären:** Namespace, Controller und Hostpfad unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Format-/Sanitize-, Schreib- und Passthrough-Befehle können Daten zerstören oder laufende Zugriffe unterbrechen. Herstellerplugins haben eigene Semantik. Keine Befehle aus einer anderen NVMe-Version ungeprüft übernehmen. Programm fehlt; kein Gerät, Selbsttest oder Netzwerk angesprochen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unterbefehl fehlt | Version oder Plugin unterscheidet sich; passende Hilfe lesen. |
| Falsches Zielobjekt | Controllerpfad und Namespace verwechselt. |
| Log eingeschränkt | Hardware unterstützt angeforderten Bezug nicht; keine Defaultwerte als Gesundheit interpretieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; nvme fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `smartctl` | Andere Laufwerksdiagnoseoberfläche. |
| `lsblk` | Gerätebeziehungen anzeigen. |
| `hdparm` | ATA-orientiertes Werkzeug, kein gleichwertiger NVMe-Ersatz. |

Ausgangsdatensatz 236 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
