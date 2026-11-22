---
id: "install"
name: "install"
command: "install"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "install"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 185
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# install – Dateien kopieren und Zielattribute bewusst setzen

## 1. Kurzbeschreibung

GNU install kopiert Dateien mit festgelegten Zielrechten oder legt Verzeichnisse an. Es ist kein Paketmanager und löst keine Softwareabhängigkeiten auf.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Der Name stammt aus der Installation von Build-Ergebnissen in Zielverzeichnisse. Ohne -m gilt normalerweise ein ausführbarer Zielmodus, weshalb Text- und Konfigurationsdateien einen ausdrücklich passenden Modus brauchen. -D erzeugt fehlende Eltern und kopiert eine Datei, -d erzeugt nur Verzeichnisse. Die angegebenen Dateirechte sind nicht automatisch die Rechte aller mit -D entstehenden Eltern. install erhält erweiterte Attribute nicht allgemein wie eine vollständige Metadatensicherung. -o und -g betreffen Eigentümer beziehungsweise Gruppe und benötigen je nach Ziel besondere Rechte.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt install invocation](https://www.gnu.org/software/coreutils/manual/html_node/install-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
install [OPTIONEN] QUELLE ZIEL
install [OPTIONEN] -t ZIELORDNER QUELLE ...
install [OPTIONEN] -d ORDNER ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -m MODUS | Rechte des Zielobjekts ausdrücklich setzen |
| -D | Fehlende Eltern erzeugen und Datei kopieren |
| -d | Verzeichnisse erzeugen statt Datei kopieren |
| -p | Zugriffs- und Änderungszeit der Quelle übernehmen |
| -C | Bei gleicher passender Datei unnötige Änderung vermeiden |
| -b | Vorhandenes Ziel vorher sichern |
| -s | Binärsymbole entfernen, verändert Inhalt |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Ein eigener kurzer Konfigurationstext wird nur in ein neues Unterverzeichnis des Übungsordners kopiert. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-install-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'modus=test\n' > eigene.conf
install -D -m 0640 -- eigene.conf ausgabe/konfiguration/eigene.conf
cmp eigene.conf ausgabe/konfiguration/eigene.conf
test "$(stat -c '%a' -- ausgabe/konfiguration/eigene.conf)" = 640
stat -c '%a %n' -- ausgabe/konfiguration/eigene.conf
)
```

### Schritt 3: Ergebnis verstehen

-D legt die fehlenden Zielordner an. -m 0640 macht die Datei für den Eigentümer les- und schreibbar und für die Gruppe lesbar. cmp bestätigt identische Bytes, stat den Dateimodus 640. Es wurde nichts in /usr, /etc oder ein sonstiges Systemziel installiert. Der Test sagt nichts über fremde Eigentümer, ACLs oder SELinux-Kontexte aus.

## 6. Typische Anwendungsfälle

Eigene Build-Ergebnisse kontrolliert in ein eigenes Stagingverzeichnis kopieren. Für Textdateien einen nicht ausführbaren Modus festlegen und Dateiwirkung von einer tatsächlichen Systeminstallation trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Bestehende Ziele können ersetzt und Rechte verändert werden. Das scheinbar vertraute Wort install macht einen Systempfad nicht ungefährlich. -s startet ein Strip-Werkzeug und ist für gewöhnliche Textdateien ungeeignet. Fehlende Privilegien nicht durch ein pauschales sudo umgehen. Eine Kopie ist kein vollständiges Metadatenbackup.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Textdatei ist ausführbar | Die Install-Vorgabe ist für Programme gedacht, -m bewusst setzen |
| Elternordner haben andere Rechte | Dateimodus und beim Anlegen geltende Elternregeln unterscheiden |
| Eigentümerwechsel abgewiesen | Keine Verwaltungsrechte für die eigene Übung erforderlich, -o weglassen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst ein eigenes neues Stagingziel verwenden. Quelle und Ziel nicht verwechseln, Inhalte vergleichen und den tatsächlichen Zielmodus auslesen. -C ist eine Vergleichsoptimierung mit Attributbedingungen und kein allgemeiner Trockenlauf.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Systeminstallation, Eigentümeränderung, Strip-, ACL- oder SELinuxprüfung. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cp | Kopieren mit anderen Attributvorgaben |
| mkdir | Nur Verzeichnisse anlegen |
| chmod | Rechte vorhandener Objekte ändern |

Herkunft: Originaldatensatz 185 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
