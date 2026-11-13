---
id: "ip_addr"
name: "ip addr"
command: "ip addr"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "ip_addr"]
status: "Ausgearbeitet; Quellen geprüft; Netlink-Laufzeitprüfung eingeschränkt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 57
reviewed_at: "2026-11-13"
locally_checked_version: "iproute2 6.1.0; Version und globale Hilfe geprüft"
---

# ip addr – Zugewiesene Adressen einer Netzwerkschnittstelle lesen

## 1. Kurzbeschreibung

`ip addr` zeigt gewöhnlich die einer Schnittstelle zugeordneten IPv4- und IPv6-Adressen. `addr` ist eine Kurzform des Objekts `address` im Programm `ip`.

**Für normale Adressanzeigen sind keine Root-Rechte nötig.** Der hier beschriebene Show-Aufruf verändert keine Netzkonfiguration. Andere address-Unterbefehle können Adressen hinzufügen oder entfernen und benötigen entsprechende Privilegien.

## 2. Was macht der Befehl?

Die Anzeige liest den aktuellen Kernelzustand im angesprochenen Netzwerk-Namespace. Eine Schnittstelle kann mehrere Adressen mit unterschiedlichen Präfixen, Gültigkeitszeiten und Scopes besitzen. `inet` bezeichnet IPv4, `inet6` IPv6. Die Zahl nach `/` ist die Präfixlänge.

Eine zugewiesene Adresse beweist weder Internetzugang noch einen funktionierenden VPN-Tunnel. Auch der administrative Zustand einer Schnittstelle, physische Verbindung und tatsächlicher Datenweg sind unterschiedliche Informationen.

Grundlagen: [ip-address-Handbuch](https://manpages.debian.org/trixie/iproute2/ip-address.8.en.html) und [allgemeine ip-Optionen](https://manpages.debian.org/trixie/iproute2/ip.8.en.html). Lokal wurde iproute2 6.1.0 festgestellt. Eine echte Zustandsabfrage ist in dieser Sandbox nicht praktisch bestätigt.

## 3. Syntax

```text
ip [OPTIONEN] address show [dev SCHNITTSTELLE]
```

```bash
ip address show
ip -brief address show
ip -4 address show dev SCHNITTSTELLE
```

`SCHNITTSTELLE` durch einen tatsächlich vorhandenen Namen ersetzen. Ein aus fremden Beispielen übernommenes `eth0` muss auf dem eigenen Rechner nicht existieren. Die ausgeschriebene Form macht das lesende `show` eindeutig.

## 4. Wichtige Optionen

| Option oder Auswahl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `show` | Adressen anzeigen. | Anders als add, replace, delete oder flush. |
| `-4` | IPv4 auswählen. | Keine Aussage über gleichzeitig vorhandenes IPv6. |
| `-6` | IPv6 auswählen. | Scope und Gültigkeit beachten. |
| `-brief` | Kompakte Übersicht. | Nicht alle Details enthalten. |
| `-json` | JSON-Ausgabe anfordern. | Geeigneten Parser und fehlende Felder berücksichtigen. |
| `-pretty` | JSON lesbarer formatieren. | Darstellung, keine weitere Zustandsprüfung. |
| `-details` | Zusätzliche Details. | Umfang abhängig vom Objekt und Build. |
| `dev NAME` | Eine Schnittstelle auswählen. | Aktuellen Namen prüfen. |
| `scope link` | Link-lokalen Adressbereich auswählen. | Nicht mit vollständiger Internetadressierung gleichsetzen. |
| `up` | Anzeige entsprechendem Interface-Zustand filtern. | „Up“ ist kein vollständiger Verbindungstest. |

Globale Optionen stehen vor `address`, objektspezifische Filter dahinter. Bei ip bedeutet `-n` Netzwerk-Namespace, nicht allgemein „keine Namensauflösung“. Optionen anderer Netzwerkwerkzeuge nicht ungeprüft übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug prüfen

```bash
ip -Version
ip --help
```

Diese Aufrufe wurden lokal geprüft. Die folgenden Schritte sind dokumentierte Zustandsabfragen und keine hier nachgewiesene reale Netzdiagnose.

### Schritt 2: Schnittstellenübersicht lesen

```bash
ip -brief address show
```

Interface-Namen und vorhandene Adressen ansehen. Loopback, physische Schnittstelle und virtuelle Tunnel nicht allein wegen ihrer Existenz gleich bewerten.

### Schritt 3: Eine konkrete Schnittstelle wählen

```text
ip address show dev SCHNITTSTELLE
```

Den Platzhalter bewusst ersetzen. Adressen, Präfixe, Scope und Lebensdauer getrennt lesen. Eine Schnittstelle ohne Adresse ist nicht automatisch defekt; sie kann eine andere Aufgabe erfüllen.

### Schritt 4: Adressfamilien getrennt betrachten

```text
ip -4 address show dev SCHNITTSTELLE
ip -6 address show dev SCHNITTSTELLE
```

Ein IPv4-Ergebnis ist kein Nachweis, dass IPv6 richtig funktioniert oder deaktiviert ist. Link-lokale und global eingeordnete Adressen fachlich unterscheiden.

### Schritt 5: Weitere Diagnose nur gezielt planen

Für den Datenweg die Routingentscheidung und gegebenenfalls DNS sowie tatsächliche Verbindung gesondert prüfen. Die Adressanzeige selbst startet keinen vollständigen Erreichbarkeits- oder VPN-Nachweis.

## 6. Typische Anwendungsfälle

**Aktuelle eigene Adresse lesen:** Für eine bewusst ausgewählte Schnittstelle statt aus einer großen Übersicht die falsche Zeile zu übernehmen.

**Mehrere Adressen verstehen:** Temporäre IPv6-Adressen, Link-lokales und weitere Adressen getrennt einordnen.

**NetMon-Diagnose vorbereiten:** Den aktuellen Kernelzustand mit der vorgesehenen Schnittstelle vergleichen. Ein alter virtueller Adapter allein bestätigt keinen aktiven Tunnel.

**Strukturierte Anzeige:** Für eigene Auswertung JSON verwenden, ohne auf zufällige Textspaltenpositionen zu vertrauen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Anzeigen und Ändern liegen im selben Werkzeug

`add`, `replace`, `delete` und `flush` haben andere Wirkungen als `show`. Ein kopiertes Löschrezept kann die Verbindung unterbrechen. Solche Unterbefehle nicht zur bloßen Diagnose ergänzen.

### Namespace und Momentaufnahme

Container oder Sandbox können einen anderen Netzwerk-Namespace zeigen als der reale Desktop. Auch eine korrekte Anzeige beschreibt nur den aktuellen Zustand. DHCP, VPN oder Gerätewechsel können ihn verändern.

### Vertrauliche Angaben

Adressen, Gerätenamen und Präfixe können interne Netzstruktur offenlegen. Vor dem Teilen eines Berichts dessen Umfang prüfen. JSON-Ausgabe anonymisiert nichts.

### Grenzen der Schlussfolgerung

Vorhandene Adresse, Interface-Up, Route, DNS und reale Erreichbarkeit sind getrennte Prüfungen. Keine einzelne Adresszeile als vollständigen Internet- oder VPN-Status ausgeben.

**Root-Rechte sind für normale Anzeigen nicht erforderlich.** Eine Sandbox-Sperre ist kein Anlass, Netzkonfiguration oder Systemberechtigungen für Dokumentationszwecke zu verändern.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Schnittstelle fehlt | Name anders oder falscher Namespace. | Aktuelle Übersicht und Kontext prüfen. |
| Nur IPv6 link-local | Keine andere sichtbare Adresse in der gewählten Familie. | Konfiguration und Zweck getrennt beurteilen. |
| Mehrere Adressen | Gewollte Mehrfachzuordnung. | Scope und Gültigkeit lesen. |
| Adresse da, Internet fehlt | Routing, DNS oder Verbindung betroffen. | Nächste Ebene gezielt prüfen. |
| Netlink nicht erlaubt | Ausführungsumgebung schränkt Kernelzugriff ein. | Einschränkung benennen, nicht als Gerätedefekt bewerten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. `address show` ausdrücklich verwenden.
2. Namen aus der aktuellen eigenen Übersicht übernehmen.
3. IPv4 und IPv6 getrennt lesen.
4. Namespace und Scope beachten.
5. Keine Flush- oder Löschaktionen zur Anzeige ergänzen.
6. Adresse nicht mit vollständiger Erreichbarkeit gleichsetzen.

**Prüfstand:** Ip-Version 6.1.0 und globale Hilfe wurden gelesen. Bereits der Versuch der address-Unterhilfe konnte wegen einer Sandbox-Netlink-Sperre nicht ausgeführt werden. Es wurde kein erfolgreicher Adressbericht erzeugt und keine Netzkonfiguration verändert. Anzeigen, Filter und reale Schnittstellenzustände bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip link show` | Schnittstellenzustand statt primär Adresszuordnung. |
| `ip route` | Wege und Routingentscheidungen lesen. |
| `ss` | Sockets statt Schnittstellenadressen untersuchen. |
| `nmcli` | NetworkManager-spezifischer Verwaltungszustand. |

Ausgangseintrag: Datensatz 57 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
