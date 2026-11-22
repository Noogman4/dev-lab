---
id: "clamdscan"
name: "clamdscan"
command: "clamdscan"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["clamdscan", "firewall & sicherheit"]
status: "Herstellerdokumentation und Manpage geprüft; kein Scan ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 311
reviewed_at: "2026-11-13"
locally_checked_version: "Client nicht installiert; kein Dienstkontakt"
---

# clamdscan – Dateien über einen laufenden ClamAV-Dienst prüfen

## 1. Kurzbeschreibung

`clamdscan` ist ein Client für den Virenscanner-Dienst `clamd`. Der Client erteilt den Prüfauftrag; die eigentliche Analyse erfolgt im Dienst. Anders als `clamscan` lädt er nicht für jeden Aufruf selbst die gesamte Scanumgebung.

**Root-Rechte sind nicht grundsätzlich nötig.** Entscheidend sind der Zugriff auf den Dienst und die benötigten Dateileserechte. Dienst und Client können unter verschiedenen Benutzerkonten laufen.

## 2. Was macht der Befehl?

Der Client übermittelt Pfade, Dateideskriptoren oder Dateiinhalte an `clamd`. Welche Variante passt, hängt vom Socket und der Konfiguration ab. Die [ClamAV-Scandokumentation](https://docs.clamav.net/manual/Usage/Scanning.html) erklärt diese Wege. Die [Debian-Manpage](https://manpages.debian.org/trixie/clamdscan/clamdscan.1.en.html) beschreibt die Clientoptionen.

Die Grenzen der Dienstkonfiguration gelten weiter. Eine akzeptierte Option aus einer `clamscan`-Anleitung bedeutet nicht, dass der Client damit das Scanverhalten des Dienstes umstellt. Für reproduzierbare Ergebnisse müssen deshalb auch Dienst und Signaturstand bekannt sein.

## 3. Syntax

```text
clamdscan [OPTIONEN] DATEI_ODER_VERZEICHNIS
clamdscan --help
clamdscan --fdpass DATEI
```

Ein Verzeichnisauftrag kann sehr viele Dateien betreffen. Den Zielpfad ausdrücklich wählen. Der Aufruf ohne Pfad kann das aktuelle Verzeichnis prüfen und ist kein Hilfsaufruf.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `--help` | Bedienung erklären. | Keine Prüfung von Dateien. |
| `--config-file=DATEI` | Client mit bestimmter Dienstkonfiguration verwenden. | Damit wird kein eigener Scanner gestartet. |
| `--fdpass` | Geöffnete Dateien übergeben. | Nur bei geeignetem lokalem Unix-Socket. |
| `--stream` | Dateiinhalte übertragen. | Ziel und Vertraulichkeit beachten. |
| `--multiscan` | Verzeichnisprüfung parallelisieren lassen. | Mehr Last; kein anderer Erkennungsnachweis. |
| `--infected` | Ausgabe auf Funde beschränken. | Fehler und Zusammenfassung weiter beachten. |
| `--log=DATEI` | Bericht speichern. | Schreibt die Berichtsdatei. |
| `--remove` | Gefundene Dateien entfernen. | Destruktive Folgeaktion, hier nicht verwenden. |

Auch `--move` und `--copy` erzeugen Folgeaktionen an Dateien. Sie gehören nicht in einen unbesehen übernommenen Einstiegsaufruf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine eigene Datei auswählen

Angenommen, die eigene Datei heißt `./pruefung/notiz.txt` und der lokale Dienst ist bereits eingerichtet. Es wird hier kein Dienst installiert, gestartet oder verändert.

### Schritt 2: Den Zugriffsweg festlegen

```bash
clamdscan --fdpass './pruefung/notiz.txt'
```

Der geplante Aufruf lässt den Client die Datei öffnen und über einen passenden Unix-Socket übergeben. Er wurde nicht ausgeführt: `clamdscan` ist lokal nicht installiert. Eine reale Verbindung zum Dienst wurde für diese Dokumentation nicht aufgebaut.

### Schritt 3: Ergebnis und Status gemeinsam lesen

Die Manpage unterscheidet Status `0` ohne Fund, `1` mit Fund und `2` bei Fehler. Ein Verbindungs- oder Lesefehler ist kein sauberes Scanergebnis. Auch bei Status `0` bleiben die Grenzen von Signaturen, Konfiguration und untersuchtem Inhalt bestehen.

### Schritt 4: Umfang festhalten

Für einen späteren Bericht den genauen Pfad, Zeitpunkt und Dienstkontext notieren. Ein erfolgreicher Auftrag für eine einzelne Datei ist keine Prüfung des gesamten Downloads-Verzeichnisses.

## 6. Typische Anwendungsfälle

- Mehrere ausdrücklich ausgewählte Dateien mit einem bereits laufenden Dienst prüfen.
- Wiederholte Aufträge ohne erneutes Laden der gesamten Datenbank durch den Client senden.
- Eine Datei trotz unterschiedlicher Benutzerkonten kontrolliert über einen lokalen Deskriptor übergeben.

Ein entfernter Dienst ist eine zusätzliche Datenverarbeitung auf einem anderen Rechner. Vor Übertragung persönlicher Dokumente muss dieser Weg gewollt und bekannt sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der normale Scan liest Dateien und beansprucht Ressourcen. Lösch- oder Verschiebeoptionen können dagegen Daten verändern oder entfernen, auch bei einem später bestätigten Fehlalarm.

ClamAV beschreibt den TCP-Dienstzugang als nicht selbst authentifiziert und geschützt. Einen solchen Socket nicht öffentlich zugänglich machen. Das Abschalten einer Firewall löst keine geeignete Dienstkonfiguration.

Dateinamen können ungewöhnliche Zeichen enthalten. Textzeilen mit einem Fundsuffix nicht ungeprüft als verlässliche Dateianweisung für automatische Maßnahmen verwenden. Auswertung und gezielter Dateizugriff brauchen eine belastbare Zuordnung.

## 8. Häufige Fehler

- **Verbindung abgelehnt:** Dienst, Socket und Rechte prüfen; kein Virenbefund.
- **Datei nicht lesbar:** Dienstsicht und Clientsicht sind möglicherweise verschieden.
- **`--fdpass` funktioniert nicht:** TCP unterstützt diesen Weg nicht.
- **Scanoption ohne Wirkung:** Die zuständige Einstellung liegt womöglich beim Dienst.
- **Nur Fundzeilen ausgewertet:** Fehlerstatus und ausgelassene Inhalte fehlen als Kontext.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer einzelnen eigenen Datei beginnen und Löschaktionen weglassen. Erst wenn Verbindung, Leserecht und Bericht nachvollziehbar sind, den Umfang erweitern.

Keine privaten Dateien probeweise an einen unbekannten TCP-Scanner schicken. Für einen einmaligen lokalen Scan ohne eingerichteten Dienst ist `clamscan` die andere Betriebsart; seine Optionen sind separat zu verstehen.

## 10. Verwandte Befehle

- `clamd`: Führt die Analyse als Dienst aus.
- `clamscan`: Eigenständiger Scanprozess.
- `freshclam`: Aktualisiert Signaturdaten; eigener Netzwerk- und Schreibvorgang.
- `clamconf`: Zeigt Konfigurationsinformationen, soweit installiert.

**Prüfstand:** Dokumentationsprüfung. Kein Dienststart, kein Socketkontakt, kein Scan und keine Dateiaktion durchgeführt.

Ausgangsdatensatz 311 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
