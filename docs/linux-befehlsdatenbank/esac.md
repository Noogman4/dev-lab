---
id: "esac"
name: "esac"
command: "esac"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "esac"]
status: "Lokale case-Hilfe und abgeschlossene Musterauswahl praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 82
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# esac – Eine case-Auswahl korrekt abschließen

## 1. Kurzbeschreibung

`esac` ist das Shell-Schlüsselwort, das eine `case`-Auswahl beendet. Der Name ist `case` rückwärts geschrieben. **Root-Rechte sind nicht nötig.** Es ist kein eigenständiges Programm mit allgemeinen Optionen.

Der Abschluss ist besonders wichtig, wenn hinter einer Auswahl weitere Befehle folgen. Er markiert die Grenze zwischen den einzelnen Auswahlzweigen und dem anschließenden gemeinsamen Ablauf.

## 2. Was macht der Befehl?

Bash verarbeitet einen Wert anhand der Muster einer `case`-Konstruktion. Die normalen Zweige enden mit `;;`. `esac` beendet dagegen die **gesamte** Konstruktion. Beides sind unterschiedliche Syntaxelemente und nicht austauschbar.

Der Abschluss selbst prüft kein Muster und führt keine Rücknahme vorheriger Aktionen durch. Primärquelle ist die lokal gelesene Hilfe `help case` aus Bash 5.2.21. Weiterführend: [Bash-Bedingungskonstrukte](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html); der Onlineabruf war hier nicht verfügbar. Das vollständige Beispiel wurde separat ausgeführt.

## 3. Syntax

```text
case "$wert" in
  MUSTER1) BEFEHLE ;;
  MUSTER2) BEFEHLE ;;
esac
```

Jedes offene `case` benötigt einen eigenen passenden Abschluss. Bei Verschachtelung muss `esac` dem richtigen Beginn zugeordnet sein. Ein `done` schließt eine Schleife, ein `fi` eine if-Auswahl; keines ersetzt diesen Abschluss.

## 4. Wichtige Optionen

`esac` hat keine Optionen. Es wird nur innerhalb der Shellgrammatik verwendet.

| Baustein | Bedeutung | Häufige Verwechslung |
| --- | --- | --- |
| `case` | Gesamte Musterauswahl beginnen. | Noch kein einzelner Zweig. |
| `MUSTER)` | Passenden Zweig kennzeichnen. | Die Klammer gehört zum Musterrahmen. |
| `;;` | Gewöhnlichen Zweig abschließen. | Beendet nach Treffer dessen Auswahllauf. |
| `esac` | Gesamte Konstruktion schließen. | Kein allgemeiner Erfolgsbefehl. |
| Befehl danach | Gemeinsamer weiterer Ablauf. | Liegt außerhalb der Auswahl. |

Einrückung hilft beim Lesen, ist aber nicht der syntaktische Abschluss. Auch ein sehr kurzer case-Block braucht seine korrekte Struktur.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen eigenen Textnamen auswerten

```bash
dateiname=probe.png
case "$dateiname" in
  *.png) printf 'PNG-Name\n' ;;
  *) printf 'Anderer Name\n' ;;
esac
printf 'Auswahl beendet\n'
```

`probe.png` ist nur ein Textwert. Keine Datei dieses Namens muss existieren, und es wird auch keine Datei geöffnet. Die Endung wird als Muster verglichen, nicht der wirkliche Dateityp untersucht.

### Schritt 2: Zweig und Gesamtablauf unterscheiden

Der Text endet auf `.png` und erreicht daher den ersten Zweig. `;;` verhindert das normale Weiterlaufen in den Sternzweig. `esac` schließt den gesamten Rahmen. Erst dahinter steht die gemeinsame Abschlussausgabe.

### Schritt 3: Ausgabe vergleichen

```text
PNG-Name
Auswahl beendet
```

Ein anderer Name würde den Standardzweig auswählen; die Ausgabe hinter `esac` könnte trotzdem folgen. Ob eine Fehlersituation den gesamten Ablauf beenden soll, muss der Zweiginhalt ausdrücklich bestimmen. Das Schlüsselwort übernimmt diese fachliche Entscheidung nicht.

## 6. Typische Anwendungsfälle

### Gemeinsam nach mehreren Alternativen weitermachen

Ein Skript verarbeitet unterschiedliche Eingabewerte in getrennten Zweigen. Danach kann ein gemeinsamer nächster Schritt hinter `esac` folgen, ohne denselben Code in jeden Zweig zu kopieren.

### Komplexe Skripte lesen

Zusammengehörige case-/esac-Paare markieren die Auswahlgrenzen. Das ist insbesondere bei Auswahl innerhalb einer Schleife hilfreich: Erst `esac` schließt die Auswahl, später `done` die Schleife.

### Syntaxfehler eingrenzen

Ein fehlender Abschluss wird unter Umständen erst am Dateiende gemeldet. Von dort rückwärts offene Konstruktionen prüfen, statt nur die letzte sichtbare Zeile zu verändern.

## 7. Risiken, Nebenwirkungen und Vorsicht

`esac` selbst verändert keine Daten. Eine falsch platzierte Grenze kann aber nachfolgende Befehle dem falschen Bereich zuordnen oder den gesamten Skriptstart verhindern. Die konkrete Gefahr ergibt sich aus den dann ausgeführten Zweigen und Folgeaktionen.

Ein gültiger Abschluss sagt nichts darüber, ob die Auswahl fachlich richtig ist. Eine Dateiendung ist kein Vertrauensbeweis für einen Dateiinhalt. Ein Sternzweig kann unerwartete Eingaben auffangen, muss sie aber auch passend behandeln. Shellcode niemals aus unbekanntem Eingabetext erzeugen, nur weil dessen Name zu einem Muster passt.

## 8. Häufige Fehler

- **`esac --help` eingegeben:** Es gibt keinen solchen externen Hilfsaufruf.
- **Nur `;;` verwendet:** Der gesamte case-Rahmen bleibt offen.
- **`done` oder `fi` eingesetzt:** Falsche Art von Abschluss.
- **Zusätzliches esac:** Kein passender offener Beginn vorhanden.
- **Erfolg nach unbekanntem Fall angenommen:** Der gewählte Zweig muss seinen Status bewusst bestimmen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Kurze mehrzeilige Auswahlen schreiben und den Abschluss auf Höhe des Beginns einrücken. Zunächst nur feste Texte vergleichen. Ein Syntaxcheck einer eigenen Skriptdatei kann fehlende Abschlüsse finden; der richtige Umgang mit Eingaben und Nebenwirkungen benötigt zusätzlich inhaltliche Prüfung.

**Prüfstand:** Lokale Bash-5.2.21-case-Hilfe gelesen. Das vollständige Beispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; die beiden erwarteten Zeilen, Status 0. Keine Datei mit dem Beispielnamen gelesen oder geschrieben. Verschachtelte Auswahlen und andere Shells nicht praktisch geprüft.

## 10. Verwandte Befehle

- `case`: Beginn der zugehörigen Musterauswahl.
- `if`, `fi`: andere bedingte Auswahl mit eigenem Abschluss.
- `do`, `done`: Rahmen eines Schleifenkörpers.
- `bash -n`: Syntaxprüfung einer eigenen Bash-Skriptdatei.

Ausgangseintrag: Datensatz 82 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
