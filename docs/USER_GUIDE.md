# Benutzeranleitung NetMon

## Einfuehrung

NetMon ist eine Linux-Anwendung mit grafischer Oberfläche auf Basis von `tkinter`/`ttk`. Der Code verbindet Netzwerkwerkzeuge, DNS-/Firewall-Steuerung, Sicherheitspruefungen, Radio, Theme Studio, Linux-Hilfe, Cleanup-Funktionen und Chad-Analyse in einer einzigen Anwendung.

## Was ist NetMon?

NetMon ist laut Codebasis eine Desktop-Anwendung fuer Netzwerk- und Security-Aufgaben mit zusaetzlichen Hilfsfunktionen. Der zentrale Einstiegspunkt ist `netmon/main.py`, die Hauptklasse ist `App` in `netmon/app.py`.

## Fuer wen ist NetMon gedacht?

- Fuer Linux-Nutzer, die DNS, Firewall, VPN, Security-Events und Netzwerk-Tools ueber eine GUI bedienen wollen.
- Fuer Nutzer, die Logik in Tabs statt in einzelnen Shell-Kommandos nutzen moechten.
- Fuer Entwickler oder Power-User, die zusaetzlich Radio, Theme Studio, Linux-Hilfe und Chad-Analyse verwenden.

## Installation

### Voraussetzungen

- Python `>=3.11` laut `pyproject.toml`.
- GUI-Unterstuetzung ueber `tkinter` laut Startpfad in `netmon/main.py`.
- Python-Pakete aus `requirements.txt`: `psutil`, `PySide6`.
- Optionale Pakete im Code: `Pillow` fuer Splash/Logo-Verarbeitung, `requests` fuer Onlinezugriffe, `openpyxl` fuer Linux-Hilfe-Import.

### Installation unter Linux

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m netmon --headless
./.venv/bin/python -m netmon
```

Wenn beim GUI-Start `tkinter` fehlt, verweist `netmon/main.py` auf `sudo apt install -y python3-tk`.

### Abhaengigkeiten

- In vielen Bereichen werden externe Linux-Tools nur verwendet, wenn sie vorhanden sind, z. B. `ufw`, `wg-quick`, `resolvectl`, `traceroute`, `mtr`, `nmap`, `iftop`, `htop`, `tcpdump`, `wireshark`, `flatpak` oder `projectM`.
- Der Code prueft fehlende Tools an mehreren Stellen und gibt Hinweise im UI oder Log aus.

## Bedienung

### Netzwerkueberwachung

- **Zweck:** Die Tabs `Trace`, `Verbindungen`, `MTR`, `Nmap`, `iftop` und `htop` bilden den Kern fuer Netzwerkbeobachtung und klassische Netzwerktests.
- **Beschreibung:** Navigation ueber Haupttab `Trace`/`Verbindungen` sowie Tools-Untertabs.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Trace-, Verbindungen- und Nmap-Ansicht.
- **Typische Anwendung:** Typische Nutzung: Hosts pruefen, Hops analysieren, offene Ports scannen, Traffic beobachten.

### DNS Guard und DNS-Steuerung

- **Zweck:** Der DNS-Tab kombiniert DNS-Check, DNS-Profile, DNS Guard und DNS-over-TLS.
- **Beschreibung:** Die Auswertung steckt im `DNSControlService`; der App-Code fuehrt Statusvariablen fuer Resolver, Konflikte, DNS Guard und DoT.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: DNS-Tab mit DNS Guard und DoT-Profilen.
- **Typische Anwendung:** Typische Nutzung: Resolver pruefen, Abweichungen erkennen, DoT-Konfiguration setzen.

### Firewall und Security-Monitoring

- **Zweck:** Der Security-Bereich enthaelt Firewall/UFW, Security-Events, Process Guard, Startup Guard, Repository Guard, Roots Baseline Guard, ClamAV, Lynis, RKHunter und Packet Capture.
- **Beschreibung:** Die Oberflaechen entstehen in `netmon/ui/tabs/security_tabs.py`; die Logik steckt in separaten Controllern.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Security-Notebook mit Firewall- und Monitoring-Ansicht.
- **Typische Anwendung:** Typische Nutzung: UFW-Status pruefen, Security-Logs sichten, Baselines erstellen, Paketmitschnitte starten.
- **VPN/UFW-Hinweis:** Nach einem erfolgreichen VPN-Profilwechsel synchronisiert NetMon die referenzierten Interface- und UDP-Endpoint-Regeln wieder mit UFW, auch wenn der Killswitch aus ist.
- **Haertungshinweis:** Der Lynis-/Haertungsbereich verwaltet Baseline-Transferpakete
  und kann freigegebene Kernel-/UFW-Haertung anwenden. Bei UFW-sysctl-Konflikten
  nennt NetMon `/etc/ufw/sysctl.conf` als Ursache; `log_martians` kann dort
  dauerhaft auf den NetMon-Sollwert gesetzt werden.

### Backup

- **Zweck:** Der Backup-Tab buendelt Timeshift-Start/-Pruefung, Desktop-Datensicherung
  und den Export eigener NetMon-Ordner.
- **Beschreibung:** Die NetMon-Sicherung exportiert ausgewaehlte Ordner unter
  `Dokumente/NetMon`. Wenn `Security` ausgewaehlt ist, wird auch der
  Security-Unterordner inklusive Baseline-Transferpaketen mitgesichert.
- **Bedienregel:** Baseline-Transferpakete werden im Haertungs-Tab bearbeitet,
  nicht im Backup-Tab. Der Backup-Tab enthaelt deshalb nur Sicherungs- und
  Oeffnen-Aktionen fuer die NetMon-Ordner.
- **Timeshift:** `Timeshift pruefen` aktualisiert den Backup-Status, schreibt
  einen Logeintrag und zeigt eine kurze Rueckmeldung mit Timeshift-, Snapshot-
  und Root-Status.

### Radio

- **Zweck:** Der Radio-Tab ist ein eigener eingebetteter Player mit Stationen, Favoriten, EQ, Miniplayer und optionalem projectM-Visualizer.
- **Beschreibung:** Funktionen liegen in `netmon/netmon_radio_app.py`, `netmon/netmon_radio_core.py` und `netmon/features/radio_controller.py`.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Radio-Tab mit aktueller Station und projectM.
- **Typische Anwendung:** Typische Nutzung: Senderdatenbank laden, Station abspielen, Favoriten pflegen, Player losloesen.
- **Standalone-Verhalten:** Das losgeloeste externe Radio startet nur noch im Darkmode; dort gibt es keine Theme-Umschaltung mehr.

### Chat / Chad

- **Zweck:** Chad bietet lokale Prompt-Erzeugung und optionale Onlineanalyse.
- **Beschreibung:** Es gibt zwei Tabs: Analyse und Einstellungen. Onlinezugriffe laufen ueber `AiOnlineService`, Prompt-Aufbereitung ueber `AiAnalysisService`.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Chad Analyse und Chad Einstellungen.
- **Typische Anwendung:** Typische Nutzung: Log-/Security-/DNS-Ausgaben zusammenfassen und erklaeren lassen.

### Systeminformationen

- **Zweck:** Im Bereich `System` liegen Untertabs fuer allgemeine Systemansicht, HDD, Links und VPN-Slots.
- **Beschreibung:** Die Builder liegen in `netmon/ui/tabs/system_tab.py`, `hdd_tab.py`, `links_tab.py` und `vpn_slots_tab.py`.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: System-Notebook mit Status, HDD und Links.
- **Typische Anwendung:** Typische Nutzung: Laufende Systemdaten, HDD-Slots, Schnelllinks und VPN-Profile pflegen.
- **Link-Slots rechts:** Der Schnellzugriff bietet 20 frei beschreibbare Slots fuer interne Systemlinks oder externe HTTP-/HTTPS-Ziele. Vorhandene Belegungen der bisherigen Slots 1 bis 15 bleiben bei der Erweiterung erhalten.
- **VPN-Slots rechts:** Der Schnellzugriff bietet 10 VPN-Slots in einheitlicher Groesse. Vorhandene Belegungen der bisherigen Slots 1 bis 5 bleiben erhalten; die Slots 6 bis 10 werden bei bestehenden Konfigurationen leer ergaenzt.

#### VPN-Profile und Statusanzeige

- Eine markierte Zeile im VPN-Slot-Tab bestimmt das zu bearbeitende Profil auch dann, wenn das Formularfeld noch leer ist.
- Beim Loeschen eines Profils bereinigt NetMon normale VPN-Slots, primaere VPN-Slots und die Privacy-VPN-Auswahl, sofern sie auf dieses Profil verweisen.
- Nach einem erfolgreichen Profilwechsel fragt NetMon die oeffentliche IP und das Exit-Land neu ab. Die VPN-Ampel im Kernstatus wird nach Abschluss der Abfrage automatisch aktualisiert.

### Speedtest und Server-ID

- Das optionale Feld `Server-ID` legt einen festen Speedtest-Server fest. Ein leeres Feld verwendet die automatische Serverauswahl des installierten Speedtest-CLI.
- Der Bedienblock ist vertikal aufgebaut: oben `Server-ID`, darunter `Speichern`, dann `Server-IDs abrufen`, `Speedtest starten` und `Speedtest-Verlauf`.
- `Server-IDs abrufen` fragt asynchron bis zu 20 verfuegbare beziehungsweise nahe Server ab und schreibt ID, Anbieter, Ort, Land und vorhandene Entfernungsangaben in das NetMon-Log.
- Die gewuenschte ID kann anschliessend in das Feld `Server-ID` eingetragen und mit `Speichern` uebernommen werden. Die Abfrage traegt keine ID automatisch ein und startet noch keinen Geschwindigkeitstest.
- Unterstuetzt werden sowohl das offizielle Ookla-CLI `speedtest` als auch das Python-Werkzeug `speedtest-cli`; die konkret verfuegbare Serverliste wird vom jeweiligen Online-Dienst geliefert.

### Secure Browser

- **Zweck:** Der Haupttab `Secure Browser` erstellt fuer ausgewaehlte Webdienste getrennte, gehaertete Firefox-Instanzen mit jeweils eigenem Profil.
- **Installationsort:** Neue Instanzen liegen gemeinsam unter `Dokumente/NetMon/Secure Browser`; NetMon legt den Ordner beim ersten Zugriff automatisch an. Ein abweichender XDG-Dokumentenordner wird beruecksichtigt.
- **Privatsphaeregewinn:** Cookies, Website-Speicher, Verlauf, Logins und Einstellungen bleiben vom normalen Browser und von anderen Secure-Browser-Instanzen getrennt. Das reduziert dienstuebergreifende Wiedererkennung und verhindert, dass mehrere sensible Webanwendungen ungewollt denselben lokalen Browserzustand teilen.
- **Hardening:** Je nach Sicherheitsprofil koennen Telemetrie, Studies, Pocket, Sync, WebRTC, Formular-/Suchvorschlaege und spekulative Netzwerkzugriffe deaktiviert werden. Strenger Tracking-Schutz, HTTPS-Only und blockierte Drittanbieter-Cookies verringern weitere Datenabfluesse.
- **Website-Filter:** Im Whitelist-Modus werden standardmaessig alle Ziele blockiert und nur konfigurierte Domains erlaubt. Notwendige Login-, Zahlungs- oder CDN-Domains muessen bewusst ergaenzt werden.
- **Cookie-Entscheidung:** Dauerhafte Cookies und Logins bieten Komfort, erhalten aber wiedererkennbare Kennungen. Ohne Cookie-Persistenz werden Sitzungen und lokale Spuren beim Beenden konsequenter entfernt.
- **Sicherer Einstieg:** Zuerst Webseite, Domains und Sicherheitsprofil festlegen, danach den `Dry-Run` pruefen und erst anschliessend mit `Anlegen` installieren.
- **Grenzen:** Der Secure Browser macht nicht anonym. Webseiten sehen weiterhin die oeffentliche IP, koennen Fingerprinting einsetzen und erkennen angemeldete Konten. VPN oder Tor, Browser-Updates und eine enge Whitelist bleiben eigenstaendige Schutzbausteine.
- **Tour:** Unter `Setup -> Tour` steht `Secure Browser` als eigene deutsche oder englische Tour bereit. Die `Volle Tour` enthaelt diesen Abschnitt automatisch.
- **Deinstallation:** Der NetMon-Deinstaller fragt separat `Installierte Secure Browser ebenfalls deinstallieren? [y/N]`. Bei `N` bleiben Browser, Profile und Starter auch dann erhalten, wenn andere NetMon-Dokumente entfernt werden. Bei `Y` entfernt der Deinstaller die dedizierte Browser-Ablage, erkannte Legacy-Container und deren NetMon-Menueeintraege.

### Scanfunktionen

- **Zweck:** Download-Scan, ClamAV, Lynis, RKHunter, Startup Guard, Repository Guard und Roots Baseline Guard sind die wichtigsten Scan-/Pruefpfade.
- **Beschreibung:** Mehrere Bereiche enthalten Baseline-, Vergleichs-, Export- und Trustlist-Logik.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Scan-/Audit-Ansicht.
- **Typische Anwendung:** Typische Nutzung: Baselines erstellen, Veraenderungen vergleichen, Findings exportieren.

### ClamAV-Scans

- **Schnellscan-Pfade:** `Schnellscan-Pfade` oeffnet einen Dialog fuer die Standardordner `Downloads`, `Desktop`, `Dokumente` und `Documents`. Zusaetzliche eigene Ordner lassen sich hinzufuegen und wieder entfernen.
- **Speicherung:** Die Auswahl bleibt in den NetMon-Einstellungen erhalten. `Standard` aktiviert wieder alle vorhandenen Standardordner und entfernt die eigenen Eintraege aus der Auswahl.
- **Ausschluesse:** Beim Schnellscan werden Cache, Papierkorb, Steam-Ordner und Snap-Daten unter dem Benutzerverzeichnis ausgelassen, sofern diese Ordner vorhanden sind.
- **Scanarten:** Der ClamAV-Bereich bietet Schnellscan, frei gewaehlten Ordnerscan und Systemscan. Der Schnellscan ist nur so klein und schnell wie die dort ausgewaehlten Ordner.
- **Fortschritt:** Die Laufzeit beginnt mit dem eigentlichen Scan und wird waehrenddessen weitergezaehlt. Die verlaessliche Zahl gescannter Dateien kommt aus der abschliessenden ClamAV-Zusammenfassung; bei ruhiger `--infected`-Ausgabe kann sie waehrend des Laufs noch bei `0` stehen.
- **Abbruch:** `Scan abbrechen` beendet den laufenden ClamAV-Prozess kontrolliert. Ein Schnellscan hat zusaetzlich ein Zeitlimit von 15 Minuten.
- **Signaturen:** Ein Update ohne root-Rechte speichert ClamAV-Signaturen unter `XDG_DATA_HOME/netmon/clamav-db` beziehungsweise `~/.local/share/netmon/clamav-db`. NetMon verwendet nur ein eigenes, nicht fuer andere Nutzer zugaengliches Verzeichnis mit vorhandenen `.cvd`- oder `.cld`-Dateien.
- **Funde:** Erkannte Dateien werden zuerst als Befunde gespeichert. Quarantaene und Wiederherstellung bleiben getrennte, vom Benutzer ausgeloeste Aktionen.

#### Laufenden ClamAV-Scan im Terminal pruefen

```bash
ps -o pid,etime,%cpu,cmd -C clamscan
```

`ELAPSED` zeigt die bisherige Laufzeit und `%CPU` die aktuelle Prozessauslastung. Die vollstaendige, nicht abgeschnittene Kommandozeile inklusive Scanpfaden zeigt:

```bash
ps -efww | grep '[c]lamscan'
```

Eine hohe CPU-Auslastung bedeutet normalerweise, dass ClamAV noch arbeitet. `clamscan --infected` liefert jedoch keine verlaessliche Live-Dateinummer; die endgueltige Anzahl steht erst nach Abschluss in der Scan-Zusammenfassung.

### RKHunter-Auswertung und Referenzupdate

- **Klassifizierung:** NetMon ordnet relevante RKHunter- und `dpkg -V`-Meldungen als erwartete Systemaenderung, pruefenswert oder kritisch ein.
- **Ausgabe:** Die Auswertung zeigt Kurzbewertung, relevante Auffaelligkeiten, Risiko, konkrete Handlungsempfehlungen und typische Fehlalarme.
- **Entwicklerumgebungen:** VS Code, Codex, Dev-Container und Docker werden nur erwaehnt, wenn eine tatsaechliche Warnzeile oder ein weiteres Risikosignal vorliegt.
- **Referenzupdate:** Der Button `Vertrauenswuerdige Referenz uebernehmen` bleibt deaktiviert, bis ein vollstaendiger Scan niedriges Risiko meldet und `dpkg -V` nur erwartete Aenderungen zeigt.
- **Bestaetigung:** `sudo rkhunter --propupd` wird ausschliesslich nach einer ausdruecklichen Bestaetigung ausgefuehrt. NetMon startet diesen Befehl niemals automatisch.
- **Nach dem Update:** Ein erfolgreiches Referenzupdate entzieht die Freigabe sofort. Vor einem weiteren Update ist ein neuer vollstaendiger Scan erforderlich.

### Logs

- **Zweck:** Der Log-Tab sammelt App-Ausgaben und kann an andere Bereiche gekoppelte Log-Links enthalten.
- **Beschreibung:** Beispiel: Nach `show_firewall_status_clean()` wird ein Link `Zur Firewall springen` angehaengt.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Log-Tab mit Sprunglink.
- **Typische Anwendung:** Typische Nutzung: Statusmeldungen lesen und aus dem Log direkt in relevante Tabs springen.

### Theme Studio

- **Zweck:** Der Tools-Untertab `Theme Studio` dient zum Anpassen des Pop-Testprofils.
- **Beschreibung:** Es gibt Funktionen fuer Vorschau, Anwenden, Speichern, Laden und Ruecksetzen.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Theme Studio.
- **Typische Anwendung:** Typische Nutzung: Farben testen und Profile in den Dokumente-Ordner schreiben.

### Linux-Hilfe

- **Zweck:** Die Linux-Hilfe zeigt CSV-/JSON-basierte Kommandoeintraege mit Kategorien, Risiken und Details.
- **Beschreibung:** Die obere Eintragsliste bietet per Rechtsklick normale Chad-Prompts und den Eintrag `Als Prompt mit PDF`. Dieser PDF-Prompt ist fuer externe Erklaerung und PDF-Erstellung gedacht; NetMon erzeugt diese PDF nicht lokal.
- **PDF-Bibliothek:** Die untere Bibliothek importiert heruntergeladene PDFs, zeigt Metadaten und Vorschau, oeffnet PDFs per Doppelklick oder Button und erlaubt per Rechtsklick das Loeschen der PDF inklusive JSON-Metadaten.
- **Screenshot-Platzhalter:** Screenshot-Platzhalter: Linux-Hilfe.
- **Typische Anwendung:** Typische Nutzung: Befehl nachschlagen, PDF-Prompt kopieren, externe PDF herunterladen und ueber `PDF importieren` in NetMon anzeigen.

## Fehlerbehebung

| Problem | Ursache im Code | Loesung / Workaround |
| --- | --- | --- |
| GUI startet nicht | `tkinter` fehlt oder `DISPLAY` ist nicht gesetzt (`netmon/main.py`) | `python3-tk` installieren oder `--headless` verwenden; bei Remote-Umgebungen X11/Wayland weiterreichen. |
| NetMon startet nicht erneut | Instanz-Lock aktiv (`acquire_netmon_instance_lock`) | Laufende Instanz beenden oder alten Prozess pruefen. |
| Onlineanalyse funktioniert nicht | `OPENAI_API_KEY` fehlt (`AiOnlineService`) | API-Key als Umgebungsvariable setzen. |
| Linux-Hilfe erzeugt keine PDF direkt | Der aktuelle Workflow ist bewusst auf Prompt-Kopie, externen PDF-Build und Import ausgelegt | Oben `Als Prompt mit PDF` nutzen, PDF extern erstellen/herunterladen und unten ueber `PDF importieren` laden. |
| projectM laesst sich nicht starten | projectM ist optional und wird gesondert erkannt | projectM/Flatpak-Pfade pruefen; im Radio-UI den Installationshinweis nutzen. |
| Packet Capture / Wireshark fehlt | Wireshark-/tshark-Launcher nicht installiert | Wireshark installieren; der Packet-Capture-Bereich enthaelt einen Installationshinweis. |
| DNS-/Firewall-Aktionen scheitern | Viele Systemaktionen benoetigen `sudo -n` oder eine frische `sudo`-Session | Sudo-Session erneuern und mit passender Linux-Umgebung arbeiten. |
| Secure Browser erreicht eine benoetigte Seite nicht | Der Website-Filter erlaubt nur die konfigurierte Domain-Liste | Dry-Run und Whitelist pruefen; nur die konkret benoetigten Login-, Zahlungs- oder CDN-Domains ergaenzen. |
| ClamAV-Schnellscan dauert unerwartet lange | Zu viele oder grosse eigene Scanpfade, Archive, viele kleine Dateien oder langsame Datentraeger | Unter `Schnellscan-Pfade` die Auswahl verkleinern; Prozessstand mit `ps -o pid,etime,%cpu,cmd -C clamscan` pruefen. |
| ClamAV zeigt waehrend des Scans `0` Dateien | `clamscan --infected` liefert die verwertbare Dateisumme erst in der Abschlussausgabe | Laufzeit und Prozess im Terminal beobachten; die endgueltige Dateizahl nach Scanende ablesen. |

## Bekannte Probleme

| Ursache | Beobachtung | Loesung |
| --- | --- | --- |
| `Linux Hilfe` fuehrt riskante Befehle nicht direkt aus | Der Bereich ist als Referenz-, Prompt- und Bibliotheksfunktion ausgelegt | Befehle pruefen, Prompts extern nutzen und PDFs ueber die Bibliothek verwalten. |
| Sprachpaket-Hinweis nennt spaetere Vollumsetzung | Sprachunterstuetzung ist vorhanden, aber der Hinweistext ist noch konservativ | Sprachdateien in `netmon/lang/` pruefen und bei Bedarf erweitern. |
| Lizenz-/Dokumentations-/Video-Links enthalten Platzhaltertexte in `app.py` | Nicht alle Hilfe-/Info-Links sind produktiv angebunden | Externe Hilfe nur verwenden, wenn konkrete Inhalte hinterlegt sind. |

## FAQ

1. **Wie starte ich NetMon ohne GUI?**
   `python -m netmon --headless` fuehrt den Headless-Snapshot aus.

2. **Wie pruefe ich nur, ob die GUI einmal startet?**
   `python -m netmon --headless-smoke` erstellt die GUI einmal und beendet sie wieder.

3. **Welche Themes kann ich direkt beim Start waehlen?**
   `--theme` akzeptiert laut `netmon/main.py` die Werte `dark`, `light`, `beige` und `pop`.

4. **Wo speichert NetMon seine Konfiguration?**
   Standardmaessig unter `~/.config/netmon` bzw. `XDG_CONFIG_HOME/netmon`.

5. **Wo speichert NetMon Laufzeit- und Statusdateien?**
   Standardmaessig unter `~/.local/state/netmon` bzw. `XDG_STATE_HOME/netmon`.

6. **Warum startet die GUI nicht?**
   Im Startpfad werden fehlendes `tkinter`, fehlendes `DISPLAY`, Tk-Fehler und weitere Bootstrap-Fehler explizit behandelt. NetMon schreibt dabei ein Startprotokoll nach `~/Documents/NetMon/diagnostics` bzw. `~/Dokumente/NetMon/diagnostics` und erzeugt zusaetzlich strukturierte Diagnoseberichte als `netmon-*.json`.

7. **Wie sende ich Fehlerprotokolle oder Diagnoseberichte an den Support?**
   Im Bereich `Einstellungen -> Support / Diagnose` kann der Benutzer ein `Supportpaket erzeugen`. Dieses ZIP landet unter `~/Documents/NetMon/support` bzw. `~/Dokumente/NetMon/support` und enthaelt das aktuelle Start-/Crash-Protokoll sowie den neuesten Diagnosebericht. Zusaetzlich gibt es im About-/Bugreport-Bereich ein Formular, dessen Angaben als Nutzermeldung in das Supportpaket aufgenommen werden.

   Vor dem Export zeigt NetMon im Support-Bereich ausserdem einen sichtbaren Datenschutzhinweis an: Diagnosepakete dienen nur der Fehleranalyse, koennen aber je nach Fall Hostnamen, Benutzernamen, Dateipfade oder IP-Adressen enthalten und sollten vor dem Versand kurz geprueft werden.

8. **Darf NetMon mehrfach parallel laufen?**
   Nein. `netmon/main.py` verwendet einen Instanz-Lock und beendet weitere Starts mit einer Fehlermeldung.

9. **Wie aktiviere ich DNS Guard?**
   Im DNS-Tab gibt es den Schalter `DNS Guard aktivieren`; Statusvariablen und Logmeldungen werden im Code gesetzt.

10. **Was macht DNS Guard?**
   Er ueberwacht die aktiven DNS-Server, bewertet Abweichungen und kann je nach Zustand eine Auto-Korrektur anstossen.

11. **Wie erkenne ich, ob DoT aktiv ist?**
   Die App fuehrt DoT-Statusvariablen wie `dot_status_var`, `dot_server_var` und `dot_last_test_var`.

12. **Wo finde ich den Radio-Bereich?**
   Als `Radio`-Tab im verschachtelten Tools-Notebook.

13. **Kann ich den Radio-Player losloesen?**
   Ja. Der Code in `netmon/netmon_radio_core.py` und `netmon/features/radio_controller.py` verwaltet Host-/Handover-/Attach-Dateien fuer eingebetteten und losgeloesten Betrieb.
   Das losgeloeste Standalone-Radio laeuft dabei aktuell ausschliesslich im Darkmode.

14. **Wo liegt die Radio-Datenbank?**
   Im State-Verzeichnis, standardmaessig als `radio_db.json` und `radio_db_meta.json`.

15. **Wie speichere ich Theme-Studio-Profile?**
   Das Theme Studio bietet `Theme speichern` und `Theme laden`; Profile landen unter `~/Documents/NetMon/ThemeStudio` oder `~/Dokumente/NetMon/ThemeStudio`.

16. **Wirkt Theme Studio auf alle Themes?**
   Nein. Laut UI-Hinweis wirkt Theme Studio nur auf das Testprofil `Pop`.

17. **Wie funktioniert Chad-Onlineanalyse?**
   Der Online-Service liest `OPENAI_API_KEY` und sendet Requests an `/v1/responses`.

18. **Was passiert ohne API-Key?**
   Der Online-Service antwortet mit `Kein API-Key gesetzt` und fuehrt keine Onlineanalyse aus.

19. **Wo finde ich System- und Security-Funktionen?**
   Im Hauptnotebook gibt es die Bereiche `System`, `Tools` und `Security` mit jeweils eigenem Unter-Notebook.

20. **Gibt es einen Packet-Capture-Export nach Wireshark?**
   Ja. Packet-Capture-Controller und UI enthalten Wireshark-/tshark-Erkennung und einen Button `In Wireshark oeffnen`.

21. **Wo sehe ich Logs?**
   Im Tab `Log`; dort existiert auch der Link aus dem Firewall-Status direkt in den Firewall-Bereich.

22. **Wie erkennt NetMon eine neue Version?**
   Im About-Dialog kann NetMon die aktuelle Website-Version ueber `netmonroots.com/latest-version.json` pruefen. Wenn online eine neuere Version gemeldet wird, kann NetMon direkt auf die Downloadseite weiterleiten.

## Unklar / Nicht dokumentiert

- Eine formale Lizenzdatei wurde im Repository nicht gefunden.
- Ein Maintainer-/Kontaktabschnitt mit belastbarer Kontaktadresse wurde nicht gefunden.
- Fuer einige Platzhalterbereiche (z. B. Dokumentations- oder Video-Links im UI) ist kein produktiver Inhalt im Repository hinterlegt.
- Fuer mehrere Systemaktionen ist die Zielumgebung implizit Linux mit passenden Tools; eine distributionsuebergreifende Installationsmatrix ist im Code nicht dokumentiert.
