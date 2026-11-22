---
id: "lynis"
name: "lynis"
command: "lynis"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["lynis", "firewall & sicherheit"]
status: "Herstelleranleitung und lokale Manpage geprüft; kein Systemaudit gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 320
reviewed_at: "2026-11-13"
locally_checked_version: "Paket lynis 3.0.9-1; lokale Manpage gelesen"
---

# lynis – Systemhärtung nachvollziehbar untersuchen

## 1. Kurzbeschreibung

`lynis` untersucht Systemeinstellungen und erstellt Hinweise zur Härtung. Es ist ein Auditwerkzeug, kein automatischer Beweis für eine sichere oder kompromittierte Maschine. Vorschläge müssen zum Einsatzzweck passen.

**Ein nicht privilegierter Lauf ist möglich; Root ist nicht grundsätzlich erforderlich.** Einige Prüfungen liefern erst mit zusätzlichen Leserechten mehr Informationen. Ein eingeschränkter Lauf muss als solcher dokumentiert werden.

## 2. Was macht der Befehl?

Ein Audit betrachtet verschiedene Bereiche wie Dienste, Konfiguration, Pakete und Protokollierung. Ergebnisse werden auf dem Bildschirm und in Berichtsdateien ausgegeben. Damit ist ein Lauf trotz überwiegend beobachtender Prüfungen nicht vollständig schreibfrei.

Die [Herstelleranleitung von CISOfy](https://cisofy.com/documentation/lynis/) erläutert Befehle, Profile und die Bewertung von Meldungen. Zusätzlich wurde die installierte Manpage gelesen; die Paketmetadaten nennen Version `3.0.9-1`.

Eine Warnung ist ein Prüfauftrag. Ob tatsächlich eine Änderung sinnvoll ist, ergibt sich aus Rolle, Anforderungen und vorhandenen Gegenmaßnahmen. Eine Desktopmaschine hat beispielsweise andere Anforderungen als ein öffentlich erreichbarer Server.

## 3. Syntax

```text
lynis show help
lynis show version
lynis audit system [OPTIONEN]
```

`audit system` startet die eigentliche Untersuchung. Eine Anweisung zur Anzeige der Hilfe ist davon getrennt. Der Systemaudit wurde hier nicht ausgeführt.

## 4. Wichtige Optionen

| Form | Wirkung | Grenze |
| --- | --- | --- |
| `show help` | Bedienung und Hinweise anzeigen. | Keine vollständige Systemprüfung. |
| `show version` | Version anzeigen. | Paketstand und Aktualität getrennt beurteilen. |
| `audit system` | Systemaudit starten. | Führt Tests aus und kann Berichte schreiben. |
| `--profile DATEI` | Prüfprofil auswählen. | Nur bekannte Profile verwenden. |
| `--tests TEST-IDs` | Bestimmte Tests auswählen. | Rest bleibt außerhalb dieses Laufs. |
| `--quick` | Interaktive Wartepausen reduzieren. | Nicht automatisch weniger Prüfungen. |
| `--logfile DATEI` | Protokollziel festlegen. | Schreibt potenziell vertrauliche Details. |
| `--report-file DATEI` | Berichtsdatei auswählen. | Bestehende Ergebnisse nicht unbedacht ersetzen. |
| `--no-plugins` | Aktivierte Plugins auslassen. | Umfang dadurch verändert. |

Uploadoptionen sind zusätzliche Datenübertragungen. Sie werden hier weder vorausgesetzt noch benutzt. Ein Systemaudit darf nicht unbemerkt zu einer Veröffentlichung von Systeminformationen werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen begrenzten Auftrag planen

Fragestellung: „Welche Härtungshinweise sind für meine bewusst ausgewählte Systemrolle relevant?“ Zunächst Version, Prüfprofil und gewünschte Berichtsablage festlegen.

### Schritt 2: Einen möglichen Lauf verstehen

```text
lynis audit system --profile EIGENES_PROFIL --logfile EIGENES_LOG --report-file EIGENER_BERICHT
```

Das ist eine Planungsschablone, kein fertig ausgeführter Befehl. Die großgeschriebenen Angaben müssen durch geprüfte, eigene Pfade ersetzt werden. Es wurde kein Profil verändert und kein Audit gestartet.

### Schritt 3: Eine fiktive Empfehlung bewerten

Angenommen, ein Bericht empfiehlt eine andere Dienstkonfiguration. Zuerst Testkennung und Begründung lesen. Dann prüfen, ob der Dienst tatsächlich genutzt wird und welche Funktion eine Änderung beeinträchtigen würde.

Die sinnvolle Dokumentation lautet etwa: „Hinweis aufgenommen, auf diese Systemrolle geprüft, Änderung aus folgendem Grund vorgesehen oder verworfen.“ Ein bloßes Wegklicken einer Warnung ist keine fachliche Bewertung.

### Schritt 4: Vergleichbarkeit erhalten

Für einen späteren Vergleich Werkzeugversion, Profil, Rechte und ausgewählte Tests notieren. Ein umfangreicherer zweiter Lauf kann mehr Meldungen erzeugen, ohne dass das System unsicherer geworden ist.

## 6. Typische Anwendungsfälle

- Eine nachvollziehbare Härtungsbestandsaufnahme vorbereiten.
- Änderungen an einer definierten Systemrolle dokumentieren.
- Einzelne Empfehlungen mit betrieblichen Anforderungen abgleichen.
- Wiederholte Audits unter vergleichbaren Bedingungen gegenüberstellen.

Ein zusammengefasster Index kann die Orientierung erleichtern. Er ist aber kein universell vergleichbarer Sicherheitswert für völlig unterschiedliche Maschinen und Profile.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Lauf liest viele Systeminformationen, startet Prüfungen und kann Ressourcen sowie temporären Speicher benötigen. Berichte können sensible Pfade, Konfigurationen und Kennungen enthalten. Speicherort und Weitergabe bewusst wählen.

Plugins und fremde Profile gehören zur Vertrauensgrenze. Sie nicht ungeprüft privilegiert verwenden. Die Absicht „nur prüfen“ macht beliebige Erweiterungen nicht automatisch harmlos.

Empfohlene Änderungen können Funktion, Erreichbarkeit oder Wartbarkeit beeinflussen. Keine Liste pauschal abarbeiten, nur um einen besseren Zahlenwert zu erreichen.

## 8. Häufige Fehler

- **`--quick` als oberflächlichen Kurztest lesen:** Der Schalter betrifft Warteverhalten, nicht automatisch Testumfang.
- **Mehr Warnungen als Verschlechterung werten:** Version, Profil und Rechte vergleichen.
- **Unprivilegiert übersprungene Tests vergessen:** Grenzen im Bericht benennen.
- **Jeden Vorschlag sofort anwenden:** Systemrolle und Nebenwirkungen fehlen noch.
- **Berichte öffentlich anhängen:** Erst vertrauliche Inhalte prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe, Handbuch und klarer Fragestellung beginnen. Einen Audit getrennt von seinen möglichen Folgemaßnahmen planen. Die ursprüngliche Ausgabe erhalten und eigene Bewertungen als solche kennzeichnen.

Für einzelne Hinweise zuerst die passende offizielle Dokumentation des betroffenen Dienstes nutzen. Eine allgemeine Empfehlung ersetzt dessen konkrete Funktionsanforderungen nicht.

## 10. Verwandte Befehle

- `rkhunter`: Andere Integritäts- und Rootkit-Hinweise.
- `chkrootkit`: Suche nach bekannten verdächtigen Merkmalen.
- `systemctl`: Dienstzustände und Verwaltung; Aufrufwirkung unterscheiden.
- `journalctl`: Passende Meldungen lesen.
- `dpkg --verify`: Paketbezogene Dateiabweichungen betrachten.

**Prüfstand:** Herstelleranleitung, lokale Manpage und Paketmetadaten geprüft. Kein Systemaudit, Upload, Pluginlauf oder Härtungseingriff ausgeführt.

Ausgangsdatensatz 320 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
