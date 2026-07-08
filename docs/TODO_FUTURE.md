# TODO / Future NetMon

Diese Liste basiert nur auf expliziten Platzhaltern, Hinweistexten und sichtbaren Optional-/Vorbereitungsstellen im Code.

## Eindeutig im Code markierte Zukunfts-/Placeholder-Themen

- **Linux-Hilfesystem:** Mehrere Texte in `app.py` und `lang/*.json` sagen, dass sichere Ausfuehrung und tiefere Terminal-Integration spaeter in einem separaten Schritt folgen.
- **Dokumentation / Video / Lizenz im UI:** `app.py` enthaelt Platzhaltertexte fuer Dokumentations-Link, Erklaervideo und Lizenzinformationen.
- **Cleanup Assistant:** Das UI-Modul beschreibt sich als Shell fuer kuenftige Analyse- und Cleanup-Aktionen.
- **Security Future Modules Host:** `ui/tabs/security_tabs.py` enthaelt einen `security_future_modules_host` und Hinweistext fuer spaetere schrittweise Anbindung von Baseline-/Dateiueberwachungslogik.
- **Theme Studio Reichweite:** Das UI sagt explizit, dass Theme Studio aktuell nur auf das Pop-Testprofil wirkt.
- **Sprachpakete:** Die Spracheinstellungen enthalten einen Hinweis, dass Sprachpakete spaeter vollstaendig umgesetzt werden.

## Themen nach angefragten Bereichen

### DNS Guard Erweiterungen
- Im Code wurde **kein expliziter TODO-Hinweis** fuer einen eigenen neuen DNS-Guard-Ausbauschritt gefunden. DNS Guard selbst ist bereits implementiert.

### Pro-Modus
- Im Code wurde **kein expliziter `Pro-Modus`-Backlog-Eintrag** gefunden.

### Wireshark Integration
- Wireshark-/tshark-Integration ist bereits vorhanden (Launcher-Erkennung, Packet Capture, Open-in-Wireshark).
- Ein expliziter Zukunftseintrag fuer einen weiteren Ausbau wurde im Code nicht gefunden.

### Raspberry Pi Version
- Explizit gefunden wurde nur der Installhinweis `Install (Debian/RPi)` in den Sprachdateien.
- Eine eigene Raspberry-Pi-Variante, eigenes Packaging oder eigener Modus ist im Code nicht dokumentiert.

### Radio Datenbank
- Radio-DB-Download, Metadaten und Persistenz sind bereits implementiert.
- Ein eigener TODO-Hinweis fuer einen weiteren Radio-DB-Ausbauschritt wurde nicht explizit gefunden.

### Linux Hilfesystem
- Hier liegen die deutlichsten Zukunftshinweise im Code vor: Anzeige und Datenpflege existieren, sichere Ausfuehrung / Terminalintegration sind explizit als spaetere Schritte markiert.

## Unklar / Nicht dokumentiert

- Fuer mehrere grosse Themen wurden eher Platzhaltertexte als konkrete Roadmap-Eintraege gefunden.
- Die Git-Historie enthaelt viele Refactoring-Commits, aber keine gesonderte oeffentliche Feature-Roadmap.
