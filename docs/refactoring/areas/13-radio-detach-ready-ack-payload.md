# 13 Radio Detach Ready Ack Payload

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Detach-Ready-Ack-Payload-Erzeugung aus `_schedule_detach_takeover_ack` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `NetMonRadioApp._schedule_detach_takeover_ack`

## Abhaengigkeiten und Seiteneffekte

- Es wird nur ein kleines Payload-Dict erzeugt.
- Timer-Logik und `netmon_radio_core.request_radio_handover_ack` bleiben unveraendert in `_schedule_detach_takeover_ack`.
- Der Helper `_radio_detach_ready_ack_payload` hat keine Datei-, Netzwerk-, Tk- oder Subprocess-Zugriffe.

## Risiken

- Normale Ack-Payloads muessen weiterhin `{"action": "detach_ready"}` bleiben.
- Timeout-Ack-Payloads muessen weiterhin `timed_out=True` enthalten.
- Transition-ID und Zielmodus duerfen nicht veraendert werden.
- Die Warte-/Retry-Logik darf nicht veraendert werden.

## Performance Vorher

- Commit vorher: `28b89dd3`
- Messbedingungen: Payload-Dict fuer Timeout-Fall, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_detach_ready_ack_payload_inline`: best of 5 `0.06889957999919716 s`

## Durchgefuehrte Aenderungen

- `_radio_detach_ready_ack_payload` eingefuehrt.
- `_schedule_detach_takeover_ack` nutzt den Helper fuer normalen Ready-Ack und Timeout-Ack.
- Direkte Tests fuer Standard- und Timeout-Payload ergaenzt.

## Unveraendertes Sollverhalten

- Nicht-spielende Handover senden weiterhin sofort `detach_ready`.
- Laufende Handover warten weiterhin auf `radio_proc`.
- Timeout-Fall sendet weiterhin `detach_ready` mit `timed_out=True`.
- Exceptions beim Ack-Senden werden weiterhin geschluckt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-detach-ready-ack-payload.md`
- `docs/refactoring/performance/areas/13-radio-detach-ready-ack-payload.md`

## Hinzugefuegte Tests

- `test_radio_detach_ready_ack_payload_defaults_to_ready_action`
- `test_radio_detach_ready_ack_payload_marks_timeout`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `289 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2525 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detach_ready_ack_payload_helper`: best of 5 `0.07753565399980289 s`

## Bewertung

- Der Helper fuegt nur minimalen Funktionsaufruf-Overhead hinzu.
- Der Pfad ist nicht laufzeitkritisch und laeuft nur bei Detach-Handover.
- Der Hauptgewinn ist direkte Testbarkeit der Payload-Entscheidung.

## Bekannte Restrisiken

- Die direkten Tests pruefen nur Payload-Erzeugung, nicht den Timer-Ablauf.
- GUI-Smoke deckt Startbarkeit ab, aber keine echte Detach-Handover-Sequenz.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detach-ready-ack-payload`.
