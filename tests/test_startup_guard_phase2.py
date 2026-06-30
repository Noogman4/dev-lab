from netmon.app import App
from netmon.services.ai_analysis_service import AiAnalysisService


class DummyTree:
    def __init__(self):
        self.items = []
        self.selected = ()

    def delete(self, *items):
        if not items:
            return
        if items == tuple(self.get_children()):
            self.items = []
            self.selected = ()
            return
        ids = set(items)
        self.items = [item for item in self.items if item["iid"] not in ids]

    def get_children(self):
        return tuple(item["iid"] for item in self.items)

    def insert(self, parent, index, values=()):
        iid = f"item{len(self.items)}"
        self.items.append({"iid": iid, "values": values})
        return iid

    def selection(self):
        return self.selected

    def index(self, iid):
        for idx, item in enumerate(self.items):
            if item["iid"] == iid:
                return idx
        return -1


def test_show_startup_guard_result_populates_tree_and_visible_entries():
    app = App.__new__(App)
    outputs = []

    app.startup_guard_tree = DummyTree()
    app.startup_guard_visible_entries = []
    app.startup_guard_selected_entry = None
    app.update_startup_guard_output = lambda text, append=False: outputs.append(text)

    result = {
        "new": [
            {
                "source": "user_autostart",
                "name": "new.desktop",
                "path": "/tmp/new.desktop",
                "sha256": "abc",
                "mtime": 1,
                "size": 10,
            }
        ],
        "changed": [
            {
                "before": {
                    "source": "systemd_user",
                    "name": "changed.service",
                    "path": "/tmp/changed.service",
                    "sha256": "old",
                    "mtime": 2,
                    "size": 20,
                },
                "after": {
                    "source": "systemd_user",
                    "name": "changed.service",
                    "path": "/tmp/changed.service",
                    "sha256": "new",
                    "mtime": 3,
                    "size": 22,
                },
            }
        ],
        "removed": [
            {
                "source": "system_autostart",
                "name": "removed.desktop",
                "path": "/tmp/removed.desktop",
                "sha256": "gone",
                "mtime": 4,
                "size": 30,
            }
        ],
        "trusted": [
            {
                "source": "user_autostart",
                "name": "trusted.desktop",
                "path": "/tmp/trusted.desktop",
                "sha256": "trusted",
                "mtime": 6,
                "size": 50,
            }
        ],
        "unchanged": [
            {
                "source": "user_autostart",
                "name": "same.desktop",
                "path": "/tmp/same.desktop",
                "sha256": "same",
                "mtime": 5,
                "size": 40,
            }
        ],
    }

    app.show_startup_guard_result(result)

    assert len(app.startup_guard_tree.items) == 5
    assert [entry["_status"] for entry in app.startup_guard_visible_entries] == [
        "NEW",
        "CHANGED",
        "REMOVED",
        "TRUSTED",
        "UNCHANGED",
    ]
    assert app.startup_guard_visible_entries[1]["_before"]["sha256"] == "old"
    assert "=== Startup Guard Prüfung ===" in outputs[-1]


def test_on_startup_guard_select_updates_selected_entry_and_details(tmp_path):
    app = App.__new__(App)
    outputs = []
    test_file = tmp_path / "demo.desktop"
    test_file.write_text("[Desktop Entry]\nName=Demo\n", encoding="utf-8")

    app.startup_guard_tree = DummyTree()
    inserted = app.startup_guard_tree.insert(
        "", "end", values=("NEW", "user_autostart", "demo.desktop", str(test_file))
    )
    app.startup_guard_tree.selected = (inserted,)
    app.startup_guard_visible_entries = [
        {
            "_status": "NEW",
            "source": "user_autostart",
            "name": "demo.desktop",
            "path": str(test_file),
            "sha256": "hash",
            "mtime": 123,
            "size": 25,
        }
    ]
    app.update_startup_guard_output = lambda text, append=False: outputs.append(text)

    app.on_startup_guard_select()

    assert app.startup_guard_selected_entry["name"] == "demo.desktop"
    assert "Dateiinhalt/Ausschnitt:" in outputs[-1]
    assert "Status: NEW" in outputs[-1]


def test_analyze_startup_guard_changes_with_chad_ignores_unchanged():
    app = App.__new__(App)
    calls = []

    app.startup_guard_last_result = {
        "new": [
            {
                "source": "user_autostart",
                "name": "new.desktop",
                "path": "/tmp/new.desktop",
                "sha256": "new",
            }
        ],
        "changed": [
            {
                "before": {
                    "source": "systemd_user",
                    "name": "chg.service",
                    "path": "/tmp/chg.service",
                    "sha256": "old",
                },
                "after": {
                    "source": "systemd_user",
                    "name": "chg.service",
                    "path": "/tmp/chg.service",
                    "sha256": "new",
                },
            }
        ],
        "removed": [
            {
                "source": "system_autostart",
                "name": "gone.desktop",
                "path": "/tmp/gone.desktop",
                "sha256": "gone",
            }
        ],
        "trusted": [
            {
                "source": "user_autostart",
                "name": "trusted.desktop",
                "path": "/tmp/trusted.desktop",
                "sha256": "trusted",
            }
        ],
        "unchanged": [
            {
                "source": "user_autostart",
                "name": "same.desktop",
                "path": "/tmp/same.desktop",
                "sha256": "same",
            }
        ],
    }
    app.prepare_chad_analysis = lambda title, text: calls.append((title, text))
    app.log = lambda msg: None

    app.analyze_startup_guard_changes_with_chad()

    assert calls
    title, text = calls[0]
    assert title == "Startup Guard Änderungen Analyse"
    assert "new.desktop" in text
    assert "chg.service" in text
    assert "gone.desktop" in text
    assert "trusted.desktop" not in text


def test_startup_guard_reset_trustlist_rechecks():
    app = App.__new__(App)
    calls = []

    app.startup_guard_trustlist_path = "/tmp/startup_guard_trustlist.json"
    app.startup_guard_service = type(
        "DummyService",
        (),
        {"reset_trustlist": lambda self, path: calls.append(path) or (True, "")},
    )()
    app.log = calls.append
    app.startup_guard_check = lambda: calls.append("recheck")

    app.startup_guard_reset_trustlist()

    assert calls[0] == "/tmp/startup_guard_trustlist.json"
    assert calls[1] == "Startup Guard: Vertrauensliste wurde zurückgesetzt."
    assert calls[2] == "recheck"


def test_startup_guard_prompt_adds_cautious_focus():
    service = AiAnalysisService()

    prompt = service.build_prompt("Startup Guard Eintrag Analyse", "Pfad: /tmp/run.sh")

    assert "Behaupte nicht, dass etwas Malware ist." in prompt
    assert "/tmp" in prompt


def test_set_startup_guard_light_sets_expected_colors_and_status():
    app = App.__new__(App)
    colors = []

    app.l_startup_guard = (object(), object(), object())
    app.set_light = lambda _light, color: colors.append(color)
    app.startup_guard_status_var = type(
        "DummyVar",
        (),
        {
            "__init__": lambda self: setattr(self, "value", ""),
            "set": lambda self, value: setattr(self, "value", value),
            "get": lambda self: getattr(self, "value", ""),
        },
    )()

    app.set_startup_guard_light("off", "Startup Guard: keine Baseline vorhanden")
    assert colors[-1] == "gray"
    assert (
        app.startup_guard_status_var.get() == "Startup Guard: keine Baseline vorhanden"
    )

    app.set_startup_guard_light("ok", "Startup Guard: keine Änderungen")
    assert colors[-1] == "green"

    app.set_startup_guard_light("changed", "Startup Guard: 2 Änderung(en) erkannt")
    assert colors[-1] == "yellow"

    app.set_startup_guard_light("error", "Startup Guard: Fehler")
    assert colors[-1] == "red"


def test_startup_guard_startup_check_sets_gray_without_baseline(tmp_path):
    app = App.__new__(App)
    calls = []

    app.startup_guard_service = object()
    app.startup_guard_baseline_path = str(tmp_path / "missing.json")
    app.set_startup_guard_light = lambda state, message="": calls.append(
        (state, message)
    )

    app.startup_guard_startup_check()

    assert calls == [("off", "Startup Guard: keine Baseline vorhanden")]


def test_startup_guard_startup_check_sets_yellow_when_changes_found(tmp_path):
    app = App.__new__(App)
    calls = []

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"entries": []}', encoding="utf-8")

    class DummyService:
        def load_baseline(self, path):
            return {"entries": []}

        def load_trustlist(self, path):
            return {"trusted": {}}

        def collect_entries(self):
            return [{"path": "/tmp/demo.desktop"}]

        def compare_to_baseline(self, baseline, current, trustlist=None):
            return {
                "new": [{"path": "/tmp/demo.desktop"}],
                "changed": [],
                "removed": [],
                "trusted": [],
            }

    app.startup_guard_service = DummyService()
    app.startup_guard_baseline_path = str(baseline_path)
    app.set_startup_guard_light = lambda state, message="": calls.append(
        (state, message)
    )

    app.startup_guard_startup_check()

    assert calls == [("changed", "Startup Guard: 1 Änderung(en) erkannt")]


def test_startup_guard_startup_check_stays_green_with_only_trusted_entries(tmp_path):
    app = App.__new__(App)
    calls = []

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"entries": []}', encoding="utf-8")

    class DummyService:
        def load_baseline(self, path):
            return {"entries": []}

        def load_trustlist(self, path):
            return {
                "trusted": {
                    "/tmp/trusted.desktop": {
                        "sha256": "trusted",
                    }
                }
            }

        def collect_entries(self):
            return [{"path": "/tmp/trusted.desktop", "sha256": "trusted"}]

        def compare_to_baseline(self, baseline, current, trustlist=None):
            return {
                "new": [],
                "changed": [],
                "removed": [],
                "trusted": [{"path": "/tmp/trusted.desktop", "sha256": "trusted"}],
                "unchanged": [],
            }

    app.startup_guard_service = DummyService()
    app.startup_guard_baseline_path = str(baseline_path)
    app.startup_guard_trustlist_path = str(tmp_path / "trustlist.json")
    app.set_startup_guard_light = lambda state, message="": calls.append(
        (state, message)
    )

    app.startup_guard_startup_check()

    assert calls == [("ok", "Startup Guard: keine Änderungen")]


def test_startup_guard_show_trustlist_uses_configured_trustlist_path(tmp_path):
    app = App.__new__(App)
    outputs = []
    calls = []

    class DummyService:
        def load_trustlist(self, path):
            calls.append(path)
            return {
                "trusted": {
                    "/tmp/demo.desktop": {
                        "name": "demo.desktop",
                        "sha256": "hash",
                        "trusted_at": "2026-06-06T12:00:00",
                    }
                }
            }

    app.startup_guard_service = DummyService()
    app.startup_guard_trustlist_path = str(tmp_path / "trustlist.json")
    app.open_startup_guard_tab = lambda: calls.append("open-tab")
    app.update_startup_guard_output = lambda text, append=False: outputs.append(text)
    app.tr = lambda _key, default=None: default or _key

    app.startup_guard_show_trustlist()

    assert calls[0] == str(tmp_path / "trustlist.json")
    assert calls[1] == "open-tab"
    assert "demo.desktop" in outputs[-1]
    assert "/tmp/demo.desktop" in outputs[-1]


def test_startup_guard_startup_check_passes_trustlist_path_to_service(tmp_path):
    app = App.__new__(App)
    calls = []

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"entries": []}', encoding="utf-8")

    class DummyService:
        def load_baseline(self, path):
            return {"entries": []}

        def load_trustlist(self, path):
            calls.append(path)
            return {"trusted": {}}

        def collect_entries(self):
            return []

        def compare_to_baseline(self, baseline, current, trustlist=None):
            return {
                "new": [],
                "changed": [],
                "removed": [],
                "trusted": [],
                "unchanged": [],
            }

    app.startup_guard_service = DummyService()
    app.startup_guard_baseline_path = str(baseline_path)
    app.startup_guard_trustlist_path = str(tmp_path / "trustlist.json")
    app.set_startup_guard_light = lambda *_args, **_kwargs: None

    app.startup_guard_startup_check()

    assert calls == [str(tmp_path / "trustlist.json")]


def test_startup_guard_mark_and_remove_trusted_trigger_recheck(tmp_path):
    app = App.__new__(App)
    logs = []
    calls = []

    class DummyService:
        def mark_trusted(self, path, entry, trustlist_path):
            calls.append(("mark", path, trustlist_path))
            return True, ""

        def remove_trusted(self, path, trustlist_path):
            calls.append(("remove", path, trustlist_path))
            return True, ""

    app.startup_guard_service = DummyService()
    app.startup_guard_trustlist_path = str(tmp_path / "trustlist.json")
    app.startup_guard_selected_entry = {
        "_status": "NEW",
        "name": "demo.desktop",
        "path": "/tmp/demo.desktop",
        "sha256": "hash",
    }
    app.log = lambda msg: logs.append(msg)
    app.startup_guard_check = lambda: calls.append(("check",))

    app.startup_guard_mark_selected_trusted()
    app.startup_guard_remove_selected_trusted()

    assert calls == [
        ("mark", "/tmp/demo.desktop", str(tmp_path / "trustlist.json")),
        ("check",),
        ("remove", "/tmp/demo.desktop", str(tmp_path / "trustlist.json")),
        ("check",),
    ]
    assert "Eintrag als bekannt markiert" in logs[0]
    assert "Eintrag aus Vertrauensliste entfernt" in logs[1]
