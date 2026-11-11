# NetMon V4 – HDD-Mount/Unmount: Ursachen und sichtbare Rückmeldung

Stand: 30.10.2026. Änderungen ausschließlich in der Arbeitskopie
`/dev-lab/projects/netmon-v4-dns-integration-test/`.

**Die fehlende Rückmeldung ist korrigiert. Der reale Mount-Blocker durch die
bestehende fstab-Policy bleibt offen.** Es gab keine echte Mount-/Unmount-,
Unlock-/Close-, Berechtigungs-, Paket- oder Systemkonfigurationsaktion.
Kein DEB wurde neu gebaut oder installiert; die installierte Anwendung enthält
die Korrektur noch nicht.

## Nachgewiesene Ursachen

Die vorhandene `Documents/NetMon/Logs/runtime.log` dokumentiert die gemeldeten
Klicks bereits, unter anderem am 30.10.2026:

- 22:36 und 22:39 Uhr: Mount für TimeShift/Daten und Media verweigert mit
  `fstab-managed or unverifiable device; mount refused.`
- 22:42 Uhr: Unmount für TimeShift/Daten scheitert mit
  `GDBus.Error:org.freedesktop.UDisks2.Error.DeviceBusy ... target is busy`.
- Frühe Klicks um 22:35 Uhr treffen auf noch nicht erkannte beziehungsweise
  nicht bestätigte Slot-Geräte; auch diese Verweigerungen stehen im Log.

Diese historischen Meldungen belegen erreichte Controller-/Backendpfade.
Die Unmount-Aktion wurde in diesem Auftrag **nicht erneut real ausgeführt**.
Die Busy-Meldung wurde ausschließlich mit einem Befehls-Fake reproduziert.

Die ausschließlich lesende aktuelle Mount-Policy-Prüfung bestätigt die UUID-/
Blockgerätebindungen der drei konfigurierten Slots. Slot 1 ist aktuell ein
LUKS-Gerät ohne freigegebenes Dateisystem; weder Entsperrung noch Passworteingabe
wurden versucht. Bei Slot 2/3 trifft die Prüfung auf `/swapfile` in der
System-fstab (`fstype=swap`, reguläre Datei). Der bestehende Service versucht,
Blockidentitäten aller relevanten fstab-Quellen zu verifizieren; hier entsteht
`System fstab source is not a block device.`. Dieser Grund wird bisher vom
äußeren Fehler `fstab-managed or unverifiable device` verdeckt.

Der lesende Prüflauf erlaubt ausdrücklich nur die beiden vorgegebenen
lsblk-Inventar-/findmnt-fstab-Abfrageformen. Er ruft weder `mount_device()` noch
eine Mount-/Unmount-/Autorisierungsfunktion auf. Der korrigierte Prüflauf
überspringt die fstab-Prüfung für LUKS ohne Dateisystemquelle; ein anfänglicher
unpassender Prüfaufruf mit `source=None` ist nicht als Produktfehler gewertet.

**GUI-Ursache:** Vorprüfungs-/Policyfehler und fehlgeschlagene Backendaktionen
wurden lediglich protokolliert. Die Fehlerpfade aktivierten keinen HDD-Tab und
hatten keinen persistent sichtbaren Aktionsstatus. LUKS-/Autorisierungsabbruch,
ungültige Slotnummern und nicht startende Worker konnten ebenfalls ohne
verständliche unmittelbare Rückmeldung bleiben. Damit wirkt die zulässige
Verweigerung oder ein Busy-Fehler wie ein wirkungsloser Button.

## Vollständiger Aktionspfad

1. Die Mount-/Unmount-Buttons werden in `App.__init__` pro HDD-Slot angelegt.
   Das Lambda bindet den jeweiligen Index mit `i=idx`. Es benutzt die gespeicherte
   Slotzuordnung, nicht willkürlich die zuletzt markierte Tabellenzeile.
2. `App.hdd_mount_async()` beziehungsweise `App.hdd_unmount_async()` leiten an
   `features/hdd_controller.py` weiter. Diese App-Wrapper sind unverändert und
   entsprechen den Fassungen im installierten DEB.
3. Der Controller kopiert den Slot, löst das erkannte Gerät passend zur UUID auf
   und friert Pfad, UUID, Gerätenummer, Node-Dateisystem und Inode in einem
   unveränderlichen `_HddRequestDevice` ein. Das geschieht weiterhin vor neuen
   GUI-Rückmeldungen, Dialogen und Workerstart.
4. Der Worker liest aktuelle lsblk-/findmnt-Daten; `_assert_hdd_request_device`
   und `_inspect_hdd_request_device` überprüfen die ursprüngliche Bindung erneut.
   Slotänderungen, Pfad-/Gerätewechsel, unklare UUIDs und fremde Mapper erhalten
   dadurch keine Aktionsberechtigung.
5. Mount läuft nach Policyprüfung über UDisks/Polkit mit festen Optionen
   `nodev,nosuid,noexec`. Der vorhandene fstab-Guard verhindert, dass ein
   fstab-Eintrag diese Optionen umgehen kann. Ein gespeicherter Mountpfad ist
   keine Mount-Autorität. Bei fehlenden Werkzeugen gibt es keinen Root-Mount-
   Ausweichpfad.
6. Unmount verifiziert das exakte aktuelle Dateisystem und Mountziel vor der
   Autorisierung und nochmals vor jedem bisherigen Fallback. Der bestehende
   Autorisierungspfad und seine Dialog-/sudo-Timestamp-Behandlung bleiben
   unverändert. Es wird kein `--force` oder Lazy-Unmount ergänzt. Ein LUKS-Close
   bleibt an den tatsächlich verifizierten Crypt-Mapper gebunden und wird auf
   tatsächliches Verschwinden nachgeprüft.
7. Rückmeldungen gelangen über `call_in_ui_thread` auf den Tk-Hauptthread.
   Gerät/Slot werden dadurch nicht neu ausgewählt oder als aktuell vertrauenswürdig
   angenommen; die Geräteautorität bleibt beim eingefrorenen Request und Service.

## Arbeitskopie, installiertes Paket und Abhängigkeiten

HDD-Controller, Mount-Service und HDD-Tab waren vor diesem Auftrag in
Arbeitskopie, vorhandenem `.2`-DEB und Installation bytegleich. Die vorherigen
GUI-Korrekturen sind nur in der Arbeitskopie vorhanden und erklären diesen
HDD-Fehler nicht. Paketvergleich: `package-comparison.json`.

| Modul | SHA-256 der bisherigen/installierten Fassung |
| --- | --- |
| `hdd_controller.py` | `4e36d6642813fca8050edebd29e40fd6b146eeb7ff1d74f63fc74a9a7455c5b1` |
| `hdd_mount_service.py` | `3523edc2c7cd3bc2988c88bef4d39570819089c9d781a296cb2cd0270a793da0` |
| `hdd_tab.py` | `97f8b36e35a78b13ef5bd0de22e4905e333356c2655539b64f6402b7c34023bc` |

Installiert sind NetMon `1.1.21~v4dnstest20261030.2`, UDisks2
`2.10.1-6ubuntu1.5`, util-linux `2.39.3-9ubuntu6.6` und polkitd
`124-2ubuntu1.24.04.4`; `udisksctl` ist vorhanden. Fehlendes UDisks2 ist damit
für diese protokollierten Fehler nicht die Ursache. Im Test-DEB steht UDisks2
in `Suggests`, nicht `Depends`; auf anderen Systemen kann die HDD-Funktion
wegen fehlender Feature-Werkzeuge verweigern. Diese Abhängigkeiten wurden nicht
verändert und es wurde nichts nachinstalliert. UDisks2 und Polkit melden
bei der lesenden Dienstabfrage `active`.

Der Service nutzt feste Systemprogrammpfade und ein minimales Environment;
benutzergesteuerte Bus-/Loader-/blkid-Umgebungen werden nicht übernommen.
Es wurde kein privilegierter Helfer ersetzt, kein neuer Helfer installiert und
keine sudoers-/Polkit-Regel oder pauschale Berechtigung hinzugefügt. Die
vorhandenen Programme und installierten HDD-Python-Dateien sind root-eigen
und nicht gruppen-/fremdschreibbar. Die bestehenden Setuid-Bits von sudo und
umount wurden ausschließlich gelesen und nicht verändert.

## Konkrete Korrektur

Geänderte Implementierung:

- `netmon/features/hdd_controller.py`: zentrale UI-Thread-Rückmeldung für
  Prüfung, Erfolg, Verweigerung, Backendfehler und Abbruch. Sie schreibt weiter
  ins Log und zusätzlich in einen sichtbaren HDD-Aktionsstatus. Bei interaktiven
  Anfragen wird der HDD-Tab geöffnet und zum sichtbaren oberen Bereich gescrollt;
  Hintergrundanfragen mit `select_tab=False` wechseln den Tab nicht.
- `netmon/ui/tabs/hdd_tab.py`: persistentes Statusfeld oberhalb der HDD-Verwaltung.
- Deutsch/Englisch: verständliche Busy-, Autorisierungs- und fstab-Erklärungen.
  Bei Policyfehlern bleibt zusätzlich die vorhandene konkrete Ursache sichtbar.

Ungültige Slotindizes und Worker-Startfehler werden sichtbar verweigert. Ein
abgebrochener LUKS-Dialog beziehungsweise verweigerte/abgebrochene Unmount-
Autorisierung erhält Rückmeldung. Ein fehlgeschlagenes LUKS-Close bleibt nach
einem erfolgreichen Unmount ebenfalls im letzten sichtbaren Status erkennbar.

**Nicht geändert:** Mount-Service, fstab-Entscheidung, eingefrorene Gerätebindung,
Revalidierung, Command-Argumente, Autorisierung, Privilegien oder Force-/Fallback-
Regeln. Alle übrigen Controllerfunktionen und -klassen sind als Quelltext
identisch. Die vorherigen GUI-Fixes sowie F1-/F6-Code bleiben unverändert.

## Tests

| Lauf | Bestanden | Fehlgeschlagen | Fehler/Skips |
| --- | ---: | ---: | ---: |
| Rote Reproduktion vor Korrektur | 0 | 27 erwartete Fälle | 0 |
| Erster HDD-Lauf | 297 | 0 | 0 |
| Abschließende HDD-/frühere GUI-Regressionen | 341 | 0 | 0 |
| Davon neue HDD-Rückmeldungsfälle | 31 | 0 | 0 |
| Vollständiger V4-Starter | 1041 Ausführungen / 1017 verschiedene IDs | 0 | 0 |

Nach der roten Reproduktion wurden vier zusätzliche Fälle ergänzt. Die
Suitegruppen überlappen; die Zahlen sind keine addierbare Zahl verschiedener
Tests. Black und Ruff für alle betroffenen Python-Dateien bestehen.

Alle HDD-Aktionen in diesen Tests benutzen künstliche Geräteinventare und
Befehls-Fakes. Ein echter Tk-Test erzeugt den HDD-Tab und betätigt einen
synthetisch gebundenen Button: Das Statusfeld ist sichtbar, der richtige Tab
aktiv und kein Hostbefehl wird ausgeführt. Worker-Rückmeldungen werden im Test
bis zur Verarbeitung auf dem Hauptthread zurückgehalten.

Abgedeckt: erfolgreiche Mount-/Unmount-Anforderungen, UDisks-Autorisierungs-
verweigerung ohne sudo-Ausweichpfad, Busy ohne Force-/Lazy-Unmount, fehlende
Werkzeuge, unverifizierte Slotbindungen, Geräte-/UUID-/Nodewechsel während der
Wartezeit, LUKS-/Autorisierungsabbruch, partielles LUKS-Close, Worker-Startfehler,
ungültige Auswahl und Hintergrundaktionen ohne Fokuswechsel. Die bestehenden
umfangreichen Gerätebindungs- und fstab-Sicherheitstests bleiben unverändert.

Der vollständige V4-Starter enthält die bisherigen DNS-/F1-/F6- und GUI-/Startup-
Fälle. Eine erneute Ausführung der gesamten projektweiten Sammlung mit den
bereits dokumentierten fremden Git-/Flatpak-/Supportpaketfehlern war nicht Teil
dieser gezielten HDD-Prüfung. Deren vorheriger Stand wird nicht als neuer Lauf
ausgegeben.

Reproduktion ohne Hostlaufwerksaktionen:

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_hdd_action_feedback.py tests/test_netmon_hdd.py \
  tests/test_hdd_mount_security.py tests/test_hdd_review_regressions.py \
  tests/test_gui_display_findings.py tests/test_netmon_about.py
python3 -B scripts/test_dns_integration.py all
```

## Offene funktionale Punkte und nächster realer Test

Die Korrektur behebt die fehlende Rückmeldung. Sie **behebt nicht den
funktionalen Mount-Blocker dieses Hosts**: `/swapfile` bleibt mit der aktuellen
Blockgeräte-Verifikation unverifizierbar. Eine sichere Unterstützung regulärer
Swapdateien müsste separat einen belastbaren Verifikationspfad erhalten;
eine pauschale Ausnahme wäre eine Abschwächung der bestehenden Prüfung.
Es wurde weder fstab noch die Policy geändert.

Der historische Busy-Unmount kann mit offenen Dateien, Arbeitsverzeichnissen
oder anderen Zugriffen zusammenhängen; welche Prozesse damals beteiligt waren,
ist damit nicht nachgewiesen. Es wurden keine Programme beendet oder Dateihalter
zwangsweise geschlossen. Ein erfolgreicher realer Mount/Unmount, echte Polkit-/
sudo-Dialoge und reale LUKS-Vorgänge bleiben **NOT RUN**.

Für einen späteren kontrollierten Funktionstest sind ein gesondert beauftragter
Paketbau/Installationsschritt und die ausdrückliche Freigabe eines genau benannten
Daten-Testlaufwerks erforderlich. Pfad und UUID vorher erfassen; Systempartitionen
bleiben ausgeschlossen. Die fstab-Verifikationsgrenze muss für einen erfolgreichen
Host-Mount zuerst sicher geklärt sein. Bei Busy bleibt die Verweigerung korrekt;
kein automatisches Bereinigen, Stoppen fremder Prozesse oder erzwungenes Aushängen.

## Erhaltungsnachweise

Vorherstände, Diff, historische HDD-Logauszüge, rein lesende Host-Policy-Prüfung,
Paketvergleich, JUnit-/Console-Logs und Hashnachweise liegen privat unter
`integration-evidence/hdd-action-feedback-20261030/`. Die bestehende Integrations-
Hashliste wird aktualisiert; ihr vorheriger Stand bleibt archiviert.

Installierter Code, vorhandenes DEB, Original und Index bleiben hashgleich.
Keine echte HDD-/Netzwerk-/Firewallaktion, Installation, Deinstallation oder
Änderung an Systempartitionen; kein Commit/Push und kein KS48-Runnerstart.
Nach Abschluss dieses Auftrags wurde gestoppt.
