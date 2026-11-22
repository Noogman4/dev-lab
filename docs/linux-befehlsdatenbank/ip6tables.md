---
id: "ip6tables"
name: "ip6tables"
command: "ip6tables"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["ip6tables", "firewall & sicherheit"]
status: "Lokale Manpage geprüft; Hilfeaufruf an fehlendem Netfilterzugriff gescheitert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 318
reviewed_at: "2026-11-13"
locally_checked_version: "Paket iptables 1.8.10-3ubuntu2; lokale Ausführung durch Umgebung beschränkt"
---

# ip6tables – IPv6-Paketfilterregeln gezielt betrachten und verwalten

## 1. Kurzbeschreibung

`ip6tables` verwaltet IPv6-Regeln der iptables-Werkzeugfamilie. Eine IPv4-Firewallregel mit `iptables` deckt IPv6 nicht automatisch ab. **Für Kernelregelzugriff sind administrative Rechte beziehungsweise `CAP_NET_ADMIN` im zuständigen Netzwerk-Namespace erforderlich.**

Regeländerungen können sofort Verbindungen unterbrechen oder unerwünschte Freigaben schaffen. Deshalb beginnt dieser Eintrag mit einer lesenden Betrachtung, nicht mit einer pauschalen Sperrvorlage.

## 2. Was macht der Befehl?

Regeln gehören zu Tabellen und Ketten. Für die Filterung sind beispielsweise eingehende Pakete zum Rechner, ausgehende Pakete und weitergeleitete Pakete unterschiedliche Wege.

Die [Netfilter-Projektbeschreibung](https://www.netfilter.org/projects/iptables/index.html) ordnet `ip6tables` IPv6 zu. Das gemeinsame [Upstream-Handbuch](https://man7.org/linux/man-pages/man8/iptables.8.html) und die lokal installierte Manpage erklären die Regeloberfläche.

Moderne Distributionen können eine Kompatibilitätsschicht auf nftables oder ein anderes Backend verwenden. Vor einer Verwaltung klären, welche Werkzeuge den Regelbestand tatsächlich pflegen. Ein leerer Ausschnitt einer Ansicht beweist keinen vollständig ungefilterten Rechner.

## 3. Syntax

```text
ip6tables [OPTIONEN] AKTION [KETTE] [REGEL]
ip6tables -t filter -L INPUT -n -v --line-numbers
ip6tables -t filter -S
```

`-L` und `-S` zeigen Regeln. Sie setzen keine neue Standardrichtlinie. Die Tabellenwahl bleibt dennoch relevant; ein unbekannter Kernelkontext kann den Zugriff verhindern.

## 4. Wichtige Optionen

| Form | Aufgabe | Folge |
| --- | --- | --- |
| `-t TABELLE` | Tabelle wählen. | Ohne Angabe ist `filter` der übliche Standard. |
| `-L KETTE` | Regeln auflisten. | Nur die gewählte Ansicht. |
| `-S` | Regeln in Spezifikationsform zeigen. | Für Konfigurationsvergleich hilfreich. |
| `-n` | Numerische Adressen und Ports zeigen. | Vermeidet Namensauflösung der Anzeige. |
| `-v` | Mehr Details und Zähler anzeigen. | Zähler benötigen Zeitkontext. |
| `--line-numbers` | Aktuelle Zeilennummern anzeigen. | Nummern können sich nach Änderungen verschieben. |
| `-A` | Regel anhängen. | Verändert den laufenden Filter. |
| `-D` | Regel löschen. | Ziel eindeutig bestimmen. |
| `-F` | Regeln einer Auswahl leeren. | Keine harmlose Rücksetzung. |
| `-P` | Standardrichtlinie ändern. | Kann den eigenen Zugriff sperren. |

`-Z` setzt Zähler zurück und ist damit eine Zustandsänderung. Es gehört nicht zusätzlich in eine reine Bestandsaufnahme.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Den IPv6-Bereich ausdrücklich wählen

Für eine geplante Betrachtung eingehender IPv6-Pakete wäre folgender Aufruf passend:

```text
ip6tables -t filter -L INPUT -n -v --line-numbers
```

Er wurde nicht als echte Regelabfrage ausgeführt. Schon die lokalen Aufrufe für Hilfe und Version scheiterten in der eingeschränkten Umgebung an fehlendem Netfilterzugriff. Die Paketversion wurde daher separat aus Paketmetadaten festgestellt.

### Schritt 2: Ein fiktives Ergebnis einordnen

Angenommen, eine Regel hätte einen Paketzähler größer null. Das zeigt zunächst passende Pakete seit dem jeweiligen Zählerbeginn. Es beweist nicht, dass eine bestimmte gewünschte Anwendung vollständig erreichbar oder sicher gesperrt war.

### Schritt 3: Keine IPv4-Vorlage blind übertragen

IPv6-Adressen und wichtige Kontrollnachrichten brauchen eine eigene Betrachtung. Eine pauschale Sperre sämtlicher ICMPv6-Nachrichten kann grundlegende Netzfunktionen beeinträchtigen. Die für ein konkretes System benötigte Regelmenge bleibt ein geplanter fachlicher Prüfpunkt.

## 6. Typische Anwendungsfälle

- IPv6 beim Vergleich einer dokumentierten Firewallkonfiguration ausdrücklich berücksichtigen.
- Eine einzelne Kette und ihre Zähler betrachten.
- Unterschiedliche Ansichten oder Backends vor Änderungen zuordnen.
- Einen Fehlerbericht um den tatsächlichen Paketweg ergänzen.

Eine Kettenauflistung ist noch kein Verbindungstest. Routing, Zielprozess und andere Filter können zusätzlich entscheidend sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Regeln können VPN, Fernzugang und grundlegende IPv6-Funktionen beeinträchtigen. Bei entfernten Rechnern braucht jede Änderung einen erreichbaren Rückweg. Pauschales Leeren oder eine sofortige Drop-Richtlinie sind keine Einsteigerdiagnose.

Die Laufzeitregeln sind außerdem nicht automatisch dauerhaft gespeichert. Ein anderer Dienst kann sie verwalten oder nach einem Neustart neu laden. Unkoordinierte Änderungen mit mehreren Werkzeugen erschweren die Nachvollziehbarkeit.

## 8. Häufige Fehler

- **IPv4 geprüft, IPv6 vergessen:** Getrennten Geltungsbereich beachten.
- **Keine Berechtigung als leere Firewall lesen:** Fehlgeschlagener Zugriff liefert keinen Regelbestand.
- **Zeilennummer später wiederverwenden:** Der Bestand kann sich verändert haben.
- **Zähler ohne Zeitraum bewerten:** Zeitpunkt und Rücksetzungen fehlen.
- **Alle Kontrollnachrichten blockieren:** Kann notwendige IPv6-Abläufe beschädigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Bestand, Verwaltung und Backend klären. Lesende Aufrufe ohne Zählerrücksetzung bevorzugen. Keine fremde Firewallvorlage ungeprüft auf dem laufenden Rechner anwenden.

Wenn ein übergeordnetes Werkzeug wie firewalld oder UFW zuständig ist, Änderungen über dessen vorgesehenen Weg planen. Eine zusätzliche direkte Regel ist nicht automatisch dauerhaft oder konfliktfrei.

## 10. Verwandte Befehle

- `iptables`: Entsprechende IPv4-Oberfläche.
- `ip6tables-save`: IPv6-Regelbestand ausgeben.
- `ip6tables-restore`: Regeln laden; verändernde Aktion.
- `nft`: nftables direkt verwalten.
- `ip -6`: IPv6-Adressen und Routen betrachten.

**Prüfstand:** Manpage und Paketversion geprüft. Eingeschränkte Hilfe-/Versionsaufrufe ohne Erfolg; keine echte Regelausgabe und keine Firewalländerung.

Ausgangsdatensatz 318 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
