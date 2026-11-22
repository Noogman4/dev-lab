---
id: "compgen"
name: "compgen"
command: "compgen"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["compgen", "grundlagen & hilfe"]
status: "Statische Wortliste als Beispiel; keine fremde Completion ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 350
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-5.2-Hilfe gelesen"
---

# compgen – mögliche Bash-Vervollständigungen erzeugen

## 1. Kurzbeschreibung

`compgen` erzeugt passende Vorschläge für Bash-Vervollständigungen. Es kann eine eigene Wortliste oder bestimmte Namensklassen filtern. **Root-Rechte sind nicht nötig.** Vorschläge sind Daten, keine automatisch auszuführenden Befehle.

## 2. Was macht der Befehl?

Grundlage ist die lokale Hilfe `help compgen`. Das Builtin gehört zur programmierbaren Vervollständigung. Eine kleine statische Auswahl ist deutlich einfacher als eine Completion, die Funktionen oder externe Programme aufruft.

Je nach gewählter Aktion kann die Ausgabe Dateinamen, Befehlsnamen oder andere Informationen der Umgebung enthalten. Sie ist deshalb nicht automatisch eine vollständige oder vertrauenswürdig geprüfte Softwareinventur.

## 3. Syntax

```bash
compgen -W 'start status stop' -- sta
```

Das Beispiel filtert die eigene Wortliste nach dem Präfix `sta`. Erwartet werden die Kandidaten `start` und `status`. Diese Erwartung ist keine gemessene lokale Laufzeitausgabe.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-W WORTLISTE` | Aus eigenen Wörtern auswählen. | Quoting und mögliche Expansionen beachten. |
| `-A AKTION` | Eine Namensklasse wählen. | Ausgabe hängt von Shell und Umgebung ab. |
| `-f` | Dateinamenskandidaten erzeugen. | Liest den betreffenden Verzeichniskontext. |
| `-d` | Verzeichniskandidaten erzeugen. | Keine Verzeichnisanlage. |
| `-c` | Befehlsnamenskandidaten erzeugen. | Kein Integritätsnachweis für diese Namen. |
| `-P`, `-S` | Präfix oder Suffix ergänzen. | Nur Darstellung der Kandidaten. |

Erweiterte Formen wie `-F` und `-C` können eigene Funktionen beziehungsweise Programme einbeziehen. Sie sind keine pauschal rein statische Suche.

## 5. Beispiel erklärt Schritt für Schritt

Erstens enthält die einfach quotierte Liste ausschließlich drei vorgegebene Wörter. Zweitens trennt `--` die Optionsangaben vom Suchpräfix. Drittens begrenzt `sta` die Auswahl.

Die Ausgabe würde lediglich die passenden Kandidaten nennen. Weder `start` noch `status` würde dadurch als Dienstaktion ausgeführt. Ein nachgeschaltetes `eval` wäre eine neue, riskantere Aktion und gehört nicht zum Beispiel.

Das Werkzeug wurde für diesen Eintrag nicht mit persönlichen Dateien oder fremden Completionfunktionen ausgeführt. Dokumentationsgrundlage ist die lokale Hilfe.

## 6. Typische Anwendungsfälle

- Eine eigene begrenzte Wortauswahl vervollständigen.
- Kandidaten für eine Shellfunktion erzeugen.
- Dateinamencompletion mit passendem Kontext planen.
- Namensklassen für eine Bedienhilfe sichtbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine unbekannte Completion kann mehr tun als Wörter auflisten, besonders wenn sie Code aufruft. Fremde Completiondateien nicht ungeprüft laden oder als harmlosen Text behandeln.

Dateinamen können Leerzeichen oder Zeilenumbrüche enthalten. Eine zeilenweise Kandidatenanzeige ist daher nicht automatisch eine sichere Dateiliste für spätere Änderungen.

## 8. Häufige Fehler

- **Vorschläge automatisch ausführen:** Daten und Code vermischen.
- **Unquotierte Wortliste:** Shell verändert Argumente vor dem Aufruf.
- **`-c` als vollständige Inventur:** Umgebung und Suchregeln begrenzen die Aussage.
- **Onlineoption lokal unbekannt:** Bash-Versionen können neue Funktionen ergänzen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer festen eigenen Wortliste anfangen. Keine dynamischen Programmaufrufe ergänzen, solange eine einfache Auswahl genügt.

Für eine konkrete Befehlsauflösung `type` oder `command -v` verwenden. Ein Vervollständigungskandidat ersetzt diese Prüfung nicht.

## 10. Verwandte Befehle

- `complete`: Vervollständigungsregeln registrieren.
- `compopt`: Eigenschaften einer Completion beeinflussen.
- `type`: Namensauflösung betrachten.
- `help`: Lokale Bash-Dokumentation.

**Prüfstand:** Lokale Builtin-Hilfe gelesen. Keine persönliche Completion registriert und kein fremder Completioncode ausgeführt.

Ausgangsdatensatz 350 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
