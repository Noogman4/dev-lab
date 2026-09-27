# Changelog

Automatisch aus der Git-Historie des Repositories erzeugt.

## 2026-09-19 - Version 1.1.21

- Umfangreiche Tab-UI-Builder wurden in ihre jeweiligen Tab-Module ausgelagert. Die Oberflaeche bleibt funktional gleich, waehrend die Codebasis klarer strukturiert und besser wartbar wird.
- Der Debian-Installer veraendert keine aktiven DNS-Profile mehr und stellt bei Upgrades noch vorhandene DNS-Altzustaende frueherer Pakete wieder her.
- Der Firefox-Basisimport akzeptiert nur regulaere TAR-Dateien und Verzeichnisse und begrenzt Download-, Member- und Extraktionsgroesse.
- Paket-, Doku- und Website-Build beziehen ihre Version aus einer kanonischen Quelle; ein Konsistenzcheck blockiert abweichende Release-Metadaten.
- Produktive Release-Bundles erfordern Minisign-Schluesselmaterial und verifizieren die erzeugte Signatur noch im Build.
- Der Minisign-Public-Key mit ID `54BF5F1867BDD004` ist in `SECURITY.md` und als kanonische Repository-Datei gepinnt; abweichende Build-Keys werden abgelehnt.

## 2026-07-19 - Unreleased

- UFW-Statusprüfung sprachunabhängig umgesetzt.
- UMASK-027-Pruefung wertbasiert und mit nachvollziehbaren Quellen umgesetzt.
- UFW-Regelerkennung korrigiert: nummerierte Firewall-Regeln werden nun sprachunabhängig erkannt und gezählt.
- Home-Verzeichnisprüfung erweitert: Rechte, Eigentümer und optionale ACLs werden nun automatisch bewertet.
- APT-Prüfung fachlich korrigiert: verfügbare Paketupdates werden nun von tatsächlichen Sicherheitslücken klar abgegrenzt.
- Prüfung kritischer Systemdateirechte erweitert: Dateirechte, Eigentümer und Gruppen werden nun automatisch gegen sichere Standardwerte bewertet.
- Secure-Boot-Prüfung erweitert: Secure-Boot-Status, UEFI-Plattformmodus und profilabhängige Bewertung werden nun getrennt dargestellt.
- Lynis-/Haertungsdiagnose erweitert: NetMon erkennt UFW-sysctl-Konflikte in `/etc/ufw/sysctl.conf` fuer `log_martians` und `rp_filter` und nennt die UFW-Quelle in der Begruendung.
- UFW-Haertung erweitert: `log_martians` kann dauerhaft in `/etc/ufw/sysctl.conf` auf den NetMon-Sollwert gesetzt werden; vorher wird ein datiertes Backup angelegt.
- Backup-Tab bereinigt: Timeshift zeigt beim Pruefen sichtbare Rueckmeldung, doppelte Timeshift-Startbuttons und redundante Transferpaket-Aktionen wurden entfernt.

## 2026-07-18 - Version 1.1.19

- DNS-Startup-Fallback und Startup-Reparatur fuer verwaiste Killswitch-Zustaende robuster gemacht.
- Nach einem erfolgreichen VPN-Profilwechsel synchronisiert NetMon den UFW-Sollzustand jetzt auch ohne aktiven Killswitch wieder mit den referenzierten VPN-Profilen.
- Das losgeloeste Standalone-Radio startet nur noch im Darkmode; die Theme-Umschaltung im externen Radio wurde entfernt.
- Der Speedtest-Bereich ordnet `Server-ID`, `Speichern`, `Server-IDs abrufen`, `Speedtest starten` und `Speedtest-Verlauf` klar vertikal an.
- Die Linux-Hilfe besitzt jetzt einen PDF-Prompt-Workflow: Eintraege koennen per Rechtsklick als normaler Prompt oder als `Als Prompt mit PDF` kopiert werden.
- PDF-Dokumentationen werden nicht mehr lokal erzeugt, sondern extern erstellt/heruntergeladen und anschliessend in der unteren Linux-Hilfe-Bibliothek importiert.
- Die Linux-Hilfe-Bibliothek kann importierte PDFs anzeigen, per Doppelklick oeffnen, den gespeicherten Prompt kopieren, den Dokumentenordner oeffnen und PDFs inklusive Metadaten per Rechtsklick loeschen.

## 2026-07-17 - Version 1.1.18

- Der Speedtest-Bereich kann verfuegbare Server-IDs abrufen und bis zu 20 Treffer mit Anbieter, Ort, Land und Entfernung im NetMon-Log anzeigen.
- Die Serverabfrage unterstuetzt sowohl das offizielle Ookla-CLI als auch `speedtest-cli`, laeuft im Hintergrund und veraendert die gespeicherte Server-ID nicht automatisch.
- Der ClamAV-Schnellscan besitzt frei konfigurierbare Standard- und eigene Scanordner; die Auswahl wird dauerhaft in den NetMon-Einstellungen gespeichert.
- Die ClamAV-Anzeige zaehlt die Laufzeit ab Scanstart weiter und stellt Abbruch, Abschlussstatus und technische Fehlerausgaben klarer dar.
- Schnellscan-Ausschluesse fuer Cache, Papierkorb, Steam und Snap vermeiden unnoetig grosse Standardscans; ohne gueltige Zielordner startet kein stiller Home-Komplettscan.
- Benutzerbezogene ClamAV-Signaturen liegen XDG-konform unter `~/.local/share/netmon/clamav-db` beziehungsweise `XDG_DATA_HOME/netmon/clamav-db`; Eigentuemerschaft und restriktive Rechte werden vor der Nutzung geprueft.
- Neue und geaenderte ClamAV-Oberflaechentexte sind ueber deutsche und englische Sprachschluessel angebunden.
- RKHunter-Warnungen werden als erwartete Systemaenderung, pruefenswert oder kritisch klassifiziert; bekannte Entwicklerumgebungen und typische Konfigurationsaenderungen werden nicht mehr pauschal als Sicherheitsproblem dargestellt.
- Die Analyseausgabe enthaelt immer Kurzbewertung, relevante Auffaelligkeiten, Risiko, konkrete Handlungsempfehlungen und die Einordnung typischer Fehlalarme.
- Ein vollstaendiger RKHunter-Scan wird um `dpkg -V` als zusaetzliche Vertrauensevidenz ergaenzt.
- `rkhunter --propupd` wird nur bei niedrigem Risiko, erfolgreicher Paketpruefung und ohne kritische oder ungeklaerte Befunde angeboten.
- Das Referenzupdate erfordert immer eine ausdrueckliche Bestaetigung und eine erneute Gate-Pruefung; es wird niemals automatisch ausgefuehrt.

## 2026-07-11 - Version 1.1.17

- Rechter Link-Slot-Bereich von 15 auf 20 frei beschreibbare interne oder externe Links erweitert; die fuenf neuen Buttons werden in Originalgroesse unten angehaengt und verschieben VPN-Slots sowie Security-Systemcheck entsprechend nach unten.
- Bestehende Konfigurationen mit 15 Link-Slots bleiben erhalten und werden beim Laden automatisch um die leeren Slots 16 bis 20 ergaenzt.
- Rechter VPN-Slot-Bereich von 5 auf 10 Slots erweitert; die neuen Slots 6 bis 10 werden in Originalgroesse unten angehaengt und verschieben nachfolgende Bereiche entsprechend nach unten.
- Bestehende VPN-Slot-Konfigurationen bleiben erhalten und werden beim Laden automatisch um die leeren Slots 6 bis 10 ergaenzt.
- Aktualisierter Paketbuild mit unveraenderter Versionsnummer `1.1.17` fuer die nachgezogenen VPN-, Status- und Tour-Korrekturen.
- VPN-Profile lassen sich im VPN-Tab wieder direkt aus der markierten Tabellenzeile loeschen, auch wenn das Profilfeld im Formular leer ist.
- Beim Loeschen eines WireGuard-Profils werden zugehoerige normale VPN-Slots, primaere VPN-Slots und die Privacy-VPN-Auswahl konsistent bereinigt.
- VPN-Slots starten vorhandene Profile auch dann, wenn die zwischengespeicherte Profilliste noch nicht aktualisiert wurde.
- Die VPN-Ampel aktualisiert nach einem erfolgreichen Profilwechsel die oeffentliche IP und das Exit-Land automatisch; der normale 60-Sekunden-Cache blockiert diesen Wechsel-Refresh nicht mehr.
- Der Secure-Browser-Tab ist als eigene deutsche und englische Tour im Setup verfuegbar und wird automatisch in die volle Tour aufgenommen.
- Die Secure-Browser-Tour erklaert Profiltrennung, Browser-Hardening, Domain-Whitelist, Cookie-Persistenz, Dry-Run und die Grenzen gegenueber IP-Sichtbarkeit, Fingerprinting und Kontoerkennung.
- Neue Secure-Browser-Instanzen werden XDG-konform unter `Dokumente/NetMon/Secure Browser` angelegt; der Zielordner entsteht bei Bedarf automatisch und harte benutzerspezifische Pfade wurden entfernt.
- Die nach abgeschlossener Browser-Migration nicht mehr benoetigte Legacy-Integration von `~/Programme` wurde aus Inventur, Verwaltung, Quellensuche und Deinstaller entfernt; Secure Browser verwenden ausschliesslich `Dokumente/NetMon/Secure Browser`.
- Der Deinstaller fragt Secure Browser separat mit der sicheren Vorgabe `[y/N]` ab und schuetzt sie bei `N` auch vor der allgemeinen NetMon-Dokumentenbereinigung.
- Secure-Browser-Menueeintraege zeigen nach Erstellung, Einbindung oder Aktualisierung nur noch den eigentlichen Namen wie `GitHub` oder `Sparkasse Ulm`; das stoerende Praefix `NetMon Secure Browser` bleibt auf technische Dateinamen und interne Kennungen beschraenkt.
- Die Secure-Browser-Aktualisierung behaelt vorhandene lokale PNG-/ICO-Symbole bei fehlgeschlagenem Favicon-Download und bevorzugt kompatible Raster-Icons vor SVG-Dateien; dadurch bleiben unter anderem Chad- und cPanel-Menueicons erhalten.
- Der mittlere Radio-/Uhrbereich im Kopf erhaelt eine groessere feste Hoehenreserve, damit die LCD-Uhr auch mit dem aktuellen Theme vollstaendig oberhalb der Haupttabs sichtbar bleibt.
- Mitgelieferte Log-Pics werden bei der Paketinstallation unter `Documents/NetMon/Log-Pics` beziehungsweise `Dokumente/NetMon/Log-Pics` vorbereitet.
- Debian-Paketlayout mit Lintian geprueft und auf `/usr/lib/netmon`, `/usr/share/netmon` sowie `/usr/share/doc/netmon` standardisiert.
- Paket um Debian-Copyright, komprimierten Changelog, Manpages und `md5sums` ergaenzt; Dateirechte, Icon-Groesse und Paketbeschreibung korrigiert.
- Deutsche und englische Sprachzuordnungen systematisch bereinigt; deutsche Presets zeigen in Firewall, PATH Guard, Lynis, Repository Guard und weiteren Security-Bereichen keine englischen Standardtexte mehr an.
- Security-Untertabs neu und kompakt benannt: `Devices`, `Firewall`, `Path`, `Prozesse`/`Processes`, `Repos`, `Roots`, `Autostart`, `Rootkithunter` und `Capture`.
- PATH Guard aus dem bisherigen Device-/Guard-Bereich in einen eigenen Security-Tab mit eigener Detailansicht verschoben; Ampel-, Menue-, Hilfe- und Tour-Navigation entsprechend angepasst.
- PATH-Guard-Berichte, Risiken, Schweregrade, Hinweise und Shell-Profilbefunde vollstaendig sprachabhaengig formatiert.
- Firewall-Bewertungen und Listener-Hinweise im deutschen Preset uebersetzt, englische Ausgaben bleiben ueber die englischen Sprachschluessel verfuegbar.
- Lynis-Status, Scanbezeichnungen, Abschlussmeldungen, Hinweise und Ergebnisplatzhalter fuer beide Sprachen konsistent zugeordnet.
- Repository-Guard-Oberflaeche, Berichte, Detailansichten, Filter, Vertrauensstatus und Befundtexte sprachabhaengig vereinheitlicht.
- D-Scan um `Pfad kopieren` erweitert; der Temp-Ordner-Pfad kann direkt in die Zwischenablage uebernommen werden. Die zugehoerigen Aktionen sind in zwei funktionale Button-Reihen gegliedert.
- Laufzeit- und Netzwerk-Debug-Logs verwenden jetzt vollstaendige Zeitstempel mit Datum, damit Eintraege ueber Tages- und Stundenwechsel chronologisch eindeutig bleiben.
- Sprach-, Controller-, Routing- und UI-Tests fuer die korrigierten Ausgaben und neuen Bedienwege erweitert.
- Paket-, App-, Dokumentations- und Downloadstand auf `1.1.17` angehoben.

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
