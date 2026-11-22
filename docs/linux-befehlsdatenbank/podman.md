---
id: "podman"
name: "podman"
command: "podman"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "rootless", "pods", "docker-kompatibel"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 147
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# podman – Container und Pods ohne zentralen Hintergrunddienst verwalten

## 1. Kurzbeschreibung

Podman („Pod Manager“) ist laut [Debian-Manpage zu podman](https://manpages.debian.org/trixie/podman/podman.1.en.html) eine vollständige **Container-Engine ohne Hintergrunddienst**. Die Bedienung entspricht weitgehend der von Docker – die Manpage fasst es mit `alias docker=podman` zusammen. Zusätzlich kennt Podman **Pods**: Gruppen von Containern, die sich Netzwerk und andere Namensräume teilen, wie in Kubernetes.

**Root-Rechte sind nicht nötig.** Laut Manpage lassen sich die meisten Podman-Befehle als normaler Benutzer ausführen („rootless“). Dafür braucht das Konto Bereiche untergeordneter IDs in `/etc/subuid` und `/etc/subgid`; auf dem geprüften System hat das Konto einen solchen Eintrag. Mit Root-Rechten arbeitet Podman mit einem getrennten Bestand.

Auf dem geprüften System ist Podman nicht installiert.

## 2. Was macht der Befehl?

Jeder `podman`-Aufruf ist ein eigener Prozess; es gibt keinen Dienst wie `dockerd`, der dauerhaft mit Root-Rechten läuft. Container laufen als Kindprozesse.

Wichtige Eigenschaften laut Manpage:

- **Getrennte Bestände:** Rootless-Container eines Benutzers sind für andere Benutzer und für Podman als Root unsichtbar.
- **Speicherorte:** Rootless unter `~/.local/share/containers/storage`, Konfiguration unter `~/.config/containers`; als Root unter `/var/lib/containers/storage`.
- **Gemeinsam mit Buildah:** Podman nutzt Buildah intern zum Bauen. Beide teilen sich **Images**, aber nicht Container.
- **Fernzugriff:** Mit `--remote`, `--connection` oder `--url` kann Podman einen entfernten Podman-Dienst steuern.

Die Manpage listet zahlreiche Unterbefehle, darunter `run`, `ps`, `images`, `pull`, `build`, `exec`, `logs`, `stop`, `rm`, `rmi`, `pod`, `network`, `volume`, `kube`, `generate`, `machine`, `secret`, `unshare` und `system`.

## 3. Syntax

```text
podman [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] [ARGUMENTE]
```

```bash
podman run --rm -it docker.io/library/alpine:3.20 sh
podman ps -a
podman images
podman pod create --name app
```

Das bisherige NetMon-Beispiel `podman --help` zeigt die Hilfe. Der Platzhalter `podman [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Befehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `run --rm -it IMAGE` | Container interaktiv starten, danach entfernen. | Vollständigen Imagenamen verwenden. |
| `ps -a` | Alle Container. | Nur lesend. |
| `images` | Lokale Images. | Nur lesend. |
| `logs`, `inspect` | Protokolle bzw. Details. | Nur lesend. |
| `pod create`, `pod ps` | Pods anlegen bzw. auflisten. | – |
| `kube play DATEI` | Kubernetes-YAML lokal ausführen. | **Prüfpunkt:** Details in `podman-kube(1)`, nicht gelesen. |
| `unshare` | Shell im Benutzer-Namensraum. | Für Dateirechte in rootless Volumes. |
| `system prune` | Ungenutzte Daten entfernen. | Endgültig. |
| `--root`, `--runroot` | Andere Speicherorte. | – |
| `--remote`, `-r` / `--connection`, `-c` | Entfernten Podman-Dienst steuern. | – |
| `--log-level` | Ausführlichkeit. | – |

### Rückgabewerte laut Manpage

| Code | Bedeutung |
| --- | --- |
| `125` | Fehler in Podman selbst, etwa unbekannte Option. |
| `126` | Befehl im Container kann nicht ausgeführt werden. |
| `127` | Befehl im Container nicht gefunden. |
| sonst | Rückgabewert des Container-Befehls. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ohne Root einen Wegwerf-Container starten, prüfen und aufräumen. Voraussetzung: Podman installiert, subuid/subgid eingerichtet. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Umgebung prüfen

```bash
podman info
```

Zeigt unter anderem, ob Podman rootless läuft und wo der Speicher liegt.

### Schritt 2: Container starten

```bash
podman run --rm docker.io/library/alpine:3.20 cat /etc/os-release
echo $?
```

Podman lädt das Image in deinen eigenen Speicher, führt den Befehl aus und löscht den Container danach (`--rm`). `echo $?` zeigt den Rückgabewert des Befehls im Container, hier `0`.

### Schritt 3: Bestand ansehen

```bash
podman images
podman ps -a
```

Das Image ist vorhanden, der Container nicht mehr.

### Schritt 4: Aufräumen

```bash
podman rmi docker.io/library/alpine:3.20
```

## 6. Typische Anwendungsfälle

- **Docker-Ersatz ohne Root-Dienst** auf Entwicklerrechnern.
- **Pods** lokal testen, bevor sie nach Kubernetes gehen.
- **Dienste mit systemd** verwalten (Podman kann dafür Einheiten erzeugen). **Prüfpunkt:** nicht in gelesenen Quellen nachgeschlagen.
- **Images bauen** mit `podman build` (intern Buildah).
- **Compose-Projekte** über `podman compose` beziehungsweise `podman-compose`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Rootless ist sicherer, aber keine vollständige Isolation:** Container-Prozesse laufen mit deinen Rechten. Was du darfst, darf auch ein eingehängter Ordner im Container.
- **Mit Root (`sudo podman`)** gelten dieselben Risiken wie bei Docker: Host-Mounts und `--privileged` geben Zugriff auf das System.
- **Gemischte Bestände:** Images und Container von `sudo podman` und `podman` sind getrennt; das verwirrt leicht.
- **Kurze Imagenamen:** Ohne Registry-Präfix kann eine Auswahl zwischen Registries stattfinden; vollständige Namen sind eindeutiger.
- **Speicher:** Rootless verwendet je nach Treiber mehr Platz.
- **Löschen:** `rm`, `rmi`, `system prune` ohne Papierkorb.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `podman: command not found` | Nicht installiert. | Paket `podman`. |
| Fehler zu subuid/subgid | Konto hat keine ID-Bereiche. | Verwaltung trägt Bereiche ein. |
| Rückgabewert `125` | Fehler in Podman, etwa unbekannte Option. | Meldung lesen, Optionen prüfen. |
| Rückgabewert `127` | Befehl im Container fehlt. | Image-Inhalt prüfen. |
| Dateien im Volume gehören fremden IDs | Benutzer-Namensraum bildet IDs ab. | `podman unshare` zum Bearbeiten. |
| Container von `sudo podman` fehlen | Getrennte Bestände. | Mit derselben Rechteebene arbeiten. |

**Prüfpunkt:** Außer den Rückgabewerten aus der Manpage sind Meldungen sinngemäß wiedergegeben und nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Rootless arbeiten,** `sudo` nur bei Bedarf.
2. **Vollständige Imagenamen mit Version.**
3. **`--rm` für Wegwerf-Container.**
4. **`podman info`** bei Problemen zuerst.
5. **Ports an `127.0.0.1` binden,** wenn nur lokal gebraucht.

### Prüfstand

- **Geprüfte Version:** keine; Podman ist nicht installiert. Lokal geprüft wurde nur, dass das Konto einen Eintrag in `/etc/subuid` hat.
- **Quellen gelesen:** Debian-Manpage `podman(1)` (Beschreibung, globale Optionen, Rootless-Modus, Rückgabewerte, Befehlsliste), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, `kube play`, systemd-Einbindung, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `docker` | Vorbild der Bedienung, mit zentralem Dienst. |
| `buildah` | Image-Bau; teilt Images mit Podman. |
| `skopeo` | Images in Registries prüfen und kopieren. |
| `podman-compose` | Compose-Dateien mit Podman. |
| `kubectl` | Für echte Kubernetes-Cluster. |

Ausgangseintrag: Datensatz 147 in `index.json` (`podman`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Die Root-Angabe wurde auf „nicht erforderlich“ korrigiert, weil Podman für den Rootless-Betrieb ausgelegt ist. Der Hilfe-Platzhalter wurde durch Arbeitsweise ohne Dienst, Speicherorte, Rückgabewerte und einen rootless Ablauf ersetzt.
