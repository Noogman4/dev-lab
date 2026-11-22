---
id: "md5deep"
name: "md5deep"
command: "md5deep"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["md5deep", "forensik & recovery"]
status: "Manpage und RFC 6151 geprüft; keine Dateien gehasht"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 335
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# md5deep – ältere MD5-Bestände mit klaren Grenzen vergleichen

## 1. Kurzbeschreibung

`md5deep` berechnet MD5-Werte für Dateien und kann sie mit bekannten Werten vergleichen. Rekursive Verarbeitung und unterschiedliche Ausgabeformen gehören zur Werkzeugfamilie. **Für eigene lesbare Dateien sind keine Root-Rechte nötig.**

MD5 ist für neue Sicherheitsanwendungen mit benötigter Kollisionsresistenz ungeeignet. Dieser Eintrag erklärt deshalb vor allem den bewussten Umgang mit vorhandenen älteren MD5-Listen.

## 2. Was macht der Befehl?

Die [md5deep-Manpage](https://manpages.debian.org/trixie/hashdeep/md5deep.1.en.html) beschreibt Berechnung und Vergleich. Die dort genannte Familie enthält auch `sha256deep`, das einen anderen Algorithmus nutzt. Die Auswahl des Programms ist nicht bloß eine andere Schreibweise desselben Hashes.

[RFC 6151](https://www.rfc-editor.org/info/rfc6151/) erläutert die Sicherheitsgrenzen von MD5. Besonders die absichtliche Erzeugung verschiedener Daten mit gleichem Digest begrenzt Anwendungen, die auf Kollisionsresistenz angewiesen sind.

Ein Vergleich mit einer alten MD5-Liste kann für deren Kompatibilität sinnvoll sein. Daraus sollte keine neue Behauptung über sichere Herausgeberidentität oder Manipulationsschutz gegenüber einem gezielten Angreifer entstehen.

## 3. Syntax

```text
md5deep -h
md5deep DATEI
md5deep -r VERZEICHNIS
md5deep -m REFERENZLISTE DATEIEN
```

Anders als bei `hashdeep` folgt die Referenzdatei hier direkt auf die passende Vergleichsoption. Optionen nicht allein wegen ähnlicher Programmnamen unverändert übertragen.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-h` | Hilfe anzeigen. | Kein Dateiinhalt gehasht. |
| `-v` | Versionsinformation anzeigen. | Nicht dieselbe Bedeutung wie überall sonst. |
| `-r` | Unterverzeichnisse durchgehen. | Umfang ausdrücklich begrenzen. |
| `-m DATEI` | Bekannte Hashwerte suchen. | Kein vollständiges Bestandsaudit allein. |
| `-x DATEI` | Nicht passende Eingaben anzeigen. | Unbekannt ist nicht gleich schädlich. |
| `-l` | Relative Pfade ausgeben. | Arbeitskontext notieren. |
| `-0` | Datensätze mit NUL beenden. | Weiterverarbeitung muss dazu passen. |
| `-q` | Dateinamen aus der Ausgabe entfernen. | Eindeutige Zuordnung kann dadurch fehlen. |

Die Manpage beschreibt auch Optionen, die Fehlermeldungen unterdrücken. Sie sind für einen nachvollziehbaren ersten Vergleich ungeeignet, wenn dadurch fehlgeschlagene Lesevorgänge unsichtbar werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur eine eigene Übungsdatei vorsehen

```bash
(
  umask 077
  uebung="$(mktemp -d -t netmon-md5deep-XXXXXX)" || exit 1
  printf 'Eigene Vergleichsuebung\n' > "$uebung/notiz.txt" || exit 1
  cd "$uebung" || exit 1
  md5deep ./notiz.txt > referenz.md5 || exit 1
  md5deep -m referenz.md5 ./notiz.txt
)
```

Das Beispiel bleibt auf neue eigene Dateien begrenzt. Es wurde nicht ausgeführt, weil `md5deep` lokal nicht installiert ist. Kein Digest und keine Erfolgsausgabe werden als gemessen behauptet.

### Schritt 2: Vergleichszweck benennen

Die zweite Berechnung würde die eigene Datei gegen den zuvor erfassten Wert prüfen. Für diese unveränderte kleine Übung wäre ein Treffer zu erwarten. Das ist eine Erwartung, kein tatsächlich gemessenes Ergebnis.

### Schritt 3: Die Sicherheitsgrenze erklären

Die Liste stammt aus demselben Übungszustand. Sie authentisiert weder einen Herausgeber noch die ursprüngliche Herkunft einer fremden Datei. Ein neuer sicherheitsbezogener Bestand sollte mit geeignetem Algorithmus und vertrauenswürdiger Referenz geplant werden.

### Schritt 4: Vollständigkeit gesondert betrachten

Laut Manpage kann das Werkzeug bei bestimmten Lese- oder Berechtigungsproblemen trotzdem Status `0` liefern. Fehlermeldungen und tatsächlich verarbeitete Eingaben müssen deshalb zusätzlich geprüft werden.

## 6. Typische Anwendungsfälle

- Einen vorhandenen älteren MD5-Katalog im vorgesehenen Kompatibilitätskontext auswerten.
- Bekannte Daten in einem begrenzten Bestand wiederfinden.
- Die Unterschiede zwischen alten und neu erfassten Hashverfahren erklären.
- Eine bewusste Umstellung auf SHA-256 vorbereiten, ohne alte Werte umzudeuten.

Ein MD5-Wert lässt sich nicht in den SHA-256-Wert derselben Datei umrechnen. Dafür muss der eigentliche Dateiinhalt erneut mit dem anderen Algorithmus gelesen werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Berechnung liest Inhalte und kann bei vielen Dateien deutliche Last erzeugen. Ausgabelisten enthalten möglicherweise vertrauliche Pfade. Keine fremden Home- oder Gerätebestände für eine bloße Übung durchsuchen.

MD5-Treffer nicht als modernen Sicherheitsbeweis verwenden. Auch ein stärkerer Hash benötigt eine vertrauenswürdige Referenz; andernfalls kann ein Angreifer Daten und Referenz gemeinsam ersetzen.

Eine Ausgabeliste durch Shellumleitung darf keine wichtige vorhandene Datei überschreiben. Referenz und Quellbestand bewusst trennen.

## 8. Häufige Fehler

- **MD5 gleich Signatur:** Es fehlt jede bestätigte Signaturschlüsselidentität.
- **Optionen von `hashdeep` kopieren:** Bedeutungen und Argumente unterscheiden sich.
- **Kein Treffer gleich Schadsoftware:** Zunächst nur Abweichung von der Liste.
- **Status `0` gleich vollständig gelesen:** Fehlerausgabe beachten.
- **SHA-256 aus MD5 ableiten wollen:** Benötigt die Originalbytes.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für neue gewöhnliche Dateivergleiche SHA-256 mit `sha256sum` oder einer ausdrücklich entsprechend eingestellten Variante bevorzugen. Vorhandene MD5-Werte klar als solche kennzeichnen.

Eine alte Referenz nicht stillschweigend ersetzen. Wenn ein Bestand neu aufgenommen wird, Zeitpunkt, Algorithmus und Herkunft der neuen Grundlage dokumentieren.

## 10. Verwandte Befehle

- `sha256deep`: Verwandtes Werkzeug für SHA-256.
- `hashdeep`: Mehralgorithmus- und Auditfunktionen mit eigener Syntax.
- `md5sum`: Einfachere MD5-Berechnung.
- `sha256sum`: Einfacher SHA-256-Vergleich.
- `cmp`: Direkter Vergleich zweier konkreter Dateien.

**Prüfstand:** Dokumentationsprüfung. Kein Hostbestand gelesen, keine Referenz ersetzt und kein Lauf als bestanden ausgegeben.

Ausgangsdatensatz 335 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
