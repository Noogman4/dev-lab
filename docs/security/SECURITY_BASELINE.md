# NetMon Security Baseline

Name: NetMon Security Baseline
Profil: Desktop / Development
Version: 1.0
Referenzsystem: Zorin OS 18
Basis: Ubuntu 24.04
Stand: 19.07.2026

## Zweck und Geltungsbereich

Diese Baseline beschreibt einen dokumentierten Referenzzustand fuer Linux-Desktop-
und Entwicklungsrechner im NetMon-Kontext. Sie ist als nachvollziehbare Soll-
Beschreibung fuer spaetere, rein lesende NetMon-Pruefungen gedacht.

Grundsaetze:

- Nur lesende und technisch pruefbare Kontrollen als Baseline-Soll.
- Keine automatische Aenderung von Systemdateien.
- Keine pauschale Bewertung einzelner Lynis-Empfehlungen ohne Profilbezug.
- Abweichungen muessen gegen Desktop-, Entwicklungs-, VPN- und Multi-Interface-
  Anforderungen bewertet werden.

## Profilkatalog und Uebertragbarkeit

Die aktuelle Baseline ist zuerst fuer `Zorin OS 18 / Ubuntu 24.04` definiert.
Sie dient als Referenzprofil und nicht als blindes Haertungsskript fuer beliebige
Linux-Systeme.

Profilkatalog fuer die weitere Umsetzung in NetMon:

- `zorin_desktop_development`
- `ubuntu_desktop_development`
- `debian_desktop_development`
- `ubuntu_server_hardening`
- `zorin_vpn_multi_interface`
- `ubuntu_vpn_multi_interface`
- `fedora_workstation_review`

Einordnung:

- Debian-/Ubuntu-nahe Systeme koennen viele Sollwerte direkt uebernehmen.
- Fedora-, RHEL- oder andere RPM-basierte Systeme brauchen eigene Adapter fuer
  Paketmanager, Firewall, Dienstnamen und Defaults.
- Server-, Desktop-, Testlabor-, Dual-Boot- und Entwicklungsprofile duerfen
  nicht mit identischen Haertungsmassnahmen behandelt werden.
- Eine Baseline ist zunaechst ein Bewertungsmodell; automatisierte Haertung
  braucht pro Profil eine explizite Freigabe und Rueckfallstrategie.

## Geplante Apply-/Rollback-Struktur

Die Baseline wird in NetMon in drei Schichten getrennt:

- `check`: rein lesende Pruefung des Ist-Zustands
- `baseline profile`: distributions- und profilbezogene Sollwerte
- `apply hardening`: spaeterer, explizit freigegebener Umsetzungspfad

Fuer spaetere automatische oder teilautomatische Haertung gelten diese Regeln:

- Nur mit vorhandenen Administratorrechten und ohne unnoetige Passwortabfragen
- Nur fuer Checks mit dokumentierter `apply strategy`
- Vor Aenderungen Ausgangszustand dokumentieren oder sichern
- Jede Aenderung braucht einen `rollback hint`
- PAM-, Boot-, Firewall- und Netzwerkpfade gelten als besonders sensitiv

Aktueller Stand am Sonntag, 19. Juli 2026:

- `sysctl` besitzt eine erste freigegebene Apply-Stufe ueber eine dedizierte
  Drop-in-Datei
- `ufw` besitzt eine erste freigegebene Apply-Stufe ueber ein explizites
  Desktop-/Development-, Server- und VPN-/Multi-Interface-Regelprofil
- ein JSON-`Transferpaket` kann die freigegebenen `sysctl`- und `ufw`-Anteile
  fuer andere Zorin-/Ubuntu-nahe Systeme exportieren und wieder importieren
- freie Regelableitung oder profilfremde Firewall-Aenderungen sind bewusst
  nicht Teil dieser Stufe

## Bootschutz

Erwartete Referenzmerkmale:

- UEFI aktiv
- GRUB2 vorhanden
- GRUB-Passwortschutz aktiv
- Secure-Boot-Status und UEFI-Plattformmodus dokumentiert

Bewertung:

- Ein deaktiviertes Secure Boot wird im Desktop-/Development-Profil nicht
  automatisch als kritischer Fehler gewertet, soll aber als bewusste
  Konfigurationsentscheidung dokumentiert werden.
- Deaktiviertes Secure Boot ist nicht automatisch als Systemfehler zu bewerten.
- Setup Mode, User Mode, Legacy-BIOS-/Nicht-UEFI-Zustaende und technische
  Prueffehler werden getrennt ausgewiesen.
- Die Einordnung haengt von Hardware, Treibern, Virtualisierung, Signaturketten
  und eingesetzten Entwicklungswerkzeugen ab.

Lesende Pruefbefehle:

```bash
test -d /sys/firmware/efi && echo UEFI || echo Legacy-BIOS
grub-install --version
sudo grep -E "password|pbkdf2" /boot/grub/grub.cfg
LANG=C LC_ALL=C mokutil --sb-state
```

## Firewall und Netzwerkschutz

Erwartete Referenzmerkmale:

- UFW aktiv
- Fail2ban installiert und aktiv
- `/etc/fail2ban/jail.local` vorhanden
- Eine SSH-Jail darf vorhanden oder konfiguriert sein, auch wenn lokal kein
  SSH-Dienst laeuft
- VPN-, WireGuard- und Multi-Interface-Systeme muessen bei der Bewertung
  beruecksichtigt werden

Bewertung:

- Ein nicht leerer Firewall-Regelsatz ist wichtiger als starre Einzelforderungen
  ohne Netzwerkkontext.
- Bei VPN- oder Multi-Interface-Betrieb koennen abweichende Regeln oder
  Interface-Ausnahmen technisch notwendig und bewusst gesetzt sein.

Lesende Pruefbefehle:

```bash
ufw status verbose
systemctl is-enabled ufw
systemctl is-active ufw
dpkg -l fail2ban
systemctl is-enabled fail2ban
systemctl is-active fail2ban
test -f /etc/fail2ban/jail.local
```

## Sicherheitswerkzeuge

Im Referenzprofil beruecksichtigte Werkzeuge:

- Lynis
- rkhunter
- ClamAV
- Fail2ban
- apt-listchanges
- needrestart
- libpam-tmpdir
- debsums, falls vorhanden

Bewertung:

- Nicht jedes Werkzeug ist in jedem Einsatzprofil gleich wichtig.
- `debsums` ist bewusst als optional dokumentiert, weil nicht jede Installation
  das Paket standardmaessig enthaelt.
- Ausstehende APT-Paketupdates zeigen Wartungsbedarf an, sind aber ohne
  separate Sicherheitsbewertung keine Aussage ueber konkrete Paketrisiken.

Lesende Pruefbefehle:

```bash
dpkg -l lynis rkhunter clamav fail2ban apt-listchanges needrestart libpam-tmpdir
dpkg -l debsums
LANG=C LC_ALL=C apt list --upgradable 2>/dev/null
```

## Authentifizierung und Dateirechte

Erwartete Referenzmerkmale:

- `UMASK 027` oder `umask 027` in aktiven, nicht auskommentierten Systemquellen
- PAM-Passwortstaerke aktiv
- keine Konten ohne Passwort
- eindeutige Benutzer- und Gruppen-IDs
- Home-Verzeichnisrechte sicher konfiguriert
- kritische Systemdateirechte fuer `/etc/passwd`, `/etc/shadow` und `/etc/sudoers`
  entsprechen bekannten sicheren Standardwerten

Bewertung:

- Die Baseline fordert keine automatische Aenderung von PAM-, Shadow- oder
  Home-Rechten.
- Offensichtlich restriktive Home-Rechte werden automatisch als erfuellt
  bewertet. Schreibrechte fuer Gruppe oder andere Benutzer gelten als nicht
  erfuellt; ACLs, Eigentuemerabweichungen und Sonderpfade bleiben pruefpflichtig.
- Bekannte sichere Rechte und Eigentuemer kritischer Systemdateien werden
  automatisch bewertet; ungewoehnliche, aber potenziell sichere Sonderfaelle
  bleiben pruefpflichtig.

Lesende Pruefbefehle:

```bash
grep -RHE '^[[:space:]]*(UMASK|umask)[[:space:]]+[0-7]{3,4}([[:space:]]|$)' /etc/login.defs /etc/profile /etc/profile.d 2>/dev/null
grep -R "pam_pwquality\\|pam_cracklib" /etc/pam.d 2>/dev/null
awk -F: '($2==""){print $1}' /etc/shadow
getent passwd
getent group
find /home -maxdepth 1 -mindepth 1 -type d -printf "%m %u %g %p\n"
stat -c "%a %U %G %n" /etc/passwd /etc/shadow /etc/sudoers
```

## Kernel-Hardening

Folgende Werte sind im Desktop-/Development-Profil zu pruefen:

```ini
kernel.kptr_restrict = 2
kernel.sysrq = 0
kernel.perf_event_paranoid = 3
kernel.unprivileged_bpf_disabled = 1
fs.protected_fifos = 2
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.default.rp_filter = 2
```

Profilhinweis:

- `net.ipv4.conf.all.rp_filter = 2` und
  `net.ipv4.conf.default.rp_filter = 2` sind bei VPN-, WireGuard- und
  Multi-Interface-Systemen als bewusste und zulaessige Konfiguration zu
  behandeln.
- Diese Werte duerfen nicht pauschal als unsicher bewertet werden, nur weil
  Lynis in einzelnen Szenarien den Wert `1` erwartet.

Bewusst nicht erzwungen:

```ini
kernel.modules_disabled = 1
```

Begruendung:

Das dauerhafte Deaktivieren des Ladens von Kernelmodulen kann auf Desktop-,
Entwicklungs-, Treiber-, VPN- und Hardware-Systemen erhebliche
Funktionsprobleme verursachen. Im NetMon-Kontext wird dieser Wert deshalb nicht
als generelle Pflichtvorgabe definiert.

Lesende Pruefbefehle:

```bash
sysctl kernel.kptr_restrict
sysctl kernel.sysrq
sysctl kernel.perf_event_paranoid
sysctl kernel.unprivileged_bpf_disabled
sysctl fs.protected_fifos
sysctl net.ipv4.conf.all.log_martians
sysctl net.ipv4.conf.default.log_martians
sysctl net.ipv4.conf.default.accept_source_route
sysctl net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.default.rp_filter
```

## Lynis-Referenz

Zuletzt dokumentierter Referenzstand:

```text
Hardening Index: 77
Warnungen: 0
Tests: 248
```

Einordnung:

- Ein hoeherer Lynis-Wert bedeutet nicht automatisch ein sichereres oder fuer
  den Einsatzzweck besser geeignetes System.
- Entscheidend ist, ob Schutzwirkung, Funktionsfaehigkeit und Betriebsprofil
  zusammenpassen.

Lesende Pruefbefehle:

```bash
lynis audit system --quick
grep -E "Hardening index|Warnings|Tests performed" /var/log/lynis.log
```

## Pruefstrategie fuer NetMon

Die spaetere technische Umsetzung in NetMon soll diese Baseline zunaechst nur
lesend bewerten:

- Paket- und Dienststatus lesen
- Datei- oder Konfigurationsvorhandensein lesen
- `sysctl`-Werte lesen
- bekannte Ausnahmen als "bewusste Abweichung" oder "manuelle Pruefung
  erforderlich" markieren

Nicht Teil dieser Baseline sind automatische Aenderungen an:

- `chmod`
- `sysctl --system`
- Paketinstallationen
- Dienstaktivierungen
- GRUB-, PAM- oder Kernel-Konfigurationen
