---
id: "vdir"
name: "vdir"
command: "vdir"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "verzeichnisse", "metadaten"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 206
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# vdir – Ausführliche Verzeichnisliste

## 1. Kurzbeschreibung

`vdir` listet Dateien standardmäßig in einer ausführlichen Darstellung ähnlich `ls -l` auf. Der gewöhnliche Aufruf ist lesend. **Für zugängliche eigene Verzeichnisse ist Root nicht nötig.**

## 2. Was macht der Befehl?

GNU `vdir` gehört zu coreutils. Es zeigt unter anderem Typ/Rechte, Linkanzahl, Besitzer, Gruppe, Größe, Änderungszeit und Namen. Ohne Pfad gilt das aktuelle Verzeichnis. Ein Listeneintrag beweist weder Dateiintegrität noch die Berechtigung, den Inhalt zu lesen. Grundlage ist die [GNU-vdir-Manpage](https://manpages.debian.org/trixie/coreutils/vdir.1.en.html).

## 3. Syntax

```bash
vdir [OPTION]... [DATEI ...]
vdir -h -- "Projekt"
vdir -a -- "Projekt"
```

`vdir` ist nicht `dir` und nicht zwingend identisch mit Shell-Aliassen für `ls`.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-a` | Versteckte Einträge einschließen. | Namen können sensibel sein. |
| `-A` | Fast alle, ohne `.` und `..`. | Übersichtlicher. |
| `-h` | Größen lesbar formatieren. | Gerundete Anzeige. |
| `-d` | Verzeichnis selbst anzeigen. | Nicht dessen Inhalt. |
| `-t` | Nach Änderungszeit sortieren. | Neueste zuerst. |
| `-S` | Nach Größe sortieren. | Kein Ersatz für `du`. |
| `-L` | Symlink-Zielmetadaten anzeigen. | Kann unerwartete Ziele betreffen. |
| `-R` | Rekursiv listen. | Viel Ausgabe möglich. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Testordner

```bash
uebung="$(mktemp -d -t netmon-vdir-XXXXXX)"
mkdir "$uebung/Projekt"
printf 'Test\n' > "$uebung/Projekt/datei.txt"
```

### Schritt 2: Standardliste

```bash
vdir -- "$uebung/Projekt"
```

Die Ausgabe sollte eine Zeile mit Dateimetadaten und `datei.txt` enthalten.

### Schritt 3: Größen lesbar darstellen

```bash
vdir -h -- "$uebung/Projekt"
```

Die Testdatei wird nicht verändert. Diese Beispiele sind **nicht praktisch geprüft**.

## 6. Typische Anwendungsfälle

**Rechte prüfen:** Vor Änderungen Metadaten betrachten. **Dateibestand vergleichen:** Namen und Änderungszeiten überblicken. **Fehleranalyse:** Symlinks und Besitzverhältnisse sichtbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Normalerweise kein Schreibzugriff. Risiken bestehen durch Veröffentlichung sensibler Namen, umfangreiche rekursive Ausgabe und Fehlinterpretation der Metadaten. `-L` folgt für die Anzeige Links; es ist kein Sicherheitscheck. Rechteänderungen werden durch `vdir` selbst nicht vorgenommen.

## 8. Häufige Fehler

| Problem | Ursache | Vorgehen |
| --- | --- | --- |
| Eintrag fehlt | Versteckter Name. | Bei Bedarf `-A`. |
| Größe überrascht | Datei- statt Blockgröße. | `du` ergänzen. |
| Zugriff verweigert | Rechte auf Elternpfad. | Eigenen Pfad verwenden. |
| Reihenfolge anders | Locale/Sortieroption. | Optionen und Locale prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für einen ersten Blick `vdir -- ORDNER` verwenden, bei großen Beständen keinen rekursiven Aufruf. Ausgabe vor dem Teilen auf vertrauliche Namen prüfen.

**Prüfstand:** Debian-Manpage zu GNU coreutils 9.7 am 2026-11-13 gelesen. Keine lokale Version, kein Testaufruf, keine NetMon-Reader-Prüfung.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ls -l` | Ähnliche lange Liste. |
| `stat` | Ausführliche Metadaten. |
| `tree` | Baumansicht. |
| `du` | Belegte Dateisystemblöcke. |

**Ausgangseintrag:** `source_record` 206 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
