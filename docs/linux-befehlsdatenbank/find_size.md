---
id: "find_size"
name: "find -size"
command: "find -size"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "find_size"]
status: "Ausgearbeitet; Größenbedingungen mit eigenen Testdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 56
reviewed_at: "2026-11-13"
locally_checked_version: "GNU findutils 4.9.0"
---

# find -size – Dateigrößen mit eindeutigen Grenzen suchen

## 1. Kurzbeschreibung

`find -size` wählt Einträge anhand ihrer logischen Größe aus. Der Eintrag bezeichnet eine Bedingung des Programms `find`, kein eigenständiges Werkzeug. Eine reine Suche mit Ausgabeaktionen verändert keine Dateiinhalte.

**Für eigene zugängliche Bestände sind keine Root-Rechte nötig.** Die hier dokumentierte Suche löscht nichts. Aktionen wie `-delete` oder `-exec` hätten einen anderen Umfang und werden nicht eingesetzt.

## 2. Was macht der Befehl?

Find durchläuft den Startbaum und prüft für jeden passenden Eintrag die Größe. Mit `-type f` wird die Auswahl auf reguläre Dateien beschränkt. Relevant ist deren logische Länge, nicht automatisch der tatsächlich belegte Plattenplatz. Sparse-Dateien können deshalb groß erscheinen, obwohl weniger Blöcke belegt sind.

Entscheidend ist die Einheit: Bei Einheiten größer als einem Byte wird für den Vergleich aufgerundet. `-size 1M` bedeutet nicht exakt 1 MiB, sondern eine auf eine MiB-Einheit gerundete Größe. Auch eine Datei mit nur einem Byte erfüllt diese Bedingung.

Grundlage: [GNU-find-Manpage der Distribution](https://manpages.debian.org/trixie/findutils/find.1.en.html) und lokale Hilfe von findutils 4.9.0. Die Grenzfälle wurden mit eigenen Dateien praktisch geprüft.

## 3. Syntax

```text
find STARTPFAD -type f -size [+|-]ZAHL[EINHEIT] -print
```

```bash
find "./Material" -type f -size +1048576c -print
```

Das Beispiel sucht Dateien mit **mehr als 1.048.576 Bytes**. Durch `c` erfolgt der Vergleich bytegenau. Ohne Vorzeichen gilt Gleichheit im jeweiligen gerundeten Maß; `+` bedeutet größer und `-` kleiner, jeweils ohne Einschluss der Grenze.

## 4. Wichtige Optionen

| Bedingung oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-size 0c` | Genau null Bytes. | Bei `-type f` leere reguläre Dateien. |
| `-size +100c` | Mehr als 100 Bytes. | 100 selbst gehört nicht dazu. |
| `-size -100c` | Weniger als 100 Bytes. | Enthält null bis 99 Bytes. |
| `-size 1M` | Aufgerundet eine MiB-Einheit. | Dateien von einem Byte bis einschließlich 1 MiB. |
| `-size -1M` | Aufgerundet weniger als eine MiB-Einheit. | Bei normalen Dateilängen nur leere Dateien. |
| `-size -1048576c` | Weniger als ein MiB in Bytes. | Enthält auch nicht leere Dateien unter der Grenze. |
| `-type f` | Nur reguläre Dateien. | Verzeichnisgrößen werden nicht als Datenbestand summiert. |
| `-maxdepth N` | Suchbaum begrenzen. | Nach dem Startpfad angeben. |
| `-xdev` | Andere Dateisysteme nicht hinabsteigen. | Ändert den berücksichtigten Bestand. |
| `-print0` | Namen NUL-getrennt ausgeben. | Für passende robuste Weiterverarbeitung. |

`k`, `M` und `G` bezeichnen hier binäre Einheiten. Ohne Einheit verwendet GNU find 512-Byte-Blöcke. Die Bedeutung nicht aus einer gleich aussehenden Option eines anderen Programms ableiten.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen kleinen Bestand anlegen

```bash
uebung="$(mktemp -d -t netmon-findsize-XXXXXX)"
cd "$uebung"
pwd
mkdir "Material"
printf '' > "Material/leer"
printf 'x' > "Material/ein-byte"
```

Nur nach erfolgreichem Wechsel fortfahren. Die beiden Dateien enthalten null beziehungsweise genau ein Byte. Es werden keine großen Benutzerdateien benötigt.

### Schritt 2: Leere Datei finden

```bash
find "./Material" -type f -size 0c -print
```

Erwartet wird nur `leer`. Die Bedingung betrifft logische Länge, nicht mögliche Dateisystemverwaltungsblöcke.

### Schritt 3: Aufrundung sichtbar machen

```bash
find "./Material" -type f -size 1M -print
```

Die Datei `ein-byte` ist ein Treffer, obwohl sie keineswegs ein MiB groß ist. Ihre Länge wird für diese Einheit auf eine Einheit aufgerundet.

### Schritt 4: Zwei vermeintlich gleiche Grenzen vergleichen

```bash
find "./Material" -type f -size -1M -print
find "./Material" -type f -size -1048576c -print
```

Die erste Suche findet nur die leere Datei. Die zweite findet beide Testdateien. Für eine fachlich exakte Byte-Grenze deshalb ausdrücklich Bytes verwenden.

### Schritt 5: Nur auswählen, nicht bereinigen

Die Liste dient zur Kontrolle. Eine große oder leere Datei ist nicht automatisch entbehrlich. Keine Löschaktion an diese Übung anhängen.

## 6. Typische Anwendungsfälle

**Große eigene Dateien eingrenzen:** Startpfad und strenge Byte-Grenze bewusst wählen.

**Leere reguläre Dateien untersuchen:** Mit `0c` suchen und anschließend deren Zweck prüfen. Leere Markerdateien können beabsichtigt sein.

**Bereiche auswählen:** Mehrere Größenbedingungen werden üblicherweise mit Und kombiniert. Ob die Unter- und Obergrenze eingeschlossen sein sollen, vorher festlegen.

**Speicherproblem vorbereitend analysieren:** Logische Dateilänge von tatsächlicher Belegung und freiem Dateisystemplatz unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Falsche Grenzen wählen falsche Daten aus

Die Rundung kann eine plausible Kurzform fachlich falsch machen. Bei späteren Änderungen wäre das besonders folgenreich. Zuerst kleine bekannte Grenzfälle prüfen und nur eine reine Liste erstellen.

### Logische Größe ist kein Löschkriterium

Sparse-Dateien, Datenbankdateien oder Images können wichtige große Inhalte darstellen. Aus einer Größenliste folgt keine Aussage über Entbehrlichkeit, Belegung oder Vertrauenswürdigkeit.

### Unvollständiger und veränderlicher Bestand

Rechtefehler, Mountgrenzen oder parallel veränderte Dateien können die Auswahl beeinflussen. Ein früherer Trefferpfad bindet kein später unverändert vorhandenes Objekt. Meldungen und Abschlussstatus mitbeurteilen.

### Dateinamen und Ausgabe

Namen können Zeilenumbrüche und Shell-Sonderzeichen enthalten. Zeilenlisten nicht ungeprüft als Kommandos verwenden. Bei maschineller Weiterverarbeitung passende NUL-Trennung und sichere Argumentübergabe planen.

**Root-Rechte sind für eigene Testdateien unnötig.** Keine verändernden Aktionen oder fremden Bestände wurden zum Nachweis genutzt.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Winzige Datei trifft `1M` | Größenrundung auf Einheiten. | Für exakte Grenzen `c` verwenden. |
| `-1M` findet nur leere Dateien | Aufgerundete Größe muss kleiner als eins sein. | Gewünschte Bytegrenze ausdrücklich schreiben. |
| Datei exakt an Grenze fehlt | `+` beziehungsweise `-` schließt Gleichheit aus. | Vergleichsart bewusst wählen. |
| Platzgewinn passt nicht zur Länge | Sparse-/Dateisystemeffekte. | Verbrauch separat mit du beurteilen. |
| Bestand unvollständig | Zugriff oder Suchgrenze. | Meldungen und Umfang prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit kleinen bekannten Größen beginnen.
2. Für exakte Grenzen Bytes und `c` verwenden.
3. Gleichheit sowie strenge Ober-/Untergrenze unterscheiden.
4. `-type f` und einen begrenzten Startpfad wählen.
5. Treffer erst ansehen und Zweck klären.
6. Keine automatische Löschung ableiten.

**Prüfstand:** GNU find 4.9.0 wurde mit selbst angelegten Dateien von 0, 1, 1.048.575, 1.048.576 und 1.048.577 Bytes geprüft. Die Bedingungen `+1048576c`, `-1M`, `1M` und `0c` lieferten genau die erwarteten Treffer. Größere Testdateien wurden sparsam angelegt. Keine Löschung, Fremddaten oder Gerätezugriffe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find -name` | Auswahl nach Basisnamen. |
| `stat` | Logische Größe und weitere Einzeldateieigenschaften lesen. |
| `du` | Verbrauch ausgewählter Bestände. |
| `df` | Verfügbaren Dateisystemplatz ansehen. |

Ausgangseintrag: Datensatz 56 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
