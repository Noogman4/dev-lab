---
id: "lspci"
name: "lspci"
command: "lspci"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["lspci", "hardware"]
status: "Keine PCI-Konfigurationsräume ausgelesen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 390
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale pciutils-Manpage 3.10.0 gelesen"
---

# lspci – PCI-Geräte und Treiberzuordnung mit begrenztem Zugriff anzeigen

## 1. Kurzbeschreibung

`lspci` zeigt PCI-Busse und angeschlossene Geräte. **Für die einfache Übersicht sind normalerweise keine Root-Rechte nötig.** Tiefe Konfigurationszugriffe können Rechte verlangen und besondere Risiken haben.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt numerische Hersteller-/Gerätekennungen, Namen und Treiberinformationen. Ein Name stammt gegebenenfalls aus einer Zuordnungsdatenbank. Er ist nicht gleich einer erfolgreich geprüften Gerätefunktion.

Eine Treiberzuordnung kann helfen, die Softwareseite zu verstehen. Sie beweist nicht, dass eine Anwendung das Gerät tatsächlich fehlerfrei benutzt.

## 3. Syntax

```bash
lspci -nn
lspci -nn -k
```

Diese geplanten Übersichten sind enger als Rohdumps des Konfigurationsraums. Es wurde kein tatsächlicher Busbericht des Rechners erstellt.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-nn` | Namen und numerische IDs. | Namen können von lokaler Datenbank abhängen. |
| `-k` | Aktive/geeignete Kernelmodule anzeigen. | Nicht jedes genannte Modul ist aktiv gebunden. |
| `-t` | Busstruktur als Baum. | Keine Funktionsprüfung. |
| `-s AUSWAHL` | Bestimmte Busposition auswählen. | Syntax und tatsächliche Identität prüfen. |
| `-mm` | Maschinenlesbarere Ausgabe. | Dokumentiertes Format verwenden. |
| `-q` | Zusätzliche Datenbankabfragen ermöglichen. | Netzwerk- und Cachebezug. |
| `-xxx`, `-xxxx` | Tiefe Konfigurationsdumps. | Nicht als normale Einsteigerdiagnose verwenden. |

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter `lspci -nn -k`-Aufruf würde IDs und Treiberkontext verbinden. Bei einem fiktiven Netzwerkgerät wäre zunächst die numerische Identität wichtig, danach der tatsächlich verwendete Treiber.

Die Ausgabe wurde nicht erhoben. Es wurde auch keine Online-ID-Abfrage ausgelöst. Für einen echten Supportbericht nur die benötigten Geräteangaben übernehmen.

Ein passender Gerätename allein bestätigt weder eine Netzwerkverbindung noch funktionierendes Routing. Die Anwendungsfrage bleibt gesondert.

## 6. Typische Anwendungsfälle

- Eine konkrete PCI-Komponente für einen Treiberfall zuordnen.
- IDs unabhängig vom angezeigten Marketingnamen festhalten.
- Aktive Treiberbindung und mögliche Module unterscheiden.
- Eine Busstruktur lesend verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Manpage warnt ausdrücklich, dass manche Geräte beim Lesen bestimmter Konfigurationsbereiche abstürzen können. Deshalb keine vollständigen tiefen Dumps nur wegen „mehr Details“ starten.

Zusatzoptionen für Onlineabfragen und Caches sind nicht rein lokale Anzeige. Für einfache Fragen reicht häufig die Standarddatenbasis.

## 8. Häufige Fehler

- **Modul genannt gleich benutzt:** Aktive Bindung unterscheiden.
- **Gerät erkannt gleich funktionsfähig:** Anderer Nachweis.
- **Tiefe Dumps als harmlos:** Geräteabhängige Risiken.
- **Fehlender Name gleich fehlendes Gerät:** Numerische IDs betrachten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit `-nn` und gegebenenfalls `-k` beginnen. Tiefe Rohzugriffe nur bei einer konkreten begründeten Fragestellung vorsehen.

Treiber nicht allein aufgrund eines Namenskonflikts entfernen oder ersetzen. Zunächst tatsächliche Bindung und benötigte Funktion klären.

## 10. Verwandte Befehle

- `lsusb`: USB-Ebene.
- `lshw`: Hardwarezusammenfassung.
- `modinfo`: Modulbeschreibung.
- `setpci`: PCI-Konfiguration verwalten; andere und potenziell verändernde Wirkung.

**Prüfstand:** Lokale Manpage gelesen. Kein PCI-Dump, Onlineabruf, Treiberwechsel oder Gerätezugriff ausgeführt.

Ausgangsdatensatz 390 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
