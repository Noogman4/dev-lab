# 12 rkhunter Repair Config

## Ausgangszustand

- Datei: `netmon/core/rkhunter_manager.py`
- Fokus dieses Schritts: Textumformung in `repair_config`
- Bestehende Tests: `tests/test_rkhunter_manager.py`
- Indirekte Aufrufer: rkhunter-Reparaturaktion im Security-Audit-Controller

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits gelesenen rkhunter-Konfigurationstext.
- Keine Root-Kommandos geaendert.
- Keine erlaubten Systempfade geaendert.
- Keine Backup-, Restore- oder `propupd`-Kommandos geaendert.
- Keine neuen Subprocess-Aufrufe.

## Risiken

- `UPDATE_MIRRORS`, `MIRRORS_MODE` und `WEB_CMD` muessen weiterhin ersetzt werden.
- Fehlende Zielwerte muessen weiterhin am Ende ergaenzt werden.
- Nicht betroffene Konfigurationszeilen muessen erhalten bleiben.
- Root-Schreibpfad und Allowlist-Pruefung duerfen sich nicht aendern.

## Performance Vorher

- Commit vorher: `243fb0a1`
- Messbedingungen: direkte synthetische Ausfuehrung der bisherigen Textumformung mit 80 Zeilen Konfigurationstext, `time.perf_counter()`, 100 Wiederholungen.
- `rkhunter_repair_config_content`: Median `0.2780 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die rkhunter-Reparatur-Textumformung ergaenzen.
- Textumformung aus `repair_config` in einen internen Helper extrahieren.
- Lesen, Schreiben, temporaere Datei, `sudo install` und Allowlist-Pruefung unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_repair_config_content` eingefuehrt.
- `repair_config` baut weiterhin die Reparaturziele und delegiert nur die reine Textumformung an den Helper.
- Keine Root-Kommandos, Systempfade oder Backup-/Restore-Pfade geaendert.

## Unveraendertes Sollverhalten

- `UPDATE_MIRRORS=1` wird weiterhin gesetzt.
- `MIRRORS_MODE=0` wird weiterhin gesetzt.
- `WEB_CMD` wird weiterhin aus `_preferred_web_cmd` uebernommen.
- Fehlende Zielzeilen werden weiterhin ergaenzt.
- Der Schreibpfad laeuft weiterhin ueber `_write_config`.

## Betroffene Dateien

- `netmon/core/rkhunter_manager.py`
- `tests/test_rkhunter_manager.py`
- `docs/refactoring/areas/12-rkhunter-repair-config.md`
- `docs/refactoring/performance/areas/12-rkhunter-repair-config.md`

## Hinzugefuegte Tests

- `test_repair_config_content_replaces_targets_and_preserves_other_lines`
- `test_repair_config_content_appends_missing_targets_in_order`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_rkhunter_manager.py`: `9 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_rkhunter_manager.py tests/test_rkhunter_security_flow.py`: `27 passed`
- `.venv/bin/python -m ruff check netmon/core/rkhunter_manager.py tests/test_rkhunter_manager.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/core/rkhunter_manager.py tests/test_rkhunter_manager.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/core/rkhunter_manager.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_rkhunter_manager.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2185 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `rkhunter_repair_config_content`: Median `0.2114 ms`

## Bewertung

- Keine relevante Performance-Verschlechterung.
- Die Verbesserung liegt in einem synthetischen Textpfad und ist nicht Ziel dieses Schritts.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische rkhunter-Konfiguration.
- Der Schritt testet keine echte Reparatur gegen `/etc/rkhunter.conf`.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-rkhunter-repair-config`.
