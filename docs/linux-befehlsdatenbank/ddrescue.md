---
id: "ddrescue"
name: "ddrescue"
command: "ddrescue"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "danger"
tags: ["backup & sync", "ddrescue"]
status: "Quellen geprüft; eigenes Dateibeispiel und Fehlerrettung praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 63
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; GNU-ddrescue-Manpage geprüft"
---

# ddrescue – Daten mit einer fortsetzbaren Rettungskarte kopieren

## 1. Kurzbeschreibung

GNU `ddrescue` kopiert Daten und versucht bei Lesefehlern zunächst erreichbare Bereiche zu retten. Eine Mapdatei hält fest, welche Bereiche erfolgreich gelesen wurden und welche noch fehlen. **Für normale eigene Dateien sind keine Root-Rechte nötig.** Zugriff auf Blockgeräte benötigt häufig erhöhte Rechte; das ist hier nicht freigegeben.

Die hohe Risikostufe entsteht aus der möglichen Verwechslung von Quelle und Ziel sowie der Arbeit an ausfallenden Medien. Das Werkzeug stellt nicht automatisch gelöschte Dateinamen wieder her und repariert kein Dateisystem. Unter Debian heißt das Paket `gddrescue`, der Befehl aber `ddrescue`.

## 2. Was macht der Befehl?

Der Kopiervorgang arbeitet mit Bereichen und einem dokumentierten Rettungsstand. Statt an einem einzigen Lesefehler dauerhaft hängen zu bleiben, können zunächst andere Bereiche kopiert und später weitere Versuche unternommen werden. Die genaue Strategie hängt von Optionen und Version ab.

Die [GNU-ddrescue-Manpage bei Debian](https://manpages.debian.org/trixie/gddrescue/ddrescue.1.en.html) beschreibt die Mapdatei und warnt vor der Wiederverwendung einer unpassenden alten Karte. Quelle, Ausgabedatei und Mapdatei bilden einen zusammengehörenden Vorgang. Eine Mapdatei ist kein Ersatz für die geretteten Daten.

## 3. Syntax

```text
ddrescue [OPTIONEN] EINGABE AUSGABE [MAPDATEI]
```

Die Reihenfolge ist entscheidend: erst lesen, dann schreiben, zuletzt den Fortschritt verwalten. Anders als bei `dd` stehen hier keine `if=`- und `of=`-Argumente. Obwohl die Mapdatei syntaktisch optional ist, sollte eine ernsthafte Rettung eine passende Karte verwenden. Ohne sie fehlt die verlässliche Grundlage zum Fortsetzen.

## 4. Wichtige Optionen

| Option | Bedeutung | Praktischer Hinweis |
| --- | --- | --- |
| `-n`, `--no-scrape` | Scraping-Phase auslassen. | Ist kein allgemeiner Dry-Run; Ausgabe wird geschrieben. |
| `-r N`, `--retry-passes=N` | Anzahl zusätzlicher Wiederholungsdurchläufe festlegen. | Mehr Versuche können ein geschädigtes Medium stärker belasten. |
| `-d`, `--idirect` | Direkten Eingabezugriff verwenden. | Geräte-/Ausrichtungsanforderungen prüfen; nicht wahllos setzen. |
| `-f`, `--force` | Schreiben auf ein Ausgabe-Gerät erlauben. | Hebt eine wichtige Schutzschranke auf. |
| `-s BYTES`, `--size=BYTES` | Rettungsbereich begrenzen. | Andere Bereiche werden dadurch nicht gerettet. |
| `-b BYTES`, `--sector-size=BYTES` | Sektorgröße angeben. | Falsche Annahmen beeinflussen die Rettung. |
| `-V`, `--version` | Version anzeigen. | Vor Übernahme fremder Optionen prüfen. |

Expertenmodi wie Fill- oder Generate-Modus ändern die Aufgabe grundlegend. Sie gehören nicht als vermeintliche Beschleunigung in einen gewöhnlichen Kopiervorgang.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur eine eigene kleine Datei vorbereiten

Dieses Beispiel beschreibt einen ungefährlichen Dateivergleich mit installiertem GNU ddrescue. Es simuliert keinen Festplattenschaden und wurde hier mangels Programm nicht ausgeführt.

```bash
(
  uebung="$(mktemp -d -t netmon-ddrescue-XXXXXX)" || exit 1
  printf 'Erste Testzeile\nZweite Testzeile\n' > "$uebung/quelle.txt" || exit 1
  ddrescue -n "$uebung/quelle.txt" "$uebung/kopie.txt" "$uebung/probe.map" || exit 1
  cmp -- "$uebung/quelle.txt" "$uebung/kopie.txt" || exit 1
  printf 'Eigener Testordner: %s\n' "$uebung"
)
```

Der neue Ordner verhindert Konflikte mit bestehenden Zieldateien. `quelle.txt` ist die einzige Eingabe. `kopie.txt` und `probe.map` sind unterschiedliche neue Dateien. Hier fehlt absichtlich `-f`: Es wird kein Gerät als Ziel benötigt.

### Schritt 2: Erwartetes Ergebnis prüfen

Bei fehlerfreier eigener Eingabe sollte `cmp` ohne Ausgabe mit Status 0 enden. Das zeigt die Inhaltsgleichheit dieser zwei kleinen Dateien. Die Mapdatei dokumentiert den Kopierstand. Zahlen wie erfolgreiche Bytes oder Fehlbereiche beschreiben nur diesen Vorgang; ein Erfolg mit einer Textdatei beweist keine Gerätekompatibilität.

### Schritt 3: Fortsetzung richtig einordnen

Ein echter abgebrochener Rettungsversuch darf nur mit derselben eindeutig bestimmten Quelle, der dazugehörigen Ausgabe und passender Karte fortgesetzt werden. Nach Neustart können Gerätenamen wechseln. Dieses Beispiel liefert bewusst keinen Folgeaufruf gegen ein reales Gerät und keine Aufforderung, künstlich Fehler auf Datenträgern zu erzeugen.

## 6. Typische Anwendungsfälle

### Lesefehler auf einem Medium

Ziel ist zunächst eine möglichst gute Kopie auf einem gesunden, ausreichend großen getrennten Speicher. Dateisystemanalysen werden anschließend an einer Arbeitskopie geplant. Reparaturen direkt auf der ursprünglichen Problemquelle können die Ausgangslage verschlechtern.

### Unterbrochener großer Kopiervorgang

Die Mapdatei ermöglicht, einen bekannten Stand weiterzuverwenden. Dafür müssen Quelle und Ausgabe unverändert zusammenpassen. Ein gleicher Dateiname oder eine ähnliche Kapazität reicht als Identifikation nicht.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein vertauschtes Ziel kann bereits vorhandene Daten überschreiben. `--force` ist keine Reparaturoption. Auch ohne diesen Schalter können gewöhnliche Ausgabedateien verändert werden; daher nie ein wichtiges bestehendes Dokument als Ziel nennen.

Ein mechanisch beschädigtes Medium kann während weiterer Leseversuche vollständig ausfallen. Bei unersetzlichen Daten vor eigenen Experimenten professionelle Hilfe erwägen. Fehlende Bereiche können im Ergebnis unvollständig oder durch früher vorhandenen Zielinhalt geprägt sein; eine vorhandene Ausgabedatei bedeutet nicht vollständige Rettung.

Die Quelle währenddessen nicht gleichzeitig beschreiben, einbinden oder reparieren lassen. Bei verschlüsselten Daten müssen spätere Entschlüsselung und benötigte Schlüssel gesondert berücksichtigt werden. Ein Rohabbild schützt vertrauliche Inhalte nicht automatisch durch Verschlüsselung.

## 8. Häufige Fehler

- **`dd_rescue` statt `ddrescue`:** Unterschiedliche Programme mit unterschiedlichen Optionen.
- **Karte von anderem Vorgang verwendet:** Kann fehlende oder bereits erledigte Bereiche falsch zuordnen.
- **`-n` als Vorschau verstanden:** Der Kopiervorgang schreibt tatsächlich.
- **Zu wenig Platz am Ziel:** Ausgabedatei und Mapdatei benötigen verfügbaren Speicher.
- **Alle Bytes gelesen, Anwendung trotzdem kaputt:** Lesbarkeit beweist keine logische Dateisystem- oder Anwendungsintegrität.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die Argumentreihenfolge an einem eigenen Dateibeispiel verstehen. Mapdateien geschützt aufbewahren und dem konkreten Vorgang eindeutig zuordnen. Keine Rettung mit allgemeinen „schneller“-Schaltern beginnen, deren Wirkung unklar ist.

**Prüfstand:** Distributions-Manpage zu GNU ddrescue gelesen. Programm lokal nicht installiert; keine lokale Programmversion bestätigt. Beispiel nicht ausgeführt. Keine Fehler simuliert, Geräte geöffnet, Reparaturen gestartet oder Rettungserfolge nachgewiesen. Direkter Zugriff, Wiederholungsstrategie und Verhalten bei echten Schäden bleiben offen.

## 10. Verwandte Befehle

- `ddrescuelog`: Mapdateien mit eigenem Funktionsumfang auswerten.
- `dd`: einfacher Datenkopierer ohne dasselbe Rettungsmodell.
- `partclone`: dateisystembezogene Abbilder gesunderer Ausgangslagen.
- `cmp`: zwei Dateien byteweise vergleichen.
- `lsblk`: Geräte zunächst lesend identifizieren; Ausgabe allein ersetzt keine sichere Zuordnung.

Ausgangseintrag: Datensatz 63 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
