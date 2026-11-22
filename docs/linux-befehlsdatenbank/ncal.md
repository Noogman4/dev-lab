---
id: "ncal"
name: "ncal"
command: "ncal"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["ncal", "grundlagen & hilfe"]
status: "Debian-Handbuch geprüft; keine lokale Kalenderausgabe"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 363
reviewed_at: "2026-11-13"
locally_checked_version: "ncal lokal nicht installiert"
---

# ncal – Kalender mit ausdrücklich gewähltem Wochenanfang anzeigen

## 1. Kurzbeschreibung

`ncal` zeigt Kalender in einer alternativen Anordnung und bietet unter anderem Auswahl des Wochenanfangs. **Root-Rechte sind nicht nötig.** Es legt keine Termine an und verändert die Uhr nicht.

## 2. Was macht der Befehl?

Das [Debian-Handbuch zur ncal-Variante](https://manpages.debian.org/trixie/ncal/ncal.1.en.html) beschreibt eine kompakte Darstellung, in der Wochentage und Wochen anders angeordnet sein können als beim traditionellen `cal`.

Für ein bestimmtes Datum Monat und vollständiges Jahr angeben. Ein wechselnder aktueller Monat ist für reproduzierbare Beispiele weniger geeignet.

## 3. Syntax

```bash
ncal -M 11 2026
ncal -y 2026
```

Die erste Form wählt November 2026 mit Montag als Wochenanfang. Die zweite fordert eine Jahresansicht an. Beide wurden hier nicht ausgeführt, weil `ncal` fehlt.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-M` | Montag als Wochenanfang. | Großes M beachten. |
| `-S` | Sonntag als Wochenanfang. | Andere Anordnung. |
| `-w` | Wochennummern ergänzen. | Passende Kalenderdarstellung lesen. |
| `-y` | Jahresansicht. | Mehr Ausgabe. |
| `-h` | Heutige Hervorhebung ausschalten. | Keine Hilfeoption. |
| `-b` | Traditionellere Darstellung. | Nicht mit vollständig identischer Implementierung gleichsetzen. |
| `-e` | Westliches Osterdatum anzeigen. | Keine vollständige Feiertagsliste. |

Die genaue Auswahl gilt für das dokumentierte Paket. Andere `cal`-Programme können dieselben Buchstaben anders verwenden.

## 5. Beispiel erklärt Schritt für Schritt

```bash
ncal -M 11 2026
```

`-M` macht den gewünschten Wochenanfang ausdrücklich. `11` und `2026` bestimmen den Monat. Zuerst die Achsen beziehungsweise Wochentagsbeschriftungen der Anzeige lesen, dann die gesuchte Tageszahl zuordnen.

Eine behauptete konkrete Ausgabe wird nicht angegeben, da kein Lauf stattfand. Die Syntax stammt aus dem Hersteller-/Distributionshandbuch.

Für historische Datumsfragen können landesabhängige Kalenderwechsel relevant sein. Die vereinfachten Annahmen des Programms sind nicht automatisch eine historische Beweisgrundlage.

## 6. Typische Anwendungsfälle

- Eine Monatsübersicht mit passendem Wochenanfang lesen.
- Kalenderwochen in einer eigenen Planung überblicken.
- Jahresübersichten im Terminal betrachten.
- Alternative Darstellung zu `cal` kennenlernen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige ist lesend. Falsch gelesene Zeilen oder Spalten können aber zu Planungsfehlern führen. Ein Kalender ist außerdem kein verbindlicher Fristen- oder Feiertagsrechner.

Wochennummer, Kalenderjahr und ein einzelnes Datum nicht ohne passenden Kontext gleichsetzen. Um den Jahreswechsel können unterschiedliche Zuordnungen relevant sein.

## 8. Häufige Fehler

- **`-h` als Hilfe:** Hier Hervorhebungssteuerung.
- **`-m` und `-M` verwechseln:** Unterschiedliche Funktionen.
- **Kurzes Jahr:** Vollständige Jahreszahl nutzen.
- **Gleiche Tabellenanordnung wie `cal` erwarten:** Beschriftung lesen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem ausdrücklich angegebenen Monat und Jahr anfangen. Für eine konkrete Installation deren eigenes Handbuch verwenden.

Wenn nur ein formatierter einzelner Zeitwert benötigt wird, ist `date` gezielter. Die Kalenderdarstellung erfordert keine Änderung der Systemzeitzone.

## 10. Verwandte Befehle

- `cal`: Traditionelle Monatsansicht.
- `date`: Einzelne Zeitwerte formatieren.
- `man`: Implementierungsbezogene Optionen.

**Prüfstand:** Handbuch gelesen. Keine Installation, kein Lauf und keine Uhränderung.

Ausgangsdatensatz 363 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
