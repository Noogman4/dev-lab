---
id: "gh"
name: "gh"
command: "gh"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "github", "git"]
status: "Ausgearbeitet; Quellen geprüft; nur lokale Hilfeaufrufe praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 130
reviewed_at: "2026-11-13"
locally_checked_version: "gh 2.45.0 (Ubuntu-Paket 2.45.0-1ubuntu0.3)"
---

# gh – GitHub von der Kommandozeile aus bedienen

## 1. Kurzbeschreibung

`gh` ist die offizielle **GitHub CLI**. Sie bringt GitHub-Funktionen ins Terminal: Repositories klonen und anlegen, Issues und Pull Requests bearbeiten, Releases erstellen, GitHub-Actions-Läufe ansehen und beliebige Anfragen an die GitHub-API senden.

**Root-Rechte sind nicht nötig.** `gh` läuft als normales Programm. Welche Aktionen erlaubt sind, bestimmt das angemeldete GitHub-Konto beziehungsweise der verwendete Token.

`gh` ergänzt `git`, ersetzt es aber nicht: Commits, Branches und Zusammenführungen bleiben Aufgaben von `git`.

## 2. Was macht der Befehl?

Aufrufe folgen dem Muster:

```text
gh BEFEHL UNTERBEFEHL [OPTIONEN]
```

Die lokale Hilfe von gh 2.45.0 gliedert die Befehle in Gruppen:

| Gruppe | Beispiele |
| --- | --- |
| Kernbefehle | `auth`, `browse`, `issue`, `pr`, `repo`, `release`, `gist`, `org`, `project`, `codespace` |
| GitHub Actions | `run`, `workflow`, `cache` |
| Weitere | `api`, `search`, `secret`, `variable`, `ssh-key`, `gpg-key`, `label`, `config`, `extension`, `alias`, `status` |

Innerhalb eines Git-Arbeitsordners erkennt `gh` das zugehörige GitHub-Repository automatisch. Außerhalb oder abweichend lässt es sich mit `-R BESITZER/REPO` beziehungsweise `GH_REPO` angeben.

Jeder Aufruf außer reinen Hilfe- und Konfigurationsbefehlen spricht über das Netz mit GitHub. Lesende Befehle (`list`, `view`, `status`) verändern nichts. Schreibende Befehle (`create`, `edit`, `merge`, `close`, `delete`) wirken **sofort und öffentlich sichtbar** auf GitHub.

Die Beschreibung folgt der lokalen Hilfe, den Hilfethemen `gh help environment` und `gh help exit-codes` sowie der [Debian-Manpage zu gh](https://manpages.debian.org/trixie/gh/gh.1.en.html). Das vollständige Handbuch verortet die lokale Hilfe unter `https://cli.github.com/manual`; diese Seite wurde nicht gesondert gelesen.

### Anmeldung und Token

Laut `gh auth login --help` meldet sich `gh` standardmäßig über den Browser an und legt den Token im Schlüsselspeicher des Systems ab. Fehlt dieser, schreibt `gh` den Token **im Klartext** in eine Datei; `gh auth status` zeigt den Ort. Alternativ nutzt `gh` einen Token aus `GH_TOKEN` oder `GITHUB_TOKEN`; diese haben Vorrang vor gespeicherten Anmeldungen. Die Konfiguration liegt in `~/.config/gh` (oder `$GH_CONFIG_DIR`).

## 3. Syntax

```text
gh BEFEHL UNTERBEFEHL [OPTIONEN]
gh BEFEHL UNTERBEFEHL --help
gh api ENDPUNKT [OPTIONEN]
```

```bash
gh auth status
gh repo clone cli/cli
gh pr list --state open
gh issue view 42
```

Das bisherige NetMon-Beispiel `gh --help` funktioniert und zeigt die Befehlsübersicht. Der Platzhalter `gh [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Variable | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Hilfe zu jedem Befehl. | Auch `gh help THEMA`. |
| `-R BESITZER/REPO`, `--repo` | Anderes Repository ansprechen. | Bei vielen Unterbefehlen vorhanden. |
| `--json FELDER` | Ausgabe als JSON. | Mit `--jq` oder `--template` filtern; siehe `gh help formatting`. |
| `--web` | Im Browser öffnen statt im Terminal. | Bei vielen Unterbefehlen. |
| `GH_TOKEN`, `GITHUB_TOKEN` | Token aus der Umgebung. | Vorrang vor gespeicherter Anmeldung. |
| `GH_HOST` | Anderer GitHub-Host (Enterprise). | Dann auch `GH_ENTERPRISE_TOKEN`. |
| `GH_REPO` | Repository festlegen. | Für Skripte außerhalb eines Arbeitsordners. |
| `GH_PROMPT_DISABLED` | Interaktive Rückfragen abschalten. | Für Automatisierung. |
| `NO_COLOR` | Keine Farbcodes ausgeben. | Für Protokolle. |

### Rückgabewerte

Laut `gh help exit-codes`: `0` Erfolg, `1` Fehler, `2` abgebrochen, `4` Authentifizierungsproblem. Einzelne Befehle können weitere Werte haben.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Anmelden und offene Pull Requests eines Repositorys nur lesend ansehen. Das braucht ein GitHub-Konto und Netzwerkzugriff; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Version und Anmeldestatus

```bash
gh --version
gh auth status
```

`auth status` zeigt, bei welchem Host und mit welchem Konto `gh` angemeldet ist und wo der Token liegt.

### Schritt 2: Anmelden, falls nötig

```bash
gh auth login
```

`gh` fragt nach Host und Protokoll und öffnet den Browser. Danach ist der Token gespeichert.

### Schritt 3: Lesend arbeiten

```bash
cd ~/projekte/mein-repo
gh pr list --state open
gh pr view 17
```

Im Arbeitsordner eines GitHub-Repositorys zeigt `gh` dessen Pull Requests. Nichts wird verändert.

### Schritt 4: Ausgabe für Skripte

```bash
gh pr list --json number,title --jq '.[].title'
```

Gibt nur die Titel aus.

## 6. Typische Anwendungsfälle

- **Pull Requests:** anlegen (`gh pr create`), prüfen (`gh pr checkout`, `gh pr diff`), zusammenführen (`gh pr merge`).
- **Issues:** anlegen, kommentieren, schließen.
- **Releases:** `gh release create v1.2.0 dateien...`.
- **Actions überwachen:** `gh run list`, `gh run watch`.
- **API-Zugriff:** `gh api repos/BESITZER/REPO` für Daten ohne eigenen HTTP-Code.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ gilt nur für Hilfe und lesende Befehle. Der Kopf verwendet `caution`:

- **Öffentliche Wirkung:** Kommentare, Issues, Pull Requests und Releases sind sofort für andere sichtbar und lösen Benachrichtigungen aus. Erwähnungen mit `@name` benachrichtigen die genannte Person.
- **Löschen:** `gh repo delete`, `gh release delete` oder `gh api -X DELETE ...` entfernen Daten auf GitHub. Laut lokaler Hilfe löscht `gh repo delete` **ohne Argument das aktuelle Repository** des Arbeitsordners.
- **Token-Schutz:** Ein gespeicherter oder in `GH_TOKEN` gesetzter Token gewährt Zugriff auf alle freigegebenen Repositories. Nicht in Skripte schreiben, nicht in Protokolle ausgeben. Fehlt ein Schlüsselspeicher, liegt er im Klartext in `~/.config/gh/hosts.yml`.
- **Erweiterungen:** `gh extension install` lädt fremden Code, der mit deinem Token läuft.
- **`gh api`:** Erlaubt jede API-Aktion, auch zerstörerische; HTTP-Methode und Pfad genau prüfen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Hinweis auf fehlende Anmeldung, Rückgabewert `4` | Kein Token. | `gh auth login`. |
| `HTTP 404` | Repository unbekannt oder keine Rechte (auch bei privaten Repositories). | Schreibweise und Berechtigung prüfen. |
| `HTTP 403` beziehungsweise Rate-Limit | Rechte fehlen oder zu viele Anfragen. | Token-Bereiche prüfen, warten. |
| Kein Repository erkannt | Außerhalb eines Git-Arbeitsordners. | `-R BESITZER/REPO`. |
| Befehl unbekannt | Ältere `gh`-Version (hier 2.45.0). | `gh --version` mit dem Handbuch vergleichen. |

**Prüfpunkt:** Die Meldungstexte sind sinngemäß wiedergegeben; ausgelöst wurde keiner.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `gh auth status` und lesenden Befehlen beginnen.**
2. **Vor schreibenden Befehlen `-R` oder den Arbeitsordner prüfen.**
3. **`--web`** nutzen, um Formulare im Browser in Ruhe auszufüllen.
4. **Tokens mit minimalen Rechten** verwenden und regelmäßig erneuern.
5. **Erweiterungen nur aus vertrauenswürdigen Quellen.**

### Prüfstand

- **Geprüfte Version:** gh 2.45.0 (Ubuntu-Paket).
- **Tatsächlich ausgeführt** (nur lokal, ohne Netzwerkanfrage): `gh --help`, `gh --version`, `gh help exit-codes`, `gh help environment`, `gh auth login --help`, `gh pr list --help`, `gh repo delete --help`, `gh config list`, Rechte von `~/.config/gh` (Dateien `0600`).
- **Nicht ausgeführt:** jede Anfrage an GitHub (`auth status`, `pr list`, `api` …), Anmeldung, schreibende Befehle und Erweiterungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `git` | Versionsverwaltung; `gh` ergänzt die GitHub-spezifischen Teile. |
| `glab` | Entsprechendes Werkzeug für GitLab. |
| `ssh-keygen`, `ssh` | SSH-Schlüssel für Git-Zugriffe; `gh ssh-key add` lädt sie hoch. |
| `curl` | Allgemeine HTTP-Anfragen; `gh api` übernimmt Anmeldung und Paginierung. |
| `jq` | Verarbeitet JSON-Ausgaben. |

Ausgangseintrag: Datensatz 130 in `index.json` (`gh`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehlsgruppen, Anmeldung und Token-Ablage, Umgebungsvariablen, Rückgabewerte und einen lesenden Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
