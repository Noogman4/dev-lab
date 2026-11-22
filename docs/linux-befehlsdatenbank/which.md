---
id: "which"
name: "which"
command: "which"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["which", "grundlagen & hilfe"]
status: "Keine Vertrauensprüfung aus bloßer PATH-Suche abgeleitet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 377
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Debian-Manpage gelesen"
---

# which – ausführbare Dateien im Suchpfad mit begrenzter Aussage suchen

## 1. Kurzbeschreibung

`which` sucht ausführbare Dateien im aktuellen `PATH`. **Root-Rechte sind nicht nötig.** Es ist kein allgemeiner Nachweis dafür, welche Alias- oder Funktionsdefinition eine persönliche Shell verwenden würde.

## 2. Was macht der Befehl?

Die lokale Debian-Manpage beschreibt die Suche nach ausführbaren passenden Namen. Die gefundenen Pfade werden nicht grundsätzlich kanonisiert. Ein Symlink kann deshalb als solcher Bestandteil des Resultats bleiben.

Ein Suchpfad wird von der Umgebung beeinflusst. Wer ein früheres Suchverzeichnis kontrolliert, kann den ersten Fund beeinflussen. Das Werkzeug bestätigt weder Eigentümer noch Integrität der Programmdatei.

## 3. Syntax

```bash
which ls
which -a ls
```

Die zweite Form sucht mehrere passende Pfade. Die dokumentierte konkrete Variante unterstützt nicht automatisch sämtliche GNU-Langoptionen anderer Werkzeuge.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `-a` | Alle passenden Fundpfade zeigen. | Nur im betrachteten Suchpfad. |
| `-s` | Ergebnis nur über Status melden. | Diese Form ist implementationsabhängig. |

Für die lokale dokumentierte Fassung bedeutet Status `0`, dass alle gesuchten Namen gefunden wurden; `1` mindestens einen fehlenden Namen und `2` eine ungültige Option. Das ist keine fachliche Funktionsprüfung der Programme.

## 5. Beispiel erklärt Schritt für Schritt

```bash
which -a ls
```

Der geplante Aufruf würde passende ausführbare Dateien entlang des Suchpfads nennen. Er startet `ls` nicht. Eine persönliche reale Pfadliste wurde hier nicht erhoben.

Wenn mehrere Funde erscheinen, deren Reihenfolge und Herkunft erklären. Danach mit `type -a ls` die Frage der Shellauflösung gesondert betrachten. Ein Alias kann den sichtbaren Arbeitsaufruf anders gestalten.

Keine Gleichsetzung vornehmen zwischen „gefunden“, „unterstützt benötigte Option“ und „vertrauenswürdig“. Das sind verschiedene Aussagen.

## 6. Typische Anwendungsfälle

- Eine erwartete externe Programmdatei im Suchpfad finden.
- Mehrere Installationspositionen erkennen.
- Ein PATH-Problem von einer fehlenden Installation unterscheiden.
- Grenzen externer Befehlsfinder erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Suche ist lesend, aber die Ausgabe kann persönliche Pfade offenlegen. Ein anschließender automatischer Aufruf des Fundes ist eine neue Aktion.

Bei privilegierten Abläufen dürfen sicherheitsrelevante Prüfungen und spätere Ausführung nicht ungeklärt unterschiedliche Programmidentitäten verwenden. Eine PATH-Abfrage allein löst dieses Problem nicht.

## 8. Häufige Fehler

- **Builtin fehlt, also Befehl fehlt:** Externe Dateisuche hat Grenzen.
- **Erster Fund sicher:** Kontrollierte Suchverzeichnisse bleiben möglich.
- **Pfad schon realpath:** Kanonisierung wird nicht garantiert.
- **Langoption überall unterstützt:** Lokale Variante beachten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für Shellskripte und Built-ins häufig `command -v` oder `type` bevorzugen. Auch diese Abfragen sind keine automatische Vertrauenskette.

Suchpfade nicht pauschal umbauen, bevor klar ist, welche Installation gewünscht ist. Eine Diagnose sollte die beobachtete Reihenfolge erklären, nicht unbesehen Dateien ersetzen.

## 10. Verwandte Befehle

- `type -a`: Bash-Auflösungen.
- `command -v`: Verfügbarkeit im Shellkontext.
- `whereis`: Programme und Dokumentationsorte.
- `readlink`, `realpath`: Verknüpfungen beziehungsweise Pfade auflösen.

**Prüfstand:** Lokale Manpage gelesen. Keine Programmdatei auf Basis des Fundes ausgeführt und keine Suchpfadänderung.

Ausgangsdatensatz 377 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
