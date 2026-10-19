#!/usr/bin/env bash

set -uo pipefail
umask 077

if (( $# > 1 )) || [[ ${1-x} == "" ]]; then
    printf 'Usage: %s [new-output-file]\n' "$0" >&2
    exit 2
fi

collect_diagnostics() {
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
        } 2>&1
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
    }

    run_section "Processes (ps -eo ...)" ps -eo pid,ppid,user,stat,comm,args --width 300
    run_section "Processes (ps -efww)" ps -efww
    run_section "Listening Sockets" ss -tulpn
    run_section "Kernel Journal (filtered)" sh -c "journalctl -k -b --no-pager | grep -Ei 'error|warn|fail|denied|oom|segfault|amdgpu|nvidia|veth|iptables|ufw' || true"
    run_section "Kernel Journal (full boot)" journalctl -k -b --no-pager
    run_section "Kernel Ring Buffer (last 300)" sh -c 'dmesg -T | tail -n 300'

}

# The writer stages privately and publishes only a complete file, without replacement.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit 1
collect_diagnostics | python3 "$script_dir/diagnostics_output.py" "$@"
