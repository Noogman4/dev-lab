# Repository Guard Next Steps

## Statusbild

`Repository Guard` ist in NetMon inzwischen deutlich ueber einen reinen
Platzhalter hinausgewachsen. Die V1 kann bereits lokal lesen, strukturieren,
bewerten und in der GUI nutzbar darstellen.

Der aktuelle Stand umfasst unter anderem:

- APT `.list` lesen
- Deb822 `.sources` lesen
- Flatpak-Remotes erfassen
- Baseline speichern, vergleichen und zuruecksetzen
- neue, entfernte, geaenderte und verschobene Quellen erkennen
- `signed-by`/Keyring-Pruefung
- Trustlist fuer bewusst erlaubte Hosts
- Quellen- und Findings-Filter
- Detailansicht mit Handlungshinweisen
- Chad-Kontextmenues
- Copy-/Export-Funktionen

Fazit:
Die V1 ist fachlich bereits nutzbar. Weitere Arbeit sollte jetzt vor allem die
Signalqualitaet verbessern, statt nur neue UI-Elemente zu ergaenzen.

## V1 Polish

Bevor neue groessere Security-Module gebaut werden, sollte `Repository Guard`
noch kurz gehaertet und geglaettet werden.

Empfohlene kurze Polish-Liste:

1. Praxisscans auf mehreren Systemprofilen
- Ubuntu mit Standardquellen
- System mit mehreren PPAs
- System mit Docker/Brave/VS Code
- System mit Flatpak
- Zorin- oder OEM-nahe Deb822-Quellen

2. Restliche Fehlalarme reduzieren
- doppelte Hinweise gegen echte Dubletten weiter schaerfen
- Trust-/Known-/Review-Logik mit echten Repo-Sets feinjustieren
- Hinweise mit geringem Mehrwert bewusst ruhiger behandeln

3. Finding-Texte weiter vereinheitlichen
- kurze, konsistente Titel
- klare Zusammenfassung
- keine unnötig alarmistische Sprache

4. Kontextmenues im Alltag pruefen
- Quellenliste
- Findings-Liste
- Detailbereich
- Chad-Flow

5. Exporte und Kopierpfade kurz gegenpruefen
- JSON-Export
- TXT-Export
- Copy von Findings und Details

## Empfehlung Fuer Das Naechste Modul

Nach dem kurzen V1-Polish sollte nicht noch mehr UI auf `Repository Guard`
gesetzt werden. Der sinnvollste naechste Schritt ist ein weiteres
Security-Modul.

Empfohlene Reihenfolge:

1. `Update Integrity`
2. `DNS Guard`
3. `Security Audit`

### Warum `Update Integrity` zuerst

`Update Integrity` baut fachlich am besten auf `Repository Guard` auf:

- gleiche Denkrichtung rund um Paketquellen und Update-Vertrauen
- naheliegende Naechstufe nach Repository-Pruefung
- hoher Sicherheitsnutzen ohne sofort in breite Netzwerkthemen zu gehen

Fuer eine erste V1 von `Update Integrity` waere sinnvoll:

- nur Struktur und lokale Leselogik
- keine Reparatur
- keine Dauerueberwachung
- Fokus auf Update-Quellen, Paket-Signaturpfade und erkennbare Inkonsistenzen

### Warum `DNS Guard` danach

`DNS Guard` ist ebenfalls sinnvoll, fuehrt aber frueher in netzwerknahe
Pruefungen und mehr Umgebungsabhaengigkeiten. Das passt gut als V1.1/V2 nach
dem Repository-/Update-Block.

## Konkreter Arbeitsvorschlag

Naechste Arbeitsreihenfolge:

1. `Repository Guard` kurz polieren und mit echten Scans gegenpruefen
2. V1-Spezifikation fuer `Update Integrity` anlegen
3. danach GUI-Platzhalter und Struktur fuer `Update Integrity` aufbauen

