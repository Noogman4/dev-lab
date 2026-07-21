# 12 rkhunter Log Evidence

## Ausgangszustand

- Datei: `netmon/features/security_audit_controller.py`
- Fokus dieses Schritts: Evidence-Zeilen aus `/var/log/rkhunter.log`
- Bestehende Tests: `tests/test_rkhunter_security_flow.py`, `tests/test_rkhunter_analysis_service.py`
- Indirekte Aufrufer: rkhunter Scan Worker und intelligente rkhunter-Auswertung

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits gelesenen rkhunter-Logtext.
- Keine rkhunter-Kommandos geaendert.
- Keine sudo- oder Root-Pfade geaendert.
- Keine `dpkg`- oder `file`-Verifikationskommandos geaendert.
- Keine Repair-, Propupd- oder Restore-Pfade geaendert.

## Risiken

- Hidden-File-Zeilen muessen weiterhin als Evidence erhalten bleiben.
- Hidden-Directory-Zeilen muessen weiterhin als Evidence erhalten bleiben.
- Suspect-File- und `[ Warning ]`-Zeilen muessen weiterhin erhalten bleiben.
- Nicht relevante Info-Zeilen muessen weiterhin ausgefiltert werden.
- Header und Zeilenreihenfolge der Evidence-Ausgabe muessen stabil bleiben.

## Performance Vorher

- Commit vorher: `8ab2e2ed`
- Messbedingungen: direkter Aufruf von `_extract_rkhunter_log_evidence` mit synthetischem rkhunter-Logtext, `time.perf_counter()`, 100 Wiederholungen.
- `rkhunter_log_evidence_filter`: Median `0.0109 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer rkhunter-Logzeilen-Evidence ergaenzen.
- Relevanzentscheidung fuer einzelne Logzeilen in einen internen Helper extrahieren.
- rkhunter Scan, Log-Lesen, Dpkg-Verifikation und UI-Ausgabe unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_rkhunter_log_line_is_evidence` eingefuehrt.
- `_extract_rkhunter_log_evidence` nutzt den Helper fuer jede Logzeile.
- Evidence-Header und Ausgabeformat bleiben unveraendert.
- Keine rkhunter-Kommandos, Root-Pfade oder Repair-Aktionen geaendert.

## Unveraendertes Sollverhalten

- Evidence-Ausgaben beginnen weiterhin mit `=== rkhunter log evidence ===`.
- Relevante Originalzeilen werden weiterhin getrimmt und in Eingabereihenfolge angehaengt.
- Ohne relevante Zeilen wird weiterhin ein leerer String geliefert.
- Der Scan Worker kombiniert weiterhin rkhunter-Ausgabe, Log-Evidence und dpkg/file-Verifikation.

## Betroffene Dateien

- `netmon/features/security_audit_controller.py`
- `tests/test_rkhunter_security_flow.py`
- `docs/refactoring/areas/12-rkhunter-log-evidence.md`
- `docs/refactoring/performance/areas/12-rkhunter-log-evidence.md`

## Hinzugefuegte Tests

- `test_rkhunter_log_line_evidence_matches_warning_and_hidden_entries`
- `test_rkhunter_log_line_evidence_ignores_non_evidence_entries`
- `test_extract_rkhunter_log_evidence_keeps_original_relevant_lines`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_rkhunter_security_flow.py tests/test_rkhunter_analysis_service.py`: `30 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_rkhunter_security_flow.py tests/test_rkhunter_analysis_service.py`: `33 passed`
- `.venv/bin/python -m ruff check netmon/features/security_audit_controller.py tests/test_rkhunter_security_flow.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/features/security_audit_controller.py tests/test_rkhunter_security_flow.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/features/security_audit_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_rkhunter_security_flow.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2196 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `rkhunter_log_evidence_filter`: Median `0.0143 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0034 ms` liegt fuer diesen kleinen Parserpfad im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische rkhunter-Logausgaben.
- Der GUI-Smoke prueft Startbarkeit, aber keinen echten rkhunter-Scan.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-rkhunter-log-evidence`.
