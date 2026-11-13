# Arbeitsauftrag für einen Befehlsdatensatz

Erstelle eine vollständige, gut lesbare Linux-Befehlsdokumentation.

## Ziel

- Der Text soll für Einsteiger verständlich sein.
- Gleichzeitig sollen fortgeschrittene Nutzer genug technische Details bekommen.
- Die Ausgabe soll direkt für eine spätere Markdown-Anzeige geeignet sein.

## Regeln

- Schreibe klar, sachlich und ohne Marketing-Sprache.
- Erkläre Optionen und Risiken konkret.
- Wenn Root-Rechte nicht nötig sind, sage das ausdrücklich.
- Erkläre bestehende Risiken konkret und praxisnah.
- Nutze kurze Abschnitte mit klaren Überschriften.
- Erfinde keine Optionen.
- Markiere unsichere oder versionsabhängige Informationen als Prüfpunkte.
- Übernimm unzutreffende Platzhalter, Beispiele oder Risikoeinstufungen des Ausgangseintrags nicht ungeprüft.
- Unterscheide Dokumentationsprüfung von tatsächlich ausgeführten Tests.

## Struktur der Befehlsdatei

1. Kurzbeschreibung
2. Was macht der Befehl?
3. Syntax
4. Wichtige Optionen
5. Beispiel erklärt Schritt für Schritt
6. Typische Anwendungsfälle
7. Risiken, Nebenwirkungen und Vorsicht
8. Häufige Fehler
9. Sichere Varianten oder Tipps für Einsteiger
10. Verwandte Befehle

## Sprache

Deutsch.

## Eingaben pro Datensatz

Name, Kommando, Kategorie, Kurzbeschreibung, Syntax, Beispiel, Datenbank-Erklärung, Zusatzhinweis, Root-Angabe, Risikostufe und Tags aus dem jeweiligen Ausgangseintrag. Der unveränderte Ausgangseintrag steht in `index.json` unter `source`.

## Zusätzliche Festlegungen für diese Überführung

- Vorlage: `7z.md`.
- Eine eigene Datei pro Eintrag; feste Kennung im Dokumentkopf.
- Offizielle Handbücher, Projektunterlagen und Distributionsdokumentation als Quellen bevorzugen.
- Beispiele nur mit kleinen, eigens angelegten Testdaten praktisch prüfen. Keine System-, Geräte-, Netzwerk- oder Benutzerkonfiguration zum Nachweisen eines Beispiels verändern.
- Die bestehende Befehlsdatenbank und die Anzeige bleiben während der Dokumentationserstellung unverändert.
- Einträge nacheinander bearbeiten und den tatsächlichen Fortschritt in `FORTSCHRITT.md` und `index.json` festhalten.
