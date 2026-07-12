# Security-Hinweise NetMon

## Netzwerkzugriffe

Im Code wurden folgende Arten von Netzwerkzugriffen gefunden:

- DNS-/Resolver-Pruefungen ueber `resolvectl`, `nmcli` und systemnahe Linux-Kommandos im `DNSControlService`.
- Netzwerk- und Portpruefungen ueber Socket-/Tooling-Pfade (`port_analysis.py`, `Trace`, `MTR`, `Nmap`, `iftop`, `Packet Capture`).
- Onlinezugriffe fuer Chad/OpenAI ueber `AiOnlineService` (`https://api.openai.com/v1/responses`).
- Radio-HTTP-Zugriffe in `netmon_radio_app.py` auf Radio-Browser-Endpunkte und Logo-/DB-Downloads.
- Repository-Guard-Pruefungen fuer APT-/Flatpak-Quellen.

## DNS-Aenderungen

- `DNSControlService` enthaelt Reparatur- und Policy-Funktionen fuer DNS-/DoT-/NetworkManager-Konfigurationen.
- Der Service nutzt u. a. `sudo -n nmcli`, `sudo -n mkdir`, `sudo -n install`, `sudo -n rm` und `sudo -n systemctl restart systemd-resolved`.
- DNS Guard kann Abweichungen erkennen und je nach Pfad Auto-Korrekturen anstossen.

## Root-Rechte / sudo

- Der generische Command-Layer prueft `sudo -n true` und kann ueber `renew_sudo_timestamp()` eine frische `sudo`-Session anfordern.
- UFW-/Firewall-, WireGuard-, DoT-, Packet-Capture-, RKHunter- und Cleanup-Funktionen enthalten `sudo`-nahe Systemkommandos.
- Der Cleanup Assistant markiert eigene `run_sudo_command`-Pfade als bestaetigungspflichtig und nutzt einen separaten `ensure_sudo_session`-Flow.

## Logging

- Startfehler enthalten `argv`, `cwd`, `DISPLAY` und optional Stacktraces in `~/Documents/NetMon/diagnostics/startup_error.log` bzw. `~/Dokumente/NetMon/diagnostics/startup_error.log`.
- Laufzeitfehler koennen zusaetzlich strukturierte Diagnoseberichte als `netmon-*.json` im Diagnoseordner erzeugen.
- Ueber `Support / Diagnose` in den Einstellungen oder ueber den About-/Bugreport-Bereich kann der Benutzer ein Supportpaket als ZIP fuer den Versand an den Support erzeugen.
- Im Support-Bereich weist NetMon vor dem Versand sichtbar darauf hin, dass Diagnosepakete systembezogene Daten wie Hostnamen, Benutzernamen, Dateipfade oder IP-Adressen enthalten koennen.
- Der Log-Tab sammelt Laufzeitmeldungen; aus einzelnen Meldungen kann in andere Tabs gesprungen werden.
- Mehrere Features persistieren strukturierte JSON-/JSONL-Dateien im Config-/State-Verzeichnis.

## Datenschutz

- `AiAnalysisService` redigiert inhaltlich mehrere sensible Muster (Bearer-Token, API Keys, E-Mail-Adressen, Home-Pfade, Passphrasen), bevor Inhalte in Prompts fliessen.
- `AiOnlineService` verwendet `OPENAI_API_KEY` aus der Umgebung und sendet Inhalte an die OpenAI-Responses-API.
- Diagnose- und Supportberichte verwenden Redaction-Helfer fuer typische sensible Werte, ersetzen aber keine manuelle Sichtpruefung vor dem Versand.
- Der sichtbare Datenschutzhinweis im Support-Tab fordert deshalb ausdruecklich zur Pruefung vor dem Versand auf und beschreibt die beabsichtigte Nutzung nur fuer Fehleranalyse und Supportbearbeitung.
- Radio- und Netzwerkfunktionen koennen externe Dienste kontaktieren; die konkreten Endpunkte sind im Code sichtbar.

### Secure Browser

- Der Secure Browser trennt Webdienste in eigene Firefox-Profile. Cookies, Website-Speicher, Verlauf, Logins und Einstellungen werden dadurch nicht automatisch mit dem normalen Browser oder anderen Secure-Browser-Instanzen geteilt.
- Das generierte Hardening reduziert unter anderem Telemetrie, Sync-, WebRTC-, Vorschlags-, Prefetch- und Drittanbieter-Cookie-Pfade. Das konkrete Verhalten haengt vom gewaehlten Sicherheitsprofil ab.
- Der optionale Firefox-Website-Filter arbeitet nach dem Prinzip `blockieren, ausser explizit erlaubt`. Eine breite Whitelist oder deaktivierter Filter reduziert die Schutzwirkung.
- Cookie- und Passwortmanager-Persistenz sind bewusste Komfort-/Datenschutzentscheidungen und sollten pro Webdienst festgelegt werden.
- Die Funktion ist keine Anonymisierung: Oeffentliche IP, Browser-/Geraete-Fingerprinting und eine Anmeldung am Benutzerkonto bleiben fuer den Webdienst erkennbar.
- Vor dem Anlegen sollte der Dry-Run geprueft werden. Browser-Updates, enge Domain-Ausnahmen und bei Bedarf ein separater VPN-/Tor-Pfad bleiben notwendig.

## Risiken

| Bereich | Risiko | Beleg im Code |
| --- | --- | --- |
| Systemkommandos | Viele Aktionen veraendern Netzwerk-, DNS- oder Firewall-Zustand auf dem Host | `sudo -n`-Kommandos in `netmon_network_service.py`, `dns_control_service.py`, `firewall_controller.py` |
| Onlineanalyse | Inhalte werden an einen externen API-Dienst gesendet | `AiOnlineService` |
| Start-Error-Logging | Startlog schreibt Umgebungsdaten und Stacktraces in Datei | `netmon/main.py` |
| Packet Capture | Rohdaten aus dem Netzwerk koennen lokal gespeichert und in Wireshark geoeffnet werden | Packet-Capture-Tab/Controller |
| Detached Radio | Handover-/Status-Dateien im State-Verzeichnis steuern Prozesswechsel | `netmon_radio_core.py` |

## Schutzmassnahmen

- Crash- und Locking-Mechanismen im Startpfad.
- Atomische JSON-Schreibfunktion `safe_write_json()` fuer viele Persistenzpfade.
- Redaction-Logik in `AiAnalysisService`.
- Sudo-Session-Pruefung vor kritischen Systemaenderungen.
- Trustlist-/Baseline-Konzepte fuer mehrere Security-Guards.

## Benutzerhinweise

- Kritische Systemfunktionen nur auf einem Linux-System mit bekannter Konfiguration und gueltiger `sudo`-Session ausfuehren.
- Onlineanalyse nur mit bewusst gesetztem API-Key und nach Pruefung des zu sendenden Inhalts nutzen.
- Packet-Capture- und Wireshark-Funktionen mit Bedacht einsetzen, da Rohdaten gespeichert werden.
- Config-/State-Verzeichnisse regelmaessig sichern, wenn Baselines, Trustlists oder Radio-Daten wichtig sind.

## Unklar / Nicht dokumentiert

- Es existiert keine zentrale Datenschutz- oder Datenaufbewahrungsrichtlinie im Repository.
- Die exakten Zugriffsmodelle fuer alle externen Radio-/Logo-Endpunkte sind nicht separat dokumentiert.

## Audit-Einordnung K1 bis K9

Die in `scripts/build_security_audit_pdf.py` aufgefuehrten Punkte `K1` bis `K9`
sind im Audit selbst nicht als bestaetigte Sicherheitsluecken bewertet, sondern
als ausgeschlossene Kandidaten mit niedriger Konfidenz.

| ID | Thema | Audit-Status | Einordnung | Aktueller Repo-Status |
| --- | --- | --- | --- | --- |
| `K1` | Git-Subcommand-Passthrough | ausgeschlossen | Lokaler Entwicklerpfad, kein LLM- oder Netzwerk-Input in `run_command()` | zusaetzlich gehaertet: Git-Subcommand-Allowlist in `agent/runner.py` |
| `K2` | WireGuard-Endpoint in UFW-Killswitch | ausgeschlossen | Profil liegt root-owned; Audit sah keinen realistischen Remote-Pfad | zusaetzlich gehaertet: Endpoint-Host wird als feste IP validiert |
| `K3` | UFW-Quelle `any` im Firewall-Formular | ausgeschlossen | beabsichtigte Admin-Funktion mit Warnung, Vorschau und Bestaetigung | unveraendert, weiter als kontextuell unkritisch bewertet |
| `K4` | Vorhersagbarer ClamAV-Temp-Pfad | ausgeschlossen | Audit sah keinen sinnvollen Code-Execution-Pfad ueber signierte ClamAV-Daten | zusaetzlich gehaertet: symlink-sichere Verzeichniserstellung |
| `K5` | Dateipfad in `image_to_data_url()` | ausgeschlossen | bewusster Upload-Fluss, Bildtypen-Restriktion, Dateidialog | zusaetzlich gehaertet: Pfad auf Benutzer-Home begrenzt |
| `K6` | WireGuard-Import via `nmcli` | ausgeschlossen | `nmcli`/NetworkManager fuehrt `wg-quick`-Hooks nicht aus | unveraendert, weiter als unkritisch bewertet |
| `K7` | WireGuard-Import via `wg-quick` | ausgeschlossen | manueller Admin-Import, kein automatischer `wg-quick up`-Pfad | unveraendert, weiter als unkritisch bewertet |
| `K8` | Shell-Snippet-Generierung im Repository-Guard | ausgeschlossen | Snippet wird nur angezeigt bzw. kopiert, nicht automatisch ausgefuehrt | zusaetzlich gehaertet: `shlex.quote()` fuer Shell-Werte |
| `K9` | Symlink-Bypass im Roots-Baseline-Guard | ausgeschlossen | Audit bewertete den praktischen Mehrwert des Bypasses als gering | zusaetzlich gehaertet: `os.path.realpath()` vor Guard-Match |

Kurz gesagt: `K1` bis `K9` sind keine bestaetigten Sicherheitsbefunde aus dem
Audit. Teile davon wurden spaeter trotzdem als Defense-in-Depth-Massnahmen
technisch gehaertet.

## Bestaetigte Findings nach dem Audit

### Radio-Station-URLs aus externem API

- Bereich: `netmon/features/radio_controller.py`
- Risiko: Low Severity
- Einordnung: bestaetigtes Finding

Radio-Stationen aus externen Quellen wie `radio-browser.info` wurden zuvor ohne
Schema-Validierung weiterverarbeitet. Dadurch konnten praepartierte URLs bis an
`mpv` und an `urllib.request.urlopen()` gelangen.

Der aktuelle Codestand haertet diesen Pfad zentral in
`normalize_station_entry()`:

- erlaubt sind nur `http`, `https`, `rtsp` und `rtmp`
- `url` und `url_resolved` werden beide normalisiert
- Eintraege mit unerlaubtem Schema werden verworfen

Ziel der Aenderung ist, unnoetige SSRF- oder lokale Protokollpfade aus
externen Stationslisten gar nicht erst in nachgelagerte Playback- oder
Metadaten-Funktionen zu uebernehmen.

### rkhunter WEB_CMD und PATH-Hijacking

- Bereich: `netmon/core/rkhunter_manager.py`
- Risiko: ehemals High Severity
- Einordnung: bestaetigtes Finding, geschlossen

Der Rueckgabewert von `shutil.which()` durfte nicht ungeprueft in
`WEB_CMD=...` fuer `rkhunter.conf` uebernommen werden, weil `rkhunter --update`
diesen Pfad spaeter mit Root-Rechten ausfuehrt.

Der aktuelle Codestand begrenzt `_preferred_web_cmd()` auf vertrauenswuerdige
Pfade:

- erlaubt sind nur Treffer unter `/usr/bin/`, `/bin/` und `/usr/local/bin/`
- user-kontrollierte Treffer wie `~/.local/bin/wget` werden verworfen
- falls nur untrusted Kandidaten gefunden werden, bleibt `WEB_CMD` leer

Ziel der Aenderung ist, PATH-Hijacking und moegliche Privilege Escalation ueber
manipulierte Benutzer-Binaries zu verhindern.

### Agent-CLI und Repo-Pfad-Confinement

- Bereich: `agent/runner.py`
- Risiko: ehemals Medium Severity
- Einordnung: bestaetigtes Finding, geschlossen

Der lokale Agent-Runner pruefte urspruenglich nur den Basisbefehl
(`black`, `ruff`, `pytest`, `ls`), aber keine uebergebenen Pfadargumente.
Dadurch konnten absolute Pfade ausserhalb des Repositories an Schreib- oder
Lese-Tools weitergereicht werden.

Der aktuelle Codestand haertet `run_command()` zusaetzlich:

- Pfadargumente fuer `black`, `ruff`, `pytest` und `ls` werden kanonisiert
- erlaubt sind nur Ziele innerhalb von `REPO_ROOT`
- auch `pytest`-Node-IDs wie `tests/test_x.py::test_name` werden korrekt auf
  den Dateipfad reduziert und geprueft

Ziel der Aenderung ist, Dateikorruption und Information Disclosure ausserhalb
des Repositories ueber Prompt-Injection oder untrusted CLI-Eingaben zu
verhindern.

### Fun-Launcher und Spielpfad-Begrenzung

- Bereich: `netmon/features/fun_controller.py`
- Risiko: ehemals Medium Severity
- Einordnung: bestaetigtes Finding, geschlossen

Der Fun-Launcher startet Python-Dateien aus dem Code-the-Classics-Bereich ueber
`subprocess.Popen(["python3", path])`. Der aktuelle Codestand begrenzt diesen
Pfad jetzt zusaetzlich:

- gestartet werden nur `.py`-Dateien innerhalb von `fun_games_dir`
- der Pfad wird per `realpath()` gegen den Spieleordner geprueft
- vorhandene NetMon-Managed-Path-Checks werden genutzt, wenn verfuegbar

Ziel der Aenderung ist, das Starten beliebiger Python-Dateien ausserhalb des
verwalteten Spielebereichs defensiv zu verhindern.
