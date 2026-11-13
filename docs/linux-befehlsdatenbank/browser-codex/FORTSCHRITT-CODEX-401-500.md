# Ausarbeitung und Prüfung 401–500

Basis: Branch `codex/linux-docs-browser-handoff-20261113`, Commit `53fbd4b8c8ddc62e2fd88f47d49bb57f95cd2ba4`. Prüfdatum 2026-11-13. Der Nutzerauftrag „genauso weiter mit 401–500“ ersetzt die frühere Bereichsgrenze und setzt denselben Quellen-, Sicherheits- und Qualitätsmaßstab fort. Keine Bearbeitung 301–400 oder über 500. Keine Unteragenten.

Separate Arbeitskopie: `/tmp/linux-docs-401-500-20261113`. Der lokale Hauptarbeitsbaum und fremde Änderungen bleiben unverändert. Es werden ausschließlich die neuen Dokumente und dieser eigene Bericht veröffentlicht, wie zuletzt auf ausdrücklichen Nutzerauftrag; kein Merge nach main.

Für 401–500 existierte kein veröffentlichter eingefrorener Teilkatalog. Deshalb wurden ausschließlich Kennung, Name, Kategorie, Dateiname und unveränderte Originalfelder aus dem vorhandenen lokalen Index gelesen und gegen die Original-CSV geprüft. Index-Snapshot SHA-256: `3ba7b7a07bb8085f85f91f2df7b8e24f8c0ba51d4965f9c77b59f808c1727595`. CSV: 713 Datensätze, SHA-256 `40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`. Die feste Zuordnung ist in der folgenden Tabelle vollständig festgehalten; ein gleichlautender temporärer Prüf-Snapshot liegt außerhalb des Repositories. Zentraler Index, bestehender Katalog und Prüfcode werden nicht geändert.

Der vorhandene CLI-Prüfer begrenzt seine Nummern auf 201–300. Für 401–500 wird deshalb dieselbe vorhandene Funktion `check_document` mit dem geprüften Zuordnungssnapshot direkt aufgerufen: gleicher tatsächlicher Parser, gleiche Metadaten- und Zehnabschnittsprüfung, keine Codeänderung oder Erweiterung von Ausführungsrechten. Nach jeder Datei folgt die Einzelprüfung. Bashblöcke werden zusätzlich mit bash -n geprüft; Funktionsprüfung wird separat ausgewiesen.

Beispiele nur an kleinen eigenen temporären Daten; mktemp-Fehler bricht ab. Keine realen Netzabfragen, Pakete/Toolchains, Dienste, Benutzer-/Systemeinstellungen, Geräte- oder Desktopaktionen zum Funktionsnachweis. Fehlende Programme und unzulässige Abläufe bleiben praktisch offen. Hilfe oder Versionsausgabe allein ist kein Funktionsnachweis. Primärquellenrecherche ist davon getrennt.

## Feste Zuordnung

| Nr. | Kennung | Name | Kategorie | Datei |
| --- | --- | --- | --- | --- |
| 401 | avahi_browse | avahi-browse | NetMon Spezial / Diagnoseideen | avahi_browse.md |
| 402 | avahi_daemon | avahi-daemon | NetMon Spezial / Diagnoseideen | avahi_daemon.md |
| 403 | avahi_resolve | avahi-resolve | NetMon Spezial / Diagnoseideen | avahi_resolve.md |
| 404 | bmon | bmon | NetMon Spezial / Diagnoseideen | bmon.md |
| 405 | darkstat | darkstat | NetMon Spezial / Diagnoseideen | darkstat.md |
| 406 | hping3 | hping3 | NetMon Spezial / Diagnoseideen | hping3.md |
| 407 | iperf | iperf | NetMon Spezial / Diagnoseideen | iperf.md |
| 408 | iperf3 | iperf3 | NetMon Spezial / Diagnoseideen | iperf3.md |
| 409 | masscan | masscan | NetMon Spezial / Diagnoseideen | masscan.md |
| 410 | nload | nload | NetMon Spezial / Diagnoseideen | nload.md |
| 411 | nm_connection_editor | nm-connection-editor | NetMon Spezial / Diagnoseideen | nm_connection_editor.md |
| 412 | nm_online | nm-online | NetMon Spezial / Diagnoseideen | nm_online.md |
| 413 | nping | nping | NetMon Spezial / Diagnoseideen | nping.md |
| 414 | ntopng | ntopng | NetMon Spezial / Diagnoseideen | ntopng.md |
| 415 | speedtest | speedtest | NetMon Spezial / Diagnoseideen | speedtest.md |
| 416 | tcpflow | tcpflow | NetMon Spezial / Diagnoseideen | tcpflow.md |
| 417 | tcpreplay | tcpreplay | NetMon Spezial / Diagnoseideen | tcpreplay.md |
| 418 | vnstat | vnstat | NetMon Spezial / Diagnoseideen | vnstat.md |
| 419 | vnstatd | vnstatd | NetMon Spezial / Diagnoseideen | vnstatd.md |
| 420 | wavemon | wavemon | NetMon Spezial / Diagnoseideen | wavemon.md |
| 421 | arp | arp | Netzwerk Grundlagen | arp.md |
| 422 | arping | arping | Netzwerk Grundlagen | arping.md |
| 423 | bridge | bridge | Netzwerk Grundlagen | bridge.md |
| 424 | conntrack | conntrack | Netzwerk Grundlagen | conntrack.md |
| 425 | dnsdomainname | dnsdomainname | Netzwerk Grundlagen | dnsdomainname.md |
| 426 | domainname | domainname | Netzwerk Grundlagen | domainname.md |
| 427 | ethtool | ethtool | Netzwerk Grundlagen | ethtool.md |
| 428 | ifconfig | ifconfig | Netzwerk Grundlagen | ifconfig.md |
| 429 | ip | ip | Netzwerk Grundlagen | ip.md |
| 430 | iw | iw | Netzwerk Grundlagen | iw.md |
| 431 | iwconfig | iwconfig | Netzwerk Grundlagen | iwconfig.md |
| 432 | iwlist | iwlist | Netzwerk Grundlagen | iwlist.md |
| 433 | mtr | mtr | Netzwerk Grundlagen | mtr.md |
| 434 | netstat | netstat | Netzwerk Grundlagen | netstat.md |
| 435 | networkctl | networkctl | Netzwerk Grundlagen | networkctl.md |
| 436 | nisdomainname | nisdomainname | Netzwerk Grundlagen | nisdomainname.md |
| 437 | nmcli | nmcli | Netzwerk Grundlagen | nmcli.md |
| 438 | nmtui | nmtui | Netzwerk Grundlagen | nmtui.md |
| 439 | ping | ping | Netzwerk Grundlagen | ping.md |
| 440 | ping6 | ping6 | Netzwerk Grundlagen | ping6.md |
| 441 | resolvectl | resolvectl | Netzwerk Grundlagen | resolvectl.md |
| 442 | route | route | Netzwerk Grundlagen | route.md |
| 443 | ss | ss | Netzwerk Grundlagen | ss.md |
| 444 | systemd_resolve | systemd-resolve | Netzwerk Grundlagen | systemd_resolve.md |
| 445 | tc | tc | Netzwerk Grundlagen | tc.md |
| 446 | tracepath | tracepath | Netzwerk Grundlagen | tracepath.md |
| 447 | traceroute | traceroute | Netzwerk Grundlagen | traceroute.md |
| 448 | ypdomainname | ypdomainname | Netzwerk Grundlagen | ypdomainname.md |
| 449 | apk | apk | Paketverwaltung | apk.md |
| 450 | apt | apt | Paketverwaltung | apt.md |
| 451 | apt_cache | apt-cache | Paketverwaltung | apt_cache.md |
| 452 | apt_get | apt-get | Paketverwaltung | apt_get.md |
| 453 | apt_mark | apt-mark | Paketverwaltung | apt_mark.md |
| 454 | brew | brew | Paketverwaltung | brew.md |
| 455 | cargo | cargo | Paketverwaltung | cargo.md |
| 456 | dnf | dnf | Paketverwaltung | dnf.md |
| 457 | dpkg | dpkg | Paketverwaltung | dpkg.md |
| 458 | dpkg_query | dpkg-query | Paketverwaltung | dpkg_query.md |
| 459 | emerge | emerge | Paketverwaltung | emerge.md |
| 460 | flatpak | flatpak | Paketverwaltung | flatpak.md |
| 461 | gem | gem | Paketverwaltung | gem.md |
| 462 | guix | guix | Paketverwaltung | guix.md |
| 463 | nix_env | nix-env | Paketverwaltung | nix_env.md |
| 464 | npm | npm | Paketverwaltung | npm.md |
| 465 | pacman | pacman | Paketverwaltung | pacman.md |
| 466 | pamac | pamac | Paketverwaltung | pamac.md |
| 467 | paru | paru | Paketverwaltung | paru.md |
| 468 | pip | pip | Paketverwaltung | pip.md |
| 469 | pip3 | pip3 | Paketverwaltung | pip3.md |
| 470 | pipx | pipx | Paketverwaltung | pipx.md |
| 471 | pnpm | pnpm | Paketverwaltung | pnpm.md |
| 472 | rpm | rpm | Paketverwaltung | rpm.md |
| 473 | snap | snap | Paketverwaltung | snap.md |
| 474 | yarn | yarn | Paketverwaltung | yarn.md |
| 475 | yay | yay | Paketverwaltung | yay.md |
| 476 | yum | yum | Paketverwaltung | yum.md |
| 477 | zypper | zypper | Paketverwaltung | zypper.md |
| 478 | atop | atop | Prozesse & Jobs | atop.md |
| 479 | bg | bg | Prozesse & Jobs | bg.md |
| 480 | btop | btop | Prozesse & Jobs | btop.md |
| 481 | chrt | chrt | Prozesse & Jobs | chrt.md |
| 482 | disown | disown | Prozesse & Jobs | disown.md |
| 483 | fg | fg | Prozesse & Jobs | fg.md |
| 484 | fuser | fuser | Prozesse & Jobs | fuser.md |
| 485 | glances | glances | Prozesse & Jobs | glances.md |
| 486 | htop | htop | Prozesse & Jobs | htop.md |
| 487 | iftop | iftop | Prozesse & Jobs | iftop.md |
| 488 | ionice | ionice | Prozesse & Jobs | ionice.md |
| 489 | iotop | iotop | Prozesse & Jobs | iotop.md |
| 490 | jobs | jobs | Prozesse & Jobs | jobs.md |
| 491 | kill | kill | Prozesse & Jobs | kill.md |
| 492 | killall | killall | Prozesse & Jobs | killall.md |
| 493 | lsof | lsof | Prozesse & Jobs | lsof.md |
| 494 | ltrace | ltrace | Prozesse & Jobs | ltrace.md |
| 495 | nethogs | nethogs | Prozesse & Jobs | nethogs.md |
| 496 | nice | nice | Prozesse & Jobs | nice.md |
| 497 | nohup | nohup | Prozesse & Jobs | nohup.md |
| 498 | perf | perf | Prozesse & Jobs | perf.md |
| 499 | pgrep | pgrep | Prozesse & Jobs | pgrep.md |
| 500 | pidof | pidof | Prozesse & Jobs | pidof.md |

## 401 – [avahi_browse.md](../avahi_browse.md)

- Inhalt: mDNS-Dienste mit DNS-SD entdecken. avahi-browse fragt über den Avahi-Daemon nach im Netz angekündigten DNS-SD-Diensten. Es öffnet die gefundenen Dienste nicht selbst. Die Anzeige kann echte Multicastanfragen auslösen und ist deshalb keine rein lokale Dateiabfrage.
- Gelesene Primärquelle: [Avahi-Projekthandbuch: avahi-browse](https://manpages.debian.org/trixie/avahi-utils/avahi-browse.1.en.html) und lokale Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 401: `format: ok`.

## 402 – [avahi_daemon.md](../avahi_daemon.md)

- Inhalt: Den mDNS-/DNS-SD-Dienst von Avahi verstehen. avahi-daemon ist ein Hintergrunddienst für mDNS und DNS-SD. Ein Start registriert lokale Adressen und konfigurierte Dienste im Netz. Es ist keine gewöhnliche Diagnoseanzeige; normale Dienstverwaltung erfordert administrative Rechte.
- Gelesene Primärquelle: [Avahi-Projekthandbuch: avahi-daemon](https://manpages.debian.org/trixie/avahi-daemon/avahi-daemon.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 402: `format: ok`.

## 403 – [avahi_resolve.md](../avahi_resolve.md)

- Inhalt: mDNS-/DNS-Namen über Avahi auflösen. avahi-resolve übersetzt Namen in Adressen oder Adressen in Namen und verwendet dabei den Avahi-Daemon. Ein normaler Benutzer braucht dafür kein Root, aber Zugriff auf den laufenden Dienst. Der Aufruf kann echte Namensanfragen erzeugen.
- Gelesene Primärquelle: [Avahi-Projekthandbuch: avahi-resolve](https://manpages.debian.org/trixie/avahi-utils/avahi-resolve.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 403: `format: ok`.

## 404 – [bmon.md](../bmon.md)

- Inhalt: Schnittstellenzähler und Datenraten beobachten. bmon sammelt Netzwerkstatistiken und berechnet daraus Datenraten. Standardmäßig zeigt eine Terminaloberfläche die Werte. Es misst keinen maximalen Internetdurchsatz und ordnet Datenverkehr nicht automatisch einzelnen Anwendungen zu.
- Gelesene Primärquelle: [bmon-Projekthandbuch](https://manpages.debian.org/trixie/bmon/bmon.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; bmon fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 404: `format: ok`.

## 405 – [darkstat.md](../darkstat.md)

- Inhalt: Paketstatistik sammeln und Webanzeige begrenzen. darkstat zeichnet Netzwerkstatistiken aus Paketen auf und bietet sie über einen HTTP-Dienst an. Ein normaler Start ist damit Mitschnitt und Serverstart. Live-Capture benötigt typischerweise besondere Rechte; diese Rechte dürfen danach nicht unnötig beibehalten werden.
- Gelesene Primärquelle: [darkstat-Projekthandbuch](https://manpages.debian.org/trixie/darkstat/darkstat.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; darkstat fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 405: `format: ok`.

## 406 – [hping3.md](../hping3.md)

- Inhalt: Gezielte Protokollpakete von einem normalen Ping unterscheiden. hping3 erzeugt anpassbare TCP/IP-Pakete und zeigt Antworten an. Der gewöhnliche Aufruf sendet tatsächlich; er ist keine passive Firewallprüfung. Rohe Pakete benötigen üblicherweise Root oder geeignete Capabilities.
- Gelesene Primärquelle: [hping-Projekthandbuch](https://manpages.debian.org/trixie/hping3/hping3.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; hping3 fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 406: `format: ok`.

## 407 – [iperf.md](../iperf.md)

- Inhalt: Durchsatz mit iperf 2 planen und interpretieren. Der Programmname iperf bezeichnet hier iperf 2. Client und Server erzeugen beziehungsweise empfangen echte Testlast. Normale Tests an unprivilegierten Ports benötigen meist kein Root. iperf 2 und iperf3 sprechen unterschiedliche Protokolle.
- Gelesene Primärquelle: [iperf-2-Projekthandbuch](https://manpages.debian.org/trixie/iperf/iperf.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; iperf fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 407: `format: ok`.

## 408 – [iperf3.md](../iperf3.md)

- Inhalt: iperf3-Messrichtung und Ergebnisberichte verstehen. iperf3 misst Durchsatz durch selbst erzeugten TCP-, UDP- oder unterstützten SCTP-Verkehr. Ein Test braucht einen passenden iperf3-Server und Client. Es ist kein passiver Geschwindigkeitssensor; normale unprivilegierte Ports benötigen meist kein Root.
- Gelesene Primärquelle: [ESnet: iperf3-Aufrufhandbuch](https://software.es.net/iperf/invoking.html)
- Lokaler Stand: Nicht praktisch geprüft; iperf3 fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 408: `format: ok`.

## 409 – [masscan.md](../masscan.md)

- Inhalt: Masscan-Konfiguration vor einem Scan lesen. masscan ist ein aktiver Portscanner mit eigener Paketverarbeitung. Ein gewöhnlicher Scan erzeugt reale Netzwerkpakete und braucht typischerweise besondere Rechte. Es ist keine harmlose Statusabfrage und keine vollständige Ersatzimplementierung aller Nmap-Funktionen.
- Gelesene Primärquelle: [Masscan-Projekt: README und Konfigurationsmodus](https://github.com/robertdavidgraham/masscan/blob/master/README.md)
- Lokaler Stand: Nicht praktisch geprüft; masscan fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 409: `format: ok`.

## 410 – [nload.md](../nload.md)

- Inhalt: Eingehende und ausgehende Datenraten im Terminal lesen. nload visualisiert aktuelle Interfacezähler und daraus berechnete Raten. Es erzeugt selbst keinen Durchsatztest. Für übliche Linuxzähler sind normalerweise keine Rootrechte nötig; es ist kein Mitschnitt einzelner Paketinhalte.
- Gelesene Primärquelle: [nload-Projekthandbuch](https://manpages.debian.org/trixie/nload/nload.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; nload fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 410: `format: ok`.

## 411 – [nm_connection_editor.md](../nm_connection_editor.md)

- Inhalt: NetworkManager-Profile grafisch bearbeiten. nm-connection-editor ist ein GTK-Editor für gespeicherte NetworkManager-Verbindungsprofile. Er kann hinzufügen, ändern und löschen. Die Oberfläche ist deshalb kein ausschließlich lesendes Diagnosewerkzeug.
- Gelesene Primärquelle: [NetworkManager-Applet-Handbuch](https://manpages.debian.org/bookworm/network-manager-gnome/nm-connection-editor.1.en.html) und lokale Manpage; neuere Webpfade waren nicht erreichbar. Handbuchstand ist keine ausgeführte Programmversion
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 411: `format: ok`.

## 412 – [nm_online.md](../nm_online.md)

- Inhalt: Auf NetworkManager-Zustände warten. nm-online wartet auf einen von NetworkManager gemeldeten Zustand. Es konfiguriert selbst keine Verbindung und ist kein unabhängiger Internet-, DNS- oder VPN-Test. Für die normale Statusabfrage ist kein Root erforderlich.
- Gelesene Primärquelle: [NetworkManager: nm-online](https://networkmanager.dev/docs/api/latest/nm-online.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 412: `format: ok`.

## 413 – [nping.md](../nping.md)

- Inhalt: Nping-Proben gezielt planen. nping erzeugt Netzwerkproben und analysiert Antworten. TCP-Connect kann ohne besondere Rechte laufen; Raw-TCP, ICMP oder ARP haben andere Rechteanforderungen. Jeder echte Zielaufruf kann Verkehr erzeugen.
- Gelesene Primärquelle: [Nmap-Projekt: Nping-Handbuch](https://nmap.org/book/nping-man.html) und lokale Hilfe
- Lokaler Stand: Nping 0.7.94SVN. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 413: `format: ok`.

## 414 – [ntopng.md](../ntopng.md)

- Inhalt: Verkehrsanalyse mit ntopng einordnen. ntopng analysiert Paket- oder Flowdaten und bietet eine Weboberfläche. Ein normaler Start kann Capture, Weblistener, Datenbankzugriffe und Zusatzabfragen auslösen. Er ist keine rein lesende Momentaufnahme.
- Gelesene Primärquelle: [ntop-Projekt: ntopng-CLI](https://www.ntop.org/guides/ntopng/cli_options/cli_options.html)
- Lokaler Stand: Nicht praktisch geprüft; ntopng fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 414: `format: ok`.

## 415 – [speedtest.md](../speedtest.md)

- Inhalt: Den tatsächlich installierten Speedtest-Client bestimmen. Der Name speedtest ist mehrdeutig. Hier verweist der lokale Startcode auf das Pythonprojekt speedtest-cli; der offizielle Ookla-Client hat eine andere CLI. Ein normaler Test überträgt echte Daten und benötigt üblicherweise kein Root.
- Gelesene Primärquelle: [speedtest-cli-Projekt und CLI](https://github.com/sivel/speedtest-cli), lokale speedtest-cli-Manpage und gelesener /usr/bin/speedtest-Wrapper; kein Inhaltsbeleg aus der nicht erreichbaren Ookla-Seite
- Lokaler Stand: Nicht praktisch geprüft; Wrapper nennt speedtest-cli 2.1.3, keine ausgeführte Version. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 415: `format: ok`.

## 416 – [tcpflow.md](../tcpflow.md)

- Inhalt: TCP-Datenströme aus Paketen rekonstruieren. tcpflow setzt erfasste TCP-Nutzdaten zu gerichteten Datenströmen zusammen und schreibt sie meist in Dateien. Es ist kein einfacher Socketstatusbefehl. Eigene Offline-PCAPs benötigen nur passende Dateirechte; Live-Capture braucht besondere Rechte.
- Gelesene Primärquelle: [tcpflow-Projekthandbuch](https://manpages.debian.org/trixie/tcpflow-nox/tcpflow.1.en.html) und [Projektbeschreibung](https://github.com/simsong/tcpflow)
- Lokaler Stand: Nicht praktisch geprüft; tcpflow fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 416: `format: ok`.

## 417 – [tcpreplay.md](../tcpreplay.md)

- Inhalt: PCAP-Pakete kontrolliert erneut senden. Tcpreplay sendet gespeicherte Capturepakete über eine ausgewählte Schnittstelle erneut. Eine PCAP ist dabei Eingabe eines aktiven Senders, keine harmlose Dokumentdatei. Raw-Injektion benötigt normalerweise besondere Rechte.
- Gelesene Primärquelle: [Tcpreplay-Projekthandbuch](https://tcpreplay.appneta.com/reference/man/tcpreplay/)
- Lokaler Stand: Nicht praktisch geprüft; tcpreplay fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 417: `format: ok`.

## 418 – [vnstat.md](../vnstat.md)

- Inhalt: Gespeicherte Netzwerkverbrauchsstatistik lesen. vnstat zeigt langfristige Verkehrsstatistiken aus seiner Datenbank. Es ist kein Paketmitschnitt und kein Durchsatztest. Abfragen lesbarer Daten brauchen normalerweise kein Root; Datenbankänderungen benötigen passende Schreibrechte.
- Gelesene Primärquelle: [vnStat-Projekt: vnstat-Handbuch](https://humdi.net/vnstat/man/vnstat.html)
- Lokaler Stand: Nicht praktisch geprüft; vnstat fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 418: `format: ok`.

## 419 – [vnstatd.md](../vnstatd.md)

- Inhalt: Interfacezähler dauerhaft in vnStat speichern. vnstatd ist der Datensammler von vnStat. Er liest Interfacezähler und schreibt eine Datenbank. Der Start ist eine echte Hintergrund-/Speicheraktion, auch wenn keine eigenen Messpakete erzeugt werden.
- Gelesene Primärquelle: [vnStat-Projekt: vnstatd-Handbuch](https://humdi.net/vnstat/man/vnstatd.html)
- Lokaler Stand: Nicht praktisch geprüft; vnstatd fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 419: `format: ok`.

## 420 – [wavemon.md](../wavemon.md)

- Inhalt: WLAN-Signalwerte ohne falsche Durchsatzschlüsse lesen. wavemon zeigt WLAN-Geräteinformationen und Signalverläufe in einer Terminaloberfläche. Einige Ansichten lösen Scans aus oder speichern Einstellungen. Allgemeine Anzeigerechte und CAP_NET_ADMIN für bestimmte Operationen sind zu unterscheiden.
- Gelesene Primärquelle: [wavemon-Projekthandbuch](https://manpages.debian.org/trixie/wavemon/wavemon.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; wavemon fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 420: `format: ok`.

## 421 – [arp.md](../arp.md)

- Inhalt: IPv4-Nachbarcache lesen und Änderungen erkennen. arp aus net-tools zeigt und verändert den IPv4-Nachbarcache des Kernels. Lesende Anzeigen brauchen meist kein Root; Setzen und Löschen erfordern Netzwerkadministrationsrechte. IPv6 verwendet Neighbor Discovery statt dieser ARP-Tabelle.
- Gelesene Primärquelle: [net-tools: arp-Handbuch](https://manpages.debian.org/trixie/net-tools/arp.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 421: `format: ok`.

## 422 – [arping.md](../arping.md)

- Inhalt: Aktive ARP-Proben im lokalen Netz verstehen. Hier ist arping aus iputils beschrieben. Es sendet IPv4-ARP-Pakete auf einem Link und benötigt CAP_NET_RAW beziehungsweise passende Privilegien. Andere Programme gleichen Namens können andere Optionen besitzen.
- Gelesene Primärquelle: [iputils: arping-Handbuch](https://manpages.debian.org/trixie/iputils-arping/arping.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; arping fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 422: `format: ok`.

## 423 – [bridge.md](../bridge.md)

- Inhalt: Bridge-Zustand nach Objekt lesen. bridge aus iproute2 verwaltet Linux-Bridges. Lesende Anzeigen und Änderungen am Weiterleitungsverhalten sind unterschiedliche Operationen. Das Werkzeug erstellt nicht durch seinen bloßen Aufruf eine neue Bridge.
- Gelesene Primärquelle: [iproute2: bridge-Handbuch](https://man7.org/linux/man-pages/man8/bridge.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 423: `format: ok`.

## 424 – [conntrack.md](../conntrack.md)

- Inhalt: Verbindungsverfolgung ist keine Socketliste. conntrack liest und verändert die Netfilter-Verbindungsverfolgung. Auch lesende Abfragen benötigen typischerweise CAP_NET_ADMIN. Ein getrackter Paketfluss muss keinem lokalen Prozess-Socket entsprechen.
- Gelesene Primärquelle: [Netfilter: conntrack-Handbuch](https://manpages.debian.org/trixie/conntrack/conntrack.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 424: `format: ok`.

## 425 – [dnsdomainname.md](../dnsdomainname.md)

- Inhalt: DNS-Domänenteil des aufgelösten Hostnamens anzeigen. dnsdomainname aus net-tools zeigt den Domänenteil des kanonisch aufgelösten lokalen Hostnamens. Es setzt keine DNS-Domain und ist kein allgemeines DNS-Abfragewerkzeug.
- Gelesene Primärquelle: [net-tools: hostname/dnsdomainname-Handbuch](https://man7.org/linux/man-pages/man1/hostname.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 425: `format: ok`.

## 426 – [domainname.md](../domainname.md)

- Inhalt: NIS-Domain vom DNS-Namen unterscheiden. domainname aus net-tools zeigt ohne Namen die NIS/YP-Domain des Kernels. Mit neuem Namen oder einer Namensdatei kann es diese ändern. Der Befehl verwaltet keine DNS-Zone.
- Gelesene Primärquelle: [net-tools: domainname/hostname-Handbuch](https://man7.org/linux/man-pages/man1/domainname.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 426: `format: ok`.

## 427 – [ethtool.md](../ethtool.md)

- Inhalt: Treiber- und Linkinformationen gezielt unterscheiden. ethtool fragt Eigenschaften von Netzwerktreibern und Geräten ab und kann sie verändern. Ein lesender Gerätebericht ist weder ein Durchsatztest noch eine Aufforderung, Linkparameter zu setzen.
- Gelesene Primärquelle: [ethtool-Projekthandbuch](https://man7.org/linux/man-pages/man8/ethtool.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 427: `format: ok`.

## 428 – [ifconfig.md](../ifconfig.md)

- Inhalt: Ältere Interfaceanzeige richtig lesen. ifconfig aus net-tools zeigt Schnittstellen und verändert deren Laufzeitkonfiguration. Ohne zusätzliche Konfigurationsargumente wird angezeigt; mit Adressen, up oder down wird ein Eingriff angefordert.
- Gelesene Primärquelle: [net-tools: ifconfig-Handbuch](https://man7.org/linux/man-pages/man8/ifconfig.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 428: `format: ok`.

## 429 – [ip.md](../ip.md)

- Inhalt: Netzwerkobjekt und Operation ausdrücklich wählen. ip aus iproute2 ist eine gemeinsame Oberfläche für Links, Adressen, Routen und weitere Netzwerkobjekte. Sein Risiko hängt vom Unterbefehl ab: show liest, add/delete/set/flush können das System verändern.
- Gelesene Primärquelle: [iproute2: ip-Handbuch](https://man7.org/linux/man-pages/man8/ip.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 429: `format: ok`.

## 430 – [iw.md](../iw.md)

- Inhalt: WLAN-Fähigkeiten und aktuellen Link trennen. iw ist das nl80211-basierte WLAN-Werkzeug für moderne Linux-Treiber. Es kann Fähigkeiten und Linkzustand anzeigen, aber auch Scans, Verbindungen und Funkkonfiguration anfordern.
- Gelesene Primärquelle: [Linux Wireless: iw-Dokumentation](https://wireless.docs.kernel.org/en/latest/en/users/documentation/iw.html)
- Lokaler Stand: Nicht praktisch geprüft; iw fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 430: `format: ok`.

## 431 – [iwconfig.md](../iwconfig.md)

- Inhalt: Wireless Extensions ohne moderne Profilverwaltung einordnen. iwconfig zeigt und setzt ältere Wireless-Extensions-Parameter. Ein Interfaceargument allein ist eine Anzeige; zusätzliche Schlüsselwörter wie essid, mode oder channel fordern Änderungen an.
- Gelesene Primärquelle: [Wireless Tools: iwconfig-Handbuch](https://manpages.debian.org/trixie/wireless-tools/iwconfig.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 431: `format: ok`.

## 432 – [iwlist.md](../iwlist.md)

- Inhalt: WLAN-Liste bedeutet nicht automatisch passiv. iwlist liefert zusätzliche Wireless-Extensions-Informationen. Der gewählte Informationsbereich entscheidet über Wirkung und Sensibilität; scanning kann einen aktiven Funkscan auslösen.
- Gelesene Primärquelle: [Wireless Tools: iwlist-Handbuch](https://manpages.debian.org/trixie/wireless-tools/iwlist.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 432: `format: ok`.

## 433 – [mtr.md](../mtr.md)

- Inhalt: Hop-Messungen ohne falsche Verlustdiagnose erklären. mtr kombiniert wiederholte Laufzeitmessungen mit einer Hop-Darstellung. Es sendet aktiv Pakete; ein Reportmodus ist kein passiver Bericht über früheren Verkehr.
- Gelesene Primärquelle: [mtr-Projekthandbuch](https://manpages.debian.org/trixie/mtr-tiny/mtr.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 433: `format: ok`.

## 434 – [netstat.md](../netstat.md)

- Inhalt: Socketanzeigen und Erreichbarkeit auseinanderhalten. netstat aus net-tools zeigt unter anderem Sockets, Routen und Interfacezähler. Für neue Anleitungen verweist sein Handbuch auf ss beziehungsweise die passenden ip-Unterbefehle.
- Gelesene Primärquelle: [net-tools: netstat-Handbuch](https://man7.org/linux/man-pages/man8/netstat.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 434: `format: ok`.

## 435 – [networkctl.md](../networkctl.md)

- Inhalt: Die Sicht von systemd-networkd verstehen. networkctl zeigt und verändert Links aus Sicht von systemd-networkd. Ein unmanaged-Link kann von einem anderen Dienst betreut werden; er ist dadurch nicht automatisch unbenutzbar.
- Gelesene Primärquelle: [systemd: networkctl-Handbuch](https://www.freedesktop.org/software/systemd/man/latest/networkctl.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 435: `format: ok`.

## 436 – [nisdomainname.md](../nisdomainname.md)

- Inhalt: NIS-Aufrufname mit schreibender Form erkennen. nisdomainname ist im net-tools-Umfeld ein Aufrufname zur NIS/YP-Domain. Ohne neuen Namen wird angezeigt; mit Namen wird eine Kerneländerung angefordert.
- Gelesene Primärquelle: [net-tools: hostname/NIS-Handbuch](https://man7.org/linux/man-pages/man1/hostname.1.html) sowie lokale hostname-Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 436: `format: ok`.

## 437 – [nmcli.md](../nmcli.md)

- Inhalt: Ein Profil ausschließlich als Text erzeugen. nmcli steuert NetworkManager und zeigt dessen Zustand. Im ausdrücklich gewählten Offline-Modus lassen sich Profiltexte ohne Daemonzugriff erzeugen. Ohne diesen Modus ist connection add eine echte Profiländerung.
- Gelesene Primärquelle: [NetworkManager: nmcli-Handbuch](https://networkmanager.dev/docs/api/latest/nmcli.html) und lokale nmcli-Manpage
- Lokaler Stand: nmcli 1.46.0. Praktisch geprüft: Offline-Erzeugung eines eigenen Profiltexts und drei Felder praktisch geprüft. Nicht geprüft: Daemon, Import, Aktivierung, Geräte, DHCP, DNS, Rechte- und Geheimnisfälle.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 437: `format: ok`.

## 438 – [nmtui.md](../nmtui.md)

- Inhalt: Textoberfläche mit echten Verwaltungsaktionen. nmtui ist die Terminaloberfläche von NetworkManager. Menüpunkte können Profile speichern, Verbindungen schalten und den Systemhostname ändern. Eine Textoberfläche ist kein Simulationsmodus.
- Gelesene Primärquelle: [NetworkManager: nmtui-Handbuch](https://networkmanager.dev/docs/api/latest/nmtui.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 438: `format: ok`.

## 439 – [ping.md](../ping.md)

- Inhalt: ICMP-Antworten mit begrenzter Aussagekraft. ping aus iputils sendet ICMP-Echo-Anfragen und misst Antworten. Es ist ein aktiver Netztest und bestätigt bei Erfolg keine Erreichbarkeit eines bestimmten TCP-/UDP-Dienstes.
- Gelesene Primärquelle: [iputils: ping-Handbuch](https://man7.org/linux/man-pages/man8/ping.8.html) sowie lokale ping-Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 439: `format: ok`.

## 440 – [ping6.md](../ping6.md)

- Inhalt: Historischen IPv6-Aufrufnamen richtig verwenden. ping6 bezeichnet in iputils die IPv6-Ping-Funktion. Sie ist seit iputils s20150815 in ping integriert; ein Aufrufname oder Symlink ping6 kann aus Kompatibilitätsgründen weiter existieren.
- Gelesene Primärquelle: [iputils: ping-Handbuch und HISTORY](https://man7.org/linux/man-pages/man8/ping.8.html) sowie lokale ping-Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 440: `format: ok`.

## 441 – [resolvectl.md](../resolvectl.md)

- Inhalt: Resolverzustand von aktiver Anfrage unterscheiden. resolvectl arbeitet mit systemd-resolved. status zeigt dessen globale und linkbezogene Einstellungen; query löst Namen oder Adressen auf und kann Netzverkehr auslösen.
- Gelesene Primärquelle: [systemd: resolvectl-Handbuch](https://www.freedesktop.org/software/systemd/man/latest/resolvectl.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 441: `format: ok`.

## 442 – [route.md](../route.md)

- Inhalt: Legacy-Routenanzeige ohne Konfigurationsauftrag. route aus net-tools zeigt ohne add/del die Kernelrouten. Mit add oder del verändert es Routing. Moderne Policy-Routing-Fragen werden mit ip route und ip rule genauer abgebildet.
- Gelesene Primärquelle: [net-tools: route-Handbuch](https://man7.org/linux/man-pages/man8/route.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 442: `format: ok`.

## 443 – [ss.md](../ss.md)

- Inhalt: Sockets mit ausdrücklich lesendem Modus untersuchen. ss aus iproute2 zeigt Sockets und TCP-Details. Die meisten Anzeigen sind lesend; die Option --kill beziehungsweise -K kann dagegen Sockets zwangsweise schließen.
- Gelesene Primärquelle: [iproute2: ss-Handbuch](https://man7.org/linux/man-pages/man8/ss.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 443: `format: ok`.

## 444 – [systemd_resolve.md](../systemd_resolve.md)

- Inhalt: Historische Resolveroberfläche mit eigener Syntax. systemd-resolve ist die ältere CLI für systemd-resolved. Der eingefrorene Katalogname bleibt erhalten. Auf aktuellen Installationen ist üblicherweise resolvectl die dokumentierte Oberfläche; alte Optionen werden nicht unverändert übertragen.
- Gelesene Primärquelle: [systemd v238: originale systemd-resolve-Handbuchdatei](https://raw.githubusercontent.com/systemd/systemd/v238/man/systemd-resolve.xml)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale systemd-resolve-Manpage. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 444: `format: ok`.

## 445 – [tc.md](../tc.md)

- Inhalt: Queueing-Objekte statt pauschaler Bandbreitenbegrenzung. tc aus iproute2 zeigt und verändert Traffic-Control-Objekte des Linux-Kernels. Lesende show-Formen sind von Änderungen an Queues, Klassen, Filtern und Aktionen zu trennen.
- Gelesene Primärquelle: [iproute2: tc-Handbuch](https://man7.org/linux/man-pages/man8/tc.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 445: `format: ok`.

## 446 – [tracepath.md](../tracepath.md)

- Inhalt: Pfad und Path-MTU aktiv erkunden. tracepath aus iputils sendet UDP-Proben und wertet Fehlerantworten aus, um Hops und Path-MTU abzuschätzen. Es benötigt gewöhnlich keine besonderen Root-Rechte, erzeugt aber echten Netzverkehr.
- Gelesene Primärquelle: [iputils: tracepath-Handbuch](https://man7.org/linux/man-pages/man8/tracepath.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 446: `format: ok`.

## 447 – [traceroute.md](../traceroute.md)

- Inhalt: Hopantworten als Messung statt vollständige Topologie. traceroute für Linux sendet Proben mit steigender TTL beziehungsweise Hop-Limit. Es rekonstruiert Antwortpunkte, nicht garantiert alle Router oder den unveränderten Pfad einer Anwendung.
- Gelesene Primärquelle: [Traceroute für Linux: Projekthandbuch](https://man7.org/linux/man-pages/man8/traceroute.8.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 447: `format: ok`.

## 448 – [ypdomainname.md](../ypdomainname.md)

- Inhalt: YP-Domain anzeigen ohne DNS-Verwechslung. ypdomainname bezeichnet im net-tools-Umfeld die NIS/YP-Domain des Systems. Ohne Wert wird gelesen; ein übergebener Name oder eine Namensdatei kann die Domain ändern.
- Gelesene Primärquelle: [net-tools: hostname/NIS-Handbuch](https://man7.org/linux/man-pages/man1/hostname.1.html) sowie lokale hostname-Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 448: `format: ok`.

## 449 – [apk.md](../apk.md)

- Inhalt: Alpines Paketbestand und world unterscheiden. apk steht für Alpine Package Keeper und ist keine Android-APK-Verwaltung. Es verwaltet Pakete und die gewünschten obersten Paketbedingungen in world. Das Programm fehlt lokal; kein Paket wurde installiert.
- Gelesene Primärquelle: [apk-tools: originales apk-Handbuch](https://man.archlinux.org/man/apk.8.en)
- Lokaler Stand: Nicht praktisch geprüft; apk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 449: `format: ok`.

## 450 – [apt.md](../apt.md)

- Inhalt: Interaktive Paketverwaltung mit klaren Änderungsgrenzen. apt ist die benutzerorientierte Oberfläche des APT-Systems. Such-/Anzeigeformen unterscheiden sich von update, Installation und Entfernung. Die Oberfläche ist primär für Menschen gedacht.
- Gelesene Primärquelle: [APT-Team: apt-Handbuch](https://manpages.debian.org/trixie/apt/apt.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 450: `format: ok`.

## 451 – [apt_cache.md](../apt_cache.md)

- Inhalt: Lokale Paketmetadaten richtig interpretieren. apt-cache durchsucht und zeigt den lokalen APT-Metadatenbestand. Es installiert keine Pakete. Metadaten können unabhängig von gerade erreichbaren Repositories gelesen werden und veraltet sein.
- Gelesene Primärquelle: [APT-Team: apt-cache-Handbuch](https://manpages.debian.org/trixie/apt/apt-cache.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 451: `format: ok`.

## 452 – [apt_get.md](../apt_get.md)

- Inhalt: Transaktionsplanung von Installation unterscheiden. apt-get ist eine spezialisierte APT-Oberfläche. Es löst Abhängigkeiten und kann Pakete herunterladen, installieren oder entfernen. Eine Simulation beschreibt nur einen Plan auf Basis des aktuellen Stands.
- Gelesene Primärquelle: [APT-Team: apt-get-Handbuch](https://manpages.debian.org/trixie/apt/apt-get.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 452: `format: ok`.

## 453 – [apt_mark.md](../apt_mark.md)

- Inhalt: Paketmarkierungen und ihre späteren Folgen. apt-mark zeigt und ändert APT-Markierungen sowie dpkg-Auswahlzustände. Eine Markierung installiert nicht unmittelbar ein Paket, kann aber spätere Upgrade- oder Entfernungsentscheidungen beeinflussen.
- Gelesene Primärquelle: [APT-Team: apt-mark-Handbuch](https://manpages.debian.org/trixie/apt/apt-mark.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 453: `format: ok`.

## 454 – [brew.md](../brew.md)

- Inhalt: Homebrew-Prefix und Distribution getrennt verwalten. brew ist die Homebrew-Oberfläche, auch unter Linux. Sie verwaltet einen eigenen Prefix und ersetzt nicht die Paketdatenbank der Distribution. Das Programm ist hier nicht installiert.
- Gelesene Primärquelle: [Homebrew: brew-Handbuch](https://docs.brew.sh/Manpage)
- Lokaler Stand: Nicht praktisch geprüft; brew fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 454: `format: ok`.

## 455 – [cargo.md](../cargo.md)

- Inhalt: Rust-Projekte statt Systempakete verwalten. cargo ist Rusts Projekt-, Build- und Paketwerkzeug. Abhängigkeiten eines Projekts und mit cargo install bereitgestellte Programme sind verschiedene Bestände. Cargo fehlt lokal; nichts wurde nachinstalliert.
- Gelesene Primärquelle: [Rust-Projekt: Cargo-Kommandos](https://doc.rust-lang.org/cargo/commands/cargo.html) und [cargo metadata](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html)
- Lokaler Stand: Nicht praktisch geprüft; cargo fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 455: `format: ok`.

## 456 – [dnf.md](../dnf.md)

- Inhalt: DNF-Version und Transaktionsumfang klären. dnf löst Pakettransaktionen in RPM-basierten Distributionen. Hier wird die DNF4-Schnittstelle des gelesenen Handbuchs beschrieben. DNF5 kann unter demselben Aufrufnamen installiert sein und abweichende Optionen besitzen.
- Gelesene Primärquelle: [DNF-Projekt: DNF4-Kommandoreferenz](https://dnf.readthedocs.io/en/latest/command_ref.html)
- Lokaler Stand: Nicht praktisch geprüft; dnf fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 456: `format: ok`.

## 457 – [dpkg.md](../dpkg.md)

- Inhalt: Debian-Versionsregeln ohne Paketänderung prüfen. dpkg verwaltet Debian-Pakete auf niedrigerer Ebene als APT. Es lädt nicht automatisch alle fehlenden Abhängigkeiten aus Repositories. Sein Versionsvergleich ist eine eigenständige, sichere Rechenfunktion.
- Gelesene Primärquelle: [dpkg-Projekt: dpkg-Handbuch](https://man7.org/linux/man-pages/man1/dpkg.1.html)
- Lokaler Stand: dpkg 1.22.6. Praktisch geprüft: Zwei reine Versionsvergleiche samt Status 0/1 praktisch geprüft. Installation, Skripte, Trigger, Paketbestand, Rechte- und Reparaturfälle nicht geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 457: `format: ok`.

## 458 – [dpkg_query.md](../dpkg_query.md)

- Inhalt: Eine eigene Statusdatei ausdrücklich auswählen. dpkg-query liest die dpkg-Datenbank. Ein gelisteter Datensatz und eine tatsächlich funktionsfähige Anwendung sind verschiedene Dinge. Mit --admindir lässt sich die lesende Abfrage auf eine eigene Testdatenbank begrenzen.
- Gelesene Primärquelle: [dpkg-Projekt: dpkg-query-Handbuch](https://man7.org/linux/man-pages/man1/dpkg-query.1.html)
- Lokaler Stand: dpkg-query 1.22.6. Praktisch geprüft: Eigene künstliche status-Datei mit --admindir abgefragt und drei Felder geprüft. Keine Abfrage oder Änderung am Hostbestand. Dateilisten, Integrität, Multiarch und andere Versionen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 458: `format: ok`.

## 459 – [emerge.md](../emerge.md)

- Inhalt: Portage-Planung und Buildausführung unterscheiden. emerge ist die Portage-Oberfläche von Gentoo. Ohne abweichende Aktion ist die Anforderung eines Pakets grundsätzlich ein Merge-/Installationsauftrag, keine reine Suche.
- Gelesene Primärquelle: [Gentoo/Portage: emerge-Projekthandbuch](https://dev.gentoo.org/~zmedico/portage/doc/man/emerge.1.html)
- Lokaler Stand: Nicht praktisch geprüft; emerge fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 459: `format: ok`.

## 460 – [flatpak.md](../flatpak.md)

- Inhalt: Apps, Runtimes und Installationsbereich trennen. flatpak verwaltet Apps und Laufzeitumgebungen und kann sie starten. Benutzer- und systemweite Installation sind getrennte Bereiche. Eine App-Sandbox ist kein Beweis, dass alle Datenzugriffe ausgeschlossen sind.
- Gelesene Primärquelle: [Flatpak-Projekt: Kommandoreferenz](https://docs.flatpak.org/en/latest/flatpak-command-reference.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 460: `format: ok`.

## 461 – [gem.md](../gem.md)

- Inhalt: Ruby-Gems und Ruby-Umgebung zusammen betrachten. gem ist die RubyGems-Oberfläche. Sie verwaltet Ruby-Pakete und deren ausführbare Programme. Welche Installation betroffen ist, hängt vom gewählten Ruby und dessen Gem-Pfaden ab.
- Gelesene Primärquelle: [RubyGems: Kommandoreferenz](https://guides.rubygems.org/command-reference/) sowie lokale gem-Hilfe
- Lokaler Stand: RubyGems 3.4.20; nur Hilfe/Version ausgeführt. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 461: `format: ok`.

## 462 – [guix.md](../guix.md)

- Inhalt: Guix-Profilgenerationen ohne System-Rollback-Verwechslung. guix verwaltet Software in Profilen und bietet weitere getrennte System-/Entwicklungsfunktionen. Hier wird guix package behandelt. Guix fehlt lokal; die offizielle Website und PDF lieferten Zugriffsfehler.
- Gelesene Primärquelle: [GNU Guix: offizielles Handbuch, gelesene Suchindex-Auszüge; Vollabruf 403](https://guix.gnu.org/manual/en/guix.pdf)
- Lokaler Stand: Nicht praktisch geprüft; guix fehlt; vollständiger Primärquellenabruf offen. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 462: `format: ok`.

## 463 – [nix_env.md](../nix_env.md)

- Inhalt: Klassische Nix-Profile und Store unterscheiden. nix-env verwaltet klassische Nix-Benutzerumgebungen. Ein Profil ist eine Sicht auf Storepfade; im Store vorhandene Software und im aktuellen Profil verfügbare Software sind verschiedene Mengen.
- Gelesene Primärquelle: [Nix-Projekt: nix-env](https://nix.dev/manual/nix/latest/command-ref/nix-env.html) und [query](https://nix.dev/manual/nix/latest/command-ref/nix-env/query)
- Lokaler Stand: Nicht praktisch geprüft; nix-env fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 463: `format: ok`.

## 464 – [npm.md](../npm.md)

- Inhalt: Eigene package.json ohne Installation auslesen. npm verwaltet JavaScript-Pakete und führt Projektskripte aus. npm pkg get liest gezielt lokale Manifestfelder. npm view fragt dagegen Registrymetadaten ab und ist nicht dieselbe Informationsquelle.
- Gelesene Primärquelle: [npm-Projekt: pkg](https://docs.npmjs.com/cli/v11/commands/npm-pkg/) und [Lifecycle-Skripte v10](https://docs.npmjs.com/cli/v10/using-npm/scripts/)
- Lokaler Stand: npm 10.9.9. Praktisch geprüft: Eigene package.json mit pkg get offline gelesen; JSON-Felder geprüft. Installation, Lifecycle-Skripte, Registry, Audit, Workspaces und Veröffentlichung praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 464: `format: ok`.

- Ergänzender Testbefund 464: Der erste npm-Aufruf mit zweimal `/dev/null` als user/global-Konfigurationsdatei brach vor der Auswertung wegen doppeltem Konfigurationspfad ab. Das veröffentlichte Beispiel verwendet zwei getrennte eigene leere Konfigurationsdateien; der erneute Lauf war erfolgreich. Keine Installation oder Registryabfrage in beiden Läufen.
- Offene Quellenprüfung 462: Offizielle Guix-HTML-/PDF-Vollabrufe scheiterten (403 beziehungsweise nicht zugänglich). Gelesen wurden ausdrücklich nur die vom Suchindex bereitgestellten Auszüge der offiziellen Handbücher; der vollständige aktuelle Handbuchabgleich bleibt offen.

## 465 – [pacman.md](../pacman.md)

- Inhalt: Pacman-Operation vor den Kurzoptionen lesen. pacman ist Archs libalpm-basierte Paketverwaltung. Großgeschriebene Operationsoptionen wie -Q, -S und -R bestimmen zuerst den Modus; nachfolgende Kleinbuchstaben haben darin unterschiedliche Bedeutungen.
- Gelesene Primärquelle: [Arch/Pacman: Projekthandbuch](https://man.archlinux.org/man/pacman.8.en)
- Lokaler Stand: Nicht praktisch geprüft; pacman fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 465: `format: ok`.

## 466 – [pamac.md](../pamac.md)

- Inhalt: Pamac-CLI von Oberfläche und AUR-Build trennen. pamac ist die Kommandozeilenoberfläche zu libpamac. pamac-manager ist die grafische Oberfläche. Unterstützte zusätzliche Paketquellen hängen vom Build und der Konfiguration ab.
- Gelesene Primärquelle: [Manjaro: Projektbeschreibung](https://raw.githubusercontent.com/manjaro/pamac/master/README.md) und [pamac-cli: originaler Parser/Hilfetexte](https://raw.githubusercontent.com/manjaro/pamac-cli/master/src/cli.vala)
- Lokaler Stand: Nicht praktisch geprüft; pamac fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 466: `format: ok`.

## 467 – [paru.md](../paru.md)

- Inhalt: AUR-Helfer mit gefährlicher argumentloser Vorgabe. paru ist ein AUR-Helfer und pacman-Wrapper. Laut Projektmanual bedeutet ein Aufruf ohne Argumente paru -Syu und damit einen Aktualisierungsauftrag, keine harmlose Übersicht.
- Gelesene Primärquelle: [Paru-Projekt: originale Manpage](https://raw.githubusercontent.com/Morganamilo/paru/master/man/paru.8)
- Lokaler Stand: Nicht praktisch geprüft; paru fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 467: `format: ok`.

## 468 – [pip.md](../pip.md)

- Inhalt: Eigene Datei hashen statt Pakete installieren. pip verwaltet Python-Distributionen für einen bestimmten Interpreter. Der Aufrufname allein beweist nicht, welche Python-Umgebung gemeint ist. Die Übung nutzt nur pip hash für eine eigene kleine Datei.
- Gelesene Primärquelle: [PyPA: pip](https://pip.pypa.io/en/stable/cli/pip/), [hash](https://pip.pypa.io/en/stable/cli/pip_hash/) und [install](https://pip.pypa.io/en/stable/cli/pip_install/)
- Lokaler Stand: pip 24.0, Python 3.12. Praktisch geprüft: Eigene Drei-Byte-Datei mit pip hash gehasht. Installation, Buildbackends, Resolver, echte Paketbestände und Index-/Netzverhalten praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 468: `format: ok`.

## 469 – [pip3.md](../pip3.md)

- Inhalt: Python3-Bindung des Aufrufnamens prüfen. pip3 ist gewöhnlich ein Starter für pip unter Python3. Er garantiert weder die gewünschte Python-Minorversion noch ein bestimmtes venv. Hier meldet er pip 24.0 für Python 3.12.
- Gelesene Primärquelle: [PyPA: pip-Aufruf](https://pip.pypa.io/en/stable/cli/pip/), [hash](https://pip.pypa.io/en/stable/cli/pip_hash/) und [install](https://pip.pypa.io/en/stable/cli/pip_install/)
- Lokaler Stand: pip3: pip 24.0, Python 3.12. Praktisch geprüft: Eigene Drei-Byte-Datei mit pip3 hash gelesen; Digest und lokale Versionsbindung geprüft. Andere Interpreter, Installation, Buildcode und echte Paketumgebungen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 469: `format: ok`.

## 470 – [pipx.md](../pipx.md)

- Inhalt: Python-CLI-Pakete getrennt von Projektbibliotheken. pipx installiert Python-Anwendungen in eigenen virtuellen Umgebungen und stellt deren Startbefehle bereit. Diese Paketpfadtrennung ist keine Betriebssystemsandbox für ausgeführten Anwendungscode.
- Gelesene Primärquelle: [PyPA/pipx: Übersicht](https://pipx.pypa.io/stable/) und [CLI-Referenz](https://pipx.pypa.io/stable/reference/cli.html)
- Lokaler Stand: Nicht praktisch geprüft; pipx fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 470: `format: ok`.

## 471 – [pnpm.md](../pnpm.md)

- Inhalt: Ein eigenes Projekt ohne Abhängigkeiten anzeigen. pnpm verwaltet JavaScript-Projekte mit eigenem Store-/Verlinkungsmodell. list zeigt einen Abhängigkeitsbestand; es ist vom installierenden Standardaufruf und von einem Lockfilebericht zu unterscheiden.
- Gelesene Primärquelle: [pnpm: list](https://pnpm.io/cli/list) und [install](https://pnpm.io/cli/install)
- Lokaler Stand: pnpm 11.25.0. Praktisch geprüft: Eigene Projektanzeige ohne Abhängigkeiten offline ausgeführt. Storeverlinkung, Installationsskripte, Registry, Workspaces und aktuelle v12-Funktionen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 471: `format: ok`.

## 472 – [rpm.md](../rpm.md)

- Inhalt: RPM-Abfrage, Verifikation und Installation auseinanderhalten. rpm arbeitet mit RPM-Paketarchiven und der installierten RPM-Datenbank. Es löst nicht wie dnf oder zypper automatisch Repositoryabhängigkeiten. Die Operation bestimmt die Bedeutung nachfolgender Optionen.
- Gelesene Primärquelle: [RPM-Projekt: rpm-Handbuch](https://rpm.org/docs/6.0.x/man/rpm.8) und lokale rpm-Manpage
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 472: `format: ok`.

- Ergänzender Testbefund 471: pnpm 11.25.0 lehnte `--offline --ignore-pnpmfile` bei `list` als CLI-Optionen ab (Status 1). Das geprüfte Beispiel nutzt die entsprechenden prozessbezogenen Konfigurationsvariablen statt dieser dort unzulässigen Argumente. Die eigene Projektanzeige lief danach mit Status 0; keine Installation/Registryabfrage.

## 473 – [snap.md](../snap.md)

- Inhalt: Snap-Revision, Kanal und Dienstzustand unterscheiden. snap ist die CLI des snapd-Systems. Sie verwaltet Apps und gegebenenfalls Dienste. list zeigt Installiertes, find sucht im Store; beide Datenquellen sind zu unterscheiden.
- Gelesene Primärquelle: [Canonical: Einstieg](https://snapcraft.io/docs/tutorials/get-started/) und [Aktualisierungen](https://snapcraft.io/docs/how-to-guides/manage-snaps/manage-updates/)
- Lokaler Stand: Nicht praktisch geprüft; snap fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 473: `format: ok`.

## 474 – [yarn.md](../yarn.md)

- Inhalt: Yarn Classic und moderne Yarn-Versionen nicht mischen. yarn ist eine JavaScript-Projektverwaltung mit mehreren deutlich verschiedenen CLI-Generationen. Yarn 1 Classic und moderne Yarn-Versionen haben unterschiedliche Befehle, Konfigurationen und Installationsmodelle.
- Gelesene Primärquelle: [Yarn: aktuelles install-Handbuch](https://yarnpkg.com/cli/install) und [Yarn Classic: list](https://classic.yarnpkg.com/en/docs/cli/list)
- Lokaler Stand: Nicht praktisch geprüft; yarn fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 474: `format: ok`.

## 475 – [yay.md](../yay.md)

- Inhalt: Yay-Standardaktion und AUR-Ausführung erkennen. yay ist ein pacman-Wrapper mit AUR-Unterstützung. Ein Aufruf ohne Operation und Ziel entspricht laut Projektmanual -Syu. Er ist deshalb kein harmloser Verfügbarkeitstest.
- Gelesene Primärquelle: [Yay-Projekt: originale Manpage im next-Zweig](https://raw.githubusercontent.com/Jguer/yay/next/doc/yay.8)
- Lokaler Stand: Nicht praktisch geprüft; yay fehlt; Quelle Entwicklungszweig v13.0+. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 475: `format: ok`.

## 476 – [yum.md](../yum.md)

- Inhalt: Historisches Yum und aktuelle Kompatibilitätsnamen trennen. yum ist historisch ein Repository- und Abhängigkeitsmanager für RPM-Pakete. Auf neueren Distributionen kann der Aufruf auf DNF-Technik verweisen. Die tatsächlich installierte Variante ist vor Optionsübernahme zu klären.
- Gelesene Primärquelle: [Yum-Projekt: originale yum-Manpage](https://raw.githubusercontent.com/rpm-software-management/yum/master/docs/yum.8)
- Lokaler Stand: Nicht praktisch geprüft; yum fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 476: `format: ok`.

## 477 – [zypper.md](../zypper.md)

- Inhalt: ZYpp-Objekte und automatische Metadatenzugriffe verstehen. zypper ist die CLI zu libzypp. Sie verwaltet Pakete, Patches, Patterns und Quellen. Ein Such-/Informationsauftrag kann je nach Refreshkonfiguration bereits Netz- und Cachezugriffe verursachen.
- Gelesene Primärquelle: [openSUSE/libzypp: zypper-Handbuch](https://manpages.opensuse.org/Tumbleweed/zypper/zypper.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; zypper fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 477: `format: ok`.

## 478 – [atop.md](../atop.md)

- Inhalt: Messintervalle und historische Aufzeichnungen unterscheiden. atop zeigt System- und Prozessressourcen über Messintervalle und kann Rohprotokolle aufzeichnen oder wiedergeben. Ein Monitorstart ist nicht unter allen Rechten und Konfigurationen nebenwirkungsfrei.
- Gelesene Primärquelle: [atop-Projekt: Handbuch](https://manpages.debian.org/trixie/atop/atop.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; atop fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 478: `format: ok`.

## 479 – [bg.md](../bg.md)

- Inhalt: Gestoppten Shelljob im Hintergrund fortsetzen. bg ist hier das Bash-Builtin für Jobsteuerung, kein systemweiter Prozessmanager. Es setzt einen vorhandenen gestoppten Job derselben Shell im Hintergrund fort.
- Gelesene Primärquelle: Lokale Primärquelle: Bash 5.2.21, `help bg`; [Bash: Job-Control-Builtins](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) (Webabruf scheiterte; lokale Hilfe gelesen)
- Lokaler Stand: Bash 5.2.21; lokale help-Ausgabe gelesen, Jobsteuerung nicht praktisch ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 479: `format: ok`.

## 480 – [btop.md](../btop.md)

- Inhalt: Ressourcenansicht mit interaktiven Eingriffen. btop ist ein interaktiver Monitor für CPU, Speicher, Datenträger, Netzwerk und Prozesse. Er kann auch Signale senden und Einstellungen speichern; der Name Monitor macht nicht jede Bedienung lesend.
- Gelesene Primärquelle: [btop: originale Manpage](https://raw.githubusercontent.com/aristocratos/btop/main/manpage.md) und [Projektbeschreibung](https://github.com/aristocratos/btop)
- Lokaler Stand: Nicht praktisch geprüft; btop fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 480: `format: ok`.

## 481 – [chrt.md](../chrt.md)

- Inhalt: Schedulingattribute der eigenen Test-Shell nur lesen. chrt liest oder verändert Schedulerpolicy und Priorität eines Tasks. Mit --pid und ausschließlich einer PID werden Attribute angezeigt. Ein zusätzlicher Prioritätsoperand kann daraus einen Änderungsauftrag machen.
- Gelesene Primärquelle: [util-linux: chrt-Handbuch](https://man7.org/linux/man-pages/man1/chrt.1.html)
- Lokaler Stand: chrt / util-linux 2.39.3. Praktisch geprüft: Nur chrt --pid auf der eigenen Test-Shell ausgeführt. Keine Attribute geändert. Echtzeit-, Mehrthread-, Berechtigungs- und neuere Versionsfunktionen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 481: `format: ok`.

## 482 – [disown.md](../disown.md)

- Inhalt: Jobtabelle und HUP-Behandlung gezielt ändern. disown ist hier das Bash-Builtin. Es entfernt ausgewählte Jobs aus der Jobtabelle oder markiert sie mit -h gegen eine bestimmte SIGHUP-Weitergabe der Shell. Es startet keinen Dienst.
- Gelesene Primärquelle: Lokale Primärquelle: Bash 5.2.21, `help disown`; [Bash-Jobsteuerung](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis
- Lokaler Stand: Bash 5.2.21; Hilfe gelesen, keine Jobentkopplung praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 482: `format: ok`.

## 483 – [fg.md](../fg.md)

- Inhalt: Shelljob in den Vordergrund holen. fg ist das Bash-Builtin für einen Job der aktuellen Shell. Es macht den gewählten Job zum Vordergrundjob und setzt einen gestoppten Job fort. Es ist kein Startbefehl für eine beliebige PID.
- Gelesene Primärquelle: Lokale Primärquelle: Bash 5.2.21, `help fg`; [Bash-Jobsteuerung](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis
- Lokaler Stand: Bash 5.2.21; Hilfe gelesen, interaktives fg praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 483: `format: ok`.

## 484 – [fuser.md](../fuser.md)

- Inhalt: Zugriff auf eine eigene geöffnete Datei anzeigen. fuser ordnet Dateien oder ausgewählten Socketnamensräumen zugreifende Prozesse zu. Ohne -k wird angezeigt; -k sendet standardmäßig SIGKILL. Die Operationsoption ist deshalb entscheidend.
- Gelesene Primärquelle: [psmisc: fuser-Handbuch](https://man7.org/linux/man-pages/man1/fuser.1.html)
- Lokaler Stand: fuser / PSmisc 23.7. Praktisch geprüft: Eigene geöffnete Datei abgefragt und Shell-PID geprüft; keine Signale. Sandbox-Netzsocketwarnung beobachtet. Fremdprozesssicht, Socket-/Mountmodus und Signalfunktionen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 484: `format: ok`.

## 485 – [glances.md](../glances.md)

- Inhalt: Monitoringmodus und Datenweitergabe ausdrücklich wählen. glances ist ein erweiterbarer Ressourcenmonitor mit Terminal-, Server-, Web- und Exportmodi. Ein Start kann daher Daten sammeln, speichern oder über einen Listener anbieten.
- Gelesene Primärquelle: [Glances-Projekt: Kommandoreferenz](https://glances.readthedocs.io/en/latest/cmds.html)
- Lokaler Stand: Nicht praktisch geprüft; glances fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 485: `format: ok`.

- Ergänzender Testbefund 484: Lokales fuser 23.7 akzeptierte die versuchte `--`-Trennform nicht und meldete Status 1. Das veröffentlichte Beispiel nutzt den absoluten eigenen Dateipfad direkt; damit wurden Status 0 und die eigene Shell-PID erreicht. Die Sandbox-Netzsocketwarnungen blieben sichtbar. Kein Signal-/Mount-/Socketmodus und keine Rechteerhöhung.

## 486 – [htop.md](../htop.md)

- Inhalt: Prozessansicht mit ausdrücklich begrenzter Bedienung. htop ist eine interaktive Prozessansicht. Neben Anzeigen kann es Signale senden und Prioritäten ändern. Markierte Prozesse können gemeinsam Ziel einer Aktion werden.
- Gelesene Primärquelle: [htop-Projekt: Manpage](https://manpages.debian.org/trixie/htop/htop.1.en.html) und lokale htop-Hilfe
- Lokaler Stand: Lokale Hilfe gelesen; keine Monitorfunktion praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 486: `format: ok`.

## 487 – [iftop.md](../iftop.md)

- Inhalt: Interfaceverkehr nach Hostpaaren messen. iftop erfasst Pakete auf einem Interface und stellt Datenraten nach Hostpaaren dar. Es ordnet Verkehr nicht automatisch lokalen Prozessen zu. Live-Erfassung benötigt passende Capture-Rechte.
- Gelesene Primärquelle: [iftop-Projekt: Manpage](https://manpages.debian.org/trixie/iftop/iftop.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 487: `format: ok`.

## 488 – [ionice.md](../ionice.md)

- Inhalt: I/O-Priorität der eigenen Shell nur lesen. ionice zeigt und setzt I/O-Schedulingklasse und -Priorität. Die reine Form -p PID ohne neue Klasse oder Prioritätsstufe liest Attribute; ein Programmoperand startet dagegen ein Programm.
- Gelesene Primärquelle: [util-linux: ionice-Handbuch](https://man7.org/linux/man-pages/man1/ionice.1.html)
- Lokaler Stand: ionice / util-linux 2.39.3. Praktisch geprüft: Nur ionice -p auf eigener Test-Shell ausgeführt. Keine Klasse oder Priorität geändert. I/O-Schedulerwirkung, Last-, Geräte- und Rechtefälle praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 488: `format: ok`.

## 489 – [iotop.md](../iotop.md)

- Inhalt: I/O-Zähler nicht mit sofortigem Gerätetransfer verwechseln. iotop zeigt prozess-/threadbezogene I/O-Messwerte. Hier ist die Python-iotop-Variante des gelesenen Handbuchs beschrieben; iotop-c kann unter demselben Namen eine andere Oberfläche liefern.
- Gelesene Primärquelle: [iotop-Projekt: Manpage der Python-Variante](https://manpages.debian.org/trixie/iotop/iotop.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; iotop fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 489: `format: ok`.

## 490 – [jobs.md](../jobs.md)

- Inhalt: Nur die Jobtabelle der eigenen Shell anzeigen. jobs ist hier das Bash-Builtin zur Anzeige der Jobtabelle dieser Shell. Es zeigt keine vollständige systemweite Prozessliste. jobs -x kann zusätzlich ein Kommando ausführen und ist deshalb gesondert zu behandeln.
- Gelesene Primärquelle: Lokale Primärquelle: Bash 5.2.21, `help jobs`; [Bash-Projekthandbuch](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener einsekündiger Hintergrundjob mit jobs -l/-p angezeigt und normal abgewartet. Keine Signale. Interaktive Jobsteuerung, Pipelines und andere Shells praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 490: `format: ok`.

## 491 – [kill.md](../kill.md)

- Inhalt: Signalprüfung von tatsächlichem Signalisieren trennen. kill sendet Signale; es bedeutet nicht immer sofortiges Beenden. Hier wird das Bash-Builtin verwendet. Externe Programme gleichen Namens können zusätzliche Optionen besitzen.
- Gelesene Primärquelle: Lokale Primärquelle: Bash 5.2.21, `help kill`; [util-linux: kill zur Implementierungsabgrenzung](https://man7.org/linux/man-pages/man1/kill.1.html)
- Lokaler Stand: Bash 5.2.21 Builtin. Praktisch geprüft: Signalnamensumsetzung und Nullsignalprüfung nur auf eigene Test-Shell ausgeführt. Keine echten Signale, Handler-, Beendigungs-, Gruppen- oder Rechtefälle geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 491: `format: ok`.

## 492 – [killall.md](../killall.md)

- Inhalt: Namensauswahl kann viele Prozesse treffen. killall aus Linux-psmisc signalisiert passende Prozesse nach Kommandonamen. Es bedeutet nicht kontrolliertes Beenden genau einer Anwendung. Andere Betriebssysteme können unter diesem Namen deutlich andere Programme anbieten.
- Gelesene Primärquelle: [psmisc: killall-Manpage](https://manpages.debian.org/trixie/psmisc/killall.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 492: `format: ok`.

## 493 – [lsof.md](../lsof.md)

- Inhalt: Eigene PID und eigenen Dateideskriptor gemeinsam auswählen. lsof zeigt offene Dateireferenzen einschließlich Sockets, Verzeichnissen und Mappings. Mehrere Auswahlarten werden oft mit ODER verknüpft; -a fordert deren UND-Verknüpfung an.
- Gelesene Primärquelle: [lsof-Projekt: Manpage](https://man7.org/linux/man-pages/man8/lsof.8.html) und lokale Versionsausgabe
- Lokaler Stand: lsof 4.95.0. Praktisch geprüft: Eigene Shell und eigener offener Deskriptor 9 mit UND-Auswahl geprüft. Keine fremden Dateien/Prozesse. Netzsockets, rekursive Pfade, gelöschte Dateien und Rechtefälle praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 493: `format: ok`.

## 494 – [ltrace.md](../ltrace.md)

- Inhalt: Bibliotheksaufrufe beobachten heißt Programm ausführen. ltrace startet ein Programm unter Beobachtung oder hängt sich an einen vorhandenen Prozess. Es protokolliert dynamische Bibliotheksaufrufe und gegebenenfalls Systemaufrufe. Das Zielprogramm läuft dabei tatsächlich.
- Gelesene Primärquelle: [ltrace-Projekt: Manpage](https://man7.org/linux/man-pages/man1/ltrace.1.html)
- Lokaler Stand: Nicht praktisch geprüft; ltrace fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 494: `format: ok`.

## 495 – [nethogs.md](../nethogs.md)

- Inhalt: Erfassten Verkehr Prozessen zuordnen mit Sichtgrenzen. nethogs erfasst Netzwerkverkehr und versucht ihn Prozessen zuzuordnen. Es benötigt Capture- und Prozesssichtrechte; ein PID-Filter macht daraus keine ausschließlich lokale Dateiabfrage.
- Gelesene Primärquelle: [NetHogs-Projekt: Manpage](https://manpages.debian.org/trixie/nethogs/nethogs.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; nethogs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 495: `format: ok`.

## 496 – [nice.md](../nice.md)

- Inhalt: Aktuellen Nice-Wert ohne Anpassung auslesen. GNU nice startet normalerweise ein Programm mit angepasster Niceness. Ohne Programmoperand gibt es nur die aktuelle Niceness aus. Diese reine Anzeige wird hier geprüft.
- Gelesene Primärquelle: Lokale Primärquelle: GNU-coreutils-Manpage nice; [Projektverweis nice](https://www.gnu.org/software/coreutils/nice) (Online-Vollabruf nicht verfügbar)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur Version und nice ohne Programmoperand ausgeführt, Wert gelesen. Keine Niceness gesetzt. Lastwirkung, negative Anpassung, Rechte und andere Implementierungen praktisch offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 496: `format: ok`.

## 497 – [nohup.md](../nohup.md)

- Inhalt: Ein eigenes kurzes Kommando mit expliziten Umleitungen. GNU nohup startet ein Kommando mit ignoriertem SIGHUP. Es versetzt es nicht automatisch in den Hintergrund und ist kein Dienstmanager oder Wiederanlaufmechanismus.
- Gelesene Primärquelle: Lokale Primärquelle: GNU-coreutils-Manpage nohup; [Projektverweis nohup](https://www.gnu.org/software/coreutils/nohup) (Online-Vollabruf nicht verfügbar)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Eigenes printf mit expliziten Kanälen ausgeführt; Ausgabetext und fehlende nohup.out geprüft. Kein HUP gesendet, keine Sitzung beendet. Logout-, Langzeit- und andere Implementierungsfälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 497: `format: ok`.

## 498 – [perf.md](../perf.md)

- Inhalt: Performancewerkzeuge mit versions- und rechteabhängiger Messung. perf ist eine Familie von Linux-Analysewerkzeugen. Unterbefehle wie stat, record und report haben verschiedene Datenquellen und Nebenwirkungen. Das vorhandene /usr/bin/perf ist lokal zunächst ein Distributionsstarter.
- Gelesene Primärquelle: [Linux/perf: Übersicht](https://man7.org/linux/man-pages/man1/perf.1.html), [stat](https://man7.org/linux/man-pages/man1/perf-stat.1.html) und lokal gelesener Starter /usr/bin/perf
- Lokaler Stand: Kein Messlauf; Starterdatei gelesen, keine ausgeführte perf-Version ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 498: `format: ok`.

## 499 – [pgrep.md](../pgrep.md)

- Inhalt: Nur eigene direkte Kindprozesse auswählen. pgrep aus procps-ng sucht Prozesse anhand von Namen und weiteren Kriterien und gibt PIDs aus. Es signalisiert sie nicht. pkill ist die verwandte, aber signalgebende Oberfläche.
- Gelesene Primärquelle: [procps-ng: pgrep-Handbuch](https://man7.org/linux/man-pages/man1/pgrep.1.html)
- Lokaler Stand: pgrep / procps-ng 4.0.4. Praktisch geprüft: Eigener zweisekündiger sleep als direktes Kind ausgewählt, PID verglichen und normales Ende abgewartet. Keine Signale. Namens-/Thread-/Namespace- und fremde Rechtefälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 499: `format: ok`.

## 500 – [pidof.md](../pidof.md)

- Inhalt: Eigenes Programm über seinen absoluten Pfad finden. pidof sucht PIDs benannter laufender Programme. Sysvinit und procps-ng stellen unterschiedliche Varianten bereit. Die lokale Manpage beschreibt die Sysvinit-Variante; zusätzliche procps-Optionen werden nicht ungeprüft übernommen.
- Gelesene Primärquelle: Lokale Primärquelle: Sysvinit-pidof-Manpage; [Sysvinit/Debian: pidof](https://manpages.debian.org/bookworm/sysvinit-utils/pidof.8.en.html) und [procps-ng-Variante zum Vergleich](https://man7.org/linux/man-pages/man1/pidof.1.html)
- Lokaler Stand: Lokale Sysvinit-Variante laut Manpage; Versionsnummer nicht gesondert ermittelt. Praktisch geprüft: Nur eigene kurzlebige Programmkopie per absolutem Pfad gefunden und PID verglichen, normal abgewartet. Keine Signale. Mehrinstanz-, Skript-, Namespace- und Variantenfälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 500: `format: ok`.

## Abschlussprüfung und Übergabe 401–500

Der Nutzer stoppte nach 485 ausdrücklich; die Arbeit pausierte sofort ohne Commit oder Push. Nach „ok kannst wieder weitermachen“ wurden 486–500 einzeln in aufsteigender Reihenfolge ergänzt. Nach 500 keine weiteren Datensätze bearbeitet.

- **Zuordnung und Struktur:** 100/100 Dokumente 401–500 erfolgreich mit der unveränderten Funktion `check_document` und dem tatsächlichen NetMon-Markdownparser geprüft. Nummern lückenlos und aufsteigend im Einzelbericht; Kennung, Name, Kategorie und Dateiname stimmen mit der obigen festen Tabelle überein. Alle 100 Originalfelder entsprechen weiterhin ihren CSV-Zeilen; 713 Gesamtzeilen und der oben genannte CSV-SHA-256 bestätigt. Keine CSV-/Index-/Katalog-/Prüfcodeänderung.
- **Shellsyntax:** Alle 17 Bashblöcke mit `bash -n` erfolgreich geprüft. Nicht ausgeführte Erklärungsmuster stehen ausdrücklich in Textblöcken und wurden nicht automatisch gestartet.
- **Vorhandene Tests:** `python3 -m pytest -q tests/test_linux_command_docs_handoff.py`: **31 passed**. Der bestehende CLI-Prüfer für den unveränderten Bereich 201–300 ebenfalls **100/100 format: ok**. Diese Nachweise prüfen Parser, Herkunft, Zuordnung und Struktur; keine GUI-, Netz-, Geräte- oder vollständige Anwendungsfreigabe.
- **Praktische Beispiele:** 17 eng begrenzte Funktionsfälle ausgeführt: 437, 457, 458, 464, 468, 469, 471, 481, 484, 488, 490, 491, 493, 496, 497, 499, 500. Inhalt je Einzelbericht: eigene Text-/Statusdateien, Hash-/Versionsvergleich, eigene PID/Deskriptoranzeige, kurzlebige eigene Kinder oder eigenes printf. Keine echten Signale; Nullsignalprüfung 491 sendet ausdrücklich kein Signal. Keine Prioritäten gesetzt. Diese 17 Fälle sind keine Vollprüfung aller Modi des jeweiligen Befehls.
- **Nur Hilfe/Version als Ausführung:** 413 und 461. Weitere lokale Hilfe-/Manpagelektüre steht in den Einzeleinträgen; sie zählt nicht als ausgeführtes Funktionsbeispiel. Für 81 Dokumente wurde kein Funktionsbeispiel ausgeführt.
- **Korrigierte Prüfprobleme:** Die oben dokumentierten npm-, pnpm- und fuser-Aufrufe wurden nach ihren ersten Fehlversuchen in der veröffentlichten Form erfolgreich geprüft. Bei 488 erkannte der echte Parser eine Tabellenzelle mit ungeschützten senkrechten Strichen; die Zelle wurde eindeutig als `-c KLASSE` formuliert und die Einzelprüfung danach bestanden.
- **Warnungen:** fuser meldete fehlende Netzsocketfunktion in der Sandbox; der eigene Dateideskriptortest war trotzdem erfolgreich. lsof 493 meldete fehlgeschlagene stat-Abfragen für `/dev/hugepages` und `/dev/mqueue` und möglicherweise unvollständige Sicht. Die eigene Datei/FD 9 wurde gefunden; keine allgemeine Vollständigkeit behauptet. htop-Hilfe weist lokal 3.3.0 aus, kein Monitorstart.

### Offene fachliche und praktische Prüfpunkte

Guix 462: Der vollständige aktuelle offizielle Handbuchabruf blieb gesperrt (403/nicht erreichbar); nur ausdrücklich benannte Suchindex-Auszüge offizieller GNU-Handbücher wurden gelesen. Vollständiger Abgleich bleibt offen und im Dokumentstatus markiert. Bei Bash-Builtins sowie nice/nohup bilden tatsächlich gelesene lokale Primärhilfen/-manpages die Grundlage, wenn der Webabruf scheiterte.

Nicht durchgeführt: aktive Netzproben, Scans, Mitschnitte, Listener-/Daemonstarts, Funk-/Geräteaktionen, echte Benutzer-/Systemänderungen, Installationen/Downloads als Beispieldurchlauf, privilegierte Reparaturen, Kernel-/Capabilityänderungen, echte Signale/Jobsteuerung an Benutzersitzungen, Echtzeit-/I/O-Prioritätsänderungen und Logouttests. Fehlende Programme wurden nicht nachinstalliert. Historische oder andere Implementierungen sind jeweils benannt, etwa iperf2/3, iputils arping, speedtest-cli/Ookla, Wireless Extensions/nl80211, systemd-resolve/resolvectl, DNF4/5, Yarn Classic/modern und Sysvinit/procps pidof. Neue Optionen und ihre Wirkungen sind außerhalb der konkret geprüften Version nicht praktisch zugesichert.

### Reproduzierbare Zuordnungs-/Strukturprüfung ohne Codeänderung

Die Tabelle dieses Berichts ist die im Repository mitgelieferte feste Zuordnung für 401–500. Folgender Aufruf nutzt diese Tabelle und die Original-CSV direkt; er braucht den temporären Hilfssnapshot nicht und führt keine Beispiele aus:

```bash
python3 - <<'PY_REVIEW'
import csv, hashlib, io, re
from pathlib import Path
from scripts.check_linux_command_docs import BASE, check_document
report = (BASE / "browser-codex/FORTSCHRITT-CODEX-401-500.md").read_text()
raw = Path("tools/netmon-linux-befehlsdatenbank-v1.csv").read_bytes()
assert hashlib.sha256(raw).hexdigest() == "40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887"
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
assert len(rows) == 713
mapping = re.findall(r"^\| (4[0-9]{2}|500) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", report, re.M)
assert [int(m[0]) for m in mapping] == list(range(401, 501))
for number, ident, name, category, filename in mapping:
    record = dict(source_record=int(number), id=ident, name=name, category=category)
    assert rows[int(number)-1]["Befehl"] == name
    assert rows[int(number)-1]["Kategorie"] == category
    check_document(BASE / filename, record, {"source_catalog": "tools/netmon-linux-befehlsdatenbank-v1.csv"})
print("401–500: 100/100 Zuordnung und Struktur OK")
PY_REVIEW
```

### Veröffentlichungsumfang

Ausschließlich die 100 neuen Dokumente 401–500 und dieser Fortschrittsbericht: **101 Dateien**. Vor Veröffentlichung wird die exakte Pfadliste geprüft und explizit gestaged. Keine älteren Dokumente/Berichte, fremden Änderungen, zentralen Indizes, Code-, Test-, Katalog- oder Packagingdateien. Commit/Push folgen dem fortgesetzten Nutzerauftrag auf `codex/linux-docs-browser-handoff-20261113`; kein Merge nach main. Commit-ID und bestätigter Remote-Stand werden außerhalb dieses selbst enthaltenen Berichts in der Übergabe genannt. Die gemeinsame fachliche Review bleibt offen.
