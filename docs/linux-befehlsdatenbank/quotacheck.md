---
id: "quotacheck"
name: "quotacheck"
command: "quotacheck"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "quotacheck"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 240
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; quotacheck fehlt"
---

# quotacheck – Quota-Abrechnung neu ermitteln und Änderungen erkennen

## 1. Kurzbeschreibung

`quotacheck` scannt Belegung und kann Quota-Dateien erzeugen, prüfen und korrigieren. Der Name check bedeutet hier nicht schreibgeschützte Beobachtung. Es ist ein administratives Werkzeug.

## 2. Was macht der Befehl?

Das Programm vergleicht ermittelten Verbrauch mit gespeicherter Abrechnung. Fehlende Quota-Dateien können angelegt werden. Die Manpage warnt vor aktiven Quoten und gleichzeitigen Änderungen. Um eine ruhige Sicht zu erhalten, kann es versuchen, Dateisysteme lesend und danach wieder schreibend zu remounten. Dieser Nebeneffekt ist bereits außerhalb einer zulässigen Dokumentationsprobe.

Quelle, am 2026-11-13 gelesen: [quotacheck-Handbuch](https://manpages.debian.org/trixie/quota/quotacheck.8.en.html)

## 3. Syntax

```text
quotacheck [OPTIONEN] DATEISYSTEM
quotacheck [OPTIONEN] -a
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-u`, `-g` | Benutzer- beziehungsweise Gruppenabrechnung wählen. |
| `-c` | Bestehende Quotadaten nicht einlesen, neu scannen und speichern. |
| `-b` | Vor Überschreiben Quota-Dateisicherung anlegen; kein vollständiges Dateisystembackup. |
| `-m` | Keinen Read-only-Remount versuchen; Konsistenzrisiko bleibt. |
| `-M` | Auch nach fehlgeschlagenem Remount weitermachen; kein Sicherheitsgewinn. |
| `-f` | Auch mit aktiven Quoten schreiben; ausdrücklich riskant. |
| `-a` | Alle passenden gemounteten Nicht-NFS-Dateisysteme auswählen. |
| `-n` | Ersten doppelten Quotaeintrag verwenden; kein Trockenlauf. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundener Abgleich:
gespeicherte Belegung 100
neu ermittelte Belegung 120
mögliche Folge: Quota-Abrechnung wird aktualisiert
```

Diese Zahlen sind nur ein Schema, keine Quota-Einheitenangabe und kein Benutzerbericht. Der Abgleich kann Dateien und Kernel-Abrechnungszustand verändern. Das ist eine andere Aufgabe als das lesende quota. Weder -n noch -m kennzeichnet einen allgemein sicheren Probelauf.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Wartung nach Inkonsistenz:** Abrechnungsdaten unter kontrollierten Bedingungen neu ermitteln. **Fehlende Tabellen:** Geplante Initialisierung eines unterstützten Quotaformats.

## 7. Risiken, Nebenwirkungen und Vorsicht

Scan, Remount und Änderungen sind für diese Aufgabe unzulässig. Fehlerhafte oder parallel veraltende Abrechnung kann Benutzer fälschlich blockieren oder Grenzen umgehen lassen. Keine Quoten abschalten oder Mountoptionen ändern, um ein Beispiel lauffähig zu machen. Programm fehlt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nur Anzeige erwartet, Dateien geändert | Werkzeugfunktion missverstanden; quota/repquota sind andere Programme. |
| Remount scheitert | Aktive Nutzung oder Rechte; nicht mit -M erzwingen. |
| Uneinheitliche Zahlen | Bestand änderte sich während des Scans oder Format passt nicht. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; quotacheck fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `quota` | Benutzerbezogene Auskunft. |
| `repquota` | Zusammenfassender Bericht. |
| `edquota` | Grenzen bearbeiten, nicht Verbrauch frei setzen. |

Ausgangsdatensatz 240 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
