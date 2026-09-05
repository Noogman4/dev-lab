# 16 Security Hardening R11

## Ziel

Offene Security-Haertungen aus Runde 11 nachvollziehbar abschliessen und mit
26 Regressionstests absichern, ohne bestehende Konfigurationsformate zu
aendern.

## Aenderungen

- UFW-sysctl-Konflikte fuer `log_martians` werden erkannt, dokumentiert und beim
  Anwenden der UFW-Haertung persistiert.
- sysctl-Read-Modify-Write bricht ab, wenn zusammengefuehrtes stderr/stdout
  plausibilitaetsfremde Zeilen enthaelt.
- Radio-Handover-Stationen werden normalisiert, bevor sie in den App-Zustand
  uebernommen werden.
- mpv-Medienargumente werden hinter `--` gesetzt, damit streamnahe Werte nicht
  als mpv-Optionen interpretiert werden.
- ffmpeg-Aufnahmen erlauben nur die benoetigten Netzwerkprotokolle und kein
  `file`-Protokoll.
- Der mpv-IPC-Socket liegt in einem privaten Verzeichnis; auch der Fehlerfallback
  erzeugt ein eigenes 0700-Tempverzeichnis.
- Performance-Logs folgen keinen Symlinks, werden mit 0600 angelegt und
  redigieren sensible Werte auch in Metadaten- und Fehlertexten.
- Der Backup-Tab trennt Timeshift-Pruefung und Snapshot-/Restore-Aktionen
  klarer.

## Tests

- `.venv/bin/python -m ruff check netmon/app.py netmon/core/performance_monitor.py netmon/features/radio_controller.py netmon/features/security_audit_controller.py tests/test_netmon_diagnostics.py tests/test_netmon_lynis_output.py tests/test_netmon_radio_module.py tests/test_performance_monitor.py scripts/build_security_audit_pdf_r11.py`
  - bestanden
- `bash scripts/run_black_filewise.sh --check netmon/app.py netmon/core/performance_monitor.py netmon/features/radio_controller.py netmon/features/security_audit_controller.py tests/test_netmon_diagnostics.py tests/test_netmon_lynis_output.py tests/test_netmon_radio_module.py tests/test_performance_monitor.py scripts/build_security_audit_pdf_r11.py`
  - bestanden
- `.venv/bin/python -m pytest tests/test_netmon_diagnostics.py tests/test_netmon_lynis_output.py tests/test_netmon_radio_module.py tests/test_performance_monitor.py`
  - `532 passed`
- `.venv/bin/python -m pytest`
  - `2562 passed, 2 skipped`

## Status

Technisch geprueft und lokal gruen. Noch nicht committed.
