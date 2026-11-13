---
id: "coproc"
name: "coproc"
command: "coproc"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "coproc"]
status: "Lokale Primärhilfe und begrenzter Pipe-Dialog praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 76
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# coproc – Mit einem nebenläufigen Bash-Prozess über Pipes sprechen

## 1. Kurzbeschreibung

`coproc` ist ein Bash-Schlüsselwort, das einen Befehl asynchron startet und seine Ein- und Ausgabe über Pipes mit der aufrufenden Shell verbindet. **Root-Rechte sind dafür nicht nötig.** Es eignet sich für fortgeschrittene Skripte, die mit einem länger laufenden Hilfsprozess Daten austauschen.

Es ist kein allgemeiner Dienstmanager und kein sicherer Ausführungskäfig. Der gestartete Befehl behält die normalen Rechte und möglichen Nebenwirkungen seiner Ausführungsumgebung.

## 2. Was macht der Befehl?

Bei einem benannten Coprozess legt Bash ein Array an. Element 0 bezeichnet das Ende, aus dem die Elternshell die Kindausgabe liest. Element 1 ist das Ende, an das sie Eingabe für das Kind schreibt. Zusätzlich gibt es eine PID-Variable für die Prozessüberwachung.

Das Starten ist nicht gleichbedeutend mit erfolgreichem Abschluss. Der Kindprozess läuft eigenständig weiter. Sein Endstatus wird mit `wait` betrachtet. Primärquelle ist `help coproc` in der lokal vorhandenen Bash 5.2.21; weiterführend: [Bash-Handbuch zu Coprozessen](https://www.gnu.org/software/bash/manual/html_node/Coprocesses.html). Der tatsächlich geprüfte Umfang steht in Abschnitt 9.

## 3. Syntax

```text
coproc NAME { BEFEHLE; }
coproc BEFEHL [ARGUMENTE ...]
```

Für einen ausdrücklich benannten Coprozess ist die zusammengesetzte Form mit geschweiften Klammern gut nachvollziehbar. Ohne Namen wird `COPROC` verwendet. Die Syntax ist Bash-spezifisch und darf nicht einfach in ein beliebiges `/bin/sh`-Skript übertragen werden.

## 4. Wichtige Optionen

`coproc` besitzt keine normale Optionsliste. Entscheidend sind die zugehörigen Shellbausteine:

| Ausdruck | Bedeutung | Hinweis |
| --- | --- | --- |
| `${NAME[0]}` | Lesedeskriptor zur Kindausgabe. | Kein Dateiname. |
| `${NAME[1]}` | Schreibdeskriptor zur Kindeingabe. | Ein Protokoll kann Zeilenabschlüsse benötigen. |
| `$NAME_PID` | Von Bash bereitgestellte Kind-PID. | Früh in eigener Variable sichern. |
| `wait "$pid"` | Ende und Status des Kindes abwarten. | Startstatus allein reicht nicht. |
| `exec {fd}<&...` | Eigenen Deskriptor duplizieren. | Lebensdauer kontrollieren und später schließen. |

Die eckigen Klammern sind hier echte Arraysyntax, keine optionalen Platzhalter. Eingabe- und Ausgaberichtung nicht vertauschen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen begrenzten Dialog starten

In einer separaten Bash folgenden vollständigen Block verwenden:

```bash
coproc ECHO_TEST {
  IFS= read -r eingabe
  printf 'Antwort: %s\n' "$eingabe"
}
kind_pid=$ECHO_TEST_PID
exec {lese_fd}<&"${ECHO_TEST[0]}"
printf 'Hallo\n' >&"${ECHO_TEST[1]}"
IFS= read -r antwort <&"$lese_fd"
printf '%s\n' "$antwort"
exec {lese_fd}<&-
wait "$kind_pid"
```

### Schritt 2: Reihenfolge verstehen

Das Kind wartet zunächst auf genau eine Eingabezeile. Dadurch bleibt Zeit, die PID zu sichern und den Lesedeskriptor zu duplizieren. Die Elternshell sendet `Hallo` samt Zeilenumbruch. Darauf erzeugt das Kind eine Antwort und endet.

Die eigene Kopie des Lesedeskriptors hält den Lesezugriff unabhängig von der späteren Verwaltung des Coprozessarrays offen. Bash kann ihre zugehörigen Variablen und Deskriptoren nach dem Kindende aufräumen; sofort endende Kinder sind deshalb eine mögliche Quelle für Wettläufe.

### Schritt 3: Ergebnis und Abschluss prüfen

Erwartete sichtbare Ausgabe:

```text
Antwort: Hallo
```

Danach wird der eigene Lesedeskriptor geschlossen und `wait` wartet auf genau das gestartete Kind. Ein realer Dialog müsste zusätzlich jeden Schreib-/Lesestatus, Zeitüberschreitungen und unerwartetes Kindende behandeln. Das feste Ein-Nachrichten-Beispiel ist kein vollständiges robustes IPC-Protokoll.

## 6. Typische Anwendungsfälle

### Wiederverwendbarer Hilfsprozess

Ein Skript kann mehrere Anfragen an einen bewusst ausgewählten Prozess senden, statt ihn jedes Mal neu zu starten. Das benötigt ein eindeutig definiertes Anfrage-/Antwortformat.

### Nebenläufige Verarbeitung

Eine begrenzte Aufgabe kann laufen, während die Elternshell andere Schritte ausführt. Der spätere Abschluss muss dennoch zuverlässig abgewartet und bewertet werden.

### Shell-IPC lernen

Das Beispiel macht Dateideskriptoren, Pipe-Richtung und Lebensdauer sichtbar. Für eine reine einmalige Datenfolge ist eine gewöhnliche Pipeline oft einfacher.

## 7. Risiken, Nebenwirkungen und Vorsicht

Beide Seiten können blockieren, wenn jede zuerst auf Daten wartet oder eine Pipe voll wird. Fehlender Zeilenumbruch oder Ausgabepufferung kann wie ein Verbindungsfehler wirken. Lange laufende Protokolle benötigen Fristen und geordnetes Schließen der Schreibseite, damit die Gegenseite EOF erkennen kann.

Der gestartete Befehl kann Dateien oder Netzwerke verwenden. `coproc` begrenzt diese Rechte nicht. Nicht von beliebig vielen unabhängig verwalteten Coprozessen pro Shell ausgehen. Deskriptoren lassen sich nicht bedenkenlos in jede Subshell oder externe Anwendung übernehmen; deren Vererbung bewusst prüfen.

## 8. Häufige Fehler

- **Index 0 und 1 vertauscht:** Lese- und Schreibende verwechselt.
- **Variablen nach Kindende verschwunden:** PID und benötigten Deskriptor rechtzeitig sichern.
- **Dialog hängt:** Beide Seiten warten, Pufferung oder Zeilenabschluss prüfen.
- **Start erfolgreich, Aufgabe fehlgeschlagen:** Endstatus mit `wait` auswerten.
- **Skript läuft unter sh:** Bash-spezifische Syntax wurde nicht berücksichtigt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit genau einem Kind und einer kurzen festen Nachricht beginnen. Keine fremden Eingaben als Shellcode ausführen. Für produktive Protokolle Statusprüfungen, Zeitlimits, EOF-Verhalten und Aufräumen separat ausarbeiten.

**Prüfstand:** Lokale Bash-5.2.21-Hilfe gelesen. Ein-Nachrichten-Dialog in einer getrennten Bash ohne persönliche Startdateien ausgeführt; `Antwort: Hallo`, Status 0, Kind mit `wait` abgeschlossen. Keine Benutzerdateien, externen Dienste oder Netzwerkverbindungen verwendet. Mehrfachdialog, Fehlerpfade, Pufferlast und Zeitüberschreitungen offen.

## 10. Verwandte Befehle

- `read`: Daten aus einer Pipe oder einem Deskriptor lesen.
- `wait`: Kindprozessabschluss abwarten.
- `exec`: unter anderem Deskriptoren gezielt verwalten.
- `jobs`: Shelljobs anzeigen; anderer Blick auf Prozessverwaltung.
- Gewöhnliche Pipelines: oft einfacher für einmalige Datenflüsse.

Ausgangseintrag: Datensatz 76 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
