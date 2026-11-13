# Codi – Abschluss der offenen Dokumentation 180–200

Auftrag vom 2026-11-13: den verbleibenden Rest nach Claude übernehmen und nach 200 stoppen. Tatsächlich fehlten 21 statt 20 Dateien: 180 dir bis 200 sync. 101–179 waren vorhanden; Claudes Bericht zählte erst bis 178. Die vorgefundenen Dateien bleiben unverändert.

Feste Zuordnung aus dem vorhandenen Index gegen die Original-CSV geprüft: tools/netmon-linux-befehlsdatenbank-v1.csv, 713 Datensätze, SHA-256 40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887. Der Index, die Original-CSV, zentrale Fortschrittsdateien und Claudes Bericht werden nicht geändert. Dieser Bericht hält ausschließlich den eigenen Stand fest. Während der Erstellung: keine Unteragenten, Commits, Pushes oder Merges. Die nachträgliche Veröffentlichung ist unten gesondert festgehalten. Besonderheit 184 find: Das Beispiel im lokalen Index enthielt zusätzliche Anführungszeichen gegenüber der CSV. Für die Ausgangsfelder ist die unveränderte CSV maßgeblich; der lokale Index wird nicht korrigiert.

Pro Eintrag: Ausgangsdatensatz gelesen, Primärquellen gelesen, Dokument ausgearbeitet, zulässige eigene Offlineübung geprüft beziehungsweise praktische Grenzen genannt, tatsächlicher Parser und Metadaten geprüft. Eigene kleine Dateien entstehen nur nach geprüftem mktemp und cd; Übungen laufen in einer eigenen Subshell mit set -eu. Hilfe/Version ist kein Funktionsnachweis. Keine realen Geräte-, Konto-, Dienst-, Mount- oder Netzänderungen und keine Paketinstallationen.

## 180 – [dir.md](dir.md)

- Überarbeitung: GNU dir listet Verzeichniseinträge und Dateiinformationen. Seine Vorgabe entspricht ls -C -b: spaltenweise, mit Backslashdarstellung nichtgrafischer Zeichen. Ohne Pfad wird das aktuelle Verzeichnis gelesen. Ein übergebenes Verzeichnis wird normalerweise geöffnet, eine Datei dagegen selbst beschrieben. -d zeigt den Verzeichniseintrag statt seines Inhalts. -a nimmt Punktnamen einschließlich . und .. auf, -A lässt genau diese zwei besonderen Einträge weg. Der Name dir bezeichnet hier das GNU-Werkzeug und nicht den gleichnamigen Windows-Shellbefehl. Optionen und Ausgabe sind deshalb nicht zwischen den Systemen austauschbar. Für eine kontrollierte Zeilenansicht wird -1 ausdrücklich gesetzt; Locale und Quotierungsoptionen bestimmen weiterhin die Darstellung.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt dir invocation](https://www.gnu.org/software/coreutils/manual/html_node/dir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Andere Dateinamen, Terminalbreiten und Implementierungen bleiben offen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 181 – [dirname.md](dirname.md)

- Überarbeitung: dirname entfernt die letzte Pfadkomponente aus einer Zeichenfolge. Es prüft nicht, ob dieser Pfad oder sein Elternverzeichnis existiert. Der Befehl arbeitet lexikalisch: Er entfernt abschließende Schrägstriche und die letzte verbleibende Komponente. Ohne Schrägstrich ergibt sich ein Punkt als Bezeichnung des aktuellen Verzeichnisses. Ein absoluter Eintrag direkt unter / liefert /. Mehrere Argumente werden getrennt verarbeitet. Punkte, .. und symbolische Links werden damit nicht zu einer tatsächlich existierenden kanonischen Datei aufgelöst. Gerade in Skripten ist die Ausgabe daher nur ein abgeleiteter Name, keine Zusicherung, dass cd dorthin erfolgreich wäre.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt dirname invocation](https://www.gnu.org/software/coreutils/manual/html_node/dirname-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. POSIX-Sonderfall // und Dateinamen mit Newlines nicht praktisch geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 182 – [du.md](du.md)

- Überarbeitung: du schätzt den für Dateien und Verzeichnisbäume belegten Speicher. Es beantwortet eine andere Frage als df, das den Zustand eines ganzen Dateisystems meldet. Die normale Ausgabe verwendet belegte Blöcke, nicht die logische Dateilänge. --apparent-size zeigt dagegen die sichtbare Länge, -b kombiniert das mit der Einheit ein Byte. Sparse-Dateien können deshalb eine große logische Länge bei geringer Belegung haben. Verzeichnismetadaten, Hardlinks, Kompression, CoW und Snapshots beeinflussen die Einordnung: du ist keine Garantie, wie viel Platz eine Löschung tatsächlich freigeben würde. Hardlinks werden standardmäßig nicht mehrfach als derselbe Dateiinhalt gezählt; -l ändert diese Regel. Ohne Zielargument wird der aktuelle Baum untersucht.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt du invocation](https://www.gnu.org/software/coreutils/manual/html_node/du-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine fremden Bäume, Netzlaufwerke, CoW-Snapshots oder Mehrfach-Hardlinks geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 183 – [file.md](file.md)

- Überarbeitung: file ordnet Dateien anhand von Dateisystemmerkmalen, Formatkennungen und Textmerkmalen ein. Die Endung allein entscheidet nicht über das Ergebnis. Die Erkennung ist eine Heuristik mit einer Magic-Datenbank. Ein Treffer bestätigt weder vollständige Formatgültigkeit noch Herkunft oder Harmlosigkeit. -b lässt den Namen weg, --mime-type liefert den erkannten Medientyp. -h betrachtet einen Symlink selbst, -L dessen Ziel. Die Vorgabe kann durch POSIXLY_CORRECT beeinflusst werden, deshalb den gewünschten Modus ausdrücklich wählen. Das Lesen kann den Zugriffszeitstempel beeinflussen. Optionen wie -z können komprimierten Inhalt untersuchen und zusätzliche Verarbeitung auslösen.
- Primärquellen: [Gelesene Primärquelle: file(1)](https://man7.org/linux/man-pages/man1/file.1.html), ergänzt durch die lokale Hilfe von file 5.45. Die Online-Manpage beschreibt 5.46, der eigene Test 5.45.
- Lokaler Stand: file 5.45. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Spezialdateien, Kompressionsvarianten oder unbekannten Binärdateien geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 184 – [find.md](find.md)

- Überarbeitung: GNU find durchsucht angegebene Startpfade und wertet für jeden Eintrag einen Ausdruck aus. Dieser Ausdruck kann nur auswählen und drucken, aber auch Programme ausführen oder Dateien löschen. Zwischen benachbarten Tests gilt normalerweise UND. -a bindet stärker als -o; Klammern sind für gemischte Bedingungen entscheidend. -name vergleicht den letzten Namen, -path den Suchpfad. Shellmuster müssen zitiert werden, damit die Shell sie nicht vor find expandiert. -print0 transportiert auch Namen mit Newlines eindeutig. Das fehlerhaft zitierte /home-Beispiel des Ausgangsdatensatzes wird durch einen kleinen eigenen Baum ersetzt. -delete ist eine aktive Löschaktion und schaltet Tiefendurchlauf ein; es ist kein Zusatz, den man unbesehen an eine Suchzeile hängt.
- Primärquellen: [Gelesene Primärquelle: GNU find(1)](https://man7.org/linux/man-pages/man1/find.1.html). Ergänzend lokale Hilfe und lokale GNU-findutils-Manpage /usr/share/man/man1/find.1.gz gelesen.
- Lokaler Stand: GNU findutils 4.9.0. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine -exec-/Löschaktion, Geräte-, Zeit- oder Rechtefilter praktisch geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 185 – [install.md](install.md)

- Überarbeitung: GNU install kopiert Dateien mit festgelegten Zielrechten oder legt Verzeichnisse an. Es ist kein Paketmanager und löst keine Softwareabhängigkeiten auf. Der Name stammt aus der Installation von Build-Ergebnissen in Zielverzeichnisse. Ohne -m gilt normalerweise ein ausführbarer Zielmodus, weshalb Text- und Konfigurationsdateien einen ausdrücklich passenden Modus brauchen. -D erzeugt fehlende Eltern und kopiert eine Datei, -d erzeugt nur Verzeichnisse. Die angegebenen Dateirechte sind nicht automatisch die Rechte aller mit -D entstehenden Eltern. install erhält erweiterte Attribute nicht allgemein wie eine vollständige Metadatensicherung. -o und -g betreffen Eigentümer beziehungsweise Gruppe und benötigen je nach Ziel besondere Rechte.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt install invocation](https://www.gnu.org/software/coreutils/manual/html_node/install-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Systeminstallation, Eigentümeränderung, Strip-, ACL- oder SELinuxprüfung.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 186 – [ln.md](ln.md)

- Überarbeitung: ln legt einen weiteren Dateinamen an. Ohne -s entsteht ein Hardlink, mit -s ein symbolischer Link, der eine Zielzeichenfolge enthält. Hardlinks auf normale Dateien teilen auf demselben Dateisystem dieselbe Dateiidentität und denselben Inhalt. Eine Änderung über einen Namen ist über den anderen sichtbar; das ist keine unabhängige Kopie. Symlinks enthalten dagegen einen Pfad. Relative Ziele werden vom Verzeichnis des Links aus aufgelöst, nicht vom späteren Arbeitsverzeichnis des Lesers. Ein nicht existentes Ziel verhindert die Anlage eines Symlinks nicht. Ein schon belegter Linkname wird normalerweise abgelehnt. -f kann vorhandene Ziele ersetzen und ist deshalb keine sichere Standardergänzung.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt ln invocation](https://www.gnu.org/software/coreutils/manual/html_node/ln-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Ersetzungsoptionen, Dateisystemwechsel oder Verzeichnis-Hardlinks geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 187 – [locate.md](locate.md)

- Überarbeitung: locate sucht Dateinamen in einer zuvor erzeugten Datenbank. Es durchläuft bei einer normalen Suche nicht wie find den aktuellen Verzeichnisbaum. Die Aktualität hängt vom Index ab: Neue Namen können fehlen, entfernte noch enthalten sein. Diese Datei beschreibt die Plocate-Familie, bei der locate je nach Distribution als entsprechender Aufruf bereitgestellt wird. Das Programm fehlt lokal. Mlocate und GNU locate sind andere Implementierungen. Besonders mehrere Suchmuster unterscheiden sich: Plocate verknüpft sie mit UND, Mlocate gewöhnlich mit ODER. -d wählt eine eigene Datenbank, eine gesetzte LOCATE_PATH-Variable kann weitere Datenbanken ergänzen. Das Suchmuster ist zunächst eine Teilzeichenfolge, bei Globbingzeichen gelten andere Abgleichregeln.
- Primärquellen: [Gelesene Primärquelle: Plocate-Handbuch](https://plocate.sesse.net/plocate.1.html), ergänzt durch die [Debian-Plocate-Manpage](https://manpages.debian.org/bookworm/plocate/plocate.1.en.html).
- Lokaler Stand: locate und updatedb nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. Indexaufbau, Datenbankformat, Sichtbarkeitsprüfung und alle Suchläufe bleiben offen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## 188 – [ls.md](ls.md)

- Überarbeitung: ls zeigt Informationen über Dateien und Verzeichnisse. Ohne Pfad wird das aktuelle Verzeichnis aufgelistet, normalerweise ohne Namen mit führendem Punkt. Die Darstellung hängt unter anderem von Terminal, Locale und gewählten Optionen ab. -l zeigt Metadaten wie Rechte, Hardlinkzahl, Eigentümer, Größe und einen Zeitstempel. Die angezeigte Dateigröße ist nicht automatisch der belegte Speicher. Bei einem Verzeichnis beschreibt dessen eigene Größe nicht die Summe seines Inhalts. -d wählt das Verzeichnis selbst. Der normale lange Zeitstempel bezeichnet mtime; ctime ist die Zeit der Metadatenänderung und keine allgemeine Erstellungszeit. Dateinamen können Leerzeichen, Newlines und Steuerzeichen enthalten, weshalb ein hübsches Listing keine universelle maschinenlesbare Dateiliste ist.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt ls invocation](https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur einfache Namen und Verzeichnis-/Dateiansicht geprüft, keine ACL-/Spezialdatei- oder Fremdbaumsuche.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 189 – [mkdir.md](mkdir.md)

- Überarbeitung: mkdir legt neue Verzeichnisse an. Es verändert den Dateibaum und ist deshalb auch bei eigenen Dateien kein rein lesender Befehl. Ohne -p führt ein bereits vorhandener Name gewöhnlich zu einem Fehler. -p erzeugt fehlende Eltern und akzeptiert vorhandene Verzeichnisse. Es macht aber eine vorhandene normale Datei nicht zum Verzeichnis und passt vorhandene Rechte nicht automatisch an. Die Rechte neuer Verzeichnisse hängen ohne besondere Vorgaben von Modus, umask und gegebenenfalls Default-ACLs ab. -m gilt für die ausdrücklich genannten neu angelegten Verzeichnisse; zusätzliche mit -p erzeugte Eltern folgen eigenen Anlageregeln. Auf einem fremden Ziel kann ein scheinbar harmloser mkdir-Aufruf daher mehr neue Objekte erzeugen als erwartet.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt mkdir invocation](https://www.gnu.org/software/coreutils/manual/html_node/mkdir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine fremden Rechte, Default-ACLs, Spezialbits oder Systemverzeichnisse verändert.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 190 – [mktemp.md](mktemp.md)

- Überarbeitung: mktemp erzeugt eine neue temporäre Datei oder mit -d ein Verzeichnis und gibt den tatsächlich reservierten Namen aus. Der erfolgreiche Anlegevorgang unterscheidet es von einer bloßen Zufallszeichenfolge. Die Vorlage braucht bei GNU mktemp mindestens drei aufeinanderfolgende X im letzten Namensbestandteil. --tmpdir beziehungsweise -p wählen das Basisverzeichnis. Ohne Vorlage wird eine Vorgabe im temporären Basisverzeichnis verwendet. Neue Dateien beginnen höchstens mit Benutzer-Lese-/Schreibrechten, neue Verzeichnisse höchstens mit Benutzer-Lese-/Schreib-/Suchrechten; eine strengere umask kann weiter einschränken. -u erzeugt nur einen noch unbenutzten Namen und reserviert nichts. Dessen spätere Verwendung als sicherer Dateiname wäre ein Race, weil ein anderer Prozess dazwischen ein Objekt anlegen könnte.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt mktemp invocation](https://www.gnu.org/software/coreutils/manual/html_node/mktemp-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine künstlich herbeigeführten Platz-/Rechtefehler, keine -u-Reservierungsrennen und keine fremden Objekte geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 191 – [mv.md](mv.md)

- Überarbeitung: mv benennt Dateien oder Verzeichnisse um beziehungsweise verschiebt sie. Anders als cp soll nach erfolgreichem Verschieben der ursprüngliche Quellname verschwunden sein. Innerhalb desselben Dateisystems genügt oft eine Umbenennung. Über eine Dateisystemgrenze kann GNU mv dagegen kopieren und anschließend die Quelle entfernen. Eine Gruppe von Verschiebungen ist deshalb keine gemeinsame atomare Transaktion. Ein bestehendes Ziel kann ohne ausdrücklich gewählten Schutz ersetzt werden. -T legt fest, dass das letzte Argument der genaue Zielname ist und nicht als vorhandenes Zielverzeichnis verwendet werden soll. Ob die Ausführung erlaubt ist, hängt wesentlich von den Rechten an Quell- und Zielverzeichnissen ab, nicht nur vom Schreibbit der Datei.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt mv invocation](https://www.gnu.org/software/coreutils/manual/html_node/mv-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur eigene Umbenennung und Kollisionsüberspringen geprüft, keine Fremdpfade oder Dateisystemwechsel.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 192 – [readlink.md](readlink.md)

- Überarbeitung: readlink zeigt ohne Kanonisierungsoption den in einem symbolischen Link gespeicherten Zieltext. Dieser Text kann relativ sein und muss auf kein existierendes Objekt zeigen. Ein normaler Dateipfad ohne Symlink liefert im einfachen Lesemodus keinen Linktext und einen Fehlerstatus. -f, -e und -m wechseln dagegen in einen anderen Modus: Sie bilden kanonische Pfade mit unterschiedlichen Anforderungen an vorhandene Komponenten. -f erlaubt eine fehlende letzte Komponente, -e verlangt alle Komponenten, -m lässt auch weitere fehlende Komponenten zu. Ein erfolgreich berechneter Pfad ist daher je nach Modus ausdrücklich kein Existenzbeweis. GNU empfiehlt für Kanonisierung den deutlicher benannten Befehl realpath.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt readlink invocation](https://www.gnu.org/software/coreutils/manual/html_node/readlink-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur gespeicherter Text, vorhandene Zielauflösung und Nicht-Link-Fall geprüft, keine Rennen oder fremden Ziele.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 193 – [realpath.md](realpath.md)

- Überarbeitung: realpath berechnet eine kanonische Pfadform. GNU realpath löst normalerweise Symlinks auf und entfernt überflüssige Slashes sowie .- und ..-Komponenten. Die normale GNU-Vorgabe verlangt vorhandene Komponenten außer der letzten. -e verlangt einen vollständig vorhandenen Pfad. -m berechnet auch bei fehlenden Komponenten eine mögliche Pfadform; es legt diese Objekte nicht an. -P löst Links vor nachfolgenden ..-Komponenten auf, -L behandelt diese logischen Komponenten anders. --relative-to liefert eine Darstellung relativ zu einem gewählten Bezugsordner. Ein kanonischer Name bleibt nur eine Aussage über die Auflösung zum Prüfzeitpunkt und bindet eine spätere Dateiöffnung nicht an dieselbe Datei.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt realpath invocation](https://www.gnu.org/software/coreutils/manual/html_node/realpath-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. -e, -m und relative Ausgabe im eigenen Baum geprüft, -L/-P-Sonderfälle und paralleler Austausch offen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 194 – [rename.md](rename.md)

- Überarbeitung: rename bezeichnet auf Linux unterschiedliche Programme mit inkompatibler Syntax. Dieses Dokument erläutert die Perl-/File::Rename-Familie, die unter Debian als file-rename beziehungsweise rename verfügbar sein kann. Die Perl-Variante erhält einen Ausdruck, der den Dateinamensstring in $_ verändert. Die Util-linux-Variante erhält dagegen getrennte Teilstring- und Ersatzargumente und wird hier separat als rename.ul dokumentiert. Lokal fehlt ein Programm namens rename; aus dem vorhandenen rename.ul wird deshalb kein getesteter Perl-Aufruf abgeleitet. Ein Perl-Ausdruck ist ausführbarer Code. -n unterdrückt die Umbenennung, macht aber unbekannten Perl-Code nicht zu passiven Daten. Die betrachtete Variante arbeitet standardmäßig auf dem ganzen übergebenen Pfad; -d begrenzt die Namensänderung auf die letzte Komponente.
- Primärquellen: [Gelesene Primärquelle: File::Rename-Handbuch](https://manpages.debian.org/bookworm/rename/file-rename.1p.en.html). Die dort beschriebene Familie wird ausdrücklich von Util-linux getrennt.
- Lokaler Stand: rename nicht vorhanden; File::Rename-Dokumentation gelesen. Nicht praktisch geprüft; praktische Prüfung offen. Keine Perl-Auswertung oder Umbenennung mit rename praktisch geprüft.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## 195 – [rename_ul.md](rename_ul.md)

- Überarbeitung: rename.ul ist auf diesem System die Rename-Variante von Util-linux. Sie erwartet einen Suchteilstring, einen Ersatz und die ausdrücklich ausgewählten Dateien; kein Perl-Programm. Normalerweise wird das erste Vorkommen der Teilzeichenfolge im letzten Namensbestandteil ersetzt. -a ersetzt alle, -l das letzte Vorkommen. Wenn Suchtext oder Ersatz einen Slash enthalten, können auch Pfadteile betroffen sein; neue Eltern werden dadurch nicht automatisch erzeugt. Ohne Schutzoptionen ist ein vorhandenes Ziel nicht pauschal geschützt. -s ändert den Zieltext eines Symlinks statt seinen Namen. Diese Wirkungen sind von einer bloßen Vorschau mit -n -v zu unterscheiden. Neuere Online-Handbücher können zusätzliche Optionen enthalten, die lokale Hilfe von 2.39.3 ist für den Test maßgeblich.
- Primärquellen: [Gelesene Primärquelle: Util-linux rename(1)](https://man7.org/linux/man-pages/man1/rename.1.html). Zusätzlich lokale Manpage /usr/share/man/man1/rename.ul.1.gz und Hilfe von 2.39.3 gelesen.
- Lokaler Stand: Util-linux 2.39.3. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur Vorschau und eigene kollisionsfreie Umbenennung geprüft, kein -s und kein vorhandenes Ziel überschrieben.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 196 – [rm.md](rm.md)

- Überarbeitung: rm entfernt angegebene Dateinamen und mit rekursiven Optionen auch Verzeichnisinhalte. Es verschiebt Dateien nicht in einen Desktop-Papierkorb und besitzt keine allgemeine Rückgängig-Funktion. Das Entfernen eines Namens ist nicht dasselbe wie sicheres Überschreiben des Inhalts. Weitere Hardlinks oder ein noch offener Dateideskriptor können die Datei beziehungsweise belegte Daten weiter erhalten. Ob ein Name entfernt werden darf, hängt wesentlich von den Rechten seines Elternverzeichnisses sowie zusätzlichen Regeln wie dem Sticky-Bit ab. Ein nicht schreibbarer Dateiinhalt ist daher kein allgemeiner Löschschutz. Ein Symlink wird bei einem gewöhnlichen Dateinamenargument selbst entfernt, nicht automatisch sein Ziel. Erweiterte oder rekursive Fälle mit Pfadbestandteilen verlangen zusätzliche Vorsicht.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt rm invocation](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Kein Entfernen, keine rekursive Aktion und keine Rückfrage praktisch ausgeführt; nur Version gelesen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## 197 – [rmdir.md](rmdir.md)

- Überarbeitung: rmdir entfernt vorhandene leere Verzeichnisse. Ein Verzeichnis mit Inhalt wird nicht rekursiv geleert, sondern normalerweise mit einer Fehlermeldung abgelehnt. Damit ist die Wirkung enger als bei rm -r, aber weiterhin eine reale Änderung am Dateibaum. Auch eine unsichtbare Punktdatei zählt als Inhalt. -p versucht nach dem ausgewählten Verzeichnis zusätzlich seine Eltern zu entfernen, bis ein Hindernis auftritt. Bei mehreren Argumenten oder -p können bereits einzelne Verzeichnisse verschwunden sein, bevor ein späterer Fehler den Gesamtstatus ungleich null macht. --ignore-fail-on-non-empty unterdrückt genau bestimmte Nichtleer-Fehler und macht nicht sämtliche anderen Ursachen harmlos.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt rmdir invocation](https://www.gnu.org/software/coreutils/manual/html_node/rmdir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Keine Verzeichnisse entfernt und kein -p-Lauf ausgeführt; nur Version gelesen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## 198 – [shred.md](shred.md)

- Überarbeitung: shred überschreibt ausgewählte Dateien und kann sie optional anschließend entfernen. Es garantiert auf heutigen Speichersystemen nicht pauschal, dass sämtliche früheren Kopien unwiederbringlich verschwinden. Das Verfahren setzt voraus, dass die betreffenden Daten tatsächlich an den relevanten physischen Stellen überschrieben werden. SSD-Wear-Leveling, Snapshots, Copy-on-Write, komprimierte Speicherung, Datenjournale und andere Kopien können diese Annahme verletzen. Backups und externe Spiegel werden nicht automatisch erfasst. Ohne -u bleibt der Name normalerweise erhalten, obwohl sein Inhalt bereits verändert wurde. Mehr Durchläufe oder eine abschließende Nullrunde lösen diese Architekturprobleme nicht. Ein beobachteter Nullinhalt wäre nur ein sichtbarer Dateizustand und kein forensischer Löschbeweis.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt shred invocation](https://www.gnu.org/software/coreutils/manual/html_node/shred-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Keine Überschreib- oder Löschfunktion getestet, keine Wirksamkeitsbehauptung für SSDs, CoW, Snapshots oder Backups; nur Version gelesen.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## 199 – [stat.md](stat.md)

- Überarbeitung: GNU stat zeigt Metadaten einer Datei oder eines Dateisystems. Es kann konkrete Werte wie Dateilänge, Modus, Inode und Hardlinkzahl getrennt von einer dekorierten ls-Ansicht ausgeben. Ohne -L wird ein übergebener Symlink selbst beschrieben, mit -L dessen Ziel. -f wechselt auf Dateisysteminformationen, deren Formatcodes andere Bedeutungen haben können. %s ist die logische Größe in Bytes, %b die Anzahl zugeordneter Blöcke und %B deren berichtete Einheit. Eine Inodenummer ist nur zusammen mit dem Dateisystem-/Gerätekontext sinnvoll. %x, %y und %z betreffen Zugriffs-, Inhaltsänderungs- und Statusänderungszeit; die letzte ist keine Erstellungszeit. Eine Erstellungszeit kann als %w vorliegen oder unbekannt sein.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt stat invocation](https://www.gnu.org/software/coreutils/manual/html_node/stat-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur eigene Datei-/Linkmetadaten geprüft, keine Fernsysteme, Automounts oder Zeitstempelauswertung.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Ein eigener Bashblock syntaktisch geprüft und ausgeführt.

## 200 – [sync.md](sync.md)

- Überarbeitung: GNU sync fordert die Synchronisierung gepufferter Schreibvorgänge an. Es ist weder ein Kopierprogramm noch ein Ersatz für ein Backup oder das kontrollierte Beenden einer Anwendung. Ohne Dateiangabe betrifft sync die globale Synchronisierung, nicht nur das aktuelle Verzeichnis. Mit ausdrücklich angegebenen Dateien verwendet GNU sync normalerweise fsync für diese Dateien. -d wählt fdatasync mit den für die Daten nötigen Metadaten. -f bezieht dagegen das ganze Dateisystem ein, auf dem die angegebene Datei liegt; der Wirkungsbereich ist also größer als der eine Dateiname vermuten lässt. Ein Anwendungsprogramm kann zusätzlich noch eigene nicht an den Kernel übergebene Puffer halten. Erfolgreiche Synchronisierung allein bestätigt weder einen konsistenten Mehrdatei-Anwendungszustand noch die Wiederherstellbarkeit einer Sicherung.
- Primärquellen: [Gelesene Primärquelle: GNU-Handbuch, Abschnitt sync invocation](https://www.gnu.org/software/coreutils/manual/html_node/sync-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.
- Lokaler Stand: GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Nur Version und Primärquelle geprüft, kein fsync-/fdatasync-/syncfs-/globaler Funktionslauf und kein Persistenztest.
- Tatsächlicher Parser, feste Zuordnung, Metadaten und zehn Hauptabschnitte: bestanden. Kein Funktionslauf; das Beispiel ist als Textmuster gekennzeichnet.

## Abschlussprüfung

- 180–200 vollständig: 21/21 neue Dokumente, einzeln in aufsteigender Reihenfolge erstellt, unmittelbar danach Parser, Metadaten, feste Zuordnung und zehn Hauptabschnitte geprüft.
- Alle 21 Beispielblöcke bestehen bash -n, einschließlich der ausdrücklich nicht ausgeführten Textmuster. Diese Syntaxprüfung führt keine darin genannten Aktion aus.
- 15 veröffentlichte eigene Bashübungen in der Abschlussprüfung erneut ausgeführt, jeweils Gesamtstatus 0. Die Blöcke wurden zuvor lesbarer auf einheitliche --tmpdir-Vorbereitung und ausgeschriebene Newline-Escapes vereinheitlicht; geprüft wurde anschließend genau der veröffentlichte Stand. Erwartete negative Einzelprüfungen, etwa beim readlink-Aufruf auf eine normale Datei, sind im jeweiligen Block ausdrücklich abgefangen.
- Praktisch geprüfte Datensätze: 180, 181, 182, 183, 184, 185, 186, 188, 189, 190, 191, 192, 193, 195, 199.
- Praktische Funktionsprüfung offen: 187 locate (Programm und updatedb fehlen), 194 rename (Perl-/File::Rename-Programm fehlt), 196 rm, 197 rmdir, 198 shred und 200 sync (keine Lösch-, Überschreib- oder Synchronisierungsaktion ausgeführt). Bei vorhandenen Werkzeugen wurde die Version gelesen. Keine davon wird durch bash -n als funktional getestet ausgegeben.
- 101–179 erneut mit aktuellem Parser auf Struktur und Zuordnung geprüft: 79/79 bestanden. Die älteren Dokumente wurden dabei nicht vollständig erneut fachlich oder praktisch geprüft.
- Vorhandene Reader-Regression: **36 passed in 0.73s**. Aufruf: python3 -m pytest -q -p no:cacheprovider tests/test_linux_help_markdown.py, über eigenen Xvfb mit privaten HOME-/XDG-Verzeichnissen. Der Testdisplay war aus der Sandbox nicht erreichbar; der bereits bekannte isolierte Testaufbau außerhalb dieser Einschränkung bestand vollständig. Kein Reader-Code geändert.
- Bestand am Ende: **713/713 Dokumentdateien vorhanden**, keine Lücke im Nummernbestand. Das ist keine erneute fachliche Abnahme aller 713 Texte. Der zentrale Index und die zentrale Fortschrittsübersicht wurden bewusst nicht verändert und enthalten noch den früheren Integrationsstand.
- Änderungsumfang: ausschließlich 21 neue Dokumente und dieser eigene Bericht. Prüfsummenvergleich aller vor Beginn erfassten 2214 vorhandenen regulären Projekt-/Übergabedateien ergab keine Änderung oder fehlende Datei. Vorhandene fremde Änderungen im Arbeitsbaum bleiben erhalten. Keine Code-, Test-, CSV-, Index- oder Vorlagenänderung; kein Git-Staging, Commit, Push oder Merge.

## Feste Zuordnung für die Nachprüfung

| Nr. | Kennung | Name | Kategorie | Datei |
| --- | --- | --- | --- | --- |
| 180 | dir | dir | Dateien & Verzeichnisse | dir.md |
| 181 | dirname | dirname | Dateien & Verzeichnisse | dirname.md |
| 182 | du | du | Dateien & Verzeichnisse | du.md |
| 183 | file | file | Dateien & Verzeichnisse | file.md |
| 184 | find | find | Dateien & Verzeichnisse | find.md |
| 185 | install | install | Dateien & Verzeichnisse | install.md |
| 186 | ln | ln | Dateien & Verzeichnisse | ln.md |
| 187 | locate | locate | Dateien & Verzeichnisse | locate.md |
| 188 | ls | ls | Dateien & Verzeichnisse | ls.md |
| 189 | mkdir | mkdir | Dateien & Verzeichnisse | mkdir.md |
| 190 | mktemp | mktemp | Dateien & Verzeichnisse | mktemp.md |
| 191 | mv | mv | Dateien & Verzeichnisse | mv.md |
| 192 | readlink | readlink | Dateien & Verzeichnisse | readlink.md |
| 193 | realpath | realpath | Dateien & Verzeichnisse | realpath.md |
| 194 | rename | rename | Dateien & Verzeichnisse | rename.md |
| 195 | rename_ul | rename.ul | Dateien & Verzeichnisse | rename_ul.md |
| 196 | rm | rm | Dateien & Verzeichnisse | rm.md |
| 197 | rmdir | rmdir | Dateien & Verzeichnisse | rmdir.md |
| 198 | shred | shred | Dateien & Verzeichnisse | shred.md |
| 199 | stat | stat | Dateien & Verzeichnisse | stat.md |
| 200 | sync | sync | Dateien & Verzeichnisse | sync.md |

## Reproduzierbare Struktur- und Syntaxprüfung

Der folgende Block führt keine Beispiele aus und verändert keine Dateien. Er kann vom Repository-Stamm mit dem vorhandenen Python ausgeführt werden; der Reader-Parser wird direkt per Dateipfad geladen. Die feste Zuordnung wird aus der vorstehenden Berichttabelle gelesen und unabhängig gegen die unveränderte CSV geprüft. Für die vollständigen Funktionsnachweise gelten die Einträge oben, nicht dieser Prüfblock.

```python
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
root = Path.cwd()
base = root / "docs/linux-befehlsdatenbank"
report = base / "FORTSCHRITT-CODI-180-200.md"
spec = importlib.util.spec_from_file_location(
    "linux_doc_review", root / "netmon/services/linux_help_markdown_service.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
raw = (root / "tools/netmon-linux-befehlsdatenbank-v1.csv").read_bytes()
assert hashlib.sha256(raw).hexdigest() == (
    "40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887"
)
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
assert len(rows) == 713
headings = (
    "1. Kurzbeschreibung", "2. Was macht der Befehl?", "3. Syntax",
    "4. Wichtige Optionen", "5. Beispiel erklärt Schritt für Schritt",
    "6. Typische Anwendungsfälle", "7. Risiken, Nebenwirkungen und Vorsicht",
    "8. Häufige Fehler", "9. Sichere Varianten oder Tipps für Einsteiger",
    "10. Verwandte Befehle",
)
records = []
for line in report.read_text().splitlines():
    cells = [x.strip() for x in line.split("|")[1:-1]]
    if len(cells) == 5 and cells[0].isdigit():
        n, identifier, name, category, filename = cells
        records.append((int(n), identifier, name, category, filename))
assert [x[0] for x in records] == list(range(180, 201))
for n, identifier, name, category, filename in records:
    assert Path(filename).name == filename
    assert rows[n-1]["Befehl"] == name
    assert rows[n-1]["Kategorie"] == category
    source = (base / filename).read_text(encoding="utf-8")
    document = module.parse_document(source)
    md = document.metadata
    assert (md["source_record"], md["id"], md["name"], md["category"]) == (
        n, identifier, name, category
    )
    assert md["source_catalog"] == "tools/netmon-linux-befehlsdatenbank-v1.csv"
    assert md["language"] == "de" and isinstance(md["root_required"], bool)
    assert md["risk_level"] in {"safe", "caution", "danger"}
    assert tuple(b.text for b in document.blocks
                 if b.kind == "heading" and b.level == 2) == headings
    example = source.split("## 5. Beispiel erklärt Schritt für Schritt\n", 1)[1]
    example = example.split("\n## 6.", 1)[0]
    blocks = re.findall(r"```(?:bash|text)\n(.*?)\n```", example, re.S)
    assert len(blocks) == 1
    subprocess.run(["bash", "-n"], input=blocks[0], text=True, check=True)
print("21/21 Dokumente: Zuordnung, Struktur und Beispielsyntax bestanden")
```

## Verbleibende gemeinsame Prüfpunkte

Die zuvor dokumentierten Nacharbeiten an Claudes älteren Dateien bleiben separat offen, insbesondere die fehlenden Fehlerabbrüche in den 26 dort genannten Übungen und die zwei Präzisierungen in cp.md. Dieser Abschluss des Restbereichs ist keine Freigabe dieser Stellen und verändert sie nicht. Auch die eigenständige Erfassung von 179 df in einem späteren zusammengeführten Fortschrittsstand und die Integration der neuen 180–200 in den zentralen Index bleiben getrennte Schritte. Das vorherige Browser-Übergabepaket enthält noch den damaligen offenen Rest und darf nicht als aktueller Vollständigkeitsstand verwendet werden.

Die sechs offenen Funktionsprüfungen, andere Implementierungen und Versionen, fremde Dateibäume, ACL-/SELinux-Sonderfälle, Datenträgerpersistenz und sichere Datenvernichtung bleiben entsprechend den einzelnen Dokumenten offen. Keine Geräte-, Konto-, Dienst-, Mount- oder Netzwerkaktion zum Nachweis eines Beispiels durchgeführt. Keine vorhandenen Nutzerdaten verändert.

Nach Datensatz 200 gestoppt. Die Ergebnisse wurden zunächst uncommittet zur gemeinsamen Prüfung bereitgestellt. Anschließend hat der Nutzer Commit und Push ausdrücklich beauftragt.

## Nachträglich beauftragte Veröffentlichung

Zielbranch: codex/linux-docs-browser-handoff-20261113, geprüfte Basis ad9233a72bb17b47534e64cdaad49a2f5f8a5a3b. Zur Veröffentlichung gehören ausschließlich diese 21 neuen Dokumente und dieser Bericht (22 neue Dateien). Die separate saubere Arbeitskopie verhindert, dass fremde Änderungen aus dem lokalen main-Arbeitsbaum aufgenommen werden. Kein Merge nach main.

Die Angaben zum lokalen Gesamtbestand von 713 Dateien, zur unveränderten lokalen Indexübersicht und zu den 36 Reader-Tests beziehen sich auf die ursprüngliche lokale Prüfarbeitskopie. Dieser eng begrenzte Veröffentlichungsschritt überträgt keine anderen Dokumentbereiche und keinen zentralen Index auf den Übergabebranch. Die bestandenen 15 Beispielübungen und sechs offenen Funktionsprüfungen gelten unverändert für die hier veröffentlichten Dokumente.


Veröffentlichungsprüfung in der sauberen Übergabearbeitskopie: 21/21 Dokumente bestehen den dortigen tatsächlichen Parser sowie Zuordnung und Beispielsyntax. Zusätzlich python3 -m pytest -q -p no:cacheprovider tests/test_linux_command_docs_handoff.py: **31 passed in 0.05s**. Diese 31 Übergabetests sind getrennt von den zuvor lokal bestandenen 36 Reader-Tests.
