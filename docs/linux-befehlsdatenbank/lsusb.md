---
id: "lsusb"
name: "lsusb"
command: "lsusb"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["lsusb", "hardware"]
status: "Keine tatsächlichen USB-Geräte abgefragt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 391
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale usbutils-Manpage 017 gelesen"
---

# lsusb – USB-Geräte, Busposition und IDs auseinanderhalten

## 1. Kurzbeschreibung

`lsusb` zeigt USB-Busse und Geräte. **Für eine einfache Übersicht sind üblicherweise keine Root-Rechte nötig; ausführliche Angaben können eingeschränkt sein.** Der Befehl hängt keine Dateisysteme ein.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt Bus-/Gerätenummern und Hersteller-/Produkt-IDs. Menschenlesbare Bezeichnungen werden aus verfügbaren Zuordnungsdaten abgeleitet.

Eine wechselnde Busposition ist keine dauerhafte Geräteidentität. Nach neuem Anstecken oder Neustart kann dieselbe Hardware anders nummeriert sein. Eine Produkt-ID wiederum kann auf vielen Geräten desselben Modells vorkommen.

## 3. Syntax

```bash
lsusb
lsusb -t
lsusb -d HERSTELLER:PRODUKT
```

Die ID-Platzhalter sind durch tatsächlich bekannte hexadezimale Werte zu ersetzen. Keine konkrete Gerätekennung dieses Rechners wurde dafür gelesen.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-t` | USB-Hierarchie anzeigen. | Nicht identisch mit physischem Steckplatznamen. |
| `-d ID:ID` | Nach Hersteller-/Produkt-ID filtern. | Identifiziert oft ein Modell, nicht ein Einzelstück. |
| `-s BUS:NUMMER` | Bus-/Gerätenummer auswählen. | Werte sind laufzeitabhängig und dezimal. |
| `-v` | Mehr Deskriptorinformationen. | Rechte und Geräteunterstützung beachten. |
| `-D GERÄTEPFAD` | Bestimmten Geräteknoten detailliert betrachten. | Laut lokaler Manpage privilegierter Zugriff. |
| `-V` | Programmversion. | Keine Gerätefunktionsprüfung. |

## 5. Beispiel erklärt Schritt für Schritt

Für eine fiktive Frage, an welchem Hub ein eigenes Gerät hängt, wäre `lsusb -t` ein passender geplanter Einstieg. Es zeigt die Struktur, ohne ein Laufwerk einzuhängen.

Der Aufruf wurde nicht ausgeführt. Die Dokumentation enthält keine tatsächlichen USB-Adressen oder Seriennummern des Benutzers.

Ein erkannter Massenspeichereintrag bedeutet noch nicht, dass dessen Dateisystem eingebunden, entschlüsselt oder fehlerfrei lesbar ist. Diese Vorgänge gehören zu anderen Ebenen.

## 6. Typische Anwendungsfälle

- Ein eigenes USB-Gerät in der Busübersicht zuordnen.
- Modell-IDs für einen Treiberfall angeben.
- Hubstruktur und Anbindung verstehen.
- Sichtbares Gerät von verwendbarer Anwendungsfunktion unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausführliche Abfragen können Geräteinformationen anfordern und Kennungen offenlegen. Nur benötigte Details betrachten und vor Weitergabe prüfen.

Keine Geräte anhand einer alten Busnummer automatisch abziehen, zurücksetzen oder umkonfigurieren. Die Nummer kann inzwischen zu einer anderen Instanz gehören.

## 8. Häufige Fehler

- **Busnummer als dauerhafte Seriennummer:** Laufzeitzuordnung.
- **Produkt-ID als Einzelgerätebeweis:** Mehrere gleiche Modelle möglich.
- **Massenspeicher sichtbar gleich gemountet:** Andere Ebene.
- **Fehlende Details gleich defekt:** Zugriffsrechte können begrenzen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit kurzer Übersicht und Struktur beginnen. Für ein einzelnes Gerät gezielt filtern, statt alle Deskriptoren zu sammeln.

USB-Geräte nicht für eine reine Dokumentationsprüfung neu verbinden. Bereits vorhandene Identität und gewünschter Eingriff müssen zu einer tatsächlichen Diagnose passen.

## 10. Verwandte Befehle

- `lspci`: Anderer Bus.
- `lsblk`: Blockgeräte und Dateisystembezug.
- `udevadm info`: Geräteinformationen mit anderer Auswahl.
- `lshw`: Zusammengefasster Hardwarebaum.

**Prüfstand:** Lokale Manpage gelesen. Kein USB-Gerät angesprochen, getrennt, zurückgesetzt oder gemountet.

Ausgangsdatensatz 391 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
