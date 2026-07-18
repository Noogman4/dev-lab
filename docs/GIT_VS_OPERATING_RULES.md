# Git and VS Operating Rules

## Ziel

Diese Regeln halten die lokale Host-Arbeitsumgebung fuer `dev-lab` stabil,
vorhersagbar und moeglichst leichtgewichtig.

## Standard

- lokal auf dem Host mit `.venv` arbeiten
- VS Code bevorzugt ueber den sicheren Startpfad verwenden
- Build-Artefakte nicht im aktiven Workspace ansammeln

## VS Code

Bevorzugter Start:

```bash
bash scripts/open_dev_lab_secure_vscode.sh
```

Alternative:

```bash
code /dev-lab/projects/dev-lab/dev-lab-secure.code-workspace
```

## Python

- genau eine aktive Host-Umgebung: `.venv`
- keine zusaetzlichen `venv`-Verzeichnisse im Projektwurzelverzeichnis anlegen
- Container-Python und Host-Python getrennt halten

## Git

Normal und erwuenscht:

- `git status`
- `git diff`
- `git log`
- `git add`
- `git commit`
- `git fetch`
- `git pull`
- `git push`

Wichtig:

- `git status --short` regelmaessig klein halten
- neue Artefakte sofort ignorieren oder auslagern
- Aenderungen in kleine Themenbloecke schneiden

## Build und Artefakte

- Build-Staging moeglichst nach `/tmp` oder in klar ignorierte Pfade
- `dist/` nicht unkontrolliert wachsen lassen
- Backups nur als Archive behalten, nicht als entpackte Baeume

## Vermeiden

- mehrere parallele Python-Umgebungen im Repo
- grosse Build-Baeume im Workspace
- entpackte Alt-Backups im Projektwurzelverzeichnis
- hunderte untracked Dateien ueber laengere Zeit
- Docker-/Remote-/Codespaces-Extensions im normalen Host-Workflow aktiv nutzen

## Warnsignale

Wenn eines davon wieder auftritt, wird die Umgebung meist wieder empfindlicher:

- `git status` zeigt sehr viele Artefakte
- neue `venv`-Ordner tauchen im Repo auf
- `dist/` waechst stark an
- VS Code reagiert spuerbar traeger bei Suche, Git oder Python-Analyse

## Faustregel

Kleiner Arbeitsbaum, eine `.venv`, sicherer VS-Startpfad, Container nur bewusst.
