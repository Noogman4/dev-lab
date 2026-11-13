---
id: "logout"
name: "logout"
command: "logout"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "logout"]
status: "Lokale Primärhilfe und lesende Shelltyp-Prüfung getestet; Logout nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 91
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# logout – Eine Login-Shell bewusst beenden

## 1. Kurzbeschreibung

`logout` ist ein Bash-Builtin zum Verlassen einer Login-Shell. **Root-Rechte sind dafür nicht nötig.** Der Aufruf kann eine wichtige Sitzung beenden; er ist kein geeigneter bloßer „Funktionstest“ in einer laufenden Arbeitsumgebung.

Eine Login-Shell ist eine bestimmte Startart der Shell. Nicht jedes Terminalfenster und nicht jede interaktive Bash ist automatisch eine Login-Shell. Der Befehl ist außerdem kein allgemeiner Desktop-Abmelde- oder Ausschaltbefehl.

## 2. Was macht der Befehl?

In einem passenden Login-Kontext beendet `logout` die Shell mit dem angegebenen Status. Bei einer gewöhnlichen Nicht-Login-Shell liefert Bash stattdessen einen Fehler. Ob mit dem Shellende auch eine entfernte Verbindung oder ein Terminalfenster endet, hängt vom umgebenden Sitzungsaufbau ab.

Primärquelle ist die lokal gelesene Hilfe `help logout` aus Bash 5.2.21. Weiterführend: [Bash-Builtins](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) und die Bash-Beschreibung von Login-/Startdateien. Ein Abmeldeablauf kann auch konfigurierte Abschlussaktionen betreffen; daher nicht als nebenwirkungsfrei einstufen.

## 3. Syntax

```text
logout [STATUS]
```

Eckige Klammern kennzeichnen ein optionales Argument und werden nicht mitgetippt. Der Status ist ein Abschlusswert, keine Benutzerkennung und keine Sitzungsnummer. Für gewöhnliche Nicht-Login-Shells ist `exit` der verwandte Mechanismus; auch dieser kann die ausführende Sitzung beenden und wird hier nicht als Übung aufgerufen.

## 4. Wichtige Optionen

`logout` hat keine allgemeine Optionsliste.

| Form | Bedeutung | Hinweis |
| --- | --- | --- |
| `logout` | Login-Shell beenden. | Ausführung beendet möglicherweise die aktuelle Arbeitssitzung. |
| `logout STATUS` | Abschlussstatus ausdrücklich setzen. | Nicht mit einer Signalnummer verwechseln. |
| `help logout` | Lokale Beschreibung lesen. | Kein Abmelden. |
| `shopt -q login_shell` | Login-Eigenschaft in Bash prüfen. | Rückgabestatus statt gewöhnlicher Textausgabe. |

Die genauen Status- und Abschlussregeln in einer produktiven Umgebung vorher anhand der tatsächlich verwendeten Shell und ihrer Startart klären.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die Hilfe lesen

```bash
help logout
```

Das erklärt die Funktion, beendet aber keine Sitzung. Ein pauschaler Aufruf `logout --help` ist kein Ersatz für die Builtin-Hilfe.

### Schritt 2: Nur den Shelltyp untersuchen

Der folgende vollständige Aufruf startet ausdrücklich eine neue gewöhnliche Bash ohne persönliche Startdateien und fragt deren Eigenschaft ab:

```bash
bash --noprofile --norc -c '
  if shopt -q login_shell; then
    printf "Login-Shell\n"
  else
    printf "Keine Login-Shell\n"
  fi
'
```

Erwartet wird `Keine Login-Shell`. Das Kind wurde ohne Login-Modus gestartet. Die Eigenschaft des Kindes sagt nicht automatisch, welchen Typ die ursprüngliche Elternshell besitzt.

### Schritt 3: Aussagegrenze beachten

Es wurde kein `logout` ausgeführt. Der Kindprozess endet regulär nach seiner kleinen Prüfsequenz. Das ist eine lesende Prüfung des Kontexts, kein Nachweis eines vollständigen Abmeldeablaufs, keiner SSH-Verbindung und keiner Desktop-Sitzung.

## 6. Typische Anwendungsfälle

### Bewusstes Ende einer Login-Sitzung

Nach abgeschlossener Arbeit kann eine passende textbasierte Sitzung beendet werden. Vorher laufende Aufgaben, benötigte Ausgaben und mögliche Abschlussaktionen prüfen.

### Fehlermeldung verstehen

Ein Terminal meldet, dass es keine Login-Shell sei. Die Startart erklären, statt daraus fehlende Root-Rechte oder einen kaputten Benutzeraccount abzuleiten.

### Sitzungsaufbau dokumentieren

Interaktive Shell, Login-Shell, SSH-Sitzung und grafische Anmeldung als getrennte Begriffe behandeln. Sie können zusammenhängen, sind aber nicht gleichbedeutend.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Ende einer Shell kann laufende Arbeit unterbrechen oder beeinflussen, abhängig von Jobverwaltung, Terminal und Sitzungssteuerung. Ein im Hintergrund gestartetes Programm ist nicht allein dadurch gegen Sitzungsende geschützt. Vor dem Verlassen wichtige Arbeitsstände sichern und Prozessverwaltung passend planen.

Konfigurierte Abschlussdateien oder andere Sitzungsmechanismen können zusätzliche Aktionen ausführen. Deshalb wird hier auch keine künstliche Login-Shell gestartet, nur um ihr Ende zu testen. Eine Verbindung, deren Wiederanmeldung unklar ist, nicht aus Neugier schließen. Der Aufruf meldet nicht beliebige andere Benutzer ab.

## 8. Häufige Fehler

- **Fehler in normalem Terminal:** Die Bash ist möglicherweise keine Login-Shell.
- **Desktop-Abmeldung erwartet:** `logout` steuert hier eine Shell, nicht universell den grafischen Sitzungsmanager.
- **Andere Sitzung beenden wollen:** Das Argument ist keine Sitzungs-ID.
- **Hilfe mit Aktionsaufruf verwechselt:** `help logout` verwenden.
- **Hintergrundaufgaben als unabhängig angenommen:** Verhalten bei Sitzungsende gesondert planen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst nur Hilfe und Shelltyp prüfen. Den eigentlichen Aktionsaufruf als bewussten Abschluss einer tatsächlich verstandenen Sitzung behandeln. Keine Hauptsitzung oder Administrationsverbindung zum Testen schließen.

**Prüfstand:** Bash 5.2.21 und lokale Logout-Hilfe gelesen. Shelltyp-Prüfung in einer getrennten Bash ohne persönliche Startdateien ausgeführt; `Keine Login-Shell`, Status 0. Kein Logout, keine Login-Shell, keine Abschlussdatei und kein Desktop-Abmeldeablauf praktisch gestartet. Sitzungsende und Auswirkungen auf Jobs bleiben offen.

## 10. Verwandte Befehle

- `exit`: ausführende Shell beziehungsweise Skriptprozess beenden.
- `return`: Funktion oder eingelesenes Skript verlassen, anderer Kontext.
- `shopt`: bestimmte Bash-Eigenschaften abfragen oder verändern.
- `jobs`, `wait`: eigene Shelljobs und deren Abschluss betrachten.

Ausgangseintrag: Datensatz 91 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
