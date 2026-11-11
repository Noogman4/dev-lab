"""Fixed resolution and CPU profiles; never accept dimensions from a pixel stream.

This module is also loaded as a read-only file by the isolated entrypoints.
Keep it independent of application state and third-party packages.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    key: str
    width: int
    height: int
    texture: int
    burst_frames: int
    max_fps: int

    @property
    def frame_bytes(self):
        return self.width * self.height * 4

    @property
    def aspect(self):
        return "4:3" if self.key == DEFAULT else "16:9"


DEFAULT = "640x480"
PROFILES = (
    Profile(DEFAULT, 640, 480, 512, 16, 120),
    Profile("960x540", 960, 540, 1024, 4, 45),
    Profile("1280x720", 1280, 720, 2048, 4, 45),
    Profile("1920x1080", 1920, 1080, 2048, 4, 45),
)


def resolve(key=DEFAULT):
    if type(key) is str:
        for profile in PROFILES:
            if key == profile.key:
                return profile
    raise ValueError("Nicht unterstützte projectM-Auflösung.")


def from_arguments(arguments):
    if not arguments:
        return resolve()
    if len(arguments) == 2 and arguments[0] == "--resolution":
        return resolve(arguments[1])
    raise ValueError("Ungültige projectM-Profilargumente.")


@dataclass(frozen=True)
class CPUProfile:
    key: str
    label: str
    fps: int
    threads: int
    quota: str


DEFAULT_CPU = "standard"
CPU_PROFILES = (
    CPUProfile(DEFAULT_CPU, "Standard", 25, 2, "pm-renderer"),
    CPUProfile("performance", "Mehr Leistung", 30, 4, "pm-renderer-performance"),
)


def resolve_cpu(key=DEFAULT_CPU):
    if type(key) is str:
        for profile in CPU_PROFILES:
            if key == profile.key:
                return profile
    raise ValueError("Nicht unterstütztes projectM-CPU-Profil.")


def renderer_arguments(arguments):
    cpu = resolve_cpu()
    if len(arguments) >= 2 and arguments[0] == "--cpu-profile":
        cpu = resolve_cpu(arguments[1])
        arguments = arguments[2:]
    return from_arguments(arguments), cpu


def resolve_backend(key):
    if type(key) is str and key in {"auto", "cpu", "gpu"}:
        return key
    raise ValueError("Nicht unterstützter projectM-Renderweg.")


# Visualizer-only EQ: shapes the PCM copy projectM analyses, never the audio.
VISUAL_EQ_MIN_DB = -12
VISUAL_EQ_MAX_DB = 12
VISUAL_EQ_VERSION = 1


@dataclass(frozen=True)
class VisualEq:
    bass_db: int = 0
    treble_db: int = 0
    sensitivity_db: int = 0


NEUTRAL_EQ = VisualEq()


def validate_visual_eq(eq):
    if type(eq) is not VisualEq:
        raise ValueError("Ungültige Klangeinstellung der Visualisierung.")
    for value in (eq.bass_db, eq.treble_db, eq.sensitivity_db):
        if type(value) is not int or not (
            VISUAL_EQ_MIN_DB <= value <= VISUAL_EQ_MAX_DB
        ):
            raise ValueError("Klangwert der Visualisierung außerhalb ±12 dB.")
    return eq


def encode_visual_eq(eq):
    """Fixed 8-byte record: bass, treble, sensitivity (int8), version, complement."""
    validate_visual_eq(eq)
    head = bytes(
        (
            eq.bass_db & 0xFF,
            eq.treble_db & 0xFF,
            eq.sensitivity_db & 0xFF,
            VISUAL_EQ_VERSION,
        )
    )
    return head + bytes(b ^ 0xFF for b in head)
