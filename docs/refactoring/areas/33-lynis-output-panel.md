# Lynis Output Panel

## Ziel

Der reine Tk-Aufbau fuer Lynis-Zusammenfassung und Ausgabefeld wird aus
`App.build_lynis_tab()` in das bestehende Security-Tab-Modul verschoben.

## Aenderungen

- `build_lynis_output_panel(app, audit_tab)` erstellt Summary, Scrollbar und
  das deaktivierte Lynis-Textfeld inklusive Platzhalter.
- `App.build_lynis_tab()` delegiert nur diesen Widget-Aufbau und aktualisiert
  anschliessend wie bisher die Security-Baseline.

## Tests

- Der Lynis-UI-Quelltest prueft Delegation und die zentrale Widget-Verkabelung.
- Lynis-Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

Der Lynis-Aktions- und Filterbereich kann als naechste UI-Gruppe folgen.
