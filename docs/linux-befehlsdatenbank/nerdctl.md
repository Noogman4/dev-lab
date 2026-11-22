---
id: "nerdctl"
name: "nerdctl"
command: "nerdctl"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "containerd", "docker-kompatibel", "rootless"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 146
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# nerdctl – Docker-kompatible Kommandozeile für containerd

## 1. Kurzbeschreibung

`nerdctl` („contaiNERD CTL“) ist eine **Docker-kompatible Kommandozeile für containerd**. Befehle und Optionen entsprechen weitgehend denen von `docker`: `nerdctl run`, `nerdctl ps`, `nerdctl build`, `nerdctl compose up`. Statt des Docker-Dienstes arbeitet es direkt mit containerd.

**Root-Rechte sind im Standardbetrieb nötig,** weil der containerd-Socket nur Root zugänglich ist; das [README des Projekts](https://github.com/containerd/nerdctl) zeigt die Beispiele entsprechend mit Root-Eingabeaufforderung. Optional gibt es einen **Rootless-Modus**: Mit `containerd-rootless-setuptool.sh install` wird ein containerd unter dem eigenen Konto eingerichtet, danach funktioniert `nerdctl` ohne Root.

Laut README ist `nerdctl` ein Unterprojekt von containerd, aber kein Kernbestandteil. Für Debian trixie gibt es keine Manpage. Auf dem geprüften System sind weder `nerdctl` noch containerd installiert.

## 2. Was macht der Befehl?

`nerdctl` übersetzt Docker-ähnliche Befehle in Aufrufe an containerd. Laut README unterstützt es:

- die gleiche Bedienung wie `docker`,
- Docker-Compose-Dateien über `nerdctl compose`,
- optional den Rootless-Betrieb,
- optional nachgeladene Images (Stargz, Nydus, OverlayBD), verschlüsselte Images und Image-Signaturen (cosign),
- optional P2P-Verteilung über IPFS – laut README **nur**, wenn man sich ausdrücklich dafür entscheidet.

Für einige Funktionen braucht es Zusatzkomponenten: **CNI-Plugins** für `nerdctl run` mit Netzwerk, **BuildKit** (`buildkitd`) für `nerdctl build` und **RootlessKit** für den Rootless-Modus. Das Archiv „nerdctl-full“ enthält diese Komponenten.

### Namespaces

containerd trennt Bestände in Namespaces. Laut README liegen die Container eines lokalen Kubernetes im Namespace `k8s.io`; mit `nerdctl --namespace k8s.io ps -a` werden sie sichtbar.

## 3. Syntax

```text
nerdctl [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] [ARGUMENTE]
```

```bash
sudo nerdctl run -it --rm alpine
sudo nerdctl ps -a
sudo nerdctl --namespace k8s.io ps -a
nerdctl compose -f compose.yaml up -d
```

Das bisherige NetMon-Beispiel `nerdctl --help` zeigt die Hilfe. Der Platzhalter `nerdctl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert. **Prüfpunkt:** Die vollständige Befehlsreferenz (`docs/command-reference.md` im Projekt) wurde nicht gelesen; Optionen über `nerdctl BEFEHL --help` der installierten Version prüfen.

## 4. Wichtige Optionen

| Befehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `run -it --rm IMAGE` | Container interaktiv starten und danach entfernen. | Standardnetz laut README `10.4.0.0/24`. |
| `run -d -p HOST:CONT --name N IMAGE` | Container im Hintergrund mit Portfreigabe. | Port an `127.0.0.1` binden, wenn nur lokal benötigt. |
| `ps -a` | Alle Container. | Nur lesend. |
| `build -t NAME ORDNER` | Image bauen. | Braucht laufendes BuildKit. |
| `load < ARCHIV.tar` | Image-Archiv laden. | Docker- oder OCI-Format. |
| `logs -f ID` | Protokolle verfolgen. | Laut README teils experimentell. |
| `compose -f DATEI up` | Compose-Projekt starten. | – |
| `--namespace NAME` | containerd-Namespace wählen. | `k8s.io` für Kubernetes. |
| `system prune` | Ungenutzte Daten entfernen. | Laut README braucht der Build-Cache-Teil BuildKit ab 0.11. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Kubernetes-Knoten mit containerd die Kubernetes-Container ansehen und ein Protokoll lesen – nur lesend. Das ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Container im Kubernetes-Namespace auflisten

```bash
sudo nerdctl --namespace k8s.io ps -a
```

In der Spalte `NAMES` erscheinen Einträge wie `k8s://kube-system/...`.

### Schritt 2: Protokoll lesen

```bash
sudo nerdctl --namespace k8s.io logs --tail 50 CONTAINER_ID
```

**Prüfpunkt:** `--tail` ist aus Docker übernommen und nicht in den gelesenen Quellen bestätigt.

### Schritt 3: Image für lokales Kubernetes laden

```bash
sudo nerdctl --namespace k8s.io load < meine-app.tar
```

Das Image steht danach im Namespace `k8s.io` bereit, ohne Registry. Das ist bereits eine Änderung am Knoten.

## 6. Typische Anwendungsfälle

- **Docker-Gewohnheiten auf containerd-Systemen** weiterverwenden.
- **Fehlersuche auf Kubernetes-Knoten** mit vertrauter Bedienung.
- **Rootless-Container** ohne Docker-Dienst.
- **Compose-Projekte** ohne Docker.
- **Images für ein lokales Kubernetes** ohne Registry bereitstellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Root-Betrieb:** Wer `nerdctl` mit Root nutzt, kann Container mit Host-Mounts und erweiterten Rechten starten und damit das System verändern.
- **Kubernetes-Namespace:** Eingriffe im Namespace `k8s.io` (Stoppen, Löschen) gehen am Kubelet vorbei und können Pods stören.
- **Portfreigaben** machen Dienste im Netz erreichbar.
- **Löschen:** `rm`, `rmi` und `system prune` entfernen ohne Papierkorb.
- **Fremde Images** können Schadcode enthalten.
- **Rootless-Einrichtung** verändert Dienste des Benutzerkontos.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `nerdctl: command not found` | Nicht installiert. | Binärarchiv aus den Projekt-Releases. |
| Rechtefehler am containerd-Socket | Ohne Root und ohne Rootless-Einrichtung. | `sudo` oder Rootless-Modus. |
| `run` ohne Netzwerk | CNI-Plugins fehlen. | Archiv „nerdctl-full“ oder CNI-Plugins installieren. |
| `build` schlägt fehl | BuildKit läuft nicht. | `buildkitd` einrichten. |
| Kubernetes-Container fehlen | Falscher Namespace. | `--namespace k8s.io`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Rootless-Modus prüfen,** wenn kein Root nötig ist.
2. **Im Namespace `k8s.io` nur lesen.**
3. **Ports an `127.0.0.1` binden.**
4. **Feste Image-Versionen** verwenden.

### Prüfstand

- **Geprüfte Version:** keine; `nerdctl` ist nicht installiert, keine Debian-Manpage vorhanden.
- **Quellen gelesen:** README des nerdctl-Projekts auf GitHub (Funktionen, Beispiele, Rootless, Abhängigkeiten), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, vollständige Befehlsreferenz, Optionen wie `--tail`, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `docker` | Vorbild der Bedienung. |
| `containerd` | Dienst, den `nerdctl` steuert. |
| `ctr` | Einfacher, nicht unterstützter Debug-Client von containerd. |
| `crictl` | Client über die Kubernetes-CRI. |
| `podman` | Weitere Docker-kompatible Alternative ohne zentralen Dienst. |

Ausgangseintrag: Datensatz 146 in `index.json` (`nerdctl`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde für den Standardbetrieb auf „erforderlich“ korrigiert; der Rootless-Modus ist als Alternative beschrieben. Der Hilfe-Platzhalter wurde durch Funktionsumfang, Abhängigkeiten, Namespaces und einen lesenden Ablauf ersetzt.
