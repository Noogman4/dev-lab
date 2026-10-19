# Manuelle WireGuard-Endpoints: Konfigurationsinjektion

Pruefung und lokale Korrektur vom 19.10.2026.

- Repository: `Noogman4/dev-lab`
- Gepruefte Basis: `edf4f32f3fa0c59cc4d5414f3de3f28fefef803e`
- Cloud-Revision des Befunds: `71ed081b77e26af8853d340e777009f027251082`
- Finding: `csf_9ad9249fdb81d96fb00affe4`
- Titel: Manual WireGuard endpoint accepts line breaks that can inject root-executed hooks
- Cloud-Schweregrad: Medium

## Verifikation

Der tatsaechliche Parser und Renderer der Basisrevision wurden isoliert
ausgefuehrt. Ein synthetischer mehrzeiliger Endpoint wurde akzeptiert und
erzeugte eine zweite Interface-Sektion samt PreUp-Direktive. Es wurden weder
wg-quick noch Hooks oder privilegierte Systemoperationen ausgefuehrt. Die
Clipboard-Verarbeitung durch Tk und die Root-Ausfuehrung sind damit nicht
dynamisch nachgewiesen.

## Korrektur

`netmon/core/manual_wireguard.py` begrenzt Endpoints auf gueltige IPv4-Adressen,
geklammerte IPv6-Adressen oder ASCII-DNS-Namen (einschliesslich Punycode) und
ASCII-Ports von 1 bis 65535. Leer-/Steuerzeichen, Konfigurationsbegrenzer,
Zone-IDs und ungueltige Hostnamen werden verworfen. Die Eingabe wird vor der
Pruefung nicht mehr mit strip veraendert. Es erfolgen keine DNS-Anfragen.

Der manuelle Renderer akzeptiert nur einzeilige Werte. Die fertige Konfiguration
wird auf genau eine Interface- und eine Peer-Sektion in dieser Reihenfolge,
zulaessige und eindeutige Felder, erforderliche Felder sowie gueltige Schluessel,
IP-Netze, DNS-Adressen, Endpoint und Keepalive geprueft. Der bestehende
Hook-Detektor wird wiederverwendet; Hooks sind in manuellen Profilen verboten.
Die Pruefung erfolgt vor der Sudo-Anfrage und erneut direkt vor dem bestehenden
unveraenderlichen Byte-Handoff im manuellen Schreibpfad.

Die gemeinsame Routine fuer IPv4-Kopien importierter Profile wurde nicht
geaendert. Der separate Import-/Bestaetigungsablauf bleibt erhalten.

## Tests und Grenzen

```sh
python -m pytest -q tests/test_manual_wireguard_security.py tests/test_wireguard_import_security.py tests/test_netmon_vpn_slots.py tests/test_vpn_slots_tab.py tests/test_netmon_nm_ownership.py
```

Ergebnis: **431 bestanden, 1 uebersprungen** (Tk-Smoke-Test ohne DISPLAY).
Der aktive Hostzugriffs-Guard meldete keinen unerwarteten Systemzugriff.

Die neuen Regressionen pruefen unter anderem CR/LF/NUL, ASCII-/C1-Steuerzeichen,
Unicode-Trenner, falsche IPv6-Klammerung, ungueltige Ports/DNS-Namen,
Injektion in alle acht ausgegebenen Felder, direkte Schreibpfad-Umgehung,
zusaetzliche Sektionen, Hooks und Doppelbelegungen. Gueltige DNS-/IPv4-/IPv6-Werte
durchlaufen Formular, Renderer und simulierte Installation. Der bestehende
Snapshot-/Root-Helper-Test verwendet einen isolierten Fake.

Black, Python-Kompilierung und git diff --check erfolgreich. Ruff meldet fuer
die beiden neuen Python-Dateien keine Fehler; in den drei bestehenden
geaenderten Python-Dateien gibt es keine neuen Diagnosen gegenueber der Basis
(79/2/2 vorhandene Diagnosen, zuvor 81/2/2).

Status: **lokal implementiert und getestet**. Kein Commit, Push oder Deployment;
der Cloud-Befund wurde nicht geschlossen. Eine erneute Pruefung nach Anwendung
des Patches auf den veroeffentlichten Commit steht aus.

## Lokale Anwendung und Bubblewrap-Nachpruefung

Der Patch wurde am 19.10.2026 auf der oben genannten Basis lokal angewendet.
Die vorstehenden 431 bestandenen Tests, der Tk-Skip und die Ruff-Altmeldungen
stammen aus dem mitgelieferten Bericht. Die dort beschriebene historische
Vorher-Reproduktion wurde hier nicht erneut ausgefuehrt. Der lokale Nachweis
prueft den angewendeten Parser, das tatsaechliche Formular, den Renderer und
die simulierte Installationsgrenze; keine Hooks oder echten Schluessel wurden
ausgefuehrt beziehungsweise verwendet.

Vor den Tests bestand die unveraenderte Bubblewrap-Probe: unprivilegierte UID,
NoNewPrivs, schreibgeschuetztes Repository, private PID-/Netzwerk-Namespaces
ohne Host-Routen sowie keine Host-Home-, WireGuard-/NetworkManager-Konfiguration
oder Dienstesockets. Alle pytest-Laeufe verwendeten den bestehenden Starter
und unveraenderten Host-Access-Guard. Es gab keine unerwarteten Guard-Zugriffe,
echten sudo-/VPN-/DNS-Operationen, externen Downloads oder Systemaenderungen.

| Auswahl | Ergebnis | Lokales Artefakt unter `/tmp/user/1000/` |
| --- | --- | --- |
| Neue manuelle WireGuard-Sicherheitstests | 160 bestanden, 0 Fehler/Skips | `netmon-isolation-9xql7k5e/junit.xml` |
| Neue Tests plus Import-, Slot-, GUI-, Eigentums- und Guard-Regressionen | 453 bestanden, 0 Fehler/Skips, 4,40 Sekunden | `netmon-isolation-39wccjxz/junit.xml` |

Die abschliessenden 453 Faelle bestehen aus 160 manuellen Sicherheits-,
73 WireGuard-Import-, 72 VPN-Slot-, 4 Slot-Tab-, 123 Eigentums-/Session- und
21 Guard-Tests. Die ersten 160 sind darin enthalten, keine zusaetzlichen
eindeutigen Faelle. Die fuenf Dateien aus dem gelieferten Testbefehl stellen
432 Faelle; mit Xvfb bestand hier auch der zuvor uebersprungene Tk-Smoke-Test.
Die weiteren 21 Faelle sind die ausdruecklich hinzugezogenen Guard-Selbsttests.
Keine unveroeffentlichten About-Tests sind Teil dieser Auswahl.

Reproduktion ausschliesslich im vorhandenen isolierten Starter:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests/test_manual_wireguard_security.py \
  tests/test_wireguard_import_security.py tests/test_netmon_vpn_slots.py \
  tests/test_vpn_slots_tab.py tests/test_netmon_nm_ownership.py \
  tests/test_host_access_guard.py
```

Ruff mit der lokalen Projektkonfiguration meldet fuer alle fuenf betroffenen
Python-Dateien keine Fehler; auch die drei vorigen Dateistaende meldeten hier
keine Ruff-Befunde. Die im Fremdbericht genannten Altmeldungen sind daher keine
lokalen Ergebnisse. Black, Python-Syntaxpruefungen ohne Ausfuehrung/pyc-Dateien
und `git diff --check` bestanden. Keine Lint-Ausnahmen oder Abhaengigkeiten
wurden ergaenzt; kein Shellskript wurde geaendert.

Der lokale Umfang bleibt bei sechs Patch-Dateien. Nur dieser Bericht wurde
gegenueber dem gelieferten Patch ergaenzt. Ein AST-Vergleich bestaetigt, dass
im VPN-Controller ausser den fuenf manuellen Formular-/Parser-/Schreibfunktionen
keine Funktionen oder Klassen geaendert wurden. Die bestehenden Tests wurden
nur an den beiden vorgesehenen synthetischen Profil-Fixtures angepasst.
Eigentumspruefung, Byte-Snapshots, Session-/Rollback-Implementierung,
Kill-Switch-Fix, About-Arbeiten, Guard und Teststarter bleiben unveraendert.

Die strengere manuelle Grammatik verwirft auch fuehrende/nachgestellte
Endpoint-Leerzeichen, Unicode-DNS-Namen ohne Punycode sowie IPv6-Zone-IDs.
Der separate Import-/Bestaetigungsablauf wird dadurch nicht ersetzt. Der
offene L-04-Same-UID-Autorisierungsblocker bleibt bestehen; diese Korrektur
stellt keinen unabhaengigen Autorisierungsbroker bereit.

Keine Gesamtsuite, produktive Profilinstallation, echte NetworkManager-
Operation oder Cloud-Pruefung ausgefuehrt. Index und HEAD bleiben unveraendert.
`secure-browser/` wurde weder gelesen noch veraendert und blieb im
Test-Namespace verdeckt. Kein Commit, Push oder Deployment.
