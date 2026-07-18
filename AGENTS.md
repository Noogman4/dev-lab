# AGENTS.md

## Ziel
Dieses Repository ist das Grundgeruest fuer Svens AI Dev Lab.

## Regeln
- Kleine, nachvollziehbare Aenderungen
- Erst lokal testen, dann committen
- Keine unnoetigen Abhaengigkeiten
- Python-Code soll mit black formatiert werden
- Code soll mit ruff pruefbar sein
- Tests laufen mit pytest

## Arbeitsfreigaben
- Nicht-destruktive Lese- und Analysebefehle duerfen ohne Rueckfrage ausgefuehrt werden, z. B. `rg`, `sed`, `cat`, `ls`, `find`, `git diff`, `git status`.
- Lokale Qualitaetschecks duerfen ohne Rueckfrage ausgefuehrt werden, z. B. `python3 -m py_compile`, `python3 -m ruff check`, `python3 -m black --check`, `pytest`.
- Formatter duerfen auf betroffenen Python-Dateien ausgefuehrt werden, wenn dadurch nur Formatierung angepasst wird, z. B. `python3 -m black <datei>`.
- Kleine, projektbezogene Python-Tools duerfen installiert werden, wenn sie fuer Build, Test oder Lint benoetigt werden, z. B. `ruff`, `black`, `pytest`.
- Nicht-destruktive Git-Befehle duerfen ohne Rueckfrage genutzt werden. Keine automatischen Commits, keine Resets, kein Checkout fremder Aenderungen.
- Netzwerkzugriffe fuer Paketinstallation und offizielle Dokumentation sind erlaubt, wenn sie direkt zur Aufgabe gehoeren.
- Destruktive Aktionen bleiben zustimmungspflichtig, insbesondere `rm`, `git reset`, `git checkout --`, systemweite Paketentfernung oder groessere Refactorings mit unklarer Wirkung.

## Build- und GUI-Freigaben
- Lokale Build-Befehle duerfen ohne Rueckfrage ausgefuehrt werden, wenn sie nur Artefakte im Projekt oder in temporaeren Verzeichnissen erzeugen.
- Paketierung und Projekt-Builds fuer NetMon sind erlaubt, z. B. Deb-Build-Skripte aus `scripts/` oder projektbezogene Packaging-Checks.
- GUI-nahe Tests und Starts duerfen ohne Rueckfrage ausgefuehrt werden, wenn sie lokal und nicht-destruktiv sind, z. B. Tkinter-Starts, `xvfb-run`, Display-Checks oder Headless-GUI-Validierung.
- Zusaetzliche Hilfstools fuer Build und GUI duerfen installiert werden, wenn sie direkt fuer die Aufgabe benoetigt werden und keine unnoetigen Grossabhaengigkeiten einfuehren.
- Schreibzugriffe ausserhalb des Repos, systemweite Konfigurationsaenderungen oder dauerhafte Systemdienste bleiben zustimmungspflichtig.

## Struktur
- agents/    Agent-Experimente
- docker/    Container-bezogene Dateien
- scripts/   Hilfsskripte
- tools/     Kleine Werkzeuge
- docs/      Notizen und Doku
