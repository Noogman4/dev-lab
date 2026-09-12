# Guided Tour Launcher Presentation

## Ziel

Die reinen Darstellungsregeln der Guided-Tour-Launcher werden von den
Tk-Widget-Aktualisierungen getrennt.

## Aenderungen

- `netmon/ui/tour_specs.py` enthaelt Helper fuer Startlabel,
  Fortschrittsmarker und Titel abgeschlossener Touren.
- `App` delegiert weiterhin ueber kompatible private Methoden.

## Tests

- Direkter Test fuer offene und abgeschlossene Touren sowie leere Titel in
  `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Der Launcher-Katalog bleibt als groesserer deklarativer Move und wird nur mit
eigenem Strukturtest angefasst.
