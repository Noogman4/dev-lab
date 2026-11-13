---
id: "ruby"
name: "ruby"
command: "ruby"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "ruby"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 298
reviewed_at: "2026-11-13"
locally_checked_version: "Ruby 3.2.3, Revision 52bb2ac0a6, x86_64-linux-gnu"
---

# ruby – Ruby-Programme prüfen und ausführen

## 1. Kurzbeschreibung

ruby startet die Ruby-Laufzeit. Sie kann Skripte, Standardinput oder direkt angegebenen Code verarbeiten. -c prüft Syntax; der normale Programmstart ist davon zu trennen.

## 2. Was macht der Befehl?

Argumente nach der Skriptdatei stehen dem Programm über ARGV zur Verfügung. -e ersetzt die Skriptdatei durch Quelltext als Argument. -n und -p bilden Eingabeschleifen; -p druckt zusätzlich die verarbeitete Zeile. Geladene Bibliotheken und Startupoptionen beeinflussen die Umgebung. Ruby-Version, Implementierung und aktivierte Gems können sich von einem anderen Rechner unterscheiden.

Quelle, am 2026-11-13 gelesen: [Ruby-Projekt: Aufrufoptionen](https://docs.ruby-lang.org/en/3.4/ruby/options_md.html) und lokale Hilfe; Webfassung 3.4 und lokaler Test 3.2 sind getrennt ausgewiesen

## 3. Syntax

```text
ruby [OPTIONEN] [--] SKRIPT.rb [ARGUMENTE...]
ruby -e CODE
ruby -c SKRIPT.rb
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` | Version anzeigen und beenden. |
| `-v` | Version anzeigen und ausführlicheren Warnmodus aktivieren; kann danach Skript ausführen. |
| `-c` | Skript auf Syntax prüfen; kein Laufzeitnachweis. |
| `-w` | Warnungen aktivieren. |
| `-e CODE` | Rubycode direkt ausführen. |
| `-I ORDNER`, `-r BIBLIOTHEK` | Ladepfad ergänzen beziehungsweise Bibliothek vorladen. |
| `-i[ENDUNG]` | Eingabedateien an Ort und Stelle ersetzen, optional mit Sicherung. |
| `--disable-gems` | Automatisches RubyGems-Laden abschalten; keine Sandbox. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-298-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
env -u RUBYOPT -u RUBYLIB ruby --version
cat > lernen.rb <<'RUBY'
wert = 6 * 7
puts "Hallo Ruby #{wert}"
RUBY
env -u RUBYOPT -u RUBYLIB ruby --disable-gems -c lernen.rb
env -u RUBYOPT -u RUBYLIB ruby --disable-gems -w lernen.rb

```

### Schritt 3: Ergebnis auswerten

Die Syntaxprüfung meldete Syntax OK. Erst der separate Lauf gab Hallo Ruby 42 aus. Das eigene Skript lädt keine zusätzlichen Bibliotheken. RUBYOPT und RUBYLIB werden nur für die jeweiligen Prozesse entfernt; --disable-gems verringert Startabhängigkeiten, beschränkt aber nicht die Rechte des Rubyprogramms. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Eigene Skripte entwickeln: Syntaxdiagnose vor dem gezielten Lauf verwenden. Textfilter verstehen: Automatische Schleife und Druckausgabe voneinander unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rubycode, vorab geladene Bibliotheken und native Erweiterungen können Dateien, Prozesse oder Netz benutzen. Eine erfolgreiche Syntaxprüfung macht unbekannten Code nicht sicher. -i kann Originale ersetzen; Ergebnis zuerst in neue eigene Dateien schreiben. Keine Geminstallation und keine echte Anwendung wurden gestartet. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| LoadError | Ladepfad und passende Umgebung prüfen. |
| Syntax OK, aber NameError | Werte und ausgeführte Pfade sind erst zur Laufzeit bekannt. |
| Version erscheint, danach Aktion | -v beendet nicht in jedem Aufruf wie --version. |
| Shell verändert Code | Unter Bash korrekt zitieren, Interpolation bewusst trennen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Ruby 3.2.3, Revision 52bb2ac0a6, x86_64-linux-gnu. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `irb` | Interaktive Rubyumgebung. |
| `gem` | Paketverwaltung mit weiteren Schreib-/Netzvorgängen. |
| `perl` | Andere Skript- und Filterlaufzeit. |

Ausgangsdatensatz 298 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
