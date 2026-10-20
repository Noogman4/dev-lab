# HDD-Slot-Konfiguration und privilegierter Mount

Prüfdatum: 2026-10-19

Repository: `Noogman4/dev-lab`

Geprüfte Ausgangsbasis: `2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f`

Cloud-Scan-Revision: `71ed081b77e26af8853d340e777009f027251082`

Finding: **User-writable HDD slot configuration reaches an unrestricted root mount**

Cloud Finding-ID: `csf_2ba51b85f8551773cd713153`

Schweregrad laut Cloud: Medium

## Unabhängige Verifikation

Der Code auf der Ausgangsbasis enthielt weiterhin den gemeldeten Pfad:
Unbekannte konfigurierte Geräte wurden unverändert zurückgegeben, ein
existierender Dateipfad genügte, und der Fallback rief `sudo -n mount` ohne
einschränkende Mount-Optionen auf. Bei bekannter Geräteadresse wurde eine
abweichende gespeicherte UUID still durch die neue UUID ersetzt.

Beide Verhaltensweisen wurden gegen den unveränderten Quelltext aus
`git show 2eb1ed8:netmon/features/hdd_controller.py` dynamisch reproduziert.
Ein synthetisches reguläres Image erreichte den simulierten Aufruf
`sudo -n mount <image> /mnt/netmon-repro`; eine UUID-Abweichung änderte den
Slot-Datensatz. Sämtliche verändernden Befehle wurden durch Fakes ersetzt.
Es wurden weder echte Dateisysteme gemountet noch sudo-Rechte benutzt.
Ein tatsächlicher Root-Kompromiss wurde nicht ausgeführt oder nachgewiesen.

## Korrektur

- Slot-Auflösung akzeptiert nur erkannte Geräte, verwirft fremde bestehende
  Pfade und überschreibt keine gespeicherte Geräteidentität mehr. Eine
  Wiedererkennung nach Geräteumbenennung über eine eindeutige UUID bleibt
  möglich, ohne den Datensatz still zu ändern.
- Der neue `netmon/services/hdd_mount_service.py` liest vor der Operation und
  unmittelbar vor dem Mount eine frische vollständige `lsblk`-Inventur.
  Er bindet Quelle und ausgewähltes Gerät an UUID, kanonischen `/dev`-Pfad,
  Blockgerätetyp, Dateisystem und Major-/Minor-Gerätenummer aus `stat` und
  `lsblk`. Nicht eindeutige UUIDs und Gerätewechsel werden abgewiesen.
- Reguläre Dateien, Zeichen-Geräte, Loop-Geräte und Partitionen unter
  Loop-Geräten werden abgewiesen. Unterstützt werden die vom HDD-Inventar
  angebotenen Disk-/Partition-/LVM-Geräte und zugehörige Crypt-Kinder.
- Die Dateisystemquelle wird aus dem aktuellen Gerätebaum bestimmt; ein
  gespeicherter oder gecachter Mapper-Name ist keine Berechtigung.
  Mehrere mögliche Dateisysteme erfordern eine konkrete Partitionsauswahl.
- Mount und LUKS-Unlock benutzen ausschließlich UDisks unter der Identität
  des angemeldeten Benutzers. Es gibt keinen sudo-, cryptsetup-, mkdir-
  oder klassischen mount-Fallback mehr in diesem Mount-Ablauf.
- Mount-Optionen sind fest `nodev,nosuid,noexec`. Vom Benutzer konfigurierbare
  Zielpfade und Optionen gelangen nicht an den Mount-Aufruf.
- Weil UDisks bei fstab-Geräten Systemoptionen übernehmen kann, werden
  solche Geräte vor dem Mount mit der festen Systemdatei `/etc/fstab`
  abgeglichen und abgewiesen. Die unten dokumentierte Nachbesserung B-01
  ersetzt die zunächst umleitbare Abfrage. Nicht eindeutige oder fehlerhafte
  Antworten führen zum Abbruch.
- Die LUKS-Passphrase verbleibt außerhalb der Kommandozeile in einer privaten
  temporären Datei mit Modus 0600, die auch bei Fehlern entfernt wird. Nach
  erfolgreichem Unlock wird kurz auf das verifizierte Crypt-Kind gewartet.
- Geräteauswahl und Identität werden vor Dialogen/Worker-Ausführung
  eingefroren und vor Unlock/Mount erneut geprüft. Ein nachträglicher
  Konfigurationswechsel lenkt den laufenden Auftrag nicht auf eine neue Quelle.

## Verhaltensänderungen

UDisks2, lsblk und findmnt sind für den HDD-Mount erforderlich. Fehlen sie
oder verweigert UDisks die Operation, zeigt NetMon einen Fehler an.
UDisks/Polkit übernimmt die Systemautorisierung; NetMon fordert dafür keine
sudo-Sitzung mehr an. Eigene Slot-Mountpunkte werden nicht mehr mit Root
erstellt oder verwendet. Das Zielverzeichnis wird von der Systemrichtlinie
bestimmt; Systemkonfigurationen wie fstab bleiben zuständig für System-Mounts.

Slots ohne gespeicherte UUID müssen ausdrücklich neu zugeordnet werden.
Ein erkannter Datenträger ohne verwendbare Dateisystem-UUID wird nicht über
NetMon gemountet. Seit B-02 verlangt auch der Unmount eine bestätigte Geräte-
und Dateisystemidentität sowie genau einen zugeordneten tatsächlichen Mount.
Gespeicherte Mountpunkte und gecachte Mapper autorisieren keinen Unmount.

## Validierung

Ausgeführt:

```sh
python -m pytest tests/test_hdd_mount_security.py tests/test_netmon_hdd.py \
  tests/test_netmon_security_modules.py tests/test_netmon_deb_packaging.py -q
```

**671 Tests bestanden**, davon 61 HDD-Tests. Die Tests arbeiten mit
synthetischen Inventuren und simulierten Befehlen. Die bisherigen fünf
Mount-Tests, die teilweise den jetzt entfernten Root-Fallback voraussetzten,
wurden durch 43 Tests des sicheren Ablaufs ersetzt. 18 andere HDD-Tests bleiben.
Ein bereits vor der Änderung fehlschlagender Alt-Test setzte ein vorhandenes
cryptsetup/udisksctl voraus, ohne dessen Vorhandensein zu simulieren; diese
Umgebungsabhängigkeit besteht in der neuen Testsuite nicht mehr.

Abgedeckt sind unter anderem Image-Pfade aus tatsächlichem Slot-JSON,
UUID-Abweichungen, fehlende/duplizierte UUIDs, falsche Gerätetypen und
Gerätenummern, Loop-Abstammung, Gerätewechsel nach einem Dialog oder
Worker-Start sowie nach der fstab-Prüfung, fremde Mapper, mehrere
Dateisystemquellen, fstab-Einträge und Prüffehler, fehlende Werkzeuge,
UDisks-Fehler ohne Fallback, erfolgreicher und fehlgeschlagener LUKS-Unlock,
verzögert sichtbare Crypt-Kinder und Entfernung temporärer Passphrase-Dateien.
Auch der tatsächliche `App.hdd_mount_async`-Einstieg wird geprüft.

Diese ursprünglichen Testergebnisse belegen nicht die Behebung der beiden
anschließend unabhängig nachgewiesenen Blocker. Die lokale Erstvalidierung
bestand einschließlich 21 Guard-Selbsttests aus 692 erfolgreichen Tests.

## Gezielte Nachbesserung B-01 und B-02

Die unabhängige Prüfung bestätigte zwei Restprobleme mit ausschließlich
synthetischen Daten und simulierten verändernden Befehlen. In diesen
Prüfläufen bestanden 86 Tests; zwei zusätzliche Solltests scheiterten:

- **B-01:** Eine synthetische System-fstab enthielt die ausgewählte Quelle.
  Nach `LIBMOUNT_FSTAB=<leere Testdatei>` lieferte die bisherige Abfrage
  dennoch `(1, "")`; der simulierte UDisks-Mount wurde erreicht.
  Außerdem unterscheidet Rückgabewert 1 allein einen fehlenden Treffer
  nicht zuverlässig von einem Fehler.
- **B-02:** Die zurückgewiesene Geräteauflösung lieferte einen leeren
  Gerätepfad. `hdd_is_mounted()` akzeptierte anschließend den Treffer einer
  `findmnt -T`-Abfrage auf ein fremdes Eltern-Dateisystem. Der bisherige
  Unmount versuchte simuliert `sudo -n umount /mnt/foreign-filesystem`.
  Die Statusanzeigefunktion bleibt außerhalb dieser Nachbesserung unverändert;
  sie wird im Unmount nicht mehr als Autorisierungsnachweis verwendet.

### B-01: feste und überprüfte System-fstab

`hdd_mount_service` öffnet ausschließlich `/etc/fstab` mit
`O_RDONLY | O_NOFOLLOW | O_NONBLOCK`. Erlaubt ist nur eine reguläre,
Root gehörende Datei ohne Gruppen-/Fremdschreibrechte. Fehlende Dateien,
Symlinks, Sonderdateien, Lesefehler und Veränderungen von Dateiidentität,
Größe oder Zeitstempeln führen zum Abbruch.

Die Grenzen sind **1 MiB**, **4.096 Einträge** und **4.096 Zeichen je Zeile**.
Sie liegen weit über üblichen Systemtabellen und begrenzen trotzdem Lesen
und Vorprüfung. UTF-8 muss gültig sein; NUL und andere unerwartete
Steuerzeichen, falsche Feldzahlen, ungültige numerische Felder und unbekannte
Escape-Sequenzen werden abgewiesen. Vier bis sechs fstab-Felder, übliche
fstab-Escapes sowie vollständige und nachgestellte Kommentare sind zulässig.

Für eine nichtleere Tabelle wird explizit
`/usr/bin/findmnt --fstab --tab-file /etc/fstab --list --json --output SOURCE,FSTYPE`
verwendet. Die inzwischen entfernte Option `--evaluate` hatte trotz fester
fstab eine blkid-Cache-Umgehung ermöglicht; die folgende Nachbesserung
beschreibt den aktuellen Stand. Gefordert sind Rückgabewert 0, gültiges JSON
und die zur direkt geprüften Tabelle passende Eintragszahl.

Quellen werden ohne blkid-Cache gegen eine frische vollständige
`lsblk`-Inventur aufgelöst. Unterstützt sind absolute Blockgerätepfade sowie
`UUID`, `LABEL`, `PARTUUID` und `PARTLABEL`. Die kanonische Quelle muss ein
geeignetes, erkanntes Blockgerät mit bestätigter Major-/Minor-Nummer,
verwendbarer UUID und konsistentem Dateisystemtyp sein. Doppelte Tags,
widersprüchliche Gerätebeschreibungen, nicht unterstützte Vorfahren und
beobachtete Geräte-/Symlinkwechsel führen zum Abbruch. Ausgewählte
Dateisysteme werden anhand ihrer UUID und Gerätenummer mit jeder Quelle
verglichen und bei einem fstab-Treffer abgelehnt. Eindeutige Pseudoquellen
wie `none`/`tmpfs` mit passendem Dateisystemtyp bleiben zulässig. Nach
Auswertung muss die begrenzt erneut gelesene Systemdatei unverändert sein.
Eine nachweislich leere Tabelle benötigt keine findmnt-Auswertung.

Der UDisks-Aufruf bleibt unverändert auf `nodev,nosuid,noexec` beschränkt.
Es gibt weiterhin keinen Root-Mount-Fallback.

### B-02: Unmount ausschließlich für die bestätigte Zuordnung

Der Slot wird kopiert. Fehlende Erkennung, fehlende gespeicherte UUID,
UUID-Abweichungen oder nicht verifizierbare Blockgeräte brechen vor der
Anforderung einer sudo-Sitzung ab. Die tatsächliche Quelle einschließlich
eines Crypt-Kindes stammt aus der frischen Geräteinventur.

Die neue Funktion `verified_mount_target()` verwendet ausdrücklich die
Kernel-Tabelle `/proc/self/mountinfo` mittels
`findmnt --kernel --tab-file /proc/self/mountinfo`. Eine Quellenabfrage und
eine exakte `--mountpoint`-Abfrage müssen jeweils genau einen konsistenten
Treffer liefern: kanonische Quelle, Dateisystem-UUID, Major/Minor und Ziel.
Root-Ziel, relative oder symlinkbehaftete Zielpfade, fremde Quellen,
Mehrfachtreffer und fehlerhafte Antworten werden zurückgewiesen. Eine
`--target`-/`-T`-Suche nach einem übergeordneten Dateisystem findet nicht statt.

Die Zuordnung wird vor der Autorisierung und erneut vor **jedem** bisherigen
Unmount-Versuch geprüft. Ein nachträglicher Geräte- oder Zielwechsel beendet
den Auftrag. Die bisherigen legitimen Unmount-Fallbacks bleiben an genau
diese Quelle und dieses Ziel gebunden. Ein Crypt-Mapper kann anschließend
nur über den verifizierten live erkannten Crypt-Quellpfad geschlossen werden;
vor jedem solchen Versuch wird seine Geräteidentität erneut geprüft.
Ein gecachter oder fremder Mappername wird nicht verwendet.

### Gezielte Regressionen nach der Nachbesserung

Ausgeführt im geprüften Bubblewrap-Namespace mit privatem Netzwerk,
schreibgeschütztem Test-Checkout, ohne Host-Home, Host-Geräte oder
Dienst-Sockets und mit unverändertem Host-Access-Guard:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests/test_hdd_mount_security.py \
  tests/test_netmon_hdd.py tests/test_host_access_guard.py
```

**146 bestanden, 0 fehlgeschlagen, 0 übersprungen:** 107 Sicherheitsfälle,
18 bestehende HDD-Funktionstests und 21 Guard-Selbsttests. Gegenüber dem
bisherigen Prüfstand sind 64 zusätzliche Sicherheitsfälle enthalten.
Der bestehende Unmount-Funktionstest behält alle vier bisherigen
Befehlsassertions und prüft zusätzlich die erneute Zuordnung vor jedem
Versuch. Seine Policy-Ergebnisse sind ausdrücklich simuliert; die neuen
Sicherheitstests führen die echte Geräte- und Mountzuordnungsprüfung aus.

Die neuen Fälle enthalten den alten LIBMOUNT-FSTAB-Entscheidungsweg als
Positivkontrolle für die Reproduktion. Echtes findmnt liest ausschließlich
synthetische Testtabellen; manipulierte leere, fremde und fehlende
Umgebungstabellen können die feste Tabelle nicht mehr ersetzen.
Alle Mount-, Unmount-, Unlock-, Mapper-Close- und sudo-Aufrufe sind Fakes.
Root-Eigentum der synthetischen fstab wird ausschließlich im Stat-Fake
abgebildet; es wurde kein chown ausgeführt.

Zusätzlich geprüft: fehlende, beschädigte, übergroße, schreibbare,
unlesbare und sich ändernde fstab; FIFO und Symlink; fehlende Identität,
fremdes Eltern-Dateisystem, falsche UUID/Gerätenummer, ungültiges JSON,
Mehrfach-Mounts, Geräte-/Zielwechsel während Worker-Wartezeit,
Autorisierung und Fallback; erfolgreicher Unmount, fehlgeschlagene Befehle,
verifizierter LUKS-Mapper und dessen Austausch vor Close.

Ruff ohne Befunde für Service, Controller und beide HDD-Testdateien;
Black-Prüfung dieser vier Dateien, Syntaxprüfung einschließlich unverändertem
`app.py` und `git diff --check` erfolgreich. Keine Gesamtsuite gestartet.

Geändert wurden für diese Nachbesserung nur Service, Controller,
die beiden HDD-Testdateien und dieser Bericht. `app.py` einschließlich
des bereits vorhandenen HDD-Drei-Zeilen-Hunks und aller About-Arbeiten
blieb bytegleich. HEAD und Index wurden nicht verändert.

## Weitere Nachbesserung nach unabhängiger Prüfung, Runde 2

Die unabhängige Prüfung hatte **B-01 weiterhin OFFEN** und **B-02 BEHOBEN**
bewertet. `BLKID_FILE` beziehungsweise `BLKID_CONF` konnten die ausgewählte
fstab-UUID über einen manipulierten Cache als `/dev/null` oder `/dev/zero`
ausgeben lassen. Die damalige Prüfung akzeptierte existierende absolute
Quellen, die nicht das ausgewählte Blockgerät waren, auch wenn es sich um
Zeichengeräte handelte. Dadurch wurde ein simulierter UDisks-Mount erreicht.

### Kontrollierter HDD-Prozessübergang

`hdd_mount_service.run_hdd_command()` verwendet ausschließlich feste
Programmpfade: `/usr/bin/findmnt`, `/usr/bin/lsblk`, `/usr/bin/udisksctl`,
`/usr/bin/umount`, `/usr/bin/sudo`, `/usr/bin/true` und
`/usr/sbin/cryptsetup`. Auch das Kindkommando hinter `sudo -n` ist absolut.
Unbekannte Programme und generische Root-Mounts werden nicht akzeptiert.
Fehlende Werkzeuge, Zeitüberschreitungen und Prozessfehler liefern Fehler;
es gibt keine Suche nach Ersatzprogrammen über eine Benutzerumgebung.

Die komplette Kindprozessumgebung besteht ausschließlich aus den festen
Werten `PATH=/usr/sbin:/usr/bin:/sbin:/bin`, `LANG=C` und `LC_ALL=C`.
`os.environ` wird weder kopiert noch übernommen. Damit gelangen insbesondere
keine `BLKID_*`, `LIBMOUNT_*`, `LD_*`, `GLIBC_TUNABLES`, `GCONV_PATH`,
`LOCPATH`, benutzerdefinierte Busadressen, `SUDO_ASKPASS` oder andere
Prozessvariablen an diese Werkzeuge. `shell=False` ist ausdrücklich gesetzt.
Passwörter für die bestehende sudo-Sitzung gehen ausschließlich über stdin.

Mount, Unlock, Inventur, fstab-Abfrage, exakte Mount-Abfrage, Unmount und
Mapper-Close nutzen diesen Runner. Die App-Weiterleitung des allgemeinen
`run_cmd` autorisiert diese Abläufe nicht mehr. Auch die vorhandene
sudo-Sitzungsprüfung für HDD-Unmount wurde als `_authorize_hdd_unmount()`
in den HDD-Pfad übernommen: vorhandene Sitzung prüfen, andernfalls maximal
drei lokale Passwortversuche zur bisherigen Timestamp-Erneuerung.
Sie erfolgt weiterhin erst nach bestätigter Geräte- und Mountzuordnung.
Die Prüfungen vor jedem Unmount-/Close-Versuch bleiben erhalten.

UDisks benutzt die Standardadresse des Systembusses und den dort
registrierten Polkit-Agenten. Eine benutzerdefinierte Busumgebung wird
absichtlich nicht durchgereicht. Root-verwaltete Programme, Systembibliotheken,
Systemkonfiguration und udev-Daten bleiben die Vertrauensbasis. Die Maßnahme
schützt Kindprozesse; sie schützt keinen Python-Prozess, der bereits beim
Start über manipulierte Bibliotheken oder Code kompromittiert wurde.

### Geänderte Dateien und Funktionen dieser Runde

- `netmon/services/hdd_mount_service.py`: neuer `run_hdd_command()`, neue
  `_read_inventory()` und `_fstab_block_source()`, angepasste
  `_check_system_fstab()` und `inspect_device()`.
- `netmon/features/hdd_controller.py`: `hdd_mount_async()` und
  `hdd_unmount_async()` verwenden den HDD-Runner; neue
  `_authorize_hdd_unmount()` für die kontrollierte sudo-Sitzungsprüfung.
- `tests/test_hdd_mount_security.py`: Angriffsregressionen, Runner-,
  Quellen-, Gerätewechsel- und Autorisierungstests; bestehende Tests und
  synthetische Inventuren an den kontrollierten Produktionspfad angepasst.
- `tests/test_netmon_hdd.py`: ausschließlich die Testinstrumentierung des
  bestehenden Unmount-/Fallback-Tests angepasst; seine vier
  Befehlsassertions und alle fünf Zuordnungsprüfungen bleiben erhalten.
- `docs/security/hdd-slot-mount.md`: aktueller Stand und Prüfbelege.

`netmon/app.py` wurde in dieser Runde nicht verändert. Seine neun bereits
vorhandenen Hunks bestehen aus genau einem HDD-Hunk (drei entfernte
`run_cmd_with_input`-Weiterleitungszeilen) und acht About-Hunks. Nur der
HDD-Hunk gehört zum späteren Sicherheitscommit. About-Dateien, HEAD und
Index werden zusätzlich per SHA-256 gegen den Beginn dieser Runde geprüft.
`secure-browser/` wurde weder gelesen noch verändert.

### Gezielte Abschlussvalidierung dieser Runde

Die vier ursprünglichen Cache-Angriffe werden mit echtem findmnt und dem
Produktions-Runner geprüft. Eine positive Gegenkontrolle zeigt zuvor, dass
der alte Auswertungsweg tatsächlich `/dev/null` oder `/dev/zero` liefert.
Der korrigierte Produktionspfad liest dagegen die unveränderte UUID aus der
festen synthetischen fstab und verweigert den Mount. Die verändernden
Schnittstellen bleiben in jedem Fall simuliert.

Ausführung im Bubblewrap-Namensraum ohne Host-Dienstsockets und Netzwerk,
mit schreibgeschütztem Repository und ohne Host-Geräte oder Host-Home:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short --maxfail=0 \
  tests/test_hdd_mount_security.py tests/test_netmon_hdd.py \
  tests/test_host_access_guard.py \
  tests/test_netmon_security_modules.py::test_scan_integrity_changes_ignores_deleted_netmon_config_files \
  tests/test_netmon_security_modules.py::test_load_security_baseline_prunes_ignored_and_stale_integrity_entries \
  tests/test_netmon_security_modules.py::test_integrity_watch_base_files_returns_fixed_watch_list
```

**212 bestanden, 0 fehlgeschlagen, 0 übersprungen:**

- 170 HDD-Sicherheitsfälle, einschließlich aller vier ursprünglichen
  blkid-Cache-Angriffe; 63 zusätzliche Sicherheitsfälle gegenüber Runde 2.
- 18 bestehende HDD-Funktionstests.
- 21 Host-Access-Guard-Selbsttests.
- 3 gezielte Security-Modultests mit HDD-Konfigurationsbezug.

Black-Prüfung und Ruff für die vier geänderten Python-Dateien erfolgreich.
Syntaxprüfung dieser Dateien und von `netmon/app.py` erfolgreich.
`git diff --check` sowie zusätzliche Whitespace-Prüfung der ungetrackten
Service-, Test- und Berichtsdatei erfolgreich. Die B-02-Funktion
`verified_mount_target()` ist gegenüber dem Beginn dieser Runde AST-identisch.
Auch `hdd_unmount_async()` ist nach Normalisierung des Runners und des
Autorisierungsaufrufs AST-identisch: keine Zuordnungsprüfung oder
Fallback-Sicherung wurde entfernt oder umgeordnet.

Hashes bestätigen unveränderte App-/About-Dateien, HEAD und Index.
Keine Gesamtsuite und kein vollständiger Lauf der 598 Security-Modultests.
Keine realen Mount-, Unmount-, LUKS- oder sudo-Operationen. Es wurden keine
Abhängigkeiten ergänzt.

Lokale technische Bewertung: **B-01 BEHOBEN**, B-02 bleibt abgesichert.
Dies ist keine Commit-Freigabe und kein Ersatz für die nächste unabhängige
Nachprüfung.

## Grenzen und Status

Der ursprüngliche Weg von einer benutzerkontrollierten Datei zum generischen
Root-Mount ist im Patch entfernt. Die Tests bestätigen die Anwendungsprüfung
und die erzeugten Argumente; es gab keinen Live-Test auf einem Desktop mit
UDisks/Polkit und echten verschlüsselten Datenträgern. Die vollständige
Repository-Testsuite wurde nicht ausgeführt.

Die Anwendung stellt keine atomare Kerneltransaktion zwischen Inventur und
UDisks-/Unmount-Aufruf her. Ein physischer Hotplug- oder Mountwechsel nach
der letzten Prüfung kann nicht vollständig ausgeschlossen werden.
Die fest vorgegebenen
Mount-Optionen und die unabhängige UDisks-Systemrichtlinie bleiben die
Begrenzung am privilegierten Übergang. Bereits vom System gemountete Geräte
werden weder umkonfiguriert noch als nachträglich gehärtet ausgewiesen.
Die temporäre Passphrase-Datei bietet keine Sicherheitsgrenze gegen andere
Prozesse derselben UID.

Die fstab-Prüfung ist bewusst konservativ: Auch ein nicht auflösbarer
Eintrag für ein anderes Gerät oder eine ungewöhnliche, nicht sicher
auswertbare Systemtabelle kann NetMons Mount-Funktion sperren. Solche
System-Mounts bleiben Aufgabe der Systemwerkzeuge. Nicht lokal auflösbare
Netzwerkquellen, reguläre Swapdateien und Bind-Mount-Quellen werden ebenfalls
konservativ abgewiesen. Feste Debian-/Ubuntu-Programmpfade sind vorausgesetzt;
abweichende Installationen führen zur sicheren Ablehnung. Die reduzierte
UDisks-/Polkit-Umgebung und der HDD-spezifische sudo-Dialog wurden nicht an
einem realen Desktop getestet. Root und die von Root
verwalteten Systemdateien/-werkzeuge bilden die Vertrauensbasis.
Unmounts ohne genau einen nachgewiesenen Mount werden abgewiesen; auch
ein bereits ungemountetes offenes LUKS-Gerät wird über diesen Pfad nicht
allein aufgrund eines gecachten Mappernamens geschlossen. Mehrfach-Mounts
und komplexere Mapper-Schichten erfordern Systemwerkzeuge. Das wirkliche
UDisks-/Polkit-Verhalten sowie reale Hotplug- und LUKS-Integration bleiben
ohne Eingriffe am Host ungeprüft.

**B-01 lokal erneut nachgebessert; B-02 bleibt abgesichert. Eine weitere
unabhängige Sicherheitsnachprüfung steht aus. Keine Selbstfreigabe.**

Dieser Bericht beschreibt einen lokal geprüften Patch; der Cloud-Status
wurde nicht geändert. Es erfolgte kein automatischer Commit oder Push.

## Primärquellen zur UDisks-Schnittstelle

- https://storaged.org/doc/udisks2-api/latest/udisksctl.1.html
- https://storaged.org/doc/udisks2-api/latest/mount_options.html
