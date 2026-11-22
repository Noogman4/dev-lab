---
id: "getent"
name: "getent"
command: "getent"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "getent"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 594
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; NSS- und Netzwerkpfade nicht ausgeführt"
---

# getent – Einträge über NSS auflösen

## 1. Kurzbeschreibung

getent fragt Datenbanken über den Name Service Switch der C-Bibliothek ab.

## 2. Was macht der Befehl?

Die Datenquelle folgt /etc/nsswitch.conf und kann lokale Dateien, Verzeichnisdienste oder Netzwerkauflösung umfassen. getent ist deshalb nicht einfach cat /etc/passwd oder eine garantierte Offlineabfrage. Ein Schlüssel begrenzt die Auswahl; ohne Schlüssel wird gegebenenfalls enumeriert.

Quelle, am 2026-11-13 gelesen: [glibc: getent-Handbuch](https://man7.org/linux/man-pages/man1/getent.1.html)

## 3. Syntax

```text
getent [OPTIONEN] DATENBANK [SCHLÜSSEL ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| passwd NAME | Kontoeintrag nach Namen; Quelle über NSS. |
| group NAME | Gruppeneintrag. |
| hosts NAME | Hostauflösung; kann Netzwerkanfragen auslösen. |
| ahosts NAME | Adressauflösung mit anderer API. |
| -s DIENST | GNU-Override eines NSS-Dienstes; gezielt und versionsabhängig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
getent passwd TESTBENUTZER
```

Das Muster wurde nicht ausgeführt. TESTBENUTZER ist ein Platzhalter; selbst eine Kontenabfrage könnte gemäß NSS einen entfernten Dienst kontaktieren. Es wurde kein Konto angelegt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Auflösungswege verstehen; Kontennamen und lokale Dateiinhalte auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Vollständige Benutzer- oder Gruppenlisten sind vertraulich. NSS-Module können weitere Kommunikation auslösen. Fehlende Einträge sind keine Freigabe, Benutzer anzulegen oder Auflösungsregeln zu ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 2 | Ein oder mehrere Schlüssel nicht gefunden. |
| Enumeration nicht unterstützt | Nicht jede Datenbankquelle liefert alle Einträge. |
| Abfrage dauert | NSS-Quellen und Netzwerkabhängigkeiten berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; NSS- und Netzwerkpfade nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| id | Benutzeridentität über weitere Abfragen. |
| getconf | Konfigurationswerte statt NSS. |
| hostnamectl | Hostkonfiguration über Manager. |

Ausgangsdatensatz 594 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
