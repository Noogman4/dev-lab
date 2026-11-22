---
id: "nft"
name: "nft"
command: "nft"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["nft", "firewall & sicherheit"]
status: "Lokale und offizielle Manpage geprüft; keine Regelabfrage oder Änderung ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 321
reviewed_at: "2026-11-13"
locally_checked_version: "Paket nftables 1.0.9-1ubuntu0.1; lokale Aufrufe eingeschränkt"
---

# nft – nftables-Regeln strukturiert lesen und verwalten

## 1. Kurzbeschreibung

`nft` verwaltet das nftables-System im Linux-Kernel. Es unterstützt unter anderem Tabellen, Ketten, Regeln und Mengen. Eine gemeinsame Internetfamilie kann IPv4 und IPv6 umfassen.

**Für Kernelregelzugriff werden administrative Rechte beziehungsweise `CAP_NET_ADMIN` im zuständigen Netzwerk-Namespace benötigt.** Die Programmhilfe ist von einer echten Regelabfrage zu unterscheiden; in dieser eingeschränkten Umgebung scheiterte allerdings bereits die Initialisierung.

## 2. Was macht der Befehl?

nftables ordnet Regeln einem bestimmten Paketverarbeitungspunkt zu. Tabellenname, Adressfamilie, Kette, Hook und Priorität bestimmen den Zusammenhang. Eine Kette ohne Einbindung in den relevanten Paketweg bewirkt nicht automatisch eine Filterung des gewünschten Verkehrs.

Die [offizielle nft-Manpage](https://netfilter.org/projects/nftables/manpage.html) und die lokale Manpage erläutern Oberfläche und Syntax. Lokal ist laut Paketmetadaten nftables `1.0.9-1ubuntu0.1` vorhanden. Ein neueres Onlinehandbuch kann darüber hinausgehende Funktionen beschreiben.

Vor direkten Änderungen außerdem klären, ob ein anderer Dienst die Regeln verwaltet. Eine manuell eingefügte Regel kann sonst später ersetzt oder mit anderen Entscheidungen kombiniert werden.

## 3. Syntax

```text
nft [OPTIONEN] BEFEHL
nft -n -a list ruleset
nft -j list ruleset
nft -c -f DATEI
```

`list ruleset` liest den Regelbestand. `-f DATEI` verarbeitet Befehle aus einer Datei; ohne Prüfmodus können sie die Firewall verändern. `-c` prüft deren Gültigkeit, ist jedoch kein Nachweis der späteren Netzwerkwirkung.

## 4. Wichtige Optionen

| Form | Zweck | Bedeutung für die Anwendung |
| --- | --- | --- |
| `-h` | Hilfe anzeigen. | Kein geplanter Regellauf. |
| `-v` | Version anzeigen. | Kleines v beachten. |
| `-n` | Numerische Darstellung wählen. | Gut für eindeutige Adressvergleiche. |
| `-a` | Objekt-Handles anzeigen. | Nicht mit dauerhafter fachlicher Identität gleichsetzen. |
| `-j` | JSON-Ausgabe verwenden. | Schema und Status prüfen. |
| `-c` | Änderungen vor Anwendung prüfen. | Kein Offline-Sicherheitsbeweis. |
| `-f DATEI` | Befehlsdatei verarbeiten. | Datei kann Includes und Änderungen enthalten. |
| `-I VERZEICHNIS` | Include-Suchpfad ergänzen. | Vertrauenswürdigkeit eingeschlossener Dateien beachten. |
| `-N` | Reverse-DNS-Auflösung einschalten. | Kann Netzwerkverkehr auslösen. |

Die Familien `ip`, `ip6` und `inet` bezeichnen IPv4, IPv6 beziehungsweise die gemeinsame Betrachtung beider. Bei einer Regelentscheidung die Familie ausdrücklich zuordnen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen lesenden Bericht planen

```text
nft -n -a list ruleset
```

Die numerische Darstellung vermeidet unnötige Mehrdeutigkeit durch Namen. Handles können später helfen, ein konkret beobachtetes Objekt zu besprechen. Diese echte Regelabfrage wurde hier nicht ausgeführt.

### Schritt 2: Die praktische Grenze festhalten

Die lokalen Hilfe- und Versionsaufrufe endeten in dieser Umgebung mit fehlendem Netlinkzugriff. Deshalb wird hier keine erfolgreich gelesene reale Firewall behauptet. Die Paketversion stammt aus Paketmetadaten, die Syntax aus den Handbüchern.

### Schritt 3: Einen fiktiven Regelbestand lesen

Angenommen, eine Ansicht enthielte eine Tabelle der Familie `inet` und eine Basiskette mit Eingangs-Hook. Dann wären Familie und Einbindung Teil der Interpretation. Ein isoliert zitierter Regeltext ohne diese Angaben könnte den falschen Eindruck über seinen Geltungsbereich erzeugen.

### Schritt 4: Prüfung und Anwendung auseinanderhalten

Ein später geplanter Aufruf mit `-c -f` kann Gültigkeitsprobleme einer bekannten Datei aufdecken. Er braucht trotzdem passenden Kontext und kann auf Systemzustand zugreifen. Ein erfolgreicher Check beweist weder, dass Fernzugang erhalten bleibt, noch dass die gewünschte Anwendung erreichbar ist.

## 6. Typische Anwendungsfälle

- Einen ausdrücklich autorisierten Regelbestand strukturiert dokumentieren.
- Adressfamilien, Ketteneinbindung und Reihenfolge nachvollziehen.
- Eine bekannte Regeldatei vor einer geplanten Anwendung prüfen.
- Maschinenlesbare Zustandsdaten für einen kontrollierten Vergleich ausgeben.

Bei Vergleichen dynamische Zähler und veränderliche Mengen berücksichtigen. Unterschiede in solchen Feldern sind nicht automatisch unerwünschte Konfigurationsänderungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`flush ruleset` kann den gesamten Regelbestand leeren. Eine unbekannte Datei kann solche Befehle und weitere Dateien einbeziehen. `nft -f` ist deshalb kein einfacher Textbetrachter.

Falsche Regeln können Fernverwaltung unterbrechen, DNS oder VPN beeinträchtigen und Dienste ungewollt öffnen. Regeln aus verschiedenen Ketten können zusammenwirken; eine einzelne positive Entscheidung erklärt nicht zwangsläufig das endgültige Ergebnis des gesamten Paketwegs.

Regeln können sensible Adressen und Netzstruktur offenlegen. Auch lesende Ausgaben vor Weitergabe prüfen.

## 8. Häufige Fehler

- **`-f` für bloßes Lesen halten:** Enthaltene Befehle können angewendet werden.
- **Prüfmodus als Wirkungstest ansehen:** Syntax und reale Erreichbarkeit sind verschiedene Fragen.
- **Falsche Familie:** IPv4, IPv6 und gemeinsame Tabellen unterscheiden.
- **Altes Handle verwenden:** Bestand könnte sich inzwischen geändert haben.
- **Keine Berechtigung als leeren Regelsatz deuten:** Ein Fehler liefert keine solche Beobachtung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer numerischen Bestandsaufnahme und bekanntem Verwaltungsweg beginnen. Keine komplette fremde Firewallvorlage anwenden. Änderungen einzeln mit Ausgangszustand und Rückweg planen.

Bei Shellaufrufen Sonderzeichen der nft-Sprache bewusst behandeln. Eine Beispielsammlung, die für eine interaktive nft-Sitzung gedacht ist, lässt sich nicht immer unverändert in Bash einfügen.

## 10. Verwandte Befehle

- `iptables`, `ip6tables`: Andere Oberflächen, gegebenenfalls mit nftables-Backend.
- `firewall-cmd`, `ufw`: Übergeordnete Regelverwaltung.
- `ip`: Adressen, Links und Routing betrachten.
- `conntrack`: Verbindungszustände untersuchen, soweit installiert und autorisiert.

**Prüfstand:** Handbücher und Paketmetadaten geprüft. Lokale Initialisierung eingeschränkt; keine echte Regelansicht als gelesen ausgegeben und keine Firewall geändert.

Ausgangsdatensatz 321 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
