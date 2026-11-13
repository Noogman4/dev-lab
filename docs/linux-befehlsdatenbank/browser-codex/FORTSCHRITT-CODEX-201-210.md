# Prüfung der Dokumentationen 201–210

Prüfdatum: 2026-11-13. Basis: Branch `codex/linux-docs-browser-handoff-20261113`, Commit `7cbfb86536a2088e58690932023f410cc5fe20b8`. Getrennte Arbeitskopie: `/tmp/linux-docs-review-201-210-20261113`; der bestehende lokale `main`-Arbeitsstand wurde nicht verändert.

Gelesen: beide geltenden AGENTS.md, Startauftrag, PROMPT, Muster 7z/tar, Reviewhinweise, eingefrorener Katalog, jeweilige Originaldatensätze und Entwürfe, tatsächlicher Parser sowie Prüfcode. Original-CSV: 713 Datensätze; SHA-256 `40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`. Quellenprüfung und praktische Prüfung werden unten getrennt ausgewiesen. Keine Paketinstallationen oder Geräte-, System- und Netzwerkaktionen zum Nachweis von Beispielen.

## 201 – touch.md

- Korrigiert: Referenzmetadaten benötigen nicht pauschal Inhaltsleserecht; Rechte für Neuanlage, beide Zeiten auf jetzt und explizite Zeitsetzung unterschieden. Eigentümerschaft kann genügen. Elf Bytes Testinhalt einschließlich Zeilenumbruch durch Ausführung bestätigt. Zeitstempel, Links und Folgen für Builds vertieft.
- Gelesene Quellen: [GNU-touch-Manpage, Debian coreutils 9.7](https://manpages.debian.org/trixie/coreutils/touch.1.en.html), [utimensat](https://man7.org/linux/man-pages/man2/utimensat.2.html), lokale Manpage coreutils 9.4. GNU-Webmanual nicht als gelesen behauptet: Abruf schlug fehl.
- Praktisch: `touch (GNU coreutils) 9.4`; gesamter Abschnitt 5 ausgeführt. Zusätzliche Assertions für Neuanlage, Inhaltserhalt, getrennte atime/mtime, `-c`, `-r` von Modus-000-Referenz, eigene Modus-000-Zieldatei und `-h` ohne Zieländerung; UID 1000, ausschließlich eigene temporäre Dateien. Erfolgreich.
- Strukturprüfung 201: `format: ok`. Offen: andere Eigentümer/Privilegien, besondere Dateiattribute und Dateisysteme, andere Versionen.

## 202 – tree.md

- Korrigiert: `Projekt/docs/info.txt` liegt auf Ebene 2. Vergleich jetzt `-L 1` gegen `-L 2`; Filter, verborgene Namen, Zählungsgrenzen und schreibende Sonderoptionen vertieft.
- Gelesen: [Projekt-Manpage bei Debian 2.2.1](https://manpages.debian.org/trixie/tree/tree.1.en.html), lokale Manpage 2.1.1.
- Praktisch: `tree v2.1.1`; kompletter Abschnitt 5 ausgeführt. Ausgaben zusätzlich per Assertions auf Ebenen, `.intern`, Verzeichnisfilter und `-P '*.txt'` mit weiterhin sichtbarem `src` geprüft. Erfolgreich.
- Strukturprüfung 202: `format: ok`. Offen: Linkverfolgung, Dateisystemgrenzen, Dateiausgabe, große Bäume, 2.2.1.

## 203 – truncate.md

- Vertieft: Byte- statt Zeichengrenzen, Sparse-Länge gegen Belegung, Größenoperatoren und Einheiten, `-c` schützt nur vor Neuanlage, `-r` kopiert keinen Inhalt. Vergrößern nach Abschneiden stellt alte Daten nicht wieder her.
- Gelesen: [GNU-truncate-Manpage bei Debian 9.7](https://manpages.debian.org/trixie/coreutils/truncate.1.en.html), lokale Manpage 9.4.
- Praktisch: `truncate (GNU coreutils) 9.4`; Abschnitt 5 komplett ausgeführt. Acht auf vier und wieder acht Bytes; `od` bestätigte `ABCD` plus vier Nullbytes. Referenzgrößen-Datei enthielt ausschließlich Nullbytes; `-c` legte nichts an. Erfolgreich.
- Strukturprüfung 203: `format: ok`. Offen: relative Größen/Rundung, `-o`, große Dateien, andere Dateisysteme und aktive Anwendungen.

## 204 – unlink.md

- Vertieft: genau ein Operand, Symlink gegen Hardlink, Linkzahl, offene Zugriffe, Elternverzeichnisrechte, keine physische Löschgarantie. Destruktive Einstufung beibehalten.
- Gelesen: [GNU-unlink-Manpage bei Debian](https://manpages.debian.org/trixie/coreutils/unlink.1.en.html), [unlink(2)](https://man7.org/linux/man-pages/man2/unlink.2.html) sowie lokale Manpages.
- Praktisch: `unlink (GNU coreutils) 9.4`; Abschnitt 5 mit ausschließlich neu angelegten Übungseinträgen ausgeführt. Ziel blieb nach Entfernen des Symlinks erhalten; gleiche Inode und Linkanzahl 2 vor, Linkanzahl 1 nach Entfernen des zweiten Hardlink-Namens. Erfolgreich.
- Strukturprüfung 204: `format: ok`. Offen: letzter Name mit offenem Deskriptor, besondere Berechtigungen, Netzdateisysteme und Wiederherstellung.

## 205 – updatedb.md

- Ergänzt: vollständiger privater Ablauf einschließlich `plocate -d` und `-e`, erwarteter absoluter Testdateipfad, `LOCATE_PATH=` gegen zusätzliche Datenbanken, gezielte Pruning-Overrides ausschließlich unter eigener `-U`-Quelle; Sichtbarkeitsflag gegen tatsächliche Verzeichnis-/DB-Rechte abgegrenzt.
- Gelesen: [updatedb](https://manpages.debian.org/trixie/plocate/updatedb.8.en.html), [updatedb.conf](https://manpages.debian.org/trixie/plocate/updatedb.conf.5.en.html), [plocate](https://manpages.debian.org/trixie/plocate/plocate.1.en.html), jeweils Debian-Paket 1.1.23.
- Lokal: Verfügbarkeit geprüft; `updatedb`, `locate`, `plocate` fehlen. Keine Version erfunden, kein Index aufgebaut, keine Suche ausgeführt und keine Pakete installiert. Vollständiger Abschnitt 5 mit `bash -n` geprüft; Shellsyntax erfolgreich. Dies ist ausdrücklich kein Funktionstest.
- Strukturprüfung 205: `format: ok`. Praktische Prüfung offen: gesamter Aufbau und Suche mit tatsächlicher plocate-Installation; erwartete Ausgaben sind gekennzeichnet.

## 206 – vdir.md

- Vertieft: GNU-Vorgabe entspricht `ls -l -b`; lange Listenfelder, logische Größe gegenüber Blocksumme, `-A`, `-d`, numerische Kennungen und Link-/Zielmetadaten nachvollziehbar erklärt.
- Gelesen: [GNU-vdir-Manpage bei Debian](https://manpages.debian.org/trixie/coreutils/vdir.1.en.html), lokale Manpage und GNU-Info `vdir invocation`.
- Praktisch: `vdir (GNU coreutils) 9.4`; Abschnitt 5 vollständig ausgeführt. Rechte `640`, fünf Bytes, Punktname, Verzeichnis selbst und `-L`-Vergleich bestätigt; Testinhalt erhalten. Erfolgreich.
- Strukturprüfung 206: `format: ok`. Offen: ACLs/Sicherheitskontexte, große Rekursion, andere Locale-Einstellungen und besondere Dateitypen.

## 207 – watch.md

- Korrigiert/vertieft: Unterbefehl bestimmt Nebenwirkungen; `sh -c` gegenüber direktem `-x`, doppelte Optionsgrenzen, sichtbare Ausgabegrenzen; `-e` friert in dieser Version ein und wartet auf Tastendruck. Zeitlich überschaubares konstantes Beispiel mit `-q 2`.
- Gelesen: [procps-ng-Manpage bei Debian](https://manpages.debian.org/trixie/procps/watch.1.en.html), lokale Hilfe und Manpage.
- Praktisch: `watch from procps-ng 4.0.4`; gesamter Abschnitt 5 mit `TERM=xterm` in eigenem Pseudoterminal. Fünf Bytes der eigenen Datei mit Leerzeichen im Namen angezeigt; automatische Beendigung nach zwei unveränderten Folgezyklen, Status 0 und Inhalt `Test` danach bestätigt. Erfolgreich.
- Strukturprüfung 207: `format: ok`. Offen: Ctrl+C, Hervorhebung/Änderungsende, Fehler-Einfrieren, präziser Modus, Resize und andere Implementierungen.

## 208 – xargs.md

- Korrigiert: GNU-Standard führt bei leerer Eingabe einmal aus; erst `-r` unterdrückt den Aufruf. Vertieft: NUL-Grenzen, feste Formate, Optionsgrenzen beim Ziel, Aufteilungskonflikte, Größen-/Parallelitätsgrenzen und Rückgabewerte.
- Gelesen: [GNU-xargs-Manpage bei Debian](https://manpages.debian.org/trixie/findutils/xargs.1.en.html), lokale Manpage findutils 4.9.0. GNU-Webkapitel zur Dateinamenbehandlung war nicht abrufbar und wird nicht als gelesen behauptet.
- Praktisch: `xargs (GNU findutils) 4.9.0`; Abschnitt 5 vollständig erfolgreich. Zusatzassertions für Leerzeichen, Zeilenumbruch, Anführungszeichen, Rückstrich und führenden Bindestrich sowie leere Eingabe mit/ohne `-r` erfolgreich. Beim ersten Zusatztest enthielt das Python-Testargument irrtümlich ein echtes NUL-Byte; Python lehnte den Start ab. Mit wörtlichem printf-Escape erneut geprüft und bestanden; kein Dokumentationsbefehl war davon betroffen.
- Strukturprüfung 208: `format: ok`. Offen: Parallelität, `-I`, interaktive Rückfrage, Größenlimits und Fehlerpfade von Zielprogrammen.

## 209 – badblocks.md

- Vertieft: Standard-/`-n`-/`-w`-Modi, Blocknummern statt Byteadressen, Größenabhängigkeit und Bezug auf das geöffnete Objekt, getrennte Ausgabekanäle, unvollständige Listen mit `-e`/`-i`, Bedeutung von `-p`, Mustervergleich und Schutzschalter.
- Gelesen: [e2fsprogs-Handbuch bei Debian 1.47.2](https://manpages.debian.org/trixie/e2fsprogs/badblocks.8.en.html), lokale Manpage 1.47.0. Lokale Paketmetadaten: `e2fsprogs 1.47.0-2.4~exp1ubuntu4.1`; keine ausgeführte badblocks-Version behauptet.
- Praktisch: nur Dokumentationslesen und Nachrechnung `17*1024=17408`, `17*4096=69632`. Kein badblocks-Prozess, kein Gerätezugriff, kein Scan, kein Testmuster geschrieben. Fehlerliste 17/300 ist ausdrücklich erfundenes Erklärungsmuster.
- Strukturprüfung 209: `format: ok`. Praktische Geräteprüfung sämtlicher Modi, Ausgabe eines echten Scans und Dateisystemintegration bleiben offen.

## 210 – blkid.md

- Korrigiert: Low-Level-Probe benötigt mindestens einen Geräteoperanden. Vertieft: Standard-/Probe-Modus, unprivilegierte Cachewerte, leere Filterausgabe trotz Status 0, Status 0/2/4/8, UUID gegen Hardware-/Partitionsidentität, Ausgabeformate und nicht interpretierbare Fremddaten. `-c /dev/null` verhindert keinen Gerätezugriff.
- Gelesen: [Debian-Handbuch util-linux 2.41.5](https://manpages.debian.org/trixie/util-linux/blkid.8.en.html), [offizielles util-linux-Quellhandbuch](https://kernel.googlesource.com/pub/scm/utils/util-linux/util-linux/+/master/misc-utils/blkid.8.adoc), lokale Manpage 2.39.3. Entwicklungsstand `master` ausdrücklich von lokaler Version abgegrenzt.
- Praktisch: ausschließlich `blkid --help` und `blkid --version`. Gemeldet: `blkid from util-linux 2.39.3 (libblkid 2.39.3, 04-Dec-2023)`. Keine Geräteinventur, Probe, Cachebereinigung oder Systemaktion. Sämtliche Kennungs- und Exportausgaben sind Muster.
- Strukturprüfung 210: `format: ok`. Praktische Prüfung an einem Ziel, Rechtefälle, echte Cache-/Probeausgaben und Gerätetest-Rückgabewerte bleiben offen.

## Ergebnisdateien zur gemeinsamen Prüfung

| Nr. | Korrigiertes Dokument | Praktischer Stand |
| --- | --- | --- |
| 201 | [touch.md](../touch.md) | Beispiel und Zusatzprüfungen erfolgreich |
| 202 | [tree.md](../tree.md) | Beispiel und Ausgabeassertions erfolgreich |
| 203 | [truncate.md](../truncate.md) | Beispiel mit Bytekontrolle erfolgreich |
| 204 | [unlink.md](../unlink.md) | Eigene Link-Beispiele erfolgreich |
| 205 | [updatedb.md](../updatedb.md) | Nur Quellen und Shellsyntax; Programme fehlen |
| 206 | [vdir.md](../vdir.md) | Beispiel erfolgreich |
| 207 | [watch.md](../watch.md) | Beispiel im Pseudoterminal erfolgreich |
| 208 | [xargs.md](../xargs.md) | Beispiel und Sonderzeichen-/Leereingabetests erfolgreich |
| 209 | [badblocks.md](../badblocks.md) | Nur Handbuch, Paketmetadaten und Musterrechnung |
| 210 | [blkid.md](../blkid.md) | Nur Hilfe und Version; Geräteausgaben sind Muster |

## Abschlussprüfungen und Grenzen

- Alle zehn Dateien jeweils vor Beginn der nächsten Nummer mit `python3 scripts/check_linux_command_docs.py --documents docs/linux-befehlsdatenbank --first NUMMER --last NUMMER` erfolgreich geprüft.
- Gesamtprüfung mit `--first 201 --last 210`: zehnmal `format: ok`. Das prüft Zuordnung und Struktur gegen den tatsächlichen begrenzten Parser; es ist keine fachliche Freigabe.
- `python3 -m pytest -q tests/test_linux_command_docs_handoff.py`: **31 passed in 0.05s**. Diese vorhandenen Tests prüfen die Übergabe, Entwurfsstruktur, Herkunftsprüfsummen und Parsergrenzen. Sie führen die korrigierten Beispiele nicht aus und bestätigen nicht automatisch deren fachliche Richtigkeit.
- Alle Bashblöcke in Abschnitt 5 zusätzlich mit `bash -n` erfolgreich geprüft. Bei 205 ist dies ausdrücklich kein Ausführungsnachweis. Die oben genannten tatsächlichen Beispieltests wurden separat durchgeführt.
- Dateiprüfung: UTF-8, LF-Zeilenenden, abschließender Zeilenumbruch, keine nachlaufenden Leerzeichen, genau zehn Hauptabschnitte und keine aktiven HTML-Einbettungen. Dokumentgrößen innerhalb der Parsergrenzen.
- Änderungsumfang geprüft: genau zehn neue Befehlsdateien und dieser eigene Bericht. Keine Änderungen an getrackten Dateien und keine gestagten Änderungen; alle ursprünglichen Entwürfe stimmen weiterhin mit `HERKUNFT-201-210.json` überein. Original-CSV/Katalog wurden durch den vorhandenen Checker erneut verifiziert.
- Keine Änderungen an Code, Tests, Originalen, Mustern, zentralem Index, GUI-Zuordnung oder anderen Fortschrittsdateien. Keine GUI-, Mount-, Geräte-, Dienst- oder Konfigurationsaktionen; keine Installationen. Kein Commit, Push oder Merge.
- Noch gemeinsam zu prüfen: fachliche Formulierungen und Umfang, insbesondere die bewusst offenen praktischen Prüfungen von updatedb sowie Geräteverhalten von badblocks/blkid. Keine Freigabe zur späteren Systemausführung aus diesem Dokument ableiten.

**Abgeschlossene Übergabe 201–210:** Die elf Ergebnisdateien wurden nach ausdrücklichem Nutzerauftrag in Commit `135b1097382b42d5b9a90e78241dcff9c388b1f2` aufgenommen und auf `codex/linux-docs-browser-handoff-20261113` gepusht. Die Prüfung dieses Commits ist laut Nutzer abgeschlossen. Der anschließende Nutzerauftrag ersetzt die frühere Stoppgrenze 210 und gibt ausschließlich die Dokumentation 211–300 frei; dafür wird ein eigener Fortschrittsbericht geführt. Die vorstehenden Abschlussangaben beschreiben den damaligen Prüfstand vor diesem autorisierten Commit/Push.
