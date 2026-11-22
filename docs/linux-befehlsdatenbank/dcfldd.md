---
id: "dcfldd"
name: "dcfldd"
command: "dcfldd"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dcfldd", "forensik & recovery"]
status: "Manpage geprüft; Beispiel ausschließlich mit eigenen neuen Dateien geplant"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 327
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# dcfldd – Daten kopieren und den Kopierumfang dokumentieren

## 1. Kurzbeschreibung

`dcfldd` kopiert Daten und ergänzt Funktionen für Hashwerte, Protokolle und geteilte Ausgaben. Die Syntax ähnelt `dd`: Quelle und Ziel stehen in Argumenten wie `if=...` und `of=...`.

**Für eigene lesbare und beschreibbare Dateien sind keine Root-Rechte nötig.** Direkter Zugriff auf geschützte Geräte braucht zusätzliche Rechte. Ein falsch angegebenes Geräte- oder Dateiziel kann Daten überschreiben.

## 2. Was macht der Befehl?

Die [Paket-Manpage](https://manpages.debian.org/trixie/dcfldd/dcfldd.1.en.html) beschreibt Kopieren, Hashen und zusätzliche Ausgabewege. Bei jeder Anwendung müssen die tatsächliche Quelle, der gelesene Umfang und das Ziel eindeutig feststehen.

Ein Hash während des Lesens beschreibt zunächst die verarbeiteten Eingabedaten. Für den Nachweis einer gespeicherten Kopie ist auch die Ausgabe relevant. Ein erfolgreicher Programmlauf allein erklärt nicht, ob die richtige Quelle ausgewählt wurde.

Bei einem laufenden, veränderlichen Dateisystem kann sich der Inhalt während der Aufnahme ändern. Ein entstandenes Abbild muss deshalb nicht dieselbe Konsistenz wie eine bewusst vorbereitete ruhende Quelle besitzen.

## 3. Syntax

```text
dcfldd if=QUELLE of=ZIEL [WEITERE_ARGUMENTE]
dcfldd --help
dcfldd --version
```

Die Gleichheitszeichen gehören zur Syntax. Quelle und Ziel nicht vertauschen. Das Programm fragt bei einem gefährlichen Ziel nicht automatisch nach der fachlich richtigen Absicht.

## 4. Wichtige Optionen

| Argument | Bedeutung | Vorsicht |
| --- | --- | --- |
| `if=DATEI` | Eingabe wählen. | Muss die beabsichtigte Quelle sein. |
| `of=DATEI` | Ausgabe wählen. | Kann vorhandene Inhalte überschreiben. |
| `bs=GRÖSSE` | Ein-/Ausgabeblockgröße setzen. | Nicht mit Gesamtmenge verwechseln. |
| `count=ANZAHL` | Zahl der Eingabeblöcke begrenzen. | Kann bewusst nur einen Ausschnitt kopieren. |
| `skip=ANZAHL` | Eingabeblöcke überspringen. | Ändert den erfassten Bereich. |
| `seek=ANZAHL` | Im Ziel versetzt schreiben. | Besonders fehleranfällig bei vorhandenen Daten. |
| `hash=sha256` | SHA-256 mitberechnen. | Kein Herkunftsnachweis. |
| `hashlog=DATEI` | Hashausgabe speichern. | Zusätzliches Schreibziel. |
| `split=GRÖSSE` | Ausgabe teilen. | Reihenfolge zu nachfolgenden Ausgaben beachten. |

Es gibt auch Ausgabeformen, die externe Programme starten. Solche erweiterten Wege gehören nicht in einen unbesehen übernommenen Kopierauftrag.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur eigene Übungsdateien verwenden

```bash
(
  umask 077
  uebung="$(mktemp -d -t netmon-dcfldd-XXXXXX)" || exit 1
  printf 'Eigene Kopieruebung\n' > "$uebung/quelle.txt" || exit 1
  dcfldd "if=$uebung/quelle.txt" "of=$uebung/kopie.txt" \
    hash=sha256 "hashlog=$uebung/kopie.sha256" || exit 1
  cmp "$uebung/quelle.txt" "$uebung/kopie.txt"
)
```

Die neue Ablage begrenzt das Beispiel auf eine frisch erzeugte Textdatei und neue Ziele. Es werden keine Geräte angesprochen. Der Aufruf wurde nicht ausgeführt, weil `dcfldd` lokal fehlt.

### Schritt 2: Die Argumente lesen

`if` bezeichnet die eigene Quelle, `of` die neue Kopie. Das Hashprotokoll ist ein weiteres Ziel. `cmp` wäre anschließend der gesonderte Inhaltsvergleich der beiden konkreten Dateien.

### Schritt 3: Ergebnis nicht überdehnen

Ein erfolgreicher Vergleich würde Gleichheit dieser Dateien zeigen. Er wäre kein Beweis für einen vollständigen Festplatteninhalt, eine unangetastete Gerätequelle oder eine gerichtsfeste Beweiskette. Diese Aufgaben erfordern zusätzliche dokumentierte Bedingungen.

## 6. Typische Anwendungsfälle

- Eine bewusst ausgewählte Datei mit dokumentiertem Umfang kopieren.
- Ein vorbereitetes Abbild unter bekanntem Aufnahmeplan erzeugen.
- Hashinformationen neben einer Kopie erfassen.
- Große geplante Ausgaben in nachvollziehbar benannte Teile aufteilen.

Bei defekten Medien ist ein normaler Kopierlauf nicht automatisch die geeignete Rettungsstrategie. Wiederholte ungezielte Leseversuche können Zeit und verbleibende Zugriffsmöglichkeiten verbrauchen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Hauptproblem ist ein falsches Ausgabeziel. Ein Gerätename statt einer Datei kann ganze Datenbereiche überschreiben. Beispiele mit echten `/dev/...`-Zielen werden hier deshalb nicht angeboten.

Abbilder können gelöschte oder vertrauliche Inhalte enthalten. Zielkapazität, Zugriffsschutz und Aufbewahrung gehören zur Planung. Auch Hashprotokolle und Fehlermeldungen können sensible Pfade enthalten.

## 8. Häufige Fehler

- **`if` und `of` vertauscht:** Die Quelle kann zum überschriebenen Ziel werden.
- **Teilkopie als Vollkopie:** `count`, `skip` und Größen beachten.
- **Hash gleich Herkunft:** Prüfsumme und bestätigte Quelle sind getrennt.
- **Zu wenig Zielplatz:** Fehlerstatus und tatsächlich gespeicherten Umfang prüfen.
- **Lebende Quelle als konsistentes Abbild:** Änderungen während der Aufnahme berücksichtigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst nur mit neuen eigenen Dateien üben. Vor einem realen Auftrag Quelle und Ziel in Worten ausschreiben und die verfügbaren Rechte nicht unnötig erhöhen.

Für fehlerhafte Datenträger ist ein gezielt geplantes Rettungswerkzeug wie GNU `ddrescue` ein eigener Themenbereich. Keine beschädigte Originalquelle für eine reine Dokumentationsübung ansprechen.

## 10. Verwandte Befehle

- `dd`: Allgemeines blockweises Kopieren.
- `ddrescue`: Geplante Rettung bei Lesefehlern.
- `sha256sum`: Hash einer gespeicherten Datei berechnen.
- `cmp`: Zwei konkrete Dateien inhaltlich vergleichen.
- `guymager`: Grafische Abbildaufnahme unter eigenem Aufnahmeplan.

**Prüfstand:** Handbuch gelesen; Beispiel nicht ausgeführt. Kein Datenträger gelesen, beschrieben, gemountet oder verändert.

Ausgangsdatensatz 327 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
