---
id: "swapon"
name: "swapon"
command: "swapon"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "swapon"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 247
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# swapon – Vorbereiteten Swap aktivieren und reine Anzeige unterscheiden

## 1. Kurzbeschreibung

`swapon` aktiviert vorbereitete Swapdateien oder Geräte. Der Anzeigemodus --show ist davon getrennt. Aktivierung ist eine administrative Kerneländerung; die verfügbare Dateigröße allein reicht nicht für eine geeignete Swapdatei.

## 2. Was macht der Befehl?

Die Swapstruktur muss initialisiert und vom Kernel/Dateisystem unterstützt sein. Dateien mit Löchern sowie ungeeignete Copy-on-Write-Layouts können abgelehnt werden. Die Quelle ist keine gewöhnliche Datenablage mehr, sobald der Kernel sie als Swap nutzt. Ein bestehender Suspend-Header kann bei Aktivierung verändert werden.

Quelle, am 2026-11-13 gelesen: [swapon-Projekthandbuch](https://manpages.debian.org/trixie/mount/swapon.8.en.html)

## 3. Syntax

```text
swapon [OPTIONEN] SWAPDATEI_ODER_GERAET
swapon --show[=SPALTEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--show` | Aktive Bereiche anzeigen, statt neue Bereiche aktivieren. |
| `--bytes` | Größen im Anzeigemodus als Bytes darstellen. |
| `-p PRIORITAET` | Priorität bei Aktivierung festlegen; höher hat Vorrang. |
| `-a` | Passende fstab-Bereiche gesammelt aktivieren; große Reichweite. |
| `--discard` | Discard bei Aktivierung/Seitenfreigabe anfordern; eigene Nebenwirkung. |
| `-f`, `--fixpgsz` | Bei Seitenformatabweichung mkswap aufrufen; kann neu initialisieren. |
| `-L`, `-U` | Quelle nach Label/UUID auswählen; tatsächliche Zuordnung prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Fiktiver --show-Auszug:
NAME         TYPE SIZE USED PRIO
LERNSWAP     file   1M   0B   -2
```

Das Schema beschreibt einen angeblich aktiven Bereich, keinen neu anzulegenden Header. USED 0 bedeutet momentan keine gemeldete Belegung, nicht deaktiviert. Die Zahlen sind erfunden und nicht am Host gelesen. Ein mkswap-Aufruf allein würde keinen solchen aktiven Eintrag erzeugen.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Speicherplanung:** Aktivierung, Prioritäten und Startkonfiguration unterscheiden. **Zustandsbericht:** Bereits aktive Bereiche im definierten Ausgabeformat auswerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Aktivierung kann sensible Speicherinhalte auf ein Ziel schreiben; Verschlüsselung und Rechte gehören zum eigenen Betriebsplan. -f kann mehr tun als bloße Fehlerkorrektur eines Parameters. Kein swapon-Test, keine Aktivierung der selbst erzeugten mkswap-Datei, keine fstab- oder Dienständerung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Invalid argument | Header, Löcher, Dateisystembedingungen oder bereits aktiver Zustand prüfen. |
| Datei groß, aber ungeeignet | Logische Größe ist kein Beleg für zulässige physische Dateiabdeckung. |
| Anzeige leer | Keine sichtbaren aktiven Bereiche oder andere Sicht; keine Aktivierung als Probe starten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mkswap` | Schreibt Swapheader ohne Aktivierung. |
| `swapoff` | Deaktiviert aktiven Swap. |
| `free` | Speicherübersicht mit anderer Aggregation. |

Ausgangsdatensatz 247 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
