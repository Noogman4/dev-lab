import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_BASE_COMMANDS = {
    "pytest",
    "ruff",
    "black",
    "ls",
    "git",
}

ALLOWED_GIT_SUBCOMMANDS = {
    "status",
    "diff",
    "log",
    "show",
}


def _flag_value(value: str) -> str:
    """Return the payload of a ``--flag=value`` argument, else the value itself."""
    text = str(value or "").strip()
    if text.startswith("-") and "=" in text:
        return text.partition("=")[2].strip()
    return text


def _is_repo_confined_path(value: str) -> bool:
    text = _flag_value(value)
    if not text:
        return False
    candidate = text.split("::", 1)[0].strip()
    if not candidate:
        return False
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        resolved = path.resolve(strict=False)
        resolved.relative_to(REPO_ROOT)
    except Exception:
        return False
    return True


def _looks_like_path_argument(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.startswith("-"):
        # Only flags of the form --flag=value can smuggle a path; a bare flag
        # (or a flag whose value is a separate token) is handled elsewhere.
        if "=" not in text:
            return False
        return _looks_like_path_argument(_flag_value(text))
    if text in {".", ".."}:
        return True
    path_candidate = text.split("::", 1)[0].strip()
    if "/" in path_candidate or path_candidate.startswith("."):
        return True
    return path_candidate.endswith((".py", ".toml", ".txt", ".md"))


def _validate_repo_confined_arguments(parts: list[str]) -> None:
    if not parts:
        return
    base = parts[0]
    if base == "black":
        for arg in parts[1:]:
            if _looks_like_path_argument(arg) and not _is_repo_confined_path(arg):
                raise ValueError(f"Pfad ausserhalb des Repositories nicht erlaubt: {arg}")
        return
    if base == "ruff":
        for arg in parts[1:]:
            if _looks_like_path_argument(arg) and not _is_repo_confined_path(arg):
                raise ValueError(f"Pfad ausserhalb des Repositories nicht erlaubt: {arg}")
        return
    if base == "pytest":
        for arg in parts[1:]:
            if _looks_like_path_argument(arg) and not _is_repo_confined_path(arg):
                raise ValueError(f"Pfad ausserhalb des Repositories nicht erlaubt: {arg}")
        return
    if base == "ls":
        for arg in parts[1:]:
            if _looks_like_path_argument(arg) and not _is_repo_confined_path(arg):
                raise ValueError(f"Pfad ausserhalb des Repositories nicht erlaubt: {arg}")


def run_command(command: str) -> str:
    parts = shlex.split(command)

    if not parts:
        raise ValueError("Leerer Befehl ist nicht erlaubt.")

    base = parts[0]

    if base not in ALLOWED_BASE_COMMANDS:
        raise ValueError(f"Befehl nicht erlaubt: {base}")
    if base == "git":
        if len(parts) < 2:
            raise ValueError("Git-Befehl ohne Subcommand ist nicht erlaubt.")
        subcommand = parts[1]
        if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
            raise ValueError(f"Git-Subcommand nicht erlaubt: {subcommand}")
    _validate_repo_confined_arguments(parts)

    try:
        result = subprocess.run(
            parts,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "\n".join(
            [
                f"$ {command}",
                "exit_code=127",
                "STDERR:",
                f"Befehl nicht gefunden: {base}",
            ]
        )

    output = []
    output.append(f"$ {command}")
    output.append(f"exit_code={result.returncode}")

    if result.stdout:
        output.append("STDOUT:")
        output.append(result.stdout.rstrip())

    if result.stderr:
        output.append("STDERR:")
        output.append(result.stderr.rstrip())

    return "\n".join(output)
