# NetMon 1.1.22 – lokaler Teststand

Branch: `release/netmon-1.1.22-test`. App- und Paketversion: **1.1.22**.
Dieser Branch und das lokal gebaute Debian-Paket dienen dem Testen. Sie sind
keine Produktivfreigabe und keine Veröffentlichung auf der Website.

## Herkunft und Umfang

Übernommen wurde der eingefrorene gemeinsame V52-Kandidat aus
`backups/netmon-unification-20261031/candidate`. Sein Quellmanifest hat SHA256
`f01c77a04d2745fc2aa67d39d7f7a8d29f886c633d255d100b66c77238043295`.
Der Hauptordner entsprach vor der Überführung noch exakt allen 1079 Dateien des
gesicherten Ausgangsstands A. Beide bisherigen Quellen und die V52-Belege
bleiben in den Sicherungsverzeichnissen erhalten. Andere unversionierte
Arbeitsnotizen und Werkzeuge gehören nicht zu diesem Commit.

Enthalten sind die gemeinsamen DNS-/DoT-/WireGuard-/Firewall-Korrekturen,
Chad mit Markdown und kopierbaren Befehlen, der Analysemodus mit ein- und
aushängbarem VTE-Terminal, das Terminal-Kontextmenü, rechte Scrollbalken,
Abhängigkeitsdiagnose und die Supportadresse `support@netmonroots.com`.
Die alte Datei `d.py` wird nicht in den aktiven Arbeitsstand übertragen oder
ausgeführt; sie bleibt im eingefrorenen Kandidaten erhalten.

Zur Überführung kommen die Version 1.1.22, aktuelle Paket-/Manpage-Angaben und
eine explizite Prüfung lokaler Paketmetadaten hinzu. GUI-Testfixtures wurden
für verschiedene Schriftgrößen und den Gesamtlauf robuster gemacht: Geometrie
wird am tatsächlichen Inhalt geprüft; der GTK-Menütest erhält einen eigenen
Xvfb ohne GLX und einen eindeutigen Ergebnis-Marker. Die eigentlichen
Terminal-/Importaktionen und ihre Prüfziele bleiben bestehen. Ein Test des
installierten UFW-Parsers meldet dessen Fehlen ausdrücklich als Skip.

## Lokales Paket bauen

```sh
python3 -B scripts/check_release_consistency.py --package-only
bash scripts/build_netmon_deb.sh
```

Erwartetes lokales Ergebnis: `dist/netmon_1.1.22_all.deb`.
Der SHA256-Nachweis liegt daneben als `netmon_1.1.22_all.deb.sha256`.
Der Build verweigert das Überschreiben eines bestehenden Pakets.

Die öffentliche Version bleibt in `site/latest-version.json` unverändert bei
1.1.21. Website, bestehende Sicherheitsberichte, Signaturen und Trust Anchor
werden nicht auf eine ungeprüfte Produktivfreigabe umgestellt. Die normale
Prüfung ohne `--package-only` und die signierten Website-/Release-Builds
verlangen weiterhin vollständig übereinstimmende öffentliche Metadaten.
`--package-only` prüft die lokalen Paket-/App-/Dokumentationsangaben und wird
von diesen Produktions-Builds nicht verwendet.

## Prüfstand und Grenzen

Die vollständige isolierte Prüfung und ihre Zwischenläufe werden lokal unter
`backups/netmon-1.1.22-test-20261107/` aufbewahrt. Dort stehen auch der gesicherte
vorherige Arbeitsstand, Transferplan, Dateivergleich und Paketnachweise.

Abschließender Lauf auf dem überführten Stand: **5520 bestanden, 14
fehlgeschlagen, 335 übersprungen**, etwa 106 Sekunden. Die 14 Fehler-IDs
wurden maschinell gegen V12 abgeglichen und stimmen exakt überein.
Die gezielte Paket-/Signatur-/Lifecycle-/Dokumentauswahl: **144 bestanden**.
Black und Ruff sind für alle 133 überführten/geänderten Python-Dateien geprüft.
Die Zwischenläufe mit ihren Fehlern bleiben separat erhalten; Zahlen werden
nicht addiert. Es gibt weiterhin keinen grünen Gesamtlauf.

Die bereits seit V11/V12 bekannten 14 Fehler-IDs betreffen Support-Dateizählung,
zwölf Repository-/Flatpak-Erwartungen und eine Secure-Browser-Launcher-Erwartung.
Sie bleiben separat offen; eine grüne Gesamtsuite wird nicht behauptet.
Native UFW-Nachweise sind vom jeweiligen Quellstand zu unterscheiden. Ein
zusätzlicher nativer Lauf ist in der aktuellen Prüfumgebung mangels
UFW-Pythonmodul nicht ausführbar; dafür wird keine Host-Firewall installiert
oder umkonfiguriert.

Die geschützten Review-Gates für konkurrierende OFF-/Fremdänderungen bleiben
bestehen. Insbesondere wird F4 nicht als vollständig automatisch gelöst
bezeichnet. Vollständige NetworkManager-/DNS-Guard-Integration, nft-/Paketfluss,
SIGKILL/Stromausfall und alle Paket-Lebenszyklusfälle erhalten hierdurch keine
neue unabhängige oder produktive Abnahme. Frühere VM-Belege bleiben an ihren
jeweiligen früheren Stand gebunden.

Der Paketbau installiert oder startet NetMon nicht. Host-Firewall, DNS, VPN,
Mounts und Systemdienste gehören nicht zu diesem Testbuild-Schritt.
