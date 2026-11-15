# Fortschritt der Glossar-Zehnerprobe

Branch: `codex/linux-glossar-pilot-001-010`

Ausgangscommit: `ffa87cb3c21383dbf4a24b12fcc2367133f0523d` (bereitgestellter Branch `work`, identischer Ausgangsstand zur vorher bereitgestellten Hauptbranch-Revision).

Quelle: `tools/it_lexikon_linux_hilfe.json`, SHA-256 `b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24`; 302 eindeutige IDs und Begriffe. Der übergebene JSON-Anhang ist byteidentisch. Keine vorhandenen Ausarbeitungen oder fremden Arbeitsänderungen vorgefunden.

Jeder Eintrag wurde einzeln recherchiert, geschrieben, geprüft und hier sowie im Index festgehalten, bevor der nächste begann. Quellenabruf: 15.11.2026, HTTPS mit unveränderter TLS-Prüfung; verlinkte Abschnittsanker auf Existenz geprüft. Quellen- und Inhaltsprüfung sind die Erstprüfung des Autors, keine unabhängige Zweitprüfung.

Prüfverfahren pro Datei: JSON-Werte des vollständigen Kopfs mit der Originalquelle verglichen; ID, Begriff, Reihenfolge und Dateiname geprüft; genau zehn vorgegebene Hauptabschnitte; UTF-8, geschlossene Codeblöcke, Größen-/Block-/Tabellenlimits und lokale Verweise geprüft. Der vorhandene Markdown-Parser erhielt ausschließlich im Arbeitsspeicher einen temporären Befehlskopf für die Prüfung der Textblöcke. Die gespeicherten Glossarköpfe enthalten keine Befehlsfelder. Das prüft keine Reader-Anbindung. Jedes Python-Beispiel wurde als eigenes Skript mit System-Python 3.13.5 in einem neu angelegten temporären Verzeichnis ausgeführt; Assertions und vollständige erwartete Standardausgabe geprüft. Keine Systemkonfiguration verändert.

## 1. Algorithmus – it_0001

Ausgearbeitet und strukturell geprüft: 671 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5549 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/howto/sorting.html#key-functions
- https://docs.python.org/3.13/tutorial/controlflow.html#for-statements

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Keine fachliche Korrektur nötig. Die Schritt-für-Schritt-Definition wurde um Voraussetzungen, eindeutige Schritte und den betrachteten endlichen Berechnungsfall ergänzt; Schleifen und Sortierschlüssel sind durch die beiden verlinkten Python-Primärquellen belegt.

SHA-256: `d28ea745a0c28260dfbe2de2c64f18791283f4bca4dcddadfb0fe9a6130c2edd`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 2. Anweisung – it_0002

Ausgearbeitet und strukturell geprüft: 664 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5564 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/compound_stmts.html#the-if-statement
- https://docs.python.org/3.13/reference/simple_stmts.html#expression-statements

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Ein einzelner Befehl“ zu einfachen und zusammengesetzten Anweisungen präzisiert; print-Aufruf als Ausdruck innerhalb einer Ausdrucksanweisung erklärt. Belege: Python-Sprachreferenz, expression-statements und the-if-statement. Der Originaleintrag bleibt unverändert.

SHA-256: `11029de1370d34b61b1f9f39e7821410cff48b62d40a81319c68fbafd062d69d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 3. Ausdruck – it_0003

Ausgearbeitet und strukturell geprüft: 712 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5767 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#boolean-operations
- https://docs.python.org/3.13/reference/expressions.html#evaluation-order
- https://docs.python.org/3.13/reference/simple_stmts.html#expression-statements

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Keine Korrektur der Kurzbeschreibung oder des Zahlenbeispiels nötig. Ergänzt wurden Fehlerfälle, Seiteneffekte, Operatorrangfolge und Kurzschlussauswertung gemäß den verlinkten Python-Referenzabschnitten.

SHA-256: `c68e63e41e9b9070fae98b418f79aadc71d515a037a80532605a93891d62cffb`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 4. Variable – it_0004

Ausgearbeitet und strukturell geprüft: 685 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5682 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types
- https://docs.python.org/3.13/reference/executionmodel.html#binding-of-names

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Speicherplatzbild und „speichert Text“ für Python zu Name-Objekt-Bindungen präzisiert. Neuzuweisung von Namen von Mutation gemeinsamer Objekte getrennt. Belege: Python executionmodel#binding-of-names und datamodel#objects-values-and-types.

SHA-256: `27efd85b5aa299b248d90230937bced022329813eeaed2e207a8c5f3a5f655dc`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 5. Konstante – it_0005

Ausgearbeitet und strukturell geprüft: 707 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6030 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/typing.html#typing.Final
- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types
- https://peps.python.org/pep-0008/#constants

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Quellbeispiel bleibt passend. Ergänzt: Großschreibung ist laut PEP 8 eine Konvention, kein Laufzeitschutz; typing.Final unterstützt statische Prüfer, erzwingt aber laut Python-Dokumentation keine Laufzeitprüfung. Bindungs- und Objektunveränderlichkeit wurden getrennt.

SHA-256: `524bf31f6d0f635a14404337abe7016224e53951de31fe4e0fce8df510bbd9a7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 6. Datentyp – it_0006

Ausgearbeitet und strukturell geprüft: 718 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5766 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#int
- https://docs.python.org/3.13/library/functions.html#type
- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Keine fachliche Korrektur nötig. Kategorie von Werten um erlaubte Operationen, Objekt-Typen, dynamische Namensbindung und ausdrückliche Umwandlung ergänzt; Belege stehen im Python-Datenmodell und bei type/int.

SHA-256: `ecc23989df073cd0b34fe1de0819d8ae0c641658b081f394f75e1945750ee02d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 7. String – it_0007

Ausgearbeitet und strukturell geprüft: 719 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5802 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/howto/unicode.html#encodings
- https://docs.python.org/3.13/library/stdtypes.html#text-sequence-type-str

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Keine Korrektur des NetMon-Textbeispiels nötig. String für Python 3 als Unicode-Codepunktfolge präzisiert; sichtbare Zeichen, Codepunkte und kodierte Bytes unterschieden. Belege: str-Referenz und Unicode HOWTO; UTF-8-Rundlauf praktisch geprüft.

SHA-256: `07d6398968523cc6628c8aed2f47fcacace87353f3da911f3b0f18cbb48759a7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 8. Integer – it_0008

Ausgearbeitet und strukturell geprüft: 701 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5608 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#int
- https://docs.python.org/3.13/library/stdtypes.html#numeric-types-int-float-complex

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Keine Korrektur von Definition oder Beispiel nötig. Ergänzt wurden negative Zahlen, Python-spezifische Genauigkeit und Ressourcengrenzen sowie der Unterschied zwischen // und int bei negativen Werten; belegt durch numerische Typen und int-Referenz.

SHA-256: `f6b8b403178049fce12920e82264f70891326e806c0a432ed8c47b5e1d6dbe78`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 9. Float – it_0009

Ausgearbeitet und strukturell geprüft: 704 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6022 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/math.html#math.isclose
- https://docs.python.org/3.13/library/stdtypes.html#numeric-types-int-float-complex
- https://docs.python.org/3.13/tutorial/floatingpoint.html#representation-error

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Zahl mit Nachkommastellen“ durch Gleitkommazahl mit begrenzter Genauigkeit ersetzt: Auch ganzzahlige Werte können Floats sein, viele Dezimalbrüche sind binär nicht exakt darstellbar. Belege: Python-Numerikreferenz und floatingpoint#representation-error; Plattformannahme und Toleranz ausdrücklich dokumentiert und praktisch geprüft.

SHA-256: `61786aa52138d75e6576987add8213a34487fdfb6b3d4729964291dc05adb390`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 10. Boolean – it_0010

Ausgearbeitet und strukturell geprüft: 743 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6184 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#boolean-type-bool
- https://docs.python.org/3.13/library/stdtypes.html#truth-value-testing
- https://docs.python.org/3.13/reference/expressions.html#boolean-operations

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Allgemeine Schreibweisen von Python-True/False getrennt. Das passende Quellbeispiel als reine Namensbindung, ausdrücklich ohne tatsächliche Rechteprüfung, erläutert. Ergänzt: bool("False") ist wahr; and/or können Operanden liefern. Belege: bool-, truth-value-testing- und boolean-operations-Referenz.

SHA-256: `d480572ac7951f88f18590d2e987fdab69b90b82f738c927384b5b4c0fad6674`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Abschluss der Zehnerprobe

**10 von 302 ausgearbeitet; unsere inhaltliche Prüfung und Reader-Anbindung stehen aus.**

- Ausgearbeitet: genau `it_0001.md` bis `it_0010.md`, jeweils Status `review_pending`.
- Strukturell geprüft: alle zehn Dokumente, Quellfelder, Quellreihenfolge, UTF-8-Grenzen, Markdown-Textblöcke, interne Verweise und die endgültigen Dokumentprüfsummen. `index.json` enthält vollständige unveränderte Ausgangseinträge und die sortierte, duplikatfreie Quellenvereinigung.
- Praktisch geprüft: alle zehn vollständigen Python-Beispiele, jeweils in einem eigenen temporären Verzeichnis. Assertions, Exitcode und dokumentierte Ausgabe stimmen überein; der abschließende Gesamtlauf wiederholte diese Prüfung für alle zehn erfolgreich.
- Quellen geprüft: alle im Index verzeichneten konkreten HTTPS-Adressen lieferten HTTP 200; gegebenenfalls erfolgte Weiterleitungen und Abschnittsanker wurden beim Abruf berücksichtigt. Die zentrale Aussageprüfung erfolgte beim Verfassen jedes Eintrags anhand der offiziellen Texte. Die geplante unabhängige inhaltliche Zweitprüfung durch Codi und Sven ist nicht erfolgt.
- Reader-Anbindung ausstehend: kein Glossar-Loader, keine Freischaltung, keine Prüfung tatsächlicher Reader-Zuordnung, Darstellung, Suche, Code-Kopieren oder getrennten Lesestatus. Der temporäre Aufruf des vorhandenen Markdown-Parsers ist ausdrücklich kein Nachweis dieser Fähigkeiten.
- Keine Anwendungstests oder Paket-/Installationsänderungen ausgeführt: Der Auftrag betrifft ausschließlich Dokumente. Quellkatalog, vorhandene Befehlsdokumentationen samt Index und Anwendungscode bleiben unverändert.
- Keine bekannten offenen Strukturfehler oder Unsicherheiten der ausgeführten Beispiele. Fachliche Präzisierungen gegenüber den kurzen Quelleinträgen sind oben einzeln ausgewiesen. Dokumentiert sind die konkrete Python-Version und die relevante Float-Plattformabhängigkeit.
- Ein erster Abruf der NIST-Algorithmus-Seite war mit HTTP 403 gesperrt. Diese Seite wird nicht als geprüfte Quelle ausgegeben und ist nicht im Index enthalten. Für den Algorithmus-Eintrag wurden die tatsächlich erreichbaren offiziellen Python-Abschnitte zu Schleifen und Sortierschlüsseln herangezogen.

Hier endet der Auftrag. `it_0011` bis `it_0302` wurden nicht angelegt oder bearbeitet. Fortsetzung erst nach ausdrücklicher Freigabe nach der Pilotprüfung.

# Fortsetzung ab Datensatz 11

Svens Fortsetzungsauftrag gibt Datensätze 11–302 ausdrücklich frei und ersetzt den historischen Stopp nach der Zehnerprobe. Es ist keine erneute Zwischenfreigabe erforderlich. Die oben dokumentierte Pilotphase bleibt als Historie erhalten. Laut Sven wurden die ersten zehn Texte inzwischen fachlich geprüft und lokal im Reader erfolgreich ausprobiert; diese Abnahme wurde in diesem Browser-Checkout nicht erneut ausgeführt.

Arbeitsbranch: `codex/linux-glossar-011-302`. Ausgangscommit: `688a83204d653b7977d11848ac813d400a7b1b8f`. Bestehendes isoliertes Checkout verwendet, kein zusätzliches Worktree. Arbeitsverzeichnis vor Beginn sauber. Pilottexte und ihre zehn Indexdatensätze als unveränderlichen Ausgangsstand geprüft. Quelle erneut auf erwarteten SHA-256, 302 Einträge sowie eindeutige IDs und Begriffe geprüft.

Die lokale Reader-Erweiterung mit `parse_glossary_document` ist in diesem Checkout nicht vorhanden. Die Textstruktur wird deshalb wie im Pilot mit dem vorhandenen begrenzten Markdown-Parser und einem ausschließlich im Arbeitsspeicher erzeugten kompatiblen Prüfkopf validiert. Das verändert keine gespeicherten Glossarköpfe und ist keine Reader-Abnahme. Quellenprüfung und Beispielausführung erfolgen einzeln je neuem Eintrag, vor dem Index-/Fortschrittsupdate und dem Beginn des nächsten Eintrags. Die konkreten HTTPS-Abschnittsanker werden beim Abruf geprüft; die inhaltliche Prüfung stützt sich auf die gelesenen Primärtexte.

## 11. Null – it_0011

Ausgearbeitet und strukturell geprüft: 688 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5625 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/constants.html#None
- https://docs.python.org/3.13/library/json.html#encoders-and-decoders

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das passende Python-Beispiel None beibehalten. „Kein Wert“ als besonderer vorhandener Wert präzisiert; Zahl 0, fehlende Felder und sprach-/schnittstellenspezifische Bedeutungen getrennt. Belege: None-Konstantenreferenz und JSON-Zuordnungstabelle.

SHA-256: `c5eed8854194d8d5f6f9ba55b00b936615c251617412408755a2459d84125f13`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 12. Operator – it_0012

Ausgearbeitet und strukturell geprüft: 697 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5582 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#boolean-operations
- https://docs.python.org/3.13/reference/expressions.html#operator-precedence

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Die Quellbeispiele +, == und and sind passend. Ihre Typabhängigkeit, Operatorrangfolge und Python-Kurzschlussauswertung ergänzt; and/or liefern nicht allgemein nur Booleans. Belege: Rangfolgetabelle und boolesche Operationen der Python-Referenz.

SHA-256: `c9164548d40d761479b92290927190386fca93b5b36acab099207b55d7fd6d42`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 13. Operand – it_0013

Ausgearbeitet und strukturell geprüft: 680 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5542 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#binary-arithmetic-operations
- https://docs.python.org/3.13/reference/expressions.html#evaluation-order

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Quellbeispiel 2 + 3 ist passend. Operand als Rolle eines Werts oder Teilausdrucks statt als eigener Datentyp erklärt; Typkombination und Reihenfolge ergänzt. Belege: binäre Rechenoperationen und Auswertungsreihenfolge der Python-Referenz.

SHA-256: `cde51a65ca13b5ce263b1436a21d49eb953a28dc364104b0ec6d0c81ca4804c1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 14. Bedingung – it_0014

Ausgearbeitet und strukturell geprüft: 622 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5177 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#truth-value-testing
- https://docs.python.org/3.13/reference/compound_stmts.html#the-if-statement

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Der Quellvergleich ist passend; als vollständige Python-Anweisung benötigt er Doppelpunkt und Block. Bedingungen von Booleans und Verzweigungsanweisungen getrennt; Python-Wahrheitswertprüfung und Reihenfolge anhand offizieller Referenz belegt. Grenzwerte 17/18/19 praktisch geprüft.

SHA-256: `366aa9e5359afa18ca6bf3ca70cf5eba8bb7ea895956271b89b73d2dddcad94d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 15. Schleife – it_0015

Ausgearbeitet und strukturell geprüft: 658 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5485 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/compound_stmts.html#the-for-statement
- https://docs.python.org/3.13/reference/compound_stmts.html#the-while-statement

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Mehrfach ausgeführter Block“ um Ablaufstruktur, mögliche Null-Durchläufe und Abbruchregeln präzisiert. for/while-Beispiele sind passend; ihre Python-Regeln sind durch die zwei verlinkten Referenzabschnitte belegt. Beide Summen praktisch geprüft.

SHA-256: `367295a493af8adb5188499f8a8e283f7d2381860c86158932ce8fe98f0a1a9b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 16. Iteration – it_0016

Ausgearbeitet und strukturell geprüft: 663 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5497 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-iterator
- https://docs.python.org/3.13/library/functions.html#enumerate

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Jedes Element ist eine Iteration“ korrigiert: Element ist der Wert, Iteration der Durchlauf; doppelte Werte können mehrere Durchläufe betreffen. Iteratorzustand und Zähler anhand offizieller Iterator-/enumerate-Dokumentation ergänzt und praktisch unterschieden.

SHA-256: `679f8fc5de54b23b16840bc91e85fbc1791b15fd76f47ae94a2f67e4288ca41e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 17. Funktion – it_0017

Ausgearbeitet und strukturell geprüft: 642 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5422 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#lambda
- https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Definition um aufrufbaren Baustein erweitert; anonyme Funktionen zeigen, dass ein eigener Name keine allgemeine Voraussetzung ist. def check_dns(): ist ohne Körper nur ein Definitionsanfang, kein vollständiges Beispiel; stattdessen ungefährliche reine Formatierungsfunktion praktisch geprüft. Quellen: Python-Funktionstutorial und Lambda-Referenz.

SHA-256: `2aa02aa54c66fb0f9b9fa0a1eee89a966060f48ec58369bdf5927b14d4529700`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 18. Parameter – it_0018

Ausgearbeitet und strukturell geprüft: 650 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5581 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-parameter
- https://docs.python.org/3.13/tutorial/controlflow.html#default-argument-values

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Der Name name im Quellbeispiel ist korrekt als Parameter eingeordnet. Definitionsanfang zu lauffähiger Funktion ergänzt; Parameterarten und Zeitpunkt der Standardwertauswertung anhand Python-Glossar und Tutorial erläutert. Standard und ausdrücklich angegebener Gruß praktisch geprüft.

SHA-256: `d32d8de8284a167eeb13338a15b069bc417e8cb90798566b2fc9ded56751dd36`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 19. Argument – it_0019

Ausgearbeitet und strukturell geprüft: 656 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5611 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-argument
- https://docs.python.org/3.13/reference/expressions.html#calls

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Quellbeispiel ist korrekt. Konkreten Argumentwert von Parameter und Argumentausdruck getrennt; Positions-/Schlüsselwortzuordnung und fehlende Kopiergarantie präzisiert. Belege: offizielles Argument-Glossar und Aufrufreferenz. Drei Aufrufformen praktisch geprüft.

SHA-256: `e1e1a2a6135eb3707d0b765961749facd86a3d6c1b5c7452c163151784a4c292`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 20. Rückgabewert – it_0020

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5449 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/simple_stmts.html#the-return-statement
- https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Quellbeispiel return True ist passend und wurde in einen vollständig prüfbaren Funktionskörper eingeordnet. Rückgabe von Ausgabe und Prozess-Exitstatus getrennt; implizites None für gewöhnliche Python-Funktionen anhand Return-Referenz und Tutorial belegt.

SHA-256: `37845faba46adbfac44a5bdacdae3210abbd734dd919b2a83348c045d5b02232`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 21. Scope – it_0021

Ausgearbeitet und strukturell geprüft: 651 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5641 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/executionmodel.html#resolution-of-names
- https://docs.python.org/3.13/tutorial/classes.html#python-scopes-and-namespaces

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Die Quellaussage ist für gewöhnliche lokale Funktionsnamen passend. Sichtbarkeit, Namensraum und Objektlebensdauer getrennt; global nicht mit prozessübergreifendem Zustand gleichgesetzt. Python-Regeln und Sonderfälle anhand Scope-Tutorial und Ausführungsmodell belegt.

SHA-256: `b6ad2eb3ae4ac0eeca156f86d7ab61755fca311c6eb39e08a0b9a449c8b11666`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 22. Kommentar – it_0022

Ausgearbeitet und strukturell geprüft: 670 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5601 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/lexical_analysis.html#comments
- https://peps.python.org/pep-0257/#what-is-a-docstring

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel # ist für Python passend. Kommentar, Stringinhalt und Docstring getrennt; „nicht ausgeführt“ um speziell verarbeitete Kodierungs-/Werkzeughinweise präzisiert. Belege: lexikalische Python-Referenz und PEP 257. Sichtbares Hashzeichen und abrufbarer Docstring praktisch geprüft.

SHA-256: `bec191093588579ecef0c7dcd2b68f9c62f4899726574dc2b3df24f87a56f126`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 23. Syntax – it_0023

Ausgearbeitet und strukturell geprüft: 636 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5565 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/compound_stmts.html#compound-statements
- https://docs.python.org/3.13/tutorial/errors.html#syntax-errors

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das fehlende-Doppelpunkt-Beispiel ist passend. Fehlerposition von Ursache getrennt und Syntaxprüfung ausdrücklich nicht als Funktionsprüfung ausgegeben. Quellen: Python-Syntaxfehlertutorial und Grammatik zusammengesetzter Anweisungen. Vollständiges Lernskript ausgeführt; darin ungültigen Beispieltext nur mit compile geprüft.

SHA-256: `4d59c56425b68c34593dc25bc0e6b77449a77036064fd198d36187e396fa02f7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 24. Semantik – it_0024

Ausgearbeitet und strukturell geprüft: 688 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5732 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#binary-arithmetic-operations
- https://docs.python.org/3.13/reference/expressions.html#comparisons

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Beispiel sind passend. Sprachlich festgelegte Bedeutung von fachlicher Anforderung getrennt. Vergleichsgrenzen und typabhängige Operationen mit Python-Primärquellen belegt; beide Vergleichsergebnisse und Grenzfälle praktisch geprüft.

SHA-256: `b717723e5a60712aa470fc383fb074db466261d80c8595d2d1bfe5664598524b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 25. Fehler – it_0025

Ausgearbeitet und strukturell geprüft: 663 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5578 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/exceptions.html#NameError
- https://docs.python.org/3.13/tutorial/errors.html#exceptions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Das Quellbeispiel ist möglich, aber kein zwingender Zusammenhang: Tippfehler können NameError oder bei anderer Bindung falsche Ergebnisse verursachen. Fehlersignal, Diagnose und Ursache getrennt. Python-Ausnahmetutorial und NameError-Referenz als Belege; absichtliche Ausnahme und korrigierte Rechnung praktisch geprüft.

SHA-256: `b35de450fe530d3f5869d49cff3b59b736aac0191ae645fd17bfc3fde0a9428a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 26. Bug – it_0026

Ausgearbeitet und strukturell geprüft: 652 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5610 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/bugs.html
- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.assertEqual

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel ist fachlich passend; reale Prozessstarts durch eine ausdrücklich gekennzeichnete Listen-Simulation ersetzt. Fehlerursache, Beobachtung und Umgebungsproblem getrennt. Quellen: offizielle Bug-Berichtsanleitung und unittest-Vergleichsdokumentation. Nur Simulation praktisch geprüft, keine GUI-/Prozessintegration.

SHA-256: `7eebf4b8bccaf7f95417f47ad0137e0fcf0dd8f496f61f11422d548729b96dca`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 27. Debugging – it_0027

Ausgearbeitet und strukturell geprüft: 648 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5512 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#breakpoint
- https://docs.python.org/3.13/library/pdb.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Interaktive Debuggersitzung nicht ausgeführt; praktisch geprüft wurde ausschließlich das Rechenbeispiel mit gezielten Ausgaben.

Präzisierung gegenüber der Quelle: Die Quellbeispiele print-Ausgaben oder Debugger sind passend. Systematisches Eingrenzen von bloßem Verändern des Codes getrennt; pdb und konfigurierbaren breakpoint-Hook anhand offizieller Dokumentation erläutert.

SHA-256: `1d549103e6af057aeaac7c82998c59a4cbc195157ea16739cc00cf4efe6c23b7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 28. Refactoring – it_0028

Ausgearbeitet und strukturell geprüft: 655 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5726 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.assertEqual
- https://martinfowler.com/bliki/DefinitionOfRefactoring.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Aufteilungsbeispiel sind passend. Beobachtbares Verhalten einschließlich Schnittstellen/Nebenwirkungen präzisiert; Refactoring von Bugkorrektur und Erweiterung getrennt. Primärquellen: Fowlers Definition und offizielle Python-Testvergleichsdokumentation. Drei Stringfälle vor/nach Aufteilung praktisch verglichen.

SHA-256: `76b224fff9208200e3aaa816e4072653e34dd2a36d7411fef6419e226359de24`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 29. Codebase – it_0029

Ausgearbeitet und strukturell geprüft: 663 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5891 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/tutorial/modules.html#modules
- https://raw.githubusercontent.com/git/git/master/Documentation/gitrepository-layout.adoc

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Gedankliche Projektstruktur nicht angelegt, importiert oder praktisch getestet; keine Lauffähigkeit behauptet.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist als allgemeine Orientierung passend. Codebestand von Repository, Arbeitsbaum und Installationsprodukt getrennt; Python-Module und Git-Verwaltungsstruktur mit offiziellen Projektquellen belegt. Die Git-Webseite und der CPython-Devguide waren beim Abruf mit HTTP 403 gesperrt; stattdessen offizielles Git-Handbuch aus dem Projektquelltext verwendet.

SHA-256: `7b5407b442ce0e1f7ea67a96f1f2ef99a5ea179eb1c3562b68c59e0fdb8d3cb0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 30. Quellcode – it_0030

Ausgearbeitet und strukturell geprüft: 684 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6098 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/lexical_analysis.html#encoding-declarations
- https://docs.python.org/3.13/tutorial/modules.html#modules

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Vom Menschen geschrieben“ um möglichen generierten Quellcode präzisiert. Dateiendung von gültigem oder sicherem Inhalt getrennt. Offizielle Python-Modul- und Kodierungsdokumentation belegt Dateistruktur und UTF-8-Regel. Eigenes temporäres Miniscript tatsächlich geschrieben, zurückgelesen und ausgeführt; keine Projektdateien verändert.

SHA-256: `7367dc23bad54fa4aa789595e7076f3d2942ec221c27c90fb64bd137217944d9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 31. Runtime – it_0031

Ausgearbeitet und strukturell geprüft: 648 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5783 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sys.html#sys.implementation
- https://docs.python.org/3.13/library/time.html#time.perf_counter

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Die zwei Bedeutungen der Quelle sind passend. Ausführungsumgebung, Ausführungszeitpunkt und gemessene Dauer getrennt; Interpreterimplementierung nicht mit Sprachversion gleichgesetzt. Quellen: sys.implementation und perf_counter. CPython-Annahme sowie Berechnung und Zeitdifferenz praktisch geprüft, kein Benchmark behauptet.

SHA-256: `4bfcc762474d1d94186532346bb33c37c90cf903ebaae3b46a23d9c2b00c8065`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 32. Build – it_0032

Ausgearbeitet und strukturell geprüft: 663 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5894 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/tutorials/packaging-projects.rst
- https://www.gnu.org/software/make/manual/html_node/Introduction.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Gedankenbeispiel nicht gebaut oder installiert; keine Artefakte oder Funktionsprüfung behauptet.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Paketbeispiel sind passend. Build von Kompilieren, Installieren und Funktionsprüfung getrennt; Wheel nicht grundsätzlich mit Maschinencode gleichgesetzt. Belege: GNU-Make-Handbuch und offizielles PyPA-Tutorial aus dessen Projektquelle. Die direkte PyPA-Webseite war mit HTTP 403 gesperrt.

SHA-256: `7a6347c570c6992a5239183297464b38891cc83f624fbe621270d94d0a9821f3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 33. Deployment – it_0033

Ausgearbeitet und strukturell geprüft: 685 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6177 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/django/django/stable/5.2.x/docs/howto/deployment/checklist.txt
- https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/concepts/workloads/controllers/deployment.md

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Bereitstellungsablauf ausschließlich als Gedankenbeispiel; keine Installation, Dienständerung oder funktionale Abnahme ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeispiel Serverbereitstellung ist passend, aber nicht die einzige Form. Deployment von Build, Installation und Veröffentlichung getrennt; Kubernetes-Ressourcenbegriff ausdrücklich als Spezialfall bezeichnet. Belege: offizielle Django-5.2- und Kubernetes-Dokumentation aus den Projektquellen.

SHA-256: `563427a6301742357377db2dcaa40847fe7bc71d34928ac7e11bb7e0b37929e0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 34. Release – it_0034

Ausgearbeitet und strukturell geprüft: 698 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6109 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://peps.python.org/pep-0602/
- https://raw.githubusercontent.com/github/docs/main/content/repositories/releasing-projects-on-github/about-releases.md

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Freigabeablauf ausschließlich gedanklich; kein Release, Tag, Paketupload oder Deployment ausgeführt.

Präzisierung gegenüber der Quelle: Das Quellbeispiel 1.0.0 ist nur mit tatsächlich erfolgter Freigabe ein Releasebeispiel; Nummer allein reicht nicht. Release von Version, Tag, Build und Deployment getrennt. Belege: offizielle GitHub-Releasebeschreibung und Python-Releasezyklus PEP 602.

SHA-256: `6d71f63e1d0de5556e235e135debfd808db2e59f74aa604d5c539e15635fec73`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 35. Version – it_0035

Ausgearbeitet und strukturell geprüft: 660 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5938 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://peps.python.org/pep-0440/#version-scheme
- https://semver.org/spec/v2.0.0.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel 1.2.3 ist passend, besitzt aber ohne erklärtes Schema keine feste Semantik. Version von Release/Commit/Dateiinhaltsnachweis getrennt. SemVer und Python-Paketregeln anhand jeweiliger Primärquelle unterschieden; Zahlenfolgenvergleich praktisch geprüft und ausdrücklich nicht als vollständiger Versionsparser bezeichnet.

SHA-256: `6b6e6618b4f99ef4ba02165eda1fe59b3ad5a8c58ca572f93cc5af6ed6477af2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 36. Changelog – it_0036

Ausgearbeitet und strukturell geprüft: 667 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6087 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://keepachangelog.com/en/1.1.0/
- https://raw.githubusercontent.com/git/git/master/Documentation/git-log.adoc

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Redaktionelles Gedankenbeispiel; keine Version gebaut, veröffentlicht oder praktisch getestet.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist passend. Kuratierte nutzerorientierte Übersicht von Commit-Historie, Testbericht und Zukunftsplan getrennt. Primärquellen: Keep a Changelog und offizielles git-log-Handbuch. Beispiel ausdrücklich erfunden, keine tatsächliche NetMon-Historie behauptet.

SHA-256: `c2ba760e18bd69e0f74f762f194b5b833e68dc2b7786976395fe1df31c98b053`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 37. Array – it_0037

Ausgearbeitet und strukturell geprüft: 674 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5632 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.rust-lang.org/book/ch03-02-data-types.html#the-array-type
- https://docs.python.org/3.13/library/array.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur Python-array-Beispiel ausgeführt; Rust-Eigenschaften anhand Dokumentation geprüft, kein Rust-Code ausgeführt.

Präzisierung gegenüber der Quelle: Array nicht allgemein mit Liste gleichgesetzt; Positionen, Elementtyp, Länge und Änderbarkeit getrennt. Feste Rust-Arrays und veränderliche Python-array-Folgen anhand ihrer offiziellen Dokumentation gegenübergestellt; kleines Python-Array praktisch geändert und erweitert.

SHA-256: `1eb2a9f8794855ab77bcccd397a719a9b42dcc2a351780520e54427188765bee`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 38. Liste – it_0038

Ausgearbeitet und strukturell geprüft: 669 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5522 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#lists
- https://docs.python.org/3.13/tutorial/datastructures.html#more-on-lists

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel ist passend. „Geordnet“ von „sortiert“ getrennt und Listenbegriff auf die jeweilige Sprache bezogen. Python-Referenz und Listenmethodentutorial belegen Veränderbarkeit sowie append/pop/remove-Unterschiede; Zwischenstände der eigenen Zahlenliste praktisch geprüft, keine Netzwerkaktion.

SHA-256: `f1e89ac636e14a724300d3f13cf6f5ce796b27016d7cb9918e765df0356f647f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 39. Tuple – it_0039

Ausgearbeitet und strukturell geprüft: 658 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5464 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#tuples
- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel ist passend. Python-Tupel eindeutig als unveränderliche Folge beschrieben; Strukturunveränderlichkeit von veränderlichen enthaltenen Objekten getrennt. Belege: Tupelreferenz und Python-Datenmodell. Abgelehnte Ersetzung und zulässige Änderung der enthaltenen Liste praktisch geprüft.

SHA-256: `05604e4db681893aaf7934fcf2a73893389d1bd72b0d9b82ed3657d905e3fba0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 40. Dictionary – it_0040

Ausgearbeitet und strukturell geprüft: 661 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5731 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#mapping-types-dict
- https://docs.python.org/3.13/tutorial/datastructures.html#dictionaries

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeschreibung und DNS-Textbeispiel sind passend. Schlüssel/Wert und Vorhandensein/Inhalt getrennt; Hashbarkeit sowie Python-3.7-Reihenfolgegarantie anhand dict-Referenz und Tutorial erläutert. Eigenes Dictionary praktisch geprüft; keine DNS- oder Netzwerkaktion ausgeführt.

SHA-256: `035384262f83ecea14248df263acbda8e85b99230295570e4282e36c5f62afd4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand der Fortsetzung

**40 von 302 ausgearbeitet und strukturell geprüft: zehn unveränderte Pilottexte und 30 neue Texte (`it_0011` bis `it_0040`). Der Gesamtauftrag bis 302 ist noch nicht abgeschlossen.**

Der Durchlauf endet an seiner Verarbeitungsgrenze. Es liegt keine erneute Freigabeanforderung und kein fachlicher oder externer Zugriffsblocker für die Fortsetzung vor. Die ausdrücklich erteilte Freigabe für sämtliche übrigen Einträge bleibt bestehen. **Nächster Datensatz: 41, `it_0041 – Map`; danach lückenlos in Originalreihenfolge weiter bis `it_0302 – Garbage Collection`.** Die noch offenen 262 Texte sind nicht angelegt; es gibt keine Platzhalter.

Tatsächlich ausgeführte Abschlussprüfungen dieses Zwischenstands:

- Quelle erneut gelesen: erwarteter SHA-256 `b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24`; 302 Einträge, eindeutige IDs und Begriffe.
- Alle 40 Dokumente und Indexdatensätze auf lückenlose Quellreihenfolge, vollständige Originaleinträge, Dateinamen, Metadaten, zehn Hauptabschnitte, UTF-8-/Zeilen-/Block-/Tabellenlimits, geschlossene Codeblöcke und existierende interne Dokumentverweise geprüft.
- Alle Dokument-SHA-256-Werte gegen die endgültigen Bytes geprüft. `documented_records` beträgt tatsächlich 40. Die globale Quellenliste ist die sortierte, duplikatfreie Vereinigung der konkreten Eintragsquellen.
- Die ersten zehn Texte byteweise mit Pilotcommit `688a83204d653b7977d11848ac813d400a7b1b8f` verglichen; ihre zehn Indexdatensätze sind inhaltlich exakt unverändert. Auch `PROMPT.md` bleibt unverändert. Der historische Zehnerstopp wird ausschließlich durch Svens Fortsetzungsauftrag ersetzt.
- Von den 30 neuen Texten enthalten 25 ein vollständiges Python-Beispiel. Diese wurden je in einem temporären Ordner mit Python 3.13.5 ausgeführt: Exitcode 0, Assertions erfolgreich und Standardausgabe exakt wie dokumentiert. Im abschließenden Gesamtlauf wurden auch die unveränderten Pilotbeispiele erneut erfolgreich ausgeführt.
- Die fünf Gedankenbeispiele (`Codebase`, `Build`, `Deployment`, `Release`, `Changelog`) wurden strukturell und redaktionell geprüft, aber nicht als reale Projekte oder betriebliche Abläufe ausgeführt. Interaktive Debuggernutzung und Rust-Code wurden ebenfalls nicht ausgeführt; die jeweiligen Texte und Einzelberichte benennen diese Grenzen.
- Beim Syntax-Beispiel wurde das vollständige Lernskript praktisch ausgeführt. Der darin enthaltene absichtlich ungültige Quelltext wurde nur mit `compile` geprüft und nicht ausgeführt. Dies ist kein Funktionsnachweis für ungültigen Code.
- Quellen wurden einzeln vor dem Schreiben der jeweiligen Einträge abgerufen und inhaltlich geprüft; verlinkte HTTPS-Adressen lieferten HTTP 200 und vorhandene Anker wurden geprüft. Einzelne gesperrte Dokumentationsseiten wurden durch tatsächlich abgerufene offizielle Projektquellen ersetzt; diese Abweichungen stehen bei den betroffenen Einträgen.
- Gesamt-Diff auf den freigegebenen Dokumentationspfad und unbeabsichtigte Änderungen geprüft; Whitespaceprüfung mit `git diff --check` bestanden. Anwendung, Tests, Abhängigkeiten, Paketierung, Quellkatalog und bestehende Befehlsdokumentation werden nicht geändert.

**Offen:** unabhängige fachliche Prüfung und lokale Reader-Abnahme der 30 neuen Texte sowie die Ausarbeitung von Eintrag 41 bis 302. Die gemeldete erfolgreiche Pilotabnahme wird nicht auf neue Texte übertragen. Ein `parse_glossary_document` ist im Browser-Checkout weiterhin nicht vorhanden; daher wurde keine tatsächliche Reader-Integration behauptet oder Anwendungscode ergänzt.

Pilot-PR #5 ist zum Zeitpunkt dieser Sicherung noch offen und nicht in `main` gemergt. Der Fortsetzungs-PR wird deshalb gegen `codex/linux-glossar-pilot-001-010` erstellt: Sein Diff zeigt ausschließlich die 30 neuen Texte und die Erweiterungen von Index/Fortschrittsbericht. Es erfolgt kein Merge und kein Force-Push.
