# 12 rkhunter Risk Gate

## Ausgangszustand

- Datei: `netmon/services/rkhunter_analysis_service.py`
- Fokus dieses Schritts: Risiko- und Critical-Flag-Ableitung aus klassifizierten rkhunter-Findings
- Bestehende Tests: `tests/test_rkhunter_analysis_service.py`
- Indirekte Aufrufer: rkhunter-Analyse, Propupd-Gate, Security-Audit-Controller

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits klassifizierte Findings und Rueckgabecodes.
- Keine rkhunter-Kommandos geaendert.
- Keine sudo- oder Root-Pfade geaendert.
- Keine `dpkg`- oder `file`-Verifikationskommandos geaendert.
- Keine Propupd-, Repair- oder Restore-Pfade geaendert.

## Risiken

- Critical Findings muessen weiterhin `high` priorisieren.
- Review Findings oder unerwartete Returncodes muessen weiterhin `medium` ergeben.
- Saubere Analysen muessen weiterhin `low` ergeben.
- Critical-Flag-Felder muessen fuer Propupd unveraendert bleiben.

## Performance Vorher

- Commit vorher: `72645586`
- Messbedingungen: direkter Aufruf von `analyze_rkhunter_output` mit synthetischer rkhunter- und dpkg-Ausgabe, `time.perf_counter()`, 100 Wiederholungen.
- `rkhunter_analysis_risk_gate`: Median `0.0865 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer Risiko- und Critical-Flag-Ableitung ergaenzen.
- Risikoableitung in einen internen Helper extrahieren.
- Critical-Flag-Ableitung in einen internen Helper extrahieren.
- Klassifizierung, Scan-Completion, Dpkg-Validierung und Propupd-Gate unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_rkhunter_risk_from_categories` eingefuehrt.
- `_rkhunter_critical_flags` eingefuehrt.
- `analyze_rkhunter_output` nutzt beide Helper am bisherigen Ort.
- Keine rkhunter-Kommandos, Root-Pfade oder Analyseentscheidungen geaendert.

## Unveraendertes Sollverhalten

- Critical Findings setzen weiterhin `risk == high`.
- Review Findings oder Returncodes ausser `0`/`1` setzen weiterhin `risk == medium`.
- Saubere Ergebnisse bleiben `risk == low`.
- Propupd bleibt nur bei abgeschlossenem Scan, erfolgreicher Dpkg-Pruefung, Low Risk und ohne Critical Flags erlaubt.

## Betroffene Dateien

- `netmon/services/rkhunter_analysis_service.py`
- `tests/test_rkhunter_analysis_service.py`
- `docs/refactoring/areas/12-rkhunter-risk-gate.md`
- `docs/refactoring/performance/areas/12-rkhunter-risk-gate.md`

## Hinzugefuegte Tests

- `test_rkhunter_risk_from_categories_prioritizes_critical_findings`
- `test_rkhunter_risk_from_categories_uses_review_and_rc_status`
- `test_rkhunter_critical_flags_maps_codes_to_gate_fields`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_rkhunter_analysis_service.py`: `16 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_rkhunter_analysis_service.py`: `19 passed`
- `.venv/bin/python -m ruff check netmon/services/rkhunter_analysis_service.py tests/test_rkhunter_analysis_service.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/services/rkhunter_analysis_service.py tests/test_rkhunter_analysis_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/services/rkhunter_analysis_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_rkhunter_analysis_service.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2201 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `rkhunter_analysis_risk_gate`: Median `0.0885 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0020 ms` liegt fuer diesen kleinen Analysepfad im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen synthetische rkhunter-Ausgaben und kuenstliche Kategorien.
- Der GUI-Smoke prueft Startbarkeit, aber keinen echten rkhunter-Scan.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-rkhunter-risk-gate`.
