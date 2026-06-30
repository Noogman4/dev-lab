import inspect

from netmon.app import App


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_set_path_guard_light_maps_states_to_colors_and_text():
    app = App.__new__(App)
    colors = []
    app.l_path_guard = ("canvas", "dot", "label")
    app.path_guard_status_var = DummyVar("")
    app.set_light = lambda light, color: colors.append((light, color))

    app.set_path_guard_light("ok")
    app.set_path_guard_light("warning")
    app.set_path_guard_light("error")
    app.set_path_guard_light("unknown")

    assert colors == [
        (app.l_path_guard, "green"),
        (app.l_path_guard, "yellow"),
        (app.l_path_guard, "red"),
        (app.l_path_guard, "gray"),
    ]
    assert app.path_guard_status_var.get() == "PATH Guard: noch nicht geprüft"


def test_run_path_guard_check_sets_ampel_for_risk_levels():
    app = App.__new__(App)
    app.path_guard_last_result = None
    app.path_guard_service = type(
        "DummyService",
        (),
        {"run_check": lambda self: {"risk": "hoch", "counts": {}, "path_entries": []}},
    )()
    app.format_path_guard_result = lambda result: "PATH Guard"
    app.security_detail = type(
        "DummyText",
        (),
        {
            "configure": lambda self, **kwargs: None,
            "index": lambda self, _arg: "1.0",
            "insert": lambda self, *_args: None,
            "see": lambda self, *_args: None,
        },
    )()
    calls = []
    app.set_path_guard_light = lambda state, message="": calls.append((state, message))
    app.log = lambda _message: None

    app.run_path_guard_check()

    assert calls[0] == ("error", "PATH Guard: Risiko hoch")


def test_path_guard_ui_source_contains_ampel_and_status_label():
    init_source = inspect.getsource(App.__init__)
    path_guard_source = inspect.getsource(App.run_path_guard_check)

    assert 'self.l_path_guard = self.make_light(amp_extra, "PATH Guard")' in init_source
    assert "textvariable=self.path_guard_status_var" in init_source
    assert (
        'self.set_path_guard_light("warning", "PATH Guard: Risiko mittel")'
        in path_guard_source
    )
