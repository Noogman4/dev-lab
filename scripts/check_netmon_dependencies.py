"""Read-only inventory for this Python interpreter; never starts NetMon or tools."""

import argparse
import importlib.metadata
import importlib.util
import json
import shutil
import sys

MODULES = (
    ("tkinter", None, "Oberfläche", True),
    ("psutil", "psutil", "Prozesse/Systemstatus", True),
    ("PIL", "Pillow", "Bilder/Oberfläche", True),
    ("keyring", "keyring", "API-Key im System-Schlüsselbund", False),
    ("secretstorage", "SecretStorage", "Linux Secret-Service-Anbindung", False),
    ("requests", "requests", "HTTP-Client (urllib-Fallback vorhanden)", False),
    ("PyPDF2", "PyPDF2", "PDF-Dateien lesen", False),
    ("docx", "python-docx", "Word-Dateien lesen", False),
    ("openpyxl", "openpyxl", "Excel-Dateien lesen", False),
)
TOOLS = (
    "nmcli",
    "resolvectl",
    "wg",
    "ufw",
    "ip",
    "sudo",
    "udisksctl",
    "cryptsetup",
    "nmap",
    "lynis",
    "rkhunter",
    "clamscan",
    "mpv",
)


def collect():
    modules = []
    for name, package, feature, required in MODULES:
        error = ""
        try:
            found = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError, AttributeError) as exc:
            found, error = False, type(exc).__name__
        version = ""
        if found and package:
            try:
                version = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                pass
        modules.append(
            {
                "module": name,
                "package": package,
                "feature": feature,
                "required": required,
                "found": found,
                "version": version,
                "error": error,
            }
        )
    return {
        "python": sys.executable,
        "virtualenv": sys.prefix != sys.base_prefix,
        "modules": modules,
        "tools": {name: shutil.which(name) or "" for name in TOOLS},
        "limit": "Nur Auffindbarkeit/Metadaten: kein Import-, Backend-, Berechtigungs- oder Funktionstest. Keine Dienste gestartet und keine Schlüssel gelesen.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args()
    report = collect()
    if options.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Python: {report['python']}\nVirtuelle Umgebung: {report['virtualenv']}")
        for row in report["modules"]:
            state = "gefunden" if row["found"] else "FEHLT"
            print(f"[{state}] {row['module']} {row['version']} — {row['feature']}")
        print("\nExterne Werkzeuge (werden nicht ausgeführt):")
        for name, path in report["tools"].items():
            print(f"{name}: {path or 'nicht gefunden'}")
        print("\n" + report["limit"])
    return int(any(r["required"] and not r["found"] for r in report["modules"]))


if __name__ == "__main__":
    raise SystemExit(main())
