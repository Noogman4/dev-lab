---
id: "buildah"
name: "buildah"
command: "buildah"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "images", "oci", "build"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 135
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# buildah – Container-Images ohne Hintergrunddienst bauen

## 1. Kurzbeschreibung

`buildah` erstellt **OCI-Container-Images** (das Format, das auch Docker und Podman verwenden). Es kann Images aus einem `Containerfile` beziehungsweise `Dockerfile` bauen oder schrittweise mit einzelnen Befehlen zusammensetzen. Anders als Docker braucht es **keinen ständig laufenden Hintergrunddienst**.

**Root-Rechte sind für die normale Arbeit nicht nötig.** `buildah` unterstützt den „rootless“-Betrieb: Images und Arbeitscontainer liegen dann unter `~/.local/share/containers/storage`. Voraussetzung sind passende Bereiche für untergeordnete Benutzer-IDs in `/etc/subuid` und `/etc/subgid`; diese einzurichten ist eine Verwaltungsaufgabe. Mit Root-Rechten liegt der Speicher unter `/var/lib/containers/storage`.

Grundlage ist die [Debian-Manpage zu buildah](https://manpages.debian.org/trixie/buildah/buildah.1.en.html). Auf dem geprüften System ist `buildah` nicht installiert.

## 2. Was macht der Befehl?

Laut Manpage kann `buildah`:

- einen **Arbeitscontainer** leer oder auf Basis eines Images anlegen (`from`),
- dessen Dateisystem einhängen und bearbeiten (`mount`, `umount`),
- Dateien hineinkopieren und Befehle darin ausführen (`copy`, `add`, `run`),
- Metadaten setzen (`config`),
- den Zustand als neues Image speichern (`commit`),
- komplette Builds aus einem Containerfile ausführen (`build`),
- Images laden, hochladen, markieren und löschen (`pull`, `push`, `tag`, `rmi`).

Ein **Arbeitscontainer** ist kein laufender Dienst wie bei `docker run`, sondern eine bearbeitbare Zwischenstufe für den Image-Bau.

### Unterbefehle

Die Manpage nennt: `add`, `build`, `commit`, `config`, `containers`, `copy`, `from`, `images`, `info`, `inspect`, `login`, `logout`, `manifest`, `mkcw`, `mount`, `prune`, `pull`, `push`, `rename`, `rm`, `rmi`, `run`, `source`, `tag`, `umount`, `unshare`, `version`.

### Gemeinsamer Speicher mit Podman

`buildah` nutzt die Bibliothek containers/storage mit der Konfiguration `/etc/containers/storage.conf` (rootless: `~/.config/containers/storage.conf`). Podman verwendet denselben Speicher; mit `buildah` gebaute Images sind deshalb in `podman images` sichtbar. **Prüfpunkt:** gilt bei gleicher Konfiguration und gleichem Benutzer.

## 3. Syntax

```text
buildah [GLOBALE_OPTIONEN] UNTERBEFEHL [OPTIONEN] [ARGUMENTE]
```

```bash
buildah build -t meinbild:1.0 .
buildah images
buildah from docker.io/library/debian:stable
buildah commit ARBEITSCONTAINER meinbild:1.1
```

Das bisherige NetMon-Beispiel `buildah --help` ist gültig (`--help`, `-h` laut Manpage). Der Platzhalter `buildah [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Unterbefehl oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `build -t NAME .` | Image aus `Containerfile`/`Dockerfile` im Ordner bauen. | Häufigster Einstieg. |
| `from IMAGE` | Arbeitscontainer aus einem Image anlegen. | Gibt den Containernamen aus. |
| `run [--] CONTAINER BEFEHL` | Befehl im Arbeitscontainer ausführen. | Syntax laut `buildah-run(1)`; für Paketinstallationen im Image. |
| `copy CONTAINER QUELLE ZIEL` | Dateien hineinkopieren. | – |
| `commit CONTAINER NAME` | Arbeitscontainer als Image speichern. | – |
| `images`, `containers` | Images bzw. Arbeitscontainer auflisten. | Nur lesend. |
| `rm`, `rmi`, `prune` | Arbeitscontainer, Images bzw. Ungenutztes löschen. | Löschen ist endgültig. |
| `push NAME ZIEL` | Image in eine Registry hochladen. | Vorher `login`. |
| `unshare` | Shell im Benutzer-Namensraum, in dem du als UID 0 erscheinst. | Laut Manpage nötig für `mount` ohne Root. |
| `--root`, `--runroot` | Anderen Speicherort verwenden. | Standard je nach UID verschieden. |
| `--storage-driver` | Speichertreiber, etwa `overlay` oder `vfs`. | Ohne Root laut Manpage standardmäßig `vfs`, sofern nicht konfiguriert. |
| `--log-level` | Ausführlichkeit. | Standard `warn`. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein kleines Image aus einem Containerfile bauen und lokal prüfen, ohne Root-Rechte. Das braucht `buildah`, Netzwerkzugriff zum Laden des Basis-Images und eingerichtete subuid-Bereiche. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Übungsordner und Containerfile

```bash
uebung="$(mktemp -d -t netmon-buildah-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'FROM docker.io/library/alpine:3.20\nRUN echo hallo > /gruss.txt\n' > Containerfile
```

### Schritt 2: Bauen

```bash
buildah build -t uebung:1 .
```

`buildah` lädt das Basis-Image, führt die `RUN`-Zeile aus und speichert das Ergebnis unter dem Namen `uebung:1`. **Prüfpunkt:** In der Liste erscheint es voraussichtlich mit dem Präfix `localhost/`; nicht geprüft.

### Schritt 3: Prüfen

```bash
buildah images
buildah inspect uebung:1
```

Die Liste zeigt das neue Image. `inspect` zeigt Metadaten wie Schichten und Konfiguration.

### Schritt 4: Aufräumen

```bash
buildah rmi uebung:1
```

Das entfernt das Übungsimage aus dem eigenen Speicher.

## 6. Typische Anwendungsfälle

- **Images in CI-Pipelines bauen,** ohne Docker-Dienst und oft ohne Root.
- **Schlanke Images** durch schrittweises Zusammensetzen.
- **Images für Podman, Kubernetes oder Docker** bereitstellen.
- **Fehlersuche bei Rechten** im rootless-Betrieb mit `buildah unshare`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution` bestehen.

- **Fremde Basis-Images:** `FROM` und `RUN` führen fremden Code beim Bau aus. Nur vertrauenswürdige Quellen und feste Versionen verwenden.
- **Geheimnisse in Images:** Dateien oder Variablen, die beim Bau in eine Schicht gelangen, bleiben dort, auch wenn ein späterer Schritt sie löscht. Wer das Image erhält, kann sie auslesen.
- **Speicherverbrauch:** Images und Zwischenstände belegen viel Platz; `vfs` speichert jede Schicht vollständig.
- **Löschen:** `rmi`, `rm` und `prune` entfernen ohne Papierkorb.
- **Hochladen:** `push` veröffentlicht Images; bei öffentlichen Registries für jeden lesbar.
- **Root-Betrieb:** Mit `sudo buildah` laufen Bauschritte mit höheren Rechten; Fehler in Containerfiles wirken stärker.
- **Registry-Zugangsdaten:** `buildah login` speichert Anmeldedaten. **Prüfpunkt:** Speicherort laut containers-auth.json(5), nicht gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `buildah: command not found` | Nicht installiert. | Paket `buildah` der Distribution. |
| Fehler zu `newuidmap` oder fehlenden subuid-Bereichen | Rootless-Voraussetzungen fehlen. | Verwaltung bittet um Einträge in `/etc/subuid` und `/etc/subgid`. |
| Kurzer Imagename wird nicht gefunden | Kein Registry-Präfix und keine Suchliste. | Vollständigen Namen wie `docker.io/library/alpine` verwenden. |
| `buildah mount` scheitert ohne Root | Laut Manpage nur in `buildah unshare` möglich. | `buildah unshare` verwenden. |
| Kein Platz mehr | Viele Images und Zwischenstände. | `buildah images`, dann gezielt `rmi`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Rootless arbeiten,** sofern eingerichtet.
2. **Vollständige Imagenamen mit Versionsangabe** nutzen.
3. **Keine Geheimnisse in Containerfiles** oder Bauschritte schreiben.
4. **Images vor `push` mit `inspect` prüfen.**
5. **Regelmäßig aufräumen,** aber Listen vorher ansehen.

### Prüfstand

- **Geprüfte Version:** keine; `buildah` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpages `buildah(1)` (Aufgaben, globale Optionen, Unterbefehle, Speicherorte, Konfigurationsdateien), `buildah-unshare(1)` und `buildah-run(1)` (Syntax), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, rootless-Einrichtung, Fehlermeldungen, Ablage der Registry-Anmeldedaten.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `podman` | Führt Container aus; teilt den Speicher mit `buildah`. |
| `docker build` | Image-Bau mit Docker-Dienst. |
| `skopeo` | Kopiert und prüft Images in Registries, ohne sie zu laden. |
| `nerdctl build` | Image-Bau für containerd. |

Ausgangseintrag: Datensatz 135 in `index.json` (`buildah`, Kategorie „Container“, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsumfang, Unterbefehle, rootless-Speicherorte, Risiken beim Image-Bau und einen Bauablauf ersetzt.
