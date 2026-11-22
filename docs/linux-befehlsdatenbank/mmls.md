---
id: "mmls"
name: "mmls"
command: "mmls"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["mmls", "forensik & recovery"]
status: "Offizielle Sleuth-Kit-Manpage geprüft; kein Abbild geöffnet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 336
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# mmls – Partitionsbereiche eines Laufwerksabbilds anzeigen

## 1. Kurzbeschreibung

`mmls` aus The Sleuth Kit zeigt die Bereichsaufteilung eines Datenträgerabbilds. Dazu gehören in einer Partitionstabelle zugeordnete Bereiche und gegebenenfalls weitere Verwaltungs- oder nicht zugeordnete Bereiche.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Das Programm kann die Bereichsstruktur ohne Mount betrachten. Es schreibt keine neue Partitionstabelle.

## 2. Was macht der Befehl?

Die [offizielle mmls-Manpage](https://www.sleuthkit.org/sleuthkit/man/mmls.html) beschreibt die Sicht auf das Volume-System. Diese Ebene ist von der Dateisystemebene zu unterscheiden: Eine Partitionstabelle beschreibt Bereiche; `fsstat` untersucht anschließend ein darin enthaltenes Dateisystem.

Nicht zugeordnet bedeutet nicht automatisch leer. Ebenso ist ein vorhandener Bereich nicht automatisch ein intaktes, vollständig lesbares Dateisystem. Die Aufteilung liefert Lageinformationen, keine vollständige Bewertung aller enthaltenen Daten.

Ein reines Partitionsabbild kann unmittelbar ein Dateisystem enthalten und gar keine übergeordnete Partitionstabelle besitzen. In diesem Fall ist ein fehlender Volume-Systembericht nicht zwangsläufig ein Defekt.

## 3. Syntax

```text
mmls [OPTIONEN] ABBILD
mmls -B laufwerk.img
mmls -t list
```

Das Beispiel setzt ein bekanntes vollständiges Laufwerksabbild voraus. Es wird hier nicht ausgeführt. Die Typenliste betrifft unterstützte Partitionierungssysteme, nicht sämtliche Dateisystemtypen.

## 4. Wichtige Optionen

| Option | Bedeutung | Abgrenzung |
| --- | --- | --- |
| `-t TYP` | Volume-Systemtyp vorgeben. | Nicht mit Dateisystemtyp verwechseln. |
| `-t list` | Unterstützte Typen anzeigen. | Kein tatsächliches Abbild analysiert. |
| `-i TYP` | Abbildformat auswählen. | Andere Ebene als die Partitionierung. |
| `-b BYTES` | Gerätesektorgröße festlegen. | Grundlage für Größen- und Positionsrechnung. |
| `-B` | Zusätzliche Größenangaben in Bytes ausgeben. | Die übrigen Positionen weiter mit ihrer Einheit lesen. |
| `-a` | Zugeordnete Datenbereiche auswählen. | Andere Bereichsarten können ausgeblendet werden. |
| `-A` | Nicht zugeordnete Bereiche auswählen. | Nicht automatisch eine Schadensdiagnose. |
| `-m` | Metadatenbereiche anzeigen. | Können andere Bereiche überlappen. |
| `-V` | Version ausgeben. | Großes V beachten. |

`-o` richtet eine Analyse auf ein versetzt beginnendes Volume-System aus. Ein solcher verschachtelter Fall benötigt eine bekannte Bezugsposition; nicht mit beliebigen Bytewerten experimentieren.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die richtige Eingabeebene bestimmen

Angenommen, `./analyse/laufwerk.img` ist eine freigegebene vollständige Arbeitskopie eines Laufwerks. Bei einem einzelnen Partitionsabbild wäre diese Annahme falsch und die weitere Auswahl anders.

### Schritt 2: Eine Übersicht planen

```text
mmls -B ./analyse/laufwerk.img
```

Dieser Aufruf wurde nicht ausgeführt, da `mmls` lokal nicht installiert ist. Es wurden keine tatsächlichen Partitionsnamen, Startwerte oder Größen gelesen.

### Schritt 3: Eine fiktive Position umrechnen

Angenommen, ein Dateisystem begänne bei Sektor `2048` und die bekannte Sektorgröße betrüge `512` Byte. Dann wäre die Byteposition `2048 × 512 = 1048576`. Diese Zahlen sind ein Rechenbeispiel, keine lokale Beobachtung.

Für einen Sleuth-Kit-Folgeaufruf mit einem Sektoroffset würde weiterhin der Sektorwert verwendet, nicht die errechnete Bytezahl. Eine Einheit ohne ihren Bezug zu übernehmen wäre fehlerhaft.

### Schritt 4: Zu einem Dateisystemwerkzeug wechseln

Mit der bestätigten Position könnte anschließend `fsstat` oder `fls` geplant werden. Erst diese Analyse beschreibt das enthaltene Dateisystem beziehungsweise dessen Einträge. `mmls` repariert bei diesem Übergang nichts.

## 6. Typische Anwendungsfälle

- Die Struktur eines bekannten Laufwerksabbilds überblicken.
- Einen passenden Dateisystembeginn für weitere Analyse bestimmen.
- Volume-Metadaten und Datenbereiche unterscheiden.
- Eine Aufnahme mit dokumentierter erwarteter Partitionierung vergleichen.

Bei überlappenden Metadatenbereichen nicht vorschnell eine unerlaubte Doppelbelegung behaupten. Verwaltungsebenen können bewusst denselben Adressraum beschreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Übersicht liest Daten. Ihre Fehlinterpretation kann jedoch gefährliche Folgebefehle vorbereiten, etwa einen falschen Ausschnitt oder eine falsche Reparatur. Lage und Einheiten deshalb vor jedem solchen Schritt unabhängig nachvollziehbar machen.

Eine Ausgabeumleitung schreibt eine neue Berichtsdatei. Sie darf nicht auf das Eingabeabbild zeigen. Der Bericht kann Namen oder Struktur eines privaten Datenträgers offenlegen.

## 8. Häufige Fehler

- **Partitionsabbild mit Laufwerksabbild verwechseln:** Eingabegrenze klären.
- **Byteposition als Sektoroffset einsetzen:** Einheiten getrennt notieren.
- **Sektorgröße stillschweigend annehmen:** Quelle oder Abbildformat berücksichtigen.
- **Nicht zugeordnet gleich leer:** Dort können Datenreste liegen.
- **Übersicht als Reparatur ansehen:** Das Werkzeug zeigt Struktur, es korrigiert sie nicht.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten Arbeitskopie und einer lesenden Übersicht beginnen. Für jede weitergegebene Lageangabe Startwert, Einheit und Sektorgröße gemeinsam notieren.

Keine Gerätepartition verändern, weil ein Bereich in der Übersicht ungewohnt aussieht. Zunächst untersuchen, welche Ebene und welches Format tatsächlich vorliegen.

## 10. Verwandte Befehle

- `fsstat`: Dateisystemstruktur an einer bekannten Lage lesen.
- `fls`: Dateinamen und Verzeichniseinträge betrachten.
- `icat`: Inhalt eines bekannten Dateisystemeintrags ausgeben.
- `fdisk`: Anderes Verwaltungswerkzeug mit möglichen Schreibaktionen.
- `testdisk`: Analyse und gegebenenfalls Wiederherstellung; nicht rein lesend in jeder Funktion.

**Prüfstand:** Herstellerhandbuch gelesen. Keine reale Partitionstabelle ausgelesen oder geändert; Rechenwerte sind ausdrücklich fiktiv.

Ausgangsdatensatz 336 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
