---
id: "find_name"
name: "find -name"
command: "find -name"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "find_name"]
status: "Ausgearbeitet; Namenssuche mit eigenen Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 55
reviewed_at: "2026-11-13"
locally_checked_version: "GNU findutils 4.9.0"
---

# find -name – Dateinamen mit begrenztem Suchumfang finden

## 1. Kurzbeschreibung

`find -name` sucht in einem Verzeichnisbaum nach passenden Basisnamen. Der Datenbankeintrag bezeichnet die Suchbedingung `-name` des Programms `find`.

**Für eigene zugängliche Ordner sind keine Root-Rechte nötig.** Mit den hier verwendeten Ausgabeaktionen wird nichts gelöscht oder ausgeführt. Andere find-Aktionen können sehr wohl Daten verändern.

## 2. Was macht der Befehl?

Find durchläuft den angegebenen Startpfad und wertet Bedingungen für einzelne Einträge aus. `-name` vergleicht nur den letzten Namensbestandteil mit einem Shell-artigen Muster. Ein Treffer sagt nichts über den tatsächlichen Dateiinhalt oder das Format aus.

`-type f` begrenzt auf reguläre Dateien. Ohne Typbedingung kann auch ein Verzeichnis mit passender Endung erscheinen. Einträge werden nicht als Momentaufnahme eingefroren; der Bestand kann sich während oder nach der Suche ändern.

Grundlagen: [Distributions-Manpage für GNU find](https://manpages.debian.org/trixie/findutils/find.1.en.html) und lokale Hilfe von findutils 4.9.0. Glob-Muster von `-name` und reguläre Ausdrücke von `-regex` sind unterschiedliche Suchsprachen.

## 3. Syntax

```text
find STARTPFAD [BEGRENZUNGEN] -type f -name 'MUSTER' -print
```

```bash
find "./Material" -type f -name '*.txt' -print
```

Das Muster wird zitiert, damit es find erreicht und nicht vorher von der Shell gegen den aktuellen Ordner erweitert wird. Eindeutige Startpfade wie `./Material` verhindern Verwechslungen mit Optionsnamen.

## 4. Wichtige Optionen

| Bestandteil | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-name MUSTER` | Basisnamen mit beachteter Groß-/Kleinschreibung prüfen. | `*.txt` ist kein Inhaltsfilter. |
| `-iname MUSTER` | Namenssuche ohne entsprechende Schreibungsunterscheidung. | Zeichensatz und Locale können relevant sein. |
| `-type f` | Reguläre Dateien wählen. | Verzeichnisse und andere Typen bleiben außen vor. |
| `-path MUSTER` | Pfaddarstellung statt nur Basisnamen prüfen. | Muster muss zum verwendeten Startpfad passen. |
| `-maxdepth N` | Tiefe begrenzen. | GNU-Funktion; nach dem Startpfad vor den Tests platzieren. |
| `-mindepth N` | Frühe Ebenen von der Auswertung ausnehmen. | Startpunkt hat Tiefe null. |
| `-xdev` | Andere Dateisysteme nicht hinabsteigen. | Kann fachlich gewünschte Mount-Unterbestände auslassen. |
| `-P` | Symbolischen Links nicht folgen. | GNU-Standard; vor die Startpfade setzen. |
| `-L` | Symbolischen Links folgen. | Kann Suchumfang erheblich erweitern. |
| `-print` | Namen zeilenweise ausgeben. | Für Menschen, nicht robust für beliebige Sonderzeichen. |
| `-print0` | Namen mit NUL trennen. | Für passende sichere Weiterverarbeitung. |
| `-o` | Logisches Oder. | Gruppierung und Vorrang beachten. |

Die Ausdrucksbestandteile ohne ausdrücklichen Operator werden gewöhnlich mit Und verknüpft. Und bindet stärker als Oder. Klammern müssen gegen die Shell geschützt werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsstruktur anlegen

```bash
uebung="$(mktemp -d -t netmon-findname-XXXXXX)"
cd "$uebung"
pwd
mkdir -p "Material/ordner.txt"
printf '%s\n' 'Eigene Notiz.' > "Material/notiz.txt"
printf '%s\n' 'Eigene Notiz.' > "Material/Gross.TXT"
printf '%s\n' 'Eigene Notiz.' > "Material/lesen.md"
```

Nur nach erfolgreichem Wechsel fortfahren. Das Verzeichnis mit `.txt` im Namen demonstriert die zusätzliche Typbedingung.

### Schritt 2: Reguläre Textnamen finden

```bash
find "./Material" -type f -name '*.txt' -print
```

Erwartet wird die kleine `notiz.txt`, nicht `Gross.TXT` und nicht das Verzeichnis `ordner.txt`. Die Dateiendung beweist keinen Textinhalt; der Test kennt diesen Inhalt unabhängig.

### Schritt 3: Schreibungsunterscheidung ändern

```bash
find "./Material" -type f -iname '*.txt' -print
```

Nun soll auch `Gross.TXT` erscheinen. Diese Änderung betrifft den Namen, keine Umbenennung oder Inhaltskonvertierung.

### Schritt 4: Zwei Namensformen gruppieren

```bash
find "./Material" -type f \( -name '*.txt' -o -name '*.md' \) -print
```

Die Klammer macht klar, dass der Typfilter für beide Alternativen gelten soll. Erwartet werden Notiz und Markdown-Datei.

### Schritt 5: Weiterverarbeitung separat planen

Für beliebige Dateinamen `-print0` und einen passenden NUL-fähigen Empfänger verwenden. Eine Liste ist keine Freigabe zum Löschen oder Ausführen gefundener Dateien.

## 6. Typische Anwendungsfälle

**Eigene Datei anhand des Namens finden:** Mit dem kleinsten sinnvollen Startordner beginnen.

**Projektdateien erfassen:** Mehrere passende Endungen bewusst gruppieren und Typfilter anwenden.

**Unvollständige Erinnerung an einen Namen:** Mit einem einfachen zitierten Muster suchen und Treffer anschließend einzeln lesen.

**Bestandsauswahl vorbereiten:** Ergebnis zunächst nur anzeigen. Eine spätere Veränderungsaktion braucht einen eigenen geprüften Umfang.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Suchaktionen unterscheiden

`-print` und `-print0` geben Daten aus. `-delete`, `-exec` und verwandte Aktionen besitzen andere Wirkungen. Nicht aus einem Suchrezept durch Anhängen eines kopierten Lösch- oder Ausführungsfragments unbemerkt einen Änderungsauftrag machen.

### Shell-Muster und Vorrang

Ein unzitiertes `*.txt` kann schon von der Shell aufgelöst werden. Ungruppierte Oder-Bedingungen können mehr Einträge auswählen als gedacht. Vor jeder späteren Aktion die reine Liste mit genau derselben Auswahl prüfen.

### Links, Mounts und Rechte

Ein großer Startpfad, Linkverfolgung oder eingehängte Unterbäume können den Umfang erhöhen. Fehlende Rechte führen zu Lücken und Meldungen. Root nicht pauschal ergänzen, nur um Warnungen verschwinden zu lassen.

### Fremde Namen und veränderlicher Bestand

Dateinamen können Zeilenumbrüche und Sonderzeichen enthalten. Zeilenlisten nicht ungeprüft als Shell-Code interpretieren. Ein Trefferpfad kann sich nach der Suche verändern; eine frühere Liste bindet nicht automatisch das spätere Objekt.

**Root-Rechte sind für die eigenen Testdaten nicht nötig.** Diese Dokumentation führt keine Lösch- oder Fremdprogramm-Aktion aus.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Expressionsfehler | Muster vorher von Shell erweitert. | Muster zitieren. |
| Verzeichnis als Treffer | Typfilter fehlt. | `-type f` ergänzen, wenn nur Dateien gemeint sind. |
| Großgeschriebene Endung fehlt | `-name` unterscheidet Schreibweise. | Bewusst `-iname` wählen. |
| Zu viele Treffer | Oder falsch gruppiert. | Klammern und Vorrang prüfen. |
| Pfadmuster trifft nicht | `-name` mit gesamtem Pfad verwechselt. | Passend `-path` oder Basisnamen verwenden. |
| Unvollständige Suche | Rechte- oder Zugriffsfehler. | Meldungen und Abschlussstatus beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit einem kleinen eigenen Startpfad beginnen.
2. Muster immer zitieren.
3. Gewünschten Dateityp ausdrücklich wählen.
4. Mehrere Alternativen bewusst gruppieren.
5. Zuerst nur ausgeben, nichts löschen oder ausführen.
6. Für beliebige Namen robuste NUL-Trennung planen.

**Prüfstand:** GNU find 4.9.0 wurde mit einem eigenen Baum aus normalen Dateien und einem ähnlich benannten Verzeichnis geprüft. Typfilter, `-name`, `-iname` und geklammerte Oder-Suche lieferten die erwarteten Treffer. Die Tests werteten `-print0` robust aus. Links, fremde Rechtebereiche, große Bestände und verändernde Aktionen wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find -size` | Auswahl nach logischer Dateigröße. |
| `grep` | Sucht Inhalte statt Dateinamen. |
| `locate` | Indexbasierte Suche mit anderem Aktualitätsmodell. |
| `stat` | Eigenschaften eines konkret gefundenen Eintrags lesen. |

Ausgangseintrag: Datensatz 55 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
