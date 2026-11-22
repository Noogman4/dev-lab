---
id: "az"
name: "az"
command: "az"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "azure", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 128
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# az – Microsoft Azure über die Kommandozeile steuern

## 1. Kurzbeschreibung

`az` ist die **Azure CLI**, die offizielle Kommandozeile für Microsoft Azure. Mit ihr lassen sich Abonnements, Ressourcengruppen, virtuelle Maschinen, Speicher, Netzwerke und viele weitere Azure-Dienste anlegen, abfragen, ändern und löschen.

**Root-Rechte sind nicht nötig.** Die Azure CLI läuft als normales Programm. Welche Aktionen erlaubt sind, entscheiden das angemeldete Azure-Konto und dessen Rollen in Azure.

Grundlage ist die offizielle Dokumentation [Get started with Azure CLI](https://learn.microsoft.com/en-us/cli/azure/get-started-with-azure-cli). Auf dem geprüften System ist `az` nicht installiert; es gab keine praktische Prüfung.

## 2. Was macht der Befehl?

Befehle sind in **Gruppen** gegliedert, die Dienste oder Ressourcentypen abbilden:

```text
az GRUPPE [UNTERGRUPPE ...] BEFEHL [PARAMETER]
```

Beispiele: `az vm list`, `az group create`, `az storage account show`. Jeder Aufruf sendet Anfragen an Azure über das Internet. Ob er nur liest oder verändert, hängt vom Befehl ab: `list` und `show` lesen, `create`, `update`, `delete`, `start`, `stop` verändern – und können **Kosten verursachen oder Daten löschen**.

### Anmeldung

`az login` öffnet laut Dokumentation den Standardbrowser für die Anmeldung; ohne Browser wird ein Gerätecode-Verfahren angeboten (`az login --use-device-code`). Danach erscheint eine Liste der Abonnements; das mit `isDefault: true` ist aktiv. Wechsel mit `az account set --subscription ID`. Die Dokumentation weist darauf hin, dass Microsoft seit September 2025 Mehrfaktor-Anmeldung für Benutzerkonten in der Azure CLI verlangt.

### Konfiguration

Laut [Dokumentation zur Konfiguration](https://learn.microsoft.com/en-us/cli/azure/azure-cli-configuration) liegt die Konfigurationsdatei unter `$AZURE_CONFIG_DIR/config`, standardmäßig `~/.azure/config`. Dort und mit `az config set` lassen sich Vorgaben setzen, etwa `defaults.group` oder `defaults.location`. Der Ordner enthält auch Protokolle und zwischengespeicherte Anmeldedaten. Die Einstellung `collect_telemetry` steuert, ob anonyme Nutzungsdaten an Microsoft gesendet werden.

## 3. Syntax

```text
az GRUPPE BEFEHL [PARAMETER] [GLOBALE_ARGUMENTE]
az GRUPPE --help
az find SUCHBEGRIFF
```

```bash
az login
az account show --output table
az vm list --output table
az group list --query "[].name" --output tsv
```

Das bisherige NetMon-Beispiel `az --help` ist eine gültige Hilfeform; die Dokumentation nennt `--help` für jede Gruppe und jeden Befehl. Der Platzhalter `az [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Argumente laut Dokumentation:

| Argument | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help`, `-h` | Hilfe zu Gruppe oder Befehl, mit Beispielen. | Gut zum Erkunden. |
| `--output`, `-o` | Ausgabeformat: `json`, `jsonc`, `tsv`, `table`, `yaml`. | `table` zum Lesen, `tsv` für Shell-Skripte. |
| `--query` | Ausgabe mit JMESPath filtern. | Filtert nur die Anzeige. |
| `--subscription` | Abonnement für diesen Aufruf wählen. | Schützt vor Aufrufen im falschen Abonnement. |
| `--verbose` | Mehr Ausführungsdetails. | – |
| `--debug` | REST-Aufrufe zur Fehlersuche. | Kann sensible Details zeigen. |
| `--only-show-errors` | Nicht kritische Ausgaben unterdrücken. | Warnungen gehen dann verloren. |

Häufige befehlsspezifische Parameter:

| Parameter | Bedeutung | Hinweis |
| --- | --- | --- |
| `--resource-group`, `-g` | Ressourcengruppe. | Pflicht bei vielen Befehlen. |
| `--name`, `-n` | Name der Ressource. | – |
| `--no-wait` | Nicht auf das Ende langer Vorgänge warten. | Fehler erscheinen dann nicht sofort. |
| `--yes`, `-y` | Rückfrage bei Löschbefehlen überspringen. | Bei `az group delete` laut [Referenz zu az group](https://learn.microsoft.com/en-us/cli/azure/group) vorhanden; nicht bei jedem Befehl. |

Weitere Hilfen: `az find vm` sucht passende Befehle, `az interactive` startet einen Modus mit Vorschlägen, `az version` zeigt die installierte Version.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Anmelden, das aktive Abonnement prüfen und Ressourcen nur lesend anzeigen. Dafür ist ein Azure-Konto nötig; das Beispiel ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Version

```bash
az version
```

### Schritt 2: Anmelden

```bash
az login
```

Der Browser öffnet sich für die Anmeldung. Ohne grafische Umgebung: `az login --use-device-code` und den angezeigten Code auf der genannten Webseite eingeben.

### Schritt 3: Aktives Abonnement prüfen

```bash
az account show --output table
```

Zeigt Name und ID des aktiven Abonnements. **Vor jeder Änderung prüfen,** dass es das gewünschte ist.

### Schritt 4: Ressourcen lesend auflisten

```bash
az group list --output table
az vm list --output table
```

Beide Befehle zeigen Ressourcengruppen beziehungsweise virtuelle Maschinen und verändern nichts.

## 6. Typische Anwendungsfälle

- **Bestandsaufnahme:** `az resource list --output table`.
- **Automatisierung:** Skripte mit `--query` und `--output tsv`.
- **Bereitstellung:** Ressourcengruppen und VMs anlegen.
- **Aufräumen:** Testumgebungen mit `az group delete` entfernen (siehe Risiken).
- **Cloud Shell:** Im Browser ist die Azure CLI laut Dokumentation bereits vorinstalliert.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ gilt nur für lesende Befehle. Der Kopf verwendet `caution`, weil derselbe Befehl Ressourcen verändern und löschen kann.

- **Löschen ganzer Gruppen:** `az group delete` entfernt alle enthaltenen Ressourcen. Mit `--yes` ohne Rückfrage, mit `--no-wait` sogar ohne sichtbares Ende.
- **Kosten:** Neue VMs, Datenbanken oder Speicher verursachen laufende Kosten.
- **Falsches Abonnement:** Vor Änderungen `az account show` prüfen oder `--subscription` angeben.
- **Gespeicherte Anmeldung:** `~/.azure/` enthält Anmeldeinformationen. Ordner nicht teilen, nicht in Sicherungen für Dritte und nicht in Repositories.
- **Ausgaben mit Geheimnissen:** Manche Befehle geben Schlüssel oder Verbindungszeichenfolgen aus. Die Konfiguration kennt laut Dokumentation eine Warnung bei sensibler Ausgabe; Ausgaben trotzdem nicht ungeprüft in Protokolle schreiben.
- **Telemetrie:** Standardmäßig können anonyme Nutzungsdaten gesendet werden; mit `az config set core.collect_telemetry=false` abschaltbar. **Prüfpunkt:** genaue Schreibweise in der installierten Version prüfen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `az: command not found` | Nicht installiert. | Installation nach offizieller Anleitung. |
| Aufforderung `Please run 'az login'` | Keine gültige Anmeldung. | `az login`. |
| `AuthorizationFailed` | Rolle erlaubt die Aktion nicht. | Identität mit `az account show` prüfen; Rechte durch die Verwaltung. |
| `ResourceGroupNotFound` | Falscher Name oder falsches Abonnement. | `az group list` im richtigen Abonnement. |
| Browser öffnet sich nicht | Keine grafische Umgebung. | `az login --use-device-code`. |
| MFA-Fehler in Skripten | Benutzerkonto mit Passwort in Automatisierung. | Laut Dokumentation auf Workload-Identitäten umstellen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `list` und `show` beginnen.**
2. **Vor Änderungen `az account show`.**
3. **`--yes` und `--no-wait` vermeiden,** solange du lernst.
4. **Testressourcen in einer eigenen Ressourcengruppe** anlegen, damit sie gezielt gelöscht werden können.
5. **Kostenwarnungen und Budgets** im Azure-Portal einrichten.
6. **`~/.azure/` schützen.**

### Prüfstand

- **Geprüfte Version:** keine; `az` ist nicht installiert.
- **Quellen gelesen** (Abruf 2026-11-13): Microsoft-Dokumentation „Get started with Azure CLI“ (Anmeldung, Hilfe, globale Argumente, interaktiver Modus), „Azure CLI configuration“ (Konfigurationsort, Vorgaben, Telemetrie) [„Tips for using the Azure CLI successfully“](https://learn.microsoft.com/en-us/cli/azure/use-azure-cli-successfully) (`--no-wait`, `--query`) sowie die Referenz zu `az group` (`--yes`, `--no-wait` bei `delete`).
- **Nicht geprüft:** alle Aufrufe, Fehlermeldungen, `--yes` je Befehl, Telemetrie-Schalter.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `aws` | Kommandozeile für Amazon Web Services. |
| `gcloud` | Kommandozeile für Google Cloud. |
| `kubectl` | Steuert Kubernetes-Cluster, etwa Azure Kubernetes Service. |
| `ssh` | Anmeldung auf Azure-VMs. |
| `jq` | Verarbeitet JSON-Ausgaben. |

Ausgangseintrag: Datensatz 128 in `index.json` (`az`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehlsaufbau, Anmeldung, Konfigurationsort, globale Argumente und einen lesenden Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
