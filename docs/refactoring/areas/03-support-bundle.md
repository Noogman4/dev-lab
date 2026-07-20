# 03 Support Bundle

## Ausgangszustand

- Datei: `netmon/core/support_bundle.py`
- Funktionen: `support_packages_dir`, `support_package_path`, `support_bundle_inputs`, `build_support_manifest`, `create_support_package`
- Direkte bestehende Tests: einzelne Support-Paket-Tests in `tests/test_netmon_diagnostics.py`
- Indirekte Aufrufer: `netmon/main.py` und Supportpaket-Aktionen in `netmon/app.py`

## Abhaengigkeiten und Seiteneffekte

- Liest Diagnostik-, Crash- und Runtime-Logpfade.
- Schreibt Support-ZIP-Dateien unter `NetMon/support`.
- Nutzt `zipfile`, `json`, Diagnose-Redaction und Systeminformationen.
- Keine Root-Rechte.
- Keine Systembefehle.
- Keine GUI-Verbindung.
- Keine Threads oder Timer.

## Risiken

- ZIP-Struktur muss stabil bleiben: `manifest.json` und Dateien unter `files/<basename>`.
- Manifest-Felder und Redaction duerfen nicht gelockert werden.
- Doppelte oder fehlende Support-Dateien duerfen nicht mehrfach oder fehlerhaft aufgenommen werden.
- Bestehende Pfadfunktionen duerfen keine realen Systempfade in Tests beschreiben.

## Absicherung vor Refactoring

- Neue Tests in `tests/test_support_bundle.py` dokumentieren:
  - Zeitstempelbasierten Paketpfad.
  - Deduplizierung und Filterung nicht vorhandener Dateien in `support_bundle_inputs`.
  - Redaction in Manifest-Metadaten.
  - ZIP-Struktur bleibt durch vorhandenen Test in `tests/test_netmon_diagnostics.py` abgedeckt.

## Geplante kleine Aenderung

- Kandidatenliste fuer Support-Dateien in einen internen Helfer extrahieren.
- Normalisierung, Deduplizierung und Existenzfilter in einen internen Helfer extrahieren.
- Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_support_bundle_candidate_paths` fuer die feste Kandidatenreihenfolge eingefuehrt.
- `_existing_unique_files` fuer `abspath`, `expanduser`, Deduplizierung und Existenzpruefung eingefuehrt.
- `support_bundle_inputs` delegiert nur noch an diese beiden Helfer.
- Lange Importzeile Black-konform umgebrochen.

## Unveraendertes Sollverhalten

- Supportpakete landen weiterhin unter `NetMon/support`.
- ZIPs enthalten weiterhin `manifest.json` und Dateien unter `files/<basename>`.
- Nicht vorhandene Dateien werden weiterhin ignoriert.
- Doppelte normalisierte Pfade werden weiterhin nur einmal aufgenommen.
- Manifest-Metadaten und Systeminformationen werden weiterhin redigiert.

## Betroffene Dateien

- `netmon/core/support_bundle.py`
- `tests/test_support_bundle.py`
- `docs/refactoring/areas/03-support-bundle.md`

## Hinzugefuegte Tests

- `tests/test_support_bundle.py`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_support_bundle.py tests/test_netmon_diagnostics.py::test_create_support_package_writes_zip_with_manifest_and_files`: `4 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/core/support_bundle.py tests/test_support_bundle.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/core/support_bundle.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_support_bundle.py`: bestanden
- `.venv/bin/python -m ruff check netmon/core/support_bundle.py tests/test_support_bundle.py`: bestanden
- `.venv/bin/python -m pytest tests/test_support_bundle.py tests/test_netmon_diagnostics.py::test_support_packages_dir_uses_documents_folder tests/test_netmon_diagnostics.py::test_create_support_package_writes_zip_with_manifest_and_files tests/test_netmon_diagnostics.py::test_create_support_package_app_method_remembers_path tests/test_netmon_diagnostics.py::test_create_support_package_app_method_merges_support_form_metadata`: `7 passed`

## Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest tests/test_support_bundle.py tests/test_netmon_diagnostics.py`: `44 passed`
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- `.venv/bin/python -m pytest`: `2152 passed, 2 skipped`

## Bekannte Restrisiken

- Tests erzeugen ZIPs nur in temporaeren Ordnern und pruefen keine manuelle UI-Aktion.
- Die Kandidatenliste bleibt statisch; neue Log-Dateien muessen weiterhin bewusst ergaenzt werden.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `03-support-bundle`.
