---
id: "repquota"
name: "repquota"
command: "repquota"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "repquota"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 241
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; repquota fehlt"
---

# repquota – Quota-Gesamtberichte lesbar auswerten

## 1. Kurzbeschreibung

`repquota` fasst Belegung und Kontingente ausgewählter Dateisysteme zusammen. Es ist ein Berichtswerkzeug, kein Quota-Editor. Für die Verwaltung fremder Benutzer-/Gruppendaten sind besondere Rechte nötig.

## 2. Was macht der Befehl?

Platz und Inodeanzahl haben getrennte Grenzspalten. Zwei Statuszeichen markieren deren Zustand: Das erste bezieht sich auf Platz, das zweite auf Inodes. Übersetzungen numerischer Kennungen in Namen können NSS-Dienste einbeziehen und dauern. `-n` vermeidet diese Namensauflösung, erzeugt aber keine Berechtigung zum Lesen fremder Daten.

Quelle, am 2026-11-13 gelesen: [repquota-Handbuch](https://manpages.debian.org/trixie/quota/repquota.8.en.html)

## 3. Syntax

```text
repquota [OPTIONEN] DATEISYSTEM ...
repquota [OPTIONEN] -a
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-u`, `-g`, `-P` | Benutzer-, Gruppen- oder Projektbericht wählen. |
| `-n` | Numerische Kennungen statt Namensauflösung. |
| `-s` | Lesbare Einheiten; gerundet, nicht unbedingt präzise Bytezahlen. |
| `-p` | Karenzende als Epochensekunden berichten. |
| `-v` | Auch Nullbelegung und mehr Dateiinformationen zeigen. |
| `-a` | Alle passenden schreibbar gemounteten Dateisysteme mit Quoten. |
| `-O csv`, `-O xml` | Dokumentierte Ausgabeformate für Datenverarbeitung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Schematischer Statusteil, keine tatsächliche Tabellenzeile:
ID 1001   +-
Bedeutung: Platzgrenze markiert, Inodegrenze nicht markiert
```

Das Plus signalisiert gemäß Handbuch eine Überschreitung des Softlimits beziehungsweise bei fehlendem Softlimit das Erreichen des Hardlimits. Karenzfristen und exakte Zähler müssten zusätzlich gelesen werden. Die ID ist erfunden; es wurde kein realer Benutzerbestand abgefragt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Kapazitätsbericht:** Grenzen und Verbrauch mehrerer Kennungen vergleichen. **Support:** Inodeüberschreitungen neben Platzproblemen sichtbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgaben können vertrauliche Benutzer- und Mountinformationen offenlegen. Skripte müssen Einheit, Statusspalten und Quotaformat berücksichtigen. Namensauflösung kann externe Dienste benötigen. Kein systemweiter Bericht, keine RPC-Abfrage und keine Quotaänderung durchgeführt; das Programm fehlt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bericht braucht lange | Namensauflösung oder großer Bestand; -n wäre eine bewusst andere Darstellung. |
| Werte erscheinen gerundet | -s verwendet skalierte Einheiten. |
| Pluszeichen falsch interpretiert | Beide Ressourcen und Karenz getrennt auswerten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; repquota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `quota` | Auskunft für einzelne Kennungen. |
| `edquota` | Grenzen verändern. |
| `quotacheck` | Abrechnung scannt und kann schreiben. |

Ausgangsdatensatz 241 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
