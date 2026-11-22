---
id: "setenforce"
name: "setenforce"
command: "setenforce"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["setenforce", "firewall & sicherheit"]
status: "Upstream-Handbuch geprüft; keine Modusänderung durchgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 325
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# setenforce – den aktuellen SELinux-Durchsetzungsmodus ändern

## 1. Kurzbeschreibung

`setenforce` wechselt bei aktivem SELinux zwischen globalem Enforcing- und Permissive-Modus. Es ist ein verändernder Verwaltungsbefehl. **Dafür sind administrative Rechte und die entsprechende SELinux-Autorisierung erforderlich.**

Die Form mit `0` ist keine harmlose Abfrage. Sie schwächt die globale Durchsetzung der SELinux-Policy. Die Form mit `1` kann bisher erlaubte Abläufe wieder an Verweigerungen scheitern lassen.

## 2. Was macht der Befehl?

Die [Upstream-Manpage zu setenforce](https://man7.org/linux/man-pages/man8/setenforce.8.html) ordnet die Werte eindeutig zu: `Enforcing` beziehungsweise `1` und `Permissive` beziehungsweise `0`. Das bereits gelesene [SELinux-Grundlagenhandbuch](https://man7.org/linux/man-pages/man8/selinux.8.html) erläutert den Zusammenhang mit Richtlinien.

Die Änderung betrifft den aktuellen Modus. Sie ist weder die komplette Einrichtung von SELinux noch ein Ersatz für eine bewusst geplante dauerhafte Konfiguration. Ein deaktiviertes SELinux wird dadurch nicht einfach vollständig aktiviert.

Für eine konkrete Anwendungsstörung ist der globale Wechsel ein sehr breiter Eingriff. Eine erfolgreiche Aktion im Permissive-Modus erklärt außerdem noch nicht, welche präzise Regel oder Dateizuordnung korrigiert werden müsste.

## 3. Syntax

```text
setenforce Enforcing
setenforce Permissive
setenforce 1
setenforce 0
```

Dies sind dokumentierte Syntaxformen, keine ausgeführte Anleitung für diesen Rechner. Es wurde keine davon gestartet. Der Katalogplatzhalter mit beliebigen Optionen wird durch diese begrenzten Argumentformen ersetzt.

## 4. Wichtige Optionen

Hier sind die Argumente wichtiger als eine Optionssammlung:

| Argument | Beabsichtigter Laufzeitmodus | Praktische Folge |
| --- | --- | --- |
| `Enforcing` oder `1` | Policy durchsetzen. | Nicht erlaubte Zugriffe können scheitern. |
| `Permissive` oder `0` | Entsprechende Policyverweigerungen nicht durchsetzen. | Globale Schutzwirkung wird verändert. |

`0` bedeutet nicht denselben Zustand wie vollständig deaktiviertes SELinux. Ebenso ist ein Moduswechsel keine Neukompilierung einer Policy und kein Relabeln sämtlicher Dateien.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Störung beschreiben

Angenommen, eine Anwendung kann auf eine benötigte Datei nicht zugreifen. Zuerst den genauen Fehler und die betroffene Funktion festhalten. Das Beispiel bezieht sich auf keine tatsächlich untersuchte Anwendung dieses Rechners.

### Schritt 2: Lesende Beobachtung vor Änderung stellen

`getenforce` und `sestatus` wären mögliche Statusquellen. Sie ändern den Modus nicht. Im vorliegenden Dokument wurden auch diese Systemabfragen nicht neu ausgeführt; die Werkzeuge sind lokal nicht vorhanden.

### Schritt 3: Die breite Wirkung eines Wechsels verstehen

Ein globaler Wechsel beträfe nicht nur die eine Datei. Deshalb bleibt er außerhalb einer unbedachten Einsteigerdiagnose. Für einen ausdrücklich geplanten Test wären erwartete Wirkung, Dauer, betroffene Dienste und Rückweg vorher zu klären.

### Schritt 4: Den eigentlichen Fehler getrennt lösen

Ein falsches Label oder eine unpassende Dienstkonfiguration braucht eine gezielte Lösung. Eine dauerhaft abgeschwächte globale Durchsetzung beseitigt den Schutz, ohne diese Ursache automatisch zu korrigieren.

## 6. Typische Anwendungsfälle

- Ein ausdrücklich autorisierter und zeitlich begrenzter SELinux-Diagnoseschritt.
- Ein geplanter Übergang nach fachlich vorbereiteter Policyprüfung.
- Wiederherstellung eines festgelegten Laufzeitmodus unter bekanntem Ausgangszustand.

Diese Fälle sind keine pauschale Empfehlung. Insbesondere das Zurückschalten auf Enforcing kann reale Anwendungen beeinträchtigen, wenn deren Zugriff zuvor nur wegen Permissive funktionierte.

## 7. Risiken, Nebenwirkungen und Vorsicht

Permissive schwächt SELinux global. Andere Rechteprüfungen bleiben zwar bestehen, aber das ersetzt nicht die zuvor durchgesetzte Policy. Während eines solchen Zeitraums können Aktionen stattfinden, die sonst verhindert worden wären.

Enforcing kann Prozesse an bislang zugelassenen Operationen hindern. Bei entfernten Systemen können auch Verwaltungsabläufe betroffen sein. Änderungen deshalb nicht ohne bekannten Zustand und erreichbaren Rückweg vornehmen.

Ein nach dem Neustart anderer Modus kann auf die getrennte Startkonfiguration zurückgehen. Daraus nicht automatisch schließen, der vorherige Aufruf habe gar nicht gewirkt.

## 8. Häufige Fehler

- **`0` als bloßen Test lesen:** Es ist eine echte Modusänderung.
- **Permissive gleich Disabled:** Unterschiedliche Zustände.
- **Laufzeitänderung als dauerhaft ansehen:** Startkonfiguration ist getrennt.
- **Berechtigungsfehler durch größere Eingriffe umgehen:** Erst den konkreten Kontext klären.
- **Funktioniert nach Wechsel, also behoben:** Die zugrunde liegende Policyfrage bleibt offen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für reine Zustandsfragen die lesenden Werkzeuge verwenden. Fehlermeldungen und betroffene Objekte gezielt untersuchen, bevor die globale Durchsetzung verändert wird.

Keine Startskripte übernehmen, die bei jeder Störung automatisch `setenforce 0` ausführen. Damit würde eine unbekannte Ursache regelmäßig mit einer systemweiten Schutzänderung beantwortet.

## 10. Verwandte Befehle

- `getenforce`: Aktuellen Modus lesen.
- `sestatus`: Weitere Statusangaben zeigen.
- `semanage`: Gezielte Anpassungsbereiche verwalten.
- `restorecon`: Sollkontexte auf Dateien anwenden; ebenfalls verändernd.
- `ausearch`: Passende bereits erfasste Auditereignisse auswerten.

**Prüfstand:** Syntax und Wirkung anhand der Handbücher beschrieben. Kein SELinux-Modus, Startparameter, Dateilabel oder Profil verändert.

Ausgangsdatensatz 325 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
