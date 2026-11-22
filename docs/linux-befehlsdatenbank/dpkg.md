---
id: "dpkg"
name: "dpkg"
command: "dpkg"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "dpkg"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 457
reviewed_at: "2026-11-13"
locally_checked_version: "dpkg 1.22.6"
---

# dpkg – Debian-Versionsregeln ohne Paketänderung prüfen

## 1. Kurzbeschreibung

dpkg verwaltet Debian-Pakete auf niedrigerer Ebene als APT. Es lädt nicht automatisch alle fehlenden Abhängigkeiten aus Repositories. Sein Versionsvergleich ist eine eigenständige, sichere Rechenfunktion.

## 2. Was macht der Befehl?

Paketstatus, gewünschte Auswahl und Fehlerflags sind getrennt. unpacked ist noch nicht configured. Eine Installation kann Maintainerskripte ausführen; --unpack ist daher kein reines Archivlesen. Für reine Paketdateimetadaten dient dpkg-deb, für Datenbankabfragen dpkg-query. Die Übung vergleicht nur selbst gewählte Strings und liest keinen echten Paketbestand.

Quelle, am 2026-11-13 gelesen: [dpkg-Projekt: dpkg-Handbuch](https://man7.org/linux/man-pages/man1/dpkg.1.html)

## 3. Syntax

```text
dpkg [OPTIONEN] AKTION
dpkg --compare-versions VERSION OP VERSION
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--compare-versions` | Debian-Versionsvergleich; 0 wahr, 1 falsch, 2 Fehler. |
| `lt`, `eq`, `gt` | Vergleichsoperatoren als Argument, keine Shellumleitung. |
| `-i` | Paket installieren und konfigurieren. |
| `--unpack` | Installationsschritt mit möglichen Skripten. |
| `--configure` | Ausgepackte Pakete konfigurieren. |
| `-r`, `-P` | Entfernen beziehungsweise Purge. |
| `--force-*` | Schutzprüfungen ändern; hier nicht verwendet. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
dpkg --version
dpkg --compare-versions '1.0~rc1' lt '1.0'
printf 'Vorabversion liegt vor 1.0\n'
if dpkg --compare-versions '1.0' lt '1.0~rc1'; then
  exit 1
else
  vergleich_status=$?
  test "$vergleich_status" -eq 1
  printf 'Umgekehrter Vergleich ist falsch (Status 1)\n'
fi
```

### Schritt 3: Ergebnis einordnen

Die Tilde sortiert vor dem Ende der Version: 1.0~rc1 liegt vor 1.0. Die zweite Bedingung muss Status 1 liefern. Das ist ein echter Funktionstest der Vergleichslogik, kein Test von Paketinstallation oder Abhängigkeitsauflösung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Versionen vergleichen:** Distributionsregeln statt lexikografischer Sortierung verwenden. **Paketstatus verstehen:** Auswahl, Zustand und Konfiguration auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installieren, Konfigurieren und Entfernen ändern Dateien und können Dienste beeinflussen. Sperren nicht löschen und keine fremden Paketprozesse beenden. Ein alternativer Rootpfad allein ist kein allgemeiner Schutz vor Paketcode. Hier kein Archiv installiert und keine Datenbank verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Vergleich liefert 1 | Bedingung ist falsch, nicht automatisch Programmfehler. |
| Version wird falsch sortiert | Nicht sort -V oder Zeichenkettenvergleich als identisch voraussetzen. |
| Abhängigkeiten fehlen | dpkg ist kein Repositoryresolver; nicht mit force-depends umgehen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** dpkg 1.22.6. Praktisch geprüft: Zwei reine Versionsvergleiche samt Status 0/1 praktisch geprüft. Installation, Skripte, Trigger, Paketbestand, Rechte- und Reparaturfälle nicht geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt-get` | Abhängigkeitsplanung und Repositorybezug. |
| `dpkg-query` | Datenbank lesen. |
| `dpkg-deb` | Paketarchive untersuchen. |

Ausgangsdatensatz 457 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
