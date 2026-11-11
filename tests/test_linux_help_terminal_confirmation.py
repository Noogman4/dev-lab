"""Catalog metadata must never waive shell execution confirmation."""

import csv
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon.features import linux_help_controller as controller


def make_app(tmp_path, item=None):
    app = SimpleNamespace(
        linux_help_selected_id="example",
        linux_help_status_var=SimpleNamespace(set=Mock()),
        linux_help_data_path=str(tmp_path / "commands.json"),
        linux_help_glossary_path=str(tmp_path / "missing-glossary.json"),
        linux_help_data=[item] if item else [],
        tr=lambda key, fallback: fallback,
        _validate_linux_help_command_for_terminal=Mock(return_value=(True, "")),
        _open_command_in_external_terminal=Mock(return_value="xterm"),
    )
    return app


def command(**overrides):
    return dict(
        {
            "id": "example",
            "category": "System",
            "name": "Example",
            "cmd": "printf '%s' $(id); printf done > /tmp/example",
            "risk": "safe",
            "root_required": False,
            "enabled": True,
        },
        **overrides,
    )


@pytest.mark.parametrize("risk", ["safe", "caution", "danger", "", "unknown"])
@pytest.mark.parametrize("answer", [True, False, None])
def test_every_catalog_command_requires_exact_confirmation(
    tmp_path, monkeypatch, risk, answer
):
    item = command(risk=risk)
    app = make_app(tmp_path, item)
    dialog = Mock(return_value=answer)
    monkeypatch.setattr(controller, "messagebox", SimpleNamespace(askyesno=dialog))

    result = controller.send_linux_help_command_to_terminal(app)

    dialog.assert_called_once()
    assert dialog.call_args.args[1].endswith("\n\n" + item["cmd"])
    assert dialog.call_args.kwargs["default"] == "no"
    assert result is (answer is True)
    if answer is True:
        app._open_command_in_external_terminal.assert_called_once_with(item["cmd"])
    else:
        app._open_command_in_external_terminal.assert_not_called()


@pytest.mark.parametrize("missing", [True, False])
def test_unavailable_confirmation_fails_closed(tmp_path, monkeypatch, missing):
    app = make_app(tmp_path, command())
    dialog = (
        None
        if missing
        else SimpleNamespace(askyesno=Mock(side_effect=RuntimeError("no display")))
    )
    monkeypatch.setattr(controller, "messagebox", dialog)
    assert controller.send_linux_help_command_to_terminal(app) is False
    app._open_command_in_external_terminal.assert_not_called()


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
@pytest.mark.parametrize("reload", [False, True])
def test_imported_safe_metadata_cannot_bypass_after_save(
    tmp_path, monkeypatch, extension, reload
):
    # Attempts to supply provenance or confirmation policy are also untrusted.
    row = command(trusted=True, source="builtin", requires_confirmation=False)
    path = tmp_path / ("catalog." + extension)
    if extension == "csv":
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)
    else:
        openpyxl = pytest.importorskip("openpyxl")
        book = openpyxl.Workbook()
        book.active.append(list(row))
        book.active.append(list(row.values()))
        book.save(path)
        book.close()
    app = make_app(tmp_path)
    entries = controller.import_linux_help_csv(app, path)
    assert len(entries) == 1
    assert entries[0]["risk"] == "safe"
    assert entries[0]["root_required"] is False
    if reload:
        assert controller.save_linux_help_data(app, update_status=False)
        app.linux_help_data = []
        entries = controller.load_linux_help_data(app)
    app.linux_help_selected_id = entries[0]["id"]
    dialog = Mock(return_value=False)
    monkeypatch.setattr(controller, "messagebox", SimpleNamespace(askyesno=dialog))
    assert controller.send_linux_help_command_to_terminal(app) is False
    assert dialog.call_args.args[1].endswith("\n\n" + row["cmd"])
    app._open_command_in_external_terminal.assert_not_called()


def test_legacy_json_without_provenance_requires_confirmation(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    with open(app.linux_help_data_path, "w", encoding="utf-8") as stream:
        json.dump([command()], stream)
    controller.load_linux_help_data(app)
    dialog = Mock(return_value=False)
    monkeypatch.setattr(controller, "messagebox", SimpleNamespace(askyesno=dialog))
    assert controller.send_linux_help_command_to_terminal(app) is False
    dialog.assert_called_once()
    app._open_command_in_external_terminal.assert_not_called()


@pytest.mark.parametrize("case", ["missing", "disabled", "glossary", "invalid"])
def test_ineligible_commands_never_prompt_or_launch(tmp_path, monkeypatch, case):
    item = command()
    if case == "disabled":
        item["enabled"] = False
    if case == "glossary":
        item["entry_type"] = "glossary"
    app = make_app(tmp_path, None if case == "missing" else item)
    if case == "invalid":
        app._validate_linux_help_command_for_terminal.return_value = (False, "invalid")
    dialog = Mock(return_value=True)
    monkeypatch.setattr(controller, "messagebox", SimpleNamespace(askyesno=dialog))
    assert controller.send_linux_help_command_to_terminal(app) is False
    dialog.assert_not_called()
    app._open_command_in_external_terminal.assert_not_called()


def test_confirmed_command_is_same_snapshot_that_runs(tmp_path, monkeypatch):
    item = command()
    original = item["cmd"]
    app = make_app(tmp_path, item)

    def confirm(*args, **kwargs):
        assert args[1].endswith("\n\n" + original)
        item["cmd"] = "different command"
        return True

    monkeypatch.setattr(controller, "messagebox", SimpleNamespace(askyesno=confirm))
    assert controller.send_linux_help_command_to_terminal(app) is True
    app._open_command_in_external_terminal.assert_called_once_with(original)
