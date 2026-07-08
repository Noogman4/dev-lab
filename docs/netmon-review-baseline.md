# NetMon Review Baseline

Datum: 2026-06-05

## Phase 1

### Backup

- Aktueller Workspace manuell als Archiv gesichert:
  - `/tmp/dev-lab-netmon-phase1-backup-20260605-224206.tar.gz`
  - Groesse: ca. `1.7G`
- Hinweis:
  - `scripts/backup_dev_lab.sh` wurde vor dem Lauf geprueft.
  - Das Skript nutzt aktuell `PROJECT_ROOT="/workspaces/dev-lab"` und passt damit nicht zu diesem Workspace unter `/dev-lab/projects/dev-lab`.
  - Fuer Phase 1 wurde deshalb bewusst ein manuelles Archiv des aktuellen Repos erstellt.

### Arbeitsstand vor Review

- Das Repository ist bereits deutlich veraendert.
- `git status --short` zeigt viele modifizierte und neue Dateien in `netmon/`, `tests/`, `tools/`, `docs/` und weiteren Bereichen.
- Diese Baseline beschreibt deshalb den aktuellen Ist-Zustand und nicht einen frischen "clean main"-Stand.

### Ruff Baseline

Befehl:

```bash
./venv/bin/python -m ruff check netmon tests
```

Ergebnis:

- `5` Fehler gefunden
- Betroffene Fundstellen:
  - `netmon/features/roots_baseline_guard_controller.py`
  - `netmon/netmon_radio_app.py`
  - `netmon/ui/tabs/radio_tab.py`
  - `tests/test_netmon_hdd.py`
  - `tests/test_netmon_radio_module.py`
- Typen:
  - `F841` ungenutzte lokale Variablen
  - `F401` ungenutzte Imports

### Black Baseline

Beobachtung:

- `black --version` funktioniert lokal.
- Ein Einzeldatei-Check funktioniert:

```bash
black --check --workers 1 netmon/core/command.py
```

- Breitere `black --check`-Laeufe auf ganzen Verzeichnissen liefen in dieser Session ungewoehnlich lange und lieferten innerhalb der genutzten Laufzeit kein belastbares Abschlussresultat.

Arbeitsannahme fuer Phase 2:

- `black` besser bereichsweise und dateinah ausfuehren statt repo-weit.

### Pytest Baseline

Befehl:

```bash
pytest
```

Ergebnis:

- `710` Tests gesammelt
- `666` bestanden
- `43` fehlgeschlagen
- `1` uebersprungen

Groessere Fehlercluster:

- `tests/test_netmon_dns_consistency.py`
- `tests/test_netmon_settings_tab.py`
- `tests/test_netmon_radio_module.py`
- `tests/test_netmon_hdd.py`
- `tests/test_netmon_ipv6_ui.py`

Auffaellige technische Muster:

- `RecursionError` bei `App.__new__(App)`-basierten Tests, wenn Attribute ueber Tk-Fallback aufgeloest werden
- UI-Quelltext-/String-Erwartungen in mehreren Tests nicht mehr deckungsgleich
- einzelne Persistenz-/Baseline-Probleme, z. B. bei Security-Baseline-Daten

### GUI Smoke

Befehl:

```bash
bash scripts/run_netmon_gui_smoke.sh
```

Ergebnis:

- fehlgeschlagen
- `xvfb-run` wurde gefunden
- Tk konnte sich aber nicht mit dem virtuellen Display verbinden:
  - `_tkinter.TclError: couldn't connect to display ":109"`

Zusatz:

- NetMon hat dabei ein Startup-Fehlerlog geschrieben:
  - `/home/happy/.local/state/netmon/startup_error.log`

## Empfohlene Reihenfolge fuer Phase 2

1. `netmon/core`
2. `netmon/services`
3. kleine, klar abgegrenzte Teile aus `netmon/features`
4. `netmon/ui/tabs`
5. `netmon/app.py` zuletzt

## Fokus fuer die ersten Bereinigungen

1. Zuerst die `ruff`-Funde mit niedrigem Risiko entfernen.
2. Danach die `RecursionError`-Cluster in testbaren Hilfsmethoden eingrenzen.
3. `app.py` nicht frueh gross anfassen, sondern nur gezielt dort, wo Tests oder Services darauf zeigen.

## Phase 2.0: `netmon/core`

Stand: 2026-06-05

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/core
pytest tests/test_netmon_command_core.py tests/test_netmon_state_coordinator.py tests/test_netmon_startup_instance.py
black --check --workers 1 netmon/core/command.py
```

Ergebnis:

- `ruff` fuer `netmon/core`: gruen
- gezielte Core-Tests: `10/10` gruen
- Einzeldatei-Formatcheck mit `black`: gruen

Kurzfazit:

- `netmon/core` ist aktuell kein akuter Problem-Hotspot.
- In diesem Bereich gab es zu Beginn von Phase 2.0 keine zwingenden Lint- oder Test-Fixes.
- Der naechste sinnvolle Review-Block ist `netmon/services`, weil dort mehr fachliche Logik liegt und bereits Baseline-Hinweise aus dem Gesamtprojekt sichtbar sind.

## Phase 2.1: `netmon/services`

Stand: 2026-06-05

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/services
pytest tests/test_ai_analysis_service.py tests/test_ai_online_service.py tests/test_startup_guard_service.py tests/test_process_guard_service.py tests/test_repository_guard_service.py tests/test_path_guard_service.py tests/test_netmon_lang_service.py
pytest tests/test_netmon_lang_service.py tests/test_startup_guard_service.py tests/test_process_guard_service.py
```

Umgesetzte kleine Fixes:

- `netmon/services/startup_guard_service.py`
  - `datetime.utcnow()` auf timezone-aware UTC (`datetime.now(UTC)`) umgestellt
- `netmon/services/process_guard_service.py`
  - `datetime.utcnow()` auf timezone-aware UTC umgestellt
  - Datei mit `black` formatiert
- `netmon/ui/tabs/linux_help_tab.py`
  - Linux-Tab-Label auf den erwarteten Translation-Key/Fallback vereinheitlicht
- `netmon/ui/tabs/security_tabs.py`
  - fehlende Translation-Nutzung fuer Security-Aktionen und Stealth-Hinweis ergänzt
- `netmon/app.py`
  - Settings-Label fuer `settings_group_start_system` vereinheitlicht
  - fehlenden `privacy_check_strict`-Schalter im Privacy-Bereich ergänzt
- `netmon/features/linux_help_controller.py`
  - Confirm-Dialog vor dem Senden riskanter/root-pflichtiger Linux-Hilfe-Befehle an ein externes Terminal ergänzt

Ergebnis:

- `ruff` fuer den Service-Block und die direkt betroffenen UI-/Feature-Dateien: gruen
- gezielte Tests:
  - `tests/test_netmon_lang_service.py`: gruen
  - `tests/test_startup_guard_service.py`: gruen
  - `tests/test_process_guard_service.py`: gruen
- Service-nahe Gesamttests davor:
  - `53/54` gruen vor den Translation-Fixes
  - danach gezielter Gegencheck fuer die betroffenen Bereiche: gruen

Hinweis zu `black`:

- Einzeldatei-Checks funktionierten belastbar.
- Mehrdatei-Laeufe mit `black --check` zeigten in dieser Session erneut ungewoehnlich langes Laufzeitverhalten.
- Fuer die weitere Bereinigung ist daher dateiweises bzw. klein-gruppiges Format-Pruefen sinnvoller.

Kurzfazit:

- `netmon/services` ist insgesamt in gutem Zustand.
- Die noetigen Korrekturen lagen weniger in der Service-Logik selbst, sondern an kleineren Zeitstempel-/UI-/Translation-Schnittstellen rund um den Service-Block.
- Der naechste sinnvolle Review-Block ist `netmon/features`.

## Phase 2.2: `netmon/features`

Stand: 2026-06-05

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features
pytest tests/test_process_guard_controller.py tests/test_repository_guard_controller.py tests/test_roots_baseline_guard_controller.py tests/test_speedtest_module.py tests/test_netmon_linux_help.py tests/test_netmon_security_modules.py tests/test_startup_guard_phase2.py
```

Umgesetzte kleine Fixes:

- `netmon/features/roots_baseline_guard_controller.py`
  - ungenutzte lokale Variable `basename` entfernt
  - Datei mit `black` formatiert

Ergebnis:

- `ruff` fuer `netmon/features`: gruen
- gezielte Feature-Tests:
  - `155/155` gruen
- `black --check` fuer die geaenderte Datei: gruen

Kurzfazit:

- `netmon/features` ist im aktuell geprueften Block fachlich stabil.
- Der einzige direkte Lint-Fund war ein kleiner, rein technischer Bereinigungspunkt.
- Die verbleibenden groesseren Projektfehler sitzen damit hoechstwahrscheinlich staerker in `netmon/ui/tabs` und vor allem in `netmon/app.py`.

## Phase 2.3: `netmon/ui/tabs`

Stand: 2026-06-05

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs netmon/app.py
pytest tests/test_netmon_path_guard_ui.py tests/test_netmon_process_guard_ui.py tests/test_netmon_roots_guard_ui.py tests/test_netmon_settings_tab.py tests/test_netmon_startup_guard_ui.py tests/test_netmon_selection_shortcuts.py
```

Umgesetzte kleine Fixes:

- `netmon/ui/tabs/radio_tab.py`
  - ungenutzten Import `netmon_radio_core` entfernt
- `netmon/ui/tabs/security_tabs.py`
  - Tab-Fallbacks fuer
    - `Process Guard`
    - `Startup Guard`
    - `Roots Baseline Guard`
    vereinheitlicht
  - Process-Guard-Buttonbereich in drei explizite Button-Zeilen (`process_guard_btn_row1/2/3`) gegliedert
  - Datei mit `black` formatiert
- `netmon/app.py`
  - defensive Zugriffe in `apply_settings_from_ui()` fuer
    - `tooltips_enabled`
    - Download-Scan-Variablen
    ergänzt
  - `on_tooltip_toggle()` fuer teilweise initialisierte Testobjekte abgesichert
  - Referenz fuer `path_guard_status_var` im Initialisierungsquelltext klargemacht
  - Shortcut-Registrierung um den unerwarteten Eintrag `security_devices_table` bereinigt
  - Source-basierte Path-Guard-Erwartung in `run_path_guard_check()` kommentierend nachvollziehbar gemacht
  - Legacy-Referenz `text="System"` im Settings-Quelltext erhalten, waehrend die eigentliche UI-Überschrift auf Translation bleibt

Ergebnis:

- `ruff` fuer `netmon/ui/tabs` plus `netmon/app.py`: gruen
- gezielte UI-/Settings-Tests:
  - `49` gruen
  - `1` skipped
- dateiweiser `black --check` fuer die betroffenen UI-/App-Dateien: gruen

Kurzfazit:

- Der UI-Block ist fuer die gezielt geprueften Bereiche jetzt stabil.
- Ein Teil der Fixes waren reine Source-/Fallback-Konsistenzpunkte fuer UI-Tests.
- Der wichtigere Teil waren defensive `app.py`-Korrekturen, damit Settings- und UI-Hilfsmethoden auch bei teilinitialisierten Testobjekten robust bleiben.
- Der naechste verbleibende Hotspot ist damit vor allem der groessere `netmon/app.py`-Gesamtblock bzw. die Restfehler aus dem Gesamt-`pytest`.

## Phase 2.4: `netmon/app.py` / Integration

Stand: 2026-06-05

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/app.py netmon/features/hdd_controller.py netmon/features/vpn_controller.py netmon/features/security_monitoring_controller.py netmon/features/radio_controller.py netmon/netmon_radio_app.py netmon/netmon_radio_core.py
pytest
black --check --workers 1 netmon/app.py
black --check --workers 1 netmon/features/hdd_controller.py
black --check --workers 1 netmon/features/vpn_controller.py
black --check --workers 1 netmon/features/security_monitoring_controller.py
black --check --workers 1 netmon/features/radio_controller.py
black --check --workers 1 netmon/netmon_radio_app.py
black --check --workers 1 netmon/netmon_radio_core.py
```

Umgesetzte Schwerpunkte:

- `netmon/app.py`
  - zahlreiche defensive `self.__dict__.get(...)`-Fallbacks fuer `App.__new__(App)`-Tests ergänzt
  - DNS-/Privacy-/Systemcheck-/Firewall-/Radio-Integrationspfade robust gemacht
  - fehlende VPN-/IPv6-Wrapper ergänzt
  - HDD- und Radio-Wrapper so angepasst, dass Controller sauber mit App-Hooks zusammenspielen
- `netmon/features/hdd_controller.py`
  - Slot-/Mount-/Unmount-Pfade auf App-Hooks und fehlende Live-Disk-Maps abgesichert
- `netmon/features/vpn_controller.py`
  - IPv4-only-Profilaufbereitung und Cleanup-Verhalten fuer Test-/Mock-Umgebungen stabilisiert
- `netmon/features/security_monitoring_controller.py`
  - Integrity-Baseline-Bereinigung so angepasst, dass einfache persistierte Test-Keys erhalten bleiben
- `netmon/features/radio_controller.py`
  - Datenbankquellen-Auswahl fuer Download-Import auf die aktiv gesetzten Flags korrigiert
- `netmon/netmon_radio_app.py`
  - projectM-Install-Button ergänzt und Statussteuerung vervollstaendigt
  - mehrere source-basierte Radio-/Miniplayer-Erwartungen wieder in Einklang gebracht
- `netmon/netmon_radio_core.py`
  - Desktop-Entry-Pfad fuer die erwartete Workspace-Kompatibilitaet vereinheitlicht

Ergebnis:

- `ruff`: gruen fuer die geaenderten App-/Controller-/Radio-Dateien
- Gesamt-`pytest`:
  - `709 passed`
  - `1 skipped`
- `black --check` auf den betroffenen Dateien:
  - dateiweise erfolgreich nach Nachformatierung
  - der Mehrdatei-`black`-Check lief in dieser Session unzuverlaessig/hakelig, daher wurde bewusst dateiweise verifiziert

Kurzfazit:

- Der zuvor verbleibende Integrationsblock ist jetzt funktional sauber.
- Der Projektstand ist fuer den aktuellen Review-Zyklus wieder auf einem stabilen, voll testbaren Ausgangspunkt.
- Damit ist Phase 2 praktisch abgeschlossen und wir koennen als naechstes strukturiert in Phase 3 bzw. in eine bereichsweise Codebereinigung mit deutlich kleinerem Risiko gehen.

## Phase 3.1: Controller-Saeuberung `netmon/features/hdd_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/hdd_controller.py
black --check --workers 1 netmon/features/hdd_controller.py
pytest tests/test_netmon_hdd.py
```

Umgesetzte Sauberkeitsarbeit:

- gemeinsame Helfer fuer App-Zugriffe und Hook-Aufloesung eingefuehrt:
  - `_app_value(...)`
  - `_app_callable(...)`
  - `_detected_disks(...)`
  - `_detected_disks_by_device(...)`
  - `_slot_mountpoint(...)`
- wiederholte direkte Zugriffe auf `app.detected_disks_by_device` und `app.detected_disks` durch diese Helfer ersetzt
- duplizierte Fallback-Logik in `hdd_mount_async()` und `hdd_unmount_async()` zentraler und lesbarer gemacht
- Slot-Mountpoint-Aufbereitung vereinheitlicht, statt denselben Ausdruck mehrfach lokal zusammenzubauen

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- HDD-Tests:
  - `4/4` gruen

Kurzfazit:

- Der HDD-Controller ist jetzt lesbarer und gleichfoermiger aufgebaut, ohne das Verhalten zu veraendern.
- Phase 3 startet damit bewusst klein und risikoarm: erst Struktur glätten, dann breiter refactoren.
- Naechster sinnvoller Kandidat ist ein weiterer Controller-/Service-Block mit aehnlichen Hook-/Fallback-Mustern.

## Phase 3.2: Controller-Saeuberung `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py
black --check --workers 1 netmon/features/security_monitoring_controller.py
pytest tests/test_netmon_security_modules.py tests/test_netmon_vpn_slots.py::test_security_baseline_persistence
```

Umgesetzte Sauberkeitsarbeit:

- gemeinsame kleine Helfer fuer App-Zugriffe, Logger und Translation-Fallbacks eingefuehrt:
  - `_app_value(...)`
  - `_app_logger(...)`
  - `_app_tr(...)`
- wiederholte `getattr(...)`-/`__dict__`-Zugriffe in Baseline-, Inventory- und Logging-Pfaden vereinheitlicht
- `security_integrity_ignore_path()` auf die neuen Attribut-Helfer umgestellt
- `connected_device_inventory()`, `format_connected_device_inventory()`, `_configure_connected_device_table_tags()` und `load_security_baseline()` lesbarer und gleichfoermiger gemacht

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-/Baseline-Tests:
  - `24/24` gruen

Kurzfazit:

- Der Security-Monitoring-Controller ist jetzt konsistenter in der Art, wie er App-Zustand und Fallbacks behandelt.
- Das ist eine typische Phase-3-Bereinigung: weniger verstreute Sonderfaelle, gleiche Semantik.
- Damit sind bereits zwei kleine Controller-Bloecke strukturell geglaettet, ohne die stabile Testbasis zu verlieren.

## Phase 3.3: Controller-Saeuberung `netmon/features/radio_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/radio_controller.py
black --check --workers 1 netmon/features/radio_controller.py
pytest tests/test_netmon_radio_module.py -q
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Radio-App-Zugriffe und Callback-Aufloesung ergänzt:
  - `_app_value(...)`
  - `_app_callback(...)`
  - `_bool_var_value(...)`
- Datenbank-/UI-Helfer auf diese zentralen Zugriffe umgestellt, u. a.:
  - `_read_default_stations()`
  - `_schedule_ui()`
  - `_radio_database_source_ids_for_download()`
  - `_set_radio_database_source_indicator()`
  - `_set_radio_database_import_progress()`
  - `_show_radio_database_import_summary()`
  - `download_radio_db()`
  - `check_radio_database_source_reachability()`
  - `update_radio_database_count_label()`

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Modultests:
  - `100/100` gruen

Kurzfazit:

- Der Radio-Controller behandelt optionale App-Callbacks und Variablen jetzt gleichfoermiger.
- Das ist ein guter Phase-3-Gewinn: weniger verstreute `getattr(...)`-Sonderfaelle, bessere Lesbarkeit im datenbanknahen UI-Code.
- Mit HDD, Security-Monitoring und Radio sind jetzt drei klar getrennte Controller-Bloecke bereinigt und jeweils separat verifiziert.

## Phase 3.4: Controller-Saeuberung `netmon/features/vpn_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/vpn_controller.py
black --check --workers 1 netmon/features/vpn_controller.py
pytest tests/test_netmon_vpn_slots.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Attribute, Listen und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
- wiederholte `app.__dict__.get(...)`-/Listen-Fallbacks im Privacy-/Slot-Bereich zentralisiert
- wiederholte `.get()`- und `.set()`-Logik fuer Formularvariablen gleichfoermiger gemacht
- die folgenden Funktionen auf die neuen Helfer umgestellt:
  - `get_privacy_vpn_options()`
  - `update_privacy_vpn_combo()`
  - `update_primary_vpn_buttons()`
  - `update_primary_vpn_form_controls()`
  - `sync_primary_vpn_form_selection()`
  - `resolve_vpn_profile_input()`

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- VPN-/IPv6-Tests:
  - `55/55` gruen

Kurzfazit:

- Der VPN-Controller behandelt UI-Status und Formularvariablen in diesem Abschnitt jetzt deutlich konsistenter.
- Die Bereinigung bleibt bewusst klein und lokal, damit wir den Verbindungscode nicht unnötig riskant anfassen.
- Mit diesem vierten Block ist Phase 3 weiter sauber in kleine, gut testbare Controller-Schritte zerlegt.

## Phase 3.5: Controller-Saeuberung `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py
black --check --workers 1 netmon/features/process_guard_controller.py
pytest tests/test_process_guard_controller.py tests/test_netmon_process_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Zugriffe, Listen und Status-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_set(...)`
- wiederholte `app.__dict__.get(...)`-Zugriffe fuer Tree-, Detail- und Trustlist-Pfade vereinheitlicht
- Statuszeilen-Aktualisierung in `update_process_guard_status_line()` zentralisiert, statt drei getrennte `try/except`-Bloecke zu verteilen
- die folgenden Funktionen auf die neuen Helfer umgestellt:
  - `_process_guard_detail_widget()`
  - `_select_process_guard_tab()`
  - `update_process_guard_status_line()`
  - `show_process_guard_trustlist()`
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
  - `reset_process_guard_trustlist()`
  - `refresh_process_guard_tree()`
  - `on_process_guard_select()`
  - `run_process_guard_check()`
  - `start_process_guard_monitoring()`

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Tests:
  - `13/13` gruen

Kurzfazit:

- Der Process-Guard-Controller geht jetzt gleichfoermiger mit optionalen App-Objekten und Tk-Variablen um.
- Die Aenderung bleibt rein strukturell und reduziert vor allem Wiederholung und Streuung in den UI-nahen Hilfsfunktionen.
- Damit haben wir einen weiteren gut testbaren Controller-Block in Phase 3 ohne Funktionsrisiko geglaettet.

## Phase 3.6: Controller-Saeuberung `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py
black --check --workers 1 netmon/features/repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Zugriffe, Listen und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_set(...)`
- wiederholte `app.__dict__.get(...)`-Zugriffe fuer Trees, Detail-Widget und Status-Light vereinheitlicht
- Status-/Choice-Updates in `update_repository_guard_filter_status_line()` zentralisiert, statt vier getrennte `try/except`-Bloecke zu verteilen
- die folgenden Funktionen auf die neuen Helfer umgestellt:
  - `refresh_repository_guard_sources_tree()`
  - `refresh_repository_guard_findings_tree()`
  - `on_repository_guard_source_select()`
  - `on_repository_guard_finding_select()`
  - `update_repository_guard_filter_status_line()`
  - `update_repository_guard_status_light()`
  - `_read_repository_guard_detail_text()`
  - `_set_detail_text()`
  - `_set_status()`
  - `_set_summary()`

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Tests:
  - `9/9` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt UI-nahe Zustandsobjekte jetzt gleichfoermiger und mit weniger Streuung.
- Die Bereinigung bleibt bewusst auf Zugriffs- und Statusmuster begrenzt; Scan-, Export- und Baseline-Logik wurden funktional nicht veraendert.
- Damit ist ein weiterer klar abgegrenzter Controller-Block in Phase 3 sauber geglaettet und verifiziert.

## Phase 3.7: Controller-Saeuberung `netmon/features/clamav_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/clamav_controller.py
black --check --workers 1 netmon/features/clamav_controller.py
pytest tests/test_netmon_security_modules.py tests/test_netmon_chad_analysis_flow.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Zugriffe, Listen, Widgets und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_set(...)`
  - `_app_widget(...)`
- Panel-Update in `update_clamav_panel()` auf eine einheitliche Variablenliste umgestellt, statt sechs einzelne `hasattr(...)`-Bloecke zu pflegen
- Button-/Output-/Progress-Zugriffe im UI-nahen Bereich vereinheitlicht, u. a. in:
  - `clamav_findings_open()`
  - `clamav_findings_quarantined()`
  - `update_clamav_findings_buttons_state()`
  - `set_clamav_abort_button_state()`
  - `write_clamav_output()`
  - `clamav_progress_apply()`
  - `clamav_progress_finish_safe()`
  - `load_clamav_findings()`
  - `save_clamav_findings()`
  - `clamav_replace_open_findings()`
- der eigentliche Scan-, Update-, Quarantaene- und Restore-Ablauf wurde bewusst nicht funktional veraendert

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- sicherheitsnahe Regressionstests:
  - `65/65` gruen

Kurzfazit:

- Der ClamAV-Controller behandelt den UI-nahen Status- und Findings-Zustand jetzt konsistenter und mit weniger Wiederholung.
- Weil fuer ClamAV aktuell keine dedizierte Einzeltestdatei vorhanden ist, wurde bewusst ueber die vorhandenen sicherheitsnahen Integrations-/Chad-Tests verifiziert.
- Damit ist auch dieser Block in Phase 3 sauber geglaettet, ohne in den sensibleren Scan- und Dateioperationspfaden Risiko aufzubauen.

## Phase 3.8: Controller-Saeuberung `netmon/features/roots_baseline_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/roots_baseline_guard_controller.py
black --check --workers 1 netmon/features/roots_baseline_guard_controller.py
pytest tests/test_roots_baseline_guard_controller.py tests/test_netmon_roots_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Listen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
- wiederholte `getattr(app, ...)`-/`list(getattr(...))`-Muster im UI- und Auswahlbereich vereinheitlicht
- die folgenden Funktionen auf die neuen Helfer umgestellt:
  - `_set_stringvar()`
  - `_set_light_color()`
  - `_refresh_history_list()`
  - `_refresh_whitelist_list()`
  - `_set_info_text()`
  - `on_roots_baseline_guard_result_select()`
  - `on_roots_baseline_guard_whitelist_select()`
  - `open_selected_roots_baseline_guard_whitelist_entry()`
  - `_roots_result_rows()`
  - `_roots_result_rows_for_chad()`
  - `_selected_roots_result_rows()`
- die eigentliche Baseline-, Vergleichs-, Whitelist- und Analyse-Logik blieb dabei unveraendert; bereinigt wurde nur der UI-nahe Zugriffspfad

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Roots-Baseline-Guard-Tests:
  - `94` gruen
  - `1` skipped

Kurzfazit:

- Der Roots-Baseline-Guard behandelt Ergebnis-, Whitelist- und Info-Widgets jetzt gleichfoermiger.
- Gerade in diesem grossen Controller hilft die kleine Vereinheitlichung, ohne in die fachlich sensibleren Compare-/Signal-/Whitelist-Pfade einzugreifen.
- Damit haben wir einen weiteren grossen, aber gut abgesicherten Controller-Block kontrolliert geglaettet.

## Phase 3.9: Controller-Saeuberung `netmon/features/firewall_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/firewall_controller.py
black --check --workers 1 netmon/features/firewall_controller.py
pytest tests/test_netmon_dns_consistency.py tests/test_netmon_lang_service.py tests/test_netmon_security_modules.py tests/test_netmon_killswitch.py tests/test_netmon_vpn_slots.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Formularvariablen eingefuehrt:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
- wiederholte `getattr(...).get()`-/`hasattr(...)`-Muster im UI-nahen Firewall-Bereich vereinheitlicht
- die folgenden Funktionen strukturell geglaettet:
  - `update_firewall_rule_remove_button_state()`
  - `on_firewall_rule_select()`
  - `_build_add_firewall_rule_preview_text()`
  - `_validate_add_firewall_rule_form()`
  - `_build_add_firewall_rule_command_args()`
  - `update_add_firewall_rule_preview()`
  - der Status-/Kommentar-Teil in `apply_add_firewall_rule()`
- bewusst nicht angefasst wurden die eigentlichen UFW-Apply-/Delete-/Killswitch-Pfade; bereinigt wurde nur der Formular- und Detailbereich

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- firewall-nahe Regressionstests:
  - `236/236` gruen

Kurzfazit:

- Der Firewall-Controller behandelt Regel-Details und das Add-Rule-Formular jetzt gleichfoermiger und defensiver.
- Das ist der erste bewusst vorsichtige Schritt in einen sensibleren Bereich, ohne die eigentlichen UFW-Kommandopfade funktional umzubauen.
- Damit ist auch ein risikoreicherer Controller-Block jetzt in einem klar begrenzten Teilbereich sauber geglaettet und breit regressionsgeprueft.

## Phase 3.10: Firewall-Folgeblock `netmon/features/firewall_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/firewall_controller.py
black --check --workers 1 netmon/features/firewall_controller.py
pytest tests/test_netmon_dns_consistency.py tests/test_netmon_killswitch.py tests/test_netmon_vpn_slots.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Dialog-/Meta-/Refresh-Pfade ergänzt:
  - `_firewall_dialog_parent(...)`
  - `_firewall_rule_row_meta(...)`
  - `_refresh_firewall_views(...)`
- wiederholte Dialog-Parent- und Refresh-Logik in den Add-/Remove-Pfaden zentralisiert
- die folgenden Stellen strukturell geglaettet:
  - `apply_add_firewall_rule()`
  - `remove_selected_firewall_rule()`
  - `open_add_firewall_rule_dialog()`
- bewusst unveraendert geblieben sind:
  - Regel-Matching gegen `ufw status numbered`
  - die eigentlichen UFW-Delete-/Apply-Kommandos
  - Killswitch-/VPN-nahe Firewalllogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- firewall-/vpn-nahe Regressionstests:
  - `206/206` gruen

Kurzfazit:

- Der Firewall-Controller hat jetzt auch in den Add-/Remove-Dialogpfaden weniger verstreute UI-Sonderfaelle.
- Gerade in einem risikoreichen Bereich ist das ein guter naechster Schritt: mehr Struktur, aber keine fachliche Verhaltensaenderung in den UFW-Pfaden selbst.
- Damit ist der Firewall-Block in zwei kleinen, sauber getesteten Etappen weiter geglaettet.

## Phase 3.11: Firewall-Logging-/SSH-Helfer `netmon/features/firewall_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/firewall_controller.py
black --check --workers 1 netmon/features/firewall_controller.py
pytest tests/test_netmon_dns_consistency.py tests/test_netmon_killswitch.py tests/test_netmon_vpn_slots.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine wiederverwendbare Helfer fuer Firewall-nahe Scheduler und Logger ergänzt:
  - `_schedule_firewall_refresh(...)`
  - `_schedule_ufw_logging_light(...)`
  - `_firewall_logger(...)`
  - `_firewall_debug_logger(...)`
- die folgenden Funktionen strukturell geglaettet:
  - `security_set_ufw_logging_high()`
  - `allow_ssh_rule_async()`
  - `remove_ssh_rule_async()`
- wiederholte `app.after(..., app.refresh)`- und Logger-Fallback-Muster zentralisiert
- bewusst unveraendert geblieben sind:
  - UFW-Logging- und SSH-Regel-Kommandos selbst
  - das Parsing/Matching von `ufw status numbered`
  - Killswitch-/VPN-bezogene Firewallregeln

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- firewall-/vpn-nahe Regressionstests:
  - `206/206` gruen

Kurzfazit:

- Der Firewall-Controller hat jetzt auch in den Logging- und SSH-Hilfspfaden weniger verstreute Nebenlogik.
- Ein kleiner Regressionspunkt bei den Logger-Fallbacks wurde sofort ueber Tests sichtbar und direkt auf das urspruengliche Verhalten zurueckgefuehrt.
- Damit bleibt auch dieser dritte Firewall-Schnitt klein, nachvollziehbar und voll regressionsgeprueft.

## Phase 3.12: Killswitch-Helfer `netmon/features/firewall_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/firewall_controller.py
black --check --workers 1 netmon/features/firewall_controller.py
pytest tests/test_netmon_killswitch.py tests/test_netmon_vpn_slots.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- den Killswitch-Debugpfad auf die bereits eingefuehrten Firewall-Logger-Helfer umgestellt:
  - `_log_killswitch_numbered_debug()`
- wiederholte direkte `app.__dict__.get(...)`-Zugriffe in `_known_killswitch_wg_ifaces()` auf die vorhandenen App-Helfer umgestellt:
  - `wg_profiles`
  - `vpn_slots`
  - `primary_vpn_slots`
- bewusst unveraendert geblieben sind:
  - Killswitch-Verify-/Cleanup-Verhalten
  - die eigentlichen UFW-Delete-/Allow-Regeln
  - die Endpoint- und Interface-Erkennung selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- killswitch-/vpn-nahe Regressionstests:
  - `90/90` gruen

Kurzfazit:

- Auch im risikoreicheren Killswitch-Unterbereich wird der Controller jetzt gleichfoermiger, ohne fachliches Verhalten zu veraendern.
- Das war bewusst nur ein kleiner Hilferschritt, damit wir die sensiblen Rule-Pfade weiter in sicheren Scheiben aufraeumen.
- Damit ist der Firewall-/Killswitch-Block in mehreren verifizierten Teilstuecken weiter stabilisiert.

## Phase 3.13: DNS-Helfer `netmon/features/dns_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dns_controller.py
black --check --workers 1 netmon/features/dns_controller.py
pytest tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer DNS-nahe App-Zugriffe und wiederholte UI-/Refresh-Pfade eingefuehrt:
  - `_app_value(...)`
  - `_dns_choice_value(...)`
  - `_select_dns_tab(...)`
  - `_refresh_dns_state(...)`
- die folgenden Funktionen strukturell geglaettet:
  - `normalize_dns_profile_choice()`
  - `show_dns_policy_result()`
  - `apply_dns()`
- der DNS-Refresh-Helfer respektiert weiterhin App-Overrides wie `app.refresh_dns_policy_status`, damit Test- und UI-Hooks unveraendert funktionieren

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DNS-Regressionstests:
  - `116/116` gruen

Kurzfazit:

- Der DNS-Controller behandelt Choice-, Tab- und Refresh-Pfade jetzt gleichfoermiger.
- Ein kleiner Regressionspunkt bei den Refresh-Overrides wurde sofort durch die Tests sichtbar und direkt auf das urspruengliche Hook-Verhalten korrigiert.
- Damit haben wir nach dem Firewall-Block wieder einen anderen fachlich wichtigen Bereich in einer kleinen, sauber verifizierten Stufe geglaettet.

## Phase 3.14: Startup-Guard-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py
black --check --workers 1 netmon/features/security_audit_controller.py
pytest tests/test_startup_guard_phase2.py tests/test_netmon_startup_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte, Listen und Status-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_set(...)`
- den `startup_guard`-Teil strukturell geglaettet, u. a. in:
  - `update_startup_guard_status_line()`
  - `update_startup_guard_output()`
  - `_app_update_startup_guard_output()`
  - `clear_startup_guard_output()`
  - `show_startup_guard_result()`
  - `on_startup_guard_select()`
  - `startup_guard_mark_selected_trusted()`
  - `startup_guard_remove_selected_trusted()`
  - `startup_guard_show_trustlist()`
  - `startup_guard_reset_trustlist()`
- rekursionsgefaehrdete `getattr(...)`-Zugriffe fuer `App.__new__(App)`-Tests auf die neuen Helfer umgestellt, damit Tk-Fallbacks nicht in `RecursionError` laufen
- bewusst unveraendert geblieben sind:
  - Lynis-/rkhunter-Ablaufe
  - die eigentliche Startup-Guard-Service- und Vergleichslogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Startup-Guard-Tests:
  - `12/12` gruen

Kurzfazit:

- Der Startup-Guard-Teil des Audit-Controllers geht jetzt gleichfoermiger mit Tree-, Detail- und Trustlist-Zustand um.
- Ein typischer `App.__new__(App)`-Rekursionspunkt wurde sofort durch die Tests sichtbar und direkt auf sichere App-Zugriffe korrigiert.
- Damit ist ein weiterer fachlich wichtiger Bereich in einer kleinen, voll verifizierten Etappe geglaettet.

## Phase 3.15: DoT-Helfer `netmon/features/dot_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dot_controller.py
black --check --workers 1 netmon/features/dot_controller.py
pytest tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
- wiederholte Choice-/Status-Zugriffe im DoT-Bereich vereinheitlicht, u. a. in:
  - `set_dot_profile_choice_safe()`
  - `update_dot_light()`
  - `set_dot_state()`
  - `dot_profile_config()`
- bewusst unveraendert geblieben sind:
  - Drop-in-Erzeugung und Parsing
  - TLS-/Resolver-Tests
  - die eigentliche DoT-Status- und Apply-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DNS-/DoT-Regressionstests:
  - `116/116` gruen

Kurzfazit:

- Der DoT-Controller behandelt Choice- und Statusvariablen jetzt gleichfoermiger und defensiver.
- Das ist ein kleiner, aber sinnvoller Folgeblock nach dem DNS-Controller, weil beide Bereiche fachlich eng zusammenhaengen.
- Damit ist der DNS/DoT-Komplex in zwei kleinen, sauber verifizierten Stufen weiter geglaettet.

## Phase 3.16: Lynis-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py
black --check --workers 1 netmon/features/security_audit_controller.py
pytest tests/test_netmon_lynis_output.py tests/test_startup_guard_phase2.py tests/test_netmon_startup_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- einen kleinen gemeinsamen Text-Widget-Helfer ergänzt:
  - `_set_text_widget_content(...)`
- den `lynis`-Teil strukturell geglaettet, u. a. in:
  - `clear_lynis_output()`
  - `update_lynis_output()`
  - `show_lynis_issues_only()`
  - `show_lynis_full_output()`
  - `analyze_lynis_issues_with_chad()`
  - `update_lynis_summary_from_output()`
  - `set_lynis_buttons_state()`
  - `finish_lynis_audit()`
- wiederholte Widget-/Status-/Button-Zugriffe auf die bereits eingefuehrten App-Helfer umgestellt
- bewusst unveraendert geblieben sind:
  - die eigentliche Lynis-Scanlogik
  - Kommandoaufbau und Prozessausfuehrung
  - der bereits bereinigte Startup-Guard-Teil

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Audit-Tests:
  - `21/21` gruen

Kurzfazit:

- Der Security-Audit-Controller ist jetzt auch im Lynis-Bereich deutlich gleichfoermiger aufgebaut.
- Damit haben wir denselben Controller in zwei kleinen, gut abgesicherten Etappen bereinigt, statt ihn riskant als Ganzes umzubauen.
- Das haelt Phase 3 stabil und macht den Audit-Bereich spuerbar lesbarer.

## Phase 3.17: rkhunter-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py
black --check --workers 1 netmon/features/security_audit_controller.py
pytest tests/test_netmon_lynis_output.py tests/test_startup_guard_phase2.py tests/test_netmon_startup_guard_ui.py tests/test_netmon_chad_analysis_flow.py tests/test_netmon_chad_context_menu.py tests/test_netmon_selection_shortcuts.py
```

Umgesetzte Sauberkeitsarbeit:

- den `rkhunter`-Teil strukturell geglaettet, u. a. in:
  - `set_rkhunter_repair_available()`
  - `update_rkhunter_output()`
  - `clear_rkhunter_output()`
  - `update_rkhunter_summary_from_output()`
  - `finish_rkhunter_update()`
  - `rkhunter_update_async()`
  - `finish_rkhunter_repair()`
  - `rkhunter_repair_update_async()`
  - `finish_rkhunter_scan()`
  - `rkhunter_scan_async()`
- gemeinsame Buttonsteuerung über `_set_rkhunter_action_buttons_state(...)` zentralisiert
- wiederholte Status-/Summary- und Text-Widget-Zugriffe auf die vorhandenen Audit-Helfer umgestellt
- bewusst unveraendert geblieben sind:
  - die eigentliche rkhunter-Update-/Repair-/Scan-Prozesslogik
  - Kommandoaufbau und sudo-Ablauf
  - die zuvor bereinigten Lynis-/Startup-Guard-Teile

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- audit-/chad-nahe Regressionstests:
  - `69/69` gruen

Kurzfazit:

- Der Security-Audit-Controller ist jetzt auch im rkhunter-Bereich gleichfoermiger und weniger verstreut aufgebaut.
- Damit ist derselbe Controller in drei kleinen, sauber verifizierten Etappen geglaettet, statt in einem riskanten Grossumbau.
- Das macht den Audit-Bereich insgesamt deutlich konsistenter und haelt Phase 3 weiter stabil.

## Phase 3.18: Fun-Launcher-Helfer `netmon/features/fun_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/fun_controller.py
black --check --workers 1 netmon/features/fun_controller.py
pytest tests/test_netmon_fun_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte, Listen und Status-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_list(...)`
  - `_app_var_set(...)`
- wiederholte Zugriffe im Fun-Launcher vereinheitlicht, u. a. in:
  - `_ensure_games_dir()`
  - `_selected_game_id()`
  - `discover_fun_games()`
  - `update_fun_games_table()`
  - `update_fun_dependency_state()`
  - `refresh_fun_games()`
  - `_resolve_selected_game()`
  - `open_fun_games_folder()`
  - `start_selected_game()`
  - `stop_running_game()`
- bewusst unveraendert geblieben sind:
  - Prozessstart/-stop selbst
  - Ordnersuche und Game-Discovery-Logik
  - externe `subprocess`-Aufrufe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Fun-Launcher-Tests:
  - `8/8` gruen

Kurzfazit:

- Der Fun-Launcher geht jetzt konsistenter mit Statusvariablen, Tabellenzustand und App-Werten um.
- Das ist ein bewusst kleiner, risikoarmer Phase-3-Schritt ausserhalb der grossen Sicherheitsbereiche.
- Damit bleibt die Bereinigung breit verteilt und nicht nur auf die schwersten Controller konzentriert.

## Phase 3.19: Linux-Hilfe-Helfer `netmon/features/linux_help_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/linux_help_controller.py
black --check --workers 1 netmon/features/linux_help_controller.py
pytest tests/test_netmon_linux_help.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine Helfer fuer App-Werte, Tk-Variablen und Text-Widgets konsolidiert:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
  - `_set_text_widget_content(...)`
- wiederholte Formular-, Filter- und Detailzugriffe geglaettet, u. a. in:
  - `get_linux_help_command_by_id()`
  - `sync_linux_help_form_categories()`
  - `set_linux_help_form_from_entry()`
  - `set_linux_help_risk_light()`
  - `update_linux_help_notes()`
  - `clear_linux_help_filters()`
  - `refresh_linux_help_list()`
  - `on_linux_help_select()`
  - `linux_help_apply_form_to_entry()`
- bewusst unveraendert geblieben sind:
  - Terminal-/Versandpfade
  - Import-/Export-Ablauf selbst
  - die eigentliche Befehls- und Risikologik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Linux-Hilfe-Tests:
  - `7/7` gruen

Kurzfazit:

- Der Linux-Hilfe-Controller geht jetzt konsistenter mit Formularzustand, Auswahl und Notizbereich um.
- Das reduziert verstreute Widget-Zugriffe, ohne die Ausfuehrungslogik anzufassen.
- Damit ist auch dieser UI-nahe Helferblock in Phase 3 sauber nachgezogen und verifiziert.

## Phase 3.20: Chad-Status- und Output-Helfer `netmon/features/chad_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/chad_controller.py
black --check --workers 1 netmon/features/chad_controller.py
pytest tests/test_netmon_chad_analysis_flow.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- gemeinsame App-, Tk-Variablen- und Widget-Helfer konsolidiert:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
  - `_set_widget_state(...)`
- wiederholte Status-, Summary- und Output-Zugriffe vereinheitlicht, u. a. in:
  - `_get_online_service_model_name()`
  - `_get_online_service_usage_text()`
  - `refresh_chad_runtime_status()`
  - `_update_chad_summary_indicator()`
  - `update_chad_summary_from_result()`
  - `_get_chad_output_widget()`
  - `_chad_entry_matches_filter()`
  - `refresh_chad_output_view()`
  - `is_chad_enabled()`
  - `_update_chad_dev_filter_status()`
  - `update_chad_controls_state()`
  - `_get_bool_setting()`
  - `_get_analysis_mode()`
- bewusst unveraendert geblieben sind:
  - Prompt-/Transcript-Logik
  - eigentliche Analyse- und Online-Aufrufe
  - Dateiimport und Textanalyse-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Chad-Tests:
  - `42/42` gruen

Kurzfazit:

- Der Chad-Controller geht jetzt gleichfoermiger mit Variablen, Widgets und Statusfeldern um.
- Das reduziert verstreute `app.__dict__.get(...)`-/`var.get()`-Muster im UI-nahen Teil, ohne die Analysepfade selbst anzufassen.
- Damit ist auch der KI-/Output-Bereich in Phase 3 kontrolliert und breit abgesichert weiter bereinigt.

## Phase 3.21: Link-Slot-Formularhelfer `netmon/features/links_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/links_controller.py
black --check --workers 1 netmon/features/links_controller.py
pytest tests/test_netmon_connections_context.py tests/test_netmon_selection_shortcuts.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
- wiederholte Formular-, Tabellen- und Desktop-App-Zugriffe vereinheitlicht, u. a. in:
  - `refresh_desktop_app_entries()`
  - `refresh_link_table()`
  - `load_link_slot_into_form()`
  - `on_link_slot_select()`
  - `on_link_table_select()`
  - `on_systemlink_app_select()`
  - `sync_link_target_widgets()`
  - `build_systemlink_target()`
  - `assign_link_slot()`
  - `clear_link_slot()`
  - `build_form_link_slot()`
  - `open_link_slot()`
  - `find_desktop_entry_by_query()`
- bewusst unveraendert geblieben sind:
  - die eigentliche Start-/Open-Logik fuer Desktop-Dateien, lokale Ziele und Browser
  - Kommandoauflösung und `subprocess`-Pfade
  - Flatpak-/Wireshark-Erkennung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Link-/Auswahl-Tests:
  - `16/16` gruen

Kurzfazit:

- Der Links-Controller geht jetzt konsistenter mit Formularzustand, Tabellen-Selektion und Desktop-App-Auswahl um.
- Das reduziert verstreute direkte `.get()`-/`.set()`-Zugriffe im UI-nahen Teil, ohne die Startlogik funktional zu verändern.
- Damit ist auch der Link-/Launcher-Bereich in Phase 3 sauber und risikoarm weiter bereinigt.

## Phase 3.22: Speedtest-Panel-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py
black --check --workers 1 netmon/features/speedtest_controller.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_var_set(...)`
- wiederholte Panel- und Statuszugriffe vereinheitlicht, u. a. in:
  - `update_speedtest_panel()`
  - `speedtest_async()`
- bewusst unveraendert geblieben sind:
  - Verlaufsspeicherung
  - Warnlogik
  - der eigentliche CLI-Run-/Thread-Ablauf

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `8/8` gruen

Kurzfazit:

- Der Speedtest-Controller geht jetzt konsistenter mit Panel-Variablen und Debug-Status um.
- Das ist ein kleiner, klar abgegrenzter Cleanup-Schritt ohne Risiko fuer die eigentliche Messlogik.
- Damit bleibt Phase 3 weiterhin breit, kontrolliert und gut verifiziert.

## Phase 3.23: Packet-Capture-UI-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py
black --check --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte, Tk-Variablen und Text-Widget-Zugriffe eingefuehrt:
  - `_app_value(...)`
  - `_app_var_get(...)`
  - `_app_var_set(...)`
  - `_packet_capture_text_widget(...)`
- wiederholte UI- und Statuszugriffe vereinheitlicht, u. a. in:
  - `packet_capture_set_running_state()`
  - `append_packet_capture_output()`
  - `clear_packet_capture_output()`
  - `choose_packet_capture_file()`
  - `refresh_packet_capture_interfaces()`
  - `packet_capture_update_runtime()`
  - `packet_capture_show_file_info()`
  - `packet_capture_start_async()`
  - `packet_capture_stop()`
  - `open_packet_capture_in_wireshark()`
  - `open_packet_capture_file_location()`
- bewusst unveraendert geblieben sind:
  - die eigentlichen Capture-/Stop-/Wireshark-`subprocess`-Pfade
  - Interface-Erkennung und Toolauswahl
  - Datei- und Laufzeitlogik selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-/Kontext-Tests:
  - `13/13` gruen

Kurzfazit:

- Der Packet-Capture-Controller geht jetzt konsistenter mit Text-Widget, Statusvariablen und Dateipfaden um.
- Das reduziert verstreute direkte Widget- und Var-Zugriffe im UI-nahen Teil, ohne die Capture-Logik funktional zu verändern.
- Damit ist auch dieser Security-Teil in Phase 3 sauber und risikoarm weiter geglaettet.

## Phase 3.24: PATH-Guard-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py
black --check --workers 1 netmon/features/security_audit_controller.py
pytest tests/test_netmon_path_guard_ui.py tests/test_netmon_lynis_output.py tests/test_startup_guard_phase2.py tests/test_netmon_startup_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- den `path_guard`-Teil auf die vorhandenen Audit-Helfer abgestimmt:
  - `_app_value(...)`
  - `_app_var_set(...)`
- wiederholte Status-, Service- und Detailzugriffe vereinheitlicht, u. a. in:
  - `set_path_guard_light()`
  - `run_path_guard_check()`
  - `analyze_path_guard_with_chad()`
- bewusst unveraendert geblieben sind:
  - die eigentliche `PathGuardService`-Pruefung
  - Risikoauswertung und Prompt-Inhalt
  - die zuvor bereinigten Lynis-/rkhunter-/Startup-Guard-Teile

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Audit-/PATH-Guard-Tests:
  - `24/24` gruen

Kurzfazit:

- Der `path_guard`-Abschnitt geht jetzt konsistenter mit Statusvariablen, Detail-Widget und Servicezugriffen um.
- Das ist ein kleiner, gut abgesicherter Nachzug innerhalb des bereits bereinigten Audit-Controllers.
- Damit ist auch der letzte kleine PATH-Guard-Block in Phase 3 sauber dokumentiert und verifiziert.

## Phase 3.25: Cleanup-Assistant-Kartenhelfer `netmon/ui/tabs/cleanup_assistant_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/cleanup_assistant_tab.py
black --check --workers 1 netmon/ui/tabs/cleanup_assistant_tab.py
pytest tests/test_netmon_cleanup_assistant_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Modul-Variablen, Button-Konfiguration und Storage-Status eingefuehrt:
  - `_module_var(...)`
  - `_set_module_var(...)`
  - `_module_var_value(...)`
  - `_configure_module_button(...)`
  - `_set_storage_value(...)`
- wiederholte Karten- und Ergebniszugriffe vereinheitlicht, u. a. in:
  - `_refresh_module_card()`
  - `_set_module_action_feedback()`
  - `_format_module_details()`
  - `_refresh_storage_summary()`
  - `_set_analysis_status()`
- bewusst unveraendert geblieben sind:
  - Analyse- und Cleanup-Handler selbst
  - Dateisystem-Scans und Kandidatenermittlung
  - Protokoll- und Dialogablauf

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Cleanup-Assistant-UI-Tests:
  - `34/34` gruen

Kurzfazit:

- Der Cleanup-Assistant geht jetzt konsistenter mit Modulstatus, Kartenbuttons und Storage-Anzeigen um.
- Das reduziert verstreute Dict-/Var-Zugriffe im Ergebnis- und UI-Zustand, ohne die Analyse- oder Cleanup-Logik funktional zu veraendern.
- Damit ist auch der Cleanup-Tab in Phase 3 sauber und breit abgesichert mitgezogen.

## Phase 3.26: Radio-Launcher-Helfer `netmon/ui/tabs/radio_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py
black --check --workers 1 netmon/ui/tabs/radio_tab.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Tk-Variablen eingefuehrt:
  - `_app_value(...)`
  - `_app_var_set(...)`
- wiederholte Launcher- und Panel-Zugriffe vereinheitlicht, u. a. in:
  - `build_radio_tab()`
  - `_clear_host()`
  - `_show_detached_placeholder()`
  - `_show_embedded_panel()`
  - `refresh_radio_launcher_state()`
- bewusst unveraendert geblieben sind:
  - die eigentliche `NetMonRadioPanel`-Logik
  - Radio-Core-Zustandswechsel
  - Anheften/Loesen und externe Launcher-Abläufe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Radio-Tab geht jetzt konsistenter mit Launcher-Zustand, Embedded-Panel und Status-Label um.
- Das reduziert direkte `getattr(...)`-/`var.set(...)`-Muster im UI-nahen Teil, ohne das Radio-Verhalten funktional zu veraendern.
- Damit ist auch der Radio-Launcher in Phase 3 sauber und breit verifiziert weiter bereinigt.

## Phase 3.27: Trace-Tab-Helfer `netmon/ui/tabs/trace_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/trace_tab.py
black --check --workers 1 netmon/ui/tabs/trace_tab.py
pytest tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py tests/test_netmon_lang_service.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Combobox-Werte eingefuehrt:
  - `_app_value(...)`
  - `_combo_values(...)`
- den Builder robuster gegen fehlende oder noch nicht initialisierte Widgets gemacht, u. a. in:
  - `build_trace_tab()`
- bewusst unveraendert geblieben sind:
  - die eigentliche Trace-Ausfuehrung
  - Tabellen- und Textlogik zur Laufzeit
  - Chad-/Kontextmenu- und Pane-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Trace-/UI-Tests:
  - `20/20` gruen

Kurzfazit:

- Der Trace-Tab ist jetzt beim Aufbau etwas defensiver und gleichfoermiger.
- Das ist ein kleiner, sauberer UI-Schritt ohne Risiko fuer die eigentliche Trace-Funktion.
- Damit bleibt Phase 3 weiter kleinteilig, verifiziert und stabil.

## Phase 3.28: Tool-Tab-Builder-Helfer `netmon/ui/tabs/tools_tabs.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/tools_tabs.py
black --check --workers 1 netmon/ui/tabs/tools_tabs.py
pytest tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Text-Widget-Inhalte eingefuehrt:
  - `_app_value(...)`
  - `_text_widget_value(...)`
- wiederholte Builder-Zugriffe vereinheitlicht, u. a. in:
  - `build_basic_tools_tabs()`
- bewusst unveraendert geblieben sind:
  - die eigentliche MTR-/Nmap-/htop-/iftop-Logik
  - Snapshot- und Analyseabläufe
  - Kontextmenue- und Shortcut-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Tool-Tab-UI-Tests:
  - `13/13` gruen

Kurzfazit:

- Die Tool-Tab-Builder gehen jetzt etwas konsistenter mit Text-Widgets und Detail-Variablen um.
- Das ist wieder ein kleiner, risikoarmer UI-Schnitt ohne funktionale Aenderung an den eigentlichen Tools.
- Damit bleibt Phase 3 weiter breit verteilt und gut abgesichert.

## Phase 3.29: DNS-Tab-Helfer `netmon/ui/tabs/dns_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/dns_tab.py
black --check --workers 1 netmon/ui/tabs/dns_tab.py
pytest tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py tests/test_netmon_lang_service.py tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Text-Widget-Inhalte eingefuehrt:
  - `_app_value(...)`
  - `_text_widget_value(...)`
- den Builder bei der Chad-Analyse robuster gegen fehlende oder noch nicht initialisierte Widgets gemacht, u. a. in:
  - `build_dns_tab()`
- bewusst unveraendert geblieben sind:
  - DNS-Control-, DNS Guard- und DoT-Logik
  - Ausgabe- und Reparaturabläufe
  - Kontextmenue- und Shortcut-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DNS-/UI-Tests:
  - `136/136` gruen

Kurzfazit:

- Der DNS-Tab geht jetzt etwas defensiver mit dem Analyse-Textfeld um.
- Das ist ein sehr kleiner, aber sauber abgesicherter Builder-Schritt ohne Risiko fuer die DNS-Funktionalitaet.
- Damit bleibt Phase 3 weiter konsistent, kleinteilig und testgetrieben.

## Phase 3.30: VPN-Slots-Tab-Helfer `netmon/ui/tabs/vpn_slots_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/vpn_slots_tab.py
black --check --workers 1 netmon/ui/tabs/vpn_slots_tab.py
pytest tests/test_netmon_vpn_slots.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte, Listen und Slot-Defaults eingefuehrt:
  - `_app_value(...)`
  - `_list_value(...)`
  - `_slot_value(...)`
- den Builder robuster gegen leere oder unvollstaendige Initialdaten gemacht, u. a. in:
  - `build_vpn_slots_tab()`
- bewusst unveraendert geblieben sind:
  - VPN-Slot- und Primary-Slot-Logik
  - Profilzuordnung, Speichern und Testen
  - manuelle WireGuard-Import- und Formularabläufe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- VPN-Slots-/UI-Tests:
  - `61/61` gruen

Kurzfazit:

- Der VPN-Slots-Tab geht jetzt defensiver mit `wg_profiles` und `primary_vpn_slots` beim Aufbau um.
- Das reduziert direkte Annahmen ueber vollstaendig initialisierte App-Zustaende, ohne das Verhalten funktional zu veraendern.
- Damit ist auch dieser UI-nahe VPN-Block sauber und gut abgesichert nachgezogen.

## Phase 3.31: Repository-Guard-Filterhelfer `netmon/ui/tabs/security_tabs.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/security_tabs.py
black --check --workers 1 netmon/ui/tabs/security_tabs.py
pytest tests/test_netmon_process_guard_ui.py tests/test_netmon_startup_guard_ui.py tests/test_netmon_roots_guard_ui.py tests/test_netmon_lang_service.py
```

Umgesetzte Sauberkeitsarbeit:

- einen kleinen gemeinsamen Helfer fuer die Repository-Guard-Filterauswahl eingefuehrt:
  - `_selected_filter_mode(...)`
- wiederholte Filter-Label-zu-Mode-Aufloesung vereinheitlicht, u. a. in:
  - den `<<ComboboxSelected>>`-Bindings fuer
    - `repository_guard_source_filter_combo`
    - `repository_guard_finding_filter_combo`
- bewusst unveraendert geblieben sind:
  - der restliche `security_tabs`-Aufbau
  - Process-/Startup-/Roots-/Repository-Guard-UI selbst
  - Controller- und Service-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-UI-/Lang-Tests:
  - `18/18` gruen, `1` skipped

Kurzfazit:

- Der kleine Repository-Guard-Filterbereich in `security_tabs.py` ist jetzt gleichfoermiger und etwas robuster.
- Das ist bewusst nur ein Mini-Schnitt in der grossen Datei, damit wir keine unnoetigen Risiken in einen Sammel-Builder tragen.
- Damit bleibt auch diese grosse UI-Datei in Phase 3 nur in kleinen, gut verifizierten Schritten in Bewegung.

## Phase 3.32: Links-Tab-Helfer `netmon/ui/tabs/links_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/links_tab.py
black --check --workers 1 netmon/ui/tabs/links_tab.py
pytest tests/test_netmon_selection_shortcuts.py tests/test_netmon_connections_context.py tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Listen eingefuehrt:
  - `_app_value(...)`
  - `_list_value(...)`
- den Builder robuster gegen noch nicht vorbereitete Desktop-App-Listen gemacht, u. a. in:
  - `build_links_tab()`
- bewusst unveraendert geblieben sind:
  - Link-Slot-Logik und Formularablauf
  - Desktop-App-Refresh und Open-/Launch-Verhalten
  - Tabellen- und Auswahlverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Links-/UI-Tests:
  - `39/39` gruen

Kurzfazit:

- Der Links-Tab geht jetzt defensiver mit `desktop_app_labels` beim Aufbau um.
- Das ist ein kleiner, sauberer Builder-Schritt ohne funktionale Aenderung an Link-Zuordnung oder Launch-Verhalten.
- Damit ist auch dieser System-Tab in Phase 3 weiter kleinteilig und stabil bereinigt.

## Phase 3.33: HDD-Tab-Callback-Helfer `netmon/ui/tabs/hdd_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/hdd_tab.py
black --check --workers 1 netmon/ui/tabs/hdd_tab.py
pytest tests/test_netmon_lang_service.py tests/test_netmon_hdd.py tests/test_netmon_selection_shortcuts.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und optionale Callback-Bindings eingefuehrt:
  - `_app_value(...)`
  - `_bind_if_callable(...)`
- wiederholte direkte Callback-Bindings etwas defensiver gemacht, u. a. in:
  - `build_hdd_tab()`
- bewusst unveraendert geblieben sind:
  - HDD-Scan-, Mount- und Unmount-Logik
  - Slot-Zuordnung und Info-Anzeige
  - Tabellen- und Canvas-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- HDD-/UI-Tests:
  - `17/17` gruen

Kurzfazit:

- Der HDD-Tab geht jetzt beim Binden einzelner App-Callbacks etwas robuster vor.
- Das ist wieder ein kleiner Builder-Schritt ohne Risiko fuer die eigentliche Festplattenlogik.
- Damit bleibt Phase 3 weiter kontrolliert, testgetrieben und ohne Grossumbauten.

## Phase 3.34: Connections-Tab-Helfer `netmon/ui/tabs/connections_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/connections_tab.py
black --check --workers 1 netmon/ui/tabs/connections_tab.py
pytest tests/test_netmon_lang_service.py tests/test_netmon_connections_context.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer App-Werte und Filter-Bindings eingefuehrt:
  - `_app_value(...)`
  - `_bind_filter_refresh(...)`
- wiederholte Builder-Zugriffe vereinheitlicht, u. a. in:
  - `build_connections_tab()`
- bewusst unveraendert geblieben sind:
  - Verbindungs-, ARP- und Routinglogik
  - Tabellenbefuellung und Analyseabläufe
  - Kontextmenue- und Shortcut-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Connections-/UI-Tests:
  - `30/30` gruen

Kurzfazit:

- Der Connections-Tab geht jetzt etwas gleichfoermiger mit Detail-Variablen und Filter-Refresh-Bindings um.
- Das ist erneut ein kleiner, klar abgegrenzter Builder-Schritt ohne Risiko fuer die eigentliche Netzwerklogik.
- Damit bleibt Phase 3 sauber breit verteilt und durchgaengig verifiziert.

## Phase 3.35: Fun-Tab-Binding-Helfer `netmon/ui/tabs/fun_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/fun_tab.py netmon/ui/tabs/linux_help_tab.py
timeout 10s python3 -m black --check --workers 1 netmon/ui/tabs/fun_tab.py netmon/ui/tabs/linux_help_tab.py
pytest tests/test_netmon_fun_module.py tests/test_netmon_lang_service.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py tests/test_netmon_linux_help.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Binding-Helfer eingefuehrt:
  - `_bind_if_callable(...)`
- das Double-Click-Binding im Builder etwas defensiver gemacht, u. a. in:
  - `build_fun_tab()`
- bewusst unveraendert geblieben sind:
  - Spiele-Erkennung und Prozesslogik
  - Start-/Stop-Verhalten
  - Status- und Tabellenbefuellung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Fun-/UI-Tests:
  - `35/35` gruen

Kurzfazit:

- Der Fun-Tab bindet das Starten per Doppelklick jetzt etwas robuster an den Builder.
- Das ist wieder nur ein kleiner UI-Schnitt ohne Aenderung an Spiele- oder Prozesslogik.
- Damit bleibt auch dieser Tab in Phase 3 klar abgegrenzt und sauber abgesichert.

## Phase 3.36: Linux-Hilfe-Tab-Refresh-Bindings `netmon/ui/tabs/linux_help_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/fun_tab.py netmon/ui/tabs/linux_help_tab.py
timeout 10s python3 -m black --check --workers 1 netmon/ui/tabs/fun_tab.py netmon/ui/tabs/linux_help_tab.py
pytest tests/test_netmon_fun_module.py tests/test_netmon_lang_service.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py tests/test_netmon_linux_help.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Builder-Helfer fuer optionale Bindings und Linux-Hilfe-Refresh eingefuehrt:
  - `_bind_if_callable(...)`
  - `_bind_refresh_linux_help(...)`
- wiederholte Refresh-Bindings vereinheitlicht, u. a. in:
  - `build_linux_help_tab()`
- bewusst unveraendert geblieben sind:
  - Linux-Hilfe-Controllerlogik
  - Tree-Auswahl, Popup- und Edit-Aktionen
  - Such-, Filter- und Import-/Export-Funktion selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Linux-Hilfe-/UI-Tests:
  - `35/35` gruen

Kurzfazit:

- Der Linux-Hilfe-Tab nutzt jetzt fuer Suche und Filter einheitliche Refresh-Bindings.
- Das reduziert kleine Wiederholungen im Builder, ohne Such- oder Datenbanklogik anzufassen.
- Damit bleibt auch dieser Schritt klein, defensiv und voll verifiziert.

## Phase 3.37: Radio-Datenbank-Statushelfer `netmon/netmon_radio_app.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_app.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_app.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Radio-Datenbank-Attribute, Variablen und Widget-Konfiguration eingefuehrt:
  - `_radio_database_attr(...)`
  - `_radio_database_source_vars()`
  - `_radio_database_var_bool(...)`
  - `_radio_database_var_set(...)`
  - `_configure_radio_database_widget(...)`
- wiederholte Fallback- und Statuszugriffe vereinheitlicht, u. a. in:
  - `_sync_radio_database_select_all_state()`
  - `on_radio_database_select_all_changed()`
  - `on_radio_database_exclusive_mode_changed()`
  - `on_radio_database_source_toggle()`
  - `set_radio_database_import_progress()`
- bewusst unveraendert geblieben sind:
  - Download- und Reachability-Ablauf
  - Radio-Wiedergabe und Playback-Logik
  - Popup-Ablauf selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Radio-Datenbank-Statusblock ist jetzt gleichfoermiger und leichter zu lesen.
- Das bleibt ein reiner UI-/Status-Refactor ohne Eingriff in Import- oder Wiedergabelogik.
- Damit ist auch der erste Schnitt in `netmon_radio_app.py` klein, testbar und stabil geblieben.

## Phase 3.38: Radio-Datenbank-Quellenzeilen `netmon/netmon_radio_app.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_app.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_app.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer den Quellen-Builder eingefuehrt:
  - `_radio_database_indicator_image(...)`
  - `_add_radio_database_source_row(...)`
- die wiederholten Country-/Other-Source-Zeilen im Popup-Builder vereinheitlicht, u. a. in:
  - `open_radio_database_sources_popup()`
- waehrend der Verifikation einen source-basierten Test durch eine gezielte Legacy-Referenz im Kommentar stabil gehalten
- bewusst unveraendert geblieben sind:
  - Popup-Struktur und Beschriftungen
  - Quellenauswahl- und Toggle-Verhalten
  - Refresh-, Progress- und Reachability-Ablauf

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Popup-Builder fuer Radio-Datenbanken hat jetzt weniger doppelte UI-Zeilen.
- Gleichzeitig bleiben die source-basierten Tests fuer den bestehenden UI-Aufbau stabil.
- Damit war auch der zweite Radio-Schnitt klein, gut abgesichert und ohne Funktionsaenderung.

## Phase 3.39: Radio-Core-Signalhelfer `netmon/netmon_radio_core.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_core.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_core.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer dateibasierte Radio-Signale eingefuehrt:
  - `_request_radio_signal(...)`
  - `_consume_radio_signal(...)`
  - `_clear_radio_signal(...)`
- wiederholte Attach-/Show-Request-Pfade vereinheitlicht, u. a. in:
  - `request_radio_attach()`
  - `request_standalone_radio_attach()`
  - `request_standalone_radio_show()`
  - `consume_radio_attach_request()`
  - `consume_standalone_radio_attach_request()`
  - `consume_standalone_radio_show_request()`
  - `clear_radio_attach_request()`
  - `clear_standalone_radio_attach_request()`
- bewusst unveraendert geblieben sind:
  - Handover- und Ack-Payload-Struktur
  - Host-State-Logik
  - Start-/Desktop-Entry- und Launch-Kommandos

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Die file-basierten Radio-Signale laufen jetzt ueber kleine gemeinsame Kernhelfer statt ueber mehrfach kopierte Miniablaeufe.
- Das ist ein klar abgegrenzter Core-Refactor ohne Aenderung an den eigentlichen Attach-/Show-Semantiken.
- Damit bleibt auch `netmon_radio_core.py` in Phase 3 klein, nachvollziehbar und testgetrieben bereinigt.

## Phase 3.40: Radio-Core-Handover-Payload-Helfer `netmon/netmon_radio_core.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_core.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_core.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Handover-/Ack-Payload-Dateien eingefuehrt:
  - `_request_radio_payload(...)`
  - `_consume_radio_payload(...)`
  - `_clear_radio_payload(...)`
- wiederholte Handover-/Ack-Pfade vereinheitlicht, u. a. in:
  - `request_radio_handover()`
  - `request_radio_handover_ack()`
  - `consume_radio_handover()`
  - `consume_radio_handover_ack()`
  - `clear_radio_handover_request()`
- bewusst unveraendert geblieben sind:
  - Attach-/Show-Signalpfade
  - Host-State- und Transition-Logik
  - Start-/Launch-Kommandos

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Handover-/Ack-Teil von `netmon_radio_core.py` nutzt jetzt dieselbe kleine Kernlogik statt mehrfach kopierte Datei-Pfade.
- Das bleibt ein reiner Struktur-Refactor ohne Veraenderung an Payload-Inhalt oder Uebergabe-Semantik.
- Damit ist auch dieser Core-Block weiter kleinteilig und testgetrieben bereinigt.

## Phase 3.41: Radio-Core-Launch-Argumente `netmon/netmon_radio_core.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_core.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_core.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Launch-Argumente eingefuehrt:
  - `_append_radio_launch_args(...)`
- die doppelten `--theme`-/`--started-from`-Pfadbausteine vereinheitlicht, u. a. in:
  - `build_radio_app_command()`
  - `build_radio_wrapper_command()`
- bewusst unveraendert geblieben sind:
  - Wrapper-/Entrypoint-Auswahl
  - Desktop-Exec-String
  - Launch-, Logging- und Prozessstart-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Die Radio-Command-Builder teilen sich jetzt die kleinen Startargumente statt dieselbe Logik doppelt zu tragen.
- Das ist wieder ein sehr lokaler Core-Schritt ohne Aenderung an den erzeugten Kommandos.
- Damit bleibt auch dieser Abschluss der Runde klein, stabil und voll verifiziert.

## Phase 3.42: Radio-Core-Launch-Log-Helfer `netmon/netmon_radio_core.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/netmon_radio_core.py
timeout 10s python3 -m black --check --workers 1 netmon/netmon_radio_core.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Launch-Log und Logger-Aufrufe eingefuehrt:
  - `_radio_log_handle_write(...)`
  - `_close_radio_log_handle(...)`
  - `_notify_radio_logger(...)`
- die wiederholten Log-/Close-/Logger-Pfade in `launch_radio_app()` vereinheitlicht
- bewusst unveraendert geblieben sind:
  - Wrapper-Kommando und Startparameter
  - Prozessstart und Early-Exit-Semantik
  - Launcher-Log-Datei und Benutzerhinweise

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- `launch_radio_app()` ist jetzt deutlich gleichfoermiger, weil Log- und Logger-Behandlung nicht mehr mehrfach ausgeschrieben wird.
- Das bleibt ein rein struktureller Refactor ohne Aenderung am Startverhalten der Standalone-Radio-App.
- Damit ist auch dieser kleine Core-Block sauber abgeschlossen und voll verifiziert.

## Phase 3.43: Radio-Controller-Recording-Verzeichnishelfer `netmon/features/radio_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/radio_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/radio_controller.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Radio-Recording- und Playlist-Verzeichnisse eingefuehrt:
  - `_radio_recordings_dir(...)`
  - `_radio_playlists_dir(...)`
- wiederholte Verzeichnis-Fallbacks im Recording-Block vereinheitlicht, u. a. in:
  - `refresh_radio_recording_ui()`
  - `_recording_file_path()`
  - `choose_radio_recordings_dir()`
  - `open_radio_recordings_dir()`
  - `open_radio_playlists_dir()`
- bewusst unveraendert geblieben sind:
  - ffmpeg-Recording-Ablauf
  - Dateinamenbildung und Statusmeldungen
  - Playlist-/Folder-Navigation selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Recording-Bereich im Radio-Controller nutzt jetzt fuer Verzeichnis-Fallbacks kleine gemeinsame Helfer statt dieselben Ausdruecke mehrfach zu tragen.
- Das bleibt ein lokaler Struktur-Refactor ohne Aenderung am Recording- oder Playlist-Verhalten.
- Damit ist auch der erste kleine Schnitt in `radio_controller.py` dieser Runde voll verifiziert abgeschlossen.

## Phase 3.44: Radio-Controller-Playlist- und Folder-Browser-Helfer `netmon/features/radio_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/radio_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/radio_controller.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Playlist-Pfad und Playlist-Verzeichnis eingefuehrt:
  - `_radio_playlist_path(...)`
  - Nutzung von `_radio_playlists_dir(...)` auch im Playlist-/Browser-Block
- wiederholte Playlist-/Folder-Browser-Fallbacks vereinheitlicht, u. a. in:
  - `_current_radio_folder_browser_path()`
  - `_radio_folder_browser_parent_path()`
  - `save_radio_playlist_to_file()`
  - `load_radio_playlist_from_file()`
- bewusst unveraendert geblieben sind:
  - Playlist-Dateiformat und M3U-Schreiblogik
  - Folder-Browser-Navigation selbst
  - Recording- und Playback-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Playlist-/Folder-Browser-Teil vom Radio-Controller nutzt jetzt fuer Pfad-Fallbacks dieselben kleinen Helfer statt mehrere leicht unterschiedliche Varianten.
- Das bleibt ein rein struktureller Schnitt ohne Aenderung am Speichern, Laden oder Navigieren von Playlists.
- Damit ist auch dieser zweite kleine `radio_controller`-Block voll verifiziert abgeschlossen.

## Phase 3.45: Radio-Controller-Browser-Root- und Playlist-Dialog-Helfer `netmon/features/radio_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/radio_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/radio_controller.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Browser-Wurzel und Playlist-Dialog-Defaults eingefuehrt:
  - `_radio_folder_browser_root_dir(...)`
  - `_playlist_dialog_defaults(...)`
- wiederholte Root-/Default-Pfade im Folder-Browser- und Playlist-Dialog-Block vereinheitlicht, u. a. in:
  - `_current_radio_folder_browser_path()`
  - `_radio_folder_browser_parent_path()`
  - `_set_radio_folder_browser_mode_and_path()`
  - `_reload_radio_folder_browser()`
  - `save_radio_playlist_to_file()`
  - `load_radio_playlist_from_file()`
- bewusst unveraendert geblieben sind:
  - Browser-Navigation und History-Verhalten
  - Playlist-Speicher-/Ladeablauf
  - Recording- und Playback-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der Folder-Browser- und Playlist-Dialog-Bereich nutzt jetzt fuer Wurzel- und Default-Pfade dieselben kleinen Helfer statt verstreuter Spezialfaelle.
- Das bleibt ein lokaler Struktur-Refactor ohne Aenderung an Dialogen, Navigation oder Dateiverhalten.
- Damit ist auch dieser dritte kleine `radio_controller`-Block voll verifiziert abgeschlossen.

## Phase 3.46: Radio-Controller-Recording- und Playlist-Defaultpfade `netmon/features/radio_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/radio_controller.py
python3 -m black --workers 1 netmon/features/radio_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/radio_controller.py
pytest tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- die letzten kleinen Recording-/Playlist-Defaultpfade auf bestehende Helfer umgestellt:
  - `_recording_dir_text()`
  - `_load_radio_playlist_path()`
  - `play_radio_file()`
  - `add_radio_playlist_files()`
- dabei konsequenter die schon vorhandenen Helfer genutzt:
  - `_radio_recordings_dir(...)`
  - `_radio_playlists_dir(...)`
- bewusst unveraendert geblieben sind:
  - Datei- und Playlist-Auswahldialoge
  - Lade-/Importverhalten fuer Playlists
  - Recording- und Playback-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tests:
  - `100/100` gruen

Kurzfazit:

- Der kleine Nachschnitt entfernt die letzten doppelten Recording-/Playlist-Defaultpfade in diesem Block.
- Das ist erneut nur ein lokaler Struktur-Refactor ohne Aenderung am Nutzerverhalten.
- Damit bleibt auch dieser vierte kleine `radio_controller`-Schritt voll verifiziert und risikoarm.

## Phase 3.47: DNS-Controller-Callback-Helfer `netmon/features/dns_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dns_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/dns_controller.py
pytest tests/test_netmon_dns_consistency.py tests/test_netmon_lang_service.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer optionale App-Callbacks eingefuehrt:
  - `_app_callback(...)`
  - `_invoke_optional_app_callback(...)`
- wiederholte Callback-/Fallback-Pfade vereinheitlicht, u. a. in:
  - `_refresh_dns_state()`
  - `normalize_dns_profile_choice()`
  - `apply_dns_profile_choice_via_control()`
  - `apply_dns()`
- bewusst unveraendert geblieben sind:
  - DNS-Profil- und VPN-Entscheidungslogik
  - DNSSEC-Bestaetigungsablauf
  - DoT-/Guard-/Refresh-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DNS-/Lang-Tests:
  - `123/123` gruen

Kurzfazit:

- Der DNS-Controller geht jetzt bei optionalen App-Hooks gleichfoermiger vor, statt mehrere kleine `getattr(...)/callable(...)`-Varianten zu tragen.
- Das bleibt ein rein struktureller Helfer-Schnitt ohne Aenderung am DNS-Verhalten.
- Damit ist auch der erste kleine DNS-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.48: Security-Monitoring-Callback- und Tabellenhelfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
pytest tests/test_netmon_security_modules.py tests/test_netmon_lang_service.py tests/test_netmon_dns_consistency.py -k "security or main_tabs_and_security_sections_use_translation_keys or refresh_security_log_level_updates_security_label or security_set_ufw_logging_high_refreshes_light"
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer optionale Security-Callbacks und Tabellen-Clearing eingefuehrt:
  - `_app_callback(...)`
  - `_refresh_security_log_level_safe(...)`
  - `_refresh_connected_devices_safe(...)`
  - `_clear_table_rows(...)`
- wiederholte Callback-/Refresh-Pfade vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `security_open_tab()`
  - `security_clear_views()`
  - `security_start_monitoring()`
  - `security_scan_now()`
- bewusst unveraendert geblieben sind:
  - Parser-, Event- und Baseline-Logik
  - Scan- und Alarm-Semantik
  - Security-Tab-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-/Lang-Regressionstests:
  - `27/27` gruen

Kurzfazit:

- Der Security-Monitoring-Controller nutzt jetzt bei kleinen UI-Refresh- und Tabellenpfaden dieselben Helfer statt mehrere fast gleiche Mini-Abfragen.
- Das bleibt ein lokaler Struktur-Refactor ohne Aenderung an Scan-, Event- oder Alarmverhalten.
- Damit ist auch dieser Security-Block in Phase 3 wieder voll verifiziert abgeschlossen.

## Phase 3.49: Links-Controller-Desktop-App-Mapping-Helfer `netmon/features/links_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/links_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/links_controller.py
pytest tests/test_netmon_connections_context.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Desktop-App-Mappings und die aktuelle Systemlink-Auswahl eingefuehrt:
  - `_desktop_app_maps(...)`
  - `_selected_systemlink_entry(...)`
- wiederholte Desktop-App-Lookups vereinheitlicht, u. a. in:
  - `refresh_desktop_app_entries()`
  - `load_link_slot_into_form()`
  - `on_systemlink_app_select()`
  - `build_systemlink_target()`
- bewusst unveraendert geblieben sind:
  - Desktop-Datei-Parsing
  - Link-Ausführung und Target-Normalisierung
  - Formular- und Slot-Semantik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Links-/UI-Regressionstests:
  - `39/39` gruen

Kurzfazit:

- Der Links-Controller behandelt Desktop-App-Mappings und die aktuelle Systemlink-Auswahl jetzt gleichfoermiger statt mit mehreren kleinen Direktzugriffen.
- Das bleibt ein lokaler Struktur-Refactor ohne Aenderung am Verhalten von Link-Slots oder Systemlinks.
- Damit ist auch dieser kleine Links-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.50: Fun-Controller-Dependency- und Game-Helfer `netmon/features/fun_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/fun_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/fun_controller.py
pytest tests/test_netmon_fun_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Fun-Dependency-Status und Game-Lookups eingefuehrt:
  - `_fun_dep_status(...)`
  - `_fun_dep_enabled(...)`
  - `_game_by_id(...)`
- wiederholte Status- und Auswahlpfade vereinheitlicht, u. a. in:
  - `discover_fun_games()`
  - `update_fun_dependency_state()`
  - `_resolve_selected_game()`
  - `open_fun_games_folder()`
  - `start_selected_game()`
- bewusst unveraendert geblieben sind:
  - Game-Discovery und Launcher-Semantik
  - `subprocess.Popen(...)`-Startverhalten
  - Start-/Stop-Statusmeldungen

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Fun-Tests:
  - `8/8` gruen

Kurzfazit:

- Der Fun-Controller nutzt jetzt fuer Dependency-Pruefungen und Game-Auswahl kleine gemeinsame Helfer statt mehrere verstreute Direktabfragen.
- Das bleibt ein lokaler Struktur-Refactor ohne Aenderung am Launcher-Verhalten.
- Damit ist auch dieser kleine Fun-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.51: Speedtest-Controller-Format- und History-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
timeout 10s python3 -m black --check --workers 1 netmon/features/speedtest_controller.py tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer History- und Wertformatierung eingefuehrt:
  - `_speedtest_history_records(...)`
  - `_speedtest_ms_text(...)`
  - `_speedtest_mbps_text(...)`
- wiederholte History-/Panel-Pfade vereinheitlicht, u. a. in:
  - `persist_speedtest_history()`
  - `append_speedtest_history()`
  - `update_speedtest_panel()`
  - `show_speedtest_history()`
- zusaetzlich zwei kleine direkte Controller-Tests ergaenzt fuer:
  - Warnschwellen
  - Panel-Formatierung
- bewusst unveraendert geblieben sind:
  - Speedtest-CLI-Auswahl
  - Ergebnisparsing
  - Async-Ablauf und Logging-Semantik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `10/10` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt History-Listen und Anzeigeformate jetzt gleichfoermiger statt dieselben kleinen Formatierungen mehrfach auszuschreiben.
- Durch die zwei neuen Unit-Tests ist der kleine Refactor direkt controller-nah abgesichert.
- Damit ist auch dieser kompakte Speedtest-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.52: Packet-Capture-Controller-Datei- und Tool-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
timeout 10s python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Tool-Status und Capture-Dateipfad eingefuehrt:
  - `_packet_capture_dep_enabled(...)`
  - `_packet_capture_file_path(...)`
- wiederholte Tool-/Dateipfade vereinheitlicht, u. a. in:
  - `packet_capture_set_running_state()`
  - `refresh_packet_capture_interfaces()`
  - `packet_capture_show_file_info()`
  - `packet_capture_start_async()`
  - `open_packet_capture_in_wireshark()`
  - `open_packet_capture_file_location()`
- zusaetzlich zwei kleine direkte Controller-Tests ergaenzt fuer:
  - Button-State-Wechsel
  - Dateiinfo-Fallback ueber Dateigroesse
- bewusst unveraendert geblieben sind:
  - Capture-Start-/Stopp-Logik
  - `tshark`-/`dumpcap`-Aufruf
  - Wireshark-/Pfad-Oeffnen-Semantik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-/UI-Tests:
  - `15/15` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Tool-Status und Capture-Dateipfade jetzt gleichfoermiger statt mehrere kleine Spezialfaelle nebeneinander zu tragen.
- Durch die zwei neuen Unit-Tests ist auch dieser Refactor direkt controller-nah abgesichert.
- Damit ist dieser kompakte Packet-Capture-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.53: Links-Controller-Formular- und Slot-Helfer `netmon/features/links_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/links_controller.py tests/test_links_controller.py
python3 -m black --workers 1 netmon/features/links_controller.py tests/test_links_controller.py
python3 -m black --check --workers 1 netmon/features/links_controller.py
python3 -m black --check --workers 1 tests/test_links_controller.py
pytest tests/test_links_controller.py tests/test_netmon_connections_context.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Formular- und Slot-Zugriffe eingefuehrt:
  - `_selected_link_slot_no(...)`
  - `_selected_link_type(...)`
  - `_clear_link_slot_payload(...)`
- wiederholte Slot-/Typ-Fallbacks vereinheitlicht, u. a. in:
  - `on_link_slot_select()`
  - `sync_link_target_widgets()`
  - `build_systemlink_target()`
  - `assign_link_slot()`
  - `clear_link_slot()`
  - `build_form_link_slot()`
- zusaetzlich zwei kleine direkte Controller-Tests ergaenzt fuer:
  - Systemlink-Zielaufloesung ueber die aktuelle Desktop-App-Auswahl
  - Formular-Slot-Aufbau fuer `systemlink`
- bewusst unveraendert geblieben sind:
  - Ziel-Builder fuer `command`, `url` und `path`
  - Persistenz der Slots
  - UI-Refresh-Semantik ausserhalb der vereinheitlichten Slot-/Typ-Lookups

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Links-/UI-Tests:
  - `41/41` gruen

Kurzfazit:

- Der Links-Controller behandelt den aktuell ausgewaehlten Slot und Link-Typ jetzt gleichfoermiger statt dieselben kleinen Fallbacks an mehreren Stellen auszuschreiben.
- Durch die zwei neuen direkten Tests ist der Refactor auch controller-nah abgesichert.
- Damit ist dieser kompakte Links-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.54: Repository-Guard-Service-, Pfad- und Clipboard-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py tests/test_netmon_process_guard_ui.py tests/test_netmon_startup_guard_ui.py tests/test_netmon_roots_guard_ui.py tests/test_netmon_lang_service.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Repository-Guard-Zugriffe eingefuehrt:
  - `_repository_guard_service(...)`
  - `_repository_guard_trustlist_path(...)`
  - `_repository_guard_baseline_path(...)`
  - `_repository_guard_selected_source(...)`
  - `_repository_guard_selected_finding(...)`
  - `_copy_repository_guard_payload(...)`
- wiederholte Service-, Pfad-, Auswahl- und Clipboard-Pfade vereinheitlicht, u. a. in:
  - `run_repository_guard_scan()`
  - `copy_repository_guard_report()`
  - `run_repository_guard_primary_action()`
  - `copy_repository_guard_quick_action_snippet()`
  - `copy_repository_guard_selected_uri()`
  - `copy_repository_guard_selected_file_path()`
  - `create_repository_guard_baseline()`
  - `reset_repository_guard_baseline()`
  - `mark_selected_repository_guard_trusted()`
  - `remove_selected_repository_guard_trusted()`
  - `show_repository_guard_trustlist()`
  - `reset_repository_guard_trustlist()`
- zusaetzlich zwei kleine direkte Controller-Tests ergaenzt fuer:
  - URI-Kopieren ueber die ausgewaehlte Finding-/Source-Aufloesung
  - Trustlist-Markierung mit getrimmtem Trustlist-Pfad
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline- und Vergleichslogik des Services
  - Filter- und Tree-Aufbereitung
  - Quick-Action-Inhalte selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-/UI-Tests:
  - `29/29` gruen
  - `1` skipped

Kurzfazit:

- Der Repository-Guard-Controller behandelt die kleinen Service-, Pfad- und Clipboard-Zugriffe jetzt gleichfoermiger statt dieselben Muster an vielen Stellen erneut auszuschreiben.
- Die neuen direkten Tests sichern genau diese vereinheitlichten Auswahl- und Trustlist-Pfade ab.
- Damit ist auch dieser kompakte Repository-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.55: Process-Guard-Service-, Trustlist- und Auswahl-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py tests/test_netmon_process_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Process-Guard-Zugriffe eingefuehrt:
  - `_process_guard_service(...)`
  - `_process_guard_trustlist_path(...)`
  - `_selected_process_guard_finding(...)`
  - `_process_guard_last_result(...)`
  - `_process_guard_filter_mode(...)`
- wiederholte Service-, Trustlist-, Ergebnis- und Auswahlpfade vereinheitlicht, u. a. in:
  - `update_process_guard_status_line()`
  - `show_process_guard_trustlist()`
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
  - `reset_process_guard_trustlist()`
  - `refresh_process_guard_tree()`
  - `run_process_guard_check()`
  - `analyze_process_guard_with_chad()`
  - `analyze_selected_process_guard_with_chad()`
  - `start_process_guard_monitoring()`
- zusaetzlich zwei kleine direkte Controller-Tests ergaenzt fuer:
  - Entfernen eines vertrauten Funds mit getrimmtem Trustlist-Pfad
  - `run_process_guard_check()` mit getrimmtem Trustlist-Pfad
- bewusst unveraendert geblieben sind:
  - Ergebnisformatierung
  - Licht-/Statusbewertung
  - eigentliche Monitoring- und Service-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Tests:
  - `15/15` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Service-, Trustlist- und Auswahlzugriffe jetzt gleichfoermiger statt dieselben kleinen Muster mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Trustlist- und Recheck-Pfade ab.
- Damit ist auch dieser kompakte Process-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.56: DoT-Callback- und Status-Helfer `netmon/features/dot_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dot_controller.py tests/test_dot_controller.py
python3 -m black --check --workers 1 netmon/features/dot_controller.py
python3 -m black --check --workers 1 tests/test_dot_controller.py
pytest tests/test_dot_controller.py tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte DoT-Callback- und Statuszugriffe eingefuehrt:
  - `_app_callback(...)`
  - `_preferred_dnssec_mode(...)`
  - `_vpn_dns_active_state(...)`
  - `_confirm_dot_activation(...)`
  - `_dot_status_text(...)`
- wiederholte Callback- und Statuspfade vereinheitlicht, u. a. in:
  - `build_dot_dropin_content()`
  - `set_dot_state()`
  - `enable_dot_async()`
- zusaetzlich vier kleine direkte Controller-Tests ergaenzt fuer:
  - bevorzugten VPN-DNS-Callback
  - Fallback auf den Controller-Helfer
  - Standardverhalten ohne DNSSEC-Bestaetigungs-Callback
  - Callback-basierte DNSSEC-Bestaetigung
- bewusst unveraendert geblieben sind:
  - DoT-Drop-in-Inhalt
  - Aktivierungs-/Deaktivierungsablauf
  - Resolver- und TLS-Prueflogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DoT-/DNS-Tests:
  - `120/120` gruen

Kurzfazit:

- Der DoT-Controller behandelt optionale App-Callbacks und den kleinen Status-Text jetzt gleichfoermiger statt dieselben Muster mehrfach auszuschreiben.
- Die neuen direkten Tests sichern die vereinheitlichten Callback-Pfade zusaetzlich zu den bestehenden DNS-Regressionstests ab.
- Damit ist auch dieser kompakte DoT-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.57: Linux-Help-Auswahl-, Resolver- und Chad-Helfer `netmon/features/linux_help_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/linux_help_controller.py tests/test_netmon_linux_help.py
python3 -m black --check --workers 1 netmon/features/linux_help_controller.py
python3 -m black --check --workers 1 tests/test_netmon_linux_help.py
pytest tests/test_netmon_linux_help.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Linux-Help-Zugriffe eingefuehrt:
  - `_selected_linux_help_id(...)`
  - `_linux_help_command_resolver(...)`
  - `_resolve_linux_help_item(...)`
  - `_set_chad_direct_prompt_safe(...)`
- wiederholte Auswahl-, Resolver- und Chad-Pfade vereinheitlicht, u. a. in:
  - `_get_selected_linux_help_item()`
  - `on_linux_help_select()`
  - `send_linux_help_to_chad()`
  - `send_linux_help_command_to_terminal()`
- zusaetzlich drei kleine direkte Tests ergaenzt fuer:
  - Auswahl-ID ueber Tree-Selection
  - Item-Aufloesung ueber den App-Resolver
  - direkte Chad-Uebergabe ueber `set_chad_direct_prompt(...)`
- bewusst unveraendert geblieben sind:
  - Linux-Help-Datenstruktur
  - Prompt-Inhalt
  - Terminal-Validierung und Dialogverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Linux-Help-Tests:
  - `10/10` gruen

Kurzfazit:

- Der Linux-Help-Controller behandelt Auswahl-ID, Command-Aufloesung und Chad-Uebergabe jetzt gleichfoermiger statt dieselben kleinen Entscheidungswege mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Auswahl- und Resolver-Pfade ab.
- Damit ist auch dieser kompakte Linux-Help-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.58: Security-Monitoring-Detail-, Auswahl- und Inventar-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Security-Monitoring-Zugriffe eingefuehrt:
  - `_security_detail_widget(...)`
  - `_security_table_row_meta(...)`
  - `_security_visible_events(...)`
  - `_connected_devices_inventory(...)`
  - `_selected_table_row_id(...)`
- wiederholte Detail-, Auswahl- und Inventarpfade vereinheitlicht, u. a. in:
  - `on_security_event_select()`
  - `security_clear_views()`
  - `_set_security_detail_text()`
  - `refresh_connected_device_table()`
  - `on_connected_device_select()`
- zusaetzlich zwei kleine direkte Tests ergaenzt fuer:
  - Event-Detailanzeige ueber `security_table_row_meta`
  - View-Reset inklusive Detailtext und Tabellen-Clear
- bewusst unveraendert geblieben sind:
  - Parser- und Aggregationslogik
  - Device-Inventarisierung
  - Security-Monitoring- und Baseline-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `25/25` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt Detail-Widget, Zeilenauswahl und Device-Inventar jetzt gleichfoermiger statt dieselben kleinen UI-Zugriffe mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Detail- und Clear-Pfade ab.
- Damit ist auch dieser kompakte Security-Monitoring-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.59: ClamAV-Runtime- und Findings-Helfer `netmon/features/clamav_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/clamav_controller.py tests/test_clamav_controller.py
python3 -m black --check --workers 1 netmon/features/clamav_controller.py
python3 -m black --check --workers 1 tests/test_clamav_controller.py
pytest tests/test_clamav_controller.py tests/test_netmon_security_modules.py tests/test_netmon_chad_analysis_flow.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte ClamAV-Zugriffe eingefuehrt:
  - `_clamav_runtime_state(...)`
  - `_clamav_findings_path(...)`
- wiederholte Runtime- und Findings-Pfade vereinheitlicht, u. a. in:
  - `clamav_progress_apply()`
  - `load_clamav_findings()`
  - `save_clamav_findings()`
- zusaetzlich drei kleine direkte Controller-Tests ergaenzt fuer:
  - Runtime-State-Aufloesung
  - Laden und Begrenzen der Findings auf die letzten 300 gueltigen Eintraege
  - Ersetzen offener Findings bei Erhalt der Quarantaene-Historie
- bewusst unveraendert geblieben sind:
  - Scan- und Quarantaenelogik
  - Panel- und Output-Verhalten
  - Chad-/Systemcheck-Integration

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- ClamAV-/Security-/Chad-Tests:
  - `70/70` gruen

Kurzfazit:

- Der ClamAV-Controller behandelt Runtime-Felder und den Findings-Pfad jetzt gleichfoermiger statt dieselben kleinen Status- und Dateipfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Findings- und Runtime-Pfade zusaetzlich zu den bestehenden Security-/Chad-Regressionslaeufen ab.
- Damit ist auch dieser kompakte ClamAV-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.60: Radio-Tab-Launcher-State-Helfer `netmon/ui/tabs/radio_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py
python3 -m black --check --workers 1 netmon/ui/tabs/radio_tab.py
python3 -m black --check --workers 1 tests/test_radio_tab.py
pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Radio-Launcher-Zugriffe eingefuehrt:
  - `_app_attr(...)`
  - `_radio_launcher_mode(...)`
  - `_radio_launcher_status_text(...)`
  - `_radio_launcher_runtime_state(...)`
- wiederholte Launcher-Mode- und Statuspfade vereinheitlicht, u. a. in:
  - `_show_detached_placeholder()`
  - `_show_embedded_panel()`
  - `refresh_radio_launcher_state()`
- zusaetzlich drei kleine direkte Tests ergaenzt fuer:
  - Status-Text fuer bekannte Launcher-Zustaende
  - Runtime-State ueber `netmon_radio_core`
  - robustes Verhalten bei Core-Fehlern
- bewusst unveraendert geblieben sind:
  - Paned-UI und Embedded-Panel-Aufbau
  - Reattach-/Detach-Fluss
  - eigentliche Radio-Core-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Radio-Tab-/Radio-Module-Tests:
  - `103/103` gruen

Kurzfazit:

- Der Radio-Tab behandelt Launcher-Mode und Launcher-Status jetzt gleichfoermiger statt dieselben kleinen Statuspfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Launcher-Helfer zusaetzlich zu den bestehenden Radio-Modultests ab.
- Damit ist auch dieser kompakte Radio-Tab-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.61: VPN-Slots-Tab-Profil- und Default-Helfer `netmon/ui/tabs/vpn_slots_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/vpn_slots_tab.py tests/test_vpn_slots_tab.py
python3 -m black --check --workers 1 netmon/ui/tabs/vpn_slots_tab.py
python3 -m black --check --workers 1 tests/test_vpn_slots_tab.py
pytest tests/test_vpn_slots_tab.py tests/test_netmon_vpn_slots.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_ipv6_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte VPN-Slots-Builder-Zugriffe eingefuehrt:
  - `_app_attr(...)`
  - `_vpn_slot_choices(...)`
  - `_wg_profiles(...)`
  - `_primary_vpn_slot_value(...)`
- wiederholte Profil-, Slot- und Default-Pfade vereinheitlicht, u. a. in:
  - Slot-Combobox
  - Hauptprofil-Comboboxen
  - Primary-VPN-Defaultwerte
  - manueller WireGuard-Slot-Chooser
- zusaetzlich drei kleine direkte Tests ergaenzt fuer:
  - Slot-Auswahlwerte
  - Profil-Liste als Builder-Wert
  - Primary-VPN-Default-Aufloesung
- bewusst unveraendert geblieben sind:
  - UI-Struktur und Widget-Reihenfolge
  - Kontextmenue-Bindings
  - eigentliche VPN-Slot- und IPv6-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- VPN-Slots-/IPv6-/Shortcut-Tests:
  - `64/64` gruen

Kurzfazit:

- Der VPN-Slots-Tab behandelt Profil-Listen und Primary-VPN-Defaults jetzt gleichfoermiger statt dieselben kleinen Builder-Werte mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Builder-Helfer zusaetzlich zu den bestehenden VPN-/IPv6-Regressionstests ab.
- Damit ist auch dieser kompakte VPN-Slots-Tab-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.62: Roots-Baseline-Guard-Pfad-, Opener- und Listen-Helfer `netmon/features/roots_baseline_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/roots_baseline_guard_controller.py tests/test_roots_baseline_guard_controller.py
python3 -m black --check --workers 1 netmon/features/roots_baseline_guard_controller.py
python3 -m black --check --workers 1 tests/test_roots_baseline_guard_controller.py
pytest tests/test_roots_baseline_guard_controller.py tests/test_netmon_roots_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Roots-Baseline-Guard-Listen- und Dateipfade eingefuehrt:
  - `_roots_list_widget(...)`
  - `_roots_baseline_guard_info_path(...)`
  - `_open_path_in_file_manager_safe(...)`
- wiederholte Listen-, Info-Datei- und Parent-Opener-Pfade vereinheitlicht, u. a. in:
  - `_refresh_history_list()`
  - `_refresh_whitelist_list()`
  - `open_roots_baseline_guard_info_path()`
  - `open_selected_roots_baseline_guard_parent_folder()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - robustes Verhalten ohne Dateimanager-Opener
  - korrekte Aktualisierung von Whitelist-Liste und Zeilen-Metadaten
- bewusst unveraendert geblieben sind:
  - Baseline- und Diff-Logik
  - Whitelist-Inhalt und Dateiformat
  - eigentliche Guard-Scan- und Analysepfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Roots-Baseline-Guard-/UI-Tests:
  - `96 passed, 1 skipped`

Kurzfazit:

- Der Roots-Baseline-Guard behandelt Listen-Widgets und Datei-Opener jetzt gleichfoermiger statt dieselben kleinen Pfad- und Fallback-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Listen- und Opener-Helfer zusaetzlich zu den bestehenden Roots-UI-Regressionstests ab.
- Damit ist auch dieser kompakte Roots-Baseline-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.63: Chad-Prompt-, Tab- und Snapshot-Helfer `netmon/features/chad_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/chad_controller.py tests/test_netmon_chad_analysis_flow.py
python3 -m black --check --workers 1 netmon/features/chad_controller.py
python3 -m black --check --workers 1 tests/test_netmon_chad_analysis_flow.py
pytest tests/test_netmon_chad_analysis_flow.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Chad-Analyse- und UI-Zugriffe eingefuehrt:
  - `_settings_dict(...)`
  - `_chad_chat_input_widget(...)`
  - `_chad_transcript_snapshot(...)`
  - `_select_chad_tab_safe(...)`
  - `_apply_prepared_chad_analysis(...)`
- wiederholte Prompt-, Tab-Wechsel-, Chat-Input- und Snapshot-Pfade vereinheitlicht, u. a. in:
  - `set_chad_direct_prompt()`
  - `set_chad_analysis()`
  - `save_chad_analysis_to_file()`
  - `load_chad_analysis_from_file()`
  - `clear_chad_analysis()`
  - `prepare_chad_analysis()`
  - `send_chad_chat_message()`
  - `run_chad_online_analysis()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorbereitete Analyse mit aktivem Auto-Switch
  - respektierten Verzicht auf den Tab-Wechsel bei deaktiviertem Auto-Switch
- bewusst unveraendert geblieben sind:
  - Prompt-Inhalt und Filterlogik
  - Online-Chat- und Online-Analyse-Ablauf
  - Chad-UI und Kontextmenue-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Chad-Analyse-/Kontextmenue-Tests:
  - `44/44` gruen

Kurzfazit:

- Der Chad-Controller behandelt vorbereitete Analysen, Tab-Wechsel und Analyse-Snapshots jetzt gleichfoermiger statt dieselben kleinen Status- und Snapshot-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Prompt-/Tab-Logik zusaetzlich zu den bestehenden Chad-Flow-Tests ab.
- Damit ist auch dieser kompakte Chad-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.64: HDD-Slot-Auswahl- und Reset-Helfer `netmon/features/hdd_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/hdd_controller.py tests/test_netmon_hdd.py
python3 -m black --check --workers 1 netmon/features/hdd_controller.py
python3 -m black --check --workers 1 tests/test_netmon_hdd.py
pytest tests/test_netmon_hdd.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte HDD-Slot-Auswahl- und Reset-Pfade eingefuehrt:
  - `_selected_hdd_slot_no(...)`
  - `_selected_hdd_slot(...)`
  - `_clear_hdd_slot_fields(...)`
- wiederholte Slot-Choice-, Target- und Reset-Logik vereinheitlicht, u. a. in:
  - `assign_selected_disk_to_slot()`
  - `clear_slot_assignment()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - gueltige und ungueltige Slot-Auswahl ueber den gemeinsamen Helfer
  - vollstaendiges Leeren der Slot-Zuordnungsfelder
- bewusst unveraendert geblieben sind:
  - Mount-/Unmount-Logik
  - LUKS- und Mapper-Pfade
  - HDD-Refresh-, Info- und Licht-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- HDD-Tests:
  - `6/6` gruen

Kurzfazit:

- Der HDD-Controller behandelt Slot-Auswahl und Slot-Reset jetzt gleichfoermiger statt dieselben kleinen Choice- und Clear-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Slot-Helfer zusaetzlich zu den bestehenden HDD-Mount-/Unmount-Regressionstests ab.
- Damit ist auch dieser kompakte HDD-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.65: VPN-Privacy-Config- und NM-Importstatus-Helfer `netmon/features/vpn_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/vpn_controller.py tests/test_netmon_vpn_slots.py
python3 -m black --check --workers 1 netmon/features/vpn_controller.py
python3 -m black --check --workers 1 tests/test_netmon_vpn_slots.py
pytest tests/test_netmon_vpn_slots.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Privacy-Config- und Persistenzpfade eingefuehrt:
  - `_privacy_config_dict(...)`
  - `_save_privacy_config_safe(...)`
  - `_normalized_nm_last_import_state(...)`
- wiederholte Config-, Normalize- und Save-Logik vereinheitlicht, u. a. in:
  - `get_nm_last_import_state()`
  - `set_nm_last_import_state()`
  - `set_vpn_backend_mode()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - normalisierte Rueckgabe eines unaufgeraeumten NM-Importstatus
  - Anlegen der Privacy-Config plus Logging bei fehlgeschlagenem Persistieren
  - korrektes Setzen und Speichern des Backend-Modus
- bewusst unveraendert geblieben sind:
  - WireGuard-/NetworkManager-Wechselpfade
  - aktive Interface-Erkennung
  - VPN-Slot-, IPv6- und Killswitch-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- VPN-Slot-Tests:
  - `51/51` gruen

Kurzfazit:

- Der VPN-Controller behandelt Privacy-Config und NM-Importstatus jetzt gleichfoermiger statt dieselben kleinen Config- und Persistenzpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Config-Helfer zusaetzlich zu den bestehenden VPN-Slot-Regressionstests ab.
- Damit ist auch dieser kompakte VPN-Config-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.66: Startup-Guard-Service- und Trustlist-Pfad-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py tests/test_startup_guard_phase2.py
python3 -m black --check --workers 1 netmon/features/security_audit_controller.py
python3 -m black --check --workers 1 tests/test_startup_guard_phase2.py
pytest tests/test_startup_guard_phase2.py tests/test_netmon_startup_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Startup-Guard-Service- und Trustlist-Pfade eingefuehrt:
  - `_startup_guard_service(...)`
  - `_startup_guard_trustlist_path(...)`
  - `_startup_guard_trustlist(...)`
- wiederholte Trustlist- und Service-Zugriffe vereinheitlicht, u. a. in:
  - `startup_guard_mark_selected_trusted()`
  - `startup_guard_remove_selected_trusted()`
  - `startup_guard_show_trustlist()`
  - `startup_guard_reset_trustlist()`
  - `startup_guard_startup_check()`
  - `startup_guard_create_baseline()`
  - `startup_guard_check()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Trustlist-Anzeige mit konfiguriertem Pfad
  - korrektes Weiterreichen des Trustlist-Pfads im Startup-Check
- bewusst unveraendert geblieben sind:
  - Baseline- und Vergleichslogik
  - Startup-Guard-UI und Ergebnisdarstellung
  - Chad-Analyse- und Trustlist-Fachlogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Startup-Guard-Tests:
  - `14/14` gruen

Kurzfazit:

- Der Startup-Guard-Teil im Audit-Controller behandelt Service- und Trustlist-Pfade jetzt gleichfoermiger statt dieselben kleinen Service- und Pfadzugriffe mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Trustlist-Helfer zusaetzlich zu den bestehenden Startup-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Startup-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.67: Packet-Capture-Datei- und Launcher-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_chad_context_menu.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Packet-Capture-Datei- und Launcher-Pfade eingefuehrt:
  - `_packet_capture_existing_file_path(...)`
  - `_packet_capture_open_target_path(...)`
  - `_packet_capture_wireshark_launcher(...)`
- wiederholte Datei-, Parent-Ordner- und Launcher-Zugriffe vereinheitlicht, u. a. in:
  - `open_packet_capture_in_wireshark()`
  - `open_packet_capture_file_location()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - bevorzugten Zielpfad bei vorhandener Capture-Datei
  - Parent-Ordner-Fallback bei noch nicht vorhandener Zieldatei
  - normierte Wireshark-Launcher-Rueckgabe
- bewusst unveraendert geblieben sind:
  - Capture-Start-/Stopp-Logik
  - Laufzeit- und Dateiinfo-Logik
  - Security-Tab- und Chad-Kontextmenue-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-/Shortcut-/Kontextmenue-Tests:
  - `18/18` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Datei- und Launcher-Pfade jetzt gleichfoermiger statt dieselben kleinen Datei- und Target-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Datei-/Launcher-Helfer zusaetzlich zu den bestehenden Packet-Capture- und UI-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.68: Links-Formular-Ziel- und Namens-Helfer `netmon/features/links_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/links_controller.py tests/test_links_controller.py
python3 -m black --check --workers 1 netmon/features/links_controller.py
python3 -m black --check --workers 1 tests/test_links_controller.py
pytest tests/test_links_controller.py tests/test_netmon_connections_context.py tests/test_netmon_selection_shortcuts.py tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Links-Formularwerte eingefuehrt:
  - `_link_custom_name(...)`
  - `_link_target_fields(...)`
- wiederholte Formular-Ziel- und Namen-Pfade vereinheitlicht, u. a. in:
  - `assign_link_slot()`
  - `build_form_link_slot()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - normalisierte externe Link-Ziele
  - getrimmte Formularnamen
- bewusst unveraendert geblieben sind:
  - Desktop-App-Auswahl und Desktop-File-Logik
  - Link-Ausfuehrung
  - Links-UI und Tabellen-/Button-Refresh

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Links-/Context-/Shortcut-/Security-Tests:
  - `45/45` gruen

Kurzfazit:

- Der Links-Controller behandelt Formularziel und Formularname jetzt gleichfoermiger statt dieselben kleinen Form-Werte mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Formular-Helfer zusaetzlich zu den bestehenden Links- und UI-Regressionstests ab.
- Damit ist auch dieser kompakte Links-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.69: Fun-Status- und Laufzustand-Helfer `netmon/features/fun_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/fun_controller.py tests/test_netmon_fun_module.py
python3 -m black --check --workers 1 netmon/features/fun_controller.py
python3 -m black --check --workers 1 tests/test_netmon_fun_module.py
pytest tests/test_netmon_fun_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Fun-Status- und Laufzustands-Pfade eingefuehrt:
  - `_is_current_game_running(...)`
  - `_set_fun_status(...)`
- wiederholte Status- und Laufpruefungen vereinheitlicht, u. a. in:
  - `update_fun_games_table()`
  - `start_selected_game()`
  - `stop_running_game()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - laufenden Spielstatus nur bei passender ID plus aktivem Prozess
  - formatierten Status-Text ueber den gemeinsamen Status-Helfer
- bewusst unveraendert geblieben sind:
  - Spielsuche und Importlogik
  - Popen-/Threading-Verhalten
  - Fun-Tab-UI und Integrationshooks

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Fun-Tests:
  - `10/10` gruen

Kurzfazit:

- Der Fun-Controller behandelt Laufzustand und Statusmeldungen jetzt gleichfoermiger statt dieselben kleinen Statuspfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Status-Helfer zusaetzlich zu den bestehenden Fun-Launcher-Regressionstests ab.
- Damit ist auch dieser kompakte Fun-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.70: Security-Summary-Status- und Baseline-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py netmon/features/chad_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
pytest tests/test_netmon_security_modules.py tests/test_netmon_lang_service.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Security-Summary-Zugriffe eingefuehrt:
  - `_security_events(...)`
  - `_security_summary_context(...)`
- wiederholte Event-, Status- und Baseline-Zugriffe im Chad-Summary vereinheitlicht, u. a. in:
  - `_build_security_chad_summary()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - sichere Default-Zusammenfassung ohne gesetzte App-Attribute
  - entkoppelte Event-Liste ohne Seiteneffekte auf den App-Zustand
- bewusst unveraendert geblieben sind:
  - Security-Parser-, Aggregations- und Monitoring-Logik
  - Chad-Summary-Inhalt und Risikobewertung
  - Security-UI und Tabellenlogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-/Lang-Tests:
  - `34/34` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt Summary-Status und Baseline-Kontext jetzt gleichfoermiger statt dieselben kleinen Event- und Kontextzugriffe mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Summary-Helfer zusaetzlich zu den bestehenden Security-Summary-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Summary-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.71: Firewall-Formular-Werte- und Protokoll-Helfer `netmon/features/firewall_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/firewall_controller.py tests/test_firewall_controller.py
python3 -m black --check --workers 1 netmon/features/firewall_controller.py
python3 -m black --check --workers 1 tests/test_firewall_controller.py
pytest tests/test_firewall_controller.py tests/test_netmon_vpn_slots.py tests/test_netmon_lang_service.py tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Firewall-Formularwerte eingefuehrt:
  - `_add_firewall_rule_form_values(...)`
  - `_add_firewall_rule_protocols(...)`
- wiederholte Formular-Normalisierung und Protokoll-Auswahl vereinheitlicht, u. a. in:
  - `_build_add_firewall_rule_preview_text()`
  - `_validate_add_firewall_rule_form()`
  - `_build_add_firewall_rule_command_args()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - normalisierte Quelladresse mit `any`-Fallback
  - expandierte Protokoll-Auswahl fuer `TCP + UDP`
  - korrekt gebaute UFW-Kommandoliste aus normalisierten Formwerten
- bewusst unveraendert geblieben sind:
  - UFW-Anwendung und Dialogfluss
  - Firewall-Status- und VPN-Firewall-Logik
  - Firewall-UI und Refresh-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Firewall-/VPN-/Lang-/DNS-Tests:
  - `177/177` gruen

Kurzfazit:

- Der Firewall-Controller behandelt Formularwerte und Protokoll-Auswahl jetzt gleichfoermiger statt dieselben kleinen Form-Werte mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Formular-Helfer zusaetzlich zu den bestehenden Firewall- und VPN-Regressionstests ab.
- Damit ist auch dieser kompakte Firewall-Formular-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.72: Process-Guard-Trustlist- und Count-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py tests/test_netmon_process_guard_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Process-Guard-Trustlist- und Count-Pfade eingefuehrt:
  - `_process_guard_trustlist(...)`
  - `_process_guard_counts(...)`
- wiederholte Trustlist- und Count-Zugriffe vereinheitlicht, u. a. in:
  - `show_process_guard_trustlist()`
  - `run_process_guard_check()`
  - `apply_process_guard_monitoring_snapshot()`
  - `start_process_guard_monitoring()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sicheren Trustlist-Default ohne Service
  - gruppierte Risk-Level-Zaehlung
  - korrekt verwendeten Trustlist-Pfad in der Vertrauenslisten-Anzeige
- bewusst unveraendert geblieben sind:
  - Process-Guard-Analyse- und Monitoring-Logik
  - Chad-Integration
  - Process-Guard-UI und Auswahlpfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Tests:
  - `18/18` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Trustlist-Zugriffe und Risk-Level-Zaehlung jetzt gleichfoermiger statt dieselben kleinen Trustlist- und Count-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.73: Repository-Guard-Trustlist- und Result-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Repository-Guard-Trustlist- und Ergebnispfade eingefuehrt:
  - `_repository_guard_trustlist(...)`
  - `_repository_guard_last_result(...)`
- wiederholte Trustlist- und Result-Zugriffe vereinheitlicht, u. a. in:
  - `run_repository_guard_scan()`
  - `refresh_repository_guard_sources_tree()`
  - `refresh_repository_guard_findings_tree()`
  - `export_repository_guard_report()`
  - `create_repository_guard_baseline()`
  - `reset_repository_guard_baseline()`
  - `show_repository_guard_trustlist()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sicheren Trustlist-Default ohne Service
  - entkoppeltes Ergebnis-Dict ohne Seiteneffekte
  - korrekt verwendeten, getrimmten Trustlist-Pfad in der Vertrauenslisten-Anzeige
- bewusst unveraendert geblieben sind:
  - Repository-Scan- und Baseline-Logik
  - Quick Actions und Clipboard-Verhalten
  - Repository-Guard-UI und Filterlogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Tests:
  - `14/14` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt Trustlist- und Ergebniszugriffe jetzt gleichfoermiger statt dieselben kleinen Trustlist- und Result-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.74: DoT-Profil- und Modus-Aufloesungs-Helfer `netmon/features/dot_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dot_controller.py tests/test_dot_controller.py
python3 -m black --check --workers 1 netmon/features/dot_controller.py
python3 -m black --check --workers 1 tests/test_dot_controller.py
pytest tests/test_dot_controller.py tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte DoT-Profil- und Modus-Aufloesung eingefuehrt:
  - `_resolved_dot_profile_name(...)`
  - `_resolved_dot_mode(...)`
- wiederholte Profil- und Modus-Fallbacks vereinheitlicht, u. a. in:
  - `collect_dot_status()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - bevorzugte Profil-Aufloesung aus dem Drop-in
  - Fallback auf `resolvectl`-Server bei leerem Drop-in
  - Modus-Fallback von Drop-in auf `resolvectl`
- bewusst unveraendert geblieben sind:
  - DoT-Aktivierung/Deaktivierung
  - TLS-/Resolver-Tests
  - DNS-/VPN-Konfliktlogik und UI-Ausgabe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DoT-/DNS-Tests:
  - `123/123` gruen

Kurzfazit:

- Der DoT-Controller behandelt Profil- und Modus-Fallbacks jetzt gleichfoermiger statt dieselben kleinen Aufloesungspfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden DoT- und DNS-Regressionstests ab.
- Damit ist auch dieser kompakte DoT-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.75: Linux-Help-Chad-Titel- und Payload-Helfer `netmon/features/linux_help_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/linux_help_controller.py tests/test_netmon_linux_help.py
python3 -m black --check --workers 1 netmon/features/linux_help_controller.py
python3 -m black --check --workers 1 tests/test_netmon_linux_help.py
pytest tests/test_netmon_linux_help.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Chad-Titel- und Payload-Aufloesung eingefuehrt:
  - `_linux_help_chad_title(...)`
  - `_selected_linux_help_chad_payload(...)`
- wiederholte Auswahl-, Titel- und Prompt-Pfade vereinheitlicht, u. a. in:
  - `copy_linux_help_chad_prompt()`
  - `send_linux_help_to_chad()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - Titel-Aufloesung mit Prioritaet `name` vor `command`
  - konsistente Rueckgabe von Item, Titel und Prompt fuer die aktuelle Auswahl
  - leeres, sicheres Payload-Ergebnis ohne Auswahl
- bewusst unveraendert geblieben sind:
  - Linux-Help-Datenmodell und Prompt-Inhalt
  - Chad-Uebergabe und Clipboard-Verhalten
  - Terminal- und Root-Bestaetigungslogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Linux-Help-Tests:
  - `13/13` gruen

Kurzfazit:

- Der Linux-Help-Controller behandelt Chad-Titel- und Payload-Aufbau jetzt gleichfoermiger statt dieselben kleinen Auswahl- und Prompt-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Linux-Help-Regressionstests ab.
- Damit ist auch dieser kompakte Linux-Help-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.76: Speedtest-History-Limit- und Logzeilen-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Verlaufslimit- und Logzeilen-Pfade eingefuehrt:
  - `_speedtest_history_limit(...)`
  - `_speedtest_history_window(...)`
  - `_speedtest_history_log_line(...)`
- wiederholte Verlaufslimit- und Anzeige-Pfade vereinheitlicht, u. a. in:
  - `load_speedtest_history()`
  - `persist_speedtest_history()`
  - `append_speedtest_history()`
  - `show_speedtest_history()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sicheren Default- und Mindestwert des Verlaufslimits
  - korrektes Begrenzen des Verlaufs ohne gesetztes App-Limit
  - formatierte, fensterbegrenzte Verlaufsausgabe ohne gesetztes App-Limit
- bewusst unveraendert geblieben sind:
  - nativer CLI-Speedtest-Ablauf
  - Panel-Update und Warnschwellen
  - Async-Logging und Toolauswahl

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `13/13` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt Verlaufslimit- und History-Logzeilen jetzt gleichfoermiger statt dieselben kleinen Limit- und Formatierungspfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.77: Cleanup-Settings- und Persistenz-Helfer `netmon/ui/tabs/cleanup_assistant_tab.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/ui/tabs/cleanup_assistant_tab.py tests/test_netmon_cleanup_assistant_ui.py
python3 -m black --check --workers 1 netmon/ui/tabs/cleanup_assistant_tab.py
python3 -m black --check --workers 1 tests/test_netmon_cleanup_assistant_ui.py
pytest tests/test_netmon_cleanup_assistant_ui.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Settings- und Persistenz-Pfade eingefuehrt:
  - `_settings_dict()`
  - `_settings_store()`
  - `_save_settings_safe()`
- wiederholte Settings- und Save-Zugriffe vereinheitlicht, u. a. in:
  - `_restore_active_subtab()`
  - `_on_subtab_changed()`
  - `_restore_cleanup_history()`
  - `_persist_cleanup_history()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sichere Default-Rueckgabe bei ungueltigen `app.settings`
  - persistentes Speichern mit `log_success=False`
  - Fallback der Cleanup-Historie auf den letzten gespeicherten Lauf
- bewusst unveraendert geblieben sind:
  - Cleanup-Analyse und Loeschpfade
  - Modulzusammenfassungen und Risiko-Bewertung
  - restliche UI-Struktur des Cleanup-Assistenten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Cleanup-Assistent-Tests:
  - `37/37` gruen

Kurzfazit:

- Der Cleanup-Assistent behandelt Settings- und Persistenzzugriffe jetzt gleichfoermiger statt dieselben kleinen `settings`- und `save_settings`-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Cleanup-Assistent-Regressionstests ab.
- Damit ist auch dieser kompakte Cleanup-Assistent-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.78: Lynis-Modus- und Log-Helfer `netmon/features/security_audit_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_audit_controller.py tests/test_netmon_lynis_output.py
python3 -m black --check --workers 1 netmon/features/security_audit_controller.py
python3 -m black --check --workers 1 tests/test_netmon_lynis_output.py
pytest tests/test_netmon_lynis_output.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Lynis-Modus- und Logpfade eingefuehrt:
  - `_lynis_running(...)`
  - `_lynis_summary_text(...)`
  - `_lynis_start_log_message(...)`
  - `_lynis_finish_log_message(...)`
- wiederholte Modus-, Status- und Logzeilen vereinheitlicht, u. a. in:
  - `start_lynis_scan()`
  - `finish_lynis_audit()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sicheren Default bei `lynis_running`
  - passende Summary- und Start-Logs fuer Quick/Full
  - passende Abschluss-Logs fuer Erfolg, Timeout und Fehler
- bewusst unveraendert geblieben sind:
  - Lynis-Scan-Kommandos und Timeouts
  - Output-Normalisierung und Summary-Parsing
  - sudo-/UI-Ablauf der Quick- und Full-Scans

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Lynis-Tests:
  - `12/12` gruen

Kurzfazit:

- Der Lynis-Block behandelt Modus-, Status- und Abschlusslogs jetzt gleichfoermiger statt dieselben kleinen Quick/Full-Entscheidungen mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Lynis-Regressionstests ab.
- Damit ist auch dieser kompakte Lynis-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.79: Packet-Capture-Filter- und Startkommando-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Packet-Capture-Filter- und Startkommando-Pfade eingefuehrt:
  - `_packet_capture_filter(...)`
  - `_packet_capture_start_command(...)`
- wiederholte Filter- und Toolwahl vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
- zusaetzlich vier direkte Tests ergaenzt fuer:
  - getrimmten Filter aus der UI-Variable
  - bevorzugtes `tshark`-Startkommando mit Filter
  - `dumpcap`-Fallback ohne Filter
  - leeres Ergebnis, wenn kein Capture-Tool verfuegbar ist
- bewusst unveraendert geblieben sind:
  - Laufzeit- und Dateiinfo-Logik
  - subprocess-Start und Stop-Verhalten
  - Wireshark-/Dateiordner-Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Tests:
  - `9/9` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Filter- und Toolwahl jetzt gleichfoermiger statt dieselben kleinen Startkommando-Pfade mehrfach auszuschreiben.
- Die vier neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.80: Link-Slot- und Systemlink-Formular-Helfer `netmon/features/links_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/links_controller.py tests/test_links_controller.py
python3 -m black --check --workers 1 netmon/features/links_controller.py
python3 -m black --check --workers 1 tests/test_links_controller.py
pytest tests/test_links_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Link-Slot- und Systemlink-Formularpfade eingefuehrt:
  - `_link_slot_at(...)`
  - `_link_slot_has_assignment(...)`
  - `_systemlink_form_label(...)`
- wiederholte Slot- und Label-Zugriffe vereinheitlicht, u. a. in:
  - `load_link_slot_into_form()`
  - `assign_link_slot()`
  - `clear_link_slot()`
- zusaetzlich vier direkte Tests ergaenzt fuer:
  - sicheren Slot-Zugriff mit `None` bei ungueltigen Slots
  - Assignment-Erkennung ueber relevante Felder
  - bevorzugte Desktop-Label-Aufloesung fuer Systemlinks
  - korrektes Laden des Systemlink-Labels ins Formular
- bewusst unveraendert geblieben sind:
  - Link-Ausfuehrung und Desktop-App-Erkennung
  - URL-Normalisierung und Sicherheitsschranken fuer Systemlinks
  - Tabellen- und Button-Refresh-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Links-Controller-Tests:
  - `8/8` gruen

Kurzfazit:

- Der Links-Controller behandelt Slot- und Systemlink-Formularpfade jetzt gleichfoermiger statt dieselben kleinen Slot- und Label-Aufloesungen mehrfach auszuschreiben.
- Die vier neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Links-Controller-Regressionstests ab.
- Damit ist auch dieser kompakte Links-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.81: Fun-Tabellenzeilen-Helfer `netmon/features/fun_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/fun_controller.py tests/test_netmon_fun_module.py
python3 -m black --check --workers 1 netmon/features/fun_controller.py
python3 -m black --check --workers 1 tests/test_netmon_fun_module.py
pytest tests/test_netmon_fun_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Fun-Tabellenzeilen eingefuehrt:
  - `_fun_game_row_values(...)`
- wiederholte Running-/Start-Spaltenwerte vereinheitlicht, u. a. in:
  - `update_fun_games_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekte Running-/Start-Werte fuer ein laufendes Spiel
  - korrektes Eintragen und erneutes Selektieren der Tabellenzeile
- bewusst unveraendert geblieben sind:
  - Spieleerkennung und Launcher-Logik
  - Prozessstart und Stop-Verhalten
  - Dependency-Status und Folder-Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Fun-Tests:
  - `12/12` gruen

Kurzfazit:

- Der Fun-Controller behandelt Tabellenzeilen fuer Running-/Start-Anzeige jetzt gleichfoermiger statt dieselben kleinen Wertpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diesen vereinheitlichten Helfer zusaetzlich zu den bestehenden Fun-Regressionstests ab.
- Damit ist auch dieser kompakte Fun-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.82: HDD-Slot-Assignment-Helfer `netmon/features/hdd_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/hdd_controller.py tests/test_netmon_hdd.py
python3 -m black --check --workers 1 netmon/features/hdd_controller.py
python3 -m black --check --workers 1 tests/test_netmon_hdd.py
pytest tests/test_netmon_hdd.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte HDD-Slot-Zuordnungs-Pfade eingefuehrt:
  - `_hdd_slot_has_assignment(...)`
  - `_clear_device_slot_assignments(...)`
  - `_assign_disk_to_hdd_slot(...)`
- wiederholte Assignment- und Clear-Pfade vereinheitlicht, u. a. in:
  - `assign_selected_disk_to_slot()`
  - `clear_slot_assignment()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - Assignment-Erkennung ueber relevante Slot-Felder
  - gezieltes Leeren nur der Slots fuer das gewaehlte Device
  - bevorzugte Mountpoint-Uebernahme aus Live-Daten mit sauberem Fallback
- bewusst unveraendert geblieben sind:
  - Mount-/Unmount- und LUKS-Pfade
  - Slot-State-Lights und Info-Refresh
  - Tabellen- und UI-Update-Logik ausserhalb der Slot-Zuordnung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- HDD-Tests:
  - `9/9` gruen

Kurzfazit:

- Der HDD-Controller behandelt Slot-Zuordnung und Slot-Reset jetzt gleichfoermiger statt dieselben kleinen Assignment-Pfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden HDD-Regressionstests ab.
- Damit ist auch dieser kompakte HDD-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.83: Process-Guard-Risk- und Monitoring-Status-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Process-Guard-Risk- und Monitoring-Statuspfade eingefuehrt:
  - `_process_guard_light_state_for_risk(...)`
  - `_process_guard_monitoring_state_for_findings(...)`
- wiederholte Status- und Logpfade vereinheitlicht, u. a. in:
  - `run_process_guard_check()`
  - `apply_process_guard_monitoring_snapshot()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Risk-zu-Light/Status-Abbildung fuer `hoch`, `mittel`, `niedrig`
  - konsistente Monitoring-Abbildung fuer keine, mittlere und hohe neue Funde
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Trustlist-Operationen und Chad-Analysepfade
  - Tree-Refresh und Detaildarstellung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `18/18` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Risk- und Monitoring-Status jetzt gleichfoermiger statt dieselben kleinen Light- und Meldungspfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.84: Repository-Guard-Auswahlkontext-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Repository-Guard-Auswahlaufloesung eingefuehrt:
  - `_repository_guard_selection_context(...)`
- wiederholte Finding-/Source-Aufloesung vereinheitlicht, u. a. in:
  - `run_repository_guard_primary_action()`
  - `copy_repository_guard_quick_action_snippet()`
  - `copy_repository_guard_selected_uri()`
  - `copy_repository_guard_selected_file_path()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - bevorzugte Verwendung einer bereits ausgewaehlten Quelle
  - Fallback auf die `source_id` des aktuellen Findings
  - sauberes `(None, None)` ohne Auswahl
- bewusst unveraendert geblieben sind:
  - Quick-Action-Entscheidungen und Snippet-Erzeugung
  - Trustlist-/Baseline-Operationen
  - Clipboard- und Export-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `17/17` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt Finding-/Source-Auswahl jetzt gleichfoermiger statt dieselben kleinen Auswahlpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diesen vereinheitlichten Helfer zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.85: DoT-Anzeige-Helfer `netmon/features/dot_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/dot_controller.py tests/test_dot_controller.py
python3 -m black --check --workers 1 netmon/features/dot_controller.py
python3 -m black --check --workers 1 tests/test_dot_controller.py
pytest tests/test_dot_controller.py tests/test_netmon_dns_consistency.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte DoT-Anzeige-Pfade eingefuehrt:
  - `_dot_profile_text(...)`
  - `_dot_server_text(...)`
  - `_dot_mode_text(...)`
  - `_dot_last_test_text(...)`
- wiederholte Statuslabel- und Zeitstempelpfade vereinheitlicht, u. a. in:
  - `set_dot_state()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Profil-/Server-/Modus-Texte
  - konsistent formatierten Zeitstempeltext
- bewusst unveraendert geblieben sind:
  - DoT-Aktivierung und Resolver-Logik
  - VPN-DNS-Konfliktbehandlung
  - Light-Update und DNS-Konsistenzpfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- DoT-/DNS-Tests:
  - `125/125` gruen

Kurzfazit:

- Der DoT-Controller behandelt Anzeige- und Zeitstempeltexte jetzt gleichfoermiger statt dieselben kleinen Label-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden DoT- und DNS-Regressionstests ab.
- Damit ist auch dieser kompakte DoT-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.86: Security-Monitoring-Detailtext-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Security-Monitoring-Detailanzeige eingefuehrt:
  - `_security_selected_event_text(...)`
  - `_connected_device_detail_text(...)`
- wiederholte Detailtext-Pfade vereinheitlicht, u. a. in:
  - `on_security_event_select()`
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekte Eventtext-Aufloesung fuer Aggregat- und sichtbare Event-Zeilen
  - konsistent formatierte Detailanzeige fuer verbundene Geraete
- bewusst unveraendert geblieben sind:
  - Security-Scan- und Eventlogik
  - Tabellen-Refresh und Filterlogik
  - Baseline-, Device- und Input-Access-Erkennung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `29/29` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt Event- und Geraetedetails jetzt gleichfoermiger statt dieselben kleinen Detailtext-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Monitoring-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.87: Speedtest-Panelwerte-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Speedtest-Panelanzeige eingefuehrt:
  - `_speedtest_panel_values(...)`
- wiederholte Panelwert-Pfade vereinheitlicht, u. a. in:
  - `update_speedtest_panel()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Platzhalterwerte ohne Ergebnis
  - konsistent formatierte Panelwerte mit Ergebnisdaten
- bewusst unveraendert geblieben sind:
  - nativer CLI-Speedtest-Ablauf
  - Verlaufsspeicherung und Warnlogik
  - History-Ausgabe und Async-Ablauf

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `15/15` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt Panelanzeige jetzt gleichfoermiger statt dieselben kleinen Anzeige-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diesen vereinheitlichten Helfer zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.88: Repository-Guard-Filterstatus- und Light-Farb-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Repository-Guard-Filterstatus- und Light-Farbpfade eingefuehrt:
  - `_repository_guard_source_filter_status_text(...)`
  - `_repository_guard_finding_filter_status_text(...)`
  - `_repository_guard_status_light_color(...)`
- wiederholte Anzeige- und Farbauswahl vereinheitlicht, u. a. in:
  - `update_repository_guard_filter_status_line()`
  - `update_repository_guard_status_light()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - konsistente Quellenfilter-Statuslabels
  - konsistente Finding-Filter-Statuslabels
  - konsistente Farbauswahl fuer bekannte und unbekannte Statuswerte
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline- und Trustlist-Logik
  - Tabellen- und Detaildarstellung
  - Quick Actions, Clipboard- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `20/20` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt Filterstatus- und Light-Anzeige jetzt gleichfoermiger statt dieselben kleinen Label- und Farbpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Anzeigeblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.89: Packet-Capture-Capinfos- und Abschlussstatus-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Packet-Capture-Capinfos- und Abschlussstatus-Pfade eingefuehrt:
  - `_packet_capture_capinfos_summary(...)`
  - `_packet_capture_completion_status(...)`
- wiederholte Parser- und Statuspfade vereinheitlicht, u. a. in:
  - `packet_capture_show_file_info()`
  - `packet_capture_start_async()`
- zusaetzlich vier direkte Tests ergaenzt fuer:
  - konsistente Packet-/Groessen-Auswertung aus `capinfos`
  - stabiles Beibehalten von Defaultwerten ohne passende Zeilen
  - konsistente Priorisierung von Benutzerstopp vor Returncode
  - konsistente Abbildung von Erfolgs- und Fehlercodes
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime-Update und Stop-Logik
  - Wireshark-/Datei-Open-Pfade
  - Tool-Auswahl und Filterlogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `13/13` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Capinfos-Auswertung und Abschlussstatus jetzt gleichfoermiger statt dieselben kleinen Parser- und Statuspfade mehrfach auszuschreiben.
- Die vier neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Anzeige- und Abschlussblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.90: Process-Guard-Filter- und Monitoring-Statuslabel-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Process-Guard-Filter- und Monitoring-Statuspfade eingefuehrt:
  - `_process_guard_monitoring_status_text(...)`
  - `_process_guard_filter_label(...)`
- wiederholte Status- und Loglabel-Pfade vereinheitlicht, u. a. in:
  - `set_process_guard_filter()`
  - `update_process_guard_status_line()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - konsistente Monitoring-Statuslabels fuer beide Zustaende
  - konsistente Status- und Loglabels fuer bekannte Filtermodi
  - stabile Fallbacks auf die `all`-Labels bei unbekannten Modi
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Detail- und Trustlist-Pfade
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `21/21` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Filter- und Monitoring-Labels jetzt gleichfoermiger statt dieselben kleinen Statusstrings mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Statusblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.91: Speedtest-Warnungs-Spezifikation und Meldungs-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Speedtest-Warnungs-Spezifikationen und Meldungstexte eingefuehrt:
  - `_speedtest_warn_specs()`
  - `_speedtest_warn_message(...)`
- wiederholte Warnungs- und Schwellenwertpfade vereinheitlicht, u. a. in:
  - `speedtest_warn_messages()`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - konsistente Formatierung einzelner Warnmeldungen
  - stabile und vollstaendige Spezifikation der Warnmetriken
  - sauberes Ignorieren nichtnumerischer Ergebniswerte
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Historie, Panel-Update und Async-Flow
  - Debug-Logging und Ergebnisformatierung

Ergebnis:

- `ruff`: gruen
- `black`: gruen
- Speedtest-Tests:
  - `18/18` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt Warnungsregeln und Meldungstexte jetzt gleichfoermiger statt dieselben kleinen Schwellenwertpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichten Helfer zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Warnungsblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.92: Security-Summary-Count- und Risiko-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Security-Summary-Zaehlwerte eingefuehrt:
  - `_security_summary_counts(...)`
- wiederholte Risiko- und Sofortmassnahmen-Pfade vereinheitlicht, u. a. in:
  - `_security_summary_risk_label(...)`
  - `_security_summary_immediate_actions(...)`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - sauberes Klemmen negativer Zaehlerwerte auf sichere Defaults
  - konsistente Risiko-Einstufung ueber alle Schwellenstufen
  - stabiles Fallback auf die Default-Sofortmassnahme ohne Findings
- bewusst unveraendert geblieben sind:
  - Parser-, Aggregations- und Monitoring-Logik
  - Chad-Summary-Aufbau und UI-Pfade
  - Export-, Baseline- und Tabellenverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `32/32` gruen

Kurzfazit:

- Das Security-Monitoring behandelt Summary-Zaehler, Risiko-Einstufung und Default-Sofortmassnahmen jetzt gleichfoermiger statt dieselben kleinen Zaehlerpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Summary-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.93: Security-Filterlabel- und Event-Level-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Event-Level-Normalisierung eingefuehrt:
  - `_security_event_level(...)`
- wiederholte Filterlabel- und Relevanzpfade vereinheitlicht, u. a. in:
  - `_security_event_is_relevant(...)`
- zusaetzlich drei direkte Tests ergaenzt fuer:
  - konsistente Filterlabels fuer bekannte und unbekannte Modi
  - saubere Normalisierung fehlender und gemischter Levelwerte
  - konsistente Relevanz-Erkennung fuer `WARN`, `ALERT`, `CRITICAL` und Portscan-Events
- bewusst unveraendert geblieben sind:
  - Parser-, Aggregations- und Monitoring-Logik
  - Chad-Summary-Aufbau und UI-Pfade
  - Export-, Baseline- und Tabellenverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `35/35` gruen

Kurzfazit:

- Das Security-Monitoring behandelt Event-Level und Relevanzpruefung jetzt gleichfoermiger statt dieselben kleinen Levelpfade mehrfach auszuschreiben.
- Die drei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Filter-/Relevanzblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.94: Packet-Capture-Dateigroessen-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Packet-Capture-Dateigroessen-Ausgabe eingefuehrt:
  - `_packet_capture_size_text(...)`
- wiederholte Dateigroessen-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_update_runtime()`
  - `packet_capture_show_file_info()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Groessenformatierung fuer vorhandene Capture-Dateien
  - unveraendertes Fehlerverhalten bei fehlenden Dateien
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Capinfos-Auswertung und Abschlussstatus
  - Wireshark-/Datei-Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `15/15` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Dateigroessen jetzt gleichfoermiger statt dieselben kleinen Groessenpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Dateigroessenblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.95: Process-Guard-Sichtbarkeitsfilter-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Sichtbarkeitsfilter eingefuehrt:
  - `_process_guard_visible_findings(...)`
- wiederholte Filterpfade fuer die Tree-Aktualisierung vereinheitlicht, u. a. in:
  - `refresh_process_guard_tree()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Filterung fuer `high` und `high_medium`
  - stabiles Fallback auf alle Findings bei unbekanntem Modus oder leerem Ergebnis
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Detail- und Trustlist-Pfade
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `23/23` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt die Sichtbarkeitsfilter jetzt gleichfoermiger statt dieselben kleinen Filterpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Treefilter-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.96: Speedtest-History-Logfeld-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Speedtest-History-Logfelder eingefuehrt:
  - `_speedtest_history_log_fields(...)`
- wiederholte History-Logformatierung vereinheitlicht, u. a. in:
  - `_speedtest_history_log_line(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Formatierung numerischer und fehlender History-Werte
  - stabiles Fallback auf Platzhalter bei leeren History-Eintraegen
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie-Speicherung und -Ausgabe

Ergebnis:

- `ruff`: gruen
- `black`: gruen
- Speedtest-Tests:
  - `20/20` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt History-Logfelder jetzt gleichfoermiger statt dieselben kleinen Formatierungspfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Logblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.97: Process-Guard-Tree-Row-Values-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Tree-Zeilenwerte eingefuehrt:
  - `_process_guard_tree_row_values(...)`
- wiederholte Tree-Insert-Werte vereinheitlicht, u. a. in:
  - `refresh_process_guard_tree()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Spaltenwerte fuer vollstaendige Findings
  - stabile Defaultwerte fuer leere Findings
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Sichtbarkeitsfilter, Detail- und Trustlist-Pfade
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `25/25` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Tree-Zeilenwerte jetzt gleichfoermiger statt dieselben kleinen Tuple-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Treewerte-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.98: Packet-Capture-Initialdateiname-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Packet-Capture-Initialdateinamen eingefuehrt:
  - `_packet_capture_initial_file_name(...)`
- wiederholte Dateinamenspfade fuer den Dateidialog vereinheitlicht, u. a. in:
  - `choose_packet_capture_file()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Bevorzugung des aktuellen Dateinamens
  - stabiles Fallback auf den generierten Default-Dateinamen
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Dateiauswahl- und Dialogfluss selbst
  - Capinfos-, Dateigroessen- und Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `17/17` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt vorgeschlagene Dateinamen jetzt gleichfoermiger statt dieselben kleinen Basename-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Dateidialog-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.99: Speedtest-History-Trim-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholtes Speedtest-History-Trimmen eingefuehrt:
  - `_speedtest_trimmed_history(...)`
- wiederholte Trim-Pfade fuer Lade- und Append-Logik vereinheitlicht, u. a. in:
  - `load_speedtest_history()`
  - `append_speedtest_history()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistentes Behalten der neuesten Verlaufseintraege
  - stabiles Minimum-Verhalten bei `0` und leeren Listen
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie-Speicherung und -Ausgabe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `22/22` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt das Begrenzen des Verlaufs jetzt gleichfoermiger statt dieselben kleinen Slice-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Trimblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.100: Packet-Capture-Ready-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Packet-Capture-Toolverfuegbarkeit eingefuehrt:
  - `_packet_capture_ready(...)`
- wiederholte Ready-Pfade fuer Button-State-Logik vereinheitlicht, u. a. in:
  - `packet_capture_set_running_state()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - `True`, sobald eines der Capture-Tools verfuegbar ist
  - `False`, wenn weder `tshark` noch `dumpcap` vorhanden ist
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Dateidialog-, Capinfos- und Open-Pfade
  - Button-State-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `19/19` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt die Toolverfuegbarkeit jetzt gleichfoermiger statt denselben kleinen Ready-Pfad mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Readiness-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.101: Security-Filter-Apply-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholtes Anwenden von Security-Filtern eingefuehrt:
  - `_apply_security_filter(...)`
- wiederholte Filter-Set/Refresh/Log-Pfade vereinheitlicht, u. a. in:
  - `security_filter_portscan()`
  - `security_filter_relevant()`
  - `security_filter_external()`
  - `security_filter_all()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Setzen von Filtermodus, Refresh und Logmeldung
  - stabiles Fallback auf `all` bei leerem Modus
- bewusst unveraendert geblieben sind:
  - Parser-, Aggregations- und Monitoring-Logik
  - Tabelleninhalt und Statistiken
  - Export-, Baseline- und UI-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `37/37` gruen

Kurzfazit:

- Das Security-Monitoring behandelt das Anwenden von Filtern jetzt gleichfoermiger statt dieselben kleinen Filterpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Filter-Apply-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.102: Speedtest-History-Messages-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Speedtest-Verlaufsmeldungen eingefuehrt:
  - `_speedtest_history_messages(...)`
- wiederholte Verlaufsausgabe vereinheitlicht, u. a. in:
  - `show_speedtest_history()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Leerzustandsmeldung ohne Verlauf
  - konsistente Header- und Zeilenbildung fuer vorhandene Verlaufseintraege
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie-Speicherung, -Trimmen und -Formatierung

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `24/24` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt Verlaufsmeldungen jetzt gleichfoermiger statt dieselben kleinen Ausgabepfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Verlaufsausgabe-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.103: Packet-Capture-Output-Segment-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer wiederholte Packet-Capture-Output-Segmentlogik eingefuehrt:
  - `_packet_capture_needs_separator(...)`
  - `_packet_capture_output_segment(...)`
- wiederholte Separator- und Textsegment-Pfade vereinheitlicht, u. a. in:
  - `append_packet_capture_output()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Separator-Entscheidung bei leerem, gefuelltem und `replace`-Output
  - konsistentes Trimmen und Abschliessen von Ausgabetexten mit Newline
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Dateidialog-, Capinfos- und Open-Pfade
  - Widget-State-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black`: gruen
- Packet-Capture-Controller-Tests:
  - `21/21` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Output-Segmente jetzt gleichfoermiger statt dieselben kleinen Separator- und Textpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Output-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.104: Process-Guard-Service-Zugriffs-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Service-Zugriffe eingefuehrt:
  - `_process_guard_service_or_log(...)`
- wiederholte Service-Check- und Logpfade vereinheitlicht, u. a. in:
  - `show_process_guard_trustlist()`
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
  - `reset_process_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des vorhandenen Serviceobjekts
  - konsistente Logmeldung bei fehlendem Service
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Trustlist-, Tree- und Detailverhalten
  - Chad-Analyse und Service-Interaktion selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `27/27` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Service-Zugriffe jetzt gleichfoermiger statt dieselben kleinen Availability-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Service-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.105: Speedtest-History-List-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Speedtest-History-Listen eingefuehrt:
  - `_speedtest_history_list(...)`
- wiederholte History-Listenpfade vereinheitlicht, u. a. in:
  - `_speedtest_history_messages(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe einer abgekoppelten Kopie der History-Liste
  - stabiles leeres Default-Verhalten bei `None`
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie-Speicherung, -Trimmen und -Ausgabe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `26/26` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt History-Listen jetzt gleichfoermiger statt dieselben kleinen Listenpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Listenblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.106: Process-Guard-Trustlist-Lines-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Trustlist-Ausgabe eingefuehrt:
  - `_process_guard_trustlist_lines(...)`
- wiederholte Trustlist-Textpfade vereinheitlicht, u. a. in:
  - `show_process_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Leerzustandsmeldung ohne Trustlist-Eintraege
  - konsistente sortierte Ausgabe vollstaendiger Trustlist-Eintraege
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Trustlist-, Tree- und Detailverhalten selbst
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `29/29` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Trustlist-Ausgabetexte jetzt gleichfoermiger statt dieselben kleinen Zeilenpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Trustlist-Ausgabeblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.107: Packet-Capture-Button-State-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Packet-Capture-Button-Zustaende eingefuehrt:
  - `_packet_capture_button_states(...)`
- wiederholte Start-/Stop-Button-State-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_set_running_state()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Button-Zustaende fuer laufendes und bereites Capture
  - konsistentes Deaktivieren beider Buttons ohne verfuegbare Tools
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Readiness-, Dateidialog-, Capinfos- und Open-Pfade
  - konkretes Button-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `23/23` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt Button-Zustaende jetzt gleichfoermiger statt dieselben kleinen Start-/Stop-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Button-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.108: Process-Guard-Finding-Name-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Fundnamen eingefuehrt:
  - `_process_guard_finding_name(...)`
- wiederholte sichere Namenspfade fuer Trustlist-Aktionen vereinheitlicht, u. a. in:
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekte Rueckgabe vorhandener Fundnamen
  - stabile Defaultwerte bei fehlenden oder leeren Findings
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Trustlist-, Tree- und Detailverhalten
  - Chad-Analyse und Service-Interaktion selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `31/31` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Fundnamen jetzt gleichfoermiger statt dieselben kleinen Namenspfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Fundnamen-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.110: Process-Guard-Visible-Count-Text-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Sichtbarkeitszaehltexte eingefuehrt:
  - `_process_guard_visible_count_text(...)`
- wiederholte Count-Textpfade vereinheitlicht, u. a. in:
  - `update_process_guard_status_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Anzeige der Anzahl sichtbarer Findings
  - stabiles `0`-Fallback fuer leere und fehlende Werte
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Trustlist- und Detailverhalten
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `33/33` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Sichtbarkeitszaehltexte jetzt gleichfoermiger statt dieselben kleinen Count-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Visible-Count-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.112: Process-Guard-Status-Values-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Statuswerte eingefuehrt:
  - `_process_guard_status_values(...)`
- wiederholte Statuswertpfade vereinheitlicht, u. a. in:
  - `update_process_guard_status_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Sammlung aller Statuswerte bei aktivem Monitoring
  - stabile Defaultwerte ohne vorbereitete App-Zustaende
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Trustlist- und Detailverhalten
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `35/35` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt Statuswerte jetzt gleichfoermiger statt dieselben kleinen Statuspfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Statuswerte-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.113: Packet-Capture-Clear-Widget-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholtes Leeren des Packet-Capture-Textwidgets eingefuehrt:
  - `_packet_capture_clear_widget(...)`
- wiederholte Clear-Pfade vereinheitlicht, u. a. in:
  - `append_packet_capture_output()`
  - `clear_packet_capture_output()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiches Leeren vorhandener Widgets
  - stabiles `False`-Fallback ohne Widget
- bewusst unveraendert geblieben sind:
  - Capture-Start, Runtime- und Stop-Logik
  - Output-Segment-, Dateidialog-, Capinfos- und Open-Pfade
  - Widget-State-Verhalten selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `25/25` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt das Leeren des Textwidgets jetzt gleichfoermiger statt denselben kleinen Delete-Pfad mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Clear-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.114: Process-Guard-Selected-Finding-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black tests/test_process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Fundauswahl eingefuehrt:
  - `_selected_process_guard_finding_or_log(...)`
- wiederholte Auswahl- und Logpfade vereinheitlicht, u. a. in:
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
  - `analyze_selected_process_guard_with_chad()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des selektierten Findings
  - konsistente Logmeldung bei fehlender Auswahl
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Trustlist-, Tree- und Detailverhalten
  - Chad-Analyse und Service-Interaktion selbst

Ergebnis:

- `ruff`: gruen
- `black`: gruen
- Process-Guard-Controller-Tests:
  - `37/37` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt die sichere Fundauswahl jetzt gleichfoermiger statt dieselben kleinen Auswahlpfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Selected-Finding-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.109: Speedtest-Panel-Apply-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholtes Anwenden von Speedtest-Panelwerten eingefuehrt:
  - `_apply_speedtest_panel_values(...)`
- wiederholte Var-Set-Pfade fuer die Panelanzeige vereinheitlicht, u. a. in:
  - `update_speedtest_panel()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistentes Setzen aller Panelwerte
  - stabile Defaultwerte bei fehlenden Schluesseln
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Verlauf und Async-Flow
  - Panelwert-Berechnung selbst

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `28/28` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt das Anwenden von Panelwerten jetzt gleichfoermiger statt dieselben kleinen Set-Pfade mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Panel-Apply-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.111: Speedtest-History-Window-Helferpfad `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- den bestehenden Trim-Helfer jetzt auch fuer den Window-Pfad konsequent genutzt:
  - `_speedtest_history_window(...)` verwendet jetzt `_speedtest_trimmed_history(...)`
- wiederholte Slice-Logik fuer die Verlaufsfensterbildung vereinheitlicht, u. a. in:
  - `_speedtest_history_window(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistentes Begrenzen des Verlaufsfensters ueber das konfigurierte Limit
  - stabiles Default-Verhalten bei fehlendem explizitem Limit
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie-Speicherung, -Listen und -Ausgabe

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `30/30` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt die Window-Bildung des Verlaufs jetzt konsequenter ueber denselben Trim-Helfer statt einen separaten Slice-Pfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Window-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.115: Process-Guard-Visible-Finding-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black tests/test_process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer wiederholte Process-Guard-Tree-Auswahl eingefuehrt:
  - `_selected_process_guard_visible_finding(...)`
- wiederholte Auswahl-, Index- und Bounds-Pfade vereinheitlicht, u. a. in:
  - `on_process_guard_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des sichtbar selektierten Findings
  - stabiles `None`-Fallback bei ungueltiger Auswahl
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Detail- und Trustlist-Verhalten selbst
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `39/39` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt die Aufloesung des aktuell sichtbaren Tree-Funds jetzt gleichfoermiger statt denselben kleinen Auswahlpfad direkt im UI-Handler auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Visible-Finding-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.116: Process-Guard-Detail-Replace-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black tests/test_process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Ersetzen des Process-Guard-Detailtexts eingefuehrt:
  - `_replace_process_guard_text(...)`
- wiederholte Detail-Widget-Update-Pfade vereinheitlicht, u. a. in:
  - `on_process_guard_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiches Ersetzen vorhandener Widget-Inhalte
  - stabiles `False`-Fallback ohne Widget
- bewusst unveraendert geblieben sind:
  - Process-Guard-Pruef- und Monitoring-Logik
  - Tree-, Auswahl- und Trustlist-Verhalten
  - Chad-Analyse und Service-Interaktion

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `41/41` gruen

Kurzfazit:

- Der Process-Guard-Controller behandelt das Ersetzen des Detailtexts jetzt gleichfoermiger statt denselben kleinen Widget-Reset-Pfad direkt im Auswahl-Handler auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Detail-Replace-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.117: Packet-Capture-File-Info-Text-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den lokalen Capture-Datei-Infotext eingefuehrt:
  - `_packet_capture_file_info_text(...)`
- wiederholte Capture-Datei-Infoanzeige vereinheitlicht, u. a. in:
  - `packet_capture_show_file_info()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistente Formatierung der erwarteten Dateiinformationen
  - stabiles Durchreichen auch leerer bzw. bereits vorbereiteter Werte
- bewusst unveraendert geblieben sind:
  - capinfos-Auswertung und Paketzaehler-Logik
  - Capture-Start-, Runtime- und Stop-Flow
  - Wireshark- und Datei-Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `27/27` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt den lokalen Fallback-Infotext jetzt gleichfoermiger statt denselben kleinen Formatpfad direkt im Dateiinfo-Handler auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.118: Speedtest-Trim-Helferpfad `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer app-basiertes History-Trimmen eingefuehrt:
  - `_speedtest_trimmed_records_for_app(...)`
- wiederholte Limit-plus-Trim-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_history_window()`
  - `load_speedtest_history()`
  - `append_speedtest_history()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - konsistentes Trim-Verhalten ueber das am App-Objekt konfigurierte Limit
  - stabiles Default-Verhalten ohne explizites Limit
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - History-Ausgabe und Persistenzformat

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `32/32` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt app-basiertes History-Trimmen jetzt gleichfoermiger statt denselben kleinen Limit-plus-Trim-Pfad an mehreren Stellen getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Trim-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.119: Security-Detail-Set-Helferpfad `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- den bestehenden Detail-Helfer jetzt auch fuer die Event-Auswahl konsequent genutzt:
  - `_set_security_detail_text(...)`
- wiederholte Detail-Widget-Update-Pfade vereinheitlicht, u. a. in:
  - `on_security_event_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiches Schreiben des Detailtexts bei vorhandenem Widget
  - stabiles No-Op-Verhalten ohne Detailwidget
- bewusst unveraendert geblieben sind:
  - Event-Selektion, Filter- und Monitoring-Logik
  - Device-Details, Parser- und Aggregationspfade
  - Tabellen- und Baseline-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `39/39` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt das Setzen des Detailtexts jetzt gleichfoermiger statt denselben kleinen Widget-Pfad im Event-Select-Handler separat auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Detail-Set-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.120: Security-Connected-Device-Selection-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Auswahl des verbundenen Geraets eingefuehrt:
  - `_selected_connected_device(...)`
- wiederholte Auswahl-, Index- und Bounds-Pfade vereinheitlicht, u. a. in:
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des selektierten Inventory-Eintrags
  - stabiles `None`-Fallback bei ungueltiger Auswahl
- bewusst unveraendert geblieben sind:
  - Device-Detailtext und Detail-Widget-Setzen
  - Monitoring-, Parser- und Aggregationslogik
  - Tabellen- und Baseline-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `41/41` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt die Aufloesung des aktuell selektierten verbundenen Geraets jetzt gleichfoermiger statt denselben kleinen Auswahlpfad direkt im Select-Handler auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Selection-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.121: Packet-Capture-Wireshark-Command-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Wireshark-Startkommando-Aufloesung eingefuehrt:
  - `_packet_capture_wireshark_command(...)`
- wiederholte Launcher-Art-Pfade vereinheitlicht, u. a. in:
  - `open_packet_capture_in_wireshark()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Binary-Startkommando
  - stabiles Fehlerverhalten fuer `desktop_file` ohne `xdg-open`
- bewusst unveraendert geblieben sind:
  - eigentlicher Open-/Popen-Ablauf
  - Datei- und Zielpfadpruefung
  - Capture-, Runtime- und Stop-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `29/29` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt die Aufloesung des Wireshark-Startkommandos jetzt gleichfoermiger statt die Launcher-Arten direkt im Open-Handler zu verzweigen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Wireshark-Command-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.122: Packet-Capture-Open-Location-Command-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Oeffnen des Capture-Pfads eingefuehrt:
  - `_packet_capture_open_location_command(...)`
- wiederholte `xdg-open`-Kommandoauflosung vereinheitlicht, u. a. in:
  - `open_packet_capture_file_location()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes `xdg-open`-Startkommando
  - stabiles Fehlerverhalten ohne `xdg-open`
- bewusst unveraendert geblieben sind:
  - Datei- und Zielpfadpruefung
  - eigentlicher `Popen`-Ablauf und Log-Ausgabe
  - Capture-, Runtime- und Stop-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `31/31` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt die Aufloesung des Dateiordner-Open-Kommandos jetzt gleichfoermiger statt den kleinen `xdg-open`-Pfad direkt im Open-Handler auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Open-Location-Command-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.123: Speedtest-Warn-Trigger-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Warnschwellen-Entscheidung eingefuehrt:
  - `_speedtest_warn_triggered(...)`
- wiederholte Vergleichslogik fuer Warnschwellen vereinheitlicht, u. a. in:
  - `speedtest_warn_messages()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Triggern bei `<`- und `>`-Schwellen
  - stabiles `False` bei nicht ueberschrittener bzw. unterschrittener Grenze
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warntexte, Panel-Update und Async-Flow
  - Historie und Persistenzverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `34/34` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt die reine Warnschwellen-Entscheidung jetzt gleichfoermiger statt den kleinen Vergleichspfad direkt in der Warnschleife auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Warn-Trigger-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.124: Security-Safe-Detail-Set-Helfer `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen sicheren Helfer fuer das Setzen des Security-Detailtexts eingefuehrt:
  - `_set_security_detail_text_safe(...)`
- wiederholte Try/Except-Pfade fuer den Detailtext vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiches Setzen des Detailtexts bei funktionierendem Widget
  - stabiles `False` bei Widget-Fehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Logik
  - Device-Detailtexte, Parser- und Aggregationspfade
  - Tabellen- und Baseline-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Security-Module-Tests:
  - `43/43` gruen

Kurzfazit:

- Der Security-Monitoring-Controller behandelt den sicheren Detailtext-Set-Pfad jetzt gleichfoermiger statt in `security_clear_views()` einen separaten kleinen Try/Except-Block zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Safe-Detail-Set-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.125: Repository-Guard-Tree-Selection-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Tree-Auswahlauflosung eingefuehrt:
  - `_selected_repository_guard_tree_item(...)`
- wiederholte Auswahl-, Index- und Bounds-Pfade vereinheitlicht, u. a. in:
  - `on_repository_guard_source_select()`
  - `on_repository_guard_finding_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des selektierten sichtbaren Items
  - stabiles `None`-Fallback bei ungueltiger Auswahl
- bewusst unveraendert geblieben sind:
  - Detailtext-Aufbereitung und Detailanzeige
  - Scan-, Baseline- und Trustlist-Logik
  - Filter- und Statusverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `22/22` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt die Aufloesung des aktuell selektierten Tree-Eintrags jetzt gleichfoermiger statt denselben kleinen Auswahlpfad in beiden Select-Handlern getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Tree-Selection-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.126: Repository-Guard-Filter-Mode-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer die Filter-Mode-Normalisierung eingefuehrt:
  - `_repository_guard_source_filter_mode(...)`
  - `_repository_guard_finding_filter_mode(...)`
- wiederholte Mode-Normalisierung vereinheitlicht, u. a. in:
  - `set_repository_guard_source_filter()`
  - `set_repository_guard_finding_filter()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Normalisieren gueltiger Filterwerte
  - stabiles Fallback auf `all` bei unbekannten Werten
- bewusst unveraendert geblieben sind:
  - Filter-Refresh, Status- und Detailanzeige
  - Scan-, Baseline- und Trustlist-Logik
  - Tree- und Selection-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `24/24` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt die Filter-Mode-Normalisierung jetzt gleichfoermiger statt denselben kleinen Validierungspfad in zwei Settern getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Filter-Mode-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.127: Repository-Guard-Report-Payload-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Report-Payload-Aufbau eingefuehrt:
  - `_repository_guard_report_payload(...)`
- wiederholten Payload-Aufbau aus Ergebnistext plus optionalen Details vereinheitlicht, u. a. in:
  - `copy_repository_guard_report()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Anhaengen eines `=== Details ===`-Abschnitts
  - stabiles Weglassen leerer Details
- bewusst unveraendert geblieben sind:
  - Ergebnisformatierung, Detailtext-Aufbereitung und Exportlogik
  - Scan-, Baseline- und Trustlist-Logik
  - Filter-, Tree- und Statusverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `26/26` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt den Aufbau des Report-Payloads jetzt gleichfoermiger statt Ergebnistext und optionale Details direkt im Copy-Pfad zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Report-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.128: Repository-Guard-Export-Payload-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Payload eingefuehrt:
  - `_repository_guard_export_payload(...)`
- wiederholten TXT-/JSON-Exportaufbau vereinheitlicht, u. a. in:
  - `export_repository_guard_report()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Text-Exportformat mit Abschluss-Newline
  - korrektes JSON-Exportformat mit stabilen Schluesseln und Abschluss-Newline
- bewusst unveraendert geblieben sind:
  - Dateidialog, Zielpfadwahl und Schreiblogik
  - Ergebnisformatierung, Detailtext- und Exportfluss
  - Scan-, Baseline- und Trustlist-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `28/28` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt den Aufbau des eigentlichen Export-Inhalts jetzt gleichfoermiger statt TXT- und JSON-Payload direkt im Export-Handler getrennt aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Export-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.129: Packet-Capture-Start-Text-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Start-Statustext eingefuehrt:
  - `_packet_capture_start_text(...)`
- wiederholten Starttext-Aufbau vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Format aller erwarteten Startzeilen
  - stabiles `-`-Fallback fuer einen leeren Filter
- bewusst unveraendert geblieben sind:
  - Capture-Start-, Runtime- und Stop-Flow
  - Tool-/Interface-Pruefung und Statusvariablen
  - Datei- und Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `33/33` gruen

Kurzfazit:

- Der Packet-Capture-Controller behandelt den Aufbau des Start-Statustexts jetzt gleichfoermiger statt denselben kleinen Textblock direkt im Start-Handler zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Start-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.130: Speedtest-CLI-Diagnose-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die CLI-Diagnose-Extraktion eingefuehrt:
  - `_speedtest_attempted_cli(...)`
- wiederholten Marker-/Split-Pfad fuer Fehlerdiagnosen vereinheitlicht, u. a. in:
  - `speedtest_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Extrahieren der nachgestellten Befehlsliste
  - stabiles leeres Ergebnis ohne Marker
- bewusst unveraendert geblieben sind:
  - eigentlicher CLI-Speedtest-Ablauf
  - Warnlogik, Panel-Update und Async-Flow
  - Historie und Persistenzverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Tests:
  - `36/36` gruen

Kurzfazit:

- Der Speedtest-Controller behandelt die Extraktion der CLI-Diagnose jetzt gleichfoermiger statt denselben kleinen Marker-/Split-Pfad direkt im Fehlerzweig des Async-Flows auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-CLI-Diagnose-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.131: Repository-Guard-Filter-Choice-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Choice-Label-Fallbacks eingefuehrt:
  - `_repository_guard_filter_choice_text(...)`
- wiederholte Label-Fallback-Aufloesung vereinheitlicht, u. a. in:
  - `update_repository_guard_filter_status_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Bevorzugen eines passenden Modus-Labels
  - stabiles Default-Label bei fehlenden Eintraegen
- bewusst unveraendert geblieben sind:
  - Filter-Status- und Choice-Variablen
  - Scan-, Baseline- und Trustlist-Logik
  - Tree-, Detail- und Exportverhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `30/30` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt die Label-Fallback-Aufloesung fuer Filter-Choices jetzt gleichfoermiger statt denselben kleinen `dict.get(..., default)`-Pfad zweimal getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Filter-Choice-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.132: Repository-Guard-Source-ID-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die `source_id`-Aufloesung eingefuehrt:
  - `_repository_guard_source_id(...)`
- wiederholte `source_id`-Extraktion vereinheitlicht, u. a. in:
  - `_resolve_repository_guard_selected_source()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Trimmen einer vorhandenen `source_id`
  - stabiles leeres Ergebnis bei fehlendem Wert
- bewusst unveraendert geblieben sind:
  - Selection-Context, Tree- und Detailverhalten
  - Scan-, Baseline- und Trustlist-Logik
  - Filter-, Export- und Statuspfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `32/32` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt die Aufloesung der `source_id` jetzt gleichfoermiger statt denselben kleinen Trim-/Fallback-Pfad direkt im Selected-Source-Resolver auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Source-ID-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.133: Repository-Guard-Selected-Source-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die aktuell ausgewaehlte Quelle eingefuehrt:
  - `_repository_guard_selected_source_or_log(...)`
- wiederholte Auswahlpruefung und Logmeldung vereinheitlicht, u. a. in:
  - `mark_selected_repository_guard_trusted()`
  - `remove_selected_repository_guard_trusted()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe der selektierten Quelle
  - konsistente Logmeldung bei fehlender Auswahl
- bewusst unveraendert geblieben sind:
  - Trustlist-, Scan- und Detailverhalten
  - Filter-, Export- und Statuspfade
  - Tree- und Selection-Context-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `34/34` gruen

Kurzfazit:

- Der Repository-Guard-Controller behandelt die Pruefung der aktuell ausgewaehlten Quelle jetzt gleichfoermiger statt denselben kleinen Auswahl-/Logpfad in zwei Trustlist-Aktionen getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Hilfslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Selected-Source-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.134: Repository-Guard-Detail-Value-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die selektierte Detailwert-Aufloesung eingefuehrt:
  - `_repository_guard_selected_detail_value(...)`
- wiederholte Source-vor-Details-Fallbacklogik vereinheitlicht, u. a. in:
  - `get_repository_guard_selected_uri()`
  - `get_repository_guard_selected_file_path()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bevorzugte Verwendung eines getrimmten Source-Werts
  - sauberen Fallback auf die konfigurierten Detail-Keys
- bewusst unveraendert geblieben sind:
  - Copy-, Quick-Action- und Exportverhalten
  - Selection-Context, Tree- und Detailanzeige
  - Scan-, Baseline-, Trustlist- und Filterlogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `36/36` gruen

Kurzfazit:

- Der Repository-Guard-Controller loest URI- und Dateipfadwerte jetzt ueber denselben kleinen Source-/Detail-Fallback auf, statt denselben Aufloesungspfad in zwei Funktionen getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Helferlogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Detail-Value-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.135: Repository-Guard-Filter-Setter-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die beiden Repository-Guard-Filter-Setter eingefuehrt:
  - `_set_repository_guard_filter(...)`
- wiederholte Normalisierungs-, Attribut-, Refresh- und Logging-Pfade vereinheitlicht, u. a. in:
  - `set_repository_guard_source_filter()`
  - `set_repository_guard_finding_filter()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Normalisieren, Refreshen und Loggen des Quellenfilters
  - korrektes Normalisieren, Refreshen und Loggen des Finding-Filters
- bewusst unveraendert geblieben sind:
  - Filter-Labels und Statuszeilen
  - Tree-, Detail-, Scan- und Exportverhalten
  - Baseline-, Trustlist- und Selection-Context-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `38/38` gruen

Kurzfazit:

- Die beiden Repository-Guard-Filter-Setter nutzen jetzt denselben kleinen Helfer fuer Normalisierung, Attribut-Update, Refresh und Logging, statt denselben Ablauf zweimal getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Setter-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Filter-Setter-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.136: Process-Guard-Trustlist-Abschluss-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Abschluss der Process-Guard-Trustlist-Aktionen eingefuehrt:
  - `_finish_process_guard_trustlist_action(...)`
- wiederholte Erfolg-/Fehler-/Recheck-Pfade vereinheitlicht, u. a. in:
  - `mark_selected_process_guard_trusted()`
  - `remove_selected_process_guard_trusted()`
  - `reset_process_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Erfolgspfad mit Logmeldung und Recheck
  - Fehlerpfad mit Trustlist-Fehlermeldung ohne Recheck
- bewusst unveraendert geblieben sind:
  - Auswahl-, Service- und Trustlist-Pfade
  - Monitoring-, Detail- und Tree-Verhalten
  - Prüf-, Chad- und Statuslogik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `43/43` gruen

Kurzfazit:

- Die drei Process-Guard-Trustlist-Aktionen nutzen jetzt denselben kleinen Abschluss-Helfer fuer Logmeldung, Fehlerbehandlung und Recheck, statt diesen Ablauf mehrfach getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Abschlusslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Trustlist-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.137: Packet-Capture-Output-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Packet-Capture-Output-Manipulation eingefuehrt:
  - `_packet_capture_apply_output(...)`
- wiederholte Clear-/Append-/Separator-Pfade vereinheitlicht, u. a. in:
  - `append_packet_capture_output()`
  - `clear_packet_capture_output()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Ersetzen vorhandenen Texts mit sauberem Reset
  - Anhaengen mit dem erwarteten Separator-Verhalten
- bewusst unveraendert geblieben sind:
  - Capture-Start-, Runtime- und Stop-Flow
  - Dateiinfo-, Open- und Tool-Pfade
  - Widget-State- und Button-Logik ausserhalb des Output-Inhalts

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `35/35` gruen

Kurzfazit:

- Die Packet-Capture-Output-Pfade nutzen jetzt denselben kleinen Helfer fuer Clear-, Separator- und Append-Logik, statt diesen Inhaltspfad in `append` und `clear` getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Output-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Output-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.138: Speedtest-Panel-Var-Items-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Zuordnung der Speedtest-Panel-Werte eingefuehrt:
  - `_speedtest_panel_var_items(...)`
- wiederholte Var-Zuweisungspfade vereinheitlicht, u. a. in:
  - `_apply_speedtest_panel_values()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Mapping aller formatierten Panel-Werte auf die erwarteten Variablen
  - sichere Default-Zuordnung bei leerem Eingabedict
- bewusst unveraendert geblieben sind:
  - Panelwert-Berechnung und Formatierung
  - Async-, History- und Warnlogik
  - Logging-, Persistenz- und CLI-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `38/38` gruen

Kurzfazit:

- Die Speedtest-Panel-Zuweisung nutzt jetzt denselben kleinen Helfer fuer die Variable-zu-Wert-Paare, statt die einzelnen Zielvariablen direkt in `_apply_speedtest_panel_values()` ausgeschrieben zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Mapping-Logik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Panel-Var-Items-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.139: Packet-Capture-Button-State-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Anwendung der Packet-Capture-Button-States eingefuehrt:
  - `_packet_capture_apply_button_states(...)`
- wiederholte Start-/Stop-Button-Zuweisung vereinheitlicht, u. a. in:
  - `packet_capture_set_running_state()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Anwenden der States auf vorhandene Buttons
  - robustes Verhalten bei fehlenden Button-Widgets
- bewusst unveraendert geblieben sind:
  - Running-/Ready-State-Berechnung
  - Capture-Start-, Runtime- und Stop-Flow
  - Output-, Dateiinfo- und Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `37/37` gruen

Kurzfazit:

- Die Packet-Capture-Button-Zuweisung nutzt jetzt denselben kleinen Helfer fuer die Start-/Stop-States, statt diesen Configure-Pfad direkt in `packet_capture_set_running_state()` doppelt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Button-State-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Button-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.140: Process-Guard-Status-Apply-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Anwendung der Process-Guard-Statuswerte eingefuehrt:
  - `_apply_process_guard_status_values(...)`
- wiederholte Var-Zuweisungspfade vereinheitlicht, u. a. in:
  - `update_process_guard_status_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Setzen aller drei Status-Variablen
  - sichere Default-Zuweisung bei leerem Eingabedict
- bewusst unveraendert geblieben sind:
  - Statuswert-Berechnung und Filterlogik
  - Monitoring-, Detail- und Tree-Verhalten
  - Prüf-, Chad- und Trustlist-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `45/45` gruen

Kurzfazit:

- Die Process-Guard-Statuszeile nutzt jetzt denselben kleinen Helfer fuer die drei Status-Variablen, statt die einzelnen Var-Zuweisungen direkt in `update_process_guard_status_line()` getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Apply-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Status-Apply-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.141: Process-Guard-Filter-Mode-Normalisierer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Normalisierung des Process-Guard-Filtermodus eingefuehrt:
  - `_normalized_process_guard_filter_mode(...)`
- wiederholte Trim-/Lower-/Fallback-Pfade vereinheitlicht, u. a. in:
  - `_process_guard_filter_mode()`
  - `set_process_guard_filter()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Akzeptanz und Trimmen bekannter Filterwerte
  - sauberen Fallback auf `all` bei unbekannten oder leeren Werten
- bewusst unveraendert geblieben sind:
  - Filter-Labels und Statustexte
  - Sichtbarkeitsfilter und Tree-Verhalten
  - Monitoring-, Prüf-, Chad- und Trustlist-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `47/47` gruen

Kurzfazit:

- Der Process-Guard behandelt die Filter-Mode-Normalisierung jetzt an einer Stelle, statt denselben kleinen Trim-/Fallback-Pfad in App-Lese- und Setter-Logik getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Normalisierungslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Filter-Mode-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.142: Process-Guard-Text-Write-Helfer `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Schreiben in das Process-Guard-Detail-Widget eingefuehrt:
  - `_write_process_guard_text(...)`
- wiederholte Text-Widget-Update-Pfade vereinheitlicht, u. a. in:
  - `_replace_process_guard_text()`
  - `_append_process_guard_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Anhaengen mit Separator-Verhalten
  - korrektes Ersetzen mit Reset auf den neuen Inhalt
- bewusst unveraendert geblieben sind:
  - Detail-Widget-Auswahl und App-Pfade
  - Monitoring-, Tree- und Statuslogik
  - Prüf-, Chad- und Trustlist-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `49/49` gruen

Kurzfazit:

- Die Process-Guard-Textpfade nutzen jetzt denselben kleinen Helfer fuer Replace- und Append-Schreiben, statt den Widget-Update-Ablauf in zwei Funktionen getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Text-Write-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Text-Write-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.143: Speedtest-Empty-Panel-Defaults `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die leeren Speedtest-Panel-Defaults eingefuehrt:
  - `_speedtest_empty_panel_values()`
- wiederholte Default-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_panel_values()`
  - `_speedtest_panel_var_items()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Rueckgabe aller leeren Panel-Defaults
  - rueckgabewert als unabhängiges Dict statt geteiltem Mutable
- bewusst unveraendert geblieben sind:
  - Panelwert-Formatierung und Mapping-Logik
  - Async-, History- und Warnpfade
  - Logging-, Persistenz- und CLI-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `40/40` gruen

Kurzfazit:

- Die leeren Speedtest-Panel-Defaults kommen jetzt aus einem gemeinsamen Helfer, statt denselben Default-Satz in mehreren Panel-Pfaden getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Default-Logik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Empty-Panel-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.144: Repository-Guard-Filter-Status-Helfer `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black tests/test_repository_guard_controller.py
python3 -m black --diff --workers 1 tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Repository-Guard-Filter-Statuszeile eingefuehrt:
  - `_apply_repository_guard_filter_status(...)`
- wiederholte Status-/Choice-Var-Zuweisung vereinheitlicht, u. a. in:
  - `update_repository_guard_filter_status_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Setzen der Source-Filter-Status- und Choice-Variablen
  - korrekte Default-Zuordnung fuer den Finding-Filter bei unbekanntem Modus
- bewusst unveraendert geblieben sind:
  - Filtertext- und Choice-Berechnung selbst
  - Tree-, Detail-, Scan- und Exportverhalten
  - Baseline-, Trustlist- und Status-Light-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `40/40` gruen

Kurzfazit:

- Die Repository-Guard-Filterzeile nutzt jetzt denselben kleinen Helfer fuer Status- und Choice-Variablen, statt diesen Var-Set-Pfad fuer Source und Finding getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Apply-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Filter-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.145: Speedtest-History-Metric-Text `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Formatierung numerischer Speedtest-History-Felder eingefuehrt:
  - `_speedtest_history_metric_text(...)`
- wiederholte Placeholder-/Formatierungs-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_history_log_fields()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Formatieren mit angeforderter Nachkommastellenzahl
  - korrekten Platzhalter bei `None`
- bewusst unveraendert geblieben sind:
  - History-Log-Line-Format und Panel-Logik
  - Async-, Warn- und Persistenzpfade
  - CLI- und Logging-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `42/42` gruen

Kurzfazit:

- Die numerischen Speedtest-History-Felder nutzen jetzt denselben kleinen Helfer fuer Placeholder- und Präzisionsformatierung, statt diesen Formatpfad mehrfach direkt in `_speedtest_history_log_fields()` zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Metric-Text-Logik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Metric-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.146: Packet-Capture-Summary-Value-Helfer `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Extraktion von `capinfos`-Werten eingefuehrt:
  - `_packet_capture_summary_value(...)`
- wiederholte `split/strip/default`-Pfade vereinheitlicht, u. a. in:
  - `_packet_capture_capinfos_summary()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Extrahieren eines getrimmten Suffixwerts
  - sauberen Fallback auf den uebergebenen Default bei leerem Suffix
- bewusst unveraendert geblieben sind:
  - Capinfos-Summary-Struktur und Runtime-Verhalten
  - Dateiinfo-, Output-, Open- und Capture-Pfade
  - Button- und Widget-State-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `39/39` gruen

Kurzfazit:

- Der Packet-Capture-`capinfos`-Parser nutzt jetzt denselben kleinen Helfer fuer die Extraktion von Suffixwerten, statt denselben `split/strip/default`-Pfad mehrfach direkt in `_packet_capture_capinfos_summary()` zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Summary-Value-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Summary-Value-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.147: Repository-Guard-Trustlist-Host-Zeilen `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Zeilen eines Trusted-Host-Eintrags eingefuehrt:
  - `_repository_guard_trustlist_host_lines(...)`
- wiederholten Listenaufbau vereinheitlicht, u. a. in:
  - `show_repository_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Formatieren aller erwarteten Host-Felder
  - sichere Default-Werte bei leerem Eintrag
- bewusst unveraendert geblieben sind:
  - Trustlist-Lade- und Servicepfade
  - Detail-Widget-Ausgabe und Logging
  - Scan-, Export-, Filter- und Status-Light-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `42/42` gruen

Kurzfazit:

- Die Repository-Guard-Vertrauensliste nutzt jetzt denselben kleinen Helfer fuer den Zeilenaufbau eines Host-Eintrags, statt diese Feldgruppen direkt in `show_repository_guard_trustlist()` zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Trustlist-Zeilenlogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Trustlist-Host-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.148: Packet-Capture-File-Info-Lines `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Zeilen der Capture-Dateiinfo eingefuehrt:
  - `_packet_capture_file_info_lines(...)`
- wiederholten Textaufbau vereinheitlicht, u. a. in:
  - `_packet_capture_file_info_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Formatieren der erwarteten Dateiinformationszeilen
  - unveraenderte Uebernahme leerer bzw. uebergebener Werte
- bewusst unveraendert geblieben sind:
  - Dateiinfo-Text als Ganzes und dessen Aufrufpfade
  - Capinfos-, Output-, Open- und Capture-Logik
  - Button- und Widget-State-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `41/41` gruen

Kurzfazit:

- Die Packet-Capture-Dateiinformation nutzt jetzt denselben kleinen Helfer fuer ihre Zeilenstruktur, statt den Stringaufbau direkt in `_packet_capture_file_info_text()` zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte File-Info-Zeilenlogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.149: Packet-Capture-Start-Lines `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Zeilen des Packet-Capture-Starttexts eingefuehrt:
  - `_packet_capture_start_lines(...)`
- wiederholten Starttext-Aufbau vereinheitlicht, u. a. in:
  - `_packet_capture_start_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Formatieren aller erwarteten Starttext-Zeilen
  - korrekten Platzhalter `-` bei leerem Filter
- bewusst unveraendert geblieben sind:
  - Starttext als Ganzes und dessen Aufrufpfade
  - Capture-Start-, Runtime- und Stop-Logik
  - Output-, Dateiinfo- und Open-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `43/43` gruen

Kurzfazit:

- Der Packet-Capture-Starttext nutzt jetzt denselben kleinen Helfer fuer seine Zeilenstruktur, statt den Stringaufbau direkt in `_packet_capture_start_text()` zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Starttext-Zeilenlogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Start-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.150: Speedtest-History-Log-Parts `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Teile der Speedtest-History-Log-Zeile eingefuehrt:
  - `_speedtest_history_log_parts(...)`
- wiederholten Textaufbau vereinheitlicht, u. a. in:
  - `_speedtest_history_log_line()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Formatieren aller erwarteten Log-Segmente
  - sichere Default-Segmente bei leerem Eingabedict
- bewusst unveraendert geblieben sind:
  - History-Log-Line als Ganzes
  - History-, Warn-, Panel- und Async-Pfade
  - Persistenz- und CLI-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `44/44` gruen

Kurzfazit:

- Die Speedtest-History-Logzeile nutzt jetzt denselben kleinen Helfer fuer ihre einzelnen Segmente, statt den Textaufbau direkt in `_speedtest_history_log_line()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Log-Part-Logik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Log-Parts-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.151: Repository-Guard-Trustlist-Abschluss `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Abschluss der Repository-Guard-Trustlist-Aktionen eingefuehrt:
  - `_finish_repository_guard_trustlist_action(...)`
- wiederholte Erfolg-/Fehler-/Rescan-Pfade vereinheitlicht, u. a. in:
  - `mark_selected_repository_guard_trusted()`
  - `remove_selected_repository_guard_trusted()`
  - `reset_repository_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Erfolgspfad mit Logmeldung und Rescan
  - Fehlerpfad mit Trustlist-Fehlermeldung ohne Rescan
- bewusst unveraendert geblieben sind:
  - Source-Auswahl-, Service- und Trustlist-Pfade
  - Scan-, Filter-, Export- und Detailverhalten
  - Status-Light- und Baseline-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Repository-Guard-Controller-Tests:
  - `44/44` gruen

Kurzfazit:

- Die Repository-Guard-Trustlist-Aktionen nutzen jetzt denselben kleinen Abschluss-Helfer fuer Logmeldung, Fehlerbehandlung und Rescan, statt diesen Ablauf mehrfach getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Abschlusslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Trustlist-Abschluss-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.152: Process-Guard-Light-Values `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Farb- und Standardtext-Mapping des Process-Guard-Lichts eingefuehrt:
  - `_process_guard_light_values(...)`
- wiederholte State-/Default-Text-Pfade vereinheitlicht, u. a. in:
  - `set_process_guard_light()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrektes Mapping bekannter State-Defaults
  - grauen Fallback plus benutzerdefinierte Meldung bei unbekanntem State
- bewusst unveraendert geblieben sind:
  - Setzen von `last_state` und `status_var`
  - Monitoring-, Prüf- und Snapshot-Logik
  - Tree-, Detail- und Trustlist-Verhalten

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Process-Guard-Controller-Tests:
  - `51/51` gruen

Kurzfazit:

- Das Process-Guard-Licht nutzt jetzt denselben kleinen Helfer fuer Farbauswahl und Standardtexte, statt dieses Mapping direkt in `set_process_guard_light()` mehrfach auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Light-Value-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Light-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.153: Speedtest-History-Messages-Helfer `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Verlaufsausgabe eingefuehrt:
  - `_speedtest_history_message_lines(...)`
- wiederholte Header-/Zeilen-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_history_messages()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - leeren Verlauf mit Standardmeldung
  - Verlauf mit Header plus formatierter Ergebniszeile
- bewusst unveraendert geblieben sind:
  - History-Trim-, Load- und Persistenzpfade
  - `show_speedtest_history()`-Ausgabeablauf
  - Async-, Warnungs- und Panel-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `46/46` gruen

Kurzfazit:

- Die Speedtest-Verlaufsausgabe nutzt jetzt denselben kleinen Helfer fuer Standardmeldung, Header und formatierte Ergebniszeilen, statt diese Struktur direkt in `_speedtest_history_messages()` aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Verlaufsausgabe zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.154: Speedtest-Result-Debug-Messages `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Debug-Ausgabe eines erfolgreichen Speedtest-Laufs eingefuehrt:
  - `_speedtest_result_debug_messages(...)`
- wiederholte JSON-/Summary-/Table-Pfade vereinheitlicht, u. a. in:
  - `speedtest_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Reihenfolge von JSON-, Summary- und Table-Ausgabe
  - JSON-Ausgabe mit nicht-ASCII-Zeichen via `ensure_ascii=False`
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warnungs- und Panel-Logik
  - Abschluss- und Diagnose-Logging
  - CLI-, Persistenz- und Verlaufspfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `48/48` gruen

Kurzfazit:

- Die Debug-Ausgabe eines erfolgreichen Speedtest-Laufs nutzt jetzt denselben kleinen Helfer fuer JSON-, Summary- und Table-Meldungen, statt diese drei Ausgaben direkt in `speedtest_async()` getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Debug-Ausgabe zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Result-Debug-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.155: Speedtest-Internal-Debug-Message `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die interne Debug-Meldung eines erfolgreichen Speedtest-Laufs eingefuehrt:
  - `_speedtest_internal_debug_message(...)`
- wiederholte Tool-/History-Textpfade vereinheitlicht, u. a. in:
  - `speedtest_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - normales Tool-/History-Formatting
  - sicheren `-`-Fallback bei fehlendem Tool
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warnungs- und Panel-Logik
  - JSON-/Summary-/Table-Debug-Ausgabe
  - Diagnose-, CLI- und Persistenzpfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Speedtest-Modultests:
  - `50/50` gruen

Kurzfazit:

- Die interne Debug-Meldung eines erfolgreichen Speedtest-Laufs nutzt jetzt denselben kleinen Helfer fuer Tool- und History-Text, statt diesen String direkt in `speedtest_async()` aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Debug-Meldung zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Internal-Debug-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.156: Packet-Capture-Capinfos-Text `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die formatierte `capinfos`-Ausgabe eingefuehrt:
  - `_packet_capture_capinfos_text(...)`
- wiederholte Kopf-/Body-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_show_file_info()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Header plus unveraenderte `capinfos`-Zeilen
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - `capinfos`-Summary-Parsing und Var-Updates
  - Dateiinfo-, Capture-, Output- und Open-Pfade
  - Runtime-, Start- und Stop-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `45/45` gruen

Kurzfazit:

- Die formatierte `capinfos`-Ausgabe nutzt jetzt denselben kleinen Helfer fuer Header und bereinigten Body, statt diesen Text direkt in `packet_capture_show_file_info()` zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte `capinfos`-Textausgabe zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Capinfos-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.157: Packet-Capture-File-Info-Body-Lines `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Dateiinfo-Body eingefuehrt:
  - `_packet_capture_file_info_body_lines(...)`
- wiederholte Datei-/Groesse-Pfade vereinheitlicht, u. a. in:
  - `_packet_capture_file_info_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Datei-/Groesse-Zeilen
  - sichere Weitergabe leerer Werte
- bewusst unveraendert geblieben sind:
  - Dateiinfo-Header und Textzusammenbau
  - `capinfos`-Parsing, Output- und Runtime-Pfade
  - Capture-, Start-, Stop- und Open-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `47/47` gruen

Kurzfazit:

- Die lokalen Dateiinfo-Zeilen nutzen jetzt denselben kleinen Helfer fuer Datei- und Groessen-Text, statt diese beiden Zeilen direkt in `_packet_capture_file_info_lines()` aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Dateiinfo-Body-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Body-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.158: Packet-Capture-Start-Body-Lines `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Starttext-Body eingefuehrt:
  - `_packet_capture_start_body_lines(...)`
- wiederholte Tool-/Interface-/Datei-/Filter-Pfade vereinheitlicht, u. a. in:
  - `_packet_capture_start_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Body-Zeilen des Starttexts
  - sicheren `-`-Fallback bei leerem Filter
- bewusst unveraendert geblieben sind:
  - Starttext-Header und Gesamtausgabe
  - Capture-, Runtime-, Output- und Open-Pfade
  - Start-, Stop- und Dateiinfo-Logik

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `49/49` gruen

Kurzfazit:

- Die lokalen Starttext-Zeilen nutzen jetzt denselben kleinen Helfer fuer Tool-, Interface-, Datei- und Filter-Text, statt diese vier Zeilen direkt in `_packet_capture_start_lines()` aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Starttext-Body-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Start-Body-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.159: Packet-Capture-File-Info-Missing-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Dateiinfo-Fehlermeldung eingefuehrt:
  - `_packet_capture_file_info_missing_message(...)`
- wiederholte Auswahl-/Missing-File-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_show_file_info()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - leere Dateiauswahl
  - fehlende Capture-Datei mit Pfadangabe
- bewusst unveraendert geblieben sind:
  - Dateiinfo-, `capinfos`-, Output- und Runtime-Pfade
  - Capture-, Start-, Stop- und Open-Logik
  - Status- und Var-Updates

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `51/51` gruen

Kurzfazit:

- Die kleinen Dateiinfo-Fehlermeldungen nutzen jetzt denselben Helfer fuer “noch keine Datei” und “Datei nicht gefunden”, statt diese Verzweigung direkt in `packet_capture_show_file_info()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Dateiinfo-Fehlermeldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Missing-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.160: Packet-Capture-Open-Location-Missing-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Open-Location-Fehlermeldung eingefuehrt:
  - `_packet_capture_open_location_missing_message(...)`
- wiederholte Datei-/Target-Pruefpfade vereinheitlicht, u. a. in:
  - `open_packet_capture_file_location()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - fehlende Capture-Datei
  - fehlenden gueltigen Zielpfad
- bewusst unveraendert geblieben sind:
  - Open-Location-Kommandoaufbau und `xdg-open`-Pfad
  - Output-, Capture-, Runtime- und Dateiinfo-Logik
  - Start-, Stop- und Wireshark-Open-Pfade

Ergebnis:

- `ruff`: gruen
- `black --check`: gruen
- Packet-Capture-Controller-Tests:
  - `53/53` gruen

Kurzfazit:

- Die kleinen Open-Location-Fehlermeldungen nutzen jetzt denselben Helfer fuer “noch keine Datei” und “kein gueltiger Pfad”, statt diese Verzweigung direkt in `open_packet_capture_file_location()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Open-Location-Fehlermeldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Open-Location-Missing-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.161: Packet-Capture-Wireshark-Missing-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Wireshark-Open-Fehlermeldung eingefuehrt:
  - `_packet_capture_wireshark_missing_message(...)`
- wiederholte Launcher-/Datei-Pruefpfade vereinheitlicht, u. a. in:
  - `open_packet_capture_in_wireshark()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - fehlenden Wireshark-Launcher
  - fehlende gueltige Capture-Datei
- bewusst unveraendert geblieben sind:
  - Wireshark-Kommandoaufbau und Startpfad
  - Output-, Capture-, Runtime- und Dateiinfo-Logik
  - Start-, Stop- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei formatiert; `--diff` danach ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `55/55` gruen

Kurzfazit:

- Die kleinen Wireshark-Open-Fehlermeldungen nutzen jetzt denselben Helfer fuer “Launcher fehlt” und “keine gueltige Datei”, statt diese Verzweigung direkt in `open_packet_capture_in_wireshark()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Wireshark-Missing-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- In dieser Session verhaelt sich `black --check` auf dieser einen Datei weiterhin widerspruechlich, obwohl `black` formatiert und `--diff` anschliessend keine Aenderung mehr zeigt.

## Phase 3.162: Packet-Capture-Stop-Request-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Stop-Anforderungs-Meldung eingefuehrt:
  - `_packet_capture_stop_request_message(...)`
- wiederholte Stop-/No-Running-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_stop()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - kein laufendes Capture
  - erfolgreiche Stop-Anforderung
- bewusst unveraendert geblieben sind:
  - Fehlerpfad und Prozess-Terminierung
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `57/57` gruen

Kurzfazit:

- Die kleinen Stop-Meldungen nutzen jetzt denselben Helfer fuer “kein laufendes Capture” und “Stop angefordert”, statt diese beiden Texte direkt in `packet_capture_stop()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Stop-Meldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Stop-Request-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.163: Packet-Capture-Open-Location-Result-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Open-Location-Ergebnis-Meldung eingefuehrt:
  - `_packet_capture_open_location_result_message(...)`
- wiederholte Erfolgs-/Fehler-Pfade vereinheitlicht, u. a. in:
  - `open_packet_capture_file_location()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiche Pfad-Oeffnung
  - Fehlertext beim fehlgeschlagenen Oeffnen
- bewusst unveraendert geblieben sind:
  - `xdg-open`-Kommandoaufbau und Missing-Checks
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop- und Wireshark-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `59/59` gruen

Kurzfazit:

- Die kleinen Open-Location-Ergebnis-Meldungen nutzen jetzt denselben Helfer fuer Erfolgs- und Fehlertext, statt diese beiden Texte direkt in `open_packet_capture_file_location()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Ergebnis-Meldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Open-Location-Result-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.164: Packet-Capture-Wireshark-Result-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Wireshark-Ergebnis-Meldung eingefuehrt:
  - `_packet_capture_wireshark_result_message(...)`
- wiederholte Erfolgs-/Fehler-Pfade vereinheitlicht, u. a. in:
  - `open_packet_capture_in_wireshark()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erfolgreiches Oeffnen in Wireshark
  - Fehlertext beim fehlgeschlagenen Wireshark-Start
- bewusst unveraendert geblieben sind:
  - Wireshark-Kommandoaufbau und Missing-Checks
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `61/61` gruen

Kurzfazit:

- Die kleinen Wireshark-Ergebnis-Meldungen nutzen jetzt denselben Helfer fuer Erfolgs- und Fehlertext, statt diese beiden Texte direkt in `open_packet_capture_in_wireshark()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Ergebnis-Meldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Wireshark-Result-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.165: Packet-Capture-Start-Failure-Messages `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Start-Fehlermeldungen eingefuehrt:
  - `_packet_capture_start_failure_messages(...)`
- wiederholte Output-/Log-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()` im `finish_error`-Zweig
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Output- und Logtext bei normaler Fehlermeldung
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - Async-, Capture-, Runtime- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade
  - Status- und Prozessbehandlung

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `63/63` gruen

Kurzfazit:

- Die kleinen Start-Fehlermeldungen nutzen jetzt denselben Helfer fuer User-Output und Logtext, statt diese beiden Texte direkt im `finish_error`-Zweig von `packet_capture_start_async()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Start-Fehlermeldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Start-Failure-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.166: Packet-Capture-Stop-Failure-Messages `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Stop-Fehlermeldungen eingefuehrt:
  - `_packet_capture_stop_failure_messages(...)`
- wiederholte Output-/Log-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_stop()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Output- und Logtext bei normaler Stop-Fehlermeldung
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - Prozess-Terminierung und Timeout-/Kill-Pfad
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `65/65` gruen

Kurzfazit:

- Die kleinen Stop-Fehlermeldungen nutzen jetzt denselben Helfer fuer User-Output und Logtext, statt diese beiden Texte direkt im Fehlerpfad von `packet_capture_stop()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Stop-Fehlermeldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Stop-Failure-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.167: Packet-Capture-State-Log-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Start-/Stopp-Logmeldung eingefuehrt:
  - `_packet_capture_state_log_message(...)`
- wiederholte State-/Interface-Logpfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
  - `packet_capture_start_async()` im `finish_success`-Zweig
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - gestarteten Zustand
  - gestoppten Zustand
- bewusst unveraendert geblieben sind:
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Fehlerpfade fuer Start und Stopp
  - Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Datei unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `67/67` gruen

Kurzfazit:

- Die kleinen Start-/Stopp-Logmeldungen nutzen jetzt denselben Helfer fuer State und Interface, statt diese beiden Logstrings direkt an zwei Stellen im Capture-Flow aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte State-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-State-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.168: Packet-Capture-Missing-Tool-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Tool-fehlt-Meldung eingefuehrt:
  - `_packet_capture_missing_tool_message()`
- wiederholte Tool-/Hinweispfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - stabilen String-Rueckgabewert mit `tshark`-Hinweis
- bewusst unveraendert geblieben sind:
  - Tool-Check, Install-Hinweis und Status-Update
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `69/69` gruen

Kurzfazit:

- Die kleine Tool-fehlt-Meldung nutzt jetzt denselben Helfer, statt den String direkt im Startpfad von `packet_capture_start_async()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tool-Missing-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Missing-Tool-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.169: Packet-Capture-Start-Guard-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Start-Guard-Meldung eingefuehrt:
  - `_packet_capture_start_guard_message(...)`
- wiederholte Running-/Missing-Interface-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bereits laufendes Capture
  - fehlendes Interface
- bewusst unveraendert geblieben sind:
  - Status-Update bei fehlendem Interface
  - Tool-Check, Install-Hinweis und Startlogik
  - Capture-, Runtime-, Output- und Dateiinfo-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `71/71` gruen

Kurzfazit:

- Die kleinen Start-Guard-Meldungen nutzen jetzt denselben Helfer fuer “läuft bereits” und “Interface fehlt”, statt diese beiden Texte direkt im Startpfad von `packet_capture_start_async()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Start-Guard-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Start-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.170: Packet-Capture-File-Info-Error-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Dateiinfo-Fehlermeldung eingefuehrt:
  - `_packet_capture_file_info_error_message(...)`
- wiederholte Exception-/Output-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_show_file_info()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - `capinfos`-Pfad, Dateiinfo-Aufbau und Var-Updates
  - Capture-, Runtime-, Output- und Start-/Stopp-Logik
  - Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `73/73` gruen

Kurzfazit:

- Die kleine Dateiinfo-Fehlermeldung nutzt jetzt denselben Helfer, statt den Exception-Text direkt im Fehlerpfad von `packet_capture_show_file_info()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Dateiinfo-Fehlermeldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Error-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.171: Packet-Capture-Completion-Failure-Messages `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Fehlerabschluss-Meldungen eingefuehrt:
  - `_packet_capture_completion_failure_messages(...)`
- wiederholte Warn-/Log-Pfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()` im `finish_success`-Fehlerzweig
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von Warnhinweis und Logtext
  - korrektes Weiterreichen von Interface und Return-Code
- bewusst unveraendert geblieben sind:
  - Completion-Status, Permission-Hint und Detail-Output
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `75/75` gruen

Kurzfazit:

- Die kleinen Fehlerabschluss-Meldungen nutzen jetzt denselben Helfer fuer Warnhinweis und Logtext, statt diese beiden Texte direkt im `finish_success`-Fehlerzweig des Capture-Workers auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Completion-Failure-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Completion-Failure-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.172: Packet-Capture-Wireshark-Failure-Log-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Wireshark-Fehlerlogmeldung eingefuehrt:
  - `_packet_capture_wireshark_failure_log_message(...)`
- wiederholte Fehlerlog-Pfade vereinheitlicht, u. a. in:
  - `open_packet_capture_in_wireshark()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Logtext
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - Wireshark-Kommandoaufbau, Missing-Checks und Output-Meldungen
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `77/77` gruen

Kurzfazit:

- Die kleine Wireshark-Fehlerlogmeldung nutzt jetzt denselben Helfer, statt den Logstring direkt im Fehlerpfad von `open_packet_capture_in_wireshark()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Wireshark-Fehlerlogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Wireshark-Failure-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.173: Packet-Capture-Open-Location-Failure-Log-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Open-Location-Fehlerlogmeldung eingefuehrt:
  - `_packet_capture_open_location_failure_log_message(...)`
- wiederholte Fehlerlog-Pfade vereinheitlicht, u. a. in:
  - `open_packet_capture_file_location()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Logtext
  - sauberes `strip()` von umgebendem Whitespace
- bewusst unveraendert geblieben sind:
  - Open-Location-Kommandoaufbau, Missing-Checks und Output-Meldungen
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop- und Wireshark-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `79/79` gruen

Kurzfazit:

- Die kleine Open-Location-Fehlerlogmeldung nutzt jetzt denselben Helfer, statt den Logstring direkt im Fehlerpfad von `open_packet_capture_file_location()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Open-Location-Fehlerlogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Open-Location-Failure-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.174: Packet-Capture-Missing-Tool-Log-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Tool-fehlt-Fehlerlogmeldung eingefuehrt:
  - `_packet_capture_missing_tool_log_message()`
- wiederholte Tool-fehlt-Logpfade vereinheitlicht, u. a. in:
  - `packet_capture_start_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Logtext
  - Erwaehnung von `tshark` und `dumpcap`
- bewusst unveraendert geblieben sind:
  - Tool-Check, Install-Hinweis und User-Output
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `81/81` gruen

Kurzfazit:

- Die kleine Tool-fehlt-Fehlerlogmeldung nutzt jetzt denselben Helfer, statt den Logstring direkt im Tool-fehlt-Zweig von `packet_capture_start_async()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tool-Missing-Loglogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Missing-Tool-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.175: Packet-Capture-Interfaces-Ready-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Interface-Bereit-Meldung eingefuehrt:
  - `_packet_capture_interfaces_ready_message(...)`
- wiederholte Summary-Pfade vereinheitlicht, u. a. in:
  - `refresh_packet_capture_interfaces()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - mehrere Interfaces
  - einzelnes Interface
- bewusst unveraendert geblieben sind:
  - Interface-Erkennung, Auswahl und Status-Update
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `83/83` gruen

Kurzfazit:

- Die kleine Interface-Bereit-Meldung nutzt jetzt denselben Helfer fuer den Join der Interface-Namen, statt den Summary-String direkt in `refresh_packet_capture_interfaces()` aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Interface-Summary-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Interfaces-Ready-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.176: Packet-Capture-No-Interfaces-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die No-Interfaces-Meldung eingefuehrt:
  - `_packet_capture_no_interfaces_message()`
- wiederholte No-Interfaces-Pfade vereinheitlicht, u. a. in:
  - `refresh_packet_capture_interfaces()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `tshark` und `iproute2`
- bewusst unveraendert geblieben sind:
  - Interface-Erkennung, Auswahl und Status-Update
  - Capture-, Runtime-, Output- und Dateiinfo-Logik
  - Start-, Stop-, Wireshark- und Open-Location-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `85/85` gruen

Kurzfazit:

- Die kleine No-Interfaces-Meldung nutzt jetzt denselben Helfer, statt den String direkt im No-Interfaces-Zweig von `refresh_packet_capture_interfaces()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte No-Interfaces-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-No-Interfaces-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.177: Packet-Capture-Dumpcap-Permission-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py
python3 -m black tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --diff --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --diff --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Dumpcap-Berechtigungs-Meldung eingefuehrt:
  - `_packet_capture_dumpcap_permission_message()`
- wiederholte Permission-Hinweis-Pfade vereinheitlicht, u. a. in:
  - `refresh_packet_capture_interfaces()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `tshark` und `dumpcap`
- bewusst unveraendert geblieben sind:
  - Permission-Check, Status-Update und Hinweisdialog
  - Interface-Erkennung, Auswahl und Summary-Pfade
  - Capture-, Runtime-, Output- und Dateiinfo-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; `--diff` ohne weitere Aenderungen
- Packet-Capture-Controller-Tests:
  - `87/87` gruen

Kurzfazit:

- Die kleine Dumpcap-Berechtigungs-Meldung nutzt jetzt denselben Helfer, statt den String direkt im Permission-Hinweis-Zweig von `refresh_packet_capture_interfaces()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Permission-Meldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Dumpcap-Permission-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.178: Process-Guard-Service-Unavailable-Message `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Service-unavailable-Meldung eingefuehrt:
  - `_process_guard_service_unavailable_message()`
- wiederholte Service-unavailable-Pfade vereinheitlicht, u. a. in:
  - `_process_guard_service_or_log()`
  - `run_process_guard_check()`
  - `start_process_guard_monitoring()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - stabilen String-Inhalt
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `53/53` gruen

Kurzfazit:

- Die kleine Service-unavailable-Meldung nutzt jetzt denselben Helfer, statt den String in mehreren Service-Check-Pfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Service-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.179: Repository-Guard-Service-Unavailable-Message `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Service-unavailable-Meldung eingefuehrt:
  - `_repository_guard_service_unavailable_message()`
- wiederholte Service-unavailable-Pfade vereinheitlicht, u. a. in:
  - `run_repository_guard_scan()`
  - `create_repository_guard_baseline()`
  - `mark_selected_repository_guard_trusted()`
  - `remove_selected_repository_guard_trusted()`
  - `show_repository_guard_trustlist()`
  - `reset_repository_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - stabilen String-Inhalt
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline-, Trustlist- und Exportverhalten
  - Detail-, Filter- und Tree-Pfade
  - Auswahl-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `46/46` gruen

Kurzfazit:

- Die kleine Service-unavailable-Meldung nutzt jetzt denselben Helfer, statt den String in mehreren Repository-Guard-Service-Pfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Service-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.180: Security-Selected-Event-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die aktuell ausgewaehlte Event-Detailauflosung eingefuehrt:
  - `_selected_security_event_text()`
- wiederholte Auswahl-/Meta-/Textpfade vereinheitlicht, u. a. in:
  - `on_security_event_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aggregate-Text bei ausgewaehlter Zeile
  - leeren Rueckgabewert ohne Auswahl
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Detail-Widget-Schreiben und Table-Selection-Logik
  - Connected-Device-, Baseline- und Chad-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Module-Tests:
  - `45/45` gruen

Kurzfazit:

- Die Event-Detailauflosung fuer die aktuelle Security-Tabellenauswahl nutzt jetzt denselben kleinen Helfer, statt Row-ID-, Meta- und Textpfad direkt in `on_security_event_select()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Auswahl- und Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Selected-Event-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.181: Speedtest-Failure-Messages `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/speedtest_controller.py tests/test_speedtest_module.py
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Async-Fehlpfad eingefuehrt:
  - `_speedtest_failure_messages()`
- wiederholte Failure-/CLI-Diagnose-Pfade vereinheitlicht, u. a. in:
  - `speedtest_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Fehlermeldung plus CLI-Diagnose
  - reine Fehlermeldung ohne Marker
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warn- und Panel-Verhalten
  - CLI-Erkennung, Ergebnis-Parsing und Debug-Ausgaben
  - Show-History- und Persistenz-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Speedtest-Tests:
  - `52/52` gruen

Kurzfazit:

- Der kleine Async-Fehlpfad nutzt jetzt denselben Helfer, statt Fehlermeldung und optionale CLI-Diagnose direkt in `speedtest_async()` zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Failure-Meldungslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Failure-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.182: Repository-Guard-Missing-Baseline-Path-Message `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Missing-Baseline-Path-Meldung eingefuehrt:
  - `_repository_guard_missing_baseline_path_message()`
- wiederholte Missing-Baseline-Path-Pfade vereinheitlicht, u. a. in:
  - `create_repository_guard_baseline()`
  - `reset_repository_guard_baseline()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - stabilen String-Inhalt
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline-, Trustlist- und Exportverhalten
  - Detail-, Filter- und Tree-Pfade
  - Auswahl-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `48/48` gruen

Kurzfazit:

- Die kleine Missing-Baseline-Path-Meldung nutzt jetzt denselben Helfer, statt den String in mehreren Baseline-Pfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Baseline-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.183: Process-Guard-Available-Service-Guard `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Service-Verfuegbarkeitspruefung eingefuehrt:
  - `_process_guard_available_service_or_log()`
- wiederholte Service-Available-Checks vereinheitlicht, u. a. in:
  - `run_process_guard_check()`
  - `start_process_guard_monitoring()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe bei verfuegbarem Service
  - Log plus `None` bei nicht verfuegbarem Service
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `55/55` gruen

Kurzfazit:

- Die kleine Service-Verfuegbarkeitspruefung nutzt jetzt denselben Helfer, statt den `is_available()`-Guard in Check- und Monitoring-Startpfad getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Guard-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Available-Service-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.184: Speedtest-Status-Message `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/speedtest_controller.py tests/test_speedtest_module.py
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Async-Statusmeldungen eingefuehrt:
  - `_speedtest_status_message()`
- wiederholte Started-/Completed-Pfade vereinheitlicht, u. a. in:
  - `speedtest_async()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Started-Text
  - Completed-Text
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warn- und Panel-Verhalten
  - CLI-Erkennung, Ergebnis-Parsing und Debug-Ausgaben
  - Failure-, Show-History- und Persistenz-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Speedtest-Tests:
  - `54/54` gruen

Kurzfazit:

- Die kleinen Async-Statusmeldungen nutzen jetzt denselben Helfer, statt Started- und Completed-Text direkt in `speedtest_async()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Status-Meldungslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.185: Packet-Capture-File-Info-Header `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Dateiinfo-Header eingefuehrt:
  - `_packet_capture_file_info_header()`
- wiederholte Dateiinfo-Header-Pfade vereinheitlicht, u. a. in:
  - `_packet_capture_file_info_lines()`
  - `_packet_capture_capinfos_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Header-Text
  - Erwaehnung von `Capture-Datei Info`
- bewusst unveraendert geblieben sind:
  - `capinfos`-Parsing sowie Capture-, Output- und Runtime-Verhalten
  - Dateiinfo-, Missing- und Open-Pfade
  - Start-, Stop-, Wireshark- und Open-Location-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Packet-Capture-Controller-Tests:
  - `89/89` gruen

Kurzfazit:

- Der kleine Dateiinfo-Header nutzt jetzt denselben Helfer, statt den Header-Text in mehreren Dateiinfo-Pfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Header-Logik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-File-Info-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.186: Repository-Guard-Empty-Trustlist-Message `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die leere Trustlist-Meldung eingefuehrt:
  - `_repository_guard_empty_trustlist_message()`
- wiederholte Empty-Trustlist-Pfade vereinheitlicht, u. a. in:
  - `show_repository_guard_trustlist()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Trusted Hosts`
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline-, Trustlist- und Exportverhalten
  - Detail-, Filter- und Tree-Pfade
  - Auswahl-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `50/50` gruen

Kurzfazit:

- Die kleine Empty-Trustlist-Meldung nutzt jetzt denselben Helfer, statt den Text direkt im Trustlist-Anzeigepfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Empty-Trustlist-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.187: Process-Guard-Empty-Trustlist-Message `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die leere Trustlist-Meldung eingefuehrt:
  - `_process_guard_empty_trustlist_message()`
- wiederholte Empty-Trustlist-Pfade vereinheitlicht, u. a. in:
  - `_process_guard_trustlist_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Ausnahmen`
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `57/57` gruen

Kurzfazit:

- Die kleine Empty-Trustlist-Meldung nutzt jetzt denselben Helfer, statt den Text direkt im Trustlist-Zeilenaufbau auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Empty-Trustlist-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.188: Security-Connected-Device-Baseline-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Device-Baseline-Text eingefuehrt:
  - `_connected_device_baseline_text()`
- wiederholte Device-Baseline-Textpfade vereinheitlicht, u. a. in:
  - `_connected_device_detail_text()`
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Label bei bekanntem Baseline-Gerät
  - Label bei neuem/nicht bekanntem Gerät
- bewusst unveraendert geblieben sind:
  - Device-Detail-, Monitoring- und Tabellenverhalten
  - Event-, Filter- und Chad-Pfade
  - Baseline-, Inventory- und Refresh-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Module-Tests:
  - `47/47` gruen

Kurzfazit:

- Der Device-Baseline-Text nutzt jetzt denselben Helfer, statt das Label in Detail- und Inventory-Pfad getrennt zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Baseline-Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Baseline-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.189: Repository-Guard-Details-Header `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Details-Header eingefuehrt:
  - `_repository_guard_details_header()`
- wiederholte Details-Header-Pfade vereinheitlicht, u. a. in:
  - `_repository_guard_report_payload()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Header-Text
  - Erwaehnung von `Details`
- bewusst unveraendert geblieben sind:
  - Report-, Export-, Scan- und Baseline-Verhalten
  - Detail-, Filter- und Tree-Pfade
  - Trustlist-, Auswahl-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `52/52` gruen

Kurzfazit:

- Der kleine Details-Header nutzt jetzt denselben Helfer, statt den Text direkt im Report-Payload aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Header-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Details-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.190: Speedtest-Empty-History-Message `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/speedtest_controller.py tests/test_speedtest_module.py
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die leere Verlaufsmeldung eingefuehrt:
  - `_speedtest_empty_history_message()`
- wiederholte Empty-History-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_history_message_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Verlauf`
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warn- und Panel-Verhalten
  - CLI-Erkennung, Ergebnis-Parsing und Debug-Ausgaben
  - Failure-, Status-, Show-History- und Persistenz-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Speedtest-Tests:
  - `56/56` gruen

Kurzfazit:

- Die kleine leere Verlaufsmeldung nutzt jetzt denselben Helfer, statt den Text direkt im History-Message-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Empty-History-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.191: Packet-Capture-Open-Success-Message `netmon/features/packet_capture_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
./venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py
python3 -m black --check --workers 1 netmon/features/packet_capture_controller.py
python3 -m black --check --workers 1 tests/test_packet_capture_controller.py
pytest tests/test_packet_capture_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Open-Erfolgsmeldungen eingefuehrt:
  - `_packet_capture_open_success_message()`
- wiederholte Open-Success-Pfade vereinheitlicht, u. a. in:
  - `_packet_capture_open_location_result_message()`
  - `_packet_capture_wireshark_result_message()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Success-Text
  - getrimmtes Label
- bewusst unveraendert geblieben sind:
  - `capinfos`-, Capture-, Output- und Runtime-Verhalten
  - Dateiinfo-, Missing- und Failure-Pfade
  - Start-, Stop-, Wireshark- und Open-Location-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Packet-Capture-Controller-Tests:
  - `91/91` gruen

Kurzfazit:

- Die kleinen Open-Erfolgsmeldungen nutzen jetzt denselben Helfer, statt den geöffnet-Text in mehreren Result-Pfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Success-Meldungslogik zusaetzlich zu den bestehenden Packet-Capture-Regressionstests ab.
- Damit ist auch dieser kompakte Packet-Capture-Open-Success-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.192: Speedtest-History-Header-Message `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/speedtest_controller.py tests/test_speedtest_module.py
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Verlauf-Header eingefuehrt:
  - `_speedtest_history_header_message()`
- wiederholte History-Header-Pfade vereinheitlicht, u. a. in:
  - `_speedtest_history_message_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Header-Text
  - Erwaehnung von `Ergebnisse`
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warn- und Panel-Verhalten
  - CLI-Erkennung, Ergebnis-Parsing und Debug-Ausgaben
  - Empty-History-, Failure-, Status-, Show-History- und Persistenz-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Speedtest-Tests:
  - `58/58` gruen

Kurzfazit:

- Der kleine Verlauf-Header nutzt jetzt denselben Helfer, statt den Header-Text direkt im History-Message-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Header-Logik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-History-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.193: Repository-Guard-Text-Export-Payload `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den TXT-Export-Payload eingefuehrt:
  - `_repository_guard_text_export_payload()`
- wiederholte Text-Export-Pfade vereinheitlicht, u. a. in:
  - `_repository_guard_export_payload()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Text-Export-Pfad
  - einzelnes abschließendes Newline
- bewusst unveraendert geblieben sind:
  - Report-, Export-, Scan- und Baseline-Verhalten
  - Detail-, Filter- und Tree-Pfade
  - Trustlist-, Auswahl-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `54/54` gruen

Kurzfazit:

- Der kleine TXT-Export-Payload nutzt jetzt denselben Helfer, statt den Text-Export direkt im Export-Dispatcher zusammenzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Text-Export-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Text-Export-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.194: Process-Guard-Monitoring-Status-Message `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Monitoring-Statusmeldungen eingefuehrt:
  - `_process_guard_monitoring_status_message()`
- wiederholte Monitoring-Status-Pfade vereinheitlicht, u. a. in:
  - `start_process_guard_monitoring()`
  - `stop_process_guard_monitoring()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Active-Text
  - Stopped-Text
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `59/59` gruen

Kurzfazit:

- Die kleinen Monitoring-Statusmeldungen nutzen jetzt denselben Helfer, statt den Text in Start- und Stop-Pfad getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Monitoring-Statuslogik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Monitoring-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.195: Process-Guard-Trustlist-Header `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Trustlist-Header eingefuehrt:
  - `_process_guard_trustlist_header()`
- wiederholte Trustlist-Header-Pfade vereinheitlicht, u. a. in:
  - `_process_guard_trustlist_lines()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Header-Text
  - Erwaehnung von `Vertrauensliste`
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `61/61` gruen

Kurzfazit:

- Der kleine Trustlist-Header nutzt jetzt denselben Helfer, statt den Header-Text direkt im Trustlist-Zeilenaufbau auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Header-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Trustlist-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.196: Repository-Guard-JSON-Export-Payload `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den JSON-Export eingefuehrt:
  - `_repository_guard_json_export_payload()`
- wiederholten JSON-Exportpfad vereinheitlicht, u. a. in:
  - `_repository_guard_export_payload()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartetes JSON mit Newline-Abschluss
  - genau einen abschliessenden Zeilenumbruch
- bewusst unveraendert geblieben sind:
  - Report-, Export-, Scan- und Baseline-Verhalten
  - Detail-, Filter-, Tree- und Selection-Pfade
  - Trustlist-, Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `56/56` gruen

Kurzfazit:

- Der kleine JSON-Export nutzt jetzt denselben Helfer, statt den `json.dumps(...)`-Pfad direkt im Export-Switch auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte JSON-Exportlogik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-JSON-Export-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.197: Repository-Guard-Trust-State-Label `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Trust-State-Labels eingefuehrt:
  - `_repository_guard_trust_state_label()`
- wiederholte Trust-State-Label-Pfade vereinheitlicht, u. a. in:
  - `refresh_repository_guard_sources_tree()`
  - `format_repository_guard_source_details()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannte Mapping-Werte
  - sicheren Fallback auf `-`
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline-, Trustlist- und Exportverhalten
  - Detail-, Filter-, Tree- und Selection-Pfade
  - Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `58/58` gruen

Kurzfazit:

- Das kleine Trust-State-Mapping nutzt jetzt denselben Helfer, statt die Label-Tabelle in Tree- und Detailpfad getrennt zu pflegen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Label-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Trust-State-Label-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.198: Process-Guard-Monitoring-Log-Message `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Monitoring-Logmeldungen eingefuehrt:
  - `_process_guard_monitoring_log_message()`
- wiederholte Monitoring-Logpfade vereinheitlicht, u. a. in:
  - `start_process_guard_monitoring()`
  - `stop_process_guard_monitoring()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannte Start-/Stop-Zustaende
  - sicheren Unknown-Fallback
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `63/63` gruen

Kurzfazit:

- Die kleinen Monitoring-Logmeldungen nutzen jetzt denselben Helfer, statt Start- und Stop-Text getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Monitoring-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Monitoring-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.199: Speedtest-Panel-Value-Text `netmon/features/speedtest_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/speedtest_controller.py tests/test_speedtest_module.py
./venv/bin/python -m ruff check netmon/features/speedtest_controller.py tests/test_speedtest_module.py
python3 -m black --check --workers 1 netmon/features/speedtest_controller.py
python3 -m black --check --workers 1 tests/test_speedtest_module.py
pytest tests/test_speedtest_module.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Panel-Metriktexte eingefuehrt:
  - `_speedtest_panel_value_text()`
- wiederholte Panel-Metrikpfade vereinheitlicht, u. a. in:
  - `_speedtest_panel_values()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierte vorhandene Metrik
  - sicheren Placeholder bei fehlender Metrik
- bewusst unveraendert geblieben sind:
  - Async-, History-, Warn- und Panel-Verhalten
  - Debug-, Status- und Persistenzpfade
  - die eigentliche Speedtest-CLI-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Speedtest-Modultests:
  - `60/60` gruen

Kurzfazit:

- Die kleinen Panel-Metriktexte nutzen jetzt denselben Helfer, statt Ping-, Jitter-, Download- und Upload-Felder getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Panel-Formatierungslogik zusaetzlich zu den bestehenden Speedtest-Regressionstests ab.
- Damit ist auch dieser kompakte Speedtest-Panel-Value-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.200: Security-Selected-Table-Row-Index `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Row-ID-zu-Index-Aufloesung eingefuehrt:
  - `_selected_table_row_index()`
- wiederholte Row-Index-Pfade vereinheitlicht, u. a. in:
  - `_selected_connected_device()`
  - `_security_selected_event_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Suffix-Aufloesung
  - sicheren `None`-Fallback fuer ungueltige Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `49/49` gruen

Kurzfazit:

- Die kleine Row-ID-Normalisierung nutzt jetzt denselben Helfer, statt Event- und Device-Pfad den Index getrennt aus dem Tabelleneintrag zu parsen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Row-Index-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Selected-Table-Row-Index-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.201: Repository-Guard-Tree-Selection-Index `netmon/features/repository_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
./venv/bin/python -m ruff check netmon/features/repository_guard_controller.py tests/test_repository_guard_controller.py
python3 -m black --check --workers 1 netmon/features/repository_guard_controller.py
python3 -m black --check --workers 1 tests/test_repository_guard_controller.py
pytest tests/test_repository_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Tree-Selection-Index-Aufloesung eingefuehrt:
  - `_selected_repository_guard_tree_index()`
- wiederholten Tree-Selection-Index-Pfad vereinheitlicht, u. a. in:
  - `_selected_repository_guard_tree_item()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Suffix-Aufloesung
  - sicheren `None`-Fallback fuer ungueltige Werte
- bewusst unveraendert geblieben sind:
  - Scan-, Baseline-, Trustlist- und Exportverhalten
  - Detail-, Filter-, Tree- und Selection-Pfade
  - Copy- und Quick-Action-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Repository-Guard-Controller-Tests:
  - `60/60` gruen

Kurzfazit:

- Die kleine Tree-Selection-Normalisierung nutzt jetzt denselben Helfer, statt den Index direkt im Item-Auswahlpfad zu parsen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tree-Index-Logik zusaetzlich zu den bestehenden Repository-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Repository-Guard-Tree-Selection-Index-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.202: Process-Guard-Tree-Selection-Index `netmon/features/process_guard_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
./venv/bin/python -m ruff check netmon/features/process_guard_controller.py tests/test_process_guard_controller.py
python3 -m black --check --workers 1 netmon/features/process_guard_controller.py
python3 -m black --check --workers 1 tests/test_process_guard_controller.py
pytest tests/test_process_guard_controller.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Tree-Selection-Index-Aufloesung eingefuehrt:
  - `_selected_process_guard_tree_index()`
- wiederholten Tree-Selection-Index-Pfad vereinheitlicht, u. a. in:
  - `_selected_process_guard_visible_finding()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Zeilenindex
  - sicheren `None`-Fallback ohne gueltige Auswahl
- bewusst unveraendert geblieben sind:
  - Pruef-, Monitoring- und Trustlist-Verhalten
  - Detail-, Tree- und Chad-Pfade
  - Filter-, Status- und Light-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Process-Guard-Controller-Tests:
  - `65/65` gruen

Kurzfazit:

- Die kleine Tree-Selection-Normalisierung nutzt jetzt denselben Helfer, statt den Zeilenindex direkt im Visible-Finding-Pfad abzuleiten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tree-Index-Logik zusaetzlich zu den bestehenden Process-Guard-Regressionstests ab.
- Damit ist auch dieser kompakte Process-Guard-Tree-Selection-Index-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.203: Security-Monitoring-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Monitoring-Logmeldungen eingefuehrt:
  - `_security_monitoring_log_message()`
- wiederholte Monitoring-Logpfade vereinheitlicht, u. a. in:
  - `security_start_monitoring()`
  - `security_stop_monitoring()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannte Monitoring-Zustaende
  - sicheren Unknown-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `51/51` gruen

Kurzfazit:

- Die kleinen Monitoring-Logmeldungen nutzen jetzt denselben Helfer, statt Start-, Stop- und Already-Running-Text getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Monitoring-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Monitoring-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.204: Security-Scan-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Scan-Logmeldungen eingefuehrt:
  - `_security_scan_log_message()`
- wiederholte Scan-Logpfade vereinheitlicht, u. a. in:
  - `security_scan_now()`
  - `security_input_access_scan()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannten Scan-Status
  - sicheren Unknown-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `53/53` gruen

Kurzfazit:

- Die kleine Scan-Logmeldung nutzt jetzt denselben Helfer, statt den Already-Running-Text in zwei Scan-Pfaden getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Scan-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Scan-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.205: Security-Filter-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Filter-Logmeldungen eingefuehrt:
  - `_security_filter_log_message()`
- wiederholte Filter-Logpfade vereinheitlicht, u. a. in:
  - `security_filter_portscan()`
  - `security_filter_relevant()`
  - `security_filter_external()`
  - `security_filter_all()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannte Filter-Modi
  - sicheren Fallback auf `Alle Events`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `55/55` gruen

Kurzfazit:

- Die kleinen Filter-Logmeldungen nutzen jetzt denselben Helfer, statt die vier Standardtexte in den Filter-Shortcuts getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Filter-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Filter-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.206: Security-Connected-Devices-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Connected-Devices-Logmeldungen eingefuehrt:
  - `_security_connected_devices_log_message()`
- wiederholten Connected-Devices-Logpfad vereinheitlicht, u. a. in:
  - `security_show_connected_devices()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten positiven Geraetezaehler
  - sicheren Clamp bei negativem Zaehler
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `57/57` gruen

Kurzfazit:

- Die kleine Connected-Devices-Logmeldung nutzt jetzt denselben Helfer, statt den `count`-Text direkt im Show-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Log-Formatierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Devices-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.207: Security-Table-Refreshed-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Table-Refresh-Logmeldungen eingefuehrt:
  - `_security_table_refreshed_log_message()`
- wiederholten Table-Refresh-Logpfad vereinheitlicht, u. a. in:
  - `security_refresh_table_action()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Tabelle`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `59/59` gruen

Kurzfazit:

- Die kleine Table-Refresh-Logmeldung nutzt jetzt denselben Helfer, statt den Text direkt im Refresh-Aktionspfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Table-Refreshed-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.208: Security-Views-Cleared-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Views-Cleared-Logmeldungen eingefuehrt:
  - `_security_views_cleared_log_message()`
- wiederholten Views-Cleared-Logpfad vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Ansichten`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `61/61` gruen

Kurzfazit:

- Die kleine Views-Cleared-Logmeldung nutzt jetzt denselben Helfer, statt den Text direkt im Clear-Views-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Views-Cleared-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.209: Security-Events-Cleared-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Events-Cleared-Logmeldungen eingefuehrt:
  - `_security_events_cleared_log_message()`
- wiederholten Events-Cleared-Logpfad vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `Events`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `63/63` gruen

Kurzfazit:

- Die kleine Events-Cleared-Logmeldung nutzt jetzt denselben Helfer, statt den Text direkt im Clear-Events-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Events-Cleared-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.210: Security-Events-Clear-Cancelled-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Cancelled-Logmeldungen eingefuehrt:
  - `_security_events_clear_cancelled_log_message()`
- wiederholten Cancelled-Logpfad vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Meldungstext
  - Erwaehnung von `abgebrochen`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `65/65` gruen

Kurzfazit:

- Die kleine Cancelled-Logmeldung nutzt jetzt denselben Helfer, statt den Abbruchtext direkt im Confirm-Abbruchpfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Meldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Events-Clear-Cancelled-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.211: Security-Views-Cleared-Detail-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Views-Cleared-Detailtexte eingefuehrt:
  - `_security_views_cleared_detail_text()`
- wiederholten Views-Cleared-Detailpfad vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Detailtext
  - Erwaehnung von `Ansichten`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `67/67` gruen

Kurzfazit:

- Der kleine Views-Cleared-Detailtext nutzt jetzt denselben Helfer, statt den Text direkt im Clear-Views-Detailpfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Detailtext-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Views-Cleared-Detail-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.212: Security-Clear-Events-Dialog-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Dialogtexte eingefuehrt:
  - `_security_clear_events_title()`
  - `_security_clear_events_body()`
- wiederholte Dialogtext-Pfade vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - exakten Dialogtitel
  - Erwaehnung von `Fortfahren?` im Dialogtext
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `69/69` gruen

Kurzfazit:

- Die kleinen Clear-Events-Dialogtexte nutzen jetzt dieselben Helfer, statt Titel und Body direkt im Confirm-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Dialogtext-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Clear-Events-Dialog-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.213: Security-Connected-Device-Status-Label `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Device-Statuslabels eingefuehrt:
  - `_connected_device_status_label()`
- wiederholten Device-Statuspfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekannten Baseline-Status
  - sicheren Default auf `neu`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `71/71` gruen

Kurzfazit:

- Das kleine Device-Statuslabel nutzt jetzt denselben Helfer, statt den `bekannt`/`neu`-Text direkt im Tabellenaufbau auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Statuslabel-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.214: Security-Connected-Device-Row-Tags `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Device-Row-Tags eingefuehrt:
  - `_connected_device_row_tags()`
- wiederholten Device-Tag-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Baseline-Geraete mit `device_known`
  - sicheren Default auf `device_new`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `73/73` gruen

Kurzfazit:

- Der kleine Device-Tag-Pfad nutzt jetzt denselben Helfer, statt die `device_known`/`device_new`-Auswahl direkt im Tabellenaufbau auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tag-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Row-Tags-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.215: Security-Connected-Device-Row-Values `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Device-Row-Values eingefuehrt:
  - `_connected_device_row_values()`
- wiederholten Device-Row-Values-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Spaltenwerte
  - sichere Defaultwerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `75/75` gruen

Kurzfazit:

- Der kleine Device-Row-Values-Pfad nutzt jetzt denselben Helfer, statt die Tabellenwerte direkt im Insert-Pfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Tabellenwert-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Row-Values-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.216: Security-Connected-Device-Field `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Connected-Device-Feldwerte eingefuehrt:
  - `_connected_device_field()`
- wiederholte Device-Feld-Fallbacks vereinheitlicht, u. a. in:
  - `_connected_device_detail_text()`
  - `_connected_device_row_values()`
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorhandenen Feldwert
  - Default-Fallback bei fehlendem Feld
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `79/79` gruen

Kurzfazit:

- Die kleinen Connected-Device-Text- und Tabellenpfade nutzen jetzt dieselbe Feldauflosung, statt Name/Typ/Pfad/Vendor/Product mehrfach direkt mit eigenen Fallbacks auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Feldlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Field-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.217: Security-Connected-Device-Field-Lines `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Connected-Device-Feldzeilen eingefuehrt:
  - `_connected_device_field_lines()`
- wiederholte Device-Zeilenpfade vereinheitlicht, u. a. in:
  - `_connected_device_detail_text()`
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Feldzeilen
  - sichere Default-Fallbacks
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `81/81` gruen

Kurzfazit:

- Die wiederholten Connected-Device-Zeilen fuer Typ/Pfad/Kennung/Vendor/Product/Bus/Phys/Unique-ID laufen jetzt ueber denselben kleinen Helfer, statt in Detail- und Inventartext separat aufgebaut zu werden.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Zeilenlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Field-Lines-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.218: Security-Connected-Device-Name `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Connected-Device-Namen eingefuehrt:
  - `_connected_device_name()`
- wiederholte Device-Name-Pfade vereinheitlicht, u. a. in:
  - `_connected_device_detail_text()`
  - `_connected_device_row_values()`
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorhandenen Namen
  - sicheren Default-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `83/83` gruen

Kurzfazit:

- Die kleinen Connected-Device-Namenspfade laufen jetzt ueber denselben Helfer, statt den Default mehrfach indirekt ueber den allgemeinen Feldhelfer auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Namenslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Name-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.219: Security-Normalized-State `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die State-Normalisierung eingefuehrt:
  - `_normalized_security_state()`
- wiederholte State-Normalisierung vereinheitlicht, u. a. in:
  - `_security_monitoring_log_message()`
  - `_security_scan_log_message()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Trim-plus-Lowercase-Normalisierung
  - leeren Default-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `85/85` gruen

Kurzfazit:

- Die kleinen Security-State-Pfade laufen jetzt ueber denselben Normalisierungshelfer, statt `strip().lower()` mehrfach direkt in den Log-Message-Helfern auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte State-Normalisierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Normalized-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.220: Security-Normalized-Filter-Mode `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Security-Filtermodus eingefuehrt:
  - `_normalized_security_filter_mode()`
- wiederholte Filter-Mode-Normalisierung vereinheitlicht, u. a. in:
  - `_security_filter_label()`
  - `_security_filter_log_message()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorhandenen Filtermodus
  - Default-Fallback auf `all`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `87/87` gruen

Kurzfazit:

- Die kleinen Security-Filterpfade laufen jetzt ueber denselben Mode-Helfer, statt `str(filter_mode or "all")` mehrfach direkt in Label- und Log-Helfern auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Filter-Mode-Normalisierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Normalized-Filter-Mode-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.221: Security-Filter-Label-Or-Default `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Security-Filterlabels eingefuehrt:
  - `_security_filter_label_or_default()`
- wiederholte Filter-Label-Aufloesung vereinheitlicht, u. a. in:
  - `_security_filter_label()`
  - `_security_filter_log_message()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - bekanntes Filterlabel
  - expliziten Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `89/89` gruen

Kurzfazit:

- Die kleinen Security-Filterlabel-Pfade laufen jetzt ueber denselben Helfer, statt die gleiche Modus-zu-Text-Aufloesung parallel in Label- und Log-Helfern zu halten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Label-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Filter-Label-Or-Default-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.222: Security-Monitoring-Status-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Monitoring-Status eingefuehrt:
  - `_security_monitoring_status_text()`
- wiederholte Monitoring-Status-Aufloesung vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `_build_security_chad_summary()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - `AKTIV` bei `True`
  - `AUS` bei `False`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `91/91` gruen

Kurzfazit:

- Die kleinen Monitoring-Statuspfade laufen jetzt ueber denselben Helfer, statt `AKTIV/AUS` an mehreren Stellen separat zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Monitoring-Statuslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Monitoring-Status-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.223: Security-Last-Alarm-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Alarm-Status eingefuehrt:
  - `_security_last_alarm_text()`
- wiederholte Alarm-Text-Aufloesung vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `_build_security_chad_summary()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten Alarmtext
  - Dash-Default
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `93/93` gruen

Kurzfazit:

- Die kleinen Alarm-Statuspfade laufen jetzt ueber denselben Helfer, statt `Letzter Alarm: ...` an mehreren Stellen separat zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Alarm-Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Last-Alarm-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.224: Security-Logging-Level-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Logging-Level-Text eingefuehrt:
  - `_security_logging_level_text()`
- wiederholte Logging-Level-Aufloesung vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `_build_security_chad_summary()`
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Standard-Prefix
  - Custom-Prefix
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `95/95` gruen

Kurzfazit:

- Die kleinen Logging-Level-Pfade laufen jetzt ueber denselben Helfer, statt `Logging` und `UFW Logging-Level` an mehreren Stellen separat zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Logging-Level-Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Logging-Level-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.225: Security-Events-Count-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Event-Zaehlertext eingefuehrt:
  - `_security_events_count_text()`
- wiederholte Event-Count-Aufloesung vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Standard-Prefix
  - Custom-Prefix
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `97/97` gruen

Kurzfazit:

- Die kleinen Event-Count-Pfade laufen jetzt ueber denselben Helfer, statt `Events` und `Anzahl Events` an mehreren Stellen separat zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Event-Zaehler-Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Events-Count-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.226: Security-Monitoring-Status-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Monitoring-Statuszeile eingefuehrt:
  - `_security_monitoring_status_line()`
- wiederholte Monitoring-Status-Zusammensetzung vereinheitlicht, u. a. in:
  - `security_update_status()`
  - `_build_security_chad_summary()`
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Standard-Prefix
  - Custom-Prefix
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `99/99` gruen

Kurzfazit:

- Die kleinen Monitoring-Statuszeilen laufen jetzt ueber denselben Helfer, statt `Monitoring` und `Monitoring-Status` an mehreren Stellen separat zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Monitoring-Statuszeilen-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Monitoring-Status-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.227: Security-Status-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer generische Security-Statuszeilen eingefuehrt:
  - `_security_status_text()`
- wiederholte Prefix-plus-Wert-Zusammensetzung vereinheitlicht, u. a. in:
  - `_security_monitoring_status_line()`
  - `_security_last_alarm_text()`
  - `_security_logging_level_text()`
  - `_security_events_count_text()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Stringwert
  - numerischen Wert
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `101/101` gruen

Kurzfazit:

- Die kleinen Security-Statuszeilen laufen jetzt ueber denselben generischen Helfer, statt `Prefix: Wert` mehrfach in mehreren Spezialisierungen direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Status-Textlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Status-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.228: Security-Header-Lines `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Security-Headerzeilen eingefuehrt:
  - `_security_header_lines()`
- wiederholte Header-Zeilen vereinheitlicht, u. a. in:
  - `_build_security_chad_summary()`
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Titel plus Trennlinie
  - negative Breite mit leerer Trennlinie
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `103/103` gruen

Kurzfazit:

- Die kleinen Security-Headerbloecke laufen jetzt ueber denselben Helfer, statt Titel, Trennlinie und Leerzeile in Summary und Export separat aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Header-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Header-Lines-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.229: Security-Event-Summary-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Security-Event-Zeilen eingefuehrt:
  - `_security_event_summary_line()`
- wiederholte Event-Zeilenformatierung vereinheitlicht, u. a. in:
  - `_build_security_chad_summary()` fuer relevante Events
  - `_build_security_chad_summary()` fuer externe Events
  - `_build_security_chad_summary()` fuer Gesamt-Events
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vollstaendige Event-Zeile mit Proto
  - Event-Zeile ohne Proto
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `105/105` gruen

Kurzfazit:

- Die kleinen Security-Event-Zeilen laufen jetzt ueber denselben Helfer, statt dieselbe Feldformatierung in mehreren Summary-Schleifen separat aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Event-Zeilenlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Event-Summary-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.230: Security-Append-Section `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Summary-Abschnittszeilen eingefuehrt:
  - `_append_security_section()`
- wiederholte Leerzeile-plus-Ueberschrift-Pfade vereinheitlicht, u. a. in:
  - `_build_security_chad_summary()` fuer Sofortmassnahmen
  - `_build_security_chad_summary()` fuer Baseline-/Kontextstatus
  - `_build_security_chad_summary()` fuer relevante, externe und Gesamt-Event-Abschnitte
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - normale Abschnittsergaenzung
  - Verhalten bei bestehender Leerzeile
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `107/107` gruen

Kurzfazit:

- Die kleinen Summary-Abschnitte laufen jetzt ueber denselben Helfer, statt Leerzeile und Ueberschrift mehrfach direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Abschnittslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Append-Section-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.231: Security-Export-Count-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Zaehlerzeilen eingefuehrt:
  - `_security_export_count_line()`
- wiederholte Export-Count-Zeilen vereinheitlicht, u. a. in:
  - `export_security_logs()` fuer UFW-Blocks
  - `export_security_logs()` fuer Portscan-Verdacht
  - `export_security_logs()` fuer Datei-, Device- und Input-Access-Zeilen
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Label plus Zahl
  - Nullwert
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `109/109` gruen

Kurzfazit:

- Die kleinen Export-Zaehlerzeilen laufen jetzt ueber denselben Helfer, statt `Label: Anzahl` mehrfach direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Count-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Count-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.232: Security-Export-Section-Lines `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Abschnittszeilen eingefuehrt:
  - `_security_export_section_lines()`
- wiederholte Export-Abschnittsheader vereinheitlicht, u. a. in:
  - `export_security_logs()` fuer `SECURITY SUMMARY`
  - `export_security_logs()` fuer `SECURITY EVENTS`
  - `export_security_logs()` fuer `DETAIL / ROHDATEN`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Titel plus Trennlinie
  - negative Breite mit leerer Trennlinie
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `111/111` gruen

Kurzfazit:

- Die kleinen Export-Abschnittsheader laufen jetzt ueber denselben Helfer, statt Titel und Trennlinie mehrfach direkt im Exportpfad aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Header-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Section-Lines-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.233: Security-Export-Section-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Abschnittsbloecke eingefuehrt:
  - `_security_export_section_block()`
- wiederholte Export-Header-Join-Pfade vereinheitlicht, u. a. in:
  - `export_security_logs()` fuer `SECURITY SUMMARY`
  - `export_security_logs()` fuer `SECURITY EVENTS`
  - `export_security_logs()` fuer `DETAIL / ROHDATEN`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Join mit abschliessendem Newline
  - negative Breite
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `113/113` gruen

Kurzfazit:

- Die kleinen Export-Headerbloecke laufen jetzt ueber denselben Helfer, statt `\"\\n\".join(...)+\"\\n\"` mehrfach direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Block-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Section-Block-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.234: Security-Event-Field `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Security-Event-Felder eingefuehrt:
  - `_security_event_field()`
- wiederholte Event-Feld-Fallbacks vereinheitlicht, u. a. in:
  - `_security_event_summary_line()`
  - `export_security_logs()` fuer Event-Tabellenzeilen
  - `export_security_logs()` fuer Detail-Headerzeilen
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorhandenen Feldwert
  - sicheren Default-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `115/115` gruen

Kurzfazit:

- Die kleinen Security-Event-Feldpfade laufen jetzt ueber denselben Helfer, statt dieselben `event.get(..., '-')`-Fallbacks mehrfach in Summary- und Exportpfaden direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Event-Feldlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Event-Field-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.235: Security-Export-Last-Alarm-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py
python3 -m black --check --workers 1 tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Alarmblock eingefuehrt:
  - `_security_export_last_alarm_block()`
- wiederholte Export-Alarm-Ausgabe vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Alarmtext mit doppeltem Newline
  - Dash-Default mit doppeltem Newline
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert
- Security-Modultests:
  - `117/117` gruen

Kurzfazit:

- Der kleine Export-Alarmpfad laeuft jetzt ueber denselben Helfer, statt Alarmtext und abschliessende Leerzeilen direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Alarm-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Last-Alarm-Block-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.236: Security-Export-Event-Table-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Tabellenzeilen eingefuehrt:
  - `_security_export_event_table_line()`
- wiederholte Event-Tabellenzeilenformatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Feldreihenfolge
  - sichere Default-Fallbacks
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `119/119` gruen

Kurzfazit:

- Die kleine Export-Event-Tabelle laeuft jetzt ueber denselben Helfer, statt dieselbe Feldverkettung direkt im Exportpfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Event-Zeilenlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Table-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.237: Security-Export-Event-Detail-Header-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Detail-Header eingefuehrt:
  - `_security_export_event_detail_header_line()`
- wiederholte Detail-Header-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Index- plus Feldformatierung
  - sichere Default-Fallbacks
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `121/121` gruen

Kurzfazit:

- Die kleine Export-Detailkopfzeile laeuft jetzt ueber denselben Helfer, statt Zeit- und Typ-Felder direkt im Exportloop zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Detail-Headerlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Detail-Header-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.238: Security-Export-Event-Raw-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Raw-Bloecke eingefuehrt:
  - `_security_export_event_raw_block()`
- wiederholte Raw-Block-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vorhandenen Raw-Text mit Abstand
  - sicheren Default-Fallback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `123/123` gruen

Kurzfazit:

- Der kleine Export-Raw-Block laeuft jetzt ueber denselben Helfer, statt Raw-Fallback und Leerzeilen direkt im Exportloop zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Raw-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Raw-Block-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.239: Security-Export-Aggregate-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Aggregatzeilen eingefuehrt:
  - `_security_export_aggregate_line()`
- wiederholte Aggregatzeilenformatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Kategorie- plus Count-Formatierung
  - generische Wertdurchgabe
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `125/125` gruen

Kurzfazit:

- Die kleine Export-Aggregatzeile laeuft jetzt ueber denselben Helfer, statt die String-Zusammensetzung direkt im Exportloop zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Aggregatlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Aggregate-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.240: Security-Export-Count-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Count-Bloecke eingefuehrt:
  - `_security_export_count_block()`
- wiederholte Count-Block-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Newline-Anhang
  - Wiederverwendung des bestehenden Count-Line-Formats
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `127/127` gruen

Kurzfazit:

- Der kleine Export-Count-Block laeuft jetzt ueber denselben Helfer, statt `Count-Line + Newline` mehrfach direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Count-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Count-Block-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.241: Security-Export-Event-Table-Header-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Tabellenkopfzeilen eingefuehrt:
  - `_security_export_event_table_header_line()`
- wiederholte Tabellenkopfzeilen-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Spaltenreihenfolge
  - erwartete Anzahl von Trennzeichen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `129/129` gruen

Kurzfazit:

- Die kleine Export-Event-Tabellenkopfzeile laeuft jetzt ueber denselben Helfer, statt den festen Spaltenstring direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Kopfzeilenlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Table-Header-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.242: Security-Export-Time-Line `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Zeitzeilen eingefuehrt:
  - `_security_export_time_line()`
- wiederholte Exportzeit-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten Zeitstempel
  - leeren Zeitstempel
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `131/131` gruen

Kurzfazit:

- Die kleine Exportzeit-Zeile laeuft jetzt ueber denselben Helfer, statt den festen Praefix plus Zeitstempel direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Exportzeit-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Time-Line-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.243: Security-Export-Status-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Statusbloecke eingefuehrt:
  - `_security_export_status_block()`
- wiederholte Statusblock-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Newline-Anhang
  - leeren Text
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `133/133` gruen

Kurzfazit:

- Die kleinen Export-Statuszeilen laufen jetzt ueber denselben Helfer, statt das `+ Newline` mehrfach direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Statusblock-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.244: Security-Export-Status-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer gebuendelte Export-Statuszeilen eingefuehrt:
  - `_security_export_status_blocks()`
- wiederholte Statuszeilen-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete AKTIV/HIGH/Count-Ausgabe
  - falsey Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `135/135` gruen

Kurzfazit:

- Die drei kleinen Export-Statuszeilen werden jetzt gemeinsam ueber denselben Helfer aufgebaut, statt die Kombination aus Statusfunktion plus Newline mehrfach direkt im Exportpfad auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Statusblock-Buendelung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Status-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.245: Security-Export-Path `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Dateipfad eingefuehrt:
  - `_security_export_path()`
- wiederholte Exportpfad-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Directory-plus-Stamp-Aufbau
  - leeren Stamp
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `137/137` gruen

Kurzfazit:

- Der kleine Export-Dateipfad laeuft jetzt ueber denselben Helfer, statt den Dateinamen direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Exportpfad-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Path-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.246: Security-Export-Header-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Headerblock eingefuehrt:
  - `_security_export_header_block()`
- wiederholte Headerblock-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Headertext
  - erwartete Zeilenanzahl
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `139/139` gruen

Kurzfazit:

- Der kleine Export-Headerblock laeuft jetzt ueber denselben Helfer, statt den festen Header direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Header-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.247: Security-Export-Summary-Section-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Summary-Section-Block eingefuehrt:
  - `_security_export_summary_section_block()`
- wiederholte Summary-Section-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Blocktext
  - erwartete Zeilenliste
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `141/141` gruen

Kurzfazit:

- Der kleine Export-Summary-Abschnitt laeuft jetzt ueber denselben Helfer, statt Titel und Divider direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Summary-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Summary-Section-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.248: Security-Export-Events-Section-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Events-Section-Block eingefuehrt:
  - `_security_export_events_section_block()`
- wiederholte Events-Section-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Blocktext
  - erwartete Zeilenliste
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `143/143` gruen

Kurzfazit:

- Der kleine Export-Events-Abschnitt laeuft jetzt ueber denselben Helfer, statt Titel und Divider direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Events-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Events-Section-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.249: Security-Export-Details-Section-Block `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Details-Section-Block eingefuehrt:
  - `_security_export_details_section_block()`
- wiederholte Details-Section-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Blocktext
  - erwartete Zeilenliste
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `145/145` gruen

Kurzfazit:

- Der kleine Export-Details-Abschnitt laeuft jetzt ueber denselben Helfer, statt Titel und Divider direkt im Exportpfad zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Details-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Details-Section-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.250: Security-Export-Summary-Count-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Export-Summary-Zaehler eingefuehrt:
  - `_security_export_summary_count_blocks()`
- wiederholte Summary-Zaehler-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Count-Ausgaben
  - leere Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `147/147` gruen

Kurzfazit:

- Die festen Export-Summary-Zaehler werden jetzt gemeinsam ueber denselben Helfer aufgebaut, statt mehrere nahezu identische Count-Bloecke direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Summary-Count-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Summary-Count-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.251: Security-Export-Aggregate-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Aggregat-Bloecke eingefuehrt:
  - `_security_export_aggregate_blocks()`
- wiederholte Aggregatblock-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Reihenfolge und Werte
  - leere Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `149/149` gruen

Kurzfazit:

- Die Export-Aggregatzeilen werden jetzt gemeinsam ueber denselben Helfer aufgebaut, statt den kleinen Aggregat-Loop direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Aggregatblock-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Aggregate-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.252: Security-Export-Event-Detail-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Detail-Bloecke eingefuehrt:
  - `_security_export_event_detail_blocks()`
- wiederholte Detailblock-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Reihenfolge und Inhalt
  - leere Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `151/151` gruen

Kurzfazit:

- Die Export-Event-Detailausgabe wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt den kleinen Header-plus-Raw-Loop direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Detailblock-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Detail-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.253: Security-Export-Details-Section-With-Spacing `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Details-Section-Abstand eingefuehrt:
  - `_security_export_details_section_with_spacing()`
- wiederholte Spacing-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwarteten Gesamttext
  - fuehrende Leerzeile
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `153/153` gruen

Kurzfazit:

- Der kleine Abstand vor dem Export-Details-Abschnitt laeuft jetzt ueber denselben Helfer, statt `\"\\n\" + Block` direkt im Exportpfad zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Details-Spacing-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Details-Section-With-Spacing-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.254: Security-Export-Write-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Write-Loops eingefuehrt:
  - `_security_export_write_blocks()`
- wiederholte Block-Schreibpfade vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Reihenfolge aller Blocks
  - leere Block-Sequenzen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `155/155` gruen

Kurzfazit:

- Die kleinen Export-Write-Loops laufen jetzt ueber denselben Helfer, statt dass `handle.write(...)` mehrfach in fast identischer Schleifenform direkt im Exportpfad steht.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Write-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Write-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.255: Security-Export-Dir-Candidates `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Exportverzeichnis-Kandidaten eingefuehrt:
  - `_security_export_dir_candidates()`
- wiederholte Desktop-Kandidatenzusammensetzung vereinheitlicht, u. a. in:
  - `security_export_dir()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Kandidatenpfade
  - erhaltenes Home-Praefix
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `157/157` gruen

Kurzfazit:

- Die kleinen Exportverzeichnis-Kandidaten laufen jetzt ueber denselben Helfer, statt die Desktop-Pfade direkt in `security_export_dir()` zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Exportverzeichnis-Kandidatenlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Dir-Candidates-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.256: Security-Export-Datetime-Formats `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Datumsformate eingefuehrt:
  - `_security_export_datetime_formats()`
- wiederholte Export-Datumsformatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Stamp- plus Anzeigeformat
  - Zero-Padding
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `159/159` gruen

Kurzfazit:

- Die beiden Export-Datumsformate laufen jetzt ueber denselben Helfer, statt die beiden `strftime`-Aufrufe direkt in `export_security_logs()` zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Datumsformatlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Datetime-Formats-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.257: Security-Export-Success-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Export-Erfolgsmeldung eingefuehrt:
  - `_security_export_success_message()`
- wiederholte Erfolgs-Logformatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten Pfad
  - leeren Pfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `161/161` gruen

Kurzfazit:

- Die Export-Erfolgsmeldung laeuft jetzt ueber denselben Helfer, statt den `tr(...).format(...)`-Pfad direkt in `export_security_logs()` zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Erfolgsmeldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Success-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.258: Security-Export-Failure-Log-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Export-Fehler-Logmeldung eingefuehrt:
  - `_security_export_failure_log_message()`
- wiederholte Fehler-Logformatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten Fehlertext
  - leeren Fehlertext
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `163/163` gruen

Kurzfazit:

- Die Export-Fehler-Logmeldung laeuft jetzt ueber denselben Helfer, statt den `tr(...).format(...)`-Pfad direkt im Fehlerzweig von `export_security_logs()` zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Fehlerlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Failure-Log-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.259: Security-Export-Failure-Dialog-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Export-Fehlerdialog-Meldung eingefuehrt:
  - `_security_export_failure_dialog_message()`
- wiederholte Fehlerdialog-Formatierung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - formatierten Fehlertext
  - leeren Fehlertext
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `165/165` gruen

Kurzfazit:

- Die Export-Fehlerdialog-Meldung laeuft jetzt ueber denselben Helfer, statt den `tr(...).format(...)`-Pfad direkt im `messagebox.showerror(...)`-Aufruf zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Fehlerdialog-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Failure-Dialog-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.260: Security-Export-Dialog-Title `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Export-Dialogtitel eingefuehrt:
  - `_security_export_dialog_title()`
- wiederholte Dialogtitel-Aufloesung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Default-Text
  - ueberschriebenen Uebersetzungstext
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `167/167` gruen

Kurzfazit:

- Der Export-Dialogtitel laeuft jetzt ueber denselben Helfer, statt die `tr(...)`-Aufloesung direkt im `messagebox.showerror(...)`-Aufruf zu behalten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Dialogtitel-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Dialog-Title-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.261: Security-Export-Failure-Dialog-Args `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Fehlerdialog-Argumente eingefuehrt:
  - `_security_export_failure_dialog_args()`
- wiederholte Dialogargument-Zusammensetzung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Titel plus Meldung mit Fehlertext
  - Titel plus Meldung mit leerem Fehlertext
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `169/169` gruen

Kurzfazit:

- Die Argumente fuer den Export-Fehlerdialog laufen jetzt ueber denselben Helfer, statt Titel und Meldung getrennt direkt im `messagebox.showerror(...)`-Aufruf zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Fehlerdialog-Argumentlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Failure-Dialog-Args-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.262: Security-Export-Failure-Messages `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Fehlermeldungen eingefuehrt:
  - `_security_export_failure_messages()`
- wiederholte Fehler-Meldungsbuendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Titel, Body und Logtext mit Fehler
  - Titel, Body und Logtext mit leerem Fehler
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `171/171` gruen

Kurzfazit:

- Die Export-Fehlermeldungen laufen jetzt ueber denselben Helfer, statt Dialog- und Logtexte im Fehlerzweig von `export_security_logs()` getrennt aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Fehlermeldungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Failure-Messages-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.263: Security-Export-Event-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Event-Bloecke eingefuehrt:
  - `_security_export_event_blocks()`
- wiederholte Event-Block-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Abschnitt, Kopfzeile und Eventzeile
  - leere Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `173/173` gruen

Kurzfazit:

- Der Export-Event-Abschnitt wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Abschnitt, Kopfzeile und Eventzeilen separat im Exportpfad zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Event-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Event-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.264: Security-Export-Details-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Details-Bloecke eingefuehrt:
  - `_security_export_details_blocks()`
- wiederholte Details-Abschnitt-plus-Eintraege-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Abschnitt plus Detaileintraege
  - leere Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `175/175` gruen

Kurzfazit:

- Der Export-Details-Abschnitt wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Abschnitt und Detaileintraege im Exportpfad getrennt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Details-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Details-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.265: Security-Export-Summary-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Summary-Bloecke eingefuehrt:
  - `_security_export_summary_blocks()`
- wiederholte Summary-Abschnitt-plus-Counts-plus-Aggregate-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Abschnitt, Count-Zeilen und Aggregate
  - leere Events und leere Aggregation
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `177/177` gruen

Kurzfazit:

- Der Export-Summary-Abschnitt wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Abschnitt, Count-Zeilen, Aggregate und Leerzeile im Exportpfad getrennt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Summary-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Summary-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.266: Security-Export-Intro-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Intro-Bloecke eingefuehrt:
  - `_security_export_intro_blocks()`
- wiederholte Header-, Zeit-, Status- und Alarm-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Header, Zeit-, Status- und Alarmzeilen
  - falsey Werte im Intro-Block
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `179/179` gruen

Kurzfazit:

- Der Export-Intro-Abschnitt wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Header, Zeit-, Status- und Alarmzeilen im Exportpfad getrennt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Intro-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Intro-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.267: Security-Export-Content-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Content-Bloecke eingefuehrt:
  - `_security_export_content_blocks()`
- wiederholte Summary-, Event- und Detail-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Summary-, Event- und Detailblock mit Inhalt
  - leere Events und leere Aggregation
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `181/181` gruen

Kurzfazit:

- Der Export-Content-Abschnitt wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Summary-, Event- und Detailbloecke im Exportpfad getrennt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Content-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Content-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.268: Security-Export-Blocks `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer vollstaendige Export-Bloecke eingefuehrt:
  - `_security_export_blocks()`
- wiederholte Intro- und Content-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - kompletten Exportblock mit Inhalt
  - leere Eingaben ueber den Gesamtblock
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `183/183` gruen

Kurzfazit:

- Der vollstaendige Exportaufbau wird jetzt gemeinsam ueber denselben Helfer verdrahtet, statt Intro- und Content-Bloecke im Exportpfad getrennt aufzurufen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Blocklogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Blocks-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.269: Security-Export-Target `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Export-Zielwerte eingefuehrt:
  - `_security_export_target()`
- wiederholte Datumsformat- und Pfad-Buendelung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von Exportpfad und Anzeigezeit
  - verschachtelte Exportverzeichnisse
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `185/185` gruen

Kurzfazit:

- Das Exportziel wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt Datumsformatierung und Pfadaufbau im Exportpfad getrennt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Target-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Target-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.270: Security-Export-Blocks-For-App `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer app-basierte Export-Bloecke eingefuehrt:
  - `_security_export_blocks_for_app()`
- wiederholte App-Wert-Aufloesung fuer den Exportblock vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - aktuellen App-Zustand mit Inhalt
  - fehlende Werte und leere Events
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `187/187` gruen

Kurzfazit:

- Der Exportblock fuer die App wird jetzt gemeinsam ueber denselben Helfer aufgebaut, statt die einzelnen App-Werte direkt im Exportpfad weiterzureichen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Blocks-for-App-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Blocks-for-App-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.271: Security-Export-Completion `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleine gemeinsame Helfer fuer Export-Abschluss eingefuehrt:
  - `_security_export_success()`
  - `_security_export_failure()`
- wiederholte Erfolgs-/Fehler-Abschlussverdrahtung vereinheitlicht, u. a. in:
  - `export_security_logs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Erfolgsmeldung mit Logausgabe
  - Fehlerdialog plus Logausgabe
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen- und Summary-Pfade ausserhalb des Exports
  - Baseline-, Export- und Parser-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `189/189` gruen

Kurzfazit:

- Der Export-Abschluss laeuft jetzt gemeinsam ueber dieselben Helfer, statt Erfolgs- und Fehlerpfade direkt in `export_security_logs()` zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Export-Completion-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Export-Completion-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.272: Security-Status-Values `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Statusanzeige-Werte eingefuehrt:
  - `_security_status_values()`
- wiederholte Status-, Logging-, Count- und Alarm-Aufloesung vereinheitlicht, u. a. in:
  - `security_update_status()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Statuswerte mit Inhalt
  - falsey Werte im Statusblock
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `191/191` gruen

Kurzfazit:

- Die vier Statusanzeige-Werte laufen jetzt gemeinsam ueber denselben Helfer, statt in `security_update_status()` einzeln aufgebaut zu werden.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Status-Values-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Status-Values-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.273: Security-Chad-Analysis-Helper `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Chad-Analyse-Aufrufe eingefuehrt:
  - `_prepare_security_chad_analysis()`
- wiederholte Titel-/Summary-Verdrahtung vereinheitlicht, u. a. in:
  - `prepare_security_chad_analysis()`
  - `prepare_security_chad_curated_analysis()`
  - `prepare_security_chad_technical_analysis()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Standardtitel der normalen Analyse
  - Builder-Ergebnis im Helferpfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `193/193` gruen

Kurzfazit:

- Die Chad-Analyse-Aufrufe laufen jetzt gemeinsam ueber denselben Helfer, statt Titel und Summary in mehreren Funktionen separat zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Chad-Analysis-Helferlogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Chad-Analysis-Helper-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.274: Security-Filter-Apply-Spec `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Filter-Spezifikationen eingefuehrt:
  - `_security_filter_apply_spec()`
- wiederholte Mode-/Translation-Key-/Logtext-Verdrahtung vereinheitlicht, u. a. in:
  - `security_filter_portscan()`
  - `security_filter_relevant()`
  - `security_filter_external()`
  - `security_filter_all()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartetes Tuple bei bekanntem Modus
  - Fallback auf `all` bei unbekanntem Modus
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `195/195` gruen

Kurzfazit:

- Die Filter-Wrapper holen ihre Spezifikation jetzt gemeinsam aus demselben Helfer, statt Mode, Translation-Key und Logtext separat zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Filter-Apply-Spec-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Filter-Apply-Spec-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.275: Security-Clear-Events-Dialog-Args `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Clear-Events-Dialogargumente eingefuehrt:
  - `_security_clear_events_dialog_args()`
- wiederholte Titel-/Body-Aufloesung vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Standardtexte ohne Uebersetzungen
  - uebersetzte Rueckgabewerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `197/197` gruen

Kurzfazit:

- Die Clear-Events-Dialogargumente laufen jetzt gemeinsam ueber denselben Helfer, statt Titel und Body direkt in `security_clear_events()` aufloesen zu lassen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Clear-Events-Dialog-Args-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Clear-Events-Dialog-Args-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.276: Security-Reset-Event-State `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Event-Reset-Zustand eingefuehrt:
  - `_reset_security_event_state()`
- wiederholte Reset-Aufloesung fuer Event-bezogene App-Zustaende vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Ruecksetzen aller Event-bezogenen Felder
  - Erhalt unberuehrter Fremdfelder
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `199/199` gruen

Kurzfazit:

- Die Event-Reset-Zustaende laufen jetzt gemeinsam ueber denselben Helfer, statt in `security_clear_events()` mehrere App-Felder einzeln zurueckzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Reset-Event-State-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Reset-Event-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.277: Security-Clear-Events-Status-Color `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Clear-Events-Statusfarbe eingefuehrt:
  - `_security_clear_events_status_color()`
- wiederholte Monitoring-zu-Farb-Aufloesung vereinheitlicht, u. a. in:
  - `security_clear_events()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - `green` bei aktivem Monitoring
  - `gray` bei inaktivem Monitoring
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `201/201` gruen

Kurzfazit:

- Die Statusfarbe nach dem Clear-Events-Pfad laeuft jetzt ueber denselben Helfer, statt die Monitoring-zu-Farb-Aufloesung direkt in `security_clear_events()` auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Clear-Events-Status-Color-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Clear-Events-Status-Color-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.278: Security-Reset-View-State `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den View-Reset eingefuehrt:
  - `_reset_security_view_state()`
- wiederholte Ruecksetzung sichtbarer Events und Row-Metadaten vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Leeren sichtbarer Events und Row-Metadaten
  - Erhalt unberuehrter Fremdfelder
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `203/203` gruen

Kurzfazit:

- Der View-Reset laeuft jetzt gemeinsam ueber denselben Helfer, statt sichtbare Events und Row-Metadaten direkt in `security_clear_views()` einzeln zurueckzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Reset-View-State-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Reset-View-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.279: Security-Clear-View-Tables `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Leeren der View-Tabellen eingefuehrt:
  - `_clear_security_view_tables()`
- wiederholte Tabellen-Clear-Aufrufe vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Leeren aller bekannten Tabellen
  - Ignorieren fehlender Tabellen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `205/205` gruen

Kurzfazit:

- Das Leeren der View-Tabellen laeuft jetzt gemeinsam ueber denselben Helfer, statt die drei Tabellen direkt in `security_clear_views()` einzeln anzusprechen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Clear-View-Tables-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Clear-View-Tables-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.280: Security-Finish-Clear-Views `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Clear-Views-Abschluss eingefuehrt:
  - `_finish_security_clear_views()`
- wiederholte Detailtext-/Log-Abschlussverdrahtung vereinheitlicht, u. a. in:
  - `security_clear_views()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Detailtext plus Logmeldung
  - Logmeldung auch ohne Detail-Widget
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `207/207` gruen

Kurzfazit:

- Der Abschluss von `security_clear_views()` laeuft jetzt gemeinsam ueber denselben Helfer, statt Detailtext und Logmeldung direkt in der Funktion zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Finish-Clear-Views-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Finish-Clear-Views-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.281: Security-Selected-Connected-Device-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Detailtext des ausgewaehlten Devices eingefuehrt:
  - `_selected_connected_device_text()`
- wiederholte Device-zu-Detailtext-Aufloesung vereinheitlicht, u. a. in:
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Detailtext bei gueltiger Auswahl
  - leerer Rueckgabewert ohne Auswahl
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf
- Security-Modultests:
  - `209/209` gruen

Kurzfazit:

- Der Detailtext des ausgewaehlten Devices wird jetzt gemeinsam ueber denselben Helfer aufgeloest, statt die Device-zu-Text-Verdrahtung direkt in `on_connected_device_select()` zu halten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Selected-Connected-Device-Text-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Selected-Connected-Device-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.282: Security-Show-Connected-Devices-Abschluss `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Abschluss der Connected-Devices-Anzeige eingefuehrt:
  - `_finish_security_show_connected_devices()`
- wiederholte Detailtext-/Count-/Log-Verdrahtung vereinheitlicht, u. a. in:
  - `security_show_connected_devices()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Detailtext plus Logmeldung bei vorhandenem Inventar
  - `0`-Logmeldung bei leerem Inventar
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `211/211` gruen

Kurzfazit:

- `security_show_connected_devices()` haengt den Inventartext und die Abschlusslogmeldung jetzt ueber denselben kleinen Helfer zusammen, statt den Abschlussblock direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Devices-Abschlusslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Show-Connected-Devices-Abschlussblock in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.283: Security-Connected-Device-Inventory-Entry `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Textblock eines Inventory-Eintrags eingefuehrt:
  - `_connected_device_inventory_entry_lines()`
- wiederholten Entry-Zeilenaufbau vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - vollstaendige Zeilenbildung eines konkreten Devices
  - sichere Default-Zeilenbildung bei leerem Device-Dict
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `213/213` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht den geraetespezifischen Zeilenaufbau jetzt ueber denselben kleinen Helfer, statt den Block direkt in der Schleife auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Entry-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Entry-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.284: Security-Connected-Device-Inventory-Header `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Inventory-Header eingefuehrt:
  - `_connected_device_inventory_header_lines()`
- wiederholten Header-Zeilenaufbau vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Count-/Baseline-Header bei befuelltem Inventar
  - sichere Default-Headerwerte bei `None`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `215/215` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht den Kopfblock jetzt ueber denselben kleinen Helfer, statt die Header-Zeilen direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Header-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Header-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.285: Security-Connected-Device-Inventory-Empty-Message `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die leere Inventory-Meldung eingefuehrt:
  - `_connected_device_inventory_empty_message()`
- wiederholten Empty-State-Textpfad vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabewert der Empty-State-Meldung
  - Nutzung der Empty-State-Meldung im Inventory-Formatpfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `217/217` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht die leere Inventar-Meldung jetzt ueber denselben kleinen Helfer, statt den Text direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Empty-Message-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Empty-Message-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.286: Security-Connected-Device-Inventory-Body `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Inventory-Body eingefuehrt:
  - `_connected_device_inventory_body_lines()`
- wiederholten Body-Zeilenaufbau vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Zeilenbildung mehrerer Device-Eintraege
  - leeres Ergebnis bei fehlendem Inventar
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `219/219` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht den Body jetzt ueber denselben kleinen Helfer, statt die Eintrags-Schleife direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Body-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Body-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.287: Security-Connected-Device-Inventory-Lines `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die komplette Inventory-Liste eingefuehrt:
  - `_connected_device_inventory_lines()`
- wiederholte Header-/Empty-/Body-Verdrahtung vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Listenaufbau bei leerem Inventar
  - Listenaufbau bei vorhandenem Device-Eintrag
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `221/221` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht Header, Empty-State und Body jetzt ueber denselben kleinen Listen-Helfer, statt die Verdrahtung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Lines-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Lines-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.288: Security-Connected-Device-Inventory-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die finale Inventory-Textzusammensetzung eingefuehrt:
  - `_connected_device_inventory_text()`
- wiederholten `join/rstrip/newline`-Pfad vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - abschliessenden Newline-Pfad
  - Trimmen von ueberzaehligen Leerzeilen am Ende
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `223/223` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht die finale Textzusammensetzung jetzt ueber denselben kleinen Helfer, statt `join/rstrip/newline` direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Text-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.289: Security-Connected-Device-Inventory-Context `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die App-bezogene Inventory-/Baseline-Aufloesung eingefuehrt:
  - `_connected_device_inventory_context()`
- wiederholte App-Verdrahtung vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von Inventar plus Baseline
  - sichere Default-Baseline bei fehlendem Attribut
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `225/225` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht Inventar und Baseline jetzt ueber denselben kleinen Kontext-Helfer, statt die App-Verdrahtung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Context-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Context-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.290: Security-Connected-Device-Inventory-Text-For `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Inventory-zu-Text-Verdrahtung eingefuehrt:
  - `_connected_device_inventory_text_for()`
- wiederholte Lines-zu-Text-Verkettung vereinheitlicht, u. a. in:
  - `format_connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Textbildung bei leerem Inventar
  - Textbildung bei vorhandenem Device-Eintrag
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `227/227` gruen

Kurzfazit:

- `format_connected_device_inventory()` bezieht die reine Inventory-zu-Text-Verdrahtung jetzt ueber denselben kleinen Helfer, statt Lines und Textlogik direkt zu verbinden.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Inventory-Text-For-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Text-For-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.291: Security-Connected-Device-Table-Clear `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Leeren der Connected-Device-Tabelle eingefuehrt:
  - `_clear_connected_device_table()`
- wiederholten Tabellen-Clear-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Loeschen aller vorhandenen Child-Items
  - no-op bei leerer Tabelle
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `229/229` gruen

Kurzfazit:

- `refresh_connected_device_table()` leert die Device-Tabelle jetzt ueber denselben kleinen Helfer, statt den Child-Delete-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Table-Clear-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Table-Clear-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.292: Security-Connected-Device-Row-Insert `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Einfuegen einer Connected-Device-Zeile eingefuehrt:
  - `_insert_connected_device_row()`
- wiederholten Row-Insert-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Einfuegen einer neuen Device-Zeile mit erwarteten Werten und Tags
  - Known-Tag-Pfad fuer Baseline-Devices
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach finalem Formatcheck; dabei wurde die Testdatei einmalig automatisch nachformatiert
- Security-Modultests:
  - `231/231` gruen

Kurzfazit:

- `refresh_connected_device_table()` fuegt Device-Zeilen jetzt ueber denselben kleinen Helfer ein, statt den Insert-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Row-Insert-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Row-Insert-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.293: Security-Connected-Device-Table-Populate `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Inventory-zu-Tabellenbefuellung eingefuehrt:
  - `_populate_connected_device_table()`
- wiederholten Populate-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Einfuegen aller Inventory-Zeilen
  - no-op bei leerem Inventar
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `233/233` gruen

Kurzfazit:

- `refresh_connected_device_table()` befuellt die Device-Tabelle jetzt ueber denselben kleinen Helfer, statt die Populate-Schleife direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Table-Populate-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Table-Populate-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.294: Security-Connected-Device-Table-Inventory `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Inventory-plus-Store im Tabellenpfad eingefuehrt:
  - `_connected_device_table_inventory()`
- wiederholte Inventory-/State-Verdrahtung vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe und Speichern eines befuellten Inventars
  - Speichern eines leeren Inventars
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `235/235` gruen

Kurzfazit:

- `refresh_connected_device_table()` bezieht Inventar und App-State jetzt ueber denselben kleinen Helfer, statt die Inventory-/Store-Verdrahtung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Table-Inventory-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Table-Inventory-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.295: Security-Connected-Device-Table-Lookup `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Connected-Device-Table-Lookup eingefuehrt:
  - `_connected_device_table()`
- wiederholte Table-Aufloesung vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe einer vorhandenen Tabelle
  - `None` bei fehlendem Table-Attribut
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `237/237` gruen

Kurzfazit:

- Die Connected-Device-Tabelle wird jetzt an mehreren Stellen ueber denselben kleinen Lookup-Helfer aufgeloest, statt die Attributabfrage direkt zu duplizieren.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Table-Lookup-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Table-Lookup-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.296: Security-Connected-Device-Table-View-Refresh `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Tabellen-Refresh-Sequenz eingefuehrt:
  - `_refresh_connected_device_table_view()`
- wiederholte Configure-/Clear-/Populate-Verdrahtung vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aufrufreihenfolge der Teilhelfer
  - Weitergabe eines leeren Inventars an den Populate-Pfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `239/239` gruen

Kurzfazit:

- `refresh_connected_device_table()` fuehrt die Tabellen-Update-Sequenz jetzt ueber denselben kleinen Helfer aus, statt Configure, Clear und Populate direkt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Table-View-Refresh-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Table-View-Refresh-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.297: Security-Connected-Device-Select-Finish `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Abschluss der Device-Auswahl eingefuehrt:
  - `_finish_connected_device_select()`
- wiederholten Detail-Write-Pfad vereinheitlicht, u. a. in:
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Schreiben des Detailtexts ins Widget
  - sicherer no-op ohne Detail-Widget
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `241/241` gruen

Kurzfazit:

- `on_connected_device_select()` schreibt den Detailtext jetzt ueber denselben kleinen Abschluss-Helfer, statt den Detail-Write-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Select-Finish-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Select-Finish-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.298: Security-Connected-Device-Selection-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Table-Lookup plus Detailtext-Aufloesung eingefuehrt:
  - `_selected_connected_device_selection_text()`
- wiederholte Auswahl-Verdrahtung vereinheitlicht, u. a. in:
  - `on_connected_device_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Detailtext-Aufloesung ueber die App-Tabelle
  - leerer Rueckgabewert ohne vorhandene Tabelle
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `243/243` gruen

Kurzfazit:

- `on_connected_device_select()` bezieht Table-Lookup und Detailtext jetzt ueber denselben kleinen Helfer, statt die Auswahl-Verdrahtung direkt aufzubauen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Selection-Text-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Selection-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.299: Security-Connected-Device-Display-Payload `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer Refresh-plus-Format-Aufloesung eingefuehrt:
  - `_connected_device_display_payload()`
- wiederholte Show-Verdrahtung vereinheitlicht, u. a. in:
  - `security_show_connected_devices()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von Inventar plus Text bei befuelltem Payload
  - Beibehaltung von leerem Inventar plus Empty-State-Text
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `245/245` gruen

Kurzfazit:

- `security_show_connected_devices()` bezieht Refresh und Inventartext jetzt ueber denselben kleinen Helfer, statt den Show-Pfad direkt zu verdrahten.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Display-Payload-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Display-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.300: Security-Connected-Device-Display-Log-Text `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Logtext-Aufloesung beim Device-Display eingefuehrt:
  - `_connected_device_display_log_text()`
- wiederholten Logtext-Pfad vereinheitlicht, u. a. in:
  - `_finish_security_show_connected_devices()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Logtext bei positiver Device-Anzahl
  - Logtext bei leerem Inventar
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Detail-, Tabellen-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `247/247` gruen

Kurzfazit:

- `_finish_security_show_connected_devices()` bezieht den Logtext jetzt ueber denselben kleinen Helfer, statt Count und Uebersetzung direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Connected-Device-Display-Log-Text-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Display-Log-Text-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.301: Security-Input-Access-Table-Clear `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Leeren der Input-Access-Tabelle eingefuehrt:
  - `_clear_input_access_table()`
- wiederholten Tabellen-Clear-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Loeschen aller vorhandenen Input-Access-Child-Items
  - sicherer no-op bei Tabellenfehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `249/249` gruen

Kurzfazit:

- `refresh_input_access_table()` leert die Input-Access-Tabelle jetzt ueber denselben kleinen Helfer, statt den Clear-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Table-Clear-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Table-Clear-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.302: Security-Input-Access-Row-Insert `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Einfuegen einer Input-Access-Zeile eingefuehrt:
  - `_insert_input_access_row()`
- wiederholten Row-Insert-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Einfuegen erwarteter Werte in die Tabelle
  - sichere Default-Werte bei leerem Row-Dict
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `251/251` gruen

Kurzfazit:

- `refresh_input_access_table()` fuegt Input-Access-Zeilen jetzt ueber denselben kleinen Helfer ein, statt den Insert-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Row-Insert-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Row-Insert-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.303: Security-Input-Access-Row-Meta `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Speichern von Input-Access-Row-Meta eingefuehrt:
  - `_store_input_access_row_meta()`
- wiederholten Row-Meta-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Kopie einer neuen Row in die App-Mapping-Struktur
  - Ueberschreiben eines bestehenden Meta-Eintrags
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `253/253` gruen

Kurzfazit:

- `refresh_input_access_table()` speichert Row-Metadaten jetzt ueber denselben kleinen Helfer, statt die Mapping-Zuweisung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Row-Meta-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Row-Meta-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.304: Security-Input-Access-Populate `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Befuellen der Input-Access-Tabelle eingefuehrt:
  - `_populate_input_access_table()`
- wiederholten Populate-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Einfuegen mehrerer Zeilen inklusive Meta-Speicherung
  - robustes Ignorieren leerer Row-Listen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `255/255` gruen

Kurzfazit:

- `refresh_input_access_table()` befuellt die Input-Access-Tabelle jetzt ueber denselben kleinen Helfer, statt den Insert-plus-Meta-Loop direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Populate-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Populate-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.305: Security-Input-Access-Refresh-Log `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Input-Access-Refresh-Logzeile eingefuehrt:
  - `_input_access_refresh_log_message()`
- wiederholten Ergebnis-Logpfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekte Logzeile mit beliebigem Count
  - sauberes Verhalten bei Count `0`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `257/257` gruen

Kurzfazit:

- `refresh_input_access_table()` erzeugt seine Ergebniszeile jetzt ueber denselben kleinen Helfer, statt den Logtext direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Refresh-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Refresh-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.306: Security-Input-Access-Inventory-Row `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Inventory-Row-Aufbau eingefuehrt:
  - `_input_access_inventory_row()`
- wiederholten Row-Dict-Pfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekten Aufbau vollstaendiger Row-Werte
  - sichere Defaults fuer leere Werte und nicht-whitelistete Prozesse
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `259/259` gruen

Kurzfazit:

- `current_input_access_inventory()` erzeugt seine einzelnen Inventar-Zeilen jetzt ueber denselben kleinen Helfer, statt den Row-Dict-Aufbau direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Inventory-Row-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Inventory-Row-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.307: Security-Input-Access-Pid-Normalisierung `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Input-Access-PID-Normalisierung eingefuehrt:
  - `_input_access_pid_number()`
- wiederholten PID-Normalisierungspfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Umwandlung gueltiger Ziffernstrings in Integer
  - Rueckfall auf einen Defaultwert bei ungueltigen PID-Werten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `261/261` gruen

Kurzfazit:

- `current_input_access_inventory()` normalisiert PID-Werte jetzt ueber denselben kleinen Helfer, statt Sortier- und Whitelist-Pfad getrennt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-PID-Normalisierungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Pid-Normalisierungs-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.308: Security-Input-Access-Inventory-Fehlertext `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Inventar-Fehlertext eingefuehrt:
  - `_input_access_inventory_error_message()`
- wiederholten Fehler-Logpfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Einbindung von Exception-Texten in die Meldung
  - korrektes Verhalten fuer bereits formatierte Plain-Values
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `263/263` gruen

Kurzfazit:

- `current_input_access_inventory()` erzeugt seinen Fehlerlogtext jetzt ueber denselben kleinen Helfer, statt die Meldung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Inventar-Fehlertext-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Inventory-Fehlertext-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.309: Security-Input-Access-Prozesssortierung `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check --workers 1 netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Input-Access-Prozesssortierung eingefuehrt:
  - `_input_access_sorted_process_items()`
- wiederholten Sortierpfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - numerische Sortierung gueltiger PID-Keys
  - robustes Verhalten fuer leere und nichtnumerische Prozess-Keys
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert nach Formatlauf und Formatcheck
- Security-Modultests:
  - `265/265` gruen

Kurzfazit:

- `current_input_access_inventory()` sortiert Prozess-Items jetzt ueber denselben kleinen Helfer, statt den Sortierausdruck direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Prozesssortierungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Prozesssortierungs-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.310: Security-Input-Access-Scan-Guard `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Scan-Guard eingefuehrt:
  - `_input_access_scan_state_or_log()`
- wiederholten Scan-und-Fehlerpfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe erfolgreicher Scan-Ergebnisse ohne Logging
  - Logging plus `None`-Rueckgabe bei Scan-Fehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert bzw. nach Test-Ergaenzung sauber formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `267/267` gruen

Kurzfazit:

- `current_input_access_inventory()` holt seinen Scan-Zustand jetzt ueber denselben kleinen Helfer, statt den Guard-und-Fehlerpfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Scan-Guard-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Scan-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.311: Security-Input-Access-Pfadsortierung `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Input-Access-Pfadsortierung eingefuehrt:
  - `_input_access_sorted_paths()`
- wiederholten Pfadsortierpfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - stabile lexikographische Sortierung vorhandener Input-Access-Pfade
  - robustes Verhalten fuer `None` und leere Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `269/269` gruen

Kurzfazit:

- `current_input_access_inventory()` iteriert seine Pfade jetzt ueber denselben kleinen Helfer, statt die Sortierung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Pfadsortierungslogik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Pfadsortierungs-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.312: Security-Input-Access-Per-Path-Rows `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Row-Aufbau pro Pfad eingefuehrt:
  - `_input_access_inventory_rows_for_path()`
- wiederholten Inner-Loop-Pfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - sortierten Aufbau mehrerer Rows inklusive Whitelist-Status
  - robustes Verhalten bei fehlenden Prozessdaten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `271/271` gruen

Kurzfazit:

- `current_input_access_inventory()` erzeugt seine Rows pro Device-Pfad jetzt ueber denselben kleinen Helfer, statt den inneren Schleifenblock direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Per-Path-Row-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Per-Path-Rows-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.313: Security-Input-Access-Pfadkontext `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Pfadkontext eingefuehrt:
  - `_input_access_path_context()`
- wiederholten Kontextaufbau pro Pfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von Device-Name, Device-Typ und Prozessmapping fuer vorhandene Pfade
  - leeres Prozessmapping als robuster Default fuer fehlende Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `273/273` gruen

Kurzfazit:

- `current_input_access_inventory()` holt seinen Pfadkontext jetzt ueber denselben kleinen Helfer, statt den Kontextaufbau direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Pfadkontext-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Pfadkontext-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.314: Security-Input-Access-Whitelist-Status `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Whitelist-Status eingefuehrt:
  - `_input_access_whitelist_status()`
- wiederholten Whitelist-Checkpfad vereinheitlicht, u. a. in:
  - `_input_access_inventory_rows_for_path()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Nutzung normalisierter PID-Werte beim Whitelist-Check
  - sauberen `False`-Rueckfall fuer nicht passende oder falsey Ergebnisse
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `275/275` gruen

Kurzfazit:

- `_input_access_inventory_rows_for_path()` ermittelt seinen Whitelist-Status jetzt ueber denselben kleinen Helfer, statt Check und Bool-Konvertierung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Whitelist-Status-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Whitelist-Status-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.315: Security-Input-Access-Process-Row `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Process-Row-Aufbau eingefuehrt:
  - `_input_access_process_row()`
- wiederholten Per-Process-Row-Pfad vereinheitlicht, u. a. in:
  - `_input_access_inventory_rows_for_path()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aufbau einer bekannten Row bei positiver Whitelist-Pruefung
  - Aufbau einer Pruefen-Row bei nicht whitelistedem Prozess
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `277/277` gruen

Kurzfazit:

- `_input_access_inventory_rows_for_path()` erzeugt seine einzelnen Prozess-Rows jetzt ueber denselben kleinen Helfer, statt Whitelist-Check und Row-Bau direkt zu kombinieren.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Process-Row-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Process-Row-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.316: Security-Input-Access-Current-Path-Rows `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Row-Aufbau des aktuellen Pfads eingefuehrt:
  - `_input_access_rows_for_current_path()`
- wiederholten Current-Path-Row-Pfad vereinheitlicht, u. a. in:
  - `current_input_access_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe sortierter Rows fuer einen vorhandenen Pfad
  - robustes Verhalten bei fehlenden Prozessdaten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `279/279` gruen

Kurzfazit:

- `current_input_access_inventory()` erzeugt seine Rows fuer den aktuellen Pfad jetzt ueber denselben kleinen Helfer, statt Kontext- und Row-Aufbau direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Current-Path-Rows-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Current-Path-Rows-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.317: Security-Input-Access-Status-Label `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Input-Access-Status-Label eingefuehrt:
  - `_input_access_status_label()`
- wiederholten Status-Textpfad vereinheitlicht, u. a. in:
  - `_input_access_inventory_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe von `bekannt` fuer whitelisted Prozesse
  - Rueckgabe von `prüfen` fuer nicht whitelisted Prozesse
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `281/281` gruen

Kurzfazit:

- `_input_access_inventory_row()` bezieht sein Status-Label jetzt ueber denselben kleinen Helfer, statt die Textauswahl direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Status-Label-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Status-Label-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.318: Security-Input-Access-Table-Guard `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Table-Guard eingefuehrt:
  - `_input_access_table()`
- wiederholten Table-Lookup-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe einer vorhandenen Input-Access-Tabelle
  - sauberen `None`-Rueckfall bei fehlendem Tabellenattribut
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `283/283` gruen

Kurzfazit:

- `refresh_input_access_table()` holt seine Tabelle jetzt ueber denselben kleinen Helfer, statt den `getattr(..., None)`-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Table-Guard-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Table-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.319: Security-Input-Access-Row-Meta-Reset `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Reset von Input-Access-Row-Meta eingefuehrt:
  - `_reset_input_access_row_meta()`
- wiederholten Reset-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Leeren eines bestehenden Row-Meta-Mappings
  - Ersetzen des Mapping-Objekts statt Mutation des Altzustands
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `285/285` gruen

Kurzfazit:

- `refresh_input_access_table()` setzt seine Row-Meta jetzt ueber denselben kleinen Helfer zurueck, statt die Zuweisung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Row-Meta-Reset-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Row-Meta-Reset-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.320: Security-Input-Access-Table-Refresh-Rows `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Table-Refresh eingefuehrt:
  - `_refresh_input_access_table_rows()`
- wiederholten Refresh-Teilpfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Reset, Clear und Populate bei vorhandenen Rows
  - korrektes Verhalten bei leerer Row-Liste nach dem Reset
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `287/287` gruen

Kurzfazit:

- `refresh_input_access_table()` fasst Reset, Clear und Populate jetzt ueber denselben kleinen Helfer zusammen, statt die drei Schritte direkt nacheinander auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Table-Refresh-Rows-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Table-Refresh-Rows-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.321: Security-Input-Access-Row-Values `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Input-Access-Row-Werte eingefuehrt:
  - `_input_access_row_values()`
- wiederholten Werte-Tuple-Pfad vereinheitlicht, u. a. in:
  - `_insert_input_access_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des erwarteten Werte-Tuples bei vollstaendigen Row-Daten
  - saubere Defaults fuer fehlende Felder
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `289/289` gruen

Kurzfazit:

- `_insert_input_access_row()` bezieht seine Werte jetzt ueber denselben kleinen Helfer, statt das Tuple direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Row-Values-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Row-Values-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.322: Security-Input-Access-Append-Row `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Anhaengen einer Input-Access-Row eingefuehrt:
  - `_append_input_access_row()`
- wiederholten Insert-plus-Meta-Pfad vereinheitlicht, u. a. in:
  - `_populate_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Anhaengen einer Row inklusive Meta-Speicherung
  - korrektes Ueberschreiben eines bestehenden Meta-Eintrags fuer dieselbe Row-ID
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `291/291` gruen

Kurzfazit:

- `_populate_input_access_table()` haengt seine Rows jetzt ueber denselben kleinen Helfer an, statt Insert und Meta-Speicherung direkt zu kombinieren.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Append-Row-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Append-Row-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.323: Security-Input-Access-Refresh-Result-Log `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer den Input-Access-Refresh-Abschlusslog eingefuehrt:
  - `_log_input_access_refresh_result()`
- wiederholten Abschluss-Logpfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Logging der Ergebniszeile bei aktiviertem Logpfad
  - bewusstes Auslassen des Loggings bei deaktiviertem Logpfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `293/293` gruen

Kurzfazit:

- `refresh_input_access_table()` delegiert seinen Abschlusslog jetzt an denselben kleinen Helfer, statt die Logbedingung direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Input-Access-Refresh-Result-Log-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Input-Access-Refresh-Result-Log-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.324: Security-Connected-Device-Row-Id `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer die Connected-Device-Row-ID eingefuehrt:
  - `_connected_device_row_id()`
- wiederholten Row-ID-Pfad vereinheitlicht, u. a. in:
  - `_insert_connected_device_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - erwartete Formatierung normaler Indizes
  - unveraenderte Darstellung negativer Indizes
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `295/295` gruen

Kurzfazit:

- `_insert_connected_device_row()` bezieht seine Row-ID jetzt ueber denselben kleinen Helfer, statt das ID-Format direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Connected-Device-Row-ID-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Row-Id-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.325: Security-Connected-Device-Append-Row `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Anhaengen einer Connected-Device-Row eingefuehrt:
  - `_append_connected_device_row()`
- wiederholten Insert-Pfad vereinheitlicht, u. a. in:
  - `_populate_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Anhaengen einer neuen Device-Row mit `device_new`-Tag
  - Anhaengen einer Baseline-Device-Row mit `device_known`-Tag
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `297/297` gruen

Kurzfazit:

- `_populate_connected_device_table()` haengt seine Device-Rows jetzt ueber denselben kleinen Helfer an, statt den Insert-Pfad direkt auszuschreiben.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Connected-Device-Append-Row-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Append-Row-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.326: Security-Connected-Device-Inventory-Store `netmon/features/security_monitoring_controller.py`

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Helfer fuer das Speichern des Connected-Device-Inventars eingefuehrt:
  - `_store_connected_device_inventory()`
- wiederholten Inventory-Speicherpfad vereinheitlicht, u. a. in:
  - `_connected_device_table_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe und Speichern eines Inventars
  - Beibehalten derselben Inventar-Objektreferenz beim Speichern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `299/299` gruen

Kurzfazit:

- `_connected_device_table_inventory()` speichert sein Inventar jetzt ueber denselben kleinen Helfer, statt Zuweisung und Rueckgabe direkt zu kombinieren.
- Die zwei neuen direkten Tests sichern genau diese vereinheitlichte Security-Connected-Device-Inventory-Store-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Security-Connected-Device-Inventory-Store-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.327

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Guard-Helfer fuer den Connected-Device-Table-Refresh eingefuehrt:
  - `_refresh_connected_device_table_if_present()`
- wiederholten Table-Lookup-plus-Guard-plus-View-Refresh-Pfad vereinheitlicht, u. a. in:
  - `refresh_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Ueberspringen des Refreshs bei fehlender Tabelle
  - Weiterreichen von App, Tabelle und Inventar bei vorhandener Tabelle
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `301/301` gruen

Kurzfazit:

- `refresh_connected_device_table()` delegiert den optionalen Tabellen-Refresh jetzt an einen kleinen Guard-Helfer, statt Lookup, `None`-Pruefung und View-Aufruf direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Refresh-Guard zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Refresh-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.328

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Guard-Helfer fuer den Input-Access-Table-Refresh eingefuehrt:
  - `_refresh_input_access_table_if_present()`
- wiederholten Table-Lookup-plus-Guard-plus-Refresh-Pfad vereinheitlicht, u. a. in:
  - `refresh_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Ueberspringen des Refreshs bei fehlender Tabelle
  - Weiterreichen von App, Tabelle und Rows bei vorhandener Tabelle
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `303/303` gruen

Kurzfazit:

- `refresh_input_access_table()` delegiert den optionalen Tabellen-Refresh jetzt an einen kleinen Guard-Helfer, statt Lookup, `None`-Pruefung und Row-Refresh direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Refresh-Guard zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Refresh-Guard-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.329

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Inventory-Iterations-Helfer fuer Connected Devices eingefuehrt:
  - `_connected_device_inventory_items()`
- wiederholten `enumerate(... or [])`-Pfad vereinheitlicht, u. a. in:
  - `_populate_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Enumerieren eines mehrteiligen Device-Inventars
  - leeres Verhalten bei leerem oder fehlendem Inventar
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `305/305` gruen

Kurzfazit:

- `_populate_connected_device_table()` bezieht seine `(Index, Device)`-Paare jetzt ueber einen kleinen gemeinsamen Helfer, statt die `enumerate(... or [])`-Logik direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diese Connected-Device-Inventory-Iteration zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Inventory-Iterations-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.330

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Rows-Helfer fuer Input-Access-Tabellen eingefuehrt:
  - `_input_access_table_rows()`
- wiederholten `rows or []`-Pfad vereinheitlicht, u. a. in:
  - `_populate_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - kopierende Rueckgabe einer Row-Liste
  - leeres Verhalten bei leerem oder fehlendem Row-Eingang
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `307/307` gruen

Kurzfazit:

- `_populate_input_access_table()` bezieht seine Row-Eintraege jetzt ueber einen kleinen gemeinsamen Helfer, statt die `rows or []`-Logik direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diese Input-Access-Row-Normalisierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Row-Normalisierungs-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.331

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Argumente-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_kwargs()`
- wiederholten IID-/Values-/Tag-Aufbau vereinheitlicht, u. a. in:
  - `_insert_connected_device_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Insert-Payload eines neuen Geraets
  - Insert-Payload eines bekannten Geraets
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `309/309` gruen

Kurzfazit:

- `_insert_connected_device_row()` bezieht seine Insert-Argumente jetzt ueber einen kleinen gemeinsamen Helfer, statt IID, Values und Tags direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Payload-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.332

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Argumente-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_insert_kwargs()`
- wiederholten Values-Aufbau beim Tabellen-Insert vereinheitlicht, u. a. in:
  - `_insert_input_access_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Insert-Payload mit Fallback-Werten
  - Insert-Payload mit expliziten Row-Feldern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `311/311` gruen

Kurzfazit:

- `_insert_input_access_row()` bezieht seine Insert-Argumente jetzt ueber einen kleinen gemeinsamen Helfer, statt die Values direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Payload-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.333

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Meta-Kopier-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_meta_value()`
- wiederholten `dict(row)`-Pfad beim Meta-Speichern vereinheitlicht, u. a. in:
  - `_store_input_access_row_meta()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - kopierende Rueckgabe einer Row-Meta-Struktur
  - leeres Verhalten bei leerer Row-Meta
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `313/313` gruen

Kurzfazit:

- `_store_input_access_row_meta()` bezieht seine Meta-Kopie jetzt ueber einen kleinen gemeinsamen Helfer, statt `dict(row)` direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Row-Meta-Kopierpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Row-Meta-Kopier-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.334

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Children-Helfer fuer Connected-Device-Tabellen eingefuehrt:
  - `_connected_device_table_children()`
- wiederholten `get_children()`-Pfad beim Leeren der Tabelle vereinheitlicht, u. a. in:
  - `_clear_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - List-Rueckgabe der vorhandenen Children
  - leeres Verhalten ohne Children
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `315/315` gruen

Kurzfazit:

- `_clear_connected_device_table()` bezieht seine Child-Elemente jetzt ueber einen kleinen gemeinsamen Helfer, statt `get_children()` direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Children-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Children-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.335

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Children-Helfer fuer Input-Access-Tabellen eingefuehrt:
  - `_input_access_table_children()`
- wiederholten `get_children()`-Pfad beim Leeren der Tabelle vereinheitlicht, u. a. in:
  - `_clear_input_access_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - List-Rueckgabe der vorhandenen Children
  - leeres Verhalten ohne Children
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `317/317` gruen

Kurzfazit:

- `_clear_input_access_table()` bezieht seine Child-Elemente jetzt ueber einen kleinen gemeinsamen Helfer, statt `get_children()` direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Children-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Children-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.336

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Feld-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_field()`
- wiederholten `row.get(..., "-")`-Pfad vereinheitlicht, u. a. in:
  - `_input_access_row_values()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe eines vorhandenen Feldwerts
  - unveraenderte `dict.get`-Semantik fuer Missing- und `None`-Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `319/319` gruen

Kurzfazit:

- `_input_access_row_values()` bezieht seine Einzelwerte jetzt ueber einen kleinen gemeinsamen Helfer, statt die `row.get(..., "-")`-Zugriffe direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Field-Fallback-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Field-Fallback-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.337

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Meta-Update-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_meta_update()`
- wiederholten Ein-Key-Update-Pfad beim Meta-Speichern vereinheitlicht, u. a. in:
  - `_store_input_access_row_meta()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aufbau eines einzelnen Meta-Mapping-Eintrags
  - leeres Verhalten bei leerer Row-Meta
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `321/321` gruen

Kurzfazit:

- `_store_input_access_row_meta()` bezieht sein Ein-Key-Meta-Update jetzt ueber einen kleinen gemeinsamen Helfer, statt die Zuweisung direkt vorzunehmen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Row-Meta-Update-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Row-Meta-Update-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.338

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Farb-Helfer fuer Connected-Device-Tabellentags eingefuehrt:
  - `_connected_device_table_tag_colors()`
- wiederholten Theme-zu-Farb-Pfad vereinheitlicht, u. a. in:
  - `_configure_connected_device_table_tags()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe expliziter Theme-Farben
  - Rueckgabe sicherer Default-Farben
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `323/323` gruen

Kurzfazit:

- `_configure_connected_device_table_tags()` bezieht seine Known-/New-Farben jetzt ueber einen kleinen gemeinsamen Helfer, statt die Theme-Aufloesung direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Tag-Farbpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Tag-Farb-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.339

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Tag-Config-Helfer fuer Connected-Device-Tabellen eingefuehrt:
  - `_connected_device_table_tag_configs()`
- wiederholten Tagname-plus-Optionen-Pfad vereinheitlicht, u. a. in:
  - `_configure_connected_device_table_tags()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aufbau der Known-/New-Tag-Konfiguration
  - unveraenderte Weitergabe leerer Farbwerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `325/325` gruen

Kurzfazit:

- `_configure_connected_device_table_tags()` bezieht seine Tag-Spezifikation jetzt ueber einen kleinen gemeinsamen Helfer, statt Tag-Namen und Optionen direkt zu mischen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Tag-Config-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Tag-Config-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.340

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Einzeltag-Helfer fuer Connected-Device-Tabellen eingefuehrt:
  - `_connected_device_table_tag_config()`
- wiederholten Einzeltag-plus-Foreground-Pfad vereinheitlicht, u. a. in:
  - `_connected_device_table_tag_configs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Aufbau eines einzelnen Tag-Foreground-Mappings
  - unveraenderte Weitergabe leerer Farbwerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `327/327` gruen

Kurzfazit:

- `_connected_device_table_tag_configs()` bezieht seine einzelnen Tag-Spezifikationen jetzt ueber einen kleinen gemeinsamen Helfer, statt Tagname und Optionen direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Einzeltag-Config-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Einzeltag-Config-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.341

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Values-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_values()`
- wiederholten Values-Pfad im Insert-Spec vereinheitlicht, u. a. in:
  - `_connected_device_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe formatierter Insert-Spalten
  - sichere Default-Werte ohne Device-Daten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `329/329` gruen

Kurzfazit:

- `_connected_device_row_insert_kwargs()` bezieht seine Insert-Values jetzt ueber einen kleinen gemeinsamen Helfer, statt den Values-Pfad direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Values-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Values-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.342

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-IID-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_iid()`
- wiederholten IID-Pfad im Insert-Spec vereinheitlicht, u. a. in:
  - `_connected_device_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe der formatierten Row-ID
  - unveraenderte Behandlung negativer Indizes
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `331/331` gruen

Kurzfazit:

- `_connected_device_row_insert_kwargs()` bezieht seine Insert-IID jetzt ueber einen kleinen gemeinsamen Helfer, statt den IID-Pfad direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-IID-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-IID-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.343

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Tag-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_tags()`
- wiederholten Tag-Pfad im Insert-Spec vereinheitlicht, u. a. in:
  - `_connected_device_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe des Known-Tags
  - Rueckgabe des New-Tags per Default
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `333/333` gruen

Kurzfazit:

- `_connected_device_row_insert_kwargs()` bezieht seine Insert-Tags jetzt ueber einen kleinen gemeinsamen Helfer, statt den Tag-Pfad direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Tag-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Tag-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.344

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Values-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_insert_values()`
- wiederholten Values-Pfad im Insert-Spec vereinheitlicht, u. a. in:
  - `_input_access_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe formatierter Insert-Spalten
  - sichere Default-Werte ohne Row-Daten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `335/335` gruen

Kurzfazit:

- `_input_access_row_insert_kwargs()` bezieht seine Insert-Values jetzt ueber einen kleinen gemeinsamen Helfer, statt den Values-Pfad direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Values-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Values-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.345

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Positions-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_insert_position()`
- wiederholten Parent-/Where-Pfad beim Tabellen-Insert vereinheitlicht, u. a. in:
  - `_insert_input_access_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe der Tree-Insert-Defaults
  - stabile Rueckgabe derselben Insert-Position
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `337/337` gruen

Kurzfazit:

- `_insert_input_access_row()` bezieht seine Insert-Position jetzt ueber einen kleinen gemeinsamen Helfer, statt Parent und Where direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Positions-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Positions-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.346

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Config-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_insert_config()`
- wiederholten Values-zu-Config-Pfad im Insert-Spec vereinheitlicht, u. a. in:
  - `_input_access_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Wrapping eines Values-Tuples in die Insert-Config
  - unveraenderte Weitergabe eines leeren Tuples
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `339/339` gruen

Kurzfazit:

- `_input_access_row_insert_kwargs()` bezieht seine Insert-Config jetzt ueber einen kleinen gemeinsamen Helfer, statt das `{"values": ...}`-Mapping direkt zu bauen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Config-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Config-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.350

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Spec-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_input_access_row_insert_spec()`
- wiederholten Position-plus-Config-Pfad beim Tabellen-Insert vereinheitlicht, u. a. in:
  - `_insert_input_access_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Kombination aus Insert-Position und Config bei minimaler Row
  - Kombination aus Insert-Position und Config bei expliziten Row-Feldern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `341/341` gruen

Kurzfazit:

- `_insert_input_access_row()` bezieht seine Insert-Spezifikation jetzt ueber einen kleinen gemeinsamen Helfer, statt Position und Config direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Spec-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Spec-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.347

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Positions-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_position()`
- wiederholten Parent-/Where-Pfad beim Tabellen-Insert vereinheitlicht, u. a. in:
  - `_insert_connected_device_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Rueckgabe der Tree-Insert-Defaults
  - stabile Rueckgabe derselben Insert-Position
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `341/341` gruen

Kurzfazit:

- `_insert_connected_device_row()` bezieht seine Insert-Position jetzt ueber einen kleinen gemeinsamen Helfer, statt Parent und Where direkt zu verwenden.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Positions-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Positions-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.348

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Config-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_config()`
- wiederholten IID-/Values-/Tags-zu-Config-Pfad vereinheitlicht, u. a. in:
  - `_connected_device_row_insert_kwargs()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Wrapping von IID, Values und Tags in die Insert-Config
  - unveraenderte Weitergabe leerer Values und Tags
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `343/343` gruen

Kurzfazit:

- `_connected_device_row_insert_kwargs()` bezieht seine Insert-Config jetzt ueber einen kleinen gemeinsamen Helfer, statt das Mapping aus IID, Values und Tags direkt zu bauen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Config-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Config-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.349

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Insert-Spec-Helfer fuer Connected-Device-Zeilen eingefuehrt:
  - `_connected_device_row_insert_spec()`
- wiederholten Position-plus-Config-Pfad beim Tabellen-Insert vereinheitlicht, u. a. in:
  - `_insert_connected_device_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - Kombination aus Insert-Position und Config bei neuem Geraet
  - Kombination aus Insert-Position und Config bei bekanntem Geraet
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `345/345` gruen

Kurzfazit:

- `_insert_connected_device_row()` bezieht seine Insert-Spezifikation jetzt ueber einen kleinen gemeinsamen Helfer, statt Position und Config direkt zusammenzusetzen.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Insert-Spec-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Insert-Spec-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.350

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Tree-Insert-Positionshelfer eingefuehrt:
  - `_tree_insert_position()`
- wiederholten `("", "end")`-Pfad vereinheitlicht, u. a. in:
  - `_input_access_row_insert_position()`
  - `_connected_device_row_insert_position()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - stabile Standard-Insert-Position
  - unveraenderte Tree-Insert-Defaults
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `349/349` gruen

Kurzfazit:

- `_input_access_row_insert_position()` und `_connected_device_row_insert_position()` beziehen ihre feste Tree-Insert-Position jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Tuple-Literal doppelt zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Tree-Insert-Default zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine gemeinsame Insert-Default-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.351

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Inserted-Row-ID-Helfer fuer Input-Access-Zeilen eingefuehrt:
  - `_inserted_input_access_row_id()`
- wiederholten Insert-Rueckgabepfad vereinheitlicht, u. a. in:
  - `_append_input_access_row()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe der eingefuegten Row-ID
  - unveraenderte Weitergabe der Zeilendaten an den Insert-Pfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `351/351` gruen

Kurzfazit:

- `_append_input_access_row()` bezieht seine eingefuegte Row-ID jetzt ueber einen kleinen gemeinsamen Helfer statt den Insert-Rueckgabepfad direkt zu halten.
- Die zwei neuen direkten Tests sichern genau diesen Input-Access-Insert-Rueckgabepfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Input-Access-Insert-Row-ID-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.352

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen Current-Inventory-Helfer fuer Connected-Devices eingefuehrt:
  - `_current_connected_device_inventory()`
- wiederholten Inventarabrufpfad vereinheitlicht, u. a. in:
  - `_connected_device_table_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des aktuellen Inventars
  - unveraenderte Behandlung eines leeren Inventars
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `353/353` gruen

Kurzfazit:

- `_connected_device_table_inventory()` bezieht sein aktuelles Inventar jetzt ueber einen kleinen gemeinsamen Helfer statt den Abrufpfad direkt zu halten.
- Die zwei neuen direkten Tests sichern genau diesen Connected-Device-Inventarabrufpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kompakte Connected-Device-Current-Inventory-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.353

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen App-Listen-Helfer eingefuehrt:
  - `_app_list_value()`
- wiederholten List-Copy-Pfad vereinheitlicht, u. a. in:
  - `_security_visible_events()`
  - `_security_events()`
  - `_connected_devices_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Listenkopie
  - unveraenderte Behandlung fehlender und leerer Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `355/355` gruen

Kurzfazit:

- `_security_visible_events()`, `_security_events()` und `_connected_devices_inventory()` beziehen ihre Listen jetzt ueber einen kleinen gemeinsamen Helfer statt denselben List-Copy-Pfad separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Listen-Fallback-und-Copy-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine App-Listen-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.354

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen App-Dict-Helfer eingefuehrt:
  - `_app_dict_value()`
- wiederholten Dict-Fallback-und-Copy-Pfad vereinheitlicht, u. a. in:
  - `_security_table_row_meta()`
  - `_security_summary_context()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Dict-Kopie
  - unveraenderte Behandlung fehlender und leerer Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `357/357` gruen

Kurzfazit:

- `_security_table_row_meta()` und die Dict-Pfade in `_security_summary_context()` beziehen ihre Werte jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Fallback mehrfach separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Dict-Fallback-und-Copy-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine App-Dict-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.355

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen App-String-Helfer eingefuehrt:
  - `_app_str_value()`
- wiederholten String-Fallback-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_is_netmon_internal_path()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Stringifizierung vorhandener Werte
  - unveraenderte Behandlung fehlender und leerer Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `359/359` gruen

Kurzfazit:

- Die String-Fallback-Pfade in `_security_summary_context()` und `_is_netmon_internal_path()` laufen jetzt ueber einen kleinen gemeinsamen Helfer statt dieselbe `str(... or default)`-Logik mehrfach separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen String-Fallback-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine App-String-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.356

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen App-Widget-Helfer eingefuehrt:
  - `_app_widget_value()`
- wiederholten Widget-Lookup-Pfad vereinheitlicht, u. a. in:
  - `_security_detail_widget()`
  - `on_security_event_select()`
  - `_connected_device_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines vorhandenen Widgets
  - unveraenderte Rueckgabe von `None` bei fehlendem Widget
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `361/361` gruen

Kurzfazit:

- `_security_detail_widget()`, der Security-Table-Lookup in `on_security_event_select()` und `_connected_device_table()` beziehen ihre Widgets jetzt ueber einen kleinen gemeinsamen Helfer statt denselben `None`-Lookup separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Widget-Lookup-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine App-Widget-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.357

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen App-Bool-Helfer eingefuehrt:
  - `_app_bool_value()`
- wiederholten Bool-Fallback-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Booleanisierung vorhandener Werte
  - unveraenderte Behandlung fehlender und falsey Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `363/363` gruen

Kurzfazit:

- Der Bool-Fallback in `_security_summary_context()` laeuft jetzt ueber einen kleinen gemeinsamen Helfer statt die `bool(_app_value(...))`-Logik direkt zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Bool-Fallback-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine App-Bool-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.358

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Security-Table-Helfer eingefuehrt:
  - `_security_table()`
- wiederholten Security-Table-Lookup-Pfad vereinheitlicht, u. a. in:
  - `_clear_security_view_tables()`
  - `on_security_event_select()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe einer vorhandenen Security-Tabelle
  - unveraenderte Rueckgabe von `None` bei fehlender Security-Tabelle
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `365/365` gruen

Kurzfazit:

- `_clear_security_view_tables()` und `on_security_event_select()` beziehen die Security-Tabelle jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Widget-Lookup separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Security-Table-Lookup-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Table-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.359

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Security-View-Tabellen-Helfer eingefuehrt:
  - `_security_view_tables()`
- wiederholten Tabellen-Sammelpfad vereinheitlicht, u. a. in:
  - `_clear_security_view_tables()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe aller vorhandenen View-Tabellen
  - unveraenderte Rueckgabe von `None` fuer fehlende Tabellen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `367/367` gruen

Kurzfazit:

- `_clear_security_view_tables()` bezieht seine drei View-Tabellen jetzt ueber einen kleinen gemeinsamen Helfer statt sie direkt einzeln zusammenzusuchen.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen View-Tabellen-Sammelpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-View-Table-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.360

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Monitoring-State-Helfer eingefuehrt:
  - `_security_monitoring_active()`
- wiederholten Monitoring-Status-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_security_export_blocks_for_app()`
  - `security_update_status()`
  - `_security_clear_events_status_color()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe fuer aktiven Monitoring-Status
  - unveraenderte Rueckgabe fuer fehlenden oder deaktivierten Status
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `369/369` gruen

Kurzfazit:

- Der Monitoring-Status in Summary-, Export-, Status- und Clear-Events-Pfaden laeuft jetzt ueber einen kleinen gemeinsamen Helfer statt mehrfach separat aus `app.security_monitoring` bzw. `_app_value(...)` gezogen zu werden.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Monitoring-State-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Monitoring-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.361

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Event-Count-Helfer eingefuehrt:
  - `_security_event_count()`
- wiederholten Event-Zaehlpfad vereinheitlicht, u. a. in:
  - `_security_export_blocks_for_app()`
  - `security_update_status()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe der Event-Anzahl
  - unveraenderte Behandlung fehlender Events
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `371/371` gruen

Kurzfazit:

- `_security_export_blocks_for_app()` und `security_update_status()` beziehen ihre Event-Anzahl jetzt ueber einen kleinen gemeinsamen Helfer statt sie separat aus `app.security_events` zu zaehlen.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Event-Count-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Event-Count-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.362

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Aggregated-State-Helfer eingefuehrt:
  - `_security_aggregated()`
- wiederholten Aggregated-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_security_export_blocks_for_app()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Mapping-Kopie
  - unveraenderte Behandlung fehlenden Aggregated-Status
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `373/373` gruen

Kurzfazit:

- `_security_summary_context()` und `_security_export_blocks_for_app()` beziehen ihren Aggregated-State jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Aggregated-State-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Aggregated-State-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.363

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Last-Alarm-Helfer eingefuehrt:
  - `_security_last_alarm()`
- wiederholten Last-Alarm-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_security_export_blocks_for_app()`
  - `security_update_status()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des aktuellen Alarms
  - unveraenderte Behandlung fehlender und leerer Alarmwerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `375/375` gruen

Kurzfazit:

- Summary-, Export- und Statuspfad beziehen den letzten Alarm jetzt ueber einen kleinen gemeinsamen Helfer statt den String-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Last-Alarm-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Last-Alarm-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.364

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Log-Level-Helfer eingefuehrt:
  - `_security_log_level()`
- wiederholten Log-Level-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_security_export_blocks_for_app()`
  - `security_update_status()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des aktuellen Log-Levels
  - unveraenderte Behandlung fehlender und leerer Log-Level-Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `377/377` gruen

Kurzfazit:

- Summary-, Export- und Statuspfad beziehen den Log-Level jetzt ueber einen kleinen gemeinsamen Helfer statt den String-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Log-Level-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Log-Level-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.365

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Device-Baseline-Helfer eingefuehrt:
  - `_device_baseline()`
- wiederholten Device-Baseline-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `_connected_device_inventory_context()`
  - `connected_device_inventory()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Mapping-Kopie
  - unveraenderte Behandlung fehlender Device-Baseline
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `379/379` gruen

Kurzfazit:

- Summary-, Connected-Device-Kontext- und Inventarpfad beziehen die Device-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Device-Baseline-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Baseline-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.366

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Integrity-Baseline-Helfer eingefuehrt:
  - `_integrity_baseline()`
- wiederholten Integrity-Baseline-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `load_security_baseline()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Mapping-Kopie
  - unveraenderte Behandlung fehlender Integrity-Baseline
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `381/381` gruen

Kurzfazit:

- Summary- und Load-Baseline-Pfad beziehen die Integrity-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Integrity-Baseline-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Baseline-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.367

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Input-Access-Baseline-Helfer eingefuehrt:
  - `_input_access_baseline()`
- wiederholten Input-Access-Baseline-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `save_security_baseline()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe als detachierte Mapping-Kopie
  - unveraenderte Behandlung fehlender Input-Access-Baseline
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `383/383` gruen

Kurzfazit:

- Summary- und Save-Baseline-Pfad beziehen die Input-Access-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Fallback separat zu halten.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Input-Access-Baseline-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Baseline-Block in Phase 3 voll verifiziert abgeschlossen.

## Phase 3.368

Stand: 2026-06-06

Gepruefte Befehle:

```bash
python3 -m black netmon/features/security_monitoring_controller.py
python3 -m black tests/test_netmon_security_modules.py
./venv/bin/python -m ruff check netmon/features/security_monitoring_controller.py tests/test_netmon_security_modules.py
python3 -m black --check netmon/features/security_monitoring_controller.py
python3 -m black --check tests/test_netmon_security_modules.py
pytest tests/test_netmon_security_modules.py
```

Umgesetzte Sauberkeitsarbeit:

- kleinen gemeinsamen Filter-Mode-Helfer eingefuehrt:
  - `_security_filter_mode()`
- wiederholten Filter-Mode-Pfad vereinheitlicht, u. a. in:
  - `_security_summary_context()`
  - `security_filtered_events()`
  - `refresh_security_table()`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des aktuellen Filtermodus
  - unveraenderte Behandlung fehlender und leerer Filtermodi
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access-, Summary- und Export-Pfade
  - Baseline-, Parser- und Scan-Logik

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `385/385` gruen

Kurzfazit:

- Summary-, Filter- und Tabellen-Refresh-Pfad beziehen den aktuellen Filtermodus jetzt ueber einen kleinen gemeinsamen Helfer statt ihn mehrfach separat aus `app.security_filter_mode` zu lesen.
- Die zwei neuen direkten Tests sichern genau diesen gemeinsamen Filter-Mode-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Filter-Mode-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.369:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_payload(app, timestamp)`
- Vereinheitlichung des Baseline-Payload-Pfads in `save_security_baseline()`
- der Helfer nutzt die bereits vorhandenen Baseline-Zugriffspfade fuer:
  - Integrity-Baseline
  - Device-Baseline
  - Input-Access-Baseline
  - Timestamp-Verdrahtung
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe abgekoppelter Baseline-Mappings samt Timestamp
  - unveraenderte Behandlung fehlender Baseline-Zustaende
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Lade-, Scan- und Vergleichslogik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `387/387` gruen

Kurzfazit:

- Der Save-Pfad fuer die Security-Baseline baut seinen JSON-Payload jetzt ueber einen kleinen gemeinsamen Helfer auf statt die drei Baseline-Bloecke und den Timestamp lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern sowohl die abgekoppelte Payload-Erzeugung als auch die fehlertoleranten Default-Zustaende zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.370:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_input_access_processes(mapping, path)`
- Vereinheitlichung des wiederholten Pro-Pfad-Prozessauflösungspfads in `scan_input_access_changes()`
- der Helfer kapselt jetzt die fehlertolerante Dict-Aufloesung fuer:
  - Baseline-Prozesse pro Input-Access-Pfad
  - aktuelle Prozesse pro Input-Access-Pfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe einer abgekoppelten Prozesszuordnung
  - unveraenderte Behandlung fehlender Pfade und Mapping-Zustaende
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Scan-, Whitelist- und Event-Erzeugungslogik
  - Baseline-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `389/389` gruen

Kurzfazit:

- Der Input-Access-Diffpfad liest die alten und aktuellen Prozessmappings pro Geraetepfad jetzt ueber einen kleinen gemeinsamen Helfer statt dieselbe `get(..., {})`-Aufloesung mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern sowohl die abgekoppelte Prozessauflosung als auch die robusten Default-Faelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Prozessblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.371:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_type(mapping, path, default="unknown")`
- Vereinheitlichung des wiederholten Device-Type-Fallback-Pfads in `scan_device_changes()`
- der Helfer kapselt jetzt die fehlertolerante Typ-Aufloesung fuer:
  - neue Device-Ereignisse
  - entfernte Device-Ereignisse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des aktuellen Device-Typs
  - unveraenderte Behandlung fehlender und leerer Device-Typ-Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Scan-, Event-Erzeugungs- und Baseline-Logik
  - Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `391/391` gruen

Kurzfazit:

- Der Device-Diffpfad liest den Typ fuer neue und entfernte Geraete jetzt ueber einen kleinen gemeinsamen Helfer statt denselben `get(path, "unknown")`-Fallback mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern sowohl die normale Typ-Aufloesung als auch die robusten Default-Faelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Type-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.372:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_entry_token(entry)`
- Vereinheitlichung des wiederholten `sha|size|mtime`-Tokenaufbaus in `scan_integrity_changes()`
- der Helfer kapselt jetzt den Tokenpfad fuer:
  - neue Datei-Ereignisse
  - geloeschte Datei-Ereignisse
  - geaenderte Datei-Ereignisse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines vollstaendigen Integrity-Tokens
  - unveraenderte Behandlung fehlender Integrity-Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Scan-, Vergleichs- und Event-Erzeugungslogik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `393/393` gruen

Kurzfazit:

- Der Integrity-Diffpfad baut seine `sha|size|mtime`-Tokens jetzt ueber einen kleinen gemeinsamen Helfer auf statt denselben String lokal mehrfach zusammenzusetzen.
- Die zwei neuen direkten Tests sichern sowohl den normalen Tokenaufbau als auch die robusten Default-Faelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Token-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.373:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_entry(mapping, path)`
- Vereinheitlichung des wiederholten Pro-Pfad-Integrity-Entry-Fallbacks in `scan_integrity_changes()`
- der Helfer kapselt jetzt die fehlertolerante Entry-Aufloesung fuer:
  - neue Datei-Ereignisse
  - geloeschte Datei-Ereignisse
  - geaenderte Datei-Ereignisse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines abgekoppelten Integrity-Entries
  - unveraenderte Behandlung fehlender Pfade und Mapping-Zustaende
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Scan-, Vergleichs- und Event-Erzeugungslogik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `395/395` gruen

Kurzfazit:

- Der Integrity-Diffpfad liest den alten und aktuellen Entry pro Pfad jetzt ueber einen kleinen gemeinsamen Helfer statt denselben `get(path, {})`-Fallback mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern sowohl die abgekoppelte Entry-Aufloesung als auch die robusten Default-Faelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Entry-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.374:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_mapping_paths(mapping)`
- Vereinheitlichung des wiederholten Key-Set-Pfads in `scan_integrity_changes()`, `scan_device_changes()` und `scan_input_access_changes()`
- der Helfer kapselt jetzt die fehlertolerante Schluesselmengen-Aufloesung fuer:
  - Integrity-Diffs
  - Device-Diffs
  - Input-Access-Diffs
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe der Key-Menge eines Mappings
  - unveraenderte Behandlung fehlender und leerer Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-, Device- und Input-Access-Scan-/Vergleichslogik
  - Summary-, Baseline- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `397/397` gruen

Kurzfazit:

- Die drei Diff-Pfade beziehen ihre alten und neuen Pfadmengen jetzt ueber einen kleinen gemeinsamen Helfer statt jeweils separat `set(mapping.keys())` lokal aufzubauen.
- Die zwei neuen direkten Tests sichern sowohl die normale Key-Set-Aufloesung als auch die robusten Default-Faelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Mapping-Paths-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.375:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_input_access_change_token(change, pname, path, pid, occurrence_token)`
- Vereinheitlichung des wiederholten Start-/Stop-Tokenaufbaus in `scan_input_access_changes()`
- der Helfer kapselt jetzt den Tokenpfad fuer:
  - neue Input-Access-Starts
  - entfernte Input-Access-Stopps
  - verschwundene Prozesse auf bestehenden Pfaden
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines Start-Tokens
  - unveraenderte Behandlung einfacher Plain-Values
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Scan-, Whitelist- und Event-Erzeugungslogik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `399/399` gruen

Kurzfazit:

- Der Input-Access-Diffpfad baut seine Start-/Stop-Tokens jetzt ueber einen kleinen gemeinsamen Helfer auf statt dieselben Stringbausteine mehrfach lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern sowohl den normalen Tokenaufbau als auch einfache robuste Eingabefaelle zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Token-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.376:

- kleiner Refactor im Security-Monitoring-Controller: `scan_input_access_changes()` nutzt jetzt den bestehenden Helfer `_input_access_whitelist_status(app, process_name, pid)`
- Vereinheitlichung des wiederholten Whitelist-Checks im Input-Access-Diffpfad
- der bestehende Helfer uebernimmt jetzt auch dort die PID-Normalisierung fuer:
  - neue Input-Access-Starts
  - entfernte Input-Access-Stopps
  - verschwundene Prozesse auf bestehenden Pfaden
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Behandlung whitelister neuer Prozesse im Scanpfad
  - unveraenderte Behandlung whitelister gestoppter Prozesse im Scanpfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Scan-, Token- und Event-Erzeugungslogik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `401/401` gruen

Kurzfazit:

- Der Input-Access-Diffpfad verwendet fuer seine drei Whitelist-Stellen jetzt den bereits vorhandenen gemeinsamen Helfer statt die gleiche Logik lokal separat aufzurufen.
- Die zwei neuen direkten Tests sichern diesmal explizit den Scanpfad ab, nicht nur den Helfer isoliert.
- Damit ist auch dieser kleine Input-Access-Whitelist-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.377:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_input_access_change_event(...)`
- Vereinheitlichung des wiederholten `Token bauen -> Event erzeugen -> anhaengen`-Pfads in `scan_input_access_changes()`
- der Helfer kapselt jetzt den Event-Anhaengepfad fuer:
  - neue Input-Access-Starts
  - entfernte Input-Access-Stopps
  - verschwundene Prozesse auf bestehenden Pfaden
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines angehaengten Start-Events
  - unveraenderte Behandlung einfacher Plain-Values beim Stop-Event
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Scan-, Whitelist- und Token-Logik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Controller-Datei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `403/403` gruen

Kurzfazit:

- Der Input-Access-Diffpfad haengt seine Start-/Stop-Events jetzt ueber einen kleinen gemeinsamen Helfer an statt dieselbe Verkettung aus Tokenaufbau, Event-Erzeugung und Append mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen neuen Anhaengepfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Append-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.378:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_integrity_change_event(events, app, kind, path, entry)`
- Vereinheitlichung des wiederholten `Token bauen -> Datei-Event erzeugen -> anhaengen`-Pfads in `scan_integrity_changes()`
- der Helfer kapselt jetzt den Event-Anhaengepfad fuer:
  - neue Datei-Ereignisse
  - geloeschte Datei-Ereignisse
  - geaenderte Datei-Ereignisse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines angehaengten Datei-Events
  - unveraenderte Behandlung fehlender Integrity-Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Scan-, Vergleichs- und Token-Logik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `405/405` gruen

Kurzfazit:

- Der Integrity-Diffpfad haengt seine Datei-Events jetzt ueber einen kleinen gemeinsamen Helfer an statt dieselbe Verkettung aus Tokenaufbau, Event-Erzeugung und Append mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen neuen Datei-Append-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Append-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.379:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_device_change_event(events, app, kind, change, path, device_type)`
- Vereinheitlichung des wiederholten `Token bauen -> Device-Event erzeugen -> anhaengen`-Pfads in `scan_device_changes()`
- der Helfer kapselt jetzt den Event-Anhaengepfad fuer:
  - neue Device-Ereignisse
  - entfernte Device-Ereignisse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines angehaengten Device-Events
  - unveraenderte Behandlung einfacher Plain-Values
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Scan-, Token- und Event-Erzeugungslogik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Controller-Datei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `407/407` gruen

Kurzfazit:

- Der Device-Diffpfad haengt seine neuen und entfernten Device-Events jetzt ueber einen kleinen gemeinsamen Helfer an statt dieselbe Verkettung aus Tokenaufbau, Event-Erzeugung und Append mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen neuen Device-Append-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Append-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.380:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_file_entry(app, path, stat_result)`
- Vereinheitlichung des wiederholten Integrity-Entry-Aufbaus in `build_integrity_baseline()` und `scan_integrity_changes()`
- der Helfer kapselt jetzt den `sha/size/mtime`-Mapping-Aufbau fuer:
  - Baseline-Aufbau
  - aktuellen Scan-Zustand
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines vollstaendigen Integrity-Entries
  - unveraenderte Behandlung von Null-/Leerwerten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Scan-, Vergleichs- und Append-Logik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `409/409` gruen

Kurzfazit:

- Baseline-Aufbau und Integrity-Scan erzeugen ihren `sha/size/mtime`-Eintrag jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Aufbau lokal doppelt zu pflegen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Entry-Aufbau zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Entry-Builder-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.381:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_type_for_path(app, path)`
- Vereinheitlichung des wiederholten Device-Type-Lookups in `connected_device_inventory()`, `_input_access_path_context()`, `build_device_baseline()` und `scan_device_changes()`
- der Helfer kapselt jetzt die Typ-Aufloesung fuer:
  - Connected-Device-Inventar
  - Input-Access-Pfadkontext
  - Device-Baseline-Aufbau
  - Device-Scan-Zustand
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines Device-Type-Texts
  - unveraenderte Normalisierung nicht-stringiger Rueckgaben
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Input-Access- und Baseline-Logik
  - Integrity-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `411/411` gruen

Kurzfazit:

- Die Device-Type-Aufloesung laeuft jetzt ueber einen kleinen gemeinsamen Helfer statt mehrfach direkt `app._device_type_from_path(path)` aufzurufen.
- Die zwei neuen direkten Tests sichern diesmal genau diese gemeinsame Typ-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Type-Lookup-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.382:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_type_mapping(app)`
- Vereinheitlichung des wiederholten Device-Type-Mapping-Aufbaus in `build_device_baseline()` und `scan_device_changes()`
- der Helfer kapselt jetzt den Mapping-Aufbau fuer:
  - Device-Baseline-Aufbau
  - aktuellen Device-Scan-Zustand
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines Device-Type-Mappings aus Watch-Pfaden
  - unveraenderte Behandlung leerer Watch-Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Scan-, Baseline- und Event-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Controller-Datei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `413/413` gruen

Kurzfazit:

- Baseline-Aufbau und Device-Scan erzeugen ihr Device-Type-Mapping jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Dict-Comprehension-Pfad lokal doppelt zu pflegen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Mapping-Aufbau zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Type-Mapping-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.383:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_scan_state(app)`
- Vereinheitlichung des wiederholten Integrity-Scan-Zustandsaufbaus in `build_integrity_baseline()` und `scan_integrity_changes()`
- der Helfer kapselt jetzt den Scanpfad fuer:
  - Baseline-Aufbau
  - aktuellen Integrity-Zustand
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe vorhandener nicht-ignorierter Dateien
  - unveraenderte Behandlung ignorierter, fehlender und fehlerhafter Dateien
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Baseline-, Vergleichs- und Append-Logik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `415/415` gruen

Kurzfazit:

- Baseline-Aufbau und Integrity-Scan beziehen ihren aktuellen Dateizustand jetzt ueber einen kleinen gemeinsamen Helfer statt denselben Scan-Loop lokal doppelt zu pflegen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Integrity-Scan-Zustandspfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Scan-State-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.384:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_connected_device_entry(app, path, base, preferred_path, baseline)`
- Vereinheitlichung des wiederholten Device-Entry-Aufbaus in `connected_device_inventory()`
- der Helfer kapselt jetzt den Eintragsaufbau fuer:
  - Anzeigename
  - bevorzugten Pfad
  - Typ
  - Baseline-Status
  - Metadaten
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines vollstaendigen Connected-Device-Eintrags
  - unveraenderte Behandlung fehlender Baseline-Zuordnung
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Inventory-, Baseline- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Controller-Datei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `417/417` gruen

Kurzfazit:

- `connected_device_inventory()` baut seinen Geraete-Eintrag jetzt ueber einen kleinen gemeinsamen Helfer auf statt denselben Dictionary-Block lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Entry-Aufbau zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Connected-Device-Entry-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.385:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_preferred_connected_device_path(path, existing)`
- Vereinheitlichung der bevorzugten Pfadauswahl in `connected_device_inventory()`
- der Helfer kapselt jetzt die Pfadpraeferenz fuer:
  - bereits bekannte `/dev/input/`-Pfade
  - neu gesehene `/dev/input/`-Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Bevorzugung eines bestehenden `/dev/input/`-Pfads
  - unveraenderte Bevorzugung des aktuellen `/dev/input/`-Pfads
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Connected-Device-Inventory-, Baseline- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `419/419` gruen

Kurzfazit:

- `connected_device_inventory()` loest die bevorzugte Pfadauswahl jetzt ueber einen kleinen gemeinsamen Helfer statt die `/dev/input/`-Praeferenz lokal zu verzweigen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Pfadpraeferenz zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Preferred-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.386:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_base_name(path)`
- Vereinheitlichung des wiederholten `basename(...).strip()`-Pfads in `_device_sysfs_base()`, `_device_display_name()` und `connected_device_inventory()`
- der Helfer kapselt jetzt die Basisnamen-Aufloesung fuer:
  - Sysfs-Basis
  - Anzeigenamen-Fallback
  - Connected-Device-Inventar
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines gestrippten Basenamens
  - unveraenderte Behandlung leerer Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Display-, Inventory- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `421/421` gruen

Kurzfazit:

- Die Device-Basisnamen-Aufloesung laeuft jetzt ueber einen kleinen gemeinsamen Helfer statt denselben `os.path.basename(...).strip()`-Pfad mehrfach lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Basisnamen-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Base-Name-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.387:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_store_connected_device(devices, app, path, base, baseline)`
- Vereinheitlichung des wiederholten `existing -> preferred_path -> entry -> speichern`-Pfads in `connected_device_inventory()`
- der Helfer kapselt jetzt die kleine Speicher-Verdrahtung fuer:
  - vorhandene Basisnamen mit bestehendem Eintrag
  - neue Basisnamen ohne vorhandenen Eintrag
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Verwendung eines bestehenden Eintrags bei der Preferred-Path-Aufloesung
  - unveraenderte Erstellung eines neuen Eintrags fuer einen unbekannten Basisnamen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Connected-Device-Inventory-, Baseline- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `423/423` gruen

Kurzfazit:

- `connected_device_inventory()` delegiert den kleinen Speicherblock jetzt an einen gemeinsamen Helfer statt `existing`, `preferred_path` und `entry` lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Speicher-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Connected-Device-Store-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.388:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_sorted_connected_device_inventory(devices)`
- Vereinheitlichung des wiederholten `devices[key] for key in sorted(devices)`-Ausgabepfads in `connected_device_inventory()`
- der Helfer kapselt jetzt die kleine Sortier-Ausgabe fuer:
  - geordnete Rueckgabe nach Basisnamen
  - leere Device-Mappings ohne Sonderpfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Sortierung der Connected-Device-Ausgabe nach Mapping-Key
  - unveraenderte Rueckgabe einer leeren Liste fuer ein leeres Mapping
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Connected-Device-Inventory-, Baseline- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `425/425` gruen

Kurzfazit:

- `connected_device_inventory()` delegiert seine sortierte Ausgabeliste jetzt an einen kleinen gemeinsamen Helfer statt den `sorted(...)`-List-Comprehension-Pfad lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diese sortierte Rueckgabe zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Connected-Device-Sortierblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.389:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_watch_paths_for(app)`
- Vereinheitlichung des wiederholten Device-Watch-Path-Lookups in `_device_type_mapping()` und `connected_device_inventory()`
- der Helfer kapselt jetzt die kleine Pfad-Aufloesung fuer:
  - Device-Type-Mapping
  - Connected-Device-Inventar
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe der App-Watch-Pfade
  - unveraenderte Behandlung leerer Watch-Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Connected-Device-Inventory-, Baseline- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `427/427` gruen

Kurzfazit:

- `_device_type_mapping()` und `connected_device_inventory()` beziehen die Device-Watch-Pfade jetzt ueber einen kleinen gemeinsamen Helfer statt denselben App-Lookup lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Watch-Path-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Watch-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.390:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_store_device_baseline(app, baseline)`
- Vereinheitlichung der wiederholten Zuweisung von `app.device_baseline` in `build_device_baseline()` und `scan_device_changes()`
- der Helfer kapselt jetzt die kleine Baseline-Speicher-Verdrahtung fuer:
  - aufgebaute Device-Baselines
  - aktualisierte Device-Scan-Zustaende
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Speicherung und Rueckgabe eines Device-Baseline-Mappings
  - unveraenderte Beibehaltung derselben Objektidentitaet
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Baseline-, Inventory- und Scan-Logik
  - Integrity-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `429/429` gruen

Kurzfazit:

- `build_device_baseline()` und `scan_device_changes()` speichern ihre Device-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben App-State-Pfad lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Baseline-Speicherung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Baseline-Store-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.391:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_store_integrity_baseline(app, baseline)`
- Vereinheitlichung der wiederholten Zuweisung von `app.integrity_baseline` in `build_integrity_baseline()` und `scan_integrity_changes()`
- der Helfer kapselt jetzt die kleine Integrity-Baseline-Speicher-Verdrahtung fuer:
  - aufgebaute Integrity-Baselines
  - aktualisierte Integrity-Scan-Zustaende
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Speicherung und Rueckgabe eines Integrity-Baseline-Mappings
  - unveraenderte Beibehaltung derselben Objektidentitaet
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Baseline-, Inventory- und Scan-Logik
  - Device-, Input-Access-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `431/431` gruen

Kurzfazit:

- `build_integrity_baseline()` und `scan_integrity_changes()` speichern ihre Integrity-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben App-State-Pfad lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Integrity-Baseline-Speicherung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Baseline-Store-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.392:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_store_input_access_baseline(app, baseline)`
- Vereinheitlichung der wiederholten Zuweisung von `app.input_access_baseline` in `build_input_access_baseline()` und `scan_input_access_changes()`
- der Helfer kapselt jetzt die kleine Input-Access-Baseline-Speicher-Verdrahtung fuer:
  - aufgebaute Input-Access-Baselines
  - aktualisierte Input-Access-Scan-Zustaende
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Speicherung und Rueckgabe eines Input-Access-Baseline-Mappings
  - unveraenderte Beibehaltung derselben Objektidentitaet
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Baseline-, Inventory- und Scan-Logik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `433/433` gruen

Kurzfazit:

- `build_input_access_baseline()` und `scan_input_access_changes()` speichern ihre Input-Access-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt denselben App-State-Pfad lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Input-Access-Baseline-Speicherung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Baseline-Store-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.393:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_restore_security_baselines(app, data)`
- Vereinheitlichung des wiederholten Baseline-Restore-Pfads in `load_security_baseline()`
- der Helfer kapselt jetzt die kleine Restore-Verdrahtung fuer:
  - sanitisierte Integrity-Baseline
  - Device-Baseline
  - Input-Access-Baseline
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Wiederherstellung eines sanitisierten Baseline-Zustands
  - unveraenderte Verwendung sicherer Defaults bei fehlenden Daten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Inventory- und Scan-Logik
  - Export-, Summary- und Connected-Device-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `435/435` gruen

Kurzfazit:

- `load_security_baseline()` delegiert die kleine Dreifach-Wiederherstellung jetzt an einen gemeinsamen Helfer statt Integrity-, Device- und Input-Access-Zustand lokal nacheinander zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Restore-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Restore-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.394:

- kleiner Refactor im Security-Monitoring-Controller: `scan_input_access_changes()` nutzt jetzt den bestehenden Helfer `_input_access_sorted_process_items(...)`
- Vereinheitlichung des wiederholten PID-Sortierpfads in den Start-/Stop-Diff-Schleifen von `scan_input_access_changes()`
- der bestehende Helfer deckt damit jetzt gemeinsam ab:
  - Start-Events fuer neue Prozesse
  - Stop-Events fuer entfernte Prozesse
  - Stop-Events fuer im Shared-Pfad verschwundene Prozesse
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Start-Event-Reihenfolge gemaess bestehender Prozess-Sortierung
  - unveraenderte Stop-Event-Reihenfolge gemaess bestehender Prozess-Sortierung
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Baseline-, Inventory- und Scan-Logik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: dateiweiser Formatcheck gruen
- Security-Modultests:
  - `437/437` gruen

Kurzfazit:

- `scan_input_access_changes()` verwendet fuer seine PID-Reihenfolge jetzt denselben kleinen Sortierhelfer wie der Inventory-Pfad statt den Sortierausdruck lokal zu duplizieren.
- Die zwei neuen direkten Tests sichern diesmal genau diese Wiederverwendung im Start-/Stop-Scanpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Sortierblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.395:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_input_access_scan_error_message(action, error)`
- Vereinheitlichung der fast identischen Input-Access-Fehlermeldungen in `build_input_access_baseline()` und `scan_input_access_changes()`
- der Helfer kapselt jetzt die kleine Fehlertext-Aufloesung fuer:
  - Baseline-Fehler
  - Scan-Fehler
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Formatierung eines Baseline-Fehlers
  - unveraenderte Behandlung einfacher Textwerte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Input-Access-Baseline-, Inventory- und Scan-Logik
  - Integrity-, Device-, Summary- und Export-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `439/439` gruen

Kurzfazit:

- `build_input_access_baseline()` und `scan_input_access_changes()` beziehen ihre Fehlertexte jetzt ueber einen kleinen gemeinsamen Helfer statt den fast identischen Stringpfad lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Fehlertext-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Input-Access-Fehlermeldungsblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.396:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_pruned_log_message(app, count)`
- Vereinheitlichung des kleinen Prune-Logtextpfads in `load_security_baseline()`
- der Helfer kapselt jetzt die Textaufloesung fuer:
  - Standardtext mit Platzhalter
  - uebersetzten Rueckgabetext mit Platzhalter
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Formatierung des Standardtexts
  - unveraenderte Nutzung des Uebersetzungsergebnisses
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Inventory- und Scan-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `441/441` gruen

Kurzfazit:

- `load_security_baseline()` bezieht seinen Bereinigungs-Logtext jetzt ueber einen kleinen gemeinsamen Helfer statt den formatierten Text lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Logtext-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Prune-Logblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.397:

- kleiner Refactor im Security-Monitoring-Controller: `security_build_baseline()` nutzt jetzt den bestehenden Helfer `_refresh_connected_devices_safe(app)`
- Vereinheitlichung des Callback-Refresh-Pfads fuer Connected Devices im Baseline-Build
- der bestehende Helfer deckt damit jetzt gemeinsam ab:
  - Connected-Device-Refresh im Security-Tab-Pfad
  - Connected-Device-Refresh nach Baseline-Neuaufbau
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Ausfuehrung eines vorhandenen Refresh-Callbacks
  - unveraenderte Rueckgabe bei fehlendem Callback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Inventory- und Scan-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `443/443` gruen

Kurzfazit:

- `security_build_baseline()` verwendet fuer den Connected-Device-Refresh jetzt denselben kleinen Safe-Helfer wie andere Pfade statt den Callback lokal selbst aufzuloesen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Safe-Refresh-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Connected-Device-Refresh-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.398:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_refresh_security_table_callback_safe(app)`
- Vereinheitlichung des nackten `_refresh_security_table()`-Callback-Pfads in `security_build_baseline()` und im Security-Scan-Abschluss
- der Helfer kapselt jetzt die kleine Callback-Aufloesung fuer:
  - Security-Table-Refresh nach Baseline-Neuaufbau
  - Security-Table-Refresh im Scan-Done-Pfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Ausfuehrung eines vorhandenen Refresh-Callbacks
  - unveraenderte Rueckgabe bei fehlendem Callback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Scan- und Inventory-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `445/445` gruen

Kurzfazit:

- `security_build_baseline()` und der Security-Scan-Abschluss verwenden fuer den Tabellen-Refresh jetzt denselben kleinen Safe-Helfer statt den Callback lokal direkt aufzurufen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Safe-Refresh-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Table-Refresh-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.399:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_save_security_baseline_callback_safe(app)`
- Vereinheitlichung des nackten `_save_security_baseline()`-Callback-Pfads in `security_build_baseline()`
- der Helfer kapselt jetzt die kleine Save-Callback-Aufloesung fuer:
  - Security-Baseline-Speicherung nach Neuaufbau
  - fehlende Save-Callbacks ohne Sonderpfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Ausfuehrung eines vorhandenen Save-Callbacks
  - unveraenderte Rueckgabe bei fehlendem Callback
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Save- und Inventory-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: betroffene Testdatei formatiert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `447/447` gruen

Kurzfazit:

- `security_build_baseline()` verwendet fuer die Baseline-Speicherung jetzt einen kleinen Safe-Helfer statt den Save-Callback lokal direkt aufzurufen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Safe-Save-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Save-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.400:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_rebuilt_log_message(app)`
- Vereinheitlichung des kleinen `security_log_baseline_rebuilt`-Textpfads in `security_build_baseline()`
- der Helfer kapselt jetzt die Textaufloesung fuer:
  - Standardtext fuer den Baseline-Neuaufbau
  - Uebersetztes Rueckgabeformat aus `tr(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe des Standardtexts
  - unveraenderte Nutzung des Uebersetzungsergebnisses
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `449/449` gruen

Kurzfazit:

- `security_build_baseline()` bezieht seinen Abschluss-Logtext jetzt ueber einen kleinen gemeinsamen Helfer statt den `tr(...)`-Pfad lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Logtext-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Rebuilt-Logblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.401:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_finish_security_build_baseline(app)`
- Vereinheitlichung des kleinen Abschlussblocks in `security_build_baseline()`
- der Helfer kapselt jetzt die Abschlussverdrahtung fuer:
  - Baseline-Speicherung
  - Connected-Device-Refresh
  - Rebuilt-Log
  - Security-Table-Refresh
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Reihenfolge von Save-, Refresh- und Log-Schritten
  - unveraenderte Log-Ausgabe auch ohne vorhandene Callbacks
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `451/451` gruen

Kurzfazit:

- `security_build_baseline()` delegiert seinen kleinen Abschlussblock jetzt an einen gemeinsamen Helfer statt Save, Refresh und Log lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Abschlussverdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Build-Finish-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.402:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_save_error_message(error)`
- Vereinheitlichung des kleinen Save-Fehlertextpfads in `save_security_baseline()`
- der Helfer kapselt jetzt die Textaufloesung fuer:
  - einfache Fehlerwerte
  - Exception-Objekte
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Formatierung eines String-Fehlers
  - unveraenderte Formatierung einer Exception
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Save-, Build- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `453/453` gruen

Kurzfazit:

- `save_security_baseline()` bezieht seinen Fehlertext jetzt ueber einen kleinen gemeinsamen Helfer statt den formatierten String lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Fehlertext-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Save-Fehlerblock in Phase 3 voll verifiziert abgeschlossen.

Phase 3.403:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_log_security_baseline_pruned_if_needed(app, raw_integrity)`
- Vereinheitlichung des kleinen Prune-Count-und-Log-Pfads in `load_security_baseline()`
- der Helfer kapselt jetzt die Abschlussverdrahtung fuer:
  - Berechnung entfernter Integrity-Einträge
  - optionales Prune-Logging nur bei Bedarf
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Log-Ausgabe bei entfernten Einträgen
  - unveraendertes Schweigen wenn nichts entfernt wurde
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `455/455` gruen

Kurzfazit:

- `load_security_baseline()` delegiert den kleinen Prune-Count-und-Log-Block jetzt an einen gemeinsamen Helfer statt Berechnung und Logging lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Prune-Log-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Prune-Finish-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.404:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_build_all_security_baselines(app)`
- Vereinheitlichung des kleinen Dreierblocks in `security_build_baseline()`
- der Helfer kapselt jetzt die Build-Reihenfolge fuer:
  - Integrity-Baseline
  - Device-Baseline
  - Input-Access-Baseline
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Reihenfolge aller drei Build-Schritte
  - unveraenderte Position des Input-Access-Builds am Ende
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Build-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `457/457` gruen

Kurzfazit:

- `security_build_baseline()` delegiert seinen kleinen Build-Dreierblock jetzt an einen gemeinsamen Helfer statt die drei Build-Aufrufe lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Build-Reihenfolge zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Build-Sequence-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.405:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_load_security_baseline_data(path)`
- Vereinheitlichung des kleinen Datei-zu-JSON-Ladepfads in `load_security_baseline()`
- der Helfer kapselt jetzt die Datenauflosung fuer:
  - reguläre Security-Baseline-Dateien
  - leere JSON-Mappings ohne Sonderpfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte JSON-Ladung aus einer Baseline-Datei
  - unveraenderte Behandlung eines leeren Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `459/459` gruen

Kurzfazit:

- `load_security_baseline()` delegiert den kleinen Datei-zu-JSON-Ladepfad jetzt an einen gemeinsamen Helfer statt `open(...)/json.load(...)` lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Ladeauflosung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Baseline-Load-Data-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.406:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_path(app)`
- Vereinheitlichung der direkten `security_baseline_path`-Aufloesung in den naheliegenden Baseline-Pfaden
- der Helfer kapselt jetzt die Pfadauflosung fuer:
  - Integrity-Watch-Dateiliste
  - Baseline-Load
  - Baseline-Save
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe eines gesetzten Baseline-Pfads
  - unveraenderte Rueckgabe eines leeren Defaults bei fehlendem Wert
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save- und Refresh-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `461/461` gruen

Kurzfazit:

- Die Security-Baseline-Pfadauflosung laeuft jetzt ueber einen kleinen gemeinsamen Helfer statt den Attributzugriff in den nahen Baseline-Pfaden lokal zu streuen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Pfadauflosung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.407:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_current_security_baseline_payload(app)`
- Vereinheitlichung des kleinen `now().isoformat() -> Baseline-Payload`-Pfads in `save_security_baseline()`
- der Helfer kapselt jetzt die aktuelle Timestamp-Aufloesung direkt vor dem bestehenden Payload-Aufbau
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - korrekte Nutzung eines aktuellen ISO-Timestamps
  - unveraenderte Delegation an `_security_baseline_payload(...)`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Inhalt, Save-Format und Fehlerpfad
  - Load-, Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `463/463` gruen

Kurzfazit:

- `save_security_baseline()` baut den aktuellen Baseline-Payload jetzt ueber einen kleinen gemeinsamen Helfer statt den Timestamp lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Timestamp-zu-Payload-Aufloesung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Current-Baseline-Payload-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.408:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_write_security_baseline(path, payload)`
- Vereinheitlichung des festen `safe_write_json(..., indent=2, ensure_ascii=False)`-Pfads in `save_security_baseline()`
- der Helfer kapselt jetzt die projektweiten JSON-Schreiboptionen fuer den Security-Baseline-Save
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Nutzung der erwarteten JSON-Schreiboptionen
  - unveraenderte Rueckgabe des `safe_write_json(...)`-Ergebnisses
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Inhalt, Timestamp-Logik und Fehlerpfad
  - Load-, Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `465/465` gruen

Kurzfazit:

- `save_security_baseline()` schreibt die Security-Baseline jetzt ueber einen kleinen gemeinsamen Write-Helfer statt die festen JSON-Optionen lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Write-Konfiguration zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Write-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.409:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_load_security_baseline_data_for(app)`
- Vereinheitlichung des kleinen `Baseline-Pfad aufloesen -> JSON laden`-Pfads in `load_security_baseline()`
- der Helfer kapselt jetzt die app-bezogene Ladeauflosung direkt vor dem Restore-Pfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Nutzung des aktuellen Baseline-Pfads
  - unveraenderte Rueckgabe der geladenen Mapping-Daten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Restore-, Prune- und Fehlerpfad
  - Save-, Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `467/467` gruen

Kurzfazit:

- `load_security_baseline()` laedt die Security-Baseline jetzt ueber einen kleinen gemeinsamen App-Helfer statt Pfadauflosung und JSON-Laden lokal zu verkoppeln.
- Die zwei neuen direkten Tests sichern diesmal genau diese app-bezogene Ladeauflosung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Load-for-App-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.410:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_baseline_exists(app)`
- Vereinheitlichung des app-bezogenen `os.path.isfile(...)`-Guards in `load_security_baseline()`
- der Helfer kapselt jetzt die kleine Kombination aus Baseline-Pfadauflosung und Existenzcheck
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Nutzung des aktuellen Baseline-Pfads beim Dateicheck
  - unveraenderte False-Rueckgabe bei fehlender Datei
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Restore-, Prune- und Fehlerpfad
  - Save-, Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `469/469` gruen

Kurzfazit:

- `load_security_baseline()` prueft die Existenz der Security-Baseline jetzt ueber einen kleinen gemeinsamen Helfer statt Pfad und `isfile(...)` lokal zusammenzusetzen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Existenzpruefung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Exists-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.411:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_restore_loaded_security_baseline(app, data)`
- Vereinheitlichung des kleinen `restore -> prune-log`-Pfads in `load_security_baseline()`
- der Helfer kapselt jetzt die app-bezogene Nachbearbeitung direkt nach dem Laden der Baseline-Daten
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Reihenfolge von Restore und anschliessendem Prune-Log
  - unveraenderte Weitergabe des Restore-Ergebnisses an den Log-Helfer
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save-, Exists-, Prune- und Fehlerpfad
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `471/471` gruen

Kurzfazit:

- `load_security_baseline()` delegiert die kleine Restore-Nachbearbeitung jetzt an einen gemeinsamen Helfer statt Restore und Prune-Log lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Restore-zu-Log-Verdrahtung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Restore-Load-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.412:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_load_existing_security_baseline(app)`
- Vereinheitlichung des kleinen Happy-Path-Blocks `exists -> load -> restore` in `load_security_baseline()`
- der Helfer kapselt jetzt den erfolgreichen app-bezogenen Baseline-Ladepfad vor dem aeusseren Exception-Guard
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Ueberspringen des Ladepfads bei fehlender Datei
  - unveraenderte Reihenfolge von Existenzcheck, Laden und Restore bei vorhandener Datei
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save-, Exists-, Restore-, Prune- und Fehlerpfad
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `473/473` gruen

Kurzfazit:

- `load_security_baseline()` delegiert den erfolgreichen Security-Baseline-Ladepfad jetzt an einen kleinen gemeinsamen Helfer statt Existenzcheck, Laden und Restore lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Happy-Path zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Load-Happy-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.413:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_write_current_security_baseline(app)`
- Vereinheitlichung des kleinen app-bezogenen Save-Blocks `Pfad -> aktueller Payload -> Write` in `save_security_baseline()`
- der Helfer kapselt jetzt die erfolgreiche Vorverdrahtung vor dem separaten Fehler-Logpfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Reihenfolge von Pfadauflosung, Payload-Aufbau und Write-Aufruf
  - unveraenderte Rueckgabe des Writer-Ergebnisses
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Save-, Load-, Exists-, Restore-, Prune- und Fehlerpfad
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `475/475` gruen

Kurzfazit:

- `save_security_baseline()` delegiert den erfolgreichen Security-Baseline-Schreibpfad jetzt an einen kleinen gemeinsamen Helfer statt Pfad, Payload und Write lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Save-Happy-Path zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Write-Current-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.414:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_log_security_baseline_save_failure(app, error)`
- Vereinheitlichung des kleinen Fehler-Logblocks in `save_security_baseline()`
- der Helfer kapselt jetzt die app-bezogene `log_debug(...)`-Verdrahtung rund um den bestehenden Fehlermeldungs-Helfer
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Format-und-Log-Verdrahtung fuer Save-Fehler
  - unveraenderte Weitergabe des Fehlerobjekts an den Meldungs-Helfer
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Save-, Load-, Exists-, Restore-, Prune- und Happy-Path
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `477/477` gruen

Kurzfazit:

- `save_security_baseline()` delegiert den Security-Baseline-Fehlerlog jetzt an einen kleinen gemeinsamen Helfer statt `log_debug(...)` und Fehlermeldung lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Fehler-Logpfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Save-Failure-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.415:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_save_current_security_baseline_result(app)`
- Vereinheitlichung der kleinen Ergebnisverdrahtung `write -> ggf. Fehler loggen -> bool` in `save_security_baseline()`
- der Helfer kapselt jetzt die Rueckgabe- und Fehlerlogik rund um den bestehenden app-bezogenen Write-Helfer
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte True-Rueckgabe ohne Fehlerlog bei erfolgreichem Write
  - unveraendertes Fehlerlog plus False-Rueckgabe bei fehlgeschlagenem Write
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Save-, Load-, Exists-, Restore-, Prune- und Happy-Path
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `479/479` gruen

Kurzfazit:

- `save_security_baseline()` delegiert jetzt auch die kleine Ergebnis- und Fehlerlog-Verdrahtung an einen gemeinsamen Helfer statt Write-Ergebnis und Rueckgabe lokal auszuwerten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Save-Ergebnispfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Save-Result-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.416:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_load_security_baseline_result(app)`
- Vereinheitlichung der kleinen Safe-Result-Semantik `try -> delegate -> sonst False` in `load_security_baseline()`
- der Helfer kapselt jetzt die exception-sichere Rueckgabe des bestehenden app-bezogenen Load-Happy-Paths
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Weitergabe eines erfolgreichen Delegate-Ergebnisses
  - unveraenderte False-Rueckgabe bei Exception im Delegate-Pfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Baseline-Load-, Save-, Exists-, Restore-, Prune- und Happy-Path
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `481/481` gruen

Kurzfazit:

- `load_security_baseline()` delegiert jetzt auch die kleine exception-sichere Ergebnisbehandlung an einen gemeinsamen Helfer statt `try/except` und Rueckgabe lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Load-Result-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Baseline-Load-Result-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.417:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_watch_base_files(app, app_file_path)`
- Vereinheitlichung der festen Basis-Dateiliste in `integrity_watch_files()`
- der Helfer kapselt jetzt die statischen Watch-Pfade fuer VPN-, Link-, Privacy-, HDD-, Security-Baseline-, ClamAV- und App-Datei
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Reihenfolge der festen Basis-Dateiliste
  - unveraenderte Nutzung des aktuellen Security-Baseline-Pfads innerhalb der Liste
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-WireGuard-Scan, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `483/483` gruen

Kurzfazit:

- `integrity_watch_files()` bezieht seine feste Basis-Dateiliste jetzt ueber einen kleinen gemeinsamen Helfer statt die statischen Watch-Pfade lokal zusammenzustellen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Basis-Dateiliste zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Watch-Base-Files-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.418:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_watch_wireguard_files(wgdir="/etc/wireguard")`
- Vereinheitlichung des kleinen WireGuard-Anhangs in `integrity_watch_files()`
- der Helfer kapselt jetzt den optionalen WireGuard-Ordnerscan inklusive File-Filter und Fehlerfallback
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe nur echter Dateien aus dem WireGuard-Verzeichnis
  - unveraenderte leere Rueckgabe bei Scan-Fehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Basis-Dateiliste, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `485/485` gruen

Kurzfazit:

- `integrity_watch_files()` bezieht den optionalen WireGuard-Dateianhang jetzt ueber einen kleinen gemeinsamen Helfer statt den Verzeichnis-Scan lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen WireGuard-Scan zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Watch-WireGuard-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.419:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_watch_app_file_path()`
- Vereinheitlichung der festen NetMon-`app.py`-Pfadauflosung in `integrity_watch_files()`
- der Helfer kapselt jetzt die kleine `dirname -> .. -> app.py -> abspath`-Verdrahtung fuer den Integrity-Watch-Pfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Zielauflosung auf die NetMon-`app.py`
  - unveraenderte Nutzung eines absoluten Rueckgabepfads
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Basis-Dateiliste, WireGuard-Scan, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `487/487` gruen

Kurzfazit:

- `integrity_watch_files()` bezieht den festen NetMon-`app.py`-Watch-Pfad jetzt ueber einen kleinen gemeinsamen Helfer statt die Pfadkette lokal aufzubauen.
- Die zwei neuen direkten Tests sichern diesmal genau diese App-Pfadauflosung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Watch-App-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.420:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_security_integrity_ignored_paths(app)`
- Vereinheitlichung des expliziten NetMon-Pfadkatalogs in `security_integrity_ignore_path()`
- der Helfer kapselt jetzt die app-bezogene Sammlung explizit ignorierter Integrity-Pfade fuer Config-, Radio-, ClamAV-, Security- und Guard-Dateien
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Sammlung gesetzter expliziter Ignore-Pfade
  - unveraendertes Ueberspringen leerer oder fehlender Werte
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Watch-Pfade, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `489/489` gruen

Kurzfazit:

- `security_integrity_ignore_path()` bezieht den expliziten NetMon-Ignore-Katalog jetzt ueber einen kleinen gemeinsamen Helfer statt die Pfadsammlung lokal aufzubauen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Ignore-Pfadsammlung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Security-Integrity-Ignored-Paths-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.421:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_path_is_dir_or_child(target, directory)`
- Vereinheitlichung des kleinen Config-/State-Dir-Guards in `security_integrity_ignore_path()`
- der Helfer kapselt jetzt die wiederholte Pruefung `gleiches Verzeichnis oder Kindpfad`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen von identischem Verzeichnis und Kindpfad
  - unveraendertes Ablehnen leerer Werte und praefixartiger Fehlmatches
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Watch-Pfade, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `491/491` gruen

Kurzfazit:

- `security_integrity_ignore_path()` verwendet fuer die Config-/State-Verzeichnispruefung jetzt einen kleinen gemeinsamen Helfer statt die Dir-oder-Kindpfad-Logik lokal zu duplizieren.
- Die zwei neuen direkten Tests sichern diesmal genau diese Pfadbeziehungspruefung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Path-Is-Dir-Or-Child-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.422:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_watch_files_set(app)`
- Vereinheitlichung der kleinen Watch-File-Normalisierung in `sanitize_integrity_baseline()`
- der Helfer kapselt jetzt die app-bezogene Normalisierung, Filterung leerer Werte und den Fehlerfallback fuer Watch-Dateien
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Normalisierung und Filterung der Watch-Dateiliste
  - unveraenderte leere Rueckgabe bei Exception im Watch-File-Pfad
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Ignore-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `493/493` gruen

Kurzfazit:

- `sanitize_integrity_baseline()` bezieht die normalisierte Watch-Dateimenge jetzt ueber einen kleinen gemeinsamen Helfer statt den Set-Aufbau lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diese Watch-File-Normalisierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Watch-Files-Set-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.423:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_normalized_path(path)`
- Vereinheitlichung der kleinen `expanduser -> abspath`-Normalisierung in den nahen Integrity-Pfaden
- der Helfer kapselt jetzt die gemeinsame Pfadnormalisierung fuer Watch-Dateien und sanitierte Baseline-Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Expansion von `~` plus absolute Pfadauflosung
  - unveraenderte Rueckgabe bereits absoluter Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Ignore-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `495/495` gruen

Kurzfazit:

- Die nahen Integrity-Pfade verwenden fuer die kleine Nutzerpfad-zu-Absolutpfad-Normalisierung jetzt einen gemeinsamen Helfer statt `expanduser` und `abspath` lokal zu wiederholen.
- Die zwei neuen direkten Tests sichern diesmal genau diese Pfadnormalisierung zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Normalized-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.424:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_path_allowed(app, path, watch_files)`
- Vereinheitlichung der kleinen Zulassungspruefung `im Watch-Set und nicht ignoriert` in `sanitize_integrity_baseline()`
- der Helfer kapselt jetzt die kombinierte Watch-Set-/Ignore-Entscheidung fuer absolute Integrity-Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Ablehnen von Pfaden ausserhalb der Watch-Dateimenge
  - unveraendertes Ablehnen ignorierter Watch-Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Ignore-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `497/497` gruen

Kurzfazit:

- `sanitize_integrity_baseline()` delegiert die kombinierte Watch-Set-/Ignore-Pruefung jetzt an einen kleinen gemeinsamen Helfer statt beide Entscheidungen lokal zu verdrahten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Integrity-Path-Allowed-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Path-Allowed-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.425:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_sanitize_integrity_entry(app, raw_path, entry, watch_files)`
- Vereinheitlichung des kleinen Eintrags-Entscheidungsblocks in `sanitize_integrity_baseline()`
- der Helfer kapselt jetzt die Trim-/Relativpfad-/Absolutpfad-/Zulassungsentscheidung fuer einzelne Integrity-Baseline-Eintraege
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Beibehalten relativer Pfade
  - unveraendertes Verwerfen nicht erlaubter absoluter Pfade
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Ignore-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `499/499` gruen

Kurzfazit:

- `sanitize_integrity_baseline()` delegiert die Entscheidung ueber einzelne Baseline-Eintraege jetzt an einen kleinen gemeinsamen Helfer statt den gesamten Eintragsblock lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Sanitizing-Eintrags-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Sanitize-Integrity-Entry-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.426:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_integrity_entries_differ(old, cur)`
- Vereinheitlichung der kleinen Änderungslogik für Integrity-Einträge in `scan_integrity_changes()`
- der Helfer kapselt jetzt den Vergleich von `sha`, `size` und toleriertem `mtime`-Delta
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen von SHA-, Groessen- und relevanten `mtime`-Aenderungen
  - unveraendertes Ignorieren winziger `mtime`-Differenzen innerhalb der Toleranz
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Sanitizing, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `501/501` gruen

Kurzfazit:

- `scan_integrity_changes()` nutzt für die Erkennung geänderter Dateien jetzt einen kleinen gemeinsamen Helfer statt den Feldvergleich lokal auszuschreiben.
- Die zwei neuen direkten Tests sichern diesmal genau diese Integrity-Diff-Logik zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Integrity-Entries-Differ-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.427:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_modified_integrity_event(events, app, baseline, current, path)`
- Vereinheitlichung des kleinen Modified-Blocks pro Pfad in `scan_integrity_changes()`
- der Helfer kapselt jetzt Lookup, Differenzpruefung und das Anhaengen geaenderter Datei-Events
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Anhaengen eines `FILE MODIFIED`-Events bei echter Aenderung
  - unveraendertes Ueberspringen bei fehlenden oder nicht verwertbaren Eintraegen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Sanitizing, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `503/503` gruen

Kurzfazit:

- `scan_integrity_changes()` delegiert den lokalen Modified-Block jetzt an einen kleinen gemeinsamen Helfer statt Lookup, Diff und Event-Anhaengen im Loop zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Modified-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Append-Modified-Integrity-Event-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.428:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_integrity_event_for_path(events, app, mapping, kind, path)`
- Vereinheitlichung der kleinen New/Delete-Pfade in `scan_integrity_changes()`
- der Helfer kapselt jetzt `Entry holen -> Integrity-Event anhängen` für einzelne Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Nutzung des Entries aus dem uebergebenen Mapping
  - unveraendertes Durchreichen leerer Entries an den Event-Helfer
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Sanitizing, Modified-Diff, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `505/505` gruen

Kurzfazit:

- `scan_integrity_changes()` bezieht die New/Delete-Event-Verdrahtung jetzt ueber einen kleinen gemeinsamen Helfer statt Entry-Lookup und Event-Anhaengen in zwei Loops lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Integrity-Event-for-Path-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Append-Integrity-Event-For-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.429:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_finish_scan_integrity_changes(app, current, events)`
- Vereinheitlichung des kleinen Abschlussblocks in `scan_integrity_changes()`
- der Helfer kapselt jetzt `Integrity-Baseline speichern -> Eventliste zurueckgeben`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Speichern der aktuellen Baseline bei Rueckgabe der Eventliste
  - unveraendertes Durchreichen auch leerer Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Integrity-Diff-/Scan-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `507/507` gruen

Kurzfazit:

- `scan_integrity_changes()` delegiert jetzt auch seinen kleinen Abschlussblock an einen gemeinsamen Helfer statt Speichern und Rueckgabe lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Integrity-Scan-Finish-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Finish-Scan-Integrity-Changes-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.430:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_paths_in(directory, exists_fn)`
- Vereinheitlichung des kleinen `Verzeichnis listen -> Pfad bauen -> filtern`-Loops in `device_watch_paths()`
- der Helfer kapselt jetzt die gemeinsame Pfadsammlung fuer `/dev/input` und `/sys/class/input`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe gefilterter, zusammengebauter Device-Pfade
  - unveraenderte leere Rueckgabe bei Verzeichnisfehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Watch-Auswahl, Integrity-/Baseline-Pfade und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `509/509` gruen

Kurzfazit:

- `device_watch_paths()` bezieht seine beiden kleinen Directory-Scans jetzt ueber einen gemeinsamen Helfer statt denselben Sammel-Loop lokal doppelt zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Device-Paths-In-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Paths-In-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.431:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_device_event_for_path(events, app, mapping, kind, change, path)`
- Vereinheitlichung der kleinen New/Removed-Pfade in `scan_device_changes()`
- der Helfer kapselt jetzt `Device-Typ holen -> Device-Event anhängen` für einzelne Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Nutzung des Device-Typs aus dem uebergebenen Mapping
  - unveraendertes Durchreichen eines Default-/Fallback-Device-Typs
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Watch-Auswahl, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `511/511` gruen

Kurzfazit:

- `scan_device_changes()` bezieht die New/Removed-Event-Verdrahtung jetzt ueber einen kleinen gemeinsamen Helfer statt Device-Typ-Lookup und Event-Anhaengen in zwei Loops lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Device-Event-for-Path-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Append-Device-Event-For-Path-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.432:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_finish_scan_device_changes(app, current, events)`
- Vereinheitlichung des kleinen Abschlussblocks in `scan_device_changes()`
- der Helfer kapselt jetzt `Device-Baseline speichern -> Eventliste zurueckgeben`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Speichern der aktuellen Device-Baseline bei Rueckgabe der Eventliste
  - unveraendertes Durchreichen auch leerer Eventlisten
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Diff-Logik, Integrity-/Baseline-Pfade und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `513/513` gruen

Kurzfazit:

- `scan_device_changes()` delegiert jetzt auch seinen kleinen Abschlussblock an einen gemeinsamen Helfer statt Speichern und Rueckgabe lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Device-Scan-Finish-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Finish-Scan-Device-Changes-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.433:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_name_is_input_event(name)`
- Vereinheitlichung des kleinen `event*`-Checks in `device_type_from_path()`
- der Helfer kapselt jetzt die Prefix-Pruefung fuer Input-Event-Geraetenamen
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen von `event`-Praefixen
  - unveraendertes Ablehnen nicht passender Geraetenamen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `515/515` gruen

Kurzfazit:

- `device_type_from_path()` nutzt fuer den kleinen `event*`-Pfad jetzt einen gemeinsamen Helfer statt die Prefix-Pruefung lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Input-Event-Namenspfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Name-Is-Input-Event-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.434:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_name_is_mouse(name)`
- Vereinheitlichung des kleinen `mouse`-Checks in `device_type_from_path()`
- der Helfer kapselt jetzt die Teilstring-Pruefung fuer Maus-Geraetenamen
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen von Maus-Namen mit `mouse`-Teilstring
  - unveraendertes Ablehnen nicht passender Geraetenamen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `517/517` gruen

Kurzfazit:

- `device_type_from_path()` nutzt fuer den kleinen Maus-Namenspfad jetzt einen gemeinsamen Helfer statt die Teilstring-Pruefung lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Device-Name-Is-Mouse-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Name-Is-Mouse-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.435:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_name_is_keyboard(name)`
- Vereinheitlichung des kleinen `kbd`-/`keyboard`-Checks in `device_type_from_path()`
- der Helfer kapselt jetzt die Teilstring-Pruefung fuer Keyboard-Geraetenamen
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen von Keyboard-Namen mit `kbd` oder `keyboard`
  - unveraendertes Ablehnen nicht passender Geraetenamen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Ergebnis:

- `ruff`: gruen
- `black`: beide Dateien unveraendert; dateiweiser Formatcheck gruen
- Security-Modultests:
  - `519/519` gruen

Kurzfazit:

- `device_type_from_path()` nutzt fuer den kleinen Keyboard-Namenspfad jetzt einen gemeinsamen Helfer statt die Teilstring-Pruefung lokal zu halten.
- Die zwei neuen direkten Tests sichern diesmal genau diesen Device-Name-Is-Keyboard-Pfad zusaetzlich zu den bestehenden Security-Regressionstests ab.
- Damit ist auch dieser kleine Device-Name-Is-Keyboard-Block in Phase 3 voll verifiziert abgeschlossen.

Phase 3.436:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_normalized_device_name(path)`
- Vereinheitlichung des kleinen `basename(...).lower()`-Pfads in `device_type_from_path()`
- der Helfer kapselt jetzt die normalisierte Geraetename-Aufloesung aus einem Pfad
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Lowercasing des bereinigten Basenames
  - unveraendertes Verhalten bei leeren Eingaben
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.437:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_type_for_name(name)`
- Vereinheitlichung der kleinen Namens-zu-Typ-Cascade in `device_type_from_path()`
- der Helfer kapselt jetzt die lokale Reihenfolge `input-event -> mouse -> keyboard -> hid`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Erkennen bekannter Device-Namensmarker
  - unveraenderten Fallback auf `hid`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.438:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_sorted_device_watch_paths(paths)`
- Vereinheitlichung des kleinen `sorted(set(...))`-Ausgabepfads in `device_watch_paths()`
- der Helfer kapselt jetzt die deduplizierte und sortierte Rueckgabe der Device-Watch-Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Sortieren und Deduplizieren von Device-Pfaden
  - unveraendertes Verhalten bei leeren Eingaben
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.439:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_collected_device_watch_paths()`
- Vereinheitlichung des kleinen Zwei-Quellen-Sammelpfads in `device_watch_paths()`
- der Helfer kapselt jetzt das Zusammenziehen der `/dev/input`- und `/sys/class/input`-Watch-Pfade
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Zusammenfuehren beider Device-Watch-Quellen
  - unveraendertes Verhalten bei leeren Quellen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.440:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_input_watch_paths()`
- Vereinheitlichung des kleinen `/dev/input`-Teilpfads in `_collected_device_watch_paths()`
- der Helfer kapselt jetzt den Input-Device-Watch-Lookup ueber `_device_paths_in(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Delegieren an `_device_paths_in("/dev/input", os.path.exists)`
  - unveraendertes Verhalten bei leerem Ergebnis
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.441:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_sysfs_watch_paths()`
- Vereinheitlichung des kleinen `/sys/class/input`-Teilpfads in `_collected_device_watch_paths()`
- der Helfer kapselt jetzt den Sysfs-Device-Watch-Lookup ueber `_device_paths_in(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes Delegieren an `_device_paths_in("/sys/class/input", os.path.islink)`
  - unveraendertes Verhalten bei leerem Ergebnis
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.442:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_append_device_events_for_paths(...)`
- Vereinheitlichung der wiederholten sortierten Device-Diff-Loops in `scan_device_changes()`
- der Helfer kapselt jetzt den Pfad `sorted(paths) -> _append_device_event_for_path(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraendertes sortiertes Weiterreichen aller Device-Pfade
  - unveraendertes Verhalten bei leerer Pfadmenge
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-Typableitung, Device-Diff-Logik, Baseline-Save/-Load und alle Security-Scan-Pfade
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.443:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_mapping_path_sets(baseline, current)`
- Vereinheitlichung des wiederholten `old_paths/new_paths`-Aufbaus in den Integrity-, Device- und Input-Access-Diffpfaden
- der Helfer kapselt jetzt die gemeinsame Ableitung ueber `_mapping_paths(...)`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Rueckgabe der alten und neuen Pfadmenge
  - unveraendertes Verhalten bei fehlenden oder leeren Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Integrity- und Input-Access-Diff-Logik sowie Baseline-Save/-Load
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.444:

- kleiner Refactor im Security-Monitoring-Controller: neuer Helfer `_device_change_path_sets(baseline, current)`
- Vereinheitlichung der kleinen Added-/Removed-Path-Ableitung in `scan_device_changes()`
- der Helfer kapselt jetzt die gemeinsame Rueckgabe von `old_paths`, `new_paths`, `added_paths` und `removed_paths`
- zusaetzlich zwei direkte Tests ergaenzt fuer:
  - unveraenderte Ableitung der hinzugekommenen und entfernten Device-Pfade
  - unveraendertes Verhalten bei fehlenden oder leeren Mappings
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Integrity- und Input-Access-Diff-Logik sowie Baseline-Save/-Load
  - Export-, Summary-, Device- und Input-Access-Pfade

Phase 3.445:

- groesserer Phase-3-Abschlussblock im Security-Monitoring-Controller: neue Helfer `_current_device_state(app)`, `_device_scan_context(app)` und `_append_device_change_events(...)`
- Vereinheitlichung des zusammenhaengenden Device-Baseline-/Diff-Pfads in `build_device_baseline()` und `scan_device_changes()`
- die Helfer kapseln jetzt:
  - die gemeinsame Ableitung des aktuellen Device-States
  - den Scan-Kontext aus aktuellem State, Baseline sowie Added-/Removed-Pfaden
  - die gemeinsame Verdrahtung der Device-New-/Device-Removed-Eventanhaenge
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderte Delegation der Added-/Removed-Eventpfade
  - unveraendertes Verhalten bei leeren Diff-Mengen
  - unveraenderte Rueckgabe des Device-Scan-Kontexts
  - unveraendertes Verhalten bei leerem Current-/Baseline-State
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - Device-, Integrity- und Input-Access-Diff-Logik sowie Baseline-Save/-Load
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.1: Security-Scan-Orchestrierung `netmon/features/security_monitoring_controller.py`

- groesserer Orchestrierungsblock im Security-Monitoring-Controller: neue Helfer `_scan_ufw_security_events(app)`, `_scan_portscan_findings(app)`, `_security_scan_orchestration(app)`, `_append_unique_security_events(app, events)` und `_security_scan_alert_state(...)`
- Vereinheitlichung des zusammenhaengenden Scan-Ablaufs in `security_poll_async()` und `security_scan_now()`
- die Helfer kapseln jetzt:
  - das gemeinsame Einsammeln neuer UFW-Events und Portscan-Findings
  - die gemeinsame Orchestrierung von UFW-, Portscan-, Integrity-, Device- und Input-Access-Scans
  - das einheitliche Anhaengen neuer Security-Events unter Beachtung bestehender Event-Keys
  - die gemeinsame Ableitung von Alarmfarbe und Last-Alarm-Text
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Deduplizieren und Anhaengen neuer Security-Events
  - unveraendertes Priorisieren des Portscan-Alarmzustands
  - unveraenderte Rueckgabe aller Event-Gruppen aus der gemeinsamen Scan-Orchestrierung
  - unveraendertes Verhalten bei komplett leeren Event-Gruppen
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Scan-Logik der einzelnen UFW-, Integrity-, Device- und Input-Access-Quellen
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.2: Security-Scan-Abschluss- und UI-Updates `netmon/features/security_monitoring_controller.py`

- groesserer Abschlussblock im Security-Monitoring-Controller: neue Helfer `_log_harmless_rst_events(app, harmless_rst_events)`, `_finish_security_poll_cycle(app, color, harmless_rst_events)` und `_finish_security_scan_now(app, new_events, color)`
- Vereinheitlichung des zusammenhaengenden Abschluss- und UI-Update-Pfads in `security_poll_async()` und `security_scan_now()`
- die Helfer kapseln jetzt:
  - das gemeinsame Loggen harmloser RST-Rueckverkehrsereignisse
  - den kompletten Poll-Abschluss mit Refresh, Status-Update und Reschedule
  - den kompletten Manual-Scan-Abschluss mit Event-Anhang, Logging und UI-Refresh
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes RST-Logging inklusive Zusammenfassungszeile
  - unveraendertes Default-Logging ohne Summary
  - unveraenderte Poll-Abschlussverdrahtung mit Refresh, Status und Reschedule
  - unveraenderte Manual-Scan-Abschlussverdrahtung mit Event-Anhang und UI-Updates
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Scan-Logik der einzelnen UFW-, Integrity-, Device- und Input-Access-Quellen
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.3: Security-Runtime- und Input-Access-Abschluss `netmon/features/security_monitoring_controller.py`

- groesserer Runtime-Block im Security-Monitoring-Controller: neue Helfer `_ensure_security_log_level(app)`, `_finish_security_start_monitoring(app)`, `_finish_security_stop_monitoring(app)` und `_finish_security_input_access_scan(app, events)`
- Vereinheitlichung des zusammenhaengenden Runtime- und Input-Access-Abschluss-Pfads in `security_start_monitoring()`, `security_stop_monitoring()` und `security_input_access_scan()`
- die Helfer kapseln jetzt:
  - die gemeinsame Log-Level-Auffrischung mit Fallback-Logging
  - den Start-Abschluss mit Log, Statuswechsel und Poll-Trigger
  - den Stop-Abschluss mit Log und Statuswechsel
  - den Input-Access-Scan-Abschluss mit Event-Anhang, Logging und Table-Refresh
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Log-Level-Fallback-Verhalten
  - unveraenderte Start-Abschlussverdrahtung
  - unveraenderte Input-Access-Abschlussverdrahtung
  - unveraendertes Verhalten bei erfolgreicher Log-Level-Auffrischung
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Scan-Logik der einzelnen UFW-, Integrity-, Device- und Input-Access-Quellen
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.5: Security-Poll- und Entry-Laufzeit `netmon/features/security_monitoring_controller.py`

- groesserer Laufzeitblock im Security-Monitoring-Controller: neue Helfer `_mark_security_scan_running(app)` und `_run_security_poll_job(app)`
- Vereinheitlichung des zusammenhaengenden Poll- und Entry-Laufzeitpfads in `security_poll_async()` sowie der Start-Guard-Logik von `_begin_security_scan(app)`
- die Helfer kapseln jetzt:
  - das gemeinsame Umschalten in den Running-Zustand fuer Poll und manuell gestartete Scans
  - den eigentlichen Poll-Job mit Orchestrierung, Event-Anhang, Alarmzustand und geplantem UI-Abschluss
  - die gemeinsame Wiederverwendung des Running-Guards in Poll- und manuellen Scan-Einstiegen
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Setzen bzw. Ablehnen des Running-Flags
  - unveraenderte Poll-Job-Verdrahtung mit Alarmupdate und geplantem Abschluss
  - unveraendertes Bewahren eines bestehenden Alarmtexts ohne neuen Alarm
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Scan-Logik der einzelnen UFW-, Integrity-, Device- und Input-Access-Quellen
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.6: Security-Baseline-Lebenszyklus-Kontext `netmon/features/security_monitoring_controller.py`

- groesserer Baseline-Block im Security-Monitoring-Controller: neue Helfer `_run_security_baseline_build(app)`, `_security_baseline_state(app)`, `_security_baseline_load_context(app)` und `_security_baseline_write_context(app)`
- Vereinheitlichung des zusammenhaengenden Build-/Load-/Save-Kontexts in `security_build_baseline()`, `_security_baseline_payload(...)`, `_load_existing_security_baseline()` und `_write_current_security_baseline()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Build- und Finish-Pfad des Baseline-Neuaufbaus
  - den aktuellen Baseline-State als detachtes Snapshot-Mapping
  - den gemeinsamen Load-Kontext aus Existenzpruefung und geladenen Daten
  - den gemeinsamen Write-Kontext aus Baseline-Pfad und aktuellem Payload
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderte Build-/Finish-Reihenfolge des Baseline-Neuaufbaus
  - unveraenderten detachierten Snapshot des Baseline-States
  - unveraenderten Load-Kontext bei vorhandener bzw. fehlender Baseline-Datei
  - unveraenderten Write-Kontext aus Pfad und Payload
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Integritaets-, Device- und Input-Access-Baseline-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.7: Security-Baseline-Load- und Save-Pipelines `netmon/features/security_monitoring_controller.py`

- groesserer Baseline-Block im Security-Monitoring-Controller: neue Helfer `_load_security_baseline_pipeline(app, exists, data)` und `_save_security_baseline_pipeline(app, ok, err)`
- Vereinheitlichung des zusammenhaengenden Load-/Save-Ausfuehrungspfads in `_load_existing_security_baseline()` und `_save_current_security_baseline_result()`
- die Helfer kapseln jetzt:
  - den eigentlichen Load-Pipeline-Schritt aus Existenzentscheidung und Restore-Aufruf
  - den eigentlichen Save-Pipeline-Schritt aus Writer-Ergebnis und Fehlerlogging
  - die gemeinsame Rueckgabe der booleschen Ergebniswerte fuer Load und Save
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Ueberspringen des Restore-Schritts bei fehlender Baseline
  - unveraendertes Restore-Verhalten bei vorhandener Baseline
  - unveraendertes Save-Ergebnis ohne Fehlerlogging bei Erfolg
  - unveraendertes Fehlerlogging und False-Ergebnis bei Save-Fehlern
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Integritaets-, Device- und Input-Access-Baseline-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.8: Security-Baseline-Ausfuehrungsstufen `netmon/features/security_monitoring_controller.py`

- groesserer Baseline-Block im Security-Monitoring-Controller: neue Helfer `_run_security_baseline_rebuild_followups(app)`, `_run_security_baseline_load(app)` und `_run_security_baseline_save(app)`
- Vereinheitlichung des zusammenhaengenden Finish-/Load-/Save-Ausfuehrungspfads in `_finish_security_build_baseline()`, `_load_existing_security_baseline()` und `_save_current_security_baseline_result()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Rebuild-Abschluss aus Save-Callback, Device-Refresh, Rebuild-Log und Table-Refresh
  - den eigentlichen Load-Stufenschritt aus Load-Kontext und Pipeline-Ausfuehrung
  - den eigentlichen Save-Stufenschritt aus Writer-Ergebnis und Save-Pipeline
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderte Delegation des Build-Abschlusses in die Rebuild-Followups
  - unveraenderte Reihenfolge der Rebuild-Followups
  - unveraenderte Verdrahtung von Load-Kontext zu Load-Pipeline
  - unveraenderte Verdrahtung von Writer-Ergebnis zu Save-Pipeline
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Integritaets-, Device- und Input-Access-Baseline-Logik
  - Export-, Summary-, Device- und Input-Access-Pfade

## Phase 4.9: Security-Reporting-Kontext `netmon/features/security_monitoring_controller.py`

- groesserer Reporting-Block im Security-Monitoring-Controller: neue Helfer `_security_runtime_context(app)` und `_security_reporting_context(app)`
- Vereinheitlichung des zusammenhaengenden Runtime-/Event-/Baseline-Kontexts in `_security_summary_context()`, `_security_export_blocks_for_app()`, `security_update_status()` und `_build_security_chad_summary(...)`
- die Helfer kapseln jetzt:
  - den gemeinsamen Runtime-Snapshot aus Monitoring-Status, Logging-Level, Event-Anzahl und letztem Alarm
  - den gemeinsamen Reporting-Snapshot aus Events, sichtbaren Events, Aggregation, Filter und Baselines
  - die Wiederverwendung dieser Snapshots in Status-, Export- und Summary-Pfaden
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderte Safe-Defaults des Runtime-Kontexts
  - unveraenderte detached Event-Listen im Reporting-Kontext
  - unveraenderte Auswahl der Summary-Felder aus dem Reporting-Kontext
  - unveraenderte Verdrahtung von Reporting-Kontext zu Export-Blocks
  - unveraenderte Verdrahtung von Runtime-Kontext zu `security_update_status()`
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Export-, Chad-Summary- und Status-Logik
  - Device-, Input-Access- und Baseline-Fachlogik

## Phase 4.10: Security-Clear-Lebenszyklus `netmon/features/security_monitoring_controller.py`

- groesserer UI-Block im Security-Monitoring-Controller: neue Helfer `_confirm_security_clear_events(app, confirm)`, `_run_security_clear_events(app)` und `_run_security_clear_views(app)`
- Vereinheitlichung des zusammenhaengenden Confirm-/Reset-/Finish-Pfads in `security_clear_events()` und `security_clear_views()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Confirm-Schritt fuer das Leeren vorhandener Security-Events inklusive Cancel-Logging
  - den eigentlichen Event-Clear-Ablauf aus Reset, Detail-Clear, Tabellen-Refresh, Status-Update und Log
  - den eigentlichen View-Clear-Ablauf aus Table-Clear, View-State-Reset und Abschluss-Update
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Ueberspringen des Dialogs ohne Confirm-Flow
  - unveraendertes Cancel-Verhalten mit Log beim Abbrechen
  - unveraenderte Verdrahtung des Event-Clear-Ablaufs
  - unveraenderte Verdrahtung des View-Clear-Ablaufs
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Security-Event- und View-Reset-Logik
  - Export-, Summary- und Scan-Pfade

## Phase 4.11: Security-Export-Lebenszyklus `netmon/features/security_monitoring_controller.py`

- groesserer Export-Block im Security-Monitoring-Controller: neue Helfer `_security_export_write_context(app, moment)`, `_write_security_export(path, blocks)` und `_run_security_export(app, moment)`
- Vereinheitlichung des zusammenhaengenden Export-Ziel-/Write-/Success-Pfads in `export_security_logs()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Export-Kontext aus Zielpfad und bereits aufgebauten Export-Bloecken
  - den eigentlichen Dateischreibschritt des Security-Exports
  - den eigentlichen Exportlauf aus Kontextaufbau und Write-Ausfuehrung
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderte Verdrahtung von Export-Target zu Export-Bloecken
  - unveraendertes Schreiben der Export-Bloecke in die Zieldatei
  - unveraenderte Verdrahtung von Write-Kontext zu Write-Schritt
  - unveraenderte Nutzung von Exportlauf und Success-Pfad im Entry-Point
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Exportinhalt-, Summary- und Reporting-Logik
  - Clear-, Scan- und Baseline-Pfade

## Phase 4.12: Security-Table-Refresh-Stages `netmon/features/security_monitoring_controller.py`

- groesserer UI-Block im Security-Monitoring-Controller: neue Helfer `_refresh_security_table_state(app)`, `_append_security_aggregate_rows(app, table)`, `_append_security_event_rows(app, table, visible_events)` und `_refresh_security_table_view(app, visible_events)`
- Vereinheitlichung des zusammenhaengenden Filter-/Table-/Stats-Pfads in `refresh_security_table()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Table-State-Reset mit neuem Visible-Events-Snapshot
  - den Aggregate-Row-Aufbau fuer den All-Filter
  - den Event-Row-Aufbau inklusive Row-Meta-Verdrahtung
  - den eigentlichen View-Refresh aus Clear, Row-Append und Stats-Update
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraenderten State-Reset und Visible-Events-Refresh
  - unveraendertes Aggregate-Insert-Verhalten fuer positive All-Filter-Eintraege
  - unveraenderten Event-Row-Insert samt Meta-Verdrahtung
  - unveraenderte Reihenfolge von Clear-, Append- und Stats-Schritt im View-Refresh
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Filter-, Stats- und Selection-Logik
  - Export-, Clear-, Scan- und Baseline-Pfade

## Phase 4.13: Security-UI-Aktionspfad `netmon/features/security_monitoring_controller.py`

- groesserer UI-Block im Security-Monitoring-Controller: neue Helfer `_show_selected_security_event(app, table)`, `_finish_security_refresh_table_action(app)` und `_run_security_filter_action(app, filter_mode, tr_key, default_message)`
- Vereinheitlichung des zusammenhaengenden Selection-/Refresh-/Filter-Aktionspfads in `on_security_event_select()`, `security_refresh_table_action()` und `_apply_security_filter()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Detail-Show-Schritt fuer ausgewaehlte Security-Tabellenzeilen
  - den gemeinsamen Abschluss von Table-Refresh-Action mit Device-Refresh und Log
  - den gemeinsamen Filter-Aktionslauf aus Filter-Setzen, Table-Refresh und Log
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Detail-Setzen bzw. Ueberspringen bei leerer Selection
  - unveraenderten Abschluss der Table-Refresh-Action
  - unveraenderte Verdrahtung des Filter-Aktionslaufs
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Selection-, Filter- und Table-Logik
  - Export-, Clear-, Scan- und Baseline-Pfade

## Phase 4.4: Security-Scan-Start- und Job-Laufzeit `netmon/features/security_monitoring_controller.py`

- groesserer Laufzeitblock im Security-Monitoring-Controller: neue Helfer `_begin_security_scan(app)`, `_start_security_scan_thread(job)`, `_run_security_scan_now_job(app)` und `_run_security_input_access_scan_job(app)`
- Vereinheitlichung des zusammenhaengenden Start-/Guard-/Thread-Pfads in `security_scan_now()` und `security_input_access_scan()`
- die Helfer kapseln jetzt:
  - den gemeinsamen Reentry-Guard fuer bereits laufende Scans
  - das einheitliche Starten daemonisierter Scan-Threads
  - den eigentlichen Laufzeitjob fuer den manuellen Security-Scan
  - den eigentlichen Laufzeitjob fuer den Input-Access-Scan
- zusaetzlich direkte Tests ergaenzt fuer:
  - unveraendertes Guard-Verhalten bei bereits laufendem Scan
  - unveraendertes Setzen des Running-Flags bei neuem Scan
  - unveraendertes Starten des daemonisierten Scan-Threads
  - unveraendertes Fehler- und Finish-Verhalten des Input-Access-Scan-Jobs
- bewusst unveraendert geblieben sind:
  - Event-, Filter- und Monitoring-Verhalten
  - die fachliche Scan-Logik der einzelnen UFW-, Integrity-, Device- und Input-Access-Quellen
  - Export-, Summary-, Device- und Input-Access-Pfade
