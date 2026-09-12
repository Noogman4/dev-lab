# Guided Tour Tab Definitions

## Ziel

Die reine Zusammensetzung der Tab-Tour-Definitionen wird neben den bereits
ausgelagerten Primaerdefinitionen im Tour-Spezifikationsmodul gebuendelt.

## Aenderungen

- `netmon/ui/tour_specs.py` enthaelt
  `build_guided_tour_tab_definitions(app)`.
- Der Helper normalisiert Tour-IDs, ueberspringt leere IDs und erstellt Titel
  sowie Schritte unveraendert aus den vorhandenen App-Spezifikationen.
- Die umfangreichen text- und UI-nahen Tab-Spezifikationen verbleiben bewusst
  in `App`, damit der Schnitt klein bleibt.

## Tests

- Direkter Test fuer gueltige und leere Tour-IDs in
  `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Weitere Auslagerungen in diesem Bereich sollten jeweils zusammenhaengende
Spezifikationsgruppen betreffen, nicht einzelne Textfragmente.
