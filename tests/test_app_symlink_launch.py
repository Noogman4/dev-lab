"""app.py must start through a symlinked netmon/ folder (desktop shortcut)."""

import os
import subprocess
import sys
from pathlib import Path

NETMON_DIR = Path(__file__).resolve().parents[1] / "netmon"


def test_app_py_imports_through_a_symlinked_folder(tmp_path):
    shortcut = tmp_path / "Verknüpfung mit netmon"
    shortcut.symlink_to(NETMON_DIR, target_is_directory=True)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    # --help exits in argparse after all module-level imports, without Tk.
    result = subprocess.run(
        [sys.executable, "-B", str(shortcut / "app.py"), "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert "NetMon GUI" in result.stdout
