---
id: "pidof"
name: "pidof"
command: "pidof"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "pidof"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 500
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Sysvinit-Variante laut Manpage; Versionsnummer nicht gesondert ermittelt"
---

# pidof – Eigenes Programm über seinen absoluten Pfad finden

## 1. Kurzbeschreibung

pidof sucht PIDs benannter laufender Programme. Sysvinit und procps-ng stellen unterschiedliche Varianten bereit. Die lokale Manpage beschreibt die Sysvinit-Variante; zusätzliche procps-Optionen werden nicht ungeprüft übernommen.

## 2. Was macht der Befehl?

Ein kurzer Programmname kann mehrere Instanzen oder andere gleichnamige Programme treffen. Ein absoluter Pfad grenzt die beabsichtigte ausführbare Datei besser ein, bleibt aber eine Momentaufnahme. -s wählt nur eine PID, garantiert jedoch weder Einzigartigkeit noch Bereitschaft. Skripterkennung ist implementierungsabhängig und unvollständig.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Sysvinit-pidof-Manpage; [Sysvinit/Debian: pidof](https://manpages.debian.org/bookworm/sysvinit-utils/pidof.8.en.html) und [procps-ng-Variante zum Vergleich](https://man7.org/linux/man-pages/man1/pidof.1.html)

## 3. Syntax

```text
pidof [OPTIONEN] PROGRAMM_ODER_PFAD...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-s` | Nur eine passende PID ausgeben. |
| `-q` | Nur Rückgabestatus, keine PID-Ausgabe. |
| `-o PID` | Bestimmte PIDs ausschließen. |
| `-x` | Auch Skripte berücksichtigen; keine vollständige Interpretererkennung. |
| `-c` | Gleichen Rootpfad verlangen; Rechte-/Implementierungsgrenzen. |
| `-d TRENNER` | Lokale Sysvinit-Ausgabetrennung; andere Variante kann -S verwenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-pidof-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cp /usr/bin/sleep "$uebung/lern-sleep"
"$uebung/lern-sleep" 2 &
kind_pid=$!
pidof -s "$uebung/lern-sleep" > pid.txt
cat pid.txt
rg -x "$kind_pid" pid.txt
wait "$kind_pid"
printf 'Eigene Programmkopie normal beendet\n'
```

### Schritt 3: Ergebnis einordnen

Die Übung kopiert nur das vorhandene sleep-Binary in einen neuen eigenen Ordner und startet diese Kopie für zwei Sekunden. Die gefundene PID muss mit $! übereinstimmen. Danach wird normal gewartet; kein Signal wird gesendet. Der absolute Pfad verhindert die Suche nach beliebigen sleep-Instanzen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Programminstanzen zuordnen:** Pfad, PID und Zeitpunkt zusammen dokumentieren. **Portabilität prüfen:** Implementierung vor Optionsübernahme identifizieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Treffer bedeutet nur gefunden, nicht betriebsbereit. PID-Wiederverwendung und Prozessende bleiben möglich. Die lokale Datei darf nicht unter einem anderen Verwaltungsnamen wie killall5 gestartet werden. Keine fremden Programme signalisiert und keine Systembinärdatei verändert; nur eigene Kopie erzeugt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Treffer, Status 1 | Prozessende, Sicht oder Pfadauswahl prüfen. |
| Mehrere Treffer | Name nicht eindeutig; -s löst die fachliche Mehrdeutigkeit nicht. |
| Skript nicht erkannt | Interpreter-/Startform und Implementierung beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Lokale Sysvinit-Variante laut Manpage; Versionsnummer nicht gesondert ermittelt. Praktisch geprüft: Nur eigene kurzlebige Programmkopie per absolutem Pfad gefunden und PID verglichen, normal abgewartet. Keine Signale. Mehrinstanz-, Skript-, Namespace- und Variantenfälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pgrep` | Regex und zusätzliche Prozesskriterien. |
| `ps` | Prozessdetails anzeigen. |
| `jobs` | Nur die Tabelle der aufrufenden Shell. |

Ausgangsdatensatz 500 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
