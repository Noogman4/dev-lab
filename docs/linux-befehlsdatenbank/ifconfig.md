---
id: "ifconfig"
name: "ifconfig"
command: "ifconfig"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ifconfig"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 428
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ifconfig – Ältere Interfaceanzeige richtig lesen

## 1. Kurzbeschreibung

ifconfig aus net-tools zeigt Schnittstellen und verändert deren Laufzeitkonfiguration. Ohne zusätzliche Konfigurationsargumente wird angezeigt; mit Adressen, up oder down wird ein Eingriff angefordert.

## 2. Was macht der Befehl?

Ohne Argument zeigt ifconfig aktive Schnittstellen; -a schließt heruntergefahrene ein. UP ist eine administrative Freigabe und kein Beweis eines funktionierenden Internetzugangs. RX/TX-Zähler sind Summen und keine aktuellen Datenraten. Für moderne, vollständige Adress- und Linkdiagnose sind die getrennten iproute2-Objekte meist verständlicher.

Quelle, am 2026-11-13 gelesen: [net-tools: ifconfig-Handbuch](https://man7.org/linux/man-pages/man8/ifconfig.8.html)

## 3. Syntax

```text
ifconfig [-a] [-s] [SCHNITTSTELLE]
ifconfig SCHNITTSTELLE [ADRESSFAMILIE] KONFIGURATION
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-a` | Auch inaktive Schnittstellen anzeigen. |
| `-s` | Kurze tabellarische Anzeige. |
| `SCHNITTSTELLE` | Anzeige auf ein Gerät begrenzen. |
| `up`, `down` | Interface aktivieren/deaktivieren; echte Änderung. |
| `netmask`, `mtu` | Adressmaske beziehungsweise Paketgröße ändern. |
| `promisc` | Empfangsmodus ändern; keine reine Anzeige. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ifconfig -a eth-lernen
```

Der erfundene Interface-Name macht die Auswahl sichtbar. -a ist eine Anzeigeoption. Ein gedachter Wert RX bytes=4096 wäre ein Zählerstand; erst die Differenz zwischen zwei bekannten Zeitpunkten könnte eine Rate liefern. Es wurde keine Schnittstelle ausgelesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Alte Anleitungen lesen:** Anzeigeform und Konfigurationsform erkennen. **Migration planen:** Link-, Adress- und Routingfragen den passenden modernen Werkzeugen zuordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Adressänderungen oder down können eine bestehende Sitzung sofort trennen. Laufzeitänderungen sind nicht automatisch dauerhaft und können von einem Netzwerkmanager überschrieben werden. Mehrfachadressen und ältere Aliasnotation sollten nicht aus unvollständigen Anzeigen rekonstruiert werden. Hier bleibt jede echte Konfiguration unberührt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Gerät nicht gefunden | Keinen universellen Namen eth0 voraussetzen. |
| Kein Interface angezeigt | Ohne -a werden inaktive Geräte ausgelassen. |
| Adresse trotz Erfolg später anders | Zuständiger Manager und persistente Konfiguration sind getrennt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip address` | Adressobjekte einschließlich mehrerer Adressen. |
| `ip link` | Linkzustand und Geräteattribute. |
| `ip route` | Routing unabhängig von Interfaceanzeige. |

Ausgangsdatensatz 428 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
