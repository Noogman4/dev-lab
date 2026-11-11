"""Protected UFW snapshots and conflict-checked, explicit restoration.

Only the installed root CLI can access fixed system paths. Tests inject a
temporary system root, ownership identity and simulated UFW/kernel backend.
The desktop journal is never accepted as restoration authority.
"""

import base64
import ctypes
from collections import Counter
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import fcntl
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

HELPER = "/usr/lib/netmon/netmon/core/ufw_snapshot.py"
PROTOCOL = 11
REGISTRY = "/var/lib/netmon/ufw-snapshot"
MUTABLE = (
    "/etc/ufw/user.rules",
    "/etc/ufw/user6.rules",
    "/etc/default/ufw",
    "/etc/ufw/ufw.conf",
    "/etc/ufw/after.rules",
    "/etc/ufw/after6.rules",
)
OBSERVED = MUTABLE + ("/etc/ufw/before.rules", "/etc/ufw/before6.rules")
MAX_FILE = 1024 * 1024
MAX_RECORD = 16 * MAX_FILE

# Validate the fixed installed script before the privileged interpreter reads it.
BOOTSTRAP = r"""
import os, stat, sys
path = "/usr/lib/netmon/netmon/core/ufw_snapshot.py"
current = "/"
for part in [""] + path.strip("/").split("/"):
    current = os.path.join(current, part)
    info = os.lstat(current)
    if info.st_uid != 0 or info.st_mode & 0o022:
        sys.exit("Unprotected UFW helper")
    if current == path:
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            sys.exit("Unsafe UFW helper")
    elif not stat.S_ISDIR(info.st_mode):
        sys.exit("Unsafe UFW helper directory")
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path] + sys.argv[1:])
"""


@contextmanager
def _ufw_output():
    """UFW writes bytes through stream.buffer, including warnings on stderr."""
    output = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        with redirect_stdout(output), redirect_stderr(output):
            yield
    finally:
        output.close()


class SnapshotError(RuntimeError):
    def __init__(self, message, code="snapshot_failed"):
        super().__init__(message)
        self.code = code


class UfwSnapshotClient:
    def __init__(self, transport=None):
        self.transport = transport
        self.token = None

    def request(self, operation, payload):
        if self.transport is not None:
            return self.transport(operation, payload)
        if not trusted_helper_available():
            raise SnapshotError("Geschützter UFW-Snapshothelfer fehlt")
        from netmon.core.command import run_cmd_with_input

        if operation != "state":
            # An older installed helper must reject the read-only handshake
            # before it can execute any mutation requested by a newer client.
            rc_probe, output_probe = run_cmd_with_input(
                [
                    "sudo",
                    "-n",
                    "/usr/bin/python3",
                    "-I",
                    "-c",
                    BOOTSTRAP,
                    "capabilities",
                ],
                input_text="{}",
                timeout=10,
            )
            try:
                compatible = rc_probe == 0 and json.loads(output_probe) == {
                    "protocol": PROTOCOL,
                    "prepared_commands": True,
                }
            except (ValueError, TypeError):
                compatible = False
            if not compatible:
                raise SnapshotError(
                    "UFW-Snapshothelfer fehlt oder ist inkompatibel; keine Änderung angefordert",
                    "incompatible",
                )
        rc, output = run_cmd_with_input(
            ["sudo", "-n", "/usr/bin/python3", "-I", "-c", BOOTSTRAP, operation],
            input_text=json.dumps(payload),
            timeout=90,
        )
        if rc:
            code = None
            messages = {
                "no_snapshot": "Keine vertrauenswürdige UFW-Sicherung vorhanden; alte Sperren werden nicht automatisch entfernt.",
                "conflict": "UFW-Zustand wurde zwischenzeitlich geändert; Benutzeränderungen bleiben erhalten, Wiederherstellung abgebrochen.",
                "inactive": "UFW muss für diese Transaktion aktiv sein und IPv4/IPv6 unterstützen.",
                "rollback_failed": "UFW-Rollback fehlgeschlagen; Sicherung bleibt erhalten, Netzwerkschutz ist nicht bestätigt.",
                "pending": "Eine frühere UFW-Transaktion muss zuerst ausdrücklich wiederhergestellt werden.",
                "preflight": "Vorhandene UFW-Regeln widersprechen dem Killswitch; keine Firewalländerung ausgeführt.",
                "busy": "UFW ist vorübergehend belegt; Vorgang unverändert erneut versuchen.",
                "not_active": "Geschützter Killswitch ist nicht mehr aktiv; keine erneute Aktivierung angefordert.",
            }
            try:
                response = json.loads(output)
                code = (
                    response.get("error")
                    if response.get("protocol") == PROTOCOL
                    else None
                )
                message = messages.get(code)
            except (ValueError, TypeError, AttributeError):
                message = None
            raise SnapshotError(
                message
                or "UFW-Wiederherstellung nicht bestätigt; bestehende Regeln manuell prüfen",
                code=code if isinstance(code, str) else "snapshot_failed",
            )
        result = json.loads(output)
        if not isinstance(result, dict) or result.get("protocol") != PROTOCOL:
            raise SnapshotError("UFW-Snapshothelfer hat eine inkompatible Version")
        return result

    def begin(
        self,
        interfaces=(),
        endpoints=(),
        *,
        blocked_interfaces=(),
        require_active=False,
    ):
        payload = {
            "interfaces": list(interfaces),
            "endpoints": [list(item) for item in endpoints],
        }
        if blocked_interfaces:
            payload["blocked_interfaces"] = list(blocked_interfaces)
        if require_active:
            payload["require_active"] = require_active
        result = self.request(
            "begin",
            payload,
        )
        self.token = result["token"]

    def run(self, arguments, timeout=0, text=True):
        if arguments[:3] != ["sudo", "-n", "ufw"] or self.token is None:
            raise SnapshotError("Invalid UFW transaction command")
        result = self.request(
            "command", {"token": self.token, "arguments": arguments[3:]}
        )
        return result["rc"], result["output"]

    def ufw_enable_force(self, timeout=0):
        return self.run(["sudo", "-n", "ufw", "--force", "enable"])

    def commit(self):
        if self.request("commit", {"token": self.token}).get("state") != "on":
            raise SnapshotError("Activation not confirmed")

    def recovery(self):
        self.request("recovery", {"token": self.token})

    def restore(self):
        if self.request("restore", {}).get("state") != "off":
            raise SnapshotError("Restoration not confirmed")

    def acknowledge(self):
        if self.request("acknowledge", {}).get("state") != "reviewed":
            raise SnapshotError("Manual review not confirmed")

    def abort_unmodified(self):
        return self.request("abort_unmodified", {}).get("unmodified") is True

    def state(self):
        if self.transport is None and not trusted_helper_available():
            return "absent"
        try:
            state = self.request("state", {}).get("state")
            return (
                state
                if state in {"on", "off", "unknown", "recovery", "absent", "reviewed"}
                else "unknown"
            )
        except Exception:
            return "unknown"


def _check(info, owner, *, directory=False):
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if info.st_uid != owner or info.st_mode & 0o022 or not expected(info.st_mode):
        raise SnapshotError("Untrusted storage")
    if not directory and info.st_nlink != 1:
        raise SnapshotError("Unexpected file links")


def _directory(path, owner, anchor, create=False):
    path, anchor = Path(path), Path(anchor)
    parts = path.relative_to(anchor).parts
    if not path.is_absolute() or ".." in parts:
        raise SnapshotError("Invalid storage path")
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
        return fd
    except BaseException:
        os.close(fd)
        raise


def trusted_helper_available():
    try:
        directory = _directory(Path(HELPER).parent, 0, Path("/"))
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
    except (OSError, ValueError, SnapshotError):
        return False


def valid_interface_name(name):
    return (
        isinstance(name, str)
        and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,14}", name) is not None
    )


def _plan(payload):
    if (
        not isinstance(payload, dict)
        or not {"interfaces", "endpoints"} <= set(payload)
        or set(payload) - {"interfaces", "endpoints", "blocked_interfaces"}
    ):
        raise SnapshotError("Invalid plan")
    interfaces, endpoints = payload["interfaces"], payload["endpoints"]
    blocked = payload.get("blocked_interfaces", [])
    if (
        not isinstance(interfaces, list)
        or not isinstance(blocked, list)
        or not isinstance(endpoints, list)
        or len(interfaces) > 64
        or len(blocked) > 64
        or len(endpoints) > 128
    ):
        raise SnapshotError("Excessive plan")
    for name in interfaces + blocked:
        if not valid_interface_name(name):
            raise SnapshotError("Invalid interface")
    if "lo" in blocked or set(interfaces) & set(blocked):
        raise SnapshotError("Conflicting interface plan")
    for endpoint in endpoints:
        if not isinstance(endpoint, list) or len(endpoint) != 2:
            raise SnapshotError("Invalid endpoint")
        if not isinstance(endpoint[0], str):
            raise SnapshotError("Invalid endpoint address")
        ipaddress.ip_address(endpoint[0])
        if (
            not isinstance(endpoint[1], str)
            or not endpoint[1].isdigit()
            or not 1 <= int(endpoint[1]) <= 65535
        ):
            raise SnapshotError("Invalid port")
    result = {
        "interfaces": sorted(set(interfaces)),
        "endpoints": [
            list(item)
            for item in sorted(
                {
                    (str(ipaddress.ip_address(ip)), str(int(port)))
                    for ip, port in endpoints
                }
            )
        ],
    }
    if blocked:
        result["blocked_interfaces"] = sorted(set(blocked))
    return result


def _command(arguments):
    if (
        not isinstance(arguments, list)
        or len(arguments) > 16
        or any(not isinstance(s, str) or len(s) > 128 for s in arguments)
    ):
        raise SnapshotError("Invalid command")
    if arguments in (
        ["status"],
        ["status", "verbose"],
        ["status", "numbered"],
        ["--force", "enable"],
    ):
        return arguments
    if (
        len(arguments) == 3
        and arguments[0] == "default"
        and arguments[1] in {"allow", "deny"}
        and arguments[2] in {"incoming", "outgoing"}
    ):
        return arguments
    if (
        len(arguments) == 3
        and arguments[:2] == ["--force", "delete"]
        and arguments[2].isdigit()
        and 1 <= int(arguments[2]) <= 4096
    ):
        return arguments
    if (arguments[2:] if arguments[:2] == ["insert", "1"] else arguments) in (
        ["deny", "out", "from", "any", "to", "any"],
        ["deny", "in", "from", "any", "to", "any"],
    ):
        return arguments
    rule = (
        arguments[2:]
        if arguments[:2] == ["insert", "1"]
        else arguments[1:] if arguments[:1] == ["delete"] else arguments
    )
    if arguments[:2] == ["insert", "1"] and rule[:1] != ["deny"]:
        raise SnapshotError("Only restrictive interface rules may be inserted")
    if (
        len(rule) == 4
        and rule[0] in {"allow", "deny"}
        and rule[1] in {"in", "out"}
        and rule[2] == "on"
        and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,14}", rule[3])
    ):
        return arguments
    if rule in (
        ["allow", "out", "53/udp"],
        ["allow", "out", "53/tcp"],
        ["allow", "out", "80/tcp"],
        ["allow", "out", "443/tcp"],
    ):
        return arguments
    if (
        len(rule) == 8
        and rule[:3] == ["allow", "out", "to"]
        and rule[4] == "port"
        and rule[6:] == ["proto", "udp"]
    ):
        _plan({"interfaces": [], "endpoints": [[rule[3], rule[5]]]})
        return arguments
    raise SnapshotError("Command not permitted")


class SnapshotStore:
    def __init__(self, backend, *, root=Path("/"), owner=0):
        self.root, self.owner, self.backend = Path(root), owner, backend
        self.registry = self.root / REGISTRY.lstrip("/")

    def _read(self, path, *, limit=MAX_FILE):
        directory = _directory(path.parent, self.owner, self.root)
        try:
            fd = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            try:
                before = os.fstat(fd)
                _check(before, self.owner)
                if before.st_size > limit:
                    raise SnapshotError("File size limit")
                with os.fdopen(fd, "rb", closefd=False) as stream:
                    content = stream.read(limit + 1)
                after = os.fstat(fd)
                if len(content) > limit or any(
                    getattr(before, k) != getattr(after, k)
                    for k in (
                        "st_dev",
                        "st_ino",
                        "st_size",
                        "st_mtime_ns",
                        "st_ctime_ns",
                    )
                ):
                    raise SnapshotError("File changed during snapshot")
                return {
                    "data": base64.b64encode(content).decode(),
                    "mode": stat.S_IMODE(before.st_mode),
                    "gid": before.st_gid,
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            finally:
                os.close(fd)
        finally:
            os.close(directory)

    def _write(self, path, row):
        data = base64.b64decode(row["data"], validate=True)
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise SnapshotError("Snapshot integrity check failed")
        directory = _directory(path.parent, self.owner, self.root, create=True)
        name = ".netmon-" + secrets.token_hex(16)
        try:
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fchmod(stream.fileno(), row["mode"])
                os.fchown(stream.fileno(), self.owner, row["gid"])
                os.fsync(stream.fileno())
            os.replace(name, path.name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(name, dir_fd=directory)
            except FileNotFoundError:
                pass
            os.close(directory)

    def capture(self):
        return {
            "files": {
                name: self._read(self.root / name.lstrip("/")) for name in OBSERVED
            },
            "runtime": self.backend.runtime(),
        }

    def load(self):
        try:
            row = self._read(self.registry / "state.json", limit=MAX_RECORD)
        except FileNotFoundError:
            return None
        if row["mode"] & 0o077:
            raise SnapshotError("Private snapshot required")
        record = json.loads(base64.b64decode(row["data"]))
        if record.get("version") != 1 or record.get("phase") not in {
            "applying",
            "active",
            "restoring",
            "recovery",
            "off",
            "reviewed",
        }:
            raise SnapshotError("Invalid snapshot journal")
        for key in (
            "original",
            "expected",
            *(("intent",) if "intent" in record else ()),
        ):
            if (
                set(record[key]) != {"files", "runtime"}
                or set(record[key]["files"]) != set(OBSERVED)
                or set(record[key]["runtime"]) != {"4", "6"}
            ):
                raise SnapshotError("Incomplete snapshot")
            for row in record[key]["files"].values():
                if (
                    not isinstance(row, dict)
                    or set(row) != {"data", "mode", "gid", "sha256"}
                    or type(row["mode"]) is not int
                    or not 0 <= row["mode"] <= 0o777
                    or row["mode"] & 0o022
                    or type(row["gid"]) is not int
                    or row["gid"] < 0
                ):
                    raise SnapshotError("Invalid snapshot metadata")
                data = base64.b64decode(row["data"], validate=True)
                if (
                    len(data) > MAX_FILE
                    or hashlib.sha256(data).hexdigest() != row["sha256"]
                ):
                    raise SnapshotError("Invalid snapshot data")
            digest = hashlib.sha256(
                json.dumps(record[key], sort_keys=True).encode()
            ).hexdigest()
            if record.get("integrity", {}).get(key) != digest:
                raise SnapshotError("Snapshot journal integrity failed")
        _plan(record["plan"])
        if type(record.get("closed", False)) is not bool or (
            record.get("closed")
            and (record["plan"]["interfaces"] or record["plan"]["endpoints"])
        ):
            raise SnapshotError("Invalid protected closed plan")
        return record

    def save(self, record):
        record["integrity"] = {
            key: hashlib.sha256(
                json.dumps(record[key], sort_keys=True).encode()
            ).hexdigest()
            for key in (
                "original",
                "expected",
                *(("intent",) if "intent" in record else ()),
            )
        }
        data = json.dumps(record).encode()
        if len(data) > MAX_RECORD:
            raise SnapshotError("Snapshot size limit")
        self._write(
            self.registry / "state.json",
            {
                "data": base64.b64encode(data).decode(),
                "mode": 0o600,
                "gid": os.getegid(),
                "sha256": hashlib.sha256(data).hexdigest(),
            },
        )

    def begin(self, plan):
        if (
            not isinstance(plan, dict)
            or type(plan.get("require_active", False)) is not bool
        ):
            raise SnapshotError("Invalid active-only precondition")
        require_active = plan.get("require_active", False)
        plan = _plan(
            {key: value for key, value in plan.items() if key != "require_active"}
        )
        record = self.load()
        # The CLI holds the UFW lock. An explicit OFF before this point must
        # never turn a stale offline resync into a fresh activation.
        if require_active and (record is None or record["phase"] != "active"):
            raise SnapshotError("Managed killswitch is no longer active", "not_active")
        closed = not plan["interfaces"] and not plan["endpoints"]
        if closed and not require_active:
            raise SnapshotError(
                "Empty plan requires protected active continuation", "preflight"
            )
        current = self.capture()
        if not self.backend.ready():
            raise SnapshotError("Active dual-family UFW required", "inactive")
        previous_plan = None
        if record and record["phase"] not in {"off", "reviewed"}:
            if record["phase"] != "active" or current != record["expected"]:
                raise SnapshotError(
                    "Recovery or external changes require inspection", "pending"
                )
            previous_plan = record["plan"]
        else:
            record = {"version": 1, "original": current}
        if closed and not self._verify_enabled(record):
            raise SnapshotError("Previous protected plan is not verified", "pending")
        if not interface_fences_ordered(
            current["runtime"],
            plan.get("blocked_interfaces", []),
            require_present=False,
            fresh_fences=logging_only_interface_fences(current),
        ):
            raise SnapshotError(
                "Existing interface deny follows an accept rule; user rule order retained",
                "preflight",
            )
        if previous_plan is None and callable(getattr(self.backend, "preflight", None)):
            self.backend.preflight(plan)
        for name in plan["interfaces"]:
            self.backend.verify_interface(name)
        if previous_plan is not None:
            departing = (
                set(previous_plan["interfaces"])
                | set(previous_plan.get("blocked_interfaces", []))
            ) - (set(plan["interfaces"]) | set(plan.get("blocked_interfaces", [])))
            for name in departing:
                if any(
                    plain_interface_rule_present(
                        record["original"]["runtime"], name, direction, "ACCEPT"
                    )
                    for direction in ("in", "out")
                ) and name not in plan.get("blocked_interfaces", []):
                    raise SnapshotError(
                        "Retired original interface grant requires an explicit fence",
                        "preflight",
                    )
        record.update(
            phase="applying", expected=current, token=secrets.token_hex(32), plan=plan
        )
        if closed:
            record["closed"] = True
        else:
            record.pop("closed", None)
        self.save(record)
        if previous_plan is not None:
            retired = []
            # Remove only our temporary fence, never a pre-existing user deny.
            for name in sorted(
                set(previous_plan.get("blocked_interfaces", []))
                - set(plan.get("blocked_interfaces", []))
            ):
                for direction in ("in", "out"):
                    retired.append(["delete", "deny", direction, "on", name])
            for name in sorted(
                set(previous_plan["interfaces"]) - set(plan["interfaces"])
            ):
                for direction in ("in", "out"):
                    if not plain_interface_rule_present(
                        record["original"]["runtime"], name, direction, "ACCEPT"
                    ):
                        retired.append(["delete", "allow", direction, "on", name])
            for ip, port in sorted(
                set(map(tuple, previous_plan["endpoints"]))
                - set(map(tuple, plan["endpoints"]))
            ):
                retired.append(
                    ["delete", "allow", "out", "to", ip, "port", port, "proto", "udp"]
                )
            for command in retired:
                if self.command(record["token"], command)["rc"]:
                    raise SnapshotError("Retired grant cleanup failed", "pending")
        return {"token": record["token"]}

    def _current(self, token):
        record = self.load()
        if not record or not secrets.compare_digest(record["token"], token):
            raise SnapshotError("Unknown transaction")
        if self.capture() != record["expected"]:
            raise SnapshotError("Firewall changed outside this transaction", "conflict")
        return record

    def command(self, token, arguments):
        arguments = _command(arguments)
        record = self._current(token)
        if record["phase"] not in {"applying", "recovery"}:
            raise SnapshotError("Transaction not writable")
        if (
            arguments[:1] == ["allow"]
            and len(arguments) == 4
            and arguments[2] == "on"
            and arguments[3] != "lo"
        ):
            self.backend.verify_interface(arguments[3])
        planner = getattr(self.backend, "prepare", None)
        kernel_committed = False
        if callable(planner) and arguments[:1] != ["status"]:
            # The real UFW parser/serializer runs against private copies first.
            # Persist the exact destination files and both family tables BEFORE
            # the first live write, allowing every per-file/per-family cut.
            try:
                record["intent"] = planner(
                    arguments, record["expected"], original=record["original"]
                )
            except (Exception, SystemExit) as exc:
                raise SnapshotError("Private UFW preparation failed") from exc
            self._current(token)
            self.save(record)
            try:
                for name in MUTABLE:
                    if (
                        record["intent"]["files"][name]
                        != record["expected"]["files"][name]
                    ):
                        self._write(
                            self.root / name.lstrip("/"),
                            record["intent"]["files"][name],
                        )
                self.backend.restore(record["intent"]["runtime"])
                kernel_committed = True
                if self.capture() != record["intent"]:
                    raise SnapshotError("Prepared operation not verified")
                rc, output = 0, "UFW operation verified"
            except Exception:
                rc, output = (
                    1,
                    "UFW operation incomplete; protected restoration required",
                )
            if not rc:
                record.pop("intent", None)
        else:
            rc, output = self.backend.command(arguments)
        current = self.capture()
        if rc and "intent" in record:
            if kernel_committed and current["files"] == record["intent"]["files"]:
                # Both kernel writers acknowledged our commit under the UFW
                # lock. A serialization gap is a failed verification, not an
                # external edit. Retain the observed state as a rollback-only
                # checkpoint; never report successful activation here.
                record["expected"] = current
            else:
                self._allow_intended_partial(record, current)
        record["expected"] = current
        if rc:
            record["phase"] = "recovery"
        self.save(record)
        return {"rc": rc, "output": output}

    def _verify_enabled(self, record):
        plan = record["plan"]
        if (
            not plan["interfaces"]
            and not plan["endpoints"]
            and not record.get("closed")
        ):
            return False
        options = {"original": record["original"]["runtime"]}
        if record.get("closed"):
            options["allow_empty_plan"] = True
        return self.backend.verify_enabled(plan, **options)

    def commit(self, token):
        record = self._current(token)
        if record["phase"] != "applying" or not self._verify_enabled(record):
            raise SnapshotError("Activation not verified")
        record["phase"] = "active"
        self.save(record)
        return {"state": "on"}

    def recovery(self, token):
        record = self.load()
        if not record or not secrets.compare_digest(record["token"], token):
            raise SnapshotError("Unknown transaction")
        self._allow_intended_partial(record, self.capture())
        record["expected"] = self.capture()
        record["phase"] = "recovery"
        self.save(record)
        return {"state": "recovery"}

    def state(self):
        record = self.load()
        if record is None:
            return {"state": "absent"}
        if record["phase"] in {"applying", "restoring", "recovery"}:
            return {"state": "recovery"}
        if record["phase"] == "off":
            # Retired receipt, not a continuing constraint on ordinary UFW use.
            return {"state": "off", "retired": True}
        if record["phase"] == "reviewed":
            return {"state": "reviewed", "retired": True}
        if self.capture() != record["expected"] or not self.backend.ready():
            return {"state": "unknown"}
        result = {"state": "on" if self._verify_enabled(record) else "unknown"}
        if result["state"] == "on" and record.get("closed"):
            result["closed"] = True
        return result

    def restore(self):
        record = self.load()
        if record is None or record["phase"] in {"off", "reviewed"}:
            raise SnapshotError(
                "No protected pre-state; manual recovery required", "no_snapshot"
            )
        current = self.capture()
        if "intent" in record:
            self._allow_intended_partial(record, current)
            record["expected"] = current
            record.pop("intent", None)
        elif record["phase"] == "restoring":
            for name in OBSERVED:
                allowed = (
                    (
                        record["expected"]["files"][name],
                        record["original"]["files"][name],
                    )
                    if name in MUTABLE
                    else (record["expected"]["files"][name],)
                )
                if current["files"][name] not in allowed:
                    raise SnapshotError(
                        "External change during restoration", "conflict"
                    )
            if not self._known_runtime_mix(
                current["runtime"],
                record["expected"]["runtime"],
                record["original"]["runtime"],
            ):
                raise SnapshotError(
                    "Unexpected live state during restoration", "conflict"
                )
        elif current != record["expected"]:
            raise SnapshotError("External firewall changes retained", "conflict")
        if not self.backend.ready():
            raise SnapshotError("UFW must remain active", "inactive")
        record["phase"] = "restoring"
        # Explicit OFF cancels earlier clients; they cannot re-close a restored
        # firewall with stale activation/recovery commands from another process.
        record["token"] = secrets.token_hex(32)
        self.save(record)
        try:
            for name in MUTABLE:
                self._write(
                    self.root / name.lstrip("/"), record["original"]["files"][name]
                )
            self.backend.restore(record["original"]["runtime"])
            if self.capture() != record["original"] or not self.backend.ready():
                raise SnapshotError("Restoration verification failed")
        except Exception:
            # Keep a protected original. Retry may only use verified known states.
            record["expected"] = self.capture()
            record["phase"] = "recovery"
            self.save(record)
            failures = []
            for command in (
                ["insert", "1", "deny", "out", "from", "any", "to", "any"],
                ["insert", "1", "deny", "in", "from", "any", "to", "any"],
            ):
                try:
                    result = self.command(record["token"], command)
                    if result["rc"]:
                        result = self.command(record["token"], command[2:])
                    if result["rc"]:
                        failures.append(command[3])
                except Exception:
                    try:
                        if self.command(record["token"], command[2:])["rc"]:
                            failures.append(command[3])
                    except Exception:
                        failures.append(command[3])
            raise SnapshotError(
                "Rollback failed; emergency commands "
                + (
                    "incomplete" if failures else "applied; verification still required"
                ),
                "rollback_failed",
            ) from None
        record["expected"] = record["original"]
        record["phase"] = "off"
        self.save(record)
        return {"state": "off"}

    @staticmethod
    def _allow_intended_partial(record, current):
        intended = record.get("intent", record["expected"])
        if any(
            current["files"][name]
            not in (record["expected"]["files"][name], intended["files"][name])
            for name in OBSERVED
        ):
            raise SnapshotError(
                "External file change during interrupted command", "conflict"
            )
        if not SnapshotStore._known_runtime_mix(
            current["runtime"], record["expected"]["runtime"], intended["runtime"]
        ):
            raise SnapshotError(
                "External runtime change during interrupted command", "conflict"
            )

    @staticmethod
    def _known_runtime_mix(current, before, after):
        """A reboot may combine known user chains with known default policies.

        Accept only complete, ordered chains from either durable checkpoint;
        foreign chains, rules, policies and within-chain mixtures stay conflicts.
        File bytes and metadata are checked separately before using this gate.
        """

        def chains(rows):
            result = {}
            for row in rows:
                if row.startswith(":"):
                    name = row.split()[0][1:]
                    if name in result:
                        return None
                    result[name] = [row]
                elif row.startswith("-A "):
                    name = shlex.split(row)[1]
                    if name not in result:
                        return None
                    result[name].append(row)
                else:
                    return None
            return result

        for family in ("4", "6"):
            if current[family] in (before[family], after[family]):
                continue
            live, old, new = map(
                chains, (current[family], before[family], after[family])
            )
            if any(item is None for item in (live, old, new)):
                return False
            for name in set(live) | set(old) | set(new):
                if live.get(name) not in (old.get(name), new.get(name)):
                    return False
        return True

    def acknowledge(self):
        """Retire authority only after explicit review; never changes UFW."""
        current = self.capture()
        if not self.backend.ready():
            raise SnapshotError("Active dual-family UFW required", "inactive")
        record = self.load()
        pending = record is not None and record["phase"] not in {"off", "reviewed"}
        self.backend.manual_review_check(legacy=not pending)
        if pending:
            if current != record["original"]:
                # A reviewed admin edit may be retained, but not our policies
                # or a temporary profile fence. This is never an OFF receipt.
                if persistent_policies(current) != persistent_policies(
                    record["original"]
                ):
                    raise SnapshotError(
                        "Persistent firewall policies must match the protected original",
                        "pending",
                    )
                if persistent_user_blocks(current) - persistent_user_blocks(
                    record["original"]
                ):
                    raise SnapshotError(
                        "Additional persistent user-chain blocks must be removed before manual completion",
                        "pending",
                    )
                for family in ("4", "6"):

                    def policies(snapshot):
                        return {
                            row.split()[0]: row.split()[1]
                            for row in snapshot["runtime"][family]
                            if row.startswith((":INPUT ", ":OUTPUT ", ":FORWARD "))
                        }

                    if len(policies(current)) != 3 or policies(current) != policies(
                        record["original"]
                    ):
                        raise SnapshotError(
                            "Original firewall policies must be restored before manual completion",
                            "pending",
                        )
                if introduced_interface_fences(
                    current["runtime"], record["original"]["runtime"]
                ):
                    raise SnapshotError(
                        "Additional interface DROP rules must be withdrawn before manual completion",
                        "pending",
                    )
            # Archive first. Failure must leave restoration authority pending.
            data = json.dumps(record, sort_keys=True).encode()
            archive = "reviewed-" + secrets.token_hex(16) + ".json"
            self._write(
                self.registry / archive,
                {
                    "data": base64.b64encode(data).decode(),
                    "mode": 0o600,
                    "gid": os.getegid(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
            )
            record["review_archive"] = archive
        if record is not None:
            record.update(
                phase="reviewed", expected=current, token=secrets.token_hex(32)
            )
            record.pop("intent", None)
            self.save(record)
        return {"state": "reviewed"}

    def abort_unmodified(self):
        record = self.load()
        if record is None:
            return {"unmodified": True}
        if self.capture() != record["original"]:
            return {"unmodified": False}
        record.update(
            phase="off", expected=record["original"], token=secrets.token_hex(32)
        )
        record.pop("intent", None)
        self.save(record)
        return {"unmodified": True}

    def removal(self):
        record = self.load()
        if record is not None and record["phase"] not in {"off", "reviewed"}:
            raise SnapshotError(
                "Active or pending firewall transaction prevents package removal",
                "pending",
            )
        return {"removable": True}


def outgoing_rules_match_plan(runtime, plan):
    return runtime_matches_plan(runtime, plan, require_active=False)


def plain_interface_rule_present(runtime, name, direction, target):
    flag = "-i" if direction == "in" else "-o"
    chain = "input" if direction == "in" else "output"
    # A matching original rule in either family forbids combined deletion.
    return any(
        shlex.split(row) == ["-A", prefix + chain, flag, name, "-j", target]
        for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-"))
        for row in runtime[family]
    )


def persistent_policies(snapshot):
    """Read UFW's literal policy settings without executing shell config.

    ufw-init sources defaults then ufw.conf. Reject non-data shell constructs
    rather than asserting a reboot policy we cannot safely determine.
    """
    wanted = {"DEFAULT_INPUT_POLICY", "DEFAULT_OUTPUT_POLICY", "DEFAULT_FORWARD_POLICY"}
    policies = {}
    for name in ("/etc/default/ufw", "/etc/ufw/ufw.conf"):
        text = base64.b64decode(snapshot["files"][name]["data"], validate=True).decode()
        for line in text.split("\n"):
            line = line.strip(" \t")
            if not line or line.startswith("#"):
                continue
            # In sh, '#' starts a comment only at a word boundary. Validate
            # the whole assignment, before discarding any comment text.
            assignment = re.fullmatch(
                r"([A-Z_][A-Z0-9_]*)=(?:\"([A-Za-z0-9_./:, -]*)\""
                r"|'([A-Za-z0-9_./:, -]*)'|([A-Za-z0-9_./:,-]*))"
                r"(?:[ \t]+#.*)?",
                line,
            )
            if assignment is None:
                raise SnapshotError(
                    "Persistent UFW config is not literal assignments", "pending"
                )
            key = assignment[1]
            value = next(item for item in assignment.groups()[1:] if item is not None)
            if key in wanted:
                if value not in {"ACCEPT", "DROP", "REJECT"}:
                    raise SnapshotError("Invalid persistent UFW policy", "pending")
                policies[key] = value
    if set(policies) != wanted:
        raise SnapshotError("Missing persistent UFW policies", "pending")
    return policies


def persistent_user_blocks(snapshot):
    """Count saved DROP/REJECT rules that can return on the next boot."""
    blocks = Counter()
    for family, name, prefix in (
        ("4", "user.rules", "ufw-"),
        ("6", "user6.rules", "ufw6-"),
    ):
        text = base64.b64decode(
            snapshot["files"]["/etc/ufw/" + name]["data"], validate=True
        ).decode()
        table = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("### tuple ###"):
                # UFW can regenerate rule lines from these even when an
                # administrator removed only the visible DROP lines.
                fields = line[len("### tuple ###") :].split(" comment=", 1)[0].split()
                if fields and fields[0].lower().split("_", 1)[0] in {"deny", "reject"}:
                    blocks[(family, "tuple:" + " ".join(fields))] += 1
                continue
            if line.startswith("*"):
                table = line
            elif line == "COMMIT":
                table = None
            elif table == "*filter" and line.startswith(("-A ", "-I ")):
                tokens = shlex.split(line)
                if tokens[1] not in {prefix + "user-input", prefix + "user-output"}:
                    continue
                if tokens[0] == "-I" and len(tokens) > 2 and tokens[2].isdigit():
                    tokens.pop(2)
                tokens[0] = "-A"
                if any(
                    tokens[i : i + 2]
                    in (
                        ["-j", "DROP"],
                        ["-j", "REJECT"],
                        ["--jump", "DROP"],
                        ["--jump", "REJECT"],
                    )
                    for i in range(2, len(tokens) - 1)
                ):
                    blocks[(family, _runtime_row(_iptables_line(tokens)))] += 1
    return blocks


def introduced_interface_fences(runtime, original, names=None):
    """Detect additional plain interface DROP rules, including retired profiles."""

    def counts(state):
        result = Counter()
        for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-")):
            for row in state[family]:
                tokens = shlex.split(row)
                if (
                    len(tokens) == 6
                    and tokens[:2]
                    in (["-A", prefix + "input"], ["-A", prefix + "output"])
                    and tokens[2] in {"-i", "-o"}
                    and (names is None or tokens[3] in names)
                    and tokens[4:] == ["-j", "DROP"]
                ):
                    result[(family, row)] += 1
        return result

    return bool(counts(runtime) - counts(original))


def logging_only_interface_fences(snapshot):
    """Identify logged full-interface DENYs that prepare cannot reuse as plain DENY.

    UFWRule.match also compares logtype. Only positively identified canonical
    logging tuples allow a fresh leading fence; unknown metadata stays strict.
    """
    plain, logged = set(), set()
    for family, filename, address in (
        ("4", "user.rules", "0.0.0.0/0"),
        ("6", "user6.rules", "::/0"),
    ):
        text = base64.b64decode(
            snapshot["files"]["/etc/ufw/" + filename]["data"], validate=True
        ).decode()
        for line in text.splitlines():
            if not line.startswith("### tuple ### "):
                continue
            fields = line[len("### tuple ### ") :].split(" comment=", 1)[0].split()
            if len(fields) != 7 or fields[1:6] != [
                "any",
                "any",
                address,
                "any",
                address,
            ]:
                continue
            direction, separator, iface = fields[6].partition("_")
            if (
                not separator
                or direction not in {"in", "out"}
                or not valid_interface_name(iface)
            ):
                continue
            key = (family, "input" if direction == "in" else "output", iface)
            if fields[0] == "deny":
                plain.add(key)
            elif fields[0] in {"deny_log", "deny_log-all"}:
                logged.add(key)
    return logged - plain


def interface_fences_ordered(runtime, interfaces, *, require_present, fresh_fences=()):
    """Never reuse a plain existing fence behind an ACCEPT/LIMIT on its interface.

    Preflight allows a missing fence because apply will insert one first. The
    final verifier also requires that every planned fence is actually present.
    """
    for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-")):
        rules = [
            shlex.split(row)
            for row in runtime[family]
            if row.startswith("-A " + prefix)
        ]
        accept_targets = {"ACCEPT", prefix + "limit-accept"}
        for iface in interfaces:
            for chain, flag in (("input", "-i"), ("output", "-o")):
                if not require_present and (family, chain, iface) in fresh_fences:
                    continue  # prepare will insert a separate leading plain DENY.
                fence = ["-A", prefix + chain, flag, iface, "-j", "DROP"]
                if fence not in rules:
                    if require_present:
                        return False
                    continue
                for tokens in rules[: rules.index(fence)]:
                    if (
                        tokens[1] == prefix + chain
                        and "-j" in tokens
                        and tokens[tokens.index("-j") + 1] in accept_targets
                        and flag in tokens
                        and tokens[tokens.index(flag) + 1] == iface
                    ):
                        return False
    return True


def runtime_matches_plan(runtime, plan, *, require_active=True, original=None):
    """Check both families and every user OUTPUT accept, beyond UI status text."""
    allowed_ifaces = {"lo", *plan["interfaces"]}
    blocked_ifaces = set(plan.get("blocked_interfaces", []))
    if require_active and introduced_interface_fences(
        runtime, original or {"4": [], "6": []}, allowed_ifaces
    ):
        return False
    if require_active and not interface_fences_ordered(
        runtime, blocked_ifaces, require_present=True
    ):
        return False
    allowed_endpoints = {
        (str(ipaddress.ip_address(ip)), str(int(port)))
        for ip, port in plan["endpoints"]
    }
    for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-")):
        rows = runtime[family]
        if require_active and not all(
            any(row.startswith(f":{chain} DROP ") for row in rows)
            for chain in ("INPUT", "OUTPUT")
        ):
            return False
        rules = [shlex.split(row) for row in rows if row.startswith("-A " + prefix)]
        accept_targets = {"ACCEPT", prefix + "limit-accept"}

        def option(tokens, key):
            if key not in tokens:
                return None
            index = tokens.index(key)
            return tokens[index + 1] if index + 1 < len(tokens) else None

        for iface in allowed_ifaces if require_active else ():
            for direction, flag in (("input", "-i"), ("output", "-o")):
                if not any(
                    tokens[1] == prefix + direction
                    and option(tokens, flag) == iface
                    and option(tokens, "-j") == "ACCEPT"
                    and "!" not in tokens
                    for tokens in rules
                ):
                    return False
        for tokens in rules:
            if (
                tokens[1] != prefix + "output"
                or option(tokens, "-j") not in accept_targets
            ):
                continue
            if "!" in tokens:
                return False
            if option(tokens, "-o") in allowed_ifaces | blocked_ifaces:
                continue
            try:
                destination = ipaddress.ip_network(option(tokens, "-d"), strict=False)
                endpoint = (str(destination.network_address), option(tokens, "--dport"))
                if (
                    destination.prefixlen == destination.max_prefixlen
                    and option(tokens, "-p") == "udp"
                    and endpoint in allowed_endpoints
                ):
                    continue
            except (ValueError, TypeError):
                pass
            return False
    return True


def _iptables_line(tokens):
    # Restore input is not a shell script: use xtables double-quote syntax.
    def quote(token):
        if not token or any(c.isspace() or c in "\\\"'" for c in token):
            return '"' + token.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return token

    return " ".join(quote(token) for token in tokens)


def _runtime_row(row):
    """Normalize known xtables defaults without interpreting option values."""
    if row.startswith(":"):
        return re.sub(r"\[\d+:\d+\]", "[0:0]", row)
    tokens = shlex.split(row)
    aliases = {
        "--source": "-s",
        "--destination": "-d",
        "--protocol": "-p",
        "--source-port": "--sport",
        "--destination-port": "--dport",
    }
    arity = {
        key: 1
        for key in (
            "-s",
            "-d",
            "-i",
            "-o",
            "-p",
            "-m",
            "-j",
            "--dport",
            "--sport",
            "--dports",
            "--sports",
            "--ports",
            "--ctstate",
            "--state",
            "--limit",
            "--limit-burst",
            "--comment",
            "--log-prefix",
            "--log-level",
            "--reject-with",
            "--icmp-type",
            "--icmpv6-type",
            "--rt-type",
            "--hl-eq",
            "--seconds",
            "--hitcount",
            "--name",
            "--mask",
            "--mac-source",
            "--uid-owner",
            "--gid-owner",
        )
    }
    arity["--tcp-flags"] = 2
    arity.update(
        {
            key: 0
            for key in (
                "--syn",
                "-f",
                "--set",
                "--update",
                "--rcheck",
                "--rsource",
                "--rdest",
                "--reap",
                "--log-tcp-sequence",
                "--log-tcp-options",
                "--log-ip-options",
                "--log-uid",
            )
        }
    )
    groups, index = [], 2
    while index < len(tokens):
        inverted = tokens[index] == "!"
        if inverted:
            index += 1
        if index >= len(tokens):
            return _iptables_line(tokens)
        key = aliases.get(tokens[index], tokens[index])
        count = arity.get(key)
        if count is None or index + count >= len(tokens):
            return _iptables_line(tokens)  # Opaque administrator extension: preserve.
        groups.append((inverted, key, tokens[index + 1 : index + 1 + count]))
        index += count + 1
    protocol = next(
        (values[0] for inv, key, values in groups if key == "-p" and not inv), None
    )
    recent = any(
        key == "-m" and values == ["recent"] for inv, key, values in groups if not inv
    )
    destination_recent = any(key == "--rdest" for _inv, key, _values in groups)
    header, matches, target = {}, [], []
    for inverted, key, values in groups:
        value = values[0] if values else None
        if not inverted:
            if (
                key == "-m"
                and value in {"tcp", "udp", "icmp", "icmp6"}
                and (value == protocol or value == "icmp6" and protocol == "ipv6-icmp")
            ):
                continue
            if (key, value) in {
                ("--limit-burst", "5"),
                ("--log-level", "4"),
                ("--log-level", "warning"),
                ("--reject-with", "icmp-port-unreachable"),
                ("--reject-with", "icmp6-port-unreachable"),
            }:
                continue
            if (
                recent
                and not destination_recent
                and (key == "--rsource" or key == "--name" and value == "DEFAULT")
            ):
                continue
            if recent and not destination_recent and key == "--mask":
                try:
                    mask = ipaddress.ip_address(value)
                    if int(mask) == 2**mask.max_prefixlen - 1:
                        continue
                except ValueError:
                    pass
        if key in {"-s", "-d"}:
            network = ipaddress.ip_network(value, strict=False)
            if network.prefixlen == 0 and not inverted:
                continue
            values = [str(network)]
        if key == "--limit" and value.endswith("/min"):
            values = [value[:-4] + "/minute"]
        group = (["!"] if inverted else []) + [key, *values]
        if key in {"-s", "-d", "-i", "-o", "-p"}:
            if key in header:
                return _iptables_line(tokens)
            header[key] = group
        elif key == "-j" or key.startswith("--log-") or key == "--reject-with":
            target.extend(group)
        else:
            matches.extend(group)
    return _iptables_line(
        tokens[:2]
        + [
            token
            for key in ("-s", "-d", "-i", "-o", "-p")
            for token in header.get(key, ())
        ]
        + matches
        + target
    )


def _ordered_runtime(rows):
    return sorted(_runtime_row(row) for row in rows if row.startswith(":")) + sorted(
        (_runtime_row(row) for row in rows if row.startswith("-A ")),
        key=lambda row: shlex.split(row)[1],
    )


class NativeUfw:
    def prepare(self, arguments, current, *, original=None):
        """Use genuine UFW serialization in private files, with live writes off.

        Only the SnapshotStore later applies these pre-journaled destinations.
        No frontend stop/start, reload, kernel write or live file write occurs.
        """
        import gettext
        import ufw.frontend

        gettext.install("ufw")
        with (
            tempfile.TemporaryDirectory(prefix="netmon-ufw-plan-") as temporary,
            _ufw_output(),
        ):
            ui = ufw.frontend.UFWFrontend(False)
            paths = {}
            for name in OBSERVED:
                path = Path(temporary) / name.lstrip("/")
                path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                path.write_bytes(base64.b64decode(current["files"][name]["data"]))
                path.chmod(current["files"][name]["mode"])
                paths[name] = path
            for key, name in list(ui.backend.files.items()):
                if name in paths:
                    ui.backend.files[key] = str(paths[name])
            # The UFW rule engine may only serialize its in-memory rules here.
            ui.backend.is_enabled = lambda: False
            # UFW's initcaps() creates temporary kernel chains. Planning must
            # never probe by mutation. Only preserve already deployed limit
            # helper chains; this command whitelist never creates LIMIT rules.
            ui.backend.caps = {
                "limit": {
                    family: any(
                        row.startswith(":" + prefix + "user-limit ")
                        for row in current["runtime"][family]
                    )
                    for family, prefix in (("4", "ufw-"), ("6", "ufw6-"))
                }
            }
            if arguments[:1] == ["default"]:
                ui.backend.set_default_policy(arguments[1], arguments[2])
                # This includes policy-dependent logging, including new chains.
                ui.backend._write_rules(False)
                ui.backend._write_rules(True)
            elif arguments == ["--force", "enable"]:
                return current  # ready() already requires active dual-family UFW.
            else:
                try:
                    parsed = ufw.frontend.parse_command(["ufw", *arguments])
                    if (
                        len(arguments) == 5
                        and arguments[:2] == ["delete", "deny"]
                        and arguments[3] == "on"
                    ):
                        if original is None:
                            raise SnapshotError(
                                "Original snapshot required for fence cleanup"
                            )
                        # Parse the protected original with UFW, retaining exact
                        # original comments and multiplicity. Remove all added
                        # matches, including duplicates from earlier versions.
                        current_rules = ui.backend.rules, ui.backend.rules6
                        original_paths = {}
                        for key, name in (
                            ("rules", "/etc/ufw/user.rules"),
                            ("rules6", "/etc/ufw/user6.rules"),
                        ):
                            path = Path(temporary) / (key + "-original")
                            path.write_bytes(
                                base64.b64decode(original["files"][name]["data"])
                            )
                            original_paths[key] = ui.backend.files[key]
                            ui.backend.files[key] = str(path)
                        ui.backend.rules, ui.backend.rules6 = [], []
                        ui.backend._read_rules()
                        originals = ui.backend.rules, ui.backend.rules6
                        ui.backend.files.update(original_paths)
                        ui.backend.rules, ui.backend.rules6 = current_rules
                        for v6, rules, old_rules in zip(
                            (False, True), current_rules, originals
                        ):
                            rule = parsed.data["rule"].dup_rule()
                            rule.set_v6(v6)
                            keep = [r for r in old_rules if rule.match(r) in (0, -2)]
                            retained = []
                            for existing in rules:
                                if rule.match(existing) not in (0, -2):
                                    retained.append(existing)
                                    continue
                                index = next(
                                    (
                                        i
                                        for i, old in enumerate(keep)
                                        if existing.match(old) == 0
                                    ),
                                    None,
                                )
                                if index is not None:
                                    retained.append(existing)
                                    keep.pop(index)
                            if keep:
                                raise SnapshotError(
                                    "Original deny rule missing; inspection required",
                                    "conflict",
                                )
                            rules[:] = retained
                            ui.backend._write_rules(v6)
                    elif arguments[:1] == ["allow"] or (
                        arguments[:3] == ["insert", "1", "deny"]
                        and arguments[4:5] == ["on"]
                    ):
                        # UFW's frontend replaces a matching opposite action,
                        # and insert skips even an existing opposite action.
                        # Preserve user rules: serialize an additional grant or
                        # a leading temporary fence in these private copies.
                        # No live backend method is called here.
                        for v6, rules in (
                            (False, ui.backend.rules),
                            (True, ui.backend.rules6),
                        ):
                            iptype = parsed.data["iptype"]
                            if iptype not in ("both", "v6" if v6 else "v4"):
                                continue
                            rule = parsed.data["rule"].dup_rule()
                            rule.set_v6(v6)
                            insert = arguments[:2] == ["insert", "1"]
                            candidates = rules
                            if not any(
                                rule.match(existing) in (0, -2)
                                for existing in candidates
                            ):
                                if insert:
                                    rules.insert(0, rule)
                                else:
                                    rules.append(rule)
                                ui.backend._write_rules(v6)
                    else:
                        ui.do_action(
                            parsed.action,
                            parsed.data.get("rule", ""),
                            parsed.data.get("iptype", ""),
                            parsed.force,
                        )
                except SystemExit:
                    raise SnapshotError("Private UFW plan rejected") from None
            files = {}
            for name, path in paths.items():
                data = path.read_bytes()
                files[name] = {
                    **current["files"][name],
                    "data": base64.b64encode(data).decode(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            runtime = {
                family: list(rows) for family, rows in current["runtime"].items()
            }
            for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
                for name in (
                    "user.rules" if family == "4" else "user6.rules",
                    "after.rules" if family == "4" else "after6.rules",
                ):
                    path = "/etc/ufw/" + name
                    if files[path] == current["files"][path]:
                        continue
                    table, rows = None, []
                    for row in paths[path].read_text().splitlines():
                        if row.startswith("*"):
                            table = row
                        elif row == "COMMIT":
                            table = None
                        elif table == "*filter" and row.startswith(
                            (":" + prefix, "-A " + prefix, "-I " + prefix)
                        ):
                            if row.startswith("-I "):
                                tokens = shlex.split(row)
                                chain = tokens[1]
                                position = next(
                                    (
                                        i
                                        for i, existing in enumerate(rows)
                                        if existing.startswith("-A " + chain + " ")
                                    ),
                                    len(rows),
                                )
                                rows.insert(
                                    position, _iptables_line(["-A", *tokens[1:]])
                                )
                            else:
                                rows.append(row)
                    chains = {row.split()[0][1:] for row in rows if row.startswith(":")}
                    runtime[family] = [
                        row
                        for row in runtime[family]
                        if (
                            row.split()[0][1:]
                            if row.startswith(":")
                            else shlex.split(row)[1]
                        )
                        not in chains
                    ] + rows
                if arguments[:1] == ["default"]:
                    direction = "input" if arguments[2] == "incoming" else "output"
                    chain = direction.upper()
                    target = "DROP" if arguments[1] == "deny" else "ACCEPT"
                    updated = []
                    for row in runtime[family]:
                        if row.startswith(":" + chain + " "):
                            row = f":{chain} {target} [0:0]"
                        if row.startswith(
                            (
                                f"-A {prefix}reject-{direction} ",
                                f"-A {prefix}track-{direction} ",
                            )
                        ):
                            continue
                        if row.startswith(f"-A {prefix}skip-to-policy-{direction} "):
                            row = f"-A {prefix}skip-to-policy-{direction} -j {target}"
                        updated.append(row)
                    if target == "ACCEPT":
                        updated.extend(
                            f"-A {prefix}track-{direction} -p {proto} -m conntrack --ctstate NEW -j ACCEPT"
                            for proto in ("tcp", "udp")
                        )
                    runtime[family] = updated
            return {
                "files": files,
                "runtime": {
                    family: _ordered_runtime(rows) for family, rows in runtime.items()
                },
            }

    def command(self, arguments):
        """Read-only UFW adapter. Mutations require a durable prepared intent."""
        if arguments not in (["status"], ["status", "verbose"], ["status", "numbered"]):
            raise SnapshotError("Native UFW mutation requires a prepared transaction")
        import gettext
        import ufw.frontend

        gettext.install("ufw")
        try:
            with _ufw_output():
                ui = ufw.frontend.UFWFrontend(False)
                parsed = ufw.frontend.parse_command(["ufw", *arguments])
                result = ui.do_action(
                    parsed.action,
                    parsed.data.get("rule", ""),
                    parsed.data.get("iptype", ""),
                    parsed.force,
                )
            return 0, str(result or "")
        except (Exception, SystemExit):
            return 1, "UFW status unavailable"

    def ready(self):
        import ufw.frontend

        rc, text = self.command(["status", "verbose"])
        with _ufw_output():
            backend = ufw.frontend.UFWFrontend(False).backend
            ipv6_enabled = backend.use_ipv6()
            persistently_enabled = backend.is_enabled()
        return (
            rc == 0
            and "Status: active" in text
            and ipv6_enabled
            and persistently_enabled
            and all(self.runtime()[family] for family in ("4", "6"))
        )

    def preflight(self, plan):
        if self.legacy_block_present():
            raise SnapshotError(
                "Existing Killswitch has no active protected predecessor", "no_snapshot"
            )
        self.manual_review_check()
        runtime = self.runtime()
        if not outgoing_rules_match_plan(runtime, plan):
            raise SnapshotError("Incompatible outbound user rules", "preflight")

    def legacy_block_present(self):
        # Independent of the next tunnel/endpoint plan. A previous legacy
        # Killswitch must never become the claimed OFF predecessor of a new one.
        from netmon.features import firewall_controller as controller

        rc, text = self.command(["status", "verbose"])
        return (
            rc == 0
            and controller.ufw_default_policy_matches(text, outgoing="deny")
            and all(
                controller.ufw_has_interface_rule(text, "lo", direction)
                for direction in ("in", "out")
            )
        )

    def manual_review_check(self, *, legacy=True):
        from netmon.features.firewall_controller import (
            _is_global_block,
            parse_ufw_structured_rule,
        )

        if self.legacy_block_present():
            raise SnapshotError(
                (
                    "Legacy Killswitch still requires manual repair"
                    if legacy
                    else "Active or partial Killswitch still requires manual repair"
                ),
                "pending",
            )
        rc, text = self.command(["status", "verbose"])
        if rc or any(
            _is_global_block(parse_ufw_structured_rule(row))
            for row in text.splitlines()
        ):
            raise SnapshotError("Global firewall blocks still present", "pending")
        for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
            for row in self.runtime()[family]:
                tokens = shlex.split(row)
                if tokens[:2] in (
                    ["-A", prefix + "user-input"],
                    ["-A", prefix + "user-output"],
                ):
                    if tokens[2:] in (["-j", "DROP"], ["-j", "REJECT"]):
                        raise SnapshotError(
                            "Global live firewall block still present", "pending"
                        )

    def verify_interface(self, name):
        from netmon.core.nm_ownership import OwnershipStore

        OwnershipStore().verify_interface(name)

    def verify_enabled(self, plan, *, original=None, allow_empty_plan=False):
        from types import SimpleNamespace
        from netmon.features import firewall_controller as controller

        rc, text = self.command(["status", "verbose"])
        app = SimpleNamespace(
            _ufw_status_is_active=controller.ufw_status_is_active,
            _ufw_default_policy_matches=controller.ufw_default_policy_matches,
            _ufw_has_interface_rule=controller.ufw_has_interface_rule,
            _ufw_has_endpoint_rule=controller.ufw_has_endpoint_rule,
        )
        if (
            rc != 0
            or not controller.verify_killswitch_rules(
                app,
                text,
                True,
                plan["interfaces"],
                plan["endpoints"],
                allow_empty_plan=allow_empty_plan,
            )[0]
        ):
            return False
        for name in plan["interfaces"]:
            if name in {iface for _index, iface in socket.if_nameindex()}:
                self.verify_interface(name)
        return runtime_matches_plan(self.runtime(), plan, original=original)

    @staticmethod
    def _execute(arguments, data=None):
        # The privileged helper is single-threaded. Do not leave a kernel writer
        # alive after its journal/lock-owning parent was killed.
        parent = os.getpid()
        libc = ctypes.CDLL(None, use_errno=True)

        def parent_lifetime():
            if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
                os.kill(os.getpid(), signal.SIGKILL)

        result = subprocess.run(
            arguments,
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=25,
            check=False,
            preexec_fn=parent_lifetime,
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        if result.returncode or len(result.stdout) > 4 * MAX_FILE:
            raise SnapshotError("Kernel firewall operation failed")
        return result.stdout.decode()

    def runtime(self):
        result = {}
        for family, program, prefix in (
            ("4", "/usr/sbin/iptables-save", "ufw-"),
            ("6", "/usr/sbin/ip6tables-save", "ufw6-"),
        ):
            rows = self._execute([program, "-t", "filter"]).splitlines()
            result[family] = [
                re.sub(r"\[\d+:\d+\]", "[0:0]", line)
                for line in rows
                if (
                    line.startswith(":" + prefix)
                    or any(
                        line.startswith(":" + chain + " ")
                        for chain in ("INPUT", "OUTPUT", "FORWARD")
                    )
                    or line.startswith("-A " + prefix)
                )
            ]
            if not any(
                line.startswith(":" + prefix + "user-output ")
                for line in result[family]
            ):
                raise SnapshotError("Missing UFW address family", "inactive")
            result[family] = _ordered_runtime(result[family])
        return result

    def restore(self, runtime):
        current = self.runtime()
        failures = []
        for family, program in (
            ("4", "/usr/sbin/iptables-restore"),
            ("6", "/usr/sbin/ip6tables-restore"),
        ):
            rows = runtime[family]
            if any(
                not isinstance(row, str)
                or any(ord(c) < 32 for c in row)
                or not row.startswith(
                    (
                        ":INPUT ",
                        ":OUTPUT ",
                        ":FORWARD ",
                        ":ufw-",
                        ":ufw6-",
                        "-A ufw-",
                        "-A ufw6-",
                    )
                )
                for row in rows
            ):
                raise SnapshotError("Invalid kernel snapshot")
            definitions = [line for line in rows if line.startswith(":")]
            chains = [
                line.split()[0][1:]
                for line in definitions
                if line.startswith((":ufw-", ":ufw6-"))
            ]
            current_chains = {
                line.split()[0][1:]
                for line in current[family]
                if line.startswith((":ufw-", ":ufw6-"))
            }
            extra = sorted(current_chains - set(chains))
            payload = "\n".join(
                [
                    "*filter",
                    *definitions,
                    *(":" + chain + " - [0:0]" for chain in extra),
                    *("-F " + chain for chain in [*chains, *extra]),
                    *(line for line in rows if line.startswith("-A ")),
                    *("-X " + chain for chain in extra),
                    "COMMIT",
                    "",
                ]
            )
            try:
                self._execute([program, "--wait", "5", "--noflush"], payload.encode())
            except Exception as exc:
                failures.append(exc)
        if failures:
            raise SnapshotError(
                "One or both address-family commits failed"
            ) from failures[0]


@contextmanager
def _ufw_lock(timeout=10):
    fd = os.open(
        "/run/ufw.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600
    )
    try:
        _check(os.fstat(fd), 0)
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise SnapshotError("UFW lock wait timed out", "busy") from None
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        yield
    finally:
        os.close(fd)


def main():
    if (
        os.geteuid() != 0
        or os.path.abspath(__file__) != HELPER
        or not trusted_helper_available()
    ):
        return 1
    # The fixed package tree was checked above; never add a user-controlled path.
    sys.path.insert(0, "/usr/lib/netmon")
    sys.dont_write_bytecode = True
    os.environ.clear()
    os.environ.update(PATH="/usr/sbin:/usr/bin:/sbin:/bin", LANG="C", LC_ALL="C")
    try:
        if len(sys.argv) == 2 and sys.argv[1] == "capabilities":
            print(json.dumps({"protocol": PROTOCOL, "prepared_commands": True}))
            return 0
        if len(sys.argv) != 2 or sys.argv[1] not in {
            "begin",
            "command",
            "commit",
            "recovery",
            "restore",
            "state",
            "acknowledge",
            "abort_unmodified",
            "removal",
        }:
            raise SnapshotError("Invalid operation")
        data = sys.stdin.buffer.read(65537)
        if len(data) > 65536:
            raise SnapshotError("Request too large")
        payload = json.loads(data)
        with _ufw_lock():
            store = SnapshotStore(NativeUfw())
            operation = sys.argv[1]
            if operation == "begin":
                result = store.begin(payload)
            elif operation == "command":
                result = store.command(payload["token"], payload["arguments"])
            elif operation in {"commit", "recovery"}:
                result = getattr(store, operation)(payload["token"])
            else:
                if payload != {}:
                    raise SnapshotError("Unexpected payload")
                result = getattr(store, operation)()
        print(json.dumps({**result, "protocol": PROTOCOL}))
        return 0
    except SnapshotError as exc:
        print(json.dumps({"protocol": PROTOCOL, "error": exc.code}))
        return 1
    except Exception:
        print(json.dumps({"protocol": PROTOCOL, "error": "snapshot_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
