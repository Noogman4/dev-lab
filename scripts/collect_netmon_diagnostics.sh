#!/usr/bin/env bash

set -u

timestamp="$(date +%Y%m%d_%H%M%S)"
output_path="${1:-/tmp/netmon_diagnostics_${timestamp}.txt}"

mkdir -p "$(dirname "$output_path")"

run_section() {
    local title="$1"
    shift

    {
        printf '\n'
        printf '================================================================================\n'
        printf '%s\n' "$title"
        printf '================================================================================\n'
        printf 'COMMAND:'
        for arg in "$@"; do
            printf ' %q' "$arg"
        done
        printf '\n\n'
        "$@"
        printf '\n'
    } >>"$output_path" 2>&1
}

{
    printf 'NetMon Diagnostics Bundle\n'
    printf 'Created: %s\n' "$(date --iso-8601=seconds)"
    printf 'Host: %s\n' "$(hostname 2>/dev/null || printf 'unknown')"
    printf 'User: %s\n' "${USER:-unknown}"
    printf 'Kernel: %s\n' "$(uname -srmo 2>/dev/null || printf 'unknown')"
    printf '\n'
    printf 'Hinweis: Diese Datei kann sensible Daten enthalten.\n'
    printf 'Bitte vor dem Weitergeben auf Tokens, API-Keys, Passwoerter und interne Pfade pruefen.\n'
    printf '\n'
} >"$output_path"

run_section "Docker Containers" docker ps -a
run_section "Docker Inspect" sh -c 'ids="$(docker ps -aq 2>/dev/null)"; if [ -n "$ids" ]; then docker inspect $ids; else echo "No containers found."; fi'
run_section "Processes (ps -eo ...)" ps -eo pid,ppid,user,stat,comm,args --width 300
run_section "Processes (ps -efww)" ps -efww
run_section "Listening Sockets" ss -tulpn
run_section "Kernel Journal (filtered)" sh -c "journalctl -k -b --no-pager | grep -Ei 'error|warn|fail|denied|oom|segfault|amdgpu|nvidia|docker|veth|iptables|ufw' || true"
run_section "Kernel Journal (full boot)" journalctl -k -b --no-pager
run_section "Kernel Ring Buffer (last 300)" sh -c 'dmesg -T | tail -n 300'

printf 'Diagnostics written to %s\n' "$output_path"
