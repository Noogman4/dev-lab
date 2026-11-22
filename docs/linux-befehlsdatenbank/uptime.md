---
id: "uptime"
name: "uptime"
command: "uptime"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["uptime", "grundlagen & hilfe"]
status: "Keine reale Last- oder Sitzungsauswertung durchgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 373
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale procps-ng-Manpage gelesen"
---

# uptime – Laufzeit und Lastmittelwerte richtig einordnen

## 1. Kurzbeschreibung

`uptime` zeigt, wie lange das System läuft, und gewöhnlich weitere Angaben wie Lastmittelwerte. **Root-Rechte sind nicht nötig.** Es misst nicht allein die CPU-Auslastung einer Anwendung.

## 2. Was macht der Befehl?

Die lokale procps-ng-Manpage nennt die Mittelwerte für eine, fünf und fünfzehn Minuten. Die Linux-Last umfasst lauffähige Aufgaben und bestimmte nicht unterbrechbare Wartezustände, etwa bei I/O.

Ein Lastwert ist deshalb kein Prozentwert. CPU-Anzahl, zeitlicher Verlauf und Wartegründe gehören zur Bewertung. Ein einzelner hoher Wert erklärt noch nicht, welches Programm die Ursache ist.

## 3. Syntax

```bash
uptime
uptime -p
uptime -s
```

Die Formen zeigen unterschiedliche Ausschnitte. Es wird kein Neustart und keine Lastbegrenzung durchgeführt.

## 4. Wichtige Optionen

| Option | Inhalt | Grenze |
| --- | --- | --- |
| `-p` | Lesbare Laufzeit. | Keine vollständige Lastansicht. |
| `-s` | Berechneter Systemstart. | Zeitpunkt mit Systemzeitkontext lesen. |
| `-h` | Hilfe. | Kein Leistungstest. |
| `-V` | Programmversion. | Kein Kernel- oder Anwendungsstatus. |

Die normale Ausgabe kann außerdem eine Zahl erfasster Anmeldesitzungen enthalten. Das ist keine vollständige Personenzählung.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, eine fiktive Anzeige meldet Lastwerte `2.0`, `1.0`, `0.5`. Das zeigt einen höheren kurzfristigen als längerfristigen Mittelwert. Es ist keine gemessene lokale Ausgabe.

Ob diese Werte belastend sind, hängt unter anderem von verfügbaren CPUs und den beteiligten Wartezuständen ab. „2.0 bedeutet 200 Prozent CPU“ wäre deshalb keine korrekte allgemeine Übersetzung.

Für die Ursachenanalyse wären bei Bedarf gezielte Prozess- und I/O-Informationen nötig. Sie werden nicht allein aus der Laufzeitanzeige abgeleitet.

## 6. Typische Anwendungsfälle

- Einen vermuteten Neustart zeitlich einordnen.
- Kurz- und längerfristige Lasttendenzen vergleichen.
- Einen Leistungsbericht um eine begrenzte Momentaufnahme ergänzen.
- Laufzeit von Anwendungsfunktion unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Abfrage ist lesend. Ihre Interpretation kann dennoch falsche Maßnahmen auslösen, etwa das Beenden eines unbeteiligten Prozesses.

Eine lange Laufzeit ist weder automatisch ein Fehler noch ein Qualitätsbeweis. Ein wichtiger Neustart kann ausstehen, während ein anderes System bewusst lange laufen soll. Den betrieblichen Kontext klären.

## 8. Häufige Fehler

- **Load als CPU-Prozent lesen:** Andere Größe.
- **Ein Wert gleich Ursache:** Prozessbezug fehlt.
- **Sitzungszahl gleich Personen:** Mehrere oder unvollständig erfasste Sitzungen sind möglich.
- **Laufzeit gleich Dienstlaufzeit:** Einzelne Anwendungen können später gestartet sein.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die benötigte Frage auswählen: Laufdauer, Startzeit oder Lasttendenz? Danach nur passende Zusatzdaten heranziehen.

Keine Prozesse oder Dienste auf Basis eines einzelnen Lastwertes neu starten. Eine nachvollziehbare Ursache braucht mehr Kontext.

## 10. Verwandte Befehle

- `top`, `htop`: Prozessbezogene Ansicht.
- `vmstat`: Weitere System- und Warteinformationen.
- `w`: Sitzungsbezogene Übersicht.
- `systemctl`: Bestimmte Dienstzustände.

**Prüfstand:** Lokale Manpage gelesen. Keine echte Prozessanalyse, kein Neustart und kein Lasttest.

Ausgangsdatensatz 373 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
