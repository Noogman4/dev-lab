---
id: "chown"
name: "chown"
command: "chown"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "rechte", "eigentuemer", "dateirechte"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten teilweise geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 104
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4; nur ohne Root-Rechte"
---

# chown – Eigentümer und Gruppe von Dateien ändern

## 1. Kurzbeschreibung

`chown` („change owner“) setzt den Eigentümer und optional die Gruppe von Dateien und Ordnern. Der Eigentümer bestimmt, wessen Rechtebits (`u` in `chmod`) gelten und wer die Rechte später ändern darf.

**Für das Ändern des Eigentümers sind Root-Rechte nötig.** Unter Linux darf nur ein Prozess mit der Fähigkeit `CAP_CHOWN` – praktisch Root – eine Datei einem anderen Konto übergeben. Ein normaler Benutzer kann mit `chown` nur die Gruppe eigener Dateien ändern, und zwar auf Gruppen, denen er angehört; das entspricht `chgrp`.

## 2. Was macht der Befehl?

`chown` ändert die Benutzer-ID und/oder Gruppen-ID im Dateisystem-Eintrag. Der Dateiinhalt bleibt gleich. Wichtig sind diese Nebenwirkungen des zugrunde liegenden Systemaufrufs:

- Bei ausführbaren Dateien löscht der Kernel bei einem Eigentümer- oder Gruppenwechsel die setuid- und setgid-Bits; seit Linux 2.2.13 auch, wenn Root ändert. Die Manpage nennt eine Ausnahme: Ohne Gruppen-Ausführungsbit bleibt ein für die historische Mandatory-Locking-Bedeutung gesetztes setgid-Bit erhalten.
- Gespeicherte Datei-Capabilities ausführbarer Dateien werden entfernt.

Beides steht in der [Debian-Manpage zu chown(2)](https://manpages.debian.org/trixie/manpages-dev/chown.2.en.html). Die Befehlsbeschreibung folgt der [Debian-Manpage zu chown(1)](https://manpages.debian.org/trixie/coreutils/chown.1.en.html) und dem [GNU-Coreutils-Handbuch](https://www.gnu.org/software/coreutils/manual/html_node/chown-invocation.html).

### Schreibweisen für Eigentümer und Gruppe

| Angabe | Wirkung |
| --- | --- |
| `anna` | Eigentümer wird `anna`, Gruppe bleibt. |
| `anna:projekt` | Eigentümer `anna`, Gruppe `projekt`. |
| `anna:` | Eigentümer `anna`, Gruppe wird `anna`s Anmeldegruppe. |
| `:projekt` | Nur die Gruppe ändern, wie `chgrp`. |
| `1001:1001` | Numerische IDs; mit `+1001` eindeutig als Zahl gekennzeichnet. |

Ältere Skripte verwenden manchmal einen Punkt statt des Doppelpunkts (`anna.projekt`). GNU unterstützt das nur noch mit Warnung; neue Aufrufe sollten den Doppelpunkt nutzen.

## 3. Syntax

```text
chown [OPTIONEN] [EIGENTÜMER][:[GRUPPE]] DATEI ...
chown [OPTIONEN] --reference=VORLAGE DATEI ...
```

```bash
sudo chown anna bericht.pdf
sudo chown -R anna:anna /home/anna/Import
chown :users eigene-datei.txt
```

Das bisherige NetMon-Beispiel `chown --help` zeigt nur die Hilfe; der Platzhalter `chown [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-R`, `--recursive` | Ordner samt Inhalt bearbeiten. | Mit Root-Rechten besonders folgenreich. |
| `-c`, `--changes` | Nur tatsächliche Änderungen melden. | Zeigt alten und neuen Besitz. |
| `-v`, `--verbose` | Jede Datei melden, auch unveränderte. | Meldet auch Fehlschläge ausführlich. |
| `-f`, `--silent` | Fehlermeldungen unterdrücken. | Für Einsteiger ungeeignet. |
| `--from=ALT:ALTGRUPPE` | Nur ändern, wenn der bisherige Besitz passt. | Verhindert Fehländerungen bei gemischten Bäumen. |
| `--reference=VORLAGE` | Besitz einer anderen Datei übernehmen. | Vorlage vorher prüfen. |
| `-h`, `--no-dereference` | Symbolischen Link selbst ändern. | Ohne `-h` wird das Linkziel geändert. |
| `-H`, `-L`, `-P` | Linkbehandlung bei `-R`. | `-P` ist Standard; `-L` folgt allen Ordnerlinks. |
| `--preserve-root` | Rekursive Arbeit auf `/` verweigern. | Bei GNU `chown` nicht Standard. |

Das GNU-Handbuch warnt ausdrücklich: Die Kombination von `-R` mit `--dereference` oder `-L` kann ein Sicherheitsrisiko sein. Ein Angreifer könnte während des Durchlaufs einen symbolischen Link einschleusen, sodass die Änderung ein beliebiges Ziel trifft.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Unterschied zwischen erlaubter Gruppenänderung und verbotener Eigentümeränderung ohne Root-Rechte sehen. Ein Eigentümerwechsel mit `sudo` ist am Ende nur als **Beispielszenario** beschrieben und wurde nicht ausgeführt.

### Schritt 1: Übungsordner und Datei

```bash
uebung="$(mktemp -d -t netmon-chown-XXXXXX)" || exit 1
cd "$uebung" || exit 1
touch a
stat -c '%U:%G %n' a
```

Die Datei gehört dir und deiner primären Gruppe.

### Schritt 2: Gruppe mit chown ändern

```bash
chown -v "$USER":users a
```

Bist du Mitglied von `users`, meldet `chown` zum Beispiel `changed ownership of 'a' from happy:happy to happy:users`. Der Eigentümer bleibt gleich; nur die Gruppe wechselt.

### Schritt 3: Eigentümerwechsel ohne Root versuchen

```bash
chown -v root a
echo $?
```

Erwartet: `Operation not permitted`, zusätzlich `failed to change ownership of 'a' from happy to root`, Rückgabewert `1`. Die Datei bleibt unverändert.

### Schritt 4: Bedingte Änderung mit --from

```bash
chown -v --from=root "$USER":"$USER" a
```

Weil `a` nicht `root` gehört, meldet `chown` `ownership of 'a' retained as ...` und ändert nichts. So lassen sich gezielt nur Dateien eines bestimmten Altbesitzers umstellen.

### Beispielszenario mit Root-Rechten (nicht ausgeführt)

```bash
sudo chown -c --from=root:root anna:anna /home/anna/Import/*.pdf
```

Ein Verwaltungskonto übergibt von Root kopierte PDF-Dateien an `anna`. `--from` begrenzt die Änderung auf Dateien, die noch `root:root` gehören. Das `*` erweitert die Shell; versteckte Dateien sind dabei nicht enthalten.

## 6. Typische Anwendungsfälle

### Mit sudo erzeugte Dateien zurückgeben

Wurden Dateien versehentlich mit `sudo` im eigenen Heimatverzeichnis angelegt, gehören sie Root. `sudo chown "$USER": DATEI` gibt sie an dich und deine Anmeldegruppe zurück. Prüfe vorher mit `ls -l`, welche Dateien betroffen sind.

### Dienstverzeichnisse vorbereiten

Ein Dienstkonto (etwa `www-data` oder `postgres`) braucht Besitz an seinem Datenordner. Der Paketverwalter erledigt das meist selbst; manuelle Änderungen nur nach Dienstdokumentation.

### Nach Kopien zwischen Systemen

Numerische IDs können auf einem anderen System anderen Konten gehören. Nach dem Zurückspielen einer Sicherung mit `tar` oder `rsync` kann eine gezielte Korrektur nötig sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Warum „danger“

`chown` wird für seinen Hauptzweck mit Root-Rechten ausgeführt. Ein falscher Pfad, ein überflüssiges `-R` oder ein Leerzeichen an der falschen Stelle (`sudo chown -R anna: / home/anna`) kann Systemordner betreffen. Danach funktionieren `sudo`, SSH, Dienste oder Paketverwaltung oft nicht mehr, weil Programme falsche Eigentümer ablehnen. Die vorherigen Besitzverhältnisse werden nirgends gespeichert. Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ wird deshalb beibehalten.

### Datenoffenlegung und Rechteausweitung

Wer Eigentümer wird, kann die Rechte frei ändern. Übergibt man vertrauliche Dateien an ein falsches Konto, erhält dieses vollen Zugriff. Umgekehrt kann ein schreibbares Skript, das Root gehört und von Root ausgeführt wird, zur Rechteausweitung führen.

### Verlust von Sonderbits

Programme mit setuid, setgid oder Datei-Capabilities verlieren diese beim Besitzwechsel. Pakete setzen sie bei der Installation; manuelle Änderungen können solche Programme funktionsunfähig machen.

### Symbolische Links

Ohne `-h` wirkt `chown` auf das Linkziel. Mit `-R -L` kann ein Durchlauf Bereiche außerhalb des gedachten Ordners erreichen. Im Test änderte `chown -h :users link` nur den Link, nicht die Zieldatei.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `chown: changing ownership of '...': Operation not permitted` | Eigentümerwechsel ohne Root-Rechte oder Gruppe, der du nicht angehörst. | Prüfen, ob die Änderung wirklich nötig ist; dann mit Verwaltungsrechten. |
| `chown: invalid user: '...'` | Konto existiert nicht oder Tippfehler. | `getent passwd NAME` prüfen. |
| `chown: invalid group: '...'` | Gruppe existiert nicht. | `getent group NAME` prüfen. |
| `ownership of '...' retained as ...` | `--from` passte nicht oder Besitz war schon richtig. | Ausgabe ist kein Fehler; Altbesitz prüfen. |
| Programm startet nach chown nicht mehr wie vorher | setuid/setgid oder Capabilities wurden entfernt. | Paket neu installieren lassen oder Bits gemäß Dokumentation neu setzen. |
| Auf einem anderen Rechner falsche Namen | Gleiche Nummern gehören dort anderen Konten. | Numerische IDs mit `ls -ln` vergleichen. |

Rückgabewert `1` bei Fehlern; mit `--from` und unpassendem Altbesitz bleibt der Rückgabewert `0`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher anzeigen:** `ls -l` oder `stat -c '%U:%G %n'`.
2. **Nur Gruppe nötig?** Dann `chgrp` oder `chown :gruppe` ohne `sudo`.
3. **`--from` verwenden,** wenn nur Dateien eines bestimmten Altbesitzers geändert werden sollen.
4. **Erst ohne `-R`,** dann gezielt einen Unterordner.
5. **`--preserve-root` und `-c`** in Verwaltungsskripten setzen.
6. **Pfade nicht mit Leerzeichen trennen,** sondern in Anführungszeichen setzen.
7. **Keine Systempakete nachträglich umbesitzen;** dafür ist der Paketverwalter zuständig.

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4, ausschließlich als normaler Benutzer.
- **Tatsächlich ausgeführt** im Testordner: `EIGENTÜMER:GRUPPE` mit eigener Gruppe, `:GRUPPE`, `EIGENTÜMER:` (Anmeldegruppe), abgelehnter Wechsel zu `root` und zur UID `0` (Rückgabe 1), `--from` ohne Treffer (Rückgabe 0), `-h` an einem symbolischen Link.
- **Nicht geprüft:** jeder tatsächliche Eigentümerwechsel mit Root-Rechten (Beispielszenario), Verlust von Capabilities, rekursive Linkoptionen `-H`/`-L`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chgrp` | Ändert nur die Gruppe; für Nicht-Root-Benutzer der passende Befehl. |
| `chmod` | Setzt die Rechte für Eigentümer, Gruppe und andere. |
| `stat`, `ls -ln` | Zeigen Eigentümer und Gruppe, auch numerisch. |
| `install -o -g` | Kopiert eine Datei und setzt Besitz in einem Schritt (mit Root). |
| `find -user`, `find -uid` | Finden Dateien eines bestimmten Eigentümers. |
| `getfacl` | Sichert Besitz und Rechte als Text vor größeren Änderungen. |

Ausgangseintrag: Datensatz 104 in `index.json` (`chown`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert, weil der Eigentümerwechsel unter Linux Root-Rechte verlangt. Der Hilfe-Platzhalter wurde durch die Schreibweisen für Besitz, `--from`, Symlink-Risiken und den Verlust von Sonderbits ersetzt.
