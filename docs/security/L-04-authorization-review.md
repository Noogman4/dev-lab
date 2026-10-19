# L-04 – Berechtigungsaudit und Testisolierung

Stand: 18. Oktober 2026, `main`,
`9944ce14650877848cb48a2ed531cd84424bcec3`.

**L-04 bleibt TEILWEISE BEHOBEN.** Die Bindung an geprüfte Profilbytes bleibt
erhalten. Der Helfer beweist weiterhin keine vom Desktop unabhängige menschliche
Zustimmung. Dieser Bericht ergänzt `L-04.md`; er ersetzt dessen Restblocker nicht.
Produktionscode, Helferschnittstelle und Systemregeln wurden nicht verändert.

## Umfang und Belege aus dem Repository

Untersucht wurden `netmon/core/nm_ownership.py`, `wireguard_import.py`,
`netmon/features/vpn_controller.py`, die delegierenden Methoden und
sudo-Authentifizierung in `netmon/app.py`, `netmon/core/command.py`,
`netmon/netmon_network_service.py`, die Regressionen für WireGuard, Eigentum,
Sitzungszustand und Uninstaller sowie `docs/SECURITY.md` und `L-04.md`.
Die Paket-/Installationsprüfung umfasst `scripts/build_netmon_deb.sh`,
`build_test_deb.sh`, `build_netmon_dark_deb.sh`, die Site-/Release-Update-Bundler,
`netmon_uninstall_menu.sh`, Dependency-Checks und die Packaging-Dateien.
Repositoryweite Suchen nach sudoers, NOPASSWD, Timestamp- und Polkit-Regeln
ergaben keine ausgelieferte NetMon-spezifische sudoers-/Polkit-Freigabe.
Erwähnungen in Auditberichten sind keine installierten Regeln.

### Aufruf und Vertrauensgrenze

`vpn_controller._owned_nm_command()` prüft zunächst den installierten Helfer
und startet ohne Shell:

```text
sudo -n /usr/bin/python3 -I /usr/lib/netmon/netmon/core/nm_ownership.py <operation>
```

Bei der Controller-Operation `import` ist das CLI-Argument `import-checked`.
`inspect` erhält zusätzlich UUID und Receipt-ID. JSON-Inhalte gelangen über
stdin zum Helfer, nicht über Konfigurationspfade oder Kommandoargumente.
Der Helfer verlangt EUID 0, genau seinen festen Installationspfad sowie
rootkontrollierte, nicht gruppen-/weltschreibbare Verzeichnisse und eine reguläre,
einfach verlinkte Helferdatei. `-I` isoliert Python von Benutzer-Importpfaden.
Eine Arbeitskopie im Repository ist kein privilegiert ausführbarer Ersatz.
Es gibt keinen direkten ungeschützten NM-Import-Fallback.

Die Standard- und Test-DEB-Bundler kopieren den Core nach `/usr/lib/netmon`,
normalisieren Verzeichnis-/Dateimodi auf 0755/0644 und verwenden
`dpkg-deb --root-owner-group`. Der normale Launcher startet Python mit den
Rechten des Benutzers. Das Paket installiert keine passende sudo-Freigabe.
Der getrennte Dark-Build unter `/opt/netmon-dark` stellt diesen festen Helferpfad
nicht bereit. Paketbau allein beweist daher weder Installation noch
Laufzeitautorisierung. Rootseitige Maintainer-Skripte und ein ausdrücklich als
root gestarteter Uninstaller sind eigene administrative Vorgänge.
Der Uninstaller prüft den geschützten festen Helferpfad vor `cleanup` ebenfalls.

### Fähigkeiten der Helferoperationen

| Operation | Wirkung und verbleibende Grenze |
| --- | --- |
| `import-checked`, Legacy-Alias `import` | Prüfen exakt `name/content/sha256/hooks`, berechnen Digest/Hooks neu und importieren einen rootseitig gestagten Snapshot nativ mit nmcli. Erstellen L-01-Receipt für eine nachweislich neue UUID. Kein unabhängiger Zustimmungsnachweis. |
| `install-profile` | Installiert konsistente Snapshotbytes als `/etc/wireguard/<name>.conf`, mit geschütztem Staging, Lock und atomarem Ersetzen. Ein vorhandenes zulässiges Ziel kann ersetzt werden. Keine allgemeine Zielpfadfreigabe, aber auch keine Beschränkung auf eine vorherige GUI-Auswahl. |
| `snapshot-profile` | Liest einen validierten Namen unter `/etc/wireguard`, begrenzt und ohne Symlink-Folgen. Gibt vollständigen Inhalt, Digest und Hooks über stdout zurück, **einschließlich vorhandener PrivateKey-/PresharedKey-Werte**. Kein Receipt und kein benutzerspezifischer Besitznachweis erforderlich. |
| `inspect` | Prüft UUID, Receipt und aktuelle Verbindungsinkarnation; liefert Identitätsdaten, nicht den vollständigen Profilinhalt. |
| `delete` | Löscht nur den unveränderten, durch gültigen Root-Receipt belegten UUID-Kandidaten. Ein Anzeigename oder benutzereigener Zustand reicht nicht. |
| `cleanup` | Ermittelt belegte NetMon-Verbindungen und verlangt Bestätigung auf stdin. Ein bereits autorisierter Prozess kann diese Eingabe selbst liefern; sie beweist keinen Menschen. Unbelegte/fremde Verbindungen werden weiterhin behalten. |

Die Root-Receipts schützen die Erstellungsprovenienz und Inkarnation, nicht die
Identität eines einzelnen Desktop-Benutzers. Die CLI prüft keine Freigabe für
einen konkreten `SUDO_UID`/Digest-Auftrag. Alle erlaubten Aufrufer erreichen die
gleiche geschützte NetMon-Registry. Die L-01-Löschprüfungen sowie die F-01-Job-,
Callback- und Rollbackzuordnung bleiben unverändert.

### Authentifizierung ist keine Zustimmung zu Profilbytes

`ensure_sudo_session()` verwendet `check_sudo_nopasswd()` und gegebenenfalls
`renew_sudo_timestamp()`. Erstere Funktion testet `sudo -n true`; letztere kann
`sudo -S -v` ausführen. Diese Funktionen wurden beim Audit **nicht aufgerufen**.
Ein Erfolg von `sudo -n true` unterscheidet NOPASSWD nicht von einem gültigen
Cache und beweist keine Erlaubnis für die Helferkommandozeile. Auch die Bezeichnung
NOPASSWD in `scripts/check_netmon_deps.sh` ist dafür kein Policy-Nachweis.

Eine sudoers-Freigabe für Python ohne Argumentbeschränkung erlaubt beliebige
Python-Argumente. Eine Freigabe für `-I <Helfer> *` kann neue Operationen
einschließen; eine exakt auf den alten Alias `import` begrenzte Regel erlaubt
`import-checked` dagegen nicht automatisch. sudoers prüft Kommando und Argumente,
nicht das JSON auf stdin. Eine engere Argumentregel bindet deshalb noch keine
Zustimmung an einen Digest. Siehe [sudoers-Primärdokumentation](https://raw.githubusercontent.com/sudo-project/sudo/main/docs/sudoers.man.in).

Same-UID allein reicht nicht: Zusätzlich müssen Kommandoautorisierung und
Authentifizierung gelten. `-n` verhindert eine Passwortabfrage und umgeht keine
Policy. NOPASSWD beseitigt die Cacheabhängigkeit für die erlaubten Kommandos.
Bei Passwortregeln kann ein nutzbarer Cache die erneute Abfrage ersparen:

| Timestamp-Kontext | Bedeutung für einen fremden Prozess derselben UID |
| --- | --- |
| `global` | Cache nicht an Terminal/Elternprozess gebunden; wesentlich breiter nutzbar. |
| `tty` | An die passende Terminalsitzung gebunden; ohne Terminal gilt das PPID-Modell. Ein anderer Prozess hat nicht automatisch denselben Kontext. |
| `ppid` | An den gemeinsamen Elternprozess gebunden. Getrennte Desktop-Prozesse können unterschiedliche Kontexte haben. GUI-Threads teilen dagegen dieselbe Prozessidentität. |
| `kernel` | OpenBSD-spezifische Terminal-Caches, keine hier nachgewiesene Linux-Konfiguration. |

Timeout, Authentifizierungs-UID und Sitzungs-/Prozessstartzeiten beeinflussen die
Nutzbarkeit zusätzlich. Kein bestimmter Timeout oder Kontext wird lokal
unterstellt. Ein kompromittierter GUI-Prozess kann den GUI-Kontext selbst nutzen.
Details: [sudoers_timestamp](https://www.sudo.ws/docs/man/sudoers_timestamp.man/).

## Tatsächlich lesend geprüfter lokaler Zustand

Die Metadaten wurden außerhalb der Sandbox unter unveränderter UID/EUID 1000
bestätigt; deren UID-Übersetzung auf 65534 wurde nicht als Host-Eigentum gewertet.
Es wurden weder sudo noch pkexec, pkaction/pkcheck, nmcli oder ein Root-Helfer
zur Berechtigungsprobe gestartet. Es wurden keine privaten Profile, Schlüssel,
Passwörter oder sudo-Timestampdateien gelesen.

| Pfad | Beobachtung auf diesem Rechner |
| --- | --- |
| `/usr/lib/netmon`, `.../netmon/core` | root:root, 0755 |
| `/usr/lib/netmon/netmon/core/nm_ownership.py` | **Nicht vorhanden**; die aktuelle Arbeitskopie ist hier kein installierter Helfer. |
| `/usr/bin/python3` | rootkontrollierter Symlink; `/usr/bin/sudo` root:root, 4755 |
| `/etc/sudo.conf` | root:root, 0644, keine aktiven Konfigurationszeilen |
| `/etc/sudoers` | root:root, 0440, unter UID 1000 nicht lesbar |
| `/etc/sudoers.d` | root:root, 0755; sichtbare Dateien `README`, `pwfeedback`, deren Inhalte nicht lesbar |
| `/etc/polkit-1/rules.d` | root, 0750, nicht lesbar; lokale Overrides bleiben unbekannt |
| `/usr/share/polkit-1/rules.d` | root:root, 0755, Distribution-Regeln lesbar |
| `/etc/wireguard` | root:root, 0700, nicht lesbar |
| `/etc/NetworkManager/system-connections` | root:root, 0755; keine Profilinhalte gelesen |
| `/var/lib/netmon/nm-wireguard-ownership` | Nicht vorhanden |

Die sichtbaren Polkit-Adminregeln `49-ubuntu-admin.rules`/`50-default.rules`
benennen sudo-/admin-Gruppen als Administratoridentitäten. Das beweist allein
keine allgemeine sudo-Berechtigung. Die sichtbare
`org.freedesktop.NetworkManager.rules` erlaubt `settings.modify.system` für
aktive lokale Mitglieder von `sudo` oder `netdev`. Die NM-Policy-XML nennt
ansonsten `auth_admin_keep` für Systemänderungen; für aktive Benutzer ist
`network-control` bereits `yes`. Diese Defaults können durch lokale Regeln
überschrieben werden. Mitgliedschaft in der lokalen sudo-Gruppe war sichtbar,
eine konkrete Polkit-Entscheidung wurde nicht angefordert.

**Nicht nachgewiesen:** effektive sudo-/LDAP-/SSSD-Regeln, NOPASSWD,
Kommando-Wildcards, Timestamp-Konfiguration oder aktueller Cache, unbekannte
Polkit-Overrides und Berechtigungen eines späteren Produktionssystems.
Der fehlende lokale Helfer begründet keine Entwarnung für eine künftige
Installation. Es wurde auch keine behauptete sudo-Ausnutzung am Host versucht.

Für einen Betreiber mit bereits bestehender, separat autorisierter Root-Sitzung
sind folgende ausschließlich lesenden Prüfungen vorgeschlagen, **nicht ausgeführt**:

```sh
stat /etc/sudoers /etc/sudoers.d /etc/polkit-1/rules.d
cat /etc/sudoers
find /etc/sudoers.d -maxdepth 1 -type f -print
find /etc/polkit-1/rules.d -maxdepth 1 -type f -print
grep '^sudoers:' /etc/nsswitch.conf
namei -l /usr/lib/netmon/netmon/core/nm_ownership.py
```

Anschließend müssten genau die eingebundenen Regeldateien und gegebenenfalls
externe Policyquellen aufgelöst werden. Keine ungefilterte Ausgabe von
Credential-Dateien. `sudo -l`, `sudo -v` oder `sudo -n true` werden hier bewusst
nicht als lokale Auditkommandos empfohlen: Ihre Ausführung könnte Authentifizierung
oder Timestamp-Nebenwirkungen auslösen.

## Angreifermodelle und Auswirkungen

| Modell | Bewertung |
| --- | --- |
| A: Ausgewählte Quelldatei manipulieren | Die sichere FD-Lesung, Identitätsprüfungen, unveränderlichen Snapshotbytes und rootseitige Prüfung schließen den ursprünglichen Pfad-TOCTOU. Spätes Ersetzen eines Benutzerpfades ändert die importierten Snapshotbytes nicht. Bestehende adversariale Regressionen bestätigen das. |
| B: Same UID ohne nutzbare sudo-Autorisierung | Erreicht den Root-Helfer nicht allein durch UID-Gleichheit, einen selbst berechneten Digest oder Zugriff auf den Repositorycode. Unabhängige Polkit-Rechte können trotzdem native NM-Änderungen erlauben; sie sind kein Zugriff auf den sudo-Helfer. |
| C: Same UID mit nutzbarer Helferfreigabe | Kann eigene konsistente Aufträge senden. `install-profile` erweitert eine reine NM-Delegation um geschützte Profil-Schreibrechte; `snapshot-profile` um das Lesen der enthaltenen Secrets. `import-checked` erlaubt NM-Neuanlagen. Die Stärke hängt von den zuvor bereits erlaubten Operationen ab. Eine generische Helfer-Wildcard darf nicht als unverändert enge Delegation behandelt werden. |
| D: Allgemeine nutzbare Root-Berechtigung | Lesen/Schreiben der Profile, beliebige NM-Aufrufe und Root-Codeausführung sind bereits unabhängig von NetMon möglich. Ein weiterer Importbroker schafft gegen diesen Angreifer keine zusätzliche Root-Sicherheitsgrenze. Bloße Gruppenmitgliedschaft oder ein noch erforderliches unbekanntes Passwort ist kein Nachweis solcher nutzbaren Rechte. |
| E: Kompromittierte GUI | Kann Warnungen und Zustimmungszustand fälschen und eigene konsistente Payloads senden, soweit ihre Privilegien reichen. Rootseitige Pfad-/Größen-/Receiptprüfungen gelten weiterhin; unabhängige menschliche Zustimmung kann die GUI nicht attestieren. F-01 schützt weiter vor versehentlich veralteten Jobs, nicht vor beliebiger Codeausführung innerhalb der GUI. |

`snapshot-profile` redigiert Secrets absichtlich nicht, weil der nachfolgende
Import die vollständigen Bytes benötigt. Die Rückgabe erfolgt über eine Pipe,
nicht als bewusstes GUI-Log. Eine Pipe ist jedoch kein Schutz vor einem
bereits autorisierten bösartigen Aufrufer. Sudo-I/O-Logging könnte zusätzlich
stdin/stdout mit Secrets protokollieren; eine solche Policy wurde nicht geprüft.
Eine begrenzte Profil-Lesefreigabe muss deshalb ausdrücklich als Secretzugriff
bewertet werden. Bestehende allgemeine `sudo cat`-/Root-Rechte wären bereits ein
unabhängiger Lesepfad, sind hier aber nicht als tatsächlich erlaubt nachgewiesen.

### Nativer NM-Import und wg-quick sind verschiedene Ausführungswege

Der Helfer ruft natives `nmcli connection import type wireguard file ...` auf,
kein `wg-quick`. Der NM-Importer ignoriert die vier wg-quick-Hookdirektiven;
deren bloße Anwesenheit belegt deshalb keine Shellausführung durch NM.
Importierte Verbindungen können jedoch autoconnect-fähig sein: Das Fehlen eines
expliziten `connection up` ist keine Garantie gegen Aktivierung durch den Daemon.
Siehe den [NetworkManager-Entwicklerbericht](https://blogs.gnome.org/thaller/2019/03/15/wireguard-in-networkmanager/).

`install-profile` schreibt hingegen eine wg-quick-Konfiguration. Erst eine
spätere entsprechende Aktivierung/Deaktivierung kann deren Hookbefehle über bash
mit den jeweiligen Rechten ausführen. NetMons Netzwerkservice verwendet dafür
`sudo -n wg-quick up/down <Profil>`. Manuelle Anwenden-/Startabläufe können beide
Schritte verbinden; reine Import-RPCs starten selbst kein wg-quick.
Diese Unterscheidung präzisiert die Aussage in `L-04.md`, ohne dessen Inhalt zu
ändern. Siehe [wg-quick-Primärdokumentation](https://git.zx2c4.com/wireguard-tools/about/src/man/wg-quick.8).

## Testisolierung und Validierung

Die vier gemeldeten Aufruflecks wurden vor Ergänzung ihrer Fakes mit einem
strengen Guard reproduziert. Alle vier Tests scheiterten am blockierten
Prozessversuch; zusätzlich meldeten vier Teardowns denselben Versuch. Es wurden
keine dieser Kommandos ausgeführt:

| Bestehender Test | Fehlende Testgrenze / Korrektur |
| --- | --- |
| `test_open_vpn_slot_switches_directly_to_new_profile_without_vpn_off` | DNS-UI-Refresh führte zu `resolvectl status`; gezielter Fake für diesen Refresh. |
| `test_open_vpn_slot_logs_missing_profile_and_opens_slot_tab` | Existenzprüfung/erneute Profillistung griffen auf den Host zu; synthetische Existenz- und Listenwerte. |
| `test_assign_vpn_slot_rolls_back_when_save_fails` | Profilauflösung listete `/etc/wireguard` privilegiert; synthetische Profilliste. Echte Save-Fehler-/Rollbacklogik und Assertions bleiben erhalten. |
| `test_remove_firewall_rules_for_vpn_profile_deletes_profile_specific_ufw_rules` | Familienauflösung las Profile per `sudo cat`; synthetische Familienauflösung. Endpoint-Sammlung, Differenzbildung und erwartete Fake-UFW-Löschungen bleiben getestet. |

Die gemeinsame Fixture blockiert `subprocess.Popen/run/call/check_call/check_output`
sowie relevante `os`-Prozessstarts. Ein zusätzlicher Teardown-Nachweis verhindert,
dass verschluckte Ausnahmen eine erfolgreiche Isolation vortäuschen.
Sie wird nur von den gezielt isolierten Tests angefordert, nicht global zum
Umgehen anderer Prüfungen eingesetzt.

Der Dateilauf zeigte zusätzlich zwei noch laufende Hintergrundjobs aus
`test_save_primary_vpn_slot_writes_config_and_updates_button_text` und
`test_save_primary_vpn_slot_updates_privacy_combobox_and_selection`.
Sie konnten in den Guard eines späteren Tests hineinlaufen. Deshalb erhielten
auch diese beiden unmittelbaren Nachbartests einen Fake für die Jobplanung und
denselben Guard. Ihre Speicher-/UI-Assertions bleiben unverändert. Das sind
notwendige Isolationsfakes, keine Produktionsänderungen oder neuen Testfälle.

Ein vorläufiger Gesamtlauf wurde wegen dieses Befunds nach 413 bestandenen Tests
abgebrochen. Ein zunächst zusätzlich verwendeter temporärer Audit-Guard konnte
die vorhandene Popen-Konstruktorprüfung überlagern. Der vom Benutzer gemeldete
Neustart ist damit technisch erklärbar; ein kausaler Host-Log-Nachweis wurde
nicht erhoben. Dieser Lauf ist kein bestandener Testnachweis. Der korrigierte
Audit-Guard hängt unterhalb des bestehenden Konstruktors an `_execute_child`;
der Repository-Reboot-Schutz bleibt aktiv. Dessen sieben eigene Tests wurden
gemeinsam mit den 72 VPN-Slot-Tests zuerst erfolgreich geprüft. Der temporäre
Guard ist kein Repositorybestandteil und kein neuer Autorisierungsmechanismus.

Abschlussläufe (bestehende Testfälle, nicht additiv zu zählen):

| Prüfung | Bestanden | Fehlgeschlagen | Fehler | Übersprungen |
| --- | ---: | ---: | ---: | ---: |
| Vier beauftragte Fälle mit strengem Guard | 4 | 0 | 0 | 0 |
| Vollständige VPN-Slot-Datei | 72 | 0 | 0 | 0 |
| Repository-Reboot-Guard zusammen mit VPN-Slot-Datei | 79 | 0 | 0 | 0 |
| L-04-/L-01-/F-01-/Uninstaller-Regressionen | 274 | 0 | 0 | 0 |
| Gesamtsuite mit zusätzlichem Audit-Guard | 3.831 | 22 | 0 | 0 |

Die vier geforderten Fälle wurden anschließend nochmals explizit gemeinsam
ausgeführt: 4 bestanden in 0,37 Sekunden. Der gezielte Lauf mit 274 Fällen
benötigte 3,72 Sekunden, der Gesamtlauf 126,38 Sekunden. Die Gesamtsuite enthält
3.853 vorhandene Fälle; **keine neuen Testfälle** wurden hinzugefügt. Vier
vorhandene Fälle wurden direkt repariert, zwei weitere zur Vermeidung ihrer
nachlaufenden Jobs isoliert. Die 73 ursprünglichen L-04-Fälle sind bereits Teil
der vorhandenen 274/3.853 Fälle und werden nicht als neue Audit-Tests gezählt.

Der zusätzliche Audit-Guard blockierte im Gesamtlauf 125 Versuche, installierte
Hostprogramme zu starten: 84 sudo-, 23 resolvectl-, 13 wg- und 5 nmcli-Aufrufe.
Auch ein vom Produktionscode abgefangener Versuch zählt hier als Auditbefund;
deshalb ist die Suite ausdrücklich **nicht grün**. Die 22 Testfehlschläge
verteilen sich auf die unveränderten Dateien:

- `tests/test_netmon_dns_consistency.py`: 13 Fälle;
- `tests/test_netmon_ipv6_ui.py`: 3 Fälle;
- `tests/test_netmon_killswitch.py`: 6 Fälle.

Ihre Tracebacks zeigen fehlende Fakes bei Hostabfragen, beispielsweise DNS-UI,
WireGuard-Interface-Ermittlung und NM-Diagnose. Ein DNS-Guard-Test fängt den
blockierten Aufruf intern ab und wechselt dadurch in den Fehlerzweig. Weitere
abgefangene Versuche führen nicht zwingend zu einem pytest-Fehlschlag. Zwei
Warnungen betreffen Tk-Variablenbereinigung und einen ebenfalls blockierten
Hintergrundjob. Diese weiteren Isolationslücken wurden nicht durch eine globale
Erfolgsattrappe verdeckt und außerhalb des Auftrags nicht repariert. Die
vollständigen Namen und Tracebacks stehen im lokalen JUnit-Bericht und Laufprotokoll.
Damit ist eine uneingeschränkte Gesamttestfreigabe nicht nachgewiesen.

Reproduzierbare Befehle; `/tmp/netmon_l04_command_guard.py` ist das zusätzliche,
nicht eingecheckte Auditwerkzeug, das reale privilegierte Hostaufrufe blockiert.
Der Guard im geänderten VPN-Slot-Testmodul ist dagegen dauerhaft enthalten:

```sh
.venv/bin/python -m pytest -q --tb=short tests/test_netmon_vpn_slots.py

PYTHONPATH=/tmp .venv/bin/python -m pytest -p netmon_l04_command_guard \
  -q --tb=short --junitxml=/tmp/netmon-l04-auth-regressions.xml \
  tests/test_wireguard_import_security.py tests/test_netmon_nm_ownership.py \
  tests/test_netmon_vpn_slots.py tests/test_netmon_uninstaller.py

PYTHONPATH=/tmp NETMON_TEST_PHP=/tmp/netmon-l04-php/runtime/usr/bin/php8.3 \
  xvfb-run -a .venv/bin/python -m pytest -p netmon_l04_command_guard \
  -q -rs --tb=short --junitxml=/tmp/netmon-l04-auth-full.xml \
  tests tools/secure_browser_manager/tests/test_browser_container_builder.py \
  > /tmp/netmon-l04-auth-full.log 2>&1

.venv/bin/python -m ruff check tests/test_netmon_vpn_slots.py
.venv/bin/python -m black --check tests/test_netmon_vpn_slots.py
.venv/bin/python -m py_compile tests/test_netmon_vpn_slots.py
git diff --check
```

Ruff, Black, Syntaxprüfung und Diff-Whitespaceprüfung bestanden.
Die Gesamtsuite lief mit lokalen Testservern, Xvfb, GnuPG und temporär entpacktem
offiziellem Ubuntu-PHP-CLI außerhalb der Sandbox unter UID 1000. PHP wurde nur
unter `/tmp` entpackt, nicht systemweit installiert. Nach dem Neustart fehlten
die vorherigen temporären Programme/Protokolle; die Abschlussläufe wurden
deshalb erneut ausgeführt. Kein positiver Abschlussnachweis stützt sich auf
einen unterbrochenen oder nicht mehr verfügbaren Lauf.

## Entscheidungsvorlage

**Empfehlung: B als nächstes Deployment-Gate, noch keine abgeschlossene
Policykorrektur.** Zuerst muss der Betreiber die tatsächlich wirksame Policy
offenlegen und gegen die zusätzlichen Lese-/Schreibfähigkeiten prüfen. Hier
fehlen sowohl der installierte Helfer als auch lesbare effektive sudo-Regeln.
Eine uneingeschränkte Aussage A oder die Notwendigkeit eines Brokers für jeden
Benutzer wäre deshalb unbelegt.

| Option | Voraussetzung, minimale Maßnahme und Konsequenz |
| --- | --- |
| A: Bestehende Policy ausreichend | Erst belegbar, wenn erlaubte Kommandos/Argumente, Gruppen, externe Regeln und Cachekontexte bekannt sind und der Betreiber das Modell bewusst auf Dateimanipulation bei vertrauenswürdiger GUI bzw. bereits allgemein autorisierte Administratoren begrenzt. Das stärkere Modell einer unabhängigen menschlichen Zustimmung wäre damit nicht erfüllt. Lokal nicht abgeschlossen. |
| B: Policy einschränken | Falls breite Python-/Helfer-Wildcards bestehen: durch explizite erforderliche Operationen am festen rootkontrollierten Pfad ersetzen; `snapshot-profile` als Secret-Leserecht und `install-profile` als Schreib-/spätere Hookfähigkeit separat freigeben oder verweigern. Kein pauschales NOPASSWD für alle Operationen. Cachekontexte und weitere Root-Umgehungswege prüfen; engere Timestamps mindern Wiederverwendung, beweisen aber keine profilbezogene Zustimmung. Entzug kann geschützte Referenzimporte, manuelle Profile/IPv4-Ableitungen, Installation oder Cleanup deaktivieren. Der generische `sudo -n true`-Vortest ist mit sehr engen Regeln möglicherweise inkompatibel; das wäre separat zu bearbeiten. Keine konkrete Hostregel wurde geändert oder ohne Beleg als zu breit bezeichnet. |
| C: Vertrauenswürdiger Broker | Erforderlich, wenn auch ein sudo-delegierter oder kompromittierter Desktop keine unbestätigten Profile installieren/importieren dürfen soll. Prepare fixiert rootseitig Bytes und Ziel; Approve bindet Digest, Aktion, normalisiertes Ziel, authentifizierte Identität, Ablaufzeit und einmalige Nonce über einen unabhängigen vertrauenswürdigen Kanal; Commit prüft und verbraucht diese Freigabe atomar und verwendet ausschließlich den gespeicherten Snapshot. Keine frei signierbaren Desktop-Flags/Tokens. Direkte alte Helfer-, Python-, Datei- und NM-Umgehungsrechte müssten zugleich entfallen. Bei kompromittierter GUI muss der Freigabekanal außerhalb ihrer kontrollierten Sitzung liegen. Gegen bereits beliebige Root-Rechte entsteht kein Schutz. Hier ausdrücklich nicht implementiert. |

Auch B allein löst den dokumentierten Zustimmungsblocker nicht. Für dessen
Beibehaltung als verbindliches starkes Schutzziel wäre nach dem Policy-Audit C
separat zu entwerfen und freizugeben. Begrenzungen und Betriebsmodell dürfen
nicht allein durch neue Erfolgsformulierungen im Bericht ersetzt werden.

## Änderungsgrenzen und Restannahmen

Geändert wird nur `tests/test_netmon_vpn_slots.py`; neu ist dieser Bericht.
Die fünf About-Dateien sind gegenüber den vor Arbeitsbeginn aufgenommenen
SHA-256-Werten bytegleich und ungestagt. Auch `L-04.md`, beide Core-Helfer und
`vpn_controller.py` sind bytegleich. `secure-browser/` bleibt unversioniert
und wurde nicht betreten oder bearbeitet. Kein Commit, Push oder Deployment.

Keine produktive Installation, keine echten NetworkManager-/WireGuard-Operationen,
keine Regeländerung und keine Änderung an Root-Dateien war Bestandteil der
Auditmaßnahmen. Der dokumentierte Testlaufvorfall ist davon ausdrücklich
ausgenommen; der korrigierte Abschlusslauf wird separat ausgewiesen.
Die ursprünglichen Grenzen zu externen Root-Schreibern, Abstürzen, NM-Autoconnect,
manueller Bereinigung nach partiellen Fehlern und einer kompromittierten GUI
bleiben bestehen. **L-04 bleibt TEILWEISE BEHOBEN.**
