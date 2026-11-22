---
id: "ufw"
name: "ufw"
command: "ufw"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["ufw", "firewall & sicherheit"]
status: "Distributionshandbuch geprüft; keine laufende Firewall abgefragt oder verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 326
reviewed_at: "2026-11-13"
locally_checked_version: "Paket ufw 0.36.2-6; lokale Manpage gelesen"
---

# ufw – Firewallregeln verständlich und gezielt verwalten

## 1. Kurzbeschreibung

`ufw` ist eine Verwaltungsoberfläche für eine Linux-Firewall. Es kann Regeln anzeigen, erlauben oder verweigern und die von UFW verwaltete Firewall aktivieren beziehungsweise deaktivieren.

**Für produktive Firewallverwaltung sind administrative Rechte erforderlich.** Die lokale Hilfe benötigt keine Root-Rechte. Eine einfache Oberfläche macht Änderungen nicht automatisch folgenlos.

## 2. Was macht der Befehl?

UFW übersetzt eine vergleichsweise lesbare Regelsprache in die vorgesehenen Filterregeln. Richtung, Protokoll, Quelle, Ziel und Schnittstelle begrenzen die Wirkung. Eine Freigabe ohne diese Überlegungen kann weiter reichen als beabsichtigt.

Die [Ubuntu-Manpage zu UFW](https://manpages.ubuntu.com/manpages/noble/man8/ufw.8.html) und die lokale Manpage wurden gelesen. Die Paketmetadaten nennen Version `0.36.2-6`.

Eine UFW-Statusanzeige bezieht sich auf den von UFW verwalteten Bereich. Sie ist kein vollständiger Beweis über sämtliche zusätzlichen Regeln anderer Dienste, Anwendungen oder Verwaltungsebenen.

## 3. Syntax

```text
ufw --help
ufw status verbose
ufw status numbered
ufw [--dry-run] allow|deny|reject|limit REGELANGABEN
```

Die letzte Zeile ist eine Syntaxschablone; die Alternativen werden nicht wörtlich gemeinsam eingegeben. Eine Portangabe ohne Protokoll kann weiter reichen als dieselbe Angabe mit ausdrücklichem `/tcp`.

## 4. Wichtige Optionen

| Form | Wirkung | Einordnung |
| --- | --- | --- |
| `--help` | Bedienung anzeigen. | Keine Regeländerung. |
| `--version` | Programmversion ausgeben. | Kein Firewallstatus. |
| `status verbose` | UFW-Status ausführlicher zeigen. | Zuständigkeit der Ansicht beachten. |
| `status numbered` | Regeln mit Nummern zeigen. | Nummern können sich nach Löschungen ändern. |
| `--dry-run` | Vorgesehene Änderungen anzeigen. | Kein realer Erreichbarkeitstest. |
| `allow`, `deny`, `reject` | Regel hinzufügen. | Verändern das vorgesehene Filterverhalten. |
| `enable` | Laden und Startaktivierung vorsehen. | Kann bestehende Verbindungen beeinflussen. |
| `disable` | UFW-Firewall entladen und Startaktivierung abschalten. | Keine neutrale Diagnose. |
| `reset` | Deaktivieren und auf Ausgangswerte zurücksetzen. | Kann benötigte Regeln entfernen. |

`--force` unterdrückt bestimmte Rückfragen. Es darf nicht als gewöhnliche Reparaturergänzung betrachtet werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die vorgesehene Freigabe eng beschreiben

Als fiktives Modell diene ein absichtlich betriebener Testdienst auf TCP-Port `8080`, erreichbar nur von `192.0.2.10`. Diese Adresse ist ein Dokumentationsbeispiel und keine gemessene lokale Gegenstelle.

### Schritt 2: Nur einen Probelauf planen

```text
ufw --dry-run allow proto tcp from 192.0.2.10 to any port 8080
```

Der Schalter soll die vorgesehenen Änderungen zeigen, ohne sie anzuwenden. Dieser Aufruf wurde hier trotzdem nicht gestartet. Es gibt keinen tatsächlichen UFW-Testbericht und keine reale Freigabe.

### Schritt 3: Die Reichweite erklären

Die Regel benennt TCP und eine einzelne Quelle. Ohne weitere Schnittstellen- oder Zieladressbegrenzung bleiben andere Aspekte bewusst noch offen. Vor produktiver Verwendung müssten diese zur tatsächlichen Anwendung passen.

### Schritt 4: Nicht zur echten Anwendung übergehen

Das Weglassen von `--dry-run` wäre eine andere, verändernde Aktion. Ebenso benötigt ein Aktivieren von UFW eine eigene Planung. Die Dokumentation führt beides nicht aus.

## 6. Typische Anwendungsfälle

- Den von UFW verwalteten Zustand vor einer geplanten Änderung dokumentieren.
- Eine einzelne fachlich begründete Freigabe mit Quelle und Protokoll vorbereiten.
- Regelreihenfolge und Kommentare nachvollziehen.
- Einen bekannten Änderungsentwurf im Dry-run betrachten.

Ein erfolgreiches Anzeigen des Entwurfs beweist nicht, dass ein Dienst läuft oder ein Gegenüber die Verbindung erreicht. Anwendung, Routing und weitere Filter bleiben getrennte Prüfpunkte.

## 7. Risiken, Nebenwirkungen und Vorsicht

Aktivierung oder Standardrichtlinien können den eigenen Fernzugang sperren. Vor Änderungen an entfernten Systemen einen erreichbaren Rückweg und die benötigten Verwaltungsverbindungen berücksichtigen.

Ein bloßer Portname kann mehrere Protokolle oder eine andere lokale Dienstezuordnung meinen. Protokoll und tatsächlichen Dienstbedarf ausdrücklich angeben. IPv6-Abdeckung hängt außerdem von der UFW-Einrichtung ab; eine sichtbare IPv4-Regel allein beantwortet diese Frage nicht.

`reset` oder `disable` können gewollten Schutz entfernen. Nicht als erste Reaktion auf eine unklare Anwendungsmeldung verwenden. Logging kann zusätzliche Datenmengen und sensible Netzwerkangaben erzeugen.

## 8. Häufige Fehler

- **Port ohne Protokoll:** Freigabe ist möglicherweise breiter als beabsichtigt.
- **Alte Regelnummer löschen:** Vorher neu auflisten; Nummerierung kann sich ändern.
- **UFW inaktiv, also keinerlei Filter:** Andere Regelverwalter bleiben möglich.
- **Dry-run als Verbindungstest:** Es wurde kein wirklicher Datenverkehr nachgewiesen.
- **Firewall aktivieren ohne Fernzugangsplanung:** Der eigene Zugang kann unterbrochen werden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe und einer klaren Einzelregel beginnen. Vor Änderungen Bestand und zuständigen Verwaltungsweg feststellen. Komplette fremde UFW-Skripte nicht ungeprüft übernehmen.

Nach einer geplanten Änderung sowohl den Regelzustand als auch die gewünschte Funktion kontrolliert prüfen. Diese spätere Prüfung muss ausdrücklich benennen, welche Verbindung getestet wurde; ein allgemeines „läuft“ reicht als Nachweis nicht.

## 10. Verwandte Befehle

- `nft`: Direkte nftables-Verwaltung.
- `iptables`, `ip6tables`: Andere Paketfilteroberflächen.
- `firewall-cmd`: Client eines anderen Verwaltungsdienstes.
- `ss`: Lokale Sockets betrachten; keine Firewallfreigabe.
- `journalctl`: Passende Meldungen auswerten.

**Prüfstand:** Handbuch und Paketmetadaten geprüft. Kein Dry-run ausgeführt, keine Firewall aktiviert oder deaktiviert und keine Regel geändert.

Ausgangsdatensatz 326 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
