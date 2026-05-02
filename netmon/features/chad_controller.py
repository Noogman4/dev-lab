"""Chad controller helpers for NetMon."""

from __future__ import annotations

import os
import threading

try:
    from netmon.services.ai_analysis_service import AiAnalysisService
except ModuleNotFoundError:
    try:
        from services.ai_analysis_service import AiAnalysisService
    except ModuleNotFoundError:
        AiAnalysisService = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception:
    tk = None
    filedialog = messagebox = ttk = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None


def log_chad_error(app, source: str, error_text: str):
    msg = (error_text or "").strip()
    if not msg:
        return
    if len(msg) > 1200:
        msg = msg[:1200].rstrip() + " ..."
    app.log_safe(f"Chad {source} Fehler: {msg}")


def append_to_chad_output(app, title: str, text: str):
    widget = app.__dict__.get("chad_analysis_text")
    if widget is None:
        return
    text = (text or "").strip()
    if not text:
        return

    widget.configure(state="normal")
    current = widget.get("1.0", "end").strip()
    if current:
        widget.insert("end", "\n\n")

    role_key = (title or "").strip().lower()
    if role_key in {"du", "user"}:
        header_tag = "chat_user_header"
        body_tag = "chat_user_body"
    elif role_key in {"chad", "chad analyse", "chad antwort", "assistant"}:
        header_tag = "chat_assistant_header"
        body_tag = "chat_assistant_body"
    else:
        header_tag = "chat_system_header"
        body_tag = "chat_system_body"

    widget.insert("end", f"--- {title} ---\n", header_tag)
    widget.insert("end", text, body_tag)
    widget.configure(state="disabled")
    try:
        if app.chad_auto_scroll_var.get():
            widget.see("end")
    except Exception:
        pass


def scroll_chad_output_to_top(app):
    try:
        app.chad_analysis_text.see("1.0")
    except Exception:
        pass


def scroll_chad_output_to_bottom(app):
    try:
        app.chad_analysis_text.see("end")
    except Exception:
        pass


def is_chad_enabled(app) -> bool:
    var = app.__dict__.get("chad_enabled_var")
    if var is None:
        return True
    try:
        return bool(var.get())
    except Exception:
        return True


def ensure_chad_enabled(app, message: str = "Chad-Anbindung ist deaktiviert."):
    if is_chad_enabled(app):
        return True
    try:
        app.chad_analysis_status_var.set(
            message
            if message != "Chad-Anbindung ist deaktiviert."
            else app.tr(
                "chad_status_disabled",
                "Chad-Anbindung ist deaktiviert.",
            )
        )
    except Exception:
        pass
    return False


def show_chad_activation_required_popup(app):
    try:
        app.chad_analysis_status_var.set(
            app.tr(
                "chad_status_activate_first",
                "Bitte vorher Chad aktivieren.",
            )
        )
    except Exception:
        pass
    try:
        messagebox.showinfo(
            app.tr("chad_popup_disabled_title", "Chad deaktiviert"),
            app.tr("chad_status_activate_first", "Bitte vorher Chad aktivieren."),
            parent=app,
        )
    except Exception:
        pass


def update_chad_controls_state(app):
    enabled = is_chad_enabled(app)

    def _set_widget_state(widget, state):
        try:
            widget.configure(state=state)
        except Exception:
            pass

    _set_widget_state(
        app.__dict__.get("openai_api_key_entry"),
        "normal" if enabled else "disabled",
    )
    _set_widget_state(
        app.__dict__.get("chad_chat_input"),
        "normal" if enabled else "disabled",
    )

    button_widgets = [
        ("btn_chad_api_paste", "normal"),
        ("btn_chad_api_apply", "normal"),
        ("btn_chad_api_save", "normal" if app.keyring_available else "disabled"),
        ("btn_chad_api_clear", "normal"),
        ("btn_chad_api_delete", "normal"),
        ("btn_chad_send", "normal"),
        ("btn_chad_take_analysis", "normal"),
        ("btn_chad_import_file", "normal"),
        ("btn_chad_online", "normal"),
        ("btn_chad_copy", "normal"),
        ("btn_chad_clear", "normal"),
        ("btn_chad_top", "normal"),
        ("btn_chad_bottom", "normal"),
        ("chad_auto_scroll_check", "normal"),
    ]
    for widget_name, enabled_state in button_widgets:
        widget = app.__dict__.get(widget_name)
        if widget is None:
            continue
        _set_widget_state(widget, enabled_state if enabled else "disabled")

    if enabled:
        try:
            app.chad_chat_status_var.set(
                app.tr("chad_status_chat_ready", "Chat bereit.")
            )
        except Exception:
            pass
    else:
        try:
            app.chad_chat_status_var.set(
                app.tr(
                    "chad_status_chat_disabled",
                    "Chad-Anbindung deaktiviert.",
                )
            )
            app.chad_online_status_var.set(
                app.tr(
                    "chad_online_status_disabled",
                    "Online-Analyse: deaktiviert",
                )
            )
            app.chad_analysis_status_var.set(
                app.tr("chad_status_disabled", "Chad-Anbindung ist deaktiviert.")
            )
        except Exception:
            pass


def build_chad_analysis_prompt(app, title: str, raw_text: str) -> str:
    service = app.ai_service or AiAnalysisService()
    return service.build_prompt(title, raw_text)


def set_chad_analysis(app, title: str, raw_text: str):
    prompt = build_chad_analysis_prompt(app, title, raw_text)
    settings = app.__dict__.get("settings", {})

    app.chad_analysis_current_prompt = prompt
    app.chad_online_result = ""
    app.chad_analysis_source_var.set(
        f"{app.tr('chad_label_source_prefix', 'Quelle')}: {title}"
    )
    app.chad_analysis_status_var.set(
        app.tr("chad_status_analysis_prepared", "Analyse vorbereitet.")
    )
    append_to_chad_output(app, title, prompt)

    try:
        if settings.get("auto_switch_to_chad", True):
            app.nb.select(app.tab_chad_analysis)
    except Exception:
        pass


def copy_chad_analysis_to_clipboard(app):
    if not ensure_chad_enabled(app):
        return
    text_widget = app.__dict__.get("chad_analysis_text")
    text = ""
    if text_widget is not None:
        try:
            text = text_widget.get("1.0", "end").strip()
        except Exception:
            text = ""
    if not text.strip():
        return

    app.clipboard_clear()
    app.clipboard_append(text)

    try:
        app.chad_analysis_status_var.set(
            app.tr(
                "chad_status_analysis_copied",
                "Analyse in Zwischenablage kopiert.",
            )
        )
    except Exception:
        pass


def clear_chad_analysis(app):
    if not ensure_chad_enabled(app):
        return
    app.chad_analysis_current_prompt = ""
    app.chad_online_result = ""
    app.chad_chat_history = []
    app.chad_pending_files = []
    app.chad_analysis_source_var.set(
        f"{app.tr('chad_label_source_prefix', 'Quelle')}: –"
    )
    app.chad_analysis_status_var.set(
        app.tr(
            "chad_status_no_analysis_prepared",
            "Noch keine Analyse vorbereitet.",
        )
    )
    app.chad_online_status_var.set(
        app.tr("chad_online_status_inactive", "Online-Analyse: inaktiv")
    )
    app.chad_chat_status_var.set(app.tr("chad_status_chat_ready", "Chat bereit."))
    widget = app.__dict__.get("chad_analysis_text")
    if widget is not None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")


def prepare_chad_analysis(
    app, title: str, raw_text: str, show_preview: bool | None = None
):
    if not ensure_chad_enabled(app):
        return
    settings = app.__dict__.get("settings", {})
    set_chad_analysis(app, title, raw_text)
    if show_preview is None:
        show_preview = bool(settings.get("chad_preview_popup", False))
    if show_preview:
        open_ai_analysis_preview(app, title, raw_text)


def open_ai_analysis_preview(app, title: str, raw_text: str):
    prompt = build_chad_analysis_prompt(app, title, raw_text)

    win = tk.Toplevel(app)
    win.title(f"Analyse mit Chad - {title}")
    win.geometry("700x500")

    text = tk.Text(win, wrap="word")
    text.insert("1.0", prompt)
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=10, pady=10)

    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill="x", padx=10, pady=(0, 10))

    def copy_to_clipboard():
        app.clipboard_clear()
        app.clipboard_append(prompt)

    ttk.Button(
        btn_frame,
        text="In Zwischenablage kopieren",
        command=copy_to_clipboard,
    ).pack(side="left")
    ttk.Button(btn_frame, text="Schließen", command=win.destroy).pack(side="right")


def send_chad_chat_message(app):
    if not ensure_chad_enabled(app):
        return "break"
    text = app.chad_chat_input.get("1.0", "end").strip()

    if not text:
        app.chad_chat_status_var.set(
            app.tr("chad_status_no_message", "Keine Nachricht eingegeben.")
        )
        return "break"

    service = app.ai_online_service
    if service is None or not service.is_available():
        app.chad_chat_status_var.set(
            app.tr("chad_status_api_key_missing", "API-Key fehlt.")
        )
        return "break"

    ok = app.confirm_chad_send(
        app.tr("chad_confirm_chat_title", "Chat mit Chad"),
        app.tr(
            "chad_confirm_chat_intro",
            "Diese Nachricht und der lokale Chatkontext werden an die OpenAI API gesendet.\nFortfahren?",
        ),
    )

    if not ok:
        app.chad_chat_status_var.set(
            app.tr("chad_status_send_cancelled", "Senden abgebrochen.")
        )
        return "break"

    app.chad_chat_input.delete("1.0", "end")
    app.chad_chat_history.append({"role": "user", "content": text})
    append_to_chad_output(app, app.tr("chad_output_you", "Du"), text)
    app.chad_chat_status_var.set(app.tr("chad_status_thinking", "Chad denkt..."))
    pending_files = list(app.chad_pending_files)

    def worker():
        success, result = service.chat(app.chad_chat_history, files=pending_files)

        def update_ui():
            if success:
                app.chad_chat_history.append({"role": "assistant", "content": result})
                app.chad_pending_files = []
                append_to_chad_output(app, app.tr("tab_chad", "Chad"), result)
                app.chad_chat_status_var.set(
                    app.tr("chad_status_reply_received", "Antwort erhalten.")
                )
            else:
                app.chad_chat_status_var.set(result)
                log_chad_error(app, "Chat", result)

        app.after(0, update_ui)

    threading.Thread(target=worker, daemon=True).start()
    return "break"


def clear_chad_chat(app):
    app.chad_chat_history = []
    app.chad_chat_status_var.set(app.tr("chad_status_chat_cleared", "Chat geleert."))


def add_current_analysis_to_chad_chat(app):
    if not ensure_chad_enabled(app):
        return
    prompt = (app.chad_analysis_current_prompt or "").strip()

    if not prompt:
        app.chad_chat_status_var.set(
            app.tr(
                "chad_status_no_current_analysis",
                "Keine aktuelle Analyse vorhanden.",
            )
        )
        return

    text = (
        app.tr(
            "chad_context_from_analysis_prefix",
            "Bitte nutze diese NetMon-Analyse als Kontext für die weitere Unterhaltung:\n\n",
        )
        + prompt
    )

    app.chad_chat_history.append({"role": "user", "content": text})
    append_to_chad_output(
        app,
        app.tr(
            "chad_output_analysis_context",
            "Analyse als Kontext übernommen",
        ),
        prompt,
    )
    app.chad_chat_status_var.set(
        app.tr(
            "chad_status_analysis_added_to_chat",
            "Aktuelle Analyse in Chat übernommen.",
        )
    )


def run_chad_online_analysis(app):
    if not ensure_chad_enabled(app):
        return
    prompt = (app.chad_analysis_current_prompt or "").strip()

    if not prompt:
        app.chad_analysis_status_var.set(
            app.tr("chad_status_no_analysis", "Keine Analyse vorhanden.")
        )
        return

    service = app.ai_online_service
    if service is None or not service.is_available():
        app.chad_analysis_status_var.set(
            app.tr("chad_status_api_key_missing", "API-Key fehlt.")
        )
        app.chad_online_status_var.set(
            app.tr("chad_online_status_inactive", "Online-Analyse: inaktiv")
        )
        return

    ok = app.confirm_chad_send(
        app.tr("chad_confirm_online_title", "Online Analyse"),
        app.tr(
            "chad_confirm_online_intro",
            "Der Text und ggf. vorgemerkte Bilder werden an die OpenAI API gesendet.\nFortfahren?",
        ),
    )
    if not ok:
        app.chad_online_status_var.set(
            app.tr(
                "chad_online_status_cancelled",
                "Online-Analyse: abgebrochen",
            )
        )
        return

    app.chad_online_status_var.set(
        app.tr("chad_online_status_running", "Analyse läuft...")
    )
    pending_files = list(app.chad_pending_files)

    def worker():
        success, result = service.analyze(prompt, files=pending_files)

        def update_ui():
            if success:
                app.chad_online_result = result
                app.chad_pending_files = []
                append_to_chad_output(
                    app,
                    app.tr("chad_output_response", "Chad Antwort"),
                    result,
                )
                app.chad_online_status_var.set(
                    app.tr(
                        "chad_online_status_done",
                        "Analyse abgeschlossen.",
                    )
                )
            else:
                app.chad_online_status_var.set(
                    app.tr(
                        "chad_online_status_error",
                        "Fehler bei Analyse.",
                    )
                )
                app.chad_analysis_status_var.set(result)
                log_chad_error(app, "Analyse", result)

        app.after(0, update_ui)

    threading.Thread(target=worker, daemon=True).start()


def extract_pdf_text_for_chad(app, path: str) -> str:
    if PyPDF2 is None:
        return app.tr(
            "chad_pdf_support_missing",
            "PDF-Unterstützung fehlt: bitte python3-pypdf2 installieren.",
        )

    try:
        parts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for idx, page in enumerate(reader.pages[:30], start=1):
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(
                        app.tr(
                            "chad_pdf_page_header",
                            "--- Seite {idx} ---\n",
                        ).format(idx=idx)
                        + text.strip()
                    )

        if not parts:
            return app.tr(
                "chad_pdf_no_text",
                "PDF gelesen, aber kein extrahierbarer Text gefunden.",
            )

        return "\n\n".join(parts)
    except Exception as e:
        return app.tr(
            "chad_pdf_read_error",
            "Fehler beim PDF-Lesen: {error}",
        ).format(error=e)


def extract_docx_text_for_chad(app, path: str) -> str:
    if docx is None:
        return app.tr(
            "chad_docx_support_missing",
            "DOCX-Unterstützung fehlt: bitte python3-docx installieren.",
        )

    try:
        document = docx.Document(path)
        parts = []

        for paragraph in document.paragraphs:
            text = (paragraph.text or "").strip()
            if text:
                parts.append(text)

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))

        if not parts:
            return app.tr(
                "chad_docx_no_text",
                "DOCX gelesen, aber kein Text gefunden.",
            )

        return "\n".join(parts)
    except Exception as e:
        return app.tr(
            "chad_docx_read_error",
            "Fehler beim DOCX-Lesen: {error}",
        ).format(error=e)


def import_file_to_chad_chat(app):
    if not ensure_chad_enabled(app):
        return
    path = filedialog.askopenfilename(
        title=app.tr(
            "chad_file_dialog_title",
            "Datei für Chad Analyse auswählen",
        ),
        filetypes=[
            (
                app.tr("chad_filetypes_supported", "Unterstützte Dateien"),
                "*.txt *.log *.md *.csv *.json *.py *.conf *.ini *.yaml *.yml *.pdf *.docx *.png *.jpg *.jpeg *.webp",
            ),
            (
                app.tr("chad_filetypes_text", "Textdateien"),
                "*.txt *.log *.md *.csv *.json *.py *.conf *.ini *.yaml *.yml",
            ),
            ("PDF", "*.pdf"),
            ("Word DOCX", "*.docx"),
            (
                app.tr("chad_filetypes_images", "Bilder"),
                "*.png *.jpg *.jpeg *.webp",
            ),
            (app.tr("chad_filetypes_all", "Alle Dateien"), "*.*"),
        ],
    )

    if not path:
        return

    ok = messagebox.askyesno(
        app.tr("chad_import_confirm_title", "Datei importieren"),
        app.tr(
            "chad_import_confirm_body",
            "Der Dateiinhalt wird lokal in den Chad-Chat übernommen.\n"
            "Er wird erst an die API gesendet, wenn du danach aktiv sendest.\n\n"
            "Fortfahren?",
        ),
        parent=app,
    )
    if not ok:
        app.chad_chat_status_var.set(
            app.tr("chad_status_file_import_cancelled", "Dateiimport abgebrochen.")
        )
        return

    try:
        max_size = 5 * 1024 * 1024
        size = os.path.getsize(path)
        filename = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()
        if size > max_size:
            messagebox.showwarning(
                app.tr("chad_file_too_large_title", "Datei zu groß"),
                app.tr(
                    "chad_file_too_large_body",
                    "Die Datei ist größer als 5 MB.\n"
                    "Bitte erst kleinere Ausschnitte verwenden.",
                ),
                parent=app,
            )
            app.chad_chat_status_var.set(
                app.tr("chad_status_file_too_large", "Datei zu groß für Import.")
            )
            return

        if size > 500_000:
            ok = messagebox.askyesno(
                app.tr("chad_large_file_title", "Große Datei"),
                app.tr(
                    "chad_large_file_body",
                    "Die Datei ist {size_mb} MB groß.\n\n"
                    "Das kann die Analyse verlangsamen.\n\n"
                    "Trotzdem laden?",
                ).format(size_mb=round(size / 1024 / 1024, 2)),
                parent=app,
            )
            if not ok:
                app.chad_chat_status_var.set(
                    app.tr(
                        "chad_status_large_file_import_cancelled",
                        "Import großer Datei abgebrochen.",
                    )
                )
                return

        if ext == ".pdf":
            content = extract_pdf_text_for_chad(app, path)
        elif ext == ".docx":
            content = extract_docx_text_for_chad(app, path)
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            item = {
                "type": "image",
                "path": path,
                "filename": filename,
                "size": size,
            }
            app.chad_pending_files.append(item)
            text = app.tr(
                "chad_imported_image_body",
                "Bild importiert: {filename}\n"
                "Pfad: {path}\n"
                "Größe: {size_mb} MB\n\n"
                "Hinweis: Das Bild wurde für die nächste Online-Analyse vorgemerkt.",
            ).format(
                filename=filename,
                path=path,
                size_mb=round(size / 1024 / 1024, 2),
            )
            append_to_chad_output(
                app,
                app.tr("chad_output_imported_image", "Importiertes Bild"),
                text,
            )
            app.chad_chat_status_var.set(
                app.tr(
                    "chad_status_image_imported", "Bild importiert: {filename}"
                ).format(filename=filename)
            )
            return
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if "\x00" in content:
                append_to_chad_output(
                    app,
                    app.tr("chad_output_import_notice", "Import-Hinweis"),
                    app.tr(
                        "chad_binary_file_notice",
                        "Die Datei {filename} wirkt wie eine Binärdatei und wurde nicht als Text übernommen.",
                    ).format(filename=filename),
                )
                app.chad_chat_status_var.set(
                    app.tr(
                        "chad_status_binary_file_skipped",
                        "Datei wirkt binär und wurde nicht importiert.",
                    )
                )
                return

        if content == app.tr(
            "chad_pdf_support_missing",
            "PDF-Unterstützung fehlt: bitte python3-pypdf2 installieren.",
        ) or content == app.tr(
            "chad_docx_support_missing",
            "DOCX-Unterstützung fehlt: bitte python3-docx installieren.",
        ):
            append_to_chad_output(
                app,
                app.tr("chad_output_import_notice", "Import-Hinweis"),
                content,
            )
            app.chad_chat_status_var.set(content)
            return

        if content.startswith(
            app.tr("chad_pdf_read_error_prefix", "Fehler beim PDF-Lesen:")
        ) or content.startswith(
            app.tr("chad_docx_read_error_prefix", "Fehler beim DOCX-Lesen:")
        ):
            append_to_chad_output(
                app,
                app.tr("chad_output_import_error", "Import-Fehler"),
                content,
            )
            app.chad_chat_status_var.set(content)
            return

        max_chars = 120_000
        if len(content) > max_chars:
            content = (
                content[:60000]
                + app.tr("chad_content_truncated_marker", "\n\n--- (gekürzt) ---\n\n")
                + content[-60000:]
            )

        text = app.tr(
            "chad_imported_file_body",
            "Datei importiert: {filename}\n"
            "Pfad: {path}\n"
            "Typ: {file_type}\n\n"
            "{content}",
        ).format(
            filename=filename,
            path=path,
            file_type=ext or app.tr("label_unknown", "unbekannt"),
            content=content,
        )

        app.chad_chat_history.append(
            {
                "role": "user",
                "content": app.tr(
                    "chad_context_from_import_prefix",
                    "Bitte nutze diese importierte Datei als Kontext:\n\n",
                )
                + text,
            }
        )
        if size > 500_000:
            append_to_chad_output(
                app,
                app.tr("chad_output_notice", "Hinweis"),
                app.tr(
                    "chad_large_file_loaded_notice",
                    "Große Datei geladen ({size_mb} MB). Inhalt ggf. gekürzt für bessere Verarbeitung.",
                ).format(size_mb=round(size / 1024 / 1024, 2)),
            )
        append_to_chad_output(
            app,
            app.tr("chad_output_imported_file", "Importierte Datei"),
            text,
        )
        app.chad_chat_status_var.set(
            app.tr("chad_status_file_imported", "Datei importiert: {filename}").format(
                filename=filename
            )
        )
    except Exception as e:
        app.chad_chat_status_var.set(
            app.tr(
                "chad_status_file_import_error",
                "Fehler beim Dateiimport: {error}",
            ).format(error=e)
        )
