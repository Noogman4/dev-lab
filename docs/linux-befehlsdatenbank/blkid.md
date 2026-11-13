---
id: "blkid"
name: "blkid"
command: "blkid"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["datentraeger", "uuid", "signaturen", "cache"]
status: "Korrigiert; Quellen, Hilfe und Version geprüft; praktische Geräteprüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 210
reviewed_at: "2026-11-13"
locally_checked_version: "blkid from util-linux 2.39.3; nur Hilfe und Version ausgeführt"
---

# blkid – Kennungen, Cache und direkte Signaturprüfung unterscheiden

## 1. Kurzbeschreibung

`blkid` verwendet `libblkid`, um Inhaltstypen und Kennungen von Speicherobjekten zu ermitteln, etwa Dateisystemtyp, UUID oder Label. Es formatiert und mountet dabei kein Dateisystem. Eine normale Abfrage kann trotzdem Geräte-I/O und Cacheverwaltung auslösen.

**Hilfe, Version und verfügbare unprivilegierte Abfragen benötigen nicht generell Root.** Darauf bezieht sich der Dokumentkopf. Direkte Zugriffe brauchen passende Leserechte auf das Ziel; unprivilegierte Standardabfragen können nur unbestätigte Cachewerte liefern. Die Rechtebedingungen sind kein Grund, für diese Übung zu eskalieren.

## 2. Was macht der Befehl?

Das Programm erkennt Signaturen und liest daraus `NAME=WERT`-Informationen. `TYPE` kann beispielsweise ein Dateisystem oder einen anderen erkannten Inhaltstyp bezeichnen. Eine Dateisystem-UUID ist eine gespeicherte Kennung, keine Seriennummer des physischen Laufwerks. Klone können dieselbe UUID enthalten; auch Labels sind nicht zuverlässig einzigartig.

| Betriebsart | Informationsquelle | Wichtige Grenze |
| --- | --- | --- |
| Standardabfrage | Geräteinformationen mit Cache-/Auswertungsmechanismen. | Unprivilegierte Ergebnisse können aus ungeprüftem Cache stammen. |
| `-L LABEL` oder `-U UUID` | Auflösung einer gesuchten Kennung. | Ein gefundenes Ziel beweist keine globale Eindeutigkeit. |
| `-p` | Direkte Low-Level-Probe, Cache wird umgangen. | Erfordert ein angegebenes Ziel und Zugriff darauf. |

Ohne Geräteoperand kann der Standardmodus erkannte Partitionen und unpartitionierte Geräte aus der Systemübersicht berücksichtigen. Ein nacktes `blkid` ist deshalb kein auf „nichts“ begrenzter Lernaufruf. Der Standardmodus kann kollidierende Signaturen still auslassen; `-p` liefert dafür den besonderen Rückgabewert 8.

Gelesene Quellen: [Debian-Manpage zu util-linux 2.41.5](https://manpages.debian.org/trixie/util-linux/blkid.8.en.html), [offizielles util-linux-Handbuch im Quellrepository](https://kernel.googlesource.com/pub/scm/utils/util-linux/util-linux/+/master/misc-utils/blkid.8.adoc) und lokale Manpage zu 2.39.3. Der Repositoryzweig `master` ist ein veränderlicher Entwicklungsstand, kein Versionsnachweis für das lokale Programm.

## 3. Syntax

```text
blkid [STANDARDOPTIONEN] [GERAET ...]
blkid -s UUID -o value GERAET
blkid -p [PROBEOPTIONEN] GERAET ...
blkid -L LABEL
blkid -U UUID
```

**Nur Syntaxmuster, keine Geräteaufrufe für diese Übung.** Bei `-p` muss mindestens ein Ziel angegeben werden. Die frühere Schreibweise `blkid -p [GERAET]` war falsch, weil sie den Operanden als optional erscheinen ließ. Auch der UUID-Filter ist hier bewusst mit einem ausdrücklichen Ziel dargestellt, um den Bereich nicht unbeabsichtigt auszuweiten.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `-p`, `--probe` | Direkte Signaturprobe ohne Cache. | Anders als Standardauswertung; mindestens ein Ziel nötig. |
| `-s TAG`, `--match-tag TAG` | Angezeigte Felder auswählen, auch mehrfach möglich. | Filtert die Ausgabe, nicht zuverlässig den Erfolgsstatus. |
| `-o full` | Vollständige menschenlesbare Kennungszeile, Standardformat. | Reihenfolge der Felder ist nicht festgelegt. |
| `-o value` | Nur Werte ausgeben. | Mit genau gewähltem Tag sinnvoll; Zuordnung zu Geräten kann fehlen. |
| `-o export` | Schlüssel/Wert-Zeilen ausgeben. | Eingaben nicht als Shellcode ausführen. |
| `-o device` | Nur Gerätenamen ausgeben. | Bei Label-/UUID-Auflösung automatisch gewählt. |
| `-c DATEI` | Alternative Cachedatei verwenden. | `-c /dev/null` startet ohne alte Cachetreffer, verhindert aber keine Gerätezugriffe. |
| `-g`, `--garbage-collect` | Nicht mehr vorhandene Ziele aus Cache entfernen. | Cacheänderung, keine reine Anzeige. |
| `-n LISTE` | Probe auf Inhaltstypen beschränken. | Für `-p`; Kommaliste und lokale Unterstützung prüfen. |
| `-O OFFSET`, `-S GROESSE` | Position beziehungsweise untersuchte Größe bei Probe wählen. | Falscher Bereich kann zu fehlender Erkennung führen. |
| `-L LABEL`, `-U UUID` | Ziel nach Kennung auflösen. | Ein einzelnes Ergebnis ist kein Beweis gegen Duplikate. |

Low-Level-Ausgabe kann andere Namen für verwandte Informationen liefern, zum Beispiel `PART_ENTRY_UUID` statt `PARTUUID`. Dateisystem-UUID und Partitionskennung sind außerdem unterschiedliche Kennungsebenen. Nicht jedes Ziel hat alle diese Felder.

## 5. Beispiel erklärt Schritt für Schritt

**Kein Gerätetest.** Voraussetzungen sind ein vorhandenes util-linux-`blkid` und die Bereitschaft, die folgenden Muster ausschließlich als Erklärung zu lesen. Nur der erste Schritt wird tatsächlich am Programm ausgeführt.

### Schritt 1: Hilfe und Version ohne Zielzugriff lesen

```bash
blkid --help
blkid --version
```

Erwartet werden Optionsübersicht und Versionsangabe. Lokal wurde `blkid from util-linux 2.39.3` mit `libblkid 2.39.3` gemeldet. Diese beiden Aufrufe fordern keine Geräteinventur an. Keine weiteren Shellbefehle mit einem Geräteoperand folgen.

### Schritt 2: Eine fiktive Standardausgabe lesen

**Erfundenes Muster, nicht gemessen:**

```text
BEISPIELGERAET: LABEL="LERNEN" UUID="11111111-2222-3333-4444-555555555555" TYPE="ext4"
```

`BEISPIELGERAET` ist ein erklärender Platzhalter. `LABEL` ist der gespeicherte Name, `UUID` die gespeicherte Dateisystemkennung und `TYPE` der erkannte Inhaltstyp. Diese Zeile beweist weder Mountzustand noch Hardwareidentität oder Dateisystemintegrität.

### Schritt 3: Gefilterte Ausgabe von vollständiger Ausgabe unterscheiden

Würde bei einem gesondert autorisierten Ziel nur der Tag UUID mit Format `value` gewählt, könnte die Ausgabe zum obigen Muster so aussehen:

```text
11111111-2222-3333-4444-555555555555
```

Der Gerätename fehlt absichtlich. Bei mehreren Zielen können solche Werte ohne weitere Zuordnung missverständlich sein. Fehlt ein ausgewählter Tag, kann trotz leerer gefilterter Ausgabe der Status 0 entstehen, wenn andere Informationen erkannt wurden. Daher immer Modus, Tagfilter und Rückgabewert zusammen lesen.

### Schritt 4: Ein fiktives Probe-/Exportmuster einordnen

**Ebenfalls nur Muster, kein ausgeführter `-p`-Aufruf:**

```text
DEVNAME=BEISPIELGERAET
LABEL=LERNEN
UUID=11111111-2222-3333-4444-555555555555
TYPE=ext4
USAGE=filesystem
```

`export` verteilt Informationen auf einzelne Schlüssel/Wert-Zeilen. Eine tatsächliche Probe kann zusätzliche Partitionsfelder liefern oder einzelne Felder auslassen. Ein erkannter Typ bedeutet noch keine Prüfung aller Dateisystemstrukturen. Werte wie Labels sind Daten vom untersuchten Objekt; Ausgabe niemals an `eval` oder einen anderen Codeinterpreter weiterreichen.

### Schritt 5: Abschlussstatus verstehen

Die Handbücher nennen folgende Werte; sie wurden hier nicht durch Gerätezugriffe provoziert:

| Status | Bedeutung | Schlussfolgerung |
| --- | --- | --- |
| `0` | Ziel gefunden und Informationen ermittelbar. | Kein Integritätsnachweis; Tagfilter kann trotzdem leere Ausgabe erzeugen. |
| `2` | Gesuchter Token fehlt, Ziel nicht identifizierbar oder Informationen nicht ermittelbar. | Nicht automatisch „leer“ oder „defekt“. |
| `4` | Aufruf- oder anderer Fehler. | Argumente und Meldungen prüfen. |
| `8` | Mehrdeutige Probe im Low-Level-Modus. | Kollidierende Signaturen fachlich klären, nicht blind löschen. |

## 6. Typische Anwendungsfälle

**Kennungen in einer bestehenden Konfiguration verstehen:** Gespeicherte UUID und Label mit einer bereits autorisierten Inventur vergleichen. Eine Änderung an Mountkonfiguration oder Datenträgern ist ein eigener Auftrag.

**Cacheabweichungen untersuchen:** Zeitpunkt, Rechte und Modus festhalten. Eine direkte Probe umgeht den Cache, ersetzt aber keine eindeutige Geräteidentifikation.

**Dateisystem- und Partitionskennungen unterscheiden:** `UUID` nicht mit `PARTUUID` gleichsetzen. Die Wahl hängt davon ab, auf welche Ebene ein Verweis tatsächlich zeigen soll.

## 7. Risiken, Nebenwirkungen und Vorsicht

Normale Signaturabfragen schreiben keine neuen Dateisystemsignaturen, können aber Geräte lesen, Cachedateien aktualisieren und je nach Konfiguration Auswertungs-/udev-Mechanismen berühren. `-g` verändert Cachemetadaten. Das Programm deshalb nicht pauschal als nebenwirkungsfreie Textanzeige behandeln.

Ein leeres Ergebnis ist mehrdeutig: Rechte, ungeeigneter Bereich, unbekannter Typ, alter Cache und kollidierende Signaturen sind unterschiedliche Ursachen. `-c /dev/null` ist kein Ersatz für `-p` und kein „kein I/O“-Schalter.

Klone können UUIDs duplizieren. Gerätenamen können sich ändern. Kennungen vor administrativer Verwendung durch weitere passende Merkmale prüfen. Aus Signaturerkennung folgt weder eine Ausführungsfreigabe für `mount` noch für Signaturlöschung.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `-p` ohne Ziel scheitert | Pflichtoperand fehlt. | Syntax verstehen; hier kein reales Ziel ergänzen. |
| Keine Kennungen sichtbar | Rechte, Cache, Filter oder Erkennung. | Modus und Status zusammen prüfen. |
| Gefilterte Ausgabe leer, Status 0 | Gewählter Tag fehlt, andere Information erkannt. | Nicht nur Erfolgscode oder Text allein auswerten. |
| Kennungen unterscheiden sich | Cache gegen Probe oder andere Kennungsebene. | Feldnamen, Quelle und Zeitpunkt dokumentieren. |
| Zwei Datenträger teilen eine UUID | Klonen oder bewusst gleiche Kennung. | Nicht als eindeutige Hardwareadresse behandeln. |
| Skript erwartet feste Feldreihenfolge | Ausgabe ist dafür nicht garantiert. | Passendes Format und sichere Datenverarbeitung verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe, Version und erklärten Mustern beginnen. Für eine später autorisierte Systemübersicht empfehlen die Handbücher eher `lsblk` beziehungsweise `findmnt`; deren Aufruf gehört ebenfalls nicht zum hier ausgeführten Nachweis. Keine Cachebereinigung und keine Probe aus bloßer Neugier starten.

**Prüfstand am 2026-11-13:** `blkid` und `libblkid` 2.39.3 durch `--version` bestätigt; `--help` sowie lokale und beide verlinkten Handbücher gelesen. Die Shellbefehle aus Schritt 1 wurden ausgeführt. **Nicht praktisch geprüft:** Standardinventur, Cachezugriff/-änderung, `-p`, Ausgabeformate an einem Ziel, Rechtefälle und Rückgabewerte eines Gerätetests. Alle Kennungszeilen sind ausdrücklich Muster. Kein reales Gerät geöffnet und kein Mount ausgeführt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lsblk` | Übersicht von Blockgeräten und ihren Beziehungen. |
| `findmnt` | Bestehende Einhängungen untersuchen. |
| `findfs` | Dateisystem nach Kennung auflösen. |
| `wipefs` | Signaturen untersuchen oder entfernen; Löschfunktionen sind eigenständig gefährlich. |
| `mount` | Dateisystem einhängen; separate Systemaktion. |

Ausgangsdatensatz 210, Kategorie und Zuordnung wurden mit dem eingefrorenen Katalog und der Original-CSV abgeglichen. Entwurfsoriginal und Quelldaten bleiben unverändert.
