---
id: "umount"
name: "umount"
command: "umount"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "umount"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 249
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# umount – Eine Einhängung geordnet lösen

## 1. Kurzbeschreibung

`umount` löst eine Dateisystemeinhängung. Es löscht nicht das Verzeichnis und wirft Hardware nicht automatisch aus. Normalerweise gelten administrative Rechte; erlaubte Benutzer-/FUSE-Mounts haben besondere Regeln.

## 2. Was macht der Befehl?

Ein genauer Einhängepfad ist meist eindeutiger als ein Gerät, das mehrfach gemountet sein kann. Offene Dateien, Arbeitsverzeichnisse oder eine aktive Swapdatei können den Mount beschäftigt halten. Nach dem Aushängen kann der zuvor verdeckte Inhalt des Zielverzeichnisses wieder sichtbar werden.

Quelle, am 2026-11-13 gelesen: [umount-Projekthandbuch](https://manpages.debian.org/trixie/mount/umount.8.en.html)

## 3. Syntax

```text
umount [OPTIONEN] MOUNTPUNKT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-R` | Untermounts rekursiv lösen; größere Wirkung als einzelnes Ziel. |
| `-a` | Viele Mounts lösen; kein Übungsstandard. |
| `-l`, `--lazy` | Sicht jetzt ablösen, Referenzen später aufräumen; kein garantiert sofort freies Gerät. |
| `-f` | Erzwingen für besondere Fälle, etwa unerreichbares NFS; verhindert Hängen nicht zuverlässig. |
| `-r` | Bei Fehlschlag lesenden Remount versuchen; weitere Zustandsänderung. |
| `-d` | Loop-Zuordnung zusätzlich freigeben, soweit passend. |
| `--fake` | Systemaufruf/Helper auslassen, kann aber Buchführung betreffen; kein Gerätetest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Planungsmuster:
Ziel = EXAKTER_MOUNTPUNKT
Vorbedingung = keine ungeklärten Nutzer des Mounts
```

Ein echtes erfolgreiches umount würde diese konkrete Sicht lösen. Lazy unmount würde dagegen nicht alle offenen Referenzen sofort beseitigen. Aus Erfolg oder Verschwinden in einer Ansicht darf nicht blind die Freigabe zum Abziehen, Überschreiben oder Löschen abgeleitet werden. Kein Mountzustand wurde hier verändert.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Wartungsende:** Einhängung nach geordnetem Beenden der Nutzung lösen. **Fehlersuche:** Busy-Zustand sachlich untersuchen, ohne Prozesse wahllos zu beenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Erzwungenes/lazy Aushängen kann Anwendungen und Datenzugriff stören. Rekursion und --all können fremde Mounts treffen. Ausgeschaltete Buchführung oder ein Fakeaufruf ist keine Unmountbestätigung. Keine realen Aushänge-, Prozessbeendigungs- oder Loopaktionen ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Target is busy | Offene Zugriffe/Arbeitsordner/Untermounts klären. |
| Nicht gemountet | Falscher Pfad oder anderer Namespace; nicht daraus Löschsicherheit ableiten. |
| Dateien nach Unmount anders | Zuvor verdeckter Zielordner wieder sichtbar. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mount` | Hängt ein. |
| `findmnt` | Zeigt Einhängungen. |
| `losetup` | Verwaltet eine darunterliegende Loopzuordnung. |

Ausgangsdatensatz 249 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
