"""Explicit local build of the version-bound PCM renderer; never run at startup."""

import hashlib
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "netmon/native/projectm_pcm"
PAYLOAD = Path("/var/lib/flatpak/app/net.sourceforge.projectM/current/active/files")
LIBRARY_SHA256 = "ca7e592e283ce782e772fa0d870dbd0d5910cbdeaa8c019ce6075a1247661730"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(gpu=False):
    library = (PAYLOAD / "lib/libprojectM.so.3").resolve(strict=True)
    if digest(library) != LIBRARY_SHA256:
        raise RuntimeError("Unsupported projectM library; no adapter built.")
    output = SOURCE / "build"
    output.mkdir(exist_ok=True)
    binary = output / ("egl-renderer" if gpu else "pcm-renderer")
    command = [
        "/usr/bin/g++",
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-fstack-protector-strong",
        "-D_FORTIFY_SOURCE=2",
        "-fPIE",
        "-pie",
        "-Wl,-z,relro,-z,now",
        "-I" + str(SOURCE / "include"),
        str(SOURCE / "pcm_renderer.cpp"),
        str(library),
        "-lGL",
        "-lX11",
        "-o",
        str(binary),
    ]
    if gpu:
        command.insert(1, "-DNETMON_EGL")
        command[command.index("-lX11")] = "-lEGL"
    subprocess.run(command, check=True, timeout=60)
    binary.chmod(0o700)
    sources = [SOURCE / "pcm_renderer.cpp", *sorted((SOURCE / "include").iterdir())]
    if gpu:
        sources.append(SOURCE / "egl_context.hpp")
    record = {
        "schema": 1,
        "library_sha256": LIBRARY_SHA256,
        "binary_sha256": digest(binary),
        "sources": {str(p.relative_to(SOURCE)): digest(p) for p in sources},
        "argv": command,
    }
    (output / ("egl-build.json" if gpu else "build.json")).write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu", action="store_true")
    main(gpu=parser.parse_args().gpu)
