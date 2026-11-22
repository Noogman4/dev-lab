---
id: "k3s"
name: "k3s"
command: "k3s"
category: "Container"
language: "de"
root_required: true
risk_level: "danger"
tags: ["container", "kubernetes", "cluster", "dienst"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 142
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# k3s – Schlanke Kubernetes-Distribution in einer einzigen Programmdatei

## 1. Kurzbeschreibung

K3s ist laut [offizieller K3s-Dokumentation](https://docs.k3s.io/) eine vollständig kompatible, leichtgewichtige **Kubernetes-Distribution**. Alle Steuerungskomponenten laufen in einer Programmdatei und einem Prozess. Mitgeliefert werden unter anderem containerd als Laufzeit, Flannel für das Netzwerk, CoreDNS, Traefik als Ingress-Controller, ein einfacher Load-Balancer und ein Speicheranbieter für lokale Volumes. Einsatzgebiete sind Homelab, Edge, Einplatinenrechner, CI und Entwicklung.

Der Befehl `k3s` startet je nach Unterbefehl einen **Server-Knoten**, einen **Agent-Knoten** oder eingebaute Werkzeuge wie `kubectl`, `crictl` und `ctr`.

**Root-Rechte sind nötig.** Installation, Server und Agent laufen als Systemdienst mit vollen Rechten, verändern Netzwerkkonfiguration und legen Daten unter `/var/lib/rancher/k3s` und `/etc/rancher/k3s` an. Auf dem geprüften System ist K3s nicht installiert.

## 2. Was macht der Befehl?

Laut [Seite zu den CLI-Werkzeugen](https://docs.k3s.io/cli):

| Unterbefehl | Wirkung |
| --- | --- |
| `k3s server` | Server-Knoten mit API-Server, Scheduler, Controller-Manager, Datenspeicher und Agent-Komponenten. |
| `k3s agent` | Arbeitsknoten mit containerd, Flannel, Netzwerkrichtlinien, kubelet und kube-proxy. |
| `k3s kubectl` | Eingebautes `kubectl`; nutzt ohne `KUBECONFIG` die Datei `/etc/rancher/k3s/k3s.yaml`. |
| `k3s crictl`, `k3s ctr` | Eingebaute Diagnose-Clients. |
| `k3s token` | Bootstrap-Tokens verwalten. |
| `k3s etcd-snapshot` | Sicherungen eines eingebetteten etcd-Datenspeichers; kein allgemeines Backup für SQLite oder Volume-Inhalte. |
| `k3s secrets-encrypt` | Verschlüsselung von Secrets einrichten. |
| `k3s certificate` | Zertifikate verwalten. |
| `k3s help` | Hilfe. |

### Installation über das Skript

Laut [Schnellstart](https://docs.k3s.io/quick-start) wird K3s meist mit einem Skript installiert, das als systemd- oder OpenRC-Dienst eingerichtet wird. Danach:

- startet der Dienst nach Neustarts und Abstürzen automatisch,
- sind `kubectl`, `crictl`, `ctr`, `k3s-killall.sh` und `k3s-uninstall.sh` installiert,
- liegt eine kubeconfig unter `/etc/rancher/k3s/k3s.yaml`,
- liegt das Token zum Hinzufügen weiterer Knoten unter `/var/lib/rancher/k3s/server/node-token`.

## 3. Syntax

```text
k3s server [OPTIONEN]
k3s agent [OPTIONEN]
k3s kubectl [KUBECTL-ARGUMENTE]
k3s help [BEFEHL]
```

```bash
sudo k3s kubectl get nodes
# Nur bei einem Cluster mit eingebettetem etcd:
sudo k3s etcd-snapshot save
sudo k3s crictl ps
```

Das bisherige NetMon-Beispiel `k3s --help` zeigt die Hilfe; die Dokumentation nennt `k3s help`. Der Platzhalter `k3s [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert. **Prüfpunkt:** Die Server- und Agent-Optionen sind sehr umfangreich und auf eigenen Seiten der Dokumentation beschrieben; sie wurden hier nicht einzeln geprüft.

## 4. Wichtige Optionen

| Variable, Pfad oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `K3S_URL` | Bei der Installation: Agent mit diesem Server verbinden. | Ohne `K3S_URL` wird ein Server installiert. |
| `K3S_TOKEN` | Token zum Beitritt. | Steht auf dem Server in `node-token`; vertraulich. |
| `K3S_NODE_NAME` | Knotenname, falls Hostnamen nicht eindeutig sind. | Laut Schnellstart muss jeder Knoten eindeutig heißen. |
| `/etc/rancher/k3s/k3s.yaml` | kubeconfig des Clusters. | Enthält Administrator-Zugang. |
| `/usr/local/bin/k3s-killall.sh` | Alle K3s-Prozesse und Container stoppen. | – |
| `/usr/local/bin/k3s-uninstall.sh` | K3s auf einem Server entfernen. | Löscht Daten, siehe Abschnitt 7. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem eigenen Testrechner einen Ein-Knoten-Cluster einrichten und prüfen. Die Installation verändert das System erheblich; das Beispiel ist ein **Beispielszenario** und wurde nicht ausgeführt. Nicht auf einem Arbeits- oder Produktivrechner ausprobieren.

### Schritt 1: Installationsskript herunterladen und lesen

```bash
curl -sfL https://get.k3s.io -o k3s-install.sh
less k3s-install.sh
```

Die Dokumentation zeigt die Installation als `curl ... | sh -`. Das Skript vorher zu speichern und zu lesen ist sicherer, weil es mit Root-Rechten läuft.

### Schritt 2: Installieren

```bash
sudo sh k3s-install.sh
```

### Schritt 3: Cluster prüfen

```bash
sudo k3s kubectl get nodes
sudo k3s kubectl get pods -A
```

Der Knoten sollte `Ready` sein; im Namespace `kube-system` laufen CoreDNS, Traefik und weitere Komponenten.

### Schritt 4: Wieder entfernen

```bash
sudo /usr/local/bin/k3s-uninstall.sh
```

## 6. Typische Anwendungsfälle

- **Homelab und Lernumgebung** für Kubernetes.
- **Edge- und IoT-Geräte,** auch ARM-Einplatinenrechner.
- **CI-Tests** mit einem echten Kubernetes.
- **Kleine Produktivcluster** mit mehreren Servern (eingebettetes etcd oder externe Datenbank).

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde auf `danger` angehoben.

- **Tiefer Systemeingriff:** Installation richtet Dienste mit Root-Rechten ein, startet Container-Laufzeit und Netzwerkkomponenten und verändert dabei Netzwerk- und Firewallregeln. **Prüfpunkt:** Zusammenspiel mit vorhandenen Firewall-, VPN- oder Killswitch-Regeln wurde nicht geprüft und kann Verbindungen beeinflussen.
- **Offene Ports:** Der API-Server lauscht laut Schnellstart auf Port 6443; Traefik veröffentlicht Ingress-Dienste.
- **Ausführen fremder Skripte:** `curl ... | sh -` führt Code aus dem Netz mit Root-Rechten aus.
- **Datenverlust bei Deinstallation:** Laut [Dokumentation zur Deinstallation](https://docs.k3s.io/installation/uninstall) stoppt das Skript K3s und alle Pods und löscht den lokalen Datenspeicher, Daten lokaler persistenter Volumes, Knotenkonfiguration und die Werkzeuge.
- **Vertrauliche Dateien:** `k3s.yaml` und `node-token` gewähren Zugang zum Cluster beziehungsweise das Hinzufügen von Knoten.
- **Ressourcen:** Ein laufender Cluster belegt dauerhaft Speicher und CPU.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `k3s: command not found` | Nicht installiert. | Installation laut Schnellstart. |
| `permission denied` beim Lesen von `k3s.yaml` | Datei nur für Root lesbar. | `sudo k3s kubectl` verwenden. **Prüfpunkt:** Standardrechte nicht geprüft. |
| Agent tritt nicht bei | Falsche `K3S_URL`, falsches Token, Port 6443 blockiert. | Token und Erreichbarkeit prüfen. |
| Knoten mit gleichem Namen | Hostnamen nicht eindeutig. | `K3S_NODE_NAME` setzen. |
| Pods ohne Netzwerk | Firewall blockiert Clusterverkehr. | Firewall-Regeln laut Dokumentation anpassen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Nur auf einem eigenen Testrechner oder in einer virtuellen Maschine** ausprobieren.
2. **Installationsskript vorher lesen.**
3. **Für reine Lernzwecke** `kind` oder `minikube` erwägen; sie lassen sich leichter vollständig entfernen.
4. **`k3s.yaml` und `node-token` schützen.**
5. **Vor der Deinstallation eine zum Datenspeicher passende Sicherung erstellen und die Wiederherstellung planen.** `k3s etcd-snapshot` gilt nur für eingebettetes etcd. Für SQLite nennt die [offizielle Sicherungsanleitung](https://docs.k3s.io/datastore/backup-restore) das Verzeichnis `/var/lib/rancher/k3s/server/db/`; externe Datenbanken benötigen ihr eigenes Sicherungsverfahren. Zusätzlich das Server-Token unter `/var/lib/rancher/k3s/server/token` vertraulich sichern: Es wird zur Wiederherstellung benötigt. Daten persistenter Volumes gesondert sichern. Dieser Sicherungs- und Wiederherstellungsablauf wurde hier nicht praktisch geprüft.

### Prüfstand

- **Geprüfte Version:** keine; K3s ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): K3s-Startseite (Bestandteile), Schnellstart (Installation, Pfade, Agent-Beitritt), CLI-Werkzeuge (Unterbefehle) und Deinstallation (Datenverlust).
- **Nicht geprüft:** Installation, alle Aufrufe, Server-/Agent-Optionen, Firewall-Verhalten, Rechte von `k3s.yaml`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kubectl` | Steuert den Cluster; bei K3s eingebaut. |
| `crictl`, `ctr` | Diagnose der Laufzeit; bei K3s eingebaut. |
| `kind`, `minikube` | Andere lokale Kubernetes-Umgebungen. |
| `helm` | Installiert Anwendungen in den Cluster. |
| `systemctl status k3s` | Dienststatus. **Prüfpunkt:** Dienstname laut Skript nicht geprüft. |

Ausgangseintrag: Datensatz 142 in `index.json` (`k3s`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Root-Angabe und Risikostufe wurden korrigiert, weil K3s als privilegierter Dienst Netzwerk und Daten des Systems verändert. Der Hilfe-Platzhalter wurde durch Bestandteile, Unterbefehle, Installationsfolgen und Deinstallationsrisiken ersetzt.
