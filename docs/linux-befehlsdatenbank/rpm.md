---
id: "rpm"
name: "rpm"
command: "rpm"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "rpm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 472
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# rpm – RPM-Abfrage, Verifikation und Installation auseinanderhalten

## 1. Kurzbeschreibung

rpm arbeitet mit RPM-Paketarchiven und der installierten RPM-Datenbank. Es löst nicht wie dnf oder zypper automatisch Repositoryabhängigkeiten. Die Operation bestimmt die Bedeutung nachfolgender Optionen.

## 2. Was macht der Befehl?

-q wählt Query, -p darin eine Paketdatei. -i ist ohne Query Installation, innerhalb einer Query Informationsanzeige. Verify vergleicht Dateien mit gespeicherten Metadaten, nicht mit einer unabhängigen vollständigen Sicherheitsreferenz. Verifikationsskripte können dabei Code ausführen; auch dieser Modus ist nicht pauschal wirkungslos.

Quelle, am 2026-11-13 gelesen: [RPM-Projekt: rpm-Handbuch](https://rpm.org/docs/6.0.x/man/rpm.8) und lokale rpm-Manpage

## 3. Syntax

```text
rpm -q [AUSWAHL] [ANZEIGEOPTIONEN]
rpm {-i|-U|-e|-V} [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-qpi DATEI` | Informationen eines nicht installierten Archivs lesen. |
| `-qpl DATEI` | Archiv-Dateiliste anzeigen. |
| `-qp --scripts DATEI` | Installationsskripte anzeigen, nicht starten. |
| `-q --qf FORMAT` | Feldbasierte Ausgabe. |
| `-V` | Installierte Dateien vergleichen; mögliche Verify-Skripte beachten. |
| `-U`, `-e` | Installieren/aktualisieren beziehungsweise entfernen. |
| `--test` | Transaktion prüfen; kein allgemeiner untrusted-Code-Sandboxmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
rpm -qpi ./eigenes-lernpaket.rpm
```

Die angenommene Datei wurde nicht angelegt oder abgefragt. Die Form zeigt Paketmetadaten ohne Installation. Ein verifiziertes Digest oder eine vorhandene Signatur sagt erst zusammen mit einem vertrauenswürdigen Schlüssel und erwarteter Herkunft etwas über Authentizität aus.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**RPM-Archive verstehen:** Name/Version/Release/Architektur und Skripte vor Transaktionen lesen. **Bestand prüfen:** Datenbankzustand von tatsächlicher Anwendungsfunktion trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Skriptlets, Trigger, Plugins und Makros haben eigene Ausführungswege. --justdb verändert die Datenbank und ist kein Dry-run. Keine RPM-Datenbank initialisiert oder repariert, keine Pakete installiert und keine echten Paketdateien verifiziert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Abhängigkeiten fehlen | Resolverfrage; nicht mit --nodeps umgehen. |
| -i falsch eingeordnet | Vorherigen Query-Modus beachten. |
| Verify meldet Konfiguration | Erwartete Änderungen und Manipulation nicht pauschal gleichsetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dnf` | Repository-/Abhängigkeitsverwaltung. |
| `rpmkeys` | Schlüssel und Signaturprüfung. |
| `rpmbuild` | Buildwerkzeug, kein passives Archivlesen. |

Ausgangsdatensatz 472 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
