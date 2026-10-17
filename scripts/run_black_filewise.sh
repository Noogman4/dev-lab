#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
BLACK_CACHE_DIR="${BLACK_CACHE_DIR:-/tmp/user/1000/black-cache}"
export BLACK_CACHE_DIR

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python not found or not executable: $PYTHON_BIN" >&2
  exit 127
fi

mode_args=()
paths=()
while (($#)); do
  case "$1" in
    --check|--diff|--fast|--safe|--quiet|-q|--verbose|-v)
      mode_args+=("$1")
      ;;
    --)
      shift
      while (($#)); do
        paths+=("$1")
        shift
      done
      break
      ;;
    -*)
      mode_args+=("$1")
      ;;
    *)
      paths+=("$1")
      ;;
  esac
  shift
done

if ((${#paths[@]} == 0)); then
  while IFS= read -r path; do
    paths+=("$path")
  done < <(cd "$ROOT_DIR" && git ls-files '*.py')
fi

status=0
for path in "${paths[@]}"; do
  if [[ "$path" != /* ]]; then
    path="$ROOT_DIR/$path"
  fi
  "$PYTHON_BIN" -m black "${mode_args[@]}" "$path" || status=$?
done

exit "$status"
