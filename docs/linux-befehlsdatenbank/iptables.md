---
id: "iptables"
name: "iptables"
command: "iptables"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["iptables", "firewall & sicherheit"]
status: "Lokales Handbuch und Paketmetadaten geprüft; keine Firewallregeln verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 319
reviewed_at: "2026-11-13"
locally_checked_version: "Paket iptables 1.8.10-3ubuntu2; Hilfe in Umgebung nicht verfügbar"
---

# iptables – IPv4-Regeln, Ketten und Richtlinien verstehen

## 1. Kurzbeschreibung

`iptables` betrachtet und verwaltet IPv4-Paketfilter- und NAT-Regeln. Ein einzelner Schalter kann Regeln nur anzeigen oder den laufenden Datenverkehr sofort beeinflussen. **Für den Kernelregelzugriff sind administrative Rechte beziehungsweise passende Netzwerk-Capabilities erforderlich.**

Für IPv6 ist die entsprechende iptables-Oberfläche `ip6tables` zuständig. Eine IPv4-Regel allein schützt nicht automatisch beide Protokollfamilien.

## 2. Was macht der Befehl?

Eine Tabelle enthält Ketten, und eine Kette enthält geordnete Regeln. Regeln verbinden Bedingungen mit einer Aktion. Der Paketweg bestimmt, welche Ketten überhaupt betrachtet werden. Für `filter` sind `INPUT`, `OUTPUT` und `FORWARD` wichtige eingebaute Ketten.

Die [Netfilter-Projektseite](https://www.netfilter.org/projects/iptables/index.html), das [Upstream-Handbuch](https://man7.org/linux/man-pages/man8/iptables.8.html) und die lokale Manpage erläutern die Werkzeugfamilie. Die lokale Handbuchfassung gehört zu iptables `1.8.10`.

Eine Regel kann formal vorhanden und trotzdem für die betrachtete Verbindung ohne Wirkung sein, etwa wegen des falschen Paketwegs oder einer vorherigen Entscheidung. Zur Einordnung gehört daher mehr als das bloße Auffinden einer Portnummer.

## 3. Syntax

```text
iptables [OPTIONEN] AKTION [KETTE] [REGEL]
iptables -t filter -L INPUT -n -v --line-numbers
iptables -t filter -S
```

Der erste konkrete Aufruf zeigt eine bestimmte Kette. Der zweite gibt die Regeln der gewählten Tabelle als Spezifikationen aus. Beide sind hier dokumentierte, nicht ausgeführte Regelabfragen.

## 4. Wichtige Optionen

| Option | Zweck | Abgrenzung |
| --- | --- | --- |
| `-t TABELLE` | Tabelle auswählen. | `filter` ist nicht dieselbe Ebene wie `nat`. |
| `-L` | Regeln auflisten. | Keine vollständige Ansicht aller möglichen Tabellen. |
| `-S` | Spezifikationen anzeigen. | Nützlich für nachvollziehbare Vergleiche. |
| `-n` | Zahlen statt aufgelöster Namen zeigen. | Vermeidet Anzeige-DNS-Abfragen. |
| `-v` | Details einschließlich Zählern ergänzen. | Zähler mit Zeitpunkt lesen. |
| `--line-numbers` | Regelpositionen anzeigen. | Nach Änderungen nicht dauerhaft stabil. |
| `-C` | Vorhandensein einer passenden Regel prüfen. | Kein syntaktischer Probelauf einer neuen Firewall. |
| `-A`, `-I` | Regel anhängen oder einfügen. | Reihenfolge beeinflusst die Wirkung. |
| `-D`, `-F` | Regel löschen oder Auswahl leeren. | Kann Schutz beziehungsweise Erreichbarkeit verändern. |
| `-P` | Standardrichtlinie ändern. | Besonders riskant bei Fernzugriff. |

`-Z` setzt Zähler zurück. Auch eine Anzeige zusammen mit diesem Schalter wäre deshalb keine unveränderte Bestandsaufnahme.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die Frage auf eingehende IPv4-Pakete begrenzen

```text
iptables -t filter -L INPUT -n -v --line-numbers
```

Dies wäre ein geplanter lesender Aufruf. Er wurde hier nicht auf die echten Regeln angewendet. Hilfe- und Versionsaufrufe scheiterten bereits am fehlenden Netfilterzugriff der eingeschränkten Umgebung.

### Schritt 2: Drei Angaben auseinanderhalten

Ein fiktiver Bericht könnte eine eingebaute Richtlinie, mehrere Regeln und Paket-/Bytezähler zeigen. Die Richtlinie behandelt das Ende der eingebauten Kette; eine konkrete Regel kann vorher entscheiden. Ein Zähler beschreibt passende Pakete, nicht automatisch erfolgreiche Anmeldungen.

### Schritt 3: Den richtigen Weg untersuchen

Ein Rechner, der Pakete nur für andere Rechner weiterleitet, nutzt dafür nicht denselben Weg wie ein lokaler Serverprozess. Ein Blick ausschließlich auf `INPUT` würde diese Weiterleitung nicht vollständig beschreiben.

### Schritt 4: Keine sofortige Korrektur anhängen

Eine unklare Ausgabe ist kein Anlass, `-F` oder eine neue Standardrichtlinie nachzuschieben. Erst Sollzustand, zuständiges Verwaltungswerkzeug und Rückweg feststellen. In dieser Übung wurde nichts geladen oder zurückgesetzt.

## 6. Typische Anwendungsfälle

- Eine konkrete IPv4-Kette für eine autorisierte Diagnose betrachten.
- Dokumentierte Regeln und tatsächliche Verwaltung zuordnen.
- Laufzeitkonfiguration vor einer geplanten einzelnen Änderung festhalten.
- Verstehen, weshalb eine sichtbare Regel nicht zum untersuchten Paketweg passt.

NAT ist Adressumsetzung und nicht automatisch eine vollständige Sicherheitsrichtlinie. Filterung, Routing und Adressumsetzung müssen im jeweiligen Zusammenhang betrachtet werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine Regeländerung kann den eigenen SSH- oder VPN-Zugang trennen. Eine zu breite Freigabe kann einen laufenden Dienst unerwartet erreichbar machen. Laufzeitänderungen sind zudem nicht automatisch nach einem Neustart vorhanden.

Distributionen können unterschiedliche Backends und übergeordnete Verwalter nutzen. `iptables`, `nft`, UFW und firewalld nicht ohne geklärte Zuständigkeit gleichzeitig verändern. Eine Ansicht mit wenigen Regeln kann außerdem nur einen Teil des wirksamen Gesamtsystems zeigen.

## 8. Häufige Fehler

- **Leere Tabelle als allgemeine Aussage lesen:** Andere Tabellen oder Verwaltungsebenen fehlen.
- **`-C` als Dry-run missverstehen:** Es sucht eine bestehende Regel.
- **Paketanzahl mit Benutzeranzahl gleichsetzen:** Zähler messen etwas anderes.
- **Falsche Kette prüfen:** Lokaler und weitergeleiteter Verkehr sind verschieden.
- **Fehlenden Zugriff durch Abschalten lösen:** Das liefert keine nachvollziehbare Diagnose.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer lesenden, numerischen und klar begrenzten Ansicht beginnen. Den beobachteten Bestand beschreiben, bevor Änderungen vorgeschlagen werden. Ein vorbereitetes Wiederherstellungskonzept gehört zu produktiven Änderungen, insbesondere bei Fernverwaltung.

Kopierte komplette Regelsätze können Regeln anderer Anwendungen verdrängen. Für einen einzelnen Anwendungsfehler ist ein pauschaler Neuaufbau deshalb meist kein nachvollziehbarer erster Schritt.

## 10. Verwandte Befehle

- `ip6tables`: IPv6-Regeln verwalten.
- `iptables-save`: Regelbestand ausgeben.
- `iptables-restore`: Regelsatz einspielen; verändernde Aktion.
- `nft`: nftables-Oberfläche.
- `ufw`, `firewall-cmd`: Übergeordnete Verwaltungsansätze.

**Prüfstand:** Handbuch und Paketstand geprüft. Lokale Hilfe-/Versionsaufrufe scheiterten an der Umgebung; keine Regelabfrage als erfolgreich behauptet und keine Regel verändert.

Ausgangsdatensatz 319 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
