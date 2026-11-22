---
id: "ssh_keygen"
name: "ssh-keygen"
command: "ssh-keygen"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "schluessel", "kryptografie"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testschlüsseln geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 172
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# ssh-keygen – SSH-Schlüssel erzeugen, prüfen und verwalten

## 1. Kurzbeschreibung

`ssh-keygen` erzeugt **SSH-Schlüsselpaare** (privat und öffentlich), zeigt deren Fingerabdrücke an, ändert Passphrasen und verwaltet die Datei `known_hosts`. Laut [Debian-Manpage zu ssh-keygen](https://manpages.debian.org/trixie/openssh-client/ssh-keygen.1.en.html) führt jeder Benutzer, der sich per Schlüssel anmelden möchte, es normalerweise einmal aus; Verwalter erzeugen damit auch Hostschlüssel.

**Root-Rechte sind für eigene Schlüssel nicht nötig.** Hostschlüssel unter `/etc/ssh/` gehören Root.

## 2. Was macht der Befehl?

Ohne Optionen fragt `ssh-keygen` nach Dateiname und Passphrase und erzeugt ein Schlüsselpaar: den **privaten Schlüssel** (zum Beispiel `~/.ssh/id_ed25519`) und den **öffentlichen** mit angehängtem `.pub`. Laut Debian-Manpage ist `ed25519` der Standardtyp.

Weitere Aufgaben:

| Aufgabe | Aufruf |
| --- | --- |
| Fingerabdruck anzeigen | `ssh-keygen -l -f DATEI.pub` |
| Öffentlichen aus privatem Schlüssel ableiten | `ssh-keygen -y -f DATEI` |
| Passphrase ändern | `ssh-keygen -p -f DATEI` |
| Host in `known_hosts` suchen | `ssh-keygen -F HOST` |
| Host aus `known_hosts` entfernen | `ssh-keygen -R HOST` |

Die Datei des privaten Schlüssels erhält die Rechte `600`; im Test hatte die `.pub`-Datei `640` (abhängig von der umask).

## 3. Syntax

```text
ssh-keygen [-t TYP] [-b BITS] [-C KOMMENTAR] [-f DATEI] [-N PASSPHRASE]
ssh-keygen -l [-v] [-E md5|sha256] -f DATEI
ssh-keygen -p [-f DATEI] [-P ALT] [-N NEU]
ssh-keygen -F HOST | -R HOST [-f KNOWN_HOSTS]
```

```bash
ssh-keygen -t ed25519 -C "anna@laptop"
ssh-keygen -l -f ~/.ssh/id_ed25519.pub
ssh-keygen -p -f ~/.ssh/id_ed25519
ssh-keygen -R server.example.org
```

Das bisherige NetMon-Beispiel `ssh-keygen --help` ist keine dokumentierte Option. **Prüfpunkt:** Verhalten nicht geprüft. Der Platzhalter `ssh-keygen [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-t TYP` | Schlüsseltyp: `ed25519`, `ecdsa`, `rsa`, `ed25519-sk`, `ecdsa-sk`. | `-sk` für Hardware-Schlüssel (FIDO). |
| `-b BITS` | Schlüssellänge. | RSA laut Manpage mindestens 1024, Vorgabe 3072. |
| `-C TEXT` | Kommentar, etwa Konto und Rechner. | Erscheint in `authorized_keys`. |
| `-f DATEI` | Dateiname. | – |
| `-N TEXT`, `-P TEXT` | Neue bzw. alte Passphrase angeben. | Steht dann in Verlauf und Prozessliste; interaktiv sicherer. |
| `-a RUNDEN` | Runden der Schlüsselableitung. | Mehr Runden erschweren das Erraten der Passphrase. |
| `-p` | Passphrase ändern. | Schlüssel selbst bleibt gleich. |
| `-l`, `-v` | Fingerabdruck, mit Bild. | – |
| `-E md5/sha256` | Hashverfahren des Fingerabdrucks. | Vorgabe `sha256`. |
| `-y` | Öffentlichen Schlüssel aus dem privaten ausgeben. | Prüft zugleich die Passphrase. |
| `-c` | Kommentar ändern. | – |
| `-F HOST`, `-R HOST` | Host in `known_hosts` suchen bzw. entfernen. | Auch `[host]:port`. |
| `-q` | Ohne Ausgaben. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein Testschlüsselpaar erzeugen, prüfen, mit Passphrase versehen und den Fingerabdruck lesen – alles in einem Übungsordner, ohne die echten Schlüssel in `~/.ssh` zu berühren.

### Schritt 1: Erzeugen

```bash
uebung="$(mktemp -d -t netmon-keygen-XXXXXX)" || exit 1
cd "$uebung" || exit 1
ssh-keygen -q -t ed25519 -N '' -C 'uebung@netmon' -f ./uebung_key
ls -l
```

Es entstehen `uebung_key` (Rechte `-rw-------`) und `uebung_key.pub`. `-N ''` (keine Passphrase) nur für diese Übung.

### Schritt 2: Fingerabdruck

```bash
ssh-keygen -l -f uebung_key.pub
```

Ausgabe: `256 SHA256:… uebung@netmon (ED25519)`.

### Schritt 3: Passphrase setzen und prüfen

```bash
ssh-keygen -p -f uebung_key
ssh-keygen -y -f uebung_key
```

`-p` fragt nach alter (leer) und neuer Passphrase. `-y` gibt den öffentlichen Schlüssel nur aus, wenn die Passphrase stimmt. Im Test wurden Passphrasen mit `-P`/`-N` übergeben; interaktiv ist das sicherer.

### Schritt 4: Überschreiben vermeiden

Ein erneuter Aufruf mit demselben Dateinamen fragt `uebung_key already exists. Overwrite (y/n)?`. **Mit `y` wäre der alte private Schlüssel unwiederbringlich verloren.**

## 6. Typische Anwendungsfälle

- **Erstmaliges Einrichten** der Schlüsselanmeldung.
- **Fingerabdrücke vergleichen,** etwa einen Hostschlüssel auf dem Server mit der Anzeige beim ersten `ssh`.
- **Veralteten Hosteintrag entfernen** nach einer Serverneuinstallation (`-R`) – erst nach Klärung des Grundes.
- **Passphrase nachträglich setzen oder ändern.**
- **Signaturen von Dateien** (`-Y sign`/`-Y verify`). **Prüfpunkt:** nicht geprüft.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft auf `-l` und `-F` zu, nicht auf das Erzeugen. Der Kopf verwendet `caution`.

- **Überschreiben eines vorhandenen Schlüssels** zerstört den Zugang zu allen Servern, die nur diesen Schlüssel kennen.
- **Schlüssel ohne Passphrase:** Wer die Datei bekommt, hat sofort Zugang.
- **Passphrase in der Befehlszeile** (`-N`, `-P`) landet in Verlauf und Prozessliste.
- **`-R` vorschnell:** Ein geänderter Hostschlüssel kann ein Angriff sein; den Eintrag erst nach Prüfung entfernen.
- **Private Schlüssel nie weitergeben** – auf Server kommt nur die `.pub`-Datei.
- **Schwache Typen:** Kurze RSA-Schlüssel und das veraltete DSA nicht mehr verwenden.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `… already exists. Overwrite (y/n)?` | Datei vorhanden (im Test). | `n` und anderen Namen wählen. |
| `incorrect passphrase supplied to decrypt private key` | Falsche Passphrase. | Erneut eingeben (Text im Programm enthalten, nicht ausgelöst). |
| `… is not a public key file.` | Falsches Dateiformat. | Datei prüfen (Text im Programm enthalten, nicht ausgelöst). |
| `UNPROTECTED PRIVATE KEY FILE` bei `ssh` | Zu offene Rechte. | `chmod 600`. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Ed25519 mit Passphrase** verwenden.
2. **Aussagekräftigen Kommentar** mit `-C`.
3. **Vorhandene Schlüssel nie überschreiben.**
4. **Passphrasen interaktiv eingeben.**
5. **Private Schlüssel sichern** (verschlüsselt), öffentliche frei verteilen.

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt** im Testordner: Erzeugen von Ed25519-Schlüsseln, Rechteprüfung, `-l`, `-l -v`, `-y`, `-p` mit `-P`/`-N` (Passphrase setzen und wieder entfernen), Überschreib-Rückfrage, `-F` gegen eine eigene `known_hosts`-Testdatei.
- **Nicht geprüft:** RSA/ECDSA/FIDO, `-R`, `-a`, `-Y sign`, Fehlermeldungen bei falscher Passphrase.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh-copy-id` | Öffentlichen Schlüssel auf Server bringen. |
| `ssh-add`, `ssh-agent` | Schlüssel für eine Sitzung bereithalten. |
| `ssh` | Anmeldung mit dem Schlüssel. |
| `openssl` | Allgemeine Schlüssel und Zertifikate. |

Ausgangseintrag: Datensatz 172 in `index.json` (`ssh-keygen`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Schlüsseltypen, Aufgaben, Optionen, Überschreib- und Passphrasenrisiken und einen geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
