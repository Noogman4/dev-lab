# NetMon V4 – gemeinsames DEB-Testpaket, 31.10.2026

## Ergebnis und Artefakt

Das neue gemeinsame Testpaket enthält die vorhandenen DNS-/F1-/F6-, GUI- und
HDD-Korrekturen einschließlich Swapfile-Behandlung und fstab-UUID-Fix.
Arbeitskopietests, statische Paketprüfung, isolierte Paketproben und lesende
busctl-/UDisks-Prüfung am Zielrechner sind bestanden.

**Keine Installation, kein echter Mount/Unmount/Unlock, keine Änderung an
Hostkonfigurationen, keine Commits/Pushes und keine KS48-Prüfrunde.**

| Merkmal | Wert |
| --- | --- |
| Paketdatei | `/dev-lab/projects/netmon-v4-dns-integration-test/dist/netmon_1.1.21~v4dnstest20261031.1_all.deb` |
| Paketname | `netmon` |
| Version | `1.1.21~v4dnstest20261031.1` |
| Architektur | `all` |
| Größe | 201854874 Bytes, rund 193 MiB |
| SHA-256 | `c4d9487f53fa7f34eb7f48e7e154161b9983865b2d38cc0fe7e152751f010d92` |

`dpkg --compare-versions` bestätigt: höher als die installierte
`1.1.21~v4dnstest20261030.2`, weiterhin niedriger als das offizielle
`1.1.21`. Control-Description, Changelog, Desktopname **NetMon V4 DNS Test** und
`TEST-BUILD.md` kennzeichnen den bestehenden Testmodus. Dieser Desktopname bleibt
erhalten; das Paket enthält die gemeinsame aktuelle Anwendung. Keine
Produktfreigabe und keine Freigabesignatur.

Verwendet wurde unverändert:

```sh
DPKG_DEB_THREADS_MAX=2 bash scripts/build_netmon_deb.sh \
  --test-version 1.1.21~v4dnstest20261031.1
```

Der Builder verweigert das Überschreiben eines vorhandenen Pakets. Das bisherige
`.2`-DEB bleibt am bisherigen Ort und bytegleich, SHA-256
`0e39f579a9ecc63ade9f4234f1a4a7dca002f37995ab4b01fb6f3a0bede2b226`.
Die installierte Version bleibt ebenfalls `.2`; sie wurde nicht aktualisiert.

## Arbeitskopietests vor dem Build

Alle Tests liefen über den unveränderten Bubblewrap-/Xvfb-Starter, nicht-root,
mit privaten Netz-/PID-/IPC-Namespaces und bestehenden Hostaktions-Guards.

| Auswahl | Bestanden | Fehlgeschlagen | Fehler | Übersprungen |
| --- | ---: | ---: | ---: | ---: |
| Dokumentierte HDD-/UUID-/Swapfile-/Busy-/GUI-/About-Auswahl | 441 | 0 | 0 | 0 |
| Vollständiger V4-Starter: Import/Module | 63 | 0 | 0 | 0 |
| V4: gezielte DNS-Unit-Fälle | 23 | 0 | 0 | 0 |
| V4: DNS-Integration | 258 | 0 | 0 | 0 |
| V4: übernommene DNS-Fälle | 48 | 0 | 0 | 0 |
| V4: angrenzende Regressionen | 626 | 0 | 0 | 0 |
| V4: GUI/Startup | 23 | 0 | 0 | 0 |
| Bestehende Paketierungs-/Maintainer-/Deinstaller-Regressionen | 57 | 0 | 0 | 0 |

V4 insgesamt: **1041 Ausführungen / 1017 unterschiedliche Test-IDs**.
Die 66 bestehenden Filterabwahlen der DNS-Unit-Auswahl sind keine übersprungenen
oder fehlgeschlagenen Tests. Die 48 simulierten übernommenen Fälle gehören zum
V4-Starter; kein KS48-Einmalrunner, keine Archivprüfung und keine Gates wurden
benutzt. Bestehende Implementierungen, Tests, Builder und Deinstaller sind in
diesem Auftrag nicht geändert worden.

## Statische Prüfung des tatsächlichen DEB

Control- und Data-Tar des gebauten Artefakts wurden geprüft:

- 204 Payload-Einträge / 167 Dateien; alle Tar-Eigentümer `root:root`.
  Verzeichnisse 0755, Dateien 0644 beziehungsweise ausdrücklich ausführbar 0755.
  Auch Control-Dateien und Maintainer-Skripte haben passende Rechte/Eigentümer.
- Keine Links/Spezialdateien, Setuid-/Setgid-Bits oder Gruppen-/Fremdschreibrechte.
  Keine Dienstunits, sudoers-/Polkit-Regeln, `/etc`-/`/var`-Payloads, Credentials,
  Git-/Cache-/venv-Verzeichnisse oder Python-Bytecode. Keine nativen ELF-Dateien.
- `md5sums` vollständig und für alle 167 Dateien korrekt. Alle 121 vom Builder
  eingebundenen NetMon-Quelldateien/Ressourcen gegen die aktuellen Quellen
  SHA-256-gebunden; Launcher, Tools und Deinstaller gesondert geprüft.
- Enthaltene Python-Dateien bestehen die 3.11-Grammatikprüfung. Laufzeitproben
  nutzen Python 3.12.3; keine vollständige Python-3.11-Laufzeitmatrix.
- Desktopvalidierung und Shellsyntax von Launcher, Deinstaller und
  Maintainer-Skripten bestanden. Zwei bestehende Desktop-Hinweise zu mehreren
  Hauptkategorien können weiterhin doppelte Menüeinträge verursachen.

Vorhandene Builder-Ausnahmen bleiben bestehen: `dark_test.py` ist ein nicht
verpackter Entwicklungsstarter, die CSV-Aliasdatei stammt aus der kanonischen
Tool-Datenbank; Entwickler-READMEs/Tests entfallen. Log-Bilder und
Code-the-Classics-Ressourcen erklären weiterhin den Großteil der Paketgröße.

**Abhängigkeiten:** `python3 (>= 3.11), python3-tk, python3-psutil, python3-pil,
python3-pil.imagetk`. Keine `Recommends`. UDisks2, cryptsetup und weitere
Featurewerkzeuge bleiben `Suggests`; es wird kein pauschaler Netzwerk-/Firewall-
Dienstsatz als Pflichtabhängigkeit hinzugefügt. Keine virtuelle Umgebung im DEB.

Installationspfade bleiben `/usr/lib/netmon`, `/usr/bin`, `/usr/share/netmon`,
Desktop/Icon-Verzeichnisse und `/usr/share/doc/netmon`. Der Starter verwendet
`/usr/bin/python3 -m netmon` mit `/usr/lib/netmon` im Suchpfad. Paketidentität und
Pfade erlauben keine parallele Installation neben dem bisherigen NetMon-Paket.

## Nachweis der enthaltenen Korrekturen

Der Vergleich mit dem echten `.2`-DEB zeigt identische Dateilisten: keine
hinzugefügten/entfernten Payload-Dateien. 158 Dateien bleiben bytegleich; neun
Dateien unterscheiden sich:

- `app.py`: DNS-Kopfzeile, beschreibendes CPU-Modell, About-Paketversion und
  tatsächliche Verfügbarkeit optionaler Dokumentation.
- HDD-Controller, Mount-Service, HDD-Tab und beide Sprachdateien: sichtbare
  Aktionsrückmeldung, lesende Busy-Diagnose, sichere Swapfile-Ausnahme und eng
  begrenzter UUID-Ausschluss. Gerätebindungen und bisherige Schutzmechanismen
  sind Bestandteil der geprüften Quellen und unverändert übernommen.
- `TEST-BUILD.md` und Changelog: neue Testversion/Builddaten.
- Generiertes 256×256-PNG-Icon: ausschließlich der PNG-`tIME`-Chunk unterscheidet
  sich; dekodierte RGBA-Pixel sind identisch. Pixel-SHA-256:
  `5f8e2f29555f820c0a9a16443d98664eb1368e80b02ff6b655ed108428b8e92c`.

Die DNS-Service-/Controllerdateien mit F1-/F6-Schutz und der Deinstaller bleiben
gegenüber `.2` bytegleich. Der neue Mount-Service im Paket hat SHA-256
`8d55ba99b138da732ceee44e48f392fda4d03a1e1d4fd33396ae5a726de0dcd3`.
Dateiweise Nachweise: `package-audit.json`, `static-extras.json`,
`package-delta.json`, `icon-comparison.json`.

## Prüfungen am entpackten Paket

Dies sind zusätzliche Paketproben, keine Wiederholung unter bloßer Verwendung
der Arbeitskopie und keine Installation:

| Paketprüfung | Ergebnis |
| --- | --- |
| Gezielte HDD-/UUID-/Swapfile-/Busy-/GUI-/About-Regressionen gegen DEB-Module | **174 bestanden**, 0 fehlgeschlagen, 0 Fehler, 0 übersprungen |
| Python-Modulherkunft vor/nach pytest | **111 Anwendungs-/Toolmodule** ausschließlich aus dem entpackten DEB |
| Native Python-Proben: Importe, CLI, CPU, DNS-Kopfzeile, About | Bestanden |
| F1 mit physischem/globalem DNS und Split-DNS-Fixtures | Bestanden |
| F6: öffentliche/private Servicepfade, Controller, automatische Wiederherstellung | Verweigerung bestätigt; keine Änderungsbefehle |
| Fehlende UDisks-Beweismöglichkeit | Sichere Verweigerung bestätigt |
| Tatsächlich verpackter Deinstaller-DNS-Reset | Rückgabecode 1; private DNS-Datei unverändert |

Für die 174 Paketregressionen wurden die entpackten Module und Sprachdateien
innerhalb des privaten Namespace schreibgeschützt an den erwarteten Pfaden
eingeblendet. Eine Herkunftsprüfung verhindert den Import von Produktcode aus
der Arbeitskopie. Tests/Fixtures und pytest stammen weiterhin aus der bestehenden
Testumgebung. Die vollständigen 441 HDD-/GUI- und 1041 V4-Ausführungen oben sind
dagegen **Arbeitskopietests**, kein vollständiger Paket-Lauf dieser Auswahlen.

Die zusätzlichen nativen Proben verwenden `/usr/bin/python3 -I -B` und die
tatsächlich vorhandenen Debian-Python-Pakete, ohne venv-Site-Packages als
Abhängigkeitssurrogat: psutil 5.9.8, Pillow 10.2.0, Tk 8.6. Netz und Dienstsockets
sind privat/abwesend; ein Python-Audithook verbietet externe Aktionen außer der
exakt festgelegten dpkg-Leseabfrage auf eine **private simulierte Paketdatenbank**.
About liest dort erfolgreich `1.1.21~v4dnstest20261031.1`. Das belegt den Codepfad,
keinen tatsächlich installierten neuen Paketstand. Nicht vorhandene optionale
PDF-/HTML-Dokumentation wird weiterhin nicht als verfügbar angeboten.

Die privilegierte Python-Hilfe verweigert erwartungsgemäß nicht-root. Eine
positive installierte Root-Helfer-Ausführung wurde nicht getestet.

## Installations- und Deinstallationsskripte

| Bestandteil | Statisch geprüftes Verhalten und zusätzliche Probe |
| --- | --- |
| `preinst`, `postrm` | Nicht vorhanden |
| `postinst` | Optional Desktop-Datenbank aktualisieren; Log-Bilder nach `/etc/skel/.../NetMon/Log-Pics` kopieren, ohne vorhandene Dateien zu ersetzen. Keine DNS-/NM-/Resolver-/Firewall-Befehle. |
| `prerm` | Absichtlich wirkungsloser erfolgreicher Abschluss; keine DNS-Rücksetzung |
| `/usr/bin/netmon-uninstall` | Quellgleich; DNS-Reset verweigert mit Rückgabecode 1, keine auswählbare DNS-Reset-Frage |

Die **tatsächlich verpackten** `postinst`- und `prerm`-Dateien wurden zusätzlich
unprivilegiert in einem privaten Dateisystem ausgeführt: `postinst` zweimal,
`prerm` einmal. `/etc/skel`, Desktopdatenbank und Resolverdatei waren ausschließlich
private Testkopien. 22 Bildnamen wurden berücksichtigt, eine vorhandene private
Bilddatei blieb erhalten, die übrigen Bilder entsprechen den Paketassets und
die Resolver-Fixture blieb unverändert. Kein Hostpfad wurde dadurch beschrieben.

Die frühere Legacy-NM-/DNS-Wiederherstellung bleibt entfernt, ebenso die
Deinstaller-DHCP-/ISP-Freigabe. Der Deinstaller enthält weiterhin ausdrücklich
auswählbare administrative Funktionen etwa für Firewall-/VPN-Bereinigung;
diese wurden nicht real ausgeführt. Der bekannte `/etc/skel`-Seiteneffekt würde
bei einer späteren tatsächlichen Installation weiter stattfinden.

Lintian: **Exit 0, keine Fehler, zwei Warnungen**:

1. `maintainer-script-empty [prerm]`: absichtlich leeres Entfernungsskript.
2. `uses-dpkg-database-directly [usr/lib/netmon/netmon/app.py]`: ausgelöst am
   festen About-Argument `--admindir=/var/lib/dpkg`. Der Produktcode verwendet
   dafür `/usr/bin/dpkg-query` und liest selbst keine internen Datenbankdateien.
   Der feste Pfad bleibt aus Sicherheitsgründen erhalten; keine neue
   Lintian-Ausnahme wurde ergänzt.

## busctl-/UDisks-Fähigkeiten des Zielrechners

Diese Prüfung verwendete ebenfalls den **Mount-Service aus dem entpackten DEB**,
diesmal für streng begrenzte reine Leseabfragen als UID 1000 am Zielrechner.
Mount/Unlock waren ausdrücklich gesperrt. Erlaubt waren nur feste lsblk-/findmnt-
Abfragen sowie die zwei vom Paket erlaubten Busmethoden.

- `/usr/bin/busctl` stammt aus `systemd` 255.4-1ubuntu8.18;
  `udisks2` ist 2.10.1-6ubuntu1.5. Systemwerkzeuge root-eigen und nicht durch
  Gruppe/Fremde beschreibbar.
- JSON-Ausgabe, `--auto-start=no`, `--allow-interactive-authorization=no` und
  `--timeout=5` funktionieren mit dem vorhandenen busctl.
- `Manager.ResolveDevice` und `Properties.GetAll` liefern die vom Paket streng
  geprüften Typen/Eigenschaften einschließlich Gerätepfad, Major/Minor, UUID,
  Dateisystemtyp, Aliasliste und Konfiguration.
- Für Slot 2 und 3 besteht die vollständige paketierte fstab-Prüfung inklusive
  Swapfile- und UUID-Fix. Slot 1 bleibt geschlossenes LUKS ohne Dateisystemquelle;
  dieser Mount-Guard wurde dort nicht ausgeführt. Keine tatsächliche Geräteaktion.
- `/etc/fstab` bleibt bei SHA-256
  `d3a3efb8988b07d0011769a12cfa9132da9717f75830fdb6bf4f9a0ee3d6e081`.

Der vorhandene Zielrechner erfüllt damit den benötigten Pfad. Für andere Systeme
gilt weiterhin: UDisks wird für HDD-Mount benötigt; busctl mit passender
JSON-Unterstützung ist Voraussetzung für die besondere UUID-Ausnahme. Diese
Werkzeuge werden nicht automatisch installiert. Fehlen sie oder ist ein
Gegenbeweis unklar, verweigert die bestehende Logik weiterhin sicher.

## Grenzen, Erhalt und Reproduktion

**Fehlgeschlagen:** keine Arbeitskopie-/Pakettests oder abschließenden Proben.
Lintian-Warnungen sind oben getrennt ausgewiesen.

**Nicht ausgeführt:** Paketinstallation/Upgrade/Remove/Purge, APT-Installation
oder Abhängigkeitsauflösung im Installationslauf, vollständiger Gast-Debian-
Lebenszyklus, neuer Host-Desktopstart, positive Root-Helfer-Ausführung, echte
Mount-/Unmount-/Unlock-/Close-, DNS-/Firewall-/VPN-Aktionen und KS48-Prüfungen.
Der bisherige Busy-Hinweis bleibt eine Verweigerung mit nicht nachgewiesener
Ursache; ein Dateimanagerfenster ist lediglich eine plausible Erklärung.

Alle 291 zu Auftragsbeginn erfassten Quell-/Test-/Builddateien bleiben bytegleich.
Auch altes DEB, Original-Git-Index sowie installierte App/Service-Dateien bleiben
hashgleich. Es wurden nur neues DEB, Bericht, Nachweise und die zugehörigen
Einträge des vorhandenen Integritätsmanifests erzeugt/ergänzt. Unbeteiligte
Manifestwerte bleiben erhalten; keine neue Original-/Archiv-/KS48-Prüfrunde.

Nachweise: `integration-evidence/deb-combined-v4-20261031/` mit Buildlog,
Quell-/Paket-JUnit, Paket-/Control-Inventar, Quellenbindungen, Paketvergleich,
Modulherkunft, nativen und Maintainer-Proben, lesenden Hostnachweisen und
Prüfskripten. Ein entpackter Payload ist keine Installation. Für eine erneute
Probe DEB mit `dpkg-deb --raw-extract` in ein neues privates Prüfverzeichnis
entpacken und die dokumentierten temporären Pfade anpassen.

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_hdd_fstab_uuid.py tests/test_hdd_swapfile_policy.py \
  tests/test_hdd_busy_diagnostics.py tests/test_hdd_action_feedback.py \
  tests/test_netmon_hdd.py tests/test_hdd_mount_security.py \
  tests/test_hdd_review_regressions.py tests/test_gui_display_findings.py \
  tests/test_netmon_about.py
python3 -B scripts/test_dns_integration.py all
dpkg-deb --info dist/netmon_1.1.21~v4dnstest20261031.1_all.deb
dpkg-deb --contents dist/netmon_1.1.21~v4dnstest20261031.1_all.deb
sha256sum dist/netmon_1.1.21~v4dnstest20261031.1_all.deb
```

Ein weiterer Build benötigt eine neue Testversionsnummer. Zeitstempel in
Changelog und PNG sowie Paketmetadaten verhindern die Zusage byteidentischer
Neubauten; der genannte Hash bindet das tatsächlich geprüfte Artefakt.
Ein späterer kontrollierter Installationstest sollte zuerst die
Paketmanager-Auflösung simulieren und anschließend GUI/About sowie die
installierten Helfer prüfen. Echte Geräte-/Netzwerkaktionen bleiben separat
freigabepflichtig. **Nach Paketbau und Prüfung gestoppt; nicht installiert.**
