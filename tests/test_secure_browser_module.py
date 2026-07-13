from pathlib import Path
from types import SimpleNamespace

from netmon.modules.secure_browser.manager import SecureBrowserManager
from netmon.modules.secure_browser.models import BrowserContainer
from netmon.modules.secure_browser.service import SecureBrowserService
from netmon.modules.secure_browser.ui import (
    _prompt_url_with_context_menu,
    create_secure_browser_tab,
)


class DummyWidget:
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.children = []
        if parent is not None and hasattr(parent, "children"):
            parent.children.append(self)

    def grid(self, *args, **kwargs):
        self.grid_args = args
        self.grid_kwargs = kwargs

    def columnconfigure(self, *args, **kwargs):
        self.columnconfigure_args = (args, kwargs)

    def rowconfigure(self, *args, **kwargs):
        self.rowconfigure_args = (args, kwargs)

    def insert(self, index, text):
        self.text_content = getattr(self, "text_content", "") + text

    def delete(self, start, end):
        self.text_content = ""

    def configure(self, **kwargs):
        self.configure_kwargs = getattr(self, "configure_kwargs", {})
        self.configure_kwargs.update(kwargs)

    def bind(self, event, callback):
        self.bound_events = getattr(self, "bound_events", {})
        self.bound_events[event] = callback

    def selection_clear(self, start, end=None):
        self.selected_indices = []

    def selection_set(self, index):
        self.selected_indices = [index]

    def activate(self, index):
        self.active_index = index

    def curselection(self):
        return tuple(getattr(self, "selected_indices", []))

    def get(self, *args):
        if len(args) == 1:
            return self.items[args[0]]
        return getattr(self, "text_content", "")

    def clipboard_clear(self):
        self.clipboard_content = ""

    def clipboard_append(self, value):
        self.clipboard_content = value

    def clipboard_get(self):
        return getattr(self, "clipboard_content", "")

    def event_generate(self, sequence):
        self.generated_events = getattr(self, "generated_events", [])
        self.generated_events.append(sequence)

    def yview(self, *args):
        self.yview_args = args

    def set(self, *args):
        self.set_args = args


class DummyCombobox(DummyWidget):
    def __init__(self, parent=None, values=None, **kwargs):
        super().__init__(parent=parent, values=values or [], **kwargs)
        self.values = list(values or [])
        self.current_value = ""

    def set(self, value):
        self.current_value = value

    def get(self):
        return self.current_value

    def configure(self, **kwargs):
        super().configure(**kwargs)
        if "values" in kwargs:
            self.values = list(kwargs["values"])


class DummyEntry(DummyWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.value = ""

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyTkEntryNoSet(DummyWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.value = ""

    def insert(self, index, text):
        self.value = text

    def delete(self, start, end=None):
        self.value = ""

    def get(self):
        return self.value


class DummyListbox(DummyWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.items = []
        self.selected_indices = []

    def insert(self, index, value):
        self.items.append(value)

    def delete(self, start, end=None):
        self.items = []
        self.selected_indices = []


class DummyButton(DummyWidget):
    pass


class DummyNotebook(DummyWidget):
    def __init__(self):
        super().__init__(None)
        self.added = []

    def add(self, widget, **kwargs):
        self.added.append((widget, kwargs))


class DummyMessageBox:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def askyesno(self, title, message):
        self.calls.append((title, message))
        return self.result


class DummyMessageBoxSequence:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def askyesno(self, title, message):
        self.calls.append((title, message))
        if self.results:
            return self.results.pop(0)
        return True


def test_browser_container_dataclass_holds_expected_fields():
    container = BrowserContainer(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
        profile_path=Path("/tmp/firefox-GitHub/profile"),
        homepage_url="https://github.com",
        allowed_domains=["github.com"],
        icon_path=Path("/tmp/firefox-GitHub/icons/favicon.png"),
        menu_entry_path=Path("/tmp/menu.desktop"),
        status="prepared",
    )

    assert container.name == "firefox-GitHub"
    assert container.allowed_domains == ["github.com"]
    assert container.status == "prepared"


def test_secure_browser_service_can_be_instantiated():
    service = SecureBrowserService()

    assert service.tool_script.name == "browser_container_builder.py"
    assert service.tool_config.name == "containers.example.json"
    assert service.tool_script.is_absolute()
    assert service.tool_script == (
        SecureBrowserService.REPO_ROOT
        / "tools/secure_browser_manager/browser_container_builder.py"
    )


def test_secure_browser_default_base_dir_uses_xdg_documents(monkeypatch, tmp_path):
    documents_dir = tmp_path / "My Documents"
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(documents_dir))
    service = SecureBrowserService()

    base_dir = service.get_default_base_dir()

    assert base_dir == documents_dir / "NetMon" / "Secure Browser"
    assert base_dir.is_dir()


def test_secure_browser_service_runs_preflight_checks(monkeypatch, tmp_path):
    tool_root = tmp_path / "secure_browser_manager"
    tool_root.mkdir()
    (tool_root / "browser_container_builder.py").write_text(
        "DEFAULT_BASE_DIR = '/tmp'\n",
        encoding="utf-8",
    )
    (tool_root / "containers.example.json").write_text("{}", encoding="utf-8")

    source_dir = tmp_path / "firefox-source"
    source_dir.mkdir()
    (source_dir / "firefox").write_text("", encoding="utf-8")

    service = SecureBrowserService(tool_root=tool_root)
    monkeypatch.setattr(service, "_load_tool_module", lambda: SimpleNamespace())
    monkeypatch.setattr(service, "get_default_source_firefox_dir", lambda: source_dir)
    monkeypatch.setattr(service, "get_default_base_dir", lambda: tmp_path / "Programme")
    monkeypatch.setattr(
        "netmon.modules.secure_browser.service.shutil.which",
        lambda name: "/usr/bin/firefox" if name == "firefox" else None,
    )

    lines = service.run_preflight_checks()

    assert any("Builder-Skript: OK" in line for line in lines)
    assert any("Builder-Konfiguration: OK" in line for line in lines)
    assert any("Builder-Modul: OK" in line for line in lines)
    assert any("Firefox-Laufzeit: OK" in line for line in lines)
    assert any("Firefox-Quelle" in line and "OK" in line for line in lines)
    assert any("Firefox-Binary" in line and "OK" in line for line in lines)
    assert any("Menüpfad:" in line for line in lines)
    assert any("Zielbasis:" in line for line in lines)


def test_secure_browser_service_reports_missing_firefox_runtime_as_hint_when_local_source_exists(
    monkeypatch, tmp_path
):
    tool_root = tmp_path / "secure_browser_manager"
    tool_root.mkdir()
    (tool_root / "browser_container_builder.py").write_text(
        "DEFAULT_BASE_DIR = '/tmp'\n",
        encoding="utf-8",
    )
    (tool_root / "containers.example.json").write_text("{}", encoding="utf-8")

    source_dir = tmp_path / "firefox-source"
    source_dir.mkdir()
    (source_dir / "firefox").write_text("", encoding="utf-8")

    service = SecureBrowserService(tool_root=tool_root)
    monkeypatch.setattr(service, "_load_tool_module", lambda: SimpleNamespace())
    monkeypatch.setattr(service, "get_default_source_firefox_dir", lambda: source_dir)
    monkeypatch.setattr(service, "get_default_base_dir", lambda: tmp_path / "Programme")
    monkeypatch.setattr(
        "netmon.modules.secure_browser.service.shutil.which",
        lambda name: None,
    )

    lines = service.run_preflight_checks()

    assert any("Firefox-Laufzeit: HINWEIS" in line for line in lines)


def test_secure_browser_service_reports_missing_firefox_runtime_as_error_without_source(
    monkeypatch, tmp_path
):
    tool_root = tmp_path / "secure_browser_manager"
    tool_root.mkdir()
    (tool_root / "browser_container_builder.py").write_text(
        "DEFAULT_BASE_DIR = '/tmp'\n",
        encoding="utf-8",
    )
    (tool_root / "containers.example.json").write_text("{}", encoding="utf-8")

    service = SecureBrowserService(tool_root=tool_root)
    monkeypatch.setattr(service, "_load_tool_module", lambda: SimpleNamespace())
    monkeypatch.setattr(service, "get_default_source_firefox_dir", lambda: None)
    monkeypatch.setattr(service, "get_default_base_dir", lambda: tmp_path / "Programme")
    monkeypatch.setattr(
        "netmon.modules.secure_browser.service.shutil.which",
        lambda name: None,
    )

    lines = service.run_preflight_checks()

    assert any("Firefox-Laufzeit: FEHLT" in line for line in lines)


def test_secure_browser_service_falls_back_to_firefox_base_when_configured_source_is_missing(
    tmp_path,
):
    tool_root = tmp_path / "secure_browser_manager"
    tool_root.mkdir()
    (tool_root / "browser_container_builder.py").write_text(
        "DEFAULT_BASE_DIR = '/tmp'\n",
        encoding="utf-8",
    )
    (tool_root / "containers.example.json").write_text(
        '{"default_source_firefox_dir": "/missing/firefox"}',
        encoding="utf-8",
    )
    firefox_base = tmp_path / "Programme" / "firefox-base" / "firefox"
    firefox_base.mkdir(parents=True)
    (firefox_base / "firefox").write_text("", encoding="utf-8")

    service = SecureBrowserService(tool_root=tool_root)
    service.get_default_base_dir = lambda: tmp_path / "Programme"

    resolved = service.get_default_source_firefox_dir()

    assert resolved == firefox_base


def test_secure_browser_service_reads_and_saves_policy_json(tmp_path):
    container_dir = tmp_path / "firefox-OpenAI"
    runtime_dir = container_dir / "firefox" / "distribution"
    runtime_dir.mkdir(parents=True)
    source_path = container_dir / "policies.json"
    runtime_path = runtime_dir / "policies.json"
    source_path.write_text(
        '{"policies":{"Homepage":{"URL":"https://chatgpt.com"}}}\n', encoding="utf-8"
    )
    runtime_path.write_text(
        '{"policies":{"Homepage":{"URL":"https://chatgpt.com"}}}\n', encoding="utf-8"
    )

    container = BrowserContainer(
        name="firefox-OpenAI",
        path=container_dir,
        binary_path=container_dir / "firefox" / "firefox",
        profile_path=container_dir / "profile",
        homepage_url="https://chatgpt.com",
        allowed_domains=["chatgpt.com"],
    )
    service = SecureBrowserService(tool_root=tmp_path)

    rendered = service.read_policy_json(container)

    assert '"Homepage"' in rendered

    result = service.save_policy_json(
        container,
        '{"policies":{"WebsiteFilter":{"Block":["<all_urls>"],"Exceptions":["*://chatgpt.com/*"]}}}',
    )

    assert source_path.read_text(encoding="utf-8").startswith("{\n")
    assert runtime_path.read_text(encoding="utf-8") == source_path.read_text(
        encoding="utf-8"
    )
    assert Path(result["backup_dir"]).is_dir()
    assert (Path(result["backup_dir"]) / "policies.json").is_file()


def test_secure_browser_service_run_builder_command_adds_runtime_inventory(
    monkeypatch, tmp_path
):
    service = SecureBrowserService(tool_root=tmp_path)

    captured = {}

    def fake_run(command, check, capture_output, text, cwd):
        captured["command"] = list(command)
        captured["cwd"] = cwd
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(
        "netmon.modules.secure_browser.service.subprocess.run", fake_run
    )

    result = service._run_builder_command(
        ["python3", str(tmp_path / "browser_container_builder.py"), "--apply"]
    )

    assert "--inventory" in captured["command"]
    inventory_index = captured["command"].index("--inventory")
    assert captured["command"][inventory_index + 1].endswith(
        "netmon-secure-browser-container_inventory.md"
    )
    assert "--base-dir" in captured["command"]
    assert result["ok"] is True


def test_secure_browser_service_rejects_invalid_policy_json(tmp_path):
    container_dir = tmp_path / "firefox-OpenAI"
    container_dir.mkdir()
    container = BrowserContainer(
        name="firefox-OpenAI",
        path=container_dir,
        binary_path=container_dir / "firefox" / "firefox",
        profile_path=container_dir / "profile",
        homepage_url="https://chatgpt.com",
        allowed_domains=["chatgpt.com"],
    )
    service = SecureBrowserService(tool_root=tmp_path)

    try:
        service.save_policy_json(container, '{"broken": ')
    except ValueError as exc:
        assert "Ungültiges JSON" in str(exc)
    else:
        raise AssertionError("ValueError expected for invalid policy JSON")


def test_secure_browser_manager_can_be_instantiated():
    manager = SecureBrowserManager()

    assert isinstance(manager.service, SecureBrowserService)


def test_secure_browser_manager_renders_preflight_text():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_preflight_checks=lambda: [
                "- Builder-Skript: OK (/tmp/browser_container_builder.py)",
                "- Firefox-Quelle: OK (/opt/netmon-browser/firefox)",
            ]
        )
    )

    rendered = manager.render_preflight_text()

    assert "Secure-Browser-Preflight" in rendered
    assert "- Modus: read-only" in rendered
    assert "Setup-Assistenten" in rendered
    assert "- Builder-Skript: OK" in rendered
    assert "- Firefox-Quelle: OK" in rendered


def test_secure_browser_manager_uses_translation_callback_for_runtime_text():
    manager = SecureBrowserManager(
        service=SimpleNamespace(run_preflight_checks=lambda: []),
        tr=lambda key, default=None: {
            "secure_browser_preflight_title": "PreflightX",
            "secure_browser_preflight_mode_label": "ModeX",
            "secure_browser_preflight_mode_read_only": "ReadOnlyX",
        }.get(key, default or key),
    )

    rendered = manager.render_preflight_text()

    assert "PreflightX" in rendered
    assert "- ModeX: ReadOnlyX" in rendered


def test_secure_browser_manager_renders_policy_editor():
    container = BrowserContainer(
        name="firefox-OpenAI",
        path=Path("/tmp/firefox-OpenAI"),
        binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
        profile_path=Path("/tmp/firefox-OpenAI/profile"),
        homepage_url="https://chatgpt.com",
        allowed_domains=["chatgpt.com"],
    )
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            read_policy_json=lambda current: '{\n  "policies": {}\n}\n',
        )
    )
    manager.last_scan = [container]

    rendered = manager.render_policy_editor("firefox-OpenAI")

    assert "Whitelist-Editor" in rendered
    assert '"policies"' in rendered


def test_secure_browser_manager_saves_policy_editor_content():
    container = BrowserContainer(
        name="firefox-OpenAI",
        path=Path("/tmp/firefox-OpenAI"),
        binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
        profile_path=Path("/tmp/firefox-OpenAI/profile"),
        homepage_url="https://chatgpt.com",
        allowed_domains=["chatgpt.com"],
    )
    captured = {}
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            save_policy_json=lambda current, content: (
                captured.update(name=current.name, content=content)
                or {
                    "source_path": "/tmp/firefox-OpenAI/policies.json",
                    "runtime_path": "/tmp/firefox-OpenAI/firefox/distribution/policies.json",
                    "backup_dir": "/tmp/firefox-OpenAI/backups/policy-editor-backups/stamp",
                    "backup_count": "2",
                }
            ),
        )
    )
    manager.last_scan = [container]

    rendered = manager.execute_policy_save_apply(
        "firefox-OpenAI",
        '{"policies":{"WebsiteFilter":{}}}',
    )

    assert captured["name"] == "firefox-OpenAI"
    assert '"WebsiteFilter"' in captured["content"]
    assert "Whitelist gespeichert" in rendered


def test_secure_browser_manager_renders_create_browser_draft():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            build_create_preview=lambda name, homepage_url, allowed_domains, **kwargs: {
                "tool_script": "/tmp/tools/browser_container_builder.py",
                "tool_config": "<generierte-create-config>",
                "command": (
                    "python3 /tmp/tools/browser_container_builder.py "
                    "--config <generierte-create-config> "
                    "--only firefox-GitHub2"
                ),
                "payload": '{\n  "name": "firefox-GitHub2",\n  "new_tab_url": "about:blank"\n}',
                "source_firefox_dir": "/opt/netmon-browser/firefox",
            },
        )
    )

    draft = manager.render_create_browser_draft(
        "firefox-GitHub2",
        "https://github.com",
        "github.com, githubassets.com",
    )

    assert "Dry-Run-Entwurf" in draft
    assert "- Zielbasis: /tmp/Programme" in draft
    assert "- Zielordner: /tmp/Programme/firefox-GitHub2" in draft
    assert "- Containername: firefox-GitHub2" in draft
    assert "- Startseite: https://github.com" in draft
    assert "- Neue Tabs: about:blank" in draft
    assert "- Menüname: GitHub2" in draft
    assert "- Icon-Modus: favicon" in draft
    assert "- Erlaubte Domains: github.com, githubassets.com" in draft
    assert "- Validierung: ohne Befund" in draft
    assert "- Keine Warnungen erkannt" in draft
    assert "Builder-Vorschau" in draft
    assert "- Firefox-Quelle: /opt/netmon-browser/firefox" in draft
    assert (
        "- Geplanter Aufruf: python3 /tmp/tools/browser_container_builder.py --config <generierte-create-config> --only firefox-GitHub2"
        in draft
    )
    assert '"name": "firefox-GitHub2"' in draft
    assert '"new_tab_url": "about:blank"' in draft


def test_secure_browser_manager_lists_create_presets():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            list_create_presets=lambda: [
                {"name": "firefox-GitHub"},
                {"name": "firefox-OpenAI"},
            ]
        )
    )

    assert manager.get_create_preset_names() == [
        "firefox-GitHub",
        "firefox-OpenAI",
    ]
    assert manager.get_create_preset("firefox-GitHub") == {"name": "firefox-GitHub"}
    assert manager.derive_menu_name("firefox-SparkasseUlm") == "SparkasseUlm"


def test_secure_browser_manager_derives_create_defaults_from_website():
    manager = SecureBrowserManager(service=SimpleNamespace())

    derived = manager.derive_create_defaults("sparkasse-ulm.de")

    assert derived["homepage_url"] == "https://sparkasse-ulm.de"
    assert derived["container_name"] == "firefox-sparkasse-ulm-de"
    assert derived["allowed_domains"] == ["sparkasse-ulm.de"]
    assert derived["menu_name"] == "Sparkasse Ulm De"


def test_secure_browser_manager_derives_known_domain_bundle_for_netflix():
    manager = SecureBrowserManager(service=SimpleNamespace())

    derived = manager.derive_create_defaults("https://www.netflix.com")

    assert derived["homepage_url"] == "https://www.netflix.com"
    assert derived["container_name"] == "firefox-netflix"
    assert derived["allowed_domains"] == [
        "netflix.com",
        "nflxvideo.net",
        "nflximg.net",
    ]
    assert derived["menu_name"] == "Netflix"


def test_secure_browser_manager_derives_known_domain_bundle_for_openai():
    manager = SecureBrowserManager(service=SimpleNamespace())

    derived = manager.derive_create_defaults("https://chatgpt.com")

    assert derived["container_name"] == "firefox-openai"
    assert derived["allowed_domains"] == [
        "chatgpt.com",
        "openai.com",
        "platform.openai.com",
        "auth.openai.com",
        "oaistatic.com",
        "oaiusercontent.com",
    ]
    assert derived["menu_name"] == "OpenAI"


def test_secure_browser_manager_derives_defaults_for_explicit_port_url():
    manager = SecureBrowserManager(service=SimpleNamespace())

    derived = manager.derive_create_defaults("https://hs21.name.tools:2083")

    assert derived["homepage_url"] == "https://hs21.name.tools:2083"
    assert derived["container_name"] == "firefox-hs21-name-tools"
    assert derived["allowed_domains"] == [
        "hs21.name.tools:2083",
        "hs21.name.tools",
        "name.tools",
    ]


def test_secure_browser_manager_normalizes_url_like_allowed_domains():
    manager = SecureBrowserManager(service=SimpleNamespace())

    resolved = manager._resolve_create_inputs(
        "firefox-Proton",
        "https://proton.me",
        "https://proton.me/, https://account.proton.me/login",
        "",
        "",
        "favicon",
    )

    assert resolved["allowed_domains"] == [
        "proton.me",
        "account.proton.me",
    ]


def test_secure_browser_manager_rejects_invalid_container_name_early():
    manager = SecureBrowserManager(service=SimpleNamespace())

    try:
        manager._resolve_create_inputs(
            "firefox/Bad",
            "https://proton.me",
            "",
            "",
            "",
            "favicon",
        )
    except ValueError as exc:
        assert "Ungültiger Containername" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid container name")


def test_secure_browser_manager_append_policy_exception_json_adds_exception():
    manager = SecureBrowserManager(service=SimpleNamespace())

    rendered = manager.append_policy_exception_json(
        '{"policies":{"WebsiteFilter":{"Block":["<all_urls>"],"Exceptions":[]}}}',
        "https://www.example.com/mail",
    )

    assert '"Exceptions"' in rendered
    assert "https://www.example.com/mail*" in rendered
    assert '"<all_urls>"' in rendered
    assert '"*://*/*"' not in rendered


def test_secure_browser_manager_append_policy_exception_json_adds_default_block():
    manager = SecureBrowserManager(service=SimpleNamespace())

    rendered = manager.append_policy_exception_json(
        '{"policies":{"WebsiteFilter":{}}}',
        "example.com",
    )

    assert '"Block"' in rendered
    assert '"<all_urls>"' in rendered
    assert "*://example.com/*" in rendered


def test_secure_browser_manager_filters_by_status():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            derive_risk_hints=lambda container: (
                ["Externes Mozilla-Profil eingebunden", "Menüeintrag fehlt"]
                if container.name == "firefox-OpenAI"
                else ["launcher.desktop fehlt"]
            )
        )
    )
    manager.last_scan = [
        BrowserContainer(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
            profile_path=Path("/tmp/firefox-GitHub/profile"),
            homepage_url="https://github.com",
            allowed_domains=["github.com"],
            icon_path=Path("/tmp/firefox-GitHub/icons"),
            menu_entry_path=Path("/tmp/menu.desktop"),
            status="vollständig",
        ),
        BrowserContainer(
            name="firefox-OpenAI",
            path=Path("/tmp/firefox-OpenAI"),
            binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
            profile_path=Path("/tmp/firefox-OpenAI/profile"),
            homepage_url="https://chatgpt.com",
            allowed_domains=["chatgpt.com"],
            icon_path=Path("/tmp/firefox-OpenAI/icons"),
            menu_entry_path=None,
            status="Launcher fehlt",
        ),
    ]

    assert manager.get_status_filter_options() == [
        "Alle",
        "Launcher fehlt",
        "vollständig",
    ]
    assert manager.get_container_names("vollständig") == ["firefox-GitHub"]
    assert (
        manager.render_inventory_summary("vollständig")
        == "1 von 2 Secure-Browser-Containern mit Status vollständig erkannt."
    )
    assert manager.get_container_names(search_query="chatgpt") == ["firefox-OpenAI"]
    assert (
        manager.render_inventory_summary(search_query="github")
        == "1 von 2 Secure-Browser-Containern passend zu 'github' erkannt."
    )
    assert (
        manager.render_inventory_metrics()
        == "Kennzahlen: Gesamt: 2 | Launcher fehlt: 1 | vollständig: 1 | externe Profile: 1 | fehlende Launcher: 1 | fehlende Menüeinträge: 1"
    )
    assert manager.get_container_names(risk_filter="Nur Risiken") == [
        "firefox-GitHub",
        "firefox-OpenAI",
    ]
    assert manager.get_container_names(risk_filter="Nur externe Profile") == [
        "firefox-OpenAI"
    ]


def test_secure_browser_manager_renders_container_report():
    service = SimpleNamespace(
        derive_risk_hints=lambda container: [
            "Externes Mozilla-Profil eingebunden",
            "Menüeintrag fehlt",
        ],
        verify_container=lambda container: [
            "Firefox-Binary: OK",
            "Menüeintrag: OK",
        ],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": "/tmp/menu.desktop",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
            "menu_entries": [
                {
                    "Datei": "netmon-secure-browser-firefox-github.desktop",
                    "Pfad": "/tmp/menu.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/start.sh",
                    "Icon": "/tmp/icon.png",
                    "Status": "aktiv",
                },
                {
                    "Datei": "netmon-secure-browser-firefox-github-old.desktop",
                    "Pfad": "/tmp/menu-old.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/old-start.sh",
                    "Icon": "/tmp/old-icon.png",
                    "Status": "zusätzlich",
                },
            ],
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh\n./firefox/firefox --no-remote",
            "launcher.desktop": "[Desktop Entry]\nExec=/tmp/start.sh",
        },
    )
    manager = SecureBrowserManager(service=service)
    manager.last_scan = [
        BrowserContainer(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
            profile_path=Path("/tmp/firefox-GitHub/profile"),
            homepage_url="https://github.com",
            allowed_domains=["github.com"],
            icon_path=Path("/tmp/firefox-GitHub/icons"),
            menu_entry_path=Path("/tmp/menu.desktop"),
            status="vollständig",
        )
    ]

    report = manager.render_container_report("firefox-GitHub")

    assert "firefox-GitHub" in report
    assert "Risiko-Hinweise" in report
    assert "- Externes Mozilla-Profil eingebunden" in report
    assert "Verifikation" in report
    assert "- Firefox-Binary: OK" in report
    assert "- Menüeintrag: OK" in report
    assert "Launcher-Prüfung" in report
    assert "- Exec: /tmp/start.sh" in report
    assert "[Gefundene Menüeinträge]" in report
    assert "Datei: netmon-secure-browser-firefox-github.desktop" in report
    assert "Icon: /tmp/old-icon.png" in report
    assert "Artefakte" in report
    assert "[start.sh]" in report
    assert "Exec=/tmp/start.sh" in report


def test_secure_browser_manager_provides_copy_payload():
    service = SimpleNamespace(
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Exec": "/tmp/start.sh",
            },
            "menu_entry": {
                "Exec": "nicht gesetzt",
            },
        }
    )
    manager = SecureBrowserManager(service=service)
    manager.last_scan = [
        BrowserContainer(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
            profile_path=Path("/tmp/firefox-GitHub/profile"),
            homepage_url="https://github.com",
            allowed_domains=["github.com"],
            icon_path=Path("/tmp/firefox-GitHub/icons"),
            menu_entry_path=Path("/tmp/menu.desktop"),
            status="vollständig",
        )
    ]

    payload = manager.get_copy_payload("firefox-GitHub")

    assert payload == {
        "path": "/tmp/firefox-GitHub",
        "exec": "/tmp/start.sh",
    }


def test_secure_browser_service_derives_risk_hints_for_external_profile():
    service = SecureBrowserService()
    container = BrowserContainer(
        name="firefox-GitHub",
        path=Path("/tmp/firefox-GitHub"),
        binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
        profile_path=Path.home() / ".mozilla" / "firefox" / "abcd.default",
        homepage_url="https://github.com",
        allowed_domains=["github.com"],
        icon_path=Path("/tmp/firefox-GitHub/icons"),
        menu_entry_path=None,
        status="vollständig",
    )

    risks = service.derive_risk_hints(container)

    assert "Externes Mozilla-Profil eingebunden" in risks
    assert "start.sh fehlt" in risks
    assert "launcher.desktop fehlt" in risks
    assert "Menüeintrag fehlt" in risks


def test_secure_browser_manager_renders_inventory_export():
    manager = SecureBrowserManager(service=SimpleNamespace())
    manager.last_scan = [
        BrowserContainer(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
            profile_path=Path("/tmp/firefox-GitHub/profile"),
            homepage_url="https://github.com",
            allowed_domains=["github.com"],
            icon_path=Path("/tmp/firefox-GitHub/icons"),
            menu_entry_path=Path("/tmp/menu.desktop"),
            status="vollständig",
        )
    ]

    exported = manager.render_inventory_export()

    assert exported.startswith("# Secure Browser Inventory")
    assert "## firefox-GitHub" in exported
    assert "- Domains: github.com" in exported


def test_secure_browser_manager_renders_artifact_view():
    service = SimpleNamespace(
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh",
            "launcher.desktop": "[Desktop Entry]",
        }
    )
    manager = SecureBrowserManager(service=service)
    manager.last_scan = [
        BrowserContainer(
            name="firefox-GitHub",
            path=Path("/tmp/firefox-GitHub"),
            binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
            profile_path=Path("/tmp/firefox-GitHub/profile"),
            homepage_url="https://github.com",
            allowed_domains=["github.com"],
            icon_path=Path("/tmp/firefox-GitHub/icons"),
            menu_entry_path=Path("/tmp/menu.desktop"),
            status="vollständig",
        )
    ]

    report = manager.render_selected_view(
        manager.VIEW_ARTIFACTS,
        "firefox-GitHub",
    )

    assert "Artefakte" in report
    assert "[start.sh]" in report


def test_secure_browser_service_scan_containers_reads_builder_inventory(monkeypatch):
    service = SecureBrowserService()
    scanned_base_dirs = []
    fake_container = SimpleNamespace(
        name="firefox-GitHub",
        root_dir=Path("/tmp/firefox-GitHub"),
        binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
        domains=["github.com"],
    )
    fake_menu_entry = SimpleNamespace(
        path=Path("/tmp/applications/netmon-secure-browser-firefox-github.desktop"),
        container_root=Path("/tmp/firefox-GitHub"),
        container_name="firefox-GitHub",
    )
    fake_module = SimpleNamespace(
        DEFAULT_BASE_DIR="/tmp",
        DEFAULT_PROFILE_BASE_DIRS=["/tmp/profiles"],
        DEFAULT_APPLICATIONS_DIR="/tmp/applications",
        discover_existing_containers=lambda base_dir: (
            scanned_base_dirs.append(base_dir) or [fake_container]
        ),
        discover_firefox_profiles=lambda profile_dirs: [
            Path("/tmp/profiles/profile.default")
        ],
        correlate_profiles=lambda containers, profiles: None,
        list_managed_menu_entries=lambda applications_dir: [fake_menu_entry],
        get_effective_profile_path=lambda container: Path(
            "/tmp/profiles/profile.default"
        ),
        read_existing_homepage_url=lambda container: "https://github.com",
        read_existing_allowed_domains=lambda container: [
            "github.com",
            "githubassets.com",
        ],
        derive_container_status=lambda container, associated: "vollständig",
    )

    monkeypatch.setattr(service, "_load_tool_module", lambda: fake_module)
    monkeypatch.setattr(
        service,
        "get_default_base_dir",
        lambda: Path("/tmp/Documents/NetMon/Secure Browser"),
    )

    containers = service.scan_containers()

    assert len(containers) == 1
    assert containers[0].name == "firefox-GitHub"
    assert containers[0].profile_path == Path("/tmp/profiles/profile.default")
    assert containers[0].menu_entry_path == fake_menu_entry.path
    assert containers[0].status == "vollständig"
    assert containers[0].homepage_url == "https://github.com"
    assert containers[0].allowed_domains == ["github.com", "githubassets.com"]
    assert scanned_base_dirs == [Path("/tmp/Documents/NetMon/Secure Browser")]


def test_secure_browser_service_scan_containers_reads_icon_from_launcher(
    monkeypatch, tmp_path
):
    service = SecureBrowserService()
    root_dir = tmp_path / "firefox-GitHub"
    root_dir.mkdir()
    launcher_path = root_dir / "launcher.desktop"
    icon_path = root_dir / "icons" / "favicon.png"
    icon_path.parent.mkdir()
    icon_path.write_text("png", encoding="utf-8")
    launcher_path.write_text(
        f"[Desktop Entry]\nIcon={icon_path}\n",
        encoding="utf-8",
    )
    fake_container = SimpleNamespace(
        name="firefox-GitHub",
        root_dir=root_dir,
        binary_path=root_dir / "firefox" / "firefox",
        domains=["github.com"],
    )
    fake_module = SimpleNamespace(
        DEFAULT_PROFILE_BASE_DIRS=["/tmp/profiles"],
        DEFAULT_APPLICATIONS_DIR="/tmp/applications",
        discover_existing_containers=lambda _base_dir: [fake_container],
        discover_firefox_profiles=lambda _profile_dirs: [],
        correlate_profiles=lambda _containers, _profiles: None,
        list_managed_menu_entries=lambda _applications_dir: [],
        get_effective_profile_path=lambda _container: None,
        derive_container_status=lambda _container, _associated: "vollständig",
    )

    monkeypatch.setattr(service, "_load_tool_module", lambda: fake_module)

    containers = service.scan_containers()

    assert containers[0].icon_path == icon_path
    assert containers[0].icon_value == str(icon_path)


def test_secure_browser_service_inspects_all_associated_menu_entries(monkeypatch):
    service = SecureBrowserService()
    container = BrowserContainer(
        name="Sparkasse",
        path=Path("/tmp/Sparkasse"),
        binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
        profile_path=Path("/tmp/Sparkasse/profile"),
        homepage_url="https://www.sparkasse-ulm.de",
        allowed_domains=["www.sparkasse-ulm.de"],
        icon_path=Path("/tmp/Sparkasse/icons"),
        menu_entry_path=Path(
            "/tmp/applications/netmon-secure-browser-sparkasse.desktop"
        ),
        status="vollständig",
    )
    fake_module = SimpleNamespace(
        DEFAULT_APPLICATIONS_DIR=Path("/tmp/applications"),
    )

    monkeypatch.setattr(service, "_load_tool_module", lambda: fake_module)
    monkeypatch.setattr(
        Path,
        "is_dir",
        lambda self: str(self) == "/tmp/applications",
    )
    monkeypatch.setattr(
        Path,
        "glob",
        lambda self, pattern: (
            [
                Path("/tmp/applications/netmon-secure-browser-sparkasse.desktop"),
                Path("/tmp/applications/Sparkasse.desktop"),
            ]
            if str(self) == "/tmp/applications" and pattern == "*.desktop"
            else []
        ),
    )
    monkeypatch.setattr(
        service,
        "_parse_desktop_entry",
        lambda path: {
            "Name": (
                "NetMon Secure Browser – Sparkasse"
                if path.name == "netmon-secure-browser-sparkasse.desktop"
                else "Sparkasse"
            ),
            "Exec": (
                "/tmp/Sparkasse/start.sh"
                if path.name
                in {
                    "netmon-secure-browser-sparkasse.desktop",
                    "Sparkasse.desktop",
                }
                else f"{path.stem}-exec"
            ),
            "Icon": f"{path.stem}-icon",
            "Type": "Application",
            "Categories": "Network;Security;",
        },
    )

    info = service.inspect_launchers(container)

    assert len(info["menu_entries"]) == 2
    assert any(entry["Datei"] == "Sparkasse.desktop" for entry in info["menu_entries"])
    assert any(entry["Status"] == "aktiv" for entry in info["menu_entries"])
    assert any(entry["Status"] == "zusätzlich" for entry in info["menu_entries"])


def test_secure_browser_integrity_checks_report_system_icon_name():
    service = SecureBrowserService()
    container = BrowserContainer(
        name="Claude",
        path=Path("/tmp/Claude"),
        binary_path=Path("/tmp/Claude/firefox/firefox"),
        profile_path=Path("/tmp/Claude/profile"),
        homepage_url="https://claude.ai",
        allowed_domains=["claude.ai"],
        icon_path=None,
        icon_value="firefox",
        menu_entry_path=None,
        status="Launcher fehlt",
    )

    checks = service.verify_container(container)

    assert "Menüeintrag: nicht registriert" in checks
    assert "Icon: System-Icon-Name hinterlegt (firefox)" in checks


def test_secure_browser_service_parse_exec_target_supports_env_bamf_hint():
    target = SecureBrowserService._parse_exec_target(
        {
            "Exec": (
                'env BAMF_DESKTOP_FILE_HINT="/tmp/sparkasse.desktop" '
                '"/tmp/Sparkasse/start.sh"'
            )
        }
    )

    assert target == Path("/tmp/Sparkasse/start.sh")


def test_secure_browser_service_loads_real_builder_module():
    service = SecureBrowserService()

    module = service._load_tool_module()

    assert module.__name__ == "netmon_secure_browser_builder"
    assert hasattr(module, "discover_existing_containers")
    assert hasattr(module, "DEFAULT_BASE_DIR")


def test_secure_browser_service_runs_internal_builder_dry_run(monkeypatch):
    service = SecureBrowserService()
    fake_spec = SimpleNamespace(name="firefox-GitHub2")
    fake_module = SimpleNamespace(
        DEFAULT_APPLICATIONS_DIR=Path("/tmp/applications"),
        validate_config_payload=lambda payload, base_dir: [fake_spec],
        discover_existing_containers=lambda base_dir: [],
        select_missing_sources=lambda specs, discovered: [],
        build_apply_plan=lambda specs, discovered, applications_dir: [
            "Dry-Run Plan",
            "",
            "- firefox-GitHub2",
            "  Status: OK: Zielordner frei",
        ],
    )
    monkeypatch.setattr(service, "_load_tool_module", lambda: fake_module)
    monkeypatch.setattr(service, "get_default_base_dir", lambda: Path("/tmp/Programme"))

    lines = service.run_create_dry_run(
        name="firefox-GitHub2",
        homepage_url="https://github.com",
        allowed_domains=["github.com"],
        target_dir=Path("/tmp/Programme/firefox-GitHub2"),
        menu_name="NetMon Secure Browser – GitHub2",
        new_tab_url="about:blank",
        icon_mode="favicon",
    )

    assert lines[0] == "Builder Dry-Run"
    assert "Dry-Run Plan" in lines
    assert "  Status: OK: Zielordner frei" in lines


def test_secure_browser_manager_renders_blocked_apply_preview():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
        )
    )

    rendered = manager.render_create_browser_apply_preview(
        "firefox-GitHub2",
        "https://github.com",
        "github.com, githubassets.com",
        confirmation="NOPE",
    )

    assert "Apply-Vorbereitung" in rendered
    assert "Noch blockiert" in rendered
    assert "`APPLY`" in rendered


def test_secure_browser_manager_renders_confirmed_apply_preview():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
                "",
                "- firefox-GitHub2",
                "  Status: OK: Zielordner frei",
            ],
        )
    )

    rendered = manager.render_create_browser_apply_preview(
        "firefox-GitHub2",
        "https://github.com",
        "github.com, githubassets.com",
        confirmation="APPLY",
    )

    assert "Bestätigungscode akzeptiert" in rendered
    assert "Dry-Run Plan" in rendered


def test_secure_browser_manager_executes_apply_after_confirmation():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
            ],
            execute_create_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --config /tmp/generated.json --only firefox-GitHub2 --apply",
                "returncode": 0,
                "stdout": "Applied successfully",
                "stderr": "",
                "ok": True,
            },
        )
    )

    rendered = manager.execute_create_browser_apply(
        "firefox-GitHub2",
        "https://github.com",
        "github.com, githubassets.com",
        confirmation="APPLY",
    )

    assert "Apply-Ausführung" in rendered
    assert "Return-Code: 0" in rendered
    assert "Applied successfully" in rendered


def test_secure_browser_manager_execute_create_browser_apply_raises_on_builder_failure():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
            ],
            execute_create_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --config /tmp/generated.json --only firefox-GitHub2 --apply",
                "returncode": 1,
                "stdout": "",
                "stderr": "source_firefox_dir fehlt",
                "ok": False,
            },
        )
    )

    try:
        manager.execute_create_browser_apply(
            "firefox-GitHub2",
            "https://github.com",
            "github.com, githubassets.com",
            confirmation="APPLY",
        )
    except RuntimeError as exc:
        text = str(exc)
        assert "Apply-Ausführung" in text
        assert "Return-Code: 1" in text
        assert "source_firefox_dir fehlt" in text
    else:
        raise AssertionError("Expected RuntimeError for failing builder apply")


def test_secure_browser_manager_renders_register_existing_preview():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_register_existing_dry_run=lambda **kwargs: [
                "Dry-Run Register Existing",
                "",
                "- firefox-chatgpt",
            ]
        )
    )

    rendered = manager.render_register_existing_preview("firefox-chatgpt", "REGISTER")

    assert "Register-Vorbereitung" in rendered
    assert "Bestätigungscode akzeptiert" in rendered
    assert "firefox-chatgpt" in rendered
    assert (
        "Wirkung: start.sh, launcher.desktop und Menüeintrag werden bei Bedarf nachgezogen"
        in rendered
    )


def test_secure_browser_manager_renders_register_existing_preview_for_custom_container():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_register_existing_dry_run=lambda **kwargs: [
                "Dry-Run Register Existing",
                "",
                "- Sparkasse",
            ]
        )
    )

    rendered = manager.render_register_existing_preview("Sparkasse", "REGISTER")

    assert "- Auswahl: Sparkasse" in rendered
    assert "Sparkasse" in rendered


def test_secure_browser_manager_executes_cleanup_menu_apply():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_cleanup_menu_dry_run=lambda: [
                "Dry-Run Cleanup Menu",
                "",
                "- orphan.desktop: verwaist",
            ],
            execute_cleanup_menu_apply=lambda: {
                "command": "python3 /tmp/tools/browser_container_builder.py --cleanup-menu --apply",
                "returncode": 0,
                "stdout": "Cleanup complete",
                "stderr": "",
                "ok": True,
            },
        )
    )

    rendered = manager.execute_cleanup_menu_apply("CLEANUP")

    assert "Cleanup-Ausführung" in rendered
    assert "Cleanup complete" in rendered


def test_secure_browser_manager_raises_when_admin_builder_action_fails():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_cleanup_menu_dry_run=lambda: ["Dry-Run Cleanup Menu"],
            execute_cleanup_menu_apply=lambda: {
                "command": "python3 builder.py --cleanup-menu --apply",
                "returncode": 1,
                "stdout": "",
                "stderr": "Menüeintrag konnte nicht entfernt werden",
                "ok": False,
            },
        )
    )

    try:
        manager.execute_cleanup_menu_apply("CLEANUP")
    except RuntimeError as exc:
        rendered = str(exc)
        assert "Cleanup-Ausführung" in rendered
        assert "Return-Code: 1" in rendered
        assert "Menüeintrag konnte nicht entfernt werden" in rendered
    else:
        raise AssertionError("Expected RuntimeError for failing admin builder action")


def test_secure_browser_manager_executes_uninstall_apply():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_uninstall_dry_run=lambda **kwargs: [
                "Dry-Run Uninstall",
                "",
                "- Container: firefox-GitHub",
            ],
            execute_uninstall_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --uninstall firefox-GitHub --apply",
                "returncode": 0,
                "stdout": "Container moved to uninstall backup",
                "stderr": "",
                "ok": True,
            },
        )
    )

    rendered = manager.execute_uninstall_apply("firefox-GitHub", "UNINSTALL")

    assert "Uninstall-Ausführung" in rendered
    assert "Container moved to uninstall backup" in rendered


def test_secure_browser_manager_uninstall_preview_handles_missing_container():
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_uninstall_dry_run=lambda **kwargs: (_ for _ in ()).throw(
                ValueError("Container nicht gefunden: firefox-GitHub")
            )
        )
    )

    rendered = manager.render_uninstall_preview("firefox-GitHub", "UNINSTALL")

    assert "Uninstall-Vorbereitung" in rendered
    assert "Status: nicht verfügbar" in rendered
    assert "Container nicht gefunden: firefox-GitHub" in rendered


def test_secure_browser_manager_uninstall_execute_stops_when_container_missing():
    called = {"executed": False}
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            run_uninstall_dry_run=lambda **kwargs: (_ for _ in ()).throw(
                ValueError("Container nicht gefunden: firefox-GitHub")
            ),
            execute_uninstall_apply=lambda **kwargs: called.update(executed=True),
        )
    )

    rendered = manager.execute_uninstall_apply("firefox-GitHub", "UNINSTALL")

    assert "Container nicht gefunden: firefox-GitHub" in rendered
    assert called["executed"] is False


def test_secure_browser_tab_can_be_created(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module
    from netmon.ui.tabs.secure_browser_tab import build_secure_browser_tab

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox())

    app = type(
        "DummyApp",
        (),
        {
            "nb": DummyNotebook(),
            "tr": staticmethod(lambda _key, default=None: default or _key),
        },
    )()

    build_secure_browser_tab(app)

    assert hasattr(app, "tab_secure_browser")
    assert app.nb.added
    assert app.nb.added[0][1]["text"] == "🌐 Secure Browser"
    assert "create" not in app.tab_secure_browser.secure_browser_buttons
    assert (
        app.tab_secure_browser.secure_browser_buttons["inventory"].kwargs["state"]
        == "normal"
    )
    assert (
        app.tab_secure_browser.secure_browser_buttons["inspect_launcher"].kwargs[
            "state"
        ]
        == "disabled"
    )
    assert (
        app.tab_secure_browser.secure_browser_buttons["backup"].kwargs["state"]
        == "disabled"
    )
    assert (
        app.tab_secure_browser.secure_browser_buttons["edit_policy"].kwargs["state"]
        == "disabled"
    )
    assert (
        app.tab_secure_browser.secure_browser_buttons["save_policy"].kwargs["state"]
        == "disabled"
    )
    assert (
        app.tab_secure_browser.secure_browser_buttons["add_policy_exception"].kwargs[
            "state"
        ]
        == "disabled"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_hint_label.kwargs["text"]
        == "Webseite eingeben, Rest wird automatisch abgeleitet. Felder bleiben änderbar."
    )
    assert app.tab_secure_browser.secure_browser_view_mode.get() == "Übersicht"
    assert app.tab_secure_browser.secure_browser_draft_name_entry.get() == ""
    assert app.tab_secure_browser.secure_browser_draft_icon_mode.get() == "favicon"
    assert (
        app.tab_secure_browser.secure_browser_draft_security_profile.get() == "Standard"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_security_profile_hint.configure_kwargs[
            "text"
        ]
        == "Standard: guter Mittelweg aus Trennung, Komfort und Kompatibilität."
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_allow_password_manager_var.get()
        is True
    )
    assert app.tab_secure_browser.secure_browser_draft_keep_cookies_var.get() is True
    assert (
        app.tab_secure_browser.secure_browser_draft_enable_website_filter_var.get()
        is True
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_preview_button.kwargs["state"]
        == "normal"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_preview_button.kwargs["text"]
        == "Neu"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_dry_run_button.kwargs["state"]
        == "normal"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_dry_run_button.kwargs["text"]
        == "Dry-Run"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_execute_button.kwargs["state"]
        == "normal"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_execute_button.kwargs["text"]
        == "Anlegen"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_remove_button.kwargs["state"]
        == "normal"
    )
    assert (
        app.tab_secure_browser.secure_browser_draft_remove_button.kwargs["text"]
        == "Entfernen"
    )
    assert (
        app.tab_secure_browser.secure_browser_status_badge.kwargs["text"]
        == "Bereit: read-only Startzustand"
    )
    assert (
        app.tab_secure_browser.secure_browser_status_badge.kwargs["style"]
        == "SecureBrowser.Status.Ready.TLabel"
    )
    assert (
        app.tab_secure_browser.secure_browser_create_section_label.kwargs["text"]
        == "Erstellen"
    )
    assert (
        app.tab_secure_browser.secure_browser_admin_section_label.kwargs["text"]
        == "Verwaltung"
    )
    assert (
        "Inventur noch nicht ausgeführt."
        in app.tab_secure_browser.secure_browser_summary_text.text_content
    )
    assert (
        "Secure-Browser-Preflight"
        in app.tab_secure_browser.secure_browser_detail_text.text_content
    )


def test_secure_browser_tab_uses_translation_callback(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox())

    def translate(key, default=None):
        mapping = {
            "secure_browser_label_view": "ViewX:",
            "secure_browser_btn_inventory": "ScanX",
            "secure_browser_section_create": "CreateX",
        }
        return mapping.get(key, default or key)

    frame = create_secure_browser_tab(
        DummyWidget(),
        SecureBrowserManager(service=SimpleNamespace(run_preflight_checks=lambda: [])),
        tr=translate,
    )

    assert frame.secure_browser_create_section_label.kwargs["text"] == "CreateX"
    assert frame.secure_browser_draft_inventory_button.kwargs["text"] == "ScanX"


def test_secure_browser_policy_editor_button_loads_json(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    class PolicyEditorService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-OpenAI",
                    path=Path("/tmp/firefox-OpenAI"),
                    binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-OpenAI/profile"),
                    homepage_url="https://chatgpt.com",
                    allowed_domains=["chatgpt.com"],
                    icon_path=Path("/tmp/firefox-OpenAI/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def read_policy_json(self, container):
            return '{\n  "policies": {\n    "WebsiteFilter": {}\n  }\n}\n'

        def verify_container(self, container):
            return ["OK"]

        def derive_risk_hints(self, container):
            return ["Keine offensichtlichen Risiken erkannt"]

        def read_container_artifacts(self, container):
            return {"start.sh": "ok", "launcher.desktop": "ok"}

        def inspect_launchers(self, container):
            return {"launcher.desktop": {}, "menu_entry": {}, "menu_entries": []}

        def run_preflight_checks(self):
            return []

    frame = create_secure_browser_tab(
        DummyWidget(), SecureBrowserManager(service=PolicyEditorService())
    )

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["edit_policy"].kwargs["command"]()

    assert '"WebsiteFilter"' in frame.secure_browser_detail_text.text_content
    assert frame.secure_browser_detail_text.configure_kwargs["state"] == "normal"


def test_secure_browser_policy_editor_save_button_persists_json(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    captured = {}

    class PolicyEditorSaveService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-OpenAI",
                    path=Path("/tmp/firefox-OpenAI"),
                    binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-OpenAI/profile"),
                    homepage_url="https://chatgpt.com",
                    allowed_domains=["chatgpt.com"],
                    icon_path=Path("/tmp/firefox-OpenAI/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def read_policy_json(self, container):
            return '{\n  "policies": {}\n}\n'

        def save_policy_json(self, container, content):
            captured["content"] = content
            return {
                "source_path": "/tmp/firefox-OpenAI/policies.json",
                "runtime_path": "/tmp/firefox-OpenAI/firefox/distribution/policies.json",
                "backup_dir": "/tmp/firefox-OpenAI/backups/policy-editor-backups/stamp",
                "backup_count": "2",
            }

        def verify_container(self, container):
            return ["OK"]

        def derive_risk_hints(self, container):
            return ["Keine offensichtlichen Risiken erkannt"]

        def read_container_artifacts(self, container):
            return {"start.sh": "ok", "launcher.desktop": "ok"}

        def inspect_launchers(self, container):
            return {"launcher.desktop": {}, "menu_entry": {}, "menu_entries": []}

        def run_preflight_checks(self):
            return []

    frame = create_secure_browser_tab(
        DummyWidget(),
        SecureBrowserManager(service=PolicyEditorSaveService()),
    )

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["edit_policy"].kwargs["command"]()
    frame.secure_browser_detail_text.delete("1.0", "end")
    frame.secure_browser_detail_text.insert(
        "1.0", '{"policies":{"WebsiteFilter":{"Exceptions":["*://chatgpt.com/*"]}}}'
    )
    frame.secure_browser_buttons["save_policy"].kwargs["command"]()

    assert '"WebsiteFilter"' in captured["content"]


def test_secure_browser_policy_exception_button_appends_url(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=False))
    monkeypatch.setattr(
        ui_module,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *args, **kwargs: "https://www.example.com/mail"
        ),
    )

    class PolicyEditorExceptionService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-Example",
                    path=Path("/tmp/firefox-Example"),
                    binary_path=Path("/tmp/firefox-Example/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-Example/profile"),
                    homepage_url="https://www.example.com",
                    allowed_domains=["www.example.com"],
                    icon_path=Path("/tmp/firefox-Example/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def read_policy_json(self, container):
            return '{\n  "policies": {\n    "WebsiteFilter": {\n      "Block": ["<all_urls>"],\n      "Exceptions": []\n    }\n  }\n}\n'

        def save_policy_json(self, container, content):
            return {
                "source_path": "/tmp/firefox-Example/policies.json",
                "runtime_path": "/tmp/firefox-Example/firefox/distribution/policies.json",
                "backup_dir": "/tmp/firefox-Example/backups/policy-editor-backups/stamp",
                "backup_count": "2",
            }

        def verify_container(self, container):
            return ["OK"]

        def derive_risk_hints(self, container):
            return ["Keine offensichtlichen Risiken erkannt"]

        def read_container_artifacts(self, container):
            return {"start.sh": "ok", "launcher.desktop": "ok"}

        def inspect_launchers(self, container):
            return {"launcher.desktop": {}, "menu_entry": {}, "menu_entries": []}

        def run_preflight_checks(self):
            return []

    frame = create_secure_browser_tab(
        DummyWidget(),
        SecureBrowserManager(service=PolicyEditorExceptionService()),
    )

    assert (
        frame.secure_browser_buttons["add_policy_exception"].kwargs["state"]
        == "disabled"
    )
    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    assert (
        frame.secure_browser_buttons["add_policy_exception"].kwargs["state"] == "normal"
    )
    frame.secure_browser_buttons["add_policy_exception"].kwargs["command"]()

    assert (
        "https://www.example.com/mail*" in frame.secure_browser_detail_text.text_content
    )

    valid_editor_content = frame.secure_browser_detail_text.text_content
    monkeypatch.setattr(
        ui_module,
        "_prompt_url_with_context_menu",
        lambda *_args, **_kwargs: "keine-gueltige-domain",
    )
    frame.secure_browser_buttons["add_policy_exception"].kwargs["command"]()

    assert frame.secure_browser_detail_text.text_content == valid_editor_content
    assert frame.secure_browser_buttons["save_policy"].kwargs["state"] == "normal"
    assert "Ungültige URL oder Domain" in (
        frame.secure_browser_status_badge.configure_kwargs["text"]
    )


def test_secure_browser_policy_exception_button_auto_loads_editor_and_saves(
    monkeypatch,
):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    messagebox_stub = DummyMessageBoxSequence([True])
    monkeypatch.setattr(ui_module, "messagebox", messagebox_stub)
    monkeypatch.setattr(
        ui_module,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *args, **kwargs: "https://www.example.com/mail"
        ),
    )

    captured = {}

    class PolicyEditorExceptionSaveService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-Example",
                    path=Path("/tmp/firefox-Example"),
                    binary_path=Path("/tmp/firefox-Example/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-Example/profile"),
                    homepage_url="https://www.example.com",
                    allowed_domains=["www.example.com"],
                    icon_path=Path("/tmp/firefox-Example/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def read_policy_json(self, container):
            return '{\n  "policies": {\n    "WebsiteFilter": {\n      "Block": ["<all_urls>"],\n      "Exceptions": []\n    }\n  }\n}\n'

        def save_policy_json(self, container, content):
            captured["content"] = content
            return {
                "source_path": "/tmp/firefox-Example/policies.json",
                "runtime_path": "/tmp/firefox-Example/firefox/distribution/policies.json",
                "backup_dir": "/tmp/firefox-Example/backups/policy-editor-backups/stamp",
                "backup_count": "2",
            }

        def verify_container(self, container):
            return ["OK"]

        def derive_risk_hints(self, container):
            return ["Keine offensichtlichen Risiken erkannt"]

        def read_container_artifacts(self, container):
            return {"start.sh": "ok", "launcher.desktop": "ok"}

        def inspect_launchers(self, container):
            return {"launcher.desktop": {}, "menu_entry": {}, "menu_entries": []}

        def run_preflight_checks(self):
            return []

    frame = create_secure_browser_tab(
        DummyWidget(),
        SecureBrowserManager(service=PolicyEditorExceptionSaveService()),
    )

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["add_policy_exception"].kwargs["command"]()

    assert "https://www.example.com/mail*" in captured["content"]
    assert "firefox-Example" in frame.secure_browser_detail_text.text_content
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"] == "[OK] Übersicht"
    )
    assert messagebox_stub.calls == [
        ("Whitelist speichern", "Ausnahme für firefox-Example jetzt direkt speichern?")
    ]


def test_prompt_url_with_context_menu_falls_back_to_simpledialog(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "simpledialog",
        SimpleNamespace(askstring=lambda *args, **kwargs: "https://example.com/path"),
    )

    value = _prompt_url_with_context_menu(DummyWidget(), "Titel", "Prompt")

    assert value == "https://example.com/path"


def test_secure_browser_inventory_button_renders_read_only_scan(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path(),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: [
            "Keine offensichtlichen Risiken erkannt",
        ],
        verify_container=lambda container: [
            "Firefox-Binary: OK",
            "Profil: nicht erkannt",
        ],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": "/tmp/menu.desktop",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
            "menu_entries": [
                {
                    "Datei": "netmon-secure-browser-firefox-github.desktop",
                    "Pfad": "/tmp/menu.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/start.sh",
                    "Icon": "/tmp/icon.png",
                    "Status": "aktiv",
                },
                {
                    "Datei": "netmon-secure-browser-firefox-github-old.desktop",
                    "Pfad": "/tmp/menu-old.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/old-start.sh",
                    "Icon": "/tmp/old-icon.png",
                    "Status": "zusätzlich",
                },
            ],
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh\n./firefox/firefox --no-remote",
            "launcher.desktop": "[Desktop Entry]\nExec=/tmp/start.sh",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()

    assert frame.secure_browser_container_list.items == ["firefox-GitHub"]
    assert (
        "1 Secure-Browser-Container erkannt."
        in frame.secure_browser_summary_text.text_content
    )
    assert (
        "Kennzahlen: Gesamt: 1 | vollständig: 1 | externe Profile: 0 | fehlende Launcher: 0 | fehlende Menüeinträge: 0"
        in frame.secure_browser_summary_text.text_content
    )
    rendered = frame.secure_browser_detail_text.text_content
    assert "firefox-GitHub" in rendered
    assert "Status: vollständig" in rendered
    assert "Profil: nicht erkannt" in rendered
    assert "Verifikation" in rendered
    assert "Launcher-Prüfung" in rendered
    assert "Artefakte" in rendered
    assert "[launcher.desktop]" in rendered
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"] == "[OK] Übersicht"
    )
    assert (
        frame.secure_browser_status_badge.configure_kwargs["style"]
        == "SecureBrowser.Status.Ok.TLabel"
    )
    assert frame.secure_browser_detail_text.configure_kwargs["state"] == "disabled"


def test_secure_browser_launcher_button_renders_launcher_report(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["Firefox-Binary: OK"],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": "/tmp/menu.desktop",
                "Name": "NetMon Secure Browser – GitHub",
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
            "menu_entries": [
                {
                    "Datei": "netmon-secure-browser-firefox-github.desktop",
                    "Pfad": "/tmp/menu.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/start.sh",
                    "Icon": "/tmp/icon.png",
                    "Status": "aktiv",
                },
                {
                    "Datei": "netmon-secure-browser-firefox-github-old.desktop",
                    "Pfad": "/tmp/menu-old.desktop",
                    "Name": "NetMon Secure Browser – GitHub",
                    "Exec": "/tmp/old-start.sh",
                    "Icon": "/tmp/old-icon.png",
                    "Status": "zusätzlich",
                },
            ],
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh\n./firefox/firefox --no-remote",
            "launcher.desktop": "[Desktop Entry]\nExec=/tmp/start.sh",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["inspect_launcher"].kwargs["command"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "Launcher-Prüfung" in rendered
    assert "[launcher.desktop strukturiert]" in rendered
    assert "[Gefundene Menüeinträge]" in rendered
    assert "Datei: netmon-secure-browser-firefox-github-old.desktop" in rendered
    assert "Icon: /tmp/old-icon.png" in rendered
    assert "- Exec: /tmp/start.sh" in rendered
    assert "[launcher.desktop Vorschau]" in rendered
    assert frame.secure_browser_view_mode.get() == "Launcher"


def test_secure_browser_view_mode_renders_artifacts(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            )
        ],
        verify_container=lambda container: ["Firefox-Binary: OK"],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": "/tmp/menu.desktop",
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh\n./firefox/firefox --no-remote",
            "launcher.desktop": "[Desktop Entry]\nExec=/tmp/start.sh",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_view_mode.set("Artefakte")
    frame.secure_browser_view_mode.bound_events["<<ComboboxSelected>>"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "Artefakte" in rendered
    assert "[start.sh]" in rendered
    assert "[launcher.desktop]" in rendered


def test_secure_browser_create_button_renders_draft(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            build_create_preview=lambda name, homepage_url, allowed_domains, **kwargs: {
                "tool_script": "/tmp/tools/browser_container_builder.py",
                "tool_config": "<generierte-create-config>",
                "command": (
                    "python3 /tmp/tools/browser_container_builder.py "
                    "--config <generierte-create-config> "
                    "--only firefox-GitHub2"
                ),
                "payload": '{\n  "name": "firefox-GitHub2"\n}',
                "source_firefox_dir": "/opt/netmon-browser/firefox",
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_name_entry.set("firefox-GitHub2")
    frame.secure_browser_draft_homepage_entry.set("https://github.com")
    frame.secure_browser_draft_domains_entry.set("github.com, githubassets.com")
    frame.secure_browser_draft_preview_button.configure_kwargs["command"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "Dry-Run-Entwurf" in rendered
    assert "- Zielordner: /tmp/Programme/firefox-GitHub2" in rendered
    assert "- Containername: firefox-GitHub2" in rendered
    assert "- Erlaubte Domains: github.com, githubassets.com" in rendered
    assert "Builder-Vorschau" in rendered
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"]
        == "[Vorschau] Neuer Browser"
    )
    assert (
        frame.secure_browser_status_badge.configure_kwargs["style"]
        == "SecureBrowser.Status.Preview.TLabel"
    )


def test_secure_browser_create_draft_derives_values_from_website(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_create_preview=lambda name, homepage_url, allowed_domains, **kwargs: {
                "tool_script": "/tmp/tools/browser_container_builder.py",
                "tool_config": "<generierte-create-config>",
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-sparkasse-ulm-de",
                "payload": '{\n  "name": "firefox-sparkasse-ulm-de"\n}',
                "source_firefox_dir": "/opt/netmon-browser/firefox",
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_homepage_entry.set("sparkasse-ulm.de")
    frame.secure_browser_draft_preview_button.configure_kwargs["command"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "- Webseite: https://sparkasse-ulm.de" in rendered
    assert "- Containername: firefox-sparkasse-ulm-de" in rendered
    assert "- Erlaubte Domains: sparkasse-ulm.de" in rendered
    assert "- Menüname: Sparkasse Ulm De" in rendered


def test_secure_browser_create_draft_supports_real_entry_widgets(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyTkEntryNoSet,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_create_preview=lambda name, homepage_url, allowed_domains, **kwargs: {
                "tool_script": "/tmp/tools/browser_container_builder.py",
                "tool_config": "<generierte-create-config>",
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-github",
                "payload": '{\n  "name": "firefox-github"\n}',
                "source_firefox_dir": "/opt/netmon-browser/firefox",
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_homepage_entry.insert(0, "github.com")
    frame.secure_browser_draft_preview_button.configure_kwargs["command"]()

    assert (
        "- Containername: firefox-github"
        in frame.secure_browser_detail_text.text_content
    )
    assert (
        "- Erlaubte Domains: github.com"
        in frame.secure_browser_detail_text.text_content
    )


def test_secure_browser_inputs_and_detail_bind_clipboard_shortcuts(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(service=SimpleNamespace())

    frame = create_secure_browser_tab(DummyWidget(), manager)

    for widget in (
        frame.secure_browser_draft_name_entry,
        frame.secure_browser_draft_homepage_entry,
        frame.secure_browser_draft_domains_entry,
        frame.secure_browser_draft_menu_entry,
        frame.secure_browser_draft_new_tab_entry,
        frame.secure_browser_detail_text,
    ):
        assert "<Control-c>" in widget.bound_events
        assert "<Control-v>" in widget.bound_events
        assert "<Control-x>" in widget.bound_events
        assert "<Button-3>" in widget.bound_events

    frame.secure_browser_detail_copy_button.configure_kwargs["command"]()
    assert "Secure-Browser-Preflight" in frame.clipboard_content
    assert (
        frame.secure_browser_detail_paste_button.configure_kwargs["state"] == "disabled"
    )


def test_secure_browser_draft_entry_copy_binding_generates_copy_event(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(service=SimpleNamespace())

    frame = create_secure_browser_tab(DummyWidget(), manager)
    handler = frame.secure_browser_draft_homepage_entry.bound_events["<Control-c>"]

    result = handler()

    assert result == "break"
    assert frame.secure_browser_draft_homepage_entry.generated_events == ["<<Copy>>"]


def test_secure_browser_builder_dry_run_button_renders_output(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            render_create_browser_builder_dry_run=None,
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
                "",
                "- firefox-GitHub2",
                "  Status: OK: Zielordner frei",
            ],
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_name_entry.set("firefox-GitHub2")
    frame.secure_browser_draft_homepage_entry.set("https://github.com")
    frame.secure_browser_draft_domains_entry.set("github.com, githubassets.com")
    frame.secure_browser_draft_dry_run_button.configure_kwargs["command"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "Builder-Dry-Run" in rendered
    assert "Dry-Run Plan" in rendered
    assert "Status: OK: Zielordner frei" in rendered


def test_secure_browser_apply_preview_button_blocks_without_token(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    dialog = DummyMessageBox(result=False)
    monkeypatch.setattr(ui_module, "messagebox", dialog)

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            scan_containers=lambda: [
                BrowserContainer(
                    name="firefox-GitHub2",
                    path=Path("/tmp/Programme/firefox-GitHub2"),
                    binary_path=Path("/tmp/Programme/firefox-GitHub2/firefox/firefox"),
                    profile_path=Path("/tmp/Programme/firefox-GitHub2/profile"),
                    homepage_url="https://github.com",
                    allowed_domains=["github.com"],
                    icon_path=Path("/tmp/Programme/firefox-GitHub2/icons"),
                    menu_entry_path=Path("/tmp/applications/menu.desktop"),
                    status="vollständig",
                )
            ],
            derive_risk_hints=lambda container: [
                "Keine offensichtlichen Risiken erkannt"
            ],
            verify_container=lambda container: ["OK"],
            inspect_launchers=lambda container: {
                "launcher.desktop": {},
                "menu_entry": {},
            },
            read_container_artifacts=lambda container: {
                "start.sh": "",
                "launcher.desktop": "",
            },
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
            ],
            execute_create_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --config /tmp/generated.json --only firefox-GitHub2 --apply",
                "returncode": 0,
                "stdout": "Applied successfully",
                "stderr": "",
                "ok": True,
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_name_entry.set("firefox-GitHub2")
    frame.secure_browser_draft_execute_button.configure_kwargs["command"]()

    assert dialog.calls
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"]
        == "[Blockiert] Erstellung abgebrochen"
    )


def test_secure_browser_apply_execute_button_confirms_before_apply(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    dialog = DummyMessageBox(result=True)
    monkeypatch.setattr(ui_module, "messagebox", dialog)

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            scan_containers=lambda: [
                BrowserContainer(
                    name="firefox-GitHub2",
                    path=Path("/tmp/Programme/firefox-GitHub2"),
                    binary_path=Path("/tmp/Programme/firefox-GitHub2/firefox/firefox"),
                    profile_path=Path("/tmp/Programme/firefox-GitHub2/profile"),
                    homepage_url="https://github.com",
                    allowed_domains=["github.com"],
                    icon_path=Path("/tmp/Programme/firefox-GitHub2/icons"),
                    menu_entry_path=Path("/tmp/applications/menu.desktop"),
                    status="vollständig",
                )
            ],
            derive_risk_hints=lambda container: [
                "Keine offensichtlichen Risiken erkannt"
            ],
            verify_container=lambda container: ["OK"],
            inspect_launchers=lambda container: {
                "launcher.desktop": {},
                "menu_entry": {},
            },
            read_container_artifacts=lambda container: {
                "start.sh": "",
                "launcher.desktop": "",
            },
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
            ],
            execute_create_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --config /tmp/generated.json --only firefox-GitHub2 --apply",
                "returncode": 0,
                "stdout": "Applied successfully",
                "stderr": "",
                "ok": True,
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_name_entry.set("firefox-GitHub2")
    frame.secure_browser_draft_execute_button.configure_kwargs["command"]()

    assert dialog.calls
    assert "firefox-GitHub2" in frame.secure_browser_detail_text.text_content


def test_secure_browser_apply_execute_button_runs_apply(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            list_create_presets=lambda: [],
            scan_containers=lambda: [
                BrowserContainer(
                    name="firefox-GitHub2",
                    path=Path("/tmp/Programme/firefox-GitHub2"),
                    binary_path=Path("/tmp/Programme/firefox-GitHub2/firefox/firefox"),
                    profile_path=Path("/tmp/Programme/firefox-GitHub2/profile"),
                    homepage_url="https://github.com",
                    allowed_domains=["github.com"],
                    icon_path=Path("/tmp/Programme/firefox-GitHub2/icons"),
                    menu_entry_path=Path("/tmp/applications/menu.desktop"),
                    status="vollständig",
                )
            ],
            derive_risk_hints=lambda container: [
                "Keine offensichtlichen Risiken erkannt"
            ],
            verify_container=lambda container: ["OK"],
            inspect_launchers=lambda container: {
                "launcher.desktop": {},
                "menu_entry": {},
            },
            read_container_artifacts=lambda container: {
                "start.sh": "",
                "launcher.desktop": "",
            },
            build_apply_preview=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --only firefox-GitHub2 --apply",
                "target_dir": "/tmp/Programme/firefox-GitHub2",
                "safety": "Backups werden vor Änderungen angelegt.",
            },
            run_create_dry_run=lambda **kwargs: [
                "Builder Dry-Run",
                "",
                "Dry-Run Plan",
            ],
            execute_create_apply=lambda **kwargs: {
                "command": "python3 /tmp/tools/browser_container_builder.py --config /tmp/generated.json --only firefox-GitHub2 --apply",
                "returncode": 0,
                "stdout": "Applied successfully",
                "stderr": "",
                "ok": True,
            },
        )
    )
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_name_entry.set("firefox-GitHub2")
    frame.secure_browser_draft_execute_button.configure_kwargs["command"]()

    rendered = frame.secure_browser_detail_text.text_content
    assert "firefox-GitHub2" in rendered
    assert frame.secure_browser_summary_text.text_content.startswith(
        "1 Secure-Browser-Container erkannt."
    )


def test_secure_browser_register_preview_and_execute(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-chatgpt",
                path=Path("/tmp/firefox-chatgpt"),
                binary_path=Path("/tmp/firefox-chatgpt/firefox/firefox"),
                profile_path=Path("/tmp/profile"),
                homepage_url="https://chatgpt.com",
                allowed_domains=["chatgpt.com"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="Launcher fehlt",
            )
        ],
        derive_risk_hints=lambda container: ["Menüeintrag fehlt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_register_existing_dry_run=lambda **kwargs: [
            "Dry-Run Register Existing",
            "",
            "- firefox-chatgpt",
        ],
        execute_register_existing_apply=lambda **kwargs: {
            "command": "python3 builder.py --register-existing --only firefox-chatgpt --apply",
            "returncode": 0,
            "stdout": "Registered",
            "stderr": "",
            "ok": True,
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["backup"].kwargs["command"]()
    assert "firefox-chatgpt" in frame.secure_browser_detail_text.text_content
    assert frame.secure_browser_summary_text.text_content.startswith(
        "1 Secure-Browser-Container erkannt."
    )


def test_secure_browser_contextual_action_states_follow_selection(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            ),
            BrowserContainer(
                name="firefox-chatgpt",
                path=Path("/tmp/firefox-chatgpt"),
                binary_path=Path("/tmp/firefox-chatgpt/firefox/firefox"),
                profile_path=Path("/tmp/profile"),
                homepage_url="https://chatgpt.com",
                allowed_domains=["chatgpt.com"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="Launcher fehlt",
            ),
        ],
        derive_risk_hints=lambda container: (
            ["Keine offensichtlichen Risiken erkannt"]
            if container.name == "firefox-GitHub"
            else ["Menüeintrag fehlt"]
        ),
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_preflight_checks=lambda: [],
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    assert frame.secure_browser_buttons["inspect_launcher"].kwargs["state"] == "normal"
    assert frame.secure_browser_buttons["edit_policy"].kwargs["state"] == "normal"
    assert frame.secure_browser_buttons["backup"].kwargs["state"] == "disabled"

    frame.secure_browser_container_list.selection_clear(0, "end")
    frame.secure_browser_container_list.selection_set(1)
    frame.secure_browser_container_list.bound_events["<<ListboxSelect>>"]()

    assert frame.secure_browser_buttons["inspect_launcher"].kwargs["state"] == "normal"
    assert frame.secure_browser_buttons["edit_policy"].kwargs["state"] == "normal"
    assert frame.secure_browser_buttons["backup"].kwargs["state"] == "normal"


def test_secure_browser_manager_resolves_custom_security_profile() -> None:
    manager = SecureBrowserManager(service=SimpleNamespace())

    resolved = manager.resolve_security_options(
        "Standard",
        enable_website_filter=False,
    )

    assert resolved["security_profile"] == "Benutzerdefiniert"
    assert resolved["allow_password_manager"] is True
    assert resolved["keep_cookies"] is True
    assert resolved["enable_website_filter"] is False


def test_secure_browser_manager_create_draft_renders_hardening_summary() -> None:
    manager = SecureBrowserManager(
        service=SimpleNamespace(
            get_default_base_dir=lambda: Path("/tmp/Programme"),
            build_create_preview=lambda *args, **kwargs: {
                "tool_script": "/tmp/browser_container_builder.py",
                "tool_config": "<generated>",
                "command": "python3 /tmp/browser_container_builder.py --only firefox-Test",
                "payload": "{}",
                "source_firefox_dir": "/tmp/firefox-source",
            },
        )
    )

    rendered = manager.render_create_browser_draft(
        "firefox-Test",
        "https://example.com",
        "example.com",
        "NetMon Secure Browser – Test",
        "about:blank",
        "favicon",
        "Streng",
        False,
        False,
        True,
    )

    assert "Hardening-Zusammenfassung" in rendered
    assert "- Sicherheitsprofil: Benutzerdefiniert" not in rendered
    assert "- Sicherheitsprofil: Streng" in rendered
    assert "- Cookies: werden beim Beenden gelöscht" in rendered
    assert "- Kompatibilitätsrisiko: hoch" in rendered


def test_secure_browser_register_preview_and_execute_for_custom_container(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="Sparkasse",
                path=Path("/tmp/Sparkasse"),
                binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
                profile_path=Path("/tmp/profile"),
                homepage_url="https://www.sparkasse-ulm.de",
                allowed_domains=["www.sparkasse-ulm.de"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="Launcher fehlt",
            )
        ],
        derive_risk_hints=lambda container: ["Menüeintrag fehlt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_register_existing_dry_run=lambda **kwargs: [
            "Dry-Run Register Existing",
            "",
            "- Sparkasse",
        ],
        execute_register_existing_apply=lambda **kwargs: {
            "command": "python3 builder.py --register-existing --only Sparkasse --apply",
            "returncode": 0,
            "stdout": "Registered Sparkasse",
            "stderr": "",
            "ok": True,
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["backup"].kwargs["command"]()
    assert "Sparkasse" in frame.secure_browser_detail_text.text_content
    assert frame.secure_browser_summary_text.text_content.startswith(
        "1 Secure-Browser-Container erkannt."
    )


def test_secure_browser_register_direct_blocks_without_selection(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    service = SimpleNamespace(
        scan_containers=lambda: [],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["backup"].kwargs["command"]()

    assert "Kein Container ausgewählt." in frame.secure_browser_detail_text.text_content
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"]
        == "[Blockiert] keine Auswahl"
    )


def test_secure_browser_refresh_preview_and_execute(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="Sparkasse",
                path=Path("/tmp/Sparkasse"),
                binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
                profile_path=Path("/tmp/profile"),
                homepage_url="https://www.sparkasse-ulm.de",
                allowed_domains=["www.sparkasse-ulm.de"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_refresh_existing_dry_run=lambda **kwargs: [
            "Dry-Run Refresh Existing",
            "",
            "- Sparkasse",
        ],
        execute_refresh_existing_apply=lambda **kwargs: {
            "command": "python3 builder.py --refresh-existing --only Sparkasse --apply",
            "returncode": 0,
            "stdout": "Refreshed Sparkasse",
            "stderr": "",
            "ok": True,
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["refresh_existing"].kwargs["command"]()
    assert "Sparkasse" in frame.secure_browser_detail_text.text_content
    assert frame.secure_browser_summary_text.text_content.startswith(
        "1 Secure-Browser-Container erkannt."
    )


def test_secure_browser_refresh_without_selection_updates_all(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    messagebox = DummyMessageBox(result=True)
    monkeypatch.setattr(ui_module, "messagebox", messagebox)

    captured = {}
    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="Sparkasse",
                path=Path("/tmp/Sparkasse"),
                binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
                profile_path=Path("/tmp/profile"),
                homepage_url="https://www.sparkasse-ulm.de",
                allowed_domains=["www.sparkasse-ulm.de"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_refresh_existing_dry_run=lambda **kwargs: [
            "Dry-Run Refresh Existing",
            "",
            "- Sparkasse",
        ],
        execute_refresh_existing_apply=lambda **kwargs: (
            captured.update(kwargs)
            or {
                "command": "python3 builder.py --refresh-existing --apply",
                "returncode": 0,
                "stdout": "Refreshed all",
                "stderr": "",
                "ok": True,
            }
        ),
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_container_list.selection_clear(0, "end")
    frame.secure_browser_buttons["refresh_existing"].kwargs["command"]()

    assert messagebox.calls[-1] == (
        "Alle Launcher/Icons aktualisieren",
        "Alle erkannten Secure-Browser jetzt aktualisieren?",
    )
    assert captured["container_name"] is None
    assert "Sparkasse" in frame.secure_browser_detail_text.text_content


def test_secure_browser_repair_policy_without_selection_updates_all(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    messagebox = DummyMessageBox(result=True)
    monkeypatch.setattr(ui_module, "messagebox", messagebox)

    captured = {}
    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="Netflix",
                path=Path("/tmp/Netflix"),
                binary_path=Path("/tmp/Netflix/firefox/firefox"),
                profile_path=Path("/tmp/Netflix/profile"),
                homepage_url="https://www.netflix.com",
                allowed_domains=["www.netflix.com"],
                icon_path=Path("/tmp/icons"),
                menu_entry_path=None,
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_repair_policy_dry_run=lambda **kwargs: [
            "Dry-Run Repair Policy",
            "",
            "- Netflix",
        ],
        execute_repair_policy_apply=lambda **kwargs: (
            captured.update(kwargs)
            or {
                "command": "python3 builder.py --repair-policy --apply",
                "returncode": 0,
                "stdout": "Repaired all",
                "stderr": "",
                "ok": True,
            }
        ),
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_container_list.selection_clear(0, "end")
    frame.secure_browser_buttons["repair_policy"].kwargs["command"]()

    assert messagebox.calls[-1] == (
        "Policies aller Browser reparieren",
        "Alle erkannten Secure-Browser-Policies jetzt reparieren?",
    )
    assert captured["container_name"] is None
    assert "Netflix" in frame.secure_browser_detail_text.text_content


def test_secure_browser_cleanup_menu_button_executes_cleanup(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    messagebox = DummyMessageBox(result=True)
    monkeypatch.setattr(ui_module, "messagebox", messagebox)

    service = SimpleNamespace(
        scan_containers=lambda: [],
        derive_risk_hints=lambda container: [],
        verify_container=lambda container: [],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_cleanup_menu_dry_run=lambda: [
            "Dry-Run Cleanup Menu",
            "",
            "- netmon-secure-browser-chad.desktop: verwaist",
        ],
        execute_cleanup_menu_apply=lambda: {
            "command": "python3 builder.py --cleanup-menu --apply",
            "returncode": 0,
            "stdout": "Cleanup complete",
            "stderr": "",
            "ok": True,
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    assert "cleanup_menu" in frame.secure_browser_buttons
    frame.secure_browser_buttons["cleanup_menu"].kwargs["command"]()

    assert messagebox.calls[-1] == (
        "Menü bereinigen",
        "Verwaiste oder doppelte Secure-Browser-Menüeinträge jetzt entfernen?",
    )
    assert (
        "keine gefilterten Container"
        in frame.secure_browser_status_badge.configure_kwargs["text"]
    )


def test_secure_browser_uninstall_preview_and_execute(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    scans = [
        [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=None,
                status="vollständig",
            )
        ],
        [],
    ]
    service = SimpleNamespace(
        scan_containers=lambda: scans.pop(0) if scans else [],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_uninstall_dry_run=lambda **kwargs: [
            "Dry-Run Uninstall",
            "",
            "- Container: firefox-GitHub",
        ],
        execute_uninstall_apply=lambda **kwargs: {
            "command": "python3 builder.py --uninstall firefox-GitHub --apply",
            "returncode": 0,
            "stdout": "Uninstalled",
            "stderr": "",
            "ok": True,
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_draft_remove_button.configure_kwargs["command"]()
    assert frame.secure_browser_detail_text.text_content == "Kein Container ausgewählt."
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"]
        == "[Bereit] keine gefilterten Container"
    )


def test_secure_browser_uninstall_execute_uses_preview_target_when_selection_changes(
    monkeypatch,
):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    captured = {}
    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=None,
                status="vollständig",
            )
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
        run_uninstall_dry_run=lambda **kwargs: [
            "Dry-Run Uninstall",
            "",
            "- Container: firefox-GitHub",
        ],
        execute_uninstall_apply=lambda **kwargs: (
            captured.update(kwargs)
            or {
                "command": "python3 builder.py --uninstall firefox-GitHub --apply",
                "returncode": 0,
                "stdout": "Uninstalled",
                "stderr": "",
                "ok": True,
            }
        ),
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_draft_remove_button.configure_kwargs["command"]()

    assert captured["container_name"] == "firefox-GitHub"


def test_secure_browser_uninstall_direct_blocks_without_selection(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox(result=True))

    service = SimpleNamespace(
        scan_containers=lambda: [],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["OK"],
        inspect_launchers=lambda container: {"launcher.desktop": {}, "menu_entry": {}},
        read_container_artifacts=lambda container: {
            "start.sh": "",
            "launcher.desktop": "",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_draft_remove_button.configure_kwargs["command"]()

    assert "Kein Container ausgewählt." in frame.secure_browser_detail_text.text_content
    assert (
        frame.secure_browser_status_badge.configure_kwargs["text"]
        == "[Blockiert] keine Auswahl"
    )


def test_secure_browser_inventory_filter_limits_visible_containers(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            ),
            BrowserContainer(
                name="firefox-OpenAI",
                path=Path("/tmp/firefox-OpenAI"),
                binary_path=Path("/tmp/firefox-OpenAI/firefox/firefox"),
                profile_path=Path("/tmp/firefox-OpenAI/profile"),
                homepage_url="https://chatgpt.com",
                allowed_domains=["chatgpt.com"],
                icon_path=Path("/tmp/firefox-OpenAI/icons"),
                menu_entry_path=None,
                status="Launcher fehlt",
            ),
        ],
        derive_risk_hints=lambda container: (
            ["Externes Mozilla-Profil eingebunden", "Menüeintrag fehlt"]
            if container.name == "firefox-OpenAI"
            else ["Keine offensichtlichen Risiken erkannt"]
        ),
        verify_container=lambda container: ["Firefox-Binary: OK"],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": (
                    str(container.menu_entry_path)
                    if container.menu_entry_path
                    else "nicht registriert"
                ),
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh",
            "launcher.desktop": "[Desktop Entry]",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()

    assert frame.secure_browser_container_list.items == [
        "firefox-GitHub",
        "firefox-OpenAI",
    ]
    assert (
        "2 Secure-Browser-Container erkannt."
        in frame.secure_browser_summary_text.text_content
    )
    assert (
        "Kennzahlen: Gesamt: 2 | Launcher fehlt: 1 | vollständig: 1 | externe Profile: 1 | fehlende Launcher: 0 | fehlende Menüeinträge: 1"
        in frame.secure_browser_summary_text.text_content
    )


def test_secure_browser_inventory_keeps_all_visible_without_status_filter(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )
    monkeypatch.setattr(ui_module, "messagebox", DummyMessageBox())

    service = SimpleNamespace(
        scan_containers=lambda: [
            BrowserContainer(
                name="firefox-GitHub",
                path=Path("/tmp/firefox-GitHub"),
                binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                profile_path=Path("/tmp/firefox-GitHub/profile"),
                homepage_url="https://github.com",
                allowed_domains=["github.com"],
                icon_path=Path("/tmp/firefox-GitHub/icons"),
                menu_entry_path=Path("/tmp/menu.desktop"),
                status="vollständig",
            ),
            BrowserContainer(
                name="Sparkasse",
                path=Path("/tmp/Sparkasse"),
                binary_path=Path("/tmp/Sparkasse/firefox/firefox"),
                profile_path=Path("/tmp/Sparkasse/profile"),
                homepage_url="https://www.sparkasse-ulm.de",
                allowed_domains=["www.sparkasse-ulm.de"],
                icon_path=Path("/tmp/Sparkasse/icons"),
                menu_entry_path=Path("/tmp/sparkasse.desktop"),
                status="Profil extern",
            ),
        ],
        derive_risk_hints=lambda container: ["Keine offensichtlichen Risiken erkannt"],
        verify_container=lambda container: ["Firefox-Binary: OK"],
        inspect_launchers=lambda container: {
            "launcher.desktop": {
                "Type": "Application",
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "StartupNotify": "true",
            },
            "menu_entry": {
                "Pfad": str(container.menu_entry_path),
                "Name": container.name,
                "Exec": "/tmp/start.sh",
                "Icon": "/tmp/icon.png",
                "Categories": "Network;Security;",
                "Type": "Application",
            },
        },
        read_container_artifacts=lambda container: {
            "start.sh": "#!/bin/sh",
            "launcher.desktop": "[Desktop Entry]",
        },
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    assert frame.secure_browser_container_list.items == ["firefox-GitHub", "Sparkasse"]

    frame.secure_browser_buttons["inventory"].kwargs["command"]()

    assert frame.secure_browser_container_list.items == ["firefox-GitHub", "Sparkasse"]


def test_secure_browser_inventory_handles_scan_errors(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    service = SimpleNamespace(
        scan_containers=lambda: (_ for _ in ()).throw(
            FileNotFoundError("builder fehlt")
        )
    )
    manager = SecureBrowserManager(service=service)
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()

    assert frame.secure_browser_container_list.items == []
    assert "Inventur fehlgeschlagen." in frame.secure_browser_summary_text.text_content
    assert "builder fehlt" in frame.secure_browser_detail_text.text_content


def test_secure_browser_selection_handles_verification_errors(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    class FailingVerifyService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-GitHub",
                    path=Path("/tmp/firefox-GitHub"),
                    binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-GitHub/profile"),
                    homepage_url="https://github.com",
                    allowed_domains=["github.com"],
                    icon_path=Path("/tmp/firefox-GitHub/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def verify_container(self, container):
            raise RuntimeError("verify kaputt")

        def inspect_launchers(self, container):
            return {
                "launcher.desktop": {},
                "menu_entry": {},
            }

        def read_container_artifacts(self, container):
            return {
                "start.sh": "irrelevant",
                "launcher.desktop": "irrelevant",
            }

    manager = SecureBrowserManager(service=FailingVerifyService())
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()

    assert (
        "Fehler bei Verifikation: verify kaputt"
        in frame.secure_browser_detail_text.text_content
    )


def test_secure_browser_launcher_button_handles_inspection_errors(monkeypatch):
    import netmon.modules.secure_browser.ui as ui_module

    monkeypatch.setattr(
        ui_module,
        "ttk",
        type(
            "DummyTtk",
            (),
            {
                "Frame": DummyWidget,
                "Label": DummyWidget,
                "Button": DummyButton,
                "Combobox": DummyCombobox,
                "Entry": DummyEntry,
            },
        )(),
    )
    monkeypatch.setattr(
        ui_module,
        "tk",
        type(
            "DummyTk",
            (),
            {
                "Text": DummyWidget,
                "Listbox": DummyListbox,
                "END": "end",
            },
        )(),
    )

    class FailingLauncherService:
        def scan_containers(self):
            return [
                BrowserContainer(
                    name="firefox-GitHub",
                    path=Path("/tmp/firefox-GitHub"),
                    binary_path=Path("/tmp/firefox-GitHub/firefox/firefox"),
                    profile_path=Path("/tmp/firefox-GitHub/profile"),
                    homepage_url="https://github.com",
                    allowed_domains=["github.com"],
                    icon_path=Path("/tmp/firefox-GitHub/icons"),
                    menu_entry_path=Path("/tmp/menu.desktop"),
                    status="vollständig",
                )
            ]

        def verify_container(self, container):
            return ["Firefox-Binary: OK"]

        def inspect_launchers(self, container):
            raise RuntimeError("launcher kaputt")

        def read_container_artifacts(self, container):
            return {
                "start.sh": "irrelevant",
                "launcher.desktop": "irrelevant",
            }

    manager = SecureBrowserManager(service=FailingLauncherService())
    frame = create_secure_browser_tab(DummyWidget(), manager)

    frame.secure_browser_buttons["inventory"].kwargs["command"]()
    frame.secure_browser_buttons["inspect_launcher"].kwargs["command"]()

    assert (
        "Fehler bei Launcher-Prüfung: launcher kaputt"
        in frame.secure_browser_detail_text.text_content
    )
