# Changelog Hardening

## 29.07.2026 - UFW-sysctl und Diagnose

- UFW-sysctl-Konflikt fuer `log_martians` analysiert: `/etc/ufw/sysctl.conf`
  kann die NetMon-Drop-in-Datei nach dem Boot ueberstimmen.
- NetMon-Haertung kann `net.ipv4.conf.all.log_martians` und
  `net.ipv4.conf.default.log_martians` dauerhaft in `/etc/ufw/sysctl.conf`
  auf `1` setzen.
- Vor der UFW-sysctl-Aenderung wird ein datiertes Backup der UFW-Datei angelegt.
- Baseline-Diagnose nennt abweichende UFW-sysctl-Werte jetzt auch im
  `rp_filter`-Zweig; die profilbezogene Bewertung bleibt unveraendert.

## 19.07.2026 - Baseline 1.0

- GRUB-Passwortschutz eingerichtet
- apt-listchanges installiert
- needrestart bestaetigt
- libpam-tmpdir installiert und aktiv
- Standard-UMASK auf 027 gesetzt
- Kernel-Hardening-Profil eingerichtet
- fs.protected_fifos dauerhaft auf 2 gesetzt
- rp_filter=2 fuer VPN- und Multi-Interface-Betrieb bewusst beibehalten
- Fail2ban jail.local angelegt
- Fail2ban-Konfiguration erfolgreich getestet
- Fail2ban-Dienst aktiv
- dpkg-Konfigurationsreste identifiziert
- Lynis Hardening Index von 65 auf 77 verbessert
- Lynis-Ergebnis: keine Warnungen
