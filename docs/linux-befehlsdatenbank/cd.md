---
id: "cd"
name: "cd"
command: "cd"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cd", "grundlagen & hilfe"]
status: "Syntax und Fehlerbehandlung anhand der Builtin-Hilfe beschrieben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 347
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe geprüft"
---

# cd – das Arbeitsverzeichnis der Shell wechseln

## 1. Kurzbeschreibung

`cd` wechselt das Arbeitsverzeichnis der aktuellen Shell. Folgende relative Pfade werden von diesem neuen Ort aus aufgelöst. **Root-Rechte sind nicht nötig; die benötigten Verzeichnisrechte müssen vorliegen.**

## 2. Was macht der Befehl?

Grundlage ist die lokale Bash-Hilfe `help cd`. Ein Verzeichniswechsel kopiert oder verschiebt keine Dateien. Er verändert aber den Bezug späterer Befehle, was bei Lösch- und Schreibaktionen wichtig ist.

Weil die Änderung die aktuelle Shell betrifft, ist `cd` ein Builtin. Ein separat gestarteter Unterprozess kann das Arbeitsverzeichnis seines Elternprozesses nicht auf diese Weise dauerhaft umstellen.

## 3. Syntax

```bash
cd -- '/pfad/mit leerzeichen'
cd ..
cd -
```

Ohne Ziel nutzt Bash das Heimatverzeichnis. `..` ist die übergeordnete Ebene. `cd -` wechselt zum vorherigen über `OLDPWD` bekannten Ort und kann diesen anzeigen.

## 4. Wichtige Optionen

| Form | Wirkung | Bedeutung |
| --- | --- | --- |
| `-L` | Logische Pfadbehandlung. | Symlinkdarstellung beeinflusst `..`. |
| `-P` | Physische Verzeichnisstruktur. | Symlinks werden vor entsprechender Auflösung berücksichtigt. |
| `--` | Ende der Optionen. | Hilft bei Namen mit führendem Bindestrich. |
| `CDPATH` | Zusätzliche Suchorte. | Kann relative Zielsuche beeinflussen. |

Nicht jede Shell bietet jede Bash-Erweiterung. Für Skripte Interpreter und gewollte Pfadsemantik festlegen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  uebung="$(mktemp -d -t netmon-cd-XXXXXX)" || exit 1
  mkdir "$uebung/unterordner" || exit 1
  cd -- "$uebung/unterordner" || exit 1
  pwd -P
)
```

Der neue eigene Ordner begrenzt die Übung. Die Subshell verhindert, dass der Wechsel das Arbeitsverzeichnis der aufrufenden Sitzung verändert. Anführungszeichen halten den Pfad als ein Argument zusammen.

`|| exit 1` beendet den Übungsblock, wenn der Wechsel scheitert. Ohne Kontrolle könnten spätere relative Operationen am alten falschen Ort stattfinden. Das Beispiel ist aus der lokalen Hilfe abgeleitet; ein tatsächlicher Übungslauf wird hier nicht behauptet.

## 6. Typische Anwendungsfälle

- Im Terminal bewusst in ein Projekt wechseln.
- Relative Pfade für einen begrenzten Skriptabschnitt festlegen.
- Logische und physische Symlinkpfade unterscheiden.
- Einen Arbeitsblock in einer Subshell ausführen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein fehlgeschlagenes `cd` lässt den bisherigen Ort bestehen. Das ist besonders vor Schreib- oder Löschbefehlen gefährlich. Den Status deshalb prüfen.

Ein bereits erfolgreich aufgelöster Pfad ist außerdem keine dauerhafte Sicherheitsgarantie gegen spätere Änderungen durch andere Prozesse. Für empfindliche Dateizugriffe braucht es mehr als einen vorherigen Verzeichniswechsel.

## 8. Häufige Fehler

- **Pfad mit Leerzeichen unquotiert:** Mehrere Argumente entstehen.
- **Im Skript gewechselt, Terminal unverändert:** Unterprozess und Elternshell unterscheiden.
- **Nach Fehler weiterarbeiten:** Relativer Bezug ist falsch.
- **Symlink und `..` überraschend:** `-L` und `-P` klären.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nach einem Wechsel bei Bedarf mit `pwd` kontrollieren. Für Skriptblöcke einen bekannten absoluten Ausgangspfad und eine klare Fehlerbehandlung verwenden.

Zum bloßen Anzeigen des aktuellen Orts `pwd` nutzen. Keine Root-Shell öffnen, nur weil ein Verzeichniswechsel wegen fehlender Rechte scheitert.

## 10. Verwandte Befehle

- `pwd`: Arbeitsverzeichnis anzeigen.
- `pushd`, `popd`: Bash-Verzeichnisstapel verwenden.
- `ls`: Verzeichnisinhalt anzeigen.
- `help cd`: Lokale Regeln nachlesen.

**Prüfstand:** Lokale Bash-Hilfe gelesen; keine persönliche Sitzung oder dauerhafte Konfiguration geändert.

Ausgangsdatensatz 347 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
