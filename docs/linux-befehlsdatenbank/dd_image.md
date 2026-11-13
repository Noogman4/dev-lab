---
id: "dd_image"
name: "dd image"
command: "dd"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: true
risk_level: "danger"
tags: ["aufgabenorientierte hilfe", "dd_image"]
status: "Ausgearbeitet; Kopie ausschließlich zwischen eigenen regulären Testdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 52
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils dd 9.4"
---

# dd image – Bytekopien verstehen und Geräteziele eindeutig abgrenzen

## 1. Kurzbeschreibung

`dd image` ist eine Aufgabenbezeichnung für Bytekopien beziehungsweise Datenträgerabbilder mit `dd`. Es gibt keinen eigenen Unterbefehl `image`. Eingabe und Ausgabe werden über `if=` und `of=` angegeben.

**Für eigene reguläre Dateien sind keine Root-Rechte nötig.** Direkter Zugriff auf reale Blockgeräte benötigt gewöhnlich entsprechende Privilegien. Ein falsches Geräte-Schreibziel kann Daten ohne Rückfrage überschreiben; die Aufgabe wird daher als gefährlich eingeordnet.

## 2. Was macht der Befehl?

Dd kopiert einen Datenstrom blockweise. Ohne bewusst gewählte Umwandlung ist das eine Bytekopie, keine Dateisystemverwaltung. Das Programm erkennt nicht automatisch, ob das Schreibziel ein leerer Testpfad oder ein wichtiger Datenträger ist.

Eine Dateikopie, ein Lesen von einem Blockgerät in eine Image-Datei und das Zurückschreiben einer Image-Datei auf ein Gerät sind unterschiedliche Aufgaben. Besonders die letzte Richtung kann Partitionstabellen und vorhandene Dateisysteminhalte ersetzen.

Grundlagen: [Distributions-Manpage zu GNU dd](https://manpages.debian.org/trixie/coreutils/dd.1.en.html) und lokale Hilfe von coreutils 9.4. Hier werden ausschließlich selbst angelegte reguläre Dateien verwendet. Reale Geräteabbilder, Mounts und Wiederherstellungen werden nicht ausgeführt.

## 3. Syntax

```text
dd if=EINGABE of=AUSGABE [WEITERE_OPERANDEN]
```

```bash
dd if="quelle.bin" of="kopie.bin" bs=64K conv=excl status=none
```

`if=` ist die Leseseite, `of=` die Schreibseite. Vertauschen kann das gewünschte Original zerstören. Die Operandenschreibweise ist keine übliche Kombination aus `--input` und `--output`. Anführungszeichen dürfen den Dateiwert beziehungsweise den ganzen Operanden schützen.

## 4. Wichtige Optionen

| Operand | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `if=DATEI` | Eingabe lesen. | Ohne Vorgabe wird stdin verwendet. |
| `of=DATEI` | Ausgabe schreiben. | Ohne Vorgabe stdout; bestehende reguläre Ziele können standardmäßig gekürzt werden. |
| `bs=GRÖSSE` | Lese-/Schreibblockgröße. | Kein Sicherheitscheck für das Ziel. |
| `count=N` | Anzahl Eingabeblöcke begrenzen. | Blöcke sind nicht automatisch Bytes. |
| `skip=N` | Eingabeblöcke überspringen. | Einheit hängt vom zugehörigen Blockmaß beziehungsweise Byte-Suffix ab. |
| `seek=N` | Ausgabeposition verschieben. | Kann gezielte Datenbereiche überschreiben. |
| `conv=excl` | Bei vorhandenem Ausgabepfad ablehnen. | Für neue reguläre Testdateien geeignet. |
| `conv=notrunc` | Bestehende Ausgabe nicht kürzen. | Verhindert nicht das Überschreiben ausgewählter Bytes. |
| `conv=fsync` | Daten und einschlägige Metadaten vor Ende synchronisieren. | Kein Schutz vor falschem Ziel. |
| `conv=sync` | Eingabeblöcke auffüllen. | Andere Bedeutung als physisches Synchronisieren. |
| `iflag=fullblock` | Vollständige Eingabeblöcke sammeln. | Für bestimmte Pipe-/Count-Abläufe relevant. |
| `status=progress` | Fortschritt melden. | Erfolgsnachweis braucht trotzdem Abschluss und Inhaltsprüfung. |
| `status=none` | Normale Statistik unterdrücken. | Fehler bleiben sichtbar. |
| `conv=noerror` | Trotz bestimmter Lesefehler fortsetzen. | Kein allgemeines Datenrettungsrezept. |

Bei GNU dd bedeutet `K` 1024 und `kB` 1000. Einheiten und Blockzählung bewusst prüfen. Der hier gezeigte Test braucht keine Direct-I/O-, Fehlerfortsetzungs- oder Geräteparameter.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Testort wählen

```bash
dd --version
uebung="$(mktemp -d -t netmon-dd-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Keinen Pfad unter `/dev` für diese Übung einsetzen.

### Schritt 2: Kleine bekannte Quelle erzeugen

```bash
printf '%s\n' 'Eigene DD-Testdatei.' > "quelle.bin"
```

Die Endung `.bin` macht den Inhalt nicht zu einem Datenträgerabbild. Es ist lediglich eine eigene reguläre Testdatei mit bekannten Bytes.

### Schritt 3: Nur in neuen regulären Pfad kopieren

```bash
dd if="quelle.bin" of="kopie.bin" bs=64K conv=excl status=none
```

Ohne `count` wird hier bis zum Ende der kleinen Quelldatei kopiert. `conv=excl` verhindert das Ersetzen einer bereits vorhandenen `kopie.bin`.

### Schritt 4: Inhalt vergleichen

```bash
cmp "quelle.bin" "kopie.bin"
```

Bei identischem Inhalt endet der Bytevergleich normalerweise ohne Ausgabe erfolgreich. Das ist ein Nachweis für diese beiden bekannten Dateien, nicht für die Wiederherstellbarkeit eines echten Dateisystems.

### Schritt 5: Vorhandenes Ziel als Schutzfall verstehen

Ein zweiter identischer dd-Aufruf soll wegen `conv=excl` abgelehnt werden. Das ist keine Aufforderung, den Schutz abzuschalten. Für eine neue Übung neuen Arbeitsordner verwenden.

## 6. Typische Anwendungsfälle

**Eigene Bytekopie erstellen:** Für reguläre Dateien häufig auch mit einfacheren Kopierwerkzeugen möglich. Dd ist besonders dann sinnvoll, wenn Block- oder Positionsparameter ausdrücklich benötigt werden.

**Ein vorhandenes Image lesen oder kontrolliert kopieren:** Größe, Herkunft und erwarteten Inhalt unabhängig prüfen. Eine Endung `.img` sagt nicht, ob ein vollständiger Datenträger oder nur eine Partition abgebildet ist.

**Administratives Datenträgerabbild:** Erfordert eine separat geplante eindeutige Gerätezuordnung, Konsistenz, ausreichenden Platz und einen geprüften Rückweg. Diese Dokumentation liefert keinen direkt ausführbaren Geräte-Schreibbefehl.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Falsches Schreibziel kann unmittelbar Daten zerstören

Dd fragt nicht allgemein nach, ob ein Blockgerät wirklich gemeint ist. Ein vertauschtes `if`/`of` kann das Original überschreiben. Ein Gerätepfad muss vor einem realen Auftrag eindeutig, aktuell und unabhängig zugeordnet werden. Platzhalter aus fremden Beispielen sind kein Nachweis.

### Aktive Dateisysteme und Konsistenz

Ein lesendes Rohabbild eines laufend veränderten Dateisystems kann inkonsistent sein. Ein erfolgreiches Kopierende beweist keine konsistente Datenbank oder später bootfähige Wiederherstellung. Mount- und Snapshot-Planung gehören zu einem eigenen Auftrag.

### Grenzen von Kopieroptionen

`conv=notrunc` verhindert nur das Kürzen, nicht das Überschreiben. `conv=sync` fügt Auffüllbytes hinzu und ist nicht dasselbe wie `fsync`. Ein großes `bs` macht einen falschen Befehl nicht richtiger.

### Defekte Medien

Ungeplante Wiederholungen können problematische Datenträger weiter beanspruchen. `noerror,sync` ist kein Ersatz für ein geprüftes Rettungsverfahren mit geeignetem Werkzeug und Fortschrittskarte. Bei wichtigen defekten Medien zuerst die konkrete Rettungsstrategie klären.

### Speicherbedarf und Ergebnisprüfung

Images können sehr groß sein. Ein voller Zielbereich kann eine unvollständige Datei hinterlassen. Abschlussstatus, Größe und passende Inhalts-/Wiederherstellungsprüfung gemeinsam beurteilen.

**Root-Rechte werden für eigene reguläre Testdateien nicht benötigt.** Blockgerätezugriff und insbesondere Gerätebeschreiben sind andere, ausdrücklich freizugebende Aufgaben.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel existiert | `conv=excl` schützt den Pfad. | Neuen kontrollierten Zielnamen wählen. |
| Kein Platz | Ausgabe größer als verfügbarer Speicher. | Platzbedarf und unvollständiges Ergebnis prüfen. |
| Berechtigung fehlt | Falscher Pfad oder geschütztes Gerät. | Zweck und Zuordnung klären, nicht reflexartig sudo ergänzen. |
| Falsche Größe | Block-/Count-Einheiten oder Abbruch. | Gewählte Einheiten und Meldungen lesen. |
| Image startet nicht | Unvollständiges oder inkonsistentes Abbild, falscher Umfang. | Geeignete Wiederherstellungsprüfung separat planen. |
| Daten trotz notrunc verändert | Option schützt nicht gegen normales Schreiben. | Tatsächlichen Bytebereich und Rückweg prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Ausschließlich eigene kleine reguläre Dateien zum Lernen verwenden.
2. Lese- und Schreibseite vor jedem Aufruf laut beziehungsweise sichtbar zuordnen.
3. Neue Ziele mit `conv=excl` schützen.
4. Keine Blockgeräte, Mounts oder echten Originale als Übung nutzen.
5. Einheiten und Grenzen ausdrücklich lesen.
6. Kopiererfolg und vollständige Wiederherstellbarkeit getrennt prüfen.

**Prüfstand:** GNU dd 9.4 kopierte eine selbst erzeugte 1024-Byte-Datei mit `conv=excl`. Quelle und Kopie waren bytegleich. Nach einer eigenen Änderung der Zieldatei wurde erneutes Schreiben abgelehnt und deren Inhalt erhalten. Keine Blockgeräte, Mounts, Rohabbilder, beschädigten Medien oder privilegierten Aktionen wurden verwendet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cp` | Gewöhnliche Dateikopien ohne dieselbe Blocksyntax. |
| `cmp`, `sha256sum` | Bytevergleich beziehungsweise Prüfsummen. |
| `ddrescue` | Spezialisierte Datenrettung mit anderem Verfahren. |
| `lsblk`, `findmnt` | Geräte-/Mountzuordnung lesen; kein automatischer Schreibauftrag. |

Ausgangseintrag: Datensatz 52 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
