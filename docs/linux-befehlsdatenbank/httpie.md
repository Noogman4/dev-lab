---
id: "httpie"
name: "httpie"
command: "httpie"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "httpie", "plugins", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 158
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert (Paket httpie fehlt); nicht praktisch geprüft"
---

# httpie – HTTPie selbst verwalten: Plugins, Sitzungen, Updates

## 1. Kurzbeschreibung

Unter dem Namen **HTTPie** ist vor allem der HTTP-Client bekannt, dessen Befehle `http` und `https` heißen. Der Befehl **`httpie`** ist etwas anderes: Laut [Debian-Manpage zu httpie](https://manpages.debian.org/trixie/httpie/httpie.1.en.html) ist er die **Verwaltungsschnittstelle** von HTTPie selbst – für Plugins, das Aktualisieren gespeicherter Sitzungen, die Updateprüfung und den Export der Befehlsbeschreibung. HTTP-Anfragen sendet `httpie` nicht; dafür verweist die Manpage ausdrücklich auf `http` und `https`.

**Root-Rechte sind nicht nötig.** Plugins werden laut [HTTPie-Dokumentation](https://httpie.io/docs/cli/main-features) standardmäßig im Konfigurationsordner des Benutzers abgelegt (einstellbar über `plugins_dir`).

Auf dem geprüften System ist HTTPie nicht installiert. Die Dokumentation kennzeichnet `httpie cli` als Beta-Funktion.

## 2. Was macht der Befehl?

Unterbefehle laut Manpage (HTTPie 3.2.4):

| Befehl | Wirkung |
| --- | --- |
| `httpie cli plugins list` | Installierte Plugins anzeigen. |
| `httpie cli plugins install ZIEL` | Plugin von PyPI oder aus lokalem Pfad installieren. |
| `httpie cli plugins upgrade ZIEL` | Plugin aktualisieren. |
| `httpie cli plugins uninstall ZIEL` | Plugin entfernen. |
| `httpie cli sessions upgrade HOST SITZUNG` | Gespeicherte Sitzung auf aktuelles Format bringen. |
| `httpie cli sessions upgrade-all` | Alle benannten Sitzungen aktualisieren. |
| `httpie cli check-updates` | Prüfen, ob eine neue HTTPie-Version verfügbar ist. |
| `httpie cli export-args [-f FORMAT]` | Beschreibung der Optionen von `http` exportieren (Vorgabe JSON). |

Die Manpage nennt zusätzlich die kürzeren Formen `httpie plugins install/upgrade/uninstall/list`.

Laut Dokumentation ist der Plugin-Manager eine dünne Schicht über `pip`; Plugins und fehlende Abhängigkeiten werden im Konfigurationsordner gespeichert.

## 3. Syntax

```text
httpie cli plugins {list,install,upgrade,uninstall} [ZIEL ...]
httpie cli sessions {upgrade,upgrade-all} [OPTIONEN]
httpie cli check-updates
httpie cli export-args [-f FORMAT]
```

```bash
httpie cli plugins list
httpie cli check-updates
httpie cli export-args
```

Das bisherige NetMon-Beispiel `httpie --help` zeigt die Hilfe der Verwaltungsschnittstelle, nicht die des HTTP-Clients. Der Platzhalter `httpie [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert. **Prüfpunkt:** `--help` nicht praktisch geprüft.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-f`, `--format` | Format für `export-args`. | Laut Dokumentation derzeit `json`. |
| `--bind-cookies` | Bei `sessions upgrade`: Cookies ohne Domain an den Host binden. | Verändert Sitzungsdateien. |
| `ZIEL` | Plugin-Name von PyPI oder lokaler Pfad. | – |
| `plugins_dir` (Konfiguration) | Ordner für Plugins. | HTTPie braucht dort Lese- und Schreibrechte. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Plugin-Bestand prüfen und gespeicherte Sitzungen nach einer Aktualisierung anpassen. Voraussetzung: HTTPie installiert. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Plugins ansehen

```bash
httpie cli plugins list
```

Zeigt installierte Plugins; nur lesend.

### Schritt 2: Sitzungen sichern

```bash
cp -a ~/.config/httpie/sessions ~/httpie-sitzungen-sicherung
```

Die Dokumentation nennt `~/.config/httpie/sessions/HOST/NAME.json` als typischen Ablageort.

### Schritt 3: Sitzungen aktualisieren

```bash
httpie cli sessions upgrade-all
```

Bringt alle benannten Sitzungen auf das aktuelle Format.

### Schritt 4: Updateprüfung

```bash
httpie cli check-updates
```

Fragt im Netz nach einer neueren Version. **Prüfpunkt:** Welche Adresse dabei kontaktiert wird, ist nicht dokumentiert worden.

## 6. Typische Anwendungsfälle

- **Anmelde-Plugins** für besondere Verfahren installieren.
- **Sitzungen** nach einem HTTPie-Update anpassen.
- **Werkzeuge anbinden,** die die Optionen von `http` über `export-args` lesen (etwa für Autovervollständigung).

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `plugins install` lädt und installiert Code. Der Kopf verwendet `caution`.

- **Fremder Code:** Plugins von PyPI laufen mit deinen Rechten bei jedem `http`-Aufruf und sehen Anfragen und Zugangsdaten. Nur vertrauenswürdige Plugins installieren.
- **Abhängigkeiten:** Über `pip` können weitere Pakete mitinstalliert werden.
- **Sitzungsdateien** enthalten Anmeldedaten und Cookies im Klartext; `sessions upgrade` verändert sie.
- **Verwechslung:** `httpie` sendet keine HTTP-Anfragen; wer das erwartet, erhält eine Fehlermeldung oder Hilfe.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `httpie: command not found` | HTTPie nicht installiert oder ältere Version ohne Verwaltungsbefehl. | Paket `httpie`; Version prüfen. |
| `httpie example.org` funktioniert nicht | Falscher Befehl für Anfragen. | `http example.org`. |
| Plugin-Installation scheitert | Kein Schreibrecht auf `plugins_dir` oder Netzproblem. | Ordnerrechte und Netz prüfen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für Anfragen `http`/`https`,** für Verwaltung `httpie`.
2. **Vor Sitzungsänderungen sichern.**
3. **Plugins sparsam und nur aus vertrauenswürdigen Quellen.**
4. **Unter Debian/Ubuntu** Plugins möglichst über die Paketverwaltung beziehen, wenn verfügbar. **Prüfpunkt:** Verfügbarkeit nicht geprüft.

### Prüfstand

- **Geprüfte Version:** keine; HTTPie ist nicht installiert. Die Debian-Manpage beschreibt 3.2.4.
- **Quellen gelesen** (Abruf 2026-11-13): Debian-Manpage `httpie(1)` und HTTPie-Dokumentation (Abschnitte Plugin-Manager, `httpie cli`, Sitzungsablage, `plugins_dir`).
- **Nicht geprüft:** alle Aufrufe, Netzwerkverhalten von `check-updates`, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `http`, `https` | Die eigentlichen HTTP-Client-Befehle von HTTPie. |
| `pip` | Grundlage der Plugin-Installation. |
| `curl` | Alternativer HTTP-Client. |

Ausgangseintrag: Datensatz 158 in `index.json` (`httpie`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Platzhalter beschrieb `httpie` wie einen allgemeinen Netzbefehl; tatsächlich ist es die Verwaltungsschnittstelle von HTTPie. Ergänzt wurden Unterbefehle, Plugin-Risiken und die Abgrenzung zu `http`. Die Risikostufe wurde auf „Vorsicht“ angehoben.
