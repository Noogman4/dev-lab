---
id: "apt_search"
name: "apt search"
command: "apt search"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "apt_search"]
status: "Ausgearbeitet; Quellen geprüft; konkrete Paketsuche nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 47
reviewed_at: "2026-11-13"
locally_checked_version: "APT 2.8.4; Hilfe und Version geprüft"
---

# apt search – Pakete anhand lokaler Listen finden

## 1. Kurzbeschreibung

`apt search` sucht in den APT bekannten Paketangaben. Es hilft, einen passenden Paketnamen zu finden, bevor Details gelesen oder eine Installation geplant wird.

**Für die normale Suche sind keine Root-Rechte nötig.** Sie installiert und aktualisiert keine Pakete. Ein anschließendes `apt update` wäre dagegen ein eigener Netzwerk- und Schreibvorgang und wird nicht automatisch ausgeführt.

## 2. Was macht der Befehl?

APT durchsucht seine lokal bekannten Paketlisten. Ein Treffer kann aus dem Namen oder der Beschreibung stammen. Die Listen bilden den zuletzt verfügbaren lokalen Stand ab; eine Suche ist keine Live-Abfrage jedes Projektwebservers.

Ein gelistetes Paket ist nicht automatisch installiert, mit dem aktuellen System konfliktfrei installierbar oder in seiner neuesten upstream-Version vorhanden. Paketversionen und Quellen gehören zur Distribution und deren Aktualisierungspolitik.

Grundlagen: [APT-Handbuch zu search](https://manpages.debian.org/trixie/apt/apt.8.en.html) und [APT-Cache-Referenz](https://manpages.debian.org/trixie/apt/apt-cache.8.en.html). Lokal wurden Hilfe und Version von APT 2.8.4 geprüft. Es wurde keine konkrete Bestands- oder Repositorysuche ausgeführt.

## 3. Syntax

```text
apt search SUCHMUSTER
```

```bash
apt search 'wireshark'
apt search '^htop$'
```

Suchmuster können reguläre Ausdrücke enthalten. Anführungszeichen schützen sie vor Shell-Erweiterung. `^` und `$` begrenzen in einem regulären Ausdruck Anfang und Ende; eine volle Textsuche ist trotzdem nicht generell dasselbe wie eine ausdrückliche reine Paketnamensuche.

## 4. Wichtige Optionen

| Aufruf oder Suchform | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `apt search 'BEGRIFF'` | Bekannte Paketangaben durchsuchen. | Treffer können aus Beschreibungen stammen. |
| `apt search '^NAME$'` | Regulären Ausdruck begrenzen. | Musterinterpretation und Suchumfang beachten. |
| `apt show PAKET` | Details zum ausgewählten Paket lesen. | Ergänzt die erste Trefferübersicht. |
| `apt-cache search --names-only MUSTER` | Alternative Suche nur über Paket-/bereitgestellte Namen. | Hier ausdrücklich apt-cache-Syntax. |
| `apt-cache policy PAKET` | Kandidaten und Prioritäten ansehen. | Für Versions- und Herkunftseinordnung. |
| `apt --help` | Allgemeine APT-Hilfe. | Kein Installationsauftrag. |
| `apt --version` | Lokalen APT-Stand lesen. | Sagt nichts über Frische der Paketlisten. |

Die Tabelle enthält bewusst sowohl Suchformen als auch ergänzende Informationsaufrufe. Optionen eines anderen Unterprogramms nicht ohne Prüfung als identische `apt search`-Schalter voraussetzen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Zweck und lokalen Stand verstehen

```bash
apt --version
```

Die Suche verwendet vorhandene Paketinformationen. Ein fehlender Treffer kann an veralteten oder unvollständigen Listen liegen, beweist aber nicht sofort, dass das Programm generell nicht für Linux existiert.

### Schritt 2: Nach einer Funktion oder einem Namen suchen

```bash
apt search 'wireshark'
```

Dies ist ein Beispiel für die Suche nach einem bekannten Analysewerkzeug. Ähnlich benannte Zusatz-, Daten- oder Bibliothekspakete können ebenfalls erscheinen. Keinen Treffer allein wegen seiner Position ungeprüft installieren.

### Schritt 3: Namen gezielt eingrenzen

```bash
apt-cache search --names-only '^wireshark$'
```

Dieser alternative Aufruf beschränkt den Suchgegenstand ausdrücklich auf Namen. Ein virtueller beziehungsweise bereitgestellter Paketname kann trotzdem anders einzuordnen sein als ein direkt installierbares Paket.

### Schritt 4: Details und Versionsauswahl lesen

```bash
apt show wireshark
apt-cache policy wireshark
```

Beschreibung, Abhängigkeiten und die vorgesehene Version betrachten. Mehrere verfügbare Versionen können aus unterschiedlichen konfigurierten Quellen stammen.

### Schritt 5: Installation getrennt entscheiden

Die Suche selbst installiert nichts. Erst ein eigener `apt install`-Auftrag würde den Paketbestand verändern. Dessen Vorschau und privilegierte Bestätigung sind im getrennten Eintrag beschrieben.

## 6. Typische Anwendungsfälle

**Unbekannten Paketnamen finden:** Mit einem Funktionsbegriff beginnen und anschließend genaue Kandidaten prüfen.

**Zusatzpakete unterscheiden:** Programmpaket, Dokumentation, Bibliotheken und Entwicklungsdateien anhand ihrer Beschreibungen auseinanderhalten.

**Offline orientieren:** Bereits vorhandene lokale Listen können auch ohne aktive Verbindung Informationen liefern. Sie beweisen keine aktuelle Erreichbarkeit des Downloadservers.

**Installation vorbereiten:** Nach einer Suche erst Details und Herkunft lesen, bevor ein Änderungsauftrag erstellt wird.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Treffer sind keine Empfehlung

Ein ähnlicher Name oder eine passende Beschreibung beweist weder Vertrauenswürdigkeit noch Eignung für den konkreten Zweck. Die tatsächlich konfigurierten Quellen und Paketdetails prüfen.

### Suchmuster können überraschen

Sonderzeichen wie Punkt, Stern oder eckige Klammern können als regulärer Ausdruck wirken. Ein unzitiertes Muster kann außerdem schon von der Shell verändert werden. Für erste Versuche einen einfachen Begriff und anschließend ausdrückliche Namenssuche verwenden.

### Listen sind ein lokaler Kenntnisstand

Ein alter Index kann fehlende oder veraltete Informationen liefern. Eine Aktualisierung der Listen ist ein eigener Vorgang mit Netzwerkzugriff und Systemschreibwirkung. Sie nicht heimlich als Teil einer vermeintlich rein lesenden Suche einschieben.

### Ausgabe nicht als stabile Schnittstelle behandeln

`apt` ist vorrangig eine interaktive Oberfläche. Anzeigeformat, Übersetzung und Hinweise können sich ändern. Für Skripte geeignete spezialisierte Werkzeuge und bewusst geprüfte Ausgabeformate einsetzen, statt Spaltenpositionen blind zu übernehmen.

**Root-Rechte sind für Suche und passende Informationsabfragen nicht nötig.** Die Risikoeinstufung gibt keine Freigabe zur späteren Installation.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Treffer | Falscher Begriff, fehlende Quelle oder alter Index. | Namen und bekannten Listenstand prüfen. |
| Zu viele Treffer | Beschreibungssuche oder breiter Regex. | Namen gezielt eingrenzen. |
| Andere Version als Projektwebsite | Distribution liefert eigenen Paketstand. | Versionspolitik und Quellen prüfen. |
| Treffer nicht installierbar | Virtueller Name oder Abhängigkeitsproblem. | Details und Installationssimulation separat lesen. |
| Ausgabe verändert sich | APT-Version, Locale oder Listenstand anders. | Nicht als starres Skriptformat voraussetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Suche ohne sudo beginnen.
2. Muster zitieren und zunächst einfach halten.
3. Gefundenen Namen mit Beschreibung und Version abgleichen.
4. Namenssuche und Beschreibungssuche unterscheiden.
5. Paketlistenstand und echte aktuelle Verfügbarkeit nicht gleichsetzen.
6. Installation als separaten bewussten Auftrag behandeln.

**Prüfstand:** APT-Hilfe und Version 2.8.4 wurden lokal gelesen; offizielle Handbücher wurden geprüft. Die beispielhaften Paketabfragen wurden nicht ausgeführt. Es wurden weder Paketlisten geladen noch Pakete verändert. Konkrete Treffer, Verfügbarkeit und Quellenzuordnung bleiben vom jeweiligen lokalen Index abhängige Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt show` | Paketdetails lesen. |
| `apt-cache search`, `apt-cache policy` | Spezialisierte Suche und Versionsauswahl. |
| `apt-file` | Pakete anhand enthaltenen Dateipfads suchen; eigener Datenbestand. |
| `apt install` | Pakete systemweit installieren oder aktualisieren. |
| `dpkg-query` | Tatsächlich installierten Paketbestand abfragen. |

Ausgangseintrag: Datensatz 47 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
