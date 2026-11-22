---
id: "aria2c"
name: "aria2c"
command: "aria2c"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "download", "bittorrent"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 151
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# aria2c – Dateien über mehrere Verbindungen und Protokolle herunterladen

## 1. Kurzbeschreibung

`aria2c` ist das Kommandozeilenprogramm von **aria2**, einem Download-Werkzeug für HTTP(S), FTP, SFTP, BitTorrent und Metalink. Es kann eine Datei über **mehrere Verbindungen und Quellen gleichzeitig** laden, unterbrochene Downloads fortsetzen und Prüfsummen kontrollieren.

**Root-Rechte sind nicht nötig.** Du brauchst nur Schreibrechte im Zielordner.

Grundlage ist die [Debian-Manpage zu aria2c](https://manpages.debian.org/trixie/aria2/aria2c.1.en.html) (aria2 1.37.0). Auf dem geprüften System ist aria2 nicht installiert.

## 2. Was macht der Befehl?

`aria2c URL` lädt die Datei in den aktuellen Ordner. Besonderheiten laut Manpage:

- **Segmentierte Downloads:** Mit `-s` und `-x` wird eine Datei in Teilen über mehrere Verbindungen geladen.
- **Mehrere Quellen:** Mehrere URLs für dieselbe Datei werden gemeinsam genutzt.
- **Steuerdatei:** Während des Downloads entsteht eine Datei `NAME.aria2`, mit der sich der Download fortsetzen lässt.
- **Dateinamenskonflikte:** Existiert die Zieldatei schon, benennt `aria2c` die neue standardmäßig um (`--auto-file-renaming`, Vorgabe `true`) und hängt eine Nummer an.
- **BitTorrent:** Bei Torrents **lädt `aria2c` auch hoch**. Nach Abschluss wird standardmäßig weiter geteilt („seeding“), bis ein Teilungsverhältnis von 1,0 erreicht ist (`--seed-ratio`, Vorgabe `1.0`). DHT ist standardmäßig aktiv.
- **Fernsteuerung:** Mit `--enable-rpc` startet ein JSON-RPC/XML-RPC-Server.

## 3. Syntax

```text
aria2c [OPTIONEN] URL ...
aria2c [OPTIONEN] -i LISTE.txt
aria2c [OPTIONEN] DATEI.torrent
```

```bash
aria2c https://example.org/datei.iso
aria2c -c -d ~/Downloads https://example.org/datei.iso
aria2c -x 4 -s 4 https://example.org/datei.iso
```

Das bisherige NetMon-Beispiel `aria2c --help` zeigt laut Manpage die Grundoptionen (Vorgabe `#basic`); `--help=#all` oder etwa `--help=#bittorrent` zeigen weitere Gruppen. Der Platzhalter `aria2c [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-d ORDNER`, `--dir` | Zielordner. | – |
| `-o NAME`, `--out` | Dateiname, relativ zu `--dir`. | – |
| `-c`, `--continue` | Teilweise geladene Datei fortsetzen. | Nur HTTP(S)/FTP. |
| `-x N`, `--max-connection-per-server` | Verbindungen pro Server (Vorgabe 1). | Viele Verbindungen belasten den Server. |
| `-s N`, `--split` | Datei über N Verbindungen laden. | – |
| `-i DATEI`, `--input-file` | URLs aus einer Datei laden. | – |
| `--checksum=TYP=WERT` | Prüfsumme prüfen, etwa `sha-256=...`. | Nur HTTP(S)/FTP. |
| `--max-download-limit`, `--max-overall-upload-limit` | Geschwindigkeit begrenzen. | `K`/`M` als Einheit. |
| `--allow-overwrite` | Ohne Steuerdatei von vorn beginnen. | Vorgabe `false`. |
| `--auto-file-renaming` | Bei vorhandener Datei umbenennen. | Vorgabe `true`. |
| `--dry-run` | Nur prüfen, ob die Datei verfügbar ist. | Bricht BitTorrent ab. |
| `--seed-time=MINUTEN`, `--seed-ratio=WERT` | Teilen nach dem Download begrenzen. | `--seed-time=0` beendet das Teilen sofort. **Prüfpunkt:** nicht geprüft. |
| `--follow-torrent=true/false/mem` | Geladene `.torrent`-Dateien automatisch ausführen. | – |
| `--enable-rpc`, `--rpc-secret`, `--rpc-listen-all` | Fernsteuerung. | Laut Manpage dringend mit Geheimnis; Vorgabe nur lokal. |
| `--check-certificate` | Zertifikatsprüfung (Vorgabe `true`). | Nicht abschalten. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine große Datei mit Prüfsumme laden und einen abgebrochenen Download fortsetzen. Das braucht Netzwerkzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verfügbarkeit prüfen

```bash
aria2c --dry-run https://example.org/abbild.iso
```

Prüft nur, ob die Datei erreichbar ist.

### Schritt 2: Herunterladen mit Prüfsumme

```bash
aria2c -d ~/Downloads -x 4 -s 4 --checksum=sha-256=PRÜFSUMME https://example.org/abbild.iso
```

`PRÜFSUMME` ist der vom Anbieter veröffentlichte SHA-256-Wert. Stimmt er nicht, meldet `aria2c` einen Fehler (Rückgabewert 32).

### Schritt 3: Abbruch und Fortsetzung

Bricht der Download ab (etwa mit Strg+C), bleiben `abbild.iso` und `abbild.iso.aria2` liegen. Derselbe Befehl, ergänzt um `-c`, setzt fort:

```bash
aria2c -c -d ~/Downloads -x 4 -s 4 --checksum=sha-256=PRÜFSUMME https://example.org/abbild.iso
```

## 6. Typische Anwendungsfälle

- **Große Dateien** schneller oder stabiler laden.
- **Listen von Downloads** mit `-i`.
- **Torrents und Magnet-Links** ohne grafisches Programm.
- **Fernsteuerung** über grafische Oberflächen, die die RPC-Schnittstelle nutzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `aria2c` schreibt Dateien, und bei BitTorrent werden Daten hochgeladen. Der Kopf verwendet `caution`.

- **Upload bei BitTorrent:** Standardmäßig teilt `aria2c` nach dem Download weiter. Deine IP-Adresse ist für andere Teilnehmer sichtbar; rechtliche Folgen hängen vom Inhalt ab.
- **RPC-Schnittstelle:** Ohne `--rpc-secret` und mit `--rpc-listen-all` kann jeder im Netz Downloads auslösen – auch in beliebige beschreibbare Ordner.
- **Serverlast:** Viele parallele Verbindungen (`-x`, `-s`) können gegen Nutzungsbedingungen verstoßen oder zu Sperren führen.
- **Ungeprüfte Dateien:** Ohne `--checksum` keine Gewähr für Unverfälschtheit; heruntergeladene Programme nicht ungeprüft ausführen.
- **Speicherplatz:** Große Dateien können das Ziel füllen (Rückgabewert 9).
- **`--allow-overwrite`** kann vorhandene Dateien ersetzen.

## 8. Häufige Fehler

Rückgabewerte laut Manpage (Auswahl):

| Code | Bedeutung | Vorgehen |
| --- | --- | --- |
| `0` | Alle Downloads erfolgreich. | – |
| `3` | Ressource nicht gefunden. | URL prüfen. |
| `6` | Netzwerkproblem. | Verbindung prüfen. |
| `7` | Unfertige Downloads beim Beenden. | Mit `-c` fortsetzen. |
| `9` | Nicht genug Speicherplatz. | Platz schaffen. |
| `13` | Datei existierte bereits. | Umbenennung oder `--allow-overwrite` bewusst wählen. |
| `19` | Namensauflösung fehlgeschlagen. | DNS prüfen. |
| `24` | HTTP-Anmeldung fehlgeschlagen. | Zugangsdaten prüfen. |
| `28` | Unbekannte Option oder falsches Argument. | Aufruf prüfen. |
| `32` | Prüfsumme stimmt nicht. | Datei verwerfen, Quelle prüfen. |

Laut Manpage meldet `aria2c` den Rückgabewert des **letzten** aufgetretenen Fehlers; Fehler in bereits abgeschlossenen Downloads erscheinen nicht.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Immer mit `--checksum`** laden, wenn der Anbieter eine Prüfsumme veröffentlicht.
2. **Bei Torrents `--seed-time` oder `--seed-ratio`** bewusst setzen.
3. **RPC nur mit `--rpc-secret`** und ohne `--rpc-listen-all`.
4. **Moderate Verbindungszahl** (`-x 4` statt Höchstwert).
5. **Eigenen Zielordner** mit `-d`.

### Prüfstand

- **Geprüfte Version:** keine; aria2 ist nicht installiert. Die Debian-Manpage beschreibt 1.37.0.
- **Quellen gelesen:** Debian-Manpage `aria2c(1)` (Beschreibung, Optionen, Steuerdatei, BitTorrent-Vorgaben, Rückgabewerte), Abruf 2026-11-13.
- **Nicht geprüft:** alle Downloads, Fortsetzen, BitTorrent-Verhalten, RPC.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `wget` | Einfache Downloads, rekursives Spiegeln. |
| `curl` | Universeller HTTP-Client, auch für APIs. |
| `sha256sum` | Prüfsummen nach dem Download kontrollieren. |
| `rsync` | Abgleich von Dateien zwischen Rechnern. |

Ausgangseintrag: Datensatz 151 in `index.json` (`aria2c`, Kategorie „DNS & Internet“, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Protokolle, Segmentierung, BitTorrent-Upload, RPC-Risiken und Rückgabewerte ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben, weil `aria2c` Dateien schreibt und bei BitTorrent Daten hochlädt.
