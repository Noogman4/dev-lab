"""Private diagnostic output without changing the process-wide umask.

Only the final log directory and checked regular files are tightened. Ancestors
are walked through descriptors without following links, never chmodded.
"""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import stat

from .log_redaction import (
    encode_log_record,
    redact_diagnostic_value,
    redact_sensitive_text,
)

MAX_LOG_RECORD_CHARS = 64 * 1024


class _RedactedLog:
    """Redact one bounded record, including secrets split across write calls.

    Publication happens when the context exits. flush() never publishes an
    incomplete record that might split a credential or multiline private key.
    """

    def __init__(self, output):
        self.output = output
        self.parts = []
        self.length = 0
        self.truncated = False
        self.encoding = "utf-8"

    def write(self, text):
        if not isinstance(text, str):
            raise TypeError("Log text must be a string")
        remaining = MAX_LOG_RECORD_CHARS - self.length
        part = text[:remaining]
        if part:
            self.parts.append(part)
        self.length += len(part)
        self.truncated |= len(text) > remaining
        return len(text)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        self.output.flush()

    def finish(self):
        if self.truncated:
            # A cut JSON/quoted value may no longer be parseable/redactable.
            # Publish no partial source text in that case.
            text = "[NetMon log record truncated]\n"
        else:
            text = redact_sensitive_text("".join(self.parts))
            # A caller may supply one final framing LF. All embedded separators
            # belong to this event, even across write()/writelines() calls.
            terminator = "\n" if text.endswith("\n") else ""
            body = text[:-1] if terminator else text
            text = (
                encode_log_record(body, limit=MAX_LOG_RECORD_CHARS - len(terminator))
                + terminator
            )
        self.output.write(text)


@contextmanager
def _private_directory(path):
    path = Path(path)
    if ".." in path.parts:
        raise PermissionError("Unsafe log directory")
    path = Path(os.path.abspath(path))
    if path == Path(path.anchor):
        raise PermissionError("Log directory cannot be the filesystem root")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    directory = os.open(path.anchor, flags)
    try:
        for index, part in enumerate(path.parts[1:], start=1):
            try:
                os.mkdir(part, 0o700, dir_fd=directory)
            except FileExistsError:
                pass
            child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
            info = os.fstat(directory)
            # Shared /tmp is allowed only with root ownership and sticky bit.
            shared_temporary = info.st_uid == 0 and info.st_mode & stat.S_ISVTX
            if info.st_uid not in {0, os.geteuid()} or (
                info.st_mode & 0o022
                and not shared_temporary
                and index != len(path.parts) - 1
            ):
                raise PermissionError("Unsafe log directory owner or permissions")
        info = os.fstat(directory)
        if info.st_uid != os.geteuid() or info.st_mode & stat.S_ISVTX:
            raise PermissionError("Foreign log directory")
        os.fchmod(directory, 0o700)
        yield directory
    finally:
        os.close(directory)


def ensure_private_log_directory(path):
    with _private_directory(path):
        pass
    return os.fspath(path)


def _check_file(info):
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.geteuid()
        or info.st_nlink != 1
    ):
        raise PermissionError("Unsafe log file type, owner or link count")


def _open_file(directory, name, mode):
    try:
        expected = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        expected = None
    if expected is not None:
        _check_file(expected)
    flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    flags |= os.O_APPEND if mode == "a" else 0
    # A missing output must still be absent at creation, rather than reopening
    # a file substituted after the stat above.
    flags |= os.O_CREAT | os.O_EXCL if expected is None or mode == "x" else 0
    fd = os.open(name, flags, 0o600, dir_fd=directory)
    try:
        actual = os.fstat(fd)
        _check_file(actual)
        if expected is not None and (actual.st_dev, actual.st_ino) != (
            expected.st_dev,
            expected.st_ino,
        ):
            raise PermissionError("Log file changed while opening")
        os.fchmod(fd, 0o600)
        if mode == "w":
            os.ftruncate(fd, 0)
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextmanager
def open_private_log(path, mode="a"):
    """Open a checked owner-only log; truncate only after all checks pass."""
    if mode not in {"a", "w", "x"}:
        raise ValueError("Unsupported private log mode")
    path = Path(path)
    with _private_directory(path.parent) as directory:
        fd = _open_file(directory, path.name, mode)
        with os.fdopen(fd, mode, encoding="utf-8") as output:
            record = _RedactedLog(output)
            try:
                yield record
            finally:
                record.finish()


def write_private_diagnostic_json(path, payload):
    """Publish a complete private report without replacing any existing name."""
    content = json.dumps(redact_diagnostic_value(payload), indent=2, ensure_ascii=False)
    path = Path(path)
    with _private_directory(path.parent) as directory:
        temporary = f".netmon-diagnostic-{secrets.token_hex(16)}.tmp"
        fd = _open_file(directory, temporary, "x")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.link(
                temporary,
                path.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
        finally:
            os.unlink(temporary, dir_fd=directory)
