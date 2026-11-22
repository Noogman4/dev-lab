---
id: "ssh_add"
name: "ssh-add"
command: "ssh-add"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "schluessel", "agent"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testschlüssel in eigenem Agenten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 169
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# ssh-add – Private SSH-Schlüssel in den SSH-Agenten laden

## 1. Kurzbeschreibung

`ssh-add` lädt private SSH-Schlüssel in den laufenden **SSH-Agenten** (`ssh-agent`). Der Agent hält die entschlüsselten Schlüssel im Arbeitsspeicher bereit, sodass `ssh`, `scp`, `git` und andere Programme sie nutzen können, ohne bei jeder Verbindung nach der Passphrase zu fragen. Außerdem listet und entfernt `ssh-add` geladene Schlüssel.

**Root-Rechte sind nicht nötig.** `ssh-add` arbeitet nur mit dem Agenten der eigenen Sitzung.

Grundlage ist die [Debian-Manpage zu ssh-add](https://manpages.debian.org/trixie/openssh-client/ssh-add.1.en.html).

## 2. Was macht der Befehl?

- Ohne Argumente lädt `ssh-add` die Standardschlüssel `~/.ssh/id_rsa`, `id_ecdsa`, `id_ecdsa_sk`, `id_ed25519` und `id_ed25519_sk`, soweit vorhanden.
- Mit Dateinamen lädt es genau diese Schlüssel. Ist ein Schlüssel mit Passphrase geschützt, fragt `ssh-add` danach.
- Voraussetzung: Ein Agent läuft, und die Variable `SSH_AUTH_SOCK` nennt dessen Socket. Auf Desktop-Systemen startet die Sitzung meist selbst einen Agenten.

`ssh-add` verändert **keine Schlüsseldateien**. Geladene Schlüssel verschwinden, wenn der Agent endet, die Lebensdauer abläuft oder sie mit `-d`/`-D` entfernt werden.

Rückgabewerte laut Manpage: `0` Erfolg, `1` Befehl fehlgeschlagen, `2` Agent nicht erreichbar.

## 3. Syntax

```text
ssh-add [OPTIONEN] [SCHLÜSSELDATEI ...]
ssh-add -l | -L
ssh-add -d [SCHLÜSSELDATEI ...] | -D
```

```bash
ssh-add
ssh-add -t 1h ~/.ssh/id_ed25519
ssh-add -l
ssh-add -D
```

Das bisherige NetMon-Beispiel `ssh-add --help` ist keine dokumentierte Option. **Prüfpunkt:** Verhalten nicht geprüft; die Optionen stehen in der Manpage. Der Platzhalter `ssh-add [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-l` | Fingerabdrücke der geladenen Schlüssel. | Rückgabewert `1`, wenn keiner geladen ist. |
| `-L` | Öffentliche Schlüssel der geladenen Identitäten. | Zum Kopieren auf Server. |
| `-t DAUER` | Lebensdauer beim Hinzufügen, in Sekunden oder z. B. `1h`. | Schlüssel wird danach automatisch entfernt. |
| `-c` | Jede Nutzung muss über `ssh-askpass` bestätigt werden. | Schutz bei Agent-Weiterleitung. |
| `-d DATEI` | Bestimmten Schlüssel entfernen. | Erwartet den öffentlichen Schlüssel; `.pub` wird ergänzt. |
| `-D` | Alle Schlüssel entfernen. | – |
| `-x`, `-X` | Agenten mit Passwort sperren bzw. entsperren. | – |
| `-h ZIEL` | Schlüssel auf bestimmte Zielrechner beschränken. | Laut Manpage seit OpenSSH 8.9. |
| `-E md5/sha256` | Hashverfahren für Fingerabdrücke. | Vorgabe `sha256`. |
| `-q` | Nach Erfolg nichts ausgeben. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen eigens erzeugten **Testschlüssel** in einen **eigenen, kurzlebigen Agenten** laden, anzeigen und wieder entfernen – ohne die echten Schlüssel oder den Agenten der Sitzung zu berühren.

### Schritt 1: Testschlüssel erzeugen

```bash
uebung="$(mktemp -d -t netmon-sshadd-XXXXXX)" || exit 1
cd "$uebung" || exit 1
ssh-keygen -q -t ed25519 -N '' -C 'uebung@netmon' -f ./uebung_key
```

`-N ''` erzeugt einen Schlüssel ohne Passphrase – nur für diese Übung sinnvoll.

### Schritt 2: Eigenen Agenten mit Unter-Shell starten

```bash
ssh-agent bash
```

`ssh-agent bash` startet einen neuen Agenten und darin eine Shell, in der `SSH_AUTH_SOCK` auf diesen Agenten zeigt. Mit `exit` endet beides.

### Schritt 3: Laden und anzeigen

```bash
ssh-add ./uebung_key
ssh-add -l
```

Ausgaben im Test: `Identity added: ./uebung_key (uebung@netmon)` und eine Zeile wie `256 SHA256:… uebung@netmon (ED25519)`.

### Schritt 4: Mit Lebensdauer laden, entfernen

```bash
ssh-add -d ./uebung_key
ssh-add -l
ssh-add -t 60 ./uebung_key
ssh-add -D
exit
```

Nach `-d` meldet `-l` `The agent has no identities.` (Rückgabewert `1`). `-t 60` meldet `Lifetime set to 60 seconds`. `-D` meldet `All identities removed.`

## 6. Typische Anwendungsfälle

- **Passphrase nur einmal pro Sitzung** eingeben.
- **Git über SSH** ohne wiederholte Abfragen.
- **Zeitlich begrenzter Zugriff** mit `-t` auf gemeinsam genutzten Rechnern.
- **Prüfen,** welche Schlüssel der Agent gerade anbietet (`-l`), wenn eine Anmeldung scheitert.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft auf `-l` und `-L` zu. Das Laden von Schlüsseln hat Sicherheitsfolgen; der Kopf verwendet `caution`.

- **Entsperrte Schlüssel:** Solange ein Schlüssel geladen ist, kann jeder Prozess mit Zugriff auf den Agenten-Socket ihn verwenden – also Programme unter deinem Konto und Root.
- **Agent-Weiterleitung:** Mit `ssh -A` kann auch Root auf dem entfernten Rechner den Agenten nutzen. `-c`, `-h` und `-t` begrenzen das Risiko. Die Manpage weist darauf hin, dass Zielbeschränkungen nur wirken, wenn Agent und kooperierendes `ssh` sie durchsetzen.
- **Unbeaufsichtigter Rechner:** Geladene Schlüssel bleiben nutzbar, bis sie entfernt werden; `ssh-add -D` oder `-x` vor Pausen.
- **Zu viele Schlüssel:** Server brechen nach mehreren Fehlversuchen ab, wenn der Agent viele Schlüssel anbietet. **Prüfpunkt:** nicht praktisch geprüft.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `Could not open a connection to your authentication agent.` (Rückgabe 2) | Kein Agent oder `SSH_AUTH_SOCK` nicht gesetzt (im Test). | Agent starten, etwa `eval "$(ssh-agent -s)"`. |
| `The agent has no identities.` (Rückgabe 1) | Kein Schlüssel geladen. | `ssh-add DATEI`. |
| `WARNING: UNPROTECTED PRIVATE KEY FILE!` | Schlüsseldatei für andere lesbar. | `chmod 600 DATEI`. |
| `Bad passphrase, try again` | Falsche Passphrase. | Erneut eingeben. **Prüfpunkt:** nicht ausgelöst. |
| Schlüssel verschwindet | Lebensdauer (`-t`) abgelaufen oder Agent neu gestartet. | Neu laden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Schlüssel immer mit Passphrase** schützen; der Agent nimmt die Wiederholung ab.
2. **`-t` verwenden,** besonders auf fremden oder gemeinsam genutzten Rechnern.
3. **`ssh-add -l` zur Kontrolle.**
4. **Agent-Weiterleitung nur zu vertrauenswürdigen Servern.**
5. **Zum Üben einen eigenen Agenten** mit `ssh-agent bash` verwenden.

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt** mit einem Testschlüssel in einem eigenen, kurzlebigen Agenten: Laden, `-l`, `-L`, `-d`, leere Liste (Rückgabe 1), `-t 60`, `-D`; außerdem `ssh-add -l` ohne erreichbaren Agenten (Rückgabe 2). Echte Schlüssel und der Agent der Sitzung wurden nicht verwendet.
- **Nicht geprüft:** Passphrasenabfrage, `-c`, `-h`, `-x`/`-X`, FIDO- und PKCS#11-Schlüssel, `--help`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh-agent` | Der Agent, den `ssh-add` befüllt. |
| `ssh-keygen` | Erzeugt Schlüssel und ändert Passphrasen. |
| `ssh` | Nutzt die geladenen Schlüssel. |
| `ssh-copy-id` | Hinterlegt öffentliche Schlüssel auf Servern. |

Ausgangseintrag: Datensatz 169 in `index.json` (`ssh-add`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, Optionen, Rückgabewerte, Risiken geladener Schlüssel und einen isoliert geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
