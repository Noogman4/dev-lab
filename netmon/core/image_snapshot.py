"""Immutable, bounded image attachments for delayed Chad uploads."""

from dataclasses import dataclass, field
import io
import os
from pathlib import Path
import stat

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_ATTACHMENTS = 4
MAX_TOTAL_IMAGE_BYTES = MAX_IMAGE_ATTACHMENTS * MAX_IMAGE_BYTES
MAX_IMAGE_PIXELS = 16 * 1024 * 1024
_FORMATS = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
    "GIF": "image/gif",
    "BMP": "image/bmp",
}
_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


@dataclass(frozen=True, slots=True)
class ImageSnapshot:
    source_path: str
    data: bytes = field(repr=False)
    mime_type: str = field(init=False)

    def __post_init__(self):
        if type(self.data) is not bytes or not 0 < len(self.data) <= MAX_IMAGE_BYTES:
            raise ValueError("Image must contain at most 5 MiB of immutable bytes.")
        # Pillow is already a NetMon dependency; import it only for image use.
        from PIL import Image

        with Image.open(io.BytesIO(self.data), formats=list(_FORMATS)) as image:
            if (
                image.format not in _FORMATS
                or not 0 < image.width <= 8192
                or not 0 < image.height <= 8192
                or image.width * image.height > MAX_IMAGE_PIXELS
            ):
                raise ValueError(
                    "Unsupported image format or excessive image dimensions."
                )
            mime_type = _FORMATS[image.format]
            image.verify()
        object.__setattr__(self, "mime_type", mime_type)


def _open_directory(parent, name):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)


def snapshot_image(path: str) -> ImageSnapshot:
    """Walk from / with retained directory FDs; never follow a selected link."""
    selected = Path(path).expanduser()
    if (
        any(ord(char) < 32 or ord(char) == 127 for char in str(selected))
        or ".." in selected.parts
    ):
        raise ValueError("Invalid image path.")
    selected = Path(os.path.abspath(selected))
    home_alias = Path(os.path.abspath(Path.home()))
    try:
        relative = selected.relative_to(home_alias)
    except ValueError as exc:
        raise ValueError("Image path must be inside the user home directory.") from exc
    if not relative.parts or selected.suffix.lower() not in _SUFFIXES:
        raise ValueError("Unsupported image file type.")
    home = home_alias.resolve(strict=True)
    canonical = home / relative
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in canonical.parts[1:-1]:
            child = _open_directory(directory, part)
            os.close(directory)
            directory = child
        descriptor = os.open(
            canonical.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory,
        )
    finally:
        os.close(directory)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image must be a regular file of at most 5 MiB.")
        data = source.read(MAX_IMAGE_BYTES + 1)
        after = os.fstat(source.fileno())
        if len(data) > MAX_IMAGE_BYTES or (
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("Image exceeded its limit or changed while reading.")
    return ImageSnapshot(str(canonical), data)


def attachment_snapshots(files: list[dict]) -> list[ImageSnapshot]:
    """Path-only legacy attachments fail closed: selection must capture bytes."""
    snapshots = []
    total = 0
    for item in files:
        if item.get("type") != "image":
            continue
        snapshot = item.get("snapshot")
        if not isinstance(snapshot, ImageSnapshot):
            raise ValueError(
                "Image has no captured copy. Please import it again before sending."
            )
        total += len(snapshot.data)
        if len(snapshots) >= MAX_IMAGE_ATTACHMENTS or total > MAX_TOTAL_IMAGE_BYTES:
            raise ValueError(
                "Image attachment limit exceeded (four images, 20 MiB total)."
            )
        snapshots.append(snapshot)
    return snapshots
