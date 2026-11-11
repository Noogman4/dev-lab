"""Exercise the real indicator and observer with simulated profile mutations."""

import tkinter as tk

import pytest

from netmon.features import dns_controller
from netmon.services.dns_control_service import DNSControlService
from tests.test_netmon_dns_consistency import DummyVar
from tools import netmon


@pytest.fixture
def app(tmp_path):
    instance = netmon.App.__new__(netmon.App)
    instance.events = []
    instance.dns_guard_enabled_var = DummyVar(True)
    instance.dns_guard_state = "ok"
    instance.dns_guard_transition_until = 0
    instance.dns_guard_indicator = object()
    instance.set_light = lambda _light, color: instance.events.append(("light", color))
    instance.log_safe = lambda text: None
    instance.log_debug_safe = lambda text: instance.events.append(("error", text))
    instance.update_idletasks = lambda: instance.events.append(
        ("paint", instance.get_dns_guard_status())
    )
    instance.is_vpn_active = lambda: False
    instance.get_selected_user_dns = lambda: ["8.8.8.8", "8.8.4.4"]
    instance.status_text = "Global\n    DNS Servers: 8.8.8.8 8.8.4.4\n"
    service = DNSControlService(
        lambda *args, **kwargs: pytest.fail("No real command allowed"),
        lambda _: False,
        dot_dropin_path=str(tmp_path / "absent.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    service.get_wireguard_interfaces = lambda: set()

    def snapshot():
        instance.events.append(("read", instance.get_dns_guard_status()))
        return service.parse_dns_snapshot(instance.status_text)

    service.read_dns_snapshot = snapshot
    instance._dns_control_service = lambda: service
    return instance


def install_operation(monkeypatch, app, *, success=True, exception=False):
    def operation(current, choice, *, manual=False):
        assert current is app and manual
        assert app.get_dns_guard_status() == "transition"
        assert ("paint", "transition") in app.events
        assert not app._dns_runtime_transition_active()
        app.events.append(("mutate", choice))
        # A periodic/automatic check during this change must not read or repair.
        before = list(app.events)
        app.run_dns_guard_check_once(auto_repair=True)
        assert [
            event for event in app.events[len(before) :] if event[0] == "read"
        ] == []
        if exception:
            raise KeyboardInterrupt("simulated cancellation")
        return {"success": success}

    monkeypatch.setattr(
        dns_controller, "_apply_dns_profile_choice_via_control_locked", operation
    )


def test_success_paints_yellow_then_fresh_read_can_turn_green(monkeypatch, app):
    install_operation(monkeypatch, app)
    result = dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )
    assert result["success"]
    assert app.get_dns_guard_status() == "ok"
    assert app.events.index(("paint", "transition")) < app.events.index(
        ("mutate", "Google (8.8.8.8)")
    )
    assert app.events.index(("read", "unknown")) < app.events.index(("light", "green"))
    assert not app._manual_dns_guard_running


@pytest.mark.parametrize("outcome", ["failure", "abort"])
def test_failure_and_abort_never_keep_old_green(monkeypatch, app, outcome):
    install_operation(monkeypatch, app, success=False, exception=outcome == "abort")
    if outcome == "abort":
        with pytest.raises(KeyboardInterrupt):
            dns_controller.apply_dns_profile_choice_via_control(
                app, "Google (8.8.8.8)", manual=True
            )
    else:
        assert not dns_controller.apply_dns_profile_choice_via_control(
            app, "Google (8.8.8.8)", manual=True
        )["success"]
    assert not app._manual_dns_guard_running
    assert app.get_dns_guard_status() == "unknown"
    assert ("light", "green") not in app.events
    # An independent subsequent check can correctly report an actual mismatch.
    app.status_text = "Global\n    DNS Servers: 1.1.1.1\n"
    app.run_dns_guard_check_once()
    assert app.get_dns_guard_status() == "problem"
    assert app.events[-1] == ("light", "red")


@pytest.mark.parametrize("status", ["Global\n    DNS Servers: 1.1.1.1\n", ""])
def test_successful_commands_do_not_override_problem_or_unknown(
    monkeypatch, app, status
):
    install_operation(monkeypatch, app)
    app.status_text = status
    dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )
    assert app.get_dns_guard_status() == ("problem" if status else "unknown")
    assert ("light", "green") not in app.events


def test_stale_observer_cannot_publish_green_after_new_change(monkeypatch, app):
    install_operation(monkeypatch, app)
    service = app._dns_control_service()
    fresh_read = service.read_dns_snapshot

    def overlapping_read():
        service.read_dns_snapshot = fresh_read
        old_snapshot = fresh_read()
        dns_controller.apply_dns_profile_choice_via_control(
            app, "Google (8.8.8.8)", manual=True
        )
        return old_snapshot

    service.read_dns_snapshot = overlapping_read
    app.run_dns_guard_check_once()
    assert app.get_dns_guard_status() == "unknown"
    assert ("light", "green") not in app.events
    app.run_dns_guard_check_once()
    assert app.get_dns_guard_status() == "ok"


def test_disabled_guard_stays_gray(monkeypatch, app):
    app.dns_guard_enabled_var.set(False)
    monkeypatch.setattr(
        dns_controller,
        "_apply_dns_profile_choice_via_control_locked",
        lambda *args, **kwargs: {"success": True},
    )
    dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )
    assert app.get_dns_guard_status() == "off"
    assert all(event[1] == "gray" for event in app.events if event[0] == "light")


def test_reentrant_manual_apply_is_rejected(monkeypatch, app):
    calls = []

    def operation(*args, **kwargs):
        calls.append(True)
        nested = dns_controller.apply_dns_profile_choice_via_control(
            app, "Google (8.8.8.8)", manual=True
        )
        assert not nested["success"]
        return {"success": True}

    monkeypatch.setattr(
        dns_controller, "_apply_dns_profile_choice_via_control_locked", operation
    )
    dns_controller.apply_dns_profile_choice_via_control(
        app, "Google (8.8.8.8)", manual=True
    )
    assert calls == [True]


def test_real_tk_repaints_yellow_before_simulated_mutation(monkeypatch, app):
    root = tk.Tk()
    try:
        label = tk.Label(root, text="DNS Guard", background="green")
        label.pack()
        root.update_idletasks()
        app.update_idletasks = root.update_idletasks
        app.set_light = lambda _light, color: label.configure(background=color)

        def operation(*args, **kwargs):
            assert label.winfo_ismapped()
            assert label.cget("background") == "yellow"
            assert app.get_dns_guard_status() == "transition"
            return {"success": True}

        monkeypatch.setattr(
            dns_controller, "_apply_dns_profile_choice_via_control_locked", operation
        )
        dns_controller.apply_dns_profile_choice_via_control(
            app, "Google (8.8.8.8)", manual=True
        )
        assert label.cget("background") == "green"
    finally:
        root.destroy()
