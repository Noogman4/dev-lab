---
id: "xzcat"
name: "xzcat"
command: "xzcat"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive & kompression", "xzcat"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 21
reviewed_at: "2026-11-13"
locally_checked_version: "XZ Utils 5.4.5"
---

# xzcat – XZ-Inhalte auf stdout ausgeben

## 1. Kurzbeschreibung

`xzcat` dekomprimiert unterstützte Eingaben und schreibt die entpackten Bytes auf die Standardausgabe, kurz stdout. Bei XZ Utils entspricht der Name `xz --decompress --stdout`.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Der normale Aufruf erhält die Eingabedatei und legt selbst keine namensabhängige entpackte Datei an. Umleitungen und Folgeprogramme können trotzdem Daten schreiben oder verändern.

## 2. Was macht der Befehl?

Die Kompressionsschicht wird entfernt, während der Inhalt als Datenstrom weitergegeben wird. Bei einer Textdatei kann das eine direkte Anzeige sein. Bei einer `.tar.xz` entsteht auf stdout dagegen TAR-Inhalt und keine normale Ordneransicht.

Mehrere Eingaben werden nacheinander ausgegeben. Es gibt dabei keine automatisch eingefügten Trenner oder neuen Dateinamen. Für eine einzelne gewünschte Ausgabe deshalb nicht wahllos mehrere Quellen wählen.

Grundlage: [offizielle XZ-Referenz 5.4.5](https://raw.githubusercontent.com/tukaani-project/xz/v5.4.5/src/xz/xz.1) und die lokale XZ-Utils-Hilfe. Der Alias enthält kein `-f`: Fremddaten werden nicht allein wegen des Namens automatisch unverändert durchgereicht.

## 3. Syntax

```text
xzcat [OPTIONEN] [DATEI ...]
xz -dc [OPTIONEN] [DATEI ...]
```

```bash
xzcat "notiz.txt.xz"
xzcat "notiz.txt.xz" > "ausgabe.txt"
```

Die zweite Zeile ist eine Schreiboperation der Shell. Ohne Dateinamen beziehungsweise mit `-` wird stdin gelesen. `--format=xz` kann die akzeptierte Eingabe ausdrücklich auf XZ beschränken.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `--format=xz` | Nur XZ als Eingabeformat. | Sonst ist unterstützte automatische Erkennung möglich. |
| `-M LIMIT` | Dekompressionsspeicher begrenzen. | Keine Ausgabegrößen- oder Laufzeitquote. |
| `-v` | Zusätzliche Angaben auf stderr. | Von den Nutzdaten auf stdout unterscheiden. |
| `-f` | Schutzprüfungen übergehen. | Kann bei stdout unbekannte Inhalte unverändert durchreichen. |
| `--single-stream` | Nach erstem Datenstrom aufhören. | Weitere Inhalte können unbemerkt fehlen. |
| `--ignore-check` | Inhaltsprüfung übergehen. | Für normale Verarbeitung vermeiden. |
| `--` | Ende der Optionen. | Bei führendem Bindestrich im Namen hilfreich. |

Für eine reine Datenprüfung besser den ausdrücklichen Hauptaufruf `xz -t` verwenden. Das macht die Absicht klarer als eine ungenutzte Terminalausgabe.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Übungsort vorbereiten

```bash
xzcat --version
uebung="$(mktemp -d -t netmon-xzcat-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Bekannten Text komprimieren

```bash
printf '%s\n' 'Eigene Ausgabe-Testnotiz.' > "notiz.txt"
xz -k "notiz.txt"
```

Das Original bleibt durch `-k` erhalten. Die neue `.xz`-Datei ist die eigene Testeingabe.

### Schritt 3: Inhalt ansehen

```bash
xzcat "notiz.txt.xz"
```

Erwartet wird die eigene Textzeile. Die komprimierte Datei bleibt bestehen. Diesen direkten Terminalaufruf nur für bekannten geeigneten Text verwenden.

### Schritt 4: Kontrollierte Ausgabe vergleichen

```bash
xzcat "notiz.txt.xz" > "ausgabe.txt"
cmp "notiz.txt" "ausgabe.txt"
```

`ausgabe.txt` muss ein freier, bewusst gewählter Name sein. `cmp` bestätigt für die bekannte Eingabe die byteweise Übereinstimmung. Es prüft keine unbekannte Herkunft.

## 6. Typische Anwendungsfälle

**Komprimierte Texte lesen:** Für kurze eigene Dateien genügt stdout; größere Texte besser mit einem geeigneten Pager ansehen.

**Daten weiterreichen:** Ein Analysewerkzeug kann den entpackten Strom lesen. Seine Eingabeerwartung, Laufzeit und Nebenwirkungen gehören zum Gesamtaufruf.

**Ein Ergebnis ohne Ableitung des Namens schreiben:** Eine kontrollierte Umleitung legt den gewünschten Zielnamen fest. Das ursprüngliche Archiv bleibt erhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

### stdout schützt keine Umleitungsziele

Bei `> ziel` öffnet die Shell die Datei vor dem Start des Werkzeugs. Bereits vorhandene Daten können auch dann verloren gehen, wenn die Dekompression später scheitert. Nie denselben Pfad für Ein- und Ausgabe verwenden.

### Teilinhalte sind noch kein Erfolg

Vor einem späteren Datenfehler können bereits Bytes ausgegeben worden sein. Meldungen und Abschlussstatus deshalb mitprüfen. Bei einer Pipeline kann ein erfolgreicher letzter Prozess den Fehler eines früheren verdecken; in eigenen Bash-Skripten passende Pipeline-Fehlerbehandlung planen.

### Grenzen der Inhaltsprüfung

Vorhandene unterstützte XZ-Prüfwerte werden normalerweise geprüft. Sie sind keine Signatur und garantieren keine Harmlosigkeit. `-f` kann die Ausgabe fremder Daten ermöglichen; `--ignore-check` schwächt die Prüfung.

### Große oder binäre Inhalte

Eine kleine Eingabe kann sehr große Ausgaben erzeugen. RAM-Limit und Ausgabemenge sind verschiedene Grenzen. Binäre beziehungsweise steuerzeichenhaltige Inhalte nicht unbedacht ins Terminal ausgeben.

**Root-Rechte werden für dieses Lesen eigener Dateien nicht benötigt.** Eine nachgeschaltete Anwendung kann trotzdem eigene Rechteanforderungen besitzen.

## 8. Häufige Fehler

| Beobachtung | Erklärung | Vorgehen |
| --- | --- | --- |
| Format nicht erkannt | Falsche oder beschädigte Eingabe. | Format und Herkunft prüfen. |
| Speicherlimit überschritten | Decoder benötigt mehr RAM. | Bedarf und Limit bewusst beurteilen. |
| Unlesbare Zeichen | Binärer Inhalt auf stdout. | Passendes Datei- oder Analyseziel verwenden. |
| Mehrere Texte kleben zusammen | Mehrere Eingaben ohne Trenner. | Einzeln verarbeiten oder Trennung selbst planen. |
| Datei enthält trotz Fehler Daten | Teilinhalt wurde vor Abbruch geschrieben. | Abschlussstatus prüfen und Ergebnis nicht als vollständig behandeln. |

XZ Utils unterscheidet Erfolg `0`, Fehler `1` und Warnung `2`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit einer eigenen kurzen Textdatei beginnen.
2. Vorhandene Ausgabepfade nicht überschreiben.
3. Für Formatprüfung `xz -t` statt Force-Durchreichen verwenden.
4. Eingaben erhalten und bekannte Inhalte vergleichen.
5. Fehler in Pipelines ausdrücklich berücksichtigen.

**Prüfstand:** Mit XZ Utils 5.4.5 wurden eine und zwei eigene komprimierte Eingaben verarbeitet. stdout war bytegleich mit einem beziehungsweise zwei Originalinhalten; die komprimierten Quellen blieben unverändert. Eine unkomprimierte Texteingabe wurde ohne `-f` abgelehnt. Keine praktischen Tests mit beschädigten Daten, Speichergrenzen oder Fremdformaten.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xz -dc` | Expliziter Hauptaufruf derselben Aufgabe. |
| `unxz` | Dekompression normalerweise in eine abgeleitete Datei. |
| `lzcat` | Legacy-LZMA-Formatwahl auf stdout. |
| `zcat`, `zstdcat` | Andere Formatfamilien und teilweise andere Force-Vorgaben. |
| `cmp` | Vergleich bekannter Inhalte. |

Ausgangseintrag: Datensatz 21 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
