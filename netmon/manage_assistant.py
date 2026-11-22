"""One explanatory graphical entry for NetMon installation and removal."""

import argparse
import json
import locale
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from netmon.core.privilege_launcher import (
    maintenance_terminal_command,
    terminal_environment,
)
from netmon.core.lifecycle import backup_for_update
from netmon.core.state import netmon_documents_path
from netmon.install_assistant import ensure_closed, installed_version

COPY = {
    "de": {
        "title": "NetMon verwalten",
        "subtitle": "Installieren, aktualisieren, sichern oder entfernen – du entscheidest, was mit deinen Daten passiert.",
        "installed": "Installierte Version: ",
        "remove_manager": "NetMon verwalten ebenfalls entfernen",
        "manager_only": "Verwaltung entfernen …",
        "manager_hint": "Weitere Optionen: Nur die Verwaltung entfernen. NetMon, Benutzerdaten und externe Sicherungen bleiben erhalten. Bestätigung folgt im Terminal.",
        "missing": "NetMon ist noch nicht installiert.",
        "unknown": "Der Paketstatus konnte nicht gelesen werden.",
        "backup": "Standard-Sicherungsordner: ",
        "footer": "Beim Öffnen dieses Fensters wird nichts verändert. Schließe NetMon, Radio und Secure Browser vor der Ausführung.\nDer gewählte Assistent öffnet sich im Terminal und zeigt Fortschritt, Rückfragen und Bestätigungen.",
        "close": "Schließen",
        "choose": "Neue NetMon-Paketdatei auswählen",
        "package": "Debian-Paket",
        "all": "Alle Dateien",
        "error": "Vorgang nicht gestartet",
        "terminal": "Es wurde kein unterstütztes Terminal gefunden.",
        "launched": "Der Assistent wurde im Terminal geöffnet. Dort geht es weiter.",
        "choose_backup": "Zielordner für die NetMon-Sicherung auswählen",
        "backup_intro": "NetMon-Sicherung: Dateien werden kopiert und anschließend vollständig mit Prüfsummen geprüft.",
        "backup_close": "Für eine konsistente Sicherung müssen NetMon, Radio und Secure Browser geschlossen sein.",
        "backup_export": "Sichern",
        "backup_verify": "Prüfen",
        "backup_done": "Sicherung erfolgreich erstellt und geprüft.",
        "backup_target": "Sicherungsordner: {path}",
        "backup_files": "Geprüfte Dateien: {count}",
        "backup_failed": "Sicherung fehlgeschlagen: {error}",
        "backup_no_root": "Die Sicherung bitte als normaler Benutzer ohne sudo starten.",
        "duration": "Je nach Datenmenge und Datenträger kann dieser Vorgang mehrere Minuten dauern. Bitte das Fenster bis zum Abschluss geöffnet lassen. Einzelne Arbeitsschritte können länger ohne neue Fortschrittsmeldung dauern.",
        "cards": [
            (
                "install",
                "Installieren oder aktualisieren",
                "Wähle eine NetMon-Paketdatei (.deb). Der Assistent erkennt eine vorhandene Version und bietet die passende Installation an. Vorhandene zentrale Benutzerdaten werden zuerst vollständig gesichert und mit Prüfsummen geprüft. Erst danach beginnt die Paketinstallation. Bei einem Backupfehler wird abgebrochen.\n\nVerwende eine Paketdatei aus vertrauenswürdiger Quelle. Auf einem frischen System ohne Benutzerdaten ist keine leere Sicherung nötig.",
                "Paketdatei auswählen …",
                "#176b78",
            ),
            (
                "backup",
                "Sicherung erstellen",
                "Sichere den zentralen NetMon-Benutzerordner mit Einstellungen, Favoriten, Dokumenten und Browserprofilen unabhängig von einer Installation oder einem Update. Wähle einen Zielordner außerhalb des aktiven NetMon-Ordners. Alle gesicherten Dateien werden anschließend anhand ihrer Prüfsummen kontrolliert.\n\nSchließe vorher NetMon, Radio und alle Secure Browser. Die Sicherung benötigt keine Administratorrechte.",
                "Sicherungsordner auswählen …",
                "#28704d",
            ),
            (
                "keep",
                "Entfernen – Daten behalten",
                "NetMon wird deinstalliert. Einstellungen, Radio-Favoriten, Slots, Dokumente, Browserprofile und gespeicherte VPN-Profile bleiben für eine spätere Installation erhalten. Eine Profil-Löschung wird in diesem Ablauf nicht angeboten.\n\nZusätzliche Systembereinigungen werden getrennt abgefragt. Nachweislich von NetMon gestartete VPN-Verbindungen können beim Entfernen getrennt werden.",
                "Entfernung mit Datenerhalt vorbereiten …",
                "#345078",
            ),
            (
                "delete",
                "Entfernen – Daten löschen",
                "NetMon wird deinstalliert; zusätzlich werden seine Benutzerdateien zur Löschung vorgesehen. Dazu gehören Einstellungen, Favoriten, Slots und Dokumente. Der Assistent zeigt vorher die genauen Pfade. Erst nach deiner Bestätigung wird gelöscht.\n\nBrowser und systemweite VPN-Profile werden gesondert abgefragt. Sicherungen außerhalb des NetMon-Datenordners bleiben erhalten.",
                "Entfernung mit Datenlöschung vorbereiten …",
                "#a63c42",
            ),
        ],
    },
    "en": {
        "title": "Manage NetMon",
        "subtitle": "Install, update, back up or remove NetMon – choose what happens to your personal data.",
        "installed": "Installed version: ",
        "remove_manager": "Also remove Manage NetMon",
        "manager_only": "Remove management application …",
        "manager_hint": "More options: remove only this management application. NetMon, personal data and external backups are retained. Confirmation follows in the terminal.",
        "missing": "NetMon is not installed yet.",
        "unknown": "The package status could not be read.",
        "backup": "Default backup folder: ",
        "footer": "Opening this window changes nothing. Close NetMon, Radio and Secure Browsers before proceeding.\nThe selected assistant opens in a terminal to show progress, questions and confirmations.",
        "close": "Close",
        "choose": "Select the new NetMon package",
        "package": "Debian package",
        "all": "All files",
        "error": "Operation not started",
        "terminal": "No supported terminal was found.",
        "launched": "The assistant opened in a terminal. Continue there.",
        "choose_backup": "Select the destination folder for the NetMon backup",
        "backup_intro": "NetMon backup: files are copied and then fully verified against their checksums.",
        "backup_close": "Close NetMon, Radio and Secure Browsers for a consistent backup.",
        "backup_export": "Backing up",
        "backup_verify": "Verifying",
        "backup_done": "Backup created and verified successfully.",
        "backup_target": "Backup folder: {path}",
        "backup_files": "Verified files: {count}",
        "backup_failed": "Backup failed: {error}",
        "backup_no_root": "Start the backup as your normal user without sudo.",
        "duration": "Depending on the amount of data and the storage device, this operation may take several minutes. Please keep the window open until completion. Individual steps may take longer without a new progress message.",
        "cards": [
            (
                "install",
                "Install or update",
                "Select a NetMon package (.deb). The assistant detects an installed version and prepares the appropriate installation. Existing central user data is fully backed up and verified with checksums first. Package installation follows only after verification. A backup error stops the operation.\n\nUse a package from a trusted source. A fresh system without user data needs no empty backup.",
                "Select package …",
                "#176b78",
            ),
            (
                "backup",
                "Create a backup",
                "Back up the central NetMon user folder, including settings, favorites, documents and browser profiles, independently of an installation or update. Choose a destination outside the active NetMon folder. Every backed-up file is then checked against its checksum.\n\nClose NetMon, Radio and all Secure Browsers first. No administrator privileges are needed for the backup.",
                "Select backup folder …",
                "#28704d",
            ),
            (
                "keep",
                "Remove – keep personal data",
                "Uninstall NetMon while keeping settings, radio favorites, slots, documents, browser profiles and saved VPN profiles for a future installation. Profile deletion is not offered in this mode.\n\nAdditional system cleanup has separate questions. VPN connections proven to have been started by NetMon may be disconnected during removal.",
                "Prepare removal, keeping data …",
                "#345078",
            ),
            (
                "delete",
                "Remove – delete personal data",
                "Uninstall NetMon and select its personal files for deletion, including settings, favorites, slots and documents. The assistant previews the exact paths before your final confirmation.\n\nBrowser and system VPN profiles have separate questions. Backups outside the NetMon data folder are retained.",
                "Prepare removal with data deletion …",
                "#a63c42",
            ),
        ],
    },
}


def language():
    try:
        with (Path(netmon_documents_path()) / "Config/config.json").open() as stream:
            content = stream.read(65537)
        data = json.loads(content) if len(content) <= 65536 else {}
        if data.get("language") in COPY:
            return data["language"]
    except (OSError, ValueError, AttributeError):
        pass
    return "de" if (locale.getlocale()[0] or "").lower().startswith("de") else "en"


def action_command(
    action, package=None, *, backup_parent=None, lang="de", remove_manager=False
):
    if remove_manager and action != "delete":
        raise ValueError("Management removal can only accompany data deletion")
    if action == "install" and package:
        return ["/usr/bin/netmon-install", str(package)]
    if action in {"keep", "delete", "manager"}:
        command = ["/usr/bin/netmon-uninstall", "--mode", action]
        if remove_manager:
            command.append("--remove-manager")
        return command
    if action == "backup" and backup_parent and lang in COPY:
        return [
            "/usr/bin/netmon-manage",
            "--backup",
            "--parent",
            str(backup_parent),
            "--lang",
            lang,
        ]
    raise ValueError("Unknown or incomplete management action")


def run_backup(parent, *, lang="de"):
    copy = COPY[lang]
    if os.geteuid() == 0:
        print(copy["backup_no_root"], file=sys.stderr)
        return 1
    try:
        ensure_closed()
        print(copy["backup_intro"], flush=True)
        print(copy["backup_close"], flush=True)
        print(copy["duration"], flush=True)

        def progress(phase, done, total):
            if done % 1000 == 0 or done == total:
                label = copy["backup_export" if phase == "export" else "backup_verify"]
                print(f"{label}: {done}/{total}", file=sys.stderr, flush=True)

        receipt = backup_for_update(parent, progress=progress)
    except (OSError, ValueError) as exc:
        print(copy["backup_failed"].format(error=exc), file=sys.stderr)
        return 1
    print(copy["backup_done"], flush=True)
    print(copy["backup_target"].format(path=receipt["backup"]), flush=True)
    print(copy["backup_files"].format(count=receipt["files_verified"]), flush=True)
    return 0


def launch_terminal(argv):
    if not Path(argv[0]).is_file():
        raise ValueError(
            "Die Verwaltung wurde entfernt. Bitte netmon-manager neu installieren. / "
            "Management has been removed. Please reinstall netmon-manager."
        )
    script = (
        shlex.join(argv)
        + '\nresult=$?\nprintf "\\nExit: %s\\n" "$result"\nread -r -p "Enter … " _unused\nexit "$result"'
    )
    command = maintenance_terminal_command(script)
    if command is None:
        raise FileNotFoundError("No supported terminal")
    subprocess.Popen(command, env=terminal_environment(), start_new_session=True)


class ManagementWindow(tk.Tk):
    def __init__(self, *, lang=None, version=None, runner=None):
        super().__init__()
        self.lang = lang or language()
        self.copy = COPY[self.lang]
        self.runner = runner or launch_terminal
        self.title(self.copy["title"])
        self.configure(background="#edf1f5")
        width = min(1060, self.winfo_screenwidth() - 60)
        height = min(880, self.winfo_screenheight() - 90)
        self.geometry(f"{width}x{height}")
        self.minsize(700, 520)
        self.buttons = {}
        self.remove_manager = tk.BooleanVar(value=False)
        self._version_override = version
        self.wrapping = []
        self.status = tk.StringVar(value="")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "Manager.TButton", font=("TkDefaultFont", 10), padding=(14, 9)
        )

        header = tk.Frame(self, background="#18334a", padx=26, pady=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text=self.copy["title"],
            font=("TkDefaultFont", 23, "bold"),
            background="#18334a",
            foreground="white",
            anchor="w",
        ).pack(fill="x")
        label = tk.Label(
            header,
            text=self.copy["subtitle"],
            font=("TkDefaultFont", 11),
            background="#18334a",
            foreground="#d5e4ef",
            justify="left",
            anchor="w",
            wraplength=width - 70,
        )
        label.pack(fill="x", pady=(7, 10))
        self.wrapping.append((label, 70))
        try:
            current = installed_version() if version is None else version
            version_text = (
                self.copy["installed"] + current if current else self.copy["missing"]
            )
        except (OSError, ValueError, subprocess.SubprocessError):
            version_text = self.copy["unknown"]
        self.version_text = tk.StringVar(value=version_text)
        tk.Label(
            header,
            textvariable=self.version_text,
            font=("TkDefaultFont", 10, "bold"),
            background="#18334a",
            foreground="#a8dfd7",
            anchor="w",
        ).pack(fill="x")

        footer = tk.Frame(self, background="#edf1f5", padx=22, pady=12)
        footer.pack(side="bottom", fill="x")
        ttk.Button(
            footer,
            text=self.copy["close"],
            style="Manager.TButton",
            command=self.destroy,
        ).pack(side="right", padx=(12, 0))
        self.footer_text = tk.Label(
            footer,
            text=self.copy["footer"],
            background="#edf1f5",
            foreground="#425367",
            justify="left",
            anchor="w",
            wraplength=width - 185,
            font=("TkDefaultFont", 9),
        )
        self.footer_text.pack(side="left", fill="x", expand=True)
        self.wrapping.append((self.footer_text, 185))
        self.status_label = tk.Label(
            self,
            textvariable=self.status,
            background="#edf1f5",
            foreground="#176b78",
            anchor="w",
            padx=24,
            pady=4,
        )
        self.status_label.pack(side="bottom", fill="x")

        viewport = tk.Frame(self, background="#edf1f5")
        viewport.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(viewport, background="#edf1f5", highlightthickness=0)
        bar = ttk.Scrollbar(viewport, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.cards = tk.Frame(self.canvas, background="#edf1f5", padx=22, pady=10)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards, anchor="nw"
        )
        self.cards.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self._resize)
        self.bind_all("<MouseWheel>", self._wheel)
        self.bind_all("<Button-4>", lambda _: self.canvas.yview_scroll(-3, "units"))
        self.bind_all("<Button-5>", lambda _: self.canvas.yview_scroll(3, "units"))
        for index, (action, title, explanation, button, color) in enumerate(
            self.copy["cards"], 1
        ):
            self._card(index, action, title, explanation, button, color, width)
        extra = tk.Label(
            self.cards,
            text=self.copy["manager_hint"],
            background="#edf1f5",
            foreground="#425367",
            justify="left",
            anchor="w",
            wraplength=width - 115,
        )
        extra.pack(fill="x", pady=(8, 6))
        self.wrapping.append((extra, 115))
        self.manager_button = ttk.Button(
            self.cards,
            text=self.copy["manager_only"],
            command=lambda: self._action("manager"),
        )
        self.manager_button.pack(anchor="w", pady=(0, 14))
        self.bind("<FocusIn>", self._refresh_version)

    def _refresh_version(self, event=None):
        if event is not None and event.widget is not self:
            return
        try:
            current = (
                installed_version()
                if self._version_override is None
                else self._version_override
            )
            self.version_text.set(
                self.copy["installed"] + current if current else self.copy["missing"]
            )
        except (OSError, ValueError, subprocess.SubprocessError):
            self.version_text.set(self.copy["unknown"])

    def _card(self, index, action, title, explanation, button, color, width):
        if action in {"install", "backup"}:
            explanation += "\n\n" + self.copy["duration"]
        card = tk.Frame(
            self.cards,
            background="white",
            highlightbackground="#d8e1e9",
            highlightthickness=1,
        )
        card.pack(fill="x", pady=(0, 12))
        tk.Frame(card, background=color, width=5).pack(side="left", fill="y")
        body = tk.Frame(card, background="white", padx=18, pady=16)
        body.pack(fill="both", expand=True)
        title_label = tk.Label(
            body,
            text=f"{index:02d}  {title}",
            font=("TkDefaultFont", 14, "bold"),
            background="white",
            foreground=color,
            anchor="w",
            justify="left",
            wraplength=width - 115,
        )
        title_label.pack(fill="x", pady=(0, 8))
        self.wrapping.append((title_label, 115))
        label = tk.Label(
            body,
            text=explanation,
            font=("TkDefaultFont", 10),
            background="white",
            foreground="#293d50",
            justify="left",
            anchor="w",
            wraplength=width - 115,
        )
        label.pack(fill="x", pady=(0, 10))
        self.wrapping.append((label, 115))
        if action in {"install", "backup"}:
            path = Path(netmon_documents_path()).parent / "NetMon-Sicherungen"
            hint = tk.Label(
                body,
                text=self.copy["backup"] + str(path),
                background="white",
                foreground="#5a6b7c",
                font=("TkDefaultFont", 9),
                justify="left",
                anchor="w",
                wraplength=width - 115,
            )
            hint.pack(fill="x", pady=(0, 10))
            self.wrapping.append((hint, 115))
        if action == "delete":
            self.manager_checkbox = tk.Checkbutton(
                body,
                text=self.copy["remove_manager"],
                variable=self.remove_manager,
                background="white",
                anchor="w",
            )
            self.manager_checkbox.pack(anchor="w", pady=(0, 10))
        style = f"{action}.Manager.TButton"
        self.style.configure(style, foreground="white", background=color, borderwidth=0)
        self.style.map(
            style,
            background=[("active", color), ("pressed", "#18334a")],
            foreground=[("active", "white")],
        )
        control = ttk.Button(
            body, text=button, style=style, command=lambda: self._action(action)
        )
        control.pack(anchor="w")
        self.buttons[action] = control

    def _resize(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        for widget, margin in self.wrapping:
            widget.configure(wraplength=max(300, event.width - margin))

    def _wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def _action(self, action):
        package = None
        backup_parent = None
        if action == "install":
            package = filedialog.askopenfilename(
                parent=self,
                title=self.copy["choose"],
                filetypes=[(self.copy["package"], "*.deb"), (self.copy["all"], "*")],
            )
            if not package:
                return
        elif action == "backup":
            backup_parent = filedialog.askdirectory(
                parent=self,
                title=self.copy["choose_backup"],
                initialdir=str(
                    Path(netmon_documents_path()).parent / "NetMon-Sicherungen"
                ),
                mustexist=True,
            )
            if not backup_parent:
                return
        try:
            if action == "backup":
                command = action_command(
                    action, backup_parent=backup_parent, lang=self.lang
                )
            else:
                command = action_command(
                    action,
                    package,
                    remove_manager=action == "delete" and self.remove_manager.get(),
                )
            self.runner(command)
            self.status.set(self.copy["launched"])
        except (OSError, ValueError) as exc:
            detail = (
                self.copy["terminal"]
                if isinstance(exc, FileNotFoundError)
                else str(exc)
            )
            messagebox.showerror(self.copy["error"], detail, parent=self)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a verified backup without installing or removing NetMon",
    )
    parser.add_argument(
        "--parent", help="Destination folder outside the active NetMon folder"
    )
    parser.add_argument("--lang", choices=tuple(COPY), help="Backup output language")
    args = parser.parse_args(argv)
    if args.backup:
        if not args.parent:
            parser.error("--backup requires --parent")
        return run_backup(args.parent, lang=args.lang or language())
    if args.parent or args.lang:
        parser.error("--parent and --lang require --backup")
    try:
        window = ManagementWindow()
        window.mainloop()
    except tk.TclError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
