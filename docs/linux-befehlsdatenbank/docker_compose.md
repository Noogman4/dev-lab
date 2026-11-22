---
id: "docker_compose"
name: "docker-compose"
command: "docker-compose"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "docker", "compose", "devops"]
status: "Ausgearbeitet; Quellen geprüft; nur lokaler Wrapper geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 140
reviewed_at: "2026-11-13"
locally_checked_version: "Nur Wrapper-Skript /usr/local/bin/docker-compose (ruft docker compose auf); Docker nicht installiert"
---

# docker-compose – Mehrere Container gemeinsam aus einer YAML-Datei steuern

## 1. Kurzbeschreibung

Docker Compose beschreibt eine Anwendung aus mehreren Containern (etwa Webserver, Datenbank, Cache) in einer Datei `compose.yaml` beziehungsweise `docker-compose.yml` und startet, stoppt und entfernt sie gemeinsam.

**Wichtig zur Schreibweise:** `docker-compose` mit Bindestrich ist der Aufruf der alten, in Python geschriebenen **Compose v1** aus dem Jahr 2014. Die heute unterstützten Fassungen (Compose v2 in Go und deren Nachfolger) werden laut [Docker-Dokumentation zur Compose-Geschichte](https://docs.docker.com/compose/intro/history/) als **`docker compose`** (mit Leerzeichen, als Docker-Plugin) aufgerufen. Viele Systeme stellen `docker-compose` nur noch als Weiterleitung bereit.

**Root-Rechte oder gleichwertige Rechte sind nötig,** weil Compose den Docker-Dienst steuert. Die Gruppe `docker` gewährt laut Docker-Dokumentation Rechte auf Root-Niveau (siehe `docker`).

Auf dem geprüften System ist `/usr/local/bin/docker-compose` ein zweizeiliges Shell-Skript, das `docker compose "$@"` aufruft. Docker selbst fehlt; jeder Aufruf scheitert deshalb mit `exec: docker: not found`.

## 2. Was macht der Befehl?

Compose liest die Projektdatei im aktuellen Ordner und vergleicht den gewünschten mit dem tatsächlichen Zustand. `up` legt fehlende Netzwerke, Volumes und Container an und startet sie; `down` stoppt und entfernt sie wieder. Der Projektname leitet sich standardmäßig vom Ordnernamen ab.

Laut Compose-Geschichte unterscheiden sich die Generationen:

| Fassung | Aufruf | Besonderheit |
| --- | --- | --- |
| Compose v1 (2014, Python) | `docker-compose` | Nutzt das Feld `version` in der Datei (Formate 2.0 bis 3.8). |
| Compose v2 (2020, Go) | `docker compose` | Ignoriert das Feld `version`, folgt der Compose-Spezifikation. |
| Compose v5 | `docker compose` | Laut Dokumentation zusätzlich ein Go-SDK; Versionssprung zur Abgrenzung von den alten Dateiformaten. |

Laut derselben Seite sind heute nur Compose v2 und v5 unterstützt.

## 3. Syntax

```text
docker compose [-f DATEI] [-p PROJEKT] BEFEHL [OPTIONEN]
docker-compose [-f DATEI] [-p PROJEKT] BEFEHL [OPTIONEN]
```

```bash
docker compose up -d
docker compose ps
docker compose logs -f web
docker compose down
```

Das bisherige NetMon-Beispiel `docker-compose --help` hätte auf dem geprüften System nur `exec: docker: not found` ausgegeben. Der Platzhalter `docker-compose [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert. **Prüfpunkt:** Ob ein vorhandenes `docker-compose` die alte v1 oder eine Weiterleitung auf v2 ist, mit `docker-compose version` prüfen.

## 4. Wichtige Optionen

| Befehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `up -d` | Dienste anlegen und im Hintergrund starten. | Ohne `-d` im Vordergrund mit Protokollen. |
| `down` | Container und Netzwerke stoppen und entfernen. | Volumes bleiben ohne `-v` erhalten. |
| `down -v`, `--volumes` | Zusätzlich benannte und anonyme Volumes löschen. | **Datenverlust** bei Datenbanken. |
| `down --rmi local/all` | Zusätzlich Images löschen. | Laut Referenz zu `compose down`. |
| `down --remove-orphans` | Container entfernen, die nicht mehr in der Datei stehen. | – |
| `ps` | Container des Projekts anzeigen. | Nur lesend. |
| `logs -f DIENST` | Protokolle verfolgen. | Nur lesend. |
| `config` | Zusammengeführte Konfiguration anzeigen. | Gut zum Prüfen von Variablen. **Prüfpunkt:** nicht in gelesenen Quellen nachgeschlagen. |
| `-f DATEI` | Andere Projektdatei. | Mehrfach angebbar. |
| `-p NAME` | Projektname festlegen. | Trennt Projekte mit gleichen Ordnernamen. |

Die Angaben zu `down` stammen aus der [Referenz zu `docker compose down`](https://docs.docker.com/reference/cli/docker/compose/down/).

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein kleines Projekt mit einem Webserver starten, prüfen und vollständig wieder entfernen. Voraussetzung ist ein funktionierendes Docker mit Compose-Plugin. Das ist ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Projektordner und Datei

```bash
uebung="$(mktemp -d -t netmon-compose-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'services:\n  web:\n    image: nginx:stable\n    ports:\n      - "127.0.0.1:8080:80"\n' > compose.yaml
```

Der Port wird nur an `127.0.0.1` gebunden, ist also nicht aus dem Netz erreichbar.

### Schritt 2: Starten

```bash
docker compose up -d
```

Compose lädt das Image, legt ein Projektnetzwerk an und startet den Container.

### Schritt 3: Prüfen

```bash
docker compose ps
curl -s http://127.0.0.1:8080 | head -n 3
```

### Schritt 4: Entfernen

```bash
docker compose down
```

Container und Netzwerk werden entfernt; das Image bleibt im lokalen Speicher.

## 6. Typische Anwendungsfälle

- **Entwicklungsumgebungen** mit mehreren Diensten.
- **Kleine Produktivinstallationen** auf einem Server.
- **Tests in CI-Pipelines** mit Datenbank und Anwendung.
- **Umzug alter Projekte** von `docker-compose` (v1) auf `docker compose`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **`down -v` löscht Volumes** und damit zum Beispiel Datenbankinhalte.
- **Root-Niveau:** Wer Compose bedienen darf, steuert den Docker-Dienst; Projektdateien mit Host-Mounts oder `privileged: true` können das System verändern.
- **Fremde Projektdateien** vor `up` lesen: Images, Mounts, Ports und Umgebungsvariablen prüfen.
- **Ports:** `"8080:80"` ohne Adresse veröffentlicht den Dienst je nach Konfiguration an allen Schnittstellen.
- **Geheimnisse in `.env`-Dateien** nicht in Repositories einchecken.
- **v1 und v2 mischen:** Unterschiedliche Container-Namensschemata können dazu führen, dass Compose vorhandene Container nicht erkennt. **Prüfpunkt:** nicht praktisch geprüft.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `exec: docker: not found` | Weiterleitungsskript ohne Docker (so auf dem Prüfsystem). | Docker installieren oder Skript entfernen lassen. |
| `docker: 'compose' is not a docker command` | Compose-Plugin fehlt. | Plugin installieren. |
| `permission denied ... docker.sock` | Keine Rechte am Docker-Dienst. | Siehe `docker`. |
| Warnung zum Feld `version` | Alte Datei unter v2. | Feld entfernen; es wird ignoriert. |
| Port belegt | Anderer Dienst nutzt den Host-Port. | Port in der Datei ändern. |

**Prüfpunkt:** Außer `exec: docker: not found` wurden keine Meldungen praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`docker compose` (mit Leerzeichen)** verwenden.
2. **Ports an `127.0.0.1` binden,** wenn sie nur lokal gebraucht werden.
3. **`down` ohne `-v`,** solange Daten erhalten bleiben sollen.
4. **Projektdateien vor `up` lesen.**
5. **Feste Image-Versionen** angeben.

### Prüfstand

- **Lokal geprüft:** Inhalt von `/usr/local/bin/docker-compose` (Weiterleitung auf `docker compose`), Aufruf von `docker-compose version` und `--help` (beide scheitern mit `exec: docker: not found`, weil Docker fehlt).
- **Quellen gelesen** (Abruf 2026-11-13): Docker-Dokumentation zur Compose-Geschichte (v1/v2/v5) und Referenz zu `docker compose down`.
- **Nicht geprüft:** jede tatsächliche Compose-Ausführung, `config`, Fehlermeldungen außer der genannten, Mischbetrieb v1/v2.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `docker` | Grundbefehl; Compose steuert denselben Dienst. |
| `podman-compose` | Compose-Dateien mit Podman ausführen. |
| `kubectl` | Für Orchestrierung über mehrere Rechner. |
| `nerdctl compose` | Compose für containerd. |

Ausgangseintrag: Datensatz 140 in `index.json` (`docker-compose`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Unterscheidung v1/v2, die lokale Wrapper-Situation, Befehle mit Datenverlustrisiko und einen Ablauf ersetzt. Die Root-Angabe wurde korrigiert, weil Compose den Docker-Dienst steuert.
