"""Native speedtest helpers for NetMon."""

from __future__ import annotations

import json
import re
from datetime import datetime


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value):
    text = str(value or "").strip()
    return text or ""


def normalize_speedtest_server_id(value):
    text = _clean_text(value)
    if text.isdigit():
        return text

    match = re.search(
        r"(?:^|\]\s*)(?:server[- ]?id|id)\s*[:#-]?\s*(\d+)" r"(?=\s*(?:$|\||\n))",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1) if match else ""


def _extract_json_payload(payload):
    text = (payload or "").strip()
    if not text:
        return ""

    # Best effort: speedtest tools may print notices before or after JSON.
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return text
    return text[first : last + 1]


def _parse_json_candidates(payload):
    text = (payload or "").strip()
    if not text:
        raise ValueError("empty output")

    candidates = []
    candidates.append(text)

    extracted = _extract_json_payload(text)
    if extracted and extracted not in candidates:
        candidates.append(extracted)

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}") and line not in candidates:
            candidates.append(line)

    last_error = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception as exc:
            last_error = exc
    raise last_error or ValueError("no JSON payload found")


def _parse_speedtest_result_payload(payload, tool_hint):
    data = _parse_json_candidates(payload)

    server_data = data.get("server") if isinstance(data.get("server"), dict) else {}
    server_id = _clean_text(server_data.get("id"))
    server_name = _clean_text(server_data.get("name"))
    server_host = _clean_text(server_data.get("host"))
    server_sponsor = _clean_text(server_data.get("sponsor"))

    if isinstance(data.get("download"), dict):
        # Ookla CLI: bandwidth in bytes/sec, ping object includes latency+jitter.
        ping_ms = _to_float((data.get("ping") or {}).get("latency"))
        jitter_ms = _to_float((data.get("ping") or {}).get("jitter"))
        download_bw = _to_float((data.get("download") or {}).get("bandwidth"), 0.0)
        upload_bw = _to_float((data.get("upload") or {}).get("bandwidth"), 0.0)
        return {
            "event": "speedtest",
            "ping_ms": ping_ms,
            "jitter_ms": jitter_ms,
            "download_mbps": max(0.0, (download_bw * 8.0) / 1_000_000.0),
            "upload_mbps": max(0.0, (upload_bw * 8.0) / 1_000_000.0),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tool": tool_hint,
            "server_id": server_id,
            "server_name": server_name,
            "server_host": server_host,
            "server_sponsor": server_sponsor,
        }

    # speedtest-cli style: download/upload in bits/sec; jitter may be missing.
    ping_ms = _to_float(data.get("ping"))
    jitter_ms = _to_float(data.get("jitter"))
    download_bits = _to_float(data.get("download"), 0.0)
    upload_bits = _to_float(data.get("upload"), 0.0)
    return {
        "event": "speedtest",
        "ping_ms": ping_ms,
        "jitter_ms": jitter_ms,
        "download_mbps": max(0.0, download_bits / 1_000_000.0),
        "upload_mbps": max(0.0, upload_bits / 1_000_000.0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool_hint,
        "server_id": server_id,
        "server_name": server_name,
        "server_host": server_host,
        "server_sponsor": server_sponsor,
    }


def _run_and_parse(run_cmd_fn, cmd, timeout, tool_hint):
    rc, out = run_cmd_fn(cmd, timeout=timeout)
    if rc != 0:
        return None, out or f"{' '.join(cmd)} failed"
    if not (out or "").strip():
        return None, f"{' '.join(cmd)} returned no output"
    try:
        return _parse_speedtest_result_payload(out, tool_hint=tool_hint), None
    except Exception as exc:
        return None, f"{' '.join(cmd)}: JSON konnte nicht gelesen werden: {exc}"


def _speedtest_server_record(item):
    if not isinstance(item, dict):
        return None
    server_id = _clean_text(item.get("id"))
    if not server_id or not server_id.isdigit():
        return None
    return {
        "id": server_id,
        "name": _clean_text(item.get("name"))
        or _clean_text(item.get("sponsor"))
        or _clean_text(item.get("host")),
        "location": _clean_text(item.get("location")) or _clean_text(item.get("city")),
        "country": _clean_text(item.get("country")),
        "distance": _clean_text(item.get("distance")),
        "host": _clean_text(item.get("host")),
    }


def _parse_speedtest_server_json(payload):
    try:
        data = _parse_json_candidates(payload)
    except Exception:
        return []
    if isinstance(data, dict):
        items = data.get("servers", [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    return [record for item in items if (record := _speedtest_server_record(item))]


def _split_server_place(value):
    place = _clean_text(value)
    if "," not in place:
        return place, ""
    location, country = place.rsplit(",", 1)
    return location.strip(), country.strip()


def _parse_speedtest_server_text(payload):
    servers = []
    for raw_line in str(payload or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # speedtest-cli: 12345) Sponsor (City, Country) [12.34 km]
        legacy = re.match(
            r"^(\d+)\)\s+(.+)\s+\(([^()]*)\)\s+\[([^]]+)\]\s*$",
            line,
        )
        if legacy:
            location, country = _split_server_place(legacy.group(3))
            servers.append(
                {
                    "id": legacy.group(1),
                    "name": legacy.group(2).strip(),
                    "location": location,
                    "country": country,
                    "distance": legacy.group(4).strip(),
                    "host": "",
                }
            )
            continue

        # Ookla CLI table: ID  Name  Location  Country (columns use spacing).
        columns = re.split(r"\s{2,}", line)
        if len(columns) >= 3 and columns[0].isdigit():
            servers.append(
                {
                    "id": columns[0],
                    "name": columns[1],
                    "location": columns[2],
                    "country": columns[3] if len(columns) >= 4 else "",
                    "distance": columns[4] if len(columns) >= 5 else "",
                    "host": "",
                }
            )
    return servers


def parse_speedtest_servers(payload):
    """Parse Ookla or speedtest-cli server output into normalized records."""

    servers = _parse_speedtest_server_json(payload)
    if not servers:
        servers = _parse_speedtest_server_text(payload)

    unique = []
    seen = set()
    for server in servers:
        server_id = server.get("id", "")
        if not server_id or server_id in seen:
            continue
        seen.add(server_id)
        unique.append(server)
    return unique


def list_speedtest_servers(run_cmd_fn, has_cmd_fn, timeout=60, limit=20):
    """Return nearby speedtest servers from an installed supported CLI."""

    candidates = []
    if callable(has_cmd_fn) and has_cmd_fn("speedtest"):
        candidates.extend(
            [
                [
                    "speedtest",
                    "--accept-license",
                    "--accept-gdpr",
                    "--servers",
                    "--format=json",
                ],
                ["speedtest", "--servers", "--format=json"],
                ["speedtest", "--accept-license", "--accept-gdpr", "--servers"],
                ["speedtest", "--servers"],
                ["speedtest", "--list"],
            ]
        )
    if callable(has_cmd_fn) and has_cmd_fn("speedtest-cli"):
        candidates.append(["speedtest-cli", "--list"])
    if not candidates:
        return [], "Kein Speedtest-CLI gefunden."

    errors = []
    for cmd in candidates:
        rc, output = run_cmd_fn(cmd, timeout=timeout)
        if rc != 0:
            errors.append(f"{' '.join(cmd)} (rc={rc})")
            continue
        servers = parse_speedtest_servers(output)
        if servers:
            safe_limit = max(1, int(limit))
            return servers[:safe_limit], None
        errors.append(f"{' '.join(cmd)} (keine Server erkannt)")

    return [], "Serverliste konnte nicht gelesen werden: " + " | ".join(errors)


def run_speedtest(run_cmd_fn, has_cmd_fn, timeout=120, server_id=None):
    """Run a native CLI speedtest and return (result, error_message)."""

    errors = []
    attempted_cmds = []
    server_id = normalize_speedtest_server_id(server_id)

    def _with_optional_server(cmd, server_option="--server"):
        full_cmd = list(cmd)
        if server_id:
            if server_option == "--server-id":
                full_cmd.append(f"--server-id={server_id}")
            else:
                full_cmd.extend([server_option, server_id])
        return full_cmd

    # Prefer Ookla CLI when available.
    if callable(has_cmd_fn) and has_cmd_fn("speedtest"):
        candidates = [
            (
                ["speedtest", "--accept-license", "--accept-gdpr", "--format=json"],
                "--server-id",
            ),
            (["speedtest", "--format=json"], "--server-id"),
            # Some systems have speedtest-cli wired as speedtest.
            (["speedtest", "--json", "--secure"], "--server"),
        ]
        if server_id:
            candidates.append((["speedtest", "--json"], "--server"))
        for base_cmd, server_option in candidates:
            cmd = _with_optional_server(base_cmd, server_option)
            attempted_cmds.append(" ".join(cmd))
            result, err = _run_and_parse(
                run_cmd_fn, cmd, timeout, tool_hint="speedtest"
            )
            if result is not None:
                return result, None
            errors.append(err)

    if callable(has_cmd_fn) and has_cmd_fn("speedtest-cli"):
        candidates = [["speedtest-cli", "--json", "--secure"]]
        if server_id:
            candidates.append(["speedtest-cli", "--json"])
        for base_cmd in candidates:
            cmd = _with_optional_server(base_cmd)
            attempted_cmds.append(" ".join(cmd))
            result, err = _run_and_parse(
                run_cmd_fn,
                cmd,
                timeout,
                tool_hint="speedtest-cli",
            )
            if result is not None:
                return result, None
            errors.append(err)

    if errors:
        details = " | ".join(e for e in errors if e)
        attempted = ", ".join(attempted_cmds) if attempted_cmds else "-"
        return None, f"{details} | Versuchte Befehle: {attempted}"

    return (
        None,
        "Kein Speedtest-CLI gefunden (installiere 'speedtest' oder 'speedtest-cli').",
    )


def format_speedtest_summary(result):
    if not isinstance(result, dict):
        return "Speedtest: no data available."

    ping = result.get("ping_ms")
    jitter = result.get("jitter_ms")
    download = result.get("download_mbps")
    upload = result.get("upload_mbps")

    ping_txt = "-" if ping is None else f"{ping:.0f}"
    jitter_txt = "-" if jitter is None else f"{jitter:.0f}"
    dl_txt = "-" if download is None else f"{download:.1f}"
    ul_txt = "-" if upload is None else f"{upload:.1f}"
    server = _clean_text(result.get("server_name")) or _clean_text(
        result.get("server_host")
    )
    server_id = _clean_text(result.get("server_id"))
    server_txt = ""
    if server or server_id:
        server_label = server or "Server"
        suffix = f" (ID {server_id})" if server_id else ""
        server_txt = f" | {server_label}{suffix}"

    return (
        f"Speedtest finished: Ping {ping_txt} ms | "
        f"Jitter {jitter_txt} ms | Download {dl_txt} Mbit/s | Upload {ul_txt} Mbit/s"
        f"{server_txt}"
    )


def format_speedtest_table(result: dict) -> str:
    if not isinstance(result, dict) or not result:
        return "No speedtest result available."

    tool = (result.get("tool") or "Speedtest").strip()
    if tool.lower() == "speedtest-cli":
        tool = "Speedtest-CLI"
    elif tool.lower() == "speedtest":
        tool = "Speedtest"

    ping = result.get("ping_ms")
    jitter = result.get("jitter_ms")
    download = result.get("download_mbps")
    upload = result.get("upload_mbps")

    ping_txt = "-" if ping is None else f"{round(ping)} ms"
    jitter_txt = "-" if jitter is None else f"{round(jitter)} ms"
    dl_txt = "-" if download is None else f"{round(download, 1):.1f} Mbit/s"
    ul_txt = "-" if upload is None else f"{round(upload, 1):.1f} Mbit/s"

    server = _clean_text(result.get("server_name")) or _clean_text(
        result.get("server_host")
    )
    server_id = _clean_text(result.get("server_id"))
    server_txt = server or "-"
    if server_id:
        server_txt = f"{server_txt} ({server_id})" if server_txt != "-" else server_id

    header = "+--------------+--------+-----------+--------------+-------------+----------------------+"
    titles = "| Tool         | Ping   | Jitter    | Download     | Upload      | Server               |"
    row = (
        f"| {tool:<12} | {ping_txt:<6} | {jitter_txt:<9} | "
        f"{dl_txt:<12} | {ul_txt:<11} | {server_txt[:20]:<20} |"
    )

    return "\n".join([header, titles, header, row, header])
