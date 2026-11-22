---
id: "hciconfig"
name: "hciconfig"
command: "hciconfig"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["hciconfig", "hardware"]
status: "Kein Controller geöffnet, zurückgesetzt oder umgeschaltet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 383
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale BlueZ-Manpage gelesen"
---

# hciconfig – ältere Bluetooth-Controlleransicht von Änderungen unterscheiden

## 1. Kurzbeschreibung

`hciconfig` ist eine ältere controllernahe Bluetooth-Oberfläche. Ohne Änderungsunterbefehl kann sie HCI-Informationen anzeigen; andere Formen verändern den Adapter. **Lesende Angaben benötigen nicht pauschal Root, Verwaltungsaktionen verlangen passende Rechte.**

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt grundlegende Angaben wie Adresse, Schnittstellentyp und Zustandsflags. `hciX` ist der Controllername, nicht der Name eines gekoppelten Kopfhörers.

Für moderne BlueZ-Abläufe ist auch `bluetoothctl` relevant. Die Verfügbarkeit einer älteren Oberfläche bedeutet nicht, dass jede dort beschriebene Funktion zur aktuellen Dienstverwaltung passt.

## 3. Syntax

```text
hciconfig
hciconfig -a
hciconfig hciX
```

`hciX` muss durch einen tatsächlich vorhandenen eigenen Controller ersetzt werden. Die Beispiele wurden nicht ausgeführt; keine realen Bluetoothadressen werden ausgegeben.

## 4. Wichtige Optionen

| Form | Wirkung | Grenze |
| --- | --- | --- |
| Ohne Gerät | Grundinformationen der Controller. | Keine fremde Gerätesuche. |
| `-a` | Erweiterte Controllerangaben. | Mehr Kennungen und Details. |
| `GERÄT` | Einen Controller anzeigen. | Richtige Identität wählen. |
| `up`, `down` | Controller öffnen/initialisieren oder schließen. | Echte Zustandsänderung. |
| `reset` | Controller zurücksetzen. | Kann Verbindungen verlieren. |
| `rstat` | Statistikzähler zurücksetzen. | Keine unveränderte Bestandsaufnahme. |
| `--help` | Bedienung lesen. | Keine Umschaltung. |

Einige Unterbefehle lesen ohne Wert und setzen mit Wert. Die Argumentzahl ist deshalb sicherheitsrelevant.

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter `hciconfig -a`-Aufruf würde verfügbare Controller ausführlicher beschreiben. Ein Flag wie `UP` erklärt zunächst den Controllerzustand, nicht jede höhere Bluetoothverbindung.

Ein Kopfhörer kann bekannt, aber getrennt sein, obwohl der Controller aktiv ist. Für eine Verbindungsfrage braucht es die entsprechende Geräteebene.

Der Aufruf wurde hier nicht gestartet. Es wurden keine Adapterinitialisierung und kein Reset zur Herstellung eines erwarteten Zustands ausgeführt.

## 6. Typische Anwendungsfälle

- Einen älteren Bluetooth-Diagnosebericht verstehen.
- Controller und gekoppeltes Endgerät unterscheiden.
- Zustandsflags vor einer geplanten Änderung einordnen.
- Verfügbarkeit und Grenzen älterer Werkzeuge feststellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`down` oder `reset` können Eingabe- und Audiogeräte trennen. Sicherheitsbezogene Unterbefehle nicht verändern, um eine unklare Kopplungsstörung zu umgehen.

Eine ausführliche Ausgabe kann eindeutige Adressen enthalten. Vor Weitergabe nur notwendige Felder übernehmen.

## 8. Häufige Fehler

- **HCI-Name gleich Endgerät:** Unterschiedliche Ebene.
- **Controller aktiv gleich Audio läuft:** Profil und Audiopfad fehlen.
- **Zählerreset als Anzeige:** Verändert Diagnosezustand.
- **Jede Altoption aktuell sinnvoll:** Lokale Version und BlueZ-Konzept beachten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der vorhandenen Beschreibung und einer lesenden Frage beginnen. Für moderne Geräteverwaltung den vorgesehenen BlueZ-Weg verwenden.

Nicht gleichzeitig mehrere Werkzeuge unkoordiniert den Controller umstellen lassen. Eine beobachtete Abweichung zuerst erklären.

## 10. Verwandte Befehle

- `bluetoothctl`: Geräte- und Controllerverwaltung über BlueZ.
- `rfkill`: Funkblockierungen betrachten.
- `btmgmt`: Andere controllernahe Verwaltungsoberfläche.
- `journalctl`: Passende Dienstmeldungen lesen.

**Prüfstand:** Lokale Manpage gelesen. Kein Bluetoothgerät gescannt, verbunden, getrennt oder zurückgesetzt.

Ausgangsdatensatz 383 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
