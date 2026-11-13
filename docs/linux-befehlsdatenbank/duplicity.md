---
id: "duplicity"
name: "duplicity"
command: "duplicity"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "duplicity"]
status: "Quellen und Hilfe geprüft; lokale Vollsicherung, Dateiliste und Rücksicherung mit eigenen Daten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 65
reviewed_at: "2026-11-13"
locally_checked_version: "duplicity 2.1.4"
---

# duplicity – Vollsicherungen und inkrementelle Dateiketten verwalten

## 1. Kurzbeschreibung

`duplicity` sichert Dateien in Vollsicherungen und darauf aufbauenden inkrementellen Sicherungen. Es unterstützt lokale und entfernte Speicherziele sowie Verschlüsselung. **Für eigene Dateien und ein eigenes beschreibbares Ziel ist Root nicht nötig.** Eine Sicherungskette ist mehr als eine einzelne beliebig verschiebbare Archivdatei.

## 2. Was macht der Befehl?

Eine Vollsicherung bildet den Ausgangspunkt. Weitere inkrementelle Stände speichern Änderungen und benötigen für eine spätere Wiederherstellung die passende vollständige Kette. Werden benötigte ältere Teile entfernt, kann ein neuerer Stand unbrauchbar werden.

Ein Ziel wird als URL angegeben. `file:///...` meint einen lokalen absoluten Pfad; andere Backends können Netzwerkverkehr und Zugangsdaten benötigen. Die [offizielle Referenz](https://duplicity.us/stable/duplicity.1.html) beschreibt Aktionen und Backend-URLs. Hier wurde lokal Version 2.1.4 geprüft; die aktuelle Online-Referenz behandelt eine neuere Ausgabe. Optionsnamen deshalb zusätzlich mit der installierten Hilfe vergleichen.

## 3. Syntax

```text
duplicity [OPTIONEN] full QUELLORDNER ZIEL_URL
duplicity [OPTIONEN] incremental QUELLORDNER ZIEL_URL
duplicity [OPTIONEN] list-current-files ZIEL_URL
duplicity [OPTIONEN] restore QUELL_URL NEUER_ZIELORDNER
```

Explizite Aktionsnamen vermeiden, dass ein Anfänger allein aus der Reihenfolge von URL und Pfad die Richtung ableiten muss. Für einzelne Rückgaben werden archivinterne relative Pfade verwendet, nicht beliebige Dateinamen aus dem Zielrechner.

## 4. Wichtige Optionen

| Option oder Aktion | Bedeutung | Vorsicht |
| --- | --- | --- |
| `full` | Neue Vollsicherungskette beginnen. | Braucht erneut Platz. |
| `incremental` | Auf vorhandener Kette aufbauen. | Passende Grundlage muss verfügbar sein. |
| `--archive-dir PFAD` | Lokale Metadatenablage bestimmen. | Gehört nicht mit der eigentlichen Sicherung verwechselt. |
| `--tempdir PFAD` | Temporäre Arbeitsdateien verlagern. | Genügend freien Platz bereitstellen. |
| `--dry-run` | Geplante Aktion ohne eigentliche Backend-Aktion berechnen. | Nicht als Wiederherstellungsnachweis verwenden. |
| `--no-encryption` | Ohne Verschlüsselung sichern. | Hier ausschließlich für unkritische eigene Testdaten. |
| `--path-to-restore PFAD` | Teil der Sicherung zurückholen. | Ältere Handbücher nennen auch andere Optionsnamen. |
| `verify --compare-data` | Gesicherte Daten zusätzlich mit lokalen Daten vergleichen. | Versionsabhängige Details und Datenzugriff beachten. |

Die ältere [Distributions-Manpage](https://manpages.debian.org/bookworm/duplicity/duplicity.1.en.html) zeigt historische Optionsnamen. Bei Widersprüchen ist für die konkrete Installation deren Hilfe entscheidend. Löschaktionen mit `--force` gehören nicht in einen ersten Übungslauf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgeschottete Übungsablage vorbereiten

Die Klammern erzeugen eine eigene Bash-Untersitzung. Beim ersten Fehler endet diese, bevor Folgeaktionen mit unvollständigen Pfaden stattfinden.

```bash
(
  uebung="$(mktemp -d -t netmon-duplicity-XXXXXX)" || exit 1
  mkdir "$uebung/daten" "$uebung/temp" || exit 1
  printf 'Eigene Testnotiz\n' > "$uebung/daten/notiz.txt" || exit 1
  export XDG_CACHE_HOME="$uebung/cache"
  export XDG_CONFIG_HOME="$uebung/config"
  export GNUPGHOME="$uebung/gnupg"
  dup=(duplicity --no-encryption --archive-dir "$uebung/archiv" --tempdir "$uebung/temp")
  "${dup[@]}" full "$uebung/daten" "file://$uebung/backup" || exit 1
  "${dup[@]}" list-current-files "file://$uebung/backup" || exit 1
  "${dup[@]}" restore "file://$uebung/backup" "$uebung/rueckgabe" || exit 1
  cmp -- "$uebung/daten/notiz.txt" "$uebung/rueckgabe/notiz.txt"
)
```

### Schritt 2: Aktionen und Ergebnis verstehen

`dup` ist ein Bash-Array für den gemeinsamen Programmaufruf. `"${dup[@]}"` erhält die einzelnen Argumente einschließlich Leerzeichen. Es handelt sich nicht um einen neuen Linux-Befehl.

`full` schreibt ausschließlich die kleine Testquelle ins neue lokale Sicherungsziel. `list-current-files` soll `notiz.txt` nennen. Diese Auflistung allein beweist nicht, dass sämtliche Archivdaten lesbar sind. Deshalb folgt eine echte Rücksicherung in einen vorher nicht vorhandenen Zielordner.

`cmp` muss ohne Ausgabe mit Rückgabewert 0 enden. Dann stimmen die Inhalte der zwei Testdateien überein. **Das Beispiel sichert unverschlüsselt.** Es ist kein Muster für vertrauliche echte Daten und prüft weder GnuPG-Schlüssel noch Passwortwiederherstellung.

## 6. Typische Anwendungsfälle

### Regelmäßige Dateistände

Wiederkehrende Sicherungen können Unterschiede gegenüber einem früheren Stand platzsparend speichern. In längeren Abläufen neue Vollsicherungen und nachvollziehbare Aufbewahrung einplanen.

### Einzelne ältere Datei zurückholen

Zuerst verfügbaren Sicherungszeitpunkt und relativen Archivpfad prüfen. Die Rückgabe in einen neuen Ordner vermeidet, dass der aktuelle Stand unbemerkt ersetzt wird.

### Entferntes Sicherungsziel

Ein unterstütztes Backend kann räumliche Trennung ermöglichen. Anmeldung, Transport, Verschlüsselung und Kosten sind zusätzliche Entscheidungen; der lokale Test macht darüber keine Aussage.

## 7. Risiken, Nebenwirkungen und Vorsicht

Sicherungen können viele Dateien und temporären Speicher erzeugen. Geheimnisse nicht in Befehlszeilen oder Shellhistorie schreiben. Passwort oder Schlüssel getrennt vom einzigen Sicherungsträger geschützt aufbewahren.

Manuelles Löschen einzelner Sicherungsvolumes kann Ketten beschädigen. Bereinigungsaktionen bewusst anhand der benötigten Wiederherstellungspunkte planen. Bei laufenden Datenbanken oder gleichzeitig geänderten Dateien ist die Anwendungskonsistenz nicht automatisch gegeben. Dateisystem-, Rechte- und Hardlink-Eigenschaften gesondert prüfen, statt nur eine fehlerfreie Abschlussmeldung zu lesen.

## 8. Häufige Fehler

- **URL und Pfad vertauscht:** Falsche Richtung; explizit `full` oder `restore` verwenden.
- **Nur jüngste Dateien aufbewahrt:** Ältere Kettenteile können weiter benötigt werden.
- **`file://` falsch zusammengesetzt:** Ein absoluter Linux-Pfad ergibt normalerweise drei Schrägstriche vor seinem ersten Verzeichnisnamen.
- **Dateiliste als Integritätsbeweis verstanden:** Sie kann aus Metadaten stammen.
- **Historische Option unbekannt:** Installierte Version und lokale Hilfe vergleichen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit unkritischen Testdaten beginnen und jede Sicherungsidee bis zur Rückgabe durchspielen. Für echte Daten Verschlüsselung ausdrücklich passend einrichten; den Übungsschalter `--no-encryption` nicht unbesehen übernehmen.

**Prüfstand:** duplicity 2.1.4 lokal festgestellt. Vollsicherung, Auflistung und Rücksicherung einer eigenen temporären Testdatei durchgeführt; alle drei Aktionen Status 0, Inhalte bytegleich. Keine Benutzerdateien oder entfernten Ziele verwendet. Inkrementelle Ketten, Verschlüsselung, Aufbewahrungsbereinigung und Metadatenvollständigkeit nicht praktisch geprüft.

## 10. Verwandte Befehle

- `deja-dup`: grafische Sicherungsanwendung; Backend hängt von der Version ab.
- `borg`, `restic`: andere verschlüsselte Repositorymodelle.
- `rsnapshot`: Dateisicherungsstände mit anderem Speicherverfahren.
- `cmp`: Rückgabe einer eigenen Testdatei inhaltlich vergleichen.

Ausgangseintrag: Datensatz 65 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
