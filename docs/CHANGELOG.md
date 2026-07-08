# Changelog

Automatisch aus der Git-Historie des Repositories erzeugt.

## 2026-07-07 - Version 1.1.16

- Release-Artefakte fuer den aktuellen Stand erneut gebaut.
- Website- und Download-Verweise des Security-Audits auf Runde 6 aktualisiert.
- Site-Bundle erzeugt jetzt den aktuellen Audit-Alias `security-audit-r6.html` und liefert `netmon_security_audit_2026_r6.pdf` mit aus.

## 2026-07-05 - Version 1.1.16

- Debian-Paketversion auf `1.1.16` angehoben.
- Release-Skripte, Doku-Build und Website-Downloadverweise auf `1.1.16` aktualisiert.
- Secure-Browser-Integration und Sprachschluessel in den aktuellen Paket- und Dokumentationsstand uebernommen.

## 2026-06-29 - Version 1.1.15

- Debian-Paketversion auf `1.1.15` angehoben, um den stabilen Recovery-/Backup-Stand neu auszurollen.
- Website-, Download- und Build-Referenzen auf `1.1.15` umgestellt.
- Produktdoku und Downloadseiten verweisen jetzt auf das aktuelle Sicherheits-Audit Runde 4 fuer `1.1.15`.
- Defense-in-Depth nachgezogen: WireGuard-Import warnt jetzt vor Hook-Direktiven wie `PostUp`/`PreDown`.

## 2026-06-28 - Version 1.1.14

- rkhunter-`WEB_CMD` auf trusted Binary-Pfade begrenzt; PATH-Hijacking ueber user-kontrollierte `wget`/`curl`-Treffer wird verworfen.
- Agent-Runner begrenzt `black`-, `ruff`-, `pytest`- und `ls`-Pfadargumente jetzt auf das Repository.
- Fun-Launcher startet nur noch validierte Python-Launcher innerhalb des verwalteten Spieleordners.
- Radio-Station-URLs aus externen APIs auf erlaubte Stream-Schemas begrenzt (`http`, `https`, `rtsp`, `rtmp`).
- Unerlaubte Stations-URLs werden bereits bei der Normalisierung verworfen und nicht mehr an `mpv` oder ICY-Metadatenabrufe weitergereicht.
- Website-Branding auf `NetMonRoots` vereinheitlicht und Header mit Banner-Icon erweitert.
- Download-, SEO- und Release-Verweise auf Paketversion `1.1.14` angehoben.
- Website-Build erwartet jetzt `netmon_1.1.14_all.deb` und erzeugt passende Release-Hashes.
- `Aktuelles` / `Updates` als zentrale Statusseiten fuer Freigaben, Testlabor-Hinweise und bekannte Themen eingefuehrt.
- About-Dialog prueft online gegen `latest-version.json` und verweist bei neueren Website-Releases auf die Downloadseite.
- LUKS-Mount-Pfad fuer Dev-Lab und installierte Pakete angeglichen; Paketabhaengigkeiten fuer `udisks2` und `cryptsetup` geschaerft.
- Support-Bereich um sichtbaren Datenschutzhinweis vor dem Versand von Diagnosepaketen erweitert.

## 2026-06-21 - Version 1.1.13

- Speedtest um konfigurierbare Server-ID erweitert.
- Speedtest zeigt jetzt zusätzlich Servername und Server-ID im Ergebnisbereich an.
- Speedtest-History und Debug-Ausgaben enthalten jetzt auch den verwendeten Server.
- WireGuard-Endpoint-Verarbeitung auf feste IP-Adressen verschärft.
- Hostnamen in WireGuard-Endpoints werden für Killswitch-/UFW-Handshake-Regeln nicht mehr stillschweigend übernommen.
- NetMon zeigt jetzt einen Hinweis, wenn ein WireGuard-Profil Hostnamen statt fester Endpoint-IP verwendet.
- ClamAV-Quarantäne- und Temp-Verzeichnisse gegen Symlink-Missbrauch gehärtet.
- AI-Bildimport (`image_to_data_url`) auf erlaubte Bildtypen und Pfade im Benutzer-Homeverzeichnis begrenzt.
- Deinstaller entschärft: Paket- und optionale Abhängigkeitsentfernung nutzt jetzt `apt remove` statt `apt purge`.
- Deinstaller-Texte und Rückmeldungen an die entschärfte Remove-Strategie angepasst.

## 2026-06-14 - Version 1.1.10

- Debian-Paketierung bis `1.1.10` konsolidiert.
- Paket enthaelt jetzt den aktuellen Deinstaller `netmon-uninstall` inklusive Desktop-Eintrag.
- Deinstaller bereinigt optional:
  - NetMon-Paket
  - Launcher-/Menue-Reste
  - Benutzerdaten, Dokumente und Caches
  - NetMon-VPN-/WireGuard-Reste
  - referenzierte NetworkManager-WireGuard-Connections
  - optional alle Profile unter `/etc/wireguard` fuer Testsysteme
  - DNS-/DoT-/NetworkManager-Overrides
  - optionale Test-Abhaengigkeiten
- Setup-Tab erweitert um Systemwartungsbuttons fuer:
  - `apt update`
  - `apt upgrade -y`
  - `apt autoremove -y`
  - `apt clean`
  - Menue-Refresh
  - Menue- und Icon-Cache-Refresh
- Security-Haertung nachgezogen:
  - WireGuard-Profilpfade gegen Path-Traversal abgesichert
  - Root-Datei-Helper in `app.py` und `rkhunter_manager.py` auf Allowlists begrenzt
  - Repo-Pfadpruefung fuer Agent-Dateilesezugriffe
  - `agent/runner.py`-Allowlist fuer lokale Shell-Kommandos verengt
  - Roots-Baseline-Guard-Root-Reads auf erlaubte Pfade begrenzt
- Startup-Guard robuster gemacht:
  - Worker-Ausnahmen blockieren den Guard nicht mehr still
  - Fehlerpfade setzen Status und UI sauber zurueck
- DNSSEC-Ausgabe bereinigt:
  - konfigurierter Modus und echter Validierungstest werden getrennt dargestellt
- VPN-Profilliste korrigiert:
  - NetMon mischt fuer WireGuard-Profile nicht mehr beliebige NM-`vpn`-Connections ein,
    sondern nur noch echte NM-`wireguard`-Connections.

- `2026-03-07` `5ceb443e` Initial commit
- `2026-03-07` `4429bb26` Set up dev container workspace
- `2026-03-07` `f7b0619d` Format code with black
- `2026-03-07` `82b539a0` Fix pytest import path and black target version
- `2026-03-07` `6656618b` Add makefile and VS Code settings
- `2026-03-07` `27a62cf4` Agent core: tools + runner + netmon integration
- `2026-03-08` `725a74ba` netmon: fix layout-related indentation and traceroute helper structure
- `2026-05-02` `e334324a` refactor(netmon): extract phase 1 startup and core helpers
- `2026-05-02` `e9239f8f` refactor(netmon): extract phase 2 ui widget helpers
- `2026-05-02` `85a56da6` refactor(netmon): continue phase 4 controller extraction
