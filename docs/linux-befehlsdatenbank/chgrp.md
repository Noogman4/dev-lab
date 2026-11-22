---
id: "chgrp"
name: "chgrp"
command: "chgrp"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "rechte", "gruppen", "dateirechte"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 102
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# chgrp – Gruppenzugehörigkeit von Dateien und Ordnern ändern

## 1. Kurzbeschreibung

`chgrp` ändert die **Besitzergruppe** einer Datei oder eines Ordners. Jede Datei unter Linux hat einen Eigentümer und eine Gruppe. Die Rechte für „Gruppe“ (zum Beispiel `rw-` in `-rw-rw----`) gelten für alle Mitglieder dieser Gruppe.

**Root-Rechte sind nicht nötig**, wenn dir die Datei gehört und du Mitglied der Zielgruppe bist. Das ist der häufigste Fall, etwa um eine Projektdatei mit einer Arbeitsgruppe zu teilen.

**Root-Rechte sind nötig**, wenn die Datei einem anderen Konto gehört oder die Zielgruppe nicht zu deinen Gruppen gehört.

## 2. Was macht der Befehl?

`chgrp` setzt für jede angegebene Datei die Gruppen-ID neu. Inhalt, Eigentümer und Rechtebits bleiben grundsätzlich unverändert – mit einer wichtigen Ausnahme: Ändert ein normaler Benutzer die Gruppe einer **ausführbaren** Datei, löscht der Linux-Kernel deren Bits `setuid` und `setgid`. Auch gespeicherte Datei-Capabilities werden bei ausführbaren Dateien entfernt. Das beschreibt die [Debian-Manpage zum Systemaufruf chown(2)](https://manpages.debian.org/trixie/manpages-dev/chown.2.en.html), auf dem `chgrp` beruht.

Die Gruppe kann als Name (`users`) oder als Nummer angegeben werden. Laut [GNU-Coreutils-Handbuch](https://www.gnu.org/software/coreutils/manual/html_node/chgrp-invocation.html) kennzeichnet ein vorangestelltes `+` eine Zahl eindeutig als Gruppen-ID, falls eine Gruppe gleichen Namens existiert.

Diese Beschreibung gilt für GNU coreutils, die unter Debian, Ubuntu und den meisten Linux-Distributionen verwendet werden. Grundlage sind die [Debian-Manpage zu chgrp](https://manpages.debian.org/trixie/coreutils/chgrp.1.en.html) und die lokale Hilfe von coreutils 9.4. BusyBox- oder BSD-Fassungen kennen weniger lange Optionen.

## 3. Syntax

```text
chgrp [OPTIONEN] GRUPPE DATEI ...
chgrp [OPTIONEN] --reference=VORLAGE DATEI ...
```

- `GRUPPE` ist der Name oder die Nummer der neuen Gruppe.
- `DATEI` kann eine oder mehrere Dateien oder Ordner sein.
- Mit `--reference` übernimmt `chgrp` die Gruppe einer vorhandenen Vorlagendatei.

```bash
chgrp users bericht.txt
chgrp -R projekt "Gemeinsamer Ordner"
chgrp --reference=vorlage.txt neu.txt
```

Das bisherige NetMon-Beispiel `chgrp --help` zeigt nur die Hilfe; der Platzhalter `chgrp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-R`, `--recursive` | Ordner mit allen Unterordnern und Dateien bearbeiten. | Wirkung vorher mit `ls -lR` oder `find` abschätzen. |
| `-c`, `--changes` | Nur tatsächliche Änderungen melden. | Gut zur Kontrolle; ohne Änderung keine Ausgabe. |
| `-v`, `--verbose` | Jede bearbeitete Datei melden. | Erzeugt bei großen Bäumen viel Ausgabe. |
| `-f`, `--silent`, `--quiet` | Die meisten Fehlermeldungen unterdrücken. | Versteckt Probleme; für Einsteiger nicht empfehlenswert. |
| `--reference=VORLAGE` | Gruppe von einer anderen Datei übernehmen. | Die Vorlage wird bei symbolischen Links immer aufgelöst. |
| `-h`, `--no-dereference` | Den symbolischen Link selbst ändern, nicht sein Ziel. | Ohne `-h` ändert `chgrp` das Linkziel. |
| `--dereference` | Linkziel ändern (Standard). | Vorgabe ohne `-R`. |
| `-H`, `-L`, `-P` | Umgang mit symbolischen Links bei `-R`. | `-P` (Standard) folgt keinen Links; `-L` folgt allen Ordnerlinks. |
| `--preserve-root` | Rekursive Arbeit auf `/` verweigern. | Unter GNU nicht automatisch aktiv für `chgrp`; bei Verwaltungsskripten bewusst setzen. |

**Versionshinweis:** Das aktuelle GNU-Handbuch (coreutils 9.12) beschreibt zusätzlich `--from=ALT`. Die lokal geprüfte Version 9.4 kennt diese Option für `chgrp` nicht und meldet `unrecognized option`. **Prüfpunkt:** Vor Verwendung von `--from` die installierte Version prüfen.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen eigenen Projektordner der Gruppe `users` zuordnen, damit deren Mitglieder ihn gemäß Gruppenrechten nutzen können. Alles geschieht in einem neuen Übungsordner.

### Schritt 1: Eigene Gruppen anzeigen

```bash
id -nG
```

Die Ausgabe listet die Gruppen, denen dein Konto angehört. Nur diese Gruppen kannst du ohne Root-Rechte vergeben. Im Beispiel wird `users` vorausgesetzt; wähle sonst eine Gruppe aus deiner Liste.

### Schritt 2: Übungsordner anlegen

```bash
uebung="$(mktemp -d -t netmon-chgrp-XXXXXX)" || exit 1
cd "$uebung" || exit 1
mkdir -p projekt/unter
printf 'a\n' > projekt/a.txt
printf 'b\n' > projekt/unter/b.txt
ls -l projekt
```

Alle Dateien gehören jetzt dir und deiner primären Gruppe.

### Schritt 3: Eine Datei umstellen

```bash
chgrp -v users projekt/a.txt
```

Erwartete Ausgabe (englische Spracheinstellung): `changed group of 'projekt/a.txt' from happy to users`. Statt `happy` steht dort deine bisherige Gruppe.

### Schritt 4: Den ganzen Ordner umstellen

```bash
chgrp -c -R users projekt
stat -c '%n %G' projekt projekt/unter/b.txt
```

`-R` bearbeitet alle Einträge, `-c` meldet nur Dateien, die sich tatsächlich ändern. `projekt/a.txt` erscheint deshalb nicht mehr. `stat` zeigt danach für jeden Pfad die Gruppe `users`.

### Schritt 5: Grenze ausprobieren

```bash
chgrp root projekt/a.txt
echo $?
```

Bist du nicht Mitglied von `root`, meldet `chgrp` `Operation not permitted` und den Rückgabewert `1`. Die Datei bleibt unverändert.

## 6. Typische Anwendungsfälle

### Gemeinsamer Arbeitsordner

Ein Ordner wird einer Projektgruppe zugeordnet, danach erhalten Gruppenmitglieder mit `chmod g+rw` Schreibrechte. Für neu angelegte Dateien hilft zusätzlich das setgid-Bit am Ordner (`chmod g+s ordner`): Neue Einträge erben dann die Ordnergruppe.

### Dienstdateien als Verwaltung zuordnen

```bash
sudo chgrp www-data /srv/web/upload
```

Typisch für Webserver oder andere Dienste, die über eine Gruppe Zugriff erhalten. Hier sind Root-Rechte nötig, weil die Datei meist nicht dem aufrufenden Konto gehört.

### Gruppe wie bei einer Vorlage setzen

`chgrp --reference=vorlage.txt neu.txt` übernimmt die Gruppe ohne Namen nachschlagen zu müssen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Zugriff öffnen oder entziehen

Eine falsche Gruppe kann vertrauliche Daten für eine ganze Gruppe lesbar machen oder Diensten den Zugriff entziehen. Ein rekursiver Aufruf auf einen falschen Ordner betrifft sofort viele Dateien; eine automatische Rückgängig-Funktion gibt es nicht.

### Systemordner

`sudo chgrp -R ...` auf `/etc`, `/usr`, `/var` oder Heimatverzeichnisse kann Anmeldung, Dienste oder Paketverwaltung stören. GNU `chgrp` schützt `/` bei `-R` nur mit ausdrücklichem `--preserve-root`.

### setuid und setgid gehen verloren

Im Test hatte ein eigenes ausführbares Skript vor der Gruppenänderung `-rwxr-sr-x`, danach `-rwxr-xr-x`. Das ist eine bewusste Schutzfunktion des Kernels, kann aber Programme beeinträchtigen, die auf diese Bits angewiesen sind.

### Symbolische Links

Ohne `-h` wirkt `chgrp` auf das Linkziel. Liegt das Ziel außerhalb des gedachten Bereichs, wird dort geändert. Bei `-R` folgt GNU `chgrp` standardmäßig keinen Ordnerlinks (`-P`).

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt passend. Für eigene Dateien sind keine erhöhten Rechte nötig; die Root-Angabe wurde deshalb auf „nicht erforderlich“ festgelegt.

## 8. Häufige Fehler

| Meldung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `chgrp: changing group of '...': Operation not permitted` | Datei gehört dir nicht oder du bist nicht Mitglied der Zielgruppe. | Mit `ls -l` und `id -nG` prüfen; ggf. die Verwaltung bitten. |
| `chgrp: invalid group: '...'` | Gruppe existiert nicht oder ist falsch geschrieben. | Mit `getent group NAME` prüfen. |
| `chgrp: cannot access '...': No such file or directory` | Pfad falsch. | Arbeitsordner mit `pwd` und Namen prüfen. |
| Neue Gruppe wirkt nicht | Gruppenmitgliedschaft wurde gerade erst vergeben. | Neu anmelden oder `newgrp` nutzen; laufende Sitzungen behalten alte Gruppen. |
| `unrecognized option '--from=...'` | Ältere coreutils-Version. | `chgrp --version` prüfen; ohne `--from` arbeiten. |

Der Rückgabewert ist `0` bei Erfolg und `1` bei Fehlern, auch wenn nur einzelne Dateien scheitern.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher anzeigen:** `ls -l` beziehungsweise `stat -c '%n %U %G'` zeigen den aktuellen Stand.
2. **Erst einzeln, dann rekursiv:** Wirkung an einer Datei prüfen, bevor `-R` folgt.
3. **`-c` verwenden,** um tatsächliche Änderungen zu sehen.
4. **Kein `-f` beim Lernen:** Fehlermeldungen sind wichtige Hinweise.
5. **Kein reflexartiges `sudo`:** Eine Ablehnung zeigt oft, dass die gewählte Gruppe oder Datei nicht stimmt.
6. **Für Verwaltungsskripte `--preserve-root` angeben.**

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4 (Ubuntu 24.04-Basis).
- **Tatsächlich ausgeführt** in einem eigenen temporären Ordner: `-v`, `-c` ohne und mit Änderung, `-c -R`, `--reference`, numerische Gruppe mit `+`, abgelehnte Fremdgruppe (`root`, Rückgabe 1), unbekannte Gruppe, Verlust des setgid-Bits an einem eigenen ausführbaren Skript, Vererbung der Ordnergruppe an neue Einträge bei gesetztem setgid-Bit am Ordner, fehlende Option `--from`.
- **Nicht geprüft:** Aufrufe mit Root-Rechten, Verhalten bei symbolischen Links (`-h`, `-H`, `-L`), Netzwerkdateisysteme und andere Implementierungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chown` | Ändert Eigentümer und optional Gruppe in einem Schritt (`chown :gruppe datei`). |
| `chmod` | Setzt die Rechte, die für Eigentümer, Gruppe und andere gelten. |
| `id`, `groups` | Zeigen die eigenen Gruppen. |
| `newgrp` | Startet eine Shell mit anderer aktiver Gruppe. |
| `getent group` | Zeigt Gruppen und Mitglieder. |
| `setfacl` | Vergibt Rechte an weitere Gruppen ohne die Besitzergruppe zu ändern. |

Ausgangseintrag: Datensatz 102 in `index.json` (`chgrp`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der allgemeine Hilfe-Platzhalter wurde durch die tatsächliche Wirkung, die Rechteregeln für Nicht-Root-Benutzer, den Verlust von setuid/setgid und einen geprüften Übungsablauf ersetzt.
