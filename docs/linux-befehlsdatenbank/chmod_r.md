---
id: "chmod_r"
name: "chmod -R"
command: "chmod -R"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "danger"
tags: ["aufgabenorientierte hilfe", "chmod_r"]
status: "Ausgearbeitet; Rechteänderung ausschließlich an eigenen Testdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 49
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils chmod 9.4"
---

# chmod -R – Rechte rekursiv ändern, ohne Dateien und Ordner gleichzusetzen

## 1. Kurzbeschreibung

`chmod -R` verändert Dateimodusrechte rekursiv in einem Verzeichnisbaum. `-R` ist eine Option von `chmod`, kein eigenes Programm. Ein falsch gewählter Startpfad kann sehr viele Dateien betreffen.

**Für eigene Dateien als deren Eigentümer sind keine Root-Rechte nötig.** Bei fremdem Eigentum werden entsprechende Privilegien benötigt. Die Aktion verändert Zugriffsrechte und ist ausdrücklich nicht nur lesend.

## 2. Was macht der Befehl?

Die üblichen Rechte unterscheiden Eigentümer (`u`), Gruppe (`g`) und andere Nutzer (`o`). `r`, `w` und `x` stehen für Lesen, Schreiben und Ausführen; bei Verzeichnissen bedeutet `x` das Durchsuchen beziehungsweise Betreten über bekannte Namen.

Dateien und Ordner brauchen nicht dieselben Rechte. Eine pauschale Rekursion mit `755` macht gewöhnliche Dateien ausführbar und gewährt Gruppe sowie anderen Leserechte. Für einen privaten eigenen Bestand ist das oft nicht die beabsichtigte Wirkung.

Quellen: [Distributions-Manpage zu GNU chmod](https://manpages.debian.org/trixie/coreutils/chmod.1.en.html) und lokale Hilfe von coreutils 9.4. Die aktuelle Manpage beschreibt auch neuere Linkoptionen, die in der lokalen Hilfe nicht angeboten werden. Solche Optionen werden hier nicht als lokal verfügbar vorausgesetzt.

## 3. Syntax

```text
chmod -R [OPTIONEN] SYMBOLISCHER_MODUS PFAD
chmod -R [OPTIONEN] OKTALMODUS PFAD
```

```bash
chmod -R --preserve-root u+rwX,go-rwx "Material"
```

Dieser bewusst private Modus gibt dem Eigentümer Lesen/Schreiben und nötiges Durchsuchen, entfernt normale Gruppen-/Andere-Rechte und behandelt Großbuchstaben-`X` anders als kleines `x`. Es ist kein allgemeines Reparaturrezept für gemeinsam genutzte oder systemweite Verzeichnisse.

## 4. Wichtige Optionen

| Bestandteil | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-R`, `--recursive` | Verzeichnisbaum bearbeiten. | Umfang vor dem Aufruf prüfen. |
| `--preserve-root` | Rekursive Bearbeitung von `/` ablehnen. | Schützt nicht vor jedem anderen falschen Startpfad. |
| `-v` | Für jeden bearbeiteten Eintrag melden. | Kann bei großen Bäumen viel Ausgabe erzeugen. |
| `-c` | Nur tatsächliche Änderungen melden. | Hilfreich für einen kleinen nachvollziehbaren Test. |
| `-f` | Viele Fehlermeldungen unterdrücken. | Für erste Diagnose vermeiden. |
| `--reference=DATEI` | Modus von Referenz übernehmen. | Eine falsche Referenz überträgt falsche Rechte. |
| `u`, `g`, `o`, `a` | Betroffene Nutzerklassen. | Explizite Klassen vermeiden manche umask-Abhängigkeiten. |
| `+`, `-`, `=` | Rechte ergänzen, entfernen oder setzen. | `=` kann bisherige normale Rechte beseitigen. |
| `X` | Ausführen/Suchen nur bei Verzeichnissen oder bereits irgendwo ausführbaren Dateien. | Anders als pauschales `x`. |
| `--` | Ende der Optionen. | Für ungewöhnliche Startnamen hilfreich. |

Spezialbits wie setuid, setgid und sticky besitzen eigene Regeln. Ein einfaches Zahlenrezept nicht als vollständiges Entfernen aller Sonderrechte behaupten, insbesondere bei Verzeichnissen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur eigenen Testbereich anlegen

```bash
chmod --version
uebung="$(mktemp -d -t netmon-chmod-XXXXXX)"
cd "$uebung"
pwd
mkdir -p "Material/Unterordner"
printf '%s\n' 'Eigene Rechtestestdatei.' > "Material/Unterordner/notiz.txt"
```

Nur nach erfolgreichem Wechsel fortfahren. Keine echten Projekt- oder Systempfade für die Übung verwenden.

### Schritt 2: Anfangszustand lesen

```bash
ls -ld "Material" "Material/Unterordner"
ls -l "Material/Unterordner/notiz.txt"
```

Eigentum und Rechte ansehen. Ordner benötigen für normalen Zugriff die passende Suchberechtigung. Reines Dateilesen hängt außerdem von den übergeordneten Verzeichnissen ab.

### Schritt 3: Private Rechte auf eigene Daten anwenden

```bash
chmod -R --preserve-root u+rwX,go-rwx "Material"
```

Der eigene Testbaum wird verändert. Die nicht ausführbare Notiz erhält durch `X` nicht pauschal ein Ausführbit. Für einen bereits ausführbaren Eintrag kann die Wirkung anders sein.

### Schritt 4: Ergebnis erneut lesen

```bash
ls -ld "Material" "Material/Unterordner"
ls -l "Material/Unterordner/notiz.txt"
```

Bei den im praktischen Test ausdrücklich vorbereiteten Ausgangsmodi 755 für Ordner und 644 für die Notiz ergaben sich 700 beziehungsweise 600. Für andere Anfangsrechte und Sonderbits gilt nicht automatisch derselbe Endmodus.

### Schritt 5: Rückweg nicht erfinden

Ein rekursiver Rechtewechsel protokolliert nicht automatisch alle früheren Einzelmodi. Für reale Bestände vorher einen passenden, vollständigen Rechte-/ACL-Rückweg sichern. Ein pauschales Gegenkommando stellt unterschiedliche Originalrechte nicht zuverlässig wieder her.

## 6. Typische Anwendungsfälle

**Eigene private Ablage einschränken:** Wenn andere Konten bewusst keine normalen Zugriffsrechte behalten sollen und keine gemeinsame Nutzung vorgesehen ist.

**Eigenen Testbaum vereinheitlichen:** Mit klar definiertem Anfangszustand und bekanntem gewünschten Rechtekonzept.

**Fehlersuche vorbereiten:** Erst Eigentum, übergeordnete Pfade und ACLs lesen. Nicht jedes Zugriffsproblem ist durch pauschale rekursive Änderung zu lösen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Falscher Startpfad und kein allgemeines Undo

Ein einzelner falscher Pfad kann viele Programme oder Benutzerbestände betreffen. `--preserve-root` verhindert lediglich einen besonders großen Fehlfall. `$HOME`, ein Systembaum oder ein gemeinsames Projekt kann trotzdem ein falsches Ziel sein.

### Dateien und Verzeichnisse unterscheiden

Pauschales `755` gewährt Leserechte und macht alle Dateien ausführbar. Pauschales `644` nimmt Verzeichnissen die Suchrechte. `X` hilft bei bestimmten Eigentümeranpassungen, ersetzt aber kein vollständiges Berechtigungskonzept.

### Links, Hardlinks und ACLs

Linkbehandlung hängt von Version und Art der Auswahl ab. Ein ausdrücklich genannter symbolischer Link kann sein Ziel betreffen; beim rekursiven Durchlauf gelten weitere Regeln. Hardlinks teilen dieselben Dateirechte auch unter anderen Namen. Bestehende ACLs können durch Modusänderungen beeinflusst werden.

### Gemeinsam genutzte Bestände

Das private Beispiel entzieht Gruppe und anderen normale Rechte. Dadurch können Dienste, Freigaben oder Teamzugriffe ausfallen. Es ist kein geeignetes Standardrezept für beliebige Projekte oder Webverzeichnisse.

**Root-Rechte sind für eigene Dateien nicht nötig.** Ein Eigentümerwechsel ist eine andere Operation; Zugriffsprobleme nicht durch blindes `sudo chmod -R` behandeln.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Operation nicht erlaubt | Nicht Eigentümer oder besondere Einschränkung. | Eigentum, Dateisystem und genaue Meldung prüfen. |
| Ordner nicht mehr zugänglich | Suchrecht fehlt. | Gezielten Pfad und Verzeichnisrechte prüfen. |
| Fremde Nutzer verlieren Zugriff | Gruppen-/Andere-Rechte entfernt. | Gewünschtes Nutzungsmodell und dokumentierten Rückweg prüfen. |
| Viele Dateien ausführbar | Kleines `x` oder pauschales 755 verwendet. | Nicht blind mit anderem Gesamtmodus gegensteuern. |
| Außerhalb des sichtbaren Namens Wirkung | Links oder gemeinsame Inodes. | Tatsächliche Objektzuordnung klären. |
| Teilweise geändert | Fehler während rekursiver Verarbeitung. | Einzelergebnisse lesen; kein automatisches Rollback voraussetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Eigentum und aktuelle Rechte zuerst lesen.
2. Nur einen eigenen kleinen Baum als Test verwenden.
3. Startpfad eindeutig und begrenzt wählen.
4. Ordner-Suchrechte und Datei-Ausführrechte unterscheiden.
5. ACLs, Links und gemeinsame Nutzung vor realer Rekursion klären.
6. Einen echten Rückweg vorbereiten, bevor viele unterschiedliche Rechte verändert werden.

**Prüfstand:** Mit GNU chmod 9.4 wurde ausschließlich ein eigener temporärer Baum bearbeitet. Aus vorbereiteten Ordnerrechten 755 und Dateirechten 644 wurden mit `u+rwX,go-rwx` 700 und 600; der Dateiinhalt blieb gleich. ACLs, Spezialbits, Links, fremdes Eigentum und reale Benutzerbestände wurden nicht praktisch verändert oder geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ls -l`, `stat` | Modus und Eigentum lesen. |
| `getfacl`, `setfacl` | Erweiterte Zugriffslisten gesondert behandeln. |
| `chown` | Eigentümer und Gruppe ändern. |
| `find` | Bestände bewusst auswählen; daraus folgt keine automatische Änderungsfreigabe. |

Ausgangseintrag: Datensatz 49 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
