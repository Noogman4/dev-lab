---
id: "ip_route"
name: "ip route"
command: "ip route"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "ip_route"]
status: "Ausgearbeitet; Quellen geprüft; Routing-Laufzeitprüfung eingeschränkt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 58
reviewed_at: "2026-11-13"
locally_checked_version: "iproute2 6.1.0; Version und globale Hilfe geprüft"
---

# ip route – Routingtabellen und konkrete Wege getrennt beurteilen

## 1. Kurzbeschreibung

`ip route` zeigt gewöhnlich Einträge der Routingtabelle. Es kann auch die Kernelentscheidung für ein bestimmtes Ziel abfragen. Derselbe Objektbereich besitzt zusätzlich verändernde Unterbefehle.

**Für die normale Anzeige sind keine Root-Rechte nötig.** Routen setzen, ersetzen oder löschen benötigt entsprechende Privilegien und kann Verbindungen unterbrechen. Hier werden keine Routingänderungen ausgeführt.

## 2. Was macht der Befehl?

Eine Route beschreibt, über welchen Weg ein Zielpräfix erreicht werden soll. Wichtige Felder können Ziel, Gateway (`via`), Schnittstelle (`dev`), bevorzugte Quelladresse (`src`) und Metrik sein. `default` steht für eine Standardroute, nicht automatisch für den Weg jeder denkbaren Verbindung.

Linux kann mehrere Tabellen und Policy-Regeln verwenden. Ein einfacher Blick auf die Haupttabelle bildet nicht zwingend die Entscheidung für einen bestimmten VPN-, Quelladress- oder Markierungsfall ab. `route get` fragt einen konkreteren Kernel-Lookup mit den angegebenen Bedingungen ab.

Grundlagen: [ip-route-Manpage](https://manpages.debian.org/trixie/iproute2/ip-route.8.en.html) und [allgemeine ip-Referenz](https://manpages.debian.org/trixie/iproute2/ip.8.en.html). Lokal ist iproute2 6.1.0 vorhanden; die Sandbox erlaubt die benötigte Netlink-Laufzeitprüfung nicht.

## 3. Syntax

```text
ip [OPTIONEN] route show [FILTER]
ip [OPTIONEN] route get ZIELADRESSE [WEITERE_BEDINGUNGEN]
```

```bash
ip -4 route show
ip -6 route show
ip -4 route get 198.51.100.1
```

Die dritte Zeile verwendet eine Dokumentationsadresse als Lookup-Beispiel. Eine Route dazu beweist keine reale Erreichbarkeit dieses Ziels. Die Beispielabfragen wurden hier nicht erfolgreich am laufenden Netz ausgeführt.

## 4. Wichtige Optionen

| Auswahl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `show` | Routen anzeigen. | Keine Änderung. |
| `get ADRESSE` | Kernelentscheidung für ein Ziel abfragen. | Bedingungen des konkreten Datenverkehrs beachten. |
| `-4`, `-6` | IPv4 beziehungsweise IPv6 auswählen. | Getrennte Tabellenansichten und Entscheidungen. |
| `table main` | Haupttabelle wählen. | Nicht automatisch alle Policy-Wege. |
| `table all` | Alle Tabellen für die Anzeige berücksichtigen. | Größerer Bericht mit lokal relevanten Sondertabellen. |
| `default` | Anzeige auf Standardroute begrenzen. | Spezifischere Routen können dennoch Vorrang haben. |
| `dev NAME` | Nach Schnittstelle filtern. | Aktuellen Namen prüfen. |
| `from ADRESSE` | Quellbedingung beim Lookup setzen. | Muss zum fachlichen Prüffall passen. |
| `mark WERT` | Markierung beim geeigneten Lookup berücksichtigen. | Keine pauschale Nachbildung jeder Anwendungssituation. |
| `-json` | Strukturierte Ausgabe. | Mit passendem Parser auswerten. |
| `-details` | Mehr Details. | Versions- und objektspezifisch. |

`add`, `replace`, `del`, `flush` und `restore` sind keine reinen Anzeigeformen. Sie gehören nicht als spontane Ergänzung in diesen Diagnoseablauf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug prüfen

```bash
ip -Version
ip --help
```

Diese lokalen Abfragen wurden ausgeführt. Eine vorhandene Version bestätigt noch keinen Zugriff auf die Routingtabellen des gewünschten Namespace.

### Schritt 2: Adressfamilie bewusst wählen

```bash
ip -4 route show
```

Zielpräfixe, Gateways und Schnittstellen lesen. Eine fehlende `via`-Angabe kann bei direkt erreichbaren Netzen oder bestimmten Punkt-zu-Punkt-Wegen normal sein.

### Schritt 3: Standardroute ansehen

```bash
ip -4 route show default
```

Ein oder mehrere Einträge sind möglich. Ihre Existenz allein bestätigt weder funktionierendes DNS noch einen erreichbaren Upstream. Metriken nicht ohne Präfixe, Tabellen und Regeln isoliert vergleichen.

### Schritt 4: Konkreten Lookup formulieren

```bash
ip -4 route get 198.51.100.1
```

Ausgabe als Kernelentscheidung für diese Beispielbedingungen verstehen. Der Aufruf ist kein Ping und kein HTTP-Test. Eine andere Quelladresse, Markierung oder Policy kann einen anderen Datenweg ergeben.

### Schritt 5: Bei Policy-Fällen erweitern

```bash
ip -4 rule show
ip -4 route show table all
```

Diese zusätzlichen lesenden Abfragen können Regeln und weitere Tabellen sichtbar machen. Sie sind keine Erlaubnis, Regeln zu löschen oder VPN-Routen zu reparieren. Im Dokumentationstest wurden sie nicht ausgeführt.

## 6. Typische Anwendungsfälle

**Falschen Ausgang eingrenzen:** Prüfen, welche Schnittstelle der konkrete Lookup verwenden würde.

**VPN-Kontext verstehen:** Sondertabellen, Regeln und Zielpräfixe statt nur einer sichtbaren Default-Zeile betrachten.

**IPv4-/IPv6-Unterschiede untersuchen:** Funktionierende Familie nicht pauschal als Nachweis für die andere ausgeben.

**Gatewayangaben lesen:** Erkennen, ob ein Weg direkt oder über einen nächsten Hop modelliert ist. Das bestätigt noch nicht dessen tatsächlichen Betrieb.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Änderungen können Verbindung sofort unterbrechen

Eine Default-Route oder eine Policy-Regel zu löschen kann auch die eigene Fernverbindung abschneiden. Die reine Diagnose deshalb sichtbar von Setz-, Lösch- und Flush-Befehlen trennen.

### Namespace und dynamischer Zustand

Container, VPN und Gerätewechsel können andere beziehungsweise veränderte Tabellen liefern. Ein Screenshot eines früheren Stands ersetzt keine aktuelle Zuordnung vor einem späteren Eingriff.

### Lookup ist kein vollständiger Datenverkehrsnachweis

Firewall, DNS, Quellbedingungen, Anwendungsbindung und Gegenstelle können den Erfolg zusätzlich beeinflussen. Ein Kernel-Lookup kann außerdem nicht jede dynamische Paketmarkierung oder entfernte Netzentscheidung abbilden. Das Ergebnis nicht als vollständigen Leak- oder VPN-Sicherheitsnachweis darstellen.

### Berichtsdaten

Interne Adressen, Gateways und Interface-Namen können Netzstruktur verraten. Vor dem Teilen den benötigten Umfang prüfen. Berichtsumleitungen schreiben Dateien mit eigenen Überschreibwirkungen.

**Root-Rechte sind für normale Routinganzeigen nicht erforderlich.** Eine eingeschränkte Netlink-Umgebung wird benannt und nicht durch ungefragte Systemänderungen umgangen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Haupttabellenroute | Andere Tabelle, Familie oder fehlende Konfiguration. | Kontext und Regeln lesen. |
| Lookup unerreichbar | Keine passende Route oder ausdrücklicher Sperrtyp. | Tabellen und Bedingungen gezielt prüfen. |
| Route da, Verbindung scheitert | Andere Netzebene betroffen. | DNS, Firewall und Gegenstelle getrennt beurteilen. |
| VPN nicht in Default-Zeile | Policy-Routing oder spezifische Präfixe. | Weitere Tabellen und konkreten Lookup prüfen. |
| Falsche Schnittstelle erwartet | Andere Quelle oder Markierung. | Konkreten Verkehrsfall beschreiben. |
| Netlink verweigert | Umgebung beschränkt Kernelzugriff. | Laufzeitprüfung als offen kennzeichnen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Show und Get verwenden, nichts spontan ändern.
2. IPv4 und IPv6 bewusst auswählen.
3. Default-Zeile nicht als vollständigen Routingzustand behandeln.
4. Konkretes Ziel und gegebenenfalls Quellbedingungen benennen.
5. Lookup und tatsächliche Erreichbarkeit trennen.
6. Vor späteren Änderungen Rückweg und Verbindungserhalt planen.

**Prüfstand:** Ip-Version 6.1.0 und globale Hilfe wurden gelesen. Der Versuch der route-Unterhilfe scheiterte bereits am in der Sandbox nicht erlaubten Netlink-Zugriff. Keine Routingtabelle wurde erfolgreich abgefragt oder verändert; auch kein Testpaket an die Beispieladresse gesendet. Alle realen Routingansichten und Lookups bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip addr` | Zugewiesene Adressen lesen. |
| `ip rule` | Policy-Regeln lesen beziehungsweise mit anderen Unterbefehlen ändern. |
| `ip link` | Schnittstellenzustand. |
| `ss` | Sockets und lokale Dienstbindungen. |
| `nmcli` | NetworkManager-spezifischer Zustand und Konfiguration. |

Ausgangseintrag: Datensatz 58 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
