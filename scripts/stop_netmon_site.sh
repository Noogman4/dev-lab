#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/netmon_site_http_server.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Kein NetMon Website-Server registriert."
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"

if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "NetMon Website-Server gestoppt."
else
  echo "Kein laufender NetMon Website-Server gefunden."
fi

rm -f "$PID_FILE"
