---
id: "swapoff"
name: "swapoff"
command: "swapoff"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "swapoff"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 246
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# swapoff – Aktive Swapbereiche kontrolliert deaktivieren

## 1. Kurzbeschreibung

`swapoff` deaktiviert ausgewählte Swapbereiche. Es ist eine privilegierte Speicherverwaltungsaktion und kein Anzeigeprogramm. Die Aktion löscht nicht automatisch die Swapdatei und macht gespeicherte Inhalte nicht sicher unsichtbar.

## 2. Was macht der Befehl?

Der Kernel muss ausgelagerte Seiten anderweitig unterbringen. Reicht der verfügbare Speicher nicht, kann die Deaktivierung scheitern oder erhebliche Last erzeugen. Alle Bereiche mit -a abzuschalten ist wesentlich umfassender als ein einzelnes Ziel. Konfiguration für den nächsten Start und gegenwärtiger Aktivzustand sind getrennte Dinge.

Quelle, am 2026-11-13 gelesen: [swapoff/swapon-Projekthandbuch](https://manpages.debian.org/trixie/mount/swapoff.8.en.html)

## 3. Syntax

```text
swapoff [OPTIONEN] SWAPDATEI_ODER_GERAET
swapoff -a
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-a`, `--all` | Alle bekannten Swapbereiche deaktivieren; ausdrücklich kein Lernaufruf. |
| `-v`, `--verbose` | Ablauf melden, verhindert keine Änderung. |
| `-L LABEL`, `-U UUID` | Ziel über Kennung wählen; Eindeutigkeit und tatsächlichen Bereich prüfen. |
| `--help`, `--version` | Dokumentation beziehungsweise Version, ohne Deaktivierungsauftrag. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Planfrage: einzelner aktiver Swapbereich soll deaktiviert werden
Fiktiver Status 2: Speicher reicht für swapoff nicht aus
```

Der dokumentierte Status 2 ab util-linux 2.36 kennzeichnet unzureichenden Speicher. Status 4 beschreibt andere swapoff-Systemaufruffehler, 8 andere Systemfehler, 16 Aufruffehler. Bei --all unterscheiden 32/64 vollständiges/teilweises Fehlschlagen. Der Status wurde hier nicht erzeugt; keine Speicherbelastung wurde ausgelöst.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Wartungsplanung:** Austausch eines Swapbereichs bei gesicherter Speicherreserve planen. **Fehlerklärung:** Aktivzustand von Dateiinhalt und Startkonfiguration unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Swapabschaltung kann Prozesse unter Speicherdruck bringen. Nicht mit -a experimentieren und nicht nach einem Fehler zusätzlich Last erzeugen. Keine reale Swapkonfiguration, kein Speicherlimit und keine fstab-Zeile verändert. Auch die eigene mkswap-Testdatei wurde nie aktiviert oder deaktiviert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nicht aktiv | Ziel war kein derzeitiger Swapbereich; nichts pauschal aktivieren. |
| Cannot allocate memory | Speicherreserve fehlt; kein Erzwingen. |
| Nach Neustart wieder aktiv | Laufender Zustand und Startkonfiguration getrennt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `swapon` | Aktiviert vorbereiteten Swap. |
| `mkswap` | Initialisiert Header, keine Aktivierung. |
| `free` | Andere Ansicht der Speicherbelegung. |

Ausgangsdatensatz 246 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
