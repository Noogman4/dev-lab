---
id: "rename"
name: "rename"
command: "rename"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "rename"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 194
reviewed_at: "2026-11-13"
locally_checked_version: "rename nicht vorhanden; File::Rename-Dokumentation gelesen"
---

# rename – Den mehrdeutigen Rename-Namen vor Gebrauch klären

## 1. Kurzbeschreibung

rename bezeichnet auf Linux unterschiedliche Programme mit inkompatibler Syntax. Dieses Dokument erläutert die Perl-/File::Rename-Familie, die unter Debian als file-rename beziehungsweise rename verfügbar sein kann.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die Perl-Variante erhält einen Ausdruck, der den Dateinamensstring in $_ verändert. Die Util-linux-Variante erhält dagegen getrennte Teilstring- und Ersatzargumente und wird hier separat als rename.ul dokumentiert. Lokal fehlt ein Programm namens rename; aus dem vorhandenen rename.ul wird deshalb kein getesteter Perl-Aufruf abgeleitet. Ein Perl-Ausdruck ist ausführbarer Code. -n unterdrückt die Umbenennung, macht aber unbekannten Perl-Code nicht zu passiven Daten. Die betrachtete Variante arbeitet standardmäßig auf dem ganzen übergebenen Pfad; -d begrenzt die Namensänderung auf die letzte Komponente.

[Gelesene Primärquelle: File::Rename-Handbuch](https://manpages.debian.org/bookworm/rename/file-rename.1p.en.html). Die dort beschriebene Familie wird ausdrücklich von Util-linux getrennt.

## 3. Syntax

```text
rename [OPTIONEN] PERL_AUSDRUCK DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -n, --nono | Geplante Umbenennungen ohne Ausführung anzeigen |
| -v | Erfolgreiche Namensänderungen berichten |
| -d, --filename | Nur letzten Namensbestandteil verändern |
| -f | Vorhandene Ziele überschreiben lassen, riskant |
| -e AUSDRUCK | Ausdrücklich gewählten Perl-Ausdruck angeben |
| -0 | NUL-getrennte Namen von Standardeingabe lesen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Für eine spätere Übung wären zwei eigene neu angelegte Dateien ./eins.txt und ./zwei.txt sowie die verifizierte Perl-Implementierung erforderlich. Hier wurde weder dieses Programm installiert noch ein Ersatzprogramm als gleichwertig ausgegeben.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
rename -n -d 's/\.txt$/.md/' -- ./eins.txt ./zwei.txt
```

### Schritt 3: Wirkung und Grenze verstehen

Der selbst formulierte Ausdruck würde ein abschließendes .txt in .md umschreiben. -n zeigt nur die Planung; ein echter Lauf ohne -n wäre eine zusätzliche Aktion. Das Muster ist kein lokal bestätigtes Ergebnis. Der Punkt muss im Perl-Muster als literaler Punkt maskiert werden und $ begrenzt auf das Namensende. Die genaue Programmbindung ist vor jedem realen Einsatz zu klären.

## 6. Typische Anwendungsfälle

Eine kleine bekannte eigene Dateiserie nach einem bewusst formulierten Schema benennen. Bei wenigen Dateien ist mv mit einzelnen eindeutigen Namen oft leichter nachzuvollziehen als ein Ausdruck.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Perl-Ausdrücke können mehr als Dateinamen berechnen. Viele Namen können auf dasselbe neue Ziel abgebildet werden. Eine Vorschau verhindert weder einen späteren Zustandswechsel noch Fehler einer falschen Implementierung. -f kann vorhandene Daten verdrängen. Pfad- und Slashänderungen sind ohne passende Begrenzung auch Verzeichniswechsel.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Ausdruck wird als zwei Textargumente erwartet | Möglicherweise Util-linux statt Perl, Implementierung feststellen |
| Punkt passt auf beliebige Zeichen | Im Perl-Regulärausdruck den Punkt bei literaler Absicht maskieren |
| Unerwartet Pfadteile verändert | -d verwenden und konkrete Zielnamen vor jeder Aktion überprüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur selbst verstandenen Code verwenden und erst die Implementierung sowie die eigene eng begrenzte Dateiauswahl klären. Die Vorschau ist nur für genau den verstandenen Ausdruck sinnvoll und keine Sandbox. Keinen Befehl aus einer Anleitung blind auf die andere Rename-Familie übertragen.

**Prüfstand am 2026-11-13:** rename nicht vorhanden; File::Rename-Dokumentation gelesen. Nicht praktisch geprüft; praktische Prüfung offen. Keine Perl-Auswertung oder Umbenennung mit rename praktisch geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rename.ul | Util-linux mit Teilstring und Ersatz als getrennten Argumenten |
| mv | Einzelne Umbenennung |
| perl | Sprache des betrachteten Ausdrucks |

Herkunft: Originaldatensatz 194 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
