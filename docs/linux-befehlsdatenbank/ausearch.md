---
id: "ausearch"
name: "ausearch"
command: "ausearch"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["ausearch", "firewall & sicherheit"]
status: "Upstream-Handbuch geprüft; keine echten Auditdaten gelesen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 309
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# ausearch – zusammengehörige Linux-Auditereignisse gezielt suchen

## 1. Kurzbeschreibung

`ausearch` sucht in Linux-Auditprotokollen nach Ereignissen. Anders als ein einfacher Textfilter berücksichtigt es, dass mehrere Datensätze zu derselben Aktion gehören können. Es ändert keine Erfassungsregeln.

**Für eigene lesbare Protokollkopien sind keine Root-Rechte nötig.** Die Originalprotokolle können administrative Leserechte verlangen. Das Werkzeug soll nicht dazu verleiten, ihre Berechtigungen zu lockern.

## 2. Was macht der Befehl?

Ein Auditereignis kann Angaben zum Systemaufruf, Pfad und weiteren Umständen enthalten. Diese Einzelzeilen sind erst gemeinsam sinnvoll auszuwerten. Ein bloßer Treffer auf einen Dateinamen zeigt möglicherweise nur einen Teil des Zusammenhangs.

Das [ausearch-Upstream-Handbuch](https://man7.org/linux/man-pages/man8/ausearch.8.html) erläutert Ereigniszusammenführung, Suchkriterien und Ausgabeformate. Die [Projektübersicht von Linux Audit](https://github.com/linux-audit/audit-userspace) beschreibt die Herkunft dieser Daten.

Eine Suche beantwortet nur Fragen, für die die Eingabe genügend Informationen enthält. Nicht aufgezeichnete oder verlorene Ereignisse lassen sich nicht nachträglich aus einem passenden Suchschalter rekonstruieren.

## 3. Syntax

```text
ausearch [OPTIONEN]
ausearch --help
ausearch --input DATEI --event NUMMER
```

`DATEI` bezeichnet eine vorhandene Audit-Rohkopie. `NUMMER` ist die Ereigniskennung, nicht die Prozessnummer. In einem Ausdruck wie `audit(zeitstempel:nummer)` steht sie hinter dem Doppelpunkt.

## 4. Wichtige Optionen

| Option | Bedeutung | Abgrenzung |
| --- | --- | --- |
| `--input DATEI` | Bestimmte Rohdaten lesen. | Nicht mit Dateinamenfilter verwechseln. |
| `--event NUMMER` | Ereigniskennung auswählen. | Zeit und Herkunft mitberücksichtigen. |
| `--file PFAD` | Nach betroffenem Pfad suchen. | Wählt Inhalt, nicht Eingabedatei. |
| `--key SCHLÜSSEL` | Nach Audit-Regelschlüssel suchen. | Nur sinnvoll, wenn solche Schlüssel erfasst wurden. |
| `--message TYP` | Ereignisse mit bestimmtem Datensatztyp suchen. | Zusammengehörige weitere Datensätze können mit erscheinen. |
| `--pid NUMMER` | Prozesskennung auswählen. | PIDs werden mit der Zeit wiederverwendet. |
| `--interpret` | Werte lesbarer auflösen. | Zuordnung kann von der Analyseumgebung abhängen. |
| `--raw` | Rohformat ausgeben. | Für weitere Auditwerkzeuge geeignet. |
| `--start`, `--end` | Zeitraum eingrenzen. | Datumsformat und Zeitzone beachten. |

`--checkpoint DATEI` verwaltet einen Fortschrittsstand und schreibt diese Datei. Es ist daher kein notwendiger Bestandteil einer einmaligen rein lesenden Suche.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine begrenzte Frage festlegen

Angenommen, ein freigegebener Bericht verweist für eine bestimmte Protokollkopie auf Ereignis `1234`. Ziel ist, dessen zusammengehörige Datensätze zu betrachten. Diese Nummer ist hier frei erfunden.

### Schritt 2: Die Rohkopie ausdrücklich angeben

```bash
ausearch --input './analyse/audit-kopie.log' --event 1234
```

Dieser Aufruf wurde nicht ausgeführt: Werkzeug und Beispieldatei sind für diese Dokumentation nicht vorhanden. Die Form zeigt, wie Eingabe und Ereignisauswahl getrennt angegeben werden.

### Schritt 3: Zusammengehörige Angaben lesen

Ein fiktives Ergebnis könnte einen Systemaufruf und einen Pfaddatensatz enthalten. Erst zusammen lässt sich beschreiben, welche Aktion auf welchen Pfad bezogen war. Der Name eines Prozesses allein beweist weder den menschlichen Urheber noch die Absicht.

### Schritt 4: Grenzen der Auswahl dokumentieren

Bei größeren Kopien müsste ein passender Zeitraum hinzukommen, damit gleiche oder wiederverwendete Kennungen nicht falsch verbunden werden. Originaldaten aufbewahren; eine interpretierte Anzeige ist nur eine zusätzliche Lesefassung.

## 6. Typische Anwendungsfälle

- Ein Ereignis hinter einer `aureport`-Zusammenfassung genauer ansehen.
- Zugriffsfehler anhand einer autorisiert bereitgestellten Auditkopie untersuchen.
- Ereignisse eines bewusst benannten Regelschlüssels eingrenzen.
- Rohdaten für einen weiteren Auditbericht auswählen.

Für eine Übergabe die Eingabedatei, Auswahl und Zeitzone benennen. Ein Textausschnitt ohne diesen Kontext kann zu einer anderen Bewertung führen als das vollständige Ereignis.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auditdaten können vertrauliche Pfade, Kennungen und Benutzerhandlungen enthalten. Ausgabe nicht ungeprüft veröffentlichen. Fremde Zeichenfolgen im Protokoll sind Daten und dürfen nicht in auszuführende Shellbefehle verwandelt werden.

Aufgelöste Benutzer- oder Systemaufrufnamen können bei fremder Herkunft vom lokalen System abhängen. Ein lesbarer Name ist deshalb kein Ersatz für numerische Originalwerte und Herkunftsangaben.

Kein Treffer bedeutet zunächst nur: Unter diesen Auswahlbedingungen wurde kein passendes Ereignis ausgegeben. Für eine weitergehende Aussage müssen Erfassungsumfang, Vollständigkeit und mögliche Fehler geklärt sein.

## 8. Häufige Fehler

- **Datei wird nicht gelesen:** `--file` filtert Ereignispfade; die Eingabe gehört zu `--input`.
- **Zu viele Treffer:** Zeitraum und Herkunft genauer bestimmen.
- **Fehlende Zusatzfelder:** Nicht jeder Datensatztyp enthält alle Kriterien.
- **Kennungen passen nicht:** Numerische Werte und Herkunftssystem prüfen.
- **Suchergebnis als Freispruch:** Datenlücken und Auswahlfehler bleiben mögliche Erklärungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst eine Kopie mit klarer Herkunft verwenden. Mit einem einzigen gut begründeten Kriterium beginnen und weitere Filter schrittweise ergänzen. Sonst bleibt unklar, welches Kriterium ein benötigtes Ereignis ausgeblendet hat.

Eine gefundene Fehlermeldung zunächst erklären, bevor Erfassungsregeln oder Schutzprofile verändert werden. Suche und Behebung sind verschiedene Arbeitsschritte.

## 10. Verwandte Befehle

- `aureport`: Häufigkeiten und Kategorien zusammenfassen.
- `auditctl`: Die vorgelagerte Erfassung steuern.
- `auditd`: Ereignisse empfangen und speichern.
- `grep`: Textmuster finden, ohne Auditereignisse automatisch vollständig zusammenzuführen.

**Prüfstand:** Quellen geprüft. Keine echte Protokollsuche, keine Checkpointdatei und keine Änderung am Audit-System ausgeführt.

Ausgangsdatensatz 309 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
