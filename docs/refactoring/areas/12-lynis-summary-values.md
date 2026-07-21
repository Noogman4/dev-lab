# 12 Lynis Summary Values

## Ausgangszustand

- Datei: `netmon/features/security_audit_controller.py`
- Fokus dieses Schritts: Summary-Wert-Erkennung fuer Lynis-Ausgaben
- Bestehende Tests: `tests/test_netmon_lynis_output.py`
- Indirekte Aufrufer: Lynis Schnellaudit, Lynis Vollscan, Security-Baseline-Zusammenfassung

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits normalisierte Lynis-Textausgabe.
- Keine Lynis-Scan-Kommandos geaendert.
- Keine sudo- oder Root-Pfade geaendert.
- Keine Security-Baseline-Hardening-Schritte geaendert.
- Keine neuen Subprocess-Aufrufe.

## Risiken

- `Hardening index` muss weiterhin aus Doppelpunkt-Formaten erkannt werden.
- `Warnings` und `Suggestions` muessen weiterhin aus Klammer- und Doppelpunkt-Formaten erkannt werden.
- Fehlende oder ungueltige Werte muessen weiterhin `-` liefern.
- Die angezeigten Summary-Strings duerfen sich nicht aendern.

## Performance Vorher

- Commit vorher: `3c731e10`
- Messbedingungen: direkter Aufruf von `update_lynis_summary_from_output` mit synthetischer Lynis-Ausgabe, `time.perf_counter()`, 100 Wiederholungen.
- `lynis_summary_values`: Median `0.0342 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die Lynis-Summary-Wert-Erkennung ergaenzen.
- Inneres Summary-Parsing aus `update_lynis_summary_from_output` in einen internen Helper extrahieren.
- Lynis-Start, sudo, Threading und Hardening-Pfade unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_lynis_summary_value` eingefuehrt.
- `update_lynis_summary_from_output` nutzt den Helper fuer `Hardening index`, `Warnings`, `Suggestions` und `Tests performed`.
- Keine Scan-Kommandos, Root-Pfade oder Hardening-Aktionen geaendert.

## Unveraendertes Sollverhalten

- Summary-Werte werden weiterhin als Strings gespeichert.
- Nicht gefundene Werte bleiben `-`.
- `lynis_hardening_index_var`, `lynis_summary_var` und `lynis_last_result` behalten ihre bisherigen Werteformate.
- Lynis-Schnellscan und Vollscan starten unveraendert.

## Betroffene Dateien

- `netmon/features/security_audit_controller.py`
- `tests/test_netmon_lynis_output.py`
- `docs/refactoring/areas/12-lynis-summary-values.md`
- `docs/refactoring/performance/areas/12-lynis-summary-values.md`

## Hinzugefuegte Tests

- `test_lynis_summary_value_reads_colon_and_parenthesized_counts`
- `test_lynis_summary_value_returns_dash_for_missing_or_invalid_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_lynis_output.py`: `152 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_lynis_output.py`: `154 passed`
- `.venv/bin/python -m ruff check netmon/features/security_audit_controller.py tests/test_netmon_lynis_output.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/features/security_audit_controller.py tests/test_netmon_lynis_output.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/features/security_audit_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_netmon_lynis_output.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2190 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `lynis_summary_values`: Median `0.0404 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0062 ms` liegt fuer diesen kleinen Parserpfad im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische Lynis-Ausgaben.
- Der GUI-Smoke prueft Startbarkeit, aber keinen echten Lynis-Lauf.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-lynis-summary-values`.
