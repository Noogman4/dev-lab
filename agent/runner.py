import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path("/workspaces/dev-lab").resolve()

ALLOWED_BASE_COMMANDS = {
    "pytest",
    "ruff",
    "black",
    "python",
    "ls",
    "cat",
    "git",
}


def run_command(command: str) -> str:
    parts = shlex.split(command)

    if not parts:
        raise ValueError("Leerer Befehl ist nicht erlaubt.")

    base = parts[0]

    if base not in ALLOWED_BASE_COMMANDS:
        raise ValueError(f"Befehl nicht erlaubt: {base}")

    result = subprocess.run(
        parts,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
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
