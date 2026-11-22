---
id: "getcap"
name: "getcap"
command: "getcap"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "safe"
tags: ["benutzer", "rechte", "capabilities", "sicherheit"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 108
reviewed_at: "2026-11-13"
locally_checked_version: "libcap2-bin 1:2.66-5ubuntu2.4"
---

# getcap – Datei-Capabilities von Programmen anzeigen

## 1. Kurzbeschreibung

`getcap` zeigt, welche **Datei-Capabilities** eine Datei trägt. Capabilities sind einzelne Teilrechte von Root, zum Beispiel „Raw-Netzwerkpakete senden“ (`cap_net_raw`) oder „Ports unter 1024 öffnen“ (`cap_net_bind_service`). Ein Programm mit solchen Capabilities erhält beim Start genau diese Teilrechte, ohne als Root zu laufen und ohne setuid-Bit.

**Root-Rechte sind nicht nötig.** `getcap` liest nur. Du brauchst lediglich Zugriff auf die Dateien und Ordner, die du prüfst. Für eine vollständige Durchsuchung des Systems kann `sudo` sinnvoll sein, weil manche Ordner für normale Benutzer nicht lesbar sind.

## 2. Was macht der Befehl?

`getcap` liest das erweiterte Attribut `security.capability` jeder angegebenen Datei und gibt Dateiname und Capabilities in Textform aus. Dateien ohne Capabilities erscheinen nicht, außer mit `-v`. Es verändert nichts.

Beispielausgabe auf dem geprüften System:

```text
/usr/bin/ping cap_net_raw=ep
/usr/bin/dumpcap cap_net_admin,cap_net_raw=ep
```

### Ausgabe lesen

Die Textform ist in der [Debian-Manpage zu cap_from_text(3)](https://manpages.debian.org/trixie/libcap-dev/cap_from_text.3.en.html) beschrieben: Hinter den Namen folgen ein Operator und Buchstaben für die betroffenen Mengen.

| Buchstabe | Menge | Bedeutung |
| --- | --- | --- |
| `p` | Permitted | Das Programm darf diese Capability nutzen. |
| `e` | Effective | Sie ist beim Start sofort aktiv. |
| `i` | Inheritable | Sie kann an weitere Programme weitergegeben werden, wenn deren Datei es erlaubt. |

`cap_net_raw=ep` heißt also: Das Programm startet mit aktiver Berechtigung für Raw- und Packet-Sockets. Was jede Capability erlaubt, beschreibt die [Debian-Manpage zu capabilities(7)](https://manpages.debian.org/trixie/manpages/capabilities.7.en.html).

Die Optionen folgen der [Debian-Manpage zu getcap](https://manpages.debian.org/trixie/libcap2-bin/getcap.8.en.html) und der lokalen Kurzhilfe von libcap 2.66.

## 3. Syntax

```text
getcap [-v] [-n] [-r] [-h] DATEI_ODER_ORDNER ...
```

```bash
getcap /usr/bin/ping
getcap -r /usr/bin
sudo getcap -r / 2>/dev/null
```

**Hinweis zum bisherigen Beispiel:** `getcap --help` aus dem Ausgangseintrag funktioniert nicht. Version 2.66 kennt keine langen Optionen, meldet `getcap: invalid option -- '-'`, zeigt die Kurzhilfe und endet mit Rückgabewert `1`. Die Hilfe erhält man mit `getcap -h`. Der Platzhalter `getcap [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-r` | Ordner rekursiv durchsuchen. | Für Systemprüfungen; bei `/` dauert es spürbar. |
| `-v` | Auch Dateien ohne Capabilities ausgeben. | Bestätigt, dass eine Datei überhaupt geprüft wurde. |
| `-n` | Benutzer-Namensraum-Root-ID mit ausgeben, falls gesetzt. | Für Capabilities aus Containern mit eigenem Namensraum. |
| `-h` | Kurzhilfe anzeigen. | Rückgabewert `0`. |
| `-l` | Lizenzhinweis anzeigen. | Steht in der lokalen Kurzhilfe, nicht in der Manpage. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Herausfinden, welche Programme in `/usr/bin` mit Capabilities ausgestattet sind, und den Unterschied zu einer eigenen Datei sehen.

### Schritt 1: Einzelnes Programm prüfen

```bash
getcap /usr/bin/ping
```

Auf dem geprüften System: `/usr/bin/ping cap_net_raw=ep`. `ping` braucht Raw-Sockets für ICMP und erhält dafür nur dieses eine Teilrecht. **Prüfpunkt:** Andere Distributionen lösen das anders (etwa über ICMP-Sockets ohne Capability); die Ausgabe kann leer sein.

### Schritt 2: Ordner durchsuchen

```bash
getcap -r /usr/bin 2>/dev/null
```

Im Test wurden `dumpcap`, `mtr-packet` und `ping` gefunden. `2>/dev/null` blendet Meldungen über nicht lesbare Pfade aus.

### Schritt 3: Eigene Datei prüfen

```bash
uebung="$(mktemp -d -t netmon-getcap-XXXXXX)" || exit 1
touch "$uebung/eigen"
getcap "$uebung/eigen"
getcap -v "$uebung/eigen"
```

Der erste Aufruf gibt nichts aus, weil keine Capabilities gesetzt sind. Mit `-v` erscheint der Dateiname ohne Zusatz.

## 6. Typische Anwendungsfälle

### Sicherheitsprüfung

Neben setuid-Programmen sind Programme mit Capabilities ein möglicher Weg zur Rechteausweitung. Eine regelmäßige Bestandsaufnahme mit `sudo getcap -r / 2>/dev/null` und ein Vergleich mit einer früheren Liste zeigen unerwartete Änderungen.

### Fehlersuche nach Kopieren oder Paketänderungen

Funktioniert ein Programm nach dem Kopieren oder Wiederherstellen nicht mehr (etwa „Operation not permitted“ bei Raw-Sockets), kann die Capability verloren gegangen sein. `getcap` zeigt das sofort.

### Containerabbilder prüfen

Mit `-n` lässt sich erkennen, ob eine Capability an eine Root-ID in einem Benutzer-Namensraum gebunden ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

`getcap` ist rein lesend. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde deshalb auf `safe` gesenkt.

Einschlägige Punkte:

- **Unvollständige Ergebnisse:** Ohne Root fehlen Dateien in nicht lesbaren Ordnern; mit `2>/dev/null` fällt das nicht auf.
- **Fehlende Datei ohne Fehlercode:** Im Test meldete `getcap` für eine nicht vorhandene Datei `(No such file or directory)`, endete aber mit Rückgabewert `0`. Skripte dürfen sich nicht allein auf den Rückgabewert verlassen.
- **Laufzeit:** `-r /` durchläuft alle eingehängten Dateisysteme, auch Netzlaufwerke und `/proc`. Das kann lange dauern und Last erzeugen.
- **Bewertung:** Eine Capability allein ist kein Befund. Entscheidend ist, ob das Programm sie benötigt und von wem es installiert wurde. Besonders kritisch sind weitreichende Capabilities wie `cap_sys_admin`, `cap_dac_read_search` oder `cap_setuid` an Programmen, die beliebige Eingaben verarbeiten.
- **Leerer Wert `=`:** Laut Manpage ist eine Datei mit leerem Capability-Satz (`=`) nicht gleichbedeutend mit einer Datei ohne Capabilities. Das ist für Ambient-Capabilities relevant.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `getcap: invalid option -- '-'` | Lange Option wie `--help` verwendet. | `getcap -h`. |
| Keine Ausgabe | Datei hat keine Capabilities oder Pfad falsch. | Mit `-v` prüfen, ob die Datei gelesen wurde. |
| `... (No such file or directory)` | Pfad existiert nicht; Rückgabewert trotzdem `0`. | Pfad prüfen. |
| `getcap: command not found` | Paket `libcap2-bin` fehlt oder `/usr/sbin` nicht im `PATH`. | `/usr/sbin/getcap` direkt aufrufen oder Paket prüfen. |
| Capability fehlt nach Kopie | `cp` ohne Erhalt erweiterter Attribute oder Zieldateisystem ohne Unterstützung. | Paket neu installieren oder mit `setcap` neu setzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`getcap` ist gefahrlos;** du kannst es ohne `sudo` ausprobieren.
2. **Mit `-v` arbeiten,** wenn du sicher sein willst, dass eine Datei geprüft wurde.
3. **Ergebnisse speichern und vergleichen:** `sudo getcap -r / 2>/dev/null > caps-$(date +%F).txt`.
4. **Bei `-r /` geduldig sein** oder gezielt `/usr`, `/opt` und `/home` prüfen.
5. **Nicht `--help` verwenden,** sondern `-h`.

### Prüfstand

- **Geprüfte Version:** libcap2-bin 1:2.66-5ubuntu2.4 (libcap 2.66).
- **Tatsächlich ausgeführt:** `getcap /usr/bin/ping`, `-v` auf `ping` und `ls`, `-r /usr/bin`, `-h`, `-l`, `--help` (Fehler, Rückgabe 1), eigene Datei ohne Capabilities mit und ohne `-v`, nicht vorhandene Datei (Rückgabe 0).
- **Nicht geprüft:** `-n` mit Namensraum-Capabilities, vollständiger Lauf über `/` mit Root-Rechten, Dateisysteme ohne erweiterte Attribute.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `setcap` | Setzt oder entfernt Datei-Capabilities (Root nötig). |
| `getpcaps` | Zeigt Capabilities laufender Prozesse. |
| `capsh` | Untersucht und startet Shells mit bestimmten Capabilities. |
| `find -perm -4000` | Findet setuid-Programme, die andere klassische Rechteausweitung. |
| `getfattr -n security.capability` | Zeigt das zugrunde liegende erweiterte Attribut roh an (Paket `attr`, lokal nicht installiert). |

Ausgangseintrag: Datensatz 108 in `index.json` (`getcap`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Das Beispiel `getcap --help` funktioniert mit libcap 2.66 nicht und wurde durch `getcap -h` und echte Prüfaufrufe ersetzt. Die Risikostufe wurde auf „sicher lesend“ gesenkt, weil der Befehl keine Daten verändert.
