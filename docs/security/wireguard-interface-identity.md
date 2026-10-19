# WireGuard-Profilnamen und UFW-Interfacefreigaben

Patch-Pruefdatum: 2026-10-19; lokale Commit-Vorpruefung: 2026-10-20.

Repository: Noogman4/dev-lab

Ausgangsbasis: `2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f` (main).
Der HDD-Branch `d69c3f26fe3af37d103deef43a8d68a35482d71f` enthaelt
dieselben betroffenen WireGuard-/Firewall-Dateien. Beide Remote-Staende
wurden am Ende der Arbeit nochmals bestaetigt.

Cloud-Finding: `csf_c60379751f7785458c2795dd`

Titel: Imported WireGuard profile names can create broad UFW allow rules on unrelated interfaces

Schweregrad: Medium. Beobachtete Cloud-Revision: `71ed081b77e26af8853d340e777009f027251082`.

## Unabhaengige Reproduktion

Vor der Aenderung wurden die unveraenderten Produktionsfunktionen fuer
Namenspruefung, Runtime-Aufloesung, Interface-Sammlung und UFW-Regelsetzung
mit synthetischen Profildaten und simulierten Systemoperationen ausgefuehrt.
Die Namen eth0, enp4s0 und wlan0 erreichten jeweils ALLOW IN und ALLOW OUT.
Profilvorhandensein genuegte; Linktyp und Profilbindung wurden nicht geprueft.

## Korrektur

- Der bestehende geschuetzte Root-Helfer erhaelt die nur lesende Operation
  `verify-interface`. Er liest das Profil aus `/etc/wireguard` ueber seine
  vorhandene begrenzte, symlinkgeschuetzte Eigentums-/Berechtigungspruefung.
- Nur ein eindeutiger Interface-Abschnitt mit genau einem PrivateKey ist
  zulaessig. Wiederholte Peer-Abschnitte bleiben unterstuetzt. Hooks werden
  weder ausgefuehrt noch fuer die Identitaetspruefung benoetigt.
- Feste ip-/wg-Pfade und eine bereinigte Umgebung pruefen einen existierenden,
  administrativ aktiven WireGuard-Link. `wg pubkey` erhaelt den privaten
  Schluessel ausschliesslich ueber stdin. Der oeffentliche Schluessel muss
  dem laufenden Interface entsprechen.
- Erneute Linkabfrage und erneutes Lesen des geschuetzten Profils muessen
  denselben Interfaceindex und dieselben Profilbytes bestaetigen. Die Antwort
  enthaelt ausschliesslich Name, Linktyp, Interfaceindex, PublicKey und Digest.
- Der Aufrufer nutzt ausschliesslich den geschuetzten installierten Helfer
  mit `/usr/bin/python3 -I`. Fehlender/veralteter Helfer, fehlende Autorisierung,
  Zeitueberschreitungen und ungueltige Antworten liefern keinen Nachweis.
- Der VPN-Collector nimmt nur verifizierte Interfaces auf. Der normale
  UFW-Sink prueft nochmals vor jeder Interfacefreigabe, einschliesslich des
  Pfads fuer vermeintlich bereits vorhandene Regeln.
- Der Killswitch prueft auch direkt gelieferte aktive Interfacenamen und
  erneut vor jeder einzelnen Interfacefreigabe. Nachweisverlust waehrend der
  Anwendung nutzt die bestehende restriktive Fehlerbehandlung.
- Der privilegierte Profilimport weist Namenskollisionen mit jeder bestehenden
  Schnittstelle ab, auch bei WireGuard. Die Abfrage wird unmittelbar vor dem
  Ersetzen der Zieldatei wiederholt. Aktive Profile muessen vor einem erneuten
  Import gestoppt werden. Fehler bei der Inventur brechen den Import ab.

## Validierung

Ausgefuehrt mit unveraendertem Hostzugriffs-Guard, synthetischen Profilen,
simuliertem Kernelzustand und simulierten privilegierten Operationen:

```sh
python -m pytest -q \
  tests/test_wireguard_interface_security.py \
  tests/test_wireguard_import_security.py \
  tests/test_netmon_nm_ownership.py \
  tests/test_firewall_controller.py \
  tests/test_netmon_vpn_slots.py \
  tests/test_netmon_killswitch.py \
  tests/test_killswitch_failure_recovery.py \
  tests/test_host_access_guard.py
```

Ergebnis: **561 bestanden, 0 fehlgeschlagen, 0 uebersprungen**.

Die neue Suite prueft insbesondere den urspruenglichen Weg durch reale
Runtime-Aufloesung, Collector, privilegierten Verifier und UFW-Sink sowie den
positiven WireGuard-Fall. Weitere Faelle: fremde Linktypen/Schluessel,
inaktive Links, Profil-/Interfacewechsel waehrend der Pruefung, Symlinks,
unsichere Berechtigungen, Importkollisionen, falsche CLI-Anfragen,
ungueltige RPC-Antworten und Killswitch-Identitaetsverlust vor IN/OUT-Regeln.

Dies ist der mitgelieferte Browser-Pruefstand. Die unten dokumentierte
erneute lokale Pruefung bestaetigt alle 561 Faelle und prueft alle sieben
betroffenen Python-Dateien mit Black und der vollstaendigen Ruff-
Projektkonfiguration ohne Befund.

## Grenzen und Inbetriebnahme

Es wurden keine echten Firewallregeln oder produktiven Profile geaendert.
Die urspruengliche Browser-Umgebung erlaubte keine vollstaendige Bubblewrap-
Isolation (`open /proc/8/ns/ns failed`). Bei der erneuten lokalen Pruefung
bestand die Isolationsprobe; alle unten genannten Tests liefen im privaten
Bubblewrap-Namespace. Es gibt weiterhin keinen echten Zorin-/UFW-/wg-quick-
Integrationstest und keinen Nachweis laufender Kernel-Netlink-Operationen.

Der Fix wird ausschliesslich als isolierter lokaler Commit gesichert; Push,
Merge und Pull Request gehoeren nicht zu diesem Auftrag. Der installierte
Root-Helfer muss zusammen mit dem Controller aktualisiert werden; bis dahin
werden Interfacefreigaben sicher verweigert. Nichtaktive Profile erhalten
keine vorauseilenden Interfacefreigaben; Endpoint-Regeln bleiben moeglich.

Bereits vor diesem Fix angelegte breite UFW-Regeln werden nicht automatisch
geloescht: Ihre Herkunft ist ohne belastbaren alten Eigentumsnachweis nicht
von absichtlich gesetzten Nutzerregeln unterscheidbar. Bestehende Regeln auf
physischen Interfaces muessen vor produktiver Freigabe gesondert geprueft
und gegebenenfalls ausdruecklich entfernt werden.

Die Pruefungen begrenzen beobachtbare Wechsel zwischen ihren Stichproben.
UFW bindet Regeln weiterhin an Namen. Eine spaetere privilegierte
Umbenennung/Neuverwendung des Namens oder Aenderung von Kernelzustand,
Root-Profil oder Firewall durch Root/CAP_NET_ADMIN wird dadurch nicht
dauerhaft verhindert. Es wird keine kontinuierliche Interfaceueberwachung
oder atomare Bindung von UFW an eine Kernel-Interfacegeneration behauptet.

Das Cloud-Finding wurde nicht geschlossen und kein kostenpflichtiger Scan
gestartet. Die formale Schliessung erfordert den bereitgestellten Fix und
eine anschliessende Pruefung des tatsaechlich gepushten/installierten Stands.

## Lokale Commit-Vorpruefung am 2026-10-20

Branch: `security/hdd-b01-b02-cloud-review`.
HEAD vor dem Commit: `d69c3f26fe3af37d103deef43a8d68a35482d71f`.
Der Git-Index war leer. Der lokale Commit baut auf diesem HDD-Commit auf;
sein eigener Diff enthaelt ausschliesslich diese acht M-05-Dateien:

- `netmon/core/nm_ownership.py`
- `netmon/features/firewall_controller.py`
- `netmon/features/vpn_controller.py`
- `tests/test_killswitch_failure_recovery.py`
- `tests/test_netmon_killswitch.py`
- `tests/test_wireguard_import_security.py`
- `tests/test_wireguard_interface_security.py`
- `docs/security/wireguard-interface-identity.md`

Der Produktionscode und die vier Testdateien entsprechen weiterhin dem
angewendeten WireGuard-Patch. Nur dieser Bericht wurde fuer Pruefbelege,
Helfer-Rollout und Altregel-Behandlung ergaenzt. HDD-Dateien und vorhandene
About-Dateien werden anhand ihrer SHA-256-Werte unveraendert gehalten.
`secure-browser/` wird weder gelesen noch geaendert oder gestagt.

### Pruefung der alternativen Aufrufpfade

Slot-Zuweisung, Import-Reconcile und Profilvorbereitung laufen ueber den
VPN-Collector und den erneut pruefenden `ensure_ufw_rule_exists()`-Sink.
Die App-Wrapper delegieren an diese Produktionsfunktionen. Auch bei direkter
Uebergabe eines Namens an diesen Sink muss der Helfer die Identitaet erneut
bestaetigen; ein gecachter vorhandener Regelschluessel ueberspringt das nicht.
Der Killswitch uebernimmt sowohl Collector-Ergebnisse als auch direkt
gelieferte aktive Namen erst nach Verifikation und prueft vor jedem IN-/OUT-
Interface-ALLOW nochmals. Service-Adapter und direkter Command-Runner liegen
jeweils hinter derselben Pruefung. Loopback ist eine explizite Ausnahme.

Die separate Security-Baseline kann ausdruecklich bestaetigte allgemeine
Firewallregeln anwenden und besitzt einen eigenen UFW-Sink. Ihre eingebauten
Profile erlauben ausschliesslich Loopback; importierte Baseline-Regeln werden
nicht aus WireGuard-Profilnamen abgeleitet. Der Netzwerk-Service bleibt ein
duenner Befehlsadapter, keine eigenstaendige Sicherheitsgrenze. Die Aussage
dieses Fixes betrifft automatische WireGuard-Interfacefreigaben, nicht jede
manuell oder ueber einen separat bestaetigten Baseline-Import gesetzte Regel.

Der fuer wg-quick relevante privilegierte `install-profile`-Pfad prueft
Namenskollisionen zweimal; manuell erzeugte Profile nutzen ebenfalls diesen
Installationspfad. Der separate NetworkManager-Import registriert Verbindungen
per UUID, installiert kein `/etc/wireguard/<name>.conf` und autorisiert dadurch
keine UFW-Interfacefreigabe. Ein NM-Anzeigename allein ist kein Nachweis.
Fehler des Helfers, der Werkzeuge oder der Inventur liefern keinen gueltigen
Nachweis; die CLI faengt auch unerwartete fehlerhafte Kernelantworten ab.

### Wiederholte Tests und Qualitaetschecks

Alle folgenden pytest-Laeufe nutzten den unveraenderten Hostzugriffs-Guard,
synthetische Profile/Kernelantworten und simulierte privilegierte Operationen.
Die Probe bestaetigte: kein Root, NoNewPrivs, schreibgeschuetztes Repository,
privates Netzwerk ohne Routen, keine Host-Heimverzeichnisse oder Dienstsockets.
Die Ausfuehrung des Namespace-Starters erfolgte ausserhalb der aeusseren
Werkzeug-Sandbox, innerhalb des geprueften Bubblewrap-Namespace.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short --maxfail=0 tests/test_wireguard_interface_security.py

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short --maxfail=0 \
  tests/test_wireguard_interface_security.py \
  tests/test_wireguard_import_security.py tests/test_netmon_nm_ownership.py \
  tests/test_firewall_controller.py tests/test_netmon_vpn_slots.py \
  tests/test_netmon_killswitch.py tests/test_killswitch_failure_recovery.py \
  tests/test_host_access_guard.py

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short --maxfail=0 tests/test_manual_wireguard_security.py \
  tests/test_vpn_slots_tab.py tests/test_netmon_deb_packaging.py
```

Ergebnisse: **65/65 neue Sicherheitsfaelle**, **561/561 bisherige relevante
Regressionen**, **176/176 ergaenzende Import-/UI-/Paketierungstests**; jeweils
0 Fehler und 0 uebersprungen. Die 65 Faelle sind bereits in den 561 enthalten:
insgesamt 737 verschiedene Testfaelle in elf Modulen, keine Gesamtsuite.
JUnit-Belege liegen unter `/tmp/user/1000/netmon-isolation-oh0y8sr9/junit.xml`,
`/tmp/user/1000/netmon-isolation-1sfbybyc/junit.xml` und
`/tmp/user/1000/netmon-isolation-k8ex_6c2/junit.xml` (temporaere lokale Artefakte).

Fuer jede der sieben Python-Dateien einzeln ausgefuehrt:
`BLACK_CACHE_DIR=/tmp/netmon-m05-black-cache .venv/bin/python -m black --check <Datei>`.
Alle sieben blieben unveraendert. `.venv/bin/python -m ruff check --no-cache`
mit diesen sieben expliziten Dateipfaden lieferte **All checks passed**.
Syntaxpruefung mit `compile(Path(datei).read_text(), datei, 'exec')` bestand
fuer diese Dateien, den unveraenderten App-Wrapper und den Netzwerk-Service.
`git diff --check` und eine zusaetzliche Whitespace-/Abschlusszeilenpruefung
aller acht M-05-Dateien bestanden. Es wurden keine Abhaengigkeiten installiert.

### Aktualisierung des installierten Root-Helfers

Ein Checkout oder GUI-Neustart aktualisiert
`/usr/lib/netmon/netmon/core/nm_ownership.py` nicht. Controller und Helfer
muessen aus demselben geprueften Release installiert werden. Der vorhandene
Deb-Builder kopiert `netmon/core` einschliesslich dieses Helfers an diesen
Pfad; Paketdateien werden auf 0644 und Verzeichnisse auf 0755 gesetzt.
Root-Eigentum, nicht schreibbare Elternpfade und fehlende Symlinks sind
Voraussetzungen der Laufzeitpruefung. Benoetigt werden ausserdem die festen
Werkzeugpfade `/usr/sbin/ip` und `/usr/bin/wg` sowie eine gueltige bestehende
sudo-Autorisierung fuer den isolierten Python-Helfer. Es wird keine neue
pauschale NOPASSWD-Freigabe fuer Python empfohlen oder eingerichtet.

Vor produktivem Einsatz in einer separaten Testumgebung installierten
Helfer und Controller mit den freigegebenen Artefakten abgleichen; danach
positiven WG-Fall, fremden Linktyp, Schluesselabweichung und Identitaetsverlust
pruefen. Ein alter Helfer kennt `verify-interface` nicht und liefert einen
Fehler; fehlende Tools/Autorisierung verweigern die Freigabe ebenfalls.
Hier wurde weder installiert noch eine echte privilegierte Abfrage ausgefuehrt.

### Vorhandene UFW-Freigaben getrennt behandeln

Der Fix ist keine Altregel-Migration. Deduplizierung und vorhandene
Killswitch-Cleanup-Funktionen koennen einzelne Regeln behandeln, entfernen
aber nicht zuverlaessig alle historisch durch M-05 entstandenen Freigaben.
Insbesondere fallen physische, jetzt abgewiesene Interfaces nicht mehr in
die Liste verifizierter WireGuard-Interfaces.

Sichere separate Vorgehensweise, hier ausschliesslich dokumentiert:

1. In einem vereinbarten Wartungsfenster den Regelzustand nur lesend mit
   `ufw status verbose`, `ufw status numbered` und `ufw show added` erfassen;
   IPv4/IPv6, IN/OUT, Interface, Quelle/Ziel, Kommentare und Reihenfolge sichern.
   Eine Linkinventur und vorhandene Aenderungsprotokolle gegenpruefen.
   Keine PrivateKeys oder kompletten WireGuard-Konfigurationen protokollieren.
2. Breite Interface-ALLOWs als Kandidaten markieren. Ein physischer Link oder
   ein fehlender WG-Nachweis beweist noch keine unerwuenschte Regelherkunft.
   Administratorfreigaben und benoetigte SSH-/Managementwege einzeln abgleichen;
   bei unklarer Herkunft die Regel zur manuellen Entscheidung vorlegen.
3. Eine konkrete Liste exakter Regelspezifikationen zur separaten Freigabe
   vorlegen. Vor spaeterer Bereinigung geschuetzte Sicherung der UFW-
   Konfiguration, Konsolenzugang und Wiederherstellungsplan vorbereiten.
   Keine automatische Loeschung allein aufgrund eines Interface-Namens.
4. Erst nach gesonderter Freigabe den aktuellen Zustand erneut vergleichen
   und ausschliesslich genehmigte Regeln einzeln entfernen. Nummerierte
   Regelindizes koennen sich verschieben und duerfen nicht aus einer alten
   Inventur uebernommen werden. Beide Adressfamilien und Managementzugang
   anschliessend kontrollieren; bei Abweichung abbrechen und neu planen.

Lokale Bewertung: Der gemeldete automatische Weg von einem importierten
Profilnamen zu breiten ALLOW-Regeln auf fremden Interfaces wird unterbunden.
Die Stichproben sind weiterhin keine atomare Kernel-/UFW-Transaktion.
Privilegierte Namenswiederverwendung und spaetere Aenderungen bleiben wie
oben beschrieben Restrisiken. M-05 wird hiermit **nicht formal geschlossen**;
es erfolgten keine Security-Cloud-Aktion und kein neuer Scan.
