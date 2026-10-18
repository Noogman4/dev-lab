#!/usr/bin/env bash
set -euo pipefail

NETMON_PACKAGE="${NETMON_PACKAGE:-netmon}"
NETMON_DOT_DROPIN="/etc/systemd/resolved.conf.d/netmon-dot.conf"
NETMON_LANG_CODE="${NETMON_LANG_CODE:-}"

OPTIONAL_PACKAGES=(
  bind9-dnsutils
  clamav
  clamav-freshclam
  dnsutils
  htop
  iftop
  lynis
  mpv
  mtr-tiny
  nmap
  python3-docx
  python3-pgzero
  python3-pil
  python3-pil.imagetk
  python3-psutil
  python3-pygame
  python3-pypdf2
  rkhunter
  speedtest-cli
  traceroute
  tshark
  ufw
  whois
  wireshark
  wireguard-tools
)

DEFAULT_CONFIG_DIR="$HOME/.config/netmon"
DEFAULT_STATE_DIR="$HOME/.local/state/netmon"
DEFAULT_CACHE_DIR="$HOME/.cache/netmon"
DEFAULT_CACHE_DIR_ALT="$HOME/.cache/netmon_roots"
DEFAULT_LOCAL_SHARE_DIR="$HOME/.local/share/netmon"
DEFAULT_APP_ENTRY_DIR="$HOME/.local/share/applications"
VPN_SLOT_CONFIG_FILE="netmon_vpn_slots.json"
PRIMARY_VPN_SLOT_CONFIG_FILE="netmon_primary_vpn_slots.json"
PRIVACY_CONFIG_FILE="netmon_privacy.json"
NETMON_WIREGUARD_ROOT="/etc/wireguard"

say() {
  printf '%s\n' "$*"
}

tr_msg() {
  local key="$1"
  case "${NETMON_LANG_CODE:-de}:$key" in
    en:warn_prefix) printf '%s' "WARNING: " ;;
    de:warn_prefix|*:warn_prefix) printf '%s' "WARNUNG: " ;;
    en:press_enter) printf '%s' "Press Enter to exit..." ;;
    de:press_enter|*:press_enter) printf '%s' "Zum Beenden Enter drücken..." ;;
    en:required_cmd_missing) printf '%s' "Required command is missing: %s" ;;
    de:required_cmd_missing|*:required_cmd_missing) printf '%s' "Benötigter Befehl fehlt: %s" ;;
    en:netmon_running_warn) printf '%s' "NetMon or the standalone radio player is still running." ;;
    de:netmon_running_warn|*:netmon_running_warn) printf '%s' "NetMon oder der Standalone-Radio-Player laufen noch." ;;
    en:close_windows_retry) printf '%s' "Please close all NetMon windows first and then start the uninstaller again." ;;
    de:close_windows_retry|*:close_windows_retry) printf '%s' "Bitte zuerst alle NetMon-Fenster schließen und dann den Deinstaller erneut starten." ;;
    en:found_processes) printf '%s' "Detected processes:" ;;
    de:found_processes|*:found_processes) printf '%s' "Gefundene Prozesse:" ;;
    en:requesting_sudo) printf '%s' "Requesting sudo privileges..." ;;
    de:requesting_sudo|*:requesting_sudo) printf '%s' "Sudo-Rechte werden angefordert..." ;;
    en:start_as_root) printf '%s' "Please start as root or with sudo." ;;
    de:start_as_root|*:start_as_root) printf '%s' "Bitte als root oder mit sudo starten." ;;
    en:removed) printf '%s' "Removed: %s" ;;
    de:removed|*:removed) printf '%s' "Entfernt: %s" ;;
    en:skipped_missing) printf '%s' "Skipped (not present): %s" ;;
    de:skipped_missing|*:skipped_missing) printf '%s' "Übersprungen (nicht vorhanden): %s" ;;
    en:nmcli_missing_vpn_cleanup) printf '%s' "nmcli not available, skipped NetworkManager VPN cleanup." ;;
    de:nmcli_missing_vpn_cleanup|*:nmcli_missing_vpn_cleanup) printf '%s' "nmcli nicht vorhanden, NetworkManager-VPN-Bereinigung übersprungen." ;;
    en:no_referenced_nm_connections) printf '%s' "No referenced NetMon NetworkManager VPN connections found." ;;
    de:no_referenced_nm_connections|*:no_referenced_nm_connections) printf '%s' "Keine referenzierten NetMon-NetworkManager-VPN-Connections gefunden." ;;
    en:nm_connection_removed) printf '%s' "Removed NetworkManager connection: %s" ;;
    de:nm_connection_removed|*:nm_connection_removed) printf '%s' "NetworkManager-Connection entfernt: %s" ;;
    en:nm_connection_remove_failed) printf '%s' "Could not remove NetworkManager connection: %s" ;;
    de:nm_connection_remove_failed|*:nm_connection_remove_failed) printf '%s' "NetworkManager-Connection konnte nicht entfernt werden: %s" ;;
    en:no_wireguard_dir) printf '%s' "No WireGuard directory found: %s" ;;
    de:no_wireguard_dir|*:no_wireguard_dir) printf '%s' "Kein WireGuard-Verzeichnis gefunden: %s" ;;
    en:no_wireguard_profiles) printf '%s' "No WireGuard profiles found under %s." ;;
    de:no_wireguard_profiles|*:no_wireguard_profiles) printf '%s' "Keine WireGuard-Profile unter %s gefunden." ;;
    en:removed_dot_dropin) printf '%s' "Removed NetMon DoT drop-in: %s" ;;
    de:removed_dot_dropin|*:removed_dot_dropin) printf '%s' "Entferntes NetMon DoT-Drop-in: %s" ;;
    en:no_dot_dropin) printf '%s' "No NetMon DoT drop-in found." ;;
    de:no_dot_dropin|*:no_dot_dropin) printf '%s' "Kein NetMon DoT-Drop-in gefunden." ;;
    en:nm_dns_override_removed) printf '%s' "Removed NetworkManager DNS override: %s (%s)" ;;
    de:nm_dns_override_removed|*:nm_dns_override_removed) printf '%s' "NetworkManager DNS-Override entfernt: %s (%s)" ;;
    en:nmcli_missing_dns_reset) printf '%s' "nmcli not available, skipped NetworkManager DNS reset." ;;
    de:nmcli_missing_dns_reset|*:nmcli_missing_dns_reset) printf '%s' "nmcli nicht vorhanden, NetworkManager-DNS-Reset übersprungen." ;;
    en:ufw_missing_reset) printf '%s' "ufw not available, skipped firewall reset." ;;
    de:ufw_missing_reset|*:ufw_missing_reset) printf '%s' "ufw nicht vorhanden, Firewall-Reset übersprungen." ;;
    en:ufw_reset_done) printf '%s' "Reset UFW to its default state." ;;
    de:ufw_reset_done|*:ufw_reset_done) printf '%s' "UFW auf Standardzustand zurückgesetzt." ;;
    en:package_not_installed) printf '%s' "Package %s is not installed according to dpkg." ;;
    de:package_not_installed|*:package_not_installed) printf '%s' "Paket %s ist laut dpkg nicht installiert." ;;
    en:summary_title) printf '%s' "Planned NetMon uninstallation" ;;
    de:summary_title|*:summary_title) printf '%s' "Geplante NetMon-Deinstallation" ;;
    en:summary_remove_package) printf '%s' "Remove package:" ;;
    de:summary_remove_package|*:summary_remove_package) printf '%s' "Paket entfernen:" ;;
    en:summary_remove_launchers) printf '%s' "Remove launcher/icon leftovers:" ;;
    de:summary_remove_launchers|*:summary_remove_launchers) printf '%s' "Launcher/Icon-Reste entfernen:" ;;
    en:summary_remove_user_files) printf '%s' "Remove user data/caches:" ;;
    de:summary_remove_user_files|*:summary_remove_user_files) printf '%s' "Benutzerdaten/Caches entfernen:" ;;
    en:summary_remove_secure_browsers) printf '%s' "Remove Secure Browsers:" ;;
    de:summary_remove_secure_browsers|*:summary_remove_secure_browsers) printf '%s' "Secure Browser entfernen:" ;;
    en:summary_remove_wireguard_artifacts) printf '%s' "Clean up WireGuard/VPN leftovers:" ;;
    de:summary_remove_wireguard_artifacts|*:summary_remove_wireguard_artifacts) printf '%s' "WireGuard/VPN-Reste bereinigen:" ;;
    en:summary_remove_all_wireguard_confs) printf '%s' "Clear /etc/wireguard:" ;;
    de:summary_remove_all_wireguard_confs|*:summary_remove_all_wireguard_confs) printf '%s' "/etc/wireguard leeren:" ;;
    en:summary_remove_nm_connections) printf '%s' "Remove NM VPN connections:" ;;
    de:summary_remove_nm_connections|*:summary_remove_nm_connections) printf '%s' "NM-VPN-Connections entfernen:" ;;
    en:summary_reset_dns_nm) printf '%s' "Reset NetMon DNS/NM changes:" ;;
    de:summary_reset_dns_nm|*:summary_reset_dns_nm) printf '%s' "NetMon DNS/NM zurücksetzen:" ;;
    en:summary_reset_firewall) printf '%s' "Fully reset UFW:" ;;
    de:summary_reset_firewall|*:summary_reset_firewall) printf '%s' "UFW komplett zurücksetzen:" ;;
    en:summary_purge_optional) printf '%s' "Remove optional dependencies:" ;;
    de:summary_purge_optional|*:summary_purge_optional) printf '%s' "Optionale Abhängigkeiten entfernen:" ;;
    en:yes) printf '%s' "yes" ;;
    de:yes|*:yes) printf '%s' "ja" ;;
    en:no) printf '%s' "no" ;;
    de:no|*:no) printf '%s' "nein" ;;
    en:uninstaller_title) printf '%s' "NetMon uninstaller" ;;
    de:uninstaller_title|*:uninstaller_title) printf '%s' "NetMon Deinstaller" ;;
    en:uninstaller_intro_1) printf '%s' "This tool removes NetMon and can optionally clean up user data," ;;
    de:uninstaller_intro_1|*:uninstaller_intro_1) printf '%s' "Dieses Werkzeug entfernt NetMon und kann optional Benutzerdaten," ;;
    en:uninstaller_intro_2) printf '%s' "desktop launchers and NetMon-related system changes." ;;
    de:uninstaller_intro_2|*:uninstaller_intro_2) printf '%s' "Desktop-Launcher sowie NetMon-nahe Systemänderungen bereinigen." ;;
    en:uninstaller_warn_optional_resets) printf '%s' "Firewall and NetworkManager resets are optional and intentionally separate." ;;
    de:uninstaller_warn_optional_resets|*:uninstaller_warn_optional_resets) printf '%s' "Firewall- und NetworkManager-Resets sind optional und bewusst separat." ;;
    en:prompt_remove_package) printf '%s' "Remove the NetMon package via apt remove?" ;;
    de:prompt_remove_package|*:prompt_remove_package) printf '%s' "NetMon-Paket per apt remove entfernen?" ;;
    en:prompt_remove_launchers) printf '%s' "Remove NetMon desktop launcher and radio launcher from the user profile?" ;;
    de:prompt_remove_launchers|*:prompt_remove_launchers) printf '%s' "NetMon Desktop-Launcher und Radio-Launcher im Benutzerprofil entfernen?" ;;
    en:prompt_remove_user_files) printf '%s' "Remove NetMon user data, caches, logs and documents?" ;;
    de:prompt_remove_user_files|*:prompt_remove_user_files) printf '%s' "NetMon Benutzerdaten, Caches, Logs und Dokumente entfernen?" ;;
    en:prompt_remove_secure_browsers) printf '%s' "Also uninstall installed Secure Browsers?" ;;
    de:prompt_remove_secure_browsers|*:prompt_remove_secure_browsers) printf '%s' "Installierte Secure Browser ebenfalls deinstallieren?" ;;
    en:prompt_remove_wireguard_artifacts) printf '%s' "Clean up user VPN slot JSON files and import folders (system profiles retained)?" ;;
    de:prompt_remove_wireguard_artifacts|*:prompt_remove_wireguard_artifacts) printf '%s' "Benutzer-VPN-Slot-JSONs und Importordner bereinigen (Systemprofile bleiben erhalten)?" ;;
    en:prompt_remove_all_wireguard_confs) printf '%s' "Delete all WireGuard profiles under /etc/wireguard? (test systems only)" ;;
    de:prompt_remove_all_wireguard_confs|*:prompt_remove_all_wireguard_confs) printf '%s' "Alle WireGuard-Profile unter /etc/wireguard löschen? (nur Testsystem)" ;;
    en:prompt_remove_nm_connections) printf '%s' "Review verified NetMon-created WireGuard UUIDs for removal?" ;;
    de:prompt_remove_nm_connections|*:prompt_remove_nm_connections) printf '%s' "Nachgewiesene NetMon-WireGuard-UUIDs zur Entfernung prüfen?" ;;
    en:prompt_reset_dns_nm) printf '%s' "Reset NetMon DNS/DoT changes and NetworkManager DNS overrides?" ;;
    de:prompt_reset_dns_nm|*:prompt_reset_dns_nm) printf '%s' "NetMon DNS-/DoT-Änderungen und NetworkManager-DNS-Overrides zurücksetzen?" ;;
    en:prompt_reset_firewall) printf '%s' "Reset UFW completely?" ;;
    de:prompt_reset_firewall|*:prompt_reset_firewall) printf '%s' "UFW komplett zurücksetzen?" ;;
    en:prompt_purge_optional) printf '%s' "Also remove optional NetMon test dependencies via apt remove?" ;;
    de:prompt_purge_optional|*:prompt_purge_optional) printf '%s' "Optionale NetMon-Test-Abhängigkeiten zusätzlich per apt remove entfernen?" ;;
    en:prompt_execute_now) printf '%s' "Start execution now?" ;;
    de:prompt_execute_now|*:prompt_execute_now) printf '%s' "Ausführung jetzt starten?" ;;
    en:cancelled) printf '%s' "Canceled." ;;
    de:cancelled|*:cancelled) printf '%s' "Abgebrochen." ;;
    en:finished) printf '%s' "NetMon uninstallation completed." ;;
    de:finished|*:finished) printf '%s' "NetMon-Deinstallation abgeschlossen." ;;
    *) printf '%s' "$key" ;;
  esac
}

format_msg() {
  local template="$1"
  shift
  printf "$template" "$@"
}

warn() {
  printf '%s%s\n' "$(tr_msg warn_prefix)" "$*" >&2
}

pause_before_exit() {
  if [[ -t 0 && -t 1 ]]; then
    printf '\n%s' "$(tr_msg press_enter)"
    read -r _unused || true
  fi
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    warn "$(format_msg "$(tr_msg required_cmd_missing)" "$1")"
    return 1
  fi
}

prompt_yes_no() {
  local prompt="$1"
  local default_answer="${2:-n}"
  local suffix="[y/N]"
  local answer=""
  if [[ "$default_answer" == "y" ]]; then
    suffix="[Y/n]"
  fi
  while true; do
    printf '%s %s ' "$prompt" "$suffix"
    read -r answer || true
    answer="${answer:-$default_answer}"
    case "${answer,,}" in
      y|yes|j|ja) return 0 ;;
      n|no) return 1 ;;
    esac
  done
}

find_running_netmon_processes() {
  if ! command -v pgrep >/dev/null 2>&1; then
    return 0
  fi

  local pattern='(^|[[:space:]])(/usr/bin/netmon|python3[[:space:]]+-m[[:space:]]+netmon|/(opt|usr/lib)/netmon/.*/main\.py|netmon/main\.py|netmon_radio_app\.py|netmon\.netmon_radio_app)([[:space:]]|$)'
  local current_pid="$$"
  local line=""
  local found=0
  local skip_pids=" $current_pid "

  while [[ -n "$current_pid" && "$current_pid" != "0" ]]; do
    current_pid="$(ps -o ppid= -p "$current_pid" 2>/dev/null | tr -d '[:space:]')"
    [[ -n "$current_pid" ]] || break
    skip_pids+=" $current_pid "
  done

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    local pid="${line%% *}"
    if [[ "$skip_pids" == *" $pid "* ]]; then
      continue
    fi
    if [[ "$line" == *"netmon-uninstall"* ]]; then
      continue
    fi
    printf '%s\n' "$line"
    found=1
  done < <(pgrep -af "$pattern" || true)

  return "$found"
}

ensure_netmon_not_running() {
  local running=""
  running="$(find_running_netmon_processes || true)"
  if [[ -z "$running" ]]; then
    return 0
  fi

  say ""
  warn "$(tr_msg netmon_running_warn)"
  say "$(tr_msg close_windows_retry)"
  say ""
  say "$(tr_msg found_processes)"
  printf '%s\n' "$running"
  pause_before_exit
  exit 1
}

ensure_root() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    return 0
  fi
  if command -v sudo >/dev/null 2>&1; then
    say "$(tr_msg requesting_sudo)"
    exec sudo --preserve-env=NETMON_PACKAGE,HOME,XDG_DOCUMENTS_DIR "$0" "$@"
  fi
  warn "$(tr_msg start_as_root)"
  exit 1
}

target_user() {
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    printf '%s\n' "$SUDO_USER"
    return
  fi
  id -un
}

target_home() {
  local user_name
  user_name="$(target_user)"
  local home_dir=""
  if [[ -n "${SUDO_USER:-}" && -n "${HOME:-}" && "${SUDO_USER}" != "root" ]]; then
    home_dir="$HOME"
  fi
  if [[ -z "$home_dir" ]]; then
    home_dir="$(getent passwd "$user_name" | cut -d: -f6)"
  fi
  printf '%s\n' "${home_dir:-/root}"
}

collect_document_dirs() {
  local doc_roots=()
  while IFS= read -r item; do
    [[ -n "$item" ]] || continue
    doc_roots+=("$item")
  done < <(collect_document_root_dirs)

  local result=()
  local item=""
  for item in "${doc_roots[@]}"; do
    result+=("$item/NetMon")
    result+=("$item/Log-Pics")
  done
  printf '%s\n' "${result[@]}"
}

collect_document_root_dirs() {
  local docs_dirs=()
  local user_home
  user_home="$(target_home)"
  local xdg_docs="${XDG_DOCUMENTS_DIR:-}"
  if [[ -n "$xdg_docs" ]]; then
    docs_dirs+=("${xdg_docs/#\~/$user_home}")
  fi
  docs_dirs+=("$user_home/Documents" "$user_home/Dokumente")

  local unique=()
  local item=""
  for item in "${docs_dirs[@]}"; do
    item="${item%/}"
    [[ -n "$item" ]] || continue
    local seen=0
    local existing=""
    for existing in "${unique[@]}"; do
      if [[ "$existing" == "$item" ]]; then
        seen=1
        break
      fi
    done
    [[ "$seen" -eq 1 ]] || unique+=("$item")
  done
  printf '%s\n' "${unique[@]}"
}

remove_path_if_exists() {
  local target="$1"
  if [[ -e "$target" || -L "$target" ]]; then
    rm -rf -- "$target"
    say "$(format_msg "$(tr_msg removed)" "$target")"
  else
    say "$(format_msg "$(tr_msg skipped_missing)" "$target")"
  fi
}

detect_netmon_language() {
  local user_home
  user_home="$(target_home)"
  local paths=(
    "$user_home/.config/netmon/config.json"
  )

  local doc_root=""
  while IFS= read -r doc_root; do
    [[ -n "$doc_root" ]] || continue
    paths+=("$doc_root/NetMon/Config/config.json")
  done < <(collect_document_root_dirs)

  local detected=""
  detected="$(NETMON_UNINSTALL_PATHS="$(printf '%s\n' "${paths[@]}")" python3 - <<'PY'
import json
import os

raw = os.environ.get("NETMON_UNINSTALL_PATHS", "")
for path in [line.strip() for line in raw.splitlines() if line.strip()]:
    try:
        with open(os.path.abspath(os.path.expanduser(path)), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        continue
    if not isinstance(data, dict):
        continue
    lang = str(data.get("language", "") or "").strip().lower()
    if lang in {"de", "en"}:
        print(lang)
        raise SystemExit(0)
print("")
PY
)"
  if [[ "$detected" == "en" || "$detected" == "de" ]]; then
    NETMON_LANG_CODE="$detected"
  elif [[ "${LANG:-}" == en* || "${LANGUAGE:-}" == en* ]]; then
    NETMON_LANG_CODE="en"
  else
    NETMON_LANG_CODE="de"
  fi
}

choice_label() {
  if [[ "${1:-}" == "ja" || "${1:-}" == "yes" ]]; then
    tr_msg yes
  else
    tr_msg no
  fi
}

remove_user_launchers() {
  local user_home
  user_home="$(target_home)"
  local app_entry_dir="$user_home/.local/share/applications"
  local targets=(
    "$app_entry_dir/netmon-radio.desktop"
    "$app_entry_dir/netmon-radio-runtime.desktop"
    "$app_entry_dir/netmon.desktop"
  )
  local target=""
  for target in "${targets[@]}"; do
    remove_path_if_exists "$target"
  done
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$app_entry_dir" >/dev/null 2>&1 || true
  fi
}

remove_user_data() {
  local preserve_secure_browsers="${1:-ja}"
  local user_home
  user_home="$(target_home)"
  local targets=(
    "$user_home/.config/netmon"
    "$user_home/.local/state/netmon"
    "$user_home/.cache/netmon"
    "$user_home/.cache/netmon_roots"
    "$user_home/.local/share/netmon"
  )
  local target=""
  for target in "${targets[@]}"; do
    remove_path_if_exists "$target"
  done

  local doc_root=""
  while IFS= read -r doc_root; do
    [[ -n "$doc_root" ]] || continue
    local netmon_docs="$doc_root/NetMon"
    local secure_browser_dir="$netmon_docs/Secure Browser"
    if [[ "$preserve_secure_browsers" == "ja" && -d "$secure_browser_dir" ]]; then
      local child=""
      while IFS= read -r -d '' child; do
        [[ "$child" == "$secure_browser_dir" ]] && continue
        remove_path_if_exists "$child"
      done < <(find "$netmon_docs" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
    else
      remove_path_if_exists "$netmon_docs"
    fi
    remove_path_if_exists "$doc_root/Log-Pics"
  done < <(collect_document_root_dirs)
}

remove_secure_browser_menu_entries() {
  local user_home
  user_home="$(target_home)"
  local app_entry_dir="$user_home/.local/share/applications"
  [[ -d "$app_entry_dir" ]] || return 0

  local entry=""
  while IFS= read -r -d '' entry; do
    if grep -Eq '^(Name=NetMon Secure Browser|Comment=NetMon Secure Browser)' "$entry" 2>/dev/null; then
      remove_path_if_exists "$entry"
    fi
  done < <(find "$app_entry_dir" -maxdepth 1 -type f -name '*.desktop' -print0 2>/dev/null)

  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$app_entry_dir" >/dev/null 2>&1 || true
  fi
}

remove_secure_browsers() {
  local doc_root=""
  while IFS= read -r doc_root; do
    [[ -n "$doc_root" ]] || continue
    remove_path_if_exists "$doc_root/NetMon/Secure Browser"
  done < <(collect_document_root_dirs)

  remove_secure_browser_menu_entries
}

collect_netmon_vpn_json_paths() {
  local user_home
  user_home="$(target_home)"
  local paths=(
    "$user_home/.config/netmon/$VPN_SLOT_CONFIG_FILE"
    "$user_home/.config/netmon/$PRIMARY_VPN_SLOT_CONFIG_FILE"
    "$user_home/.config/netmon/$PRIVACY_CONFIG_FILE"
    "$user_home/.local/share/netmon/wireguard"
  )

  local doc_root=""
  while IFS= read -r doc_root; do
    [[ -n "$doc_root" ]] || continue
    paths+=(
      "$doc_root/NetMon/Config/$VPN_SLOT_CONFIG_FILE"
      "$doc_root/NetMon/Config/$PRIMARY_VPN_SLOT_CONFIG_FILE"
      "$doc_root/NetMon/Config/$PRIVACY_CONFIG_FILE"
      "$doc_root/NetMon/WireGuard"
    )
  done < <(collect_document_root_dirs)

  printf '%s\n' "${paths[@]}"
}

remove_netmon_nm_connections() {
  # Validate installed code BEFORE executing it as root. No configurable helper
  # path and no import from a user-writable checkout / PYTHONPATH.
  if /usr/bin/python3 -I -c '
import os
from pathlib import Path
import stat
import sys

helper = Path("/usr/lib/netmon/netmon/core/nm_ownership.py")
try:
    for path in [*reversed(helper.parents), helper]:
        info = path.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("unprotected helper")
        if path == helper:
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("unsafe helper file")
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError("unsafe helper directory")
except (OSError, ValueError):
    print("No protected ownership helper; legacy/unproven connections retained.")
    sys.exit(0)
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", str(helper), "cleanup"])
'; then
    :
  else
    warn "Ownership verification failed; unproven connections retained."
  fi
}

remove_netmon_wireguard_artifacts() {
  local target=""
  while IFS= read -r target; do
    [[ -n "$target" ]] || continue
    remove_path_if_exists "$target"
  done < <(collect_netmon_vpn_json_paths)

  # User labels cannot prove ownership of /etc/wireguard/*.conf. Keep all
  # system configurations here; the separately confirmed bulk test-system
  # cleanup is a different, explicitly destructive operation.
}

remove_all_wireguard_conf_files() {
  if [[ ! -d "$NETMON_WIREGUARD_ROOT" ]]; then
    say "$(format_msg "$(tr_msg no_wireguard_dir)" "$NETMON_WIREGUARD_ROOT")"
    return 0
  fi

  local found=0
  local wg_path=""
  while IFS= read -r wg_path; do
    [[ -n "$wg_path" ]] || continue
    found=1
    remove_path_if_exists "$wg_path"
  done < <(find "$NETMON_WIREGUARD_ROOT" -maxdepth 1 -type f -name '*.conf' 2>/dev/null | sort)

  if [[ "$found" -eq 0 ]]; then
    say "$(format_msg "$(tr_msg no_wireguard_profiles)" "$NETMON_WIREGUARD_ROOT")"
  fi
}

reset_netmon_dns_changes() {
  if [[ -f "$NETMON_DOT_DROPIN" ]]; then
    rm -f -- "$NETMON_DOT_DROPIN"
    say "$(format_msg "$(tr_msg removed_dot_dropin)" "$NETMON_DOT_DROPIN")"
  else
    say "$(tr_msg no_dot_dropin)"
  fi

  if command -v nmcli >/dev/null 2>&1; then
    local line=""
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      local conn_name="${line%%:*}"
      local device="${line#*:}"
      [[ -n "$conn_name" && -n "$device" ]] || continue
      case "${device,,}" in
        lo|wg*|tun*|tap*|ppp*)
          continue
          ;;
      esac
      nmcli connection modify "$conn_name" \
        ipv4.dns "" \
        ipv4.ignore-auto-dns no \
        ipv6.dns "" \
        ipv6.ignore-auto-dns no >/dev/null 2>&1 || true
      say "$(format_msg "$(tr_msg nm_dns_override_removed)" "$conn_name" "$device")"
      nmcli connection up "$conn_name" >/dev/null 2>&1 || true
    done < <(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null)
  else
    say "$(tr_msg nmcli_missing_dns_reset)"
  fi

  if command -v resolvectl >/dev/null 2>&1; then
    local iface=""
    while IFS= read -r iface; do
      [[ -n "$iface" ]] || continue
      resolvectl revert "$iface" >/dev/null 2>&1 || true
    done < <(ip -o link show 2>/dev/null | awk -F': ' '{print $2}')
    resolvectl flush-caches >/dev/null 2>&1 || true
  fi

  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart systemd-resolved >/dev/null 2>&1 || true
    systemctl restart NetworkManager >/dev/null 2>&1 || true
  fi
}

reset_ufw() {
  if ! command -v ufw >/dev/null 2>&1; then
    say "$(tr_msg ufw_missing_reset)"
    return 0
  fi
  ufw --force disable >/dev/null 2>&1 || true
  ufw --force reset
  say "$(tr_msg ufw_reset_done)"
}

purge_optional_packages() {
  require_cmd apt-get
  apt-get remove -y "${OPTIONAL_PACKAGES[@]}" || true
}

purge_netmon_package() {
  require_cmd apt-get
  if dpkg -s "$NETMON_PACKAGE" >/dev/null 2>&1; then
    apt-get remove -y "$NETMON_PACKAGE"
  else
    say "$(format_msg "$(tr_msg package_not_installed)" "$NETMON_PACKAGE")"
  fi
}

print_summary() {
  say ""
  say "$(tr_msg summary_title)"
  say "============================="
  printf '%-32s %s\n' "$(tr_msg summary_remove_package)" "$(choice_label "$1")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_launchers)" "$(choice_label "$2")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_user_files)" "$(choice_label "$3")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_secure_browsers)" "$(choice_label "$4")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_wireguard_artifacts)" "$(choice_label "$5")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_all_wireguard_confs)" "$(choice_label "$6")"
  printf '%-32s %s\n' "$(tr_msg summary_remove_nm_connections)" "$(choice_label "$7")"
  printf '%-32s %s\n' "$(tr_msg summary_reset_dns_nm)" "$(choice_label "$8")"
  printf '%-32s %s\n' "$(tr_msg summary_reset_firewall)" "$(choice_label "$9")"
  printf '%-32s %s\n' "$(tr_msg summary_purge_optional)" "$(choice_label "${10}")"
  say ""
}

main() {
  ensure_root "$@"
  detect_netmon_language

  local remove_package="ja"
  local remove_launchers="ja"
  local remove_user_files="nein"
  local remove_secure_browsers="nein"
  local remove_wireguard_artifacts="nein"
  local remove_all_wireguard_confs="nein"
  local remove_nm_vpn_connections="nein"
  local reset_dns_nm="ja"
  local reset_firewall="nein"
  local purge_optional="nein"

  say "$(tr_msg uninstaller_title)"
  say "=================="
  say "$(tr_msg uninstaller_intro_1)"
  say "$(tr_msg uninstaller_intro_2)"
  say ""
  warn "$(tr_msg uninstaller_warn_optional_resets)"
  say ""

  prompt_yes_no "$(tr_msg prompt_remove_package)" "y" && remove_package="ja" || remove_package="nein"
  prompt_yes_no "$(tr_msg prompt_remove_launchers)" "y" && remove_launchers="ja" || remove_launchers="nein"
  prompt_yes_no "$(tr_msg prompt_remove_user_files)" "n" && remove_user_files="ja" || remove_user_files="nein"
  prompt_yes_no "$(tr_msg prompt_remove_secure_browsers)" "n" && remove_secure_browsers="ja" || remove_secure_browsers="nein"
  prompt_yes_no "$(tr_msg prompt_remove_wireguard_artifacts)" "n" && remove_wireguard_artifacts="ja" || remove_wireguard_artifacts="nein"
  prompt_yes_no "$(tr_msg prompt_remove_all_wireguard_confs)" "n" && remove_all_wireguard_confs="ja" || remove_all_wireguard_confs="nein"
  prompt_yes_no "$(tr_msg prompt_remove_nm_connections)" "n" && remove_nm_vpn_connections="ja" || remove_nm_vpn_connections="nein"
  prompt_yes_no "$(tr_msg prompt_reset_dns_nm)" "y" && reset_dns_nm="ja" || reset_dns_nm="nein"
  prompt_yes_no "$(tr_msg prompt_reset_firewall)" "n" && reset_firewall="ja" || reset_firewall="nein"
  prompt_yes_no "$(tr_msg prompt_purge_optional)" "n" && purge_optional="ja" || purge_optional="nein"

  print_summary \
    "$remove_package" \
    "$remove_launchers" \
    "$remove_user_files" \
    "$remove_secure_browsers" \
    "$remove_wireguard_artifacts" \
    "$remove_all_wireguard_confs" \
    "$remove_nm_vpn_connections" \
    "$reset_dns_nm" \
    "$reset_firewall" \
    "$purge_optional"

  prompt_yes_no "$(tr_msg prompt_execute_now)" "n" || {
    say "$(tr_msg cancelled)"
    pause_before_exit
    exit 0
  }

  ensure_netmon_not_running

  [[ "$remove_launchers" == "ja" ]] && remove_user_launchers
  [[ "$remove_nm_vpn_connections" == "ja" ]] && remove_netmon_nm_connections
  [[ "$remove_wireguard_artifacts" == "ja" ]] && remove_netmon_wireguard_artifacts
  [[ "$remove_all_wireguard_confs" == "ja" ]] && remove_all_wireguard_conf_files
  [[ "$remove_secure_browsers" == "ja" ]] && remove_secure_browsers
  if [[ "$remove_user_files" == "ja" ]]; then
    local preserve_secure_browsers="ja"
    [[ "$remove_secure_browsers" == "ja" ]] && preserve_secure_browsers="nein"
    remove_user_data "$preserve_secure_browsers"
  fi
  [[ "$reset_dns_nm" == "ja" ]] && reset_netmon_dns_changes
  [[ "$reset_firewall" == "ja" ]] && reset_ufw
  [[ "$purge_optional" == "ja" ]] && purge_optional_packages
  [[ "$remove_package" == "ja" ]] && purge_netmon_package

  say ""
  say "$(tr_msg finished)"
  pause_before_exit
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
