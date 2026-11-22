---
id: "glab"
name: "glab"
command: "glab"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "gitlab", "git"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 131
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# glab – GitLab von der Kommandozeile aus bedienen

## 1. Kurzbeschreibung

`glab` ist die offizielle **GitLab CLI**. Sie bringt GitLab-Funktionen ins Terminal: Merge Requests und Issues bearbeiten, CI/CD-Pipelines ansehen und neu starten, Releases anlegen, Variablen verwalten und beliebige Anfragen an die GitLab-API senden. Sie funktioniert mit GitLab.com und selbst betriebenen GitLab-Instanzen.

**Root-Rechte sind nicht nötig.** `glab` läuft als normales Programm. Was erlaubt ist, bestimmen das GitLab-Konto beziehungsweise der Token und dessen Rechte.

Grundlage sind die [GitLab-Dokumentation zur GitLab CLI](https://docs.gitlab.com/cli/), die Seite zu [`glab auth login`](https://docs.gitlab.com/cli/auth/login/) und die [Debian-Manpage zu glab](https://manpages.debian.org/trixie/glab/glab.1.en.html). Auf dem geprüften System ist `glab` nicht installiert.

## 2. Was macht der Befehl?

Aufrufe folgen dem Muster:

```text
glab BEFEHL [UNTERBEFEHL] [OPTIONEN]
```

Wichtige Befehlsgruppen laut Manpage und Dokumentation:

| Befehl | Aufgabe |
| --- | --- |
| `glab auth` | Anmelden, abmelden, Status. |
| `glab mr` | Merge Requests. |
| `glab issue` | Issues. |
| `glab ci`, `glab job`, `glab schedule` | Pipelines, Jobs, Zeitpläne. |
| `glab release` | Releases. |
| `glab repo` | Repositories klonen, anlegen, anzeigen. |
| `glab variable` | CI/CD-Variablen. |
| `glab api` | Direkte API-Anfragen. |
| `glab config` | Einstellungen. |

Laut Dokumentation erkennt `glab` in einem Git-Arbeitsordner die GitLab-Instanz anhand der Remotes automatisch und kann mehrere angemeldete Instanzen verwalten. Listen sind seitenweise; mit `--page` und `--per-page` lässt sich blättern.

Lesende Befehle (`list`, `view`, `status`) verändern nichts. Schreibende Befehle (`create`, `merge`, `close`, `delete`, `retry`) wirken sofort auf GitLab.

### Anmeldung und Speicherung

Laut aktueller Dokumentation zu `glab auth login` speichert `glab` Zugangsdaten im Schlüsselbund des Betriebssystems (unter Linux über den Secret Service), wenn einer verfügbar ist. Sonst oder mit `--insecure-storage` landen sie **im Klartext** in `~/.config/glab-cli/config.yml`. Die Umgebungsvariablen `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN` oder `OAUTH_TOKEN` haben Vorrang vor gespeicherten Daten. **Prüfpunkt:** Die Schlüsselbund-Speicherung ist in der aktuellen Dokumentation beschrieben; ältere Paketversionen (Debian trixie liefert eine Fassung von Juni 2025) können anders speichern.

## 3. Syntax

```text
glab BEFEHL UNTERBEFEHL [OPTIONEN]
glab BEFEHL --help
```

```bash
glab auth login
glab mr list
glab ci status
glab issue view 12
```

Das bisherige NetMon-Beispiel `glab --help` ist gültig; die Manpage nennt `--help` und `-v`/`--version`. Der Platzhalter `glab [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Variable | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Hilfe zu jedem Befehl. | – |
| `-v`, `--version` | Version anzeigen. | – |
| `-R BESITZER/REPO` | Anderes Projekt ansprechen. | Bei vielen Unterbefehlen. **Prüfpunkt:** je Befehl prüfen. |
| `--page`, `--per-page` | Seitenweise Listen. | Laut Dokumentation. |
| `glab auth login --hostname HOST` | Bei bestimmter Instanz anmelden. | Für selbst betriebene GitLab-Server. |
| `glab auth login --stdin` | Token von der Standardeingabe lesen. | Besser als `--token` in der Befehlszeile. |
| `glab auth login --device` | Gerätecode-Anmeldung ohne lokalen Browser. | Laut Dokumentation ab GitLab 17.9. |
| `GITLAB_TOKEN` | Token aus der Umgebung. | Vorrang vor gespeicherten Daten. |
| `GITLAB_HOST` | Standard-Instanz. | Für Aufrufe außerhalb eines Arbeitsordners. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Bei einer GitLab-Instanz anmelden und offene Merge Requests nur lesend ansehen. Das braucht ein Konto und Netzwerkzugriff; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Version prüfen

```bash
glab --version
```

### Schritt 2: Anmelden

```bash
glab auth login --hostname gitlab.example.org
```

Der interaktive Dialog fragt nach Anmeldeart und Protokoll. Für Tokens aus einer Datei: `glab auth login --hostname gitlab.example.org --stdin < token.txt`.

### Schritt 3: Status prüfen

```bash
glab auth status
```

Zeigt, bei welchen Instanzen `glab` angemeldet ist.

### Schritt 4: Lesend arbeiten

```bash
cd ~/projekte/mein-gitlab-repo
glab mr list
glab ci status
```

Zeigt offene Merge Requests und den Pipeline-Zustand des aktuellen Branches.

## 6. Typische Anwendungsfälle

- **Merge Requests** anlegen, prüfen und zusammenführen.
- **CI/CD beobachten:** Pipelines ansehen, fehlgeschlagene Jobs erneut starten.
- **Releases** mit Dateien anlegen.
- **Automatisierung in Pipelines** mit Job-Token.
- **API-Zugriff** ohne eigenen HTTP-Code.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ gilt nur für lesende Befehle. Der Kopf verwendet `caution`:

- **Sofort wirksame Änderungen:** Zusammenführen, Schließen, Löschen und Pipeline-Starts wirken direkt auf das Projekt und können Bereitstellungen auslösen.
- **CI/CD-Variablen:** `glab variable` kann Geheimnisse anzeigen oder überschreiben.
- **Token im Klartext:** Ohne Schlüsselbund oder mit `--insecure-storage` liegt der Token in `~/.config/glab-cli/config.yml`. Dateien nicht teilen.
- **Token in der Befehlszeile:** `--token glpat-...` erscheint in Shell-Verlauf und Prozessliste. `--stdin` verwenden.
- **Falsche Instanz:** Mehrere angemeldete Instanzen; vor schreibenden Befehlen `glab auth status` und Arbeitsordner prüfen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `glab: command not found` | Nicht installiert. | Paket der Distribution oder offizielle Installation. |
| Nicht angemeldet | Kein Token für den Host. | `glab auth login --hostname HOST`. |
| `401` / `403` | Token ungültig oder Rechte fehlen. | Token-Bereiche prüfen, neu anmelden. |
| `404 Project Not Found` | Projekt unbekannt oder privat ohne Rechte. | Pfad und Berechtigung prüfen. |
| Falsche Instanz angesprochen | Kein GitLab-Remote im Ordner. | `GITLAB_HOST` oder `--hostname`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `glab auth status` und `list`/`view` beginnen.**
2. **Tokens über `--stdin`** übergeben.
3. **Tokens mit minimalen Rechten und Ablaufdatum** erstellen.
4. **Vor `merge` oder `delete` Projekt und Branch prüfen.**
5. **Schlüsselbund nutzen** und `--insecure-storage` vermeiden.

### Prüfstand

- **Geprüfte Version:** keine; `glab` ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): GitLab-Dokumentation zur CLI (Funktionsumfang, Anmeldung, Paginierung), Seite zu `glab auth login` (Speicherung, Variablen, Optionen) und Debian-Manpage `glab(1)` (Befehlsliste, Fassung Juni 2025).
- **Nicht geprüft:** alle Aufrufe, `-R` je Unterbefehl, Speicherverhalten der installierbaren Paketversion.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `git` | Versionsverwaltung; `glab` ergänzt die GitLab-spezifischen Teile. |
| `gh` | Entsprechendes Werkzeug für GitHub. |
| `ssh-keygen` | SSH-Schlüssel für Git-Zugriffe. |
| `curl` | Allgemeine HTTP-Anfragen an die GitLab-API. |

Ausgangseintrag: Datensatz 131 in `index.json` (`glab`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehlsgruppen, Anmeldung und Token-Speicherung, Optionen und einen lesenden Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
