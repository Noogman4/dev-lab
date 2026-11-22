# Eigenständige NetMon-Verwaltung

Das Paket `netmon-manager` stellt „NetMon verwalten“, `netmon-manage`,
`netmon-install` und `netmon-uninstall` bereit. Es benötigt keine installierte
NetMon-App. Seine eigenen Backup- und Prüfhilfen liegen geschützt unter
`/usr/lib/netmon-manager`; gemeinsam benutzte Dateien gehören nie beiden Paketen.

- **Entfernen – Daten behalten:** entfernt die App; Verwaltung und Daten bleiben.
- **Entfernen – Daten löschen:** bisherige Vorschau und Bestätigungen bleiben.
  „NetMon verwalten ebenfalls entfernen“ ist zunächst ausgeschaltet. Erst die
  abschließende Bestätigung entfernt gegebenenfalls beide Pakete.
- **Verwaltung entfernen …:** entfernt nur `netmon-manager`. App, Benutzerdaten
  und externe Sicherungen bleiben erhalten. Neuinstallation der Verwaltung ist
  später mit ihrer Paketdatei möglich.
- Externe Sicherungen werden in keinem dieser Abläufe gelöscht. Vor einer
  Datenlöschung eine eigenständige, geprüfte Sicherung erstellen.

Die einmalige Umstellung von den kombinierten Beta-1/2-Paketen erfordert App
`1.1.22~beta3` oder neuer und das Verwaltungspaket in derselben APT-Transaktion.
`Breaks`/`Replaces` übergeben die bisherigen Verwaltungsdateien an das neue Paket.
Ältere App-Pakete enthalten diese Dateien noch und können nicht gleichzeitig
mit der eigenständigen Verwaltung installiert werden. Kein Erzwingen mit dpkg.

Lokaler Build: `python3 -B scripts/build_netmon_manager_deb.py`.
Das Verwaltungspaket ist ein lokales Testpaket ohne Herausgebersignatur. Die
bestehenden Signatur- und Release-Belegprüfungen werden nicht verändert. Eine
öffentliche gemeinsame Auslieferung beider Pakete ist gesondert vorzubereiten.

Die optionale Bereinigung systemweiter VPN-/Firewall-Einstellungen im bisherigen
Deinstaller bleibt getrennt und ausdrücklich bestätigungspflichtig. „Verwaltung
entfernen“ führt sie nicht aus. Aktive oder ungeklärte Firewall-Transaktionen
blockieren App-Entfernung und App-Installation weiter. Geschützte Prüfhilfen sind
auch verfügbar, wenn die App bereits entfernt wurde.
