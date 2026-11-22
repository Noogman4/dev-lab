---
id: "quota"
name: "quota"
command: "quota"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "quota"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 239
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; quota fehlt"
---

# quota – Belegung, Softlimit und Hardlimit anzeigen

## 1. Kurzbeschreibung

`quota` zeigt Speicher- und Inodekontingente. Eigene Benutzerquoten benötigen normalerweise kein Root; fremde Benutzer- und Projektquoten unterliegen zusätzlichen Rechten. Der Aufruf ändert keine Grenzen.

## 2. Was macht der Befehl?

Ein Dateisystem kann freie Kapazität haben und einen Benutzer wegen seiner Quote trotzdem beim Schreiben begrenzen. Platzkontingent und Inodekontingent beantworten unterschiedliche Fragen. Die normale Ausgabe verwendet historisch als blocks bezeichnete Größenfelder; Einheit und menschenlesbare Umschaltung beachten. NFS-Quoten können per RPC vom Server abgefragt werden, weshalb ein Anzeigeprogramm nicht automatisch offline ist.

Quelle, am 2026-11-13 gelesen: [quota-tools-Handbuch](https://manpages.debian.org/trixie/quota/quota.1.en.html)

## 3. Syntax

```text
quota [OPTIONEN]
quota -u BENUTZER
quota -g GRUPPE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-u`, `-g`, `-P` | Benutzer-, Gruppen- oder Projektbericht; Rechtebedingungen verschieden. |
| `-l` | Nur lokale Dateisysteme, keine NFS-Quotaabfrage. |
| `-s` | Lesbare Einheiten; gerundete Darstellung nicht als exakte Bytezahl parsen. |
| `-v` | Auch Dateisysteme ohne aktuelle Belegung zeigen. |
| `-q` | Nur Überschreitungen berichten; keine Ausgabe ist keine Vollinventur. |
| `-f DATEISYSTEM ...` | Bericht auf ausgewählte Dateisysteme begrenzen. |
| `-p` | Karenzende als Epochensekunden für Auswertung anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Schema:
Platz benutzt 900 KiB, soft 800 KiB, hard 1000 KiB
Inodes benutzt 12, soft 20, hard 30
```

Hier wäre das Platz-Softlimit überschritten. Ob weiteres Schreiben noch erlaubt wäre, hängt unter anderem von der Karenzfrist ab. Das Inodelimit ist dagegen nicht erreicht. Diese Zahlen gehören zu keinem realen Benutzer; es wird kein Konto abgefragt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Schreibfehler erklären:** Benutzergrenzen von gesamter freier Kapazität unterscheiden. **Eigenen Verbrauch verstehen:** Platz und Dateianzahl getrennt beobachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte enthalten Konten- und Mountinformationen. Entfernte Quellen können Netzverkehr verursachen. -l schränkt NFS ein, aktiviert aber keine Quoten und beseitigt keine fehlenden Rechte. Programm fehlt; keine Benutzer-/Serverabfrage oder Installation durchgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Ausgabe | Keine passende Quote, Filter oder fehlende Unterstützung; Zustand nicht raten. |
| df zeigt noch frei | Dateisystemkapazität und persönliche Grenze verschieden. |
| Viele kleine Dateien scheitern | Inodegrenze kann zuerst greifen. |
| Abfrage hängt | Entfernte Quoten/RPC möglich; keine beliebigen Dienste verändern. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; quota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `edquota` | Grenzen bearbeiten. |
| `repquota` | Gesamtbericht für Verwaltung. |
| `df` | Gesamte Dateisystemkapazität anzeigen. |

Ausgangsdatensatz 239 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
