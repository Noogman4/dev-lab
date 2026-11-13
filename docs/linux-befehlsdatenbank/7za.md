---
id: "7za"
name: "7za"
command: "7za"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 2
reviewed_at: "2026-11-13"
locally_checked_version: "7-Zip (a) 23.01"
---

# 7za – Archive mit der eigenständigen 7-Zip-Variante bearbeiten

## 1. Kurzbeschreibung

`7za` erstellt, untersucht und entpackt Archive. Es gehört zur 7-Zip-Werkzeugfamilie und ist die Variante mit einem eingebauten, gegenüber der vollständigen Variante begrenzten Formatumfang und ohne externe Format-Plugins.

**Für eigene Dateien brauchst du keine Root-Rechte.** Der Aufruf ist nicht grundsätzlich lesend: `a` verändert Archive, `x` schreibt entpackte Dateien und `d` entfernt Archiveinträge. Die ursprüngliche Einstufung „sicher lesend“ beschreibt daher nur einzelne Arbeitsweisen.

## 2. Was macht der Befehl?

Mit einem Unterkommando wählst du die Aufgabe. Die Schreibweise ähnelt `7z`; die beiden Programmnamen garantieren jedoch keinen identischen Formatumfang. Prüfe bei einem fremden Archiv zunächst die Möglichkeiten der tatsächlich installierten Variante.

| Unterkommando | Aufgabe | Dateiwirkung |
| --- | --- | --- |
| `a` | Dateien hinzufügen, bei Bedarf ein Archiv erstellen. | Schreibt das Archiv. |
| `l` | Archiveinträge auflisten. | Liest den Inhalt. |
| `t` | Integrität testen. | Verarbeitet Archivdaten ohne entpackte Ausgabedateien. |
| `x` | Mit gespeicherter Ordnerstruktur entpacken. | Schreibt Zieldateien. |
| `e` | Ohne gespeicherte Ordnerstruktur entpacken. | Gleiche Dateinamen können kollidieren. |
| `d` | Ausgewählte Einträge entfernen. | Verändert das Archiv. |
| `i` | Informationen über unterstützte Formate anzeigen. | Zeigt den installierten Funktionsumfang. |

Die Varianten unterscheidet das [Debian-Handbuch für 7zip](https://manpages.debian.org/trixie/7zip/7za.1.en.html). Die hier genannten Unterkommandos wurden zusätzlich mit der lokalen Hilfe von `7za` 23.01 abgeglichen.

## 3. Syntax

```text
7za UNTERKOMMANDO [OPTIONEN] ARCHIV [DATEIEN_ODER_ORDNER ...]
```

Beispiele für unterschiedliche Absichten:

```bash
7za l "sammlung.7z"
7za a -t7z "sammlung.7z" "Material/"
7za x "sammlung.7z" -oAusgabe -aos
```

Eckige Klammern kennzeichnen optionale Teile und werden nicht eingegeben. Das Unterkommando ist kein Dateiname. Der erste Aufruf liest, der zweite schreibt ein Archiv, der dritte schreibt entpackte Dateien.

```bash
7za -h
7za i
```

Der erste Aufruf zeigt Hilfe, der zweite Formatinformationen. **Prüfpunkt:** Auf dem Zielsystem können Programmname, Paket und Funktionsumfang abweichen. Ein fehlendes `7za` bedeutet nicht, dass dort überhaupt kein 7-Zip vorhanden ist.

## 4. Wichtige Optionen

| Option | Bedeutung | Vorsicht oder Voraussetzung |
| --- | --- | --- |
| `-t7z` | Neues Archiv im 7z-Format anlegen. | Zum gewählten Format passende Optionen verwenden. |
| `-tzip` | Neues ZIP-Archiv anlegen. | Nicht jede zusätzliche ZIP-Methode ist mit jedem Empfängerprogramm kompatibel. |
| `-mx=5` | Mittlere Kompressionsstufe wählen. | Vernünftiger Ausgangspunkt, keine Garantie für eine kleinere Datei. |
| `-mx=0` | Ohne Kompression speichern. | Sinnvoll für bereits komprimierte Testdaten oder schnellen Durchsatz. |
| `-oORDNER` | Ausgabeordner beim Entpacken setzen. | Zusammenhängendes Argument, etwa `-o"Mein Ziel"`. |
| `-aos` | Vorhandene Ausgabedateien überspringen. | Schützt diese Dateien, erzeugt aber möglicherweise keinen vollständig neuen Datenbestand. |
| `-aoa` | Vorhandene Ausgabedateien überschreiben. | Kann Dateien ohne Rückfrage ersetzen. |
| `-p` | Passwort interaktiv abfragen. | Kein echtes Passwort als sichtbares Kommandozeilenargument anhängen. |
| `-mhe=on` | Auch Dateinamen im Archivkopf verschlüsseln. | Für das 7z-Format in Verbindung mit einem Passwort. |
| `-slt` | Technische Angaben beim Auflisten ausgeben. | Beispielsweise mit `7za l -slt sammlung.7z`. |

Ausführliche Grundlagen: [Überschreibmodi](https://sources.debian.org/data/main/p/p7zip/16.02%2Bdfsg-6/DOC/MANUAL/cmdline/switches/overwrite.htm), [Methoden und Kopfverschlüsselung](https://sources.debian.org/data/main/p/p7zip/16.02%2Bdfsg-6/DOC/MANUAL/cmdline/switches/method.htm) und [Ausgabeordner](https://sources.debian.org/data/main/p/p7zip/16.02%2Bdfsg-6/DOC/MANUAL/cmdline/switches/output_dir.htm). Diese ausführlichen Seiten stammen aus dem älteren p7zip-Handbuch; sie ersetzen nicht die Prüfung neuer versionsspezifischer Funktionen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine getrennte Übung vorbereiten

```bash
uebung="$(mktemp -d -t netmon-7za-XXXXXX)"
cd "$uebung"
pwd
mkdir "Material"
printf '%s\n' 'Eine kleine Testnotiz.' > "Material/notiz.txt"
```

Arbeite nur weiter, wenn `cd` erfolgreich war und `pwd` den neuen Übungsordner zeigt. `printf` erstellt die Testdatei; eine Wiederholung würde dieselbe Datei durch die Umleitung `>` neu schreiben.

### Schritt 2: Ein neues Archiv erstellen

```bash
7za a -t7z -mx=5 "sammlung.7z" "Material/"
```

`a` nimmt den Ordner auf, `-t7z` wählt das Format, `-mx=5` die Kompressionsstufe. Das Ergebnis heißt `sammlung.7z`. Die Quelldatei bleibt erhalten. Ein vollständiger Ordner wird auch ohne zusätzliches `-r` mit seinem Inhalt aufgenommen.

### Schritt 3: Auflisten und prüfen

```bash
7za l "sammlung.7z"
7za t "sammlung.7z"
```

In der Liste sollte `Material/notiz.txt` erscheinen. Der Test sollte ohne Fehler enden. Er prüft die verarbeitbaren Archivdaten, nicht die Vertrauenswürdigkeit oder Harmlosigkeit der enthaltenen Dateien.

### Schritt 4: Getrennt entpacken

```bash
7za x "sammlung.7z" -oAusgabe -aos
```

Die Testnotiz liegt anschließend unter `Ausgabe/Material/notiz.txt`. `-aos` lässt eine dort bereits vorhandene Datei bestehen. Für einen vollständigen Neuvergleich wählst du deshalb besser einen neuen Ausgabeordner statt immer denselben Zielordner.

## 6. Typische Anwendungsfälle

**Dateien zusammen weitergeben:** Ein neues ZIP lässt sich mit `7za a -tzip austausch.zip Material/` erstellen. Verwende einen noch nicht belegten Archivnamen, wenn du eine unabhängige Kopie möchtest.

**Ein fremdes Archiv zunächst untersuchen:** `7za l archiv.7z` zeigt Einträge, `7za l -slt archiv.7z` zusätzliche Details. Große gemeldete Ausgabemengen sind ein Anlass, freien Speicher und Herkunft genauer zu prüfen.

**Vertrauliche Daten verpacken:** `7za a -t7z -p -mhe=on privat.7z Material/` erstellt ein neues, passwortgeschütztes Archiv mit geschütztem Archivkopf. Die unverschlüsselten Quelldateien bleiben weiterhin vorhanden. Das Passwort muss für eine spätere Wiederherstellung verfügbar sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Bestehendes Archiv verändert:** `a` ist nicht „immer neu erstellen“. Ein vorhandenes Archiv kann ergänzt oder verändert werden. Für eine neue Sicherung einen neuen Namen wählen.
- **Unbeabsichtigte Dateiauswahl:** Fehlende Eingabepfade bei einer schreibenden Aktion können eine wesentlich größere Auswahl betreffen als erwartet. Pfade ausdrücklich angeben.
- **Dateien überschrieben:** Entpacken schreibt Daten. `-aoa` und automatische Ja-Antworten mit `-y` sind für ungeprüfte Inhalte keine vorsichtige Standardeinstellung.
- **Quelldateien gelöscht:** `-sdel` ist eine gesonderte Löschoption. Sie gehört nicht in den hier gezeigten Standardablauf.
- **Sensible Informationen sichtbar:** Dateinamen in Ausgaben und echte Passwörter in Argumenten können in Mitschnitten oder Verlauf auftauchen.
- **Verarbeitung fremder Daten:** Ein neuer Ordner ist keine Sandbox. Aktuelle Software verwenden und entpackte Skripte nicht ungeprüft starten.

Für ein Linux-Systembackup genügt ein gewöhnliches 7z-Archiv nicht ohne Prüfung benötigter Metadaten und Wiederherstellung. Die [p7zip-Manpage](https://manpages.debian.org/bookworm/p7zip-full/7z.1.en.html#Backup_and_limitations) weist ausdrücklich auf Grenzen bei Eigentümer- und Gruppeninformationen hin. Root-Rechte lösen diese Formatfrage nicht.

## 8. Häufige Fehler

| Beobachtung | Einordnung | Nächster Schritt |
| --- | --- | --- |
| `command not found` | Variante nicht installiert oder nicht im Suchpfad. | `command -v 7za` und vorhandene Alternativen prüfen. |
| Format nicht unterstützt | Die eigenständige Variante kann nicht jedes Format bearbeiten. | `7za i` und Distributionsdokumentation ansehen. |
| Archiv lässt sich nicht öffnen | Möglicherweise unvollständiger Download oder anderes Dateiformat. | Herkunft, Größe und tatsächlichen Dateityp prüfen. |
| Alte Zieldatei bleibt bestehen | Bei `-aos` beabsichtigt. | Neuen Zielordner verwenden, nicht vorschnell Überschreiben erzwingen. |
| Dateien liegen ohne Unterordner vor | `e` statt `x` benutzt. | Für die gespeicherte Struktur `x` wählen. |
| Test schlägt fehl | Unter anderem Datenfehler oder falsches Passwort möglich. | Ausgabe lesen; Originalarchiv und weitere Kopien erhalten. |

Für Skripte gilt: Eine vorhandene Ausgabedatei beweist keinen Erfolg. 7-Zip meldet unter anderem `0` für Erfolg, `1` für Warnungen und `2` für einen schwerwiegenden Fehler. Weitere Werte beschreibt das [Handbuch zu Rückgabewerten](https://sources.debian.org/data/main/p/p7zip/16.02%2Bdfsg-6/DOC/MANUAL/cmdline/exit_codes.htm).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit der obigen kleinen Übung beginnen und keine privaten Originale als erste Testdaten verwenden.
2. Ordnerpfade direkt angeben und Namen mit Leerzeichen in Anführungszeichen setzen.
3. Vor dem Entpacken auflisten und genügend Platz für die unkomprimierten Daten einplanen.
4. Die Originale behalten, bis eine getrennte Wiederherstellung überprüft ist.
5. `-aos` als Schutz vor einem bestimmten Überschreiben verstehen, nicht als umfassenden Sicherheitsmodus.
6. Bei einem Rechtefehler zuerst Pfade und Eigentum prüfen; nicht automatisch `sudo` voranstellen.
7. Für benötigte Formate die lokale Hilfe der installierten Variante heranziehen.

**Prüfstand:** Hilfe und der Ablauf Erstellen–Auflisten–Testen–Entpacken wurden mit `7za` 23.01 an eigenen Textdateien geprüft. Überspringen einer bestehenden Ausgabedatei wurde kontrolliert. Passwortdialog und andere Versionen wurden nicht praktisch geprüft. Die generische Syntax und pauschale Risikoeinstufung des ursprünglichen Datensatzes wurden inhaltlich präzisiert.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `7z` | Vollständigere Variante mit je nach Paket zusätzlicher Formatunterstützung. |
| `7zz` | Weitere eigenständige 7-Zip-Variante; Paket und Formatumfang prüfen. |
| `tar` | Ordnerbäume bündeln; für Linux-Metadaten passende Optionen und Formate beachten. |
| `zip`, `unzip` | Spezialisierte ZIP-Werkzeuge mit eigener Syntax. |
| `file` | Dateityp untersuchen, wenn Endung und Inhalt möglicherweise nicht zusammenpassen. |

Der genaue Ausgangseintrag bleibt in `index.json` unter Datensatz 2 erhalten. Weiterführende gemeinsame Grundlagen stehen außerdem in [7z.md](7z.md).
