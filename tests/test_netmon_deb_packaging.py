import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_deb_builder_uses_debian_compliant_install_locations():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_deb.sh").read_text(
        encoding="utf-8"
    )

    assert 'APP_ROOT="$PKG_DIR/usr/lib/netmon"' in source
    assert 'ASSETS_ROOT="$PKG_DIR/usr/share/netmon/assets"' in source
    assert 'FUN_ASSETS_ROOT="$ASSETS_ROOT/fun"' in source
    assert 'DOCS_ROOT="$PKG_DIR/usr/share/doc/netmon"' in source
    assert 'NETMON_HOME="/usr/lib/netmon"' in source
    assert 'ASSET_DIR="/usr/share/netmon/assets/log-pics"' in source
    assert 'APP_ROOT="$PKG_DIR/opt/netmon"' not in source


def test_main_deb_builder_bundles_code_the_classics_in_system_asset_path():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_deb.sh").read_text(
        encoding="utf-8"
    )

    assert '"$ROOT_DIR/netmon/features/Code-the-Classics.zip"' in source
    assert '"$FUN_ASSETS_ROOT/Code-the-Classics.zip"' in source


def test_main_deb_builder_generates_required_policy_artifacts():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_deb.sh").read_text(
        encoding="utf-8"
    )

    assert 'copy_file "$ROOT_DIR/packaging/copyright"' in source
    assert '"$DOCS_ROOT/changelog.gz"' in source
    assert '"$MAN_ROOT/netmon.1.gz"' in source
    assert '"$MAN_ROOT/netmon-uninstall.1.gz"' in source
    assert "xargs -0 md5sum > DEBIAN/md5sums" in source
    assert 'find "$PKG_DIR" -type d -exec chmod 0755' in source
    assert 'find "$PKG_DIR" -type f -exec chmod 0644' in source


def test_main_deb_builder_only_restores_legacy_install_dns():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_deb.sh").read_text(
        encoding="utf-8"
    )

    assert 'NETMON_INSTALL_DNS_STATE="$NETMON_STATE_DIR/install-dns-nm.state"' in source
    assert "restore_legacy_install_dns" in source
    assert "apply_netmon_install_dns" not in source
    assert "NETMON_INSTALL_DNS_SERVER" not in source
    assert "8.8.8.8" not in source
    assert 'cat > "$PKG_DIR/DEBIAN/prerm"' in source
    assert "restore_netmon_install_dns" in source
    assert 'ipv4.dns "$OLD_DNS"' in source
    assert 'rm -f "$NETMON_INSTALL_DNS_STATE"' in source
    assert '"$PKG_DIR/DEBIAN/prerm"' in source


def test_main_deb_policy_sources_exist():
    for relative_path in (
        "packaging/copyright",
        "packaging/changelog",
        "packaging/netmon.1",
        "packaging/netmon-uninstall.1",
        "packaging/netmon.doc-base",
        "packaging/netmon.lintian-overrides",
    ):
        assert (PROJECT_ROOT / relative_path).is_file()


def test_deb_builders_do_not_duplicate_code_the_classics_archive():
    for script_name in ("build_netmon_deb.sh", "build_test_deb.sh"):
        source = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert 'rm -f "$APP_PY_ROOT/features/Code-the-Classics.zip"' in source
        assert '"$FUN_ASSETS_ROOT/Code-the-Classics.zip"' in source


def test_site_bundle_publishes_current_r12_audit_and_keeps_archives():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_site_bundle.sh").read_text(
        encoding="utf-8"
    )

    assert 'CURRENT_AUDIT_VERSIONED_HTML="security-audit-r12.html"' in source
    assert 'require_file "$ROOT_DIR/site/security-audit-r10.html"' in source
    assert 'require_file "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf"' in source
    assert 'require_file "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf"' in source
    assert (
        'cp "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf" '
        '"$PUBLIC_DIR/netmon_security_audit_2026.pdf"'
    ) in source
    assert (
        'cp "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf" '
        '"$PUBLIC_DIR/netmon_security_audit_2026_r11.pdf"'
    ) in source


def test_release_update_bundle_includes_r12_html_pdf_and_r11_pdf_archive():
    source = (
        PROJECT_ROOT / "scripts" / "build_netmon_release_update_bundle.sh"
    ).read_text(encoding="utf-8")

    assert 'require_file "$ROOT_DIR/site/security-audit.html"' in source
    assert 'require_file "$ROOT_DIR/site/security-audit-r10.html"' in source
    assert 'require_file "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf"' in source
    assert 'require_file "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf"' in source
    assert (
        'cp "$ROOT_DIR/site/security-audit.html" '
        '"$PUBLIC_DIR/security-audit-r12.html"'
    ) in source
    assert (
        'cp "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf" '
        '"$PUBLIC_DIR/netmon_security_audit_2026.pdf"'
    ) in source
    assert (
        'cp "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf" '
        '"$PUBLIC_DIR/netmon_security_audit_2026_r11.pdf"'
    ) in source
    assert 'echo "  public_html/security-audit-r12.html"' in source


def test_release_builders_derive_version_and_require_signatures():
    for script_name in (
        "build_netmon_deb.sh",
        "build_netmon_site_bundle.sh",
        "build_netmon_release_update_bundle.sh",
    ):
        source = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert 'scripts/read_netmon_version.py")"' in source

    for script_name in (
        "build_netmon_site_bundle.sh",
        "build_netmon_release_update_bundle.sh",
    ):
        source = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "NETMON_ALLOW_UNSIGNED_BUILD" in source
        assert "Release-Abbruch: minisign ist nicht installiert." in source
        assert 'python3 "$ROOT_DIR/scripts/check_release_consistency.py"' in source
        assert '"$MINISIGN_VERIFY_SCRIPT"' in source
        assert 'cmp -s "$RELEASE_MINISIGN_PUBKEY" "$PINNED_MINISIGN_PUBKEY"' in source
        assert "maybe_sign_release" not in source


def test_current_release_metadata_is_consistent():
    result = subprocess.run(
        [sys.executable, "scripts/check_release_consistency.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_signature_verifier_rejects_mismatched_pinned_key(tmp_path):
    public_key = tmp_path / "netmonroots.minisign.pub"
    signature = tmp_path / "SHA256SUMS.minisig"
    sums = tmp_path / "SHA256SUMS"
    public_key.write_text("untrusted comment: test\nRWACTUAL\n", encoding="utf-8")
    signature.write_text("test", encoding="utf-8")
    sums.write_text("test", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            "scripts/verify_netmon_signature.sh",
            str(public_key),
            str(signature),
            str(sums),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "NETMON_EXPECTED_MINISIGN_PUBKEY": "RWEXPECTED"},
        check=False,
    )

    assert result.returncode == 1
    assert "stimmt nicht" in result.stderr


def test_release_public_key_is_pinned_in_repository_and_policy():
    key_file = PROJECT_ROOT / "docs" / "security" / "netmonroots.minisign.pub"
    key_lines = [
        line.strip()
        for line in key_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    policy = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert key_lines == [
        "untrusted comment: minisign public key 54BF5F1867BDD004",
        "RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R",
    ]
    assert key_lines[0].rsplit(" ", 1)[-1] in policy
    assert key_lines[1] in policy
