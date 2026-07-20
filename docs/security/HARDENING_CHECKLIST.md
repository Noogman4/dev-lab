# Hardening Checklist

## Statusdefinitionen

- Erfuellt
- Nicht erfuellt
- Nicht anwendbar
- Bewusste Abweichung
- Manuelle Pruefung erforderlich

Hinweis:

- Die Checkliste dient als lesende Soll-/Ist-Abgleichsliste.
- Eine Abweichung ist nicht automatisch kritisch, sondern muss gegen das
  Einsatzprofil bewertet werden.

## Baseline-Checks

| Pruefung | Zielstatus | Typische Lesekontrolle | Bewertungsnotiz |
| --- | --- | --- | --- |
| [ ] UFW installiert | Erfuellt | `dpkg -l ufw` | Paketstatus lesend pruefen |
| [ ] UFW aktiv | Erfuellt | `ufw status verbose` | Bei alternativer Firewall manuell bewerten |
| [ ] Fail2ban installiert | Erfuellt | `dpkg -l fail2ban` | Paketstatus lesend pruefen |
| [ ] Fail2ban aktiv | Erfuellt | `systemctl is-active fail2ban` | Dienststatus lesen, nicht aendern |
| [ ] /etc/fail2ban/jail.local vorhanden | Erfuellt | `test -f /etc/fail2ban/jail.local` | Datei nur pruefen |
| [ ] Lynis installiert | Erfuellt | `dpkg -l lynis` | Paketstatus lesend pruefen |
| [ ] rkhunter installiert | Erfuellt | `dpkg -l rkhunter` | Paketstatus lesend pruefen |
| [ ] ClamAV installiert | Erfuellt | `dpkg -l clamav` | Paketstatus lesend pruefen |
| [ ] apt-listchanges installiert | Erfuellt | `dpkg -l apt-listchanges` | Paketstatus lesend pruefen |
| [ ] needrestart installiert | Erfuellt | `dpkg -l needrestart` | Paketstatus lesend pruefen |
| [ ] libpam-tmpdir installiert | Erfuellt | `dpkg -l libpam-tmpdir` | Paketstatus lesend pruefen |
| [ ] UMASK 027 gesetzt | Erfuellt | `grep -RHE "(UMASK|umask)"` | Wert und Quelle auswerten; Konflikte manuell bewerten |
| [ ] Home-Verzeichnisrechte sicher konfiguriert | Erfuellt | `find /home -maxdepth 1 -mindepth 1 -type d -printf "%m %u %g %p\\n"` | Schreibrechte fuer Gruppe/Andere automatisch bewerten; ACLs und Sonderfaelle manuell |
| [ ] GRUB-Passwortschutz erkannt | Erfuellt | `grep -E "password|pbkdf2" /boot/grub/grub.cfg` | Nur lesend bewerten |
| [ ] Kernelparameter entsprechen dem Desktop-/Development-Profil | Erfuellt | `sysctl <parameter>` | `rp_filter=2` kann bewusste Soll-Abweichung gegenueber Lynis sein |
| [ ] Alte dpkg-Konfigurationsreste geprueft | Manuelle Pruefung erforderlich | `dpkg -l | awk '/^rc/ {print $2}'` | Nicht automatisch bereinigen |
| [ ] Kritische Systemdateirechte geprueft | Erfuellt | `stat /etc/passwd /etc/shadow /etc/sudoers` | Bekannte sichere Rechte/Eigentuemer automatisch bewerten |
| [ ] AppArmor aktiv | Erfuellt | `aa-status` | Falls Tool fehlt, manuell pruefen |
| [ ] Benutzerdefinierte UFW-Regeln vorhanden | Erfuellt | `LANG=C LC_ALL=C ufw status numbered` | Zaehlt nummerierte Regeln; bewertet nicht die fachliche Qualitaet |
| [ ] Ausstehende APT-Paketupdates | Manuelle Pruefung erforderlich | `LANG=C LC_ALL=C apt list --upgradable` | Zaehlt verfuegbare Updates; keine Aussage ueber Sicherheitsrelevanz |

## Einordnung von Abweichungen

- Secure Boot deaktiviert: nicht automatisch kritisch.
- `rp_filter=2`: auf VPN-, WireGuard- und Multi-Interface-Systemen als
  bewusste Abweichung bzw. als profilgerechte Konfiguration zulassen.
- `kernel.modules_disabled=1`: nicht als Pflichtziel setzen, da Desktop- und
  Entwicklungsumgebungen hiervon funktional beeintraechtigt werden koennen.

## Empfohlene Ergebnisdarstellung fuer NetMon

NetMon sollte spaeter pro Check mindestens folgende Felder lesend abbilden:

- Pruefname
- Sollwert oder Sollzustand
- Ist-Wert
- Status
- Begruendung
- Quelle oder Lesebefehl
- Zeitstempel der Pruefung
