---
id: "wget"
name: "wget"
command: "wget"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "download", "http", "spiegeln"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 175
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Wget 1.21.4 (Paket wget 1.21.4-1ubuntu4.5); nur Version und Schema-Prüfung"
---

# wget – Dateien und ganze Webseiten nicht-interaktiv herunterladen

## 1. Kurzbeschreibung

GNU `wget` lädt Dateien über **HTTP, HTTPS und FTP** herunter, ohne Benutzereingriff. Es eignet sich für Skripte, setzt abgebrochene Downloads fort und kann Webseiten rekursiv **spiegeln**. Anders als `curl` speichert `wget` standardmäßig in eine Datei.

**Root-Rechte sind nicht nötig.** Du brauchst Schreibrechte im Zielordner.

Grundlage ist die [Debian-Manpage zu wget](https://manpages.debian.org/trixie/wget/wget.1.en.html).

## 2. Was macht der Befehl?

`wget URL` lädt die Datei in den aktuellen Ordner und benennt sie nach dem letzten Teil der URL.

**Vorhandene Dateien:** Laut Manpage wird ohne `-N`, `-nc`, `-r` oder `-p` eine vorhandene Datei **nicht überschrieben**; die neue Kopie heißt `datei.1`, `datei.2` usw. Mit `-nc` lädt `wget` gar nicht erneut, mit `-N` nur, wenn die Serverfassung neuer ist. `-O DATEI` dagegen schreibt immer in die genannte Datei und ersetzt sie.

**Rekursion:** Mit `-r` folgt `wget` Links (Vorgabetiefe 5), mit `-m` spiegelt es eine Seite unbegrenzt tief mit Zeitstempelvergleich.

Lokale `file://`-URLs unterstützt `wget` nicht; im Test meldete es `Unsupported scheme.`

## 3. Syntax

```text
wget [OPTIONEN] URL ...
wget [OPTIONEN] -i LISTE.txt
```

```bash
wget https://example.org/datei.iso
wget -c https://example.org/datei.iso
wget -O liste.txt https://example.org/download?id=1
wget -r -l 1 -np https://example.org/doku/
```

Das bisherige NetMon-Beispiel `wget --help` zeigt die Optionsübersicht. Der Platzhalter `wget [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-O DATEI` | Ausgabe in diese Datei (`-` = Standardausgabe). | Überschreibt; bei mehreren URLs wird alles aneinandergehängt. |
| `-P ORDNER` | Zielordner. | – |
| `-c`, `--continue` | Teilweise geladene Datei fortsetzen. | – |
| `-nc`, `--no-clobber` | Vorhandene Dateien nicht erneut laden. | – |
| `-N` | Nur laden, wenn die Serverfassung neuer ist. | – |
| `-q`, `-nv` | Still bzw. knappe Ausgabe. | – |
| `-i DATEI` | URLs aus Datei. | – |
| `--spider` | Nur prüfen, ob die Seiten existieren. | Lädt nichts. |
| `-r`, `-l TIEFE` | Rekursiv mit Tiefe (Vorgabe 5). | Kann sehr viel laden. |
| `-np`, `--no-parent` | Nicht in übergeordnete Ordner wechseln. | Begrenzung bei Rekursion. |
| `-m`, `--mirror` | Spiegeln: `-r -N -l inf` und mehr. | – |
| `-k`, `-p` | Links für lokale Ansicht umschreiben bzw. Bilder/Stile mitladen. | Für Offline-Kopien. |
| `-w SEKUNDEN`, `--limit-rate=20k` | Warten zwischen Abrufen bzw. Geschwindigkeit begrenzen. | Schont Server. |
| `--user`, `--ask-password` | Anmeldung. | `--password` steht im Verlauf. |
| `--no-check-certificate` | Zertifikatsprüfung abschalten. | Nur in Ausnahmefällen. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Datei laden, einen Abbruch fortsetzen und die Prüfsumme kontrollieren. Das braucht Netzwerkzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Zielordner und Download

```bash
uebung="$(mktemp -d -t netmon-wget-XXXXXX)" || exit 1
wget -P "$uebung" https://example.org/abbild.iso
```

### Schritt 2: Fortsetzen nach Abbruch

```bash
wget -c -P "$uebung" https://example.org/abbild.iso
```

`-c` setzt die vorhandene Teildatei fort, statt `abbild.iso.1` anzulegen.

### Schritt 3: Prüfen

```bash
sha256sum "$uebung/abbild.iso"
```

Den Wert mit der vom Anbieter veröffentlichten Prüfsumme vergleichen.

### Schritt 4: Nur Erreichbarkeit prüfen

```bash
wget --spider https://example.org/abbild.iso
echo $?
```

`0` bedeutet: vorhanden; `8` laut Manpage: Server meldet einen Fehler (etwa 404).

## 6. Typische Anwendungsfälle

- **Downloads in Skripten** oder auf Servern ohne Browser.
- **Große Dateien** mit Fortsetzbarkeit.
- **Offline-Kopien** von Dokumentationen (`-m -k -p -np`).
- **Linkprüfung** mit `--spider`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `wget` schreibt Dateien, und rekursive Abrufe können sehr groß werden. Der Kopf verwendet `caution`.

- **Rekursion ohne Grenzen** lädt ganze Webseiten, füllt den Speicher und belastet fremde Server. `-l`, `-np`, `-w` und `--limit-rate` verwenden; Nutzungsbedingungen beachten.
- **`-O` überschreibt** vorhandene Dateien.
- **`wget … | sh`** oder das Ausführen geladener Skripte ohne Prüfung.
- **Passwörter** in `--password` oder in der URL erscheinen im Verlauf; `--ask-password` nutzen.
- **`--no-check-certificate`** macht HTTPS angreifbar.
- **Konfigurationsdatei:** `~/.wgetrc` kann Vorgaben setzen, die das Verhalten ändern.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Ursache | Vorgehen |
| --- | --- | --- |
| `Unsupported scheme.` | Schema wie `file://` nicht unterstützt (im Test). | `curl` für lokale Dateien. |
| `4` – Netzwerkfehler | Keine Verbindung, DNS-Fehler. | Netz prüfen. |
| `5` – SSL-Prüfung fehlgeschlagen | Zertifikatsproblem. | Ursache klären, nicht pauschal abschalten. |
| `6` – Anmeldung fehlgeschlagen | Falsche Zugangsdaten. | Prüfen. |
| `8` – Server meldet Fehler | Etwa 404 oder 403. | URL prüfen. |
| Datei heißt `name.1` | Datei existierte bereits. | `-nc`, `-N` oder `-O` bewusst wählen. |

Rückgabewerte laut Manpage; ausgelöst wurde nur `Unsupported scheme.` (Rückgabe 1).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Eigenen Zielordner mit `-P`.**
2. **Prüfsummen vergleichen.**
3. **Rekursion immer begrenzen** (`-l`, `-np`) und Wartezeiten setzen.
4. **Keine Passwörter in der Befehlszeile.**
5. **Geladene Skripte vor dem Ausführen lesen.**

### Prüfstand

- **Geprüfte Version:** GNU Wget 1.21.4 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `wget --version`; Abruf einer eigenen `file://`-Datei (abgelehnt mit `Unsupported scheme.`, Rückgabe 1).
- **Nicht geprüft:** alle Netzwerkabrufe, Fortsetzen, Rekursion, Rückgabewerte außer 1.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `curl` | Universeller Client, Ausgabe standardmäßig auf dem Terminal. |
| `aria2c` | Downloads über mehrere Verbindungen und BitTorrent. |
| `sha256sum` | Prüfsummen vergleichen. |
| `rsync` | Abgleich ganzer Verzeichnisse über SSH. |

Ausgangseintrag: Datensatz 175 in `index.json` (`wget`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Speicher- und Überschreibregeln, Rekursion, Optionen, Rückgabewerte und einen Downloadablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
