"""Version-bound, explicitly built renderer. Never compile or download at startup."""

import hashlib
import json
from pathlib import Path
import stat

from netmon.core.radio_sandbox import RadioSandboxError

SOURCE = Path(__file__).resolve().parents[1] / "native/projectm_pcm"
LIBRARY_SHA256 = "ca7e592e283ce782e772fa0d870dbd0d5910cbdeaa8c019ce6075a1247661730"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(payload):
    return _artifact(payload, gpu=False)


def gpu_artifact(payload):
    return _artifact(payload, gpu=True)


def _artifact(payload, *, gpu):
    try:
        binary = SOURCE / "build" / ("egl-renderer" if gpu else "pcm-renderer")
        record = json.loads(
            (SOURCE / "build" / ("egl-build.json" if gpu else "build.json")).read_text()
        )
        library = payload / "lib/libprojectM.so.3"
        info = binary.lstat()
        sources = [SOURCE / "pcm_renderer.cpp", *sorted((SOURCE / "include").iterdir())]
        if gpu:
            sources.append(SOURCE / "egl_context.hpp")
        expected = {str(p.relative_to(SOURCE)): digest(p) for p in sources}
        if (
            record.get("schema") != 1
            or record.get("library_sha256") != LIBRARY_SHA256
            or digest(library) != LIBRARY_SHA256
            or record.get("sources") != expected
            or record.get("binary_sha256") != digest(binary)
            or not stat.S_ISREG(info.st_mode)
            or not info.st_mode & 0o100
            or info.st_mode & 0o022
        ):
            raise ValueError("Unsupported adapter artifact")
        return binary
    except (OSError, ValueError, TypeError) as error:
        raise RadioSandboxError(
            "Passender PCM-Adapter fehlt oder ist veraltet; geschützter Start abgelehnt."
        ) from error
