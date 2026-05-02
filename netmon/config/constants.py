"""Pure constants shared across NetMon modules."""

NETMON_APP_VERSION = "1.1.1"

VPN_CH = "proton"
VPN_DE = "proton-de"
PRIVACY_VPN_LABELS = {
    "Proton CH": VPN_CH,
    "Proton DE": VPN_DE,
}
PRIVACY_VPN_PROFILES_TO_LABEL = {
    profile: label for label, profile in PRIVACY_VPN_LABELS.items()
}

SAFE_INPUT_PROCESS_NAMES = {
    "xorg",
    "xwayland",
    "gnome-shell",
    "kwin",
    "plasmashell",
    "sway",
    "weston",
    "lightdm",
    "gdm",
    "gdm-x-session",
    "sddm",
    "accounts-daemon",
    "systemd-logind",
    "logind",
    "seatd",
}

PORT_REALITY_DISPLAY_MAP = {
    "open": "offen",
    "pseudo-open": "verdächtig (kein echter Dienst)",
    "closed": "geschlossen",
    "filtered": "keine Antwort / blockiert",
}

SPEEDTEST_WARN_DEFAULTS = {
    "download_mbps_min": 10.0,
    "upload_mbps_min": 2.0,
    "ping_ms_max": 120.0,
    "jitter_ms_max": 40.0,
}

DNS_PROFILES = {
    "System (DHCP/auto)": None,
    "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
    "Google (8.8.8.8)": ["8.8.8.8", "8.8.4.4"],
    "Quad9 (malware-blocking)": ["9.9.9.9", "149.112.112.112"],
}

DNS_MODE_LABELS = {
    "auto": "Auto (empfohlen)",
    "vpn": "VPN bevorzugen",
    "manual": "Manuell (User DNS)",
}

DOT_PROFILES = {
    "Cloudflare": {
        "dns": ["1.1.1.1", "1.0.0.1"],
        "hostname": "cloudflare-dns.com",
    },
    "Quad9": {
        "dns": ["9.9.9.9", "149.112.112.112"],
        "hostname": "dns.quad9.net",
    },
    "Google": {
        "dns": ["8.8.8.8", "8.8.4.4"],
        "hostname": "dns.google",
    },
}

DOT_DROPIN_DIR = "/etc/systemd/resolved.conf.d"
DOT_DROPIN_PATH = "/etc/systemd/resolved.conf.d/netmon-dot.conf"

TRACE_TARGETS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
    "ifconfig.me",
    "github.com",
    "cloudflare.com",
]

VSCODE_DESKTOP_FILES = (
    "code.desktop",
    "visual-studio-code.desktop",
    "code-insiders.desktop",
    "codium.desktop",
)

HDD_SLOT_COUNT = 5
HDD_SLOT_CONFIG_FILE = "netmon_hdd_slots.json"
LINK_SLOT_COUNT = 15
LINK_SLOT_CONFIG_FILE = "netmon_link_slots.json"
VPN_SLOT_COUNT = 5
VPN_SLOT_CONFIG_FILE = "netmon_vpn_slots.json"
PRIMARY_VPN_SLOT_CONFIG_FILE = "netmon_primary_vpn_slots.json"
PRIVACY_CONFIG_FILE = "netmon_privacy.json"
SECURITY_BASELINE_FILE = "netmon_security_baseline.json"
CLAMAV_FINDINGS_FILE = "netmon_clamav_findings.json"
WG_IPV4_PROFILE_SUFFIX = "__ipv4"
