---
id: "unrar"
name: "unrar"
command: "unrar"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "rar", "entpacken"]
status: "Ausgearbeitet; Herstellerdokumentation geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 16
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; RAR-Handbuch 7.23 und UnRAR-Quelltexte 7.30 beta 2 gelesen"
---

# unrar – RAR-Archive auflisten, testen und gezielt entpacken

## 1. Kurzbeschreibung

`unrar` ist das Entpackwerkzeug für RAR-Archive. Die hier beschriebenen Aufrufe beziehen sich auf **RARLAB UnRAR**, nicht auf ein beliebiges anders implementiertes Werkzeug mit ähnlichem Namen. Es erstellt keine neuen RAR-Archive.

**Zum Lesen und Entpacken eigener Archive in einen eigenen Ordner sind keine Root-Rechte nötig.** Entpacken schreibt Dateien und kann vorhandene Daten betreffen. Die Auswahl des Zielordners und des Überschreibmodus ist deshalb wesentlich.

## 2. Was macht der Befehl?

Ein RAR-Archiv kann mehrere Dateien, Verzeichnisse, komprimierte Inhalte, Metadaten und verschlüsselte Daten enthalten. UnRAR verarbeitet die Entpackseite dieses Formats. Dafür gibt es getrennte Aufgaben: Einträge auflisten, komprimierte Inhalte testen und Dateien tatsächlich wiederherstellen.

Ein Testlauf entpackt intern zur Prüfung, ohne die normalen Ausgabedateien anzulegen. Er ist kein Virenscan und bestätigt keine vertrauenswürdige Herkunft. Eine Namensliste wiederum prüft nicht zwangsläufig jeden Dateiinhalt.

RARLAB beschreibt die Herkunft des Werkzeugs auf seiner [offiziellen Zusatzseite](https://www.rarlab.com/rar_add.htm). Als Detailgrundlage wurden das Text-Handbuch im [offiziellen Linux-Paket 7.23](https://www.rarlab.com/rar/rarlinux-x64-723.tar.gz) und ausgewählte Textdateien aus dem [offiziellen UnRAR-Quellarchiv](https://www.rarlab.com/rar/unrarsrc-7.3.2.tar.gz) gelesen. Letzteres kennzeichnet sich intern als 7.30 beta 2. Daraus wird keine Aussage über eine hier installierte Version oder praktische Ausführung abgeleitet.

## 3. Syntax

```text
unrar BEFEHL [SCHALTER ...] ARCHIV [DATEIAUSWAHL ...] [ZIELORDNER/]
```

```bash
unrar l -cfg- "sammlung.rar"
unrar t -cfg- "sammlung.rar"
unrar x -cfg- -o- "sammlung.rar" "Ausgabe/"
```

`l`, `t` und `x` sind Befehle ohne vorangestellten Bindestrich. Optionen wie `-cfg-` und `-o-` sind Schalter. Die beiden Endstriche gehören jeweils zur Schreibweise des Schalters und dürfen nicht weggelassen werden.

`Ausgabe/` ist der Zielpfad. Der abschließende Schrägstrich macht die Verzeichnisabsicht deutlich. Für Pfade mit Leerzeichen Anführungszeichen verwenden.

**Prüfpunkt:** Vor der Übernahme mit `unrar '-?'` die lokale Hilfe und deren Programmtitel prüfen. Das Fragezeichen wird zitiert, damit die Shell es nicht als Dateinamenmuster auswertet. `unrar-free` oder andere Varianten können sich unterscheiden.

## 4. Wichtige Optionen

| Befehl oder Schalter | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `l` | Archivinhalt auflisten. | Geeignet für eine erste Namensübersicht. |
| `lt` | Technische Eintragsangaben anzeigen. | Angaben hängen vom Archiv und der Version ab. |
| `t` | Archivdateien durch interne Verarbeitung testen. | Keine normale Wiederherstellung und kein Herkunftsnachweis. |
| `x` | Mit gespeicherter Pfadstruktur entpacken. | Frischen, eigenen Zielordner verwenden. |
| `e` | Ohne gespeicherte Verzeichnispfade entpacken. | Gleiche Dateinamen aus unterschiedlichen Ordnern können kollidieren. |
| `p` | Gewählte Datei auf stdout ausgeben. | Binäre Inhalte nicht unbedacht ins Terminal schreiben. |
| `-cfg-` | Konfiguration und entsprechende Umgebungsvorgaben ausschließen. | Macht die hier gezeigten Aufrufe nachvollziehbarer. |
| `-o-` | Bereits vorhandene Ausgabedateien überspringen. | Ein übersprungener Eintrag ist nicht neu wiederhergestellt. |
| `-o+` | Vorhandene Ausgabedateien überschreiben. | Für die erste Wiederherstellung vermeiden. |
| `-p` | Passwortverarbeitung wählen; ohne angehängtes Passwort Eingabe anfordern. | Passwort nicht als sichtbaren Kommandozeilenwert hinterlegen. |
| `-y` | Nachfragen automatisch bestätigen. | Kann eine wichtige Rückfrage beseitigen. |
| `-kb` | Beschädigte entpackte Dateien behalten. | Solche Dateien sind nicht automatisch brauchbare Ergebnisse. |

Die genaue Auswahl unterstützter Schalter ist implementations- und versionsabhängig. Funktionen des vollständigen `rar`-Packers dürfen nicht ungeprüft auf `unrar` übertragen werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug prüfen und eigenes Archiv auswählen

```bash
unrar '-?'
```

Für die weitere Übung ein eigenes, bereits vorhandenes RAR-Archiv verwenden. Das Werkzeug ist hier nicht installiert; die folgenden Schritte sind deshalb eine dokumentierte Anleitung und kein ausgeführter Testbericht. Es wird kein fremdes Testarchiv heruntergeladen.

### Schritt 2: Neuen Arbeitsordner vorbereiten

```bash
uebung="$(mktemp -d -t netmon-unrar-XXXXXX)"
cd "$uebung"
pwd
mkdir "Ausgabe"
```

Nur nach erfolgreichem Wechsel fortfahren. Eine Kopie des eigenen Archivs als `sammlung.rar` in diesem Arbeitsordner bereitstellen. Die Übung verändert damit nicht das einzige Original.

### Schritt 3: Namen und Struktur prüfen

```bash
unrar l -cfg- "sammlung.rar"
```

Prüfen, ob die erwarteten Einträge und eine plausible Verzeichnisstruktur enthalten sind. Viele unerwartete Dateien oder auffällige Namen sind ein Grund, den Ablauf zu unterbrechen und die Herkunft zu klären.

### Schritt 4: Inhalte testen

```bash
unrar t -cfg- "sammlung.rar"
```

Ein verschlüsseltes Archiv kann ein Passwort verlangen. Fehlermeldungen zu Daten, fehlenden Teilen oder falschem Passwort zuerst klären. Eine erfolgreiche Namensliste ersetzt diesen Schritt nicht.

### Schritt 5: In den frischen Ordner entpacken

```bash
unrar x -cfg- -o- "sammlung.rar" "Ausgabe/"
```

`x` erhält die gespeicherten Unterpfade. `-o-` vermeidet das Ersetzen bereits vorhandener Ausgabedateien. Danach die Meldungen und die tatsächlich entstandenen Dateien prüfen. Wiederholte Aufrufe können Einträge überspringen; daraus darf keine vollständige neue Wiederherstellung abgeleitet werden.

## 6. Typische Anwendungsfälle

**Ein erhaltenes RAR-Archiv öffnen:** Erst auflisten, dann testen und in einen eigenen neuen Ordner entpacken. Für ZIP-Dateien ein passendes ZIP-Werkzeug verwenden.

**Ältere eigene Sicherung wiederherstellen:** Nach dem Entpacken wichtige bekannte Inhalte vergleichen. Eine Dateiliste allein beweist nicht, dass die Sicherung vollständig und brauchbar war.

**Mehrteilige Archive verarbeiten:** Zusammengehörige Teile am selben Ort bereithalten und mit dem ersten Teil beginnen, beispielsweise `sammlung.part1.rar`. Eine abweichende Benennung kann einen anderen ersten Teil vorsehen. Fehlende Teile lassen sich nicht durch beliebiges Umbenennen ersetzen.

**Gezielt einen Eintrag ausgeben:** Bei einem bekannten Textmitglied kann `p` für weitere kontrollierte Verarbeitung geeignet sein. Mitgliedsname und gewünschte Ausgabe müssen vorher eindeutig feststehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Entpacken ist eine Schreiboperation

Ein bestehender Zielordner kann fremde oder wichtige Dateien enthalten. Deshalb einen neuen Ordner wählen und Überschreibregeln bewusst setzen. `-o-` schützt vor einfachem Ersetzen vorhandener Dateien, bildet aber keine vollständige Sicherheitsgrenze um ein unbekanntes Archiv.

### Fremde Inhalte bleiben fremde Inhalte

Ein Test erkennt bestimmte Archiv- und Prüfsummenfehler. Er beurteilt keine Makros, Skripte, Programme oder schädlichen Dokumentinhalte. Entpackte Programme nicht allein wegen eines erfolgreichen Tests starten. Zum Entpacken kein enthaltenes selbstextrahierendes Programm ausführen, wenn ein geeignetes Archivwerkzeug die Aufgabe übernehmen kann.

### Pfade, Links und Ressourcen beachten

Archive können Verknüpfungen und besondere Metadaten enthalten. Die tatsächlich installierte Version und deren Schutzverhalten sind maßgeblich. Auch ein frischer Zielordner begrenzt nicht automatisch RAM, Laufzeit oder Ausgabemenge. Unbekannte Archive nicht mit Root-Rechten entpacken.

### Passwörter nicht offen hinterlegen

Ein direkt angehängtes Passwort kann in Shell-Verlauf, Prozessargumenten oder Diagnoseausgaben sichtbar werden. Interaktive Eingabe bevorzugen und Kennwörter nicht in diese Dokumentation oder NetMon-Notizen kopieren. Verschlüsselung ist kein Nachweis für einen vertrauenswürdigen Absender.

### Beschädigte Ergebnisse und fehlende Teile

Mit `-kb` behaltene Dateien können unvollständig oder inhaltlich falsch sein. Sie nicht als erfolgreiche Wiederherstellung behandeln. Bei wichtigen Daten Originalteile erhalten und Fehlerursachen getrennt klären.

**Root-Rechte sind für die eigene Übung nicht erforderlich.** Sie beheben weder ein falsches Passwort noch fehlende Archivteile.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Befehl fehlt | Kein passendes UnRAR installiert. | Paketangebot und lokale Implementierung bewusst prüfen. |
| Unbekannte Option | Andere Variante oder anderer Versionsstand. | Zur konkreten lokalen Hilfe zurückkehren. |
| Prüfsummenfehler | Beschädigte Daten; bei verschlüsselten Daten auch Passwortproblem möglich. | Quelle, vollständige Teile und Passwort prüfen. |
| Nächster Teil wird verlangt | Mehrteilige Sammlung unvollständig oder falsch abgelegt. | Zusammengehörige Originalteile bereitstellen. |
| Dateien werden übersprungen | Ziel existiert und `-o-` ist aktiv. | Neues Ziel wählen statt blind zu überschreiben. |
| Ordnerstruktur fehlt | `e` statt `x` verwendet. | Für erhaltene Unterpfade `x` wählen. |

Ein Abschluss ohne Fehler ist anders zu bewerten als eine Warnung oder ein Abbruch. Die Herstellerreferenz nennt unter anderem `0` für Erfolg, `3` für einen Prüfsummenfehler und `11` für ein falsches Passwort. Die konkrete Meldung und den lokalen Versionsstand mitbeurteilen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. RARLAB UnRAR und ähnlich benannte Alternativen unterscheiden.
2. Eigenes Archiv kopieren und das Original erhalten.
3. Erst auflisten, dann testen, dann entpacken.
4. Einen neuen eigenen Zielordner und `-o-` verwenden.
5. Keine pauschale Bestätigung mit `-y` ergänzen.
6. Passwörter interaktiv eingeben.
7. Entpackte Inhalte und übersprungene Einträge ausdrücklich prüfen.
8. Für einen tatsächlichen Wiederherstellungsnachweis bekannte Inhalte vergleichen.

**Prüfstand:** Herstellerreferenz und ausgewählte Quelltexte wurden ausschließlich als Text gelesen. Das verwendete UnRAR-Quellarchiv ist als 7.30 beta 2 gekennzeichnet; diese Beta wurde weder gebaut noch ausgeführt. UnRAR ist hier nicht installiert. Auflisten, Testen, Entpacken, Passwortabfragen und mehrteilige Archive sind daher praktische Prüfpunkte und werden nicht als erfolgreich getestet ausgegeben.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `rar` | Vollständiger RAR-Packer mit zusätzlichen Archivänderungen. |
| `7z` | Kann je nach Build weitere Archivformate einschließlich RAR lesen; Unterstützung konkret prüfen. |
| `unzip` | Entpacker für ZIP-Archive mit anderer Syntax. |
| `tar` | Werkzeug für eine andere Archivfamilie. |
| `cmp`, `sha256sum` | Inhaltsvergleich beziehungsweise Prüfsummen mit einer vertrauenswürdigen Referenz. |

Ausgangseintrag: Datensatz 16 in `index.json`. Der allgemeine Hilfe-Platzhalter wurde durch getrennte Lese-, Test- und Entpackaufgaben mit offengelegtem praktischem Prüfbedarf ersetzt.
