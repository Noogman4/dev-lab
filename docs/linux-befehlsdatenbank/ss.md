---
id: "ss"
name: "ss"
command: "ss"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ss"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 443
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ss – Sockets mit ausdrücklich lesendem Modus untersuchen

## 1. Kurzbeschreibung

ss aus iproute2 zeigt Sockets und TCP-Details. Die meisten Anzeigen sind lesend; die Option --kill beziehungsweise -K kann dagegen Sockets zwangsweise schließen.

## 2. Was macht der Befehl?

Lauschende TCP-Sockets, Verbindungen und UDP-Sockets sind unterschiedliche Auswahlmengen. Ohne -l/-a fehlen Listener in der Standardansicht. Bindeadresse und Port müssen zusammen betrachtet werden. Empfangs-/Sendewarteschlangen sind zustandsabhängige Werte, keine direkte Bandbreitenmessung. Prozessinformationen können wegen Rechten oder Prozessende unvollständig sein.

Quelle, am 2026-11-13 gelesen: [iproute2: ss-Handbuch](https://man7.org/linux/man-pages/man8/ss.8.html)

## 3. Syntax

```text
ss [OPTIONEN] [FILTER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t`, `-u`, `-x` | TCP, UDP oder Unix-Sockets auswählen. |
| `-l`, `-a` | Nur Listener beziehungsweise auch andere ausgewählte Sockets. |
| `-n` | Numerische Service-/Portanzeige. |
| `-p` | Nutzende Prozesse anzeigen, soweit sichtbar. |
| `-i`, `-m` | TCP-Interna beziehungsweise Socket-Speicher. |
| `-H` | Kopfzeile unterdrücken. |
| `-K`, `--kill` | Passende Sockets schließen; kein Lesefilter. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ss -lnt 'sport = :8080'
```

Der zitierte Filter betrifft den lokalen Quellport 8080 der ausgewählten lauschenden TCP-Sockets. Die Shell soll den Ausdruck nicht in eigene Operatoren zerlegen. Das Muster wurde nicht ausgeführt. Ein Treffer wäre keine Bestätigung externer Erreichbarkeit.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Dienstdiagnose planen:** Lokale Bindung von Firewall und externem Pfad trennen. **Skripte verstehen:** Filter an ss übergeben statt komplizierte Textzeilen blind zu durchsuchen.

## 7. Risiken, Nebenwirkungen und Vorsicht

-K kann laufende Verbindungen zerstören; die Anwesenheit einer Ergebnisliste macht es nicht zu einer Anzeigeoption. Prozess- und Socketdaten können vertraulich sein. Keine Sockets wurden geöffnet, gelesen oder geschlossen und keine fremden Prozesse untersucht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Listener sichtbar | Protokoll, -l und Filter prüfen. |
| PID fehlt | Rechte und Lebensdauer berücksichtigen. |
| Syntax error im Filter | Zitierung und ss-Ausdruck statt Shellsyntax prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `netstat` | Ältere Socketanzeige. |
| `lsof` | Offene Dateien einschließlich Sockets. |
| `conntrack` | Getrackte Flüsse statt lokaler Socketobjekte. |

Ausgangsdatensatz 443 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
