"""Private-Xvfb Tk fixture for R01; media processes and UI helpers are stubs."""

import json
from pathlib import Path
import sys
import threading
import time
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from netmon.features import radio_controller as radio  # noqa: E402


class Player:
    def __init__(self):
        self.dead = threading.Event()
        self.ipc_path = ""

    def terminate(self):
        threading.Timer(0.25, self.dead.set).start()

    def kill(self):
        self.dead.set()

    def wait(self, timeout=None):
        if not self.dead.wait(timeout):
            raise TimeoutError
        return 0

    def poll(self):
        return 0 if self.dead.is_set() else None


def main():
    root = tk.Tk()
    root.withdraw()
    root.radio_proc = Player()
    root.radio_ipc_path = ""
    root.radio_volume_var = tk.IntVar(root, 50)
    root.tr = lambda _key, default=None: default
    result = {
        "mode": sys.argv[1],
        "completed": False,
        "close_seconds": 0,
        "tcl_threaded": root.tk.eval("set tcl_platform(threaded)") == "1",
    }

    def close():
        started = time.monotonic()
        radio.stop_radio_playback(root, async_mode=False)
        result["close_seconds"] = time.monotonic() - started
        result["completed"] = True
        root.after(500, root.quit)

    def first():
        if result["mode"] == "switch-then-close":
            radio.play_radio_station(root, "B")
        else:
            radio.stop_radio_playback(root)
        root.after(50, close)

    def start(*_args, **_kwargs):
        time.sleep(0.15)
        return Player()

    helpers = {
        name: lambda *_a, **_k: None
        for name in (
            "save_radio_settings",
            "update_radio_header",
            "refresh_radio_source_ui",
            "refresh_radio_station_table",
            "refresh_radio_favorites_list",
            "_set_radio_light",
            "_set_radio_station_text",
            "_set_radio_title_text",
            "set_radio_status",
            "_poll_radio_metadata",
        )
    }
    helpers.update(
        radio_available=lambda _: True,
        _resolve_target_station=lambda *_a, **_k: {
            "id": "B",
            "name": "B",
            "url": "https://example.com/b",
        },
        _start_radio_playback=start,
    )
    with patch.multiple(radio, **helpers):
        root.after(10, close if result["mode"] == "control" else first)
        root.mainloop()
        root.destroy()
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
