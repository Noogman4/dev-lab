# NetMon Refactoring Plan

## Leitplanken

- Refactoring nur in kleinen, einzeln testbaren Bereichen.
- Kein UI-Redesign, keine Konfigurationsformat-Aenderung, keine Aenderung von Systempfaden oder Root-Verhalten ohne ausdrueckliche Freigabe.
- Sicherheitskritische Pfade zuerst dokumentieren und mit Tests absichern, dann erst veraendern.
- Nach jedem Bereich: gezielte Tests, relevante Smoke-Tests, danach ungefaehrliche Regressionstests.
- Jeder abgeschlossene Bereich erhaelt eine eigene Dokumentation unter `docs/refactoring/areas/` und einen eigenen Commit.

## Startreihenfolge

1. Reine Hilfsfunktionen und kleine Utility-Module
2. Parser und Auswertungslogik ohne Systemschreibzugriff
3. Konfigurationsleser und Pfad-Helfer ohne Formatwechsel
4. GUI-Helfer ohne sichtbare Layout-Aenderung
5. Einzelne kleine Tabs oder Controller mit guter Testabdeckung
6. Prozessausfuehrung und Subprocess-Kapselung
7. Netzwerk-, DNS- und Repository-Pruefungen
8. Security Guards
9. Firewall-, VPN-, rkhunter-, Lynis- und ClamAV-Integration
10. Installer, Deinstaller, Packaging und andere Systemaenderungen

## Bereiche

### 01 Core Utilities

- Dateien: `netmon/core/utils.py`, `netmon/core/state.py`, `netmon/core/diagnostics.py`, `netmon/core/support_bundle.py`
- Ziel: reine Funktionen klarer strukturieren, Duplikate reduzieren, Testbarkeit erhalten.
- Tests: `tests/test_netmon_diagnostics.py`, `tests/test_netmon_state_coordinator.py`, passende gezielte Tests.
- Risiko: Pfad- und Dokumentenordner duerfen sich nicht aendern.

### 02 Command Helpers und Sudo-Sitzung

- Dateien: `netmon/core/command.py`, spaeter Aufrufer in Features.
- Ziel: Subprocess-Verhalten dokumentieren, Rueckgabewerte und Fehlertexte konsistent halten.
- Tests: `tests/test_netmon_command_core.py`, `tests/test_destructive_command_guard.py`, sicherheitsnahe Mock-Tests.
- Risiko: Root-/sudo-Verhalten, Timeouts und Locale fuer `ufw status` duerfen nicht unbemerkt wechseln.

### 03 Tooling und externe Programme

- Dateien: `netmon/core/tooling.py`, Abhaengigkeitspruefungen in `netmon/app.py`.
- Ziel: Tool-Erkennung und optionale Backends besser trennen.
- Tests: `tests/test_netmon_dependency_installer.py`, `tests/test_netmon_diagnostics.py`.
- Risiko: Installierbarkeits- und Verfuegbarkeitslogik darf keine Pakete installieren.

### 04 Security Audit und Baseline-Auswertung

- Dateien: `netmon/features/security_audit_controller.py`, `docs/security/*`, `tests/test_netmon_lynis_output.py`, `tests/test_security_baseline_docs.py`
- Ziel: grosse Auswertungsfunktionen in kleinere reine Funktionen teilen.
- Tests: gezielte Security-Baseline- und Lynis-Tests, danach komplette Suite.
- Risiko: Empfehlungen, Schweregrade, Transferpakete und angezeigte Labels muessen stabil bleiben.

### 05 Security Monitoring Controller

- Dateien: `netmon/features/security_monitoring_controller/_core.py`, `_scanning.py`
- Ziel: Scan- und UI-Zustandslogik besser abgrenzen.
- Tests: `tests/test_netmon_security_modules.py`, passende UI-Tests.
- Risiko: keine Aenderung an Scan-Kommandos, Statusanzeige oder Fehlerbehandlung.

### 06 Repository Guard

- Dateien: `netmon/services/repository_guard_service.py`, `netmon/features/repository_guard_controller.py`
- Ziel: Service-Logik und Controller-Aufgaben schaerfer trennen.
- Tests: `tests/test_repository_guard_service.py`, `tests/test_repository_guard_controller.py`.
- Risiko: Keine realen Repository- oder Paketquellen aendern; Tests muessen read-only oder gemockt bleiben.

### 07 Process Guard

- Dateien: `netmon/services/process_guard_service.py`, `netmon/features/process_guard_controller.py`, UI-Anbindung in `netmon/app.py`
- Ziel: Prozessanalyse und Anzeige sauber trennen.
- Tests: `tests/test_process_guard_service.py`, `tests/test_process_guard_controller.py`, `tests/test_netmon_process_guard_ui.py`.
- Risiko: Prozessbeendigung oder Root-Aktionen nicht veraendern.

### 08 Firewall und UFW

- Dateien: `netmon/features/firewall_controller.py`, UFW-nahe Teile in `netmon/app.py`
- Ziel: Parsing, Statusauswertung und Befehlsbau trennen.
- Tests: `tests/test_firewall_controller.py`, `tests/test_ufw_locale.py`, `tests/test_netmon_killswitch.py`.
- Risiko: Keine Lockerung von Firewall-, Killswitch- oder Spielmodus-Regeln.

### 09 VPN und WireGuard

- Dateien: `netmon/features/vpn_controller.py`, `netmon/ui/tabs/vpn_slots_tab.py`, Slot-Konfigurationen
- Ziel: Slot- und Statuslogik isolieren.
- Tests: `tests/test_netmon_vpn_slots.py`, `tests/test_vpn_slots_tab.py`.
- Risiko: Keine Aenderung an WireGuard-Aufrufen, Slot-Dateiformaten oder Root-Kommandos.

### 10 DNS und Netzwerkdienste

- Dateien: `netmon/services/dns_control_service.py`, `netmon/services/network_service.py`, `netmon/netmon_network_service.py`, `tools/netmon_network_service.py`
- Ziel: Ausgabeparsing und UI-Status trennen.
- Tests: `tests/test_netmon_dns_consistency.py`, Netzwerk-Service-Tests.
- Risiko: Keine realen DNS-/Netzwerk-Konfigurationsschreibungen in Tests.

### 11 Packet Capture

- Dateien: `netmon/features/packet_capture_controller.py`
- Ziel: Befehlsbau, Pfadpruefung und Statusauswertung separieren.
- Tests: `tests/test_packet_capture_controller.py`.
- Risiko: Capture-Kommandos und Dateiziele muessen sicher bleiben.

### 12 rkhunter, Lynis und ClamAV

- Dateien: `netmon/core/rkhunter_manager.py`, `netmon/features/clamav_controller.py`, Lynis-nahe Auswertung
- Ziel: Parser und Root-Aufrufe voneinander trennen.
- Tests: `tests/test_rkhunter_manager.py`, `tests/test_rkhunter_security_flow.py`, `tests/test_clamav_controller.py`, `tests/test_netmon_lynis_output.py`.
- Risiko: Root-Schreibpfade und Repair-Funktionen nicht ohne zusaetzliche Absicherung refaktorieren.

### 13 UI Tabs und Dialoge

- Dateien: `netmon/ui/tabs/*.py`, UI-nahe Methoden in `netmon/app.py`
- Ziel: kleine, gut getestete UI-Helfer extrahieren; keine sichtbaren Layout-Aenderungen.
- Tests: tab-spezifische UI-Tests, GUI-Smoke.
- Risiko: Source-String-Tests koennen auf Formatierung reagieren; bei Bedarf inhaltlich robuster machen.

### 14 Radio und Funktionsmodule

- Dateien: `netmon/netmon_radio_core.py`, `netmon/netmon_radio_app.py`, `netmon/ui/tabs/radio_tab.py`, `netmon/features/fun_controller.py`
- Ziel: Status- und Launcher-Logik isolieren.
- Tests: `tests/test_netmon_radio_module.py`, `tests/test_radio_tab.py`, `tests/test_netmon_fun_module.py`.
- Risiko: Keine Aenderung an gespeicherten Radio-Konfigurationen oder externen Player-Aufrufen.

### 15 Packaging, Website und Audit-Artefakte

- Dateien: `scripts/build_netmon_deb.sh`, `packaging/*`, `site/*`, Audit-PDF-Skripte
- Ziel: Build-Skripte lesbarer machen, ohne Ausgabeformate zu aendern.
- Tests: `tests/test_netmon_deb_packaging.py`, Website-/Audit-Tests, relevante Build-Checks.
- Risiko: Artefakt-Namen, Versionen und Downloadpfade duerfen nicht unbeabsichtigt wechseln.

## Bereichsablauf

Fuer jeden Bereich:

1. Analyse in `docs/refactoring/areas/NN-name.md` anlegen.
2. Bestehende Tests pruefen und bei Bedarf Verhaltenstests ergaenzen.
3. Kleine Refactoring-Aenderung mit `apply_patch`.
4. Direkt `compileall` fuer betroffene Dateien.
5. Gezielte Bereichstests.
6. Relevante Smoke-Tests.
7. Vollstaendige ungefaehrliche Regression: mindestens `ruff`, dateiweise Black fuer geaenderte Python-Dateien und `pytest`.
8. Ergebnis im Bereichsdokument festhalten.
9. Gezielt stagen, Diff pruefen, Commit erstellen.
