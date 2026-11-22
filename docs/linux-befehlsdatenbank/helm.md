---
id: "helm"
name: "helm"
command: "helm"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "kubernetes", "paketverwaltung", "charts"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 141
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# helm – Paketverwaltung für Kubernetes-Anwendungen

## 1. Kurzbeschreibung

`helm` ist der **Paketmanager für Kubernetes**. Anwendungen werden als **Charts** verteilt: Pakete aus Vorlagen für Kubernetes-Objekte (Deployments, Dienste, Konfigurationen) und einstellbaren Werten. `helm` installiert ein Chart als **Release** in einen Cluster, aktualisiert es, rollt es zurück oder entfernt es.

**Root-Rechte auf dem eigenen Rechner sind nicht nötig.** `helm` arbeitet mit der Kubernetes-Konfiguration des Benutzers (kubeconfig). Was erlaubt ist, entscheiden die Rechte dieses Kontos im **Cluster**.

Grundlage ist die [Helm-Befehlsreferenz](https://helm.sh/docs/helm/helm/) in der Fassung für Helm 4.3.1 sowie die Seite zu [`helm install`](https://helm.sh/docs/helm/helm_install/). Für Debian trixie gibt es keine Manpage. Auf dem geprüften System ist `helm` nicht installiert.

## 2. Was macht der Befehl?

Typischer Ablauf laut Referenz: Charts suchen (`search`), herunterladen und ansehen (`pull`, `show`), installieren (`install`), Releases auflisten (`list`).

Wichtige Unterbefehle:

| Befehl | Wirkung im Cluster |
| --- | --- |
| `repo add/update/list/remove` | Lokale Liste der Chart-Quellen; keine Clusteränderung. |
| `search`, `show`, `pull` | Charts finden, Informationen ansehen, herunterladen; keine Clusteränderung. |
| `template`, `lint` | Vorlagen lokal rendern bzw. prüfen; keine Clusteränderung. |
| `list`, `status`, `history`, `get` | Releases ansehen; nur lesend. |
| `install` | Neues Release anlegen. |
| `upgrade` | Release aktualisieren. |
| `rollback` | Auf frühere Revision zurück. |
| `uninstall` | Release und seine Objekte entfernen. |
| `test` | Tests eines Charts ausführen. |
| `plugin` | Erweiterungen verwalten. |

### Speicherorte

Laut Referenz legt Helm unter Linux Daten unter `~/.cache/helm`, `~/.config/helm` und `~/.local/share/helm` ab (änderbar über `HELM_CACHE_HOME`, `HELM_CONFIG_HOME`, `HELM_DATA_HOME` oder XDG-Variablen). Dazu gehören `repositories.yaml` und die Registry-Anmeldung `registry/config.json`. Den Zustand eines Releases speichert Helm im Cluster selbst; der Treiber ist mit `HELM_DRIVER` wählbar (`configmap`, `secret`, `memory`, `sql`).

## 3. Syntax

```text
helm BEFEHL [ARGUMENTE] [OPTIONEN]
```

```bash
helm repo add beispiel https://charts.example.org
helm search repo webserver
helm install meinweb beispiel/webserver -n web --create-namespace
helm list -A
helm uninstall meinweb -n web
```

Das bisherige NetMon-Beispiel `helm --help` ist gültig (`-h`, `--help` laut Referenz). Der Platzhalter `helm [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Optionen laut Referenz:

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--kube-context NAME` | kubeconfig-Kontext wählen. | Schützt vor Aktionen im falschen Cluster. |
| `--kubeconfig DATEI` | Andere kubeconfig-Datei. | – |
| `-n`, `--namespace NAME` | Namespace für diese Anfrage. | Releases sind namespace-gebunden. |
| `--debug` | Ausführliche Ausgaben. | – |
| `--kube-insecure-skip-tls-verify` | Zertifikatsprüfung abschalten. | Laut Referenz unsicher. |
| `--repository-config`, `--registry-config` | Andere Konfigurationsdateien. | – |

Optionen von `helm install` laut Referenz:

| Option | Bedeutung |
| --- | --- |
| `-f`, `--values DATEI` | Werte aus YAML-Datei. |
| `--set k=v` | Einzelne Werte setzen. |
| `--version` | Chart-Version festlegen; ohne Angabe die neueste. |
| `--create-namespace` | Namespace anlegen, falls er fehlt. |
| `--dry-run=client` / `--dry-run=server` | Nur simulieren (lokal bzw. auf dem Server). |
| `--wait` | Auf Bereitschaft der Objekte warten. |
| `--rollback-on-failure` | Bei Fehlschlag automatisch zurückrollen. |

**Versionshinweis:** Die Referenz beschreibt Helm 4. **Prüfpunkt:** Ältere Helm-3-Versionen verwenden für einige dieser Funktionen andere Optionsnamen und Werte (etwa beim automatischen Zurückrollen); das wurde nicht anhand einer Helm-3-Quelle geprüft. Optionen deshalb mit `helm install --help` der installierten Version abgleichen.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein Chart zuerst lokal prüfen, dann in einem Test-Namespace installieren und wieder entfernen. Das braucht einen Kubernetes-Cluster und Netzzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Ziel-Cluster prüfen

```bash
kubectl config current-context
```

### Schritt 2: Chart-Quelle hinzufügen und Werte ansehen

`charts.example.org` und `beispiel/webserver` sind Platzhalter für eine vertrauenswürdige Chart-Quelle.

```bash
helm repo add beispiel https://charts.example.org
helm show values beispiel/webserver > werte.yaml
```

`werte.yaml` zeigt alle einstellbaren Werte; anpassen statt viele `--set`.

### Schritt 3: Lokal rendern

```bash
helm template meinweb beispiel/webserver -f werte.yaml > vorschau.yaml
```

`vorschau.yaml` enthält die Kubernetes-Objekte, die angelegt würden. Nichts wird im Cluster verändert.

### Schritt 4: Installieren

```bash
helm install meinweb beispiel/webserver -f werte.yaml -n test --create-namespace --version 15.0.0
helm status meinweb -n test
```

Die Version ist nur ein Platzhalter; mit `helm search repo webserver --versions` eine vorhandene wählen.

### Schritt 5: Entfernen

```bash
helm uninstall meinweb -n test
```

## 6. Typische Anwendungsfälle

- **Fertige Anwendungen** (Datenbanken, Ingress-Controller, Überwachung) installieren.
- **Eigene Anwendungen** als Charts paketieren (`create`, `package`, `push`).
- **Aktualisierungen mit Rückweg:** `upgrade` und `rollback`.
- **Prüfungen in CI:** `lint` und `template`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Clusterweite Wirkung:** Charts können Rollen, Berechtigungen, CRDs und Dienste anlegen, die weit über die Anwendung hinausgehen. Vorher mit `template` prüfen.
- **Fremde Charts** enthalten Images und Vorlagen Dritter. Nur vertrauenswürdige Quellen, feste Versionen.
- **`uninstall`** entfernt die Objekte des Releases; Daten in persistenten Volumes können je nach Chart verloren gehen oder verwaist zurückbleiben.
- **Geheimnisse in Werten:** `--set passwort=...` erscheint im Shell-Verlauf; Werte werden im Release-Zustand gespeichert.
- **Falscher Kontext oder Namespace:** Ohne `--kube-context` und `-n` gilt die aktuelle kubeconfig-Auswahl.
- **Plugins** führen fremden Code mit deinen Cluster-Rechten aus.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `helm: command not found` | Nicht installiert. | Offizielle Installation. |
| Verbindungsfehler zum Cluster | kubeconfig fehlt oder falscher Kontext. | `kubectl config get-contexts`. |
| Release-Name bereits vergeben | Gleicher Name im Namespace. | Anderen Namen oder `upgrade --install`. **Prüfpunkt:** nicht in gelesenen Quellen geprüft. |
| Chart nicht gefunden | Repository fehlt oder veraltet. | `helm repo update`. |
| `forbidden` | Rechte im Cluster fehlen. | Rolle prüfen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vor jeder Installation `helm template` oder `--dry-run`.**
2. **Kontext und Namespace ausdrücklich angeben.**
3. **Chart-Versionen festlegen.**
4. **Werte in Dateien statt `--set`,** Geheimnisse über Kubernetes-Secrets.
5. **Eigener Test-Namespace** für Versuche.

### Prüfstand

- **Geprüfte Version:** keine; `helm` ist nicht installiert, keine Debian-Manpage vorhanden.
- **Quellen gelesen** (Abruf 2026-11-13): Helm-Referenz `helm` (Helm 4.3.1: Unterbefehle, globale Optionen, Umgebungsvariablen, Speicherorte) und `helm install` (Installationsoptionen).
- **Nicht geprüft:** alle Aufrufe, Helm-3-Unterschiede im Detail, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kubectl` | Grundwerkzeug für Kubernetes; Helm nutzt dieselbe kubeconfig. |
| `kind`, `minikube`, `k3s` | Lokale Test-Cluster für Helm-Versuche. |
| `docker`, `podman` | Bauen die Images, die Charts verwenden. |

Ausgangseintrag: Datensatz 141 in `index.json` (`helm`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Begriffe (Chart, Release), Unterbefehle nach Wirkung, Speicherorte, Optionen von Helm 4 und einen Ablauf mit lokaler Prüfung ersetzt.
