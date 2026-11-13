# Ausarbeitung und Prüfung 501–600

Basis: Branch `codex/linux-docs-browser-handoff-20261113`, Commit `69819704a60c30f21203bfc86dfb8377c3a80563`. Prüfdatum 2026-11-13. Der Nutzerauftrag „genauso weiter mit 501–600“ setzt Vorgehen und Veröffentlichung des vorherigen Bereichs fort; nach 600 stoppen. Keine Unteragenten. Separate Arbeitskopie: `/tmp/linux-docs-501-600-20261113`.

Es werden ausschließlich die 100 neuen Dokumentationen und dieser eigene Fortschrittsbericht bearbeitet und nach lokaler Prüfung auf denselben Branch committet/gepusht. Keine fremden Änderungen, keine zentralen Indizes, Originale, Code-, Test- oder Packagingdateien und kein Merge nach main.

Für diesen Bereich existiert im Branch kein eingefrorener Teilkatalog. Die unten festgehaltene Zuordnung wurde daher aus den reinen Zuordnungsfeldern des vorhandenen lokalen Index gelesen und gegen jede betreffende Original-CSV-Zeile geprüft. Die Originalfelder bleiben unverändert; ihre Platzhalter und Einstufungen werden fachlich nicht ungeprüft übernommen. Index-Snapshot SHA-256: `e3d5e00b563dbe90580c34cc535753ed3d73b56a6e7789bb9ccaf6e649b68953`. CSV: 713 Datensätze, SHA-256 `40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`. Ein identischer temporärer Prüfsnapshot liegt außerhalb des Repositories.

Die unveränderte CLI-Strukturprüfung ist auf 201–300 beschränkt. Deshalb wird wie zuvor dieselbe vorhandene Funktion `check_document` mit dem unten dokumentierten Zuordnungssnapshot direkt aufgerufen: tatsächlicher Markdownparser, Metadaten und exakt zehn Hauptabschnitte. Einzelprüfung nach jeder Datei, Gesamtprüfung am Ende. Keine Prüfcodeänderung. Shellsyntaxprüfung, tatsächlich ausgeführtes Beispiel und offene Betriebsfälle sind verschiedene Nachweise.

Beispiele ausschließlich mit kleinen eigenen temporären Dateien oder eng begrenzten eigenen kurzlebigen Prozessen. mktemp-Fehler bricht ab. Keine echten Signale/Änderungen an bestehenden Benutzersitzungen, keine realen Geräte-/Netz-/Konten-/Dienst-/Systemeingriffe, keine Paketinstallationen, Kernel-/Capabilityänderungen oder dauerhaften Prozesse. Fehlende Programme nicht nachinstallieren. Offizielle Quellenrecherche getrennt von Beispieldurchläufen. Hilfe-/Versionsausgabe allein ist kein Funktionsnachweis.

## Feste Zuordnung

| Nr. | Kennung | Name | Kategorie | Datei |
| --- | --- | --- | --- | --- |
| 501 | pkill | pkill | Prozesse & Jobs | pkill.md |
| 502 | pmap | pmap | Prozesse & Jobs | pmap.md |
| 503 | prlimit | prlimit | Prozesse & Jobs | prlimit.md |
| 504 | ps | ps | Prozesse & Jobs | ps.md |
| 505 | pstree | pstree | Prozesse & Jobs | pstree.md |
| 506 | renice | renice | Prozesse & Jobs | renice.md |
| 507 | strace | strace | Prozesse & Jobs | strace.md |
| 508 | taskset | taskset | Prozesse & Jobs | taskset.md |
| 509 | time | time | Prozesse & Jobs | time.md |
| 510 | timeout | timeout | Prozesse & Jobs | timeout.md |
| 511 | times | times | Prozesse & Jobs | times.md |
| 512 | top | top | Prozesse & Jobs | top.md |
| 513 | wait | wait | Prozesse & Jobs | wait.md |
| 514 | black | black | Python & Daten | black.md |
| 515 | ipython | ipython | Python & Daten | ipython.md |
| 516 | jupyter | jupyter | Python & Daten | jupyter.md |
| 517 | mongo | mongo | Python & Daten | mongo.md |
| 518 | mypy | mypy | Python & Daten | mypy.md |
| 519 | mysql | mysql | Python & Daten | mysql.md |
| 520 | psql | psql | Python & Daten | psql.md |
| 521 | pytest | pytest | Python & Daten | pytest.md |
| 522 | redis_cli | redis-cli | Python & Daten | redis_cli.md |
| 523 | ruff | ruff | Python & Daten | ruff.md |
| 524 | sqlite3 | sqlite3 | Python & Daten | sqlite3.md |
| 525 | venv | venv | Python & Daten | venv.md |
| 526 | virtualenv | virtualenv | Python & Daten | virtualenv.md |
| 527 | dtoverlay | dtoverlay | Raspberry Pi | dtoverlay.md |
| 528 | dtparam | dtparam | Raspberry Pi | dtparam.md |
| 529 | gpio | gpio | Raspberry Pi | gpio.md |
| 530 | pinout | pinout | Raspberry Pi | pinout.md |
| 531 | raspi_config | raspi-config | Raspberry Pi | raspi_config.md |
| 532 | raspinfo | raspinfo | Raspberry Pi | raspinfo.md |
| 533 | rpi_eeprom_update | rpi-eeprom-update | Raspberry Pi | rpi_eeprom_update.md |
| 534 | vcgencmd | vcgencmd | Raspberry Pi | vcgencmd.md |
| 535 | linux_help | . | Shell & Skripting | linux_help.md |
| 536 | bash | bash | Shell & Skripting | bash.md |
| 537 | dash | dash | Shell & Skripting | dash.md |
| 538 | declare | declare | Shell & Skripting | declare.md |
| 539 | dirs | dirs | Shell & Skripting | dirs.md |
| 540 | env | env | Shell & Skripting | env.md |
| 541 | eval | eval | Shell & Skripting | eval.md |
| 542 | exec | exec | Shell & Skripting | exec.md |
| 543 | export | export | Shell & Skripting | export.md |
| 544 | fish | fish | Shell & Skripting | fish.md |
| 545 | getopts | getopts | Shell & Skripting | getopts.md |
| 546 | ksh | ksh | Shell & Skripting | ksh.md |
| 547 | local | local | Shell & Skripting | local.md |
| 548 | mapfile | mapfile | Shell & Skripting | mapfile.md |
| 549 | popd | popd | Shell & Skripting | popd.md |
| 550 | printenv | printenv | Shell & Skripting | printenv.md |
| 551 | pushd | pushd | Shell & Skripting | pushd.md |
| 552 | read | read | Shell & Skripting | read.md |
| 553 | readonly | readonly | Shell & Skripting | readonly.md |
| 554 | select | select | Shell & Skripting | select.md |
| 555 | set | set | Shell & Skripting | set.md |
| 556 | sh | sh | Shell & Skripting | sh.md |
| 557 | shopt | shopt | Shell & Skripting | shopt.md |
| 558 | source | source | Shell & Skripting | source.md |
| 559 | trap | trap | Shell & Skripting | trap.md |
| 560 | ulimit | ulimit | Shell & Skripting | ulimit.md |
| 561 | unset | unset | Shell & Skripting | unset.md |
| 562 | zsh | zsh | Shell & Skripting | zsh.md |
| 563 | busctl | busctl | Systemd & Dienste | busctl.md |
| 564 | chkconfig | chkconfig | Systemd & Dienste | chkconfig.md |
| 565 | machinectl | machinectl | Systemd & Dienste | machinectl.md |
| 566 | rc_service | rc-service | Systemd & Dienste | rc_service.md |
| 567 | service | service | Systemd & Dienste | service.md |
| 568 | systemctl | systemctl | Systemd & Dienste | systemctl.md |
| 569 | systemd_cat | systemd-cat | Systemd & Dienste | systemd_cat.md |
| 570 | systemd_cgls | systemd-cgls | Systemd & Dienste | systemd_cgls.md |
| 571 | systemd_cgtop | systemd-cgtop | Systemd & Dienste | systemd_cgtop.md |
| 572 | systemd_detect_virt | systemd-detect-virt | Systemd & Dienste | systemd_detect_virt.md |
| 573 | systemd_escape | systemd-escape | Systemd & Dienste | systemd_escape.md |
| 574 | systemd_inhibit | systemd-inhibit | Systemd & Dienste | systemd_inhibit.md |
| 575 | systemd_notify | systemd-notify | Systemd & Dienste | systemd_notify.md |
| 576 | systemd_run | systemd-run | Systemd & Dienste | systemd_run.md |
| 577 | systemd_sysusers | systemd-sysusers | Systemd & Dienste | systemd_sysusers.md |
| 578 | systemd_tmpfiles | systemd-tmpfiles | Systemd & Dienste | systemd_tmpfiles.md |
| 579 | update_rc_d | update-rc.d | Systemd & Dienste | update_rc_d.md |
| 580 | journalctl_f | journalctl -f | Systemd Aufgaben | journalctl_f.md |
| 581 | journalctl_u | journalctl -u | Systemd Aufgaben | journalctl_u.md |
| 582 | systemctl_disable | systemctl disable | Systemd Aufgaben | systemctl_disable.md |
| 583 | systemctl_enable | systemctl enable | Systemd Aufgaben | systemctl_enable.md |
| 584 | systemctl_restart | systemctl restart | Systemd Aufgaben | systemctl_restart.md |
| 585 | systemctl_start | systemctl start | Systemd Aufgaben | systemctl_start.md |
| 586 | systemctl_status | systemctl status | Systemd Aufgaben | systemctl_status.md |
| 587 | systemctl_stop | systemctl stop | Systemd Aufgaben | systemctl_stop.md |
| 588 | ac | ac | Systeminformationen | ac.md |
| 589 | arch | arch | Systeminformationen | arch.md |
| 590 | depmod | depmod | Systeminformationen | depmod.md |
| 591 | dmesg | dmesg | Systeminformationen | dmesg.md |
| 592 | free | free | Systeminformationen | free.md |
| 593 | getconf | getconf | Systeminformationen | getconf.md |
| 594 | getent | getent | Systeminformationen | getent.md |
| 595 | hostnamectl | hostnamectl | Systeminformationen | hostnamectl.md |
| 596 | iostat | iostat | Systeminformationen | iostat.md |
| 597 | ipcrm | ipcrm | Systeminformationen | ipcrm.md |
| 598 | ipcs | ipcs | Systeminformationen | ipcs.md |
| 599 | journalctl | journalctl | Systeminformationen | journalctl.md |
| 600 | last | last | Systeminformationen | last.md |

## 501 – [pkill.md](../pkill.md)

- Inhalt: Prozesse anhand eines Musters signalisieren. pkill sucht passende Prozesse und sendet ihnen ein Signal. Schon ein Aufruf ohne Signaloption kann Programme beenden.
- Gelesene Primärquelle: [procps-ng-Handbuch pgrep/pkill](https://man7.org/linux/man-pages/man1/pgrep.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 501: `format: ok`.

## 502 – [pmap.md](../pmap.md)

- Inhalt: Speicherabbildungen eines Prozesses lesen. pmap zeigt die virtuellen Speicherbereiche einer angegebenen PID.
- Gelesene Primärquelle: [pmap-Handbuch](https://man7.org/linux/man-pages/man1/pmap.1.html), [Kernel-Manpage smaps](https://man7.org/linux/man-pages/man5/proc_pid_smaps.5.html)
- Lokaler Stand: procps-ng 4.0.4. Praktisch geprüft: Eigene Shell lesend geprüft; andere PIDs, Konfigurationsschreiben und Rechtefälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 502: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 503 – [prlimit.md](../prlimit.md)

- Inhalt: Ressourcenlimits abfragen und bewusst begrenzen. prlimit liest oder setzt die Ressourcenlimits eines Prozesses. Eine Zuweisung verändert den Zielprozess.
- Gelesene Primärquelle: [util-linux prlimit-Handbuch](https://man7.org/linux/man-pages/man1/prlimit.1.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Nur eigenes NOFILE gelesen; Änderungen, Vererbung und privilegierte Fälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 503: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 504 – [ps.md](../ps.md)

- Inhalt: Einen Prozess als Momentaufnahme anzeigen. ps zeigt ausgewählte Prozessinformationen zu einem bestimmten Zeitpunkt.
- Gelesene Primärquelle: [procps-ng ps-Handbuch](https://man7.org/linux/man-pages/man1/ps.1.html)
- Lokaler Stand: procps-ng 4.0.4. Praktisch geprüft: Eigene PID und vier Felder geprüft; andere Auswahlfamilien und Rechtefälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 504: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 505 – [pstree.md](../pstree.md)

- Inhalt: Prozessbeziehungen als Baum lesen. pstree ordnet sichtbare Prozesse nach ihren Elternbeziehungen.
- Gelesene Primärquelle: [PSmisc pstree-Handbuch](https://man7.org/linux/man-pages/man1/pstree.1.html)
- Lokaler Stand: PSmisc 23.7. Praktisch geprüft: Eigener Teilbaum geprüft; fremde Prozesse und Namespacewechsel offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 505: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 506 – [renice.md](../renice.md)

- Inhalt: Nice-Werte laufender Prozesse ändern. renice verändert die Scheduling-Gewichtung bereits laufender Prozesse.
- Gelesene Primärquelle: [util-linux renice-Handbuch](https://man7.org/linux/man-pages/man1/renice.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 506: `format: ok`.

## 507 – [strace.md](../strace.md)

- Inhalt: Systemaufrufe eines Programms beobachten. strace protokolliert Systemaufrufe und empfangene Signale eines Programms.
- Gelesene Primärquelle: [strace-Projekthandbuch](https://man7.org/linux/man-pages/man1/strace.1.html)
- Lokaler Stand: strace 6.8; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 507: `format: ok`.

- Abschlusskorrektur: Platzhalter für den Systemaufruffilter präzisiert; kein Dateiname als Trace-Klasse dargestellt. Einzelstruktur erneut `format: ok`.

- Tatsächlich ausgeführter Zusatzaufruf: `strace --version`, Status 0. Ausschließlich Versionsnachweis, kein Funktionsnachweis.

## 508 – [taskset.md](../taskset.md)

- Inhalt: CPU-Affinität gezielt abfragen. taskset liest oder setzt die Menge logischer CPUs, auf denen ein Prozess laufen darf.
- Gelesene Primärquelle: [util-linux taskset-Handbuch](https://man7.org/linux/man-pages/man1/taskset.1.html)
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Eigene PID nur abgefragt; Maskensetzen und Threadänderungen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 508: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 509 – [time.md](../time.md)

- Inhalt: Laufzeit und Ressourcenverbrauch messen. time startet einen Befehl und misst dessen Ausführung. Shell-Schlüsselwort und externes GNU Time sind zu unterscheiden.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: GNU-Time-Programmhilfe `/usr/bin/time --help`; [Projektverweis](https://www.gnu.org/software/time/) (Onlineabruf fehlgeschlagen)
- Lokaler Stand: GNU Time meldet Version UNKNOWN. Praktisch geprüft: Kurzer eigener Befehl mit -p/-o geprüft; Lastvergleiche und weitere Messgrößen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 509: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 510 – [timeout.md](../timeout.md)

- Inhalt: Einen neu gestarteten Befehl zeitlich begrenzen. timeout startet einen Befehl und kann ihn nach Ablauf einer Frist signalisieren.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: GNU-coreutils-Programmhilfe `timeout --help`; [Projektverweis](https://www.gnu.org/software/coreutils/) (Onlineabruf fehlgeschlagen)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Nur reguläres Ende vor Frist geprüft; Fristablauf und Signale nicht getestet.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 510: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 511 – [times.md](../times.md)

- Inhalt: Kumulierte CPU-Zeit der Shell anzeigen. times ist ein Shell-Builtin und zeigt aufgelaufene CPU-Zeiten der Shell und ihrer Kinder.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help times`; [Bash-Projekt](https://www.gnu.org/software/bash/) (Handbuchabruf online fehlgeschlagen)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Builtin in neuer Shell geprüft; quantitative Zeitmessung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 511: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 512 – [top.md](../top.md)

- Inhalt: Prozess- und Systemwerte wiederholt beobachten. top zeigt Prozessdaten und eine laufend aktualisierte Systemübersicht.
- Gelesene Primärquelle: [procps-ng top-Handbuch](https://man7.org/linux/man-pages/man1/top.1.html)
- Lokaler Stand: Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 512: `format: ok`.

## 513 – [wait.md](../wait.md)

- Inhalt: Auf eigene Hintergrundaufgaben warten. wait ist ein Shell-Builtin zum Warten auf Kinder derselben Shell.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help wait`; [Bash-Projekt](https://www.gnu.org/software/bash/) (Handbuchabruf online fehlgeschlagen)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigenes sofort endendes Kind geprüft; Jobkontrolle, -n/-p und Signalunterbrechung offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 513: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 514 – [black.md](../black.md)

- Inhalt: Python-Dateien einheitlich formatieren. Black formatiert Python-Quelltext; der Standardaufruf schreibt die betroffenen Dateien neu.
- Gelesene Primärquelle: [Black-Projektdokumentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- Lokaler Stand: Black 24.2.0 unter Python 3.12.3. Praktisch geprüft: Eine eigene Datei mit --check/--diff geprüft; Schreibmodus und weitere Grammatiken offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 514: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 515 – [ipython.md](../ipython.md)

- Inhalt: Python interaktiv mit Zusatzfunktionen verwenden. IPython ist eine erweiterte interaktive Python-Shell mit Hilfen und Magic-Befehlen.
- Gelesene Primärquelle: [IPython-Referenz](https://ipython.readthedocs.io/en/stable/interactive/reference.html)
- Lokaler Stand: Nicht vorhanden; keine IPython-Version praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 515: `format: ok`.

## 516 – [jupyter.md](../jupyter.md)

- Inhalt: Jupyter-Unterbefehle einordnen. jupyter ist der Einstieg in mehrere Notebook- und Entwicklungswerkzeuge.
- Gelesene Primärquelle: [Jupyter: Running the Notebook](https://docs.jupyter.org/en/latest/running.html)
- Lokaler Stand: Nicht vorhanden; Jupyter-Betrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 516: `format: ok`.

## 517 – [mongo.md](../mongo.md)

- Inhalt: Historische MongoDB-Shell richtig zuordnen. mongo bezeichnet im Katalog die ältere MongoDB-Shell, nicht den Datenbankserver und nicht automatisch mongosh.
- Gelesene Primärquelle: [MongoDB: aktuelle Shell-Dokumentation](https://www.mongodb.com/docs/mongodb-shell/); Legacy-Quellen wurden in der Abschlusskorrektur zusätzlich direkt gelesen (Links siehe unten)
- Lokaler Stand: mongo und mongosh nicht vorhanden; Legacy-Optionen r5.0.31 nachgelesen, Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 517: `format: ok`.

- Abschlusskorrektur: Legacy-Schnittstelle gegen die Herstellerdateien shell_options.idl und shell_options.cpp aus r5.0.31 nachgeprüft und konkret ergänzt; nur die praktische Ausführung und andere Versionen bleiben offen. Die anfangs wegen umgeleiteter Handbücher offene Quellenfrage ist damit für diesen Stand geklärt. Einzelstruktur erneut `format: ok`.

## 518 – [mypy.md](../mypy.md)

- Inhalt: Python-Typen statisch prüfen. mypy analysiert Typinformationen in Python-Code, ohne das Programm als normalen Anwendungslauf auszuführen.
- Gelesene Primärquelle: [mypy: Kommandozeilenreferenz](https://mypy.readthedocs.io/en/stable/command_line.html)
- Lokaler Stand: Nicht vorhanden; keine mypy-Ausführung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 518: `format: ok`.

## 519 – [mysql.md](../mysql.md)

- Inhalt: MySQL über einen Client ansprechen. mysql ist ein SQL-Client; ein Aufruf startet nicht automatisch den Datenbankserver.
- Gelesene Primärquelle: [MySQL 8.4: Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)
- Lokaler Stand: Nicht vorhanden; Verbindung und SQL offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 519: `format: ok`.

## 520 – [psql.md](../psql.md)

- Inhalt: PostgreSQL mit psql bedienen. psql ist ein Terminalclient für PostgreSQL mit SQL und eigenen Metabefehlen.
- Gelesene Primärquelle: [PostgreSQL: psql-Handbuch](https://www.postgresql.org/docs/current/app-psql.html)
- Lokaler Stand: Nicht vorhanden; Serverzugriffe offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 520: `format: ok`.

## 521 – [pytest.md](../pytest.md)

- Inhalt: Python-Tests gezielt ausführen. pytest sammelt Python-Tests und führt sie aus. Auch die Sammlung kann bereits Python-Code laden.
- Gelesene Primärquelle: [pytest: Aufruf und Testauswahl](https://docs.pytest.org/en/stable/how-to/usage.html)
- Lokaler Stand: pytest 7.4.4 unter Python 3.12.3. Praktisch geprüft: Eine eigene Testdatei ausgeführt; Plugin- und komplexe Fixturefälle offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 521: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 522 – [redis_cli.md](../redis_cli.md)

- Inhalt: Redis-Kommandos bewusst an einen Server senden. redis-cli ist der Kommandozeilenclient für Redis. Der nachgestellte Redis-Befehl entscheidet über Lesen oder Schreiben.
- Gelesene Primärquelle: [Redis: CLI-Handbuch](https://redis.io/docs/latest/develop/tools/cli/)
- Lokaler Stand: Nicht vorhanden; Redis-Verbindung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 522: `format: ok`.

## 523 – [ruff.md](../ruff.md)

- Inhalt: Python-Code mit Ruff prüfen. Ruff bietet Lintprüfung und Formatierung als getrennte Unterbefehle.
- Gelesene Primärquelle: [Ruff-Linter](https://docs.astral.sh/ruff/linter/), [Ruff-Konfiguration und CLI](https://docs.astral.sh/ruff/configuration/)
- Lokaler Stand: Nicht vorhanden; Ruff-Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 523: `format: ok`.

## 524 – [sqlite3.md](../sqlite3.md)

- Inhalt: SQLite mit der Kommandozeile verwenden. sqlite3 ist eine Kommandozeilenanwendung für SQLite-Datenbanken und kein eigenständiger Server.
- Gelesene Primärquelle: [SQLite: offizielles CLI-Handbuch](https://sqlite.org/cli.html)
- Lokaler Stand: sqlite3-CLI nicht vorhanden; Python-Modul vorhanden, nicht als CLI-Test genutzt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 524: `format: ok`.

## 525 – [venv.md](../venv.md)

- Inhalt: Virtuelle Python-Umgebung anlegen. venv ist ein Modul der Python-Standardbibliothek; der übliche Aufruf lautet python3 -m venv.
- Gelesene Primärquelle: [Python: venv-Handbuch](https://docs.python.org/3/library/venv.html); lokale Hilfe Python 3.12 gelesen
- Lokaler Stand: Python 3.12.3. Praktisch geprüft: Neue eigene Umgebung ohne pip geprüft; Aktivierung, Paketinstallation und andere Python-Versionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 525: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 526 – [virtualenv.md](../virtualenv.md)

- Inhalt: Python-Umgebungen mit virtualenv erzeugen. virtualenv ist ein zusätzliches Werkzeug zur Erzeugung virtueller Python-Umgebungen.
- Gelesene Primärquelle: [virtualenv: offizielle CLI-Referenz](https://virtualenv.pypa.io/en/stable/reference/cli.html)
- Lokaler Stand: Nicht vorhanden; virtualenv-Erzeugung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 526: `format: ok`.

## 527 – [dtoverlay.md](../dtoverlay.md)

- Inhalt: Device-Tree-Overlays zur Laufzeit verwalten. dtoverlay kann auf passenden Raspberry-Pi-Systemen Overlays anzeigen, laden und entfernen.
- Gelesene Primärquelle: [Raspberry Pi: dtoverlay-Implementierung und Hilfe](https://raw.githubusercontent.com/raspberrypi/utils/master/dtmerge/dtoverlay.c)
- Lokaler Stand: Nicht vorhanden; Geräte- und Ladeprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 527: `format: ok`.

## 528 – [dtparam.md](../dtparam.md)

- Inhalt: Parameter des Basis-Device-Trees verstehen. dtparam kann zur Laufzeit Parameter des Raspberry-Pi-Basisbaums anwenden.
- Gelesene Primärquelle: [Raspberry Pi: Dynamic Device Tree und dtparam](https://www.raspberrypi.com/documentation/computers/configuration.html#dynamic-device-tree)
- Lokaler Stand: Nicht vorhanden; dtparam-Wirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 528: `format: ok`.

## 529 – [gpio.md](../gpio.md)

- Inhalt: WiringPi-GPIO-Befehle richtig zuordnen. gpio bezeichnet hier das WiringPi-Werkzeug für Raspberry-Pi-GPIOs; der Name ist keine universelle Linux-GPIO-Schnittstelle.
- Gelesene Primärquelle: [WiringPi: gpio-Quelltext mit Nutzungshilfe](https://raw.githubusercontent.com/WiringPi/WiringPi/master/gpio/gpio.c)
- Lokaler Stand: Nicht vorhanden; Hardware und elektrische Wirkung ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 529: `format: ok`.

## 530 – [pinout.md](../pinout.md)

- Inhalt: GPIO-Belegung als Diagramm nachschlagen. pinout aus GPIO Zero stellt die Pinbelegung eines Raspberry-Pi-Modells dar.
- Gelesene Primärquelle: [GPIO Zero: pinout-Handbuch](https://gpiozero.readthedocs.io/en/stable/cli_pinout.html)
- Lokaler Stand: Nicht vorhanden; Diagramm und Board-Erkennung nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 530: `format: ok`.

- Abschlusskorrektur: Browseroption -x als zusätzliche Nebenwirkung ergänzt; keine Ausführung. Einzelstruktur erneut `format: ok`.

## 531 – [raspi_config.md](../raspi_config.md)

- Inhalt: Raspberry-Pi-Konfiguration gezielt vorbereiten. raspi-config ist eine Oberfläche für Systemkonfiguration und keine reine Statusanzeige.
- Gelesene Primärquelle: [raspi-config: offizieller Paketquelltext](https://raw.githubusercontent.com/RPi-Distro/raspi-config/master/raspi-config), [Hersteller: Konfigurationswege](https://www.raspberrypi.com/documentation/computers/configuration.html#configuration-methods)
- Lokaler Stand: Nicht vorhanden; Menü- und Änderungsabläufe offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 531: `format: ok`.

## 532 – [raspinfo.md](../raspinfo.md)

- Inhalt: Umfassenden Pi-Diagnosebericht einordnen. raspinfo sammelt zahlreiche Diagnoseangaben eines Raspberry Pi in einer Ausgabe.
- Gelesene Primärquelle: [raspberrypi/utils: raspinfo-Quelltext](https://raw.githubusercontent.com/raspberrypi/utils/master/raspinfo/raspinfo)
- Lokaler Stand: Nicht vorhanden; Sammlung, sudo- und Gerätepfade offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 532: `format: ok`.

## 533 – [rpi_eeprom_update.md](../rpi_eeprom_update.md)

- Inhalt: EEPROM-Status und Aktualisierung unterscheiden. rpi-eeprom-update prüft beziehungsweise aktualisiert unterstützte Raspberry-Pi-Bootloader-EEPROMs.
- Gelesene Primärquelle: [Raspberry Pi: rpi-eeprom-update-Implementierung](https://raw.githubusercontent.com/raspberrypi/rpi-eeprom/master/rpi-eeprom-update)
- Lokaler Stand: Nicht vorhanden; EEPROM-Abfrage und Aktualisierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 533: `format: ok`.

- Abschlusskorrektur: Updateangebot des aktuellen Quellstands auch beim Aufruf ohne -a ausdrücklich berücksichtigt; kein garantierter Lesemodus behauptet. Einzelstruktur erneut `format: ok`.

## 534 – [vcgencmd.md](../vcgencmd.md)

- Inhalt: Firmwareinformationen gezielt abfragen. vcgencmd kommuniziert mit der Raspberry-Pi-Firmware; der Unterbefehl bestimmt die Wirkung.
- Gelesene Primärquelle: [Raspberry Pi OS: vcgencmd-Referenz](https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd)
- Lokaler Stand: Nicht vorhanden; Firmwarewerte und Gerätepfade offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 534: `format: ok`.

## 535 – [linux_help.md](../linux_help.md)

- Inhalt: Datei in der aktuellen Shell ausführen. Der Punkt . ist ein Shell-Builtin zum Einlesen und Ausführen einer Datei im aktuellen Shellkontext.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help .`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 535: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 536 – [bash.md](../bash.md)

- Inhalt: Bash bewusst als Interpreter starten. bash interpretiert Shellcode aus einer Datei, einer Zeichenfolge oder der Standardeingabe.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: `bash --help` und `help set`; [GNU-Bash-Projektverweis](https://www.gnu.org/software/bash/) (Onlinehandbuch nicht abrufbar)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener -c-Fall geprüft; interaktiver Start, Profile und fremde Skripte offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 536: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 537 – [dash.md](../dash.md)

- Inhalt: Skripte mit Dash ausführen. dash ist ein eigener Shellinterpreter, der sich an der POSIX-Shellsprache orientiert.
- Gelesene Primärquelle: [Dash: mit dem Debian-Paket ausgeliefertes Handbuch](https://manpages.debian.org/bookworm/dash/dash.1.en.html)
- Lokaler Stand: Dash-Paket 0.5.12-6ubuntu5. Praktisch geprüft: Eigenes minimales Skript geprüft; vollständige POSIX-Kompatibilität nicht behauptet.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 537: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 538 – [declare.md](../declare.md)

- Inhalt: Variablenattribute und Arrays erklären. declare verwaltet Bash-Variablen, Attribute und Funktionen.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help declare`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 538: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 539 – [dirs.md](../dirs.md)

- Inhalt: Den Verzeichnisstapel anzeigen. dirs zeigt den Verzeichnisstapel der aktuellen Bash.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help dirs`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 539: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 540 – [env.md](../env.md)

- Inhalt: Umgebung eines Kindbefehls gezielt setzen. env kann Umgebungsvariablen anzeigen oder mit einer veränderten Umgebung einen Befehl starten.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: GNU coreutils `env --help`; [Handbuchverweis](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html) (GNU-Onlineabruf gestört)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Ein eigener Wert mit -i geprüft; weitere Startmodi und fremde Umgebungen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 540: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 541 – [eval.md](../eval.md)

- Inhalt: Zusammengesetzten Text als Shellcode ausführen. eval verbindet seine Argumente und interpretiert das Ergebnis erneut als Shellcode.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help eval`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 541: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 542 – [exec.md](../exec.md)

- Inhalt: Die aktuelle Shell durch einen Befehl ersetzen. exec ersetzt mit einem Programmargument die aktuelle Shell; ohne Programm verändert es deren Umleitungen.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help exec`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 542: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 543 – [export.md](../export.md)

- Inhalt: Variablen an Kindprozesse vererben. export markiert Shellvariablen für die Umgebung später gestarteter Kindprozesse.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help export`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 543: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 544 – [fish.md](../fish.md)

- Inhalt: Fish als eigenständige Shell verwenden. fish ist eine interaktive Shell mit eigener Skriptsprache; sie ist kein austauschbarer Bash-Interpreter.
- Gelesene Primärquelle: [Fish: offizielle Startoptionen](https://fishshell.com/docs/current/cmds/fish.html)
- Lokaler Stand: Nicht vorhanden; Fish-Syntax und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 544: `format: ok`.

## 545 – [getopts.md](../getopts.md)

- Inhalt: Kurzoptionen im eigenen Skript auswerten. getopts verarbeitet Optionsargumente in der aktuellen Shell schrittweise.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help getopts`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 545: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 546 – [ksh.md](../ksh.md)

- Inhalt: KornShell-Implementierung bewusst auswählen. ksh ist der Startname einer KornShell-Implementierung; ksh93 ist nicht mit mksh oder Bash gleichzusetzen.
- Gelesene Primärquelle: [ksh93: offizielles Handbuch im Projektquelltext](https://raw.githubusercontent.com/ksh93/ksh/dev/src/cmd/ksh93/sh.1)
- Lokaler Stand: Nicht vorhanden; ksh93 und andere Varianten praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 546: `format: ok`.

## 547 – [local.md](../local.md)

- Inhalt: Variablen innerhalb einer Funktion begrenzen. local legt in Bash funktionslokale Variablen an.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help local`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 547: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 548 – [mapfile.md](../mapfile.md)

- Inhalt: Zeilen in ein Bash-Array einlesen. mapfile liest Eingabe in ein indiziertes Array; readarray ist ein Bash-Synonym.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help mapfile`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 548: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 549 – [popd.md](../popd.md)

- Inhalt: Zum vorherigen Stapelverzeichnis zurückkehren. popd entfernt einen Eintrag aus dem Bash-Verzeichnisstapel und wechselt normalerweise das Verzeichnis.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help popd`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 549: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 550 – [printenv.md](../printenv.md)

- Inhalt: Einzelne Umgebungswerte ausgeben. printenv zeigt die Umgebung seines Prozesses oder ausgewählte benannte Werte.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: GNU coreutils `printenv --help`; [Handbuchverweis](https://www.gnu.org/software/coreutils/manual/html_node/printenv-invocation.html) (Onlineabruf gestört)
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: Eigene vorhandene und fehlende Variable geprüft; komplexe Werte und andere Implementierungen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 550: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 551 – [pushd.md](../pushd.md)

- Inhalt: Verzeichnisse auf einem Stapel merken. pushd fügt Verzeichnisse zum Bash-Stapel hinzu oder ordnet den Stapel um.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help pushd`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 551: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 552 – [read.md](../read.md)

- Inhalt: Eine Zeile ohne unbeabsichtigte Aufteilung lesen. read liest Eingabe und weist Teile davon Shellvariablen zu.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help read`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 552: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 553 – [readonly.md](../readonly.md)

- Inhalt: Eigene Shellvariablen schreibschützen. readonly setzt ein Attribut, das spätere Änderungen einer Shellvariablen verhindert.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help readonly`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 553: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 554 – [select.md](../select.md)

- Inhalt: Eine Auswahl aus einer Liste auswerten. select ist in Bash ein Sprachkonstrukt für nummerierte Auswahlmenüs.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help select`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 554: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 555 – [set.md](../set.md)

- Inhalt: Shelloptionen und Positionsparameter setzen. set verändert Shelloptionen oder Positionsparameter; ohne Argumente kann es viele Shellwerte ausgeben.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help set`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 555: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 556 – [sh.md](../sh.md)

- Inhalt: sh als Schnittstelle statt feste Implementierung verstehen. sh ist der übliche Aufruf einer Shell mit POSIX-orientierter Schnittstelle; welche Implementierung dahinterliegt, hängt vom System ab.
- Gelesene Primärquelle: [Dash-Handbuch als lokale sh-Implementierung](https://manpages.debian.org/bookworm/dash/dash.1.en.html); `/bin/sh`-Verknüpfung lokal geprüft, POSIX-Onlinereferenz nicht abrufbar
- Lokaler Stand: /bin/sh -> dash; Paket 0.5.12-6ubuntu5. Praktisch geprüft: Lokale sh-Implementierung und eigenes Skript geprüft; andere Systeme und vollständige POSIX-Konformität offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 556: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 557 – [shopt.md](../shopt.md)

- Inhalt: Zusätzliche Bash-Optionen steuern. shopt zeigt und verändert Bash-Optionen, die teilweise über set hinausgehen.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help shopt`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/The-Shopt-Builtin.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 557: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 558 – [source.md](../source.md)

- Inhalt: Geprüften Shellcode im gleichen Prozess laden. source ist in Bash ein Synonym für das Punkt-Builtin .
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help source`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 558: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 559 – [trap.md](../trap.md)

- Inhalt: Shellereignisse mit Trap behandeln. trap hinterlegt Shellcode für bestimmte Ereignisse oder Signale.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help trap`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 559: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 560 – [ulimit.md](../ulimit.md)

- Inhalt: Ressourcenlimits der Shell lesen. ulimit ist ein Shell-Builtin für Ressourcenlimits der Shell und ihrer späteren Kinder.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help ulimit`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 560: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 561 – [unset.md](../unset.md)

- Inhalt: Eigene Variablen oder Funktionen entfernen. unset entfernt Shellvariablen beziehungsweise Funktionen im aktuellen Shellkontext.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Bash 5.2 `help unset`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)
- Lokaler Stand: Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 561: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 562 – [zsh.md](../zsh.md)

- Inhalt: Zsh als eigene Shell starten. zsh ist eine eigenständige Shell mit eigenen Optionen und Erweiterungen.
- Gelesene Primärquelle: [Zsh: offizielle Aufrufreferenz](https://zsh.sourceforge.io/Doc/Release/Invocation.html)
- Lokaler Stand: Nicht vorhanden; Startdateien und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 562: `format: ok`.

## 563 – [busctl.md](../busctl.md)

- Inhalt: D-Bus-Schnittstellen gezielt untersuchen. busctl kann D-Bus-Namen und Schnittstellen anzeigen, Methoden aufrufen sowie Eigenschaften setzen.
- Gelesene Primärquelle: [Systemd: busctl-Handbuch](https://man7.org/linux/man-pages/man1/busctl.1.html); lokale Programmhilfe gelesen
- Lokaler Stand: Programm vorhanden; kein funktionaler D-Bus-Test. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 563: `format: ok`.

## 564 – [chkconfig.md](../chkconfig.md)

- Inhalt: SysV-Startverknüpfungen mit chkconfig einordnen. chkconfig verwaltet bei der hier dokumentierten Fedora-SysV-Implementierung Runlevel-Startinformationen.
- Gelesene Primärquelle: [Fedora-SysV: chkconfig-Primärhandbuch](https://raw.githubusercontent.com/fedora-sysv/chkconfig/main/chkconfig.8)
- Lokaler Stand: Nicht vorhanden; Runlevelverwaltung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 564: `format: ok`.

## 565 – [machinectl.md](../machinectl.md)

- Inhalt: Registrierte Maschinen und Container verwalten. machinectl steuert den systemd-Maschinenmanager und kann Informationen zu registrierten Instanzen liefern.
- Gelesene Primärquelle: [Systemd: machinectl-Handbuch](https://man7.org/linux/man-pages/man1/machinectl.1.html)
- Lokaler Stand: Nicht vorhanden; Maschinenmanager und Images ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 565: `format: ok`.

## 566 – [rc_service.md](../rc_service.md)

- Inhalt: OpenRC-Dienstskripte gezielt ansprechen. rc-service findet ein OpenRC-Dienstskript und ruft dessen Aktion auf.
- Gelesene Primärquelle: [OpenRC: rc-service-Primärhandbuch](https://raw.githubusercontent.com/OpenRC/openrc/master/man/rc-service.8)
- Lokaler Stand: Nicht vorhanden; Dienstskripte und neue Optionen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 566: `format: ok`.

## 567 – [service.md](../service.md)

- Inhalt: Distributionsabhängige Dienstschnittstelle verstehen. service ruft auf Debian-Systemen ein Init-Skript auf oder leitet geeignete Aktionen an den Dienstmanager weiter.
- Gelesene Primärquelle: [Debian init-system-helpers: service-Handbuch](https://manpages.debian.org/bookworm/init-system-helpers/service.8.en.html)
- Lokaler Stand: Wrapper vorhanden; keine Dienstaktion ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 567: `format: ok`.

## 568 – [systemctl.md](../systemctl.md)

- Inhalt: Systemd-Units und ihre Zustände unterscheiden. systemctl fragt den systemd-Manager ab und kann Units sowie Systemzustände verändern.
- Gelesene Primärquelle: [Systemd: systemctl-Handbuch](https://man7.org/linux/man-pages/man1/systemctl.1.html); lokale vollständige CLI-Hilfe gelesen
- Lokaler Stand: Programm vorhanden; Managerbetrieb praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 568: `format: ok`.

## 569 – [systemd_cat.md](../systemd_cat.md)

- Inhalt: Programmausgabe ins Journal schreiben. systemd-cat leitet Eingaben oder Programmausgaben an das systemd-Journal.
- Gelesene Primärquelle: [Systemd: systemd-cat-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cat.1.html)
- Lokaler Stand: Programm vorhanden; Journaltransport nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 569: `format: ok`.

## 570 – [systemd_cgls.md](../systemd_cgls.md)

- Inhalt: Prozesse nach Cgroups ordnen. systemd-cgls zeigt Inhalte einer Cgroup-Hierarchie als Baum.
- Gelesene Primärquelle: [Systemd: systemd-cgls-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cgls.1.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; reale Cgroups nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 570: `format: ok`.

## 571 – [systemd_cgtop.md](../systemd_cgtop.md)

- Inhalt: Ressourcenverbrauch von Cgroups beobachten. systemd-cgtop zeigt Ressourcenwerte für Kontrollgruppen und aktualisiert sie wiederholt.
- Gelesene Primärquelle: [Systemd: systemd-cgtop-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cgtop.1.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; Accountingwerte nicht praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 571: `format: ok`.

## 572 – [systemd_detect_virt.md](../systemd_detect_virt.md)

- Inhalt: Virtualisierungserkennung richtig interpretieren. systemd-detect-virt versucht die eigene virtualisierte Laufumgebung zu erkennen.
- Gelesene Primärquelle: [Systemd: systemd-detect-virt-Handbuch](https://man7.org/linux/man-pages/man1/systemd-detect-virt.1.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; Umgebungsdetektion nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 572: `format: ok`.

## 573 – [systemd_escape.md](../systemd_escape.md)

- Inhalt: Text in einen Systemd-Unitnamen umwandeln. systemd-escape kodiert Zeichenfolgen für Unitnamen und kann diese Kodierung zurücknehmen.
- Gelesene Primärquelle: [Systemd: systemd-escape-Handbuch](https://man7.org/linux/man-pages/man1/systemd-escape.1.html)
- Lokaler Stand: systemd 255.4-1ubuntu8.18. Praktisch geprüft: Ein eigener Pfadtext mit Leerzeichen hin und zurück geprüft; Vorlagen, problematische Pfade und Unitbetrieb offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 573: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 574 – [systemd_inhibit.md](../systemd_inhibit.md)

- Inhalt: Inhibitor-Sperren als Systemwirkung verstehen. systemd-inhibit kann für die Laufzeit eines Befehls eine Sperre gegen bestimmte Systemaktionen halten.
- Gelesene Primärquelle: [Systemd: systemd-inhibit-Handbuch](https://man7.org/linux/man-pages/man1/systemd-inhibit.1.html)
- Lokaler Stand: Programm vorhanden; Sperren und Managerzugriff nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 574: `format: ok`.

## 575 – [systemd_notify.md](../systemd_notify.md)

- Inhalt: Dienstbereitschaft an den Manager melden. systemd-notify übermittelt Statusinformationen eines Dienstes an den Service-Manager.
- Gelesene Primärquelle: [Systemd: systemd-notify-Handbuch](https://man7.org/linux/man-pages/man1/systemd-notify.1.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; keine Benachrichtigung versandt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 575: `format: ok`.

## 576 – [systemd_run.md](../systemd_run.md)

- Inhalt: Programme in transienten Units ausführen. systemd-run erstellt vorübergehende Units und kann darin Programme tatsächlich starten.
- Gelesene Primärquelle: [Systemd: systemd-run-Handbuch](https://man7.org/linux/man-pages/man1/systemd-run.1.html)
- Lokaler Stand: Programm vorhanden; transiente Units und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 576: `format: ok`.

## 577 – [systemd_sysusers.md](../systemd_sysusers.md)

- Inhalt: Systemkonten aus Sysusers-Regeln anlegen. systemd-sysusers legt Systembenutzer und Gruppen nach Konfigurationsregeln an.
- Gelesene Primärquelle: [Systemd: sysusers-Werkzeug](https://man7.org/linux/man-pages/man8/systemd-sysusers.8.html), [Regelformat sysusers.d](https://man7.org/linux/man-pages/man5/sysusers.d.5.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; keine Kontenregeln ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 577: `format: ok`.

## 578 – [systemd_tmpfiles.md](../systemd_tmpfiles.md)

- Inhalt: Dateiregeln von Tmpfiles sicher einordnen. systemd-tmpfiles erstellt, bereinigt oder entfernt Dateien anhand von Regeln.
- Gelesene Primärquelle: [Systemd: tmpfiles-Werkzeug](https://man7.org/linux/man-pages/man8/systemd-tmpfiles.8.html), [Regelformat tmpfiles.d](https://man7.org/linux/man-pages/man5/tmpfiles.d.5.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; lokale Hilfe 255 berücksichtigt, keine Dateiregel angewendet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 578: `format: ok`.

## 579 – [update_rc_d.md](../update_rc_d.md)

- Inhalt: Debian-SysV-Startlinks verwalten. update-rc.d verwaltet Start- und Stopverknüpfungen von SysV-Init-Skripten auf Debian-Systemen.
- Gelesene Primärquelle: [Debian init-system-helpers: update-rc.d-Handbuch](https://manpages.debian.org/bookworm/init-system-helpers/update-rc.d.8.en.html)
- Lokaler Stand: Programm vorhanden; Runlevelverknüpfungen nicht angefasst. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 579: `format: ok`.

## 580 – [journalctl_f.md](../journalctl_f.md)

- Inhalt: Neue Journaleinträge fortlaufend verfolgen. journalctl -f ist eine Aufgabenform von journalctl und zeigt neu hinzukommende Journaleinträge fortlaufend.
- Gelesene Primärquelle: [Systemd: journalctl-Follow-Referenz](https://man7.org/linux/man-pages/man1/journalctl.1.html); lokale CLI-Hilfe gelesen
- Lokaler Stand: journalctl vorhanden; Follow praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 580: `format: ok`.

## 581 – [journalctl_u.md](../journalctl_u.md)

- Inhalt: Journal auf eine Unit begrenzen. journalctl -u ist eine Filteraufgabe von journalctl; nach -u muss eine Unit oder ein Muster stehen.
- Gelesene Primärquelle: [Systemd: journalctl-Unitfilter](https://man7.org/linux/man-pages/man1/journalctl.1.html); lokale CLI-Hilfe gelesen
- Lokaler Stand: journalctl vorhanden; Unitfilter praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 581: `format: ok`.

## 582 – [systemctl_disable.md](../systemctl_disable.md)

- Inhalt: Startverknüpfungen einer Unit deaktivieren. systemctl disable verändert die Installationszuordnung einer Unit, stoppt sie standardmäßig aber nicht.
- Gelesene Primärquelle: Lokal gelesenes Systemd-255-Handbuch `systemctl(1)`, Abschnitt disable, und CLI-Hilfe; [Primärhandbuch online](https://man7.org/linux/man-pages/man1/systemctl.1.html)
- Lokaler Stand: systemctl vorhanden; keine Linkänderung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 582: `format: ok`.

## 583 – [systemctl_enable.md](../systemctl_enable.md)

- Inhalt: Eine Unit für Aktivierungswege einrichten. systemctl enable richtet Installationsverknüpfungen nach den Angaben einer Unitdatei ein.
- Gelesene Primärquelle: [Systemd: Unit-Installationsregeln](https://man7.org/linux/man-pages/man5/systemd.unit.5.html); lokal gelesenes `systemctl(1)`, Abschnitt enable
- Lokaler Stand: systemctl vorhanden; Enable nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 583: `format: ok`.

## 584 – [systemctl_restart.md](../systemctl_restart.md)

- Inhalt: Eine Unit neu starten. systemctl restart stoppt und startet die ausgewählte Unit; eine vorher inaktive Unit kann dabei ebenfalls starten.
- Gelesene Primärquelle: [Systemd: Diensttypen und Startabschluss](https://man7.org/linux/man-pages/man5/systemd.service.5.html); lokal gelesenes `systemctl(1)`, Abschnitt restart
- Lokaler Stand: systemctl vorhanden; Restart offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 584: `format: ok`.

## 585 – [systemctl_start.md](../systemctl_start.md)

- Inhalt: Eine bekannte Unit aktivieren. systemctl start fordert die Aktivierung einer Unit im gewählten Manager an.
- Gelesene Primärquelle: Lokal gelesenes Systemd-255-Handbuch `systemctl(1)`, Abschnitt start; [Service-Primärhandbuch](https://man7.org/linux/man-pages/man5/systemd.service.5.html)
- Lokaler Stand: systemctl vorhanden; Start nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 585: `format: ok`.

## 586 – [systemctl_status.md](../systemctl_status.md)

- Inhalt: Unitstatus als Momentaufnahme lesen. systemctl status zeigt einen für Menschen gedachten Laufzustand und gegebenenfalls letzte Journaleinträge.
- Gelesene Primärquelle: Lokal gelesenes Systemd-255-Handbuch und CLI-Hilfe; [systemctl-Statusreferenz](https://man7.org/linux/man-pages/man1/systemctl.1.html)
- Lokaler Stand: systemctl vorhanden; Statusabfrage nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 586: `format: ok`.

## 587 – [systemctl_stop.md](../systemctl_stop.md)

- Inhalt: Eine Unit geordnet deaktivieren. systemctl stop fordert das Stoppen der ausgewählten Unit an.
- Gelesene Primärquelle: [Systemd: Prozessbeendigung von Units](https://man7.org/linux/man-pages/man5/systemd.kill.5.html); lokal gelesenes `systemctl(1)`, Abschnitt stop
- Lokaler Stand: systemctl vorhanden; Stop und Signalwirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 587: `format: ok`.

## 588 – [ac.md](../ac.md)

- Inhalt: Verbindungszeiten aus Wtmp-Daten summieren. ac aus GNU acct berechnet Sitzungszeiten anhand von Login- und Logoutdatensätzen.
- Gelesene Primärquelle: [GNU-acct: mit Debian ausgeliefertes ac-Handbuch](https://manpages.debian.org/bookworm/acct/ac.1.en.html)
- Lokaler Stand: Nicht vorhanden; Wtmp-Auswertung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 588: `format: ok`.

## 589 – [arch.md](../arch.md)

- Inhalt: Maschinenarchitektur knapp ausgeben. arch aus GNU coreutils zeigt den Maschinen-Hardwarenamen wie uname -m.
- Gelesene Primärquelle: [GNU-coreutils: arch-Handbuch](https://man7.org/linux/man-pages/man1/arch.1.html)
- Lokaler Stand: GNU coreutils 9.4; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 589: `format: ok`.

- Tatsächlich ausgeführter Zusatzaufruf: `arch --version`, Status 0. Ausschließlich Versionsnachweis, kein Funktionsnachweis.

## 590 – [depmod.md](../depmod.md)

- Inhalt: Abhängigkeiten von Kernelmodulen erzeugen. depmod analysiert Kernelmodule und erzeugt Abhängigkeits- und Zuordnungsdateien.
- Gelesene Primärquelle: [kmod: depmod-Primärhandbuch](https://man7.org/linux/man-pages/man8/depmod.8.html)
- Lokaler Stand: Programm vorhanden; Modulbaum und Indexerzeugung ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 590: `format: ok`.

## 591 – [dmesg.md](../dmesg.md)

- Inhalt: Kernelmeldungen und Änderungsmodi unterscheiden. dmesg zeigt normalerweise den Kernel-Ringpuffer an, besitzt aber auch zustandsändernde Optionen.
- Gelesene Primärquelle: [util-linux: dmesg-Handbuch](https://man7.org/linux/man-pages/man1/dmesg.1.html)
- Lokaler Stand: Programm vorhanden; Kernelpuffer nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 591: `format: ok`.

## 592 – [free.md](../free.md)

- Inhalt: Arbeitsspeicherwerte richtig lesen. free zeigt zusammengefasste RAM- und Swapinformationen aus /proc/meminfo.
- Gelesene Primärquelle: [procps-ng: free-Handbuch](https://man7.org/linux/man-pages/man1/free.1.html); lokales Handbuch und Hilfe gelesen
- Lokaler Stand: procps-ng 4.0.4; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 592: `format: ok`.

- Tatsächlich ausgeführter Zusatzaufruf: `free --version`, Status 0. Ausschließlich Versionsnachweis, kein Funktionsnachweis.

## 593 – [getconf.md](../getconf.md)

- Inhalt: Konfigurationsgrenzen eines eigenen Pfads abfragen. getconf fragt benannte System- oder Pfadkonfigurationswerte ab.
- Gelesene Primärquelle: [libc-bin: getconf-Handbuch](https://manpages.debian.org/bookworm/libc-bin/getconf.1.en.html); lokale glibc-Hilfe gelesen
- Lokaler Stand: glibc 2.39-0ubuntu8.9. Praktisch geprüft: NAME_MAX am eigenen Ordner geprüft; andere Pfade, Spezifikationen und unbestimmte Werte offen.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 593: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## 594 – [getent.md](../getent.md)

- Inhalt: Einträge über NSS auflösen. getent fragt Datenbanken über den Name Service Switch der C-Bibliothek ab.
- Gelesene Primärquelle: [glibc: getent-Handbuch](https://man7.org/linux/man-pages/man1/getent.1.html)
- Lokaler Stand: Programm vorhanden; NSS- und Netzwerkpfade nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 594: `format: ok`.

## 595 – [hostnamectl.md](../hostnamectl.md)

- Inhalt: Hostnamenanzeige und Hostnamenänderung trennen. hostnamectl fragt Hostinformationen ab und kann Hostnamen sowie weitere Eigenschaften ändern.
- Gelesene Primärquelle: [Systemd: hostnamectl-Handbuch](https://man7.org/linux/man-pages/man1/hostnamectl.1.html)
- Lokaler Stand: Programm vorhanden; Hostmanager nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 595: `format: ok`.

## 596 – [iostat.md](../iostat.md)

- Inhalt: CPU- und Geräte-I/O-Statistiken einordnen. iostat aus Sysstat zeigt CPU- und Blockgeräte-I/O-Statistiken.
- Gelesene Primärquelle: [Sysstat: iostat-Primärhandbuch](https://man7.org/linux/man-pages/man1/iostat.1.html)
- Lokaler Stand: Sysstat 12.6.1; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 596: `format: ok`.

- Tatsächlich ausgeführter Zusatzaufruf: `iostat -V`, Status 0. Ausschließlich Versionsnachweis, kein Funktionsnachweis.

## 597 – [ipcrm.md](../ipcrm.md)

- Inhalt: IPC-Objekte nur nach eindeutiger Identifikation entfernen. ipcrm entfernt IPC-Ressourcen und ist kein Informationsbefehl.
- Gelesene Primärquelle: [util-linux: ipcrm-Handbuch](https://man7.org/linux/man-pages/man1/ipcrm.1.html); lokale ältere CLI-Hilfe separat gelesen
- Lokaler Stand: Programm vorhanden; lokale Hilfe 2.39-Funktionsumfang, keine Entfernung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 597: `format: ok`.

## 598 – [ipcs.md](../ipcs.md)

- Inhalt: System-V-IPC-Bestand lesend anzeigen. ipcs zeigt Informationen zu System-V-IPC-Ressourcen im sichtbaren Namespace.
- Gelesene Primärquelle: [util-linux: ipcs-Handbuch](https://man7.org/linux/man-pages/man1/ipcs.1.html); lokale Hilfe gelesen
- Lokaler Stand: Programm vorhanden; IPC-Bestand nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 598: `format: ok`.

## 599 – [journalctl.md](../journalctl.md)

- Inhalt: Journalquellen, Filter und Änderungsoptionen unterscheiden. journalctl liest gespeicherte Systemd-Journale und bietet daneben Verwaltungsfunktionen.
- Gelesene Primärquelle: Lokal gelesene Primärquelle: Systemd-255-Programmhilfe `journalctl --help`; [Online-Journalhandbuch](https://man7.org/linux/man-pages/man1/journalctl.1.html)
- Lokaler Stand: Programm vorhanden; reale und synthetische Journaldateien funktional ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen.
- Kein ausführbarer Bashblock; Funktionsmuster als nicht ausgeführter Text. Einzelstrukturprüfung 599: `format: ok`.

## 600 – [last.md](../last.md)

- Inhalt: Loginhistorie aus ausgewählter Wtmp-Datei lesen. last aus util-linux zeigt Login- und Logoutinformationen aus Wtmp-Daten.
- Gelesene Primärquelle: [util-linux: last-Primärhandbuch](https://man7.org/linux/man-pages/man1/last.1@@util-linux.html); lokale Hilfe und Version gelesen
- Lokaler Stand: util-linux 2.39.3. Praktisch geprüft: Eigene leere Datei verarbeitet; keine Login-/Logoutdatensätze, DNS- oder Systemhistorie geprüft.
- Bashblöcke syntaktisch geprüft; Einzelstrukturprüfung 600: `format: ok`.

- Ausgeführte Prüfung: vollständiger Bashblock aus Abschnitt 5 der verlinkten Datei, Status 0; Ergebnis und enge Aussagegrenze dort erklärt. Keine erneute automatische Ausführung durch den Strukturprüfer.

## Abschlussstand und offene Prüfung

100 Einträge wurden in aufsteigender Reihenfolge einzeln fertiggestellt und unmittelbar mit dem vorhandenen Parser geprüft. Die fachliche gemeinsame Prüfung steht aus; der Parser attestiert lediglich Format und Zuordnung.

- Gesamtprüfung: 100/100 korrekte Zuordnungen, vollständige Original-CSV-Zeilen gegen den eingefrorenen temporären Snapshot identisch, CSV-Hash unverändert. Alle 100 Dokumente besitzen die zehn erwarteten Hauptabschnitte. Befehlsformen einschließlich `.` und `python3 -m venv` zusätzlich geprüft.
- 40 eigene begrenzte Funktionsbeispiele tatsächlich ausgeführt, jeweils Status 0. Genau 40 veröffentlichte Bashblöcke mit `bash -n` geprüft. Das ist keine Freigabe für die übrigen Optionen des jeweiligen Befehls.
- Vier weitere Einträge nur mit Versionsaufruf geprüft: 507, 589, 592, 596. Bei 56 Einträgen kein Funktionsbeispiel ausgeführt. Zusätzlich zur Recherche gelesene lokale Hilfen sind Schnittstellennachweise, keine Funktionsnachweise.
- Vorhandene Übergabetests: `python3 -m pytest -q tests/test_linux_command_docs_handoff.py` → **31 passed**. Regression 201–300 mit unveränderter CLI → **100/100 ok**. Regression 401–500 über deren unveränderte Berichtstabelle und dieselbe Parserfunktion → **100/100 ok**. Keine GUI-, vollständige Repository- oder Systemintegrationstestbehauptung.
- Sicherheitsgrenzen eingehalten: keine realen Signale, Prioritäts-/Affinitäts-/Limitänderungen an bestehenden Prozessen; keine Netzwerkbeispielabfragen, Gerätezugriffe, Konten-/Dienst-/Firmware-/Systemänderungen oder Paketinstallationen. Benötigte eigene Testdateien und neue Shells blieben isoliert vom Benutzerzustand. Keine Unteragenten.

Praktisch geprüft wurden die Datensätze: 502, 503, 504, 505, 508, 509, 510, 511, 513, 514, 521, 525, 535, 536, 537, 538, 539, 540, 541, 542, 543, 545, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 573, 593, 600.

Besonders enge Nachweise: 510 endet regulär vor der Frist, der Timeout-Abbruch bleibt ungeprüft; 514 prüft eine einzelne schon formatierte Datei und schreibt keinen Quelltext; 521 führt genau einen eigenen Test aus; 525 erzeugt eine neue eigene Umgebung ohne pip; 559 prüft nur EXIT mit Textausgabe, keine Signalzustellung; 560 liest lediglich Limits; 573 kodiert Text und mountet nichts; 600 prüft nur eine eigene **leere** Wtmp-Datei, keine Sitzungsdatensätze.

Offen bleiben reale Betriebs-, Rechte-, Fehler- und Versionsfälle außerhalb dieser Übungen. Nicht vorhandene Werkzeuge wurden nicht installiert, insbesondere Datenbankclients, Ruff/mypy/IPython/Jupyter/virtualenv, Raspberry-Pi-Werkzeuge, Fish/Ksh/Zsh, chkconfig, machinectl, rc-service und ac. Keine praktischen Aussagen über Datenbankverbindungen, Hardware, Firmwareupdates, reale NSS-Quellen, IPC-Bestand, Dienststart/-stopp oder Journaldaten. Ein vorhandenes Programm belegt keinen funktionierenden Dienstmanager.

Einzelne GNU-Onlinehandbücher waren wiederholt nicht erreichbar. Für die betroffenen Shell-Builtins und GNU-Werkzeuge wurden deshalb die mitgelieferten Primärhilfen beziehungsweise lokalen Handbücher gelesen; die Dokumente unterscheiden diese Nachweise ausdrücklich von bloßen Projekt-/Handbuchverweisen. Erneute Onlineprüfung der GNU-Verweise bleibt für die gemeinsame Review offen. Mongo-Legacy-Optionen wurden nach zunächst umgeleiteten Handbuchadressen gegen die Herstellerquellen **r5.0.31** konkret nachgeprüft; andere Versionen bleiben offen. Bei `rpi-eeprom-update` wurde die mögliche interaktive Update-Rückfrage auch ohne `-a` berücksichtigt.

Git-Abgrenzung vor Veröffentlichung: exakt **101 neue Dateien**, keine Änderung einer bestehenden Datei. `git diff --cached --check` nach reiner Zeilenendbereinigung ohne Befund. Der Remote-Branch stand vor dem Commit unverändert auf dem oben genannten Basiscommit.

## Reproduzierbare Abschlussprüfung

Vom Repository-Stamm aus. Dieser Code ruft den bestehenden Parser auf und führt **keine** Befehlsbeispiele aus; `bash -n` liest ausschließlich Syntax. Die feste Dateizuordnung stammt aus der oben veröffentlichten Berichtstabelle, ohne temporäre externe Katalogdatei vorauszusetzen.

```python
import csv, hashlib, io, json, pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path.cwd()))
from scripts.check_linux_command_docs import BASE, check_document, load_catalog
from netmon.services.linux_help_markdown_service import parse_document
report = BASE / 'browser-codex/FORTSCHRITT-CODEX-501-600.md'
text = report.read_text(encoding='utf-8')
mapping = []
for line in text.splitlines():
    fields = [field.strip() for field in line.split('|')[1:-1]]
    if len(fields) == 5 and fields[0].isdigit():
        nr, identifier, name, category, filename = fields
        mapping.append(dict(source_record=int(nr), id=identifier, name=name,
                            category=category, document=filename))
assert [r['source_record'] for r in mapping] == list(range(501, 601))
assert len({r['document'] for r in mapping}) == 100
original = load_catalog()
raw = pathlib.Path(original['source_catalog']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == '40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887'
rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
assert len(rows) == 713
catalog = {'source_catalog': original['source_catalog']}
blocks = 0
functional = []
for record in mapping:
    nr = record['source_record']
    assert rows[nr-1]['Befehl'] == record['name']
    assert rows[nr-1]['Kategorie'] == record['category']
    path = BASE / record['document']
    assert path.parent == BASE and path.suffix == '.md'
    result = check_document(path, record, catalog)
    assert result['format'] == 'ok'
    source = path.read_text(encoding='utf-8')
    metadata = parse_document(source).metadata
    expected_command = 'python3 -m venv' if nr == 525 else record['name']
    assert metadata['command'] == expected_command
    assert isinstance(metadata['root_required'], bool)
    assert metadata['risk_level'] in {'safe', 'caution', 'danger'}
    examples = re.findall(r'```bash\n(.*?)\n```', source, re.S)
    for example in examples:
        subprocess.run(['bash', '-n'], input=example, text=True, check=True)
        blocks += 1
    if examples:
        functional.append(nr)
assert re.findall(r'^## (\d+) –', text, re.M) == [str(n) for n in range(501, 601)]
print(f'501–600: {len(mapping)} Zuordnungen/Strukturen OK; {blocks} Bashblöcke bash -n OK')
print('Dokumentierte begrenzte Funktionsfälle:', len(functional), functional)
# Existing preceding range, without changing the original checker.
previous = BASE / 'browser-codex/FORTSCHRITT-CODEX-401-500.md'
older = []
for line in previous.read_text(encoding='utf-8').splitlines():
    cells = [x.strip() for x in line.split('|')[1:-1]]
    if len(cells) == 5 and cells[0].isdigit():
        n, identifier, name, category, filename = cells
        older.append(dict(source_record=int(n), id=identifier, name=name,
                          category=category, document=filename))
assert [r['source_record'] for r in older] == list(range(401, 501))
for record in older:
    assert check_document(BASE/record['document'], record, catalog)['format'] == 'ok'
print('Regression 401–500: 100/100 Struktur und Zuordnung OK')
```

Die Veröffentlichung umfasst ausschließlich diese 100 neuen Dokumente und diesen neuen Bericht. Der Remote-Stand wurde vor der Veröffentlichung mit dem Basiscommit abgeglichen; kein Force-Push und kein Merge. Der konkrete Commit- und Pushnachweis wird nach erfolgreicher Veröffentlichung in der Übergabe genannt. Nach Datensatz 600 endet dieser Auftrag.
