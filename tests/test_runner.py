import pytest

from agent.runner import run_command


def test_run_command_rejects_disallowed_command() -> None:
    with pytest.raises(ValueError, match="Befehl nicht erlaubt"):
        run_command("echo hallo")


def test_run_command_rejects_git_without_subcommand() -> None:
    with pytest.raises(ValueError, match="Git-Befehl ohne Subcommand"):
        run_command("git")


def test_run_command_rejects_disallowed_git_subcommand() -> None:
    with pytest.raises(ValueError, match="Git-Subcommand nicht erlaubt: checkout"):
        run_command("git checkout .")


def test_run_command_allows_git_status(monkeypatch: pytest.MonkeyPatch) -> None:
    def _run(*args, **kwargs):
        assert args[0] == ["git", "status"]
        return type(
            "CompletedProcess",
            (),
            {"returncode": 0, "stdout": "On branch main\n", "stderr": ""},
        )()

    monkeypatch.setattr("agent.runner.subprocess.run", _run)

    output = run_command("git status")

    assert "$ git status" in output
    assert "exit_code=0" in output
    assert "On branch main" in output


def test_run_command_handles_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("not found")

    monkeypatch.setattr("agent.runner.subprocess.run", _raise_file_not_found)

    output = run_command("ruff check .")

    assert "$ ruff check ." in output
    assert "exit_code=127" in output
    assert "Befehl nicht gefunden: ruff" in output


def test_run_command_rejects_black_path_outside_repo() -> None:
    with pytest.raises(ValueError, match="Pfad ausserhalb des Repositories nicht erlaubt"):
        run_command("black ../outside.py")


def test_run_command_rejects_pytest_nodeid_outside_repo() -> None:
    with pytest.raises(ValueError, match="Pfad ausserhalb des Repositories nicht erlaubt"):
        run_command("pytest ../outside.py::test_example")


def test_run_command_rejects_pytest_flag_value_outside_repo() -> None:
    with pytest.raises(ValueError, match="Pfad ausserhalb des Repositories nicht erlaubt"):
        run_command("pytest --junitxml=/etc/passwd tests/test_runner.py")


def test_run_command_rejects_ruff_flag_value_outside_repo() -> None:
    with pytest.raises(ValueError, match="Pfad ausserhalb des Repositories nicht erlaubt"):
        run_command("ruff check . --output-file=/tmp/../etc/evil.txt")


def test_run_command_allows_flag_value_inside_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    def _run(*args, **kwargs):
        return type(
            "CompletedProcess",
            (),
            {"returncode": 0, "stdout": "", "stderr": ""},
        )()

    monkeypatch.setattr("agent.runner.subprocess.run", _run)

    output = run_command("pytest --junitxml=report.xml tests/test_runner.py")

    assert "exit_code=0" in output
