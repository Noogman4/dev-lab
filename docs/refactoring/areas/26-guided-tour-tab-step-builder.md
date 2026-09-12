# Guided Tour Tab Step Builder

## Ziel

Die wiederkehrende Aufbereitung von Überblick-, Ziel-, Detail- und
Abschluss-Schritten fuer Tab-Touren wird aus `App` ausgeloest.

## Aenderungen

- `netmon/ui/tour_specs.py` enthaelt
  `build_guided_tab_tour_steps(app, spec)`.
- Der Helper bewahrt Titel-, Beschreibungs-, Hint-, Aktions- und
Detail-Schritt-Semantik unveraendert.
- `App` liefert weiterhin die UI-nahe Navigation-Callback-Fabrik.

## Tests

- Direkter Test fuer Normalisierung, Aktion und Detail-Schritte in
  `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Als naechste klar getrennte Tour-Helfer kommen die Volltour-Sequenz oder eine
zusammenhaengende Spezifikationsgruppe in Betracht.
