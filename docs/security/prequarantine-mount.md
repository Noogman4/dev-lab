# Vor-Quarantäne: fester tmpfs-Mountpunkt

## Nachtrag 12.11.2026

Finding: **Pre-quarantine can mount tmpfs over an attacker-selected host
directory** (Scan `4852934e`, Finding 1, HIGH, Revision `bac02d28`).

Bisher hängte NetMon das tmpfs per `sudo mount` an einem Pfad ein, den die
Benutzereinstellung vorgab oder der aus einer Kandidatenliste kam. Die Liste
enthielt auch `/dev/shm/netmon_roots/download_scan` und
`/tmp/netmon_roots/download_scan`. Bei einem tmpfs-Elternordner versuchte NetMon
nur ein `remount` des Unterordners. Das scheitert, weil der Unterordner kein
Mountpunkt ist. Auf Systemen ohne tmpfs-`/tmp` landete der erste echte Mount
deshalb im gemeinsamen `/tmp`. `os.makedirs` und `mount` folgen Symlinks. Ein
vorher angelegter Symlink, von einem anderen lokalen Konto in `/tmp` oder von
derselben UID über die Einstellung, konnte das tmpfs mit `uid=<Benutzer>` über
einen Systemordner wie `/etc` legen.

Neues Verhalten (`netmon/core/prequarantine_mount.py`):

- Root hängt nur noch `/run/netmon-prequarantine/<uid>` ein. Beide Ordner legt
  root per `install -d -o root -g root -m 0755` unter dem root-eigenen `/run`
  an. Kein unprivilegierter Prozess, auch nicht dieselbe UID, kann eine
  Komponente zwischen Prüfung und Mount austauschen.
- Vor dem Mount prüft NetMon per `lstat`, dass `/run`, `/run/netmon-prequarantine`
  und der Endordner echte Verzeichnisse sind, root gehören und nicht für Gruppe
  oder andere beschreibbar sind. Ein vorhandener Mount am festen Punkt wird
  weder vorbereitet noch überlagert. Jede Abweichung bricht ab.
- Nach dem Mount muss `/proc/self/mountinfo` genau an diesem Punkt ein tmpfs mit
  Quelle `tmpfs` und `noexec,nosuid,nodev` zeigen. Der Ordner muss dem Benutzer
  gehören und Modus `0700` haben. Erst dann übernimmt NetMon den Pfad in die
  Einstellungen.
- Benutzerpfade, `/tmp` und `/dev/shm` sind keine Mount-Ziele mehr. Liegt der
  eingestellte Ordner bereits in einem noexec-tmpfs, nutzt NetMon ihn ohne
  privilegierte Aktion.
- Deaktivieren hängt nur noch genau das NetMon-tmpfs am festen Punkt aus.
  Früher konnte ein eingestellter Pfad in einem System-tmpfs mit `noexec`
  (z. B. `/run/lock`) an `sudo umount` gehen. Danach und nach einem Neustart
  fällt der Temp-Ordner auf den unprivilegierten Standard zurück.

Grenzen:

- Mounts, die eine ältere Version an anderen Pfaden angelegt hat, werden nicht
  automatisch ausgehängt. Sie verschwinden beim Neustart oder durch manuelles
  `umount`.
- Der unprivilegierte Standardpfad (ohne Mount) kann weiterhin unter
  `/dev/shm` oder `/tmp` liegen, wenn `XDG_RUNTIME_DIR` fehlt. Root ist dort
  nicht beteiligt.

Validierung: `tests/test_prequarantine_mount.py` (22 Tests) mit simulierten
Befehlen und eigener mountinfo-Datei. Abgedeckt sind ein gepflanzter Symlink
im Benutzerpfad, ein symlinkter Endordner oder Elternordner, fremde Besitzer,
beschreibbare Eltern, ein fremder Mount am festen Punkt, ein Mount ohne
`noexec`, ein abgebrochenes sudo und Unmount-Ziele. Es wurde kein echtes
sudo, `mount` oder `umount` ausgeführt.
