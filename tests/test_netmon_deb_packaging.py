import subprocess
import sys
import json
import shutil
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


def test_main_deb_builder_never_restores_legacy_install_dns():
    import re

    source = (PROJECT_ROOT / "scripts/build_netmon_deb.sh").read_text()
    for phase in ("postinst", "prerm"):
        match = re.search(
            rf"^cat > \"\$PKG_DIR/DEBIAN/{phase}\" <<'([A-Z]+)'\n(.*?)^\1$",
            source,
            re.M | re.S,
        )
        assert match is not None
        assert not re.search(r"\b(nmcli|resolvectl|systemctl|nft|sudo)\b", match[2])
        assert not re.search(r"^\s*(?:/usr/sbin/)?ufw\s", match[2], re.M)
        if phase == "prerm":
            assert "ufw-snapshot/state.json" in match[2]
            assert '"-I", path, "removal"' in match[2]
    assert "restore_legacy_install_dns" not in source
    assert "restore_netmon_install_dns" not in source
    assert "install-dns-nm.state" not in source


def test_deb_test_version_rejects_non_test_versions_without_building():
    result = subprocess.run(
        [
            "bash",
            str(PROJECT_ROOT / "scripts/build_netmon_deb.sh"),
            "--test-version",
            "1.1.21",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Test version must be" in result.stderr


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
        assert "NETMON_ALLOW_UNSIGNED_BUILD" not in source
        assert "require_release_signing" in source
        assert "begin_release_build" in source
        assert "finish_release_build" in source
        assert 'python3 "$ROOT_DIR/scripts/check_release_consistency.py"' in source
        assert '"$MINISIGN_VERIFY_SCRIPT"' in source
        assert "maybe_sign_release" not in source


def test_current_package_metadata_is_consistent():
    result = subprocess.run(
        [sys.executable, "scripts/check_release_consistency.py", "--package-only"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_public_release_gate_remains_separate_from_local_test_package():
    version = subprocess.check_output(
        [sys.executable, "scripts/read_netmon_version.py"], cwd=PROJECT_ROOT, text=True
    ).strip()
    published = json.loads((PROJECT_ROOT / "site/latest-version.json").read_text())
    result = subprocess.run(
        [sys.executable, "scripts/check_release_consistency.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if published["version"] == version:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1
        assert "site/latest-version.json: erwartet Version" in result.stdout


def test_package_only_check_still_rejects_mismatched_package_version(tmp_path):
    files = (
        "scripts/check_release_consistency.py",
        "scripts/read_netmon_version.py",
        "netmon/config/constants.py",
        "docs/security/netmonroots.minisign.pub",
        "README.md",
        "docs/README.md",
        "docs/CONFIGURATION.md",
        "docs/DEB_PACKAGING_PLAN.md",
        "docs/CHANGELOG.md",
        "packaging/changelog",
        "packaging/netmon.1",
        "packaging/netmon-uninstall.1",
    )
    for name in files:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / name, target)
    changelog = tmp_path / "packaging/changelog"
    changelog.write_text("netmon (0.0.0) unstable; urgency=low\n")
    result = subprocess.run(
        [sys.executable, "scripts/check_release_consistency.py", "--package-only"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "packaging/changelog: fehlt" in result.stdout


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
    verifier = (PROJECT_ROOT / "scripts" / "verify_netmon_signature.sh").read_text(
        encoding="utf-8"
    )
    assert key_lines[1] in verifier


def test_production_lifecycle_always_verifies_before_promotion():
    source = (PROJECT_ROOT / "scripts/netmon_release_common.sh").read_text(
        encoding="utf-8"
    )
    assert "NETMON_ALLOW_UNSIGNED_BUILD" not in source
    assert "Release-Abbruch: minisign ist nicht installiert." in source
    assert 'cmp -s "$RELEASE_MINISIGN_PUBKEY" "$PINNED_MINISIGN_PUBKEY"' in source
    assert 'bash "$ROOT_DIR/scripts/verify_netmon_signature.sh"' in source
    assert source.index(
        'python3 "$ROOT_DIR/scripts/verify_netmon_release_bundle.py"'
    ) < source.index('    "$BUILD_DIR" "$OUTPUT_DIR"')
