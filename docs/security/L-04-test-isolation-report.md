# L-04 – Testisolierung, nachgewiesene Grenzen und Abschlussbefunde

**NACHARBEIT ERFORDERLICH. L-04 bleibt TEILWEISE BEHOBEN.**

Ausgangsrevision und unveränderter HEAD:
`9944ce14650877848cb48a2ed531cd84424bcec3`, Branch `main`.
Dieser Bericht dokumentiert einen begrenzten Testabschluss, keine vollständige
Gesamttest- oder Sicherheitsfreigabe. Keine Produktionskorrektur, Installation,
Policyänderung, neuer Autorisierungsbroker, Commit, Push oder Deployment.

## Ausgangszustand und sichere Bestandsaufnahme

Der ursprüngliche JUnit-Bericht `/tmp/netmon-l04-auth-full.xml` enthält 3.853
Fälle, davon 3.831 bestanden und 22 fehlgeschlagen, ohne Skips. Die Verteilung
13 DNS / 3 IPv6 / 6 Killswitch wurde anhand der tatsächlichen Fälle ermittelt.
Die Fehler wurden nicht pauschal als reine Testprobleme vorausgesetzt.

Der Index war leer. Bereits vorhanden waren die vier versionierten About-
Änderungen, die unversionierte About-Testdatei, die geänderte VPN-Slot-Testdatei,
beide unversionierten L-04-Audit-/Konzeptdokumente und `secure-browser/`.
Diese Arbeiten wurden nicht zurückgesetzt, gestagt oder bearbeitet.
Die frühere temporäre Guard-Korrektur lag in `/tmp`, nicht im Produktionscode.
Hashes der geschützten Dateien sowie der L-01-/F-01-/L-04-Produktionsbausteine
wurden vor Beginn aufgenommen und am Ende verglichen.

## Hostisolation vor dem ersten Test

Der neue Teststarter `tests/run_isolated_suite.py` verwendet ausschließlich
bereits vorhandenes Bubblewrap und Xvfb. Bubblewrap war innerhalb der Codex-
Sandbox nicht nutzbar, außerhalb unter der normalen Benutzeridentität dagegen
erfolgreich. Das ist keine sudo-/Root-Authentifizierung.

Die vor dem ersten Test ausgeführte Probe bestätigte:

- UID ungleich 0, `NoNewPrivs: 1`, abgelegte Capabilities;
- eigener PID-, Netzwerk-, IPC- und UTS-Namespace;
- schreibgeschütztes Projekt und schreibgeschützte Systemprogramme/Bibliotheken;
- keine externe Netzwerkroute; synthetische Server ausschließlich im privaten
  Loopback-Netz, keine Verbindung zum Host-Loopback;
- kein Host-HOME, kein `/etc/wireguard`, kein `/etc/NetworkManager`, keine
  Host-D-Bus-/systemd-Sockets;
- geleerte Umgebung, eigenes HOME/XDG/Temp-Verzeichnis, keine Host-Xauthority;
- verdecktes `secure-browser/` und verdeckte lokale `.aws`/`.codex`/`.agents`-
  Verzeichnisse; keine Untersuchung ihrer Inhalte;
- persistente Testausgaben ausschließlich in einem neu angelegten isolierten
  Ausgabeverzeichnis; Testlauf-Caches im Projekt sind deaktiviert.

Schreibbare Laufzeitdateien liegen im eigenen Testbereich oder in flüchtigen
Namespace-Mounts. Prüfprogramme können keine Host-Netzwerk-/Dienstkonfiguration
erreichen. Die vorhandene PHP-Testbinary wurde nur lesend in den Test-Namespace
eingebunden; es wurde nichts installiert. Alle verwendeten Profile/Schlüssel
der Regressionen sind synthetisch.

`tests/conftest.py` ergänzt den bestehenden Reboot-/Shutdown-Guard, ersetzt
ihn aber nicht. Vor dem echten `Popen`-Start werden System-/Netzwerkkommandos
wie sudo, nmcli, wg, UFW, resolvectl, sysctl und ip blockiert. Nicht eindeutig
analysierte Shellstrings werden ebenfalls verweigert. Netzwerkverbindungen
sind nur zu Loopback im ausdrücklich isolierten Lauf erlaubt. Kontrollierte
Test-Fakes sowie die bereits getestete reine `systemctl --version`-Abfrage
bleiben möglich. Es gibt keine globale erfolgreiche Befehlsattrappe.

Jeder blockierte Zugriff wird ohne stdin, Environment oder Konfigurationsinhalte
mit Herkunftsframes erfasst. Ein autouse-Teardown und der Sitzungsabschluss
verhindern ein grünes Ergebnis, wenn Produktionscode die Guard-Ausnahme abfängt.
Normale Läufe haben zusätzlich Fail-Fast. Der ausschließlich für die bekannte
Vorher-Reproduktion verwendete `--netmon-audit-continue`-Modus erlaubt weiterhin
keinen Zugriff, sondern sammelt die blockierten Fälle.

Der Python-Guard allein ist keine vollständige Sandbox gegen beliebige native
Unterprozesse. Der Nachweis stützt sich auf seine Kombination mit der äußeren
OS-Isolation; insbesondere gilt er nicht als Freigabe für unisolierte Hosttests.

## Unabhängige Reproduktion aller 22 Fälle

Unter wirksamer Isolation scheiterten dieselben **22 Testfälle** erneut.
Zusätzlich meldeten 22 Teardowns die blockierten Aufrufversuche. Das sind keine
44 unabhängigen Fälle. Laufzeit: 18,59 Sekunden.
Der strengere Guard fängt teilweise bereits frühere Abfragen als der alte
temporäre Guard ab, etwa `ip` oder `sysctl` statt eines späteren `nmcli`/`wg`.

Die folgende Tabelle nennt je Fall den Produktionspfad, Ursache, gezielte
Korrektur und endgültiges Ergebnis. Alle Testnamen bleiben unverändert.

| Nr. | Test | Produktionspfad / Ursache | Präzise Isolationskorrektur | Ergebnis |
| ---: | --- | --- | --- | --- |
| 1 | `test_show_dot_status_result_startup_stays_silent_for_dns_output_and_chad` | DoT-Statusdarstellung → DNS-UI-Refresh → resolvectl | Nur den nachgelagerten DNS-UI-Refresh faken; Status-/Ausgabeassertions bleiben echt. | bestanden |
| 2 | `test_analyze_dns_health_reports_dot_vpn_conflict` | DNS-Report → Linkparser → dynamische WireGuard-Inventarisierung | Auf dieser Serviceinstanz leeres synthetisches Interfaceinventar; echter Parser wertet den gelieferten Text und die Temp-Dropin-Datei aus. | bestanden |
| 3 | `test_enable_dot_blocks_when_vpn_dns_active` | DoT-Aktivierungssperre → DNS-UI-Refresh → resolvectl | Nur UI-Refresh faken; Warnung, Sperre und Assertion gegen sudo-Anforderung erhalten. | bestanden |
| 4 | `test_active_nm_dns_targets_only_returns_physical_connections` | `_active_nm_dns_targets()` fragt zusätzlich Defaultinterface und dessen Verbindung ab | `enp4s0` und passende synthetische Verbindung ergänzen; reale physische Filterlogik bleibt aktiv. | bestanden |
| 5 | `test_evaluate_dns_policy_flags_global_dns_with_vpn` | DNS-Policy → Linkparser → wg-Inventar | Leeres synthetisches Serviceinventar; eigentliche Policyanalyse bleibt aktiv. | bestanden |
| 6 | `test_detect_vpn_active_ignores_non_link_text` | Auch Text ohne Link löst vorher Interfaceinventar aus | Synthetisches leeres Inventar; beide bestehenden positiven/negativen Parserassertions bleiben erhalten. | bestanden |
| 7 | `test_dns_leak_check_reports_low_risk_for_exclusive_vpn_dns` | DNS-Leak-Report → Policy/Parser → wg-Inventar | Serviceinventar faken, echte Auswertung der synthetischen DNS-Daten beibehalten. | bestanden |
| 8 | `test_update_dns_controls_state_disables_manual_controls_with_vpn` | Controls lesen neben VPN-Zustand auch DoT über resolvectl | DoT-Fakt explizit False; reale Controls-Logik und alle Widgetassertions erhalten. | bestanden |
| 9 | `test_update_dns_controls_state_disables_manual_controls_during_transition` | Gleiche zusätzliche DoT-Abfrage im Transition-Fall | DoT-Fakt False; Transition- und Widgetlogik unverändert. | bestanden |
| 10 | `test_apply_dns_reports_control_layer_target_errors` | DNS-Auswahl synchronisiert Protokolllabel und fragt DoT ab | DoT-Fakt False; der bestehende Fehler-Fake und die Fehlermeldungsassertions bleiben. | bestanden |
| 11 | `test_apply_dns_refreshes_dns_guard_whitelist_and_check_on_success` | Gleiche Protokolllabel-Synchronisierung | DoT-Fakt False; Whitelist-, Guard-, Consistency- und Statusassertions unverändert. | bestanden |
| 12 | `test_apply_dns_aborts_when_dnssec_strict_confirmation_is_declined` | DoT-Abfrage und Statusrefresh nach abgelehnter Bestätigung | DoT False und nachgelagerten Policy-Statusrefresh faken; echter Abbruch bleibt geprüft. | bestanden |
| 13 | `test_dns_guard_loop_enforces_when_dirty` | Guard fragt DoT/VPN-Status; abgefangene Ausnahme führte zum Fehlerzweig | Beide externen Statusfakten False; echte Dirty-Erkennung und bestehender Repair-Fake bleiben aktiv. | bestanden |
| 14 | `test_update_ipv6_controls_state_keeps_left_buttons_enabled_for_active_ipv4_only_vpn` | Systemzustand via sysctl und Laufzeitinterface via wg/ip | System-IPv6 aktiv, Interface `wg0`, keine globale IPv6-Adresse am Interface explizit synthetisch setzen. | Hostisolation bestanden; fachliche Assertion weiterhin fehlgeschlagen, siehe Befund unten. |
| 15 | `test_update_ipv6_controls_state_keeps_left_buttons_enabled_without_active_vpn` | Unbeabsichtigte sysctl-/wg-Abfragen | System-IPv6 aktiv, kein aktives Interface explizit setzen. | bestanden |
| 16 | `test_update_ipv6_controls_state_ignores_destroyed_hint_widgets` | Gleiche Systemabfragen vor Widgetprüfung | System-IPv6 aktiv, kein aktives Interface setzen; reale Prüfung zerstörter Widgets erhalten. | bestanden |
| 17 | `test_isp_stealth_on_skips_duplicate_killswitch_activation_when_already_active` | `_capture_stealth_runtime_state()` liest IPv6 und VPN-Zustand | Explizite synthetische IPv6-/VPN-Fakten; reale Zustandsaufnahme und Killswitch-Verzweigung erhalten. | bestanden |
| 18 | `test_internet_on_sync_forces_reconnect_and_keeps_killswitch_active` | Nachgelagerte `debug_nm_state()`-Diagnose liest Hostzustand | Nur Diagnosesammler faken; Wiederherstellung und Killswitch-/Schedulingassertions erhalten. | bestanden |
| 19 | `test_internet_on_sync_retries_network_ready_after_wg_and_killswitch_reset` | Gleiche zusätzliche NM-Diagnose | Diagnosesammler faken; Retry- und Reset-Assertions erhalten. | bestanden |
| 20 | `test_internet_on_sync_uses_short_initial_wait_for_pending_vpn_restore` | Gleiche zusätzliche NM-Diagnose | Diagnosesammler faken; Wartezeit- und Restore-Assertions erhalten. | bestanden |
| 21 | `test_internet_on_sync_keeps_killswitch_active_when_vpn_not_ready` | Gleiche zusätzliche NM-Diagnose | Diagnosesammler faken; bestehende Assertions zum Erhalt des Killswitch bleiben. | bestanden |
| 22 | `test_vpn_switch_empty_target_preserves_active_killswitch` | VPN-Wechsel startet zusätzliche NM-Diagnose vor Eingabeprüfung | Nur Diagnosesammler faken; leeres Ziel und Sicherheits-Recovery unverändert geprüft. | bestanden |

Nr. 1–13 liegen in `tests/test_netmon_dns_consistency.py`, Nr. 14–16 in
`tests/test_netmon_ipv6_ui.py`, Nr. 17–22 in `tests/test_netmon_killswitch.py`.
Die Fakes ersetzen konkrete externe Abfrage-/Diagnosegrenzen, nicht die
jeweils behauptete Fachlogik. Keine Assertion wurde entfernt oder abgeschwächt.
Ein AST-Vergleich bestätigt alle ursprünglichen Assertions: 392 DNS-, 29
IPv6- und 222 Killswitch-Assertions unverändert.

## Separater Produktionsbefund: IPv4-only-Tunnel wird als IPv6 dargestellt

Nr. 14 war nicht allein durch fehlende Mocks erklärbar. Nach vollständiger
Isolation gilt deterministisch:

```text
aktives Profil: wg0
System-IPv6 deaktiviert: False
aktives Interface: wg0
Profil unterstützt IPv6: False
IPv6 zur Laufzeit am Interface verfügbar: False
Erwarteter Text: VPN-Profil: nutzt nur IPv4
Tatsächlicher Text: VPN-Profil: nutzt IPv6
```

Ursache in der tatsächlichen `App.update_ipv6_controls_state()`:

```python
elif active_runtime_ipv6 or (active_iface and system_ipv6_enabled):
    vpn_status = "nutzt IPv6"
```

Die Existenz des Interfaces zusammen mit systemweit freigeschaltetem IPv6
überstimmt die ausdrücklich negative Laufzeit-/Profilinformation. Das ist ein
nachgewiesener Anzeigefehler für den synthetisch gültigen IPv4-only-Zustand,
kein durch diese Nacharbeit eingeführter Fehler: Der AST dieser Methode ist
gegenüber HEAD unverändert. Ein leeres Interface zu faken, nur um die Assertion
grün zu bekommen, würde das benannte Szenario nicht korrekt abbilden.

Risiko: irreführende Anzeige der IPv6-Nutzung; daraus folgt allein weder ein
nachgewiesenes Routingproblem noch ein tatsächlicher DNS-/IPv6-Leak. Die echte
Netzwerkfunktion wurde nicht am Host getestet. Eine separate fachliche
Korrekturentscheidung und Freigabe sind nötig. Produktionscode und Assertion
wurden auftragsgemäß **nicht** korrigiert oder als xfail markiert.

## Sicherheitsregressionen und Ergebnisse

| Lauf | Bestanden | Fehlgeschlagen | Teardown-/sonstige Fehler | Skips | Warnungen |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vorher-Reproduktion, 22 verschiedene Fälle | 0 | 22 | 22 Meldungen derselben blockierten Zugriffe | 0 | 0 |
| Abschließender Lauf aller 22 Fälle | 21 | 1 fachlicher IPv6-Fehler | 0 | 0 | 0 |
| L-01/F-01/L-04/Uninstaller plus Guard-Selbsttests | 302 | 0 | 0 | 0 | 0 |
| Gesamtsuite, beim ersten weiteren Isolationsbefund gestoppt | 557 laut pytest-Zusammenfassung | 0 | 1 | 0 | 0 |

Laufzeiten: 18,59 s / 0,55 s / 3,54 s / 61,36 s.
Zahlen sind nicht additiv: Die Sicherheitsauswahl enthält 274 vorhandene
Sicherheitsregressionen, sieben vorhandene Reboot-Guard-Fälle und 21 neue
Klassifikations-/Netzwerk-Guard-Fälle. Der Gesamtlauf ist **kein vollständiger
Lauf aller gesammelten Tests**. JUnit weist dort 557 Fälle mit einem Fehler aus;
pytest zählt den erfolgreichen Call und den fehlgeschlagenen Teardown eines
Falles in seiner Zusammenfassung getrennt. Es wurde kein Test übersprungen,
deaktiviert oder als erwarteter Fehler markiert.

Die gezielte Auswahl prüft weiterhin L-01-Receipts/fremde Verbindungen,
F-01-Sitzungszustand, parallele Jobs und Callbackfehler sowie L-04-Snapshots,
Same-UID-Dateimanipulation, Root-Staging und fehlenden Helfer. Die Produktions-
bausteine und die bereits korrigierte VPN-Slot-Testdatei blieben bytegleich.

## Zusätzlicher Blocker und auftragsgemäßer Stopp der Gesamtsuite

Der neue dauerhafte Guard ist strenger als der frühere temporäre Guard und
führt spätestens bei einem abgefangenen Zugriff im Teardown zum Fail-Fast-Stopp.
Der Gesamtlauf erreichte folgenden zusätzlichen Fall:

```text
tests/test_firewall_controller.py::
test_collect_firewall_transparency_snapshot_uses_german_defaults_for_ratings

App._collect_firewall_transparency_snapshot()
  -> check_sudo_nopasswd()
  -> subprocess.run(["sudo", "-n", "true"])
  -> Guard blockiert vor Popen-Ausführung
```

`check_sudo_nopasswd()` fängt die Guard-Ausnahme ab. Der autouse-Teardown weist
den Versuch trotzdem nach; kein fälschlich grüner Lauf. Es gab **keine echte
sudo-Ausführung und keine Timestamp-Erneuerung**. Danach wurden keine weiteren
Tests gestartet und dieser zusätzliche Fall wurde nicht eigenmächtig repariert.
Weitere bislang verdeckte Hostabfragen sind nicht ausgeschlossen. Der frühere
3.831/22-Lauf beweist daher keine umfassende Isolation der übrigen Fälle.

**Abnahmekriterium null Fehler bei vollständiger Hostisolation nicht erreicht.**
Ein erneuter unisolierter Lauf zur Herstellung grüner Zahlen ist unzulässig.

## Teststarter, Guard-Prüfung und Qualitätskontrollen

Reproduzierbare Aufrufe mit bereits vorhandenen Werkzeugen, ohne sudo:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short tests/test_host_access_guard.py \
  tests/test_destructive_command_guard.py tests/test_wireguard_import_security.py \
  tests/test_netmon_nm_ownership.py tests/test_netmon_vpn_slots.py \
  tests/test_netmon_uninstaller.py

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  --php /tmp/netmon-l04-php/runtime/usr/bin/php8.3
```

Der letzte Befehl startete die vollständige Auswahl einschließlich
Secure-Browser-Builder-Tests und stoppte wie oben dokumentiert. Für die 22
Einzelfälle wurden exakt die Node-IDs aus dem alten JUnit-Bericht übergeben;
der Abschlusslauf verwendete `--maxfail=0`, damit der bekannte fachliche Fehler
die übrigen isolierten Fälle nicht verdeckt. Das erlaubt keine Hostzugriffe.
Der tatsächliche Ausgabeordner wird vom Starter gedruckt.

Lokale Artefakte, jeweils `junit.xml`, kopiertes `console.log` und `xvfb.log`:

- Reproduktion: `/tmp/user/1000/netmon-isolation-wa_0jrnf`;
- 22 Abschlussfälle: `/tmp/user/1000/netmon-isolation-ebmmrg6p`;
- 302 Sicherheits-/Guardfälle: `/tmp/user/1000/netmon-isolation-n61gnyxt`;
- gestoppte Gesamtsuite: `/tmp/user/1000/netmon-isolation-1z709t1k`.

Die Pfade sind temporär und kein dauerhafter Ersatz für diesen Bericht.
Ein früher Xvfb-Start scheiterte im isolierten System beim Laden einer
unnötigen Grafiktreiber-/GLX-Erweiterung. Der Starter deaktiviert diese
Erweiterung; anschließend waren Wrapper-Exitstatus und Teststatus konsistent.
Der Reboot-Guard wurde zu keinem Zeitpunkt durch einen überschriebenen
Popen-Konstruktor umgangen. Seine sieben alten Fälle bestehen unverändert.
Die 21 neuen Guardfälle prüfen Ablehnung/zulässige Fakes ohne die geprüften
Hostkommandos oder Netzwerkverbindungen tatsächlich auszuführen.

Ruff und Black-Check der sechs betroffenen Python-Test-/Starterdateien bestanden.
Die Syntax wurde mit `compile(..., "exec")` ohne Ausführung oder pyc-Ausgabe
geprüft. `git diff --check` bestand. Black-Multiprocessing blockierte in der
Codex-Sandbox; die eigenen Formatterprozesse wurden unterbrochen und die
Formatierung/Prüfung anschließend mit einem Worker außerhalb dieser Sandbox
abgeschlossen. Keine Änderungen an geschützten Dateien durch den Formatter.

## Tatsächlich geänderte Dateien und erhaltene Grenzen

Nur diese sieben Aufgabenpfade wurden bearbeitet oder neu erstellt:

- `tests/conftest.py`: dauerhafter Host-/Netzwerk-Guard und Nachweis abgefangener Versuche;
- `tests/test_netmon_dns_consistency.py`: Fakes für die 13 nachgewiesenen Fälle;
- `tests/test_netmon_ipv6_ui.py`: Laufzeitfakten für drei Fälle, fachlicher Fehler bleibt sichtbar;
- `tests/test_netmon_killswitch.py`: Fakes für sechs Abfrage-/Diagnosepfade;
- `tests/run_isolated_suite.py` (neu): unprivilegierter isolierter Teststarter;
- `tests/test_host_access_guard.py` (neu): 21 Guardfälle;
- dieses Dokument (neu).

Die About-Dateien, die bestehende VPN-Slot-Nacharbeit, sämtliche bisherigen
L-04-Dokumente, `wireguard_import.py`, `nm_ownership.py`, `nm_import_session.py`
und `vpn_controller.py` blieben unverändert. `secure-browser/` wurde nicht
bearbeitet oder in den Tests zugänglich gemacht. Keine Staging-Aktion, Index
leer, HEAD unverändert. Der vollständige bestehende Git-Status enthält daher
zusätzlich weiterhin die früheren About-/Audit-/Konzeptarbeiten.

Nicht getestet wurden reale NetworkManager-/WireGuard-/DNS-/UFW-/IPv6-/Root-
Operationen, tatsächliche sudo-Timestamps, produktive Schlüssel, Host-Polkit,
Paketinstallation oder Deployment. Die äußere Isolation lässt lokale
synthetische Loopback-Tests zu, keine echten externen Netzwerkzugriffe.

## Einsatzbilanz und Empfehlung

Alle 22 ursprünglichen Fälle reproduziert; alle 22 anschließend ohne
Hostzugriffsversuch isoliert. **21 bestehen vollständig; ein eigenständiger
IPv6-Anzeigefehler bleibt offen.** Zusätzlich stoppt ein bisher nicht zur
22er-Auswahl gehörender Firewall-Isolationsfehler die Gesamtsuite. Die 302
gezielten Sicherheits-/Guardfälle sind grün. Es gibt keinen vollständigen
grünen Gesamtlauf und keine uneingeschränkte Freigabe.

Eine unabhängige Nachprüfung der begrenzten Teständerungen und beider offenen
Befunde ist möglich und empfohlen. Für einen vollständigen Abschluss sind
zuerst eine gesonderte Entscheidung zum IPv6-Produktionsbefund und eine Freigabe
zur weiteren Testisolierung nötig. Es wurden keine weiteren Arbeitspakete
begonnen und keine offenen Fälle durch globale Erfolgs-Mocks verdeckt.

Technisch bleibt der ursprüngliche Dateipfad-TOCTOU geschlossen. Unabhängige
menschliche Zustimmung gegenüber einer kompromittierten GUI ist weiterhin
nicht implementiert. Variante C bleibt ausschließlich Zukunftskonzept.
Allgemeine nutzbare Root-Rechte bleiben außerhalb dieses Schutzversprechens.
**L-04 bleibt TEILWEISE BEHOBEN – NACHARBEIT ERFORDERLICH.**

## Nacharbeit Runde 2 – gezielter Abschluss der beiden Restbefunde

Diese Ergänzung dokumentiert den Folgeauftrag. Die Ergebnisse und der gestoppte
Gesamtlauf oben bleiben historische Nachweise; in Runde 2 wurde ausdrücklich
**keine Gesamtsuite** gestartet. HEAD bleibt
`9944ce14650877848cb48a2ed531cd84424bcec3`, Branch `main`.

### A – Firewall-Transparenz: begrenzte Testkorrektur

Der zuvor zuerst auffällige Test ist
`test_collect_firewall_transparency_snapshot_uses_german_defaults_for_ratings`.
Auch der direkt folgende englische Übersetzungstest hat dieselbe Mock-Lücke.
Beide setzen den UFW-Status synthetisch auf Fehler, ersetzen aber nur
`netmon.run_cmd`. Die echte Funktion `check_sudo_nopasswd()` aus
`netmon/core/command.py` ruft unmittelbar `subprocess.run()` auf und erreicht
dadurch diesen Fake nicht.

Vor der Änderung wurden ausschließlich diese beiden Fälle in Bubblewrap mit
aktivem Hostzugriffs-Guard und `--netmon-audit-continue --maxfail=0` reproduziert.
Beide fachlichen Calls bestanden; beide Teardowns meldeten den vorher
blockierten sudo-Versuch. JUnit: zwei Fälle mit jeweils einem Fehler, keine
Skips. Exitstatus 1. **Kein sudo-Prozess wurde gestartet.** Der Nachweis zeigt
auch, dass das Abfangen der Guard-Ausnahme durch `check_sudo_nopasswd()` keine
fälschlich erfolgreiche Testsitzung erlaubt. Der Audit-Schalter erlaubt nur
die Erfassung dieser bekannten Fehler, niemals den Hostzugriff.

Die Änderung in `tests/test_firewall_controller.py` ergänzt ausschließlich in
diesen beiden Tests einen durch `monkeypatch` zurückgenommenen Fake:
`netmon.check_sudo_nopasswd = lambda: False`. Er setzt den konkreten externen
Autorisierungszustand, ersetzt weder die Snapshot-/Übersetzungslogik noch den
prozessweiten Guard. Alle **39 vorhandenen Assertions der Datei** sind per
AST-Vergleich gegen HEAD unverändert erhalten. Es wurde keine Assertion
entfernt, entschärft, übersprungen oder als erwarteter Fehler markiert.

### B – IPv6: bestätigte Ursache, Auswirkungen und Änderungsvorschlag

Die Anzeige wird in `App.update_ipv6_controls_state()` in `netmon/app.py`
gebildet. Das synthetische Szenario bleibt unverändert: aktives Profil und
Interface `wg0`, System-IPv6 eingeschaltet, Profil ohne IPv6 und ausdrücklich
negative Laufzeitabfrage. Der echte Produktionscode zeigt dennoch
`VPN-Profil: nutzt IPv6`. Der vorhandene Test scheitert weiterhin an genau
dieser Textassertion; die vorherigen Assertions für beide eingeschalteten
IPv6-Schaltflächen und die deaktivierte Privacy-IPv6-Auswahl bestehen.

Die Ursache ist die bereits oben belegte Oder-Bedingung. Systemweit erlaubtes
IPv6 und ein vorhandenes Interface sind keine Nachweise für IPv6 auf diesem
Tunnel. Hier wird also ein Konfigurations-/Verfügbarkeitszustand als positiver
Laufzeitnachweis ausgegeben, obwohl `active_runtime_ipv6` False ist.

Die Quellen sind getrennt:

- `App.ipv6_is_disabled()` liest den Systemzustand über sysctl/proc.
- `vpn_controller.profile_supports_ipv6()` untersucht IPv6-Einträge in Address,
  DNS, AllowedIPs oder Endpoint; das belegt Konfiguration, keinen Verkehr.
- `App.ipv6_runtime_available_on_iface()` sucht globale IPv6-Adressen mittels
  `ip -6 -o addr show dev … scope global`. False bedeutet auch Abfragefehler,
  fehlendes Interface oder abgeschaltetes System-IPv6.

Im untersuchten Kontrollfluss wird das falsch positive `vpn_status` nur in
den Text von `ipv6_controls_hint` übernommen. Die Farbe des Hinweises nutzt
bereits `active_runtime_ipv6`; der Text kann daher sogar bei roter Farbe
fälschlich IPv6-Nutzung behaupten. IPv6-Statusampel und Kopfzeile im Refresh
fragen den Laufzeitzustand separat ab und enthalten diese Oder-Bedingung nicht.
Die Privacy-Checkbox wird separat anhand der Profilkonfiguration freigegeben;
beide IPv6-Schaltflächen bleiben unabhängig vom fehlerhaften Text bedienbar.
Aus dem Fehler folgt in diesen Pfaden keine Änderung an Firewall, DNS, Routing,
NetworkManager, WireGuard oder Rollback-Berechtigungen. Die irreführende Anzeige
kann jedoch Benutzerentscheidungen beeinflussen. Ein tatsächlicher Leak oder
ein Defekt der Host-Netzwerkfunktion wurde damit nicht nachgewiesen.

**Konkreter minimaler Vorschlag, noch nicht implementiert:** ausschließlich
die positive Textbedingung ändern von

```python
elif active_runtime_ipv6 or (active_iface and system_ipv6_enabled):
```

zu

```python
elif active_runtime_ipv6:
```

Die übrigen Verzweigungen, Profil-/Systemabfragen und Widgetzustände würden
dabei erhalten. Dafür sind vor einer gesondert freigegebenen Korrektur folgende
Regressionen vorzusehen:

1. Aktiver IPv4-only-Tunnel bei eingeschaltetem System-IPv6 und negativer
   Laufzeitabfrage: IPv4-Hinweis; bisherige Button-/Privacy-Assertions erhalten.
2. Positive Laufzeitabfrage: IPv6-Hinweis und grüne Hinweisfarbe; unterschiedliche
   Profilkonfiguration darf den positiven Laufzeitnachweis nicht ersetzen.
3. Konfiguriertes IPv6 ohne Laufzeitnachweis: niemals positive IPv6-Nutzung
   behaupten; bei abgeschaltetem System die bestehende Erwartungswarnung.
4. Kein aktives Profil, ausgewähltes IPv4-/IPv6-Profil und zerstörte Widgets:
   bisherige Hinweise und Bedienzustände erhalten.
5. Fehler der Laufzeitabfrage und fehlende/globale IPv6-Adressen gezielt faken;
   keine privilegierten Aktionen oder Hostabfragen beim Widgettest erlauben.

Grenze dieses Minimalvorschlags: Eine globale Interfaceadresse beweist weder
IPv6-Routing durch den Tunnel noch erfolgreichen IPv6-Verkehr. Außerdem
unterscheidet der bestehende boolesche Rückgabewert nicht zwischen fehlendem
IPv6 und nicht ermittelbarem Zustand. Die Entfernung der Oder-Bedingung behebt
den nachgewiesenen falschen Positivbefund, aber nicht diese weitergehende
Diagnoseunschärfe. Ein eigener Status „unbekannt“ würde eine zusätzliche
fachliche Entscheidung und gesonderte Freigabe erfordern. Produktionscode,
IPv6-Testdatei und ihre fachliche Sollassertion blieben in Runde 2 bytegleich.

### Ausgeführte Validierung in Runde 2

Vor jedem der beiden Testläufe wurde die vorhandene `--probe` erfolgreich
ausgeführt: unprivilegierter Benutzer, NoNewPrivs, schreibgeschütztes Projekt,
privater Netzwerk-Namespace ohne externe Route, keine Host-Home-/Schlüssel-
oder Dienstsocket-Zugriffe. Die Tests selbst verwenden weiterhin denselben
Bubblewrap-Starter und den unveränderten Hostzugriffs-Guard. Im Abschlusslauf
war der Audit-Fortsetzungsmodus **nicht** aktiv.

Gezielter Abschlussaufruf nach der Probe:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short --maxfail=0 tests/test_firewall_controller.py \
  tests/test_host_access_guard.py tests/test_destructive_command_guard.py \
  tests/test_netmon_ipv6_ui.py
```

| Gruppe | Fälle | Bestanden | Fehlgeschlagen | Sonstige Fehler | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| Firewall-Controller | 16 | 16 | 0 | 0 | 0 |
| Hostzugriffs-Guard | 21 | 21 | 0 | 0 | 0 |
| Bestehender Reboot-/Shutdown-Guard | 7 | 7 | 0 | 0 | 0 |
| IPv6-UI und Profilfunktionen | 8 | 7 | 1 | 0 | 0 |
| Gesamt dieser gezielten Auswahl | 52 | 51 | 1 | 0 | 0 |

Laufzeit 0,36 Sekunden, Exitstatus 1 ausschließlich wegen des bewusst
unkorrigierten IPv6-Produktionsbefunds. Keine neuen blockierten Hostversuche,
keine Warnungen. Die 28 Guard-Selbsttests und die Vorher-Reproduktion ergänzen
sich: Klassifikations-/Rebootregressionen bestehen, tatsächliche unerwartete
sudo-Versuche werden vor dem Prozessstart abgefangen und bleiben als Fehler
sichtbar. Das beweist weiterhin keine vollständige Sicherheit beliebiger
nativer Unterprozesse ohne die äußere Bubblewrap-Isolation.

Temporäre Artefakte mit jeweils `junit.xml` und `xvfb.log`:

- Vorher-Reproduktion: `/tmp/user/1000/netmon-isolation-_pkwnksa`;
- Abschlussauswahl: `/tmp/user/1000/netmon-isolation-8qcxnyot`.

Ruff und Black-Check der einzigen in Runde 2 geänderten Python-Datei bestanden.
Syntaxprüfung mittels `compile(..., "exec")` ohne Ausführung/pyc-Ausgabe und
`git diff --check` bestanden ebenfalls. Der vollständige Rundendiff umfasst nur
`tests/test_firewall_controller.py` und diese Berichtsergänzung. Hashvergleiche
gegen den Rundeneinstieg bestätigen alle anderen zuvor erfassten Dateien als
unverändert, einschließlich der fünf About-Dateien, der bestehenden Test-/Guard-
Arbeiten, aller L-01-/F-01-/L-04-Produktionsbausteine sowie der Audit-/Konzeptdokumente.
`secure-browser/` wurde nicht bearbeitet oder inhaltlich untersucht und blieb
für die Testprozesse verdeckt. Der Index bleibt leer.

**A ist lokal behoben; B ist reproduziert und benötigt eine gesonderte
Produktionsfreigabe.** Weitere bislang verdeckte Test-Hostabfragen sind ohne
erneuten Gesamtlauf nicht ausgeschlossen. Es wurde keine Gesamtsuite gestartet,
keine echte sudo-/Root-Operation, Netzwerkverbindung, Systemänderung, Installation,
Commit-, Push- oder Deployment-Aktion ausgeführt. Der unabhängige
Same-UID-Autorisierungsblocker bleibt offen; ein Broker wurde nicht implementiert.
**L-04 bleibt TEILWEISE BEHOBEN – NACHARBEIT ERFORDERLICH.**

## Folgeauftrag – IPv6-Anzeigekorrektur und erneutes Isolations-Gate

Dieser Abschnitt ergänzt die historischen Ergebnisse der vorherigen Runden.
Er dokumentiert die gesondert freigegebene minimale Produktionskorrektur und
den folgenden, beim ersten neuen Guard-Befund gestoppten gezielten Testlauf.
HEAD und Branch bleiben unverändert:
`9944ce14650877848cb48a2ed531cd84424bcec3`, `main`.

### Tatsächliche Produktionskorrektur

In `App.update_ipv6_controls_state()` wurde ausschließlich die Bedingung für
den positiven Hinweis geändert:

```diff
-        elif active_runtime_ipv6 or (active_iface and system_ipv6_enabled):
+        elif active_runtime_ipv6:
             vpn_status = "nutzt IPv6"
```

Ein vorhandenes Interface und systemweit erlaubtes IPv6 überstimmen damit
keine negative Laufzeitabfrage mehr. Die Ermittlung von System-/Profilzustand,
die Runtime-Abfrage, Widgetfreigaben und alle übrigen Verzweigungen sind
unverändert. Keine Firewall-, DNS-, Routing-, VPN-Import-, Eigentums- oder
Rollbacklogik wurde geändert. Die bestehenden About-Änderungen in `app.py`
bleiben vollständig erhalten: Wird nur die obige Zeile im Speicher zurück
auf den Ausgangstext abgebildet, stimmt der SHA256 der gesamten Datei wieder
mit dem Rundeneinstieg überein. Es wurde nichts zurückgesetzt oder gestagt.

Die vorher dokumentierte Diagnosegrenze bleibt bestehen: Ein globaler
IPv6-Adressnachweis ist kein Beweis für Routing oder Verkehr durch den Tunnel.
Der bestehende boolesche Runtime-Helper unterscheidet Abfragefehler nicht von
fehlender IPv6-Adresse. Bei Fehlern bleibt die bisherige IPv4-Fallbackanzeige
erhalten; ein eigener Status „unbekannt“ wurde nicht eingeführt. Insbesondere
erscheint ohne positiven Runtime-Nachweis kein Hinweis „nutzt IPv6“.

### Regressionen und ausgeführter gezielter Lauf

`tests/test_netmon_ipv6_ui.py` ergänzt fünf parametrisierte synthetische Fälle:

- IPv4-only: keine globale IPv6-Adresse, keine positive IPv6-Anzeige;
- aktive globale IPv6-Adresse: positiver Hinweis und grüne Farbe;
- positiver Runtime-Nachweis trotz negativer Profilfähigkeitsangabe: Anzeige
  folgt dem Runtime-Nachweis, die Privacy-Freigabe weiterhin der Konfiguration;
- fehlgeschlagene Runtime-Abfrage trotz IPv6-Profil: keine positive Anzeige;
- konfiguriertes IPv6 ohne Runtime-Adresse: keine positive Anzeige.

Dabei läuft der echte `ipv6_runtime_available_on_iface()`-Parser mit exakt
kontrollierten `run_cmd`-Ergebnissen. Die Tests prüfen den erwarteten
Abfragebefehl, Hinweistext, Farbe, beide IPv6-Schaltflächen sowie die unveränderte
Privacy-Freigabe und deren Hinweis. Das Dummy-Widget speichert zusätzlich die
Farbe. Alle bestehenden Testassertions bleiben erhalten, einschließlich des
ursprünglich fehlgeschlagenen IPv4-only-Sollfalls.

Vor dem Testlauf bestand die vorhandene Bubblewrap-Probe erneut: UID ungleich
0, NoNewPrivs, schreibgeschütztes Projekt, eigener Netzwerk-Namespace ohne
externe Route, kein Host-HOME und keine Host-Dienstsockets. Die gleiche
Bubblewrap-Konfiguration und der unveränderte Hostzugriffs-Guard blieben im
eigentlichen Lauf aktiv. Kein Audit-Fortsetzungsmodus und keine Guard-Umgehung.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short tests/test_netmon_ipv6_ui.py tests/test_firewall_controller.py \
  tests/test_host_access_guard.py tests/test_destructive_command_guard.py \
  tests/test_netmon_dns_consistency.py tests/test_netmon_killswitch.py \
  tests/test_netmon_vpn_slots.py
```

| Gruppe | Erreichte Fälle | Fehlerfreie Fälle | Assertion-Fehler | Teardown-Fehler | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| IPv6-UI / Profilfunktionen | 13 | 13 | 0 | 0 | 0 |
| Firewall-Controller | 16 | 16 | 0 | 0 | 0 |
| Hostzugriffs-Guard | 21 | 21 | 0 | 0 | 0 |
| Reboot-/Shutdown-Guard | 7 | 7 | 0 | 0 | 0 |
| DNS-Konsistenz, bis zum Stopp | 58 | 57 | 0 | 1 | 0 |
| Gesamt erreicht | 115 | 114 | 0 | 1 | 0 |

Pytest meldet **115 passed, 1 error in 0.69s**, Exitstatus 1: Beim betroffenen
Fall bestehen die fachlichen Assertions, sein Teardown scheitert jedoch am
blockierten Hostversuch. JUnit enthält 115 unterschiedliche Fälle, davon einen
mit Fehler; das sind nicht 116 verschiedene Fälle. Keine Warnungen oder Skips.
Die übrigen DNS-Tests sowie Killswitch- und VPN-Slot-Gruppen wurden durch diesen
Fail-Fast-Stopp nicht mehr erreicht. Historische Erfolge dieser Gruppen werden
nicht als neue Testergebnisse ausgegeben.

### Neuer Guard-Blocker und sicherer Stopp

Betroffen ist der bestehende Test
`tests/test_netmon_dns_consistency.py::test_apply_dns_blocks_when_vpn_active`.
Er faked die aktive VPN-Sperre, Warnung, Ausgabe und Controls-Aktualisierung,
aber nicht den zusätzlich aufgerufenen DNS-Policy-Statusrefresh:

```text
App.apply_dns()
  -> dns_controller.apply_dns(): VPN-Sperre, Rückgabewert False
  -> _refresh_dns_state(app, safe=True)
  -> App.refresh_dns_policy_status()
  -> dns_controller.refresh_dns_policy_status()
  -> run_cmd(["resolvectl", "status"], timeout=8)
  -> Hostzugriffs-Guard blockiert vor dem Prozessstart
```

Die sichere Callback-Hülle fängt die Guard-Ausnahme ab; der unveränderte
autouse-Teardown macht den Versuch trotzdem zum Fehler. Es wurde kein echtes
`resolvectl` ausgeführt und kein Host-DNS gelesen oder geändert. Die vorhandenen
Assertions zur VPN-Sperre, Warnung und Fehlermeldung bestehen. Diese zusätzliche
Mock-Lücke ist kein Nachweis einer durch die IPv6-Anzeigeänderung verursachten
DNS-Produktionsregression; der DNS-Pfad wurde nicht geändert.

Der Lauf wurde beim ersten neuen Guard-Befund automatisch gestoppt. Der Test,
die DNS-Produktionsfunktionen, der Guard und der Starter wurden nicht geändert.
Als gezielte spätere Testisolierung käme ausschließlich ein instanzlokaler
Fake für `app.refresh_dns_policy_status` in diesem Sperr-/Warnungstest infrage,
unter Erhalt aller bisherigen Assertions. Er wurde in diesem Auftrag nicht
ergänzt. Es gab weder globale Erfolgs-Mocks noch zusätzliche Freigaben.

**Die Gesamtsuite wurde nicht gestartet**, weil die ausdrücklich verlangte
Voraussetzung erfolgreicher gezielter Tests nicht erfüllt war. Ein vollständiger
grüner Gesamtlauf ist weiterhin nicht nachgewiesen; weitere verborgene
Test-Hostabfragen sind nicht ausgeschlossen.

Temporärer JUnit-/Xvfb-Nachweis:
`/tmp/user/1000/netmon-isolation-uln3b0se/{junit.xml,xvfb.log}`.
Die Probe lag in `/tmp/user/1000/netmon-isolation-z5wdulzb`.

### Qualität, Änderungsumfang und unveränderte Sicherheitsgrenzen

Ruff, Black-Check und Syntaxprüfung beider betroffenen Python-Dateien sowie
`git diff --check` bestanden. Der Black-Check innerhalb der Codex-Sandbox hing,
wurde abgebrochen und außerhalb mit einem Worker erfolgreich rein lesend
wiederholt. Keine Formatteränderungen an `app.py`; Black formatierte nur die
ergänzten Tests. Syntaxprüfung mittels `compile(..., "exec")` ohne Ausführung
oder pyc-Dateien. Es wurden keine Abhängigkeiten installiert.

Diese Runde änderte nur `netmon/app.py` (eine Anzeigebedingung),
`tests/test_netmon_ipv6_ui.py` (fünf Regressionen und Farberfassung im Testdouble)
und diese Berichtsergänzung. Der frühere Berichtsinhalt bleibt unverändert
erhalten. Alle übrigen erfassten Dateien bleiben gegenüber dem Rundeneinstieg
hashgleich, einschließlich der separaten About-Dateien, bestehender
Testisolierungsarbeiten, L-01-/F-01-/L-04-Produktionsbausteine und der beiden
Autorisierungsdokumente. `secure-browser/` wurde weder inhaltlich gelesen noch
verändert oder gestagt und blieb für die Testprozesse verdeckt. Index leer,
HEAD unverändert; keine echten privilegierten Operationen, Host-Netzwerkzugriffe,
Systemänderungen, Commits, Pushes, Installationen oder Deployments.

**IPv6-Anzeigekorrektur lokal nachgewiesen; Testabschluss durch den neuen
DNS-Isolationsbefund blockiert.** Der unabhängige Autorisierungsbroker wurde
nicht implementiert. Die Anzeigeänderung behebt den Same-UID-Autorisierungsblocker
nicht und erweitert das Sicherheitsversprechen nicht.
**L-04 bleibt TEILWEISE BEHOBEN – NACHARBEIT ERFORDERLICH.**

## Folgeauftrag – gezielte DNS-Testisolierung

Der nachfolgende Auftrag gab ausschließlich die Korrektur von
`test_apply_dns_blocks_when_vpn_active` frei, anschließend den Einzeltest und
bei Erfolg die genannten Gruppen. Bei einem weiteren Hostversuch war sofort
zu stoppen. Produktionscode und Hostzugriffs-Guard wurden nicht verändert.

Der bekannte Pfad führt nach der korrekten VPN-Sperre über
`dns_controller.apply_dns()` → `_refresh_dns_state(app, safe=True)` →
`App.refresh_dns_policy_status()` → `dns_controller.refresh_dns_policy_status()`
zu `run_cmd(["resolvectl", "status"], timeout=8)`.

Nur auf der synthetischen App-Instanz des freigegebenen Tests wurde
`refresh_dns_policy_status` durch einen deterministischen Fake ersetzt. Dieser
erfasst seinen Aufruf in einer lokalen Liste. Eine zusätzliche Assertion prüft
genau einen Aufruf. Die echte VPN-Sperrentscheidung und alle vier bestehenden
Assertions dieses Tests bleiben erhalten. Ein AST-Vergleich bestätigt außerdem
alle 392 zuvor vorhandenen Assertions der gesamten DNS-Testdatei unverändert
als Teilfolge; es wurde keine Assertion entfernt oder abgeschwächt. Der Fake
gilt weder für andere Tests noch für Produktionsinstanzen oder den Guard.

Vor beiden Testläufen bestand erneut die vorhandene Bubblewrap-Probe. Beide
Läufe nutzten unverändert den isolierten Starter und den aktiven Hostzugriffs-
Guard ohne Audit-Fortsetzungsmodus. Der Einzeltest bestand: **1 passed in
0.59s**, Exitstatus 0, keine Fehler oder Skips.

Daraufhin wurde die freigegebene Gruppenauswahl gestartet:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short tests/test_netmon_dns_consistency.py tests/test_netmon_ipv6_ui.py \
  tests/test_firewall_controller.py tests/test_host_access_guard.py \
  tests/test_destructive_command_guard.py tests/test_netmon_killswitch.py \
  tests/test_netmon_vpn_slots.py
```

Der Gruppenlauf stoppte in der ersten Gruppe, DNS, mit **61 passed, 1 error
in 0.77s**, Exitstatus 1. JUnit enthält 61 verschiedene Fälle: 60 vollständig
fehlerfrei und einen mit erfolgreichem fachlichen Call, aber Teardown-Fehler.
Keine Assertion-Fehler, Warnungen oder Skips. Der Einzeltest ist auch in diesen
61 Fällen enthalten; die Laufzahlen sind nicht additiv. Die späteren Gruppen
IPv6, Firewall, Guard, Killswitch und VPN-Slots wurden diesmal nicht erreicht.

### Weiterer Guard-Befund: DNS-Laufzeittransition

Der nächste bisher verdeckte Test ist
`tests/test_netmon_dns_consistency.py::test_apply_dns_blocks_during_dns_runtime_transition`.
Er setzt den VPN-Zustand auf False und die DNS-Laufzeittransition auf True.
Die echte Sperrlogik liefert korrekt False, Warnung, Ausgabe und Logmeldung;
alle bestehenden fachlichen Assertions bestehen. Der zusätzliche Statusrefresh
ist jedoch auch hier nicht gefaked:

```text
test_apply_dns_blocks_during_dns_runtime_transition
  -> App.apply_dns()
  -> dns_controller.apply_dns(): Transition-Sperre
  -> _refresh_dns_state(app, safe=True)
  -> _invoke_optional_app_callback()
  -> App.refresh_dns_policy_status()
  -> dns_controller.refresh_dns_policy_status()
  -> run_cmd(["resolvectl", "status"], timeout=8)
  -> subprocess.run() / _GuardedPopen
  -> Guard blockiert resolvectl vor dem Prozessstart
  -> sichere Callback-Hülle fängt die Ausnahme
  -> autouse-Teardown meldet den aufgezeichneten Hostversuch
```

Kein echtes `resolvectl` oder sudo wurde gestartet und kein Host-Netzwerkzustand
abgefragt oder geändert. Der unveränderte Guard verhindert ein grünes Ergebnis
trotz abgefangener Ausnahme. Es handelt sich um eine weitere lokale
Testisolationslücke, keinen Nachweis einer neuen Produktionsregression.

Gemäß Stoppvorgabe wurde dieser weitere Test nicht geändert. Keine zusätzlichen
Tests nach dem Blocker, keine globale Mock-Freigabe und keine Produktionsänderung.
**Die Gesamtsuite wurde nicht gestartet**, weil die gezielten Gruppen nicht
vollständig erfolgreich waren. Weitere verdeckte Hostversuche bleiben möglich.
Eine weitere Freigabe für eine ebenso lokale Isolationskorrektur des
Transition-Tests ist für den nächsten Validierungsschritt erforderlich.

Artefakte, jeweils `junit.xml` und `xvfb.log`:

- Einzeltest: `/tmp/user/1000/netmon-isolation-9_fpdcdv`;
- gestoppte Gruppenauswahl: `/tmp/user/1000/netmon-isolation-jhz042_m`.

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Ausgabe und
`git diff --check` bestanden. Diese Runde ergänzt ausschließlich vier Zeilen in
`tests/test_netmon_dns_consistency.py` und diesen Berichtsabschnitt. Bestehende
Teständerungen und der vorherige Berichtsinhalt bleiben erhalten. Hashvergleiche
bestätigen alle anderen erfassten Dateien als unverändert, einschließlich
Produktionscode, Guard, Starter und der fünf About-Dateien. `secure-browser/`
wurde nicht inhaltlich gelesen, geändert oder gestagt und blieb in den Tests
verdeckt. HEAD und Branch unverändert, Index leer. Keine Systemänderungen,
Commits, Pushes oder Deployments.

**Der freigegebene DNS-VPN-Sperrtest ist isoliert behoben; der neue
Transition-Testbefund blockiert den weiteren Testabschluss. L-04 bleibt
TEILWEISE BEHOBEN.** Die offene Same-UID-Autorisierungsfrage wurde nicht bearbeitet.

## Folgeauftrag – systematische DNS-Statusisolierung

Diese Runde untersucht die Mock-Struktur der gesamten DNS-Testdatei und führt
eine ausdrücklich angeforderte, eng begrenzte Status-Fixture ein. Der folgende
neue Befund stoppte den Lauf auftragsgemäß; die DNS-Gruppe ist weiterhin nicht
vollständig grün. HEAD bleibt `9944ce14650877848cb48a2ed531cd84424bcec3`.

### Reichweite und gewählte Strategie

`tests/test_netmon_dns_consistency.py` hatte keine gemeinsame automatische
Status-Fixture. Die Tests setzen überwiegend instanzlokale Fakten und Callbacks
oder ersetzen einzelne Modulabhängigkeiten per `monkeypatch`. Zu unterscheiden
sind insbesondere:

- Beabsichtigte Aktionen wie DNS-Profilanwendung, Drop-in-Schreiben und
  Dienststeuerung haben eigene gezielte Service-/Callback-Fakes. Diese bleiben
  unverändert; ein allgemeines erfolgreiches `run_cmd` wäre hier irreführend.
- Statusdarstellungs-, Health-/Leak- und Policytests verwenden unterschiedliche
  synthetische DNS-Ausgaben. Sie dürfen keine allgemeine Standardantwort erhalten.
- Von den sechs unmittelbaren `apply_dns()`-Tests hatte ausschließlich der
  Transition-Test noch keinen isolierten Statusrefresh. VPN-Sperre, Stealth-Auto,
  Zielschichtfehler, Erfolg und abgelehnte DNSSEC-Bestätigung besitzen bereits
  eigene Fakes mit jeweils passender Testaussage. Diese wurden nicht vereinheitlicht.
- Die DNS-Testdatei enthält außerdem allgemeine UI-Refresh-Tests. Dort kann ein
  zweiter Statusweg über die VPN-Statusanzeige und den DNS-Control-Service laufen;
  dieser ist vom Controller-Statusrefresh getrennt, siehe neuer Befund unten.

Die neue funktionslokale, nicht automatische Fixture `passive_dns_status` wird
nur vom Transition-Test und ihren beiden neuen Sicherheitsregressionen verlangt.
Sie ersetzt allein `netmon.dns_controller.run_cmd` durch einen Dispatcher:
**nur die exakte Liste `["resolvectl", "status"]`** erhält erfolgreich den festen
Text `Global\n    DNS Servers: 192.0.2.53\n`. Das ist eine synthetische Adresse
aus dem Dokumentationsnetz. Jeder andere Befehl samt Argumenten und Optionen
wird an die vor der Fixture gespeicherte echte Funktion weitergereicht. Kein
Prefix-Matching, kein pauschaler Erfolg und keine Änderung an Popen oder Guard.
`monkeypatch` nimmt die Moduländerung nach jedem betreffenden Test zurück.

Im Transition-Test bleiben die echte Sperrentscheidung, der echte Statusrefresh,
die Policyauswertung und die Widgetdarstellung aktiv. Ergänzt sind lokale
Statusvariablen, ein ausdrücklich leeres synthetisches WireGuard-Inventar auf
der Serviceinstanz und ein nicht existierender Drop-in-Pfad im eigenen
Temp-Verzeichnis. Das inventarisiert weder den Host noch verändert es die
eigentliche DNS-Transition-Sperre. Zusätzliche Assertions prüfen genau eine
Statusabfrage mit Timeout 8 und die dargestellten Resolver-/Konfliktwerte.
Die anderen DNS-Tests erhalten diese Fixture nicht.

Alle **393 beim Rundeneinstieg vorhandenen Assertions** bleiben unverändert.
Der vollständige frühere DNS-Dateitext wird bytegleich rekonstruiert, wenn man
ausschließlich die neue Fixture, ihre Regressionen, Imports und die neuen
Transition-Setup-/Prüfzeilen im Speicher entfernt. Es wurde keine vorhandene
Assertion entfernt, abgeschwächt, übersprungen oder als erwarteter Fehler markiert.

### Unveränderter Guard: absichtliche negative Nachweise

Zwei neue parametrisierte Fälle prüfen neben der erlaubten synthetischen
Statusantwort die Weitergabe von `["sudo", "-n", "true"]` und
`["resolvectl", "status", "--no-pager"]`. Für jeden Fall startet der Test innerhalb
des bestehenden Bubblewrap-Namespace eine eigene pytest-Kindsitzung mit dem
unveränderten `tests.conftest`-Guard und derselben opt-in Fixture.

Der Kindtest fängt die Guard-Ausnahme absichtlich ab. Trotzdem muss die
Kindsitzung wegen des im Teardown erfassten Hostversuchs mit Exitstatus 1
scheitern und den passenden Befehlsnamen in `Blocked host accesses` melden.
Der Elternfall prüft diese Bedingungen und die unveränderte Liste der erlaubten
Statusabfragen. Beide Elternfälle bestanden im DNS-Lauf. Das weist die echte
Guard-Weiterleitung einschließlich Fehlerbuchführung nach, ohne `_record_host_attempt`
oder den Popen-Konstruktor zu ersetzen und ohne sudo/resolvectl auszuführen.
Diese zwei geplanten negativen Nachweise sind keine unerwarteten Hostzugriffe
des Hauptlaufs; ihre absichtlich roten Kindsitzungen werden nicht als Fehler
der DNS-Gruppe gezählt. Beliebige native Unterprozesse bleiben auf die äußere
OS-Isolation angewiesen.

### Tatsächliche Testläufe und neuer sicherer Stopp

Vor beiden Läufen bestand erneut die vorhandene Bubblewrap-Probe. Der Starter,
Hostzugriffs-Guard und Audit-Modus blieben unverändert; der Audit-Fortsetzungsmodus
war nicht aktiv. Keine unisolierten Testläufe.

| Lauf | Vollständig fehlerfreie Fälle | Assertion-Fehler | Teardown-Fehler | Skips |
| --- | ---: | ---: | ---: | ---: |
| Transition-Einzeltest | 1 | 0 | 0 | 0 |
| DNS-Gruppe bis zum ersten neuen Blocker | 110 | 0 | 1 | 0 |

Der Einzeltest meldete **1 passed in 0.61s**, Exitstatus 0. Erst danach startete
die vollständige DNS-Auswahl mit `tests/test_netmon_dns_consistency.py`.
Der DNS-Lauf meldete **111 passed, 1 error in 2.28s**, Exitstatus 1. JUnit enthält
111 verschiedene Fälle, davon einen mit erfolgreichem fachlichen Call und
Teardown-Fehler. Keine Warnungen oder Skips. Der Einzeltest ist auch in der
DNS-Auswahl enthalten; Zahlen sind nicht additiv. Die zwei neuen negativen
Guardregressionen bestanden vor dem neuen Blocker.

Der neue, tatsächlich blockierte Fall ist
`test_refresh_updates_ufw_logging_light`. Seine UFW-, Internet-, Profil- und
Policy-Statusabhängigkeiten sind synthetisch, die allgemeine VPN-Statusanzeige
wird aber nicht ersetzt. Ein gefaktes `active_wg_profile()` ersetzt nicht
automatisch die davon unabhängige Funktion `is_vpn_active()`:

```text
test_refresh_updates_ufw_logging_light
  -> App.refresh()
  -> App.update_vpn_status_text()
  -> App.is_vpn_active()
  -> DNSControlService.read_resolvectl_status(timeout=6)
  -> Service.run_cmd(["resolvectl", "status"], timeout=6)
  -> netmon.core.command.run_cmd()
  -> subprocess.run() / _GuardedPopen
  -> Guard blockiert vor dem Prozessstart
  -> update_vpn_status_text() fängt die Ausnahme
  -> autouse-Teardown verhindert fälschlich grünen Hauptlauf
```

Dieser Service verwendet die beim Erstellen der Instanz übergebene
`netmon.app.run_cmd`-Referenz, nicht `dns_controller.run_cmd`. Die Fixture wurde
bewusst nicht global auf alle Kommando-Quellen ausgedehnt und ist für diesen
UI-Test auch nicht aktiviert. Keine echte Statusabfrage fand statt.

Die ergänzende rein lesende AST-/Aufrufprüfung identifiziert denselben noch
nicht isolierten Statusweg als Kandidaten in:

- `test_refresh_no_longer_starts_dns_consistency_loop`;
- `test_refresh_sets_internet_warning_on_first_failure_and_red_after_second`;
- `test_refresh_sets_internet_transition_yellow_during_dns_transition`.

Diese drei Fälle wurden nach dem Stopp nicht ausgeführt; die Einschätzung ist
statisch, keine zusätzliche Reproduktion. Andere Refresh-Tests ersetzen bereits
`update_vpn_status_text`; die zwei direkten VPN-Statusdarstellungstests setzen
`is_vpn_active` ausdrücklich synthetisch. Das ist keine Freigabe anderer,
bislang nicht erreichter Aufrufpfade. Für einen Folgeauftrag wären eine
instanzlokale Isolation der nachgelagerten VPN-Anzeige oder eine ausdrücklich
aktivierte, ebenfalls exakt begrenzte Statusantwort auf der jeweiligen
Serviceinstanz zu prüfen, ohne UFW-/Internet-/Sperrassertions zu ersetzen.

Gemäß Stoppvorgabe wurde keiner dieser zusätzlichen UI-Tests geändert. Keine
weiteren Tests nach dem Blocker, keine weiteren gezielten Gruppen und keine
Gesamtsuite: Die dafür erforderliche vollständig erfolgreiche DNS-Gruppe ist
nicht nachgewiesen. Weitere Hostabfragen bleiben möglich. Aus diesem Befund
folgt keine nachgewiesene Produktionsregression; Produktionscode ist unverändert.

Artefakte, jeweils `junit.xml` und `xvfb.log`:

- Transition-Einzeltest: `/tmp/user/1000/netmon-isolation-qotcs051`;
- gestoppter DNS-Lauf: `/tmp/user/1000/netmon-isolation-z2nd5ok2`.

### Abschlussgrenzen

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Ausgabe und
`git diff --check` bestanden. Diese Runde verändert ausschließlich
`tests/test_netmon_dns_consistency.py` und diese Berichtsergänzung. Frühere
Berichtsabschnitte, Produktionscode, Guard, Starter, About-Dateien und andere
erfasste Sicherheitsarbeiten bleiben unverändert. `secure-browser/` wurde weder
inhaltlich gelesen noch geändert oder gestagt und blieb für Tests verdeckt.
Index leer, Branch und HEAD unverändert. Keine echten privilegierten Operationen,
Host-Netzwerkzugriffe, Systemänderungen, Commits, Pushes oder Deployments.

**Transition-Sperrtest isoliert behoben; neuer UI-/Service-Statusweg blockiert
den Testabschluss. L-04 bleibt TEILWEISE BEHOBEN.** Der unabhängige
Same-UID-Autorisierungsblocker wurde nicht verändert und kein Broker implementiert.

## Folgeauftrag – vier bekannte UI-/Service-Kandidaten

Diese Runde untersucht die vier zuletzt benannten Kandidaten gemeinsam.
Alle rufen `App.refresh()` auf; ihr zusätzlicher passiver Statusweg ist
`update_vpn_status_text()` → `is_vpn_active()` →
`DNSControlService.read_resolvectl_status(timeout=6)` →
`service.run_cmd(["resolvectl", "status"], timeout=6)`.

Die jeweiligen Testaussagen sind UFW-Logging-Refresh, kein neuer
DNS-Konsistenzlauf, Internetampel gelb/rot bei aufeinanderfolgenden Fehlern und
Internetampel gelb während einer DNS-Transition. Keiner der vier Tests prüft
den Statusleser als eigene Funktion. Die zusätzliche DNS-Abfrage ist daher
eine isolierbare Darstellungsabhängigkeit. Bereits vorhandene Tests für
Statusleser/-darstellung und deren eigene synthetische Daten bleiben erhalten.

### Begrenzte Bindung der vorhandenen Fixture

Die neue, nicht automatische Fixture `passive_dns_service` verwendet die
bereits vorhandene `passive_dns_status`-Fixture. Ihre Bindefunktion wird nur
auf der ausdrücklich übergebenen Test-App aufgerufen. Sie prüft zunächst,
dass die Serviceinstanz noch denselben echten Kommando-Fallback wie die App
verwendet. Dann bindet sie den bestehenden, exakt auf
`["resolvectl", "status"]` begrenzten Dispatcher an `service.run_cmd` und setzt
auf dieser Instanz ein leeres synthetisches WireGuard-Inventar. Die Erkennung
bekommt damit einen vollständig synthetischen Zustand ohne aktives VPN.

`read_resolvectl_status()`, Parser und die echte Refresh-Logik bleiben aktiv.
Andere Kommandos oder abweichende resolvectl-Argumente werden weiterhin an
die echte, vom Guard geschützte Funktion weitergereicht. Es gibt keine
automatische Aktivierung für andere DNS-Tests, keine Klassen-/Prozess-/Netzwerk-
Mocks und keine Produktionsänderung. Die vier Kandidaten fordern beide Fixtures
ausdrücklich an. Zusätzliche Assertions prüfen je Refresh genau eine Statusabfrage
mit Timeout 6, beim Zweifach-Refresh entsprechend zwei.

Die zwei bisherigen negativen Guardregressionen behalten sämtliche Assertions.
Ihre Parametrisierung ist um den Service-Pfad erweitert: sudo und abweichende
resolvectl-Argumente sollen sowohl über Controller als auch gebundene Service-
Instanz geprüft werden. Die Kindprozesse verwenden den echten Guard samt
Fehlerbuchführung. **Diese vier parametrisierten Negativfälle wurden in dieser
Runde wegen des früheren Stoppkriteriums noch nicht ausgeführt.** Die positiven
Ergebnisse der vorherigen zwei Controller-Fälle bleiben historische Ergebnisse,
kein Nachweis für die nun ergänzte Service-Variante.

Alle **402 beim Rundeneinstieg vorhandenen Assertions** bleiben unverändert als
Teilfolge der jeweiligen Funktionen/Klassen erhalten; per AST geprüft. Keine
Assertions entfernt, abgeschwächt, deaktiviert oder als erwarteter Fehler markiert.

### Einzeltests und neuer unbekannter Guard-Blocker

Vor jedem gestarteten Einzeltest bestand erneut die bestehende Bubblewrap-Probe.
Starter und Guard blieben unverändert, kein Audit-Fortsetzungsmodus.

| Kandidat | Tatsächlicher Lauf dieser Runde |
| --- | --- |
| `test_refresh_updates_ufw_logging_light` | 1 bestanden in 0,61 s, Exitstatus 0 |
| `test_refresh_no_longer_starts_dns_consistency_loop` | Fachlicher Call bestanden; 1 Teardown-Fehler in 0,68 s, Exitstatus 1 |
| `test_refresh_sets_internet_warning_on_first_failure_and_red_after_second` | Nach neuem Blocker nicht gestartet |
| `test_refresh_sets_internet_transition_yellow_during_dns_transition` | Nach neuem Blocker nicht gestartet |

Keine Assertion-Fehler, Warnungen oder Skips. Der zweite Fall meldet
`1 passed, 1 error`, enthält aber nur einen unterschiedlichen JUnit-Fall.
Seine zusätzliche DNS-Statusassertion besteht: Der bekannte Service-Statusweg
ist hier ebenfalls isoliert. Der neue Fehler entsteht erst bei einer anderen
nachgelagerten Abfrage:

```text
test_refresh_no_longer_starts_dns_consistency_loop
  -> App.refresh()
  -> App.update_ufw_logging_light()
  -> App._security_query_log_level()
  -> run_cmd(["sudo", "-n", "ufw", "status", "verbose"], timeout=12)
  -> UFW-Locale-Normalisierung: env LANG=C LC_ALL=C vor ufw
  -> subprocess.run() / _GuardedPopen
  -> Guard blockiert sudo vor dem Prozessstart
  -> abgefangene Ausnahme; fachliche Assertions bestehen
  -> autouse-Teardown meldet den aufgezeichneten sudo-Versuch
```

Kein sudo/UFW-Prozess wurde gestartet. Dieser Befund zeigt insbesondere, dass
der aktive DNS-Status-Fake die separate produktive UFW-Abfrage nicht verdeckt.
Der Test prüft keinen UFW-Loggingzustand und hatte diesen zusätzlichen
Abfragepfad bislang nicht isoliert. Das ist eine Testisolationslücke; der
unveränderte Produktionscode belegt hier keine neue Produktionsregression.

Gemäß Stoppvorgabe wurde der unbekannte UFW-Blocker nicht korrigiert. Die beiden
übrigen vorbereiteten Kandidaten, negative Guardregressionen, vollständige
DNS-Gruppe, übrige gezielte Gruppen und Gesamtsuite wurden nicht gestartet.
Eine vollständige Freigabe der Testisolierung ist daher weiterhin nicht möglich.
Die statische Prüfung zeigt, dass auch die zwei ungestarteten Internetampel-
Kandidaten `update_ufw_logging_light()` bislang nicht ersetzen; sie könnten
denselben zusätzlichen UFW-Pfad erreichen. Das wurde nicht am Testlauf bestätigt.
Für eine spätere Freigabe wäre eine konkrete instanzlokale Isolation dieser
UFW-Statusabhängigkeit zu prüfen, unter Erhalt der Internet-/DNS-Assertions.

Artefakte, jeweils `junit.xml` und `xvfb.log`:

- erster Kandidat: `/tmp/user/1000/netmon-isolation-hxo01ioq`;
- zweiter Kandidat mit Guard-Stopp: `/tmp/user/1000/netmon-isolation-rj_zhxuu`.

### Erhaltener Änderungsumfang und Sicherheitsstatus

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Ausgabe und
`git diff --check` bestanden. Nur `tests/test_netmon_dns_consistency.py` und
diese Berichtsergänzung wurden in dieser Runde geändert. Die früheren
Berichtsabschnitte bleiben bytegleich erhalten. Hashvergleiche bestätigen
Produktionscode, Hostzugriffs-Guard, Starter, About-Dateien und andere erfasste
Sicherheitsarbeiten als unverändert. `secure-browser/` wurde nicht inhaltlich
gelesen, geändert oder gestagt und blieb für die Tests verdeckt. Index leer,
Branch und HEAD unverändert. Keine echten privilegierten Operationen,
Host-DNS-/Netzwerkzugriffe, Systemänderungen, Commits, Pushes oder Deployments.

**Der bekannte DNS-Control-Service-Pfad ist in den zwei ausgeführten Kandidaten
isoliert nachgewiesen; ein neuer UFW-Statusblocker verhindert den weiteren
Testabschluss. L-04 bleibt TEILWEISE BEHOBEN.** Der Same-UID-Autorisierungsblocker
wurde nicht verändert; kein unabhängiger Broker implementiert.

## Folgeauftrag – lokale UFW-Statusisolierung und erfolgreiches DNS-Gate

Die ausdrücklich freigegebene Codeänderung dieser Runde umfasst genau drei
Zeilen in `tests/test_netmon_dns_consistency.py`. Ausschließlich diese Tests
erhalten jeweils `app._security_query_log_level = lambda: "LOW"`:

- `test_refresh_no_longer_starts_dns_consistency_loop`;
- `test_refresh_sets_internet_warning_on_first_failure_and_red_after_second`;
- `test_refresh_sets_internet_transition_yellow_during_dns_transition`.

Vor der Änderung wurde die Verwendung des Werts geprüft:
`update_ufw_logging_light()` setzt damit den separaten UFW-Loggingwert und
gegebenenfalls dessen Widgets/Farbe. Die drei synthetischen Apps besitzen
keine UFW-Logging-Widgets. Ihre Aussagen betreffen DNS-Scheduling oder die
Internetampel, deren Farben und Transition-Text separat bestimmt und geprüft
werden. Der feste Wert verändert diese Aussagen nicht. Die echte
`update_ufw_logging_light()`-Logik bleibt aktiv; keine Änderung der DNS-Fixtures,
des Produktionscodes oder des Guards. Alle bestehenden Assertions bleiben
unverändert. Entfernt man ausschließlich die drei neuen Zuweisungen im Speicher,
stimmt der SHA256 der gesamten DNS-Testdatei wieder mit dem Rundeneinstieg überein.

### Ausgeführte Validierungsfolge

Vor jedem Testlauf bestand erneut die vorhandene Bubblewrap-Probe. Alle
Tests liefen mit unverändertem Hostzugriffs-Guard, ohne Audit-Fortsetzungsmodus,
ohne echte privilegierte Operationen oder Host-Netzwerkzugriffe.

1. Die vier bekannten UI-Kandidaten wurden jeweils einzeln ausgeführt: jeder
   **1 passed in 0.60s**, Exitstatus 0. Keine Fehler oder Skips.
2. Die vier negativen Guard-Regressionen wurden anschließend ausgeführt:
   **4 passed in 3.74s**, Exitstatus 0. Unerwartetes sudo sowie abweichende
   resolvectl-Argumente werden über Controller und gebundene Serviceinstanz
   an den echten Guard weitergereicht. Die absichtlich fehlschlagenden
   isolierten Kindsitzungen bleiben trotz abgefangener Ausnahme rot; die
   Elternfälle prüfen Rückgabestatus, Fehlerbuchführung und Befehlsnamen.
3. Die vollständige DNS-Gruppe bestand erstmals in dieser Folgeprüfung:
   **132 passed in 3.81s**, Exitstatus 0. Keine Assertion-Fehler, Teardown-Fehler,
   Warnungen oder Skips. Einzeltests und negative Guardfälle sind darin bereits
   enthalten; die Zahlen sind nicht additiv.
4. Erst danach wurden die weiteren freigegebenen Gruppen gestartet:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short tests/test_netmon_ipv6_ui.py tests/test_firewall_controller.py \
  tests/test_host_access_guard.py tests/test_destructive_command_guard.py \
  tests/test_netmon_killswitch.py tests/test_netmon_vpn_slots.py
```

| Gruppe | Erreichte Fälle | Vollständig fehlerfrei | Assertion-Fehler | Teardown-Fehler | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| IPv6 | 13 | 13 | 0 | 0 | 0 |
| Firewall-Controller | 16 | 16 | 0 | 0 | 0 |
| Hostzugriffs-Guard | 21 | 21 | 0 | 0 | 0 |
| Reboot-/Shutdown-Guard | 7 | 7 | 0 | 0 | 0 |
| Killswitch bis zum neuen Blocker | 18 | 17 | 0 | 1 | 0 |
| Gesamt dieses Gruppenlaufs | 75 | 74 | 0 | 1 | 0 |

Pytest meldet **75 passed, 1 error in 0.63s**, Exitstatus 1: 75 verschiedene
JUnit-Fälle, davon einer mit erfolgreichem fachlichen Call und Teardown-Fehler.
Keine Warnungen. Die übrigen Killswitch-Fälle und VPN-Slot-Gruppe wurden nicht
mehr erreicht. Die Voraussetzung für die Gesamtsuite war dadurch nicht erfüllt;
**die isolierte Gesamtsuite wurde nicht gestartet**.

### Neuer Guard-Blocker im Killswitch-Test

Betroffen ist
`tests/test_netmon_killswitch.py::test_vpn_off_shows_notice_when_killswitch_stays_active`.
Seine eigentliche Interfacebereinigung, Warnung, DNS-Nachbereitung und
UI-Aktualisierung sind bereits gefaked. Der Test setzt jedoch nur
`log_network_debug` und lässt die davon getrennte Diagnosefunktion
`debug_nm_state` aktiv. Diese wird vor und nach dem synthetischen VPN-Aus
aufgerufen:

```text
test_vpn_off_shows_notice_when_killswitch_stays_active
  -> App.vpn_off(ensure_sudo=False, refresh_ui=True)
  -> vpn_controller.vpn_off()
  -> App.debug_nm_state("vor VPN AUS") / ("nach VPN AUS")
  -> run_cmd(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,STATE",
              "connection", "show"], timeout=10)
  -> subprocess.run() / _GuardedPopen
  -> Guard blockiert nmcli jeweils vor dem Prozessstart
  -> debug_nm_state() fängt die Ausnahme und protokolliert sie
  -> autouse-Teardown meldet beide aufgezeichneten Hostversuche
```

Es handelt sich um zwei Versuche derselben ersten nmcli-Abfrage in einem
Testfall, nicht zwei unabhängige Testfehler. Die danach im Diagnosecode
vorgesehene `connection show --active`-Abfrage wird wegen der ersten Ausnahme
jeweils nicht erreicht. Kein nmcli-Prozess wurde gestartet, keine Verbindung
verändert. Die fachlichen Assertions zur erhaltenen Killswitch-Warnung bestehen.
Der Test erhält aber zu Recht kein vollständig grünes Ergebnis.

Gemäß Vorgabe stoppte der Lauf beim neuen Guard-Blocker. Killswitch-Testdatei,
Produktionscode und Guard wurden nicht geändert; keine zusätzlichen Tests
gestartet. Für eine spätere gesonderte Isolationskorrektur wäre ein konkreter
instanzlokaler Fake für den Diagnose-Collector `app.debug_nm_state` zu prüfen.
Auch der benachbarte Test ohne Killswitch-Warnung besitzt laut Quellprüfung
dieselbe fehlende Diagnoseisolation; er wurde in dieser Runde nicht erreicht.
Weitere bislang verdeckte Hostzugriffe sind nicht ausgeschlossen. Aus der
abgefangenen Diagnoseabfrage folgt keine nachgewiesene Produktionsregression.

Temporäre Artefakte, jeweils `junit.xml` und `xvfb.log`:

- vier Einzeltests: `/tmp/user/1000/netmon-isolation-jk3c7mx7`,
  `/tmp/user/1000/netmon-isolation-nflphljk`,
  `/tmp/user/1000/netmon-isolation-olfq2twq`,
  `/tmp/user/1000/netmon-isolation-7pedxs7s`;
- vier negative Guardfälle: `/tmp/user/1000/netmon-isolation-77jj5cq8`;
- vollständige DNS-Gruppe: `/tmp/user/1000/netmon-isolation-yms7ok4_`;
- gestoppter weiterer Gruppenlauf: `/tmp/user/1000/netmon-isolation-xd8u3dgo`.

### Erhaltene Grenzen

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Dateien und
`git diff --check` bestanden. Diese Runde änderte nur die drei beschriebenen
Fake-Zeilen und diese Berichtsergänzung. Frühere Berichtsabschnitte bleiben
bytegleich erhalten. Hashvergleiche bestätigen alle anderen erfassten Dateien
als unverändert, einschließlich Produktionscode, Guard, Starter, Killswitch-
und VPN-Slot-Tests, About-Arbeiten und Autorisierungsdokumenten.
`secure-browser/` wurde weder inhaltlich gelesen noch verändert oder gestagt
und blieb in den Tests verdeckt. Index leer, HEAD und Branch unverändert.
Keine Systemänderungen, echten privilegierten Operationen, Host-DNS-/Netzwerk-
zugriffe, Commits, Pushes oder Deployments.

**DNS-Isolations-Gate mit 132 bestandenen Tests erreicht; neuer nmcli-
Diagnoseblocker verhindert den weiteren Testabschluss. L-04 bleibt
TEILWEISE BEHOBEN.** Der Same-UID-Autorisierungsblocker bleibt unverändert.

## Folgeauftrag – instanzlokale NetworkManager-Diagnoseisolation

### Produktionsprüfung und begrenzte Änderung

Der tatsächliche Code von `App.debug_nm_state()` wurde vor der Änderung
einschließlich der verwendeten Profil-/Interfaceermittlung und der Aufrufstellen
in `vpn_controller.vpn_off()` geprüft. Er liest geladene Profilnamen, aktuelle
Interfaceinformationen und per `nmcli connection show` beziehungsweise
`connection show --active` Verbindungsstatus. Er erstellt ausschließlich eine
diagnostische Logzusammenfassung und führt keine Import-, Bereinigungs-,
Aktivierungs-, Lösch- oder Firewalloperation aus. Die verwendete
WireGuard-Erkennung kann ebenfalls lesende Statuskommandos und Logs auslösen.
Die Funktion ist daher diagnostisch, aber kein nebenwirkungsfreier Parser.

Alle Rückkehrpfade liefern nur `None`. Der Controller ruft sie vor und nach
dem VPN-Aus auf, wertet ihren Rückgabewert aber nicht aus. Erfolg/Abbruch,
Interfacebereinigung, Killswitch-Zustand und Warnungsentscheidung werden von
anderen Funktionen bestimmt. Ein Fake dieser Diagnose in den Warnungstests
erteilt keine Berechtigung und ersetzt keine Sicherheitsentscheidung.

Die drei benachbarten `vpn_off()`-Fälle wurden geprüft. Der DNS-Nachbereitungstest
besitzt bereits eigene Kommando-Fakes und prüft keine Diagnoseausgabe; er bleibt
unverändert. Nur die beiden bisher betroffenen Warnungsfälle erhalten einen
instanzlokalen, aufzeichnenden Fake:

- `test_vpn_off_shows_notice_when_killswitch_stays_active`;
- `test_vpn_off_does_not_show_killswitch_notice_when_killswitch_is_off`.

Jeweils ergänzte Zeilen: eine lokale Liste, eine Zuweisung
`app.debug_nm_state = lambda context: debug_calls.append(context)` und eine
Assertion `debug_calls == ["vor VPN AUS", "nach VPN AUS"]`. Der Fake liefert
wie die echte Diagnose `None`. Keine gemeinsame automatische Fixture und kein
globaler Kommando-/Prozess-/Netzwerk-Fake. Entfernt man diese insgesamt sechs
neuen Zeilen im Speicher, ist die gesamte Killswitch-Testdatei gegenüber dem
Rundeneinstieg bytegleich. Alle **222 bisherigen Assertions** bleiben erhalten.

Die beiden bestehenden Tests der echten Diagnose in
`tests/test_netmon_settings_tab.py` behalten ihre eigenen synthetischen
Kommando-/Verfügbarkeitsdaten. Ihre Testaussagen wurden nicht gefaked oder
entfernt; sie wurden in dieser Runde zusätzlich erfolgreich ausgeführt.

### Erfolgreiche gezielte Validierung

Vor jedem Testlauf bestand erneut die vorhandene Bubblewrap-Probe. Starter
und Hostzugriffs-Guard bleiben unverändert; kein Audit-Fortsetzungsmodus und
keine echten Hostoperationen.

| Prüfung | Ergebnis | Zeit |
| --- | --- | ---: |
| Warnung bei aktiv bleibendem Killswitch, einzeln | 1 bestanden | 0,53 s |
| Keine Warnung bei ausgeschaltetem Killswitch, einzeln | 1 bestanden | 0,54 s |
| Vollständige Killswitch-Gruppe | 47 bestanden | 2,58 s |
| Übrige gezielte Gruppen und zwei echte Diagnosetests | 263 bestanden | 4,08 s |

Alle diese Läufe: Exitstatus 0, keine Fehler, Warnungen oder Skips. Die
Einzeltests sind in den 47 Fällen enthalten und werden nicht nochmals addiert.
Die weitere Auswahl umfasst 72 VPN-Slot-, 132 DNS-, 13 IPv6-, 16 Firewall-,
21 Hostzugriffs-Guard-, sieben Reboot-/Shutdown-Guard- und zwei Diagnosetests.
Damit bestehen **310 verschiedene gezielte Fälle**. Die vier negativen
Controller-/Service-Guardfälle sind Bestandteil der DNS-Auswahl und bestehen
ebenfalls. Für diese freigegebene Auswahl wurde kein weiterer unerwarteter
Hostzugriff gemeldet.

Erst nach diesem vollständigen Erfolg wurde die isolierte Gesamtsuite gestartet:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests \
  tools/secure_browser_manager/tests/test_browser_container_builder.py
```

### Tatsächlicher Gesamtlauf: Setupgrenze statt neuem Guard-Blocker

Der Gesamtlauf stoppte gemäß unverändertem Fail-Fast nach **386 passed,
314 skipped, 1 error in 9.64s**, Exitstatus 1. JUnit bestätigt 701 erreichte
Fälle: 386 bestanden, 314 übersprungen, ein Setupfehler und keine
Assertion-Fehler. Das ist kein vollständig abgeschlossener oder grüner
Gesamtlauf. Die gezielten Zahlen sind nicht zum Gesamtlauf zu addieren.

Fehlernder Fall:
`tests/test_icon_http_security.py::test_real_https_keeps_certificate_and_hostname_checks[icons.example.com]`.
Seine Fixture `tls_contexts` erzeugt lokale synthetische Zertifikate mit
`openssl req -x509 -newkey rsa:2048 ...`. OpenSSL beendet sich dabei mit
Rückgabecode 1, bevor der eigentliche TLS-Test starten kann. Der Trace enthält
keinen Hostzugriffs-Guard-Blocker. Die genaue Ursache wurde anschließend mit
demselben Bubblewrap-Starter, erfolgreicher Probe und geladenem unveränderten
Guard diagnostiziert, ohne die Suite oder Repositorydateien zu verändern:

```text
Can't open "/usr/lib/ssl/openssl.cnf" for reading, No such file or directory
```

Die öffentlich lesbare Pfadmetadatenprüfung bestätigt einen Link von
`/usr/lib/ssl/openssl.cnf` nach `/etc/ssl/openssl.cnf`. Das isolierte `/etc`
enthält diese Datei nicht. Der Diagnoseaufruf verwendete ausschließlich
frische synthetische Zertifikats-/Schlüsselpfade im eigenen `/work/tmp`;
keine produktiven Schlüssel wurden gelesen oder ausgegeben. Es wurden keine
TLS-/Hostnameprüfungen abgeschaltet oder verfälscht.

Alle 314 Skips stammen laut JUnit aus der vorhandenen PHP-Fixture:
`PHP CLI required; optionally set NETMON_TEST_PHP`. In dieser Umgebung ist
keine PHP-CLI verfügbar; der in einer früheren Runde temporär bereitgestellte
Pfad existiert nicht mehr. Es wurden weder Tests deaktiviert noch PHP oder
andere Pakete installiert. Die Ergebnisse früherer PHP-Läufe ersetzen keinen
aktuellen Nachweis in dieser Umgebung.

Der vollständige Nachweis bleibt damit offen. Vor einem erneuten Gesamtlauf
wären eine ausdrücklich begrenzte synthetische OpenSSL-Konfiguration im
Test-Namespace und die isolierte Bereitstellung einer geeigneten PHP-CLI zu
prüfen. Kein pauschales Einbinden des Host-Konfigurations-/Schlüsselbaums und
keine Abschwächung der TLS-Prüfungen. Diese Umgebungsänderungen, der Teststarter
und die betroffene TLS-/PHP-Testimplementierung wurden in diesem Auftrag
nicht verändert. Weitere hinter dem Setupfehler liegende Guard-Blocker sind
nicht ausgeschlossen.

### Artefakte und erhaltene Grenzen

JUnit-/Xvfb-Artefakte:

- Warnungstest aktiv: `/tmp/user/1000/netmon-isolation-vt6lu7t6`;
- Warnungstest inaktiv: `/tmp/user/1000/netmon-isolation-de28coue`;
- vollständige Killswitch-Gruppe: `/tmp/user/1000/netmon-isolation-mbxe3frt`;
- weitere 263 Fälle: `/tmp/user/1000/netmon-isolation-f5wlllk0`;
- gestoppte Gesamtsuite: `/tmp/user/1000/netmon-isolation-x9h6vkdx`.

Die isolierte OpenSSL-Diagnose lag in
`/tmp/user/1000/netmon-isolation-4f7zpbka`; dort sind nur die eigene
Probe-/Diagnoseumgebung und gegebenenfalls synthetische Temporärdateien,
kein zusätzlicher pytest-Lauf mit JUnit.

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Dateien und
`git diff --check` bestanden. In dieser Runde wurden ausschließlich die sechs
beschriebenen Zeilen in `tests/test_netmon_killswitch.py` und diese
Berichtsergänzung geändert. Alle anderen erfassten Dateien, einschließlich
Produktionscode, Guard, Starter, DNS-/VPN-Slot-Tests, About-Arbeiten und
Autorisierungsdokumente, bleiben hashgleich. Frühere Berichtsabschnitte bleiben
bytegleich erhalten. `secure-browser/` wurde nicht inhaltlich gelesen,
verändert oder gestagt und blieb für Tests verdeckt. Branch und HEAD
unverändert, Index leer. Keine echten privilegierten Operationen,
Host-Netzwerkzugriffe, Systemänderungen, Installationen, Commits, Pushes oder
Deployments.

**Killswitch-Diagnoseisolation und alle 310 gezielten Fälle erfolgreich;
Gesamtnachweis wegen OpenSSL-Setupfehler und fehlender PHP-CLI unvollständig.
L-04 bleibt TEILWEISE BEHOBEN.** Die Same-UID-Autorisierungsfrage wurde nicht
verändert; kein unabhängiger Broker implementiert.

## Folgeauftrag – synthetische OpenSSL-Konfiguration im Test-Namespace

### Bestätigte Ursache und minimale Umgebungsänderung

Der zuvor gescheiterte Fall ist
`tests/test_icon_http_security.py::test_real_https_keeps_certificate_and_hostname_checks[icons.example.com]`.
Seine Fixture `tls_contexts` benötigt `openssl req` zum Erzeugen ausschließlich
synthetischer Zertifikate. Der Standardpfad `/usr/lib/ssl/openssl.cnf` verweist
auf `/etc/ssl/openssl.cnf`, das im isolierten `/etc` absichtlich nicht vorhanden
ist. Die frühere isolierte Diagnose hat genau diesen fehlenden Pfad bestätigt.

Geändert wurde ausschließlich die OpenSSL-Bereitstellung in
`tests/run_isolated_suite.py`: Jeder Lauf legt in seinem frischen privaten
Ausgabeverzeichnis `config/openssl.cnf` mit Dateimodus 0600 an. Der enthaltende
Konfigurationsordner hat bereits Modus 0700. Inhalt:

```ini
[req]
prompt = no
distinguished_name = test_dn
[test_dn]
CN = isolated-test.invalid
```

Die bereits geleerte Namespace-Umgebung erhält
`OPENSSL_CONF=/work/config/openssl.cnf`. Der bestehende `/work`-Bind macht diese
synthetische Datei zugänglich; es gibt **keinen zusätzlichen Host-Mount** und
keine Lektüre/Kopie der Host-OpenSSL-Konfiguration. Die Einstellung wirkt nur
in dieser Testumgebung und ihren Kindprozessen. Keine Änderung der globalen
OpenSSL-Einstellungen, Zertifikatsspeicher, Provider-/TLS-Policy oder der
Produktionsumgebung. Die CLI-Argumente des bestehenden Tests bestimmen
weiterhin Zertifikatssubjekt und SAN.

Die bestehende Probe prüft zusätzlich den festen Namespacepfad und die
Verfügbarkeit der synthetischen Datei. Alle bisherigen Mount-, Netzwerk-,
UID-/Capability-, NoNewPrivs- und Dienstsocket-Grenzen bleiben erhalten.
Der Hostzugriffs-Guard und sämtliche Testassertions wurden nicht verändert.
Entfernt man ausschließlich die neue Dateierzeugung, die Namespace-Variable
und die zwei Probe-Assertions im Speicher, ist der gesamte frühere Starter
gegenüber dem Rundeneinstieg bytegleich.

### Betroffener TLS-Test und erneuter Gesamtlauf

Vor beiden Läufen bestand die erweiterte Bubblewrap-Probe. Zunächst wurde
ausschließlich der betroffene Test mit beiden vorhandenen Parametern ausgeführt:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short \
  tests/test_icon_http_security.py::test_real_https_keeps_certificate_and_hostname_checks
```

Ergebnis: **2 passed in 0.22s**, Exitstatus 0, keine Fehler oder Skips. Der
passende Hostname funktioniert, der falsche Hostname wird weiterhin durch
`SSLCertVerificationError` abgewiesen. Die bestehenden Assertions zu
`check_hostname` und `CERT_REQUIRED` bleiben aktiv. Die minimale req-Konfiguration
reicht somit für den tatsächlichen Zertifikatsaufbau aus, ohne die
kryptografischen Verifikationsprüfungen zu ersetzen.

Erst danach wurde die vollständige bisherige Python-Auswahl erneut gestartet:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests \
  tools/secure_browser_manager/tests/test_browser_container_builder.py
```

Der Lauf kam über den OpenSSL-Setupfehler hinaus und stoppte bei einem neuen
unerwarteten Hostversuch: **950 passed, 314 skipped, 1 error in 18.55s**,
Exitstatus 1. JUnit enthält 1.264 unterschiedliche Fälle: 949 vollständig
fehlerfrei, 314 übersprungen und einen Fall mit erfolgreichem fachlichen Call,
aber Teardown-Fehler. Keine Assertion-Fehler oder Warnungen. Der erfolgreiche
Call des betroffenen Falls ist in den 950 pytest-Aufrufen enthalten; es sind
nicht 1.265 verschiedene Fälle. Kein vollständiger grüner Gesamtnachweis.

**Alle 314 PHP-Tests sind ausdrücklich NICHT VALIDIERT.** Sämtliche Skips
tragen unverändert den Grund `PHP CLI required; optionally set NETMON_TEST_PHP`.
PHP wurde nicht installiert, bereitgestellt oder durch zusätzliche Hostzugriffe
freigegeben. Frühere PHP-Ergebnisse sind kein aktueller Nachweis dieses Laufs.

### Neuer Guard-Blocker: Game-Mode-Rollback und DNS-Whitelist

Betroffen ist
`tests/test_netmon_lynis_output.py::test_disable_game_mode_rolls_back_optional_ufw_exception_rules`.
Der Test faked UFW-/Killswitch-Aktionen sowie mehrere Statuscallbacks, aber
nicht die zusätzlich ausgelöste DNS-Whitelist-Neuberechnung:

```text
test_disable_game_mode_rolls_back_optional_ufw_exception_rules
  -> App.disable_game_mode()
  -> App._apply_game_mode_dns_guard(True)
  -> App.rebuild_dns_guard_whitelist()
  -> App.is_vpn_active()
  -> DNSControlService.read_resolvectl_status(timeout=6)
  -> run_cmd(["resolvectl", "status"], timeout=6)
  -> subprocess.run() / _GuardedPopen
  -> Guard blockiert resolvectl vor dem Prozessstart
  -> _apply_game_mode_dns_guard() fängt die Ausnahme
  -> autouse-Teardown verhindert fälschlich grünen Lauf
```

Kein echtes resolvectl oder anderer Host-Netzwerkzugriff wurde ausgeführt.
Die bestehenden fachlichen Rollback-Assertions bestehen, der Fall wird wegen
des aufgezeichneten Hostversuchs trotzdem als fehlerhaft gewertet. Der Guard
bleibt unverändert wirksam. Es wurde nach diesem Befund kein weiterer Test
gestartet. Die Game-Mode-/DNS-Produktionsfunktionen und der betroffene Test
wurden nicht verändert. Eine spätere Testisolierung muss die fachliche
Wiederherstellung des DNS-Guards berücksichtigen; die Whitelist-Logik darf
nicht pauschal als bloße Diagnose übersprungen werden. Weitere noch nicht
erreichte Hostzugriffe sind nicht ausgeschlossen.

### Nachweise und Änderungsgrenzen

Artefakte, jeweils `junit.xml` und `xvfb.log`:

- beide TLS-Parameter: `/tmp/user/1000/netmon-isolation-a440na3l`;
- gestoppter Gesamtlauf: `/tmp/user/1000/netmon-isolation-ewwtyjth`.

Die jeweilige synthetische OpenSSL-Datei liegt zusätzlich im Unterordner
`config/openssl.cnf` dieser isolierten Ausgabeordner. Die vorherigen 310
gezielten Erfolge bleiben historische Nachweise; sie wurden in dieser Runde
nicht zusätzlich als eigene Auswahl wiederholt oder zu den Gesamtzahlen addiert.

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Dateien und
`git diff --check` bestanden. Diese Runde änderte ausschließlich den
Teststarter und diese Berichtsergänzung. Alle übrigen erfassten Dateien,
einschließlich Produktionscode, Hostzugriffs-Guard, bisherigen Testkorrekturen,
About-Arbeiten und Autorisierungsdokumenten, bleiben hashgleich. Frühere
Berichtsabschnitte bleiben bytegleich erhalten. `secure-browser/` wurde nicht
inhaltlich gelesen, geändert oder gestagt und blieb für Tests verdeckt.
Index leer, Branch und HEAD unverändert. Keine Systemänderungen,
Installationen, echten privilegierten Operationen, Host-Netzwerkzugriffe,
Commits, Pushes oder Deployments.

**OpenSSL-Setupfehler lokal behoben; Gesamtlauf durch neuen Game-Mode-/DNS-
Guardbefund gestoppt. 314 PHP-Tests nicht validiert. L-04 bleibt
TEILWEISE BEHOBEN.** Die Same-UID-Autorisierungsfrage bleibt unverändert.

## Folgeauftrag – Game-Mode-Rollback mit echter VPN-/DNS-Guard-Auswertung

### Ursachen- und Fixtureanalyse vor der Änderung

Der zuvor blockierte Pfad wurde im Produktionscode vollständig nachverfolgt:
`disable_game_mode()` → `_apply_game_mode_dns_guard(True)` →
`rebuild_dns_guard_whitelist()` → `is_vpn_active()` →
`DNSControlService.read_resolvectl_status(timeout=6)` →
`run_cmd(["resolvectl", "status"], timeout=6)`.

**`is_vpn_active()` ist hier keine bloße Diagnose.** Die echte Whitelistlogik
wählt bei positivem VPN-Nachweis `get_active_vpn_dns()`, sonst bei aktivem DoT
die gewählten DoT-Resolver und andernfalls Benutzer-/System-DNS. Diese Liste
wird als `dns_guard_allowed_dns` gespeichert und später zur Abweichungserkennung
herangezogen. Auch `run_dns_guard_check_once()`, DNS-Erzwingung/Policy und die
Game-Mode-Aktivierung verwenden den VPN-Zustand. Die UFW-/Killswitch-
Rollbackaktionen in `disable_game_mode()` richten sich hingegen nach dem
gespeicherten Game-Mode-Zustand und ihren eigenen Ergebnissen; der DNS-Guard
wird anschließend separat wieder aktiviert. Deshalb wäre ein pauschales
Ersetzen von `is_vpn_active()` oder der Whitelistberechnung unzureichend.

Vor einer Änderung wurden die bestehenden, ausdrücklich aktivierten Fixtures
`passive_dns_status` und `passive_dns_service` aus der DNS-Testdatei geprüft.
Der bestehende Servicebinder erhält den echten Statusleser und Parser, bindet
den exakt begrenzten Statusdispatcher an die betreffende Serviceinstanz und
stellt bereits ein leeres synthetisches Interfaceinventar bereit. Der
WG-Linkname im Status wird weiterhin vom echten Parser als VPN erkannt.
Diese vorhandene synthetische Inventargrenze wurde nicht erweitert.

Die bisher feste Standardantwort beschreibt nur den VPN-inaktiven Fall. Daher
erhält ausschließlich die vorhandene Status-Fixture eine optionale indirekte
pytest-Parametrisierung: ohne `request.param` exakt dieselbe bisherige Antwort;
mit explizitem Parameter den jeweiligen synthetischen Statustext. Nur die
exakte Abfrage `["resolvectl", "status"]` wird simuliert. Jeder andere Befehl
wird weiterhin an den ursprünglichen, vom unveränderten Guard geschützten
Fallback weitergereicht. Kein autouse, keine Klassen-/Prozess-/Netzwerk-Mocks
und keine pauschale Freigabe. Die Fixtures werden nur für die beiden
Rollbacktests zusätzlich importiert und ausdrücklich angefordert.

### Tatsächliche Sicherheitslogik und Regressionen

Diese beiden vorhandenen Tests werden jeweils über drei realistische
resolvectl-Textausgaben parametrisiert:

- `test_disable_game_mode_rolls_back_optional_ufw_exception_rules`;
- `test_disable_game_mode_restores_previous_state`.

| Synthetischer Zustand | Echte VPN-Erkennung | Erwartete Whitelist | Echte Guardbewertung |
| --- | --- | --- | --- |
| Physischer Link `enp1s0`, DNS `192.0.2.53`, kein VPN/DoT | False | `192.0.2.53` über System-DNS-Fallback | `ok` |
| Link `wg0` mit ausschließlich `10.8.0.1` als DNS | True | ausschließlich `10.8.0.1` | `ok` |
| `wg0` mit `10.8.0.1` plus physischer DNS `192.0.2.53` | True | weiterhin ausschließlich `10.8.0.1` | `problem` |

Die Antwort enthält Linkabschnitte, DNS-Felder und ausgeschaltetes DoT.
`192.0.2.53` stammt aus dem Dokumentationsnetz, `10.8.0.1` ist ein synthetischer
privater VPN-Resolver. Es werden keine echten DNS- oder Interfaceabfragen
durchgelassen.

Die Tests führen die echten Methoden `is_vpn_active()`,
`get_active_vpn_dns()`/`get_current_dns()`, `rebuild_dns_guard_whitelist()` und
`_apply_game_mode_dns_guard()` aus. In genau diesen beiden Tests wurde auch
der bisherige No-op für `run_dns_guard_check_once()` entfernt: Die echte
Guardprüfung läuft mit `auto_repair=False`. Dafür wurden lediglich synthetische
Statusvariablen ergänzt. Die bereits bestehenden UI-/Statuscallbacks und
privilegierten UFW-/Killswitch-Aktions-Fakes bleiben erhalten.

Zusätzliche Assertions prüfen VPN-Ergebnis, Guard-Aktivierung, Whitelist,
Bewertung `ok` beziehungsweise `problem`, zurückgesetztes Prüf-Running-Flag
und tatsächlich erfasste Statusabfragen. Alle **710 beim Rundeneinstieg
vorhandenen Assertions** der Lynis-/Security-Testdatei bleiben als unveränderte
Teilfolge je Funktion/Klasse erhalten; per AST-Fingerprints geprüft. Keine
vorhandene Assertion entfernt, abgeschwächt oder als erwarteter Fehler markiert.

Der gemischte DNS-Fall zeigt ausdrücklich: Ein erfolgreicher Rückgabewert des
Game-Mode-Rollbacks bedeutet nicht automatisch sauberes DNS. Die realen
UFW-/Killswitch-Rollbackassertions bestehen, während der echte DNS-Guard die
Abweichung weiterhin als `problem` meldet. Es wird keine automatische
Reparatur oder produktive Netzwerkänderung ausgelöst. Weitergehende Aussagen
über den bislang nicht behandelten DoT-Zweig oder reale Hostzustände werden
nicht aus diesen synthetischen Fällen abgeleitet.

### Testfolge und neuer sicherer Stopp

Vor jedem gestarteten Testlauf bestand erneut die vorhandene Bubblewrap-Probe.
OpenSSL-Testkonfiguration, Starter und Hostzugriffs-Guard blieben unverändert;
kein Audit-Fortsetzungsmodus und keine unisolierten Tests.

| Lauf | Ergebnis | Zeit |
| --- | --- | ---: |
| Zuvor betroffener Rollbacktest, drei Zustände | 3 bestanden | 0,60 s |
| Game-Mode-Gruppe: `tests/test_netmon_lynis_output.py -k game_mode` | 19 bestanden, 159 nicht ausgewählt | 0,63 s |
| Komplette DNS-Gruppe, einschließlich vier negativer Guardfälle | 132 bestanden | 2,74 s |

Alle drei Läufe Exitstatus 0, keine Fehler, Warnungen oder Skips. Nicht
ausgewählte Fälle sind keine Skips. Der 3er-Lauf ist bereits in der Game-Mode-
Gruppe enthalten und wird nicht addiert. Der zusätzliche DNS-Lauf bestätigt,
dass die neue optionale Antwortparametrisierung den Standard der bisherigen
Tests und die Controller-/Service-Guardregressionen nicht verändert.

Erst nach diesen Erfolgen wurde die Python-Gesamtauswahl erneut gestartet.
Ergebnis: **974 passed, 314 skipped, 1 error in 17.36s**, Exitstatus 1.
JUnit bestätigt 1.288 verschiedene Fälle: 973 vollständig fehlerfrei,
314 übersprungen und einen Fall mit erfolgreichem fachlichen Call, aber
Teardown-Fehler. Keine Assertion-Fehler oder Warnungen. Der neue Blocker ist
nicht Teil des Game-Mode-Pfades:

```text
tests/test_netmon_lynis_output.py::
test_run_security_baseline_checks_evaluates_special_cases
  -> security_audit_controller.run_security_baseline_checks()
  -> _detect_hardening_privilege_context(app)
  -> check_sudo_nopasswd()
  -> subprocess.run(["sudo", "-n", "true"])
  -> _GuardedPopen blockiert sudo vor dem Prozessstart
  -> check_sudo_nopasswd() fängt die Ausnahme und liefert False
  -> autouse-Teardown meldet den aufgezeichneten Hostversuch
```

Der Test besitzt synthetische Baseline-Kommandodaten über `run_cmd_fn`, aber
die vorgeschaltete Privilegienerkennung verwendet separat die echte
`check_sudo_nopasswd()`-Funktion. Kein sudo-Prozess wurde gestartet und kein
Timestamp erneuert. Die fachlichen Assertions bestehen, der Test wird wegen
des aufgezeichneten Versuchs trotzdem als fehlerhaft gewertet.
Nach diesem neuen Guard-Befund wurde kein weiterer Test gestartet. Die
Privilegienerkennung und ihr Test wurden nicht verändert; insbesondere wurde
keine erfolgreiche Autorisierung pauschal gefaked. Weitere verdeckte
Hostzugriffe und ein vollständiger grüner Gesamtlauf bleiben ungeprüft.

### Konkreter Nachweis der 314 PHP-Skips

Die JUnit-Datei des aktuellen Gesamtlaufs ordnet sämtliche Skips folgenden
konkreten Testdateien zu, identisch zum vorherigen Lauf:

| Testdatei | Übersprungene Fälle | Skip-Grund |
| --- | ---: | --- |
| `tests/test_download_statistics.py` | 63 | `PHP CLI required; optionally set NETMON_TEST_PHP` |
| `tests/test_download_statistics_auth.py` | 185 | derselbe Grund |
| `tests/test_download_statistics_limits.py` | 66 | derselbe Grund |
| Gesamt | 314 | fehlende PHP-CLI |

Die Session-Fixture `php()` in `tests/test_download_statistics.py` (Zeilen
27–32) prüft `NETMON_TEST_PHP` beziehungsweise `shutil.which("php")` und ruft
bei fehlendem Interpreter genau `pytest.skip()` mit dieser Meldung auf.
Die Authentifizierungs- und Limit-Testdateien importieren diese Fixture aus
derselben Datei. Es handelt sich nicht um bewusst deaktivierte Tests oder
bestätigte Funktionserfolge. **Alle 314 PHP-Fälle sind weiterhin NICHT
VALIDIERT.** Keine PHP-Installation, kein Interpreter-Mount und keine neuen
Hostzugriffsfreigaben.

### Nachweise und erhaltener Umfang

Artefakte, jeweils `junit.xml` und `xvfb.log`:

- betroffener Einzeltest: `/tmp/user/1000/netmon-isolation-_3zqg4bn`;
- Game-Mode-Gruppe: `/tmp/user/1000/netmon-isolation-12u6_bmm`;
- DNS-Regressionsgruppe: `/tmp/user/1000/netmon-isolation-6xx5x4iy`;
- gestoppte Gesamtsuite: `/tmp/user/1000/netmon-isolation-bw1o5pl7`.

Ruff, Black-Check, Syntaxprüfung ohne Ausführung/pyc-Dateien und
`git diff --check` bestanden. Diese Runde verändert ausschließlich die
optionale Antwortparametrisierung in `tests/test_netmon_dns_consistency.py`,
die beschriebenen Game-Mode-Regressionsdaten und zwei Rollbacktests in
`tests/test_netmon_lynis_output.py` sowie diesen Berichtsabschnitt. Alle anderen
erfassten Dateien bleiben hashgleich, einschließlich Produktionscode,
Hostzugriffs-Guard, Starter/OpenSSL-Konfiguration, About-Arbeiten und bisherigen
Sicherheitskorrekturen. Frühere Berichtsabschnitte bleiben bytegleich erhalten.
`secure-browser/` wurde nicht inhaltlich gelesen, geändert oder gestagt und
blieb in den Tests verdeckt. Index leer, Branch und HEAD unverändert. Keine
Systemänderungen, echten privilegierten Operationen, Host-DNS-/Netzwerkzugriffe,
Installationen, Commits, Pushes oder Deployments.

**Game-Mode-Rollback mit echter VPN-/DNS-Guard-Auswertung lokal geprüft;
Gesamtlauf durch neuen Baseline-Privilegien-Guardbefund gestoppt. 314 PHP-Fälle
nicht validiert. L-04 bleibt TEILWEISE BEHOBEN.** Die Same-UID-Autorisierungsfrage
bleibt unverändert.

## Security-Baseline: eng begrenzte sudo-Probe-Isolation

### Ursache, Sicherheitsentscheidungen und Testgrenze

Der zuvor aufgezeichnete Aufrufpfad lautet:
`test_run_security_baseline_checks_evaluates_special_cases()` →
`run_security_baseline_checks()` → `_detect_hardening_privilege_context()` →
`check_sudo_nopasswd()` → `run_cmd(["sudo", "-n", "true"])`.
Die vorhandenen synthetischen Baseline-Kommandodaten isolierten diesen separat
ausgeführten Autorisierungsprobe-Aufruf nicht.

Das Ergebnis ist sicherheitsrelevant: Es bestimmt `has_sudo_session`,
`root_available` und die Privilegienquelle. Diese beeinflussen unter anderem
den Lesepfad für Shadow-/PAM-/Dateirechte-Prüfungen, die Verwendung von
`sudo -n bash -lc` sowie Ergebnisfelder wie `root_used`. Deshalb wird weder
die gesamte Kontextermittlung noch die Baseline-Auswertung ersetzt.
Keine Änderung am produktiven Autorisierungsvertrag.

Die neue funktionslokale Opt-in-Fixture `synthetic_sudo_probe` in
`tests/test_netmon_lynis_output.py` ersetzt ausschließlich die externe Antwort
auf exakt `["sudo", "-n", "true"]` mit den tatsächlich verwendeten
`subprocess.run`-Optionen (`PIPE`, `STDOUT`, Textmodus, Timeout 3, `check=False`).
Andere Argumente oder Optionen gehen an den unveränderten realen Runner und
damit den Hostzugriffs-Guard. Nur die `subprocess`-Modulbindung in
`netmon.core.command` wird vorübergehend durch einen delegierenden Proxy
ersetzt; das globale `subprocess.run`, `Popen`, EUID, Guard und Produktionscode
bleiben unverändert. Die Fixture verlangt eine nicht privilegierte Test-UID.

Die vorhandenen DNS-Fixtures sind hierfür fachlich ungeeignet; bestehende
Privilegien-Einzeltests ersetzen teils den ganzen Kontext und prüfen einen
anderen Vertrag. Daher eine eigene, ausdrücklich aktivierte Fixture statt
Autouse oder globaler Prozessfreigabe. 66 weitere statisch identifizierte
Baseline-Tests, deren echte Kontextermittlung denselben Probe-Aufruf erreicht,
aktivieren sie explizit mit `usefixtures`, standardmäßig ohne Sitzung.
Unbeteiligte Tests erhalten keine automatische Isolation.

Der betroffene Haupttest läuft zusätzlich mit und ohne verfügbare Sitzung.
Beide Varianten führen die echte Kontextermittlung und Baseline-Auswertung
aus. Der schon vorhandene synthetische Baseline-Runner akzeptiert im positiven
Fall zusätzlich den erwarteten sudo-Präfix; es werden keine Root-Kommandos
ausgeführt. Die Probe muss genau einmal aufgerufen werden. Geprüft werden
Privilegienquelle, tatsächliche Wahl des synthetischen sudo-Lesepfads sowie
`root_available` und `root_used` für Shadow-, PAM- und Dateirechte-Prüfungen.
Die ursprüngliche Log-Assertion für fehlende Sitzung bleibt in dieser
Variante erhalten; die positive Variante besitzt eine eigene exakte
Log-Assertion. Alle zuvor vorhandenen 725 Assert-ASTs der Testdatei sind
einschließlich ihrer Häufigkeit je Funktion/Klasse erhalten (SHA256-Vergleich
der AST-Darstellungen als Multimenge gegen den Rundenbeginn).

Zwei neue negative Guard-Fälle starten innerhalb der bestehenden Isolation
je einen isolierten pytest-Kindprozess mit der Fixture, einmal pro
Sitzungszustand. Der abweichende Befehl `["sudo", "-n", "id"]` muss vor
Prozessstart blockiert werden. Assertions verlangen Rückgabecode 1,
`Blocked host accesses:` und den aufgezeichneten sudo-Versuch. Auch ein
Abfangen der Ausnahme im Kindtest darf den Guard-Teardown nicht umgehen.
Diese geplanten negativen Kindtests sind Teil der grünen Eltern-Tests.

### DNS-Leak-Schutz: nachgewiesene Aussagen und offene Nachweise

Die Produktionslogik und alle bisherigen DNS-Assertions bleiben unverändert.
Die beiden vorhandenen parametrisierten Game-Mode-Rollbacktests führen
weiterhin die echte VPN-Erkennung, Whitelistbildung und DNS-Guard-Auswertung
aus, jeweils mit drei synthetischen Zuständen:

| Zustand | Erwartete Whitelist | Erwarteter Guardzustand |
| --- | --- | --- |
| VPN aus, physischer DNS `192.0.2.53` | `192.0.2.53` | `ok` |
| VPN an, ausschließlich VPN-DNS `10.8.0.1` | `10.8.0.1` | `ok` |
| VPN an, zusätzlich physischer DNS | ausschließlich `10.8.0.1` | **`problem`** |

Der letzte Fall ist eine erwartete Negativprüfung und darf nicht auf `ok`
geändert werden. Der physische Resolver wird nicht autorisiert. Die
DNS-Gruppe prüft außerdem unter anderem
`test_rebuild_dns_guard_whitelist_switches_between_vpn_and_manual`,
`test_evaluate_dns_policy_flags_global_dns_with_vpn`,
`test_use_user_dns_blocks_when_vpn_active`,
`test_apply_dns_blocks_when_vpn_active` und
`test_enforce_dns_policy_prefers_vpn_when_active`.
Die Killswitch-Regressionsgruppe kontrolliert Default-Deny-Kommandos,
Entfernung globaler DNS-Freigaben und Ablehnung solcher Restregeln.
Alle externen Kommandodaten bleiben synthetisch; reale Regeln werden nicht
verändert und der Guard wird nicht umgangen.

Die statische Prüfung von `rebuild_dns_guard_whitelist()` zeigt im aktiven
VPN-Zweig keine Übernahme physischer Resolver, auch bei leerem VPN-DNS-Ergebnis.
`enforce_dns_policy()` wählt bei aktivem VPN den VPN-DNS-Pfad. Dennoch fehlt ein
vollständiger Regressionstest für einen unerreichbaren VPN-DNS-Server bei
weiter aktivem Tunnel einschließlich Fehler-, Wiederholungs- und
Wiederherstellungspfaden. Der vorhandene Test für fehlende Ziel-DNS prüft
einen synthetisch leeren Whitelistzustand, nicht diese Ende-zu-Ende-Situation.
Tests des ISP-/Cloudflare-Restores verwenden VPN aus und sind hierfür kein
Nachweis. Kein Paketfilter-/Kernel-Datenpfadnachweis und kein vollständiger
Nachweis pro erlaubtem DNS-Server über sämtliche IPv4-/IPv6-Firewallpfade.
Die Meldung `problem` allein beweist keine Paketblockierung. Die verbindliche
Architektur bleibt: VPN an erlaubt ausschließlich autorisierte VPN-DNS-Server;
ein Ausfall darf keinen ungeschützten Fallback freigeben. Diese Runde ändert
daran nichts und behauptet keine umfassendere Validierung als nachgewiesen.

### Ausgeführte Reihenfolge und Ergebnisse

Vor den Läufen wurde die vorhandene Bubblewrap-Probe geprüft: unprivilegierte
UID, `NoNewPrivs`, schreibgeschütztes Repository, privater Netzwerk-Namespace
ohne Host-Routen, keine Host-Dienste-/D-Bus-Sockets und synthetische
OpenSSL-Konfiguration. Alle pytest-Läufe erfolgten ausschließlich über
`tests/run_isolated_suite.py`, mit aktivem unverändertem Guard und
Abbruch beim ersten Fehler. Keine PHP-Installation oder neuen Host-Mounts.

| Lauf | Ergebnis | Artefaktverzeichnis unter `/tmp/user/1000/` |
| --- | --- | --- |
| Betroffener Einzeltest, beide Sitzungszustände | 2 bestanden, 0 übersprungen, 0 Fehler | `netmon-isolation-r1gp7et9` |
| Relevante Baseline-Gruppe einschließlich beider negativen Guard-Fälle | 109 bestanden, 0 übersprungen, 0 Fehler | `netmon-isolation-c8f2j3be` |
| DNS, Killswitch, Firewall und beide parametrisierten Game-Mode-Rollbacks | 201 bestanden, 0 übersprungen, 0 Fehler | `netmon-isolation-zxa44v5r` |
| Gesamtsuite, beim neuen Guard-Befund gestoppt | pytest: 2.259 passed, 314 skipped, 1 error; Exit 1 | `netmon-isolation-gfraureg` |

Jedes Verzeichnis enthält `junit.xml` und `xvfb.log`. Der Gesamtlauf endete nach
37,93 Sekunden. Die pytest-Zählung enthält den erfolgreichen Testkörper des
anschließend im Teardown fehlerhaften Tests. JUnit enthält daher 2.573
eindeutige Fälle: **2.258 vollständig bestanden, 314 übersprungen, 1 Fehler**.
Kein fehlgeschlagener fachlicher Assert; keine Behauptung einer grünen
Gesamtsuite. Nach dem neuen Guard-Befund wurden keine weiteren Tests gestartet.

Die PHP-Skips bleiben **NICHT VALIDIERT**: 63 in
`tests/test_download_statistics.py`, 185 in
`tests/test_download_statistics_auth.py`, 66 in
`tests/test_download_statistics_limits.py`. Im neuen JUnit erneut bestätigt;
Grund jeweils `PHP CLI required; optionally set NETMON_TEST_PHP` aus der
gemeinsamen Session-Fixture `php()`. Weder installiert noch zusätzlich
eingebunden; insbesondere kein neuer Nachweis für M-01/M-06/L-02.

### Neuer Blocker: Einstellungen zurücksetzen

`tests/test_netmon_settings_tab.py::test_reset_settings_to_defaults_restores_defaults`
erreicht bei `reset_settings_to_defaults()` → `_apply_settings_runtime_state()`
→ `refresh_runtime_language_state()` mehrere nicht isolierte Statuspfade:

- DNS-Bedienelemente: `_dns_controls_locked()` → `is_vpn_active_for_dns_ui()`
  → `DNSControlService.read_resolvectl_status(timeout=6)` →
  `run_cmd(["resolvectl", "status"])`;
- VPN-Text: `update_vpn_status_text()` → `is_vpn_active()` → dieselbe Abfrage;
- DNS-Header: `update_dns_header()` → `get_default_iface()` →
  `run_cmd(["ip", "route", "show", "default"], timeout=3)`;
- Protokollbeschriftung: `_sync_dns_protocol_profile_labels()` → `is_dot_active()`
  → `DNSControlService.read_resolvectl_status()`;
- DNS-Guard: `run_dns_guard_check_once()` → `rebuild_dns_guard_whitelist()`
  → `is_vpn_active()` → dieselbe Statusabfrage;
- asynchroner DNS-Bericht: `resolved_status_async(select_tab=False)` →
  `job()` im Hintergrundthread →
  `run_cmd(["systemctl", "is-active", "systemd-resolved"], timeout=4)`.

Sechs Hostversuche wurden im Guard-Teardown aufgezeichnet und vor dem
Prozessstart abgewiesen (vier resolvectl, einer ip, einer systemctl).
Zusätzlich meldete pytest die Guard-Ausnahme im Hintergrundthread.
Mehrere Statusmethoden fangen Ausnahmen, deshalb ist die bleibende
Guard-Aufzeichnung samt Teardown-Kontrolle wesentlich. Kein tatsächlicher
Hostbefehl wurde für diese Versuche gestartet. Ob weitere Folgepfade
auftreten, ist wegen des Abbruchs nicht geprüft. Keine neue Fixture oder
Produktionsänderung für diesen Befund in dieser Runde.

### Änderungsgrenzen und Abschluss

Diese Runde ändert ausschließlich `tests/test_netmon_lynis_output.py` und
diesen neu angehängten Berichtsabschnitt. Ruff, Black-Check, Syntaxprüfung
ohne Ausführung/pyc und `git diff --check` bestanden. Alle anderen erfassten
Dateien bleiben SHA256-gleich zum Rundenbeginn, insbesondere Produktionscode,
Hostzugriffs-Guard, Bubblewrap-Starter, About-Arbeiten, F-01/L-01/L-04-Code
und die bisherigen L-04-Autorisierungsberichte. Der bisherige Bericht bleibt
als bytegleicher Präfix erhalten. `secure-browser/` nicht inhaltlich gelesen,
verändert oder gestagt; im Test-Namespace weiterhin verdeckt. Index leer,
Branch `main`, HEAD unverändert bei
`9944ce14650877848cb48a2ed531cd84424bcec3`.

Keine echten privilegierten Operationen, sudo-Zeitstempeländerungen,
Host-DNS-/Netzwerkoperationen, Systemänderungen, Installationen, Commits,
Pushes oder Deployments. Temporäre Testartefakte liegen ausschließlich in
den privaten Isolationsverzeichnissen.

**Baseline-Privilegienprobe lokal isoliert und in beiden Zuständen geprüft;
Gesamtsuite wegen neuem Einstellungen-Statusrefresh-Blocker gestoppt.
314 PHP-Fälle weiterhin nicht validiert. L-04 bleibt TEILWEISE BEHOBEN.**
Der Same-UID-Autorisierungsblocker bleibt ausdrücklich offen.

## Einstellungs-Reset: Statusabfragen und Worker lokal isoliert

### Teständerung und erhaltene Aussagen

Diese Runde bearbeitet ausschließlich den im vorigen Lauf aufgezeichneten
Blocker in `test_reset_settings_to_defaults_restores_defaults` und seine
Testisolation. Produktionscode, Hostzugriffs-Guard und die bestehende
Bubblewrap-Umgebung bleiben unverändert.

Die neue ausdrücklich aktivierte Fixture `reset_status_environment` in
`tests/test_netmon_settings_tab.py` verwendet die vorhandenen Opt-in-Fixtures
`passive_dns_status` und `passive_dns_service` für die externe Abfrage
`["resolvectl", "status"]`. Letztere bindet ausschließlich die konkrete
Testinstanz und liefert für die zusätzliche WireGuard-Interface-Erkennung
synthetisch eine leere Menge. Das passt zum hier geprüften Zustand VPN aus.
Der Resolverstatus enthält den synthetischen System-DNS `192.0.2.53`.

Zwei zusätzliche exakte Kommandoantworten ergänzen diesen Zustand:

- `["ip", "route", "show", "default"]` →
  `default via 192.0.2.1 dev eth0 proto dhcp`;
- `["systemctl", "is-active", "systemd-resolved"]` → `active`.

Der direkte resolvectl-Aufruf des asynchronen Berichts nutzt denselben
bestehenden Statusdispatcher wie die Service-Abfragen. Alle anderen
Argumentkombinationen werden an den ursprünglichen Runner weitergegeben und
bleiben durch den Guard gesperrt. Ausschließlich die Verfügbarkeit von
`resolvectl` wird für diesen Test synthetisch bestätigt, damit der Test nicht
von der Werkzeuginstallation auf dem Host abhängt. Andere
Werkzeug-Verfügbarkeitsabfragen bleiben unverändert. Keine globale
Autouse-Fixture und keine pauschale Prozessfreigabe.

Der Status-Worker bleibt ein echter Thread mit unverändertem Produktionsziel.
Ein delegierender Proxy nur für die `threading`-Bindung im App-Modul zeichnet
die erzeugten Threads auf; das globale Threading-Modul bleibt unverändert.
Der Test wartet mit begrenztem `join(timeout=5)` auf sein Ende und prüft, dass
genau ein Worker erzeugt wurde. Auch im Fehlerfall erfolgt das Join im
Fixture-Teardown vor Rücknahme der lokalen Mocks. Ein weiterlebender Worker
wäre ein Testfehler. Der synthetische GUI-Scheduler sammelt den Callback;
nach Workerabschluss wird genau ein 50-ms-Callback geprüft und ausgeführt.
Das fehlende GUI-Textwidget wird als `None` modelliert; die echte Verarbeitung
des Queue-Ergebnisses bleibt erhalten.

Echte Wiederherstellung der Einstellungen, Laufzeitaktualisierung,
VPN-Erkennung, DNS-Policy-Auswertung, Whitelistbildung und DNS-Guard laufen
weiter. Zusätzlich geprüft: VPN aus, Whitelist ausschließlich `192.0.2.53`,
Guard `ok`, abgeschlossene Guard-Prüfung, gleiche Service-Instanz, exakte
Statusabfragen, jeweils genau eine Routing-/Dienststatusabfrage sowie keine
übrig gebliebenen GUI-Callbacks. **Alle 285 vorher vorhandenen Assert-ASTs
der Testdatei sind je Funktion/Klasse einschließlich Häufigkeit erhalten**
(SHA256-AST-Vergleich als Multimenge mit dem Rundenbeginn).

### Negative Guard-Regressionen

Vier neue Fälle aktivieren dieselbe Fixture in einem pytest-Kindprozess
innerhalb der bestehenden Bubblewrap-Isolation und versuchen jeweils:

- `["sudo", "-n", "true"]`;
- `["resolvectl", "status", "--no-pager"]`;
- `["systemctl", "is-active", "ssh"]`;
- `["ip", "route", "get", "198.51.100.1"]`.

Jeder Eltern-Test verlangt Rückgabecode 1, `Blocked host accesses:` und den
aufgezeichneten konkreten Kommandonamen. Die Kindtests versuchen gewöhnliche
Ausnahmen abzufangen; die bleibende Guard-Aufzeichnung muss den Fehler
dennoch erzwingen. Kein solcher Hostbefehl wird gestartet. Die geplanten
negativen Kindläufe sind bestandene Sicherheitsregressionen, keine neuen
unerwarteten Hostzugriffe.

### Reihenfolge, Isolation und Ergebnisse

Vor jeder Stufe wurde die unveränderte Bubblewrap-Probe ausgeführt:
nicht privilegierte UID, `NoNewPrivs`, schreibgeschütztes Repository,
privater Netzwerk-Namespace ohne Host-Routen und ohne Host-Home,
WireGuard-/NetworkManager-Konfiguration oder Dienste-/D-Bus-Sockets.
Alle pytest-Läufe liefen ausschließlich über `tests/run_isolated_suite.py`
mit aktivem Guard und Abbruch beim ersten Fehler.

| Lauf | Ergebnis | Artefaktverzeichnis unter `/tmp/user/1000/` |
| --- | --- | --- |
| Einstellungs-Reset-Einzeltest | 1 bestanden, 0 Fehler/Skips | `netmon-isolation-_sk8fjld` |
| Ganze Einstellungs-Testdatei einschließlich vier neuer Guard-Fälle | 37 bestanden, 0 Fehler/Skips | `netmon-isolation-0tqyrsvb` |
| Guard, Baseline, DNS, Killswitch, Firewall und Game-Mode-Rollbacks | 331 bestanden, 0 Fehler/Skips | `netmon-isolation-v6r5k_tn` |
| Gesamtsuite bis zum ersten Fehler | 2.610 bestanden, 314 übersprungen, 1 fehlgeschlagen, 0 Teardown-Fehler; Exit 1 | `netmon-isolation-94m2nfoz` |

Die 331 Fälle bestehen aus 21 Guard-Selbsttests, 109 Baseline-Fällen und
201 DNS-/Schutzregel-Fällen; die vorher geprüfte Auswahl bleibt erhalten.
Die Gesamtsuite endete nach 41,56 Sekunden. JUnit bestätigt 2.925 eindeutige
Fälle mit derselben Aufteilung. Jeder Lauf besitzt `junit.xml` und
`xvfb.log`. Kein neuer unerwarteter Host-Access-Guard-Blocker bis zu diesem
Abbruch. Keine weiteren Testläufe nach dem neuen fachlichen Fehler.

**314 PHP-Fälle bleiben NICHT VALIDIERT**: Statistik 63,
Authentifizierung 185, Limits 66. Im neuen JUnit erneut bestätigt; Grund
jeweils `PHP CLI required; optionally set NETMON_TEST_PHP`. Keine
PHP-Installation, zusätzlichen Interpreter-Mounts oder Hostfreigaben.

### Neuer Befund: hostabhängige Executable-Existenz im Process-Guard-Test

Der Gesamtlauf scheitert jetzt an
`tests/test_process_guard_service.py::test_evaluate_process_does_not_flag_temp_argument_as_temp_execution`
(Assertion in Zeile 107: `finding is None`). Dieser Test wurde nicht geändert.
Er übergibt einen synthetischen `crashhelper`-Prozess, dessen Executable auf
einen fest eingetragenen Pfad unter `/home/happy/Dokumente/NetMon/Secure Browser/`
zeigt. Er stellt dessen Existenz jedoch nicht synthetisch her.

Statisch nachvollziehbare Ursache: `ProcessGuardService.evaluate_process()`
prüft zusätzlich zu temporären Ausführungspfaden die Existenz absoluter
Executable-Pfade mit `os.path.exists(exe)`. Ein fehlender Pfad erzeugt
Score 2 und den Grund `Executable-Pfad ist nicht mehr vorhanden.`. In der
geprüften Isolation ist `/home/happy` absichtlich nicht vorhanden. Der
temporäre Kommandozeilenparameter wird dabei nicht als temporäre
Executable bewertet; der zusätzliche Existenzcheck verhindert trotzdem
das erwartete `None`. Dies ist kein Nachweis einer durch diese Runde
eingeführten Produktionsregression und kein neuer Autorisierungsbefund.
Es wurden keine tatsächlichen Browserdateien oder fremden Projekte gelesen.

Eine nächste gezielte Testkorrektur könnte einen existierenden synthetischen
Executable-Pfad im privaten Namespace-Home verwenden (außerhalb der als
verdächtig eingestuften Temp-/Downloadverzeichnisse), ohne ihn auszuführen.
Damit würde die beabsichtigte Vorbedingung hergestellt, statt den
Existenzcheck oder Guard abzuschalten. Zuvor sind Testabsicht und
benachbarte HOME-/Pfadannahmen zu prüfen. **In dieser Runde keine Änderung
am Process-Guard-Test, Produktionscode oder Sandbox-Mounts.** Weitere
Folgefehler bleiben wegen des Abbruchs ungeprüft.

### Schutzgrenzen und Abschluss

Diese Runde verändert ausschließlich `tests/test_netmon_settings_tab.py`
und diesen angehängten Berichtsabschnitt. Ruff, Black-Check, Syntaxprüfung
ohne Codeausführung/pyc sowie `git diff --check` bestanden. Die vorherigen
Berichtsbytes bleiben als bytegleicher Präfix erhalten. Alle anderen
erfassten Dateien bleiben SHA256-gleich zum Rundenbeginn, insbesondere
Produktionscode, Guard, Isolation/OpenSSL-Konfiguration, Baseline-/DNS-Tests,
About-Arbeiten und die bisherigen L-04-Autorisierungsberichte.
`secure-browser/` wurde weder inhaltlich gelesen noch verändert und bleibt
im Test-Namespace verdeckt. Der vollständige Index ist hashgleich zum
Rundenbeginn und leer relativ zu HEAD. Branch `main`, HEAD unverändert:
`9944ce14650877848cb48a2ed531cd84424bcec3`.

Keine echten privilegierten Operationen oder Host-Netzwerkzugriffe,
keine Systemänderungen, Installationen, Commits, Pushes oder Deployments.
Nur lokale Test-/Berichtsänderungen und private temporäre Testartefakte.
Der erwartete DNS-Guard-Negativzustand `problem` bei zusätzlichem physischem
DNS bleibt geprüft. Die zuvor dokumentierten offenen Nachweise für den
VPN-DNS-Ausfall ohne ungeschützten Fallback und den realen Paketfilter
bleiben bestehen und werden durch diesen Lauf nicht ersetzt.

**Einstellungs-Reset lokal isoliert; 37 Einstellungs- und 331 weitere
gezielte Tests grün. Gesamtsuite wegen Process-Guard-Testvorbedingung
gestoppt; 314 PHP-Fälle unvalidiert. L-04 bleibt TEILWEISE BEHOBEN.**
Der Same-UID-Autorisierungsblocker bleibt ausdrücklich offen.

## Process-Guard: synthetische Dateivorbedingungen statt Hostpfade

### Ursache und begrenzte Korrektur

Der zuvor fehlgeschlagene Test
`test_evaluate_process_does_not_flag_temp_argument_as_temp_execution` prüft,
dass ein temporärer Kommandozeilenparameter keine Ausführung aus einem
temporären Verzeichnis darstellt. Sein fester `crashhelper`-Executable-Pfad
unter `/home/happy/...` fehlte jedoch in der Isolation. Die echte zusätzliche
Existenzprüfung erzeugte deshalb einen unabhängigen Fund. Diese
Produktionsprüfung bleibt vollständig erhalten.

Die ausdrücklich verwendete Test-Fixture `existing_executable` in
`tests/test_process_guard_service.py` stellt jetzt reale, leere, nicht
ausführbare Dateien unter dem privaten Namespace-Home bereit. Vor jeder
Erstellung verlangt sie `NETMON_TEST_ISOLATED=1` und `Path.home() == /work/home`.
Damit werden bei versehentlicher Ausführung außerhalb des vorgesehenen
Starters keine Dateien im echten Benutzer-Home erzeugt. Die Dateien liegen
in testweise getrennten Unterverzeichnissen, außerhalb der produktiven
Temp-/Download-Präfixe, mit Modus 0600; ein Assert prüft fehlende Execute-Bits.
Diese Dateien werden weder gestartet noch über einen Prozessaufruf geprüft.
Keine Änderung der Präfixlisten oder des Existenzchecks, keine neuen
Host-Mounts und keine pauschalen Dateisystem-Mocks.

Neben dem ursprünglichen Test werden vier unmittelbar benachbarte
Testvorbedingungen entsprechend präzisiert:

- Der Download-Pfad-Test verwendet `Path.home() / "Downloads"` statt
  `/home/happy/Downloads` und eine existierende synthetische Python-Datei.
  Der bestehende exakte Risikowert 3 und das Level `medium` bleiben geprüft.
- Der Snapshot-Summierungstest stellt seine als unauffällig erwartete
  Systemd-Datei und die Python-Datei synthetisch bereit; Prozessanzahl,
  genau ein Fund und Risikozusammenfassung bleiben geprüft.
- Der Trustlist-Test verwendet eine synthetische Python-Datei; die echte
  Fundbewertung und das Ausfiltern des vertrauten Funds bleiben aktiv.
- Der Test für den bloßen Namen `NetworkManager` verwendet eine existierende
  synthetische Datei gleichen Namens statt einer installierten Hostdatei.
  Die bisherige Assertion `finding is None` bleibt bestehen.

Dies sind vier weitere Tests neben dem ursprünglichen Test, also fünf
angepasste Tests insgesamt. Nicht vom Dateisystem ausgewertete Pfadstrings
im synthetischen `ps`-Fallback-Snapshot bleiben unverändert. Ebenso bleiben
bewusst riskante Temp-/Run-Pfade und die Kernel-Thread-Fälle erhalten.

Ein neuer Negativtest
`test_evaluate_process_reports_missing_executable_with_temp_argument` verwendet
denselben harmlosen Prozessnamen und einen temporären Parameter, aber einen
nachweislich fehlenden Pfad neben der synthetischen Datei. Assertions:
Fund vorhanden, Score exakt 2, Level `low`, einziger Grund
`Executable-Pfad ist nicht mehr vorhanden.`. Damit ist die Existenzprüfung
nicht durch die Herstellung des positiven Testfalls verdeckt.

Alle **42 zuvor vorhandenen Assert-ASTs** der Testdatei sind je Funktion/Klasse
einschließlich Häufigkeit unverändert erhalten (SHA256-AST-Vergleich als
Multimenge gegen den Rundenbeginn). Kein Produktionscode, Host-Access-Guard,
Bubblewrap-Starter oder anderer Test wurde in dieser Runde geändert.

### Validierung in der vorgegebenen Reihenfolge

Vor jeder Stufe bestand die unveränderte Bubblewrap-Probe: nicht privilegierte
UID, `NoNewPrivs`, schreibgeschütztes Repository, eigener Netzwerk-Namespace
ohne Host-Routen, keine Host-Home-/VPN-Konfiguration und keine
Host-Dienste-/D-Bus-Sockets. Alle pytest-Läufe erfolgten ausschließlich über
`tests/run_isolated_suite.py` mit aktivem Guard und Abbruch beim ersten Fehler.

| Lauf | Ergebnis | Artefaktverzeichnis unter `/tmp/user/1000/` |
| --- | --- | --- |
| Ursprünglich betroffener Einzeltest | 1 bestanden, 0 Fehler/Skips | `netmon-isolation-t_mfyy90` |
| Ganze Process-Guard-Service-Testdatei | 16 bestanden, 0 Fehler/Skips | `netmon-isolation-c7ewxk8z` |
| Bisherige gezielte Regressionen | 368 bestanden, 0 Fehler/Skips | `netmon-isolation-_h4xa9ql` |
| Gesamtsuite bis zum nächsten Fehler | 3.000 bestanden, 314 übersprungen, 1 fehlgeschlagen, 0 Teardown-Fehler; Exit 1 | `netmon-isolation-dblqnfro` |

Die 368 Fälle umfassen unverändert 37 Einstellungs-, 21 Guard-, 109 Baseline-
und 201 DNS-/Schutzregel-Fälle. Der neue Negativtest ist in den 16
Process-Guard-Fällen enthalten. Der Gesamtlauf endete nach 43,01 Sekunden;
JUnit bestätigt 3.315 eindeutige Fälle mit derselben Aufteilung. Jeder Lauf
besitzt `junit.xml` und `xvfb.log`. Kein grüner Gesamtlauf und keine weiteren
Tests nach dem neuen Befund.

Die **314 PHP-Skips bleiben NICHT VALIDIERT**: Statistik 63,
Authentifizierung 185, Limits 66. Diese Aufteilung ist im neuen JUnit erneut
bestätigt. Grund jeweils `PHP CLI required; optionally set NETMON_TEST_PHP`.
Keine PHP-Installation, zusätzlichen Interpreter-Mounts oder neuen
Hostfreigaben. Die früher dokumentierten Grenzen des DNS-Ausfall- und
Paketfilter-Nachweises bleiben unverändert; der zusätzliche physische DNS
führt im vorhandenen VPN-Negativtest weiterhin zu `problem`.

### Neuer Isolationsbefund: Flatpak-Abfrage im APT-Parser-Test

Der nächste Fehler ist
`tests/test_repository_guard_service.py::test_collect_sources_parses_valid_and_disabled_entries`
(Zeile 20: `errors == []`). Dieser Test übergibt zwar ausschließlich seine
synthetische `sources.list`, isoliert aber die automatisch ebenfalls
ausgeführte Flatpak-Inventarisierung nicht. Tatsächlicher Aufrufpfad:

```text
test_collect_sources_parses_valid_and_disabled_entries()
  -> RepositoryGuardService(source_patterns=[synthetische Datei])
  -> collect_sources()
  -> _collect_flatpak_sources()
  -> flatpak_available_fn(): shutil.which("flatpak")
  -> flatpak_runner(scope): _run_flatpak_command(scope)
  -> subprocess.run(["flatpak", "remotes", "--system", "--show-disabled",
                     "--columns=name,url,options"], check=True, ...)
```

Der System-Aufruf scheitert mit Exit 1 und erzeugt
`repo_flatpak_query_failed`; deshalb schlägt die bestehende Assertion fehl.
Die produktive Schleife fragt zusätzlich den Scope `user` mit demselben
Kommando und `--user` ab. Die statische Nachprüfung zeigt eine
**Klassifikationslücke des bestehenden Host-Access-Guards: `flatpak` steht
nicht in `_HOST_COMMANDS`**. Deshalb wurde diese externe Abfrage nicht vor
ihrem Prozessstart durch den Guard abgewiesen. Keine pauschale Behauptung,
dass alle externen Systemabfragen inzwischen vom Guard erkannt werden.

Diese Flatpak-Prozesse liefen ausschließlich im bereits geprüften
Bubblewrap-Namespace: privates Home, fehlende Host-Flatpak-Konfiguration
unter `/etc` und `/var`, keine Host-Dienste-Sockets und kein Host-Netzwerk.
Es wurden keine Flatpak-Installations-, Änderungs- oder privilegierten
Operationen aufgerufen. Die bestehende Namespace-Isolation wurde dafür
weder erweitert noch gelockert. Nach dem Befund keine weitere Ausführung,
nur lesende Ursachenanalyse.

Die Service-Schnittstelle bietet bereits `flatpak_available_fn` und
`flatpak_runner`. Ein nächster enger Testschritt kann für reine APT-Tests
explizit einen verfügbaren, aber leeren synthetischen Flatpak-Bestand für
beide Scopes injizieren. Ein bloßes `available=False` wäre bei manchen
Scan-Assertions ungeeignet, weil es zusätzlich die Meldung für fehlendes
Flatpak erzeugt. Echte Flatpak-Testfälle müssen ihre eigenen positiven,
negativen und Fehlerantworten behalten. Dieser Vorschlag und die separate
Guard-Klassifikationslücke sind **nicht implementiert**. Repository-Guard-
Produktionscode und -Tests sowie der Host-Access-Guard bleiben unverändert.

### Änderungsumfang und Abschluss

Diese Runde ändert ausschließlich `tests/test_process_guard_service.py`
und diesen angehängten Berichtsabschnitt. Ruff, Black-Check, Syntaxprüfung
ohne Codeausführung/pyc und `git diff --check` bestanden. Alle anderen
erfassten Dateien sind SHA256-gleich zum Rundenbeginn, insbesondere
Produktionscode, Guard, Teststarter, alle bisherigen Testkorrekturen,
About-Arbeiten und Autorisierungsdokumente. Der bisherige Bericht bleibt
als bytegleicher Präfix erhalten. `secure-browser/` wurde weder inhaltlich
gelesen noch verändert und blieb im Namespace verdeckt.

Der vollständige Index ist hashgleich zum Rundenbeginn und leer relativ zu
HEAD. Branch `main`, HEAD unverändert:
`9944ce14650877848cb48a2ed531cd84424bcec3`. Keine echten privilegierten
Operationen, Host-Netzwerkzugriffe, Systemänderungen, Installationen,
Commits, Pushes oder Deployments. Ausschließlich lokale Test-/Berichtsarbeit
und private temporäre Testartefakte.

**Process-Guard-Testvorbedingungen lokal isoliert; 16 Process-Guard- und
368 bisherige gezielte Tests grün. Gesamtsuite wegen Flatpak-Testisolation
gestoppt; 314 PHP-Fälle unvalidiert. L-04 bleibt TEILWEISE BEHOBEN.**
Der Same-UID-Autorisierungsblocker bleibt ausdrücklich offen.
