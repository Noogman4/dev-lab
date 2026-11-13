---
id: "unzip"
name: "unzip"
command: "unzip"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive & kompression", "unzip"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 18
reviewed_at: "2026-11-13"
locally_checked_version: "Info-ZIP UnZip 6.00, Debian-Build"
---

# unzip – ZIP-Archive ansehen, testen und kontrolliert entpacken

## 1. Kurzbeschreibung

`unzip` liest ZIP-Archive, zeigt deren Einträge, testet komprimierte Inhalte und stellt Dateien wieder her. Diese Anleitung beschreibt Info-ZIP UnZip unter Linux. Andere Programme mit ähnlicher Oberfläche können abweichen.

**Für eigene Archive und einen eigenen Ausgabeordner sind keine Root-Rechte nötig.** Ohne reine Anzeige- oder Testoption entpackt das Programm und schreibt Dateien. Die pauschale Einordnung als nur lesender Befehl wäre falsch.

## 2. Was macht der Befehl?

ZIP bündelt Dateieinträge mit Namen, Daten und Metadaten. Einträge können unterschiedliche Kompressionsmethoden besitzen. Welche davon verarbeitet werden können, hängt vom installierten Build ab. Eine unterstützte ZIP-Dateiendung garantiert weder Unterstützung jeder Verschlüsselung noch jedes Kompressionsverfahrens.

Standardmäßig wird in das aktuelle Verzeichnis entpackt. Für eine übersichtliche Wiederherstellung deshalb einen ausdrücklichen Zielordner mit `-d` wählen. Im Unterschied zu vielen Einzeldatei-Kompressoren bleibt das ZIP-Archiv beim gewöhnlichen Entpacken erhalten.

Grundlage: [Distributions-Manpage für unzip](https://manpages.debian.org/trixie/unzip/unzip.1.en.html) und die lokal geprüfte Hilfe `unzip -hh`. Der lokale Versionsaufruf `unzip -v` zeigt außerdem kompilierte Funktionen und Umgebungsvorgaben.

## 3. Syntax

```text
unzip [OPTIONEN] ARCHIV.zip [MITGLIED ...] [-x MUSTER ...] [-d ZIELORDNER]
```

```bash
unzip -l "sammlung.zip"
unzip -t "sammlung.zip"
unzip -n "sammlung.zip" -d "Ausgabe"
```

Mitgliedsnamen bezeichnen Pfade innerhalb des Archivs. Suchmuster zitieren, damit die Shell sie nicht schon gegen Dateien im aktuellen Ordner auflöst. Bei einem Archivpfad mit führendem Bindestrich einen eindeutigen Pfad wie `./-sammlung.zip` verwenden.

## 4. Wichtige Optionen

| Option | Aufgabe | Konkreter Hinweis |
| --- | --- | --- |
| `-l` | Kurze Inhaltsliste. | Zeigt Namen und Größen, prüft nicht alle Nutzdaten. |
| `-t` | Komprimierte Daten prüfen. | Verarbeitet Inhalte und vergleicht die gespeicherten CRC-Werte. |
| `-d ORDNER` | Ausgabeordner wählen. | Schreibziel ausdrücklich festlegen. |
| `-n` | Existierende Dateien nie überschreiben. | Übersprungene Einträge sind keine neue Wiederherstellung. |
| `-o` | Ohne Nachfrage überschreiben. | Kann wichtige Zieldateien ersetzen. |
| `-p` | Nur Mitgliedsdaten auf stdout ausgeben. | Bei mehreren gewählten Mitgliedern können Inhalte direkt aufeinanderfolgen. |
| `-j` | Gespeicherte Unterverzeichnisse verwerfen. | Gleiche Basisnamen können kollidieren. |
| `-x MUSTER` | Mitglieder ausschließen. | Muster bezieht sich auf Archivpfade. |
| `-a` | Als Text erkannte Dateien konvertieren. | Kann Zeilenenden und damit Bytes verändern. |
| `-v` | Detaillierte Liste beziehungsweise ohne Archiv Versionsdaten. | Bedeutung hängt vom übrigen Aufruf ab. |
| `-Z` | In ZipInfo-Modus wechseln. | Muss zuerst stehen; danach gelten dessen Optionen. |
| `-hh` | Erweiterte Hilfe. | Geeignet zur lokalen Funktionsprüfung. |

Die lokale Hilfe führt zusätzlich `-O` und `-I` zur Zeichensatzwahl. Solche Distributions- oder Build-Erweiterungen nicht ohne Prüfung als überall verfügbare Optionen voraussetzen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsort wählen

```bash
unzip -v
uebung="$(mktemp -d -t netmon-unzip-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Eine Kopie eines eigenen kleinen ZIP-Archivs als `sammlung.zip` bereitstellen. Für einen vollständigen Erstellungsablauf siehe den getrennten Eintrag `zip`.

### Schritt 2: Namen prüfen

```bash
unzip -l "sammlung.zip"
```

Erwartete Einträge und entpackte Größen ansehen. Unerwartete Programme, Pfade oder Ausgabemengen zuerst klären.

### Schritt 3: Daten testen

```bash
unzip -t "sammlung.zip"
```

Fehler zu CRC, Verschlüsselung oder unbekannten Methoden nicht durch pauschales Erzwingen übergehen. Ein erfolgreicher Test prüft Archivkonsistenz, nicht die Harmlosigkeit der Dateien.

### Schritt 4: Frischen Zielordner verwenden

```bash
mkdir "Ausgabe"
unzip -n "sammlung.zip" -d "Ausgabe"
```

Unterpfade bleiben erhalten. `-n` verhindert einfaches Überschreiben bereits vorhandener Dateien. Danach Meldungen und tatsächlich entstandene Dateien prüfen.

### Schritt 5: Einzelnes bekanntes Textmitglied lesen

```bash
unzip -p "sammlung.zip" "unterordner/notiz.txt"
```

Dieser Mitgliedsname muss tatsächlich vorhanden sein. Für unbekannte Binärdaten keine direkte Terminalausgabe wählen. Eine bekannte Originaldatei kann anschließend mit der entpackten Datei über `cmp` verglichen werden.

## 6. Typische Anwendungsfälle

**Dateiaustausch:** Eine erhaltene ZIP-Sammlung in einen neuen eigenen Ordner entpacken und die Ergebnisse prüfen.

**Gezielte Wiederherstellung:** Nach der Liste einzelne Mitgliedspfade auswählen, statt den gesamten Inhalt in ein bestehendes Projekt zu schreiben.

**Fehlersuche:** Mit `-t` Datenfehler und mit `-v` verfügbare Methoden beziehungsweise Build-Eigenschaften untersuchen.

**Reine Weiterverarbeitung:** `-p` liefert Dateidaten ohne normale Statusausgabe auf stdout. Das Ergebnis muss ein passendes Folgewerkzeug erhalten; mehrere Mitglieder sind kein strukturiertes neues Archiv.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Zielkonflikte und Pfade

Entpacken kann Dateien und Verzeichnisse erzeugen sowie Metadaten wiederherstellen. Einen neuen Zielordner verwenden. `-n` ist keine Sandbox gegen jede Wirkung besonderer Archivpfade oder Verknüpfungen. Optionen wie `-:` zum Zulassen von Pfaden außerhalb des Entpackwurzelverzeichnisses vermeiden.

### Prüfsummen und Kennwörter

Ein gültiger CRC-Wert beweist keine vertrauenswürdige Herkunft. Verschlüsselte Archive können ein Passwort anfordern. Ein Passwort hinter `-P` kann in Prozessargumenten oder im Shell-Verlauf sichtbar werden; interaktive Abfrage bevorzugen. Nicht jede moderne ZIP-Verschlüsselung wird von jedem UnZip-Build unterstützt.

### Konvertierung und Ressourcen

`-a` kann Inhalte verändern. Für bytegenaue Wiederherstellung nicht unbedacht einsetzen. Komprimierte Daten können sehr große Ausgaben erzeugen; freier Plattenplatz und Laufzeit müssen passen. Die Größenliste ist keine durchgesetzte Ausgabequote.

### Umgebung und Metadaten

`UNZIP` und `UNZIPOPT` können Standardoptionen ergänzen. Bei überraschendem Verhalten die mit `unzip -v` angezeigten Vorgaben prüfen. ZIP ist nicht automatisch eine vollständige Sicherung aller Linux-ACLs, Eigentümer und erweiterten Attribute.

**Root-Rechte sind für die gezeigte eigene Übung nicht nötig.** Fremde Inhalte nicht als privilegierter Nutzer entpacken.

## 8. Häufige Fehler

| Meldung oder Verhalten | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Zentrales Verzeichnis fehlt | Beschädigte Datei, falsches Format oder unvollständiger Download. | Herkunft und Vollständigkeit prüfen. |
| Methode nicht unterstützt | Build unterstützt die verwendete Kompression nicht. | Kompressionsmethode und geeignete Implementierung ermitteln. |
| Mitglied nicht gefunden | Abweichender Pfad oder Groß-/Kleinschreibung. | Exakten Namen aus der Liste übernehmen. |
| Dateien übersprungen | `-n` schützt existierende Ziele. | Neuen Ausgabeordner wählen. |
| Umlaute falsch | Alte Zeichensatzangaben oder abweichender Erzeuger. | Lokale Zeichensatzoptionen gezielt prüfen. |
| Geteiltes ZIP scheitert | Split-Archive nicht direkt unterstützt. | Passenden dokumentierten Konvertierungsweg getrennt prüfen. |

Ein vorhandener Ausgabeordner allein beweist keinen vollständigen Erfolg. Abschlussstatus und Meldungen mitbeurteilen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erst auflisten und testen, danach entpacken.
2. Einen neuen eigenen Ordner und `-n` verwenden.
3. `-o`, Textkonvertierung und fremde Eigentümer nicht pauschal übernehmen.
4. Passwörter interaktiv eingeben.
5. Bekannte wiederhergestellte Inhalte vergleichen.
6. Entpackte Programme nicht allein wegen eines erfolgreichen Tests starten.

**Prüfstand:** Mit dem lokalen Info-ZIP UnZip 6.00 wurden Liste, Testmodus, Entpacken mit `-n` und stdout-Ausgabe an einem selbst erzeugten ZIP mit Deflate geprüft. Der Inhalt war bytegleich; eine geänderte eigene Zieldatei blieb bei erneutem Aufruf erhalten. Das Archiv blieb bestehen. Keine praktischen Tests mit Verschlüsselung, Split-Archiven, fremden Pfaden oder anderen Kompressionsmethoden.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `zip` | Erstellt oder verändert ZIP-Archive. |
| `zipinfo`, `unzip -Z` | Detaillierte Metadatenansicht. |
| `7z` | Anderes Mehrformatwerkzeug mit abweichender Syntax und Unterstützung. |
| `funzip` | Sonderfall zur Stream-Ausgabe des ersten Mitglieds; kein allgemeiner Ersatz. |
| `cmp` | Bytevergleich bekannter Dateien. |

Ausgangseintrag: Datensatz 18 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
