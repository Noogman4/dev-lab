#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import tkinter as tk
import unittest
from tkinter import messagebox, ttk

APP_TITLE = "Bautei NetMon Festplatten V2"
REFRESH_MS = 2500
LSBLK_COLUMNS = (
    "NAME,KNAME,PATH,TYPE,SIZE,MODEL,VENDOR,LABEL,FSTYPE,"
    "MOUNTPOINTS,RM,HOTPLUG,TRAN,SERIAL,PKNAME"
)
SAFE_SYSTEM_PREFIXES = ("/", "/boot", "/home", "/var", "/usr")


class PasswordDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=prompt, wraplength=320).pack(anchor="w", pady=(0, 8))
        self.entry = ttk.Entry(frame, show="*", width=40)
        self.entry.pack(fill="x", pady=(0, 10))
        self.entry.focus_set()

        btns = ttk.Frame(frame)
        btns.pack(fill="x")
        ttk.Button(btns, text="Abbrechen", command=self.cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="OK", command=self.accept).pack(side="right")

        self.bind("<Return>", lambda _e: self.accept())
        self.bind("<Escape>", lambda _e: self.cancel())

        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = max(parent.winfo_width(), 1)
        parent_h = max(parent.winfo_height(), 1)
        dialog_w = max(self.winfo_width(), 360)
        dialog_h = max(self.winfo_height(), 120)
        pos_x = parent_x + (parent_w - dialog_w) // 2
        pos_y = parent_y + (parent_h - dialog_h) // 2
        self.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")

    def accept(self):
        self.result = self.entry.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class DiskManagerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1180x700")
        self.root.minsize(980, 560)

        self.devices = {}
        self.selected_key = None
        self.last_device_paths = set()

        self.show_internal_var = tk.BooleanVar(value=False)
        self.show_mounted_only_var = tk.BooleanVar(value=False)
        self.auto_open_after_mount_var = tk.BooleanVar(value=False)

        self._build_ui()
        self.refresh_devices(initial=True)
        self._schedule_refresh()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 16, "bold")).pack(side="left")

        action_bar = ttk.Frame(header)
        action_bar.pack(side="right")

        self.refresh_btn = ttk.Button(action_bar, text="Aktualisieren", command=self.refresh_devices)
        self.refresh_btn.pack(side="left", padx=4)

        self.mount_btn = ttk.Button(action_bar, text="Öffnen / Mounten", command=self.mount_selected)
        self.mount_btn.pack(side="left", padx=4)

        self.unmount_btn = ttk.Button(action_bar, text="Unmounten", command=self.unmount_selected)
        self.unmount_btn.pack(side="left", padx=4)

        self.open_btn = ttk.Button(action_bar, text="Ordner öffnen", command=self.open_mountpoint)
        self.open_btn.pack(side="left", padx=4)

        filters = ttk.LabelFrame(outer, text="Filter / Optionen", padding=10)
        filters.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(
            filters,
            text="Interne Laufwerke anzeigen",
            variable=self.show_internal_var,
            command=self.refresh_devices,
        ).pack(side="left", padx=(0, 14))

        ttk.Checkbutton(
            filters,
            text="Nur gemountete anzeigen",
            variable=self.show_mounted_only_var,
            command=self.refresh_devices,
        ).pack(side="left", padx=(0, 14))

        ttk.Checkbutton(
            filters,
            text="Nach Mounten Ordner öffnen",
            variable=self.auto_open_after_mount_var,
        ).pack(side="left", padx=(0, 14))

        self.summary_var = tk.StringVar(value="Keine Geräte geladen")
        ttk.Label(filters, textvariable=self.summary_var).pack(side="right")

        main = ttk.Panedwindow(outer, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=(0, 0, 10, 0))
        right = ttk.Frame(main)
        main.add(left, weight=4)
        main.add(right, weight=2)

        columns = ("gerät", "typ", "größe", "usb", "dateisystem", "status", "mountpoint")
        self.tree = ttk.Treeview(left, columns=columns, show="tree headings", height=22)
        self.tree.heading("#0", text="Name / Pfad")
        self.tree.heading("gerät", text="Gerät")
        self.tree.heading("typ", text="Typ")
        self.tree.heading("größe", text="Größe")
        self.tree.heading("usb", text="USB")
        self.tree.heading("dateisystem", text="Dateisystem")
        self.tree.heading("status", text="Status")
        self.tree.heading("mountpoint", text="Mountpoint")

        self.tree.column("#0", width=280, anchor="w")
        self.tree.column("gerät", width=110, anchor="w")
        self.tree.column("typ", width=90, anchor="center")
        self.tree.column("größe", width=90, anchor="center")
        self.tree.column("usb", width=70, anchor="center")
        self.tree.column("dateisystem", width=110, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("mountpoint", width=210, anchor="w")

        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_double_click)

        ttk.Label(right, text="Gerätedetails", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))
        self.details = tk.Text(right, height=16, wrap="word")
        self.details.pack(fill="both", expand=True)
        self.details.configure(state="disabled")

        ttk.Label(right, text="Aktionen / Hinweise", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 6))
        self.hints = tk.Text(right, height=10, wrap="word")
        self.hints.pack(fill="both", expand=False)
        self.hints.configure(state="normal")
        self.hints.insert(
            "1.0",
            "• Doppelklick: öffnet/mountet oder unmountet das ausgewählte Gerät.\n"
            "• LUKS-verschlüsselte Laufwerke fragen beim Öffnen nach dem Passwort.\n"
            "• Interne System-Partitionen werden standardmäßig ausgeblendet.\n"
            "• USB-Sticks und Wechselmedien werden bevorzugt angezeigt.\n"
            "• Für NetMon kann dieses Modul später als eigene Klasse übernommen werden.\n"
            "• Mount/Unmount läuft über udisksctl und benötigt eine saubere Desktop-Umgebung.\n",
        )
        self.hints.configure(state="disabled")

        statusbar = ttk.Frame(outer, padding=(0, 8, 0, 0))
        statusbar.pack(fill="x")
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(statusbar, textvariable=self.status_var).pack(side="left")

    def _schedule_refresh(self):
        self.root.after(REFRESH_MS, self._auto_refresh)

    def _auto_refresh(self):
        self.refresh_devices(silent=True)
        self._schedule_refresh()

    def run_command(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as exc:
            return 1, "", str(exc)

    def get_lsblk_data(self):
        code, out, err = self.run_command(["lsblk", "-J", "-p", "-o", LSBLK_COLUMNS])
        if code != 0:
            raise RuntimeError(err or "lsblk konnte nicht ausgeführt werden.")
        return json.loads(out)

    @staticmethod
    def is_usb_like(dev):
        tran = (dev.get("tran") or "").lower()
        hotplug = str(dev.get("hotplug") or "0")
        rm = str(dev.get("rm") or "0")
        return tran == "usb" or hotplug == "1" or rm == "1"

    @staticmethod
    def is_likely_system_device(dev):
        mountpoints = [m for m in (dev.get("mountpoints") or []) if m]
        for mp in mountpoints:
            if mp in SAFE_SYSTEM_PREFIXES:
                return True
            if mp.startswith("/boot") or mp.startswith("/home"):
                return True
        return False

    @staticmethod
    def is_luks_container(dev):
        return (dev.get("fstype") or "").lower() == "crypto_luks"

    @staticmethod
    def flatten_partitions(blockdevices):
        items = []

        def walk(dev, parent=None):
            dtype = dev.get("type")
            children = dev.get("children") or []

            if dtype in ("part", "crypt", "lvm"):
                items.append((dev, parent))
            elif dtype == "disk" and not children:
                items.append((dev, parent))

            for child in children:
                walk(child, dev)

        for dev in blockdevices:
            walk(dev)
        return items

    def should_display_device(self, info):
        if self.show_mounted_only_var.get() and not info["mounted"]:
            return False
        if self.show_internal_var.get():
            return True
        return info["usb"] or not info["system_like"] or info.get("is_luks", False)

    def refresh_devices(self, initial=False, silent=False):
        previous = self.selected_key
        try:
            data = self.get_lsblk_data()
            entries = self.flatten_partitions(data.get("blockdevices", []))
            parsed_devices = {}

            for dev, parent in entries:
                path = dev.get("path") or ""
                if not path:
                    continue

                mountpoints = [m for m in (dev.get("mountpoints") or []) if m]
                mounted = bool(mountpoints)
                usb = self.is_usb_like(dev) or bool(parent and self.is_usb_like(parent))
                system_like = self.is_likely_system_device(dev)
                is_luks = self.is_luks_container(dev)
                name = dev.get("label") or dev.get("model") or os.path.basename(path)
                dtype = dev.get("type") or "?"
                fstype = dev.get("fstype") or "-"
                size = dev.get("size") or "-"
                mp = ", ".join(mountpoints) if mountpoints else "-"
                if is_luks and not mounted:
                    status = "verschlüsselt"
                else:
                    status = "gemountet" if mounted else "nicht gemountet"
                device_short = dev.get("name") or os.path.basename(path)

                parsed_devices[path] = {
                    "path": path,
                    "name": name,
                    "type": dtype,
                    "size": size,
                    "fstype": fstype,
                    "mountpoints": mountpoints,
                    "mounted": mounted,
                    "usb": usb,
                    "system_like": system_like,
                    "vendor": dev.get("vendor") or (parent or {}).get("vendor") or "",
                    "model": dev.get("model") or (parent or {}).get("model") or "",
                    "serial": dev.get("serial") or (parent or {}).get("serial") or "",
                    "tran": dev.get("tran") or (parent or {}).get("tran") or "",
                    "parent": (parent or {}).get("path", "-"),
                    "parent_name": (parent or {}).get("name", "-"),
                    "rm": dev.get("rm"),
                    "hotplug": dev.get("hotplug"),
                    "label": dev.get("label") or "",
                    "display_status": status,
                    "display_mountpoints": mp,
                    "device_short": device_short,
                    "is_luks": is_luks,
                }

            new_paths = set(parsed_devices.keys()) - self.last_device_paths
            removed_paths = self.last_device_paths - set(parsed_devices.keys())
            self.last_device_paths = set(parsed_devices.keys())

            self.devices = {}
            self.tree.delete(*self.tree.get_children())

            visible_count = 0
            mounted_count = 0
            usb_count = 0

            for key, info in sorted(parsed_devices.items(), key=lambda item: item[0]):
                if not self.should_display_device(info):
                    continue

                visible_count += 1
                mounted_count += 1 if info["mounted"] else 0
                usb_count += 1 if info["usb"] else 0
                self.devices[key] = info

                item_id = self.tree.insert(
                    "",
                    "end",
                    iid=key,
                    text=f"{info['name']}  ({info['path']})",
                    values=(
                        info["device_short"],
                        info["type"],
                        info["size"],
                        "Ja" if info["usb"] else "Nein",
                        info["fstype"],
                        info["display_status"],
                        info["display_mountpoints"],
                    ),
                )

                if previous == key:
                    self.tree.selection_set(item_id)
                    self.tree.focus(item_id)
                    self.selected_key = key

            if previous not in self.devices:
                self.selected_key = None

            self.summary_var.set(
                f"Angezeigt: {visible_count} | Gemountet: {mounted_count} | USB/Wechselmedien: {usb_count}"
            )

            if new_paths and not silent:
                self.set_status(f"Neues Gerät erkannt: {', '.join(sorted(new_paths))}")
            elif removed_paths and not silent:
                self.set_status(f"Gerät entfernt: {', '.join(sorted(removed_paths))}")
            elif not silent:
                self.set_status("Geräteliste aktualisiert")

            if initial and not self.devices:
                self.set_status("Keine passenden Laufwerke gefunden")

            self.update_details()
            self.update_buttons()
        except Exception as exc:
            if not silent:
                messagebox.showerror("Fehler", str(exc))
            self.set_status(f"Fehler: {exc}")

    def set_status(self, text):
        self.status_var.set(text)

    def on_select(self, _event=None):
        selection = self.tree.selection()
        self.selected_key = selection[0] if selection else None
        self.update_details()
        self.update_buttons()

    def on_double_click(self, _event=None):
        if not self.selected_key:
            return
        dev = self.devices.get(self.selected_key)
        if not dev:
            return
        if dev["mounted"] and not dev.get("is_luks"):
            self.unmount_selected()
        else:
            self.mount_selected()

    def update_buttons(self):
        dev = self.devices.get(self.selected_key) if self.selected_key else None
        if not dev:
            self.mount_btn.configure(state="disabled")
            self.unmount_btn.configure(state="disabled")
            self.open_btn.configure(state="disabled")
            return

        mount_enabled = True if dev.get("is_luks") else not dev["mounted"]
        unmount_enabled = dev["mounted"] and not dev["system_like"] and not dev.get("is_luks")
        open_enabled = dev["mounted"]

        self.mount_btn.configure(state="normal" if mount_enabled else "disabled")
        self.unmount_btn.configure(state="normal" if unmount_enabled else "disabled")
        self.open_btn.configure(state="normal" if open_enabled else "disabled")

    def update_details(self):
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")

        dev = self.devices.get(self.selected_key) if self.selected_key else None
        if not dev:
            self.details.insert("end", "Kein Gerät ausgewählt.")
        else:
            recommendation = []
            if dev["system_like"]:
                recommendation.append("Achtung: Sieht nach System- oder wichtiger interner Partition aus.")
            if dev.get("is_luks"):
                recommendation.append("LUKS-verschlüsselt: Beim Öffnen wird ein Passwortdialog angezeigt.")
            if dev["usb"]:
                recommendation.append("Geeignet für externes Medium / USB-Stick.")
            if not dev["mounted"] and not dev.get("is_luks"):
                recommendation.append("Kann direkt aus der GUI gemountet werden.")
            if dev["mounted"] and not dev["system_like"]:
                recommendation.append(
                    "Kann sicher aus der GUI unmountet werden, sofern keine Datei offen ist."
                )

            lines = [
                f"Name: {dev['name']}",
                f"Pfad: {dev['path']}",
                f"Kurzer Gerätename: {dev['device_short']}",
                f"Typ: {dev['type']}",
                f"Größe: {dev['size']}",
                f"Dateisystem: {dev['fstype']}",
                f"LUKS-Container: {'Ja' if dev.get('is_luks') else 'Nein'}",
                f"USB/Wechselmedium: {'Ja' if dev['usb'] else 'Nein'}",
                f"Systemrelevant erkannt: {'Ja' if dev['system_like'] else 'Nein'}",
                f"Gemountet: {'Ja' if dev['mounted'] else 'Nein'}",
                f"Mountpoints: {', '.join(dev['mountpoints']) if dev['mountpoints'] else '-'}",
                f"Label: {dev['label'] or '-'}",
                f"Hersteller: {dev['vendor'] or '-'}",
                f"Modell: {dev['model'] or '-'}",
                f"Seriennummer: {dev['serial'] or '-'}",
                f"Transfer: {dev['tran'] or '-'}",
                f"Parent-Gerät: {dev['parent']} ({dev['parent_name']})",
                "",
                "Empfehlung:",
                *(recommendation or ["Keine besondere Empfehlung."]),
            ]
            self.details.insert("end", "\n".join(lines))

        self.details.configure(state="disabled")

    def prompt_for_passphrase(self, dev):
        dialog = PasswordDialog(
            self.root,
            "LUKS-Passwort",
            f"Bitte Passwort für {dev['path']} eingeben:",
        )
        self.root.wait_window(dialog)
        return dialog.result

    def find_unlocked_child_for(self, luks_path):
        try:
            data = self.get_lsblk_data()
        except Exception:
            return None

        for dev, parent in self.flatten_partitions(data.get("blockdevices", [])):
            if (parent or {}).get("path") == luks_path:
                child_path = dev.get("path")
                if child_path and not self.is_luks_container(dev):
                    return child_path
        return None

    def unlock_luks_and_mount(self, dev):
        passphrase = self.prompt_for_passphrase(dev)
        if passphrase is None:
            self.set_status("LUKS-Entsperren abgebrochen")
            return
        if passphrase == "":
            messagebox.showwarning("Leeres Passwort", "Bitte ein Passwort eingeben.")
            return

        keyfile_path = None
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                tmp.write(passphrase)
                tmp.flush()
                keyfile_path = tmp.name

            code, out, err = self.run_command(["udisksctl", "unlock", "-b", dev["path"], "--key-file", keyfile_path])
            if code != 0:
                messagebox.showerror("Entsperren fehlgeschlagen", err or out or "Unbekannter Fehler")
                self.set_status(f"LUKS-Entsperren fehlgeschlagen: {dev['path']}")
                return

            self.refresh_devices(silent=True)
            unlocked_path = self.find_unlocked_child_for(dev["path"])
            if not unlocked_path:
                self.set_status(out or f"Entsperrt: {dev['path']}")
                messagebox.showinfo(
                    "Entsperrt",
                    "Das LUKS-Laufwerk wurde entsperrt, aber das gemappte Gerät konnte nicht automatisch gefunden werden.",
                )
                return

            code, mout, merr = self.run_command(["udisksctl", "mount", "-b", unlocked_path])
            if code != 0:
                messagebox.showerror("Mounten fehlgeschlagen", merr or mout or "Unbekannter Fehler")
                self.set_status(f"Entsperrt, aber Mounten fehlgeschlagen: {unlocked_path}")
                return

            self.set_status(mout or f"Entsperrt und gemountet: {unlocked_path}")
            self.refresh_devices(silent=True)
            if unlocked_path in self.devices:
                self.tree.selection_set(unlocked_path)
                self.tree.focus(unlocked_path)
                self.selected_key = unlocked_path
                self.update_details()
                self.update_buttons()
            if self.auto_open_after_mount_var.get():
                self.open_mountpoint()
        finally:
            if keyfile_path and os.path.exists(keyfile_path):
                try:
                    os.remove(keyfile_path)
                except OSError:
                    pass

    def mount_selected(self):
        dev = self.devices.get(self.selected_key) if self.selected_key else None
        if not dev:
            return

        if dev.get("is_luks"):
            self.unlock_luks_and_mount(dev)
            return

        code, out, err = self.run_command(["udisksctl", "mount", "-b", dev["path"]])
        if code != 0:
            messagebox.showerror("Mounten fehlgeschlagen", err or out or "Unbekannter Fehler")
            self.set_status(f"Mounten fehlgeschlagen: {dev['path']}")
            return

        self.set_status(out or f"Gemountet: {dev['path']}")
        self.refresh_devices(silent=True)
        if self.auto_open_after_mount_var.get():
            self.open_mountpoint()

    def unmount_selected(self):
        dev = self.devices.get(self.selected_key) if self.selected_key else None
        if not dev:
            return
        if dev["system_like"]:
            messagebox.showwarning(
                "Geschützt",
                "Diese Partition wirkt systemrelevant und wird in Version 2 vorsichtshalber nicht unmountet.",
            )
            return

        code, out, err = self.run_command(["udisksctl", "unmount", "-b", dev["path"]])
        if code != 0:
            messagebox.showerror("Unmounten fehlgeschlagen", err or out or "Unbekannter Fehler")
            self.set_status(f"Unmounten fehlgeschlagen: {dev['path']}")
            return

        self.set_status(out or f"Unmountet: {dev['path']}")
        self.refresh_devices(silent=True)

    def open_mountpoint(self):
        dev = self.devices.get(self.selected_key) if self.selected_key else None
        if not dev or not dev["mountpoints"]:
            return

        mountpoint = dev["mountpoints"][0]
        try:
            subprocess.Popen(["xdg-open", mountpoint])
            self.set_status(f"Ordner geöffnet: {mountpoint}")
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))


class DiskManagerLogicTests(unittest.TestCase):
    def test_is_usb_like_detects_usb_transport(self):
        self.assertTrue(DiskManagerApp.is_usb_like({"tran": "usb", "hotplug": "0", "rm": "0"}))

    def test_is_usb_like_detects_hotplug(self):
        self.assertTrue(DiskManagerApp.is_usb_like({"tran": None, "hotplug": "1", "rm": "0"}))

    def test_is_usb_like_detects_removable(self):
        self.assertTrue(DiskManagerApp.is_usb_like({"tran": None, "hotplug": "0", "rm": "1"}))

    def test_is_usb_like_false_for_internal_disk(self):
        self.assertFalse(DiskManagerApp.is_usb_like({"tran": "sata", "hotplug": "0", "rm": "0"}))

    def test_is_likely_system_device_for_root(self):
        self.assertTrue(DiskManagerApp.is_likely_system_device({"mountpoints": ["/"]}))

    def test_is_likely_system_device_for_boot(self):
        self.assertTrue(DiskManagerApp.is_likely_system_device({"mountpoints": ["/boot/efi"]}))

    def test_is_likely_system_device_false_for_media_mount(self):
        self.assertFalse(DiskManagerApp.is_likely_system_device({"mountpoints": ["/media/sven/USB"]}))

    def test_is_luks_container_detects_crypto_luks(self):
        self.assertTrue(DiskManagerApp.is_luks_container({"fstype": "crypto_LUKS"}))

    def test_is_luks_container_false_for_ext4(self):
        self.assertFalse(DiskManagerApp.is_luks_container({"fstype": "ext4"}))

    def test_flatten_partitions_collects_partitions_and_leaf_disks(self):
        blockdevices = [
            {
                "path": "/dev/sda",
                "type": "disk",
                "children": [
                    {"path": "/dev/sda1", "type": "part", "children": []},
                    {"path": "/dev/sda2", "type": "part", "children": []},
                ],
            },
            {"path": "/dev/sdb", "type": "disk", "children": []},
        ]
        items = DiskManagerApp.flatten_partitions(blockdevices)
        paths = [item[0]["path"] for item in items]
        self.assertEqual(paths, ["/dev/sda1", "/dev/sda2", "/dev/sdb"])


def check_dependencies():
    missing = []
    for cmd in ("lsblk", "udisksctl", "xdg-open"):
        if subprocess.run(["sh", "-c", f"command -v {cmd}"], capture_output=True).returncode != 0:
            missing.append(cmd)
    if missing:
        raise RuntimeError("Fehlende Programme: " + ", ".join(missing))


def run_tests():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DiskManagerLogicTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    if "--test" in sys.argv:
        raise SystemExit(run_tests())

    check_dependencies()
    root = tk.Tk()
    try:
        root.iconname(APP_TITLE)
    except Exception:
        pass
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    DiskManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
