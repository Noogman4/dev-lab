# Devcontainer Profiles

## Standard

`devcontainer.json` ist der gehaertete Default.

Eigenschaften:

- kein Docker-Socket-Mount
- kein X11-/`DISPLAY`-Passthrough
- kein Host-`.Xauthority`-Bind
- Container-Python liegt getrennt unter `/home/vscode/.venvs/dev-lab`

Ziel:

- stabile VS-Code-/Codex-Sitzungen
- keine versehentliche Beschaedigung der Host-`.venv`
- minimalere Host-Angriffsoberflaeche

## Python-Umgebungen

- Host-Entwicklung im Repository: `.venv`
- Container-Entwicklung: `/home/vscode/.venvs/dev-lab`

Diese Trennung ist absichtlich, damit Host und Container sich nicht mehr gegenseitig die Interpreterpfade kaputtschreiben.
