---
id: "passwd"
name: "passwd"
command: "passwd"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "konten", "passwort", "sicherheit"]
status: "Ausgearbeitet; Quellen geprüft; nur Statusabfragen praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 116
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Status"
---

# passwd – Passwort ändern und Passwortstatus eines Kontos verwalten

## 1. Kurzbeschreibung

`passwd` ändert das Anmeldepasswort eines Benutzerkontos. Außerdem zeigt es den Passwortstatus und verwaltet – für Root – Sperrung, Ablauf und Gültigkeitsfristen.

**Root-Rechte sind für das eigene Passwort nicht nötig.** `passwd` ist ein SUID-Programm und fragt zuerst dein aktuelles Passwort ab. **Root-Rechte sind nötig** für fremde Konten sowie für Sperren, Entsperren, Löschen und das Setzen von Fristen.

## 2. Was macht der Befehl?

Beim normalen Aufruf läuft laut [Debian-Manpage zu passwd](https://manpages.debian.org/trixie/passwd/passwd.1.en.html) Folgendes ab:

1. Abfrage des **aktuellen Passworts** (nur ein Versuch). Root überspringt diesen Schritt.
2. Prüfung der Passwortfristen: Darf das Passwort jetzt schon geändert werden?
3. **Zweimalige Eingabe** des neuen Passworts; beide müssen übereinstimmen.
4. Prüfung auf ausreichende Stärke und Speichern als Hash in `/etc/shadow`.

Die Änderung läuft über **PAM**. Auf dem geprüften System prüft `pam_pwquality` die Passwortstärke mit bis zu drei Versuchen, `pam_unix` speichert den Hash mit dem Verfahren yescrypt, und `pam_gnome_keyring` passt den Schlüsselbund der Desktop-Sitzung an. Welche Regeln gelten, steht in `/etc/pam.d/common-password` und kann sich je nach System unterscheiden.

Für Konten aus Verzeichnisdiensten (LDAP, Active Directory über SSSD) leitet PAM die Änderung gegebenenfalls dorthin weiter; das hängt von der Einrichtung ab.

### Status lesen

```bash
passwd -S
```

Auf dem geprüften System: `happy P 2026-03-07 0 99999 7 -1`. Die sieben Felder bedeuten:

| Feld | Bedeutung |
| --- | --- |
| `happy` | Kontoname |
| `P` | Passwortzustand: `P` nutzbar, `L` gesperrt, `NP` kein Passwort |
| `2026-03-07` | Letzte Änderung |
| `0` | Mindestalter in Tagen |
| `99999` | Höchstalter in Tagen (praktisch unbegrenzt) |
| `7` | Warnfrist in Tagen |
| `-1` | Inaktivitätsfrist; `-1` heißt keine |

## 3. Syntax

```text
passwd [OPTIONEN] [KONTONAME]
```

```bash
passwd
passwd -S
sudo passwd anna
sudo passwd -l anna
```

Das bisherige NetMon-Beispiel `passwd --help` zeigt nur die Hilfe; der Platzhalter `passwd [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Rechte |
| --- | --- | --- |
| *(keine)* | Eigenes Passwort ändern. | Eigenes Konto |
| `-S`, `--status` | Passwortstatus anzeigen. | Eigenes Konto; fremde nur Root |
| `-a`, `--all` | Mit `-S` den Status aller Konten zeigen. | Root |
| `-l`, `--lock` | Passwort sperren (`!` vor den Hash). | Root |
| `-u`, `--unlock` | Sperre aufheben. | Root |
| `-e`, `--expire` | Passwort sofort ablaufen lassen; Änderung bei nächster Anmeldung. | Root |
| `-d`, `--delete` | Passwort löschen (leer). | Root; gefährlich |
| `-n TAGE`, `-x TAGE`, `-w TAGE`, `-i TAGE` | Mindest-, Höchstalter, Warn- und Inaktivitätsfrist. | Root |
| `-k`, `--keep-tokens` | Nur abgelaufene Passwörter ändern. | Eigenes Konto |
| `-q`, `--quiet` | Weniger Ausgaben. | – |
| `-R VERZ`, `--root VERZ` | In einem anderen Wurzelverzeichnis arbeiten. | Root |

**Wichtig zu `-l`:** Laut Manpage sperrt `-l` nur das Passwort, **nicht das Konto**. Eine Anmeldung per SSH-Schlüssel kann weiter funktionieren. Zum vollständigen Sperren empfiehlt die Manpage `usermod --expiredate 1`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Das eigene Passwort ändern. Das verändert dein Konto und ist deshalb ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Status prüfen

```bash
passwd -S
```

Steht im zweiten Feld `P`, hast du ein nutzbares Passwort. Ein Mindestalter größer `0` kann eine sofortige erneute Änderung verhindern.

### Schritt 2: Passwort ändern

```bash
passwd
```

Erwarteter Dialog (deutsche Spracheinstellung, sinngemäß): aktuelles Passwort, neues Passwort, neues Passwort wiederholen. Eingaben werden nicht angezeigt – auch keine Sternchen.

### Schritt 3: Ergebnis

Bei Erfolg meldet `passwd` sinngemäß „Passwort erfolgreich geändert“. Danach zeigt `passwd -S` im dritten Feld das heutige Datum.

### Schritt 4: Testen, bevor du dich abmeldest

Öffne ein zweites Terminal und prüfe die Anmeldung, zum Beispiel mit `su - "$USER"`. So bemerkst du Tippfehler, solange du noch angemeldet bist.

## 6. Typische Anwendungsfälle

| Aufgabe | Aufruf |
| --- | --- |
| Eigenes Passwort ändern | `passwd` |
| Vergessenes Passwort eines Kontos neu setzen | `sudo passwd anna` |
| Änderung bei nächster Anmeldung erzwingen | `sudo passwd -e anna` |
| Passwortanmeldung vorübergehend sperren | `sudo passwd -l anna` |
| Status aller Konten prüfen | `sudo passwd -S -a` |

Für Fristen ist `chage` die ausführlichere Alternative.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Aussperren:** Ein vertipptes neues Passwort kann dich aussperren, besonders bei Konsolenanmeldung mit anderer Tastaturbelegung. Deshalb vor dem Abmelden testen.
- **Schlüsselbund und verschlüsselte Daten:** Wenn Root dein Passwort neu setzt, kennt der Desktop-Schlüsselbund das alte Passwort weiter; gespeicherte Passwörter fragt er dann ab. Ähnliches kann bei verschlüsseltem Heimatverzeichnis gelten. **Prüfpunkt:** systemabhängig, nicht praktisch geprüft.
- **`-d` macht das Konto ohne Passwort zugänglich,** je nach PAM-Einstellung (`nullok`) auch für Anmeldungen.
- **`-l` ist keine vollständige Sperre;** SSH-Schlüssel und andere Verfahren bleiben möglich.
- **Passwörter nicht als Argument oder in Skripten übergeben.** Für automatisierte Verwaltung gibt es `chpasswd`; auch dort gelangen Passwörter leicht in Verlauf oder Protokolle.
- **Sicherheit des Passworts:** Die Manpage empfiehlt lange, zufällige Passwörter; Länge ist wichtiger als Sonderzeichen.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen. Die Root-Angabe „Häufig“ wurde präzisiert: für das eigene Passwort nicht nötig, für Verwaltungsoptionen nötig.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| „Authentication token manipulation error“ | Altes Passwort falsch oder `/etc/shadow` nicht beschreibbar. | Altes Passwort prüfen; bei Root auf Dateisystemfehler oder schreibgeschütztes System achten. |
| Neues Passwort wird abgelehnt (zu kurz, zu einfach, im Wörterbuch) | `pam_pwquality`-Regeln. | Längeres, nicht naheliegendes Passwort wählen. |
| „Passwords do not match“ | Zwei Eingaben verschieden. | Langsam neu eingeben. |
| „You must wait longer to change your password“ | Mindestalter noch nicht erreicht. | `passwd -S` prüfen; Verwaltung fragen. |
| „Sie dürfen die Passwortinformationen für root nicht anzeigen oder ändern.“ | Fremdes Konto ohne Root (im Test mit `passwd -S root`). | Nur eigenes Konto oder Verwaltungsrechte. |

Rückgabewerte laut Manpage: `0` Erfolg, `1` Berechtigung verweigert, `2` ungültige Optionskombination, `3` unerwarteter Fehler, `4` Passwortdatei fehlt, `5` Datei belegt, `6` ungültiges Argument. Im Test lieferte `passwd -S root` den Wert `1`. **Prüfpunkt:** Die englischen PAM-Meldungen sind sinngemäß wiedergegeben und hängen von PAM-Modulen und Spracheinstellung ab.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher `passwd -S`** ausführen.
2. **Ein zweites Terminal offen lassen** und die neue Anmeldung testen.
3. **Lange Passphrasen** aus mehreren zufälligen Wörtern verwenden.
4. **Passwörter nie in Befehlszeilen oder Skripten** notieren.
5. **Für Kontosperren** `usermod --expiredate 1` zusätzlich zu `passwd -l` erwägen.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `passwd --help`, `passwd -S` für das eigene Konto, `passwd -S root` (abgelehnt, Rückgabe 1), Lesen von `/etc/pam.d/common-password`, Prüfung des SUID-Bits.
- **Nicht ausgeführt:** jede Passwortänderung, Sperrung oder Friständerung; damit auch Beispiel und Fehlermeldungen aus Abschnitt 8 außer der Root-Ablehnung.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chage` | Zeigt und setzt Passwortfristen ausführlich. |
| `usermod -L`, `usermod --expiredate` | Sperren Passwort beziehungsweise Konto. |
| `chpasswd` | Setzt Passwörter für viele Konten aus einer Liste (Root). |
| `chfn`, `chsh` | Ändern andere Felder des eigenen Kontos. |
| `gpasswd` | Setzt Gruppenpasswörter. |
| `ssh-keygen -p` | Ändert die Passphrase eines SSH-Schlüssels, nicht des Kontos. |

Ausgangseintrag: Datensatz 116 in `index.json` (`passwd`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch den Ablauf einer Änderung, die Statusfelder, die Rechteunterschiede, die Grenzen von `-l` und die PAM-Einbindung ersetzt.
