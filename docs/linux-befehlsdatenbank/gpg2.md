---
id: "gpg2"
name: "gpg2"
command: "gpg2"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["gpg2", "firewall & sicherheit"]
status: "Programmnamen und GnuPG-Handbuch geprüft; keine zweite Kryptografieprüfung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 317
reviewed_at: "2026-11-13"
locally_checked_version: "gpg2 nicht installiert; gpg meldet GnuPG 2.4.4"
---

# gpg2 – den GnuPG-2-Aufruf distributionsgerecht einordnen

## 1. Kurzbeschreibung

`gpg2` ist auf manchen Distributionen ein Programmname für GnuPG 2. Auf anderen heißt dieselbe Programmgeneration einfach `gpg`. **Für eigene Dateien und Schlüssel sind keine Root-Rechte nötig.** Der zusätzliche Namensbestandteil bedeutet keine automatisch höhere Vertrauenswürdigkeit.

Lokal ist `gpg2` nicht vorhanden, während `gpg --version` GnuPG `2.4.4` meldet. Die moderne Generation ist also vorhanden, obwohl der zweite Name fehlt.

## 2. Was macht der Befehl?

Wenn der Name eine entsprechende GnuPG-Installation bezeichnet, stehen OpenPGP-Verschlüsselung, Signaturen und Schlüsselverwaltung zur Verfügung. Die genaue Funktionsmenge richtet sich nach der Version, nicht allein nach der Ziffer im Dateinamen.

Das [offizielle GnuPG-Handbuch zum Aufruf](https://www.gnupg.org/documentation/manuals/gnupg/Invoking-GPG.html) beschreibt die Programmgenerationen. Die lokale `gpg`-Hilfe wurde bereits für den zugehörigen Eintrag gelesen. Eine doppelte Untersuchung persönlicher Schlüssel oder ein zweiter vermeintlich unabhängiger Kryptografietest wurde nicht vorgenommen.

Ein Alias oder eine Verknüpfung wäre zunächst eine Namenszuordnung. Zwei solche Aufrufe sind nicht automatisch zwei unabhängige Implementierungen.

## 3. Syntax

```text
gpg2 [OPTIONEN] AKTION [DATEIEN]
gpg2 --version
gpg2 --verify SIGNATURDATEI DATENDATEI
```

Diese Formen gelten nur, wenn `gpg2` tatsächlich installiert ist. Auf dem geprüften Rechner wird nicht eigenmächtig eine Systemverknüpfung angelegt, um den Namen künstlich verfügbar zu machen.

## 4. Wichtige Optionen

| Form | Zweck | Abgrenzung |
| --- | --- | --- |
| `--version` | Tatsächliche Version feststellen. | Programmname allein reicht nicht. |
| `--help` | Lokale Bedienung anzeigen. | Gilt für die aufgerufene Installation. |
| `--verify` | Signatur prüfen. | Daten und erwarteten Schlüssel ausdrücklich zuordnen. |
| `--encrypt` | Für Empfänger verschlüsseln. | Richtige öffentliche Schlüssel nötig. |
| `--decrypt` | Entschlüsseln. | Erzeugt schutzbedürftigen Klartext. |
| `--detach-sign` | Separate Signatur erzeugen. | Benötigt eigenen geheimen Schlüssel. |
| `--homedir VERZEICHNIS` | Datenbereich wählen. | Übungen von persönlichen Beständen trennen. |

Ein neueres Onlinehandbuch kann Funktionen enthalten, die eine ältere lokale GnuPG-2-Version noch nicht bietet. Solche Optionen nicht ohne Versionsabgleich übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Die Generation feststellen

```bash
gpg --version
```

Diese Ausgabe wurde lokal bereits geprüft: `gpg (GnuPG) 2.4.4`. Sie zeigt, dass hier der Name `gpg` zur zweiten Generation gehört. Für die Namensfrage ist damit kein Schlüsselzugriff erforderlich.

### Schritt 2: Eine fremde Anleitung übertragen

Eine Anleitung könnte `gpg2 --verify archiv.sig archiv.tar` nennen. Vor einer Übernahme prüfen, ob der vorhandene `gpg` die benötigte Aktion unterstützt. Dann beide tatsächlichen Dateien ausdrücklich nennen. Nicht nur die Signaturdatei angeben und auf eine automatische Dateizuordnung vertrauen.

### Schritt 3: Den Prüfstand ehrlich begrenzen

Die Anleitung wurde hier nicht mit einem echten Release ausgeführt. Es wurde kein Herausgeberschlüssel geladen und keine Signatur geprüft. Der Nachweis betrifft die lokale Programmversion und das Fehlen des alternativen Namens.

## 6. Typische Anwendungsfälle

- Anleitungen zwischen Distributionen übertragen.
- Einen vorhandenen modernen `gpg`-Aufruf von einer alten Programmgeneration unterscheiden.
- Skripte an ausdrücklich unterstützte Installationen anpassen.
- Mehrere GnuPG-Installationen vor einer Nutzung sauber zuordnen.

Bei mehreren Installationen außerdem den konkreten Programmpfad und Datenbereich festhalten. Andernfalls kann ein Test unbeabsichtigt einen anderen Schlüsselbestand oder eine andere Version verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Ersatzprogramme nicht aus beliebigen Quellen installieren, nur weil eine Anleitung `gpg2` schreibt. Zunächst die vorhandene Installation prüfen. Eine fremde ausführbare Datei gleichen Namens ist keine verlässliche GnuPG-Installation.

Die inhaltlichen Risiken bleiben dieselben: falsche Empfänger, verlorene Schlüssel, veröffentlichte Geheimnisse oder eine gültige Signatur des falschen Schlüssels. Die Namensziffer löst keines dieser Probleme.

## 8. Häufige Fehler

- **„gpg2 fehlt, also kein GnuPG 2“:** Die Ausgabe von `gpg --version` prüfen.
- **Zwei Namen als unabhängige Bestätigung:** Möglicherweise dieselbe Installation.
- **Beliebige Verknüpfung anlegen:** Löst keine Versions- oder Vertrauensfrage.
- **Option unbekannt:** Installierte Versionsnummer mit dem passenden Handbuch abgleichen.
- **Gute Signatur falsch zugeordnet:** Erwarteten vollständigen Fingerabdruck separat bestätigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Den vorhandenen, dokumentierten Distributionsaufruf verwenden. Für Übungen einen getrennten Datenbereich und unwichtige Dateien wählen. Keine persönlichen Schlüsselbestände für eine reine Kompatibilitätsfrage verändern.

Die ausführliche Bedienung und der tatsächlich getestete eigene Hashaufruf stehen im Eintrag `gpg`. Dieser Eintrag ergänzt die Namens- und Versionsfrage, ohne denselben Test als neue unabhängige Prüfung auszugeben.

## 10. Verwandte Befehle

- `gpg`: Üblicher Name auch für GnuPG 2.
- `gpg1`: Möglicher gesonderter Name für die ältere Generation.
- `gpgv`: Gezielte Signaturprüfung.
- `gpg-agent`: Begleitdienst für bestimmte Schlüsseloperationen.

**Prüfstand:** `gpg2` fehlt lokal; `gpg` ist Version 2.4.4. Keine Neuinstallation, Systemverknüpfung oder persönliche Schlüsseloperation durchgeführt.

Ausgangsdatensatz 317 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
