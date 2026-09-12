# Guided Tour Completion Query

## Ziel

Die Abfrage eines gespeicherten Guided-Tour-Abschlusses wird neben der
Fortschrittsnormalisierung als reiner Datenhelper bereitgestellt.

## Aenderungen

- `is_guided_tour_completed(raw, tour_name)` normalisiert IDs und liefert
  fuer fehlende oder falsche Werte stets `False`.
- `App.is_guided_tour_completed()` delegiert mit dem unveraenderten
  Settings-Rohwert.

## Tests

- Direkter Test fuer normalisierte IDs, deaktivierte und fehlende Flags sowie
  leere Tour-IDs in `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Weitere Tour-Arbeit fokussiert den Launcher-Katalog als eigenen grossen,
deklarativen Block.
