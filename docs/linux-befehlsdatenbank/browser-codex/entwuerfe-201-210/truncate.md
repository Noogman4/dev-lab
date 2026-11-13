---
id: "truncate"
name: "truncate"
command: "truncate"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "groesse", "datenverlust"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 203
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# truncate – Dateigröße gezielt ändern

## 1. Kurzbeschreibung

`truncate` setzt die logische Länge einer Datei. Beim Verkleinern gehen abgeschnittene Daten verloren; beim Vergrößern entsteht ein Bereich, der als Nullbytes gelesen wird. **Root ist für eigene beschreibbare Dateien nicht nötig.**

## 2. Was macht der Befehl?

Anders als ein Texteditor berücksichtigt `truncate` keine Datensatzgrenzen. Es ändert die Dateilänge unabhängig davon, ob Inhalte sinnvoll bleiben. Eine fehlende Datei wird normalerweise neu angelegt. Die [GNU-coreutils-Manpage](https://manpages.debian.org/trixie/coreutils/truncate.1.en.html) erläutert auch Größenpräfixe und relative Größen.

## 3. Syntax

```bash
truncate -s GROESSE -- DATEI
truncate -c -s 0 -- DATEI
truncate -r REFERENZ -- DATEI
```

`-s 0` leert eine bestehende Datei vollständig. Die zweite Zeile verhindert nur das **Neuanlegen**, nicht das Leeren.

## 4. Wichtige Optionen

| Option | Bedeutung | Vorsicht |
| --- | --- | --- |
| `-s`, `--size=SIZE` | Zielgröße setzen. | Kleinere Größe schneidet Daten ab. |
| `-c`, `--no-create` | Keine neue Datei anlegen. | Vorhandene Datei bleibt veränderbar. |
| `-r DATEI` | Größe an Referenz ausrichten. | Inhalt wird nicht kopiert. |
| `-o`, `--io-blocks` | Größe in I/O-Blöcken interpretieren. | Blockgröße ist kontextabhängig. |
| `+N`, `-N` bei `-s` | Relative Vergrößerung/Verkleinerung. | Nicht mit negativen absoluten Größen verwechseln. |
| `<N`, `>N` bei `-s` | Höchst- beziehungsweise Mindestgröße. | Shell-Operatoren stets zitieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Testdatei

```bash
uebung="$(mktemp -d -t netmon-truncate-XXXXXX)"
printf 'ABCDEFGH' > "$uebung/muster.txt"
wc -c < "$uebung/muster.txt"
```

### Schritt 2: Theoretisches Kürzen auf vier Bytes

```bash
truncate -s 4 -- "$uebung/muster.txt"
wc -c < "$uebung/muster.txt"
```

Erwartete logische Länge: vier Bytes, erwarteter Inhalt `ABCD`. Die restlichen Bytes sind nicht über `truncate` wiederherstellbar.

### Schritt 3: Nur Größeninformation prüfen

```bash
stat -c '%s Byte' -- "$uebung/muster.txt"
```

**Wichtig:** Das Beispiel ist dokumentiert, aber **nicht ausgeführt**. Nur eigene wegwerfbare Testdateien verwenden.

## 6. Typische Anwendungsfälle

**Testdateien:** Definierte Dateigrößen erzeugen. **Sparse-Dateien:** Eine Datei vergrößern, ohne jeden Block unmittelbar zu belegen. **Protokollrotation:** Nur in ausdrücklich dafür vorgesehenen Abläufen; bei laufenden Prozessen kann Abschneiden Daten und Konsistenz zerstören.

## 7. Risiken, Nebenwirkungen und Vorsicht

`-s 0` ist ein vollständiges Leeren, nicht ein sicheres Zurücksetzen. Sparse-Bereiche können später Speicher benötigen. Schreibzugriff auf laufend genutzte Dateien kann Anwendungen stören. Symlinks und Pfadverwechslungen erhöhen das Risiko. Weder `-c` noch `--` schützen vor Verlust am richtig benannten, aber falschen Ziel. Kein `sudo` als Standard.

## 8. Häufige Fehler

| Problem | Ursache | Maßnahme |
| --- | --- | --- |
| Datei leer | `-s 0` angewendet. | Nur aus Backup wiederherstellen. |
| Inhalt unvollständig | Größe verkleinert. | Vorher Sicherung und Ziel prüfen. |
| Speicherbelegung überrascht | Sparse-Datei / Dateisystem. | `stat` und `du` unterscheiden. |
| Ungültige Größe | Einheit oder Shell-Umleitung. | Größenargument zitieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor jeder Änderung `stat -c '%s %n'` ausführen und eine getrennte Kopie der eigenen Testdatei vorhalten. Zum Erlernen nur neue temporäre Dateien verwenden. `truncate` niemals unbesehen auf Logdateien, Datenbanken oder Systempfade anwenden.

**Prüfstand:** GNU-coreutils-9.7-Manpage am 2026-11-13 geprüft. Keine Laufzeittests und keine Wiederherstellung nachgewiesen; lokale Implementierung unbekannt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `stat` | Logische Größe anzeigen. |
| `du` | Belegte Blöcke anzeigen. |
| `cp` | Separate Sicherheitskopie eigener Dateien. |
| `fallocate` | Speicherbelegung gezielt beeinflussen. |

**Ausgangseintrag:** `source_record` 203 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
