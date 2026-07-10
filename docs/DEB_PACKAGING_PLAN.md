# Debian Packaging Plan

Diese Datei beschreibt die Soll-Struktur fuer `netmon` als `.deb` auf Basis des aktuellen Repository-Stands.

Aktueller dokumentierter Paketstand: `1.1.17`.

## Ziel

Die `.deb` soll die startfaehige NetMon-Anwendung enthalten, inklusive aller zur Laufzeit benoetigten Python-Module aus dem Repo, der Desktop-Integration und der statischen App-Daten. Entwicklungsdateien, Tests, Backups und Build-Artefakte gehoeren nicht ins Paket.

## Vorgeschlagene Paketstruktur

### Debian-Metadaten

- `DEBIAN/control`
- `DEBIAN/postinst`
- `DEBIAN/prerm`

### Starter und Desktop-Integration

- `/usr/bin/netmon`
- `/usr/bin/netmon-uninstall`
- `/usr/share/applications/netmon.desktop`
- `/usr/share/applications/netmon-uninstall.desktop`
- `/usr/share/icons/hicolor/256x256/apps/netmon.png`

### Applikationscode

Basisziel: `/opt/netmon/netmon/`

Direkt unter `/opt/netmon/netmon/`:

- `__init__.py`
- `__main__.py`
- `main.py`
- `app.py`
- `netmon_ops.py`
- `netmon_network_service.py`
- `netmon_state_coordinator.py`
- `netmon_security_parser.py`
- `netmon_security_store.py`
- `netmon_projectm_sidecar.py`
- `netmon_radio_app.py`
- `netmon_radio_core.py`
- `linux-befehle.csv`

Unterverzeichnisse, die komplett mitgenommen werden sollen:

- `/opt/netmon/netmon/config/`
- `/opt/netmon/netmon/core/`
- `/opt/netmon/netmon/features/`
- `/opt/netmon/netmon/lang/`
- `/opt/netmon/netmon/modules/`
- `/opt/netmon/netmon/services/`
- `/opt/netmon/netmon/ui/`

## Statische Daten und Assets

### Mitliefern

- `/opt/netmon/assets/log-pics/`
  - Quelle: `tools/Log-Pics/`
  - Zweck: Seed-Bilder fuer Log-/Overlay-Funktionen

- `features/Code-the-Classics.zip`
  - Zielpfad: `/opt/netmon/netmon/features/Code-the-Classics.zip`
  - Soll offiziell Teil des Pakets sein

- projectM-Presets
  - Sollen offiziell mit ausgeliefert werden
  - Quellen:
    - `tools/MD2 Presets Edited for projectM 4.x/`
    - optional zusaetzlich ausgewaehlte Inhalte aus `tools/mdpresets/`, falls wir diese kuratieren wollen
  - Aktueller Paketpfad: `/opt/netmon/tools/`
  - Hintergrund: Der Laufzeitcode sucht die gebuendelten Preset-Quellen aktuell repo-relativ unter `tools/`

### Optional mitliefern

- derzeit nichts weiter

## Nicht in die `.deb`

- `tests/`
- `backups/`
- `dist/`
- `.venv/`
- `venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- Repo-interne Hilfsskripte ausser dem eigentlichen Paket-Build
- alternative Icons und Dev-Artefakte ohne Laufzeitbezug

## Abhaengigkeiten

Die bisherige `control`-Datei im Build-Skript ist zu schmal und teilweise veraltet. Sie basiert noch auf einem kleineren Altpaket.

### `Depends`

Diese Abhaengigkeiten sind fuer einen normalen GUI-Start plausibel und sollten als erste Zielmenge gelten:

- `python3`
- `python3-tk`
- `python3-psutil`
- `python3-pil`
- `python3-pil.imagetk`
- `udisks2`
- `cryptsetup`

### `Recommends`

Diese Tools werden laut Code aktiv genutzt, sind aber eher Feature-bezogen als fuer den nackten Start zwingend:

- `network-manager`
- `systemd-resolved`
- `dnsutils`
- `wireguard-tools`
- `ufw`
- `traceroute`
- `mtr`
- `nmap`
- `iproute2`
- `iftop`
- `htop`
- `lynis`
- `rkhunter`
- `clamav`
- `clamav-freshclam`
- `speedtest-cli`
- `mpv`
- `whois`

### `Suggests`

Diese Komponenten sind optional oder eher Zusatzfunktionen:

- `projectm`
- `projectm-pulseaudio`
- `wireshark`
- `tshark`
- `python3-pypdf2`
- `python3-docx`
- `python3-pygame`
- `python3-pgzero`

## Hinweise zur Python-Laufzeit

- `requirements.txt` nennt aktuell `psutil` und `PySide6`.
- Der aktuelle Startpfad `python -m netmon` laeuft aber ueber `netmon/main.py` und `netmon/app.py`, die auf `tkinter` setzen.
- `Pillow` wird im Startpfad fuer Bildfunktionen verwendet.
- `requests` ist derzeit nicht hart erforderlich, weil der Online-Service auf `urllib` zurueckfallen kann.
- `PySide6` wirkt nach heutigem Stand nicht wie eine Kernabhaengigkeit des Debian-GUI-Starts von `netmon`.

## Konsequenz fuer den Builder

Der aktuelle Builder in `scripts/build_netmon_deb.sh` sollte von einer Datei-fuer-Datei-Auswahl auf eine bewusst gepflegte Paketliste umgestellt werden.

Stand `1.1.17`:

- `scripts/build_netmon_deb.sh` liefert bereits eine explizite Datei-/Ordnerliste.
- `udisks2` und `cryptsetup` sind fuer den installierten LUKS-/Mount-Pfad als `Depends` hinterlegt.
- Die AppStream-Datei `packaging/netmon.metainfo.xml` wird mit ausgeliefert, damit Software-Center die Lizenz korrekt erkennen.

Empfohlene Richtung:

1. Vollstaendige Laufzeit-Unterpakete `config`, `core`, `features`, `lang`, `modules`, `services`, `ui` uebernehmen.
2. Die benoetigten Top-Level-Dateien aus `netmon/` explizit kopieren.
3. Assets getrennt unter `/opt/netmon/assets/` oder `/usr/share/netmon/assets/` ablegen.
4. `Depends`, `Recommends` und `Suggests` aus der aktuellen Feature-Registry in `netmon/app.py` ableiten.
5. Tests und Repo-Ballast explizit ausschliessen, statt implizit wegzulassen.

## Festgelegte Entscheidungen

- `Code-the-Classics.zip` wird standardmaessig im Paket enthalten sein.
- projectM-Presets werden offiziell mit ausgeliefert.
- Konfigurations-Defaults bleiben direkt im Paket unter `netmon/config/`.
- Es wird nur `netmon` als Produktpaket gepflegt.
- `netmon.png` ist das Hauptprogramm-Icon.
- `netmon-radio.png` ist das Radio-spezifische Icon.

## Deinstaller-Stand

Der aktuelle Paketstand liefert `netmon-uninstall` als eigenen Launcher und CLI-Weg mit aus.

Der Deinstaller fragt optional per `y/n` ab:

- Paket entfernen
- Launcher-/Menue-Reste entfernen
- Benutzerdaten und Dokumente entfernen
- NetMon-VPN-/WireGuard-Reste entfernen
- alle Profile unter `/etc/wireguard` auf Testsystemen entfernen
- NetMon-NetworkManager-WireGuard-Connections entfernen
- DNS-/DoT-/NetworkManager-Reste zuruecksetzen
- UFW zuruecksetzen
- optionale Test-Abhaengigkeiten purgen

Hinweis:

- Die aggressive Option fuer `/etc/wireguard` ist bewusst nur als Testsystem-Option gedacht.
- Die normale NetMon-VPN-Bereinigung versucht weiterhin, NetMon-bezogene Reste gezielt statt pauschal zu entfernen.

## `netmon-dark`

`netmon-dark` sollte nicht als separates Debian-Paket weitergefuehrt werden.

Begruendung:

- Der Dark Mode ist bereits im Hauptprogramm eingebaut.
- In `netmon/app.py` sind `LIGHT_THEME`, `DARK_THEME`, `BEIGE_THEME` und `POP_THEME` direkt Teil von `THEMES`.
- `netmon/main.py` unterstuetzt bereits `--theme`.
- `scripts/build_netmon_dark_deb.sh` startet nur einen separaten Test-Launcher `python3 -m netmon.dark_test`.

Konsequenz:

- `netmon-dark` ist als historischer Test-/Migrationspfad zu behandeln.
- Fuer die Debian-Auslieferung sollte nur `netmon` gebaut werden.
- Falls gewuenscht, koennen wir den separaten `netmon-dark`-Builder spaeter entfernen oder archivieren.
