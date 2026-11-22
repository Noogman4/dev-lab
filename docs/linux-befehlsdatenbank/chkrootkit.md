---
id: "chkrootkit"
name: "chkrootkit"
command: "chkrootkit"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "caution"
tags: ["chkrootkit", "firewall & sicherheit"]
status: "README und Hersteller-FAQ geprüft; kein Systemscan"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 310
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# chkrootkit – Hinweise auf bekannte Rootkit-Muster untersuchen

## 1. Kurzbeschreibung

`chkrootkit` untersucht ein System auf Hinweise bekannter Rootkit-Veränderungen. Es ist ein Hinweisgeber, kein Beweisautomat für eine Infektion und kein Werkzeug zur automatischen Bereinigung.

**Für die eigentliche Systemprüfung sieht das Projekt Root-Rechte vor.** Hilfe und Versionsinformation benötigen keine privilegierte Vollprüfung. Auf dem lokalen Rechner ist das Werkzeug nicht installiert; es wurde kein Scan gestartet.

## 2. Was macht der Befehl?

Verschiedene Tests suchen beispielsweise nach auffälligen Merkmalen in Programmen oder nach Widersprüchen zwischen Prozessansichten. Welche Tests sinnvoll sind, hängt von System und Werkzeugversion ab.

Die [Projekt-README](https://www.chkrootkit.org/README) beschreibt Aufruf und Testauswahl. Die [offizielle FAQ](https://www.chkrootkit.org/faq/) erklärt wichtige Grenzen und Fehlalarme. Die FAQ enthält ältere Beispiele; konkrete Namen und Optionen daher mit der lokal installierten Fassung abgleichen.

Eine Untersuchung auf dem möglicherweise kompromittierten Rechner hängt von dessen sichtbarem Zustand ab. Wird dieser Zustand manipuliert, kann auch das Ergebnis unvollständig sein. Ein unauffälliger Lauf beantwortet deshalb nicht jede Sicherheitsfrage.

## 3. Syntax

```text
chkrootkit [OPTIONEN] [TESTNAME ...]
chkrootkit -h
chkrootkit -l
```

Ohne Testnamen wird die gesamte vorgesehene Testauswahl gestartet. Ein leerer Aufruf ist also kein harmloser Ersatz für Hilfe. Der Katalogplatzhalter `--help` wird hier durch den dokumentierten Schalter `-h` präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Praxisbezug |
| --- | --- | --- |
| `-h` | Hilfe anzeigen. | Zuerst Bedienung prüfen. |
| `-V` | Version ausgeben. | Großes V beachten. |
| `-l` | Testnamen auflisten. | Noch keine vollständige Untersuchung. |
| `-q` | Ausgabe auf bestimmte Befundmeldungen reduzieren. | Weniger Kontext ist nicht mehr Gewissheit. |
| `-x` | Expertenansicht bereitstellen. | Bewertung bleibt beim Untersuchenden. |
| `-r VERZEICHNIS` | Andere Untersuchungswurzel wählen. | Kein Mount und keine automatische Isolation. |
| `-p PFADLISTE` | Suchpfade externer Hilfsprogramme festlegen. | Nur tatsächlich vertrauenswürdige Programme verwenden. |
| `-n` | NFS-Verzeichnisse überspringen. | Dann ist dieser Bereich nicht untersucht. |

Eine vom Benutzer beschreibbare Programmsammlung ist keine geeignete vertrauenswürdige Hilfsbasis für einen privilegierten Prüflauf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Den Untersuchungsumfang planen

Fragestellung: „Welche Tests bietet meine installierte Fassung?“ Dafür ist noch kein Vollscan erforderlich. Ein geplanter Einstieg wäre:

```bash
chkrootkit -h
chkrootkit -l
```

Beide Aufrufe wurden hier nicht ausgeführt, weil das Werkzeug fehlt. Die Beispiele sind anhand der Projektbeschreibung dokumentiert.

### Schritt 2: Einen fiktiven Hinweis untersuchen

Angenommen, ein späterer Bericht nennt eine auffällige Prozessabweichung. Zuerst Zeitpunkt und genaue Testbezeichnung sichern. Anschließend prüfen, ob kurzlebige Prozesse während zweier aufeinanderfolgender Ansichten entstanden oder beendet wurden.

Eine zeitlich bedingte Differenz wäre eine mögliche Erklärung, kein automatisch bewiesener Fehlalarm. Ebenso ist die Meldung allein noch kein Nachweis eines versteckten Angreiferprozesses.

### Schritt 3: Belege vor Maßnahmen ergänzen

Die betroffene Datei oder der Prozess braucht eine nachvollziehbare Herkunft und passende Zusatzbelege. Ein ungewöhnlicher Dateiname allein rechtfertigt keine Löschung. Bei begründetem Verdacht ist eine geplante Untersuchung aus vertrauenswürdiger Umgebung sinnvoller als hektisches Verändern des laufenden Systems.

## 6. Typische Anwendungsfälle

- Einen bestehenden Sicherheitsverdacht um zusätzliche Hinweise ergänzen.
- Bekannte Tests nach einem klar beschriebenen Untersuchungsplan durchführen.
- Einen Bericht mit Paketinformationen und unabhängigen Beobachtungen abgleichen.
- Eine ausdrücklich bereitgestellte Untersuchungswurzel bewerten.

Ein wiederkehrender Scan ist erst dann hilfreich, wenn Meldungen mit Kontext ausgewertet werden. Eine ungeprüfte tägliche Warnungsmenge kann relevante Veränderungen ebenso verdecken wie ein pauschales Ausblenden sämtlicher Meldungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Scans können Ressourcen und sensible Systeminformationen beanspruchen. Ein Bericht kann private Pfade oder Prozessdetails enthalten. Eine Anzeige in einem Sicherheitswerkzeug ist kein Grund, den gesamten Bericht öffentlich weiterzugeben.

Unbekannte Varianten können ohne bekannten Suchhinweis bleiben. Umgekehrt können legitime Dateien, Programme oder zeitliche Änderungen auffällig wirken. Beides begrenzt die Schlussfolgerung.

Keine automatisch nachgeschaltete Löschung, Quarantäne oder Neuinstallation aus einzelnen Texttreffern ableiten. Solche Maßnahmen benötigen eine eigene Begründung und können wichtige Daten oder Untersuchungsbelege verändern.

## 8. Häufige Fehler

- **„INFECTED“ sofort als Abschlussdiagnose lesen:** Test und zusätzliche Belege fehlen noch.
- **Kein Hinweis, also garantiert sauber:** Erkennungsumfang bleibt begrenzt.
- **Expertenausgabe missverstehen:** Verdächtige Zeichenfolgen müssen fachlich eingeordnet werden.
- **Fremde Programme als Root starten:** Vertrauenskette der Hilfsprogramme ist ungeklärt.
- **Andere Wurzel mit Isolation verwechseln:** `-r` erzeugt keine sichere Analyseumgebung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Hilfe, Version und Testauswahl kennenlernen. Einen einzelnen Befund mit vollständiger Meldung und Zeitpunkt beschreiben. Keine unbekannten Dateien nur zur Befriedigung einer Warnung löschen.

Bei Abweichungen zwischen zwei Läufen außerdem Werkzeugversion, Rechte und Systemzustand vergleichen. Eine veränderte Ausgabe kann auf einen anderen Prüfkontext zurückgehen.

## 10. Verwandte Befehle

- `rkhunter`: Anderer Satz von Integritäts- und Rootkit-Hinweisen.
- `dpkg --verify`: Paketbezogene Abweichungen untersuchen; distributionsabhängig.
- `ps`: Sichtbare Prozesse anzeigen.
- `clamscan`: Dateien mit einer anderen Erkennungsmethode untersuchen.

**Prüfstand:** Herstellerquellen gelesen. Kein Systemscan, keine Dateiänderung und keine automatische Bewertung des tatsächlichen Rechners vorgenommen.

Ausgangsdatensatz 310 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
