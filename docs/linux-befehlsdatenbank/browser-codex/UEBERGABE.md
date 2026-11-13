# Übergabestand für Browser-Codex

Erstellt am 13. November 2026 auf Basis von Commit
`f7097d3a0f46496eb03107a02815befbe2219b83`.

Die Übergabe enthält ausschließlich die gemeinsame Dokumentationsgrundlage,
den eingefrorenen Katalog 201–300, zwei Muster, den vorhandenen Markdown-Parser,
die isolierte Strukturprüfung und Chads unveränderte Rückgabe 201–210 samt Review.
Die Original-CSV gehört bereits zum Basiscommit und wird nicht verändert.

## Geprüft

- Alle 100 Katalogzuordnungen 201–300 stimmen mit ihren Originalzeilen überein;
  SHA-256 der vollständigen CSV stimmt mit dem eingefrorenen Ausgangsstand überein.
- Das Rückgabe-ZIP ist lesbar; genau zehn Befehlsdateien und ein Fortschrittsbericht.
  Die kopierten Originale sind über SHA-256 in `HERKUNFT-201-210.json` erfasst.
- Alle zehn Entwürfe und beide Muster passen zum tatsächlichen NetMon-Parser.
- 31 isolierte Pytest-Fälle bestanden; Ruff und Black für die drei Python-Dateien
  bestanden. Black wurde pro Datei einzeln aufgerufen.
- Der CLI-Prüfer akzeptiert die zehn ursprünglichen Entwürfe strukturell und
  weist die noch fehlenden korrigierten Ergebnisdateien erwartungsgemäß zurück.

Das ist keine fachliche Freigabe der Entwürfe. Die vier bekannten Fehler und die
gewünschten Ergänzungen stehen in `REVIEW-201-210.md` und sind noch zu bearbeiten.
Kein GUI-, vollständiger NetMon-Suite-, Paketbau- oder Geräteprüfungslauf ist
Bestandteil dieser Übergabe. Korrekturen sind noch nicht in NetMon integriert.

## Start

Verwende den Branch `codex/linux-docs-browser-handoff-20261113` und lies
`../BROWSER-CODEX-START.md`. Danach ausschließlich 201–210 korrigieren und stoppen.
Der Bereich 211–300 bleibt bis zur nächsten ausdrücklichen Freigabe unbearbeitet.

Die Veröffentlichung dieses Übergabebranches ist nicht die Freigabe für spätere
Commits, Pushes oder Merges von Browser-Codex. Ergebnisse zunächst zur Review
bereitstellen. Der vollständige lokale Index und parallele Änderungen anderer
Bearbeiter verbleiben in deren Arbeitsständen.
