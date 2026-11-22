---
id: "sleuthkit"
name: "sleuthkit"
command: "The Sleuth Kit (Werkzeugsammlung)"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["sleuthkit", "forensik & recovery"]
status: "Projektbeschreibung geprüft; Katalogplatzhalter als Sammlungsname präzisiert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 339
reviewed_at: "2026-11-13"
locally_checked_version: "Werkzeugsammlung lokal nicht installiert"
---

# sleuthkit – die Werkzeugsammlung statt eines einzelnen Befehls einordnen

## 1. Kurzbeschreibung

`sleuthkit` bezeichnet in diesem Katalog The Sleuth Kit, eine Sammlung von Analysewerkzeugen und Bibliotheken. Es ist hier kein nachgewiesener einzelner Linux-Befehl mit universeller Syntax `sleuthkit --help`.

**Für die Analyse eigener lesbarer Abbilddateien mit geeigneten Einzelwerkzeugen sind keine Root-Rechte nötig.** Zugriff auf geschützte Geräte ist ein anderer Anwendungsfall mit zusätzlichen Rechten.

## 2. Was macht der Befehl?

Die [offizielle Projektübersicht](https://www.sleuthkit.org/sleuthkit/) beschreibt eine Bibliothek und mehrere Kommandozeilenprogramme zur Analyse von Datenträger- und Dateisysteminformationen. Deshalb wird zuerst das passende Einzelwerkzeug gewählt.

Für diese Datenbank sind beispielsweise `mmls`, `fsstat`, `fls`, `icat` und `tsk_recover` eigene dokumentierte Einträge. Ihre Optionen sind nicht unter einem erfundenen Sammelaufruf zusammenzufassen.

Eine Analysefolge arbeitet auf mehreren Ebenen: erst Abbild und Bereichsstruktur, dann Dateisystem, anschließend einzelne Einträge und Inhalte. Ein Ergebnis aus einer Ebene beantwortet nicht automatisch alle Fragen einer anderen Ebene.

## 3. Syntax

Es gibt für den Sammlungsnamen keine hier bestätigte universelle Befehlssyntax. Stattdessen beispielsweise:

```text
mmls ABBILD
fsstat DATEISYSTEMABBILD
fls DATEISYSTEMABBILD
icat DATEISYSTEMABBILD METADATENKENNUNG
```

Die Formen sind eine Übersicht. Eingabeart und gegebenenfalls Offsets müssen für jeden konkreten Fall stimmen. Keiner dieser Aufrufe wurde für diesen Eintrag ausgeführt.

## 4. Wichtige Optionen

Optionen gehören zum jeweiligen Programm, nicht zur Sammlung. Die passende Auswahl lässt sich nach Aufgabe ordnen:

| Frage | Einzelwerkzeug | Ergebnisart |
| --- | --- | --- |
| Welche Bereiche enthält das Laufwerksabbild? | `mmls` | Volume- und Partitionsübersicht. |
| Welche Struktur besitzt das Dateisystem? | `fsstat` | Allgemeine Dateisystemdetails. |
| Welche Namen und Kennungen sind sichtbar? | `fls` | Verzeichniseinträge. |
| Welcher Inhalt gehört zu einer Kennung? | `icat` | Dateidaten auf Standardausgabe. |
| Welche Dateien sollen exportiert werden? | `tsk_recover` | Dateien in einer eigenen Zielablage. |

Ein identischer Optionsbuchstabe kann bei verschiedenen Werkzeugen etwas anderes bedeuten. Besonders `-h` bei `icat` nicht als universelle Hilfe verwenden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Aufgabe formulieren

Angenommen, aus einer freigegebenen Arbeitskopie soll eine bestimmte bekannte Datei betrachtet werden. Es wird kein tatsächliches Benutzerabbild für diese Dokumentation geöffnet.

### Schritt 2: Eingabeebene bestimmen

Bei einem ganzen Laufwerksabbild muss die passende Dateisystemposition bekannt sein. Bei einer reinen Partitionskopie kann diese zusätzliche äußere Struktur fehlen. Ein Werkzeug für Partitionstabellen muss dort nicht dieselbe Ausgabe liefern.

### Schritt 3: Namen und Inhalt verbinden

Eine passende `fls`-Auflistung könnte eine Metadatenkennung ergeben. `icat` müsste anschließend dieselbe Quelle und Lage verwenden. Eine zufällige Kennung aus einer anderen Aufnahme ist keine gültige Verbindung.

### Schritt 4: Ausgabe getrennt behandeln

Ein Export schreibt neue Dateien und braucht eine geeignete Ablage. Eine lesende Auflistung ist deshalb nicht mit einer vollständigen Rettung gleichzusetzen. Für jedes Ergebnis Herkunft und tatsächlichen Prüfumfang notieren.

## 6. Typische Anwendungsfälle

- Für eine Abbildanalyse das richtige Einzelwerkzeug auswählen.
- Eine nachvollziehbare Folge von der Bereichsübersicht bis zur Datei planen.
- Begriffe wie Partition, Dateisystem, Metadatenkennung und Inhalt auseinanderhalten.
- Einen Export von einer bloßen Status- oder Namensauflistung unterscheiden.

Die Sammlung ist keine allgemeine Garantie für vollständige Wiederherstellung. Unterstützte Formate und Funktionen müssen zur konkreten lokalen Version und Quelle passen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Abbilder können private und gelöschte Inhalte enthalten. Nur bekannte autorisierte Quellen analysieren und Ergebnisse angemessen schützen. Der Dateibesitz allein erklärt nicht jeden zulässigen Verwendungszweck.

Fehlerhafte Offsets oder falsche Eingabearten können irreführende Ergebnisse erzeugen. Aus einer solchen Fehlersituation keine ungeplante Reparatur am Original ableiten.

Einzelwerkzeuge mit Inhaltsausgabe oder Export können viel Platz beanspruchen beziehungsweise Zielpfade überschreiben, wenn die Shellumleitung falsch gewählt wurde. Die Sammlung als Ganzes ist deshalb nicht pauschal „nur lesend“ für jede mögliche Aufruffolge.

## 8. Häufige Fehler

- **Paketname als ausführbaren Befehl behandeln:** Tatsächliches Einzelwerkzeug wählen.
- **Eine Option überall übertragen:** Jeweiliges Handbuch lesen.
- **Partitionsebene überspringen:** Dateisystemlage kann falsch sein.
- **Name gefunden, Datei vollständig gerettet:** Unterschiedliche Nachweise.
- **Alle Funktionen als lokal getestet ausgeben:** Hier wurde nur die Architektur dokumentiert.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer konkreten Frage und einer bekannten Arbeitskopie beginnen. Nur das dafür benötigte Einzelwerkzeug verwenden. Eingabe, Position, Einheit und Ausgabeziel gemeinsam notieren.

Dieser Eintrag ändert die feste Katalogzuordnung nicht. Er korrigiert den allgemeinen Platzhalter fachlich, ohne einen nicht bestätigten Sammelbefehl zu erfinden.

## 10. Verwandte Befehle

- `mmls`, `fsstat`, `fls`, `icat`: Hier genannte Einzelwerkzeuge.
- `tsk_recover`: Geplanter Export aus einem Abbild.
- `photorec`: Anderer, inhaltsbasierter Rettungsansatz.
- `guymager`: Abbildaufnahme statt anschließender Detailanalyse.

**Prüfstand:** Projektbeschreibung und bereits zugeordnete Herstellerhandbücher verwendet. Keine neue Inhaltsprüfung älterer Datenbanktexte, kein Programmstart und kein Abbildzugriff.

Ausgangsdatensatz 339 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
