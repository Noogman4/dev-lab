# Secure Browser

Platzhalter-Modul für die spätere NetMon-Integration des Secure Browser Managers.

## Zweck

Dieses Modul bereitet die Architektur für getrennte, gehärtete Browser-Container
innerhalb von NetMon vor. Aktuell stellt es Datenmodell, Service-Skeleton,
Manager-Skeleton und einen lesenden GUI-Tab für die Inventur bestehender
Container bereit. Der Einstieg prüft per read-only Preflight, ob Builder,
Konfiguration, Firefox-Quelle und Menüpfade für die spätere Nutzung
vorhanden sind.

## Sicherheitsprinzipien

- Dry-Run zuerst
- Backup vor Änderung
- keine externen Profile löschen
- keine Container überschreiben
- keine Änderungen ohne spätere explizite Freigabe
- Zugangsdaten bleiben getrennt pro Container speicherbar

## Aktueller Stand

- Rein lesende Inventur bestehender Secure-Browser-Container
- Read-only Preflight für Builder-Skript, Konfiguration, Firefox-Quelle und Menüpfad
- Auswahl erkannter Container im Tab
- Detailansicht für Pfad, Binary, Profil, Menüeintrag und Domains
- Markdown-Export der aktuell gefilterten Inventuransicht in die Zwischenablage
- Read-only-Verifikation für ausgewählten Container
- Strukturierte Prüfung von `launcher.desktop` und Menüeintrag
- Vorschau von `start.sh` und `launcher.desktop` für den ausgewählten Container
- Explizite read-only Aktion `Launcher prüfen`
- Mehrbereichs-Viewer für `Übersicht`, `Launcher` und `Artefakte`
- Kennzahlen zur Statusverteilung der letzten Inventur
- Kompakter Risiko-Block pro ausgewähltem Container
- Schnellfilter für `Nur Risiken` und `Nur externe Profile`
- Erweiterte Kennzahlen für externe Profile, fehlende Launcher und fehlende Menüeinträge
- Erster Dry-Run-Entwurf für `Neuer Browser` mit Name, Startseite und Domains
- Erweiterter Dry-Run-Entwurf mit Vorlage, Menüname, Neue-Tab-URL und Icon-Modus
- Validierter Erstellplan im Dry-Run mit Zielordner, Builder-Vorschau und Warnhinweisen
- Interner Builder-Dry-Run ohne CLI-Dateiausgaben und ohne `--apply`
- Apply-Vorbereitung mit explizitem Bestätigungscode, weiterhin ohne Schreibpfad
- Separater `Apply ausführen`-Pfad über den bestehenden Builder mit Rückgabe von `stdout` und `stderr`
- Keine zusätzliche Paketinstallation durch NetMon für den Preflight erforderlich
- Keine automatische Erstellung oder Entfernung ohne explizite Benutzeraktion im Tab

## Geplante Funktionen

- Inventur
- Erstellen
- Registrieren bestehender Container
- Startmenü-Integration
- Favicon-Icons
- Deinstallation/Cleanup
- Update/Verify
