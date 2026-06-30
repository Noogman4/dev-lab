"""NetMon startup entrypoint."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
import re
import shutil
import subprocess
import sys
import traceback

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

try:
    from netmon.core.crash import (
        CRASH_LOG_PATH,
        _append_crash_dump,
        _install_global_crash_hooks,
    )
    from netmon.core.diagnostics import current_os_label, write_diagnostic_report
    from netmon.core.lock import (
        acquire_netmon_instance_lock,
        format_netmon_instance_lock_info,
        release_netmon_instance_lock,
    )
    from netmon.core.state import get_netmon_documents_dir
    from netmon.core.support_bundle import create_support_package
except ModuleNotFoundError:
    from core.crash import (
        CRASH_LOG_PATH,
        _append_crash_dump,
        _install_global_crash_hooks,
    )
    from core.diagnostics import current_os_label, write_diagnostic_report
    from core.lock import (
        acquire_netmon_instance_lock,
        format_netmon_instance_lock_info,
        release_netmon_instance_lock,
    )
    from core.state import get_netmon_documents_dir
    from core.support_bundle import create_support_package


def get_startup_error_log_path():
    diagnostics_dir = os.path.join(get_netmon_documents_dir(), "diagnostics")
    os.makedirs(diagnostics_dir, exist_ok=True)
    return os.path.join(diagnostics_dir, "startup_error.log")


def _write_startup_error_log(
    title: str, detail: str = "", exc: BaseException | None = None
):
    log_path = get_startup_error_log_path()
    diagnostic_path = ""
    try:
        diagnostic_path = write_diagnostic_report(
            kind="startup-error",
            title=title,
            detail=detail,
            exc=exc,
            context={
                "stage": "startup",
                "display": os.environ.get("DISPLAY", ""),
            },
        )
    except Exception:
        diagnostic_path = ""

    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 80 + "\n")
            fh.write(f"{title}\n\n")
            fh.write(f"argv={sys.argv!r}\n")
            fh.write(f"cwd={os.getcwd()}\n")
            fh.write(f"os={current_os_label()}\n")
            fh.write(f"DISPLAY={os.environ.get('DISPLAY', '')!r}\n\n")
            if diagnostic_path:
                fh.write(f"diagnostic_report={diagnostic_path}\n\n")
            if detail:
                fh.write(detail.rstrip() + "\n\n")
            if exc is not None:
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=fh)
            fh.write("=" * 80 + "\n")
    except Exception:
        pass
    return log_path, diagnostic_path


def _startup_support_form_metadata(
    *,
    detail: str = "",
    contact_name: str = "",
    contact_email: str = "",
    last_step: str = "",
    repro_status: str = "",
    description: str = "",
):
    return {
        "startup_report": {
            "contact_name": str(contact_name or "").strip(),
            "contact_email": str(contact_email or "").strip(),
            "last_step": str(last_step or "").strip(),
            "repro_status": str(repro_status or "").strip(),
            "description": str(description or "").strip(),
            "bootstrap_detail": str(detail or "").strip(),
        }
    }


def _create_startup_support_package(*, detail: str = "", form_data: dict | None = None):
    metadata = {"stage": "startup"}
    if detail:
        metadata["startup_detail"] = str(detail).strip()
    if isinstance(form_data, dict):
        metadata.update(_startup_support_form_metadata(detail=detail, **form_data))
    return create_support_package(metadata=metadata)


def _open_support_dir_with_xdg_open() -> bool:
    support_dir = os.path.join(get_netmon_documents_dir(), "support")
    try:
        os.makedirs(support_dir, exist_ok=True)
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["xdg-open", support_dir],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


def _show_startup_support_dialog(title: str, detail: str = "", log_path: str = ""):
    try:
        import tkinter as _tk
        from tkinter import messagebox as _messagebox
        from tkinter import ttk as _ttk
    except Exception:
        return ""

    result = {"package_path": ""}
    root = None
    try:
        root = _tk.Tk()
        root.withdraw()
        win = _tk.Toplevel(root)
        win.title("NetMon Startfehler")
        win.geometry("720x560")
        win.minsize(620, 500)
        try:
            win.update_idletasks()
            width, height, pos_x, pos_y = _center_geometry_on_primary_monitor(
                720,
                560,
                fallback_screen_width=win.winfo_screenwidth(),
                fallback_screen_height=win.winfo_screenheight(),
                minimum_margin=20,
            )
            win.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        except Exception:
            pass

        outer = _ttk.Frame(win, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(6, weight=1)

        _ttk.Label(
            outer,
            text=title,
            font=("TkDefaultFont", 11, "bold"),
            justify="left",
            wraplength=660,
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        _ttk.Label(
            outer,
            text=(
                "NetMon konnte nicht vollständig starten. "
                "Hier kannst du eine kurze Fehlerbeschreibung ergänzen und direkt "
                "ein Supportpaket vorbereiten."
            ),
            justify="left",
            wraplength=660,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 12))

        _ttk.Label(outer, text="Name / Kürzel").grid(row=2, column=0, sticky="w")
        contact_name_var = _tk.StringVar(
            value="Platzhalter: Name oder Kürzel (optional)"
        )
        _ttk.Entry(outer, textvariable=contact_name_var).grid(
            row=2, column=1, sticky="ew", padx=(10, 0), pady=(0, 6)
        )

        _ttk.Label(outer, text="E-Mail").grid(row=3, column=0, sticky="w")
        contact_email_var = _tk.StringVar(
            value="Platzhalter: E-Mail-Adresse (optional)"
        )
        _ttk.Entry(outer, textvariable=contact_email_var).grid(
            row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 6)
        )

        _ttk.Label(outer, text="Letzter Schritt").grid(row=4, column=0, sticky="w")
        last_step_var = _tk.StringVar(
            value="Platzhalter: letzter Schritt vor dem Fehler"
        )
        _ttk.Entry(outer, textvariable=last_step_var).grid(
            row=4, column=1, sticky="ew", padx=(10, 0), pady=(0, 6)
        )

        _ttk.Label(outer, text="Reproduzierbarkeit").grid(row=5, column=0, sticky="w")
        repro_var = _tk.StringVar(
            value="Platzhalter: z. B. immer / manchmal / noch unklar"
        )
        _ttk.Entry(outer, textvariable=repro_var).grid(
            row=5, column=1, sticky="ew", padx=(10, 0), pady=(0, 6)
        )

        _ttk.Label(outer, text="Fehlerbeschreibung").grid(row=6, column=0, sticky="nw")
        details_widget = _tk.Text(outer, height=8, wrap="word")
        details_widget.grid(row=6, column=1, sticky="nsew", padx=(10, 0), pady=(0, 6))
        details_widget.insert(
            "1.0",
            "Platzhalter: kurze Fehlerbeschreibung, Beobachtungen, gewünschtes Verhalten",
        )

        info_box = _ttk.LabelFrame(outer, text="Diagnose", padding=8)
        info_box.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        _ttk.Label(
            info_box,
            text=f"Start-Log: {log_path or '-'}",
            justify="left",
            wraplength=640,
        ).pack(anchor="w")
        _ttk.Label(
            info_box,
            text=f"Diagnoseordner: {os.path.join(get_netmon_documents_dir(), 'diagnostics')}",
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(4, 0))
        _ttk.Label(
            info_box,
            text=(
                "Hinweis: Das Supportpaket kannst du später an den Support "
                "weitergeben. Falls ein eigener Mailer genutzt wird, die ZIP-Datei "
                "einfach manuell anhängen."
            ),
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(8, 0))

        def _clean(text, placeholder):
            text = str(text or "").strip()
            return "" if not text or text == placeholder else text

        def _create_package():
            try:
                package_path = _create_startup_support_package(
                    detail=detail,
                    form_data={
                        "contact_name": _clean(
                            contact_name_var.get(),
                            "Platzhalter: Name oder Kürzel (optional)",
                        ),
                        "contact_email": _clean(
                            contact_email_var.get(),
                            "Platzhalter: E-Mail-Adresse (optional)",
                        ),
                        "last_step": _clean(
                            last_step_var.get(),
                            "Platzhalter: letzter Schritt vor dem Fehler",
                        ),
                        "repro_status": _clean(
                            repro_var.get(),
                            "Platzhalter: z. B. immer / manchmal / noch unklar",
                        ),
                        "description": _clean(
                            details_widget.get("1.0", "end-1c"),
                            (
                                "Platzhalter: kurze Fehlerbeschreibung, Beobachtungen, "
                                "gewünschtes Verhalten"
                            ),
                        ),
                    },
                )
            except Exception as exc:
                _messagebox.showerror(
                    "Supportpaket",
                    f"Supportpaket konnte nicht erzeugt werden:\n{exc}",
                    parent=win,
                )
                return
            result["package_path"] = package_path
            _messagebox.showinfo(
                "Supportpaket",
                f"Supportpaket erstellt:\n{package_path}",
                parent=win,
            )

        button_row = _ttk.Frame(outer)
        button_row.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        _ttk.Button(
            button_row,
            text="Supportpaket erzeugen",
            command=_create_package,
        ).pack(side="left")
        _ttk.Button(
            button_row,
            text="Supportordner öffnen",
            command=_open_support_dir_with_xdg_open,
        ).pack(side="left", padx=(8, 0))
        _ttk.Button(
            button_row,
            text="Schließen",
            command=win.destroy,
        ).pack(side="right")

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        try:
            win.transient(root)
            win.grab_set()
            win.focus_force()
        except Exception:
            pass
        root.wait_window(win)
    except Exception:
        return ""
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
    return result["package_path"]


def _startup_splash_candidates():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return [
        os.path.join(repo_root, "tools", "netmon_roots_splash.png"),
        os.path.join(repo_root, "tools", "netmon_roots_startup.png"),
        os.path.join(repo_root, "tools", "netmon.png"),
    ]


def _startup_splash_path():
    for candidate in _startup_splash_candidates():
        if os.path.isfile(candidate):
            return candidate
    return ""


XRANDR_CONNECTED_MONITOR_RE = re.compile(
    r"^(?P<name>\S+)\s+connected(?:\s+(?P<primary>primary))?\s+"
    r"(?P<width>\d+)x(?P<height>\d+)\+(?P<x>-?\d+)\+(?P<y>-?\d+)\b"
)


def _parse_xrandr_monitor_bounds(line: str):
    text = str(line or "").strip()
    if not text:
        return None
    match = XRANDR_CONNECTED_MONITOR_RE.match(text)
    if match is None:
        return None
    try:
        x = int(match.group("x"))
        y = int(match.group("y"))
        width = int(match.group("width"))
        height = int(match.group("height"))
    except Exception:
        return None
    if width <= 0 or height <= 0:
        return None
    return {
        "name": match.group("name"),
        "primary": bool(match.group("primary")),
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def _detect_primary_monitor_bounds():
    display = str(os.environ.get("DISPLAY", "") or "").strip()
    if not display or shutil.which("xrandr") is None:
        return None
    try:
        result = subprocess.run(
            ["xrandr", "--query"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
            check=False,
        )
    except Exception:
        return None

    monitors = []
    for raw_line in str(result.stdout or "").splitlines():
        parsed = _parse_xrandr_monitor_bounds(raw_line)
        if parsed is not None:
            monitors.append(parsed)
    if not monitors:
        return None

    primary = next((item for item in monitors if item["primary"]), None)
    selected = primary or monitors[0]
    return (
        int(selected["x"]),
        int(selected["y"]),
        int(selected["width"]),
        int(selected["height"]),
    )


def _center_geometry_on_primary_monitor(
    window_width: int,
    window_height: int,
    *,
    fallback_screen_width: int,
    fallback_screen_height: int,
    minimum_margin: int = 0,
):
    bounds = _detect_primary_monitor_bounds()
    if bounds is not None:
        screen_x, screen_y, screen_width, screen_height = bounds
    else:
        screen_x = 0
        screen_y = 0
        screen_width = max(1, int(fallback_screen_width or 1))
        screen_height = max(1, int(fallback_screen_height or 1))
    width = max(1, int(window_width or 1))
    height = max(1, int(window_height or 1))
    margin = max(0, int(minimum_margin or 0))
    pos_x = max(screen_x + margin, int(screen_x + ((screen_width - width) / 2)))
    pos_y = max(screen_y + margin, int(screen_y + ((screen_height - height) / 2)))
    return width, height, pos_x, pos_y


def _show_startup_splash(duration_ms: int = 5000):
    splash_path = _startup_splash_path()
    if not splash_path:
        return

    try:
        import tkinter as _tk
    except Exception:
        return

    root = None
    try:
        root = _tk.Tk()
        root.overrideredirect(True)
        root.configure(bg="#05070d")
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass

        scaled_photo = None
        if Image is not None and ImageTk is not None:
            try:
                with Image.open(splash_path) as img:
                    if img.mode not in {"RGB", "RGBA"}:
                        img = img.convert("RGBA")
                    target_size = (
                        max(1, int(img.width * 0.7)),
                        max(1, int(img.height * 0.7)),
                    )
                    if hasattr(Image, "Resampling"):
                        resample = Image.Resampling.LANCZOS
                    else:
                        resample = Image.LANCZOS
                    resized = img.resize(target_size, resample)
                    scaled_photo = ImageTk.PhotoImage(resized)
            except Exception:
                scaled_photo = None

        if scaled_photo is None:
            photo = _tk.PhotoImage(file=splash_path)
            scaled_photo = photo
            try:
                scaled_photo = _tk.PhotoImage()
                scaled_photo.tk.call(
                    str(scaled_photo),
                    "copy",
                    str(photo),
                    "-zoom",
                    7,
                    7,
                    "-subsample",
                    10,
                    10,
                )
            except Exception:
                scaled_photo = photo
        root._startup_splash_photo = scaled_photo

        label = _tk.Label(
            root,
            image=scaled_photo,
            bg="#05070d",
            bd=0,
            highlightthickness=0,
        )
        label.pack()

        root.update_idletasks()
        width = max(1, label.winfo_reqwidth())
        height = max(1, label.winfo_reqheight())
        width, height, pos_x, pos_y = _center_geometry_on_primary_monitor(
            width,
            height,
            fallback_screen_width=root.winfo_screenwidth(),
            fallback_screen_height=root.winfo_screenheight(),
        )
        root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        root.after(max(250, int(duration_ms)), root.destroy)
        root.mainloop()
    except Exception:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def _smoke_noop(*_args, **_kwargs):
    return None


def _cancel_pending_after_callbacks(app):
    try:
        pending = tuple(app.tk.call("after", "info"))
    except Exception:
        pending = ()
    for callback_id in pending:
        try:
            app.after_cancel(callback_id)
        except Exception:
            pass


@contextmanager
def _temporary_app_smoke_patches(app_cls):
    method_names = (
        "setup_sudo_auth",
        "refresh_wg_profiles",
        "update_startup_vpn_profile_options",
        "refresh_radio_ui",
        "update_primary_vpn_form_controls",
        "sync_primary_vpn_form_selection",
        "preflight_dependencies",
        "update_ipv6_controls_state",
        "refresh",
        "debug_nm_state",
        "apply_startup_settings",
        "startup_guard_startup_check",
        "attach_all_chad_context_menus",
        "attach_all_selection_copy_shortcuts",
        "attach_all_local_mousewheel_bindings",
        "scan_hdds_async",
        "hdd_refresh_async",
        "_activate_startup_log_view",
        "_poll_radio_attach_request",
        "check_keyring_availability",
        "load_ai_config",
        "prepare_download_scan_workspace",
        "refresh_roots_baseline_guard_status",
        "setup_all_tab_tooltips",
    )
    originals = {}
    for name in method_names:
        if hasattr(app_cls, name):
            originals[name] = getattr(app_cls, name)
            setattr(app_cls, name, _smoke_noop)
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(app_cls, name, original)


def run_headless_smoke(app_cls, *, theme_name=None):
    app = None
    with _temporary_app_smoke_patches(app_cls):
        try:
            app = app_cls(start_theme=theme_name)
            app.update_idletasks()
            app.update()
            print("NetMon GUI smoke test ok")
            return 0
        finally:
            if app is not None:
                _cancel_pending_after_callbacks(app)
                try:
                    app.quit()
                except Exception:
                    pass
                try:
                    app.destroy()
                except Exception:
                    pass
                try:
                    app.update()
                except Exception:
                    pass


def main(argv=None):
    try:
        from netmon.app import App, TK_IMPORT_ERROR, TkError, run_headless_snapshot, tk
    except ModuleNotFoundError:
        from app import App, TK_IMPORT_ERROR, TkError, run_headless_snapshot, tk

    parser = argparse.ArgumentParser(description="NetMon GUI / headless launcher")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI and print a compact status snapshot.",
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light", "beige", "pop"],
        default=None,
        help="Start theme for the integrated NetMon UI.",
    )
    parser.add_argument(
        "--headless-smoke",
        action="store_true",
        help="Create the NetMon GUI once, skip heavy startup actions, and exit.",
    )
    args, unknown_args = parser.parse_known_args(argv)

    print(f"[NetMon] startup_error.log: {get_startup_error_log_path()}")
    if unknown_args:
        print(
            f"[NetMon] Ignoring extra startup args: {unknown_args!r}",
            file=sys.stderr,
        )

    if args.headless:
        run_headless_snapshot()
        return 0

    if tk is None:
        log_path = _write_startup_error_log(
            "NetMon startup failure: tkinter missing",
            detail=f"TK_IMPORT_ERROR={TK_IMPORT_ERROR}",
        )
        if isinstance(log_path, tuple):
            log_path, diagnostic_path = log_path
        else:
            diagnostic_path = ""
        print(
            "Fehler: tkinter ist nicht installiert. GUI kann nicht gestartet werden.\n"
            "Lösung (Debian/Ubuntu): sudo apt install -y python3-tk\n"
            "Alternativ: mit --headless starten.\n"
            f"Details: {TK_IMPORT_ERROR}\n"
            f"Start-Log: {log_path}\n"
            + (f"Diagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            file=sys.stderr,
        )
        return 2

    display = os.environ.get("DISPLAY", "").strip()
    if not display:
        log_path = _write_startup_error_log(
            "NetMon startup failure: no DISPLAY",
            detail="Kein DISPLAY gesetzt.",
        )
        if isinstance(log_path, tuple):
            log_path, diagnostic_path = log_path
        else:
            diagnostic_path = ""
        print(
            "Fehler: Kein DISPLAY gesetzt. GUI kann nicht gestartet werden.\n"
            "Tipp: Mit --headless starten oder X11/Wayland-Forwarding aktivieren.\n"
            f"Start-Log: {log_path}\n"
            + (f"Diagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            file=sys.stderr,
        )
        return 2

    _install_global_crash_hooks()

    if args.headless_smoke:
        return run_headless_smoke(App, theme_name=args.theme)

    lock_ok, lock_path = acquire_netmon_instance_lock()
    if not lock_ok:
        lock_detail = format_netmon_instance_lock_info(lock_path)
        startup_log = _write_startup_error_log(
            "NetMon startup failure: instance lock",
            detail=lock_detail,
        )
        if isinstance(startup_log, tuple):
            startup_log, diagnostic_path = startup_log
        else:
            diagnostic_path = ""
        print(
            "Fehler: NetMon läuft bereits. Es wird nur eine Instanz gleichzeitig erlaubt.\n"
            f"{lock_detail}\n"
            "Tipp: Prüfe, ob noch eine NetMon-GUI läuft oder ein alter Prozess hängt.\n"
            f"Start-Log: {startup_log}\n"
            + (f"Diagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            file=sys.stderr,
        )
        return 1

    try:
        _show_startup_splash(duration_ms=5000)
        app = App(start_theme=args.theme)
        app.mainloop()
        return 0
    except TkError as e:
        _append_crash_dump("main.tk", type(e), e, e.__traceback__)
        log_path = _write_startup_error_log(
            "NetMon startup failure: TkError",
            detail=f"Crash-Dump: {CRASH_LOG_PATH}",
            exc=e,
        )
        if isinstance(log_path, tuple):
            log_path, diagnostic_path = log_path
        else:
            diagnostic_path = ""
        print(
            "Fehler: Tkinter konnte keine GUI-Verbindung aufbauen "
            f"(DISPLAY={display!r}).\n"
            "Hinweis: In VS Code Remote/Container fehlt oft X11-Auth.\n"
            "Optionen: 1) --headless nutzen 2) xvfb-run verwenden 3) X11-Forwarding korrekt einrichten.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}\n"
            f"Start-Log: {log_path}\n"
            + (f"Diagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        _append_crash_dump("main.exception", type(e), e, e.__traceback__)
        log_path = _write_startup_error_log(
            "NetMon startup failure: exception",
            detail=f"Crash-Dump: {CRASH_LOG_PATH}",
            exc=e,
        )
        if isinstance(log_path, tuple):
            log_path, diagnostic_path = log_path
        else:
            diagnostic_path = ""
        print(
            "Fehler: NetMon ist beim Start abgestürzt.\n"
            f"Details: {e}\n"
            f"Crash-Dump: {CRASH_LOG_PATH}\n"
            f"Start-Log: {log_path}\n"
            + (f"Diagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            file=sys.stderr,
        )
        return 1
    finally:
        release_netmon_instance_lock()


def _report_bootstrap_failure(exc: BaseException):
    log_path = _write_startup_error_log(
        "NetMon startup bootstrap failure",
        exc=exc,
    )
    if isinstance(log_path, tuple):
        log_path, diagnostic_path = log_path
    else:
        diagnostic_path = ""

    try:
        import tkinter as _tk
        from tkinter import messagebox as _messagebox

        root = _tk.Tk()
        root.withdraw()
        _messagebox.showerror(
            "NetMon Startfehler",
            "NetMon konnte nicht gestartet werden.\n\n"
            f"Fehler: {exc}\n\n"
            f"Details: {log_path}"
            + (f"\nDiagnose-Report: {diagnostic_path}" if diagnostic_path else ""),
            parent=root,
        )
        _show_startup_support_dialog(
            "NetMon konnte nicht gestartet werden.",
            detail="Fehler beim frühen Start vor App-Initialisierung.",
            log_path=log_path,
        )
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        _report_bootstrap_failure(exc)
        raise
