---
id: "aa_complain"
name: "aa-complain"
command: "aa-complain"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "danger"
tags: ["aa_complain", "firewall & sicherheit"]
status: "Quellen und Struktur geprüft; keine Profiländerung ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 303
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; AppArmor-Handbücher geprüft"
---

# aa-complain – AppArmor-Verstöße protokollieren statt normal durchsetzen

## 1. Kurzbeschreibung

`aa-complain` schaltet ausgewählte AppArmor-Profile in den Complain-Modus. Dieser Modus ist für kontrollierte Profilentwicklung gedacht und schwächt die normale Durchsetzung. **Die Änderung von Systemprofilen benötigt administrative Rechte.** Handbuchlesen benötigt kein Root.

Das Werkzeug ist kein reiner Logbetrachter und keine allgemeine Reparatur für ein blockiertes Programm. Ein Aufruf kann gespeicherte Profilinformationen ändern und ein Neuladen auslösen.

## 2. Was macht der Befehl?

Im Complain-Modus werden bestimmte Zugriffe, die sonst wegen fehlender Erlaubnis verweigert würden, zugelassen und protokolliert. Das ist eine reale Änderung der Schutzwirkung. Ausdrückliche `deny`-Regeln bleiben nach der [aa-complain-Referenz](https://manpages.debian.org/trixie/apparmor-utils/aa-complain.8.en.html) trotzdem wirksam.

Das [AppArmor-Grundlagenhandbuch](https://manpages.debian.org/trixie/apparmor/apparmor.7.en.html) unterscheidet geladene Profile, Profilanwendung und Durchsetzungsmodi. Eine Datei auf dem Datenträger ist nicht automatisch der gerade wirksame Kernelzustand. Der Modus allein beweist außerdem nicht, dass ein bestimmter Prozess überhaupt dem gewünschten Profil unterliegt.

## 3. Syntax

```text
aa-complain AUSFUEHRBARE_DATEI [WEITERE_AUSFUEHRBARE_DATEIEN ...]
aa-complain -d PROFILVERZEICHNIS --no-reload AUSFUEHRBARE_DATEI
```

Das sind ausschließlich Syntaxmuster. Keine realen Programmpfade werden hier ausgewählt. Die Werkzeugfamilie erwartet die zu den Profilen gehörenden ausführbaren Ziele; nicht beliebige Profilnamen oder Zeichenketten aus einer Logmeldung blind übergeben.

## 4. Wichtige Optionen

| Element | Bedeutung | Grenze |
| --- | --- | --- |
| Programmoperand | Zugehöriges Profil auswählen. | Identität, Profilzuordnung und Mehrfachprofile vorher klären. |
| Mehrere Operanden | Mehrere Profile bearbeiten. | Vergrößert die Auswirkungen. |
| `-d`, `--dir PFAD` | Profilverzeichnis wählen. | Andere Quelle, kein automatisch sicherer Testmodus. |
| `--no-reload` | Nach Änderung nicht automatisch neu laden. | Die gespeicherte Änderung erfolgt trotzdem. |

Insbesondere `--no-reload` ist kein Dry-Run. Es kann den Zustand auf dem Datenträger vom wirksamen Zustand trennen. Weitere lokale Hilfeoptionen erst anhand der tatsächlich installierten Version voraussetzen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur die Dokumentation lesen

```bash
man 8 aa-complain
```

Falls die Manpage lokal fehlt, die oben verlinkte Distributionsreferenz verwenden. Das Werkzeug ist in dieser Arbeitsumgebung nicht installiert; ein echter Moduswechsel gehört nicht zur Übung.

### Schritt 2: Einen fiktiven Änderungsplan auseinandernehmen

Angenommen, eine ausschließlich zu diesem Zweck vorbereitete Laboranwendung scheitert an einem noch unvollständigen Profil. Der Plan müsste mindestens festhalten:

| Punkt | Fiktiver Prüfstand |
| --- | --- |
| Zielprogramm | Eigene entbehrliche Laboranwendung, noch nicht ausgewählt. |
| Aktueller geladener Modus | Vor jeder Änderung gesondert zu prüfen. |
| Zweck | Eine konkrete erwartete Zugriffsart verstehen. |
| Geplante Einschränkung | Nur das eindeutig zugeordnete Laborprofil. |
| Abschluss | Geprüftes Profil und bewusst wiederhergestellte Durchsetzung. |

Die Tabelle ist kein Systembefund und führt nichts aus. Ein produktiver Browser, Netzwerkdienst oder Sicherheitsprogramm wäre kein beiläufiges Übungsziel.

### Schritt 3: Aussage der möglichen Protokolle verstehen

Eine später beobachtete Meldung kann erklären, welche Aktion unter welchem Profil protokolliert wurde. Daraus folgt nicht automatisch, dass die Aktion fachlich erforderlich oder ungefährlich ist. Nicht jeden protokollierten Zugriff als neue Erlaubnis übernehmen.

### Schritt 4: Rückkehr gesondert planen

Das spätere `aa-enforce` wäre selbst wieder eine Änderung mit möglichen Funktionsfolgen. Keine automatische Umschaltfolge ausführen, deren Ausgangsprofil und vorheriger Zustand nicht bekannt sind. Hier wird weder ein Profil geladen noch ein Log gelesen.

## 6. Typische Anwendungsfälle

### Kontrollierte Profilentwicklung

In einer entbehrlichen Laborumgebung kann nachvollzogen werden, welche legitimen Zugriffe ein eigener Programmablauf benötigt. Dazu gehören bewusst gewählte Testfälle und spätere Prüfung der engen Regeln.

### Eine vermutete Blockade einordnen

Zunächst Profil, Anwendungsversion und konkrete Fehlermeldung verstehen. Ein unspezifisches „geht nicht“ rechtfertigt keine pauschale Schwächung aller Schutzprofile.

## 7. Risiken, Nebenwirkungen und Vorsicht

Complain kann Zugriffe erlauben, die vorher blockiert wurden. In einer feindlichen oder ungeklärten Umgebung kann die Beobachtung dadurch selbst neue Gefahren schaffen. Ausdrückliche Deny-Regeln bedeuten zugleich, dass die Anwendung trotz Complain weiter blockiert sein kann.

Eine nur gespeicherte Änderung kann bei einem späteren Neuladen wirksam werden. Profile, Includes und laufende Prozesse sind gemeinsam zu betrachten. Protokolle können private Pfade und Daten enthalten. Moduswechsel nicht als Nachweis behandeln, dass eine Anwendung sicher eingerichtet oder ein Finding behoben ist.

## 8. Häufige Fehler

- **Nur Loganzeige erwartet:** Der Aufruf ändert den Schutzmodus.
- **--no-reload als Simulation verstanden:** Änderungen auf dem Datenträger bleiben möglich.
- **Anwendung trotz Complain blockiert:** Ausdrückliche Deny-Regeln oder andere Kontrollen können weiter wirken.
- **Falsches Profil gewählt:** Ausführbares Ziel und geladene Zuordnung unterscheiden.
- **Jede Meldung erlaubt:** Ein protokollierter Zugriff ist noch keine fachliche Anforderung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Handbuch, Zielzuordnung und Ausgangszustand verstehen. Für einen echten Moduswechsel eine ausdrückliche getrennte Freigabe und einen nachvollziehbaren Rückkehrplan verwenden. Fremde Policy nicht aus einzelnen Logs automatisch erweitern.

**Prüfstand:** Beide verlinkten AppArmor-Handbücher gelesen; lokale Verfügbarkeit geprüft, `aa-complain` fehlt. Kein Programmoperand verwendet, keine Profildatei geändert, kein Profil neu geladen und kein Schutzmodus umgeschaltet. Praktische Modus- und Logprüfung vollständig offen.

## 10. Verwandte Befehle

- `aa-enforce`: normale Durchsetzung für ausgewählte Profile herstellen.
- `aa-status`, `apparmor_status`: Statusinformationen statt Modusänderung.
- `apparmor_parser`: Profile übersetzen und gegebenenfalls laden, eigener Änderungsumfang.
- `aa-logprof`: Profilbearbeitung anhand von Meldungen; keine automatische Freigabe unbekannter Zugriffe.

Ausgangsdatensatz 303 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
