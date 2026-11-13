---
id: "done"
name: "done"
command: "done"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "done"]
status: "Lokale Schleifenhilfen und Grenze des Schleifenkörpers praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 78
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# done – Eine Shellschleife korrekt abschließen

## 1. Kurzbeschreibung

`done` ist das abschließende Schlüsselwort für Shellschleifen wie `for`, `while` und `until`. Es ist kein externer Befehl und bedeutet nicht, dass eine Aufgabe erfolgreich war. **Root ist für diese Sprachkonstruktion nicht nötig.**

Der Abschluss legt fest, welche Anweisungen wiederholt werden und welche erst nach dem Ende der Schleife folgen. Diese Grenze ist für das Verständnis eines Skripts wichtiger als die rein optische Einrückung.

## 2. Was macht der Befehl?

Die Shell erkennt mit `done` das Ende des vorher durch `do` begonnenen Körpers. Je nach Schleifenart folgt danach der nächste Wert, eine Fortschaltung oder eine erneute Bedingungsprüfung. Erst wenn die Schleife endet, wird der Code hinter dem gesamten Konstrukt erreicht.

Primärquellen sind die lokal gelesenen Hilfen zu `for`, `while` und `until` in Bash 5.2.21. Das [Bash-Handbuch zu Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html) ist weiterführend verlinkt; der Onlineabruf war hier nicht verfügbar. `done` selbst besitzt keine eigenständige Hilfeoption oder Statusausgabe.

## 3. Syntax

```text
for NAME in WERTE; do
  BEFEHLE
done

while BEDINGUNG; do
  BEFEHLE
done
```

In einer einzeiligen Form muss auch der letzte Befehl vor `done` sauber abgeschlossen werden, beispielsweise mit einem Semikolon. Bei verschachtelten Schleifen benötigt jede ihren passenden Abschluss. Ein `fi` schließt eine Bedingung, aber keine Schleife.

## 4. Wichtige Optionen

Es gibt keine Optionen von `done`. Relevant sind Kontext und Anordnung:

| Form | Bedeutung | Hinweis |
| --- | --- | --- |
| `do ... done` | Körper einer Schleife abgrenzen. | Gehört zum vorherigen Schleifenkopf. |
| `done` auf eigener Zeile | Lesbarer mehrzeiliger Abschluss. | Einrückung entsprechend dem Beginn wählen. |
| `...; done` | Abschluss einer einzeiligen Form. | Das Trennzeichen ist erforderlich. |
| Code nach `done` | Wird nach Schleifenende erreicht. | Nicht mehr pro Durchlauf ausführen. |

Eine Umleitung am gesamten Schleifenkonstrukt kann alle enthaltenen Ausgaben beziehungsweise Eingaben betreffen. Sie ist keine Option von `done`; ihre tatsächliche Wirkung muss separat betrachtet werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Innen und außen sichtbar machen

```bash
for wert in eins zwei; do
  printf 'Innen: %s\n' "$wert"
done
printf 'Nach der Schleife\n'
```

Der Körper enthält nur den ersten `printf`-Aufruf. Der zweite steht ausdrücklich hinter dem Abschluss. Es werden keine Dateien gelesen oder verändert.

### Schritt 2: Wiederholung verfolgen

Für `eins` erscheint eine Innenzeile. Danach erreicht der Ablauf `done`, die Schleife nimmt den nächsten Wert und führt denselben Körper erneut aus. Nach `zwei` gibt es keinen weiteren Listenwert; erst jetzt folgt die Ausgabe außerhalb des Körpers.

### Schritt 3: Erwartetes Ergebnis vergleichen

```text
Innen: eins
Innen: zwei
Nach der Schleife
```

Würde die letzte `printf`-Zeile vor `done` verschoben, erschiene sie ebenfalls pro Durchlauf. Ein solches Versehen ist syntaktisch möglicherweise völlig gültig und wird daher nicht allein durch einen Syntaxcheck erkannt.

## 6. Typische Anwendungsfälle

### Abschlussmeldung nach Verarbeitung

Ein Skript kann nach einer Liste einmal zusammenfassen, statt nach jeder Datei dieselbe Meldung auszugeben. Für eine ehrliche Erfolgsmeldung muss es zusätzlich die tatsächlichen Fehler der Verarbeitung berücksichtigen.

### Aufbau verschachtelter Abläufe lesen

Passende `do`-/`done`-Paare markieren, welche Anweisungen zur inneren und welche zur äußeren Schleife gehören. Klare Einrückung erleichtert diese Zuordnung.

### Gesamtausgabe umleiten

Eine bewusst am vollständigen Schleifenkonstrukt angebrachte Umleitung kann mehrere Ausgaben bündeln. Bei Schreibumleitungen sind Überschreiben und Zielpfad eigene Risiken; das Beispiel verwendet deshalb keine Umleitung.

## 7. Risiken, Nebenwirkungen und Vorsicht

`done` selbst schreibt keine Daten. Ein falsch gesetzter Abschluss kann aber eine eigentlich einmalige Aktion in die Schleife aufnehmen oder notwendige Arbeit daraus entfernen. Bei Lösch-, Installations- oder Netzwerkaktionen wäre das erheblich.

Ein syntaktisch korrektes `done` beweist weder, dass die Schleife endet, noch dass alle Durchläufe erfolgreich waren. Ein letztes erfolgreiches `printf` kann einen zuvor relevanten Status überdecken. Rückgabewerte deshalb zeitnah erfassen, wenn der Ablauf sie benötigt. In Pipeline-Konstrukten können zusätzlich Subshell- und Statusregeln eine Rolle spielen.

## 8. Häufige Fehler

- **Unerwartetes Dateiende:** Ein zugehöriges `done` oder ein anderer Abschluss fehlt.
- **Unerwartetes Token:** Es gibt einen zusätzlichen Abschluss oder ein Trennzeichen fehlt.
- **Falscher Abschluss:** `esac` gehört zu `case`, `fi` zu `if`.
- **Meldung wird mehrfach ausgegeben:** Sie steht noch innerhalb des Körpers.
- **Dauerlauf trotz korrekter Syntax:** Schleifenbedingung oder Fortschaltung ist falsch.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mehrzeilig schreiben und Innen-/Außengrenzen zunächst mit einfachen Ausgaben sichtbar machen. Einen Syntaxcheck als Grammatikprüfung verstehen; er findet nicht jede logisch falsch platzierte, aber gültige Anweisung.

**Prüfstand:** Bash-5.2.21-Schleifenhilfen gelesen. Das vollständige Innen-/Außenbeispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; genau die drei erwarteten Zeilen, Status 0. Keine Benutzerdateien oder Systemeinstellungen verändert. Umleitungen, verschachtelte Schleifen und Pipeline-Status für diesen Eintrag nicht praktisch geprüft.

## 10. Verwandte Befehle

- `do`: Beginn des Schleifenkörpers.
- `for`, `while`, `until`: Schleifen, die `done` abschließt.
- `fi`: Abschluss einer if-Auswahl.
- `esac`: Abschluss einer case-Auswahl.

Ausgangseintrag: Datensatz 78 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
