# Architektur NetMon

## Systemarchitektur

NetMon ist eine monolithische Tk-/ttk-Desktop-Anwendung mit einer grossen zentralen `App`-Klasse und ausgelagerter Fachlogik in Controllern, Services, Core-Helfern und UI-Tab-Builders.

### Architekturueberblick

```mermaid
flowchart TD
    A[python -m netmon] --> B[netmon/__main__.py]
    B --> C[netmon/main.py]
    C --> D{CLI-Modus?}
    D -- headless --> E[run_headless_snapshot]
    D -- headless-smoke --> F[run_headless_smoke]
    D -- GUI --> G[Startup-Checks
tkinter / DISPLAY / Lock / Splash]
    G --> H[App in netmon/app.py]
    H --> I[Main Notebook]
    I --> J[System Notebook]
    I --> K[Tools Notebook]
    I --> L[Security Notebook]
    H --> M[Controller in netmon/features]
    H --> N[Services in netmon/services]
    H --> O[Core-Helfer in netmon/core]
    H --> P[Radio Core / Detached Radio]
```

## GUI-Architektur

```mermaid
flowchart LR
    App[App]
    App --> MainNB[Hauptnotebook self.nb]
    MainNB --> Log[Log]
    MainNB --> Trace[Trace]
    MainNB --> Conn[Verbindungen]
    MainNB --> DNS[DNS]
    MainNB --> Chad[Chad]
    MainNB --> Download[Download Scan]
    MainNB --> Settings[Settings]
    MainNB --> SystemMain[System]
    MainNB --> ToolsMain[Tools]
    MainNB --> SecurityMain[Security]
    SystemMain --> SystemNB[system_nb]
    ToolsMain --> ToolsNB[tools_nb]
    SecurityMain --> SecurityNB[security_nb]
```

## Backend-Architektur

```mermaid
flowchart TD
    App --> Features[features/*_controller.py]
    Features --> Services[services/*.py]
    Features --> Core[core/*.py]
    App --> Tabs[ui/tabs/*.py]
    Tabs --> App
    App --> RadioCore[netmon_radio_core.py]
    App --> SecurityParser[netmon_security_parser.py]
    App --> SecurityStore[netmon_security_store.py]
    Services --> State[state.py]
    Services --> Utils[utils.py]
```

## Konfigurations- und Laufzeitdaten

```mermaid
flowchart LR
    Config[~/.config/netmon] --> AppCfg[config.json / ai_config.json]
    Config --> Slots[HDD/Link/VPN/Privacy/Radio JSON]
    Config --> LinuxHelp[linux_help_commands.json]
    Config --> RadioCfg[radio_stations.json / radio_favorites.json / radio_settings.json]
    Data[XDG_DATA_HOME/netmon] --> ClamDb[clamav-db / Benutzersignaturen]
    State[~/.local/state/netmon] --> Sec[security / startup / repository / roots baseline Dateien]
    State --> RadioState[radio_db.json / handover / attach / detached state]
    State --> Logs[startup_error.log / logs/speedtest_history.jsonl]
    State --> Capture[captures/]
```

## GUI

- Tk-Basis ueber `tkinter`/`ttk`.
- Hauptnavigation ueber drei Ebenen: Haupttabs, verschachtelte System-/Tools-/Security-Notebooks und bereichsspezifische Widgets.
- Theme-System in `app.py` mit Light, Dark, Beige und Pop sowie Theme Studio fuer das Pop-Profil.

## Backend

- Controller-Module in `netmon/features/` kapseln UI-nahe Aktionen und Dateipfade.
- Services in `netmon/services/` kapseln Parser, Policies, Guards oder Onlinezugriffe.
- Core-Helfer in `netmon/core/` kapseln Basiskommandos, Locking, Crash-Handling, Pfad- und Formatierungslogik.
- `clamav_controller.py` verwaltet Scanarten, Schnellscan-Konfiguration, Fortschrittsanzeige, Signaturauswahl, Befunde und Quarantaene.
- `security_audit_controller.py` orchestriert RKHunter-Scans und Referenzupdates; `rkhunter_analysis_service.py` klassifiziert die Ausgabe und liefert die Gate-Evidenz.

## Netzwerkmodule

- `NetmonNetworkService`: `sudo`-nahe Adapter fuer WireGuard und UFW.
- `DNSControlService`: Resolver-/VPN-/DoT-/DNSSEC-Evaluation und Reparaturen.
- `port_analysis.py`, `speedtest.py`, Trace-/MTR-/Nmap-/iftop-/htop-Tabs: klassische Netzwerkanalyse.
- Packet-Capture-Controller: tcpdump/Wireshark/tshark-nahe Integration.

## Logging

- Startfehler werden in eine dedizierte State-Datei geschrieben.
- Laufende Aktionen landen im Log-Tab.
- Mehrere Bereiche schreiben JSON- oder JSONL-Dateien fuer Persistenz, Baselines, History oder Handover.

## Konfiguration

- XDG-basierte Config-/State-Verzeichnisse ueber `netmon/core/state.py`.
- Dateinamen zentral in `netmon/config/constants.py`.
- Viele Features bekommen ihre Pfade zentral in `App.__init__`.

## Moduldiagramm nach Codebereichen

```mermaid
flowchart TD
    subgraph Core
        C1[command.py]
        C2[state.py]
        C3[utils.py]
        C4[lock.py]
        C5[crash.py]
    end
    subgraph Services
        S1[dns_control_service.py]
        S2[ai_online_service.py]
        S3[repository_guard_service.py]
        S4[startup_guard_service.py]
        S5[path_guard_service.py]
        S6[process_guard_service.py]
        S7[rkhunter_analysis_service.py]
    end
    subgraph Features
        F1[dns_controller.py]
        F2[firewall_controller.py]
        F3[vpn_controller.py]
        F4[radio_controller.py]
        F5[security_monitoring_controller.py]
        F6[security_audit_controller.py]
        F7[repository_guard_controller.py]
        F8[clamav_controller.py]
    end
    subgraph UI
        U1[ui/tabs/*.py]
        U2[ui/widgets/*.py]
    end
    App[app.py] --> Core
    App --> Services
    App --> Features
    App --> UI
    Features --> Services
    Features --> Core
    UI --> App
```

## Unklar / Nicht dokumentiert

- Es existiert keine separate Architektur-Dokumentation im Quellcode; die hier gezeigte Architektur ist aus Importen, Buildern und Aufrufpfaden abgeleitet.
- Einzelne UI-Texte beschreiben noch Platzhalter oder spaetere Integrationsschritte; sie spiegeln nicht immer den aktuellen Implementierungsstand 1:1 wider.
