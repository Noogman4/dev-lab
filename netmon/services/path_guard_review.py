"""User-level PATH finding reviews; never grants privileged authority."""

import errno
import fcntl
import grp
import hashlib
import json
import os
from pathlib import Path
import pwd
import secrets
import stat
from datetime import datetime, timezone
from contextlib import contextmanager

GROUP_WRITE = "PATH-Verzeichnis ist gruppenbeschreibbar."
EARLY = "Ungewöhnlicher PATH-Eintrag steht sehr weit vorne."
RULES = {GROUP_WRITE: "group_write", EARLY: "early_path"}
MAX_BYTES = 1_000_000


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def directory_fd(path, *, create_private=False):
    """Anchor every path component, rejecting links; only create state dirs."""
    if not os.path.isabs(path):
        raise ValueError("Absoluter Verzeichnispfad erforderlich.")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = Path(os.path.normpath(path)).parts[1:]
        for part in parts:
            try:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
            except FileNotFoundError:
                if not create_private:
                    raise
                os.mkdir(part, 0o700, dir_fd=fd)
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
            os.close(fd)
            fd = child
        result, fd = fd, None
        return result
    finally:
        if fd is not None:
            os.close(fd)


def acl_snapshot(fd):
    result = {}
    for name in ("system.posix_acl_access", "system.posix_acl_default"):
        try:
            result[name] = os.getxattr(fd, name).hex()
        except OSError as exc:
            if exc.errno not in {errno.ENODATA, errno.ENOTSUP}:
                raise
            result[name] = ""
    return result


def permissions_snapshot(path):
    """Bind reviews to path identity, all ancestors, ACLs and NSS group data."""
    if not os.path.isabs(path) or os.path.normpath(path) != path:
        raise ValueError("Nur eindeutige absolute Pfade können bestätigt werden.")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    chain = []
    try:
        for part in (None, *Path(path).parts[1:]):
            if part is not None:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                os.close(fd)
                fd = child
            info = os.fstat(fd)
            if info.st_mode & stat.S_IWOTH:
                raise ValueError(
                    "Ein übergeordnetes Verzeichnis ist allgemein beschreibbar."
                )
            group = grp.getgrgid(info.st_gid)
            members = sorted(
                set(group.gr_mem)
                | {p.pw_name for p in pwd.getpwall() if p.pw_gid == info.st_gid}
            )
            identities = [
                (account.pw_name, account.pw_uid, account.pw_gid)
                for account in (pwd.getpwnam(name) for name in members)
            ]
            chain.append(
                {
                    "dev": info.st_dev,
                    "ino": info.st_ino,
                    "uid": info.st_uid,
                    "gid": info.st_gid,
                    "mode": stat.S_IMODE(info.st_mode),
                    "acl": acl_snapshot(fd),
                    "group": group.gr_name,
                    "members": members,
                    "member_ids": identities,
                }
            )
        if chain[-1]["uid"] != os.geteuid():
            raise ValueError(
                "Nur eigene PATH-Verzeichnisse können bestätigt oder korrigiert werden."
            )
        return chain
    finally:
        os.close(fd)


class PathGuardReview:
    def __init__(self, path=None):
        base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
        self.path = (
            Path(path)
            if path is not None
            else Path(base) / "netmon/path-guard/reviews.json"
        )

    def _store_fd(self, create=False):
        fd = directory_fd(str(self.path.parent), create_private=create)
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            os.close(fd)
            raise ValueError(
                "Bestätigungen benötigen einen eigenen privaten Speicherordner (0700)."
            )
        return fd

    @contextmanager
    def locked(self):
        directory = self._store_fd(create=True)
        fd = None
        try:
            fd = os.open(
                self.path.name + ".lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600,
                dir_fd=directory,
            )
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise ValueError("Unsichere Bestätigungssperre.")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError(
                    "Eine andere Bearbeitung läuft; bitte anschließend erneut prüfen."
                ) from exc
            yield
        finally:
            if fd is not None:
                os.close(fd)
            os.close(directory)

    def load(self):
        try:
            directory = self._store_fd()
        except FileNotFoundError:
            return {}
        try:
            try:
                fd = os.open(
                    self.path.name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
            except FileNotFoundError:
                return {}
            try:
                info = os.fstat(fd)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600
                ):
                    raise ValueError(
                        "Unsicherer Bestätigungsspeicher; keine Ausnahmen übernommen."
                    )
                with os.fdopen(fd, "rb", closefd=False) as handle:
                    data = handle.read(MAX_BYTES + 1)
                after = os.fstat(fd)
                if len(data) > MAX_BYTES or (info.st_size, info.st_mtime_ns) != (
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    raise ValueError(
                        "Bestätigungsspeicher während des Lesens verändert."
                    )
            finally:
                os.close(fd)
        finally:
            os.close(directory)
        saved = json.loads(data)
        if (
            not isinstance(saved, dict)
            or saved.get("version") != 1
            or not isinstance(saved.get("records"), dict)
            or len(saved["records"]) > 500
        ):
            raise ValueError("Ungültiger Bestätigungsspeicher.")
        for key, record in saved["records"].items():
            if not isinstance(record, dict) or set(record) != {
                "fingerprint",
                "target",
                "rule",
                "time",
                "active",
            }:
                raise ValueError("Ungültige Bestätigung.")
            if (
                any(not isinstance(record[k], str) for k in record if k != "active")
                or type(record["active"]) is not bool
                or len(key) != 64
                or len(record["fingerprint"]) != 64
                or record["rule"] not in RULES.values()
            ):
                raise ValueError("Ungültige Bestätigung.")
        return saved["records"]

    def save(self, records):
        if len(records) > 500:
            raise ValueError(
                "Zu viele Bestätigungen; alte Einträge zuerst zurücknehmen."
            )
        data = json.dumps({"version": 1, "records": records}, sort_keys=True).encode()
        if len(data) > MAX_BYTES:
            raise ValueError("Bestätigungsspeicher zu groß.")
        directory = self._store_fd(create=True)
        temp = ".review-" + secrets.token_hex(12)
        try:
            fd = os.open(
                temp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                with os.fdopen(fd, "wb", closefd=False) as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(temp, self.path.name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temp, dir_fd=directory)
            except FileNotFoundError:
                pass
            os.close(directory)

    def enrich(self, result):
        error = ""
        try:
            records = self.load()
        except (OSError, ValueError, UnicodeError) as exc:
            records = {}
            error = str(exc)
        rows = []
        for kind, items in (
            ("path", result["path_findings"]),
            ("profile", result["profile_findings"]),
        ):
            for item in items:
                if item["severity"] not in {"medium", "high"}:
                    continue
                target = item.get("entry", item.get("path", ""))
                issues = item.get("issues") or [
                    "Shell-Profil prüfen; Details im Prüfbericht."
                ]
                for issue in issues:
                    rule = RULES.get(issue, issue)
                    key = digest([kind, target, item.get("index"), rule])
                    row = {
                        "id": key,
                        "target": target,
                        "rule": rule,
                        "issue": issue,
                        "severity": item["severity"],
                        "state": "offen",
                        "can_accept": False,
                        "can_repair": False,
                        "has_review": key in records,
                        "fingerprint": "",
                        "explanation": issue,
                        "snapshot": [],
                    }
                    if (
                        kind == "path"
                        and item["severity"] == "medium"
                        and issue in RULES
                    ):
                        row["explanation"] += (
                            "\nGruppenmitglieder können hier Programme hinzufügen oder austauschen. Bei gemeinsam genutzten Entwicklungsordnern kann dies beabsichtigt sein."
                            if rule == "group_write"
                            else "\nFrühe PATH-Einträge können gleichnamige Systemprogramme überdecken. Python-Umgebungen und nvm stehen häufig absichtlich vorne; ihre Herkunft und Zugriffsrechte müssen dennoch geprüft werden."
                        )
                        try:
                            snapshot = permissions_snapshot(target)
                            row["snapshot"] = snapshot
                            row["fingerprint"] = digest(
                                [key, result["path_entries"], snapshot]
                            )
                            row["can_accept"] = not bool(error)
                            if any(any(part["acl"].values()) for part in snapshot):
                                row["can_accept"] = False
                                row[
                                    "explanation"
                                ] += "\nErweiterte ACLs: keine einfache Bestätigung möglich; Zugriffsfreigaben zuerst gesondert prüfen."
                            row["can_repair"] = rule == "group_write" and not any(
                                any(part["acl"].values()) for part in snapshot
                            )
                            if snapshot[-1]["mode"] & 0o7000:
                                row["can_repair"] = False
                                row[
                                    "explanation"
                                ] += "\nBesondere Rechtebits gesetzt: keine automatische Rechteänderung; gemeinsame Verzeichnisnutzung zuerst gesondert prüfen."
                            row["explanation"] += (
                                "\nEigentümer-UID: "
                                + str(snapshot[-1]["uid"])
                                + "; Gruppe: "
                                + snapshot[-1]["group"]
                                + "; Mitglieder laut NSS: "
                                + ", ".join(snapshot[-1]["members"])
                                + "\nEine Bestätigung akzeptiert diesen Hinweis; sie behebt keine Rechte und prüft keine Programminhalte."
                            )
                            if (
                                row["can_accept"]
                                and records.get(key, {}).get("active") is True
                                and records.get(key, {}).get("fingerprint")
                                == row["fingerprint"]
                            ):
                                row["state"] = "geprüft / Risiko akzeptiert"
                            elif key in records:
                                row["state"] = "offen / Bestätigung veraltet"
                            if key in records:
                                row["explanation"] += (
                                    "\nGespeicherte Bestätigung: "
                                    + records[key]["time"]
                                )
                        except (OSError, ValueError, KeyError) as exc:
                            row[
                                "explanation"
                            ] += "\nBestätigung/Korrektur nicht verfügbar: " + str(exc)
                    else:
                        row[
                            "explanation"
                        ] += "\nNicht bestätigbar; Ursache prüfen und beheben. Keine automatische Bearbeitung von Shell-Profilen."
                    rows.append(row)
        current = {r["id"] for r in rows}
        accepted = {
            r["id"] for r in rows if r["state"] == "geprüft / Risiko akzeptiert"
        }
        invalid = {
            key
            for key, record in records.items()
            if record["active"] and key not in accepted
        }
        if invalid:
            try:
                with self.locked():
                    live = self.load()
                    changed = False
                    for key in invalid:
                        # Do not overwrite a newer decision by another instance.
                        if live.get(key) == records[key]:
                            live[key] = dict(live[key], active=False)
                            changed = True
                    if changed:
                        self.save(live)
            except (OSError, ValueError) as exc:
                error = "Veraltete Bestätigungen nicht sicher gespeichert: " + str(exc)
                for row in rows:
                    row["can_accept"] = False
        for key, record in records.items():
            if key not in current:
                rows.append(
                    {
                        "id": key,
                        "target": record["target"],
                        "rule": record["rule"],
                        "issue": "Gespeicherte Bestätigung",
                        "severity": "info",
                        "state": "nicht mehr gemeldet",
                        "can_accept": False,
                        "can_repair": False,
                        "has_review": True,
                        "fingerprint": "",
                        "explanation": "Aktuell nicht gemeldet; dies ist kein Nachweis einer Reparatur. Bestätigung kann zurückgenommen werden.",
                    }
                )
        opened = [
            r
            for r in rows
            if r["severity"] in {"high", "medium"}
            and r["state"] != "geprüft / Risiko akzeptiert"
        ]
        result["review_items"] = rows
        result["review_summary"] = {
            "high": sum(r["severity"] == "high" for r in opened),
            "medium": sum(r["severity"] == "medium" for r in opened),
            "accepted": sum(r["state"] == "geprüft / Risiko akzeptiert" for r in rows),
            "error": error,
        }
        return result

    def accept(self, result, key, fingerprint):
        row = self._current(result, key, fingerprint)
        if not row["can_accept"]:
            raise ValueError("Dieser Befund kann nicht bestätigt werden.")
        with self.locked():
            records = self.load()
            records[key] = {
                "fingerprint": fingerprint,
                "target": row["target"],
                "rule": row["rule"],
                "time": datetime.now(timezone.utc).isoformat(),
                "active": True,
            }
            self.save(records)

    def revoke(self, key):
        with self.locked():
            records = self.load()
            records.pop(key, None)
            self.save(records)

    @staticmethod
    def _current(result, key, fingerprint):
        row = next((r for r in result["review_items"] if r["id"] == key), None)
        if row is None or not fingerprint or row["fingerprint"] != fingerprint:
            raise ValueError("Befund verändert; zuerst erneut prüfen.")
        return row

    def repair(self, result, key, fingerprint):
        row = self._current(result, key, fingerprint)
        if not row["can_repair"]:
            raise ValueError(
                "Für diesen Befund ist keine sichere automatische Korrektur verfügbar."
            )
        fd = directory_fd(row["target"])
        try:
            info = os.fstat(fd)
            expected = row["snapshot"][-1]
            if (
                info.st_dev,
                info.st_ino,
                info.st_uid,
                info.st_gid,
                stat.S_IMODE(info.st_mode),
                acl_snapshot(fd),
            ) != (
                expected["dev"],
                expected["ino"],
                expected["uid"],
                expected["gid"],
                expected["mode"],
                expected["acl"],
            ):
                raise ValueError("Verzeichnis verändert; keine Rechteänderung.")
            new_mode = expected["mode"] & ~stat.S_IWGRP
            os.fchmod(fd, new_mode)
            if stat.S_IMODE(os.fstat(fd).st_mode) != new_mode:
                raise OSError("Rechteänderung nicht bestätigt; Zustand erneut prüfen.")
        finally:
            os.close(fd)
