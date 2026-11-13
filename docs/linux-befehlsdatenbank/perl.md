---
id: "perl"
name: "perl"
command: "perl"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "perl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 292
reviewed_at: "2026-11-13"
locally_checked_version: "Perl 5.38.2"
---

# perl – Perl-Skripte und kontrollierte Textfilter verwenden

## 1. Kurzbeschreibung

perl startet den Perl-Interpreter. Er kann vollständige Programme oder kurze Textfilter ausführen. Auch ein scheinbarer Prüfmodus kann bereits Code während der Kompilierphase ausführen.

## 2. Was macht der Befehl?

Perl kompiliert zunächst in seine interne Form und führt anschließend den normalen Programmablauf aus. -c unterbindet diesen normalen Ablauf, jedoch nicht BEGIN-, UNITCHECK-, CHECK-Blöcke und use-Anweisungen. Es ist damit keine sichere Untersuchung fremder Skripte. -n legt eine Eingabeschleife an, -p zusätzlich eine automatische Ausgabe jeder verarbeiteten Zeile. Ohne -i verändert ein Filter die Quelldatei nicht von selbst; eine Shellumleitung kann dennoch Dateien überschreiben.

Quelle, am 2026-11-13 gelesen: [Perl-Porters: perlrun](https://perldoc.perl.org/perlrun)

## 3. Syntax

```text
perl [OPTIONEN] SKRIPT [ARGUMENTE...]
perl -e CODE [-- DATEIEN...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-v`, `-V` | Version beziehungsweise ausführliche Buildkonfiguration. |
| `-e CODE` | Kurzen Code ausführen; Shellzitierung beachten. |
| `-c` | Syntax prüfen, aber Compilezeitcode kann laufen. |
| `-n`, `-p` | Eingabeschleife ohne beziehungsweise mit automatischem Drucken. |
| `-i[ENDUNG]` | Dateien ersetzen, optional Sicherungsendung; nicht Teil der Übung. |
| `-I ORDNER`, `-M MODUL` | Modulsuche erweitern beziehungsweise Modul laden. |
| `-f` | Sitecustomize-Startcode unterdrücken, falls so gebaut. |
| `-T` | Taintprüfung; kein allgemeiner Sandboxingmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-292-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
env -u PERL5OPT -u PERL5LIB perl -f -e 'printf "Perl v%vd\n", $^V'
cat > lernen.pl <<'PERL'
use strict;
use warnings;
print "Hallo Perl ", 6 * 7, "
";
PERL
env -u PERL5OPT -u PERL5LIB perl -f -c lernen.pl
env -u PERL5OPT -u PERL5LIB perl -f lernen.pl
printf 'blau
' > vorher.txt
env -u PERL5OPT -u PERL5LIB perl -f -pe 's/blau/gruen/g' -- vorher.txt > nachher.txt
cat vorher.txt nachher.txt

```

### Schritt 3: Ergebnis auswerten

Die eigene Syntaxprüfung meldete lernen.pl syntax OK; der Start gab Hallo Perl 42 aus. Der Filter schrieb gruen in die neue nachher.txt, während vorher.txt weiterhin blau enthielt. Es wurde kein -i verwendet. Die geladenen strict-/warnings-Pragmas stammen aus der installierten Standardumgebung; der Test ist kein Nachweis harmloser Compilezeitaktionen in fremden Quellen. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Eigene Textumwandlungen: Ergebnis erst in eine neue Datei schreiben und vergleichen. Kleine Skripte entwickeln: Compilefehler und normale Laufzeitfehler auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

-i kann Originale ersetzen und Linkbeziehungen verändern. Fremde use-Module und Compileblöcke führen Code aus. Reguläre Ausdrücke mit Ausführungsmodifikatoren sind keine bloßen Suchmuster. Keine CPAN-Installation, fremden Module oder echten Benutzerdateien wurden verwendet. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Syntax OK als Sicherheitsfreigabe | Compilezeitaktionen bleiben möglich. |
| Ausgabe doppelt | -p druckt automatisch, zusätzliches print prüfen. |
| Variable von Shell ersetzt | Perl-Ausdruck unter Bash passend einfach zitieren. |
| Datei nach Filter leer | Ausgabe nicht auf dieselbe Eingabedatei umleiten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Perl 5.38.2. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sed` | Anderer Textfilter. |
| `awk` | Datensatzorientierte Textverarbeitung. |
| `python3` | Andere Programmiersprache. |

Ausgangsdatensatz 292 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
