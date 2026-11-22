---
id: "ctr"
name: "ctr"
command: "ctr"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "containerd", "fehlersuche", "laufzeit"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 138
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# ctr – Diagnose-Client für containerd

## 1. Kurzbeschreibung

`ctr` ist der mit containerd ausgelieferte Kommandozeilen-Client. Er spricht direkt mit dem containerd-Dienst und kann Images laden, Container und Aufgaben („tasks“) anlegen, auflisten, stoppen und löschen. Laut [Debian-Manpage zu ctr](https://manpages.debian.org/trixie/containerd/ctr.8.en.html) ist `ctr` ausdrücklich ein **nicht unterstützter Debug- und Verwaltungs-Client**: Befehle, Optionen und Verhalten müssen zwischen containerd-Versionen nicht kompatibel bleiben.

**Root-Rechte sind praktisch nötig.** `ctr` verbindet sich standardmäßig mit `/run/containerd/containerd.sock`; dieser Socket ist normalerweise nur für Root zugänglich.

Für den Alltag sind komfortablere Clients vorgesehen: `nerdctl` (Docker-ähnlich) oder auf Kubernetes-Knoten `crictl`. Auf dem geprüften System sind weder `ctr` noch containerd installiert.

## 2. Was macht der Befehl?

containerd unterscheidet Begriffe, die bei Docker zusammenfallen:

| Begriff | Bedeutung |
| --- | --- |
| Image | Geladenes Container-Abbild. |
| Container | Metadaten und Konfiguration eines Containers – läuft noch nicht. |
| Task | Der laufende Prozess eines Containers. |
| Snapshot | Dateisystemstand für einen Container. |
| Namespace | Trennt Bestände verschiedener Nutzer von containerd. Standard: `default`. |

Wichtige Befehlsgruppen laut Manpage: `images` (`pull`, `list`, `export`, `import`, `remove`), `containers` (`create`, `list`, `info`, `delete`), `tasks` (`list`, `kill`, `attach`, `delete`), `run`, `snapshots`, `namespaces`, `content`, `events`, `plugins`, `version`.

### Namespaces

Ein Image, das Docker oder Kubernetes über containerd geladen hat, erscheint in `ctr images ls` nur, wenn der passende Namespace mit `-n` gewählt ist. Mit `ctr namespaces ls` siehst du, welche existieren. Laut [README des nerdctl-Projekts](https://github.com/containerd/nerdctl) liegen die Container eines lokalen Kubernetes im Namespace `k8s.io`. **Prüfpunkt:** Den Namespace von Docker nennt keine der gelesenen Quellen.

## 3. Syntax

```text
ctr [GLOBALE_OPTIONEN] BEFEHL [UNTERBEFEHL] [OPTIONEN] [ARGUMENTE]
```

```bash
sudo ctr version
sudo ctr namespaces ls
sudo ctr -n default images ls
sudo ctr images pull docker.io/library/alpine:latest
```

Das bisherige NetMon-Beispiel `ctr --help` zeigt die Hilfe. Der Platzhalter `ctr [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--address`, `-a` | Socket von containerd. | Standard `/run/containerd/containerd.sock`. |
| `--namespace`, `-n` | containerd-Namespace. | Standard `default`. |
| `--timeout`, `--connect-timeout` | Zeitlimits. | Standard `0s` (kein Limit). |
| `--debug` | Diagnoseausgaben. | – |
| `images pull REFERENZ` | Image laden. | Vollständige Referenz mit Registry verwenden. **Prüfpunkt:** Kurzformen nicht geprüft. |
| `images ls` | Images auflisten. | Nur lesend. |
| `containers ls`, `tasks ls` | Container bzw. laufende Tasks. | Nur lesend. |
| `run IMAGE ID` | Container anlegen und starten. | Viele Sicherheitsoptionen, siehe unten. |
| `tasks kill ID` | Signal senden (Standard SIGTERM). | `-s` für anderes Signal. |
| `containers delete ID` | Container entfernen. | `--keep-snapshot` behält das Dateisystem. |
| `namespaces remove NAME` | Namespace entfernen. | `--cgroup` löscht auch die cgroup. |

### Sicherheitsrelevante Optionen bei `create` und `run`

`--privileged`, `--net-host`, `--cap-add`, `--allow-new-privs`, `--mount` mit Host-Pfaden und `--device` schwächen die Isolation des Containers erheblich.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Rechner mit containerd nur lesend prüfen, welche Namespaces, Images und Container vorhanden sind. Das ist ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Verbindung prüfen

```bash
sudo ctr version
```

Zeigt Client- und Serverversion. Ein Fehler hier bedeutet meist, dass der Dienst nicht läuft oder der Socket woanders liegt.

### Schritt 2: Namespaces auflisten

```bash
sudo ctr namespaces ls
```

### Schritt 3: Images und Container eines Namespace

```bash
sudo ctr -n default images ls
sudo ctr -n default containers ls
sudo ctr -n default tasks ls
```

Statt `default` den in Schritt 2 gefundenen Namen einsetzen. `tasks ls` zeigt, welche Container tatsächlich laufen.

## 6. Typische Anwendungsfälle

- **Fehlersuche an containerd** selbst, etwa Plugins mit `ctr plugins ls`.
- **Images exportieren und importieren** (`images export`, `images import`) für Rechner ohne Registry-Zugang.
- **Prüfen, was containerd sieht,** wenn Docker oder Kubernetes Fehler melden.
- **Schnelle Tests** auf Entwicklungssystemen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Am Docker- oder Kubernetes-Verwalter vorbei:** Änderungen in deren Namespaces (Löschen, Stoppen) können Docker oder das Kubelet in inkonsistente Zustände bringen.
- **Nicht stabil:** Laut Manpage kein unterstütztes Werkzeug; Skripte können nach Updates brechen.
- **Schwache Isolation:** `--privileged`, `--net-host` oder Host-Mounts geben Containern weitreichenden Zugriff auf das System.
- **Löschen:** `containers delete`, `images remove`, `namespaces remove` entfernen ohne Papierkorb.
- **Root-Zugriff:** Wer `ctr` mit Root-Rechten benutzen darf, kontrolliert praktisch den ganzen Rechner.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `ctr: command not found` | containerd nicht installiert. | Paket `containerd`. |
| Verbindungsfehler zum Socket | Dienst läuft nicht oder ohne Root. | `systemctl status containerd`; `sudo`. |
| Image aus Docker oder Kubernetes fehlt | Falscher Namespace. | `ctr namespaces ls`, dann `-n NAME`. |
| Container lässt sich nicht löschen | Task läuft noch. | Erst `tasks kill`, dann `tasks delete`, dann `containers delete`. |
| Image-Referenz wird nicht gefunden | Kurzname ohne Registry. | Vollständige Referenz verwenden. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für Container-Arbeit `nerdctl` oder `docker` nutzen;** `ctr` nur zur Diagnose.
2. **Immer zuerst `namespaces ls`** und dann gezielt `-n` angeben.
3. **Nur lesende Befehle** (`ls`, `info`, `version`) in fremden Namespaces.
4. **Keine Sicherheitsoptionen abschwächen,** wenn nicht zwingend nötig.

### Prüfstand

- **Geprüfte Version:** keine; `ctr` und containerd sind nicht installiert.
- **Quellen gelesen:** Debian-Manpage `ctr(8)` (Status als nicht unterstützter Client, globale Optionen, Befehlsgruppen, Optionen von `containers create`, `images pull`, `namespaces`, `tasks`), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Namespace-Name von Docker, Fehlermeldungen. Der Kubernetes-Namespace `k8s.io` ist im nerdctl-README belegt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `containerd` | Der Dienst, mit dem `ctr` spricht. |
| `nerdctl` | Docker-kompatibler, unterstützter Client für containerd. |
| `crictl` | Client über die Kubernetes-CRI-Schnittstelle. |
| `runc` | Low-Level-Laufzeit unter containerd. |
| `docker` | Nutzt containerd als Unterbau. |

Ausgangseintrag: Datensatz 138 in `index.json` (`ctr`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert. Der Hilfe-Platzhalter wurde durch Begriffe (Image, Container, Task, Namespace), Befehlsgruppen, Sicherheitsoptionen und einen lesenden Ablauf ersetzt.
