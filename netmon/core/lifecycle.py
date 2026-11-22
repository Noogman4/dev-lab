"""Unprivileged path lookup and verified backup for the guided package updater."""

import argparse
import json
import os
from pathlib import Path
import secrets
import sys

from netmon.core import user_backup
from netmon.core.state import netmon_documents_path
from netmon.core.user_files import legacy_sources


def document_root():
    """Read the account's saved XDG setting; caller environment grants no authority."""
    # The launcher supplies a passwd-verified HOME in a clean environment.
    # Discard per-process overrides to match a regular desktop installation.
    previous = {
        key: os.environ.pop(key, None)
        for key in ("XDG_DOCUMENTS_DIR", "XDG_CONFIG_HOME")
    }
    try:
        return Path(netmon_documents_path()).parent
    finally:
        for key, value in previous.items():
            if value is not None:
                os.environ[key] = value


def backup_for_update(parent, *, progress=None):
    """Export a full snapshot and read every file back before authorizing update."""
    source = document_root() / "NetMon"
    if not source.is_dir():
        raise ValueError(
            "Kein zentraler NetMon-Datenordner vorhanden. Zuerst die Datenuebernahme in NetMon abschliessen."
        )
    parent = Path(parent)
    if not parent.is_absolute() or ".." in parent.parts:
        raise ValueError("Bitte einen absoluten Sicherungsordner angeben.")
    if parent == source or source in parent.parents:
        raise ValueError(
            "Die Sicherung muss ausserhalb des aktiven NetMon-Ordners liegen."
        )
    # Inspect existing ancestors before creating the selected child. A symlink
    # must not create even an empty folder inside the active profile on failure.
    with user_backup._directory(parent.parent) as directory:
        try:
            os.mkdir(parent.name, 0o700, dir_fd=directory)
        except FileExistsError:
            pass
    exported = user_backup.export_backup(source, parent, progress=progress)
    preview = user_backup.preview_restore(
        exported,
        parent / (".netmon-update-preview-" + secrets.token_hex(12)),
        progress=progress,
    )
    if preview.kind != "full":
        raise ValueError("Keine Vollsicherung erzeugt.")
    return {
        "backup": str(exported),
        "source": str(source),
        "files_verified": len(preview.entries),
        "manifest_sha256": preview.manifest_sha256,
    }


def inspect_user_data():
    """Report saved paths without creating a profile or migrating any files."""
    documents = document_root()
    source = documents / "NetMon"
    legacy = [str(path) for path, _, _ in legacy_sources(source) if path.exists()]
    return {
        "documents": str(documents),
        "source": str(source),
        "canonical_data_present": source.is_dir(),
        "legacy_data_present": bool(legacy),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["documents", "inspect", "backup"])
    parser.add_argument("--parent")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error(
            "Benutzerdaten nur mit den Rechten des aufrufenden Benutzers bearbeiten."
        )
    try:
        if args.operation == "documents":
            print(document_root())
        elif args.operation == "inspect":
            print(json.dumps(inspect_user_data(), ensure_ascii=False))
        elif args.parent:
            print(
                "Sicherung und vollstaendige Pruefsummenpruefung koennen je nach Datenmenge mehrere Minuten dauern. "
                "Bitte das Terminal geoeffnet lassen; die Fortschrittsmeldungen erscheinen nach abgeschlossenen Dateigruppen.",
                file=sys.stderr,
                flush=True,
            )

            def progress(phase, done, total):
                if done % 1000 == 0 or done == total:
                    print(
                        f"Backup {phase}: {done}/{total}", file=sys.stderr, flush=True
                    )

            print(
                json.dumps(
                    backup_for_update(args.parent, progress=progress),
                    ensure_ascii=False,
                )
            )
        else:
            parser.error("--parent fehlt")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
