# Support bundle: Symlink-Export abgesichert

Pruefdatum: 2026-10-19. Basis: `96bc3791bc6ca62a888cb7bb38a6b00115261f8b`
(`main`, Noogman4/dev-lab). Lokale Aenderungen, nicht committet oder gepusht.

Cloud-Befund: **Support bundle follows diagnostic symlinks into arbitrary
readable files**, Low, CWE-59. Urspruengliche Scanrevision:
`c6a6c5bfefd5189bfdab890aa608dea0c94078d9`.

## Reproduktion

Der unveraenderte Produktionscode der aktuellen Basis exportierte synthetischen
Geheimtext ueber Symlinks an allen sechs Kandidatenpositionen: Diagnosebericht,
startup_error.log, crash.log, Documents/NetMon/Logs/runtime.log sowie
State/logs/runtime.log und network_debug.log. Ein weiterer Test ersetzte die
Quelle nach der Manifest-Erstellung durch einen Symlink; auch hier erschien der
Geheimtext im Archiv. Vor der Korrektur: **7 fehlgeschlagene Sicherheitstests,
1 bestandener positiver Kontrolltest**. Keine echten Geheimnisse oder
privilegierten Operationen wurden verwendet.

## Korrektur

- Diagnoseauswahl verwirft Symlinks ueber lstat und prueft regulaere Dateien.
- Export erlaubt nur festgelegte Dateinamen beziehungsweise Diagnoseberichte
  unmittelbar in den drei freigegebenen Quellverzeichnissen.
- Jede Verzeichniskomponente wird relativ zu einem offenen Verzeichnisdeskriptor
  mit O_DIRECTORY und O_NOFOLLOW geoeffnet. Das Quellverzeichnis muss dem
  effektiven Benutzer gehoeren und darf nicht gruppen-/weltbeschreibbar sein.
- Quellen werden mit O_NOFOLLOW und O_NONBLOCK geoeffnet. Vorherige Metadaten
  und fstat muessen dieselbe Device-/Inode-Identitaet zeigen. Nur regulaere
  Dateien mit genau einem Hardlink, erwartetem Eigentuemer und ohne
  Gruppen-/Weltschreibrechte werden akzeptiert.
- Nach erneuter Pruefung beim eigentlichen Export bleiben die Deskriptoren bis
  zum Ende offen. ZIP-Inhalte werden daraus gestreamt; kein ZipFile.write und
  kein erneutes Oeffnen des Quellpfads. Das Manifest nennt nur akzeptierte Quellen.
- Das Ziel wird ebenfalls in einem ohne Symlinks geoeffneten Verzeichnis mit
  O_EXCL und Modus 0600 erstellt. Vorhandene ZIPs werden nicht ueberschrieben.
- Fehlen die benoetigten Linux-No-Follow-Primitiven, scheitert der Export sicher.

## Validierung

**76 Tests bestanden**, einschliesslich **29 neuer Sicherheitstests**:

```sh
python3 -m pytest -q tests/test_support_bundle_security.py \
  tests/test_support_bundle.py tests/test_core_diagnostics.py \
  tests/test_netmon_diagnostics.py
```

Abgedeckt: alle sechs Quell-Symlinks, neuester Bericht als Symlink,
Verzeichnis- und Vorfahren-Symlinks, Hardlinks, FIFO, unsichere Dateirechte,
fremder Eigentuemer, unsichere Verzeichnisrechte, Dateiaustausch nach Auswahl,
Dateiaustausch zwischen stat/open (Symlink, FIFO, regulaere Ersatzdatei),
Verzeichnisaustausch waehrend des Oeffnens, Dateiaustausch nach Manifestbildung,
unzulassige Pfade, fehlende No-Follow-Unterstuetzung, kollidierende Ausgabedateien
und private ZIP-Rechte. Normale Diagnoseberichte und Logs bleiben exportierbar.

Ein vorhandener Integrationstest simuliert nun auch den freigegebenen
Diagnoseordner; die neue Produktionspruefung wird nicht umgangen.

Black und git diff --check bestanden. Die neue Testdatei besteht Ruff ohne
Ausnahmen. In den drei geaenderten vorhandenen Python-Dateien bestehen zusammen
12 bereits auf der Basis vorhandene Ruff-Meldungen; ein Vergleich der
Regel-/Meldungspaare bestaetigt keine neuen Lint-Befunde. Kein Gesamtsuitenlauf
und kein neuer kostenpflichtiger Cloud-Scan.

## Grenzen und Verhalten

Die gepruefte Symlink-/Pfadwechselursache ist lokal behoben. Der Cloud-Status
wurde nicht geaendert. Diese Pruefung ist keine Sicherheitsfreigabe fuer das
gesamte Repository.

Absichtlich verlinkte Benutzerverzeichnisse sowie gruppenbeschreibbare Dateien
und Quellordner werden konservativ ausgeschlossen; ein unsicherer Zielordner
fuehrt zum Fehler. Ein zweiter Export mit identischem Zeitstempelnamen meldet
FileExistsError, statt das erste ZIP zu ersetzen.

Dies schafft keine Isolation gegen Root oder gegen beliebige Schreibaktionen
derselben UID. Ein Deskriptor bindet die Dateidentitaet, friert aber vorhandene
Dateibytes nicht ein; gleichzeitige In-place-Aenderungen eines akzeptierten
Inodes sind keine unveraenderliche Momentaufnahme. Weitere Themen wie
Log-Inhaltsredaktion, Groessenbudgets oder vollstaendige Same-UID-Isolation
sind nicht Gegenstand dieser Korrektur.

## Uebernahme

Der beigefuegte Patch ist gegen die oben genannte Basis erzeugt und per
`git apply --check --cached` gegen deren unveraenderten Index geprueft.
Im eigenen Checkout zuerst `git apply --check support-bundle-symlink-fix.patch`,
dann `git apply support-bundle-symlink-fix.patch` ausfuehren und die Tests erneut
laufen lassen. Bei abweichender Revision erst den Diff pruefen.

## Lokale Nachpruefung in Bubblewrap

Die vorstehenden Reproduktions- und 76-Test-Angaben stammen aus dem gelieferten
Pruefbericht. Die nachfolgende Pruefung wurde im lokalen Checkout auf Basis
`96bc3791bc6ca62a888cb7bb38a6b00115261f8b` ausgefuehrt. Die urspruengliche
Vorher-Reproduktion mit sieben Fehlern wurde hier nicht erneut ausgefuehrt.

Der unveraendert uebernommene Patch scheiterte hier zunaechst im ersten
Sicherheitstest: Die Test-Fixture erzeugte einen gruppenbeschreibbaren
Ausgabeordner mit Modus 0770. Die neue Produktionspruefung wies ihn korrekt ab;
es handelte sich nicht um einen Hostzugriff oder einen erfolgreichen Export.
Der Lauf wurde nach diesem einen Fehler beendet.

Zwei eng begrenzte Ergaenzungen stellen gueltige Vorbedingungen her:

- `support_packages_dir()` legt **neue** Ausgabeordner explizit mit Modus 0700
  an. Vorhandene Ordner werden nicht umberechtigt; unsichere bestehende Ordner
  bleiben abgewiesen. Es wird keine Sicherheitspruefung abgeschwaecht.
- Gueltige synthetische Quelldateien und Verzeichnisse erhalten explizit
  0600 beziehungsweise 0700. Das betrifft die neue Sicherheits-Fixture sowie
  die vorhandenen Exporttests in `tests/test_support_bundle.py` und
  `tests/test_netmon_diagnostics.py`. Die absichtlich unsicheren Rechte,
  Symlinks, Hardlinks und FIFO-Faelle bleiben unveraendert wirksam.

Drei weitere Regressionen pruefen private Neuanlage auch bei Prozess-Umask 0,
Abweisung eines vorhandenen gruppenbeschreibbaren Ausgabeordners ohne
Umberechtigung und Abweisung eines Ausgabeordner-Symlinks. Die Umask wird
ausschliesslich im isolierten Testprozess kurzzeitig geaendert und im
`finally`-Block wiederhergestellt. Alle Assertions der mitgelieferten
Sicherheits- und Integrationstests sind erhalten.

Vor beiden abschliessenden Teststufen bestand die unveraenderte
Bubblewrap-Probe: unprivilegierte UID, NoNewPrivs, schreibgeschuetztes
Repository, privater Netzwerk-Namespace ohne Host-Routen, keine Host-Home-,
WireGuard-/NetworkManager-Konfiguration oder Host-Dienstesockets.
Alle pytest-Laeufe liefen ueber `tests/run_isolated_suite.py` mit aktivem
unveraendertem Host-Access-Guard, ohne PHP-Installation oder neue Host-Mounts.

| Lauf | Ergebnis | Artefaktverzeichnis unter `/tmp/user/1000/` |
| --- | --- | --- |
| Erster Lauf des unveraenderten Patches | 1 fehlgeschlagener Test wegen unsicherem Fixture-Ausgabeordner; danach Abbruch | `netmon-isolation-84aby5pz` |
| Sicherheitsregressionen nach Berechtigungsanpassung | 32 bestanden, 0 Fehler/Skips | `netmon-isolation-812na05k` |
| Support-/Diagnosegruppe plus Guard und About | 109 bestanden, 0 Fehler/Skips | `netmon-isolation-atgtjum7` |

Die 109 Faelle bestehen aus 32 Sicherheits-, 3 Support-Bundle-, 3
Core-Diagnostik-, 41 NetMon-Diagnostik-, 21 Guard- und 9 About-Tests. Die 32
Sicherheitsfaelle sind Teil der 109, keine zusaetzlichen eindeutigen Faelle.
JUnit bestaetigt die Aufteilung. Laufzeit der abschliessenden Auswahl:
1,48 Sekunden. Die Verzeichnisse enthalten jeweils `junit.xml` und `xvfb.log`.

Reproduzierbare abschliessende Auswahl, ausschliesslich im vorhandenen Starter:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  -q --tb=short tests/test_support_bundle_security.py \
  tests/test_support_bundle.py tests/test_core_diagnostics.py \
  tests/test_netmon_diagnostics.py tests/test_host_access_guard.py \
  tests/test_netmon_about.py
```

Lokales Ruff 0.15.20 mit der Projektkonfiguration meldet fuer die fuenf
betroffenen Python-Dateien keine Fehler. Die im Fremdbericht genannten
12 Altmeldungen wurden mit dieser lokalen Konfiguration auch vor der
Uebernahme in den drei vorhandenen Patch-Dateien nicht gemeldet. Black,
Syntaxpruefung ohne Import/Ausfuehrung oder pyc-Dateien sowie
`git diff --check` bestanden. Keine Lint-Ausnahmen oder Guard-Aenderungen.

Der lokale Umfang betraegt sechs Dateien: die fuenf Patch-Dateien sowie
`tests/test_support_bundle.py` fuer sichere Testvorbedingungen. Alle anderen
erfassten Dateien einschliesslich der fuenf About-Arbeiten sind hashgleich
erhalten; die About-Tests fuer Deutsch/Englisch und hell/dunkel bestehen.
`secure-browser/` wurde weder inhaltlich gelesen noch veraendert und blieb
im Test-Namespace verdeckt. Index unveraendert und leer, HEAD unveraendert.

Keine Gesamtsuite und kein Cloud-Scan gestartet. Der bekannte Flatpak-
Isolationsblocker und die 314 unvalidierten PHP-Faelle bleiben separat offen.
Die zuvor genannten Grenzen hinsichtlich In-place-Aenderungen, Same-UID,
Root, Inhaltsredaktion und Ressourcenbudgets gelten weiterhin. Der offene
L-04-Autorisierungsblocker wird durch diese Support-Bundle-Korrektur nicht
behoben. Keine echten privilegierten Operationen, produktiven Dateizugriffe,
Host-Netzwerk- oder Systemkonfigurationsaenderungen. Kein Commit, Push oder
Deployment.
