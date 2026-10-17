"""Plan names and filesystem-object budgets before creating preset outputs."""

from dataclasses import dataclass
import os
from pathlib import PureWindowsPath
import sys
import unicodedata

from netmon.core.archive_limits import ByteBudget, copy_limited
from netmon.core.projectm_archive import MAX_FILE_BYTES, MAX_TOTAL_BYTES

# Preserve capacity for 50,000 flat presets plus their flat-scan entries and
# three root directories. Implicit directories consume this same object budget.
MAX_OUTPUT_OBJECTS = 100_003
MAX_OUTPUT_DIRECTORIES = 2_048


def path_key(parts):
    normalized = tuple(
        os.path.normcase(unicodedata.normalize("NFC", part)) for part in parts
    )
    if sys.platform == "darwin":
        normalized = tuple(part.casefold() for part in normalized)
    return normalized


class ObjectBudget:
    def __init__(self):
        self.planned = set()
        self.directories = 0
        self.created = set()
        self.created_directories = 0
        self.auxiliary_files = []
        self.auxiliary_directory = ""

    def plan(self, kind, key):
        item = (kind, key)
        if item in self.planned:
            return
        if len(self.planned) >= MAX_OUTPUT_OBJECTS:
            raise ValueError("Preset filesystem object budget exceeded.")
        if kind == "directory":
            if self.directories >= MAX_OUTPUT_DIRECTORIES:
                raise ValueError("Preset directory object budget exceeded.")
            self.directories += 1
        self.planned.add(item)

    def create(self, kind, key):
        item = (kind, key)
        if (
            item not in self.planned
            or item in self.created
            or len(self.created) >= MAX_OUTPUT_OBJECTS
        ):
            raise ValueError("Unplanned or excessive preset filesystem object.")
        if kind == "directory":
            if self.created_directories >= MAX_OUTPUT_DIRECTORIES:
                raise ValueError("Preset directory object budget exceeded.")
            self.created_directories += 1
        self.created.add(item)

    def rollback_auxiliary(self):
        for path in reversed(self.auxiliary_files):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        if self.auxiliary_directory:
            os.rmdir(self.auxiliary_directory)


@dataclass(frozen=True)
class PlannedFile:
    member: object
    parts: tuple[str, ...]
    preset: bool


class ImportPlan:
    def __init__(self, parsed_members, preset_extensions, allowed_extensions):
        self.budget = ObjectBudget()
        for root in ("pack-root", "packs-root", "flat-root"):
            self.budget.plan("directory", root)
        self.directories = {}
        self.reserved = set()
        self.next_suffix = 2
        self.files = []
        top = {parts[0] for _, parts in parsed_members if len(parts) > 1}
        strip = len(top) == 1
        selected = []
        for member, parts in parsed_members:
            parts = tuple(parts[1:] if strip and len(parts) > 1 else parts)
            if os.path.splitext(parts[-1])[1].lower() not in allowed_extensions:
                continue
            for part in parts:
                if len(os.fsencode(part)) > 255 or (
                    os.name == "nt"
                    and (
                        part.endswith((" ", ".")) or PureWindowsPath(part).is_reserved()
                    )
                ):
                    raise ValueError("Unsafe or excessive preset path component.")
            selected.append((member, parts))
            self._directory(parts[:-1])
        for member, parts in selected:
            parent = self.directories.get(path_key(parts[:-1]), ())
            parts = (*parent, parts[-1])
            target = self._filename(parts)
            preset = os.path.splitext(target[-1])[1].lower() in preset_extensions
            self.budget.plan("file", path_key(target))
            if preset:
                self.budget.plan("flat", path_key(target))
            self.files.append(PlannedFile(member, target, preset))

    def _directory(self, parts):
        if not parts:
            return ()
        key = path_key(parts)
        if key in self.directories:
            return self.directories[key]
        parent = self._directory(parts[:-1])
        canonical = (*parent, parts[-1])
        self.budget.plan("directory", key)
        self.directories[key] = canonical
        self.reserved.add(key)
        return canonical

    def _filename(self, parts):
        original = path_key(parts)
        candidate = parts
        if original in self.reserved:
            stem, extension = os.path.splitext(parts[-1])
            counter = self.next_suffix
            while True:
                suffix = f"_{counter}"
                available = 255 - len((suffix + extension).encode("utf-8"))
                short_stem = stem.encode("utf-8")[:available].decode(
                    "utf-8", errors="ignore"
                )
                candidate = (*parts[:-1], f"{short_stem}{suffix}{extension}")
                counter += 1
                if path_key(candidate) not in self.reserved:
                    break
            self.next_suffix = counter
        self.reserved.add(path_key(candidate))
        return candidate


def sync_import_flat_scan(preset_dir, flat_dir, sources, make_name, budget, new_files):
    """Budget every missing cache object before creating any; preserve old ones."""
    if os.path.islink(flat_dir):
        raise ValueError("Preset flat-scan directory must not be a symlink.")
    pending = []
    for source in sources:
        link = os.path.join(flat_dir, make_name(preset_dir, source))
        if os.path.lexists(link):
            continue
        key = new_files.get(source, ("existing", link))
        budget.plan("flat", key)
        pending.append((link, source, key))
    if not os.path.exists(flat_dir):
        os.mkdir(flat_dir, mode=0o700)
        budget.auxiliary_directory = flat_dir
    copy_budget = ByteBudget(MAX_TOTAL_BYTES)
    for link, source, key in pending:
        budget.create("flat", key)
        try:
            os.symlink(os.path.relpath(source, flat_dir), link)
        except FileExistsError:
            raise
        except OSError:
            with open(link, "xb") as destination:
                budget.auxiliary_files.append(link)
                with open(source, "rb") as handle:
                    copy_limited(
                        handle, destination, MAX_FILE_BYTES, budget=copy_budget
                    )
        else:
            budget.auxiliary_files.append(link)
    return flat_dir
