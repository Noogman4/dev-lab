---
id: "wait"
name: "wait"
command: "wait"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "wait"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 513
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# wait – Auf eigene Hintergrundaufgaben warten

## 1. Kurzbeschreibung

wait ist ein Shell-Builtin zum Warten auf Kinder derselben Shell.

## 2. Was macht der Befehl?

Eine beliebige fremde PID kann nicht einfach durch wait übernommen werden. Die Shell merkt die Beendigungsstatus ihrer eigenen Hintergrundaufgaben. Mit einer konkreten PID liefert wait deren Status. Ohne Argumente wartet Bash auf aktive Kinder und liefert bei regulärem Ablauf 0; damit werden einzelne Fehler leicht übersehen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help wait`; [Bash-Projekt](https://www.gnu.org/software/bash/) (Handbuchabruf online fehlgeschlagen)

## 3. Syntax

```text
wait [PID oder JOB ...]
wait -n [-p VARIABLE] [PID ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| PID | Auf dieses eigene Kind warten. |
| -n | Auf das nächste passende Kind warten; Bash-Erweiterung. |
| -p VARIABLE | Mit -n die erledigte Kennung speichern; versionsabhängig. |
| -f | Bei Jobkontrolle bis zur Beendigung statt bloßem Statuswechsel warten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
bash --noprofile --norc -c '
  (exit 7) &
  child_pid=$!
  if wait "$child_pid"; then result=0; else result=$?; fi
  test "$result" -eq 7 || exit 1
  printf "Kindstatus=%s\n" "$result"
'
```

### Schritt 3: Ergebnis einordnen

Nur ein selbst erzeugtes, sofort endendes Kind ist beteiligt. Sein bewusst gesetzter Status 7 wird übernommen und überprüft; die äußere Übung endet erfolgreich. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Ergebnisse eigener paralleler Aufgaben einsammeln; Hintergrundarbeit vor dem nächsten Schritt abschließen.

## 7. Risiken, Nebenwirkungen und Vorsicht

wait ohne Auswahl kann unerwartet lange auf eigene andere Jobs warten. Nach dem Ende darf eine alte PID nicht als aktuelle Prozessidentität verwendet werden. Es werden keine Signale versandt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Not a child / Status 127 | Kind gehört zu anderer Shell oder Kennung ist unbekannt. |
| set -e beendet Skript | Erwarteten Nichtnullstatus in if behandeln statt verlieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigenes sofort endendes Kind geprüft; Jobkontrolle, -n/-p und Signalunterbrechung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| jobs | Jobs der aktuellen Shell anzeigen. |
| timeout | Neuen Befehl begrenzen. |
| bash | Shell-Kontext der Kinder. |

Ausgangsdatensatz 513 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
