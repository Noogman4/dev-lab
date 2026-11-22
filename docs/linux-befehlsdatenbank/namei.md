---
id: "namei"
name: "namei"
command: "namei"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "safe"
tags: ["benutzer", "rechte", "pfade", "symlinks", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 114
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# namei – Pfade Schritt für Schritt auflösen und Rechte entlang des Wegs zeigen

## 1. Kurzbeschreibung

`namei` zerlegt einen Pfad in seine einzelnen Bestandteile und zeigt für jeden Teil Typ, Rechte und Eigentümer. Symbolische Links werden sichtbar aufgelöst. So findest du schnell heraus, **an welcher Stelle** ein Zugriff scheitert oder wohin ein Link wirklich führt.

**Root-Rechte sind nicht nötig.** `namei` liest nur. Es zeigt das, was dein Konto auf dem Weg sehen darf; an nicht betretbaren Ordnern endet die Auswertung mit einer Fehlermeldung.

## 2. Was macht der Befehl?

Für jeden angegebenen Pfad beginnt `namei` mit einer Zeile `f: PFAD` und listet dann jeden Teil des Weges in einer eigenen Zeile. Ein Buchstabe am Zeilenanfang kennzeichnet den Typ:

| Zeichen | Bedeutung |
| --- | --- |
| `d` | Ordner |
| `D` | Ordner, der ein Einhängepunkt ist (nur mit `-x`) |
| `l` | Symbolischer Link; das Ziel folgt eingerückt |
| `-` | Normale Datei |
| `s`, `b`, `c`, `p` | Socket, Block-, Zeichengerät, benannte Pipe |
| `?` | Fehler, etwa fehlende Rechte |

Die Zeichen und Optionen folgen der [Debian-Manpage zu namei](https://manpages.debian.org/trixie/util-linux/namei.1.en.html). `namei` gehört zu **util-linux** und ist auf den meisten Linux-Distributionen vorinstalliert.

Ein wichtiger Unterschied zu `ls -l`: `ls -l` zeigt nur den letzten Teil eines Pfads. Für den Zugriff braucht man aber auf **jedem Ordner davor** das Recht `x` (betreten). `namei -l` zeigt alle diese Stufen auf einmal.

## 3. Syntax

```text
namei [OPTIONEN] PFAD ...
```

```bash
namei -l /var/www/html/index.html
namei /usr/bin/python3
namei -x -l /media/usb/datei.txt
```

Das bisherige NetMon-Beispiel `namei --help` zeigt nur die Hilfe; der Platzhalter `namei [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-l`, `--long` | Langes Format: Rechte, Eigentümer, ausgerichtet. | Entspricht `-m -o -v`; die häufigste Wahl. |
| `-m`, `--modes` | Rechtebits wie bei `ls` anzeigen. | Zum Beispiel `drwxr-xr-x`. |
| `-o`, `--owners` | Eigentümer und Gruppe anzeigen. | Namen statt Nummern. |
| `-v`, `--vertical` | Rechte und Eigentümer untereinander ausrichten. | Bessere Lesbarkeit. |
| `-n`, `--nosymlinks` | Symbolischen Links nicht folgen. | Zeigt nur den Link selbst. |
| `-x`, `--mountpoints` | Einhängepunkte mit `D` markieren. | Hilft bei Problemen mit eingehängten Laufwerken. |
| `-Z`, `--context` | Sicherheitskontext (SELinux) anzeigen. | Ohne SELinux erscheint `?`. |
| `-h`, `--help`, `-V`, `--version` | Hilfe beziehungsweise Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen symbolischen Link verfolgen und herausfinden, an welchem Ordner ein Zugriff scheitert. Alles geschieht mit eigenen Übungsdateien.

### Schritt 1: Übungsstruktur anlegen

```bash
uebung="$(mktemp -d -t netmon-namei-XXXXXX)" || exit 1
cd "$uebung" || exit 1
mkdir -p a/b
printf 'x\n' > a/b/datei
ln -s a/b/datei verweis
```

### Schritt 2: Link auflösen

```bash
namei verweis
```

Ausgabe:

```text
f: verweis
 l verweis -> a/b/datei
   d a
   d b
   - datei
```

Die Einrückung zeigt, dass `a`, `b` und `datei` zum Ziel des Links gehören.

### Schritt 3: Rechte entlang des Pfads

```bash
namei -l "$PWD/verweis"
```

Jetzt erscheinen alle Ordner ab `/` mit Rechten und Eigentümern. Du siehst zum Beispiel, dass `/tmp` die Rechte `drwxrwxrwt` hat.

### Schritt 4: Fehlerstelle finden

```bash
chmod 000 a/b
namei -l a/b/datei
echo $?
chmod 755 a/b
```

`namei` zeigt `d--------- ... b` und darunter `datei - Permission denied`; Rückgabewert `1`. Damit ist klar: Der Ordner `b` blockiert. Die letzte Zeile stellt die Rechte wieder her.

## 6. Typische Anwendungsfälle

- **Webserver liefert 403:** `namei -l /var/www/seite/index.html` zeigt, ob ein Ordner auf dem Weg für andere nicht betretbar ist.
- **„Too many levels of symbolic links“:** `namei` zeigt die Schleife. Im Test brach es mit `exceeded limit of symlinks` ab und listete die Kette.
- **Wohin zeigt ein Programm wirklich?** `namei /usr/bin/python3` zeigt `python3 -> python3.12`.
- **Probleme mit eingehängten Laufwerken:** `namei -x -l` markiert, wo ein anderes Dateisystem beginnt; dort gelten dessen Rechte und Einhängeoptionen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`namei` ist rein lesend und verändert nichts. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde auf `safe` gesenkt.

Zu beachten:

- **Sichtbare Informationen:** Die Ausgabe nennt Eigentümer, Gruppen und Ordnerstrukturen. Beim Weitergeben in Foren oder Tickets persönliche Pfade prüfen.
- **Nur klassische Rechte:** `namei` zeigt die Rechtebits, aber keine ACLs und keine Einhängeoptionen wie `noexec`. Ein `+` bei ACLs fehlt in der Ausgabe. Für ACLs ist `getfacl`, für Einhängeoptionen `findmnt` nötig.
- **Keine Garantie für den Zugriff:** Sicherheitsmodule wie AppArmor oder SELinux können trotz passender Rechte ablehnen.
- **Bei Fehlern mit `sudo` gegenprüfen:** Mit Root-Rechten sieht man auch hinter gesperrte Ordner. Das ist für die Diagnose nützlich, zeigt aber nicht mehr, was das eigentlich betroffene Konto sieht.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `... - Permission denied` | Ordner davor nicht betretbar (`x` fehlt). | Ordner mit den Rechten in der Zeile darüber prüfen. |
| `... - No such file or directory` | Pfadteil fehlt oder Link zeigt ins Leere. | Schreibweise und Linkziel prüfen. |
| `namei: ...: exceeded limit of symlinks` | Link-Schleife. | Kette in der Ausgabe verfolgen und einen Link korrigieren. |
| `?` statt Kontext bei `-Z` | Kein SELinux oder ohne Unterstützung gebaut. | Normal auf Systemen ohne SELinux. |
| Rechte passen, Zugriff scheitert trotzdem | ACL, Einhängeoption oder Sicherheitsmodul. | `getfacl`, `findmnt -T PFAD`, Systemprotokoll prüfen. |

In allen Fehlerfällen endete `namei` im Test mit Rückgabewert `1`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Fast immer `namei -l` verwenden;** es zeigt alles Wichtige.
2. **Absolute Pfade angeben,** damit die Kette ab `/` sichtbar wird.
3. **Gezielt von oben nach unten lesen:** Die erste Zeile mit fehlendem `x` für dein Konto ist meist die Ursache.
4. **Zum Prüfen für ein anderes Konto** `sudo -u KONTO namei -l PFAD` verwenden; dann siehst du dessen Sicht.

### Prüfstand

- **Geprüfte Version:** namei aus util-linux 2.39.3.
- **Tatsächlich ausgeführt** im Testordner: Linkauflösung, `-l` mit absolutem Pfad, Ablehnung an einem Ordner mit `000` (Rückgabe 1), `-n`, Link-Schleife (Meldung `exceeded limit of symlinks`, Rückgabe 1), `-x -m` an `/proc/self/root`, `-Z` ohne SELinux, nicht vorhandener Pfad, Auflösung von `/usr/bin/python3`.
- **Nicht geprüft:** `-Z` mit aktivem SELinux, Gerätedateien, Netzlaufwerke, `sudo -u` für ein anderes Konto.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ls -ld` | Zeigt Rechte eines einzelnen Eintrags. |
| `readlink -f`, `realpath` | Geben das endgültige Ziel eines Pfads aus, ohne Zwischenschritte. |
| `stat` | Zeigt alle Metadaten eines einzelnen Eintrags. |
| `getfacl` | Zeigt ACLs, die `namei` nicht berücksichtigt. |
| `findmnt -T` | Zeigt das Dateisystem und die Einhängeoptionen eines Pfads. |

Ausgangseintrag: Datensatz 114 in `index.json` (`namei`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Ausgabeformat, Diagnoseanwendungen und einen geprüften Ablauf ersetzt. Die Risikostufe wurde auf „sicher lesend“ gesenkt.
