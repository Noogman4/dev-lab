# WireGuard-Profilnamen und UFW-Interface-Identitaet

Gepruefte Basis: `2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f` (main).
Befund: `csf_c60379751f7785458c2795dd`, Auftreten
`occ_d2462e0bb7f1d3dcafde8344` aus dem Repository-Scan von `71ed081`.

## Bestaetigung und Korrektur

Auch auf der neueren Basis machte ein vorhandenes `eth0.conf` den Namen `eth0`
zum effektiven Firewall-Interface. Der Import-Reconcile konnte damit breite
UFW-ALLOW-Regeln auf einer physischen Schnittstelle erzeugen.

Die Korrektur trennt Startkandidaten von freigabefaehigen Interfaces:

- Dateiinstallation, generierte Profile und NM-Import verweigern Namen bereits
  vorhandener Nicht-WireGuard-Links. Nicht lesbare Interface-Auskunft bricht ab.
- Der Start prueft die Namenskollision und verlangt direkt vor `wg-quick up`
  die Abwesenheit des Runtime-Interfaces, auch bei uebersprungenem Cleanup.
- Nur ein erfolgreicher Start mit anschliessend bestaetigtem Kernel-Linktyp
  `wireguard` erzeugt einen fluechtigen Startnachweis fuer den exakten
  Runtime-Profilnamen und seinen Kernel-ifindex.
- Runtime-Aufloesung, Interface-Collector, Nicht-Killswitch-Regelsetzung und
  Killswitch-Aktivierung verlangen diesen Nachweis und pruefen erneut Typ und
  ifindex. Ein Profilname oder `wg show` allein reicht nicht.
- Cleanup und erfolgreiches Ersetzen einer Profildatei verwerfen betroffene
  Nachweise. Verschwundene oder ersetzte Links verlieren ihre Freigabefaehigkeit.
- Offline-Profile behalten Runtime-Profil und Endpoint-Vorbereitung, erzeugen
  aber keine pauschalen Interface-Freigaben.

Nach einem App-Neustart werden aktive Tunnel nicht automatisch uebernommen.
Ein expliziter Reconnect stellt den Startnachweis wieder her. Die Pruefung
verlangt Kernel-WireGuard und eine funktionierende `ip -j -d link show`-Auskunft.
Userspace-TUN-Implementierungen erhalten damit keine pauschale Freigabe.

## Validierung

682 Tests bestanden, ein Tk-Smoke-Test ohne DISPLAY uebersprungen. Alle
Netzwerk- und Firewall-Mutationen wurden simuliert; kein echter Host-UFW- oder
VPN-Test. Der vorhandene Hostzugriffs-Guard blieb unveraendert aktiv. Der
vollstaendige Bubblewrap/Xvfb-Starter konnte mangels `xvfb-run` nicht verwendet
werden; dies ist keine Validierung auf einem isolierten Linux-Desktop.

```sh
python -m pytest -q tests/test_wireguard_interface_identity.py \
  tests/test_wireguard_import_security.py tests/test_netmon_vpn_slots.py \
  tests/test_netmon_killswitch.py tests/test_firewall_controller.py
# 231 passed
python -m pytest -q tests/test_killswitch_failure_recovery.py \
  tests/test_manual_wireguard_security.py tests/test_netmon_nm_ownership.py \
  tests/test_host_access_guard.py tests/test_vpn_slots_tab.py
# 451 passed, 1 skipped
```

Neue Regressionen pruefen die vier Importwege mit physischem `eth0`, Startfolge,
exakte IPv4-Runtime-Namen, fehlgeschlagene/unbestaetigte Starts, fremde aktive
WireGuard-Links, geaenderte Typen/ifindices und unlesbare/malformed Auskunft.
Killswitch-Regeltests pruefen auch, dass unbestaetigte aktive Namen keine
Freigaben erhalten. Bestehende Tests stellen die neue Kernel-Auskunft explizit
synthetisch bereit; die Produktionspruefung wird nicht uebersprungen.

Black, Syntaxpruefung und `git diff --check` bestanden. Die neue Testdatei ist
Ruff-sauber. Ein Vergleich der geaenderten bestehenden Python-Dateien mit HEAD
zeigt keine zusaetzlichen Ruff-Meldungen; bestehende Meldungen bleiben bestehen.

## Grenzen

Der Nachweis liegt im App-Prozess und ist kein separater privilegierter Broker.
Er schuetzt nicht vor einem Angreifer mit Prozessspeicherzugriff oder Rechten,
Kernel-Interfaces/Firewall parallel zu manipulieren. Bereits vor diesem Patch
angelegte UFW-Freigaben werden nicht automatisch migriert oder entfernt.
Der Cloud-Befund wurde nicht geschlossen. Eine erneute Cloud-Pruefung des
gepushten Commits steht noch aus.

## Lokale Pruefung vor Commit und Push am 2026-10-20

Der aktuelle Neun-Dateien-Patch wurde im separaten Worktree
`/tmp/netmon-main-interface-identity` auf `main` bei
`2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f` mit `git apply --check`
geprueft und konfliktfrei angewendet. Patch-SHA-256:
`32b7077b1bf9335611958c97df0b9128a577af82e19707604fda35c985d93a08`.
Der aeltere Acht-Dateien-Patch wurde nicht verwendet.

Der unveraenderte Starter `tests/run_isolated_suite.py` und der unveraenderte
Hostzugriffs-Guard wurden verwendet. Ein temporaerer Wrapper bindet nur die
vorhandene Python-Umgebung sowie fuer historische Regressionen benoetigte
Git-Metadaten zusaetzlich lesend ein. Die Isolationsprobe bestaetigte:
nicht-root, no-new-privileges, Repository nur lesbar, privates Netzwerk ohne
Routen, keine Host-Dienstsockets, kein Host-Home oder WireGuard-/NM-Konfiguration.
Es gab keine Installation oder echten UFW-/WireGuard-/Root-Operationen.

```sh
PYTHONDONTWRITEBYTECODE=1 /dev-lab/projects/dev-lab/.venv/bin/python -B \
  /tmp/netmon-main-interface-run-isolated.py --probe
PYTHONDONTWRITEBYTECODE=1 /dev-lab/projects/dev-lab/.venv/bin/python -B \
  /tmp/netmon-main-interface-run-isolated.py -q -rs --tb=short --maxfail=0 \
  tests/test_wireguard_interface_identity.py \
  tests/test_wireguard_import_security.py tests/test_netmon_vpn_slots.py \
  tests/test_netmon_killswitch.py tests/test_firewall_controller.py
# 231 passed
PYTHONDONTWRITEBYTECODE=1 /dev-lab/projects/dev-lab/.venv/bin/python -B \
  /tmp/netmon-main-interface-run-isolated.py -q -rs --tb=short --maxfail=0 \
  tests/test_killswitch_failure_recovery.py \
  tests/test_manual_wireguard_security.py tests/test_netmon_nm_ownership.py \
  tests/test_host_access_guard.py tests/test_vpn_slots_tab.py
# 452 passed
```

**683 bestanden, 0 fehlgeschlagen, 0 uebersprungen.** Der zuvor mangels
DISPLAY uebersprungene Tk-Smoke-Test lief diesmal unter Xvfb erfolgreich.
JUnit-Ausgaben liegen unter
`/tmp/user/1000/netmon-isolation-mte35wu_/junit.xml` und
`/tmp/user/1000/netmon-isolation-62upibvu/junit.xml`.
Keine vollstaendige Repository-Testsuite und kein Live-Netzwerktest.

Alle acht betroffenen Python-Dateien bestanden Black, Ruff mit vollstaendiger
Projektkonfiguration und Syntaxpruefung; Whitespace-Pruefung einschliesslich
der neuen Dateien und `git diff --check` bestanden. Produktionscode und Tests
wurden gegenueber der aktuellen Patchdatei nicht veraendert.

Das urspruengliche HDD-/About-Arbeitsverzeichnis bleibt unveraendert.
Bestehende UFW-Freigaben werden durch diesen Fix nicht automatisch migriert
oder entfernt. Nach einem App-Neustart ist ein expliziter Reconnect fuer den
fluechtigen Startnachweis erforderlich. Die Kernel-Abfragen und nachfolgenden
UFW-Aufrufe bilden keine atomare Transaktion; das separate TOCTOU-Risiko
bleibt offen. Der Cloud-Befund bleibt bis zur erneuten Pruefung des gepushten
Commits offen; kein Cloud-Scan wurde gestartet.
