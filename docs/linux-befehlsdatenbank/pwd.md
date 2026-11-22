---
id: "pwd"
name: "pwd"
command: "pwd"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["pwd", "grundlagen & hilfe"]
status: "Kein persönlicher Pfad für das Beispiel erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 365
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# pwd – logischen oder physischen Arbeitsverzeichnispfad anzeigen

## 1. Kurzbeschreibung

`pwd` zeigt das aktuelle Arbeitsverzeichnis. Es kann eine logische Pfaddarstellung oder die physische Struktur ohne Symlinknamen verwenden. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Die lokale Hilfe `help pwd` beschreibt die Bash-Variante. Das Arbeitsverzeichnis ist der Bezugspunkt für relative Pfade. Eine angezeigte Zeichenfolge beschreibt diesen Ort zum Abfragezeitpunkt, keine dauerhafte Zugriffsberechtigung.

Beim Wechsel über Symlinks kann ein logischer Pfad anders aussehen als der physische. Beide können denselben aktuellen Ort bezeichnen. Unterschiedliche Zeichenfolgen sind daher nicht automatisch unterschiedliche Dateiinhalte.

## 3. Syntax

```bash
pwd
pwd -L
pwd -P
```

Die Bash-Standarddarstellung entspricht grundsätzlich der logischen Variante. Externe Varianten und andere Shells können eigene Details haben.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-L` | Passenden logischen `PWD`-Bezug nutzen. | Symlinkdarstellung kann erhalten bleiben. |
| `-P` | Physischen Pfad anzeigen. | Symlinkkomponenten werden nicht als solche beibehalten. |

`pwd` führt keinen Verzeichniswechsel aus. Für die eigene Builtinhilfe `help pwd` verwenden, statt eine universelle `--help`-Bedeutung vorauszusetzen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  uebung="$(mktemp -d -t netmon-pwd-XXXXXX)" || exit 1
  cd -- "$uebung" || exit 1
  pwd -P
)
```

Der neue Ordner ist nur für die Übung vorgesehen. Nach erfolgreichem `cd` würde `pwd -P` seinen physischen Pfad zeigen. Der Zufallsanteil des Namens ist bewusst nicht als festes Ergebnis angegeben.

Der Ablauf wurde für diesen Eintrag nicht gesondert ausgeführt. Die Subshell würde verhindern, dass die aufrufende Sitzung an einen anderen Ort wechselt.

## 6. Typische Anwendungsfälle

- Vor relativen Arbeitsaufrufen den Bezug prüfen.
- Einen Skriptfehler durch unerwartetes Arbeitsverzeichnis erklären.
- Symlinkdarstellung und tatsächliche Struktur unterscheiden.
- Einen eigenen Diagnoseausschnitt mit bewusst freigegebenem Pfad erstellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Ausgabe ist lesend, kann aber persönliche Namen und Projektpfade offenlegen. Nur weitergeben, wenn diese Angaben benötigt werden.

Ein vorher angezeigter Pfad verhindert keine späteren Änderungen durch andere Prozesse. Er ist insbesondere kein Ersatz für sichere Dateiöffnung bei empfindlichen Schreiboperationen.

## 8. Häufige Fehler

- **Anzeige mit Wechsel verwechseln:** `pwd` bewegt die Shell nicht.
- **Logisch und physisch immer gleich:** Symlinks können Unterschiede erzeugen.
- **Pfad als Rechtebeweis:** Berechtigungen bleiben eine eigene Frage.
- **Nach gescheitertem `cd` falschen Ort übersehen:** Wechselstatus prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nach einem beabsichtigten Wechsel bei Unsicherheit `pwd -P` lesen. In Skripten Fehler des `cd` behandeln, statt nur später eine Ausgabe zu betrachten.

Nicht das gesamte Heimatverzeichnis ausgeben oder durchsuchen, wenn nur der aktuelle Bezug gefragt ist. Der einfache Aufruf genügt.

## 10. Verwandte Befehle

- `cd`: Arbeitsverzeichnis ändern.
- `realpath`: Einen ausdrücklich genannten Pfad auflösen.
- `readlink`: Verknüpfungsinformationen betrachten.
- `type pwd`: Builtin oder externe Variante erkennen.

**Prüfstand:** Lokale Builtinhilfe gelesen. Keine persönliche Pfadangabe veröffentlicht und kein Sitzungswechsel ausgeführt.

Ausgangsdatensatz 365 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
