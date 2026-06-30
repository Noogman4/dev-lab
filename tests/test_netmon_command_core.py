from netmon.core import command


class DummyParent:
    def winfo_exists(self):
        raise RuntimeError("application has been destroyed")


class DummyMessagebox:
    def __init__(self):
        self.calls = []

    def showerror(self, title, message, **kwargs):
        self.calls.append((title, message, kwargs))
        return "ok"


def test_safe_messagebox_showerror_skips_destroyed_parent():
    messagebox = DummyMessagebox()

    ok = command._safe_messagebox_showerror(
        messagebox,
        "Sudo Passwort",
        "Passwort ungültig oder sudo-Rechte fehlen.",
        parent=DummyParent(),
    )

    assert ok is True
    assert messagebox.calls == [
        ("Sudo Passwort", "Passwort ungültig oder sudo-Rechte fehlen.", {})
    ]


def test_safe_messagebox_showerror_tolerates_dialog_failure():
    class FailingMessagebox:
        def showerror(self, title, message, **kwargs):
            raise RuntimeError("grab failed")

    ok = command._safe_messagebox_showerror(
        FailingMessagebox(),
        "Sudo Passwort",
        "Passwort ungültig oder sudo-Rechte fehlen.",
        parent=DummyParent(),
    )

    assert ok is False
