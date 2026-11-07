# NetMon V4 – fehlender fstab-UUID-Alias: Ursache, Härtung und Korrektur

Stand: 31.10.2026. Änderungen ausschließlich in
`/dev-lab/projects/netmon-v4-dns-integration-test/`.

**Ergebnis:** Der bisher global blockierende Eintrag ist für die beiden
ausgewählten Laufwerke nachweislich unabhängig. Die eng begrenzte Korrektur
besteht synthetische Regressionen und die vollständige fstab-Prüfung am Rechner
als reine Leseprüfung. Es wurden keine echten Mount-/Unmount-/Unlock-Aktionen,
Systemkonfigurationsänderungen, Installationen, Paketbauten, Commits oder Pushes
ausgeführt. Der installierte Stand enthält die Korrektur weiterhin nicht.

Dieser Bericht klärt den noch offenen UUID-Befund aus
`HDD-MOUNT-BLOCKERS-REPORT.md`; der frühere Bericht bleibt als historischer
Prüfstand erhalten. Die dortige Swapfile-Korrektur bleibt unverändert.

## Konkreter Eintrag und Gerätezuordnung

Lesend aus `/etc/fstab`:

```fstab
/dev/disk/by-uuid/8f6bf0dc-a7cb-41b7-a8be-293a345da986 /mnt/8f6bf0dc-a7cb-41b7-a8be-293a345da986 auto nosuid,nodev,nofail,x-gvfs-show,noauto 0 0
```

Der Alias selbst fehlt auch bei der Prüfung außerhalb der Sandbox. Die
Elternverzeichnisse `/`, `/dev`, `/dev/disk`, `/dev/disk/by-uuid` sind vorhanden,
root-eigen und nicht durch Gruppe/Fremde beschreibbar. In der eingeschränkten
Sandbox war dagegen bereits das Aliasverzeichnis unsichtbar; daraus allein
wurde keine Aussage über ein physisch fehlendes Gerät abgeleitet.

Das vollständige aktuelle lsblk-Inventar enthält die referenzierte UUID nicht.
Welches frühere beziehungsweise abgetrennte Laufwerk diesen Eintrag ursprünglich
begründete, ist nicht belegt. Es wird kein Datenträger umbenannt, repariert oder
neu zugeordnet. Insbesondere wird `nofail` nicht als Sicherheitsausnahme gewertet.

| Aktuell ausgewählte Quelle | Dateisystem-UUID | Major:Minor | Typ | Node-FS-ID / Inode |
| --- | --- | --- | --- | --- |
| `/dev/sdc1` – TimeShift/Daten | `296f7a9f-c639-4e21-a0a2-2395352fbce3` | `8:33` | ext4 | `7 / 547` |
| `/dev/sdd` – Media | `bea55c3b-848c-492a-9ae6-2e1b3bfabff2` | `8:48` | ext4 | `7 / 563` |

Beide Geräte bestehen die eingefrorene Request-Bindung und die Live-Inventar-
Prüfung. Auch UDisks bestätigt jeweils kanonischen Gerätepfad, Gerätenummer,
UUID und Dateisystemtyp. Seine jeweiligen `Symlinks` enthalten den fraglichen
fremden Alias nicht; `Configuration` ist leer. Slot 1 (`/dev/sda1`) bleibt ein
geschlossenes LUKS-Gerät ohne Dateisystemquelle; seine fstab-Mountprüfung wurde
nicht ausgeführt und kein Unlock versucht.

Die Werte für Inode und Node-FS-ID sind Momentaufnahmen, keine dauerhaft
gespeicherten Freigaben. `node_device` bezeichnet `stat.st_dev` des `/dev`-
Geräteknotens, `number` bezeichnet dessen `stat.st_rdev`. Die Dateisystemquelle
wird separat über Dateisystem-UUID, Typ, Pfad und Major/Minor gebunden; ein
zusätzlicher `statfs`-FSID-Mechanismus wird nicht eingeführt.

## Zusammenhang mit der HDD-Sicherheitshärtung

Die vorhandene Git-Historie wurde ausschließlich mit lesenden
`git --no-optional-locks log/show/rev-parse`-Befehlen untersucht. Historische
Controller wurden nur exportiert und als Quelltext/AST gelesen, nicht ausgeführt.

| Revision | Nachgewiesener Zustand |
| --- | --- |
| `2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f` – vor der Härtung | Kein `hdd_mount_service.py`, keine globale fstab-Prüfung im Mount-Controller. UDisks-Aufruf ohne feste Schutzoptionen, anschließend unter Umständen klassische Root-Mount-Fallbacks. |
| `d69c3f26fe3af37d103deef43a8d68a35482d71f`, 19.10.2026 | Führt den Mount-Service einschließlich `_check_system_fstab()` (damals Zeilen 218–259) und `_fstab_block_source()` (164–215) ein. Alle relevanten fstab-Quellen müssen auflösbar sein; Fehler einer unabhängigen Quelle verweigern global. |
| `baecee92f83764ca7af73ee0c61cf0f29f4bff3d`, 20.10.2026 | Ergänzt die frühe unveränderliche Gerätebindung im Controller. Die beiden genannten fstab-Funktionen sind gegenüber `d69c3f26` AST-identisch. |

Der globale UUID-Blocker ist somit eine funktionale Nebenwirkung der mit der
Härtung eingeführten fstab-Prüfung. Er wird **nicht** durch einen nachgewiesenen
UUID-, Inode-, FS-ID- oder Major/Minor-Konflikt des ausgewählten Geräts verursacht.
Die spätere frühe Request-Bindung hat diesen globalen Prüfentscheid nicht
eingeführt oder verstärkt. Die vorhandene Sicherheitsdokumentation
`docs/security/hdd-slot-mount.md` beschreibt den Grund der fstab-Härtung:
UDisks kann bei systemverwalteten Geräten fstab-Optionen verwenden, während eine
umleitbare/fehlerhafte alte Abfrage einen Treffer übersehen konnte.

Konkreter vorheriger Codepfad:

1. Controller `_capture_hdd_request_device()` friert ursprünglichen/kanonischen
   Pfad, UUID, `st_rdev`, `st_dev` und Inode ein.
2. `_inspect_hdd_request_device()` und `inspect_device()` bestätigen diese
   Auswahl einschließlich Live-UUID, Gerätetyp, Dateisystemquelle und Vorfahren.
3. `mount_device()` revalidiert und ruft `_check_system_fstab()` auf.
4. Die Schleife erreicht die fremde Pfadquelle. `_fstab_block_source()` führt
   `realpath()` und `os.stat()` aus; `stat` wirft `FileNotFoundError`.
5. Der globale Wrapper erzeugt `MountPolicyError: fstab-managed or unverifiable
   device; mount refused.`. Der UDisks-Mount wird nicht erreicht.

Der Fehler entsteht also vor dem bisherigen Vergleich
`device.number == source.number or device.uuid == source.uuid` für diesen Eintrag.
Die bisherige Logik konnte an dieser Stelle nicht zwischen „fremder, fehlender
Alias“ und „nicht sicher zuordenbar“ unterscheiden.

## Minimale Korrektur und Sicherheitsargument

Nur `netmon/services/hdd_mount_service.py` wird als bestehende Produktdatei
geändert. `_fstab_block_source()`, die Swapfile-Prüfung, `inspect_device()`,
`revalidate()`, `mount_device()`, Unmount-/LUKS- und alle Controllerfunktionen
bleiben unverändert. Der neue Zweig läuft ausschließlich nach einem
`FileNotFoundError` beim bisherigen Auflösungsversuch.

Die Ausnahme verlangt **alle** folgenden Nachweise:

- Quelle exakt `/dev/disk/by-uuid/<36-stellige hexadezimale UUID mit Bindestrichen>`,
  Dateisystemtyp `auto`, Übereinstimmung der direkt gelesenen fstab-Felder und
  findmnt-Zeile. Kein frei interpretierter Pfad und keine generische ENOENT-Ausnahme.
- Die UUID ist weder gleich der ausgewählten UUID – vorsichtshalber ohne
  Unterscheidung der Groß-/Kleinschreibung – noch im aktuellen Inventar vorhanden.
  Die ausgewählte Quelle besteht nochmals die alte vollständige Blockprüfung.
- Alle Eltern werden relativ zu gepinnten Verzeichnis-FDs mit
  `O_PATH|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` geprüft. Root-Eigentum und fehlende
  Gruppen-/Fremdschreibrechte sind zwingend. Der letzte Verzeichniseintrag muss
  wirklich fehlen; auch ein dangling Symlink zählt als vorhanden und wird nicht
  ausgeschlossen.
- Die Mount-Server-Sicht wird direkt per UDisks-`ResolveDevice` und
  `Properties.GetAll` gelesen: genau ein Blockobjekt; Gerätepfad, Gerätenummer,
  UUID, Typ und Nutzung müssen zur gebundenen Quelle passen. Die Aliasliste muss
  die eigene UUID enthalten und den fraglichen fremden Pfad ausschließen.
  Nichtleere Systemkonfiguration führt konservativ zur Verweigerung.
- Eltern-/Abwesenheitsnachweis und Inventar werden nach der Serverabfrage erneut
  geprüft. Die gesamte Ausschlussbindung wird vor Abschluss der fstab-Prüfung
  nochmals mit frischen Abfragen verglichen. Danach folgen unveränderte fstab-
  Stabilitätsprüfung und bisherige Geräte-Revalidierung vor dem Mount.

Der Serverabgleich ist erforderlich: UDisks 2.10.1 vergleicht eine Pfadquelle
mit `Block.Device` und `Block.Symlinks`; bei Tags wird unter anderem `IdUUID`
verglichen. Eine abweichende UUID oder fehlende Datei allein wäre deshalb kein
ausreichender Gegenbeweis gegen eine alte Server-Aliaszuordnung.
[UDisks-Quellcode: `udisks_linux_block_matches_id`](https://github.com/storaged-project/udisks/blob/udisks-2.10.1/src/udiskslinuxblock.c#L361),
[fstab-Verwendung beim Mount](https://github.com/storaged-project/udisks/blob/udisks-2.10.1/src/udiskslinuxfilesystem.c#L818).

Verwendet wird vorhandenes `/usr/bin/busctl` mit festem Systembus/Zieldienst,
JSON-Ausgabe, fünf Sekunden Bus-Timeout, deaktivierter Dienstaktivierung und
deaktivierter interaktiver Autorisierung. Der bestehende Subprozess-Timeout ist
acht Sekunden je Abfrage. Das bereinigte Prozess-Environment bleibt unverändert.
Nur exakt die zwei genannten lesenden Methoden sind im HDD-Runner erlaubt;
Set/Signals/Mount/Unmount/LoopSetup sowie andere Dienste/Busadressen sind über
diesen neuen Werkzeugpfad gesperrt. Es werden keine Werkzeuge installiert.
[busctl-Dokumentation](https://www.freedesktop.org/software/systemd/man/latest/busctl.html).
Die [UDisks-Implementierung von ResolveDevice](https://github.com/storaged-project/udisks/blob/udisks-2.10.1/src/udiskslinuxmanager.c#L1134)
liest und filtert vorhandene Blockobjekte; sie führt keine Mount-Aktion aus.

Die Auswertung verlangt eindeutiges typisiertes JSON, verwirft doppelte Schlüssel,
falsche Typen, ungültige Bytepfade und Antworten über 1 MiB. Menschenlesbare
`udisksctl info`-Ausgabe wurde zur Diagnose betrachtet, dient aber nicht als
Sicherheitsautorität. Die bisherigen Mountoptionen bleiben `nodev,nosuid,noexec`;
es gibt weiterhin keinen Root-Mount-Fallback und keine neue Rechtefreigabe.

| Zuordnung | Entscheidung |
| --- | --- |
| Aufgelöste Quelle betrifft ausgewählte UUID/Gerätenummer | Weiterhin verweigern. |
| Aufgelöste fremde Blockquelle mit vollständiger alter Identitätsprüfung | Weiterhin zulassen, wie zuvor. |
| Fehlender UUID-Alias mit vollständigem neuen Gegenbeweis | Als unabhängig ausschließen; andere Einträge bleiben vollständig prüfpflichtig. |
| Alias existiert/ist dangling, UUID taucht live auf, Server kennt Alias oder widerspricht | Verweigern. |
| Andere fehlende Pfade/Tags, andere UUID-Formate/Dateisystemtypen, ungeschützte Eltern, fehlende Abfragemöglichkeit, API-/JSON-/Timeoutfehler oder Änderungen | Weiterhin fail-closed verweigern. |

**Grenzen:** `busctl` mit passender JSON-Unterstützung und erreichbares UDisks
sind für diese Ausnahme nötig; bei Fehlen bleibt das bisherige Nein erhalten.
Es gibt keine neue Paketabhängigkeit oder automatische Nachinstallation.
Vertrauenswürdiger Kernel/Systembus/Systemwerkzeuge und root-administrierte
Systempfade bleiben die bisherige Vertrauensgrenze. Die Wiederholungsprüfungen
sind keine atomare Transaktion gegenüber gleichzeitig handelnden Administratoren
oder vollständige Garantie gegen Änderungen nach der letzten Prüfung.

## Nachweise und Ergebnisse

Neues Modul `tests/test_hdd_fstab_uuid.py`: **49 Fälle**. Abgedeckt sind sichere
Mount-Anforderung mit unveränderten Optionen und tatsächlichem Controller-Einstieg,
verdeckte Server-Aliaszuordnung, falsche UUID/Gerätenummer/Pfad/Typ/Nutzung,
Systemkonfiguration, fehlende/doppelte Objekte, beschädigtes/mehrdeutiges JSON,
Fehler/Timeout, geschützte Eltern, dangling/vorhandener Eintrag, Änderungen an
Serverbindung/Inventar/fstab/Verzeichnissen sowie die ausschließliche Zulassung
lesender Busmethoden und das bereinigte Environment.

Vor der Korrektur scheitert die neue positive Regression erwartungsgemäß mit
demselben `FileNotFoundError` und äußeren Policyfehler. Der anschließende gezielte
Zwischenlauf bestand 247 Fälle; die abschließenden Läufe sind separat erfasst.

Vorhandene Sicherheitsregressionen bleiben unverändert, insbesondere
`test_valid_fstab_block_identity_allows_unrelated_hdd`,
`test_fstab_identity_conflicts_abort`,
`test_fstab_device_switch_during_stat_is_rejected` sowie die Controller-Tests
für eingefrorene Gerätebindung und Wechsel nach Dialog/Worker/fstab-Prüfung.

| Abschließende Auswahl | Bestanden | Fehlgeschlagen | Fehler | Übersprungen |
| --- | ---: | ---: | ---: | ---: |
| HDD/UUID/Swapfile/Busy/frühere GUI-/About-Regressionen | 441 | 0 | 0 | 0 |
| V4 Import-/Modulfälle | 63 | 0 | 0 | 0 |
| V4 gezielte DNS-Unit-Fälle | 23 | 0 | 0 | 0 |
| V4 DNS-Integration | 258 | 0 | 0 | 0 |
| Im V4-Lauf übernommene DNS-Fälle | 48 | 0 | 0 | 0 |
| V4 angrenzende Regressionen | 626 | 0 | 0 | 0 |
| V4 GUI/Startup | 23 | 0 | 0 | 0 |

V4: **1041 Ausführungen / 1017 unterschiedliche IDs**, unveränderter
`scripts/test_dns_integration.py all`. Die bestehenden 66 Filterabwahlen in
`dns-unit` sind keine übersprungenen/fehlgeschlagenen Tests. Alle Testausführungen
über den vorhandenen Bubblewrap-/Xvfb-Starter mit privaten Netz-/PID-/IPC-
Namespaces und Hostaktions-Guards. Syntax, Black und Ruff der beiden betroffenen
Python-Dateien bestanden.

Hostprüfung als UID 1000: Slot 2 und 3 vor Korrektur verweigert, danach
vollständiger fstab-Guard bestanden. Sowohl tatsächliche Geräteaktionen als auch
Unlock sind im Prüfskript ausdrücklich gesperrt; zugelassen sind nur die festen
lsblk-/findmnt-Abfragen und die beiden beschränkten Bus-Lesemethoden. Request-
Bindung und `/etc/fstab`-Hash bleiben während der Prüfung unverändert.

**Fehlgeschlagen:** keine abschließenden Tests. Die getrennte rote Reproduktion
vor Korrektur enthält genau einen erwarteten fehlgeschlagenen Test.

**Nicht ausgeführt:** echte Mount-/Unmount-/Unlock-/Close-Aktionen, neuer
Desktop-Anwendungsstart, Vollmatrix außerhalb obiger Auswahl, Installation,
DEB-Neubau, DNS-/Firewall-/VPN-Eingriffe. Keine erneuten KS48-Runner-, Gate-,
Archiv- oder Einmalstartprüfungen. Die 48 übernommenen simulierten DNS-Fälle
gehören zum ausdrücklich angeforderten V4-Testlauf, nicht zum KS48-Einmalrunner.

## Integrität und Reproduktion

Gegen die vor Auftrag erfassten 290 Quell-/Test-/Skriptdateien ist ausschließlich
die bestehende `hdd_mount_service.py` verändert; hinzu kommen das neue Testmodul,
dieser Bericht und auftragsbezogene Nachweise. Die 22 übrigen vorbestehenden
Service-Funktions-/Klassendefinitionen sind AST-identisch. Ausgenommen sind nur
`_check_system_fstab()` und der um die lesende Bus-Whitelist ergänzte
`run_hdd_command()`. Controller, Gerätebindung, Swapfile-/Busy-Korrektur, F1/F6,
die bisherigen Tests und Paketierung bleiben bytegleich. Alte Manifestwerte
außerhalb dieses Auftrags werden erhalten; es erfolgt keine neue Archivprüfung.

| Datei | SHA-256 |
| --- | --- |
| Mount-Service nach Korrektur | `8d55ba99b138da732ceee44e48f392fda4d03a1e1d4fd33396ae5a726de0dcd3` |
| Neues Testmodul | `7c5d48d1c795853081a6472e11d8355a267a9af05c82ca718262dc124275833c` |
| `/etc/fstab`, unverändert | `d3a3efb8988b07d0011769a12cfa9132da9717f75830fdb6bf4f9a0ee3d6e081` |
| Original-Git-Index, unverändert | `8d318f997b4dfe5ae97cd51e1eeed455ed53891afaca7655004201c775098ef3` |
| Vorhandenes `.2`-DEB, unverändert | `0e39f579a9ecc63ade9f4234f1a4a7dca002f37995ab4b01fb6f3a0bede2b226` |
| Installierter Mount-Service, unverändert | `3523edc2c7cd3bc2988c88bef4d39570819089c9d781a296cb2cd0270a793da0` |

Nachweise: `integration-evidence/fstab-uuid-blocker-20261031/` mit Vorherstand,
Diff, historischen Quellen/Ausschnitten, Hash-/AST-Vergleich, JUnit und Logs,
lesendem Host-Prüfskript sowie Inventar-/UDisks-/Verzeichnisbindungen.
Historische Quellen sind ausschließlich Vergleichsmaterial; nicht ausführen.
Temporäre Prüfpfade für eine Reproduktion anpassen und neue Ausgabeordner wählen.

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_hdd_fstab_uuid.py tests/test_hdd_swapfile_policy.py \
  tests/test_hdd_busy_diagnostics.py tests/test_hdd_action_feedback.py \
  tests/test_netmon_hdd.py tests/test_hdd_mount_security.py \
  tests/test_hdd_review_regressions.py tests/test_gui_display_findings.py \
  tests/test_netmon_about.py
python3 -B scripts/test_dns_integration.py all
```

Ein realer Funktionstest bleibt separat: Er benötigt einen bereitgestellten
Stand mit dieser Korrektur und die ausdrückliche Freigabe eines bestimmten
Testlaufwerks. Aus dem bestandenen lesenden Guard wird kein erfolgreicher
Mount abgeleitet. Der frühere Busy-Hinweis bleibt eine Verweigerung mit nicht
nachgewiesener Ursache; ein Dateimanagerfenster ist weiterhin nur eine plausible
Erklärung und kein nachgewiesener NetMon-Codefehler.
