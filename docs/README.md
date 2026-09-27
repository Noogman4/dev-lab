# NetMon

Dokumentierter Paket- und App-Stand: `1.1.21`.

NetMon ist eine Linux-GUI fuer Netzwerk-, DNS-, Firewall-, VPN-, Security-, Radio- und Hilfsfunktionen. Der Startpfad liegt in `netmon/main.py`, die Hauptoberflaeche in `netmon/app.py`, und die Funktionslogik ist in Controller-, Service- und Tab-Module aufgeteilt.

## Kurzbeschreibung

NetMon kombiniert klassische Netzwerk-Werkzeuge, DNS-/DoT-Steuerung, Firewall- und Sicherheitspruefungen, VPN-Slots, Radio, Theme Studio, Linux-Hilfe und Chad-Analyse in einer Tk-/ttk-Oberflaeche. Der Code verwendet fuer die GUI `tkinter`, fuer den Start einen Splash-/Lock-/Crash-Flow und fuer viele Teilbereiche klar getrennte Controller- und Service-Module.

## Hauptfunktionen

- GUI-Start ueber `python -m netmon` mit optionalen Modi `--headless`, `--headless-smoke` und `--theme`.
- Haupttabs fuer Log, Trace, Verbindungen, DNS, Chad, Download-Scan, Einstellungen sowie verschachtelte Bereiche `System`, `Tools` und `Security`.
- DNS-Funktionen inklusive DNS Guard, DNS-over-TLS-Profilen und Resolver-Pruefungen.
- Firewall-, UFW-, Killswitch- und Packet-Capture-Funktionen.
- Security-Monitoring mit Security-Events, Startup Guard, Process Guard, Repository Guard, Roots Baseline Guard, ClamAV, Lynis und RKHunter.
- ClamAV-Schnellscan mit dauerhaft konfigurierbaren Standard- und eigenen Ordnern, sichtbarer Laufzeit, Abbruchfunktion sowie Fund- und Quarantaeneverwaltung.
- RKHunter-Auswertung mit deterministischer Risikoklassifizierung, ergaenzender `dpkg -V`-Pruefung und streng geschuetzter manueller Referenzuebernahme.
- Radio-Modul mit eingebetteter und losgeloester Radio-App, Datenbank-/Favoriten-/Settings-Dateien und optionalem projectM-Visualizer.
- Theme Studio fuer das Pop-Testprofil inklusive Speichern/Laden von Profilen.
- Linux-Hilfe mit Such-/Glossaransicht, Prompt-Kopie fuer externe PDF-Erstellung und importierbarer PDF-Bibliothek.
- Cleanup Assistant, HDD-/Link-/VPN-Slot-Verwaltung und Chad-Analyse.
- Secure Browser fuer getrennte, gehaertete Firefox-Instanzen pro Webdienst mit Sicherheitsprofilen, Domain-Whitelist, Dry-Run und verwalteten Cookie-/Login-Optionen.
- Gefuehrte Touren im Setup, einschliesslich einer zweisprachigen Secure-Browser-Tour mit ausfuehrlicher Datenschutz- und Grenzen-Erklaerung.
- VPN-Profilverwaltung mit konsistenter Slot-/Privacy-Bereinigung und automatischer Aktualisierung der oeffentlichen IP nach einem Profilwechsel.
- About-Dialog mit Online-Versionspruefung gegen `netmonroots.com` und automatischer Weiterleitung auf die Downloadseite bei neueren Website-Releases.
- Support-/Diagnosebereich mit lokalem Supportpaket-Export und sichtbarem Datenschutzhinweis vor dem Versand.
- Paketierter Deinstaller mit optionaler Bereinigung von NetMon-, WireGuard-, NetworkManager- und Testsystem-Resten.
- Aktueller Security-Audit-Stand fuer die Produktdoku: Runde 12 auf Basis von `1.1.21`; die PDF-Fassung von Runde 11 bleibt als Archiv erhalten.

## Screenshots

> Screenshot-Platzhalter: Hauptfenster mit Haupttabs.
>
> Screenshot-Platzhalter: Radio-Tab mit aktuellem Sender, Steuerung & EQ und projectM.
>
> Screenshot-Platzhalter: Security-Bereich mit Firewall-/Monitoring-Ansicht.

## Installation

### Im Repository deklarierte Python-Abhaengigkeiten

- `requirements.txt`: `psutil`, `PySide6`
- `pyproject.toml`: `requires-python >=3.11`

### Im Startpfad explizit vorausgesetzt oder optional importiert

- `tkinter` wird in `netmon/main.py` fuer die GUI vorausgesetzt.
- `Pillow` (`PIL`) wird im Start-Splash optional verwendet.
- `Pillow.ImageTk` wird fuer Bild-/Log-Overlay-Pfade benoetigt; unter Debian/Ubuntu ist dafuer typischerweise `python3-pil.imagetk` erforderlich.
- `requests` wird im Online-AI-Service optional verwendet; ohne `requests` faellt der Code auf `urllib` zurueck.

### Debian-Paketstand

- Aktueller Test-/Paketstand in diesem Repository: `1.1.21`
- Build-Skript: `scripts/build_netmon_deb.sh`
- Ergebnisdatei: `dist/netmon_<version>_all.deb`
- Harte Laufzeitabhaengigkeiten im Paket: `udisks2`, `cryptsetup`
- Paket liefert derzeit unter anderem:
  - `netmon`
  - `netmon-uninstall`
  - `netmon.desktop`
  - `netmon-uninstall.desktop`
  - `netmon.png`
  - `netmon-radio.png` als Radio-spezifisches Asset
  - Secure-Browser-Manager und dessen Builder-/Policy-Ressourcen
  - aktuelle HTML-/PDF-Dokumentation fuer Version `1.1.21`

### Beispiel-Setup unter Linux

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m netmon --headless
./.venv/bin/python -m netmon
```

Wenn `tkinter` fehlt, meldet `netmon/main.py` explizit den Debian/Ubuntu-Hinweis `sudo apt install -y python3-tk`.

## Erste Schritte

1. Optional im Headless-Modus pruefen: `./.venv/bin/python -m netmon --headless`
2. GUI starten: `./.venv/bin/python -m netmon`
3. Im Bereich `Settings` / `Theme Studio` Theme und Sprache pruefen.
4. DNS-, Firewall- und Security-Bereiche nur mit passender Linux-Umgebung und ggf. `sudo` nutzen.
5. Weitere Details: [USER_GUIDE.md](./USER_GUIDE.md), [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md), [CONFIGURATION.md](./CONFIGURATION.md)

## Externes Testlabor

- Fuer ein externes Linux-Testlabor auf `/media/happy/Work2/netmon-lab` siehe [LAB_WORKFLOW.md](./LAB_WORKFLOW.md).
- Ein neuer Run-Ordner laesst sich mit `scripts/lab/init_test_run.sh` vorbereiten.

## Lizenz

NetMon verweist im aktuellen Stand auf `GPL-3.0-or-later`. Relevante Dateien:

- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- AppStream-Metadaten unter `packaging/netmon.metainfo.xml`

## Kontakt

Projekt-/Support-Kontakte im aktuellen Stand:

- `info@netmonroots.com`
- `support@netmonroots.com`

## Changelog

Siehe [CHANGELOG.md](./CHANGELOG.md).
