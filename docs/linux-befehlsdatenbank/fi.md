---
id: "fi"
name: "fi"
command: "fi"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "fi"]
status: "Lokale if-Hilfe und vollständig abgeschlossene Auswahl praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 84
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# fi – Eine if-Auswahl korrekt abschließen

## 1. Kurzbeschreibung

`fi` ist das abschließende Shell-Schlüsselwort einer `if`-Auswahl. Der Name ist `if` rückwärts geschrieben. **Root-Rechte sind nicht nötig.** Es handelt sich nicht um ein eigenständiges Programm, das man mit beliebigen Optionen starten könnte.

Der Abschluss gehört zur Grammatik. Er bestätigt weder den Erfolg der Bedingung noch den Erfolg einer enthaltenen Arbeitsaktion.

## 2. Was macht der Befehl?

Eine vollständige if-Auswahl enthält eine erste Bedingung und deren `then`-Zweig. Optional folgen `elif` und `else`. Das passende `fi` schließt die ganze Auswahl; erst dahinter liegt der gemeinsame weitere Ablauf.

Bei Verschachtelung benötigt jedes `if` ein eigenes `fi`. Einrückung macht diese Zuordnung sichtbar, ersetzt sie aber nicht. Als Primärquelle wurde die lokale Hilfe `help if` aus Bash 5.2.21 gelesen. Die weiterführende Grammatik ist im [Bash-Handbuch](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html) beschrieben; dessen Onlineabruf war zuvor nicht verfügbar.

## 3. Syntax

```text
if BEDINGUNG; then
  BEFEHLE
else
  ALTERNATIVE
fi
```

Die Bedingung ist eine Befehlsliste. Ihr Rückgabestatus bestimmt den Zweig: 0 gilt als Erfolg. `else` ist optional, `fi` nicht. Bei einzeiliger Schreibweise müssen die Befehle vor dem Abschluss passend mit Semikolon oder einem anderen zulässigen Trennzeichen abgeschlossen werden.

## 4. Wichtige Optionen

`fi` besitzt keine Optionen. Zu unterscheiden sind die zugehörigen Sprachbausteine:

| Baustein | Rolle | Hinweis |
| --- | --- | --- |
| `if` | Auswahl beginnen. | Eröffnet den zu schließenden Rahmen. |
| `then` | Erfolgszweig beginnen. | Kein Ersatz für den Abschluss. |
| `elif` | Weitere Bedingung prüfen. | Benötigt eigenes then, aber kein zusätzliches fi. |
| `else` | Verbleibenden Restfall behandeln. | Ohne eigene Bedingung. |
| `fi` | Gesamte Auswahl schließen. | Gehört zum passenden offenen if. |

Ein Statusvergleich oder eine Schreibumleitung hinter dem gesamten Konstrukt ist keine Option von `fi`. Solche Ergänzungen haben eigene Auswirkungen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine kleine feste Entscheidung schreiben

```bash
anzahl=0
if [ "$anzahl" -gt 0 ]; then
  printf 'Einträge vorhanden\n'
else
  printf 'Keine Einträge\n'
fi
printf 'Weiter\n'
```

`anzahl` ist nur ein eigener Übungswert. Es werden keine echten Verzeichnisse gezählt und keine Dateien bearbeitet.

### Schritt 2: Grenze der Auswahl erkennen

0 ist nicht größer als 0. Deshalb wird der `else`-Zweig ausgewählt. Das `fi` beendet danach die gesamte Auswahl. Die letzte `printf`-Zeile steht außerhalb und folgt nach diesem Entscheidungsblock.

### Schritt 3: Erwartete Ausgabe prüfen

```text
Keine Einträge
Weiter
```

Würde `Weiter` noch vor `fi` in einem Zweig stehen, wäre es nicht mehr zwangsläufig gemeinsame Ausgabe. Eine solche falsche Platzierung kann syntaktisch gültig sein. Der Syntaxcheck allein erkennt deshalb nicht jede falsche Absicht.

## 6. Typische Anwendungsfälle

### Gemeinsamen Ablauf fortsetzen

Mehrere Alternativen führen nach der Auswahl zu demselben nächsten Schritt. Dieser steht einmal hinter `fi`, statt mehrfach in jedem Zweig.

### Verschachtelte Entscheidungen lesen

Eine äußere Entscheidung kann eine innere if-Auswahl enthalten. Passende Einrückung und klar erkennbare Abschlüsse zeigen, welcher Restfall zu welcher Bedingung gehört.

### Syntaxfehler finden

Ein fehlender Abschluss wird manchmal erst am Dateiende gemeldet. Dann alle offenen `if`-, `case`- und Schleifenrahmen prüfen, statt nur die letzte Zeile blind anzupassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Abschluss selbst verändert keine Daten. Die Anordnung kann jedoch entscheiden, ob eine Aktion nur unter einer Bedingung oder immer ausgeführt wird. Ein Schreibbefehl hinter `fi` läuft grundsätzlich nach der Auswahl weiter, sofern kein Zweig vorher den Ablauf beendet hat.

Ein gültiges `fi` beweist außerdem weder, dass die richtige Bedingung geprüft wurde, noch dass frühere Fehler berücksichtigt sind. Der Rückgabestatus einer Auswahl hängt vom ausgeführten Zweig ab; spätere Befehle können ihn überdecken. Fehler- und Erfolgszustände bei Bedarf unmittelbar und bewusst erfassen.

## 8. Häufige Fehler

- **`fi --help` aufgerufen:** Sprachabschluss und ausführbares Programm verwechselt; `help if` verwenden.
- **`done` oder `esac` eingesetzt:** Diese schließen andere Konstruktionen.
- **Ein fi pro elif ergänzt:** Nur echte zusätzliche if-Auswahlen benötigen eigene Abschlüsse.
- **Unerwartetes Dateiende:** Ein erforderlicher Abschluss oder eine Anführungszeichenfolge fehlt.
- **Folgeaktion läuft immer:** Sie liegt hinter dem gesamten Entscheidungsblock.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mehrzeilig schreiben und Beginn und Abschluss auf dieselbe Einrückungsebene setzen. Zunächst feste Daten und reine Ausgaben verwenden. Eine eigene Skriptdatei mit `bash -n DATEI` syntaktisch prüfen und die tatsächlichen Zweige zusätzlich gezielt testen.

**Prüfstand:** Lokale Bash-5.2.21-if-Hilfe gelesen. Vollständiges Beispiel in einer separaten Bash ohne persönliche Startdateien ausgeführt; `Keine Einträge` und `Weiter`, Status 0. Keine Benutzerdateien verändert. Verschachtelung, Umleitungen und andere Shells nicht praktisch geprüft.

## 10. Verwandte Befehle

- `if`, `then`, `elif`, `else`: weitere Bestandteile derselben Auswahl.
- `esac`: Abschluss einer case-Auswahl.
- `done`: Abschluss eines Schleifenkörpers.
- `bash -n`: Grammatik einer eigenen Skriptdatei prüfen.

Ausgangseintrag: Datensatz 84 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
