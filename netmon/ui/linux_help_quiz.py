"""Nonmodal Linux learning quiz; all answers are passive, local text."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from netmon.features import linux_help_controller as reader
    from netmon.services.linux_help_quiz_service import (
        available_questions,
        choose_questions,
        load_questions,
    )
    from netmon.ui.linux_help_prompt import _colors, _tr
except ModuleNotFoundError:
    from features import linux_help_controller as reader
    from services.linux_help_quiz_service import (
        available_questions,
        choose_questions,
        load_questions,
    )
    from ui.linux_help_prompt import _colors, _tr


class QuizWindow(tk.Toplevel):
    def __init__(self, parent, owner, state, *, automatic=False):
        super().__init__(parent)
        self.owner, self.state = owner, state
        self.kind_labels = {
            "both": self.tr("linux_help_quiz_kind_both", "Befehle und Glossar"),
            "command": self.tr("linux_help_source_commands", "Befehle"),
            "glossary": self.tr("linux_help_source_glossary", "Glossar"),
        }
        self.kind_ids = {label: kind for kind, label in self.kind_labels.items()}
        self.all_categories = self.tr("linux_help_all_categories", "Alle Kategorien")
        self.automatic = automatic
        self.round_id = None
        self.questions = []
        self.index = 0
        self.answered = False
        self.bank, self.pool, self.suspended = [], [], []
        self.title(self.tr("linux_help_quiz_title", "Linux-Lernquiz"))
        self.geometry("780x820")
        self.minsize(680, 740)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.status = tk.StringVar(self)
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 4))
        self.quiz_tab, self.stats_tab, self.settings_tab = (
            ttk.Frame(self.tabs, padding=10) for _ in range(3)
        )
        for frame, title in (
            (self.quiz_tab, self.tr("linux_help_quiz_tab_quiz", "Quiz")),
            (self.stats_tab, self.tr("linux_help_quiz_tab_stats", "Statistik")),
            (
                self.settings_tab,
                self.tr("linux_help_quiz_tab_settings", "Einstellungen"),
            ),
        ):
            self.tabs.add(frame, text=title)
            frame.columnconfigure(0, weight=1)
        self._build_quiz()
        self._build_stats()
        self._build_settings()
        footer = ttk.Frame(self, padding=(12, 4, 12, 10))
        footer.grid(row=1, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer, textvariable=self.status, wraplength=640, justify="left"
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.snooze_button = ttk.Button(
            footer,
            text=self.tr("linux_help_quiz_snooze", "In 10 Minuten erinnern"),
            command=self.snooze,
        )
        self.snooze_button.grid(row=1, column=0, sticky="w")
        ttk.Button(
            footer, text=self.tr("btn_close", "Schließen"), command=self.close
        ).grid(row=1, column=1, sticky="e")
        self.tabs.bind("<<NotebookTabChanged>>", self._tab_changed)
        self.bind("<Configure>", self._resize, add="+")
        self.refresh_bank()
        self.refresh_stats()
        if automatic:
            self.kind.set(self.kind_labels[self.state.data["settings"]["kind"]])
            self.count.set(str(self.state.data["settings"]["count"]))
            self.status.set(
                self.tr(
                    "linux_help_quiz_reminder",
                    "Zeit für eine Lernrunde. Du kannst jetzt starten oder verschieben.",
                )
            )
        if state.error:
            self.status.set(state.error)
        self._snooze_state()
        _colors(owner, self)
        if automatic and not state.error and self.start():
            self.status.set(
                self.tr(
                    "linux_help_quiz_automatic_round",
                    "Automatische Lernrunde. Du kannst sie um zehn Minuten verschieben.",
                )
            )

    def tr(self, key, fallback):
        return _tr(self.owner, key, fallback)

    def _summary(self, pair):
        count, correct = pair
        percentage = f"{100 * correct / count:.0f} %" if count else "–"
        return self.tr(
            "linux_help_quiz_score",
            "{correct} / {count} richtig · Trefferquote {percentage}",
        ).format(correct=correct, count=count, percentage=percentage)

    def _resize(self, event):
        if event.widget is self:
            width = max(340, event.width - 90)
            self.prompt_label.configure(wraplength=width)
            self.feedback_label.configure(wraplength=width)
            for widget in self.option_buttons:
                widget.configure(wraplength=width - 35)

    def _build_quiz(self):
        form = ttk.Frame(self.quiz_tab)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.kind = tk.StringVar(self, value=self.kind_labels["both"])
        self.category = tk.StringVar(self, value=self.all_categories)
        self.count = tk.StringVar(self, value="5")
        self.read_only = tk.BooleanVar(self)
        self.form_widgets = []
        for row, (label, variable, values) in enumerate(
            (
                (
                    self.tr("linux_help_quiz_selection", "Auswahl"),
                    self.kind,
                    list(self.kind_ids),
                ),
                (
                    self.tr("linux_help_quiz_category", "Kategorie"),
                    self.category,
                    [self.all_categories],
                ),
                (
                    self.tr("linux_help_quiz_count", "Umfang"),
                    self.count,
                    ["5", "10", "15", "20", "25", "30"],
                ),
            )
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=3)
            combo = ttk.Combobox(
                form, textvariable=variable, values=values, state="readonly"
            )
            combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=3)
            self.form_widgets.append(combo)
        self.category_combo = self.form_widgets[1]
        read_button = ttk.Checkbutton(
            form,
            text=self.tr("linux_help_quiz_read_only", "Nur bereits gelesene Einträge"),
            variable=self.read_only,
        )
        read_button.grid(row=3, column=0, columnspan=2, sticky="w", pady=6)
        self.form_widgets.append(read_button)
        actions = ttk.Frame(self.quiz_tab)
        actions.grid(row=1, column=0, sticky="ew", pady=8)
        self.start_button = ttk.Button(
            actions,
            text=self.tr("linux_help_quiz_start", "Runde starten"),
            command=self.start,
        )
        self.start_button.pack(side="left")
        self.errors_button = ttk.Button(
            actions,
            text=self.tr("linux_help_quiz_repeat_errors", "Fehler wiederholen"),
            command=lambda: self.start(errors_only=True),
        )
        self.errors_button.pack(side="left", padx=8)
        self.round_status = tk.StringVar(
            self,
            value=self.tr("linux_help_quiz_round_idle", "Noch keine Runde gestartet."),
        )
        ttk.Label(self.quiz_tab, textvariable=self.round_status, wraplength=620).grid(
            row=2, column=0, sticky="ew", pady=5
        )
        question_frame = ttk.LabelFrame(
            self.quiz_tab, text=self.tr("linux_help_quiz_question", "Frage"), padding=10
        )
        question_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        question_frame.columnconfigure(0, weight=1)
        question_frame.rowconfigure(0, weight=1)
        self.quiz_tab.rowconfigure(3, weight=1)
        self.question_canvas = tk.Canvas(
            question_frame, highlightthickness=0, height=280
        )
        self.question_canvas.grid(row=0, column=0, sticky="nsew")
        question_scroll = ttk.Scrollbar(
            question_frame, orient="vertical", command=self.question_canvas.yview
        )
        question_scroll.grid(row=0, column=1, sticky="ns")
        self.question_canvas.configure(yscrollcommand=question_scroll.set)
        question_body = ttk.Frame(self.question_canvas)
        question_body.columnconfigure(0, weight=1)
        content = self.question_canvas.create_window(
            (0, 0), window=question_body, anchor="nw"
        )
        question_body.bind(
            "<Configure>",
            lambda _event: self.question_canvas.configure(
                scrollregion=self.question_canvas.bbox("all")
            ),
        )
        self.question_canvas.bind(
            "<Configure>",
            lambda event: self.question_canvas.itemconfigure(
                content, width=event.width
            ),
        )
        self.prompt_label = ttk.Label(
            question_body,
            text=self.tr(
                "linux_help_quiz_welcome", "Wähle deine Themen und starte eine Runde."
            ),
            wraplength=620,
            justify="left",
        )
        self.prompt_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.choice = tk.IntVar(self, value=-1)
        self.option_buttons = []
        for row in range(4):
            button = tk.Radiobutton(
                question_body,
                variable=self.choice,
                value=row,
                text="",
                state="disabled",
                wraplength=590,
                anchor="w",
                justify="left",
                borderwidth=0,
            )
            button.grid(row=row + 1, column=0, sticky="ew", pady=4)
            self.option_buttons.append(button)
        self.feedback_label = ttk.Label(
            question_body, text="", wraplength=620, justify="left"
        )
        self.feedback_label.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        for widget in [
            self.question_canvas,
            question_body,
            self.prompt_label,
            self.feedback_label,
            *self.option_buttons,
        ]:
            widget.bind(
                "<Button-4>",
                lambda _event: self.question_canvas.yview_scroll(-1, "units"),
            )
            widget.bind(
                "<Button-5>",
                lambda _event: self.question_canvas.yview_scroll(1, "units"),
            )
        answer_row = ttk.Frame(self.quiz_tab)
        answer_row.grid(row=4, column=0, sticky="ew")
        self.answer_button = ttk.Button(
            answer_row,
            text=self.tr("linux_help_quiz_check_answer", "Antwort prüfen"),
            command=self.answer,
            state="disabled",
        )
        self.answer_button.pack(side="left")
        self.unknown_button = ttk.Button(
            answer_row,
            text=self.tr("linux_help_quiz_unknown", "Weiß ich nicht"),
            command=lambda: self.answer(unknown=True),
            state="disabled",
        )
        self.unknown_button.pack(side="left", padx=8)
        self.next_button = ttk.Button(
            answer_row,
            text=self.tr("linux_help_quiz_next", "Weiter"),
            command=self.next_question,
            state="disabled",
        )
        self.next_button.pack(side="right")
        self.reader_button = ttk.Button(
            self.quiz_tab,
            text=self.tr("linux_help_quiz_open_reader", "Im Reader nachlesen"),
            command=self.open_reader,
            state="disabled",
        )
        self.reader_button.grid(row=5, column=0, sticky="w", pady=(10, 0))

    def _build_stats(self):
        self.stats_tab.rowconfigure(0, weight=1)
        self.stats_text = tk.Text(
            self.stats_tab,
            wrap="word",
            state="disabled",
            width=45,
            height=20,
            relief="flat",
        )
        self.stats_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            self.stats_tab, orient="vertical", command=self.stats_text.yview
        )
        scroll.grid(row=0, column=1, sticky="ns")
        self.stats_text.configure(yscrollcommand=scroll.set)
        ttk.Button(
            self.stats_tab,
            text=self.tr("linux_help_quiz_repeat_errors", "Fehler wiederholen"),
            command=self.repeat_errors,
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

    def _build_settings(self):
        saved = self.state.data["settings"]
        self.auto_enabled = tk.BooleanVar(self, value=saved["enabled"])
        self.auto_minutes = tk.StringVar(self, value=str(saved["minutes"]))
        self.auto_count = tk.StringVar(self, value=str(saved["count"]))
        self.auto_kind = tk.StringVar(self, value=self.kind_labels[saved["kind"]])
        ttk.Checkbutton(
            self.settings_tab,
            text=self.tr("linux_help_quiz_automatic", "Automatische Lernrunden"),
            variable=self.auto_enabled,
        ).grid(row=0, column=0, sticky="w", pady=8)
        form = ttk.Frame(self.settings_tab)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        for row, (label, variable, low, high) in enumerate(
            (
                (
                    self.tr("linux_help_quiz_interval", "Alle (Minuten)"),
                    self.auto_minutes,
                    1,
                    1440,
                ),
                (
                    self.tr("linux_help_quiz_round_size", "Fragen je Runde"),
                    self.auto_count,
                    1,
                    30,
                ),
            )
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Spinbox(form, from_=low, to=high, textvariable=variable, width=8).grid(
                row=row, column=1, sticky="w", padx=10, pady=6
            )
        ttk.Label(form, text=self.tr("linux_help_quiz_topics", "Themen")).grid(
            row=2, column=0, sticky="w", pady=6
        )
        ttk.Combobox(
            form,
            textvariable=self.auto_kind,
            values=list(self.kind_ids),
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=10, pady=6)
        ttk.Label(
            self.settings_tab,
            text=(
                self.tr(
                    "linux_help_quiz_settings_help",
                    "Lernrunden erscheinen, solange NetMon läuft. Nach einem Neustart beginnt das Intervall neu. Während anderer Dialoge wird die Erinnerung verschoben.\n\nDas Quiz führt keine Befehle aus. Lesestatus und Lernergebnisse werden getrennt gespeichert. Einstellungen und Ergebnisse liegen lokal unter LinuxHelp/quiz.json und werden mit diesem Ordner gesichert.\n\nVorgaben: 60 Minuten und 5 Fragen. Die Automatik ist zunächst ausgeschaltet.",
                )
            ),
            wraplength=590,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=18)
        ttk.Button(
            self.settings_tab,
            text=self.tr("linux_help_quiz_save_settings", "Einstellungen speichern"),
            command=self.save_settings,
        ).grid(row=3, column=0, sticky="w")

    def _entries(self):
        return [
            *(vars(self.owner).get("linux_help_data") or []),
            *(vars(self.owner).get("linux_help_glossary") or []),
        ]

    def refresh_bank(self):
        try:
            self.bank = load_questions()
            self.pool, self.suspended = available_questions(
                self.bank, self._entries(), reader.load_entry_document
            )
            categories = sorted(
                {item.get("category", q.category) for q, item in self.pool}
            )
            self.category_combo.configure(values=[self.all_categories, *categories])
            self.status.set(
                self.tr(
                    "linux_help_quiz_bank_summary",
                    "{available} geprüfte Fragen verfügbar · {suspended} ausgesetzt / erneut zu prüfen.",
                ).format(available=len(self.pool), suspended=len(self.suspended))
            )
            return True
        except (OSError, ValueError, UnicodeError, RecursionError) as error:
            self.bank, self.pool, self.suspended = [], [], []
            self.status.set(
                self.tr(
                    "linux_help_quiz_bank_failed",
                    "Fragen konnten nicht geladen werden: {error}",
                ).format(error=error)
            )
            return False

    def _locked(self, locked):
        for widget in [self.start_button, self.errors_button, *self.form_widgets]:
            widget.configure(
                state=(
                    "disabled"
                    if locked
                    else ("readonly" if isinstance(widget, ttk.Combobox) else "normal")
                )
            )

    def start(self, *, errors_only=False):
        if self.round_id is not None:
            self.status.set(
                self.tr(
                    "linux_help_quiz_round_already_running",
                    "Beende zuerst die laufende Runde.",
                )
            )
            return False
        if not self.state.reload():
            self.status.set(self.state.error)
            return False
        if not self.refresh_bank():
            return False
        try:
            count = int(self.count.get())
            if not 1 <= count <= 30:
                raise ValueError(
                    self.tr(
                        "linux_help_quiz_question_count_range",
                        "Bitte 1–30 Fragen wählen.",
                    )
                )
            selected = choose_questions(
                self.pool,
                self.state.data["progress"],
                count,
                kind=self.kind_ids[self.kind.get()],
                category=(
                    ""
                    if self.category.get() == self.all_categories
                    else self.category.get()
                ),
                read=(
                    (lambda item: reader._reading_state(self.owner).get(item)["read"])
                    if self.read_only.get()
                    else None
                ),
                errors_only=errors_only,
            )
            if not selected:
                self.status.set(
                    self.tr(
                        "linux_help_quiz_no_questions",
                        "Keine passenden Fragen. Prüfe die Filter; möglicherweise gibt es keine aktuellen Fehler.",
                    )
                )
                return False
            self.round_id = self.state.start_round(len(selected))
        except (OSError, ValueError, KeyError) as error:
            self.status.set(
                self.tr(
                    "linux_help_quiz_start_failed",
                    "Runde konnte nicht gestartet werden: {error}",
                ).format(error=error)
            )
            return False
        self.questions, self.index = selected, 0
        self._locked(True)
        self.tabs.select(self.quiz_tab)
        self.show_question()
        return True

    def show_question(self):
        q, _item = self.questions[self.index]
        self.choice.set(-1)
        self.answered = False
        self.round_status.set(
            self.tr(
                "linux_help_quiz_question_progress",
                "Frage {number} von {total} · {name}",
            ).format(number=self.index + 1, total=len(self.questions), name=q.name)
        )
        self.prompt_label.configure(text=q.prompt)
        order = list(range(4))
        random.SystemRandom().shuffle(order)
        for button, option in zip(self.option_buttons, order):
            button.configure(text=q.options[option], value=option, state="normal")
        self.feedback_label.configure(text="")
        self.question_canvas.yview_moveto(0)
        self.answer_button.configure(state="normal")
        self.unknown_button.configure(state="normal")
        self.reader_button.configure(state="normal")
        self.next_button.configure(
            state="disabled",
            text=(
                self.tr("linux_help_quiz_results", "Auswertung")
                if self.index == len(self.questions) - 1
                else self.tr("linux_help_quiz_next", "Weiter")
            ),
        )

    def answer(self, *, unknown=False):
        if self.round_id is None or self.answered:
            return False
        choice = None if unknown else self.choice.get()
        if choice == -1:
            self.status.set(
                self.tr(
                    "linux_help_quiz_answer_required",
                    "Bitte eine Antwort auswählen oder „Weiß ich nicht“ wählen.",
                )
            )
            return False
        q, item = self.questions[self.index]
        active, _suspended = available_questions(
            [q], self._entries(), reader.load_entry_document
        )
        if not active:
            self.status.set(
                self.tr(
                    "linux_help_quiz_source_changed",
                    "Die Dokumentation wurde verändert. Diese Runde bitte schließen und neu starten.",
                )
            )
            return False
        try:
            correct = self.state.record_answer(self.round_id, self.index, q, choice)
        except (OSError, ValueError, UnicodeError, RecursionError) as error:
            self.status.set(
                self.tr(
                    "linux_help_quiz_answer_failed",
                    "Antwort nicht gespeichert: {error}",
                ).format(error=error)
            )
            return False
        self.answered = True
        outcome = (
            self.tr("linux_help_quiz_correct", "Richtig!")
            if correct
            else (
                self.tr("linux_help_quiz_not_known", "Noch nicht gewusst.")
                if unknown
                else self.tr("linux_help_quiz_incorrect", "Leider falsch.")
            )
        )
        self.feedback_label.configure(
            text=self.tr(
                "linux_help_quiz_answer_feedback",
                "{outcome}\nRichtige Antwort: {answer}\n\n{explanation}",
            ).format(
                outcome=outcome, answer=q.options[q.answer], explanation=q.explanation
            )
        )
        for button in [*self.option_buttons, self.answer_button, self.unknown_button]:
            button.configure(state="disabled")
        self.next_button.configure(state="normal")
        self.status.set(
            self.tr(
                "linux_help_quiz_answer_saved",
                "Antwort gespeichert. Du kannst nachlesen oder weitergehen.",
            )
        )
        self.update_idletasks()
        self.question_canvas.yview_moveto(1)
        self.refresh_stats()
        return True

    def next_question(self):
        if self.round_id is None or not self.answered:
            return
        self.index += 1
        if self.index < len(self.questions):
            self.show_question()
            return
        session = next(r for r in self.state.data["rounds"] if r["id"] == self.round_id)
        self.round_status.set(
            self.tr(
                "linux_help_quiz_round_summary", "Runde abgeschlossen · {score}"
            ).format(score=self._summary([session["answered"], session["correct"]]))
        )
        self.round_id = None
        self.reader_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self._locked(False)
        self.refresh_stats()
        self.tabs.select(self.stats_tab)

    def open_reader(self):
        if self.round_id is not None:
            reader.open_linux_help_reader(
                self.owner, command_id=self.questions[self.index][0].entry_id
            )

    def repeat_errors(self):
        self.tabs.select(self.quiz_tab)
        self.start(errors_only=True)

    def refresh_stats(self):
        if not self.state.reload():
            self.status.set(self.state.error)
        lines = []
        for week, heading in (
            (False, self.tr("linux_help_quiz_stats_total", "Gesamt")),
            (
                True,
                self.tr(
                    "linux_help_quiz_stats_last_week",
                    "Letzte sieben Kalendertage (einschließlich heute)",
                ),
            ),
        ):
            stats = self.state.statistics(week=week)
            lines.extend(
                [
                    heading,
                    self._summary(stats["total"]),
                    self.tr(
                        "linux_help_quiz_stats_commands", "Befehle: {score}"
                    ).format(score=self._summary(stats["command"])),
                    self.tr(
                        "linux_help_quiz_stats_glossary", "Glossar: {score}"
                    ).format(score=self._summary(stats["glossary"])),
                ]
            )
            if not week:
                lines.append(
                    self.tr(
                        "linux_help_quiz_stats_distinct",
                        "Verschiedene geübte Einträge: {count}",
                    ).format(count=stats["distinct"])
                )
            for category, pair in sorted(stats["categories"].items()):
                lines.append(f"  {category}: {self._summary(pair)}")
            lines.append("")
        progress = self.state.data["progress"]
        errors = sorted(
            (
                q
                for q, _item in self.pool
                if q.id in progress
                and progress[q.id][0] == q.revision
                and progress[q.id][6]
            ),
            key=lambda q: progress[q.id][4] - progress[q.id][5],
            reverse=True,
        )
        lines.append(
            self.tr(
                "linux_help_quiz_stats_errors", "Aktuelle Fehler (häufigste zuerst)"
            )
        )
        lines.extend(
            self.tr(
                "linux_help_quiz_stats_misses", "  {name}: {count} Fehlversuche"
            ).format(name=q.name, count=progress[q.id][4] - progress[q.id][5])
            for q in errors
        )
        if not errors:
            lines.append(
                self.tr("linux_help_quiz_stats_no_errors", "  Keine aktuellen Fehler.")
            )
        lines.extend(
            [
                "",
                self.tr(
                    "linux_help_quiz_stats_recent_rounds", "Letzte Runden (maximal 30)"
                ),
            ]
        )
        for session in reversed(self.state.data["rounds"]):
            label = (
                self.tr("linux_help_quiz_round_complete", "abgeschlossen")
                if session["complete"]
                else self.tr("linux_help_quiz_round_incomplete", "nicht abgeschlossen")
            )
            lines.append(
                f"  {session['started'][:16].replace('T', ' ')} · {label}\n"
                f"  {self._summary([session['answered'], session['correct']])}"
            )
        if self.suspended:
            lines.extend(
                [
                    "",
                    self.tr(
                        "linux_help_quiz_stats_suspended",
                        "Ausgesetzte Fragen – erneute Prüfung erforderlich",
                    ),
                ]
            )
            lines.extend(f"  {q.name}: {reason}" for q, reason in self.suspended)
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", "\n".join(lines))
        self.stats_text.configure(state="disabled")

    def _tab_changed(self, _event):
        if self.tabs.select() == str(self.stats_tab):
            self.refresh_bank()
            self.refresh_stats()

    def save_settings(self):
        try:
            self.state.save_settings(
                {
                    "enabled": self.auto_enabled.get(),
                    "minutes": int(self.auto_minutes.get()),
                    "count": int(self.auto_count.get()),
                    "kind": self.kind_ids[self.auto_kind.get()],
                }
            )
        except (OSError, ValueError, KeyError, UnicodeError, RecursionError) as error:
            self.status.set(
                self.tr(
                    "linux_help_quiz_settings_failed",
                    "Einstellungen nicht gespeichert: {error}",
                ).format(error=error)
            )
            return False
        scheduler = vars(self.owner).get("linux_help_quiz_scheduler")
        if scheduler is not None:
            scheduler.reset()
        self._snooze_state()
        self.status.set(
            self.tr(
                "linux_help_quiz_settings_saved",
                "Einstellungen gespeichert. Das Intervall beginnt jetzt neu.",
            )
        )
        return True

    def _snooze_state(self):
        self.snooze_button.configure(
            state=("normal" if self.state.data["settings"]["enabled"] else "disabled")
        )

    def snooze(self):
        if self.state.data["settings"]["enabled"]:
            self.close(snooze=True)

    def close(self, *, snooze=False):
        if self.round_id is not None:
            session = next(
                (r for r in self.state.data["rounds"] if r["id"] == self.round_id), None
            )
            if session and not session["complete"]:
                if not (
                    self.automatic and session["answered"] == 0
                ) and not messagebox.askyesno(
                    self.tr("linux_help_quiz_close_title", "Lernrunde beenden?"),
                    self.tr(
                        "linux_help_quiz_close_message",
                        "Die Runde ist noch nicht fertig. Bisherige Antworten bleiben gespeichert.\nRunde beenden?",
                    ),
                    parent=self,
                ):
                    return False
                try:
                    self.state.end_round(self.round_id)
                except (OSError, ValueError) as error:
                    self.status.set(
                        self.tr(
                            "linux_help_quiz_close_failed",
                            "Runde konnte nicht beendet werden: {error}",
                        ).format(error=error)
                    )
                    return False
        self.owner.linux_help_quiz_window = None
        scheduler = vars(self.owner).get("linux_help_quiz_scheduler")
        if scheduler is not None:
            scheduler.reset(minutes=10 if snooze else None)
        self.destroy()
        return True
