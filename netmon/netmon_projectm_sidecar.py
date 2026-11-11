"""Optional external projectM sidecar integration for the standalone radio app."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import threading
import hashlib
from dataclasses import dataclass

from netmon.core import (
    projectm_archive,
    projectm_zip,
    projectm_process,
    projectm_frontend,
)
from netmon.core.projectm_import_plan import ImportPlan, path_key, sync_import_flat_scan
from netmon.core.archive_limits import ByteBudget, copy_limited
from netmon.core.state import get_netmon_documents_dir, get_netmon_documents_subdir
from netmon.core.projectm_profile import NEUTRAL_EQ

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
_PROCESS_LOCK = threading.RLock()
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
PROJECTM_PRESET_EXTENSIONS = projectm_zip.PRESET_EXTENSIONS
PROJECTM_PRESET_ASSET_EXTENSIONS = projectm_zip.ASSET_EXTENSIONS

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
    starting: bool = False


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
        if abs_walk_root == flat_scan_dir or abs_walk_root.startswith(
            flat_scan_dir + os.sep
        ):
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
    digest = hashlib.sha1(
        rel_path.encode("utf-8", errors="replace"), usedforsecurity=False
    ).hexdigest()[:10]
    cleaned_stem = (
        stem.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" ._-")
        or "preset"
    )
    return f"{cleaned_stem}__{digest}{ext.lower()}"


def _sync_projectm_flat_scan_dir(
    app, preset_dir: str, import_plan=None, target_root=""
) -> str:
    root_dir = os.path.abspath(str(preset_dir or "").strip())
    if not root_dir:
        return ""
    flat_dir = _projectm_flat_scan_dir(root_dir)
    if import_plan is not None:
        new_files = {
            os.path.join(target_root, *item.parts): path_key(item.parts)
            for item in import_plan.files
            if item.preset
        }
        return sync_import_flat_scan(
            root_dir,
            flat_dir,
            _iter_projectm_preset_files(root_dir) or (),
            _projectm_flat_scan_name,
            import_plan.budget,
            new_files,
        )
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
            os.path.join(flat_dir, name) for name in os.listdir(flat_dir)
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


def _migrate_legacy_projectm_presets(app, target_dir, import_budget=None):
    legacy_dir = _legacy_projectm_preset_dir(app)
    if not legacy_dir or os.path.abspath(legacy_dir) == os.path.abspath(target_dir):
        return
    if not os.path.isdir(legacy_dir):
        return
    try:
        entries = os.listdir(legacy_dir)
    except Exception:
        return
    copy_budget = ByteBudget(projectm_archive.MAX_TOTAL_BYTES)
    for name in entries:
        source = os.path.join(legacy_dir, name)
        target = os.path.join(target_dir, name)
        if not os.path.isfile(source) or os.path.exists(target):
            continue
        if import_budget is not None:
            import_budget.plan("legacy", target)
            import_budget.create("legacy", target)
            with open(target, "xb") as destination:
                import_budget.auxiliary_files.append(target)
                with open(source, "rb") as handle:
                    copy_limited(
                        handle,
                        destination,
                        projectm_archive.MAX_FILE_BYTES,
                        budget=copy_budget,
                    )
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


def install_projectm_preset_archive(app, archive_path: str, pack_name: str = ""):
    preset_dir = get_projectm_preset_dir(app)
    if not preset_dir:
        raise RuntimeError("Preset directory could not be prepared.")
    archive_path = os.path.abspath(str(archive_path or "").strip())
    if not archive_path or not os.path.isfile(archive_path):
        raise FileNotFoundError("Preset archive not found.")
    allowed_exts = PROJECTM_PRESET_EXTENSIONS | PROJECTM_PRESET_ASSET_EXTENSIONS
    imported_presets = 0
    imported_assets = 0
    imported_files = 0
    target_root = ""
    try:
        with projectm_zip.prepared_archive(archive_path) as prepared:
            parsed_members = prepared.members
            if not any(
                os.path.splitext(parts[-1])[1].lower() in PROJECTM_PRESET_EXTENSIONS
                for _, parts in parsed_members
            ):
                raise ValueError(
                    "The selected ZIP file does not contain any .milk or .prjm presets."
                )
            plan = ImportPlan(parsed_members, PROJECTM_PRESET_EXTENSIONS, allowed_exts)
            packs_root = _projectm_downloaded_packs_dir(preset_dir)
            if os.path.islink(preset_dir):
                raise ValueError("Preset directories must not be symlinks.")
            plan.budget.create("directory", "packs-root")
            os.makedirs(packs_root, exist_ok=True)
            if os.path.islink(packs_root):
                raise ValueError("Preset directories must not be symlinks.")
            # Exclusive creation: never reuse an existing pack, even after a race.
            safe_pack = _sanitize_projectm_pack_name(
                pack_name or os.path.splitext(os.path.basename(archive_path))[0]
            )
            suffix = 1
            while True:
                candidate = os.path.join(
                    packs_root,
                    safe_pack if suffix == 1 else f"{safe_pack}_{suffix}",
                )
                try:
                    os.mkdir(candidate, mode=0o700)
                except FileExistsError:
                    suffix += 1
                    continue
                target_root = candidate
                plan.budget.create("directory", "pack-root")
                break
            for key, parts in plan.directories.items():
                plan.budget.create("directory", key)
                os.mkdir(os.path.join(target_root, *parts), mode=0o700)
            budget = ByteBudget(projectm_archive.MAX_TOTAL_BYTES)
            for item in plan.files:
                target_path = os.path.abspath(os.path.join(target_root, *item.parts))
                if os.path.commonpath([target_root, target_path]) != target_root:
                    raise ValueError("Unsafe ZIP target path.")
                plan.budget.create("file", path_key(item.parts))
                with open(target_path, "xb") as dest:
                    prepared.copy_member(item.member, dest, budget)
                imported_files += 1
                if item.preset:
                    imported_presets += 1
                else:
                    imported_assets += 1
        _migrate_legacy_projectm_presets(app, preset_dir, import_budget=plan.budget)
        plan.budget.create("directory", "flat-root")
        _sync_projectm_flat_scan_dir(
            app, preset_dir, import_plan=plan, target_root=target_root
        )
    except BaseException:
        try:
            if target_root:
                plan.budget.rollback_auxiliary()
        finally:
            if target_root:
                shutil.rmtree(target_root)
        raise

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
    # Both callers have already synchronized the scan. Do not repeat an
    # unbudgeted rebuild after the archive import's budgeted synchronization.
    playlist_dir = _projectm_flat_scan_dir(preset_dir)
    if not os.path.isdir(playlist_dir):
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
            timeout=10,
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
            timeout=10,
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
    probe = probe_projectm_package_candidates(app=app)
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


class _ProjectMRequest:
    """One generation of asynchronous start; only its worker touches capsules."""

    def __init__(
        self,
        app,
        playback,
        preset_dir,
        previous=None,
        *,
        resolution="640x480",
        preset_name=None,
        cpu_profile="standard",
        backend="cpu",
        visual_eq=None,
    ):
        from netmon.core.projectm_profile import (
            NEUTRAL_EQ,
            resolve,
            resolve_backend,
            resolve_cpu,
            validate_visual_eq,
        )

        self._visual_eq = validate_visual_eq(
            NEUTRAL_EQ if visual_eq is None else visual_eq
        )
        self._visual_eq_pending = False
        self.resolution = resolve(resolution).key
        self.cpu_profile = resolve_cpu(cpu_profile).key
        self.backend = resolve_backend(backend)
        self._actual_backend = "pending"
        self._gpu_error = ""
        self._preset_name = preset_name
        self.app, self.playback, self.preset_dir = app, playback, preset_dir
        self.previous = previous
        self.cancelled = threading.Event()
        self.done = threading.Event()
        self._lock = threading.Lock()
        self.phase, self.message = "starting", "projectM: Start wird vorbereitet."
        self.pid = 0
        self.returncode = None
        self._presets = ()
        self._selected_preset = None
        self._preset_pending = False
        from netmon.core.projectm_pixels import FrameMailbox

        self.frames = FrameMailbox(self.resolution)
        self.thread = threading.Thread(
            target=self._run, name="projectm-owner", daemon=True
        )

    def snapshot(self):
        with self._lock:
            return self.phase, self.message, self.pid, self.returncode

    def poll(self):
        return self.snapshot()[3]

    def preset_state(self):
        with self._lock:
            return self._presets, self._selected_preset

    def render_state(self):
        with self._lock:
            return self._actual_backend, self._gpu_error

    @property
    def visual_eq(self):
        with self._lock:
            return self._visual_eq

    def set_visual_eq(self, eq):
        """Tk only queues the newest EQ; the owner thread writes it."""
        from netmon.core.projectm_profile import validate_visual_eq

        try:
            validate_visual_eq(eq)
        except ValueError:
            return False
        if self._invalid():
            return False
        with self._lock:
            self._visual_eq = eq
            self._visual_eq_pending = True
        return True

    def select_preset(self, index):
        """Tk only queues the newest choice; the owner writes to the renderer."""
        if self._invalid():
            return False
        with self._lock:
            if self.phase != "running" or (
                index is not None
                and (type(index) is not int or not 0 <= index < len(self._presets))
            ):
                return False
            self._selected_preset = index
            self._preset_name = None if index is None else self._presets[index]
            self._preset_pending = True
        return True

    def selected_preset_name(self):
        with self._lock:
            return self._preset_name

    def stop(self):
        self.cancelled.set()
        with self._lock:
            if self.returncode is None:
                self.phase, self.message = "stopping", "projectM: wird beendet."
        return True

    def _invalid(self):
        with _PROCESS_LOCK:
            state = vars(self.app)
            return (
                self.cancelled.is_set()
                or state.get("radio_projectm_proc") is not self
                or state.get("radio_proc") is not self.playback
                or state.get("radio_stop_requested", False)
                or state.get("_radio_panel_destroying", False)
                or state.get("_projectm_closing", False)
            )

    def _run(self):
        session = None
        code, message = 0, "projectM: gestoppt."
        try:
            # A rapid stop/start waits for the older owner to finish cleanup.
            older = self.previous
            while older is not None:
                while not older.done.wait(0.05):
                    if self._invalid():
                        return
                older = older.previous
            self.previous = None
            if self._invalid():
                return
            backend_options = {} if self.backend == "cpu" else {"backend": self.backend}
            with self._lock:
                start_eq, self._visual_eq_pending = self._visual_eq, False
            if start_eq != NEUTRAL_EQ:
                backend_options["visual_eq"] = start_eq
            session = projectm_frontend.start(
                self.playback,
                self.preset_dir,
                cancelled=self._invalid,
                resolution=self.resolution,
                preset_name=self._preset_name,
                cpu_profile=self.cpu_profile,
                **backend_options,
            )
            if not isinstance(session, projectm_frontend.FrontendSession):
                raise RuntimeError("Unbekanntes projectM-Startresultat abgelehnt.")
            if session.pixels is None:
                raise RuntimeError("projectM ohne privaten Pixelstrom abgelehnt.")
            if getattr(session, "resolution", "640x480") != self.resolution:
                raise RuntimeError("projectM mit falschem Auflösungsprofil abgelehnt.")
            if getattr(session, "cpu_profile", "standard") != self.cpu_profile:
                raise RuntimeError("projectM mit falschem CPU-Profil abgelehnt.")
            actual_backend = getattr(session, "backend", "cpu")
            if actual_backend not in {"cpu", "gpu"} or (
                self.backend != "auto" and self.backend != actual_backend
            ):
                raise RuntimeError("projectM mit falschem Renderweg abgelehnt.")
            self.frames = session.pixels.frames
            if self._invalid():
                return
            if session.poll() is not None:
                raise RuntimeError(
                    "Privater projectM-Verbund wurde vor der Statusuebernahme beendet."
                )
            with _PROCESS_LOCK:
                if self._invalid():
                    return
                with self._lock:
                    self._presets = getattr(session, "presets", ())
                    self._selected_preset = getattr(session, "selected_preset", None)
                    self._preset_name = (
                        self._presets[self._selected_preset]
                        if self._selected_preset is not None
                        else None
                    )
                    self.pid = session.pid
                    self._actual_backend = actual_backend
                    self._gpu_error = getattr(session, "gpu_error", "")
                    self.phase, self.message = (
                        "running",
                        "projectM: gestartet ("
                        + ("GPU" if actual_backend == "gpu" else "CPU")
                        + ("; GPU nicht verfügbar" if self._gpu_error else "")
                        + ").",
                    )
            # Keep the Popen creator alive: Bubblewrap's parent is this thread.
            while not self.cancelled.wait(0.05):
                if self._invalid():
                    break
                with self._lock:
                    pending, selected = self._preset_pending, self._selected_preset
                    self._preset_pending = False
                    eq_pending, eq = self._visual_eq_pending, self._visual_eq
                    self._visual_eq_pending = False
                if pending:
                    session.select_preset(selected)
                if eq_pending:
                    session.set_visual_eq(eq)
                result = session.poll()
                if result is not None:
                    code = result
                    message = (
                        "projectM: beendet."
                        if result == 0
                        else "projectM: privater Verbund wurde beendet (Fehler)."
                    )
                    break
        except Exception as exc:
            if not self._invalid():
                code, message = 2, f"projectM: geschuetzter Start fehlgeschlagen: {exc}"
        finally:
            try:
                if isinstance(session, projectm_frontend.FrontendSession):
                    session.stop()
            except Exception as exc:
                code, message = 2, f"projectM: Bereinigung fehlgeschlagen: {exc}"
            if self.cancelled.is_set() and not code:
                message = "projectM: gestoppt."
            with self._lock:
                self.pid = 0
                self.returncode = code
                self.phase, self.message = ("error" if code else "stopped"), message
            self.done.set()


def launch_projectm_sidecar(app=None):
    if app is None:
        return ProjectMSidecarStatus(
            False,
            False,
            False,
            "projectm_private",
            "projectM-Start ohne Besitzer abgelehnt.",
        )
    with _PROCESS_LOCK:
        state = vars(app)
        playback = state.get("radio_proc")
        from netmon.core.radio_sandbox import SandboxProcess

        if (
            not isinstance(playback, SandboxProcess)
            or state.get("_projectm_closing", False)
            or state.get("_radio_panel_destroying", False)
        ):
            return ProjectMSidecarStatus(
                False,
                False,
                False,
                "projectm_private",
                "projectM benoetigt aktive geschuetzte NetMon-Wiedergabe.",
            )
        previous = state.get("radio_projectm_proc")
        if (
            isinstance(previous, _ProjectMRequest)
            and not previous.done.is_set()
            and not previous.cancelled.is_set()
            and previous.playback is playback
        ):
            running = previous.snapshot()[0] == "running"
            return ProjectMSidecarStatus(
                True,
                running,
                False,
                "projectm_private",
                (
                    "projectM laeuft bereits."
                    if running
                    else "projectM-Start laeuft bereits."
                ),
                launched=running,
                starting=not running,
            )
        if previous is not None and not isinstance(previous, _ProjectMRequest):
            # Old/foreign objects cannot be adopted as protected sessions.
            return ProjectMSidecarStatus(
                False,
                False,
                False,
                "projectm_private",
                "projectM: vorhandenen alten Prozess zuerst beenden.",
            )
        if isinstance(previous, _ProjectMRequest):
            previous.stop()
        request = _ProjectMRequest(
            app,
            playback,
            get_projectm_preset_dir(app),
            previous,
            resolution=state.get("_projectm_resolution", "640x480"),
            cpu_profile=state.get("_projectm_cpu_profile", "standard"),
            backend=state.get("_projectm_backend", "auto"),
            visual_eq=state.get("_projectm_visual_eq"),
        )
        app.radio_projectm_proc = request
        app.radio_projectm_command = []
        try:
            request.thread.start()
        except Exception:
            request.returncode = 2
            request.phase, request.message = (
                "error",
                "projectM: Start-Worker konnte nicht gestartet werden.",
            )
            request.done.set()
            return ProjectMSidecarStatus(
                False, False, False, "projectm_private", request.message
            )
        return ProjectMSidecarStatus(
            True,
            False,
            False,
            "projectm_private",
            "projectM-Start wird vorbereitet.",
            starting=True,
        )


def change_projectm_resolution(app, current, resolution):
    from netmon.core.projectm_profile import resolve

    return _change_projectm_profile(app, current, resolution=resolve(resolution).key)


def change_projectm_cpu_profile(app, current, cpu_profile):
    from netmon.core.projectm_profile import resolve_cpu

    return _change_projectm_profile(
        app, current, cpu_profile=resolve_cpu(cpu_profile).key
    )


def change_projectm_backend(app, current, backend):
    from netmon.core.projectm_profile import resolve_backend

    return _change_projectm_profile(app, current, backend=resolve_backend(backend))


def _change_projectm_profile(
    app, current, *, resolution=None, cpu_profile=None, backend=None
):
    """Replace only the visualizer owner; its successor waits for complete cleanup."""
    with _PROCESS_LOCK:
        if (
            not isinstance(current, _ProjectMRequest)
            or current._invalid()
            or current.done.is_set()
        ):
            return None
        resolution = current.resolution if resolution is None else resolution
        cpu_profile = current.cpu_profile if cpu_profile is None else cpu_profile
        backend = current.backend if backend is None else backend
        if (
            current.resolution == resolution
            and current.cpu_profile == cpu_profile
            and current.backend == backend
        ):
            return current
        request = _ProjectMRequest(
            app,
            current.playback,
            current.preset_dir,
            current,
            resolution=resolution,
            cpu_profile=cpu_profile,
            backend=backend,
            preset_name=current.selected_preset_name(),
            visual_eq=current.visual_eq,
        )
        current.stop()
        app.radio_projectm_proc = request
        app._projectm_resolution = resolution
        app._projectm_cpu_profile = cpu_profile
        app._projectm_backend = backend
        try:
            request.thread.start()
        except Exception:
            request.returncode = 2
            request.phase, request.message = (
                "error",
                "projectM: Profilwechsel fehlgeschlagen.",
            )
            request.done.set()
        return request


def invalidate_projectm_playback(app, playback=None):
    """Revoke before teardown; an old EOF may not cancel a newer playback."""
    with _PROCESS_LOCK:
        request = vars(app).get("radio_projectm_proc")
        if isinstance(request, _ProjectMRequest) and (
            playback is None or request.playback is playback
        ):
            request.stop()
            return True
    return False


def stop_projectm_sidecar(app):
    with _PROCESS_LOCK:
        proc = getattr(app, "radio_projectm_proc", None)
        if proc is None:
            return False
        if isinstance(proc, _ProjectMRequest):
            return proc.stop()
        # Old PID lists and command names confer no authority to signal.
        if not isinstance(proc, projectm_process.OwnedProcess):
            return False
        if not proc.stop():
            return False
        log_path = str(getattr(app, "radio_projectm_log_path", "") or "").strip()
        app.radio_projectm_proc = None
        app.radio_projectm_command = []
        app.radio_projectm_known_pids = set()
        log_handle = getattr(app, "radio_projectm_log_handle", None)
        if log_handle is not None:
            try:
                log_handle.close()
            except OSError:
                pass
        app.radio_projectm_log_handle = None
        if log_path:
            try:
                _append_log(log_path, "projectM owned processes stopped")
            except OSError:
                pass
        return True


def _detected_status(app):
    """Package discovery runs off Tk; the UI only receives cached metadata."""
    with _PROCESS_LOCK:
        data = vars(app)
        cached = data.get("_projectm_detected_status")
        if not data.get("_projectm_probe_pending") and (
            cached is None
            or time.monotonic() - data.get("_projectm_probe_time", 0) > 60
        ):
            data["_projectm_probe_pending"] = True

            def probe():
                try:
                    probe_projectm_package_candidates(app=app, refresh=True)
                    result = get_projectm_sidecar_status(app=app)
                except Exception:
                    result = ProjectMSidecarStatus(
                        False,
                        False,
                        False,
                        "projectm_private",
                        "projectM: Paketerkennung fehlgeschlagen.",
                    )
                try:
                    with _PROCESS_LOCK:
                        data["_projectm_detected_status"] = result
                        data["_projectm_probe_time"] = time.monotonic()
                finally:
                    with _PROCESS_LOCK:
                        data["_projectm_probe_pending"] = False

            try:
                threading.Thread(
                    target=probe, name="projectm-detect", daemon=True
                ).start()
            except RuntimeError:
                cached = ProjectMSidecarStatus(
                    False,
                    False,
                    False,
                    "projectm_private",
                    "projectM: Paketerkennung konnte nicht gestartet werden.",
                )
                data["_projectm_detected_status"] = cached
                data["_projectm_probe_time"] = time.monotonic()
                data["_projectm_probe_pending"] = False
        return cached


def describe_projectm_sidecar_runtime(app):
    status = _detected_status(app)
    with _PROCESS_LOCK:
        data = vars(app)
        proc = data.get("radio_projectm_proc")
        phase, message, pid = "stopped", "projectM: gestoppt", 0
        if isinstance(proc, _ProjectMRequest):
            phase, message, pid, _ = proc.snapshot()
        elif proc is not None:
            # Legacy ownership objects remain stoppable, never a protected state.
            message = "projectM: alter Prozess; zuerst beenden."
        running = phase == "running"
        installed = bool(status and status.installed) or running
        if proc is None and status is None:
            message = "projectM: Verfuegbarkeit wird geprueft."
        elif proc is None and status and not status.installed:
            message = status.message
        return {
            "running": running,
            "starting": phase == "starting",
            "phase": phase,
            "polling": bool(data.get("_projectm_probe_pending"))
            or phase in {"starting", "running", "stopping"},
            "installed": installed,
            "installable": bool(status and status.installable),
            "pid": pid,
            "command": (
                "projectM-pulseaudio (privates Profil)"
                if isinstance(proc, _ProjectMRequest)
                else ""
            ),
            "log_path": data.get("radio_projectm_log_path", ""),
            "status_text": message,
            "install_text": (
                "projectM-Paket erkannt; privates Profil wird beim Start geprueft."
                if installed
                else "Paketerkennung laeuft." if status is None else status.message
            ),
            "install_command": status.install_command if status else "",
            "backend_label": (
                "Privates Qt5-Profil"
                if isinstance(proc, _ProjectMRequest)
                else status.backend_label if status else ""
            ),
            "install_strategy": status.install_strategy if status else "skip",
            "preset_dir": get_projectm_preset_dir(app),
            "preset_mount_count": 0,
            "preset_access_text": "Private lesende Kopie aus heruntergeladenen Preset-Packs und eigenen Imports; kein Benutzerordner im Renderer.",
            "sandbox_state": "started" if running else phase,
            "runtime_verified": False,
        }
