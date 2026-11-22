---
id: "foremost"
name: "foremost"
command: "foremost"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["foremost", "forensik & recovery"]
status: "Paket-Manpage geprüft; kein Carving-Lauf ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 330
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# foremost – Dateien anhand ihrer Inhaltsmerkmale extrahieren

## 1. Kurzbeschreibung

`foremost` sucht in Daten nach typischen Dateimerkmalen und extrahiert passende Bereiche. Diese Methode heißt File Carving. Sie kann helfen, wenn ursprüngliche Dateisystemnamen oder Verzeichniseinträge nicht mehr nutzbar sind.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Die Ausgabe benötigt einen eigenen beschreibbaren Ort mit ausreichend Platz. Ein erfolgreicher Lauf garantiert keine vollständigen Originaldateien.

## 2. Was macht der Befehl?

Die [Foremost-Manpage bei Debian](https://manpages.debian.org/trixie/foremost/foremost.8.en.html) beschreibt Suchmerkmale, Dateitypen und Ausgabe. Ein Treffer basiert auf Inhaltseigenschaften, nicht auf einer sicheren Wiederherstellung der ursprünglichen Dateisystemzuordnung.

Dadurch können auch eingebettete Dateien, unvollständige Fragmente oder mehrfach vorhandene Inhalte erscheinen. Eine extrahierte Datei kann anders heißen als früher. Ein passendes Suffix beweist nicht, dass sie sich vollständig öffnen lässt.

Für eine Auswertung ist daher nicht allein die Zahl der Dateien wichtig. Gefragter Typ, tatsächlicher Inhalt, erwartete Größe und Bezug zum Abbild gehören zur Bewertung.

## 3. Syntax

```text
foremost -h
foremost -i ABBILD -o AUSGABEVERZEICHNIS -t TYPEN
foremost -i ABBILD -o AUSGABEVERZEICHNIS -t jpg,pdf
```

Das Eingabeabbild bleibt von der Ausgabe getrennt. Das Beispiel richtet sich nicht an ein echtes Gerät und wird hier nicht ausgeführt.

## 4. Wichtige Optionen

| Option | Bedeutung | Folge |
| --- | --- | --- |
| `-h` | Hilfe anzeigen. | Kein Extraktionslauf. |
| `-i DATEI` | Eingabe wählen. | Passende bekannte Arbeitskopie verwenden. |
| `-o VERZEICHNIS` | Ergebnisse dort speichern. | Benötigt freien Platz. |
| `-t TYPEN` | Suchtypen begrenzen. | Nicht gewählte Typen bleiben außerhalb des Auftrags. |
| `-c DATEI` | Suchkonfiguration auswählen. | Inhalt und Herkunft prüfen. |
| `-v` | Ausführlicher berichten. | Ausgabe kann sensible Details enthalten. |
| `-w` | Nur Auditinformationen schreiben. | Keine Nutzdateiextraktion, aber weiterhin Ausgabe. |
| `-q` | Schnellsuche verwenden. | Kann bestimmte eingebettete Dateien verpassen. |
| `-T` | Zeitbezogenes Ausgabeverzeichnis verwenden. | Erleichtert getrennte Läufe. |

`-q` und `-Q` sind verschieden: Großes `Q` reduziert Meldungen. Eine stillere Ausgabe beweist keinen fehlerfreien Lauf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen Suchauftrag eingrenzen

Angenommen, `./analyse/arbeitskopie.img` ist eine freigegebene Kopie und gesucht werden JPEG- und PDF-Inhalte. Ein neuer Ergebnisordner wird auf einem geeigneten Ausgabeziel vorgesehen.

### Schritt 2: Eingabe und Ausgabe ausdrücklich trennen

```text
foremost -i ./analyse/arbeitskopie.img -o ./rettung-lauf-01 -t jpg,pdf
```

Der Aufruf ist ein nicht ausgeführter Plan. Werkzeug und Übungsabbild sind lokal nicht vorhanden. Der Ordnername ist kein tatsächlich erzeugtes Ergebnis.

### Schritt 3: Suchtypen verstehen

`jpg,pdf` begrenzt den Auftrag auf diese eingebauten Sucharten. Das bedeutet nicht, dass jede ursprüngliche JPEG- oder PDF-Datei noch vollständig vorhanden ist. Zerstörte oder fragmentierte Inhalte können unbrauchbar bleiben.

### Schritt 4: Ergebnisse einzeln einordnen

Ein späteres Ergebnis wäre zunächst eine extrahierte Datenfolge. Nur bekannte, geeignete Betrachter verwenden und aktive Inhalte nicht ungeprüft starten. Für vertrauliche Daten außerdem die Ergebnisablage entsprechend schützen.

## 6. Typische Anwendungsfälle

- Bestimmte Dateitypen aus einer bekannten Arbeitskopie extrahieren.
- Einen metadatenbasierten Rettungsversuch durch einen anderen Ansatz ergänzen.
- Eingebettete Inhalte bewusst untersuchen.
- Eine begrenzte Suche mit dokumentierter Konfiguration wiederholen.

Carving ersetzt keine Sicherung. Vorhandene Backups können Dateinamen, Struktur und Vollständigkeit deutlich zuverlässiger wiederherstellen als eine Signatursuche in Restdaten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Ausgabe kann sehr groß werden und das Ziel füllen. Niemals Rettungsdaten in das betroffene Originaldateisystem schreiben; dadurch können noch benötigte Restdaten überschrieben werden.

Eine Auswertung kann längst gelöschte persönliche oder fremde Inhalte sichtbar machen. Die Berechtigung zum Besitz einer Abbilddatei und der zulässige Untersuchungsumfang müssen klar sein. Für diese Dokumentation wird kein fremdes Material herangezogen.

Eine erhöhte Trefferzahl ist nicht automatisch bessere Qualität. Falsch abgegrenzte, doppelte oder unvollständige Ausgaben sind möglich und gehören zur Nachbewertung.

## 8. Häufige Fehler

- **Kein Erfolg trotz passender Endung:** Inhalt kann unvollständig sein.
- **Alter Name fehlt:** Carving rekonstruiert die ursprüngliche Struktur nicht zuverlässig.
- **Schnellmodus als gleiche Abdeckung lesen:** `-q` kann Treffer auslassen.
- **Ausgabeplatz erschöpft:** Ergebnisumfang und Fehlerstatus prüfen.
- **Konfiguration unbeachtet:** Andere Suchregeln verändern den tatsächlichen Auftrag.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer kleinen bekannten Kopie und wenigen Dateitypen beginnen. Jeden Lauf in einer neuen eigenen Ausgabeablage halten und den genauen Aufruf notieren.

Gefundene Dateien nicht automatisch in den normalen Dokumentenbestand übernehmen. Erst Inhalt, Qualität und mögliche Duplikate prüfen. Ein wiederhergestellter ausführbarer Inhalt ist nicht automatisch vertrauenswürdig.

## 10. Verwandte Befehle

- `photorec`: Anderes inhaltsbasiertes Rettungswerkzeug.
- `scalpel`: Konfigurierbares Carving.
- `fls`, `icat`: Dateisystemeinträge und zugehörige Inhalte betrachten.
- `extundelete`: Journalbasierter Ansatz für bestimmte ext-Dateisysteme.
- `sha256sum`: Ergebnisse identifizieren und Duplikate vergleichen.

**Prüfstand:** Manpage gelesen. Keine Extraktion, kein Originalzugriff, keine Mountaktion und kein reales Rettungsergebnis erzeugt.

Ausgangsdatensatz 330 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
