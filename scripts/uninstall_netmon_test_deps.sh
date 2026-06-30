#!/usr/bin/env bash
set -euo pipefail

PACKAGES=(
  netmon
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

usage() {
  cat <<'EOF'
NetMon test dependency cleanup

Default:
  Zeigt nur die auszufuehrenden Befehle an.

Usage:
  bash scripts/uninstall_netmon_test_deps.sh
  bash scripts/uninstall_netmon_test_deps.sh --run

Hinweise:
  - Entfernt bewusst keine kritischen Systempakete wie python3, network-manager,
    systemd-resolved, iproute2 oder cryptsetup.
  - Entfernt zusaetzlich nur NetMon-nahe Test-/Feature-Abhaengigkeiten.
EOF
}

print_commands() {
  printf 'sudo apt remove -y'
  printf ' %q' "${PACKAGES[@]}"
  printf '\n'
}

run_cleanup() {
  sudo apt remove -y "${PACKAGES[@]}"
}

main() {
  case "${1:-}" in
    "")
      print_commands
      ;;
    --run)
      run_cleanup
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
}

main "${1:-}"
