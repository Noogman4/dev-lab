---
id: "zless"
name: "zless"
command: "zless"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive & kompression", "zless"]
status: "Ausgearbeitet; nichtinteraktive Ausgabe mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 27
reviewed_at: "2026-11-13"
locally_checked_version: "zless aus GNU gzip 1.12; less 590"
---

# zless – Komprimierte Texte seitenweise lesen

## 1. Kurzbeschreibung

`zless` öffnet unterstützte komprimierte oder normale Textdateien im Terminal-Pager `less`. Ein Pager zeigt lange Texte seitenweise und bietet Navigation sowie Suche.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Die gewöhnliche Anzeige ersetzt die Eingaben nicht durch entpackte Dateien. Der Pager kann jedoch Verlauf speichern und besitzt zusätzliche Funktionen über bloßes Lesen hinaus.

## 2. Was macht der Befehl?

Der lokale `zless`-Wrapper richtet für den gestarteten `less`-Prozess einen Eingabefilter über `LESSOPEN` ein. Dieser nutzt GNU gzip zur vorbereitenden Ausgabe des Inhalts. Normale unkomprimierte Texte können ebenfalls angezeigt werden. Eine lesbare Anzeige ist deshalb kein Beweis für ein gültiges gzip-Format.

Navigation und Suche kommen von `less`, nicht vom Kompressor. Die Tastenkürzel gelten innerhalb des laufenden Pagers; sie werden nicht als neue Shell-Kommandos eingegeben.

Grundlagen: [Distributions-Manpage für zless](https://manpages.debian.org/trixie/gzip/zless.1.en.html), [less-Manpage](https://manpages.debian.org/trixie/less/less.1.en.html) und das lokal gelesene Wrapper-Skript aus GNU gzip 1.12. Versionsabhängige Filterdetails wurden nicht als allgemeine Eigenschaften aller Systeme übernommen.

## 3. Syntax

```text
zless [LESS_OPTIONEN] DATEI ...
```

```bash
zless "probe.log.gz"
zless -N -S "probe.log.gz"
```

Die zweite Zeile zeigt Zeilennummern und vermeidet den normalen Umbruch langer Zeilen. Zum Anzeigen einer eigenen Datei einen Dateinamen ausdrücklich angeben.

**Prüfpunkt:** Die Verarbeitung komprimierter stdin-Daten ist zwischen Handbuchfassungen und Wrapper-Versionen unterschiedlich beschrieben. Für eine nachvollziehbare Pipeline den ausdrücklichen Ablauf `gzip -dc DATEI | less` erwägen und dessen Fehlerbehandlung gesondert planen. Die Beispiele hier verwenden Dateipfade.

## 4. Wichtige Optionen

| Option oder Taste | Bedeutung | Hinweis |
| --- | --- | --- |
| `-N` | Zeilennummern anzeigen. | Bezieht sich auf den angezeigten entpackten Text. |
| `-S` | Lange Zeilen abschneiden statt umbrechen. | Horizontal navigieren, um den Rest zu sehen. |
| `-i` | Suche abhängig von Musterschreibweise ohne Groß-/Kleinschreibungsunterscheidung. | Großbuchstaben im Muster können die Unterscheidung aktivieren. |
| `-I` | Such-Groß-/Kleinschreibung immer ignorieren. | Andere Wirkung als das kleine `-i`. |
| `Leertaste` | Eine Seite vorwärts. | Innerhalb des Pagers. |
| `b` | Eine Seite zurück. | Bereits gelesene Bereiche ansehen. |
| `g`, `G` | Anfang beziehungsweise Ende. | Sprung ans Ende kann viel Verarbeitung benötigen. |
| `/MUSTER`, Enter | Vorwärts suchen. | Regulärer Ausdruck; nicht stets wörtliche Zeichenfolge. |
| `n`, `N` | Nächster beziehungsweise vorheriger Suchtreffer. | Nach einer Suche. |
| `h` | Tastenhilfe. | Innerhalb von less. |
| `q` | Pager verlassen. | Kein Löschen der Eingabedatei. |

`zless --version` zeigt den Wrapper-Stand; `less --version` den Pager. Deren Versionen nicht gleichsetzen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Neue Übung vorbereiten

```bash
zless --version
less --version
uebung="$(mktemp -d -t netmon-zless-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Bekannte Textdaten erstellen

```bash
printf '%s\n' 'Info: Start' 'FEHLER: Probe' 'Info: Ende' > "probe.log"
gzip -k "probe.log"
```

Das ist eine eigene kurze Datei. Ein langer echter Systemlog ist zum Erlernen der Tasten nicht erforderlich.

### Schritt 3: Datei im Pager öffnen

```bash
LESSHISTFILE=- zless -N "probe.log.gz"
```

Die vorgestellte Umgebungszuweisung gilt nur für diesen Aufruf. `LESSHISTFILE=-` deaktiviert bei less die History-Datei. Es ist keine allgemeine Sandbox und deaktiviert nicht jede zusätzliche Pager-Funktion.

### Schritt 4: Suchen und schließen

Im Pager `/FEHLER` eingeben und Enter drücken. Mit `n` zur nächsten passenden Stelle suchen. Mit `q` zurück zur Shell wechseln. Die Quelle soll weiterhin vorhanden sein.

### Schritt 5: Format bei Bedarf getrennt prüfen

```bash
gzip -t "probe.log.gz"
```

Ein separater Datenprüfungslauf beantwortet eine andere Frage als „Kann ich Text im Pager lesen?“.

## 6. Typische Anwendungsfälle

**Archivierte eigene Protokolle lesen:** Seitenweise navigieren, ohne eine dauerhafte entpackte Kopie im Projekt abzulegen.

**Einzelne Meldung im Kontext betrachten:** Über `/MUSTER` suchen und benachbarte Zeilen prüfen. Für maschinelle Trefferlisten ist `zgrep` meist die passendere Oberfläche.

**Lange Textzeilen untersuchen:** Mit `-S` horizontal statt umgebrochen lesen. Das ist etwa bei breiten Tabellen hilfreich, verändert aber nicht deren Daten.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Pager besitzt zusätzliche Funktionen

`less` kann je nach Konfiguration externe Befehle aufrufen, Editoren starten oder Ausgaben speichern. Solche Aktionen gehen über Lesen hinaus. Keine unbekannten Befehle aus angezeigtem Text als Pager- oder Shell-Eingabe übernehmen.

### Verlauf und vertrauliche Suchtexte

Ein Pager kann Suchtexte und Positionen speichern. `LESSHISTFILE=-` verhindert die normale less-History-Datei für diesen Prozess. Vertrauliche Inhalte können trotzdem auf dem Bildschirm, im Terminalpuffer oder in einer bewusst gespeicherten Ausgabe stehen.

### Sichere Modi und Eingabefilter

`LESSSECURE` kann Funktionen einschließlich Eingabefiltern deaktivieren. Dadurch kann die von zless benötigte Dekompression ausfallen. Eine Meldung über Binärdaten ist dann nicht automatisch ein beschädigtes Archiv. Einen geschützten Modus nicht blind abschalten; erst die eingesetzte Version und den gewünschten Anzeigepfad klären.

### Große oder ungeeignete Inhalte

Sprünge ans Ende und Rückwärtssuche können viel Dekompressionsarbeit verlangen. Binärdaten und fremde Steuerzeichen nicht als normalen Text behandeln. Schutzoptionen wie ungefilterte Rohanzeige nicht ohne konkreten Bedarf aktivieren.

**Root-Rechte sind für die Beispielanzeige unnötig.** Der lesende Grundaufruf ändert nicht die Rechte möglicher Zusatzfunktionen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| less fehlt | Pager nicht verfügbar. | Abhängigkeit und lokalen Paketstand prüfen. |
| Binärdatei statt Text | Inhalt binär oder Filter deaktiviert. | Format und Filterkonfiguration getrennt prüfen. |
| Suche findet nichts | Regex, Schreibweise oder falscher Textbereich. | Mit bekanntem einfachen Muster beginnen. |
| Zeilen wirken abgeschnitten | `-S` aktiv. | Horizontal bewegen oder Umbruch wieder wählen. |
| Anzeige bleibt scheinbar offen | Pager wartet auf Eingabe. | `q` zum Beenden verwenden. |
| Komprimierte Pipeline scheitert | Versionsabhängige stdin-Behandlung. | Explizite Dekompressionsstufe planen. |

Pager-Ende und vollständige Kompressionsprüfung sind unterschiedliche Ereignisse. Bei Zweifeln den Datenstrom gesondert testen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Eine kleine eigene Textdatei und ausdrücklichen Dateipfad verwenden.
2. Zuerst `q`, Leertaste, `/` und `n` lernen.
3. Mit `LESSHISTFILE=-` bei Bedarf den Suchverlauf vermeiden.
4. Rohanzeige, Editorstart und Shell-Funktionen nicht für normales Lesen nutzen.
5. Filterprobleme und beschädigte Daten getrennt untersuchen.
6. Für Integrität einen eigenen gzip-Test durchführen.

**Prüfstand:** Mit zless aus GNU gzip 1.12 und less 590 wurde eine eigene gzip-Datei über eine nichtinteraktive stdout-Verbindung ausgegeben. Der bekannte Inhalt erschien und die Quelle blieb bytegleich; History war im Test deaktiviert. Ein Versuch mit `LESSSECURE=1` unterband den benötigten Eingabefilter und wurde nicht als erfolgreicher Dekompressionstest gewertet. Interaktive Tasten, Suche, Terminaldarstellung und History-Speicherung wurden nicht praktisch geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `less` | Eigentlicher Pager. |
| `zmore` | Andere seitenweise Anzeigeoberfläche. |
| `zcat` | Gibt den entpackten Strom ohne Pager aus. |
| `zgrep` | Liefert ausgewählte Suchzeilen. |
| `gzip -t` | Separate Datenprüfung. |

Ausgangseintrag: Datensatz 27 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
