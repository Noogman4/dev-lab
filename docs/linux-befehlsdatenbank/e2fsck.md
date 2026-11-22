---
id: "e2fsck"
name: "e2fsck"
command: "e2fsck"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "e2fsck"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 216
reviewed_at: "2026-11-13"
locally_checked_version: "e2fsck 1.47.0 (5-Feb-2023), begrenzter Hilfstest in Datensatz 242"
---

# e2fsck – ext-Strukturen prüfen und Reparaturmodi unterscheiden

## 1. Kurzbeschreibung

`e2fsck` prüft ext2/ext3/ext4-Dateisysteme und kann deren Strukturen reparieren. Das ist keine bloße Statusabfrage. Für rohe Datenträger sind meist administrative Rechte nötig; eigene Abbilder benötigen nur passende Dateirechte.

## 2. Was macht der Befehl?

Journalwiedergabe und vollständige Strukturprüfung sind verschiedene Abläufe. Ein sauber markiertes Journaldateisystem wird nicht unter allen Umständen vollständig geprüft. `-f` erzwingt die Prüfung, `-n` öffnet lesend und beantwortet Reparaturfragen mit Nein. Ein gemountetes Dateisystem liefert auch bei lesender Prüfung keine verlässlichen konsistenten Ergebnisse. Die Ausnahmen und Warnungen der Manpage sind keine Aufforderung, aktive Systeme zu testen.

Quelle, am 2026-11-13 gelesen: [e2fsck-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/e2fsck.8.en.html)

## 3. Syntax

```text
e2fsck [OPTIONEN] GERAET_ODER_ABBILD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-n` | Lesend öffnen, Fragen mit Nein; nicht mit -p oder -y kombinieren. |
| `-f` | Auch als sauber markierte Strukturen prüfen. |
| `-p` | Bestimmte Reparaturen automatisch ausführen; kein Trockenlauf. |
| `-y` | Alle Fragen mit Ja beantworten; riskanter Sammelentscheid. |
| `-c` | badblocks-Lesetest integrieren; doppelt angegeben Lese-Schreib-Test. |
| `-b BLOCK`, `-B BYTES` | Alternativsuperblock und Blockgröße gezielt wählen. |
| `-z DATEI` | Undo-Protokoll alter Blöcke; keine Absicherung gegen Stromausfall. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
e2fsck -f -n ABBILD
Musterstatus 4: Fehler blieben unkorrigiert
Musterstatus 8: Betriebsfehler
```

Diese Syntax würde eine vollständige lesende Prüfung einer geeigneten unbenutzten Abbildkopie anfordern. Status 4 ist ein anderer Befund als ein Zugriffs- oder Betriebsfehler. Die Statusbits werden kombiniert: 0 ohne Fehler, 1 korrigiert, 2 korrigiert mit Neustartanforderung, 4 unkorrigiert, 8 Betriebsfehler, 16 Aufruffehler, 32 Abbruch, 128 Bibliotheksfehler. Keiner dieser Werte wurde hier erzeugt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Offline-Diagnose:** Eine konsistente ext-Kopie strukturell untersuchen. **Wartungsablauf:** Reparaturentscheidungen anhand eines gesonderten Sicherungs- und Wiederanlaufplans treffen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reparaturen verändern Metadaten und können Dateien anders zuordnen oder verwerfen. `-n` nicht mit beliebigen schreibenden/scanbezogenen Optionen kombinieren. Keine aktiven Root-Dateisysteme prüfen, keine automatischen Ja-Antworten als Fehlerlösung verwenden. Strukturkonsistenz beweist keine inhaltliche Unversehrtheit.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Prüfung übersprungen | Sauber-Markierung; -f ist eine bewusste andere Anforderung. |
| Gerät gemountet | Anhalten; keine erzwingende Bestätigung. |
| Unbekanntes Feature | Werkzeugversion unterstützt Dateisystem nicht; Features nicht blind entfernen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** e2fsck 1.47.0 (5-Feb-2023), begrenzter Hilfstest in Datensatz 242. Das Erklärungsmuster in Abschnitt 5 wurde nicht ausgeführt. Ergänzender praktischer Nachweis aus Datensatz 242: e2fsck -f -n wurde vor resize2fs ausschließlich an der eigenen frisch erzeugten 16-MiB-ext2-Abbilddatei erfolgreich ausgeführt. Der vollständige Ablauf steht in resize2fs.md. Praktische Prüfung von Reparaturmodi, beschädigten Daten, realen Geräten, gemounteten Dateisystemen und anderen Versionen offen. Quellenprüfung, Strukturprüfung und begrenzter Hilfstest sind getrennte Nachweise.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fsck` | Dispatcher an dateisystemspezifische Prüfer. |
| `dumpe2fs` | Metadaten anzeigen. |
| `resize2fs` | Größe eines ext-Dateisystems ändern. |

Ausgangsdatensatz 216 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
