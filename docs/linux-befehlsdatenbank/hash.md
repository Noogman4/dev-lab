---
id: "hash"
name: "hash"
command: "hash"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "hash"]
status: "Lokale Primärhilfe sowie Eintragen, Anzeigen und Entfernen in Kind-Bash geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 87
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# hash – Gespeicherte Programmpfade der Bash verwalten

## 1. Kurzbeschreibung

`hash` ist ein Bash-Builtin für den Zwischenspeicher externer Programmpfade. Es hat hier **nichts mit kryptografischen Prüfsummen** zu tun. **Root-Rechte sind nicht nötig.** Der Cache gehört zunächst zur jeweiligen Shell.

Wer den Inhalt einer Datei prüfen möchte, benötigt beispielsweise `sha256sum`. Wer dagegen verstehen möchte, welchen externen Pfad Bash gespeichert hat, ist bei diesem Builtin richtig.

## 2. Was macht der Befehl?

Bash kann den bei einer Suche in `PATH` gefundenen Programmpfad speichern. Spätere Aufrufe müssen dann nicht dieselbe vollständige Pfadsuche wiederholen. `hash NAME` ermittelt und merkt einen passenden Pfad, führt das Zielprogramm aber nicht allein dadurch aus.

Einträge können gezielt angezeigt oder vergessen werden. Das ist nützlich, wenn ein Programm verschoben wurde oder ein alter Verweis irritiert. Es ist keine sichere Identitätsprüfung: Ein gespeicherter Pfad kann auf inzwischen andere Bytes zeigen. Primärquelle ist die lokale Hilfe `help hash` aus Bash 5.2.21; weiterführend: [Bash-Builtins](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html).

## 3. Syntax

```text
hash [OPTIONEN] [NAME ...]
hash -t NAME
hash -d NAME
hash -r
```

Ohne Argumente wird der bestehende Speicher angezeigt. `NAME` bezeichnet den aufzulösenden externen Befehlsnamen. Builtins, Aliase und Funktionen sind weitere Ebenen der Shellauflösung, die nicht einfach durch diese Pfadliste vollständig beschrieben werden.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-t NAME` | Gespeicherten Pfad anzeigen. | Fehlender Eintrag kann einen Fehlerstatus liefern. |
| `-d NAME` | Einzelnen gespeicherten Pfad vergessen. | Entfernt keine Programmdatei. |
| `-r` | Alle gespeicherten Pfade vergessen. | Betrifft Shellcache, nicht Softwareinstallation. |
| `-l` | Einträge in wiederverwendbarer Form anzeigen. | Ausgabe nicht ungeprüft als Skript übernehmen. |
| `-p PFAD NAME` | Vorgegebenen Pfad für einen Namen speichern. | Kann die spätere Ausführung gezielt umlenken. |
| `help hash` | Installierte Primärhilfe lesen. | Kein kryptografischer Hashlauf. |

Ein Trefferzähler in einer Cacheanzeige ist kein Auditnachweis aller Programmstarts. Andere Aufrufweisen oder Prozesse besitzen eigene Zustände.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine eigene Shell ohne Startdateien verwenden

Die folgende vollständige Sequenz kann in einer separaten Bash ausgeführt werden:

```bash
hash uname
hash -t uname
hash -d uname
if hash -t uname >/dev/null 2>&1; then
  printf 'Noch gespeichert\n'
else
  printf 'Eintrag entfernt\n'
fi
```

Es wird nur die Verfügbarkeit des externen Namens `uname` für den Cache betrachtet. Das Programm selbst wird durch diese Sequenz nicht gestartet.

### Schritt 2: Auflösung und Speicher unterscheiden

Der erste Aufruf sucht den Namen im verfügbaren `PATH`. Der zweite zeigt den gespeicherten Pfad. Im isolierten Test mit `PATH=/usr/bin:/bin` war das `/usr/bin/uname`. Auf einem anderen System kann der Pfad abweichen.

### Schritt 3: Vergessen überprüfen

`hash -d uname` entfernt nur den Cacheeintrag. Die folgende Abfrage wird bewusst als Bedingung behandelt; ein fehlender Eintrag führt zur Ausgabe `Eintrag entfernt`. Die Programmdatei bleibt bestehen und könnte bei einem späteren echten Aufruf neu gefunden werden.

Erwartete Ausgabe der geprüften Umgebung:

```text
/usr/bin/uname
Eintrag entfernt
```

## 6. Typische Anwendungsfälle

### Alten Verweis nach einer Änderung untersuchen

Ein gespeicherter Pfad ist nicht mehr passend. Zuerst anzeigen und Ursache verstehen, dann gezielt vergessen. Nicht als ersten Schritt Programme löschen oder Rechte verändern.

### Shellauflösung lernen

Mit `type NAME` und `hash -t NAME` verschiedene Aspekte vergleichen. Dass ein Name als Funktion aufgelöst wird, ist etwas anderes als ein gespeicherter externer Pfad.

### Bewusst gebundene Testpfade verwalten

Fortgeschrittene Skripte können Pfade ausdrücklich setzen. Dabei muss der gesamte Pfad samt Besitz, Austauschmöglichkeiten und Programmidentität vertrauenswürdig sein. Ein Cache allein bietet diese Garantie nicht.

## 7. Risiken, Nebenwirkungen und Vorsicht

`-p` kann einen vertrauten Namen auf ein anderes Programm lenken. Dadurch kann der nächste gleich geschriebene Aufruf unerwartete Aktionen ausführen. Keine fremden Cacheanweisungen oder wieder einlesbaren Listen blind ausführen.

Ein gespeicherter absoluter Pfad prüft weder den aktuellen Dateiinhalt noch dessen Herkunft. Eine ausgetauschte Datei an derselben Stelle bleibt möglich. Cacheanzeigen können persönliche Installationspfade verraten. Das Entfernen von Einträgen repariert keine unsicheren `PATH`-Verzeichnisse und ist kein allgemeines Härtungsverfahren.

## 8. Häufige Fehler

- **Dateiprüfsumme erwartet:** `hash` ist hier ein Auflösungscache, kein Hashalgorithmus.
- **Kein Eintrag gefunden:** Der Name wurde nicht gespeichert oder inzwischen vergessen.
- **Programm nach `-d` weiter vorhanden:** Genau richtig; nur Cachezustand wurde entfernt.
- **Alle Auflösungen aus Cache abgeleitet:** Funktionen, Aliase und Builtins haben eigene Regeln.
- **Gespeicherter Pfad als Sicherheitsbeweis betrachtet:** Aktuelle Dateiidentität wurde nicht geprüft.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit lesender Anzeige beginnen. Für Lernversuche eine zusätzliche Shell verwenden und keine vorgegebenen fremden Pfade mit `-p` setzen. Bei Problemen genaue Auflösung und Fehlermeldung betrachten, statt pauschal `hash -r` als Reparatur für jede Ursache einzusetzen.

**Prüfstand:** Bash 5.2.21 und lokale Hilfe gelesen. `uname` in einer getrennten Bash ohne persönliche Startdateien gespeichert, angezeigt und gezielt vergessen; erwartete Ausgaben, Status 0. Zielprogramm nicht ausgeführt und Programmdateien nicht verändert. Pfadumlenkung mit `-p`, austauschbare Dateien und andere Shells nicht praktisch geprüft.

## 10. Verwandte Befehle

- `type`: Auflösungsart und mögliche Definitionen anzeigen.
- `command -v`: eine Befehlsauflösung abfragen.
- `enable`: Verfügbarkeit von Bash-Builtins steuern.
- `sha256sum`: tatsächliche Dateiprüfsummen berechnen, andere Aufgabe.

Ausgangseintrag: Datensatz 87 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
