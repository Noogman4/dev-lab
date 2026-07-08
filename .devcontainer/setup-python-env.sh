#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_VENV="/home/vscode/.venvs/dev-lab"
APT_PACKAGES=(python3-tk)

# Some upstream devcontainer images include optional third-party APT repos
# that can break reproducible setup when their signing key or metadata drifts.
if [[ -f /etc/apt/sources.list.d/yarn.list ]] && grep -q 'dl.yarnpkg.com' /etc/apt/sources.list.d/yarn.list; then
  sudo mv /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.list.disabled
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"

mkdir -p "$(dirname "$CONTAINER_VENV")"
python3 -m venv "$CONTAINER_VENV"
"$CONTAINER_VENV/bin/pip" install --upgrade pip
"$CONTAINER_VENV/bin/pip" install -r "$ROOT_DIR/requirements.txt"
"$CONTAINER_VENV/bin/pip" install black ruff pytest Pillow requests openpyxl
