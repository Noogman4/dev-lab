from netmon.features import links_controller


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


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
