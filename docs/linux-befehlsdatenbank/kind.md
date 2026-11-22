---
id: "kind"
name: "kind"
command: "kind"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "kubernetes", "test", "entwicklung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 143
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# kind – Lokale Kubernetes-Cluster in Containern

## 1. Kurzbeschreibung

`kind` („Kubernetes in Docker“) startet **lokale Kubernetes-Cluster**, deren Knoten als Container laufen. Laut [kind-Projektseite](https://kind.sigs.k8s.io/) wurde es vor allem für Tests von Kubernetes selbst entwickelt, eignet sich aber auch für lokale Entwicklung und CI.

**Root-Rechte sind für `kind` selbst nicht nötig,** aber ein Zugriff auf eine Container-Laufzeit. Mit Docker heißt das: Root oder Mitglied der Gruppe `docker` (die laut Docker-Dokumentation Root-Niveau gewährt). Mit Podman oder nerdctl läuft `kind` laut [Schnellstart](https://kind.sigs.k8s.io/docs/user/quick-start/) standardmäßig rootless, braucht dann aber zusätzliche Einrichtung.

Auf dem geprüften System sind weder `kind` noch eine Container-Laufzeit installiert.

## 2. Was macht der Befehl?

`kind create cluster` startet einen oder mehrere Container mit einem vorgefertigten **Knoten-Image** (`kindest/node`) und richtet darin Kubernetes ein. Anschließend schreibt `kind` die Zugangsdaten in die kubeconfig, sodass `kubectl` den Cluster sofort ansprechen kann.

Laut Schnellstart:

- Standardname des Clusters ist `kind`; der kubectl-Kontext heißt dann `kind-kind`.
- Die kubeconfig liegt standardmäßig in `~/.kube/config`, sonst in den Dateien aus `KUBECONFIG`.
- `kind` erkennt Docker, Podman oder nerdctl automatisch; `KIND_EXPERIMENTAL_PROVIDER` wählt fest.
- Das Löschen eines nicht vorhandenen Clusters erzeugt absichtlich **keinen Fehler**.

## 3. Syntax

```text
kind BEFEHL [UNTERBEFEHL] [OPTIONEN]
```

```bash
kind create cluster
kind create cluster --name test --wait 5m
kind get clusters
kind load docker-image meine-app:1.0 --name test
kind delete cluster --name test
```

Das bisherige NetMon-Beispiel `kind --help` ist gültig; die Dokumentation nennt `kind help` und `kind --help`. Der Platzhalter `kind [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Befehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `create cluster` | Cluster anlegen. | Lädt beim ersten Mal ein großes Knoten-Image. |
| `--name NAME` | Clustername. | Kontext heißt `kind-NAME`. |
| `--image IMAGE` | Anderes Knoten-Image, etwa andere Kubernetes-Version. | Passende Images stehen in den Versionshinweisen der jeweiligen kind-Version. |
| `--wait DAUER` | Warten, bis die Steuerungsebene bereit ist. | Mit Einheit, z. B. `30s`, `5m`. |
| `--kubeconfig DATEI` | Nur diese kubeconfig verwenden. | Kein Zusammenführen mit anderen Dateien. |
| `get clusters` | Vorhandene kind-Cluster auflisten. | Nur lesend. |
| `delete cluster [--name NAME]` | Cluster löschen. | Ohne `--name` wird `kind` gelöscht. |
| `load docker-image IMAGE` | Lokales Image in die Knoten laden. | Spart den Umweg über eine Registry. |
| `version` | kind-Version. | – |
| `KIND_EXPERIMENTAL_PROVIDER` | Laufzeit festlegen: `docker`, `podman`, `nerdctl`. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen Testcluster starten, prüfen und vollständig entfernen. Voraussetzung: `kind`, `kubectl` und eine funktionierende Container-Laufzeit. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Cluster anlegen

```bash
kind create cluster --name uebung --wait 5m
```

`kind` lädt bei Bedarf das Knoten-Image, startet den Knoten-Container und meldet den neuen Kontext.

### Schritt 2: Prüfen

```bash
kind get clusters
kubectl cluster-info --context kind-uebung
kubectl get nodes --context kind-uebung
```

Der Knoten `uebung-control-plane` sollte `Ready` sein.

### Schritt 3: Eigenes Image verwenden

```bash
kind load docker-image meine-app:1.0 --name uebung
```

### Schritt 4: Entfernen

```bash
kind delete cluster --name uebung
```

Die Knoten-Container und der Kontext in der kubeconfig werden entfernt. **Prüfpunkt:** Ob heruntergeladene Knoten-Images im Speicher der Laufzeit bleiben, wurde nicht geprüft.

## 6. Typische Anwendungsfälle

- **Kubernetes lernen** ohne Cloud-Konto.
- **CI-Tests** mit einem echten Cluster pro Durchlauf.
- **Helm-Charts und Manifeste testen,** bevor sie in einen echten Cluster gehen.
- **Mehrere Kubernetes-Versionen** parallel mit `--image`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Rechte der Laufzeit:** Mit Docker laufen die Knoten-Container mit weitreichenden Rechten. Wer `kind` über Docker benutzt, hat ohnehin Root-gleiche Rechte.
- **kubeconfig wird verändert:** `create` und `delete` ändern `~/.kube/config`. Der aktuelle Kontext wechselt dabei; Folgebefehle mit `kubectl` können unerwartet den Testcluster treffen – oder nach dem Löschen wieder einen anderen. Vorher sichern.
- **Ressourcen:** Ein Cluster belegt mehrere Gigabyte Speicherplatz und spürbar Arbeitsspeicher.
- **Stilles Löschen:** `delete cluster` ohne `--name` löscht den Cluster `kind`; ein Tippfehler im Namen bleibt ohne Fehlermeldung.
- **Nicht für Produktion:** Laut Projekt für Tests und Entwicklung gedacht.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `kind: command not found` | Nicht installiert. | Installation laut Projektseite. |
| Keine Laufzeit gefunden | Docker, Podman oder nerdctl fehlen oder sind nicht erreichbar. | Laufzeit installieren und Rechte prüfen. |
| Rechtefehler am Docker-Socket | Kein Zugriff auf Docker. | Siehe `docker`. |
| Cluster mit Podman nicht voll funktionsfähig | Rootless benötigt Zusatzeinrichtung. | Anleitung „Rootless“ der kind-Dokumentation. |
| `kubectl` spricht falschen Cluster an | Kontext gewechselt. | `kubectl config current-context`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Cluster immer benennen** und beim Löschen `--name` angeben.
2. **kubeconfig vorher sichern** oder `--kubeconfig` mit eigener Datei nutzen.
3. **`--context` bei `kubectl`** ausdrücklich angeben.
4. **Nicht benötigte Cluster löschen,** um Speicher freizugeben.

### Prüfstand

- **Geprüfte Version:** keine; `kind` ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): kind-Projektseite (Zweck) und Schnellstart (Erstellen, Laufzeiterkennung, kubeconfig, Löschen, Image-Laden).
- **Nicht geprüft:** alle Aufrufe, rootless-Betrieb, Verbleib der Knoten-Images, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kubectl` | Steuert den Cluster. |
| `minikube` | Andere lokale Kubernetes-Umgebung, auch mit virtuellen Maschinen. |
| `k3s` | Leichtgewichtige Distribution, direkt als Systemdienst. |
| `docker`, `podman`, `nerdctl` | Laufzeiten für die Knoten-Container. |
| `helm` | Anwendungen im Testcluster installieren. |

Ausgangseintrag: Datensatz 143 in `index.json` (`kind`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, Laufzeitvoraussetzungen, Befehle mit kubeconfig-Wirkung und einen Testablauf ersetzt.
