---
id: "gpg"
name: "gpg"
command: "gpg"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "caution"
tags: ["gpg", "firewall & sicherheit"]
status: "Hilfe, Manpage und eigener SHA-256-Beispielaufruf geprüft; keine persönlichen Schlüssel verwendet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 316
reviewed_at: "2026-11-13"
locally_checked_version: "GnuPG 2.4.4; libgcrypt 1.10.3"
---

# gpg – OpenPGP-Verschlüsselung, Signaturen und Schlüssel verstehen

## 1. Kurzbeschreibung

`gpg` ist der OpenPGP-Teil von GnuPG. Es kann Daten verschlüsseln, entschlüsseln, signieren und Signaturen prüfen. Außerdem verwaltet es Schlüssel. Diese Aufgaben haben unterschiedliche Voraussetzungen und dürfen nicht gleichgesetzt werden.

**Root-Rechte sind für die übliche Arbeit mit eigenen Dateien und eigenen Schlüsseln nicht nötig.** Der Aufruf als Root würde einen anderen Kontext und zusätzliche Risiken schaffen.

## 2. Was macht der Befehl?

Verschlüsselung schützt den Inhalt gegenüber Personen ohne den passenden Schlüssel oder das Passwort. Eine Signatur bindet Daten an einen Signaturschlüssel. Ob dieser Schlüssel zur erwarteten Person oder zum erwarteten Herausgeber gehört, muss gesondert geklärt werden.

Das [GnuPG-Kapitel zum Programmaufruf](https://www.gnupg.org/documentation/manuals/gnupg/Invoking-GPG.html) ordnet das Werkzeug ein. Die Kapitel [Operationen](https://www.gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html) und [Ein- und Ausgabe](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Input-and-Output.html) erklären die jeweiligen Funktionen. Zusätzlich wurden lokale Hilfe und Manpage für GnuPG `2.4.4` betrachtet.

Ein heruntergeladener Schlüssel ist nicht schon deshalb vertrauenswürdig, weil sein angezeigter Name richtig aussieht. Der erwartete vollständige Fingerabdruck braucht einen geeigneten unabhängigen Bestätigungsweg.

## 3. Syntax

```text
gpg [OPTIONEN] AKTION [DATEIEN]
gpg --verify SIGNATURDATEI DATENDATEI
gpg --output ZIEL --encrypt --recipient EMPFÄNGER QUELLE
gpg --output ZIEL --decrypt VERSCHLÜSSELTE_DATEI
```

Bei einer abgetrennten Signatur beide Dateien ausdrücklich nennen. So bleibt klar, welche Bytes geprüft werden. Eine gute Signatur für Datei A sagt nichts über eine anschließend ersetzte Datei B aus.

## 4. Wichtige Optionen

| Form | Aufgabe | Voraussetzung oder Folge |
| --- | --- | --- |
| `--verify` | Signatur prüfen. | Erwarteten Schlüssel und Datenbezug klären. |
| `--encrypt` | Für öffentliche Empfängerschlüssel verschlüsseln. | Richtige Empfänger auswählen. |
| `--recipient` | Empfänger bestimmen. | Namen können mehrdeutig sein. |
| `--symmetric` | Mit Passwort verschlüsseln. | Starkes Passwort und sicherer Austausch nötig. |
| `--decrypt` | Entschlüsseln. | Klartext kann sichtbar oder gespeichert werden. |
| `--detach-sign` | Separate Signatur erzeugen. | Benötigt geeigneten eigenen geheimen Schlüssel. |
| `--armor` | Textdarstellung erzeugen. | Keine zusätzliche Verschlüsselungsstärke. |
| `--output DATEI` | Ausgabeziel festlegen. | Bestehende Dateien schützen. |
| `--homedir VERZEICHNIS` | Eigenen GnuPG-Datenbereich wählen. | Für isolierte Übungen hilfreich. |
| `--print-md SHA256` | SHA-256-Digest berechnen. | Hash allein ist keine Signatur. |

Schlüsselimport und -export verändern beziehungsweise verbreiten Daten. Insbesondere geheime Schlüssel nie versehentlich exportieren oder in Supportanfragen einfügen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen eigenen Übungsbereich anlegen

```bash
(
  umask 077
  uebung="$(mktemp -d -t netmon-gpg-XXXXXX)" || exit 1
  mkdir -m 700 "$uebung/gnupg" || exit 1
  printf 'NetMon GPG Beispiel\n' > "$uebung/notiz.txt" || exit 1
  gpg --no-options --homedir "$uebung/gnupg" --batch \
    --print-md SHA256 "$uebung/notiz.txt"
)
```

Der neue Bereich und seine Datei gehören nur zur Übung. Der Aufruf nutzt keine persönliche Schlüsselablage. `--no-options` vermeidet die gewöhnliche Optionsdatei; der eigene Datenbereich trennt außerdem die Übung von persönlichen Schlüsseln.

### Schritt 2: Den Digest lesen

Der entsprechende GPG-Aufruf wurde lokal mit einer neu angelegten eigenen Datei ausgeführt und mit `hashlib.sha256` verglichen. Status `0`; der Digest lautete, ohne Anzeigeleerzeichen:

```text
4fc5ce0de63c103eb145e0f7206ea0b6e9605ef047b873915fddf87ce133a4b5
```

GPG legte dabei eine neue Keybox im eigenen Übungsbereich an. Der Vorgang war also nicht vollständig schreibfrei, obwohl keine Schlüssel erzeugt oder importiert wurden.

### Schritt 3: Den Beweisumfang begrenzen

Der Digest identifiziert diesen Dateiinhalt zum Prüfzeitpunkt. Er beweist weder Herkunft noch Ungefährlichkeit. Die Übung ist ein erfolgreicher Hashaufruf, kein getesteter Verschlüsselungs- oder Signaturablauf.

## 6. Typische Anwendungsfälle

- Ein freigegebenes Release mit bekannter Herausgebersignatur prüfen.
- Eigene Daten für festgelegte Empfänger verschlüsseln.
- Eine separate Signatur für eigene Dokumente erzeugen.
- Schlüsselbestände mit überprüften Fingerabdrücken verwalten.

Für automatisierte Prüfungen reicht ein menschlich lesbarer Satz wie „Gute Signatur“ nicht. Erwartete Identität, tatsächlich geprüfte Daten und maschinenlesbare Statusinformationen müssen zusammenpassen. Dafür können eine kontrollierte Schlüsselmenge und `gpgv` geeigneter sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

Verschlüsselung ersetzt keine Sicherung. Gehen Schlüssel oder Passwort verloren, können eigene Daten unlesbar bleiben. Beim Entschlüsseln entsteht wieder schutzbedürftiger Klartext.

Passwörter nicht als direkt sichtbare Befehlsargumente eintippen oder in Beispiele mit echten Geheimnissen übernehmen. Shellverlauf, Prozessinformationen und weitergegebene Protokolle können sonst Informationen offenlegen.

Ein Schlüsselserverabruf ist ein Netzwerkzugriff; Schlüsselversand kann Daten dauerhaft verbreiten. Solche Vorgänge werden durch die Übung nicht ausgelöst. Auch ein importierter öffentlicher Schlüssel ist zunächst nur gespeichertes Schlüsselmaterial, keine bestätigte Identität.

## 8. Häufige Fehler

- **Kein öffentlicher Schlüssel:** Prüfung kann nicht abschließend erfolgen; keine gute Signatur behaupten.
- **Schlechter Signaturstatus:** Datei, Signatur und Herkunft untersuchen; nicht Warnungen unterdrücken.
- **Gültige Signatur, falscher Schlüssel:** Erwarteten Fingerabdruck prüfen.
- **Falscher Empfänger:** Die eigene Entschlüsselbarkeit ist nicht automatisch gewährleistet.
- **Klartext unerwartet im Terminal:** Ausgabeziel vor dem Entschlüsseln festlegen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem getrennten Datenbereich und unwichtigen eigenen Dateien üben. Originale erhalten, Ziele eindeutig benennen und vor produktiver Nutzung einen vollständigen Wiederherstellungsweg verstehen.

Nicht sämtliche GPG-Vorgänge unter einem pauschalen „sicher“-Etikett zusammenfassen. Signieren, Verschlüsseln und Hashen lösen unterschiedliche Probleme.

## 10. Verwandte Befehle

- `gpg2`: Distributionsabhängiger alternativer Programmname für GnuPG 2.
- `gpgv`: Signaturprüfung mit einem vorgesehenen Vertrauensbestand.
- `gpg-agent`: Verwaltet bestimmte Schlüsseloperationen und Passwortabfragen.
- `sha256sum`: Einfacher Dateidigest ohne OpenPGP-Schlüsselverwaltung.
- `minisign`: Anderes Signaturformat; nicht mit GPG austauschbar.

**Prüfstand:** Lokale Version, Hilfe, Manpage und isolierter Hashaufruf geprüft. Kein persönlicher Schlüssel gelesen, erzeugt oder exportiert; keine Signatur oder Verschlüsselung als praktisch getestet ausgegeben.

Ausgangsdatensatz 316 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
