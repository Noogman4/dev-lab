---
id: "badblocks"
name: "badblocks"
command: "badblocks"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["datentraeger", "diagnose", "blockgroesse", "datenverlust"]
status: "Korrigiert; Quellen und Struktur geprüft; praktische Geräteprüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 209
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Paketmetadaten: e2fsprogs 1.47.0-2.4~exp1ubuntu4.1"
---

# badblocks – Prüfmodi, Blocknummern und Diagnosegrenzen verstehen

## 1. Kurzbeschreibung

`badblocks` aus e2fsprogs untersucht einen ausgewählten Speicherbereich auf fehlerhafte Blöcke. **Der Schreibtest `-w` überschreibt den untersuchten Bereich und zerstört dort vorhandene Daten.** Auch der als nichtdestruktiv bezeichnete Modus `-n` schreibt und ist kein gefahrloser Test.

Für reale Blockgeräte sind üblicherweise besondere Zugriffsrechte nötig; darauf bezieht sich `root_required: true`. Es ist keine Aussage, dass jeder mögliche Zugriff zwingend unter UID 0 erfolgen muss. Dokumentationslesen benötigt kein Root. Hier werden keine Geräte geöffnet und keine Scans ausgeführt.

## 2. Was macht der Befehl?

Die gewählte Betriebsart bestimmt, wie Blöcke geprüft werden:

| Modus | Vorgang | Bedeutung für vorhandene Daten |
| --- | --- | --- |
| Standard ohne `-n` und `-w` | Lesender Test. | Schreibt keine Testmuster, kann aber Datenträger und I/O stark belasten. |
| `-n` | Lese-Schreib-Test mit beabsichtigter Wiederherstellung ursprünglicher Daten. | Schreibt tatsächlich. Fehler, Abbruch oder Stromausfall können Daten beschädigen. |
| `-w` | Testmuster schreiben, lesen und vergleichen. | Ursprüngliche Daten werden überschrieben; keine Erhaltung zugesichert. |

`-n` und `-w` schließen sich aus. Ein gewöhnlicher Lesetest bestätigt zunächst nur, ob die angefragten Blöcke lesbar waren. Ohne bekannte Referenz lässt sich daraus nicht ableiten, ob die gelesenen Nutzdaten inhaltlich richtig sind. `-t` im Lesemodus setzt voraus, dass das ausgewählte Muster bereits vorhanden ist; sonst entstehen erwartbare Vergleichsfehler.

Gelesen wurden die [e2fsprogs-Manpage bei Debian, Version 1.47.2](https://manpages.debian.org/trixie/e2fsprogs/badblocks.8.en.html) und die lokale Manpage zu 1.47.0. Sie empfehlen bei einer beabsichtigten Weitergabe an ext-Dateisystemwerkzeuge deren integrierte Prüfabläufe, damit die Blockgröße passt. Das ist keine Freigabe, hier `e2fsck` oder `mke2fs` zu starten.

## 3. Syntax

```text
badblocks [OPTIONEN] GERAET [LETZTER_BLOCK [ERSTER_BLOCK]]
```

**Nur Syntaxmuster, nicht ausführen.** `GERAET` muss bei einer später gesondert geplanten Wartung eindeutig identifiziert werden. Ein vermuteter Gerätename genügt nicht. Die optionale Endblocknummer begrenzt den Bereich; ohne sie wird grundsätzlich bis zum Geräteende geprüft. Ohne Anfangsangabe beginnt der Bereich am ersten Block. Soll ein Anfang angegeben werden, muss in dieser Positionssyntax auch der Endblock davor stehen.

Blocknummern beziehen sich auf die mit `-b` gewählte Blockgröße und auf den Anfang des geöffneten Objekts. Bei einer Partition ist das nicht automatisch derselbe Byteoffset wie auf dem gesamten physischen Laufwerk.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze oder Risiko |
| --- | --- | --- |
| `-b BYTES` | Größe eines Prüfblocks, Standard 1024 Bytes. | Fehlernummern ändern ihre Bedeutung mit dieser Einheit. |
| `-c N` | Anzahl gleichzeitig bearbeiteter Blöcke. | Anders als `-b`; beeinflusst Arbeitsmenge und Speicherbedarf. |
| `-s` | Groben Fortschritt des aktuellen Durchgangs anzeigen. | 100 Prozent eines Durchgangs ist nicht immer das Ende aller Durchgänge. |
| `-v` | Fehlerstatistik auf Standardfehler ausgeben. | Unterscheidet Lese-, Schreib- und Datenvergleichsfehler. |
| `-o DATEI` | Neue fehlerhafte Blocknummern in Datei schreiben. | Kann vorhandene Ausgabedaten ersetzen; kein Backup. |
| `-i DATEI` | Bereits bekannte fehlerhafte Blöcke einlesen. | Diese werden übersprungen und in der neuen Fehlerliste nicht erneut aufgeführt. |
| `-e N` | Bei N gefundenen fehlerhaften Blöcken abbrechen. | Ergebnisliste kann absichtlich unvollständig sein; 0 begrenzt die Zahl nicht. |
| `-p N` | Wiederholen, bis N aufeinanderfolgende Durchgänge keine neuen Blöcke liefern. | Nicht einfach „genau N Durchgänge“. |
| `-t MUSTER` | Vergleichs-/Schreibmuster auswählen. | Im Lesemodus nur ein vorhandenes, nicht zufälliges Muster. |
| `-n` | Nichtdestruktiv gedachter Lese-Schreib-Modus. | Trotzdem Schreibzugriffe und Ausfallrisiko. |
| `-w` | Destruktiver Schreibmodus. | Nicht auf einem Datenträger mit zu erhaltenden Daten verwenden. |

`-f` kann die Ablehnung bei einem gemounteten Ziel übergehen; `-X` ist ein interner Schalter zum Umgehen der exklusiven Belegungsprüfung. Beides gehört nicht in einen Lern- oder Standardaufruf. Ein fehlender Schutzfehler beweist umgekehrt keine sichere Zielwahl.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur das Handbuch lesen

Voraussetzung ist eine vorhandene lokale Manpage. Der folgende Aufruf liest Dokumentation und führt keinen Blocktest aus:

```bash
man 8 badblocks
```

Erwartet wird die Handbuchseite mit Abschnitten zu Syntax, Optionen und Warnungen. Fehlt sie, die oben verlinkte Dokumentation lesen; zur Erfüllung dieser Übung ist keine Installation erforderlich. Lokal wurde die Seite mit `man -P cat badblocks` vollständig gelesen.

### Schritt 2: Eine ausdrücklich erfundene Fehlerliste verstehen

**Das folgende Muster ist keine Ausgabe eines ausgeführten Scans.** Angenommen, ein bereits gesondert geplanter Test hätte Blockgröße 1024 Bytes verwendet und diese neuen Fehlernummern geliefert:

```text
17
300
```

Ohne `-o` stünde eine solche Nummernliste auf der Standardausgabe; mit `-o` in der benannten Datei. Fortschritt und ausführliche Diagnose werden davon getrennt auf Standardfehler ausgegeben. Die Liste enthält Blocknummern, keine Dateinamen, Seriennummern oder Byteadressen.

### Schritt 3: Die Einheit nachrechnen

Bei nullbasierter Nummerierung beginnt Block 17 bei `17 × 1024 = 17408` Bytes relativ zum Beginn des untersuchten Objekts. Derselbe Zahlenwert 17 bedeutete bei Blockgröße 4096 dagegen `69632` Bytes. Eine Liste ohne dokumentierte Blockgröße und eindeutigen Zielbezug ist deshalb nicht zuverlässig weiterverwendbar.

Nicht einfach diese Nummern einem Dateisystemwerkzeug übergeben. Dessen Blockgröße und Adressbezug müssen übereinstimmen. Es erfolgt hier keine Übernahme einer Fehlerliste und keine Dateisystemänderung.

### Schritt 4: Die Aussagegrenze festhalten

Eine leere neue Liste kann bedeuten, dass keine neuen Fehler gefunden wurden. Sie kann zusammen mit Abbruch, falschem Bereich, übersprungenen bekannten Blöcken oder einer unvollständigen Ausführung aber auch irreführend sein. Meldungen, Abschluss und tatsächlich geprüften Bereich gemeinsam beurteilen. Das Muster erbringt keinerlei Aussage über ein vorhandenes Laufwerk.

## 6. Typische Anwendungsfälle

**Kontrollierte Wartungsdiagnose:** Ein gesondert freigegebener Ablauf untersucht einen eindeutig bestimmten Bereich. Bei einem bereits auffälligen Datenträger hat eine geeignete Sicherungs- oder Rettungsstrategie Vorrang vor belastenden Experimenten.

**Dateisystembezogene Fehlerlisten:** ext-Werkzeuge können eigene integrierte Prüfungen anbieten. Deren Optionen sind eigenständige Arbeitsaufträge; eine Datei mit Nummern ist nicht beliebig zwischen Werkzeugen austauschbar.

**Test eines entbehrlichen Mediums:** Ein destruktiver Test wäre nur bei einem bewusst vollständig entbehrlichen Ziel denkbar. Das ist kein Bestandteil dieser Dokumentationserprobung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Aushängen allein beweist keine sichere Exklusivität. Abbildungen über LVM, RAID, Verschlüsselung und andere Schichten sowie Zugriffe anderer Prozesse müssen in einem echten Wartungsplan verstanden werden. Auch ein nur lesend gemountetes Dateisystem ist kein zulässiges Argument, Schreibtest-Schutzprüfungen zu umgehen.

Ein langer vollständiger Lesetest kann bereits geschädigte Hardware weiter belasten. Schreibtests beanspruchen das Medium zusätzlich. Interne Fehlerkorrektur, Remapping und Speichercontroller begrenzen, was ein logischer Blocktest über physische Zellen aussagt. Ein bestandener Test garantiert weder zukünftige Zuverlässigkeit noch einen fehlerfreien Dateisystemzustand.

Root-Rechte schaffen keine fachliche Freigabe. Die Beispieldarstellung enthält absichtlich keinen kopierfertigen Geräteaufruf.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel wird als benutzt abgelehnt | Schutz gegen konkurrierende Nutzung. | Stoppen und Wartungsplan klären, nicht Schutzoptionen umgehen. |
| Fast alles scheitert beim Mustervergleich | Vorausgesetztes Muster war nicht gespeichert. | Prüfart und Erwartung klären. |
| Fehlerliste passt nicht zum Dateisystem | Blockgrößen oder Adressbezug verschieden. | Nicht importieren; Zuordnung fachlich prüfen. |
| Nur wenige Nummern trotz vieler Probleme | `-e` oder Abbruch begrenzt; `-i` lässt bekannte aus. | Laufumfang und Meldungen prüfen. |
| Keine Fehler, trotzdem Ausfälle | Defekt intermittierend oder außerhalb der Prüfung. | Ergebnis nicht als Gesundnachweis verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Handbuch und klar markierte Muster lesen, statt an realen Geräten zu üben. Modus und Blockeinheit vor jeder späteren Wartungsplanung ausdrücklich festhalten. `-n` niemals als Synonym für „nur lesen“ verstehen.

**Prüfstand am 2026-11-13:** Lokale und verlinkte Handbücher gelesen. Die lokale Paketdatenbank meldet `e2fsprogs 1.47.0-2.4~exp1ubuntu4.1`; das ist ein Paketnachweis, kein ausgeführter Programmtest. **Nicht praktisch geprüft:** badblocks selbst, alle Modi, Geräte-I/O, Ausgabeformat eines echten Scans und Übernahme von Fehlerlisten. Kein Gerät geöffnet, kein Scan und kein Schreibtest ausgeführt. Die Zahlen in Abschnitt 5 sind ausschließlich ein erklärtes Muster.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `e2fsck` | ext-Dateisystemprüfung mit eigenen Voraussetzungen und Risiken. |
| `mke2fs` | ext-Dateisystemerstellung; kann Daten zerstören. |
| `dumpe2fs` | Informationen über ext-Dateisysteme, unter anderem bekannte fehlerhafte Blöcke. |
| `smartctl` | Andere Ebene der Laufwerksdiagnose; ersetzt keine Sicherung. |
| `lsblk` | Übersicht über Blockgeräteschichten, kein alleiniger Identitätsbeweis. |

Ausgangsdatensatz 209, Kategorie und Dateizuordnung wurden mit Katalog und Original-CSV abgeglichen. Die Entwurfsdatei bleibt als Vergleich erhalten.
