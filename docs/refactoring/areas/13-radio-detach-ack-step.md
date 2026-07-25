# 13 Radio Detach Ack Step

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Detach-Ack-Schrittentscheidung aus `_schedule_detach_takeover_ack` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `NetMonRadioApp._schedule_detach_takeover_ack`

## Abhaengigkeiten und Seiteneffekte

- Es wird nur anhand von `radio_proc` und `attempts_left` entschieden.
- Timer-Logik, Retry-Intervall und Core-Ack-Aufrufe bleiben in `_schedule_detach_takeover_ack`.
- Der Helper `_radio_detach_ack_step` hat keine Datei-, Netzwerk-, Tk- oder Subprocess-Zugriffe.

## Risiken

- Wenn `radio_proc` existiert, muss weiterhin sofort `ready` quittiert werden.
- Ohne verbleibende Versuche muss weiterhin der Timeout-Fall genutzt werden.
- Mit verbleibenden Versuchen und ohne Prozess muss weiterhin gewartet werden.
- Die `after(150, ...)`-Planung darf nicht veraendert werden.

## Performance Vorher

- Commit vorher: `0c6fe483`
- Messbedingungen: reine Step-Entscheidung mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_detach_ack_step_inline`: best of 5 `0.03236726600152906 s`

## Durchgefuehrte Aenderungen

- `_radio_detach_ack_step` eingefuehrt.
- `_schedule_detach_takeover_ack` nutzt den Helper innerhalb `_wait_for_playback_ready`.
- Direkte Tests fuer `ready`, `timeout` und `wait` ergaenzt.

## Unveraendertes Sollverhalten

- Playback-ready-Fall sendet weiterhin normalen `detach_ready`-Ack.
- Timeout-Fall sendet weiterhin `detach_ready` mit `timed_out=True`.
- Wait-Fall plant weiterhin einen weiteren Versuch nach 150 ms.
- Exceptions beim Ack-Senden oder Timer-Planen werden weiterhin geschluckt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-detach-ack-step.md`
- `docs/refactoring/performance/areas/13-radio-detach-ack-step.md`

## Hinzugefuegte Tests

- `test_radio_detach_ack_step_is_ready_when_process_exists`
- `test_radio_detach_ack_step_times_out_without_attempts`
- `test_radio_detach_ack_step_waits_with_attempts_left`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `292 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2528 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detach_ack_step_helper`: best of 5 `0.06203502799871785 s`

## Bewertung

- Der Helper fuegt nur minimalen Funktionsaufruf-Overhead hinzu.
- Der Pfad ist nicht laufzeitkritisch und laeuft nur bei Detach-Handover.
- Der Hauptgewinn ist direkte Testbarkeit der Retry-Entscheidung.

## Bekannte Restrisiken

- Die direkten Tests pruefen nur die Step-Entscheidung, nicht den echten Tk-Timer.
- GUI-Smoke deckt Startbarkeit ab, aber keine echte Detach-Handover-Sequenz.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detach-ack-step`.
