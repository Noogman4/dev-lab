---
id: "fls"
name: "fls"
command: "fls"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["fls", "forensik & recovery"]
status: "Sleuth-Kit-Handbuch geprüft; kein Abbild untersucht"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 329
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# fls – Dateinamen und Verzeichniseinträge in Abbildern lesen

## 1. Kurzbeschreibung

`fls` aus The Sleuth Kit listet Dateinamen und Verzeichniseinträge eines Dateisystems in einem Abbild. Es kann auch Hinweise auf gelöschte Einträge anzeigen. Das ist noch keine Wiederherstellung ihrer vollständigen Inhalte.

**Für ein eigenes lesbares Abbild sind keine Root-Rechte nötig.** Das Abbild muss dafür nicht als Dateisystem gemountet werden. Direkter Gerätezugriff wäre ein eigener, berechtigungsabhängiger Weg.

## 2. Was macht der Befehl?

Die [offizielle fls-Manpage](https://www.sleuthkit.org/sleuthkit/man/fls.html) beschreibt Dateisystemeinträge, Metadatenkennungen und Darstellung. Ein gefundener Name kann bei weiteren Schritten helfen, ist aber nicht gleichbedeutend mit intaktem Dateiinhaltsbereich.

Für ein ganzes Laufwerksabbild ist häufig die Lage des untersuchten Dateisystems anzugeben. Ein reines Partitionsabbild beginnt dagegen gegebenenfalls unmittelbar mit dessen Struktur. Ein falscher Beginn kann zu Fehlern oder einer unpassenden Interpretation führen.

Ergebnisse sollten immer an genau das Abbild und dessen Dateisystemposition gebunden sein. Eine isolierte Inodenummer ist ohne diesen Kontext kein eindeutiger Verweis auf irgendeine Datei des laufenden Rechners.

## 3. Syntax

```text
fls [OPTIONEN] ABBILD [METADATENKENNUNG]
fls -l -p partition.img
fls -r -p partition.img
fls -d -p partition.img
```

Die letzten Formen setzen ein passendes Partitionsabbild voraus. Sie wurden hier nicht ausgeführt. Ohne letzte Kennung wird der vorgesehene Wurzeleintrag des Dateisystems verwendet.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-l` | Zusätzliche Dateidetails zeigen. | Zeiten und Größe sind Metadatenangaben. |
| `-p` | Vollständige Pfaddarstellung wählen. | Pfad bleibt ein Name innerhalb des Abbilds. |
| `-r` | Verzeichnisse rekursiv durchgehen. | Gelöschte Verzeichnisse werden nicht allgemein rekursiv verfolgt. |
| `-d` | Gelöschte Einträge auswählen. | Inhalt kann bereits fehlen oder verändert sein. |
| `-u` | Nicht gelöschte Einträge auswählen. | Andere Einträge bleiben ausgeblendet. |
| `-o SEKTOREN` | Beginn des Dateisystems angeben. | Einheit und Sektorgröße müssen passen. |
| `-b BYTES` | Zugrunde gelegte Sektorgröße bestimmen. | Nicht mit Dateisystemblockgröße verwechseln. |
| `-f TYP` | Dateisystemtyp festlegen. | Keine Umwandlung des Abbilds. |
| `-V` | Version anzeigen. | Großes V beachten. |

`-m` erzeugt eine für Zeitlinien vorgesehene Ausgabe. Das dort verwendete Pfadpräfix ist kein echter Mountauftrag.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eingabe und Grenze festlegen

Angenommen, `./analyse/partition.img` ist eine bekannte eigene Arbeitskopie eines unterstützten Dateisystems. Die Datei wird hier weder erstellt noch geöffnet.

### Schritt 2: Eine begrenzte Auflistung planen

```text
fls -l -p ./analyse/partition.img
```

Der Aufruf würde Namen und zusätzliche Details ausgeben. Er wurde nicht ausgeführt, weil `fls` lokal nicht installiert ist. Es gibt keine gemessenen Einträge oder Zeiten.

### Schritt 3: Eine fiktive Kennung lesen

Angenommen, ein Eintrag verweist auf die Metadatenkennung `123`. Diese Kennung ist hier erfunden. Für eine spätere Inhaltsausgabe mit `icat` müssten dasselbe Abbild und dieselbe Dateisystemposition verwendet werden.

### Schritt 4: Gelöscht nicht mit rettbar verwechseln

Ein gelöschter Name kann noch aufgelistet werden, obwohl seine ehemaligen Datenblöcke inzwischen andere Inhalte tragen. Eine Namensauflistung erlaubt daher keine Erfolgszusage für die anschließende Rettung.

## 6. Typische Anwendungsfälle

- Dateisystemnamen aus einem Abbild ohne Mount lesen.
- Eine passende Kennung für eine gezielte Inhaltsanalyse suchen.
- Sichtbare und gelöschte Einträge gezielt unterscheiden.
- Eine dokumentierte Zeitlinienanalyse vorbereiten.

Bei Zeitangaben Zeitzone und mögliche Uhrabweichungen berücksichtigen. Eine aufbereitete Zeitdarstellung ist nicht automatisch der genaue Zeitpunkt einer menschlichen Handlung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Untersuchung liest potenziell private Namen und Metadaten. Ein Abbild kann auch Spuren gelöschter persönlicher Inhalte enthalten. Ergebnisse nicht ungeprüft öffentlich teilen.

Eine Shellumleitung der Ausgabe würde eine zusätzliche Datei schreiben. Das gewählte Ziel darf weder das Eingabeabbild noch eine wichtige vorhandene Datei sein. Fremde Dateinamen im Bericht nicht als auszuführende Befehle behandeln.

## 8. Häufige Fehler

- **Dateisystem nicht erkannt:** Abbildart, Offset und Unterstützung prüfen.
- **Offset in Bytes angegeben:** `-o` erwartet Sektoren.
- **Rekursion als vollständige Gelöschtenrettung:** `-r` hat ausdrücklich Grenzen.
- **Kennung aus anderem Abbild verwenden:** Herkunft und Position müssen zusammenpassen.
- **Name gefunden, Inhalt sicher:** Metadaten und Dateninhalt unterscheiden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten Arbeitskopie und einer kleinen Auflistung beginnen. Vor tieferer Analyse Abbildidentität, Dateisystembeginn und Sektorgröße dokumentieren.

Keine Mount- oder Reparaturaktion allein deshalb durchführen, weil eine Auflistung fehlschlägt. Die Ursache kann bereits eine unpassende Eingabegrenze sein.

## 10. Verwandte Befehle

- `mmls`: Datenträgerbereiche und mögliche Dateisystemlagen betrachten.
- `fsstat`: Allgemeine Dateisystemdetails lesen.
- `icat`: Inhalt über eine Metadatenkennung ausgeben.
- `istat`: Einzelne Metadaten betrachten.
- `mactime`: Passende Zeitliniendaten weiter aufbereiten.

**Prüfstand:** Herstellerhandbuch gelesen. Kein reales Abbild, Gerät oder Benutzerdateisystem untersucht; keine Datei wiederhergestellt.

Ausgangsdatensatz 329 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
