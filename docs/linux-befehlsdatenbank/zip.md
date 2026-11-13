---
id: "zip"
name: "zip"
command: "zip"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive & kompression", "zip"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 25
reviewed_at: "2026-11-13"
locally_checked_version: "Info-ZIP Zip 3.0"
---

# zip – Dateisammlungen erstellen und bestehende Archive bewusst ändern

## 1. Kurzbeschreibung

`zip` verpackt Dateien und Verzeichnisse in ZIP-Archive. Es kann neue Archive erstellen und vorhandene Einträge hinzufügen, ersetzen oder löschen. Diese Anleitung beschreibt Info-ZIP Zip 3.0 unter Linux.

**Für eigene Dateien sind keine Root-Rechte nötig.** Archivänderungen sind Schreiboperationen. Manche Optionen löschen zusätzlich Quelldateien; der Befehl ist deshalb nicht pauschal sicher lesend.

## 2. Was macht der Befehl?

Ein ZIP-Archiv enthält getrennte Mitglieder mit Namen, Daten und Metadaten. Standardmäßig fügt `zip` die ausgewählten Dateien hinzu beziehungsweise ersetzt gleichnamige Archivmitglieder. Nicht erneut ausgewählte alte Mitglieder bleiben normalerweise erhalten. Ein bestehendes Archiv wird dadurch nicht automatisch zum exakten Abbild des aktuellen Quellordners.

Verzeichnisse werden mit `-r` rekursiv aufgenommen. Kompression und Archivierung sind hier gemeinsam verfügbar. Eine bereits komprimierte Datei kann trotzdem kaum kleiner werden.

Quellen: [Distributions-Manpage für zip](https://manpages.debian.org/trixie/zip/zip.1.en.html), lokale Hilfe `zip -h` und Build-Angaben aus `zip -v`. Unterstützung für Zip64, Kompressionsmethoden und Verschlüsselung anhand der tatsächlichen Empfänger prüfen.

## 3. Syntax

```text
zip [OPTIONEN] ARCHIV.zip QUELLE ...
```

```bash
zip "notizen.zip" "notiz.txt"
zip -r "sammlung.zip" "Material"
```

Der Archivname steht vor den Quellen. Existiert er bereits, ist ein Änderungsauftrag möglich. Für eine neue unvermischt aufgebaute Sammlung einen wirklich neuen Archivnamen wählen. Namen und Shell-Muster bewusst zitieren.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-r` | Ordner rekursiv aufnehmen. | Kann unbeabsichtigte private Unterordner einbeziehen. |
| `-0` | Ohne Kompression speichern. | Archivstruktur entsteht trotzdem. |
| `-1` bis `-9` | Kompressionsaufwand wählen. | Kein garantierter Platzgewinn bei allen Daten. |
| `-u` | Neue beziehungsweise geänderte Dateien aktualisieren. | Keine vollständige Spiegelung mit Löschung alter Mitglieder. |
| `-f` | Bestehende Mitglieder auffrischen. | Andere Wirkung als normales Hinzufügen. |
| `-d` | Mitglieder aus dem Archiv löschen. | Verändert das Archiv, nicht die entsprechenden Quelldateien. |
| `-m` | Nach erfolgreicher Aufnahme Quellen entfernen. | Für erste Übungen vermeiden. |
| `-j` | Verzeichnispfade verwerfen. | Gleiche Basisnamen können kollidieren. |
| `-x MUSTER` | Passende Namen ausschließen. | Muster gegen Archiv-/Quellpfade prüfen. |
| `-y` | Unter Unix symbolische Links als Links speichern. | Andernfalls kann referenzierter Inhalt aufgenommen werden. |
| `-T` | Archiv prüfen. | Unterstütztes Testwerkzeug muss verfügbar sein. |
| `-e` | Mit Passwort verschlüsseln. | Klassische Verschlüsselung dieser Variante nicht als modernen Schutz sensibler Daten behandeln. |
| `-h2` | Erweiterte Hilfe. | Für Sonderfälle die lokale Fassung lesen. |

`-P PASSWORT` kann das Geheimnis in Argumenten und Shell-Verlauf offenlegen. Auch eine interaktive Passworteingabe macht ein ungeeignetes Verschlüsselungsverfahren nicht stärker.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsordner wählen

```bash
zip -v
uebung="$(mktemp -d -t netmon-zip-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Die nächsten Namen dürfen nicht mit wichtigen bestehenden Daten belegt sein.

### Schritt 2: Kleine Sammlung vorbereiten

```bash
mkdir -p "Material/unterordner"
printf '%s\n' 'Eigene ZIP-Testnotiz.' > "Material/unterordner/notiz.txt"
```

Die eigene Testdatei liegt in einer bekannten Unterstruktur.

### Schritt 3: Neues Archiv erstellen

```bash
zip -r "sammlung.zip" "Material"
```

Das Archiv liegt außerhalb von `Material`. So gehört die wachsende Archivdatei nicht zur aufgenommenen Quellstruktur. Die Quelldatei bleibt ohne `-m` erhalten.

### Schritt 4: Mitglieder und Daten prüfen

```bash
zipinfo -1 "sammlung.zip"
unzip -t "sammlung.zip"
```

Die Namensliste zeigt die erwartete Mitgliedsstruktur. Der zweite Aufruf verarbeitet Inhalte zur Prüfung. Beide Prüfziele unterscheiden sich.

### Schritt 5: Kontrolliert wiederherstellen

```bash
mkdir "Ausgabe"
unzip -n "sammlung.zip" -d "Ausgabe"
cmp "Material/unterordner/notiz.txt" "Ausgabe/Material/unterordner/notiz.txt"
```

Die Ordnerstruktur enthält den aufgenommenen Quellordnernamen. `cmp` vergleicht die bekannte Datei byteweise. Für eine neue Übung einen neuen Arbeitsort verwenden.

## 6. Typische Anwendungsfälle

**Dateien weitergeben:** Eine bewusst ausgewählte Sammlung mit verbreitetem Containerformat erstellen. Kompressions- und Verschlüsselungsunterstützung des Empfängers beachten.

**Eigene Unterlagen bündeln:** Vorher nach Zugangsdaten, versteckten Dateien und unnötigen Build-Ergebnissen sehen. Ein ZIP ist nicht allein dadurch eine vollständige Sicherung aller Linux-Eigenschaften.

**Vorhandenes Archiv ändern:** Ausgewählte Mitglieder ergänzen oder ersetzen. Vorher eine unabhängige Kopie aufbewahren, wenn ältere Archivstände wichtig sind.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Alte Mitglieder können erhalten bleiben

Ein neuer Lauf über einen geschrumpften Quellordner entfernt dessen inzwischen gelöschte Dateien normalerweise nicht aus einem bestehenden Archiv. Dadurch können veraltete oder vertrauliche Inhalte weiter enthalten sein. Für einen neuen Veröffentlichungsstand einen frischen Archivpfad und eine geprüfte Mitgliederliste verwenden.

### Lösch- und Pfadoptionen

`-d` entfernt Archivmitglieder; `-m` kann Quelldateien löschen. `-j` verändert die Struktur. Keine dieser Optionen aus fremden Rezepten übernehmen, ohne die konkrete Wirkung zu verstehen.

### Links, Metadaten und laufende Dateien

Symbolische Links können zusätzliche Daten erreichbar machen. `-y` verändert die Linkdarstellung, ist aber keine allgemeine Sicherung aller Metadaten. Laufend veränderte Dateien und Datenbanken erfordern einen konsistenten Aufnahmeablauf.

### Vertraulichkeit und Ressourcen

Dateinamen und Kommentare können Informationen verraten. Klassische ZIP-Verschlüsselung nicht als verlässlichen Schutz hochsensibler Daten einsetzen. Große Archive brauchen temporären und endgültigen Speicherplatz; ein voller Datenträger kann eine Aktualisierung scheitern lassen.

**Root-Rechte sind für die Übung nicht erforderlich.** Erhöhte Rechte würden den zugänglichen Quellumfang vergrößern und damit zusätzliche Daten einschließen können.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Nothing to do | Keine passenden Eingaben. | Quellpfade und Muster prüfen. |
| Unterordner fehlen | Ohne `-r` gearbeitet. | Gewünschte Auswahl bewusst rekursiv erfassen. |
| Alte Datei weiter enthalten | Bestehendes Archiv nur aktualisiert. | Für frischen Stand neues Archiv erstellen und auflisten. |
| Empfänger kann nicht entpacken | Methode, Zip64 oder Verschlüsselung nicht unterstützt. | Kompatibilität konkret prüfen. |
| Unerwartete Namen | Pfadwahl oder `-j` verändert Struktur. | Mitgliedsliste vor dem Teilen prüfen. |

Warnungen über nicht lesbare Quellen beachten. Ein erzeugtes Archiv kann trotzdem Einträge vermissen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Eigenen kleinen Ordner und neuen Archivnamen verwenden.
2. Archiv außerhalb der Quellen ablegen.
3. Ohne `-m` und `-d` beginnen.
4. Mitgliederliste, Datenprüfung und Wiederherstellung getrennt prüfen.
5. Vor einer Weitergabe vertrauliche und veraltete Mitglieder ausschließen.
6. Ein vorhandenes Archiv nicht als automatische Spiegelung verstehen.

**Prüfstand:** Mit Info-ZIP Zip 3.0 wurden rekursive Erstellung einer eigenen kleinen Struktur, Mitgliederliste, `unzip -t` und stdout-Wiedergewinnung geprüft. Der Inhalt war bytegleich. Ein erneuter Aufruf für dasselbe Mitglied ersetzte dessen archivierten Inhalt; Quellen blieben erhalten. Verschlüsselung, Linkbehandlung, große Archive und Löschoptionen wurden nicht praktisch geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `unzip` | ZIP-Dateien testen und entpacken. |
| `zipinfo` | Mitglieder und technische Angaben lesen. |
| `7z` | Andere Archivoberfläche mit eigenem Funktionsumfang. |
| `tar` | Dateisammlung mit anderen Metadaten- und Kompressionsregeln. |
| `cmp` | Bekannte wiederhergestellte Inhalte vergleichen. |

Ausgangseintrag: Datensatz 25 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
