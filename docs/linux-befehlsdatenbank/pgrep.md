---
id: "pgrep"
name: "pgrep"
command: "pgrep"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "pgrep"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 499
reviewed_at: "2026-11-13"
locally_checked_version: "pgrep / procps-ng 4.0.4"
---

# pgrep – Nur eigene direkte Kindprozesse auswählen

## 1. Kurzbeschreibung

pgrep aus procps-ng sucht Prozesse anhand von Namen und weiteren Kriterien und gibt PIDs aus. Es signalisiert sie nicht. pkill ist die verwandte, aber signalgebende Oberfläche.

## 2. Was macht der Befehl?

Unterschiedliche Kriterien müssen gemeinsam passen; mehrere Werte innerhalb eines Kriteriums sind Alternativen. Das Muster ist ein erweiterter regulärer Ausdruck. Ohne -f wird der Prozessname verwendet und kann auf 15 Zeichen begrenzt sein; -f betrachtet die gesamte Befehlszeile und kann die Auswahl unerwartet erweitern.

Quelle, am 2026-11-13 gelesen: [procps-ng: pgrep-Handbuch](https://man7.org/linux/man-pages/man1/pgrep.1.html)

## 3. Syntax

```text
pgrep [OPTIONEN] REGULAERER_AUSDRUCK
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-P PPID` | Direkte Kinder ausgewählter Eltern; nicht alle Nachfahren. |
| `-x` | Vollständiger Mustervergleich statt Teiltreffer. |
| `-f` | Ganze Befehlszeile vergleichen. |
| `-l`, `-a` | Name beziehungsweise vollständige Argumente mit ausgeben. |
| `-u`, `-U` | Effektive beziehungsweise reale Benutzerkennung. |
| `-c` | Treffer zählen; null Treffer liefern weiterhin Status 1. |
| `-n`, `-o` | Neueste beziehungsweise älteste passende Instanz; keine Bereitschaftsprüfung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-pgrep-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
pgrep --version
sleep 2 &
kind_pid=$!
pgrep -P "$$" -x sleep > pids.txt
cat pids.txt
rg -x "$kind_pid" pids.txt
wait "$kind_pid"
```

### Schritt 3: Ergebnis einordnen

Die Eltern-PID ist die eigene Test-Shell; der einzige eigens gestartete sleep läuft zwei Sekunden und endet normal. Seine gespeicherte PID muss unter den Treffern stehen. Kein Signal und kein Folgekommando auf Treffer-PIDs wird ausgeführt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Auswahl prüfen:** Elternbeziehung und exakten Namen kombinieren. **Skripte lesen:** Kein Treffer ist ein eigener Zustand, nicht automatisch ein Werkzeugfehler.

## 7. Risiken, Nebenwirkungen und Vorsicht

PIDs können zwischen Auswahl und späterer Aktion verschwinden oder wiederverwendet werden. Befehlszeilen können Geheimnisse enthalten. Ergebnisse nie ungeprüft an kill/renice weiterreichen. Nur eigene direkte Kinder ausgewählt; keine fremden Prozesse verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 | Keine Treffer; stderr und Kontext prüfen. |
| Langer Name fehlt | Namenslänge und -f-Semantik unterscheiden. |
| Enkelprozess fehlt | -P ist keine rekursive Baumabfrage. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** pgrep / procps-ng 4.0.4. Praktisch geprüft: Eigener zweisekündiger sleep als direktes Kind ausgewählt, PID verglichen und normales Ende abgewartet. Keine Signale. Namens-/Thread-/Namespace- und fremde Rechtefälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pidof` | Programmnamen-/Pfadzuordnung mit anderer Semantik. |
| `ps` | Details ausgewählter Prozesse. |
| `pkill` | Signale senden, nicht mit pgrep verwechseln. |

Ausgangsdatensatz 499 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
