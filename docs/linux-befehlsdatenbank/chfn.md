---
id: "chfn"
name: "chfn"
command: "chfn"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "konten", "gecos", "passwd"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 101
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Lesezugriffe"
---

# chfn – Namen und Kontaktfelder eines Benutzerkontos ändern

## 1. Kurzbeschreibung

`chfn` („change finger information“) ändert die Zusatzangaben eines Benutzerkontos: vollständiger Name, Raumnummer, dienstliche und private Telefonnummer sowie ein Feld für sonstige Angaben. Diese Angaben stehen im sogenannten GECOS-Feld, dem fünften Feld eines Eintrags in `/etc/passwd`.

**Root-Rechte sind für Änderungen am eigenen Konto in der Regel nicht nötig.** Das Programm ist dafür mit gesetztem SUID-Bit installiert und fragt über PAM nach deinem Passwort. Welche Felder du selbst ändern darfst, legt die Systemverwaltung in `/etc/login.defs` fest.

**Root-Rechte sind nötig**, um Felder eines anderen Kontos zu ändern, um Felder zu ändern, die `CHFN_RESTRICT` sperrt, oder um das Feld „Sonstiges“ (`-o`) zu setzen.

## 2. Was macht der Befehl?

`chfn` schreibt den GECOS-Teil des eigenen oder eines angegebenen Kontos neu. Das Feld besteht aus durch Kommas getrennten Teilen:

| Position | Inhalt | Option |
| --- | --- | --- |
| 1 | Vollständiger Name | `-f` |
| 2 | Raumnummer | `-r` |
| 3 | Telefon dienstlich | `-w` |
| 4 | Telefon privat | `-h` |
| 5 und folgende | Sonstige Angaben, etwa für Abrechnungsprogramme | `-o` |

Andere Kontodaten wie Passwort, Benutzerkennung, Heimatverzeichnis oder Anmelde-Shell ändert `chfn` nicht. Für die Shell ist `chsh` zuständig, für das Passwort `passwd`.

Die gespeicherten Angaben sind **für alle lokalen Benutzer lesbar**, weil `/etc/passwd` allgemein lesbar ist. Programme wie `finger`, `pinky` oder Anmeldebildschirme zeigen sie an.

Die Beschreibung folgt der [Debian-Manpage zu chfn aus dem Paket passwd](https://manpages.debian.org/trixie/passwd/chfn.1.en.html). Dort steht auch, dass die Felder keine Doppelpunkte und – außer „Sonstiges“ – keine Kommas oder Gleichheitszeichen enthalten dürfen.

### Zwei verschiedene Implementierungen

Debian, Ubuntu und darauf aufbauende Systeme wie Zorin OS verwenden `chfn` aus der Shadow-Suite (Paket `passwd`). Andere Distributionen liefern `chfn` aus **util-linux** aus. Diese Fassung kennt unter anderem `-o` für das Büro und `-p` für das Bürotelefon sowie `-V` für die Version; siehe [util-linux-Manpage bei man7.org](https://man7.org/linux/man-pages/man1/chfn.1.html). **Prüfpunkt:** Vor dem Einsatz mit `chfn --help` klären, welche Fassung installiert ist. Dieses Dokument beschreibt die Shadow-Fassung.

## 3. Syntax

```text
chfn [OPTIONEN] [KONTONAME]
```

- Ohne `KONTONAME` gilt der Aufruf für das eigene Konto.
- Ohne Optionen fragt `chfn` jedes erlaubte Feld interaktiv ab. Der aktuelle Wert steht in eckigen Klammern; eine leere Eingabe übernimmt ihn unverändert.
- Mit Optionen werden nur die genannten Felder gesetzt.

```bash
chfn
chfn -r "B 2.14"
sudo chfn -f "Erika Beispiel" erika
```

Das bisherige NetMon-Beispiel `chfn --help` zeigt nur die Hilfe. Der bisherige Platzhalter `chfn [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Die Tabelle beschreibt die Shadow-Fassung, geprüft an der lokalen Hilfe von shadow 4.13 und der Debian-Manpage.

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-f NAME`, `--full-name NAME` | Vollständigen Namen setzen. | Unter Debian/Ubuntu für normale Benutzer standardmäßig gesperrt. |
| `-r RAUM`, `--room RAUM` | Raumnummer setzen. | Keine Kommas verwenden. |
| `-w TELEFON`, `--work-phone TELEFON` | Bürotelefon setzen. | Nur ASCII-Zeichen werden bei Telefonnummern akzeptiert. |
| `-h TELEFON`, `--home-phone TELEFON` | Privattelefon setzen. | **Nicht** die Hilfe; `-h` erwartet einen Wert. |
| `-o TEXT`, `--other TEXT` | Feld „Sonstiges“ setzen. | Nur für Root. |
| `-R VERZ`, `--root VERZ` | Änderung in einem anderen Wurzelverzeichnis vornehmen. | Für Verwaltung eines eingehängten Systemabbilds; nur absolute Pfade. |
| `-u`, `--help` | Hilfe anzeigen. | Die lange Form ist die zuverlässigste Wahl. |
| `--extrausers` | Die zusätzliche Benutzerdatenbank von libnss-extrausers verwenden. | Ubuntu-spezifisch, in der Debian-Manpage nicht enthalten; **Prüfpunkt** bei anderen Systemen. |

### Was dürfen normale Benutzer ändern?

Die Variable `CHFN_RESTRICT` in `/etc/login.defs` enthält die Buchstaben `f`, `r`, `w`, `h` für die vier Felder, die normale Benutzer ändern dürfen. Auf dem geprüften System steht dort `rwh`: Raum und Telefonnummern sind erlaubt, der vollständige Name nicht. Fehlt die Variable, darf nur Root ändern. Die Bedeutung ist in der [Debian-Manpage unter CONFIGURATION](https://manpages.debian.org/trixie/passwd/chfn.1.en.html) beschrieben.

```bash
grep -E '^\s*CHFN_RESTRICT' /etc/login.defs
```

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die eigene Raumnummer eintragen, ohne den Namen oder andere Kontodaten zu berühren. Das Beispiel ändert das eigene Konto in `/etc/passwd`. Es ist deshalb **nur ein Beispielszenario** und wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Aktuellen Eintrag lesen

```bash
getent passwd "$USER" | cut -d: -f5
```

`getent passwd` liest den eigenen Kontoeintrag aus der Benutzerdatenbank, `cut` zeigt nur das fünfte Feld. Eine Ausgabe wie `Erika Beispiel,,,` bedeutet: Name gesetzt, die übrigen Felder leer. Dieser Schritt ändert nichts.

### Schritt 2: Erlaubte Felder prüfen

```bash
grep -E '^\s*CHFN_RESTRICT' /etc/login.defs
```

Enthält der Wert ein `r`, darfst du die Raumnummer selbst setzen. Fehlt der Buchstabe, wird `chfn` die Änderung ablehnen.

### Schritt 3: Raumnummer setzen

```bash
chfn -r "B 2.14"
```

`chfn` fragt nach deinem Passwort. Nach erfolgreicher Anmeldung schreibt es nur die Raumnummer. Name und Telefonnummern bleiben wie zuvor.

### Schritt 4: Ergebnis kontrollieren

```bash
getent passwd "$USER" | cut -d: -f5
```

Erwartet wird zum Beispiel `Erika Beispiel,B 2.14,,`. Bei einer zentralen Benutzerverwaltung (LDAP, SSSD, Active Directory) ist eine lokale Änderung oft nicht möglich oder nicht sinnvoll; siehe Abschnitt 8.

### Rückgängig machen

Mit `chfn -r ""` lässt sich die Raumnummer wieder leeren. **Prüfpunkt:** Das Leeren über eine leere Zeichenkette ist nicht praktisch geprüft.

## 6. Typische Anwendungsfälle

### Eigene Kontaktangaben pflegen

In Mehrbenutzersystemen mit `finger`- oder `pinky`-Auswertung können Benutzer Raum und Telefonnummer selbst aktuell halten, sofern `CHFN_RESTRICT` das erlaubt.

### Vollständigen Namen als Verwaltung setzen

```bash
sudo chfn -f "Erika Beispiel" erika
```

Der Anzeigename erscheint danach etwa in Anmeldemasken oder als Absendername einiger Programme. Für neu angelegte Konten ist oft `useradd -c` oder `adduser` der passendere Weg.

### Systemabbild verwalten

`-R /mnt/abbild` schreibt in die Kontodateien unterhalb dieses Pfads statt in die des laufenden Systems. Das ist nur sinnvoll, wenn das Abbild bewusst eingehängt und für die Bearbeitung vorgesehen ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Lesen und Ändern unterscheiden

| Aktion | Einordnung |
| --- | --- |
| `chfn --help`, `getent passwd` | Nur lesend. |
| `chfn` am eigenen Konto | Ändert `/etc/passwd` über ein SUID-Programm; Passwortabfrage. |
| `sudo chfn ... KONTO` | Ändert ein fremdes Konto mit vollen Rechten. |

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wird übernommen: Der Befehl verändert eine zentrale Kontodatei, wenn auch nur in einem Textfeld.

### Datenoffenlegung

Alles im GECOS-Feld ist für jedes lokale Konto lesbar. Trage keine privaten Telefonnummern, Personalnummern oder andere vertrauliche Angaben ein, wenn das nicht ausdrücklich gewünscht ist.

### Format und nachgelagerte Programme

Doppelpunkte würden die Struktur von `/etc/passwd` zerstören und werden abgelehnt. Kommas würden Felder verschieben. Einige Programme werten den vollständigen Namen aus, etwa für Absenderzeilen. Ein unpassender Wert kann dort sichtbar werden.

### SUID-Programm

`chfn` läuft mit Root-Rechten, auch wenn du es als normaler Benutzer startest. Die Manpage nennt als strengste Absicherung, `chfn` ohne SUID-Bit zu installieren. Das ist eine Entscheidung der Systemverwaltung und gehört nicht in eine Übung.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `chfn: Permission denied.` beim Namen | `CHFN_RESTRICT` erlaubt das Feld `f` nicht. | Wert in `/etc/login.defs` prüfen; Namensänderung durch die Verwaltung erledigen lassen. |
| `chfn: PAM: Authentication failure` | Falsches Passwort. | Erneut versuchen; Feststelltaste und Tastaturlayout prüfen. |
| `chfn: invalid room number: '...'` (ebenso `invalid name`, `invalid work phone`, `invalid home phone`) | Doppelpunkt, Komma, Gleichheitszeichen oder Nicht-ASCII-Zeichen bei Telefonnummern. | Wert ohne diese Zeichen eingeben. |
| `chfn: option '-h' requires an argument` | `-h` als Hilfe missverstanden. | `chfn --help` verwenden. |
| `chfn: user '...' does not exist in /etc/passwd` | Konto stammt aus LDAP, SSSD oder einem anderen Verzeichnisdienst. | Änderung im jeweiligen Verzeichnisdienst vornehmen. |
| Optionen wie `-p` fehlen oder bedeuten etwas anderes | Andere Implementierung (util-linux statt Shadow). | `chfn --help` lesen und passende Manpage verwenden. |

Die Meldungstexte wurden mit den im lokalen Programm enthaltenen englischen Meldungen abgeglichen. Mit deutscher Spracheinstellung können sie übersetzt erscheinen. Praktisch ausgelöst wurde nur die Meldung zu einem fehlenden Argument (bei `-R`).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Zuerst nur lesen:** `getent passwd "$USER" | cut -d: -f5` zeigt den aktuellen Stand ohne Änderung.
2. **Einzelne Felder gezielt setzen** statt des interaktiven Modus, wenn du nur eine Angabe ändern willst.
3. **Hilfe mit `--help` aufrufen.** `-h` ist bei dieser Fassung das Privattelefon.
4. **Keine vertraulichen Angaben eintragen;** das Feld ist für alle lokalen Benutzer sichtbar.
5. **Kein `sudo` für das eigene Konto,** solange `CHFN_RESTRICT` das Feld erlaubt. Mit `sudo` werden die vorgesehenen Einschränkungen umgangen.
6. **Bei zentral verwalteten Konten** die Änderung dort vornehmen, wo das Konto tatsächlich gespeichert ist.

### Prüfstand

- **Geprüfte Version:** shadow 4.13, Ubuntu-Paket `passwd 1:4.13+dfsg1-4ubuntu3.2` auf Zorin OS 18.1.
- **Tatsächlich ausgeführt:** `chfn --help`, `chfn -R` ohne Argument (Fehlermeldung), Lesen des eigenen GECOS-Felds mit `getent`, Lesen von `CHFN_RESTRICT` (`rwh`), Prüfung des SUID-Bits und der PAM-Konfiguration `/etc/pam.d/chfn`.
- **Nicht ausgeführt:** jede Änderung an einem Konto, also auch das Beispiel aus Abschnitt 5, sowie `-R` und `--extrausers`. Diese Teile beruhen auf der Debian-Manpage (shadow 4.17.4) und der lokalen Hilfe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chsh` | Ändert die Anmelde-Shell eines Kontos. |
| `passwd` | Ändert Passwort und Passwortstatus. |
| `usermod -c` | Setzt das GECOS-Feld als Verwaltungsbefehl in einem Schritt. |
| `getent passwd` | Liest Kontoeinträge aus allen konfigurierten Quellen. |
| `pinky`, `finger` | Zeigen unter anderem die Angaben aus dem GECOS-Feld an. |

Ausgangseintrag: Datensatz 101 in `index.json` (`chfn`, Kategorie „Benutzer & Rechte“, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die allgemeine Beschreibung, die Platzhaltersyntax und das reine Hilfebeispiel wurden durch die tatsächlichen Felder, die Rechteregel `CHFN_RESTRICT`, die Unterscheidung zwischen Shadow- und util-linux-Fassung sowie die Falle `-h` ersetzt. Die Risikostufe „Vorsicht“ bleibt bestehen und ist jetzt begründet.
