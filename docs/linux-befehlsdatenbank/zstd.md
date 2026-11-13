---
id: "zstd"
name: "zstd"
command: "zstd"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive & kompression", "zstd"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 28
reviewed_at: "2026-11-13"
locally_checked_version: "Zstandard CLI 1.5.5"
---

# zstd – Daten mit Zstandard komprimieren und zurückgewinnen

## 1. Kurzbeschreibung

`zstd` ist das Kommandozeilenwerkzeug für Zstandard-Kompression. Es komprimiert Datenströme, dekomprimiert sie und bietet Test- sowie Informationsmodi.

**Für eigene Dateien sind keine Root-Rechte nötig.** Standardmäßig bleiben Eingaben erhalten. Ausgaben werden neu geschrieben; `--rm` kann Quellen nach Erfolg entfernen. Deshalb ist nicht jede Betriebsart nur lesend.

## 2. Was macht der Befehl?

Aus einer Datei kann eine komprimierte `.zst`-Datei entstehen. Mehrere Eingaben werden normalerweise einzeln behandelt. Eine `.zst`-Datei verwaltet keine allgemeine Sammlung benannter Ordner und Dateien wie ZIP. Für solche Sammlungen häufig zunächst TAR verwenden.

Kompressionsvorgaben beeinflussen Aufwand, Speicherbedarf und Ergebnisgröße. Ein hoher Wert ist nicht für jede Eingabe oder jedes Zielgerät sinnvoll. Die Wiederherstellung muss mit den tatsächlich gewählten Parametern und gegebenenfalls einem zusätzlichen Wörterbuch möglich bleiben.

Quellen: [offizielle CLI-Referenz 1.5.7](https://raw.githubusercontent.com/facebook/zstd/v1.5.7/programs/zstd.1.md) und die lokal geprüfte Hilfe der Version 1.5.5. Lokal nicht vorhandene beziehungsweise nicht getestete Zusatzfunktionen sind keine zugesicherten Eigenschaften dieses Rechners.

## 3. Syntax

```text
zstd [OPTIONEN] [EINGABE ...] [-o AUSGABE]
```

```bash
zstd "notiz.txt"
zstd "notiz.txt" -o "eigener-name.zst"
zstd -d "notiz.txt.zst" -o "wiederhergestellt.txt"
```

Ohne abweichenden Modus wird komprimiert. Ohne Eingabedatei beziehungsweise mit `-` kann stdin verarbeitet werden. Explizite Ausgabe mit `-o` ist für kontrollierte Dateinamen hilfreich; `-c` wählt stattdessen stdout.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-d`, `--decompress` | Dekomprimieren. | Gegenrichtung zum normalen Modus. |
| `-t`, `--test` | Daten verarbeiten und Ausgabe verwerfen. | Vorhandene unterstützte Inhaltsprüfwerte prüfen. |
| `-l` | Zstandard-Dateiinformationen anzeigen. | Keine Liste von TAR-Mitgliedern. |
| `-o DATEI` | Ausgabepfad festlegen. | Vorhandene Ziele bewusst behandeln. |
| `-c`, `--stdout` | Daten auf stdout schreiben. | Umleitungen können trotzdem bestehende Dateien überschreiben. |
| `-k`, `--keep` | Eingabe erhalten. | Bereits Standard. |
| `--rm` | Quelle nach erfolgreicher Verarbeitung entfernen. | Für erste Versuche vermeiden. |
| `-1` bis `-19` | Kompressionsstufe wählen. | Standard ist hier `3`; Nutzen datenabhängig. |
| `--ultra` | Höhere Stufen bis zur unterstützten Obergrenze freigeben. | Deutlich mehr Ressourcen möglich. |
| `--fast[=N]` | Schnellere Kompressionsvorgabe. | Anderer Parameterbereich, keine feste Geschwindigkeitsgarantie. |
| `-T N` | Kompressions-Threads wählen. | `0` wählt automatisch; Build und RAM beachten. |
| `-D DATEI` | Wörterbuch verwenden. | Wird für spätere Wiederherstellung benötigt. |
| `--check`, `--no-check` | Inhaltsprüfwert einschalten beziehungsweise weglassen. | Standardmäßig eingeschaltet; kein Herkunftsnachweis. |
| `-f`, `--force` | Schutzregeln übergehen. | Überschreiben und Durchreichen fremder stdout-Daten möglich. |
| `-M128MB` | Beispiel eines Decoder-Speicherlimits. | Keine allgemeine Plattenplatzquote. |

Langstreckenparameter, Wörterbuchtraining und Patch-Verfahren gehören zu speziellen Arbeitsabläufen. Sie benötigen eigene Kompatibilitäts- und Wiederherstellungstests, nicht bloß eine kleinere erzeugte Datei.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsbereich schaffen

```bash
zstd --version
uebung="$(mktemp -d -t netmon-zstd-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel weitermachen.

### Schritt 2: Bekannte Datei erzeugen

```bash
printf '%s\n' 'Eigene ZSTD-Testnotiz.' > "notiz.txt"
```

Die Umleitung schreibt ausschließlich eine neue Übungsdatei. Für weitere Versuche einen neuen Ordner wählen.

### Schritt 3: Standardkompression verwenden

```bash
zstd "notiz.txt"
```

Danach werden `notiz.txt` und `notiz.txt.zst` erwartet. Das Original bleibt erhalten. Bei einer kleinen Testdatei kann Formatverwaltung den Platzgewinn überwiegen.

### Schritt 4: Informationen und Test unterscheiden

```bash
zstd -l "notiz.txt.zst"
zstd -t "notiz.txt.zst"
```

Die Liste beschreibt bestimmte Dateieigenschaften. Der Test verarbeitet die Daten. Keine der beiden Zeilen stellt die ursprüngliche Datei unter einem neuen Namen wieder her.

### Schritt 5: In freie Ausgabe zurücklesen

```bash
zstd -d "notiz.txt.zst" -o "wiederhergestellt.txt"
cmp "notiz.txt" "wiederhergestellt.txt"
```

Bei bytegleichem Inhalt bleibt `cmp` normalerweise ohne Ausgabe und endet erfolgreich. Die komprimierte Quelle bleibt ohne `--rm` erhalten.

## 6. Typische Anwendungsfälle

**Einzeldateien komprimieren:** Geeignete Stufe anhand eigener Daten und benötigter Ressourcen wählen, statt pauschal maximale Kompression zu verlangen.

**Dateisammlungen verpacken:** Eine bewusst erstellte TAR-Datei als Strom komprimieren. Archivstruktur und vollständige Metadatensicherung bleiben Aufgaben des Archivverfahrens.

**Wiederholte ähnliche Inhalte verarbeiten:** Ein Wörterbuch kann bei bestimmten Daten helfen. Es muss unabhängig verfügbar bleiben und ist Teil der Wiederherstellungsvoraussetzungen.

**Verarbeitungsketten:** stdin und stdout vermeiden bestimmte Zwischenkopien. Fehlerbehandlung, Ausgabepfade und Empfänger müssen dabei ausdrücklich geplant werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Originalerhalt ist eine bewusste Eigenschaft

Zstandard behält Quellen normalerweise. Nicht dieselben Annahmen wie bei `gzip` oder `xz` übernehmen. `--rm` ändert diesen Standard. Bestehende Ausgaben und Umleitungen können trotzdem Datenverlust verursachen.

### Kompressionsgewinn kann Folgekosten erzeugen

Mehr Threads und hohe Stufen können RAM und Zeit kosten. Große Fenster können den späteren Decoderbedarf erhöhen. Eine erfolgreich erzeugte Datei ist nicht automatisch auf einem kleineren Empfängergerät brauchbar.

### Wörterbuch gehört zur Sicherung

Ein fehlendes oder unpassendes Wörterbuch kann die spätere Dekompression verhindern. Die Wörterbuchdatei und ihre Zuordnung dokumentieren. Das Paket allein kann für eine vollständige Wiederherstellung unzureichend sein.

### Prüfwerte und Formatunterstützung

Inhaltsprüfwerte erkennen bestimmte Fehler und authentifizieren keinen Urheber. Dateien ohne Inhaltsprüfwert können trotzdem formal verarbeitet werden. `--no-check` nicht zur vermeintlichen Fehlerbehebung verwenden. Unterstützung anderer Formate ist buildabhängig und kein universeller Archivimport.

### Laufende Dateien und Metadaten

Das Werkzeug speichert einen Datenstrom und ersetzt keinen konsistenten Datenbanksnapshot oder eine vollständige Linux-Systemkopie. Besondere Eigentümer, ACLs und Linkstrukturen gesondert planen.

**Root-Rechte sind für die gezeigte Übung unnötig.** Das Lesen fremder Bestände wird nicht allein durch den Dokumentationsauftrag freigegeben.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel existiert | Frühere Ausgabe oder Originalname belegt. | Freien Zielpfad wählen. |
| Wörterbuch verlangt | Eingabe wurde mit zusätzlichem Wörterbuch erzeugt. | Passendes Original bereitstellen. |
| Speicherbedarf zu hoch | Fenster oder Decoderlimit passt nicht. | Bedarf und Zielumgebung bewusst prüfen. |
| Datei kaum kleiner | Kleine oder bereits komprimierte Daten. | Nutzen anhand realer Daten beurteilen. |
| Ordnerstruktur fehlt | Kompression mit Archivierung verwechselt. | Geeignetes Archivverfahren ergänzen. |
| Daten erscheinen trotz falschem Format | Force-/Pass-through-Modus aktiv. | Normalen Test ohne Aufweichung verwenden. |

Fehlermeldungen und Abschlussstatus prüfen; eine vorhandene Ausgabedatei kann unvollständig sein.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit Standardstufe und eigenen kleinen Daten anfangen.
2. Eingaben bis zur geprüften Wiederherstellung behalten.
3. Neue Ausgabepfade statt `-f` verwenden.
4. Inhaltsprüfung und Rückgewinnung getrennt durchführen.
5. Bekannte Inhalte byteweise vergleichen.
6. Erst bei konkretem Bedarf Wörterbuch-, Thread- oder Langstreckenparameter ergänzen.

**Prüfstand:** Mit Zstandard CLI 1.5.5 wurden Standardkompression einer eigenen Datei, Liste, Test und stdout-Dekompression geprüft. Die Quelle blieb standardmäßig erhalten und die wiedergewonnenen Bytes entsprachen dem Original. Keine praktischen Tests für Wörterbücher, hohe Stufen, Threads, große Fenster oder vollständige Sicherungsabläufe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `unzstd` | Dekompressionsalias. |
| `zstdcat` | stdout-Alias mit Force-Verhalten. |
| `tar` | Bündelt eine Dateisammlung. |
| `xz`, `gzip`, `lz4` | Andere Kompressionswerkzeuge mit eigenen Voreinstellungen. |
| `cmp` | Kontrolliert bekannte wiederhergestellte Dateien. |

Ausgangseintrag: Datensatz 28 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
