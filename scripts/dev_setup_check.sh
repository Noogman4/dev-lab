#!/usr/bin/env bash
set -u

have() {
  command -v "$1" >/dev/null 2>&1
}

ok() {
  printf "OK   %s\n" "$1"
}

warn() {
  printf "WARN %s\n" "$1"
}

miss() {
  printf "MISS %s\n" "$1"
}

section() {
  printf "\n== %s ==\n" "$1"
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

check_file() {
  local path="$1"
  local label="${2:-$1}"
  if [ -e "$path" ]; then
    ok "$label"
    return 0
  fi
  miss "$label"
  return 1
}

check_userns() {
  local value
  value="$(sysctl -n kernel.unprivileged_userns_clone 2>/dev/null || true)"
  if [ "$value" = "1" ]; then
    ok "kernel.unprivileged_userns_clone=1"
  elif [ -n "$value" ]; then
    warn "kernel.unprivileged_userns_clone=$value"
  else
    warn "kernel.unprivileged_userns_clone nicht lesbar"
  fi
}


check_codex_patch_mode() {
  if ! have bwrap; then
    warn "Codex-Patchmodus: bwrap fehlt (apply_patch kann in Agent-Umgebungen scheitern)"
    return
  fi
  if bwrap --ro-bind / / --proc /proc --dev /dev true >/dev/null 2>&1; then
    ok "Codex-Patchmodus: bwrap namespace ok"
  else
    warn "Codex-Patchmodus: bwrap vorhanden, Namespace-Erstellung fehlgeschlagen"
  fi
}

check_python_tool() {
  local module="$1"
  local label="${2:-$1}"
  if "$PYTHON_CHECK_BIN" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec(\"${module}\") else 1)" >/dev/null 2>&1; then
    ok "$label (python module)"
    return 0
  fi
  warn "$label (python module fehlt evtl.)"
  return 1
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON_CHECK_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_CHECK_BIN="python3"
fi

missing_required=0
missing_recommended=0

section "System"
printf "Projekt: %s\n" "$PROJECT_ROOT"
printf "User: %s\n" "$(id -un 2>/dev/null || echo unknown)"
printf "Kernel: %s\n" "$(uname -srmo 2>/dev/null || uname -a)"
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  printf "OS: %s\n" "${PRETTY_NAME:-unknown}"
fi

section "Pflicht-CLI"
for cmd in git python3 pytest ruff black rg jq lsblk findmnt mount umount udisksctl; do
  if ! check_cmd "$cmd"; then
    missing_required=$((missing_required + 1))
  fi
done

section "Empfohlen"
for cmd in make curl shellcheck docker docker-compose cryptsetup; do
  if ! check_cmd "$cmd"; then
    missing_recommended=$((missing_recommended + 1))
  fi
done

section "Python-Projekt"
check_file "$PROJECT_ROOT/pyproject.toml" "pyproject.toml"
check_file "$PROJECT_ROOT/.venv" ".venv"
check_file "$PROJECT_ROOT/tests" "tests/"
printf "Python-Modulcheck via: %s\n" "$PYTHON_CHECK_BIN"
check_python_tool psutil psutil || true

section "Codex-Workflow"
check_codex_patch_mode

section "System-Integration"
check_userns
if sudo -n true >/dev/null 2>&1; then
  ok "sudo -n ohne Passwort"
else
  warn "sudo -n benoetigt Passwort oder ist nicht erlaubt"
fi
if groups 2>/dev/null | grep -qw docker; then
  ok "User ist in Gruppe docker"
else
  warn "User ist nicht in Gruppe docker"
fi

section "Mount und Storage"
if findmnt -rn -o TARGET / >/dev/null 2>&1; then
  root_target="$(findmnt -rn -o TARGET / | head -n1)"
  root_source="$(findmnt -rn -o SOURCE / | head -n1)"
  printf "Root: %s auf %s\n" "${root_source:-?}" "${root_target:-?}"
fi
if have docker; then
  docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
  if [ -n "$docker_root" ]; then
    printf "DockerRootDir: %s\n" "$docker_root"
  else
    warn "DockerRootDir nicht lesbar (docker evtl. nicht aktiv oder Rechte fehlen)"
  fi
fi

section "Projektbefehle"
if [ -f "$PROJECT_ROOT/Makefile" ]; then
  ok "Makefile"
  make_targets="$(make -qp 2>/dev/null | awk -F: '/^[A-Za-z0-9_.-]+:/ {print $1}')"
  for target in test lint format run check; do
    if printf '%s\n' "$make_targets" | grep -qx "$target"; then
      ok "make $target"
    else
      warn "make $target fehlt"
    fi
  done
else
  warn "Makefile fehlt"
fi

section "Empfehlungen"
printf -- "- Pflicht-Fehler: %s\n" "$missing_required"
printf -- "- Empfohlene Luecken: %s\n" "$missing_recommended"
printf -- "- Fuer Codex besonders wichtig: rg, pytest, ruff, black, jq, lsblk, findmnt, udisksctl\n"
printf -- "- Fuer weniger Reibung: kernel.unprivileged_userns_clone=1\n"
printf -- "- Python-Standard: .venv im Projekt und Tests lokal startbar\n"
printf -- "- Wenn apply_patch scheitert: docs/CODEX_PATCH_WORKFLOW.md nutzen und nach jeder Aenderung lint/tests laufen lassen\n"
printf -- "- Docker am besten auf schneller, stabil verbundener SSD\n"

section "Install-Vorschlag Debian oder Zorin"
printf '%s\n' 'sudo apt update'
printf '%s\n' 'sudo apt install -y git python3 python3-venv python3-pip python3-pytest ruff black ripgrep jq util-linux udisks2 make curl cryptsetup shellcheck docker.io docker-compose'

if [ "$missing_required" -eq 0 ]; then
  section "Ergebnis"
  printf '%s\n' 'Pflicht-Checks sind ok. Wir koennen darauf gut aufbauen.'
  exit 0
fi

section "Ergebnis"
printf "Pflicht-Checks fehlen: %s\n" "$missing_required"
exit 1
