"""Settings variable synchronization helpers."""

from __future__ import annotations


def app_var_value(app, name: str, default):
    """Return a Tk variable value, falling back when the variable is absent or broken."""
    var = getattr(app, "__dict__", {}).get(name)
    if var is None:
        return default
    try:
        return var.get()
    except Exception:
        return default


def sync_app_vars_from_mapping(app, mapping: dict) -> None:
    """Apply values to existing Tk variables, ignoring absent or broken variables."""
    app_dict = getattr(app, "__dict__", {})
    for attr_name, value in mapping.items():
        var = app_dict.get(attr_name)
        if var is None:
            continue
        try:
            var.set(value)
        except Exception:
            pass
