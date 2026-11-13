---
id: "debugfs"
name: "debugfs"
command: "debugfs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "debugfs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 214
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# debugfs – ext-Dateisysteme unterhalb der normalen Dateioperationen untersuchen

## 1. Kurzbeschreibung

`debugfs` untersucht und verändert ext2/ext3/ext4-Strukturen direkt. Der Standard öffnet lesend; `-w` schaltet Schreibzugriff ein. Für eigene Abbilddateien ist kein Root nötig, für reale Geräte gelten deren Zugriffsrechte.

## 2. Was macht der Befehl?

Das Werkzeug arbeitet mit Inodes und Blöcken, nicht über die normale eingehängte Dateiansicht. Pfade innerhalb des geöffneten Dateisystems sind von Pfaden auf dem Host zu unterscheiden. Selbst lesendes Öffnen macht Exportbefehle wie `dump` nicht nebenwirkungsfrei: Sie schreiben Hostdateien. Es ist ein Expertenwerkzeug und kein allgemeines Undelete-Programm.

Quelle, am 2026-11-13 gelesen: [debugfs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/debugfs.8.en.html) sowie lokale Manpage 1.47.0

## 3. Syntax

```text
debugfs [OPTIONEN] [GERAET_ODER_ABBILD]
debugfs -R ANFRAGE ABBILD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-R ANFRAGE` | Einen internen Befehl ausführen und beenden; Anfrage als ein Shellargument zitieren. |
| `-w` | Dateisystem schreibend öffnen; kein normaler Diagnosezusatz. |
| `-f DATEI` | Interne Befehle aus Datei ausführen; Quelle muss vertrauenswürdig sein. |
| `-b BYTES`, `-s BLOCK` | Blockgröße und alternativen Superblock wählen; falsche Werte verfälschen die Analyse. |
| `-z DATEI` | Alte überschriebene Blöcke protokollieren; Undo-Datei schützt nicht bei Strom-/Systemausfall. |
| `-V` | Version anzeigen und beenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
debugfs -R "stat /" ABBILD
Musterbedeutung: Inode des Wurzelverzeichnisses untersuchen
```

Der Schrägstrich bezeichnet hier die Wurzel im geöffneten Abbild, nicht automatisch die Hostwurzel. Erwartet würden Inode-Metadaten wie Typ und Blockbezüge. Die konkrete Inodeausgabe wurde nicht erzeugt. Keine internen Schreibbefehle oder Hostexporte wurden getestet.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Strukturanalyse:** Metadaten einer gesondert gesicherten ext-Abbildkopie untersuchen. **Entwicklung:** Dateisysteminterne Strukturen nachvollziehen; nicht mit allgemeinem Dateizugriff verwechseln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Schreibende Kommandos können Inkonsistenzen erzeugen, weil übliche Dateisystemprüfungen umgangen werden. Auf einem aktiv veränderten Dateisystem wäre die Sicht inkonsistent. Optionen zum Abschalten von Prüfsummenprüfung sind keine Reparatur. Auch interne `ln`/`unlink`-Operationen haben andere Nebenbedingungen als normale Shellwerkzeuge.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bad magic number | Falsches Objekt, Offset oder Dateisystem; nicht blind Schreibmodus ergänzen. |
| Datei nicht gefunden | Abbildinterner Pfad und Hostpfad verwechselt. |
| Einzelanforderung fehlerhaft | Shellzitierung und interne Syntax getrennt prüfen; Prozessende allein beweist keine korrekte Anfrage. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dumpe2fs` | ext-Superblockinformationen lesen. |
| `e2fsck` | Dateisystemprüfung mit anderem Ziel. |
| `e2image` | Spezielle Metadatenabbilder; nicht immer vollständige Nutzdatenkopien. |

Ausgangsdatensatz 214 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
