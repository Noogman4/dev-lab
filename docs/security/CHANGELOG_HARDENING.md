# Changelog Hardening

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
