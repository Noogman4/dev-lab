# Begrenzter WireGuard-Abbau bei VPN-Wechsel und VPN-Aus

Geprüfte Basis: `8f5dfe9` (main).
Befund: `csf_3733ff47c60e949783e69898`, Auftreten
`occ_02a0b1b5ccbccb85dfe57842`, ursprünglich beobachtet auf `71ed081`.

Der Befund bestand weiterhin: `cleanup_wireguard_interfaces` verwendete das
globale Ergebnis von `wg show interfaces` für `wg-quick down` und anschließend
`ip link delete`. Ein fremder Tunnel konnte dadurch abgebaut werden.

Start und Abbau laufen jetzt über den vorhandenen geschützten Root-Helfer
`nm_ownership.py`. Der neue WireGuard-Store führt ein eigenes, gesperrtes
Verzeichnis `/var/lib/netmon/wg-quick-ownership` mit privaten Root-Dateien.
Nur ein vom Helfer neu angelegtes Interface erhält einen Erstellungsnachweis.
Bestehende gleichnamige Links werden niemals übernommen.

Der Nachweis bindet den Namen an Interface-Index, öffentlichen WireGuard-Schlüssel,
Boot-ID und Netzwerk-Namespace. Der Abbau prüft diese Identität erneut unmittelbar
vor `wg-quick down`. Fehlende Links lassen den alten Nachweis verfallen; ersetzte
oder nicht verifizierbare Links bleiben erhalten und der Vorgang schlägt fehl.
Globale Inventare, Profilnamen und GUI-Zustand erteilen keine Abbauberechtigung.
Es gibt keine erzwungene Link-Löschung mehr, auch nicht nach einem Fehler.

Eine private Kopie der ursprünglichen Konfiguration mit SHA-256-Nachweis liefert
die Abbauparameter und Hooks. Spätere Änderungen am installierten Profil können
diese Kopie nicht ersetzen. Die Nachweise überleben einen Anwendungsneustart;
die gesonderten UFW-Startnachweise bleiben wie bisher sitzungsgebunden.

## Prüfung

Die Tests verwenden echte temporäre Nachweisdateien und synthetische Kernel- und
WireGuard-Adapter. Sie prüfen unter anderem:

- VPN-Wechsel und VPN-Aus mit einem parallelen fremden Tunnel;
- Abbau nach Anwendungsneustart und mit geändertem installierten Profil;
- ausgetauschten Index, Schlüssel, Boot oder Netzwerk-Namespace;
- Austausch unmittelbar vor dem Abbau;
- manipulierte, fehlende, verlinkte und unzureichend geschützte Nachweise;
- fehlgeschlagenen oder unvollständigen Abbau ohne erzwungenes Löschen;
- Namenskollisionen und ungültige Interface-Namen.

Die betroffenen VPN-, UFW-, IPv6-, NM-Eigentums- und Importtests laufen ebenfalls.
Es werden keine Host-Tunnel oder Host-Firewallregeln geändert.

Black, Python-Kompilierung und `git diff --check` sind erfolgreich. Ruff meldet
gegenüber der Basis keine zusätzlichen Diagnosen (112 bestehende Diagnosen in
den geprüften Dateien); die neue Testdatei ist Ruff-fehlerfrei. Die vollständige
Suite konnte hier nicht abgeschlossen werden: Die Firefox-Signaturtests scheitern
beim Erstellen eines GPG-Testschlüssels; ein weiterer Testlauf wurde vom bestehenden
Hostzugriffs-Guard wegen eines Netzwerkversuchs abgebrochen. Der Guard bleibt aktiv.

## Betriebsgrenzen

Der installierte Root-Helfer muss zusammen mit der Anwendung aktualisiert werden.
Ohne den passenden geschützten Helfer bricht der Vorgang ab; ein ungeschützter
Ausweichpfad existiert nicht. Vor der Aktualisierung gestartete Tunnel erhalten
keinen nachträglichen Nachweis und bleiben unangetastet. Ein nach dem Start
fehlgeschlagener Nachweis kann einen manuellen Abbau erforderlich machen.

Die Sperre serialisiert NetMon-Vorgänge. Fremde privilegierte Netzwerkmanager
verwenden diese Sperre nicht; Kernel-Abfrage und namensbasierter `wg-quick`-Aufruf
sind keine atomare Operation. Die erneute Prüfung verkleinert dieses Zeitfenster,
kann gleichzeitige Eingriffe anderer Root-Prozesse aber nicht vollständig sperren.
