"""Privileged, creation-only WireGuard receipts. No user-state ownership claims.

The CLI has fixed paths, runs only from a protected installation as root, and
never registers an existing connection. Injectable objects below are for local
unit tests, not CLI flags or environment-controlled privilege bypasses.
"""

import configparser
import fcntl
import hashlib
import json
import os
import re
import secrets
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid as uuid_module
from contextlib import contextmanager
from pathlib import Path

HELPER = "/usr/lib/netmon/netmon/core/nm_ownership.py"
REGISTRY = "/var/lib/netmon/nm-wireguard-ownership"
NM_DIRECTORY = "/etc/NetworkManager/system-connections"
PROFILE_DIRECTORY = "/etc/wireguard"
OWNER = "netmon-wireguard-created-v1"
MAX_CONFIG = 1024 * 1024
MAX_RECORD = 16384
MAX_ENTRIES = 512


def _interface_name(name):
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,14}", name)
        or name in {".", ".."}
    ):
        raise OwnershipError("Invalid interface name")
    return name


def _profile_private_key(content):
    # Peer sections may repeat; only one unambiguous Interface/PrivateKey may
    # establish identity. Never execute wg-quick or any profile hooks here.
    section = ""
    interfaces = 0
    keys = []
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            interfaces += section == "interface"
        elif section == "interface":
            key, sep, value = line.partition("=")
            if sep and key.strip().lower() == "privatekey":
                keys.append(value.strip())
    if (
        interfaces != 1
        or len(keys) != 1
        or not re.fullmatch(r"[A-Za-z0-9+/]{43}=", keys[0])
    ):
        raise OwnershipError("Invalid interface key")
    return keys[0]


def _interface_command(argv, *, input_text=None):
    result = subprocess.run(
        argv,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
    )
    if result.returncode or len(result.stdout) > MAX_CONFIG:
        raise OwnershipError("Interface identity unavailable")
    return result.stdout.strip()


def _wireguard_link(name):
    rows = json.loads(
        _interface_command(["/usr/sbin/ip", "-j", "-d", "link", "show", "dev", name])
    )
    if not isinstance(rows, list) or len(rows) != 1:
        raise OwnershipError("Ambiguous interface identity")
    row = rows[0]
    if (
        row.get("ifname") != name
        or type(row.get("ifindex")) is not int
        or row["ifindex"] <= 0
        or "UP" not in row.get("flags", [])
        or row.get("linkinfo", {}).get("info_kind") != "wireguard"
    ):
        raise OwnershipError("Expected live WireGuard interface")
    return row["ifindex"]


def verified_interface(name):
    """Ask the protected helper; missing deployment/privilege is a closed gate."""
    try:
        _interface_name(name)
        if not trusted_helper_available():
            return None
        result = subprocess.run(
            ["sudo", "-n", "/usr/bin/python3", "-I", HELPER, "verify-interface"],
            input=json.dumps({"name": name}),
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        if result.returncode or len(result.stdout) > MAX_RECORD:
            return None
        proof = json.loads(result.stdout)
        if (
            not isinstance(proof, dict)
            or proof.get("name") != name
            or type(proof.get("ifindex")) is not int
            or proof["ifindex"] <= 0
            or proof.get("kind") != "wireguard"
        ):
            return None
        return proof
    except (OSError, ValueError, TypeError, OwnershipError, subprocess.SubprocessError):
        return None


def wireguard_hooks(data):
    found = []
    for line in data.decode("utf-8", errors="strict").splitlines():
        key = line.split("#", 1)[0].split(";", 1)[0].split("=", 1)
        if len(key) != 2:
            continue
        canonical = {
            "preup": "PreUp",
            "postup": "PostUp",
            "predown": "PreDown",
            "postdown": "PostDown",
        }.get(key[0].strip().lower())
        if canonical and canonical not in found:
            found.append(canonical)
    return tuple(found)


def checked_import_payload(payload):
    if not isinstance(payload, dict) or set(payload) != {
        "name",
        "content",
        "sha256",
        "hooks",
    }:
        raise OwnershipError("Reviewed import proof required")
    name, content, digest = payload["name"], payload["content"], payload["sha256"]
    if (
        not isinstance(name, str)
        or name in {".", ".."}
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
    ):
        raise OwnershipError("Invalid import name")
    if (
        not isinstance(content, str)
        or not 0 < len(content.encode()) <= MAX_CONFIG
        or "\0" in content
    ):
        raise OwnershipError("Invalid import content")
    data = content.encode("utf-8")
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or hashlib.sha256(data).hexdigest() != digest
        or not isinstance(payload["hooks"], list)
        or payload["hooks"] != list(wireguard_hooks(data))
    ):
        raise OwnershipError("Reviewed import bytes changed")
    return name, content


@contextmanager
def _import_snapshot(parent, name, data, *, owner):
    # parent has already been opened/validated as root-controlled by the caller.
    with tempfile.TemporaryDirectory(prefix=".import-", dir=parent) as staging:
        source = Path(staging) / (name + ".conf")
        with source.open("xb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            view = memoryview(data)
            while view:
                written = handle.write(view)
                if not written or written < 0 or written > len(view):
                    raise OwnershipError("Incomplete import snapshot")
                view = view[written:]
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(staging, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _check(os.fstat(directory), owner, directory=True, private=True)
            actual, _info = _read(directory, source.name, owner, MAX_CONFIG)
            if actual != data:
                raise OwnershipError("Privileged import snapshot changed")
            yield source
        finally:
            os.close(directory)


class OwnershipError(RuntimeError):
    pass


def canonical_uuid(value):
    if not isinstance(value, str) or str(uuid_module.UUID(value)) != value:
        raise OwnershipError("Invalid connection UUID")
    return value


def _fingerprint(info):
    return {
        key: getattr(info, "st_" + key)
        for key in ("dev", "ino", "uid", "gid", "mode", "size", "mtime_ns", "ctime_ns")
    }


def _check(info, owner, *, directory=False, private=False):
    if info.st_uid != owner or info.st_mode & 0o022:
        raise OwnershipError("Untrusted ownership or permissions")
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise OwnershipError("Expected a protected directory")
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OwnershipError("Expected a regular, singly linked file")
    if private and info.st_mode & 0o077:
        raise OwnershipError("Private ownership evidence required")


def _directory(path, *, owner=0, anchor=Path("/"), create=False, private=False):
    path, anchor = Path(path), Path(anchor)
    parts = path.relative_to(anchor).parts
    if not path.is_absolute() or ".." in parts:
        raise OwnershipError("Invalid protected path")
    fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        _check(os.fstat(fd), owner, directory=True)
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = child
            _check(os.fstat(fd), owner, directory=True)
        _check(os.fstat(fd), owner, directory=True, private=private)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read(directory_fd, name, owner, limit):
    if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
        raise OwnershipError("Invalid evidence filename")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    try:
        before = os.fstat(fd)
        _check(before, owner, private=True)
        if before.st_size > limit:
            raise OwnershipError("Evidence size limit exceeded")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        after = os.fstat(fd)
        if len(data) > limit or _fingerprint(before) != _fingerprint(after):
            raise OwnershipError("Evidence changed while reading")
        return data, _fingerprint(after)
    finally:
        os.close(fd)


def _keyfile(data, *, wireguard_only=True):
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read_string(data.decode("utf-8"))
    if wireguard_only and parser.get("connection", "type") != "wireguard":
        return None
    return canonical_uuid(parser.get("connection", "uuid"))


class NetworkManager:
    def command(self, *arguments):
        result = subprocess.run(
            ["/usr/bin/nmcli", "--colors", "no", "--wait", "20", *arguments],
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=25,
            check=False,
        )
        if result.returncode or len(result.stdout) > MAX_CONFIG:
            # Do not relay config-parser errors which might contain secrets.
            raise OwnershipError("NetworkManager operation failed")
        return result.stdout.decode("utf-8", errors="strict").strip()

    def profiles(self):
        rows = self.command(
            "--escape", "no", "-t", "-f", "UUID,FILENAME", "connection", "show"
        ).splitlines()
        if len(rows) > MAX_ENTRIES:
            raise OwnershipError("Excessive connection list")
        result = {}
        for row in rows:
            identity, separator, filename = row.partition(":")
            canonical_uuid(identity)
            if (
                not separator
                or identity in result
                or len(filename.encode()) > 4096
                or any(ord(c) < 32 for c in filename)
            ):
                raise OwnershipError("Ambiguous connection storage")
            result[identity] = filename
        return result

    def uuids(self):
        return set(self.profiles())

    def filename(self, uuid):
        return self.profiles().get(canonical_uuid(uuid))

    def show(self, uuid):
        values = self.command(
            "--escape",
            "no",
            "-g",
            "connection.uuid,connection.id,connection.type",
            "connection",
            "show",
            "uuid",
            canonical_uuid(uuid),
        ).splitlines()
        if len(values) != 3 or values[0] != uuid or values[2] != "wireguard":
            raise OwnershipError("Connection identity/type mismatch")
        name = values[1]
        if (
            not name
            or len(name.encode()) > 1024
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
        ):
            raise OwnershipError("Unsafe connection display name")
        return {"uuid": uuid, "name": name}

    def create(self, path):
        output = self.command(
            "connection", "import", "type", "wireguard", "file", str(path)
        )
        match = re.fullmatch(
            r"Connection '[^\r\n]*' \(([0-9a-f-]{36})\) successfully added\.", output
        )
        if not match:
            raise OwnershipError("Import identity unavailable; no ownership registered")
        return canonical_uuid(match[1])

    def delete(self, uuid):
        self.command("connection", "delete", "uuid", canonical_uuid(uuid))


class OwnershipStore:
    def __init__(
        self,
        registry=REGISTRY,
        nm_directory=NM_DIRECTORY,
        *,
        owner=0,
        anchor=Path("/"),
        nm=None,
    ):
        self.registry, self.nm_directory = Path(registry), Path(nm_directory)
        self.owner, self.anchor, self.nm = owner, Path(anchor), nm or NetworkManager()

    @contextmanager
    def locked(self, *, create=False):
        directory = _directory(
            self.registry,
            owner=self.owner,
            anchor=self.anchor,
            create=create,
            private=True,
        )
        lock = None
        try:
            lock = os.open(
                ".lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600,
                dir_fd=directory,
            )
            _check(os.fstat(lock), self.owner, private=True)
            until = time.monotonic() + 2
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= until:
                        raise OwnershipError("Ownership registry busy")
                    time.sleep(0.01)
            yield directory
        finally:
            if lock is not None:
                os.close(lock)
            os.close(directory)

    def _snapshot(self, filename):
        directory = _directory(self.nm_directory, owner=self.owner, anchor=self.anchor)
        try:
            data, info = _read(directory, filename, self.owner, MAX_CONFIG)
            return data, {
                **info,
                "filename": filename,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        finally:
            os.close(directory)

    def _scan_keyfiles(self, *, all_types=False):
        directory = _directory(self.nm_directory, owner=self.owner, anchor=self.anchor)
        try:
            entries = os.listdir(directory)
            if len(entries) > MAX_ENTRIES:
                raise OwnershipError("Too many keyfiles")
            found, total = [], 0
            for name in entries:
                if not name.endswith(".nmconnection"):
                    continue
                try:
                    data, info = _read(directory, name, self.owner, MAX_CONFIG)
                    total += len(data)
                    if total > 16 * MAX_CONFIG:
                        raise OwnershipError("Keyfile scan budget exceeded")
                    identity = _keyfile(data, wireguard_only=not all_types)
                    if identity is not None:
                        found.append(
                            (
                                identity,
                                {
                                    **info,
                                    "filename": name,
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                },
                            )
                        )
                except (OSError, ValueError, configparser.Error):
                    continue
            return found
        finally:
            os.close(directory)

    def _find_created(self, uuid):
        found = [info for identity, info in self._scan_keyfiles() if identity == uuid]
        if len(found) != 1:
            raise OwnershipError("Unique root-controlled keyfile unavailable")
        return found[0]

    def _verify(self, directory, uuid, receipt_id=None):
        uuid = canonical_uuid(uuid)
        data, _ = _read(directory, uuid + ".json", self.owner, MAX_RECORD)
        receipt = json.loads(data)
        if (
            receipt.get("owner") != OWNER
            or receipt.get("schema") != 1
            or receipt.get("uuid") != uuid
            or not re.fullmatch(r"[0-9a-f]{32}", receipt.get("receipt_id", ""))
            or (receipt_id is not None and receipt["receipt_id"] != receipt_id)
            or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("source_sha256", ""))
            or not isinstance(receipt.get("created_ns"), int)
            or not 0 < receipt["created_ns"] <= time.time_ns() + 60_000_000_000
        ):
            raise OwnershipError("Invalid creation receipt")
        current = self.nm.show(uuid)
        if self.nm.filename(uuid) != str(
            self.nm_directory / receipt["keyfile"]["filename"]
        ):
            raise OwnershipError("NetworkManager storage backend changed")
        keyfile, snapshot = self._snapshot(receipt["keyfile"]["filename"])
        if snapshot != receipt["keyfile"] or _keyfile(keyfile) != uuid:
            raise OwnershipError("Connection incarnation changed")
        return {
            **current,
            "receipt_id": receipt["receipt_id"],
            "receipt_sha256": hashlib.sha256(data).hexdigest(),
        }

    def candidates(self):
        try:
            with self.locked() as directory:
                entries = os.listdir(directory)
                if len(entries) > MAX_ENTRIES:
                    raise OwnershipError("Too many ownership receipts")
                result = []
                for name in sorted(entries):
                    if not name.endswith(".json"):
                        continue
                    try:
                        result.append(self._verify(directory, name[:-5]))
                    except (
                        OSError,
                        ValueError,
                        KeyError,
                        TypeError,
                        AttributeError,
                        RecursionError,
                        OwnershipError,
                        configparser.Error,
                    ):
                        continue
                return result
        except FileNotFoundError:
            return []

    def inspect(self, uuid, receipt_id):
        with self.locked() as directory:
            return self._verify(directory, uuid, receipt_id)

    def delete(self, candidate):
        with self.locked() as directory:
            current = self._verify(
                directory, candidate["uuid"], candidate["receipt_id"]
            )
            if current != candidate:
                raise OwnershipError("Cleanup plan changed; confirmation expired")
            # All cooperating NetMon writers share this lock. nmcli's UUID API
            # has no generation compare-and-delete: privileged external NM edits
            # in the final command gap remain a documented administrative race.
            self.nm.delete(current["uuid"])
            os.unlink(current["uuid"] + ".json", dir_fd=directory)
            os.fsync(directory)

    def create(self, name, content):
        if (
            not isinstance(name, str)
            or name in {".", ".."}
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
        ):
            raise OwnershipError("Invalid import name")
        if not isinstance(content, str) or not 0 < len(content.encode()) <= MAX_CONFIG:
            raise OwnershipError("Invalid import size")
        with self.locked(create=True) as directory:
            if len(os.listdir(directory)) >= MAX_ENTRIES:
                raise OwnershipError("Ownership registry full")
            before = self.nm.uuids()
            # Unloaded on-disk profiles are existing profiles too. Never
            # retroactively claim one merely because NM did not list it.
            before.update(
                identity for identity, _info in self._scan_keyfiles(all_types=True)
            )
            # Source bytes cross sudo via stdin, not a root-opened user path or
            # a private key in process arguments. nmcli sees a root-only snapshot.
            with _import_snapshot(
                self.registry, name, content.encode(), owner=self.owner
            ) as source:
                uuid = self.nm.create(source)
            if uuid in before:
                raise OwnershipError("Existing UUID cannot be registered")
            current = self.nm.show(uuid)
            receipt = {
                "schema": 1,
                "owner": OWNER,
                "uuid": uuid,
                "receipt_id": secrets.token_hex(16),
                "created_ns": time.time_ns(),
                "source_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "keyfile": self._find_created(uuid),
            }
            encoded = json.dumps(receipt, sort_keys=True).encode()
            if len(encoded) > MAX_RECORD:
                raise OwnershipError("Receipt too large")
            temporary = ".receipt-" + secrets.token_hex(16)
            try:
                fd = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                with os.fdopen(fd, "wb") as handle:
                    if handle.write(encoded) != len(encoded):
                        raise OwnershipError("Incomplete receipt write")
                    handle.flush()
                    os.fsync(handle.fileno())
                # link() publishes without overwriting any pre-existing receipt.
                os.link(
                    temporary,
                    uuid + ".json",
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                    follow_symlinks=False,
                )
            finally:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass
            os.fsync(directory)
            verified = self._verify(directory, uuid, receipt["receipt_id"])
            if verified["name"] != current["name"]:
                raise OwnershipError("Imported connection changed")
            return verified

    def snapshot_profile(self, name):
        if (
            not isinstance(name, str)
            or name in {".", ".."}
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
        ):
            raise OwnershipError("Invalid profile name")
        directory = _directory(PROFILE_DIRECTORY, owner=self.owner, anchor=self.anchor)
        try:
            data, _info = _read(directory, name + ".conf", self.owner, MAX_CONFIG)
            content = data.decode("utf-8", errors="strict")
            result = {
                "name": name,
                "content": content,
                "sha256": hashlib.sha256(data).hexdigest(),
                "hooks": list(wireguard_hooks(data)),
            }
            checked_import_payload(result)
            return result
        finally:
            os.close(directory)

    def install_profile(self, payload):
        name, content = checked_import_payload(payload)
        # Even a same-named WireGuard link must be stopped before replacement.
        # Recheck at the privileged installation boundary, not just in the UI.
        if name in {iface for _index, iface in socket.if_nameindex()}:
            raise OwnershipError("Profile name collides with a live interface")
        with self.locked(create=True):
            directory = _directory(
                PROFILE_DIRECTORY,
                owner=self.owner,
                anchor=self.anchor,
                create=True,
            )
            try:
                try:
                    _data, previous = _read(
                        directory, name + ".conf", self.owner, MAX_CONFIG
                    )
                except FileNotFoundError:
                    previous = None
                with _import_snapshot(
                    PROFILE_DIRECTORY, name, content.encode(), owner=self.owner
                ) as source:
                    try:
                        _data, current = _read(
                            directory, name + ".conf", self.owner, MAX_CONFIG
                        )
                    except FileNotFoundError:
                        current = None
                    if current != previous:
                        raise OwnershipError("Destination changed during import")
                    if name in {iface for _index, iface in socket.if_nameindex()}:
                        raise OwnershipError(
                            "Profile name collides with a live interface"
                        )
                    os.replace(source, name + ".conf", dst_dir_fd=directory)
                    os.fsync(directory)
            finally:
                os.close(directory)

    def verify_interface(self, name):
        """Bind a live link to exact protected profile bytes, without hooks."""
        _interface_name(name)
        profile = self.snapshot_profile(name)
        private = _profile_private_key(profile["content"])
        index = _wireguard_link(name)
        public = _interface_command(
            ["/usr/bin/wg", "pubkey"], input_text=private + "\n"
        )
        live = _interface_command(["/usr/bin/wg", "show", name, "public-key"])
        if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", public) or public != live:
            raise OwnershipError("Interface does not belong to profile")
        if _wireguard_link(name) != index or self.snapshot_profile(name) != profile:
            raise OwnershipError("Interface/profile changed during verification")
        return {
            "name": name,
            "kind": "wireguard",
            "ifindex": index,
            "public_key": public,
            "profile_sha256": profile["sha256"],
        }


def trusted_helper_available():
    try:
        directory = _directory(Path(HELPER).parent)
        try:
            fd = os.open(
                Path(HELPER).name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            try:
                _check(os.fstat(fd), 0)
            finally:
                os.close(fd)
        finally:
            os.close(directory)
        return True
    except (OSError, ValueError, OwnershipError):
        return False


def main(arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if (
        os.geteuid() != 0
        or os.path.abspath(__file__) != HELPER
        or not trusted_helper_available()
    ):
        print("Protected installed root helper required", file=sys.stderr)
        return 1
    try:
        store = OwnershipStore()
        if arguments in (
            ["import"],
            ["import-checked"],
            ["install-profile"],
            ["snapshot-profile"],
            ["verify-interface"],
        ):
            raw = sys.stdin.buffer.read(6 * MAX_CONFIG + 4097)
            if len(raw) > 6 * MAX_CONFIG + 4096:
                raise OwnershipError("Import request too large")
            payload = json.loads(raw)
            if arguments in (["snapshot-profile"], ["verify-interface"]):
                if not isinstance(payload, dict) or set(payload) != {"name"}:
                    raise OwnershipError("Invalid profile snapshot request")
                result = (
                    store.snapshot_profile(payload["name"])
                    if arguments == ["snapshot-profile"]
                    else store.verify_interface(payload["name"])
                )
                print(json.dumps(result))
            else:
                name, content = checked_import_payload(payload)
                if arguments in (["import"], ["import-checked"]):
                    print(json.dumps(store.create(name, content)))
                else:
                    store.install_profile(payload)
        elif len(arguments) == 3 and arguments[0] == "inspect":
            print(json.dumps(store.inspect(arguments[1], arguments[2])))
        elif arguments == ["delete"]:
            raw = sys.stdin.buffer.read(MAX_RECORD + 1)
            if len(raw) > MAX_RECORD:
                raise OwnershipError("Cleanup request too large")
            store.delete(json.loads(raw))
        elif arguments == ["cleanup"]:
            candidates = store.candidates()
            if not candidates:
                print(
                    "No verified NetMon connections; legacy/unproven connections retained."
                )
                return 0
            for item in candidates:
                print(
                    json.dumps(
                        {"name": item["name"], "uuid": item["uuid"]}, ensure_ascii=True
                    )
                )
            print(
                "Delete exactly these verified UUIDs? / Diese UUIDs loeschen? [y/N] ",
                end="",
                flush=True,
            )
            if sys.stdin.readline(16).strip().lower() not in {"y", "yes", "j", "ja"}:
                print("Canceled / Abgebrochen.")
                return 0
            for item in candidates:
                try:
                    store.delete(item)
                    print("Removed UUID: " + item["uuid"])
                except Exception:
                    print("Retained changed/unverifiable UUID: " + item["uuid"])
        else:
            raise OwnershipError("Unknown ownership operation")
        return 0
    except Exception:
        print(
            "Ownership verification failed; unproven connections retained. A failed import may require manual cleanup.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
