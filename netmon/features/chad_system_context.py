"""Explicit, bounded snapshots of already displayed tab data, without scans."""

from datetime import datetime

from netmon.services.ai_analysis_service import AiAnalysisService

MAX_SECTION_CHARS = 4000
MAX_CONTEXT_CHARS = 80000
MAX_TABLE_ROWS = 60
VARIABLE_LABELS = {
    "system_cpu_var": "CPU",
    "system_ram_var": "RAM",
    "system_swap_var": "Swap",
    "system_disk_var": "Dateisystembelegung",
    "system_temp_var": "CPU-Temperatur",
    "system_gpu_temp_var": "GPU-Temperatur",
    "vpn_status_text_var": "VPN-Status",
    "speedtest_ping_var": "Ping",
    "speedtest_jitter_var": "Jitter",
    "speedtest_download_var": "Download",
    "speedtest_upload_var": "Upload",
    "speedtest_timestamp_var": "Messzeitpunkt",
}

# Explicit sources only: no chat history, credentials/settings or terminal buffers.
SOURCES = (
    (
        "Systemressourcen",
        tuple(
            ("variable", name)
            for name in (
                "system_cpu_var",
                "system_ram_var",
                "system_swap_var",
                "system_disk_var",
                "system_temp_var",
                "system_gpu_temp_var",
            )
        ),
    ),
    ("DNS", (("text", "dns_text"),)),
    ("VPN / WireGuard", (("variable", "vpn_status_text_var"),)),
    ("Verbindungen", (("tree", "conn_table"),)),
    ("Routing / ARP", (("tree", "route_table"), ("tree", "arp_table"))),
    (
        "Firewall",
        (("tree", "firewall_rules_table"), ("tree", "firewall_listeners_table")),
    ),
    ("Security", (("tree", "security_table"), ("text", "security_detail"))),
    (
        "Process Guard",
        (("tree", "process_guard_tree"), ("text", "process_guard_detail")),
    ),
    (
        "Startup Guard",
        (("tree", "startup_guard_tree"), ("text", "startup_guard_details_text")),
    ),
    ("PATH Guard", (("text", "path_guard_detail"),)),
    (
        "Roots Baseline Guard",
        (
            ("tree", "roots_baseline_guard_results_table"),
            ("text", "roots_baseline_guard_info_text"),
        ),
    ),
    (
        "Repository Guard",
        (
            ("tree", "repository_guard_findings_tree"),
            ("text", "repository_guard_detail_text"),
        ),
    ),
    ("Lynis", (("text", "lynis_text"),)),
    ("rkhunter", (("text", "rkhunter_text"),)),
    ("ClamAV", (("text", "clamav_output_text"),)),
    (
        "Geräte / Eingabezugriffe",
        (("tree", "security_devices_table"), ("tree", "input_access_table")),
    ),
    ("Nmap", (("text", "nmap_text"),)),
    ("MTR", (("text", "mtr_text"),)),
    ("Traceroute", (("tree", "trace_table"), ("text", "trace_text"))),
    (
        "Speedtest",
        tuple(
            ("variable", name)
            for name in (
                "speedtest_ping_var",
                "speedtest_jitter_var",
                "speedtest_download_var",
                "speedtest_upload_var",
                "speedtest_timestamp_var",
            )
        ),
    ),
    ("iftop", (("text", "iftop_text"),)),
    ("htop", (("tree", "htop_table"), ("text", "htop_text"))),
    ("Packet Capture", (("text", "packet_capture_text"),)),
    ("HDD / Dateisystem", (("text", "hdd_info_text"),)),
    ("NetMon Log", (("text", "text"),)),
)


def _read_source(widget, kind):
    if kind == "text":
        # Bound before asking Tk to allocate a Python copy; incomplete PEM is
        # also redacted by the shared filter before any further truncation.
        return str(widget.get("1.0", f"1.0+{MAX_SECTION_CHARS + 1}c"))
    if kind == "variable":
        return str(widget.get())[: MAX_SECTION_CHARS + 1]
    rows = widget.get_children("")
    try:
        columns = widget.cget("columns")
        names = [str(widget.heading(column, "text")) for column in columns]
        lines = ["Spalten: Eintrag, " + ", ".join(names)]
    except (AttributeError, TypeError):
        lines = ["Zeilen: Beschriftung und Spaltenwerte"]
    length = 0
    for row in rows[:MAX_TABLE_ROWS]:
        label = widget.item(row, "text")
        values = widget.item(row, "values")
        line = f"{label}: {values}"
        lines.append(line)
        length += len(line)
        if length > MAX_SECTION_CHARS:
            break
    if len(rows) > len(lines) - 1:
        lines.append("[Tabelle gekürzt; weitere Zeilen nicht aufgenommen.]")
    return "\n".join(lines)


def collect_system_context(app):
    """Read only existing UI snapshots; never refresh, scan or enumerate the host."""
    sanitizer = AiAnalysisService()
    sections = [
        "=== NetMon Gesamtcheck: vorhandener Tab-Kontext ===",
        f'Zusammenstellung: {datetime.now().astimezone().isoformat(timespec="seconds")}',
        "Kein neuer Systemscan. Die Aktualität richtet sich nach den einzelnen Anzeigen. "
        "Fehlende, alte oder unvollständige Daten sind keine Entwarnung.",
    ]
    used = sum(len(part) + 2 for part in sections)
    for position, (label, sources) in enumerate(SOURCES):
        parts = []
        available = False
        for kind, attribute in sources:
            widget = app.__dict__.get(attribute)
            if widget is None:
                continue
            available = True
            try:
                data = sanitizer.sanitize_content(_read_source(widget, kind)).strip()
            except Exception:
                parts.append("Anzeige nicht lesbar; für die Bewertung nicht verfügbar.")
                continue
            if data:
                parts.append(
                    f"{VARIABLE_LABELS[attribute]}: {data}"
                    if kind == "variable"
                    else data
                )
        if not available:
            data = "Tab-Daten nicht geladen oder nicht vorhanden; nicht geprüft."
        else:
            data = "\n".join(parts) or "Keine auswertbaren Anzeigedaten; nicht geprüft."
        if len(data) > MAX_SECTION_CHARS:
            data = data[:MAX_SECTION_CHARS] + "\n[Auszug gekürzt.]"
        section = f"--- {label} ---\n{data}"
        if used + len(section) + 1200 > MAX_CONTEXT_CHARS:
            sections.append(
                "[Gesamtlimit erreicht; nicht aufgenommen: "
                + ", ".join(name for name, _ in SOURCES[position:])
                + "]"
            )
            break
        sections.append(section)
        used += len(section) + 2
    return "\n\n".join(sections)


def prepare_system_prompt(app):
    from netmon.features import chad_controller

    # Local preparation only. Browser/API transport retains its existing
    # explicit action/confirmation and final shared redaction boundary.
    chad_controller.prepare_chad_analysis(
        app, "NetMon Gesamtcheck", collect_system_context(app)
    )
