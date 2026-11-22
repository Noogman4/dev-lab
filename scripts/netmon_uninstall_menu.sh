#!/bin/bash -p
set -euo pipefail

# No caller-selected package, executable search path or user-data authority.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
readonly NETMON_PACKAGE=netmon
readonly NETMON_MANAGER_PACKAGE=netmon-manager
NETMON_LANG_CODE="${NETMON_LANG_CODE:-}"
USER_CLEANUP_MODE=execute

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
    en:dns_reset_blocked) printf '%s' "DHCP/ISP DNS release is temporarily blocked (F6). DNS configuration is preserved." ;;
    de:dns_reset_blocked|*:dns_reset_blocked) printf '%s' "DHCP-/ISP-DNS-Freigabe vorläufig gesperrt (F6). Die DNS-Konfiguration bleibt erhalten." ;;
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
    en:mode_title) printf '%s' "Choose an operation:" ;;
    de:mode_title|*:mode_title) printf '%s' "Gewünschten Ablauf wählen:" ;;
    en:mode_update) printf '%s' "1) Update from a local .deb (verified backup, retain user data)" ;;
    de:mode_update|*:mode_update) printf '%s' "1) Aktualisieren mit lokaler .deb (geprüftes Backup, Benutzerdaten behalten)" ;;
    en:mode_keep) printf '%s' "2) Uninstall — retain settings and personal files (default)" ;;
    de:mode_keep|*:mode_keep) printf '%s' "2) Deinstallieren – Einstellungen und persönliche Dateien behalten (Standard)" ;;
    en:mode_delete) printf '%s' "3) Uninstall — delete user data after reviewing exact paths" ;;
    de:mode_delete|*:mode_delete) printf '%s' "3) Deinstallieren – Benutzerdaten nach genauer Pfadprüfung löschen" ;;
    en:mode_cancel) printf '%s' "0) Cancel" ;;
    de:mode_cancel|*:mode_cancel) printf '%s' "0) Abbrechen" ;;
    en:keep_binding) printf '%s' "Settings, documents, browser profiles, VPN slots and profile files will be retained." ;;
    de:keep_binding|*:keep_binding) printf '%s' "Einstellungen, Dokumente, Browserprofile, VPN-Slots und Profildateien bleiben erhalten." ;;
    en:removal_tunnels) printf '%s' "Package removal may disconnect verified NetMon-owned WireGuard tunnels; saved profiles are retained unless explicitly selected for deletion." ;;
    de:removal_tunnels|*:removal_tunnels) printf '%s' "Beim Entfernen können nachweislich NetMon-eigene WireGuard-Tunnel getrennt werden; gespeicherte Profile bleiben ohne ausdrückliche Löschwahl erhalten." ;;
    en:invalid_plan) printf '%s' "Conflicting choices: retaining data forbids profile, browser and VPN deletion." ;;
    de:invalid_plan|*:invalid_plan) printf '%s' "Widersprüchliche Auswahl: Daten behalten verbietet das Löschen von Profilen, Browsern und VPN-Daten." ;;
    en:package_path) printf '%s' "Absolute path to the new NetMon .deb: " ;;
    de:package_path|*:package_path) printf '%s' "Absoluter Pfad zur neuen NetMon-.deb: " ;;
    en:backup_parent) printf '%s' "Backup destination (Enter accepts the displayed default): " ;;
    de:backup_parent|*:backup_parent) printf '%s' "Sicherungsordner (Enter übernimmt den angezeigten Vorschlag): " ;;
    en:operation_duration) printf '%s' "Preparation, backup, verification and installation may take several minutes depending on the data and storage device. Please keep the terminal open until completion. Individual steps may take longer without a new progress message." ;;
    de:operation_duration|*:operation_duration) printf '%s' "Vorbereitung, Sicherung, Prüfung und Installation können je nach Datenmenge und Datenträger mehrere Minuten dauern. Bitte das Terminal bis zum Abschluss geöffnet lassen. Einzelne Schritte können länger ohne neue Fortschrittsmeldung dauern." ;;
    en:invalid_package) printf '%s' "Update requires an installed NetMon and a newer netmon package for this architecture." ;;
    de:invalid_package|*:invalid_package) printf '%s' "Für das Update werden ein installiertes NetMon und ein neueres netmon-Paket für diese Architektur benötigt." ;;
    en:update_summary) printf '%s' "Verified backup; update directly in place. Personal data and optional packages are retained." ;;
    de:update_summary|*:update_summary) printf '%s' "Backup geprüft; direkte Paketaktualisierung. Benutzerdaten und optionale Pakete bleiben erhalten." ;;
    en:local_package_warning) printf '%s' "Install only a .deb from a trusted source. This local workflow does not verify a publisher signature." ;;
    de:local_package_warning|*:local_package_warning) printf '%s' "Nur eine .deb aus vertrauenswürdiger Quelle verwenden. Dieser lokale Ablauf prüft keine Herausgebersignatur." ;;
    en:custom_documents_manual) printf '%s' "External or redirected Documents folder retained; review it manually:" ;;
    de:custom_documents_manual|*:custom_documents_manual) printf '%s' "Externer oder umgeleiteter Dokumentenordner bleibt erhalten; bitte manuell prüfen:" ;;
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

  local pattern='(^|[[:space:]])(/usr/bin/netmon|([^[:space:]]*/)?python3(\.[0-9]+)*[[:space:]]+-m[[:space:]]+netmon(\.main|\.netmon_radio_app)?|([^[:space:]]*/)?netmon/(main|app)\.py|([^[:space:]]*/)?netmon_radio_app\.py|netmon\.netmon_radio_app)([[:space:]]|$)'
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

is_root() {
  [[ "$EUID" -eq 0 ]]
}

ensure_root() {
  if is_root; then
    return 0
  fi
  if [[ -x /usr/bin/sudo ]]; then
    say "$(tr_msg requesting_sudo)"
    # sudo supplies the caller identity. The protected bootstrap carries only
    # that identity into a clean environment and executes the installed script.
    exec /usr/bin/sudo -- /bin/bash -p -c '
exec /usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 \
  SUDO_USER="${SUDO_USER:?}" SUDO_UID="${SUDO_UID:?}" \
  /bin/bash -p /usr/bin/netmon-uninstall "$@"
' netmon-uninstall "$@"
  fi
  warn "$(tr_msg start_as_root)"
  exit 1
}

target_user() {
  if [[ -n "${SUDO_USER:-}" || -n "${SUDO_UID:-}" ]]; then
    [[ "${SUDO_UID:-}" =~ ^[0-9]+$ && -n "${SUDO_USER:-}" ]] || return 1
    local record name _password uid _rest
    record="$(getent passwd "$SUDO_UID")" || return 1
    [[ "$record" != *$'\n'* ]] || return 1
    IFS=: read -r name _password uid _rest <<< "$record"
    [[ "$name" == "$SUDO_USER" && "$uid" == "$SUDO_UID" ]] || return 1
    printf '%s\n' "$name"
  else
    id -un
  fi
}

target_home() {
  local user_name
  user_name="$(target_user)" || return 1
  local record name _password _uid _gid _description home_dir _shell canonical
  record="$(getent passwd "$user_name")" || return 1
  [[ "$record" != *$'\n'* ]] || return 1
  IFS=: read -r name _password _uid _gid _description home_dir _shell <<< "$record"
  [[ "$name" == "$user_name" && "$home_dir" == /* && "$home_dir" != / ]] || return 1
  [[ "$home_dir" != *[[:cntrl:]]* ]] || return 1
  canonical="$(realpath -e -- "$home_dir")" || return 1
  [[ "$canonical" == "$home_dir" && -d "$canonical" ]] || return 1
  printf '%s\n' "$canonical"
}

run_user_lifecycle() {
  case "${1:-}" in documents|backup) ;; *) return 1 ;; esac
  local user_name user_home
  user_name="$(target_user)" || return 1
  user_home="$(target_home)" || return 1
  local command=(/usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8
    HOME="$user_home" USER="$user_name" LOGNAME="$user_name"
    /usr/bin/python3 -I -c
    'import sys; sys.path.insert(0, "/usr/lib/netmon-manager"); from netmon.core.lifecycle import main; sys.exit(main())')
  if is_root; then
    [[ "$(id -u "$user_name")" != 0 ]] || return 1
    /usr/sbin/runuser -u "$user_name" -- "${command[@]}" "$@"
  else
    "${command[@]}" "$@"
  fi
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
  user_home="$(target_home)" || return 1
  # Never turn an inherited XDG override into a privileged deletion target.
  docs_dirs+=("$user_home/Documents" "$user_home/Dokumente")
  # Read the saved XDG setting as the account, never trust a caller override.
  # Deletion remains unprivileged and confined to the passwd-verified home.
  local configured canonical
  if configured="$(run_user_lifecycle documents 2>/dev/null)" && [[ -n "$configured" ]]; then
    canonical="$(realpath -m -- "$configured")" || return 1
    if [[ "$configured" != *[[:cntrl:]]* && "$configured" == "$canonical" && "$canonical" == "$user_home/"* ]]; then
      docs_dirs+=("$configured")
    else
      warn "$(tr_msg custom_documents_manual) $configured"
    fi
  fi

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
  [[ "$target" != *[[:cntrl:]]* ]] || { warn "Ungültiger Dateiname im Bereinigungsziel."; return 1; }
  if ! is_root; then
    local home_dir canonical
    home_dir="$(target_home)" || return 1
    canonical="$(realpath -m -- "$target")" || return 1
    if [[ "$canonical" != "$home_dir/"* || "$canonical" != "$target" ]]; then
      warn "Unsicheres Benutzerziel; keine automatische Bereinigung: $target"
      return 1
    fi
  fi
  if [[ "$USER_CLEANUP_MODE" == preview ]]; then
    printf '  %s\n' "$target"
    return 0
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    rm -rf -- "$target"
    say "$(format_msg "$(tr_msg removed)" "$target")"
  else
    say "$(format_msg "$(tr_msg skipped_missing)" "$target")"
  fi
}

detect_netmon_language() {
  local user_home
  user_home="$(target_home)" || return 1
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
  user_home="$(target_home)" || return 1
  local app_entry_dir="$user_home/.local/share/applications"
  local targets=(
    "$app_entry_dir/netmon-radio.desktop"
    "$app_entry_dir/netmon-radio-runtime.desktop"
    "$app_entry_dir/netmon.desktop"
  )
  local target=""
  for target in "${targets[@]}"; do
    remove_path_if_exists "$target" || return 1
  done
  if [[ "$USER_CLEANUP_MODE" != preview ]] && command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$app_entry_dir" >/dev/null 2>&1 || true
  fi
}

remove_user_data() {
  local preserve_secure_browsers="${1:-ja}"
  local user_home
  user_home="$(target_home)" || return 1
  local targets=(
    "$user_home/.config/netmon"
    "$user_home/.local/state/netmon"
    "$user_home/.cache/netmon"
    "$user_home/.cache/netmon_roots"
    "$user_home/.local/share/netmon"
  )
  local target=""
  for target in "${targets[@]}"; do
    remove_path_if_exists "$target" || return 1
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
        remove_path_if_exists "$child" || return 1
      done < <(find "$netmon_docs" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
    else
      remove_path_if_exists "$netmon_docs" || return 1
    fi
    remove_path_if_exists "$doc_root/Log-Pics" || return 1
  done < <(collect_document_root_dirs)
}

remove_secure_browser_menu_entries() {
  local user_home
  user_home="$(target_home)" || return 1
  local app_entry_dir="$user_home/.local/share/applications"
  [[ -d "$app_entry_dir" ]] || return 0

  local entry=""
  while IFS= read -r -d '' entry; do
    if grep -Eq '^(Name=NetMon Secure Browser|Comment=NetMon Secure Browser)' "$entry" 2>/dev/null; then
      remove_path_if_exists "$entry" || return 1
    fi
  done < <(find "$app_entry_dir" -maxdepth 1 -type f -name '*.desktop' -print0 2>/dev/null)

  if [[ "$USER_CLEANUP_MODE" != preview ]] && command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$app_entry_dir" >/dev/null 2>&1 || true
  fi
}

remove_secure_browsers() {
  local doc_root=""
  while IFS= read -r doc_root; do
    [[ -n "$doc_root" ]] || continue
    remove_path_if_exists "$doc_root/NetMon/Secure Browser" || return 1
  done < <(collect_document_root_dirs)

  remove_secure_browser_menu_entries
}

collect_netmon_vpn_json_paths() {
  local user_home
  user_home="$(target_home)" || return 1
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

helper = Path("/usr/lib/netmon-manager/netmon/core/nm_ownership.py")
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
    remove_path_if_exists "$target" || return 1
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
    remove_path_if_exists "$wg_path" || return 1
  done < <(find "$NETMON_WIREGUARD_ROOT" -maxdepth 1 -type f -name '*.conf' 2>/dev/null | sort)

  if [[ "$found" -eq 0 ]]; then
    say "$(format_msg "$(tr_msg no_wireguard_profiles)" "$NETMON_WIREGUARD_ROOT")"
  fi
}

reset_netmon_dns_changes() {
  warn "$(tr_msg dns_reset_blocked)"
  return 1
}

check_firewall_transaction() {
  # The installed, root-owned helper is authoritative. Check before cleanup,
  # not only in dpkg's prerm after the optional reset has already happened.
  if [[ -e /var/lib/netmon/ufw-snapshot || -L /var/lib/netmon/ufw-snapshot ]]; then
    if ! /usr/bin/python3 -I -c '
import os, stat, sys
path = "/usr/lib/netmon-manager/netmon/core/ufw_snapshot.py"
current = "/"
for part in [""] + path.strip("/").split("/"):
    current = os.path.join(current, part)
    info = os.lstat(current)
    if info.st_uid != 0 or info.st_mode & 0o022:
        sys.exit("Unprotected removal helper")
    if current == path:
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            sys.exit("Unsafe removal helper")
    elif not stat.S_ISDIR(info.st_mode):
        sys.exit("Unsafe helper directory")
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path, "removal"])
' >/dev/null <<'JSON'
{}
JSON
    then
      warn "NetMon: aktive oder ungeklärte Firewall-Transaktion. Bereinigung abgebrochen; zuerst verifiziert wiederherstellen."
      return 1
    fi
  fi
}

run_checked_cleanup() {
  check_firewall_transaction || exit 1
  case "$1" in
    remove_user_launchers|remove_user_data|remove_secure_browsers|remove_netmon_wireguard_artifacts)
      run_user_cleanup execute "$@" ;;
    *) "$@" ;;
  esac
}

run_user_cleanup() {
  local mode="$1" operation="$2"
  shift 2
  [[ "$mode" == preview || "$mode" == execute ]] || return 1
  case "$operation" in
    remove_user_launchers|remove_user_data|remove_secure_browsers|remove_netmon_wireguard_artifacts) ;;
    *) return 1 ;;
  esac
  if is_root; then
    local user_name user_home
    user_name="$(target_user)" || return 1
    user_home="$(target_home)" || return 1
    if [[ "$(id -u "$user_name")" == 0 ]]; then
      warn "Keine automatische Benutzerdatei-Bereinigung für root."
      return 0
    fi
    /usr/sbin/runuser -u "$user_name" -- /usr/bin/env -i \
      PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 \
      HOME="$user_home" USER="$user_name" LOGNAME="$user_name" \
      /bin/bash -p /usr/bin/netmon-uninstall --user-cleanup "$mode" "$operation" "$@"
  else
    USER_CLEANUP_MODE="$mode" "$operation" "$@"
  fi
}

reset_ufw() {
  check_firewall_transaction || return 1
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

remove_manager_only() {
  say "NetMon verwalten / Manage NetMon: $NETMON_MANAGER_PACKAGE"
  say "Nur die Verwaltung entfernen. NetMon, Benutzerdaten und externe Sicherungen bleiben erhalten."
  say "Remove management only. NetMon, personal data and external backups are retained."
  prompt_yes_no "NetMon verwalten wirklich entfernen? / Really remove management?" "n" || {
    say "$(tr_msg cancelled)"
    return 0
  }
  require_cmd apt-get
  apt-get remove -y "$NETMON_MANAGER_PACKAGE"
}

remove_selected_packages() {
  local app="$1" manager="$2"
  local packages=()
  [[ "$app" != ja ]] || packages+=("$NETMON_PACKAGE")
  [[ "$manager" != ja ]] || packages+=("$NETMON_MANAGER_PACKAGE")
  (( ${#packages[@]} )) || return 0
  require_cmd apt-get
  apt-get remove -y "${packages[@]}"
}

print_summary() {
  local user_name user_home
  user_name="$(target_user)" || return 1
  user_home="$(target_home)" || return 1
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
  say "Paket / package: $NETMON_PACKAGE"
  say "Benutzer / user: $user_name"
  say "Home: $user_home"
  say "Dateiziele / file targets:"
  [[ "$2" != ja ]] || run_user_cleanup preview remove_user_launchers || return 1
  if [[ "$3" == ja ]]; then
    local preserve=ja
    [[ "$4" != ja ]] || preserve=nein
    run_user_cleanup preview remove_user_data "$preserve" || return 1
  fi
  [[ "$4" != ja ]] || run_user_cleanup preview remove_secure_browsers || return 1
  [[ "$5" != ja ]] || run_user_cleanup preview remove_netmon_wireguard_artifacts || return 1
  if [[ "$6" == ja ]]; then
    find "$NETMON_WIREGUARD_ROOT" -maxdepth 1 -type f -name '*.conf' -print 2>/dev/null || true
  fi
  [[ "${10}" != ja ]] || printf 'Optionale Pakete / optional packages: %s\n' "${OPTIONAL_PACKAGES[*]}"
  say ""
}

select_operation() {
  local answer
  say "$(tr_msg mode_title)" >&2
  say "$(tr_msg mode_update)" >&2
  say "$(tr_msg mode_keep)" >&2
  say "$(tr_msg mode_delete)" >&2
  say "$(tr_msg mode_cancel)" >&2
  while true; do
    printf '> ' >&2
    read -r answer || { printf 'cancel\n'; return; }
    case "$answer" in
      1) printf 'update\n'; return ;;
      2|'') printf 'keep\n'; return ;;
      3) printf 'delete\n'; return ;;
      0) printf 'cancel\n'; return ;;
    esac
  done
}

validate_uninstall_choices() {
  local mode="$1"
  shift
  [[ "$mode" == keep || "$mode" == delete ]] || return 1
  if [[ "$mode" == keep ]]; then
    local choice
    for choice in "$@"; do
      [[ "$choice" == nein ]] || { warn "$(tr_msg invalid_plan)"; return 1; }
    done
  fi
}

stage_update_package() {
  # The root-owned snapshot prevents replacing the chosen package after review.
  /usr/bin/python3 -I -c '
import hashlib, os, stat, sys
source, destination = sys.argv[1:]
fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
with os.fdopen(fd, "rb") as incoming:
    before = os.fstat(incoming.fileno())
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 4 * 1024**3:
        raise ValueError("Not a regular DEB within the size limit")
    with open(destination, "xb") as outgoing:
        remaining = before.st_size
        while remaining:
            chunk = incoming.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("Package became shorter while copying")
            outgoing.write(chunk)
            remaining -= len(chunk)
        if incoming.read(1):
            raise ValueError("Package grew while copying")
        outgoing.flush()
        os.fsync(outgoing.fileno())
    after = os.fstat(incoming.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Package changed while copying")
with open(destination, "rb") as stream:
    print(hashlib.file_digest(stream, "sha256").hexdigest())
' "$1" "$2"
}

perform_update() (
  local package_path staging='' snapshot digest candidate installed architecture documents parent receipt
  trap '[[ -z "$staging" ]] || rm -rf -- "$staging"' EXIT
  ensure_netmon_not_running
  check_firewall_transaction || return 1
  printf '%s' "$(tr_msg package_path)"
  read -r package_path || return 1
  [[ "$package_path" == /* && "$package_path" != *[[:cntrl:]]* ]] || return 1
  say "$(tr_msg operation_duration)"
  staging="$(mktemp -d /var/tmp/netmon-update.XXXXXXXX)" || return 1
  snapshot="$staging/netmon.deb"
  digest="$(stage_update_package "$package_path" "$snapshot")" || return 1
  candidate="$(dpkg-deb -f "$snapshot" Version)" || return 1
  architecture="$(dpkg-deb -f "$snapshot" Architecture)" || return 1
  installed="$(dpkg-query -W -f='${Version}' netmon)" || return 1
  if [[ "$(dpkg-deb -f "$snapshot" Package)" != netmon ]] ||
    [[ "$(dpkg-query -W -f='${Status}' netmon)" != 'install ok installed' ]] ||
    { [[ "$architecture" != all ]] && [[ "$architecture" != "$(dpkg --print-architecture)" ]]; } ||
    ! dpkg --compare-versions "$candidate" gt "$installed"; then
    warn "$(tr_msg invalid_package)"
    return 1
  fi
  documents="$(run_user_lifecycle documents)" || return 1
  printf '%s\n' "$documents/NetMon-Sicherungen"
  printf '%s' "$(tr_msg backup_parent)"
  read -r parent || return 1
  parent="${parent:-$documents/NetMon-Sicherungen}"
  receipt="$(run_user_lifecycle backup --parent "$parent")" || return 1
  say "$(tr_msg update_summary)"
  say "NetMon: $installed -> $candidate"
  printf 'Paket / package: %s\nSHA256: %s\nBackup: %s\n' "$package_path" "$digest" "$receipt"
  warn "$(tr_msg local_package_warning)"
  prompt_yes_no "$(tr_msg prompt_execute_now)" "n" || { say "$(tr_msg cancelled)"; return 0; }
  ensure_netmon_not_running
  check_firewall_transaction || return 1
  # No uninstall step. apt is forbidden from removing other packages to solve dependencies.
  apt-get --no-remove install --no-install-recommends "$snapshot"
)

main() {
  if [[ "${1:-}" == --user-cleanup ]]; then
    # This private entry can only perform allowlisted, unprivileged file work.
    ! is_root || return 1
    [[ $# -ge 3 ]] || return 1
    shift
    run_user_cleanup "$@"
    return
  fi
  local requested_operation='' remove_manager=nein
  if [[ $# -gt 0 ]]; then
    [[ ( $# == 2 || $# == 3 ) && "$1" == --mode ]] || return 1
    case "$2" in keep|delete|manager) requested_operation="$2" ;; *) return 1 ;; esac
    if [[ $# == 3 ]]; then
      [[ "$2" == delete && "$3" == --remove-manager ]] || return 1
      remove_manager=ja
    fi
  fi
  ensure_root "$@"
  target_home >/dev/null || { warn "Benutzer-Home konnte nicht sicher ermittelt werden."; return 1; }
  detect_netmon_language
  if [[ "$requested_operation" == manager ]]; then
    remove_manager_only
    return
  fi
  check_firewall_transaction || return 1
  local operation
  if [[ -n "$requested_operation" ]]; then
    operation="$requested_operation"
  else
    operation="$(select_operation)" || return 1
  fi
  case "$operation" in
    update) perform_update; return ;;
    keep|delete) ;;
    cancel) say "$(tr_msg cancelled)"; return 0 ;;
    *) return 1 ;;
  esac

  local remove_package="ja"
  local remove_launchers="ja"
  local remove_user_files="nein"
  local remove_secure_browsers="nein"
  local remove_wireguard_artifacts="nein"
  local remove_all_wireguard_confs="nein"
  local remove_nm_vpn_connections="nein"
  local reset_dns_nm="nein"
  local reset_firewall="nein"
  local purge_optional="nein"

  say "$(tr_msg uninstaller_title)"
  say "=================="
  say "$(tr_msg uninstaller_intro_1)"
  say "$(tr_msg uninstaller_intro_2)"
  say ""
  warn "$(tr_msg uninstaller_warn_optional_resets)"
  warn "$(tr_msg removal_tunnels)"
  [[ "$operation" != keep ]] || say "$(tr_msg keep_binding)"
  say ""

  prompt_yes_no "$(tr_msg prompt_remove_package)" "y" && remove_package="ja" || remove_package="nein"
  prompt_yes_no "$(tr_msg prompt_remove_launchers)" "y" && remove_launchers="ja" || remove_launchers="nein"
  if [[ "$operation" == delete ]]; then
    remove_user_files="ja"
    prompt_yes_no "$(tr_msg prompt_remove_secure_browsers)" "n" && remove_secure_browsers="ja" || remove_secure_browsers="nein"
    prompt_yes_no "$(tr_msg prompt_remove_wireguard_artifacts)" "n" && remove_wireguard_artifacts="ja" || remove_wireguard_artifacts="nein"
    prompt_yes_no "$(tr_msg prompt_remove_all_wireguard_confs)" "n" && remove_all_wireguard_confs="ja" || remove_all_wireguard_confs="nein"
    prompt_yes_no "$(tr_msg prompt_remove_nm_connections)" "n" && remove_nm_vpn_connections="ja" || remove_nm_vpn_connections="nein"
  fi
  if [[ "$operation" == delete && "$remove_manager" != ja ]]; then
    prompt_yes_no "NetMon verwalten ebenfalls entfernen? / Also remove management?" "n" && remove_manager=ja || remove_manager=nein
  fi
  # Keeping data never removes management; removing both requires App removal.
  [[ "$remove_manager" != ja || ( "$operation" == delete && "$remove_package" == ja ) ]] || return 1
  say "$(tr_msg dns_reset_blocked)"
  prompt_yes_no "$(tr_msg prompt_reset_firewall)" "n" && reset_firewall="ja" || reset_firewall="nein"
  prompt_yes_no "$(tr_msg prompt_purge_optional)" "n" && purge_optional="ja" || purge_optional="nein"
  validate_uninstall_choices "$operation" "$remove_user_files" "$remove_secure_browsers" \
    "$remove_wireguard_artifacts" "$remove_all_wireguard_confs" "$remove_nm_vpn_connections" || return 1

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
    "$purge_optional" || return 1
  say "NetMon verwalten / Manage NetMon entfernen: $(choice_label "$remove_manager")"

  prompt_yes_no "$(tr_msg prompt_execute_now)" "n" || {
    say "$(tr_msg cancelled)"
    pause_before_exit
    exit 0
  }

  ensure_netmon_not_running
  check_firewall_transaction || return 1
  validate_uninstall_choices "$operation" "$remove_user_files" "$remove_secure_browsers" \
    "$remove_wireguard_artifacts" "$remove_all_wireguard_confs" "$remove_nm_vpn_connections" || return 1

  [[ "$remove_launchers" == "ja" ]] && run_checked_cleanup remove_user_launchers
  [[ "$remove_nm_vpn_connections" == "ja" ]] && run_checked_cleanup remove_netmon_nm_connections
  [[ "$remove_wireguard_artifacts" == "ja" ]] && run_checked_cleanup remove_netmon_wireguard_artifacts
  [[ "$remove_all_wireguard_confs" == "ja" ]] && run_checked_cleanup remove_all_wireguard_conf_files
  [[ "$remove_secure_browsers" == "ja" ]] && run_checked_cleanup remove_secure_browsers
  if [[ "$remove_user_files" == "ja" ]]; then
    local preserve_secure_browsers="ja"
    [[ "$remove_secure_browsers" == "ja" ]] && preserve_secure_browsers="nein"
    run_checked_cleanup remove_user_data "$preserve_secure_browsers"
  fi
  [[ "$reset_dns_nm" == "ja" ]] && run_checked_cleanup reset_netmon_dns_changes
  [[ "$reset_firewall" == "ja" ]] && run_checked_cleanup reset_ufw
  [[ "$purge_optional" == "ja" ]] && run_checked_cleanup purge_optional_packages
  if [[ "$remove_manager" == ja ]]; then
    run_checked_cleanup remove_selected_packages "$remove_package" "$remove_manager"
  elif [[ "$remove_package" == ja ]]; then
    run_checked_cleanup purge_netmon_package
  fi

  say ""
  say "$(tr_msg finished)"
  pause_before_exit
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
