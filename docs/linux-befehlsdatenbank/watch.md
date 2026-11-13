---
id: "watch"
name: "watch"
command: "watch"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["monitoring", "terminal", "wiederholung", "procps"]
status: "Korrigiert; Quellen und temporäres Terminalbeispiel geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 207
reviewed_at: "2026-11-13"
locally_checked_version: "watch from procps-ng 4.0.4"
---

# watch – Einen bewusst gewählten Befehl wiederholt anzeigen

## 1. Kurzbeschreibung

`watch` startet einen Befehl wiederholt und zeigt dessen Ausgabe bildschirmfüllend im Terminal. **Root ist für die Beobachtung eigener zugänglicher Daten nicht nötig.** Die Sicherheit hängt vom Unterbefehl ab: Ein wiederholter Schreib- oder Löschbefehl bleibt schreibend oder destruktiv. Die Katalogkategorie bleibt erhalten; technisch ist `watch` ein allgemeiner Wiederholungshelfer.

## 2. Was macht der Befehl?

Die hier beschriebene procps-ng-Variante verwendet ohne Intervalloption grundsätzlich zwei Sekunden; `WATCH_INTERVAL` kann einen anderen Vorgabewert liefern. `-n` wählt das Intervall ausdrücklich. Angezeigt werden Standard- und Fehlerausgabe, begrenzt durch die Bildschirmgröße.

Standardmäßig wird der Befehl über `sh -c` ausgeführt. Argumente durchlaufen dann zusätzlich eine Shell-Auswertung. `-x` führt das Programm direkt aus und erhält die übergebenen Argumentgrenzen, etwa bei einem Dateinamen oder Format mit Leerzeichen. Pipelines und Umleitungen werden in diesem Modus nicht als Shellsyntax ausgewertet. `-x` macht den Unterbefehl nicht ungefährlich.

Quelle: [procps-ng-watch-Manpage bei Debian](https://manpages.debian.org/trixie/procps/watch.1.en.html), zusätzlich lokale Hilfe und Manpage zu procps-ng 4.0.4 gelesen. Insbesondere `-e` bedeutet dort: Anzeige bei Fehler einfrieren und nach Tastendruck beenden; es ist keine automatische Wiederherstellung.

## 3. Syntax

```text
watch [WATCH_OPTIONEN] -- PROGRAMM [ARGUMENTE ...]
watch -x [WEITERE_WATCH_OPTIONEN] -- PROGRAMM [ARGUMENTE ...]
```

Watch-Optionen stehen vor dem Programmnamen. Danach gehören Optionen zum Unterbefehl. `--` markiert das Ende der Watch-Optionen; ein weiteres `--` kann separat für den Unterbefehl nötig sein. Alle dargestellten Optionen gelten für procps-ng, nicht automatisch für andere Implementierungen.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `-n SEK`, `--interval SEK` | Intervall ausdrücklich setzen. | Kein Echtzeitplaner; langsame Befehle brauchen trotzdem Zeit. |
| `-x`, `--exec` | Direkter Programmstart statt `sh -c`. | Keine Shell-Pipeline oder Umleitung ohne eigens gestartete Shell. |
| `-d`, `--differences` | Unterschiede zwischen Anzeigen hervorheben. | Vergleicht sichtbare Darstellung, nicht vollständige Dateiinhalte. |
| `-g`, `--chgexit` | Bei Änderung der sichtbaren Ausgabe beenden. | Nicht sichtbare Änderungen können unbemerkt bleiben. |
| `-q N`, `--equexit N` | Nach N Zyklen ohne Ausgabeänderung beenden. | Keine allgemeine Laufzeitgrenze für jeden beliebigen Unterbefehl. |
| `-e`, `--errexit` | Bei Fehler einfrieren, nach Tastendruck beenden. | Verhalten der lokal beschriebenen Version beachten. |
| `-t`, `--no-title` | Kopfzeile ausblenden. | Intervall und Zeitpunkt sind dann nicht sichtbar. |
| `-p`, `--precise` | Möglichst regelmäßige Startzeitpunkte versuchen. | Lange Laufzeiten und Nachholeffekte bleiben möglich. |
| `-w`, `--no-wrap` | Lange Zeilen abschneiden statt umbrechen. | Kann wichtige Teile der Ausgabe ausblenden. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GNU `stat`, procps-ng `watch` mit `-x` und `-q` sowie ein funktionsfähiges Terminal. Der Test verwendet nur eine eigene temporäre Datei. Alle Schritte in derselben Shell ausführen. Ohne Terminal können Fehler wie `Error opening terminal` entstehen; das ist keine Aussage über die Testdatei.

### Schritt 1: Kleine Datei mit Leerzeichen im Namen anlegen

```bash
uebung="$(mktemp -d -t netmon-watch-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' 'Test' > 'Meine Notiz.txt' || exit 1
```

Die Datei hat fünf Bytes einschließlich Zeilenumbruch. Der frische Ordner begrenzt alle Schreibzugriffe auf die Übung und bleibt danach erhalten.

### Schritt 2: Unterbefehl einzeln prüfen

```bash
stat -c '%s Byte' -- "$uebung/Meine Notiz.txt"
```

Die Ausgabe muss `5 Byte` lauten. Der Formattext ist ein Argument; der vollständige Dateipfad ein weiteres. Erst bei erfolgreicher Einzelprüfung mit der Wiederholung fortfahren.

### Schritt 3: Begrenzte Beobachtung starten

```bash
watch -n 1 -q 2 -x -- stat -c '%s Byte' -- "$uebung/Meine Notiz.txt"
```

`watch` zeigt die unveränderten `5 Byte` und beendet sich nach zwei unveränderten Folgezyklen normalerweise nach ungefähr zwei Sekunden. `-x` ist hier wesentlich: Es bewahrt sowohl den Formattext mit Leerzeichen als auch den Dateipfad als jeweils einzelnes Argument. Die Datei selbst wird nicht beschrieben.

Die Kopfzeile zeigt Befehl und Intervall. Während der Vollbildanzeige ist die normale Shell-Eingabe nicht verfügbar; nach dem Ende kehrt die Eingabeaufforderung zurück. Das automatische Ende dieser konstanten Ausgabe ist keine Zusicherung, dass `-q` jede Überwachung zeitlich begrenzt.

### Schritt 4: Inhalt nach der Beobachtung kontrollieren

```bash
cat -- 'Meine Notiz.txt'
```

Erwartet wird weiterhin `Test`. Bei einer später bewusst gestarteten Dauerbeobachtung ohne `-q` beendet `Ctrl+C` die Beobachtung normalerweise. Das Abbrechen kann bereits erfolgte Nebenwirkungen eines Unterbefehls nicht rückgängig machen.

## 6. Typische Anwendungsfälle

**Eigene Dateigröße verfolgen:** Mit einem lesenden `stat`-Aufruf Veränderungen sichtbar machen. Ein veränderter Größenwert erklärt noch nicht die Ursache.

**Lesenden lokalen Status beobachten:** Einen zuvor einzeln geprüften Statusbefehl mit angemessenem Intervall wiederholen. Aufwand und Ausgabeumfang müssen zum Intervall passen.

**Sichtbare Änderungen bemerken:** `-d` oder `-g` verwenden, wenn die relevante Ausgabe auf den Bildschirm passt. Für vollständige Ereignisprotokolle ein passendes anderes Werkzeug wählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Jede Wiederholung kann erneut schreiben, Prozesse starten oder Last verursachen. `watch` ist keine Sandbox und macht auch Fehler nicht rückgängig. Keine unüberprüften Skripte wiederholt starten; keine realen Netzabfragen zum Nachweis dieser Übung verwenden.

Ohne `-x` kann zusätzliche Shell-Auswertung Zeichen wie `$`, `*`, `;` oder Umleitungen neu interpretieren. Mit `-x` werden sie dagegen als Argumentdaten übergeben. Diese Unterschiede vor dem Übernehmen komplexer Aufrufe verstehen.

Die Anzeige kann geheime Pfade oder Werte enthalten; eine Bildschirmsitzung ist kein geschützter Protokollspeicher. Sehr kurze Intervalle und `-p` können unerwünschte Last verursachen. Keine privilegierte Beobachtung starten, wenn der Einzelbefehl keine Privilegien braucht.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Terminalfehler | Terminaltyp oder Terminalzugang fehlt. | In einem geeigneten Terminal starten. |
| Argument mit Leerzeichen zerfällt | Zusätzliche Shell-Auswertung ohne `-x`. | Für direkten Programmstart `-x` verwenden. |
| Pipeline funktioniert mit `-x` nicht | Direkter Start interpretiert keine Shelloperatoren. | Ausführungsmodell bewusst wählen. |
| `-g` reagiert nicht | Änderung außerhalb des sichtbaren Bereichs. | Ausgabeumfang reduzieren; nicht als vollständigen Vergleich behandeln. |
| `-q` läuft weiter | Ausgabe ändert sich oder Unterbefehl hängt. | Bedingung verstehen und gegebenenfalls abbrechen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Unterbefehl zuerst einzeln ausführen, danach mit kleinem eigenem Datenbestand wiederholen. Ein vernünftiges Intervall ausdrücklich setzen und einfache direkte Aufrufe bevorzugen. Für dauerhafte geplante Aufgaben ist eine kurzlebige Terminalbeobachtung kein Ersatz.

**Prüfstand am 2026-11-13:** `watch from procps-ng 4.0.4`; lokale Hilfe/Manpage und verlinkte Referenz gelesen. Abschnitt 5 in einem eigenen Pseudoterminal ausgeführt. `5 Byte` war sichtbar, `-q 2` beendete die Beobachtung erfolgreich; der Dateiinhalt blieb erhalten. Das ist ein Terminaltest, kein NetMon-GUI-Test.

**Nicht praktisch geprüft:** manueller Abbruch mit `Ctrl+C`, `-d`, `-g`, Fehler-Einfrieren mit `-e`, `-p`, Größenänderung des Terminals und andere Implementierungen. Keine Systemdienste oder Netzabfragen gestartet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `stat` | Metadaten einer eigenen Datei anzeigen. |
| `tail -f` | Neu angehängte Textdaten verfolgen statt alles erneut auszuführen. |
| `date` | Zeit anzeigen; lesender möglicher Unterbefehl. |
| `top` | Eigene interaktive Prozessbeobachtung. |

Ausgangsdatensatz 207 wurde mit Katalog und Original-CSV abgeglichen. Die feste Kategorie bleibt trotz allgemeiner Funktion unverändert.
