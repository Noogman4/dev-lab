---
id: "localectl"
name: "localectl"
command: "localectl"
category: "Systeminformationen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systeminformationen", "localectl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 604
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# localectl – Systemlocale und Tastaturbelegung unterscheiden

## 1. Kurzbeschreibung

localectl fragt Systemvorgaben ab und kann Locale sowie Tastaturbelegung verändern.

## 2. Was macht der Befehl?

Der Client kommuniziert mit systemd-localed. Systemvorgaben sind nicht zwingend die bereits laufende Benutzersitzung. Konsolenbelegung und X11-Belegung sind unterschiedliche Ebenen; automatische Konvertierung kann weitere Einstellungen betreffen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/localectl.1.html)

## 3. Syntax

```text
localectl [OPTIONEN] AKTION
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| status | Vorgaben anzeigen |
| list-locales | Verfügbare Locales |
| set-locale | Systemvorgabe schreiben |
| set-keymap | Konsolenbelegung setzen |
| --no-convert | Automatische Belegungskonvertierung unterbinden |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
localectl status
```

Eine reale Managerabfrage wäre nötig und bleibt offen. Status allein würde keine funktionierende Eingabe in jeder Sitzung beweisen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Konfigurationsbereiche vor einer späteren gezielten Änderung verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Setzaktionen können Eingabe und Anmeldung beeinflussen. Kein Dienstkontakt, keine Localegenerierung und keine Tastaturänderung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bus fehlt | Programmverfügbarkeit ist kein Managernachweis |
| Sitzung unverändert | Vererbung und bereits gestartete Prozesse berücksichtigen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| locale | Aktueller Prozess |
| timedatectl | Andere Systemvorgabe |
| loginctl | Sitzungen |

Ausgangsdatensatz 604 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
