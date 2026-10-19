# DEB-Postinstall: keine privilegierten Schreibzugriffe auf Benutzer-Homes

Lokaler Stand vom 19.10.2026, Basis
`c73a092359b75e54b90c46ef0354fce409229a4b`.

Finding: **Root package post-install scripts follow user-controlled
home-directory symlinks**.

## Ursache und gezielte Korrektur

Die von `scripts/build_netmon_deb.sh` und
`scripts/build_netmon_dark_deb.sh` erzeugten `postinst`-Skripte ermittelten
ueber `SUDO_USER` und `getent passwd` ein Benutzer-Home. Dort wurden Bilder
unter `Documents/NetMon/Log-Pics` beziehungsweise `Dokumente/NetMon/Log-Pics`
angelegt und Verzeichnisse sowie Bilder mit zwei `chown`-Aufrufen zugeordnet.
Die Verzeichnis-, Kopier- und Eigentumsoperationen folgten dabei
benutzerkontrollierten Symlinks; bei einer Paketinstallation liefen sie als root.

In beiden Build-Skripten wurde ausschliesslich der vollstaendige
`SUDO_USER`-Block entfernt. Die erzeugten `postinst`-Skripte enthalten damit
keine `SUDO_USER`-/`USER_HOME`-Verarbeitung, keine `getent`-Benutzerabfrage
und keine `chown`-/`chgrp`-Aufrufe mehr. Es gibt keinen Ersatzpfad zur
privilegierten Befuellung vorhandener Benutzer-Homes.

Die systemweiten Log-Pics-Assets bleiben erhalten:

| Paket | Asset-Verzeichnis |
| --- | --- |
| NetMon | `/usr/share/netmon/assets/log-pics` |
| NetMon Dark | `/opt/netmon-dark/assets/log-pics` |

Alle anderen Installer-Inhalte einschliesslich Launcher, Paket-Metadaten,
Desktop-Aktualisierung, `prerm`, DNS-Altzustandswiederherstellung im Hauptpaket
und `/etc/skel`-Initialisierung bleiben bytegleich. Der Produktionsdiff
entfernt ausschliesslich die beiden Bloecke, ohne Umstrukturierung.

## Reproduktion und Regressionen

`tests/test_deb_postinst_security.py` fuehrt nur die originalen gequoteten
Here-Document-Emitter fuer `DEBIAN/postinst` aus. Die vollstaendigen Builder,
`dpkg`/`dpkg-deb` und eine Paketinstallation werden nicht ausgefuehrt.
Die erzeugten Inhalte werden mit dem Here-Document verglichen und mit
`/bin/sh -n` geprueft; die Builder werden mit `bash -n` geprueft.

In temporaeren Postinstall-Kopien werden ausschliesslich die festen Asset-,
Skeleton- und Systemzustandspfade auf synthetische Pfade umgelegt. `getent`,
`chown`, `nmcli` und `update-desktop-database` sind protokollierende Fakes.
Es gibt keine echten Eigentumswechsel, Benutzerabfragen oder Hostoperationen.

Die Vorher-Laeufe mit unveraenderten Buildern reproduzierten:

- Das Hauptpaket legte `new.png` im synthetischen Benutzerverzeichnis an.
- Beide Pakete schrieben ueber einen `Log-Pics`-Symlink `new.png` in ein
  separates synthetisches Zielverzeichnis.

Die drei betreffenden Regressionen schlugen erwartungsgemaess fehl. Die
Root-Auswirkung einer realen Installation wird daraus abgeleitet; es gab
keine dynamische Root- oder echte `chown`-Ausfuehrung.

Nach der Korrektur pruefen **34 neue Tests** beide Paketvarianten:

- Keine Benutzer-Home-Verarbeitung oder Eigentumsbefehle im generierten Skript.
- Gueltige Syntax der Builder und generierten Skripte.
- Originale Asset-Kopiersegmente liefern PNG-/JPG-/JPEG-Testdateien in die
  erwarteten Paket-Staging-Verzeichnisse.
- Benutzerdateien bleiben fuer `Documents` und `Dokumente` unveraendert:
  regulaere Verzeichnisse, Symlinks auf Dokumenten-, NetMon- und Log-Pics-Ebene
  sowie bestehende und haengende Dateisymlinks. Verglichen werden Inhalte,
  Inodes, Typen, Modi, UID/GID, Linkzahlen, mtime/ctime und Linkziele, ohne
  Verzeichnissymlinks zu verfolgen.
- Skeleton-Befuellung und Desktop-Aktualisierung bleiben funktional;
  bestehende Skeleton-Bilder werden nicht ersetzt.

## Lokale Testnachweise

Alle Tests liefen mit unveraendertem Bubblewrap-Starter und Host-Access-Guard.
Die Probe bestaetigte eine unprivilegierte UID, NoNewPrivs, ein
schreibgeschuetztes Repository, einen privaten Netzwerk-Namespace ohne
Host-Routen und keine Host-Home-/VPN-Konfigurationen oder Dienstesockets.

| Auswahl | Bestanden | Fehler / Skips | Artefakt unter `/tmp/user/1000/` |
| --- | ---: | --- | --- |
| Neue Postinstall-Sicherheitsregressionen | 34 | 0 / 0 | `netmon-isolation-cbiid5qm/junit.xml` |
| Bestehende Packaging-Tests | 12 | 0 / 0 | `netmon-isolation-73gcoyhb/junit.xml` |
| Guard-Selbsttests | 21 | 0 / 0 | `netmon-isolation-73gcoyhb/junit.xml` |

Insgesamt **67 unterschiedliche gezielte Tests bestanden**. Die drei roten
Vorher-Laeufe sind in `netmon-isolation-obp0nxt_`, `netmon-isolation-u0pfn7ce`
und `netmon-isolation-6e1t6q1s` unter demselben temporaeren Verzeichnis
nachvollziehbar. Die lokalen Artefakte sind kein dauerhafter CI-Nachweis.

Ruff, Black und Python-Syntax fuer die neue Testdatei sowie
`git diff --check` bestanden. ShellCheck bestand fuer beide Build-Skripte
und beide extrahierten Postinstall-Skripte. Der Bytevergleich zur Basis
bestaetigt, dass ausser den entfernten Bloecken kein Installer-Inhalt
veraendert wurde. HEAD und Index blieben unveraendert.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q -rs --tb=short tests/test_deb_postinst_security.py \
  tests/test_netmon_deb_packaging.py tests/test_host_access_guard.py
```

## Kompatibilitaet und verbleibende Grenzen

Vorhandene Benutzer erhalten durch das Postinstall keine automatisch
angelegten oder nachgefuellten Log-Pics-Verzeichnisse mehr. Bestehende
Benutzerdateien werden weder migriert noch entfernt oder umbenannt.
Systemweite Assets und Skeleton-Vorlage bleiben verfuegbar.

**Die `/etc/skel`-Initialisierung wurde ausdruecklich nicht gehaertet.**
Ihre Hilfsfunktionen verwenden weiterhin `mkdir`, `find`, `cp` und
symlinkfolgende Dateitests. Sicherer Betrieb setzt voraus, dass `/etc/skel`,
genutzte Unterverzeichnisse und Symlink-Ziele vertrauenswuerdig administriert
werden. Auf benutzerbeschreibbare Ziele umgeleitete Skeleton-Pfade koennen
weiterhin privilegierte Schreibzugriffe ausloesen. Fuer diesen erhaltenen
Pfad wird keine allgemeine Symlink- oder TOCTOU-Sicherheit behauptet.

Andere Installer, bestehende Pakete und systemweite Altzustandsdateien
bleiben ausserhalb der gezielten Korrektur. Kein DEB-Archiv gebaut, keine
echte Installation, Gesamtsuite oder Cloud-Pruefung ausgefuehrt.
About-Arbeiten, andere Sicherheitskorrekturen, Guard und Starter bleiben
unveraendert; `secure-browser/` wurde weder gelesen noch veraendert.

Status: **lokal korrigiert und gezielt getestet; unabhaengige adversariale
Nachpruefung und ausdrueckliche Commit-Freigabe stehen aus.** Kein Commit,
Push oder Deployment.
