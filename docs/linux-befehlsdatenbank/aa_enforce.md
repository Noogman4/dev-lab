---
id: "aa_enforce"
name: "aa-enforce"
command: "aa-enforce"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "caution"
tags: ["aa_enforce", "firewall & sicherheit"]
status: "Quellen und Struktur geprüft; Durchsetzungswechsel praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 304
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; AppArmor-Handbücher geprüft"
---

# aa-enforce – Ein AppArmor-Profil wieder durchsetzen

## 1. Kurzbeschreibung

`aa-enforce` setzt ausgewählte AppArmor-Profile in den Enforce-Modus. Zugriffe werden dann nach den Profilregeln tatsächlich beschränkt. **Für Änderungen an Systemprofilen sind administrative Rechte nötig.** Das Lesen der Dokumentation benötigt kein Root.

Der Befehl erzeugt kein automatisch passendes Sicherheitsprofil und repariert keine beliebige Anwendung. Ein vorhandenes unvollständiges Profil kann nach dem Umschalten benötigte Funktionen blockieren.

## 2. Was macht der Befehl?

Enforce bedeutet, dass die geladene Richtlinie durchgesetzt wird. Die [aa-enforce-Referenz](https://manpages.debian.org/trixie/apparmor-utils/aa-enforce.8.en.html) beschreibt den Wechsel aus anderen Zuständen. Welche Zugriffe erlaubt oder verweigert werden, hängt vom Profilinhalt und der tatsächlichen Zuordnung eines Prozesses ab.

Das [AppArmor-Grundlagenhandbuch](https://manpages.debian.org/trixie/apparmor/apparmor.7.en.html) unterscheidet gespeicherte Regeln, geladene Regeln und Prozessbindung. Ein schon unbeschränkt laufender Prozess wird nicht allein durch die Existenz einer neu geladenen Profilzuordnung rückwirkend passend eingeschränkt. Ein bereits unter einem ersetzten Profil laufender Prozess kann dagegen unmittelbar von dessen neuen Regeln betroffen sein. Start- und Betriebszustand gehören deshalb zur Planung.

## 3. Syntax

```text
aa-enforce AUSFUEHRBARE_DATEI [WEITERE_AUSFUEHRBARE_DATEIEN ...]
aa-enforce -d PROFILVERZEICHNIS --no-reload AUSFUEHRBARE_DATEI
```

Nur Syntaxmuster, hier nicht ausführen. Keine Wildcardliste über alle Systemprogramme als Lernbeispiel verwenden. Die zugehörige Programmauswahl muss zur vorhandenen Profildefinition passen.

## 4. Wichtige Optionen

| Element | Bedeutung | Grenze |
| --- | --- | --- |
| Programmoperand | Profil zum ausführbaren Ziel auswählen. | Geladene Prozesszuordnung gesondert prüfen. |
| Mehrere Operanden | Mehrere Profile umstellen. | Vergrößert mögliche Ausfälle. |
| `-d`, `--dir PFAD` | Anderes Profilverzeichnis verwenden. | Nicht automatisch eine isolierte Testumgebung. |
| `--no-reload` | Profil nach Änderung nicht automatisch neu laden. | Gespeicherte Änderung bleibt eine echte Änderung. |

Der Aufruf ohne Reload kann zu unterschiedlichen Zuständen auf dem Datenträger und im Kernel führen. Er ist kein allgemeiner Dry-Run und kein Nachweis, dass die neue Durchsetzung bereits aktiv wäre.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Handbuch und Ausgangsfrage klären

```bash
man 8 aa-enforce
```

Fehlt das Handbuch lokal, die oben verlinkte Referenz lesen. Das Werkzeug ist hier nicht installiert. Für diese Übung werden keine Profile angelegt oder geändert.

### Schritt 2: Einen fiktiven Rückkehrplan betrachten

Eine eigene Laboranwendung hätte zuvor ein kontrolliert entwickeltes Profil erhalten. Vor dem geplanten Umschalten wären folgende Punkte festzuhalten:

| Prüffrage | Erforderliche Information |
| --- | --- |
| Welches Ziel? | Eindeutig zugeordnete Laboranwendung und Profil. |
| Welcher bisheriger Zustand? | Gespeicherter Modus, geladener Modus und laufender Prozess. |
| Welche legitimen Aktionen? | Kleine bekannte Funktionsfälle. |
| Wie wird kontrolliert? | Modusprüfung und erwartete Funktion unter dem Profil. |
| Was bei Ausfall? | Vorbereiteter, gesondert freigegebener Wiederanlauf. |

Diese Tabelle ist ein Plan und kein gemessener Sicherheitsstatus.

### Schritt 3: Erfolg nicht nur am Modusnamen festmachen

Ein späterer echter Test müsste zeigen, dass der gewünschte Prozess im passenden Profil läuft, erwartete Funktionen weiter möglich sind und unerlaubte Zugriffe entsprechend behandelt werden. Eine bloße Anzahl geladener Enforce-Profile ersetzt diese Zuordnung nicht.

### Schritt 4: Änderungen sauber abschließen

Gespeicherten und wirksamen Zustand auseinanderhalten, besonders wenn ein Reload absichtlich ausblieb. Für laufende Anwendungen einen passenden geplanten Neustart beziehungsweise Wiederanlauf gesondert beurteilen. Hier wird kein Prozess gestartet oder beendet.

## 6. Typische Anwendungsfälle

### Nach kontrollierter Profilentwicklung

Ein geprüftes Laborprofil soll nicht dauerhaft im abgeschwächten Beobachtungsmodus bleiben. Der Rückwechsel verlangt trotzdem eine Prüfung der tatsächlich vorgesehenen Funktionen.

### Vorhandene Schutzkonfiguration wiederherstellen

Eine bekannte, zuvor dokumentierte Betriebsart wird auf ausdrücklichen Auftrag hergestellt. Unbekannte Ausgangszustände nicht als angeblich sicheren Standard überschreiben.

### Betrieb nachvollziehbar dokumentieren

Profilquelle, Version, geladener Zustand und betroffener Prozess werden zusammen festgehalten. Damit lässt sich später ein beobachtetes Problem genauer eingrenzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Neue Verweigerungen können Dateiablagen, Netzwerkzugriff oder andere benötigte Funktionen unterbrechen. Insbesondere produktive Dienste nicht ohne Vorbereitung umstellen. Fehlende Regeln sind nicht automatisch ein Anlass, das gesamte Profil wieder abzuschalten.

Enforce ist kein allgemeiner Vertrauensbeweis für den Profilinhalt. Zu weit gefasste erlaubende Regeln können weiter bestehen. Auch andere Sicherheitsmechanismen, klassische Dateirechte und Prozesskontexte bleiben relevant. Umgekehrt ist eine protokollierte Verweigerung zunächst ein Ereignis, keine vollständige Diagnose ihrer fachlichen Ursache.

## 8. Häufige Fehler

- **Profilmodus mit Prozessschutz gleichgesetzt:** Tatsächliche Bindung des Prozesses fehlt möglicherweise.
- **--no-reload als aktive Umstellung verstanden:** Kernelzustand kann noch der alte sein.
- **Unvollständiges Profil blockiert Arbeit:** Erwartete Zugriffe und genaue Regeln prüfen.
- **Alle Profile gleichzeitig umgestellt:** Umfang und Wiederanlauf wurden nicht begrenzt.
- **Erfolgscode als Sicherheitsabnahme verstanden:** Fachlicher Funktionstest und Regeln fehlen weiterhin.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Dokumentation und einer entbehrlichen Laboranwendung beginnen. Modusänderungen als echte Systemänderung behandeln. Regeln gezielt prüfen und nur ausdrücklich beauftragte Ziele umstellen.

**Prüfstand:** Verlinkte Werkzeug- und AppArmor-Grundlagenhandbücher gelesen; `aa-enforce` lokal nicht installiert. Keine Profiländerung, kein Reload, kein Dienstneustart und keine Modusprüfung am realen System ausgeführt. Praktische Durchsetzung und Anwendungseignung bleiben offen.

## 10. Verwandte Befehle

- `aa-complain`: bestimmte Verweigerungen durch Protokollierung ersetzen, Schutzänderung.
- `aa-status`, `apparmor_status`: geladene Zustände abfragen.
- `apparmor_parser`: Profilverarbeitung und gegebenenfalls Laden.
- `aa-logprof`: Regeln anhand von Meldungen bearbeiten, eigener Prüfbedarf.

Ausgangsdatensatz 304 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
