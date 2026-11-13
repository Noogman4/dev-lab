---
id: "zdiff"
name: "zdiff"
command: "zdiff"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive & kompression", "zdiff"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 23
reviewed_at: "2026-11-13"
locally_checked_version: "zdiff aus GNU gzip 1.12; GNU diff"
---

# zdiff – Inhalte komprimierter Textdateien vergleichen

## 1. Kurzbeschreibung

`zdiff` vergleicht Dateiinhalte mithilfe von `diff` und dekomprimiert unterstützte komprimierte Eingaben bei Bedarf. Es zeigt damit Unterschiede der entpackten Texte, nicht bloß Unterschiede zwischen komprimierten Bytes.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Die Eingaben werden nicht aktualisiert oder durch entpackte Fassungen ersetzt. Die Implementierung kann intern temporäre Daten verwenden; eine Ausgabeumleitung schreibt außerdem ein eigenes Ziel.

## 2. Was macht der Befehl?

Zwei gzip-Dateien können sich auf Byteebene unterscheiden, obwohl der entpackte Inhalt gleich ist, etwa wegen anderer Header oder Kompressionseinstellungen. Für den Textvergleich entfernt `zdiff` zuerst die unterstützte Kompressionsschicht und übergibt die Inhalte an `diff`.

Die Vergleichsoptionen stammen deshalb im Wesentlichen von `diff`. Eine leere Ausgabe kann bedeuten, dass unter den gewählten Regeln kein Unterschied vorliegt. Der Abschlussstatus unterscheidet Gleichheit, Unterschiede und technische Fehler.

Grundlagen: [Distributions-Manpage zu zdiff](https://manpages.debian.org/trixie/gzip/zdiff.1.en.html), die lokale `zdiff --help`, das lokal installierte Wrapper-Skript aus GNU gzip 1.12 und `diff --help`. Die Beispiele verwenden bewusst zwei ausdrückliche Dateinamen.

## 3. Syntax

```text
zdiff [DIFF_OPTIONEN] DATEI1 DATEI2
```

```bash
zdiff "alt.txt.gz" "neu.txt.gz"
zdiff -u "alt.txt.gz" "neu.txt.gz"
```

Eingaben können je nach unterstützter Erkennung komprimiert oder unkomprimiert sein. Für einen verlässlichen Einstieg eindeutige gzip-Dateinamen verwenden. ZIP-Dateisammlungen werden nicht automatisch Mitglied für Mitglied verglichen.

**Prüfpunkt bei der Ein-Datei-Kurzform:** Die lokale Hilfe und die Umsetzung der Namensableitung sind nicht ohne Weiteres austauschbar mit jeder Manpage-Fassung. Für reproduzierbare Anleitungen beide Vergleichsdateien ausdrücklich angeben, statt eine abgeleitete Nachbardatei vorauszusetzen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-u` | Unterschiede im Unified-Format. | Mit Kontext, gut für nachvollziehbare Textänderungen. |
| `-q` | Nur melden, dass Unterschiede vorliegen. | Zeigt nicht deren Einzelheiten. |
| `-s` | Auch gleiche Dateien ausdrücklich melden. | Hilfreich für einen sichtbaren Kontrolllauf. |
| `-i` | Groß-/Kleinschreibung beim Vergleich ignorieren. | Unterschiedliche Bytes können dadurch als gleich gelten. |
| `-b` | Änderungen der Menge an Leerraum ignorieren. | Kann bei bedeutungsvollem Leerraum relevante Änderungen ausblenden. |
| `-w` | Leerraumunterschiede vollständig ignorieren. | Nicht für bytegenaue Integritätsprüfung geeignet. |
| `--help` | Wrapper-Hilfe anzeigen. | Für die eigentlichen Vergleichsregeln zusätzlich `diff --help` lesen. |
| `--version` | Versionsangaben anzeigen. | Wrapper und aufgerufenes Vergleichswerkzeug unterscheiden. |
| `--` | Ende der Optionen. | Hilfreich vor ungewöhnlichen Dateinamen. |

`diff` besitzt auch Verzeichnisfunktionen. Daraus folgt nicht, dass `zdiff` beliebige komprimierte Verzeichnisbäume rekursiv als Archive vergleicht. Für solche Aufgaben vorher die gewünschte Datenebene festlegen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen eigenen Arbeitsordner wählen

```bash
zdiff --version
uebung="$(mktemp -d -t netmon-zdiff-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Zwei kleine Texte vorbereiten

```bash
printf '%s\n' 'Name: Test' 'Wert: 1' > "alt.txt"
printf '%s\n' 'Name: Test' 'Wert: 2' > "neu.txt"
gzip -k "alt.txt" "neu.txt"
```

Die Texte unterscheiden sich absichtlich nur in der zweiten Zeile. `-k` erhält beim Komprimieren die Originale.

### Schritt 3: Unterschiede zeigen

```bash
zdiff -u "alt.txt.gz" "neu.txt.gz"
```

Im Unified-Text bezeichnet `-` die alte und `+` die neue Fassung einer geänderten Zeile. Die Kopfzeilen können interne Stream- beziehungsweise Hilfsnamen statt der ursprünglichen Eingaben zeigen. Sie nicht als tatsächlich umzubenennende Dateien interpretieren.

### Schritt 4: Abschlussstatus beurteilen

```bash
printf 'Abschlussstatus: %s\n' "$?"
```

Unmittelbar nach `zdiff` ausführen, damit keine andere Anweisung den Status ersetzt. Bei dieser absichtlichen Änderung wird `1` erwartet: Das bezeichnet einen gefundenen Unterschied, keinen technischen Ausführungsfehler.

### Schritt 5: Gleichen Inhalt vergleichen

```bash
zdiff -s "alt.txt.gz" "alt.txt.gz"
```

Hier wird Gleichheit erwartet. Für die wichtige Wiederherstellung einer Datei kann zusätzlich ein direkter Bytevergleich der bekannten entpackten Inhalte sinnvoll sein.

## 6. Typische Anwendungsfälle

**Komprimierte Textstände vergleichen:** Etwa zwei eigene gespeicherte Konfigurationsauszüge, ohne dauerhaft entpackte Kopien im Projekt abzulegen.

**Unterschiedliche Kompression von geändertem Inhalt trennen:** Der Vergleich konzentriert sich auf den entpackten Text. Identische Inhalte müssen nicht identische gzip-Dateien ergeben.

**Änderungsbericht erzeugen:** `-u` gibt eine menschenlesbare Darstellung aus. Eine Umleitung in eine freie Berichtsdatei kann sie speichern; vertrauliche Textstellen werden dadurch mitkopiert.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Ignorierregeln können wichtige Änderungen verbergen

`-i`, `-b` und `-w` verändern den Gleichheitsbegriff. In Passwörtern, Quelltexten, Tabellen oder Einrückungsformaten können genau diese Unterschiede entscheidend sein. Für den ersten Vergleich keine Ignorieroptionen setzen.

### Ausgabe kann vertrauliche Inhalte zeigen

Ein Diff gibt Teile beider Texte wieder. Vor dem Teilen eines Berichts Zugangsdaten und private Werte prüfen. Der lokale Vergleich sendet den Bericht nicht selbst an einen externen Dienst.

### Dekompression und temporäre Daten

Große beziehungsweise stark komprimierte Eingaben können RAM, Laufzeit und je nach Implementierungsweg temporären Plattenplatz benötigen. Ein lesender Vergleich ist deshalb keine Ressourcenisolation.

### Textvergleich ist keine Archiv- oder Herkunftsprüfung

Ein gültiges Vergleichsergebnis authentifiziert keinen Absender und garantiert keine vollständige Metadatenübereinstimmung. Binärinhalte können lediglich als unterschiedlich gemeldet werden. Die Ausgabe nicht ungeprüft als anwendbaren Patch für ursprüngliche Dateinamen verwenden.

**Root-Rechte werden für die gezeigten eigenen Eingaben nicht benötigt.** Umleitungen besitzen ihre eigenen Schreibrechte und Überschreibwirkungen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Status `1` trotz funktionierendem Aufruf | Inhalte unterscheiden sich. | Als Vergleichsergebnis behandeln. |
| Status `2` | Lese-, Dekompressions- oder Vergleichsfehler. | Genaue Meldung prüfen. |
| Keine Unterschiede trotz anderer Bytes | Ignorierregeln aktiv oder nur komprimierte Header verschieden. | Vergleichsebene und Optionen prüfen. |
| Ungewohnte Namen im Bericht | Interne Datenströme statt Originalpfade. | Inhalt und explizite Eingaben zuordnen. |
| Binärdateien unterscheiden sich | Kein sinnvoller zeilenweiser Textvergleich. | Geeignetes Byte- oder Fachformatwerkzeug verwenden. |

Die Statuswerte sind `0` für Gleichheit, `1` für Unterschiede und `2` für Probleme. Nicht jede von null abweichende Rückgabe bedeutet hier dieselbe Art von Fehler.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zwei Dateinamen ausdrücklich angeben.
2. Mit eigenen kurzen Texten und `-u` beginnen.
3. Keine Ignorieroptionen vor der ersten Sichtprüfung verwenden.
4. Status `1` und technische Fehler unterscheiden.
5. Berichte vor dem Weitergeben auf vertrauliche Inhalte prüfen.

**Prüfstand:** GNU-gzip-Wrapper 1.12 wurde mit selbst erzeugten gzip-Dateien geprüft. Gleiche Inhalte lieferten `0`, absichtlich unterschiedliche Texte mit `-u` lieferten `1`, eine fehlende Eingabe `2`. Die vorhandenen Quellen blieben bytegleich. Keine praktischen Tests mit der Ein-Datei-Kurzform, Binärdaten, großen Dateien oder alternativen Vergleichsprogrammen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `diff` | Zeilenweiser Vergleich ohne automatische gzip-Vorbereitung. |
| `zcmp` | Bytevergleich unterstützter komprimierter Eingaben. |
| `cmp` | Direkter Bytevergleich. |
| `zcat` | Gibt entpackte Inhalte auf stdout aus. |
| `gzip -t` | Prüft Kompressionsdaten statt zweier Textstände. |

Ausgangseintrag: Datensatz 23 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
