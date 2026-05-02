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
    from netmon.core.utils import human_size
except ModuleNotFoundError:
    from core.utils import human_size


def packet_capture_set_running_state(app, running):
    packet_capture_ready = bool(
        app.dep_status.get("tshark") or app.dep_status.get("dumpcap")
    )
    if hasattr(app, "btn_packet_capture_start"):
        app.btn_packet_capture_start.configure(
            state="disabled" if running or not packet_capture_ready else "normal"
        )
    if hasattr(app, "btn_packet_capture_stop"):
        app.btn_packet_capture_stop.configure(
            state="normal" if running and packet_capture_ready else "disabled"
        )


def append_packet_capture_output(app, text: str, replace: bool = False):
    if not hasattr(app, "packet_capture_text") or app.packet_capture_text is None:
        return
    widget = app.packet_capture_text
    widget.configure(state="normal")
    if replace:
        widget.delete("1.0", "end")
    if text:
        if not replace and widget.index("end-1c") != "1.0":
            widget.insert("end", "\n")
        widget.insert("end", text.rstrip() + "\n")
    widget.see("end")
    widget.configure(state="disabled")


def clear_packet_capture_output(app):
    if not hasattr(app, "packet_capture_text") or app.packet_capture_text is None:
        return
    app.packet_capture_text.configure(state="normal")
    app.packet_capture_text.delete("1.0", "end")
    app.packet_capture_text.configure(state="disabled")


def packet_capture_generate_default_path(app):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(app.packet_capture_dir, f"capture_{stamp}.pcapng")


def choose_packet_capture_file(app):
    initial_dir = app.packet_capture_dir
    current_path = (app.packet_capture_file_var.get() or "").strip()
    generated_path = packet_capture_generate_default_path(app)
    initial_file = os.path.basename(current_path or generated_path)
    chosen = filedialog.asksaveasfilename(
        parent=app,
        title="Capture-Datei auswählen",
        initialdir=initial_dir,
        initialfile=initial_file,
        defaultextension=".pcapng",
        filetypes=[
            ("Packet Capture", "*.pcapng *.pcap"),
            ("Alle Dateien", "*.*"),
        ],
    )
    if chosen:
        app.packet_capture_file_var.set(chosen)
        app.packet_capture_output_path = chosen
        append_packet_capture_output(app, f"Capture-Datei gesetzt: {chosen}")


def refresh_packet_capture_interfaces(app):
    app._select_security_tab(app.tab_packet_capture)
    interfaces = []
    details = []
    if app.dep_status.get("tshark"):
        rc, out = run_cmd(["tshark", "-D"], timeout=8)
        if rc == 0:
            for line in (out or "").splitlines():
                raw = line.strip()
                if not raw:
                    continue
                entry = raw.split(".", 1)[-1].strip() if "." in raw else raw
                name = entry.split(" ", 1)[0].strip()
                if name:
                    interfaces.append(name)
                    details.append(raw)
        elif app._looks_like_dumpcap_permission_issue(out):
            app.packet_capture_status_var.set("Berechtigung fehlt")
            append_packet_capture_output(
                app,
                "tshark ist vorhanden, aber dumpcap hat keine ausreichenden Berechtigungen.",
                replace=True,
            )
            app.show_dumpcap_permission_hint()
    if not interfaces and app.dep_status.get("ip"):
        rc, out = run_cmd(["ip", "-o", "link", "show"], timeout=6)
        if rc == 0:
            for line in (out or "").splitlines():
                parts = line.split(":", 2)
                if len(parts) < 2:
                    continue
                name = parts[1].strip().split("@", 1)[0]
                if name:
                    interfaces.append(name)
    unique = []
    seen = set()
    for name in interfaces:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    app.packet_capture_interfaces = unique
    app.dep_status["packet_capture_interfaces"] = bool(unique)
    if hasattr(app, "packet_capture_interface_combo"):
        app.packet_capture_interface_combo.configure(values=unique)
    preferred = next(
        (name for name in unique if name != "lo"),
        unique[0] if unique else "",
    )
    if preferred and not (app.packet_capture_interface_var.get() or "").strip():
        app.packet_capture_interface_var.set(preferred)
    elif (app.packet_capture_interface_var.get() or "").strip() not in unique:
        app.packet_capture_interface_var.set(preferred)
    if unique:
        summary = "Verfügbare Interfaces: " + ", ".join(unique)
        app.packet_capture_status_var.set("Interfaces bereit")
        append_packet_capture_output(app, summary, replace=True)
        if details:
            append_packet_capture_output(app, "\n".join(details))
    else:
        app.packet_capture_status_var.set("Keine Interfaces gefunden")
        append_packet_capture_output(
            app,
            "Keine Capture-Interfaces gefunden. Prüfe tshark, dumpcap oder iproute2.",
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
    app.packet_capture_runtime_var.set(f"{runtime}s")
    file_path = (app.packet_capture_output_path or "").strip()
    if file_path and os.path.isfile(file_path):
        try:
            size_bytes = os.path.getsize(file_path)
            app.packet_capture_size_var.set(human_size(size_bytes))
        except Exception:
            pass
    app.packet_capture_text_after_id = app.after(
        1000,
        lambda: packet_capture_update_runtime(app),
    )


def packet_capture_show_file_info(app):
    file_path = (
        app.packet_capture_output_path or app.packet_capture_file_var.get() or ""
    ).strip()
    if not file_path:
        append_packet_capture_output(app, "Noch keine Capture-Datei ausgewählt.")
        return
    if not os.path.isfile(file_path):
        append_packet_capture_output(app, f"Capture-Datei nicht gefunden: {file_path}")
        return
    if app.dep_status.get("capinfos"):
        rc, out = run_cmd(["capinfos", file_path], timeout=10)
        if rc == 0 and (out or "").strip():
            append_packet_capture_output(
                app,
                "=== Capture-Datei Info ===\n" + (out or "").strip(),
            )
            packets = "-"
            size_text = app.packet_capture_size_var.get()
            for line in (out or "").splitlines():
                lower = line.lower()
                if "number of packets" in lower:
                    packets = line.split(":", 1)[-1].strip() or "-"
                if lower.startswith("file size"):
                    size_text = line.split(":", 1)[-1].strip() or size_text
            app.packet_capture_packets_var.set(packets)
            app.packet_capture_size_var.set(size_text)
            return
    try:
        size_bytes = os.path.getsize(file_path)
        size_text = human_size(size_bytes)
        app.packet_capture_size_var.set(size_text)
        append_packet_capture_output(
            app,
            "=== Capture-Datei Info ===\n"
            f"Datei: {file_path}\n"
            f"Größe: {size_text}",
        )
    except Exception as exc:
        append_packet_capture_output(
            app,
            f"Datei-Info konnte nicht gelesen werden: {exc}",
        )


def packet_capture_start_async(app):
    if app.packet_capture_running:
        append_packet_capture_output(app, "Ein Capture läuft bereits.")
        return
    interface = (app.packet_capture_interface_var.get() or "").strip()
    if not interface:
        append_packet_capture_output(
            app,
            "Bitte zuerst ein Capture-Interface auswählen.",
            replace=True,
        )
        app.packet_capture_status_var.set("Interface fehlt")
        return
    output_file = (app.packet_capture_file_var.get() or "").strip()
    if not output_file:
        output_file = packet_capture_generate_default_path(app)
        app.packet_capture_file_var.set(output_file)
    output_dir = os.path.dirname(output_file)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
    capture_filter = (app.packet_capture_filter_var.get() or "").strip()
    if app.dep_status.get("tshark"):
        cmd = ["tshark", "-i", interface]
        if capture_filter:
            cmd.extend(["-f", capture_filter])
        cmd.extend(["-w", output_file])
        capture_tool = "tshark"
    elif app.dep_status.get("dumpcap"):
        cmd = ["dumpcap", "-i", interface]
        if capture_filter:
            cmd.extend(["-f", capture_filter])
        cmd.extend(["-w", output_file])
        capture_tool = "dumpcap"
    else:
        append_packet_capture_output(
            app,
            "Packet Capture ist nicht verfügbar: tshark oder dumpcap fehlt.",
            replace=True,
        )
        app.packet_capture_status_var.set("Tool fehlt")
        app.log("Packet Capture fehlgeschlagen: tshark/dumpcap fehlt.")
        app.show_wireshark_install_hint()
        return
    app._select_security_tab(app.tab_packet_capture)
    clear_packet_capture_output(app)
    append_packet_capture_output(
        app,
        "=== Packet Capture gestartet ===\n"
        f"Tool: {capture_tool}\n"
        f"Interface: {interface}\n"
        f"Datei: {output_file}\n"
        f"Filter: {capture_filter or '-'}",
    )
    app.packet_capture_running = True
    app.packet_capture_cancel_requested = False
    app.packet_capture_started_at = time.time()
    app.packet_capture_output_path = output_file
    app.packet_capture_status_var.set("läuft")
    app.packet_capture_runtime_var.set("0s")
    app.packet_capture_packets_var.set("-")
    app.packet_capture_size_var.set("-")
    packet_capture_set_running_state(app, True)
    app.log(f"Packet Capture gestartet ({interface}).")

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
            if proc.stdout is not None:
                for line in proc.stdout:
                    text_line = (line or "").rstrip()
                    if not text_line:
                        continue
                    captured_lines.append(text_line)
                    app.after(
                        0,
                        lambda msg=text_line: append_packet_capture_output(app, msg),
                    )
            return_code = proc.wait()
            details = "\n".join(captured_lines[-20:]).strip()

            def finish_success():
                app.packet_capture_active_process = None
                app.packet_capture_running = False
                app.packet_capture_status_var.set(
                    "gestoppt"
                    if app.packet_capture_cancel_requested
                    else (
                        "abgeschlossen"
                        if return_code == 0
                        else f"Fehler ({return_code})"
                    )
                )
                packet_capture_set_running_state(app, False)
                if details:
                    append_packet_capture_output(app, details)
                if return_code != 0 and not app.packet_capture_cancel_requested:
                    append_packet_capture_output(
                        app,
                        "Hinweis: Capture wurde mit Fehler beendet. Fehlende Rechte "
                        "für tshark/dumpcap sind häufig die Ursache.",
                    )
                    app.log(
                        f"Packet Capture fehlgeschlagen ({interface}, rc={return_code})."
                    )
                    if app._looks_like_dumpcap_permission_issue(details):
                        app.show_dumpcap_permission_hint()
                else:
                    app.log(f"Packet Capture gestoppt ({interface}).")
                packet_capture_show_file_info(app)
                packet_capture_update_runtime(app)

            app.after(0, finish_success)
        except Exception as exc:
            error_text = str(exc)

            def finish_error(message=error_text):
                app.packet_capture_active_process = None
                app.packet_capture_running = False
                app.packet_capture_status_var.set("Fehler")
                packet_capture_set_running_state(app, False)
                append_packet_capture_output(
                    app,
                    f"Capture konnte nicht gestartet werden: {message}",
                )
                app.log(f"Packet Capture fehlgeschlagen: {message}")
                packet_capture_update_runtime(app)

            app.after(0, finish_error)

    threading.Thread(target=worker, daemon=True).start()
    packet_capture_update_runtime(app)


def packet_capture_stop(app):
    if not app.packet_capture_running:
        append_packet_capture_output(app, "Es läuft aktuell kein Capture.")
        return
    app.packet_capture_cancel_requested = True
    proc = app.packet_capture_active_process
    if proc is None:
        app.packet_capture_running = False
        app.packet_capture_status_var.set("gestoppt")
        packet_capture_set_running_state(app, False)
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception as exc:
        append_packet_capture_output(app, f"Capture-Stopp fehlgeschlagen: {exc}")
        app.log(f"Packet Capture-Stopp fehlgeschlagen: {exc}")
        return
    append_packet_capture_output(app, "Capture-Stopp angefordert.")


def open_packet_capture_in_wireshark(app):
    file_path = (
        app.packet_capture_output_path or app.packet_capture_file_var.get() or ""
    ).strip()
    launcher = dict(app.dep_status.get("wireshark_launcher") or {})
    target = (launcher.get("target") or "").strip()
    kind = (launcher.get("kind") or "").strip()
    if not target:
        append_packet_capture_output(
            app,
            "Wireshark ist nicht verfügbar. Installationshinweis: sudo apt install wireshark",
        )
        return
    if not file_path or not os.path.isfile(file_path):
        append_packet_capture_output(
            app,
            "Keine gültige Capture-Datei zum Öffnen gefunden.",
        )
        return
    try:
        if kind == "binary":
            subprocess.Popen([target, file_path])
        elif kind == "flatpak":
            subprocess.Popen(["flatpak", "run", target, file_path])
        elif kind == "desktop":
            if has_cmd("gtk-launch"):
                subprocess.Popen(["gtk-launch", target])
            else:
                raise RuntimeError("gtk-launch ist nicht verfügbar.")
        elif kind == "desktop_file":
            if has_cmd("xdg-open"):
                subprocess.Popen(["xdg-open", target])
            else:
                raise RuntimeError("xdg-open ist nicht verfügbar.")
        else:
            raise RuntimeError("Kein Wireshark-Launcher gefunden.")
        append_packet_capture_output(app, f"Wireshark geöffnet: {file_path}")
    except Exception as exc:
        append_packet_capture_output(
            app,
            f"Wireshark konnte nicht geöffnet werden: {exc}",
        )
        app.log(f"Wireshark-Start fehlgeschlagen: {exc}")


def open_packet_capture_file_location(app):
    file_path = (
        app.packet_capture_output_path or app.packet_capture_file_var.get() or ""
    ).strip()
    if not file_path:
        append_packet_capture_output(app, "Noch keine Capture-Datei vorhanden.")
        return
    target = file_path if os.path.exists(file_path) else os.path.dirname(file_path)
    if not target:
        append_packet_capture_output(
            app,
            "Kein gültiger Pfad für Capture-Datei vorhanden.",
        )
        return
    if not has_cmd("xdg-open"):
        append_packet_capture_output(app, "xdg-open ist nicht verfügbar.")
        return
    try:
        subprocess.Popen(["xdg-open", target])
        append_packet_capture_output(app, f"Capture-Pfad geöffnet: {target}")
    except Exception as exc:
        append_packet_capture_output(
            app,
            f"Capture-Pfad konnte nicht geöffnet werden: {exc}",
        )
        app.log(f"Capture-Datei öffnen fehlgeschlagen: {exc}")
