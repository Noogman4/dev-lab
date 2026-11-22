---
id: "svn"
name: "svn"
command: "svn"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["svn", "entwicklung"]
status: "Quellen und Struktur geprüft; lokales Arbeitskopiebeispiel praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 301
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Apache-Anleitung und Referenz geprüft"
---

# svn – Eine Subversion-Arbeitskopie verwalten

## 1. Kurzbeschreibung

`svn` ist das Kommandozeilenwerkzeug von Apache Subversion, einer zentral organisierten Versionsverwaltung. Es verbindet lokale Arbeitskopien mit einem Repository und kann Änderungen anzeigen, übernehmen oder veröffentlichen. **Für eigene Arbeitsdateien sind keine Root-Rechte nötig.** Zugriffsrechte am Repository sind davon getrennt.

## 2. Was macht der Befehl?

Eine Arbeitskopie enthält Projektdateien und Verwaltungsdaten im Verzeichnis `.svn`. Das Repository bewahrt den versionierten Verlauf. Nicht jeder lokale Dateischritt ist bereits veröffentlicht: `add` merkt eine neue Datei für die Aufnahme vor, `commit` überträgt die gewählten Änderungen in eine neue Repositoryrevision.

Die [offizielle Apache-Kurzanleitung](https://subversion.apache.org/quick-start) erklärt Repository, Arbeitskopie und grundlegende Aktionen. Die [Distributions-Manpage](https://manpages.debian.org/trixie/subversion/svn.1.en.html) verweist für die installierte Syntax zusätzlich auf `svn help`. Für Statusspalten wurde auch die [Subversion-Buchreferenz](https://svnbook.red-bean.com/en/1.8/svn.ref.svn.c.status.html) gelesen; diese Seite kennzeichnet ihren Stand als überarbeitungsfähig, daher werden daraus keine Zusagen über neue Versionsfunktionen abgeleitet.

## 3. Syntax

```text
svn UNTERBEFEHL [OPTIONEN] [ZIELE ...]
svn help UNTERBEFEHL
svn status [ARBEITSKOPIE]
svn diff [ARBEITSKOPIE]
```

Unterbefehle haben eigene Bedeutungen. `update` holt Änderungen in die Arbeitskopie, `commit` veröffentlicht gewählte Änderungen im Repository. `checkout` erzeugt eine neue Arbeitskopie. Ein lokaler Pfad und eine Repository-URL sind nicht austauschbar.

## 4. Wichtige Optionen

| Form | Bedeutung | Grenze |
| --- | --- | --- |
| `help NAME` | Hilfe zu einem Unterbefehl. | Vor Übernahme fremder Optionen lesen. |
| `--version` | Clientversion anzeigen. | Kein Nachweis einer Serverkompatibilität. |
| `--config-dir PFAD` | Eigene Clientkonfiguration wählen. | Kein vollständiger Ausführungskäfig. |
| `status` | Lokale Änderungen anzeigen. | Ohne -u gewöhnlich kein Repositorykontakt nötig. |
| `status -u` | Zusätzlich Repositorystand berücksichtigen. | Kann Serverkontakt und Anmeldung benötigen. |
| `diff` | Unterschiede darstellen. | Ausgabe kann vertrauliche Inhalte enthalten. |
| `-r REVISION` | Revision für passende Aktionen auswählen. | Bedeutung hängt vom Unterbefehl ab. |
| `commit -m TEXT` | Änderungen mit Nachricht veröffentlichen. | Echter Repository-Schreibvorgang. |

Ein `revert` kann lokale ungesicherte Änderungen verwerfen. Es gehört nicht als beiläufige Reparatur in einen ersten Lernablauf.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur ein neues lokales Repository vorbereiten

Dieses Beispiel setzt `svn` und `svnadmin` voraus. Beide fehlen hier; der Ablauf wurde nicht ausgeführt. Er verwendet ausschließlich neue temporäre Daten und eine lokale Datei-URL, keinen Server.

```bash
(
  uebung="$(mktemp -d -t netmon-svn-XXXXXX)" || exit 1
  svnadmin create "$uebung/repo" || exit 1
  svn checkout --config-dir "$uebung/config" "file://$uebung/repo" "$uebung/arbeit" || exit 1
  printf 'Eigene Testnotiz\n' > "$uebung/arbeit/notiz.txt" || exit 1
  svn add --config-dir "$uebung/config" "$uebung/arbeit/notiz.txt" || exit 1
  svn status --config-dir "$uebung/config" "$uebung/arbeit" || exit 1
  svn diff --config-dir "$uebung/config" "$uebung/arbeit"
)
```

### Schritt 2: Rollen auseinanderhalten

`repo` ist die neue lokale Verlaufsspeicherung; `arbeit` die neue Arbeitskopie. `config` nimmt die ausdrücklich gewählte Clientkonfiguration auf. Die Datei-URL ergibt mit dem absoluten Pfad die Form `file:///...`. Das Anlegen dieses lokalen Testrepositories erfordert keinen laufenden Netzwerkdienst.

### Schritt 3: Erwarteten Status verstehen

Nach `add` sollte `status` die Testdatei als vorgemerkt hinzugefügt kennzeichnen. `diff` sollte ihren Inhalt als neue Änderung zeigen. Das ist eine erwartete, nicht gemessene Ausgabe. Es erfolgt kein Commit; die Datei ist damit noch kein veröffentlichter Projektstand. Auch für einen echten Server würde ein bloßer add-Schritt nichts übertragen.

## 6. Typische Anwendungsfälle

### Änderungen vor Veröffentlichung prüfen

Status und Diff zeigen, welche lokalen Bearbeitungen tatsächlich vorliegen. Eine sauber formulierte Commitnachricht ersetzt die Kontrolle des Umfangs nicht.

### Einen gemeinsamen Projektstand bearbeiten

Eine Arbeitskopie ermöglicht eigene Änderungen. Fremde zwischenzeitliche Änderungen können beim Aktualisieren Konflikte erzeugen; diese fachlich lösen statt unbesehen eine Seite zu verwerfen.

### Frühere Versionen nachvollziehen

Revisionen und Verlauf können erklären, wann eine Änderung eingegangen ist. Verfügbarkeit und Leserechte des Repositorys bleiben Voraussetzungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`commit`, Repositorykopien und andere serverbezogene Aktionen können gemeinsam genutzte Daten verändern. `update`, `switch` und `revert` beeinflussen lokale Dateien. Vor solchen Aktionen eigene Änderungen sichern und Ziel sowie Richtung verstehen.

Repositoryinhalte und URLs können vertraulich sein. Zugangsdaten nicht in Befehlszeilen schreiben. Externals können zusätzliche Projekte oder Quellen einbeziehen; eine vermeintlich kleine Arbeitskopie muss deshalb nicht nur den unmittelbar sichtbaren Bestand betreffen. Clientkonfiguration und vertrauenswürdige Transportprüfung bewusst planen.

## 8. Häufige Fehler

- **Nicht in einer Arbeitskopie:** Normales Verzeichnis mit einem versionierten Arbeitsbereich verwechselt.
- **Neue Datei nicht im Repository:** Nur add, aber kein bewusst freigegebener Commit erfolgt.
- **Konflikt nach Update:** Änderungen beider Seiten müssen zusammenpassen.
- **Status prüft Server nicht:** Lokale Anzeige und -u unterscheiden.
- **Falsche URL oder Revision:** Projektzweig und gewünschten Stand vor Änderung prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem neuen lokalen Übungsrepository beginnen und vor schreibenden Aktionen Status und Diff lesen. Keine echten Zugangsdaten oder gemeinsamen Repositorys zum Dokumentationsnachweis verwenden.

**Prüfstand:** Apache-Kurzanleitung und verlinkte Referenzen gelesen. `svn` und `svnadmin` lokal nicht installiert. Kein Repository angelegt, kein Checkout, Commit, Serverkontakt oder Dateiverwerfen ausgeführt. Das gesamte Beispiel bleibt praktisch offen; eine Quellenprüfung ist kein Funktionstest.

## 10. Verwandte Befehle

- `svnadmin`: lokale Repositoryverwaltung mit eigenem Funktionsumfang.
- `svnlook`: Repositoryinformationen in geeigneten Verwaltungsumgebungen lesen.
- `git`, `hg`: andere Versionsverwaltungen mit anderen Arbeitsmodellen.
- `diff`: Textunterschiede unabhängig von Versionsverwaltung darstellen.

Ausgangsdatensatz 301 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
