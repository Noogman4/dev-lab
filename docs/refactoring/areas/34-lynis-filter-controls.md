# Lynis Filter Controls

## Ziel

Die beiden Lynis-Ausgabefilter werden als geschlossene UI-Gruppe aus
`App.build_lynis_tab()` verschoben.

## Aenderungen

- `build_lynis_filter_controls(app, lynis_top)` erzeugt die Filterzeile sowie
  die Buttons fuer Issues und Vollausgabe.
- Attribute, Tooltips und Controller-Callbacks bleiben unveraendert.

## Tests

- Der Lynis-UI-Quelltest sichert Delegation und beide Button-Callbacks.
- Lynis-Tests und volle Suite nach dem Schnitt.
