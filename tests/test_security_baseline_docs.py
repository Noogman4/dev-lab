from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SECURITY_DOCS = REPO_ROOT / "docs" / "security"


def _read_doc(name: str) -> str:
    return (SECURITY_DOCS / name).read_text(encoding="utf-8")


def test_security_docs_exist():
    expected = {
        "SECURITY_BASELINE.md",
        "HARDENING_CHECKLIST.md",
        "KERNEL_SYSCTL.md",
        "CHANGELOG_HARDENING.md",
    }
    assert SECURITY_DOCS.is_dir()
    assert expected.issubset({path.name for path in SECURITY_DOCS.iterdir()})


def test_security_baseline_contains_required_reference_values():
    content = _read_doc("SECURITY_BASELINE.md")

    for expected_line in (
        "Name: NetMon Security Baseline",
        "Profil: Desktop / Development",
        "Version: 1.0",
        "Referenzsystem: Zorin OS 18",
        "Basis: Ubuntu 24.04",
        "Stand: 19.07.2026",
        "Hardening Index: 77",
        "Warnungen: 0",
        "Tests: 248",
        "kernel.kptr_restrict = 2",
        "kernel.sysrq = 0",
        "kernel.perf_event_paranoid = 3",
        "kernel.unprivileged_bpf_disabled = 1",
        "fs.protected_fifos = 2",
        "net.ipv4.conf.all.log_martians = 1",
        "net.ipv4.conf.default.log_martians = 1",
        "net.ipv4.conf.default.accept_source_route = 0",
        "net.ipv4.conf.all.rp_filter = 2",
        "net.ipv4.conf.default.rp_filter = 2",
        "kernel.modules_disabled = 1",
    ):
        assert expected_line in content

    assert "Secure-Boot-Status und UEFI-Plattformmodus dokumentiert" in content
    assert "nicht automatisch als" in content
    assert "bewusste und zulaessige Konfiguration" in content
    assert "hoeherer Lynis-Wert bedeutet nicht automatisch" in content
    assert "zorin_desktop_development" in content
    assert "ubuntu_server_hardening" in content
    assert "zorin_vpn_multi_interface" in content
    assert "ubuntu_vpn_multi_interface" in content
    assert "fedora_workstation_review" in content
    assert "`check`: rein lesende Pruefung des Ist-Zustands" in content
    assert (
        "`apply hardening`: spaeterer, explizit freigegebener Umsetzungspfad" in content
    )
    assert "rollback hint" in content
    assert (
        "Desktop-/Development-, Server- und VPN-/Multi-Interface-Regelprofil" in content
    )
    assert "Transferpaket" in content
    assert "exportieren und wieder importieren" in content


def test_hardening_checklist_contains_required_checks_and_statuses():
    content = _read_doc("HARDENING_CHECKLIST.md")

    for expected_line in (
        "- Erfuellt",
        "- Nicht erfuellt",
        "- Nicht anwendbar",
        "- Bewusste Abweichung",
        "- Manuelle Pruefung erforderlich",
        "[ ] UFW installiert",
        "[ ] UFW aktiv",
        "[ ] Fail2ban installiert",
        "[ ] Fail2ban aktiv",
        "[ ] /etc/fail2ban/jail.local vorhanden",
        "[ ] Lynis installiert",
        "[ ] rkhunter installiert",
        "[ ] ClamAV installiert",
        "[ ] apt-listchanges installiert",
        "[ ] needrestart installiert",
        "[ ] libpam-tmpdir installiert",
        "[ ] UMASK 027 gesetzt",
        "[ ] GRUB-Passwortschutz erkannt",
        "[ ] Kernelparameter entsprechen dem Desktop-/Development-Profil",
        "[ ] Alte dpkg-Konfigurationsreste geprueft",
        "[ ] Kritische Systemdateirechte geprueft",
        "[ ] AppArmor aktiv",
        "[ ] Benutzerdefinierte UFW-Regeln vorhanden",
        "[ ] Ausstehende APT-Paketupdates",
    ):
        assert expected_line in content


def test_kernel_sysctl_doc_contains_required_parameters_and_loader_example():
    content = _read_doc("KERNEL_SYSCTL.md")

    for expected_line in (
        "/usr/lib/sysctl.d/",
        "/run/sysctl.d/",
        "/etc/sysctl.d/",
        "/etc/sysctl.conf",
        "/usr/lib/sysctl.d/99-protect-links.conf",
        "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "kernel.kptr_restrict",
        "kernel.sysrq",
        "kernel.perf_event_paranoid",
        "kernel.unprivileged_bpf_disabled",
        "fs.protected_fifos",
        "net.ipv4.conf.all.log_martians",
        "net.ipv4.conf.default.log_martians",
        "net.ipv4.conf.default.accept_source_route",
        "net.ipv4.conf.all.rp_filter",
        "net.ipv4.conf.default.rp_filter",
        "kernel.modules_disabled",
    ):
        assert expected_line in content

    assert "bewusste" in content
    assert "VPN-, WireGuard- und" in content


def test_hardening_changelog_contains_initial_entry():
    content = _read_doc("CHANGELOG_HARDENING.md")

    for expected_line in (
        "## 19.07.2026 - Baseline 1.0",
        "- GRUB-Passwortschutz eingerichtet",
        "- apt-listchanges installiert",
        "- needrestart bestaetigt",
        "- libpam-tmpdir installiert und aktiv",
        "- Standard-UMASK auf 027 gesetzt",
        "- Kernel-Hardening-Profil eingerichtet",
        "- fs.protected_fifos dauerhaft auf 2 gesetzt",
        "- rp_filter=2 fuer VPN- und Multi-Interface-Betrieb bewusst beibehalten",
        "- Fail2ban jail.local angelegt",
        "- Fail2ban-Konfiguration erfolgreich getestet",
        "- Fail2ban-Dienst aktiv",
        "- dpkg-Konfigurationsreste identifiziert",
        "- Lynis Hardening Index von 65 auf 77 verbessert",
        "- Lynis-Ergebnis: keine Warnungen",
    ):
        assert expected_line in content
