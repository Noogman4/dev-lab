"""Bounded station-file import; no resolution, external entities or playback."""

import hashlib
import os
from pathlib import Path
import re
import shlex
from urllib.parse import unquote, urlsplit
from xml.parsers import expat

from netmon.core.import_limits import read_bounded_bytes
from netmon.core.private_logs import _private_directory

MAX_BYTES = 1024 * 1024
MAX_TRACKS = 1000
MAX_NODES = 20000
MAX_DEPTH = 24
MAX_FIELD_CHARS = 8192
MAX_PLS_FIELDS = 4002
NS = "http://xspf.org/ns/0/|"
PLAYLIST = NS + "playlist"
TRACK_LIST = NS + "trackList"
TRACK = NS + "track"
SUPPORTED_SUFFIXES = {".xspf", ".m3u", ".m3u8", ".pls"}


def _direct_stream_url(url):
    if not url or len(url) > MAX_FIELD_CHARS:
        return False
    if any(char.isspace() or not char.isprintable() for char in url) or "\\" in url:
        return False
    try:
        parsed = urlsplit(url)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.fragment
            and not parsed.netloc.endswith(":")
            and parsed.port != 0
            and not unquote(parsed.path)
            .lower()
            .endswith((".m3u", ".m3u8", ".pls", ".mpd", ".xspf"))
        )
    except ValueError:
        return False


def stream_key(url):
    """Compare equivalent origin spellings without changing path/query semantics."""
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return (
        parsed.scheme.lower(),
        parsed.hostname.lower(),
        port,
        parsed.path or "/",
        parsed.query,
    )


def parse_xspf(payload):
    if len(payload) > MAX_BYTES:
        raise ValueError("XSPF-Datei ist größer als 1 MiB.")
    parser = expat.ParserCreate(namespace_separator="|")
    stack = []
    fields = []
    field_size = 0
    nodes = tracks = track_lists = 0
    playlist_title = ""
    track = None
    candidates = []

    def refuse(*_args):
        raise ValueError("DTD und XML-Entitäten sind im Senderimport nicht erlaubt.")

    def start(name, attributes):
        nonlocal nodes, tracks, track_lists, track, field_size
        stack.append(name)
        nodes += 1
        if nodes > MAX_NODES or len(stack) > MAX_DEPTH:
            raise ValueError("XSPF-Struktur überschreitet die Importgrenze.")
        if len(stack) == 1 and (name != PLAYLIST or attributes.get("version") != "1"):
            raise ValueError("Keine unterstützte XSPF-1-Playlist.")
        if stack == [PLAYLIST, TRACK_LIST]:
            track_lists += 1
            if track_lists > 1:
                raise ValueError("Mehrere XSPF-trackList-Elemente sind nicht erlaubt.")
        if stack == [PLAYLIST, TRACK_LIST, TRACK]:
            tracks += 1
            if tracks > MAX_TRACKS:
                raise ValueError("XSPF enthält mehr als 1000 Sender.")
            track = {"title": "", "locations": []}
        fields.clear()
        field_size = 0

    def characters(text):
        nonlocal field_size
        if stack in (
            [PLAYLIST, NS + "title"],
            [PLAYLIST, TRACK_LIST, TRACK, NS + "title"],
            [PLAYLIST, TRACK_LIST, TRACK, NS + "location"],
        ):
            field_size += len(text)
            if field_size > MAX_FIELD_CHARS:
                raise ValueError("XSPF-Feld überschreitet die Importgrenze.")
            fields.append(text)

    def end(name):
        nonlocal playlist_title, track
        value = "".join(fields).strip()
        if stack == [PLAYLIST, NS + "title"]:
            playlist_title = value
        elif stack == [PLAYLIST, TRACK_LIST, TRACK, NS + "title"]:
            track["title"] = value
        elif stack == [PLAYLIST, TRACK_LIST, TRACK, NS + "location"]:
            track["locations"].append(value)
        elif stack == [PLAYLIST, TRACK_LIST, TRACK]:
            candidates.append(track)
            track = None
        stack.pop()
        fields.clear()

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters
    parser.StartDoctypeDeclHandler = refuse
    parser.EntityDeclHandler = refuse
    parser.ExternalEntityRefHandler = refuse
    try:
        parser.Parse(payload, True)
    except expat.ExpatError as exc:
        raise ValueError("XSPF-Datei enthält ungültiges XML.") from exc
    if track_lists != 1 or not tracks:
        raise ValueError("XSPF enthält keine Senderliste.")
    return _station_rows(candidates, "XSPF", playlist_title)


def _station_rows(candidates, format_name, playlist_title=""):
    rows = []
    seen = set()
    skipped = duplicates = 0
    for item in candidates:
        url = next(
            (
                location
                for location in item["locations"]
                if _direct_stream_url(location)
            ),
            "",
        )
        if not url:
            skipped += 1
            continue
        key = stream_key(url)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        title = item["title"] or playlist_title or urlsplit(url).hostname
        title = re.sub(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]+", " ", title)
        rows.append(
            {
                "name": title[:512],
                "url": url,
                "category": f"{format_name}-Import",
                "custom": True,
            }
        )
    if not rows:
        raise ValueError(
            f"{format_name} enthält keine unterstützten direkten HTTP-/HTTPS-Streams."
        )
    return rows, {
        "tracks": len(candidates),
        "skipped": skipped,
        "duplicates": duplicates,
    }


def _decode_station_text(payload, label, *, utf8_only=False):
    if len(payload) > MAX_BYTES:
        raise ValueError(f"{label}-Datei ist größer als 1 MiB.")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        if utf8_only or payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError(f"{label}-Datei enthält ungültiges UTF-8.") from exc
        text = payload.decode("latin-1")
    if "\x00" in text:
        raise ValueError(f"{label} enthält unzulässige NUL-Zeichen.")
    return text


def parse_m3u(payload, *, utf8_only=False):
    """Read plain or extended station lists; HLS manifests are not station lists."""
    text = _decode_station_text(payload, "M3U", utf8_only=utf8_only)
    candidates = []
    pending = None
    header = False
    for raw in re.split(r"\r\n|\r|\n", text):
        if len(raw) > MAX_FIELD_CHARS:
            raise ValueError("M3U-Zeile überschreitet die Importgrenze.")
        line = raw.strip()
        if not line:
            continue
        if line == "#EXTM3U":
            if header or pending is not None or candidates:
                raise ValueError("M3U-Kopf steht nicht am Anfang der Senderliste.")
            header = True
            continue
        if line.startswith("#EXT-X-"):
            raise ValueError(
                "HLS-Manifest erkannt: keine importierbare Radiosenderliste."
            )
        if line.startswith("#EXTINF:"):
            if pending is not None:
                raise ValueError("M3U-Sendereintrag enthält keine Stream-Adresse.")
            quoted = False
            separator = None
            for index, char in enumerate(line):
                if char == '"':
                    quoted = not quoted
                elif char == "," and not quoted:
                    separator = index
                    break
            if separator is None:
                raise ValueError("Ungültige M3U-Senderbeschreibung.")
            try:
                tokens = shlex.split(line[8:separator])
            except ValueError as exc:
                raise ValueError("Ungültige M3U-Senderbeschreibung.") from exc
            if not tokens or not re.fullmatch(r"-?\d+(?:\.\d+)?", tokens[0]):
                raise ValueError("Ungültige M3U-Dauerangabe.")
            pending = line[separator + 1 :].strip()
            continue
        if line.startswith("#"):
            continue
        candidates.append({"title": pending or "", "locations": [line]})
        pending = None
        if len(candidates) > MAX_TRACKS:
            raise ValueError("M3U enthält mehr als 1000 Sender.")
    if pending is not None:
        raise ValueError("M3U-Sendereintrag enthält keine Stream-Adresse.")
    return _station_rows(candidates, "M3U")


def parse_pls(payload):
    """Read indexed PLS entries as data, without INI interpolation or options."""
    text = _decode_station_text(payload, "PLS")
    header = False
    fields = {}
    entries = {}
    declared = None
    for raw in re.split(r"\r\n|\r|\n", text):
        if len(raw) > MAX_FIELD_CHARS:
            raise ValueError("PLS-Zeile überschreitet die Importgrenze.")
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if not header:
            if line.casefold() != "[playlist]":
                raise ValueError("PLS benötigt den Abschnitt [playlist].")
            header = True
            continue
        if line.startswith("[") or "=" not in line:
            raise ValueError("Ungültige PLS-Struktur; erwartet wird eine Senderliste.")
        key, value = line.split("=", 1)
        key, value = key.strip().casefold(), value.strip()
        if not key or key in fields:
            raise ValueError("PLS enthält einen leeren oder doppelten Schlüssel.")
        fields[key] = value
        if len(fields) > MAX_PLS_FIELDS:
            raise ValueError("PLS enthält zu viele Felder.")
        if key == "numberofentries":
            if not re.fullmatch(r"[0-9]{1,4}", value) or int(value) > MAX_TRACKS:
                raise ValueError("Ungültige oder zu große PLS-Senderanzahl.")
            declared = int(value)
            continue
        if key == "version":
            if value not in {"1", "2"}:
                raise ValueError("Nicht unterstützte PLS-Version.")
            continue
        match = re.fullmatch(r"(file|title|length)([1-9][0-9]{0,3})", key)
        if match is None:
            if key.startswith(("file", "title", "length")):
                raise ValueError("Ungültige PLS-Sendernummer.")
            # Unknown player directives remain ignored metadata.
            continue
        kind, number = match.group(1), int(match.group(2))
        if number > MAX_TRACKS:
            raise ValueError("PLS-Sendernummer überschreitet die Importgrenze.")
        item = entries.setdefault(number, {"title": "", "locations": []})
        if kind == "file":
            item["locations"] = [value]
        elif kind == "title":
            item["title"] = value
        elif not re.fullmatch(r"-1|[0-9]{1,10}", value) or int(value) > 2**31 - 1:
            raise ValueError("Ungültige PLS-Dauerangabe.")
    if not header:
        raise ValueError("PLS benötigt den Abschnitt [playlist].")
    if declared is not None and declared != len(entries):
        raise ValueError("PLS-Senderanzahl passt nicht zu den enthaltenen Einträgen.")
    return _station_rows([entries[number] for number in sorted(entries)], "PLS")


def read_station_file(path):
    suffix = Path(path).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(
            "Bitte eine XSPF-, M3U-, M3U8- oder PLS-Senderdatei auswählen."
        )
    payload = read_bounded_bytes(path, MAX_BYTES, label="Senderimport")
    if suffix == ".xspf":
        rows, summary = parse_xspf(payload)
    elif suffix == ".pls":
        rows, summary = parse_pls(payload)
    else:
        rows, summary = parse_m3u(payload, utf8_only=suffix == ".m3u8")
    return payload, rows, summary


def read_xspf(path):
    if Path(path).suffix.lower() != ".xspf":
        raise ValueError("Bitte eine XSPF-Senderdatei auswählen.")
    payload = read_bounded_bytes(path, MAX_BYTES, label="XSPF")
    rows, summary = parse_xspf(payload)
    return payload, rows, summary


def merge_imported_stations(existing, imported):
    """Append custom stations once, preserving existing rows and unique IDs."""
    merged = list(existing)
    seen = set()
    identifiers = {row.get("id") for row in existing}
    for row in existing:
        for field in ("url", "url_resolved"):
            try:
                seen.add(stream_key(row[field]))
            except (KeyError, ValueError, AttributeError, TypeError):
                pass
    added = duplicates = 0
    for row in imported:
        key = stream_key(row["url"])
        if key in seen:
            duplicates += 1
            continue
        station = dict(row)
        base = (
            station.get("id")
            or "xspf-" + hashlib.sha256(repr(key).encode()).hexdigest()[:16]
        )
        identifier = base
        suffix = 2
        while identifier in identifiers:
            identifier = f"{base}-{suffix}"
            suffix += 1
        station.update(id=identifier, custom=True)
        merged.append(station)
        seen.add(key)
        identifiers.add(identifier)
        added += 1
    return merged, added, duplicates


def archive_station_file(payload, source_path, folder):
    """Keep the exact validated bytes; never move or overwrite the source."""
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(source_path).stem)[:48] or "sender"
    suffix = Path(source_path).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError("Nicht unterstütztes Archivformat.")
    name = f"{stem}-{hashlib.sha256(payload).hexdigest()[:16]}{suffix}"
    with _private_directory(folder) as directory:
        try:
            descriptor = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
        except FileExistsError:
            if (
                read_bounded_bytes(Path(folder) / name, MAX_BYTES, label="Senderarchiv")
                != payload
            ):
                raise ValueError(
                    "Archivdatei ist bereits mit anderem Inhalt vorhanden."
                )
        else:
            with os.fdopen(descriptor, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
    return Path(folder) / name


def archive_xspf(payload, source_path, folder):
    return archive_station_file(payload, source_path, folder)
