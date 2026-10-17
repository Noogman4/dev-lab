# App.py Residualplan 2026-09-05

## Ziel

Nach dem mergefaehigen Zwischenabschluss sollen weitere `app.py`-Schnitte nur
noch dort passieren, wo sie klar testbar sind und die Modulgrenzen bereits
existieren. Kein breiter Move-only-Umbau vor dem Zwischenmerge.

## Groesste verbleibende Methoden

AST-Auswertung auf `netmon/app.py`:

| Zeilen | Start | Methode |
| ---: | ---: | --- |
| 3657 | 2216 | `__init__` |
| 1990 | 7128 | `_guided_tour_tab_specs` |
| 848 | 24780 | `build_settings_tab` |
| 693 | 29951 | `build_lynis_tab` |
| 655 | 9203 | `_build_quickstart_tour_steps` |
| 577 | 27294 | `build_chad_settings_tab` |
| 423 | 20925 | `apply_settings_from_ui` |
| 412 | 26705 | `build_theme_studio_tab` |
| 373 | 23047 | `_run_download_scan` |
| 324 | 39319 | `_internet_on_restore_sequence` |

## Sichere Folgeschnitte

1. Guided-Tour-Spezifikationen
   - Kandidaten: `_guided_tour_tab_specs`, `_build_quickstart_tour_steps`,
     `_build_security_tour_steps`, `_build_download_scan_tour_steps`,
     `_build_radio_tour_steps`.
   - Ziel: reine Daten-/Builder-Funktionen in ein eigenes Tour-Modul ziehen.
   - Risiko: niedrig bis mittel; Source-String-Tests und Uebersetzungsschluessel
     koennen empfindlich reagieren.
   - Tests: `tests/test_netmon_diagnostics.py`, UI-/Tour-nahe Tests,
     volle Suite.

2. Settings-Tab und Settings-Sync
   - Kandidaten: `build_settings_tab`, `_build_settings_backup_tab`,
     `_sync_settings_vars_from_settings`, `apply_settings_from_ui`.
   - Ziel: Tab-Builder und reine Payload-Sync-Helfer trennen.
   - Risiko: mittel; viele Tk-Variablen und Persistenzfelder.
   - Tests: `tests/test_netmon_settings_tab.py`,
     `tests/test_netmon_lynis_output.py` fuer Backup-/Baseline-Verkabelung,
     volle Suite.

3. Lynis-/Baseline-UI-Builder
   - Kandidat: `build_lynis_tab`.
   - Ziel: UI-Aufbau in `netmon/ui/tabs/security_tabs.py` oder ein dediziertes
     Lynis-Tab-Modul ziehen; Controller-Logik bleibt in
     `security_audit_controller.py`.
   - Risiko: mittel; viele Button-Callbacks und Treeview-Spalten.
   - Tests: `tests/test_netmon_lynis_output.py`,
     `tests/test_security_baseline_docs.py`, volle Suite.

## Spaeter, nicht vor dem Zwischenmerge

- `__init__`: erst weiter zerlegen, wenn die Initialisierung nach Themen
  in risikoarme Init-Helfer gruppiert ist. Das ist ein groesserer Umbau.
- Netzwerk-/DNS-Sequenzen am Ende von `app.py`: technisch wertvoll, aber wegen
  Root-/NetworkManager-/VPN-Zustandslogik nur mit enger Mock-Abdeckung anfassen.
- Standalone-Radio (`netmon_radio_app.py`): nach dem Zwischenmerge separat
  planen; nicht mit `app.py`-Restarbeiten vermischen.

## Aufwand

- Mergefaehiger Zwischenabschluss: erreicht.
- Guided-Tour-Spezifikationen: ca. 0,5 bis 1 Tag.
- Settings-Tab/Synchronisierung: ca. 1 bis 2 Tage.
- Lynis-/Baseline-UI-Builder: ca. 1 Tag.
- Weitere `__init__`-Zerlegung: ca. 2 bis 4 Tage, nur wenn wirklich gewuenscht.
