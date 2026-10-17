"""Packet capture controller helpers for NetMon."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime
from tkinter import filedialog

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd

try:
    from netmon.core.utils import human_size, call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import human_size, call_in_ui_thread


def _app_value(app, name: str, default=None):
    if app is None:
        return default
    data = getattr(app, "__dict__", None)
    if isinstance(data, dict) and name in data:
        return data.get(name, default)
    try:
        return object.__getattribute__(app, name)
    except AttributeError:
        return default


def _app_var_get(app, name: str, default=""):
    var = _app_value(app, name)
    if var is None:
        return default
    try:
        value = var.get()
    except Exception:
        value = default
    return value if value is not None else default


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _packet_capture_dep_enabled(app, name: str) -> bool:
    return bool((_app_value(app, "dep_status", {}) or {}).get(name))


def _packet_capture_interfaces_from_tshark_output(
    output: str,
) -> tuple[list[str], list[str]]:
    interfaces = []
    details = []
    for line in str(output or "").splitlines():
        raw = line.strip()
        if not raw:
            continue
        entry = raw.split(".", 1)[-1].strip() if "." in raw else raw
        name = entry.split(" ", 1)[0].strip()
        if name:
            interfaces.append(name)
            details.append(raw)
    return interfaces, details


def _packet_capture_interfaces_from_ip_output(output: str) -> list[str]:
    interfaces = []
    for line in str(output or "").splitlines():
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        name = parts[1].strip().split("@", 1)[0]
        if name:
            interfaces.append(name)
    return interfaces


def _packet_capture_unique_interfaces(interfaces) -> list[str]:
    unique = []
    seen = set()
    for name in interfaces:
        value = str(name or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _packet_capture_text_widget(app):
    return _app_value(app, "packet_capture_text")


def _packet_capture_file_path(app) -> str:
    return str(
        _app_value(app, "packet_capture_output_path")
        or _app_var_get(app, "packet_capture_file_var", "")
        or ""
    ).strip()


def _packet_capture_existing_file_path(app) -> str:
    file_path = _packet_capture_file_path(app)
    if file_path and os.path.isfile(file_path):
        return file_path
    return ""


def _packet_capture_has_existing_file(app) -> bool:
    return bool(_packet_capture_existing_file_path(app))


def _packet_capture_open_target_path(app) -> str:
    file_path = _packet_capture_file_path(app)
    if not file_path:
        return ""
    return file_path if os.path.exists(file_path) else os.path.dirname(file_path)


def _packet_capture_wireshark_launcher(app) -> dict:
    return dict(
        (_app_value(app, "dep_status", {}) or {}).get("wireshark_launcher") or {}
    )


def _packet_capture_wireshark_command(
    launcher: dict,
    file_path: str,
    *,
    has_cmd_fn=has_cmd,
):
    target = str((launcher or {}).get("target") or "").strip()
    kind = str((launcher or {}).get("kind") or "").strip()
    if kind == "binary":
        return [target, file_path]
    if kind == "flatpak":
        return ["flatpak", "run", target, file_path]
    if kind == "desktop":
        if has_cmd_fn("gtk-launch"):
            return ["gtk-launch", target]
        raise RuntimeError("gtk-launch ist nicht verfügbar.")
    if kind == "desktop_file":
        if has_cmd_fn("xdg-open"):
            return ["xdg-open", target]
        raise RuntimeError("xdg-open ist nicht verfügbar.")
    raise RuntimeError("Kein Wireshark-Launcher gefunden.")


def _packet_capture_open_location_command(target: str, *, has_cmd_fn=has_cmd):
    if has_cmd_fn("xdg-open"):
        return ["xdg-open", target]
    raise RuntimeError("xdg-open ist nicht verfügbar.")


def _packet_capture_filter(app) -> str:
    return str(_app_var_get(app, "packet_capture_filter_var", "") or "").strip()


def _packet_capture_start_command(app, interface: str, output_file: str):
    capture_filter = _packet_capture_filter(app)
    if _packet_capture_dep_enabled(app, "tshark"):
        cmd = ["tshark", "-i", interface]
        if capture_filter:
            cmd.extend(["-f", capture_filter])
        cmd.extend(["-w", output_file])
        return cmd, "tshark"
    if _packet_capture_dep_enabled(app, "dumpcap"):
        cmd = ["dumpcap", "-i", interface]
        if capture_filter:
            cmd.extend(["-f", capture_filter])
        cmd.extend(["-w", output_file])
        return cmd, "dumpcap"
    return None, ""


def _packet_capture_capinfos_summary(output: str, default_size: str = "-") -> dict:
    packets = "-"
    size_text = str(default_size or "-")
    for line in str(output or "").splitlines():
        lower = line.lower()
        if "number of packets" in lower:
            packets = _packet_capture_summary_value(line, "-")
        if lower.startswith("file size"):
            size_text = _packet_capture_summary_value(line, size_text)
    return {"packets": packets, "size_text": size_text}


def _packet_capture_summary_value(line: str, default: str = "-") -> str:
    return str(line or "").split(":", 1)[-1].strip() or str(default or "-")


def _packet_capture_completion_status(cancel_requested: bool, return_code: int) -> str:
    if cancel_requested:
        return "gestoppt"
    if return_code == 0:
        return "abgeschlossen"
    return f"Fehler ({return_code})"


def _packet_capture_size_text(file_path: str) -> str:
    return human_size(os.path.getsize(file_path))


def _packet_capture_file_info_header() -> str:
    return "=== Capture-Datei Info ==="


def _packet_capture_file_info_body_lines(file_path: str, size_text: str) -> list[str]:
    return [
        f"Datei: {file_path}",
        f"Größe: {size_text}",
    ]


def _packet_capture_file_info_lines(file_path: str, size_text: str) -> list[str]:
    return [_packet_capture_file_info_header()] + _packet_capture_file_info_body_lines(
        file_path,
        size_text,
    )


def _packet_capture_file_info_text(file_path: str, size_text: str) -> str:
    return "\n".join(_packet_capture_file_info_lines(file_path, size_text))


def _packet_capture_file_info_missing_message(file_path: str) -> str:
    path = str(file_path or "").strip()
    if not path:
        return "Noch keine Capture-Datei ausgewählt."
    return f"Capture-Datei nicht gefunden: {path}"


def _packet_capture_open_location_missing_message(file_path: str, target: str) -> str:
    if not str(file_path or "").strip():
        return "Noch keine Capture-Datei vorhanden."
    if not str(target or "").strip():
        return "Kein gültiger Pfad für Capture-Datei vorhanden."
    return ""


def _packet_capture_wireshark_missing_message(target: str, file_path: str) -> str:
    if not str(target or "").strip():
        return "Wireshark ist nicht verfügbar. Installationshinweis: sudo apt install wireshark"
    if not str(file_path or "").strip():
        return "Keine gültige Capture-Datei zum Öffnen gefunden."
    return ""


def _packet_capture_stop_request_message(has_running_capture: bool) -> str:
    if not has_running_capture:
        return "Es läuft aktuell kein Capture."
    return "Capture-Stopp angefordert."


def _packet_capture_open_success_message(label: str, target: str) -> str:
    return f"{str(label or '').strip()} geöffnet: {target}"


def _packet_capture_open_location_result_message(
    target: str, error_message: str = ""
) -> str:
    if str(error_message or "").strip():
        return f"Capture-Pfad konnte nicht geöffnet werden: {error_message}"
    return _packet_capture_open_success_message("Capture-Pfad", target)


def _packet_capture_wireshark_result_message(
    file_path: str, error_message: str = ""
) -> str:
    if str(error_message or "").strip():
        return f"Wireshark konnte nicht geöffnet werden: {error_message}"
    return _packet_capture_open_success_message("Wireshark", file_path)


def _packet_capture_start_failure_messages(message: str) -> tuple[str, str]:
    error_text = str(message or "").strip()
    return (
        f"Capture konnte nicht gestartet werden: {error_text}",
        f"Packet Capture fehlgeschlagen: {error_text}",
    )


def _packet_capture_stop_failure_messages(message: str) -> tuple[str, str]:
    error_text = str(message or "").strip()
    return (
        f"Capture-Stopp fehlgeschlagen: {error_text}",
        f"Packet Capture-Stopp fehlgeschlagen: {error_text}",
    )


def _packet_capture_state_log_message(state: str, interface: str) -> str:
    return f"Packet Capture {state} ({interface})."


def _packet_capture_missing_tool_message() -> str:
    return "Packet Capture ist nicht verfügbar: tshark oder dumpcap fehlt."


def _packet_capture_start_guard_message(is_running: bool, interface: str) -> str:
    if is_running:
        return "Ein Capture läuft bereits."
    if not str(interface or "").strip():
        return "Bitte zuerst ein Capture-Interface auswählen."
    return ""


def _packet_capture_file_info_error_message(message: str) -> str:
    return f"Datei-Info konnte nicht gelesen werden: {str(message or '').strip()}"


def _packet_capture_completion_failure_messages(
    interface: str, return_code: int
) -> tuple[str, str]:
    return (
        "Hinweis: Capture wurde mit Fehler beendet. Fehlende Rechte für tshark/dumpcap sind häufig die Ursache.",
        f"Packet Capture fehlgeschlagen ({interface}, rc={return_code}).",
    )


def _packet_capture_wireshark_failure_log_message(message: str) -> str:
    return f"Wireshark-Start fehlgeschlagen: {str(message or '').strip()}"


def _packet_capture_open_location_failure_log_message(message: str) -> str:
    return f"Capture-Datei öffnen fehlgeschlagen: {str(message or '').strip()}"


def _packet_capture_missing_tool_log_message() -> str:
    return "Packet Capture fehlgeschlagen: tshark/dumpcap fehlt."


def _packet_capture_interfaces_ready_message(interfaces) -> str:
    return "Verfügbare Interfaces: " + ", ".join(list(interfaces or []))


def _packet_capture_no_interfaces_message() -> str:
    return "Keine Capture-Interfaces gefunden. Prüfe tshark, dumpcap oder iproute2."


def _packet_capture_dumpcap_permission_message() -> str:
    return "tshark ist vorhanden, aber dumpcap hat keine ausreichenden Berechtigungen."


def _packet_capture_permission_failure_message() -> str:
    return (
        "Capture fehlgeschlagen: keine Berechtigung für dieses Interface.\n"
        "Nutze in NetMon den Button 'Capture-Rechte reparieren' und melde dich danach einmal neu an."
    )


def _packet_capture_looks_like_permission_issue(app, text: str) -> bool:
    detector = getattr(app, "_looks_like_dumpcap_permission_issue", None)
    if callable(detector) and detector(text):
        return True
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "you do not have permission to capture on device",
        "operation not permitted",
        "permission denied",
        "cap_net_raw",
        "cap_net_admin",
    ]
    return any(marker in lowered for marker in markers)


def _packet_capture_capinfos_text(output: str) -> str:
    return _packet_capture_file_info_header() + "\n" + str(output or "").strip()


def _packet_capture_start_text(
    capture_tool: str,
    interface: str,
    output_file: str,
    capture_filter: str,
) -> str:
    return "\n".join(
        _packet_capture_start_lines(
            capture_tool,
            interface,
            output_file,
            capture_filter,
        )
    )


def _packet_capture_start_body_lines(
    capture_tool: str,
    interface: str,
    output_file: str,
    capture_filter: str,
) -> list[str]:
    return [
        f"Tool: {capture_tool}",
        f"Interface: {interface}",
        f"Datei: {output_file}",
        f"Filter: {capture_filter or '-'}",
    ]


def _packet_capture_start_lines(
    capture_tool: str,
    interface: str,
    output_file: str,
    capture_filter: str,
) -> list[str]:
    return ["=== Packet Capture gestartet ==="] + _packet_capture_start_body_lines(
        capture_tool,
        interface,
        output_file,
        capture_filter,
    )


def _packet_capture_initial_file_name(current_path: str, generated_path: str) -> str:
    return os.path.basename(str(current_path or generated_path or "").strip())


def _packet_capture_ready(app) -> bool:
    return _packet_capture_dep_enabled(app, "tshark") or _packet_capture_dep_enabled(
        app, "dumpcap"
    )


def _packet_capture_needs_separator(widget, replace: bool) -> bool:
    return bool(widget is not None and not replace and widget.index("end-1c") != "1.0")


def _packet_capture_output_segment(text: str) -> str:
    return str(text or "").rstrip() + "\n"


def _packet_capture_button_states(running: bool, ready: bool) -> dict:
    return {
        "start": "disabled" if running or not ready else "normal",
        "stop": "normal" if running and ready else "disabled",
    }


def _packet_capture_clear_widget(widget) -> bool:
    if widget is None:
        return False
    widget.delete("1.0", "end")
    return True


def _packet_capture_apply_output(
    widget, text: str = "", *, replace: bool = False
) -> bool:
    if widget is None:
        return False
    if replace:
        _packet_capture_clear_widget(widget)
    if text:
        if _packet_capture_needs_separator(widget, replace):
            widget.insert("end", "\n")
        widget.insert("end", _packet_capture_output_segment(text))
    return True


def _packet_capture_apply_button_states(app, states: dict) -> None:
    start_button = _app_value(app, "btn_packet_capture_start")
    if start_button is not None:
        start_button.configure(state=states.get("start", "disabled"))
    stop_button = _app_value(app, "btn_packet_capture_stop")
    if stop_button is not None:
        stop_button.configure(state=states.get("stop", "disabled"))


def packet_capture_set_running_state(app, running):
    packet_capture_ready = _packet_capture_ready(app)
    states = _packet_capture_button_states(running, packet_capture_ready)
    _packet_capture_apply_button_states(app, states)
    light = _app_value(app, "l_capture")
    set_light = _app_value(app, "set_light")
    if light is not None and callable(set_light):
        try:
            set_light(light, "green" if running else "red")
        except Exception:
            pass


def append_packet_capture_output(app, text: str, replace: bool = False):
    widget = _packet_capture_text_widget(app)
    if widget is None:
        return
    widget.configure(state="normal")
    _packet_capture_apply_output(widget, text, replace=replace)
    widget.see("end")
    widget.configure(state="disabled")


def clear_packet_capture_output(app):
    widget = _packet_capture_text_widget(app)
    if widget is None:
        return
    widget.configure(state="normal")
    _packet_capture_apply_output(widget, replace=True)
    widget.configure(state="disabled")


def packet_capture_generate_default_path(app):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(app.packet_capture_dir, f"capture_{stamp}.pcapng")


def choose_packet_capture_file(app):
    initial_dir = app.packet_capture_dir
    current_path = str(_app_var_get(app, "packet_capture_file_var", "") or "").strip()
    generated_path = packet_capture_generate_default_path(app)
    initial_file = _packet_capture_initial_file_name(current_path, generated_path)
    chosen = filedialog.asksaveasfilename(
        parent=app,
        title=app.tr("packet_capture_file_dialog_title", "Choose capture file"),
        initialdir=initial_dir,
        initialfile=initial_file,
        defaultextension=".pcapng",
        filetypes=[
            ("Packet Capture", "*.pcapng *.pcap"),
            ("All files", "*.*"),
        ],
    )
    if chosen:
        _app_var_set(app, "packet_capture_file_var", chosen)
        app.packet_capture_output_path = chosen
        append_packet_capture_output(app, f"Capture file set: {chosen}")


def refresh_packet_capture_interfaces(app):
    app._select_security_tab(app.tab_packet_capture)
    interfaces = []
    details = []
    if _packet_capture_dep_enabled(app, "tshark"):
        rc, out = run_cmd(["tshark", "-D"], timeout=8)
        if rc == 0:
            parsed_interfaces, details = _packet_capture_interfaces_from_tshark_output(
                out
            )
            interfaces.extend(parsed_interfaces)
        elif _packet_capture_looks_like_permission_issue(app, out):
            app.packet_capture_status_var.set("permission missing")
            append_packet_capture_output(
                app,
                _packet_capture_dumpcap_permission_message(),
                replace=True,
            )
            app.show_dumpcap_permission_hint()
    if not interfaces and _packet_capture_dep_enabled(app, "ip"):
        rc, out = run_cmd(["ip", "-o", "link", "show"], timeout=6)
        if rc == 0:
            interfaces.extend(_packet_capture_interfaces_from_ip_output(out))
    unique = _packet_capture_unique_interfaces(interfaces)
    app.packet_capture_interfaces = unique
    app.dep_status["packet_capture_interfaces"] = bool(unique)
    interface_combo = _app_value(app, "packet_capture_interface_combo")
    if interface_combo is not None:
        interface_combo.configure(values=unique)
    preferred = next(
        (name for name in unique if name != "lo"),
        unique[0] if unique else "",
    )
    selected_interface = str(
        _app_var_get(app, "packet_capture_interface_var", "") or ""
    ).strip()
    if preferred and not selected_interface:
        _app_var_set(app, "packet_capture_interface_var", preferred)
    elif selected_interface not in unique:
        _app_var_set(app, "packet_capture_interface_var", preferred)
    if unique:
        summary = _packet_capture_interfaces_ready_message(unique)
        _app_var_set(app, "packet_capture_status_var", "interfaces ready")
        append_packet_capture_output(app, summary, replace=True)
        if details:
            append_packet_capture_output(app, "\n".join(details))
    else:
        _app_var_set(app, "packet_capture_status_var", "no interfaces found")
        append_packet_capture_output(
            app,
            _packet_capture_no_interfaces_message(),
            replace=True,
        )


def packet_capture_update_runtime(app):
    if app.packet_capture_text_after_id is not None:
        try:
            app.after_cancel(app.packet_capture_text_after_id)
        except Exception:
            pass
        app.packet_capture_text_after_id = None
    if not app.packet_capture_running:
        return
    runtime = max(0, int(time.time() - float(app.packet_capture_started_at or 0.0)))
    _app_var_set(app, "packet_capture_runtime_var", f"{runtime}s")
    file_path = (app.packet_capture_output_path or "").strip()
    if file_path and os.path.isfile(file_path):
        try:
            _app_var_set(
                app,
                "packet_capture_size_var",
                _packet_capture_size_text(file_path),
            )
        except Exception:
            pass
    app.packet_capture_text_after_id = app.after(
        1000,
        lambda: packet_capture_update_runtime(app),
    )


def packet_capture_show_file_info(app):
    file_path = _packet_capture_file_path(app)
    if not file_path:
        append_packet_capture_output(
            app,
            _packet_capture_file_info_missing_message(file_path),
        )
        return
    if not os.path.isfile(file_path):
        append_packet_capture_output(
            app,
            _packet_capture_file_info_missing_message(file_path),
        )
        return
    if _packet_capture_dep_enabled(app, "capinfos"):
        rc, out = run_cmd(["capinfos", file_path], timeout=10)
        if rc == 0 and (out or "").strip():
            append_packet_capture_output(
                app,
                _packet_capture_capinfos_text(out),
            )
            size_text = str(_app_var_get(app, "packet_capture_size_var", "-") or "-")
            summary = _packet_capture_capinfos_summary(out, size_text)
            _app_var_set(app, "packet_capture_packets_var", summary["packets"])
            _app_var_set(app, "packet_capture_size_var", summary["size_text"])
            return
    try:
        size_text = _packet_capture_size_text(file_path)
        _app_var_set(app, "packet_capture_size_var", size_text)
        append_packet_capture_output(
            app,
            _packet_capture_file_info_text(file_path, size_text),
        )
    except Exception as exc:
        append_packet_capture_output(
            app,
            _packet_capture_file_info_error_message(str(exc)),
        )


def packet_capture_start_async(app):
    interface = str(_app_var_get(app, "packet_capture_interface_var", "") or "").strip()
    guard_message = _packet_capture_start_guard_message(
        app.packet_capture_running,
        interface,
    )
    if app.packet_capture_running:
        append_packet_capture_output(app, guard_message)
        return
    if not interface:
        append_packet_capture_output(
            app,
            guard_message,
            replace=True,
        )
        _app_var_set(app, "packet_capture_status_var", "interface missing")
        return
    output_file = str(_app_var_get(app, "packet_capture_file_var", "") or "").strip()
    if not output_file:
        output_file = packet_capture_generate_default_path(app)
        _app_var_set(app, "packet_capture_file_var", output_file)
    output_dir = os.path.dirname(output_file)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
    capture_filter = _packet_capture_filter(app)
    cmd, capture_tool = _packet_capture_start_command(app, interface, output_file)
    if not cmd or not capture_tool:
        append_packet_capture_output(
            app,
            _packet_capture_missing_tool_message(),
            replace=True,
        )
        _app_var_set(app, "packet_capture_status_var", "tool missing")
        app.log(_packet_capture_missing_tool_log_message())
        app.show_wireshark_install_hint()
        return
    app._select_security_tab(app.tab_packet_capture)
    clear_packet_capture_output(app)
    append_packet_capture_output(
        app,
        _packet_capture_start_text(
            capture_tool,
            interface,
            output_file,
            capture_filter,
        ),
    )
    app.packet_capture_running = True
    app.packet_capture_cancel_requested = False
    app.packet_capture_started_at = time.time()
    app.packet_capture_output_path = output_file
    _app_var_set(app, "packet_capture_status_var", "running")
    _app_var_set(app, "packet_capture_runtime_var", "0s")
    _app_var_set(app, "packet_capture_packets_var", "-")
    _app_var_set(app, "packet_capture_size_var", "-")
    packet_capture_set_running_state(app, True)
    app.log(_packet_capture_state_log_message("gestartet", interface))

    def worker():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            app.packet_capture_active_process = proc
            captured_lines = []
            suppress_live_output = False
            if proc.stdout is not None:
                for line in proc.stdout:
                    text_line = (line or "").rstrip()
                    if not text_line:
                        continue
                    captured_lines.append(text_line)
                    if _packet_capture_looks_like_permission_issue(
                        app,
                        "\n".join(captured_lines[-10:]),
                    ):
                        suppress_live_output = True
                    if suppress_live_output:
                        continue
                    app.after(
                        0,
                        lambda msg=text_line: append_packet_capture_output(app, msg),
                    )
            return_code = proc.wait()
            details = "\n".join(captured_lines[-20:]).strip()

            def finish_success():
                app.packet_capture_active_process = None
                app.packet_capture_running = False
                permission_issue = _packet_capture_looks_like_permission_issue(
                    app, details
                )
                _app_var_set(
                    app,
                    "packet_capture_status_var",
                    _packet_capture_completion_status(
                        app.packet_capture_cancel_requested,
                        return_code,
                    ),
                )
                packet_capture_set_running_state(app, False)
                if details:
                    append_packet_capture_output(
                        app,
                        (
                            _packet_capture_permission_failure_message()
                            if permission_issue
                            else details
                        ),
                    )
                if return_code != 0 and not app.packet_capture_cancel_requested:
                    output_message, log_message = (
                        _packet_capture_completion_failure_messages(
                            interface,
                            return_code,
                        )
                    )
                    append_packet_capture_output(
                        app,
                        output_message,
                    )
                    app.log(log_message)
                    if permission_issue:
                        app.show_dumpcap_permission_hint()
                else:
                    app.log(_packet_capture_state_log_message("stopped", interface))
                if _packet_capture_has_existing_file(app):
                    packet_capture_show_file_info(app)
                packet_capture_update_runtime(app)

            call_in_ui_thread(app, finish_success)
        except Exception as exc:
            error_text = str(exc)

            def finish_error(message=error_text):
                app.packet_capture_active_process = None
                app.packet_capture_running = False
                _app_var_set(app, "packet_capture_status_var", "error")
                packet_capture_set_running_state(app, False)
                output_message, log_message = _packet_capture_start_failure_messages(
                    message
                )
                append_packet_capture_output(
                    app,
                    output_message,
                )
                app.log(log_message)
                packet_capture_update_runtime(app)

            call_in_ui_thread(app, finish_error)

    threading.Thread(target=worker, daemon=True).start()
    packet_capture_update_runtime(app)


def packet_capture_stop(app):
    if not app.packet_capture_running:
        append_packet_capture_output(
            app,
            _packet_capture_stop_request_message(False),
        )
        return
    app.packet_capture_cancel_requested = True
    proc = app.packet_capture_active_process
    if proc is None:
        app.packet_capture_running = False
        _app_var_set(app, "packet_capture_status_var", "stopped")
        packet_capture_set_running_state(app, False)
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception as exc:
        output_message, log_message = _packet_capture_stop_failure_messages(str(exc))
        append_packet_capture_output(app, output_message)
        app.log(log_message)
        return
    append_packet_capture_output(
        app,
        _packet_capture_stop_request_message(True),
    )


def open_packet_capture_in_wireshark(app):
    if (
        callable(getattr(app, "wireshark_launch_blocked", None))
        and app.wireshark_launch_blocked()
    ):
        message = (
            "Wireshark launch is blocked in NetMon.\n"
            "Note: this option only blocks it inside NetMon. "
            "System-wide permissions or packages must be adjusted separately."
        )
        append_packet_capture_output(app, message)
        try:
            app.log("Wireshark launch from NetMon blocked.")
        except Exception:
            pass
        return
    file_path = _packet_capture_existing_file_path(app)
    launcher = _packet_capture_wireshark_launcher(app)
    target = (launcher.get("target") or "").strip()
    missing_message = _packet_capture_wireshark_missing_message(target, file_path)
    if missing_message:
        append_packet_capture_output(app, missing_message)
        return
    try:
        subprocess.Popen(_packet_capture_wireshark_command(launcher, file_path))
        append_packet_capture_output(
            app,
            _packet_capture_wireshark_result_message(file_path),
        )
    except Exception as exc:
        append_packet_capture_output(
            app,
            _packet_capture_wireshark_result_message(file_path, str(exc)),
        )
        app.log(_packet_capture_wireshark_failure_log_message(str(exc)))


def open_packet_capture_file_location(app):
    file_path = _packet_capture_file_path(app)
    target = _packet_capture_open_target_path(app)
    missing_message = _packet_capture_open_location_missing_message(file_path, target)
    if missing_message:
        append_packet_capture_output(
            app,
            missing_message,
        )
        return
    try:
        subprocess.Popen(_packet_capture_open_location_command(target))
        append_packet_capture_output(
            app,
            _packet_capture_open_location_result_message(target),
        )
    except Exception as exc:
        append_packet_capture_output(
            app,
            _packet_capture_open_location_result_message(target, str(exc)),
        )
        app.log(_packet_capture_open_location_failure_log_message(str(exc)))
