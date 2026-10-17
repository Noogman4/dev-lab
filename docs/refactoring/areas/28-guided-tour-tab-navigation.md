# Guided Tour Tab Navigation

## Ziel

Die gemeinsame Vorbereitung der Guided-Tour-Tabnavigation wird mit den
uebrigen Tour-Spezifikationshelfern gebuendelt.

## Aenderungen

- `build_guided_tour_tab_prepare_callable(app, selector, tab_attr)` baut die
  Navigation fuer Top-, System-, Tools- und Security-Tabs.
- Der Tab-Schritt-Builder verwendet den Helper direkt.
- `App` behaelt einen delegierenden Kompatibilitaets-Wrapper fuer bestehende
  Aufrufer.

## Tests

- Direkte Tests fuer alle Navigationstypen sowie fehlende Ziel-Tabs in
  `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Die Launcher- und Tab-Spezifikationsdaten sind der verbleibende groeßere
Tour-Block und sollten nur gruppenweise ausgelagert werden.
