---
id: "runc"
name: "runc"
command: "runc"
category: "Container"
language: "de"
root_required: true
risk_level: "caution"
tags: ["container", "oci", "laufzeit", "low-level"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 149
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# runc – OCI-Container auf unterster Ebene starten

## 1. Kurzbeschreibung

`runc` ist eine **Low-Level-Container-Laufzeit**: das Programm, das einen Container tatsächlich als Linux-Prozess mit Namensräumen, cgroups und eingeschränkten Rechten startet. Laut [Debian-Manpage zu runc](https://manpages.debian.org/trixie/runc/runc.8.en.html) ist es eine konforme Umsetzung der Spezifikation der Open Container Initiative (OCI). Docker, containerd und andere Werkzeuge rufen `runc` im Hintergrund auf; Benutzer verwenden es selten direkt.

**Root-Rechte sind im Normalfall nötig.** `runc` legt Namensräume, cgroups und Einhängungen an. Laut Manpage gibt es einen **Rootless-Modus** (Vorgabe: automatisch erkannt), für den mit `runc spec --rootless` eine passende Konfiguration erzeugt wird.

Auf dem geprüften System ist `runc` nicht installiert.

## 2. Was macht der Befehl?

`runc` arbeitet mit **Bundles**: Ein Bundle ist ein Ordner mit

- einer Spezifikationsdatei `config.json` (Befehl, Umgebungsvariablen, Einhängungen, Namensräume, Rechte, Ressourcen) und
- einem Wurzeldateisystem, meist `rootfs/`.

`runc` lädt **keine Images** und kennt keine Registries. Diese Aufgaben übernehmen höhere Werkzeuge wie containerd, Podman oder Docker.

Befehle laut Manpage:

| Befehl | Wirkung |
| --- | --- |
| `spec` | Neue `config.json` als Ausgangspunkt erzeugen. |
| `run ID` | Container erzeugen und starten. |
| `create ID`, `start ID` | Erzeugen und getrennt davon starten. |
| `list` | Mit `runc` gestartete Container auflisten. |
| `state ID`, `ps ID`, `events ID` | Zustand, Prozesse, Ereignisse. |
| `exec ID BEFEHL` | Weiteren Prozess im Container starten. |
| `kill ID [SIGNAL]` | Signal an den Hauptprozess senden. |
| `pause`, `resume` | Prozesse anhalten bzw. fortsetzen. |
| `update ID` | Ressourcenlimits ändern. |
| `checkpoint`, `restore` | Zustand sichern und wiederherstellen (mit CRIU). |
| `delete ID` | Ressourcen eines Containers freigeben. |

Der Container-Zustand liegt laut Manpage unter `/run/runc` beziehungsweise rootless unter `$XDG_RUNTIME_DIR/runc`.

## 3. Syntax

```text
runc [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] [ARGUMENTE]
runc run [-b BUNDLE] CONTAINER-ID
```

```bash
runc spec
sudo runc run test1
sudo runc list
sudo runc delete test1
```

Das bisherige NetMon-Beispiel `runc --help` ist gültig (`--help`, `-h` laut Manpage). Der Platzhalter `runc [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Optionen müssen laut Manpage vor dem Befehl stehen:

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--root PFAD` | Ordner für Containerzustände. | Sollte auf tmpfs liegen; Standard `/run/runc`. |
| `--rootless true/false/auto` | Rootless-Modus steuern. | Standard `auto`. |
| `--systemd-cgroup` | cgroups über systemd verwalten. | Erwartet ein bestimmtes `cgroupsPath`-Format. |
| `--log PFAD`, `--log-format text/json` | Protokollziel und -format. | – |
| `--debug` | Diagnoseausgaben. | – |
| `--criu PFAD` | CRIU-Programm für Sicherung/Wiederherstellung. | – |
| `-b`, `--bundle PFAD` | Bundle-Ordner bei `run`, `create`, `spec`. | Standard: aktueller Ordner. |
| `spec --rootless` | Konfiguration für rootless Container erzeugen. | Laut Manpage etwas anderes als die globale Option `--rootless`. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein minimales Bundle anlegen und einen Container starten – angelehnt an das Beispiel der Manpage zu `runc spec`. Es braucht ein Wurzeldateisystem (in der Manpage aus einem exportierten Docker-Image) und Root-Rechte. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Bundle-Ordner und Wurzeldateisystem

```bash
mkdir -p hallo/rootfs
cd hallo
tar -C rootfs -xf hello-world.tar
```

`hello-world.tar` ist ein zuvor exportiertes Dateisystem eines Containers.

### Schritt 2: Spezifikation erzeugen und anpassen

```bash
runc spec
jq '.process.args |= ["/hello"]' < config.json > neu.json
mv -f neu.json config.json
```

Laut Manpage ist die erzeugte Datei nur ein Ausgangspunkt; standardmäßig startet sie `sh`. Hier wird der Befehl auf `/hello` geändert.

### Schritt 3: Container starten

```bash
sudo runc run container1
```

`container1` ist der frei gewählte, auf dem Rechner eindeutige Name.

### Schritt 4: Aufräumen

```bash
sudo runc list
sudo runc delete container1
```

## 6. Typische Anwendungsfälle

- **Grundlage anderer Werkzeuge:** Docker, containerd, Podman (je nach Konfiguration) nutzen `runc`.
- **Fehlersuche** an Laufzeitproblemen auf niedriger Ebene.
- **Lernen,** wie Container technisch funktionieren.
- **Eingebettete Systeme,** die Container ohne vollständige Engine starten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`.

- **Konfiguration bestimmt die Isolation:** Fehler in `config.json` (zusätzliche Capabilities, Host-Einhängungen, fehlende Namensräume) heben den Schutz auf. Mit Root-Rechten kann ein falsch konfigurierter Container das System verändern.
- **Eingriffe neben Docker oder containerd:** Container, die diese Werkzeuge verwalten, nicht direkt mit `runc` stoppen oder löschen; sonst geraten deren Zustände durcheinander. **Prüfpunkt:** Die von containerd verwendeten `--root`-Ordner wurden nicht geprüft.
- **Sicherheitsaktualisierungen:** Als Laufzeit ist `runc` sicherheitskritisch; Pakete aktuell halten.
- **Zustandsordner:** Inhalte unter `/run/runc` nicht von Hand ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `runc: command not found` | Nicht installiert. | Paket `runc`. |
| `config.json` fehlt | Kein Bundle im Ordner. | `runc spec` oder `-b PFAD`. |
| Befehl im Container nicht gefunden | `process.args` passt nicht zum Wurzeldateisystem. | Laut Manpage Startbefehl anpassen. |
| Container-ID schon vorhanden | Name nicht eindeutig. | Anderen Namen oder alten Container löschen. |
| Rechtefehler | Ohne Root und ohne Rootless-Konfiguration. | `sudo` oder `runc spec --rootless`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für Alltagsarbeit Podman, Docker oder nerdctl verwenden.**
2. **`runc` zum Lernen in einer virtuellen Maschine** ausprobieren.
3. **`config.json` gründlich lesen,** bevor ein Container mit Root startet.
4. **Eindeutige Container-IDs** und Aufräumen mit `delete`.

### Prüfstand

- **Geprüfte Version:** keine; `runc` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpages `runc(8)` (Beschreibung, Befehle, globale Optionen) und `runc-spec(8)` (Spezifikation, Rootless, Beispiel), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Zusammenspiel mit containerd, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `containerd`, `ctr` | Höhere Ebene, die `runc` aufruft. |
| `docker`, `podman`, `nerdctl` | Komfortable Container-Werkzeuge. |
| `unshare`, `nsenter` | Namensräume direkt erzeugen beziehungsweise betreten. |
| `criu` | Sichert und stellt Prozesszustände wieder her. |

Ausgangseintrag: Datensatz 149 in `index.json` (`runc`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert; der Rootless-Modus ist beschrieben. Der Hilfe-Platzhalter wurde durch Bundle-Konzept, Befehle, globale Optionen und das Beispiel der Manpage ersetzt.
