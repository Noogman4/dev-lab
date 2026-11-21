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

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Gedankliche Projektstruktur nicht angelegt, importiert oder praktisch getestet; keine Lauffähigkeit behauptet.

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

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Gedankenbeispiel nicht gebaut oder installiert; keine Artefakte oder Funktionsprüfung behauptet.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Paketbeispiel sind passend. Build von Kompilieren, Installieren und Funktionsprüfung getrennt; Wheel nicht grundsätzlich mit Maschinencode gleichgesetzt. Belege: GNU-Make-Handbuch und offizielles PyPA-Tutorial aus dessen Projektquelle. Die direkte PyPA-Webseite war mit HTTP 403 gesperrt.

SHA-256: `7a6347c570c6992a5239183297464b38891cc83f624fbe621270d94d0a9821f3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 33. Deployment – it_0033

Ausgearbeitet und strukturell geprüft: 685 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6177 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/django/django/stable/5.2.x/docs/howto/deployment/checklist.txt
- https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/concepts/workloads/controllers/deployment.md

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Bereitstellungsablauf ausschließlich als Gedankenbeispiel; keine Installation, Dienständerung oder funktionale Abnahme ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeispiel Serverbereitstellung ist passend, aber nicht die einzige Form. Deployment von Build, Installation und Veröffentlichung getrennt; Kubernetes-Ressourcenbegriff ausdrücklich als Spezialfall bezeichnet. Belege: offizielle Django-5.2- und Kubernetes-Dokumentation aus den Projektquellen.

SHA-256: `563427a6301742357377db2dcaa40847fe7bc71d34928ac7e11bb7e0b37929e0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 34. Release – it_0034

Ausgearbeitet und strukturell geprüft: 698 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6109 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://peps.python.org/pep-0602/
- https://raw.githubusercontent.com/github/docs/main/content/repositories/releasing-projects-on-github/about-releases.md

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Freigabeablauf ausschließlich gedanklich; kein Release, Tag, Paketupload oder Deployment ausgeführt.

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

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Redaktionelles Gedankenbeispiel; keine Version gebaut, veröffentlicht oder praktisch getestet.

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

# Fortsetzung ab Datensatz 41

Sven hat die unveränderte Weiterarbeit bis einschließlich Datensatz 302 erneut bestätigt; die gemeinsame abschließende Zusammenfassung ist erst danach vorgesehen. Start dieses Durchlaufs: Branch `codex/linux-glossar-011-302`, Commit `65bfd29c4428729ddce00b018488e3ba213e87ee`, sauberer Arbeitsstand. Quelle, 302 eindeutige IDs/Begriffe und Gesamtindex mit 40 Dokumenten erneut geprüft; alle vorhandenen Dokumente samt Beispielen bestehen die Strukturprüfung. Kein zusätzliches Worktree, keine Unteragenten. Der bestehende Entwurfs-PR #6 bleibt der Fortsetzungs-PR.

Protokollkorrektur bei Wiederaufnahme: In den Einzelberichten 29, 32, 33, 34 und 36 wurde eine unzutreffende generische Python-Prüfzeile durch die tatsächliche Kennzeichnung als Gedankenbeispiel ersetzt. Die jeweiligen Dokumente und weiteren Einzelhinweise hatten bereits ausdrücklich keine praktische Ausführung behauptet. Der temporäre Berichtsschreiber verwendet nun den tatsächlich festgestellten Beispieltyp.

## 41. Map – it_0041

Ausgearbeitet und strukturell geprüft: 621 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5372 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-mapping
- https://docs.python.org/3.13/library/functions.html#map

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Die Map-Zuordnung aus der Quelle ist passend. Allgemeines Mapping ausdrücklich von Pythons map()-Funktion getrennt; Eindeutigkeit der Schlüssel nicht mit eindeutigen Werten verwechselt. Belege: Mapping-Glossar und map-Referenz. Beide Bedeutungen mit eigenen Daten praktisch geprüft.

SHA-256: `7098411ec97dcf7e548da05890782c335aafb8625932cbca88891d5bc7dccce5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 42. Set – it_0042

Ausgearbeitet und strukturell geprüft: 626 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5343 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#set-types-set-frozenset
- https://docs.python.org/3.13/tutorial/datastructures.html#sets

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Automatisches Entfernen doppelter Einträge präzisiert: Eine Mengenbildung verändert die ursprüngliche Liste nicht automatisch; Reihenfolge und Häufigkeiten sind im Set nicht erhalten. Hashbarkeit und set/frozenset mit offizieller Referenz belegt; Mengenoperationen und sortierte Anzeige praktisch geprüft.

SHA-256: `fa6434858e1fd77c1056cca6f13378c50ab82070a74b7ebd57723c2a1759a874`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 43. Stack – it_0043

Ausgearbeitet und strukturell geprüft: 638 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5386 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/queue.html#queue.LifoQueue
- https://docs.python.org/3.13/tutorial/datastructures.html#using-lists-as-stacks

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Listenstack mit Reihenfolge, Nachsehen und absichtlich leerer Entnahme ausgeführt. Blockierende LifoQueue- und reale Aufrufstapelabläufe nicht praktisch getestet.

Präzisierung gegenüber der Quelle: Quellbeschreibung und LIFO-Beispiel sind passend. Abstrakte Zugriffsschnittstelle von Liste und Laufzeit-Aufrufstapel getrennt; leeren Zustand und schnittstellenspezifische Kapazität erläutert. Primärquellen: Python-Stack-Tutorial und LifoQueue-Referenz.

SHA-256: `96e292a0e27102a8b849273347820f24adeab5c97ceefbe857966379bbfddbe5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 44. Queue – it_0044

Ausgearbeitet und strukturell geprüft: 630 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5448 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/collections.html#collections.deque
- https://docs.python.org/3.13/library/queue.html#queue.Queue.empty

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Lokale deque-Verarbeitung ausgeführt; Warteverhalten, Hintergrundarbeiter und konkurrierende Zugriffe nicht praktisch getestet.

Präzisierung gegenüber der Quelle: FIFO-Aussage präzisiert: Entnahmereihenfolge ist bei parallelen Arbeitern keine Abschlussgarantie. deque von blockierender Queue und unterschiedlicher Kapazitätsbehandlung getrennt. Belege: deque-Referenz und Warnung zu Queue.empty().

SHA-256: `9703bcef2e0155b2fbe62273343efb5a789e79f0d3223fd257eab36124f8b759`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 45. Baum – it_0045

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5627 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/xml.etree.elementtree.html#building-xml-documents
- https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.tree.recognition.is_tree.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur ElementTree-Speicherbeispiel ausgeführt; kein reales Dateisystem untersucht und NetworkX weder ausgeführt noch installiert.

Präzisierung gegenüber der Quelle: Baumdefinition um Wurzelkonvention und Zyklenfreiheit präzisiert; reales Dateisystem mit zusätzlichen Links nicht pauschal als einfacher Baum ausgegeben. Belege: NetworkX-Baumdefinition und ElementTree-Aufbau. Eigene Elementhierarchie praktisch erstellt und besucht.

SHA-256: `994d0f0f592037955d181b10dd97e1f6280b018485467a8c7f942a4190596242`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 46. Knoten – it_0046

Ausgearbeitet und strukturell geprüft: 647 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5596 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types
- https://networkx.org/documentation/stable/reference/classes/generated/networkx.Graph.add_node.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes Dictionary-Knotenmodell ausgeführt; keine realen Ordner/Geräte untersucht und NetworkX nicht ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist passend. Knotenkennung, Beschriftung, Inhalt und technische Objektidentität getrennt; abstrakten Knoten nicht mit Dateisystem-Inode gleichgesetzt. Belege: offizielle NetworkX-Knotenschnittstelle und Python-Datenmodell.

SHA-256: `b9f60120e7937e6f86dd0e2ef875feee5c9c136be068e8926e59de2af2bf4f79`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 47. Graph – it_0047

Ausgearbeitet und strukturell geprüft: 633 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5384 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://networkx.org/documentation/stable/reference/classes/digraph.html#networkx.DiGraph
- https://networkx.org/documentation/stable/reference/classes/graph.html#networkx.Graph

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenen Graphen mit Kreis und isoliertem Knoten praktisch durchlaufen; keine reale Topologie gemessen und NetworkX nicht ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Netzwerkvergleich sind passend. Richtung, Kreise und Modell/Messung getrennt; Eigenschaften einzelner Graphklassen nicht verallgemeinert. Belege: offizielle NetworkX-Graph-/DiGraph-Referenz.

SHA-256: `689b369d051c72d16d29e0a52c70dc94fe6c86c8e6dafdbf8b449efaa0fa4391`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 48. Hash – it_0048

Ausgearbeitet und strukturell geprüft: 639 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5718 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/hashlib.html#usage
- https://docs.python.org/3.13/reference/datamodel.html#object.__hash__

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: „Kurz-Wert“ präzisiert: Verfahren und Darstellungsform bestimmen das Ergebnis; nicht jeder Hash ist kryptografisch oder dauerhaft. Dateiintegrität von Herkunft und Verschlüsselung getrennt; Kollisionen nicht ausgeschlossen. Belege: hashlib-Verwendung und Objekt-Hashregeln. Eigene temporäre Datei vor/nach Änderung praktisch gehasht.

SHA-256: `4d805da8410548e0f8420348e1ec343c88637f5735b3bda9571c28f096e7888c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 49. Index – it_0049

Ausgearbeitet und strukturell geprüft: 634 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5655 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/stdtypes.html#common-sequence-operations
- https://www.sqlite.org/lang_createindex.html
- https://www.sqlite.org/queryplanner.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Listenposition und eigener SQLite-Speicherindex praktisch geprüft; weder Datenbankdatei verändert noch Geschwindigkeit oder konkreten Abfrageplan nachgewiesen.

Präzisierung gegenüber der Quelle: Beide Quellbedeutungen beibehalten und getrennt. Position nicht als dauerhafte Kennung ausgegeben; Suchindex nicht mit garantierter Beschleunigung gleichgesetzt. Belege: Python-Folgeoperationen sowie offizielle SQLite-Index-/Abfrageplanungsdokumentation.

SHA-256: `00c0e61c98a5e6e4461e6ee5071aecd99a6662872e4d82649271db2309eee7cc`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 50. Pointer – it_0050

Ausgearbeitet und strukturell geprüft: 629 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5460 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html
- https://www.gnu.org/software/c-intro-and-ref/manual/html_node/Invalid-Dereference.html
- https://www.gnu.org/software/c-intro-and-ref/manual/html_node/Pointers.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. C-Funktion ausschließlich anhand Sprachregeln erläutert; nicht kompiliert oder ausgeführt. Kein C-/Rust- oder Rohspeicherexperiment durchgeführt.

Präzisierung gegenüber der Quelle: Speicheradresse und sprachliche Referenz nicht pauschal gleichgesetzt. C-Zeigerwert, Objektinhalt und Gültigkeit getrennt; sichere Rust-Referenzen als eigener Vertrag erläutert. Primärquellen: GNU-C-Pointer-/Dereferenzierungsdokumentation und offizielles Rust-Buch.

SHA-256: `f7d1339b7f3e22452637afebd10005909f7d4f74af6fb1347efd05477b62b2ba`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 51. Referenz – it_0051

Ausgearbeitet und strukturell geprüft: 671 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5610 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html
- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur flache eigene Python-Liste geprüft; verschachtelte Kopien, Rust-Ausleihen und C-Zugriffe nicht praktisch ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist passend, aber sprachabhängig. Referenz, Kopie, Name, Pointer und Identität getrennt. Python-Datenmodell und offizielle Rust-Ausleihregeln als Primärquellen. Gemeinsame Liste und neue äußere Kopie praktisch verglichen.

SHA-256: `c36fc8f4f2208cff709dc9edf0277c6d939f01ceb19c178da9d74f3a79fc3df5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 52. Klasse – it_0052

Ausgearbeitet und strukturell geprüft: 627 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5549 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/tutorial/classes.html#class-definition-syntax
- https://docs.python.org/3.13/tutorial/classes.html#class-objects

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei eigene reine Dateninstanzen praktisch geprüft; keine echten Fenster oder GUI-Bibliotheken gestartet.

Präzisierung gegenüber der Quelle: Vorlagenbild um Python-Klassenobjekt und ausgeführte Definition ergänzt. class Window: als unvollständigen Definitionsanfang eingeordnet; Initialisierung nicht pauschal mit Erzeugung gleichgesetzt. Belege: offizielle Klassendefinitions-/Klassenobjektabschnitte.

SHA-256: `08a4c0581e1197521433f108367ad9582b2fba1b8effaaa566b983a482769382`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 53. Objekt – it_0053

Ausgearbeitet und strukturell geprüft: 670 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5601 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types
- https://docs.python.org/3.13/tutorial/classes.html#instance-objects

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene Dictionary-Zustände geprüft; keine realen Fenster oder äußeren Ressourcen erzeugt.

Präzisierung gegenüber der Quelle: Klasseninstanz-Bild für Python um allgemeines Objektmodell erweitert: Auch eingebaute Werte, Funktionen und Klassen sind Objekte. Identität, Typ, Wert und Name getrennt. Belege: Python-Datenmodell und Instanzobjekt-Tutorial. Gleiche Inhalte und gemeinsame Identität praktisch unterschieden.

SHA-256: `32988e103a81c75a1c92e96ec0bd250c9b9f360a7c013e5999977dbd2d4585d6`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 54. Instanz – it_0054

Ausgearbeitet und strukturell geprüft: 644 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5618 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#isinstance
- https://docs.python.org/3.13/tutorial/classes.html#class-objects

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei eigene reine Zustandsinstanzen und einen Alias praktisch geprüft; keine echte GUI oder Verbindung erzeugt.

Präzisierung gegenüber der Quelle: Quellbeispiel ist für eine gewöhnliche Python-Klasse passend. Klassenaufruf und zusätzliche Namensbindung getrennt; Instanzzugehörigkeit einschließlich Unterklassen nicht mit exakter Typidentität verwechselt. Belege: Klassenobjekt-Tutorial und isinstance-Referenz.

SHA-256: `a96955b2862d8c200b7865e6b42a6ace8040e47cb5d031789437a5b2074a6ad7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 55. Methode – it_0055

Ausgearbeitet und strukturell geprüft: 651 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5608 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#staticmethod
- https://docs.python.org/3.13/tutorial/classes.html#method-objects

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Zählermethode einschließlich gespeichertem gebundenem Aufruf praktisch geprüft; keine echte GUI, Callback-Registrierung oder Betriebssystemaktion getestet.

Präzisierung gegenüber der Quelle: Quellbeschreibung und click-Aufruf sind passend. Normal gebundene Methode, Funktionsobjekt und staticmethod unterschieden; Abrufen nicht mit Aufrufen gleichgesetzt. Belege: Python-Methodentutorial und staticmethod-Referenz.

SHA-256: `084db9b565a006e180550d3fe0c80aea3ecd088713315abb0f25ac488259c3a9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 56. Attribut – it_0056

Ausgearbeitet und strukturell geprüft: 638 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5577 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#property
- https://docs.python.org/3.13/tutorial/classes.html#instance-objects

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Eigenschaftsbild um Datenattribute, Methoden und vermittelte Eigenschaften ergänzt. window.title nicht pauschal als Text bestimmter GUI-Bibliotheken ausgegeben. Belege: Instanzobjekt-Tutorial und property-Referenz. Eigener Textwert und berechnete Länge praktisch geprüft.

SHA-256: `5276661a79aad2023846028b56dcd6c13537969d502661bc25aa15e2250c0cc1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 57. Konstruktor – it_0057

Ausgearbeitet und strukturell geprüft: 629 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5710 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/datamodel.html#object.__init__
- https://docs.python.org/3.13/reference/datamodel.html#object.__new__

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur gewöhnlichen Aufbau einer eigenen Klasse geprüft; besondere Fabrikfälle, GUI- und Ressourceninitialisierung nicht praktisch getestet.

Präzisierung gegenüber der Quelle: Quellbeispiel fachlich präzisiert: __new__ erzeugt eine Instanz; __init__ initialisiert sie und darf keinen anderen Wert als None liefern. „__init__ ist der Konstruktor“ daher ausdrücklich als Vereinfachung eingeordnet. Primärquellen: beide Python-Datenmodellabschnitte. Reihenfolge praktisch protokolliert.

SHA-256: `5712d3de46dbdde255b40ad40461705eba2c8c7d68a577d30ed20be2580b6828`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 58. Vererbung – it_0058

Ausgearbeitet und strukturell geprüft: 606 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5735 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#super
- https://docs.python.org/3.13/tutorial/classes.html#inheritance

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Einfache eigene Vererbung praktisch geprüft; keine Mehrfachvererbung, echten Konten oder GUI-Typen getestet.

Präzisierung gegenüber der Quelle: Quellbeispiel ist als Klassenmodell passend, verleiht aber keine Betriebssystemrechte. Geerbte Schnittstelle, überschriebenes Verhalten und Initialisierung getrennt; super an Methodenauflösungsreihenfolge gebunden. Belege: Python-Vererbungstutorial und super-Referenz.

SHA-256: `cebf9ebfe5abe9bad9f5e9539fa6f88adb1aa2453fa6c10286e9e55861641cb2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 59. Polymorphismus – it_0059

Ausgearbeitet und strukturell geprüft: 608 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5550 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-duck-typing
- https://docs.python.org/3.13/library/typing.html#typing.Protocol

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei unabhängige eigene Textimplementierungen praktisch geprüft; keine echten Widgets oder statischen Typprüfer ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Widget-Beispiel sind passend. Gemeinsamen Methodenname nicht mit vollständiger Kompatibilität gleichgesetzt; Polymorphismus nicht auf Vererbung beschränkt. Belege: offizielles Duck-Typing-Glossar und Protocol-Dokumentation.

SHA-256: `dd358681174860b7d39ccd706db19ec0492533d6875da4da5e28e6454f0c253f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 60. Kapselung – it_0060

Ausgearbeitet und strukturell geprüft: 630 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5719 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#property
- https://docs.python.org/3.13/tutorial/classes.html#private-variables

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur kleine eigene Integerfälle der vorgesehenen Methode getestet; keine vollständige Typvalidierung oder Isolation behauptet.

Präzisierung gegenüber der Quelle: „Zustand nur über Methoden“ als Entwurfsziel statt Python-Zugriffsgarantie eingeordnet. Unterstriche und Name-Mangling nicht als Sicherheitsgrenze ausgegeben. Belege: offizielle Private-Variablen-Erklärung und property-Referenz. Gültige Erhöhung und zustandserhaltende Ablehnung praktisch geprüft.

SHA-256: `0f5c5264a11c38a8f2f432e8d1b0123ac8d577c8137e9207f16d0c1ec4789756`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 61. Interface – it_0061

Ausgearbeitet und strukturell geprüft: 624 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5791 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/abc.html#abc.abstractmethod
- https://docs.python.org/3.13/library/typing.html#typing.Protocol

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine echten Plugins, Laufzeit-Vertragssuite oder statischen Typprüfer ausgeführt.

Präzisierung gegenüber der Quelle: Methodenliste um Eingaben, Ergebnisse, Fehlerfälle und Semantik erweitert; Interface nicht auf ein bestimmtes Schlüsselwort beschränkt. Protocol und abstrakte Basisklasse anhand offizieller Python-Dokumentation unterschieden. Basiserzeugungsablehnung und eigene Textimplementierung praktisch geprüft.

SHA-256: `755f5defcecf7d185caa70b200a3925037b10a05c262485f2ce4e440c4397363`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 62. Abstraktion – it_0062

Ausgearbeitet und strukturell geprüft: 638 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5619 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pathlib.html#pure-paths
- https://www.sqlite.org/queryplanner.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene PurePosixPath-Operationen ausgeführt; keine Datei-, Datenbank- oder Netzwerkprüfung vorgenommen.

Präzisierung gegenüber der Quelle: Abstraktion als zweckbezogene Auswahl relevanter Eigenschaften erklärt, nicht auf Klassen oder Geheimhalten beschränkt. Belege: offizielle PurePath-Trennung und SQLite-Erklärung deklarativer Anfragen. Grenzen des NetworkScanner-Namens ausdrücklich benannt.

SHA-256: `b6e6f0198e431f9c6b19e4fc94cea76a7c1c9a9e1d0ae7701fb67c6b29b1244c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 63. Mixin – it_0063

Ausgearbeitet und strukturell geprüft: 631 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5763 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/collections.abc.html#collections-abstract-base-classes
- https://docs.python.org/3.13/tutorial/classes.html#multiple-inheritance

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Ein eigenes einfaches Mixin mit getrennten Instanzlisten praktisch geprüft; keine komplexe Mehrfachvererbung oder echte Protokolldatei getestet.

Präzisierung gegenüber der Quelle: Quellbeschreibung und LoggingMixin-Beispiel sind passend. Mixin als Entwurfsrolle statt Sprachschlüsselwort eingeordnet; erforderliche Attribute, Namensauflösung und Instanziierbarkeit präzisiert. Belege: collections.abc-Mixinmethoden und offizielles Mehrfachvererbungstutorial.

SHA-256: `c158464738ce45e87b810347967c07e36658d36aabb7d2359ad7aa625bd41c07`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 64. GUI – it_0064

Ausgearbeitet und strukturell geprüft: 627 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5651 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qtwidgets-index.html
- https://docs.python.org/3.13/library/tkinter.html#a-hello-world-program

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Oberflächenablauf ausschließlich als Gedankenbeispiel; kein Fenster aufgebaut, keine Bedien- oder Reader-/NetMon-GUI-Abnahme durchgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist passend. GUI nicht auf Mausbedienung oder gesamten Anwendungskern reduziert; sichtbaren Zustand von nachgewiesener Wirkung getrennt. Belege: offizielles Tkinter-Einstiegsprogramm und Qt-Widgets-Dokumentation. Den geprüften Tkinter-Abschnittsanker nach tatsächlichem Dokumentaufbau verwendet.

SHA-256: `35ed389a7721d465f41295cf64cbc3b016ad97bfd794de6c429614ab1254e466`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 65. CLI – it_0065

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5763 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/argparse.html#argparse.ArgumentParser.parse_args
- https://www.gnu.org/software/bash/manual/html_node/What-is-a-shell_003f.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes temporäres CLI-Programm samt Argumentverarbeitung, Ausgabe und Hilfe tatsächlich gestartet; keine fremden Befehle oder Netzverbindungen getestet.

Präzisierung gegenüber der Quelle: CLI von Terminal und Shell getrennt; interaktive Eingabe nicht als einzige Verwendung ausgegeben. Ping-Aufruf ist begrifflich passend, aber wegen echtem Netzverkehr durch eine eigene lokale CLI ersetzt. Belege: Bash-Shellbeschreibung und argparse-Referenz.

SHA-256: `df6f33a561f5d712a94b6af4d079359ae404ceed5f4b9743f25171e4be4ebea8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 66. TUI – it_0066

Ausgearbeitet und strukturell geprüft: 621 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5579 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/howto/curses.html#what-is-curses
- https://raw.githubusercontent.com/htop-dev/htop/main/htop.1.in

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Erfundene Bildschirmansicht nicht implementiert oder bedient; weder curses/htop gestartet noch reale Prozesse verändert.

Präzisierung gegenüber der Quelle: Quellbeschreibung und htop-Beispiel sind passend. Laufende Textoberfläche von bloßer Textausgabe und CLI-Aufruf getrennt; mögliche Mausbedienung und verändernde Aktionen anhand offiziellen htop-Handbuchs benannt. Weitere Primärquelle: Python-curses-Einführung.

SHA-256: `f904a870d92e6152876a78662b2e1b62639e8e8f9a7bb6c869a9a2fa7207a5a5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 67. Widget – it_0067

Ausgearbeitet und strukturell geprüft: 622 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5605 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qtwidgets-index.html
- https://docs.python.org/3.13/library/tkinter.html#a-hello-world-program

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene verborgene Tk-Hierarchie unter Xvfb praktisch erzeugt und abgefragt; kein Layout, echter Klick, visueller Reader-/NetMon- oder Qt-Test.

Präzisierung gegenüber der Quelle: Quellbeispiele sind passend. Widget nicht auf Eingabeelement oder Fenster beschränkt; Existenz, Layout und Bedienbarkeit getrennt. Primärquellen: offizielle Qt-Widgets-Übersicht und Tkinter-Einstiegsprogramm.

SHA-256: `f69320ed9488d922f244e199f77900f2545c6f83404e8fb6dc9668b4254eec46`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 68. Button – it_0068

Ausgearbeitet und strukturell geprüft: 654 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5726 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Button.invoke
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_button.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur programmgesteuerten eigenen Tk-Callback getestet; kein echter Klick, Layout-/Zugänglichkeits- oder NetMon-Scan-Test.

Präzisierung gegenüber der Quelle: „Anklickbar“ um vorgesehene Aktivierungswege erweitert; Aktivierung nicht als erfolgreicher Abschluss ausgegeben. Belege: offizielles ttk::button-Handbuch und Python-invoke-Referenz. Callback und deaktivierter Zustand unter Xvfb praktisch geprüft.

SHA-256: `54e56598c34d3cfb15108ce118933113f6f1babd2477c115926b3a74383de72e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 69. Label – it_0069

Ausgearbeitet und strukturell geprüft: 650 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5551 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Label
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_label.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene StringVar-Label-Bindung unter Xvfb tatsächlich geändert und abgefragt; keine sichtbare Darstellung, Verbindung oder NetMon-Statusmessung geprüft.

Präzisierung gegenüber der Quelle: Reine Textdefinition um toolkitabhängige Bildmöglichkeiten und dynamischen Inhalt ergänzt. Statuswortlaut nicht als eigenständigen fachlichen Nachweis ausgegeben. Belege: offizielle ttk.Label-Referenz und Tk-Label-Handbuch.

SHA-256: `f224576d2b751bd63c296878cbfcf60a01ad48210ea9fdc8ecf3235a3f89149d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 70. Textfeld – it_0070

Ausgearbeitet und strukturell geprüft: 633 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5710 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.ip_address
- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Entry
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_entry.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes Entry unter Xvfb programmgesteuert bearbeitet; gültige und ungültige eigene Adresstexte geparst. Keine Netzwerkverbindung oder echte Tastatur-/Layout-/Reader-Abnahme.

Präzisierung gegenüber der Quelle: Quellbeispiel ist passend. Textspeicherung, Adresssyntax und reale Erreichbarkeit getrennt; ttk.Entry als einzeilige Ausprägung eingeordnet. Primärquellen: Python-Entry-Referenz, offizielles Tk-Entry-Handbuch und ip_address-Referenz.

SHA-256: `c768ede422a8c3ccbd7e9b56d38d9d92599207526c359ddb2e9154c8f3c68b8f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 71. Checkbox – it_0071

Ausgearbeitet und strukturell geprüft: 628 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5808 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Checkbutton.invoke
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_checkbutton.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene lokale Checkbutton-Umschaltung und Callback-Werte unter Xvfb geprüft; keine DNS-Guard-, echte Eingabe- oder gemischte Zustandsprüfung.

Präzisierung gegenüber der Quelle: Quellbeispiel als möglicher Zusammenhang eingeordnet, sichtbare Auswahl aber nicht mit wirksamer DNS-Konfiguration gleichgesetzt. Zustandswerte und Anwendungszeitpunkt präzisiert. Belege: offizielles Tk-Checkbutton-Handbuch und Python-invoke-Referenz.

SHA-256: `9a80ce47743dcbf91fa74ceba0b5653614153cef5d3e98ad9930e88b936dbb52`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 72. Radiobutton – it_0072

Ausgearbeitet und strukturell geprüft: 601 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5552 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Radiobutton.invoke
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_radiobutton.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Tk-Gruppe unter Xvfb mit leerer Anfangsauswahl, Wechsel und Wiederaktivierung geprüft; keine echten Eingaben oder Netzwerkeinstellungen verändert.

Präzisierung gegenüber der Quelle: „Genau eine“ zu Gruppenexklusivität plus nötigem Ausgangszustand präzisiert. IPv4/IPv6-Beispiel nur als exklusive Anwendungsmoduswahl eingeordnet, nicht als Unvereinbarkeit beider Protokolle. Belege: offizielles Tk-Radiobutton-Handbuch und Python-invoke-Referenz.

SHA-256: `5d28c93892a0c5e34a55931a557d784f4ab81c3034364dcc7f1af3c5ac5533a7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 73. Dropdown – it_0073

Ausgearbeitet und strukturell geprüft: 617 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5495 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Combobox
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_combobox.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Combobox-Werte unter Xvfb gesetzt und abgefragt; kein Popup-/Tastatur-/Geräte- oder Netzwerkauswahltest.

Präzisierung gegenüber der Quelle: Dropdown von editierbarer Combobox unterschieden. readonly nicht als allgemeine Wertvalidierung ausgegeben; Position, Beschriftung und stabile Kennung getrennt. Belege: offizielle Python- und Tk-Combobox-Dokumentation. Auch programmatisch gesetzter Fremdwert praktisch geprüft.

SHA-256: `6ad182f8b44c76340746c7c3e27294fda8f59347396e5c6c74d6515e1c63777b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 74. Dialog – it_0074

Ausgearbeitet und strukturell geprüft: 640 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5466 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qdialog.html
- https://docs.python.org/3.13/library/dialog.html#tkinter.simpledialog.Dialog

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Dialog ausschließlich als Gedankenmodell; kein Fenster geöffnet, kein Abbruch-/Fokus-/Modalitätsablauf oder Paketmitschnitt praktisch getestet.

Präzisierung gegenüber der Quelle: „Kleines Fenster“ als häufige Erscheinungsform statt Definition eingeordnet. Dialogrolle von Modalität und Bestätigung von fachlichem Erfolg getrennt. Belege: offizielle QDialog-Beschreibung und simpledialog.Dialog-Referenz.

SHA-256: `a05464e9c15047e542d43a760e4e0fa4eff73dd8c8efff76c4338779f5c96c88`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 75. Modal – it_0075

Ausgearbeitet und strukturell geprüft: 645 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5689 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qdialog.html
- https://docs.python.org/3.13/library/dialog.html#tkinter.simpledialog.Dialog

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Ausschließlich Gedankenmodell; keine echten Fokus-/Fenster-/Eingabesperren oder NetMon-Dialoge praktisch geprüft.

Präzisierung gegenüber der Quelle: „Vor Weiterarbeit schließen“ um den betroffenen Geltungsbereich präzisiert. Bedienmodalität von synchronem Warten und blockierter Ereignisverarbeitung getrennt. Belege: offizielle Qt-Modalitätsbeschreibung und Python-simpledialog-Vertrag.

SHA-256: `e14ce27bedfbcc7c7a6139d8c1ab9c4a0e98683745731c4dce78f87d1ace92e9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 76. Event – it_0076

Ausgearbeitet und strukturell geprüft: 623 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5570 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.html#bindings-and-events
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/bind.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigenes virtuelles Tk-Ereignis unter Xvfb erzeugt; keine echten Eingaben, Betriebssystembenachrichtigungen oder NetMon-Handler getestet.

Präzisierung gegenüber der Quelle: Maushandlung als Beispiel beibehalten, Ereignis aber um interne/virtuelle Anlässe erweitert. Ereignis, Reaktion und fachlichen Erfolg getrennt. Belege: Tkinter-Bindings und offizielles Tk-bind-Handbuch. Eigenes virtuelles Ereignis mit Ziel und Warteschlangenzustand praktisch geprüft.

SHA-256: `16b251999c52eea52a8610908b5c079d329e68f1b86a3fc20f3bdbcef9654490`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 77. Event Loop – it_0077

Ausgearbeitet und strukturell geprüft: 632 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5695 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/asyncio-eventloop.html#running-and-stopping-the-loop
- https://docs.python.org/3.13/library/tkinter.html#threading-model

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene verborgene Tk-mainloop mit geplantem Rückruf und begrenzter Beendigung unter Xvfb geprüft; keine asyncio-, Thread- oder NetMon-Laufzeitabnahme.

Präzisierung gegenüber der Quelle: GUI-Fokus der Quelle um weitere Ereignisschleifen erweitert. mainloop nicht mit fachlichem Erfolg, Parallelität oder garantierter Timerfrist gleichgesetzt. Belege: Tkinter-Threading-Modell und asyncio-Loop-Lebenszyklus.

SHA-256: `3024c0454505696a2e2073d6d963a981d2d295e7604888cb2d7de4acd7f12a74`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 78. Callback – it_0078

Ausgearbeitet und strukturell geprüft: 655 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5517 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-callback
- https://docs.python.org/3.13/library/tkinter.html#bindings-and-events

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Unmittelbaren eigenen Callback mit gebundener Listenmethode praktisch geprüft; keine GUI-, Thread- oder Hintergrundausführung getestet.

Präzisierung gegenüber der Quelle: Auf Ereignisse bezogene Quellbeschreibung erweitert: Callbacks sind weitergegebene Aufrufmöglichkeiten und können synchron ohne Event Loop laufen. Signatur und Weitergeben statt sofortigem Aufruf präzisiert. Belege: offizielles Callback-Glossar und Tkinter-Bindings.

SHA-256: `22acd7ee769d61bda783b0f30d5c9b96505e857032d68b87527e9472ec868e76`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 79. Layout – it_0079

Ausgearbeitet und strukturell geprüft: 646 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5884 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/layout.html
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/grid.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene grid-Positionen, Ausrichtung und Gewicht unter Xvfb praktisch abgefragt; keine reale Größen-/Pixel-/Skalierungs- oder NetMon-/Reader-Abnahme.

Präzisierung gegenüber der Quelle: Reihen-/Spaltenbeispiel um Größenverteilung, Hierarchie und Inhaltsänderungen ergänzt. Konfigurationsprüfung nicht mit sichtbarer Bedienbarkeit gleichgesetzt. Belege: offizielle Qt-Layoutbeschreibung und Tk-grid-Handbuch.

SHA-256: `cbbe7fe1adcbe4cf12f6ae9de5734464a2755addadbb70421a1d6053cf8a809f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 80. Frame – it_0080

Ausgearbeitet und strukturell geprüft: 625 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5591 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Frame
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/destroy.n
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_frame.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene verschachtelte Tk-Frames und Kindzerstörung unter Xvfb praktisch geprüft; kein sichtbares Layout oder NetMon-Einstellungsbereich getestet.

Präzisierung gegenüber der Quelle: Quellbeschreibung ist passend. Containerrolle von sichtbarem Rahmen, Layout und anderen Frame-Bedeutungen getrennt; Toolkit-Lebensdauer nicht mit Python-Namensbindung gleichgesetzt. Belege: offizielle Python-/Tk-Frame-Dokumentation und Tk-destroy-Handbuch.

SHA-256: `e5cfb78db819a293355e48033a05644dac1c2c4bb60601cb1039cbd704ed2a15`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Arbeitscheckpoint nach Datensatz 80

Tatsächlicher Stand: **80 von 302 Texten ausgearbeitet und strukturell geprüft**. In diesem Durchlauf wurden `it_0041 – Map` bis `it_0080 – Frame` einzeln recherchiert, geschrieben, validiert und jeweils vor dem nächsten Eintrag im Index sowie hier gespeichert. Die gemeinsame Gesamtzusammenfassung bleibt gemäß Svens Auftrag bis einschließlich 302 vorgesehen.

Der aktuelle Durchlauf wird an seiner Verarbeitungsgrenze gesichert. Der Auftrag ist weiterhin bis 302 freigegeben; keine erneute Zwischenfreigabe erforderlich. **Nächster Datensatz: `it_0081 – Canvas`**. Die noch offenen 222 Dokumente wurden nicht als Platzhalter angelegt.

Prüfungen und tatsächliche Grenzen dieses Checkpoints:

- Quelle: SHA-256 weiterhin `b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24`; 302 Einträge sowie eindeutige IDs und Begriffe.
- Index: unverändertes Schema, 80 lückenlose Originalzuordnungen, vollständige unveränderte Quelldatensätze, tatsächliche endgültige Dokumentprüfsummen und sortierte duplikatfreie Quellenvereinigung. Neue Texte bleiben `review_pending`.
- Vorhandener Stand: Dokumente und Indexdatensätze 1–40 mit dem Durchlauf-Ausgangscommit `65bfd29c4428729ddce00b018488e3ba213e87ee` verglichen. Die zehn Pilottexte zusätzlich mit `688a83204d653b7977d11848ac813d400a7b1b8f` verglichen. Diese Inhalte sowie `PROMPT.md` sind unverändert.
- Alle 80 Dokumente: JSON-kompatibler Kopf, exakte Originalfelder und Kategorien, zehn vereinbarte Hauptabschnitte, geschlossene Codeblöcke, Größen-/Zeilen-/Block-/Tabellenlimits und vorhandene interne Verweise geprüft. Der vorhandene begrenzte Markdown-Parser wird ausschließlich mit temporärem kompatiblem Kopf im Arbeitsspeicher verwendet; keine gespeicherten Befehlsfelder hinzugefügt.
- 35 neue vollständige Python-Beispiele praktisch unter Python 3.13.5 ausgeführt, mit Exitcode 0, Assertions und exakter dokumentierter Standardausgabe. Der Gesamtlauf wiederholt auch die zuvor vorhandenen Beispiele.
- Davon 11 eigene Tk-Beispiele (67–73, 76, 77, 79, 80) unter dem bereits vorhandenen Xvfb ausgeführt. Geprüft wurden gezielte Erzeugung, Zustände, programmgesteuerte Aktionen, Ereignisverarbeitung, Layoutvorgaben oder Lebensdauer. Das sind keine visuellen Bedien-, Tastatur-, Maus-, Zugänglichkeits- oder Reader-Abnahmen.
- Kein Python-Ausführungsnachweis für die C-Erläuterung `Pointer` oder die vier Gedankenbeispiele `GUI`, `TUI`, `Dialog`, `Modal`; diese Grenzen sind in Text und Einzelbericht ausgewiesen. Kein C-/Rust-Code kompiliert, keine realen Netzwerke, Prozesse oder Gerätekonfigurationen verändert.
- Tatsächlich abgerufene HTTPS-Primärquellen je Eintrag geprüft und mit konkreten Adressen verlinkt; vorhandene Abschnittsanker anhand der gelieferten Dokumente geprüft. Nicht vorhandene zunächst vermutete Tkinter-/argparse-Anker wurden vor Verwendung durch die tatsächlich vorhandenen Anker ersetzt; im Index stehen nur erfolgreich geprüfte Adressen.
- Der temporäre Strukturprüfer wurde korrigiert, damit Kommentare und gültige Tk-Ereignissyntax innerhalb geschlossener Codeblöcke nicht als Dokumentüberschrift oder HTML-Markup fehlklassifiziert werden. Erst nach erfolgreicher erneuter Prüfung wurde der betroffene Eintrag 67 in den Index übernommen. Anwendungscode und Reader wurden dafür nicht verändert.
- Unzutreffende generische Python-Prüfzeilen bei den früheren Gedankenbeispielen 29, 32, 33, 34 und 36 wurden im Fortschrittsbericht berichtigt. Diese reine Protokollkorrektur ändert keine betreffenden Dokumente oder Indexdatensätze. Der Berichtsschreiber verwendet jetzt den tatsächlichen Beispieltyp.
- Änderungen ausschließlich unter `docs/linux-glossar/`, keine Anwendung, Tests, Abhängigkeiten, Paketierung, ursprünglichen Befehlsdokumentationen oder Quellkatalog geändert. Vollständiger Änderungsumfang und Whitespaceprüfung geprüft. Kein zusätzliches Worktree, kein Merge und kein Force-Push.

Offen bleiben Ausarbeitungen 81–302 sowie die unabhängige fachliche Prüfung und lokale Reader-Abnahme der neuen Texte. Der im Browser-Checkout fehlende `parse_glossary_document` wurde nicht durch Anwendungscodeänderungen ergänzt. Die bereits von Sven gemeldete lokale Pilotabnahme wird nicht als Abnahme der Fortsetzung ausgegeben.

Der fortlaufende Entwurfs-PR ist #6 auf Branch `codex/linux-glossar-011-302`. Der bestehende PR wird um diesen geprüften Stand erweitert; die Inhalte sind kein Abschluss des gesamten Auftrags.

# Fortsetzung ab Datensatz 81

Sven hat die Weiterarbeit bis 302 erneut bestätigt. Ausgangspunkt dieses Durchlaufs: Branch `codex/linux-glossar-011-302`, Commit `b6c38afbcbe9957c7921e27f4efe9bdbff6a593c`, sauberer Arbeitsstand. Quelle und Index mit 80 Dokumenten erneut geprüft; vorhandene Texte, Zuordnungen und praktische Beispiele bestehen den Gesamtlauf. Der vorhandene Entwurfs-PR #6 wird fortgeführt. Kein zusätzliches Worktree, keine Unteragenten, keine Änderungen außerhalb des freigegebenen Dokumentationspfads. Die abschließende gemeinsame Zusammenfassung bleibt für Eintrag 302 vorgesehen.

## 81. Canvas – it_0081

Ausgearbeitet und strukturell geprüft: 615 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5600 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qgraphicsscene.html
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/canvas.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Tk-Elemente unter Xvfb erzeugt, bewegt und entfernt; keine visuelle Grafik-, Qt-, NetMon- oder Messdatenabnahme.

Präzisierung gegenüber der Quelle: Quellbeschreibung und Grafikbeispiel sind passend. Toolkitabhängiges Zeichenmodell sowie Objektkennung/Tag getrennt; Qt-Szene nicht mit Tk-Canvas gleichgesetzt. Primärquellen: offizielles Tk-Canvas-Handbuch und QGraphicsScene-Referenz.

SHA-256: `8d66283e5035058ae23da8e88ef697bb0d05bbc39fb24ad06dd74928597c5685`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 82. Tooltip – it_0082

Ausgearbeitet und strukturell geprüft: 649 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5581 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qtooltip.html
- https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Ausschließlich Hilfetext-Gedankenmodell; keine tatsächliche Anzeige, Maus-/Tastaturbedienung oder Qt-/Reader-Abnahme.

Präzisierung gegenüber der Quelle: Mausauslöser der Quelle als häufige Variante statt alleinige Definition eingeordnet. Tooltip von Hauptbeschriftung und Dialog getrennt. Primärquellen: Qt-QToolTip und informative W3C-Erläuterung zu Webinhalten; deren Geltungsbereich ausdrücklich benannt.

SHA-256: `98f911cdf2d9341636220b1d468ad7a51aa5fc6d8a7781e37b746c395bd3c4ba`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

# Fortsetzung ab Datensatz 83

Sven hat am 21.11.2026 zunächst Commit und Push des gespeicherten Stands 81–82 und anschließend die Weiterarbeit beauftragt. Der Gesamtlauf für 82 Texte bestand; ausschließlich die vier erwarteten Dateien wurden als Commit `21a3c95` gesichert und auf `codex/linux-glossar-011-302` gepusht. Vorhandene Texte und Indexdatensätze 1–80 blieben dabei unverändert. Die Weiterarbeit beginnt mit `it_0083 – Theme`, erneut einzeln in Quellreihenfolge, ohne Unteragenten und ohne zusätzliches Worktree. Quellenabrufe und Beispielprüfungen des folgenden Durchlaufs erfolgen am 21.11.2026. Der Browser-Checkout enthält weiterhin keinen `parse_glossary_document`; verwendet wird ausschließlich die dokumentierte temporäre Strukturprüfung, keine Reader-Abnahme.

## 83. Theme – it_0083

Ausgearbeitet und strukturell geprüft: 613 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5507 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.ttk.html#tkinter.ttk.Style.theme_create
- https://raw.githubusercontent.com/tcltk/tk/core-8-6-branch/doc/ttk_style.n

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes Tk-Theme unter Xvfb erzeugt, gewählt und abgefragt; keine sichtbare Kontrast-, Systemtheme- oder NetMon-Abnahme.

Präzisierung gegenüber der Quelle: Dark Mode als mögliche Theme-Variante statt vollständiger universeller Gestaltung eingeordnet. Widget-Stil, Theme, Layout und fachliche Wirkung getrennt. Belege: offizielles ttk-style-Handbuch und theme_create-Referenz.

SHA-256: `f9aa68f53ce8cadf915a627a1225671d31b9f278a2b7e651c18c914ddfa8fc12`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 84. Responsive Design – it_0084

Ausgearbeitet und strukturell geprüft: 622 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5717 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/layout.html
- https://www.w3.org/WAI/WCAG22/Understanding/reflow.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes Tk-Feld unter Xvfb bei zwei Fenstergrößen tatsächlich gemessen; keine vollständige Responsive-, WCAG-, NetMon- oder Reader-Abnahme.

Präzisierung gegenüber der Quelle: Quellbeschreibung als Gestaltungsziel eingeordnet, nicht als automatische Garantie. Web-Reflow und Desktopanpassung samt unterschiedlichen Maßsystemen getrennt. Belege: offizielle W3C-Reflow-Erläuterung und Qt-Layoutdokumentation.

SHA-256: `c78238fadf4dd15ab466a50a5f46f80acb77718ad959fbd10c301068751d1eda`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 85. Python – it_0085

Ausgearbeitet und strukturell geprüft: 622 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5659 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-CPython
- https://docs.python.org/3.13/library/tkinter.html#module-tkinter
- https://docs.python.org/3.13/tutorial/appetite.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Subjektive Lesbarkeit nicht als Qualitätsgarantie ausgegeben. Sprache, konkrete Implementierung und Bibliotheksvoraussetzungen getrennt. Belege: offizieller Tutorialeinstieg, CPython-Glossar und Tkinter-Modulbeschreibung. Eigene reine Integerverarbeitung samt Grenzfällen ausgeführt.

SHA-256: `37c1c245413e873777b87581081ccf2cbc3f32392351c6bcd665f9a74b86c5d5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 86. Modul – it_0086

Ausgearbeitet und strukturell geprüft: 654 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5806 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/import.html#the-module-cache
- https://docs.python.org/3.13/tutorial/modules.html#modules

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Dateibeispiel als häufige, nicht einzige Modulrepräsentation eingeordnet. Namensraum und Importcache anhand offizieller Python-Dokumentation präzisiert. Eigenes temporäres Modul und Identität bei zweimaligem normalem Import tatsächlich im Kindprozess geprüft.

SHA-256: `a5645290bc1d78a88a3b3fd1715104368fe2e176f8f63d4a1259c1d6a3067aff`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 87. Paket – it_0087

Ausgearbeitet und strukturell geprüft: 605 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5824 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/import.html#namespace-packages
- https://docs.python.org/3.13/reference/import.html#packages
- https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/discussions/distribution-package-vs-import-package.rst

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes reguläres Paket samt Initialisierungsdatei und Untermodul praktisch importiert; keine Namespace-Verteilung oder Installation getestet.

Präzisierung gegenüber der Quelle: Sammlungsbild um hierarchischen Importnamensraum präzisiert. Reguläre und Namespace-Pakete sowie Importpaket und installierbare Distribution getrennt. Belege: offizielle Python-Paket-/Namespace-Beschreibung und PyPA-Begriffsklärung.

SHA-256: `385ab0ef1ea2028b92e799b5ace70a7f4f470f7efa2250ac6d51349a630d076b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 88. Import – it_0088

Ausgearbeitet und strukturell geprüft: 665 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5852 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/import.html#loading
- https://docs.python.org/3.13/reference/simple_stmts.html#the-import-statement

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Quellbeispiel ist passend. Finden/Laden und lokale Namensbindung von Installation sowie Quelltextkopie getrennt. Belege: offizielle import-Anweisung und Ladebeschreibung. Eigenen Initialisierungslauf, Modulalias und separat gebundenen Integer praktisch geprüft.

SHA-256: `bd898b54e74f4c8383e30cea34bc27a51d3cf3444bbad0f56c616d07cafa3c21`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 89. pip – it_0089

Ausgearbeitet und strukturell geprüft: 626 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5747 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/pypa/pip/main/docs/html/cli/pip_install.rst
- https://raw.githubusercontent.com/pypa/pip/main/docs/html/user_guide.rst

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Beide beschriebenen pip-Aufrufe nicht ausgeführt; keine Installation, Aktualisierung, Entfernung oder Build-Ausführung vorgenommen.

Präzisierung gegenüber der Quelle: Paketmanager-Bild auf Python-Distributionen und ausgewählten Interpreter präzisiert. Installationsanforderung nicht mit neuem Download, Update oder Funktionsnachweis gleichgesetzt. Primärquellen: offizielle pip-Benutzeranleitung und Installationsreferenz aus dem Projektquelltext; direkte Dokumentationsseite war mit HTTP 403 gesperrt.

SHA-256: `976f639b5b003d5de6e55617e7ccff4f4463bd9dd3f32a5e6255e0b6d55b4dfd`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 90. venv – it_0090

Ausgearbeitet und strukturell geprüft: 612 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5830 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/venv.html#creating-virtual-environments
- https://docs.python.org/3.13/library/venv.html#venv.EnvBuilder

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene temporäre Linux-venv ohne pip oder Paketinstallation erzeugt und Interpreterpräfix geprüft; bestehende Projektumgebung und Systeminstallation unverändert.

Präzisierung gegenüber der Quelle: „Isolierte Umgebung“ auf Python-Paketkontext präzisiert, nicht als Sicherheitscontainer ausgegeben. Aktivierung von tatsächlicher Interpreterwahl getrennt. Belege: offizielle venv-Einführung und EnvBuilder-Referenz.

SHA-256: `2a3ede75be4dea8ef43bf4697f8c3f05eba04ac6a2fbf26b8113826da4c0feab`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 91. Exception – it_0091

Ausgearbeitet und strukturell geprüft: 609 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5405 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/exceptions.html#exception-hierarchy
- https://docs.python.org/3.13/tutorial/errors.html#handling-exceptions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Ausnahme nicht pauschal mit Defekt oder jedem Laufzeitproblem gleichgesetzt. Exception-Klasse von BaseException-Hierarchie und erwarteten Kontrollabläufen getrennt. Belege: offizielles Behandlungstutorial und Ausnahmehierarchie. Gezielte ValueError-Behandlung mit gültiger Null praktisch geprüft.

SHA-256: `6a540831871623d2a5d62368325e5f272f1b073cf0be2f38ac0ce61bd9346680`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 92. Traceback – it_0092

Ausgearbeitet und strukturell geprüft: 620 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5512 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/traceback.html#traceback.extract_tb
- https://docs.python.org/3.13/tutorial/errors.html#exceptions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine nicht ausgeführten praktischen Beispiele.

Präzisierung gegenüber der Quelle: Übliche Fehlerausgabe vom Traceback-Aufrufkontext und ergänzender Ausnahmeart getrennt. Letzte Stelle nicht als automatische Wurzelursache ausgegeben. Belege: offizielles Ausnahmetutorial und extract_tb-Referenz. Eigene Aufrufkette und Zeilennummern praktisch untersucht.

SHA-256: `26ed07d310a4b49dd170461f74e86e12b67d1d4e366c2931ead6c61cea5f071f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 93. Decorator – it_0093

Ausgearbeitet und strukturell geprüft: 698 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6126 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functions.html#staticmethod
- https://docs.python.org/3.13/library/functools.html#functools.wraps
- https://docs.python.org/3.13/reference/compound_stmts.html#function-definitions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Klassen-Decorators und gestapelte Decorators nicht praktisch ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeschreibung auf aufrufbare Objekte und Definitionsergebnis präzisiert; Zusatzarbeit pro Aufruf ist nur ein möglicher Aufbau. staticmethod anhand der offiziellen Referenz eingeordnet; wraps und eigene Hülle praktisch geprüft.

SHA-256: `95c054ccaee139e3bba58e5e660acc0a8baf20f02e114c8c5a0319c13fa48bd1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 94. Generator – it_0094

Ausgearbeitet und strukturell geprüft: 719 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5947 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html#term-generator
- https://docs.python.org/3.13/reference/expressions.html#yield-expressions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine großen Dateien, Ressourcenverwaltung oder gleichzeitigen Abläufe praktisch geprüft.

Präzisierung gegenüber der Quelle: Generatorfunktion und Generatorobjekt getrennt; yield erzeugt nicht bei jedem Durchlauf ein neues Generatorobjekt, sondern unterbricht dessen Ausführung. Verzögerte Berechnung und Erschöpfung praktisch geprüft.

SHA-256: `8c39fcf121994bd6efd2094e186c0186f13fde3088be96bbdc311689f6b67727`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 95. List Comprehension – it_0095

Ausgearbeitet und strukturell geprüft: 709 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5716 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/reference/expressions.html#displays-for-lists-sets-and-dictionaries
- https://docs.python.org/3.13/tutorial/datastructures.html#list-comprehensions

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Laufzeitmessung und keine großen Eingaben ausgeführt.

Präzisierung gegenüber der Quelle: Quellbeispiel um Filter, unveränderte Eingabe und sofortigen Ergebnisaufbau ergänzt. Neue Liste von Kopien ihrer Elemente abgegrenzt. Praktischer Vergleich mit ausgeschriebener Schleife und leerer Eingabe.

SHA-256: `9377e96edeaee73a56255b85872f2d0a0f4ef4e346fef07362496b9a3ed788c9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 96. Docstring – it_0096

Ausgearbeitet und strukturell geprüft: 692 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6055 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/using/cmdline.html#cmdoption-OO

- https://docs.python.org/3.13/tutorial/controlflow.html#documentation-strings
- https://peps.python.org/pep-0257/#what-is-a-docstring

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Dokumentationsgeneratoren, doctest und der Modus -OO wurden nicht ausgeführt.

Präzisierung gegenüber der Quelle: Regulären Docstring als erste Stringliteral-Anweisung von Kommentaren und beliebigen Texten getrennt; __doc__ und Beschreibung gegenüber tatsächlicher Prüfung abgegrenzt. Eigene Funktion samt und ohne Docstring praktisch geprüft.

SHA-256: `d07fa6e0ea620b02c01f711d6232ea3f84cf27ead104092773beb020297cb7a6`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 97. Type Hint – it_0097

Ausgearbeitet und strukturell geprüft: 701 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5933 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/typing.html
- https://peps.python.org/pep-0484/#non-goals

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein externer statischer Typprüfer installiert oder ausgeführt; keine entsprechende Diagnose behauptet.

Präzisierung gegenüber der Quelle: Typangaben ausdrücklich von Laufzeitprüfung und Umwandlung getrennt; Python 3.13 als Beispielversion genannt. Ausgelesene Hinweise und absichtlich nicht passender String-Aufruf praktisch geprüft.

SHA-256: `932c7e150206f33d256c30c413d7267bb6168dbb972bb669d9363cae7d57dd56`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 98. PEP 8 – it_0098

Ausgearbeitet und strukturell geprüft: 682 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5967 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://peps.python.org/pep-0008/#a-foolish-consistency-is-the-hobgoblin-of-little-minds
- https://peps.python.org/pep-0008/#function-and-variable-names
- https://peps.python.org/pep-0008/#indentation

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Absichtlich ungünstige erste Schreibweise unverändert als Lehrbeispiel; kein Formatierer oder Stilprüfer ausgeführt und keine vollständige PEP-8-Konformität behauptet.

Präzisierung gegenüber der Quelle: Stilregeln von Syntax und Verhalten abgegrenzt; ausdrücklich dokumentierte Priorität des Projektstils und Kompatibilität übernommen. Drei Eingabepaare zeigen gleiches Verhalten zweier Schreibweisen.

SHA-256: `05752d441f92ff01dd870477296850d5cc14e6bfe371c70a37e26b74981479b4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 99. Tkinter – it_0099

Ausgearbeitet und strukturell geprüft: 679 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6214 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tkinter.html#architecture
- https://docs.python.org/3.13/library/tkinter.html#threading-model
- https://docs.python.org/3.13/library/tkinter.ttk.html#ttk-widgets

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Interne Verweise auf GUI und Widget gegen die Originalbegriffe geprüft und korrigiert. Keine menschliche Bedienung, dauerhafte mainloop, Thread-Beispiele oder NetMon-/Reader-Abnahme ausgeführt.

Präzisierung gegenüber der Quelle: Standardschnittstelle zu Tcl/Tk statt reinem Python-Zeichensystem; nicht auf einfache Oberflächen beschränkt und Verfügbarkeit von Installation/Display getrennt. Eigenen Ttk-Button und Variable unter virtuellem Bildschirm praktisch geprüft.

SHA-256: `f46f6e934d381a9066b89b1afbe34e788e43f416eb491a7dcd98456fe8f11ee4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 100. PyQt – it_0100

Ausgearbeitet und strukturell geprüft: 730 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6306 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html
- https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Ausschließlich Gedankenbeispiel: keine Installation, kein PyQt-Import, kein Fensterstart und keine praktische GUI-Abnahme.

Präzisierung gegenüber der Quelle: PyQt als Python-Binding von Qt, nicht als ausschließliches Python-Zeichensystem erklärt; PyQt6-Dokumentation von anderen Hauptversionen getrennt. Signale und Slots anhand offizieller Riverbank-Quellen eingeordnet.

SHA-256: `734c47d0eca8a8323f6be960181be4aac7fbf238b7b53c4edb43524fd82c4210`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 101. subprocess – it_0101

Ausgearbeitet und strukturell geprüft: 702 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6379 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/subprocess.html#security-considerations
- https://docs.python.org/3.13/library/subprocess.html#subprocess.TimeoutExpired
- https://docs.python.org/3.13/library/subprocess.html#subprocess.run

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein ping, Netzwerkzugriff im Praxisbeispiel, Timeout-Ereignis oder check=True praktisch ausgelöst.

Präzisierung gegenüber der Quelle: Netzwerkbeispiel durch eigenen lokalen Unterprozess ersetzt; getrennte Argumente, Ausgabekanäle und absichtlichen Rückgabecode 3 praktisch geprüft. Sicherheit ohne Shell nicht mit Ungefährlichkeit beliebiger Programme gleichgesetzt.

SHA-256: `8133748ea272b83e1f1881d617a654174d08d7575493f685fa587aa81a31f1f9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 102. pathlib – it_0102

Ausgearbeitet und strukturell geprüft: 675 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5955 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.home
- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.read_text
- https://docs.python.org/3.13/library/pathlib.html#pure-paths

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Objekt-Verweis gegen Originalbegriff korrigiert. Kein Path.home-Aufruf, kein Zugriff auf Benutzerdaten und keine Tests symbolischer Links oder paralleler Dateiveränderungen.

Präzisierung gegenüber der Quelle: Pfadobjekt von Datei und reinem Namensumgang von Dateisystemzugriff getrennt. Path.home als auflösungsabhängig erläutert; Praxis ausschließlich eigener temporärer Pfad mit UTF-8-Schreiben und Lesen.

SHA-256: `16e414e7d7a5bfcb27307a265b240c97477a856c133e84203a0c02abb01d6d4f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 103. logging – it_0103

Ausgearbeitet und strukturell geprüft: 683 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6395 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/howto/logging.html#a-simple-example
- https://docs.python.org/3.13/library/logging.html#logging.Formatter
- https://docs.python.org/3.13/library/logging.html#logging.Logger

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Dateilogs, Logrotation oder Systemjournalzugriffe ausgeführt; vorhandene Logging-Konfiguration nicht verändert.

Präzisierung gegenüber der Quelle: Katalogbeispiel korrigiert: INFO ist bei voreingestelltem WARNING-Schwellwert nicht sichtbar. Ereignisfelder von automatisch strukturiertem JSON getrennt. Eigener Logger, Handler, Formatter und Schwellwert praktisch im Speicher geprüft.

SHA-256: `71a51afec73fd1b45bdb0d1adbd880034da196f1083758c0198e3e9a8fa8c729`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 104. Linux – it_0104

Ausgearbeitet und strukturell geprüft: 713 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6240 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/intro/about
- https://www.kernel.org/doc/html/latest/admin-guide/README.html
- https://zorin.com/os/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Systeminspektion, Installation, Gerätezugriffe oder praktische Ablaufverfolgung. Ein zunächst gesuchter Zorin-Hilfeartikel lieferte HTTP 404; verwendet wurde die erreichbare offizielle Projektübersicht.

Präzisierung gegenüber der Quelle: Technische Kernelbedeutung und alltägliche Bezeichnung vollständiger Systeme getrennt. Zorin-Beispiel anhand offizieller Projektseite bestätigt; Hardwareunterstützung nicht pauschal behauptet. Gedanklicher Dateizugriff nur als vereinfachte Zuständigkeitsfolge.

SHA-256: `5886e302b49e8beccbb9a0d275d2392bba971bade54186086b306a292efcf6de`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 105. Distribution – it_0105

Ausgearbeitet und strukturell geprüft: 676 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6278 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.en.html
- https://www.debian.org/intro/about
- https://www.debian.org/releases/
- https://zorin.com/os/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktives Gedankenbeispiel, keine Installation oder Bestandsabfrage. Ubuntu-about-Abruf lieferte HTTP 503; verwendet wurden erreichbare Debian- und Zorin-Primärquellen.

Präzisierung gegenüber der Quelle: Distribution als abgestimmte und gewartete Zusammenstellung statt bloßer Oberfläche erklärt. Debian-spezifische Releasezweige und APT-Beispiele nicht verallgemeinert; Zorin-Grundlage anhand offizieller Seite geprüft.

SHA-256: `b5d729e0511b2577bc0ba64e0d60a2019c474458fb8c050a5dd7a3f7dd3532cb`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 106. Kernel – it_0106

Ausgearbeitet und strukturell geprüft: 712 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6280 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.kernel.org/admin-guide/mm/concepts.html
- https://docs.kernel.org/scheduler/sched-design-CFS.html
- https://docs.kernel.org/userspace-api/index.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Gedankenbeispiel ohne Ressourcenmessung, Kernel-, Treiber- oder Parameteränderungen.

Präzisierung gegenüber der Quelle: Allgemeine Kernaufgaben von Linux-Ausprägungen und konkreten Scheduler-Versionen getrennt. Virtuelle Speicherverwaltung mit Hardwarevoraussetzung erläutert; Benutzerraum und Administratorrechte nicht gleichgesetzt.

SHA-256: `bb0db9011e5b345fdc461dfa149f7c04fcc491ce693c77f0bdab01f6f18417bb`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 107. Shell – it_0107

Ausgearbeitet und strukturell geprüft: 709 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6031 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html
- https://www.gnu.org/software/bash/manual/html_node/What-is-a-shell_003f.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine interaktive Sitzung, kein Profil, keine Fremdeingaben und keine umfassende POSIX-Konformitätsprüfung.

Präzisierung gegenüber der Quelle: Shell als Befehlsinterpreter und Programmiersprache auch ohne interaktive Eingabe präzisiert. POSIX-Sprache von Bash-Erweiterungen getrennt. Lokale /bin/sh mit fester Variablenzuweisung, Quotierung und printf praktisch geprüft.

SHA-256: `86eeb0f8fb9d055959735c41bc6d35ff9910cb2a196c2dd4f0372465eec8ad55`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 108. Terminal – it_0108

Ausgearbeitet und strukturell geprüft: 710 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6071 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://help.gnome.org/gnome-terminal/introduction.html
- https://invisible-island.net/xterm/xterm.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Ausschließlich Gedankenbeispiel, keine interaktive Sitzung und keine Tastatur-, Profil- oder Prozessänderungen.

Präzisierung gegenüber der Quelle: Terminalemulator und Shell getrennt; auch andere interaktive Programme und textuelle Oberflächen möglich. Konkrete GNOME-/xterm-Eigenschaften nicht pauschal auf alle Terminalprogramme übertragen.

SHA-256: `0636798f3039722d6e2bf606470e1e55d79b420ddce13be1ac776bd14a46e08a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 109. Bash – it_0109

Ausgearbeitet und strukturell geprüft: 689 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6029 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.gnu.org/software/bash/manual/html_node/Arrays.html
- https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html
- https://www.gnu.org/software/bash/manual/html_node/What-is-Bash_003f.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine interaktive Sitzung, Benutzerdateiänderung oder Prüfung aller Startmodi; zusätzliche Shells nicht getestet.

Präzisierung gegenüber der Quelle: Bash von Shell-Oberbegriff, Terminal und sh getrennt. Indiziertes Array und quotierte Weitergabe anhand offizieller Dokumentation erklärt. Eigener Unterprozess mit ausgeschlossenem BASH_ENV und festen Werten praktisch geprüft.

SHA-256: `5e7dd2e81bda21d4c9f1346fb22b5355aed44d6277d80a23ea0f289ebde94a67`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 110. sudo – it_0110

Ausgearbeitet und strukturell geprüft: 697 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6221 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/sudo-project/sudo/main/docs/sudo.mdoc.in
- https://raw.githubusercontent.com/sudo-project/sudo/main/docs/sudoers.mdoc.in
- https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.en.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine sudo-Ausführung, Authentifizierung, Konten-/Richtlinienabfrage oder Paketaktion. sudo.ws-Handbuchabruf lieferte HTTP 403; beide offiziellen Handbuchquellen aus sudo-project/sudo waren erreichbar.

Präzisierung gegenüber der Quelle: sudo nicht auf root beschränkt; Richtlinie, Authentifizierung und Zielidentität getrennt. Quellbeispiel apt update als Aktualisierung der Paketinformationen präzisiert. Offizielle Handbuchquellen statt nicht abrufbarer Website verwendet.

SHA-256: `f661c944d93c0759b28cc91add9ad3473721b942cf9ebf13a3d272e906be39e2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 111. Root – it_0111

Ausgearbeitet und strukturell geprüft: 671 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6015 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man7/capabilities.7.html
- https://man7.org/linux/man-pages/man7/user_namespaces.7.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Gedankenbeispiel ohne Kontenabfrage, Identitätswechsel, Root-Aufruf, Namensraumexperiment oder Systemänderung.

Präzisierung gegenüber der Quelle: Root über UID und Prozessrechte erklärt; pauschales fast alles durch Linux-Capabilities und Benutzer-Namensräume präzisiert. Benutzerkonto von Kernel und Wurzelverzeichnis getrennt.

SHA-256: `bada5ec2730383c9aa5a7a4258163d8c53504d857fdf90e648d21c9aaebd5a39`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 112. Dateirechte – it_0112

Ausgearbeitet und strukturell geprüft: 709 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6056 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man7/path_resolution.7.html
- https://www.gnu.org/software/coreutils/manual/html_node/Mode-Structure.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Identitätswechsel, ACL-, Lösch- oder Fremdbenutzer-Zugriffstests. GNU-Quelle zunächst HTTP 503, beim unveränderten erneuten Abruf HTTP 200.

Präzisierung gegenüber der Quelle: Datei- und Verzeichnisbedeutung der Rechte getrennt; 755 nicht als universelle Empfehlung ausgegeben. Tatsächliche 0640-Modusbits einer eigenen temporären Datei geprüft, keine fremde Benutzerrolle simuliert.

SHA-256: `738957ddcca071e5bf0625ed0fc35959f68d934b96e32d602a79c17327f01c07`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 112 – 21.11.2026

Tatsächlicher Stand: **112 von 302** ausgearbeitet und strukturell geprüft; 190 fehlen. Nächster Datensatz: **it_0113 – chmod**. Die Fortsetzungsfreigabe gilt weiterhin bis 302; dies ist ein Sicherungspunkt, keine Abschlussmeldung oder Gesamtzusammenfassung.

Branch: `codex/linux-glossar-011-302`. Ausgangscommit dieses Durchlaufs: `b6c38afbcbe9957c7921e27f4efe9bdbff6a593c` (80 Einträge). Die zunächst gespeicherten Einträge 81–82 wurden auf Svens Auftrag zuerst mit `21a3c95d121e8356e612af5bee2249ea6c005cff` committet und gepusht. Danach wurden 83–112 einzeln recherchiert, geschrieben, geprüft und unmittelbar in Index und Fortschritt gesichert.

Gesamtprüfung erfolgreich: alle 112 Dokumente samt tatsächlichen SHA-256-Prüfsummen, Originalzuordnung, vollständigen Metadaten, Hauptabschnitten, geschlossenen Codeblöcken, Parserlimits und internen Verweisen. Indexfelder und Datensatzschema unverändert; records lückenlos, documented_records 112, source_urls sortierte duplikatfreie Vereinigung. Quelle weiterhin bytegetreu mit dem vereinbarten SHA-256 und 302 eindeutigen IDs und Begriffen. Alle Dokumente 1–82 sowie ihre Indexdatensätze gegenüber 21a3c95 unverändert; die zehn Pilottexte zusätzlich unmittelbar gegen Pilotcommit 688a832 geprüft. PROMPT.md unverändert. Interne Linkbeschriftungen der neuen Texte auch semantisch gegen die Originalbegriffe geprüft.

Alle 93 vollständigen Python-Beispiele des Gesamtstands erneut erfolgreich ausgeführt: Assertions, Exitcodes und Standardausgaben stimmen. In 83–112 sind es 22 ausgeführte Python-Beispiele und acht reine Gedankenbeispiele. Drei der neuen Beispiele nutzen den bereits vorhandenen virtuellen X-Bildschirm für eigene Tk-Kontexte; keine Installation und keine NetMon-/Reader-Abnahme. Nicht ausgeführte Teile, darunter PyQt, privilegierte Aktionen und reale Systemkonfigurationen, sind ausdrücklich im jeweiligen Eintrag gekennzeichnet. Der Reader-Glossarparser fehlt weiterhin; nur temporäre kompatible Prüfköpfe im Arbeitsspeicher des vorhandenen Markdown-Parsers verwendet.

Der geprüfte Änderungsumfang dieses Sicherungspunkts umfasst ausschließlich 30 neue Glossartexte, index.json und FORTSCHRITT.md unter docs/linux-glossar/. git diff --check erfolgreich. Fachliche Zweitprüfung und lokale Reader-Prüfung der neuen Texte stehen aus; Status review_pending bleibt erhalten. Kein Merge, kein Force-Push und keine Veröffentlichung der Cloud-Umgebung.

## 113. chmod – it_0113

Ausgearbeitet und strukturell geprüft: 698 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6114 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.gnu.org/software/coreutils/manual/html_node/Symbolic-Modes.html
- https://www.gnu.org/software/coreutils/manual/html_node/chmod-invocation.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Datei nicht gestartet; keine fremde Benutzerrolle, symbolischen Links oder rekursiven Aufrufe getestet. GNU-Quelle nach einmaligem HTTP 503 unverändert erneut erfolgreich abgerufen.

Präzisierung gegenüber der Quelle: Quellbeispiel +x um ausdrückliche Benutzerklasse u+x und umask-Einfluss präzisiert. Modusänderung von Programmgültigkeit und Eigentümerschaft getrennt. Tatsächliche chmod-Aufrufe ausschließlich an eigener temporärer Datei geprüft.

SHA-256: `7ba0beb0650ae5f34e50a04e57f33af74b702ccb9dc0da874b2ab15bdef2befc`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 114. chown – it_0114

Ausgearbeitet und strukturell geprüft: 687 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5903 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man2/chown.2.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/chown.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktives Gedankenbeispiel; keine Eigentümer-, Gruppen- oder Kontenänderung. GNU-Einzel- und Gesamthandbuchabrufe lieferten HTTP 503, erreichbare POSIX- und Linux-Primärquellen verwendet.

Präzisierung gegenüber der Quelle: Eigentümer- und Gruppenzuordnung von Modusbits und Kontenverwaltung getrennt. Linux-Berechtigung zur Eigentümerübertragung anhand chown(2) präzisiert; POSIX-Syntax für owner:group verwendet.

SHA-256: `3498110894524c84f7a830aa32c6d82001e95120f76d10f0a39c973d8c4ae193`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 115. Prozess – it_0115

Ausgearbeitet und strukturell geprüft: 701 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6053 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/subprocess.html#subprocess.run
- https://man7.org/linux/man-pages/man2/execve.2.html
- https://man7.org/linux/man-pages/man2/fork.2.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Prozessliste, fremden Prozesse, Signale, Parallelitätsmessung oder Speicherisolationsprüfung.

Präzisierung gegenüber der Quelle: Prozess von Programmdatei, CPU-Aktivität, Thread und Dienst getrennt. fork als konkrete Schnittstelle und execve als Programmbildwechsel erläutert. Ausschließlich eigenen Kindprozess mit Elternbeziehung und Ergebnis praktisch geprüft.

SHA-256: `ea67fc04ab18945a8f9ddc6fca56d0a368fdcb231e30523a4d513d85dd449e94`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 116. PID – it_0116

Ausgearbeitet und strukturell geprüft: 710 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6065 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man1/kill.1.html
- https://man7.org/linux/man-pages/man2/getpid.2.html
- https://man7.org/linux/man-pages/man2/kill.2.html
- https://man7.org/linux/man-pages/man7/pid_namespaces.7.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Reines Gedankenbeispiel mit erfundenen PIDs; keine Prozessliste, keine Signaloperation und kein Beenden von Prozessen.

Präzisierung gegenüber der Quelle: Eindeutigkeit auf Zeit und PID-Namensraum eingegrenzt. Katalogbehauptung kill beendet korrigiert: Signalübermittlung, Berechtigung und tatsächliches Ende getrennt; TERM gemäß Handbuch erläutert.

SHA-256: `99d5b7ce724e4060ccf8b01fe8c3d4f6652808574bfa6f96a7ac793be30271c9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 117. Daemon – it_0117

Ausgearbeitet und strukturell geprüft: 706 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6026 UTF-8-Bytes; 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.freedesktop.org/software/systemd/man/latest/daemon.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktives Gedankenbeispiel ohne Einrichtung, Überwachung, Dienststart, Statusabfrage oder Konfigurationsänderung.

Präzisierung gegenüber der Quelle: Daemonrolle von beliebigem Hintergrundprozess und Service-Verwaltung getrennt. Klassische Selbstablösung nicht als universelle Pflicht dargestellt; modernes systemd-Modell anhand offizieller Dokumentation erläutert.

SHA-256: `f1d9c35988efba456c73bd53f084dfbd78dfe03df2286e7308b311a3924692d6`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 118. systemd – it_0118

Ausgearbeitet und strukturell geprüft: 691 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6108 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktive Statuserläuterung; kein systemctl-Aufruf, keine Unit-Dateiänderung und kein Start oder Neustart.

Präzisierung gegenüber der Quelle: Systemmanager, Benutzermanager und systemctl getrennt. Unit-Typen, Abhängigkeit gegenüber Reihenfolge sowie active gegenüber enabled erläutert. Katalogname ssh nicht als distributionsübergreifend garantiert dargestellt.

SHA-256: `e37c15cfb2769c1b5546fb1edb98525130a08a6323aa5c82a1f8f95ad82b1327`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 119. Service – it_0119

Ausgearbeitet und strukturell geprüft: 711 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6228 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- https://www.networkmanager.dev/docs/api/latest/NetworkManager.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur Gedankenbeispiel; keine Statusabfrage, Unit-Erstellung, Dienst- oder Netzwerkaktion.

Präzisierung gegenüber der Quelle: Service nicht auf dauerhaft laufenden Hintergrundprozess beschränkt; systemd-oneshot-Modell und fachliche Funktion vom Managerstatus getrennt. NetworkManager-Aufgabe anhand offizieller Projektbeschreibung bestätigt.

SHA-256: `c7e13a3f06449a95ee633ddc2dda08044f371ef7707c038cc7e495245855f581`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 120. Logdatei – it_0120

Ausgearbeitet und strukturell geprüft: 692 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6327 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/logging.handlers.html#logging.FileHandler
- https://man7.org/linux/man-pages/man8/logrotate.8.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine vorhandenen Logs, Zeitabgleiche, Rotation, Parallel-Schreibzugriffe oder Ausfalltests; temporäre Datei ausschließlich eigene Meldungen.

Präzisierung gegenüber der Quelle: Logdatei von vollständiger Ablaufaufzeichnung und Sicherung getrennt; /var/log nicht als universeller Speicherort dargestellt. Eigene UTF-8-Logdatei mit zwei Meldungen geschrieben und vollständig zurückgelesen.

SHA-256: `b4efaa3292b26826fc2c335bf8a25e31efeb4c55a4485dc020d1053d8d58b22e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 121. syslog – it_0121

Ausgearbeitet und strukturell geprüft: 673 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6022 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc5424.html
- https://www.rfc-editor.org/rfc/rfc5425.html
- https://www.rsyslog.com/doc/configuration/modules/omfile.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Erfundene RFC-5424-Zeile nicht gesendet und nicht durch einen Empfänger validiert; keine lokalen Logs oder Netzwerkdienste verändert.

Präzisierung gegenüber der Quelle: syslog von einzelner Datei und Implementierung getrennt, nicht auf Linux beschränkt. RFC-5424-Format und TLS-Transportzuordnung unterschieden; rsyslog-Dateiausgabe als konfigurationsabhängig erläutert.

SHA-256: `db22abc03c5974cc65b09b8cff4a0e9c739b953710ee4d8fd7419fa178f2d544`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 122. Journal – it_0122

Ausgearbeitet und strukturell geprüft: 688 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6091 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.freedesktop.org/software/systemd/man/latest/journalctl.html
- https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.service.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. journalctl nicht ausgeführt; keine vorhandenen Logs gelesen, keine Speicher-, Rechte- oder Dienstkonfiguration verändert.

Präzisierung gegenüber der Quelle: Journal, journald und journalctl getrennt; Speicherung nicht pauschal dauerhaft oder unbegrenzt. Dateisystemjournal als andere Wortbedeutung abgegrenzt. Filtermuster mit ausdrücklich fiktiver Unit erläutert.

SHA-256: `0261931136352b30ed5b0cf85eb8c8bcee9678f1a523aeef811c23ce6f484a62`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 123. Paketmanager – it_0123

Ausgearbeitet und strukturell geprüft: 667 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6030 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.fedoraproject.org/en-US/quick-docs/dnf/
- https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.en.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktiver Paketplan, keine Paketabfrage, Installation, Aktualisierung, Entfernung oder Quellenänderung.

Präzisierung gegenüber der Quelle: Paketmanager über Suche, Bestand und Abhängigkeiten erklärt; Paketinformationen aktualisieren von Softwareaktualisierung getrennt. Systempakete, Python-Importpakete und pip-Zuständigkeit auseinandergehalten.

SHA-256: `0cbb62da388be842bacc183fc32ef55fbbf003919c1aca8fe4733ea7c104a27a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 124. APT – it_0124

Ausgearbeitet und strukturell geprüft: 665 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6060 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://manpages.debian.org/trixie/apt/apt-get.8.en.html
- https://manpages.debian.org/trixie/apt/apt-secure.8.en.html
- https://manpages.debian.org/trixie/apt/apt.8.en.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Kein apt/apt-get-Aufruf, keine Paketlistenabfrage oder -aktualisierung, keine Installation, Entfernung oder Quellenänderung.

Präzisierung gegenüber der Quelle: APT-Familie von apt-Programm und DEB-Format getrennt; update, install und upgrade präzisiert. Bereits erfüllten Installationsauftrag und Vertrauenskette ohne Qualitätsgarantie erläutert; versionsgebundene Debian-trixie-Handbücher verwendet.

SHA-256: `a9220ced9971e185cec0ffacf738f9243fae454f8a911e7f40755fcfbe0b506e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 125. DEB – it_0125

Ausgearbeitet und strukturell geprüft: 645 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5971 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html
- https://manpages.debian.org/trixie/dpkg/dpkg-deb.1.en.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur vereinfachtes Gedankenbild; kein Paket gebaut, heruntergeladen, entpackt, untersucht oder installiert und keine bestehende Paketierung verändert.

Präzisierung gegenüber der Quelle: DEB als Binärpaketformat auch für Skripte und Daten erklärt; Formatkennung, Kontroll- und Datenarchiv von Paket-/Anwendungsversion getrennt. NetMon-Quellbeispiel nicht als tatsächlicher Paketierungsnachweis übernommen.

SHA-256: `0250ec4b82338a9715c0e80a41f1634caf76c6c14e4c9f8246f47932bbeb3a8d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 125 – 21.11.2026

**125 von 302** ausgearbeitet und strukturell geprüft; 177 fehlen. Nächster Datensatz: **it_0126** (Originalbegriff bei der Fortsetzung aus dem Katalog lesen). Die Freigabe bis 302 bleibt bestehen. Dies ist ein weiterer Sicherungspunkt und keine Gesamtabschlussmeldung.

Ausgangspunkt dieses Abschnitts: `215643f28d7dcb351dc595a3c5c3fff38acb9682` auf `codex/linux-glossar-011-302`. Die 13 Einträge 113–125 wurden jeweils einzeln recherchiert, geschrieben, praktisch beziehungsweise als Gedankenmodell geprüft und unmittelbar in Index und Fortschritt gesichert.

Gesamtprüfung aller 125 Dokumente erfolgreich: Quelle mit unveränderter vereinbarter SHA-256 und 302 eindeutigen Originaldatensätzen, Metadaten und Kategorieableitung, Reihenfolge, Indexzuordnung, tatsächliche Dokumentprüfsummen, zehn Hauptabschnitte, Codeblöcke, Parserlimits und interne Verweise. Alle 96 vollständigen Python-Beispiele des Gesamtstands erneut erfolgreich ausgeführt. Die jüngsten 13 Texte enthalten drei praktische Python-Beispiele (eigene chmod-Testdatei, eigener Kindprozess, eigene Logdatei) und zehn ausdrücklich nicht ausgeführte Gedankenbeispiele. Keine privilegierten Aktionen oder Änderungen an bestehenden Dateien, Konten, Geräten, Diensten, Netzwerken oder Paketbeständen.

Alle vorherigen Dokumente 1–112 und ihre Indexdatensätze gegenüber 215643f unverändert; die Pilottexte zusätzlich gegen den ursprünglichen Pilotcommit geprüft. Neue interne Linkbeschriftungen auch gegen Originalbegriffe geprüft. Änderungen ausschließlich 13 neue Glossartexte sowie index.json und FORTSCHRITT.md; git diff --check erfolgreich. Keine neue Reader-Anbindung oder unabhängige Inhaltsabnahme behauptet; review_pending bleibt erhalten.

## 126. Repository – it_0126

Ausgearbeitet und strukturell geprüft: 689 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6212 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://manpages.debian.org/trixie/apt/sources.list.5.en.html
- https://raw.githubusercontent.com/git/git/master/Documentation/gitrepository-layout.adoc

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur Gedankenvergleich. Kein Repository, keine Paketquelle oder Git-Konfiguration angelegt oder verändert. git-scm-Handbuchabruf HTTP 403; offizielle Handbuchquelldatei aus git/git erfolgreich geprüft.

Präzisierung gegenüber der Quelle: Paketquelle und Git-Repository ausdrücklich getrennt; Git nicht mit GitHub, Arbeitsverzeichnis oder Backup gleichgesetzt. Bare-Repositories und mögliche .git-Verweisdatei anhand offizieller Git-Dokumentation präzisiert.

SHA-256: `30a434a03e11ccfcd030a66c17ec1d83e9c9d415a793fcba241cf106e860ba04`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 127. Lockfile – it_0127

Ausgearbeitet und strukturell geprüft: 691 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6223 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/fcntl.html#fcntl.flock
- https://man7.org/linux/man-pages/man2/flock.2.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein Mehrprozessstart, NetMon-Test, Netzwerkdateisystem oder Entfernen fremder Lockfiles.

Präzisierung gegenüber der Quelle: Dateiexistenz von korrektem Sperrverfahren getrennt; flock, PID-File und Abhängigkeits-Lockfile unterschieden. Zwei unabhängige Öffnungen einer eigenen temporären Datei geprüft; kein NetMon-Single-Instance-Nachweis behauptet.

SHA-256: `78dd37f8ce11d0cedfc88eed75234e7af8ba5efbe0786d7875ef96d7875d0a0b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 128. Cron – it_0128

Ausgearbeitet und strukturell geprüft: 679 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5865 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man5/crontab.5.html
- https://man7.org/linux/man-pages/man8/cron.8.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Beispielzeile nur erklärt; keine Crontab gelesen, eingerichtet oder verändert, kein Dienst oder zeitgesteuerter Auftrag ausgeführt.

Präzisierung gegenüber der Quelle: Zeitplanung von erfolgreicher Ausführung und Nachholen getrennt; Benutzer- und Systemtabellen unterschieden. Cronie als konkrete Implementierungsquelle genannt, Zeitumstellungen und Ausführungsumgebung nicht verallgemeinert.

SHA-256: `50c66415d328cb0aeddfd8676e8145ddd66926087887b05a8e0bb607afee8a0e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 129. Socket – it_0129

Ausgearbeitet und strukturell geprüft: 667 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6115 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/socket.html#socket.socketpair
- https://man7.org/linux/man-pages/man7/socket.7.html
- https://man7.org/linux/man-pages/man7/unix.7.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Beide Endpunkte im selben Prüfprozess; keine Ports, DNS-Abfragen, fremden Dienste, Netzwerk- oder Mehrprozessabnahme.

Präzisierung gegenüber der Quelle: Socket als Endpunkt statt Port oder zwingender Internetverbindung erklärt; AF_UNIX und Stream-Grenzen anhand offizieller Quellen präzisiert. Eigene lokale Socket-Paar-Anfrage und Antwort mit längengeprüftem Empfang praktisch getestet.

SHA-256: `ab1f3dc25140629c16c9252d0d1c918689264824156c90f7e04d1d4c5bc94317`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 130. Pipe – it_0130

Ausgearbeitet und strukturell geprüft: 702 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6198 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/subprocess.html#replacing-shell-pipeline
- https://man7.org/linux/man-pages/man7/pipe.7.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine ls-/grep-Auswertung realer Dateien, keine FIFO, großen Datenmengen oder vorzeitig abbrechenden Gegenstellen getestet.

Präzisierung gegenüber der Quelle: Pipe als begrenzten unidirektionalen Bytestrom erläutert, nicht als semantischen Dateifilter. Shell-Pipeline und direkte Prozessverkettung getrennt; eigener Erzeuger und Verarbeiter praktisch verbunden und beide Exitcodes geprüft.

SHA-256: `f1e754f16a155f227af3828adbcf9ba86633719aba12c5e3ccc6ce3960d7197c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 131. Umgebungsvariable – it_0131

Ausgearbeitet und strukturell geprüft: 707 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6270 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/os.html#os.environ
- https://docs.python.org/3.13/library/subprocess.html#subprocess.run
- https://man7.org/linux/man-pages/man7/environ.7.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Startdateien, dauerhaften Umgebungswerte oder Dienst-/Desktopkonfigurationen verändert; keine vorhandenen Umgebungsinhalte ausgegeben.

Präzisierung gegenüber der Quelle: Umgebung als prozessbezogene Textzuordnung statt globaler Variablentabelle präzisiert; Shell-Export und normale Programmiervariablen getrennt. Eigenen Wert nur in kopierter Kindumgebung gesetzt und unveränderten Elternwert geprüft.

SHA-256: `f51b9b30856d6117cc1b1b0c91eb87e53b9460a1f4550bacb5b73da6a5d0f95d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 132. PATH – it_0132

Ausgearbeitet und strukturell geprüft: 719 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6381 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/shutil.html#shutil.which
- https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap08.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Testdateien nicht gestartet, tatsächliche PATH-Variable nicht gelesen oder geändert; keine Startdateien oder dauerhaften Umgebungen bearbeitet.

Präzisierung gegenüber der Quelle: PATH als geordnete Suchliste und nicht alleinige Fehlerursache präzisiert. Shell-interne Auswahl von Dateisuche abgegrenzt. Zwei eigene gleichnamige Dateien über explizite Suchlisten in wechselnder Reihenfolge gefunden.

SHA-256: `6dc384a14c59d43265da49f055806e619b2f71f47446b7e80be480c3c35966ae`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 133. Home-Verzeichnis – it_0133

Ausgearbeitet und strukturell geprüft: 704 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6152 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.home
- https://man7.org/linux/man-pages/man5/passwd.5.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Pfade; keine Konten- oder Verzeichnisabfrage, kein Path.home-Aufruf, keine persönlichen Daten und kein Verzeichniswechsel.

Präzisierung gegenüber der Quelle: Home von Arbeits-, Projekt- und Wurzelverzeichnis getrennt; /home/sven nicht als universelle Regel ausgegeben. Kontenzuordnung, HOME-Umgebung und tatsächliche Rechte unterschieden.

SHA-256: `f6f9a3c4dcde825baec62d1f94e2cf9ef701154ad3f765d635949f987cdc1287`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 134. Mount – it_0134

Ausgearbeitet und strukturell geprüft: 723 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6047 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man2/mount.2.html
- https://man7.org/linux/man-pages/man7/mount_namespaces.7.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktive Struktur; keine Geräteabfrage, Mount-/Unmount-Operation, Namensraum- oder Dateisystemänderung.

Präzisierung gegenüber der Quelle: Mount von Formatieren und Kopieren getrennt; Quelle nicht auf physischen Datenträger beschränkt. Verdeckte Inhalte und prozessbezogene Mount-Namensräume anhand Linux-Dokumentation erläutert.

SHA-256: `462e3d903a6badc8026e081a3462a2a87b58189e16923e493c52d7cd6c1d72f9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 135. Symlink – it_0135

Ausgearbeitet und strukturell geprüft: 699 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5902 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.symlink_to
- https://man7.org/linux/man-pages/man7/symlink.7.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine fremden Dateien, Systemlinks, Linkschleifen, rekursiven Änderungen oder Mount-Aktionen getestet.

Präzisierung gegenüber der Quelle: Symlink als gespeicherten Zielpfad statt Kopie oder Desktop-Verknüpfung erklärt. Relative Zielauflösung und gebrochene Links unterschieden. Eigener relativer Link und eigener Link ohne Ziel praktisch geprüft.

SHA-256: `934f137ba7a1880189883c99a553bd2986b0c190fb88199aa89b613ce504df5e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 135 – 21.11.2026

**135 von 302** ausgearbeitet und strukturell geprüft; 167 fehlen. Nächster Datensatz: **it_0136 – Shebang**. Die Freigabe bis 302 bleibt bestehen; keine Gesamtabschlussmeldung.

Ausgangspunkt dieses Abschnitts: `b3a3c5d8ea0222b877cccf87945e970e0d8ebd1d` auf `codex/linux-glossar-011-302`. Zehn Texte 126–135 einzeln recherchiert, geschrieben und nach jeweiliger Prüfung in Index und Fortschritt gespeichert.

Alle 135 Dokumente und Indexzuordnungen erneut geprüft: unveränderte Quelle mit vereinbarter SHA-256 und 302 eindeutigen Originaldatensätzen; Metadaten, Kategorieableitung, lückenlose Reihenfolge, ursprüngliches Indexschema, tatsächliche Dokumentprüfsummen, zehn Hauptabschnitte, geschlossene Codeblöcke, Parserlimits und interne Verweise. Quellenvereinigung weiterhin sortiert und duplikatfrei. Neue Linkbeschriftungen gegen Originalbegriffe verglichen.

Alle 102 vollständigen Python-Beispiele des Gesamtstands erneut erfolgreich ausgeführt, einschließlich Assertions, Exitcodes und dokumentierten Standardausgaben. In 126–135 sind sechs praktische Beispiele und vier Gedankenmodelle enthalten. Praktisch wurden nur eigene temporäre Daten, lokale Unix-Socket-Paare, eigene kurzlebige Kindprozesse und explizite Suchpfadkopien verwendet. Kein Netzwerkport oder fremder Dienst angesprochen, keine Konten-, Mount-, Paket-, Profil- oder Dienständerung. Das PATH-Beispiel startet seine Testdateien nicht und verändert die tatsächliche PATH-Variable nicht. Der Lockfile-Test prüft eigene Dateideskriptoren, keine NetMon-Eininstanzabnahme.

Dokumente 1–125 und ihre Indexdatensätze gegenüber b3a3c5d unverändert; Pilottexte zusätzlich gegen ursprünglichen Pilotcommit geprüft. PROMPT.md unverändert. Nur zehn neue Glossartexte, index.json und FORTSCHRITT.md geändert; git diff --check erfolgreich. Unabhängige Inhaltsprüfung und lokale Reader-Abnahme der neuen Texte bleiben offen. Alle neuen Statuswerte bleiben review_pending.

## 136. Shebang – it_0136

Ausgearbeitet und strukturell geprüft: 665 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6001 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/tutorial/appendix.html#executable-python-scripts
- https://man7.org/linux/man-pages/man2/execve.2.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/env.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Katalogvariante mit /usr/bin/env python3 und andere Plattformen nicht ausgeführt; keine vorhandenen Skripte, Installationen oder Suchpfade verändert.

Präzisierung gegenüber der Quelle: Shebang von Endung und explizitem Interpreteraufruf getrennt; env-Variante als umgebungsabhängige Suche präzisiert. Eigenes Skript mit tatsächlichem System-Interpreter im Shebang direkt gestartet und Ausgabe geprüft.

SHA-256: `ec78ec50be5b924d8c9854a4e50b1e86152188e84fa85d52366640bde111f6fe`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 137. Exit-Code – it_0137

Ausgearbeitet und strukturell geprüft: 683 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6196 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/subprocess.html#subprocess.CompletedProcess.returncode
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/grep.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein grep, Signalversuch oder Zugriff auf Fremddaten; beide Unterprozesse ausdrücklich nach eigener Statusvereinbarung ausgewertet.

Präzisierung gegenüber der Quelle: Nichtnullen Status von Bug und fachlichem Fehler getrennt; grep-Konvention und Pythons negative Signalrepräsentation eingeordnet. Eigene Such-Kindprozesse mit erwartetem Status 0 und 1 samt leeren Ausgabekanälen geprüft.

SHA-256: `f8d90c53e1c1c1296688f92c68c6abb920d368c69e1768258934227dc666c615`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 138. Netzwerk – it_0138

Ausgearbeitet und strukturell geprüft: 702 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6061 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc1122.html
- https://www.rfc-editor.org/rfc/rfc1812.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktives Heimnetz; keine Verbindungsversuche, Scans, Mitschnitte, Geräteabfragen oder Netzwerkkonfigurationsänderungen.

Präzisierung gegenüber der Quelle: Netzwerk von Internet, Funkzugang und Anwendungsfunktion getrennt. TCP/IP-Schichten und IPv4-Routerrolle anhand RFCs eingeordnet, historische Spezifikationen nicht als vollständige heutige Konfigurationsanweisung verwendet.

SHA-256: `929b9a7064de2ab0d6a0e9e54660f58cb19ff50ceb7d5b58d27d6777344ba2c7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 139. IP-Adresse – it_0139

Ausgearbeitet und strukturell geprüft: 672 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6009 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.ip_address
- https://www.rfc-editor.org/rfc/rfc1918.html
- https://www.rfc-editor.org/rfc/rfc3849.html
- https://www.rfc-editor.org/rfc/rfc4291.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine reale Adressvergabe, DNS-Auflösung, Schnittstellenabfrage, Pakete oder Erreichbarkeitsprüfung.

Präzisierung gegenüber der Quelle: Geräteadresse auf kontextabhängige Schnittstellenadressierung präzisiert; mehrere Adressen und private IPv4-Wiederverwendung erläutert. Eigenes IPv4-/Dokumentations-IPv6-Parsing samt Bereich und Schreibweisengleichheit praktisch geprüft.

SHA-256: `be35eb8fdb6ab406232de92941754af63feaa613252d8efa92c985cf33099f46`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 140. IPv4 – it_0140

Ausgearbeitet und strukturell geprüft: 697 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6057 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.IPv4Address
- https://www.rfc-editor.org/rfc/rfc4632.html
- https://www.rfc-editor.org/rfc/rfc5737.html
- https://www.rfc-editor.org/rfc/rfc791.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur Adressberechnung mit reserviertem Dokumentationsbereich; keine Pakete, Schnittstellen-, Routen- oder Gerätekonfigurationsänderung.

Präzisierung gegenüber der Quelle: IPv4 als Protokollversion statt bloß älterem Textformat erklärt. 32-Bit-Adresse, vier Oktette und CIDR-Präfix getrennt; .1 nicht als universellen Routerwert ausgegeben. Dokumentationsadresse, /24-Größe und ungültiges Oktett praktisch geprüft.

SHA-256: `e1dbb3eb640fa94ff7c0eff9c7a19b100e5a3e039eaa3dda2c3a5a1c91f8860c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 140 – 21.11.2026

**140 von 302** ausgearbeitet und strukturell geprüft; 162 fehlen. Nächster Datensatz: **it_0141 – IPv6**. Die Fortsetzungsfreigabe bis 302 bleibt bestehen. Dieser an der Verarbeitungsgrenze gesicherte Stand ist keine Fertigmeldung; die gemeinsame Gesamtzusammenfassung folgt erst nach 302.

Ausgangspunkt dieses Abschnitts: `70f1875a39bd38b1c6b45d1a79280d5f741b3fa4` auf `codex/linux-glossar-011-302`. Die fünf Einträge 136–140 wurden einzeln recherchiert, geschrieben, geprüft und unmittelbar in Index und Fortschritt gespeichert.

Gesamtprüfung erfolgreich für alle 140 Dokumente: unveränderte Originalquelle mit vereinbarter SHA-256 und 302 eindeutigen IDs und Begriffen; tatsächliche Dokumentprüfsummen, Originalzuordnung, vollständige JSON-Metadaten, Kategorieableitung, unverändertes Indexschema, lückenlose Reihenfolge, zehn Hauptabschnitte, geschlossene Codeblöcke, Parserlimits und interne Verweise. Neue Linkbeschriftungen gegen Originalbegriffe geprüft. documented_records 140; source_urls sortierte, duplikatfreie Vereinigung der genauen Eintragsquellen.

Alle 106 vollständigen Python-Beispiele des Gesamtstands erneut erfolgreich ausgeführt: Assertions, Exitcodes und dokumentierte Standardausgaben. Vier neue praktische Beispiele betreffen einen eigenen direkten Skriptstart, eigene Kindprozesse mit erwarteten Statuswerten sowie ausschließlich lokale Adressberechnungen. Das Netzwerk-Gedankenmodell wurde nicht ausgeführt. Keine Netzwerkpakete, DNS-Abfragen, Scans, Schnittstellen-, Geräte-, Konten-, Dienst- oder Paketänderungen. Nicht ausgeführte Varianten sind in den Einträgen und Einzelberichten kenntlich gemacht.

Alle Dokumente 1–135 und ihre Indexdatensätze gegenüber 70f1875 unverändert; Pilottexte zusätzlich gegen den ursprünglichen Pilotcommit geprüft. PROMPT.md unverändert. Änderungsumfang nur fünf neue Glossartexte, index.json und FORTSCHRITT.md; git diff --check erfolgreich. Im gesamten Durchlauf ausschließlich docs/linux-glossar/ geändert. Der vorhandene Markdown-Parser prüft nur die Struktur mit temporärem Kopf im Arbeitsspeicher. Unabhängige Inhaltsprüfung und lokale Reader-Abnahme der neuen Texte bleiben offen; review_pending bleibt erhalten. Kein Merge, Force-Push oder Veröffentlichen der Cloud-Umgebung.

## 141. IPv6 – it_0141

Ausgearbeitet und strukturell geprüft: 656 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5869 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc3849.html
- https://www.rfc-editor.org/rfc/rfc4291.html
- https://www.rfc-editor.org/rfc/rfc5952.html
- https://www.rfc-editor.org/rfc/rfc8200.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur lokale Adressberechnung; keine Schnittstellen, Verbindungen, Pakete oder Netzkonfigurationen verändert.

Präzisierung gegenüber der Quelle: IPv6 als Protokoll statt bloßes Adressformat erklärt; Darstellung, 128-Bit-Wert und Sicherheit getrennt. Dokumentationspräfix, gleichwertige Schreibweisen und unzulässige doppelte Verkürzung geprüft.

SHA-256: `1ca3ea68f1105443e0be0d3c9643fce3bd0ed4aa2d93b99af689164046fe27e5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 142. Port – it_0142

Ausgearbeitet und strukturell geprüft: 701 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5737 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc6335.html
- https://www.rfc-editor.org/rfc/rfc9110.html#section-4.2.1
- https://www.rfc-editor.org/rfc/rfc9293.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktive Tabelle; keine Ports geöffnet, gescannt oder angesprochen und keine Freigaben geändert.

Präzisierung gegenüber der Quelle: Port nicht als zwingende Dienstidentität erklärt; Transport und Adresse einbezogen. HTTP-Standardport und tatsächliche Anwendung getrennt, TCP-Verbindung über Endpunktpaar erläutert.

SHA-256: `b1e300cc91247369d943d8f2646f2fe8ac5931f9fa7b23140da628c579e580c7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 143. TCP – it_0143

Ausgearbeitet und strukturell geprüft: 664 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5943 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc9000.html
- https://www.rfc-editor.org/rfc/rfc9114.html
- https://www.rfc-editor.org/rfc/rfc9293.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur vereinfachtes relatives Byte-Gedankenmodell; kein TCP-Port, keine Paketübertragung oder reale Transportabnahme.

Präzisierung gegenüber der Quelle: Zuverlässigen geordneten Bytestrom von Anwendungserfolg und Nachrichtengrenzen getrennt. HTTPS-Beispiel durch HTTP/3 über QUIC/UDP eingeschränkt, belegt mit RFC 9114 und RFC 9000.

SHA-256: `7f6f26dd8503e9854cdf3b3689cb045980ace41707f788659610e750c2ff0cd4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 144. UDP – it_0144

Ausgearbeitet und strukturell geprüft: 681 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5978 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc9000.html

- https://www.rfc-editor.org/rfc/rfc768.html
- https://www.rfc-editor.org/rfc/rfc7766.html
- https://www.rfc-editor.org/rfc/rfc8085.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktiver Verlauf, kein UDP-Socket oder Netzwerkverkehr; keine Verlust- oder Geschwindigkeitsmessung.

Präzisierung gegenüber der Quelle: Pauschale Geschwindigkeitsaussage korrigiert; Datagrammgrenzen, Verlust, Reihenfolge und Anwendungspflichten getrennt. DNS-Beispiel durch verpflichtende TCP-Unterstützung eingeordnet.

SHA-256: `ecd0d116469a5cdbf7b82c1f71c80f902a0b2e6cf623032ac5e6a5566c6ad97a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 145. HTTP – it_0145

Ausgearbeitet und strukturell geprüft: 694 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5865 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc9110.html
- https://www.rfc-editor.org/rfc/rfc9112.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine HTTP-Anfrage, kein Serverstart und keine fremden Ressourcen abgerufen; Dialog nicht als Netzwerkaufzeichnung ausgegeben.

Präzisierung gegenüber der Quelle: HTTP-Semantik, Inhaltssprache und Transport getrennt; Zustandslosigkeit nicht als Verbot von Sitzungen dargestellt. Fiktiver HTTP/1.1-Dialog mit ausdrücklich nur fünf Körperbytes und nicht bytegenauer Markdown-Darstellung.

SHA-256: `b54133fb72cce0508fc7da2d08f2659efff138c51e6ebbbe956c6c13ee94c151`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 146. HTTPS – it_0146

Ausgearbeitet und strukturell geprüft: 678 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5978 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc8446.html
- https://www.rfc-editor.org/rfc/rfc9110.html#section-4.2.2
- https://www.rfc-editor.org/rfc/rfc9114.html
- https://www.rfc-editor.org/rfc/rfc9525.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktives Modell; kein Handshake, Zertifikat, HTTPS-Anwendungsabruf oder Ändern von Vertrauensablagen.

Präzisierung gegenüber der Quelle: HTTPS um Vertraulichkeit, Integrität und passende Dienstidentität präzisiert; Inhaltsvertrauen und Benutzeranmeldung getrennt. HTTP/3-Ausnahme für TCP berücksichtigt.

SHA-256: `219d3f9f2192b04fd4f6ad2045251f168c9c7db3f32239993e4087a52a5aef8e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 147. TLS – it_0147

Ausgearbeitet und strukturell geprüft: 658 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6170 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ssl.html#ssl.PROTOCOL_TLS_CLIENT
- https://www.rfc-editor.org/rfc/rfc8446.html
- https://www.rfc-editor.org/rfc/rfc9325.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein Handshake, keine Zertifikatsannahme und keine verschlüsselte Verbindung getestet; keine Vertrauensablage oder Systemeinstellung verändert.

Präzisierung gegenüber der Quelle: TLS-Handschlag, Datenschutz, Authentifizierung und Anwendung getrennt; Zertifikate nicht als einziges Verfahren aller TLS-Fälle dargestellt. Nur Zertifikats- und Namensprüfflags eines neuen Python-Clientkontexts praktisch geprüft.

SHA-256: `d0e3a6c27dafd76290d3505f4ffa55d76fbcf3169d5cfd540e18108ffaf58244`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 148. DNS – it_0148

Ausgearbeitet und strukturell geprüft: 681 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5680 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc1034.html
- https://www.rfc-editor.org/rfc/rfc1035.html
- https://www.rfc-editor.org/rfc/rfc3596.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine DNS-Anfrage, Cache-, Zonen- oder Resolverkonfigurationsänderung; keine realen example.com-Adressen behauptet.

Präzisierung gegenüber der Quelle: Name-zu-IP als Teilfunktion präzisiert; Eintragstypen, mehrere Werte, TTL und Transport unabhängig von Antwortadressversion erläutert. Fiktive A-/AAAA-Tabelle statt echter Auflösung.

SHA-256: `36a36cbe06582673f4b9d6b6145d7261bdcf8a1804ab4b98ab371eee8b762827`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 149. Resolver – it_0149

Ausgearbeitet und strukturell geprüft: 721 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6042 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html
- https://www.rfc-editor.org/rfc/rfc9499.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur mögliche fiktive Kette; keine DNS-Anfrage, Systemdatei-, Cache- oder Resolverkonfigurationsabfrage.

Präzisierung gegenüber der Quelle: Stub-, rekursive und autoritative Rollen getrennt. Cacheantwort und systemweite Namensquellen berücksichtigt; erfolgreiche Auflösung nicht mit aktueller DNS-Abfrage oder späterer Erreichbarkeit gleichgesetzt.

SHA-256: `eebca4976aed255ca5dfecdcfcc972a5045a27f5eeadd0559eb5595dff097a04`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 150. Gateway – it_0150

Ausgearbeitet und strukturell geprüft: 684 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5640 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man8/ip-route.8.html
- https://www.rfc-editor.org/rfc/rfc1812.html
- https://www.rfc-editor.org/rfc/rfc5737.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Routingabfrage, Pakete, Gerätezugriffe oder Änderungen von Routen und Netzparametern.

Präzisierung gegenüber der Quelle: Gateway als Rolle und IP-Nächster-Hop erläutert; Standardroute von spezielleren Wegen sowie DNS-Rolle getrennt. Fiktive Dokumentationsnetze statt tatsächlicher Routeradressen verwendet.

SHA-256: `c9c46493a64eebee5eab042f03a026573bff0f606060df34a4e299ebf4d6e480`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Datensatz 150 – 21.11.2026

**150 von 302** ausgearbeitet und strukturell geprüft; 152 fehlen. Nächster Datensatz: **it_0151 – Router**. Fortsetzungsfreigabe bis 302 bleibt bestehen; kein Abschluss und keine Gesamtzusammenfassung.

Tatsächlicher Branch: codex/linux-glossar-011-302. Ausgangscommit dieses Durchlaufs: d0848a417938d150f64f3020650588eadd926964. Zu Beginn war das Arbeitsverzeichnis sauber; erneuter Push bestätigte Everything up-to-date. Danach wurden 141–150 einzeln recherchiert, geschrieben, geprüft und sofort im Index und hier gespeichert. Quellenabruf 21.11.2026, HTTPS mit unveränderter TLS-Prüfung. Keine Unteragenten oder zusätzlichen Worktrees.

Gesamtprüfung aller 150 Dokumente erfolgreich: unveränderte Originalquelle samt vereinbarter SHA-256 und 302 eindeutigen IDs und Begriffen; genaue Originalzuordnung, Metadaten, Kategorieableitung, unverändertes Indexschema, lückenlose Quellreihenfolge, tatsächliche SHA-256-Prüfsummen, zehn Hauptabschnitte, Codeblöcke, Parserlimits und interne Verweise. Linkbeschriftungen der neuen Texte gegen Originalbegriffe geprüft. documented_records 150; source_urls sortierte duplikatfreie Vereinigung. Alle 108 Python-Beispiele des Gesamtstands erneut ausgeführt; Assertions, Exitcodes und Standardausgaben erfolgreich.

Die neuen zehn Texte enthalten zwei praktische Python-Prüfungen (lokale IPv6-Werte und Einstellungen eines eigenen TLS-Kontexts) und acht Gedankenbeispiele. Kein TLS-Handshake oder Netzwerkverkehr in den Praxisbeispielen; keine Ports, Zertifikatsablagen, Resolver- oder Routingkonfigurationen verändert. HTTPS-Quellenrecherche ist davon getrennt. Nicht ausgeführte Modelle ausdrücklich gekennzeichnet.

Dokumente 1–140 und ihre Indexdatensätze gegen d0848a4 unverändert; zehn Pilottexte zusätzlich unmittelbar gegen ursprünglichen Pilotcommit geprüft. PROMPT.md unverändert. Nur zehn neue Glossartexte, index.json und FORTSCHRITT.md geändert; git diff --check erfolgreich. Keine Anwendungscodeänderung, Installation oder Veröffentlichung der Cloud-Umgebung. Unabhängige Inhaltsprüfung und lokale Reader-Abnahme stehen aus; temporärer Prüfkopf im vorhandenen Markdown-Parser ist keine Reader-Abnahme. Alle neuen Texte bleiben review_pending.

## 151. Router – it_0151

Ausgearbeitet und strukturell geprüft: 703 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5787 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc1812.html
- https://www.rfc-editor.org/rfc/rfc3022.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktives Weiterleitungsmodell, keine Pakete, Geräteanmeldung, Routen- oder Freigabeänderung.

Präzisierung gegenüber der Quelle: Routerrolle von Hardwareform, Funkzugang, NAT und Anwendungsproxy getrennt. IPv4-Weiterleitung und TTL anhand RFC 1812 erläutert; Heimgerät nicht als Garantie aller Netzfunktionen dargestellt.

SHA-256: `a86398761ab7d5c27b5e04e2a154d17176f894603b711cf00300b6ce2439f1c2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 152. Subnetz – it_0152

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5653 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.IPv4Network
- https://www.rfc-editor.org/rfc/rfc4632.html
- https://www.rfc-editor.org/rfc/rfc5737.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur lokale Adressrechnung; keine Schnittstellenzuweisung, Geräteabfrage oder Änderung von Netzen, Routen oder Filtern.

Präzisierung gegenüber der Quelle: Subnetz als Präfixbereich statt physischer oder automatischer Sicherheitsgrenze erklärt. Blockgröße von frei nutzbarer Gerätezahl getrennt. Eigenen /24-Dokumentationsblock in vier /26-Blöcke geteilt und Zugehörigkeiten geprüft.

SHA-256: `c4928bc704a85218f7f2942de0ea9cdf1bf57bb80b6e10b0ddf79a6de90a2d7d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 153. CIDR – it_0153

Ausgearbeitet und strukturell geprüft: 660 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5930 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.collapse_addresses
- https://www.rfc-editor.org/rfc/rfc4291.html
- https://www.rfc-editor.org/rfc/rfc4632.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Route, Schnittstelle oder Filterregel eingerichtet; rechnerische Zusammenfassung nicht als reale Erreichbarkeit oder Routingabnahme ausgegeben.

Präzisierung gegenüber der Quelle: CIDR über reine Schreibweise hinaus als klassenloses Zuteilungs- und Aggregationskonzept erklärt. Präfixlänge, Netzgrenze und Schnittstellenadresse getrennt. Zwei passend ausgerichtete /25-Dokumentationsblöcke rechnerisch zusammengefasst.

SHA-256: `7f0d888a8a8e991856b5b4820fa55bd3a9851dd75281b03959c38db32a37aaaa`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 154. MAC-Adresse – it_0154

Ausgearbeitet und strukturell geprüft: 660 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5873 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.networkmanager.dev/docs/api/latest/settings-802-11-wireless.html
- https://www.rfc-editor.org/rfc/rfc9542.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine reale Schnittstelle, Herstellerabfrage, Adresszuweisung oder Netzwerkprofiländerung; keine Eindeutigkeit des Testwerts behauptet.

Präzisierung gegenüber der Quelle: Hardwareadresse nicht als unveränderliche Geräteidentität dargestellt. Verbindungsebene, 48-Bit-Format und lokale/universelle Einordnung präzisiert; NetworkManager-Adresszuweisung anhand offizieller Dokumentation belegt. Eigene Bytes und zwei Adressbits geprüft.

SHA-256: `e9b2e80d5a288fedc8f510ab76c08f058a97d7d6a2d523ae39b33ea492fe846b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 155. ARP – it_0155

Ausgearbeitet und strukturell geprüft: 716 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6016 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man7/arp.7.html
- https://www.rfc-editor.org/rfc/rfc4861.html
- https://www.rfc-editor.org/rfc/rfc826.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Zuordnung; keine ARP-Pakete, Nachbartabellen, Cache- oder Schnittstellenänderungen.

Präzisierung gegenüber der Quelle: ARP auf passende lokale Protokoll-/Verbindungsadresszuordnung eingegrenzt; Route bestimmt nächsten Hop, nicht zwingend finales Ziel. Cache, Identitätsvertrauen und IPv6 Neighbor Discovery getrennt.

SHA-256: `6ecd7c38560e90c19aef59bf5051a94505952ed730648da187e41a4836ed841b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 156. DHCP – it_0156

Ausgearbeitet und strukturell geprüft: 670 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5904 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc2131.html
- https://www.rfc-editor.org/rfc/rfc2132.html
- https://www.rfc-editor.org/rfc/rfc4861.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Nachrichtenfolge; kein Client oder Server gestartet, keine Adresse oder Lease angefordert und keine Netzprofile verändert.

Präzisierung gegenüber der Quelle: DHCP auf Bereitstellung mehrerer Netzwerkparameter erweitert; Heimrouter nur als mögliche Serverrolle. Typischen anfänglichen IPv4-Ablauf von Erneuerung und IPv6-Verfahren getrennt.

SHA-256: `504e7356ab2658d13555d0af069af79b2dbe037f444f28afe122e24c19ef11d7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 157. Ping – it_0157

Ausgearbeitet und strukturell geprüft: 677 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5695 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man8/ping.8.html
- https://www.rfc-editor.org/rfc/rfc4443.html
- https://www.rfc-editor.org/rfc/rfc792.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Ping-Ausführung, öffentlichen oder lokalen Ziele, Verlustmessung oder ICMP-Konfigurationsänderung; Tabelle vollständig fiktiv.

Präzisierung gegenüber der Quelle: Erreichbarkeit auf beobachteten ICMP-Echo-Austausch eingegrenzt; fehlende Antwort nicht mit sicherem Geräteausfall gleichgesetzt. RTT von Einwegzeit, Bandbreite und Anwendungsfunktion getrennt.

SHA-256: `cdb50dc08dd7fb37bfef586dc62eeccedd2402fe8ead0e1dff68a12b4844c9a1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 158. Traceroute – it_0158

Ausgearbeitet und strukturell geprüft: 699 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5881 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man8/traceroute.8.html
- https://www.rfc-editor.org/rfc/rfc1812.html
- https://www.rfc-editor.org/rfc/rfc4443.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Traceroute-, Ping- oder DNS-Anfrage; fiktive Tabelle ohne echte Zwischenstationen oder gemessene Laufzeiten.

Präzisierung gegenüber der Quelle: Weganzeige als methoden- und zeitabhängige Probe interpretiert; Sternchen nicht als sicherer Defekt. RTT je Probe von Einzelsegmentlaufzeit getrennt, IPv4-TTL und IPv6-Hop-Limit eingeordnet.

SHA-256: `d5013dd60b4c742496eaec296274e72b491a5c9b5093b8b67766cd27a86c0752`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 159. Firewall – it_0159

Ausgearbeitet und strukturell geprüft: 682 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5859 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://firewalld.org/documentation/concepts.html
- https://wiki.nftables.org/wiki-nftables/index.php/Netfilter_hooks

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur erfundene Richtlinientabelle; keine Regeln, Statusabfragen oder Freigabeänderungen. NIST-Übersichtsabruf HTTP 403; erreichbare offizielle Projektquellen verwendet.

Präzisierung gegenüber der Quelle: Firewall von Routing, NAT, Verschlüsselung und Anmeldung getrennt. Lokale Eingabe, Ausgabe und Weiterleitung sowie Zustandsbezug anhand offizieller firewalld-/nftables-Dokumentation erläutert.

SHA-256: `b707fecb27171e5d0234f0604985caabfd987bedbffd7de2611ad135c3c5d56a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 160. NAT – it_0160

Ausgearbeitet und strukturell geprüft: 655 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5955 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc2663.html
- https://www.rfc-editor.org/rfc/rfc3022.html
- https://www.rfc-editor.org/rfc/rfc5737.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Übersetzungstabelle gelesen, Pakete, Portweiterleitungen oder Änderungen von NAT, Firewall oder Geräten.

Präzisierung gegenüber der Quelle: NAT nicht auf privat-zu-öffentlich eingeengt; Basic NAT und NAPT unterschieden. Routing, Filterung, Identität und Verschlüsselung getrennt; Beispieltabelle ausdrücklich unvollständiges fiktives Modell.

SHA-256: `f8f3d5d0d785232dbab21a1eccb518205e23601d1ddab56e679991bbd4f25c01`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 160 – 21.11.2026

**160 von 302** ausgearbeitet und strukturell geprüft; 142 fehlen. Nächster Datensatz: **it_0161 – VPN**. Die Fortsetzungsfreigabe bis 302 bleibt bestehen. Der an der Verarbeitungsgrenze gesicherte Stand ist keine Fertigmeldung; die gemeinsame Gesamtzusammenfassung bleibt bis nach 302 zurückgestellt.

Branch: codex/linux-glossar-011-302. Ausgangscommit dieses Durchlaufs: d0848a417938d150f64f3020650588eadd926964 (140 Einträge). Zunächst wurde bestätigt, dass dieser Stand bereits committet und gepusht war. Die Einträge 141–150 wurden mit 60f77aa73625277d830ca531925a77a38ba7b382 gesichert und gepusht; danach folgten 151–160 strikt einzeln mit jeweiliger Recherche, Ausarbeitung, Prüfung und unmittelbarer Index-/Fortschrittsspeicherung.

Gesamtprüfung erfolgreich für alle 160 Dokumente und Indexdatensätze: vereinbarte Originalquelle mit unveränderter SHA-256 und 302 eindeutigen IDs und Begriffen; ursprüngliches Indexschema, genaue Originalzuordnung und Kategorieableitung, vollständige Metadaten, lückenlose Quellreihenfolge, dokumentierte tatsächliche SHA-256-Prüfsummen, zehn Hauptabschnitte, geschlossene Codeblöcke, Parserlimits und interne Verweise. Linkbeschriftungen 141–160 zusätzlich mit Originalbegriffen verglichen. documented_records 160; source_urls sortierte duplikatfreie Vereinigung der genauen Quellen.

Alle 111 vollständigen Python-Beispiele des Gesamtstands erneut erfolgreich ausgeführt: Assertions, Exitcodes und vollständige Standardausgaben. Die 20 neuen Texte dieses Durchlaufs enthalten fünf praktische Python-Prüfungen und 15 Gedankenbeispiele. Praktisch wurden ausschließlich eigene IPv6-/Präfix-/MAC-Werte und ein eigener TLS-Kontext untersucht. Keine Netzwerkverbindung oder TLS-Handshake in diesen Beispielen. Ping, Traceroute, DNS-, DHCP- und ARP-Abläufe sowie Firewall- und NAT-Tabellen sind ausdrücklich nicht ausgeführte Modelle. Keine Geräte, Konten, Dienste, Zertifikatsablagen, Routing-, Firewall-, NAT- oder Netzprofile verändert.

Alle Dokumente 1–150 und ihre Indexdatensätze gegenüber 60f77aa unverändert; die Pilottexte zusätzlich unmittelbar gegen 688a832 geprüft. PROMPT.md unverändert. Der aktuelle Änderungsumfang enthält nur zehn neue Glossartexte, index.json und FORTSCHRITT.md; git diff --check erfolgreich. Im gesamten Durchlauf ausschließlich docs/linux-glossar/ geändert. Anwendung, Tests, Abhängigkeiten, Paketierung, Originalquelle und Befehlsdokumentationen unverändert. Keine zusätzlichen Worktrees oder Unteragenten. Keine Reader-Abnahme behauptet: Strukturprüfung weiterhin nur mit temporärem kompatiblem Kopf im vorhandenen Markdown-Parser. Inhaltliche Zweitprüfung und lokale Reader-Prüfung bleiben offen; review_pending bleibt erhalten. Kein Merge, Force-Push oder Veröffentlichen der Cloud-Umgebung.

## 161. VPN – it_0161

Ausgearbeitet und strukturell geprüft: 696 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6176 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc4026.html
- https://www.rfc-editor.org/rfc/rfc4301.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Reines Gedankenmodell: kein Client, Tunnel, Schlüssel, Routing- oder Netzwerkprofil angelegt oder verändert.

Präzisierung gegenüber der Quelle: VPN-Oberbegriff von häufig verschlüsseltem Fernzugriff getrennt. Verkehrsselektion, Endpunktschutz und Anwendungsberechtigung berücksichtigt; IPsec nur als konkretes Beispiel eingeordnet.

SHA-256: `1c9a595ad2b82e00c37f5a68bcf11b038530c0d3c6e6916f7ee7cfb0e04a7c2e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 162. Proxy – it_0162

Ausgearbeitet und strukturell geprüft: 710 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6126 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc9110.html#section-3.7
- https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.6
- https://www.rfc-editor.org/rfc/rfc9112.html#section-3.2.2

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Vermittlung; keine Proxy-, Browser- oder Vertrauenseinstellungen, DNS-Abfragen oder echten Anfragen.

Präzisierung gegenüber der Quelle: Forward Proxy, Reverse Proxy und Tunnel getrennt; HTTP-Verhalten nicht auf jede Proxyart verallgemeinert. CONNECT-Tunnel nicht automatisch als TLS-Entschlüsselung dargestellt.

SHA-256: `c0f78ce173db417aaf2c253f55ab8fc40b638ccc2deece731c8dc5c84e528a58`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 163. Packet – it_0163

Ausgearbeitet und strukturell geprüft: 671 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5949 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc768.html
- https://www.rfc-editor.org/rfc/rfc791.html
- https://www.rfc-editor.org/rfc/rfc8200.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Gedankenmodell ohne Paketbau, Prüfsummenabnahme, Mitschnitt oder Übertragung; keine fremden Daten oder Schnittstellen.

Präzisierung gegenüber der Quelle: Paketbegriff nach Protokollebene eingegrenzt; Rahmen, IP-Paket, Transport- und Anwendungsnachricht getrennt. 33-Byte-Beispiel ausdrücklich nur Kopf-/Nutzdatenrechnung ohne vollständiges Paket.

SHA-256: `20e3bae229efa2da2c1d6974b2892aa5dc1a8bfc2ee4206cbb2bbe3a7aa8aa1b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 164. Packet Capture – it_0164

Ausgearbeitet und strukturell geprüft: 686 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5778 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.tcpdump.org/manpages/pcap-savefile.5.html
- https://www.wireshark.org/docs/man-pages/dumpcap.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Fiktive Metadaten; kein Mitschnitt oder Fremddateizugriff. wireshark, tshark, dumpcap und capinfos nicht im Suchpfad; nichts installiert oder privilegiert ausgeführt.

Präzisierung gegenüber der Quelle: Aufzeichnung auf konkreten Beobachtungspunkt und Grenzen eingegrenzt. Gespeicherte von gemeldeter ursprünglicher Länge sowie Capture- von Display-Filter getrennt. Werkzeugverfügbarkeit ehrlich geprüft.

SHA-256: `2782eb026ec8d9afb7f82f24c94dfff2d354091481f448aa9fc0340e8361ce68`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 165. Wireshark – it_0165

Ausgearbeitet und strukturell geprüft: 654 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5718 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.wireshark.org/docs/man-pages/wireshark-filter.html
- https://www.wireshark.org/docs/man-pages/wireshark.html
- https://www.wireshark.org/docs/wsug_html_chunked/ChapterIntroduction.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Wireshark nicht im Suchpfad; Filter und Tabelle nur Gedankenbeispiel. Keine Installation, Oberfläche, Dateiöffnung oder Erfassung ausgeführt.

Präzisierung gegenüber der Quelle: Wireshark als grafische Analyse vorhandener Beobachtungen erklärt; Dissectoren, Display- und Capture-Filter getrennt. tcp.port-Filter nicht als vollständigen HTTPS- oder Verschlüsselungsnachweis ausgegeben.

SHA-256: `cf58d2d11f24d7df8808d752cd87c11475c785a598f142ed6f4aa35d1c36d414`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 166. tshark – it_0166

Ausgearbeitet und strukturell geprüft: 670 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5725 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.wireshark.org/docs/dfref/i/ip.html
- https://www.wireshark.org/docs/man-pages/tshark.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. tshark nicht im Suchpfad; Muster nicht ausgeführt, keine Testdatei oder Ergebniswerte vorgetäuscht, keine Installation oder Erfassung.

Präzisierung gegenüber der Quelle: TShark als eigene CLI-Schnittstelle erklärt; Dateilesen von möglicher Live-Erfassung getrennt. Feldausgabe und IPv4-spezifische Felder eingeordnet, fehlende Werte nicht als fehlende Kommunikation gewertet.

SHA-256: `e1de43903bab499a8404ade9ab483fefb3d9bddf991bcbf1b3afce1f0a96e12d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 167. Hostname – it_0167

Ausgearbeitet und strukturell geprüft: 686 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5863 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man7/hostname.7.html
- https://www.rfc-editor.org/rfc/rfc1123.html
- https://www.rfc-editor.org/rfc/rfc6762.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Namen; keine lokalen Namens- oder Systemdateiabfragen, DNS-/mDNS-Anfragen oder Umbenennungen.

Präzisierung gegenüber der Quelle: Kurzen Systemnamen, vollständigen Host-/DNS-Namen, IP und URL getrennt. Kontextabhängige Auflösung und .local-Sonderrolle erläutert; Katalogbeispiel nicht als tatsächlicher Rechnername ausgegeben.

SHA-256: `e14a100409444283dbc6f18ede01fa60916d06a9d32b88226e133288ba6e97dd`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 168. localhost – it_0168

Ausgearbeitet und strukturell geprüft: 636 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5685 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.IPv4Address.is_loopback
- https://man7.org/linux/man-pages/man7/network_namespaces.7.html
- https://www.rfc-editor.org/rfc/rfc1122.html
- https://www.rfc-editor.org/rfc/rfc4291.html
- https://www.rfc-editor.org/rfc/rfc6761.html#section-6.3

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Namensauflösung, Sockets, Dienste oder Namensräume abgefragt oder verändert; Adressklassifikation keine Erreichbarkeitsabnahme.

Präzisierung gegenüber der Quelle: localhost-Namen, Loopback-Adressen und laufenden Dienst getrennt; IPv4-Bereich, IPv6 und Linux-Netzkontext berücksichtigt. Vier eigene Adresswerte lokal klassifiziert.

SHA-256: `a4dbed37ec22b890a1ae074b577c65436820deafe3166bc389ab80feea84a59b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 169. API – it_0169

Ausgearbeitet und strukturell geprüft: 662 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5791 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/json.html#json.loads
- https://www.rfc-editor.org/rfc/rfc9110.html#section-9

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Wetterdaten oder entfernte API, keine Dienste oder Konten angesprochen; nur selbst erzeugte Werte.

Präzisierung gegenüber der Quelle: API nicht auf Web, JSON oder REST eingeschränkt. Dokumentierte Eingaben, Fehler und Ergebnisstruktur getrennt. Eigene JSON-Zeichenketten über lokale Bibliotheks-API praktisch verarbeitet.

SHA-256: `d42283b59005202cc6bf774d90e30b444c37de23194f57890e644826b049b5d5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 170. REST – it_0170

Ausgearbeitet und strukturell geprüft: 675 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6016 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm
- https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.1

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Notizdarstellung; keine API-Anfrage, Implementierung oder REST-Konformitätsabnahme.

Präzisierung gegenüber der Quelle: REST nach Fieldings Originalbeschreibung von HTTP, JSON und einzelnen Pfaden getrennt. Zustandslosigkeit nicht mit Verbot gespeicherter Ressourcen verwechselt; Hypermedia und weitere Bedingungen berücksichtigt.

SHA-256: `071bd869dfe8fd858f936c9727011f598990e2f9eed143d98bace814b34830b1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Datensatz 170 – 21.11.2026

**170 von 302** ausgearbeitet und strukturell geprüft; 132 fehlen. Nächster Datensatz: **it_0171 – Endpoint**. Die Fortsetzungsfreigabe bis 302 besteht; keine Abschlussmeldung und keine gemeinsame Gesamtzusammenfassung.

Branch: codex/linux-glossar-011-302. Ausgangscommit dieses Durchlaufs: 2cda9c06c5d23d784d848394d12801ab1d9b01e2 (160 Einträge). Arbeitsverzeichnis anfangs sauber; erneuter Push bestätigte Everything up-to-date. Danach 161–170 einzeln recherchiert, geschrieben, geprüft und unmittelbar in Index und Fortschritt gespeichert. Quellenabruf 21.11.2026 über HTTPS mit unveränderter TLS-Prüfung. Keine Unteragenten oder weiteren Worktrees.

Gesamtprüfung aller 170 Dokumente erfolgreich: unveränderte Originalquelle mit vereinbarter SHA-256 und 302 eindeutigen Originaldatensätzen; Metadaten und Kategorieableitung, zehn Hauptabschnitte, Codeblöcke und Parserlimits, lückenloser Index, tatsächliche Dokumentprüfsummen, genaue Quellenvereinigung und interne Verweise. Linkbeschriftungen der neuen Texte zusätzlich gegen Originalbegriffe geprüft. Alle 113 vollständigen Python-Beispiele erneut ausgeführt; Assertions, Exitcodes und dokumentierte Ausgaben erfolgreich.

Die zehn neuen Texte enthalten zwei praktische Python-Beispiele (eigene Loopback-Adresswerte und eigene JSON-Daten über eine lokale API) und acht nicht ausgeführte Gedankenbeispiele. Keine Verbindungen, Namensauflösungen oder Mitschnitte in den Beispielen. wireshark, tshark, dumpcap und capinfos bei reiner Suchpfadprüfung nicht gefunden; nichts installiert und keine Werkzeugabnahme behauptet. Quellenbelegte Filter und Kommandomuster ausdrücklich nicht ausgeführt. VPN, Proxy, Netzwerkprofile, Zertifikate und Dienste unverändert.

Dokumente 1–160 und deren Indexdatensätze gegenüber 2cda9c0 unverändert; Pilottexte zusätzlich unmittelbar gegen Pilotcommit 688a832 geprüft. PROMPT.md unverändert. Änderungsumfang nur zehn neue Glossartexte, index.json und FORTSCHRITT.md; git diff --check erfolgreich. Keine Anwendung, Tests, Abhängigkeiten, Paketierung, Originalquelle oder Befehlsdokumentationen verändert. Strukturprüfung weiterhin über temporären kompatiblen Kopf im vorhandenen Markdown-Parser, keine neue Reader-Abnahme. Inhaltliche Zweitprüfung und lokaler Reader-Test stehen aus; review_pending bleibt erhalten.

## 171. Endpoint – it_0171

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5657 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/urllib.parse.html#urllib.parse.urlsplit
- https://spec.openapis.org/oas/v3.1.1.html#paths-object

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Verbindung oder API-Operation; URL-Parsing nicht als Erreichbarkeits- oder Sicherheitsprüfung ausgegeben.

Präzisierung gegenüber der Quelle: Endpoint-Pfad von vollständiger URL und Operation getrennt; Methode und API-Vertrag berücksichtigt. OpenAPI 3.1.1 ausdrücklich als verwendete Spezifikation genannt. Eigene URL lokal in Bestandteile zerlegt.

SHA-256: `5720f508faffa89744a284529b0ce22d907fb012396788bab56e9b62925e81a4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 172. Request – it_0172

Ausgearbeitet und strukturell geprüft: 667 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5783 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/urllib.request.html#urllib.request.Request
- https://www.rfc-editor.org/rfc/rfc9110.html#section-6
- https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein urlopen, DNS, Serverkontakt oder Handshake; Accept-Präferenz nicht als tatsächliche Serverantwort ausgegeben.

Präzisierung gegenüber der Quelle: Anfrageerzeugung, Senden und Ausführung getrennt; HTTP nur als konkreter Kontext. Wiederholungsrisiko und idempotente Semantik eingeordnet. Eigenes Request-Objekt ohne Sendeoperation praktisch geprüft.

SHA-256: `7d87013d54aaa00f2bc6459379414386e8dfea63e20038298235bb91f3b103ee`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 173. Response – it_0173

Ausgearbeitet und strukturell geprüft: 678 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6020 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/http.client.html#http.client.parse_headers
- https://www.rfc-editor.org/rfc/rfc9110.html#section-6.4
- https://www.rfc-editor.org/rfc/rfc9112.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein Server, Socket oder echter API-Austausch. Beispiel nicht als vollständiger Parser für beliebige HTTP-Nachrichten oder Dienstabnahme ausgegeben.

Präzisierung gegenüber der Quelle: Response von Körper, JSON und fachlichem Erfolg getrennt. Öffentliche parse_headers-Funktion nur für ihre dokumentierte Teilaufgabe verwendet; eigene vollständige Beispielbytes und Feld-/Körperlänge geprüft.

SHA-256: `74bf83569aac49386e3f97c3820e4536b7c628c4062f476ebb20251c79a1d5ec`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 174. Statuscode – it_0174

Ausgearbeitet und strukturell geprüft: 680 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5567 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/http.html#http.HTTPStatus
- https://www.rfc-editor.org/rfc/rfc9110.html#section-15
- https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.5

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Verbindung, Endpoint-Prüfung oder API-Antwort; Bibliothekszuordnung ist keine Serverdiagnose.

Präzisierung gegenüber der Quelle: HTTP-Status von Exit-Code und fachlichem Erfolg getrennt. Klassen und 404-Existenz-/Offenlegungsaussage präzisiert. Eigene Zahlen über Python-3.13-HTTPStatus geprüft, keine echten Antworten behauptet.

SHA-256: `a292a0fca743bae626c70c3bf555126e28c8b3687a1e4469cdbb70dfb5711fda`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 175. JSON – it_0175

Ausgearbeitet und strukturell geprüft: 683 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6050 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/json.html#json.dumps
- https://docs.python.org/3.13/library/json.html#standard-compliance-and-interoperability
- https://www.rfc-editor.org/rfc/rfc8259.html

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene Speicherwerte; keine API, Fremddatei oder Konfiguration. Rücklesen ist keine vollständige Schema- oder Sicherheitsabnahme.

Präzisierung gegenüber der Quelle: JSON-Standard von Python-Strukturen, Parsererweiterungen und Anwendungsschema getrennt. Objekte nicht als einzige gültige Wurzelwerte dargestellt; NaN-Ausgabe im eigenen Beispiel ausdrücklich abgelehnt.

SHA-256: `34edff1007e3cb9e1b0d99ced5268f69891cdeb354b7764fce5b4a3c99766124`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 176. YAML – it_0176

Ausgearbeitet und strukturell geprüft: 685 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5803 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://compose-spec.github.io/compose-spec/spec.html
- https://pyyaml.org/wiki/PyYAMLDocumentation
- https://yaml.org/spec/1.2.2/

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Installation, Compose-Ausführung oder echte Konfigurationsdatei. safe_load-Test keine umfassende Schema- oder Sicherheitsabnahme.

Präzisierung gegenüber der Quelle: YAML-Version, Schema, Parser und Anwendungsvertrag getrennt. Compose-Dateiname anhand aktueller Spezifikation eingeordnet. Vorhandenes PyYAML 6.0.2 für eigene Werte genutzt; yes-Verhalten ausdrücklich als Parserverhalten statt YAML-1.2-Regel bezeichnet.

SHA-256: `e2af493c2bf0354d4e15e6a6157003b604892209211086ac3154e4efdd63ff1e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 177. XML – it_0177

Ausgearbeitet und strukturell geprüft: 682 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6162 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/xml.etree.elementtree.html#xml.etree.ElementTree.fromstring
- https://docs.python.org/3.13/library/xml.html#xml-vulnerabilities
- https://www.w3.org/TR/xml/

Praktische Prüfung: ein vollständiges Python-Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Fremddateien, externen Entitäten oder Netzwerkzugriffe; keine Schema-, Sicherheits- oder Importabnahme behauptet.

Präzisierung gegenüber der Quelle: XML-Wohlgeformtheit von Schema und Fachvertrag getrennt; Element-/Attributstruktur und Texttypen erläutert. Eigene Zeichenketten mit ElementTree verarbeitet und echte Verschachtelungsablehnung geprüft.

SHA-256: `539dba3939b26ab1e29c213f201c0e8a70ee543b71ba15c198039db42753af2b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 178. HTML – it_0178

Ausgearbeitet und strukturell geprüft: 670 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5778 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element
- https://html.spec.whatwg.org/multipage/introduction.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur inaktiver Textblock; keine Browser-, Tastatur- oder Barrierefreiheitsabnahme. Temporäre Quellenankerprüfung um zulässige unquotierte HTML-id-Attribute ergänzt; kein Anwendungscode geändert.

Präzisierung gegenüber der Quelle: HTML-Struktur und Semantik von Gestaltung und Programmlogik getrennt. Buttonbeispiel mit explizitem Typ und ohne automatische Fachaktion erklärt. Aktueller WHATWG-Standard als Primärquelle.

SHA-256: `e2d6e21c2b3473e1fe7bc0aec4362a7d92c9fea73a776bb3faab74792cf0a4a1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 179. CSS – it_0179

Ausgearbeitet und strukturell geprüft: 682 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5904 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.w3.org/TR/css-values-4/#font-relative-lengths

- https://www.w3.org/TR/css-cascade-5/
- https://www.w3.org/TR/selectors-4/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur inaktiver CSS-Text; kein Browserrendering, Pixel-, Kontrast- oder Responsive-Test. Keine Stylesheets oder Reader-Darstellung verändert.

Präzisierung gegenüber der Quelle: CSS über reine Farben hinaus als Darstellungssprache erläutert. Selektor, Deklaration, Kaskade und Vererbung getrennt; letzte-Regel-Regel ausdrücklich an Vergleichsbedingungen gebunden.

SHA-256: `a3e282f7b474f706bb7caa5be1e69e673ec54dd1e260f553524dbb30e5cc9ae1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 180. JavaScript – it_0180

Ausgearbeitet und strukturell geprüft: 651 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5943 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://dom.spec.whatwg.org/#introduction-to-dom-events
- https://nodejs.org/api/globals.html
- https://tc39.es/ecma262/
- https://tc39.es/ecma262/#sec-array.prototype.map

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein Browser-, Klick-, DOM- oder Netzwerkversuch; keine Pakete installiert. Nur temporären Validator um korrekt markierte JavaScript-Beispiele erweitert, Anwendungscode unverändert.

Präzisierung gegenüber der Quelle: ECMAScript-Sprachkern von Browser-/DOM- und Node-APIs getrennt. Eigenes JavaScript mit vorhandener Node.js 24.22.1 praktisch ausgeführt; Arraywerte, Objekttrennung und Funktionsfälle geprüft.

SHA-256: `b9e7bd959f29ce7d972183556e25fc4d400da32cc73b6c460d8f692497931bba`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Datensatz 180 – 21.11.2026

**180 von 302** ausgearbeitet und strukturell geprüft; 122 fehlen. Nächster Datensatz: **it_0181** (Originalbegriff vor Beginn aus dem Katalog lesen). Die Freigabe bis 302 bleibt bestehen; kein Abschluss des Gesamtauftrags.

Branch codex/linux-glossar-011-302; Ausgangspunkt dieses Abschnitts 4672b57676ce0703f7243a6c1c6d8008d215958b. Einträge 171–180 einzeln recherchiert, geschrieben und nach Prüfung unmittelbar in Index und Fortschritt gespeichert. Originaldaten und Reihenfolge erhalten. Neuer JavaScript-Code ist korrekt als javascript markiert; alle Glossarköpfe bleiben im vereinbarten unveränderten Schema.

Alle 180 Dokumente und Indexdatensätze erneut erfolgreich geprüft: vereinbarter Quellhash, 302 eindeutige Originaldatensätze, vollständige Metadaten, Kategorieableitung, zehn Hauptabschnitte, Codeblöcke, Grenzen, lokale Verweise und tatsächliche Dokumentprüfsummen. Indexschema unverändert; documented_records 180 und genaue Quellenvereinigung sortiert und duplikatfrei. Neue Linkbeschriftungen zusätzlich gegen Originalbegriffe geprüft.

Gesamtlauf: 120 vollständige Python-Beispiele mit System-Python und ein JavaScript-Beispiel mit vorhandenem Node.js 24.22.1 erneut erfolgreich ausgeführt. Assertions, Exitcodes und Standardausgaben geprüft. In 171–180 sind sieben Python-Beispiele, ein JavaScript-Beispiel und zwei Gedankenmodelle enthalten. Vorhandenes PyYAML 6.0.2 ohne Installation genutzt; dessen yes-Auflösung ausdrücklich von YAML-1.2-Regeln unterschieden. Alle Daten selbst erzeugt und Ausführungen in temporären Ordnern. Kein Serverkontakt, Browser-, Klick- oder Darstellungstest. HTML und CSS nur inaktive Textblöcke.

Temporärer Validator um JavaScript-Ausführung und zulässige unquotierte HTML-id-Attribute bei Quellenankern ergänzt; kein Anwendungscode verändert. Der vorhandene Markdown-Parser hat ausschließlich im Prüfprozess einen kompatiblen Kopf erhalten. Keine Reader-Abnahme oder vollständige Schema-/Sicherheitsvalidierung behauptet.

Alle Texte 1–170 und ihre Indexdatensätze gegenüber 4672b57 unverändert, Pilottexte zusätzlich gegen ursprünglichen Pilotcommit geprüft. PROMPT.md unverändert. Nur zehn neue Glossartexte, index.json und FORTSCHRITT.md geändert; git diff --check erfolgreich. Keine Anwendung, Tests, Abhängigkeiten, Paketierung, Originalquelle, Befehlsdokumentation oder Cloud-Veröffentlichung geändert. Fachliche Zweitprüfung und lokale Reader-Prüfung bleiben ausstehend; review_pending bleibt erhalten.

## 181. Frontend – it_0181

Ausgearbeitet und strukturell geprüft: 643 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5785 UTF-8-Bytes; 28 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview
- https://www.w3.org/WAI/tutorials/forms/validation/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktives Zustandsmodell, keine Oberfläche, API-Anfrage oder Bedien-/Reader-Abnahme.

Präzisierung gegenüber der Quelle: Sichtbaren Teil um Interaktion, Zustände und zugängliche Rückmeldung erweitert. Browserprüfung und ausgeblendete Elemente nicht als ausreichende serverseitige Sicherheit dargestellt.

SHA-256: `aec2253582f9655dc9b7177c21780e5ad0c2e5ee90611b5bcc656e31fb82ff82`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 182. Backend – it_0182

Ausgearbeitet und strukturell geprüft: 692 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6064 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.djangoproject.com/en/5.2/intro/overview/
- https://www.w3.org/WAI/tutorials/forms/validation/

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Anwendung, Authentifizierung, Datenbank oder HTTP-Verarbeitung getestet; nur eigene lokale Werte.

Präzisierung gegenüber der Quelle: Backend als Architekturrolle statt bloßem Hintergrundprozess erklärt; Datenbank nicht vorausgesetzt. Eigenes begrenztes Eingabemodell inklusive String-, Boolean- und Bereichsablehnung praktisch geprüft.

SHA-256: `68a0d06c33c53e748657a346f81c197d940fd0c0e4b717b403b701694ce688fd`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 183. Client – it_0183

Ausgearbeitet und strukturell geprüft: 693 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5671 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/urllib.request.html#urllib.request.urlopen
- https://www.rfc-editor.org/rfc/rfc9110.html#section-3.3

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktiver Ablauf, kein urlopen oder anderer Clientzugriff und keine neue Software.

Präzisierung gegenüber der Quelle: Client als Programmrolle von Mensch, GUI und Geräteklasse getrennt. HTTP-Definition nicht als universeller Ablauf aller Protokolle verwendet; Mehrfachrollen eines Vermittlers berücksichtigt.

SHA-256: `86fb973e93a8e6a7cc955db519775f2cd02a7e39c5d03018a9f5ea3386fdc941`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 184. Server – it_0184

Ausgearbeitet und strukturell geprüft: 682 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5942 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/http.server.html
- https://www.rfc-editor.org/rfc/rfc9110.html#section-3.3

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Kein Serverstart, Port, Dateifreigabe oder Verbindungsversuch; keine Produktions- oder Betriebsabnahme.

Präzisierung gegenüber der Quelle: Serverprogramm, Rechner, Backend und Dienstverwaltung getrennt. Erreichbarkeit und Fachfunktion nicht aus bloßer Installation abgeleitet; http.server nur als begrenzten Bibliotheksbaustein eingeordnet.

SHA-256: `d8e4cf0602023b47454729fbf74296d3904a2c7aea760d11e095127f16cb4413`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 185. CORS – it_0185

Ausgearbeitet und strukturell geprüft: 692 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5931 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://fetch.spec.whatwg.org/#http-cors-protocol
- https://www.rfc-editor.org/rfc/rfc6454.html#section-4

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktive Origin-Tabelle; kein Browser-CORS-Test, keine Anfragen, Header-, Browserflag- oder Serveränderungen.

Präzisierung gegenüber der Quelle: Domainverkürzung auf Origin aus Schema, Host und Port präzisiert. Browser-Antwortfreigabe von Authentifizierung, Autorisierung, Senden und CSRF-Schutz getrennt; Preflight nicht pauschal vorausgesetzt.

SHA-256: `2715cd5e2940cb6d951f7dfbc5854ce9628474bf6a6dc3f4bfbf2d260286c84c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 186. Cookie – it_0186

Ausgearbeitet und strukturell geprüft: 651 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5777 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie
- https://docs.python.org/3.13/library/http.cookies.html#http.cookies.SimpleCookie
- https://www.rfc-editor.org/rfc/rfc6265.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein Browserbestand, Login, Serverkontakt oder Cookieversand; Parserprüfung keine Browser- oder Sitzungsabnahme.

Präzisierung gegenüber der Quelle: Cookie von vollständiger Sitzung und pauschalem Zugriffsnachweis getrennt. Attribute und Browserpolitik unterschieden; Origin nicht mit Site gleichgesetzt. Eigene Felder mit SimpleCookie lokal geprüft.

SHA-256: `b361beff43eda1e693999d62d8f7f09ab13524af92ee39036016af7c73a253a7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 187. Session – it_0187

Ausgearbeitet und strukturell geprüft: 684 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6064 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.djangoproject.com/en/5.2/topics/http/sessions/
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Session_Management_Cheat_Sheet.md

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nur fiktiver Ablauf, keine Konten oder Sitzungen. OWASP-Webseite lieferte HTTP 403; erreichbare offizielle Quelldatei aus OWASP/CheatSheetSeries verwendet.

Präzisierung gegenüber der Quelle: Sitzung von Cookie, Kennung, Verbindung und Login getrennt. Unterschiedliche Speicherverfahren und Gültigkeitsregeln anhand Django 5.2 und OWASP eingeordnet.

SHA-256: `a1481115d58f33a0d4ce6fefcb859dbb3571c58b6ae5ad23e9a814c4e624145c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 188. Token – it_0188

Ausgearbeitet und strukturell geprüft: 687 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5780 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/secrets.html#secrets.token_urlsafe
- https://www.rfc-editor.org/rfc/rfc6750.html
- https://www.rfc-editor.org/rfc/rfc7519.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Kein bestehender Token, Konto oder Dienst verwendet; keine Berechtigung, Speicherung oder Sicherheitsabnahme des Gesamtsystems.

Präzisierung gegenüber der Quelle: Tokenarten, Bearer-Modell und JWT-Format getrennt; Darstellung nicht mit Gültigkeit oder Berechtigung gleichgesetzt. Neuen eigenen Zufallswert erzeugt und nur Umfang/Form ohne Geheimwertausgabe geprüft.

SHA-256: `f462f2973e541fb7321f42252fbe1dadec1e883a02ca494c4d0ded7186f409ee`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 189. OAuth – it_0189

Ausgearbeitet und strukturell geprüft: 711 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 5997 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.rfc-editor.org/rfc/rfc6749.html
- https://www.rfc-editor.org/rfc/rfc9700.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Keine Anbieterintegration, Clientregistrierung, Anmeldung, PKCE-, Konto- oder Tokenoperation.

Präzisierung gegenüber der Quelle: OAuth 2.0 als Autorisierungsrahmen von allgemeiner Anmeldung und Tokenformat getrennt. Grundstandard mit RFC 9700 als neueren Sicherheitsempfehlungen eingeordnet; fiktiver Umfang nicht als universeller Scope ausgegeben.

SHA-256: `93e4c84a3cbebeb586be49f332cd3a9026c0e0a0b4f96bcc2036ad3afd4106e4`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 190. Webhook – it_0190

Ausgearbeitet und strukturell geprüft: 686 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6203 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.github.com/en/webhooks/about-webhooks
- https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
- https://docs.python.org/3.13/library/hmac.html#hmac.compare_digest

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Benachrichtigung, Registrierung, Empfänger, Konten oder echten Schlüssel; HMAC-Test keine vollständige Webhook-, Replay- oder Berechtigungsabnahme.

Präzisierung gegenüber der Quelle: Webhook als anbieterspezifischen Ereignisweg erklärt; Annahme, Verarbeitung und Wiederholung getrennt. Eigenes HMAC-Beispiel prüft unveränderte gegen veränderte Rohbytes ohne tatsächlichen Anbieter.

SHA-256: `3c58eb699a26b523af784f2e0473b6470754976a6944361ffff97add96540624`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Gesicherter Zwischenstand nach Datensatz 190 – 21.11.2026

**190 von 302** ausgearbeitet und strukturell geprüft; 112 fehlen. Nächster Datensatz: **it_0191 – Datenbank**. Die Fortsetzungsfreigabe bis 302 bleibt bestehen. An der Verarbeitungsgrenze gesichert; keine Fertigmeldung und keine gemeinsame Gesamtzusammenfassung vor 302.

Tatsächlicher Branch: codex/linux-glossar-011-302. Ausgangscommit dieses Durchlaufs: 27ca13ce704cad028cb4126bef57f63bd5899833. Nach Svens ausdrücklicher Pause wurde auf sein „ok mach weiter“ fortgesetzt. Anfangsstand sauber, Quelle und Index 180 bestätigt. Die beim Stopp zurückgestellte PR-Beschreibung zunächst auf 180 aktualisiert. Danach 181–190 einzeln recherchiert, geschrieben, geprüft und unmittelbar in Index und Fortschritt gespeichert. Keine Unteragenten oder weiteren Worktrees.

Gesamtprüfung aller 190 Dokumente erfolgreich: unveränderte Originalquelle mit vereinbarter SHA-256 und 302 eindeutigen Originaldatensätzen; Metadaten, Kategorieableitung, zehn Hauptabschnitte, Codeblöcke und Parserlimits, tatsächliche Dokumentprüfsummen, interne Verweise und unverändertes Indexschema. Linkbeschriftungen der neuen Texte zusätzlich gegen Originalbegriffe geprüft. records lückenlos in Quellreihenfolge; documented_records 190; source_urls sortierte duplikatfreie Vereinigung der genauen Eintragsquellen.

Gesamtlauf erfolgreich: 124 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut ausgeführt; Assertions, Exitcodes und vollständige Standardausgaben stimmen. Die zehn neuen Texte enthalten vier praktische Python-Prüfungen und sechs Gedankenmodelle. Praktisch wurden nur eigene Eingaben, Cookie-Headerdaten, ein neu erzeugter nicht berechtigender Testwert und eine eigene HMAC-Nachricht geprüft. Keine echten Tokens ausgegeben, Konten genutzt oder Benachrichtigungen gesendet. Kein Browser-, CORS-, Session-, OAuth-, Backend- oder Webhook-Integrationstest behauptet. Die Beispielprüfungen sind keine allgemeine Sicherheitsabnahme.

Alle Dokumente 1–180 und ihre Indexdatensätze gegenüber 27ca13c unverändert; die zehn Pilottexte zusätzlich unmittelbar gegen 688a832 geprüft. PROMPT.md unverändert. Nur zehn neue Glossartexte, index.json und FORTSCHRITT.md geändert; git diff --check erfolgreich. Anwendung, Tests, Abhängigkeiten, Paketierung, Originalquelle und Befehlsdokumentationen unverändert. Keine Cloud-Veröffentlichung, kein Merge oder Force-Push. Strukturprüfung weiterhin nur mit temporärem kompatiblem Kopf im vorhandenen begrenzten Markdown-Parser. Fachliche Zweitprüfung und lokale Reader-Abnahme der neuen Texte bleiben offen; review_pending bleibt erhalten.

## 191. Datenbank – it_0191

Ausgearbeitet und strukturell geprüft: 688 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6084 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#sqlite3.connect
- https://www.postgresql.org/docs/current/tutorial-concepts.html
- https://www.sqlite.org/about.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine Anwendungsdatenbank, Dienste oder Installationen; kein Ausfall-, Mehrbenutzer- oder Sicherungstest.

Präzisierung gegenüber der Quelle: Datenbestand, Managementsystem und relationales Modell getrennt; eingebettete und servergestützte Bereitstellung berücksichtigt. Eigene temporäre SQLite-Datei geschrieben und nach neuer Verbindung wieder gelesen.

SHA-256: `183e8a5344f3ee003a61e84c1317947a3d56aaea2bd9d3f000eb58f491d91e74`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 192. SQL – it_0192

Ausgearbeitet und strukturell geprüft: 710 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6259 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#sqlite3-placeholders
- https://www.sqlite.org/lang.html
- https://www.sqlite.org/lang_select.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Datenbank; keine Anwendungstabellen oder verändernden Operationen an fremden Beständen. Kein vollständiger Sicherheitsnachweis.

Präzisierung gegenüber der Quelle: SQL von Datenbanksystem und rein lesender Abfrage getrennt; Dialekt, Ergebnisreihenfolge und Wertbindung berücksichtigt. Eigene Apostroph- und SQL-ähnliche Werte mit Platzhaltern geprüft.

SHA-256: `8b53f6006cb354e06c1e2414a501e37029810aaab57d558501efb0d371ff1305`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 193. SQLite – it_0193

Ausgearbeitet und strukturell geprüft: 683 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6241 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.sqlite.org/about.html
- https://www.sqlite.org/inmemorydb.html
- https://www.sqlite.org/wal.html
- https://www.sqlite.org/whentouse.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine vorhandene Datei, WAL-Einstellung oder Installation verändert; keine parallele Last-, Sicherungs- oder Ausfallabnahme.

Präzisierung gegenüber der Quelle: SQLite von bloß kleinem Dateiformat getrennt; eingebettetes Modell, In-Memory-Form und WAL-Zusatzdateien berücksichtigt. Zwei private Speicherverbindungen praktisch auf getrennte Bestände geprüft.

SHA-256: `0dae46d782367cce03879649a330c7aacfd58ee6d669e3ad7418fe49c2f9bdf8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 194. Tabelle – it_0194

Ausgearbeitet und strukturell geprüft: 715 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6143 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.postgresql.org/docs/current/ddl-basics.html
- https://www.sqlite.org/lang_createtable.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Keine reale Stationsdatei, bestehende Tabelle oder Anwendung verändert; kein vollständiges Fachmodell oder Radiodienst getestet.

Präzisierung gegenüber der Quelle: SQL-Tabelle von geordneter Liste und Bildschirmansicht getrennt. Eindeutigkeit und Nicht-Fehlen als ausdrücklich gewählte Regeln behandelt. Eigene SQLite-Tabelle samt gleichen Namen und abgelehntem NULL geprüft.

SHA-256: `c3937af5b42cfedab3b1bdaae216c719a6643c5155ed3348a543c65438da0781`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 195. Zeile – it_0195

Ausgearbeitet und strukturell geprüft: 729 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6133 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.postgresql.org/docs/current/ddl-basics.html
- https://www.sqlite.org/lang_select.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Daten; keine echten Notizen, Sender oder Anwendungsbestände verändert.

Präzisierung gegenüber der Quelle: Datenbankzeile von Textzeile und Ausgabeposition getrennt. Vorhandene Zeile mit NULL von fehlendem Treffer unterschieden. Eigener mehrzeiliger Text und beide Fehlwertfälle praktisch geprüft.

SHA-256: `b5dc620fe4fa0359d081a242587e460938c5dd421c55b5b8bdf3d416b0917280`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 196. Spalte – it_0196

Ausgearbeitet und strukturell geprüft: 701 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6230 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.postgresql.org/docs/current/ddl-basics.html
- https://www.sqlite.org/datatype3.html
- https://www.sqlite.org/stricttables.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Tabellen mit SQLite 3.46.1; keine Anwendungsschemata, Migrationen oder Versionen verändert.

Präzisierung gegenüber der Quelle: Spalte ausdrücklich von Feldtyp getrennt. SQLite-Affinität und versionsabhängige STRICT-Regeln nicht als allgemeines SQL-Verhalten ausgegeben. Eigene normale und strenge Integer-Spalten praktisch verglichen.

SHA-256: `8e6bc8c1bc1c9f725f0cc0ca0d652c3f3e5ca62ecebe63d96a9b776457ec8e02`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 197. Primärschlüssel – it_0197

Ausgearbeitet und strukturell geprüft: 714 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6360 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-PRIMARY-KEYS
- https://www.sqlite.org/lang_createtable.html#the_primary_key

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Tabelle; keine konkurrierenden Zugriffe oder vorhandenen Datenbanken geprüft.

Präzisierung gegenüber der Quelle: Primärschlüssel können mehrteilig sein; Spaltenname, Nummernerzeugung und Ergebnisposition sind davon getrennt. SQLite-NULL-Ausnahmen ausdrücklich eingeordnet.

SHA-256: `d82771c40d4abeac88934da95058d5cae09aa836e8d2ad80de766ea2a2b3a1bc`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 198. Fremdschlüssel – it_0198

Ausgearbeitet und strukturell geprüft: 697 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6321 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK
- https://www.sqlite.org/foreignkeys.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Daten; keine Löschkaskaden, aufgeschobenen Prüfungen oder produktiven Importe getestet.

Präzisierung gegenüber der Quelle: Fremdschlüssel können mehrteilig und selbstbezüglich sein. Verpflichtende Zuordnung, Löschaktionen und SQLite-Aktivierung sind getrennte Regeln.

SHA-256: `f194d1992a1586df2110f0bcaf4c1733271254a1bdf9b7eda4e37e1feeceab8a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 199. Index Datenbank – it_0199

Ausgearbeitet und strukturell geprüft: 738 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6361 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.sqlite.org/lang_createindex.html
- https://www.sqlite.org/queryplanner.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur Indexanlage und Ergebnisgleichheit geprüft; kein Ausführungsplan und kein Leistungstest.

Präzisierung gegenüber der Quelle: Index kann passende Zugriffswege unterstützen; keine pauschale Beschleunigung, automatische Eindeutigkeit oder Ergebnisordnung. Schreib- und Speicheraufwand eingeordnet.

SHA-256: `752c51019f6abd2762bd4149717dc4bf8cd80dccb2e1985e8d47cb6505a4abd1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 200. Query – it_0200

Ausgearbeitet und strukturell geprüft: 746 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6314 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#sqlite3-placeholders
- https://www.postgresql.org/docs/current/tutorial-select.html
- https://www.sqlite.org/lang_select.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Abfrage; keine Leistungsmessung oder fremde Datenquelle.

Präzisierung gegenüber der Quelle: Abfragetext, Ausführung und Ergebnis unterschieden; Auswahl, Filter, explizite Sortierung, leeres Ergebnis und sichere Wertbindung erläutert. Andere Verwendungen des Begriffs eingeordnet.

SHA-256: `0fcd494ba24e7e1813342def221770cecb09b1dc0a86cd8c06b196c026b4aeeb`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 201. Migration – it_0201

Ausgearbeitet und strukturell geprüft: 732 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6767 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#transaction-control-via-the-autocommit-attribute
- https://www.sqlite.org/lang_altertable.html
- https://www.sqlite.org/lang_transaction.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene In-Memory-Schemaänderung mit Rollback und Commit geprüft; kein Migrationswerkzeug, Backup, NetMon-Update oder produktiver Bestand getestet.

Präzisierung gegenüber der Quelle: Migration als geplante Schema- und gegebenenfalls Datenänderung eingeordnet; Versionsverwaltung, Bestandswerte, Kompatibilität und begrenzte Rücknahme getrennt. SQLite-ALTER-Grenzen beachtet.

SHA-256: `979445fc64a38272b39ba408e0782bc7f23bc49279f59f5616c4772486dbd51f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 202. Transaktion – it_0202

Ausgearbeitet und strukturell geprüft: 730 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6717 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#how-to-use-the-connection-context-manager
- https://www.postgresql.org/docs/current/tutorial-transactions.html
- https://www.sqlite.org/lang_transaction.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigener SQLite-Fehlerpfad mit Kontextmanager und erfolgreicher Bestätigung; keine Crashfestigkeit, Mehrbenutzerisolation oder externen Wirkungen geprüft.

Präzisierung gegenüber der Quelle: Automatische Gesamtrücknahme bei jedem Fehler ausdrücklich korrigiert; Transaktionsgrenzen, Schnittstellensteuerung und externe Wirkungen getrennt.

SHA-256: `2ff42706172a7eac8c7b7ef95ca459338b32ed2d63268f0c8ab5aec442d46496`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 203. NoSQL – it_0203

Ausgearbeitet und strukturell geprüft: 704 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6348 UTF-8-Bytes; 29 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://cassandra.apache.org/doc/latest/cassandra/architecture/overview.html
- https://www.mongodb.com/docs/manual/core/transactions/
- https://www.mongodb.com/docs/manual/data-modeling/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Gedankenbeispiel mit eigenen JSON-Dokumentformen; kein NoSQL-System installiert, gestartet oder abgenommen.

Präzisierung gegenüber der Quelle: NoSQL als heterogener Sammelbegriff erklärt; Dokumentmodell nicht mit JSON-Datei gleichgesetzt. Schemaflexibilität, CQL-Tabellen und produktabhängige Transaktionen differenziert.

SHA-256: `ed202b1254b642ee91873caeaf0d6a3c6acb1f64fe31968a03f30bfec6aacee9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 204. ORM – it_0204

Ausgearbeitet und strukturell geprüft: 733 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6552 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- https://docs.sqlalchemy.org/en/20/tutorial/metadata.html
- https://docs.sqlalchemy.org/en/20/tutorial/orm_data_manipulation.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Gedankenbeispiel; keine ORM-Bibliothek installiert oder praktische Speicherung behauptet.

Präzisierung gegenüber der Quelle: ORM als explizite Zuordnung erklärt, nicht beliebige Objektserialisierung. SQLAlchemy 2.0 dient als versionsbezogenes Beispiel; Objektzustand, Flush, Commit und Migration getrennt.

SHA-256: `f958c1cd114241daf6a21a561eee64af8624f37c4d1972bb11f13777e45f6e16`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 205. Git – it_0205

Ausgearbeitet und strukturell geprüft: 718 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6546 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-init.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/gittutorial.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigenes temporäres Git-Repository mit Git 2.52.0; keine Netzwerkoperation und keine bestehende Konfiguration verändert.

Präzisierung gegenüber der Quelle: Git als verteiltes Werkzeug von Hostingdienst und Backup unterschieden; bewusste Auswahl, Index, Commit und Upload getrennt.

SHA-256: `9621754b9574e0dd8339ef508a47079299ffbf7214009a7b1fe8c12dbe035326`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 206. Repository Git – it_0206

Ausgearbeitet und strukturell geprüft: 758 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6757 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-init.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/gitrepository-layout.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur zwei eigene leere temporäre Repositories; kein zusätzliches Projekt-Worktree, kein Remote, kein Netzwerk und keine bestehenden Git-Metadaten verändert.

Präzisierung gegenüber der Quelle: Repository-Daten von Arbeitsverzeichnis unterschieden; Bare-Form, mögliche gitfile und anfänglicher Branch ohne Commit erläutert.

SHA-256: `55cc33f1699bf84473b72b63664fbdb9c89b4706257415a542605435cbe32896`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 207. Commit – it_0207

Ausgearbeitet und strukturell geprüft: 745 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6659 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-add.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-commit.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigenes temporäres Repository; vorgemerkte und spätere Fassung tatsächlich verglichen, kein Push und keine produktive Historie verändert.

Präzisierung gegenüber der Quelle: Commit als Projektstand mit Metadaten und Vorgängern erklärt; fachliche Vollständigkeit keine Git-Garantie. Indexaufnahme von späterer Bearbeitung und Upload unterschieden.

SHA-256: `c38b413560c1906a556b026fa0cb1a5727c620472a2f535369a8f62fa460e43a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 208. Branch – it_0208

Ausgearbeitet und strukturell geprüft: 751 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6674 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-branch.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-switch.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigener temporärer Branchversuch; keine Projekt-Referenzen, Remotes oder offenen fremden Änderungen berührt.

Präzisierung gegenüber der Quelle: Branch als bewegliche Referenz erklärt; Anlegen, Wechseln, Commit und Remote-Zuordnung getrennt. Schutz bei offenen Änderungen differenziert.

SHA-256: `2733df7fcf217c2c94aaec69b4b2f3d026db64b1752adfef24d3c75b2a587c37`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 209. Merge – it_0209

Ausgearbeitet und strukturell geprüft: 748 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6922 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-merge-base.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-merge.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene konfliktfreie temporäre Zweige; keine Konfliktauflösung, produktive Zusammenführung oder Netzwerkoperation getestet.

Präzisierung gegenüber der Quelle: Merge-Richtung, Fast-Forward und Merge-Commit unterschieden; gemeinsame Basis und Grenzen automatischer Konfliktfreiheit erläutert.

SHA-256: `97c6459372920b437fa95878bca84276e529752c067997248660fd3a9e3901f3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 210. Pull – it_0210

Ausgearbeitet und strukturell geprüft: 790 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6970 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-fetch.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-pull.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur zwei eigene lokale temporäre Repositories; kein Internettransport, kein Rebase-/Konfliktfall und kein Pull im Projekt.

Präzisierung gegenüber der Quelle: Pull als Abruf plus Integration erklärt, nicht nur Download. Optionen und Konfiguration differenziert; explizites Fast-Forward statt vorausgesetztem Standardverhalten.

SHA-256: `e82dfbf71ad0e6166e16897e63a4709bf1004036084b03d8729c0186be59452d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 210

Fortsetzung am 21.11.2026 auf Branch `codex/linux-glossar-011-302`, Ausgangscommit `612c62ae00b9459412d27c9bf11af4e1319f3325`. Einträge 191–210 wurden in Quellreihenfolge einzeln recherchiert, geschrieben, geprüft und jeweils vor dem nächsten Eintrag in Index und Fortschritt gespeichert. Tatsächlicher Gesamtstand: 210 von 302; 92 fehlen. Nächster Eintrag: `it_0211` – Push. Der Auftrag bis 302 besteht fort; die gemeinsame Gesamtzusammenfassung folgt erst danach.

Gesamtprüfung erfolgreich: 210 Dokumente, Originalzuordnung, unverändertes Indexschema, lückenlose records, documented_records, genaue sortierte Quellenvereinigung, JSON-kompatible Metadaten, zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. 142 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut mit erfolgreichen Assertions, Exitcodes und exakten Ausgaben ausgeführt. Quelle unverändert mit dem vereinbarten SHA-256; 302 eindeutige IDs und Begriffe. Alle bisherigen 190 Texte und ihre vollständigen Indexdatensätze gegenüber dem Ausgangscommit unverändert; Pilottexte und Pilotindex zusätzlich gegen `688a83204d653b7977d11848ac813d400a7b1b8f` geprüft. PROMPT.md unverändert. Semantische Linkbeschriftungen der neuen Texte gegen den Katalog geprüft. Änderungen ausschließlich unter docs/linux-glossar/; git diff --check erfolgreich.

Die neuen Datenbankbeispiele verwenden eigene temporäre Dateien beziehungsweise In-Memory-Datenbanken mit SQLite 3.46.1. Die Git-Beispiele verwenden eigene temporäre Repositories mit Git 2.52.0, ohne Übernahme von Vorlagen und ohne persönliche oder systemweite Git-Konfiguration in den Kindprozessen. Keine bestehenden Anwendungsdaten oder Projekt-Referenzen für Übungen geändert; kein zusätzlicher Projekt-Worktree und keine Netzwerktransporte in den Git-Beispielen. NoSQL und ORM sind ausdrücklich nicht ausgeführte Gedankenbeispiele. Nichts installiert. Primärquellen über HTTPS geprüft; nicht abrufbare Webdarstellungen durch offizielle Git-Dokumentationsquellen ersetzt. Alle neuen Texte bleiben review_pending. Fachliche Zweitprüfung und lokale Reader-Abnahme stehen aus; die temporäre kompatible Kopfprüfung im vorhandenen Markdown-Parser ist keine Reader-Abnahme.

## 211. Push – it_0211

Ausgearbeitet und strukturell geprüft: 796 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7121 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-push.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-remote.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene lokale temporäre Quelle und Bare-Ziel; kein Force-Push, Git-Netzwerktransport oder Dienstablauf.

Präzisierung gegenüber der Quelle: Push überträgt gespeicherte Objekte und aktualisiert ausgewählte Referenzen, nicht offene Arbeitsdateien. Zielkonfiguration, Schutzregeln, Merge und Veröffentlichung getrennt.

SHA-256: `8400878d944c59d3032e35e3004841773ab7139a2ce5bf5a57c16febbb46df37`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 212. Clone – it_0212

Ausgearbeitet und strukturell geprüft: 777 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7052 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-clone.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/gitrepository-layout.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene temporäre lokale Quelle und Kopie; kein fremder Download, Internettransport, zusätzlicher Projekt-Worktree oder Ausführen von Projektcode.

Präzisierung gegenüber der Quelle: Clone von Dateikopie, ZIP, Installation und automatischer Synchronisierung getrennt. Begrenzte Historie, Remote-Referenzen und nicht übernommene offene Quelldateien erläutert.

SHA-256: `845ad3855f8b63d3324fc1ae69763a8bb7a4f1b39797c0cc0c29aa37c1ad853d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 213. Fork – it_0213

Ausgearbeitet und strukturell geprüft: 752 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6415 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.github.com/en/pull-requests/how-tos/work-with-forks/syncing-a-fork
- https://docs.github.com/en/pull-requests/reference/forks

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Gedankenbeispiel; kein Fork, Konto, Vorschlag, Plattform-Schreibzugriff oder Nachricht angelegt.

Präzisierung gegenüber der Quelle: Fork als eigenständig verwaltete Abzweigung erklärt; GitHub-Regeln ausdrücklich plattformspezifisch. Von Clone, Branch, automatischer Synchronisierung und Unix-Prozessbegriff getrennt.

SHA-256: `06f05f1039d164fb57b0e1c4e8edaaef8131000fcba969ad1d2d5b8bd08eceb5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 214. Pull Request – it_0214

Ausgearbeitet und strukturell geprüft: 751 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6325 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/changing-the-stage-of-a-pull-request
- https://docs.github.com/en/pull-requests/reference/pull-requests

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Gedankenbeispiel; kein zusätzlicher PR, keine Reviewer-Zuweisung, Nachricht oder Integration.

Präzisierung gegenüber der Quelle: Vorschlag und tatsächliche Integration getrennt; Ablehnung, Aktualisierungen und Entwurfsstatus erklärt. GitHub-Funktionen ausdrücklich plattformspezifisch, keine allgemeine Review-Garantie.

SHA-256: `b949883d34d7e7bffa6f62003e7598ae9c3ac3cfda6d90e088db7f86dbe7c8d5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 215. Conflict – it_0215

Ausgearbeitet und strukturell geprüft: 789 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7226 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-diff.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-merge.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigener temporärer Text-Merge-Konflikt samt Auflösung und Abschluss; keine Binär-, Lösch-, Rebase-Konflikte oder produktiven Dateien getestet.

Präzisierung gegenüber der Quelle: Konflikt als angehaltene technische Integration von fachlicher Unverträglichkeit unterschieden. Weitere Konfliktarten und verfahrensabhängige Fortsetzung eingeordnet.

SHA-256: `210d988e28c2830c5c453f2f2be9ec12481e91010bdd54621a0fb57e843d5e7a`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 216. Tag – it_0216

Ausgearbeitet und strukturell geprüft: 786 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7004 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-push.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-tag.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene temporäre einfache und annotierte Tags; keine Signaturprüfung, Veröffentlichung, Übertragung oder bestehende Projektmarkierung verändert.

Präzisierung gegenüber der Quelle: Lightweight- und annotierte Tags, stehende Markierung und beweglicher Branch getrennt. Tagname keine Release-/Stabilitätsgarantie; Austausch und Signatur gesondert eingeordnet.

SHA-256: `6a83ab6f0429b25b5cb3c41d0fdac9337843c3a76503e1d68e083abeec093524`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 217. Staging – it_0217

Ausgearbeitet und strukturell geprüft: 775 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6815 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/git/git/master/Documentation/git-add.adoc
- https://raw.githubusercontent.com/git/git/master/Documentation/git-diff.adoc

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur zwei eigene temporäre Textdateien; kein Projekt-Staging, Commit, Netzwerktransport, interaktive Patchauswahl oder Konfliktfall.

Präzisierung gegenüber der Quelle: Staging als Inhaltsauswahl im Index erklärt; spätere Bearbeitung, untracked Dateien und verschiedene Diff-Vergleiche getrennt. Nicht mit Bereitstellungsumgebung gleichgesetzt.

SHA-256: `d7cd2f3e384b43079018afad4ff9cc8876bbe75bdfa64517fde8e6b1473d7b9f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 218. Architektur – it_0218

Ausgearbeitet und strukturell geprüft: 768 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6618 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
- https://learn.microsoft.com/en-us/azure/architecture/guide/design-principles/

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht implementiertes Gedankenmodell einer eigenen Notizanwendung; keine Repository-Architekturprüfung, Messung oder Dienständerung.

Präzisierung gegenüber der Quelle: Architektur über Ordnerstruktur hinaus als Verantwortlichkeiten, Beziehungen und wichtige Entscheidungen erklärt. Cloud-Primärquellen ausdrücklich kontextualisiert; keine Behauptung über NetMon-Implementierung.

SHA-256: `cef3be5a8060e47882f883893195c6ed1847e8409711edfcdac387bd44146449`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 219. Modularisierung – it_0219

Ausgearbeitet und strukturell geprüft: 754 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6755 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/importlib.html#importlib.util.spec_from_file_location
- https://docs.python.org/3.13/tutorial/modules.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur selbst erzeugtes temporäres Python-Modul mit Erfolgs- und Fehlerfall; keine DNS-Abfrage, Installation, Anwendungsänderung oder Austauschbarkeitsabnahme.

Präzisierung gegenüber der Quelle: Modularisierung als Aufgaben- und Schnittstellengestaltung erklärt, nicht bloß Dateiaufteilung. Austauschbarkeit, Seiteneffekte und zyklische Abhängigkeiten differenziert.

SHA-256: `4ff81b5389af6f9ec7a8cde240c987a01e7aca4dc4580f7c04cc7d31002c2fc9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 220. MVC – it_0220

Ausgearbeitet und strukturell geprüft: 775 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6486 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://developer.mozilla.org/en-US/docs/Glossary/MVC
- https://doc.qt.io/qt-6/model-view-programming.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Aufgabenlistenmodell; keine GUI gestartet, Implementierung, Klickprüfung, Speicherung oder Reader-Abnahme behauptet.

Präzisierung gegenüber der Quelle: MVC-Rollen von Klassen-/Dateizahl und Datenbanktabellen getrennt; Qt Model/View mit Delegates ausdrücklich als Frameworkvariante eingeordnet.

SHA-256: `44eafca64c20d84e0a39fb26b1546f5b6d3b84325ed6dcc4b8458000dca30df3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 220

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `f6ec7ea8034dc064164f1f5d4b738ba21902de06`. Einträge 211–220 einzeln in Quellreihenfolge recherchiert, geschrieben und geprüft; Index und Fortschritt nach jedem Abschluss gespeichert. Tatsächlicher Stand: 220 von 302, noch 82 offen. Nächster Eintrag: `it_0221` – Plugin. Der Auftrag bis 302 bleibt aktiv; keine Gesamtfertigmeldung.

Gesamtprüfung aller 220 Dokumente erfolgreich: Quelle und 302 eindeutige Originaldatensätze, unverändertes Indexschema und Originalzuordnung, lückenlose Reihenfolge, documented_records, genaue sortierte duplikatfreie Quellenvereinigung, Metadaten, zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche SHA-256-Prüfsummen. 148 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich ausgeführt, Assertions und vollständige Ausgaben geprüft. Sämtliche bisherigen 210 Texte und Indexdatensätze gegenüber dem Ausgangscommit unverändert. Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Neue Linkbeschriftungen stimmen semantisch mit den verlinkten Katalogbegriffen überein. Exakter Änderungsumfang nur neue Texte 211–220 sowie Index und Fortschritt; git diff --check erfolgreich.

Sechs neue ausführbare Beispiele: eigene temporäre Git-Tests für Push, Clone, Textkonflikt, Tags und Staging sowie ein selbst erzeugtes Python-Modul. Vier ausdrücklich nicht ausgeführte Gedankenbeispiele zu Fork, Pull Request, Architektur und MVC. Keine zusätzlichen Hostingaktionen für die Beispiele, kein Git-Netzwerktransport, kein produktiver Merge, keine neuen Projekt-Worktrees und keine fremden Module ausgeführt. Git 2.52.0 und Python 3.13 bereits vorhanden, nichts installiert. Architekturquellen mit Cloudkontext gekennzeichnet; Qt Model/View von allgemeinem MVC unterschieden. Alle neuen Texte review_pending. Fachliche Zweitprüfung und lokale Reader-Abnahme weiterhin offen; Strukturprüfung mit temporärem kompatiblem Kopf im vorhandenen Markdown-Parser ist keine Reader-Abnahme.

## 221. Plugin – it_0221

Ausgearbeitet und strukturell geprüft: 750 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6598 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/importlib.metadata.html#entry-points
- https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/guides/creating-and-discovering-plugins.rst

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Export-Gedankenmodell; keine Plugins gesucht, geladen, installiert oder aktiviert und keine vorhandene Anwendung geändert.

Präzisierung gegenüber der Quelle: Plugin als vertraglich eingebundene Erweiterung erklärt; Erkennung, Laden und Ausführung getrennt. Python Entry Points als konkrete Möglichkeit, keine automatische Sandbox oder Verträglichkeitsgarantie.

SHA-256: `4654a1119b35ac57d08e005109b379b999ca774b45427b7449f9bf3fd6f9a708`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 222. Dependency – it_0222

Ausgearbeitet und strukturell geprüft: 734 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6758 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/importlib.metadata.html#distribution-requirements
- https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/specifications/dependency-specifiers.rst

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Modell mit erfundenen Paketnamen; keine Installation, Paketauflösung oder Änderung von Abhängigkeiten und Umgebungen.

Präzisierung gegenüber der Quelle: Direkte, transitive, optionale und zweckgebundene Anforderungen getrennt. Python-Spezifikationen kontextualisiert; deklarierte Metadaten und Versionsbereiche keine Laufzeit-/Kompatibilitätsgarantie.

SHA-256: `3caa590c4ea497dbe10380bef989c6428a9f6ed4e68a0f29842ab830cb04559f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 223. Dependency Injection – it_0223

Ausgearbeitet und strukturell geprüft: 743 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6503 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/overview
- https://martinfowler.com/articles/injection.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Test mit übergebener Listensammelfunktion; kein echtes Logging, Dateizugriff, Container oder Dienst getestet.

Präzisierung gegenüber der Quelle: Übergabe benötigter Fähigkeiten von Container und Service Locator unterschieden. .NET-Details und Fowlers Java-Beispiele kontextualisiert; Lebensdauer und Ersatzgrenzen erläutert.

SHA-256: `320108b2be968519be717554cd7e4ed06f3365c1c8e7ddc21f596147fe99bb4b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 224. Singleton – it_0224

Ausgearbeitet und strukturell geprüft: 699 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6390 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/logging.html#logging.getLogger
- https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/service-lifetimes

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Test zeigt nur Logger-Wiederverwendung pro Name; kein klassischer Singleton implementiert, keine Thread-/Prozess-Einzigkeit oder Container-Lebensdauer abgenommen.

Präzisierung gegenüber der Quelle: Klassisches Singleton, Container-Lebensdauer und Namensregistrierung getrennt. Geltungsbereich, Testzustand und fehlende automatische Threadsicherheit ausdrücklich eingeordnet.

SHA-256: `297bbac25cc122e7930880704e78836a7e440301929a70bc364231e182cf1b3e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 225. Factory – it_0225

Ausgearbeitet und strukturell geprüft: 725 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6496 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qstylefactory.html#create
- https://docs.python.org/3.13/library/json.html#json.dumps
- https://docs.python.org/3.13/library/logging.html#logging.setLogRecordFactory

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Python-Auswahl zwischen Text- und JSON-Darstellung samt Fehlerfall; keine Qt-/Logging-Factory geändert, Plugins gesucht oder Scanner-/Netzwerkfunktion ausgeführt.

Präzisierung gegenüber der Quelle: Factory als gekapselte Erzeugung erklärt; einfache Auswahlfunktion von Factory Method und Abstract Factory getrennt. Rückgabe, Fehler und Objektlebensdauer ausdrücklich vertraglich eingeordnet.

SHA-256: `c799241d23b127edb565e5c62c70d156b03b3580fead1bfbd75af089f56f6831`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 226. Observer – it_0226

Ausgearbeitet und strukturell geprüft: 713 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6486 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qobject.html#disconnect
- https://doc.qt.io/qt-6/signalsandslots.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene synchrone Python-Statusliste mit Anmeldung, Unterdrückung gleicher Werte und Abmeldung geprüft; kein Scan, GUI-, Thread- oder Queue-Test.

Präzisierung gegenüber der Quelle: Observer von Polling, Warteschlange und automatischer Asynchronität getrennt. Qt-Verbindungsregeln versionsabhängig; Lebensdauer, Fehler und doppelte Anmeldungen als Vertragsfragen erläutert.

SHA-256: `96159df44ae1a9328641cd2053f8c185e803b702723e4e6a94c7ff06ac958fa1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 227. State – it_0227

Ausgearbeitet und strukturell geprüft: 743 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6624 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://doc.qt.io/qt-6/qstatemachine.html
- https://docs.python.org/3.13/library/enum.html#enum.Enum

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Python-Zustandsfolge und abgelehnter Wechsel; kein Scan, GUI-, Parallelitäts-, Speicher- oder Wiederanlauftest einer Anwendung.

Präzisierung gegenüber der Quelle: Allgemeinen Zustand, vereinfachten Status, Zustandsautomaten und State-Entwurfsmuster getrennt. Enum garantiert keine Übergänge; Qt-Ausführung nicht auf das synchrone Beispiel übertragen.

SHA-256: `a2623cee21e8e57b81286255c922cc9ad96dfefbf6af8944cc33c1d7b2955387`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 228. Config – it_0228

Ausgearbeitet und strukturell geprüft: 720 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6389 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/configparser.html#supported-datatypes
- https://docs.python.org/3.13/library/tomllib.html#tomllib.load

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Nur eigene INI-Zeichenketten im Speicher; keine Dateien gelesen/geschrieben, DNS-, Netzwerk-, Geräte- oder Diensteinstellungen verändert.

Präzisierung gegenüber der Quelle: Konfiguration von einzelner Datei, Laufzeitstatus und Typprüfung getrennt. Quellenpriorität und Wirksamkeitszeitpunkt anwendungsabhängig; ConfigParser-Zeichenketten und getboolean ausdrücklich erklärt.

SHA-256: `3f1a8c0071e01ad4205c8ad531b6d93f0c7d4c3871a6e018013e932ea6bbae36`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 229. Feature Flag – it_0229

Ausgearbeitet und strukturell geprüft: 729 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6615 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://learn.microsoft.com/en-us/azure/azure-app-configuration/feature-management-python-reference
- https://openfeature.dev/specification/sections/flag-evaluation/

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Darstellungstest mit gesonderter simulierter Zugriffsentscheidung; keine echte Autorisierung, Lizenzprüfung, Zielgruppenverwaltung oder Produktaktivierung abgenommen.

Präzisierung gegenüber der Quelle: Funktionsauswahl von Berechtigung/Lizenz und Veröffentlichung getrennt. Standardwerte, Aktualisierungsgrenzen, Kombinationen und nicht rücknehmbare Wirkungen eingeordnet.

SHA-256: `313b30598ab77c678d9170d85b19bb04f8cde913d98822338e791d8b31aa70d0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 230. Cache – it_0230

Ausgearbeitet und strukturell geprüft: 752 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6407 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/functools.html#functools.lru_cache
- https://www.rfc-editor.org/rfc/rfc1035.html#section-3.2.1
- https://www.rfc-editor.org/rfc/rfc9111.html#section-4.2

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Funktionscache mit gezählten Quellzugriffen, veraltetem Wert und cache_clear geprüft; kein DNS-/Netzwerkzugriff, Löschen vorhandener Dateien, Zeitablauf- oder Leistungstest.

Präzisierung gegenüber der Quelle: Zwischenspeicherung von Gültigkeit, Verdrängung, Puffer und Backup getrennt. DNS- und HTTP-Regeln kontextualisiert; lru_cache besitzt keine automatische Quelleninvalidierung oder TTL.

SHA-256: `72dd279a21f0d0d03b9778772ad7c2263168fa04b25d7fdb29e4ccc04bd5dbdf`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 230

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `92e815e360bdc6ea710ce688a76554c334a6c33b`. Einträge 221–230 in Quellreihenfolge einzeln recherchiert, geschrieben, geprüft und jeweils in Index und Fortschritt gespeichert. Tatsächlicher Gesamtstand: 230 von 302; noch 72 offen. Nächster Eintrag: `it_0231` – Queue Worker. Auftrag bis 302 weiterhin aktiv; die gemeinsame Gesamtzusammenfassung steht noch aus.

Gesamtprüfung erfolgreich für alle 230 Dokumente: unveränderte Quelle mit erwartetem SHA-256 und 302 eindeutigen IDs/Begriffen; Metadaten und Kategorieableitung; exakte vollständige Originalzuordnung; unverändertes Indexschema; lückenlose records und documented_records; sortierte duplikatfreie Vereinigung der genauen Eintragsquellen; zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. 156 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich mit Assertions, Exitcodes und vollständigen Ausgaben geprüft. Alle bisherigen 220 Texte und Indexdatensätze sowie PROMPT.md gegenüber dem Ausgangscommit unverändert. Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Semantische Linkbeschriftungen der neuen Texte mit den Originalbegriffen verglichen. Ausschließlich neue Texte 221–230 sowie Index und Fortschritt verändert; git diff --check erfolgreich.

Acht neue ausgeführte Python-Beispiele zu Übergabe einer Meldungsfunktion, begrenzter Logger-Wiederverwendung, Factory-Auswahl, synchronem Observer, Zustandsübergängen, eigenen Config-Zeichenketten, Feature-Flag-Auswahl und eigenem Funktionscache. Zwei nicht ausgeführte Gedankenbeispiele zu Plugins und Paketabhängigkeiten. Kein Plugin, Paket, Framework oder SDK installiert; kein fremder Code geladen; keine bestehenden Konfigurationsdateien, Dienste, Konten, Geräte oder Netzwerkeinstellungen verändert. Kein echter Scan, DNS-Zugriff, Pro-Modus oder Berechtigungssystem getestet. Framework- und Protokollbesonderheiten von den allgemeinen Begriffen getrennt. Alle neuen Texte review_pending; fachliche Zweitprüfung und lokale Reader-Abnahme offen. Temporäre Prüfung der Textstruktur im vorhandenen Markdown-Parser ist keine Reader-Abnahme.

## 231. Queue Worker – it_0231

Ausgearbeitet und strukturell geprüft: 733 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6597 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/queue.html#queue.Queue
- https://docs.python.org/3.13/library/queue.html#queue.Queue.join
- https://docs.python.org/3.13/library/queue.html#queue.Queue.task_done

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Thread verarbeitet zwei harmlose Texte und Stoppsignal; Threadende kontrolliert. Keine Netzwerkchecks, GUI-, Absturz-, Wiederholungs- oder Mehrworkerprüfung.

Präzisierung gegenüber der Quelle: Worker von Warteschlange und Cache getrennt; FIFO-Entnahme, Abschlussmeldung, Threadende und fachlicher Erfolg unterschieden. Keine Dauerhaftigkeits- oder Genau-einmal-Garantie.

SHA-256: `be31d97585bffe3c29f67c17c6041951e58c17d8b85f9c50ad3d5ebf75bff1e0`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 232. Authentifizierung – it_0232

Ausgearbeitet und strukturell geprüft: 725 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6491 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Authentication_Cheat_Sheet.md
- https://raw.githubusercontent.com/usnistgov/800-63-4/nist-pages/sp800-63b/introduction/index.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Modell eines erfundenen Kontos; keine Anmeldung, Passwortprüfung, MFA-, Sitzungs- oder Wiederherstellungsabnahme und keine Kontenänderung.

Präzisierung gegenüber der Quelle: Digitale Authentifizierung als Prüfung zugeordneter Nachweise präzisiert; von Identifikation, realer Identitätsprüfung, Sitzung und Berechtigung getrennt. Faktorarten und Richtliniengeltungsbereich eingeordnet.

SHA-256: `9b5691ae367ba2112a26b7ff92906e36fc3312df0b4548cc886978173ca6a972`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 233. Autorisierung – it_0233

Ausgearbeitet und strukturell geprüft: 714 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6543 UTF-8-Bytes; 30 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Authorization_Cheat_Sheet.md
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene erfundene Notizen mit erlaubten und drei abgelehnten Speicherzugriffen; keine reale Anmeldung, Rollen-/Rechteänderung oder produktionsreife Autorisierungsabnahme.

Präzisierung gegenüber der Quelle: Aktion-, objekt- und identitätsbezogene Entscheidung von Login, Anzeige und Kennung getrennt. Öffentliche Ressourcen, Identitätsherkunft und getrennte Lese-/Änderungsrechte eingeordnet.

SHA-256: `cdb632ad37f375f2f803f58d04312d3eb81a6659ebdd0aa4c1ce77b5c6f21d31`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 234. Verschlüsselung – it_0234

Ausgearbeitet und strukturell geprüft: 738 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6914 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Cryptographic_Storage_Cheat_Sheet.md
- https://www.rfc-editor.org/rfc/rfc8446.html#section-1

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Transportmodell; keine TLS-Verbindung, Schlüssel, Archive, Datenträger, Bibliotheksinstallation oder Kryptografieabnahme.

Präzisierung gegenüber der Quelle: Vertraulichkeit von Integrität, Authentifizierung, Autorisierung und Verfügbarkeit getrennt. TLS-Kanalschutz und Endpunktspeicherung unterschieden; keine Eigenbau-Kryptografie als Beispiel.

SHA-256: `006133808ffa9a963d732990d639d8d76ffd468d815846c9bab1961b96b078e8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 235. Hashing – it_0235

Ausgearbeitet und strukturell geprüft: 721 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6641 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/hashlib.html
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Password_Storage_Cheat_Sheet.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener SHA-256-Bytevergleich samt Digest-/Hexlänge geprüft; keine Passwortspeicherung, allgemeine Kollisionsfreiheit, Herkunftsprüfung oder Kryptografieabnahme.

Präzisierung gegenüber der Quelle: Hash nicht als kollisionsfreie Kennung, Verschlüsselung oder Herkunftsbeweis dargestellt. Dateiprüfsummen von langsamen gesalzenen Passwortverfahren getrennt; SHA-256-Beispiel ausschließlich harmlose Testbytes.

SHA-256: `c6208e446c0249e00ad739f2a632163b74995b2a11cae8b3adcc96654feabf97`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 236. Salt – it_0236

Ausgearbeitet und strukturell geprüft: 792 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6937 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Password_Storage_Cheat_Sheet.md
- https://raw.githubusercontent.com/usnistgov/800-63-4/nist-pages/sp800-63b/authenticators/index.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht berechnetes Kontenmodell ohne echte Passworttexte oder erfundene Hashausgaben; keine Konten-, Passwortdatei-, Bibliotheks- oder Widerstandsprüfung.

Präzisierung gegenüber der Quelle: Salt als individueller nicht geheimer Zusatz für geeignete Passwortverfahren erklärt; Prüfung mit gespeichertem Salt, Kostenfaktoren und Pepper getrennt. Kein schneller Eigenbau-Passworthash.

SHA-256: `296744481b93a81455c69c6e00c5a9e5485ea83815894e61a90f274996b49b53`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 237. Firewall-Regel – it_0237

Ausgearbeitet und strukturell geprüft: 762 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6699 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://netfilter.org/projects/nftables/manpage.html
- https://wiki.nftables.org/wiki-nftables/index.php/Configuring_chains

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht konfiguriertes Paketmodell mit Dokumentationsadressen; keine Firewall gelesen/gesetzt, privilegierten Befehle, Resolveranfragen, Netzwerktests oder DNS-Schutzabnahme.

Präzisierung gegenüber der Quelle: Regelwirkung im Kontext von Ketten, Hooks, Richtung, Protokollen und Familien erläutert. Erlauben keine Zustellgarantie; Port-53-Modell ausdrücklich kein vollständiger DNS-Schutz.

SHA-256: `2dd9f86b7e6e5315991edc01de473cdb07f6eff2334eea37af85f2906ada0816`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 238. Privilege Escalation – it_0238

Ausgearbeitet und strukturell geprüft: 765 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6829 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.kernel.org/security/credentials.html
- https://man7.org/linux/man-pages/man7/capabilities.7.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht implementiertes Hilfsprogramm-Modell ohne Systempfade/Befehle; keine Schwachstellensuche, Eskalation, privilegierte Aktion oder Rechte-/Konten-/Dienständerung.

Präzisierung gegenüber der Quelle: Unzulässige Rechteausweitung von erlaubter Administration getrennt; mögliche Effekte über Hilfsprogramme und einzelne Capabilities statt pauschal immer Root erklärt.

SHA-256: `35eff6bb15ff2c5414076f9a7442c23a3a7e5ad89c2866a40541d3b4c259d9e5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 239. Least Privilege – it_0239

Ausgearbeitet und strukturell geprüft: 781 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6838 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.kernel.org/userspace-api/no_new_privs.html
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Authorization_Cheat_Sheet.md

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht umgesetztes Exportmodell; keine Prozessisolation, Rechteverringerung, Konten-/Dateirechte-, Capability- oder Dienständerung.

Präzisierung gegenüber der Quelle: Minimalrechte auf Aufgaben, Ressourcen, Dauer und indirekte Wirkungen bezogen. no_new_privs als begrenzten execve-Mechanismus statt vollständiger Rechteentziehung oder Sandbox erklärt.

SHA-256: `e687aa2b1e5cd2a8c0b4d054f9a131d1fde24fa34710e781658f69988caa99a8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 240. Sandbox – it_0240

Ausgearbeitet und strukturell geprüft: 762 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6605 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.kernel.org/userspace-api/landlock.html
- https://docs.kernel.org/userspace-api/seccomp_filter.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht umgesetztes Textverarbeitungsmodell; kein fremder Code, Container/VM, Sicherheitsprofil, Filter oder zusätzlicher Isolationsmechanismus ausgeführt und keine Cloud-Schutzabnahme behauptet.

Präzisierung gegenüber der Quelle: Sandbox über konkrete Grenzen und Freigaben erklärt; Ordner, Paketumgebung, Container und Systemaufruffilter nicht mit vollständiger Isolation gleichgesetzt. Landlock-Funktionen ABI-/kernelabhängig.

SHA-256: `4c2cad0ca4dba9035db685da095efa5b2e6276e3e947be5e88275151bcf2765c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 240

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `bfd253a895d8bc2761bee4c78e7ebf7a23fbebf0`. Einträge 231–240 in Originalreihenfolge einzeln recherchiert, geschrieben und geprüft; Index und Fortschritt jeweils vor dem nächsten Eintrag gespeichert. Tatsächlicher Stand: 240 von 302; 62 fehlen. Nächster Eintrag: `it_0241` – Injection. Freigabe bis 302 besteht fort; gemeinsame Gesamtzusammenfassung noch offen.

Gesamtprüfung aller 240 Dokumente erfolgreich: vollständige Originalzuordnung und Metadaten, Kategorieableitung, unverändertes Indexschema, lückenlose records und documented_records, genaue sortierte duplikatfreie Quellenvereinigung, zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. Quelle unverändert mit erwartetem SHA-256 und 302 eindeutigen IDs/Begriffen. Alle bisherigen 230 Texte und ihre vollständigen Indexdatensätze sowie PROMPT.md gegenüber dem Ausgangscommit unverändert; Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Neue Linkbeschriftungen mit Katalogbegriffen abgeglichen. 159 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich mit Assertions, Exitcodes und exakten Ausgaben ausgeführt. Ausschließlich neue Texte 231–240 sowie Index und Fortschritt geändert; git diff --check erfolgreich.

Drei neue praktische Python-Prüfungen: eigene Queue mit beendetem Worker-Thread, objektbezogene Erlaubnis-/Ablehnungsentscheidung für erfundene Notizen und SHA-256-Vergleich eigener harmloser Bytes. Sieben ausdrücklich nicht ausgeführte Gedankenmodelle zu Authentifizierung, Verschlüsselung, Salt, Firewall-Regel, Privilege Escalation, Least Privilege und Sandbox. Keine echten Anmeldungen, Kontodaten, Passwörter, Schlüssel, Firewall-Regeln oder Systemschutzprofile gelesen beziehungsweise verändert. Keine privilegierten Aktionen, Geräte-, Dienst- oder Netzwerkkonfiguration; keine Installationen. Keine Reader-, GUI-, Kryptografie-, Autorisierungs-, DNS-Schutz- oder Sandbox-Abnahme behauptet. Alle neuen Texte review_pending; fachliche Zweitprüfung und lokale Reader-Prüfung offen. Strukturprüfung nur über temporären kompatiblen Kopf im vorhandenen Markdown-Parser.

## 241. Injection – it_0241

Ausgearbeitet und strukturell geprüft: 775 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6837 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.md
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene SQLite-Speicherdaten mit sicher gebundenem legitimen Apostrophnamen und ungewöhnlichem Datenwert geprüft; keine unsichere Abfrage, Shell, externen Befehle oder fremden Systeme.

Präzisierung gegenüber der Quelle: Injection als Verwechslung von Daten und Anweisungssyntax präzisiert; SQL-Wertbindung von dynamischen Strukturentscheidungen, Shellkontext und Dependency Injection getrennt.

SHA-256: `68f23e3bae27c9b616cd4ee405bb684e1cf1a4c84cee58046729dcbe0f74af84`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 242. Input Validation – it_0242

Ausgearbeitet und strukturell geprüft: 740 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6522 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/ipaddress.html#ipaddress.ip_address
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Input_Validation_Cheat_Sheet.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene IPv4-/IPv6-Textliterale und drei Ablehnungen lokal geprüft; keine DNS-Auflösung, Verbindung, Netzwerk-/Dienste-/Geräteänderung.

Präzisierung gegenüber der Quelle: Syntax und Semantik sowie Normalisierung, sichere Weitergabe und Autorisierung getrennt. IP-Literalprüfung von Hostname, Erreichbarkeit und Nutzungserlaubnis unterschieden; Parser-Verhalten versionsbezogen.

SHA-256: `c2646e0b678f5dca407b44ec0904acff19e7fc3783f436781a6e462df3ff40f8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 243. Escaping – it_0243

Ausgearbeitet und strukturell geprüft: 739 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6555 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/html.html#html.escape
- https://docs.python.org/3.13/library/shlex.html#shlex.quote
- https://docs.python.org/3.13/library/subprocess.html#security-considerations

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene HTML-Zeichenreferenzen und shlex-Rückvergleich geprüft; keine echte Shell, Unterprogramme, Browserausgabe oder Netzwerkoperation ausgeführt.

Präzisierung gegenüber der Quelle: Escaping als kontextgebundene Darstellung erklärt; HTML, POSIX-Shell, Argumentlisten und SQL-Parameter getrennt. Keine universelle Entschärfung oder Validierungs-/Verschlüsselungsgarantie.

SHA-256: `9d1cc53272870edda7a5a37428a12d11f50df39bd2fb0d008da8819d99e553ec`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 244. Secrets – it_0244

Ausgearbeitet und strukturell geprüft: 763 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6548 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/secrets.html
- https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Secrets_Management_Cheat_Sheet.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener nicht registrierter Zufallstestwert ohne Inhaltsausgabe oder Speicherung; nur Form und Vergleich geprüft, keine echte Anmeldung, Token-/Rechteverwaltung oder Laufzeitsicherheitsabnahme.

Präzisierung gegenüber der Quelle: Secrets nach Funktion und Lebenszyklus eingeordnet; öffentliche Schlüssel und Salt getrennt. Versteckte Dateien, Umgebungsvariablen und aktuelle Git-Löschung keine universellen Schutzgarantien.

SHA-256: `7cfb994b905c140b4847c63d7e1f973eca293bfa808494e65a9a5761e43c875d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 245. Keyring – it_0245

Ausgearbeitet und strukturell geprüft: 760 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6732 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.kernel.org/security/keys/core.html
- https://specifications.freedesktop.org/secret-service/latest/ch01.html
- https://specifications.freedesktop.org/secret-service/latest/ch10.html
- https://specifications.freedesktop.org/secret-service/latest/unlocking.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Speichermodell; keine echten Zugangswerte, Keyring-Abfragen, Entsperrungen, Dialoge, Konten-, Schlüssel- oder Dienständerungen.

Präzisierung gegenüber der Quelle: Desktop-Secret-Service von Kernel-Keyrings getrennt. Abgerufener Secret-Service-Entwurf 0.2, nicht geheime Suchattribute, Sperr-/Fehlerzustände und nicht vorgeschriebene Zugriffskontrolle ausdrücklich eingeordnet.

SHA-256: `92af80a36fe39f714b749ed067367abcf6dc0f97ab4c7b15666862909ede73b1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 246. Test – it_0246

Ausgearbeitet und strukturell geprüft: 741 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6439 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/unittest.html
- https://raw.githubusercontent.com/pytest-dev/pytest/main/doc/en/how-to/assert.rst

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Notizlistenmodell; kein GUI-/DNS-/End-to-End-Lauf, keine Änderung bestehender Anwendungstests oder Behauptung einer Reader-Abnahme.

Präzisierung gegenüber der Quelle: Test als begrenzte Beobachtung mit unabhängiger Erwartung erklärt; Erfolg, Fehlerfall, übersprungene Fälle, Review und statische Prüfung getrennt. Keine automatische Vollständigkeitsgarantie.

SHA-256: `95ef91062163890615576f09c04ef4496b7054f1fbf6d8a16e8107cc94ff9ae1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 247. Unit Test – it_0247

Ausgearbeitet und strukturell geprüft: 740 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6543 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/unittest.html#basic-example
- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.assertRaises

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei eigene unittest-Fälle mit Standardbibliothek im temporären Skript ausgeführt; keine App-Imports, vorhandenen Testsuite-Dateien oder Integrations-/GUI-Abnahme.

Präzisierung gegenüber der Quelle: Unit als gewählte kleine Vertragsgrenze erklärt, nicht zwingend einzelne Methode. Beobachtbare Erwartungen, vorgesehene Fehler und Grenzen von Ersatzobjekten/Erfolg getrennt.

SHA-256: `41e131f653f338c4c59d0a1bc4a7c3d7563ab8819f5594ad3ff50dd30adc8d33`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 248. Integrationstest – it_0248

Ausgearbeitet und strukturell geprüft: 770 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6876 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/sqlite3.html#sqlite3.connect
- https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests?view=aspnetcore-10.0

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-/SQLite-Dateirundlauf mit Commit, Verbindungswechsel und kontrolliertem Aufräumen; keine App-Imports, vorhandenen Tests, Server, Konkurrenz-, Stromausfall- oder End-to-End-Prüfung.

Präzisierung gegenüber der Quelle: Integration als benannte gemeinsame Prüfgrenze erklärt. ASP.NET-Core-Werkzeuge kontextualisiert; tatsächliche SQLite-Datei mit neuer Verbindung von GUI-/Netzwerk-/Fremddatenbankabnahme getrennt.

SHA-256: `8da6b9c477b730548f0105775b6fa2ecfae9691ab6dc3130ec15be32a96c89c3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 249. End-to-End-Test – it_0249

Ausgearbeitet und strukturell geprüft: 757 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6599 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://playwright.dev/docs/best-practices
- https://playwright.dev/docs/writing-tests

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Notizoberflächenmodell; keine Browser-/GUI-Installation, Klick-, Netzwerk-, Scan-, Produkt- oder Reader-Abnahme.

Präzisierung gegenüber der Quelle: End-to-End als vollständigen benannten Ablauf mit begrenztem Umfang erklärt; Browserwerkzeuge von Desktop-/Readerprüfung getrennt. Erwartungen, Bedingungen und Ersatzstellen statt bloßer Aktionsfolge.

SHA-256: `4c7ccad43d02b6affd7ef0a16ec469062a6facc6527080ec12d00cab160d9050`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 250. Mock – it_0250

Ausgearbeitet und strukturell geprüft: 741 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6639 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/unittest.mock.html#auto-speccing
- https://docs.python.org/3.13/library/unittest.mock.html#unittest.mock.Mock.side_effect

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener Python-Mock mit Signaturvorlage, Rückgabe, Aufrufkontrolle und simuliertem TimeoutError geprüft; kein realer Dienst, Netzfehler, App-Import oder bestehende Testsuite verändert.

Präzisierung gegenüber der Quelle: Mock als begrenztes kontrolliertes Test Double erklärt; Rückgabeverarbeitung und Aufrufprüfung getrennt. Autospeccing und simulierte Fehler keine echte Integrations-/Timeoutabnahme.

SHA-256: `941f7a4ca2f82f32292578934f209939db9e11fb8c0bf396a805d822df86d1c3`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 250

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `31c1886a8a9f2e176463e9a8d07647b380e5115f`. Einträge 241–250 einzeln in Quellreihenfolge recherchiert, geschrieben, geprüft und nach jedem Abschluss in Index und Fortschritt gespeichert. Tatsächlicher Gesamtstand: 250 von 302; noch 52 offen. Nächster Eintrag: `it_0251` – Fixture. Der Auftrag bis 302 bleibt aktiv; gemeinsame Gesamtzusammenfassung noch ausstehend.

Gesamtprüfung aller 250 Dokumente erfolgreich: Quelle unverändert mit erwartetem SHA-256, 302 eindeutige IDs/Begriffe; vollständige Originalzuordnung, Metadaten und Kategorieableitung; unverändertes Indexschema, lückenlose records und documented_records; genaue sortierte duplikatfreie Quellenvereinigung; zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. Alle bisherigen 240 Texte und Indexdatensätze sowie PROMPT.md gegenüber dem Ausgangscommit unverändert, Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Neue Linkbeschriftungen mit Katalogbegriffen abgeglichen. 166 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich ausgeführt, Assertions, Exitcodes und vollständige Standardausgaben geprüft. Exakter Änderungsumfang neue Texte 241–250 sowie Index und Fortschritt; git diff --check erfolgreich.

Sieben neue ausführbare Python-Beispiele: sichere SQLite-Wertbindung, lokale IP-Literalprüfung, HTML-/POSIX-Shell-Textdarstellung, eigener nicht registrierter Zufallswert ohne Inhaltsausgabe, zwei eigene Unit-Testfälle, temporärer SQLite-Dateirundlauf und kontrollierter Mock. Drei nicht ausgeführte Gedankenmodelle zu Keyring, allgemeinem Test und End-to-End-Test. Keine unsichere SQL-Variante oder echte Shell ausgeführt; keine Verbindungen oder echten Zugangsdaten verwendet. Kein Keyring gelesen/entsperrt, keine Browser-/GUI-Werkzeuge installiert, keine vorhandenen Anwendungstests verändert. Secret-Service-Quelle als abgerufenen Entwurf 0.2 gekennzeichnet. Keine echte Login-, Rechte-, Netzwerk-, End-to-End- oder Reader-Abnahme behauptet. Alle neuen Texte review_pending; fachliche Zweitprüfung und lokale Reader-Prüfung offen. Strukturprüfung im vorhandenen Markdown-Parser mit ausschließlich temporärem kompatiblem Kopf.

## 251. Fixture – it_0251

Ausgearbeitet und strukturell geprüft: 753 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7098 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tempfile.html#tempfile.TemporaryDirectory
- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.addCleanup
- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.setUp

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei eigene unittest-Fälle mit jeweils frischer temporärer Textdatei ausgeführt; Ausgangsinhalt und abschließende Entfernung beider Ordner geprüft. Keine vorhandenen Tests oder Dateien verändert.

Präzisierung gegenüber der Quelle: Fixture als verwaltete Ausgangsbedingungen mit Lebensdauer/Aufräumen erklärt; unittest-setUp und rechtzeitig registrierte Cleanups kontextualisiert. Temporäre Ablage keine Sandbox.

SHA-256: `edcbcbc0b465cab3101172caa1cc3fdf2a62ee3a1e87eb55a7800ef83ee17c4e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 252. Assertion – it_0252

Ausgearbeitet und strukturell geprüft: 741 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6732 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/unittest.html#unittest.TestCase.assertEqual
- https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene minimale Python-Datei normal und mit -O gestartet; erwarteten AssertionError beziehungsweise dessen Wegfall kontrolliert, keine vorhandenen Tests/Sicherheitsprüfungen verändert.

Präzisierung gegenüber der Quelle: Assertion als präzise Erwartung von Gleichheit/Wahrheit/Identität und produktiver Prüfung getrennt. Python-assert unter -O ausdrücklich nicht unverzichtbare Sicherheitskontrolle; Frameworkmethoden gesondert.

SHA-256: `dc6db515543946724c0d10d334d85b2d0243e97064f4dd02b96ad9bd64843d8d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 253. Regression – it_0253

Ausgearbeitet und strukturell geprüft: 742 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6416 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/test.html
- https://docs.python.org/3.13/library/unittest.html#organizing-test-code

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene frühere und absichtlich verschlechterte Textfunktion verglichen; keine App-Regressionsmeldung, vorhandene Testsuite oder Leistungsprüfung.

Präzisierung gegenüber der Quelle: Regression über Wiederkehr desselben Bugs hinaus als Verschlechterung früheren Verhaltens erklärt; Anforderungsänderung, Testfehlschlag und Ursache getrennt. Python-internes test-Paket nicht als App-Werkzeug verwendet.

SHA-256: `835ebf6c8ebd6a26b3682647daf4fad4f2393f1bb996e4919376d73408507008`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 254. Linting – it_0254

Ausgearbeitet und strukturell geprüft: 757 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6767 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/astral-sh/ruff/main/crates/ruff_linter/src/rules/pyflakes/rules/unused_import.rs
- https://raw.githubusercontent.com/astral-sh/ruff/main/docs/linter.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Vorhandenes Ruff 0.17.5 prüft nur eigene temporäre kompilierbare Datei, F401 gezielt erkannt, Dateibytes unverändert; nichts installiert, keine App- oder Testkonfiguration verändert.

Präzisierung gegenüber der Quelle: Linting von Syntaxprüfung, Formatter, Tests und Typprüfung getrennt. Ruff-Regelauswahl/Version und erwarteter Verstoß-Exitcode ausdrücklich eingeordnet; keine automatische Korrektur.

SHA-256: `d691c90f26d0c8a77274b104f1642c14303d7f4dada88426c898d0cb3e38ce32`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 255. Formatter – it_0255

Ausgearbeitet und strukturell geprüft: 775 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 7029 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/psf/black/main/docs/the_black_code_style/current_style.md
- https://raw.githubusercontent.com/psf/black/main/docs/usage_and_configuration/the_basics.md

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Vorhandenes Black 26.10.1 auf einer eigenen temporären Quelldatei pro Aufruf geprüft; Formatänderung, gleicher AST und anschließender erfolgreicher --check kontrolliert, keine App-/Test-/Projektdateien verändert.

Präzisierung gegenüber der Quelle: Formatter von Linter, Laufzeitprüfung und Review getrennt. Black-Version, Prüf-/Schreibmodus, Rückgabewerte und begrenzte AST-Kontrolle eingeordnet.

SHA-256: `65baee888e58e12bcaf2fc8052d6aeca5b74f49ed4eef8d13f3f00343f80a071`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 256. Code Review – it_0256

Ausgearbeitet und strukturell geprüft: 753 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6495 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://google.github.io/eng-practices/review/reviewer/looking-for.html
- https://google.github.io/eng-practices/review/reviewer/standard.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Review-Modell; keine echte Fehlerstelle behauptet, Reviewer zugewiesen, Nachricht/Kommentar versandt oder unabhängige Glossar-/Reader-Freigabe behauptet.

Präzisierung gegenüber der Quelle: Review als menschliche Beurteilung eines konkreten Stands erklärt; Tests, Werkzeuge, Stilwünsche und unabhängige Zweitprüfung getrennt. Google-Praktiken als organisationsbezogene Primärquelle eingeordnet.

SHA-256: `31348b8a4f8691f2b277610b9eac0e4ab884782e810b9c86cb97a628638db125`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 257. CI – it_0257

Ausgearbeitet und strukturell geprüft: 754 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6664 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.github.com/en/actions/get-started/continuous-integration
- https://martinfowler.com/articles/continuousIntegration.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Workflow-Modell; keine CI-Datei, manueller Lauf, Runner, Konten-/Secrets-/Berechtigungsänderung, Merge oder Veröffentlichung angelegt.

Präzisierung gegenüber der Quelle: CI über automatische Tests hinaus als regelmäßige Integration mit Rückmeldung erklärt. Plattformauslöser, Commitbezug, übersprungene Prüfungen und Veröffentlichung getrennt.

SHA-256: `3217a7953245a2e8ee935511dfc9a36a6299100297908b2ff5c883479bb3d21f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 258. Coverage – it_0258

Ausgearbeitet und strukturell geprüft: 749 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6713 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/trace.html#trace.Trace
- https://raw.githubusercontent.com/nedbat/coveragepy/master/doc/branch.rst
- https://raw.githubusercontent.com/nedbat/coveragepy/master/doc/howitworks.rst

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene temporäre falsche Funktion vollständig im ausdrücklich gewählten Zeilenausschnitt erreicht und falsches Ergebnis nachgewiesen; Dateizuordnung für trace gesetzt. Keine Bibliothek installiert, App-/Testsuite-/CI-Coverage verändert.

Präzisierung gegenüber der Quelle: Coverage als Ausführungsmaß mit erklärtem Nenner statt Korrektheitsbeweis erklärt; Zeilen-/Statement- und Branch-Abdeckung getrennt. Standard-trace-Modell keine coverage.py-/Projektmessung.

SHA-256: `8e06d5e10ca878f24fd648ad083e986a05ade10bbd7e01536a0b2c9bda33628d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 259. Thread – it_0259

Ausgearbeitet und strukturell geprüft: 733 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6499 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/threading.html#gil-and-performance-considerations
- https://docs.python.org/3.13/library/threading.html#threading.Thread.join
- https://man7.org/linux/man-pages/man7/pthreads.7.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener kurzlebiger Python-Thread mit gleicher PID, anderer Threadkennung und erwarteter Textausgabe geprüft; Ende kontrolliert, keine GUI-/Netzwerk-/Leistungs- oder allgemeine Synchronisierungsabnahme.

Präzisierung gegenüber der Quelle: Thread von Prozessisolierung, Worker-Rolle und automatischer Beschleunigung getrennt. CPython-GIL-Aussagen auf Version/Build bezogen; join, Timeout, Ende und Erfolg unterschieden.

SHA-256: `2c60ec78504fb2ea81037bbf1ac0a2f4877cfea302bee49ed3c4eee910e6c046`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 260. Multithreading – it_0260

Ausgearbeitet und strukturell geprüft: 746 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6845 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/threading.html#barrier-objects
- https://docs.python.org/3.13/library/threading.html#event-objects
- https://docs.python.org/3.13/library/threading.html#gil-and-performance-considerations
- https://docs.python.org/3.13/library/threading.html#lock-objects

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Zwei eigene Python-Worker mit Barrier/Event/Lock, erwarteten Werten und kontrolliertem Ende; keine CPU-Parallelitäts-, Leistungs-, GUI- oder Netzwerkprüfung.

Präzisierung gegenüber der Quelle: Multithreading als nebenläufige und je nach Umgebung auch parallele Ausführung präzisiert. GIL versions-/buildbezogen; Event, Barrier, Lock, Reihenfolge, Beenden und Leistung getrennt.

SHA-256: `0704ec621de1966aec9fc1a84574854cada25bfbeefa121d3c67c3e4e9f70bce`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 260

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `f73d71ac19e08fed01c3da9e3473396167fa68b3`. Einträge 251–260 einzeln in Quellreihenfolge recherchiert, geschrieben und geprüft; Index und Fortschritt nach jedem Abschluss gespeichert. Tatsächlicher Stand: 260 von 302; 42 fehlen. Nächster Eintrag: `it_0261` – Process Fork. Freigabe bis 302 bleibt aktiv; gemeinsame Gesamtzusammenfassung noch offen.

Gesamtprüfung aller 260 Dokumente erfolgreich: Quelle mit erwartetem SHA-256 unverändert, 302 eindeutige IDs/Begriffe; vollständige Originalzuordnung, Metadaten, Kategorieableitung, unverändertes Indexschema, lückenlose records und documented_records; sortierte duplikatfreie Vereinigung der genauen Eintragsquellen; zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. Alle bisherigen 250 Texte und Indexdatensätze sowie PROMPT.md gegenüber dem Ausgangscommit unverändert; Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Neue semantische Linkbeschriftungen stimmen mit Originalbegriffen überein. 174 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich ausgeführt; Assertions, Exitcodes und exakte Ausgaben kontrolliert. Ausschließlich neue Texte 251–260 sowie Index und Fortschritt verändert; git diff --check erfolgreich.

Acht neue praktische Python-Beispiele: Fixture samt Cleanup, assert mit/ohne Optimierung, eigenes Regressionsmodell, Linting, Formatierung, begrenzte Zeilenaufzeichnung, Thread und Multithreading. Vorhandenes Ruff 0.17.5 und Black 26.10.1 ausschließlich an eigenen temporären Quelldateien geprüft; Black pro Aufruf mit einer Quelldatei und eigener Konfiguration, ohne Cache. Erwartete Unterprozess-Verstoßcodes ausdrücklich kontrolliert. Keine Tools installiert, Projektdateien formatiert oder bestehende Tests verändert. Coverage-Demonstration verwendet Standardbibliothek trace und erklärt ihren Umfang; keine App-Coverage gemessen. Eigene Threads beendet, Ressourcen aufgeräumt. Code Review und CI bleiben ausdrücklich nicht ausgeführte Gedankenmodelle; keine Reviewer-Kommentare, manuellen Workflows, Berechtigungsänderungen oder Veröffentlichungen ausgelöst. Alle neuen Texte review_pending; unabhängige inhaltliche Prüfung und lokale Reader-Abnahme weiterhin offen. Temporäre Kopf-/Markdown-Strukturprüfung ist keine Reader-Abnahme.

## 261. Process Fork – it_0261

Ausgearbeitet und strukturell geprüft: 764 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6618 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/os.html#os.fork
- https://man7.org/linux/man-pages/man2/fork.2.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes einzelnes Linux-Kind und eigene Pipe mit unterschiedlichen Variablenwerten geprüft; Deskriptoren geschlossen und waitpid-Status kontrolliert. Keine bestehende App oder Mehrthread-Fork-Integration getestet.

Präzisierung gegenüber der Quelle: Linux-fork mit eigenen Prozesskennungen, getrenntem gewöhnlichem Speicher und geerbten Ressourcen präzisiert; Copy-on-write, Threadgrenzen, Programmwechsel und Repository-Fork getrennt.

SHA-256: `f497fb875c71618ce978977410e1949a19566c92d21669577ac17939e99dab48`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 262. Async – it_0262

Ausgearbeitet und strukturell geprüft: 753 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6726 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/asyncio-sync.html#asyncio.Event
- https://docs.python.org/3.13/library/asyncio-task.html#asyncio.to_thread
- https://docs.python.org/3.13/library/asyncio-task.html#coroutines

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener asyncio-Lauf mit zwei wartenden Tasks, Freigabe und kontrollierten Ergebnissen; kein Netzwerk, GUI, Worker-Thread, Leistungs- oder bestehender Event-Loop-Eingriff.

Präzisierung gegenüber der Quelle: Async als kooperative Aufgabenplanung erklärt, nicht automatisch nichtblockierender Inhalt oder Thread pro Task. Coroutine-Aufruf, Planung, Event und Thread-Auslagerung getrennt.

SHA-256: `8a2e9f0cb98c90c7e172d95a826bda77758898c88b3015023c1693ddd24db75b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 263. Await – it_0263

Ausgearbeitet und strukturell geprüft: 733 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6545 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/asyncio-future.html#asyncio.Future.set_result
- https://docs.python.org/3.13/library/asyncio-task.html#awaitables
- https://docs.python.org/3.13/reference/expressions.html#await-expression

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes fertiges Future und separat geplanter asyncio-Task mit kontrollierter Reihenfolge geprüft; keine Eager-Factory, fremder Event Loop, GUI, Netzwerk oder feste Wartezeit.

Präzisierung gegenüber der Quelle: Awaitable-Typen, direkte Erwartung und Task-Planung getrennt; fertiges Future erzwingt unter den gezeigten Standardbedingungen keinen Taskwechsel. Keine automatische Thread-/Erfolgszusage.

SHA-256: `be2cd66d2dd1b038c25fa1fa793df31098f2796ea818b758b60864867988d282`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 264. Race Condition – it_0264

Ausgearbeitet und strukturell geprüft: 771 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6862 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://cwe.mitre.org/data/definitions/362.html
- https://docs.python.org/3.13/library/threading.html#lock-objects

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigener deterministisch verschachtelter Zähler mit Barrier und getrennten Locks sowie geschützter Gesamtaktualisierung geprüft; alle Threads beendet, keine bestehende Ressource oder allgemeine Race-Freiheit abgenommen.

Präzisierung gegenüber der Quelle: Race als ungeregelte Korrektheitsabhängigkeit der Reihenfolge statt nur gleichzeitiges Schreiben erklärt. Einzelne gesperrte Zugriffe von notwendiger gesamter Aktualisierung getrennt; GIL keine Pauschalgarantie.

SHA-256: `f6be22d3c12a985814be5d68e78c711b472d477d99e7f41b56a7f251c07cde40`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 265. Deadlock – it_0265

Ausgearbeitet und strukturell geprüft: 803 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6659 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://cwe.mitre.org/data/definitions/833.html
- https://docs.python.org/3.13/library/threading.html#lock-objects

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht ausgeführtes Zwei-Sperren-Modell; keine dauerhafte Blockade, angehaltenen Threads/Dienste, Fremdprozessdiagnose oder allgemeine Deadlock-Freiheitsabnahme.

Präzisierung gegenüber der Quelle: Deadlock als festgefahrene Warteabhängigkeit von langsamer Arbeit, Race und Starvation getrennt. Einheitliche Sperrreihenfolge und Timeout nur mit ihren konkreten Grenzen erklärt.

SHA-256: `5d983ac8946b5484d1bb809bd4e68c93e3e00414c0f33b467ceb9e64defe987d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 266. Mutex – it_0266

Ausgearbeitet und strukturell geprüft: 702 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6178 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/threading.html#lock-objects
- https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigenes Python-Lock ausschließlich nichtblockierend erworben und freigegeben; Zustände kontrolliert, keine POSIX-Besitzer-/Fairness-/Mehrprozess- oder allgemeine Korrektheitsprüfung.

Präzisierung gegenüber der Quelle: Mutex/Mutual Exclusion über konkreten Schutzumfang erklärt; POSIX-Besitzerregeln von Python-primitivem Lock getrennt. Nichtblockierender Versuch, Reentranz, Fairness und Geltungsbereich eingeordnet.

SHA-256: `3492574e0f9b8be5421bcfbb50966085f69dff864149000f464bc68ca0a33e8d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 267. Semaphore – it_0267

Ausgearbeitet und strukturell geprüft: 732 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6575 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/threading.html#semaphore-objects
- https://docs.python.org/3.13/library/threading.html#threading.BoundedSemaphore
- https://man7.org/linux/man-pages/man7/sem_overview.7.html

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene begrenzte Python-Semaphore nichtblockierend erworben/freigegeben; Kapazität und überzählige Freigabe geprüft, keine Downloads, Verbindungen, benannten OS-Objekte oder Fairness-/Mehrprozessprüfung.

Präzisierung gegenüber der Quelle: Semaphore als Kapazitätszähler mit korrekt gepaarter Lebensdauer erklärt; Python BoundedSemaphore von POSIX-Formen, Mutex, Event und Autorisierung getrennt.

SHA-256: `f956893e586bbf3cce48e180c42a7a1279263f3d73c5fe3a7f377b6b1aa6d70d`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 268. Blocking – it_0268

Ausgearbeitet und strukturell geprüft: 722 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6223 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/asyncio-dev.html#running-blocking-code
- https://docs.python.org/3.13/library/queue.html#queue.Queue.get

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Queue mit kurzem begrenztem Warten/Empty und verfügbarem Text geprüft; kein Ping, Netzwerk, GUI-, genaue Zeitmessung oder unbegrenzter Wartezustand.

Präzisierung gegenüber der Quelle: Blocking auf betroffenen Ausführungsort und Schnittstellenvertrag bezogen, nicht pauschal gesamter Rechner oder Fehler. Worker-Auslagerung, Event Loop und Timeout-Erfolg getrennt.

SHA-256: `cdd0ddfcdd0191abf5070f2e4c0ad3476ec32ddb2c95b51fc7595bcda9c5d9cc`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 269. Nonblocking – it_0269

Ausgearbeitet und strukturell geprüft: 739 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6474 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/queue.html#queue.Queue.get_nowait
- https://docs.python.org/3.13/library/socket.html#socket.socket.setblocking

Praktische Prüfung: ein vollständiges ausführbares Beispiel, Exitcode 0; Ausgabe exakt wie dokumentiert. Eigene Queue mit Empty ohne Warten, anderer Datenverarbeitung und späterem Eintrag geprüft; kein Socket, Netzwerkmodus, Worker, GUI-, Zeit- oder Echtzeittest.

Präzisierung gegenüber der Quelle: Nonblocking als konkreten Bereitschaftsvertrag von Timeout, Async und Worker-Auslagerung getrennt. Fehlende Bereitschaft keine Erfolgsgarantie; Gesamtreaktionsfähigkeit nicht aus einzelner API abgeleitet.

SHA-256: `abe8898732b4b69b6fa88ed083109a83f54422ce475f058adfd6fc6dcbb181f9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 270. Paketierung – it_0270

Ausgearbeitet und strukturell geprüft: 749 durch Leerraum getrennte Wörter einschließlich Beispiel/Links; 6785 UTF-8-Bytes; 31 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://raw.githubusercontent.com/pypa/packaging.python.org/main/source/tutorials/packaging-projects.rst
- https://www.debian.org/doc/debian-policy/ch-binary.html

Gedankenbeispiel: keine praktische Ausführung vorgesehen oder behauptet. Nicht gebautes Notizanwendungsmodell; keine Artefakte, Builds, Paket-/Abhängigkeitsänderungen, Installationen, Skripte oder Uploads ausgeführt.

Präzisierung gegenüber der Quelle: Paketierung als zielbezogene Dateiauswahl/Metadaten erklärt; Debian-Binärpaket von Python-Distribution, Build, Installation und Veröffentlichung getrennt. Keine tatsächliche NetMon-Paketbehauptung.

SHA-256: `d7e590f8ceaa71e96ca0ab920ef3d06bc3f2627f602c81953a6710d2df812295`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Sicherungspunkt nach Eintrag 270

Branch `codex/linux-glossar-011-302`; Ausgangscommit dieses Abschnitts `9e1a898e216d6d4c27505409ee8824356ced8068`. Einträge 261–270 einzeln in Quellreihenfolge recherchiert, geschrieben, geprüft und jeweils in Index und Fortschritt gespeichert. Tatsächlicher Stand: 270 von 302; 32 fehlen. Nächster Eintrag: `it_0271` – Installer. Fortsetzungsfreigabe bis 302 bleibt aktiv; gemeinsame Gesamtzusammenfassung noch offen.

Gesamtprüfung aller 270 Dokumente erfolgreich: unveränderte Quelle mit erwartetem SHA-256 und 302 eindeutigen IDs/Begriffen; vollständige Originalzuordnung, Metadaten, Kategorieableitung, unverändertes Indexschema, lückenlose records und documented_records; sortierte duplikatfreie Vereinigung der genauen Eintragsquellen; zehn Hauptabschnitte, Codeblöcke, Größen-/Parserlimits, interne Verweise und tatsächliche Dokumentprüfsummen. Alle bisherigen 260 Texte und Indexdatensätze sowie PROMPT.md gegenüber dem Ausgangscommit unverändert; Pilottexte und Pilotindex zusätzlich gegen den Pilotcommit geprüft. Neue Linkbeschriftungen mit Katalogbegriffen verglichen. 182 vollständige Python-Beispiele und ein JavaScript-Beispiel erneut erfolgreich ausgeführt, Assertions, Exitcodes und vollständige Ausgaben kontrolliert. Exakter Änderungsumfang nur neue Texte 261–270 sowie Index und Fortschritt; git diff --check erfolgreich.

Acht neue praktische Python-Prüfungen: eigener Fork samt Pipe/waitpid, zwei asyncio-Tasks, fertiges Future/Await-Reihenfolge, deterministischer verlorener Zählerstand mit Gegenprüfung, nichtblockierendes Lock, begrenzte Semaphore, kurz begrenzte Queue-Wartefrist und unmittelbarer Queue-Abruf. Eigene Kindprozesse, Tasks und Threads kontrolliert beendet; eigene Ressourcen aufgeräumt. Deadlock und Paketierung ausdrücklich nicht ausgeführte Gedankenmodelle. Keine permanente Blockade, echte Netzwerkverbindung, Paket-/Build-/Installationsänderung, privilegierte Aktion oder fremde Ressourcenverwaltung. Neue Texte review_pending. Unabhängige inhaltliche Prüfung sowie lokale Reader-Abnahme bleiben offen; die temporäre Kopf-/Markdown-Strukturprüfung ist keine Reader-Abnahme.

## 271. Installer – it_0271

Ausgearbeitet und strukturell geprüft: 569 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4617 UTF-8-Bytes, 25 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://manpages.debian.org/stable/dpkg/dpkg.1.en.html
- https://manpages.debian.org/stable/apt/apt.8.en.html

Gedankenbeispiel: Installationsablauf eines fiktiven Debian-Pakets beschrieben. Keine Paketdatei ausgeführt und keine Systemänderung vorgenommen.

Präzisierung gegenüber der Quelle: Ein .deb als Installationsartefakt eingeordnet. Die Rolle des Installationswerkzeugs, Abhängigkeitsauflösung und getrennte Zustände beim Entpacken und Konfigurieren erläutert.

SHA-256: `8e81a9eb8f902daf1b10a2b1e169c4b5c1c563618ce0337adfd015651b256be2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 272. Abhängigkeiten – it_0272

Ausgearbeitet und strukturell geprüft: 527 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4445 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/doc/debian-policy/ch-relationships.html
- https://packaging.python.org/en/latest/specifications/pyproject-toml/

Gedankenbeispiel: Voraussetzungen für Kern- und Zusatzfunktion zugeordnet. Keine Programme oder Pakete installiert.

Präzisierung gegenüber der Quelle: Erforderliche, empfohlene und optionale Komponenten unterschieden. Wireshark als hypothetisches Beispiel behandelt, ohne eine tatsächliche NetMon-Abhängigkeit zu behaupten.

SHA-256: `1fe37d100ef06557e2413eec77ae8ca33fde030a1ecf795f09ec6dca5586ac42`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 273. Manifest – it_0273

Ausgearbeitet und strukturell geprüft: 503 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4122 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://packaging.python.org/en/latest/specifications/pyproject-toml/
- https://www.debian.org/doc/debian-policy/ch-controlfields.html

Gedankenbeispiel: Paketbeschreibung einer fiktiven Notizanwendung verglichen. Keine Manifestdatei geschrieben oder verarbeitet.

Präzisierung gegenüber der Quelle: Manifest als formatabhängige Beschreibung eingeordnet. pyproject.toml und Debian-Kontrolldaten als konkrete Beispiele mit jeweils eigenem Schema erklärt.

SHA-256: `61fd6a1d8d33e55985a1636f04f4c687bd847390403c0c881277fb25d8a4da17`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 274. pyproject.toml – it_0274

Ausgearbeitet und strukturell geprüft: 506 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4239 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://packaging.python.org/en/latest/specifications/pyproject-toml/
- https://docs.python.org/3.13/library/tomllib.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. TOML mit der Python-Standardbibliothek eingelesen und beide Tabellen geprüft. Kein Build-Backend importiert und kein Paket installiert.

Präzisierung gegenüber der Quelle: Build-Voraussetzungen, Projektmetadaten und werkzeugspezifische Einstellungen getrennt. Versionsangabe kann abhängig vom Build-Backend statisch oder dynamisch sein.

SHA-256: `fe2bc7b1642c59cf56d91f7d2fbce762242425ad6a5f5bd0e1f203e1295107e7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 275. Wheel – it_0275

Ausgearbeitet und strukturell geprüft: 479 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4164 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://packaging.python.org/en/latest/specifications/binary-distribution-format/
- https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Die drei Kompatibilitäts-Tags eines selbst gewählten Dateinamens zerlegt. Keine Wheel-Datei erstellt, geprüft oder installiert.

Präzisierung gegenüber der Quelle: Binäres Distributionsformat von nativem Maschinencode unterschieden. Kompatibilitäts-Tags und Abhängigkeiten erläutert.

SHA-256: `db598047a6268690ad21d0e73e3941c07abef339cc7ef72ea1e8d69b6a99ed99`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 276. AppImage – it_0276

Ausgearbeitet und strukturell geprüft: 514 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4166 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.appimage.org/introduction/concepts.html
- https://docs.appimage.org/user-guide/troubleshooting/fuse.html

Gedankenbeispiel: Startversuch einer hypothetischen AppImage-Datei beschrieben. Keine Datei heruntergeladen oder ausgeführt.

Präzisierung gegenüber der Quelle: Portabilität an Architektur und Systemvoraussetzungen gebunden. Direkter Start, Desktop-Integration und Isolation als getrennte Eigenschaften erklärt.

SHA-256: `1990de4aa8e821f5deaf9d86e5cacce9c07333fe027627f9b585fbe8b0881925`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 277. Flatpak – it_0277

Ausgearbeitet und strukturell geprüft: 510 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4136 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.flatpak.org/en/latest/basic-concepts.html
- https://docs.flatpak.org/en/latest/sandbox-permissions.html

Gedankenbeispiel: Dateizugriff eines fiktiven Bildprogramms über einen systemvermittelten Dialog. Keine App oder Runtime installiert.

Präzisierung gegenüber der Quelle: Flatpak als Verteilungssystem mit getrennten Apps und Runtimes beschrieben. Sandbox, deklarierte Freigaben und Portale konkret eingeordnet.

SHA-256: `7e08b5dfe0436f9e207f4e1f9cbd213992656b0320e3d01903c67dcc7ec227be`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 278. Snap – it_0278

Ausgearbeitet und strukturell geprüft: 501 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4222 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://snapcraft.io/docs/explanation/security/snap-confinement/index.html
- https://snapcraft.io/docs/reference/interfaces/

Gedankenbeispiel: Zugriffsprofil eines erfundenen Bildprogramms betrachtet. Kein Snap installiert und keine Schnittstelle verbunden.

Präzisierung gegenüber der Quelle: Paketformat, Snap-Dienst und abgestufte Isolation unterschieden. Distributionseignung an Unterstützung und konkreten Snap gebunden.

SHA-256: `38d6c6505ff03bd33f824f3db82bd2609a169f44e0ce5f7992a9a0afe20abc59`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 279. Postinst – it_0279

Ausgearbeitet und strukturell geprüft: 495 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4161 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html
- https://manpages.debian.org/stable/dpkg/dpkg.1.en.html

Gedankenbeispiel: wiederholbare Konfiguration eines erfundenen Debian-Pakets durchgespielt. Kein Paketbetreuerskript geschrieben oder ausgeführt.

Präzisierung gegenüber der Quelle: Postinst auf die Konfigurationsphase und weitere dokumentierte Aufrufpfade bezogen. Fehler und Wiederholung von der eigentlichen Dateiauslieferung getrennt.

SHA-256: `d947dbbc33d7633632b6387e8ecc5927bbb84b99dc53a94454e7535c47c3efa1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 280. Preinst – it_0280

Ausgearbeitet und strukturell geprüft: 489 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3988 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html
- https://manpages.debian.org/stable/dpkg/dpkg.1.en.html

Gedankenbeispiel: Prüfung eines eigenen Paketpfads vor dem Entpacken modelliert. Keine Dateien oder Systemkonfiguration geändert.

Präzisierung gegenüber der Quelle: Zeitpunkt vor dem Entpacken der neuen Paketdateien präzisiert. Installations- und Upgrade-Argumente sowie begrenzte verfügbare Abhängigkeiten berücksichtigt.

SHA-256: `23141d9cfa09dc55ae413baed198f180dc8676066a9de98e27d2e05d7c2e4de9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 281. Postrm – it_0281

Ausgearbeitet und strukturell geprüft: 489 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4025 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html
- https://manpages.debian.org/stable/dpkg/dpkg.1.en.html

Gedankenbeispiel: Paketdaten und persönliche Nutzerdaten beim Entfernen abgegrenzt. Keine Löschung und kein Skriptlauf.

Präzisierung gegenüber der Quelle: Postrm auf mehrere mögliche Aufrufe bezogen. Remove, Purge und Upgrade als verschiedene Fälle mit unterschiedlichen Aufräumgrenzen erläutert.

SHA-256: `2d9be3cafd2f2857fe9fd2ee9035289025641e8ff773aae0d4f05fbbe725fef9`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 282. Dokumentation – it_0282

Ausgearbeitet und strukturell geprüft: 484 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4069 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://diataxis.fr/
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes

Gedankenbeispiel: Informationen für eine fiktive Notizanwendung auf mehrere Dokumenttypen verteilt.

Präzisierung gegenüber der Quelle: Dokumentation nach Bedarf und Zielgruppe eingeordnet. README als Einstieg, Verfahrensanleitung und Referenz als unterschiedliche Hilfen beschrieben.

SHA-256: `5b617f1c0887b7f2a47bcfa49d18e128f976e5f2d8ebb5308aee56b623a770b6`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 283. README – it_0283

Ausgearbeitet und strukturell geprüft: 484 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3997 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- https://docs.gitlab.com/user/project/repository/files/

Gedankenbeispiel: Einstiegsinformationen und weiterführende Links für ein Modellprojekt entworfen.

Präzisierung gegenüber der Quelle: README als sichtbaren Einstieg eingeordnet. Automatische Anzeige vom Host und Ablageort abhängig gemacht.

SHA-256: `cd40ee65fd0e55bb8c3daa250fd64fbbe90511663a285d93c2a6a723361f83a5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 284. Markdown – it_0284

Ausgearbeitet und strukturell geprüft: 465 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3660 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://spec.commonmark.org/0.31.2/
- https://github.github.com/gfm/

Gedankenbeispiel: Quelltext und erwartete Darstellung beschrieben. Kein Renderer für dieses Beispiel ausgeführt.

Präzisierung gegenüber der Quelle: Markdown-Syntax, CommonMark und plattformspezifische Erweiterungen getrennt. Überschrift mit Leerzeichen nach dem Markierungszeichen gezeigt.

SHA-256: `e712a6a773d1a51632b6beac7ac11093014af809dd6f290a2f9f1d256698f2f2`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 285. Docstring Python – it_0285

Ausgearbeitet und strukturell geprüft: 445 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3570 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://peps.python.org/pep-0257/
- https://docs.python.org/3.13/library/inspect.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Rückgabewert und den von inspect.getdoc ausgelesenen Text geprüft.

Präzisierung gegenüber der Quelle: Position des Docstrings und Zugriff zur Laufzeit erläutert. Von Kommentaren, Typannotationen und automatischer Prüfung abgegrenzt.

SHA-256: `591f6a89d4147616262e572a76ce46716deabcb4fee53a789c3759824434549f`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 286. Glossar – it_0286

Ausgearbeitet und strukturell geprüft: 476 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3917 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.w3.org/TR/skos-reference/
- https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-glossary

Gedankenbeispiel: Begriff, Synonym und Querverweis für einen fiktiven Glossareintrag zugeordnet.

Präzisierung gegenüber der Quelle: Glossar als Begriffsnachschlagewerk mit Beziehungen und Vorzugsbenennungen erläutert.

SHA-256: `440a1e150cb1f32844b1fb4d41a54e442db2e0b5c4f14d5c684e05dbbe2c835c`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 287. FAQ – it_0287

Ausgearbeitet und strukturell geprüft: 455 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3654 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/faq/general.html
- https://design-system.service.gov.uk/components/accordion/

Gedankenbeispiel: Wiederkehrende Fragen für eine fiktive Notizanwendung strukturiert.

Präzisierung gegenüber der Quelle: FAQ anhand echter wiederkehrender Fragen eingeordnet. Längere Verfahren und Grundlagen in passende Dokumente verwiesen.

SHA-256: `e352792e59f29801d91839e578cd0eab1d0a73b16f19e8092d2a32cb19510e46`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 288. How-to – it_0288

Ausgearbeitet und strukturell geprüft: 482 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3811 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://diataxis.fr/how-to-guides/
- https://www.debian.org/doc/debian-policy/ch-binary.html

Gedankenbeispiel: Aufbau einer Anleitung für ein hypothetisches Debian-Paket. Kein Paket gebaut oder installiert.

Präzisierung gegenüber der Quelle: How-to auf ein konkretes Ergebnis samt Voraussetzungen und Abschlusskriterium bezogen. Paketierung als Gegenstand eines hypothetischen How-tos eingeordnet.

SHA-256: `1cd21556026b47798e898927d10cf007bef1aeecd4701a40dc1cbfa6375c43f7`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 289. Tutorial – it_0289

Ausgearbeitet und strukturell geprüft: 469 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3643 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://diataxis.fr/tutorials/
- https://tkdocs.com/tutorial/firstexample.html

Gedankenbeispiel: Ablauf einer ersten GUI-Lektion skizziert. Keine GUI gestartet.

Präzisierung gegenüber der Quelle: Tutorial auf Lernerfolg und überprüfbare Zwischenschritte bezogen. Das Tk-Beispiel konzeptionell eingeordnet.

SHA-256: `2a5aa7f6abe69f39dfda5c866dab3e8035d07725ca7237f964ad31a154624eff`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 290. Manpage – it_0290

Ausgearbeitet und strukturell geprüft: 465 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3771 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://man7.org/linux/man-pages/man1/man.1.html
- https://www.freedesktop.org/software/systemd/man/latest/systemctl.html

Gedankenbeispiel: örtliche und aktuelle Online-Referenz verglichen. Kein systemctl-Befehl aufgerufen und kein Dienst verändert.

Präzisierung gegenüber der Quelle: Manpage als lokale Referenz mit nummerierten Abschnitten eingeordnet. Das Lesen der systemctl-Hilfe vom Ausführen des Verwaltungsbefehls getrennt.

SHA-256: `4930d246d0dd04c2b1dfed419df24a392ece289bfdec09aae39fa3893d90ab37`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 291. Compiler – it_0291

Ausgearbeitet und strukturell geprüft: 467 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3833 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html
- https://clang.llvm.org/docs/CommandGuide/clang.html

Gedankenbeispiel: C-Übersetzung bis zur Objektdatei und danach zum Programm beschrieben. Kein Compiler aufgerufen.

Präzisierung gegenüber der Quelle: Compiler auf Übersetzung in Zielcode bezogen. Einzelne Stufen des C-Werkzeugaufrufs von der Übersetzung im engeren Sinn getrennt.

SHA-256: `6aa428410b63c18731c175100aeca70ca3fa413a9e71103b7061f95e2e3c71a5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 292. Interpreter – it_0292

Ausgearbeitet und strukturell geprüft: 454 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3627 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/glossary.html
- https://docs.python.org/3.13/library/dis.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Codeobjekt mit compile erzeugt und in leerem eigenen Namensraum ausgeführt. Errechneten Wert geprüft.

Präzisierung gegenüber der Quelle: „Direkt“ für CPython präzisiert. Übersetzung in Bytecode und Ausführung durch die Laufzeit unterschieden.

SHA-256: `301295018cb1e6c23173c7dd798993afebf48e98e1948922b1e736e7b180143b`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 293. Transpiler – it_0293

Ausgearbeitet und strukturell geprüft: 454 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3884 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.typescriptlang.org/docs/handbook/typescript-from-scratch.html
- https://www.typescriptlang.org/tsconfig/target.html

Gedankenbeispiel: TypeScript-Quelltext und erwartete JavaScript-Form modelliert. Kein Compilerlauf.

Präzisierung gegenüber der Quelle: Transpiler als Compiler mit Quelltext als Zielausgabe eingeordnet. TypeScript-Typen und JavaScript-Laufzeitkompatibilität getrennt.

SHA-256: `b3098d952ac78ec7af321b618a01130c1eb90e51dd8ffbf9bd2e30e14e57f5c8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 294. IDE – it_0294

Ausgearbeitet und strukturell geprüft: 467 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3955 UTF-8-Bytes, 27 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://www.jetbrains.com/help/pycharm/quick-start-guide.html
- https://code.visualstudio.com/docs/python/python-tutorial

Gedankenbeispiel: Projektumgebung auswählen, Test starten und Fehler untersuchen. Keine IDE gestartet.

Präzisierung gegenüber der Quelle: IDE als gebündelte Entwicklungsumgebung beschrieben. VS Code als erweiterbaren Editor mit IDE-ähnlichem Funktionsumfang eingeordnet.

SHA-256: `e8bbf4a7ca1ba2d19948666d12e49c2cd85e047e4d301d476f19ac51256432dd`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 295. Editor – it_0295

Ausgearbeitet und strukturell geprüft: 452 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3599 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://code.visualstudio.com/docs/editor/codebasics
- https://www.nano-editor.org/dist/latest/nano.html

Gedankenbeispiel: Markdown-Datei im Terminal oder Desktop bearbeiten und den Diff prüfen. Keine Editoraktion ausgeführt.

Präzisierung gegenüber der Quelle: Editor nach der Textbearbeitung eingeordnet. Sprachfunktionen, Dateikodierung und IDE-ähnliche Erweiterungen unterschieden.

SHA-256: `4911511d51099ff971ae9cd779c661d664ab563cb496ec014bd3b46af17c05f5`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 296. Debugger – it_0296

Ausgearbeitet und strukturell geprüft: 465 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3776 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pdb.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Breakpoints.html

Gedankenbeispiel: fehlerhaften Teilschritt in einer erfundenen Mengenberechnung untersucht. Kein interaktiver Debugger gestartet.

Präzisierung gegenüber der Quelle: Debugger auf Laufzeitzustand, schrittweise Analyse und Grenzen bei Timingfehlern bezogen.

SHA-256: `9d6799e03213e8601fbd4ce9bf08b1e2fa74650426680546eec50c464a4cfcf1`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 297. Breakpoint – it_0297

Ausgearbeitet und strukturell geprüft: 469 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3799 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/pdb.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Breakpoints.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Eigenen Breakpoint-Hook aufgerufen und anschließend wiederhergestellt. Kein interaktiver Debugger und keine Prozessanbindung.

Präzisierung gegenüber der Quelle: Haltepunkte an Orten und mit Bedingungen erläutert. Von Einzelschritt und Watchpoint abgegrenzt. Python-eigenen Hook ohne interaktives Anhalten getestet.

SHA-256: `7917554e1dc67f7019326f309337a02e9dbc0443f87ecfd63673679e4a8eebb8`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 298. Profiling – it_0298

Ausgearbeitet und strukturell geprüft: 467 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3862 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/profile.html
- https://docs.python.org/3.13/library/tracemalloc.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Mit cProfile das eigene Beispiel gemessen und in pstats drei Aufrufe der Zielfunktion geprüft. Keine Zeitwerte zugesichert.

Präzisierung gegenüber der Quelle: CPU- und Speicherprofile unterschieden. Profilwerte und Messinstrument bewusst auf eigene Testarbeit begrenzt.

SHA-256: `bc2c4f7831ad1144ee63070b5e4f4516a74846404990f3d2146b59c7c460372e`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 299. Benchmark – it_0299

Ausgearbeitet und strukturell geprüft: 476 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 3890 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/timeit.html
- https://pyperf.readthedocs.io/en/latest/run_benchmark.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Ergebnisse zweier Rechenvarianten und jeweils drei Messwerte geprüft. Keine Laufzeit oder Rangfolge zugesichert.

Präzisierung gegenüber der Quelle: Vergleichsmessung an gleiche Arbeit und dokumentierte Bedingungen gebunden. Warm-up, Wiederholungen und Streuung erläutert.

SHA-256: `62b2fb255f2f7eca4429e81e15642215a24c32d43579de6524009be79f395235`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 300. Performance – it_0300

Ausgearbeitet und strukturell geprüft: 485 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4090 UTF-8-Bytes, 26 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/asyncio-dev.html
- https://docs.python.org/3.13/library/tkinter.html

Gedankenbeispiel: lange Prüfung in einer GUI mit Reaktion, Fortschritt und Rückgabe modelliert. Keine GUI und kein Netzwerkzugriff.

Präzisierung gegenüber der Quelle: Leistung über konkrete Kenngrößen eingeordnet. GUI-Reaktionszeit von Gesamtdauer und Durchsatz getrennt.

SHA-256: `7393e82e7c69a8e47e3df11f79b9f35d1e97b968492045b8200ccd18a971eb19`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 301. Memory Leak – it_0301

Ausgearbeitet und strukturell geprüft: 513 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4093 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/tracemalloc.html
- https://man7.org/linux/man-pages/man5/proc_pid_status.5.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Mit schwachen Referenzen drei unbeabsichtigt gehaltene Objekte und ihre Freigabe durch Leeren der Liste in CPython geprüft. Kein RSS-Grenzwert behauptet.

Präzisierung gegenüber der Quelle: Speicherleck anhand unbeabsichtigt dauerhaft belegter Ressourcen erläutert. Wachsenden Prozessspeicher als Hinweis eingeordnet. Behaltene Python-Referenzen praktisch modelliert.

SHA-256: `5ba4b399c07b3116d212b9ac94752ed2152644b8ab401d491015eca99c45e636`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## 302. Garbage Collection – it_0302

Ausgearbeitet und strukturell geprüft: 497 durch Leerraum getrennte Wörter einschließlich Beispiel/Links, 4084 UTF-8-Bytes, 24 Darstellungsblöcke.

Geprüfte Primärquellen:

- https://docs.python.org/3.13/library/gc.html
- https://docs.python.org/3.13/reference/datamodel.html

Praktische Prüfung: eigenständiges Python-Beispiel im temporären Verzeichnis, Exitcode 0 und erwartete Ausgabe. Eigenen unerreichbaren Zyklus mit schwachen Referenzen und einem expliziten Sammellauf geprüft. Vorherigen Automatikzustand wiederhergestellt.

Präzisierung gegenüber der Quelle: Automatische Speicherbereinigung auf nicht mehr erreichbare Objekte bezogen. CPython-Referenzzählung und ergänzenden Zyklensammler erläutert. Ressourcenlebensdauer getrennt.

SHA-256: `1f311b0d1db6e498b138013e6f0992851f1f8c2bfbc218021ad7c0bab9e2b605`.

Offen: unabhängige inhaltliche Prüfung sowie Reader-Zuordnung, Darstellung, Suche, Code-Kopieren und getrennter Lesestatus.

## Abschluss nach Eintrag 302 – 21.11.2026

Auf dem Branch `codex/linux-glossar-011-302` sind **302 von 302 Einträgen ausgearbeitet und strukturell geprüft**. Dieser Abschnitt beginnt beim Commit `04b1d1e14e793a7ab042712d0a58dc3fa173230d` und ergänzt die Einträge 271 „Installer“ bis 302 „Garbage Collection“. Alle 302 Indexdatensätze stehen auf `review_pending`.

Der Gesamtcheck hat die unveränderte Originalquelle mit SHA-256 `b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24` und 302 eindeutige IDs und Begriffe bestätigt. Geprüft wurden Quellreihenfolge, vollständige Originaldatensätze, Kategorieableitung, JSON-kompatible Köpfe, genau zehn Hauptabschnitte pro Dokument, Codeblöcke, Parsergrenzen, interne Linkziele, Dokumentprüfsummen und die sortierte Quellenvereinigung. Die Dokumente und Indexdatensätze 1–270 sowie `PROMPT.md` sind byteweise beziehungsweise als unveränderte JSON-Datensätze mit dem Ausgangscommit abgeglichen. Der bisherige Teil dieses Fortschrittsprotokolls ist erhalten.

Für die 32 neuen Texte wurden die angegebenen Primärquellen per HTTPS abgerufen und die zentralen Aussagen mit den jeweiligen Referenzen abgeglichen. Neun neue Python-Beispiele liefen mit Python 3.12.14 in temporären Verzeichnissen mit Exitcode 0 und erwarteter Standardausgabe. Die übrigen 23 Beispiele sind im jeweiligen Eintrag als nicht ausgeführte Gedankenbeispiele gekennzeichnet. Die früheren praktischen Beispiele wurden in diesem Durchlauf nicht erneut ausgeführt.

Die unabhängige fachliche Zweitprüfung und die lokale NetMon-Reader-Abnahme stehen aus. Dazu zählen die Zuordnung, Darstellung, Suche, Code-Kopierfunktion und der getrennte Lesestatus. Die Strukturprüfung verwendete den vorhandenen Markdown-Parser mit einem nur im Speicher ergänzten kompatiblen Kopf. Der separate pytest-Lauf zum Befehlsreader konnte in dieser Umgebung mangels installiertem pytest nicht starten.
