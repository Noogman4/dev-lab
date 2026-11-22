"""System file viewer, checks and reviewed edits."""

from dataclasses import replace
import difflib
from functools import partial
import hashlib
import threading
import tkinter as tk
from tkinter import ttk

try:
    from netmon.core import privileged_config, system_files
    from netmon.ui.button_sound import bind_menu_click_sound
    from netmon.ui.widgets.text_analysis import TextAnalysisActions
except ModuleNotFoundError:  # pragma: no cover - legacy flat layout
    from core import privileged_config, system_files
    from ui.button_sound import bind_menu_click_sound
    from ui.widgets.text_analysis import TextAnalysisActions

MAX_SEARCH_MATCHES = 500


def _text_panel(parent, *, height=14):
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    text = tk.Text(frame, wrap="none", height=height, width=60, font=("Courier", 10))
    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
    text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    text.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")
    frame.pack(fill="both", expand=True)
    return text


def _replace_text(widget, content, *, editable=False):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", content)
    if not editable:
        widget.configure(state="disabled")


def _background(widget, action, complete):
    result = []
    root = widget._root()

    def work():
        try:
            result.append((action(), None))
        except (OSError, ValueError) as exc:
            result.append((None, exc))

    def poll():
        if not widget.winfo_exists():
            return
        if result:
            complete(*result[0])
        else:
            root.after(40, poll)

    threading.Thread(target=work, daemon=True).start()
    root.after(40, poll)


class SystemFilesView:
    def __init__(self, app, parent):
        self.app = app
        self.tr = app.tr
        self.frame = ttk.Frame(parent, padding=(0, 8, 0, 0))
        self.loaded = False
        self.catalog = None
        self.catalog_generation = 0
        self.read_generation = 0
        self.selected_path = None
        self.snapshot = None
        self.editors = {}
        self.check_reports = {}

        body = ttk.Frame(self.frame)
        body.pack(fill="both", expand=True)
        sidebar = ttk.Frame(body)
        sidebar.pack(side="left", fill="y", padx=(0, 6))
        self.filter_var = tk.StringVar(self.frame)
        ttk.Label(sidebar, text=self.tr("system_files_filter", "Dateien filtern")).pack(
            anchor="w"
        )
        filter_entry = ttk.Entry(sidebar, textvariable=self.filter_var, width=18)
        filter_entry.pack(fill="x", pady=(0, 6))
        tree_box = ttk.Frame(sidebar)
        tree_box.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_box, show="tree", selectmode="browse", height=12)
        self.tree.column("#0", width=210, stretch=False)
        tree_scroll = ttk.Scrollbar(
            tree_box, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree_check_path = None
        self.tree_check_menu = tk.Menu(self.tree, tearoff=False)
        self.tree_apt_menu = tk.Menu(self.tree, tearoff=False)
        self.tree_edit_menu = tk.Menu(self.tree, tearoff=False)
        menus = (self.tree_check_menu, self.tree_apt_menu, self.tree_edit_menu)
        for menu in menus:
            menu.add_command(command=self._check_tree_file)
        self.tree_edit_menu.add_command(
            command=lambda: self._check_tree_file(edit=True)
        )
        for enabled in (True, False):
            self.tree_apt_menu.add_command(
                label=self._apt_toggle_label(enabled),
                command=lambda enabled=enabled: self._check_tree_file(enabled),
            )
        play_command = app.__dict__.get("_click_sound_command")
        if play_command:
            for menu in menus:
                menu.configure(postcommand=play_command)
                bind_menu_click_sound(menu, play_command)
        self.tree.bind("<Button-3>", self._show_tree_check_menu)
        self.filter_var.trace_add("write", lambda *_: self._render_catalog())

        panel = ttk.Frame(body)
        panel.pack(side="left", fill="both", expand=True)
        header = ttk.Frame(panel)
        header.pack(fill="x", pady=(0, 6))
        refresh_button = ttk.Button(
            header, text=self.tr("btn_refresh", "Aktualisieren"), command=self.refresh
        )
        refresh_button.pack(side="right")
        self.file_action = ttk.Button(
            header,
            text=self.tr("btn_edit", "Bearbeiten"),
            command=self.edit_hosts,
            state="disabled",
        )
        self.file_action.pack(side="right", padx=(0, 6))
        self.file_edit_button = ttk.Button(
            header,
            text=self.tr("btn_edit", "Bearbeiten"),
            state="disabled",
        )
        self.path_var = tk.StringVar(self.frame)
        ttk.Label(header, textvariable=self.path_var).pack(side="left", fill="x")
        search_bar = ttk.Frame(panel)
        search_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(
            search_bar, text=self.tr("system_files_find", "Im Inhalt suchen")
        ).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar(self.frame)
        self.search_entry = ttk.Entry(
            search_bar, textvariable=self.search_var, width=18
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_prev = ttk.Button(
            search_bar, text="↑", width=3, command=lambda: self._move_match(-1)
        )
        self.search_prev.pack(side="left", padx=(5, 0))
        self.search_next = ttk.Button(
            search_bar, text="↓", width=3, command=lambda: self._move_match(1)
        )
        self.search_next.pack(side="left")
        self.search_status = tk.StringVar(self.frame)
        ttk.Label(search_bar, textvariable=self.search_status, width=14).pack(
            side="left", padx=(5, 0)
        )

        self.text = _text_panel(panel)
        self.text.configure(state="disabled")
        self.text.tag_configure("nsswitch_hosts", underline=True)
        self.text.tag_configure(
            "search_hit", background="#f3ca52", foreground="#101010"
        )
        self.text.tag_configure(
            "search_current", background="#bd6418", foreground="#ffffff"
        )
        self.text.tag_raise("sel")
        self._matches = []
        self._match_position = -1
        self._match_count = ""
        self._match_length = tk.IntVar(self.frame)
        self.search_var.trace_add("write", lambda *_: self._find_matches())
        self.search_entry.bind("<Return>", lambda _e: self._move_match(1))
        self.search_entry.bind("<Shift-Return>", lambda _e: self._move_match(-1))
        for widget in (
            self.text,
            self.tree,
            filter_entry,
            self.search_entry,
            refresh_button,
            self.file_action,
            self.file_edit_button,
            self.search_prev,
            self.search_next,
        ):
            widget.bind("<Control-f>", self._focus_search)
        self._find_matches()
        self.status = tk.StringVar(self.frame)
        ttk.Label(self.frame, textvariable=self.status, anchor="w").pack(
            fill="x", pady=(6, 0)
        )
        self.text_actions = TextAnalysisActions(
            app, self.text, self.status, self._analysis_title, system_file=True
        )

    def on_shown(self):
        if not self.loaded:
            self.refresh()

    def refresh(self):
        self.loaded = True
        self.status.set(self.tr("syslogs_loading", "Wird geladen …"))
        self.catalog_generation += 1
        generation = self.catalog_generation

        def populate(catalog, error):
            if generation != self.catalog_generation:
                return
            if error:
                self.status.set(str(error))
                return
            self.catalog = catalog
            self._render_catalog(reload=True)

        _background(self.frame, system_files.discover_files, populate)

    def _render_catalog(self, *, reload=False):
        if self.catalog is None:
            return
        needle = self.filter_var.get().strip().casefold()
        self.tree.delete(*self.tree.get_children())
        first_file = None
        for group, label in (
            ("mounts", self.tr("system_files_mounts", "Einhängepunkte")),
            ("apparmor", "AppArmor"),
            ("network", self.tr("system_files_network", "Netzwerk & DNS")),
            ("packages", self.tr("system_files_packages", "Paketquellen")),
            ("firewall", self.tr("tab_firewall", "Firewall")),
        ):
            paths = [
                path
                for path in self.catalog.get(group, ())
                if needle in path.casefold()
            ]
            if needle and not paths:
                continue
            self.tree.insert("", "end", iid=group, text=label, open=True)
            for path in paths:
                display_name = (
                    path.removeprefix("/etc/apparmor.d/")
                    if group == "apparmor"
                    else path.rsplit("/", 1)[-1]
                )
                self.tree.insert(group, "end", iid=path, text=display_name)
                first_file = first_file or path
        target = self.selected_path
        if not target or not self.tree.exists(target):
            target = first_file
        if target:
            self.tree.selection_set(target)
            self.tree.see(target)
        if reload or target != self.selected_path:
            self._load(target)
        elif target is None:
            self.status.set(
                self.tr("system_files_no_files_match", "Keine passenden Dateien.")
            )

    def _selected(self, _event=None):
        selection = self.tree.selection()
        if selection and selection[0] != self.selected_path:
            self._load(selection[0])

    def _file_check_action(self, path):
        if path == system_files.FSTAB:
            return self.tr("system_files_check_fstab", "fstab prüfen"), self.check_fstab
        if path == privileged_config.HOSTS:
            return self.tr("system_files_check_hosts", "hosts prüfen"), self.check_hosts
        if path == system_files.RESOLV_CONF:
            return (
                self.tr("system_files_check_resolv", "resolv.conf prüfen"),
                self.check_resolv,
            )
        if system_files.is_apparmor_profile(path):
            return (
                self.tr("system_files_check_apparmor", "Profil prüfen"),
                self.check_apparmor,
            )
        if system_files.is_apt_sources_file(path):
            return (
                self.tr("system_files_check_apt", "Paketquellen prüfen"),
                self.check_apt_sources,
            )
        return None

    def _file_edit_action(self, path):
        if path == privileged_config.HOSTS:
            return self.tr("btn_edit", "Bearbeiten"), self.edit_hosts
        if path == system_files.RESOLV_CONF:
            return (
                self.tr("system_files_edit_dns", "DNS bearbeiten"),
                self.app.open_dns_profile_manager,
            )
        if privileged_config.is_apparmor_profile_path(path):
            return self.tr("btn_edit", "Bearbeiten"), self.edit_apparmor
        return None

    def _show_tree_check_menu(self, event):
        path = self.tree.identify_row(event.y)
        action = self._file_check_action(path)
        if action is None or path == system_files.FSTAB:
            return None
        self.tree_check_path = path
        menu = self.tree_check_menu
        edit_action = self._file_edit_action(path)
        if privileged_config.is_deb822_source(path):
            menu = self.tree_apt_menu
        elif edit_action is not None:
            menu = self.tree_edit_menu
            edit_disabled = (
                path == self.selected_path
                and self.file_edit_button.instate(["disabled"])
            )
            menu.entryconfigure(
                1, label=edit_action[0], state="disabled" if edit_disabled else "normal"
            )
        menu.entryconfigure(0, label=action[0])
        return self.app._show_context_menu(menu, event)

    def _check_tree_file(self, enabled=None, *, edit=False):
        path = self.tree_check_path
        self.app._close_active_context_menu()
        if not path or not self.tree.exists(path):
            return
        if edit:
            command = self._file_edit_action(path)[1]
        elif enabled is not None:
            command = partial(self.review_apt_source, enabled)
        else:
            command = self._file_check_action(path)[1]
        self.tree.focus(path)
        self.tree.selection_set(path)
        if (path == self.selected_path and self.snapshot is not None) or (
            edit and path == system_files.RESOLV_CONF
        ):
            command()
        else:
            self._load(path, after_load=command)

    def _load(self, path, *, after_load=None, as_admin=False):
        self.read_generation += 1
        generation = self.read_generation
        self.selected_path = path
        self.snapshot = None
        self.file_action.state(["disabled"])
        self.file_edit_button.state(["disabled"])
        edit_action = self._file_edit_action(path)
        if edit_action is not None:
            self.file_edit_button.configure(text=edit_action[0], command=edit_action[1])
            self.file_edit_button.pack(
                side="right", padx=(0, 6), after=self.file_action
            )
            if path == system_files.RESOLV_CONF:
                self.file_edit_button.state(["!disabled"])
        else:
            self.file_edit_button.pack_forget()
        check_action = self._file_check_action(path)
        label, command = check_action or (
            self.tr("btn_edit", "Bearbeiten"),
            "",
        )
        self.file_action.configure(text=label, command=command)
        self.path_var.set(path if path and path.startswith("/") else "")
        self._show_text("")
        if path is None:
            self.status.set(
                self.tr("system_files_no_files_match", "Keine passenden Dateien.")
            )
            return
        if not path.startswith("/"):
            key, fallback = (
                ("system_files_choose", "Datei auswählen.")
                if self.tree.get_children(path)
                else ("system_files_none", "Keine Dateien gefunden.")
            )
            self.status.set(self.tr(key, fallback))
            return
        self.status.set(self.tr("syslogs_loading", "Wird geladen …"))

        def show(snapshot, error):
            if generation != self.read_generation:
                return
            if error:
                if path in privileged_config.PROTECTED_READ_PATHS and (
                    as_admin or isinstance(error, PermissionError)
                ):
                    self._offer_admin_read(path, failed=as_admin)
                    return
                key, fallback = (
                    ("system_files_missing", "Datei ist nicht vorhanden.")
                    if isinstance(error, FileNotFoundError)
                    else ("system_files_unreadable", "Datei ist nicht als Text lesbar.")
                )
                self.status.set(self.tr(key, fallback))
                return
            self.snapshot = snapshot
            if snapshot.link:
                self.path_var.set(f"{path} → {snapshot.link}")
            self._show_text(snapshot.text or "")
            if snapshot.text is not None and check_action is not None:
                self.file_action.state(["!disabled"])
            if snapshot.hosts_editable or snapshot.apparmor_editable:
                self.file_edit_button.state(["!disabled"])
            self.status.set(
                self.tr("system_files_read_only", "Schreibgeschützt")
                if snapshot.text is not None
                else self.tr(
                    "system_files_link_only", "Nur das Linkziel wird angezeigt."
                )
            )
            if after_load is not None and snapshot.text is not None:
                after_load()

        def read():
            if as_admin:
                return system_files.FileSnapshot(
                    privileged_config.read_system_config(path)
                )
            return system_files.read_file(path)

        _background(self.frame, read, show)

    def _offer_admin_read(self, path, *, failed):
        if not privileged_config.hosts_save_available():
            self.status.set(
                self.tr(
                    "system_files_admin_reader_required",
                    "Das Lesen mit Adminrechten benötigt den Helfer aus dem installierten NetMon-Paket.",
                )
            )
            return

        def read():
            if self.selected_path != path:
                return
            if not self.app.ensure_sudo_session(path):
                self.status.set(
                    self.tr("system_files_auth_cancelled", "Autorisierung abgebrochen.")
                )
                return
            if self.selected_path == path:
                self._load(path, as_admin=True)

        self.file_action.configure(
            text=self.tr("system_files_admin_read", "Mit Adminrechten lesen"),
            command=read,
        )
        self.file_action.state(["!disabled"])
        if failed:
            self.status.set(
                self.tr(
                    "system_files_admin_read_failed",
                    "Die Datei konnte mit Adminrechten nicht gelesen werden.",
                )
            )
        else:
            self.status.set(
                self.tr(
                    "system_files_permission_denied",
                    "Die Datei benötigt besondere Leserechte.",
                )
            )

    def _analysis_title(self):
        return self.tr("system_files_prompt_source", "Systemdatei: {path}").format(
            path=self.selected_path
        )

    def _show_text(self, text):
        _replace_text(self.text, text)
        if self.selected_path == system_files.NSSWITCH:
            for number, line in enumerate(text.split("\n"), 1):
                database, separator, _ = line.partition(":")
                if separator and database.strip() == "hosts":
                    self.text.tag_add("nsswitch_hosts", f"{number}.0", f"{number}.end")
        self._find_matches()

    def _focus_search(self, _event=None):
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")
        return "break"

    def _find_matches(self):
        self._matches.clear()
        self._match_position = -1
        self.text.tag_remove("search_hit", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        needle = self.search_var.get()
        following = "1.0"
        if needle:
            while len(self._matches) < MAX_SEARCH_MATCHES:
                start = self.text.search(
                    needle, following, "end-1c", nocase=True, count=self._match_length
                )
                if not start:
                    break
                following = self.text.index(f"{start}+{self._match_length.get()}c")
                self.text.tag_add("search_hit", start, following)
                self._matches.append((start, following))
        state = "!disabled" if self._matches else "disabled"
        self.search_prev.state([state])
        self.search_next.state([state])
        if not self._matches:
            self.search_status.set(
                self.tr("linux_help_reader_no_match", "Keine Treffer.")
                if needle
                else ""
            )
            return
        self._match_count = str(len(self._matches))
        if len(self._matches) == MAX_SEARCH_MATCHES and self.text.search(
            needle, following, "end-1c", nocase=True
        ):
            self._match_count += "+"
        self._move_match(1)

    def _move_match(self, direction):
        if self._matches:
            self._match_position = (self._match_position + direction) % len(
                self._matches
            )
            start, end = self._matches[self._match_position]
            self.text.tag_remove("search_current", "1.0", "end")
            self.text.tag_add("search_current", start, end)
            self.text.see(start)
            self.search_status.set(
                self.tr("system_files_match_count", "{current} von {total}").format(
                    current=self._match_position + 1, total=self._match_count
                )
            )
        return "break"

    def _fstab_report_text(self, result):
        lines = []
        if result.syntax_errors == 0:
            lines.append(self.tr("system_files_fstab_syntax_ok", "Syntax in Ordnung."))
        elif result.syntax_errors is not None:
            lines.append(
                self.tr(
                    "system_files_fstab_syntax_errors",
                    "Syntaxfehler gefunden ({count}).",
                ).format(count=result.syntax_errors)
            )
        for target in result.optional_missing:
            lines.append(
                self.tr(
                    "system_files_fstab_optional_missing",
                    "Das optionale Laufwerk unter {target} ist derzeit nicht verfügbar (noauto,nofail).",
                ).format(target=target)
            )
        for target, filesystem in result.mounted_types:
            lines.append(
                self.tr(
                    "system_files_fstab_mounted_type",
                    "{target} ist laut Kernel als {filesystem} eingehängt. Die direkte Prüfung am Datenträger braucht Leserechte.",
                ).format(target=target, filesystem=filesystem)
            )
        if result.type_unavailable:
            lines.append(
                self.tr(
                    "system_files_fstab_type_unavailable",
                    "Fehlende Leserechte verhindern die Prüfung des Dateisystemtyps für {targets}.",
                ).format(targets=", ".join(result.type_unavailable))
            )
        for path in result.active_swaps:
            lines.append(
                self.tr(
                    "system_files_fstab_swap_active",
                    "Die Swapdatei {path} ist laut Kernel aktiv.",
                ).format(path=path)
            )
        if lines and result.detail:
            lines.extend(
                (
                    "",
                    self.tr(
                        "system_files_fstab_original", "Originalausgabe von findmnt"
                    ),
                    result.detail,
                )
            )
        return "\n".join(lines) if lines else result.detail

    def check_fstab(self):
        if self.selected_path != system_files.FSTAB:
            return None
        return self._open_check_report(
            title=self.tr("system_files_check_fstab", "fstab prüfen"),
            hint=self.tr(
                "system_files_fstab_check_hint",
                "Prüfung des angezeigten Stands von /etc/fstab mit findmnt.",
            ),
            checker=system_files.check_fstab,
            missing=self.tr(
                "system_files_fstab_check_missing", "Das Prüfwerkzeug findmnt fehlt."
            ),
            render=self._fstab_report_text,
        )

    def check_hosts(self):
        if self.selected_path != privileged_config.HOSTS:
            return None
        return self._open_check_report(
            title=self.tr("system_files_check_hosts", "hosts prüfen"),
            hint=self.tr(
                "system_files_hosts_check_hint",
                "Prüft die IP-Adressen und Rechnernamen in der angezeigten Datei.",
            ),
            checker=system_files.check_hosts,
            render=lambda result: result.detail
            or self.tr(
                "system_files_hosts_check_clean",
                "Die Einträge entsprechen dem hosts-Dateiformat.",
            ),
        )

    def check_resolv(self):
        if self.selected_path != system_files.RESOLV_CONF:
            return None

        def render(result):
            if result.outcome == "errors":
                return self.tr(
                    "system_files_resolv_invalid",
                    "Ungültige Nameserver-Einträge in folgenden Zeilen: {lines}.",
                ).format(lines=result.detail)
            if result.outcome == "warnings":
                return self.tr(
                    "system_files_resolv_no_nameserver",
                    "In der Datei ist kein Nameserver eingetragen.",
                )
            return self.tr(
                "system_files_resolv_check_clean",
                "Die Nameserver-Einträge enthalten gültige IP-Adressen.",
            )

        return self._open_check_report(
            title=self.tr("system_files_check_resolv", "resolv.conf prüfen"),
            hint=self.tr(
                "system_files_resolv_check_hint",
                "Prüft die Nameserver-Einträge in der angezeigten Datei.",
            ),
            checker=system_files.check_resolv_nameservers,
            render=render,
        )

    def check_apparmor(self):
        path = self.selected_path
        if not system_files.is_apparmor_profile(path):
            return None

        def render(result):
            if result.outcome == "ok":
                return self.tr(
                    "system_files_apparmor_check_clean",
                    "Der Parser meldet für {path} keine Fehler oder Warnungen.",
                ).format(path=path)
            return result.detail

        return self._open_check_report(
            title=self.tr("system_files_check_apparmor", "Profil prüfen"),
            hint=self.tr(
                "system_files_apparmor_check_hint",
                "Prüfung des angezeigten Profils {path} ohne Laden in den Kernel oder Schreiben in den Cache.",
            ).format(path=path),
            checker=system_files.check_apparmor_profile,
            missing=self.tr(
                "system_files_apparmor_check_missing",
                "Das Prüfwerkzeug apparmor_parser fehlt.",
            ),
            render=render,
        )

    def check_apt_sources(self):
        path = self.selected_path
        if not system_files.is_apt_sources_file(path):
            return None

        def render(result):
            if result.outcome == "ok":
                return self.tr(
                    "system_files_apt_check_clean",
                    "APT meldet für {path} keine Fehler oder Warnungen.",
                ).format(path=path)
            return result.detail

        return self._open_check_report(
            title=self.tr("system_files_check_apt", "Paketquellen prüfen"),
            hint=self.tr(
                "system_files_apt_check_hint",
                "APT prüft die angezeigte Datei {path} lokal.",
            ).format(path=path),
            checker=lambda text: system_files.check_apt_sources(path, text),
            missing=self.tr(
                "system_files_apt_check_missing", "Das Prüfwerkzeug apt-get fehlt."
            ),
            render=render,
        )

    def _apt_toggle_label(self, enabled):
        if enabled:
            return self.tr(
                "system_files_apt_enable", "Alle Quellen in der Datei aktivieren"
            )
        return self.tr(
            "system_files_apt_disable", "Alle Quellen in der Datei deaktivieren"
        )

    def review_apt_source(self, enabled):
        path = self.selected_path
        if (
            not privileged_config.is_deb822_source(path)
            or self.snapshot is None
            or self.snapshot.text is None
        ):
            return None
        original = self.snapshot.text

        def render(result):
            if result.outcome == "ok" and not result.digest:
                return self.tr("system_files_no_changes", "Keine Änderungen.")
            diff = "\n".join(
                difflib.unified_diff(
                    original.split("\n"),
                    result.draft.split("\n"),
                    fromfile=path,
                    tofile=self.tr("system_files_draft", "Entwurf"),
                    lineterm="",
                )
            )
            report = result.detail
            if result.outcome == "ok":
                report = self.tr(
                    "system_files_apt_review_clean",
                    "APT meldet im Entwurf und den übrigen Standardquellen keine Fehler oder Warnungen.",
                )
            return "\n\n".join(part for part in (diff, report) if part)

        return self._open_check_report(
            title=self._apt_toggle_label(enabled),
            hint=self.tr(
                "system_files_apt_review_warning",
                "Nur für erfahrene Linux-Nutzer. Diese Änderung betrifft alle Einträge in {path} und kann Paketupdates beeinflussen.",
            ).format(path=path),
            checker=lambda text: system_files.review_apt_source_change(
                path, text, enabled
            ),
            missing=self.tr(
                "system_files_apt_check_missing", "Das Prüfwerkzeug apt-get fehlt."
            ),
            render=render,
            save_review=True,
        )

    def _open_check_report(
        self, *, title, hint, checker, missing="", render=None, save_review=False
    ):
        path = self.selected_path
        report_key = (path, title) if save_review else path
        report = self.check_reports.get(report_key)
        if report is not None and report.winfo_exists():
            report.deiconify()
            report.lift()
            return report
        snapshot = self.snapshot
        if snapshot is None or snapshot.text is None:
            return None

        self.check_reports[report_key] = window = tk.Toplevel(self.frame)
        window.title(title)
        window.transient(self.frame.winfo_toplevel())

        def forget_report(event):
            if event.widget is window:
                self.check_reports.pop(report_key, None)

        window.bind("<Destroy>", forget_report)
        pane = ttk.Frame(window, padding=10)
        pane.pack(fill="both", expand=True)
        feedback = tk.StringVar(window, hint)
        ttk.Label(pane, textvariable=feedback, wraplength=560).pack(
            fill="x", pady=(0, 6)
        )
        status = ttk.Label(
            pane,
            text=self.tr("system_files_fstab_check_running", "Prüfung läuft …"),
            wraplength=560,
        )
        status.pack(fill="x", pady=(0, 6))
        output = _text_panel(pane, height=10)
        output.configure(state="disabled", wrap="word")
        actions = TextAnalysisActions(
            self.app,
            output,
            feedback,
            lambda: self.tr(
                "system_files_check_report_source", "Prüfbericht zu {path}"
            ).format(path=path),
            system_file=True,
        )

        saving = False

        def close_report(_event=None):
            if saving:
                return "break"
            if self.app.__dict__.get("_active_context_menu") is actions.menu:
                self.app._close_active_context_menu()
            window.destroy()
            return "break"

        window.protocol("WM_DELETE_WINDOW", close_report)
        window.bind("<Escape>", close_report)
        close = ttk.Button(
            pane, text=self.tr("btn_close", "Schließen"), command=close_report
        )
        close.pack(side="right", pady=(6, 0))
        save_button = None
        if save_review:
            save_button = ttk.Button(
                pane, text=self.tr("btn_save", "Speichern"), state="disabled"
            )
            save_button.pack(side="right", padx=(0, 6), pady=(6, 0))

        def save(result):
            nonlocal saving
            saving = True
            save_button.state(["disabled"])
            close.state(["disabled"])
            status.configure(text=self.tr("system_files_saving", "Wird gespeichert …"))
            if not self.app.ensure_sudo_session(path):
                saving = False
                close.state(["!disabled"])
                save_button.state(["!disabled"])
                status.configure(
                    text=self.tr(
                        "system_files_auth_cancelled", "Autorisierung abgebrochen."
                    )
                )
                return

            def finish(saved, error):
                nonlocal saving
                saving = False
                close.state(["!disabled"])
                if error or saved[0] != 0:
                    status.configure(
                        text=self.tr(
                            "system_files_save_failed",
                            "Speicherstatus bitte durch erneutes Laden prüfen. {detail}",
                        ).format(detail=str(error) if error else saved[1])
                    )
                    return
                status.configure(
                    text=self.tr(
                        "system_files_saved", "Gespeichert. Sicherung unter {path}"
                    ).format(path=saved[1])
                )
                if self.selected_path == path:
                    self._load(path)

            _background(
                window,
                lambda: privileged_config.save_apt_source_config(
                    path, result.draft, result.digest
                ),
                finish,
            )

        def show(result, error):
            if error:
                status.configure(
                    text=self.tr(
                        "system_files_fstab_check_failed",
                        "Prüfung konnte nicht ausgeführt werden.",
                    )
                )
                _replace_text(output, str(error))
                return
            if result.outcome == "missing":
                status.configure(text=missing)
                return
            key, message = {
                "ok": (
                    "system_files_fstab_check_ok",
                    "Keine Fehler oder Warnungen gemeldet.",
                ),
                "warnings": (
                    "system_files_fstab_check_warnings",
                    "Prüfung meldet Warnungen.",
                ),
                "errors": ("system_files_fstab_check_errors", "Prüfung meldet Fehler."),
                "timeout": (
                    "system_files_fstab_check_timeout",
                    "Zeitlimit der Prüfung überschritten.",
                ),
            }[result.outcome]
            status.configure(text=self.tr(key, message))
            _replace_text(output, render(result) if render else result.detail)
            if (
                save_button is not None
                and result.digest
                and result.outcome in {"ok", "warnings"}
            ):
                if privileged_config.hosts_save_available():
                    save_button.configure(command=lambda: save(result), state="normal")
                else:
                    feedback.set(
                        self.tr(
                            "system_files_install_required",
                            "Speichern benötigt den Schreibhelfer aus dem installierten NetMon-Paket.",
                        )
                    )

        _background(window, lambda: checker(snapshot.text), show)
        return window

    def edit_hosts(self):
        snapshot = self.snapshot
        if snapshot is None or not snapshot.hosts_editable:
            return
        risk = self.tr(
            "system_files_hosts_risk",
            "Änderungen an /etc/hosts können lokale Namen auf falsche Adressen umleiten.",
        )
        return self._open_file_editor(
            privileged_config.HOSTS, snapshot, risk, privileged_config.save_hosts_config
        )

    def edit_apparmor(self):
        path, snapshot = self.selected_path, self.snapshot
        if snapshot is None or not snapshot.apparmor_editable:
            return
        risk = self.tr(
            "system_files_apparmor_edit_risk",
            "Änderungen können den Schutz oder die Funktion von Programmen beeinflussen. "
            "Neue Regeln wirken beim nächsten Laden des Profils.",
        )
        return self._open_file_editor(
            path,
            snapshot,
            risk,
            lambda draft, digest: privileged_config.save_apparmor_profile(
                path, draft, digest
            ),
            syntax_check=system_files.check_apparmor_profile,
        )

    def _open_file_editor(
        self, path, snapshot, risk, save_config, *, syntax_check=None
    ):
        if path in self.editors:
            window = self.editors[path]
            window.deiconify()
            window.lift()
            return window
        self.editors[path] = window = tk.Toplevel(self.frame)

        def forget_editor(event):
            if event.widget is window:
                self.editors.pop(path, None)

        window.bind("<Destroy>", forget_editor)
        window.title(f"{self.tr('btn_edit', 'Bearbeiten')} · {path}")
        window.transient(self.frame.winfo_toplevel())
        pane = ttk.Frame(window, padding=10)
        pane.pack(fill="both", expand=True)
        warning = self.tr(
            "system_files_warning",
            "Nur für erfahrene Linux-Nutzer. Änderungen an Systemdateien können den "
            "Systemstart, das Netzwerk oder Sicherheitsfunktionen beeinträchtigen. "
            "Ändere nur Einträge, deren Wirkung du kennst.",
        )
        ttk.Label(pane, text=f"{warning}\n{risk}", wraplength=580).pack(
            fill="x", pady=(0, 8)
        )
        text = _text_panel(pane)
        original = snapshot.text
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
        _replace_text(text, original, editable=True)
        text.focus_set()
        status = tk.StringVar(window)
        title = self.tr("system_files_editor_prompt_source", "Entwurf zu {path}")
        TextAnalysisActions(
            self.app,
            text,
            status,
            lambda: title.format(path=path),
            system_file=True,
            allow_paste=True,
        )
        ttk.Label(pane, textvariable=status, wraplength=580).pack(fill="x", pady=(6, 0))
        controls = ttk.Frame(pane)
        controls.pack(fill="x", pady=(8, 0))
        cancel = ttk.Button(
            controls, text=self.tr("btn_cancel", "Abbrechen"), command=window.destroy
        )
        cancel.pack(side="right")
        action = ttk.Button(
            controls, text=self.tr("system_files_review", "Änderungen prüfen")
        )
        action.pack(side="right", padx=(0, 6))

        def review():
            draft = text.get("1.0", "end-1c")
            if draft == original:
                status.set(self.tr("system_files_no_changes", "Keine Änderungen."))
                return
            if syntax_check is None:
                try:
                    privileged_config.validate_hosts(draft)
                except ValueError as exc:
                    status.set(str(exc))
                    return
                preview(draft)
            else:
                action.state(["disabled"])
                text.configure(state="disabled")
                status.set(
                    self.tr("system_files_fstab_check_running", "Prüfung läuft …")
                )
                _background(
                    window,
                    lambda: syntax_check(draft),
                    lambda result, error: reviewed(draft, result, error),
                )

        def reviewed(draft, result, error):
            if error:
                edit(draft)
                status.set(str(error))
                return
            key, message = {
                "ok": (
                    "system_files_fstab_check_ok",
                    "Keine Fehler oder Warnungen gemeldet.",
                ),
                "warnings": (
                    "system_files_fstab_check_warnings",
                    "Prüfung meldet Warnungen.",
                ),
                "errors": ("system_files_fstab_check_errors", "Prüfung meldet Fehler."),
                "missing": (
                    "system_files_apparmor_check_missing",
                    "Das Prüfwerkzeug apparmor_parser fehlt.",
                ),
                "timeout": (
                    "system_files_fstab_check_timeout",
                    "Zeitlimit der Prüfung überschritten.",
                ),
            }[result.outcome]
            preview(
                draft,
                message=self.tr(key, message),
                detail=result.detail,
                can_save=result.outcome in {"ok", "warnings"},
            )

        def preview(draft, *, message="", detail="", can_save=True):
            diff = "\n".join(
                difflib.unified_diff(
                    original.split("\n"),
                    draft.split("\n"),
                    fromfile=path,
                    tofile=self.tr("system_files_draft", "Entwurf"),
                    lineterm="",
                )
            )
            _replace_text(text, f"{detail}\n\n{diff}" if detail else diff)
            status.set(message or risk)
            action.configure(
                text=self.tr("btn_save", "Speichern"), command=lambda: save(draft)
            )
            cancel.configure(
                text=self.tr("system_files_back", "Zurück zum Entwurf"),
                command=lambda: edit(draft),
            )
            if not can_save:
                action.state(["disabled"])
            elif not privileged_config.hosts_save_available():
                action.state(["disabled"])
                status.set(
                    self.tr(
                        "system_files_install_required",
                        "Speichern benötigt den Schreibhelfer aus dem installierten NetMon-Paket.",
                    )
                )
            else:
                action.state(["!disabled"])

        def edit(draft):
            _replace_text(text, draft, editable=True)
            status.set("")
            cancel.configure(
                text=self.tr("btn_cancel", "Abbrechen"), command=window.destroy
            )
            action.configure(
                text=self.tr("system_files_review", "Änderungen prüfen"), command=review
            )
            action.state(["!disabled"])
            text.focus_set()

        def save(draft):
            action.state(["disabled"])
            cancel.state(["disabled"])
            window.protocol("WM_DELETE_WINDOW", lambda: None)
            if not self.app.ensure_sudo_session(path):
                finish(draft, None, None)
                return
            status.set(self.tr("system_files_saving", "Wird gespeichert …"))
            _background(
                window,
                lambda: save_config(draft, digest),
                lambda result, error: finish(draft, result, error),
            )

        def finish(draft, result, error):
            window.protocol("WM_DELETE_WINDOW", window.destroy)
            cancel.state(["!disabled"])
            action.state(["!disabled"])
            if error:
                status.set(str(error))
            elif result is None:
                status.set(
                    self.tr("system_files_auth_cancelled", "Autorisierung abgebrochen.")
                )
            elif result[0] == 0:
                window.destroy()
                if self.selected_path == path:
                    # Publish the committed text without discarding the saved-backup status.
                    self.read_generation += 1
                    self.snapshot = replace(snapshot, text=draft)
                    self._show_text(self.snapshot.text)
                self.status.set(
                    self.tr(
                        "system_files_saved", "Gespeichert. Sicherung unter {path}"
                    ).format(path=result[1])
                )
            else:
                status.set(
                    self.tr(
                        "system_files_save_failed",
                        "Speicherstatus bitte durch erneutes Laden prüfen. {detail}",
                    ).format(detail=result[1])
                )

        action.configure(command=review)
        return window
