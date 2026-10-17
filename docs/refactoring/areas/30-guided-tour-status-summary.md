# Guided Tour Status Summary

## Ziel

Die textuelle Fortschrittszusammenfassung der primaeren Guided Tours wird von
der App-UI getrennt und direkt testbar gemacht.

## Aenderungen

- `guided_tour_status_text(app)` erstellt die uebersetzte Zusammenfassung.
- Der Helper behandelt gemischten Fortschritt, vollstaendige Abschluesse und
  noch nicht begonnene Touren.
- `App` delegiert ueber die bestehende private Methode.

## Tests

- Direkte Tests fuer alle drei Statuszustaende in
  `tests/test_guided_tour_specs.py`.
- Tour-nahe Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Der Launcher-Katalog bleibt der naechste groessere deklarative Tour-Bereich.
