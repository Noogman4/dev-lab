"""Read-only distribution references bundled with NetMon."""

from pathlib import Path
import re
import tkinter as tk
from tkinter import ttk

try:
    from netmon.services import linux_help_markdown_service as markdown
    from netmon.ui.linux_help_reader import LinuxHelpReader
except ModuleNotFoundError:
    from services import linux_help_markdown_service as markdown
    from ui.linux_help_reader import LinuxHelpReader


COMPONENTS_DIR = Path(__file__).resolve().parents[2] / "docs/linux-komponenten"
ZORIN_DOCUMENT = COMPONENTS_DIR / "Zorin-OS-Komponenten.md"
MINT_DOCUMENT = COMPONENTS_DIR / "Linux-Mint-Komponenten.md"
_ZORIN_SOURCES = frozenset(
    {
        "https://zorin.com/os/details/",
        "https://help.zorin.com/docs/getting-started/getting-zorin-os-lite/",
        "https://ubuntu.com/tutorials/access-desktop-networkmanager-settings-through-netplan",
        "https://forum.zorin.com/t/disable-wayland/36384",
    }
)
_MINT_SOURCES = frozenset(
    {
        "https://linuxmint-installation-guide.readthedocs.io/en/latest/choose.html",
        "https://linuxmint-developer-guide.readthedocs.io/en/latest/cinnamon.html",
        "https://linuxmint-developer-guide.readthedocs.io/en/latest/mint-tools.html",
        "https://www.linuxmint.com/rel_xia_cinnamon_whatsnew.php",
        "https://linuxmint-installation-guide.readthedocs.io/en/latest/timeshift.html",
        "https://github.com/linuxmint/timeshift",
        "https://linuxmint-user-guide.readthedocs.io/en/latest/snap.html",
        "https://www.linuxmint.com/download_lmde.php",
    }
)


def _load_components(path, name):
    source = markdown._read_regular(path, markdown.MAX_BYTES).decode("utf-8-sig")
    lines = source.splitlines()
    if len(lines) > markdown.MAX_LINES:
        raise ValueError("Zu viele Zeilen.")
    rendered = []
    in_contents = False
    for line in lines:
        if line.startswith("## "):
            in_contents = line == "## Inhaltsverzeichnis"
        if (
            in_contents
            or line == "---"
            or re.fullmatch(r'<a id="[a-z0-9-]+"></a>', line)
        ):
            continue
        if line.startswith(">"):
            line = line[1:].lstrip()
        if re.fullmatch(r"\*[^*]+\*", line):
            line = line[1:-1]
        rendered.append(line)
    # The reader builds its own navigation from the document's headings.
    return markdown.Document(
        {"entry_type": "reference", "name": name},
        markdown._parse_blocks(rendered, 0),
        source,
    )


def open_linux_help_components(app):
    window = getattr(app, "linux_help_components_window", None)
    if window is not None and window.winfo_exists():
        window.deiconify()
        window.lift()
        return window

    parent = app.tab_linux_help.winfo_toplevel()
    window = tk.Toplevel(parent)
    app.linux_help_components_window = window
    window.title(app.tr("linux_help_components", "Linux Komponenten"))
    window.geometry("920x700")
    window.minsize(530, 390)
    # A normal window lets the desktop handle minimize and maximize.
    window.resizable(True, True)
    window.bind("<Escape>", lambda _event: window.destroy())
    tabs = ttk.Notebook(window)
    tabs.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    for tab, name, path, sources in (
        ("Zorin", "Zorin OS", ZORIN_DOCUMENT, _ZORIN_SOURCES),
        ("Mint", "Linux Mint", MINT_DOCUMENT, _MINT_SOURCES),
    ):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text=tab)
        try:
            document = _load_components(path, name)
        except (OSError, ValueError):
            ttk.Label(
                frame,
                padding=12,
                text=app.tr(
                    "linux_help_components_load_failed",
                    "Die Übersicht konnte nicht geladen werden.",
                ),
            ).pack(anchor="nw")
            continue
        reader = LinuxHelpReader(
            frame,
            tr=app.tr,
            allow_popout=False,
            source_validator=sources.__contains__,
        )
        reader.pack(fill="both", expand=True)
        reader.set_document(document)
    ttk.Button(
        window, text=app.tr("btn_close", "Schließen"), command=window.destroy
    ).pack(anchor="e", padx=10, pady=8)
    return window
