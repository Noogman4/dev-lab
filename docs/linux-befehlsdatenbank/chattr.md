---
id: "chattr"
name: "chattr"
command: "chattr"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "chattr"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 213
reviewed_at: "2026-11-13"
locally_checked_version: "chattr 1.47.0 (5-Feb-2023)"
---

# chattr – Dateiattribute gezielt von normalen Rechten unterscheiden

## 1. Kurzbeschreibung

`chattr` verändert besondere Dateisystemattribute. Es ersetzt `chmod` nicht. Für manche Attribute eigener Dateien genügt Eigentümerschaft; `i` und `a` erfordern besondere Privilegien. Root ist deshalb nicht generell für jeden Aufruf erforderlich.

## 2. Was macht der Befehl?

`+` ergänzt ausgewählte Attribute, `-` entfernt sie und `=` setzt die gewählte Attributmenge statt einer bloßen Ergänzung. Die Unterstützung ist dateisystemabhängig. `d` schließt eine Datei vom Werkzeug `dump` aus, nicht von sämtlichen Backup-Produkten. `i` bedeutet unveränderlich, `a` nur anhängbar; beide sind kein allgemeiner Schutz vor privilegierten Angreifern. Die Handbuchgrenzen zu bereits offenen Deskriptoren und nicht unterstützten Flags beachten.

Quelle, am 2026-11-13 gelesen: [chattr-Handbuch aus e2fsprogs](https://manpages.debian.org/trixie/e2fsprogs/chattr.1.en.html) und lokale Manpage 1.47.0

## 3. Syntax

```text
chattr [OPTIONEN] MODUS DATEI ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `+d`, `-d` | dump-Ausschluss setzen beziehungsweise entfernen; keine allgemeine Backupsperre. |
| `+i`, `+a` | Unveränderlich beziehungsweise append-only; CAP_LINUX_IMMUTABLE nötig. |
| `-R` | Rekursiv ändern; sehr großer Wirkungsbereich. |
| `-V` | Ausführlich melden und Programmversion anzeigen. |
| `-v NUMMER` | Generation/Version der Datei setzen; keine Programmversionsabfrage. |
| `-f` | Viele Fehler unterdrücken; zum Lernen ungeeignet. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, e2fsprogs und ein Dateisystem mit Unterstützung für das `d`-Attribut. Keine Privilegien erhöhen, wenn der Test scheitert.

### Schritt 1: Eigene Datei erstellen

Die erste Hälfte des folgenden Ablaufs erzeugt nur eine neue Übungsdatei. `mktemp`-Fehler brechen ab.

```bash
uebung="$(mktemp -d -t netmon-chattr-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'Test\n' > probe.txt
chattr -V +d probe.txt
lsattr probe.txt
chattr -V -d probe.txt
lsattr probe.txt
cat probe.txt
```

### Schritt 2: Die beiden Attributanzeigen vergleichen

Nach `+d` muss ein `d` im Attributfeld stehen; nach `-d` fehlt es wieder. Andere Buchstaben können je nach Dateisystem abweichen und sollen unverändert bleiben. Der abschließende Inhalt bleibt `Test`. Die temporäre Datei bleibt erhalten.

### Schritt 3: Aussage eingrenzen

Dieser Test bestätigt nur Setzen und Entfernen von `d` an dieser eigenen Datei. Er prüft weder ein Backup-Programm noch `i`, `a`, Rekursion oder Löschschutz.

## 6. Typische Anwendungsfälle

**Backup-Sonderfall:** Ausschluss im Kontext von `dump` markieren. **Fehleranalyse:** Bei scheinbar unerklärlichen Schreibfehlern Attribute mit `lsattr` von Modusbits unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unveränderlichkeits- und Append-only-Flags können Verwaltungsabläufe blockieren. `=` kann bislang gewollte Attribute entfernen. Flags wie `s` und `u` sind auf ext2/3/4 nicht als verlässliche sichere Löschung oder Wiederherstellung implementiert. Keine Systemdateien verändern und kein pauschales `-R` ausführen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Attribut, Eigentümer oder Capability passt nicht; nicht automatisch sudo ergänzen. |
| Operation not supported | Dateisystem unterstützt den ioctl/Flag nicht; Prüfung als offen markieren. |
| Version unerwartet geändert | `-v` ist eine Dateieigenschaft; Programmversion über dokumentiertes `-V` im Ablauf. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur ein gezielt benanntes Attribut ergänzen oder entfernen; Ausgangszustand vorher erfassen. Der ursprüngliche rote Risikohinweis bleibt sinnvoll, obwohl die kleine Übung beschränkt ist.

**Prüfstand am 2026-11-13:** chattr 1.47.0 (5-Feb-2023). Praktisch geprüft: Abschnitt-5-Ablauf ausgeführt; d gesetzt und entfernt, Inhalt erhalten. Nicht praktisch geprüft: i/a, privilegierte Ausnahmen, Rekursion, andere Dateisysteme. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lsattr` | Attribute anzeigen. |
| `chmod` | Klassische Modusbits ändern. |
| `getfacl` | ACLs untersuchen. |

Ausgangsdatensatz 213 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
