# Ausarbeitung und Prüfung 601–713

Basis: Branch `codex/linux-docs-browser-handoff-20261113`, Commit `2574ea5194c949ca1d5b50284ab0d6063b3c519e`. Datum 2026-11-13. Einzeln aufsteigend bearbeiten, nach 713 stoppen. Keine Unteragenten. Separate Arbeitskopie `/tmp/linux-docs-601-713-20261113`; Hauptarbeitsbaum und fremde Änderungen bleiben unberührt.

Veröffentlichungsumfang nach lokaler Prüfung: ausschließlich die 113 neuen Dokumente und dieser eigene Bericht auf demselben Branch. Die zugehörige Commit-ID steht im Git-Protokoll und in der Rückmeldung.  Keine Änderungen an Code, Tests, zentralem Index, bestehenden Dokumenten, Original-CSV, bestehendem Katalog oder main.

Für diesen Bereich existiert kein separater veröffentlichter Teilkatalog. Die folgende feste Zuordnung stammt aus den Zuordnungsfeldern des vollständigen lokalen Index (SHA-256 `241242a539e293a95edb54d5be1d471e06cc0cd48ab3411256e508482e1fbd23`) und wurde gegen die Original-CSV geprüft. CSV: 713 Datensätze, SHA-256 `40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`. Alle Originalfelder des temporären Prüfsnapshots stammen direkt aus der unveränderten CSV. Besonderheit 662: Im lokalen Index wich das Beispiel durch zusätzliche Anführungszeichen ab; die CSV ist maßgeblich. Keine Korrektur am fremden Index.

Die unveränderte CLI-Prüfung beschränkt sich auf 201–300. Hier wird dieselbe Funktion `check_document` direkt mit der unten festgehaltenen Zuordnung aufgerufen: tatsächlicher Markdownparser, Metadaten und zehn Hauptabschnitte. Einzelprüfung nach jedem Dokument, Gesamtprüfung am Ende; keine Prüfcodeänderung.

Tests nur mit kleinen eigenen Dateien im neuen privaten Temporärordner, mktemp-Fehler bricht ab. Keine realen Geräte-, Netz-, Konten-, Dienst- oder Systemänderungen, keine fremden Dateien, Paketinstallationen, Hypervisoraktionen oder Live-Mitschnitte. Offizielle Quellenrecherche ist getrennt von Beispieltests. Hilfe/Version ist kein Funktionsnachweis. Fachliche Freigabe und reale Betriebsfälle bleiben getrennt vom Strukturtest.

## Feste Zuordnung

| Nr. | Kennung | Name | Kategorie | Datei |
| --- | --- | --- | --- | --- |
| 601 | lastb | lastb | Systeminformationen | lastb.md |
| 602 | lastlog | lastlog | Systeminformationen | lastlog.md |
| 603 | locale | locale | Systeminformationen | locale.md |
| 604 | localectl | localectl | Systeminformationen | localectl.md |
| 605 | loginctl | loginctl | Systeminformationen | loginctl.md |
| 606 | lsipc | lsipc | Systeminformationen | lsipc.md |
| 607 | lslogins | lslogins | Systeminformationen | lslogins.md |
| 608 | lsmod | lsmod | Systeminformationen | lsmod.md |
| 609 | lsns | lsns | Systeminformationen | lsns.md |
| 610 | modinfo | modinfo | Systeminformationen | modinfo.md |
| 611 | modprobe | modprobe | Systeminformationen | modprobe.md |
| 612 | mpstat | mpstat | Systeminformationen | mpstat.md |
| 613 | nsenter | nsenter | Systeminformationen | nsenter.md |
| 614 | sar | sar | Systeminformationen | sar.md |
| 615 | sysctl | sysctl | Systeminformationen | sysctl.md |
| 616 | systemd_analyze | systemd-analyze | Systeminformationen | systemd_analyze.md |
| 617 | timedatectl | timedatectl | Systeminformationen | timedatectl.md |
| 618 | vmstat | vmstat | Systeminformationen | vmstat.md |
| 619 | w | w | Systeminformationen | w.md |
| 620 | who | who | Systeminformationen | who.md |
| 621 | bat | bat | Text anzeigen | bat.md |
| 622 | cat | cat | Text anzeigen | cat.md |
| 623 | column | column | Text anzeigen | column.md |
| 624 | expand | expand | Text anzeigen | expand.md |
| 625 | fmt | fmt | Text anzeigen | fmt.md |
| 626 | fold | fold | Text anzeigen | fold.md |
| 627 | head | head | Text anzeigen | head.md |
| 628 | hexdump | hexdump | Text anzeigen | hexdump.md |
| 629 | less | less | Text anzeigen | less.md |
| 630 | more | more | Text anzeigen | more.md |
| 631 | nl | nl | Text anzeigen | nl.md |
| 632 | od | od | Text anzeigen | od.md |
| 633 | rev | rev | Text anzeigen | rev.md |
| 634 | script | script | Text anzeigen | script.md |
| 635 | scriptreplay | scriptreplay | Text anzeigen | scriptreplay.md |
| 636 | strings | strings | Text anzeigen | strings.md |
| 637 | tac | tac | Text anzeigen | tac.md |
| 638 | tail | tail | Text anzeigen | tail.md |
| 639 | tailf | tailf | Text anzeigen | tailf.md |
| 640 | tee | tee | Text anzeigen | tee.md |
| 641 | unexpand | unexpand | Text anzeigen | unexpand.md |
| 642 | wc | wc | Text anzeigen | wc.md |
| 643 | xxd | xxd | Text anzeigen | xxd.md |
| 644 | ack | ack | Text suchen & verarbeiten | ack.md |
| 645 | ag | ag | Text suchen & verarbeiten | ag.md |
| 646 | awk | awk | Text suchen & verarbeiten | awk.md |
| 647 | b2sum | b2sum | Text suchen & verarbeiten | b2sum.md |
| 648 | base32 | base32 | Text suchen & verarbeiten | base32.md |
| 649 | base64 | base64 | Text suchen & verarbeiten | base64.md |
| 650 | basenc | basenc | Text suchen & verarbeiten | basenc.md |
| 651 | cksum | cksum | Text suchen & verarbeiten | cksum.md |
| 652 | cmp | cmp | Text suchen & verarbeiten | cmp.md |
| 653 | comm | comm | Text suchen & verarbeiten | comm.md |
| 654 | csplit | csplit | Text suchen & verarbeiten | csplit.md |
| 655 | cut | cut | Text suchen & verarbeiten | cut.md |
| 656 | diff | diff | Text suchen & verarbeiten | diff.md |
| 657 | diff3 | diff3 | Text suchen & verarbeiten | diff3.md |
| 658 | dos2unix | dos2unix | Text suchen & verarbeiten | dos2unix.md |
| 659 | egrep | egrep | Text suchen & verarbeiten | egrep.md |
| 660 | fgrep | fgrep | Text suchen & verarbeiten | fgrep.md |
| 661 | gawk | gawk | Text suchen & verarbeiten | gawk.md |
| 662 | grep | grep | Text suchen & verarbeiten | grep.md |
| 663 | iconv | iconv | Text suchen & verarbeiten | iconv.md |
| 664 | join | join | Text suchen & verarbeiten | join.md |
| 665 | jq | jq | Text suchen & verarbeiten | jq.md |
| 666 | mawk | mawk | Text suchen & verarbeiten | mawk.md |
| 667 | md5sum | md5sum | Text suchen & verarbeiten | md5sum.md |
| 668 | paste | paste | Text suchen & verarbeiten | paste.md |
| 669 | patch | patch | Text suchen & verarbeiten | patch.md |
| 670 | recode | recode | Text suchen & verarbeiten | recode.md |
| 671 | rg | rg | Text suchen & verarbeiten | rg.md |
| 672 | ripgrep | ripgrep | Text suchen & verarbeiten | ripgrep.md |
| 673 | sdiff | sdiff | Text suchen & verarbeiten | sdiff.md |
| 674 | sed | sed | Text suchen & verarbeiten | sed.md |
| 675 | sha1sum | sha1sum | Text suchen & verarbeiten | sha1sum.md |
| 676 | sha224sum | sha224sum | Text suchen & verarbeiten | sha224sum.md |
| 677 | sha256sum | sha256sum | Text suchen & verarbeiten | sha256sum.md |
| 678 | sha384sum | sha384sum | Text suchen & verarbeiten | sha384sum.md |
| 679 | sha512sum | sha512sum | Text suchen & verarbeiten | sha512sum.md |
| 680 | sort | sort | Text suchen & verarbeiten | sort.md |
| 681 | split | split | Text suchen & verarbeiten | split.md |
| 682 | sum | sum | Text suchen & verarbeiten | sum.md |
| 683 | tr | tr | Text suchen & verarbeiten | tr.md |
| 684 | uniq | uniq | Text suchen & verarbeiten | uniq.md |
| 685 | unix2dos | unix2dos | Text suchen & verarbeiten | unix2dos.md |
| 686 | xmlstarlet | xmlstarlet | Text suchen & verarbeiten | xmlstarlet.md |
| 687 | yq | yq | Text suchen & verarbeiten | yq.md |
| 688 | vboxmanage | VBoxManage | Virtualisierung | vboxmanage.md |
| 689 | incus | incus | Virtualisierung | incus.md |
| 690 | lxc | lxc | Virtualisierung | lxc.md |
| 691 | lxc_create | lxc-create | Virtualisierung | lxc_create.md |
| 692 | lxc_ls | lxc-ls | Virtualisierung | lxc_ls.md |
| 693 | lxc_start | lxc-start | Virtualisierung | lxc_start.md |
| 694 | lxc_stop | lxc-stop | Virtualisierung | lxc_stop.md |
| 695 | lxd | lxd | Virtualisierung | lxd.md |
| 696 | multipass | multipass | Virtualisierung | multipass.md |
| 697 | qemu_img | qemu-img | Virtualisierung | qemu_img.md |
| 698 | qemu_system_x86_64 | qemu-system-x86_64 | Virtualisierung | qemu_system_x86_64.md |
| 699 | vagrant | vagrant | Virtualisierung | vagrant.md |
| 700 | virsh | virsh | Virtualisierung | virsh.md |
| 701 | virt_install | virt-install | Virtualisierung | virt_install.md |
| 702 | virt_manager | virt-manager | Virtualisierung | virt_manager.md |
| 703 | virt_viewer | virt-viewer | Virtualisierung | virt_viewer.md |
| 704 | capinfos | capinfos | Wireshark & Analyse | capinfos.md |
| 705 | dumpcap | dumpcap | Wireshark & Analyse | dumpcap.md |
| 706 | editcap | editcap | Wireshark & Analyse | editcap.md |
| 707 | mergecap | mergecap | Wireshark & Analyse | mergecap.md |
| 708 | randpkt | randpkt | Wireshark & Analyse | randpkt.md |
| 709 | rawshark | rawshark | Wireshark & Analyse | rawshark.md |
| 710 | reordercap | reordercap | Wireshark & Analyse | reordercap.md |
| 711 | text2pcap | text2pcap | Wireshark & Analyse | text2pcap.md |
| 712 | tshark | tshark | Wireshark & Analyse | tshark.md |
| 713 | wireshark | wireshark | Wireshark & Analyse | wireshark.md |

## 601 – [lastb.md](../lastb.md)

- Inhalt: Fehlgeschlagene Anmeldungen aus einer Datei lesen. lastb zeigt fehlgeschlagene Anmeldeversuche aus Btmp-Daten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/last.1@@util-linux.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 601: `format: ok`.

## 602 – [lastlog.md](../lastlog.md)

- Inhalt: Letzte Anmeldung je Konto einordnen. lastlog zeigt den letzten gespeicherten Login eines Kontos, keine vollständige Sitzungsfolge.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lastlog.8.html)
- Lokaler Stand: Shadow-lastlog vorhanden; --help scheiterte vor Hilfeausgabe am Auditinterface, Status 1. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 602: `format: ok`.
- Der Hilfeversuch `lastlog --help` endete mit Status `1` und `Cannot open audit interface - aborting.`. Keine Erhöhung von Rechten, kein erneuter Anmelde- oder Kontentest; auch eine erfolgreich gelesene Hilfe wird nicht behauptet.

## 603 – [locale.md](../locale.md)

- Inhalt: Sprach- und Zeichensatzeinstellungen anzeigen. locale zeigt die wirksamen Locale-Kategorien und vorhandene Localeinformationen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/locale.1.html)
- Lokaler Stand: glibc 2.39; Version gelesen, Kategorien nicht praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 603: `format: ok`.

## 604 – [localectl.md](../localectl.md)

- Inhalt: Systemlocale und Tastaturbelegung unterscheiden. localectl fragt Systemvorgaben ab und kann Locale sowie Tastaturbelegung verändern.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/localectl.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 604: `format: ok`.

## 605 – [loginctl.md](../loginctl.md)

- Inhalt: Sitzungen über Logind verwalten. loginctl fragt Sitzungen und Benutzerzustände ab und besitzt aktive Steuerfunktionen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/loginctl.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 605: `format: ok`.

## 606 – [lsipc.md](../lsipc.md)

- Inhalt: IPC-Ressourcen strukturiert anzeigen. lsipc zeigt Informationen zu zugänglichen IPC-Ressourcen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/lsipc.1.html)
- Lokaler Stand: Lokale Hilfe util-linux gelesen; keine Objektabfrage. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 606: `format: ok`.

## 607 – [lslogins.md](../lslogins.md)

- Inhalt: Konteninformationen gezielt zusammenführen. lslogins zeigt ausgewählte Konten- und Loginmerkmale aus mehreren Datenquellen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/lslogins.1.html)
- Lokaler Stand: Lokale Hilfe gelesen; keine Kontenabfrage. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 607: `format: ok`.

## 608 – [lsmod.md](../lsmod.md)

- Inhalt: Geladene Kernelmodule anzeigen. lsmod formatiert die Liste aktuell geladener Kernelmodule.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lsmod.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 608: `format: ok`.

## 609 – [lsns.md](../lsns.md)

- Inhalt: Namespaces lesend auflisten. lsns zeigt zugängliche Linux-Namespaces mit ihren Kennungen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lsns.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 609: `format: ok`.

## 610 – [modinfo.md](../modinfo.md)

- Inhalt: Metadaten einer Moduldatei lesen. modinfo liest Metadaten aus Kernelmodulen und lädt sie nicht.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/modinfo.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 610: `format: ok`.

## 611 – [modprobe.md](../modprobe.md)

- Inhalt: Kernelmodule mitsamt Abhängigkeiten verwalten. modprobe lädt oder entfernt Kernelmodule und kann damit Gerätefunktionen verändern.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/modprobe.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 611: `format: ok`.

## 612 – [mpstat.md](../mpstat.md)

- Inhalt: CPU-Zeitanteile je Prozessor einordnen. mpstat aus Sysstat zeigt CPU-Aktivitätsstatistiken.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/mpstat.1.html)
- Lokaler Stand: Sysstat 12.6.1; Versionsaufruf, kein Funktionslauf. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 612: `format: ok`.

## 613 – [nsenter.md](../nsenter.md)

- Inhalt: Ein Programm in ausgewählten Namespaces starten. nsenter führt ein Programm in anderen Linux-Namespaces aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/nsenter.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 613: `format: ok`.

## 614 – [sar.md](../sar.md)

- Inhalt: Aktuelle und gespeicherte Aktivitätsberichte unterscheiden. sar sammelt oder liest Systemaktivitätsstatistiken aus dem Sysstat-Paket.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sar.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 614: `format: ok`.

## 615 – [sysctl.md](../sysctl.md)

- Inhalt: Kernelparameter lesen und Setzformen erkennen. sysctl kann Laufzeitparameter unter /proc/sys lesen oder verändern.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/sysctl.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 615: `format: ok`.

## 616 – [systemd_analyze.md](../systemd_analyze.md)

- Inhalt: Systemd-Analysemodi gezielt auswählen. systemd-analyze bündelt Startzeitanalyse und weitere Diagnose- beziehungsweise Parserfunktionen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/systemd-analyze.1.html)
- Lokaler Stand: systemd 255.4-1ubuntu8.18. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 616: `format: ok`.

## 617 – [timedatectl.md](../timedatectl.md)

- Inhalt: Zeiteinstellung von Synchronisierungszustand trennen. timedatectl zeigt Zeitkonfiguration und kann Uhr, Zeitzone oder Synchronisierung ändern.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/timedatectl.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 617: `format: ok`.

## 618 – [vmstat.md](../vmstat.md)

- Inhalt: Systemstatistik als begrenzte Zeitreihe lesen. vmstat zeigt Prozess-, Speicher-, Paging-, I/O- und CPU-Kennzahlen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/vmstat.8.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 618: `format: ok`.

## 619 – [w.md](../w.md)

- Inhalt: Sitzungs- und Prozessinformationen einordnen. w kombiniert Sitzungsinformationen mit Aktivitäts- und CPU-Angaben.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/w.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 619: `format: ok`.

## 620 – [who.md](../who.md)

- Inhalt: Sitzungsdaten statt eigener Identität anzeigen. who zeigt Sitzungsinformationen aus einer Utmp-artigen Datenquelle.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/who.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 620: `format: ok`.

## 621 – [bat.md](../bat.md)

- Inhalt: Text mit Syntaxhervorhebung anzeigen. bat erweitert die Textanzeige um Syntaxfarben, Zeilennummern und weitere Darstellung.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://github.com/sharkdp/bat)
- Lokaler Stand: bat nicht vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 621: `format: ok`.

## 622 – [cat.md](../cat.md)

- Inhalt: Dateien hintereinander ausgeben. cat verbindet Dateiinhalte in der angegebenen Reihenfolge auf der Standardausgabe.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cat.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 622: `format: ok`.

## 623 – [column.md](../column.md)

- Inhalt: Einfache Felder als Tabelle darstellen. column formatiert Listen oder getrennte Felder für eine lesbare Tabellenansicht.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/column.1.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 623: `format: ok`.

## 624 – [expand.md](../expand.md)

- Inhalt: Tabulatoren an Tabstopps in Leerzeichen umsetzen. expand ersetzt Tabulatoren durch passende Leerzeichen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/expand.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 624: `format: ok`.

## 625 – [fmt.md](../fmt.md)

- Inhalt: Absätze für eine Zielbreite neu umbrechen. fmt formatiert Textabsätze und schreibt das Ergebnis auf Standardausgabe.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/fmt.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 625: `format: ok`.

## 626 – [fold.md](../fold.md)

- Inhalt: Einzelne Zeilen auf eine Breite umbrechen. fold bricht jede Eingabezeile nach einer Breitenregel um.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/fold.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 626: `format: ok`.

## 627 – [head.md](../head.md)

- Inhalt: Den Anfang einer Datei begrenzt anzeigen. head gibt ohne Mengenoption die ersten zehn Zeilen aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/head.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 627: `format: ok`.

## 628 – [hexdump.md](../hexdump.md)

- Inhalt: Eigene Bytes als Hexdump lesen. hexdump stellt Bytes in gewählten Zahlen- und Zeichenformaten dar.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/hexdump.1.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 628: `format: ok`.

## 629 – [less.md](../less.md)

- Inhalt: Dateien seitenweise betrachten. less ist ein interaktiver Pager mit Such- und Navigationsfunktionen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/less.1.html)
- Lokaler Stand: less 590; Version gelesen, Interaktivbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 629: `format: ok`.

## 630 – [more.md](../more.md)

- Inhalt: Einfaches seitenweises Lesen einordnen. more zeigt Text seitenweise und ist vom direkten cat-Aufruf zu unterscheiden.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/more.1.html)
- Lokaler Stand: util-linux 2.39.3; Version gelesen, Interaktivbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 630: `format: ok`.

## 631 – [nl.md](../nl.md)

- Inhalt: Zeilen mit definierter Nummerierung ausgeben. nl nummeriert logische Textzeilen nach gewählten Regeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/nl.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 631: `format: ok`.

## 632 – [od.md](../od.md)

- Inhalt: Bytes ohne Textannahme darstellen. od zeigt Daten in Oktal-, Hex- und weiteren Zahlenformaten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/od.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 632: `format: ok`.

## 633 – [rev.md](../rev.md)

- Inhalt: Zeichen innerhalb jeder Zeile umkehren. rev kehrt die Zeichenfolge einzelner Zeilen um, nicht die Reihenfolge der Zeilen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/rev.1.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 633: `format: ok`.

## 634 – [script.md](../script.md)

- Inhalt: Terminalaufzeichnung als aktive Ausführung verstehen. script startet einen Terminalkontext und zeichnet dessen Ausgabe beziehungsweise optional Eingabe auf.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/script.1.html)
- Lokaler Stand: util-linux 2.39.3; nur Version, Aufzeichnung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 634: `format: ok`.

## 635 – [scriptreplay.md](../scriptreplay.md)

- Inhalt: Aufzeichnungen wiedergeben ohne Originalbefehle neu zu starten. scriptreplay gibt aufgezeichnete Daten mit Timinginformationen wieder.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/scriptreplay.1.html)
- Lokaler Stand: Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 635: `format: ok`.

## 636 – [strings.md](../strings.md)

- Inhalt: Druckbare Zeichenfolgen aus eigenen Bytes finden. strings sucht hinreichend lange druckbare Zeichenfolgen in Binärdaten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/strings.1.html)
- Lokaler Stand: GNU Binutils 2.42. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 636: `format: ok`.

## 637 – [tac.md](../tac.md)

- Inhalt: Zeilenreihenfolge umkehren. tac gibt Datensätze in umgekehrter Reihenfolge aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tac.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 637: `format: ok`.

## 638 – [tail.md](../tail.md)

- Inhalt: Dateiende begrenzen und Follow-Modi unterscheiden. tail zeigt standardmäßig die letzten zehn Zeilen einer Eingabe.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tail.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 638: `format: ok`.

## 639 – [tailf.md](../tailf.md)

- Inhalt: Historisches tailf korrekt zuordnen. tailf ist ein älteres Werkzeug zum Verfolgen wachsender Dateien und nicht dasselbe Programm wie tail.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/stretch/util-linux/tailf.1.en.html)
- Lokaler Stand: Nicht vorhanden; historische Schnittstelle aus Primärhandbuch, Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 639: `format: ok`.

## 640 – [tee.md](../tee.md)

- Inhalt: Daten gleichzeitig ausgeben und in eine Datei schreiben. tee kopiert Standardeingabe auf Standardausgabe und in benannte Dateien.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tee.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 640: `format: ok`.

## 641 – [unexpand.md](../unexpand.md)

- Inhalt: Leerzeichen nach Tabstopps verdichten. unexpand ersetzt geeignete Leerzeichenfolgen durch Tabulatoren.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/unexpand.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 641: `format: ok`.

## 642 – [wc.md](../wc.md)

- Inhalt: Zeilenenden, Wörter und Bytes getrennt zählen. wc liefert Mengenangaben für Eingabedaten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/wc.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 642: `format: ok`.

## 643 – [xxd.md](../xxd.md)

- Inhalt: Hexdarstellung erzeugen und zurückwandeln. xxd kann Bytes als Hexdump darstellen und eine passende Darstellung wieder in Bytes zurückwandeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/xxd/xxd.1.en.html)
- Lokaler Stand: xxd 2023-10-25. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 643: `format: ok`.

## 644 – [ack.md](../ack.md)

- Inhalt: Quelltextsuche mit Ack begrenzen. ack durchsucht ausgewählte Quelltextdateien mit Perl-Regulärausdrücken.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://beyondgrep.com/documentation/)
- Lokaler Stand: Nicht vorhanden; Ack-Suche offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 644: `format: ok`.

## 645 – [ag.md](../ag.md)

- Inhalt: Silver-Searcher-Suchumfang verstehen. ag ist der Programmname von The Silver Searcher.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://raw.githubusercontent.com/ggreer/the_silver_searcher/master/doc/ag.1)
- Lokaler Stand: Nicht vorhanden; ag-Suche offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 645: `format: ok`.

## 646 – [awk.md](../awk.md)

- Inhalt: Datensätze mit Awk-Feldregeln verarbeiten. awk ist eine Textverarbeitungssprache mit Muster-Aktions-Regeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/awk.1p.html)
- Lokaler Stand: awk -> mawk 1.3.4 20240123. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 646: `format: ok`.

## 647 – [b2sum.md](../b2sum.md)

- Inhalt: BLAKE2b-Prüfsummen erzeugen und prüfen. b2sum berechnet standardmäßig eine BLAKE2b-Prüfsumme mit 512 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/b2sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 647: `format: ok`.

## 648 – [base32.md](../base32.md)

- Inhalt: Binärdaten als Text kodieren und dekodieren. base32 kodiert Daten in ein gewähltes Textalphabet und kann sie zurückwandeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/base32.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 648: `format: ok`.

## 649 – [base64.md](../base64.md)

- Inhalt: Binärdaten als Text kodieren und dekodieren. base64 kodiert Daten in ein gewähltes Textalphabet und kann sie zurückwandeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/base64.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 649: `format: ok`.

## 650 – [basenc.md](../basenc.md)

- Inhalt: Binärdaten als Text kodieren und dekodieren. basenc kodiert Daten in ein gewähltes Textalphabet und kann sie zurückwandeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/basenc.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 650: `format: ok`.

## 651 – [cksum.md](../cksum.md)

- Inhalt: CRC-Dateiprüfsummen von Kryptografie unterscheiden. cksum berechnet traditionell eine CRC-Prüfsumme mit Bytelänge.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cksum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 651: `format: ok`.

## 652 – [cmp.md](../cmp.md)

- Inhalt: Zwei Dateien byteweise vergleichen. cmp vergleicht Bytes und kann einen Unterschied oder Gleichheit per Status melden.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cmp.1.html)
- Lokaler Stand: GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 652: `format: ok`.

## 653 – [comm.md](../comm.md)

- Inhalt: Sortierte Zeilenmengen vergleichen. comm verteilt den Vergleich zweier sortierter Dateien auf drei Ausgabespalten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/comm.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 653: `format: ok`.

## 654 – [csplit.md](../csplit.md)

- Inhalt: Dateien anhand von Kontext in Teile schreiben. csplit erzeugt mehrere Ausgabedateien an Zeilen- oder Mustergrenzen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/csplit.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 654: `format: ok`.

## 655 – [cut.md](../cut.md)

- Inhalt: Felder nach einem einfachen Trenner auswählen. cut wählt festgelegte Bytes, Zeichen oder getrennte Felder aus Zeilen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cut.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 655: `format: ok`.

## 656 – [diff.md](../diff.md)

- Inhalt: Zeilenunterschiede nachvollziehbar anzeigen. diff vergleicht Textdateien und beschreibt Unterschiede.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/diff.1.html)
- Lokaler Stand: GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 656: `format: ok`.

## 657 – [diff3.md](../diff3.md)

- Inhalt: Drei Fassungen mit gemeinsamer Basis vergleichen. diff3 vergleicht drei Textstände und kann ein Mergeergebnis erzeugen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/diff3.1.html)
- Lokaler Stand: GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 657: `format: ok`.

## 658 – [dos2unix.md](../dos2unix.md)

- Inhalt: Windows-Zeilenenden bewusst umwandeln. dos2unix wandelt unter anderem CRLF-Zeilenenden in LF um.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://dos2unix.sourceforge.io/dos2unix/man1/dos2unix.htm)
- Lokaler Stand: Nicht vorhanden; Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 658: `format: ok`.

## 659 – [egrep.md](../egrep.md)

- Inhalt: Veralteten Egrep-Namen einordnen. egrep ist der historische Aufruf für grep mit erweiterten regulären Ausdrücken.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)
- Lokaler Stand: GNU grep 3.11; historischer Wrapper. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 659: `format: ok`.
- Der geprüfte Wrapper gab keine Obsoleszenzwarnung aus. Die frühere Entwurfsbehauptung einer beobachteten Warnung wurde korrigiert; grep -E bleibt die empfohlene Schreibweise.

## 660 – [fgrep.md](../fgrep.md)

- Inhalt: Historischen Fgrep-Aufruf als Literalsuche verstehen. fgrep ist die historische Form für grep -F.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)
- Lokaler Stand: GNU grep 3.11; historischer Wrapper. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 660: `format: ok`.

## 661 – [gawk.md](../gawk.md)

- Inhalt: GNU Awk von anderen Awk-Implementierungen unterscheiden. gawk ist die GNU-Implementierung der Awk-Sprache.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/gawk.1.html)
- Lokaler Stand: Nicht vorhanden; gawk-Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 661: `format: ok`.

## 662 – [grep.md](../grep.md)

- Inhalt: Zeilen nach bewusst gewählter Mustersprache suchen. grep filtert Eingabezeilen anhand eines Musters.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)
- Lokaler Stand: GNU grep 3.11. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 662: `format: ok`.

## 663 – [iconv.md](../iconv.md)

- Inhalt: Zeichencodierung ausdrücklich konvertieren. iconv wandelt zwischen angegebenen Zeichencodierungen um.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/iconv.1.html)
- Lokaler Stand: glibc 2.39-0ubuntu8.9. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 663: `format: ok`.

## 664 – [join.md](../join.md)

- Inhalt: Sortierte Datensätze über einen Schlüssel verbinden. join verbindet Zeilen zweier Dateien anhand gleicher Feldwerte.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/join.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 664: `format: ok`.

## 665 – [jq.md](../jq.md)

- Inhalt: JSON strukturiert statt per Textmuster verarbeiten. jq wertet JSON mit einer Filtersprache aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://jqlang.org/manual/)
- Lokaler Stand: jq 1.7. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 665: `format: ok`.

## 666 – [mawk.md](../mawk.md)

- Inhalt: Text mit der Mawk-Implementierung bearbeiten. mawk ist eine eigenständige Awk-Implementierung.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/testing/mawk/mawk.1.en.html)
- Lokaler Stand: mawk 1.3.4 20240123. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 666: `format: ok`.
- Die tatsächlich gelesene Mawk-Primärquelle ist die verlinkte testing-Handbuchfassung; das lokale Ergebnis bezieht sich ausschließlich auf Mawk 1.3.4 20240123.

## 667 – [md5sum.md](../md5sum.md)

- Inhalt: MD5 nur mit klarer Sicherheitsgrenze verwenden. md5sum berechnet und prüft MD5-Werte.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/md5sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 667: `format: ok`.

## 668 – [paste.md](../paste.md)

- Inhalt: Gleich positionierte Zeilen nebeneinander setzen. paste verbindet entsprechende Zeilen mehrerer Eingaben mit Trennzeichen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/paste.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 668: `format: ok`.

## 669 – [patch.md](../patch.md)

- Inhalt: Eine selbst erzeugte Textänderung gezielt anwenden. patch wendet eine Differenzbeschreibung auf Dateien an.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/patch.1.html)
- Lokaler Stand: GNU patch 2.7.6. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 669: `format: ok`.

## 670 – [recode.md](../recode.md)

- Inhalt: Zeichensätze mit Recode umwandeln. recode wandelt Zeichensätze und bestimmte Oberflächenkodierungen um.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://raw.githubusercontent.com/rrthomas/recode/master/doc/recode.texi)
- Lokaler Stand: Nicht vorhanden; Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 670: `format: ok`.

## 671 – [rg.md](../rg.md)

- Inhalt: Ripgrep mit begrenztem Suchziel verwenden. rg ist die Kommandozeile von ripgrep für schnelle Textsuche.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://raw.githubusercontent.com/BurntSushi/ripgrep/master/GUIDE.md)
- Lokaler Stand: ripgrep 14.1.0, Programm rg. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 671: `format: ok`.

## 672 – [ripgrep.md](../ripgrep.md)

- Inhalt: Projektname Ripgrep und Programmname rg unterscheiden. ripgrep ist der Projekt- und häufig Paketname; der übliche ausführbare Befehl heißt rg.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://raw.githubusercontent.com/BurntSushi/ripgrep/master/GUIDE.md)
- Lokaler Stand: rg 14.1.0 vorhanden; kein ripgrep-Binärname, kein zusätzlicher Funktionslauf. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 672: `format: ok`.
- Fachliche Zuordnung: unveränderte Kennung/Name ripgrep, aber Metadatenfeld command = rg. Kein erfundener zweiter Binärname und kein zusätzlicher Funktionslauf.

## 673 – [sdiff.md](../sdiff.md)

- Inhalt: Unterschiede nebeneinander darstellen. sdiff vergleicht zwei Textdateien in nebeneinanderstehenden Spalten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sdiff.1.html)
- Lokaler Stand: GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 673: `format: ok`.

## 674 – [sed.md](../sed.md)

- Inhalt: Textströme ohne Änderung der Quelle bearbeiten. sed führt ein Bearbeitungsprogramm auf einem Textstrom aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sed.1.html)
- Lokaler Stand: GNU sed 4.9. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 674: `format: ok`.

## 675 – [sha1sum.md](../sha1sum.md)

- Inhalt: Eine 160-Bit-Prüfsumme vergleichen. sha1sum erzeugt oder prüft einen Digest mit 160 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha1sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 675: `format: ok`.

## 676 – [sha224sum.md](../sha224sum.md)

- Inhalt: Eine 224-Bit-Prüfsumme vergleichen. sha224sum erzeugt oder prüft einen Digest mit 224 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha224sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 676: `format: ok`.

## 677 – [sha256sum.md](../sha256sum.md)

- Inhalt: Eine 256-Bit-Prüfsumme vergleichen. sha256sum erzeugt oder prüft einen Digest mit 256 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha256sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 677: `format: ok`.

## 678 – [sha384sum.md](../sha384sum.md)

- Inhalt: Eine 384-Bit-Prüfsumme vergleichen. sha384sum erzeugt oder prüft einen Digest mit 384 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha384sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 678: `format: ok`.

## 679 – [sha512sum.md](../sha512sum.md)

- Inhalt: Eine 512-Bit-Prüfsumme vergleichen. sha512sum erzeugt oder prüft einen Digest mit 512 Bit.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha512sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 679: `format: ok`.

## 680 – [sort.md](../sort.md)

- Inhalt: Text nach ausdrücklich gewählter Ordnung sortieren. sort ordnet Textzeilen nach Vergleichsregeln.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sort.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 680: `format: ok`.

## 681 – [split.md](../split.md)

- Inhalt: Eine Datei in neue Teile zerlegen. split schreibt Teile einer Eingabe in mehrere Ausgabedateien.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/split.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 681: `format: ok`.

## 682 – [sum.md](../sum.md)

- Inhalt: Historische Dateisummen und Blockzahlen verstehen. sum berechnet einfache BSD- oder System-V-Prüfsummen samt Blockzahl.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sum.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 682: `format: ok`.

## 683 – [tr.md](../tr.md)

- Inhalt: Zeichen übersetzen oder löschen. tr verarbeitet Standardeingabe anhand zweier Zeichenmengen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tr.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 683: `format: ok`.

## 684 – [uniq.md](../uniq.md)

- Inhalt: Nur benachbarte gleiche Zeilen zusammenfassen. uniq vergleicht aufeinanderfolgende Zeilen und fasst gleiche Gruppen zusammen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/uniq.1.html)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 684: `format: ok`.

## 685 – [unix2dos.md](../unix2dos.md)

- Inhalt: LF-Zeilenenden in CRLF umwandeln. unix2dos ist die Gegenrichtung zu dos2unix für Textzeilenenden.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://dos2unix.sourceforge.io/dos2unix/man1/dos2unix.htm)
- Lokaler Stand: Nicht vorhanden; CRLF-Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 685: `format: ok`.

## 686 – [xmlstarlet.md](../xmlstarlet.md)

- Inhalt: XML mit einem strukturierten Werkzeug abfragen. xmlstarlet bietet XML-Auswahl, Bearbeitung, Formatierung und Validierung als Unterbefehle.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://xmlstar.sourceforge.net/doc/UG/xmlstarlet-ug.html)
- Lokaler Stand: Nicht vorhanden; XPath und Parserverhalten offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 686: `format: ok`.

## 687 – [yq.md](../yq.md)

- Inhalt: Gleichnamige Yq-Implementierungen unterscheiden. yq ist kein eindeutiger Implementierungsname: verbreitet sind Mike Farahs Go-Werkzeug und Kislyuks jq-Wrapper.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://mikefarah.gitbook.io/yq/commands/evaluate)
- Lokaler Stand: Nicht vorhanden; Implementierung und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 687: `format: ok`.

## 688 – [vboxmanage.md](../vboxmanage.md)

- Inhalt: VirtualBox über die korrekte Kommandozeile verwalten. VBoxManage ist die VirtualBox-Kommandozeile auf dem Host.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/vboxmanage.html)
- Lokaler Stand: Nicht vorhanden; Host- und VM-Funktionen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 688: `format: ok`.

## 689 – [incus.md](../incus.md)

- Inhalt: Incus-Client und Serverkontext unterscheiden. incus verwaltet Container und virtuelle Maschinen über einen Incus-Server.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://linuxcontainers.org/incus/docs/main/reference/manpages/incus/)
- Lokaler Stand: Nicht vorhanden; Server und Instanzen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 689: `format: ok`.

## 690 – [lxc.md](../lxc.md)

- Inhalt: Lxd-Client lxc von Lxc-Einzelwerkzeugen trennen. lxc bezeichnet hier den Client von LXD, nicht den Server und nicht lxc-create.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://canonical.com/lxd/docs/latest/reference/manpages/lxc/)
- Lokaler Stand: Nicht vorhanden; LXD-Clientbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 690: `format: ok`.

## 691 – [lxc_create.md](../lxc_create.md)

- Inhalt: Eine klassische Lxc-Containerdefinition anlegen. lxc-create erstellt einen klassischen LXC-Container mitsamt Konfiguration und möglichem Rootdateisystem.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-create.1.html)
- Lokaler Stand: Nicht vorhanden; Erzeugung und Templates offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 691: `format: ok`.

## 692 – [lxc_ls.md](../lxc_ls.md)

- Inhalt: Klassische Lxc-Container auflisten. lxc-ls zeigt klassische LXC-Container des gewählten Suchbereichs.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-ls.1.html)
- Lokaler Stand: Nicht vorhanden; Bestandsabfrage offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 692: `format: ok`.

## 693 – [lxc_start.md](../lxc_start.md)

- Inhalt: Eine vorhandene klassische Lxc-Definition starten. lxc-start führt die Anwendung beziehungsweise Init eines klassischen LXC-Containers aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-start.1.html)
- Lokaler Stand: Nicht vorhanden; Start offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 693: `format: ok`.

## 694 – [lxc_stop.md](../lxc_stop.md)

- Inhalt: Containerstop und erzwungene Beendigung unterscheiden. lxc-stop fordert die Beendigung eines klassischen LXC-Containers an.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-stop.1.html)
- Lokaler Stand: Nicht vorhanden; Stop-/Signalwirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 694: `format: ok`.

## 695 – [lxd.md](../lxd.md)

- Inhalt: Lxd als Server statt Client einordnen. lxd ist die Serverkomponente der LXD-Container- und VM-Verwaltung.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://canonical.com/lxd/docs/latest/explanation/lxd_lxc/)
- Lokaler Stand: Nicht vorhanden; Serverbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 695: `format: ok`.

## 696 – [multipass.md](../multipass.md)

- Inhalt: Multipass-Instanzen bewusst verwalten. multipass verwaltet virtuelle Instanzen über einen Hintergrunddienst.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://canonical.com/multipass/docs/latest/reference/command-line-interface/)
- Lokaler Stand: Nicht vorhanden; Instanzbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 696: `format: ok`.

## 697 – [qemu_img.md](../qemu_img.md)

- Inhalt: Ein eigenes leeres Diskabbild offline prüfen. qemu-img bearbeitet Diskabbilddateien offline und startet selbst keine virtuelle Maschine.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.qemu.org/docs/master/tools/qemu-img.html)
- Lokaler Stand: QEMU 8.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 697: `format: ok`.

## 698 – [qemu_system_x86_64.md](../qemu_system_x86_64.md)

- Inhalt: Systememulator von Imagewerkzeug unterscheiden. qemu-system-x86_64 startet einen x86-64-Systememulator mit konfigurierten Geräten.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.qemu.org/docs/master/system/invocation.html)
- Lokaler Stand: QEMU 8.2.2; nur -version, VM-Betrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 698: `format: ok`.

## 699 – [vagrant.md](../vagrant.md)

- Inhalt: Vagrant-Konfiguration als ausführbaren Code betrachten. vagrant steuert Entwicklungsumgebungen über Provider und eine Vagrantfile.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://developer.hashicorp.com/vagrant/docs/cli)
- Lokaler Stand: Nicht vorhanden; Projekt-/Providerbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 699: `format: ok`.

## 700 – [virsh.md](../virsh.md)

- Inhalt: Libvirt-Verbindung und Domänenaktion auswählen. virsh ist eine Kommandozeile zur Verwaltung von Libvirt-Domänen und Ressourcen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.libvirt.org/manpages/virsh.html)
- Lokaler Stand: Nicht vorhanden; Libvirt-Betrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 700: `format: ok`.

## 701 – [virt_install.md](../virt_install.md)

- Inhalt: Virtuelle Maschinen mit ausdrücklichen Ressourcen anlegen. virt-install plant und erstellt Gäste über Libvirt.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/virtinst/virt-install.1.en.html)
- Lokaler Stand: Nicht vorhanden; Gastanlage offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 701: `format: ok`.

## 702 – [virt_manager.md](../virt_manager.md)

- Inhalt: Grafische VM-Verwaltung richtig einordnen. virt-manager ist eine grafische Verwaltungsanwendung für Libvirt.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/virt-manager/virt-manager.1.en.html)
- Lokaler Stand: Nicht vorhanden; GUI und Libvirt-Zugriff offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 702: `format: ok`.

## 703 – [virt_viewer.md](../virt_viewer.md)

- Inhalt: Eine grafische Gastkonsole als Verbindung verstehen. virt-viewer verbindet sich mit der grafischen Konsole einer virtuellen Maschine.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/virt-viewer/virt-viewer.1.en.html)
- Lokaler Stand: Nicht vorhanden; Konsole und Transport offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 703: `format: ok`.
- Abschlusskorrektur: -d/--direct unterbindet den SSH-Tunnel, -a/--attach bittet Libvirt um einen vorverbundenen Socket. Transportbedingungen und möglicher Fallback ausdrücklich getrennt.

## 704 – [capinfos.md](../capinfos.md)

- Inhalt: Metadaten einer Capturedatei auswerten. capinfos zeigt Dateiformat, Paketanzahl, Zeitbereich und weitere Metadaten gespeicherter Captures.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/capinfos.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 704: `format: ok`.

## 705 – [dumpcap.md](../dumpcap.md)

- Inhalt: Live-Capture als echten Netzwerkzugriff erkennen. dumpcap zeichnet Pakete von einer Capturequelle in eine Datei auf.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/dumpcap.html)
- Lokaler Stand: Programm vorhanden; keine Interface- oder Capturefunktion ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 705: `format: ok`.

## 706 – [editcap.md](../editcap.md)

- Inhalt: Paketauswahl aus einer Datei neu schreiben. editcap bearbeitet Capturedateien und schreibt eine neue Fassung.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/editcap.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 706: `format: ok`.

## 707 – [mergecap.md](../mergecap.md)

- Inhalt: Capturedateien mit definierter Reihenfolge verbinden. mergecap kombiniert gespeicherte Captures zu einer neuen Datei.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/mergecap.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 707: `format: ok`.

## 708 – [randpkt.md](../randpkt.md)

- Inhalt: Zufallspakete nur als Testdatei erzeugen. randpkt erzeugt eine Capturedatei mit zufälligen Testpaketen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/randpkt.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 708: `format: ok`.

## 709 – [rawshark.md](../rawshark.md)

- Inhalt: Rawshark-Eingabeformat ausdrücklich festlegen. rawshark wertet Roh-Paketströme mit vorgegebener Kapselung aus.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/rawshark.html)
- Lokaler Stand: Hilfe Wireshark 4.2.2 gelesen; keine Paketverarbeitung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 709: `format: ok`.
- Zusätzlich Headergröße, Byteordnung und plattformabhängigen pcap_pkthdr-Modus abgegrenzt; weiterhin kein Decoderlauf.

## 710 – [reordercap.md](../reordercap.md)

- Inhalt: Paketdateien nach gespeicherten Zeiten sortieren. reordercap ordnet Pakete nach aufsteigendem gespeicherten Zeitstempel.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/reordercap.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 710: `format: ok`.

## 711 – [text2pcap.md](../text2pcap.md)

- Inhalt: Einen eigenen Hexdump in eine Capturedatei umwandeln. text2pcap erzeugt Paketdateien aus passenden Hexdarstellungen.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/text2pcap.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 711: `format: ok`.
- Ein erster Testentwurf scheiterte mit Python-Syntaxfehler an falsch eingebetteten Newline-Escapes. Vor Fertigstellung korrigiert; danach lief genau der veröffentlichte Beispielblock erfolgreich. Abschlussprüfung kompiliert zusätzlich alle eingebetteten Python-Heredocs.

## 712 – [tshark.md](../tshark.md)

- Inhalt: Paketfelder ausdrücklich offline auswerten. tshark kann live aufzeichnen oder gespeicherte Capturedateien analysieren.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/tshark.html)
- Lokaler Stand: Wireshark-Werkzeugfamilie 4.2.2. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen.
- Eigener Beispielblock aus Abschnitt 5 ausgeführt, zuletzt in der Abschlussprüfung: Gesamtstatus `0`; Bashsyntax geprüft. Einzelstrukturprüfung 712: `format: ok`.

## 713 – [wireshark.md](../wireshark.md)

- Inhalt: Wireshark-Dateianalyse und Liveaufzeichnung unterscheiden. wireshark ist eine grafische Anwendung für Paketdateien und Live-Captures.
- Gelesene Primärquelle: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/wireshark.html)
- Lokaler Stand: Programm vorhanden; GUI, Profile und Livebetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bash-Beispielblock: ausdrücklich nicht ausgeführtes Textmuster, kein Funktionsnachweis. Einzelstrukturprüfung 713: `format: ok`.

## Abschlussprüfung und Aussagegrenzen

Alle Datensätze 601–713 wurden einzeln in aufsteigender Reihenfolge ausgearbeitet und unmittelbar strukturell geprüft. Sämtliche 113 Dokumente enthalten eine tatsächlich gelesene verlinkte Primärquelle, die feste Zuordnung, die zehn Abschnitte sowie ihren eigenen lokalen Prüfstand. Die Originalfelder sind Ausgangsmaterial und keine ungeprüfte fachliche Autorität. In der Abschlussdurchsicht wurden insbesondere Namens-/Implementierungsunterschiede, veraltete Werkzeuge, Abfrage versus Änderung, Rückgabestatus und tatsächliche Testaussagen nachgeschärft. Bei 45 einfachen Textwerkzeugen wurden konkrete Fehlerbilder, passende Vergleiche und Anwendungsfälle ergänzt.

- 113/113 neue Dokumente: Zuordnung gegen Berichttabelle und unveränderte Original-CSV sowie tatsächlicher NetMon-Parser und `check_document` erfolgreich. Auch command, boolescher Rechtewert und zulässige Risikowerte geprüft.
- 62/62 veröffentlichte Bash-Beispielblöcke: `bash -n` erfolgreich und sämtliche Blöcke in der Abschlussprüfung mit `bash -e` erneut ausgeführt, jeweils Gesamtstatus 0. Erwartete negative Einzelprüfungen werden im jeweiligen Block ausdrücklich abgefangen; der Gesamtstatus ist nicht der Status jedes enthaltenen Einzelbefehls.
- 10/10 eingebettete Python-Heredocs: zusätzlich `compile(...)` erfolgreich. Ihre betreffenden Bashblöcke wurden ebenfalls tatsächlich ausgeführt.
- `python3 -m pytest -q tests/test_linux_command_docs_handoff.py`: **31 passed**.
- Unveränderte CLI für 201–300: **100/100** Struktur/Zuordnung erfolgreich. Zusätzliche Regressionen mit derselben Prüffunktion anhand der bestehenden Berichttabellen: 401–500 **100/100**, 501–600 **100/100**. Diese Strukturregressionen sind keine erneuten fachlichen oder praktischen Prüfungen der älteren Bereiche.
- Kein Prüfcode angepasst; kein zentraler Index, Quellkatalog, Originaldatensatz, bestehendes Dokument oder fremder Arbeitsbereich verändert.

Praktisch begrenzt geprüfte Datensätze (62): 601, 616, 622, 623, 624, 625, 626, 627, 628, 631, 632, 633, 636, 637, 638, 640, 641, 642, 643, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 659, 660, 662, 663, 664, 665, 666, 667, 668, 669, 671, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 697, 704, 706, 707, 708, 710, 711, 712.

Praktische Funktionsprüfung offen (51): 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 617, 618, 619, 620, 621, 629, 630, 634, 635, 639, 644, 645, 658, 661, 670, 672, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 698, 699, 700, 701, 702, 703, 705, 709, 713. Die Gründe und gegebenenfalls nur gelesenen Hilfen/Versionen sind oben je Eintrag und in Abschnitt 9 der jeweiligen Datei genannt. Ein fehlendes Programm wurde nicht nachinstalliert.

Besonders begrenzte Nachweise: lastb las nur eine neu erstellte leere eigene Datei, keine echten fehlgeschlagenen Anmeldungen. systemd-analyze prüfte nur eine Dauerzeichenfolge, keine Boot-, Manager- oder Securityanalyse. qemu-img erzeugte und konvertierte nur ein neues leeres eigenes 1-MiB-Abbild; geprüft wurden Format, virtuelle Größe und gleicher gastseitiger Inhalt, keine VM und kein Dateisystem. Sämtliche Digesttests prüfen den Manifestablauf mit eigenen Bytes, keine mathematische Sicherheit. Kodierungs-Roundtrips prüfen nur ihre konkret angegebenen Eingaben.

Die Capturetests erzeugen ihre Pcap-Dateien vollständig aus eigenen festen Bytes, ohne Netzschnittstelle. Aufbauquelle: [pcap-savefile(5)](https://man7.org/linux/man-pages/man5/pcap-savefile.5.html). Die Zeitstempel und Adressen sind erfunden. Für randpkt wurden drei kleine Zufallspakete ausschließlich in eine Datei geschrieben. Die Daten wurden nicht eingespeist. TShark las ausdrücklich mit -r und -n; die persönlichen Konfigurationspfade wurden auf eigene temporäre Verzeichnisse gesetzt. Es gab keinen Live-Capture, keine Interfaceauflistung und keine GUI. Der mergecap-Test prüft nur -a, nicht den zeitbasierten Standardmerge; reordercap prüft Sortieren gespeicherter Zeiten und keine Uhrkorrektur. text2pcap prüft die eigenen 42 Rahmenbytes und keine gemessenen Zeitmetadaten.

Offen bleiben insbesondere reale Konten-/Kernel-/Namespace-/Systemd-/Zeitzonen- und Leistungsdaten, Pager-/Terminalinteraktion, fehlende Konvertierungswerkzeuge, konkrete Yq-Variante, VM-/Container-/Hypervisorbetrieb, Netzzugriffe, Liveaufzeichnung und Wireshark-Oberfläche. Es wurden keine realen Geräte-, System- oder Benutzeränderungen durchgeführt. Fachliche gemeinsame Freigabe bleibt von bestandener Struktur und den begrenzten Beispielen getrennt.

## Reproduzierbare Zuordnungs- und Syntaxprüfung

Vom Repository-Stamm aus; benötigt nur die vorhandenen Projektmodule und Bash. Dieser Prüfblock führt keine Beispiele aus. Er rekonstruiert die Zuordnung aus der oben veröffentlichten Tabelle, prüft die CSV-Herkunft und verwendet die unveränderte Projektprüfung. Die Beispielausführung steht getrennt oben und ist nicht durch diesen Block nachgewiesen.

```python
import csv, hashlib, io, json, pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path.cwd()))
from scripts.check_linux_command_docs import BASE, check_document, load_catalog
from netmon.services.linux_help_markdown_service import parse_document

def mapping(first, last):
    report = BASE / f'browser-codex/FORTSCHRITT-CODEX-{first}-{last}.md'
    records = []
    for line in report.read_text(encoding='utf-8').splitlines():
        fields = [field.strip() for field in line.split('|')[1:-1]]
        if len(fields) == 5 and fields[0].isdigit():
            nr, identifier, name, category, filename = fields
            records.append(dict(source_record=int(nr), id=identifier, name=name,
                                category=category, document=filename))
    assert [r['source_record'] for r in records] == list(range(first, last+1))
    assert len({r['document'] for r in records}) == len(records)
    return report, records

original = load_catalog()
raw = pathlib.Path(original['source_catalog']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == '40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887'
rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
assert len(rows) == 713
catalog = {'source_catalog': original['source_catalog']}
report, records = mapping(601, 713)
assert re.findall(r'^## (\d+) –', report.read_text(), re.M) == [str(n) for n in range(601, 714)]
functional = []
python_blocks = 0
for record in records:
    nr = record['source_record']
    assert rows[nr-1]['Befehl'] == record['name']
    assert rows[nr-1]['Kategorie'] == record['category']
    path = BASE / record['document']
    assert path.parent == BASE and path.suffix == '.md'
    assert check_document(path, record, catalog)['format'] == 'ok'
    source = path.read_text(encoding='utf-8')
    metadata = parse_document(source).metadata
    assert metadata['command'] == ('rg' if nr == 672 else record['name'])
    assert isinstance(metadata['root_required'], bool)
    assert metadata['risk_level'] in {'safe', 'caution', 'danger'}
    blocks = re.findall(r'```bash\n(.*?)\n```', source, re.S)
    assert len(blocks) <= 1
    for block in blocks:
        subprocess.run(['bash', '-n'], input=block, text=True, check=True)
        assert 'probe_dir=$(mktemp -d) || exit 1' in block
        assert 'cd "$probe_dir" || exit 1' in block
        for match in re.finditer(r"python3 <<'([A-Z0-9_]+)'\n(.*?)\n\1(?:\n|$)", block, re.S):
            compile(match[2], f'{path.name}:{match[1]}', 'exec')
            python_blocks += 1
        functional.append(nr)
print(f'601–713: {len(records)} Zuordnungen/Strukturen OK; {len(functional)} Bashblöcke bash -n OK; {python_blocks} Python-Heredocs compile OK')
print('Begrenzte Funktionsfälle:', len(functional), functional)
for first,last in [(401,500),(501,600)]:
    _, previous = mapping(first,last)
    for record in previous:
        assert check_document(BASE/record['document'],record,catalog)['format'] == 'ok'
    print(f'Regression {first}–{last}: {len(previous)}/{len(previous)} Struktur und Zuordnung OK')
```

Nach Datensatz 713 gestoppt. Veröffentlichungsumfang: 113 neue Dokumente plus ausschließlich dieser Bericht (114 neue Dateien). Kein Merge nach main.
