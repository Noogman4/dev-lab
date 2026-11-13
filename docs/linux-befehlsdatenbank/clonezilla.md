---
id: "clonezilla"
name: "clonezilla"
command: "Clonezilla Live"
category: "Backup & Sync"
language: "de"
root_required: true
risk_level: "danger"
tags: ["backup & sync", "clonezilla"]
status: "Quellen geprüft; Live-System und Datenträgeraktionen nicht praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 62
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle Clonezilla-Live-Dokumentation geprüft"
---

# Clonezilla – Datenträgerabbilder planen und sicher einordnen

## 1. Kurzbeschreibung

Clonezilla ist eine Werkzeugsammlung zum Sichern, Wiederherstellen und Klonen von Partitionen oder ganzen Datenträgern. Typischerweise startet man dafür ein separates Clonezilla-Live-System. **Datenträgeraktionen benötigen administrative Rechte.** Das Lesen der Dokumentation benötigt kein Root.

Der Datenbankname `clonezilla` bezeichnet hier das Produkt und den Arbeitsablauf. Er ist keine Zusage, dass ein universeller Linux-Befehl `clonezilla --help` installiert ist. Die Suite verwendet unter anderem eigene `ocs-*`-Werkzeuge und weitere Imaging-Programme. Ein Live-Workflow lässt sich deshalb nicht durch einen erfundenen Einzeiler ersetzen.

## 2. Was macht der Befehl?

Clonezilla kann einen Datenträger als Sammlung von Image-Dateien sichern oder direkt auf einen anderen Datenträger kopieren. Ein solches Image ist nicht mit einer einzelnen normalen `.iso`-Datei gleichzusetzen. Welche Speicherbereiche gesichert werden, hängt unter anderem vom Dateisystem und verwendeten Werkzeug ab.

Wichtig sind zwei getrennte Rollen: **Quelle** enthält die zu erhaltenden Daten, **Ziel** nimmt Image oder Kopie auf. Beim Wiederherstellen wird der ausgewählte Zieldatenträger überschrieben. Die [offizielle Live-Dokumentation](https://clonezilla.org/clonezilla-live-doc.php) zeigt diese getrennten Abläufe für `savedisk`, `restoredisk` und direktes Klonen. Menüs und Beschriftungen können zwischen Live-Versionen abweichen.

## 3. Syntax

Für diesen Eintrag ist eine Menüfolge verständlicher als ein ausführbarer Datenträgerbefehl:

```text
Clonezilla Live starten
→ device-image
→ Sicherungsablage auswählen
→ savedisk: Datenträger als Image sichern

Clonezilla Live starten
→ device-image
→ vorhandene Sicherungsablage auswählen
→ restoredisk: Image auf ausgewählten Zieldatenträger zurückschreiben
```

Dies sind Ablaufmuster, keine Terminalbefehle. Die Wörter hinter den Pfeilen werden im passenden Dialog ausgewählt. Optionen von `ocs-sr` sind versionsabhängige Expertenparameter und dürfen nicht auf beliebige Programme übertragen werden.

## 4. Wichtige Optionen

| Auswahl | Zweck | Entscheidende Frage |
| --- | --- | --- |
| `device-image` | Mit einer Image-Sicherung arbeiten. | Wo liegt das vollständige Image-Verzeichnis? |
| `device-device` | Direkt zwischen Geräten kopieren. | Welches physische Gerät wird überschrieben? |
| `local_dev` | Lokales Gerät als Image-Ablage auswählen. | Ist diese Ablage wirklich getrennt von der Quelle? |
| `savedisk` | Ganzen Datenträger sichern. | Sind alle gewünschten Partitionen enthalten? |
| `restoredisk` | Ganzes Datenträgerimage zurückschreiben. | Darf das gewählte Ziel vollständig ersetzt werden? |
| Beginner-/Expert-Modus | Umfang der Einstellmöglichkeiten wählen. | Verstehst du die zusätzlichen Schalter tatsächlich? |

Das sind Menüentscheidungen, keine allgemeinen Kommandozeilenoptionen. Für Partitionsoperationen gibt es eigene Abläufe; nicht aus dem Namen auf identische Schutzwirkung schließen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen Plan statt einer Geräteaktion erstellen

Angenommen, ein ausgeschalteter Testrechner soll vor einem Umbau gesichert werden. Notiere Modell, Kapazität und eindeutige Hardwarekennungen des Quelllaufwerks. Lege fest, welches getrennte Medium die Sicherungsdateien aufnehmen soll. Kürzel wie `sda` können sich nach einem Neustart ändern und reichen nicht als Identifikation.

### Schritt 2: Sicherungsart festlegen

Für ein später wiederverwendbares Image ist `device-image` vorgesehen. Eine direkte Gerät-zu-Gerät-Kopie benötigt dagegen bereits den konkreten Ersatzdatenträger. Wähle nicht die direkte Kopie, wenn du eigentlich eine aufbewahrbare Sicherung wolltest.

### Schritt 3: Image-Ablage und Quelle getrennt prüfen

Im geplanten Live-Ablauf wird zunächst die Ablage eingebunden, anschließend die Quelle gewählt. Verwechsle diese Reihenfolge nicht mit „erst Ziel der Wiederherstellung auswählen“. Bei jedem Dialog Beschreibung und Geräteidentität prüfen. Ein großes Laufwerk ist nicht automatisch das richtige Laufwerk.

### Schritt 4: Wiederherstellung vorab mitdenken

Ein belastbarer Plan nennt ein entbehrliches Ersatzgerät und einen getrennten späteren Wiederherstellungstest. Dabei müssen Partitionsgrößen, Bootverfahren und eventuell verschlüsselte Bereiche berücksichtigt werden. Ein gültiges Image-Verzeichnis beweist noch nicht, dass die zurückgespielte Maschine startet.

### Schritt 5: Erwartetes Ergebnis benennen

Nach einer tatsächlich durchgeführten Sicherung wären ein vollständiges Image-Verzeichnis, Abschlussmeldung und Prüfprotokoll zu kontrollieren. Diese Dokumentation führt keine Sicherung aus und erzeugt keinen Nachweis dafür. Keine tatsächlichen Gerätenamen oder automatisch bestätigten Überschreibbefehle gehören in diese Übung.

## 6. Typische Anwendungsfälle

### Geplanter Hardwaretausch

Eine vorbereitete Sicherung vor einem Laufwerkstausch kann Rückkehrmöglichkeiten schaffen. Dateisicherung und Datenträgerimage können sich ergänzen: Für einzelne Dokumente ist eine normale Rücksicherung oft leichter handhabbar.

### Gleichartige Testrechner

Klonen kann die Bereitstellung erleichtern. Kopierte Rechner können aber identische Dateisystem-UUIDs, Maschinenkennungen oder andere gerätespezifische Zustände tragen. Ein geklontes System benötigt deshalb eine gesonderte Inbetriebnahmeprüfung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Wiederherstellung und direktes Klonen können sämtliche bisherigen Zieldaten verlieren lassen. Bestätigungsdialoge schützen nicht vor einer vorher falsch bestimmten Geräteidentität. Die Quelle sollte für konsistente Abbilder nicht gleichzeitig aktiv verändert werden.

Ein Image kann persönliche Daten, Schlüssel und gelöschte Datenreste enthalten. Sicherungsmedien entsprechend schützen; Kompression ist keine Verschlüsselung. Bei bereits defekten oder ausfallenden Medien kann wiederholtes Lesen zusätzlichen Ausfall provozieren. Dann ist geplante Datenrettung mit spezialisiertem Vorgehen statt einer routinemäßigen Clonezilla-Aktion gefragt.

## 8. Häufige Fehler

- **Image lässt sich nicht finden:** Nur einzelne Dateien statt des vollständigen Image-Verzeichnisses kopiert oder falsche Ablage gewählt.
- **Quell- und Zielgerät vertauscht:** Geräte nur anhand wechselnder Kurzbezeichnungen ausgewählt.
- **Abbild passt nicht aufs kleinere Ziel:** Genutzter Speicher und Partitionslayout verwechselt; spezielle Verkleinerung nicht voraussetzen.
- **Zurückgespieltes System bootet nicht:** Firmwaremodus, Bootloader, Partitionen und Hardware unterscheiden sich.
- **Geöffnete Programme fehlen konsistent:** Ein Datenträgerabbild ersetzt keinen anwendungsgerechten Export laufender Datenbanken.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die offiziellen Abläufe lesen und Quelle, Image-Ablage und späteres Wiederherstellungsziel schriftlich auseinanderhalten. Ein Probelauf gehört auf entbehrliche Testhardware. Automatische Bestätigung und Expertenoptionen erst verwenden, wenn ihre Wirkung einzeln verstanden wurde.

**Prüfstand:** Offizielle Clonezilla-Live-Ablaufübersicht geprüft. Clonezilla ist lokal nicht installiert. Kein Live-System gestartet, keine Geräte gelesen oder beschrieben, keine Sicherung oder Rücksicherung durchgeführt. Die aktuell verwendete Live-Version und konkrete Hardwarekompatibilität bleiben Prüfpunkte.

## 10. Verwandte Befehle

- `partclone`: dateisystemspezifisches Imaging-Werkzeug, Bestandteil möglicher Abläufe.
- `ddrescue`: Datenrettung mit Mapdatei bei Lesefehlern.
- `lsblk`: Geräte und Dateisystemstruktur zunächst lesend anzeigen.
- `borg`, `restic`: versionierte Sicherung einzelner Dateien und Verzeichnisse.
- `timeshift`: Systemzustände mit eigenem Wiederherstellungsmodell.

Ausgangseintrag: Datensatz 62 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
