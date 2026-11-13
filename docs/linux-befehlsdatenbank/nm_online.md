---
id: "nm_online"
name: "nm-online"
command: "nm-online"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "safe"
tags: ["NetMon Spezial / Diagnoseideen", "nm-online"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 412
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# nm-online – Auf NetworkManager-Zustände warten

## 1. Kurzbeschreibung

nm-online wartet auf einen von NetworkManager gemeldeten Zustand. Es konfiguriert selbst keine Verbindung und ist kein unabhängiger Internet-, DNS- oder VPN-Test. Für die normale Statusabfrage ist kein Root erforderlich.

## 2. Was macht der Befehl?

Im Standardmodus wird auf eine aktive Verbindung gewartet. -s wartet dagegen darauf, dass die anfänglichen verfügbaren Autoconnect-Versuche abgeschlossen sind. Nach diesem Startabschluss kann -s sofort erfolgreich zurückkehren, selbst wenn das Netz später offline ist. Eine aktivierte Verbindung muss auch nicht beide Adressfamilien erfolgreich konfiguriert haben; dies hängt von Profilregeln ab. Solche Regeln werden hier nur erklärt, nicht verändert.

Quelle, am 2026-11-13 gelesen: [NetworkManager: nm-online](https://networkmanager.dev/docs/api/latest/nm-online.html)

## 3. Syntax

```text
nm-online [--quiet] [--timeout SEKUNDEN] [--wait-for-startup]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t SEKUNDEN` | Maximale Wartezeit; sonst kann NM_ONLINE_TIMEOUT oder der Default gelten. |
| `-s` | Startabschluss statt aktuelle Verbindung abwarten. |
| `-q` | Keine normale Ausgabe; Status bleibt auszuwerten. |
| `-x` | Sofort beenden, wenn NetworkManager weder läuft noch verbindet. |
| `-h` | Hilfe lesen ohne Funktionsprüfung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nm-online -q -t 5
```

Das Muster würde bis zu fünf Sekunden warten. Status 0 bedeutet Erfolg nach der gewählten Bedingung, 1 offline/Timeout, 2 einen nicht näher bestimmten Fehler. Es wurde nicht auf den echten Dienst zugegriffen. Auch ein realer Status 0 würde keine erfolgreiche DNS-Auflösung oder erreichbare Webseite nachweisen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Startabhängigkeiten erklären: Bootabschluss von aktueller Konnektivität unterscheiden. Skripte prüfen: Timeout und Exitstatus statt bloßer Textausgabe verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Warten kann Skripte und Startabläufe verzögern. Ein Erfolg darf keine ungeprüften Folgeänderungen auslösen. Keine systemd-Abhängigkeiten, NetworkManager-Profile oder may-fail-Einstellungen zur Demonstration ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Sofortiger Erfolg trotz offline | -s kann früher abgeschlossenen Start melden. |
| Keine Ausgabe | -q ist gewählt; Rückgabestatus lesen. |
| Verbindung da, Dienst unerreichbar | Aktivierung und Ende-zu-Ende-Funktion unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nmcli` | Weitere Status- und Änderungsoberfläche. |
| `networkctl` | Andere Verwaltungssicht, oft systemd-networkd. |
| `ping` | Aktiver ICMP-Test eines konkreten Ziels. |

Ausgangsdatensatz 412 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
