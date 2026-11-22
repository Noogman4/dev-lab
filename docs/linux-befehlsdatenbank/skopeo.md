---
id: "skopeo"
name: "skopeo"
command: "skopeo"
category: "Container"
language: "de"
root_required: false
risk_level: "caution"
tags: ["container", "images", "registry", "oci"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 150
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# skopeo – Container-Images prüfen und kopieren, ohne sie zu laden

## 1. Kurzbeschreibung

`skopeo` arbeitet mit **Container-Images und Registries**, ohne eine Container-Engine zu benötigen. Es kann Images zwischen Speicherorten kopieren und dabei umwandeln, Metadaten eines Images in einer Registry ansehen, ohne es herunterzuladen, verfügbare Tags auflisten, Images signieren und prüfen sowie Images aus einer Registry löschen.

**Root-Rechte sind nicht nötig.** Laut [Debian-Manpage zu skopeo](https://manpages.debian.org/trixie/skopeo/skopeo.1.en.html) braucht `skopeo` für die meisten Funktionen weder laufende Container-Dienste noch Root – außer beim Kopieren in den Speicher einer Laufzeit wie den Docker-Dienst oder containers/storage.

Auf dem geprüften System ist `skopeo` nicht installiert.

## 2. Was macht der Befehl?

### Imagenamen mit Transport

Die meisten Befehle erwarten Images im Format `TRANSPORT:DETAILS`. Die Manpage nennt:

| Transport | Bedeutung |
| --- | --- |
| `docker://REFERENZ` | Image in einer Registry (Docker Registry HTTP API V2). |
| `containers-storage:REFERENZ` | Lokaler Speicher von Podman, Buildah, CRI-O. |
| `docker-daemon:REFERENZ` | Speicher des Docker-Dienstes. |
| `docker-archive:PFAD` | Datei im Format von `docker save`. |
| `oci:PFAD:TAG` | Ordner im OCI-Image-Layout. |
| `oci-archive:PFAD:TAG` | TAR-Archiv im OCI-Image-Layout. |
| `dir:PFAD` | Ordner mit Manifest und Schichten als Einzeldateien (vor allem zur Fehlersuche). |

### Unterbefehle

| Befehl | Wirkung |
| --- | --- |
| `inspect` | Metadaten eines Images anzeigen, ohne es herunterzuladen. |
| `list-tags` | Tags eines Repositorys auflisten. |
| `copy` | Image (Manifest, Schichten, Signaturen) kopieren. |
| `sync` | Mehrere Images zwischen Orten abgleichen. |
| `delete` | Image in einer Registry löschen. |
| `login`, `logout` | Anmeldung bei einer Registry. |
| `manifest-digest` | Prüfsumme eines Manifests berechnen. |
| `standalone-sign`, `standalone-verify`, `generate-sigstore-key` | Signaturen erzeugen und prüfen. |

### Anmeldedaten

Für `docker://` nutzt `skopeo` laut Manpage die Anmeldung aus `$XDG_RUNTIME_DIR/containers/auth.json` (gesetzt mit `skopeo login`), ersatzweise `~/.docker/config.json` (von `docker login`).

## 3. Syntax

```text
skopeo [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] QUELLE [ZIEL]
```

```bash
skopeo inspect docker://docker.io/library/alpine:3.20
skopeo list-tags docker://docker.io/library/alpine
skopeo copy docker://docker.io/library/alpine:3.20 oci-archive:alpine.tar:3.20
```

Das bisherige NetMon-Beispiel `skopeo --help` ist gültig (`--help`, `-h` laut Manpage). Der Platzhalter `skopeo [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Optionen stehen laut Manpage **vor** dem Unterbefehl:

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--policy DATEI` | Andere Vertrauensrichtlinie (`policy.json`). | Bestimmt, welche Images als vertrauenswürdig gelten. |
| `--insecure-policy` | Alles erlauben, keine Richtlinie. | Laut Manpage unsicher. |
| `--override-arch`, `--override-os`, `--override-variant` | Image für andere Architektur oder anderes System wählen. | Etwa `--override-arch arm64`. |
| `--tmpdir ORDNER` | Ordner für temporäre Dateien. | Standard `/var/tmp`; große Images brauchen Platz. |
| `--command-timeout DAUER` | Zeitlimit. | – |
| `--debug` | Diagnose. | – |
| `--registries.d ORDNER` | Andere Registry-Konfiguration. | – |
| `-v`, `--version` | Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Vor dem Herunterladen prüfen, welche Versionen eines Images es gibt und was ein Tag enthält, und das Image dann als Archiv sichern. Das braucht Netzwerkzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verfügbare Tags

```bash
skopeo list-tags docker://docker.io/library/alpine
```

Laut `skopeo-list-tags(1)` liefert der Befehl die Liste der Tags dieses Repositorys. **Prüfpunkt:** Das genaue Ausgabeformat wurde nicht geprüft.

### Schritt 2: Metadaten ansehen

```bash
skopeo inspect docker://docker.io/library/alpine:3.20
```

Zeigt unter anderem Digest, Erstellungsdatum, Architektur, Schichten und Labels – ohne das Image zu laden.

### Schritt 3: Als Archiv speichern

```bash
uebung="$(mktemp -d -t netmon-skopeo-XXXXXX)" || exit 1
skopeo copy docker://docker.io/library/alpine:3.20 "oci-archive:$uebung/alpine.tar:3.20"
```

Das Image liegt danach als OCI-Archiv im Übungsordner und lässt sich etwa auf einen Rechner ohne Internetzugang übertragen.

## 6. Typische Anwendungsfälle

- **Images prüfen, bevor man sie startet** (Herkunft, Datum, Digest).
- **Registry-Spiegel** mit `copy` oder `sync` befüllen.
- **Offline-Übertragung** über `oci-archive` oder `docker-archive`.
- **Signaturen** erzeugen und prüfen.
- **Aufräumen in Registries** mit `delete`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution`; `inspect` und `list-tags` sind harmlos.

- **`delete` entfernt Images in der Registry** – für alle Nutzer dieser Registry.
- **`copy` und `sync` in eine Registry** überschreiben vorhandene Tags.
- **`--insecure-policy`** schaltet die Vertrauensprüfung ab.
- **Anmeldedaten** liegen in `auth.json` beziehungsweise `~/.docker/config.json`; Dateien schützen.
- **Speicherplatz:** Große Images belegen beim Kopieren Platz in `/var/tmp` und am Ziel.
- **Kopieren in Laufzeitspeicher** (`docker-daemon:`, `containers-storage:`) braucht passende Rechte und verändert dort den Bestand.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `skopeo: command not found` | Nicht installiert. | Paket `skopeo`. |
| Transport fehlt oder unbekannt | Referenz ohne `docker://` o. Ä. | Transport angeben. |
| Anmeldung verweigert | Private Registry ohne Login. | `skopeo login REGISTRY`. |
| Kein Image für diese Architektur | Image nur für andere Plattformen. | `--override-arch`. |
| Richtlinie lehnt ab | `policy.json` verlangt Signaturen. | Signaturen prüfen statt `--insecure-policy`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `inspect` und `list-tags` beginnen.**
2. **Images über den Digest festlegen,** nicht nur über Tags.
3. **Keine `--insecure-policy`.**
4. **Vor `delete` und Kopien in Registries das Ziel doppelt prüfen.**

### Prüfstand

- **Geprüfte Version:** keine; `skopeo` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpage `skopeo(1)` (Funktionen, Transporte, globale Optionen, Unterbefehle, Anmeldedaten), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Ausgabeformate, Fehlermeldungen, Signaturfunktionen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `podman`, `buildah` | Nutzen dieselben Bibliotheken und Speicher. |
| `docker pull`, `docker save` | Laden bzw. speichern Images über den Docker-Dienst. |

Ausgangseintrag: Datensatz 150 in `index.json` (`skopeo`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Transporte, Unterbefehle nach Wirkung, Anmeldedaten und einen Prüfablauf ersetzt.
