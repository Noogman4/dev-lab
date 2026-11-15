# Arbeitsauftrag für die ersten zehn Glossardokumentationen

Erstelle die ersten zehn ausführlichen Glossardokumentationen für NetMons
Linux-Tab. Schreibe verständliches Deutsch für Einsteiger und liefere zugleich
fachlich belastbare Erklärungen. Die Dokumente werden anschließend von Codi und
Sven geprüft und in den vorhandenen Dokumentenreader eingebunden.

**Dieser Erstauftrag endet nach zehn Einträgen. Bearbeite Eintrag 11 bis 302 erst
nach einer ausdrücklichen Fortsetzungsfreigabe nach unserer Pilotprüfung.**

## Repository und Arbeitsbranch

- Verwende das bereitgestellte NetMon-Repository und einen eigenen Branch:
  `codex/linux-glossar-pilot-001-010`. Falls die Browser-Umgebung einen festen
  Task-Branch vorgibt, verwende diesen und nenne seinen tatsächlichen Namen.
- Ausgangspunkt ist der aktuelle bereitgestellte Hauptbranch. Halte den
  Ausgangscommit fest. Arbeite bei fremden Änderungen in einer isolierten
  Arbeitskopie; übernimm oder verwerfe sie nicht.
- Ändere ausschließlich Dateien unter `docs/linux-glossar/`.
- Die Glossarquelle, die 713 Befehlsdokumentationen samt ihrem Index sowie
  Anwendungscode, Tests, Paketierung und installierte Version bleiben unverändert.
- Keine Unteragenten oder parallele Bearbeitung. Bearbeite jeden Eintrag einzeln:
  Quellen prüfen, schreiben, validieren, Fortschritt festhalten, dann den nächsten.

## Verbindliche Quelle und Reihenfolge

Die Quelle ist `tools/it_lexikon_linux_hilfe.json`, Liste `entries` in ihrer
vorhandenen Reihenfolge. Sie enthält **302 unterschiedliche IDs und Begriffe**.
Der erwartete SHA-256 der unveränderten Quelldatei lautet:

```text
b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24
```

Prüfe vor Beginn Existenz, Prüfsumme, Anzahl und eindeutige IDs. Bei Abweichung
melde den Unterschied und halte an; ändere weder die Quelle noch den erwarteten
Hash auf eigene Faust. Ist die Datei in der Browser-Arbeitskopie nicht vorhanden,
melde den fehlenden Pfad. Rekonstruiere den Katalog nicht aus Vermutungen.

Übernimm `id`, `term`, `short`, `example`, `tags` und `related` als Ausgangsdaten.
Prüfe die fachlichen Aussagen: Eine unzutreffende Kurzbeschreibung oder ein
ungeeignetes Beispiel darf im ausführlichen Text korrigiert werden. Halte eine
solche Korrektur im Fortschrittsbericht mit Begründung und Quelle fest; der
Originaldatensatz bleibt unverändert.

| Datensatznummer | Feste ID | Begriff | Zieldatei |
| --- | --- | --- | --- |
| 1 | it_0001 | Algorithmus | docs/linux-glossar/it_0001.md |
| 2 | it_0002 | Anweisung | docs/linux-glossar/it_0002.md |
| 3 | it_0003 | Ausdruck | docs/linux-glossar/it_0003.md |
| 4 | it_0004 | Variable | docs/linux-glossar/it_0004.md |
| 5 | it_0005 | Konstante | docs/linux-glossar/it_0005.md |
| 6 | it_0006 | Datentyp | docs/linux-glossar/it_0006.md |
| 7 | it_0007 | String | docs/linux-glossar/it_0007.md |
| 8 | it_0008 | Integer | docs/linux-glossar/it_0008.md |
| 9 | it_0009 | Float | docs/linux-glossar/it_0009.md |
| 10 | it_0010 | Boolean | docs/linux-glossar/it_0010.md |

## Ablage und Lieferumfang

Erstelle genau diese zehn ausgearbeiteten Markdown-Dateien sowie:

- `docs/linux-glossar/index.json`: Zuordnung, unveränderte Ausgangseinträge,
  Dokumentprüfsummen und genaue Quellenadressen für die spätere Reader-Anbindung.
- `docs/linux-glossar/FORTSCHRITT.md`: tatsächlicher Fortschritt pro Eintrag,
  Quellenprüfung, Validierung, Korrekturen und offene Punkte.

Dieser Prompt unter `docs/linux-glossar/PROMPT.md` ist die Arbeitsgrundlage.
Wenn er im Browser-Checkout fehlt, darfst du den vollständig übergebenen Auftrag
dort ablegen. Erstelle keine leeren Dokumente für die übrigen 292 Einträge.
Überschreibe keine bereits vorhandene Ausarbeitung ohne Klärung ihres Standes.

## Schreibweise und fachliche Qualität

- Erkläre Fachwörter beim ersten Auftreten. Verwende kurze Absätze und konkrete
  Beispiele. Etwa 500 bis 900 Wörter pro Begriff sind ein Richtwert; Länge folgt
  dem Erklärbedarf. Vermeide Fülltext und gleichförmige Standardabsätze.
- Ein Alltagsvergleich dient als Einstieg. Erkläre anschließend auch seine
  Grenzen, damit keine falsche technische Vorstellung entsteht.
- Unterscheide allgemeine Konzepte von Eigenschaften einer bestimmten Sprache
  oder eines Programms. Beispielsweise ist eine Python-Konvention nicht
  automatisch eine Regel aller Programmiersprachen.
- Nenne passende Linux-Anwendungen, ohne künstlich aus jedem Begriff einen
  Terminalbefehl zu machen. Auch ein kleines Gedankenbeispiel kann genügen.
- Prüfe zentrale Aussagen anhand offizieller Sprach-, Projekt-, Standard- oder
  Distributionsdokumentation. Verwende konkrete HTTPS-Quellenlinks direkt bei
  den zugehörigen Aussagen. Zwei geeignete Primärquellen pro Begriff sind das
  Ziel; eine begründete einzelne Primärquelle ist besser als ein unpassender
  zweiter Link. Sammle keine Quellen, die die Aussagen nicht belegen.
- Erfinde keine Quellen oder Testergebnisse. Kennzeichne verbleibende fachliche
  Unsicherheit und relevante Versionsabhängigkeiten genau an der betreffenden
  Stelle. Vermeide kopierte längere Passagen aus fremden Dokumentationen.
- Verwandte Begriffe erhalten einen kurzen Hinweis, wie sie zusammenhängen.
  Ergänzte Verweise müssen zu vorhandenen Glossareinträgen passen. Die originalen
  `related`-Werte im Ausgangsdatensatz werden dabei nicht umgeschrieben.

## Feste Struktur jeder Glossardatei

Verwende eine Hauptüberschrift mit dem originalen Begriff und genau diese zehn
nummerierten Hauptabschnitte als Überschriften der Ebene 2:

1. Kurzbeschreibung
2. Was bedeutet der Begriff?
3. Einfacher Vergleich aus dem Alltag
4. Wie funktioniert das?
5. Wo begegnet mir das unter Linux?
6. Konkretes Beispiel Schritt für Schritt
7. Abgrenzung zu ähnlichen Begriffen
8. Häufige Missverständnisse
9. Praktische Hinweise und gegebenenfalls Risiken
10. Verwandte Begriffe

Unterüberschriften sind möglich. Quellenlinks stehen in den jeweiligen
Abschnitten; ein zusätzlicher elfter Hauptabschnitt ist nicht erforderlich.
Die bisherige Befehlsvorlage `docs/linux-befehlsdatenbank/7z.md` zeigt die
gewünschte Sorgfalt, ihr befehlsspezifischer Aufbau wird nicht übernommen.

## Dokumentkopf und Reader-Format

Jede Datei beginnt mit `---`, einer Metadatenzeile pro Feld und erneut `---`.
Verwende JSON-kompatible Werte: Zeichenketten in doppelten Anführungszeichen,
Arrays als JSON-Arrays und Zahlen ohne Anführungszeichen. Kein freies YAML.

Beispiel für den Kopf von `it_0001.md`:

```text
---
id: "it_0001"
entry_type: "glossary"
name: "Algorithmus"
category: "Grundlagen"
language: "de"
tags: ["grundlagen"]
related: []
source_catalog: "tools/it_lexikon_linux_hilfe.json"
source_record: 1
status: "review_pending"
---
```

- `name` entspricht exakt `term`, `id` der Originalkennung, `source_record` der
  einsbasierten Position in `entries`. `tags` und `related` entsprechen der Quelle.
- Für `category` verwende eine vorhandene Quellkategorie. Fehlt sie, nimm das
  erste Tag mit Python-`str.title()`; ohne Tag lautet sie `Glossary`. Das entspricht
  der bisherigen Glossar-Zuordnung des Linux-Tabs.
- Erfinde für einen Begriff keine `command`-, `root_required`- oder
  `risk_level`-Angabe. Beschreibe Risiken konkreter Beispiele im Text.
- Dieser Glossarkopf ist die vereinbarte Schnittstelle für die anschließende
  Reader-Erweiterung. Der bisherige Befehlskatalog-Loader erwartet Befehlsfelder
  und unterstützt diese Glossardateien noch nicht. Ändere oder umgehe ihn nicht,
  um die Dokumente während dieses Schreibauftrags freizuschalten.
- Nutze UTF-8, normale Absätze, Überschriften, einfache Listen, kleine Tabellen
  sowie dreifache Backticks für Code. Setze bei Code die Sprache, etwa `python`
  oder `text`. Codeblöcke müssen vollständig geschlossen sein.
- Keine HTML-Inhalte, Bilder, Skripteinbindungen, Includes, verschachtelten
  Codeblöcke oder extern nachgeladenen Inhalte. Keine Leerzeilen innerhalb einer
  Tabelle; höchstens acht Spalten und insgesamt 1000 Tabellenzellen je Dokument.
- Höchstens 256 KiB UTF-8, 5000 Zeilen und 500 Darstellungsblöcke je Dokument;
  ein Codeblock höchstens 32768 Zeichen. Bleibe mit den kurzen Glossartexten
  deutlich darunter. Verwende keine absoluten lokalen Dateipfade für die Zuordnung.

## Aufbau des Glossarindex

Schreibe ein JSON-Objekt mit diesen Feldern:

- `schema_version`: Zahl `1`.
- `kind`: Zeichenkette `glossary`.
- `source_catalog`: `tools/it_lexikon_linux_hilfe.json`.
- `source_sha256`: die oben vorgegebene tatsächliche Quelldatei-Prüfsumme.
- `total_records`: Zahl `302`, also die Gesamtzahl der Quelle.
- `documented_records`: Zahl der tatsächlich ausgearbeiteten und strukturell
  geprüften Dokumente; am Ende dieses Piloten `10`.
- `records`: genau die ausgearbeiteten Datensätze in Quellreihenfolge. Jeder
  enthält `source_record`, `id`, `term`, `category`, `document`, `sha256`, `source`,
  `source_urls` und `status`.
- Pro Datensatz ist `document` ausschließlich der Dateiname, etwa `it_0001.md`.
  `sha256` ist der tatsächliche SHA-256 der endgültigen Dokumentbytes. `source`
  ist der vollständige unveränderte Originaleintrag aus `entries`.
  `source_urls` enthält die konkreten im Dokument verwendeten HTTPS-Quellen;
  `status` bleibt `review_pending`, bis unsere spätere Prüfung erfolgt ist.
- Die oberste Liste `source_urls` enthält die sortierte, duplikatfreie Vereinigung
  dieser Quellenadressen. Keine pauschale Freigabe ganzer Websites.

## Prüfung und Fortschritt pro Eintrag

Prüfe nach jeder Datei Kennung, Begriff, Datensatzposition, Dateiname und
Quellfelder gegen den Originaleintrag. Prüfe den JSON-kompatiblen Dokumentkopf,
alle zehn Hauptüberschriften, geschlossene Codeblöcke, Größenbegrenzungen und
die tatsächliche Dokumentprüfsumme. Prüfe, dass die genannten Quellen die
zentralen Aussagen stützen und die Links zu den beschriebenen Inhalten führen.

Ein vorhandener Befehlskatalog-Test ist kein Nachweis der Glossar-Anbindung.
Falls du den bestehenden Markdown-Parser zur Prüfung der Textblöcke wiederverwendest,
darfst du nur im Prüfprozess einen temporären kompatiblen Kopf erzeugen. Speichere
keine erfundenen Befehlsfelder in den eigentlichen Glossardateien. Alternativ prüfe
die beschriebene Struktur mit einem kleinen temporären Python-Prüfer.

Praktische Beispiele darfst du ausschließlich mit kleinen, selbst angelegten
Testdaten in einem temporären Verzeichnis prüfen. Keine privilegierten Befehle,
Paketinstallationen, Geräte-, Konto-, Dienst- oder Netzwerkkonfigurationsänderungen.
Normale HTTPS-Recherche in Dokumentationsquellen ist erlaubt. Ein Beispiel, das
du nicht praktisch ausgeführt hast, wird entsprechend als nicht ausgeführt
dokumentiert; eine Syntaxprüfung ist keine praktische Funktionsprüfung.

Aktualisiere nach jedem Eintrag `index.json` und `FORTSCHRITT.md`. Der Bericht
enthält pro Eintrag Quellen, tatsächlich durchgeführte Prüfungen und Ergebnisse,
nicht ausgeführte Beispiele, Korrekturen gegenüber der Quelle sowie offene Punkte.
Die Zusammenfassung unterscheidet: ausgearbeitet, strukturell geprüft,
inhaltliche Zweitprüfung ausstehend und Reader-Anbindung ausstehend.

## Abschluss der Zehnerprobe

1. Prüfe den vollständigen Diff: ausschließlich `docs/linux-glossar/`.
2. Prüfe, dass die Quelldatei weiterhin die ursprüngliche Prüfsumme hat und
   genau zehn Glossardokumentationen vorhanden sind.
3. Committe die Pilotdateien auf deinem Arbeitsbranch. Nenne Branch,
   Ausgangscommit, Ergebniscommit und die ausgeführten Prüfungen. Stelle über den
   üblichen Browser-Codex-Workflow einen prüfbaren Diff beziehungsweise einen
   Entwurfs-PR bereit. Kein Merge in den Hauptbranch und kein Force-Push.
4. Melde den Stand **10 von 302 ausgearbeitet; unsere inhaltliche Prüfung und
   Reader-Anbindung stehen aus**. Stoppe hier. Beginne `it_0011` nicht automatisch.

Wir prüfen dann die zehn Texte auf Verständlichkeit, fachliche Qualität und
Quellen. Lokal prüfen wir außerdem die tatsächliche Reader-Zuordnung, Darstellung,
Suche, Code-Kopieren und getrennten Lesestatus. Erst danach erhältst du den
Fortsetzungsauftrag für Eintrag 11 bis 302 im bestätigten Format.

Bei einem ausdrücklichen Stopp halte sofort an. Der pro Eintrag gespeicherte
Fortschritt bleibt der Ausgangspunkt für eine spätere Fortsetzung.
