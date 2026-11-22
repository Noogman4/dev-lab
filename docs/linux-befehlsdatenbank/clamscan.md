---
id: "clamscan"
name: "clamscan"
command: "clamscan"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["clamscan", "firewall & sicherheit"]
status: "Lokale Manpage und Hilfe geprüft; Beispielscan nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 312
reviewed_at: "2026-11-13"
locally_checked_version: "ClamAV 1.5.4; Hilfe und Version lokal gelesen"
---

# clamscan – einzelne Dateien und Verzeichnisse mit ClamAV prüfen

## 1. Kurzbeschreibung

`clamscan` prüft Dateien mit der ClamAV-Scanengine und einer Signaturdatenbank. Es arbeitet als eigener Prozess und benötigt dafür keinen laufenden `clamd`-Dienst.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Ein Scan wird nicht genauer, nur weil er als Root läuft. Mehr Rechte erweitern vor allem den möglichen Dateizugriff und die Folgen zusätzlich gewählter Dateiaktionen.

## 2. Was macht der Befehl?

Die Engine liest Inhalte und untersucht unterstützte Dateiformate, gegebenenfalls auch enthaltene Daten. Aufwand und Abdeckung hängen von Format, Grenzwerten und Signaturen ab. Die [offizielle ClamAV-Beschreibung](https://docs.clamav.net/manual/Usage/Scanning.html) unterscheidet den Einmalscan vom Dienstbetrieb.

Lokal wurden `clamscan --help`, `clamscan --version` und die installierte Manpage gelesen. Gemeldet wurde ClamAV `1.5.4`; die Ausgabe enthielt zusätzlich den Datenbankstand. Ein echter Dateiscan wurde dafür nicht gestartet.

Eine Erkennung ist ein technischer Befund, der zur konkreten Datei passen muss. Ein ausbleibender Fund ist keine Garantie, dass eine Datei gefahrlos ausgeführt werden kann.

## 3. Syntax

```text
clamscan [OPTIONEN] DATEI_ODER_VERZEICHNIS
clamscan --help
clamscan --recursive VERZEICHNIS
```

Ohne Dateiangabe wird das aktuelle Verzeichnis betrachtet. `--recursive` ergänzt Unterverzeichnisse. Das aktuelle Arbeitsverzeichnis deshalb vor einem solchen Auftrag bewusst wählen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Folge |
| --- | --- | --- |
| `--help` | Lokale Optionen anzeigen. | Kein Scan. |
| `--version` | Engine- und gegebenenfalls Datenbankstand anzeigen. | Kein Nachweis einer aktuellen Onlineprüfung. |
| `--recursive` | Unterverzeichnisse einbeziehen. | Der Prüfbereich kann stark wachsen. |
| `--infected` | Erfolgszeilen unterdrücken, Funde zeigen. | Fehler und Zusammenfassung mitlesen. |
| `--database=PFAD` | Bestimmte Signaturquelle verwenden. | Nur vertrauenswürdige Datenbanken laden. |
| `--log=DATEI` | Scanbericht schreiben. | Speicherort und Vertraulichkeit beachten. |
| `--cross-fs=no` | Wechsel in andere Dateisysteme begrenzen. | Ausgeschlossene Bereiche bleiben ungeprüft. |
| `--follow-file-symlinks=0` | Dateisymlinks nicht verfolgen. | Verlinkte Ziele werden dadurch nicht geprüft. |
| `--follow-dir-symlinks=0` | Verzeichnissymlinks nicht verfolgen. | Begrenzt den Pfadumfang. |

Größen-, Zeit- und Rekursionsgrenzen schützen vor übermäßigem Ressourcenbedarf. Ihr Erreichen kann zugleich bedeuten, dass nicht jeder enthaltene Bestandteil untersucht wurde.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine eigene, bekannte Datei vorsehen

Als Beispiel diene `./pruefung/notiz.txt`. Es wird keine fremde Datei heruntergeladen und kein Testschadcode angelegt. Der tatsächliche Aufruf bleibt hier ein dokumentierter Vorschlag.

### Schritt 2: Ohne automatische Dateiaktionen prüfen

```bash
clamscan --follow-file-symlinks=0 --follow-dir-symlinks=0 './pruefung/notiz.txt'
```

Die Optionen begrenzen das Folgen von Links. Die Datei selbst bleibt ohne Lösch-, Verschiebe- oder Kopieroption an ihrem Ort. Das Beispiel wurde nicht ausgeführt; lediglich Hilfe und Version wurden tatsächlich abgefragt.

### Schritt 3: Den Rückgabestatus unterscheiden

| Status | Bedeutung | Schlussfolgerung |
| --- | --- | --- |
| `0` | Kein Fund gemeldet. | Abdeckung und Warnungen weiter berücksichtigen. |
| `1` | Mindestens ein Fund. | Datei und Erkennung nachvollziehbar zuordnen. |
| `2` | Fehler aufgetreten. | Nicht als abgeschlossene unauffällige Prüfung behandeln. |

Ein Skript muss diese drei Fälle getrennt behandeln. Nur nach einem Wort in einer Ausgabezeile zu suchen ist dafür nicht ausreichend.

### Schritt 4: Bericht mit Umfang verbinden

Für ein späteres Ergebnis Signaturstand, Zielpfad und verwendete Optionen festhalten. „Kein Fund in einer Textdatei“ darf nicht zu „gesamtes System sauber“ verkürzt werden.

## 6. Typische Anwendungsfälle

- Eine ausdrücklich ausgewählte eigene Datei vor weiterer Verwendung untersuchen.
- Einen überschaubaren Downloadordner bewusst rekursiv prüfen.
- Einen Scan mit dokumentierter Datenbank und Einstellungen nachvollziehbar machen.
- Eine Fundmeldung mit Dateiherkunft und weiteren Belegen abgleichen.

Für viele wiederholte Aufträge kann ein bereits eingerichteter `clamd`-Dienst zweckmäßig sein. Er ist jedoch eine andere Betriebsart und wird nicht durch diesen Eintrag eingerichtet.

## 7. Risiken, Nebenwirkungen und Vorsicht

`--remove` kann Dateien löschen. `--move` verschiebt sie; auch das kann Programme oder Abläufe unterbrechen. Solche Aktionen hier nicht aus einer Beispielzeile ergänzen. Ein Fehlalarm kann sonst unmittelbar Datenverlust verursachen.

Archive können sehr viel Arbeitsspeicher, Zeit oder temporären Platz beanspruchen. Grenzwerte nicht pauschal deaktivieren, nur um eine Warnung verschwinden zu lassen. Verschlüsselte Inhalte können ohne passende Entschlüsselung nicht vollständig bewertet werden.

Dateinamen können Zeilenumbrüche enthalten. Eine textuelle Fundzeile ist deshalb keine sichere alleinige Grundlage für automatisches Löschen anderer Pfade. Der Dateizugriff muss eindeutig zur tatsächlich geprüften Datei gehören.

## 8. Häufige Fehler

- **Datenbank fehlt:** Der Scanner kann ohne geeignete Signaturen nicht normal arbeiten.
- **Alte Signaturen:** Versionsausgabe und Aktualisierungsweg getrennt prüfen.
- **Datei übersprungen:** Leserechte, Links und Grenzen beachten.
- **Fund mit Fehler verwechselt:** Rückgabestatus `1` und `2` unterscheiden.
- **Signaturstand mit Sicherheitsgarantie verwechselt:** Auch aktuelle Erkennung bleibt begrenzt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer einzelnen eigenen Datei und ohne automatische Bereinigung beginnen. Ausführbare Downloads auch nach einem unauffälligen Scan nur aus nachvollziehbaren Quellen verwenden.

Berichte vor Weitergabe auf private Dateinamen prüfen. Ein Datenbankupdate über `freshclam` ist ein eigener Netzwerk- und Schreibvorgang; es wurde für diese Dokumentation nicht ausgelöst.

## 10. Verwandte Befehle

- `clamdscan`: Client für den laufenden Scandienst.
- `clamd`: Dienst mit eigener Konfiguration und geladenen Signaturen.
- `freshclam`: Signaturdaten aktualisieren.
- `sha256sum`: Dateiinhalt identifizieren; erkennt für sich keine Schadsoftware.

**Prüfstand:** Lokale Hilfe, Version und Manpage geprüft. Kein Datei- oder Systemscan, kein Datenbankupdate und keine Dateiaktion durchgeführt.

Ausgangsdatensatz 312 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
