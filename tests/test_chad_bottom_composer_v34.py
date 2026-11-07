"""Real Tk bottom composer and reading-position regressions in private Xvfb."""

from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock

import pytest

from netmon.features import chad_controller as controller
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app


def fill_history(root, app):
    controller.append_to_chad_output(
        app,
        "Chad Antwort",
        "\n".join(
            f"Zeile {i:03d}: Leseposition im längeren Verlauf." for i in range(200)
        ),
    )
    root.update()
    return app.chad_analysis_text


def assert_last_line_visible(history):
    # Styled Tk text can report a fraction below 1 despite the complete final line
    # sitting at the bottom. Check actual rendered content, not the estimate.
    line = history.dlineinfo("end-1c")
    assert line is not None
    assert 0 <= line[1] and line[1] + line[3] <= history.winfo_height()
    assert history.index(f"@0,{history.winfo_height()-1}") == history.index("end-1c")


@pytest.mark.parametrize("geometry", ["820x480", "1024x768", "1280x720"])
def test_input_and_actions_stay_below_scrollable_history(chad_app, geometry):
    root, app = chad_app
    root.geometry(geometry)
    history = fill_history(root, app)
    composer = app.chad_chat_input
    assert (
        history.winfo_rooty() + history.winfo_height()
        <= app.btn_chad_import_file.winfo_rooty()
    )
    for button in (app.btn_chad_import_file, app.btn_chad_browser, app.btn_chad_online):
        assert button.winfo_rooty() + button.winfo_height() <= composer.winfo_rooty()
        assert button.winfo_ismapped()
    assert history.winfo_height() > composer.winfo_height()
    position = (composer.winfo_rootx(), composer.winfo_rooty(), composer.winfo_height())
    for index in ("1.0", "70.0", "end"):
        history.see(index)
        root.update()
        assert (
            composer.winfo_rootx(),
            composer.winfo_rooty(),
            composer.winfo_height(),
        ) == position
        assert (
            composer.winfo_rooty() + composer.winfo_height()
            <= root.winfo_rooty() + root.winfo_height()
        )
    composer.insert("1.0", "Nächste Rückfrage bleibt hier stehen.")
    assert composer.get("1.0", "end-1c") == "Nächste Rückfrage bleibt hier stehen."


def test_new_answers_preserve_reading_anchor_selection_and_draft(chad_app):
    root, app = chad_app
    history = fill_history(root, app)
    history.yview("70.0")
    root.update()
    anchor = history.index("@0,0")
    history.tag_add("sel", anchor, f"{anchor} lineend")
    selection = history.tag_ranges("sel")
    selected_text = history.get(*selection)
    app.chad_chat_input.insert("1.0", "Ungesendeter Entwurf")
    for i in range(3):
        controller.append_to_chad_output(
            app, "Chad Antwort", f"Neue Antwort {i}\n" * 20
        )
        root.update()
        assert history.index("@0,0") == anchor
        assert history.tag_ranges("sel") == selection
        assert history.get(*history.tag_ranges("sel")) == selected_text
        assert history.yview()[1] < 1.0
        assert app.chad_chat_input.get("1.0", "end-1c") == "Ungesendeter Entwurf"


@pytest.mark.parametrize("enabled", [True, False])
def test_follow_new_answers_only_when_enabled_and_already_at_bottom(chad_app, enabled):
    root, app = chad_app
    history = fill_history(root, app)
    app.chad_auto_scroll_var.set(enabled)
    history.see("end")
    root.update()
    anchor = history.index("@0,0")
    controller.append_to_chad_output(
        app, "Chad Antwort", "Neue Antwort\n" * 40 + "LATEST_END"
    )
    root.update()
    if enabled:
        assert_last_line_visible(history)
        assert history.dlineinfo(history.search("LATEST_END", "1.0")) is not None
    else:
        assert history.index("@0,0") == anchor
        assert history.yview()[1] < 1.0
        assert history.dlineinfo("end-1c") is None


def test_resuming_at_bottom_reenables_following_and_filter_drops_old_selection(
    chad_app,
):
    root, app = chad_app
    history = fill_history(root, app)
    history.yview("50.0")
    root.update()
    history.tag_add("sel", "50.0", "50.end")
    controller.append_to_chad_output(app, "System", "Prüfergebnis")
    root.update()
    assert history.yview()[1] < 1.0
    history.see("end")
    root.update()
    controller.append_to_chad_output(app, "Chad Antwort", "Neue letzte Antwort\n" * 20)
    root.update()
    assert_last_line_visible(history)
    app.chad_output_filter_var.set("Nur ergebnisse")
    controller.refresh_chad_output_view(app)
    root.update()
    assert not history.tag_ranges("sel")
    assert "Prüfergebnis" in history.get("1.0", "end")
    assert "Neue letzte Antwort" not in history.get("1.0", "end")


def test_return_binding_still_uses_existing_send_action(chad_app):
    root, app = chad_app
    app.send_chad_chat_message = Mock(return_value="break")
    app.chad_chat_input.insert("1.0", "Private fixture question")
    app.chad_chat_input.focus_force()
    root.update()
    app.chad_chat_input.event_generate("<Return>")
    root.update()
    app.send_chad_chat_message.assert_called_once_with()


def test_bottom_composer_visual_fixture(chad_app):
    root, app = chad_app
    root.geometry("1100x700")
    app.chad_dev_filter_status_var.set("Eingabe unten – Verlauf unabhängig scrollbar")
    controller.append_to_chad_output(
        app,
        "Chad Antwort",
        "Empfehlung: Den Resolver prüfen.\n```bash\nresolvectl status\n```\nPrüfung: DNS-Server mit dem gewählten Profil vergleichen.",
    )
    app.chad_chat_input.insert("1.0", "Meine Rückfrage zur Auswertung …")
    root.update()
    if shutil.which("import"):
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/chad-bottom-composer.png",
            ],
            check=True,
            timeout=10,
        )
        assert Path("/work/chad-bottom-composer.png").is_file()
