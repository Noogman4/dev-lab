---
id: "shred"
name: "shred"
command: "shred"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "shred"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 198
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# shred – Überschreiben von einer Vernichtungsgarantie unterscheiden

## 1. Kurzbeschreibung

shred überschreibt ausgewählte Dateien und kann sie optional anschließend entfernen. Es garantiert auf heutigen Speichersystemen nicht pauschal, dass sämtliche früheren Kopien unwiederbringlich verschwinden.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Das Verfahren setzt voraus, dass die betreffenden Daten tatsächlich an den relevanten physischen Stellen überschrieben werden. SSD-Wear-Leveling, Snapshots, Copy-on-Write, komprimierte Speicherung, Datenjournale und andere Kopien können diese Annahme verletzen. Backups und externe Spiegel werden nicht automatisch erfasst. Ohne -u bleibt der Name normalerweise erhalten, obwohl sein Inhalt bereits verändert wurde. Mehr Durchläufe oder eine abschließende Nullrunde lösen diese Architekturprobleme nicht. Ein beobachteter Nullinhalt wäre nur ein sichtbarer Dateizustand und kein forensischer Löschbeweis.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt shred invocation](https://www.gnu.org/software/coreutils/manual/html_node/shred-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
shred [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -n ANZAHL | Zahl der Überschreibrunden, GNU-Vorgabe drei |
| -z | Zusätzliche abschließende Nullrunde |
| -x | Logische Länge einer normalen Datei nicht auf den nächsten Block aufrunden |
| -u | Nach Überschreiben zusätzlich entfernen |
| -s BYTES | Überschreibmenge begrenzen, verändert Auswahlwirkung |
| -f | Nötigenfalls Dateirechte zum Schreiben ändern, zusätzliche Wirkung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Das Muster ist ausschließlich eine Leseübung an einer selbst definierten Wegwerfdatei. Es wurde keine Datei überschrieben oder entfernt und kein Gerät angesprochen. Eine echte Datenträgerbereinigung ist nicht Gegenstand dieses Auftrags.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-shred-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'eigene unkritische Wegwerfbytes\n' > wegwerfdatei.txt
shred -n 1 -z -x -- ./wegwerfdatei.txt
)
```

### Schritt 3: Wirkung und Grenze verstehen

Dieser ausdrücklich nicht ausgeführte Aufruf würde eine normale Überschreibrunde und zusätzlich eine Nullrunde anfordern. -x würde die logische Dateilänge nicht zum nächsten Block aufrunden, ohne -u bliebe der Dateiname bestehen. Weder ein späterer erfolgreich gemeldeter Status noch ein Lesen von Nullen würde beweisen, dass Snapshots, SSD-Blöcke oder Backups keine alten Daten mehr enthalten.

## 6. Typische Anwendungsfälle

In älteren Abläufen die beabsichtigte Überschreibwirkung und ihre Grenzen beurteilen. Für reale vertrauliche Daten zuerst Speicherkonzept, Kopien und das für die konkrete Plattform geeignete Löschverfahren klären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf ist absichtlich destruktiv für den erreichbaren Inhalt. Hardlinks verweisen auf denselben Inhalt und wären ebenfalls betroffen. Bei falschem Ziel droht Datenverlust; auf Gerätedateien wären ganze Bereiche gefährdet. Unbekannte Speichereigenschaften dürfen nicht zugunsten einer scheinbaren Erfolgsgarantie ausgelegt werden. Vertrauliche Dateien nicht nur zum Test anlegen und keine Schutzrechte mit -f übergehen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Dateiname besteht nachher weiter | Ohne -u wird nicht automatisch entfernt, Inhalt kann trotzdem zerstört sein |
| Datei länger geworden | Ohne -x kann die letzte Blockgrenze aufgerundet werden |
| Alte Fassung im Snapshot vorhanden | Überschreiben erfasst andere gespeicherte Kopien nicht |

## 9. Sichere Varianten oder Tipps für Einsteiger

Kein Dateibeispiel als Nachweis einer medienweiten Löschung ausgeben. Die Rolle von -n, -z und -u getrennt lesen. Für aktuelle Datenträger sind passende verifizierte Verfahren gesondert zu planen; diese Dokumentation nimmt keine Änderung an Datenträgern oder Verschlüsselungsschlüsseln vor.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Keine Überschreib- oder Löschfunktion getestet, keine Wirksamkeitsbehauptung für SSDs, CoW, Snapshots oder Backups; nur Version gelesen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rm | Namen entfernen ohne gezieltes Überschreiben |
| stat | Aktuelle Länge anzeigen, kein Löschbeweis |
| sync | Schreibpuffer synchronisieren, keine Datenvernichtung |

Herkunft: Originaldatensatz 198 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
