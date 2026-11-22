---
id: "hostnamectl"
name: "hostnamectl"
command: "hostnamectl"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "hostnamectl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 595
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Hostmanager nicht abgefragt"
---

# hostnamectl – Hostnamenanzeige und Hostnamenänderung trennen

## 1. Kurzbeschreibung

hostnamectl fragt Hostinformationen ab und kann Hostnamen sowie weitere Eigenschaften ändern.

## 2. Was macht der Befehl?

Systemd unterscheidet unter anderem statischen, transienten und frei darstellbaren Pretty-Hostnamen. Diese Werte erfüllen unterschiedliche Zwecke. Die aktuelle Online-CLI und ältere lokale Versionen können verschiedene Namen für Setter anbieten. Für einen konkreten Änderungsaufruf gilt die lokale Hilfe.

Quelle, am 2026-11-13 gelesen: [Systemd: hostnamectl-Handbuch](https://man7.org/linux/man-pages/man1/hostnamectl.1.html)

## 3. Syntax

```text
hostnamectl [OPTIONEN] [AKTION]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| status | Hostinformationen anzeigen. |
| --static | Statischen Hostnamen adressieren. |
| --transient | Vorübergehenden Namen adressieren. |
| --pretty | Anzeigenamen adressieren. |
| --no-ask-password | Interaktive Authentisierungsabfrage unterdrücken, keine Rechte gewähren. |
| set-hostname / hostname NAME | Versionsabhängige Setzformen; reale Änderung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
hostnamectl status
```

Die unausgeführte Statusabfrage würde über die Systemd-Schnittstelle Informationen lesen. Sie ist kein Beleg für bestehende DNS-Einträge und kein Auftrag zur Änderung des Hostnamens.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Hostnamenarten verstehen; Statusausgabe vor einer später freigegebenen Konfigurationsänderung einordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Setter können Dienste und Namensbezüge beeinflussen. Managerabfragen können einen aktivierbaren Dienst kontaktieren; kein Offline-Dateitest. Keine Hostnamen, Maschineneigenschaften oder Dateien verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bus nicht erreichbar | Systemd-Dienstumgebung fehlt möglicherweise. |
| Pretty-Name anders | Anzeigename und technischer statischer Name unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Hostmanager nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| hostname | Andere Hostnamensschnittstelle. |
| getent | NSS-Auflösung, kann Netzwerk nutzen. |
| systemctl | Managerzustände. |

Ausgangsdatensatz 595 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
