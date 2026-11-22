---
id: "containerd"
name: "containerd"
command: "containerd"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "laufzeit", "dienst", "oci"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 136
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# containerd – Hintergrunddienst für Container-Laufzeit

## 1. Kurzbeschreibung

`containerd` ist eine **Container-Laufzeitumgebung**, die als Hintergrunddienst (Daemon) läuft. Sie lädt Images, verwaltet Snapshots und startet Container über eine Low-Level-Laufzeit wie `runc`. Docker, Kubernetes (über die CRI-Schnittstelle), `nerdctl` und `ctr` sprechen mit diesem Dienst.

Der Befehl `containerd` **startet den Dienst selbst** oder gibt Konfigurationsinformationen aus. Für das Verwalten von Containern ist er nicht gedacht; dafür gibt es Clients wie `ctr`, `nerdctl` oder `crictl`.

**Root-Rechte sind für den normalen Systemdienst nötig.** Laut [Konfigurationsmanpage](https://manpages.debian.org/trixie/containerd/containerd-config.toml.5.en.html) liegen seine Daten unter `/var/lib/containerd`, der Zustand unter `/run/containerd` und der Steuersocket unter `/run/containerd/containerd.sock`. In der Praxis startet ein Dienstverwalter wie systemd `containerd`, nicht ein Benutzer von Hand. **Prüfpunkt:** Ein rootless-Betrieb ist mit Zusatzwerkzeugen möglich, wurde aber nicht anhand von Quellen geprüft.

Auf dem geprüften System ist `containerd` nicht installiert.

## 2. Was macht der Befehl?

Laut [Debian-Manpage zu containerd](https://manpages.debian.org/trixie/containerd/containerd.8.en.html):

- Ohne Unterbefehl startet `containerd` den **Dienst im Vordergrund**.
- Ohne eigene Konfiguration gilt eine eingebaute Standardkonfiguration; die Datei liegt standardmäßig unter `/etc/containerd/config.toml`.
- `containerd config default` gibt die Standardkonfiguration aus, die man als Grundlage einer eigenen Datei verwenden kann.
- `containerd config dump` zeigt die tatsächlich wirksame Konfiguration einschließlich eingebundener Teildateien.
- `publish` und `oci-hook` sind interne Hilfsbefehle für Ereignisse und OCI-Hooks.

Der Dienst stellt eine **gRPC-Schnittstelle** über den Socket bereit. Wer auf diesen Socket schreiben darf, kann Container mit beliebigen Rechten starten.

## 3. Syntax

```text
containerd [GLOBALE_OPTIONEN] [BEFEHL] [BEFEHLSOPTIONEN]
```

```bash
containerd config default > config.toml
sudo containerd config dump
systemctl status containerd
```

Das bisherige NetMon-Beispiel `containerd --help` zeigt die Hilfe; die Manpage nennt einen Hilfebefehl. Der Platzhalter `containerd [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--config`, `-c DATEI` | Konfigurationsdatei. | Standard `/etc/containerd/config.toml`. |
| `--address`, `-a ADRESSE` | Adresse des gRPC-Dienstes. | Standard laut Konfigurationsmanpage `/run/containerd/containerd.sock`. |
| `--root VERZ` | Datenordner. | Standard `/var/lib/containerd`. |
| `--state VERZ` | Zustandsordner. | Standard `/run/containerd`. |
| `--log-level`, `-l` | Protokollstufe `trace` bis `panic`. | Für Fehlersuche. |
| `config default` | Standardkonfiguration ausgeben. | Nur Ausgabe, keine Änderung. |
| `config dump` | Wirksame Konfiguration ausgeben. | Liest vorhandene Konfiguration. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die Standardkonfiguration ansehen und den Zustand des Dienstes prüfen, ohne etwas zu ändern. Das ist ein **Beispielszenario** und wurde nicht ausgeführt, weil `containerd` nicht installiert ist.

### Schritt 1: Läuft der Dienst?

```bash
systemctl status containerd
```

Zeigt, ob der Dienst aktiv ist, seit wann er läuft und die letzten Protokollzeilen. Das Lesen des Status braucht meist keine Root-Rechte.

### Schritt 2: Standardkonfiguration ansehen

```bash
uebung="$(mktemp -d -t netmon-containerd-XXXXXX)" || exit 1
containerd config default > "$uebung/default.toml"
less "$uebung/default.toml"
```

Die Ausgabe landet in einer eigenen Datei, nicht in `/etc`. **Prüfpunkt:** Ob `config default` ohne Root läuft, ist nicht geprüft.

### Schritt 3: Wirksame Konfiguration vergleichen

```bash
sudo containerd config dump > "$uebung/aktiv.toml"
diff "$uebung/default.toml" "$uebung/aktiv.toml"
```

`diff` zeigt, was gegenüber der Vorgabe geändert wurde.

### Schritt 4: Protokolle ansehen

```bash
journalctl -u containerd --since today
```

## 6. Typische Anwendungsfälle

- **Grundlage für Docker:** Docker nutzt containerd intern.
- **Kubernetes-Knoten:** containerd als CRI-Laufzeit, angesprochen über `crictl` und das Kubelet.
- **Konfiguration erstellen:** `containerd config default` als Ausgangspunkt für `/etc/containerd/config.toml`.
- **Fehlersuche:** Dienst mit höherer Protokollstufe im Vordergrund starten (nur auf Testsystemen).

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution` bestehen; Konfigurationsausgaben sind harmlos, Eingriffe in den laufenden Dienst nicht.

- **Zugriff auf den Socket = Root-Zugriff:** Wer Container starten kann, kann Host-Ordner einhängen und so das System übernehmen. Socket-Rechte nicht lockern.
- **Zweiter Dienst:** Ein von Hand gestartetes `containerd` neben dem Systemdienst kann um Socket und Ordner konkurrieren.
- **Neustart:** Ein Neustart des Dienstes kann je nach Konfiguration laufende Container und Kubernetes-Workloads beeinträchtigen. **Prüfpunkt:** Verhalten laufender Container bei Neustart nicht geprüft.
- **Konfigurationsfehler:** Eine fehlerhafte `config.toml` verhindert den Start; Docker oder Kubernetes fallen dann ebenfalls aus.
- **Speicherplatz:** Images und Snapshots unter `/var/lib/containerd` können sehr groß werden.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `containerd: command not found` | Nicht installiert. | Paket der Distribution (`containerd`) oder über Docker. |
| Fehler beim Öffnen von `/run/containerd/...` | Ohne Root gestartet oder Socket schon belegt. | Dienst über systemd verwalten. |
| Dienst startet nicht nach Konfigurationsänderung | Fehler in `config.toml`. | `journalctl -u containerd`; Datei mit der Vorgabe vergleichen. |
| Clients erreichen den Dienst nicht | Falscher Socket-Pfad oder fehlende Rechte. | Adresse im Client angeben, Rechte prüfen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`containerd` nicht von Hand starten,** sondern den Systemdienst verwenden.
2. **Konfigurationsausgaben in eigene Dateien** schreiben und prüfen.
3. **Vor Änderungen an `/etc/containerd/config.toml` sichern.**
4. **Für Container-Arbeit Clients nutzen** (`nerdctl`, `ctr`, `crictl`).
5. **Socket-Zugriff nur Verwaltungskonten** geben.

### Prüfstand

- **Geprüfte Version:** keine; `containerd` ist nicht installiert (kein Programm, kein Dienst, keine Datenordner).
- **Quellen gelesen:** Debian-Manpages `containerd(8)` und `containerd-config.toml(5)`, Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Rechtebedarf von `config default`, rootless-Betrieb, Verhalten bei Neustart.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ctr` | Einfacher Diagnose-Client von containerd. |
| `nerdctl` | Docker-ähnlicher Client für containerd. |
| `crictl` | Client für die CRI-Schnittstelle (Kubernetes). |
| `runc` | Low-Level-Laufzeit, die containerd zum Starten verwendet. |
| `docker` | Nutzt containerd als Unterbau. |
| `systemctl`, `journalctl` | Dienst steuern und Protokolle lesen. |

Ausgangseintrag: Datensatz 136 in `index.json` (`containerd`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert, weil der Dienst systemweite Ordner und Sockets verwendet. Der Hilfe-Platzhalter wurde durch die Rolle als Dienst, Konfigurationsbefehle, Standardpfade und Sicherheitsfolgen ersetzt.
