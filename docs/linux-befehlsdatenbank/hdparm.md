---
id: "hdparm"
name: "hdparm"
command: "hdparm"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "hdparm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 223
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# hdparm – ATA-Informationen von schreibenden Laufwerkseinstellungen trennen

## 1. Kurzbeschreibung

`hdparm` fragt SATA/IDE-Parameter ab und kann sie verändern. Es ist kein universelles Werkzeug für jedes NVMe-, USB- oder RAID-Gerät. Direkte Laufwerksbefehle benötigen passende Rechte und sind keine gewöhnlichen Dateizugriffe.

## 2. Was macht der Befehl?

Bei vielen get/set-Optionen bedeutet ein fehlender Wert Abfrage, ein angehängter Wert dagegen Änderung. Schon ein einzelner zusätzlicher Zahlenwert kann damit den Modus wechseln. Bridge- und Treiberunterstützung beeinflusst die Verfügbarkeit. Ohne Optionen wird eine Gruppe voreingestellter Abfragen angenommen, nicht nur Hilfe angezeigt.

Quelle, am 2026-11-13 gelesen: [hdparm-Projekthandbuch](https://manpages.debian.org/trixie/hdparm/hdparm.8.en.html)

## 3. Syntax

```text
hdparm [OPTIONEN] [GERAET ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i` | Vom Kernel gespeicherte Identifikationsinformationen anzeigen; können älter sein. |
| `-I` | Identifikation direkt vom Laufwerk anfordern; andere Quelle als -i. |
| `-C` | Aktuellen Energiezustand abfragen; keine Zustandsänderung anfordern. |
| `-B [WERT]` | APM abfragen oder mit Wert setzen; Werte haben spezielle Bedeutungen und nicht jedes Gerät unterstützt sie. |
| `--Istdin` | Passend formatierten gespeicherten Identify-Block statt Gerät lesen; muss allein verwendet werden. |
| `-h` | Kurzhilfe anzeigen, kein Gerätetest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Fiktive Identifikation:
Model Number: LERNMODELL
Serial Number: MUSTER123
Power mode: standby
```

Die Felder wären Gerätedaten, aber kein Beleg, dass Schreibcache, Firmware oder physische Gesundheit in Ordnung sind. Ein gespeicherter -i-Bericht und eine direkte -I-Abfrage können zeitlich unterschiedliche Zustände zeigen. Hier wurde auch keine reine Geräteabfrage ausgeführt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Diagnoseberichte lesen:** Modell, Schnittstelle und gespeicherte Identifikation zuordnen. **Energieverwaltung planen:** Nur auf dokumentierter Hardware und mit eigenem Wartungsauftrag Einstellungen beurteilen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Firmware-, Sicherheits-, Kapazitäts- und Schreiboptionen können massiven Datenverlust bis zur Unbenutzbarkeit des Laufwerks verursachen. Energiesparänderungen können Verfügbarkeit und mechanische Last beeinflussen. Benchmarks können Last und Cacheeffekte verursachen. Keine vermeintlichen Tuningwerte blind übernehmen, keine realen Geräte ansprechen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Inappropriate ioctl | Schnittstelle oder Bridge unterstützt Befehl nicht; nicht Schutzprüfungen umgehen. |
| Abfrage wird Einstellung | Option mit Zahlenwert verwendet; Syntax vor Ausführung unterscheiden. |
| NVMe nicht unterstützt | Anderes Protokoll; zuständiges Werkzeug und Handbuch verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `smartctl` | SMART-/Gesundheitsberichte mit eigener Gerätekommunikation. |
| `nvme` | NVMe-spezifische Verwaltung. |
| `lsblk` | Gerätebeziehungen auf anderer Ebene anzeigen. |

Ausgangsdatensatz 223 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
