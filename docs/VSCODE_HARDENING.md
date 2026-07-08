# VS Code Hardening

## Ziel

Diese Arbeitsumgebung soll auf dem Host moeglichst stabil laufen, ohne dass
Datei-Watcher, mehrere Python-Umgebungen oder offene Container-Integrationen
die Sitzung unnoetig empfindlich machen.

## Standard-Workflow

Verwende auf dem Host bevorzugt:

- `dev-lab-secure.code-workspace`
- lokale `.venv`

Beispiel:

```bash
code /dev-lab/projects/dev-lab/dev-lab-secure.code-workspace
```

Noch strikter und reproduzierbarer ist:

```bash
bash scripts/open_dev_lab_secure_vscode.sh
```

Dabei wird das sichere Workspace-Fenster mit dem Profil `dev-lab-secure`
geoeffnet und eine definierte Liste von Remote-/Cloud-Extensions fuer
dieses Fenster deaktiviert.

## Host-Profil

Fuer normalen Code-, Test- und Lint-Workflow reichen diese Extensions:

- `ms-python.python`
- `ms-python.vscode-pylance`
- `ms-python.black-formatter`
- `charliermarsh.ruff`

## Nicht Standard auf dem Host

Diese Erweiterungen sind fuer den normalen Host-Workflow bewusst nicht empfohlen:

- Docker-/Container-Extensions
- Codespaces-/RemoteHub-Integrationen
- weitere Remote-Explorer-Erweiterungen

Sie koennen weiter installiert bleiben, sollten aber fuer den stabilen
Host-Workflow nicht der Default sein.

Die konkrete Liste steht in:

- `.vscode/secure-disabled-extensions.txt`

## Wann der Devcontainer sinnvoll ist

Der Devcontainer ist optional und nur noch als gehaertete Python-
Entwicklungsumgebung vorgesehen:

- gehaerteter Standard: `.devcontainer/devcontainer.json`
- kein Docker-Socket-Mount
- kein zusaetzliches GUI-/Docker-Profil mehr im Setup

Nur verwenden, wenn reproduzierbare Isolation fuer den Python-Workflow
wirklich benoetigt wird. Fuer normalen NetMon-Alltag ist Host + `.venv`
der vorgesehene Standardweg.

## Stabilitaetsregeln

- nur eine aktive Host-venv: `.venv`
- keine Build-Artefakte im Workspace ansammeln
- grosse Asset-/Screenshot-/Preset-Baeume aus Watchern und Search heraushalten
- fuer normale Entwicklung Host + `.venv` bevorzugen
- fuer Spezialfaelle bewusst in den gehaerteten Devcontainer wechseln
- Docker ist kein vorausgesetzter Bestandteil des NetMon-Setups mehr
