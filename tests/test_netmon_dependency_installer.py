import io
import inspect
import tarfile

import pytest

from netmon.app import (
    App,
    CODE_THE_CLASSICS_ZIP_DEV,
    CODE_THE_CLASSICS_ZIP_SYSTEM,
    DEPENDENCIES,
    SETUP_REMOVABLES,
    _download_url_to_file_limited,
    _extract_regular_tar_archive,
    find_code_the_classics_zip,
)
from netmon.ui.tabs.log_tab import build_log_tab


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _write_test_tar(path, members):
    with tarfile.open(path, "w") as archive:
        for member, payload in members:
            archive.addfile(
                member, io.BytesIO(payload) if payload is not None else None
            )


def test_extract_regular_tar_archive_accepts_files_and_directories(tmp_path):
    archive_path = tmp_path / "firefox.tar"
    directory = tarfile.TarInfo("firefox")
    directory.type = tarfile.DIRTYPE
    directory.mode = 0o755
    binary = tarfile.TarInfo("firefox/firefox")
    binary.size = 6
    binary.mode = 0o755
    _write_test_tar(archive_path, [(directory, None), (binary, b"binary")])

    target = tmp_path / "extract"
    with tarfile.open(archive_path, "r") as archive:
        _extract_regular_tar_archive(archive, target)

    assert (target / "firefox" / "firefox").read_bytes() == b"binary"
    assert (target / "firefox" / "firefox").stat().st_mode & 0o777 == 0o755


@pytest.mark.parametrize("member_type", [tarfile.SYMTYPE, tarfile.LNKTYPE])
def test_extract_regular_tar_archive_rejects_links(tmp_path, member_type):
    archive_path = tmp_path / "firefox.tar"
    link = tarfile.TarInfo("firefox/firefox")
    link.type = member_type
    link.linkname = "/bin/sh"
    _write_test_tar(archive_path, [(link, None)])

    with tarfile.open(archive_path, "r") as archive:
        with pytest.raises(ValueError, match="Links oder Sonderdateien"):
            _extract_regular_tar_archive(archive, tmp_path / "extract")


def test_extract_regular_tar_archive_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "firefox.tar"
    escaped = tarfile.TarInfo("../firefox")
    escaped.size = 4
    _write_test_tar(archive_path, [(escaped, b"nope")])

    with tarfile.open(archive_path, "r") as archive:
        with pytest.raises(ValueError, match="Unsicherer TAR-Pfad"):
            _extract_regular_tar_archive(archive, tmp_path / "extract")


def test_extract_regular_tar_archive_limits_total_size(tmp_path):
    archive_path = tmp_path / "firefox.tar"
    binary = tarfile.TarInfo("firefox/firefox")
    binary.size = 6
    _write_test_tar(archive_path, [(binary, b"binary")])

    with tarfile.open(archive_path, "r") as archive:
        with pytest.raises(ValueError, match="zu gross"):
            _extract_regular_tar_archive(
                archive,
                tmp_path / "extract",
                max_total_size=5,
            )


def test_download_url_to_file_limited_rejects_oversized_stream(tmp_path, monkeypatch):
    from test_firefox_runtime_security import Response, wire

    wire(monkeypatch, [Response(b"abcdef")])

    with pytest.raises(ValueError, match="zu gross"):
        _download_url_to_file_limited(
            "https://download.mozilla.org/firefox.tar.xz",
            tmp_path / "firefox.tar.xz",
            5,
        )


def test_dependency_registry_contains_selected_tools():
    assert DEPENDENCIES["nmap"]["apt_packages"] == ["nmap"]
    assert DEPENDENCIES["systemd_resolved"]["apt_packages"] == ["systemd-resolved"]
    assert DEPENDENCIES["iproute2_tools"]["apt_packages"] == ["iproute2"]
    assert DEPENDENCIES["iftop"]["apt_packages"] == ["iftop"]
    assert DEPENDENCIES["htop"]["apt_packages"] == ["htop"]
    assert DEPENDENCIES["mpv"]["checks"] == ["mpv"]
    assert DEPENDENCIES["secure_browser_firefox_source"]["type"] == "file_feature"
    assert (
        DEPENDENCIES["secure_browser_firefox_source"]["install_method"]
        == "url_tar_import"
    )
    assert (
        "download.mozilla.org"
        in DEPENDENCIES["secure_browser_firefox_source"]["install_url"]
    )
    assert DEPENDENCIES["projectm_visualizer"]["apt_packages"] == [
        "projectm",
        "projectm-pulseaudio",
    ]
    assert DEPENDENCIES["projectm_visualizer"]["type"] == "optional_backend"
    assert DEPENDENCIES["timeshift"]["apt_packages"] == ["timeshift"]
    assert DEPENDENCIES["timeshift"]["type"] == "optional_backend"
    assert DEPENDENCIES["mintbackup"]["apt_packages"] == ["mintbackup"]
    assert DEPENDENCIES["mintbackup"]["type"] == "optional_backend"
    assert DEPENDENCIES["deja_dup"]["apt_packages"] == ["deja-dup"]
    assert DEPENDENCIES["deja_dup"]["type"] == "optional_backend"
    assert DEPENDENCIES["projectm_presets_cream_crop"]["type"] == "file_feature"
    assert (
        DEPENDENCIES["projectm_presets_cream_crop"]["install_method"]
        == "url_zip_import"
    )
    assert (
        "presets-cream-of-the-crop"
        in DEPENDENCIES["projectm_presets_cream_crop"]["install_url"]
    )
    assert DEPENDENCIES["clamav"]["apt_packages"] == ["clamav", "clamav-freshclam"]
    assert DEPENDENCIES["pgzero_module"]["apt_packages"] == [
        "python3",
        "python3-pygame",
        "python3-pgzero",
    ]
    assert DEPENDENCIES["pgzero_module"]["pip_packages"] == []
    assert DEPENDENCIES["wireguard_tools"]["apt_packages"] == ["wireguard-tools"]
    assert DEPENDENCIES["code_the_classics_files"]["type"] == "file_feature"
    assert DEPENDENCIES["code_the_classics_files"]["install_method"] == "zip_import"
    assert SETUP_REMOVABLES["radio_mpv"]["packages"] == ["mpv"]
    assert SETUP_REMOVABLES["fun_pygame"]["packages"] == ["python3-pygame"]
    assert SETUP_REMOVABLES["fun_code_classics"]["kind"] == "data"


def test_find_code_the_classics_zip_prefers_existing_repo_asset():
    import netmon.app as app_module

    expected = CODE_THE_CLASSICS_ZIP_DEV
    original_isfile = app_module.os.path.isfile

    def fake_isfile(path):
        if path == expected:
            return True
        return False

    app_module.os.path.isfile = fake_isfile
    try:
        path = find_code_the_classics_zip()
    finally:
        app_module.os.path.isfile = original_isfile

    assert path
    assert path.endswith("Code-the-Classics.zip")
    assert path in {
        CODE_THE_CLASSICS_ZIP_DEV,
        CODE_THE_CLASSICS_ZIP_SYSTEM,
        "netmon/features/Code-the-Classics.zip",
    } or path.endswith("/netmon/features/Code-the-Classics.zip")


def test_collect_missing_installable_dependencies_uses_registry():
    app = App.__new__(App)
    checks = {
        "nmap": False,
        "resolvectl": False,
        "ss": False,
        "iftop": False,
        "htop": False,
        "mpv": True,
        "secure_browser_firefox_source": False,
        "projectm_visualizer": False,
        "projectm_visualizer_installable": True,
        "projectm_preset_pack_available": True,
        "projectm_presets_cream_crop": False,
        "clamav": False,
        "freshclam": True,
        "timeshift": False,
        "timeshift_installable": True,
        "mintbackup": False,
        "mintbackup_installable": False,
        "deja_dup": False,
        "deja_dup_installable": True,
    }

    missing = app._collect_missing_installable_dependencies(checks)
    missing_with_optional = app._collect_missing_installable_dependencies(
        checks,
        include_optional=True,
    )

    assert "nmap" in missing
    assert "systemd_resolved" in missing
    assert "iproute2_tools" in missing
    assert "iftop" in missing
    assert "htop" in missing
    assert "clamav" in missing
    assert "secure_browser_firefox_source" in missing
    assert "projectm_visualizer" not in missing
    assert "projectm_visualizer" in missing_with_optional
    assert "projectm_presets_cream_crop" in missing_with_optional
    assert "timeshift" in missing_with_optional
    assert "deja_dup" in missing_with_optional
    assert "mintbackup" not in missing_with_optional
    assert "mpv" not in missing


def test_build_dependency_terminal_command_deduplicates_packages():
    app = App.__new__(App)

    cmd = app._build_dependency_terminal_command(["tshark", "pillow", "pgzero_module"])

    assert (
        cmd
        == "sudo apt install -y wireshark tshark python3-pil python3-pil.imagetk python3 python3-pygame python3-pgzero"
    )


def test_build_packet_capture_permission_repair_script_contains_required_steps():
    app = App.__new__(App)

    script = app._build_packet_capture_permission_repair_script("happy")

    assert "wireshark-common wireshark-common/install-setuid boolean true" in script
    assert "groupadd --system wireshark" in script
    assert 'chown root:wireshark "$DUMPCAP_PATH"' in script
    assert 'chmod 0750 "$DUMPCAP_PATH"' in script
    assert 'usermod -a -G wireshark "$TARGET_USER"' in script
    assert "setcap cap_net_raw,cap_net_admin=ep" in script
    assert "TARGET_USER=happy" in script


def test_build_packet_capture_permission_repair_terminal_command_wraps_script():
    app = App.__new__(App)

    cmd = app._build_packet_capture_permission_repair_terminal_command("happy")

    assert cmd.startswith("sudo /bin/bash -lc ")
    assert "dpkg-reconfigure -f noninteractive wireshark-common" in cmd


def test_build_dependency_terminal_command_returns_empty_for_removed_internal_visualizers():
    app = App.__new__(App)

    cmd = app._build_dependency_terminal_command(["pyside6_visualizer"])

    assert cmd == ""


def test_build_dependency_terminal_command_prefers_projectm_install_strategy(
    monkeypatch,
):
    app = App.__new__(App)

    monkeypatch.setattr(
        "netmon.app.netmon_projectm_sidecar.probe_projectm_package_candidates",
        lambda app=None, refresh=False: {
            "install_strategy": "flatpak",
            "install_command": "flatpak install -y flathub net.sourceforge.projectM",
        },
    )
    monkeypatch.setattr(
        "netmon.app.netmon_projectm_sidecar.build_projectm_install_command",
        lambda probe=None: str((probe or {}).get("install_command", "")),
    )

    cmd = app._build_dependency_terminal_command(["projectm_visualizer", "mpv"])

    assert "flatpak install -y flathub net.sourceforge.projectM" in cmd
    assert "sudo apt install -y mpv" in cmd


def test_dependency_installer_sort_key_prioritizes_projectm_and_mpv():
    app = App.__new__(App)

    ordered = sorted(
        ["nmap", "pyside6_visualizer", "projectm_visualizer", "mpv"],
        key=app._dependency_installer_sort_key,
    )

    assert ordered[:2] == ["projectm_visualizer", "mpv"]


def test_build_setup_removal_terminal_command_deduplicates_packages():
    app = App.__new__(App)

    cmd = app._build_setup_removal_terminal_command(
        ["radio_mpv", "fun_pgzero", "fun_pygame"]
    )

    assert cmd == "sudo apt remove -y mpv python3-pgzero python3-pygame"


def test_collect_setup_removable_components_uses_wireshark_package_marker():
    app = type(
        "DummyApp",
        (),
        {
            "_count_code_the_classics_files": lambda self: 0,
            "_is_safe_netmon_managed_path": lambda self, path: False,
        },
    )()

    removable = App._collect_setup_removable_components(
        app,
        {
            "wireshark": False,
            "wireshark_installed": True,
            "tshark": False,
            "dumpcap": False,
        },
    )

    assert "wireshark_suite" in removable


def test_is_debian_package_installed_reads_dpkg_status(monkeypatch):
    import netmon.app as app_module

    calls = []

    monkeypatch.setattr(app_module, "has_cmd", lambda name: name == "dpkg-query")

    def fake_run(cmd, stdout=None, stderr=None, text=None, timeout=None, check=None):
        calls.append(cmd)
        return type(
            "Completed",
            (),
            {"returncode": 0, "stdout": "install ok installed"},
        )()

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)

    assert app_module.is_debian_package_installed("wireshark") is True
    assert calls == [["dpkg-query", "-W", "-f=${Status}", "wireshark"]]


def test_dependency_installer_integration_hooks_are_present():
    init_source = inspect.getsource(App.__init__)
    preflight_source = inspect.getsource(App.preflight_dependencies)
    install_source = inspect.getsource(App.install_selected_dependencies)
    remove_source = inspect.getsource(App.remove_selected_setup_components)
    remove_helper_source = inspect.getsource(App._remove_selected_netmon_paths)
    open_source = inspect.getsource(App.open_dependency_installer)
    helper_source = inspect.getsource(App._log_dependency_installer_summary)
    hint_source = inspect.getsource(App.show_fun_install_hint)
    log_source = inspect.getsource(build_log_tab)

    assert "self.dep_installer_missing_keys = []" in init_source
    assert "self.missing_dependencies = []" in init_source
    assert "self.dep_installer_removable_keys = []" in init_source
    assert "self.dep_installer_remove_vars = {}" in init_source
    assert "self.dep_installer_button_var = tk.StringVar(" in init_source
    assert "self._collect_missing_installable_dependencies(" in preflight_source
    assert (
        "self.missing_dependencies = list(self.dep_installer_missing_keys)"
        in preflight_source
    )
    assert (
        "self.dep_installer_removable_keys = self._collect_setup_removable_components("
        in preflight_source
    )
    assert "self._log_dependency_installer_summary()" in preflight_source
    assert "self._update_dependency_installer_button()" in preflight_source
    assert "self._build_external_terminal_command(script)" in install_source
    assert "_install_selected_file_features(" in install_source
    assert "self._get_code_the_classics_zip_path()" in inspect.getsource(
        App._install_selected_file_features
    )
    assert '"projectm_presets_cream_crop"' in inspect.getsource(
        App._install_selected_file_features
    )
    assert "self.preflight_dependencies(manual_trigger=False)" in open_source
    assert (
        'body.add(install_tab, text=self.tr("setup_assistant_tab_install", "Install"))'
        in open_source
    )
    assert (
        'body.add(remove_tab, text=self.tr("setup_assistant_tab_remove", "Remove"))'
        in open_source
    )
    assert "install_canvas = tk.Canvas(" in open_source
    assert "remove_canvas = tk.Canvas(" in open_source
    assert (
        "self._apply_dependency_installer_theme(self._app_theme or LIGHT_THEME)"
        in open_source
    )
    assert 'orient="vertical"' in open_source
    assert "self.dep_installer_optional_frame = optional_hint" in open_source
    assert "self.remove_selected_setup_components" in open_source
    assert (
        "def _populate_dependency_installer_optional_hint(self):"
        in inspect.getsource(App._populate_dependency_installer_optional_hint)
    )
    assert '"setup_assistant_optional_projectm"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert "Flatpak-Installation ist optional möglich." in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_btn_select_only_projectm"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_btn_select_only_projectm_presets"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_optional_timeshift"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_btn_select_only_timeshift"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_optional_desktop_backup"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert '"setup_assistant_btn_select_only_desktop_backup"' in inspect.getsource(
        App._populate_dependency_installer_optional_hint
    )
    assert (
        '"code_the_classics_files": self._count_code_the_classics_files() > 0'
        in preflight_source
    )
    assert '"projectm_presets_cream_crop"' in preflight_source
    assert '"projectm_preset_pack_available"' in preflight_source
    assert "sudo apt remove -y" in inspect.getsource(
        App._build_setup_removal_terminal_command
    )
    assert (
        '"dep_installer_status_remove_cancelled"' in remove_source
        or "Warning:" in remove_source
    )
    assert "self._is_safe_netmon_managed_path(path)" in remove_helper_source
    assert "Code the Classics games: MISSING" in inspect.getsource(
        App._log_preflight_manual_summary
    )
    assert (
        "projectm_state = netmon_projectm_sidecar.get_projectm_sidecar_status("
        in preflight_source
    )
    assert (
        "projectm_probe = netmon_projectm_sidecar.probe_projectm_package_candidates("
        in preflight_source
    )
    assert '"projectm_visualizer_installable"' in preflight_source
    assert '"timeshift_installable"' in preflight_source
    assert '"mintbackup": has_cmd("mintbackup")' in preflight_source
    assert '"deja_dup": has_cmd("deja-dup")' in preflight_source
    assert '"mintbackup_installable"' in preflight_source
    assert '"deja_dup_installable"' in preflight_source
    assert (
        'checks["flatpak"] = bool(projectm_probe.get("flatpak_available", False))'
        in preflight_source
    )
    assert "include_optional=True" in preflight_source
    assert 'self._venv_python_modules_available("pygame")' in preflight_source
    assert 'self._venv_python_modules_available("pgzero")' in preflight_source
    assert (
        'self._venv_python_modules_available("PIL", "PIL.ImageTk")' in preflight_source
    )
    assert 'self._venv_python_modules_available("PyPDF2")' in preflight_source
    assert 'self._venv_python_modules_available("docx")' in preflight_source
    assert (
        "Preflight: {count} components missing. Please open the setup assistant."
        in helper_source
    )
    assert "python3-pgzero" in hint_source
    assert "pip install" not in hint_source
    assert "python3 -m venv" in inspect.getsource(
        App._build_dependency_terminal_command
    )
    assert 'if dep_key == "projectm_visualizer":' in inspect.getsource(
        App._build_dependency_terminal_command
    )
    assert "pip install -r" in inspect.getsource(App._build_dependency_terminal_command)
    assert "python3-venv python3-full" in inspect.getsource(
        App._build_dependency_terminal_command
    )
    assert "textvariable=app.dep_installer_button_var" in log_source


def test_preflight_logged_tools_are_covered_by_dependency_registry():
    covered_checks = set()
    for info in DEPENDENCIES.values():
        covered_checks.update(info.get("checks", []) or [])

    logged_preflight_keys = {
        "traceroute",
        "mtr",
        "nmap",
        "nmcli",
        "resolvectl",
        "wg",
        "wg-quick",
        "ufw",
        "ss",
        "iftop",
        "htop",
        "tshark",
        "dumpcap",
        "wireshark",
        "capinfos",
        "lynis",
        "rkhunter",
        "timeshift",
        "mintbackup",
        "deja_dup",
        "whois",
        "mpv",
        "secure_browser_firefox_source",
        "projectm_visualizer",
        "projectm_presets_cream_crop",
        "python3",
        "speedtest",
        "clamav",
        "freshclam",
        "pillow",
        "pygame_module",
        "pgzero_module",
    }

    assert logged_preflight_keys.issubset(covered_checks)


def test_venv_python_modules_available_uses_project_venv_python(tmp_path, monkeypatch):
    app = App.__new__(App)
    calls = []

    monkeypatch.setattr(
        App, "_project_venv_python_path", lambda self: "/tmp/netmon-venv/bin/python"
    )
    monkeypatch.setattr(
        "netmon.app.os.path.isfile", lambda path: path == "/tmp/netmon-venv/bin/python"
    )
    monkeypatch.setattr(
        "netmon.app.os.access", lambda path, mode: path == "/tmp/netmon-venv/bin/python"
    )
    monkeypatch.setattr("netmon.app.importlib.util.find_spec", lambda name: None)

    def fake_run(cmd, stdout=None, stderr=None, text=None, timeout=None, check=None):
        calls.append(cmd)
        return type("Completed", (), {"returncode": 0, "stdout": "1"})()

    monkeypatch.setattr("netmon.app.subprocess.run", fake_run)

    assert app._venv_python_modules_available("PySide6") is True
    assert calls
    assert calls[0][0] == "/tmp/netmon-venv/bin/python"
