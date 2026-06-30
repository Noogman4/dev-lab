#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${NETMON_SITE_PORT:-8765}"
URL="http://127.0.0.1:${PORT}/site/index.html"
PID_FILE="/tmp/netmon_site_http_server.pid"
LOG_FILE="/tmp/netmon_site_http_server.log"

server_running() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

wait_for_server() {
  local attempt
  for attempt in $(seq 1 20); do
    if python3 - "$PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])
try:
    sock = socket.socket()
    sock.settimeout(0.2)
    sock.connect(("127.0.0.1", port))
except OSError:
    sys.exit(1)
except PermissionError:
    sys.exit(2)
finally:
    try:
        sock.close()
    except Exception:
        pass
sys.exit(0)
PY
    then
      return 0
    fi
    status=$?
    if [[ $status -eq 2 ]]; then
      sleep 0.5
      server_running && return 0
    fi
    sleep 0.2
  done
  return 1
}

start_server() {
  (
    cd "$ROOT_DIR"
    nohup python3 -m http.server "$PORT" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
}

if server_running; then
  echo "NetMon Website-Server laeuft bereits."
else
  echo "Starte NetMon Website-Server auf Port ${PORT}..."
  start_server
fi

if ! wait_for_server; then
  echo "Server konnte nicht gestartet werden. Log: $LOG_FILE" >&2
  exit 1
fi

echo
echo "Website bereit:"
echo "  $URL"
echo "Logdatei:"
echo "  $LOG_FILE"
echo

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi
