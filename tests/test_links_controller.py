import json

from netmon.config.constants import LINK_SLOT_COUNT
from netmon.features import links_controller


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyLinkTable:
    def __init__(self, values_by_row, selection=()):
        self.values_by_row = dict(values_by_row)
        self._selection = tuple(selection)

    def selection(self):
        return self._selection

    def item(self, row_id, option=None):
        values = self.values_by_row[row_id]
        if option == "values":
            return values
        return {"values": values}


def test_default_link_slots_contains_twenty_slots():
    slots = links_controller.default_link_slots()

    assert LINK_SLOT_COUNT == 20
    assert len(slots) == 20
    assert [slot["slot"] for slot in slots] == list(range(1, 21))


def test_load_link_slots_config_extends_legacy_fifteen_slot_config(tmp_path):
    config_path = tmp_path / "netmon_link_slots.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "slot": slot_no,
                    "custom_name": f"Legacy {slot_no}",
                    "link_type": "Externer Link",
                    "target": f"https://example.com/{slot_no}",
                }
                for slot_no in range(1, 16)
            ]
        ),
        encoding="utf-8",
    )
    app = type("DummyApp", (), {})()
    app.link_config_path = str(config_path)
    app.log = lambda _message: None

    slots = links_controller.load_link_slots_config(app)

    assert len(slots) == 20
    assert slots[14]["custom_name"] == "Legacy 15"
    assert slots[15]["slot"] == 16
    assert slots[15]["target"] == ""
    assert slots[19]["slot"] == 20


def test_build_systemlink_target_uses_selected_desktop_entry():
    app = type("DummyApp", (), {})()
    app.link_type_var = DummyVar("Systemlink")
    app.link_system_app_var = DummyVar("Visual Studio Code")
    app.desktop_app_by_label = {
        "Visual Studio Code": {
            "name": "Visual Studio Code",
            "desktop_id": "code.desktop",
            "desktop_file": "/usr/share/applications/code.desktop",
        }
    }

    target, app_name, desktop_id, desktop_file = (
        links_controller.build_systemlink_target(app)
    )

    assert target == "desktop:code.desktop"
    assert app_name == "Visual Studio Code"
    assert desktop_id == "code.desktop"
    assert desktop_file == "/usr/share/applications/code.desktop"


def test_build_form_link_slot_uses_selected_systemlink_data():
    app = type("DummyApp", (), {})()
    app.link_slot_choice = DummyVar("2")
    app.link_custom_name_var = DummyVar("Editor")
    app.link_type_var = DummyVar("Systemlink")
    app.link_target_var = DummyVar("")
    app.link_system_app_var = DummyVar("Visual Studio Code")
    app.desktop_app_by_label = {
        "Visual Studio Code": {
            "name": "Visual Studio Code",
            "desktop_id": "code.desktop",
            "desktop_file": "/usr/share/applications/code.desktop",
        }
    }

    slot = links_controller.build_form_link_slot(app)

    assert slot == {
        "slot": 2,
        "custom_name": "Editor",
        "link_type": "Systemlink",
        "target": "desktop:code.desktop",
        "app_name": "Visual Studio Code",
        "desktop_id": "code.desktop",
        "desktop_file": "/usr/share/applications/code.desktop",
    }


def test_link_target_fields_normalizes_external_link_target():
    app = type("DummyApp", (), {})()
    app.link_type_var = DummyVar("Externer Link")
    app.link_target_var = DummyVar("example.com")

    target, app_name, desktop_id, desktop_file = links_controller._link_target_fields(
        app
    )

    assert target == "https://example.com"
    assert app_name == ""
    assert desktop_id == ""
    assert desktop_file == ""


def test_link_custom_name_returns_trimmed_form_value():
    app = type("DummyApp", (), {})()
    app.link_custom_name_var = DummyVar("  Work Link  ")

    assert links_controller._link_custom_name(app) == "Work Link"


def test_link_slot_at_returns_slot_or_none():
    app = type("DummyApp", (), {})()
    app.link_slots = [{"slot": 1}, {"slot": 2}]

    assert links_controller._link_slot_at(app, 2) == {"slot": 2}
    assert links_controller._link_slot_at(app, 3) is None


def test_link_slot_has_assignment_checks_relevant_fields():
    assert links_controller._link_slot_has_assignment({}) is False
    assert (
        links_controller._link_slot_has_assignment(
            {"custom_name": "", "link_type": "", "target": "https://example.com"}
        )
        is True
    )


def test_systemlink_form_label_prefers_loaded_desktop_label():
    app = type("DummyApp", (), {})()
    app.desktop_app_by_id = {
        "code.desktop": {
            "label": "Visual Studio Code",
        }
    }

    assert (
        links_controller._systemlink_form_label(
            app,
            {
                "desktop_id": "code.desktop",
                "app_name": "Code",
            },
        )
        == "Visual Studio Code"
    )


def test_load_link_slot_into_form_uses_systemlink_label():
    app = type("DummyApp", (), {})()
    app.link_slots = [
        {
            "slot": 1,
            "custom_name": "Editor",
            "link_type": "Systemlink",
            "target": "desktop:code.desktop",
            "app_name": "Code",
            "desktop_id": "code.desktop",
            "desktop_file": "/usr/share/applications/code.desktop",
        }
    ]
    app.desktop_app_by_id = {
        "code.desktop": {
            "label": "Visual Studio Code",
        }
    }
    app.link_slot_choice = DummyVar("")
    app.link_custom_name_var = DummyVar("")
    app.link_type_var = DummyVar("")
    app.link_target_var = DummyVar("")
    app.link_system_app_var = DummyVar("")

    links_controller.load_link_slot_into_form(app, 1)

    assert app.link_slot_choice.get() == "1"
    assert app.link_custom_name_var.get() == "Editor"
    assert app.link_system_app_var.get() == "Visual Studio Code"


def test_on_systemlink_app_select_autofills_display_name():
    app = type("DummyApp", (), {})()
    app.link_system_app_var = DummyVar("Visual Studio Code")
    app.link_target_var = DummyVar("")
    app.link_custom_name_var = DummyVar("")
    app.desktop_app_by_label = {
        "Visual Studio Code": {
            "name": "Visual Studio Code",
            "label": "Visual Studio Code",
            "desktop_id": "code.desktop",
        }
    }

    links_controller.on_systemlink_app_select(app)

    assert app.link_target_var.get() == "desktop:code.desktop"
    assert app.link_custom_name_var.get() == "Visual Studio Code"


def test_on_systemlink_app_select_keeps_manual_display_name():
    app = type("DummyApp", (), {})()
    app.link_system_app_var = DummyVar("Visual Studio Code")
    app.link_target_var = DummyVar("")
    app.link_custom_name_var = DummyVar("Mein Editor")
    app.link_custom_name_autofill = "Alter Auto-Name"
    app.desktop_app_by_label = {
        "Visual Studio Code": {
            "name": "Visual Studio Code",
            "label": "Visual Studio Code",
            "desktop_id": "code.desktop",
        }
    }

    links_controller.on_systemlink_app_select(app)

    assert app.link_target_var.get() == "desktop:code.desktop"
    assert app.link_custom_name_var.get() == "Mein Editor"


def test_remove_link_table_selection_uses_selected_slot():
    app = type("DummyApp", (), {})()
    app.link_table = DummyLinkTable({"link-slot-7": ("7", "Docs", "Systemlink", "x")}, selection=("link-slot-7",))
    app.link_slot_choice = DummyVar("1")
    logs = []
    app.log = logs.append

    captured = {}

    def fake_clear_link_slot(target_app, confirm=False):
        captured["slot_choice"] = target_app.link_slot_choice.get()
        captured["confirm"] = confirm

    original = links_controller.clear_link_slot
    links_controller.clear_link_slot = fake_clear_link_slot
    try:
        links_controller.remove_link_table_selection(app)
    finally:
        links_controller.clear_link_slot = original

    assert captured == {"slot_choice": "7", "confirm": True}
    assert logs == []
