import inspect
import zipfile

from netmon.app import App
from netmon.features import fun_controller
from netmon.ui.tabs.fun_tab import build_fun_tab


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyFunTable:
    def __init__(self, selected=None):
        self.rows = {}
        self.selected = tuple(selected or ())
        self.seen = []

    def selection(self):
        return self.selected

    def get_children(self):
        return tuple(self.rows.keys())

    def delete(self, item):
        self.rows.pop(item, None)

    def insert(self, _parent, _index, iid=None, values=()):
        self.rows[iid] = tuple(values)

    def selection_set(self, item):
        self.selected = (item,)

    def see(self, item):
        self.seen.append(item)


def test_discover_fun_games_finds_python_launchers(tmp_path):
    games_dir = tmp_path / "code_the_classics"
    game_dir = games_dir / "cavern"
    game_dir.mkdir(parents=True)
    (game_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.fun_games_dir = str(games_dir)
    app.dep_status = {"python3": True}
    app.tr = lambda _key, default=None: default

    games = fun_controller.discover_fun_games(app)

    assert len(games) == 1
    assert games[0]["name"] == "Cavern"
    assert games[0]["source"] == "Code the Classics"
    assert games[0]["start"] == "Ja"


def test_update_fun_dependency_state_reports_missing_modules():
    app = type("DummyApp", (), {})()
    app.dep_status = {"python3": True, "pygame_module": False, "pgzero_module": False}
    app.fun_dependency_var = DummyVar("")
    app.tr = lambda _key, default=None: default

    fun_controller.update_fun_dependency_state(app)

    assert "pygame fehlt" in app.fun_dependency_var.get()
    assert "pgzero fehlt" in app.fun_dependency_var.get()


def test_is_current_game_running_requires_matching_id_and_process():
    app = type("DummyApp", (), {})()
    app.fun_current_game = {"id": "cavern::main.py"}
    app.fun_game_proc = object()

    assert fun_controller._is_current_game_running(app, "cavern::main.py") is True
    assert fun_controller._is_current_game_running(app, "other::main.py") is False

    app.fun_game_proc = None

    assert fun_controller._is_current_game_running(app, "cavern::main.py") is False


def test_set_fun_status_formats_translated_text():
    app = type("DummyApp", (), {})()
    app.fun_status_var = DummyVar("")
    app.tr = lambda key, default=None: {
        "fun_status_started": "Spiel gestartet: {name}"
    }.get(key, default)

    fun_controller._set_fun_status(
        app,
        "fun_status_started",
        "Spiel gestartet: {name}",
        name="Cavern",
    )

    assert app.fun_status_var.get() == "Spiel gestartet: Cavern"


def test_fun_game_row_values_marks_running_game():
    app = type("DummyApp", (), {})()
    app.fun_current_game = {"id": "cavern::main.py"}
    app.fun_game_proc = object()
    app.tr = lambda _key, default=None: default

    values = fun_controller._fun_game_row_values(
        app,
        {
            "id": "cavern::main.py",
            "name": "Cavern",
            "source": "Code the Classics",
            "status": "Bereit",
            "start": "Ja",
        },
        "cavern::main.py",
    )

    assert values == ("Cavern", "Code the Classics", "Läuft", "Ja")


def test_update_fun_games_table_inserts_rows_and_preserves_selection():
    app = type("DummyApp", (), {})()
    app.fun_games = [
        {
            "id": "cavern::main.py",
            "name": "Cavern",
            "source": "Code the Classics",
            "status": "Bereit",
            "start": "Ja",
        }
    ]
    app.fun_current_game = None
    app.fun_game_proc = None
    app.fun_games_table = DummyFunTable(selected=["cavern::main.py"])
    app.tr = lambda _key, default=None: default

    fun_controller.update_fun_games_table(app)

    assert app.fun_games_table.rows["cavern::main.py"] == (
        "Cavern",
        "Code the Classics",
        "Bereit",
        "Ja",
    )
    assert app.fun_games_table.selected == ("cavern::main.py",)
    assert app.fun_games_table.seen == ["cavern::main.py"]


def test_start_selected_game_uses_silent_background_popen(tmp_path):
    game_path = tmp_path / "cavern" / "main.py"
    game_path.parent.mkdir(parents=True)
    game_path.write_text("print('ok')\n", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.dep_status = {"python3": True}
    app.fun_games = [
        {
            "id": "cavern::main.py",
            "name": "Cavern",
            "path": str(game_path),
            "status": "Bereit",
            "start": "Ja",
        }
    ]
    app.fun_game_proc = None
    app.fun_current_game = None
    app.fun_status_var = DummyVar("")
    app.fun_games_dir = str(tmp_path)
    app.tr = lambda _key, default=None: default
    app.log_safe = lambda _message: None
    app.after = lambda _delay, func: func()
    app._is_safe_netmon_managed_path = lambda path: str(path).startswith(str(tmp_path))

    class DummyTable:
        def selection(self):
            return ("cavern::main.py",)

    app.fun_games_table = DummyTable()

    calls = []

    class DummyProc:
        def wait(self, timeout=None):
            calls.append(("wait", timeout))
            return 0

    original_popen = fun_controller.subprocess.Popen
    original_thread = fun_controller.threading.Thread
    original_update = fun_controller.update_fun_games_table

    def fake_popen(args, **kwargs):
        calls.append(("popen", args, kwargs))
        return DummyProc()

    class DummyThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            calls.append(("thread_start", self.daemon))

    try:
        fun_controller.subprocess.Popen = fake_popen
        fun_controller.threading.Thread = DummyThread
        fun_controller.update_fun_games_table = lambda _app: calls.append(("update",))

        assert fun_controller.start_selected_game(app) is True
    finally:
        fun_controller.subprocess.Popen = original_popen
        fun_controller.threading.Thread = original_thread
        fun_controller.update_fun_games_table = original_update

    popen_call = calls[0]
    assert popen_call[0] == "popen"
    assert popen_call[1] == ["python3", str(game_path)]
    assert popen_call[2]["cwd"] == str(game_path.parent)
    assert popen_call[2]["stdin"] is fun_controller.subprocess.DEVNULL
    assert popen_call[2]["stdout"] is fun_controller.subprocess.DEVNULL
    assert popen_call[2]["stderr"] is fun_controller.subprocess.DEVNULL
    assert popen_call[2]["start_new_session"] is True


def test_start_selected_game_rejects_path_outside_games_dir(tmp_path):
    games_dir = tmp_path / "games"
    games_dir.mkdir()
    outside_path = tmp_path / "outside.py"
    outside_path.write_text("print('nope')\n", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.fun_games_dir = str(games_dir)
    app.dep_status = {"python3": True}
    app.fun_games = [
        {
            "id": "outside.py",
            "name": "Outside",
            "path": str(outside_path),
            "status": "Bereit",
            "start": "Ja",
        }
    ]
    app.fun_game_proc = None
    app.fun_current_game = None
    app.fun_status_var = DummyVar("")
    app.tr = lambda _key, default=None: default
    app.log_safe = lambda _message: None
    app.after = lambda _delay, func: func()
    app._is_safe_netmon_managed_path = lambda path: str(path).startswith(str(tmp_path))

    class DummyTable:
        def selection(self):
            return ("outside.py",)

    app.fun_games_table = DummyTable()

    assert fun_controller.start_selected_game(app) is False
    assert app.fun_status_var.get() == "Start fehlgeschlagen: unsicherer Spielpfad"


def test_count_code_the_classics_files_requires_real_python_files(tmp_path):
    app = App.__new__(App)
    app.netmon_config_dir = str(tmp_path / "config")
    app.netmon_state_dir = str(tmp_path / "state")
    app.fun_games_dir = str(tmp_path / "fun" / "code_the_classics")
    app._is_safe_netmon_managed_path = lambda _path: True
    games_dir = tmp_path / "fun" / "code_the_classics"
    games_dir.mkdir(parents=True)
    (games_dir / "README.txt").write_text("placeholder\n", encoding="utf-8")

    assert app._count_code_the_classics_files() == 0

    game_dir = games_dir / "cavern"
    game_dir.mkdir()
    (game_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    assert app._count_code_the_classics_files() == 1


def test_import_code_the_classics_zip_archive_extracts_python_files(tmp_path):
    app = App.__new__(App)
    app.netmon_config_dir = str(tmp_path / "config")
    app.netmon_state_dir = str(tmp_path / "state")
    app.fun_games_dir = str(tmp_path / "fun" / "code_the_classics")
    app._is_safe_netmon_managed_path = lambda _path: True

    zip_path = tmp_path / "ctc.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("cavern/main.py", "print('ok')\n")
        zip_ref.writestr("cavern/README.txt", "info\n")

    imported_count = app._import_code_the_classics_zip_archive(str(zip_path))

    assert imported_count == 1
    assert (tmp_path / "fun" / "code_the_classics" / "cavern" / "main.py").exists()


def test_import_code_the_classics_zip_archive_rejects_zip_slip(tmp_path):
    app = App.__new__(App)
    app.netmon_config_dir = str(tmp_path / "config")
    app.netmon_state_dir = str(tmp_path / "state")
    app.fun_games_dir = str(tmp_path / "fun" / "code_the_classics")
    app._is_safe_netmon_managed_path = lambda _path: True

    zip_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("../escape.py", "print('nope')\n")

    try:
        app._import_code_the_classics_zip_archive(str(zip_path))
    except ValueError as exc:
        assert "Unsicherer ZIP-Pfad erkannt" in str(exc)
    else:
        raise AssertionError("Zip-Slip wurde nicht blockiert")


def test_fun_integration_hooks_are_present():
    init_source = inspect.getsource(App.__init__)
    close_source = inspect.getsource(App.on_close)
    preflight_source = inspect.getsource(App.preflight_dependencies)
    manual_summary_source = inspect.getsource(App._log_preflight_manual_summary)

    assert "self.fun_games_dir = os.path.expanduser(" in init_source
    assert 'self.fun_status_var = tk.StringVar(value="Fun: bereit")' in init_source
    assert "build_fun_tab(self)" in init_source
    assert "self.stop_running_fun_game()" in close_source
    assert '"python3": has_cmd("python3")' in preflight_source
    assert (
        '"pygame_module": importlib.util.find_spec("pygame") is not None'
        in preflight_source
    )
    assert (
        '"pgzero_module": importlib.util.find_spec("pgzero") is not None'
        in preflight_source
    )
    assert (
        '"code_the_classics_files": self._count_code_the_classics_files() > 0'
        in preflight_source
    )
    assert '("python3 (Fun)", "python3")' in manual_summary_source
    assert "Code the Classics Spiele: FEHLT" in manual_summary_source
    assert (
        'self.set_feature_enabled("fun", checks.get("python3", False))'
        in preflight_source
    )
    assert (
        "self.missing_dependencies = list(self.dep_installer_missing_keys)"
        in preflight_source
    )
    assert "self._log_dependency_installer_summary()" in preflight_source


def test_fun_tab_source_contains_launcher_controls():
    source = inspect.getsource(build_fun_tab)

    assert 'text=app.tr("tools_tab_fun", "Fun")' in source
    assert "app.fun_games_table" in source
    assert 'text=app.tr("fun_btn_open_folder", "Spieleordner öffnen")' in source
    assert 'text=app.tr("fun_btn_refresh", "Liste aktualisieren")' in source
    assert 'text=app.tr("fun_btn_start", "Spiel starten")' in source
    assert 'text=app.tr("fun_btn_stop", "Spiel stoppen")' in source
    assert 'columns=("name", "source", "status", "start")' in source
