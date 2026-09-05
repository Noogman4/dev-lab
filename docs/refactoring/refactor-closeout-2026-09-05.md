# Refactoring-Zwischenabschluss 2026-09-05

## Stand

- Branch: `refactor/safe-stepwise-20260720-222422`
- Arbeitsziel: mergefaehiger Zwischenstand statt weiterer breiter Zerlegung.
- Letzter grosser Abschlussblock: R11-Security-Haertung und Audit-Artefakte.
- Voller Teststand: `2562 passed, 2 skipped`.

## Erledigt

- Core-Helfer, State, Diagnostics, Support-Bundle und Tooling wurden in kleinen
  Schritten bearbeitet und dokumentiert.
- Repository Guard, Process Guard, Firewall/UFW, VPN/WireGuard, DNS/Netzwerk,
  Packet Capture und Security-nahe Parser/Auswertungen wurden bereichsweise
  abgesichert.
- Radio/UI wurde umfangreich in kleine Callback-, Runtime-State- und
  Builder-Schritte zerlegt.
- R11-Haertungen sind umgesetzt: UFW-sysctl-Konflikte, mpv/ffmpeg-Senken,
  Radio-Handover, Performance-Log-Redaction und Symlink-Schutz.
- Website- und Release-Bundle-Skripte nehmen den aktuellen R11-Auditbericht,
  das R10-Archiv und das R11-PDF korrekt mit.

## Bewusst offen

- `netmon/app.py` bleibt mit rund 47k Zeilen der groesste Monolith. Weitere
  Auslagerung ist sinnvoll, aber nicht mehr Voraussetzung fuer diesen
  Zwischenabschluss.
- `netmon/features/security_audit_controller.py` bleibt mit rund 9k Zeilen ein
  grosser, aber testabgedeckter Controller.
- `netmon/netmon_radio_app.py` bleibt mit rund 6.7k Zeilen ein groesserer
  Standalone-Block.
- Packaging kann spaeter weiter refaktoriert werden; fuer den aktuellen Stand
  sind die relevanten Site-/Release-Bundle-Smokes gruen.

## Abschlusschecks

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`
- `bash -n scripts/build_netmon_site_bundle.sh`
- `bash -n scripts/build_netmon_release_update_bundle.sh`
- `.venv/bin/python -m pytest tests/test_netmon_deb_packaging.py -q`
- `bash scripts/build_netmon_site_bundle.sh`
- `bash scripts/build_netmon_release_update_bundle.sh`
- `bash scripts/run_black_filewise.sh --check netmon/app.py netmon/core/performance_monitor.py netmon/features/radio_controller.py netmon/features/security_audit_controller.py tests/test_netmon_diagnostics.py tests/test_netmon_lynis_output.py tests/test_netmon_radio_module.py tests/test_performance_monitor.py scripts/build_security_audit_pdf_r11.py`
- `.venv/bin/python -m pytest`

Die Build-Skripte ueberspringen die Minisign-Signatur erwartbar, wenn
`NETMON_MINISIGN_SECRET_KEY` nicht gesetzt ist.

Ein repo-weiter dateiweiser Black-Lauf ueber `netmon tests tools scripts agent`
wurde nach langer Laufzeit kontrolliert abgebrochen. Der robuste Abschlusscheck
nutzt deshalb die zuletzt geaenderten Python-Dateien gezielt; `ruff` und die
vollstaendige Testsuite laufen repo-weit gruen.
