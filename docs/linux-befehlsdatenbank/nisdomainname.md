---
id: "nisdomainname"
name: "nisdomainname"
command: "nisdomainname"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "nisdomainname"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 436
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# nisdomainname – NIS-Aufrufname mit schreibender Form erkennen

## 1. Kurzbeschreibung

nisdomainname ist im net-tools-Umfeld ein Aufrufname zur NIS/YP-Domain. Ohne neuen Namen wird angezeigt; mit Namen wird eine Kerneländerung angefordert.

## 2. Was macht der Befehl?

Eine NIS-Domain ist keine DNS-Suchdomain und kein Nachweis einer Domänenanmeldung. Der Wert betrifft die lokale Laufzeitumgebung. Ein gesetzter Name allein prüft weder Serververfügbarkeit noch Benutzerzuordnung. Die lokale hostname-Manpage und die aktuelle Projektfassung unterscheiden sich in historischen Details; hier wird keine persistente Konfiguration daraus abgeleitet.

Quelle, am 2026-11-13 gelesen: [net-tools: hostname/NIS-Handbuch](https://man7.org/linux/man-pages/man1/hostname.1.html) sowie lokale hostname-Manpage

## 3. Syntax

```text
nisdomainname
nisdomainname NIS_NAME
nisdomainname -F DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne Argument | NIS-Domain anzeigen. |
| `NIS_NAME` | NIS-Domain ändern; administrative Rechte erforderlich. |
| `-F DATEI` | Namensdatei für eine Änderung; keine beliebige Textanzeige. |
| `--help` | Hilfe der tatsächlich installierten Variante prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nisdomainname
Gedachter NIS-Wert: lernnis
```

Der Name lernnis ist nur die gedachte Ausgabe und wird nicht als Operand übergeben. Ein einzelnes Wort in der Ausgabe erklärt keine DNS-Auflösung. Der Aufruf wurde nicht ausgeführt; auch ein leerer Wert wurde nicht gemessen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**NIS-Altbestand verstehen:** Namen dem richtigen Verzeichnisdienst zuordnen. **Anleitungen prüfen:** Fehlende Operanden von Setzformen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein zusätzlicher Name kann die Domain ändern und NIS-abhängige Abläufe stören. Laufzeitänderung und Startkonfiguration sind getrennt. Keine Änderungen an Hostnamen, Konten oder Systemdateien; keine Dienste gestartet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wert entspricht nicht dem FQDN | NIS und DNS sind verschiedene Namensräume. |
| Setzen verweigert | Argumentform prüfen, keine automatische sudo-Wiederholung. |
| Server nicht erreichbar trotz Wert | Der Kernelwert prüft keinen Dienst. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `domainname` | Verwandte NIS-Anzeige und Setzform. |
| `ypdomainname` | Weitere Aufrufvariante. |
| `dnsdomainname` | DNS-bezogene andere Fragestellung. |

Ausgangsdatensatz 436 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
