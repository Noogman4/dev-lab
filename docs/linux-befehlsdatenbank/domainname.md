---
id: "domainname"
name: "domainname"
command: "domainname"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "domainname"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 426
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# domainname – NIS-Domain vom DNS-Namen unterscheiden

## 1. Kurzbeschreibung

domainname aus net-tools zeigt ohne Namen die NIS/YP-Domain des Kernels. Mit neuem Namen oder einer Namensdatei kann es diese ändern. Der Befehl verwaltet keine DNS-Zone.

## 2. Was macht der Befehl?

Die NIS-Domain ist ein eigener Namensraum für historische Verzeichnisdienste. Sie ist weder der DNS-Suffix des FQDN noch eine Active-Directory-Mitgliedschaft. Eine Kernelanzeige allein bestätigt keinen erreichbaren NIS-Server. Änderungen brauchen entsprechende Privilegien und setzen nicht automatisch eine dauerhafte Startkonfiguration.

Quelle, am 2026-11-13 gelesen: [net-tools: domainname/hostname-Handbuch](https://man7.org/linux/man-pages/man1/domainname.1.html)

## 3. Syntax

```text
domainname [-v]
domainname [-v] {NEUER_NAME | -F DATEI}
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne Namen | Aktuellen NIS-Domainwert anzeigen. |
| `NEUER_NAME` | Schreibende Änderung statt Suchanfrage. |
| `-F DATEI` | Neuen Namen aus Datei lesen und setzen. |
| `-v` | Ausführliche Diagnose. |
| `--help`, `--version` | Lokale Schnittstelle beziehungsweise Programmstand anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
domainname
Gedachter Wert: lernnis
Kein Aufruf mit einem neuen Namen
```

Das erste Muster ist die lesende Form. lernnis ist nur ein erfundener NIS-Wert und wird hier nicht als Argument übergeben. Wer eine DNS-Domain prüfen möchte, beantwortet mit diesem Wert die falsche Frage.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Altumgebungen verstehen:** NIS-Konfiguration von DNS trennen. **Fehlerdiagnose:** Den Kernelwert nicht mit einem funktionierenden Verzeichnisdienst gleichsetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein zusätzlicher Operand kann eine echte Systemänderung anfordern. Ein geänderter NIS-Wert kann die Zuordnung zu Verzeichnisdiensten stören. Nicht unbesehen mit sudo wiederholen. Hier wurden weder Name noch Systemdateien oder Benutzerzuordnungen verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Wahrscheinlich wurde ein Setzmodus angefordert; Argumente prüfen. |
| (none) oder leer | Kein sinnvoller Domainwert; nicht automatisch ein DNS-Fehler. |
| Nach Neustart anderer Wert | Laufzeitwert und Startkonfiguration sind getrennt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nisdomainname` | Alias im net-tools-Umfeld. |
| `ypdomainname` | Weitere NIS-bezogene Aufrufvariante. |
| `dnsdomainname` | DNS-Domänenteil des FQDN. |

Ausgangsdatensatz 426 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
