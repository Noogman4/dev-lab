---
id: "podman_compose"
name: "podman-compose"
command: "podman-compose"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "podman", "compose", "rootless"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 148
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# podman-compose – Compose-Dateien mit Podman ausführen

## 1. Kurzbeschreibung

`podman-compose` führt Anwendungen aus mehreren Containern aus, die in einer Compose-Datei (`docker-compose.yml` oder `compose.yaml`) beschrieben sind – mit **Podman** statt Docker. Es ist ein eigenständiges Programm, das die Compose-Datei liest und daraus `podman`-Aufrufe erzeugt.

**Root-Rechte sind nicht nötig,** weil Podman rootless arbeiten kann. Es gelten die Voraussetzungen von Podman (Bereiche in `/etc/subuid` und `/etc/subgid`). Eine Ausnahme ist die einmalige systemd-Einrichtung, für die die Manpage `sudo podman-compose systemd -a create-unit` vorsieht.

Grundlage ist die [Debian-Manpage zu podman-compose](https://manpages.debian.org/trixie/podman-compose/podman-compose.1.en.html). Auf dem geprüften System ist es nicht installiert.

### Abgrenzung zu `podman compose`

Podman selbst kennt den Befehl `podman compose`. Laut [Debian-Manpage zu podman](https://manpages.debian.org/trixie/podman/podman.1.en.html) führt dieser Compose-Arbeitslasten „über einen externen Compose-Anbieter“ aus – das kann `podman-compose` oder ein anderes Compose-Programm sein. **Prüfpunkt:** Welcher Anbieter verwendet wird, hängt von Installation und Konfiguration ab.

## 2. Was macht der Befehl?

`podman-compose up` liest die Compose-Datei, kann die Dienste in einem gemeinsamen **Pod** anlegen (steuerbar mit `--in-pod`; **Prüfpunkt:** die Vorgabe ist in der Manpage nicht beschrieben), erzeugt Netzwerke und Volumes und startet die Dienste als Podman-Container. `down` baut alles wieder ab. Der Projektname leitet sich vom Ordnernamen ab.

Befehle laut Manpage:

| Befehl | Wirkung |
| --- | --- |
| `up` | Stapel oder einzelne Dienste anlegen und starten. |
| `down` | Gesamten Stapel abbauen. |
| `ps`, `logs`, `images`, `port`, `stats`, `config` | Zustand ansehen. |
| `start`, `stop`, `restart`, `pause`, `unpause`, `kill` | Laufende Dienste steuern. |
| `run`, `exec` | Einmalbefehl bzw. Befehl in laufendem Container. |
| `pull`, `push`, `build` | Images laden, hochladen, bauen. |
| `systemd` | systemd-Einheiten für Compose-Stapel erzeugen. |
| `wait` | Auf das Ende laufender Container warten. |

## 3. Syntax

```text
podman-compose [OPTIONEN] BEFEHL [ARGUMENTE]
```

```bash
podman-compose up -d
podman-compose ps
podman-compose logs
podman-compose down
```

Das bisherige NetMon-Beispiel `podman-compose --help` ist gültig (`-h`, `--help` laut Manpage). Der Platzhalter `podman-compose [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert. **Prüfpunkt:** Die Option `-d` bei `up` ist von Docker Compose übernommen und in der Manpage nicht einzeln aufgeführt.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-f DATEI`, `--file DATEI` | Compose-Datei; Standard `docker-compose.yml`, `-` für Standardeingabe. | – |
| `-p NAME`, `--project-name NAME` | Projektname statt Ordnername. | – |
| `--env-file DATEI` | Andere Umgebungsdatei. | – |
| `--profile NAME` | Profil aktivieren. | – |
| `--in-pod WERT` | Steuern, ob ein Pod angelegt wird. | – |
| `--dry-run` | Keine Aktion, nur Simulation der Befehle. | Gut zum Prüfen. |
| `--no-cleanup` | Vorhandenen Pod und Container nicht stoppen und entfernen. | – |
| `--podman-run-args ...` und Verwandte | Zusätzliche Argumente an einzelne Podman-Befehle. | – |
| `--verbose` | Diagnoseausgaben. | – |
| `-v`, `--version` | Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein Compose-Projekt zuerst simulieren, dann rootless starten und wieder abbauen. Voraussetzung: Podman und `podman-compose` installiert. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Projekt anlegen

```bash
uebung="$(mktemp -d -t netmon-pcompose-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'services:\n  web:\n    image: docker.io/library/nginx:stable\n    ports:\n      - "127.0.0.1:8080:80"\n' > docker-compose.yml
```

### Schritt 2: Simulieren

```bash
podman-compose --dry-run up
```

Zeigt die Podman-Befehle, die ausgeführt würden, ohne sie auszuführen.

### Schritt 3: Starten und prüfen

```bash
podman-compose up -d
podman-compose ps
```

### Schritt 4: Abbauen

```bash
podman-compose down
```

## 6. Typische Anwendungsfälle

- **Vorhandene Compose-Projekte ohne Docker** betreiben.
- **Rootless Entwicklungsumgebungen** mit mehreren Diensten.
- **Dauerhafte Dienste** über die systemd-Einbindung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Kompatibilität:** Nicht jede Compose-Funktion verhält sich wie bei Docker Compose. **Prüfpunkt:** Unterschiede nicht im Einzelnen geprüft.
- **Fremde Compose-Dateien** vor `up` lesen: Images, Ports, Mounts.
- **Datenverlust:** `down` entfernt Container; ob Volumes erhalten bleiben, hängt von Optionen und Version ab. **Prüfpunkt:** Volumenverhalten von `down` nicht in der Manpage beschrieben.
- **systemd-Einrichtung mit `sudo`:** verändert Systemkonfiguration.
- **Ports** ohne `127.0.0.1` sind im Netz erreichbar.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `podman-compose: command not found` | Nicht installiert. | Paket `podman-compose`. |
| Datei nicht gefunden | Standardname `docker-compose.yml` fehlt. | `-f compose.yaml`. |
| Rootless-Fehler | subuid/subgid fehlen. | Siehe `podman`. |
| Port unter 1024 lässt sich nicht öffnen | Rootless darf niedrige Ports standardmäßig nicht binden. | Höheren Port verwenden. **Prüfpunkt:** Systemeinstellung nicht geprüft. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `--dry-run` beginnen.**
2. **Projektnamen mit `-p` festlegen.**
3. **Ports an `127.0.0.1` binden.**
4. **Compose-Dateien vor dem Start lesen.**

### Prüfstand

- **Geprüfte Version:** keine; `podman-compose` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpages `podman-compose(1)` (Optionen und Befehle) und `podman(1)` (Abgrenzung zu `podman compose`), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Kompatibilität zu Docker Compose, Volumenverhalten, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `podman` | Container-Engine, die `podman-compose` aufruft. |
| `podman compose` | Podman-Befehl, der einen externen Compose-Anbieter nutzt. |
| `docker compose` | Compose für Docker. |
| `podman kube play` | Kubernetes-YAML statt Compose. |

Ausgangseintrag: Datensatz 148 in `index.json` (`podman-compose`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Arbeitsweise, Befehle, Optionen, Abgrenzung zu `podman compose` und einen Ablauf mit Simulation ersetzt.
