---
id: "chown_r"
name: "chown -R"
command: "chown -R"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: true
risk_level: "danger"
tags: ["aufgabenorientierte hilfe", "chown_r"]
status: "Ausgearbeitet; Quellen geprüft; Eigentümerwechsel nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 50
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils chown 9.4; Hilfe und Version geprüft"
---

# chown -R – Eigentum rekursiv ändern und den Zielumfang begrenzen

## 1. Kurzbeschreibung

`chown -R` ändert Eigentümer und gegebenenfalls Gruppe rekursiv in einem Verzeichnisbaum. Es ist eine Optionenkombination des Programms `chown`, kein eigenes Programm.

**Ein wirklicher Wechsel auf einen anderen Eigentümer benötigt normalerweise Root-Rechte beziehungsweise entsprechende Privilegien.** Bestimmte Gruppenwechsel eigener Dateien sind für berechtigte Gruppenmitglieder ohne Root möglich. Der rekursive Administrationsfall ist ausdrücklich keine nur lesende Aktion.

## 2. Was macht der Befehl?

Linux ordnet Dateien einer numerischen Benutzer-ID und Gruppen-ID zu. Angezeigte Namen werden über die Kontenauflösung diesen IDs zugeordnet. Eine Namensgleichheit auf einem anderen Rechner garantiert deshalb keine identische Zuordnung.

Ein Eigentümerwechsel ist nicht dasselbe wie ein Moduswechsel mit `chmod`. Trotzdem kann er Auswirkungen auf Zugriff, Spezialbits und die Arbeit von Diensten haben. Ein falsch gewählter Startpfad kann sehr viele Dateien und gemeinsam genutzte Bestände betreffen.

Grundlagen: [Distributions-Manpage zu chown](https://manpages.debian.org/trixie/coreutils/chown.1.en.html) und lokale Hilfe von GNU coreutils 9.4. Es wurden keine echten Eigentumszuordnungen verändert.

## 3. Syntax

```text
chown -R [OPTIONEN] EIGENTÜMER[:GRUPPE] PFAD
chown -R [OPTIONEN] :GRUPPE PFAD
```

Die Schreibweisen unterscheiden sich:

| Operand | Wirkung |
| --- | --- |
| `BENUTZER` | Eigentümer ändern, Gruppe grundsätzlich beibehalten. |
| `BENUTZER:GRUPPE` | Eigentümer und Gruppe ausdrücklich setzen. |
| `BENUTZER:` | Eigentümer und dessen Login-Gruppe wählen. |
| `:GRUPPE` | Nur Gruppe ändern. |

Die Platzhalter müssen durch tatsächlich geprüfte Konten und einen begrenzten Pfad ersetzt werden. `$USER:$USER` ist kein allgemeingültiger Ersatz: Die passende Gruppe muss nicht wie das Benutzerkonto heißen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-R`, `--recursive` | Baum rekursiv bearbeiten. | Vorher Umfang und Mount-/Linkstruktur prüfen. |
| `--preserve-root` | Rekursive Operation auf `/` ablehnen. | Kein Schutz vor jedem falschen anderen Startpfad. |
| `--from=ALTUSER:ALTGRUPPE` | Nur aktuell passende Eigentumszuordnungen ändern. | Zusätzliche Auswahlbedingung, kein vollständiger Transaktionsschutz. |
| `-h`, `--no-dereference` | Linkobjekt statt referenzierter Datei behandeln. | Linkunterstützung und Traversierung getrennt verstehen. |
| `-P` | Keine symbolischen Verzeichnislinks traversieren. | Im GNU-Handbuch Standard für rekursiven Durchlauf. |
| `-H` | Als Startargument gewähltem Verzeichnislink folgen. | Kann Umfang außerhalb des erwarteten sichtbaren Baums erweitern. |
| `-L` | Verzeichnislinks beim Durchlauf folgen. | Für erste Administrationsaufträge vermeiden. |
| `--reference=DATEI` | Eigentümer und Gruppe von Referenz übernehmen. | Referenz wird dereferenziert; genau prüfen. |
| `-c` | Tatsächliche Änderungen melden. | Kein automatisches vollständiges Rückrollprotokoll. |
| `-v` | Alle bearbeiteten Einträge melden. | Bei großen Bäumen sehr umfangreich. |
| `-f` | Fehlermeldungen unterdrücken. | Bei Diagnose und erstem Auftrag vermeiden. |
| `--` | Ende der Optionen. | Für ungewöhnliche Startnamen hilfreich. |

Traversierung und Behandlung des einzelnen Links sind verschiedene Fragen. Ein pauschales „Links sind immer sicher“ wäre falsch.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug und gewünschte Identität prüfen

```bash
chown --version
chown --help
```

Diese Hilfeschritte wurden lokal ausgeführt. Einen späteren echten Auftrag erst nach klarer Entscheidung über neuen Eigentümer und Gruppe planen.

### Schritt 2: Zielbaum ausschließlich lesen

```bash
ls -ld "/PFAD/ZUM/BEGRENZTEN/PROJEKT"
```

Der Pfad ist ein ausdrücklich zu ersetzender Platzhalter. Vorher prüfen, ob es sich wirklich um den gewünschten Bestand handelt, welche Links oder eingebundenen Dateisysteme enthalten sind und ob unterschiedliche legitime Eigentümer vorkommen.

### Schritt 3: Rückweg vorbereiten

Für reale Daten bisherige Eigentümer, Gruppen, ACLs und besondere Eigenschaften passend sichern. Eine spätere pauschale Zuweisung an den alten Startordnereigentümer stellt unterschiedliche vorherige Einträge nicht zuverlässig wieder her.

### Schritt 4: Begrenzten Änderungsauftrag formulieren

```text
sudo chown -R -h -P --preserve-root --from=ALTUSER:ALTGRUPPE NEUUSER:NEUGRUPPE /PFAD/ZUM/BEGRENZTEN/PROJEKT
```

Dies ist ein Schema und kein hier ausführbarer fertiger Befehl. Alle Konten, Bedingungen und der Pfad müssen geprüft und ersetzt werden. `--from` begrenzt die Auswahl; `-P` und `-h` benennen die beabsichtigte Linkbehandlung. Die Operation würde echte Dateieigentümer verändern.

### Schritt 5: Ergebnis gezielt kontrollieren

Nach einem separat freigegebenen realen Auftrag die erwarteten Zuordnungen und Funktion betroffener Dienste prüfen. Ein teilweise fehlgeschlagener Lauf kann bereits einige Dateien verändert haben. Kein automatisches vollständiges Rollback voraussetzen.

## 6. Typische Anwendungsfälle

**Einen eigenen bewusst ausgewählten Projektbestand übertragen:** Etwa bei einer kontrollierten Kontenmigration mit dokumentierten alten und neuen IDs.

**Falsch zugeordnete Dateien gezielt korrigieren:** Ursache zunächst klären und nur tatsächlich betroffene Einträge auswählen. Nicht die ganze Benutzerablage als allgemeine Reparatur nehmen.

**Gruppenzuordnung vereinheitlichen:** Nur wenn das Nutzungsmodell klar ist; eine Gruppe, ACLs und Modusrechte müssen zusammenpassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Zugriff und Dienstfunktion

Ein falscher Eigentümer kann Anwendungen, Webdienste, Schlüsseldateien oder Sicherungen unbrauchbar machen. Erhöhte Rechte vergrößern den möglichen Schadensumfang. Systempfade nicht als Übungsdaten verwenden.

### Links, gemeinsame Inodes und Dateisystemgrenzen

Hardlinks besitzen dieselbe Eigentumszuordnung unter mehreren Namen. Symbolische Links und Referenzdateien können weitere Ziele betreffen. Ein rekursiver Baum kann eingebundene Dateisysteme enthalten; `-P` ist keine allgemeine Grenze gegen Mounts.

### Spezialbits und weitere Eigenschaften

Ein Eigentümerwechsel kann besondere Berechtigungseigenschaften beeinflussen. Besitz, Modus, ACLs und anwendungsbezogene Erwartungen getrennt prüfen. Ein wieder richtig angezeigter Name allein beweist keinen vollständig wiederhergestellten Sicherheitszustand.

### Auswahlbedingung ist keine abgeschlossene Transaktion

`--from` reduziert den Änderungsumfang, macht einen dynamischen gemeinsam schreibbaren Baum aber nicht automatisch unveränderlich. Parallel veränderte Bestände benötigen eine passende administrativ kontrollierte Vorgehensweise.

### Kein allgemeines Undo

Verschiedene alte Eigentümer lassen sich nicht aus einem einzigen neuen Eigentümer rekonstruieren. Eine Liste nach dem Eingriff ersetzt keinen vorher gesicherten Zustand. Teilweise Fehler ausdrücklich aufarbeiten.

**Für den normalen administrativen Eigentümerwechsel sind Root-Rechte nötig.** Reine Leseprüfung benötigt sie nicht; dieser Dokumentationsauftrag erteilt keine Freigabe für reale Zuordnungsänderungen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Benutzer oder Gruppe unbekannt | Falscher Name beziehungsweise Kontenauflösung. | Tatsächliche Identität und IDs prüfen. |
| Operation nicht erlaubt | Fehlende Privilegien oder Dateisystemgrenze. | Genaue Meldung und legitimen Zweck klären. |
| Dateien bleiben unverändert | `--from` passt nicht oder Eintrag wurde ausgelassen. | Aktuelle Zuordnung und Auswahl lesen. |
| Dienst funktioniert nicht mehr | Erwartetes Eigentum verändert. | Gesicherten Zustand und Dienstanforderungen prüfen. |
| Außerhalb des sichtbaren Pfads Wirkung | Link-/Mount-/Hardlinkstruktur. | Tatsächlich betroffene Objekte klären. |
| Nur Teil geändert | Lauf teilweise gescheitert. | Bestand einzeln prüfen; keine Atomarität annehmen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erst klären, ob Eigentum überhaupt die Ursache ist.
2. Namen, IDs und passende Gruppe ausdrücklich prüfen.
3. Startpfad begrenzen und Link-/Mountstruktur lesen.
4. Unterschiedliche alte Zuordnungen vorher sichern.
5. Keine pauschalen `$USER:$USER`-Rezepte übernehmen.
6. Nach dem Eingriff Zuordnung und betroffene Funktion getrennt prüfen.

**Prüfstand:** GNU-chown-Version 9.4 und lokale Hilfe wurden gelesen; das Distributionshandbuch wurde geprüft. Es wurde kein Eigentümer- oder Gruppenwechsel ausgeführt. Privilegierte Wirkung, Linkbehandlung, ACL-/Spezialbitfolgen und reale Dienstverträglichkeit bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chgrp` | Nur Gruppenbesitz ändern. |
| `chmod` | Modusrechte statt Eigentümer ändern. |
| `ls -l`, `stat` | Zuordnungen und Eigenschaften lesen. |
| `id`, `getent` | Benutzer- und Gruppenauflösung prüfen. |
| `getfacl` | ACLs unabhängig von einfacher Modusanzeige lesen. |

Ausgangseintrag: Datensatz 50 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
