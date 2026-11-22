---
id: "docker"
name: "docker"
command: "docker"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "docker", "devops", "images"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 139
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# docker – Container, Images und Netzwerke mit Docker verwalten

## 1. Kurzbeschreibung

`docker` ist der Kommandozeilen-Client der Docker-Plattform. Er steuert den **Docker-Dienst** (`dockerd`): Images laden und bauen, Container starten, stoppen und löschen, Netzwerke und Volumes verwalten. Das Beispiel aus dem Ausgangseintrag, `docker ps -a`, listet alle Container einschließlich gestoppter.

**Root-Rechte oder gleichwertige Rechte sind nötig.** Der Client spricht über den Socket `/var/run/docker.sock` mit dem Dienst, der laut [Docker-Sicherheitsdokumentation](https://docs.docker.com/engine/security/) Root-Rechte hat, sofern nicht der Rootless-Modus gewählt wurde. Statt `sudo` werden Benutzer oft in die Gruppe `docker` aufgenommen. Die [Docker-Anleitung nach der Installation](https://docs.docker.com/engine/install/linux-postinstall/) warnt ausdrücklich: **Die Gruppe `docker` gewährt Rechte auf Root-Niveau.** Die Root-Angabe im Kopf bezieht sich deshalb auf „Root oder Mitgliedschaft in `docker`“.

Auf dem geprüften System ist Docker nicht installiert.

## 2. Was macht der Befehl?

Laut [Debian-Manpage zu docker](https://manpages.debian.org/trixie/docker.io/docker.1.en.html) ist `docker` ein Client, der über die Kommandozeile mit dem Dienst `dockerd` kommuniziert. Er hat über 30 Befehle, jeweils mit eigener Hilfe.

Wichtige Befehle:

| Befehl | Wirkung |
| --- | --- |
| `docker ps` / `docker container ls` | Laufende Container auflisten; mit `-a` auch gestoppte. |
| `docker images` | Lokale Images auflisten. |
| `docker pull IMAGE` | Image aus einer Registry laden. |
| `docker run IMAGE` | Container aus Image erzeugen und starten. |
| `docker logs CONTAINER` | Ausgaben eines Containers. |
| `docker exec -it CONTAINER sh` | Befehl im laufenden Container. |
| `docker stop` / `docker rm` | Stoppen / löschen. |
| `docker rmi IMAGE` | Image löschen. |
| `docker build -t NAME .` | Image aus Dockerfile bauen. |
| `docker volume`, `docker network` | Volumes und Netzwerke verwalten. |
| `docker system prune` | Ungenutzte Objekte entfernen. |

Befehle wie `ps`, `images`, `logs` und `inspect` lesen Informationen; auch Hilfe und Versionsabfragen sind keine Containeränderungen. Dagegen verändern etwa `run`, `stop`, `rm` und `prune` den Zustand des Dienstes und teils das Hostsystem. Die Wirkung hängt vom Unterbefehl ab.

## 3. Syntax

```text
docker [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] [ARGUMENTE]
docker BEFEHL --help
```

```bash
docker ps -a
docker images
docker run --rm -it debian:stable bash
docker logs --tail 50 meincontainer
```

Der Ausgangseintrag nennt `docker BEFEHL [OPTIONEN]` und das Beispiel `docker ps -a` („Listet Container inklusive gestoppter Container.“). Beides ist zutreffend und wurde übernommen.

## 4. Wichtige Optionen

### Globale Optionen laut Manpage

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-H`, `--host` | Ziel-Dienst, Standard `unix:///var/run/docker.sock`. | Entfernten Zugriff über SSH oder passend authentifiziertes TLS schützen. |
| `--config` | Ort der Client-Konfiguration, Standard `~/.docker`. | Dort liegen auch Registry-Anmeldungen. |
| `--tls`, `--tlsverify` | TLS-Transport beziehungsweise explizite Zertifikatsprüfung bei TCP-Verbindungen. | Client und Dienst passend konfigurieren: Verschlüsselung allein ersetzt keine Zugriffskontrolle. |
| `-D`, `--debug` | Diagnosemodus. | – |
| `-v`, `--version` | Version. | – |

### Optionen von `docker ps` laut [Befehlsreferenz](https://docs.docker.com/reference/cli/docker/container/ls/)

| Option | Bedeutung |
| --- | --- |
| `-a`, `--all` | Alle Container, nicht nur laufende. |
| `-q`, `--quiet` | Nur Container-IDs. |
| `-s`, `--size` | Gesamtgröße der Dateien. |
| `-f`, `--filter` | Nach Bedingungen filtern, etwa `status=exited`. |
| `--format` | Ausgabe mit Vorlage formatieren. |
| `-n N`, `-l` | Die letzten N bzw. den zuletzt erstellten Container. |
| `--no-trunc` | Ausgabe nicht kürzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Zustand aller Container prüfen und einen beendeten Container untersuchen, ohne etwas zu verändern. Das ist ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Alle Container auflisten

```bash
docker ps -a
```

Spalten: `CONTAINER ID`, `IMAGE`, `COMMAND`, `CREATED`, `STATUS`, `PORTS`, `NAMES`. `STATUS` zeigt zum Beispiel `Up 2 hours` oder `Exited (1) 5 minutes ago`; die Zahl ist der Rückgabewert des Hauptprozesses.

### Schritt 2: Nur beendete Container

```bash
docker ps -a --filter status=exited
```

### Schritt 3: Ursache im Protokoll suchen

```bash
docker logs --tail 50 CONTAINERNAME
```

### Schritt 4: Details ansehen

```bash
docker inspect CONTAINERNAME
```

Gibt JSON mit Konfiguration, Mounts, Netzwerk und Zustand aus.

## 6. Typische Anwendungsfälle

- **Entwicklungsumgebungen** mit Datenbanken oder Diensten in Containern.
- **Dienste betreiben** mit festen Image-Versionen.
- **Images bauen und verteilen.**
- **Wegwerf-Umgebungen:** `docker run --rm -it IMAGE sh` – der Container wird nach dem Beenden gelöscht.
- **Aufräumen:** `docker system prune` (siehe Risiken).

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution` für den dokumentierten lesenden Normalfall. Eingriffe können deutlich gefährlicher sein:

- **Docker-Zugriff = Root-Zugriff:** Laut Docker-Sicherheitsdokumentation kann ein Container den Ordner `/` des Hosts einhängen und ohne Einschränkung verändern. Wer `docker` bedienen darf, kann das System übernehmen.
- **Gefährliche Optionen:** `--privileged`, `-v /:/host`, `--pid=host`, `--net=host` oder der Docker-Socket im Container heben die Isolation praktisch auf.
- **Datenverlust:** `docker rm` löscht Container samt nicht in Volumes gespeicherter Daten. `docker system prune` entfernt laut Referenz ungenutzte Container, Netzwerke, Images und Build-Cache, optional auch Volumes.
- **Offene Ports:** `-p 8080:80` veröffentlicht Dienste, je nach Konfiguration an allen Netzwerkschnittstellen. Docker verwaltet dazu eigene Firewall-Regeln. **Prüfpunkt:** Zusammenspiel mit `ufw` nicht geprüft.
- **Ungeschützter TCP-Socket:** Ein erreichbarer Docker-Dienst ohne Authentifizierung erlaubt anderen, ihn zu steuern. Für Fernzugriff beschreibt die [Docker-Anleitung zum Socket-Schutz](https://docs.docker.com/engine/security/protect-access/) SSH oder TLS mit passender Zertifikatsprüfung; bei gegenseitigem TLS muss auch der Dienst die Clients prüfen.
- **Fremde Images:** Können Schadcode enthalten; feste Versionen aus vertrauenswürdigen Quellen nutzen.
- **Anmeldedaten:** `docker login` speichert Zugangsdaten unter `~/.docker`.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `permission denied ... /var/run/docker.sock` | Weder Root noch Gruppe `docker`, oder Gruppe noch nicht aktiv. | Neu anmelden; Gruppenmitgliedschaft bewusst entscheiden. |
| `Cannot connect to the Docker daemon` | Dienst läuft nicht. | `systemctl status docker`. |
| `docker: command not found` | Nicht installiert. | Paket `docker.io` oder offizielle Installation. |
| `port is already allocated` | Port belegt. | Anderen Host-Port wählen. |
| `No space left on device` | Images und Volumes füllen den Speicher. | `docker system df`; gezielt aufräumen. |
| Container sofort `Exited` | Hauptprozess beendet oder Fehler. | `docker logs`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit lesenden Befehlen** (`ps -a`, `images`, `logs`) beginnen.
2. **Gruppe `docker` nur vertrauenswürdigen Konten** geben oder den Rootless-Modus prüfen.
3. **Daten in Volumes** speichern, nicht im Container.
4. **Vor `prune` mit `docker system df`** prüfen, was betroffen ist.
5. **Ports an `127.0.0.1` binden,** wenn sie nur lokal gebraucht werden (`-p 127.0.0.1:8080:80`).
6. **Feste Image-Versionen** statt `latest`.

### Prüfstand

- **Geprüfte Version:** keine; Docker ist auf dem Prüfsystem nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): Debian-Manpage `docker(1)`, Docker-Sicherheitsdokumentation (Angriffsfläche des Dienstes), Anleitung nach der Installation (Gruppe `docker`), Befehlsreferenzen zu `docker container ls` und `docker system prune`.
- **Nicht geprüft:** alle Aufrufe, Fehlermeldungen, Firewall-Verhalten, Rootless-Modus.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `docker compose`, `docker-compose` | Mehrere Container per YAML-Datei. |
| `podman` | Docker-kompatibel, ohne zentralen Root-Dienst. |
| `nerdctl` | Docker-ähnlicher Client für containerd. |
| `containerd`, `runc` | Unterbau, den Docker verwendet. |
| `skopeo` | Images in Registries prüfen und kopieren. |

Ausgangseintrag: Datensatz 139 in `index.json` (`docker`, Kurzbeschreibung „Verwaltet Docker-Container, Images und Netzwerke.“, Beispiel `docker ps -a`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Die zutreffenden Angaben wurden übernommen; ergänzt wurden die Root-Gleichwertigkeit der Gruppe `docker`, Befehlsübersicht, Optionen und Sicherheitsfolgen.
