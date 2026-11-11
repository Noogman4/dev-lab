# NetMon V4 – kontrollierte Installation, 31.10.2026

## Ergebnis

**Erfolgreich installiert:** `netmon`, Version
`1.1.21~v4dnstest20261031.1`, Architektur `all`.
Nur NetMon wurde hinzugefügt. Keine anderen Pakete installiert, aktualisiert
oder entfernt; kein Autoremove. DNS-/Resolverzustand, Firewallregeln,
UFW-Startkonfiguration und erfasste Einstellungen sind unverändert.

**Kein NetMon-GUI-Start, keine privilegierten NetMon-Funktionstests,
keine Geräte-/DNS-/Firewall-/VPN-Aktionen, keine fstab-Änderung,
kein Paketneubau, keine KS48-Prüfrunde, keine Commits oder Pushes.**

## Paketbindung und Ausgangszustand

| Merkmal | Bestätigter Wert |
| --- | --- |
| Ursprüngliches lokales DEB | `/dev-lab/projects/netmon-v4-dns-integration-test/dist/netmon_1.1.21~v4dnstest20261031.1_all.deb` |
| Version | `1.1.21~v4dnstest20261031.1` |
| Architektur | `all` |
| SHA-256 | `c4d9487f53fa7f34eb7f48e7e154161b9983865b2d38cc0fe7e152751f010d92` |

Vorher war NetMon nicht installiert; `dpkg-query` fand keinen passenden
Paketdatensatz. Keine NetMon-Prozesse, `dpkg --audit` ohne Befund.
Paketmetadaten und die bereits geprüften Maintainer-Skripte wurden erneut gegen
das konkrete DEB bestätigt. Alle 167 Ziel-Dateipfade waren konfliktfrei.

Für APT wurde eine SHA-identische Kopie unter einem root-eigenen temporären
Verzeichnis `/var/tmp/netmon-apt-verified-…/` bereitgestellt. Verzeichnis und
Datei waren nicht durch Gruppe/Fremde beschreibbar; APT konnte die Datei über
seinen normalen `_apt`-Benutzer lesen. Vor dem tatsächlichen Aufruf wurden sowohl
Original als auch Kopie erneut gegen den vorgegebenen Hash geprüft. Die Kopie
wurde nach erfolgreicher Nachkontrolle gezielt entfernt; das ursprüngliche DEB
bleibt erhalten.

Die administrative Anmeldung erfolgte ausschließlich über die normale
interaktive sudo-Abfrage im lokalen Terminal. Keine Passwortübergabe über
Chat, Datei, Skript oder `sudo -S`.

## Vergleichsbasis und Simulation

Vorprüfung und unmittelbare Installationsvorbereitung erfassten:

- `ufw status verbose/numbered`, `ufw show added/raw`;
  IPv4-/IPv6-Regeln mit `iptables-save`, `ip6tables-save`, nft-JSON und den
  vorhandenen Legacy-Save-Werkzeugen.
- DNS-Server, Domains und DefaultRoute über resolvectl; aktive NM-Verbindungen
  und NM-Geräte-/DNS-Felder; Resolver-Gesamtstatus als Rohaufnahme.
- Hashes, Eigentümer, Rechte und Symlinkziele relevanter fstab-/UFW-/resolved-/
  NetworkManager-/Netplan-Konfigurationen und Resolver-Laufzeitdateien.
  Geschützte Profile wurden gehasht, nicht als Klartext ausgegeben.
- Benutzer-/NetMon-Einstellungen und Zustand; `/etc/skel` sowie bekannte
  Desktop-/Iconcache-Dateien gesondert.
- Paketstatusliste und UFW-Autostart einschließlich tatsächlicher Unit,
  Overrides, Enablement-Link und `/etc/ufw/ufw.conf`.

APT wurde nach der Vorprüfung und unmittelbar vor der Installation erneut
simuliert. Beide Pläne enthielten ausschließlich:

```text
0 upgraded, 1 newly installed, 0 to remove
Inst netmon (1.1.21~v4dnstest20261031.1 local-deb [all])
Conf netmon (1.1.21~v4dnstest20261031.1 local-deb [all])
```

Keine zusätzlichen Recommends/Suggests, keine weiteren Abhängigkeiten, keine
Paketentfernungen oder Konflikte. Die von APT aufgelisteten unbenötigten Pakete
waren reine Hinweise und wurden nicht entfernt. Vor Installation waren auch
Vergleichsbasis, Einstellungen, Skel und APT-Konfiguration weiterhin unverändert.

## Tatsächliche Installation

APT wurde mit genau der verifizierten lokalen Kopie aufgerufen:

```sh
NEEDRESTART_SUSPEND=1 apt-get --no-remove --no-auto-remove \
  --no-install-recommends -o APT::Install-Suggests=false \
  -o APT::Get::Purge=false -y install /var/tmp/netmon-apt-verified-…/netmon_1.1.21~v4dnstest20261031.1_all.deb
```

Der vollständige tatsächliche Pfad und Aufruf stehen in
`installation-command.json` und `installation/apt-install.log`.
APT endete mit Code 0. Das Log bestätigt ausdrücklich:
`packages have been installed but needrestart is suspended`.
Die Unterdrückung galt nur für das Prozess-Environment dieses Ablaufs;
keine dauerhafte Hook-Konfiguration wurde verändert.

Der Vorher-/Nachhervergleich sämtlicher Paketstatuszeilen ergibt genau einen
neuen Eintrag: `netmon`, `all`, `installed`, erwartete Version. Keine Entfernung,
kein Versions-/Statuswechsel eines anderen Pakets.

## UFW: laufende Regeln und Autostart getrennt bewertet

**Laufender Schutz:** Vorher und nachher `ufw status` aktiv:

```text
Status: active
Logging: on (high)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip
```

32 UFW-Ketten für IPv4 und 31 für IPv6 bleiben vorhanden. Tabellen, Ketten,
Regeln, Policies und nft-Handles stimmen überein. Nur variable Paket-/Bytezähler
und iptables-Generatorzeitstempel wurden für den Vergleich ausgeblendet;
Rohaufnahmen mit Zählern sind erhalten. Auch die persistenten UFW-Dateien sind
hashgleich. Keine Regel wurde zurückgesetzt oder neu geladen.

**Startkonfiguration, ausschließlich gelesen:**

| Prüfung | Vorher und nachher |
| --- | --- |
| `systemctl is-enabled ufw.service` | `enabled` |
| Tatsächliche Unit | `/usr/lib/systemd/system/ufw.service` |
| Overrides / `DropInPaths` | Keine |
| Enablement-Link | `/etc/systemd/system/multi-user.target.wants/ufw.service` → tatsächliche Unit |
| Install-Ziel | `WantedBy=multi-user.target` |
| Diensttyp | `Type=oneshot`, `RemainAfterExit=yes` |
| Startbefehl | `/usr/lib/ufw/ufw-init start quiet` |
| `/etc/ufw/ufw.conf` | Genau ein `ENABLED=yes` |
| Aktueller Unitstatus | `inactive (dead)` |

Damit ist der übliche Autostart konfiguriert. **Separat offen bleibt der Grund
des aktuellen inaktiven Unitstatus**; systemd meldet außerdem
`ConditionResult=no`. Diese Beobachtung ist gegenüber der Ausgangslage
unverändert und wurde nicht durch Starten/Stoppen/Enablement-Änderung bearbeitet.
Ein tatsächlicher erfolgreicher Start beim nächsten Boot wurde nicht getestet.
Aktive Kernelregeln und konfigurierte Startabsicht sind keine Bestätigung einer
gegenwärtig aktiven systemd-Unit oder eines praktisch geprüften Bootablaufs.

## Nachkontrolle und bekannte Nebenwirkungen

| Prüfung | Ergebnis |
| --- | --- |
| Installierter Status | `install ok installed`, erwartete Version |
| `dpkg --audit` | Leer / ohne Befund; zusätzlich unabhängig nachgeprüft |
| Tatsächlich installierte Dateien | Alle **167** SHA-256-, Typ-, Rechte-, UID-/GID-Werte stimmen mit dem konkreten DEB überein |
| Launcher und Desktopdatei | Vorhanden und paketgleich, einschließlich `/usr/bin/netmon` und `netmon.desktop` |
| Installierte Maintainer-Skripte | Paketgleich; kein neues preinst/postrm/Trigger-Skript im geprüften DEB |
| Benutzer-/NetMon-Einstellungen | **11 Dateien / 23 erfasste Einträge** einschließlich Abwesenheitsnachweisen unverändert |
| Geschützte Konfigurations-/Resolverbereiche | **393 erfasste Einträge** unverändert, einschließlich `/etc/fstab` |
| DNS-/Resolver-/NM-Werte | Serverlisten, Domains, DefaultRoute und abgefragte aktive Verbindungen/Gerätefelder unverändert |
| UFW-/Firewall-/Autostartdaten | Unverändert wie oben beschrieben |
| NetMon-Prozesse | Keine; NetMon wurde nicht gestartet |

Globale DNS bleiben `1.1.1.1`, `9.9.9.9`; Link `enp42s0` bleibt bei
`192.168.0.1`, Link `enp4s0` ohne angezeigte DNS. Dies ist ausschließlich der
Zustandsvergleich, keine neue Bewertung oder Korrektur der DNS-Routen.

**Erwartete Installationsnebenwirkungen:** Paketmanager-Metadaten und
NetMon-Paketdateien wurden angelegt; die regulären Trigger für
`hicolor-icon-theme`, `gnome-menus`, `man-db` und `desktop-file-utils` liefen.
Der Hicolor-Iconcache änderte sich erwartungsgemäß. Die erfasste
`mimeinfo.cache` blieb inhaltlich gleich, auch wenn die Desktop-Datenbank
aktualisiert wurde.

Das bekannte nicht überschreibende Bildseeding des `postinst` lief. Der
NetMon-Bereich unter `/etc/skel` enthielt bereits die benötigten Vorlagen:
Alle **23 dort erfassten Dateien** bleiben unverändert; keine zusätzlichen
Skel-Einträge wurden angelegt. Keine vorhandene Bilddatei wurde überschrieben.
Diese Skel-Prüfung ist ausdrücklich von den Benutzereinstellungen getrennt.

## Bestanden, fehlgeschlagen, nicht ausgeführt

**Bestanden:** Paket-/Hash-/Skriptprüfung, konfliktfreie Zielpfade,
administrative Baseline, reine Autostartaufnahme, beide APT-Simulationen,
Installation, Versions-/Audit-/167-Dateien-Nachkontrolle und alle beschriebenen
Erhaltungsvergleiche. Keine Abweichung von der unmittelbar vorherigen Baseline.

**Fehlgeschlagen:** Keine abschließende Installations- oder Nachprüfung.
Der inaktive Unitstatus ist ein unveränderter gesonderter Befund,
kein fehlgeschlagener Installationsschritt.

**Nicht ausgeführt:** NetMon-GUI-/Anwendungstest, privilegierte NetMon-Funktionen,
echte Mount-/Unmount-/Unlock-Aktionen, DNS-/Firewall-/VPN-Konfigurationsänderungen,
UFW-/DNS-/VPN-Dienststart/-stopp/-enablement, Neustart/Bootprüfung, Paketneubau, neue
Regressions-/KS48-/Archivprüfrunde, Commits oder Pushes.

Nachweise: `integration-evidence/apt-install-20261031/` mit Paketbindung,
Simulations-/Installationslogs, installierten Dateihashes, Vorher-/Nachherdaten,
tatsächlicher Unit samt Enablement-Daten, Einstellungs-/Konfigurationsmanifesten
und begrenztem administrativem Ablauf als nicht ausführbarem Nachweistext.
Die Nachweise liegen in einem privaten Verzeichnis. Kein Passwort wurde
aufgezeichnet; die Installation darf aus dem Nachweisablauf nicht blind
wiederholt werden.

**Installation und Nachkontrolle abgeschlossen. Hier gestoppt; NetMon noch nicht gestartet.**
