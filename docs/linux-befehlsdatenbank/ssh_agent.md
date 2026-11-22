---
id: "ssh_agent"
name: "ssh-agent"
command: "ssh-agent"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "schluessel", "agent"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit kurzlebigem eigenen Agenten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 170
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# ssh-agent – Entsperrte SSH-Schlüssel für eine Sitzung bereithalten

## 1. Kurzbeschreibung

`ssh-agent` ist laut [Debian-Manpage zu ssh-agent](https://manpages.debian.org/trixie/openssh-client/ssh-agent.1.en.html) ein Programm, das **private Schlüssel für die Anmeldung per öffentlichem Schlüssel** bereithält. Programme wie `ssh` finden den Agenten über Umgebungsvariablen und lassen ihn Anmeldungen signieren – die Passphrase muss dann nur einmal beim Laden mit `ssh-add` eingegeben werden.

**Root-Rechte sind nicht nötig.** Jeder Benutzer startet seinen eigenen Agenten. Auf Desktop-Systemen läuft meist bereits einer; auf dem geprüften System etwa ein Agent der Schlüsselverwaltung der Desktop-Sitzung.

## 2. Was macht der Befehl?

`ssh-agent` öffnet einen **Unix-Domain-Socket** (Vorgabe laut Manpage `$TMPDIR/ssh-XXXXXXXXXX/agent.PPID`) und wartet auf Anfragen. Zwei Variablen machen ihn auffindbar:

- `SSH_AUTH_SOCK` – Pfad des Sockets,
- `SSH_AGENT_PID` – Prozessnummer (für `ssh-agent -k`).

Die Manpage nennt drei Startarten:

| Art | Aufruf | Lebensdauer |
| --- | --- | --- |
| Mit Unterprogramm | `ssh-agent bash` | Endet, wenn das Unterprogramm endet. |
| Für die laufende Shell | `eval "$(ssh-agent -s)"` | Läuft im Hintergrund weiter, bis er beendet wird. |
| Über einen Dienstverwalter | Socket-Aktivierung, etwa durch systemd | Vom Dienstverwalter gesteuert. |

Der Agent gibt private Schlüssel **nie heraus**; er führt nur Signaturen für berechtigte Anfragen aus.

## 3. Syntax

```text
ssh-agent [-c | -s] [-D | -d] [-a SOCKET] [-t DAUER] [BEFEHL [ARGUMENTE]]
ssh-agent [-c | -s] -k
```

```bash
eval "$(ssh-agent -s)"
ssh-agent bash
ssh-agent -t 1h bash
eval "$(ssh-agent -k)"
```

Das bisherige NetMon-Beispiel `ssh-agent --help` ist keine dokumentierte Option. **Prüfpunkt:** Verhalten nicht geprüft. Der Platzhalter `ssh-agent [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-s` | Befehle für sh/bash ausgeben. | Mit `eval` übernehmen. |
| `-c` | Befehle für csh ausgeben. | – |
| `-k` | Agenten aus `SSH_AGENT_PID` beenden. | Mit `eval` werden die Variablen zurückgesetzt. |
| `-t DAUER` | Vorgabe-Lebensdauer geladener Schlüssel. | Ohne Angabe laut Manpage unbegrenzt; `ssh-add -t` hat Vorrang. |
| `-a SOCKET` | Bestimmten Socket-Pfad verwenden. | Rechte des Ordners beachten. |
| `-D`, `-d` | Im Vordergrund bzw. mit Diagnose laufen. | Für Fehlersuche oder Dienstverwalter. |
| `-E md5/sha256` | Hashverfahren für Fingerabdrücke. | – |
| `-O OPTION` | Sonderoptionen, etwa für PKCS#11/FIDO. | Für Fortgeschrittene. |
| `BEFEHL` | Unterprogramm starten. | Agent endet mit dem Unterprogramm. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen **eigenen, kurzlebigen Agenten** verwenden, ohne den Agenten der Desktop-Sitzung zu berühren.

### Schritt 1: Agent mit Unterprogramm starten

```bash
ssh-agent bash
echo "$SSH_AUTH_SOCK"
```

In der neuen Shell zeigt `SSH_AUTH_SOCK` auf einen neuen Socket.

### Schritt 2: Testschlüssel laden

```bash
uebung="$(mktemp -d -t netmon-agent-XXXXXX)" || exit 1
ssh-keygen -q -t ed25519 -N '' -f "$uebung/test_key"
ssh-add "$uebung/test_key"
ssh-add -l
```

Der Testschlüssel ohne Passphrase dient nur der Übung. `ssh-add -l` zeigt ihn im neuen Agenten an.

### Schritt 3: Beenden

```bash
exit
```

Mit dem Ende der Unter-Shell endet auch der Agent; die geladenen Schlüssel sind verschwunden.

### Hinweis aus dem Test

`ssh-agent -s` ohne `eval` und ohne Unterprogramm startet einen Agenten im Hintergrund, der weiterläuft. Im Test blieb so ein zusätzlicher Agent zurück und musste mit `kill PID` beendet werden. Deshalb: entweder `eval "$(ssh-agent -s)"` und später `eval "$(ssh-agent -k)"`, oder die Form mit Unterprogramm.

## 6. Typische Anwendungsfälle

- **Passphrase einmal pro Sitzung** eingeben.
- **Terminal-Sitzungen ohne Desktop** (etwa auf Servern oder in `tmux`) mit eigenem Agenten.
- **Agent-Weiterleitung** zu Sprungrechnern (mit Vorsicht).
- **Zeitlich begrenzte Schlüssel** über `-t`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: Ein Agent hält Anmeldefähigkeiten bereit. Der Kopf verwendet `caution`.

- **Socket-Zugriff = Schlüsselnutzung:** Wer auf den Socket zugreifen kann (eigene Prozesse, Root), kann sich mit den geladenen Schlüsseln anmelden.
- **Weiterleitung (`ssh -A`):** Root auf dem Zielrechner kann den weitergeleiteten Agenten nutzen.
- **Vergessene Agenten** laufen mit geladenen Schlüsseln weiter; `-t` begrenzt das.
- **Mehrere Agenten** verwirren: `ssh-add` lädt in den Agenten aus `SSH_AUTH_SOCK`, nicht unbedingt in den, den man meint.
- **`-a` mit eigenem Pfad:** Ein Socket in einem für andere beschreibbaren Ordner ist angreifbar.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `Could not open a connection to your authentication agent.` | `SSH_AUTH_SOCK` fehlt oder Agent beendet. | Agent starten; `eval` nicht vergessen. |
| Ausgabe von `ssh-agent -s` erscheint, aber nichts ändert sich | Ohne `eval` werden die Variablen nicht übernommen. | `eval "$(ssh-agent -s)"`. |
| Viele Agent-Prozesse | Wiederholt ohne `-k` gestartet. | `ssh-agent -k` oder `kill PID`. |
| `-k` meldet fehlende Variable | `SSH_AGENT_PID` nicht gesetzt. | PID mit `ps` ermitteln. **Prüfpunkt:** Wortlaut nicht geprüft. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Auf Desktops den vorhandenen Agenten nutzen,** keinen zweiten starten.
2. **Wenn eigener Agent: `ssh-agent bash`** – er endet automatisch.
3. **`-t` für eine Vorgabe-Lebensdauer.**
4. **Agent-Weiterleitung sparsam.**

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** kurzlebiger Agent über `ssh-agent bash -c '…'` mit Testschlüssel (Laden, Auflisten, Entfernen; Agent endete mit der Unter-Shell). Ein versehentlich mit `ssh-agent -s` gestarteter Hintergrundagent wurde sofort mit `kill` beendet. Vorhandene Agenten der Sitzung wurden nicht verändert.
- **Nicht geprüft:** `eval`-Form in einer dauerhaften Shell, `-k`, `-t`, `-a`, Socket-Aktivierung, Weiterleitung.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh-add` | Lädt, listet und entfernt Schlüssel im Agenten. |
| `ssh` | Nutzt den Agenten zur Anmeldung. |
| `ssh-keygen` | Erzeugt Schlüssel. |
| `gpg-agent` | Kann in manchen Einrichtungen die Rolle des SSH-Agenten übernehmen. **Prüfpunkt:** nicht geprüft. |

Ausgangseintrag: Datensatz 170 in `index.json` (`ssh-agent`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Startarten, Umgebungsvariablen, Optionen und Risiken bereitgehaltener Schlüssel ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
