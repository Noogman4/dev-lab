---
id: "else"
name: "else"
command: "else"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "else"]
status: "Lokale if-Hilfe und Restfallbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 80
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# else – Den Restfall einer Shellbedingung behandeln

## 1. Kurzbeschreibung

`else` leitet den alternativen Zweig einer Shell-if-Auswahl ein. Dieser Zweig läuft, wenn keine vorherige Bedingung der Auswahl erfolgreich war. **Root-Rechte sind nicht nötig.** `else` ist ein Schlüsselwort, kein eigenständiges ausführbares Programm.

Das Wort bedeutet „andernfalls“. Es prüft nicht selbst eine neue Bedingung. Für eine zusätzliche Bedingung ist `elif` vorgesehen.

## 2. Was macht der Befehl?

Eine Shellbedingung entscheidet anhand eines Befehlsstatus. Status 0 gilt als Erfolg; andere Werte führen zur nächsten Bedingung oder zum Restfall. Der `else`-Zweig kann deshalb sowohl einen erwarteten negativen Test als auch einen echten Prüffehler erreichen.

Das ist ein wichtiger Unterschied: „Datei fehlt“ und „Prüfung konnte nicht durchgeführt werden“ müssen je nach Anwendung getrennt behandelt werden. Eine gewöhnliche if-Auswahl macht diese fachliche Unterscheidung nicht automatisch. Die lokale Primärquelle ist `help if` in Bash 5.2.21. Weiterführend: [Bash-Bedingungen](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html); Onlineabruf hier nicht verfügbar.

## 3. Syntax

```text
if BEDINGUNG; then
  BEFEHLE_BEI_ERFOLG
else
  ALTERNATIVE_BEFEHLE
fi
```

Ein `else` gehört zum passenden offenen `if`. Es kann nach mehreren `elif`-Zweigen stehen, bleibt aber der letzte Restfall. Eine eigenständige Eingabe `else` am Prompt ist daher kein sinnvoller Test seiner Funktion.

## 4. Wichtige Optionen

Für `else` gibt es keine Schalter. Die folgenden Elemente helfen bei der Einordnung:

| Element | Bedeutung | Abgrenzung |
| --- | --- | --- |
| `if BEDINGUNG` | Prüfung starten. | Status entscheidet über Zweige. |
| `then` | Erfolgszweig beginnen. | Gehört zu einer Bedingung. |
| `elif BEDINGUNG` | Weitere Prüfung vor dem Restfall. | Braucht erneut then. |
| `else` | Verbleibenden Fall behandeln. | Keine eigene Bedingung. |
| `fi` | Auswahl schließen. | Muss korrekt zugeordnet sein. |

Soll ein Zweig bewusst keine Aktion ausführen, kann die Shellanweisung `:` als klarer Platzhalter dienen. Ein wirklich leerer Anweisungsteil ist nicht einfach durch Weglassen aller Syntaxelemente ersetzt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen festen Übungsstatus verwenden

```bash
bereit=nein
if [ "$bereit" = ja ]; then
  printf 'Freigegeben\n'
else
  printf 'Nicht freigegeben\n'
fi
```

Die Variable enthält einen eigenen Testtext. Die Ausgabe erteilt keine wirkliche Geräte-, Paket- oder Systemfreigabe. Es wird ausschließlich Text verglichen.

### Schritt 2: Vergleich auswerten

`[` vergleicht den Variableninhalt mit `ja`. Da `nein` nicht gleich `ja` ist, liefert dieser Vergleich Nichterfolg. Der erste Zweig wird übersprungen und der Restfall erreicht.

### Schritt 3: Erwartete Ausgabe lesen

```text
Nicht freigegeben
```

Der Wert könnte später bewusst auf `ja` geändert werden, um den anderen Pfad zu untersuchen. Ein funktionierender Restfall allein belegt aber noch nicht, dass eine echte fachliche Prüfung korrekt implementiert wurde.

## 6. Typische Anwendungsfälle

### Erwartete Alternative anzeigen

Ein Skript kann bei fehlender Auswahl eine verständliche Meldung ausgeben, statt still nichts zu tun. Die Meldung sollte beschreiben, was tatsächlich geprüft wurde.

### Sicheren Standard wählen

Bei einer nur ausdrücklich erlaubten Aktion kann der Restfall die Durchführung unterlassen. Dafür muss die Erfolgsbedingung zuverlässig und eng genug formuliert sein.

### Fehlerpfad verständlich gestalten

Wird ein fehlgeschlagener Arbeitsbefehl geprüft, kann `else` eine Fehlermeldung oder geordneten Abbruch veranlassen. Soll dessen genauer Status erhalten bleiben, muss er rechtzeitig gesichert werden; zusätzliche Ausgabebefehle verändern den zuletzt sichtbaren Status.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Befehle im Restfall besitzen die normalen Benutzerrechte. Ein `else`-Zweig ist nicht automatisch harmlos. Gerade vermeintliche Reparatur- oder Ersatzaktionen können Dateien überschreiben oder ungewollt weitere Aktionen ausführen.

Eine fehlgeschlagene Prüfung darf nicht ohne fachliche Begründung als Erlaubnis gelten. Wenn etwa ein Prüfdienst nicht erreichbar ist, wäre eine automatische Freigabe im Restfall häufig falsch. Das Schlüsselwort bietet keine solche Schutzlogik; sie muss im konkreten Skript bewusst festgelegt werden.

## 8. Häufige Fehler

- **Neue Bedingung hinter else geschrieben:** Für eine zusätzliche Prüfung ist `elif` oder ein bewusst verschachteltes `if` nötig.
- **Falschem if zugeordnet:** Verschachtelung und Abschlüsse sauber einrücken.
- **Negatives Ergebnis und Prüffehler gleichgesetzt:** Beide können Nichterfolg liefern, fachlich aber verschieden sein.
- **Erfolg nach Fehlermeldung gemeldet:** Ein erfolgreiches `printf` kann den vorherigen Status überdecken.
- **`else --help` verwendet:** Hilfe zur vollständigen Konstruktion mit `help if` lesen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit festen eigenen Variablen testen. Für jeden Zweig vorher benennen, welche Situation er wirklich abdeckt. Bei sicherheitsrelevanten Entscheidungen einen unerklärten Prüffehler ausdrücklich behandeln statt daraus eine günstige Annahme abzuleiten.

**Prüfstand:** Lokale Bash-5.2.21-if-Hilfe gelesen. Beispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; `Nicht freigegeben`, Status 0. Keine realen Freigaben, Dateien oder Systemeinstellungen verändert. Erfolgszweig und externe Prüffehler in diesem Eintrag nicht praktisch geprüft.

## 10. Verwandte Befehle

- `if`, `then`, `elif`, `fi`: vollständiger Rahmen der Auswahl.
- `case`: mehrere Textfälle übersichtlich unterscheiden.
- `return`: einen Funktionspfad mit bewusstem Status beenden.
- `exit`: einen gesamten Skriptprozess mit bewusstem Status beenden.

Ausgangseintrag: Datensatz 80 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
