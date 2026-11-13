---
id: "case"
name: "case"
command: "case"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "case"]
status: "Lokale Primärhilfe und Auswahlbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 74
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# case – Textwerte anhand von Shellmustern auswählen

## 1. Kurzbeschreibung

`case` ist ein Shell-Schlüsselwort für die Auswahl zwischen mehreren Textmustern. Es eignet sich für kleine Menüs, Unterbefehle oder Dateinamenklassen. **Root-Rechte sind für diese Sprachkonstruktion nicht nötig.** Welche Wirkung entsteht, hängt von den Befehlen im gewählten Zweig ab.

`case` ist kein eigenständiges Programm mit einer allgemeinen `--help`-Option. In Bash erklärt `help case` die installierte Syntax.

## 2. Was macht der Befehl?

Ein ausgewertetes Wort wird der Reihe nach mit den angegebenen Mustern verglichen. Beim ersten passenden Zweig werden dessen Befehle ausgeführt. Mit dem gewöhnlichen Abschluss `;;` endet anschließend die gesamte Auswahl.

Die Muster sind Shellmuster, keine regulären Ausdrücke. `*.txt` kann einen Text mit der Endung `.txt` treffen, während ein Stern allein alles auffängt. Die Muster werden nicht automatisch als Dateisuche im aktuellen Ordner verstanden. Primärquelle ist die lokale Bash-5.2.21-Hilfe; ergänzend ist die Struktur im [Bash-Handbuch zu Bedingungen](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html) beschrieben. Der Onlineabruf war hier nicht verfügbar.

## 3. Syntax

```text
case "$wert" in
  MUSTER1) BEFEHLE ;;
  MUSTER2) BEFEHLE ;;
  *) STANDARD_BEFEHLE ;;
esac
```

`in`, die schließende Musterklammer und `esac` gehören zur Grammatik. Das Muster `*` ist ein üblicher Standardfall und sollte zuletzt stehen. Es ist kein zusätzliches Schlüsselwort für Fehlerbehandlung.

## 4. Wichtige Optionen

Die Auswahl hat keine Kommandozeilenschalter. Wichtig sind ihre Sprachbausteine:

| Baustein | Zweck | Hinweis |
| --- | --- | --- |
| `case "$wert" in` | Zu vergleichenden Wert festlegen. | Variable als ein Argument verständlich zitieren. |
| `MUSTER)` | Beginn eines Auswahlzweigs. | Klammer gehört zur Syntax. |
| `;;` | Nach passendem Zweig Auswahl beenden. | Für Einsteiger der klare Normalfall. |
| `*` | Beliebigen Wert auffangen. | Am Anfang würde es spätere Fälle überdecken. |
| `esac` | Auswahl abschließen. | Ist `case` rückwärts geschrieben. |

Mehrere alternative Muster lassen sich mit einem senkrechten Strich trennen. Bash kennt außerdem `;&` für Weiterlaufen im nächsten Zweig und `;;&` für erneute Prüfung folgender Muster. Das sind unterschiedliche, nicht beliebig austauschbare Erweiterungen; für das Grundbeispiel werden sie nicht benötigt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen festen Testwert festlegen

```bash
aktion=status
case "$aktion" in
  start) printf 'Start gewählt\n' ;;
  stop) printf 'Stop gewählt\n' ;;
  status|info) printf 'Nur Statusausgabe\n' ;;
  *) printf 'Unbekannte Auswahl\n' ;;
esac
```

Das Beispiel benutzt ausschließlich eine eigene Variable und `printf`. Die Bezeichnungen `start` und `stop` sind reine Textwerte; es werden keine Dienste gestartet oder beendet.

### Schritt 2: Auswahl verfolgen

`status` passt weder zu `start` noch zu `stop`. Der dritte Zweig besitzt zwei Alternativen, `status` und `info`. Deshalb passt er und gibt `Nur Statusausgabe` aus. `;;` verhindert, dass anschließend auch der Standardzweig läuft.

### Schritt 3: Grenzen verstehen

Ein anderer unbekannter Wert würde den Sternzweig erreichen. Dieser meldet im Beispiel nur Text. Soll ein echtes Skript unbekannte Eingaben als Fehler bewerten, muss es bewusst einen passenden Status zurückgeben. Die bloße Existenz von `*)` macht daraus noch keinen Fehlerstatus.

## 6. Typische Anwendungsfälle

### Kleine Unterbefehle

Ein Skript unterscheidet feste Aktionen wie `anzeigen`, `prüfen` und `hilfe`. Jede Aktion erhält einen klar abgegrenzten Zweig, statt Eingabetext als Shellcode auszuführen.

### Dateinamen einordnen

Muster können Endungen oder bekannte Namensformen erkennen. Eine Endung beweist aber weder den wirklichen Dateityp noch die Vertrauenswürdigkeit des Inhalts.

### Eingaben nachvollziehbar behandeln

Ein abschließender Standardzweig erklärt unbekannte Werte. Dabei gegebenenfalls auch leere Eingaben bewusst berücksichtigen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`case` selbst verändert keine Dateien. Die ausgewählten Befehle können jedoch schreiben, löschen oder Netzwerkaktionen ausführen. Die Risikobewertung muss deshalb den tatsächlichen Zweiginhalt einschließen.

Ein sehr allgemeines frühes Muster kann speziellere spätere Fälle unerreichbar machen. Das ist bei sicherheitsrelevanten Entscheidungen problematisch. Keine Eingaben mit `eval` ausführen, nur weil sie zuvor einen Mustervergleich bestanden haben. Groß-/Kleinschreibung und Bash-Einstellungen können die Auswahl beeinflussen; solche Abhängigkeiten ausdrücklich dokumentieren.

## 8. Häufige Fehler

- **Regex statt Shellmuster verwendet:** Beispielsweise `.*` hat hier nicht automatisch die erwartete Regexbedeutung.
- **`*` zuerst gesetzt:** Alle Werte treffen schon auf den Standardfall.
- **`;;` vergessen:** Syntaxfehler oder unbeabsichtigte Konstruktion.
- **`esac` fehlt:** Die Shell wartet auf den Abschluss oder meldet unerwartetes Dateiende.
- **Unbekannte Aktion wird als Erfolg behandelt:** Status bewusst im Standardzweig bestimmen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit festen Textwerten und reinen Ausgaben beginnen. Muster von spezifisch nach allgemein anordnen. Bei Benutzeraktionen erlaubte Varianten explizit nennen und den Rest verständlich ablehnen.

**Prüfstand:** Lokale Hilfe von Bash 5.2.21 gelesen. Das vollständige Beispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; genau `Nur Statusausgabe` erhalten, Status 0. Keine Dateien, Dienste oder Benutzereinstellungen verändert. Erweiterte Fallabschlüsse, andere Shells und veränderte Pattern-Einstellungen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `if`, `elif`, `else`: Auswahl anhand von Befehlsstatus oder komplexeren Bedingungen.
- `esac`: notwendiger Abschluss einer case-Auswahl.
- `test`, `[` und Bash `[[ ... ]]`: andere Vergleichsformen mit jeweils eigener Syntax.
- `read`: Eingaben lesen, die anschließend bewusst ausgewertet werden können.

Ausgangseintrag: Datensatz 74 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
