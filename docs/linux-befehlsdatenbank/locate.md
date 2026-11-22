---
id: "locate"
name: "locate"
command: "locate"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "locate"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 187
reviewed_at: "2026-11-13"
locally_checked_version: "locate und updatedb nicht vorhanden"
---

# locate – Eine ausdrücklich ausgewählte Dateinamendatenbank durchsuchen

## 1. Kurzbeschreibung

locate sucht Dateinamen in einer zuvor erzeugten Datenbank. Es durchläuft bei einer normalen Suche nicht wie find den aktuellen Verzeichnisbaum.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die Aktualität hängt vom Index ab: Neue Namen können fehlen, entfernte noch enthalten sein. Diese Datei beschreibt die Plocate-Familie, bei der locate je nach Distribution als entsprechender Aufruf bereitgestellt wird. Das Programm fehlt lokal. Mlocate und GNU locate sind andere Implementierungen. Besonders mehrere Suchmuster unterscheiden sich: Plocate verknüpft sie mit UND, Mlocate gewöhnlich mit ODER. -d wählt eine eigene Datenbank, eine gesetzte LOCATE_PATH-Variable kann weitere Datenbanken ergänzen. Das Suchmuster ist zunächst eine Teilzeichenfolge, bei Globbingzeichen gelten andere Abgleichregeln.

[Gelesene Primärquelle: Plocate-Handbuch](https://plocate.sesse.net/plocate.1.html), ergänzt durch die [Debian-Plocate-Manpage](https://manpages.debian.org/bookworm/plocate/plocate.1.en.html).

## 3. Syntax

```text
locate [OPTIONEN] MUSTER ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -d DATEI | Ausdrückliche Datenbank auswählen |
| -b | Nur den letzten Pfadbestandteil vergleichen |
| -e | Nur aktuell vorhandene Einträge melden, zusätzliche Dateisystemabfragen |
| -i | Groß-/Kleinschreibung gemäß Locale ignorieren |
| -l ANZAHL | Trefferzahl begrenzen |
| -0 | NUL-getrennte Ausgabe |
| --regex | Erweiterten regulären Ausdruck verwenden, Implementierung prüfen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Erforderlich wären ein verifiziertes Locate-/Plocate-Programm und eine ausschließlich aus eigenen Testdaten gebaute passende Datenbank. Weder locate noch updatedb ist lokal vorhanden. Nichts wurde installiert und keine Systemdatenbank aktualisiert.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
LOCATE_PATH= locate -d EIGENE_TESTDATENBANK -b -- 'notiz'
```

### Schritt 3: Wirkung und Grenze verstehen

Das Muster würde nur die ausdrücklich angegebene private Datenbank befragen; LOCATE_PATH ist für diesen Aufruf leer. Es ist kein funktionierender Lauf auf diesem Prüfsystem und keine Liste tatsächlich gefundener Dateien. Die Datenbank muss vorher mit der passenden Implementierung und begrenztem eigenen Suchbaum erstellt worden sein. Eine locate-Suche ersetzt deren Erstellung nicht.

## 6. Typische Anwendungsfälle

Bekannte Dateinamen schnell in einem vorhandenen freigegebenen Index finden. Für eine aktuelle begrenzte Suche ohne Index ist find oft die passendere Vergleichsschnittstelle.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Index enthält potenziell vertrauliche Pfadnamen und kann veraltet sein. Die normale Systemsicht darf nicht mit einer privaten Übung verwechselt werden. updatedb ohne sorgfältige Begrenzung kann fremde Verzeichnisse erfassen. Sichtbarkeitsregeln und Datenbankzugriffsrechte sind implementationsabhängig. Status 1 kann bei Plocate sowohl Nichttreffer als auch Fehler bedeuten, daher Diagnosen mitlesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Neue Datei fehlt | Index noch nicht passend erzeugt oder aktualisiert |
| Mehrere Muster liefern weniger Treffer | Plocate verwendet UND, nicht die normale Mlocate-ODER-Regel |
| Trotz -d unerwartete Daten | LOCATE_PATH und passende Datenbankimplementierung prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für eine spätere eigene Übung Datenbankquelle und -ziel ausdrücklich begrenzen und genau diesen Index mit -d auswählen. Einen fehlenden Treffer nicht als Nachweis nehmen, dass ein Pfad nicht existiert. Fremde Indizes oder einen System-Updatejob nicht zum Test aufrufen.

**Prüfstand am 2026-11-13:** locate und updatedb nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. Indexaufbau, Datenbankformat, Sichtbarkeitsprüfung und alle Suchläufe bleiben offen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| updatedb | Erzeugt den passenden Dateinamenindex |
| find | Aktuelle Suche im ausdrücklich gewählten Baum |
| ls | Bekannte Verzeichnisse unmittelbar anzeigen |

Herkunft: Originaldatensatz 187 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
