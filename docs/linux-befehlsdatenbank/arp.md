---
id: "arp"
name: "arp"
command: "arp"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "arp"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 421
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# arp – IPv4-Nachbarcache lesen und Änderungen erkennen

## 1. Kurzbeschreibung

arp aus net-tools zeigt und verändert den IPv4-Nachbarcache des Kernels. Lesende Anzeigen brauchen meist kein Root; Setzen und Löschen erfordern Netzwerkadministrationsrechte. IPv6 verwendet Neighbor Discovery statt dieser ARP-Tabelle.

## 2. Was macht der Befehl?

Ein Cacheeintrag verbindet eine lokale IPv4-Nachbaradresse mit einer Linkadresse. Entfernte Internetziele erscheinen gewöhnlich über ihren nächsten Router, nicht als direkte MAC-Ziele. Der Cache ist keine vollständige Liste eingeschalteter Rechner und keine vertrauenswürdige Geräteidentität. Permanente Einträge sind Kernelzustand, keine automatisch über Neustarts gespeicherte Konfiguration.

Quelle, am 2026-11-13 gelesen: [net-tools: arp-Handbuch](https://manpages.debian.org/trixie/net-tools/arp.8.en.html)

## 3. Syntax

```text
arp -n [-i INTERFACE]
arp -s ADRESSE MAC
arp -d ADRESSE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-n` | Numerisch anzeigen, zusätzliche Namensauflösung vermeiden. |
| `-i NAME` | Einträge auf ein Interface beschränken. |
| `-a`, `-e` | BSD- beziehungsweise Linuxdarstellung. |
| `-s` | Eintrag setzen; schreibender Eingriff. |
| `-d` | Eintrag löschen; kann erneute Auflösung und Verbindungsstörungen auslösen. |
| `-f DATEI` | Einträge aus Datei setzen, nicht bloß eine Tabelle offline lesen. |
| `C`, `M`, `P` | Vollständig, permanent beziehungsweise veröffentlicht; Ansicht beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
arp -n -i LERNINTERFACE
```

Das Muster würde vorhandene Kernelinformationen numerisch anzeigen, ohne mit -s/-d einzugreifen. Eine leere Tabelle wäre kein fehlgeschlagener LAN-Scan, denn es wird gar kein vollständiger Scan angefordert. Der echte Cache wurde hier nicht gelesen oder verändert. IPv6-Ergebnisse wären mit einem anderen Werkzeug zu untersuchen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Nachbarauflösung verstehen: Nächsten Hop von fernem Ziel trennen. Altwerkzeuge einordnen: Moderne ip-neigh-Sicht mit ARP-spezifischer Ansicht vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche statische Einträge können Datenverkehr fehlleiten oder unterbrechen. Cachelöschen ist keine harmlose Erstmaßnahme. Fremde MAC-/IP-Zuordnungen nicht als Identitätsbeweis verwenden. Keine Echtgeräte, Proxy-ARP-Einträge oder Systemdateien bearbeiten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Host fehlt | Cache nur bei Bedarf gefüllt, kein Gesamtinventar. |
| IPv6 nicht sichtbar | ARP ist IPv4-spezifisch. |
| Permanenter Eintrag nach Neustart weg | Kernelcache und persistente Einrichtung unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip neigh` | Moderne IPv4-/IPv6-Nachbarverwaltung. |
| `arping` | Sendet aktive ARP-Pakete. |
| `route` | Bestimmt nächste Hops auf IP-Ebene. |

Ausgangsdatensatz 421 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
