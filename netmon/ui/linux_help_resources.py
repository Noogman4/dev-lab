"""Browse the reference links used by the bundled Linux help catalogues."""

import tkinter as tk
from tkinter import font, ttk

try:
    from netmon.services.linux_help_markdown_service import _https_url
except ModuleNotFoundError:
    from services.linux_help_markdown_service import _https_url

# Names from the bundled examples and named libraries in their references.
LIBRARIES = (
    ("django", "Django", "https://docs.djangoproject.com/"),
    ("ffmpeg", "FFmpeg", "https://ffmpeg.org/documentation.html"),
    ("gio", "GIO", "https://docs.gtk.org/gio/"),
    ("glib", "GLib", "https://docs.gtk.org/glib/"),
    ("glibc", "GNU C Library", "https://www.gnu.org/software/libc/manual/"),
    ("gnutls", "GnuTLS", "https://gnutls.org/manual/html_node/"),
    ("gtk", "GTK", "https://docs.gtk.org/gtk4/"),
    ("libalpm", "libalpm", "https://man.archlinux.org/man/libalpm.3.en"),
    ("libblkid", "libblkid", "https://man7.org/linux/man-pages/man3/libblkid.3.html"),
    ("libcap", "libcap", "https://kernel.googlesource.com/pub/scm/libs/libcap/libcap/"),
    ("libcurl", "libcurl", "https://curl.se/libcurl/"),
    ("libgcrypt", "Libgcrypt", "https://www.gnupg.org/software/libgcrypt/"),
    (
        "libgpiod",
        "libgpiod",
        "https://kernel.googlesource.com/pub/scm/libs/libgpiod/libgpiod/",
    ),
    ("libinput", "libinput", "https://wayland.freedesktop.org/libinput/doc/latest/"),
    (
        "libnotify",
        "libnotify",
        "https://manpages.debian.org/trixie/libnotify-bin/notify-send.1.en.html",
    ),
    (
        "extrausers",
        "libnss-extrausers",
        "https://packages.debian.org/trixie/libnss-extrausers",
    ),
    ("libpamac", "libpamac", "https://github.com/manjaro/pamac"),
    ("libpcap", "libpcap", "https://man7.org/linux/man-pages/man3/pcap.3pcap.html"),
    ("libvirt", "libvirt", "https://libvirt.org/docs.html"),
    ("libzypp", "libzypp", "https://github.com/openSUSE/libzypp"),
    ("lz4", "LZ4", "https://github.com/lz4/lz4"),
    ("ncurses", "ncurses", "https://invisible-island.net/ncurses/"),
    ("networkx", "NetworkX", "https://networkx.org/"),
    ("openssl", "OpenSSL", "https://docs.openssl.org/"),
    ("pango", "Pango", "https://docs.gtk.org/Pango/"),
    ("playwright", "Playwright", "https://playwright.dev/docs/intro"),
    (
        "pulseaudio",
        "PulseAudio (libpulse)",
        "https://www.freedesktop.org/software/pulseaudio/doxygen/",
    ),
    ("pyqt", "PyQt", "https://www.riverbankcomputing.com/software/pyqt/"),
    ("pytest", "pytest", "https://docs.pytest.org/"),
    ("pyyaml", "PyYAML", "https://pyyaml.org/wiki/PyYAMLDocumentation"),
    ("qt", "Qt", "https://doc.qt.io/"),
    ("sphinx", "Sphinx", "https://www.sphinx-doc.org/"),
    ("sqlalchemy", "SQLAlchemy", "https://docs.sqlalchemy.org/"),
    ("sqlite", "SQLite", "https://www.sqlite.org/docs.html"),
    ("tcltk", "Tcl/Tk", "https://www.tcl-lang.org/man/"),
    ("wiringpi", "WiringPi", "https://github.com/WiringPi/WiringPi"),
    ("xz", "XZ Utils (liblzma)", "https://tukaani.org/xz/"),
    ("zstd", "Zstandard (libzstd)", "https://facebook.github.io/zstd/"),
)

# Standard-library modules used in examples or named in the catalogued sources.
# The external PyYAML package is listed above.
PYTHON_MODULES = (
    "abc",
    "argparse",
    "array",
    "ast",
    "asyncio",
    "base64",
    "cProfile",
    "collections",
    "configparser",
    "contextlib",
    "curses",
    "dis",
    "enum",
    "fcntl",
    "functools",
    "gc",
    "hashlib",
    "hmac",
    "html",
    "http",
    "importlib",
    "inspect",
    "io",
    "ipaddress",
    "json",
    "logging",
    "math",
    "os",
    "pathlib",
    "pdb",
    "pstats",
    "py_compile",
    "queue",
    "re",
    "secrets",
    "shlex",
    "shutil",
    "socket",
    "sqlite3",
    "ssl",
    "stat",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "time",
    "timeit",
    "tkinter",
    "tomllib",
    "trace",
    "traceback",
    "tracemalloc",
    "typing",
    "unittest",
    "urllib",
    "venv",
    "weakref",
    "xml",
)
_PYTHON_DOC_URLS = {
    "cProfile": "https://docs.python.org/3.13/library/profile.html#module-cProfile",
    "pstats": "https://docs.python.org/3.13/library/profile.html#module-pstats",
}
PYTHON_LIBRARIES = tuple(
    (
        f"python_{module.lower()}",
        module,
        _PYTHON_DOC_URLS.get(
            module, f"https://docs.python.org/3/library/{module}.html"
        ),
    )
    for module in PYTHON_MODULES
)

REFERENCES = (
    ("linux_man", "Linux man-pages", "https://man7.org/linux/man-pages/"),
    ("debian_man", "Debian Manpages", "https://manpages.debian.org/"),
    (
        "debian_reference",
        "Debian Reference",
        "https://www.debian.org/doc/manuals/debian-reference/",
    ),
    ("ubuntuusers", "ubuntuusers Wiki", "https://wiki.ubuntuusers.de/Startseite/"),
    ("ubuntu_server", "Ubuntu Server Documentation", "https://ubuntu.com/server/docs/"),
    ("linux_kernel", "Linux Kernel Documentation", "https://docs.kernel.org/"),
    (
        "gnu_coreutils",
        "GNU Coreutils",
        "https://www.gnu.org/software/coreutils/manual/coreutils.html",
    ),
    ("gnu_bash", "GNU Bash", "https://www.gnu.org/software/bash/manual/bash.html"),
    (
        "systemd",
        "systemd Manual",
        "https://www.freedesktop.org/software/systemd/man/latest/",
    ),
    ("python_docs", "Python-Dokumentation", "https://docs.python.org/3/"),
    ("pypa", "Python Packaging User Guide", "https://packaging.python.org/en/latest/"),
    ("git_book", "Pro Git", "https://git-scm.com/book/de/v2"),
    ("mdn", "MDN Web Docs", "https://developer.mozilla.org/de/"),
    ("rfc", "RFC Editor", "https://www.rfc-editor.org/"),
    ("owasp", "OWASP Cheat Sheet Series", "https://cheatsheetseries.owasp.org/"),
)


def open_linux_help_resources(app):
    window = getattr(app, "linux_help_resources_window", None)
    if window is not None and window.winfo_exists():
        window.deiconify()
        window.lift()
        return window

    parent = app.tab_linux_help.winfo_toplevel()
    window = tk.Toplevel(parent)
    app.linux_help_resources_window = window
    window.title(app.tr("linux_help_resources_title", "Libraries und Nachschlagewerke"))
    window.geometry("760x580")
    window.minsize(420, 300)
    window.transient(parent)
    window.bind("<Escape>", lambda _event: window.destroy())
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    tabs = ttk.Notebook(window)
    tabs.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
    status = ttk.Label(window)
    status.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
    ttk.Button(
        window, text=app.tr("btn_close", "Schließen"), command=window.destroy
    ).grid(row=1, column=0, sticky="e", padx=10, pady=8)

    def open_link(url):
        if app._open_url_with_xdg_open(url):
            status.configure(text="")
        else:
            status.configure(
                text=app.tr(
                    "linux_help_resources_open_failed",
                    "Browser konnte nicht gestartet werden.",
                )
            )
        return "break"

    heading_font = font.nametofont("TkDefaultFont", root=window).copy()
    heading_font.configure(weight="bold")
    window.resource_heading_font = heading_font

    for title, groups in (
        (
            app.tr("linux_help_resources_libraries", "Verwendete Libraries"),
            (
                ("", LIBRARIES),
                (
                    app.tr(
                        "linux_help_resources_standard", "Python-Standardbibliothek"
                    ),
                    PYTHON_LIBRARIES,
                ),
            ),
        ),
        (
            app.tr("linux_help_resources_references", "IT und Linux"),
            (("", REFERENCES),),
        ),
    ):
        pane = ttk.Frame(tabs)
        tabs.add(pane, text=title)
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(0, weight=1)
        text = tk.Text(pane, wrap="word", padx=12, pady=10, font="TkDefaultFont")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(pane, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        text.tag_configure("heading", font=heading_font, spacing1=8, spacing3=8)
        text.tag_configure("resource_link", underline=True)
        text.tag_configure("description", spacing3=10)
        text.tag_bind(
            "resource_link", "<Enter>", lambda e: e.widget.configure(cursor="hand2")
        )
        text.tag_bind(
            "resource_link", "<Leave>", lambda e: e.widget.configure(cursor="")
        )

        for heading, entries in groups:
            if heading:
                text.insert("end", heading + "\n", "heading")
            for key, name, url in entries:
                if not _https_url(url):
                    continue
                text.insert("end", name, ("resource_link", key))
                text.tag_bind(key, "<Button-1>", lambda _e, url=url: open_link(url))
                text.insert(
                    "end",
                    "\n" + app.tr(f"linux_help_resource_{key}", name) + "\n",
                    "description",
                )
        text.configure(state="disabled")

    apply_theme = getattr(app, "_apply_tk_widget_theme", None)
    palette = getattr(app, "_app_theme", None)
    if callable(apply_theme) and palette:
        apply_theme(window, palette)
    return window
