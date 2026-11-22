---
id: "usermod"
name: "usermod"
command: "usermod"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer", "konten", "gruppen", "kontenverwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 125
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Meldungstexte"
---

# usermod – Vorhandenes Benutzerkonto ändern

## 1. Kurzbeschreibung

`usermod` ändert Eigenschaften eines vorhandenen Kontos: Zusatzgruppen, primäre Gruppe, Shell, Heimatverzeichnis, Name, UID, Sperre oder Ablaufdatum. Am häufigsten wird es verwendet, um **ein Konto einer Gruppe hinzuzufügen**: `usermod -aG GRUPPE KONTO`.

**Root-Rechte sind nötig.** Normale Benutzer ändern ihre eigenen Angaben mit `chfn`, `chsh` und `passwd`.

## 2. Was macht der Befehl?

`usermod` schreibt in `/etc/passwd`, `/etc/shadow`, `/etc/group` und `/etc/gshadow`. Je nach Option passiert mehr, als der Name vermuten lässt. Die Angaben folgen der [Debian-Manpage zu usermod](https://manpages.debian.org/trixie/passwd/usermod.8.en.html):

| Option | Zusätzliche Wirkung |
| --- | --- |
| `-G` ohne `-a` | **Entfernt das Konto aus allen nicht genannten Zusatzgruppen.** |
| `-u NEUE_UID` | Passt Dateien **im Heimatverzeichnis** und das Postfach an; Dateien anderswo nicht. |
| `-g GRUPPE` | Passt Dateien im Heimatverzeichnis an, die der alten Primärgruppe gehörten. |
| `-d VERZ -m` | Verschiebt den Inhalt des Heimatverzeichnisses an den neuen Ort. |
| `-l NEU` | Ändert nur den Namen; Heimatverzeichnis und Postfach heißen weiter wie vorher. |
| `-L` | Setzt `!` vor den Passwort-Hash; Schlüsselanmeldung bleibt möglich. |

Laut Manpage müssen Crontabs und at-Aufträge bei Namens- oder UID-Änderungen manuell angepasst werden, und bei UID-, Namens- oder Heimatänderungen dürfen keine Prozesse des Kontos laufen.

Neue Gruppenmitgliedschaften wirken erst nach **erneuter Anmeldung**.

## 3. Syntax

```text
usermod [OPTIONEN] KONTO
```

```bash
sudo usermod -aG docker anna
sudo usermod -s /bin/zsh anna
sudo usermod -L -e 1 anna
```

Das bisherige NetMon-Beispiel `usermod --help` zeigt nur die Hilfe; der Platzhalter `usermod [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-aG G1,G2` | Zusatzgruppen **ergänzen**. | Fast immer die richtige Form. |
| `-G G1,G2` | Zusatzgruppen **ersetzen**. | Entfernt alle anderen. |
| `-rG G1` | Aus genannten Zusatzgruppen entfernen. | In 4.13 lokal vorhanden. |
| `-g GRUPPE` | Primäre Gruppe ändern. | Gruppe muss existieren. |
| `-s SHELL` | Anmelde-Shell ändern. | Wie `chsh`; die Shell vorher testen. **Prüfpunkt:** Umfang der Pfadprüfung versionsabhängig. |
| `-c TEXT` | GECOS-Feld (Name) ändern. | Wie `chfn`. |
| `-d VERZ` | Heimatverzeichnis ändern. | Mit `-m` Inhalt verschieben. |
| `-l NEU` | Kontoname ändern. | Heimatordner separat umbenennen. |
| `-u UID` | UID ändern. | Dateien außerhalb des Heimatordners manuell nachziehen. |
| `-L`, `-U` | Passwort sperren bzw. entsperren. | Konto bleibt ohne `-e` per Schlüssel nutzbar. |
| `-e DATUM` | Ablaufdatum; `1` sperrt das Konto vollständig. | `-e ""` oder `-1` hebt es auf. |
| `-f TAGE` | Inaktivitätsfrist nach Passwortablauf. | – |
| `-p HASH` | Passwort-Hash setzen. | In der Prozessliste sichtbar; meiden. |
| `-v`, `-V`, `-w`, `-W` | Untergeordnete UID/GID-Bereiche verwalten. | Für rootless Container. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Das Konto `anna` soll zusätzlich der Gruppe `dialout` angehören, um ein USB-Seriell-Gerät zu nutzen, ohne andere Gruppen zu verlieren. Das verändert die Gruppendatenbank; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Ausgangslage

```bash
id anna
```

Die Ausgabe zeigt alle aktuellen Gruppen. Merke sie dir.

### Schritt 2: Gruppe ergänzen

```bash
sudo usermod -aG dialout anna
```

`-a` ist entscheidend: Ohne `-a` wäre `anna` danach nur noch in `dialout` als Zusatzgruppe.

### Schritt 3: Kontrolle

```bash
id anna
```

Die Liste enthält nun zusätzlich `dialout`, alle bisherigen Gruppen sind noch da.

### Schritt 4: Wirkung herstellen

`anna` meldet sich ab und wieder an. In einem einzelnen Terminal hilft vorübergehend `newgrp dialout`.

## 6. Typische Anwendungsfälle

| Aufgabe | Aufruf |
| --- | --- |
| Gruppe ergänzen | `usermod -aG GRUPPE KONTO` |
| Aus Gruppe entfernen | `usermod -rG GRUPPE KONTO` oder `gpasswd -d KONTO GRUPPE` |
| Konto vollständig sperren | `usermod -L -e 1 KONTO` |
| Sperre aufheben | `usermod -U -e "" KONTO` |
| Heimatverzeichnis verlegen | `usermod -d /daten/anna -m anna` |
| Konto umbenennen | `usermod -l neu alt`, dann Heimatordner mit `-d ... -m` |

## 7. Risiken, Nebenwirkungen und Vorsicht

- **`-G` ohne `-a`:** Der häufigste Fehler. Das Konto verliert zum Beispiel die Gruppe `sudo` und damit Verwaltungsrechte – bei dem einzigen Verwaltungskonto ein echtes Aussperren.
- **Privilegierte Gruppen:** `sudo`, `docker`, `adm`, `disk`, `shadow` geben weitreichende Rechte.
- **UID-Änderung:** Dateien außerhalb des Heimatordners gehören danach niemandem. Laufende Prozesse verhindern die Änderung.
- **Verschieben mit `-m`:** Bei großen Ordnern dauert es, und ein Abbruch kann einen Teilzustand hinterlassen. Vorher sichern.
- **`-L` allein sperrt nicht vollständig;** SSH-Schlüssel funktionieren weiter. Für eine echte Sperre zusätzlich `-e 1`.
- **Namen in Konfigurationen:** Nach `-l` greifen sudo-Regeln, Freigaben oder Skripte mit dem alten Namen nicht mehr.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen. Die Root-Angabe „Häufig“ wurde auf „erforderlich“ präzisiert.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Konto hat Gruppen verloren | `-G` ohne `-a`. | Mit `-aG` und der vorher notierten Liste wiederherstellen. |
| `usermod: user ... is currently used by process ...` | Prozesse laufen bei UID-, Namens- oder Heimatänderung. | Prozesse beenden und erneut versuchen. |
| `usermod: group '...' does not exist` | Tippfehler oder fehlende Gruppe. | `getent group` prüfen. |
| `usermod: user '...' does not exist` | Konto unbekannt. | `getent passwd` prüfen. |
| `usermod: no changes` | Gewünschter Zustand bestand schon. | Kein Fehler. |
| `The previous home directory (...) does not exist or is inaccessible. Move cannot be completed.` | `-m` ohne vorhandenen alten Ordner. | Pfade prüfen. |
| Neue Gruppe wirkt nicht | Sitzung älter als die Änderung. | Neu anmelden. |

Die englischen Meldungstexte wurden im lokalen Programm abgeglichen, aber nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vor jeder Gruppenänderung `id KONTO` notieren.**
2. **Immer `-aG`** statt `-G`.
3. **Zum Entfernen aus einer Gruppe `gpasswd -d`** verwenden; das ist eindeutig.
4. **Für vollständige Sperren `-L -e 1`.**
5. **Bei UID- oder Namensänderungen** vorher sichern und Prozesse beenden.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `usermod --help` (bestätigt `-a`, `-r`, `-v`), Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Kontoänderung, also Beispiel, Optionen und Fehlerfälle.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gpasswd -a`, `gpasswd -d` | Gruppenmitgliedschaft aus Sicht der Gruppe. |
| `chfn`, `chsh`, `passwd` | Eigene Angaben ohne Root ändern. |
| `useradd`, `userdel` | Konten anlegen und löschen. |
| `id`, `getent passwd` | Ergebnis prüfen. |
| `newgrp` | Neue Gruppe sofort in einem Terminal nutzen. |
| `chage` | Passwort- und Kontofristen ausführlich verwalten. |

Ausgangseintrag: Datensatz 125 in `index.json` (`usermod`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch die tatsächlichen Nebenwirkungen der Optionen, die Falle `-G` ohne `-a`, Sperrvarianten und einen vorsichtigen Ablauf ersetzt.
