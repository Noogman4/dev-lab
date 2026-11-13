# Gemeinsame Linux-Befehlsdokumentation

## Arbeitsaufteilung

- Codi lokal: Datensätze 1–100; Claude: 101–200.
- Browser-Codex: 201–300 reserviert. Der aktuelle Auftrag umfasst ausschließlich
  die Korrektur von 201–210; danach stoppen und Prüfung abwarten.
- Keine Unteragenten oder weiteren Bearbeiter eigenständig beauftragen.
- Bei einem ausdrücklichen Stopp sofort pausieren.

## Verbindliche Unterlagen

Lies `BROWSER-CODEX-START.md`, `PROMPT.md`, `7z.md`, `tar.md` sowie
`browser-codex/REVIEW-201-210.md` vor der Bearbeitung.
`browser-codex/KATALOG-201-300.json` enthält die eingefrorene Zuordnung für
Browser-Codex. Kennung, Name, Kategorie, Dateiname und Datensatznummer sind
verbindlich. Die ursprünglichen CSV-Felder sind Ausgangsmaterial und können
fachlich falsch sein. Korrigiere die Erklärung, nicht den Ausgangsdatensatz.

## Dateiformat und Qualität

- Eine UTF-8-Markdown-Datei pro Eintrag, Dateiname exakt aus dem Katalog.
- Frontmatter mit JSON-kompatiblen Werten; keine zusätzlichen YAML-Konstrukte.
- Exakt die zehn Hauptabschnitte aus dem Startauftrag; Unterabschnitte erlaubt.
- Kurze, konkrete Abschnitte; keine Fülltexte und keine starre Mindestwortzahl.
- Optionen, Berechtigungen, Risiken und erwartete Ausgaben konkret erklären.
- Tatsächlich gelesene Primärquellen direkt verlinken. Implementierungs- und
  Versionsunterschiede benennen; Unklarheiten als Prüfpunkt markieren.
- Reader-kompatibles Markdown: einfache Tabellen, Listen, geschlossene
  Codeblöcke, normale Links. Keine Skripteinbettung, Includes, Bilder oder HTML.
- Parserprüfung ist keine fachliche Freigabe. Ausgeführte Beispiele,
  Quellenprüfung und offene praktische Prüfungen getrennt dokumentieren.
- Musterdateien sind Stilbeispiele; ihr Prüfstand gilt nicht für neue Dokumente.

## Ausführungsgrenzen

Beispieltests nur mit kleinen eigenen Dateien in einem eigenen temporären
Verzeichnis. Fehler beim Anlegen dieses Verzeichnisses müssen den Test abbrechen.
Keine realen Benutzerdateien, privilegierten Aktionen, Gerätezugriffe,
Konten-/Dienst-/Systemänderungen, Paketinstallationen, Mounts, Audio-/Videoaktionen
oder realen Netzwerkanfragen zum Nachweis von Beispielen.
Offizielle Quellenrecherche ist erlaubt. `badblocks` und `blkid` nicht an realen
Datenträgern testen. Fehlende Programme oder unzulässige Tests als offen melden;
keine Ausführungen oder Versionen erfinden.

## Änderungen und Übergabe

Der aktuelle Auftrag erlaubt ausschließlich neue korrigierte Dokumente 201–210
im Ordner `docs/linux-befehlsdatenbank/` und den eigenen Fortschrittsbericht
`browser-codex/FORTSCHRITT-CODEX-201-210.md`. Ursprüngliche Entwürfe bleiben als
Vergleich erhalten. Fortschrittsbericht: pro Datei Quellenstand, wirklich
ausgeführte Tests samt Version, offene Punkte und vorgenommene Korrekturen.

Keine Änderungen an zentralem `index.json`, zentralen Fortschrittsdateien,
Original-CSV, Katalog, Mustern, Entwurfsoriginalen, Prüfcode, NetMon-Code, Reader,
UI oder Packaging. Der Hinweis auf Index-/Fortschrittsänderungen in `PROMPT.md`
wird durch diese engere Aufgabenverteilung ersetzt; Codi integriert später.
Keine eigenständigen Commits, Pushes oder Merges ohne ausdrücklichen Auftrag.

## Strukturprüfung nach jeder Datei und am Ende

Vom Repository-Stamm aus mit dem verfügbaren Python-Interpreter:

```bash
python3 scripts/check_linux_command_docs.py --documents docs/linux-befehlsdatenbank --first 201 --last 201
python3 scripts/check_linux_command_docs.py --documents docs/linux-befehlsdatenbank --first 201 --last 210
python3 -m pytest -q tests/test_linux_command_docs_handoff.py
```

Die erste Prüfung jeweils auf die tatsächlich bearbeitete Nummer anpassen.
Die Tests prüfen auch die unveränderten Entwürfe strukturell; deren bekannte
fachliche Fehler stehen ausdrücklich im Review und werden damit nicht behoben.
