---
id: "sestatus"
name: "sestatus"
command: "sestatus"
category: "Firewall & Sicherheit"
language: "de"
root_required: false
risk_level: "safe"
tags: ["sestatus", "firewall & sicherheit"]
status: "Upstream-Manpage geprüft; keine echte Systemabfrage"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 324
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# sestatus – SELinux-Status und Konfigurationskontext lesen

## 1. Kurzbeschreibung

`sestatus` zeigt mehr SELinux-Kontext als die kurze Modusabfrage mit `getenforce`. Dazu können Aktivierung, Policy und der Unterschied zwischen aktuellem Modus und gespeicherter Vorgabe gehören. Es ändert diese Einstellungen nicht.

**Die übliche Statusansicht benötigt grundsätzlich keine Root-Rechte.** Für zusätzliche Angaben zu geschützten Dateien oder Prozessen kann der Zugriff eingeschränkt sein. Eine unvollständige Ansicht bleibt entsprechend zu kennzeichnen.

## 2. Was macht der Befehl?

Nach der [Upstream-Manpage zu sestatus](https://man7.org/linux/man-pages/man8/sestatus.8.html) lassen sich grundlegende Statusdaten sowie weitere Kontexte oder Booleans anzeigen. Welche zusätzlichen Objekte betrachtet werden, hängt bei der ausführlichen Kontextansicht auch von `sestatus.conf` ab.

Eine solche Abfrage ist eine Bestandsaufnahme. Sie prüft nicht jede Policyentscheidung und führt keinen umfassenden Sicherheitstest aus. Ein angezeigter Policyname ist eine Beschreibung der verwendeten Richtlinie, keine Bewertung ihrer Eignung.

Besonders hilfreich ist die Trennung zwischen Laufzeit und Konfiguration. Wenn diese Angaben voneinander abweichen, muss zunächst die Ursache der Abweichung verstanden werden. Ein automatisches Angleichen ist keine Funktion der Statusanzeige.

## 3. Syntax

```text
sestatus
sestatus -b
sestatus -v
```

Der Aufruf ohne Optionen fordert eine grundlegende Statusansicht an. `-b` wählt die Boolean-Anzeige, `-v` zusätzliche Kontextinformationen. Die Kürzel nicht ungeprüft von anderen Werkzeugen übertragen: `-v` ist hier kein vorausgesetzter Versionsschalter.

## 4. Wichtige Optionen

| Form | Inhalt | Aussagegrenze |
| --- | --- | --- |
| Ohne Option | Allgemeiner SELinux-Zustand. | Keine Prüfung aller Anwendungen. |
| `-b` | Aktuelle Boolean-Zustände. | Richtige fachliche Einstellung bleibt gesonderte Frage. |
| `-v` | Zusätzliche Datei- und Prozesskontexte. | Auswahl folgt unter anderem lokaler Konfiguration. |

Die Manpage dokumentiert diese Kernformen. Ein universelles `--help` oder weitere erfundene Schalter werden aus dem allgemeinen Datenbankplatzhalter nicht abgeleitet.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Bestandsfrage wählen

```bash
sestatus
```

Dieser Aufruf wurde hier nicht ausgeführt, weil das Programm lokal nicht installiert ist. Das Beispiel beschreibt die übliche Statusanfrage und enthält keine echten Systemdaten.

### Schritt 2: Ein fiktives Paar von Angaben lesen

Angenommen, der aktuelle Modus wäre `permissive`, die Konfigurationsvorgabe dagegen `enforcing`. Dann stimmen Laufzeit und gespeicherte Vorgabe nicht überein. Das ist die Beobachtung; eine Aussage über Ursache oder Absicht folgt daraus noch nicht.

### Schritt 3: Keine Konfigurationsänderung ableiten

Für eine autorisierte Diagnose wäre zu klären, welche Vorgabe beabsichtigt ist und weshalb der aktuelle Zustand davon abweicht. `sestatus` löst diese Frage nicht durch Umschalten. Eine Schutzänderung wäre ein eigener Verwaltungsauftrag.

### Schritt 4: Den Kontext der Ausgabe erhalten

Zeitpunkt und Umgebung mitnotieren. Ein ausgeschnittener Satz wie „enabled“ kann sonst den falschen Eindruck erwecken, die Richtlinie werde bereits in jedem relevanten Bereich durchgesetzt.

## 6. Typische Anwendungsfälle

- Laufzeitmodus und gespeicherte Vorgabe gegenüberstellen.
- Einen bekannten Policykontext für einen Fehlerbericht beschreiben.
- Boolean-Zustände vor einer geplanten Einzelprüfung betrachten.
- Zusätzliche Kontexte gezielt lesen, wenn die Grundansicht nicht genügt.

Für eine bestimmte Zugriffsverweigerung reichen globale Angaben häufig nicht aus. Betroffener Prozess, Objekt und genaue Policyentscheidung gehören dann zur weiteren Untersuchung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Statusaufruf verändert keine Policy. Seine Ausgabe kann aber Namen, Pfade und Sicherheitsstruktur offenlegen. Besonders ausführliche Berichte vor einer Weitergabe auf vertrauliche Angaben prüfen.

Eine konfigurierte Objektliste ist keine vollständige Inventur des Dateisystems. Fehlende Objekte in der Anzeige sind deshalb nicht automatisch ungeschützt oder verschwunden. Ebenso darf eine allgemeine Aktivierungsanzeige nicht als universeller Schutzbeweis verwendet werden.

## 8. Häufige Fehler

- **Enabled gleich Enforcing:** Aktivierung und Modus unterscheiden.
- **`-v` als Version lesen:** Hier werden zusätzliche Kontexte abgefragt.
- **Konfigurationsmodus gleich Laufzeit:** Beide Felder getrennt lesen.
- **Keine Ausgabe als deaktiviert werten:** Erst Ausführungsfehler und Verfügbarkeit prüfen.
- **Boolean sichtbar, also richtig:** Der passende Wert hängt von Aufgabe und Policy ab.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der Grundansicht beginnen und nur für eine konkrete Frage zusätzliche Daten anfordern. Meldungen zunächst sachlich wiedergeben, bevor Änderungen vorgeschlagen werden.

Fehlt das Werkzeug, Distribution und vorgesehenes Schutzkonzept klären. Nicht allein zur Erzeugung einer erwarteten Statuszeile ein neues Schutzsystem installieren oder bestehende Mechanismen umstellen.

## 10. Verwandte Befehle

- `getenforce`: Kurze Abfrage des globalen Modus.
- `setenforce`: Modusänderung, keine reine Diagnose.
- `getsebool`: Boolean-Zustände abfragen.
- `semanage`: Bestimmte Policyanpassungen verwalten.
- `aa-status`: Status von AppArmor, einem anderen Schutzsystem.

**Prüfstand:** Upstream-Handbuch gelesen. Keine reale Prozess-, Datei- oder Policyansicht erhoben und keine SELinux-Einstellung verändert.

Ausgangsdatensatz 324 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
