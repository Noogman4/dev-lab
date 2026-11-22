---
id: "crictl"
name: "crictl"
command: "crictl"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "kubernetes", "cri", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 137
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# crictl – Container und Pods auf Kubernetes-Knoten untersuchen

## 1. Kurzbeschreibung

`crictl` ist ein Kommandozeilenwerkzeug für **CRI-kompatible Container-Laufzeiten** wie containerd oder CRI-O. CRI ist die Schnittstelle, über die Kubernetes (genauer: das Kubelet) Container startet. `crictl` dient vor allem der **Fehlersuche direkt auf einem Kubernetes-Knoten**: Pods, Container, Images und Protokolle ansehen.

**Root-Rechte sind praktisch nötig.** `crictl` spricht über den Socket der Laufzeit, etwa `/run/containerd/containerd.sock`, und dieser ist normalerweise nur für Root zugänglich. **Prüfpunkt:** Die Socket-Rechte hängen von der Laufzeitkonfiguration ab.

Grundlagen sind die Kubernetes-Seite [Debugging Kubernetes nodes with crictl](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/) und die [crictl-Dokumentation im cri-tools-Projekt](https://github.com/kubernetes-sigs/cri-tools/blob/master/docs/crictl.md). Für Debian trixie gibt es keine Manpage zu `crictl`. Auf dem geprüften System ist `crictl` nicht installiert.

## 2. Was macht der Befehl?

`crictl` sendet Anfragen an die Laufzeit über den Socket. Laut Dokumentation versucht es ohne Angabe eine Liste bekannter Endpunkte, darunter `unix:///run/containerd/containerd.sock` und `unix:///run/crio/crio.sock`. Den Endpunkt legt man besser fest:

- mit `--runtime-endpoint` und `--image-endpoint`,
- mit den Variablen `CONTAINER_RUNTIME_ENDPOINT` und `IMAGE_SERVICE_ENDPOINT`,
- oder in `/etc/crictl.yaml` (andere Datei mit `--config`).

Laut Kubernetes-Dokumentation kann das automatische Durchprobieren die Geschwindigkeit beeinträchtigen.

### Unterbefehle nach Wirkung

| Wirkung | Unterbefehle |
| --- | --- |
| Lesen | `pods`, `ps`, `images`, `inspect`, `inspectp`, `inspecti`, `logs`, `stats`, `statsp`, `info`, `version`, `events`, `imagefsinfo` |
| Eingreifen | `exec`, `attach`, `port-forward`, `pull`, `start`, `stop`, `stopp`, `update`, `checkpoint` |
| Anlegen | `create`, `run`, `runp` |
| Löschen | `rm`, `rmi`, `rmp` |
| Konfiguration | `config`, `update-runtime-config` |

## 3. Syntax

```text
crictl [GLOBALE_OPTIONEN] BEFEHL [BEFEHLSOPTIONEN] [ARGUMENTE]
crictl help
crictl BEFEHL help
```

```bash
sudo crictl pods
sudo crictl ps -a
sudo crictl logs --tail=50 CONTAINER_ID
sudo crictl images
```

Das bisherige NetMon-Beispiel `crictl --help` zeigt die Hilfe; die Kubernetes-Dokumentation nennt `crictl help` und `crictl BEFEHL help`. Der Platzhalter `crictl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--runtime-endpoint ADRESSE` | Socket der Laufzeit. | Etwa `unix:///run/containerd/containerd.sock`. |
| `--image-endpoint ADRESSE` | Socket für Image-Dienst. | Meist gleich. |
| `--config DATEI` | Andere Konfigurationsdatei als `/etc/crictl.yaml`. | – |
| `--timeout`, `--debug` | Zeitlimit und Diagnose. | Auch in der Konfigurationsdatei. |
| `pods --name NAME`, `pods --label k=v` | Pods filtern. | Laut Kubernetes-Beispielen. |
| `ps -a` | Auch beendete Container. | – |
| `images -q` | Nur Image-IDs. | – |
| `logs --tail=N ID` | Letzte Zeilen eines Container-Protokolls. | – |
| `exec -i -t ID BEFEHL` | Befehl in laufendem Container. | Eingriff in einen produktiven Container. |
| `rmi BILD` | Image entfernen. | Siehe Abschnitt 7. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Kubernetes-Knoten mit containerd herausfinden, warum ein Container neu startet – nur lesend. Das ist ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Endpunkt festlegen

```bash
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock info
```

Liefert Informationen zur Laufzeit. Funktioniert das, kann der Endpunkt in `/etc/crictl.yaml` eingetragen werden.

### Schritt 2: Pod finden

```bash
sudo crictl pods --name meine-app
```

Zeigt Pod-ID, Status und Namespace.

### Schritt 3: Container mit Neustarts finden

```bash
sudo crictl ps -a
```

Die Spalte `ATTEMPT` zeigt, wie oft ein Container neu gestartet wurde; `STATE` zeigt `Exited` für beendete.

### Schritt 4: Protokoll lesen

```bash
sudo crictl logs --tail=50 CONTAINER_ID
```

Die letzten 50 Zeilen enthalten meist die Fehlerursache.

## 6. Typische Anwendungsfälle

- **Fehlersuche,** wenn `kubectl` nicht erreichbar ist oder das Kubelet Probleme hat.
- **Images auf einem Knoten prüfen** oder gezielt vorab laden (`pull`).
- **Ressourcen ansehen** mit `stats` und `statsp`.
- **Laufzeitinformationen** mit `info` und `version`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`; lesende Befehle sind harmlos, eingreifende nicht.

- **Am Kubelet vorbei:** `crictl` arbeitet direkt mit der Laufzeit. Gestoppte oder gelöschte Pods und Container kann das Kubelet wieder anlegen oder in einen unerwarteten Zustand bringen. Für normale Verwaltung ist `kubectl` vorgesehen. **Prüfpunkt:** genaues Zusammenspiel nicht geprüft.
- **`rmi` entfernt alle Tags:** Laut cri-tools-Dokumentation entfernt `crictl rmi` wegen Einschränkungen der CRI-Schnittstelle **das ganze Image mit allen Tags**, auch wenn nur ein Tag angegeben ist – anders als `docker rmi` oder `nerdctl rmi`.
- **`exec` und `attach`** greifen in laufende, womöglich produktive Container ein.
- **Protokolle** können vertrauliche Daten enthalten.
- **Root-Zugriff** auf den Laufzeit-Socket entspricht voller Kontrolle über den Knoten.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `crictl: command not found` | Nicht installiert. | Laut Doku Release-Archiv passend zur Kubernetes-Version. |
| Verbindungsfehler zum Socket | Falscher Endpunkt oder Laufzeit läuft nicht. | Endpunkt setzen; Dienst prüfen. |
| `permission denied` am Socket | Ohne Root. | Mit `sudo`. |
| Warnung zu Standard-Endpunkten | Kein Endpunkt konfiguriert. | `/etc/crictl.yaml` anlegen. |
| Unerwartet verschwundene Tags | `rmi` entfernt alle Tags. | Für einzelne Tags das Werkzeug der Laufzeit verwenden. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Endpunkt in `/etc/crictl.yaml` festlegen.**
2. **Nur lesende Befehle** (`pods`, `ps`, `logs`, `inspect`) für die Fehlersuche.
3. **Verwaltung über `kubectl`,** nicht über `crictl`.
4. **Version passend zur Kubernetes-Version** verwenden.
5. **Vor `rmi` an den Tag-Verlust denken.**

### Prüfstand

- **Geprüfte Version:** keine; `crictl` ist nicht installiert, und Debian bietet keine Manpage dazu.
- **Quellen gelesen** (Abruf 2026-11-13): Kubernetes-Dokumentation zu crictl (Endpunkte, Konfiguration, Beispiele) und `docs/crictl.md` im cri-tools-Repository (Unterbefehle, Standard-Endpunkte, Hinweis zu `rmi`).
- **Nicht geprüft:** alle Aufrufe, Socket-Rechte, Zusammenspiel mit dem Kubelet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kubectl` | Verwaltung über die Kubernetes-API. |
| `ctr` | Einfacher Client nur für containerd. |
| `nerdctl` | Docker-ähnlicher Client für containerd. |
| `containerd` | Häufige CRI-Laufzeit. |
| `journalctl -u kubelet` | Protokolle des Kubelet. |

Ausgangseintrag: Datensatz 137 in `index.json` (`crictl`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert, weil der Laufzeit-Socket meist nur Root zugänglich ist. Der Hilfe-Platzhalter wurde durch Endpunkte, Unterbefehle nach Wirkung, das Verhältnis zum Kubelet und einen lesenden Ablauf ersetzt.
