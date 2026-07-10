#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/lab/init_test_run.sh --distro DISTRO --scenario SCENARIO [options]

Options:
  --distro NAME       Target distro name, e.g. zorin, ubuntu, fedora
  --scenario NAME     Short scenario name, e.g. smoke, gui, packaging
  --root PATH         Lab root. Default: /media/happy/Work2/netmon-lab
  --run-id ID         Explicit run id. Default: <date>-<distro>-<scenario>
  --note TEXT         One-line note written into notes.md
  --print-only        Print resolved paths without creating files
  -h, --help          Show this help
EOF
}

require_arg() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ]; then
    printf 'Missing required argument: %s\n' "$name" >&2
    usage >&2
    exit 1
  fi
}

sanitize_slug() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr ' /' '--' | tr -cd 'a-z0-9._-'
}

LAB_ROOT="/media/happy/Work2/netmon-lab"
DISTRO=""
SCENARIO=""
RUN_ID=""
NOTE=""
PRINT_ONLY=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --distro)
      DISTRO="${2:-}"
      shift 2
      ;;
    --scenario)
      SCENARIO="${2:-}"
      shift 2
      ;;
    --root)
      LAB_ROOT="${2:-}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:-}"
      shift 2
      ;;
    --note)
      NOTE="${2:-}"
      shift 2
      ;;
    --print-only)
      PRINT_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_arg "--distro" "$DISTRO"
require_arg "--scenario" "$SCENARIO"

DISTRO_SLUG="$(sanitize_slug "$DISTRO")"
SCENARIO_SLUG="$(sanitize_slug "$SCENARIO")"

if [ -z "$RUN_ID" ]; then
  RUN_ID="$(date +%F)-${DISTRO_SLUG}-${SCENARIO_SLUG}"
fi

RUN_DIR="$LAB_ROOT/runs/$RUN_ID"
DISTRO_DIR="$LAB_ROOT/distros/$DISTRO_SLUG"
ENV_DIR="$RUN_DIR/env"
LOGS_DIR="$RUN_DIR/logs"
SCREENSHOTS_DIR="$RUN_DIR/screenshots"
EXPORTS_DIR="$RUN_DIR/exports"
CAPTURES_DIR="$RUN_DIR/captures"
ARTIFACTS_DIR="$RUN_DIR/artifacts"
NOTES_FILE="$RUN_DIR/notes.md"
MANIFEST_FILE="$RUN_DIR/run.env"

printf 'Lab root:    %s\n' "$LAB_ROOT"
printf 'Distro dir:  %s\n' "$DISTRO_DIR"
printf 'Run dir:     %s\n' "$RUN_DIR"

if [ "$PRINT_ONLY" -eq 1 ]; then
  exit 0
fi

mkdir -p \
  "$LAB_ROOT/isos" \
  "$LAB_ROOT/vms" \
  "$LAB_ROOT/images" \
  "$LAB_ROOT/distros" \
  "$LAB_ROOT/runs" \
  "$LAB_ROOT/artifacts" \
  "$LAB_ROOT/screenshots" \
  "$LAB_ROOT/shared/netmon-testdata" \
  "$LAB_ROOT/notes" \
  "$DISTRO_DIR/notes" \
  "$ENV_DIR" \
  "$LOGS_DIR" \
  "$SCREENSHOTS_DIR" \
  "$EXPORTS_DIR" \
  "$CAPTURES_DIR" \
  "$ARTIFACTS_DIR"

cat > "$MANIFEST_FILE" <<EOF
RUN_ID=$RUN_ID
DISTRO=$DISTRO
DISTRO_SLUG=$DISTRO_SLUG
SCENARIO=$SCENARIO
SCENARIO_SLUG=$SCENARIO_SLUG
LAB_ROOT=$LAB_ROOT
RUN_DIR=$RUN_DIR
CREATED_AT=$(date -Is)
HOSTNAME=$(hostname 2>/dev/null || echo unknown)
KERNEL=$(uname -srmo 2>/dev/null || uname -a)
EOF

cat > "$NOTES_FILE" <<EOF
# NetMon Test Run

- Run ID: \`$RUN_ID\`
- Distro: \`$DISTRO\`
- Scenario: \`$SCENARIO\`
- Created: \`$(date -Is)\`
- Host: \`$(hostname 2>/dev/null || echo unknown)\`

## Goal

Describe what this run is supposed to validate.

## Environment

- Install type:
- Desktop:
- Python:
- Optional tools:

## Checks

- [ ] Repo state recorded
- [ ] Headless start checked
- [ ] GUI start checked
- [ ] Diagnostics exported
- [ ] Screenshots collected

## Notes

${NOTE:-Add findings, failures, and follow-up tasks here.}
EOF

printf 'Created run: %s\n' "$RUN_DIR"
printf 'Manifest:    %s\n' "$MANIFEST_FILE"
printf 'Notes:       %s\n' "$NOTES_FILE"
