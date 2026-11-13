---
id: "chkconfig"
name: "chkconfig"
command: "chkconfig"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "chkconfig"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 564
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Runlevelverwaltung offen"
---

# chkconfig – SysV-Startverknüpfungen mit chkconfig einordnen

## 1. Kurzbeschreibung

chkconfig verwaltet bei der hier dokumentierten Fedora-SysV-Implementierung Runlevel-Startinformationen.

## 2. Was macht der Befehl?

Startkonfiguration und aktuell laufender Dienst sind verschiedene Zustände. on beziehungsweise off verändert Zuordnungen für Runlevel, nicht automatisch den aktuellen Laufzustand. Andere Distributionen können abweichende Implementierungen oder Weiterleitungen zu systemctl liefern. chkconfig ist lokal nicht vorhanden.

Quelle, am 2026-11-13 gelesen: [Fedora-SysV: chkconfig-Primärhandbuch](https://raw.githubusercontent.com/fedora-sysv/chkconfig/main/chkconfig.8)

## 3. Syntax

```text
chkconfig --list [DIENST]
chkconfig [--level RUNLEVEL] DIENST on oder off
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --list | Runlevelinformationen anzeigen. |
| --level ZAHLEN | Betroffene Runlevel ausdrücklich wählen. |
| --add DIENST | Dienst in Verwaltung aufnehmen. |
| --del DIENST | Verwaltungsverknüpfungen entfernen. |
| --no-redirect | Implementierungsabhängige systemd-Weiterleitung unterbinden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
chkconfig --list TESTDIENST
```

TESTDIENST steht für einen zuvor bekannten Dienst einer passenden SysV-Installation. Die Abfrage bleibt unausgeführt. Aus on allein folgt kein gerade laufender Prozess.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ältere Runlevelkonfiguration verstehen; distributionsspezifische Wartungsanleitungen zuordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Schreibende Modi beeinflussen spätere Starts und Systembetrieb. Nicht mit anderen chkconfig-Varianten vermischen. Kein Dienst registriert, deaktiviert oder gelöscht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Befehl fehlt | Init-System und Distribution prüfen. |
| on, aber Dienst läuft nicht | Startverknüpfung und aktuellen Zustand getrennt untersuchen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Runlevelverwaltung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| update-rc.d | Debian-SysV-Verknüpfungen. |
| service | Aktuellen Dienst bedienen. |
| systemctl | Systemd-Verwaltung. |

Ausgangsdatensatz 564 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
