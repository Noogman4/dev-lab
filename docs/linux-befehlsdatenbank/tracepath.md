---
id: "tracepath"
name: "tracepath"
command: "tracepath"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "tracepath"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 446
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# tracepath – Pfad und Path-MTU aktiv erkunden

## 1. Kurzbeschreibung

tracepath aus iputils sendet UDP-Proben und wertet Fehlerantworten aus, um Hops und Path-MTU abzuschätzen. Es benötigt gewöhnlich keine besonderen Root-Rechte, erzeugt aber echten Netzverkehr.

## 2. Was macht der Befehl?

Die Path-MTU ist die für den beobachteten Pfad ermittelte Paketgrößengrenze; sie ist keine Bandbreite. Unterschiedliche Antworten und asymmetrische Pfade begrenzen die Interpretation. Ein Fragezeichen kennzeichnet unvollständig bekannte Hopinformation. Die Schätzung des Rückwegs ist laut Handbuch nicht zuverlässig.

Quelle, am 2026-11-13 gelesen: [iputils: tracepath-Handbuch](https://man7.org/linux/man-pages/man8/tracepath.8.html)

## 3. Syntax

```text
tracepath [-4|-6] [-n] [-l LAENGE] [-m MAX_HOPS] [-p PORT] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-4`, `-6` | Adressfamilie auswählen. |
| `-n` | Primär numerische Anzeige. |
| `-b` | Namen und IP-Adressen anzeigen. |
| `-m HOPS` | Maximale Hopzahl; keine globale Paketanzahl. |
| `-l LAENGE` | Anfängliche Paketlänge. |
| `-p PORT` | Anfänglichen UDP-Zielport setzen. |
| `-V` | Programmversion ohne Pfadtest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
tracepath -4 -n -m 3 192.0.2.1
```

Das Muster begrenzt die Hopzahl auf drei und verwendet eine Dokumentationsadresse. Es wurde nicht ausgeführt. Eine gedachte Zeile pmtu 1500 wäre eine Größeninformation, nicht 1500 Mbit/s. reached kann gerade aus einem Port-Unreachable-Fehler abgeleitet werden und bedeutet keinen laufenden UDP-Dienst.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**MTU-Probleme einordnen:** Paketgröße und Pfadrückmeldungen verstehen. **Diagnose vergleichen:** Protokoll und Zielpfad von einer TCP-Anwendung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Proben können von Filtern blockiert werden oder Alarme auslösen. Ein fehlender Hop darf nicht durch ungefragte Protokoll-/Zielwechsel getestet werden. Keine Pakete gesendet, MTUs verändert oder Kernelparameter gesetzt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| !A | Administrativ untersagte Kommunikation, kein lokaler Formatfehler. |
| pmtu kleiner als erwartet | Pfad-/Tunnelgrenze möglich; nicht sofort Interface-MTU ändern. |
| Nur Sterne oder Zeitüberschreitung | Fehlende Rückmeldung ist keine eindeutige Topologieaussage. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `traceroute` | Andere aktive Methoden. |
| `ping` | Echo-Laufzeitmessung. |
| `ip route` | Lokale Routingobjekte statt gemessenem Pfad. |

Ausgangsdatensatz 446 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
