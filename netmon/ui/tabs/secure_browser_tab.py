"""Secure Browser tab builder for NetMon."""

from __future__ import annotations

from netmon.modules.secure_browser.manager import SecureBrowserManager
from netmon.modules.secure_browser.ui import create_secure_browser_tab


def build_secure_browser_tab(app):
    app.secure_browser_manager = SecureBrowserManager(tr=app.tr)
    app.tab_secure_browser = create_secure_browser_tab(
        app.nb,
        app.secure_browser_manager,
        tr=app.tr,
        title=app.tr("secure_browser_title", "NetMon Secure Browser"),
    )
    app.nb.add(
        app.tab_secure_browser,
        text=app.tr("tab_secure_browser", "🌐 Secure Browser"),
    )
