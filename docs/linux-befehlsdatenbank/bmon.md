---
id: "bmon"
name: "bmon"
command: "bmon"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "safe"
tags: ["NetMon Spezial / Diagnoseideen", "bmon"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 404
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; bmon fehlt"
---

# bmon – Schnittstellenzähler und Datenraten beobachten

## 1. Kurzbeschreibung

bmon sammelt Netzwerkstatistiken und berechnet daraus Datenraten. Standardmäßig zeigt eine Terminaloberfläche die Werte. Es misst keinen maximalen Internetdurchsatz und ordnet Datenverkehr nicht automatisch einzelnen Anwendungen zu.

## 2. Was macht der Befehl?

Zählerdifferenz geteilt durch Messintervall ergibt eine Rate. Ein Interfacezähler ist keine Nutzdatenmessung einer bestimmten Verbindung. Virtuelle und physische Interfaces können denselben Verkehr mehrfach abbilden. Netlink ist der übliche Eingang, proc ein Ausweichweg. Eingangs-/Ausgangsmodule und lesende Rechte hängen vom System ab; normale Zähler benötigen häufig kein Root. Ein Anzeigenfilter verändert nicht die Schnittstelle selbst.

Quelle, am 2026-11-13 gelesen: [bmon-Projekthandbuch](https://manpages.debian.org/trixie/bmon/bmon.8.en.html)

## 3. Syntax

```text
bmon [OPTIONEN] [-i EINGANG] [-o AUSGANG]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p POLICY` | Anzuzeigende Interfacenamen auswählen; Wildcards vor Shellauswertung zitieren. |
| `-a` | Auch administrativ ausgeschaltete Interfaces anzeigen. |
| `-r SEKUNDEN` | Leseintervall wählen. |
| `-R SEKUNDEN` | Intervall der Ratenberechnung wählen. |
| `-b` | Bit/s statt Byte/s anzeigen, Faktor 8 beachten. |
| `-U` | Dezimale statt binärer Skalierung. |
| `-i`, `-o` | Datenquelle und Ausgabe auswählen; Modulhilfe ist implementationsabhängig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
bmon -p "LERNINTERFACE" -b -U
```

LERNINTERFACE ist durch einen später gesondert ausgewählten vorhandenen Namen zu ersetzen. Die Anzeige wäre in dezimal skalierten Bit/s zu lesen. 1000000 Byte/s entsprächen rechnerisch 8000000 Bit/s; dies ist ein erfundenes Rechenbeispiel und keine lokale Messung. Ein stilles Interface beweist keinen funktionierenden Internetzugang.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Datenraten einordnen: Einheiten und Intervall festhalten. Interfacepfade vergleichen: Tunnel und darunterliegende Geräte nicht unkritisch aufsummieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Bmon liest reale Systemstatistiken und kann interne Namen offenlegen. Anzeige und exportierte Daten können Ressourcen beanspruchen; keine fremden Module oder Konfigurationen übernehmen. Keine Netzlast, Interface- oder Dienständerung wird durch dieses Dokument getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Werte | Quelle, Policy, Rechte oder aktualisierte Zähler prüfen. |
| Faktor-8-Abweichung | Bit und Byte unterscheiden. |
| Doppelte Summen | Mehrere Ebenen des selben Verkehrs erfasst. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; bmon fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip -s link` | Andere Interfacestatistik. |
| `vnstat` | Langzeitstatistik mit Datenbank. |
| `iftop` | Verkehr nach Verbindung statt nur Interfacezähler. |

Ausgangsdatensatz 404 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
