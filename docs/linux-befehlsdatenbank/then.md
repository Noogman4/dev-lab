---
id: "then"
name: "then"
command: "then"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "then"]
status: "Lokale if-Hilfe sowie erfolgreicher und übersprungener Zweig praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 94
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# then – Den Erfolgszweig einer Shellbedingung beginnen

## 1. Kurzbeschreibung

`then` ist ein Shell-Schlüsselwort, das nach einer `if`- oder `elif`-Bedingung den zugehörigen Anweisungsteil beginnt. **Root-Rechte sind nicht nötig.** Es ist kein eigenständiges Linuxprogramm und benötigt keinen erfundenen Aufruf `then --help`.

Der Name bezeichnet den Teil „dann führe dies aus“. Ob dieser Teil betreten wird, entscheidet bereits der Rückgabestatus der vorangehenden Bedingung.

## 2. Was macht der Befehl?

Eine if-Auswahl führt zunächst eine Befehlsliste als Bedingung aus. Wenn deren maßgeblicher Status 0 ist, wird der Abschnitt hinter `then` ausgeführt. Bei Nichterfolg wird dieser Abschnitt übersprungen und gegebenenfalls mit weiteren Bedingungen oder dem Restfall fortgesetzt.

`then` prüft selbst keine zusätzliche Eigenschaft und verändert nicht automatisch den Status eines fehlerhaften Prüfbefehls. Lokale Primärquelle ist `help if` aus Bash 5.2.21. Weiterführend: [Bash-Bedingungskonstrukte](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html). Die hier praktisch geprüften Aussagen beziehen sich auf die installierte Bash.

## 3. Syntax

```text
if BEDINGUNG; then
  BEFEHLE
fi

if BEDINGUNG1; then
  BEFEHLE1
elif BEDINGUNG2; then
  BEFEHLE2
fi
```

Vor `then` muss die Bedingung passend abgeschlossen werden. In einer Zeile ist das gewöhnlich ein Semikolon, auf getrennten Zeilen kann der Zeilenumbruch den Abschluss übernehmen. Das gesamte Konstrukt endet mit `fi`.

## 4. Wichtige Optionen

`then` besitzt keine Kommandozeilenschalter. Relevant sind die benachbarten Bausteine:

| Baustein | Rolle | Hinweis |
| --- | --- | --- |
| `if` | Erste Bedingung starten. | Noch kein Erfolgszweig. |
| `then` | Zugehörige Erfolgsanweisungen beginnen. | Nach jeder elif-Bedingung erneut erforderlich. |
| `elif` | Weitere Bedingung bei bisherigem Nichterfolg. | Nicht gleichbedeutend mit else. |
| `else` | Restfall ohne neue Bedingung. | Benötigt kein zusätzliches then. |
| `fi` | Gesamte Auswahl abschließen. | Nicht mit done verwechseln. |

Eine leere beabsichtigte Aktion lässt sich mit `:` darstellen. Ein Zweig ohne jede erforderliche Anweisung ist nicht dadurch korrekt, dass nur passend eingerückt wird.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Zwei ausdrücklich bekannte Bedingungen verwenden

```bash
if true; then
  printf 'Erfolgszweig\n'
fi
if false; then
  printf 'Nicht erreicht\n'
fi
printf 'Nach der Auswahl\n'
```

Die Builtins `true` und `false` liefern absichtlich Erfolg beziehungsweise Nichterfolg. Sie lesen keine reale Konfiguration. Alle Zweiginhalte sind reine Ausgaben.

### Schritt 2: Erfolgreichen Zweig verfolgen

Die erste Bedingung liefert 0. Deshalb wird die Anweisung hinter ihrem `then` ausgeführt. Das Wort `true` muss dafür nicht als sichtbarer Text ausgegeben werden; entscheidend ist allein der Status.

### Schritt 3: Übersprungenen Zweig erkennen

Die zweite Bedingung liefert Nichterfolg. Ihr `then`-Teil bleibt unbetreten. Nach dem abschließenden `fi` geht der gemeinsame weitere Ablauf trotzdem weiter.

Erwartete Ausgabe:

```text
Erfolgszweig
Nach der Auswahl
```

Die fehlende Zeile `Nicht erreicht` ist gewollt. Das Beispiel zeigt die Zweigwahl, nicht den Erfolg einer externen fachlichen Prüfung.

## 6. Typische Anwendungsfälle

### Arbeit nur bei passender Voraussetzung

Eine konkrete Prüfung entscheidet, ob der Körper ausgeführt werden darf. Die Prüfung muss den wirklich benötigten Zustand abdecken; der bloße Besitz eines then-Zweigs macht sie nicht ausreichend.

### Verzweigungen verständlich gliedern

Die Trennung zwischen Bedingung und zugehörigen Arbeitsanweisungen wird sichtbar. Saubere Einrückung erleichtert die Prüfung, welche Befehle nur unter dieser Bedingung laufen.

### Mehrere Alternativen ordnen

Auch ein `elif` erhält sein eigenes `then`. Dadurch gehört jede Aktionsfolge eindeutig zur jeweils unmittelbar vorherigen Bedingung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Erfolgszweig kann echte Änderungen ausführen. Ist die Bedingung falsch formuliert oder liefert ein Prüfbefehl unerwartet 0, können diese Aktionen trotzdem starten. Vor Schreib-, Lösch- oder Netzwerkoperationen deshalb Bedingung und Zweiginhalt gemeinsam bewerten.

Bereits die Bedingung kann Nebenwirkungen haben. Ein Befehl wird nicht allein dadurch lesend, dass er vor `then` steht. Ein Status 0 zeigt den vom Programm definierten Erfolg und ist kein allgemeiner Sicherheits- oder Integritätsnachweis. Bei zeitabhängigen Dateiprüfungen kann sich der Zustand bis zur Aktion ändern.

## 8. Häufige Fehler

- **Semikolon oder Zeilenumbruch fehlt:** Bedingung und Zweigbeginn sind nicht korrekt getrennt.
- **Else mit then ergänzt:** Der Restfall besitzt keine eigene Bedingung.
- **Gedrucktes Wort ausgewertet:** Die Shell verwendet Status, nicht automatisch den Ausgabetext.
- **Befehl steht hinter fi:** Er gehört nicht mehr zum bedingten Zweig.
- **Abschluss vergessen:** Die Shell meldet möglicherweise erst am Dateiende den offenen Rahmen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst mit `true`, `false` und `printf` den Ablauf verstehen. Danach eigene kleine Prüfungen ergänzen und jeden Zweig testen. Die Frage „Was passiert bei einem Prüffehler?“ ausdrücklich beantworten, bevor ein echter Arbeitsbefehl eingesetzt wird.

**Prüfstand:** Lokale Bash-5.2.21-if-Hilfe gelesen. Beide Entscheidungen in einer getrennten Bash ohne persönliche Startdateien ausgeführt; erwartete zwei Zeilen, Status 0. Keine Benutzerdateien oder Systemeinstellungen verändert. Externe Prüfprogramme, komplexe Bedingungen und Dateisystemrennen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `if`, `elif`, `else`, `fi`: weitere Teile der Auswahl.
- `true`, `false`: feste Teststatus erzeugen.
- `do`: Körper einer Schleife beginnen, anderer Kontext.
- `test`, `[`: konkrete Eigenschaften mit eigener Argumentgrammatik prüfen.

Ausgangseintrag: Datensatz 94 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
