# Konfiguration NetMon

## Speicherorte

- Konfigurationsverzeichnis: `XDG_CONFIG_HOME/netmon` oder `~/.config/netmon` (`netmon/core/state.py`).
- Status-/State-Verzeichnis: `XDG_STATE_HOME/netmon` oder `~/.local/state/netmon` (`netmon/core/state.py`).
- Dokumentenverzeichnis: `~/Documents/NetMon` oder `~/Dokumente/NetMon` (`netmon/core/state.py`).
- Diagnoseordner: `~/Documents/NetMon/diagnostics` oder `~/Dokumente/NetMon/diagnostics` (`netmon/core/diagnostics.py`).
- Supportordner: `~/Documents/NetMon/support` oder `~/Dokumente/NetMon/support` (`netmon/core/support_bundle.py`).
- Theme-Studio-Profile: `~/Documents/NetMon/ThemeStudio` oder `~/Dokumente/NetMon/ThemeStudio` (`app.py`).

## Konfigurationsdateien

| Datei | Standardort | Zweck |
| --- | --- | --- |
| `config.json` | Config | App-Einstellungen (`self.netmon_config_path`) |
| `ai_config.json` | Config | Chad-/AI-bezogene Einstellungen (`self.ai_config_path`) |
| `linux_help_commands.json` | Config | Linux-Hilfe-Daten |
| `netmon_hdd_slots.json` | Config | HDD-Slot-Konfiguration |
| `netmon_link_slots.json` | Config | Link-Slot-Konfiguration |
| `netmon_vpn_slots.json` | Config | VPN-Slots |
| `netmon_primary_vpn_slots.json` | Config | Primaere VPN-Slots |
| `netmon_privacy.json` | Config | Privacy-/DNS-/VPN-Einstellungen |
| `radio_stations.json` | Config | Radio-Stationen |
| `radio_favorites.json` | Config | Radio-Favoriten |
| `radio_settings.json` | Config | Radio-Einstellungen |

## State- und Laufzeitdateien

| Datei / Ordner | Standardort | Zweck |
| --- | --- | --- |
| `radio_db.json` | State | Radio-Datenbank |
| `radio_db_meta.json` | State | Radio-DB-Metadaten |
| `radio_host_state.json` | State | Host-Status fuer eingebetteten Radio-Betrieb |
| `radio_attach_request.json` | State | Attach-Anforderung |
| `radio_standalone_attach_request.json` | State | Standalone-Attach-Anforderung |
| `radio_standalone_show_request.json` | State | Show-Anforderung fuer Standalone-Radio |
| `radio_detached_state.json` | State | Status fuer losgeloesten Player |
| `radio_handover_request.json` | State | Handover an externen Player |
| `radio_handover_ack.json` | State | Handover-Bestaetigung |
| `netmon_security_baseline.json` | State | Security-Baseline |
| `startup_guard_baseline.json` | State | Startup-Guard-Baseline |
| `startup_guard_trustlist.json` | State | Startup-Guard-Trustlist |
| `repository_guard_baseline.json` | State | Repository-Guard-Baseline |
| `repository_guard_trustlist.json` | State | Repository-Guard-Trustlist |
| `process_guard_trustlist.json` | State | Process-Guard-Trustlist |
| `roots_baseline_guard_baseline.json` | State | Roots-Baseline-Guard-Baseline |
| `roots_baseline_guard_whitelist.json` | State | Roots-Baseline-Guard-Whitelist |
| `netmon_clamav_findings.json` | State | Persistierte ClamAV-Funde |
| `captures/` | State | Packet-Capture-Dateien |
| `logs/speedtest_history.jsonl` | State | Speedtest-Historie |
| `logs/` | State | Laufzeit- und Feature-Logs, z. B. `speedtest_history.jsonl` |
| `WireGuard/` | Documents | NetMon-Importordner fuer lokale WireGuard-Profile |

## Diagnose- und Supportdateien

| Datei / Ordner | Standardort | Zweck |
| --- | --- | --- |
| `startup_error.log` | Documents/diagnostics | Startfehlerprotokoll mit Bootstrap- und GUI-Startfehlern |
| `crash.log` | Documents/diagnostics | Sammellog fuer Laufzeitabstuerze |
| `netmon-*.json` | Documents/diagnostics | Strukturierte Diagnoseberichte fuer Start- und Laufzeitfehler |
| `netmon-support-*.zip` | Documents/support | Supportpaket mit Manifest, Diagnosebericht und Fehlerprotokollen |

## Standardwerte

- App-Version laut `netmon/config/constants.py`: `1.1.17`
- Theme-Startwert: `light` als bevorzugtes Theme in `App.__init__`.
- Chad-Startmodell: `gpt-4.1-mini`.
- DNS Guard startet mit `False` / inaktiv, mehrere Statusvariablen initialisieren auf Platzhaltertexte.
- Fehler- und Supportdiagnose ist standardmaessig aktiv; Supportpakete werden bei Bedarf manuell aus der UI erzeugt.
- Der About-Dialog kann online `https://netmonroots.com/latest-version.json` pruefen und bei einer neueren Website-Version auf die Downloadseite verweisen.

## Backup / Restore

- Das Repository enthaelt Shell-Skripte fuer Backups und Restore unter `scripts/`, z. B. `backup_dev_lab.sh`, `restore_dev_lab_backup.sh` und `restore_selected_dev_lab_backup.sh`.
- Zusaetzlich existiert bereits [BACKUP_RESTORE.md](./BACKUP_RESTORE.md).
- Fuer Feature-spezifische JSON-Dateien erfolgt die Persistenz ueber `safe_write_json()` oder lokale JSON-Schreiber.

## Unklar / Nicht dokumentiert

- Es gibt keine zentrale schema-basierte Dokumentation aller JSON-Dateien.
- Defaultwerte vieler einzelner Settings liegen verteilt in `App.__init__`, `_default_settings_payload()` und Feature-Modulen; nicht jedes Setting ist separat kommentiert.

## Hinweise zu VPN-/WireGuard-Profilen

- NetMon liest WireGuard-Profile nicht nur aus Slot-JSON-Dateien, sondern auch aus:
  - `/etc/wireguard/*.conf`
  - `Documents/NetMon/WireGuard` bzw. `Dokumente/NetMon/WireGuard`
  - echten NetworkManager-`wireguard`-Connections
- Seit dem aktuellen Stand werden dabei keine allgemeinen NetworkManager-`vpn`-Connections mehr als WireGuard-Profile in den NetMon-Profilpool aufgenommen.
