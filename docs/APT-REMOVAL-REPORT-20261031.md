# NetMon V4 – kontrollierte APT-Entfernung, 31.10.2026

**Ergebnis:** Ausschließlich `netmon` Version
`1.1.21~v4dnstest20261030.2` wurde erfolgreich regulär über APT entfernt.
Kein Purge, kein Autoremove, kein Aufruf von `netmon-uninstall`.
Das neue DEB wurde nicht installiert. Einstellungen, DNS-/Resolverzustand und
Firewallregeln sind in der Nachkontrolle unverändert.

## Vorprüfung und tatsächlich ausgeführte Aktion

Die installierte Version war `install ok installed`,
`1.1.21~v4dnstest20261030.2`. Die installierten Maintainer-Skripte wurden im echten
Hostkontext geprüft: reguläre root-eigene Dateien ohne Gruppen-/Fremdschreibrecht,
bytegleich zu den bereits geprüften Paket-Skripten.

| Installierter Bestandteil | Befund |
| --- | --- |
| `prerm` | Wirkungsloses `exit 0`; keine DNS-/Firewall-/VPN-Aktion |
| `postinst` | Desktopcache und nicht überschreibendes `/etc/skel`-Bildseeding; keine DNS-Rücksetzung; bei Entfernung nicht aufgerufen |
| `preinst`, `postrm`, eigene Triggerdatei | Nicht vorhanden |

SHA-256: `prerm`
`2296cf23b750aaeb2e7647395c91753013289479385008c8d314df7add60f730`,
`postinst`
`200a6195ebd1f087a1657c608a1c3b73b0f9a42ed553eeaf5659d902645c6007`.
Keine laufenden NetMon-Prozesse; `dpkg --audit` ohne Befund.

Administrative Prüfungen und Entfernung erfolgten nach normaler interaktiver
sudo-Anmeldung im lokalen Terminal. Keine Passwortübergabe über Chat, Datei,
Skript oder `sudo -S`. Die erste Terminalverbindung endete nach der erfolgreichen
Vorprüfung, bevor eine Entfernung gestartet war. Die anschließende lokale
Anmeldung führte erst nach erneuter Versions-/Skript-/Simulationsprüfung die
beauftragte Entfernung aus.

```sh
NEEDRESTART_SUSPEND=1 apt-get --no-auto-remove --no-install-recommends \
  -o APT::Install-Suggests=false -o APT::Get::Purge=false \
  -y remove -- netmon
```

Der vorhandene `needrestart`-APT-Hook wurde ausschließlich über dieses
Prozess-Environment unterdrückt, damit keine zusätzlichen Dienstneustarts
ausgelöst werden. Keine dauerhafte Hook-/Systemkonfiguration wurde geändert.
Die übrigen geprüften APT-Hooks und regulären Desktop-/Paketmanageraktionen
blieben unverändert. Der konfigurierte rkhunter-Hook war nicht aktiv:
`APT_AUTOGEN="false"`, das aufgerufene rkhunter-Programm war nicht vorhanden.

## Simulationen

| Zeitpunkt / Simulation | Geplanter Effekt |
| --- | --- |
| Vorher: reguläres Remove | Genau `Remv netmon`; keine Installation/Änderung anderer Pakete |
| Vorher: anschließende Installation in privater Zustandskopie ohne NetMon | Genau `Inst netmon` und `Conf netmon`, Version `1.1.21~v4dnstest20261031.1` |
| Unmittelbar vor Entfernung | Beide Simulationen erneut gleich; APT-Konfiguration gegenüber geprüfter Vorprüfung unverändert |
| Nach Entfernung: Installation im tatsächlichen neuen Hostzustand, weiterhin nur `--simulate` | Nur das neue NetMon-Paket, keine zusätzliche Abhängigkeit und keine Entfernung |

Die private Simulation entfernte den NetMon-Absatz ausschließlich aus einer
Kopie der dpkg-Statusdatei unter dem privaten Prüfpfad. Die echte Paketdatenbank
wurde dafür nicht verändert. Die Aufrufe zur Installation enthielten immer
`--simulate --no-remove` und deaktivierte Recommends/Suggests.

APT zeigte zahlreiche automatisch installierte, inzwischen unbenötigte Pakete
als Hinweis an. **Keines dieser Pakete wurde entfernt.** Es gab keine
unerwartete Paketentfernung und keinen Abhängigkeitskonflikt.

## Nachkontrolle

Der Vorher-/Nachhervergleich der vollständigen Paketstatuslisten ergibt:
**einzig `netmon` entfernt, kein Paket hinzugefügt, keine andere Paketversion
oder anderer Paketstatus verändert.** APT endete mit Code 0.

- `dpkg-query` meldet `no packages found matching netmon` (erwarteter Code 1).
  Das Paket hat keine deklarierte Conffile-Liste; dieser Zustand kann auch bei
  regulärem Remove ohne Purge entstehen.
- Keine verbliebenen NetMon-Prozesse. `/usr/bin/netmon`,
  `/usr/bin/netmon-uninstall`, die installierte `app.py` und der systemweite
  NetMon-Desktopstarter sind nicht mehr vorhanden.
- Die Nachprüfung mit `dpkg --audit` bleibt ohne Befund.
- 34 Dateien in den erfassten Einstellungs-/Zustandsbereichen bleiben hashgleich
  (49 erfasste Einträge einschließlich Verzeichnissen/Abwesenheitsnachweisen).
  Dazu gehören `Documents/NetMon/Config`, gegebenenfalls `Dokumente/NetMon/Config`,
  `~/.config/netmon`, `~/.local/state/netmon`, `/etc/netmon`, `/var/lib/netmon`
  und NetMon-Seeding unter `/etc/skel`. Es wurde nichts bereinigt.

Normale Paketmanager-Nebenwirkungen sind dokumentiert: dpkg-/APT-Metadaten
aktualisiert, NetMon-Paketdateien entfernt, Trigger für `hicolor-icon-theme`,
`gnome-menus`, `man-db` und `desktop-file-utils` verarbeitet. Keine DNS-,
Firewall- oder VPN-Reparatur wurde ausgeführt.

## UFW und Firewall: aktiv und Regeln erhalten

Vorher und nachher identisch:

```text
Status: active
Logging: on (high)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip
```

Die laufenden Regelsätze wurden mit `iptables-save`, `ip6tables-save`,
`nft --json list ruleset` und beiden vorhandenen Legacy-Save-Werkzeugen erfasst
und verglichen. 32 UFW-Ketten für IPv4 und 31 für IPv6 sind weiter vorhanden.
`ufw status numbered` und `ufw show added` sind ebenfalls identisch; zusätzliche
UFW-Benutzerregeln wurden bereits vor der Entfernung nicht angezeigt.

Für den Vergleich wurden ausschließlich variable Paket-/Bytezähler sowie
Generator-Kommentarzeitstempel der iptables-Ausgabe ausgeblendet. Die eigentlichen
Tabellen, Ketten, Regeln, Policies und nft-Handles bleiben gleich. Rohaufnahmen
mit Zählern sind zusätzlich archiviert. Persistente UFW-Konfigurationen bleiben
ebenfalls hashgleich.

Zur Einordnung: `ufw.service` wurde sowohl vorher als auch nachher von systemd
als `inactive` gemeldet. Dieser Zustand wurde nicht geändert. Die Bestätigung
„UFW aktiv“ bezieht sich auf `ufw status` und die unverändert vorhandenen
Kernelregeln, nicht auf eine behauptete aktive systemd-Unit.

## DNS, Resolver und NetworkManager unverändert

Serverlisten, Domains, DefaultRoute-Angaben, aktive NM-Verbindungen und die
abgefragten NM-Geräte-/DNS-Felder sind vorher/nachher identisch. Globale DNS:
`1.1.1.1`, `9.9.9.9`; `enp42s0`: `192.168.0.1`; `enp4s0`: keine angezeigten DNS.
Dies ist eine Bestandsaufnahme, keine neue Sicherheitsbewertung der DNS-Routen.

393 erfasste Konfigurations-/Dateisystemeinträge einschließlich UFW, fstab,
`resolv.conf` und Resolver-Laufzeitdateien, resolved-Konfiguration, NM-Konfiguration
und geschützten Profilen sowie Netplan bleiben unverändert. Für geschützte
Konfigurationen wurden Hashes/Metadaten erfasst, keine Passwörter oder privaten
Schlüssel ausgegeben. NetworkManager und systemd-resolved bleiben aktiv.

## Neues Paket bleibt ausstehend

Vorhanden und unverändert:

`/dev-lab/projects/netmon-v4-dns-integration-test/dist/netmon_1.1.21~v4dnstest20261031.1_all.deb`

SHA-256:
`c4d9487f53fa7f34eb7f48e7e154161b9983865b2d38cc0fe7e152751f010d92`.

**Nicht ausgeführt:** Installation des neuen DEB, Purge, Autoremove,
NetMon-Menüdeinstaller, Geräteaktionen, DNS-/Firewall-/VPN-Änderungen,
Commits oder Pushes. Nach der Entfernung wurde ausschließlich die mögliche
Neuinstallation simuliert. Keine neue KS48- oder Archivprüfung.

Nachweise: `integration-evidence/apt-remove-20261031/` mit geprüften Skripten,
APT-Plänen und tatsächlichem Entfernungslog, Roh-/Vergleichsdaten vor/nach,
Einstellungshashes, Prozess-/Paketstatus sowie begrenztem Prüfablauf.
Die Nachweise liegen in einem privaten Verzeichnis. Der ausgeführte administrative
Ablauf dient nur als Nachweis und darf nicht blind wiederholt werden.

**Entfernung abgeschlossen. Neues DEB nicht installiert. Hier gestoppt.**
