---
id: "kubectl"
name: "kubectl"
command: "kubectl"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "kubernetes", "cluster", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 144
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# kubectl – Kubernetes-Cluster über die Kommandozeile steuern

## 1. Kurzbeschreibung

`kubectl` ist das offizielle Kommandozeilenwerkzeug für **Kubernetes**. Es spricht über die Kubernetes-API mit der Steuerungsebene eines Clusters und kann Ressourcen wie Pods, Deployments, Dienste und Konfigurationen anzeigen, anlegen, ändern und löschen.

**Root-Rechte auf dem eigenen Rechner sind nicht nötig.** `kubectl` liest laut [Kubernetes-Dokumentation](https://kubernetes.io/docs/reference/kubectl/) die Datei `~/.kube/config` (oder die Dateien aus `KUBECONFIG` beziehungsweise `--kubeconfig`). Was erlaubt ist, entscheiden die Zugangsdaten darin und die Rollen im **Cluster**.

Grundlagen sind die Kubernetes-Dokumentation und die [Debian-Manpage zu kubectl](https://manpages.debian.org/trixie/kubectl/kubectl.1.en.html) (kubectl 1.32.3). Auf dem geprüften System ist `kubectl` nicht installiert.

## 2. Was macht der Befehl?

Die Grundsyntax laut Dokumentation:

```text
kubectl [BEFEHL] [TYP] [NAME] [OPTIONEN]
```

- `BEFEHL`: Aktion wie `get`, `describe`, `create`, `delete`.
- `TYP`: Ressourcentyp; Groß- und Kleinschreibung egal, Einzahl, Mehrzahl oder Kurzform (`pod`, `pods`, `po`).
- `NAME`: Name der Ressource; ohne Name gilt der Befehl für alle Ressourcen des Typs.

Die Manpage gliedert die Befehle in Gruppen. Für die Sicherheit entscheidend ist, ob ein Befehl liest oder verändert:

| Wirkung | Befehle |
| --- | --- |
| Lesen | `get`, `describe`, `logs`, `events`, `explain`, `top`, `api-resources`, `cluster-info`, `diff`, `auth can-i`, `version` |
| Ändern | `apply`, `create`, `edit`, `patch`, `replace`, `scale`, `rollout`, `label`, `annotate`, `set`, `autoscale` |
| Löschen | `delete` |
| Eingreifen in laufende Container | `exec`, `attach`, `cp`, `debug`, `port-forward` |
| Knotenverwaltung | `cordon`, `uncordon`, `drain`, `taint` |
| Lokale Konfiguration | `config` (ändert die kubeconfig) |

Läuft `kubectl` selbst in einem Pod, verwendet es laut Dokumentation automatisch das Dienstkonto des Pods.

## 3. Syntax

```text
kubectl BEFEHL [TYP] [NAME] [-n NAMESPACE] [--context KONTEXT] [OPTIONEN]
kubectl BEFEHL --help
kubectl options
```

```bash
kubectl get pods -n kube-system
kubectl describe deployment web
kubectl logs -f deployment/web
kubectl apply -f manifest.yaml
```

Das bisherige NetMon-Beispiel `kubectl --help` ist gültig; die Manpage nennt `kubectl BEFEHL --help` und `kubectl options` für globale Optionen. Der Platzhalter `kubectl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--context NAME` | Kontext aus der kubeconfig wählen. | Schützt vor Befehlen im falschen Cluster. |
| `-n NAME`, `--namespace NAME` | Namespace. | Ohne Angabe gilt der Namespace des Kontexts. |
| `-A`, `--all-namespaces` | Über alle Namespaces (bei `get`). | Nur lesend sinnvoll. |
| `-o wide/yaml/json` | Ausgabeformat. | `-o yaml` zeigt die vollständige Ressource. |
| `-f DATEI` | Ressourcen aus Datei. | Bei `apply`, `create`, `delete`, `get`. |
| `--dry-run=client/server` | Nur simulieren. | Vor `apply` oder `create`. **Prüfpunkt:** Werte je Version prüfen. |
| `-l SCHLÜSSEL=WERT` | Nach Labels auswählen. | Achtung bei `delete`. |
| `--kubeconfig DATEI` | Andere kubeconfig. | – |
| `config current-context` / `get-contexts` / `use-context` | Kontexte anzeigen bzw. wechseln. | `use-context` ändert die Datei. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, in welchem Cluster man arbeitet, eine Änderung vorab vergleichen und dann anwenden. Das braucht einen Cluster (etwa mit `kind` oder `minikube`); es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Kontext prüfen

```bash
kubectl config current-context
kubectl get nodes
```

### Schritt 2: Rechte prüfen

```bash
kubectl auth can-i create deployments -n test
```

Antwortet `yes` oder `no`, ohne etwas zu verändern.

### Schritt 3: Änderung vergleichen

```bash
kubectl diff -f manifest.yaml -n test
```

`diff` zeigt den Unterschied zwischen laufender und gewünschter Konfiguration.

### Schritt 4: Anwenden und beobachten

```bash
kubectl apply -f manifest.yaml -n test
kubectl rollout status deployment/web -n test
kubectl get pods -n test
```

## 6. Typische Anwendungsfälle

- **Zustand prüfen:** `get`, `describe`, `events`, `logs`.
- **Anwendungen ausrollen:** `apply -f` mit versionierten Manifesten.
- **Fehlersuche:** `exec`, `debug`, `port-forward`.
- **Skalieren und zurückrollen:** `scale`, `rollout undo`.
- **Wartung:** Knoten mit `drain` leeren und mit `uncordon` wieder freigeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`; sie gilt für den lesenden Normalfall. Verändernde Befehle können erhebliche Folgen haben:

- **Falscher Kontext:** Der häufigste schwere Fehler. Ein `delete` im Produktionscluster statt im Testcluster. Immer `--context` oder einen deutlich sichtbaren Prompt verwenden.
- **Breites Löschen:** `kubectl delete pods --all`, `delete namespace NAME` oder `-l` mit zu allgemeinem Selektor entfernen viele Objekte auf einmal. Ein gelöschter Namespace nimmt alles darin mit.
- **`drain`** verdrängt Pods vom Knoten; ohne genügende Kapazität fallen Dienste aus.
- **`exec` und `cp`** greifen in laufende Container ein und können Daten verändern.
- **kubeconfig schützen:** Die Datei enthält Zertifikate oder Tokens. Wer sie besitzt, hat die Rechte des darin hinterlegten Kontos.
- **Secrets im Klartext:** `kubectl get secret -o yaml` zeigt base64-kodierte und damit leicht lesbare Geheimnisse.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Verbindung zum Server abgelehnt | Keine oder falsche kubeconfig, Cluster aus. | `kubectl config view`, Kontext prüfen. |
| `Forbidden` | Rolle erlaubt die Aktion nicht. | `kubectl auth can-i ...`. |
| `NotFound` | Falscher Namespace oder Name. | `-n` prüfen, `get` ohne Name. |
| Versionswarnung zwischen Client und Server | Zu großer Versionsabstand. | Passende kubectl-Version verwenden. |
| `error: the server doesn't have a resource type` | Tippfehler oder CRD fehlt. | `kubectl api-resources`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vor jeder Änderung `config current-context`.**
2. **`diff` und `--dry-run` vor `apply`.**
3. **Mit `get`, `describe` und `logs` beginnen.**
4. **`--context` und `-n` ausdrücklich angeben,** besonders in Skripten.
5. **Getrennte kubeconfig-Dateien** für Test und Produktion.

### Prüfstand

- **Geprüfte Version:** keine; `kubectl` ist nicht installiert. Die Debian-Manpage beschreibt kubectl 1.32.3.
- **Quellen gelesen** (Abruf 2026-11-13): Kubernetes-Dokumentation „Command line tool (kubectl)“ (Syntax, kubeconfig, Pod-Betrieb) und Debian-Manpage `kubectl(1)` (Befehlsgruppen).
- **Nicht geprüft:** alle Aufrufe, `--dry-run`-Werte, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `helm` | Paketverwaltung über dieselbe kubeconfig. |
| `kind`, `minikube`, `k3s` | Lokale oder leichte Cluster. |
| `crictl` | Diagnose direkt auf einem Knoten. |
| `kustomize` | Manifeste zusammensetzen; in `kubectl` eingebaut (`kubectl kustomize`). |

Ausgangseintrag: Datensatz 144 in `index.json` (`kubectl`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Syntax, Befehle nach Wirkung, kubeconfig-Logik, Optionen und einen Ablauf mit Vorabvergleich ersetzt.
