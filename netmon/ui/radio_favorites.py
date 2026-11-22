"""Responsive favorite cards; only the existing sandbox fetches logo images."""

from collections import OrderedDict
import hashlib
import os
from pathlib import Path
import queue
import stat
import tempfile
import threading
import time
import tkinter as tk
from tkinter import font as tkfont, ttk

from netmon.core import icon_http, radio_logo, radio_sandbox

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

CARD_WIDTH = 156
CARD_HEIGHT = 118
CARD_GAP = 8
LOGO_SIZE = 52
RETRY_DELAY_MS = 2000
RETRY_COOLDOWN = 300


def logo_url(station):
    try:
        return icon_http.parse_url(str(station.get("favicon", "") or "")).url
    except (ValueError, UnicodeError):
        return ""


def logo_homepage(station):
    try:
        return icon_http.parse_url(str(station.get("homepage", "") or "")).url
    except (ValueError, UnicodeError):
        return ""


def logo_key(station):
    return logo_url(station) or (
        "homepage:" + logo_homepage(station) if logo_homepage(station) else ""
    )


def load_logo(url, cache_dir, *, homepage=""):
    """Read bounded raw pixels, or fetch/decode through the existing sandbox."""
    path = Path(cache_dir) / (
        hashlib.sha256(url.encode("utf-8")).hexdigest() + ".pixels"
    )
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_size > radio_logo.MAX_REPLY_BYTES
            ):
                raise ValueError("Invalid logo cache")
            payload = stream.read(radio_logo.MAX_REPLY_BYTES + 1)
        radio_logo.validate_pixels(payload)
        return payload
    except (OSError, ValueError):
        pass
    if url.startswith("homepage:"):
        homepage, url = url[len("homepage:") :], ""
    payload = (
        radio_sandbox.fetch_logo(url, homepage=homepage)
        if homepage
        else radio_sandbox.fetch_logo(url)
    )
    radio_logo.validate_pixels(payload)
    # Cache failures must not prevent displaying an otherwise valid logo.
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".favorite-logo-", delete=False
        ) as stream:
            temporary = stream.name
            stream.write(payload)
        os.replace(temporary, path)
    except OSError:
        pass
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)
    return payload


def fit_name(name, font, width, max_lines=2):
    """Fit a name into a bounded number of lines, including unbroken names."""
    remaining = " ".join(str(name or "").split())
    lines = []
    for line in range(max_lines):
        end = len(remaining)
        while end > 1 and font.measure(remaining[:end]) > width:
            end -= 1
        if end < len(remaining):
            if line == max_lines - 1:
                text = remaining[:end]
                while text and font.measure(text + "…") > width:
                    text = text[:-1]
                lines.append(text.rstrip() + "…")
                break
            split = remaining.rfind(" ", 0, end + 1)
            end = split if split > 0 else end
        lines.append(remaining[:end])
        remaining = remaining[end:].lstrip()
        if not remaining:
            break
    return "\n".join(lines)


def fit_logo_dimensions(width, height, size):
    """Fit either small or large images proportionally into the given box."""
    scale = min(size[0] / width, size[1] / height)
    return (
        max(1, min(size[0], round(width * scale))),
        max(1, min(size[1], round(height * scale))),
    )


def fit_logo_image(image, size):
    """Resize trusted RGBA pixels and center them in a fixed transparent box."""
    resized = image.resize(
        fit_logo_dimensions(image.width, image.height, size), Image.Resampling.LANCZOS
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(
        resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2)
    )
    return canvas


class RadioFavoriteTiles(ttk.Frame):
    """A page of cards with bounded logo work and normal station callbacks."""

    def __init__(
        self,
        parent,
        *,
        cache_dir,
        limiter,
        on_select,
        on_play,
        on_context,
        theme,
        loader=load_logo,
        on_logo_error=None,
    ):
        super().__init__(parent)
        self.cache_dir, self.limiter, self.loader = cache_dir, limiter, loader
        self.on_select, self.on_play, self.on_context = on_select, on_play, on_context
        self.on_logo_error = on_logo_error
        self.theme = dict(theme)
        self.font = tkfont.Font(
            self,
            family=tkfont.nametofont("TkDefaultFont").actual("family"),
            size=11,
            weight="bold",
        )
        self.canvas = tk.Canvas(
            self, highlightthickness=0, borderwidth=0, yscrollincrement=24
        )
        self.canvas.pack(fill="both", expand=True)
        self.body = ttk.Frame(self.canvas)
        self.body_window = self.canvas.create_window(
            0, 0, window=self.body, anchor="nw"
        )
        self.canvas.bind("<Configure>", self._layout)
        self.body.bind("<Configure>", self._update_scrollregion)
        self.rows, self.cards, self.photos = [], {}, OrderedDict()
        self.selected, self.signature = "", None
        self.columns = 1
        self.results = queue.Queue(maxsize=100)
        self.stop = threading.Event()
        self.poll = None
        self.scroll_update = None
        self.pending = set()
        self.failures = OrderedDict()
        self.retry = None
        self.bind("<Destroy>", self._destroyed, add="+")
        for widget in (self.canvas, self.body):
            self._bind_wheel(widget)
        self.apply_theme(theme)

    def _bind_wheel(self, widget):
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(sequence, self._wheel)

    def _wheel(self, event):
        if self.body.winfo_reqheight() <= self.canvas.winfo_height():
            self.canvas.yview_moveto(0)
            return "break"
        direction = (
            -1 if getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0 else 1
        )
        self.canvas.yview_scroll(direction, "units")
        return "break"

    def _update_scrollregion(self, _event=None):
        viewport = max(1, self.canvas.winfo_height())
        content = self.body.winfo_reqheight()
        self.canvas.configure(
            scrollregion=(0, 0, self.canvas.winfo_width(), max(viewport, content))
        )
        if content <= viewport:
            self.canvas.yview_moveto(0)

    def deactivate(self):
        self.stop.set()
        if self.retry is not None:
            self.after_cancel(self.retry)
            self.retry = None
        if self.scroll_update is not None:
            self.after_cancel(self.scroll_update)
            self.scroll_update = None
        if self.poll is not None:
            self.after_cancel(self.poll)
            self.poll = None
        self.signature = None
        self.pending.clear()
        while True:
            try:
                self.results.get_nowait()
            except queue.Empty:
                break

    def _destroyed(self, event):
        if event.widget is self:
            self.deactivate()

    def show_stations(self, rows, selected=""):
        # The controller passes one existing page (at most 50 favorites).
        rows = list(rows)[:50]
        signature = tuple(
            (
                str(row.get("id", "")),
                str(row.get("name", "")),
                logo_key(row),
                logo_homepage(row),
            )
            for row in rows
        )
        if signature == self.signature:
            self.select(selected)
            self._start_logo_jobs()
            return
        self.deactivate()
        self.stop = threading.Event()
        self.signature, self.rows = signature, rows
        for card in self.cards.values():
            card.destroy()
        self.cards = {}
        for row in rows:
            key = str(row.get("id", ""))
            card = tk.Canvas(
                self.body,
                height=CARD_HEIGHT,
                highlightthickness=0,
                borderwidth=0,
                cursor="hand2",
                takefocus=True,
            )
            self.cards[key] = card
            card.bind("<ButtonRelease-1>", lambda e, k=key: self._click(k, e))
            card.bind("<Return>", lambda _e, k=key: self._activate(k))
            card.bind("<space>", lambda _e, k=key: self._activate(k))
            card.bind("<ButtonRelease-3>", lambda e, k=key: self._context(k, e))
            card.bind("<Menu>", lambda _e, k=key: self._keyboard_context(k))
            card.bind("<Shift-F10>", lambda _e, k=key: self._keyboard_context(k))
            card.bind("<FocusIn>", lambda _e, k=key: self.select(k))
            card.bind("<Enter>", lambda _e, k=key: self._draw(k, hover=True))
            card.bind("<Leave>", lambda _e, k=key: self._draw(k))
            for keyname, step in (
                ("Left", -1),
                ("Right", 1),
                ("Up", None),
                ("Down", None),
            ):
                card.bind(
                    "<" + keyname + ">",
                    lambda _e, k=key, n=keyname, s=step: self._navigate(k, n, s),
                )
            self._bind_wheel(card)
        self.canvas.yview_moveto(0)
        self.select(selected)
        self._layout()
        for _key, _name, url, _home in signature:
            if url in self.photos:
                self.photos.move_to_end(url)
        self._start_logo_jobs()

    def _start_logo_jobs(self):
        if self.retry is not None:
            self.after_cancel(self.retry)
        self.retry = None
        if self.stop.is_set():
            return
        now, jobs = time.monotonic(), {}
        for _key, _name, url, home in self.signature or ():
            if not url or url in self.photos or url in self.pending:
                continue
            attempts, retry_at, _reason = self.failures.get(url, (0, 0, ""))
            if now < retry_at:
                continue
            if attempts >= 2:
                self.failures.pop(url, None)
            jobs.setdefault(url, home)
        self.pending.update(jobs)
        if jobs:
            stop = self.stop
            threading.Thread(
                target=self._load, args=(list(jobs.items()), stop), daemon=True
            ).start()
            if self.poll is None:
                self.poll = self.after(60, self._receive)
        self._schedule_logo_retry()

    def _load(self, urls, stop):
        for url, homepage in urls:
            while not stop.is_set():
                if self.limiter.acquire(timeout=0.1):
                    break
            else:
                return
            try:
                if stop.is_set():
                    return
                try:
                    payload = (
                        self.loader(url, self.cache_dir, homepage=homepage)
                        if homepage
                        else self.loader(url, self.cache_dir)
                    )
                    reason = ""
                except Exception as error:
                    payload = None
                    reason = radio_sandbox.logo_error_code(error)
            finally:
                self.limiter.release()
            if stop.is_set():
                return
            try:
                self.results.put_nowait((stop, url, payload, reason))
            except queue.Full:
                return

    def _receive(self):
        self.poll = None
        while True:
            try:
                stop, url, payload, reason = self.results.get_nowait()
            except queue.Empty:
                break
            if stop is not self.stop or stop.is_set():
                continue
            self.pending.discard(url)
            photo = None
            if payload is not None and Image is not None and ImageTk is not None:
                try:
                    width, height, raw = radio_logo.validate_pixels(payload)[2]
                    image = Image.frombytes("RGBA", (width, height), raw)
                    image = fit_logo_image(image, (LOGO_SIZE, LOGO_SIZE))
                    photo = ImageTk.PhotoImage(image, master=self)
                except Exception:
                    reason = "invalid_reply"
            if photo is not None:
                self.photos[url] = photo
                self.photos.move_to_end(url)
                self.failures.pop(url, None)
            else:
                attempts = self.failures.get(url, (0, 0, ""))[0] + 1
                delay = RETRY_DELAY_MS / 1000 if attempts < 2 else RETRY_COOLDOWN
                reason = reason or "invalid_reply"
                self.failures[url] = (attempts, time.monotonic() + delay, reason)
                self.failures.move_to_end(url)
                while len(self.failures) > 128:
                    self.failures.popitem(last=False)
                if self.on_logo_error is not None:
                    self.on_logo_error(reason)
            while len(self.photos) > 128:
                self.photos.popitem(last=False)
            for key, _name, source, _home in self.signature or ():
                if source == url:
                    self._draw(key)
        if not self.stop.is_set() and self.pending:
            self.poll = self.after(100, self._receive)
        self._schedule_logo_retry()

    def _schedule_logo_retry(self):
        if not self.stop.is_set() and self.retry is None:
            active = {source for _, _, source, _ in self.signature or ()}
            times = [
                at
                for source, (attempts, at, _) in self.failures.items()
                if source in active and source not in self.pending and attempts < 2
            ]
            if times:
                delay = max(1, int((min(times) - time.monotonic()) * 1000) + 1)
                self.retry = self.after(delay, self._start_logo_jobs)

    def select(self, key):
        self.selected = key
        for station_id in self.cards:
            self._draw(station_id)

    def _activate(self, key):
        self.cards[key].focus_set()
        self.select(key)
        self.on_select(key)
        self.on_play(key)
        return "break"

    def _click(self, key, event):
        width = self.cards[key].winfo_width()
        if event.x >= width - 30 and event.y <= 28:
            return self._context(key, event)
        return self._activate(key)

    def _keyboard_context(self, key):
        card = self.cards[key]
        event = tk.Event()
        event.x_root = card.winfo_rootx() + card.winfo_width() - 20
        event.y_root = card.winfo_rooty() + 28
        return self._context(key, event)

    def _context(self, key, event):
        self.cards[key].focus_set()
        self.select(key)
        self.on_select(key)
        self.on_context(key, event)
        return "break"

    def _navigate(self, key, direction, step):
        keys = list(self.cards)
        delta = (
            step
            if step is not None
            else (-self.columns if direction == "Up" else self.columns)
        )
        next_key = keys[max(0, min(len(keys) - 1, keys.index(key) + delta))]
        self.cards[next_key].focus_set()
        self.select(next_key)
        self.on_select(next_key)
        row = keys.index(next_key) // self.columns
        top, bottom = self.canvas.yview()
        total = max(1, self.body.winfo_height())
        row_height = CARD_HEIGHT + CARD_GAP
        if row * row_height < top * total:
            self.canvas.yview_moveto(row * row_height / total)
        elif (row + 1) * row_height > bottom * total:
            self.canvas.yview_moveto(
                ((row + 1) * row_height - self.canvas.winfo_height()) / total
            )
        return "break"

    def _layout(self, _event=None):
        width = max(1, self.canvas.winfo_width())
        previous_columns = self.columns
        self.columns = max(1, width // CARD_WIDTH)
        self.canvas.itemconfigure(self.body_window, width=width)
        for column in range(max(previous_columns, self.columns)):
            self.body.columnconfigure(column, weight=0, minsize=0, uniform="")
        for column in range(self.columns):
            self.body.columnconfigure(column, weight=1, uniform="favorite")
        for index, (key, card) in enumerate(self.cards.items()):
            card.configure(width=max(100, width // self.columns - CARD_GAP))
            card.grid(
                row=index // self.columns,
                column=index % self.columns,
                sticky="ew",
                padx=CARD_GAP // 2,
                pady=CARD_GAP // 2,
            )
            self._draw(key)
        if self.scroll_update is None:

            def update_scrollregion():
                self.scroll_update = None
                self._update_scrollregion()

            # Grid may change the requested height while the body is offscreen.
            self.scroll_update = self.after_idle(update_scrollregion)

    def apply_theme(self, theme):
        self.theme = dict(theme)
        self.canvas.configure(background=theme["panel_bg"])
        for key in self.cards:
            self._draw(key)

    def _draw(self, key, hover=False):
        card = self.cards.get(key)
        if card is None:
            return
        row = next(row for row in self.rows if str(row.get("id", "")) == key)
        theme = self.theme
        width = max(100, int(card.cget("width")))
        center = width / 2
        card.configure(bg=theme["panel_bg"])
        card.delete("all")
        color = theme["tab_selected_bg"] if hover else theme["tree_bg"]
        outline = theme["accent"] if key == self.selected or hover else theme["border"]
        card.create_polygon(
            11,
            2,
            width - 11,
            2,
            width - 2,
            2,
            width - 2,
            11,
            width - 2,
            CARD_HEIGHT - 2,
            width - 11,
            CARD_HEIGHT - 2,
            11,
            CARD_HEIGHT - 2,
            2,
            CARD_HEIGHT - 2,
            2,
            CARD_HEIGHT - 11,
            2,
            11,
            2,
            2,
            smooth=True,
            splinesteps=24,
            fill=color,
            outline=outline,
            width=2 if key == self.selected or hover else 1,
        )
        photo = self.photos.get(logo_key(row))
        if photo is not None:
            card.create_image(center, 37, image=photo)
        else:
            # Our own vector radio mark: antenna, speaker and tuning controls.
            accent = theme["accent"]
            card.create_oval(
                center - 28, 9, center + 28, 65, fill=theme["tab_bg"], outline=""
            )
            card.create_line(
                center - 15, 27, center + 10, 17, fill=accent, width=2, capstyle="round"
            )
            card.create_rectangle(
                center - 19, 28, center + 19, 52, fill=color, outline=accent, width=2
            )
            card.create_oval(center - 14, 33, center - 1, 46, outline=accent, width=2)
            card.create_line(center + 5, 35, center + 15, 35, fill=accent, width=2)
            card.create_line(center + 5, 40, center + 15, 40, fill=accent, width=2)
            card.create_oval(center + 10, 45, center + 14, 49, fill=accent, outline="")
        card.create_text(
            center,
            93,
            text=fit_name(row.get("name", ""), self.font, width - 24),
            font=self.font,
            fill=theme["fg"],
            justify="center",
            anchor="center",
        )
        card.create_text(
            width - 15,
            14,
            text="⋯",
            fill=theme["muted_fg"],
            font=("TkDefaultFont", 12, "bold"),
            tags="actions",
        )
