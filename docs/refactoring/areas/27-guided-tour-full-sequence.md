# Guided Tour Full Sequence

## Ziel

Die allgemeine Zusammenstellung der Volltour wird aus `App` in das vorhandene
Tour-Spezifikationsmodul uebernommen.

## Aenderungen

- `build_guided_tour_full_sequence(app)` liefert die bereinigte, konfigurierte
  Launcher-Reihenfolge ohne Schnellstart und Volltour selbst.
- `build_full_tour_steps(app, definitions)` erzeugt den Einleitungs- und
  Abschlussrahmen und fuegt nur gueltige Tour-Definitionen ein.
- `App` delegiert weiterhin und stellt die konkrete Settings-Tab-Navigation.

## Tests

- Direkter Test fuer Reihenfolge, Ausschluesse, ungueltige Definitionen und
  die Start-/Endnavigation in `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Die verbleibenden Tab-Spezifikationen sind der grosse Tour-Block. Er sollte
nur nach thematischer Gruppierung und mit string-sensitiven Tests bewegt werden.
