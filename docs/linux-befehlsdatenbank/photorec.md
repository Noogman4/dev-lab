---
id: "photorec"
name: "photorec"
command: "photorec"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["photorec", "forensik & recovery"]
status: "PhotoRec-Anleitung und Manpage geprüft; keine Wiederherstellung gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 337
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# photorec – Dateien anhand von Inhaltsmerkmalen wiedergewinnen

## 1. Kurzbeschreibung

`photorec` sucht nach erkennbaren Dateiinhalten und schreibt gefundene Daten in eine separate Ablage. Es rettet nicht nur Fotos, sondern unterstützt viele Dokument-, Archiv- und Medienformate.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Direkter Zugriff auf geschützte Datenträger erfordert zusätzliche Rechte. Rettungsdateien benötigen einen eigenen geeigneten Ausgabeort.

## 2. Was macht der Befehl?

PhotoRec arbeitet als File Carver. Es versucht, Inhalte anhand von Merkmalen zu erkennen, statt vollständig auf ursprüngliche Dateinamen und Verzeichnisstrukturen zu vertrauen. Diese Namen und Strukturen werden deshalb nicht zuverlässig wiederhergestellt.

Die [offizielle PhotoRec-Anleitung](https://www.cgsecurity.org/testdisk_doc/photorec.html) erklärt die interaktive Auswahl. Die [PhotoRec-Manpage](https://manpages.debian.org/trixie/testdisk/photorec.8.en.html) beschreibt die Aufrufformen.

Ein erfolgreicher Lauf bedeutet nicht automatisch, dass die gesuchte ursprüngliche Datei vollständig erhalten ist. Fragmente, eingebettete Vorschaubilder und doppelte Inhalte können erscheinen. Jedes Ergebnis braucht eine passende Qualitätsbewertung.

## 3. Syntax

```text
photorec [/log] [/debug] [/d AUSGABE] ABBILD
photorec /version
photorec /d ./rettung-lauf-01 ./analyse/arbeitskopie.img
```

Die mit Schrägstrich beginnenden Optionen gehören zur dokumentierten Syntax. Nicht ohne Prüfung durch gewöhnliche GNU-Schalter ersetzen. Das angegebene Abbild ist ein geplanter eigener Dateipfad, kein tatsächlich untersuchtes Medium.

## 4. Wichtige Optionen

| Auswahl | Aufgabe | Vorsicht |
| --- | --- | --- |
| `/version` | Programmversion zeigen. | Kein Rettungsnachweis. |
| `/log` | Protokoll erzeugen. | Zusätzliche Datei mit möglichen Details. |
| `/debug` | Diagnose erweitern. | Mehr Daten und gegebenenfalls größere Logs. |
| `/d VERZEICHNIS` | Ausgabeort vorgeben. | Darf nicht auf das betroffene Originaldateisystem führen. |
| `File Opt` | Gewünschte Dateitypen auswählen. | Auswahl verändert die Suche. |
| Suchbereich | Gesamten Bereich oder geeignete freie Bereiche wählen. | Unterstützung hängt von Struktur und Zustand ab. |
| `Keep corrupted files` | Auch beschädigte Ergebnisse behalten. | Mehr Nacharbeit, keine Qualitätsgarantie. |

Auswahlmöglichkeiten in der Oberfläche hängen von Version und erkanntem Dateisystem ab. Keine universelle feste Klickfolge für jedes beschädigte Medium annehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Arbeitskopie und ein Ziel voraussetzen

Angenommen, `./analyse/arbeitskopie.img` ist bereits freigegeben und unverändert verfügbar. Ein neuer eigener Ausgabeort besitzt genügend Platz. Es wird hier keine Aufnahme, Entschlüsselung oder Mountaktion vorgenommen.

### Schritt 2: Den geplanten Aufruf lesen

```text
photorec /d ./rettung-lauf-01 ./analyse/arbeitskopie.img
```

Der Aufruf würde die interaktive Rettungsoberfläche mit dieser Eingabe öffnen. Er wurde nicht gestartet; `photorec` ist lokal nicht installiert.

### Schritt 3: Quelle und Auswahl kontrollieren

Vor einem tatsächlichen Suchstart müsste die Anzeige zum bekannten Abbild passen. Dateisystemart und Suchbereich beeinflussen den Auftrag. Eine automatische Vorauswahl ist eine Hilfe, keine fachliche Bestätigung der gewünschten Quelle.

### Schritt 4: Ergebnisse getrennt bewerten

PhotoRec verwendet Ergebnisordner wie `recup_dir.1`. Die gefundenen Dateien werden zunächst als Rettungsergebnisse behandelt. Ein neuer Name oder lesbares Vorschaubild beweist weder den ursprünglichen Pfad noch die Vollständigkeit einer großen Originaldatei.

## 6. Typische Anwendungsfälle

- Dateien aus einer bekannten Kopie bei beschädigter Verzeichnisstruktur zu retten versuchen.
- Eine metadatenbasierte Rettung durch einen inhaltsbasierten Ansatz ergänzen.
- Bestimmte Medien- oder Dokumentinhalte unter bekanntem Untersuchungsumfang suchen.
- Gerettete Ergebnisse mit einer vorhandenen Sicherung vergleichen.

Ein Backup bleibt für die zuverlässige Wiederherstellung von Namen, Struktur und geprüften Inhalten häufig der bessere Ausgangspunkt. Carving dient einer anderen Ausgangslage.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ergebnisse nicht auf dem betroffenen Originaldateisystem speichern. Neue Schreibzugriffe können dort noch vorhandene Restdaten überschreiben. Auch die Installation des Rettungsprogramms auf diesem Dateisystem wäre im Verlustfall ungünstig.

Ausgaben können sehr viel Platz verbrauchen und vertrauliche gelöschte Inhalte enthalten. Zielkapazität und Zugriffsschutz vorher planen. Ein Ziel mit begrenzter maximaler Dateigröße kann für große Rettungsdateien ungeeignet sein.

Gefundene Programme oder aktive Dokumente nicht ungeprüft öffnen. Das Wiedergewinnen von Daten bestätigt ihre Vertrauenswürdigkeit nicht.

## 8. Häufige Fehler

- **Originalnamen erwartet:** PhotoRec rekonstruiert sie nicht zuverlässig.
- **Große Zahl gleich großer Erfolg:** Duplikate und Fragmente mitzählen wäre irreführend.
- **Ausgabe auf Quelle:** Kann weitere Rettung zerstören.
- **Zeitstempel als präzise Beweise:** Herkunft und Zeitzone sind mögliche Fehlerquellen.
- **Beschädigte Datei behalten gleich repariert:** Die Option rettet nicht automatisch ihre Struktur.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer eigenen bekannten Arbeitskopie beginnen und jeden Lauf getrennt ablegen. Suchauswahl und Ergebnisumfang dokumentieren. Gefundene Inhalte erst nach Sichtung in die normale Ablage übernehmen.

Bei wichtigen oder physisch fehlerhaften Originalmedien nicht eine Folge ungeplanter Rettungsversuche starten. Zuerst einen geeigneten Aufnahme- und Rettungsplan festlegen.

## 10. Verwandte Befehle

- `testdisk`: Andere Analyse- und Wiederherstellungsfunktionen.
- `foremost`, `scalpel`: Weitere Carving-Werkzeuge.
- `extundelete`: Anderer Ansatz mit Dateisysteminformationen.
- `fls`, `icat`: Metadatenbasierte Betrachtung und Extraktion.
- `sha256sum`: Ergebnisse identifizieren und bekannte Referenzen vergleichen.

**Prüfstand:** Herstelleranleitung und Manpage gelesen. Keine Oberfläche geöffnet, kein Datenträger gelesen und keine Rettungsdatei erzeugt.

Ausgangsdatensatz 337 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
