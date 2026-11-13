---
id: "ar"
name: "ar"
command: "ar"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "entwicklung", "bibliotheken"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 3
reviewed_at: "2026-11-13"
locally_checked_version: "GNU ar 2.42"
---

# ar – Dateien bündeln und statische Bibliotheken bearbeiten

## 1. Kurzbeschreibung

`ar` legt mehrere Dateien als Mitglieder in einem Archiv ab und kann solche Archive auflisten, verändern und auslesen. In der Softwareentwicklung wird es häufig für statische Bibliotheken mit der Endung `.a` verwendet. Ein solches Archiv ist kein ZIP-Archiv und komprimiert seine Mitglieder nicht automatisch.

**Für eigene Archive sind keine Root-Rechte erforderlich.** Je nach Operation wird nur gelesen oder das Archiv beziehungsweise der Ausgabeordner verändert. Die Datenbankangabe „sicher lesend“ darf deshalb nicht pauschal auf `ar` übertragen werden.

## 2. Was macht der Befehl?

Ein Archivmitglied ist eine enthaltene Datei. Beim Erstellen einer Bibliothek sind dies häufig übersetzte Objektdateien wie `modul.o`; für eine Übung reichen gewöhnliche Textdateien. Das Bündeln allein führt den Inhalt nicht als Programm aus.

`ar` arbeitet nicht wie ein Verzeichnis-Synchronisationsprogramm: Bei einer Ersetzung entscheidet der Mitgliedsname darüber, welcher Eintrag betroffen ist. Zwei Dateien aus unterschiedlichen Ordnern können denselben Basisnamen besitzen. Das muss bei Build-Prozessen und selbst zusammengestellten Archiven bedacht werden.

Grundlagen einschließlich statischer und dünner Archive erklärt das [GNU-Binutils-Handbuch zu `ar`](https://sourceware.org/binutils/docs/binutils/ar.html).

## 3. Syntax

```text
ar OPERATION[MODIFIKATOREN] ARCHIV [MITGLIED ...]
```

Die Buchstaben werden häufig ohne vorangestellten Bindestrich zusammengeschrieben:

```bash
ar rc "sammlung.a" "eins.txt" "zwei.txt"
ar t "sammlung.a"
ar x "sammlung.a"
```

`r` ist eine Operation, `c` ein Modifikator. `t` und `x` sind jeweils eigene Operationen. Eckige Klammern und die großgeschriebenen Platzhalter gehören nicht wörtlich in den Aufruf.

```bash
ar --help
ar --version
```

Diese Angaben beziehen sich auf GNU `ar`. **Prüfpunkt:** Andere Unix-Implementierungen und Werkzeuge wie `llvm-ar` können in Details abweichen. Für ein Build-System muss die gewählte Toolchain zusammenpassen.

## 4. Wichtige Optionen

| Operation oder Modifikator | Bedeutung | Konkrete Wirkung |
| --- | --- | --- |
| `t` | Mitglieder auflisten. | Ohne Auswahl alle Namen anzeigen. |
| `p` | Mitgliedsinhalte auf die Standardausgabe schreiben. | Ohne Auswahl können mehrere Inhalte unmittelbar aufeinander folgen. |
| `x` | Mitglieder extrahieren. | Schreibt Dateien in den aktuellen Ausgabeort. |
| `r` | Mitglieder einfügen oder gleichnamige ersetzen. | Ändert das Archiv. |
| `d` | Genannte Mitglieder löschen. | Entfernt Inhalte aus dem Archiv. |
| `c` | Das Anlegen eines neuen Archivs ausdrücklich vorsehen. | Unterdrückt die sonst übliche Anlagewarnung; kein Schutz vor Änderungen eines vorhandenen Archivs. |
| `s` | Symbolindex für Objektdateien erstellen oder aktualisieren. | Für statische Bibliotheken wichtig, etwa in `ar rcs`. |
| `v` | Ausführlichere Ausgabe. | Mit `t` unter anderem zusätzliche Mitgliedsangaben. |
| `D` | Deterministische Archivmetadaten verwenden. | Zeit- und Eigentümerangaben werden vereinheitlicht; für reproduzierbare Builds gedacht. |

Die genaue Bedeutung steht im [GNU-Handbuch zur Kommandozeile](https://sourceware.org/binutils/docs/binutils/ar-cmdline.html). Ein deterministischer Modus ist bei manchen GNU-Builds bereits Standard. Er ist kein Verfahren zum originalgetreuen Sichern von Dateimetadaten.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Kleine Testdaten vorbereiten

```bash
uebung="$(mktemp -d -t netmon-ar-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Erste Notiz.' > "eins.txt"
printf '%s\n' 'Zweite Notiz.' > "zwei.txt"
```

Nur weiterarbeiten, wenn der Wechsel in den neuen Übungsordner erfolgreich war. Die Umleitungen erzeugen dort zwei Testdateien. Bei einer Wiederholung am selben Ort würden die vorhandenen Testdateien überschrieben.

### Schritt 2: Beide Dateien bündeln

```bash
ar rc "sammlung.a" "eins.txt" "zwei.txt"
```

`r` nimmt die genannten Dateien auf. `c` kündigt die Anlage eines neuen Archivs an. `sammlung.a` ist der Archivname; die folgenden beiden Namen sind die Eingabedateien. Die Originale bleiben erhalten. Weil dies ein Übungsarchiv mit Textdateien ist, ist es noch keine nutzbare Programmbibliothek.

### Schritt 3: Inhaltsliste ansehen

```bash
ar t "sammlung.a"
```

Erwartet werden `eins.txt` und `zwei.txt`, jeweils als eigener Mitgliedsname. Eine Liste beweist lediglich, dass diese Einträge lesbar sind; sie ist kein Sicherheitsnachweis und keine vollständige Wiederherstellungsprüfung.

### Schritt 4: Einen Textinhalt auslesen

```bash
ar p "sammlung.a" "eins.txt"
```

Die erste Testnotiz wird auf der Standardausgabe angezeigt. Bei unbekannten Binärdaten sollte dieser Aufruf nicht blind direkt ins Terminal ausgegeben werden. Für die selbst angelegte Textdatei ist er gut nachvollziehbar.

### Schritt 5: In einen getrennten Ordner extrahieren

```bash
mkdir "Ausgabe"
cd "Ausgabe"
ar x "../sammlung.a"
```

Die beiden Notizen werden in `Ausgabe` angelegt. Vergleiche sie mit den ursprünglichen Dateien im übergeordneten Übungsordner. Das Archiv bleibt dabei erhalten. Für weitere Arbeiten am Archiv beachte, dass der aktuelle Arbeitsordner nun `Ausgabe` ist.

## 6. Typische Anwendungsfälle

**Statische Bibliotheken erstellen:** In einem passenden Build-Ablauf bündelt beispielsweise `ar rcs libbeispiel.a modul.o` Objektdateien und legt einen Symbolindex an. Das setzt vorhandene, zur Zielplattform passende Objektdateien voraus. Der Textdatei-Test ersetzt keinen Compiler- und Linkertest.

**Archivmitglieder untersuchen:** `ar tv sammlung.a` zeigt eine ausführlichere Übersicht. Vor einer gezielten Ersetzung prüfen, ob der erwartete Mitgliedsname tatsächlich vorhanden ist.

**Debian-Pakete technisch betrachten:** Ein `.deb` besitzt eine `ar`-Hülle; eine Inhaltsliste ist damit grundsätzlich möglich. Zur regulären Paketinstallation oder für Paketinformationen die Werkzeuge der Distribution verwenden. Ein Paket manuell zu extrahieren installiert es nicht korrekt.

**Reproduzierbare Build-Ergebnisse:** Deterministische Metadaten können Unterschiede zwischen zwei Builds verringern. Gleiche Archivmetadaten allein beweisen jedoch weder gleiche Quelldaten noch eine vertrauenswürdige Toolchain.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Gleichnamiges Mitglied ersetzt:** `r` kann einen bestehenden Eintrag austauschen. Das ist beim Aktualisieren erwünscht, bei einer falschen Dateiauswahl aber Datenverlust innerhalb des Archivs.
- **Ausgabedateien verändert:** `x` kann vorhandene Dateien am Ausgabeort ersetzen. Zum ersten Extrahieren einen neuen Ordner verwenden; nicht auf eine ZIP-ähnliche Rückfrage vertrauen.
- **Archivinhalt gelöscht:** `d` ist eine schreibende, löschende Operation. Ein wichtiger Originalbestand braucht vorher eine getrennte Kopie.
- **Binärdaten im Terminal:** `p` eignet sich direkt für bekannte Textdaten. Ungeprüfte Inhalte können unlesbare oder steuernde Zeichen enthalten.
- **Keine umfassende Ordnersicherung:** Das Format und der Umgang mit Namen und Metadaten sind nicht als Ersatz für eine Linux-Systemdatensicherung zu behandeln.
- **Dünnes Archiv verwechselt:** Ein „thin archive“ enthält Verweise auf externe Objektdateien. Allein die `.a`-Datei weiterzugeben kann daher unzureichend sein. Dieses Verhalten beschreibt das [GNU-Handbuch zu dünnen Archiven](https://sourceware.org/binutils/docs/binutils/ar.html).

**Root ist für keine der gezeigten Übungen nötig.** Ein Schreibfehler sollte zuerst zu einer Prüfung des Ausgabeordners führen, nicht zu einem ungeprüften `sudo ar ...`.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `ar: command not found` | Passendes Binutils-Paket fehlt. | Paketverwaltung und lokale Toolchain prüfen. |
| `file format not recognized` | Datei ist kein passendes Archiv oder beschädigt. | Dateityp und Herkunft prüfen; nicht nur der Endung vertrauen. |
| Datei zum Einfügen nicht gefunden | Arbeitsordner oder Pfad stimmt nicht. | `pwd` und die konkrete Eingabedatei prüfen. |
| Ein erwartetes Mitglied fehlt | Falsches Archiv oder gleicher Mitgliedsname ersetzt. | Vollständige Liste ansehen und Eingaben vergleichen. |
| Linker findet Symbole nicht | Index, Objektdateien, Architektur oder Linkeraufruf passen nicht. | Build-Protokoll prüfen; der Archivname allein macht noch keine funktionierende Bibliothek. |
| Dünnes Archiv lässt sich nicht wie erwartet auspacken | Es enthält Verweise statt vollständig eingebetteter Dateien. | Originale und vorgesehenen Build-Ablauf prüfen. |

Rückgabewert und Fehlermeldung gemeinsam beachten. Dass eine Archivdatei schon existiert, beweist nicht, dass ein neuer Änderungsaufruf erfolgreich war.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Den Ablauf zunächst mit den beiden kleinen Textdateien nachvollziehen.
2. Auflisten und Auslesen von schreibenden Operationen unterscheiden.
3. Zum Extrahieren einen leeren, eigenen Zielordner verwenden.
4. Vor einer Archivänderung die Mitgliederliste und die zugehörige Eingabedatei prüfen.
5. `c` nicht als „nur neu anlegen“ oder Überschreibschutz missverstehen.
6. Für statische Bibliotheken Compiler, Objektformat, Architektur und Linker als zusammengehörige Toolchain betrachten.
7. Bei Unsicherheit mit `ar --help` die lokal angebotenen Optionen prüfen.

**Prüfstand:** Mit GNU `ar` 2.42 wurden Textdateien gebündelt, aufgelistet, ausgelesen und getrennt extrahiert. Die extrahierten Inhalte entsprachen den Eingaben. Die gezielte Ersetzung eines Mitglieds wurde ebenfalls geprüft. Kein Compilerlauf, keine Paketinstallation und keine Löschoperation an Benutzerdateien wurden ausgeführt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ranlib` | Symbolindex einer statischen Bibliothek bearbeiten. |
| `nm` | Symbole von Objektdateien oder Bibliotheken untersuchen. |
| `objdump` | Technische Informationen zu Objekt- und Binärdateien anzeigen. |
| `gcc`, `clang` | Quellcode zu passenden Objektdateien übersetzen. |
| `tar` | Allgemeinere Ordner- und Dateiarchive mit anderer Syntax. |
| `dpkg-deb` | Debian-Pakete mit dafür vorgesehenen Funktionen untersuchen. |

Der ursprüngliche NetMon-Eintrag ist unter Datensatz 3 in `index.json` unverändert nachvollziehbar. Seine allgemeine Syntax wurde durch die erforderliche Operationsangabe ersetzt; die Dateiwirkungen sind nun getrennt beschrieben.
