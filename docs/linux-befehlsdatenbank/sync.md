---
id: "sync"
name: "sync"
command: "sync"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "sync"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 200
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# sync – Schreibpuffer mit passendem Wirkungsbereich synchronisieren

## 1. Kurzbeschreibung

GNU sync fordert die Synchronisierung gepufferter Schreibvorgänge an. Es ist weder ein Kopierprogramm noch ein Ersatz für ein Backup oder das kontrollierte Beenden einer Anwendung.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Ohne Dateiangabe betrifft sync die globale Synchronisierung, nicht nur das aktuelle Verzeichnis. Mit ausdrücklich angegebenen Dateien verwendet GNU sync normalerweise fsync für diese Dateien. -d wählt fdatasync mit den für die Daten nötigen Metadaten. -f bezieht dagegen das ganze Dateisystem ein, auf dem die angegebene Datei liegt; der Wirkungsbereich ist also größer als der eine Dateiname vermuten lässt. Ein Anwendungsprogramm kann zusätzlich noch eigene nicht an den Kernel übergebene Puffer halten. Erfolgreiche Synchronisierung allein bestätigt weder einen konsistenten Mehrdatei-Anwendungszustand noch die Wiederherstellbarkeit einer Sicherung.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt sync invocation](https://www.gnu.org/software/coreutils/manual/html_node/sync-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
sync [OPTIONEN] [DATEI ...]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| ohne DATEI | Globale Synchronisierung anfordern, kein reiner Lesemodus |
| DATEI ... | Bei GNU gezielte fsync-Anforderungen für diese Dateien |
| -d, --data | Daten und nötige Metadaten mit fdatasync synchronisieren |
| -f, --file-system | Ganzes jeweils zugehöriges Dateisystem mit syncfs synchronisieren |
| --version | Nur Programmversion anzeigen, kein Funktionsnachweis |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Der Funktionsaufruf wird hier nicht ausgeführt, auch nicht global. Das Muster erklärt nur den auf eine neue eigene normale Datei begrenzten GNU-Modus. Geräte und eingehängte Dateisysteme werden dafür nicht untersucht oder verändert.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-sync-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'eigener unkritischer Testinhalt\n' > eigene-datei.txt
sync -- ./eigene-datei.txt
)
```

### Schritt 3: Wirkung und Grenze verstehen

Das Muster würde nach dem Schreiben eine gezielte Synchronisierungsanforderung für die eigene Datei stellen. Es benutzt weder den globalen argumentlosen Aufruf noch -f. Eine tatsächliche Messung von Medienpersistenz, Controllern oder Stromausfallverhalten wird nicht behauptet. Ein späterer erfolgreicher Rückgabestatus wäre nur das Betriebssystemergebnis dieses Aufrufs, kein vollständiger Haltbarkeitsnachweis.

## 6. Typische Anwendungsfälle

Vorhandene Speicherroutinen verstehen und deren beabsichtigten Wirkungsbereich unterscheiden. Konsistente Backups, Anwendungs-Flush und kontrolliertes Aushängen gehören in eigenständige abgestimmte Abläufe.

## 7. Risiken, Nebenwirkungen und Vorsicht

Globale oder dateisystemweite Synchronisierung kann Last und Wartezeit für andere Anwendungen verursachen. Ein angegebener Gerätename zusammen mit -f betrifft dessen umgebendes Dateisystem und ist nicht automatisch die erwartete Datenträgeroperation. sync ersetzt weder ein Unmount noch schützt es vor logisch fehlerhaften Daten oder unzuverlässigem Hardwareverhalten.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Keine Ausgabe | Normal für Erfolg, Status und ausgewählten Wirkungsbereich trotzdem beachten |
| Aufruf dauert lange | Offene I/O kann Wartezeit verursachen, nicht beliebig weitere globale Aufrufe starten |
| Nach sync fehlt Anwendungsinhalt | Noch nicht an den Kernel übergebene Anwendungspuffer sind eine zusätzliche Ebene |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor Verwendung klären, ob Datei-, Dateisystem- oder globale Synchronisierung beabsichtigt ist. -f nicht als Force- oder Einzeldateioption missverstehen. Diese Dokumentation führt weder eine Systemoptimierung noch einen Datenträgertest aus.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Nur Version und Primärquelle geprüft, kein fsync-/fdatasync-/syncfs-/globaler Funktionslauf und kein Persistenztest. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| stat | Metadaten anzeigen, keine Synchronisierung |
| cp | Kopieren, kein vollständiger Konsistenzplan |
| umount | Aushängen als separate Systemaktion |

Herkunft: Originaldatensatz 200 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
