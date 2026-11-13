---
id: "fc"
name: "fc"
command: "fc"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "danger"
tags: ["bash builtins", "fc"]
status: "Lokale Primärhilfe und reine Anzeige selbst eingesetzter Testhistorie praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 83
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# fc – Shellhistorie anzeigen und erneute Ausführung unterscheiden

## 1. Kurzbeschreibung

`fc` ist ein Bash-Builtin zum Anzeigen, Bearbeiten und erneuten Ausführen früherer Shellbefehle. **Root-Rechte sind dafür nicht nötig.** Die hohe Risikostufe betrifft vor allem die erneute Ausführung: Ein früherer Lösch- oder Schreibbefehl kann dadurch nochmals wirken.

Für eine reine Anzeige muss die Listenform bewusst gewählt werden. Ein nacktes `fc` ist kein harmloser Ersatz für einen Blick in eine Textliste.

## 2. Was macht der Befehl?

Die Shell hält je nach Einstellung eine Verlaufsliste. Mit `fc -l` lässt sich ein Bereich daraus anzeigen. Ohne Listenmodus kann `fc` einen Editor öffnen und die bearbeiteten Befehle anschließend ausführen. `fc -s` wiederholt einen ausgewählten Befehl unmittelbar, gegebenenfalls nach Textersetzung.

Die lokale Primärquelle ist `help fc` aus Bash 5.2.21. Als ergänzende Referenz dient das [Bash-Builtin-Handbuch bei Debian](https://manpages.debian.org/trixie/bash/bash-builtins.7.en.html). Historie ist ein Komfortmerkmal, kein vertrauenswürdiges Auditprotokoll: Einstellungen, mehrere Sitzungen und manuelle Änderungen beeinflussen ihren Inhalt.

## 3. Syntax

```text
fc -l [-n] [-r] [ERSTER [LETZTER]]
fc [-e EDITOR] [ERSTER [LETZTER]]
fc -s [ALT=NEU] [AUSWAHL]
```

Die erste Form listet. Die zweite und dritte können Befehle ausführen. Auswahlwerte können Eintragsnummern oder geeignete Textanfänge sein; negative Zahlen beziehen sich auf relative Historiepositionen. Nicht raten, welcher frühere Eintrag gerade gemeint ist.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Gefahr oder Grenze |
| --- | --- | --- |
| `-l` | Einträge auflisten statt bearbeiten. | Bewusster Einstieg für lesende Kontrolle. |
| `-n` | Nummern bei der Liste weglassen. | Allein kein sicherer Ersatz für Listenmodus. |
| `-r` | Bereich in umgekehrter Reihenfolge behandeln. | Mit anderen Modi auf die spätere Reihenfolge achten. |
| `-e EDITOR` | Editor zum Bearbeiten auswählen. | Danach kann die Ausführung folgen. |
| `-s` | Befehl unmittelbar wiederholen. | Keine Vorschau und keine allgemeine Rückfrage. |
| `ALT=NEU` | Text vor Wiederholung ersetzen. | Textersetzung ist keine semantische Pfadprüfung. |

Die Editorwahl kann von `FCEDIT`, dann `EDITOR` und schließlich dem Standardeditor abhängen. Einen fremden oder überraschenden Editoraufruf nicht als reine Datenanzeige behandeln.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine isolierte Testhistorie verwenden

Der vollständige Aufruf startet eine neue Bash ohne persönliche Startdateien. Als Historiedatei ist nur `/dev/null` vorgesehen:

```bash
HISTFILE=/dev/null bash --noprofile --norc -c '
  history -s "printf TESTZEILE"
  fc -l -n
'
```

Es wird keine bestehende persönliche Historie geleert oder eingelesen. `history -s` setzt den angegebenen Text als eigenen Verlaufseintrag ein. Dieser Text wird dadurch **nicht ausgeführt**.

### Schritt 2: Angezeigten Text von Ausführung unterscheiden

Die Listenform zeigt den Text `printf TESTZEILE`, möglicherweise mit führender Einrückung. Würde der Befehl tatsächlich ausgeführt, wäre seine Ausgabe nur `TESTZEILE`. Gerade der sichtbare Programmname belegt hier die Anzeige des Historietextes.

### Schritt 3: Testgrenze festhalten

Die Kind-Shell endet nach der Liste. In der ursprünglichen Shell wird weder ein früherer Befehl ausgewählt noch wiederholt. Das Beispiel öffnet keinen Editor und setzt keine `fc -s`-Aktion ab. Die erwartete Wirkung ist ausschließlich die Anzeige einer selbst vorbereiteten Zeile.

## 6. Typische Anwendungsfälle

### Frühere Schreibweise nachsehen

Mit ausdrücklich gesetztem `-l` einen bekannten Bereich lesen. Vor Weitergabe persönliche Pfade, Zugangsdaten und andere vertrauliche Argumente entfernen.

### Bewusste Wiederverwendung

Fortgeschrittene Nutzer können einen früheren eigenen Befehl gezielt bearbeiten und nochmals ausführen. Vorher müssen aktuelle Pfade, Argumente, Berechtigungen und Umgebung erneut stimmen; alte erfolgreiche Ausführung ist keine heutige Freigabe.

### Shellverhalten lernen

Eine selbst erzeugte Testhistorie erklärt Auswahl und Darstellung ohne Zugriff auf echte Benutzereinträge. Leere Historie oder deaktivierte Aufzeichnung sind dabei mögliche normale Zustände.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine erneute Ausführung kann Dateien löschen, Daten überschreiben oder Netzwerkaktionen wiederholen. Zwischenzeitlich können sich Arbeitsverzeichnis, Variablen und Bestände geändert haben. Ein textlich identischer Befehl muss deshalb nicht dieselbe Wirkung haben.

Historietext kann Geheimnisse enthalten. Nicht die gesamte eigene Historie zur Fehlersuche veröffentlichen. Der Aufruf `fc -s` ist keine sichere Abkürzung für einen bloßen Vergleich. Auch bearbeitete Zeilen müssen vor Ausführung vollständig verstanden werden; das Schließen eines Editors bedeutet hier unter Umständen den Übergang zur echten Aktion.

## 8. Häufige Fehler

- **`fc` sollte nur anzeigen:** `-l` fehlte; Editor- und Ausführungsmodus wurden gewählt.
- **Falscher früherer Befehl ausgewählt:** Relative Position oder Textpräfix war nicht eindeutig verstanden.
- **Keine Einträge:** Historie ist leer, nicht aufgezeichnet oder in diesem Kontext nicht verfügbar.
- **`-n` als Nichtausführen verstanden:** Der Schalter betrifft Nummern, nicht allgemein die Ausführung.
- **Ersetzung traf mehr als erwartet:** Textmuster und tatsächliche Argumentbedeutung unterscheiden sich.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst nur `fc -l` oder eine eigene isolierte Testhistorie verwenden. Für eine echte Aktion ist ein vollständig neu formulierter und geprüfter Aufruf oft verständlicher als eine verdeckte Wiederholung. Keine Bearbeitungs- oder Wiederholungsform zum bloßen „Ausprobieren“ verwenden.

**Prüfstand:** Bash 5.2.21, lokale Hilfe und ergänzende Handbuchbeschreibung geprüft. Eine selbst eingefügte Testzeile in einer getrennten Bash angezeigt, Status 0. Keine persönliche Historie gelesen oder gelöscht. Editor, `-s`, relative Bereiche und tatsächliche Wiederholung nicht praktisch geprüft.

## 10. Verwandte Befehle

- `history`: Verlauf anzeigen oder verwalten; einzelne Optionen verändern ihn.
- `help fc`: installierte Builtin-Hilfe.
- `type fc`: Einordnung als Builtin prüfen.
- `read`: eigene Eingabedaten lesen, ohne Historiewiederholung.

Ausgangseintrag: Datensatz 83 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
