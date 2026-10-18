"""Authenticated Mozilla runtime installation; never executes downloaded code.

Only stable Linux x86_64/de releases signed by the pinned Mozilla release
signer are accepted. Local, pre-existing runtimes remain user-managed inputs.
"""

import ctypes
import errno
import hashlib
import http.client
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from urllib.parse import urljoin, urlsplit

CHUNK_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_SIGNATURE_BYTES = 16 * 1024
MAX_REDIRECTS = 5
TOTAL_SECONDS = 300
SOCKET_SECONDS = 30
MIN_VERSION = (158, 0)
PRIMARY_FINGERPRINT = "14F26682D0916CDD81E37B6D61B7B526D98F0353"
SIGNER_FINGERPRINT = "827E658608679618CD349F93678E455D76767AA3"
KEYRING = Path(__file__).with_name("mozilla-release.gpg")
KEYRING_SHA256 = "f6399f61dc09ce81c0a128e5fa31192496ec2794840490f71b846e4ee7f3fcbd"
ALLOWED_HOSTS = frozenset(
    {
        "download.mozilla.org",
        "download-installer.cdn.mozilla.net",
        "archive.mozilla.org",
    }
)
RELEASE_PATH = re.compile(
    r"/pub/firefox/releases/([1-9][0-9]{0,3}(?:\.[0-9]{1,3}){1,2})/"
    r"linux-x86_64/de/firefox-\1\.tar\.xz\Z"
)


def _url_parts(url):
    if (
        not isinstance(url, str)
        or not 1 <= len(url) <= 2048
        or any(ord(c) <= 32 or ord(c) >= 127 for c in url)
        or "\\" in url
    ):
        raise ValueError("Ungueltige Firefox-Download-URL")
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in ALLOWED_HOSTS
        or parts.netloc not in {parts.hostname, f"{parts.hostname}:443"}
        or parts.fragment
    ):
        raise ValueError("Firefox-Downloadziel ist nicht freigegeben")
    return parts


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Firefox-Download-Zeitlimit erreicht")
    return min(SOCKET_SECONDS, remaining)


def download(url, destination, max_bytes, *, deadline=None):
    """Stream HTTPS with explicit redirects; intermediate bodies are never read."""
    deadline = deadline if deadline is not None else time.monotonic() + TOTAL_SECONDS
    seen = set()
    created = False
    try:
        for redirect in range(MAX_REDIRECTS + 1):
            parts = _url_parts(url)
            if url in seen:
                raise ValueError("Firefox-Redirect-Schleife")
            seen.add(url)
            connection = http.client.HTTPSConnection(
                parts.hostname, timeout=_remaining(deadline)
            )
            response = None
            try:
                # No cookies, Authorization, environment proxies or ambient headers.
                connection.request(
                    "GET",
                    parts.path + ("?" + parts.query if parts.query else ""),
                    headers={
                        "User-Agent": "NetMonRoots",
                        "Accept-Encoding": "identity",
                    },
                )
                response = connection.getresponse()
                if response.status in (301, 302, 303, 307, 308):
                    locations = response.headers.get_all("Location", [])
                    if len(locations) != 1 or redirect == MAX_REDIRECTS:
                        raise ValueError("Ungueltiger Firefox-Redirect")
                    if any(ord(c) <= 32 or ord(c) >= 127 for c in locations[0]):
                        raise ValueError("Ungueltiges Firefox-Redirect-Ziel")
                    url = urljoin(url, locations[0])
                    _url_parts(url)
                    continue
                if response.status != 200:
                    raise ValueError("Firefox-Download fehlgeschlagen")
                lengths = response.headers.get_all("Content-Length", [])
                encodings = response.headers.get_all("Content-Encoding", [])
                transfers = response.headers.get_all("Transfer-Encoding", [])
                if (
                    len(lengths) > 1
                    or (lengths and transfers)
                    or encodings not in ([], ["identity"])
                    or transfers not in ([], ["chunked"])
                ):
                    raise ValueError("Mehrdeutige HTTP-Antwort")
                expected = None
                if lengths:
                    if not re.fullmatch(r"[0-9]{1,12}", lengths[0]):
                        raise ValueError("Ungueltige HTTP-Laenge")
                    expected = int(lengths[0])
                    if expected > max_bytes:
                        raise ValueError("Firefox-Download ist zu gross")
                received = 0
                with open(destination, "xb") as output:
                    created = True
                    while True:
                        timeout = _remaining(deadline)
                        if connection.sock is not None:
                            connection.sock.settimeout(timeout)
                        block = response.read1(CHUNK_BYTES)
                        if not block:
                            break
                        received += len(block)
                        if received > max_bytes:
                            raise ValueError("Firefox-Download ist zu gross")
                        view = memoryview(block)
                        while view:
                            written = output.write(view)
                            if not written or written < 0 or written > len(view):
                                raise OSError(
                                    "Unvollstaendiger Firefox-Download-Schreibvorgang"
                                )
                            view = view[written:]
                    if expected is not None and received != expected:
                        raise ValueError("Unvollstaendiger Firefox-Download")
                    _remaining(deadline)
                    output.flush()
                return url
            finally:
                if response is not None:
                    response.close()
                connection.close()
    except BaseException:
        if created:
            Path(destination).unlink(missing_ok=True)
        raise


def _verify_manifest(directory, gpgv):
    with KEYRING.open("rb") as handle:
        key = handle.read(64 * 1024 + 1)
    if len(key) > 64 * 1024 or hashlib.sha256(key).hexdigest() != KEYRING_SHA256:
        raise ValueError("Mozilla-Trust-Anchor ist ungueltig")
    key_path = directory / "trusted.gpg"
    key_path.write_bytes(key)
    home = directory / "gnupg"
    home.mkdir(mode=0o700)
    result = subprocess.run(
        [
            gpgv,
            "--homedir",
            str(home),
            "--keyring",
            str(key_path),
            "--status-fd",
            "1",
            str(directory / "SHA256SUMS.asc"),
            str(directory / "SHA256SUMS"),
        ],
        env={"PATH": os.defpath, "LC_ALL": "C", "GNUPGHOME": str(home)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    statuses = [
        line.split() for line in result.stdout.decode("ascii", "replace").splitlines()
    ]
    signatures = [s for s in statuses if len(s) > 1 and s[1] == "VALIDSIG"]
    forbidden = {
        "BADSIG",
        "ERRSIG",
        "REVKEYSIG",
        "EXPKEYSIG",
        "EXPSIG",
        "KEYEXPIRED",
        "SIGEXPIRED",
    }
    if (
        result.returncode != 0
        or len(signatures) != 1
        or any(len(s) > 1 and s[1] in forbidden for s in statuses)
    ):
        raise ValueError("Mozilla-Pruefsummen sind nicht gueltig signiert")
    signature = signatures[0]
    if (
        len(signature) != 12
        or signature[2] != SIGNER_FINGERPRINT
        or signature[11] != PRIMARY_FINGERPRINT
        or signature[9] not in {"8", "9", "10"}
    ):
        raise ValueError(
            "Mozilla-Signatur stammt nicht vom gepinnten Signierschluessel"
        )


def _manifest_digest(path, archive_path):
    matches = []
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([\x21-\x7e][\x20-\x7e]*)", line)
        if not match:
            raise ValueError("Ungueltiges Mozilla-Pruefsummenformat")
        if match[2] == archive_path:
            matches.append(match[1])
    if len(matches) != 1:
        raise ValueError("Firefox-Archiv ist nicht eindeutig signiert")
    return matches[0]


def _publish_no_replace(source, target):
    """Linux atomic no-clobber commit; unsupported platforms fail closed."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise OSError(errno.ENOSYS, "Atomare Firefox-Installation nicht unterstuetzt")
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(target), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(
            error, "Firefox-Installation konnte nicht atomar freigegeben werden"
        )


def install(url, target, extract):
    """Verify signed digest before extraction and publish into an absent target."""
    _url_parts(url)
    gpgv = shutil.which("gpgv")
    if not gpgv:
        raise RuntimeError("Firefox-Installation erfordert gpgv (GnuPG)")
    target = Path(os.path.abspath(target))
    if os.path.lexists(target):
        raise FileExistsError("Vorhandene Firefox-Basis wird nicht ersetzt")
    if target.parent.resolve() != target.parent:
        raise ValueError("Firefox-Zielpfad enthaelt Symlinks")
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.parent.stat().st_uid != os.geteuid():
        raise ValueError("Firefox-Zielverzeichnis muss dem Benutzer gehoeren")
    deadline = time.monotonic() + TOTAL_SECONDS
    with tempfile.TemporaryDirectory(
        prefix=".netmon-firefox-", dir=target.parent
    ) as work:
        work = Path(work)
        archive = work / "runtime.tar.xz"
        final_url = download(url, archive, MAX_ARCHIVE_BYTES, deadline=deadline)
        parts = _url_parts(final_url)
        match = RELEASE_PATH.fullmatch(parts.path)
        if (
            not match
            or parts.query
            or tuple(map(int, match[1].split("."))) < MIN_VERSION
        ):
            raise ValueError("Firefox-Download ist kein freigegebenes stabiles Release")
        version = match[1]
        release_url = f"https://archive.mozilla.org/pub/firefox/releases/{version}/"
        download(
            release_url + "SHA256SUMS",
            work / "SHA256SUMS",
            MAX_MANIFEST_BYTES,
            deadline=deadline,
        )
        download(
            release_url + "SHA256SUMS.asc",
            work / "SHA256SUMS.asc",
            MAX_SIGNATURE_BYTES,
            deadline=deadline,
        )
        _verify_manifest(work, gpgv)
        expected = _manifest_digest(
            work / "SHA256SUMS", f"linux-x86_64/de/firefox-{version}.tar.xz"
        )
        # Hash and extract the same open file in a private staging directory.
        with archive.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
            if digest != expected:
                raise ValueError(
                    "Firefox-Archiv stimmt nicht mit signierter SHA256-Pruefsumme ueberein"
                )
            handle.seek(0)
            staging = work / "unpacked"
            staging.mkdir(mode=0o700)
            with tarfile.open(fileobj=handle, mode="r:*") as packed:
                extract(packed, staging)
        source = staging / "firefox"
        binary = source / "firefox"
        if not source.is_dir() or not binary.is_file() or binary.is_symlink():
            raise ValueError("Firefox-Basis im authentifizierten Archiv nicht gefunden")
        for root, directories, files in os.walk(source, followlinks=False):
            for entry in [Path(root), *(Path(root) / n for n in directories + files)]:
                mode = entry.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    raise ValueError("Unsicherer Dateityp in Firefox-Basis")
                # No group/world-writable or special privilege bits in installed files.
                entry.chmod(stat.S_IMODE(mode) & 0o755)
        binary.chmod(binary.stat().st_mode & 0o755 | 0o500)
        _publish_no_replace(source, target)
    return str(target)
