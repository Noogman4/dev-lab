---
id: "minikube"
name: "minikube"
command: "minikube"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "kubernetes", "test", "entwicklung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 145
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# minikube – Lokalen Kubernetes-Cluster für Entwicklung und Tests betreiben

## 1. Kurzbeschreibung

`minikube` startet einen **lokalen Kubernetes-Cluster** auf dem eigenen Rechner – wahlweise in einem Container oder in einer virtuellen Maschine. Es ist für Lernen, Entwicklung und Tests gedacht und bringt Zusatzfunktionen wie Erweiterungen („addons“), ein Web-Dashboard und den Zugriff auf Dienste mit.

**Root-Rechte sind mit den empfohlenen Treibern nicht nötig.** `minikube` braucht laut [Schnellstart](https://minikube.sigs.k8s.io/docs/start/) einen Container- oder VM-Verwalter wie Docker, Podman, KVM, QEMU oder VirtualBox. Dessen Rechte gelten: Mit Docker bedeutet das Root oder die Gruppe `docker`. Der Treiber `none` (direkt auf dem Host) braucht laut [Dokumentation des none-Treibers](https://minikube.sigs.k8s.io/docs/drivers/none/) für `start` Root-Rechte und verringert die Sicherheit.

Auf dem geprüften System ist `minikube` nicht installiert.

## 2. Was macht der Befehl?

`minikube start` legt einen Cluster-Knoten mit dem gewählten Treiber an, installiert Kubernetes darin und richtet einen Kontext in der kubeconfig ein. Laut Schnellstart sind Mindestvoraussetzungen:

- 2 CPUs oder mehr,
- 2 GB freier Arbeitsspeicher,
- 20 GB freier Plattenplatz,
- Internetverbindung,
- ein Container- oder VM-Verwalter.

### Treiber unter Linux

Laut [Treiberübersicht](https://minikube.sigs.k8s.io/docs/drivers/):

| Treiber | Art | Einordnung laut Dokumentation |
| --- | --- | --- |
| `docker` | Container | bevorzugt |
| `kvm2` | VM | bevorzugt |
| `virtualbox` | VM | – |
| `qemu` | VM | – |
| `podman` | Container | experimentell |
| `none` | direkt auf dem Host | nur für fortgeschrittene Nutzer |
| `ssh` | entfernter Rechner | – |

### Profile

Mit `-p NAME` lassen sich mehrere Cluster („Profile“) parallel betreiben, etwa mit unterschiedlichen Kubernetes-Versionen.

## 3. Syntax

```text
minikube BEFEHL [OPTIONEN]
```

```bash
minikube start
minikube status
minikube kubectl -- get pods -A
minikube stop
minikube delete
```

Das bisherige NetMon-Beispiel `minikube --help` zeigt die Hilfe. Der Platzhalter `minikube [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Befehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `start` | Cluster anlegen bzw. starten. | Lädt beim ersten Mal große Images. |
| `start --driver=docker` | Treiber festlegen. | Sonst automatische Wahl. **Prüfpunkt:** Optionsname nicht in den gelesenen Seiten bestätigt. |
| `start -p NAME --kubernetes-version=V` | Weiteres Profil mit bestimmter Version. | Laut Schnellstart nur die drei neuesten Minor-Versionen. |
| `status` | Zustand anzeigen. | Nur lesend. |
| `pause`, `unpause` | Kubernetes anhalten, ohne Anwendungen zu beenden. | – |
| `stop` | Cluster anhalten. | Daten bleiben erhalten. |
| `delete` | Cluster löschen. | Daten im Cluster gehen verloren. |
| `delete --all` | Alle minikube-Cluster löschen. | – |
| `kubectl -- ...` | Passendes `kubectl` über minikube. | Doppelstrich trennt die Argumente. |
| `dashboard` | Web-Oberfläche öffnen. | – |
| `service NAME` | Dienst im Browser öffnen oder Adresse anzeigen. | – |
| `addons list`, `addons enable NAME` | Erweiterungen anzeigen und aktivieren. | Etwa `ingress`. |
| `config set memory WERT` | Vorgabe für Arbeitsspeicher setzen. | Laut Schnellstart Neustart nötig. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen Cluster starten, eine Testanwendung ansehen und den Cluster wieder entfernen. Voraussetzung: `minikube` und Docker (oder ein anderer Treiber). Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Starten

```bash
minikube start
```

### Schritt 2: Zustand prüfen

```bash
minikube status
minikube kubectl -- get pods -A
```

Die Systempods im Namespace `kube-system` sollten laufen.

### Schritt 3: Testanwendung

```bash
minikube kubectl -- create deployment hallo --image=nginx:stable
minikube kubectl -- expose deployment hallo --type=NodePort --port=80
minikube service hallo --url
```

Die letzte Zeile gibt eine lokale Adresse aus, unter der die Anwendung erreichbar ist.

### Schritt 4: Aufräumen

```bash
minikube delete
```

## 6. Typische Anwendungsfälle

- **Kubernetes lernen** mit Dashboard und Erweiterungen.
- **Anwendungen lokal testen,** bevor sie in einen echten Cluster gehen.
- **Mehrere Kubernetes-Versionen** über Profile vergleichen.
- **Ingress und andere Erweiterungen** ausprobieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Ressourcenverbrauch:** Mindestens 2 GB RAM und 20 GB Platz; dauerhaft laufende Cluster belasten den Rechner.
- **Treiber `none`:** Laut Dokumentation verringerte Sicherheit, verwirrendes Rechtemodell (teils Root, teils Benutzer) und nur für Fortgeschrittene. Auf Arbeitsrechnern meiden.
- **Laufzeitrechte:** Mit Docker gelten die Root-gleichen Rechte der Gruppe `docker`.
- **kubeconfig-Änderung:** `start` setzt den aktuellen kubectl-Kontext; spätere `kubectl`-Befehle treffen dann den lokalen Cluster – nach `delete` womöglich einen anderen.
- **Datenverlust:** `delete` und `delete --all` entfernen Cluster samt Inhalten.
- **Netzwerk:** VM-Treiber legen virtuelle Netzwerke an. **Prüfpunkt:** Zusammenspiel mit VPN- oder Firewall-Regeln nicht geprüft.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `minikube: command not found` | Nicht installiert. | Installation laut Schnellstart. |
| Kein Treiber gefunden | Weder Docker noch VM-Verwalter verfügbar. | Treiber installieren. |
| Zu wenig Speicher | Weniger als die Mindestwerte. | `config set memory`, andere Programme schließen. |
| Rechtefehler bei Docker | Kein Zugriff auf den Docker-Socket. | Siehe `docker`. |
| Falscher Cluster bei `kubectl` | Kontext gewechselt. | `kubectl config current-context`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Treiber `docker` oder `kvm2`,** nicht `none`.
2. **Profile benennen** und nicht benötigte löschen.
3. **`minikube stop`** statt laufen lassen, wenn du ihn nicht brauchst.
4. **Vor `kubectl`-Befehlen den Kontext prüfen.**

### Prüfstand

- **Geprüfte Version:** keine; `minikube` ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): minikube-Schnellstart (Voraussetzungen, Befehle zur Verwaltung), Treiberübersicht und Seite zum Treiber `none` (Sicherheit, Rechte).
- **Nicht geprüft:** alle Aufrufe, Treiberwahl, Netzwerkfolgen, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kubectl` | Steuert den Cluster. |
| `kind` | Lokale Cluster nur in Containern. |
| `k3s` | Leichtgewichtige Distribution als Systemdienst. |
| `docker`, `podman` | Container-Treiber. |
| `helm` | Anwendungen im Cluster installieren. |

Ausgangseintrag: Datensatz 145 in `index.json` (`minikube`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Voraussetzungen, Treiber mit Sicherheitseinordnung, Verwaltungsbefehle und einen Testablauf ersetzt.
