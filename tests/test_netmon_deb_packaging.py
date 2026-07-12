from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_deb_builder_uses_debian_compliant_install_locations():
    source = (PROJECT_ROOT / "scripts" / "build_netmon_deb.sh").read_text(
        encoding="utf-8"
    )

    assert 'APP_ROOT="$PKG_DIR/usr/lib/netmon"' in source
    assert 'ASSETS_ROOT="$PKG_DIR/usr/share/netmon/assets"' in source
    assert 'DOCS_ROOT="$PKG_DIR/usr/share/doc/netmon"' in source
    assert 'NETMON_HOME="/usr/lib/netmon"' in source
    assert 'ASSET_DIR="/usr/share/netmon/assets/log-pics"' in source
    assert 'APP_ROOT="$PKG_DIR/opt/netmon"' not in source


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
