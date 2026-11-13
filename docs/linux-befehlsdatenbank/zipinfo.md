---
id: "zipinfo"
name: "zipinfo"
command: "zipinfo"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive & kompression", "zipinfo"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 26
reviewed_at: "2026-11-13"
locally_checked_version: "ZipInfo 3.00 aus Info-ZIP UnZip 6.00"
---

# zipinfo – ZIP-Mitglieder und technische Archivangaben lesen

## 1. Kurzbeschreibung

`zipinfo` zeigt Namen und technische Angaben der Mitglieder eines ZIP-Archivs. Es entpackt die Nutzdaten nicht als normale Dateien. Unter Info-ZIP gehört diese Ansicht zur UnZip-Werkzeugfamilie.

**Für eigene lesbare Archive sind keine Root-Rechte nötig.** Die normalen Listenaufrufe verändern das Archiv nicht. Ausgaben können vertrauliche Namen oder Kommentare enthalten.

## 2. Was macht der Befehl?

Die Archivstruktur enthält Angaben wie Mitgliedsnamen, Größen, Kompressionsmethoden, Zeitstempel und gespeicherte Attribute. ZipInfo stellt diese je nach Option unterschiedlich ausführlich dar. Das Standardformat ähnelt einer Unix-Dateiliste, beschreibt aber archivierte Angaben und nicht die aktuellen Rechte einer bereits entpackten Datei.

Eine Metadatenliste ist kein vollständiger Dekompressions- und CRC-Test. Ebenso sind die gespeicherten Namen keine Bestätigung, dass ein Archiv beim Entpacken ausschließlich unproblematische Dateien erzeugen wird.

Grundlagen: [Distributions-Manpage zu zipinfo](https://manpages.debian.org/trixie/unzip/zipinfo.1.en.html) und die lokal geprüfte Hilfe von ZipInfo 3.00. Der alternative Aufruf `unzip -Z` schaltet zuerst in denselben Informationsmodus.

## 3. Syntax

```text
zipinfo [OPTIONEN] ARCHIV.zip [MITGLIED ...] [-x MUSTER ...]
unzip -Z [ZIPINFO_OPTIONEN] ARCHIV.zip
```

```bash
zipinfo -1 "sammlung.zip"
zipinfo -v "sammlung.zip"
```

Die Optionen gehören zum ZipInfo-Modus. Gleich aussehende UnZip-Schalter können dort etwas anderes bedeuten. `unzip -Z` muss den Modus vor den folgenden Informationsoptionen wählen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-1` | Nur Mitgliedsnamen, einer je Zeile. | Keine sichere Nulltrennung für beliebige Dateinamen. |
| `-2` | Namensliste mit optionalen Zusatzzeilen. | Nicht mit garantiert reiner `-1`-Ausgabe verwechseln. |
| `-s` | Kurzes Unix-artiges Format. | Übliche Standardansicht. |
| `-m` | Mittlere Detailansicht mit Kompressionsverhältnis. | Prozentangaben richtig zur gewählten Ansicht zuordnen. |
| `-l` | Längere Ansicht mit komprimierten Größen. | Anders als UnZip-Optionen beurteilen. |
| `-v` | Sehr ausführliche technische Darstellung. | Kann lange Ausgaben erzeugen. |
| `-h` | Kopfzeile anzeigen. | Hier nicht einfach der allgemeine Hilfeschalter. |
| `-t` | Summen anzeigen. | **Kein Inhaltstest**, anders als `unzip -t`. |
| `-T` | Zeitstempel in sortierbarer Zahlenform. | Kein Herkunfts- oder Manipulationsnachweis. |
| `-z` | Archivkommentar einschließen. | Kommentare können vertrauliche Angaben enthalten. |
| `-x MUSTER` | Mitglieder von der Liste ausschließen. | Ändert weder Archiv noch gespeicherte Mitglieder. |

Die Hilfe erscheint beim lokalen Aufruf ohne Archiv; sie ist auch über die allgemeinen UnZip-Hilfewege zugänglich. Zeichenkodierungsoptionen können Distributions- beziehungsweise Build-Erweiterungen sein.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Eingabe vorbereiten

```bash
uebung="$(mktemp -d -t netmon-zipinfo-XXXXXX)"
cd "$uebung"
pwd
mkdir "Material"
printf '%s\n' 'Eigene ZIPINFO-Testnotiz.' > "Material/notiz.txt"
zip -r "sammlung.zip" "Material"
```

Nur nach erfolgreichem Verzeichniswechsel fortfahren. Diese Vorbereitung schreibt ausschließlich neue Übungsdaten.

### Schritt 2: Mitgliedsnamen lesen

```bash
zipinfo -1 "sammlung.zip"
```

Erwartet werden die aufgenommene Struktur und `Material/notiz.txt`. Verzeichnis-Einträge können als eigene Namen mit abschließendem Schrägstrich erscheinen.

### Schritt 3: Technische Angaben ansehen

```bash
zipinfo -l "sammlung.zip"
zipinfo -v "sammlung.zip"
```

Die ausführliche Variante zeigt mehr Strukturinformationen. Größen unterscheiden: Die Summe komprimierter Mitgliedsdaten muss wegen zusätzlicher Header nicht der gesamten Archivdateigröße entsprechen.

### Schritt 4: Summen und Test auseinanderhalten

```bash
zipinfo -t "sammlung.zip"
unzip -t "sammlung.zip"
```

Die erste Zeile liefert Summen. Erst die zweite führt den hier gemeinten UnZip-Datentest aus. Gleicher Optionsbuchstabe bedeutet bei diesen Modi nicht gleiche Aufgabe.

## 6. Typische Anwendungsfälle

**Vor dem Entpacken orientieren:** Namen, Ordnerstruktur und angekündigte Größen prüfen, bevor normale Ausgabedateien angelegt werden.

**Kompatibilität untersuchen:** Die angezeigte Kompressionsmethode und archivierten Herkunftsangaben helfen bei der Suche nach einem passenden Entpacker. Sie garantieren nicht dessen tatsächliche Unterstützung.

**Veröffentlichungsinhalt kontrollieren:** Vor dem Teilen nach alten Dateien, privaten Namen, unerwarteten Pfaden und Kommentaren sehen.

**Archivänderungen nachvollziehen:** Namenslisten verschiedener Stände vergleichen. Für einen wirklichen Inhaltsvergleich zusätzlich geeignete Datenprüfungen einsetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Metadaten nicht als Vertrauensbeweis behandeln

Zeitstempel, Erzeugersystem und Namen sind Angaben aus dem Archiv. Sie authentifizieren keinen Absender. Auch eine plausible Liste kann zu einem beschädigten oder unerwünschten Inhalt gehören.

### Listen nicht blind als Befehle verwenden

Mitgliedsnamen können Leerzeichen, Sonderzeichen und ungewöhnliche Zeichen enthalten. Zeilenweise Ausgabe allein bietet keine robuste Grundlage für unzitierte Shell-Schleifen oder automatische Löschaktionen. Namen nicht als ausführbaren Text behandeln.

### Vertrauliche Angaben und Berichtsdateien

Ein Dateiname kann bereits den Inhalt persönlicher Unterlagen verraten. Vor dem Weitergeben einer technischen Liste Namen und Kommentare prüfen. Umleitungen schreiben Dateien und können bestehende Berichte überschreiben.

### Keine durchgesetzte Größenbegrenzung

Angekündigte Größen helfen zur Orientierung. Sie begrenzen den späteren Entpacker nicht und ersetzen keine Ressourcenplanung. Die Liste führt selbst keinen vollständigen Wiederherstellungstest durch.

**Root-Rechte sind für die Leseaufgabe nicht nötig.** Für eigene Archive die normale Benutzerkennung verwenden.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `-t` prüft keine Daten | Summenmodus mit UnZip-Test verwechselt. | Für Datentest `unzip -t` verwenden. |
| `-h` zeigt nur Kopf | ZipInfo-Option anders als allgemeine Hilfe. | Lokale Hilfedokumentation lesen. |
| Mitglied fehlt | Auswahlmuster oder Groß-/Kleinschreibung. | Zunächst vollständige Namensliste ansehen. |
| Zeichen falsch | Abweichende Namenskodierung. | Build und tatsächlich verwendete Kodierung prüfen. |
| Listenaufruf scheitert | Beschädigtes Archiv oder keine ZIP-Datei. | Herkunft und genaue Fehlermeldung klären. |

Meldungen und Abschlussstatus beachten. Auch eine teilweise erzeugte technische Liste kann von einem späteren Fehler begleitet sein.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit `-1` die Struktur und mit `-l` grundlegende Details ansehen.
2. `-v` für gezielte technische Fragen verwenden.
3. Summenmodus und Datenprüfung klar trennen.
4. Mitgliedsnamen nicht ungeprüft in Shell-Befehle übernehmen.
5. Vor dem Teilen vertrauliche Angaben prüfen.

**Prüfstand:** Mit ZipInfo 3.00 aus UnZip 6.00 wurden reine Namen, lange Ansicht, technische Ansicht und Summen an einem selbst erzeugten Deflate-ZIP geprüft. Die reine Liste enthielt den erwarteten Mitgliedsnamen; alle Aufrufe endeten erfolgreich. Das Archiv blieb bytegleich. Ungewöhnliche Namen, Verschlüsselung und alternative Kompressionsmethoden wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `unzip -Z` | Alternativer Einstieg in den Informationsmodus. |
| `unzip -t` | Prüft komprimierte Mitgliedsinhalte. |
| `zip` | Erstellt und verändert ZIP-Archive. |
| `7z l` | Andere Listenoberfläche für unterstützte Archive. |
| `diff` | Vergleicht bewusst erzeugte Textlisten. |

Ausgangseintrag: Datensatz 26 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
