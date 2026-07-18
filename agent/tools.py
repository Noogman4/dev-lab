from pathlib import Path
from typing import List

REPO_ROOT = Path("/workspaces/dev-lab").resolve()


def _ensure_repo_path(path: Path) -> Path:
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise PermissionError("Pfad liegt außerhalb des Repositories.") from exc
    return path


def list_files(path: str = ".") -> List[str]:
    target = _ensure_repo_path((REPO_ROOT / path).resolve())
    files = []

    for p in target.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            files.append(str(p.relative_to(REPO_ROOT)))

    return sorted(files)


def read_file(path: str) -> str:
    file_path = _ensure_repo_path((REPO_ROOT / path).resolve())

    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    return file_path.read_text(encoding="utf-8")
