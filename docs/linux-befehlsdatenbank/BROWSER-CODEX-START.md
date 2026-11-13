# Startauftrag für Browser-Codex: NetMon 201–210

## Ausgangspunkt und Arbeitsgrenze

Repository: `Noogman4/dev-lab`.
Übergabebranch: `codex/linux-docs-browser-handoff-20261113`.
Arbeite in einer eigenen Cloud-Arbeitskopie auf Grundlage dieses Branches.
Prüfe zuerst, ob die hier genannten Dateien tatsächlich vorhanden sind.
Unveröffentlichte Dateien auf Svens lokalem Rechner gehören nicht zu deinem
Arbeitsstand und dürfen nicht vorausgesetzt werden.

Codi bearbeitet 1–100, Claude 101–200. Für dich ist 201–300 reserviert.
**Jetzt ausschließlich die vorhandenen Entwürfe 201–210 korrigieren und prüfen.
Danach stoppen.** Die Reservierung ist keine Freigabe, bis 300 weiterzuarbeiten.

Lies die geltenden `AGENTS.md`, dann `PROMPT.md`, die Muster `7z.md` und `tar.md`,
den eingefrorenen Katalog und `browser-codex/REVIEW-201-210.md`.

## Was bereits vorhanden ist

- `browser-codex/KATALOG-201-300.json`: feste Kennungen und Originaldatensätze.
- `tools/netmon-linux-befehlsdatenbank-v1.csv`: vollständige Originalquelle,
  713 Datensätze; CSV-Kopf zählt nicht mit.
- `browser-codex/entwuerfe-201-210/`: Chads unveränderte Rückgabe, keine Freigabe.
- `browser-codex/HERKUNFT-201-210.json`: SHA-256 des Rückgabe-ZIP und seiner
  enthaltenen Dateien; Herkunftsnachweis innerhalb der Übergabe, keine Signatur.
- `netmon/services/linux_help_markdown_service.py`: tatsächlicher begrenzter
  NetMon-Parser. Die GUI-Dokumentzuordnung bleibt auf den 7z-Piloten begrenzt.
- `scripts/check_linux_command_docs.py`: Struktur- und Zuordnungsprüfung.
- `tests/test_linux_command_docs_handoff.py`: isolierte Tests ohne GUI oder Netz.

Der gemeinsame vollständige Arbeitsindex und die Dateien anderer Bearbeiter
werden bewusst nicht mitveröffentlicht. Das Katalog-JSON ist kein Fortschrittsindex.
Die Original-CSV hat SHA-256
`40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887`.

## Ablauf pro Befehl

1. Originaldatensatz und vorhandenen Entwurf lesen.
2. Aussagen anhand tatsächlich gelesener offizieller Handbücher prüfen.
3. Fachliche Fehler korrigieren und fehlende Erklärungstiefe ergänzen.
4. Nur erlaubte, ungefährliche Beispiele mit eigenen temporären Testdaten prüfen.
5. Vollständige korrigierte Datei im Hauptordner dieser Dokumentation anlegen.
6. Strukturprüfung für diese Nummer ausführen und tatsächlichen Prüfstand notieren.
7. Erst danach mit dem nächsten Datensatz fortfahren.

Bei jedem Beispiel Voraussetzungen, einzelne Schritte und erwartetes Ergebnis
erklären. Bei Gerätebefehlen dürfen erklärte, eindeutig als Muster markierte
Ausgaben verwendet werden; sie sind keine ausgeführten Tests.
Bei `updatedb` auch zeigen, wie die eigene Testdatenbank ausdrücklich ausgewählt
und durchsucht wird. Bei `badblocks` und `blkid` Modi, Ausgabe und Grenzen
ausführlicher erklären, ohne reale Geräte anzusprechen.

## Format

Frontmatter: `id`, `name`, `command`, `category`, `language`, `root_required`,
`risk_level`, `tags`, `status`, `source_catalog`, `source_record`, `reviewed_at`,
`locally_checked_version`. Zeichenketten doppelt zitieren; Booleans als
`true`/`false`, Listen als JSON. Kennung, Name, Kategorie und Nummer exakt aus
dem Katalog übernehmen. `command`, Rechte, Risiko und Tags fachlich bestimmen.
Zulässige Risiken sind `safe`, `caution`, `danger`. Sprache ist `de`.
`reviewed_at` enthält das tatsächliche Prüfdatum im Format `YYYY-MM-DD`.

Nach dem Titel exakt diese zehn Hauptabschnitte:

```text
## 1. Kurzbeschreibung
## 2. Was macht der Befehl?
## 3. Syntax
## 4. Wichtige Optionen
## 5. Beispiel erklärt Schritt für Schritt
## 6. Typische Anwendungsfälle
## 7. Risiken, Nebenwirkungen und Vorsicht
## 8. Häufige Fehler
## 9. Sichere Varianten oder Tipps für Einsteiger
## 10. Verwandte Befehle
```

Abschnitt 9 nennt die wirklich verwendete Version, tatsächlich geprüfte Schritte
und offene Aspekte. Bei fehlender praktischer Prüfung weiterhin ausdrücklich
`Nicht praktisch geprüft` beziehungsweise `praktische Prüfung offen` verwenden.
Eine Syntaxprüfung rechtfertigt keine Aussage, dass das Beispiel funktioniert.

## Rückgabe und Stopp

Ergebnisdateien im Ordner `docs/linux-befehlsdatenbank/`:
`touch.md`, `tree.md`, `truncate.md`, `unlink.md`, `updatedb.md`, `vdir.md`,
`watch.md`, `xargs.md`, `badblocks.md`, `blkid.md`.
Zusätzlich ausschließlich den eigenen Bericht
`browser-codex/FORTSCHRITT-CODEX-201-210.md` anlegen.
Ergebnisse als Änderungen zur Review bereitstellen. Keine eigenständigen
Commits, Pushes, Merges oder Weiterarbeit über 210 ohne ausdrücklichen Auftrag.
Keine Änderungen an Code, Prüfungen, Originalen, Katalog oder zentralem Index.

Beginne mit einer kurzen Zusammenfassung von Bereich, Vorgehen und Stoppgrenze.
