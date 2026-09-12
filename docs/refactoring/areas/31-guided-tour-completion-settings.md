# Guided Tour Completion Settings

## Ziel

Die Normalisierung gespeicherter Guided-Tour-Fortschritte wird aus `App`
ausgelagert und fuer alle Verwender zentralisiert.

## Aenderungen

- `normalize_guided_tour_completed_settings(raw)` akzeptiert nur Mappingdaten,
  normalisiert IDs und wandelt Werte in boolesche Flags um.
- `App._guided_tour_completed_settings()` delegiert mit dem vorhandenen
  Settings-Wert.

## Tests

- Direkter Test fuer ungueltige Eingaben, leere IDs und normalisierte Werte in
  `tests/test_guided_tour_specs.py`.
- Tour- und Settings-Tests sowie volle Suite nach dem Schnitt.

## Naechster Schnitt

Der groessere Launcher-Katalog bleibt ein separater deklarativer Refactoring-
Schritt.
