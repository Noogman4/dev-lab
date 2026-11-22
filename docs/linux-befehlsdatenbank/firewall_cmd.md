---
id: "firewall_cmd"
name: "firewall-cmd"
command: "firewall-cmd"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["firewall_cmd", "firewall & sicherheit"]
status: "Offizielle firewalld-Dokumentation geprüft; keine Firewallabfrage oder Änderung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 314
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# firewall-cmd – firewalld-Zonen und Regelzustände verwalten

## 1. Kurzbeschreibung

`firewall-cmd` ist die Kommandozeilenoberfläche für den Dienst `firewalld`. Sie kann Zonen und Freigaben abfragen oder verändern. Dabei sind aktuell wirksame Regeln und dauerhaft gespeicherte Konfiguration getrennt.

**Änderungen benötigen eine administrative Autorisierung.** Die konkrete Abfrageberechtigung hängt von der lokalen Richtlinie ab. Für die reine Programmhilfe sind keine Root-Rechte nötig.

## 2. Was macht der Befehl?

firewalld ordnet Verbindungen, Schnittstellen oder Quellen einer Firewallkonfiguration zu. Eine Freigabe in der falschen Zone kann wirkungslos bleiben oder an einer unerwarteten Schnittstelle gelten.

Das [offizielle firewall-cmd-Handbuch](https://firewalld.org/documentation/man-pages/firewall-cmd.html) erklärt die Oberfläche. Die gesonderte [Beschreibung von Laufzeit und dauerhafter Konfiguration](https://firewalld.org/documentation/configuration/runtime-versus-permanent.html) erläutert den Lebenszyklus.

Für die Planung müssen drei Fragen geklärt sein: Welche Verbindung ist betroffen? Welche Zone ist ihr zugeordnet? Soll die Änderung sofort, nach einem späteren Neuladen oder dauerhaft wirksam sein? Eine kopierte Portfreigabe ohne diesen Zusammenhang ist keine vollständige Konfiguration.

## 3. Syntax

```text
firewall-cmd [OPTIONEN]
firewall-cmd --help
firewall-cmd --get-active-zones
firewall-cmd --zone=ZONE --list-all
```

`ZONE` ist durch einen tatsächlich vorhandenen Namen zu ersetzen. Die letzten beiden Formen lesen Zustände; sie wurden hier nicht ausgeführt. Der Client ist lokal nicht installiert.

## 4. Wichtige Optionen

| Option | Zweck | Abgrenzung |
| --- | --- | --- |
| `--help` | Bedienung anzeigen. | Keine Freigabe. |
| `--state` | Dienstzustand abfragen. | Kein vollständiger Erreichbarkeitstest. |
| `--get-active-zones` | Aktive Zuordnungen anzeigen. | Wichtig vor einer zonenbezogenen Entscheidung. |
| `--zone=NAME` | Zone auswählen. | Sonst kann die Standardzone gemeint sein. |
| `--list-all` | Konfiguration der ausgewählten Zone anzeigen. | Nicht automatisch sämtliche Filter jeder Verwaltungsebene. |
| `--permanent` | Dauerhafte Konfiguration adressieren. | Eine Änderung gilt dadurch nicht automatisch sofort. |
| `--reload` | Dauerhafte Einstellungen neu übernehmen. | Kann reine Laufzeitänderungen ersetzen. |
| `--runtime-to-permanent` | Laufzeitkonfiguration dauerhaft speichern. | Kann gespeicherte Einstellungen überschreiben. |

`--add-service` und `--remove-service` verändern Freigaben. Eine Dienstfreigabe und ein tatsächlich gestarteter Netzwerkdienst sind außerdem unterschiedliche Dinge.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die Fragestellung begrenzen

Angenommen, eine Anwendung ist über eine bestimmte Verbindung nicht erreichbar. Zuerst prüfen, ob die Ursache tatsächlich in firewalld liegt. Eine fehlende Anwendung oder ein falscher Zielport wird durch eine Firewallfreigabe nicht behoben.

### Schritt 2: Zuordnung vor der Regel lesen

```text
firewall-cmd --get-active-zones
firewall-cmd --zone=public --list-all
```

Die zweite Zeile ist nur dann passend, wenn die erste beziehungsweise die bekannte Konfiguration tatsächlich die Zone `public` als relevant ergibt. Die Befehle sind ein nicht ausgeführter Diagnoseplan und keine Aussage über diesen Rechner.

### Schritt 3: Dauerhaftigkeit bewusst vergleichen

Eine zusätzliche Abfrage derselben Zone mit `--permanent` würde die gespeicherte Seite betrachten. Unterschiede zur Laufzeit sind möglich und müssen nicht automatisch ein Fehler sein. Sie können auf eine beabsichtigte vorläufige Änderung zurückgehen.

### Schritt 4: Kein Neuladen ohne Bedarf

Eine reine Bestandsaufnahme benötigt keinen Reload. Erst ein getrennt geplanter Änderungsauftrag darf entscheiden, welche gespeicherte Konfiguration in die Laufzeit übernommen wird und welcher Rückweg besteht.

## 6. Typische Anwendungsfälle

- Die wirksame Zone einer Verbindung nachvollziehen.
- Aktuelle und dauerhaft gespeicherte Freigaben vergleichen.
- Eine geplante einzelne Freigabe im passenden Bereich vorbereiten.
- Nach einer autorisierten Änderung den erwarteten Zustand abfragen.

Eine Abfrage dokumentiert Konfiguration. Ein tatsächlicher Verbindungstest ist ein weiterer Schritt mit eigener Quelle, Zieladresse und Fragestellung. Er wird durch eine Regelauflistung nicht ersetzt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine falsche Änderung kann Fernzugang, DNS, VPN oder Anwendungen unterbrechen. Zu breite Freigaben können Dienste an unerwünschten Schnittstellen erreichbar machen. Bei Fernadministration muss ein unabhängiger Rückweg bestehen.

`--complete-reload` kann Zustandsinformationen und aktive Verbindungen beeinträchtigen. Es ist kein gewöhnlicher Aktualisierungsknopf. Auch ein normaler Reload verändert Regeln und gehört nicht in eine rein lesende Diagnosefolge.

Nicht gleichzeitig mit mehreren Verwaltungswerkzeugen dieselben Regeln unkoordiniert verändern. Sonst kann eine scheinbar lokale Korrektur von einem anderen Dienst wieder überschrieben werden.

## 8. Häufige Fehler

- **Regel ohne Wirkung:** Falsche Zone oder Verbindung ausgewählt.
- **Nach Neustart verschwunden:** Nur Laufzeit geändert.
- **Gespeichert, aber noch unwirksam:** Nur dauerhafte Seite geändert.
- **Dienst läuft, Verbindung scheitert:** Dienstzustand beweist keine passende Regel und keinen funktionierenden Zielprozess.
- **Reload beseitigt Sonderregel:** Der vorläufige Zustand war nicht dauerhaft übernommen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Abfragen und einer konkreten Verbindung beginnen. Vor einer Änderung Ausgangszustand, gewünschte Freigabe und zeitlichen Umfang beschreiben. Nie pauschal die Firewall abschalten, um eine unklare Ursache zu testen.

Für zeitlich begrenzte Freigaben existieren je nach Operation Timeoutmöglichkeiten. Unterstützung und Geltungsbereich zunächst im lokalen Handbuch prüfen, statt einen Timeout als allgemeine Rücknahmegarantie anzunehmen.

## 10. Verwandte Befehle

- `firewall-offline-cmd`: Andere Betriebsart für Offlinekonfiguration.
- `nmcli`: Verbindungs- und unter Umständen Zonenzuordnungen betrachten.
- `nft`: Unterliegende Netfilter-Regeln verwalten.
- `ufw`: Alternatives Verwaltungswerkzeug; Betriebskonzept vor parallelen Änderungen klären.

**Prüfstand:** Herstellerdokumentation gelesen. Kein Dienstkontakt und keine Änderung an Firewall, Schnittstellen oder dauerhaften Konfigurationsdateien.

Ausgangsdatensatz 314 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
