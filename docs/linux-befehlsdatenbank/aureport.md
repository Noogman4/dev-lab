---
id: "aureport"
name: "aureport"
command: "aureport"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["aureport", "firewall & sicherheit"]
status: "Upstream-Handbuch geprüft; Beispiel als nicht ausgeführte Offlineauswertung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 308
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# aureport – Auditprotokolle zu verständlichen Berichten verdichten

## 1. Kurzbeschreibung

`aureport` erstellt Übersichten aus Linux-Auditprotokollen. Statt jedes Ereignis einzeln durchzusehen, lassen sich beispielsweise Anmeldungen oder fehlgeschlagene Aktionen zusammenfassen. Das Werkzeug verändert keine Auditregeln.

**Für eine eigene lesbare Protokollkopie sind keine Root-Rechte nötig.** Die Systemprotokolle sind häufig besonders geschützt. Ein fehlendes Leserecht ist deshalb kein Grund, die Originaldateien allgemein zugänglich zu machen.

## 2. Was macht der Befehl?

Ein Rohprotokoll enthält zusammengehörige Auditdatensätze. `aureport` ordnet diese für die gewählte Berichtskategorie ein. Eine Zusammenfassung kann Schwerpunkte zeigen, ersetzt aber nicht die Einzelfallanalyse.

Das [aureport-Upstream-Handbuch](https://man7.org/linux/man-pages/man8/aureport.8.html) beschreibt Eingabe, Berichtstypen und Darstellung. Die [Linux-Audit-Projektübersicht](https://github.com/linux-audit/audit-userspace) erläutert die Ereignisaufzeichnung.

Zahlen hängen von den vorliegenden Daten und ihrer Auswahl ab. „Drei fehlgeschlagene Anmeldungen“ ist eine andere Aussage als „drei Angreifer“. Wiederholte Bedienfehler, Dienste und automatisierte Abläufe sind mögliche andere Erklärungen, die anhand der Ereignisse geprüft werden müssen.

## 3. Syntax

```text
aureport [OPTIONEN]
aureport --help
aureport --input DATEI --login --summary
```

`DATEI` steht für eine ausdrücklich ausgewählte Kopie im Audit-Rohformat. Eine beliebige Textdatei mit selbst formulierten Beschreibungen ist kein passender Ersatz. Ohne explizite Eingabe kann das Werkzeug die konfigurierten Protokolle heranziehen.

## 4. Wichtige Optionen

| Option | Wirkung | Hinweis |
| --- | --- | --- |
| `--input DATEI` | Bestimmte Eingabe auswerten. | Original und Analyseausgabe getrennt halten. |
| `--login` | Bericht zu Anmeldungen wählen. | Nicht jede Authentisierung ist dieselbe Ereigniskategorie. |
| `--auth` | Authentisierungsversuche betrachten. | Fragestellung entscheidet über den Bericht. |
| `--failed` | Fehlgeschlagene Ereignisse auswählen. | Auswahl kann erfolgreiche Folgeaktionen ausblenden. |
| `--success` | Erfolgreiche Ereignisse auswählen. | Erfolg bedeutet nicht automatisch Berechtigung im fachlichen Sinn. |
| `--summary` | Unterstützte Berichte zusammenfassen. | Nicht für jeden Bericht verfügbar. |
| `--interpret` | Numerische Angaben lesbarer auflösen. | Lokale Kontenzuordnung kann von der Herkunft abweichen. |
| `--start`, `--end` | Zeitfenster begrenzen. | Datumssyntax und Zeitzone dokumentieren. |

Für die Hilfe `--help` verwenden. `-h` bezeichnet bei `aureport` den Hostbericht und ist hier gerade kein verlässlicher kurzer Hilfsschalter.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Eingabe ausdrücklich auswählen

Für die Planung heiße eine bereits autorisiert bereitgestellte Rohkopie `./analyse/audit-kopie.log`. Diese Datei wird hier weder angelegt noch vom System kopiert. Vor einer echten Analyse müssen Herkunft, Zeitraum und Leserecht geklärt sein.

### Schritt 2: Nur den Bericht anfordern

```bash
aureport --input './analyse/audit-kopie.log' --login --summary
```

Das wäre eine Offlineauswertung der benannten Datei. Der Aufruf wurde nicht ausgeführt, weil `aureport` lokal nicht installiert ist. Es gibt daher keine gemessene Beispielausgabe.

### Schritt 3: Verdichtung angemessen lesen

Ein fiktiver Bericht könnte mehrere Anmeldungen für eine Kennung zusammenfassen. Damit ist zunächst eine Häufigkeit innerhalb der Eingabe beschrieben. Für Ursache, Herkunft und Zusammenhang wären anschließend die einzelnen Ereignisse erforderlich.

### Schritt 4: Auffälligkeiten zurückverfolgen

Ereignisnummern können beim Wechsel zu `ausearch` helfen. Zeitraum und Herkunft gehören dazu, weil eine Nummer ohne ihren Protokollkontext nicht jede Verwechslung verhindert. Ein gekürzter Bericht darf nicht als vollständiger Rohdatenersatz archiviert werden.

## 6. Typische Anwendungsfälle

- Umfang von Anmeldungen in einer freigegebenen Protokollkopie überblicken.
- Fehlgeschlagene Aktionen für eine nachfolgende Einzelfallprüfung eingrenzen.
- Zwei gleichartig erfasste Zeiträume mit dokumentierten Auswahlkriterien vergleichen.
- Eine technische Bestandsaufnahme mit nachvollziehbaren Zahlen ergänzen.

Bei Vergleichen müssen dieselbe Datenabdeckung und dieselben Filter gelten. Eine andere Auditregel oder eine Lücke kann die Zahlen verändern, ohne dass sich das Benutzerverhalten entsprechend geändert hat.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Auswertung ist grundsätzlich lesend, aber ihre Ergebnisse können personenbezogene Angaben enthalten. Berichte und Rohkopien nur am vorgesehenen Ort aufbewahren. Keine vollständigen Anmeldeprotokolle ungeprüft in öffentliche Anfragen einfügen.

`--interpret` macht Kennungen lesbarer, kann bei einer Analyse auf einem anderen Rechner jedoch fremde lokale Namen zuordnen. Numerische Originalwerte erhalten und die Auflösung als Darstellung kennzeichnen.

## 8. Häufige Fehler

- **Kein Bericht:** Format, Zeitraum und tatsächliche Eingabemenge prüfen.
- **Unbekannte Namen:** Kontozuordnung der Analyseumgebung passt möglicherweise nicht zur Herkunft.
- **Datum abgewiesen:** Lokale Datumsdarstellung beachten; nicht Tag und Monat vertauschen.
- **Zahl unerwartet klein:** Filter oder unvollständige Daten könnten Ereignisse ausschließen.
- **Hilfe zeigt etwas anderes:** `--help` verwenden, nicht den Hostschalter `-h`.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer freigegebenen Kopie und einem einfachen Bericht beginnen. Den genauen Aufruf, die Eingabe und den Zeitraum notieren. Erst danach weitere Filter ergänzen, damit ihre Auswirkung sichtbar bleibt.

Keine Befehle aus Berichtsfeldern ausführen. Ein Protokoll beschreibt möglicherweise fremde Eingaben; sein Text ist keine vertrauenswürdige Anleitung für die Shell.

## 10. Verwandte Befehle

- `ausearch`: Ereignisse gezielt im Zusammenhang betrachten.
- `auditctl`: Erfassungsregeln verwalten; andere Wirkung als die Auswertung.
- `auditd`: Auditdaten speichern.
- `journalctl`: Journal nach passenden Zusatzinformationen durchsuchen.

**Prüfstand:** Dokumentation geprüft, keine lokale Ausführung und keine Einsicht in echte Benutzer- oder Systemprotokolle.

Ausgangsdatensatz 308 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
