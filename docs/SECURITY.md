# Security-Hinweise NetMon

## Netzwerkzugriffe

Im Code wurden folgende Arten von Netzwerkzugriffen gefunden:

- DNS-/Resolver-Pruefungen ueber `resolvectl`, `nmcli` und systemnahe Linux-Kommandos im `DNSControlService`.
- Netzwerk- und Portpruefungen ueber Socket-/Tooling-Pfade (`port_analysis.py`, `Trace`, `MTR`, `Nmap`, `iftop`, `Packet Capture`).
- Onlinezugriffe fuer Chad/OpenAI ueber `AiOnlineService` (`https://api.openai.com/v1/responses`).
- Radio-HTTP-Zugriffe in `netmon_radio_app.py` auf Radio-Browser-Endpunkte und Logo-/DB-Downloads.
- Repository-Guard-Pruefungen fuer APT-/Flatpak-Quellen.
- Die automatische Versionsabfrage im About-Dialog erlaubt ausschliesslich HTTPS auf `netmonroots.com` mit Port 443, auch nach Weiterleitungen. Jede DNS-Antwort wird vollstaendig auf oeffentliche Adressen geprueft; gemischte oeffentliche/private Antworten und Sondernetze werden abgewiesen. Verbindungen verwenden nur die geprueften numerischen Adressen und kontrollieren die Gegenstelle vor TLS/HTTP. TLS-Zertifikat und Hostname werden weiterhin geprueft. Umgebungs-Proxys werden fuer diese Abfrage ignoriert; die bisherigen Zeit-, Groessen-, Redirect- und JSON-Limits bleiben erhalten.

## DNS-Aenderungen

- `DNSControlService` enthaelt Reparatur- und Policy-Funktionen fuer DNS-/DoT-/NetworkManager-Konfigurationen.
- Der Service nutzt u. a. `sudo -n nmcli`, `sudo -n mkdir`, `sudo -n install`, `sudo -n rm` und `sudo -n systemctl restart systemd-resolved`.
- DNS Guard kann Abweichungen erkennen und je nach Pfad Auto-Korrekturen anstossen.

## Root-Rechte / sudo

- WireGuard-Profile mit `PreUp`, `PostUp`, `PreDown` oder `PostDown` werden abgewiesen. Die gemeinsame Pruefung gilt fuer alle Importwege, den privilegierten Payload-Empfaenger, direkte NM-Erstellung/Installation und die Aktivierung bereits gespeicherter Profile. Ein Hash oder ein allgemeiner Importdialog erteilt keine Hook-Freigabe. Profile und Befehlsinhalte werden nicht automatisch bereinigt oder umgeschrieben.
- Alte WireGuard-Teardown-Belege mit Hooks werden ebenfalls nicht ausgefuehrt. Betroffene Interfaces und Belege bleiben erhalten und erfordern eine bewusste administrative Bereinigung ausserhalb dieses NetMon-Ablaufs. Hookfreie Original-Belege bleiben fuer normales Teardown verwendbar, auch wenn eine spaeter geaenderte Profildatei Hooks enthaelt. Fehleranzeigen nennen nur die Direktiven, keine Befehlsinhalte oder Schluessel.
- Finding `acf_e08a86c597b7355ed23fc8aa237462bd`: 731 isolierte WireGuard-/VPN-Tests bestanden. Die Tests verwenden synthetische Profile und simulierte NM-/WG-Befehle; kein echter Hook, sudo-, VPN- oder Firewall-Aufruf wurde ausgefuehrt. Diese Hook-Sperre ersetzt keine unabhaengige Bewertung anderer L-04-Autorisierungsfragen; aeltere Berichte unter `docs/security/L-04*` dokumentieren den damaligen Stand.
- Der generische Command-Layer prueft `sudo -n true` und kann ueber `renew_sudo_timestamp()` eine frische `sudo`-Session anfordern.
- UFW-/Firewall-, WireGuard-, DoT-, Packet-Capture-, RKHunter- und Cleanup-Funktionen enthalten `sudo`-nahe Systemkommandos.
- Der Cleanup Assistant markiert eigene `run_sudo_command`-Pfade als bestaetigungspflichtig und nutzt einen separaten `ensure_sudo_session`-Flow.

### RKHunter-Referenzdatenbank

`rkhunter --propupd` kann manipulierte Dateieigenschaften als neue Referenz akzeptieren und ist deshalb besonders geschuetzt:

- Der Befehl wird niemals automatisch ausgefuehrt.
- Ein vollstaendiger RKHunter-Scan und eine erfolgreiche `dpkg -V`-Pruefung sind erforderlich.
- Rootkits, Backdoors, verdaechtige Laufzeit- oder Netzwerkfunde, manipulierte Systemprogramme, gelbe Prueffaelle und Scanfehler blockieren die Freigabe.
- Das berechnete Gesamtrisiko muss `Niedrig` sein.
- Der Benutzer muss den Vorgang ausdruecklich bestaetigen und eine sudo-Sitzung freigeben.
- Das Sicherheits-Gate wird vor dem Dialog, nach der Bestaetigung und nach der sudo-Freigabe erneut geprueft.
- Jeder neue, fehlgeschlagene oder blockierte Scan sowie jedes Referenzupdate entzieht eine vorherige Freigabe.

### ClamAV-Signaturdatenbank

- Ein benutzerbezogenes `freshclam`-Update schreibt Signaturen nach `XDG_DATA_HOME/netmon/clamav-db` oder ersatzweise `~/.local/share/netmon/clamav-db`, nicht in einen vorhersagbaren gemeinsamen `/tmp`-Ordner.
- Benutzer-Konfigurationen werden ausschliesslich ohne erhoehte Rechte verwendet. Der Datenbankpfad wird separat als `--datadir`-Argument uebergeben; Pfade mit Steuerzeichen werden vor Dateizugriffen und Update-Versuchen abgewiesen. Die temporaere Konfiguration enthaelt keine interpolierten Pfade und kein `UpdateLogFile`; Ausgaben werden ueber stdout erfasst.
- Der sudo-Fallback verwendet nur `/usr/bin/freshclam` mit `/etc/clamav/freshclam.conf`. Vor dem privilegierten Aufruf werden beide Dateien und alle uebergeordneten Verzeichnisse auf Root-Eigentuemerschaft, passenden Dateityp und fehlende Gruppen-/Fremdschreibrechte geprueft; Symlinks werden abgewiesen. Eine als Root gestartete NetMon-GUI fuehrt das Benutzerupdate nicht aus.
- NetMon erstellt den Ordner ohne Symlink-Folgen und mit Benutzerrechten. Vor `clamscan --database` werden Eigentuemerschaft, Verzeichnistyp und fehlende Gruppen-/Fremdrechte geprueft.
- Als benutzerbezogene Datenbank werden nur Verzeichnisse mit vorhandenen `.cvd`- oder `.cld`-Signaturen akzeptiert. Andernfalls wird auf eine gueltige Systemdatenbank unter `/var/lib/clamav` beziehungsweise auf die ClamAV-Standardsuche zurueckgefallen.
- Schnellscan-Pfade werden vom Benutzer ausgewaehlt und als normalisierte absolute Pfade gespeichert. Nicht mehr vorhandene Ordner werden beim Scan uebersprungen.
- Quarantaene- und Wiederherstellungspfade werden getrennt validiert; ein Fund wird nicht allein durch den Scan automatisch verschoben oder wiederhergestellt.
- Alle ClamAV-Scans verwenden einen gemeinsamen nichtblockierenden Pipe-Leser mit einer absoluten monotonen Deadline. Das Budget wird auch bei Stille, unvollstaendigen Zeilen, stetiger Ausgabe oder einem bereits beendeten Hauptprozess mit offenem Kindprozess-Pipe geprueft. Die bisherigen Scan-Zeitlimits bleiben bestehen; Download-Dateiscans zeigen Rueckgabecode 124 ebenfalls als Timeout an.
- Scanner-Ausgabe ist auf 2 MiB pro Scan und 16 KiB pro Zeile begrenzt. Es werden maximal 300 Fundzeilen und ein Diagnose-Endstueck von 64 KiB gehalten. Ein ueberschrittenes Ausgabe-, Zeilen- oder Fundlimit beendet den Scan mit Fehlercode 125 als unvollstaendig; es erteilt keine Sauber-Freigabe. Der Systemscan verwendet wie die anderen rekursiven Scans `--infected`; die abschliessende ClamAV-Zusammenfassung liefert die Gesamtzahl gescannter Dateien. Die vorgelagerte Dateizaehlung dient weiterhin nur der Fortschrittsschaetzung, nicht als Scan-Dateibudget.
- Bei Abbruch, Deadline, Budgetueberschreitung oder einem Fehler wird die eigene Scanner-Prozessgruppe mit TERM und nach maximal 0,2 Sekunden mit KILL beendet; der Hauptprozess wird mit begrenztem Wait eingesammelt und die Pipe geschlossen. Die UI fordert nur den Abbruch an, der erzeugende Worker besitzt die Bereinigung. Finding `acf_eb89be621fb4817a4260122840d80aa7` wurde mit synthetischen Scannern in der bestehenden Isolation geprueft; kein echter ClamAV-Scan, Update oder Host-Eingriff.

## Logging

- Rohtext-Logs und strukturierte Diagnose-/Supportdaten nutzen dieselbe Redaktion aus `netmon/core/log_redaction.py`. Bekannte Passwort-/Token-/API-Key-/PrivateKey-Felder, getrennte argv-Optionen und Werte, mehrzeilige private PEM-Schluessel, Authorization-/Cookie-Werte, URL-Zugangsdaten, E-Mail-Adressen und Home-Benutzernamen werden ausgeblendet. Sensible strukturierte Schluessel werden unabhaengig vom Wertformat maskiert. JSON-Logeintraege werden strukturiert redigiert, damit escapte Befehlszeichenketten gueltig bleiben. Unquotierte sensible Werte werden konservativ bis zum Zeilenende entfernt. Dies ist musterbasierte Redaktion, keine vollstaendige Anonymisierung beliebiger Inhalte.
- Der private Log-Schreibhelfer sammelt einen Eintrag ueber mehrere Schreibaufrufe bis zum Kontextende, bevor er ihn redigiert und schreibt. flush() veroeffentlicht keine ungeprueften Teilwerte. Bei mehr als 64 KiB Zeichen wird der gesamte Eintrag durch einen Auslassungsmarker ersetzt; abgeschnittene Geheimnisse oder JSON-Fragmente werden nicht gespeichert. Ein Redaktionsfehler fuehrt zu keinem Rohtext-Fallback. Runtime-/Netzwerk-Debug-Anzeige und -Zwischenspeicher werden ebenfalls gefiltert; Port-Debug-Daten bleiben JSON.
- Auch der direkte `app.py`-Bootstrap-Fehlerpfad verwendet den sicheren privaten Log-Helfer. Bereits bestehende Logs werden nicht nachtraeglich inhaltlich umgeschrieben; die Runtime-Anzeige filtert auch geladene alte Eintraege. Finding `acf_6cad9e5a324aa3312c04fc156aa348f4`: 328 isolierte Log-/Diagnose-/Support-/Systemlog-Tests bestanden; ein bestehender realer chown-Fall bleibt mangels zweiter UID uebersprungen. Tests verwenden ausschliesslich synthetische Geheimnisse und temporaere Dateien, keine vorhandenen Host-Logs oder echten GUI-Starts.
- Startfehler-, Crash-, Runtime-, Netzwerk- und Port-Debug-Logs werden ueber einen gemeinsamen geprueften Schreibhelfer mit Modus `0600` geschrieben. Eigene bestehende Logs werden vor Schreiben oder Leeren auf `0600` eingeschraenkt; Log-Verzeichnisse und die NetMon-State-/Dokumentwurzel erhalten `0700`. Uebergeordnete Benutzerverzeichnisse werden nicht umgestellt, und die Prozess-umask bleibt unveraendert.
- Pfadkomponenten werden deskriptorrelativ ohne Symlink-Folgen geoeffnet. Fremde Eigentuemer, Hardlinks, Spezialdateien und unsichere Vorfahren verhindern den Log-Zugriff. Leeren erfolgt erst nach Identitaets-/Rechtepruefung. Unsichere Pfade werden nicht durch einen ungeprueften Schreib-Fallback umgangen.
- Strukturierte Diagnoseberichte werden privat vorbereitet und ohne Ueberschreiben bestehender Namen atomar veroeffentlicht. Vorhandene Host-Logs werden durch die Entwicklungstests nicht veraendert; die Rechteanpassung erfolgt beim spaeteren Zugriff durch den korrigierten Code. Das Finding `acf_f5143e3319e9dbcaadd69a5e0b7ad782` wurde mit 186 bestandenen isolierten Tests geprueft. Ein bestehender realer chown-Test benoetigt eine zweite UID und bleibt in dieser Isolation uebersprungen; simulierte Fremdeigentuemer-Pruefungen sind bestanden.
- Startfehler enthalten `argv`, `cwd`, `DISPLAY` und optional Stacktraces in `~/Documents/NetMon/diagnostics/startup_error.log` bzw. `~/Dokumente/NetMon/diagnostics/startup_error.log`.
- Laufzeitfehler koennen zusaetzlich strukturierte Diagnoseberichte als `netmon-*.json` im Diagnoseordner erzeugen.
- Ueber `Support / Diagnose` in den Einstellungen oder ueber den About-/Bugreport-Bereich kann der Benutzer ein Supportpaket als ZIP fuer den Versand an den Support erzeugen.
- Im Support-Bereich weist NetMon vor dem Versand sichtbar darauf hin, dass Diagnosepakete systembezogene Daten wie Hostnamen, Benutzernamen, Dateipfade oder IP-Adressen enthalten koennen.
- Der Log-Tab sammelt Laufzeitmeldungen; aus einzelnen Meldungen kann in andere Tabs gesprungen werden.
- Mehrere Features persistieren strukturierte JSON-/JSONL-Dateien im Config-/State-Verzeichnis.

## Datenschutz

- Linux-Hilfe-Importe begrenzen CSV auf 8 MiB und XLSX auf eine validierte OOXML-Kopie mit 5 MiB Archivgroesse und 32 MiB entpackten Daten. Datensaetze werden zeilenweise verarbeitet: hoechstens 20.000 Datenzeilen, 64 Spalten, 200.000 Zellen einschliesslich leerer/paddierter Zellen und 8 MiB Zeichen insgesamt; einzelne Zellen bleiben auf 64 KiB Zeichen begrenzt. Wiederverwendete XLSX-Shared-Strings werden bei jeder Zellverwendung gezaehlt. Auch normalisierte Befehlsdaten unterliegen dem Gesamttextbudget.
- CSV-/XLSX-Parser und Befehlsnormalisierung laufen in einem Wegwerf-Prozess mit 512 MiB virtuellem Adressraum, 4 Sekunden CPU, 8 Sekunden Parser-Laufzeit, 64 Dateideskriptoren, keinen zusaetzlichen Benutzerprozessen und hoechstens 16 MiB Antwort. XLSX-XML ist auf 500.000 Elemente und Tiefe 64 begrenzt; DTDs, uebergrosse Dimensionen und ausserhalb der Grenzen liegende explizite/implizite Zellkoordinaten werden abgewiesen. Der Elternprozess validiert die begrenzte Antwort erneut. Es werden ausschliesslich unveraenderliche Dateikopien weitergegeben; die Originalauswahl wird vom Kind nicht erneut geoeffnet. Fehler oder Zeitueberschreitung beenden die eigene Prozessgruppe und lassen die bestehende Befehlsdatenbank unveraendert.
- Der Linux-Hilfe-Importdialog arbeitet im Hintergrund und uebernimmt nur vollstaendige Ergebnisse im UI-Thread. Gleichzeitige weitere Importe werden abgewiesen; waehrenddessen bearbeitete Daten werden nicht durch ein spaetes Ergebnis ersetzt. Finding `acf_d24f32116532c4b5fb7cb1ef2c543102`: 191 isolierte Import-, Linux-Hilfe- und OOXML-/DOCX-Regressionstests bestanden, einschliesslich realer Wegwerf-Prozesse fuer CPU-, Speicher-, Zeit- und Ausgabelimits. Keine importierten Linux-Befehle oder Host-Aktionen wurden ausgefuehrt. Die bestehenden Bestaetigungen vor einem spaeteren Terminalstart bleiben erhalten. Prozess-Ressourcenlimits sind keine Dateisystem-/Netzwerk-Sandbox.
- Chad-DOCX-Importe pruefen weiterhin die begrenzte ZIP-Kopie vor der Verarbeitung. XML-Strukturpruefung und `python-docx` laufen in einem eigenen Prozess mit hoechstens 512 MiB virtuellem Adressraum, 4 Sekunden CPU-Zeit, 32 Dateideskriptoren, keinen zusaetzlichen Benutzerprozessen und hoechstens 1 MiB Ausgabedatei. Strengere geerbte Limits bleiben erhalten. Nach 8 Sekunden verstrichener Zeit wird die eigene Prozessgruppe beendet und der Prozess eingesammelt. Die XML-Pruefung begrenzt die Struktur auf 100.000 Elemente und Tiefe 64, verbietet DTDs und begrenzt Tabellen-Spans. Die Textextraktion stoppt bei 120.000 Zeichen. Ein Hintergrundthread haelt die GUI bedienbar; pro GUI ist nur ein DOCX-Import gleichzeitig erlaubt. Das Leeren der Analyse verwirft noch ausstehende Ergebnisse. Dies sind Prozess-Ressourcenlimits, keine Dateisystem-/Netzwerk-Sandbox.
- Chad-Bilder werden beim Import als unveraenderliche Bildkopien im Speicher erfasst. Die Pfadkomponenten und die Datei werden ohne Symlink-Folgen geoeffnet; nur regulaere Dateien innerhalb des Home-Verzeichnisses bis 5 MiB werden gelesen. Bildformat und Dimensionen werden geprueft. Maximal vier Bilder mit zusammen 20 MiB koennen vorgemerkt werden. Beide API-Sendewege verwenden ausschliesslich diese Kopien und oeffnen die urspruenglichen Pfade nicht erneut. Alte Anhaenge ohne Bildkopie muessen erneut importiert werden.
- `AiAnalysisService` redigiert inhaltlich mehrere sensible Muster (Bearer-Token, API Keys, E-Mail-Adressen, Home-Pfade, Passphrasen), bevor Inhalte in Prompts fliessen.
- `AiOnlineService` verwendet `OPENAI_API_KEY` aus der Umgebung und sendet Inhalte an die OpenAI-Responses-API.
- Diagnose- und Supportberichte verwenden Redaction-Helfer fuer typische sensible Werte, ersetzen aber keine manuelle Sichtpruefung vor dem Versand.
- Der sichtbare Datenschutzhinweis im Support-Tab fordert deshalb ausdruecklich zur Pruefung vor dem Versand auf und beschreibt die beabsichtigte Nutzung nur fuer Fehleranalyse und Supportbearbeitung.
- Radio- und Netzwerkfunktionen koennen externe Dienste kontaktieren; die konkreten Endpunkte sind im Code sichtbar.

### Secure Browser

- Neu erzeugte `backup.sh`-Skripte benoetigen Python 3 und GNU tar. Sie sichern Profile mit privaten Verzeichnisrechten (0700) und Archivrechten (0600), unabhaengig von der aufrufenden Umask. Unsichere oder verlinkte Backupziele werden abgewiesen; fehlgeschlagene Archive werden nicht veroeffentlicht.
- Bereits vorhandene Container behalten ihr bisheriges `backup.sh`; dieses muss vor weiteren Backups durch die neu erzeugte Version ersetzt werden. Alte Archive und bestehende Profile erhalten durch das Update nicht automatisch neue Rechte. Neue Container und Profilverzeichnisse werden direkt mit hoechstens 0700 angelegt, ohne nachtraegliches pfadbasiertes chmod. Eine strengere Umask wird respektiert; entzieht sie dem Eigentuemer erforderliche Rechte, kann die Erstellung sicher abbrechen.

- Der Secure Browser trennt Webdienste in eigene Firefox-Profile. Cookies, Website-Speicher, Verlauf, Logins und Einstellungen werden dadurch nicht automatisch mit dem normalen Browser oder anderen Secure-Browser-Instanzen geteilt.
- Das generierte Hardening reduziert unter anderem Telemetrie, Sync-, WebRTC-, Vorschlags-, Prefetch- und Drittanbieter-Cookie-Pfade. Das konkrete Verhalten haengt vom gewaehlten Sicherheitsprofil ab.
- Der optionale Firefox-Website-Filter arbeitet nach dem Prinzip `blockieren, ausser explizit erlaubt`. Eine breite Whitelist oder deaktivierter Filter reduziert die Schutzwirkung.
- Cookie- und Passwortmanager-Persistenz sind bewusste Komfort-/Datenschutzentscheidungen und sollten pro Webdienst festgelegt werden.
- Die Funktion ist keine Anonymisierung: Oeffentliche IP, Browser-/Geraete-Fingerprinting und eine Anmeldung am Benutzerkonto bleiben fuer den Webdienst erkennbar.
- Vor dem Anlegen sollte der Dry-Run geprueft werden. Browser-Updates, enge Domain-Ausnahmen und bei Bedarf ein separater VPN-/Tor-Pfad bleiben notwendig.

## Risiken

Der einzeln verteilbare Hash-Helfer `scripts/verify_netmon_download.sh` prueft
vor jedem Nutzdatenzugriff das gesamte Manifest und dessen exakte, doppelfreie
Uebereinstimmung mit den uebergebenen Dateien. Er akzeptiert einfache ASCII-
Dateinamen und `docs/<Dateiname>` (Eingabedokumente im Ordner `docs`). Er berechnet
Hashes direkt ueber die explizit uebergebenen, ohne Symlink-Folgen geoeffneten
Dateideskriptoren. Hardlinks und Spezialdateien werden abgewiesen; Identitaet,
Groesse und Zeitstempel muessen beim Lesen stabil bleiben. Manifestnamen werden
nie als zu oeffnende Pfade verwendet. Grenzen: 64 KiB Manifest, 64 Dateien,
2 GiB je Datei und 4 GiB insgesamt. Es gibt keine temporaeren Nutzdatenkopien
und keine externe `sha256sum -c`-Ausfuehrung mehr. Python 3 ist erforderlich.
Finding: `acf_60d5f933bcfac4c965278b49e427ad7d`. Der Helfer prueft weiterhin nur
Integritaet; die separate gepinnte Signaturpruefung bleibt fuer Herkunft noetig.

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
- Eigentums-, Rechte- und Symlink-Pruefungen fuer benutzerbezogene ClamAV-Signaturen und Quarantaenepfade.

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
