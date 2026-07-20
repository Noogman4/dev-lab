# NetMon Refactoring Baseline

## Stand

- Datum: 2026-07-20T22:24:58+02:00
- Branch: `refactor/safe-stepwise-20260720-222422`
- Ausgangsbranch: `feature/secure-browser-manager`
- Commit: `445279acbfdc0dacbe9156a5c0d8773f307f2066`
- Commit-Kurzform: `445279ac chore: save current NetMon state`
- Sicherungs-Tag: `pre-refactor-20260720-222422`
- NetMon-Backup: `/dev-lab/projects/dev-lab/backups/netmon-refactor/netmon-before-refactor-20260720-222422`
- Vorheriges Pre-Cleanup-Backup: `/dev-lab/projects/dev-lab/backups/netmon-refactor/netmon-before-refactor-20260720-215822`

## Backup-Pruefung

- Backup-Ziel: NetMon-Projektordner `/dev-lab/projects/dev-lab/netmon/`
- Backup-Groesse: `141M`
- Vergleich: `diff -qr /dev-lab/projects/dev-lab/netmon /dev-lab/projects/dev-lab/backups/netmon-refactor/netmon-before-refactor-20260720-222422 --exclude=.git --exclude=__pycache__ --exclude=*.pyc`
- Ergebnis: keine Abweichungen
- Hinweis: `/dev-lab/projects/dev-lab/netmon` ist kein eigenes Git-Repository. Die Git-Metadaten liegen im Parent-Repo `/dev-lab/projects/dev-lab/.git`, daher enthaelt das NetMon-Ordnerbackup erwartungsgemaess kein eigenes `.git`.

## Umgebung

- System-Python: `Python 3.12.3`
- Projekt-Python: `.venv/bin/python`, `Python 3.12.3`
- Betriebssystem: `Linux proglab 7.0.0-28-generic #28~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Jul  1 15:50:57 UTC 2 x86_64 x86_64 x86_64 GNU/Linux`
- Virtuelle Umgebung: `/dev-lab/projects/dev-lab/.venv`
- Pip-Hinweis: `pip freeze` meldete, dass `/home/happy/.cache/pip` nicht beschreibbar ist; der Pip-Cache wurde deaktiviert. Das beeinflusst die installierten Pakete nicht.

## Hauptabhaengigkeiten

- `black==26.5.1`
- `pytest==9.1.1`
- `ruff==0.15.20`
- `psutil==7.2.2`
- `requests==2.34.2`
- `reportlab==5.0.0`
- `PySide6==6.11.1`
- `pillow==12.2.0`
- `openpyxl==3.1.5`

## Verfuegbare Testbefehle

- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`
- `.venv/bin/python -m ruff check netmon tests tools scripts agent`
- Dateiweiser Black-Check fuer geaenderte Python-Dateien:
  `git ls-files --modified --others --exclude-standard -- ':(glob)**/*.py'` und pro Datei `timeout 60 .venv/bin/python -m black --fast --check <datei>`
- `.venv/bin/python -m pytest`
- `make roots-guard-smoke`
- `make roots-guard-checks`
- `bash scripts/run_netmon_gui_smoke.sh`

## Baseline-Testergebnisse

- `compileall`: bestanden
- `ruff check netmon tests tools scripts agent`: bestanden
- Black dateiweise fuer alle geaenderten Python-Dateien: bestanden
- `pytest`: `2136 passed, 2 skipped`
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- GUI-Smoke:
  - In der Sandbox scheiterte Tk/xvfb mit `couldn't connect to display`.
  - Ausserhalb der Sandbox bestanden: `NetMon GUI smoke test ok`.

## Bekannte Warnungen und bestehende Besonderheiten

- Repo-weite Black-Checks ueber grosse Pfadgruppen koennen lange laufen oder haengen. Fuer sichere Verifikation wurde dateiweise mit Timeout gearbeitet.
- `git diff --cached --check` meldete Whitespace innerhalb der PDF `site/netmon_security_audit_2026_r10.pdf`. Das wurde als PDF-Artefakt bewertet und nicht veraendert.
- Das Repository enthaelt historische Backups und ignorierte Caches. Test- und Dateisuchen fuer Refactoring sollen `backups/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` und Build-Artefakte vermeiden.

## Funktionierende Hauptbereiche

- Vollstaendige Pytest-Suite
- Roots Baseline Guard UI und Controller
- Headless-GUI-Start
- Security Baseline / Lynis-Auswertung laut Tests
- Firewall-, VPN-, DNS-, Packet-Capture-, Repository-Guard- und Process-Guard-Testbereiche
- NetMon-Web-/Audit-Artefakte laut vorhandenen Tests

## Manuelle Pruefungen

- Anwender bestaetigte vor dem Commit: NetMon laeuft aktuell wie gewuenscht.
- Arbeitsbaum war nach Commit `445279ac` sauber.
- Sicherungs-Tag und Refactoring-Branch wurden vor Code-Refactoring erstellt.
