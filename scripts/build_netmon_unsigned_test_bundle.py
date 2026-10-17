#!/usr/bin/env python3
"""Package local payloads for testing only; this is never a website upload."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from read_netmon_version import ROOT, read_netmon_version

MARKER = "UNSIGNED-TEST-ONLY"


def build_test_bundle():
    version = read_netmon_version()
    output = ROOT / "unsigned-test-builds"
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError("Unsafe unsigned-test output directory")
    output.mkdir(mode=0o700, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="test-", dir=output))
    try:
        artifact = directory / f"netmon-{MARKER}.zip"
        payloads = [
            (ROOT / f"dist/netmon_{version}_all.deb", f"netmon-{MARKER}.deb"),
            (
                ROOT / f"dist/docs/netmon_dokumentation_{version}.pdf",
                f"documentation-{MARKER}.pdf",
            ),
            (
                ROOT / f"dist/docs/netmon_dokumentation_{version}.html",
                f"documentation-{MARKER}.html",
            ),
        ]
        with zipfile.ZipFile(
            artifact, "x", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr(
                f"{MARKER}/{MARKER}",
                f"{MARKER}\nDO NOT PUBLISH. NICHT VEROEFFENTLICHEN.\n",
            )
            archive.writestr(
                f"{MARKER}/test-build.json",
                json.dumps(
                    {
                        "identity": MARKER,
                        "production_release": False,
                        "source_version": version,
                    }
                ),
            )
            for source, name in payloads:
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"Missing regular test input: {source}")
                archive.write(source, f"{MARKER}/payload/{name}")
    except BaseException:
        shutil.rmtree(directory)
        raise
    return artifact


if __name__ == "__main__":
    print("UNSIGNED-TEST-ONLY: DO NOT PUBLISH. NICHT VEROEFFENTLICHEN.")
    print(build_test_bundle())
