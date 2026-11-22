---
id: "rkhunter"
name: "rkhunter"
command: "rkhunter"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "caution"
tags: ["rkhunter", "firewall & sicherheit"]
status: "Handbuch und Paketmetadaten geprüft; kein Prüflauf und keine Referenzaktualisierung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 322
reviewed_at: "2026-11-13"
locally_checked_version: "Paket rkhunter 1.4.6-12; lokale Manpage gelesen"
---

# rkhunter – Integritäts- und Rootkit-Hinweise mit Kontext bewerten

## 1. Kurzbeschreibung

`rkhunter` prüft bekannte verdächtige Merkmale und bestimmte Dateieigenschaften. Es kann auf Veränderungen hinweisen, erklärt aber nicht automatisch deren Ursache. Eine Warnung ist noch kein bestätigter Angriff.

**Für die vollständige Systemprüfung sind administrative Rechte üblich und für geschützte Bereiche erforderlich.** Die reine Hilfe braucht keine Root-Prüfung des Systems. Für diese Dokumentation wurde kein Scan gestartet.

## 2. Was macht der Befehl?

Das Werkzeug verbindet mehrere Prüfarten. Unter anderem können aktuelle Eigenschaften mit gespeicherten Referenzwerten verglichen werden. Eine solche Referenz muss aus einem begründet vertrauenswürdigen Zustand stammen.

Die [mit dem Paket veröffentlichte Manpage](https://manpages.debian.org/trixie/rkhunter/rkhunter.8.en.html) und die lokale Manpage beschreiben Aktionen und Grenzen. Die lokalen Paketmetadaten nennen `1.4.6-12`.

Eine Veränderung nach einem legitimen Paketupdate ist eine mögliche Erklärung für eine Warnung. Sie muss anhand passender Paket- und Dateiinformationen geprüft werden. Ebenso wenig darf jede Abweichung pauschal mit einem Update erklärt werden.

## 3. Syntax

```text
rkhunter --help
rkhunter --version
rkhunter --check [OPTIONEN]
rkhunter --config-check
```

`--check` startet Untersuchungen und erzeugt normalerweise ein Protokoll. `--config-check` betrachtet Konfiguration, ist aber keine vollständige Prüfung der Dateiintegrität.

## 4. Wichtige Optionen

| Form | Zweck | Wichtige Grenze |
| --- | --- | --- |
| `--help` | Bedienung anzeigen. | Noch kein Systemscan. |
| `--version` | Installierte Programmversion anzeigen. | Kein Netzwerkvergleich. |
| `--list tests` | Verfügbare Tests nennen. | Keine Durchführung dieser Tests. |
| `--check` | Systemprüfungen durchführen. | Kann Logs und temporäre Daten schreiben. |
| `--config-check` | Konfiguration auf Probleme prüfen. | Kein allgemeiner Sauberkeitsnachweis. |
| `--skip-keypress` | Warteaufforderungen auslassen. | Umfang dadurch nicht automatisch reduziert. |
| `--report-warnings-only` | Bildschirmausgabe auf Warnungen begrenzen. | Fehler und Vollprotokoll bleiben wichtig. |
| `--update` | Textdaten aktualisieren. | Netzwerk- und Schreibvorgang. |
| `--propupd` | Dateieigenschaften als neue Referenz speichern. | Kein Reparatur- oder Verifikationsbefehl. |

`--versioncheck` fragt nach einer neueren Programmversion. Es ist nicht dasselbe wie die rein lokale Anzeige mit `--version`.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Warnung präzise beschreiben

Angenommen, ein späterer Bericht meldet geänderte Eigenschaften eines Programms. Zuerst Pfad, genaue Meldung, Zeitpunkt und Referenzkontext festhalten. Dieses Beispiel bezieht sich auf keine tatsächlich untersuchte Datei des Rechners.

### Schritt 2: Eine mögliche Erklärung überprüfen

War ein passendes Paketupdate erfolgt, wäre die Datei mit verlässlichen Paketinformationen abzugleichen. Zeitliche Nähe allein reicht nicht: Auch der konkrete Inhalt beziehungsweise die nachvollziehbare Herkunft muss passen.

### Schritt 3: Nicht durch Referenzübernahme „reparieren“

`rkhunter --propupd` würde aktuelle Eigenschaften zur Referenz machen. Damit kann eine noch ungeklärte Veränderung künftig weniger auffallen. Die Aktion beweist nicht, dass die Datei unverändert, original oder sicher ist.

### Schritt 4: Ergebnisgrenzen notieren

Ein sinnvoller Vermerk unterscheidet bestätigte legitime Änderung, weiterhin ungeklärte Abweichung und fehlgeschlagene Prüfung. Diese Zustände dürfen nicht in ein gemeinsames grünes Ergebnis zusammenfallen.

Es wurde hier weder ein Prüflauf noch ein Update oder eine Referenzübernahme ausgeführt. Die lokale Version stammt aus Paketmetadaten.

## 6. Typische Anwendungsfälle

- Eine bekannte Systemänderung mit Integritätshinweisen abgleichen.
- Wiederkehrende Beobachtungen unter dokumentierten Bedingungen vergleichen.
- Einen einzelnen Hinweis als Ausgangspunkt für gezielte weitere Prüfung verwenden.
- Eine Konfigurationsstörung von einem tatsächlichen Fund unterscheiden.

Ein fehlgeschlagener Test kann von fehlenden Hilfsprogrammen oder Zugriffsrechten kommen. Er liefert nicht dieselbe Aussage wie ein abgeschlossener Test ohne Auffälligkeit.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Lauf kann sensible Systemdetails lesen und speichern. Logs vor Weitergabe auf private oder betriebliche Angaben prüfen. Temporäre Dateien und Berichtspfade gehören ebenfalls zum Prüfkontext.

Die größte fachliche Gefahr ist eine ungeprüfte Normalisierung: Warnungen ausblenden oder aktuelle Werte übernehmen, bevor deren Herkunft geklärt ist. So kann eine unklare Abweichung aus der Aufmerksamkeit verschwinden, ohne behoben zu sein.

Umgekehrt keine regulären Entwicklungs-, Paket- oder Systemabläufe allein wegen eines unbekannten Namens als Angriff bezeichnen. Dafür braucht es passende zusätzliche Belege.

## 8. Häufige Fehler

- **Warnung gleich Infektion:** Ursache und Gegenbelege fehlen.
- **Fehler gleich sauber:** Ein abgebrochener Test hat keine solche Aussage.
- **`--propupd` gleich Reparatur:** Es aktualisiert Vergleichswerte.
- **Jedes Update als Entwarnung:** Konkreten Datei- und Paketbezug prüfen.
- **Nur reduzierte Anzeige lesen:** Kontext aus dem Protokoll kann fehlen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Handbuch und einer einzelnen konkreten Meldung beginnen. Referenzwerte nicht automatisch nach jedem unbekannten Ereignis ersetzen. Eine begründete Baselineaktualisierung ist ein eigener Verwaltungsauftrag.

Bei wiederholten Läufen Version, Rechte, Konfiguration und ausgeschlossene Tests notieren. Nur so lässt sich erklären, ob ein Unterschied vom System oder vom Prüfumfang stammt.

## 10. Verwandte Befehle

- `chkrootkit`: Andere bekannte verdächtige Merkmale untersuchen.
- `lynis`: Härtungs- und Konfigurationshinweise sammeln.
- `dpkg --verify`: Paketbezogene Abweichungen betrachten.
- `sha256sum`: Dateiinhalt mit einer verlässlichen Referenz vergleichen.

**Prüfstand:** Handbuch und Paketmetadaten geprüft. Kein Systemscan, Datenupdate, Referenzwechsel oder Eingriff in eine bestehende Untersuchung vorgenommen.

Ausgangsdatensatz 322 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
