#!/usr/bin/env bash
set -u

have() {
  command -v "$1" >/dev/null 2>&1
}

ok() {
  printf "OK   %s\n" "$1"
}

miss() {
  printf "MISS %s\n" "$1"
}

check_cmd() {
  local cmd="$1"
  local label="${2:-$1}"
  if have "$cmd"; then
    ok "$label"
    return 0
  fi
  miss "$label"
  return 1
}

echo "== NetMon Dependency Check =="
echo
echo "[Pflicht]"
req_missing=0
check_cmd sudo || req_missing=$((req_missing + 1))
check_cmd ip "ip (iproute2)" || req_missing=$((req_missing + 1))
check_cmd ping "ping (iputils-ping)" || req_missing=$((req_missing + 1))
check_cmd curl || req_missing=$((req_missing + 1))
check_cmd wg "wg (wireguard-tools)" || req_missing=$((req_missing + 1))
check_cmd wg-quick "wg-quick (wireguard-tools)" || req_missing=$((req_missing + 1))
check_cmd ufw || req_missing=$((req_missing + 1))

echo
echo "[Optional]"
check_cmd nmcli "nmcli (network-manager)" || true
if have dig || have nslookup; then
  ok "dnsutils (dig/nslookup)"
else
  miss "dnsutils (dig/nslookup)"
fi
if have tracepath || have traceroute; then
  ok "tracepath/traceroute"
else
  miss "tracepath/traceroute"
fi
check_cmd traceroute "traceroute (Hops-Ansicht)" || true
check_cmd ss "ss (iproute2)" || true
check_cmd resolvectl "resolvectl (systemd-resolved)" || true
check_cmd find || true
check_cmd install "install (coreutils)" || true

echo
echo "[Sudo -n Test]"
if sudo -n true >/dev/null 2>&1; then
  ok "sudo -n ohne Passwort (NOPASSWD)"
else
  miss "sudo -n ohne Passwort (NOPASSWD)"
fi

echo
echo "[Install-Vorschlag Debian/RPi]"
echo "sudo apt update"
echo "sudo apt install -y wireguard-tools ufw iproute2 iputils-ping curl traceroute dnsutils network-manager"

echo
if [ "$req_missing" -eq 0 ]; then
  echo "Ergebnis: Pflicht-Abhaengigkeiten vorhanden."
  exit 0
fi
echo "Ergebnis: Pflicht-Abhaengigkeiten fehlen ($req_missing)."
exit 1
