---
id: "unxz"
name: "unxz"
command: "unxz"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "xz", "dekompression"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 17
reviewed_at: "2026-11-13"
locally_checked_version: "unxz aus XZ Utils 5.4.5"
---

# unxz – XZ-Dateien prüfen und mit erhaltener Quelle dekomprimieren

## 1. Kurzbeschreibung

`unxz` ist der Dekompressionsaufruf von XZ Utils und entspricht `xz --decompress`. Typischer Einsatz ist das Wiederherstellen des Inhalts einer `.xz`-Datei.

**Für eigene Dateien sind keine Root-Rechte nötig.** Ein gewöhnlicher erfolgreicher Dateiaufruf entfernt die komprimierte Eingabe. Mit `-k` bleibt sie erhalten; mit `-c` wird auf stdout statt in eine abgeleitete Datei geschrieben.

## 2. Was macht der Befehl?

Eine komprimierte Datei wird als Datenstrom verarbeitet. Aus `notiz.txt.xz` entsteht normalerweise `notiz.txt`. Das ist keine allgemeine Wiederherstellung einer Dateisammlung: Eine `.tar.xz`-Datei enthält nach der Dekompression weiterhin ein TAR-Archiv.

Der Aufrufname wählt den Dekompressionsmodus, erzwingt aber nicht automatisch ausschließlich das `.xz`-Format. XZ Utils kann abhängig von der Version weitere unterstützte Formate erkennen. Wer ausdrücklich nur `.xz` akzeptieren will, setzt `--format=xz`.

Die Zuordnung der Namen und die automatische Formaterkennung stehen in der [Distributions-Manpage zu unxz](https://manpages.debian.org/trixie/xz-utils/unxz.1.en.html). Optionen wurden mit der lokalen XZ-Utils-Hilfe abgeglichen. Formatdetails beschreibt die [offizielle Projektreferenz](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1).

## 3. Syntax

```text
unxz [OPTIONEN] [DATEI ...]
xz --decompress [OPTIONEN] [DATEI ...]
```

```bash
unxz -k "notiz.txt.xz"
unxz -t "notiz.txt.xz"
unxz -c "notiz.txt.xz"
unxz --format=xz -k "notiz.txt.xz"
```

Die ersten drei Aufrufe unterscheiden Dateiausgabe, Test und stdout. Der vierte macht die Formatbeschränkung ausdrücklich. Die Dateiendung steuert bei normaler Dateiausgabe auch die Ableitung des Ausgabenamens.

Ohne Dateiangabe beziehungsweise mit `-` liest das Werkzeug von stdin. Das ist eine andere Arbeitsweise als das automatische Ableiten eines Ausgabepfads aus einem Dateinamen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Eingabedatei behalten. | Für einen ersten Wiederherstellungsversuch ausdrücklich setzen. |
| `-c`, `--stdout` | Ergebnis auf stdout schreiben. | Erhält die Quelle; Umleitungen bleiben eigenständige Schreiboperationen. |
| `-t`, `--test` | Dekomprimieren und Ausgabe verwerfen. | Prüft vorhandene unterstützte Integritätsinformationen, keine Herkunft. |
| `-l`, `--list` | XZ-Dateiinformationen anzeigen. | Keine Liste von TAR-Mitgliedern und kein vollständiger Inhaltstest. |
| `--format=xz` | Nur `.xz` als Eingabeformat akzeptieren. | Hilfreich bei einer eindeutig festgelegten Schnittstelle. |
| `-M LIMIT`, `--memlimit=LIMIT` | Speicherbedarf begrenzen. | Bei zu hohem Dekompressionsbedarf schlägt der Vorgang fehl. |
| `-v`, `--verbose` | Mehr Angaben ausgeben. | Fortschritt und Diagnose; nicht mit Erfolg gleichsetzen. |
| `-f`, `--force` | Schutzregeln übergehen. | Kann vorhandene Zieldateien entfernen beziehungsweise ersetzen. |
| `--single-stream` | Nur den ersten Datenstrom verarbeiten und nachfolgende Daten ignorieren. | Kann gewollte weitere Inhalte ausschließen. |
| `--ignore-check` | Integritätsprüfung beim Dekomprimieren übergehen. | Für gewöhnliche Wiederherstellung vermeiden. |
| `--` | Optionen beenden. | Hilfreich für Dateinamen mit führendem Bindestrich. |

Nicht jeder Aufruf besitzt in jeder Version dieselben Zusatzfunktionen. Insbesondere Optionen für parallele Verarbeitung, Speichergrenzen und Sonderformate anhand der lokalen Version prüfen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und eigenen Arbeitsordner prüfen

```bash
unxz --version
uebung="$(mktemp -d -t netmon-unxz-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Verzeichniswechsel fortfahren. Die Übung verwendet keine bestehenden persönlichen Dokumente.

### Schritt 2: Bekannte kleine Datei komprimieren

```bash
printf '%s\n' 'Eigene UNXZ-Testnotiz.' > "original.txt"
xz -k "original.txt"
cp "original.txt.xz" "probe.xz"
```

Das Erstellen der Testeingabe erfolgt mit `xz`. Die Kopie `probe.xz` wird später zu `probe`, sodass das erhaltene `original.txt` nicht als Ausgabekonflikt im Weg steht.

### Schritt 3: Komprimierte Daten testen

```bash
unxz -t "probe.xz"
```

Ein erfolgreicher Abschluss legt noch keine dekomprimierte Datei an. Bei Fehlern nicht einfach die Inhaltsprüfung abschalten. Zuerst prüfen, ob die Datei vollständig und aus der erwarteten Quelle stammt.

### Schritt 4: Entpacken und vergleichen

```bash
unxz -k "probe.xz"
cmp "original.txt" "probe"
```

Die komprimierte Kopie bleibt erhalten. Die Wiederherstellung wird bei dieser bekannten Datei byteweise verglichen. `cmp` bleibt bei gleichem Inhalt normalerweise ohne Ausgabe und liefert einen erfolgreichen Abschlussstatus.

### Schritt 5: Bekannten Text auf stdout lesen

```bash
unxz -c "original.txt.xz"
```

Hier ist der Inhalt als eigene kurze Textdatei bekannt. Unbekannte Binärdaten nicht entsprechend ins Terminal schreiben. Es wird keine zweite Datei namens `original.txt` angelegt.

## 6. Typische Anwendungsfälle

**Eigene komprimierte Datei wiederherstellen:** Mit `-k` die Eingabe erhalten, solange das Ergebnis noch nicht geprüft ist. Bei wichtigen Daten mit einer unabhängigen Referenz vergleichen.

**Komprimiertes Archiv vorbereiten:** Aus `sammlung.tar.xz` wird eine TAR-Datei. Deren Einträge anschließend separat auflisten und in einen frischen Ordner entpacken. Die Dekompressionsstufe allein stellt keine Ordnerstruktur aus TAR her.

**Komprimierte Protokolle kontrolliert lesen:** stdout lässt sich einem geeigneten Anzeige- oder Analysewerkzeug zuführen. Das gewählte Folgeprogramm und die Fehlerbehandlung der Pipeline gehören zum Ablauf dazu.

**XZ-Datei vor einer Übertragung prüfen:** Ein Test kann bestimmte Datenfehler sichtbar machen. Für die Authentizität eines heruntergeladenen Pakets weiterhin den vorgesehenen vertrauenswürdigen Signatur- oder Referenzweg verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Eingabe wird normalerweise ersetzt

Ohne `-k` beziehungsweise stdout wird die komprimierte Quelldatei nach erfolgreicher Dateiausgabe entfernt. Der Name `unxz` bedeutet daher nicht nur lesende Betrachtung. Ein versehentlich falscher Pfad kann den falschen Bestand verändern.

### Prüfsummen sind keine Absenderprüfung

Das `.xz`-Format kann Inhaltsprüfwerte enthalten. Welche Prüfung tatsächlich vorhanden ist, hängt von der Datei ab; das Format erlaubt auch einen fehlenden Inhaltsprüfwert. Selbst eine erfolgreiche unterstützte Prüfung beweist nicht, wer den Inhalt erstellt hat oder ob er harmlos ist. Einzelheiten stehen in der [XZ-Projektdokumentation](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1).

### RAM und Ausgabemenge unterscheiden

Eine hohe Kompression kann viel RAM für den Decoder und sehr viel Plattenplatz für das Ergebnis erfordern. `-M` begrenzt den Dekompressionsspeicher, nicht die spätere Dateigröße. Mehr freien RAM bereitzustellen löst keinen vollen Datenträger.

### Mehrere Datenströme können zum Inhalt gehören

Gültige hintereinandergehängte `.xz`-Datenströme werden normalerweise gemeinsam dekomprimiert. `--single-stream` kann nach dem ersten aufhören und weitere Daten ignorieren. Den Schalter nicht als universelle Lösung gegen eine Meldung über nachfolgende Daten verwenden.

### Erzwingen und Umleiten können Schutz aufheben

`-f` kann bestehende Ausgaben ersetzen. Eine Shell-Umleitung kann ihr Ziel schon öffnen und leeren, bevor die Dekompression später scheitert. Eingabe und Ausgabe dürfen deshalb nie derselbe Pfad sein. Kein ungeprüftes `--ignore-check` ergänzen.

**Root-Rechte sind für die Übung nicht erforderlich.** Ein fehlendes Schreibrecht sollte zuerst Anlass sein, den gewählten Zielpfad zu prüfen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel existiert bereits | Original erhalten oder früher entpackt. | Freien kontrollierten Ausgabepfad wählen. |
| Format nicht erkannt | Falsche, unvollständige oder beschädigte Eingabe. | Quelle und tatsächliches Format prüfen. |
| Speicherlimit überschritten | Decoder benötigt mehr RAM als erlaubt. | Bedarf und Herkunft beurteilen, Limit bewusst wählen. |
| Nach dem Vorgang bleibt `.tar` | Kompression entfernt, Archivierung noch vorhanden. | Mit einem passenden Archivwerkzeug fortfahren. |
| Liste sieht plausibel aus, Inhalt schlägt fehl | Metadatenansicht mit vollständigem Test verwechselt. | `-t` und gegebenenfalls Wiederherstellung getrennt prüfen. |
| Ergebnis ist kürzer als erwartet | Nur erster Datenstrom verarbeitet. | `--single-stream` und Eingabestruktur prüfen. |

Bei XZ Utils bedeutet Status `0` Erfolg, `1` Fehler und `2` Warnung. Vorhandene Ausgaben, Meldungen und den Abschlussstatus gemeinsam beurteilen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit `--version` die konkrete Implementierung prüfen.
2. Eigene kleine Testdaten und einen neuen Arbeitsordner verwenden.
3. Komprimierte Eingaben mit `-k` erhalten.
4. Vorhandene Zieldateien nicht unbedacht erzwingen.
5. Für fest vereinbarte XZ-Eingaben `--format=xz` erwägen.
6. Prüfung und tatsächliche Wiederherstellung getrennt durchführen.
7. RAM-Bedarf und Ausgabespeicher getrennt planen.
8. Vertraute Referenzen für Inhalt und Herkunft zusätzlich heranziehen.

**Prüfstand:** Mit `unxz` aus XZ Utils 5.4.5 wurden Testmodus, Dateiausgabe mit `-k`, stdout und die normale Entfernung einer zusätzlichen eigenen Eingabekopie geprüft. Die Inhalte waren bytegleich. Eine vorhandene geänderte Testausgabe wurde ohne Erzwingen abgelehnt und blieb erhalten. Zwei hintereinandergehängte gültige XZ-Datenströme wurden auf stdout vollständig zusammen ausgegeben. Keine praktischen Tests mit großen Dateien, fremden Inhalten, Speichergrenzen oder sämtlichen Prüfwertvarianten.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xz` | Hauptaufruf für Kompression, Dekompression und weitere XZ-Funktionen. |
| `xzcat` | Dekomprimiert standardmäßig auf stdout. |
| `unlzma` | Legacy-LZMA-Formatwahl mit abweichenden Containergrenzen. |
| `tar` | Behandelt eine enthaltene Dateisammlung. |
| `cmp` | Vergleicht bekannte Dateien byteweise. |
| `gunzip`, `unzstd` | Andere Dekompressionswerkzeuge mit eigenen Formaten und Regeln. |

Ausgangseintrag: Datensatz 17 in `index.json`. Originalerhalt, Formatwahl, Prüfgrenzen und die Behandlung mehrerer XZ-Datenströme sind gegenüber dem Hilfe-Platzhalter konkretisiert.
