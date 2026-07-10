"""Pure constants shared across NetMon modules."""

NETMON_APP_VERSION = "1.1.17"

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

DNS_PROVIDER_CATALOG = [
    {
        "name": "Cloudflare (1.1.1.1)",
        "servers": ["1.1.1.1", "1.0.0.1"],
        "category": "Standard",
    },
    {
        "name": "Google (8.8.8.8)",
        "servers": ["8.8.8.8", "8.8.4.4"],
        "category": "Standard",
    },
    {
        "name": "Quad9 (malware-blocking)",
        "servers": ["9.9.9.9", "149.112.112.112"],
        "category": "Security",
    },
    {
        "name": "OpenDNS",
        "servers": ["208.67.222.222", "208.67.220.220"],
        "category": "Standard",
    },
    {
        "name": "AdGuard DNS",
        "servers": ["94.140.14.14", "94.140.15.15"],
        "category": "AdBlock",
    },
    {
        "name": "AdGuard Family",
        "servers": ["94.140.14.15", "94.140.15.16"],
        "category": "Family",
    },
    {
        "name": "CleanBrowsing Security",
        "servers": ["185.228.168.9", "185.228.169.9"],
        "category": "Security",
    },
    {
        "name": "CleanBrowsing Family",
        "servers": ["185.228.168.168", "185.228.169.168"],
        "category": "Family",
    },
    {
        "name": "DNS.WATCH",
        "servers": ["84.200.69.80", "84.200.70.40"],
        "category": "Privacy",
    },
    {
        "name": "Mullvad DNS",
        "servers": ["194.242.2.2", "194.242.2.3"],
        "category": "Privacy",
    },
    {
        "name": "Control D",
        "servers": ["76.76.2.0", "76.76.10.0"],
        "category": "Custom",
    },
    {
        "name": "Comodo Secure DNS",
        "servers": ["8.26.56.26", "8.20.247.20"],
        "category": "Security",
    },
    {
        "name": "Alternate DNS",
        "servers": ["76.76.19.19", "76.223.122.150"],
        "category": "AdBlock",
    },
    {
        "name": "Yandex Safe DNS",
        "servers": ["77.88.8.88", "77.88.8.2"],
        "category": "Security",
    },
    {
        "name": "Yandex Family DNS",
        "servers": ["77.88.8.7", "77.88.8.3"],
        "category": "Family",
    },
]

DNS_PROFILES = {
    "System (DHCP/auto)": None,
    **{
        item["name"]: list(item["servers"])
        for item in DNS_PROVIDER_CATALOG
        if item.get("name") and item.get("servers")
    },
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
RADIO_STATIONS_CONFIG_FILE = "radio_stations.json"
RADIO_FAVORITES_CONFIG_FILE = "radio_favorites.json"
RADIO_SETTINGS_CONFIG_FILE = "radio_settings.json"
SECURITY_BASELINE_FILE = "netmon_security_baseline.json"
CLAMAV_FINDINGS_FILE = "netmon_clamav_findings.json"
WG_IPV4_PROFILE_SUFFIX = "__ipv4"
