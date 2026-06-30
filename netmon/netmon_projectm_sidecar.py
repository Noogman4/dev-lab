"""Optional external projectM sidecar integration for the standalone radio app."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
import hashlib
import zipfile
from dataclasses import dataclass

from netmon.core.state import get_netmon_documents_dir, get_netmon_documents_subdir

PROJECTM_COMMAND_CANDIDATES = (
    "projectM-pulseaudio",
    "projectm-pulseaudio",
    "projectM",
    "projectm",
)
PROJECTM_APT_POLICY_PACKAGES = ("projectm", "projectm-pulseaudio", "libprojectm4")
PROJECTM_INSTALL_PACKAGES = ("projectm", "projectm-pulseaudio")
PROJECTM_FLATPAK_APP_ID = "net.sourceforge.projectM"
PROJECTM_FLATPAK_REF_CANDIDATES = (PROJECTM_FLATPAK_APP_ID, "projectM")
PROJECTM_FLATPAK_INSTALL_COMMAND = (
    "flatpak remote-add --if-not-exists flathub "
    "https://flathub.org/repo/flathub.flatpakrepo && "
    f"flatpak install -y flathub {PROJECTM_FLATPAK_APP_ID}"
)
PROJECTM_PROCESS_MATCH_TERMS = (
    "projectm-pulseaudio",
    "projectm",
    "net.sourceforge.projectm",
)
PROJECTM_FLATPAK_CONFIG_SUBDIR = os.path.join(
    ".var", "app", PROJECTM_FLATPAK_APP_ID, "config", "projectM"
)
PROJECTM_HOST_PRESET_DIR_CANDIDATES = (
    "/usr/share/projectM",
    "/usr/share/projectm",
    "/usr/local/share/projectM",
    "/usr/local/share/projectm",
)
PROJECTM_FLAT_SCAN_SUBDIR = ".netmon_projectm_flat_scan_v1"
PROJECTM_PRESET_EXTENSIONS = {".milk", ".prjm"}
PROJECTM_PRESET_ASSET_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tga",
    ".gif",
    ".dds",
    ".ppm",
    ".pgm",
}
PROJECTM_DOWNLOADED_PACKS_DIRNAME = "Downloaded Packs"


@dataclass
class ProjectMSidecarStatus:
    available: bool
    installed: bool
    installable: bool
    backend_id: str
    message: str
    launched: bool = False
    command: list[str] | None = None
    install_command: str = ""
    backend_label: str = ""
    install_strategy: str = "skip"


def get_projectm_preset_dir(app=None):
    if app is not None:
        cached = str(getattr(app, "radio_projectm_preset_dir", "") or "").strip()
        if cached:
            return cached
    path = os.path.join(get_netmon_documents_dir(), "projectM Visualizer", "Presets")
    if app is not None:
        app.radio_projectm_preset_dir = path
    return path


def ensure_projectm_preset_dir(app=None):
    path = get_projectm_preset_dir(app)
    if not path:
        return ""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        return ""
    _migrate_legacy_projectm_presets(app, path)
    _sync_projectm_flat_scan_dir(app, path)
    _sync_projectm_flatpak_playlist_file(app, path)
    return path


def _projectm_flat_scan_dir(preset_dir: str) -> str:
    return os.path.join(str(preset_dir or "").strip(), PROJECTM_FLAT_SCAN_SUBDIR)


def _iter_projectm_preset_files(preset_dir: str):
    root_dir = os.path.abspath(str(preset_dir or "").strip())
    if not root_dir or not os.path.isdir(root_dir):
        return
    flat_scan_dir = os.path.abspath(_projectm_flat_scan_dir(root_dir))
    for walk_root, _dirs, files in os.walk(root_dir):
        abs_walk_root = os.path.abspath(walk_root)
        if abs_walk_root == flat_scan_dir or abs_walk_root.startswith(flat_scan_dir + os.sep):
            continue
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in PROJECTM_PRESET_EXTENSIONS:
                continue
            source = os.path.join(walk_root, filename)
            if os.path.isfile(source):
                yield source


def _projectm_flat_scan_name(root_dir: str, source_path: str) -> str:
    rel_path = os.path.relpath(source_path, root_dir)
    base_name = os.path.basename(source_path)
    stem, ext = os.path.splitext(base_name)
    digest = hashlib.sha1(rel_path.encode("utf-8", errors="replace")).hexdigest()[:10]
    cleaned_stem = stem[:180].rstrip(" ._-") or "preset"
    return f"{cleaned_stem}__{digest}{ext.lower()}"


def _sync_projectm_flat_scan_dir(app, preset_dir: str) -> str:
    root_dir = os.path.abspath(str(preset_dir or "").strip())
    if not root_dir:
        return ""
    flat_dir = _projectm_flat_scan_dir(root_dir)
    try:
        os.makedirs(flat_dir, exist_ok=True)
    except Exception:
        return ""

    desired_links = {}
    for source_path in _iter_projectm_preset_files(root_dir) or ():
        link_name = _projectm_flat_scan_name(root_dir, source_path)
        desired_links[os.path.join(flat_dir, link_name)] = source_path

    existing_entries = []
    try:
        existing_entries = [
            os.path.join(flat_dir, name)
            for name in os.listdir(flat_dir)
        ]
    except Exception:
        existing_entries = []

    for entry_path in existing_entries:
        if entry_path in desired_links:
            continue
        try:
            if os.path.islink(entry_path) or os.path.isfile(entry_path):
                os.unlink(entry_path)
        except Exception:
            pass

    for link_path, source_path in desired_links.items():
        rel_target = os.path.relpath(source_path, os.path.dirname(link_path))
        try:
            if os.path.islink(link_path):
                current_target = os.readlink(link_path)
                if current_target == rel_target:
                    continue
                os.unlink(link_path)
            elif os.path.exists(link_path):
                continue
            os.symlink(rel_target, link_path)
        except Exception:
            try:
                if os.path.exists(link_path):
                    continue
                shutil.copy2(source_path, link_path)
            except Exception:
                continue
    return flat_dir


def _legacy_projectm_preset_dir(app=None):
    if app is not None:
        state_dir = str(getattr(app, "netmon_state_dir", "") or "").strip()
        if state_dir:
            return os.path.join(state_dir, "projectm_presets")
    return os.path.join(
        os.path.expanduser("~"), ".local", "state", "netmon", "projectm_presets"
    )


def _migrate_legacy_projectm_presets(app, target_dir):
    legacy_dir = _legacy_projectm_preset_dir(app)
    if not legacy_dir or os.path.abspath(legacy_dir) == os.path.abspath(target_dir):
        return
    if not os.path.isdir(legacy_dir):
        return
    try:
        entries = os.listdir(legacy_dir)
    except Exception:
        return
    for name in entries:
        source = os.path.join(legacy_dir, name)
        target = os.path.join(target_dir, name)
        if not os.path.isfile(source) or os.path.exists(target):
            continue
        try:
            shutil.copy2(source, target)
        except Exception:
            continue


def _sanitize_projectm_pack_name(name: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in {" ", "-", "_", "."} else "_"
        for char in str(name or "").strip()
    )
    cleaned = cleaned.strip(" ._-")
    return cleaned[:120] or "Preset Pack"


def _projectm_downloaded_packs_dir(preset_dir: str) -> str:
    return os.path.join(
        os.path.abspath(str(preset_dir or "").strip()),
        PROJECTM_DOWNLOADED_PACKS_DIRNAME,
    )


def _unique_projectm_pack_dir(root_dir: str, pack_name: str) -> str:
    safe_name = _sanitize_projectm_pack_name(pack_name)
    target_dir = os.path.join(root_dir, safe_name)
    if not os.path.exists(target_dir):
        return target_dir
    counter = 2
    while True:
        candidate = os.path.join(root_dir, f"{safe_name}_{counter}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def install_projectm_preset_archive(app, archive_path: str, pack_name: str = ""):
    preset_dir = ensure_projectm_preset_dir(app)
    if not preset_dir:
        raise RuntimeError("Preset directory could not be prepared.")
    archive_path = os.path.abspath(str(archive_path or "").strip())
    if not archive_path or not os.path.isfile(archive_path):
        raise FileNotFoundError("Preset archive not found.")
    if not zipfile.is_zipfile(archive_path):
        raise ValueError("Only ZIP preset packs are supported.")

    packs_root = _projectm_downloaded_packs_dir(preset_dir)
    os.makedirs(packs_root, exist_ok=True)
    target_root = _unique_projectm_pack_dir(
        packs_root,
        pack_name or os.path.splitext(os.path.basename(archive_path))[0],
    )
    os.makedirs(target_root, exist_ok=True)

    allowed_exts = PROJECTM_PRESET_EXTENSIONS | PROJECTM_PRESET_ASSET_EXTENSIONS
    imported_presets = 0
    imported_assets = 0
    imported_files = 0
    top_level_dirs = set()

    with zipfile.ZipFile(archive_path, "r") as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        parsed_members = []
        top_level_dirs = set()
        for member in members:
            raw_name = str(member.filename or "").replace("\\", "/").strip("/")
            if not raw_name:
                continue
            parts = [part for part in raw_name.split("/") if part not in {"", ".", ".."}]
            if not parts:
                continue
            parsed_members.append((member, parts))
            if len(parts) > 1:
                top_level_dirs.add(parts[0])
        strip_first_dir = len(top_level_dirs) == 1
        for member, parts in parsed_members:
            rel_parts = parts[1:] if strip_first_dir and len(parts) > 1 else parts
            rel_path = os.path.join(*rel_parts)
            ext = os.path.splitext(rel_path)[1].lower()
            if ext not in allowed_exts:
                continue
            target_path = os.path.abspath(os.path.join(target_root, rel_path))
            if not target_path.startswith(target_root + os.sep):
                continue
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                counter = 2
                while os.path.exists(target_path):
                    target_path = f"{base}_{counter}{ext}"
                    counter += 1
            with archive.open(member, "r") as source, open(target_path, "wb") as dest:
                shutil.copyfileobj(source, dest)
            imported_files += 1
            if ext in PROJECTM_PRESET_EXTENSIONS:
                imported_presets += 1
            else:
                imported_assets += 1

    if not imported_presets:
        shutil.rmtree(target_root, ignore_errors=True)
        raise ValueError("The selected ZIP file does not contain any .milk or .prjm presets.")

    _sync_projectm_flat_scan_dir(app, preset_dir)
    _sync_projectm_flatpak_playlist_file(app, preset_dir)
    return {
        "target_dir": target_root,
        "imported_files": imported_files,
        "imported_presets": imported_presets,
        "imported_assets": imported_assets,
    }


def _projectm_flatpak_config_files():
    config_root = os.path.join(os.path.expanduser("~"), PROJECTM_FLATPAK_CONFIG_SUBDIR)
    return [
        os.path.join(config_root, "qprojectM.conf"),
        os.path.join(config_root, "qprojectM-pulseaudio.conf"),
    ]


def _sync_projectm_flatpak_playlist_file(app, preset_dir):
    status = get_projectm_sidecar_status(app=app) if app is not None else None
    backend_label = str(getattr(status, "backend_label", "") or "").strip()
    if backend_label != "Flatpak":
        return
    playlist_dir = _sync_projectm_flat_scan_dir(app, preset_dir) or preset_dir
    for config_path in _projectm_flatpak_config_files():
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
        except Exception:
            continue
        try:
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as handle:
                    lines = handle.read().splitlines()
            else:
                lines = ["[General]"]
        except Exception:
            continue
        if not lines:
            lines = ["[General]"]
        if lines[0].strip() != "[General]":
            lines.insert(0, "[General]")
        updated = []
        playlist_written = False
        playlist_path_written = False
        for raw_line in lines:
            line = str(raw_line or "")
            if line.startswith("PlaylistFile="):
                updated.append(f"PlaylistFile={playlist_dir}")
                playlist_written = True
            elif line.startswith("playlistPath="):
                updated.append(f"playlistPath={playlist_dir}")
                playlist_path_written = True
            else:
                updated.append(line)
        if not playlist_written:
            updated.append(f"PlaylistFile={playlist_dir}")
        if not playlist_path_written:
            updated.append(f"playlistPath={playlist_dir}")
        try:
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(updated).rstrip() + "\n")
        except Exception:
            continue


def _collect_projectm_host_preset_mounts(app=None):
    mounts = []
    preset_dir = ensure_projectm_preset_dir(app)
    if preset_dir:
        mounts.append((preset_dir, "create"))
    for path in PROJECTM_HOST_PRESET_DIR_CANDIDATES:
        if os.path.isdir(path):
            mounts.append((path, "ro"))
    return mounts


def _build_projectm_launch_command(status, app=None):
    command = list(getattr(status, "command", []) or [])
    if not command:
        return []
    if not _is_flatpak_projectm_command(command):
        return command
    flatpak_path = str(command[0] or "").strip()
    app_id = str(command[-1] or "").strip()
    if not flatpak_path or not app_id:
        return command
    launch = [flatpak_path, "run"]
    for mount_path, mode in _collect_projectm_host_preset_mounts(app):
        suffix = ":create" if mode == "create" else ":ro"
        launch.append(f"--filesystem={mount_path}{suffix}")
    launch.append(app_id)
    return launch


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _legacy_projectm_log_candidates(app=None) -> tuple[str, ...]:
    candidates = []
    if app is not None:
        state_dir = str(getattr(app, "netmon_state_dir", "") or "").strip()
        if state_dir:
            candidates.append(
                os.path.join(state_dir, "logs", "projectm_visualizer.log")
            )
    candidates.append(os.path.join(_repo_root(), "logs", "projectm_visualizer.log"))
    return tuple(candidates)


def _migrate_legacy_projectm_log(app, target_path: str) -> None:
    if os.path.isfile(target_path):
        return
    for source in _legacy_projectm_log_candidates(app):
        if not source or os.path.abspath(source) == os.path.abspath(target_path):
            continue
        if not os.path.isfile(source):
            continue
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(source, target_path)
            return
        except Exception:
            continue


def _log_path(app=None):
    path = os.path.join(get_netmon_documents_subdir("Logs"), "projectm_visualizer.log")
    _migrate_legacy_projectm_log(app, path)
    return path


def _append_log(log_path, message):  # pragma: no cover - runtime-only path
    text = str(message or "").strip()
    if not text:
        return
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {text}\n")


def _read_flatpak_list_output(flatpak_path):
    try:
        completed = subprocess.run(
            [flatpak_path, "list"],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.stdout or completed.stderr or ""
    except Exception:
        return ""


def _flatpak_list_contains_projectm(text):
    lowered = str(text or "").lower()
    return any(
        candidate.lower() in lowered for candidate in PROJECTM_FLATPAK_REF_CANDIDATES
    )


def _detect_projectm_flatpak_command():
    flatpak_path = shutil.which("flatpak")
    if not flatpak_path:
        return []
    if _flatpak_list_contains_projectm(_read_flatpak_list_output(flatpak_path)):
        return [flatpak_path, "run", PROJECTM_FLATPAK_APP_ID]
    return []


def _detect_projectm_command():
    for command in PROJECTM_COMMAND_CANDIDATES:
        resolved = shutil.which(command)
        if resolved:
            return [resolved]
    return _detect_projectm_flatpak_command()


def _is_flatpak_projectm_command(command):
    parts = list(command or [])
    return len(parts) >= 3 and os.path.basename(str(parts[0])) == "flatpak"


def _read_process_rows():
    try:
        completed = subprocess.run(
            ["ps", "-eo", "pid=,ppid=,args="],
            check=False,
            capture_output=True,
            text=True,
        )
        output = completed.stdout or ""
    except Exception:
        output = ""
    rows = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except Exception:
            continue
        rows.append({"pid": pid, "ppid": ppid, "args": parts[2]})
    return rows


def _collect_descendant_pids(root_pid):
    if not root_pid:
        return set()
    rows = _read_process_rows()
    child_map = {}
    for row in rows:
        child_map.setdefault(int(row["ppid"]), set()).add(int(row["pid"]))
    found = set()
    pending = [int(root_pid)]
    while pending:
        parent = pending.pop()
        for child_pid in child_map.get(parent, set()):
            if child_pid in found:
                continue
            found.add(child_pid)
            pending.append(child_pid)
    return found


def _collect_matching_projectm_pids():
    rows = _read_process_rows()
    matches = set()
    for row in rows:
        args = str(row.get("args", "") or "").lower()
        if any(term in args for term in PROJECTM_PROCESS_MATCH_TERMS):
            matches.add(int(row["pid"]))
    return matches


def _collect_projectm_runtime_pids(proc, command):
    known = set()
    if proc is not None:
        try:
            known.add(int(proc.pid))
        except Exception:
            pass
    launcher_pid = int(proc.pid) if proc is not None else 0
    if launcher_pid:
        known.update(_collect_descendant_pids(launcher_pid))
    if _is_flatpak_projectm_command(command):
        known.update(_collect_matching_projectm_pids())
    return {pid for pid in known if int(pid) > 0}


def _signal_pid(pid, sig):
    try:
        os.kill(int(pid), sig)
        return True
    except Exception:
        return False


def _parse_apt_policy_output(text):
    data = {
        package: {"installed": "", "candidate": ""}
        for package in PROJECTM_APT_POLICY_PACKAGES
    }
    current = ""
    for raw_line in str(text or "").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if not raw_line.startswith(" ") and stripped.endswith(":"):
            package_name = stripped[:-1].strip()
            current = package_name if package_name in data else ""
            continue
        if not current:
            continue
        if stripped.startswith("Installed:"):
            data[current]["installed"] = stripped.partition(":")[2].strip()
        elif stripped.startswith("Candidate:"):
            data[current]["candidate"] = stripped.partition(":")[2].strip()
    available_packages = [
        package
        for package in PROJECTM_INSTALL_PACKAGES
        if str(data.get(package, {}).get("candidate", "") or "").strip()
        and str(data.get(package, {}).get("candidate", "") or "").strip() != "(none)"
    ]
    installable = bool(available_packages)
    return {
        "packages": data,
        "available_packages": available_packages,
        "apt_installable": installable,
        "installable": installable,
    }


def probe_projectm_package_candidates(app=None, refresh=False):
    cache = (
        getattr(app, "radio_projectm_package_probe", None) if app is not None else None
    )
    if cache and not refresh:
        return dict(cache)
    try:
        completed = subprocess.run(
            ["apt-cache", "policy", *PROJECTM_APT_POLICY_PACKAGES],
            check=False,
            capture_output=True,
            text=True,
        )
        output = completed.stdout or completed.stderr or ""
    except Exception:
        output = ""
    result = _parse_apt_policy_output(output)
    flatpak_path = shutil.which("flatpak") or ""
    flatpak_output = _read_flatpak_list_output(flatpak_path) if flatpak_path else ""
    flatpak_projectm_installed = _flatpak_list_contains_projectm(flatpak_output)
    result["raw_output"] = output
    result["checked_at"] = time.time()
    result["flatpak_available"] = bool(flatpak_path)
    result["flatpak_path"] = flatpak_path
    result["flatpak_list_output"] = flatpak_output
    result["flatpak_projectm_installed"] = flatpak_projectm_installed
    install_strategy = "skip"
    install_command = ""
    if result.get("apt_installable"):
        install_strategy = "apt"
        install_command = "sudo apt install -y " + " ".join(
            list(result.get("available_packages", []) or [])
        )
    elif flatpak_projectm_installed:
        install_strategy = "installed"
    elif flatpak_path:
        install_strategy = "flatpak"
        install_command = PROJECTM_FLATPAK_INSTALL_COMMAND
    else:
        install_strategy = "install_flatpak"
        install_command = (
            "sudo apt install -y flatpak && " + PROJECTM_FLATPAK_INSTALL_COMMAND
        )
    result["install_strategy"] = install_strategy
    result["install_command"] = install_command
    result["installable"] = install_strategy in {"apt", "flatpak", "install_flatpak"}
    if app is not None:
        app.radio_projectm_package_probe = dict(result)
    return result


def build_projectm_install_command(probe=None):
    info = dict(probe or {})
    command = str(info.get("install_command", "") or "").strip()
    if command:
        return command
    packages = list(info.get("available_packages", []) or [])
    if packages:
        return "sudo apt install -y " + " ".join(packages)
    return ""


def get_projectm_sidecar_status(app=None):
    binary_command = []
    for command in PROJECTM_COMMAND_CANDIDATES:
        resolved = shutil.which(command)
        if resolved:
            binary_command = [resolved]
            break
    probe = probe_projectm_package_candidates(app=app, refresh=not binary_command)
    flatpak_command = (
        [str(probe.get("flatpak_path") or "").strip(), "run", PROJECTM_FLATPAK_APP_ID]
        if probe.get("flatpak_projectm_installed") and probe.get("flatpak_path")
        else []
    )
    installable = bool(probe.get("installable", False))
    install_command = build_projectm_install_command(probe)
    install_strategy = str(probe.get("install_strategy", "skip") or "skip")
    if binary_command:
        return ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=installable,
            backend_id="projectm_external",
            message="projectM externer Test-Visualizer ist verfügbar.",
            launched=False,
            command=binary_command,
            install_command=install_command,
            backend_label="Binary",
            install_strategy=install_strategy,
        )
    if flatpak_command:
        return ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=installable,
            backend_id="projectm_external",
            message="projectM installiert (Flatpak)",
            launched=False,
            command=flatpak_command,
            install_command=install_command,
            backend_label="Flatpak",
            install_strategy=install_strategy,
        )
    return ProjectMSidecarStatus(
        available=False,
        installed=False,
        installable=installable,
        backend_id="projectm_external",
        message="projectM nicht installiert",
        launched=False,
        command=[],
        install_command=install_command,
        backend_label="",
        install_strategy=install_strategy,
    )


def launch_projectm_sidecar(app=None):
    status = get_projectm_sidecar_status(app=app)
    logger = getattr(app, "log_safe", None)
    if not status.installed or not status.command:
        if callable(logger):
            try:
                logger(f"projectM: {status.message}")
            except Exception:
                pass
        return status
    proc = getattr(app, "radio_projectm_proc", None)
    if proc is not None and proc.poll() is None:
        return ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=status.installable,
            backend_id="projectm_external",
            message="projectM läuft bereits.",
            launched=True,
            command=status.command,
            install_command=status.install_command,
        )

    launch_command = _build_projectm_launch_command(status, app=app)
    log_path = _log_path(app)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    _append_log(log_path, "projectM launch requested")
    _append_log(log_path, "Command: " + " ".join(launch_command))
    log_handle = open(log_path, "a", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            launch_command,
            cwd=_repo_root(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log_handle,
            start_new_session=True,
        )
    except Exception as exc:
        try:
            log_handle.close()
        except Exception:
            pass
        _append_log(log_path, f"projectM launch failed: {exc}")
        failed = ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=status.installable,
            backend_id="projectm_external",
            message=f"projectM konnte nicht gestartet werden: {exc}",
            launched=False,
            command=launch_command,
            install_command=status.install_command,
        )
        if callable(logger):
            try:
                logger(f"projectM: {failed.message}")
            except Exception:
                pass
        return failed

    time.sleep(0.25)
    if proc.poll() is not None:
        exit_code = proc.returncode
        try:
            log_handle.close()
        except Exception:
            pass
        _append_log(log_path, f"projectM exited immediately with code {exit_code}")
        failed = ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=status.installable,
            backend_id="projectm_external",
            message=f"projectM wurde sofort beendet (Code {exit_code}).",
            launched=False,
            command=launch_command,
            install_command=status.install_command,
        )
        if callable(logger):
            try:
                logger(f"projectM: {failed.message}")
            except Exception:
                pass
        return failed

    if app is not None:
        app.radio_projectm_proc = proc
        app.radio_projectm_command = list(launch_command)
        app.radio_projectm_log_handle = log_handle
        app.radio_projectm_log_path = log_path
        app.radio_projectm_known_pids = set()
    time.sleep(0.2)
    known_pids = _collect_projectm_runtime_pids(proc, launch_command)
    if app is not None:
        app.radio_projectm_known_pids = set(known_pids)
    if known_pids:
        _append_log(
            log_path,
            "projectM runtime PIDs: " + ", ".join(map(str, sorted(known_pids))),
        )
    _append_log(log_path, f"projectM started with PID {proc.pid}")
    if callable(logger):
        try:
            logger(f"projectM: gestartet (PID {proc.pid}).")
        except Exception:
            pass
    return ProjectMSidecarStatus(
        available=True,
        installed=True,
        installable=status.installable,
        backend_id="projectm_external",
        message="projectM läuft.",
        launched=True,
        command=launch_command,
        install_command=status.install_command,
    )


def stop_projectm_sidecar(app):
    proc = getattr(app, "radio_projectm_proc", None)
    log_handle = getattr(app, "radio_projectm_log_handle", None)
    command = list(getattr(app, "radio_projectm_command", []) or [])
    known_pids = set(getattr(app, "radio_projectm_known_pids", set()) or set())
    log_path = str(
        getattr(app, "radio_projectm_log_path", "") or _log_path(app)
    ).strip()
    if proc is None:
        if log_handle is not None:
            try:
                log_handle.close()
            except Exception:
                pass
            app.radio_projectm_log_handle = None
        app.radio_projectm_known_pids = set()
        return False
    terminated = False
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        terminated = True
        proc.wait(timeout=2.0)
    except Exception:
        terminated = False
    if proc.poll() is None and _is_flatpak_projectm_command(command):
        flatpak_path = shutil.which("flatpak")
        if flatpak_path:
            try:
                subprocess.run(
                    [flatpak_path, "kill", PROJECTM_FLATPAK_APP_ID],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                terminated = True
            except Exception:
                pass
            try:
                proc.wait(timeout=1.5)
            except Exception:
                pass
    if proc is not None:
        known_pids.update(_collect_projectm_runtime_pids(proc, command))
    known_pids.update(_collect_matching_projectm_pids())
    for pid in sorted({pid for pid in known_pids if pid and pid != os.getpid()}):
        if _signal_pid(pid, signal.SIGTERM):
            terminated = True
    time.sleep(0.3)
    for pid in sorted({pid for pid in known_pids if pid and pid != os.getpid()}):
        _signal_pid(pid, signal.SIGKILL)
    if proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            terminated = True
            proc.wait(timeout=1.0)
        except Exception:
            pass
    if log_path:
        _append_log(
            log_path, "projectM stopped" if terminated else "projectM stop requested"
        )
    app.radio_projectm_proc = None
    app.radio_projectm_command = []
    app.radio_projectm_known_pids = set()
    if log_handle is not None:
        try:
            log_handle.close()
        except Exception:
            pass
    app.radio_projectm_log_handle = None
    return True


def describe_projectm_sidecar_runtime(app):
    proc = getattr(app, "radio_projectm_proc", None)
    log_path = str(
        getattr(app, "radio_projectm_log_path", "") or _log_path(app)
    ).strip()
    if proc is not None and proc.poll() is not None:
        try:
            if getattr(app, "radio_projectm_log_handle", None) is not None:
                app.radio_projectm_log_handle.close()
        except Exception:
            pass
        app.radio_projectm_proc = None
        app.radio_projectm_log_handle = None
        proc = None
    status = get_projectm_sidecar_status(app=app)
    running = proc is not None and proc.poll() is None
    pid = int(proc.pid) if running else 0
    command = " ".join(
        getattr(app, "radio_projectm_command", []) or status.command or []
    )
    if running:
        status_text = "projectM: läuft"
    elif status.installed:
        status_text = "projectM: gestoppt"
    else:
        status_text = status.message
    backend_label = str(status.backend_label or "").strip()
    preset_dir = ensure_projectm_preset_dir(app)
    preset_mounts = _collect_projectm_host_preset_mounts(app)
    if status.installed and backend_label == "Flatpak":
        preset_access_text = (
            "Flatpak nutzt Dokumente/NetMon mit heruntergeladenen Preset-Packs und eigenen Imports."
            if preset_dir
            else "Kein freigegebener projectM-Preset-Ordner verfuegbar."
        )
    elif status.installed and backend_label == "Binary":
        preset_access_text = "System-Binary nutzt Dokumente/NetMon mit heruntergeladenen Preset-Packs und eigenen Imports."
    else:
        preset_access_text = (
            "Preset-Zugriff nach Installation ueber Dokumente/NetMon verfuegbar. Externe Packs koennen spaeter geladen werden."
        )
    if status.installed and backend_label:
        install_text = f"projectM Backend: {backend_label}"
    elif status.install_strategy == "apt":
        install_text = "projectM nicht installiert"
    elif status.install_strategy == "flatpak":
        install_text = (
            "projectM nicht als Paket gefunden. Flatpak-Installation optional."
        )
    elif status.install_strategy == "install_flatpak":
        install_text = (
            "projectM nicht gefunden. Flatpak kann optional installiert werden."
        )
    else:
        install_text = "projectM ist in deinen Paketquellen nicht verfügbar."
    return {
        "running": running,
        "installed": status.installed,
        "installable": status.installable,
        "pid": pid,
        "command": command,
        "log_path": log_path,
        "status_text": status_text,
        "install_text": install_text,
        "install_command": status.install_command,
        "backend_label": backend_label,
        "install_strategy": status.install_strategy,
        "preset_dir": preset_dir,
        "preset_mount_count": len(preset_mounts),
        "preset_access_text": preset_access_text,
    }
