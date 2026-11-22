---
id: "dbus_send"
name: "dbus-send"
command: "dbus-send"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "dbus-send"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 253
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Version ermittelt"
---

# dbus-send – Typisierte Nachrichten an einen D-Bus senden

## 1. Kurzbeschreibung

`dbus-send` sendet D-Bus-Nachrichten. Eine Methode kann lesen, schreiben, Anwendungen starten oder Dienste steuern. Der ursprüngliche Hinweis sicher lesend ist deshalb zu pauschal. Zugriff auf den eigenen Sessionbus braucht kein Root; Richtlinien des Zielbusses bleiben maßgeblich.

## 2. Was macht der Befehl?

Bus, Zielname, Objektpfad, Schnittstelle und Mitglied sind getrennte Adressbestandteile. Der Sessionbus ist nicht der Systembus. Ohne Typauswahl wird gewöhnlich ein Signal gesendet; --print-reply wählt zugleich method_call und wartet auf Antwort. Die Argumente sind typisiert, etwa string: oder int32:. Leere und verschachtelte Container werden von diesem Werkzeug nicht allgemein unterstützt.

Quelle, am 2026-11-13 gelesen: [offizielles D-Bus-Handbuch zu dbus-send](https://dbus.freedesktop.org/doc/dbus-send.1.html)

## 3. Syntax

```text
dbus-send [BUSOPTIONEN] [--dest=NAME] [--type=TYPE] OBJEKTPFAD SCHNITTSTELLE.MITGLIED [TYP:WERT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--session`, `--system` | Bus ausdrücklich auswählen; Session ist Vorgabe. |
| `--dest=NAME` | Empfänger festlegen; für fast alle sinnvollen Methoden erforderlich. |
| `--type=method_call` | Methodenaufruf statt Signal anfordern; Wirkung hängt vom Empfänger ab. |
| `--print-reply` | Antwort abwarten und menschenlesbar ausgeben; kein Schutz vor Nebenwirkungen. |
| `--reply-timeout=MSEC` | Wartezeit begrenzen, rückgängig macht der Timeout nichts. |
| `--peer=ADRESSE` | Direkter Server statt Bus; keine Hello-Registrierung. |
| `--sender=NAME` | Busnamen vor Versand anfordern; ebenfalls Zustandswirkung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur die Adresse und Typen lesen

Es wird kein echter Bus kontaktiert. Als Lernmuster dient die im Projekthandbuch verwendete Beispielschnittstelle, kein vorhandener Dienst.

```text
Empfänger: org.freedesktop.ExampleName
Objekt: /org/freedesktop/sample/object/name
Mitglied: org.freedesktop.ExampleInterface.ExampleMethod
Argumente: int32:47 und string:hello
```

### Schritt 2: Das erwartete Verhalten bestimmen

Ein wirklicher Methodenaufruf müsste die Signatur des Zielobjekts erfüllen. Erst dessen Schnittstellenvertrag würde erklären, ob eine Antwort und welche Nebenwirkung zu erwarten ist. Der gleiche Text an einen anderen Bus ist ein anderer Auftrag.

### Schritt 3: Nicht senden

Die Syntax wird nur erklärt. Eine timeout-Meldung würde nicht beweisen, dass die Methode nichts ausgeführt hat; Antwortverlust und Ausführung sind verschiedene Ereignisse. Kein Status eines echten Aufrufs wird behauptet.

## 6. Typische Anwendungsfälle

**Schnittstellen verstehen:** Adressierung und Argumenttypen nachvollziehen. **Fehlersuche planen:** Unbekannte Methode von fehlendem Ziel und fehlenden Rechten unterscheiden. Ein Produktionsbus ist kein Lernspielplatz.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nachrichten können echte Desktop-, Netzwerk-, Sitzungs- oder Energieaktionen auslösen. Keine realen Session-/Systembusmethoden senden. --print-reply und ein kurzer Timeout sind keine Simulation. Fremde Strings korrekt als Daten zitieren, nicht zu Shellcode zusammensetzen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ServiceUnknown | Ziel auf diesem Bus nicht vorhanden; nicht automatisch einen Dienst starten. |
| UnknownMethod/InvalidArgs | Schnittstelle, Mitglied oder Signatur passen nicht. |
| AccessDenied | Busrichtlinie oder Empfängerrechte; kein pauschales sudo. |
| Timeout | Ausführung kann bereits begonnen haben; nicht blind wiederholen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für Lernzwecke dokumentierte Beispieladressen als Text behandeln. Vor jedem später gesondert erlaubten Aufruf die Empfängersignatur und Wirkung prüfen. Das Werkzeug ersetzt keine Autorisierung.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Version ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Nachrichtenversand an Session-/Systembus und private Buslaufzeit nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gdbus` | Andere D-Bus-Oberfläche mit Introspektion. |
| `busctl` | Weitere Busverwaltung, ebenfalls mit echten Nebenwirkungen. |
| `dbus-monitor` | Beobachtung kann vertrauliche Nachrichten offenlegen. |

Ausgangsdatensatz 253 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
