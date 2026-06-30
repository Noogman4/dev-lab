"""Fun tab launcher helpers for NetMon."""

from __future__ import annotations

import os
import subprocess
import threading

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread



def _tr(app, key, default):
    try:
        return app.tr(key, default)
    except Exception:
        return default


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_list(app, name: str):
    return list(_app_value(app, name, []) or [])


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _fun_dep_status(app) -> dict:
    return _app_value(app, "dep_status", {}) or {}


def _fun_dep_enabled(app, name: str, default=False) -> bool:
    return bool(_fun_dep_status(app).get(name, default))


def _ensure_games_dir(app):
    path = str(_app_value(app, "fun_games_dir", "") or "").strip()
    if not path:
        return ""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _is_allowed_game_launcher_path(app, path: str) -> bool:
    games_dir = _ensure_games_dir(app)
    raw_path = str(path or "").strip()
    if not games_dir or not raw_path:
        return False
    try:
        games_root = os.path.realpath(os.path.expanduser(games_dir))
        candidate = os.path.realpath(os.path.expanduser(raw_path))
    except Exception:
        return False
    if not candidate.endswith(".py") or os.path.basename(candidate) == "__init__.py":
        return False
    if candidate != games_root and not candidate.startswith(games_root + os.sep):
        return False
    safe_path_check = getattr(app, "_is_safe_netmon_managed_path", None)
    if callable(safe_path_check):
        try:
            if not safe_path_check(games_root):
                return False
        except Exception:
            return False
    return os.path.isfile(candidate)


def _selected_game_id(app):
    table = _app_value(app, "fun_games_table")
    if table is None:
        return ""
    try:
        selection = table.selection()
    except Exception:
        return ""
    if not selection:
        return ""
    return str(selection[0] or "").strip()


def _game_name_from_path(path: str) -> str:
    filename = os.path.basename(path)
    stem, _ext = os.path.splitext(filename)
    if stem.lower() in {"main", "game", "run_game"}:
        stem = os.path.basename(os.path.dirname(path)) or stem
    return stem.replace("_", " ").replace("-", " ").strip().title() or "Spiel"


def _game_by_id(app, game_id: str):
    selected_id = str(game_id or "").strip()
    if not selected_id:
        return None
    for game in _app_list(app, "fun_games"):
        if str(game.get("id", "") or "").strip() == selected_id:
            return game
    return None


def discover_fun_games(app):
    games_dir = _ensure_games_dir(app)
    if not games_dir:
        return []

    python_ready = _fun_dep_enabled(app, "python3", default=True)
    rows = []
    for root, _dirs, files in os.walk(games_dir):
        for filename in sorted(files):
            if not filename.endswith(".py") or filename == "__init__.py":
                continue
            path = os.path.join(root, filename)
            if not _is_allowed_game_launcher_path(app, path):
                continue
            game_id = os.path.relpath(path, games_dir).replace(os.sep, "::")
            rows.append(
                {
                    "id": game_id,
                    "name": _game_name_from_path(path),
                    "source": "Code the Classics",
                    "status": (
                        _tr(app, "fun_status_ready", "Bereit")
                        if python_ready
                        else _tr(app, "fun_status_python_missing", "Python fehlt")
                    ),
                    "start": (
                        _tr(app, "fun_start_yes", "Ja")
                        if python_ready
                        else _tr(app, "fun_start_no", "Nein")
                    ),
                    "path": path,
                }
            )
    rows.sort(key=lambda item: (item["name"].lower(), item["path"].lower()))
    return rows


def _current_running_id(app):
    current = _app_value(app, "fun_current_game")
    if isinstance(current, dict):
        return str(current.get("id", "") or "")
    return ""


def _is_current_game_running(app, game_id: str) -> bool:
    current_running = _current_running_id(app)
    return bool(
        game_id
        and game_id == current_running
        and _app_value(app, "fun_game_proc") is not None
    )


def _set_fun_status(app, key: str, default: str, **kwargs) -> bool:
    text = _tr(app, key, default)
    if kwargs:
        text = text.format(**kwargs)
    return _app_var_set(app, "fun_status_var", text)


def _fun_game_row_values(app, game, current_running: str):
    game_id = str(game.get("id", "") or "").strip()
    return (
        game.get("name", ""),
        game.get("source", ""),
        (
            _tr(app, "fun_status_running", "Läuft")
            if _is_current_game_running(app, game_id)
            else game.get("status", "")
        ),
        (
            _tr(app, "fun_start_yes", "Ja")
            if game_id == current_running
            else game.get("start", "")
        ),
    )


def update_fun_games_table(app):
    table = _app_value(app, "fun_games_table")
    if table is None:
        return

    current_running = _current_running_id(app)
    previous_selection = _selected_game_id(app)
    try:
        for item in table.get_children():
            table.delete(item)
    except Exception:
        return

    for game in _app_list(app, "fun_games"):
        game_id = str(game.get("id", "") or "").strip()
        if not game_id:
            continue
        values = _fun_game_row_values(app, game, current_running)
        try:
            table.insert("", "end", iid=game_id, values=values)
        except Exception:
            pass

    selected = previous_selection or current_running
    if selected:
        try:
            table.selection_set(selected)
            table.see(selected)
        except Exception:
            pass


def update_fun_dependency_state(app):
    messages = []
    if not _fun_dep_enabled(app, "python3"):
        messages.append(_tr(app, "fun_dep_python_missing", "python3 fehlt"))
    if not _fun_dep_enabled(app, "pygame_module"):
        messages.append(_tr(app, "fun_dep_pygame_missing", "pygame fehlt"))
    if not _fun_dep_enabled(app, "pgzero_module"):
        messages.append(_tr(app, "fun_dep_pgzero_missing", "pgzero fehlt"))

    hint = (
        _tr(app, "fun_dep_ready", "Fun-Launcher bereit.")
        if not messages
        else " | ".join(messages)
    )
    _app_var_set(app, "fun_dependency_var", hint)


def refresh_fun_games(app):
    app.fun_games = discover_fun_games(app)
    update_fun_games_table(app)
    update_fun_dependency_state(app)
    count = len(_app_list(app, "fun_games"))
    _app_var_set(
        app,
        "fun_status_var",
        _tr(app, "fun_status_count", "Spiele: {count}").format(count=count),
    )
    _app_var_set(
        app,
        "fun_hint_var",
        _tr(
            app,
            "fun_hint_path",
            "Spieleordner: {path}",
        ).format(path=_ensure_games_dir(app)),
    )


def _resolve_selected_game(app):
    return _game_by_id(app, _selected_game_id(app))


def open_fun_games_folder(app):
    folder = _ensure_games_dir(app)
    if not folder:
        return False
    if _fun_dep_enabled(app, "xdg-open"):
        try:
            subprocess.Popen(
                ["xdg-open", folder],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception:
            pass
    try:
        app.log_safe(folder)
    except Exception:
        pass
    return False


def start_selected_game(app):
    game = _resolve_selected_game(app)
    if game is None:
        _set_fun_status(app, "fun_status_no_game", "Kein Spiel ausgewählt.")
        return False

    if not _fun_dep_enabled(app, "python3"):
        _set_fun_status(app, "fun_status_python_missing", "Python fehlt")
        return False
    game_path = str(game.get("path", "") or "").strip()
    if not _is_allowed_game_launcher_path(app, game_path):
        _set_fun_status(app, "fun_status_start_failed", "Start fehlgeschlagen: {error}", error="unsicherer Spielpfad")
        return False

    try:
        proc = subprocess.Popen(
            ["python3", game_path],
            cwd=os.path.dirname(game_path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        _set_fun_status(
            app,
            "fun_status_start_failed",
            "Start fehlgeschlagen: {error}",
            error=exc,
        )
        try:
            app.log_safe(f"Fun-Launcher Fehler: {exc}")
        except Exception:
            pass
        return False

    app.fun_game_proc = proc
    app.fun_current_game = dict(game)
    update_fun_games_table(app)
    _set_fun_status(
        app,
        "fun_status_started",
        "Spiel gestartet: {name}",
        name=game.get("name", ""),
    )

    def monitor():
        try:
            proc.wait()
        except Exception:
            pass

        def finalize():
            if _app_value(app, "fun_game_proc") is proc:
                app.fun_game_proc = None
                app.fun_current_game = None
                update_fun_games_table(app)
                _set_fun_status(app, "fun_status_stopped", "Spiel gestoppt.")

        try:
            call_in_ui_thread(app, finalize)
        except Exception:
            finalize()

    threading.Thread(target=monitor, daemon=True).start()
    return True


def stop_running_game(app):
    proc = _app_value(app, "fun_game_proc")
    if proc is None:
        _set_fun_status(app, "fun_status_not_running", "Kein Spiel läuft.")
        return False
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    app.fun_game_proc = None
    app.fun_current_game = None
    update_fun_games_table(app)
    _set_fun_status(app, "fun_status_stopped", "Spiel gestoppt.")
    return True
