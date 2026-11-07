"""Selection-based review UI for PATH Guard; mutations require explicit consent."""

from tkinter import messagebox, ttk

from ..services.ai_analysis_service import AiAnalysisService


def tr(app, key, fallback):
    return app.tr(key, fallback)


def display_target(app, target):
    return (
        target
        if target != ""
        else tr(
            app,
            "path_guard_empty_entry",
            "(leerer Eintrag → aktuelles Verzeichnis)",
        )
    )


def copy_prompt(app):
    """Copy the last complete report using the shared local prompt builder."""
    from .security_audit_controller import _format_path_guard_result

    result = app.__dict__.get("path_guard_last_result")
    if not result:
        app.log(tr(app, "path_guard_copy_empty", "PATH Guard: zuerst PATH prüfen."))
        return False
    text = _format_path_guard_result(app, result)
    for row in result.get("review_items", []):
        text += f"\n- {display_target(app, row['target'])} | {row['issue']} | {row['state']}"
    # Export every finding, including development paths hidden by Chad filters.
    # The shared builder still redacts credentials before clipboard export.
    prompt = AiAnalysisService().build_prompt("PATH Guard Analyse", text)
    app.clipboard_clear()
    app.clipboard_append(prompt)
    app.log(
        tr(
            app,
            "path_guard_copy_done",
            "PATH Guard: Prompt kopiert; mit Strg+V im gewünschten Chat einfügen.",
        )
    )
    return True


def review_status(app, result):
    summary = result.get("review_summary")
    if summary is None:
        return None
    if summary["high"]:
        return "error", tr(app, "path_review_high", "PATH Guard: hohe Risiken offen")
    if summary["error"]:
        return "unknown", tr(
            app, "path_review_unknown", "PATH Guard: Bestätigungen nicht prüfbar"
        )
    if summary["medium"]:
        return "warning", tr(
            app, "path_review_open", "PATH Guard: {count} offene Warnungen"
        ).format(count=summary["medium"])
    if summary["accepted"]:
        return "ok", tr(
            app,
            "path_review_accepted_summary",
            "PATH Guard: keine offenen Warnungen; geprüfte Ausnahmen: {count}",
        ).format(count=summary["accepted"])
    return "ok", tr(app, "path_review_clean", "PATH Guard: keine offenen Warnungen")


def summary_text(app, result):
    summary = result.get("review_summary")
    if summary is None:
        return ""
    text = tr(
        app,
        "path_review_report",
        "Bearbeitung: {open} offen, {accepted} geprüft / Risiko akzeptiert.\nDie ursprüngliche Risikobewertung bleibt im Bericht sichtbar; eine Bestätigung ist keine Reparatur.",
    ).format(open=summary["high"] + summary["medium"], accepted=summary["accepted"])
    if summary["error"]:
        text += "\n" + summary["error"]
    return "\n\n" + text


def selected(app):
    table = app.__dict__.get("path_guard_findings_table")
    selection = table.selection() if table is not None else ()
    if not selection:
        return None
    return app.__dict__.get("path_guard_review_rows", {}).get(selection[0])


def update_buttons(app):
    row = selected(app)
    for name, enabled in (
        ("details", bool(row)),
        (
            "accept",
            bool(
                row
                and row["can_accept"]
                and row["state"] != "geprüft / Risiko akzeptiert"
            ),
        ),
        ("repair", bool(row and row["can_repair"])),
        ("revoke", bool(row and row["has_review"])),
    ):
        button = app.__dict__.get("path_guard_review_buttons", {}).get(name)
        if button is not None:
            button.configure(state="normal" if enabled else "disabled")


def render(app, result):
    table = app.__dict__.get("path_guard_findings_table")
    if table is None:
        return
    prior = table.selection()
    rows = result.get("review_items", [])
    app.path_guard_review_rows = {row["id"]: row for row in rows}
    table.delete(*table.get_children())
    for row in rows:
        from .security_audit_controller import _translate_path_guard_issue

        labels = {
            "offen": ("path_review_state_open", "offen"),
            "geprüft / Risiko akzeptiert": (
                "path_review_state_accepted",
                "geprüft / Risiko akzeptiert",
            ),
            "offen / Bestätigung veraltet": (
                "path_review_state_stale",
                "offen / Bestätigung veraltet",
            ),
            "nicht mehr gemeldet": ("path_review_state_absent", "nicht mehr gemeldet"),
        }
        state_key, state_fallback = labels[row["state"]]
        table.insert(
            "",
            "end",
            iid=row["id"],
            values=(
                tr(app, "path_guard_severity_" + row["severity"], row["severity"]),
                display_target(app, row["target"]),
                _translate_path_guard_issue(app, row["issue"]),
                tr(app, state_key, state_fallback),
            ),
        )
    if prior and prior[0] in app.path_guard_review_rows:
        table.selection_set(prior[0])
    update_buttons(app)


def details(app):
    row = selected(app)
    if row is None:
        return
    text = display_target(app, row["target"]) + "\n\n" + row["explanation"]
    text += "\n\n" + tr(
        app,
        "path_review_guidance",
        "Vorgehen: Herkunft des Pfads prüfen. Fehlende oder unerwartete Einträge in der Shell-/IDE-Konfiguration korrigieren. Bei gemeinsam genutzten Gruppen vorher klären, wer Schreibzugriff benötigt. Danach erneut prüfen. Es werden keine Shell-Profile automatisch umgeschrieben.",
    )
    messagebox.showinfo(
        tr(app, "path_review_details", "Befund prüfen / Anleitung"), text, parent=app
    )


def act(app, action):
    row = selected(app)
    if row is None:
        return
    service = app.path_guard_service
    try:
        if action == "accept":
            if not row["can_accept"]:
                return
            prompt = row["target"] + "\n\n" + row["issue"] + "\n\n" + row["explanation"]
            prompt += "\n\n" + tr(
                app,
                "path_review_accept_prompt",
                "Herkunft und Zugriffsrechte geprüft und dieses Risiko bewusst akzeptiert?\nDie Ausnahme gilt nur für diesen Hinweis und die aktuelle PATH-Reihenfolge, Verzeichnisidentität, Eigentümer, Rechte, ACLs und Gruppeninformationen. Änderungen werden bei der nächsten Prüfung erneut gemeldet.",
            )
            if not messagebox.askyesno(
                tr(app, "path_review_accept", "Als geprüft bestätigen …"),
                prompt,
                parent=app,
            ):
                return
            service.accept_finding(row["id"], row["fingerprint"])
        elif action == "repair":
            if not row["can_repair"]:
                return
            mode = row["snapshot"][-1]["mode"]
            prompt = row["target"] + f"\n\n{mode:04o} → {mode & ~0o020:04o}\n\n"
            prompt += tr(
                app,
                "path_review_repair_prompt",
                "Nur das Gruppenschreibrecht dieses eigenen Ordners entfernen?\nKeine rekursive Änderung, kein sudo, keine Änderung an Dateien oder übergeordneten Ordnern. Gemeinsam arbeitende Gruppen können dadurch den Ordner nicht mehr verändern. Andere PATH-Warnungen können bestehen bleiben.",
            )
            if not messagebox.askyesno(
                tr(app, "path_review_repair", "Gruppenschreibrecht entfernen …"),
                prompt,
                parent=app,
            ):
                return
            service.repair_finding(row["id"], row["fingerprint"])
            messagebox.showinfo(
                tr(app, "path_review_repair_done", "Rechteänderung geprüft"),
                tr(
                    app,
                    "path_review_repair_note",
                    "Gruppenschreibrecht entfernt. Anschließend werden alle Befunde neu geprüft; andere Hinweise sind dadurch nicht automatisch behoben.",
                ),
                parent=app,
            )
        elif action == "revoke":
            service.revoke_finding(row["id"])
    except (OSError, ValueError) as exc:
        messagebox.showerror(
            tr(app, "path_review_action_error", "Bearbeitung nicht bestätigt"),
            str(exc)
            + "\n"
            + tr(
                app,
                "path_review_recheck_note",
                "Der aktuelle Zustand wird erneut geprüft. Bei einem Schreibfehler können Teiländerungen bereits erfolgt sein.",
            ),
            parent=app,
        )
    finally:
        # Even declined/stale proposals must never leave an old green verdict.
        app.run_path_guard_check()


def build_review_panel(app, pane):
    frame = ttk.LabelFrame(
        pane, text=tr(app, "path_review_title", "Befunde bearbeiten"), padding=6
    )
    pane.add(frame, weight=1)
    table_frame = ttk.Frame(frame)
    table_frame.pack(fill="both", expand=True)
    table = app.path_guard_findings_table = ttk.Treeview(
        table_frame,
        columns=("risk", "path", "issue", "state"),
        show="headings",
        selectmode="browse",
        height=5,
    )
    for column, key, fallback, width in (
        ("risk", "path_review_risk", "Risiko", 75),
        ("path", "path_review_path", "Pfad", 300),
        ("issue", "path_review_issue", "Befund", 280),
        ("state", "path_review_state", "Bearbeitungsstand", 240),
    ):
        table.heading(column, text=tr(app, key, fallback))
        table.column(column, width=width, minwidth=65)
    table.grid(row=0, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
    horizontal.grid(row=1, column=0, sticky="ew")
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)
    actions = ttk.Frame(frame)
    actions.pack(fill="x", pady=(6, 0))
    app.path_guard_review_buttons = {}
    for name, key, label in (
        ("details", "path_review_details", "Befund prüfen / Anleitung"),
        ("repair", "path_review_repair", "Gruppenschreibrecht entfernen …"),
        ("accept", "path_review_accept", "Als geprüft bestätigen …"),
        ("revoke", "path_review_revoke", "Bestätigung zurücknehmen"),
    ):
        callback = (
            (lambda: details(app))
            if name == "details"
            else (lambda action=name: act(app, action))
        )
        button = ttk.Button(
            actions, text=tr(app, key, label), command=callback, state="disabled"
        )
        button.pack(side="left", padx=(0, 6))
        app.path_guard_review_buttons[name] = button
    table.bind("<<TreeviewSelect>>", lambda _event: update_buttons(app))
    table.bind("<Double-1>", lambda _event: details(app))
    render(app, app.__dict__.get("path_guard_last_result") or {})
