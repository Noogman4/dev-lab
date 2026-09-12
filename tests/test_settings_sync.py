from types import SimpleNamespace

from netmon.ui.settings_sync import app_var_value, sync_app_vars_from_mapping


class DummyVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class BrokenVar:
    def get(self):
        raise RuntimeError("cannot read")

    def set(self, _value):
        raise RuntimeError("cannot write")


def test_app_var_value_returns_default_for_missing_or_broken_vars():
    app = SimpleNamespace(present=DummyVar("configured"), broken=BrokenVar())

    assert app_var_value(app, "present", "fallback") == "configured"
    assert app_var_value(app, "missing", "fallback") == "fallback"
    assert app_var_value(app, "broken", "fallback") == "fallback"


def test_sync_app_vars_from_mapping_updates_existing_vars_only():
    app = SimpleNamespace(first=DummyVar("old"), broken=BrokenVar())

    sync_app_vars_from_mapping(
        app,
        {
            "first": "new",
            "missing": "ignored",
            "broken": "ignored",
        },
    )

    assert app.first.get() == "new"
