"""Real Tk selection/actions under private Xvfb; only fixture permissions change."""

import stat
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.app import App
from netmon.features import path_guard_controller as controller
from tests import test_path_guard_review_v24 as review_fixtures

model = review_fixtures.model


@pytest.fixture
def ui(model, monkeypatch):
    root = tk.Tk()
    root.geometry("1180x650")
    app = App.__new__(App)
    app.lang = {}
    app.path_guard_service = model.service
    app.path_guard_status_var = tk.StringVar(master=root)
    app.l_path_guard = object()
    app.colors = []
    app.set_light = lambda _light, color: app.colors.append(color)
    app.log = lambda _: None
    app._open_security_menu_target_tab = lambda _: None
    ttk.Label(root, textvariable=app.path_guard_status_var).pack(anchor="w")
    pane = ttk.Panedwindow(root, orient="vertical")
    pane.pack(fill="both", expand=True)
    controller.build_review_panel(app, pane)
    detail_frame = ttk.Frame(pane)
    pane.add(detail_frame, weight=1)
    app.path_guard_detail = tk.Text(detail_frame, wrap="word")
    app.path_guard_detail.pack(fill="both", expand=True)
    app.run_path_guard_check()
    root.update_idletasks()
    row_id = app.path_guard_findings_table.get_children()[0]
    app.path_guard_findings_table.selection_set(row_id)
    controller.update_buttons(app)
    dialogs = []
    monkeypatch.setattr(
        controller.messagebox, "showinfo", lambda *args, **kwargs: dialogs.append(args)
    )
    monkeypatch.setattr(
        controller.messagebox, "showerror", lambda *args, **kwargs: dialogs.append(args)
    )
    yield app, dialogs
    root.destroy()


def test_real_buttons_accept_and_revoke_with_explicit_risk_text(ui, model, monkeypatch):
    app, dialogs = ui
    prompts = []
    monkeypatch.setattr(
        controller.messagebox,
        "askyesno",
        lambda title, text, **kwargs: prompts.append(text) or True,
    )
    assert app.colors[-1] == "yellow"
    assert app.path_guard_findings_table.winfo_ismapped()
    app.path_guard_review_buttons["accept"].invoke()
    assert "bewusst akzeptiert" in prompts[0]
    assert app.colors[-1] == "green"
    assert "geprüfte Ausnahmen: 1" in app.path_guard_status_var.get()
    report = app.path_guard_detail.get("1.0", "end")
    assert "Risiko: mittel" in report
    assert "Bestätigung ist keine Reparatur" in report
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o775
    if shutil.which("import"):
        root = tk._default_root
        root.update()
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/path-guard-reviewed.png",
            ],
            check=True,
            timeout=8,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    app.path_guard_review_buttons["revoke"].invoke()
    assert app.colors[-1] == "yellow"
    assert not model.service.reviews.load()
    assert not dialogs


def test_declined_repair_changes_nothing(ui, model, monkeypatch):
    app, _dialogs = ui
    prompts = []
    monkeypatch.setattr(
        controller.messagebox,
        "askyesno",
        lambda title, text, **kwargs: prompts.append(text) or False,
    )
    app.path_guard_review_buttons["repair"].invoke()
    assert "0775 → 0755" in prompts[0]
    assert "Keine rekursive Änderung" in prompts[0]
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o775
    assert not model.service.reviews.path.exists()
    assert app.colors[-1] == "yellow"


def test_confirmed_repair_rechecks_and_marks_no_open_findings(ui, model, monkeypatch):
    app, dialogs = ui
    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *args, **kwargs: True)
    app.path_guard_review_buttons["repair"].invoke()
    assert stat.S_IMODE(model.target.stat().st_mode) == 0o755
    assert app.colors[-1] == "green"
    assert not app.path_guard_last_result["review_items"]
    assert dialogs and "Gruppenschreibrecht entfernt" in dialogs[0][1]


def test_changes_during_confirmation_are_rejected(ui, model, monkeypatch):
    app, dialogs = ui

    def confirm(*args, **kwargs):
        model.target.chmod(0o770)
        return True

    monkeypatch.setattr(controller.messagebox, "askyesno", confirm)
    app.path_guard_review_buttons["accept"].invoke()
    assert not model.service.reviews.path.exists()
    assert app.colors[-1] == "yellow"
    assert dialogs and "verändert" in dialogs[0][1]


def test_high_risk_buttons_are_disabled(ui, model):
    app, _dialogs = ui
    model.target.chmod(0o777)
    app.run_path_guard_check()
    app.path_guard_findings_table.selection_set(
        app.path_guard_findings_table.get_children()[0]
    )
    controller.update_buttons(app)
    assert app.colors[-1] == "red"
    assert app.path_guard_review_buttons["accept"].instate(["disabled"])
    assert app.path_guard_review_buttons["repair"].instate(["disabled"])
    assert app.path_guard_review_buttons["details"].instate(["!disabled"])


def test_broken_confirmation_store_keeps_gray_instead_of_green(ui, model, monkeypatch):
    app, _dialogs = ui
    row = controller.selected(app)
    model.service.accept_finding(row["id"], row["fingerprint"])
    model.service.reviews.path.write_text("{broken")
    app.run_path_guard_check()
    assert app.colors[-1] == "gray"
    assert app.path_guard_last_result["review_summary"]["medium"] == 1
