---
id: "visudo"
name: "visudo"
command: "visudo"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "rechte", "sudo", "konfiguration"]
status: "Ausgearbeitet; Quellen geprüft; Prüfmodus mit eigenen Testdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 126
reviewed_at: "2026-11-13"
locally_checked_version: "visudo 1.9.15p5 (sudoers-Grammatik 50)"
---

# visudo – sudo-Regeln sicher bearbeiten und prüfen

## 1. Kurzbeschreibung

`visudo` ist das vorgesehene Werkzeug zum Bearbeiten der sudo-Richtlinie `/etc/sudoers` und der Dateien in `/etc/sudoers.d/`. Es sperrt die Datei gegen gleichzeitige Bearbeitung, öffnet einen Editor auf einer temporären Kopie und **übernimmt Änderungen erst, wenn die Syntax stimmt**. Außerdem kann es Dateien nur prüfen (`-c`).

**Zum Bearbeiten der Systemrichtlinie sind Root-Rechte nötig** (üblich: `sudo visudo`). **Ohne Root** lässt sich der Prüfmodus auf eigene Dateien anwenden, etwa einen Entwurf im eigenen Ordner; die echte `/etc/sudoers` ist für normale Benutzer nicht lesbar.

## 2. Was macht der Befehl?

Laut [Debian-Manpage zu visudo](https://manpages.debian.org/trixie/sudo/visudo.8.en.html):

1. `visudo` sperrt die sudoers-Datei; bearbeitet sie schon jemand, kommt die Aufforderung, es später zu versuchen.
2. Es öffnet den Editor auf einer Kopie (`DATEI.tmp`).
3. Nach dem Speichern prüft es die gesamte Richtlinie. Bei einem Fehler nennt es die Zeile und fragt **„What now?“**:
   - `e` – erneut bearbeiten,
   - `x` – ohne Speichern beenden,
   - `Q` – trotz Fehler speichern (laut Manpage nur mit äußerster Vorsicht, weil dann auch sudo den Fehler sieht).
4. Ohne Fehler ersetzt es die Originaldatei und setzt Eigentümer und Rechte auf die Vorgaben.

Der Editor wird aus der sudoers-Einstellung `editor` gewählt, mit `env_editor` (Vorgabe: an) auch aus `SUDO_EDITOR`, `VISUAL` oder `EDITOR`. Standardpfad ist `/usr/bin/editor`, unter Debian/Ubuntu meist `nano`.

## 3. Syntax

```text
visudo [-c] [-q] [-s] [-I] [-O] [-P] [[-f] DATEI]
```

```bash
sudo visudo
sudo visudo -f /etc/sudoers.d/90-anna
sudo visudo -c
visudo -c -f entwurf.sudoers
```

Das bisherige NetMon-Beispiel `visudo --help` zeigt nur die Hilfe; der Platzhalter `visudo [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-c`, `--check` | Nur prüfen, nichts ändern. | Rückgabe `0` bei Erfolg, `1` bei Fehler. Ohne Dateiangabe auch Eigentümer und Rechte prüfen. |
| `-f DATEI` | Andere Datei bearbeiten oder prüfen. | Seit 1.8.27 auch ohne `-f` als Argument möglich. |
| `-` (mit `-c`) | Richtlinie von der Standardeingabe lesen. | Nur im Prüfmodus. |
| `-s`, `--strict` | Strenge Prüfung: undefinierte Aliase sind Fehler. | Im Test sonst nur Warnung. |
| `-q`, `--quiet` | Fehlerdetails unterdrücken. | Nur mit `-c` sinnvoll. |
| `-I`, `--no-includes` | Eingebundene Dateien nicht mitbearbeiten. | – |
| `-O`, `-P` | Standard-Eigentümer bzw. -Rechte erzwingen oder prüfen. | Ohne Dateiangabe automatisch aktiv. |
| `-V` | Versionen von visudo und Grammatik. | – |

Laut Manpage reicht es nicht, eine einzelne Include-Datei isoliert zu prüfen, weil die Richtlinie als Ganzes ausgewertet wird. Für die echte Gesamtprüfung dient `sudo visudo -c`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einem Konto `anna` erlauben, nur `apt update` mit Root-Rechten auszuführen. Zuerst wird ein Entwurf **ohne Root** geprüft; das Einspielen ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Entwurf im eigenen Ordner schreiben und prüfen (geprüft)

```bash
uebung="$(mktemp -d -t netmon-visudo-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf 'anna ALL=(ALL:ALL) /usr/bin/apt update\n' > 90-anna
visudo -c -f 90-anna
```

Ausgabe im Test: `90-anna: parsed OK`, Rückgabewert `0`.

### Schritt 2: Fehler sichtbar machen (geprüft)

```bash
printf 'anna ALLE\n' > fehler
visudo -c -f fehler
echo $?
```

`visudo` meldet `fehler:1:10: syntax error`, zeigt die Zeile mit Markierung und endet mit `1`.

### Schritt 3: Regel einspielen (Beispielszenario)

```bash
sudo visudo -f /etc/sudoers.d/90-anna
```

Inhalt aus dem Entwurf eintragen, speichern. `visudo` prüft und setzt Rechte. Dateinamen in `/etc/sudoers.d/` dürfen laut [Debian-Manpage zu sudoers(5)](https://manpages.debian.org/trixie/sudo/sudoers.5.en.html) keinen Punkt enthalten und nicht auf `~` enden, sonst werden sie übersprungen. Die Dateien werden in lexikalischer Reihenfolge gelesen. **Prüfpunkt:** Die Namensregel wurde nicht praktisch geprüft.

### Schritt 4: Gesamtprüfung und Test

```bash
sudo visudo -c
sudo -l -U anna
```

`-c` prüft alle Dateien zusammen; `sudo -l -U anna` zeigt, was `anna` nun darf.

## 6. Typische Anwendungsfälle

- **Eigene Regeln in `/etc/sudoers.d/`** statt in der Hauptdatei – Paketaktualisierungen ersetzen dann nichts.
- **Eingeschränkte Freigaben** für einzelne Befehle.
- **Automatisierte Prüfung** von Konfigurationsdateien in Skripten oder vor dem Ausrollen: `visudo -c -f DATEI`.
- **Reparatur nach Fehlern:** `sudo visudo -c` zeigt, welche Datei die Richtlinie bricht.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Warum „danger“

Die sudoers-Datei entscheidet, wer Root-Rechte bekommt. `visudo` verhindert Syntaxfehler, aber **keine logischen Fehler**: `ALL ALL=(ALL) NOPASSWD: ALL` ist syntaktisch korrekt und gibt jedem lokalen Konto Root ohne Passwort. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde deshalb auf `danger` angehoben.

### Weitere Punkte

- **Aussperren:** Entfernt man die eigene Freigabe oder speichert mit `Q` einen Fehler, funktioniert `sudo` nicht mehr. Dann hilft nur ein anderer Root-Zugang (Wiederherstellungsmodus, `pkexec`, Konsole).
- **Nie direkt mit einem Editor bearbeiten:** `sudo nano /etc/sudoers` umgeht Sperre und Prüfung.
- **Shell-Ausbrüche:** Freigaben für Editoren, `less`, Interpreter oder Programme mit Shell-Funktion sind praktisch volle Root-Rechte.
- **Editor als Root:** Mit `env_editor` kann `visudo` beliebige Editoren als Root starten. Die Manpage warnt, dass jemand mit visudo-Freigabe so beliebige Befehle ohne Protokoll ausführen kann.
- **Undefinierte Aliase:** Ohne `-s` gelten sie nur als Warnung; im Test meldete `visudo -c` trotzdem `parsed OK`.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `DATEI:ZEILE:SPALTE: syntax error` | Tippfehler in einer Regel. | Markierte Stelle korrigieren; im Editor mit `e`. |
| `User_Alias "..." referenced but not defined` | Alias fehlt oder Name in Großbuchstaben als Alias gedeutet. | Alias definieren; Großschreibung bei Kontonamen vermeiden. |
| `visudo: unable to open /etc/sudoers: Permission denied` | Ohne Root aufgerufen. | `sudo visudo`. |
| `... busy, try again later` | Datei wird gerade bearbeitet. | Später erneut. |
| Regel wirkt nicht | Datei in `sudoers.d` wegen Namen ignoriert, oder spätere Regel überschreibt. | Dateinamen prüfen; letzte passende Regel gewinnt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Immer `visudo`,** nie einen normalen Editor.
2. **Eigene Regeln in eigene Dateien** unter `/etc/sudoers.d/`.
3. **Entwürfe vorher mit `visudo -c -f` prüfen,** auch ohne Root.
4. **Ein zweites Root-Terminal offen lassen,** bis die neue Regel getestet ist.
5. **`Q` nie verwenden.**
6. **So wenig wie möglich freigeben,** möglichst mit vollständigen Programmpfaden und Argumenten.

### Prüfstand

- **Geprüfte Version:** visudo 1.9.15p5, Grammatik 50; Debian-Manpage 1.9.16p2.
- **Tatsächlich ausgeführt** mit eigenen Dateien im Testordner: `-c -f` mit gültiger Regel (Rückgabe 0), zwei Syntaxfehlern (Rückgabe 1 mit Positionsangaben), undefiniertem Alias mit und ohne `-s`, `-cq`, Prüfung über Standardeingabe, `-V`, `-h`, Aufruf von `visudo -c` ohne Root (keine Leserechte auf `/etc/sudoers`).
- **Nicht ausgeführt:** Bearbeiten oder Prüfen der echten Richtlinie mit Root, „What now?“-Dialog, Namensregeln in `/etc/sudoers.d/`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sudo` | Wendet die Richtlinie an; `sudo -l` zeigt Freigaben. |
| `sudoedit` | Bearbeitet andere Systemdateien sicher. |
| `vipw`, `vigr` | Bearbeiten Konto- und Gruppendateien mit Sperre. |
| `pkexec` | Alternativer Root-Zugang über polkit, etwa zur Reparatur. |

Ausgangseintrag: Datensatz 126 in `index.json` (`visudo`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde für das Bearbeiten auf „erforderlich“ korrigiert, die Risikostufe auf „Gefahr“ angehoben. Der Hilfe-Platzhalter wurde durch Ablauf, Prüfmodus, Optionen und einen teilweise ohne Root geprüften Ablauf ersetzt.
