import inspect

from netmon import app as netmon_app
from netmon import main as netmon_main
from netmon.core import lock as netmon_lock


class DummyNotebook:
    def __init__(self):
        self.selected = None

    def select(self, tab):
        self.selected = tab


def test_activate_startup_log_view_selects_log_tab_and_shows_overlay():
    app = netmon_app.App.__new__(netmon_app.App)
    calls = []

    app.nb = DummyNotebook()
    app.tab_log = object()
    app.log_overlay_image_path = "/tmp/demo.png"
    app.log_overlay_source_image = None
    app.log_overlay_source_photo = None
    app._render_log_overlay_image = lambda: calls.append("render")
    app._set_log_overlay_visible = lambda visible, persist=True: calls.append(
        ("visible", visible, persist)
    )

    app._activate_startup_log_view()

    assert app.nb.selected is app.tab_log
    assert calls == ["render", ("visible", True, False)]


def test_activate_startup_log_view_skips_overlay_without_image():
    app = netmon_app.App.__new__(netmon_app.App)
    calls = []

    app.nb = DummyNotebook()
    app.tab_log = object()
    app.log_overlay_image_path = ""
    app.log_overlay_source_image = None
    app.log_overlay_source_photo = None
    app._render_log_overlay_image = lambda: calls.append("render")
    app._set_log_overlay_visible = lambda visible, persist=True: calls.append(
        ("visible", visible, persist)
    )

    app._activate_startup_log_view()

    assert app.nb.selected is app.tab_log
    assert calls == []


def test_acquire_and_release_netmon_instance_lock(tmp_path, monkeypatch):
    netmon_lock.release_netmon_instance_lock()
    monkeypatch.setattr(netmon_lock, "get_netmon_state_dir", lambda: str(tmp_path))

    ok, lock_path = netmon_lock.acquire_netmon_instance_lock()

    assert ok is True
    assert lock_path == str(tmp_path / netmon_lock.NETMON_INSTANCE_LOCK_NAME)
    assert netmon_lock.NETMON_INSTANCE_LOCK_HANDLE is not None

    netmon_lock.release_netmon_instance_lock()

    assert netmon_lock.NETMON_INSTANCE_LOCK_HANDLE is None
    assert netmon_lock.NETMON_INSTANCE_LOCK_PATH == ""


def test_acquire_netmon_instance_lock_is_idempotent(tmp_path, monkeypatch):
    netmon_lock.release_netmon_instance_lock()
    monkeypatch.setattr(netmon_lock, "get_netmon_state_dir", lambda: str(tmp_path))

    first_ok, first_path = netmon_lock.acquire_netmon_instance_lock()
    second_ok, second_path = netmon_lock.acquire_netmon_instance_lock()

    assert first_ok is True
    assert second_ok is True
    assert first_path == second_path

    netmon_lock.release_netmon_instance_lock()


def test_run_headless_smoke_creates_and_destroys_app():
    calls = []

    class DummyApp:
        def __init__(self, start_theme=None):
            calls.append(("init", start_theme))

        def update_idletasks(self):
            calls.append("update_idletasks")

        def update(self):
            calls.append("update")

        def quit(self):
            calls.append("quit")

        def destroy(self):
            calls.append("destroy")

    rc = netmon_main.run_headless_smoke(DummyApp, theme_name="dark")

    assert rc == 0
    assert calls[0] == ("init", "dark")
    assert "update_idletasks" in calls
    assert "quit" in calls
    assert "destroy" in calls


def test_parse_xrandr_monitor_bounds_detects_primary_output():
    parsed = netmon_app._parse_xrandr_monitor_bounds(
        "DP-1 connected primary 2560x1440+1920+0 (normal left inverted right x axis y axis)"
    )

    assert parsed == {
        "name": "DP-1",
        "primary": True,
        "x": 1920,
        "y": 0,
        "width": 2560,
        "height": 1440,
    }


def test_main_parse_xrandr_monitor_bounds_detects_primary_output():
    parsed = netmon_main._parse_xrandr_monitor_bounds(
        "DP-1 connected primary 2560x1440+1920+0 (normal left inverted right x axis y axis)"
    )

    assert parsed == {
        "name": "DP-1",
        "primary": True,
        "x": 1920,
        "y": 0,
        "width": 2560,
        "height": 1440,
    }


def test_detect_primary_monitor_bounds_prefers_primary_output(monkeypatch):
    class DummyResult:
        stdout = "\n".join(
            [
                "HDMI-1 connected 1920x1080+2560+0 (normal left inverted right x axis y axis)",
                "DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis)",
            ]
        )

    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(netmon_app, "has_cmd", lambda name: name == "xrandr")
    monkeypatch.setattr(netmon_app.subprocess, "run", lambda *args, **kwargs: DummyResult())

    assert netmon_app._detect_primary_monitor_bounds() == (0, 0, 2560, 1440)


def test_main_detect_primary_monitor_bounds_prefers_primary_output(monkeypatch):
    class DummyResult:
        stdout = "\n".join(
            [
                "HDMI-1 connected 1920x1080+2560+0 (normal left inverted right x axis y axis)",
                "DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis)",
            ]
        )

    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(netmon_main.shutil, "which", lambda name: "/usr/bin/xrandr")
    monkeypatch.setattr(
        netmon_main.subprocess, "run", lambda *args, **kwargs: DummyResult()
    )

    assert netmon_main._detect_primary_monitor_bounds() == (0, 0, 2560, 1440)


def test_center_geometry_on_primary_monitor_uses_detected_bounds(monkeypatch):
    monkeypatch.setattr(
        netmon_main, "_detect_primary_monitor_bounds", lambda: (1920, 0, 2560, 1440)
    )

    assert netmon_main._center_geometry_on_primary_monitor(
        720,
        560,
        fallback_screen_width=5120,
        fallback_screen_height=1440,
        minimum_margin=20,
    ) == (720, 560, 2840, 440)


def test_apply_primary_monitor_start_geometry_uses_detected_bounds(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    calls = []

    monkeypatch.setattr(
        netmon_app,
        "_detect_primary_monitor_bounds",
        lambda: (1920, 0, 2560, 1440),
    )
    app.winfo_screenwidth = lambda: 5120
    app.winfo_screenheight = lambda: 1440
    app.geometry = lambda value: calls.append(("geometry", value))
    app.minsize = lambda width, height: calls.append(("minsize", width, height))
    app.maxsize = lambda width, height: calls.append(("maxsize", width, height))

    app._apply_primary_monitor_start_geometry()

    assert calls == [
        ("geometry", "2560x1440+1920+0"),
        ("minsize", 900, 600),
        ("maxsize", 2560, 1440),
    ]


def test_show_startup_splash_centers_on_primary_monitor(monkeypatch):
    geometry_calls = []

    class DummyLabel:
        def __init__(self, *_args, **_kwargs):
            pass

        def pack(self):
            return None

        def winfo_reqwidth(self):
            return 800

        def winfo_reqheight(self):
            return 400

    class DummyRoot:
        def overrideredirect(self, *_args):
            return None

        def configure(self, **_kwargs):
            return None

        def attributes(self, *_args):
            return None

        def update_idletasks(self):
            return None

        def winfo_screenwidth(self):
            return 5120

        def winfo_screenheight(self):
            return 1440

        def geometry(self, value):
            geometry_calls.append(value)

        def after(self, *_args):
            return None

        def mainloop(self):
            return None

        def destroy(self):
            return None

    class DummyTkModule:
        Label = DummyLabel

        @staticmethod
        def Tk():
            return DummyRoot()

        @staticmethod
        def PhotoImage(*_args, **_kwargs):
            return object()

    monkeypatch.setattr(netmon_main, "_startup_splash_path", lambda: "/tmp/splash.png")
    monkeypatch.setattr(
        netmon_main, "_detect_primary_monitor_bounds", lambda: (1920, 0, 2560, 1440)
    )
    monkeypatch.setattr(netmon_main, "Image", None)
    monkeypatch.setattr(netmon_main, "ImageTk", None)
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tkinter":
            return DummyTkModule
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    netmon_main._show_startup_splash(duration_ms=500)

    assert geometry_calls == ["800x400+2800+520"]


def test_show_startup_support_dialog_centers_on_primary_monitor(monkeypatch):
    geometry_calls = []

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

    class DummyText:
        def __init__(self, *_args, **_kwargs):
            self.value = ""

        def grid(self, **_kwargs):
            return None

        def insert(self, *_args):
            return None

        def get(self, *_args):
            return self.value

    class DummyWidget:
        def __init__(self, *_args, **_kwargs):
            return None

        def grid(self, **_kwargs):
            return None

        def pack(self, **_kwargs):
            return None

        def columnconfigure(self, *_args, **_kwargs):
            return None

        def rowconfigure(self, *_args, **_kwargs):
            return None

    class DummyButton(DummyWidget):
        pass

    class DummyToplevel:
        def title(self, *_args):
            return None

        def geometry(self, value):
            geometry_calls.append(value)

        def minsize(self, *_args):
            return None

        def update_idletasks(self):
            return None

        def winfo_screenwidth(self):
            return 5120

        def winfo_screenheight(self):
            return 1440

        def protocol(self, *_args):
            return None

        def transient(self, *_args):
            return None

        def grab_set(self):
            return None

        def focus_force(self):
            return None

        def destroy(self):
            return None

    class DummyRoot:
        def withdraw(self):
            return None

        def wait_window(self, *_args):
            return None

        def destroy(self):
            return None

    class DummyTkModule:
        Text = DummyText
        StringVar = DummyVar
        messagebox = None
        ttk = None

        @staticmethod
        def Tk():
            return DummyRoot()

        @staticmethod
        def Toplevel(*_args, **_kwargs):
            return DummyToplevel()

    class DummyTtkModule:
        Frame = DummyWidget
        Label = DummyWidget
        Entry = DummyWidget
        LabelFrame = DummyWidget
        Button = DummyButton

    class DummyMessageBox:
        @staticmethod
        def showerror(*_args, **_kwargs):
            return None

        @staticmethod
        def showinfo(*_args, **_kwargs):
            return None

    DummyTkModule.messagebox = DummyMessageBox
    DummyTkModule.ttk = DummyTtkModule

    monkeypatch.setattr(
        netmon_main, "_detect_primary_monitor_bounds", lambda: (1920, 0, 2560, 1440)
    )
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tkinter":
            return DummyTkModule
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert netmon_main._show_startup_support_dialog("Fehler", "Detail") == ""
    assert geometry_calls[:2] == ["720x560", "720x560+2840+440"]


def test_main_source_contains_headless_smoke_flag():
    source = inspect.getsource(netmon_main.main)
    init_source = inspect.getsource(netmon_app.App.__init__)
    splash_source = inspect.getsource(netmon_main._show_startup_splash)
    support_source = inspect.getsource(netmon_main._show_startup_support_dialog)

    assert "--headless-smoke" in source
    assert "run_headless_smoke(App, theme_name=args.theme)" in source
    assert "self._apply_primary_monitor_start_geometry()" in init_source
    assert "_center_geometry_on_primary_monitor(" in splash_source
    assert "_center_geometry_on_primary_monitor(" in support_source
