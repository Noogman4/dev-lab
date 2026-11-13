---
id: "watch"
name: "watch"
command: "watch"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["monitoring", "terminal", "wiederholung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 207
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# watch – Befehlsausgabe wiederholt anzeigen

## 1. Kurzbeschreibung

`watch` führt einen angegebenen Befehl regelmäßig erneut aus und zeigt dessen Ausgabe im Terminal. Die Wiederholung ist nur so sicher wie der **ausgeführte Unterbefehl**. Für lesende eigene Befehle ist **kein Root nötig**.

## 2. Was macht der Befehl?

Bei procps-ng beträgt das Standardintervall zwei Sekunden. Standardausgabe und Fehlerausgabe werden angezeigt, bis der Nutzer abbricht. `watch` ist kein Dateisystemwerkzeug, sondern ein allgemeiner Beobachtungshelfer. Die [procps-ng-Manpage](https://www.man7.org/linux/man-pages/man1/watch.1%40%40procps-ng.html) dokumentiert Intervall und Exit-Bedingungen.

## 3. Syntax

```bash
watch [OPTIONEN] BEFEHL [ARGUMENTE ...]
watch -n 5 -- date
watch -n 3 -- stat -c %s DATEI
```

Je nach Version werden Argumente zu einem Shell-Befehl zusammengesetzt; Shell-Metazeichen und Zitierung sorgfältig behandeln.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-n SEK` | Wiederholintervall. | Zu klein erzeugt Last. |
| `-d` | Änderungen hervorheben. | Nur sichtbare Ausgabe. |
| `-g` | Bei sichtbarer Änderung beenden. | Bildschirmgröße beeinflusst Erkennung. |
| `-e` | Bei Fehler anhalten. | Fehlermeldung prüfen. |
| `-t` | Kopfzeile ausblenden. | Weniger Kontext. |
| `-p` | Möglichst zeitgenaue Starts. | Langsame Befehle bleiben langsam. |
| `-x` | Befehl direkt ausführen. | Nicht in allen Versionen identisch verfügbar; lokale Hilfe prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Harmlosen Befehl wählen

```bash
date
```

### Schritt 2: Wiederholung im Terminal starten

```bash
watch -n 5 -- date
```

Etwa alle fünf Sekunden erscheint die aktuelle Uhrzeit. Das ist ein **Anwendungsbeispiel**, kein ausgeführter Test.

### Schritt 3: Beenden

`Ctrl+C` im Terminal drücken. `watch` beendet dann seine laufende Beobachtung; bei lang laufenden Unterprozessen deren Zustand getrennt prüfen.

## 6. Typische Anwendungsfälle

**Status beobachten:** Wiederholt freien Speicher oder die Uhrzeit ansehen. **Dateigröße:** Mit `stat` eine eigene wachsende Datei beobachten. **Änderungen erkennen:** `-d` zur visuellen Hervorhebung nutzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`watch` kann destruktive Kommandos immer wieder ausführen. Zu kurze Intervalle verursachen CPU-, I/O- oder Netzlast; Netzabfragen gehören nicht in diese Übung. Bildschirm-/Logausgaben können Geheimnisse offenlegen. `watch` nicht mit `sudo` starten, wenn nur die Uhrzeit beobachtet werden soll.

## 8. Häufige Fehler

| Problem | Ursache | Vorgehen |
| --- | --- | --- |
| Ausgabe bleibt gleich | Befehl liefert konstante Werte. | Erst einzeln ausführen. |
| Unerwartete Shell-Wirkung | Falsche Quotierung. | Argumente prüfen; ggf. `-x`. |
| Hohe Last | Intervall zu klein. | Intervall vergrößern. |
| Ausgabe abgeschnitten | Terminal zu klein. | Befehl enger filtern. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vorher den Unterbefehl einmal ohne `watch` prüfen. Mit fünf Sekunden Intervall und ausschließlich lesenden Befehlen beginnen. Bei Skripten sicherstellen, dass sie wiederholbar und nebenwirkungsfrei sind.

**Prüfstand:** procps-ng-Manpage am 2026-11-13 gelesen. Kein interaktiver Terminaltest, keine lokale Version; `-x` und Shell-Quotierung sind bei abweichenden Implementierungen **Prüfpunkte**.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `date` | Harmloser Demo-Unterbefehl. |
| `stat` | Wiederholt Dateimetadaten lesen. |
| `tail -f` | Angehängte Logdaten verfolgen. |
| `top` | Interaktive Prozessbeobachtung. |

**Ausgangseintrag:** `source_record` 207 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
