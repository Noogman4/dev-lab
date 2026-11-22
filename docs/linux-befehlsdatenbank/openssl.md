---
id: "openssl"
name: "openssl"
command: "openssl"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "tls", "zertifikate", "kryptografie"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 163
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSL 3.0.13 (Ubuntu-Paket openssl 3.0.13-0ubuntu3.16)"
---

# openssl – Schlüssel, Zertifikate, Prüfsummen und TLS-Tests

## 1. Kurzbeschreibung

`openssl` ist das Kommandozeilenprogramm der **OpenSSL-Kryptografiebibliothek**. Laut [Debian-Manpage zu openssl](https://manpages.debian.org/trixie/openssl/openssl.1ssl.en.html) dient es unter anderem zum Erzeugen und Verwalten von Schlüsseln, zum Erstellen von X.509-Zertifikaten und Zertifikatsanträgen, zum Berechnen von Prüfsummen, zum Ver- und Entschlüsseln sowie zum Testen von SSL/TLS-Clients und -Servern.

**Root-Rechte sind nicht nötig.** Ausnahmen betreffen nur das Schreiben in Systemordner, etwa für Zertifikate von Diensten unter `/etc/ssl/private`.

## 2. Was macht der Befehl?

`openssl` besteht aus vielen **Unterbefehlen**, jeweils mit eigener Manpage (`openssl-UNTERBEFEHL`, etwa `openssl-x509`). Häufig genutzte:

| Unterbefehl | Aufgabe | Wirkung |
| --- | --- | --- |
| `version` | Version anzeigen. | Lesend. |
| `dgst` | Prüfsumme oder Signatur. | Lesend (bei `-out` schreibend). |
| `rand` | Zufallsbytes erzeugen. | – |
| `genpkey` | Privaten Schlüssel erzeugen. | Schreibt eine geheime Datei. |
| `req` | Zertifikatsantrag (CSR) oder selbstsigniertes Zertifikat. | Schreibt Dateien. |
| `x509` | Zertifikate anzeigen und umwandeln. | Lesend oder schreibend. |
| `verify` | Zertifikatskette prüfen. | Lesend. |
| `s_client` | TLS-Verbindung zu einem Server testen. | Netzwerkverbindung. |
| `enc` | Daten symmetrisch ver- und entschlüsseln. | Schreibt Dateien. |
| `pkcs12` | Schlüssel und Zertifikat bündeln. | Schreibt Dateien. |

`openssl help` listet die verfügbaren Unterbefehle.

## 3. Syntax

```text
openssl UNTERBEFEHL [OPTIONEN] [ARGUMENTE]
```

```bash
openssl version
openssl dgst -sha256 datei.iso
openssl x509 -in zertifikat.pem -noout -subject -dates
openssl s_client -connect example.org:443 -servername example.org
```

Das bisherige NetMon-Beispiel `openssl --help` zeigt in Version 3.0.13 dieselbe Befehlsübersicht wie `openssl help` (im Test geprüft); die Hilfe zu einem Unterbefehl liefert `openssl UNTERBEFEHL -help`. Der Platzhalter `openssl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Aufruf | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `dgst -sha256 DATEI` | SHA-256-Prüfsumme. | Gleiches Ergebnis wie `sha256sum`. |
| `rand -hex N` | N Zufallsbytes hexadezimal. | Etwa für Tokens. |
| `genpkey -algorithm ed25519 -out key.pem` | Ed25519-Schlüssel erzeugen. | Mit `umask 077` erzeugen, damit nur du lesen darfst. |
| `req -new -x509 -key K -subj "/CN=NAME" -days N -out C` | Selbstsigniertes Zertifikat. | Für Tests, nicht für öffentliche Dienste. |
| `x509 -in C -noout -text` | Zertifikat vollständig anzeigen. | `-subject`, `-issuer`, `-dates`, `-fingerprint` für Auszüge. |
| `verify -CAfile CA C` | Zertifikat gegen eine CA prüfen. | – |
| `s_client -connect HOST:PORT -servername HOST` | TLS-Verbindung testen. | `-servername` für SNI. |
| `enc -aes-256-cbc -pbkdf2 -in … -out …` | Symmetrisch verschlüsseln. | Siehe Abschnitt 7. |
| `-pass file:DATEI`, `-pass env:VAR` | Passwortquelle angeben. | Siehe `openssl-passphrase-options(1)`; nicht `pass:` in der Befehlszeile. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Prüfsumme berechnen, einen Testschlüssel und ein selbstsigniertes Zertifikat erzeugen und das Zertifikat prüfen. Alles geschieht mit eigenen Dateien in einem Übungsordner.

### Schritt 1: Übungsordner und Prüfsumme

```bash
uebung="$(mktemp -d -t netmon-openssl-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'abc' > d.txt
openssl dgst -sha256 d.txt
```

Ausgabe: `SHA2-256(d.txt)= ba7816bf…15ad` – derselbe Wert wie `sha256sum d.txt`.

### Schritt 2: Privaten Schlüssel erzeugen

```bash
(umask 077; openssl genpkey -algorithm ed25519 -out key.pem)
ls -l key.pem
```

Die Unter-Shell mit `umask 077` sorgt für die Rechte `-rw-------`.

### Schritt 3: Selbstsigniertes Zertifikat

```bash
openssl req -new -x509 -key key.pem -subj "/CN=uebung.local" -days 30 -out cert.pem
openssl x509 -in cert.pem -noout -subject -issuer -dates -fingerprint -sha256
```

Ausgabe: `subject=CN = uebung.local`, gleicher Aussteller, Gültigkeit 30 Tage und der SHA-256-Fingerabdruck.

### Schritt 4: Zertifikat prüfen

```bash
openssl verify -CAfile cert.pem cert.pem
```

Ausgabe: `cert.pem: OK` – das Zertifikat ist mit sich selbst als Vertrauensanker gültig.

## 6. Typische Anwendungsfälle

- **Downloads prüfen** mit `dgst`.
- **Zertifikate von Webservern kontrollieren:** Ablaufdatum, Aussteller, Name.
- **Zertifikatsanträge** für eine Zertifizierungsstelle erstellen.
- **Testzertifikate** für interne Dienste.
- **TLS-Fehlersuche** mit `s_client`.
- **Formate umwandeln** (PEM, DER, PKCS#12).

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft auf Anzeigebefehle zu, nicht auf alle Funktionen. Der Kopf verwendet `caution`:

- **Private Schlüssel schützen:** Dateien mit Schlüsseln dürfen nur für den Eigentümer lesbar sein. Wer den Schlüssel hat, kann sich als der Dienst ausgeben.
- **Passwörter in der Befehlszeile:** `-pass pass:GEHEIM` erscheint in Shell-Verlauf und Prozessliste; besser `file:` oder `env:`.
- **`enc` ist kein vollständiges Verschlüsselungsformat:** Laut [Manpage zu openssl-enc](https://manpages.debian.org/trixie/openssl/openssl-enc.1ssl.en.html) unterstützt `enc` keine authentifizierten Modi (wie GCM) und überlässt die Schlüssel- und IV-Verwaltung dem Benutzer. Für Datenverschlüsselung empfiehlt die Manpage `openssl cms`; für Alltagszwecke ist zum Beispiel `gpg` gängiger. Ohne `-pbkdf2` warnte OpenSSL im Test vor veralteter Schlüsselableitung.
- **Überschreiben:** `-out` ersetzt vorhandene Dateien ohne Rückfrage – auch einen bestehenden Schlüssel.
- **Selbstsignierte Zertifikate** sind nicht vertrauenswürdig für Dritte; Browser warnen zu Recht.
- **Veraltete Verfahren** (MD5, SHA-1, kurze RSA-Schlüssel) nicht für neue Schlüssel oder Signaturen verwenden.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `Could not read certificate from DATEI` / `Unable to load certificate` | Datei ist kein PEM-Zertifikat oder in DER. | Inhalt prüfen; ggf. `-inform DER`. |
| `*** WARNING : deprecated key derivation used.` | `enc` ohne `-pbkdf2` oder `-iter`. | `-pbkdf2` verwenden. |
| `bad decrypt` | Falsches Passwort oder andere Parameter beim Entschlüsseln. | Gleiche Optionen wie beim Verschlüsseln. **Prüfpunkt:** nicht ausgelöst. |
| `unable to get local issuer certificate` | Zwischenzertifikat oder CA fehlt. | Kette oder `-CAfile` prüfen. **Prüfpunkt:** nicht ausgelöst. |
| `certificate has expired` | Ablaufdatum überschritten. | `-dates` prüfen, erneuern. **Prüfpunkt:** nicht ausgelöst. |

Im Test endete `openssl x509` mit einer Nicht-Zertifikatsdatei mit den ersten beiden Meldungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Schlüssel mit `umask 077`** erzeugen.
2. **Passwörter nie mit `pass:`** übergeben.
3. **Zum Anzeigen `-noout`** verwenden, damit nicht zusätzlich der Inhalt ausgegeben wird.
4. **Für Dateiverschlüsselung `gpg` oder `openssl cms`** statt `enc`.
5. **Vorhandene Schlüssel nicht mit `-out` überschreiben;** neue Namen verwenden.

### Prüfstand

- **Geprüfte Version:** OpenSSL 3.0.13 (Ubuntu 24.04-Basis); Debian-Manpages aus trixie.
- **Tatsächlich ausgeführt** im Testordner: `dgst -sha256` (gleich `sha256sum`), `rand -hex 8`, `genpkey` Ed25519 mit `umask 077`, `req -x509` mit `-subj`, `x509 -noout -subject -issuer -dates -fingerprint`, `verify` (OK), `enc -aes-256-cbc -pbkdf2` mit Passwortdatei und Entschlüsselung (bytegleich), `enc` ohne `-pbkdf2` (Warnung), `x509` mit falscher Eingabe (Fehlermeldung), `openssl help`.
- **Nicht geprüft:** `s_client` und alle Netzwerkverbindungen, CSRs für echte CAs, PKCS#12, `cms`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sha256sum` | Prüfsummen ohne OpenSSL. |
| `gnutls-cli`, `certtool` | Entsprechende Werkzeuge aus GnuTLS. |
| `gpg` | Verschlüsselung und Signaturen von Dateien. |
| `ssh-keygen` | Schlüssel für SSH. |
| `curl -v` | Zeigt TLS-Details bei HTTP-Abrufen. |

Ausgangseintrag: Datensatz 163 in `index.json` (`openssl`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Unterbefehle, Optionen, Schlüsselschutz, die Grenzen von `enc` und einen geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
