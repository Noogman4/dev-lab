# 12 Lynis Issue Lines

## Ausgangszustand

- Datei: `netmon/features/security_audit_controller.py`
- Fokus dieses Schritts: Zeilenfilterung fuer `extract_lynis_issues_and_recommendations`
- Bestehende Tests: `tests/test_netmon_lynis_output.py`
- Indirekte Aufrufer: Lynis-Problemanzeige und Chad-Uebergabe

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits normalisierte Lynis-Textausgabe.
- Keine Lynis-Scan-Kommandos geaendert.
- Keine sudo- oder Root-Pfade geaendert.
- Keine Security-Baseline-Hardening-Schritte geaendert.
- Keine UI-Texte geaendert.

## Risiken

- Relevante Warnungen, Empfehlungen und Hardening-Zeilen muessen weiterhin sichtbar bleiben.
- Generische deutsche `gefunden`-OK-Zeilen muessen weiterhin ausgefiltert werden.
- `Dateien gefunden` muss weiterhin als relevante Fundzeile erhalten bleiben.
- Die Reihenfolge und der Originaltext der gefilterten Zeilen muessen stabil bleiben.

## Performance Vorher

- Commit vorher: `69e47dbd`
- Messbedingungen: direkter Aufruf von `extract_lynis_issues_and_recommendations` mit synthetischer Lynis-Ausgabe, `time.perf_counter()`, 100 Wiederholungen.
- `lynis_issue_line_filter`: Median `0.0585 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer Lynis-Issue-Zeilenrelevanz ergaenzen.
- Keyword- und `gefunden`-Sonderfalllogik in interne Helper extrahieren.
- Anzeige-Header, Chad-Uebergabe, Scan-Start und sudo-Pfade unveraendert lassen.

## Durchgefuehrte Aenderungen

- `LYNIS_ISSUE_KEEP_KEYWORDS` eingefuehrt.
- `_lynis_issue_line_is_relevant` eingefuehrt.
- `_lynis_relevant_issue_lines` eingefuehrt.
- `extract_lynis_issues_and_recommendations` nutzt diese Helper und behaelt die bisherigen Header und Rueckgaben bei.

## Unveraendertes Sollverhalten

- Warnungen, Empfehlungen und Hardening-Zeilen bleiben sichtbar.
- `Dateien gefunden` bleibt sichtbar.
- Generische `gefunden`-OK-Zeilen bleiben ausgefiltert.
- Leere Treffer liefern weiterhin den bestehenden leeren Lynis-Probleme-Text.

## Betroffene Dateien

- `netmon/features/security_audit_controller.py`
- `tests/test_netmon_lynis_output.py`
- `docs/refactoring/areas/12-lynis-issue-lines.md`
- `docs/refactoring/performance/areas/12-lynis-issue-lines.md`

## Hinzugefuegte Tests

- `test_lynis_issue_line_relevance_keeps_warning_suggestion_and_hardening`
- `test_lynis_issue_line_relevance_skips_generic_found_line`
- `test_lynis_relevant_issue_lines_preserves_order_and_line_text`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_lynis_output.py`: `154 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_lynis_output.py`: `157 passed`
- `.venv/bin/python -m ruff check netmon/features/security_audit_controller.py tests/test_netmon_lynis_output.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/features/security_audit_controller.py tests/test_netmon_lynis_output.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/features/security_audit_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_netmon_lynis_output.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2193 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `lynis_issue_line_filter`: Median `0.0646 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0061 ms` liegt fuer diesen kleinen Parserpfad im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische Lynis-Ausgaben.
- Der GUI-Smoke prueft Startbarkeit, aber keinen echten Lynis-Lauf.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-lynis-issue-lines`.
