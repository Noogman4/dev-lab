"""Trusted Tk window for fixed pixels; no renderer X socket reaches the desktop."""

import threading
import time
import tkinter as tk

from netmon.core import projectm_profile as profiles, stall_log

DISPLAY_MODES = (
    ("fit", "Originalformat (4:3)"),
    ("fill", "Fenster ausfüllen (beschnitten)"),
    ("stretch", "Auf Fenstergröße strecken"),
)


def _scaled_image(image, size, mode):
    if image.size == size:
        return image
    from PIL import Image, ImageOps

    if mode == "fill":
        return ImageOps.fit(image, size, method=Image.Resampling.BILINEAR)
    return image.resize(size, Image.Resampling.BILINEAR)


class Scaler:
    """Resizes frames off the Tk main thread; newest job wins, one result slot.

    The worker touches only PIL images, never Tk, the request or the app.
    """

    def __init__(self):
        self._condition = threading.Condition()
        self._job = None
        self._result = None
        self.error = None
        self._ended = False
        self.thread = threading.Thread(
            target=self._run, name="projectm-scaler", daemon=True
        )
        self.thread.start()

    def submit(self, image, size, mode="fit", generation=0):
        with self._condition:
            self._job = (image, size, mode, generation)
            self._condition.notify()

    def take(self):
        with self._condition:
            result, self._result = self._result, None
            return result

    def stop(self):
        with self._condition:
            self._ended = True
            self._job = None
            self._condition.notify()
        if threading.current_thread() is not self.thread:
            self.thread.join(timeout=0.05)

    def _run(self):
        try:
            while True:
                with self._condition:
                    while self._job is None and not self._ended:
                        self._condition.wait()
                    if self._ended:
                        return
                    image, size, mode, generation = self._job
                    self._job = None
                image = _scaled_image(image, size, mode)
                with self._condition:
                    self._result = (image, mode, generation)
        except Exception as exc:
            with self._condition:
                self.error = f"{type(exc).__name__}: {exc}"[:256]


class PixelWindow:
    def __init__(self, app, request):
        from PIL import Image, ImageTk

        self.app, self.request = app, request
        self.profile = profiles.resolve(
            getattr(request, "resolution", profiles.DEFAULT)
        )
        self.cpu_profile = profiles.resolve_cpu(
            getattr(request, "cpu_profile", profiles.DEFAULT_CPU)
        )
        self.generation = 0
        self._backend_title = ""
        self.Image, self.ImageTk = Image, ImageTk
        self.closed = False
        self.timer = None
        self.photo = None
        self.image = None
        self.scaler = None
        self.menu = None
        self.fullscreen = False
        self.windowed_geometry = None
        self.display_mode = "fit"
        self.displayed = 0
        self.eq_window = None
        self.eq_scales = {}
        # Opt-in diagnosis only (NETMON_RADIO_STALL_LOG=1); None costs nothing.
        self.monitor = stall_log.WindowMonitor() if stall_log.enabled() else None
        self.window = tk.Toplevel(app)
        try:
            self.window.title("NetMon Visualisierung")
            self.window.geometry(profiles.DEFAULT)
            self.window.configure(background="black")
            self.label = tk.Label(
                self.window,
                text="Visualisierung wird vorbereitet …",
                background="black",
                foreground="white",
                borderwidth=0,
                highlightthickness=0,
            )
            self.label.pack(fill="both", expand=True)
            self.fullscreen_var = tk.BooleanVar(self.window, False)
            self.preset_var = tk.IntVar(self.window, -1)
            self.display_mode_var = tk.StringVar(self.window, self.display_mode)
            self.resolution_var = tk.StringVar(self.window, self.profile.key)
            self.cpu_profile_var = tk.StringVar(self.window, self.cpu_profile.key)
            self.backend_var = tk.StringVar(
                self.window, getattr(request, "backend", "cpu")
            )
            self.window.protocol("WM_DELETE_WINDOW", self.close)
            self.window.bind("<Destroy>", self._destroyed, add="+")
            self.window.bind("<Double-Button-1>", self.toggle_fullscreen)
            self.window.bind("<Escape>", self.exit_fullscreen)
            self.window.bind("<Button-3>", self.show_menu)
            self.window.bind("<Configure>", self._resized, add="+")
            self.scaler = Scaler()
            self.timer = self.window.after(5, self.tick)
        except Exception:
            self.close()
            raise

    def _destroyed(self, event):
        if event.widget is self.window and not self.closed:
            self.close(destroy=False)

    def _current(self):
        data = vars(self.app)
        return not (
            self.closed
            or data.get("radio_projectm_proc") is not self.request
            or self.request.cancelled.is_set()
            or self.request.done.is_set()
            or data.get("_radio_panel_destroying")
            or data.get("_projectm_closing")
        )

    def toggle_fullscreen(self, _event=None):
        if not self._current():
            return "break"
        if self.fullscreen:
            return self.exit_fullscreen()
        self.windowed_geometry = self.window.geometry()
        self.window.attributes("-fullscreen", True)
        self.fullscreen = True
        self.fullscreen_var.set(True)
        return "break"

    def exit_fullscreen(self, _event=None):
        if not self.closed and self.fullscreen:
            self.window.attributes("-fullscreen", False)
            self.fullscreen = False
            self.fullscreen_var.set(False)
            if self.windowed_geometry:
                self.window.geometry(self.windowed_geometry)
        return "break"

    def _resized(self, event):
        if event.widget is self.window and self._current():
            self._draw()

    def _target_size(self):
        width = min(self.window.winfo_width(), self.window.winfo_screenwidth())
        height = min(self.window.winfo_height(), self.window.winfo_screenheight())
        if width < 2 or height < 2:
            width, height = self.profile.width, self.profile.height
        if self.display_mode != "fit":
            return width, height
        scale = min(width / self.profile.width, height / self.profile.height)
        return (
            max(1, int(self.profile.width * scale)),
            max(1, int(self.profile.height * scale)),
        )

    def _draw(self):
        # One-off redraw of the last frame after a resize or display-mode change.
        if self.image is None or self.closed:
            return
        size = self._target_size()
        image = _scaled_image(self.image, size, self.display_mode)
        self._show(image)

    def set_display_mode(self, mode):
        if not self._current() or mode not in {name for name, _label in DISPLAY_MODES}:
            return False
        self.display_mode = mode
        self.display_mode_var.set(mode)
        self._draw()
        return True

    def _show(self, image):
        # Main thread: copy into one reused Tk image instead of a new one per frame.
        if (
            self.photo is None
            or (self.photo.width(), self.photo.height()) != image.size
        ):
            self.photo = self.ImageTk.PhotoImage("RGB", image.size, master=self.window)
            self.label.configure(image=self.photo, text="")
        self.photo.paste(image)

    def _preset_state(self):
        callback = getattr(self.request, "preset_state", None)
        return callback() if callback else ((), None)

    def choose_preset(self, index, owner=None):
        if (
            (owner is None or owner is self.request)
            and self._current()
            and self.request.select_preset(index)
        ):
            self.preset_var.set(-1 if index is None else index)

    def set_resolution(self, resolution, owner=None):
        if (owner is not None and owner is not self.request) or not self._current():
            return False
        from netmon.netmon_projectm_sidecar import change_projectm_resolution

        request = change_projectm_resolution(self.app, self.request, resolution)
        return self._replace_request(request)

    def set_cpu_profile(self, cpu_profile, owner=None):
        if (owner is not None and owner is not self.request) or not self._current():
            return False
        from netmon.netmon_projectm_sidecar import change_projectm_cpu_profile

        request = change_projectm_cpu_profile(self.app, self.request, cpu_profile)
        return self._replace_request(request)

    def set_backend(self, backend, owner=None):
        if (owner is not None and owner is not self.request) or not self._current():
            return False
        from netmon.netmon_projectm_sidecar import change_projectm_backend

        return self._replace_request(
            change_projectm_backend(self.app, self.request, backend)
        )

    def _current_visual_eq(self):
        eq = getattr(self.request, "visual_eq", None)
        return eq if isinstance(eq, profiles.VisualEq) else profiles.NEUTRAL_EQ

    def open_visual_eq(self):
        """Small slider window; only the projectM PCM copy is shaped, not audio."""
        if not self._current():
            return None
        if self.eq_window is not None:
            try:
                self.eq_window.deiconify()
                self.eq_window.lift()
                return self.eq_window
            except tk.TclError:
                self.eq_window = None
        window = tk.Toplevel(self.window)
        window.title("Klang für Visualisierung")
        window.resizable(False, False)
        current = self._current_visual_eq()
        self.eq_scales = {}
        for row, (key, label, value) in enumerate(
            (
                ("bass_db", "Bass (dB)", current.bass_db),
                ("treble_db", "Höhen (dB)", current.treble_db),
                ("sensitivity_db", "Empfindlichkeit (dB)", current.sensitivity_db),
            )
        ):
            tk.Label(window, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", padx=8, pady=4
            )
            scale = tk.Scale(
                window,
                from_=profiles.VISUAL_EQ_MIN_DB,
                to=profiles.VISUAL_EQ_MAX_DB,
                resolution=1,
                orient="horizontal",
                length=240,
            )
            scale.set(value)
            scale.configure(command=lambda _value: self._visual_eq_changed())
            scale.grid(row=row, column=1, padx=8, pady=4)
            self.eq_scales[key] = scale
        tk.Button(window, text="Zurücksetzen", command=self.reset_visual_eq).grid(
            row=3, column=0, columnspan=2, pady=(4, 2)
        )
        tk.Label(
            window,
            text="Wirkt nur auf die Visualisierung, nicht auf den Ton.",
            foreground="#666666",
        ).grid(row=4, column=0, columnspan=2, padx=8, pady=(0, 8))
        window.protocol("WM_DELETE_WINDOW", self._close_visual_eq)
        self.eq_window = window
        return window

    def _visual_eq_from_scales(self):
        return profiles.VisualEq(
            *(
                int(self.eq_scales[key].get())
                for key in ("bass_db", "treble_db", "sensitivity_db")
            )
        )

    def _visual_eq_changed(self):
        if not self._current() or not self.eq_scales:
            return False
        eq = self._visual_eq_from_scales()
        setter = getattr(self.request, "set_visual_eq", None)
        if setter is None or not setter(eq):
            return False
        self.app._projectm_visual_eq = eq
        return True

    def reset_visual_eq(self):
        for scale in self.eq_scales.values():
            scale.set(0)
        return self._visual_eq_changed()

    def _close_visual_eq(self):
        window, self.eq_window = self.eq_window, None
        self.eq_scales = {}
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass

    def _render_state(self):
        callback = getattr(self.request, "render_state", None)
        return callback() if callback else ("cpu", "")

    def _replace_request(self, request):
        if request is None:
            return False
        if request is self.request:
            return True
        self.request = request
        self.profile = profiles.resolve(request.resolution)
        self.cpu_profile = profiles.resolve_cpu(request.cpu_profile)
        self.generation += 1
        self.label.configure(image="", text="Visualisierung wird vorbereitet …")
        self.image = self.photo = None
        self.resolution_var.set(self.profile.key)
        self.cpu_profile_var.set(self.cpu_profile.key)
        self.backend_var.set(request.backend)
        if self.menu is not None:
            self.menu.destroy()
            self.menu = None
        return True

    def _fill_presets(self, menu, choices, start, end):
        # Lazy pages keep a large preset pack from constructing 50,000 Tk items.
        menu.delete(0, "end")
        for child in menu.winfo_children():
            child.destroy()
        if end - start <= 100:
            for index in range(start, end):
                label = " ".join(choices[index].split())[:140]
                menu.add_radiobutton(
                    label=label,
                    variable=self.preset_var,
                    value=index,
                    command=lambda i=index, owner=self.request: self.choose_preset(
                        i, owner
                    ),
                )
            return
        step = 1000 if end - start > 10000 else 100
        for first in range(start, end, step):
            last = min(first + step, end)
            page = tk.Menu(menu, tearoff=False)
            page.configure(
                postcommand=lambda m=page, a=first, b=last: self._fill_presets(
                    m, choices, a, b
                )
            )
            menu.add_cascade(
                label=f"{first + 1}–{last}: {' '.join(choices[first].split())[:60]}",
                menu=page,
            )

    def show_menu(self, event):
        if not self._current():
            return "break"
        if self.menu is not None:
            self.menu.destroy()
        self.menu = tk.Menu(self.window, tearoff=False)
        self.menu.add_checkbutton(
            label="Vollbild",
            variable=self.fullscreen_var,
            command=self.toggle_fullscreen,
        )
        display = tk.Menu(self.menu, tearoff=False)
        for mode, label in DISPLAY_MODES:
            if mode == "fit":
                label = f"Originalformat ({self.profile.aspect})"
            display.add_radiobutton(
                label=label,
                variable=self.display_mode_var,
                value=mode,
                command=lambda value=mode: self.set_display_mode(value),
            )
        self.menu.add_cascade(label="Darstellung", menu=display)
        resolution = tk.Menu(self.menu, tearoff=False)
        for profile in profiles.PROFILES:
            resolution.add_radiobutton(
                label=f"{profile.width} × {profile.height}"
                + (" (Standard)" if profile.key == profiles.DEFAULT else ""),
                variable=self.resolution_var,
                value=profile.key,
                command=lambda key=profile.key, owner=self.request: self.set_resolution(
                    key, owner
                ),
            )
        self.menu.add_cascade(label="Auflösung", menu=resolution)
        cpu = tk.Menu(self.menu, tearoff=False)
        for profile in profiles.CPU_PROFILES:
            cpu.add_radiobutton(
                label=profile.label,
                variable=self.cpu_profile_var,
                value=profile.key,
                command=lambda key=profile.key, owner=self.request: self.set_cpu_profile(
                    key, owner
                ),
            )
        actual, _error = self._render_state()
        self.menu.add_cascade(
            label="CPU-Leistung",
            menu=cpu,
            state=(
                "disabled"
                if actual == "gpu" or getattr(self.request, "backend", "cpu") == "gpu"
                else "normal"
            ),
        )
        backend = tk.Menu(self.menu, tearoff=False)
        for key, label in (("auto", "Automatisch"), ("cpu", "CPU"), ("gpu", "GPU")):
            backend.add_radiobutton(
                label=label,
                variable=self.backend_var,
                value=key,
                command=lambda value=key, owner=self.request: self.set_backend(
                    value, owner
                ),
            )
        self.menu.add_cascade(label="Rendern", menu=backend)
        self.menu.add_command(
            label="Klang für Visualisierung…", command=self.open_visual_eq
        )
        self.menu.add_separator()
        choices, selected = self._preset_state()
        self.preset_var.set(-1 if selected is None else selected)
        self.menu.add_radiobutton(
            label="Automatischer Preset-Wechsel",
            variable=self.preset_var,
            value=-1,
            state="normal" if choices else "disabled",
            command=lambda owner=self.request: self.choose_preset(None, owner),
        )
        presets = tk.Menu(self.menu, tearoff=False)
        if choices:
            self._fill_presets(presets, choices, 0, len(choices))
        else:
            presets.add_command(label="Presets werden vorbereitet …", state="disabled")
        self.menu.add_cascade(label="Presets", menu=presets)
        self.menu.add_separator()
        self.menu.add_command(label="Visualisierung schließen", command=self.close)
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
        return "break"

    def tick(self):
        self.timer = None
        if self.closed:
            return
        if not self._current():
            self.close(notify=False)
            return
        try:
            actual, gpu_error = self._render_state()
            title = "NetMon Visualisierung" + (
                " · GPU"
                if actual == "gpu"
                else (
                    " · CPU (GPU nicht verfügbar)"
                    if actual == "cpu" and gpu_error
                    else " · CPU" if actual == "cpu" else ""
                )
            )
            if title != self._backend_title:
                self.window.title(title)
                self._backend_title = title
            if self.scaler.error:
                raise RuntimeError(self.scaler.error)
            frame = self.request.frames.take()
            if frame is not None:
                # Frames are opaque RGBA; drop the alpha channel, it halves the cost.
                self.image = self.Image.frombuffer(
                    "RGB",
                    (self.profile.width, self.profile.height),
                    frame,
                    "raw",
                    "RGBX",
                    0,
                    1,
                )
                self.scaler.submit(
                    self.image, self._target_size(), self.display_mode, self.generation
                )
            scaled = self.scaler.take()
            paste_ms = None
            if scaled is not None:
                image, mode, generation = scaled
                if (
                    generation == self.generation
                    and mode == self.display_mode
                    and image.size == self._target_size()
                ):
                    started = time.perf_counter()
                    self._show(image)
                    paste_ms = (time.perf_counter() - started) * 1000.0
                    self.displayed += 1
            if self.monitor is not None:
                self.monitor.observe(self.request.frames.received, paste_ms)
            self.timer = self.window.after(5, self.tick)
        except Exception:
            # Invalid Tk/raw-frame handling stops this owner, never a fallback.
            self.close()

    def close(self, *, notify=True, destroy=True):
        if self.closed:
            return
        self.closed = True
        if notify:
            self.request.stop()
        if self.timer is not None:
            try:
                self.window.after_cancel(self.timer)
            except tk.TclError:
                pass
            self.timer = None
        if self.scaler is not None:
            self.scaler.stop()
        self.photo = None
        self.image = None
        if self.menu is not None and destroy:
            self.menu.destroy()
        self.menu = None
        if destroy:
            self._close_visual_eq()
        else:
            self.eq_window, self.eq_scales = None, {}
        if vars(self.app).get("_projectm_pixel_window") is self:
            self.app._projectm_pixel_window = None
        if destroy:
            try:
                self.window.destroy()
            except tk.TclError:
                pass


def ensure(app, request):
    old = vars(app).get("_projectm_pixel_window")
    if old is not None:
        if old.request is request and not old.closed:
            old.window.deiconify()
            old.window.lift()
            return old
        old.close(notify=False)
    try:
        window = PixelWindow(app, request)
        app._projectm_pixel_window = window
        return window
    except Exception:
        request.stop()
        raise


def close(app):
    window = vars(app).get("_projectm_pixel_window")
    if window is not None:
        window.close()
