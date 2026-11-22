---
id: "delgroup"
name: "delgroup"
command: "delgroup"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "gruppen", "kontenverwaltung", "debian"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 106
reviewed_at: "2026-11-13"
locally_checked_version: "adduser 3.137ubuntu1; nur Hilfe, Version und Nicht-Root-Ablehnung"
---

# delgroup – Gruppe vom System entfernen (Debian-Werkzeug)

## 1. Kurzbeschreibung

`delgroup` entfernt eine Gruppe aus der Gruppendatenbank (`/etc/group` und `/etc/gshadow`). Es gehört zum Paket **adduser** von Debian und Ubuntu und ist dort ein Verweis auf das Perl-Programm `deluser`. Intern ruft es das Basiswerkzeug `groupdel` auf und ergänzt Prüfungen und Konfigurationsregeln.

**Root-Rechte sind immer nötig.** Als normaler Benutzer bricht `delgroup` mit `fatal: Only root may remove a user or group from the system.` und dem Rückgabewert `54` ab.

## 2. Was macht der Befehl?

`delgroup GRUPPE` löscht den Gruppeneintrag. Was dabei **nicht** passiert, ist ebenso wichtig:

- Dateien, die dieser Gruppe gehören, werden weder gelöscht noch umgestellt. Sie behalten die numerische Gruppen-ID (GID). `ls -l` zeigt danach nur noch eine Zahl.
- Benutzerkonten werden nicht gelöscht; sie verlieren lediglich die Mitgliedschaft.
- Die **primäre Gruppe** eines vorhandenen Kontos kann nicht gelöscht werden.

Die Debian-Manpage zu [groupdel](https://manpages.debian.org/trixie/passwd/groupdel.8.en.html) rät ausdrücklich, danach alle Dateisysteme auf verbliebene Dateien dieser Gruppe zu prüfen. Wird die freie GID später an eine neue Gruppe vergeben, gehören ihr diese alten Dateien automatisch.

Die Beschreibung der Modi und Optionen folgt der [Debian-Manpage zu delgroup/deluser](https://manpages.debian.org/trixie/adduser/delgroup.8.en.html). Lokal geprüft wurde die inhaltlich gleiche Manpage von adduser 3.137ubuntu1.

### Andere Systeme

`delgroup` ist kein allgemeiner Linux-Standardbefehl. Fedora, Arch und andere Distributionen verwenden direkt `groupdel`. BusyBox (etwa unter Alpine Linux) hat ein eigenes `delgroup [BENUTZER] GRUPPE` mit anderem Funktionsumfang; siehe [BusyBox-Befehlsübersicht](https://busybox.net/downloads/BusyBox.html). Dieses Dokument beschreibt die Debian-Fassung.

## 3. Syntax

```text
delgroup [--system] [--only-if-empty] [--conf DATEI] GRUPPE
deluser --group [OPTIONEN] GRUPPE
deluser BENUTZER GRUPPE
```

- Die ersten beiden Formen löschen eine Gruppe.
- Die dritte Form entfernt nur einen Benutzer aus einer Gruppe; die Gruppe bleibt bestehen. Für diese Aufgabe ist sie die passende, weniger folgenreiche Wahl.

```bash
sudo delgroup --only-if-empty altprojekt
sudo deluser anna altprojekt
```

Das bisherige NetMon-Beispiel `delgroup --help` zeigt nur die Hilfe; der Platzhalter `delgroup [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--only-if-empty` | Nur löschen, wenn die Gruppe keine Mitglieder mehr hat. | Sonst Abbruch mit Rückgabewert `41`. Empfohlen. |
| `--system` | Nur löschen, wenn es eine Systemgruppe ist. | Existiert die Gruppe nicht, gibt es keinen Fehler. Für Paketskripte gedacht. |
| `--conf DATEI` | Andere Konfigurationsdatei statt `/etc/deluser.conf` verwenden. | Mehrfach möglich. |
| `--quiet`, `--verbose`, `--debug` | Ausgabemenge steuern. | Laut Manpage veraltet; Ersatz sind die `--...msglevel`-Optionen. |
| `--stdoutmsglevel`, `--stderrmsglevel`, `--logmsglevel` | Mindestpriorität für Konsole und Protokoll. | Werte `trace`, `debug`, `info`, `warn`, `err`, `fatal`. |
| `--help`, `--version` | Hilfe beziehungsweise Version anzeigen. | Funktionieren auch ohne Root. |

Die Option `ONLY_IF_EMPTY` in `/etc/deluser.conf` kann `--only-if-empty` zur Vorgabe machen. Auf dem geprüften System ist sie auskommentiert, Standardwert `0`: **Gruppen werden auch mit Mitgliedern gelöscht.**

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine nicht mehr benötigte Projektgruppe `altprojekt` sicher entfernen. Das verändert die Gruppendatenbank und ist deshalb ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Gruppe und Mitglieder ansehen

```bash
getent group altprojekt
```

Die Ausgabe hat die Form `altprojekt:x:1050:anna,ben`. Die dritte Spalte ist die GID, die vierte nennt zusätzliche Mitglieder.

### Schritt 2: Prüfen, ob sie primäre Gruppe eines Kontos ist

```bash
awk -F: '$4 == 1050 {print $1}' /etc/passwd
```

Gibt der Befehl Kontonamen aus, kann `delgroup` die Gruppe nicht entfernen. Diese Konten brauchen erst eine andere primäre Gruppe. Bei Konten aus LDAP oder SSSD ist zusätzlich `getent passwd` heranzuziehen.

### Schritt 3: Dateien der Gruppe finden

```bash
sudo find / -xdev -group altprojekt -print 2>/dev/null
```

`-xdev` bleibt auf dem Dateisystem von `/`. Weitere Dateisysteme wie `/home` auf eigener Partition müssen einzeln durchsucht werden. Gefundene Dateien vorher einer anderen Gruppe zuordnen (`chgrp`) oder bewusst behalten.

### Schritt 4: Mitglieder austragen und Gruppe löschen

```bash
sudo deluser anna altprojekt
sudo deluser ben altprojekt
sudo delgroup --only-if-empty altprojekt
```

Die letzte Zeile löscht nur, wenn wirklich keine Mitglieder mehr eingetragen sind.

### Schritt 5: Ergebnis kontrollieren

```bash
getent group altprojekt
echo $?
```

Keine Ausgabe und Rückgabewert `2` von `getent` bedeuten: Die Gruppe existiert nicht mehr.

## 6. Typische Anwendungsfälle

- **Aufräumen nach Projektende:** leere Projektgruppen entfernen.
- **Paketdeinstallation:** Paketskripte nutzen `delgroup --system NAME`, damit nur Systemgruppen betroffen sind und eine bereits fehlende Gruppe keinen Fehler auslöst.
- **Benutzer aus Gruppe nehmen:** `deluser BENUTZER GRUPPE` – kein Löschen der Gruppe nötig.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Nicht umkehrbar ohne Sicherung

Eine gelöschte Gruppe kann zwar neu angelegt werden, aber Mitgliederliste, Gruppenpasswort und Verwalter aus `/etc/gshadow` sind weg. Verwende dieselbe GID, damit alte Dateien wieder richtig zugeordnet werden.

### Verwaiste Dateien und GID-Wiederverwendung

Dateien behalten die alte GID. Eine später neu angelegte Gruppe mit derselben GID erhält damit ungewollt Zugriff. Das ist eine reale Datenoffenlegungsgefahr auf Mehrbenutzersystemen.

### Systemgruppen

Das Löschen von Gruppen wie `sudo`, `adm`, `audio`, `video`, `docker` oder Dienstgruppen kann Verwaltung, Hardwarezugriff oder Dienste lahmlegen. Ohne `--system` unterscheidet `delgroup` nicht zwischen System- und Benutzergruppen.

### Eingeschränkte sudo-Freigaben sind keine Absicherung

Die Manpage warnt: `deluser` und `delgroup` über `sudo` mit eingeschränkten Parametern freizugeben ist leicht zu umgehen, unter anderem über `--conf`. Wer Teilrechte braucht, sollte ein eigenes geprüftes Hilfsskript freigeben.

Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ bleibt bestehen. Die Root-Angabe wurde von „Nein/selten“ auf „erforderlich“ korrigiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `fatal: Only root may remove a user or group from the system.` (54) | Ohne Root aufgerufen. | Nur mit Verwaltungsrechten und nach Prüfung. |
| Rückgabewert `12` | Gruppe existiert nicht. | Namen mit `getent group` prüfen. |
| Rückgabewert `41` | Gruppe ist nicht leer (`--only-if-empty`). | Mitglieder mit `deluser BENUTZER GRUPPE` austragen. |
| Rückgabewert `13` | Bei `--system`: Gruppe ist keine Systemgruppe. | Absicht prüfen; ohne `--system` nur bewusst löschen. |
| `groupdel: cannot remove the primary group of user '...'`, danach Rückgabewert `82` | Gruppe ist primäre Gruppe eines Kontos; `delgroup` prüft das nicht selbst, sondern `groupdel` lehnt ab. | Konto zuerst mit `usermod -g` umstellen oder entfernen. |
| `delgroup: command not found` | Keine Debian-Familie oder Paket `adduser` fehlt. | `groupdel` verwenden. |

Die Rückgabewerte stammen aus dem Abschnitt EXIT VALUES der [Debian-Manpage zu adduser](https://manpages.debian.org/trixie/adduser/adduser.8.en.html), auf den die delgroup-Manpage verweist. Die Zuordnung des Primärgruppenfalls zu Wert `82` ergibt sich aus dem lokalen Perl-Quelltext von `deluser` (Aufruf von `groupdel` über eine Hilfsfunktion, die bei einem Fehler des Unterprogramms mit 82 endet). Praktisch ausgelöst wurde nur Wert `54`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Nur Benutzer austragen?** Dann `deluser BENUTZER GRUPPE` statt `delgroup`.
2. **Immer `--only-if-empty` verwenden,** solange nicht bewusst eine Gruppe mit Mitgliedern gelöscht werden soll.
3. **Vorher sichern:** `sudo cp -a /etc/group /etc/gshadow /root/` oder eine vollständige Systemsicherung.
4. **Dateien suchen,** bevor die GID frei wird.
5. **Systemgruppen nicht anfassen,** wenn ihre Aufgabe unklar ist.

### Prüfstand

- **Geprüfte Version:** adduser 3.137ubuntu1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie zum Vergleich.
- **Tatsächlich ausgeführt:** `delgroup --help`, `deluser --version`, `delgroup gibtsnicht` als normaler Benutzer (Rückgabe 54), Lesen von `/etc/deluser.conf` (alle Werte auskommentiert).
- **Nicht ausgeführt:** jede Löschung, also das Beispiel aus Abschnitt 5, sowie `--system` und die Rückgabewerte 12, 13 und 41.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `groupdel` | Basiswerkzeug aus der Shadow-Suite; auf allen gängigen Distributionen vorhanden. |
| `deluser` | Gleiches Programm; entfernt Konten oder Benutzer aus Gruppen. |
| `addgroup`, `groupadd` | Legen Gruppen an. |
| `gpasswd -d` | Entfernt einen Benutzer aus einer Gruppe. |
| `getent group` | Zeigt Gruppen aus allen konfigurierten Quellen. |
| `find -group`, `find -nogroup` | Finden Dateien einer Gruppe beziehungsweise verwaiste Dateien. |

Ausgangseintrag: Datensatz 106 in `index.json` (`delgroup`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert. Der Hilfe-Platzhalter wurde durch die Debian-spezifische Einordnung, die Folgen für Dateien und GIDs, die Rückgabewerte und einen vorsichtigen Ablauf ersetzt.
