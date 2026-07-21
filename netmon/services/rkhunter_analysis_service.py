"""Deterministic classification for rkhunter and dpkg verification output."""

from __future__ import annotations

import re

CATEGORY_EXPECTED = "expected"
CATEGORY_REVIEW = "review"
CATEGORY_CRITICAL = "critical"

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_ALERT_RE = re.compile(
    r"\b(warning|changed|modified|replaced|mismatch|suspicious|suspect|"
    r"infected|hidden file|hidden directory|unknown|unexpected|new executable|"
    r"new module|autostart)\b",
    re.IGNORECASE,
)
_NEGATIVE_FINDING_RE = re.compile(
    r"(?:\b(?:no|none)\b.{0,50}\b(?:found|detected|present)\b|"
    r"\bnot\s+(?:found|detected|infected|suspicious)\b|"
    r"\[(?:\s*ok\s*|\s*none found\s*|\s*not found\s*)\]|"
    r"\b(?:possible rootkits?|rootkits?|backdoors?|suspect files)\s*:\s*0\b)",
    re.IGNORECASE,
)

_NETWORK_CONFIG_RE = re.compile(
    r"(?:/etc/(?:network|netplan|NetworkManager|systemd/network|resolv\.conf)|"
    r"/lib/netplan|interfaces(?:\.d)?|wireguard|wg\d*\.conf)",
    re.IGNORECASE,
)
_EXPECTED_CONFIG_RE = re.compile(
    r"(?:/etc/(?:rkhunter\.conf|gdm3/custom\.conf|fwupd\.conf|"
    r"systemd/resolved\.conf|systemd/timesyncd\.conf)|mirrors\.dat)",
    re.IGNORECASE,
)
_DEVELOPER_ENV_RE = re.compile(
    r"(?:\bvisual studio code\b|\bvs code\b|\bvscode\b|\bcodex\b|"
    r"\bdev[- ]?container\b|(?<![A-Za-z0-9_.-])docker(?![A-Za-z0-9_.-])|"
    r"(?<![A-Za-z0-9_.-])containerd(?![A-Za-z0-9_.-])|"
    r"/\.devcontainer(?:/|$)|/\.vscode(?:/|$)|/\.codex(?:/|$))",
    re.IGNORECASE,
)
_KERNEL_FILE_RE = re.compile(
    r"(?:/boot/(?:vmlinuz|initrd|config|System\.map)|/lib/modules/)",
    re.IGNORECASE,
)
_HIDDEN_SYSTEM_FILE_RE = re.compile(
    r"(?:hidden (?:file|directory).*(?:/etc|/usr|/bin|/sbin|/lib)|"
    r"(?:/etc|/usr|/bin|/sbin|/lib)/\.[^\s/]+)",
    re.IGNORECASE,
)
_EXPECTED_HIDDEN_SYSTEM_ARTIFACT_RE = re.compile(
    r"/etc/\.(?:resolv\.conf\.systemd-resolved\.bak|updated)\b",
    re.IGNORECASE,
)
_AUTOSTART_RE = re.compile(
    r"(?:autostart|/etc/(?:xdg/autostart|init\.d|systemd/system)|"
    r"/\.config/autostart/)",
    re.IGNORECASE,
)
_KERNEL_MODULE_RE = re.compile(
    r"(?:new|unknown|unexpected|suspicious).{0,30}\bkernel module\b|"
    r"\bkernel module\b.{0,30}(?:new|unknown|unexpected|suspicious)",
    re.IGNORECASE,
)
_CORE_PROGRAM_RE = re.compile(
    r"(?:/(?:usr/)?(?:s?bin)/(?:bash|login|sudo|ssh|sshd)(?:\s|:|$)|"
    r"/(?:usr/)?lib[^\s]*/(?:libc[^/\s]*|security/pam_[^/\s]+))",
    re.IGNORECASE,
)
_REPLACED_BY_SCRIPT_RE = re.compile(r"\breplaced by (?:a )?script\b", re.IGNORECASE)
_PATH_RE = re.compile(r"(/[A-Za-z0-9._+@%=-][^\s'\":;,)]*)")
_SCRIPT_FILE_TYPE_RE = re.compile(
    r"\b(?:script|python|perl|ruby|shell|bash|posix shell)\b", re.IGNORECASE
)
_DPKG_PERMISSION_NOISE_RE = re.compile(
    r"(?:Keine Berechtigung|Permission denied|Operation not permitted)", re.IGNORECASE
)
_EXPECTED_MISSING_PATH_RE = re.compile(
    r"(?:/var/lib/polkit-1/localauthority|/var/cache/cups/rss|"
    r"/var/spool/cups/tmp|/etc/apparmor\.d/disable|"
    r"/etc/gtk-3\.0/settings\.ini\.real)",
    re.IGNORECASE,
)
_EXPECTED_NETWORK_PACKAGE_FILE_RE = re.compile(
    r"/lib/netplan/00-network-manager-all\.yaml",
    re.IGNORECASE,
)
_EXPECTED_RKHUNTER_DATA_RE = re.compile(
    r"/var/lib/rkhunter/db/(?:mirrors\.dat|programs_bad\.dat|backdoorports\.dat)",
    re.IGNORECASE,
)


def _finding(category: str, code: str, reason: str, line: str, source: str):
    return {
        "category": category,
        "code": code,
        "reason": reason,
        "line": line.strip(),
        "source": source,
    }


def _is_negative_finding(line: str) -> bool:
    return bool(_NEGATIVE_FINDING_RE.search(line))


def _extract_unique_paths_from_lines(
    output: str, line_matches, path_allowed=None
) -> list[str]:
    paths = []
    seen = set()
    cleaned_output = _ANSI_RE.sub("", str(output or ""))
    for line in cleaned_output.splitlines():
        if not line_matches(line):
            continue
        for match in _PATH_RE.finditer(line):
            path = match.group(1).rstrip(".")
            if path_allowed is not None and not path_allowed(path):
                continue
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def extract_replaced_script_paths(output: str) -> list[str]:
    """Return command paths from rkhunter 'replaced by script' warnings."""

    return _extract_unique_paths_from_lines(
        output,
        lambda line: bool(_REPLACED_BY_SCRIPT_RE.search(line)),
    )


def extract_warning_command_paths(output: str) -> list[str]:
    return _extract_unique_paths_from_lines(
        output,
        lambda line: "[ Warning ]" in line,
        lambda path: path.startswith(("/usr/bin/", "/usr/sbin/", "/bin/", "/sbin/")),
    )


def _parse_path_evidence(output: str) -> dict[str, tuple[int, str]]:
    evidence = {}
    for line in _ANSI_RE.sub("", str(output or "")).splitlines():
        path, sep, rest = line.partition("\t")
        if not sep:
            continue
        rc_text, sep, text = rest.partition("\t")
        if not sep:
            continue
        try:
            rc = int(rc_text)
        except ValueError:
            continue
        evidence[path.strip()] = (rc, text.strip())
    return evidence


def _package_owner_verified(
    path: str, owner_evidence: dict[str, tuple[int, str]]
) -> bool:
    rc, text = owner_evidence.get(path, (1, ""))
    return rc == 0 and ":" in text and "no path found" not in text.lower()


def _file_type_verified(path: str, file_evidence: dict[str, tuple[int, str]]) -> bool:
    rc, text = file_evidence.get(path, (1, ""))
    return rc == 0 and bool(_SCRIPT_FILE_TYPE_RE.search(text))


def _dpkg_path_clean(path: str, dpkg_findings) -> bool:
    return not any(path in item["line"] for item in dpkg_findings)


def _is_dpkg_expected_noise(text: str) -> bool:
    lowered = text.lower()
    if _DPKG_PERMISSION_NOISE_RE.search(text) and _EXPECTED_MISSING_PATH_RE.search(
        text
    ):
        return True
    if lowered.startswith("missing") and _EXPECTED_MISSING_PATH_RE.search(text):
        return True
    if _EXPECTED_NETWORK_PACKAGE_FILE_RE.search(text):
        return True
    if _EXPECTED_RKHUNTER_DATA_RE.search(text):
        return True
    return False


def _is_expected_hidden_system_artifact(line: str) -> bool:
    return bool(_EXPECTED_HIDDEN_SYSTEM_ARTIFACT_RE.search(line))


def _classify_rkhunter_line(line: str):
    text = line.strip()
    if not text or _is_negative_finding(text):
        return None

    possible_rootkits = re.search(r"possible rootkits?\s*:\s*(\d+)", text, re.I)
    if (possible_rootkits and int(possible_rootkits.group(1)) > 0) or re.search(
        r"\brootkit\b.{0,50}\b(found|detected|present)\b", text, re.I
    ):
        return _finding(
            CATEGORY_CRITICAL,
            "rootkit",
            "A rootkit indicator was reported.",
            text,
            "rkhunter",
        )
    if re.search(
        r"\bbackdoor\b.{0,60}\b(port|found|detected|open|present)\b|"
        r"\bbackdoor port\b",
        text,
        re.I,
    ):
        return _finding(
            CATEGORY_CRITICAL,
            "backdoor",
            "A backdoor indicator or backdoor port was reported.",
            text,
            "rkhunter",
        )
    if _CORE_PROGRAM_RE.search(text) and _ALERT_RE.search(text):
        return _finding(
            CATEGORY_CRITICAL,
            "system_program",
            "A security-critical system program or library may be modified.",
            text,
            "rkhunter",
        )
    if re.search(
        r"(?:additional|another|unexpected|unknown).{0,40}\buid[ -]?0\b|"
        r"\buid[ -]?0\b.{0,40}(?:account|user)",
        text,
        re.I,
    ):
        return _finding(
            CATEGORY_CRITICAL,
            "uid0_account",
            "An additional UID-0 account may exist.",
            text,
            "rkhunter",
        )
    if re.search(r"\bpam\b|/security/pam_", text, re.I) and _ALERT_RE.search(text):
        return _finding(
            CATEGORY_CRITICAL,
            "pam_module",
            "A PAM authentication component may be modified.",
            text,
            "rkhunter",
        )
    if re.search(
        r"\b(suspicious|malicious).{0,30}\b(process|connection|listener)\b|"
        r"\b(process|connection|listener)\b.{0,30}\b(suspicious|malicious)\b",
        text,
        re.I,
    ):
        return _finding(
            CATEGORY_CRITICAL,
            "suspicious_runtime",
            "A suspicious process or network connection was reported.",
            text,
            "rkhunter",
        )

    if not _ALERT_RE.search(text):
        return None

    if _NETWORK_CONFIG_RE.search(text):
        return _finding(
            CATEGORY_REVIEW,
            "network_config",
            "A network configuration change should be verified.",
            text,
            "rkhunter",
        )
    if _HIDDEN_SYSTEM_FILE_RE.search(text):
        return _finding(
            CATEGORY_REVIEW,
            "hidden_system_file",
            "A hidden file in a system directory should be identified.",
            text,
            "rkhunter",
        )
    if re.search(r"checking for hidden files and directories", text, re.IGNORECASE):
        return _finding(
            CATEGORY_REVIEW,
            "hidden_files_summary",
            "rkhunter reported hidden files; inspect /var/log/rkhunter.log for the concrete path.",
            text,
            "rkhunter",
        )
    suspect_files = re.search(r"\bsuspect files\s*:\s*(\d+)\b", text, re.IGNORECASE)
    if suspect_files and int(suspect_files.group(1)) > 0:
        return _finding(
            CATEGORY_REVIEW,
            "suspect_files",
            "rkhunter reported suspect files; inspect the log evidence for concrete paths.",
            text,
            "rkhunter",
        )
    if re.search(r"/usr/local/(?:s?bin)/", text, re.I):
        return _finding(
            CATEGORY_REVIEW,
            "local_executable",
            "An executable under /usr/local should be traced to its owner.",
            text,
            "rkhunter",
        )
    if _AUTOSTART_RE.search(text):
        return _finding(
            CATEGORY_REVIEW,
            "autostart",
            "A new or changed autostart entry should be verified.",
            text,
            "rkhunter",
        )
    if _KERNEL_MODULE_RE.search(text):
        return _finding(
            CATEGORY_REVIEW,
            "kernel_module",
            "A new or unknown kernel module should be verified.",
            text,
            "rkhunter",
        )
    if _DEVELOPER_ENV_RE.search(text):
        return _finding(
            CATEGORY_EXPECTED,
            "developer_environment",
            "The path belongs to a known development or container environment.",
            text,
            "rkhunter",
        )
    if _KERNEL_FILE_RE.search(text):
        return _finding(
            CATEGORY_EXPECTED,
            "kernel_update_file",
            "Kernel files commonly change during regular system updates.",
            text,
            "rkhunter",
        )
    if _EXPECTED_CONFIG_RE.search(text):
        return _finding(
            CATEGORY_EXPECTED,
            "configuration_file",
            "A known configuration or rkhunter data file changed.",
            text,
            "rkhunter",
        )
    return _finding(
        CATEGORY_REVIEW,
        "unclassified_warning",
        "The warning is not a known benign pattern and should be reviewed.",
        text,
        "rkhunter",
    )


def _classify_dpkg_line(line: str):
    text = line.strip()
    if not text:
        return None
    if _is_dpkg_expected_noise(text):
        return _finding(
            CATEGORY_EXPECTED,
            "dpkg_expected_noise",
            "dpkg reports a known permission or transient system path noise item.",
            text,
            "dpkg",
        )
    if _CORE_PROGRAM_RE.search(text):
        return _finding(
            CATEGORY_CRITICAL,
            "dpkg_system_program",
            "dpkg reports a change to a security-critical program or library.",
            text,
            "dpkg",
        )
    if _NETWORK_CONFIG_RE.search(text):
        if re.search(r"\s+c\s+", text):
            return _finding(
                CATEGORY_EXPECTED,
                "dpkg_network_conffile",
                "dpkg reports a changed network conffile.",
                text,
                "dpkg",
            )
        return _finding(
            CATEGORY_REVIEW,
            "dpkg_network_config",
            "dpkg reports a network configuration change.",
            text,
            "dpkg",
        )
    if _KERNEL_FILE_RE.search(text):
        return _finding(
            CATEGORY_EXPECTED,
            "dpkg_kernel_file",
            "dpkg reports a kernel file that may have changed during an update.",
            text,
            "dpkg",
        )
    if re.search(r"\s+c\s+/etc/", text) and _EXPECTED_CONFIG_RE.search(text):
        return _finding(
            CATEGORY_EXPECTED,
            "dpkg_configuration_file",
            "dpkg reports a changed conffile, which may be administrator-managed.",
            text,
            "dpkg",
        )
    return _finding(
        CATEGORY_REVIEW,
        "dpkg_unexpected_change",
        "dpkg reports a package-managed file change that should be verified.",
        text,
        "dpkg",
    )


def _rkhunter_risk_from_categories(categories: dict, rc: int) -> str:
    if categories[CATEGORY_CRITICAL]:
        return RISK_HIGH
    if categories[CATEGORY_REVIEW] or rc not in (0, 1):
        return RISK_MEDIUM
    return RISK_LOW


def _rkhunter_critical_flags(codes: set[str]) -> dict[str, bool]:
    return {
        "rootkits": "rootkit" in codes,
        "backdoors": "backdoor" in codes,
        "suspicious_runtime": "suspicious_runtime" in codes,
        "system_programs": bool(
            {"system_program", "dpkg_system_program", "pam_module"} & codes
        ),
        "critical_network": bool({"backdoor", "suspicious_runtime"} & codes),
    }


def analyze_rkhunter_output(
    output: str,
    rc: int,
    *,
    dpkg_output: str = "",
    dpkg_rc: int | None = None,
    dpkg_owner_output: str = "",
    file_type_output: str = "",
):
    """Return classified findings and a conservative propupd eligibility gate."""

    cleaned_output = _ANSI_RE.sub("", str(output or ""))
    findings = []
    for line in cleaned_output.splitlines():
        finding = _classify_rkhunter_line(line)
        if finding is not None:
            findings.append(finding)

    dpkg_findings = []
    for line in _ANSI_RE.sub("", str(dpkg_output or "")).splitlines():
        finding = _classify_dpkg_line(line)
        if finding is not None:
            dpkg_findings.append(finding)
    findings.extend(dpkg_findings)

    owner_evidence = _parse_path_evidence(dpkg_owner_output)
    file_evidence = _parse_path_evidence(file_type_output)
    replaced_script_paths = set(extract_replaced_script_paths(cleaned_output))
    warning_command_paths = set(extract_warning_command_paths(cleaned_output))
    for item in findings:
        if (
            item["category"] != CATEGORY_REVIEW
            or item["code"] != "unclassified_warning"
        ):
            continue
        is_script_warning = _REPLACED_BY_SCRIPT_RE.search(item["line"])
        line_paths = set(_PATH_RE.findall(item["line"]))
        candidate_paths = line_paths & (replaced_script_paths | warning_command_paths)
        if not is_script_warning and not candidate_paths:
            continue
        verified_paths = [
            path
            for path in candidate_paths
            if _package_owner_verified(path, owner_evidence)
            and _dpkg_path_clean(path, dpkg_findings)
            and _file_type_verified(path, file_evidence)
        ]
        if not verified_paths:
            continue
        item.update(
            {
                "category": CATEGORY_EXPECTED,
                "code": "packaged_script_false_positive",
                "reason": (
                    "Kein Hinweis auf Manipulation. Wahrscheinlich "
                    "distributionsbedingter Fehlalarm."
                ),
            }
        )

    hidden_findings = [
        item
        for item in findings
        if item["category"] == CATEGORY_REVIEW and item["code"] == "hidden_system_file"
    ]
    hidden_expected = [
        item
        for item in hidden_findings
        if _is_expected_hidden_system_artifact(item["line"])
    ]
    if hidden_findings and len(hidden_findings) == len(hidden_expected):
        for item in hidden_expected:
            item.update(
                {
                    "category": CATEGORY_EXPECTED,
                    "code": "hidden_system_artifact",
                    "reason": (
                        "Known hidden system artifact from resolver or update state; "
                        "no manipulation indicator by itself."
                    ),
                }
            )
        for item in findings:
            if item["category"] == CATEGORY_REVIEW and item["code"] in {
                "hidden_files_summary",
                "suspect_files",
            }:
                item.update(
                    {
                        "category": CATEGORY_EXPECTED,
                        "code": "hidden_files_explained",
                        "reason": (
                            "Hidden-file summary is explained by known system artifacts."
                        ),
                    }
                )

    categories = {
        category: [item for item in findings if item["category"] == category]
        for category in (CATEGORY_EXPECTED, CATEGORY_REVIEW, CATEGORY_CRITICAL)
    }
    risk = _rkhunter_risk_from_categories(categories, rc)

    codes = {item["code"] for item in findings}
    scan_completed = rc in (0, 1) and bool(
        re.search(
            r"(?:system checks summary|rootkit checks|possible rootkits?\s*:\s*\d+)",
            cleaned_output,
            re.IGNORECASE,
        )
    )
    dpkg_verified = dpkg_rc == 0 and not any(
        item["category"] in (CATEGORY_REVIEW, CATEGORY_CRITICAL)
        for item in dpkg_findings
    )
    critical_flags = _rkhunter_critical_flags(codes)
    propupd_allowed = (
        scan_completed
        and dpkg_verified
        and risk == RISK_LOW
        and not any(critical_flags.values())
    )

    return {
        "rc": rc,
        "risk": risk,
        "findings": findings,
        "expected": categories[CATEGORY_EXPECTED],
        "review": categories[CATEGORY_REVIEW],
        "critical": categories[CATEGORY_CRITICAL],
        "scan_completed": scan_completed,
        "dpkg_rc": dpkg_rc,
        "dpkg_verified": dpkg_verified,
        "critical_flags": critical_flags,
        "propupd_allowed": propupd_allowed,
    }
