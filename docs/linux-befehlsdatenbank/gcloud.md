---
id: "gcloud"
name: "gcloud"
command: "gcloud"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "google-cloud", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 129
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# gcloud – Google Cloud über die Kommandozeile steuern

## 1. Kurzbeschreibung

`gcloud` ist das zentrale Kommandozeilenwerkzeug der **Google Cloud CLI**. Damit werden Projekte, virtuelle Maschinen (Compute Engine), Kubernetes-Cluster, Konten, Rechte und viele weitere Google-Cloud-Dienste verwaltet.

**Root-Rechte sind nicht nötig.** `gcloud` läuft als normales Programm. Was erlaubt ist, bestimmen das angemeldete Google-Konto beziehungsweise Dienstkonto und dessen Rollen im Projekt.

Grundlage ist die offizielle [Übersicht zur gcloud CLI](https://cloud.google.com/sdk/gcloud) und die [gcloud-Referenz](https://cloud.google.com/sdk/gcloud/reference). Auf dem geprüften System ist `gcloud` nicht installiert; es gab keine praktische Prüfung.

## 2. Was macht der Befehl?

Befehle sind in verschachtelten **Befehlsgruppen** organisiert, die Produkte oder Funktionen abbilden:

```text
gcloud [FREIGABESTUFE] GRUPPE [UNTERGRUPPE] BEFEHL [POSITIONSARGUMENTE] [OPTIONEN]
```

Beispiel: `gcloud compute instances list`. Laut Dokumentation bezeichnen Positionsargumente das Objekt, auf das ein Befehl wirkt; Optionen verändern sein Verhalten.

### Freigabestufen

| Stufe | Bedeutung laut Dokumentation |
| --- | --- |
| ohne Zusatz (GA) | Stabil, für den Produktivbetrieb. |
| `beta` | Funktional vollständig, Änderungen ohne Ankündigung möglich. |
| `alpha` | Frühe Fassung, Änderungen ohne Ankündigung. |
| `preview` | Zum Sammeln von Rückmeldungen. |

Die Komponenten `alpha`, `beta` und `preview` sind nicht standardmäßig installiert; beim ersten Aufruf bietet `gcloud` die Installation an.

### Konfigurationen und Eigenschaften

Eine **Konfiguration** ist eine benannte Sammlung von Eigenschaften wie Projekt, Konto, Zone; sie wirkt wie ein Profil. Laut [Dokumentation zu Konfigurationen](https://cloud.google.com/sdk/docs/configurations) liegen sie unter Linux in `~/.config/gcloud` (änderbar über `CLOUDSDK_CONFIG`). Dort befinden sich auch die zwischengespeicherten Anmeldedaten.

### Ausgabe und Rückfragen

Erfolgreiche Ausgaben gehen nach stdout, Rückfragen, Warnungen und Fehler nach stderr. Vor zerstörerischen Aktionen wie `gcloud projects delete` fragt `gcloud` nach. `--quiet` schaltet alle Rückfragen ab.

## 3. Syntax

```text
gcloud GRUPPE BEFEHL [ARGUMENTE] [--project=ID] [--format=FORMAT] [--quiet]
gcloud GRUPPE --help
gcloud help BEGRIFF
```

```bash
gcloud init
gcloud config list
gcloud projects list
gcloud compute instances list --project=mein-projekt
```

Das bisherige NetMon-Beispiel `gcloud --help` ist gültig; die Referenz nennt `--help` als globale Option für ausführliche Hilfe. Der Platzhalter `gcloud [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Optionen laut Referenz:

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--project=ID` | Projekt für diesen Aufruf. | Bestimmt auch Abrechnung und Kontingente. |
| `--account=KONTO` | Konto für diesen Aufruf. | Überschreibt `core/account`. |
| `--configuration=NAME` | Benannte Konfiguration verwenden. | Für mehrere Projekte oder Konten. |
| `--format=FORMAT` | Ausgabeformat, etwa `json`, `yaml`, `csv`, `table`, `value`. | Für Skripte `json` oder `value(...)`. |
| `--quiet`, `-q` | Alle Rückfragen abschalten. | Löschbefehle laufen dann ohne Bestätigung. |
| `--verbosity=STUFE` | Ausführlichkeit (Standard `warning`). | – |
| `--impersonate-service-account=KONTO` | Anfragen als Dienstkonto stellen. | Erfordert entsprechende Rechte. |
| `--help` | Ausführliche Hilfe. | – |

Wichtige Verwaltungsbefehle:

| Befehl | Zweck |
| --- | --- |
| `gcloud init` | Ersteinrichtung: Anmeldung, Projekt, Region. |
| `gcloud auth login` | Benutzerkonto anmelden. |
| `gcloud config set project ID` | Aktives Projekt setzen. |
| `gcloud config configurations create NAME` | Neue Konfiguration anlegen. |
| `gcloud config configurations activate NAME` | Konfiguration wechseln. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einrichten, das aktive Projekt prüfen und virtuelle Maschinen nur lesend anzeigen. Das braucht ein Google-Cloud-Konto; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Ersteinrichtung

```bash
gcloud init
```

`gcloud init` führt durch Anmeldung, Projektauswahl und Standardregion.

### Schritt 2: Aktive Einstellungen ansehen

```bash
gcloud config list
```

Zeigt Konto und Projekt der aktiven Konfiguration. **Vor Änderungen immer prüfen.**

### Schritt 3: Lesend auflisten

```bash
gcloud compute instances list --format=table
```

Zeigt VMs im aktiven Projekt. Ist die Compute-Engine-API im Projekt nicht aktiviert, kann `gcloud` deren Aktivierung anbieten – das wäre bereits eine Änderung am Projekt. **Prüfpunkt:** Dieses Verhalten ist nicht in den gelesenen Quellen belegt und nicht praktisch geprüft.

### Schritt 4: Getrennte Konfiguration für ein zweites Projekt

```bash
gcloud config configurations create test
gcloud config set project mein-testprojekt
gcloud config configurations activate default
```

So bleiben Test- und Produktivprojekt getrennt.

## 6. Typische Anwendungsfälle

- **Bestandsaufnahme:** `gcloud projects list`, `gcloud compute instances list`.
- **Kubernetes-Zugang:** Zugangsdaten für GKE-Cluster in `kubectl` übernehmen.
- **Automatisierung:** Skripte mit `--format=json` und `--quiet` (nach sorgfältiger Prüfung).
- **Mehrere Projekte:** Konfigurationen pro Projekt oder Kunde.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nur auf lesende Befehle zu. Der Kopf verwendet `caution`.

- **Löschen und Kosten:** Befehle wie `gcloud projects delete` oder `compute instances create` verändern Ressourcen und verursachen Kosten.
- **`--quiet` schaltet Schutzabfragen ab.** In Skripten nur verwenden, wenn die Befehle vorher geprüft sind.
- **Falsches Projekt:** Ohne `--project` gilt das aktive Projekt der aktiven Konfiguration.
- **API-Aktivierung:** Das Aktivieren von Diensten verändert das Projekt und kann Kosten auslösen; Rückfragen dazu nicht ungelesen bestätigen.
- **Anmeldedaten:** `~/.config/gcloud` enthält Zugangstoken. Nicht teilen und nicht in Repositories oder Fehlerberichte übernehmen.
- **Alpha- und Beta-Befehle:** können sich ohne Ankündigung ändern; für Skripte im Produktivbetrieb ungeeignet.
- **stderr nicht auswerten:** Laut Dokumentation sind Texte auf stderr nicht stabil.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `gcloud: command not found` | Nicht installiert. | Installation nach offizieller Anleitung. |
| Hinweis, dass kein Konto angemeldet ist | Keine Anmeldung. | `gcloud auth login` oder `gcloud init`. |
| `PERMISSION_DENIED` | Rolle fehlt. | Konto und Projekt mit `gcloud config list` prüfen. |
| Projekt nicht gesetzt | Kein `core/project`. | `gcloud config set project ID` oder `--project`. |
| Frage nach Installation einer Komponente | `alpha`/`beta`-Befehl ohne Komponente. | Installieren oder GA-Befehl verwenden. |
| API nicht aktiviert | Dienst im Projekt deaktiviert. | Bewusst entscheiden, ob aktiviert werden soll. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`gcloud config list` vor jeder Änderung.**
2. **Lesende Befehle zuerst** (`list`, `describe`).
3. **`--quiet` vermeiden,** solange du lernst.
4. **Eigene Konfiguration pro Projekt.**
5. **Budgets und Kostenwarnungen** im Projekt einrichten.
6. **Nur GA-Befehle in Skripten.**

### Prüfstand

- **Geprüfte Version:** keine; `gcloud` ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): gcloud-Übersicht (Freigabestufen, Befehlsgruppen, Konfigurationen, stdout/stderr, Rückfragen), Dokumentation zu Konfigurationen (Speicherort, `CLOUDSDK_CONFIG`) und gcloud-Referenz (globale Optionen).
- **Nicht geprüft:** alle Aufrufe, Fehlermeldungen und das Verhalten bei der API-Aktivierung.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gcloud storage` | Gruppe für Cloud-Storage-Buckets und -Objekte (laut Referenz). |
| `kubectl` | Steuert GKE-Cluster. |
| `aws`, `az` | Kommandozeilen anderer Cloud-Anbieter. |
| `ssh` | Anmeldung auf VMs. |

Ausgangseintrag: Datensatz 129 in `index.json` (`gcloud`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehlsaufbau, Freigabestufen, Konfigurationen, globale Optionen und einen lesenden Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
