#!/usr/bin/env python3
"""Export only public static files from a verified Apache public_html bundle.

This is not a release/package builder and never copies PHP or statistics state.
The input bundle must stay immutable during the export.
"""

import argparse
from contextlib import contextmanager
import html
import os
from pathlib import Path
import re
import shutil
import stat
from urllib.parse import parse_qs, urlsplit

# Kept identical to the Caddy @public path expression; anchored, no directories.
PUBLIC_PATH = (
    r"^/(?:"
    r"(?:index|downloads|download1|docs|tour|legal|impressum|aktuelles|changelog)\.html|"
    r"security-audit(?:-r[0-9]+)?\.html|"
    r"en/(?:index|downloads|download1|docs|tour|legal|impressum|updates|changelog|security-audit)\.html|"
    r"(?:styles|theme-bright|theme-dark)\.css|app\.js|"
    r"(?:favicon|bannericon)\.png|"
    r"(?:latest-version\.json|robots\.txt|sitemap\.xml|LICENSE\.txt|THIRD_PARTY_NOTICES\.md)|"
    r"netmon_security_audit_[0-9]{4}(?:_r[0-9]+)?\.pdf|"
    r"screenshots/[A-Za-z0-9_-]+\.(?:png|jpe?g|gif|svg|webp)|"
    r"tools/(?:netmon|netmon-radio)\.png|docs/CHANGELOG\.md|"
    r"dist/(?:netmon_[0-9][0-9A-Za-z.+~_-]*_all\.deb|SHA256SUMS(?:\.minisig)?)|"
    r"dist/docs/netmon_dokumentation_[0-9][0-9A-Za-z.+~_-]*\.(?:html|pdf)|"
    r"verify/(?:verify_netmon_download\.sh|verify_netmon_signature\.sh|netmonroots\.minisign\.pub)"
    r")$"
)
PUBLIC = re.compile(PUBLIC_PATH)
PRIVATE = re.compile(
    r"(?i)(?:^|/)(?:\.|data(?:/|$))|\.(?:php[0-9]*|phtml|phar)(?:[./]|$)"
)
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


def is_public(path):
    return PUBLIC.fullmatch("/" + path) is not None and not PRIVATE.search(path)


def read_regular(directory, name):
    fd = os.open(name, FILE_FLAGS, dir_fd=directory)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Source must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def download_targets(config):
    """Read only the repository's literal download-ID/target format; never run PHP.

    Unsupported expressions or unknown IDs in an HTML link fail the export.
    No tokens/configuration bytes are included in the output.
    """
    pairs = re.findall(
        r'"([a-z0-9-]+)"\s*=>\s*\[\s*"label"\s*=>\s*"[^"\r\n]*",\s*'
        r'"target"\s*=>\s*"([^"\r\n]+)"\s*,?\s*\]',
        config,
    )
    targets = {}
    for name, target in pairs:
        if name in targets or not target.startswith("/") or not is_public(target[1:]):
            raise ValueError("Unsupported or non-public download target")
        targets[name] = target
    if not targets:
        raise ValueError("No literal public download targets found")
    return targets


def static_links(text, targets):
    def replace(match):
        quote, value = match.groups()
        url = urlsplit(html.unescape(value))
        if url.path not in {"/download.php", "download.php"}:
            return match[0]
        if url.scheme or url.netloc:
            raise ValueError("External download endpoint in static HTML")
        values = parse_qs(url.query, keep_blank_values=True).get("id", [])
        if len(values) != 1 or values[0] not in targets:
            raise ValueError("Unknown download ID in static HTML")
        target = targets[values[0]] + "?dl=1"
        return "href=" + quote + html.escape(target, quote=True) + quote

    return re.sub(r"\bhref\s*=\s*([\"'])(.*?)\1", replace, text, flags=re.IGNORECASE)


@contextmanager
def output_directory(parent, name):
    """Create exclusively with bounded permissions; never adopt an existing path."""
    os.mkdir(name, 0o755, dir_fd=parent)
    fd = os.open(name, DIR_FLAGS, dir_fd=parent)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) & ~0o755
        ):
            raise ValueError("Unsafe export directory permissions or owner")
        yield fd
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(current.st_mode)
            or current.st_uid != os.geteuid()
            or stat.S_IMODE(current.st_mode) & ~0o755
            or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino)
        ):
            raise ValueError("Export directory changed during creation")
    finally:
        os.close(fd)


@contextmanager
def output_file(directory, name):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(name, flags, 0o644, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) & ~0o644
        ):
            raise ValueError("Unsafe export file permissions or owner")
        with os.fdopen(fd, "wb", closefd=False) as stream:
            yield stream
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_uid != os.geteuid()
            or current.st_nlink != 1
            or stat.S_IMODE(current.st_mode) & ~0o644
            or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino)
        ):
            raise ValueError("Export file changed during creation")
    finally:
        os.close(fd)


def export_site(source, destination):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if source.is_symlink() or source.resolve() in destination.resolve().parents:
        raise ValueError("Use a separate source and a fresh output directory")
    root = os.open(source, DIR_FLAGS)
    try:
        targets = download_targets(read_regular(root, "download-config.php").decode())
        copied = set()

        def copy_public(directory, output, prefix=""):
            for name in sorted(os.listdir(directory)):
                path = prefix + name
                if name.startswith(".") or PRIVATE.search(path):
                    continue
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError("Symlinks are not allowed in the source bundle")
                if stat.S_ISDIR(info.st_mode):
                    if path not in {
                        "en",
                        "screenshots",
                        "tools",
                        "docs",
                        "dist",
                        "dist/docs",
                        "verify",
                    }:
                        continue
                    child = os.open(name, DIR_FLAGS, dir_fd=directory)
                    try:
                        with output_directory(output, name) as child_output:
                            copy_public(child, child_output, path + "/")
                    finally:
                        os.close(child)
                elif is_public(path):
                    # Signed release artefacts, including HTML documentation,
                    # must stay byte-identical to their SHA256SUMS manifest.
                    if path.endswith(".html") and not path.startswith("dist/"):
                        data = read_regular(directory, name)
                        data = static_links(data.decode("utf-8"), targets).encode(
                            "utf-8"
                        )
                        with output_file(output, name) as stream:
                            stream.write(data)
                    else:
                        fd = os.open(name, FILE_FLAGS, dir_fd=directory)
                        with os.fdopen(fd, "rb") as stream:
                            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                                raise ValueError("Source must be a regular file")
                            with output_file(output, name) as result:
                                shutil.copyfileobj(stream, result, 1024 * 1024)
                    copied.add("/" + path)

        parent = os.open(destination.parent, DIR_FLAGS)
        try:
            with output_directory(parent, destination.name) as output:
                copy_public(root, output)
                if not {"/index.html", *targets.values()} <= copied:
                    raise ValueError(
                        "Incomplete public bundle: a page/download target is missing"
                    )
        finally:
            os.close(parent)
    finally:
        os.close(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_html", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        export_site(args.public_html, args.output)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"Static export failed: {exc}\n")


if __name__ == "__main__":
    main()
