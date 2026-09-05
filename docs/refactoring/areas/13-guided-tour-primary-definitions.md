# 13 Guided Tour Primary Definitions

## Ziel

Den ersten kleinen Guided-Tour-Schnitt aus `netmon/app.py` herausloesen, ohne
Tour-Inhalte, IDs, Reihenfolge oder Callback-Verhalten zu veraendern.

## Aenderung

- Neues Modul `netmon/ui/tour_specs.py` mit
  `build_guided_tour_primary_definitions(app)`.
- `App._guided_tour_primary_definitions()` delegiert nur noch an diese Factory.
- Die Factory nutzt weiterhin die App-Methoden fuer Step-Builder und
  Uebersetzungen; dadurch bleiben bestehende Lambdas, Callbacks und
  Runtime-Zugriffe in `app.py`.

## Risiko

Niedrig. Der Schnitt bewegt nur die Primaer-Tour-Definitionen (`quickstart`,
`dns`, `security`, `download-scan`, `radio`) in eine reine Factory. Die grossen
Step-Listen bleiben unveraendert in `app.py`.

## Tests

- `.venv/bin/python -m py_compile netmon/app.py netmon/ui/tour_specs.py tests/test_guided_tour_specs.py`
- `.venv/bin/python -m pytest tests/test_guided_tour_specs.py tests/test_netmon_secure_browser_tour.py tests/test_netmon_lang_service.py -q`
- `.venv/bin/python -m ruff check netmon/app.py netmon/ui/tour_specs.py tests/test_guided_tour_specs.py tests/test_netmon_secure_browser_tour.py tests/test_netmon_lang_service.py`
- `bash scripts/run_black_filewise.sh --check netmon/app.py netmon/ui/tour_specs.py tests/test_guided_tour_specs.py`
