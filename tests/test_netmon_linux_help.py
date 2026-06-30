import inspect

from netmon.features import linux_help_controller
from tools import netmon


def test_linux_help_get_risk_level_classifies_commands():
    app = netmon.App.__new__(netmon.App)

    assert app.linux_help_get_risk_level("ls -la") == "safe"
    assert app.linux_help_get_risk_level("systemctl status ssh") == "caution"
    assert app.linux_help_get_risk_level("rm -rf /tmp/test") == "danger"


def test_normalize_linux_help_entry_adds_defaults_and_id():
    app = netmon.App.__new__(netmon.App)

    item = app.normalize_linux_help_entry(
        {
            "category": "Dateien",
            "name": "ls",
            "info": "Dateien zeigen",
            "cmd": "ls -la",
        }
    )

    assert item["id"] == "ls"
    assert item["risk"] == "safe"
    assert item["explanation"] == "Dateien zeigen"
    assert item["warning_text"] == ""
    assert item["enabled"] is True


def test_import_linux_help_csv_reads_csv_and_groups_categories(tmp_path):
    csv_path = tmp_path / "linux-befehle.csv"
    csv_path.write_text(
        "\ufeffcategory,name,info,cmd\n"
        "Dateien,ls,Dateien zeigen,ls -la\n"
        "System,systemctl status,Dienststatus anzeigen,systemctl status ssh\n"
        "Dateien,rm,Datei löschen,rm DATEI\n"
        "\n",
        encoding="utf-8",
    )

    app = netmon.App.__new__(netmon.App)
    app.linux_help_data = []
    app.linux_help_commands = []
    app.linux_help_categories = []
    app.linux_help_commands_by_category = {}

    commands = app.import_linux_help_csv(str(csv_path))

    assert [item["name"] for item in commands] == ["ls", "rm", "systemctl status"]
    assert app.linux_help_categories == ["Dateien", "System"]
    assert [
        item["name"] for item in app.linux_help_commands_by_category["Dateien"]
    ] == [
        "ls",
        "rm",
    ]
    assert app.linux_help_commands_by_category["System"][0]["risk"] == "caution"
    assert app.linux_help_commands_by_category["Dateien"][0]["id"] == "ls"


def test_load_linux_help_data_prefers_json_over_csv(tmp_path):
    json_path = tmp_path / "linux_help_commands.json"
    csv_path = tmp_path / "linux-befehle.csv"
    json_path.write_text(
        '[{"id":"custom_df","category":"System","name":"df","info":"Disk","cmd":"df -h","risk":"safe","explanation":"Disk info","warning_text":"","enabled":true}]',
        encoding="utf-8",
    )
    csv_path.write_text(
        "category,name,info,cmd\nDateien,ls,Dateien zeigen,ls -la\n",
        encoding="utf-8",
    )

    app = netmon.App.__new__(netmon.App)
    app.linux_help_data_path = str(json_path)
    app._linux_help_csv_candidates = lambda: [str(csv_path)]
    app.linux_help_data = []
    app.linux_help_commands = []
    app.linux_help_categories = []
    app.linux_help_commands_by_category = {}
    app.linux_help_glossary_path = str(tmp_path / "missing_glossary.json")
    app.linux_help_glossary = []
    app.linux_help_glossary_by_category = {}
    app.linux_help_combined_categories = []
    app.linux_help_visible_commands = []
    app.linux_help_visible_command_ids = []
    app.linux_help_selected_id = ""
    app.linux_help_dirty = False

    commands = app.load_linux_help_data()

    assert len(commands) == 1
    assert commands[0]["id"] == "custom_df"
    assert commands[0]["name"] == "df"
    assert app.linux_help_categories == ["System"]


def test_load_linux_help_glossary_normalizes_entries(tmp_path):
    glossary_path = tmp_path / "it_lexikon_linux_hilfe.json"
    glossary_path.write_text(
        '{"entries":[{"id":"it_1","term":"Algorithm","short":"Definition","example":"Sort list","tags":["grundlagen"],"related":["Variable"]}]}',
        encoding="utf-8",
    )

    app = netmon.App.__new__(netmon.App)
    app.linux_help_data = []
    app.linux_help_categories = ["System"]
    app.linux_help_glossary_path = str(glossary_path)
    app.linux_help_glossary = []
    app.linux_help_glossary_by_category = {}
    app.linux_help_combined_categories = []

    glossary = linux_help_controller.load_linux_help_glossary(app)

    assert len(glossary) == 1
    assert glossary[0]["entry_type"] == "glossary"
    assert glossary[0]["name"] == "Algorithm"
    assert glossary[0]["category"] == "Grundlagen"
    assert glossary[0]["related"] == "Variable"
    assert "Grundlagen" in app.linux_help_combined_categories


def test_save_and_reload_linux_help_glossary_roundtrip(tmp_path):
    glossary_path = tmp_path / "linux_help_glossary.json"

    app = netmon.App.__new__(netmon.App)
    app.linux_help_glossary_path = str(glossary_path)
    app.linux_help_glossary = [
        {
            "id": "algo",
            "entry_type": "glossary",
            "category": "Basics",
            "name": "Algorithm",
            "info": "Definition",
            "example": "Sort list",
            "tags": "grundlagen, coding",
            "related": "Variable, Function",
            "explanation": "Longer explanation",
            "warning_text": "Note text",
            "enabled": True,
        }
    ]

    assert linux_help_controller.save_linux_help_glossary(app, update_status=False)

    reloaded = netmon.App.__new__(netmon.App)
    reloaded.linux_help_data = []
    reloaded.linux_help_categories = []
    reloaded.linux_help_glossary_path = str(glossary_path)
    reloaded.linux_help_glossary_seed_path = ""
    reloaded.linux_help_glossary = []
    reloaded.linux_help_glossary_by_category = {}
    reloaded.linux_help_combined_categories = []

    glossary = linux_help_controller.load_linux_help_glossary(reloaded)

    assert glossary[0]["category"] == "Basics"
    assert glossary[0]["explanation"] == "Longer explanation"
    assert glossary[0]["warning_text"] == "Note text"
    assert glossary[0]["related"] == "Variable, Function"


def test_get_linux_help_commands_for_category_supports_glossary_mode():
    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = netmon.App.__new__(netmon.App)
    app.tr = lambda _key, default: default
    app.linux_help_source_var = DummyVar("Glossary")
    app.linux_help_commands = [
        {"id": "ls", "category": "Files", "name": "ls", "entry_type": "command"}
    ]
    app.linux_help_commands_by_category = {"Files": list(app.linux_help_commands)}
    app.linux_help_glossary = [
        {
            "id": "algo",
            "category": "Basics",
            "name": "Algorithm",
            "entry_type": "glossary",
        }
    ]
    app.linux_help_glossary_by_category = {"Basics": list(app.linux_help_glossary)}

    items = app.get_linux_help_commands_for_category("Basics")

    assert [item["id"] for item in items] == ["algo"]


def test_app_init_sets_netmon_config_dir_before_linux_help_data_path():
    init_source = inspect.getsource(netmon.App.__init__)

    config_idx = init_source.index("self.netmon_config_dir = get_netmon_config_dir()")
    linux_help_path_idx = init_source.index("self.linux_help_data_path = os.path.join(")

    assert config_idx < linux_help_path_idx


def test_validate_linux_help_command_for_terminal_rejects_multiline():
    app = netmon.App.__new__(netmon.App)

    ok, reason = app._validate_linux_help_command_for_terminal("ls -la\npwd")

    assert ok is False
    assert "Mehrzeilige" in reason


def test_send_linux_help_command_to_terminal_sends_safe_selected_command():
    class DummyText:
        def __init__(self):
            self.value = ""

        def delete(self, *_args):
            self.value = ""

        def insert(self, *_args):
            self.value += _args[-1]

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = "ls"
    app.linux_help_status_var = DummyVar("")
    app.linux_help_text = DummyText()
    app.log_messages = []
    app.log = app.log_messages.append
    app.get_linux_help_command_by_id = lambda _id: {
        "id": "ls",
        "name": "ls",
        "category": "Dateien",
        "cmd": "ls -la",
        "risk": "safe",
        "enabled": True,
    }
    app._open_command_in_external_terminal = lambda cmd: "xterm"

    assert app.send_linux_help_command_to_terminal() is True
    assert "external terminal" in app.linux_help_status_var.get()
    assert "Terminal: xterm" in app.linux_help_text.value
    assert any(
        "Linux help: command sent to terminal" in msg for msg in app.log_messages
    )


def test_selected_linux_help_id_prefers_tree_selection():
    class DummyTree:
        def selection(self):
            return ("ls",)

    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = ""
    app.linux_help_tree = DummyTree()

    assert linux_help_controller._selected_linux_help_id(app) == "ls"


def test_resolve_linux_help_item_prefers_app_resolver():
    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = "custom"
    app.get_linux_help_command_by_id = lambda command_id: {
        "id": command_id,
        "name": "custom",
    }

    item = linux_help_controller._resolve_linux_help_item(app)

    assert item == {"id": "custom", "name": "custom"}


def test_send_linux_help_to_chad_uses_direct_prompt_setter():
    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = "ls"
    app.linux_help_status_var = DummyVar("")
    app.tr = lambda _key, default: default
    app.get_linux_help_command_by_id = lambda command_id: {
        "id": command_id,
        "name": "ls",
        "category": "Dateien",
        "cmd": "ls -la",
        "info": "Dateien zeigen",
        "syntax": "ls -la",
        "example": "ls -la",
        "risk": "safe",
        "root_required": False,
        "tags": "",
        "explanation": "Dateien zeigen",
        "warning_text": "",
    }
    calls = []
    app.set_chad_direct_prompt = lambda title, prompt: calls.append((title, prompt))

    assert app.send_linux_help_to_chad() is True
    assert calls
    assert calls[0][0] == "Explain Linux command: ls"
    assert "Command data from NetMon:" in calls[0][1]


def test_linux_help_chad_title_prefers_name_then_command():
    assert (
        linux_help_controller._linux_help_chad_title({"name": "ls", "cmd": "ls -la"})
        == "Explain Linux command: ls"
    )
    assert (
        linux_help_controller._linux_help_chad_title({"cmd": "ls -la"})
        == "Explain Linux command: ls -la"
    )
    assert (
        linux_help_controller._linux_help_chad_title(
            {"name": "Algorithm", "entry_type": "glossary"}
        )
        == "Explain glossary term: Algorithm"
    )


def test_selected_linux_help_chad_payload_returns_prompt_and_title():
    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = "ls"
    app.get_linux_help_command_by_id = lambda command_id: {
        "id": command_id,
        "name": "ls",
        "category": "Dateien",
        "cmd": "ls -la",
        "info": "Dateien zeigen",
        "syntax": "ls -la",
        "example": "ls -la",
        "risk": "safe",
        "root_required": False,
        "tags": "",
        "explanation": "Dateien zeigen",
        "warning_text": "",
    }
    app.tr = lambda _key, default=None: default

    item, title, prompt = linux_help_controller._selected_linux_help_chad_payload(app)

    assert item["id"] == "ls"
    assert title == "Explain Linux command: ls"
    assert "Command data from NetMon:" in prompt


def test_selected_linux_help_chad_payload_returns_empty_when_nothing_selected():
    app = netmon.App.__new__(netmon.App)
    app.linux_help_selected_id = ""

    assert linux_help_controller._selected_linux_help_chad_payload(app) == (
        None,
        "",
        "",
    )
