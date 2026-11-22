---
id: "aws"
name: "aws"
command: "aws"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "aws", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 127
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# aws – Amazon Web Services über die Kommandozeile steuern

## 1. Kurzbeschreibung

`aws` ist die offizielle Kommandozeile für **Amazon Web Services** (AWS CLI). Damit lassen sich nahezu alle AWS-Dienste steuern: Speicher (S3), virtuelle Maschinen (EC2), Benutzer und Rechte (IAM) und viele weitere. Jeder Aufruf schickt Anfragen über das Internet an AWS und handelt im Namen eines AWS-Kontos.

**Root-Rechte sind nicht nötig.** Die AWS CLI läuft als normales Programm. Welche Aktionen erlaubt sind, entscheiden die **AWS-Zugangsdaten und deren IAM-Berechtigungen**, nicht die Linux-Rechte.

Dieses Dokument beschreibt die **AWS CLI Version 2** anhand des [AWS-CLI-Benutzerhandbuchs](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-commandstructure.html). Auf dem geprüften System ist `aws` nicht installiert; es gab keine praktische Prüfung.

## 2. Was macht der Befehl?

Ein Aufruf besteht laut Handbuch aus festen Teilen in dieser Reihenfolge:

```text
aws DIENST OPERATION [OPTIONEN UND PARAMETER]
```

- `DIENST` ist meist ein AWS-Dienst, etwa `s3`, `ec2`, `iam`, `sts`.
- `OPERATION` ist die Aktion, zum Beispiel `ls`, `describe-instances`, `get-caller-identity`.
- Optionen und Parameter folgen in beliebiger Reihenfolge.

Ob ein Aufruf nur liest oder etwas verändert, hängt allein von der Operation ab. `describe-…`, `list-…` und `get-…` lesen in der Regel. `create-…`, `delete-…`, `put-…`, `run-instances` oder `s3 rm` verändern Ressourcen und können **Kosten verursachen oder Daten löschen**.

### Zugangsdaten und Konfiguration

Laut [Handbuch zu Konfigurationsdateien](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) speichert `aws configure` die vertraulichen Zugangsdaten in `~/.aws/credentials` und die übrigen Einstellungen in `~/.aws/config`. Beide sind **Klartextdateien**, gegliedert in Profile. Ohne Angabe gilt das Profil `default`. Alternativ unterstützt die CLI kurzlebige Anmeldungen über IAM Identity Center (SSO, Abschnitte `sso-session`).

## 3. Syntax

```text
aws [GLOBALE_OPTIONEN] DIENST OPERATION [PARAMETER]
aws DIENST wait BEDINGUNG [PARAMETER]
aws help
aws DIENST help
```

```bash
aws sts get-caller-identity
aws s3 ls --profile privat
aws ec2 describe-instances --region eu-central-1 --output table
```

Das bisherige NetMon-Beispiel `aws --help` ist nicht die dokumentierte Hilfeform; das Handbuch verweist auf `aws help` und `aws DIENST OPERATION help`. **Prüfpunkt:** Verhalten von `--help` in der installierten Version prüfen. Der Platzhalter `aws [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Globale Optionen laut [Handbuch zu Befehlszeilenoptionen](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-options.html):

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--profile NAME` | Benanntes Profil verwenden. | Schützt vor Aufrufen im falschen Konto. |
| `--region REGION` | AWS-Region wählen. | Ressourcen sind meist regionsgebunden. |
| `--output FORMAT` | Ausgabeformat: `json`, `yaml`, `yaml-stream`, `text`, `table`, `off`. | `table` für Menschen, `json` für Skripte. |
| `--query AUSDRUCK` | Ausgabe mit JMESPath filtern. | Filtert nur die Anzeige, nicht die Anfrage. |
| `--no-cli-pager` | Ausgabe nicht an einen Pager geben. | Für Skripte. |
| `--no-paginate` | Nur die erste Ergebnisseite. | Große Listen bleiben unvollständig. |
| `--endpoint-url URL` | Anderen Endpunkt verwenden. | Etwa für lokale Testumgebungen. |
| `--debug` | Ausführliche Diagnose. | Kann vertrauliche Details enthalten. |
| `--no-verify-ssl` | Zertifikatsprüfung abschalten. | Laut Handbuch keine gute Praxis; anfällig für Abhören. |
| `--no-sign-request` | Anfragen ohne Anmeldung senden. | Nur für öffentliche Ressourcen. |

Einige Operationen bieten `--dry-run` (etwa bei EC2) beziehungsweise `--dryrun` (bei `aws s3 cp`, `sync`, `rm`), um nur die Berechtigung zu prüfen oder geplante Aktionen anzuzeigen. **Prüfpunkt:** Verfügbarkeit hängt von der einzelnen Operation ab.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, mit welcher Identität die CLI arbeitet, und dann einen Speicherbereich nur lesend auflisten. Das Beispiel braucht ein AWS-Konto und Zugangsdaten; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Version und Installation

```bash
aws --version
```

Die Ausgabe nennt die CLI-Version. Beginnt sie mit `aws-cli/1.`, ist die ältere Version 1 installiert, für die teils andere Details gelten.

### Schritt 2: Profil einrichten

```bash
aws configure --profile uebung
```

Die CLI fragt Zugangsschlüssel, geheimen Schlüssel, Standardregion und Ausgabeformat ab und schreibt sie in `~/.aws/credentials` und `~/.aws/config`.

### Schritt 3: Identität prüfen

```bash
aws sts get-caller-identity --profile uebung
```

Die Ausgabe nennt Konto-ID, Benutzer- oder Rollen-ARN. Laut [Referenz zu get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) braucht dieser Aufruf keine Berechtigungen. Er ist deshalb ein guter erster Test, ob Zugangsdaten überhaupt funktionieren und **welches Konto** betroffen wäre.

### Schritt 4: Nur lesend auflisten

```bash
aws s3 ls --profile uebung
```

Zeigt die S3-Buckets, auf die die Identität Zugriff hat. Es wird nichts verändert.

## 6. Typische Anwendungsfälle

- **Bestandsaufnahme:** `aws ec2 describe-instances --output table`.
- **Dateien übertragen:** `aws s3 cp datei s3://bucket/` oder `aws s3 sync ordner s3://bucket/ordner`.
- **Automatisierung:** Skripte mit `--output json` und `--query`.
- **Warten auf Zustände:** `aws ec2 wait instance-running --instance-ids ...`.
- **Fehlersuche bei Rechten:** `aws sts get-caller-identity`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nur für lesende Operationen zu. Der Kopf verwendet `caution`, weil derselbe Befehl Cloud-Ressourcen anlegen, ändern und löschen kann.

- **Kosten:** Das Starten von Instanzen oder Speichern großer Datenmengen kostet Geld, auch wenn es nur ein Versehen war.
- **Datenverlust:** `aws s3 rm --recursive` oder `aws s3 sync --delete` löschen Objekte; laut [Referenz zu s3 sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html) entfernt `--delete` Ziel-Dateien, die in der Quelle fehlen, und `--dryrun` zeigt die geplanten Schritte ohne Ausführung. Ohne aktivierte Versionierung gibt es keinen Papierkorb.
- **Falsches Konto oder falsche Region:** Ohne `--profile` greift `default`. Vorher immer `get-caller-identity` prüfen.
- **Zugangsdaten im Klartext:** `~/.aws/credentials` enthält dauerhafte Schlüssel. Die Datei darf nicht in Sicherungen, Repositories oder Fehlerberichten landen. Kurzlebige Anmeldungen (SSO) sind sicherer.
- **Diagnoseausgaben:** `--debug` und Fehlermeldungen können Kontonummern, ARNs oder Anfragedetails zeigen.
- **Zertifikatsprüfung:** `--no-verify-ssl` öffnet Angriffen auf die Verbindung die Tür.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `aws: command not found` | CLI nicht installiert. | Installation nach offizieller Anleitung oder Paket der Distribution. |
| `Unable to locate credentials` | Keine Zugangsdaten für das gewählte Profil. | `aws configure --profile NAME` oder SSO-Anmeldung. |
| `AccessDenied` / `UnauthorizedOperation` | IAM-Rechte fehlen. | Mit `get-caller-identity` Identität prüfen; Rechte durch die Verwaltung. |
| `You must specify a region` | Keine Region gesetzt. | `--region` oder Standardregion im Profil. |
| `ExpiredToken` | Sitzungsschlüssel abgelaufen. | Neu anmelden, etwa `aws sso login`. |
| SSL-Zertifikatsfehler | Proxy, falsche Systemzeit, fehlende Zertifizierungsstelle. | Ursache beheben, nicht `--no-verify-ssl` verwenden. |

**Prüfpunkt:** Meldungstexte sind sinngemäß wiedergegeben und nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Immer zuerst `aws sts get-caller-identity`.**
2. **Benannte Profile statt `default`** für produktive Konten.
3. **Mit lesenden Operationen beginnen** (`list`, `describe`, `get`).
4. **Bei `s3 sync` und `s3 rm` erst `--dryrun`.**
5. **Kurzlebige Anmeldungen (SSO) bevorzugen;** dauerhafte Schlüssel regelmäßig erneuern.
6. **`~/.aws/` nicht teilen** und Rechte auf `700` beziehungsweise `600` halten.

### Prüfstand

- **Geprüfte Version:** keine; `aws` ist auf dem Prüfsystem nicht installiert.
- **Quellen gelesen:** AWS-CLI-Benutzerhandbuch Version 2 (Befehlsstruktur, Konfigurationsdateien, Befehlszeilenoptionen) sowie die Referenzen zu `sts get-caller-identity`, `s3 sync` und `sso login`, Stand des Abrufs 2026-11-13.
- **Nicht geprüft:** sämtliche Aufrufe, Fehlermeldungen, Unterschiede zwischen Version 1 und 2 sowie das Verhalten von `--help`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `az` | Kommandozeile für Microsoft Azure. |
| `gcloud` | Kommandozeile für Google Cloud. |
| `ssh` | Anmeldung auf EC2-Instanzen. |
| `rsync`, `curl` | Datenübertragung ohne AWS-spezifische Funktionen. |
| `jq` | Verarbeitet JSON-Ausgaben weiter. |

Ausgangseintrag: Datensatz 127 in `index.json` (`aws`, Kategorie „Cloud & Remote“, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehlsstruktur, Zugangsdatenablage, globale Optionen und einen lesenden Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben, weil schreibende Operationen Cloud-Ressourcen verändern und Kosten verursachen.
