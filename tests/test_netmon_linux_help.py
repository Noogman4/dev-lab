import inspect
import os

from netmon.features import linux_help_controller
from netmon.services import linux_help_document_service
from netmon.services import linux_help_library_service
from netmon.services import linux_help_prompt_service
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
    app = netmon.App.__new__(netmon.App)
    app.tr = lambda _key, default: default

    assert (
        linux_help_controller._linux_help_chad_title(
            app, {"name": "ls", "cmd": "ls -la"}
        )
        == "Explain Linux command: ls"
    )
    assert (
        linux_help_controller._linux_help_chad_title(app, {"cmd": "ls -la"})
        == "Explain Linux command: ls -la"
    )
    assert (
        linux_help_controller._linux_help_chad_title(
            app,
            {"name": "Algorithm", "entry_type": "glossary"}
        )
        == "Explain glossary term: Algorithm"
    )


def test_build_linux_help_chad_prompt_uses_translated_german_labels():
    app = netmon.App.__new__(netmon.App)
    translations = {
        "linux_help_prompt_command_intro": "Bitte erkläre den folgenden Linux-Befehl für Einsteiger in klarem, gut strukturiertem Deutsch.",
        "linux_help_prompt_command_data_header": "Befehlsdaten aus NetMon:",
        "linux_help_prompt_command_name": "Befehlsname: {value}",
        "linux_help_prompt_category": "Kategorie: {value}",
        "linux_help_prompt_command": "Befehl: {value}",
        "linux_help_prompt_short_description": "Kurzbeschreibung: {value}",
        "linux_help_prompt_syntax": "Syntax: {value}",
        "linux_help_prompt_example": "Beispiel: {value}",
        "linux_help_prompt_database_explanation": "Datenbank-Erklärung/Hinweis: {value}",
        "linux_help_prompt_additional_warning": "Zusätzliche Warnung: {value}",
        "linux_help_prompt_root_required": "Root erforderlich: {value}",
        "linux_help_prompt_risk_level": "Risikostufe: {value}",
        "linux_help_prompt_tags": "Tags: {value}",
        "linux_help_prompt_requirements": "Wichtige Anforderungen an deine Antwort:",
        "linux_help_prompt_command_req_1": "- Schreibe einsteigerfreundlich und setze kein Vorwissen voraus.",
        "linux_help_prompt_command_req_2": "- Beginne mit einer kurzen Erklärung, wofür der Befehl verwendet wird.",
        "linux_help_prompt_command_req_3": "- Zerlege dann die Syntax und die wichtigsten Bestandteile.",
        "linux_help_prompt_command_req_4": "- Erkläre das Beispiel Schritt für Schritt.",
        "linux_help_prompt_command_req_5": "- Nenne typische praktische Einsatzfälle.",
        "linux_help_prompt_command_req_6": "- Weise klar auf Risiken, Root-Bedarf und häufige Fehler hin.",
        "linux_help_prompt_command_req_7": "- Beende die Antwort mit 3 sicheren Tipps oder Varianten für Einsteiger.",
        "linux_help_prompt_command_req_8": "- Verwende ruhige, klare Sprache statt unnötigem Fachjargon.",
        "linux_help_prompt_no_additional_warning": "Keine zusätzliche Warnung gespeichert.",
    }
    app.tr = lambda key, default: translations.get(key, default)

    prompt = linux_help_controller.build_linux_help_chad_prompt(
        app,
        {
            "name": "ls",
            "category": "Dateien",
            "cmd": "ls -la",
            "info": "Dateien anzeigen",
            "syntax": "ls [OPTIONEN] [DATEI]",
            "example": "ls -la",
            "risk": "safe",
            "root_required": False,
            "tags": "bash",
            "explanation": "Zeigt Dateien an.",
            "warning_text": "",
        },
    )

    assert "Bitte erkläre den folgenden Linux-Befehl" in prompt
    assert "Befehlsdaten aus NetMon:" in prompt
    assert "Befehlsname: ls" in prompt
    assert "Root erforderlich: No" in prompt


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


def test_build_linux_help_pdf_prompt_contains_command_context():
    prompt = linux_help_prompt_service.build_linux_help_pdf_prompt(
        {
            "name": "unlzma",
            "cmd": "unlzma -k archiv.tar.lzma",
            "category": "Archive",
            "info": "LZMA-Dateien entpacken",
            "syntax": "unlzma [OPTIONEN] [DATEI]",
            "example": "unlzma --help",
            "explanation": "Entpackt .lzma-Dateien.",
            "warning_text": "Dateiname vorher pruefen.",
            "risk": "safe",
            "root_required": False,
            "tags": "archive,compression",
        }
    )

    assert "unlzma" in prompt
    assert "unlzma [OPTIONEN] [DATEI]" in prompt
    assert "LZMA-Dateien entpacken" in prompt
    assert "Risikostufe: 🟢 Sicher" in prompt


def test_linux_help_document_bundle_writes_pdf_and_metadata(tmp_path, monkeypatch):
    target_root = tmp_path / "Documents"

    def fake_documents_subdir(*parts):
        path = target_root.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(
        linux_help_library_service,
        "get_netmon_documents_subdir",
        fake_documents_subdir,
    )

    document = linux_help_document_service.build_linux_help_document(
        {
            "name": "unlzma",
            "cmd": "unlzma -k archiv.tar.lzma",
            "category": "Archive",
            "info": "LZMA-Dateien entpacken",
            "syntax": "unlzma [OPTIONEN] [DATEI]",
            "example": "unlzma --help",
            "explanation": "Entpackt die Datei und behaelt das Original.",
            "warning_text": "Speicherplatz vorher pruefen.",
            "risk": "safe",
            "root_required": False,
            "tags": "archive,compression",
        },
        source_prompt="Beispiel-Prompt",
    )

    metadata = linux_help_library_service.create_linux_help_document_bundle(document)

    assert metadata["id"].startswith("unlzma_")
    assert os.path.isfile(metadata["pdf_path"])
    assert os.path.isfile(metadata["json_path"])
    assert metadata["source_prompt"] == "Beispiel-Prompt"
    assert metadata["summary"] == "LZMA-Dateien entpacken"


def test_import_linux_help_pdf_creates_library_entry(tmp_path, monkeypatch):
    source_pdf = tmp_path / "hilfe.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
    target_root = tmp_path / "Documents"

    def fake_documents_subdir(*parts):
        path = target_root.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(
        linux_help_library_service,
        "get_netmon_documents_subdir",
        fake_documents_subdir,
    )

    metadata = linux_help_library_service.import_linux_help_pdf(str(source_pdf))

    assert metadata["generator"] == "import"
    assert os.path.isfile(metadata["pdf_path"])
    assert os.path.isfile(metadata["json_path"])
    assert "Importierte Linux-Hilfe-PDF" in metadata["preview_text"]


def test_delete_linux_help_document_removes_pdf_and_metadata(tmp_path, monkeypatch):
    target_root = tmp_path / "Documents"

    def fake_documents_subdir(*parts):
        path = target_root.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(
        linux_help_library_service,
        "get_netmon_documents_subdir",
        fake_documents_subdir,
    )

    document = linux_help_document_service.build_linux_help_document(
        {
            "name": "ls",
            "cmd": "ls -la",
            "category": "Dateien",
            "info": "Dateien anzeigen",
            "syntax": "ls [OPTIONEN]",
            "example": "ls -la",
            "risk": "safe",
        }
    )
    metadata = linux_help_library_service.create_linux_help_document_bundle(document)

    result = linux_help_library_service.delete_linux_help_document(metadata["id"])

    assert result["id"] == metadata["id"]
    assert metadata["pdf_path"] in result["deleted"]
    assert metadata["json_path"] in result["deleted"]
    assert not os.path.exists(metadata["pdf_path"])
    assert not os.path.exists(metadata["json_path"])
    assert linux_help_library_service.get_linux_help_document_by_id(metadata["id"]) is None
