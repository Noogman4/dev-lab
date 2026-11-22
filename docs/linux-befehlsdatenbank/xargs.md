---
id: "xargs"
name: "xargs"
command: "xargs"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["shell", "argumente", "pipeline", "dateinamen"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 208
reviewed_at: "2026-11-13"
locally_checked_version: "xargs (GNU findutils) 4.9.0"
---

# xargs – Eingaben als Argumente weiterreichen und Befehle ausführen

## 1. Kurzbeschreibung

`xargs` liest Eingabeelemente, bildet daraus Argumentlisten und startet einen Zielbefehl. Es zeigt einen Aufruf nicht nur an, sondern führt ihn aus. **Für die hier verwendete Ausgabe eigener Testwerte ist kein Root nötig.** Das Risiko hängt vom Zielprogramm ab; eine schreibende oder löschende Pipeline kann entsprechend gefährlich sein.

## 2. Was macht der Befehl?

Zuerst stehen der Programmname und feste Argumente; anschließend hängt `xargs` die eingelesenen Elemente an. Je nach Anzahl und Größenlimits werden ein oder mehrere Aufrufe gebildet. Ohne Zielprogramm verwendet GNU `xargs` `echo`; für klare Beispiele wird das Ziel hier immer angegeben.

Die Standardeingabe wird normalerweise an Leerraum aufgeteilt. Anführungszeichen und Rückstriche haben dabei eigene Bedeutung. Shell-Zitierung beim Erzeugen einer Ausgabe bleibt nicht automatisch als Dateinamensgrenze im ausgegebenen Text erhalten.

Mit `-0` trennt dagegen ein NUL-Byte die Elemente. Leerzeichen, Zeilenumbrüche, Anführungszeichen und Rückstriche innerhalb eines Elements bleiben Daten. Ein passender Erzeuger ist `find -print0`. Nulltrennung schützt Argumentgrenzen, aber weder vor einem falsch gewählten Zielprogramm noch vor Änderungen der Dateien zwischen Suche und Verwendung.

Quelle: [GNU-xargs-Manpage bei Debian](https://manpages.debian.org/trixie/findutils/xargs.1.en.html), zusätzlich lokale Manpage zu findutils 4.9.0 gelesen. Die Aussage des ursprünglichen Entwurfs zu leerer Eingabe war falsch: **GNU xargs startet ohne `-r` auch bei vollständig leerer Eingabe einmal. Erst `-r` unterdrückt diesen Aufruf.**

## 3. Syntax

```text
ERZEUGER | xargs [XARGS_OPTIONEN] PROGRAMM [FESTE_ARGUMENTE ...]
```

Die von der Eingabe kommenden Elemente folgen den festen Argumenten. Das Zielprogramm läuft direkt; `xargs` ist nicht selbst ein allgemeiner Shell-Interpreter. Ein ausdrücklich als Ziel gestartetes `sh -c` würde eine zusätzliche Shell-Auswertung einführen und erfordert gesonderte Sorgfalt. Eingabetext nicht in Shellcode einsetzen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `-0`, `--null` | NUL-getrennte Elemente lesen. | Der Erzeuger muss dasselbe Trennformat liefern. |
| `-r`, `--no-run-if-empty` | Bei fehlenden Elementen keinen Zielaufruf starten. | Kein GNU-Standardverhalten ohne diese Option. |
| `-n N` | Höchstens N Eingabeargumente je Aufruf. | Weitere Größenlimits können kleinere Gruppen erzwingen. |
| `-I ZEICHEN` | Platzhalter in festen Argumenten ersetzen. | Ändert auch Eingabeverarbeitung; nicht unbedacht mit `-n` oder `-L` kombinieren. |
| `-P N` | Bis zu N Prozesse gleichzeitig. | Standard 1; 0 bedeutet möglichst viele, keine sichere Lastbegrenzung. |
| `-t` | Geplanten Aufruf auf Standardfehler ausgeben. | Er wird anschließend trotzdem ausgeführt. |
| `-p` | Vor jedem Aufruf am Terminal fragen. | Kein allgemeiner Trockenlauf. |
| `-a DATEI` | Elemente aus Datei statt Standardeingabe lesen. | Kann für den Zielbefehl dessen Standardeingabe verfügbar halten. |
| `-s N` | Obergrenze der Befehlszeilenlänge setzen. | Zu kleine Grenzen können Fehler verursachen. |

`-n`, `-L` und `-I` beeinflussen die Aufteilung und stehen grundsätzlich miteinander in Konflikt; GNU dokumentiert eine besondere Ausnahme für `-n 1` nach `-I`. Für Einsteiger pro Aufgabe ein verständliches Aufteilungsmodell wählen.

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GNU findutils und coreutils. Nur `printf` wird als Zielprogramm gestartet; keine Dateien werden durch `xargs` verändert. Alle Schritte in derselben Shell durchführen.

### Schritt 1: Eigenen Bereich vorbereiten

```bash
set -o pipefail
uebung="$(mktemp -d -t netmon-xargs-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir dateien || exit 1
printf '%s\n' 'A' > 'dateien/eins zwei.txt' || exit 1
printf '%s\n' 'B' > dateien/drei.txt || exit 1
```

`pipefail` lässt später auch einen Fehler im linken Teil einer Pipeline deren Status beeinflussen. Der Ordner enthält genau zwei eigene Dateien und bleibt zur Kontrolle bestehen.

### Schritt 2: Zwei NUL-getrennte Werte unverändert ausgeben

```bash
printf '%s\0' 'eins zwei' 'drei' | xargs -0 -r -n 1 printf '[%s]\n'
```

Erwartete Ausgabe:

```text
[eins zwei]
[drei]
```

`printf` links liefert zwei Elemente. `-0` bewahrt das Leerzeichen in `eins zwei`, `-n 1` startet für jedes Element einen Aufruf. Der rechte Formattext bleibt ein festes Argument; Eingabedaten werden über `%s` eingesetzt und nicht als Formattext oder Shellcode verwendet.

### Schritt 3: Vollständig leere Eingabe vergleichen

```bash
printf '%s' '' | xargs printf 'AUFRUF\n'
printf '%s' '' | xargs -r printf 'AUFRUF\n'
```

Der erste Aufruf gibt genau einmal `AUFRUF` aus. Der zweite gibt nichts aus, weil GNU `-r` den Zielaufruf bei leerer Eingabe verhindert. Links werden tatsächlich null Bytes geliefert; ein ausgegebenes NUL-Byte wäre ein anderes Eingabeobjekt.

### Schritt 4: Eigene Dateinamen aus find weiterreichen

```bash
find "$uebung/dateien" -type f -print0 | xargs -0 -r -n 1 printf 'Datei: <%s>\n'
```

Es erscheinen zwei vollständige absolute Pfade, darunter einer mit `eins zwei.txt` als zusammengehörigem Namen. Die Reihenfolge von `find` ist nicht garantiert. Die Ausgabe dient nur der Sichtkontrolle; eine zeilenbasierte Anzeige ist selbst kein verlustfreies Austauschformat für Namen mit Zeilenumbrüchen.

## 6. Typische Anwendungsfälle

**Viele Elemente bündeln:** Argumentlisten in passende Gruppen aufteilen, damit Betriebssystemlimits nicht durch einen einzigen riesigen Aufruf überschritten werden.

**Dateien aus einer Suche verarbeiten:** Erzeuger und Empfänger konsequent auf NUL-Trennung einstellen. Wenn ein Zielprogramm Dateinamen als Optionen verstehen könnte, dessen eigenes `--` an der passenden Stelle verwenden; das ist getrennt von xargs-Optionen zu betrachten.

**Unabhängige Aufgaben parallelisieren:** `-P` nur mit verstandenen Ressourcen- und Reihenfolgefolgen einsetzen. Diese Dokumentation führt keine Paralleltests aus.

## 7. Risiken, Nebenwirkungen und Vorsicht

`-t` ist keine Simulation. Ein Zielprogramm kann bereits beim ersten Aufruf viele Daten verändern. Auch `-0 -r` schützt nicht vor einem falschen Pfad oder einer falschen Aktion. Daten mit führendem Bindestrich können beim Zielprogramm Optionen auslösen.

Zwischen Erzeugen einer Dateiliste und Verwenden ihrer Namen liegt Zeit. Andere Prozesse können den Bestand austauschen. Eine korrekte Nulltrennung beseitigt diese Rennen nicht. Bei gemeinsam beschreibbaren Bäumen und privilegierten Aktionen sind gesonderte Verfahren nötig.

`-P` kann Ausgaben mischen und Zugriffskonflikte verursachen. In der lokal verwendeten Version 4.9.0 dokumentiert die neuere Manpage zudem ein Problem beim parallelen Abbruch nach Kindstatus 255; daraus wird keine Zusage über das Aufräumen aller Kinder abgeleitet.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Dateiname zerfällt | Ungeeignete Leerraumtrennung. | Passendes `-print0` und `-0` kombinieren. |
| Ziel startet ohne Eingaben | GNU-Standard ohne `-r`. | `-r` bewusst setzen. |
| Optionenkonflikt bei Aufteilung | `-I`, `-L` und `-n` gemischt. | Ein geeignetes Modell wählen. |
| Ziel wartet auf Eingabe | xargs nutzt gewöhnlich dessen Standardeingabe nicht als interaktiven Datenkanal. | Zielanforderungen verstehen; nicht beliebig interaktive Programme einsetzen. |
| Status ist nicht der direkte Kindstatus | xargs fasst Ergebnisse zusammen. | Rückgabewerte separat auswerten. |

GNU `xargs` liefert unter anderem 0 bei Erfolg, 123 bei einem Kindstatus 1–125, 124 bei Kindstatus 255, 126 bei nicht ausführbarem und 127 bei nicht gefundenem Ziel. Das sind unterschiedliche Fehlerursachen, kein Nachweis vollständiger Verarbeitung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Erst mit festem `printf`-Format und wenigen bekannten Werten üben. Keine unkontrollierten Eingaben zu Shellcode machen. `find -exec PROGRAMM ... {} +` kann eine einfachere Alternative sein; auch dort müssen Optionen, Rechte und parallele Bestandsänderungen bedacht werden.

**Prüfstand am 2026-11-13:** GNU `xargs` 4.9.0; lokale und verlinkte Manpage gelesen. Abschnitt 5 vollständig ausgeführt. Zusatzprüfungen bestätigten Byte für Byte Argumente mit Leerzeichen, Zeilenumbruch, Anführungszeichen, Rückstrich und führendem Bindestrich sowie leere Eingabe mit/ohne `-r`. Nur harmlose Ausgabeprogramme wurden gestartet.

**Nicht praktisch geprüft:** `-P`, `-I`, `-p`, Größenlimits, Fehlercodes aus fehlgeschlagenen Zielprogrammen sowie schreibende oder privilegierte Pipelines.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find -print0` | Dateinamen NUL-getrennt erzeugen. |
| `find -exec` | Gefundene Pfade direkt an einen Zielbefehl übergeben. |
| `printf` | Vorhersagbare Testdaten und Ausgabeformate erzeugen. |
| `sh` | Zusätzliche Shellauswertung nur bei bewusstem Bedarf. |

Ausgangsdatensatz 208 ist gegen Katalog und Original-CSV geprüft; die falsche GNU-Standardbeschreibung wurde im Ergebnis korrigiert, nicht im erhaltenen Entwurf.
