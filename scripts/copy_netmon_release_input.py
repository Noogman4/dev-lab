#!/usr/bin/env python3
"""Stage regular workspace files without following source or staging symlinks."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import stat

from read_netmon_version import ROOT

DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@contextmanager
def anchored_parent(root, path):
    """Walk beneath a trusted root using directory FDs, rejecting every link."""
    relative = path.relative_to(root)
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"Path must be beneath {root}: {path}")
    descriptor = os.open(root, DIRECTORY_FLAGS)
    try:
        for part in relative.parts[:-1]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, relative.name
    finally:
        os.close(descriptor)


def copy_input(source_root, source, staging_root, destination):
    # Keep the destination inside this build, but anchor its whole directory
    # walk at the repository so a swapped .release-work ancestor is rejected.
    relative = destination.relative_to(staging_root)
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"Destination must be beneath {staging_root}")
    with anchored_parent(source_root, source) as (parent, name):
        descriptor = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError(f"Release input must be a regular file: {source}")
        with anchored_parent(source_root, destination) as (parent, name):
            target = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
        with os.fdopen(target, "wb") as output:
            shutil.copyfileobj(handle, output, length=1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staging_root", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        copy_input(ROOT, args.source, args.staging_root, args.destination)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Release-Abbruch: Unsichere Release-Eingabe: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
