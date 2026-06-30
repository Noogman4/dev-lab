from __future__ import annotations

import glob
import os
import shutil
import subprocess
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    try:
        from core.utils import safe_write_json
    except ModuleNotFoundError:

        def safe_write_json(path, data):
            try:
                parent = os.path.dirname(os.path.abspath(path))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                tmp_path = f"{path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as handle:
                    json.dump(
                        data, handle, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    handle.write("\n")
                os.replace(tmp_path, path)
                return True, ""
            except Exception as exc:
                return False, str(exc)


class RepositoryGuardService:
    def __init__(
        self,
        source_patterns: list[str] | None = None,
        *,
        flatpak_runner=None,
        flatpak_available_fn=None,
        file_exists_fn=None,
    ):
        self.source_patterns = list(
            source_patterns
            or [
                "/etc/apt/sources.list",
                "/etc/apt/sources.list.d/*.list",
                "/etc/apt/sources.list.d/*.sources",
            ]
        )
        self.flatpak_runner = flatpak_runner or self._run_flatpak_command
        self.flatpak_available_fn = flatpak_available_fn or self._flatpak_is_available
        self.file_exists_fn = file_exists_fn or os.path.isfile
        self.known_hosts = {
            "deb.debian.org",
            "security.debian.org",
            "archive.ubuntu.com",
            "security.ubuntu.com",
            "ppa.launchpadcontent.net",
            "dl.flathub.org",
            "brave-browser-apt-release.s3.brave.com",
            "download.docker.com",
            "packages.microsoft.com",
            "packages.zorinos.com",
        }
        self.flatpak_status = "unchecked"
        self.allowed_keyring_prefixes = (
            "/usr/share/keyrings/",
            "/etc/apt/keyrings/",
            "/etc/apt/trusted.gpg.d/",
        )

    def scan(self, trustlist: dict | None = None) -> dict:
        sources, errors = self.collect_sources()
        self.apply_trustlist(sources, trustlist)
        findings = self.build_findings(sources, errors)
        summary = self.build_summary(sources, findings, errors)
        return {
            "status": self._status_from_findings(findings, errors),
            "checked_at": self._utc_now(),
            "summary": summary,
            "sources": sources,
            "findings": findings,
            "errors": errors,
        }

    def load_trustlist(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {"trusted_hosts": {}}
        except Exception:
            return {"trusted_hosts": {}}
        if not isinstance(data, dict):
            return {"trusted_hosts": {}}
        data.setdefault("trusted_hosts", {})
        if not isinstance(data.get("trusted_hosts"), dict):
            data["trusted_hosts"] = {}
        return data

    def save_trustlist(self, path: str, trustlist: dict) -> tuple[bool, str]:
        payload = dict(trustlist or {})
        payload.setdefault("trusted_hosts", {})
        return safe_write_json(path, payload)

    def mark_host_trusted(self, source: dict, path: str) -> tuple[bool, str]:
        host = str((source or {}).get("host") or "").strip().lower()
        if not host:
            return False, "Kein Host vorhanden."
        trustlist = self.load_trustlist(path)
        trusted_hosts = dict(trustlist.get("trusted_hosts") or {})
        trusted_hosts[host] = {
            "host": host,
            "uri": str((source or {}).get("uri") or ""),
            "repo_type": str((source or {}).get("repo_type") or ""),
            "trusted_at": self._utc_now(),
        }
        trustlist["trusted_hosts"] = trusted_hosts
        return self.save_trustlist(path, trustlist)

    def remove_host_trusted(self, source: dict, path: str) -> tuple[bool, str]:
        host = str((source or {}).get("host") or "").strip().lower()
        if not host:
            return False, "Kein Host vorhanden."
        trustlist = self.load_trustlist(path)
        trusted_hosts = dict(trustlist.get("trusted_hosts") or {})
        trusted_hosts.pop(host, None)
        trustlist["trusted_hosts"] = trusted_hosts
        return self.save_trustlist(path, trustlist)

    def reset_trustlist(self, path: str) -> tuple[bool, str]:
        return self.save_trustlist(path, {"trusted_hosts": {}})

    def apply_trustlist(self, sources: list[dict], trustlist: dict | None) -> None:
        trusted_hosts = {
            str(host or "").strip().lower()
            for host in dict((trustlist or {}).get("trusted_hosts") or {}).keys()
            if str(host or "").strip()
        }
        for source in list(sources or []):
            host = str(source.get("host") or "").strip().lower()
            source["trusted_host"] = bool(host and host in trusted_hosts)
            if source["trusted_host"]:
                source["trust_state"] = "trusted"
            elif str(source.get("origin_class") or "") == "known":
                source["trust_state"] = "known"
            else:
                source["trust_state"] = "review"

    def collect_sources(self) -> tuple[list[dict], list[dict]]:
        sources: list[dict] = []
        errors: list[dict] = []
        seen_paths: set[str] = set()
        self.flatpak_status = "unchecked"

        for pattern in self.source_patterns:
            matched = self._expand_pattern(pattern)
            if not matched and self._is_explicit_path(pattern):
                errors.append(
                    {
                        "code": "repo_file_missing",
                        "severity": "error",
                        "file_path": pattern,
                        "message": "Repository-Datei nicht gefunden.",
                    }
                )
                continue

            for path in matched:
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                self._collect_sources_from_file(path, sources, errors)

        self._collect_flatpak_sources(sources, errors)
        sources.sort(key=lambda item: (item.get("file_path", ""), item.get("line_no", 0)))
        return sources, errors

    def build_findings(self, sources: list[dict], errors: list[dict]) -> list[dict]:
        findings: list[dict] = []
        duplicate_groups: dict[tuple, list[dict]] = {}

        for source in sources:
            scheme = str(source.get("scheme") or "").strip().lower()
            components = list(source.get("components") or [])
            signed_by = str(source.get("signed_by") or "").strip()
            signed_by_paths = list(source.get("signed_by_paths") or [])
            signed_by_embedded = bool(source.get("signed_by_embedded", False))
            origin_class = str(source.get("origin_class") or "").strip()
            source_kind = str(source.get("kind") or "").strip().lower()
            enabled = bool(source.get("enabled", True))

            if not enabled:
                findings.append(
                    self._finding(
                        source=source,
                        severity="notice",
                        code="repo_disabled_entry",
                        title="Deaktivierter Repository-Eintrag",
                        summary="Quelle ist vorhanden, aber aktuell auskommentiert.",
                    )
                )
                continue

            if source_kind == "flatpak":
                if origin_class == "unknown" and not source.get("trusted_host", False):
                    findings.append(
                        self._finding(
                            source=source,
                            severity="notice",
                            code="repo_flatpak_remote_untrusted_candidate",
                            title="Flatpak-Remote mit Prüfbedarf",
                            summary="Flatpak-Remote ist nicht in der kleinen bekannten Basisliste enthalten.",
                        )
                    )
                else:
                    findings.append(
                        self._finding(
                            source=source,
                            severity="info",
                            code="repo_flatpak_remote_present",
                            title="Flatpak-Remote erkannt",
                            summary="Flatpak-Remote wurde lokal erfasst.",
                        )
                    )
                continue

            if scheme == "http":
                findings.append(
                    self._finding(
                        source=source,
                        severity="warning",
                        code="repo_http_used",
                        title="Repository nutzt HTTP",
                        summary="Paketquelle verwendet unverschluesseltes HTTP.",
                    )
                )

            if source.get("repo_type") == "deb-src":
                findings.append(
                    self._finding(
                        source=source,
                        severity="notice",
                        code="repo_deb_src_enabled",
                        title="Quellpaket-Repository aktiv",
                        summary="`deb-src` ist aktiviert und sollte bewusst gesetzt sein.",
                    )
                )

            if not components:
                findings.append(
                    self._finding(
                        source=source,
                        severity="warning",
                        code="repo_empty_components",
                        title="Repository ohne Komponenten",
                        summary="Der Eintrag enthaelt keine Komponenten.",
                    )
                )

            if origin_class == "unknown" and not source.get("trusted_host", False):
                findings.append(
                    self._finding(
                        source=source,
                        severity="warning",
                        code="repo_unknown_origin",
                        title="Unbekannte Repository-Herkunft",
                        summary="Die Quelle gehoert nicht zur kleinen bekannten Basisliste.",
                    )
                )

            if origin_class == "unknown" and not signed_by:
                findings.append(
                    self._finding(
                        source=source,
                        severity="warning",
                        code="repo_no_signed_by",
                        title="Quelle ohne signed-by-Hinweis",
                        summary="Drittquelle nutzt keinen expliziten Keyring-Hinweis.",
                    )
                )
            elif signed_by and not signed_by_embedded:
                for keyring_path in signed_by_paths or [signed_by]:
                    if not self._is_absolute_keyring_path(keyring_path):
                        findings.append(
                            self._finding(
                                source=source,
                                severity="warning",
                                code="repo_signed_by_unexpected_path",
                                title="signed-by mit ungewöhnlichem Pfad",
                                summary="Der referenzierte Keyring-Pfad ist nicht absolut oder liegt an einem ungewöhnlichen Ort.",
                                details={"keyring_path": keyring_path},
                            )
                        )
                        continue
                    if not self.file_exists_fn(keyring_path):
                        findings.append(
                            self._finding(
                                source=source,
                                severity="warning",
                                code="repo_signed_by_missing_file",
                                title="signed-by-Datei fehlt",
                                summary="Die referenzierte Keyring-Datei ist aktuell nicht vorhanden.",
                                details={"keyring_path": keyring_path},
                            )
                        )
                        continue
                    if not self._is_allowed_keyring_location(keyring_path):
                        findings.append(
                            self._finding(
                                source=source,
                                severity="notice",
                                code="repo_signed_by_unexpected_location",
                                title="Keyring-Datei an ungewöhnlichem Ort",
                                summary="Die referenzierte Keyring-Datei existiert, liegt aber nicht in einem typischen APT-Keyring-Verzeichnis.",
                                details={"keyring_path": keyring_path},
                            )
                        )

            duplicate_key = self._source_identity_key(source)
            duplicate_groups.setdefault(duplicate_key, []).append(source)

        for duplicate_sources in duplicate_groups.values():
            if len(duplicate_sources) < 2:
                continue
            config_fingerprints = {
                self._duplicate_config_fingerprint(source) for source in duplicate_sources
            }
            if len(config_fingerprints) == 1:
                duplicate_code = "repo_duplicate_source"
                duplicate_title = "Doppelte Repository-Quelle"
                duplicate_summary = "Diese Paketquelle ist mehrfach konfiguriert."
            else:
                duplicate_code = "repo_duplicate_source_variant"
                duplicate_title = "Repository mehrfach mit Abweichungen"
                duplicate_summary = (
                    "Diese Paketquelle ist mehrfach vorhanden und nutzt "
                    "abweichende Konfigurationsdetails."
                )
            duplicate_ids = [str(item.get("id") or "") for item in duplicate_sources]
            for source in duplicate_sources:
                findings.append(
                    self._finding(
                        source=source,
                        severity="warning",
                        code=duplicate_code,
                        title=duplicate_title,
                        summary=duplicate_summary,
                        details={
                            "duplicate_source_ids": list(duplicate_ids),
                            "duplicate_count": len(duplicate_sources),
                        },
                    )
                )

        for error in errors:
            findings.append(
                {
                    "id": f"finding:{error.get('code', 'error')}:{error.get('file_path', '-')}",
                    "severity": str(error.get("severity") or "error"),
                    "code": str(error.get("code") or "repo_runtime_error"),
                    "title": "Repository-Dateifehler",
                    "summary": str(error.get("message") or "Unbekannter Fehler."),
                    "source_id": "",
                    "details": {
                        "file_path": error.get("file_path", ""),
                    },
                }
            )

        if self.flatpak_status == "missing":
            findings.append(
                {
                    "id": "finding:repo_flatpak_not_installed",
                    "severity": "info",
                    "code": "repo_flatpak_not_installed",
                    "title": "Flatpak nicht installiert",
                    "summary": "Flatpak-Remotes konnten nicht geprüft werden, da Flatpak nicht verfügbar ist.",
                    "source_id": "",
                    "details": {},
                }
            )

        findings.sort(key=lambda item: (self._severity_rank(item.get("severity")), item["id"]))
        return findings

    def build_summary(
        self, sources: list[dict], findings: list[dict], errors: list[dict]
    ) -> dict:
        summary = {
            "repositories_total": len(sources),
            "findings_total": len(findings),
            "critical": 0,
            "warning": 0,
            "notice": 0,
            "info": 0,
            "errors": len(errors),
        }
        for finding in findings:
            severity = str(finding.get("severity") or "").strip().lower()
            if severity == "error":
                summary["errors"] += 1
            elif severity in summary:
                summary[severity] += 1
        return summary

    def load_baseline(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {}
        except Exception:
            return {}
        if isinstance(data, dict):
            data.setdefault("sources", [])
            return data
        if isinstance(data, list):
            return {"sources": data}
        return {}

    def save_baseline(self, path: str, sources: list[dict]) -> tuple[bool, str]:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
                "+00:00", "Z"
            ),
            "sources": list(sources or []),
        }
        return safe_write_json(path, payload)

    def compare_to_baseline(self, baseline: dict, current: list[dict]) -> dict:
        baseline_sources = list((baseline or {}).get("sources") or [])
        current_sources = list(current or [])

        baseline_map = {
            str(item.get("id") or ""): item
            for item in baseline_sources
            if str(item.get("id") or "")
        }
        current_map = {
            str(item.get("id") or ""): item
            for item in current_sources
            if str(item.get("id") or "")
        }

        new_sources: list[dict] = []
        removed_sources: list[dict] = []
        changed_sources: list[dict] = []
        moved_sources: list[dict] = []
        unchanged_sources: list[dict] = []

        matched_baseline_ids: set[str] = set()
        matched_current_ids: set[str] = set()

        for source_id, current_item in current_map.items():
            baseline_item = baseline_map.get(source_id)
            if baseline_item is None:
                continue
            matched_baseline_ids.add(source_id)
            matched_current_ids.add(source_id)
            if self._source_fingerprint(baseline_item) != self._source_fingerprint(
                current_item
            ):
                changed_sources.append(
                    {
                        "before": baseline_item,
                        "after": current_item,
                        "changed_fields": self._changed_fields(
                            baseline_item,
                            current_item,
                        ),
                    }
                )
            else:
                unchanged_sources.append(current_item)

        remaining_baseline = [
            item
            for source_id, item in baseline_map.items()
            if source_id not in matched_baseline_ids
        ]
        remaining_current = [
            item for source_id, item in current_map.items() if source_id not in matched_current_ids
        ]

        baseline_by_identity = self._group_sources_by_identity(remaining_baseline)
        current_by_identity = self._group_sources_by_identity(remaining_current)
        all_identity_keys = sorted(
            set(baseline_by_identity.keys()) | set(current_by_identity.keys()),
            key=str,
        )

        for identity_key in all_identity_keys:
            baseline_group = sorted(
                baseline_by_identity.get(identity_key, []),
                key=self._baseline_match_sort_key,
            )
            current_group = sorted(
                current_by_identity.get(identity_key, []),
                key=self._baseline_match_sort_key,
            )
            matched_count = min(len(baseline_group), len(current_group))

            for index in range(matched_count):
                before = baseline_group[index]
                after = current_group[index]
                if self._source_fingerprint(before) == self._source_fingerprint(after):
                    moved_sources.append(
                        {
                            "before": before,
                            "after": after,
                        }
                    )
                else:
                    changed_sources.append(
                        {
                            "before": before,
                            "after": after,
                            "changed_fields": self._changed_fields(before, after),
                        }
                    )
                matched_baseline_ids.add(str(before.get("id") or ""))
                matched_current_ids.add(str(after.get("id") or ""))

        for source_id, current_item in current_map.items():
            if source_id not in matched_current_ids:
                new_sources.append(current_item)

        for source_id, baseline_item in baseline_map.items():
            if source_id not in matched_baseline_ids:
                removed_sources.append(baseline_item)

        new_sources.sort(key=lambda item: item.get("id", ""))
        moved_sources.sort(
            key=lambda item: item.get("after", {}).get("id")
            or item.get("before", {}).get("id", "")
        )
        removed_sources.sort(key=lambda item: item.get("id", ""))
        changed_sources.sort(
            key=lambda item: item.get("after", {}).get("id")
            or item.get("before", {}).get("id", "")
        )
        unchanged_sources.sort(key=lambda item: item.get("id", ""))

        return {
            "new": new_sources,
            "removed": removed_sources,
            "changed": changed_sources,
            "moved": moved_sources,
            "unchanged": unchanged_sources,
        }

    def _collect_sources_from_file(
        self, path: str, sources: list[dict], errors: list[dict]
    ) -> None:
        if path.endswith(".sources"):
            self._collect_sources_from_deb822_file(path, sources, errors)
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for line_no, raw_line in enumerate(handle, start=1):
                    parsed = self._parse_list_line(path, line_no, raw_line)
                    if parsed is None:
                        continue
                    if parsed.get("parse_error"):
                        errors.append(
                            {
                                "code": "repo_parse_error",
                                "severity": "error",
                                "file_path": path,
                                "line_no": line_no,
                                "message": parsed["parse_error"],
                                "raw_line": raw_line.rstrip("\n"),
                            }
                        )
                        continue
                    sources.append(parsed)
        except OSError as exc:
            errors.append(
                {
                    "code": "repo_file_unreadable",
                    "severity": "error",
                    "file_path": path,
                    "message": f"Repository-Datei konnte nicht gelesen werden: {exc}",
                }
            )

    def _collect_sources_from_deb822_file(
        self, path: str, sources: list[dict], errors: list[dict]
    ) -> None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except OSError as exc:
            errors.append(
                {
                    "code": "repo_file_unreadable",
                    "severity": "error",
                    "file_path": path,
                    "message": f"Repository-Datei konnte nicht gelesen werden: {exc}",
                }
            )
            return

        blocks = self._split_deb822_blocks(lines)
        for block_index, block in enumerate(blocks, start=1):
            parsed_entries, parse_error = self._parse_deb822_block(path, block_index, block)
            if parse_error:
                errors.append(
                    {
                        "code": "repo_parse_error",
                        "severity": "error",
                        "file_path": path,
                        "line_no": block.get("line_no", 0),
                        "message": parse_error,
                        "raw_block": block.get("raw_block", ""),
                    }
                )
                continue
            sources.extend(parsed_entries)

    def _split_deb822_blocks(self, lines: list[str]) -> list[dict]:
        blocks: list[dict] = []
        current_lines: list[str] = []
        current_start = 1

        for line_no, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            if not stripped:
                if current_lines:
                    blocks.append(
                        {
                            "line_no": current_start,
                            "raw_block": "".join(current_lines).strip(),
                        }
                    )
                    current_lines = []
                current_start = line_no + 1
                continue
            if not current_lines:
                current_start = line_no
            current_lines.append(raw_line)

        if current_lines:
            blocks.append(
                {
                    "line_no": current_start,
                    "raw_block": "".join(current_lines).strip(),
                }
            )
        return blocks

    def _parse_deb822_block(
        self,
        file_path: str,
        block_index: int,
        block: dict,
    ) -> tuple[list[dict], str]:
        fields = self._parse_deb822_fields(str(block.get("raw_block") or ""))
        types = self._split_multivalue_field(fields.get("Types", ""))
        uris = self._split_multivalue_field(fields.get("URIs", ""))
        suites = self._split_multivalue_field(fields.get("Suites", ""))
        components = self._split_multivalue_field(fields.get("Components", ""))
        signed_by = str(fields.get("Signed-By", "") or "").strip()
        signed_by_embedded = self._signed_by_is_embedded_key(signed_by)
        enabled = str(fields.get("Enabled", "yes") or "yes").strip().lower() not in {
            "no",
            "false",
            "0",
        }

        if not types or not uris or not suites:
            return [], (
                f"Deb822-Block ist unvollständig in {file_path}:"
                f"{block.get('line_no', 0)}."
            )

        entries: list[dict] = []
        for repo_type in types:
            for uri in uris:
                parsed_uri = urlparse(uri)
                host = parsed_uri.netloc.lower()
                scheme = parsed_uri.scheme.lower()
                for suite in suites:
                    entries.append(
                        {
                            "id": (
                                f"apt-deb822:{file_path}:{block.get('line_no', 0)}:"
                                f"{block_index}:{repo_type}:{uri}:{suite}"
                            ),
                            "kind": "apt",
                            "format": "deb822",
                            "file_path": file_path,
                            "line_no": int(block.get("line_no", 0) or 0),
                            "enabled": enabled,
                            "raw_block": block.get("raw_block", ""),
                            "raw_line": block.get("raw_block", ""),
                            "repo_type": repo_type,
                            "uri": uri,
                            "suite": suite,
                            "components": list(components),
                            "options": {},
                            "signed_by": signed_by,
                            "signed_by_paths": self._extract_signed_by_paths(signed_by),
                            "signed_by_embedded": signed_by_embedded,
                            "scheme": scheme,
                            "host": host,
                            "origin_class": self._classify_origin(host),
                            "types": list(types),
                            "uris": list(uris),
                            "suites": list(suites),
                        }
                    )
        return entries, ""

    def _parse_deb822_fields(self, raw_block: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        current_key = ""
        for raw_line in str(raw_block or "").splitlines():
            if not raw_line.strip():
                continue
            if raw_line[:1].isspace() and current_key:
                fields[current_key] = (
                    f"{fields.get(current_key, '')} {raw_line.strip()}".strip()
                )
                continue
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            current_key = key.strip()
            fields[current_key] = value.strip()
        return fields

    def _split_multivalue_field(self, value: str) -> list[str]:
        return [part.strip() for part in str(value or "").split() if part.strip()]

    def _parse_list_line(
        self,
        file_path: str,
        line_no: int,
        raw_line: str,
    ) -> dict | None:
        line = str(raw_line or "").rstrip("\n")
        stripped = line.strip()
        if not stripped:
            return None

        enabled = True
        candidate = stripped
        if stripped.startswith("#"):
            enabled = False
            candidate = stripped[1:].strip()
            if not candidate:
                return None

        if not (candidate.startswith("deb ") or candidate.startswith("deb-src ")):
            return None

        tokens = candidate.split()
        if len(tokens) < 3:
            return {
                "parse_error": f"Repository-Zeile ist unvollstaendig in {file_path}:{line_no}.",
            }

        repo_type = tokens[0]
        options, option_tokens = self._parse_options(candidate)
        content = candidate
        if option_tokens:
            content = candidate.replace(option_tokens, "", 1).strip()
        tokens = content.split()

        if len(tokens) < 3:
            return {
                "parse_error": f"Repository-Zeile ist unvollstaendig in {file_path}:{line_no}.",
            }

        repo_type = tokens[0]
        uri = tokens[1]
        suite = tokens[2]
        components = tokens[3:]
        parsed_uri = urlparse(uri)
        host = parsed_uri.netloc.lower()
        scheme = parsed_uri.scheme.lower()

        return {
            "id": f"apt:{file_path}:{line_no}",
            "kind": "apt",
            "format": "list",
            "file_path": file_path,
            "line_no": line_no,
            "enabled": enabled,
            "raw_line": line,
            "repo_type": repo_type,
            "uri": uri,
            "suite": suite,
            "components": components,
            "options": options,
            "signed_by": options.get("signed-by", ""),
            "signed_by_paths": self._extract_signed_by_paths(
                options.get("signed-by", "")
            ),
            "signed_by_embedded": self._signed_by_is_embedded_key(
                options.get("signed-by", "")
            ),
            "scheme": scheme,
            "host": host,
            "origin_class": self._classify_origin(host),
        }

    def _collect_flatpak_sources(self, sources: list[dict], errors: list[dict]) -> None:
        if not self.flatpak_available_fn():
            self.flatpak_status = "missing"
            return

        had_error = False
        had_success = False
        for scope in ("system", "user"):
            try:
                output = self.flatpak_runner(scope)
            except Exception as exc:
                had_error = True
                errors.append(
                    {
                        "code": "repo_flatpak_query_failed",
                        "severity": "error",
                        "file_path": f"flatpak:{scope}",
                        "message": f"Flatpak-Remotes konnten nicht gelesen werden: {exc}",
                    }
                )
                continue

            had_success = True
            sources.extend(self._parse_flatpak_remotes(scope, output))

        if had_error:
            self.flatpak_status = "error"
        elif had_success:
            self.flatpak_status = "available"
        else:
            self.flatpak_status = "missing"

    def _parse_flatpak_remotes(self, scope: str, output: str) -> list[dict]:
        entries: list[dict] = []
        for line_no, raw_line in enumerate(str(output or "").splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            parts = [part.strip() for part in raw_line.split("\t")]
            if len(parts) < 3:
                parts = [part.strip() for part in raw_line.split(None, 2)]
            if len(parts) < 3:
                continue
            name, url, options_text = parts[0], parts[1], parts[2]
            parsed_uri = urlparse(url)
            host = parsed_uri.netloc.lower()
            options_normalized = str(options_text or "").strip().lower()
            enabled = "disabled" not in options_normalized
            entries.append(
                {
                    "id": f"flatpak:{scope}:{name}",
                    "kind": "flatpak",
                    "format": "remote",
                    "file_path": f"flatpak:{scope}",
                    "line_no": line_no,
                    "enabled": enabled,
                    "raw_line": raw_line,
                    "repo_type": "flatpak",
                    "uri": url,
                    "suite": scope,
                    "components": [],
                    "options": {"remote_options": options_text},
                    "signed_by": "",
                    "scheme": parsed_uri.scheme.lower(),
                    "host": host,
                    "origin_class": self._classify_origin(host),
                    "name": name,
                    "scope": scope,
                }
            )
        return entries

    def _parse_options(self, candidate: str) -> tuple[dict, str]:
        option_start = candidate.find("[")
        option_end = candidate.find("]")
        if option_start < 0 or option_end <= option_start:
            return {}, ""

        option_tokens = candidate[option_start : option_end + 1]
        raw_options = option_tokens[1:-1].strip()
        if not raw_options:
            return {}, option_tokens

        options: dict[str, str] = {}
        for token in raw_options.split():
            if "=" in token:
                key, value = token.split("=", 1)
                options[key.strip().lower()] = value.strip()
            else:
                options[token.strip().lower()] = "true"
        return options, option_tokens

    def _extract_signed_by_paths(self, signed_by: str) -> list[str]:
        raw = str(signed_by or "").strip()
        if not raw:
            return []
        if self._signed_by_is_embedded_key(raw):
            return []
        separators_normalized = raw.replace(",", " ")
        return [part.strip() for part in separators_normalized.split() if part.strip()]

    def _signed_by_is_embedded_key(self, signed_by: str) -> bool:
        raw = str(signed_by or "").strip()
        if not raw:
            return False
        return "-----BEGIN PGP PUBLIC KEY BLOCK-----" in raw

    def _expand_pattern(self, pattern: str) -> list[str]:
        matches = glob.glob(pattern)
        if matches:
            return sorted(os.path.abspath(path) for path in matches)
        if self._is_explicit_path(pattern) and os.path.exists(pattern):
            return [os.path.abspath(pattern)]
        return []

    def _is_explicit_path(self, pattern: str) -> bool:
        return not any(token in pattern for token in "*?[]")

    def _flatpak_is_available(self) -> bool:
        return bool(shutil.which("flatpak"))

    def _run_flatpak_command(self, scope: str) -> str:
        args = [
            "flatpak",
            "remotes",
            f"--{scope}",
            "--show-disabled",
            "--columns=name,url,options",
        ]
        completed = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
        )
        return str(completed.stdout or "")

    def _classify_origin(self, host: str) -> str:
        return "known" if host in self.known_hosts else "unknown"

    def _is_absolute_keyring_path(self, path: str) -> bool:
        text = str(path or "").strip()
        return bool(text) and text.startswith("/")

    def _is_allowed_keyring_location(self, path: str) -> bool:
        normalized = str(path or "").strip()
        return any(
            normalized.startswith(prefix) for prefix in self.allowed_keyring_prefixes
        )

    def _source_fingerprint(self, item: dict) -> tuple:
        return (
            str(item.get("kind") or ""),
            str(item.get("format") or ""),
            bool(item.get("enabled", True)),
            str(item.get("repo_type") or ""),
            str(item.get("uri") or ""),
            str(item.get("suite") or ""),
            tuple(item.get("components") or []),
            str(item.get("signed_by") or ""),
            str(item.get("host") or ""),
            str(item.get("scope") or ""),
            str(item.get("name") or ""),
        )

    def _source_identity_key(self, item: dict) -> tuple:
        return (
            str(item.get("kind") or ""),
            str(item.get("repo_type") or ""),
            str(item.get("uri") or ""),
            str(item.get("suite") or ""),
            tuple(item.get("components") or []),
            str(item.get("scope") or ""),
            str(item.get("name") or ""),
        )

    def _duplicate_config_fingerprint(self, item: dict) -> tuple:
        return (
            bool(item.get("enabled", True)),
            str(item.get("signed_by") or ""),
            tuple(sorted((item.get("options") or {}).items())),
        )

    def _group_sources_by_identity(self, sources: list[dict]) -> dict[tuple, list[dict]]:
        groups: dict[tuple, list[dict]] = {}
        for item in list(sources or []):
            groups.setdefault(self._source_identity_key(item), []).append(item)
        return groups

    def _baseline_match_sort_key(self, item: dict) -> tuple:
        return (
            self._source_fingerprint(item),
            str(item.get("file_path") or ""),
            int(item.get("line_no", 0) or 0),
            str(item.get("id") or ""),
        )

    def _changed_fields(self, before: dict, after: dict) -> list[str]:
        fields = []
        comparisons = {
            "enabled": bool(before.get("enabled", True)) != bool(after.get("enabled", True)),
            "repo_type": str(before.get("repo_type") or "") != str(after.get("repo_type") or ""),
            "uri": str(before.get("uri") or "") != str(after.get("uri") or ""),
            "suite": str(before.get("suite") or "") != str(after.get("suite") or ""),
            "components": tuple(before.get("components") or []) != tuple(after.get("components") or []),
            "signed_by": str(before.get("signed_by") or "") != str(after.get("signed_by") or ""),
            "host": str(before.get("host") or "") != str(after.get("host") or ""),
            "scope": str(before.get("scope") or "") != str(after.get("scope") or ""),
            "name": str(before.get("name") or "") != str(after.get("name") or ""),
        }
        for field_name, changed in comparisons.items():
            if changed:
                fields.append(field_name)
        return fields

    def _severity_rank(self, severity: str | None) -> int:
        order = {
            "critical": 0,
            "error": 1,
            "warning": 2,
            "notice": 3,
            "info": 4,
        }
        return order.get(str(severity or "").strip().lower(), 9)

    def _status_from_findings(self, findings: list[dict], errors: list[dict]) -> str:
        if errors:
            return "error"
        severities = {str(item.get("severity") or "").strip().lower() for item in findings}
        if "critical" in severities:
            return "critical"
        if "warning" in severities:
            return "warning"
        if "notice" in severities:
            return "notice"
        if findings:
            return "ok"
        return "ok"

    def _finding(
        self,
        *,
        source: dict,
        severity: str,
        code: str,
        title: str,
        summary: str,
        details: dict | None = None,
    ) -> dict:
        return {
            "id": f"finding:{code}:{source.get('id', '-')}",
            "severity": severity,
            "code": code,
            "title": title,
            "summary": summary,
            "source_id": source.get("id", ""),
            "details": {
                "file_path": source.get("file_path", ""),
                "line_no": source.get("line_no", 0),
                "uri": source.get("uri", ""),
                **(details or {}),
            },
        }

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
