# Cleanup Report NetMon

Dieser Bericht dokumentiert nur Befunde. Es wurden keine automatischen Bereinigungen ausgefuehrt.

## Methodik

- API-Inventur per AST ueber die Python-Module des Projekts.
- Unused-Checks mit `ruff --select F401,F841` auf aktivem Code: **ohne Treffer**.
- Zusatzlauf ueber das gesamte Repository zeigte **3 ungenutzte Imports** in Backup-Testdateien unter `backups/...`.
- Heuristik fuer potenziell tote Funktionen: Regex-Referenzsuche im Projekt/Testcode; Treffer mit `0` oder `legacy_*` sind nur **Kandidaten**, keine endgueltigen Loeschfreigaben.

## Befunde

| Datei / Bereich | Problem | Empfehlung | Risiko |
| --- | --- | --- | --- |
| `backups/netmon_backup_*/tests/test_netmon_hdd.py` | `ruff` meldet dort ungenutzte `types`-Imports. | Backup-Baum separat pflegen oder von Qualitaetslaeufen ausschliessen. | Niedrig |
| `netmon/app.py`, `netmon/lang/*.json` | Mehrere Platzhaltertexte fuer Dokumentation, Video, Lizenz und Linux-Hilfe sind noch im UI sichtbar. | Platzhalter durch produktive Inhalte oder klar deaktivierte UI-Zustaende ersetzen. | Mittel |
| `requirements.txt` / `netmon/main.py` | Der GUI-Startpfad benoetigt `tkinter`, die Python-Abhaengigkeitsdateien dokumentieren das aber nicht direkt. | Installationsdokumentation und Packaging um den `python3-tk`-Hinweis ergaenzen. | Mittel |
| `netmon/features/*_controller.py` | Mehrfach vorhandene generische App-Helfer wie `_app_value`, `_app_var_set` und `_app_list`. | Gemeinsames Helper-Modul fuer Controller anlegen. | Mittel |
| `netmon/app.py` | Wiederholte lokale Hilfsfunktionen fuer Auswahl-/Kontextmenues | Generische Auswahl-/Kontextmenu-Helfer extrahieren. | Mittel |
| `netmon/features/radio_controller.py` | Mehrere `legacy_*`-Funktionen haben in der heuristischen Projektsuche keine externen Treffer. | Altpfade manuell gegen UI-/Dispatch-Aufrufe pruefen und danach dokumentieren oder entfernen. | Mittel |
| `netmon/netmon_radio_core.py` | Potenziell tote Funktion `radio_entrypoint_path` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_load_radio_runtime` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_save_radio_favorites` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_update_radio_header` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_refresh_radio_favorites_list` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_refresh_radio_station_table` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_refresh_radio_ui` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_play_radio_station` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_toggle_selected_favorite` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |
| `netmon/features/radio_controller.py` | Potenziell tote Funktion `legacy_add_custom_station` (heuristischer Referenztreffer: 0). | Direkte und indirekte Aufrufe pruefen; erst danach entfernen oder dokumentieren. | Mittel |

## Potenziell tote Funktionen (heuristisch)

Nur Kandidaten mit **0** Regex-Treffern im Projekt-/Testcode:

- `netmon/netmon_radio_core.py` Zeile `55`: `radio_entrypoint_path`
- `netmon/features/radio_controller.py` Zeile `542`: `legacy_load_radio_runtime`
- `netmon/features/radio_controller.py` Zeile `628`: `legacy_save_radio_favorites`
- `netmon/features/radio_controller.py` Zeile `1098`: `legacy_update_radio_header`
- `netmon/features/radio_controller.py` Zeile `1111`: `legacy_refresh_radio_favorites_list`
- `netmon/features/radio_controller.py` Zeile `1185`: `legacy_refresh_radio_station_table`
- `netmon/features/radio_controller.py` Zeile `1247`: `legacy_refresh_radio_ui`
- `netmon/features/radio_controller.py` Zeile `3539`: `legacy_play_radio_station`
- `netmon/features/radio_controller.py` Zeile `3830`: `legacy_toggle_selected_favorite`
- `netmon/features/radio_controller.py` Zeile `3862`: `legacy_add_custom_station`
- `netmon/features/radio_controller.py` Zeile `3923`: `legacy_delete_selected_station`
- `netmon/features/radio_controller.py` Zeile `3979`: `legacy_play_favorite_selection`
- `netmon/features/firewall_controller.py` Zeile `1594`: `dedupe_vpn_ufw_rules`
- `netmon/features/firewall_controller.py` Zeile `1650`: `ufw_has_outgoing_port_rule`
- `netmon/features/chad_controller.py` Zeile `370`: `get_chad_inline_input`
- `netmon/features/chad_controller.py` Zeile `380`: `clear_chad_inline_input`
- `netmon/features/chad_controller.py` Zeile `401`: `guard_chad_inline_input`
- `netmon/features/chad_controller.py` Zeile `421`: `guard_chad_inline_delete`
- `netmon/features/fun_controller.py` Zeile `11`: `module_available`
- `netmon/features/security_monitoring_controller.py` Zeile `1435`: `security_query_log_level`

## Kommentar-/Placeholder-Marker

- `netmon/app.py` Zeile `1504`: "Linux Hilfe: Vorbereitung aktiv – Integration folgt später.",
- `netmon/app.py` Zeile `12724`: "Die UI ist vorbereitet, die eigentliche Scan-Anbindung folgt später schrittweise.\n"
- `netmon/app.py` Zeile `19979`: "Backend-Logik folgt später."

## Unklar / Nicht dokumentiert

- Die Heuristik fuer tote Funktionen erkennt keine dynamischen Aufrufe, Attributverkettungen oder String-basierten Dispatch-Pfade.
- Doppelte Logik wurde ueber normalisierte AST-Dumps gesucht; das erzeugt bewusst auch viele triviale Wrappergruppen und ist daher nur als Hinweis zu lesen.
