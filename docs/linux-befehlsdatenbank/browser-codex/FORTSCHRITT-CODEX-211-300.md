# Ausarbeitung und Prüfung 211–300

Basis: `codex/linux-docs-browser-handoff-20261113`, Commit `135b1097382b42d5b9a90e78241dcff9c388b1f2`. Prüfdatum: 2026-11-13. Der aktuelle ausdrückliche Nutzerauftrag ersetzt die frühere Grenze 210; die gemeinsamen Regeln zu Quellen, Format, Einzelreihenfolge, Ausführungsgrenzen und Änderungsumfang gelten weiter. Keine Unteragenten eingesetzt.

Arbeitskopie: `/tmp/linux-docs-review-201-210-20261113`. Bearbeitung einzeln, aufsteigend; pro Nummer Originaldatensatz lesen, Primärquelle lesen, Dokument ausarbeiten, zulässige Prüfung und Einzelstrukturprüfung, dann Bericht ergänzen. Ein temporäres Autorenhilfsmittel außerhalb der Git-Arbeitskopie setzt nur Metadaten/Überschriften und führt die ausdrücklich angegebenen Prüfungen aus; es ersetzt keine Quellen- oder Fachprüfung.

Original-CSV und eingefrorener Katalog werden vom vorhandenen Checker gegengeprüft (713 Datensätze, SHA-256 `40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`). Für fehlende Programme keine Installation. Geräte-/System-/Kontenänderungen, Mounts, Dienstaufrufe, reale Netzabfragen und Desktopänderungen sind keine Beispieltests. Unausgeführte Geräte-/GUI-Abläufe sind mit Erklärungsmustern und offenem praktischem Stand dokumentiert. Eine Paket- oder Handbuchversion ist keine ausgeführte Programmversion.

## 211 – [btrfs.md](../btrfs.md)

- Inhalt: Btrfs-Unterbefehle und ihre Eingriffe unterscheiden. `btrfs` ist die Verwaltungswerkzeugsammlung für Btrfs-Dateisysteme. Die Untergruppe bestimmt, ob nur Informationen gelesen oder Daten verändert werden. Für administrative Operationen sind häufig besondere Rechte nötig; Hilfe benötigt kein Root.
- Gelesene Primärquelle: [Btrfs-Hauptwerkzeug](https://btrfs.readthedocs.io/en/latest/btrfs.html), [Btrfs check](https://btrfs.readthedocs.io/en/latest/btrfs-check.html)
- Lokaler Stand: Nicht praktisch geprüft; btrfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 211: `format: ok`.

## 212 – [cfdisk.md](../cfdisk.md)

- Inhalt: Partitionstabellen interaktiv bearbeiten. `cfdisk` ist ein textbasierter interaktiver Partitionstabelleneditor aus util-linux. Er benötigt für reale Datenträger üblicherweise administrative Zugriffsrechte. Er ändert Partitionierung, nicht automatisch das enthaltene Dateisystem.
- Gelesene Primärquelle: [cfdisk-Projekthandbuch bei Debian](https://manpages.debian.org/trixie/fdisk/cfdisk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; cfdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 212: `format: ok`.

## 213 – [chattr.md](../chattr.md)

- Inhalt: Dateiattribute gezielt von normalen Rechten unterscheiden. `chattr` verändert besondere Dateisystemattribute. Es ersetzt `chmod` nicht. Für manche Attribute eigener Dateien genügt Eigentümerschaft; `i` und `a` erfordern besondere Privilegien. Root ist deshalb nicht generell für jeden Aufruf erforderlich.
- Gelesene Primärquelle: [chattr-Handbuch aus e2fsprogs](https://manpages.debian.org/trixie/e2fsprogs/chattr.1.en.html) und lokale Manpage 1.47.0
- Lokaler Stand: chattr 1.47.0 (5-Feb-2023). Praktisch geprüft: Abschnitt-5-Ablauf ausgeführt; d gesetzt und entfernt, Inhalt erhalten. Nicht praktisch geprüft: i/a, privilegierte Ausnahmen, Rekursion, andere Dateisysteme.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 213: `format: ok`.

## 214 – [debugfs.md](../debugfs.md)

- Inhalt: ext-Dateisysteme unterhalb der normalen Dateioperationen untersuchen. `debugfs` untersucht und verändert ext2/ext3/ext4-Strukturen direkt. Der Standard öffnet lesend; `-w` schaltet Schreibzugriff ein. Für eigene Abbilddateien ist kein Root nötig, für reale Geräte gelten deren Zugriffsrechte.
- Gelesene Primärquelle: [debugfs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/debugfs.8.en.html) sowie lokale Manpage 1.47.0
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 214: `format: ok`.

## 215 – [dumpe2fs.md](../dumpe2fs.md)

- Inhalt: Superblock und Blockgruppen von ext lesen. `dumpe2fs` zeigt Verwaltungsinformationen von ext2/ext3/ext4 an. Es prüft nicht sämtliche Nutzdaten und führt keine Reparatur aus. Ein lesbares eigenes Abbild benötigt kein Root; rohe Geräte erfordern passende Zugriffsrechte.
- Gelesene Primärquelle: [dumpe2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/dumpe2fs.8.en.html) und lokale Manpage 1.47.0
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 215: `format: ok`.

## 216 – [e2fsck.md](../e2fsck.md)

- Inhalt: ext-Strukturen prüfen und Reparaturmodi unterscheiden. `e2fsck` prüft ext2/ext3/ext4-Dateisysteme und kann deren Strukturen reparieren. Das ist keine bloße Statusabfrage. Für rohe Datenträger sind meist administrative Rechte nötig; eigene Abbilder benötigen nur passende Dateirechte.
- Gelesene Primärquelle: [e2fsck-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/e2fsck.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 216: `format: ok`.

## 217 – [edquota.md](../edquota.md)

- Inhalt: Speicher- und Inodequoten bearbeiten. `edquota` öffnet einen Editor für Benutzer-, Gruppen- oder Projektquoten. Das Speichern kann reale Kontingente ändern. Die Dokumentation setzt hierfür administrative Rechte voraus; es ist kein gewöhnlicher Textdateieditor für beliebige Dateien.
- Gelesene Primärquelle: [edquota-Handbuch der quota-tools](https://manpages.debian.org/trixie/quota/edquota.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; edquota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 217: `format: ok`.

## 218 – [fdisk.md](../fdisk.md)

- Inhalt: Partitionstabellen anzeigen und Änderungen bewusst schreiben. `fdisk` aus util-linux ist ein interaktiver Partitionstabelleneditor mit separatem Listenmodus. Anzeigen und Schreiben haben grundverschiedene Wirkungen. Für rohe Geräte sind passende, häufig administrative Rechte nötig.
- Gelesene Primärquelle: [fdisk-Projekthandbuch](https://manpages.debian.org/trixie/fdisk/fdisk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; fdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 218: `format: ok`.

## 219 – [findmnt.md](../findmnt.md)

- Inhalt: Mountinformationen und Konfigurationspläne getrennt lesen. `findmnt` sucht in Mounttabellen und zeigt Dateisystembeziehungen an. Das Programm hängt nichts ein. Gewöhnliche Auskünfte und die eigene Testtabelle benötigen kein Root.
- Gelesene Primärquelle: [findmnt-Handbuch](https://manpages.debian.org/trixie/util-linux/findmnt.8.en.html) und lokale Manpage 2.39.3
- Lokaler Stand: findmnt from util-linux 2.39.3. Praktisch geprüft: Eigene alternative fstab-Tabelle vollständig wie im Beispiel gelesen. Nicht praktisch geprüft: echte Mountsuche, Tagauflösung, Polling und fremde Namespaces.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 219: `format: ok`.

## 220 – [fsck.md](../fsck.md)

- Inhalt: Prüfer auswählen, ohne einen Trockenlauf mit Reparatur zu verwechseln. `fsck` ist ein Verteiler an dateisystemspezifische Prüfer wie `fsck.ext4`. Es ist keine für alle Dateisysteme gleich funktionierende Reparatur. Der echte Einsatz benötigt passende Zielrechte und einen Wartungsplan; der gezeigte reine Planaufruf braucht kein Root.
- Gelesene Primärquelle: [fsck-Handbuch](https://manpages.debian.org/trixie/util-linux/fsck.8.en.html)
- Lokaler Stand: fsck from util-linux 2.39.3. Praktisch geprüft: Nur -N-Plan mit eigener leerer Tabelle und eigener leerer Datei ausgeführt. Keine Strukturprüfung oder Reparatur; echte Prüferläufe, Statusbits und Parallelverhalten offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 220: `format: ok`.

## 221 – [fstrim.md](../fstrim.md)

- Inhalt: Freie Dateisystembereiche für Discard melden. `fstrim` meldet unbenutzte Bereiche eines eingehängten Dateisystems an den Speicherstack. Es löscht keine benannten Dateien, ist aber eine wirkliche Speicherverwaltungsaktion mit administrativen Rechteanforderungen.
- Gelesene Primärquelle: [fstrim-Handbuch](https://manpages.debian.org/trixie/util-linux/fstrim.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 221: `format: ok`.

## 222 – [gdisk.md](../gdisk.md)

- Inhalt: GPT-Tabellen und ihre Sicherungskopien verstehen. `gdisk` ist der interaktive GPT-Partitionstabelleneditor aus GPT fdisk. Er kann vorhandene MBR-/BSD-Strukturen im Arbeitsspeicher nach GPT umsetzen. Das spätere Schreiben ist eine potenziell destruktive Änderung.
- Gelesene Primärquelle: [gdisk-Projekthandbuch](https://manpages.debian.org/trixie/gdisk/gdisk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; gdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 222: `format: ok`.

## 223 – [hdparm.md](../hdparm.md)

- Inhalt: ATA-Informationen von schreibenden Laufwerkseinstellungen trennen. `hdparm` fragt SATA/IDE-Parameter ab und kann sie verändern. Es ist kein universelles Werkzeug für jedes NVMe-, USB- oder RAID-Gerät. Direkte Laufwerksbefehle benötigen passende Rechte und sind keine gewöhnlichen Dateizugriffe.
- Gelesene Primärquelle: [hdparm-Projekthandbuch](https://manpages.debian.org/trixie/hdparm/hdparm.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 223: `format: ok`.

## 224 – [losetup.md](../losetup.md)

- Inhalt: Abbilddateien und Loop-Geräte zuordnen. `losetup` verknüpft Dateien mit Loop-Blockgeräten, zeigt Zuordnungen oder löst sie. Eine Zuordnung ist eine Kernelzustandsänderung, selbst wenn die Datei im temporären Ordner liegt. Dafür sind üblicherweise administrative Rechte nötig.
- Gelesene Primärquelle: [losetup-Handbuch](https://manpages.debian.org/trixie/mount/losetup.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 224: `format: ok`.

## 225 – [lsattr.md](../lsattr.md)

- Inhalt: Besondere Dateiattribute lesen. `lsattr` zeigt Dateisystemattribute an, statt sie zu verändern. Für eigene erreichbare Dateien ist kein Root nötig. Es ergänzt die klassische Rechteanzeige von ls und ACL-Werkzeugen, ersetzt sie aber nicht.
- Gelesene Primärquelle: [lsattr-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/lsattr.1.en.html), [Attributbedeutungen](https://manpages.debian.org/trixie/e2fsprogs/chattr.1.en.html) und lokale Manpage
- Lokaler Stand: lsattr 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel komplett an eigenen Dateien: Einzelansicht, Punktname, Verzeichnis selbst und lange Namen erfolgreich. Andere Dateisysteme, privilegierte Fälle und Spezialattribute nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 225: `format: ok`.

## 226 – [lsblk.md](../lsblk.md)

- Inhalt: Blockgeräte und ihre Abhängigkeiten darstellen. `lsblk` zeigt Blockgeräte und ihre Beziehungen an. Normale Informationen aus sysfs/udev benötigen üblicherweise kein Root. Falls diese Daten fehlen, kann Dateisystemerkennung direkte Gerätezugriffe mit anderen Rechteanforderungen benötigen.
- Gelesene Primärquelle: [lsblk-Handbuch](https://manpages.debian.org/trixie/util-linux/lsblk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 226: `format: ok`.

## 227 – [mkfs.md](../mkfs.md)

- Inhalt: Den Dateisystem-Ersteller bewusst auswählen. `mkfs` ist ein älteres Frontend für dateisystemspezifische Ersteller. Eine Ausführung kann bestehende Dateisystemstrukturen überschreiben. Das Projekthandbuch bevorzugt die konkreten Programme `mkfs.TYP`. Auf realen Datenträgern sind entsprechende Verwaltungsrechte nötig.
- Gelesene Primärquelle: [mkfs-Projekthandbuch](https://manpages.debian.org/trixie/util-linux/mkfs.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 227: `format: ok`.

## 228 – [mkfs_btrfs.md](../mkfs_btrfs.md)

- Inhalt: Ein neues Btrfs-Dateisystem planen. `mkfs.btrfs` legt Btrfs-Strukturen auf einem oder mehreren Zielen an. Vorhandene Daten können dadurch verloren gehen. Eigene Abbilddateien können ohne Root beschrieben werden; reale Geräte benötigen entsprechende Zugriffsrechte.
- Gelesene Primärquelle: [mkfs.btrfs-Projekthandbuch](https://btrfs.readthedocs.io/en/latest/mkfs.btrfs.html)
- Lokaler Stand: Nicht praktisch geprüft; mkfs.btrfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 228: `format: ok`.

## 229 – [mkfs_ext2.md](../mkfs_ext2.md)

- Inhalt: Ein ext2-Dateisystem in einer eigenen Abbilddatei anlegen. `mkfs.ext2` ist ein Aufrufname von mke2fs und wählt ext2 als Typ. Es erzeugt neue Strukturen und kann bestehende Daten überschreiben. Für die ausschließlich eigene gewöhnliche Abbilddatei ist kein Root erforderlich; ein echtes Blockgerät hätte andere Rechte- und Freigabebedingungen.
- Gelesene Primärquelle: [mke2fs-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/mke2fs.8.en.html) und lokale mke2fs-Manpage
- Lokaler Stand: mke2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel mit eigener 16-MiB-Abbilddatei ausgeführt und Label/Featureliste gelesen. Nicht praktisch geprüft: reale Geräte, Mounts, Kernelkompatibilität, Reparatur, Datenwiederherstellung und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 229: `format: ok`.

## 230 – [mkfs_ext3.md](../mkfs_ext3.md)

- Inhalt: Ein ext3-Dateisystem in einer eigenen Abbilddatei anlegen. `mkfs.ext3` ist ein Aufrufname von mke2fs und wählt ext3 als Typ. Es erzeugt neue Strukturen und kann bestehende Daten überschreiben. Für die ausschließlich eigene gewöhnliche Abbilddatei ist kein Root erforderlich; ein echtes Blockgerät hätte andere Rechte- und Freigabebedingungen.
- Gelesene Primärquelle: [mke2fs-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/mke2fs.8.en.html) und lokale mke2fs-Manpage
- Lokaler Stand: mke2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel mit eigener 16-MiB-Abbilddatei ausgeführt und Label/Featureliste gelesen. Nicht praktisch geprüft: reale Geräte, Mounts, Kernelkompatibilität, Reparatur, Datenwiederherstellung und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 230: `format: ok`.

## 231 – [mkfs_ext4.md](../mkfs_ext4.md)

- Inhalt: Ein ext4-Dateisystem in einer eigenen Abbilddatei anlegen. `mkfs.ext4` ist ein Aufrufname von mke2fs und wählt ext4 als Typ. Es erzeugt neue Strukturen und kann bestehende Daten überschreiben. Für die ausschließlich eigene gewöhnliche Abbilddatei ist kein Root erforderlich; ein echtes Blockgerät hätte andere Rechte- und Freigabebedingungen.
- Gelesene Primärquelle: [mke2fs-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/mke2fs.8.en.html) und lokale mke2fs-Manpage
- Lokaler Stand: mke2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel mit eigener 16-MiB-Abbilddatei ausgeführt und Label/Featureliste gelesen. Nicht praktisch geprüft: reale Geräte, Mounts, Kernelkompatibilität, Reparatur, Datenwiederherstellung und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 231: `format: ok`.

## 232 – [mkfs_xfs.md](../mkfs_xfs.md)

- Inhalt: XFS-Geometrie und Anlageparameter festlegen. `mkfs.xfs` erzeugt ein neues XFS-Dateisystem. Der Inhalt eines vorhandenen Ziels kann dabei zerstört werden. Eigene Abbilddateien sind ohne Root möglich; reale Geräte verlangen passende Verwaltungsrechte.
- Gelesene Primärquelle: [mkfs.xfs-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/mkfs.xfs.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; mkfs.xfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 232: `format: ok`.

## 233 – [mkswap.md](../mkswap.md)

- Inhalt: Swap-Metadaten vorbereiten, ohne Swap zu aktivieren. `mkswap` legt einen Linux-Swap-Header in einer Datei oder auf einem Gerät an. Es aktiviert keinen Swap. Für die neue eigene Testdatei ist kein Root nötig; echte Gerätezugriffe und die spätere Aktivierung sind Verwaltungsaktionen.
- Gelesene Primärquelle: [mkswap-Handbuch](https://manpages.debian.org/trixie/util-linux/mkswap.8.en.html)
- Lokaler Stand: mkswap from util-linux 2.39.3. Praktisch geprüft: Nur Header in eigener voll beschriebener 1-MiB-Datei angelegt; Länge und Modus geprüft. Nicht praktisch geprüft: Geräte, Aktivierung, Kernel-/Dateisystemeignung und neue --file-Optionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 233: `format: ok`.

## 234 – [mount.md](../mount.md)

- Inhalt: Dateisysteme in den Verzeichnisbaum einhängen. `mount` verbindet ein Dateisystem oder eine andere Dateisicht mit einem Pfad. Das verändert den Mountzustand. Üblicherweise sind administrative Rechte nötig; ausdrücklich erlaubte Benutzermounts, FUSE oder Namespaces haben eigene Regeln.
- Gelesene Primärquelle: [mount-Projekthandbuch](https://manpages.debian.org/trixie/mount/mount.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 234: `format: ok`.

## 235 – [mountpoint.md](../mountpoint.md)

- Inhalt: Einen Mountpunkt prüfen, ohne etwas einzuhängen. `mountpoint` prüft, ob ein Pfad im eigenen Mount-Namespace als Mountpunkt geführt wird. Es mountet und unmountet nichts. Für erreichbare eigene Verzeichnisse sind keine Root-Rechte nötig.
- Gelesene Primärquelle: [mountpoint-Handbuch](https://manpages.debian.org/trixie/util-linux/mountpoint.1.en.html) und lokale Manpage
- Lokaler Stand: mountpoint from util-linux 2.39.3. Praktisch geprüft: Negativer Test am eigenen frischen Unterordner erfolgreich. Positive Mountfälle, --nofollow, -x und andere Namespaces nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 235: `format: ok`.

## 236 – [nvme.md](../nvme.md)

- Inhalt: NVMe-Unterbefehle und Zielbereiche unterscheiden. `nvme` aus nvme-cli ist eine Sammlung für NVMe-Controller und Namespaces. Sie umfasst lesende Berichte ebenso wie Formatierung, Firmware- und Namespaceänderungen. Hilfe benötigt kein Root; echte Gerätebefehle haben unterbefehlsspezifische Rechteanforderungen.
- Gelesene Primärquelle: [nvme-cli-Hauptseite](https://manpages.debian.org/trixie/nvme-cli/nvme.1.en.html), [smart-log](https://manpages.debian.org/trixie/nvme-cli/nvme-smart-log.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; nvme fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 236: `format: ok`.

## 237 – [parted.md](../parted.md)

- Inhalt: Partitionen mit GNU Parted verändern. `parted` zeigt und verändert Partitionstabellen. Schreibende Befehle gehören in einen Wartungsablauf; sie sind kein Lesecheck. Auf realen Datenträgern sind passende administrative Rechte nötig.
- Gelesene Primärquelle: [GNU-Parted-Manpage bei Debian](https://manpages.debian.org/trixie/parted/parted.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 237: `format: ok`.

## 238 – [partprobe.md](../partprobe.md)

- Inhalt: Den Kernel über geänderte Partitionstabellen informieren. `partprobe` informiert den Kernel über Partitionstabellenänderungen. Es ist weder ein Dateisystemprüfer noch bloß ein allgemeiner Statusbefehl. Das Aktualisieren des Kernelzustands ist eine administrative Systemaktion.
- Gelesene Primärquelle: [partprobe-Manpage](https://manpages.debian.org/trixie/parted/partprobe.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 238: `format: ok`.

## 239 – [quota.md](../quota.md)

- Inhalt: Belegung, Softlimit und Hardlimit anzeigen. `quota` zeigt Speicher- und Inodekontingente. Eigene Benutzerquoten benötigen normalerweise kein Root; fremde Benutzer- und Projektquoten unterliegen zusätzlichen Rechten. Der Aufruf ändert keine Grenzen.
- Gelesene Primärquelle: [quota-tools-Handbuch](https://manpages.debian.org/trixie/quota/quota.1.en.html)
- Lokaler Stand: Nicht praktisch geprüft; quota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 239: `format: ok`.

## 240 – [quotacheck.md](../quotacheck.md)

- Inhalt: Quota-Abrechnung neu ermitteln und Änderungen erkennen. `quotacheck` scannt Belegung und kann Quota-Dateien erzeugen, prüfen und korrigieren. Der Name check bedeutet hier nicht schreibgeschützte Beobachtung. Es ist ein administratives Werkzeug.
- Gelesene Primärquelle: [quotacheck-Handbuch](https://manpages.debian.org/trixie/quota/quotacheck.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; quotacheck fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 240: `format: ok`.

## 241 – [repquota.md](../repquota.md)

- Inhalt: Quota-Gesamtberichte lesbar auswerten. `repquota` fasst Belegung und Kontingente ausgewählter Dateisysteme zusammen. Es ist ein Berichtswerkzeug, kein Quota-Editor. Für die Verwaltung fremder Benutzer-/Gruppendaten sind besondere Rechte nötig.
- Gelesene Primärquelle: [repquota-Handbuch](https://manpages.debian.org/trixie/quota/repquota.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; repquota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 241: `format: ok`.

## 242 – [resize2fs.md](../resize2fs.md)

- Inhalt: Dateisystemgröße von Partitionsgröße unterscheiden. `resize2fs` ändert die Größe von ext2/ext3/ext4. Es ändert keine Partitionstabelle. Für die eigene neue Abbilddatei sind keine Root-Rechte nötig; reale Online-/Offline-Wartung erfordert andere Rechte und Freigaben.
- Gelesene Primärquelle: [resize2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/resize2fs.8.en.html)
- Lokaler Stand: resize2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Offline-Vergrößerung der eigenen frischen ext2-Datei von 16 auf 32 MiB erfolgreich, Blockgeometrie gelesen. Nicht praktisch geprüft: Verkleinern, Onlinebetrieb, echte Partitionen, 64bit-Konvertierung und Wiederherstellung.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 242: `format: ok`.

## 243 – [sfdisk.md](../sfdisk.md)

- Inhalt: Partitionstabellen als Skriptdaten behandeln. `sfdisk` aus util-linux liest oder schreibt Partitionstabellen, besonders für Skripte. Der Standardauftrag mit Ziel liest einen Plan von Standardeingabe und kann ihn schreiben. Das ist keine reine Inventur; reale Ziele benötigen passende Verwaltungsrechte.
- Gelesene Primärquelle: [sfdisk-Projekthandbuch](https://manpages.debian.org/trixie/fdisk/sfdisk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; sfdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 243: `format: ok`.

## 244 – [sgdisk.md](../sgdisk.md)

- Inhalt: GPT-Aktionen in Skripten ausdrücklich auswählen. `sgdisk` ist die kommandozeilenorientierte GPT-Verwaltung aus GPT fdisk. Anders als der interaktive Verwandte gdisk führt es Änderungen gewöhnlich ohne abschließende Bestätigung aus. Für reale Ziele sind passende administrative Rechte nötig.
- Gelesene Primärquelle: [sgdisk-Projekthandbuch](https://manpages.debian.org/trixie/gdisk/sgdisk.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; sgdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 244: `format: ok`.

## 245 – [smartctl.md](../smartctl.md)

- Inhalt: SMART-Berichte und Selbsttests auseinanderhalten. `smartctl` liest Laufwerksinformationen und steuert SMART-/Selbsttestfunktionen. Reine Berichte und zustandsändernde Test-/Einstellbefehle sind getrennte Aufgaben. Gerätekommunikation benötigt passende Zugriffsrechte.
- Gelesene Primärquelle: [smartmontools-Projekthandbuch, einschließlich Statusbits](https://manpages.debian.org/trixie/smartmontools/smartctl.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; smartctl fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 245: `format: ok`.

## 246 – [swapoff.md](../swapoff.md)

- Inhalt: Aktive Swapbereiche kontrolliert deaktivieren. `swapoff` deaktiviert ausgewählte Swapbereiche. Es ist eine privilegierte Speicherverwaltungsaktion und kein Anzeigeprogramm. Die Aktion löscht nicht automatisch die Swapdatei und macht gespeicherte Inhalte nicht sicher unsichtbar.
- Gelesene Primärquelle: [swapoff/swapon-Projekthandbuch](https://manpages.debian.org/trixie/mount/swapoff.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 246: `format: ok`.

## 247 – [swapon.md](../swapon.md)

- Inhalt: Vorbereiteten Swap aktivieren und reine Anzeige unterscheiden. `swapon` aktiviert vorbereitete Swapdateien oder Geräte. Der Anzeigemodus --show ist davon getrennt. Aktivierung ist eine administrative Kerneländerung; die verfügbare Dateigröße allein reicht nicht für eine geeignete Swapdatei.
- Gelesene Primärquelle: [swapon-Projekthandbuch](https://manpages.debian.org/trixie/mount/swapon.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 247: `format: ok`.

## 248 – [tune2fs.md](../tune2fs.md)

- Inhalt: ext-Superblockparameter lesen und gezielt ändern. `tune2fs` zeigt oder verändert ext2/ext3/ext4-Verwaltungsparameter. Kleinbuchstabe -l listet, Großbuchstabe -L ändert das Label. Für die neue eigene Abbilddatei braucht man kein Root; echte Datenträger haben andere Zugriffsbedingungen.
- Gelesene Primärquelle: [tune2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/tune2fs.8.en.html)
- Lokaler Stand: tune2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Eigenes frisches ext2-Abbild vor/nach Labeländerung erfolgreich gelesen. Nicht praktisch geprüft: echte Geräte, Feature-/UUID-Konvertierung, Mount-/Prüfplanung und Wiederherstellung.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 248: `format: ok`.

## 249 – [umount.md](../umount.md)

- Inhalt: Eine Einhängung geordnet lösen. `umount` löst eine Dateisystemeinhängung. Es löscht nicht das Verzeichnis und wirft Hardware nicht automatisch aus. Normalerweise gelten administrative Rechte; erlaubte Benutzer-/FUSE-Mounts haben besondere Regeln.
- Gelesene Primärquelle: [umount-Projekthandbuch](https://manpages.debian.org/trixie/mount/umount.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 249: `format: ok`.

## 250 – [wipefs.md](../wipefs.md)

- Inhalt: Signaturen anzeigen, ohne sie zu löschen. `wipefs` erkennt Dateisystem-, RAID- und Partitionstabellensignaturen und kann sie löschen. Ohne Löschoption wird am angegebenen Ziel eine Liste erzeugt. Für das eigene Abbild benötigt die Anzeige kein Root; echte Geräte haben eigene Rechtebedingungen.
- Gelesene Primärquelle: [wipefs-Handbuch](https://manpages.debian.org/trixie/util-linux/wipefs.8.en.html)
- Lokaler Stand: wipefs from util-linux 2.39.3. Praktisch geprüft: Nur Signaturanzeige der eigenen ext2-Datei; SHA-256 blieb gleich. Nicht praktisch geprüft: Signaturlöschung, Geräte, Cache-/Kernelnebenwirkungen und Wiederherstellung.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 250: `format: ok`.

## 251 – [xfs_info.md](../xfs_info.md)

- Inhalt: XFS-Geometrie ohne Größenänderung lesen. `xfs_info` beschreibt die Geometrie eines vorhandenen XFS-Dateisystems und verändert dessen Inhalte nicht. Ein lesbares eigenes Abbild braucht kein Root; rohe Geräte unterliegen deren Dateirechten. Das Werkzeug ist keine Reparatur und keine Vergrößerung.
- Gelesene Primärquelle: [xfs_info-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/xfs_info.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; xfs_info fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 251: `format: ok`.

## 252 – [xfs_repair.md](../xfs_repair.md)

- Inhalt: XFS-Strukturprüfung von Reparatur und Logverlust trennen. `xfs_repair` prüft und repariert XFS-Strukturen. Ein gewöhnlicher Lauf kann schreiben. Das Ziel muss für einen korrekten Reparaturablauf ungemountet sein. Eigene Abbildkopien benötigen keine allgemeine Rootpflicht; reale Geräte entsprechende Rechte.
- Gelesene Primärquelle: [xfs_repair-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/xfs_repair.8.en.html)
- Lokaler Stand: Nicht praktisch geprüft; xfs_repair fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 252: `format: ok`.

## 253 – [dbus_send.md](../dbus_send.md)

- Inhalt: Typisierte Nachrichten an einen D-Bus senden. `dbus-send` sendet D-Bus-Nachrichten. Eine Methode kann lesen, schreiben, Anwendungen starten oder Dienste steuern. Der ursprüngliche Hinweis sicher lesend ist deshalb zu pauschal. Zugriff auf den eigenen Sessionbus braucht kein Root; Richtlinien des Zielbusses bleiben maßgeblich.
- Gelesene Primärquelle: [offizielles D-Bus-Handbuch zu dbus-send](https://dbus.freedesktop.org/doc/dbus-send.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine lokale Version ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Nachrichtenversand an Session-/Systembus und private Buslaufzeit nicht ausgeführt; praktische Prüfung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 253: `format: ok`.

## 254 – [dconf.md](../dconf.md)

- Inhalt: Direkte dconf-Werte und Offline-Kompilierung unterscheiden. `dconf` liest und verändert eine Einstellungsdatenbank. Es verwendet dabei nicht automatisch die Schema-/Typprüfungen von GSettings. Normale eigene Benutzereinstellungen brauchen kein Root, können aber sofort den Desktop beeinflussen. Hier wird nur eine neue separate Binärdatei kompiliert.
- Gelesene Primärquelle: [dconf-Projekthandbuch bei Debian](https://manpages.debian.org/trixie/dconf-cli/dconf.1.en.html)
- Lokaler Stand: Paket dconf-cli vorhanden; Programmversionsausgabe nicht ermittelt. Praktisch geprüft: Nur Offline-compile eigener Keyfiles erfolgreich; keine Installation der DB. Benutzer-/Systemprofil, Typsemantik, Buszugriff und Desktopwirkung nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 254: `format: ok`.

## 255 – [gio.md](../gio.md)

- Inhalt: GIO-Unterbefehle nach ihrer Wirkung auswählen. `gio` stellt Dateifunktionen der GLib/GIO-Bibliothek bereit. Einige Unterbefehle lesen, andere kopieren, löschen, mounten, starten Programme oder ändern Dateizuordnungen. Eigene lokale Dateien brauchen kein Root; GIO ist deshalb trotzdem nicht pauschal sicher lesend.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [offizielle GIO-Übersicht](https://docs.gtk.org/gio/overview.html), lokale Manpage
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Version, cat-Hilfe und cat eigener temporärer Datei mit local-VFS erfolgreich. Schreibende Unterbefehle, GVfs, Apps und entfernte URIs nicht praktisch geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 255: `format: ok`.

## 256 – [gio_cat.md](../gio_cat.md)

- Inhalt: Dateiinhalte mit gio cat lesen. Der Katalogname `gio-cat` bezeichnet hier den Unterbefehl **`gio cat`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 256: `format: ok`.

## 257 – [gio_copy.md](../gio_copy.md)

- Inhalt: Dateien mit gio copy gezielt kopieren. Der Katalogname `gio-copy` bezeichnet hier den Unterbefehl **`gio copy`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 257: `format: ok`.

## 258 – [gio_info.md](../gio_info.md)

- Inhalt: GIO-Metadaten gezielt abfragen. Der Katalogname `gio-info` bezeichnet hier den Unterbefehl **`gio info`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 258: `format: ok`.

## 259 – [gio_list.md](../gio_list.md)

- Inhalt: Verzeichniseinträge mit gio list auflisten. Der Katalogname `gio-list` bezeichnet hier den Unterbefehl **`gio list`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 259: `format: ok`.

## 260 – [gio_mime.md](../gio_mime.md)

- Inhalt: MIME-Zuordnungen mit GIO verstehen. Der eingefrorene Katalogname gio-mime wird als `gio mime` ausgeführt. Ohne zweites Argument werden Anwendungen zu einem MIME-Typ abgefragt; mit zweitem Argument wird die Standardanwendung geändert. Die Abfrage bestimmt nicht den Typ einer Datei.
- Gelesene Primärquelle: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html) und lokale Unterbefehlshilfe
- Lokaler Stand: gio / GLib 2.80.0. Praktisch geprüft: Nur Unterbefehlshilfe ausgeführt. Praktische Abfragen echter Zuordnungen, Setzen eines Handlers und Anwendungsstarts bleiben offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 260: `format: ok`.

## 261 – [gsettings.md](../gsettings.md)

- Inhalt: Schemaabhängige Einstellungen lesen und gezielt ändern. GSettings stellt typisierte Anwendungseinstellungen bereit. gsettings kann lesen, beobachten und schreiben; die ursprüngliche Einstufung als ausschließlich lesend ist falsch. Normale Einstellungen gehören zur Benutzersitzung, nicht zu Root.
- Gelesene Primärquelle: [GSettings-Handbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gsettings.1.en.html), [GSettings-Schemata](https://docs.gtk.org/gio/class.Settings.html) und lokale Manpage
- Lokaler Stand: GLib 2.80.0. Praktisch geprüft: Eigenes Schema kompiliert, Memory-Vorgabewert und Typ gelesen. Praktische Änderungen echter Einstellungen, D-Bus-Schreiben und Monitoring bleiben offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 261: `format: ok`.

## 262 – [kdialog.md](../kdialog.md)

- Inhalt: Dialoge in KDE-Shellskripten. kdialog zeigt KDE-/Qt-Dialoge und liefert je nach Dialog eine Antwort über Standardausgabe oder Exitstatus. Es ist kein allgemeiner Systemstatusbefehl. Grafische Sitzung und Dialogtyp bestimmen die benötigten Voraussetzungen.
- Gelesene Primärquelle: [KDE: Shell scripting with KDE dialogs](https://develop.kde.org/docs/administration/kdialog/)
- Lokaler Stand: Nicht praktisch geprüft; Programm nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Kein Funktionsaufruf ausgeführt.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 262: `format: ok`.

## 263 – [notify_send.md](../notify_send.md)

- Inhalt: Passive Desktopbenachrichtigungen senden. notify-send sendet eine Nachricht an den Benachrichtigungsdienst der Benutzersitzung. Es liest nicht bloß einen Status und zeigt keine verlässliche Bestätigungsfrage. Sichtbarkeit und Dauer entscheidet auch der Desktopdienst.
- Gelesene Primärquelle: [libnotify-Handbuch](https://manpages.debian.org/trixie/libnotify-bin/notify-send.1.en.html), [Freedesktop-Benachrichtigungsstandard](https://specifications.freedesktop.org/notification/latest/) und lokale Manpage
- Lokaler Stand: notify-send 0.8.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 263: `format: ok`.

## 264 – [xdg_mime.md](../xdg_mime.md)

- Inhalt: MIME-Typen und Standardanwendungen unterscheiden. xdg-mime kann Dateitypen und Standards abfragen, aber auch Zuordnungen ändern und Typbeschreibungen installieren. Abfrage, Standardhandler und MIME-Datenbank sind getrennte Aufgaben. Die pauschale Einstufung als lesend greift deshalb zu kurz.
- Gelesene Primärquelle: [xdg-utils: xdg-mime](https://portland.freedesktop.org/doc/xdg-mime.html) und lokale Manpage
- Lokaler Stand: xdg-mime 1.1.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 264: `format: ok`.

## 265 – [xdg_open.md](../xdg_open.md)

- Inhalt: Dateien über die bevorzugte Desktopanwendung öffnen. xdg-open übergibt eine Datei oder URL an die bevorzugte Anwendung der Sitzung. Es ist ein Programmstarter mit möglichen Folgeaktionen, kein rein lesender Dateibefehl.
- Gelesene Primärquelle: [xdg-utils: xdg-open](https://portland.freedesktop.org/doc/xdg-open.html) und lokale Manpage
- Lokaler Stand: xdg-open 1.1.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 265: `format: ok`.

## 266 – [xdg_settings.md](../xdg_settings.md)

- Inhalt: Desktopvorgaben abfragen, prüfen und setzen. xdg-settings vermittelt ausgewählte Eigenschaften der Desktopumgebung. get und check lesen beziehungsweise vergleichen; set verändert Vorgaben. Es ist keine universelle Schnittstelle für jede beliebige Desktopoption.
- Gelesene Primärquelle: [xdg-utils: xdg-settings](https://portland.freedesktop.org/doc/xdg-settings.html) und lokale Manpage
- Lokaler Stand: xdg-settings 1.1.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 266: `format: ok`.

## 267 – [zenity.md](../zenity.md)

- Inhalt: GTK-Dialoge und deren Antworten auswerten. zenity zeigt GTK-Dialoge für Shellskripte. Antworten kommen abhängig vom Dialogtyp über Standardausgabe oder Exitstatus zurück. Der Aufruf benötigt bei echter Dialognutzung eine passende grafische Sitzung.
- Gelesene Primärquelle: [Zenity-Projekthandbuch als Debian-Manpage](https://manpages.debian.org/trixie/zenity/zenity.1.en.html) und lokale Manpage; die früheren GNOME-help-URLs waren nicht erreichbar und sind kein verwendeter Inhaltsbeleg
- Lokaler Stand: zenity 4.0.1. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 267: `format: ok`.

## 268 – [as.md](../as.md)

- Inhalt: Assemblertext in eine Objektdatei übersetzen. GNU as übersetzt zielarchitekturspezifischen Assemblertext in Objektdateien. Es ist weder ein C-Compiler noch ein vollständiger Programmlinker. Die erzeugte .o-Datei wird hier nicht ausgeführt.
- Gelesene Primärquelle: [GNU-as-Überblick](https://sourceware.org/binutils/docs/as/Overview.html), [Aufrufoptionen](https://sourceware.org/binutils/docs/as/Invoking.html)
- Lokaler Stand: GNU as / Binutils 2.42, Target x86_64-linux-gnu. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 268: `format: ok`.

## 269 – [clang.md](../clang.md)

- Inhalt: C gezielt übersetzen und linken. clang ist ein Compilertreiber. Er steuert Vorverarbeitung, Übersetzung, Assemblierung und bei normalem Aufruf auch das Linken. Er erzeugt Dateien; ein Programmstart ist ein gesonderter Schritt.
- Gelesene Primärquelle: [Clang-Treiberhandbuch](https://clang.llvm.org/docs/CommandGuide/clang.html)
- Lokaler Stand: Nicht praktisch geprüft; clang ist nicht im PATH vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 269: `format: ok`.

## 270 – [clang_2.md](../clang_2.md)

- Inhalt: C++ gezielt übersetzen und linken. clang++ ist ein Compilertreiber. Er steuert Vorverarbeitung, Übersetzung, Assemblierung und bei normalem Aufruf auch das Linken. Er erzeugt Dateien; ein Programmstart ist ein gesonderter Schritt.
- Gelesene Primärquelle: [Clang-Treiberhandbuch](https://clang.llvm.org/docs/CommandGuide/clang.html) und [Clang-Benutzerhandbuch](https://clang.llvm.org/docs/UsersManual.html)
- Lokaler Stand: Nicht praktisch geprüft; clang++ ist nicht im PATH vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 270: `format: ok`.

## 271 – [cmake.md](../cmake.md)

- Inhalt: Buildsysteme erzeugen und getrennt bauen. CMake liest CMakeLists.txt, konfiguriert ein Projekt und erzeugt Dateien für ein gewähltes Buildsystem. Konfigurieren, Bauen, Testen und Installieren sind eigenständige Schritte. CMake ist selbst kein C-Compiler.
- Gelesene Primärquelle: [CMake-Aufrufhandbuch](https://cmake.org/cmake/help/latest/manual/cmake.1.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 271: `format: ok`.

## 272 – [g.md](../g.md)

- Inhalt: C++ gezielt übersetzen und linken. g++ ist ein Compilertreiber. Er steuert Vorverarbeitung, Übersetzung, Assemblierung und bei normalem Aufruf auch das Linken. Er erzeugt Dateien; ein Programmstart ist ein gesonderter Schritt.
- Gelesene Primärquelle: [GCC: C++ übersetzen](https://gcc.gnu.org/onlinedocs/gcc/Invoking-G_002b_002b.html) und [GCC-Ausgabestufen](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)
- Lokaler Stand: g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1). Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 272: `format: ok`.

## 273 – [gcc.md](../gcc.md)

- Inhalt: C gezielt übersetzen und linken. gcc ist ein Compilertreiber. Er steuert Vorverarbeitung, Übersetzung, Assemblierung und bei normalem Aufruf auch das Linken. Er erzeugt Dateien; ein Programmstart ist ein gesonderter Schritt.
- Gelesene Primärquelle: [GCC-Ausgabestufen](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html), [C-Sprachmodi](https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html), [Diagnoseoptionen](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)
- Lokaler Stand: gcc 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1). Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 273: `format: ok`.

## 274 – [gdb.md](../gdb.md)

- Inhalt: Eigene Programme mit GNU GDB untersuchen. GDB ist ein Debugger. Er liest Symbole, kann Programme starten und anhalten, Speicher ändern und Funktionen aufrufen. Er ist deshalb kein grundsätzlich passiver Analysebefehl.
- Gelesene Primärquelle: [GDB-Modusoptionen](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Mode-Options.html), [Beispielsitzung](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), [Auto-load-Sicherheitsgrenze](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Auto_002dloading-safe-path.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 274: `format: ok`.

## 275 – [git.md](../git.md)

- Inhalt: Versionen und Änderungen mit Git unterscheiden. Git verwaltet lokale Versionsgeschichte und kann sie mit anderen Repositories austauschen. Sein Verhalten hängt vollständig vom Unterbefehl ab: diff ist eine Ansicht, commit schreibt Geschichte und push überträgt sie. Git ist nicht pauschal lesend.
- Gelesene Primärquelle: [Git-Handbuch](https://git-scm.com/docs/git), [git-diff](https://git-scm.com/docs/git-diff)
- Lokaler Stand: git 2.43.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 275: `format: ok`.

## 276 – [gitk.md](../gitk.md)

- Inhalt: Git-Geschichte grafisch durchsuchen. gitk ist ein grafischer Browser für Git-Repositories. Er stellt Commitgraphen, Commitinformationen und Änderungen dar. Es handelt sich um ein zusätzliches Tcl/Tk-Werkzeug, nicht um einen im Browser geöffneten GitHubdienst.
- Gelesene Primärquelle: [Git-Projekthandbuch: gitk](https://git-scm.com/docs/gitk)
- Lokaler Stand: Nicht praktisch geprüft; Programm nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Kein Funktionsaufruf ausgeführt.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 276: `format: ok`.

## 277 – [go.md](../go.md)

- Inhalt: Go-Quellen bauen und ausführen. go ist die Werkzeugoberfläche der Go-Toolchain. Unterbefehle bauen, testen, formatieren, starten oder verwalten Abhängigkeiten. Besonders run und test führen Code aus; get ist kein allgemeiner Nur-Leseaufruf.
- Gelesene Primärquelle: [Go-Werkzeughandbuch](https://pkg.go.dev/cmd/go)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 277: `format: ok`.

## 278 – [gradle.md](../gradle.md)

- Inhalt: Projektaufgaben mit Gradle ausführen. Gradle wertet Buildlogik aus und führt daraus gebildete Tasks aus. Buildskripte sind ausführbarer Groovy- oder Kotlin-Code. Selbst eine Aufgabenliste ist deshalb keine garantiert passive Dateianalyse.
- Gelesene Primärquelle: [Gradle-Aufrufhandbuch](https://docs.gradle.org/current/userguide/command_line_interface.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 278: `format: ok`.

## 279 – [hg.md](../hg.md)

- Inhalt: Verteilte Versionsverwaltung mit Mercurial. hg ist die Kommandooberfläche von Mercurial. Ein Repository enthält lokale Changesets; der Arbeitsordner enthält die bearbeitete Fassung. Lesen, Versionswechsel, Aufzeichnen und Übertragen sind verschiedene Unterbefehle mit unterschiedlichen Risiken.
- Gelesene Primärquelle: [Mercurial-Befehlshandbuch](https://www.mercurial-scm.org/help/commands), [status](https://www.mercurial-scm.org/help/commands/status) und [pull](https://www.mercurial-scm.org/help/commands/pull)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 279: `format: ok`.

## 280 – [jar.md](../jar.md)

- Inhalt: Java-Archive anlegen und ihren Inhalt lesen. jar erstellt, listet, verändert und entpackt JAR-Archive. Ein JAR beruht auf ZIP und kann Klassen sowie Ressourcen enthalten. Eine Archivliste führt die enthaltenen Java-Klassen nicht aus.
- Gelesene Primärquelle: [JDK-21-Werkzeughandbuch: jar](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jar.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 280: `format: ok`.

## 281 – [java.md](../java.md)

- Inhalt: Java-Anwendungen in der JVM starten. java startet eine Java Virtual Machine und führt Anwendungscode aus. Der Klassenstart, der JAR-Start und der Quelldateimodus sind unterschiedliche Aufrufformen. Eine JVM ist keine Sicherheitsisolation für unbekannte Programme.
- Gelesene Primärquelle: [JDK-21-Launcherhandbuch](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 281: `format: ok`.

## 282 – [javac.md](../javac.md)

- Inhalt: Java-Quelltext in Klassen übersetzen. javac kompiliert Java-Quellen in .class-Dateien für die JVM. Es startet das fertige Anwendungsprogramm nicht automatisch. Ein JDK mit Compiler und eine bloße Laufzeitinstallation sind zu unterscheiden.
- Gelesene Primärquelle: [JDK-21-Compilerhandbuch](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 282: `format: ok`.

## 283 – [ld.md](../ld.md)

- Inhalt: Objektdateien mit dem GNU-Linker verbinden. ld verbindet Objektdateien und Archive, ordnet Sektionen und löst Symbolbezüge auf. Es kann ausführbare Programme, gemeinsame Bibliotheken oder weitere verschiebbare Objekte erzeugen. Das Linkergebnis wird nicht automatisch gestartet.
- Gelesene Primärquelle: [GNU-ld-Aufruf](https://sourceware.org/binutils/docs/ld/Invocation.html) und [Optionen](https://sourceware.org/binutils/docs/ld/Options.html)
- Lokaler Stand: GNU ld / Binutils 2.42; Hilfscompiler gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 283: `format: ok`.

## 284 – [ldd.md](../ldd.md)

- Inhalt: Dynamische Bibliotheksabhängigkeiten nachvollziehen. ldd zeigt benötigte Shared Libraries und ihre Auflösung durch den Laufzeitlinker. Es ist kein allgemeiner sicherer Scanner für unbekannte Programme. Die Originaleinstufung als sicher lesend wird wegen möglicher Codeausführung korrigiert.
- Gelesene Primärquelle: [Linux-man-pages: ldd](https://man7.org/linux/man-pages/man1/ldd.1.html) und lokale Manpage
- Lokaler Stand: ldd / glibc 2.39 (Ubuntu 2.39-0ubuntu8.9); gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 284: `format: ok`.

## 285 – [lldb.md](../lldb.md)

- Inhalt: Eigene Programme mit LLDB untersuchen. LLDB ist der Debugger des LLVM-Projekts. Er kann Symbole lesen, Prozesse starten oder übernehmen und deren Zustand verändern. Seine Befehle sind nicht durchgehend mit GDB austauschbar.
- Gelesene Primärquelle: [LLDB-Aufrufhandbuch](https://lldb.llvm.org/man/lldb.html) und [LLDB-Tutorial](https://lldb.llvm.org/use/tutorial.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 285: `format: ok`.

## 286 – [make.md](../make.md)

- Inhalt: Abhängigkeiten und Bauaktionen mit GNU Make steuern. Make entscheidet anhand von Regeln und Dateizeitstempeln, welche Ziele neu erzeugt werden sollen. Die zugehörigen Rezepte sind echte Shellbefehle. Make ist nicht auf Compiler beschränkt und kein passiver Projektprüfer.
- Gelesene Primärquelle: [GNU-Make-Handbuch als Projektmanpage](https://manpages.debian.org/trixie/make/make.1.en.html) und lokale Manpage; die GNU-HTML-Unterseiten waren beim Abruf nicht erreichbar
- Lokaler Stand: GNU Make 4.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 286: `format: ok`.

## 287 – [mvn.md](../mvn.md)

- Inhalt: Maven-Phasen und Plugingoals gezielt wählen. mvn startet Apache Maven. Es liest das Projektmodell pom.xml und führt Phasen oder Plugingoals aus. validate ist eine Phase und keine garantierte reine XML-Syntaxprüfung eines beliebigen Projekts.
- Gelesene Primärquelle: [Maven-Lebenszyklus](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html) und [Maven-3.9-CLI](https://maven.apache.org/ref/3.9.11/maven-embedder/cli.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 287: `format: ok`.

## 288 – [ninja.md](../ninja.md)

- Inhalt: Explizite Buildregeln mit Ninja ausführen. Ninja führt einen vorgegebenen Abhängigkeitsgraphen aus build.ninja aus. Solche Dateien werden häufig von CMake oder anderen Generatoren erzeugt. Die darin genannten Kommandos sind echte Programme mit Benutzerrechten.
- Gelesene Primärquelle: [Ninja-Projekthandbuch](https://ninja-build.org/manual.html)
- Lokaler Stand: Ninja 1.11.1. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 288: `format: ok`.

## 289 – [nm.md](../nm.md)

- Inhalt: Symbole in Objektdateien und Bibliotheken lesen. GNU nm listet Symbole aus Objektdateien, Archiven und geeigneten Programmen. Es zeigt unter anderem Definitionen und noch offene Bezüge. Die Datei wird dabei nicht als Programm gestartet.
- Gelesene Primärquelle: [GNU-Binutils: nm](https://sourceware.org/binutils/docs/binutils/nm.html)
- Lokaler Stand: GNU nm / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 289: `format: ok`.

## 290 – [node.md](../node.md)

- Inhalt: JavaScript mit Node.js prüfen und starten. node führt JavaScript außerhalb des Browsers aus. Node.js stellt unter anderem Datei-, Prozess- und Netzwerkschnittstellen bereit. Es ist deshalb kein bloßer Textbetrachter und keine Browser-Sandbox.
- Gelesene Primärquelle: [Node.js-Aufrufhandbuch](https://nodejs.org/api/cli.html); die aktuelle Webfassung beschreibt eine neuere Hauptversion als der lokale Test. Die Version-22-spezifische URL war nicht erreichbar; lokale Nachweise gelten nur für die ausgeführten Optionen
- Lokaler Stand: Node.js v22.23.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 290: `format: ok`.

## 291 – [objdump.md](../objdump.md)

- Inhalt: Binärstrukturen und Maschinenbefehle statisch lesen. GNU objdump zeigt Strukturen unterstützter Objektformate und kann Maschinenbefehle disassemblieren. Es startet das untersuchte Programm nicht. Zum sinnvollen Aufruf gehört eine ausdrückliche Auswahl der gewünschten Ansicht.
- Gelesene Primärquelle: [GNU-Binutils: objdump](https://sourceware.org/binutils/docs/binutils/objdump.html)
- Lokaler Stand: GNU objdump / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 291: `format: ok`.

Nachprüfung 291 vor Abschluss 292: objdump 2.42 meldete do-not-use-debuginfod als unbekannte Debugoption trotz Exitstatus 0. Option aus dem Beispiel entfernt; korrigierten gesamten Bashblock erneut ohne stderr und mit Status 0 ausgeführt. Lokale Hilfe bestätigt no-follow-links. Einzelstrukturprüfung 291 erneut bestanden.

## 292 – [perl.md](../perl.md)

- Inhalt: Perl-Skripte und kontrollierte Textfilter verwenden. perl startet den Perl-Interpreter. Er kann vollständige Programme oder kurze Textfilter ausführen. Auch ein scheinbarer Prüfmodus kann bereits Code während der Kompilierphase ausführen.
- Gelesene Primärquelle: [Perl-Porters: perlrun](https://perldoc.perl.org/perlrun)
- Lokaler Stand: Perl 5.38.2. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 292: `format: ok`.

## 293 – [python.md](../python.md)

- Inhalt: Den unversionierten Python-Aufruf richtig einordnen. python ist ein unversionierter Interpretername. Je nach Distribution und Umgebung kann er Python 3, historisch Python 2 oder gar kein Programm bezeichnen. Ein vorhandenes python3 beweist nicht, dass auch python verfügbar ist.
- Gelesene Primärquelle: [Python-Projekt: PEP 394](https://peps.python.org/pep-0394/) und [CPython-3-Aufrufhandbuch](https://docs.python.org/3/using/cmdline.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 293: `format: ok`.

## 294 – [python3.md](../python3.md)

- Inhalt: Python-3-Skripte kontrolliert ausführen. python3 startet einen Python-3-Interpreter. Skript-, Modul-, Standardinput- und Ausdrucksmodus führen Code aus. Eine separate Bytecodekompilierung prüft andere Eigenschaften als ein tatsächlicher Programmlauf.
- Gelesene Primärquelle: [CPython-3.12-Aufrufhandbuch](https://docs.python.org/3.12/using/cmdline.html) und [py_compile](https://docs.python.org/3.12/library/py_compile.html)
- Lokaler Stand: CPython 3.12.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 294: `format: ok`.

## 295 – [python3_config.md](../python3_config.md)

- Inhalt: C-Buildparameter einer Python-Installation lesen. python3-config gibt Compiler-, Linker- und ABI-Informationen der zugehörigen Python-Installation aus. Es kompiliert kein Programm und installiert keine Pakete. Der Name garantiert nicht die Übereinstimmung mit jeder anderen Python-Installation im PATH.
- Gelesene Primärquelle: [CPython: Einbettung und Linkparameter](https://docs.python.org/3.12/extending/embedding.html#compiling-and-linking-under-unix-like-systems), [Debian-python3-config-Handbuch](https://manpages.debian.org/trixie/python3-dev/python3-config.1.en.html) und lokale Hilfe. Die alten pauschalen Buildbeispiele der Debian-Manpage werden nicht übernommen
- Lokaler Stand: python3-config mit CPython-3.12-Flags; kein eigener --version-Schalter. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 295: `format: ok`.

## 296 – [ranlib.md](../ranlib.md)

- Inhalt: Symbolindex eines Objektarchivs erzeugen. GNU ranlib schreibt einen Symbolindex in ein bestehendes ar-Archiv. Damit ist der normale Aufruf schreibend. Es erzeugt keine einzelnen Objektdateien und keine fertig gelinkte Anwendung.
- Gelesene Primärquelle: [GNU-Binutils: ranlib](https://sourceware.org/binutils/docs/binutils/ranlib.html) und [ar](https://sourceware.org/binutils/docs/binutils/ar.html)
- Lokaler Stand: GNU ranlib / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 296: `format: ok`.

## 297 – [readelf.md](../readelf.md)

- Inhalt: ELF-Header, Sektionen und Symbole lesen. readelf zeigt Strukturen von ELF-Dateien und Archiven mit ELF-Mitgliedern. Es führt das Zielprogramm nicht aus und arbeitet unabhängig von der BFD-Bibliothek, die andere Binutils-Werkzeuge verwenden.
- Gelesene Primärquelle: [GNU-Binutils: readelf](https://sourceware.org/binutils/docs/binutils/readelf.html)
- Lokaler Stand: GNU readelf / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 297: `format: ok`.

## 298 – [ruby.md](../ruby.md)

- Inhalt: Ruby-Programme prüfen und ausführen. ruby startet die Ruby-Laufzeit. Sie kann Skripte, Standardinput oder direkt angegebenen Code verarbeiten. -c prüft Syntax; der normale Programmstart ist davon zu trennen.
- Gelesene Primärquelle: [Ruby-Projekt: Aufrufoptionen](https://docs.ruby-lang.org/en/3.4/ruby/options_md.html) und lokale Hilfe; Webfassung 3.4 und lokaler Test 3.2 sind getrennt ausgewiesen
- Lokaler Stand: Ruby 3.2.3, Revision 52bb2ac0a6, x86_64-linux-gnu. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 298: `format: ok`.

## 299 – [rustc.md](../rustc.md)

- Inhalt: Rust-Quelltext mit festgelegter Edition übersetzen. rustc ist der Rust-Compiler. Er übersetzt eine Crate und kann Programme, Bibliotheken oder Zwischenformate erzeugen. Cargo ist die darüberliegende Projekt-/Abhängigkeitsverwaltung und nicht mit rustc gleichzusetzen.
- Gelesene Primärquelle: [Rust-Projekt: rustc-Aufrufargumente](https://doc.rust-lang.org/rustc/command-line-arguments.html)
- Lokaler Stand: Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 299: `format: ok`.

## 300 – [strip.md](../strip.md)

- Inhalt: Symbol- und Debugdaten gezielt entfernen. GNU strip entfernt Symbole oder Debuginformationen aus Binärdateien und Archiven. Ohne eigenes Ausgabeziel verändert es die angegebenen Dateien. Die ursprüngliche pauschale Einstufung als sicher lesend ist daher falsch.
- Gelesene Primärquelle: [GNU-Binutils: strip](https://sourceware.org/binutils/docs/binutils/strip.html)
- Lokaler Stand: GNU strip / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 300: `format: ok`.

## Ergänzender Abgleich des Prüfstands

Die aufsteigende Erstbearbeitung ist bis 300 abgeschlossen. Im abschließenden Abgleich wurden die Prüfstandsangaben von 215 (dumpe2fs) und 216 (e2fsck) ergänzt: Bei ihrer Erstbearbeitung waren ihre Erklärungsmuster nicht ausgeführt. Spätere zulässige Abbildübungen verwendeten dumpe2fs 1.47.0 als lesendes Hilfswerkzeug (229–231, 242, 250) und e2fsck 1.47.0 mit -f -n am eigenen frischen ext2-Abbild (242). Diese begrenzten Nachweise werden jetzt direkt in den beiden Dokumenten mit Querverweisen ausgewiesen; sie sind keine Geräte- oder Reparaturtests. Beide Einzelstrukturprüfungen anschließend erneut bestanden.

## Abschluss und Übergabe nach 300

- Vollständig vorhanden: 90 neue Dokumente für 211–300, mit unveränderten Katalogkennungen, Namen, Kategorien und Dateinamen. Der Bericht enthält die lückenlose Reihenfolge 211 bis 300. Nach 300 wurde kein weiterer Datensatz begonnen.
- Quellen: je Dokument tatsächlich gelesene Primärhandbücher verlinkt; lokale Hilfe/Manpages und Unterschiede zur Webversion benannt. Fehlgeschlagene Quellenabrufe sind keine Inhaltsbelege. Die Ersatzquellen sind im jeweiligen Dokument ausgewiesen.
- Praktische Nachweise: 37 Einträge mit ausgeführten eigenen Abschnitt-5-Funktionsbeispielen; zusätzlich zwei nur als Hilfswerkzeuge in späteren Übungen geprüfte Einträge (215/216). Sechs weitere Einträge (260, 263–267) haben ausschließlich einen Hilfe-/Versionsaufruf als lokalen Nachweis. Bei 45 Einträgen erfolgte keine Funktionsausführung. Auch bei ausgeführten Minimalbeispielen bleiben andere Modi, Versionen und reale Einsatzbedingungen offen. Die konkreten Grenzen stehen pro Datei; bloße Hilfe wird nicht als Desktopfunktionstest gezählt.
- Ausführungsumfang: ausschließlich eigene temporäre Dateien, kleine Abbilder und selbst geschriebene Quellen. Keine realen Geräte geöffnet oder verändert, keine Mounts/Loop-Zuordnungen, Swapaktivierungen, Konten-/Dienst-/Systemänderungen, echten Dateizuordnungsänderungen, Dialoge oder Benachrichtigungen. Keine Pakete oder Toolchains installiert, keine Netzwerkanfragen als Beispielnachweis. Offizielle Quellenrecherche erfolgte getrennt davon.
- Struktur: jede Datei nach Fertigstellung einzeln geprüft. Anschließender Gesamtlauf 211–300: 90 von 90 `format: ok`. Alle 52 Bashblöcke einschließlich der ausdrücklich unausgeführten Muster mit bash -n geprüft. Das bestätigt Shellsyntax, nicht Funktionsfähigkeit fehlender Programme.
- Vorhandene Übergabetests: `python3 -m pytest -q tests/test_linux_command_docs_handoff.py` → 31 bestanden. Sie prüfen Übergabestruktur, Katalog/CSV-Zuordnung, Parser und Herkunftserhalt; keine fachliche Freigabe und kein GUI-/Gerätefunktionsnachweis.
- Umfangskontrolle: genau 90 neue Befehlsdokumente und dieser neue Bericht; als einzige Änderung an einer bereits versionierten Datei die angeforderte Abschlusskorrektur im Bericht 201–210. Original-CSV, Katalog, Entwurfsoriginale, korrigierte Dokumente 201–210, AGENTS, Muster, Code, Tests und zentraler Index unverändert.
- Historischer Git-Stand vor der anschließenden ausdrücklichen Commit-/Push-Freigabe: Basis und HEAD bleiben `135b1097382b42d5b9a90e78241dcff9c388b1f2`; Stagingindex leer. Für diesen Auftrag keine Commits, Pushes oder Merges. Änderungen liegen ausschließlich in der genannten separaten Arbeitskopie zur gemeinsamen Prüfung bereit.

**Stopp nach Datensatz 300.** Fachliche Review und die ausdrücklich offenen praktischen Punkte bleiben der gemeinsamen Prüfung vorbehalten. Eine spätere reale Systemausführung ist hieraus nicht freigegeben.

## Abschließende Gesamtprüfung und autorisierte Veröffentlichung

Der anschließende Nutzerauftrag erlaubt ausdrücklich Commit und Push ausschließlich der neuen Dokumente 211–300 und der zugehörigen eigenen Fortschrittsberichte auf `codex/linux-docs-browser-handoff-20261113`. Die bisherigen Aussagen zum uncommitteten Übergabestand beschreiben den Zeitpunkt vor dieser Freigabe. Die Dokumentationen 201–210 selbst werden bei dieser Veröffentlichung nicht erneut verändert.

- Gesamtprüfung erneut ausgeführt: `python3 scripts/check_linux_command_docs.py --documents docs/linux-befehlsdatenbank --first 201 --last 300` → alle 100 Dokumente mit `format: ok`. Geprüft werden unter anderem Kennung, Name, Kategorie, Dateiname, Datensatznummer, Originalquellenbezug, Frontmatter und die zehn Hauptabschnitte. Der eingefrorene Katalog wurde gegen die unveränderte Original-CSV mit 713 Datensätzen und deren SHA-256 geprüft.
- Vorhandene vorgeschriebene Tests erneut ausgeführt: `python3 -m pytest -q tests/test_linux_command_docs_handoff.py` → 31 bestanden. Keine Geräte-/GUI-Beispiele oder Projektanwendungen hierfür gestartet. Diese Tests sind kein fachlicher oder realer Systemfunktionsnachweis.
- Vorgesehener Commitumfang: exakt 90 neue Befehlsdokumente, dieser neue Bericht und die bereits angeforderte Aktualisierung des eigenen Berichts 201–210; insgesamt 92 Dateien. Keine fremden Dateien, kein zentraler Index, kein Code, keine Tests und keine Originale.
- Vor dem Commit abgefragter Remotezweig: `135b1097382b42d5b9a90e78241dcff9c388b1f2`. Die Sandbox-DNS-Grenze erforderte die freigegebene Netzwerkabfrage außerhalb der Sandbox. Der Push erfolgt ohne Force auf genau den genannten Zweig; kein Merge nach main.
- Offene Prüfpunkte bleiben unverändert: fachliche gemeinsame Review; die einzeln benannten nicht ausgeführten Beispiele, fehlenden Programme, realen Geräte-/Mount-/Reparaturfälle und Desktop-/Sitzungswirkungen; außerdem andere Versionen und Plattformen. Bei 201–210 bleiben insbesondere die dokumentierten praktischen Grenzen von updatedb sowie badblocks/blkid bestehen. Hilfe-/Versionsaufrufe werden nicht als Funktionsprüfung gewertet.

Die zugehörige Commit-ID und das tatsächlich bestätigte Push-Ergebnis werden in der Rückmeldung zur Veröffentlichung genannt; die Commit-ID kann nicht als eigener Inhalt desselben Commits festgeschrieben werden.
