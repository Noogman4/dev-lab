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
