# 02 Core State Paths

## Ausgangszustand

- Datei: `netmon/core/state.py`
- Funktionen: `_xdg_dir`, `get_netmon_config_dir`, `get_netmon_state_dir`, `get_netmon_documents_dir`, `get_netmon_documents_subdir`
- Direkte Tests vor Beginn: keine dedizierte `core/state`-Testdatei
- Indirekte Aufrufer: App-Initialisierung, Locking, Diagnostics, Support-Bundles, Radio, VPN, Speedtest, Secure Browser und Linux-Help-Services

## Abhaengigkeiten und Seiteneffekte

- Verwendet `os.environ`, `os.path.expanduser`, `os.path.isdir` und `os.makedirs`.
- Erstellt NetMon-Unterordner automatisch.
- Keine Root-Rechte.
- Keine Systembefehle.
- Keine GUI-Verbindung.
- Keine Threads oder Timer.

## Risiken

- XDG-Pfade und Dokumentenordner duerfen sich nicht aendern.
- Reihenfolge der Dokumentenordner-Suche muss erhalten bleiben:
  1. `XDG_DOCUMENTS_DIR`
  2. `~/Documents`, falls vorhanden
  3. `~/Dokumente`, falls vorhanden
  4. Fallback `~/Documents/NetMon`
- Leere Subdir-Teile muessen weiterhin ignoriert werden.
- Fehler beim Erstellen von Ordnern werden aktuell geschluckt; das Verhalten bleibt unveraendert.

## Absicherung vor Refactoring

- Neue Tests in `tests/test_core_state.py` dokumentieren:
  - `XDG_CONFIG_HOME` und `XDG_STATE_HOME`
  - `XDG_DOCUMENTS_DIR`
  - Prioritaet von `~/Documents` vor `~/Dokumente`
  - Fallback auf `~/Documents/NetMon`
  - Subdir-Erstellung mit ignorierten Leersegmenten

## Geplante kleine Aenderung

- Wiederholte `os.makedirs(..., exist_ok=True)`-Bloecke in einen kleinen Helfer extrahieren.
- Dokumenten-Kandidaten klarer kapseln.
- Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_ensure_dir` als internen Helfer eingefuehrt; er erstellt Ordner und schluckt Fehler wie zuvor.
- `_netmon_child_dir` fuer XDG-basierte `netmon`-Unterordner eingefuehrt.
- Wiederholte `try: os.makedirs(...); except Exception: pass`-Bloecke entfernt.
- Dokumentenpfad-Reihenfolge unveraendert gelassen.

## Unveraendertes Sollverhalten

- `XDG_CONFIG_HOME` und `XDG_STATE_HOME` erzeugen weiterhin `<base>/netmon`.
- `XDG_DOCUMENTS_DIR` erzeugt weiterhin `<base>/NetMon` und hat Vorrang vor `HOME`.
- Ohne `XDG_DOCUMENTS_DIR` wird weiterhin zuerst `~/Documents`, dann `~/Dokumente`, dann `~/Documents` als Fallback genutzt.
- `get_netmon_documents_subdir` ignoriert weiterhin leere oder whitespace-only Segmente.
- Fehler beim Ordneranlegen werden weiterhin ignoriert.

## Betroffene Dateien

- `netmon/core/state.py`
- `tests/test_core_state.py`
- `docs/refactoring/areas/02-core-state.md`

## Hinzugefuegte Tests

- `tests/test_core_state.py`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_core_state.py`: `6 passed`
- `.venv/bin/python -m compileall -q netmon/core/state.py tests/test_core_state.py`: bestanden
- `.venv/bin/python -m ruff check netmon/core/state.py tests/test_core_state.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/core/state.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_core_state.py`: bestanden

## Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest tests/test_core_state.py tests/test_netmon_startup_instance.py tests/test_netmon_diagnostics.py tests/test_netmon_radio_module.py tests/test_speedtest_module.py`: `261 passed`
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- `.venv/bin/python -m pytest`: `2149 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh` ausserhalb der Sandbox: `NetMon GUI smoke test ok`

## Bekannte Restrisiken

- Die Tests verwenden temporaere HOME- und XDG-Pfade, aber keine realen Benutzerordner.
- Fehler beim Ordneranlegen werden wie bisher geschluckt; dieses Verhalten ist nicht verbessert worden.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `02-core-state`.
