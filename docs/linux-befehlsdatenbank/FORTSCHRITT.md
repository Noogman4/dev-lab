# Ausbau der Linux-Befehlsdokumentation

Veröffentlichter Stand: 100 von 713 Einträgen ausgearbeitet; 613 offen.

Dieser Commit veröffentlicht ausschließlich Codis Bereich 1–100. Die Bereiche 101–200 (Claude) und 201–300 (Browser-Codex) werden getrennt geprüft und veröffentlicht. Ein offener Eintrag im veröffentlichten Index ist keine Aussage über unveröffentlichte Arbeiten anderer Bearbeiter.

Die Original-CSV bleibt unverändert. Jede veröffentlichte Befehlsdatei enthält die zehn vereinbarten Hauptabschnitte. Quellenprüfung, tatsächliche Beispieltests und offene praktische Aspekte stehen in den einzelnen Dokumenten. Der Index enthält die ursprüngliche Zuordnung und SHA-256 der vorhandenen Dateien.

Codis Stoppgrenze 100 ist erreicht. Die Erstellung allein schaltet weitere Dokumente nicht automatisch für die GUI frei. Der Reader wird separat veröffentlicht.

## Veröffentlichte Dokumente

| Nr. | Befehl | Kategorie | Dokument |
| --- | --- | --- | --- |
| 1 | `7z` | Archive & Kompression | [7z.md](7z.md) |
| 2 | `7za` | Archive & Kompression | [7za.md](7za.md) |
| 3 | `ar` | Archive & Kompression | [ar.md](ar.md) |
| 4 | `bunzip2` | Archive & Kompression | [bunzip2.md](bunzip2.md) |
| 5 | `bzcat` | Archive & Kompression | [bzcat.md](bzcat.md) |
| 6 | `bzip2` | Archive & Kompression | [bzip2.md](bzip2.md) |
| 7 | `cpio` | Archive & Kompression | [cpio.md](cpio.md) |
| 8 | `gunzip` | Archive & Kompression | [gunzip.md](gunzip.md) |
| 9 | `gzip` | Archive & Kompression | [gzip.md](gzip.md) |
| 10 | `lz4` | Archive & Kompression | [lz4.md](lz4.md) |
| 11 | `lz4cat` | Archive & Kompression | [lz4cat.md](lz4cat.md) |
| 12 | `lzma` | Archive & Kompression | [lzma.md](lzma.md) |
| 13 | `rar` | Archive & Kompression | [rar.md](rar.md) |
| 14 | `tar` | Archive & Kompression | [tar.md](tar.md) |
| 15 | `unlzma` | Archive & Kompression | [unlzma.md](unlzma.md) |
| 16 | `unrar` | Archive & Kompression | [unrar.md](unrar.md) |
| 17 | `unxz` | Archive & Kompression | [unxz.md](unxz.md) |
| 18 | `unzip` | Archive & Kompression | [unzip.md](unzip.md) |
| 19 | `unzstd` | Archive & Kompression | [unzstd.md](unzstd.md) |
| 20 | `xz` | Archive & Kompression | [xz.md](xz.md) |
| 21 | `xzcat` | Archive & Kompression | [xzcat.md](xzcat.md) |
| 22 | `zcat` | Archive & Kompression | [zcat.md](zcat.md) |
| 23 | `zdiff` | Archive & Kompression | [zdiff.md](zdiff.md) |
| 24 | `zgrep` | Archive & Kompression | [zgrep.md](zgrep.md) |
| 25 | `zip` | Archive & Kompression | [zip.md](zip.md) |
| 26 | `zipinfo` | Archive & Kompression | [zipinfo.md](zipinfo.md) |
| 27 | `zless` | Archive & Kompression | [zless.md](zless.md) |
| 28 | `zstd` | Archive & Kompression | [zstd.md](zstd.md) |
| 29 | `zstdcat` | Archive & Kompression | [zstdcat.md](zstdcat.md) |
| 30 | `aplay` | Audio Video Grafik | [aplay.md](aplay.md) |
| 31 | `arecord` | Audio Video Grafik | [arecord.md](arecord.md) |
| 32 | `convert` | Audio Video Grafik | [convert.md](convert.md) |
| 33 | `exiftool` | Audio Video Grafik | [exiftool.md](exiftool.md) |
| 34 | `ffmpeg` | Audio Video Grafik | [ffmpeg.md](ffmpeg.md) |
| 35 | `ffprobe` | Audio Video Grafik | [ffprobe.md](ffprobe.md) |
| 36 | `identify` | Audio Video Grafik | [identify.md](identify.md) |
| 37 | `magick` | Audio Video Grafik | [magick.md](magick.md) |
| 38 | `mediainfo` | Audio Video Grafik | [mediainfo.md](mediainfo.md) |
| 39 | `mogrify` | Audio Video Grafik | [mogrify.md](mogrify.md) |
| 40 | `pactl` | Audio Video Grafik | [pactl.md](pactl.md) |
| 41 | `pavucontrol` | Audio Video Grafik | [pavucontrol.md](pavucontrol.md) |
| 42 | `play` | Audio Video Grafik | [play.md](play.md) |
| 43 | `playerctl` | Audio Video Grafik | [playerctl.md](playerctl.md) |
| 44 | `sox` | Audio Video Grafik | [sox.md](sox.md) |
| 45 | `wpctl` | Audio Video Grafik | [wpctl.md](wpctl.md) |
| 46 | `apt install` | Aufgabenorientierte Hilfe | [apt_install.md](apt_install.md) |
| 47 | `apt search` | Aufgabenorientierte Hilfe | [apt_search.md](apt_search.md) |
| 48 | `apt update upgrade` | Aufgabenorientierte Hilfe | [apt_update_upgrade.md](apt_update_upgrade.md) |
| 49 | `chmod -R` | Aufgabenorientierte Hilfe | [chmod_r.md](chmod_r.md) |
| 50 | `chown -R` | Aufgabenorientierte Hilfe | [chown_r.md](chown_r.md) |
| 51 | `curl -I` | Aufgabenorientierte Hilfe | [curl_i.md](curl_i.md) |
| 52 | `dd image` | Aufgabenorientierte Hilfe | [dd_image.md](dd_image.md) |
| 53 | `df -h` | Aufgabenorientierte Hilfe | [df_h.md](df_h.md) |
| 54 | `du -sh` | Aufgabenorientierte Hilfe | [du_sh.md](du_sh.md) |
| 55 | `find -name` | Aufgabenorientierte Hilfe | [find_name.md](find_name.md) |
| 56 | `find -size` | Aufgabenorientierte Hilfe | [find_size.md](find_size.md) |
| 57 | `ip addr` | Aufgabenorientierte Hilfe | [ip_addr.md](ip_addr.md) |
| 58 | `ip route` | Aufgabenorientierte Hilfe | [ip_route.md](ip_route.md) |
| 59 | `ss -tulpen` | Aufgabenorientierte Hilfe | [ss_tulpen.md](ss_tulpen.md) |
| 60 | `tail -f` | Aufgabenorientierte Hilfe | [tail_f.md](tail_f.md) |
| 61 | `borg` | Backup & Sync | [borg.md](borg.md) |
| 62 | `clonezilla` | Backup & Sync | [clonezilla.md](clonezilla.md) |
| 63 | `ddrescue` | Backup & Sync | [ddrescue.md](ddrescue.md) |
| 64 | `deja-dup` | Backup & Sync | [deja_dup.md](deja_dup.md) |
| 65 | `duplicity` | Backup & Sync | [duplicity.md](duplicity.md) |
| 66 | `partclone` | Backup & Sync | [partclone.md](partclone.md) |
| 67 | `rclone` | Backup & Sync | [rclone.md](rclone.md) |
| 68 | `restic` | Backup & Sync | [restic.md](restic.md) |
| 69 | `rsnapshot` | Backup & Sync | [rsnapshot.md](rsnapshot.md) |
| 70 | `timeshift` | Backup & Sync | [timeshift.md](timeshift.md) |
| 71 | `bind` | Bash Builtins | [bind.md](bind.md) |
| 72 | `break` | Bash Builtins | [break.md](break.md) |
| 73 | `caller` | Bash Builtins | [caller.md](caller.md) |
| 74 | `case` | Bash Builtins | [case.md](case.md) |
| 75 | `continue` | Bash Builtins | [continue.md](continue.md) |
| 76 | `coproc` | Bash Builtins | [coproc.md](coproc.md) |
| 77 | `do` | Bash Builtins | [do.md](do.md) |
| 78 | `done` | Bash Builtins | [done.md](done.md) |
| 79 | `elif` | Bash Builtins | [elif.md](elif.md) |
| 80 | `else` | Bash Builtins | [else.md](else.md) |
| 81 | `enable` | Bash Builtins | [enable.md](enable.md) |
| 82 | `esac` | Bash Builtins | [esac.md](esac.md) |
| 83 | `fc` | Bash Builtins | [fc.md](fc.md) |
| 84 | `fi` | Bash Builtins | [fi.md](fi.md) |
| 85 | `for` | Bash Builtins | [for.md](for.md) |
| 86 | `function` | Bash Builtins | [function.md](function.md) |
| 87 | `hash` | Bash Builtins | [hash.md](hash.md) |
| 88 | `if` | Bash Builtins | [if.md](if.md) |
| 89 | `in` | Bash Builtins | [in.md](in.md) |
| 90 | `let` | Bash Builtins | [let.md](let.md) |
| 91 | `logout` | Bash Builtins | [logout.md](logout.md) |
| 92 | `readarray` | Bash Builtins | [readarray.md](readarray.md) |
| 93 | `return` | Bash Builtins | [return.md](return.md) |
| 94 | `then` | Bash Builtins | [then.md](then.md) |
| 95 | `typeset` | Bash Builtins | [typeset.md](typeset.md) |
| 96 | `until` | Bash Builtins | [until.md](until.md) |
| 97 | `while` | Bash Builtins | [while.md](while.md) |
| 98 | `addgroup` | Benutzer & Rechte | [addgroup.md](addgroup.md) |
| 99 | `adduser` | Benutzer & Rechte | [adduser.md](adduser.md) |
| 100 | `chage` | Benutzer & Rechte | [chage.md](chage.md) |
