---
id: "guymager"
name: "guymager"
command: "guymager"
category: "Forensik & Recovery"
language: "de"
root_required: true
risk_level: "danger"
tags: ["guymager", "forensik & recovery"]
status: "Projektseite und Manpage geprüft; kein Gerät ausgewählt oder aufgenommen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 332
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; kein GUI-Start"
---

# guymager – Datenträgerabbilder mit einer grafischen Oberfläche aufnehmen

## 1. Kurzbeschreibung

`guymager` startet einen grafischen Abbildaufnehmer. Das Programm kann Datenträger in Abbilddateien erfassen und unterstützt auch Klonvorgänge. Diese beiden Arten von Ausgabe haben unterschiedliche Risiken.

**Für den üblichen Zugriff auf physische Geräte sind administrative Rechte erforderlich.** Eine Geräteaufnahme ist kein gewöhnlicher Dateibetrachter und wird nicht allein zum Ausprobieren der Oberfläche gestartet.

## 2. Was macht der Befehl?

Die [Guymager-Projektseite](https://guymager.sourceforge.io/) nennt unter anderem flache Abbilddateien sowie EWF- und AFF-Formate. Die [Distributions-Manpage](https://manpages.debian.org/trixie/guymager/guymager.1.en.html) beschreibt Startparameter und Protokolle.

Die Oberfläche erleichtert Auswahl und Fortschrittsanzeige. Sie ersetzt nicht die eindeutige Identifikation von Quelle und Ziel. Zwei gleich große Geräte können verschiedene Inhalte und Funktionen haben. Ein bekannter Serienbezug ist aussagekräftiger als eine wechselnde Position in einer Liste.

Eine Aufnahme dokumentiert die gelesenen Daten unter bestimmten Bedingungen. Ob die Quelle ruhig, vollständig lesbar und gegen Veränderung geschützt war, muss separat festgehalten werden.

## 3. Syntax

```text
guymager
guymager log=EIGENES_PROTOKOLL cfg=BEKANNTE_KONFIGURATION
```

Der Start öffnet eine GUI und kann Geräte erfassen beziehungsweise Protokolle schreiben. Er ist kein vorausgesetzter folgenloser Hilfsaufruf. Ein allgemeines `--help` wird aus dem Datenbankplatzhalter hier nicht abgeleitet.

## 4. Wichtige Optionen

| Parameter oder Auswahl | Zweck | Abgrenzung |
| --- | --- | --- |
| `log=DATEI` | Programmprotokoll wählen. | Zusätzliches Schreibziel. |
| `cfg=DATEI` | Konfiguration bestimmen. | Herkunft und Einstellungen müssen bekannt sein. |
| Abbildformat | Speicherform festlegen. | Unterstützung durch spätere Analysewerkzeuge prüfen. |
| Quellgerät | Zu erfassendes Medium auswählen. | Identität unabhängig von der Listenposition bestätigen. |
| Abbildziel | Dateien und Segmente speichern. | Kapazität und Vertraulichkeit planen. |
| Klonziel | Auf anderes Gerät schreiben. | Kann dessen bisherige Daten überschreiben. |

Weitere Konfigurationsparameter sind versionsabhängig in der mitgelieferten Konfiguration beschrieben. Nicht beliebige Schalter aus einer anderen Imager-Anleitung übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen Aufnahmeplan vor der GUI erstellen

Für ein fiktives Übungsmedium zuerst Quelle, erwartete Größe und geeigneten Ausgabeort beschreiben. Es wird hier kein tatsächlicher Gerätename vorgegeben und kein Gerät aus der laufenden Maschine ausgewählt.

### Schritt 2: Dateiabild und Klonen unterscheiden

Für die geplante Auswertung wird eine neue Abbilddatei benötigt. Ein Klon auf ein anderes Gerät wäre eine andere Aufgabe. Die grafische Auswahl muss diesen Unterschied vor dem Start eindeutig zeigen.

### Schritt 3: Speicherform und spätere Nutzung abstimmen

Ein flaches Abbild kann anders verarbeitet werden als ein segmentierter Container. Vorher klären, welche Analysewerkzeuge die gewünschte Ausgabe tatsächlich lesen können. Alle Segmente gehören zum vorgesehenen Datensatz.

### Schritt 4: Bericht und Prüfung einplanen

Hashangaben, Lesefehler und Aufnahmeumfang müssen zusammen betrachtet werden. Ein angezeigter Abschluss ist keine unabhängige Bestätigung, dass die fachlich richtige Quelle gewählt wurde.

Keiner dieser GUI-Schritte wurde lokal ausgeführt; `guymager` ist nicht installiert. Es wurden keine Geräte gescannt, geöffnet oder beschrieben.

## 6. Typische Anwendungsfälle

- Eine autorisierte Datenträgeraufnahme mit nachvollziehbaren Metadaten planen.
- Eine geeignete Arbeitskopie für spätere Analyse erzeugen.
- Mehrteilige Ausgaben unter einem klaren Namens- und Ablagekonzept erstellen.
- Aufnahmeberichte und Prüfinformationen gemeinsam verwalten.

Ein normaler Imager ist nicht automatisch die beste Rettungsstrategie für stark fehlerhafte Medien. Bei Lesefehlern muss der weitere Umgang zum Zustand der Quelle passen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das falsche Klonziel kann Daten verlieren. Auch ein Abbildziel auf dem untersuchten Originalmedium ist ungeeignet, weil Schreibzugriffe dort die zu erfassenden Daten verändern können.

Abbilder können gelöschte Inhalte, Zugangsdaten und persönliche Dokumente enthalten. Entsprechend geschützte Ablage und genügend Platz vorsehen. Eine Kompression macht Inhalte nicht vertraulich.

Die Projektseite beschreibt Schutzmarkierungen für konfigurierte lokale Geräte. Eine solche Markierung ist eine zusätzliche Hilfe, keine Garantie, dass jede Quellauswahl automatisch korrekt erkannt wird.

## 8. Häufige Fehler

- **Gerät nur nach Größe auswählen:** Mehrere Medien können gleich groß sein.
- **Klonen mit Dateiabild verwechseln:** Anderes Ziel und andere Folgen.
- **Ein Segment allein weitergeben:** Der Container kann dadurch unvollständig sein.
- **Hash als Quellenfreigabe lesen:** Hash und richtige Geräteidentität sind getrennt.
- **Keine Fehler gemeldet, also konsistente Quelle:** Laufende Veränderungen gesondert betrachten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Die Bedienung zuerst anhand der Dokumentation und eines Aufnahmeplans lernen. Einen echten Geräteversuch nur mit geeigneter, ausdrücklich freigegebener Übungsquelle durchführen.

Alte Installationsanleitungen auf Projektseiten können überholte Paket- und Schlüsselverfahren enthalten. Für eine tatsächliche Installation die aktuellen Vorgaben der Distribution nutzen; hier wurde nichts installiert oder systemweit eingerichtet.

## 10. Verwandte Befehle

- `dcfldd`: Kommandozeilenorientiertes Kopieren und Hashen.
- `ddrescue`: Geplante Aufnahme bei Lesefehlern.
- `sha256sum`: Gespeicherte Dateien identifizieren.
- `mmls`, `fsstat`: Aufgenommene Abbilder anschließend analysieren.
- `ewfinfo`: EWF-Containerinformationen, soweit installiert.

**Prüfstand:** Projektseite und Handbuch gelesen. Kein GUI-Start, Gerätezugriff, Mount, Klon oder Abbildauftrag ausgeführt.

Ausgangsdatensatz 332 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
